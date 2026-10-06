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

"""Long-term-statistics backfill for be_water_prices price sensors.

The History dashboard and the Energy dashboard's tariff overlays draw
their multi-day chart from the recorder's hourly long-term-statistics
table. A fresh config entry starts with that table empty, so the price
line only appears from the install moment forward.

This module backfills hourly rows from the configured start
(default Jan 1 of the current year) up to the previous full hour,
flat-lining at the currently-known tariff value for every
``MEASUREMENT``-class price sensor on the entry. The ``TOTAL`` YTD
sensors depend on the user's actual meter history and are intentionally
excluded -- synthesising them would invent consumption.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import WaterCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_BACKFILL_PRICES = "backfill_prices"
ATTR_ENTRY_ID = "entry_id"
ATTR_START_DATE = "start_date"
ATTR_CLEAR = "clear"

# Persisted on entry.data once a year has been backfilled, so the
# auto-once path skips on subsequent HA restarts. When the calendar year
# rolls over, the value will no longer match and the next setup extends
# the flat line into the new year automatically.
DATA_BACKFILL_YEAR = "backfill_year"

# How many hourly rows to build between yields to the event loop.
_BACKFILL_YIELD_EVERY = 744  # a long month

# Sensor keys eligible for backfill: the card's rates and fee, read
# straight off the latest tariff. The meter-driven sensors are excluded on
# purpose, since their values come from the user's water meter history,
# and so is the projected annual cost, which is computed from the
# configured consumption rather than read off the card.
_BACKFILL_KEYS: tuple[str, ...] = (
    "yearly_fee",
    "basis_rate",
    "comfort_rate",
    "sanering_rate",
    "all_in_basis",
)


SERVICE_BACKFILL_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Optional(ATTR_START_DATE): cv.date,
        vol.Optional(ATTR_CLEAR, default=False): cv.boolean,
    }
)


def _jan_1_local() -> datetime:
    return dt_util.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


async def async_backfill_prices(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    start: datetime,
    clear: bool = False,
) -> int:
    """Import flat-line hourly stats for this entry's MEASUREMENT price sensors.

    ``start`` is clamped to ``max(start, tariff.valid_from)`` so the
    backfill never invents prices for a period where no tariff snapshot
    existed. With ``clear=True`` the targeted ``statistic_id`` rows are
    wiped first; otherwise the import upserts on (statistic_id, start)
    and is safely idempotent.

    Returns the total number of rows handed to the recorder.
    """
    try:
        # mypy --strict flags these because the recorder module does not
        # re-export them via __all__; the same pattern as in coordinator.py.
        from homeassistant.components.recorder import (  # type: ignore[attr-defined]
            get_instance,
        )
        from homeassistant.components.recorder.models import (  # type: ignore[attr-defined,unused-ignore]
            StatisticData,
            StatisticMeanType,
            StatisticMetaData,
        )
        from homeassistant.components.recorder.statistics import (
            async_import_statistics,
        )
        from homeassistant.helpers.recorder import DATA_INSTANCE
    except ImportError:
        _LOGGER.warning("recorder unavailable; skipping price backfill")
        return 0

    # Skip cleanly when the recorder hasn't been initialised yet (e.g.
    # the pytest_homeassistant_custom_component harness without the
    # recorder fixture). Without this gate get_instance() throws
    # KeyError mid-import and propagates out of async_setup_entry.
    if DATA_INSTANCE not in hass.data:
        _LOGGER.debug("recorder not initialised; skipping price backfill")
        return 0

    from .sensor import SENSORS  # local import: sensor.py imports from coordinator

    coordinator: WaterCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is None or coordinator.data is None:
        _LOGGER.debug("coordinator not ready for %s; skipping backfill", entry.entry_id)
        return 0

    data = coordinator.data
    tariff = data.tariff

    tz = dt_util.DEFAULT_TIME_ZONE
    valid_from_dt = datetime(
        tariff.valid_from.year,
        tariff.valid_from.month,
        tariff.valid_from.day,
        tzinfo=tz,
    )
    if start.tzinfo is None:
        start = start.replace(tzinfo=tz)
    if start < valid_from_dt:
        start = valid_from_dt

    start_utc = start.astimezone(dt_util.UTC).replace(minute=0, second=0, microsecond=0)
    end_utc = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
    # Clamp the far end to the snapshot too. Only the near end was
    # clamped, so on a year rollover against a page that has not
    # published the new year yet, last year's rates were flat-lined
    # across January as though they still applied.
    if tariff.valid_until is not None:
        # The card runs to the end of its last day, so the exclusive end
        # is the midnight after it. Clamping at 23:00 left the last hour
        # of every card unwritten.
        valid_until_dt = (
            datetime(
                tariff.valid_until.year,
                tariff.valid_until.month,
                tariff.valid_until.day,
                tzinfo=tz,
            )
            + timedelta(days=1)
        ).astimezone(dt_util.UTC)
        end_utc = min(end_utc, valid_until_dt.replace(minute=0, second=0, microsecond=0))
    if end_utc <= start_utc:
        # Nothing to write, and with clear=True nothing was cleared
        # either: say why, or the service call ends in silence.
        _LOGGER.info(
            "be_water_prices backfill for %s: start %s is not before the window's end %s; "
            "nothing written or cleared",
            entry.entry_id,
            start_utc.isoformat(),
            end_utc.isoformat(),
        )
        return 0

    ent_reg = er.async_get(hass)
    rows_total = 0

    cleared_done = False
    for desc in SENSORS:
        if desc.key not in _BACKFILL_KEYS:
            continue
        unique_id = f"{entry.entry_id}_{desc.key}"
        entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
        if entity_id is None:
            # Sensor not created for this entry (e.g. comfort_rate outside Flanders).
            continue
        value = desc.value_fn(data)
        if value is None:
            continue

        if clear:
            # ``async_clear_statistics`` is an instance method on the
            # Recorder (not exported from ``recorder.statistics``); call
            # it through get_instance(hass). Schedules the delete on the
            # recorder executor so we do not block the event loop.
            get_instance(hass).async_clear_statistics([entity_id])
            cleared_done = True

        bucket = start_utc
        rows: list[StatisticData] = []
        while bucket < end_utc:
            rows.append(
                StatisticData(
                    start=bucket,
                    mean=float(value),
                    min=float(value),
                    max=float(value),
                )
            )
            bucket += timedelta(hours=1)
            # A full year is ~8760 rows per sensor and five sensors run
            # through this loop, so building them in one go held the
            # event loop for a third of a second on this hardware. Give
            # it air every month's worth.
            if len(rows) % _BACKFILL_YIELD_EVERY == 0:
                await asyncio.sleep(0)

        metadata = StatisticMetaData(
            statistic_id=entity_id,
            source="recorder",
            name=None,
            unit_of_measurement=desc.native_unit_of_measurement,
            has_mean=True,
            mean_type=StatisticMeanType.ARITHMETIC,
            has_sum=False,
            unit_class=None,
        )
        async_import_statistics(hass, metadata, rows)
        rows_total += len(rows)

    _LOGGER.info(
        "be_water_prices backfill for %s: %d rows%s",
        entry.entry_id,
        rows_total,
        " (cleared first)" if cleared_done else "",
    )
    return rows_total


async def _async_has_statistics_before(
    hass: HomeAssistant, entity_id: str, cutoff: datetime
) -> bool:
    """Whether ``entity_id`` carries long-term rows older than ``cutoff``."""
    from homeassistant.components.recorder import (  # type: ignore[attr-defined]
        get_instance,
    )
    from homeassistant.components.recorder.statistics import (
        statistics_during_period,
    )

    instance = get_instance(hass)
    try:
        stats = await instance.async_add_executor_job(
            statistics_during_period,
            hass,
            datetime(1970, 1, 1, tzinfo=dt_util.UTC),
            cutoff,
            {entity_id},
            "month",
            None,
            {"mean"},
        )
    except Exception as err:
        # Any failure here means we cannot prove the history is empty, so
        # keep the rows rather than risk deleting years of real data.
        _LOGGER.debug("could not read history for %s: %s", entity_id, err)
        return True
    return bool(stats.get(entity_id))


async def _async_clear_orphan_backfill_keys(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clear LTS rows for backfill keys the *current* operator's tariff
    does not produce (orphan rows left over by the previous operator).

    The recorder only offers a whole-statistic delete, so this refuses to
    run for any key that carries rows from an earlier year: those are a
    genuine record of what the household paid under the old operator and
    losing them is worse than leaving a stale line behind. Only a key
    whose entire history sits inside the current year -- the flat line the
    previous operator's backfill just wrote -- is cleared.
    """
    # mypy --strict flags get_instance because the recorder module does
    # not re-export it via __all__; same pattern as async_backfill_prices.
    from homeassistant.components.recorder import (  # type: ignore[attr-defined]
        get_instance,
    )
    from homeassistant.helpers.recorder import DATA_INSTANCE

    from .sensor import SENSORS  # local import: sensor.py imports from coordinator

    # Same guard pattern async_backfill_prices uses: skip cleanly when
    # the recorder is not yet up (cold-boot, test harness without the
    # recorder fixture). Without this the get_instance() call below
    # raises KeyError mid-setup, escaping async_setup_entry and
    # leaving the OptionsFlow reload listener unregistered.
    if DATA_INSTANCE not in hass.data:
        return

    coordinator: WaterCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is None or coordinator.data is None:
        return
    ent_reg = er.async_get(hass)
    recorder = get_instance(hass)
    year_start = dt_util.start_of_local_day(
        datetime(dt_util.now().year, 1, 1, tzinfo=dt_util.DEFAULT_TIME_ZONE)
    ).astimezone(dt_util.UTC)
    for desc in SENSORS:
        if desc.key not in _BACKFILL_KEYS:
            continue
        # Current operator's tariff doesn't produce this metric ->
        # any LTS rows are orphans from the previous operator.
        if desc.value_fn(coordinator.data) is not None:
            continue
        unique_id = f"{entry.entry_id}_{desc.key}"
        entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
        if entity_id is None:
            continue
        if await _async_has_statistics_before(hass, entity_id, year_start):
            _LOGGER.debug(
                "keeping %s: it holds history from before %s", entity_id, year_start.date()
            )
            continue
        recorder.async_clear_statistics([entity_id])


