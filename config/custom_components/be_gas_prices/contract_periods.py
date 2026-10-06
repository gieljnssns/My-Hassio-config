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

"""The contracts a household held earlier in the year.

When a household changes supplier, the options flow records the settings it
had and the last day they applied, so the year's running cost bills each day
on the contract that supplied it. Each earlier contract is priced on its own
supplier's cards, month by month, the way the current one is.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import date, timedelta
from typing import Any

import aiohttp

from .bill import contract_leg, month_key
from .const import (
    CONF_CALIBER,
    CONF_CONTRACT,
    CONF_CONTRACT_END_DATE,
    CONF_CONTRACT_START_DATE,
    CONF_CUSTOM_PRICE,
    CONF_DSO,
    CONF_PREVIOUS_CONTRACTS,
    CONF_REGION,
    CONF_SUPPLIER,
    CONF_TARIFF_CARD_DATE,
    CONF_YTD_FROM_CONTRACT_START,
    CUSTOM_KEYS,
    DEFAULT_CALIBER,
    MANUAL_RATE_KEYS,
    SUPPLIER_CUSTOM,
)
from .month_cards import ArchiveUnavailable, MonthCardCache, current_card, fetch_archived_card
from .pricing import PricingError
from .providers._pdf import is_transient_fetch_error
from .providers._rates import EnergyRates
from .providers.base import (
    CardNotReadableError,
    ExtractorError,
    IndexTable,
    SupplierExtractor,
    SupplierSnapshot,
)
from .providers.custom import build_snapshot as build_custom_snapshot
from .running_costs import Household, RunningCosts, running_costs
from .running_costs import months_between as _months_between

_LOGGER = logging.getLogger(__name__)

# What an earlier contract keeps of the entry: enough to price it the way
# the current one is, on its signing card and the figures typed from it, or
# on the card typed for the custom supplier; nothing about the meter, which
# stays the household's.
PERIOD_KEYS = (
    CONF_SUPPLIER,
    CONF_CONTRACT,
    CONF_REGION,
    CONF_DSO,
    CONF_CALIBER,
    CONF_CONTRACT_START_DATE,
    CONF_TARIFF_CARD_DATE,
    CONF_YTD_FROM_CONTRACT_START,
    *MANUAL_RATE_KEYS,
    *CUSTOM_KEYS,
)


def parse_date(value: Any) -> date | None:
    """An ISO date from the entry, or None for a missing or malformed one."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def signing_month(data: Mapping[str, Any]) -> str | None:
    """The month of the card a contract was signed on, if its settings say:
    the tariff card month, else the month the contract started."""
    signed = parse_date(data.get(CONF_TARIFF_CARD_DATE)) or parse_date(
        data.get(CONF_CONTRACT_START_DATE)
    )
    return None if signed is None else month_key(signed)


