# Copyright (c) 2026, Renaud Allard <renaud@allard.it>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""The data coordinator of one config entry.

Ticks hourly. Each tick keeps the supplier's card fresh (a cheap probe where
the supplier offers one, a 24-hour TTL otherwise), refreshes the supplier's
index values and the calorific values once a day, reads the gas meter out of
the recorder, and prices the household on all of it.

A card that cannot be fetched is never a reason to stop pricing: the last
good one keeps serving, restored from the entry's store across a restart,
and when there is none or it has gone stale the card archive stands in. The
Repairs cards say when either happens.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import ssl
from dataclasses import replace
from datetime import date, datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.loader import async_get_integration
from homeassistant.util import dt as dt_util

from . import calorific
from .bill import IndexValue, bill_month, contract_leg, month_key
from .compare import OwnContract, rank
from .const import (
    CONF_ANNUAL_CONSUMPTION_KWH,
    CONF_CALIBER,
    CONF_CARD_ARCHIVE,
    CONF_CONTRACT,
    CONF_CONTRACT_START_DATE,
    CONF_CONVERSION_FACTOR,
    CONF_CONVERSION_MODE,
    CONF_DAILY_COMPARE,
    CONF_DSO,
    CONF_GAS_METER,
    CONF_REGION,
    CONF_STATION,
    CONF_SUPPLIER,
    CONF_YTD_FROM_CONTRACT_START,
    CONVERSION_MANUAL,
    DEFAULT_ANNUAL_CONSUMPTION_KWH,
    DEFAULT_CALIBER,
    DEFAULT_CARD_ARCHIVE,
    DEFAULT_CONVERSION_MODE,
    DEFAULT_DAILY_COMPARE,
    DOMAIN,
    STORAGE_VERSION,
    SUPPLIER_CUSTOM,
    UPDATE_INTERVAL_MINUTES,
)
from .contract_periods import (
    PeriodBilling,
    current_period_start,
    parse_date,
    periods_this_year,
    previous_contracts,
    signing_month,
)
from .coordinator_data import Conversion, CoordinatorData
from .daily_ranking import DailyRanking, ranking_minute
from .gas_meter import (
    MeterKind,
    RecorderUnavailable,
    daily_consumption,
    discover_energy_gas_meter,
    statistic_kind,
)
from .issues import sync_issues
from .month_cards import (
    ArchiveUnavailable,
    MonthCardCache,
    current_card,
    fetch_archived_row,
)
from .pricing import PriceBreakdown, PricingError, fixed_costs
from .providers import get as get_extractor
from .providers._pdf import is_transient_fetch_error
from .providers._rates import EnergyRates
from .providers._resolve import resolve_for_delivery, tier_for
from .providers.base import (
    CardNotReadableError,
    ExtractorError,
    IndexTable,
    SupplierExtractor,
    SupplierSnapshot,
)
from .providers.custom import build_snapshot as build_custom_snapshot
from .running_costs import (
    Household,
    RunningCosts,
    meter_start,
    rolling_year_kwh,
    running_costs,
    to_kwh,
)
from .snapshot_codec import SnapshotDecodeError, snapshot_from_json, snapshot_to_json

_LOGGER = logging.getLogger(__name__)

# A card is fetched again after this long when the supplier offers no probe.
SNAPSHOT_TTL = timedelta(hours=24)
# The index values and the calorific values move monthly; once a day catches
# a publication within a day.
INDEX_TTL = timedelta(hours=12)
CALORIFIC_TTL = timedelta(hours=24)
# A card this old, or this long past the last day it prices, is stale: the
# supplier has not been readable for a week, or has not published a new month.
SNAPSHOT_STALE_AGE = timedelta(days=7)
SNAPSHOT_STALE_AFTER_VALIDITY = timedelta(days=7)
# The card archive is asked back this many months for a card to stand in.
_ARCHIVE_MONTHS_BACK = 12


