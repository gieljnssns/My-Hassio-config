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

"""Reading the household's gas meter out of Home Assistant.

A gas meter reaches Home Assistant either as a volume (a P1 reader reports
m3; some meters litres or cubic feet) or as energy (an integration that has
already converted to kWh). Both are what the Energy dashboard accepts for a
gas source, and both are read here: the recorder converts a volume to m3 and
an energy to kWh, and the caller decides what a cubic metre is worth.

Everything is read from long-term statistics, whose ``change`` per bucket
already carries a ``total_increasing`` meter across its resets.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, date, datetime, timedelta
from functools import partial
from typing import Any, Literal

from homeassistant.const import UnitOfEnergy, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import EnergyConverter, VolumeConverter

_LOGGER = logging.getLogger(__name__)

MeterKind = Literal["volume", "energy"]

# A volume reported with no unit, or in the ASCII spelling of cubic metres,
# is cubic metres already: there is nothing to convert and nothing to misread.
_ALREADY_CUBIC_METRES = frozenset({None, "m3"})

# How long a coordinator tick waits for the energy manager singleton. A failed
# first load of .storage/energy leaves it waiting forever, and one tick is the
# most that should cost.
_ENERGY_MANAGER_TIMEOUT_S = 10.0


class RecorderUnavailable(Exception):
    """A running recorder could not answer, or the meter's unit is unusable."""


def meter_kind(unit: str | None) -> MeterKind | None:
    """Whether a meter reporting ``unit`` counts volume or energy, or None
    for a unit Home Assistant cannot convert to either."""
    if unit in VolumeConverter.VALID_UNITS or unit in _ALREADY_CUBIC_METRES:
        return "volume"
    if unit in EnergyConverter.VALID_UNITS:
        return "energy"
    return None


async def discover_energy_gas_meter(hass: HomeAssistant) -> tuple[str | None, int]:
    """The first gas source of the Energy dashboard, and how many it lists.

    (None, 0) when none is configured or the energy component is not
    available. One meter is billed; the count lets the caller say that the
    others are ignored.
    """
    try:
        from homeassistant.components.energy import (  # type: ignore[attr-defined]
            async_get_manager,
        )
    except ImportError:
        return None, 0
    try:
        async with asyncio.timeout(_ENERGY_MANAGER_TIMEOUT_S):
            manager = await async_get_manager(hass)
    except Exception as err:  # a timeout, or whatever the energy component raised
        _LOGGER.debug("energy manager unavailable: %s", err)
        return None, 0
    data = getattr(manager, "data", None)
    if not data:
        return None, 0
    stats = [
        str(source["stat_energy_from"])
        for source in data.get("energy_sources") or []
        if isinstance(source, dict)
        and source.get("type") == "gas"
        and source.get("stat_energy_from")
    ]
    if not stats:
        return None, 0
    return stats[0], len(stats)


def _recorder(hass: HomeAssistant) -> Any | None:
    """The running recorder, or None where there is none and never will be."""
    try:
        from homeassistant.components.recorder import (  # type: ignore[attr-defined]
            get_instance,
        )
    except ImportError:
        return None
    try:
        return get_instance(hass)
    except Exception as err:  # importable but not running
        _LOGGER.debug("no recorder instance: %s", err)
        return None


async def statistic_kind(hass: HomeAssistant, statistic_id: str) -> MeterKind | None:
    """The kind of meter behind ``statistic_id``, read off its statistics.

    None when there are no statistics yet (nothing to read, nothing to
    misread). Raises :class:`RecorderUnavailable` for a unit Home Assistant
    cannot convert: asked to convert one, the recorder would hand the figures
    back untouched and unremarked, so litres typed as "l" would be read as
    cubic metres.
    """
    instance = _recorder(hass)
    if instance is None:
        return None
    from homeassistant.components.recorder.statistics import get_metadata

    try:
        metadata = await instance.async_add_executor_job(
            partial(get_metadata, hass, statistic_ids={statistic_id})
        )
    except Exception as err:
        raise RecorderUnavailable(f"could not read the unit of {statistic_id}: {err}") from err
    entry = metadata.get(statistic_id)
    if entry is None:
        return None
    unit = entry[1].get("unit_of_measurement")
    kind = meter_kind(unit)
    if kind is None:
        raise RecorderUnavailable(
            f"{statistic_id} records statistics in {unit!r}, which Home Assistant "
            "can convert neither to a volume nor to an energy"
        )
    return kind


def _target_units(kind: MeterKind) -> dict[str, str]:
    if kind == "volume":
        return {VolumeConverter.UNIT_CLASS: UnitOfVolume.CUBIC_METERS}
    return {EnergyConverter.UNIT_CLASS: UnitOfEnergy.KILO_WATT_HOUR}


async def daily_consumption(
    hass: HomeAssistant,
    statistic_id: str,
    kind: MeterKind,
    start: date,
    end: date,
) -> dict[date, float]:
    """Consumption per local day over [start, end], in m3 or kWh by ``kind``.

    Days the recorder holds nothing for are absent. A negative change is a
    ``total`` meter that was replaced or re-based, never gas flowing back,
    and counts as none. Raises :class:`RecorderUnavailable` when a running
    recorder could not answer; returns {} when there is no recorder.
    """
    instance = _recorder(hass)
    if instance is None or end < start:
        return {}
    from homeassistant.components.recorder.statistics import statistics_during_period

    start_dt = dt_util.start_of_local_day(start).astimezone(UTC)
    end_dt = dt_util.start_of_local_day(end + timedelta(days=1)).astimezone(UTC)
    try:
        stats = await instance.async_add_executor_job(
            statistics_during_period,
            hass,
            start_dt,
            end_dt,
            {statistic_id},
            "day",
            _target_units(kind),
            {"change"},
        )
    except Exception as err:
        raise RecorderUnavailable(f"recorder query for {statistic_id} failed: {err}") from err
    out: dict[date, float] = {}
    for row in stats.get(statistic_id, []):
        change = row.get("change")
        if change is None:
            continue
        day = dt_util.as_local(datetime.fromtimestamp(row["start"], UTC)).date()
        out[day] = max(0.0, float(change))
    return out