def previous_contracts(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The recorded earlier contracts, oldest first, each with a valid
    ``until`` date; anything malformed is left out rather than guessed."""
    out: list[dict[str, Any]] = []
    for period in data.get(CONF_PREVIOUS_CONTRACTS) or []:
        if not isinstance(period, dict):
            continue
        try:
            date.fromisoformat(str(period["until"]))
        except (KeyError, ValueError):
            continue
        if period.get(CONF_SUPPLIER) and period.get(CONF_CONTRACT) and period.get(CONF_DSO):
            out.append(period)
    return sorted(out, key=lambda period: str(period["until"]))


def record_switch(data: dict[str, Any], switched: date) -> dict[str, Any]:
    """The entry's data with its current contract moved into the earlier
    contracts, ending the day before ``switched``, and the new contract
    starting on it. The caller then asks for the new contract's settings."""
    period = {key: data[key] for key in PERIOD_KEYS if key in data}
    period["until"] = (switched - timedelta(days=1)).isoformat()
    new = dict(data)
    new[CONF_PREVIOUS_CONTRACTS] = [*previous_contracts(data), period]
    new[CONF_CONTRACT_START_DATE] = switched.isoformat()
    # The old contract's card month, end date and typed figures are not the
    # new one's: left in, the next steps would offer them for it.
    for key in (CONF_TARIFF_CARD_DATE, CONF_CONTRACT_END_DATE, *MANUAL_RATE_KEYS):
        new.pop(key, None)
    # The year now starts with the earlier contract, so counting it from the
    # new contract's start would drop the days the earlier one supplied.
    new.pop(CONF_YTD_FROM_CONTRACT_START, None)
    return new


def periods_this_year(data: dict[str, Any], today: date) -> list[tuple[dict[str, Any], date, date]]:
    """Each earlier contract that supplied part of this year, with the first
    and last day of it that falls in the year. One the entry billed from its
    contract start is billed from that day, as it was before the switch."""
    year_start = date(today.year, 1, 1)
    out: list[tuple[dict[str, Any], date, date]] = []
    start = year_start
    for period in previous_contracts(data):
        until = date.fromisoformat(str(period["until"]))
        first = start
        began = parse_date(period.get(CONF_CONTRACT_START_DATE))
        if period.get(CONF_YTD_FROM_CONTRACT_START) and began is not None:
            first = max(start, began)
        if until >= year_start and until >= first:
            out.append((period, first, min(until, today)))
        start = max(start, until + timedelta(days=1))
    return out


def current_period_start(data: dict[str, Any], default: date, today: date) -> date:
    """The first day the current contract supplied this year: the day after
    the last earlier contract ended, or ``default``."""
    periods = periods_this_year(data, today)
    if not periods:
        return default
    return max(default, periods[-1][2] + timedelta(days=1))


class PeriodBilling:
    """Prices the earlier contracts of the year on their own suppliers' cards.

    Their current cards and index tables are read once a day and kept here;
    a card not read, and an index table a failure a retry may cure (network,
    storage, HTTP 5xx, 403, 408, 429) kept from a supplier with none held,
    are asked again on the next tick. Their past
    months come from the entry's month card cache, which is keyed by
    supplier and contract already.
    """

    def __init__(self, months: MonthCardCache) -> None:
        self._months = months
        self._cards: dict[tuple[str, str, str], tuple[date, SupplierSnapshot]] = {}
        self._tables: dict[str, tuple[date, IndexTable | None]] = {}

    async def _current_card(
        self,
        session: aiohttp.ClientSession,
        extractor: SupplierExtractor,
        contract: str,
        region: str,
        today: date,
        use_archive: bool,
    ) -> SupplierSnapshot | None:
        key = (extractor.id, contract, region)
        held = self._cards.get(key)
        if held is not None and held[0] == today:
            return held[1]
        try:
            card, _source = await current_card(
                session, extractor, contract, region, f"{today:%Y-%m}", use_archive=use_archive
            )
        except ExtractorError as err:
            _LOGGER.debug("%s card for an earlier contract not read: %s", extractor.label, err)
            if held is not None:
                return held[1]
            if not use_archive or isinstance(err, CardNotReadableError):
                # current_card asks the archive itself for a card it
                # cannot read.
                return None
            # Nothing held, as after a restart: the card archive's row for
            # the month stands in, as it does for the entry's own card, and
            # the supplier is asked again next tick.
            try:
                return await fetch_archived_card(
                    session, extractor.id, contract, region, f"{today:%Y-%m}"
                )
            except ArchiveUnavailable:
                return None
        self._cards[key] = (today, card)
        return card

    async def _table(
        self, session: aiohttp.ClientSession, extractor: SupplierExtractor, today: date
    ) -> IndexTable | None:
        held = self._tables.get(extractor.id)
        if held is not None and held[0] == today:
            return held[1]
        table = None
        if extractor.fetch_index is not None:
            try:
                table = await extractor.fetch_index(session)
            except ExtractorError as err:
                _LOGGER.debug("%s index values not read: %s", extractor.label, err)
                if (held is None or held[1] is None) and is_transient_fetch_error(str(err)):
                    # Nothing held, and the source may answer the next time:
                    # asked again next tick, like a card not read.
                    return None
                # A held table keeps pricing, and a page the parser refuses
                # will be refused next hour too: asked again tomorrow.
                table = None if held is None else held[1]
        self._tables[extractor.id] = (today, table)
        return table

    async def fill(
        self,
        session: aiohttp.ClientSession,
        data: dict[str, Any],
        today: date,
        *,
        use_archive: bool,
    ) -> None:
        """Fetch the closed months' cards each earlier contract is billed on,
        its signing month's included, into the month cache."""
        from .providers import get as get_extractor

        current = month_key(today)
        for period, start, end in periods_this_year(data, today):
            try:
                extractor = get_extractor(str(period[CONF_SUPPLIER]))
            except ExtractorError:
                continue
            if extractor.id == SUPPLIER_CUSTOM:
                # The typed card prices every month the contract supplied.
                continue
            contract = str(period[CONF_CONTRACT])
            region = str(period[CONF_REGION])
            wanted = _months_between(start, end)
            signing = signing_month(period)
            if signing is not None and signing not in wanted:
                wanted.append(signing)
            for month in wanted:
                if month < current:
                    try:
                        await self._months.card(
                            session, extractor, contract, region, month, use_archive=use_archive
                        )
                    except (ExtractorError, ArchiveUnavailable) as err:
                        _LOGGER.debug("%s card for %s not read: %s", extractor.label, month, err)

    async def bill(
        self,
        session: aiohttp.ClientSession,
        data: dict[str, Any],
        today: date,
        kwh_days: Mapping[date, float],
        annual_kwh: float,
        *,
        use_archive: bool,
        fill: bool = True,
    ) -> tuple[list[RunningCosts], list[str]]:
        """What each earlier contract of the year cost, and the ones that
        could not be priced (their supplier is gone or its card unreadable).
        ``fill`` fetches their months' cards first. A month without a card of
        its own is priced on the contract's last month's card, or on today's
        while that one is not held or cannot price the household."""
        from .providers import get as get_extractor

        if fill:
            await self.fill(session, data, today, use_archive=use_archive)
        costs: list[RunningCosts] = []
        missing: list[str] = []
        # One index read per supplier and tick, however many earlier
        # contracts it supplied.
        tables: dict[str, IndexTable | None] = {}
        current = month_key(today)
        for period, start, end in periods_this_year(data, today):
            try:
                extractor = get_extractor(str(period[CONF_SUPPLIER]))
            except ExtractorError:
                missing.append(str(period[CONF_SUPPLIER]))
                continue
            contract = str(period[CONF_CONTRACT])
            region = str(period[CONF_REGION])
            custom = extractor.id == SUPPLIER_CUSTOM
            if custom and CONF_CUSTOM_PRICE not in period:
                # Recorded before a switch kept the typed card.
                missing.append(extractor.label)
                continue
            signing = None if custom else signing_month(period)

            # The typed card prices every month a custom contract supplied,
            # as each month's own card.
            typed = build_custom_snapshot(period) if custom else None

            def month_card(
                month: str,
                _e: str = extractor.id,
                _c: str = contract,
                _r: str = region,
                _typed: SupplierSnapshot | None = typed,
            ) -> SupplierSnapshot | None:
                if _typed is not None:
                    return _typed
                row = self._months.get(_e, _c, _r, month)
                return None if row is None else row.snapshot

            end_card = typed
            if end_card is None and month_key(end) < current:
                end_card = month_card(month_key(end))
            # A closed last month without its own card is billed on today's,
            # and named with the other months billed that way.
            end_on_current = end_card is None and month_key(end) < current
            if end_card is None:
                end_card = await self._current_card(
                    session, extractor, contract, region, today, use_archive
                )
            if end_card is None:
                missing.append(extractor.label)
                continue
            if extractor.id not in tables:
                tables[extractor.id] = await self._table(session, extractor, today)
            table = tables[extractor.id]
            signed: SupplierSnapshot | None = None
            if signing is not None and signing < current:
                signed = month_card(signing)
            elif signing is not None and month_key(end) == current:
                # The running month's card, read above for the last month.
                signed = end_card
            elif signing is not None:
                signed = await self._current_card(
                    session, extractor, contract, region, today, use_archive
                )

            def energy_for(
                card: SupplierSnapshot,
                _signed: EnergyRates | None = None if signed is None else signed.energy,
                _table: IndexTable | None = table,
                _data: dict[str, Any] = period,
            ) -> EnergyRates:
                return contract_leg(card.energy, _signed, _table, _data)

            household = Household(
                dso=str(period[CONF_DSO]),
                caliber=str(period.get(CONF_CALIBER, DEFAULT_CALIBER)),
                annual_kwh=annual_kwh,
            )

            def cost_on(
                card: SupplierSnapshot,
                _start: date = start,
                _end: date = end,
                _household: Household = household,
                _month_card: Callable[[str], SupplierSnapshot | None] = month_card,
                _energy_for: Callable[[SupplierSnapshot], EnergyRates] = energy_for,
                _table: IndexTable | None = table,
            ) -> RunningCosts:
                return running_costs(
                    kwh_days=kwh_days,
                    today=_end,
                    window_start=_start,
                    household=_household,
                    current_card=card,
                    month_card=_month_card,
                    energy_for=_energy_for,
                    table=_table,
                )

            cost: RunningCosts | None = None
            try:
                cost = cost_on(end_card)
            except PricingError as err:
                # The last month's own card cannot price the household (an
                # archived card missing its DSO row or tier): today's card
                # stands in for it and for every month it stood in for.
                fallback = None
                if not custom and not end_on_current and month_key(end) < current:
                    fallback = await self._current_card(
                        session, extractor, contract, region, today, use_archive
                    )
                if fallback is not None:
                    with contextlib.suppress(PricingError):
                        cost = cost_on(fallback)
                if cost is None:
                    _LOGGER.warning("%s: earlier contract not priced: %s", extractor.label, err)
                    missing.append(extractor.label)
                    continue
                end_on_current = True
            if end_on_current:
                cost = replace(
                    cost,
                    months_on_current_card=(*cost.months_on_current_card, month_key(end)),
                )
            costs.append(cost)
        return costs, missing