def _card_digest(card: SupplierSnapshot) -> str:
    """A card's figures, digested."""
    blob = json.dumps(snapshot_to_json(card), sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


class GasCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Fetches the card, reads the meter and prices one household."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.entry = entry
        self._session: aiohttp.ClientSession = async_get_clientsession(hass)
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )
        self.extractor: SupplierExtractor = get_extractor(entry.data[CONF_SUPPLIER])
        self._snapshot: SupplierSnapshot | None = None
        self._fetched_at: datetime | None = None
        self._probe_key: str | None = None
        self._card_source = "live"
        # The card in hand stands in for the one of the month: restored from
        # the Store, or the card archive's latest row taken after a failure.
        # Due at once, unlike a card read for the month, here or by the
        # card archive, which is due when it changes or ages.
        self._stand_in = False
        self._force_refresh = False
        self._failures = 0
        self.last_error = ""
        # The last error was the card failing to price the household.
        self._pricing_error = ""
        self.card_unreadable = False
        # The card in hand is the card archive's OCR reading of a card
        # published as page images.
        self.card_read_by_ocr = False
        self._index_table: IndexTable | None = None
        self._index_fetched_at: datetime | None = None
        self._gcv: dict[str, float] = {}
        self._gcv_fetched_at: datetime | None = None
        self._gcv_context: ssl.SSLContext | None = None
        self._months = MonthCardCache()
        # The release the store was written by: past months' cards read by
        # another release are read again, so a parser fix reaches them, and
        # kept where no one serves them any more.
        self._release: str | None = None
        self._month_fill: asyncio.Task[None] | None = None
        self._first_tick = True
        self.meter: str | None = None
        self.meter_count = 0
        self.meter_error = ""
        # The household the last tick priced, measured volume included, for
        # the price history backfill to price past months the same way.
        self.household: Household | None = None
        # What the price history was last drawn from (backfill.py), kept in
        # the store so a restart does not redraw an unchanged year.
        self.backfill_stamp: str | None = None
        self._periods = PeriodBilling(self._months)
        self.unpriced_periods: list[str] = []
        # The last daily ranking (compare.py), kept across restarts, and the
        # task computing the next one.
        self.daily_ranking: DailyRanking | None = None
        self._ranking_task: asyncio.Task[None] | None = None

    # ---- settings ---------------------------------------------------------

    @property
    def _data(self) -> dict[str, Any]:
        return dict(self.entry.data)

    @property
    def contract(self) -> str:
        return str(self._data[CONF_CONTRACT])

    @property
    def region(self) -> str:
        return str(self._data[CONF_REGION])

    def window_start(self, today: date) -> date:
        """The first day the running costs cover: 1 January, or the contract
        start when the entry bills from it and records no earlier contract
        this year (which would then go unbilled)."""
        start = date(today.year, 1, 1)
        if periods_this_year(self._data, today):
            return start
        contract_start = parse_date(self._data.get(CONF_CONTRACT_START_DATE))
        if self._data.get(CONF_YTD_FROM_CONTRACT_START) and contract_start is not None:
            return max(start, min(contract_start, today))
        return start

    def period_start(self, today: date) -> date:
        """The first day the current contract supplied this year."""
        return current_period_start(self._data, self.window_start(today), today)

    def switch_day(self) -> date | None:
        """The day the current contract took over from the last one recorded
        at a switch, whatever its year, None when none is recorded."""
        periods = previous_contracts(self._data)
        if not periods:
            return None
        return max(date.fromisoformat(str(p["until"])) for p in periods) + timedelta(days=1)

    # ---- persistence ------------------------------------------------------

    async def async_load_persistent(self) -> None:
        """Restore the last card and the caches, so a restart while the
        supplier is down still prices on something real."""
        self._release = str((await async_get_integration(self.hass, DOMAIN)).version)
        blob = await self._store.async_load()
        if not isinstance(blob, dict):
            return
        try:
            snapshot = snapshot_from_json(blob.get("snapshot"))
            fetched_at = datetime.fromisoformat(blob["fetched_at"])
        except (SnapshotDecodeError, KeyError, TypeError, ValueError):
            snapshot = None
            fetched_at = None
        # Only a card for this contract that prices this household's DSO: a
        # move to another region keeps the supplier and the contract, and a
        # card of the old region would stand in for the new one's.
        if (
            snapshot is not None
            and (snapshot.supplier, snapshot.contract) == (self.extractor.id, self.contract)
            and str(self._data.get(CONF_DSO)) in snapshot.dsos
        ):
            self._snapshot = snapshot
            self._fetched_at = fetched_at
            self._card_source = "cache"
            self._stand_in = True
            # The archive's OCR reading, as the store says: stored as such
            # again whatever the next check finds, and waited on like one.
            self.card_read_by_ocr = blob.get("read_by_ocr") is True
        # A price is only resolved against its own supplier's publication:
        # a table another supplier published, before a change of supplier,
        # is not restored, even under an index name the two share.
        table = blob.get("index")
        if isinstance(table, dict) and blob.get("index_supplier") == self.extractor.id:
            self._index_table = {
                str(name): {str(k): float(v) for k, v in values.items()}
                for name, values in table.items()
                if isinstance(values, dict)
            }
        gcv = blob.get("gcv")
        if isinstance(gcv, dict) and gcv.get("station") == self._data.get(CONF_STATION):
            self._gcv = {str(k): float(v) for k, v in (gcv.get("values") or {}).items()}
        self._months.load_json(blob.get("months"), reread=blob.get("release") != self._release)
        stamp = blob.get("backfill")
        self.backfill_stamp = stamp if isinstance(stamp, str) else None
        ranking = DailyRanking.from_json(blob.get("ranking"))
        # A ranking made for another contract prices a saving against a
        # contract the household left, and one made under other settings
        # (volume, DSO, caliber, typed figures) for another household: the
        # day is ranked again instead.
        if (
            ranking is not None
            and ranking.own == (self.extractor.id, self.contract)
            and blob.get("ranking_for") == self._settings_digest()
        ):
            self.daily_ranking = ranking

    async def _save_persistent(self) -> None:
        if not self._set_up():
            return
        payload: dict[str, Any] = {
            "snapshot": None if self._snapshot is None else snapshot_to_json(self._snapshot),
            "fetched_at": None if self._fetched_at is None else self._fetched_at.isoformat(),
            "read_by_ocr": self.card_read_by_ocr,
            "index": self._index_table,
            "index_supplier": self.extractor.id,
            "gcv": {"station": self._data.get(CONF_STATION), "values": self._gcv},
            "months": self._months.to_json(),
            "release": self._release,
            "backfill": self.backfill_stamp,
            "ranking": None if self.daily_ranking is None else self.daily_ranking.to_json(),
            "ranking_for": self._settings_digest(),
        }
        await self._store.async_save(payload)

    def _settings_digest(self) -> str:
        """The entry's settings, digested: what a stored ranking was made
        under."""
        blob = json.dumps(self._data, sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    async def async_save(self) -> None:
        """Write the store now, outside a tick."""
        await self._save_persistent()

    def card_months_signature(self) -> str:
        """What the year's past months are priced from: the entry's
        settings, each past month's own card and the card in hand as read,
        the latest index value and the latest calorific value. It moves when
        any of them changes or lands, a card read again after an update
        included, which is when the price history is worth drawing again."""
        today = dt_util.now().date()
        own = [
            f"{month}:{_card_digest(card)}"
            for month in self._months_needed(today)
            if (card := self._month_card(month)) is not None
        ]
        index = max((max(v) for v in (self._index_table or {}).values() if v), default="")
        gcv = max(self._gcv, default="")
        current = "" if self._snapshot is None else _card_digest(self._snapshot)
        return f"{self._settings_digest()}|{','.join(own)}|{index}|{gcv}|{current}"

    # ---- the card ---------------------------------------------------------

    def snapshot_age(self) -> timedelta | None:
        if self._fetched_at is None:
            return None
        return dt_util.utcnow() - self._fetched_at

    def snapshot_stale(self) -> bool:
        age = self.snapshot_age()
        if self._snapshot is None or age is None:
            return False
        if age > SNAPSHOT_STALE_AGE:
            return True
        valid_until = self._snapshot.valid_until
        return (
            valid_until is not None
            and dt_util.now().date() > valid_until + SNAPSHOT_STALE_AFTER_VALIDITY
        )

    async def _card_is_due(self) -> tuple[bool, str | None]:
        """Whether the card must be fetched, and the probe key seen.

        A card from the Store or a stand-in from the card archive is due at
        once; the archive's reading of an unreadable card is the card of the
        month, and is asked for again when the supplier's card changes and
        once a day besides, since the archive reads a card reissued in the
        month a day after the key moved. The probe is asked either way, so
        a card fetched for another reason is kept against the key it was
        fetched under rather than fetched again on the next tick.
        """
        key = None
        if self.extractor.probe is not None:
            key = await self.extractor.probe(self._session, self.contract, self.region)
        if self._snapshot is None or self._force_refresh or self._stand_in:
            return True, key
        # A card whose month is over is asked for again on every tick until
        # its successor is out, probe or not: the successor may have gone up
        # before its month began, under the key the card in hand is kept
        # against, and no later change of key would ever come for it.
        valid_until = self._snapshot.valid_until
        if valid_until is not None and dt_util.now().date() > valid_until:
            return True, key
        if key is not None and (key != self._probe_key or not self.card_read_by_ocr):
            return key != self._probe_key, key
        age = self.snapshot_age()
        return age is None or age >= SNAPSHOT_TTL, key

    async def _refresh_snapshot(self) -> None:
        if self.extractor.id == SUPPLIER_CUSTOM:
            # The household's typed card: nothing to fetch, never stale.
            self._snapshot = build_custom_snapshot(self._data)
            self._fetched_at = dt_util.utcnow()
            self._card_source = "live"
            self._stand_in = False
            self.last_error = ""
            return
        due, key = await self._card_is_due()
        if not due:
            if key is not None and not self.card_read_by_ocr:
                # The supplier still serves the card in hand: as good as a
                # fetch, and what keeps a month's card from ageing into
                # staleness between two publications.
                self._fetched_at = dt_util.utcnow()
            return
        try:
            snapshot, source = await current_card(
                self._session,
                self.extractor,
                self.contract,
                self.region,
                f"{dt_util.now().date():%Y-%m}",
                use_archive=bool(self._data.get(CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE)),
            )
        except CardNotReadableError as err:
            if self.card_read_by_ocr and self._snapshot is not None:
                # The card archive's reading of last month's card is in hand,
                # read here, restored from the store or taken as a stand-in,
                # and the archive has not read the new month's yet: it reads
                # once a day, so this is a wait, not an unreadable card.
                self.card_unreadable = False
                self.card_read_by_ocr = True
                self._fetch_failed(str(err), transient=True)
            else:
                self.card_unreadable = True
                self.card_read_by_ocr = False
                self._fetch_failed(str(err), transient=False)
        except ExtractorError as err:
            transient = is_transient_fetch_error(str(err))
            # A network failure says nothing about the card: one known to be
            # unreadable stays so, rather than its count of failures being
            # read as a layout change.
            if not transient:
                self.card_unreadable = False
            self._fetch_failed(str(err), transient=transient)
        else:
            self._snapshot = snapshot
            self._fetched_at = dt_util.utcnow()
            self._probe_key = key
            self._card_source = source
            self._stand_in = False
            self._force_refresh = False
            self._failures = 0
            self.card_unreadable = False
            self.card_read_by_ocr = source == "ocr"
            self.last_error = ""
            return
        if self._snapshot is None or self.snapshot_stale():
            await self._adopt_archived_card()

    def _fetch_failed(self, message: str, *, transient: bool) -> None:
        self.last_error = message
        if not transient:
            self._failures += 1
        _LOGGER.warning("%s: tariff card not refreshed: %s", self.extractor.label, message)

    async def _adopt_archived_card(self) -> None:
        """Stand the card archive's latest row in for a card we cannot read.

        This month's row first, then back a month at a time, stopping at the
        first one that holds a card and as soon as GitHub fails to answer,
        since a month it could not read may still hold one. Taken only if it
        is newer than what is held.
        """
        if not self._data.get(CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE):
            return
        today = dt_util.now().date()
        year, month = today.year, today.month
        for _ in range(_ARCHIVE_MONTHS_BACK):
            key = f"{year}-{month:02d}"
            try:
                row = await fetch_archived_row(
                    self._session, self.extractor.id, self.contract, self.region, key
                )
            except ArchiveUnavailable as err:
                _LOGGER.debug("card archive unavailable: %s", err)
                return
            if row is not None:
                card, read_by_ocr = row
                held = self._snapshot
                if held is None or (card.valid_until or date.min) > (held.valid_until or date.min):
                    self._snapshot = card
                    self._card_source = "archive"
                    self._stand_in = True
                    self.card_read_by_ocr = read_by_ocr
                    if read_by_ocr:
                        # The archive's reading of a card published as
                        # images: what such a card is priced on, as good as
                        # a fetch, so the card found unreadable is no
                        # failure while the archive has not read the newest.
                        self._fetched_at = dt_util.utcnow()
                        if self.card_unreadable:
                            self._failures = 0
                            self.card_unreadable = False
                    else:
                        self._fetched_at = dt_util.as_utc(
                            dt_util.start_of_local_day(date(year, month, 1))
                        )
                return
            year, month = (year - 1, 12) if month == 1 else (year, month - 1)

    # ---- index values and calorific values ---------------------------------

    async def _refresh_index(self) -> None:
        fetch = self.extractor.fetch_index
        if fetch is None:
            return
        now = dt_util.utcnow()
        if self._index_fetched_at is not None and now - self._index_fetched_at < INDEX_TTL:
            return
        try:
            self._index_table = await fetch(self._session)
        except ExtractorError as err:
            _LOGGER.warning("%s: index values not refreshed: %s", self.extractor.label, err)
            if self._index_table is None and is_transient_fetch_error(str(err)):
                # Nothing held: every indexed month waits on it at the card's
                # printed price, so a source that may answer the next time is
                # asked again next tick.
                return
            # A held table keeps pricing, and a source that refuses the
            # read will refuse it next hour too: not worth an hourly retry.
        self._index_fetched_at = now

    async def _refresh_calorific(self) -> None:
        station = self._data.get(CONF_STATION)
        if self._conversion_mode() == CONVERSION_MANUAL or not station:
            return
        now = dt_util.utcnow()
        if self._gcv_fetched_at is not None and now - self._gcv_fetched_at < CALORIFIC_TTL:
            return
        try:
            if self._gcv_context is None:
                self._gcv_context = await self.hass.async_add_executor_job(
                    calorific.build_ssl_context
                )
            key = await calorific.subscription_key(self._session)
            months = await calorific.list_months(self._session, self._gcv_context, key)
            wanted = [m for m in sorted(months) if m >= f"{dt_util.now().year - 1}-01"]
        except calorific.CalorificError as err:
            # Asked again next tick: with no value held for the station,
            # every running cost waits on it.
            _LOGGER.warning("calorific values not refreshed: %s", err)
            return
        failed = False
        for month in wanted:
            if month in self._gcv:
                continue
            # Each month on its own: one file that cannot be read must not
            # keep every later month from being read.
            try:
                values = await calorific.fetch_month(
                    self._session, self._gcv_context, key, months[month]
                )
            except calorific.CalorificError as err:
                _LOGGER.warning("calorific values of %s not read: %s", month, err)
                failed = failed or is_transient_fetch_error(str(err))
                continue
            for held_station, value in values.items():
                if held_station.ean == station:
                    self._gcv[month] = value
        if failed and not self._gcv:
            # Still nothing for the station, and a file a retry may cure:
            # asked again next tick. One the parser refuses waits a day.
            return
        self._gcv_fetched_at = now

    def _conversion_mode(self) -> str:
        return str(self._data.get(CONF_CONVERSION_MODE, DEFAULT_CONVERSION_MODE))

    def _factor_for(self, kind: MeterKind | None) -> Any:
        """The kWh one meter unit is worth in a month, as a function."""

        def factor(month: str) -> float | None:
            if kind == "energy":
                return 1.0
            return self._m3_factor(month)[0]

        return factor

    def _m3_factor(self, month: str) -> tuple[float | None, str | None]:
        """The kWh one cubic metre is worth in ``month``, and the month the
        value belongs to (the latest published before it while ``month``
        itself is not)."""
        if self._conversion_mode() == CONVERSION_MANUAL:
            value = self._data.get(CONF_CONVERSION_FACTOR)
            return (float(value), None) if value else (None, None)
        if month in self._gcv:
            return self._gcv[month], month
        earlier = [key for key in self._gcv if key < month]
        if not earlier:
            return None, None
        latest = max(earlier)
        return self._gcv[latest], latest

    def _conversion(self, month: str) -> Conversion:
        factor, published = self._m3_factor(month)
        if factor is None:
            return Conversion(factor=None, source="none")
        source = "manual" if self._conversion_mode() == CONVERSION_MANUAL else "station"
        return Conversion(factor=factor, source=source, month=published)

    # ---- month cards --------------------------------------------------------

    def _months_needed(self, today: date) -> list[str]:
        if self.extractor.id == SUPPLIER_CUSTOM:
            # Every month bills on the typed card.
            return []
        start = self.period_start(today)
        current = month_key(today)
        months: list[str] = []
        year, month = start.year, start.month
        while f"{year}-{month:02d}" < current:
            months.append(f"{year}-{month:02d}")
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        signing = signing_month(self._data)
        if signing is not None and signing < current and signing not in months:
            months.append(signing)
        return months

    async def async_fill_month_cards(self, months: list[str]) -> None:
        if self.extractor.id == SUPPLIER_CUSTOM:
            # Nothing to fetch: the typed card is every month's.
            return
        use_archive = bool(self._data.get(CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE))
        for month in months:
            # The cache answers a held month at once, and asks again for one
            # it holds as absent once that answer has aged.
            try:
                await self._months.card(
                    self._session,
                    self.extractor,
                    self.contract,
                    self.region,
                    month,
                    use_archive=use_archive,
                )
            except (ExtractorError, ArchiveUnavailable) as err:
                _LOGGER.debug("%s card for %s not read: %s", self.extractor.label, month, err)

    def _month_card(self, month: str) -> SupplierSnapshot | None:
        if self.extractor.id == SUPPLIER_CUSTOM:
            # The typed card is every month's own.
            return self._snapshot
        row = self._months.get(self.extractor.id, self.contract, self.region, month)
        return None if row is None else row.snapshot

    def _energy_for(self, card: SupplierSnapshot) -> EnergyRates:
        """The energy leg a card bills this household on: the signing card's
        when the entry names a signing month the archive can serve and the
        contract holds its figures, with the figures the household typed
        from its contract laid over it."""
        signed: SupplierSnapshot | None = None
        signing = signing_month(self._data)
        if signing is not None:
            today_month = month_key(dt_util.now().date())
            signed = self._snapshot if signing == today_month else self._month_card(signing)
        return contract_leg(
            card.energy, None if signed is None else signed.energy, self._index_table, self._data
        )

    def month_price(
        self, month: str, *, own_card: bool = False
    ) -> tuple[PriceBreakdown, float | None] | None:
        """The all-in price of ``month`` and the kWh a cubic metre was worth
        in it, priced the way the running costs price it: the month's own
        card where one is held and prices the household, the current card
        otherwise, or with ``own_card`` not at all. None before the first
        tick has priced the household."""
        snapshot = self._snapshot
        household = self.household
        if snapshot is None or household is None:
            return None
        cards = [snapshot]
        # The custom supplier's typed card prices every month.
        if month != month_key(dt_util.now().date()) and self.extractor.id != SUPPLIER_CUSTOM:
            held = self._month_card(month)
            cards = ([] if held is None else [held]) + ([] if own_card else [snapshot])
        for card in cards:
            try:
                bill = bill_month(
                    month=month,
                    card=card,
                    energy=self._energy_for(card),
                    table=self._index_table,
                    dso=household.dso,
                    annual_kwh=household.annual_kwh,
                    caliber=household.caliber,
                    kwh=0.0,
                    days=0,
                    days_in_year=365,
                )
            except PricingError:
                # A month's own card missing the household's DSO or tier is
                # no better than none, as in the running costs.
                continue
            return bill.breakdown, self._m3_factor(month)[0]
        return None

    # ---- the tick -------------------------------------------------------------

    async def async_force_refresh(self, *, wait: bool = False) -> None:
        """Fetch the card, the index values and the calorific values again on
        the next tick whatever their age, or with ``wait`` now, past the
        cooldown that spaces requested refreshes."""
        self._force_refresh = True
        self._index_fetched_at = None
        self._gcv_fetched_at = None
        if wait:
            await self.async_refresh()
        else:
            await self.async_request_refresh()

    @property
    def failures(self) -> int:
        """Consecutive fetches that failed for a reason a retry will not fix."""
        return self._failures

    async def _async_update_data(self) -> CoordinatorData:
        try:
            return await self._tick()
        finally:
            if self._set_up():
                sync_issues(self.hass, self)

    def _set_up(self) -> bool:
        """Whether the entry is still set up, or being set up, with this
        coordinator: a refresh that outlives an unload, a removal or a
        reload of the entry leaves no Repairs card or store behind it."""
        entry = self.hass.config_entries.async_get_entry(self.entry.entry_id)
        return (
            entry is not None
            and entry.state in (ConfigEntryState.LOADED, ConfigEntryState.SETUP_IN_PROGRESS)
            and getattr(entry, "runtime_data", None) is self
        )

    async def _tick(self) -> CoordinatorData:
        await self._refresh_snapshot()
        if self._snapshot is None:
            raise UpdateFailed(self.last_error or "no tariff card available")
        await self._refresh_index()
        await self._refresh_calorific()
        today = dt_util.now().date()
        needed = self._months_needed(today)
        if self._first_tick:
            # The first tick is what setup waits on: fetch the past months'
            # cards, the earlier contracts' too, in the background and price
            # them on the current card until they land.
            self._first_tick = False
            if needed or periods_this_year(self._data, today):
                self._month_fill = self.entry.async_create_background_task(
                    self.hass, self._fill_then_refresh(needed), f"{DOMAIN} month cards"
                )
        elif not self._filling():
            await self.async_fill_month_cards(needed)
        if self._pricing_error and self.last_error == self._pricing_error:
            # Asked again below, before the data the sensors show is built: a
            # card not due for a fetch would keep it.
            self.last_error = ""
        self._pricing_error = ""
        try:
            data = await self._build(today)
        except PricingError as err:
            # The card cannot price this household: its DSO or its tier is
            # missing, for this month or for one the running costs bill.
            self.last_error = self._pricing_error = str(err)
            raise UpdateFailed(str(err)) from err
        self.maybe_rank(today)
        await self._save_persistent()
        return data

    def maybe_rank(self, today: date) -> None:
        """Start the day's ranking once its minute has come, when the entry
        asked for one. The minute is derived from the entry id so that
        installations do not all fetch every supplier at the same time.

        A listener calls this at the minute itself, and every tick after it
        catches a day the minute was missed on (Home Assistant was down)."""
        if not self._data.get(CONF_DAILY_COMPARE, DEFAULT_DAILY_COMPARE):
            return
        if self.daily_ranking is not None and self.daily_ranking.day == today:
            return
        if self._ranking_task is not None and not self._ranking_task.done():
            return
        now = dt_util.now()
        if now.hour * 60 + now.minute < ranking_minute(self.entry.entry_id):
            return
        household = self.household
        if household is None:
            return
        # Tied to the entry, so an unload, a removal or a failed setup
        # cancels it rather than let it write the entry's store afterwards.
        self._ranking_task = self.entry.async_create_background_task(
            self.hass, self._rank(today, household), f"{DOMAIN} daily ranking"
        )

    async def _rank(self, today: date, household: Household) -> None:
        try:
            quotes, _skipped = await rank(
                self._session,
                self.region,
                household,
                month_key(today),
                use_archive=bool(self._data.get(CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE)),
                own=self.own_contract(),
            )
        except Exception:
            # A background job with nobody watching: log it, and let the next
            # tick try again rather than leave an unretrieved exception.
            _LOGGER.exception("daily ranking failed")
            return
        own = (self.extractor.id, self.contract)
        if not any(q.annual_cost is not None for q in quotes if (q.supplier, q.contract) != own):
            # No other contract could be priced, the network down most
            # likely: not kept as the day's ranking, so the next tick tries
            # again.
            _LOGGER.warning("daily ranking priced no other contract; trying again")
            return
        self.daily_ranking = DailyRanking.from_quotes(
            today, quotes, (self.extractor.id, self.contract)
        )
        await self._save_persistent()
        self.async_update_listeners()

    def own_contract(self) -> OwnContract | None:
        """The household's contract as a comparison quotes it: on the card in
        hand with the energy leg the entry is billed on. None before a card
        is held."""
        snapshot = self._snapshot
        if snapshot is None:
            return None
        return OwnContract(
            self.extractor,
            self.contract,
            replace(snapshot, energy=self._energy_for(snapshot)),
            read_by_ocr=self.card_read_by_ocr,
            table=self._index_table,
        )

    def _filling(self) -> bool:
        """Whether the first tick's month cards are still being fetched."""
        return self._month_fill is not None and not self._month_fill.done()

    async def _fill_then_refresh(self, months: list[str]) -> None:
        await self.async_fill_month_cards(months)
        await self._periods.fill(
            self._session,
            self._data,
            dt_util.now().date(),
            use_archive=bool(self._data.get(CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE)),
        )
        await self.async_request_refresh()

    async def _meter(self) -> str | None:
        configured = self._data.get(CONF_GAS_METER)
        if configured:
            self.meter_count = 1
            return str(configured)
        meter, count = await discover_energy_gas_meter(self.hass)
        self.meter_count = count
        return meter

    async def _read_meter(self, today: date) -> tuple[MeterKind | None, dict[date, float]]:
        self.meter = await self._meter()
        self.meter_error = ""
        if self.meter is None:
            return None, {}
        try:
            kind = await statistic_kind(self.hass, self.meter)
            if kind is None:
                return None, {}
            days = await daily_consumption(self.hass, self.meter, kind, meter_start(today), today)
        except RecorderUnavailable as err:
            self.meter_error = str(err)
            _LOGGER.warning("gas meter not read: %s", err)
            return None, {}
        return kind, days

    async def _build(self, today: date) -> CoordinatorData:
        snapshot = self._snapshot
        assert snapshot is not None
        household = Household(
            dso=str(self._data[CONF_DSO]),
            caliber=str(self._data.get(CONF_CALIBER, DEFAULT_CALIBER)),
            annual_kwh=float(
                self._data.get(CONF_ANNUAL_CONSUMPTION_KWH, DEFAULT_ANNUAL_CONSUMPTION_KWH)
            ),
        )
        kind, meter_days = await self._read_meter(today)
        kwh_days = (
            to_kwh(meter_days, self._factor_for(kind), date(today.year, 1, 1))
            if meter_days
            else None
        )
        costs: RunningCosts | None = None
        earlier: list[RunningCosts] = []
        # Named afresh on every tick: last year's earlier contracts are no
        # part of this year's cost.
        self.unpriced_periods = []
        measured = False
        if kwh_days is not None:
            # A measured year picks the tier and the excise slices; the typed
            # estimate stands in until the meter has one.
            rolling = rolling_year_kwh(kwh_days, today)
            if rolling is not None:
                measured = True
                household = Household(
                    dso=household.dso, caliber=household.caliber, annual_kwh=rolling
                )
            costs = running_costs(
                kwh_days=kwh_days,
                today=today,
                window_start=self.period_start(today),
                household=household,
                current_card=snapshot,
                month_card=self._month_card,
                energy_for=self._energy_for,
                table=self._index_table,
            )
            if periods_this_year(self._data, today):
                earlier, self.unpriced_periods = await self._periods.bill(
                    self._session,
                    self._data,
                    today,
                    kwh_days,
                    household.annual_kwh,
                    use_archive=bool(self._data.get(CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE)),
                    fill=not self._filling(),
                )
        month = month_key(today)
        now_bill = bill_month(
            month=month,
            card=snapshot,
            energy=self._energy_for(snapshot),
            table=self._index_table,
            dso=household.dso,
            annual_kwh=household.annual_kwh,
            caliber=household.caliber,
            kwh=0.0,
            days=0,
            days_in_year=365,
        )
        fixed = fixed_costs(
            replace(resolve_for_delivery(snapshot, today), energy=self._energy_for(snapshot)),
            household.dso,
            household.annual_kwh,
            household.caliber,
        )
        self.household = household
        index: IndexValue | None = now_bill.index
        age = self.snapshot_age()
        rolling = None if costs is None else costs.rolling_year_kwh
        all_bills = tuple(b for period in earlier for b in period.months) + (
            () if costs is None else costs.months
        )
        earlier_cost = sum(period.current_year_cost for period in earlier)
        earlier_kwh = sum(period.ytd_kwh for period in earlier)
        year_end = None if costs is None else costs.projected_year_end_cost
        year_kwh = None if costs is None else costs.projected_year_kwh
        return CoordinatorData(
            snapshot=snapshot,
            card_source=self._card_source,
            breakdown=now_bill.breakdown,
            fixed=fixed,
            index=index,
            price_provisional=now_bill.provisional,
            conversion=self._conversion(month),
            tier=tier_for(household.annual_kwh),
            annual_kwh=household.annual_kwh,
            annual_kwh_measured=measured,
            snapshot_fetched_at=self._fetched_at,
            snapshot_age_hours=None if age is None else age.total_seconds() / 3600,
            snapshot_stale=self.snapshot_stale(),
            last_error=self.last_error,
            day=today,
            current_year_cost=None if costs is None else costs.current_year_cost + earlier_cost,
            current_month_cost=(
                None if costs is None else sum(b.total for b in all_bills if b.month == month)
            ),
            ytd_kwh=None if costs is None else costs.ytd_kwh + earlier_kwh,
            months=all_bills,
            # Every contract's months in order, one shared by two named once.
            months_on_current_card=tuple(
                dict.fromkeys(
                    [m for period in earlier for m in period.months_on_current_card]
                    + ([] if costs is None else list(costs.months_on_current_card))
                )
            ),
            rolling_year_kwh=rolling,
            projected_year_cost=(
                None if rolling is None else rolling * now_bill.breakdown.all_in + fixed.total
            ),
            projected_year_end_cost=None if year_end is None else year_end + earlier_cost,
            projected_year_kwh=None if year_kwh is None else year_kwh + earlier_kwh,
            meter=self.meter,
            unpriced_periods=tuple(self.unpriced_periods),
        )