async def async_maybe_backfill_once(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Run the auto-once backfill, gated by ``(year, utility)``.

    The flag records the calendar year the entry was last backfilled, the
    utility it was backfilled for, and the year of the card the rates came
    off. When the year rolls over, OR the user reconfigures to a different
    operator (postcode-resolver move, manual override, split-postcode
    choice), OR the operator finally publishes the new year's card, the
    gate trips again and the fresh flat line replaces the old one rather
    than mixing rates inside the same calendar year.
    """
    from .const import CONF_COMMUNE, CONF_UTILITY

    coordinator_now: WaterCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    current_year = dt_util.now().year
    current_utility = entry.data.get(CONF_UTILITY)
    # The card's own year is part of the gate. Publishers run late, and
    # carry_prior_year_card lets last year's card stand until 31 March, so
    # in January the flat line is written at last year's rate and the gate
    # was stamped for the calendar year: when the real card arrived in
    # March the gate already matched and nothing ever corrected the line.
    card_year = (
        coordinator_now.data.tariff.valid_from.year
        if coordinator_now is not None and coordinator_now.data is not None
        else None
    )
    # The commune belongs here too. Several of the sensors this writes are
    # made of it: the gemeentelijke saneringsbijdrage is a commune's own
    # number, so sanering_rate and all_in_basis move with it. A household
    # that installs, gets the operator default flat-lined, and then picks
    # its own commune kept the default's rates in History for the rest of
    # the year, 0.59 EUR/m3 out on De Watergroep at Overijse and 0.66 on
    # Water-link at Edegem. Appended rather than inserted: the orphan
    # cleanup below reads the utility out of field one.
    current_commune = entry.options.get(CONF_COMMUNE)
    current_gate = f"{current_year}:{current_utility}:{card_year}:{current_commune}"
    previous_gate = entry.data.get(DATA_BACKFILL_YEAR)
    if previous_gate == current_gate:
        return

    # On operator change, any LTS rows the previous operator wrote for
    # sensor keys that the new operator does not produce (e.g.
    # comfort_rate after Flanders -> Wallonia) become orphans: the
    # entity may be removed from the registry but its historical rows
    # persist forever because the new backfill loop skips them. Detect
    # the orphans by checking each backfill key's value_fn against the
    # current tariff and clear the stale rows. This runs before the
    # stale-snapshot deferral below: the cleanup finds the rows through
    # the registry entry that setup removes right after this, so a
    # deferred cleanup never got a second chance.
    if isinstance(previous_gate, str) and ":" in previous_gate:
        # "<year>:<utility>" first, then the card year joined it, then the
        # commune. A utility id never contains a colon and every term since
        # has been appended, so the second field is the utility whichever
        # release wrote the string.
        previous_utility = previous_gate.split(":")[1]
        if previous_utility != str(current_utility):
            await _async_clear_orphan_backfill_keys(hass, entry)

    coordinator: WaterCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is not None and coordinator.data is not None and coordinator.data.snapshot_stale:
        # The snapshot cannot cover the window we are about to fill, and
        # stamping the gate anyway would lock in whatever we wrote: the
        # gate is keyed on (year, utility), so a later run with a fresh
        # tariff would find it already satisfied and never correct the
        # line. Leave it unstamped and retry on the next setup.
        _LOGGER.debug("snapshot is stale; deferring the auto-once backfill for %s", entry.entry_id)
        return

    # ``clear=False`` is sufficient: async_import_statistics overwrites
    # rows at matching (statistic_id, bucket_start) timestamps, so
    # re-running for the same year just replaces the old operator's
    # flat-line for Jan 1..now without wiping older historical rows
    # (prior years, manual annotations). The flatline replacement is
    # what we actually want on an operator switch.
    rows = await async_backfill_prices(hass, entry, start=_jan_1_local(), clear=False)
    if rows <= 0:
        return

    hass.config_entries.async_update_entry(
        entry,
        data={**entry.data, DATA_BACKFILL_YEAR: current_gate},
    )


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register the ``backfill_prices`` service if not already registered."""
    if hass.services.has_service(DOMAIN, SERVICE_BACKFILL_PRICES):
        return

    async def _handle_backfill(call: ServiceCall) -> None:
        entries_data: dict[str, Any] = hass.data.get(DOMAIN, {})

        target_id = call.data.get(ATTR_ENTRY_ID)
        clear = bool(call.data.get(ATTR_CLEAR, False))
        # clear=True wipes the long-term-statistics rows for every
        # backfill key on every targeted entry. Without an explicit
        # entry_id the operation cascades across the user's entire
        # be_water_prices install -- a footgun that's irreversible.
        # Refuse the blanket combination loudly so the user has to
        # opt in per-entry.
        if clear and not target_id:
            raise vol.Invalid(
                "backfill_prices: clear=true requires an explicit entry_id"
                " (refuses to wipe long-term-statistics for every loaded entry)"
            )
        if target_id:
            target_ids = [target_id] if target_id in entries_data else []
            if not target_ids:
                _LOGGER.warning("backfill_prices: no loaded entry %s", target_id)
        else:
            target_ids = list(entries_data.keys())

        start_date = call.data.get(ATTR_START_DATE)
        if start_date is not None:
            start_dt = datetime(
                start_date.year,
                start_date.month,
                start_date.day,
                tzinfo=dt_util.DEFAULT_TIME_ZONE,
            )
        else:
            start_dt = _jan_1_local()

        for entry_id in target_ids:
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                continue
            await async_backfill_prices(hass, entry, start=start_dt, clear=clear)

    hass.services.async_register(
        DOMAIN,
        SERVICE_BACKFILL_PRICES,
        _handle_backfill,
        schema=SERVICE_BACKFILL_SCHEMA,
    )


@callback
def async_unregister_services(hass: HomeAssistant) -> None:
    """Drop the service when the last entry of this integration unloads."""
    if hass.services.has_service(DOMAIN, SERVICE_BACKFILL_PRICES):
        hass.services.async_remove(DOMAIN, SERVICE_BACKFILL_PRICES)
