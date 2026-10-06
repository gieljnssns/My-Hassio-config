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

"""Daily-refresh coordinator for be_water_prices."""

from __future__ import annotations

import asyncio
import calendar
import json
import logging
import math
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta
from functools import partial
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfVolume,
)
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import VolumeConverter

from ._redact import scrub_tokens, sensitive_tokens, source_url_without_commune
from .const import (
    CARD_ARCHIVE_URL,
    CONF_CARD_ARCHIVE,
    CONF_COMMUNE,
    CONF_COMMUNE_LABEL,
    CONF_CONSUMPTION_M3_PER_YEAR,
    CONF_PERSONS,
    CONF_POSTCODE,
    CONF_SOCIAL_TARIFF,
    CONF_UTILITY,
    CONF_WATER_METER_SENSOR,
    DEFAULT_CARD_ARCHIVE,
    DEFAULT_CONSUMPTION_M3,
    DEFAULT_PERSONS,
    DOMAIN,
    INTEGRATION_VERSION,
    MAX_CONSUMPTION_M3,
    MIN_CONSUMPTION_M3,
    PROJECTION_DRIFT_RATIO,
    SNAPSHOT_STALE_AFTER_DAYS,
    UPDATE_INTERVAL_HOURS,
)
from .pricing import compute_annual_cost, compute_ytd_cost
from .providers import ExtractorError, TransientFetchError, WaterTariff, get
from .providers._pdf import fetch_text
from .providers._postcodes import resolve_candidates
from .providers.base import WaterExtractor, relabel_with_human_commune, tariff_from_dict

if TYPE_CHECKING:
    import aiohttp

_LOGGER = logging.getLogger(__name__)

# How long one tariff fetch may take, parse included. The per-request
# timeouts bound the network, not the parse: a page-long content stream
# kept pdfplumber busy for ten minutes past the inflate guard, and the
# refresh it wedged never re-armed the daily tick.
_FETCH_BUDGET_S = 180

# How many months back a failed refresh looks for a stored card, newest
# first and stopping at the first one it finds. The daily run files a row
# a month, so this month and the one before it cover an outage. The rest
# is for the utility the runner cannot reach, whose rows reach the branch
# only when someone runs the archiver from a residential address, and for
# a month the archiver spent locked out of a publication. A water tariff
# is annual, so the oldest card this can reach is last year's, the card
# every extractor already stands on in January, and the staleness clock
# still runs from the day it was captured.
_ARCHIVE_MONTHS_BACK = 12

# Bumped only if the persisted YTD cycle dict changes shape incompatibly.
# The minor version carries shape changes so a rollback degrades to a
# re-bootstrap instead of a failed setup; see _YtdStore.
_YTD_STORE_VERSION = 1
_YTD_STORE_MINOR_VERSION = 2
# The meter's days behind the year figures, in a Store of their own: they
# are read once a day and have nothing to do with the YTD cycle's shape.
_METERED_STORE_VERSION = 1
# Debounce window for the live path's best-effort Store flush. The daily
# tick and a clean unload save authoritatively; this only bounds how much of
# the climbing high-water mark a hard crash between ticks can lose.
_YTD_SAVE_DELAY_S = 30
# Consecutive sub-baseline readings required before treating the meter as
# swapped (re-anchoring YTD to ~0). A single low value is held as a glitch so
# a rebooting meter reporting 0 does not floor the running figure.
_SWAP_CONFIRM_READINGS = 3
# ...and how long that run has to last. Counting readings alone is a
# proxy for persistence that only holds on the daily tick. The live path
# fires on every state event, so three of them can land inside a second
# -- a meter that drops out and reconnects, or a burst of attribute-only
# updates carrying the same stale value -- and re-anchor the year on a
# glitch. A real replacement keeps reading low for far longer than this.
_SWAP_CONFIRM_SPAN_S = 600.0

# How long to wait for the Energy dashboard's manager singleton before
# giving up on it for this tick.
_ENERGY_MANAGER_TIMEOUT_S = 10.0
# How many refused daily buckets it takes before a year counts as
# unreadable rather than empty. A year that has barely begun has one or
# two, and if a reset is what they hold it has still used nothing; a
# meter that poisons every bucket accumulates them by the month.
_REFUSALS_BEFORE_UNREADABLE = 2

# What no household draws in a day: a year's water, near enough, in one of
# them. Two things measure by it. A daily statistics bucket claiming more
# than this, plus what the days standing behind it could hold, is a re-based
# or reset register rather than water and is dropped. And two readings
# further apart than this are about separate events: it is how far below a
# held jump the next reading may stand and still confirm it, and how far
# from the run before it a sub-baseline reading may stand and still join it.
#
# It was the bound on a single live report too, and _MAX_STEP_M3 took that
# over because at ten times the size it tested nothing: a reading 90 m3
# above where the meter stood was taken on sight and pinned the year.
_IMPLAUSIBLE_JUMP_M3 = 100.0

# The most one meter report may add to the year before it is held for
# confirmation. A household uses 80-100 m3 in a year, so ten of them in a
# single step is already far past anything real. _IMPLAUSIBLE_JUMP_M3 was
# the only bound here and it is ten times looser: below it nothing was
# tested at all, and a reading 90 m3 above where the meter stood was taken
# on sight and pinned the year 1254 EUR over. Refusing here only ever
# delays a figure -- the next reading confirms it, or the recorder settles
# it on the next tick -- so it can afford to be tight.
_MAX_STEP_M3 = 30.0

_SECONDS_PER_DAY = 86400.0

# How far back the year figures read the meter: the rolling year's 365
# closed days and the month before them, which proves the meter was already
# running when the year opened. Last year's remaining days fall inside it.
_METERED_DAYS = 365 + 31

# How long a read of them stands in for one the recorder could not answer.
# Long enough to ride out a locked or restarting database, short enough
# that a recorder which stays broken does not publish an old year as today's.
_METERED_HOLD = timedelta(days=7)

# What a day out of sight may add to the step bound. A household uses
# 80-100 m3 in a year, so a full cubic metre a day is already several
# times any of them and covers a heavy one comfortably: three months off
# the air buys 90 m3 on top of the ordinary bound, and a meter reporting
# once a day buys one. _IMPLAUSIBLE_JUMP_M3 is the wrong rate for this
# even though it is the other bound in here, because it is the figure a
# day cannot exceed rather than one a day plausibly reaches, and using it
# handed the whole of that ceiling to every daily-reporting meter.
_AWAY_M3_PER_DAY = 1.0

# How far a recorder answer may trail the meter and still be current.
# Home Assistant compiles statistics every five minutes, so a query that
# has not lost history is at most a few minutes of flow behind the reading
# it is being compared with.
_RECORDER_LAG_M3 = 2.0

# Units that need no conversion because the figure behind them already is
# cubic metres. A reading with no unit at all is the common case, and
# ASCII "m3" is the superscript one typed on a keyboard: Home Assistant's
# volume converter knows neither, and both halves of the meter path have
# to accept exactly the same set or a meter is read on one and refused on
# the other. Spelled out separately they drifted apart twice.
_ALREADY_CUBIC_METRES: tuple[str | None, ...] = (None, "m3", UnitOfVolume.CUBIC_METERS)


class RecorderUnavailable(Exception):
    """The recorder could not be queried, as distinct from answering empty.

    An empty answer means the year holds no consumption yet and may be
    anchored at zero. This means the year's consumption is simply unknown
    right now, and anchoring on it would discard whatever has already been
    reported.
    """


class _YtdStore(Store[dict[str, Any]]):
    """Store for the YTD cycle anchor, with a place to migrate its shape.

    The shape is versioned through ``minor_version`` rather than
    ``version`` on purpose: Home Assistant calls the migration for either,
    but only re-raises the base NotImplementedError on a *major* mismatch.
    Since the load runs during entry setup with nothing catching it, a
    major bump would break setup for anyone rolling the integration back,
    while an older build meeting a newer minor simply finds no keys it
    knows and re-bootstraps from the recorder.
    """

    async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict[str, Any]
    ) -> dict[str, Any]:
        if old_minor_version < 2:
            return _migrate_cycle_to_v2(old_data)
        return old_data


def _migrate_cycle_to_v2(old: dict[str, Any]) -> dict[str, Any]:
    """Fold the eight-key cycle written before v2 into the single record.

    The old shape carried two year-to-date figures that never met: the live
    one, ``live_hwm_m3 - baseline_m3``, and the recorder-served one,
    ``served_hwm_m3``, each with its own year stamp. The record holds one, so
    the migration picks the newer year and the larger figure in it, which is
    what every reader of the old shape would have published anyway.

    A mark that cannot be dated is dropped rather than carried: it could
    never be released, and it would pin the bill at an old peak in this year
    and every year after it. The default on ``cost_year`` only applies when
    the key is absent, which is a release predating it, whose mark belongs
    to the anchor's own year. Present and ``None`` is a release that knew
    about the key and had nothing to date, and keeps its ``None``.
    """
    if "m3" in old or "offset_m3" in old:
        # Already the new shape. Home Assistant re-stamps a store with its own
        # minor version after any migration, so a release rolled back over this
        # one loaded the record, failed to recognise a single key, and wrote it
        # straight back under minor 1. The label says which release touched the
        # file last, not what shape it holds, so decide by the keys that are
        # actually there. Folding a v2 payload as if it were v1 finds none of
        # the keys it looks for and empties the record.
        kept: dict[str, Any] = {
            key: old.get(key) for key in ("meter", "year", "m3", "cost", "offset_m3")
        }
        for key in ("basis", "recorder_hwm", "seen_at"):
            # Carried when it is there, and not invented when it is not.
            # Rebuilding the dict without a key dropped it on every
            # rollback-and-upgrade: the floor lost its own provenance, and
            # the year lost what the recorder had reported for it. Adding
            # one as None to a record that predates it would make this
            # migration rewrite a record it is meant to hand back
            # untouched. Anything added to the record belongs on this list.
            if key in old:
                kept[key] = old[key]
        return kept
    anchor_year = old.get("year")
    offset = old.get("baseline_m3")
    hwm = old.get("live_hwm_m3")
    live_m3 = max(0.0, hwm - offset) if offset is not None and hwm is not None else None
    mark_year = old.get("cost_year", anchor_year)
    served = old.get("served_hwm_m3")
    cost = old.get("cost_hwm")

    figures: list[tuple[int, float]] = []
    if anchor_year and live_m3 is not None:
        figures.append((anchor_year, live_m3))
    if mark_year and served is not None:
        figures.append((mark_year, served))
    cost_year = mark_year if cost is not None else None

    years = [year for year, _ in figures]
    if cost_year:
        years.append(cost_year)
    if not years:
        return {
            "meter": old.get("meter"),
            "year": None,
            "m3": None,
            "cost": None,
            "offset_m3": None,
        }
    year = max(years)
    current = [figure for stamp, figure in figures if stamp == year]
    return {
        "meter": old.get("meter"),
        "year": year,
        "m3": max(current) if current else None,
        "cost": cost if cost_year == year else None,
        "offset_m3": offset if anchor_year == year and live_m3 is not None else None,
    }


def _ytd_store(hass: HomeAssistant, entry_id: str) -> Store[dict[str, Any]]:
    """The per-entry Store holding that entry's YTD cycle anchor.

    Defined once so entry removal deletes exactly the file the coordinator
    writes rather than a second guess at the same key.
    """
    return _YtdStore(
        hass,
        _YTD_STORE_VERSION,
        f"{DOMAIN}.{entry_id}.ytd",
        minor_version=_YTD_STORE_MINOR_VERSION,
    )


async def async_remove_stores(hass: HomeAssistant, entry_id: str) -> None:
    """Delete an entry's persisted YTD cycle anchor and its meter's days."""
    await _ytd_store(hass, entry_id).async_remove()
    await _metered_store(hass, entry_id).async_remove()


def _metered_store(hass: HomeAssistant, entry_id: str) -> Store[dict[str, Any]]:
    """The per-entry Store holding the last read of the meter's days."""
    return Store(hass, _METERED_STORE_VERSION, f"{DOMAIN}.{entry_id}.metered")


@dataclass(frozen=True)
class _YtdCycle:
    """One year's running consumption, and the frame that produces it.

    ``m3`` is what the year has published: the high-water mark of every
    figure it has seen, whatever produced them. ``offset_m3`` is the
    meter's cumulative reading at the start of the cycle (Jan 1, or the
    moment of a confirmed meter swap), so a live reading ``r`` contributes
    ``r - offset_m3``. A cycle with a figure but no frame is one being
    served straight from the recorder: the year's consumption is known,
    the reading that would produce it is not.

    ``basis`` is who the cost was computed for: the operator, the commune
    and the options that price them. The floor must not outlive that. A
    household granted the social tariff in July, or one whose commune is
    resolved for the first time, gets a cheaper bill for reasons that have
    nothing to do with a dip.

    ``year`` dates the whole record. A stamp from a previous year makes
    ``m3``, ``cost`` and ``offset_m3`` invisible without erasing them,
    because the stamp is what tells a cycle that has merely rolled over
    from one that never existed, and only the latter may start a year at
    zero.
    """

    meter: str | None = None
    year: int | None = None
    m3: float | None = None
    cost: float | None = None
    offset_m3: float | None = None
    # What the cost floor was computed under: the tariff's own rates plus
    # the options that price them. A floor only holds while these hold. An
    # older record has no basis and simply rebuilds its floor once.
    basis: str | None = None
    # The highest figure the recorder has reported for this cycle. It only
    # ever climbs while its history is intact, since consumption
    # accumulates, so an answer below it is a database that has lost some
    # and must not be believed against the year.
    recorder_hwm: float | None = None
    # When a reading was last folded into this cycle, as epoch seconds.
    # Persisted, because the gap that matters most is the one across a
    # restart and no in-process clock survives that. It is what the step
    # bound is scaled by: a meter comes back carrying whatever was drawn
    # while nobody was looking, and how much that can be depends entirely
    # on how long nobody was looking.
    #
    # Out of the comparison, because it moves on every reading and the
    # comparison is what marks the record for saving. A meter reporting
    # every ten seconds says nothing new about the year most of the time,
    # and writing the Store for each of those reports is a great deal of
    # flash wear on the hardware this usually runs on. It rides along with
    # the next real change instead, so what is persisted may trail the
    # figure in hand by however long the year sat still.
    seen_at: float | None = field(default=None, compare=False)


@dataclass(frozen=True)
class _YtdFold:
    """What :func:`_fold` decided: the new cycle, and what to publish."""

    cycle: _YtdCycle
    m3: float | None
    cost: float | None
    hold_m3: float | None
    hold_run: int
    hold_span_s: float
    run_m3: float | None
    high_m3: float | None
    # Set by the round that treats the meter as replaced. The frame is
    # then built on a register with no history, so the year's figure rests
    # on nothing but that reading until something dates it: the next tick
    # asks the recorder rather than trusting the frame it just built.
    swapped: bool = False
    # Set by a round that has met evidence it cannot weigh on its own and
    # wants the recorder on the next tick. Distinct from ``swapped``,
    # which also says the year restarted.
    arbitrate: bool = False


def _fold(
    cycle: _YtdCycle,
    *,
    now_year: int,
    meter: str,
    reading: float | None,
    recorder_m3: float | None,
    recorder_ok: bool | None,
    hold_m3: float | None,
    hold_run: int,
    hold_span_s: float,
    run_m3: float | None,
    elapsed_s: float,
    now_ts: float,
    high_m3: float | None,
    basis: str,
    cost_of: Callable[[float], float | None],
) -> _YtdFold:
    """Fold one round of evidence into the year-to-date cycle.

    The whole rule, with no clock, no I/O and no coordinator state. Both
    callers, the daily tick and the live meter event, hand over the
    evidence they have and get back the new record plus the figures to
    publish. The tick can bring a recorder answer, the live path never
    does; nothing else distinguishes them.

    ``recorder_m3`` is this year's consumption as the recorder reports it,
    or ``None`` when it was not asked or could not answer. ``recorder_ok``
    tells those apart for the one decision that needs it: ``False`` when
    the query failed, ``True`` when it succeeded, ``None`` when nothing has
    asked yet. ``hold_m3`` is a reading held pending confirmation by the
    next one, ``hold_run`` counts consecutive readings below the frame and
    ``run_m3`` is the value that run is sitting at; all three are transient
    and none is persisted.

    Every figure a round produces is a candidate, and the published one is
    the highest of the candidates and the mark already standing. That
    comparison is source-blind, which is what keeps a year-to-date figure
    from walking backwards when the evidence changes hands.
    """
    if cycle.meter != meter:
        # Repointed at a different meter: its cumulative reading has nothing
        # to do with the old one's, so the record goes rather than being
        # reinterpreted. The year's figure restarts, which is the user's
        # only escape from a meter that was wrong all along.
        cycle = _YtdCycle(meter=meter)
        hold_m3 = None
        hold_run = 0
        hold_span_s = 0.0
        high_m3 = None

    current = cycle.year == now_year
    mark = cycle.m3 if current else None
    # A floor only speaks for the household it was measured for. Enabling
    # the social tariff, registering a resident, or resolving the commune
    # the household actually lives in all lower the bill for the rest of
    # the year, and clamping those to a figure measured under the old
    # answer published 437.56 EUR where 87.51 was owed. A cheaper card is
    # not in that set and is still clamped. Consumption is unaffected: no
    # rate has any say in the m3 mark.
    floor = cycle.cost if current and cycle.basis == basis else None
    offset = cycle.offset_m3 if current else None
    recorder_hwm = cycle.recorder_hwm if current else None
    if not current:
        hold_m3 = None
        hold_run = 0
        hold_span_s = 0.0
        high_m3 = None
    # The highest reading the meter has shown this cycle, and what tells a
    # meter climbing past a stale frame from one dipping below a sound one.
    # Only an admitted reading raises it (see the end of the round): a spike
    # that was held and then refuted used to set it for the life of the
    # process, and no real reading could clear it again, so the frame
    # correction below was switched off until the next restart.
    # How long the meter has been out of sight, across restarts included.
    # A backward clock step reads as no gap at all rather than a negative
    # one, which is the cautious way round.
    seen_at = cycle.seen_at
    away_s = 0.0 if seen_at is None else max(0.0, now_ts - seen_at)
    # What one report may add before it is held: the ordinary bound, plus
    # whatever the household could have drawn while the meter was out of
    # sight. A meter that was away comes back carrying all of it and that
    # step is real however large, but how large it can be depends on how
    # long nobody was looking.
    #
    # The gap used to count for nothing but its own existence. One dropped
    # report bought the same 100 m3 as three months off the air, which is
    # about five hours of a domestic connection at full bore or 437 days
    # of an average household, and a spike arriving on the round after a
    # single dropout was taken on sight for 993 EUR.
    step_bound = _MAX_STEP_M3 + away_s / _SECONDS_PER_DAY * _AWAY_M3_PER_DAY
    was_high = high_m3
    # A record still carrying a stamp has history on this meter, so a
    # reading it cannot place comes from a meter that has been running all
    # along. A cleared record has no such history and must wait for the
    # recorder rather than declare the year starts at the first reading it
    # happens to see.
    known_meter = cycle.year is not None

    candidate: float | None = None
    swapped = False
    arbitrate = False
    seen = [figure for figure in (mark, recorder_m3) if figure is not None]
    # What a reading has to clear to belong to this cycle. A framed year
    # measures against the frame. A year served from the recorder has no
    # frame yet, so its own consumption stands in: a meter that has been
    # running since January cannot read below what the year has used.
    bar = offset if offset is not None else (max(seen) if seen else None)
    if reading is None:
        # No reading to confirm or refute a held jump, and the hold only
        # means anything against the reading that follows it directly.
        # Keeping it would let the next spike through unheld, whenever it
        # came.
        hold_m3 = None
    elif bar is not None and reading < bar:
        # Below the bar is either a transient glitch (a rebooting meter
        # reporting 0, a dropout) or a genuine meter swap. Distinguish by
        # persistence: a lone low reading is held rather than flooring the
        # year, and only a sustained run re-anchors.
        if hold_run == 0 or run_m3 is None or abs(reading - run_m3) > _IMPLAUSIBLE_JUMP_M3:
            # Being under the bar is not enough to join a run. A replaced
            # register climbs from where the last reading left it, so a
            # reading that stands nowhere near the ones before it is a
            # separate event and starts a run of its own. Counting them
            # together let two honest readings and one dropout confirm a
            # replacement between them, and the frame was then rebuilt on
            # whichever of the three happened to come last.
            run_m3 = reading
            hold_run = 0
            hold_span_s = 0.0
        hold_run += 1
        if hold_run > 1:
            # The span is how long the run itself has lasted. The gap
            # before its first reading is the meter's ordinary silence,
            # and counting it let three readings inside a second pass
            # for ten minutes after any quiet hour.
            hold_span_s += max(0.0, elapsed_s)
        # A reading under the bar says nothing about a jump held above it,
        # so the hold lapses here too rather than standing until some
        # later spike walks straight past it.
        hold_m3 = None
        if hold_run >= _SWAP_CONFIRM_READINGS and hold_span_s >= _SWAP_CONFIRM_SPAN_S:
            base = max(seen) if seen else None
            if base is not None and reading >= base:
                # The run is sustained, but the meter still shows more water
                # than the year has used, so it cannot be the fresh register a
                # replacement leaves behind. What it sits below is a frame
                # built too high, from a reading that overstated the meter,
                # and the frame is the part that has to give: rebuild it under
                # this reading so the year carries on from the figure it has
                # already published instead of starting over. The figure the
                # frame is rebuilt against is the one standing, so the round
                # publishes what it already published; the recorder answer is
                # kept, because it is still about this meter.
                offset = reading - base
                # Ask the recorder on the next tick, as the swap below
                # does. A frame rebuilt this way reproduces the figure
                # already standing, so the stale-frame gate in
                # _compute_ytd is satisfied from the moment it is built
                # and nothing would ever query again: a run of low
                # readings that was really a dropout left the year on a
                # frame nobody could check, 540.23 m3 against 40.30.
                arbitrate = True
                hold_m3 = None
                hold_run = 0
                hold_span_s = 0.0
            else:
                # Reading below what the year has already used: no meter that
                # measured that water can show this, so the register is a new
                # one. Zero the record before the figures are compared below,
                # or the old mark resurrects itself through the comparison and
                # the swap never takes effect.
                swapped = True
                offset = reading
                mark = 0.0
                floor = None
                candidate = 0.0
                # The year restarts on a register with no history, so what
                # the recorder reported for the old meter, and any water it
                # could not see there, go with it.
                recorder_hwm = None
                hold_m3 = None
                hold_run = 0
                hold_span_s = 0.0
            # Whichever way it went, the reading is where the meter stands
            # now. Leaving an older mark behind would keep every later reading
            # under a mark it cannot reach, and the frame could never be
            # corrected again this year.
            high_m3 = reading
    elif offset is None:
        # No frame this year yet, and the reading clears the bar. Build the
        # frame from the highest figure the year already has, so the reading
        # continues what is published instead of restarting it.
        hold_run = 0
        hold_span_s = 0.0
        if seen:
            base = max(seen)
            offset = reading - base
            candidate = base
        elif known_meter and recorder_ok is not False:
            # Nothing to place the reading against, and no reason to believe
            # the year holds anything: it starts here. A failed query is not
            # such a reason, since the year may well have consumption we
            # simply could not read, and anchoring would discard it.
            offset = reading
            candidate = 0.0
    else:
        hold_run = 0
        hold_span_s = 0.0
        framed = reading - offset
        # A held jump is released by a reading that stands behind it --
        # the meter really is up there. A reading that lands somewhere
        # else entirely refutes the hold instead of confirming it, and
        # has to face the jump test on its own rather than being waved
        # through on the strength of the value it just contradicted.
        corroborated = hold_m3 is not None and reading >= hold_m3 - _IMPLAUSIBLE_JUMP_M3
        if corroborated and seen and framed - max(seen) > step_bound:
            # Two readings agreeing establish where the meter stands, never
            # where it stood when the cycle opened, so a step this size is
            # either a frame sitting under the meter or water the year has
            # genuinely used since anyone last looked. Nothing in a reading
            # tells those apart.
            if recorder_m3 is not None:
                # The recorder reads the same meter's own statistics and
                # says the year used far less, so the frame is what is
                # wrong: that is what a re-anchor onto a reading the meter
                # never really showed leaves behind. Rebuild it against
                # what the year knows instead of billing the difference.
                offset = reading - max(seen)
            else:
                # The live path never carries a recorder answer, so this
                # was the branch that billed the whole of a re-based
                # register: 1012.85 m3 where 12.8 was owed, and nothing but
                # the recorder can take a mark back, so it stood until
                # January. Publish nothing and put the question to the
                # recorder on the next tick.
                arbitrate = True
            hold_m3 = None
        elif corroborated:
            candidate = framed
            hold_m3 = None
        elif mark is not None and framed - mark > step_bound:
            # A step this large in one report is a garbage value far more
            # often than real usage, and only the recorder can take the mark
            # back down, so taking it would pin the year on a household whose
            # recorder never speaks. Hold it for one reading: a meter really
            # sitting there repeats the jump, while a spike is followed by
            # normal values.
            hold_m3 = reading
        else:
            candidate = framed
            hold_m3 = None

    spoken_before = recorder_hwm is not None
    if recorder_m3 is not None and (recorder_hwm is None or recorder_m3 >= recorder_hwm):
        # A recorder answer only climbs while its history is intact, since
        # consumption accumulates. One at or above every previous answer is
        # therefore a database that still holds the year, and it read the
        # same meter's own statistics for all of it, so water it has no
        # record of did not flow. One below is a database that has lost
        # some, and it is ignored rather than believed against the year.
        recorder_hwm = recorder_m3
        if (
            candidate is not None
            and candidate - recorder_m3 > _RECORDER_LAG_M3
            and (spoken_before or mark is None or recorder_m3 >= mark)
        ):
            # Published figures are the maximum of what a round holds, so
            # without this the recorder loses to the reading rather than
            # settling it: a meter 90 m3 above where it stands pinned the
            # year 1254 EUR over with the recorder saying otherwise in the
            # same round.
            _LOGGER.warning(
                "%s: a reading implying %.1f m3 for the year against the recorder's %.1f; "
                "taking the recorder, which has the year's own statistics behind it",
                meter,
                candidate,
                recorder_m3,
            )
            candidate = None
        if spoken_before and mark is not None and mark - recorder_m3 > _RECORDER_LAG_M3:
            # And the mark comes down with it. A spike smaller than the step
            # bound is admitted on sight, raises the mark, and the mark only
            # ever climbed, so it stood until January however plainly the
            # recorder contradicted it. The frame is rebuilt under the
            # corrected figure and the cost floor goes with it, or the
            # correction would show on the volume and not on the bill.
            #
            # Only against a recorder that has already spoken for this
            # year. One answering for the first time has nothing behind it
            # to show its history is whole, and a database that lost the
            # year before anyone asked would read exactly like this.
            _LOGGER.warning(
                "%s: the year stood at %.1f m3 against the recorder's %.1f; taking the "
                "recorder, which has the year's own statistics behind it",
                meter,
                mark,
                recorder_m3,
            )
            mark = recorder_m3
            floor = None
            if reading is not None:
                offset = reading - recorder_m3
                high_m3 = reading

    if candidate is not None and reading is not None:
        # The meter was seen, which means it gave an answer this round could
        # place. A reading held for confirmation or refused as a glitch is
        # not that, and stamping on those spent the allowance a real
        # catch-up needed: a garbage value arriving first after an outage
        # took the whole of it and the reading behind it, which really did
        # carry three months of water, was held as a spike.
        seen_at = now_ts
        if high_m3 is None or reading > high_m3:
            high_m3 = reading

    if swapped:
        # The year restarts on the new meter, so a recorder total spanning
        # the old one says nothing about it.
        recorder_m3 = None
    figures = [figure for figure in (mark, candidate, recorder_m3) if figure is not None]
    if not figures:
        # Nothing is known about this year. Leave the record alone, stamp and
        # all, and report nothing rather than publish a zero it has not
        # earned: the stamp is what stops the next reading starting the year
        # over.
        return _YtdFold(
            cycle,
            None,
            None,
            hold_m3,
            hold_run,
            hold_span_s,
            run_m3,
            high_m3,
            swapped,
            arbitrate,
        )
    published = max(figures)

    if (
        offset is not None
        and reading is not None
        and recorder_m3 is not None
        and candidate is not None
        and was_high is not None
        and reading >= was_high
        and published > reading - offset
        and reading >= published
    ):
        # A reading and a recorder figure read in the same round are the only
        # pair that dates the year's consumption to a meter position, so this
        # is the only place the frame can be corrected without guessing.
        #
        # It also takes a high-water mark to compare against. Without one
        # the record has seen nothing on this meter yet -- a restart, a
        # fresh year -- and a reading that happens to dip cannot be told
        # from one that climbs, so a single low sample would rebuild the
        # frame beneath the meter and over-report every day until January.
        # Waiting a round for the mark to re-establish itself costs the
        # correction nothing. The
        # figure on its own says how much water the year has seen but not
        # where the meter stood when it did, and the frame's own last position
        # is not an answer: a reading held as a spike, or one never seen at
        # all, leaves it behind the meter, and correcting against it would
        # count the same water twice.
        #
        # Rebuilt this way the frame produces exactly what is being published,
        # so the meter carries on from there instead of having to climb back
        # up to where the frame had got to on its own.
        offset = reading - published

    cost = cost_of(published)
    if cost is not None:
        if floor is not None and cost < floor:
            # Consumption comes down only where the recorder has corrected
            # it, and that path drops the floor itself. The bill is recomputed
            # each tick from a freshly fetched tariff and an elapsed-day
            # fraction, so it needs this floor of its own to stop a lower
            # tariff or a backward clock step publishing a decrease.
            cost = floor
        else:
            floor = cost
    return _YtdFold(
        _YtdCycle(
            meter=meter,
            year=now_year,
            m3=published,
            cost=floor,
            offset_m3=offset,
            basis=basis,
            recorder_hwm=recorder_hwm,
            seen_at=seen_at,
        ),
        published,
        cost,
        hold_m3,
        hold_run,
        hold_span_s,
        run_m3,
        high_m3,
        swapped,
        arbitrate,
    )


def utility_device_info(coordinator: WaterCoordinator) -> DeviceInfo:
    """Build the HA DeviceInfo block shared by every entity on this entry.

    Anchors every sensor onto one per-entry device identified by
    ``(DOMAIN, entry.entry_id)`` so the integration's *Devices* tab
    shows a single card per configured utility instead of orphan
    entities. ``manufacturer`` carries the utility label, ``model``
    carries the region, and ``configuration_url`` deep-links to the
    utility's tariff publication for one-click verification.
    """
    utility_id = str(coordinator.entry.data.get(CONF_UTILITY, ""))
    try:
        extractor = get(utility_id)
        manufacturer = extractor.label
        model = extractor.region.title()
    except ExtractorError:
        manufacturer = utility_id or "Belgian Water"
        model = ""
    source_url: str | None = None
    if coordinator.data is not None:
        # The device card is as public as the sensor attribute -- it shows
        # in screenshots and exports the same way -- so the commune slug
        # comes out of the deep link too.
        source_url = source_url_without_commune(
            coordinator.data.tariff.source_url,
            coordinator.entry.options.get(CONF_COMMUNE),
        )
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.entry.entry_id)},
        name=coordinator.entry.title,
        manufacturer=manufacturer,
        model=model or None,
        configuration_url=source_url,
    )


@dataclass(frozen=True)
class YearFigures:
    """The rolling year and the calendar year's projection, read off the meter.

    Each is ``None`` until the meter's statistics cover the days it needs.
    """

    rolling_m3: float | None = None
    rolling_cost_eur: float | None = None
    projected_m3: float | None = None
    projected_end_cost_eur: float | None = None


@dataclass
class CoordinatorData:
    tariff: WaterTariff
    fetched_at: datetime
    snapshot_age_hours: float
    snapshot_stale: bool
    last_error: str = ""
    projected_annual_cost_eur: float | None = None
    current_year_cost_eur: float | None = None
    ytd_consumption_m3: float | None = None
    year_figures: YearFigures = field(default_factory=YearFigures)


@dataclass(frozen=True)
class _MeteredDays:
    """Each closed day's water as the recorder held it for ``meter`` on ``read_on``."""

    meter: str
    read_on: date
    days: dict[date, float]


async def _archived_row(
    session: aiohttp.ClientSession, utility: str, commune: str, month: date
) -> dict[str, Any] | None:
    """The row the project's card archive holds for that utility, commune
    and month, or None when it holds none or what it holds is not a row.

    Raises :class:`TransientFetchError` when the archive could not be
    asked (a network failure, a 5xx, a rate limit): that says nothing
    about whether the month is held."""
    url = f"{CARD_ARCHIVE_URL}/{utility}/{quote(commune, safe='')}/{month:%Y-%m}.json"
    try:
        body = await fetch_text(session, url)
    except TransientFetchError:
        raise
    except ExtractorError:
        return None
    try:
        row = json.loads(body)
    except ValueError:
        return None
    return row if isinstance(row, dict) else None


class WaterCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Fetches the configured utility's tariff once a day."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, *, defer_meter_history: bool = False
    ) -> None:
        self.entry = entry
        utility_id = entry.data[CONF_UTILITY]
        self._extractor: WaterExtractor = get(utility_id)
        self._last_good: CoordinatorData | None = None
        # Resolved meter entity and the meter's reading back at Jan 1,
        # captured on each daily tick so meter state-change events can
        # recompute YTD live without re-querying the recorder.
        self._meter_entity_id: str | None = None
        # Unsub for the live meter subscription. Kept so a later tick that
        # resolves a different meter can re-point it; the entry unload calls
        # async_unsub_live_tracking to tear the current one down.
        self._meter_unsub: CALLBACK_TYPE | None = None
        # The year-to-date cycle, persisted across restarts via _store. It
        # holds the year's consumption, its cost floor and the meter offset
        # that produces them; see :class:`_YtdCycle`. Restoring it means an
        # HA restart or reload no longer re-derives the year from the
        # recorder's trailing daily total, which used to snap the published
        # figure downward.
        self._ytd = _YtdCycle()
        # A reading held pending confirmation by the next one, and the run
        # length of consecutive readings below the cycle's bar. Both are
        # in-memory only: a restart simply re-runs the hold, and a real
        # meter swap re-accumulates the run.
        self._ytd_hold_m3: float | None = None
        self._retired = False
        self._ytd_hold_run = 0
        self._ytd_hold_span_s = 0.0
        self._ytd_run_m3: float | None = None
        self._ytd_last_fold_at: float | None = None
        # Highest reading the meter has shown this cycle. In memory only: it
        # decides whether a reading is the meter climbing or a dip, and after
        # a restart the very next reading re-establishes it.
        self._ytd_high_m3: float | None = None
        # Set when a round has treated the meter as replaced, cleared by
        # the next tick that asks the recorder about it. In memory only, so
        # a restart in between loses the arbitration: the record a swap
        # persists is a complete, self-consistent frame, so every clause of
        # the gate reads False and nothing asks again. That is the same
        # place v0.7.8 was in permanently, and closing it needs the intent
        # persisted rather than held.
        self._ytd_arbitrate: bool = False
        # Whether the last recorder query succeeded, None before anything has
        # asked. Transient by design: it says what the database did a moment
        # ago, which is exactly as long as the answer is worth trusting.
        self._recorder_ok: bool | None = None
        # Set when the cycle changes. The daily tick and a clean unload flush
        # it to the Store authoritatively; the live meter-event path
        # additionally schedules a debounced save so a hard crash between
        # ticks keeps the climbing figure.
        self._cycle_dirty = False
        # (meter, year, configured m3) the projection prompt was last
        # decided for. The answer only changes when one of those does, so
        # remembering them spares the thirteen-month statistics query on
        # every tick but the first. The meter belongs in the key: an
        # options change reloads the entry and rebuilds this, but
        # Energy-dashboard auto-discovery can resolve a different meter
        # with no reload at all, and that is a different year's worth of
        # water.
        self._projection_checked: tuple[str, int, float] | None = None
        # The meter's closed days back to a month before the rolling year,
        # read once a day: the rolling year and the rest of the calendar
        # year, taken from last year's same days, both come off it.
        self._metered: _MeteredDays | None = None
        # Whether the next refresh leaves those two reads of the meter's year
        # out: asked for by setup only, whose first refresh Home Assistant
        # waits on inside a startup stage every integration shares. Set
        # pending by the refresh that left them out, for setup to start
        # async_read_meter_history once it no longer holds startup up.
        self._meter_history_deferred = defer_meter_history
        self.meter_history_pending = False
        self._store: Store[dict[str, Any]] = _ytd_store(hass, entry.entry_id)
        self._metered_store = _metered_store(hass, entry.entry_id)
        super().__init__(
            hass,
            _LOGGER,
            # Explicit rather than the setup-context fallback Home Assistant
            # flags: the entry is what registers the shutdown and makes the
            # daily tick an entry task.
            config_entry=entry,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(hours=UPDATE_INTERVAL_HOURS),
        )

    async def _async_update_data(self) -> CoordinatorData:
        session = async_get_clientsession(self.hass)
        commune = self.entry.options.get(CONF_COMMUNE)
        budget = asyncio.timeout(_FETCH_BUDGET_S)
        failure: Exception | None = None
        try:
            async with budget:
                if commune and self._extractor.fetch_for_commune is not None:
                    tariff = await self._extractor.fetch_for_commune(session, str(commune))
                    tariff = relabel_with_human_commune(
                        tariff,
                        commune_id=str(commune),
                        commune_label=self.entry.options.get(CONF_COMMUNE_LABEL),
                    )
                else:
                    tariff = await self._extractor.fetch(session)
        except Exception as err:
            # Catch broader than ExtractorError so a future extractor
            # that forgets to wrap (asyncio.TimeoutError, ssl.SSLError,
            # KeyError on a malformed response) still falls through to
            # the cached-snapshot path. Two exception families must
            # still propagate:
            #   - asyncio.CancelledError: HA cancels coordinator tasks
            #     on shutdown / reload, that signal has to reach the
            #     event loop unchanged.
            #   - ConfigEntryAuthFailed / ConfigEntryError: HA's
            #     DataUpdateCoordinator runs the reauth flow on these,
            #     swallowing them here would silently break future
            #     credentialed-tariff extractors.
            from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError

            if isinstance(err, asyncio.CancelledError | ConfigEntryAuthFailed | ConfigEntryError):
                raise
            failure = err
        if failure is not None:
            # Handled outside the except block on purpose: whatever the
            # cached path below raises would otherwise carry the raw
            # fetch error as its context, and a traceback logged by the
            # coordinator would print the URL, town name and all, that
            # every other surface scrubs.
            return await self._serve_cached(failure, budget.expired())

        now = datetime.now(UTC)
        ytd_m3, ytd_cost = await self._compute_ytd(tariff)
        data = CoordinatorData(
            tariff=tariff,
            fetched_at=now,
            snapshot_age_hours=0.0,
            snapshot_stale=self._is_stale(tariff, now),
            projected_annual_cost_eur=self._project_cost(tariff),
            current_year_cost_eur=ytd_cost,
            ytd_consumption_m3=ytd_m3,
            year_figures=self._year_figures(tariff, ytd_m3, ytd_cost),
        )
        self._last_good = data
        self._sync_repair_issue(data)
        self._sync_operator_issue()
        if self.entry.state is ConfigEntryState.LOADED and self._owns_the_entry():
            # Only once the entry is up. The first refresh runs inside
            # setup, which calls the backfill itself a few lines later,
            # and doing it here as well would stamp the gate mid-setup and
            # reload the entry out from under it.
            #
            # Scheduled rather than awaited: an await between the fold
            # above and this return is the window a live meter event uses
            # to publish a higher figure that the locals here would then
            # overwrite with a lower one.
            self.hass.async_create_task(self._async_rewrite_price_history())
        return data

    async def _async_rewrite_price_history(self) -> None:
        """Re-run the auto-once price backfill when its gate has moved.

        The gate carries the year of the card the rates came off, so it
        trips when a publisher that ran late finally puts the new one up
        and January's flat line can be rewritten at the rate that really
        applied. Only entry setup consulted it, so an install that has not
        restarted between January and the card landing kept the old line.

        Cheap on every other day: the gate matches and the call returns
        having touched nothing.
        """
        from .statistics import async_maybe_backfill_once

        try:
            await async_maybe_backfill_once(self.hass, self.entry)
        except Exception:
            _LOGGER.exception("could not rewrite the price history for %s", self.entry.entry_id)

    @staticmethod
    def _age_hours(fetched_at: datetime) -> float:
        # Use abs() so a future-dated fetched_at (clock skew, container
        # restored from a future-dated snapshot) surfaces a positive
        # age on the sensor attribute -- masking it with a 0 clamp
        # would hide the symptom while _is_stale fired the Repair.
        return abs((datetime.now(UTC) - fetched_at).total_seconds()) / 3600.0

    @staticmethod
    def _is_stale(tariff: WaterTariff, fetched_at: datetime) -> bool:
        delta = datetime.now(UTC) - fetched_at
        # Future-dated cache is always stale: a snapshot 'from the
        # future' is suspect by definition (clock skew, NTP jump,
        # container restored). Surfacing it as stale lets the
        # snapshot_stale Repair fire on day one instead of waiting
        # for real time to catch up over weeks / months.
        if delta.total_seconds() < 0:
            return True
        age_days = delta.days
        if age_days > SNAPSHOT_STALE_AFTER_DAYS:
            return True
        return tariff.valid_until is not None and tariff.valid_until < dt_util.now().date()

    @property
    def stale_issue_id(self) -> str:
        """Stable Repairs issue id for this entry's stale-snapshot warning."""
        return f"snapshot_stale_{self.entry.entry_id}"

    async def _serve_cached(self, failure: Exception, out_of_time: bool) -> CoordinatorData:
        """What a refresh publishes when its fetch failed with ``failure``.

        The last good snapshot, with the failure scrubbed into last_error
        and the stale check re-run, so a dashboard sees the age and the
        reason rather than every sensor going blank. With no snapshot to
        fall back on, or with one that has gone stale and a newer card in
        the project's archive, the archived card is served instead. With
        neither the refresh fails, which on a first refresh is the entry's
        "not ready" reason.
        """
        if out_of_time:
            # A bare TimeoutError, whose str() is empty. The parse thread
            # it gave up on runs to completion on its own.
            failure = ExtractorError(f"fetch did not finish within {_FETCH_BUDGET_S} s")
        # The message quotes the URL it failed on, and a per-commune URL
        # carries the town name. The sensor attribute, diagnostics and the
        # Repair card all scrub that; the log was the one surface left
        # publishing it.
        scrubbed = scrub_tokens(
            str(failure), sensitive_tokens(self.entry), placeholder="**redacted**"
        )
        held = self._last_good
        # Nothing to serve, or what is held has gone stale: ask the
        # archive. Asking again on a stale snapshot is what carries an
        # outage that outlives the staleness window: the archive files a
        # row a month, and an entry that adopted one in January would
        # otherwise serve that same January card until Home Assistant
        # restarts, Repair card and all. Only a capture newer than what is
        # held replaces it.
        card: tuple[WaterTariff, datetime] | None = None
        if held is None or self._is_stale(held.tariff, held.fetched_at):
            archived = await self._from_card_archive()
            if archived is not None and (held is None or archived[1] > held.fetched_at):
                card = archived
        if card is not None:
            tariff, fetched_at = card
            _LOGGER.warning(
                "water tariff fetch failed (%s), serving the card archived on %s: %s",
                type(failure).__name__,
                fetched_at.date(),
                scrubbed,
            )
        elif held is not None:
            tariff, fetched_at = held.tariff, held.fetched_at
            _LOGGER.warning(
                "water tariff fetch failed (%s), serving cached: %s",
                type(failure).__name__,
                scrubbed,
            )
        else:
            raise UpdateFailed(scrubbed) from failure
        # One fold a round, whichever card is being served: the cycle
        # counts the rounds it has seen, and two in the same refresh would
        # have a reading confirm itself.
        ytd_m3, ytd_cost = await self._compute_ytd(tariff)
        data = CoordinatorData(
            tariff=tariff,
            fetched_at=fetched_at,
            snapshot_age_hours=self._age_hours(fetched_at),
            snapshot_stale=self._is_stale(tariff, fetched_at),
            last_error=scrubbed,
            projected_annual_cost_eur=self._project_cost(tariff),
            current_year_cost_eur=ytd_cost,
            ytd_consumption_m3=ytd_m3,
            year_figures=self._year_figures(tariff, ytd_m3, ytd_cost),
        )
        if card is not None:
            # From here on the archived card is the last good snapshot,
            # ageing like one. The failure is not part of it; the round
            # that serves it writes its own.
            self._last_good = replace(data, last_error="")
        self._sync_repair_issue(data)
        return data

    async def _from_card_archive(self) -> tuple[WaterTariff, datetime] | None:
        """The last card the project's archive holds for this entry and the
        moment it was captured; None when the archive is switched off,
        unreachable, or has nothing for this utility and commune.

        Asked when a refresh failed with nothing to serve, which is a
        restart or a fresh install while the utility is down, and again
        once what is held has gone stale. The entry then loads on that
        card, stale after the usual 35 days, instead of retrying setup
        until the utility is back. This month's row first, since the
        archive writes one per month, then back a month at a time: last
        month's covers the first days of a month, and the ones before it a
        utility the daily run cannot reach at all.
        """
        if not self.entry.options.get(CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE):
            return None
        commune = self.entry.options.get(CONF_COMMUNE)
        key = (
            str(commune) if commune and self._extractor.fetch_for_commune is not None else "default"
        )
        session = async_get_clientsession(self.hass)
        month = dt_util.now().date()
        row: dict[str, Any] | None = None
        for _ in range(_ARCHIVE_MONTHS_BACK):
            try:
                row = await _archived_row(session, self._extractor.id, key, month)
            except TransientFetchError as err:
                # This month may well be held; the archive just did not say.
                # Walking on would take an older month in its place, which
                # in January is last year's card, so stop and let the next
                # refresh ask again. The URL in the message names the
                # commune, so only the kind of failure is logged.
                _LOGGER.debug(
                    "card archive unreachable for %s (%s)", self._extractor.id, type(err).__name__
                )
                return None
            if row is not None:
                break
            # The first of the month, a day back: the last day of the one
            # before, whatever its length.
            month = month.replace(day=1) - timedelta(days=1)
        if row is None:
            return None
        try:
            tariff = tariff_from_dict(row)
            seen_on = date.fromisoformat(str(row["_seen_on"]))
        except (KeyError, TypeError, ValueError):
            return None
        if key != "default":
            tariff = relabel_with_human_commune(
                tariff, commune_id=key, commune_label=self.entry.options.get(CONF_COMMUNE_LABEL)
            )
        # The archive walks at 05:23 UTC; the hour only feeds the age. A
        # row written today can be read before that hour, and a manual run
        # writes at any hour, so never date the capture after now: a
        # snapshot from the future counts as stale, and a card captured
        # this morning raised the stale-snapshot Repair for a whole day.
        captured = datetime(seen_on.year, seen_on.month, seen_on.day, 6, tzinfo=UTC)
        return tariff, min(captured, dt_util.utcnow())

    @callback
    def async_retire(self) -> None:
        """Mark this coordinator as no longer speaking for its entry.

        Called when the entry forgets it, on unload and on a failed
        setup. Read from the entry's state alone, the old coordinator of
        a reload still looked like the owner while the new setup was in
        progress and the bucket not yet filled, and took the owner's
        save path.
        """
        self._retired = True
        self.async_unsub_live_tracking()

    def _owns_the_entry(self) -> bool:
        """Whether this coordinator still speaks for its entry.

        A refresh started from the Repair card runs in the flow's own
        task, which an unload neither cancels nor waits for. When its
        fetch lands after the entry is unloaded, removed, or set up again
        with a new coordinator, nothing it learned may reach the Store,
        the Repairs list or the meter subscription: the file a removal
        deleted came back and the cards were raised for an entry that no
        longer exists.
        """
        return not self._retired and self.entry.state in (
            ConfigEntryState.SETUP_IN_PROGRESS,
            ConfigEntryState.LOADED,
        )

    def _sync_repair_issue(self, data: CoordinatorData) -> None:
        """Create or clear the stale-snapshot Repair issue for this entry.

        Surfaces in Settings -> Repairs as a warning card when the
        snapshot has not refreshed for SNAPSHOT_STALE_AFTER_DAYS days
        or the parsed valid_until is in the past. Auto-clears on the
        next successful, fresh fetch.
        """
        if not self._owns_the_entry():
            return
        if data.snapshot_stale:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                self.stale_issue_id,
                is_fixable=True,
                is_persistent=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="snapshot_stale",
                translation_placeholders={
                    "utility": self._extractor.label,
                    "age_days": f"{int(data.snapshot_age_hours // 24)}",
                    "valid_until": (
                        data.tariff.valid_until.isoformat()
                        if data.tariff.valid_until is not None
                        else "unknown"
                    ),
                    # Already scrubbed on the way into CoordinatorData,
                    # but a caller could build one by hand.
                    "last_error": scrub_tokens(
                        data.last_error, sensitive_tokens(self.entry), placeholder="**redacted**"
                    )
                    or "(none)",
                },
                # Carry the entry id so the Repairs UI flow handler in
                # repairs.py knows which coordinator to refresh when the
                # user clicks the fix button.
                data={"entry_id": self.entry.entry_id},
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, self.stale_issue_id)

    @property
    def projection_issue_id(self) -> str:
        """Stable Repairs issue id for this entry's projection-drift prompt."""
        return f"projection_outdated_{self.entry.entry_id}"

    async def _sync_projection_issue(self, meter: str) -> None:
        """Offer a whole metered year as the projected-cost sensor's input.

        The projection runs off a figure typed once during setup and never
        revisited, while the meter has since measured a full year of the
        real thing. Overwriting the option outright would move a sensor
        with no visible cause, so the measured figure is offered through a
        Repair the user accepts or ignores.

        Reads a closed year straight from the recorder and asks the running
        cycle nothing, so it cannot disturb the year in progress.
        """
        year = dt_util.now().year - 1
        configured = float(
            self.entry.options.get(CONF_CONSUMPTION_M3_PER_YEAR, DEFAULT_CONSUMPTION_M3)
        )
        if self._projection_checked == (meter, year, configured):
            return
        try:
            metered = await _recorder_full_year_m3(self.hass, meter, year)
        except RecorderUnavailable as err:
            # Leave the pair unrecorded so the next tick asks again rather
            # than treating an unreadable database as a settled answer.
            _LOGGER.debug("could not read %d for %s: %s", year, meter, err)
            return
        self._projection_checked = (meter, year, configured)
        if not self._owns_the_entry():
            # That read yielded to the loop; the entry may be gone by now.
            return
        offer = round(metered) if metered is not None else None
        if (
            offer is None
            or not MIN_CONSUMPTION_M3 <= offer <= MAX_CONSUMPTION_M3
            or configured <= 0
            or abs(offer - configured) / configured < PROJECTION_DRIFT_RATIO
        ):
            ir.async_delete_issue(self.hass, DOMAIN, self.projection_issue_id)
            return
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self.projection_issue_id,
            is_fixable=True,
            is_persistent=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="projection_outdated",
            translation_placeholders={
                "utility": self._extractor.label,
                "year": str(year),
                "metered": f"{offer:d}",
                "configured": f"{configured:.0f}",
            },
            # The fix flow writes the option, so it needs both the entry to
            # write it to and the figure to write; the issue's placeholders
            # are display strings and are not read back as numbers.
            data={"entry_id": self.entry.entry_id, "consumption_m3": offer},
        )

    def _project_cost(self, tariff: WaterTariff) -> float | None:
        opts = self.entry.options
        consumption = float(opts.get(CONF_CONSUMPTION_M3_PER_YEAR, DEFAULT_CONSUMPTION_M3))
        return self._annual_cost(tariff, consumption)

    def _annual_cost(self, tariff: WaterTariff, m3: float) -> float | None:
        """A year's bill for ``m3`` on ``tariff``, for this household."""
        opts = self.entry.options
        persons = int(opts.get(CONF_PERSONS, DEFAULT_PERSONS))
        social = bool(opts.get(CONF_SOCIAL_TARIFF, False))
        return compute_annual_cost(tariff, m3, persons, social_tariff=social)

    async def _read_metered_days(self, meter: str) -> None:
        """Read the meter's closed days for :meth:`_year_figures`.

        Once a day: the days are closed, so a second read the same day
        finds the same water. A read that fails keeps what an earlier one
        found for this meter for up to :data:`_METERED_HOLD`, so a database
        hiccup leaves the figures a day behind rather than unknown until
        the next tick.
        """
        today = dt_util.now().date()
        held = self._metered
        if held is not None and held.meter == meter and held.read_on == today:
            return
        start = today - timedelta(days=_METERED_DAYS)
        end = today - timedelta(days=1)
        try:
            rows = await _recorder_daily_rows(self.hass, meter, start, end)
        except RecorderUnavailable as err:
            _LOGGER.debug("could not read the last year of %s: %s", meter, err)
            if held is not None and (held.meter != meter or today - held.read_on > _METERED_HOLD):
                self._metered = None
            return
        # Quietly: this reads the same thirteen months every day, so a bucket
        # refused here would be warned about daily until it left the window.
        # The year-to-date and full-year readers say so when they meet one.
        admitted, _refused = _admitted_changes(rows, meter, start, end, level=logging.DEBUG)
        days = {
            dt_util.as_local(datetime.fromtimestamp(bucket, UTC)).date(): m3
            for bucket, m3 in admitted
            if bucket is not None
        }
        self._metered = _MeteredDays(meter=meter, read_on=today, days=days)
        if self._owns_the_entry():
            # Only for the entry this coordinator still speaks for: a read
            # that lands after a removal would bring the file back.
            await self._metered_store.async_save(
                {
                    "meter": meter,
                    "read_on": today.isoformat(),
                    "days": {day.isoformat(): m3 for day, m3 in days.items()},
                }
            )

    async def _read_meter_history(self, meter: str) -> None:
        """The two reads of a year of the meter: the projection check and
        the days behind the year figures.

        Advisory, so a failure logs and is dropped rather than taking the
        tick down and blanking every sensor on the entry.
        """
        try:
            await self._sync_projection_issue(meter)
        except Exception:
            _LOGGER.exception("could not check the projection against a metered year")
        try:
            await self._read_metered_days(meter)
        except Exception:
            _LOGGER.exception("could not read the last year of %s", meter)

    async def async_read_meter_history(self) -> None:
        """Make the reads setup's own refresh left out, and publish the
        year figures they give.

        Started by setup as a background task once its refresh is in, so
        Home Assistant does not wait on them. Nothing is folded: the year
        figures are built from the year-to-date already published, read
        afresh after the reads, so a meter event handled meanwhile is not
        overwritten.
        """
        if not self.meter_history_pending:
            return
        self.meter_history_pending = False
        meter = self._meter_entity_id
        if meter is None:
            return
        await self._read_meter_history(meter)
        if self.data is None or not self._owns_the_entry():
            return
        self.data = replace(
            self.data,
            year_figures=self._year_figures(
                self.data.tariff, self.data.ytd_consumption_m3, self.data.current_year_cost_eur
            ),
        )
        self.async_update_listeners()

    def _year_figures(
        self, tariff: WaterTariff, ytd_m3: float | None, ytd_cost: float | None
    ) -> YearFigures:
        """The rolling year and the year-end projection on ``tariff``.

        The rolling year is the 365 closed days before the last read,
        priced as a year. The projection is the year so far plus last
        year's same remaining days, and its cost is the running bill plus
        what that rest adds to it: a running bill its floor holds above
        today's card carries into the year end rather than being priced
        away.
        """
        metered = self._metered
        if metered is None or metered.meter != self._meter_entity_id:
            return YearFigures()
        rolling = _rolling_year_m3(metered.days, metered.read_on)
        # The year the published figure was folded for, not the one the
        # clock reads now: a tick that folds 31 December and returns after
        # midnight would otherwise add last year's whole rest to a year
        # that has closed.
        year = self._ytd.year
        projected = end_cost = None
        if year is not None and ytd_m3 is not None:
            rest = _rest_of_year_m3(metered.days, _priced_on(year))
            if rest is not None:
                projected = ytd_m3 + rest
                if ytd_cost is not None:
                    so_far = self._ytd_cost_from_m3(tariff, ytd_m3, year)
                    whole = self._annual_cost(tariff, projected)
                    if so_far is not None and whole is not None:
                        end_cost = round(ytd_cost + whole - so_far, 2)
        return YearFigures(
            rolling_m3=rolling,
            rolling_cost_eur=None if rolling is None else self._annual_cost(tariff, rolling),
            projected_m3=projected,
            projected_end_cost_eur=end_cost,
        )

    async def async_resolve_meter_entity(self) -> str | None:
        """Return the water-meter entity_id to query for YTD computations.

        Priority order:

          1. ``CONF_WATER_METER_SENSOR`` from the OptionsFlow -- explicit
             override that wins over auto-discovery.
          2. The first ``water`` source configured in HA's Energy
             dashboard. Most users wire their water meter there once
             already; auto-discovering it from that config means the
             YTD sensors light up without having to re-pick the same
             entity in our OptionsFlow.
          3. ``None`` -- YTD entities stay unknown.
        """
        explicit = self.entry.options.get(CONF_WATER_METER_SENSOR)
        if explicit:
            self._sync_several_meters_issue(0)
            return str(explicit)
        meter, count = await _discover_energy_water_meter(self.hass)
        self._sync_several_meters_issue(count)
        return meter

    @property
    def several_meters_issue_id(self) -> str:
        """Stable Repairs issue id for this entry's ambiguous-meter notice."""
        return f"several_water_meters_{self.entry.entry_id}"

    @callback
    def _sync_several_meters_issue(self, count: int) -> None:
        """Say so when the dashboard leaves the choice of meter to list order.

        There is no right answer to fall back on: summing would double
        count a sub-meter and over-bill a rainwater or well meter. So the
        one meter is still billed and the household is asked which, rather
        than the choice being made silently on the order the sources
        happen to be stored in. A log line was the only signal, and a bill
        computed from a hot-water sub-meter is not a log-level problem.
        """
        if count > 1 and self._owns_the_entry():
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                self.several_meters_issue_id,
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="several_water_meters",
                translation_placeholders={
                    "utility": self._extractor.label,
                    "count": str(count),
                },
            )
            return
        ir.async_delete_issue(self.hass, DOMAIN, self.several_meters_issue_id)

    @property
    def operator_issue_id(self) -> str:
        """Stable Repairs issue id for this entry's re-resolved postcode."""
        return f"operator_moved_{self.entry.entry_id}"

    @callback
    def _sync_operator_issue(self) -> None:
        """Say so when the stored postcode no longer resolves here.

        v2 entries keep the postcode expressly so a later correction to
        the resolver can reach them, and nothing read it: ``resolve_candidates``
        is called from the config flow alone, so a household that installed
        before the correction stays on the operator that was wrong when it
        installed. Twelve postcodes moved from Pidpa to Water-link in
        0.7.10 and every entry already on one of them kept paying 121.09
        EUR a year too much, with nothing anywhere to say the release had
        changed anything.

        Saying it rather than acting on it. Changing operator rewrites the
        entry's title, its unique id and its commune, and a move into
        Flanders has to ask for the household first; the reconfigure flow
        knows all of that and this does not need to learn it twice. What
        was missing was the signal, not the machinery.
        """
        postcode = self.entry.options.get(CONF_POSTCODE) or self.entry.data.get(CONF_POSTCODE)
        utility = self.entry.data.get(CONF_UTILITY, "")
        candidates = resolve_candidates(str(postcode)) if postcode else ()
        if not candidates or utility in candidates or not self._owns_the_entry():
            # No postcode, an unresolvable one, or one that still answers
            # with the operator in use. A postcode split between operators
            # counts as answering: the household picked one of them.
            ir.async_delete_issue(self.hass, DOMAIN, self.operator_issue_id)
            return
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self.operator_issue_id,
            is_fixable=False,
            is_persistent=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="operator_moved",
            translation_placeholders={
                "utility": self._extractor.label,
                "resolved": get(candidates[0]).label,
            },
        )

    async def async_load_ytd_state(self) -> None:
        """Restore the persisted YTD cycle before the first refresh.

        Restoring it across restarts is what stops the running cost
        falling back: without it every restart re-derived the year from the
        recorder's trailing daily total and snapped the published figure
        downward.

        A cycle that cannot be read or migrated is dropped rather than
        raised: this runs during entry setup with nothing catching it, so a
        bad record would otherwise block the entry entirely. Starting with
        no cycle costs one re-bootstrap from the recorder.
        """
        try:
            data = await self._store.async_load()
        except Exception:
            _LOGGER.exception("could not load the YTD cycle; starting a fresh one")
            return
        if not data:
            return
        cycle = _cycle_from_record(data)
        if cycle is None:
            _LOGGER.warning("the persisted YTD cycle is not readable; starting a fresh one")
            return
        self._ytd = cycle

    async def async_load_metered_days(self) -> None:
        """Restore the last read of the meter's days before the first refresh.

        That refresh leaves the read out, so without this the year figures
        read ``unknown`` after every restart until the read setup starts
        lands; with it they stand where they stood, and a restart on the
        day of the read makes none at all. A record older than
        :data:`_METERED_HOLD` is not adopted, for the reason a failed read
        stops standing in after it.
        """
        try:
            data = await self._metered_store.async_load()
        except Exception:
            _LOGGER.exception("could not load the meter's days; reading them afresh")
            return
        held = _metered_from_record(data)
        if held is None or dt_util.now().date() - held.read_on > _METERED_HOLD:
            return
        self._metered = held

    async def async_save_ytd_state(self) -> None:
        """Flush a pending cycle change to the Store on a clean unload / reload.

        The daily tick persists on each change and the live path schedules a
        debounced save, but a reload can land between those, so flush here
        too. Otherwise the climbing figure would revert to its last persisted
        value and a glitch right after the restart would no longer be
        clamped.
        """
        if self._cycle_dirty:
            self._cycle_dirty = False
            await self._store.async_save(self._cycle_state())

    def _cycle_state(self) -> dict[str, Any]:
        return {
            "meter": self._ytd.meter,
            "year": self._ytd.year,
            "m3": self._ytd.m3,
            "cost": self._ytd.cost,
            "offset_m3": self._ytd.offset_m3,
            "basis": self._ytd.basis,
            "recorder_hwm": self._ytd.recorder_hwm,
            "seen_at": self._ytd.seen_at,
        }

    def _fold_cycle(
        self,
        tariff: WaterTariff,
        *,
        meter: str,
        now_year: int,
        reading: float | None,
        recorder_m3: float | None,
    ) -> tuple[float | None, float | None]:
        """Fold a round of evidence into the cycle and return what to publish.

        The rule itself is :func:`_fold`; this is the only place that keeps
        its answer. The record and the transient hold state are written back
        before returning, so a caller that decides not to publish still
        cannot lose a swap run, a held reading, or a rebuilt frame.
        """
        # How long since the last round. The rule itself keeps no clock,
        # so the caller measures the gap and hands it over as evidence --
        # that is what tells a run of readings spread over hours from a
        # burst of them inside a second.
        now = time.monotonic()
        elapsed_s = 0.0 if self._ytd_last_fold_at is None else now - self._ytd_last_fold_at
        self._ytd_last_fold_at = now
        out = _fold(
            self._ytd,
            now_year=now_year,
            meter=meter,
            reading=reading,
            recorder_m3=recorder_m3,
            recorder_ok=self._recorder_ok,
            hold_m3=self._ytd_hold_m3,
            hold_run=self._ytd_hold_run,
            hold_span_s=self._ytd_hold_span_s,
            run_m3=self._ytd_run_m3,
            elapsed_s=elapsed_s,
            # Wall clock, not the monotonic one above: this is the stamp
            # the record carries, and the gap it has to measure is the one
            # across a restart, which no monotonic clock survives.
            now_ts=dt_util.utcnow().timestamp(),
            high_m3=self._ytd_high_m3,
            basis=_cost_basis(
                utility=tariff.utility,
                commune=self.entry.options.get(CONF_COMMUNE),
                persons=int(self.entry.options.get(CONF_PERSONS, DEFAULT_PERSONS)),
                social=bool(self.entry.options.get(CONF_SOCIAL_TARIFF, False)),
                card_year=tariff.valid_from.year,
            ),
            cost_of=lambda m3: self._ytd_cost_from_m3(tariff, m3, now_year),
        )
        if out.cycle != self._ytd:
            self._cycle_dirty = True
        self._ytd = out.cycle
        self._ytd_hold_m3 = out.hold_m3
        self._ytd_hold_run = out.hold_run
        self._ytd_hold_span_s = out.hold_span_s
        self._ytd_run_m3 = out.run_m3
        self._ytd_high_m3 = out.high_m3
        if out.swapped or out.arbitrate:
            # Nothing has dated the new register yet, or the round met a
            # step it could not weigh. Ask the recorder on the next tick:
            # without it the frame is self-consistent from the moment it
            # is built, so the gate in _compute_ytd never queries again
            # and a meter that was merely offline bills its whole
            # lifetime into this year.
            self._ytd_arbitrate = True
        return out.m3, out.cost

    async def _compute_ytd(self, tariff: WaterTariff) -> tuple[float | None, float | None]:
        """Compute YTD m³ and cost for the daily tick.

        The recorder is consulted only when the cycle cannot answer on its
        own: no frame for this year, or no reading to put through it. From
        there the live meter drives, and :func:`_fold` decides what the year
        publishes.

        Returns ``(ytd_m3, ytd_cost_eur)``; both ``None`` when no meter is
        configured or nothing is known about this year yet.
        """
        deferred = self._meter_history_deferred
        self._meter_history_deferred = False
        meter = await self.async_resolve_meter_entity()
        if meter != self._meter_entity_id:
            # Auto-discovery can start resolving a different Energy-dashboard
            # source with no options change, so nothing reloads the entry.
            # Move the live subscription across before anchoring on it.
            self._meter_entity_id = meter
            self.async_setup_live_tracking()
        if not meter:
            self._metered = None
            return None, None
        # Before anything reads the meter or folds the cycle, not after:
        # these await recorder queries, and an await between the fold and
        # the return is exactly the window a live meter event uses to
        # publish a higher figure that the stale locals here would then
        # overwrite with a lower one. Everything below re-reads its state.
        if deferred:
            self.meter_history_pending = True
        else:
            await self._read_meter_history(meter)
        now_year = dt_util.now().year
        live = _state_volume_m3(self.hass.states.get(meter))
        recorder_m3: float | None = None
        # The frame produces less than the year has already published, so it
        # has fallen behind what is known. Only a reading and a recorder
        # figure read together can put it back, so ask for one. The mismatch
        # closes as soon as the frame is rebuilt, which makes this
        # self-terminating: a year whose meter drives it never queries.
        # A frame is built as reading - published, and subtracting it back
        # leaves binary residue on about half of all pairs, which read as
        # the frame trailing the figure by a femtolitre and asked the
        # recorder on every idle tick.
        stale_frame = (
            self._ytd.m3 is not None
            and self._ytd.offset_m3 is not None
            and live is not None
            and self._ytd.m3 > live - self._ytd.offset_m3
            and not math.isclose(self._ytd.m3, live - self._ytd.offset_m3, abs_tol=1e-6)
        )
        # Decide before folding, not after: the fold clears the record itself
        # when the meter has been repointed, and a gate reading the cleared
        # record would miss the very case that needs the query most.
        if (
            self._ytd.meter != meter
            or self._ytd.year != now_year
            or self._ytd.offset_m3 is None
            or live is None
            or stale_frame
            or self._ytd_arbitrate
        ):
            self._ytd_arbitrate = False
            today = dt_util.now().date()
            jan1 = date(now_year, 1, 1)
            try:
                recorder_m3 = await _recorder_ytd_m3(self.hass, meter, jan1, today)
                self._recorder_ok = True
            except RecorderUnavailable as err:
                _LOGGER.debug("recorder unreadable for %s: %s", meter, err)
                self._recorder_ok = False
            # That query yielded to the loop, and the reading captured before
            # it is the one thing here that can have gone stale meanwhile. Read
            # the meter again: this is the tick that decides how the year is
            # framed, and framing it on a reading the meter has already moved
            # past is wrong for the rest of the year, not just for this tick.
            live = _state_volume_m3(self.hass.states.get(meter))
        else:
            # The cycle answered on its own, so nothing asked the recorder and
            # there is no pending doubt about it. Forget the last answer rather
            # than letting it stand: this branch is the healthy year, so a
            # failure from months ago would otherwise still be believed at the
            # January rollover and block the first live reading from starting
            # the new year.
            self._recorder_ok = None
        ytd_m3, ytd_cost = self._fold_cycle(
            tariff, meter=meter, now_year=now_year, reading=live, recorder_m3=recorder_m3
        )
        if self._cycle_dirty and self._owns_the_entry():
            self._cycle_dirty = False
            folded = self._ytd
            await self._store.async_save(self._cycle_state())
            if self._ytd != folded:
                # That save yielded to the loop and a meter event handled
                # while it ran moved the cycle on. Publish the cycle as it
                # stands rather than the figure computed before the await,
                # which the year has already climbed past.
                ytd_m3, ytd_cost = self._fold_cycle(
                    tariff, meter=meter, now_year=now_year, reading=None, recorder_m3=None
                )
        return ytd_m3, ytd_cost

    def _ytd_cost_from_m3(self, tariff: WaterTariff, ytd_m3: float, year: int) -> float | None:
        """Apply the pro-rated YTD bill math to a year-to-date m³ figure.

        Shared by the daily recorder path (:meth:`_compute_ytd`) and the
        live meter-event path (:meth:`_recompute_live_ytd`) so both use
        identical fee pro-rating and regional math.

        ``year`` is the one the round is being folded for, not the one the
        clock reads now. A tick that starts on 31 December and crosses
        local midnight while its recorder query runs would otherwise price
        the closing year at one day elapsed and hand back a fee of nothing.
        """
        today = _priced_on(year)
        jan1 = date(year, 1, 1)
        elapsed = (today - jan1).days + 1  # include today
        days_in_year = 366 if calendar.isleap(year) else 365
        fraction = elapsed / days_in_year
        persons = int(self.entry.options.get(CONF_PERSONS, DEFAULT_PERSONS))
        social = bool(self.entry.options.get(CONF_SOCIAL_TARIFF, False))
        return compute_ytd_cost(tariff, ytd_m3, persons, fraction, social_tariff=social)

    @callback
    def async_setup_live_tracking(self) -> None:
        """Subscribe to the resolved meter so YTD sensors update on each draw.

        Called after the first refresh has resolved the meter, and again by
        any later tick that resolves a different one. An options change
        reloads the entry, but the Energy-dashboard source behind
        auto-discovery can change with no reload at all, so the
        subscription has to follow the meter rather than stay pinned to
        whichever entity was resolved at setup.
        """
        self.async_unsub_live_tracking()
        if self._meter_entity_id is None or not self._owns_the_entry():
            # A late refresh on a retired coordinator resolves the meter
            # too; subscribed, it would fold readings into a dead cycle
            # and write the Store of an entry that is gone.
            return
        self._meter_unsub = async_track_state_change_event(
            self.hass, [self._meter_entity_id], self._async_meter_state_event
        )

    @callback
    def async_unsub_live_tracking(self) -> None:
        """Tear down the live meter subscription, if any."""
        if self._meter_unsub is not None:
            self._meter_unsub()
            self._meter_unsub = None

    @callback
    def _async_meter_state_event(self, event: Event[EventStateChangedData]) -> None:
        # Ignore anything that is not the meter we are currently anchored
        # on, so a subscription that outlives a meter change cannot feed a
        # foreign reading into the cycle.
        if event.data["entity_id"] != self._meter_entity_id:
            return
        self._recompute_live_ytd(event.data["new_state"])

    @callback
    def _recompute_live_ytd(self, state: State | None) -> None:
        """Push a fresh YTD figure from the meter's live state.

        Pure in-memory arithmetic (no recorder / network call), so it is
        safe to run on every meter update. The same rule the daily tick
        uses, minus the recorder answer the tick can bring: a reading that
        the cycle cannot place yet contributes nothing and the last good
        value stays, as it does when the meter reads unavailable, unknown,
        non-numeric or in a unit that is not a volume.
        """
        if self.data is None:
            return
        meter = self._meter_entity_id
        if meter is None:
            return
        live = _state_volume_m3(state)
        if live is None:
            return
        ytd_m3, ytd_cost = self._fold_cycle(
            self.data.tariff,
            meter=meter,
            now_year=dt_util.now().year,
            reading=live,
            recorder_m3=None,
        )
        if ytd_m3 is None:
            # Nothing is known about this year yet. The fold has still kept
            # whatever the reading proved, so the sensors hold rather than
            # blanking on a year that has not started.
            return
        if ytd_m3 == self.data.ytd_consumption_m3 and ytd_cost == self.data.current_year_cost_eur:
            # Nothing changed -- a same-value meter re-report or an
            # attribute-only state event. Skip so a frequently-reporting
            # meter does not write a redundant recorder row for every
            # sensor. The cost is part of the check so a year rollover (or
            # the midnight fee-proration step) still republishes even when
            # the volume figure is unchanged at ~0.
            return
        if self._cycle_dirty and self._owns_the_entry():
            # The cycle moved. Schedule a debounced flush (the daily tick and
            # the unload save authoritatively; this just bounds how much of
            # the climbing figure a hard crash between ticks can lose).
            # _cycle_dirty stays set so the next authoritative save still
            # writes and clears it.
            self._store.async_delay_save(self._cycle_state, _YTD_SAVE_DELAY_S)
        # Publish without async_set_updated_data: that helper cancels and
        # re-arms the update_interval timer, and a meter reports far more
        # often than once a day, so the daily tariff refresh would be pushed
        # forward on every draw and never come due.
        # snapshot_age_hours is deliberately left alone: a meter draw says
        # nothing about how old the tariff snapshot is, and refreshing it here
        # changed an attribute on every entity on every reading, so every
        # sensor wrote a recorder row per draw instead of the ones that
        # actually moved. It advances on the daily tick, as it already does on
        # an install with no meter at all.
        # The year-end projection is the year so far plus a rest that only
        # the daily tick reads, so it moves with the year.
        self.data = replace(
            self.data,
            ytd_consumption_m3=ytd_m3,
            current_year_cost_eur=ytd_cost,
            year_figures=self._year_figures(self.data.tariff, ytd_m3, ytd_cost),
        )
        self.async_update_listeners()


def _priced_on(year: int) -> date:
    """The day a round folded for ``year`` is priced on.

    Today, unless the clock moved on mid-round. Then the year the round is
    about, which is the one its consumption belongs to: its last day when
    the clock is already past it, its first when the clock stepped back.
    """
    today = dt_util.now().date()
    if today.year == year:
        return today
    return date(year, 12, 31) if today.year > year else date(year, 1, 1)


def _cost_basis(
    *, utility: str, commune: str | None, persons: int, social: bool, card_year: int
) -> str:
    """What the household is billed as, rather than what it is billed for.

    The cost floor exists to stop a momentary dip publishing a decrease: a
    backward clock step, or a tariff fetch that came back cheaper than the
    one before it. It is not meant to outlive a change in who the bill is
    for. Enabling the social tariff, registering a resident, or resolving
    the commune the household actually lives in each lower the bill for
    the rest of the year, and clamping those to a floor measured under the
    old answer published 437.56 EUR where 87.51 was owed, until January.

    Only those inputs are here. The tariff's own rates are deliberately
    absent: a cheaper card is exactly the transient this floor is for, and
    a real mid-year price cut still waits for the year to turn, which is
    the behaviour the README documents and four tests pin.

    The release is here for the same reason the others are. A release that
    corrects a rate downwards is not a dip either, and keying the floor on
    the rates would defeat it, so the version stands in: an upgrade
    rebuilds the floor once, and a correction reaches the running bill the
    day it ships rather than in January. Rebuilding is safe because the m3
    mark comes down only where the recorder has corrected it, and that path
    drops the floor as it goes, so the recomputed cost can only come out
    lower when the rates really are.

    The card's own year is here for the same reason again, and the price
    backfill has kept it in its gate all along for exactly this: when a
    publisher runs late every extractor serves last year's card until
    31 March, so January to March accrues at a stand-in's rates. Those are
    not a transient fetch, and if the real card comes in cheaper a floor
    that cannot tell the two apart holds the household on the stand-in
    until the year turns. A card year moves once, when the publisher
    catches up.
    """
    return "|".join(
        str(part)
        for part in (INTEGRATION_VERSION, utility, commune or "", persons, social, card_year)
    )


def _figure(value: object) -> float | None:
    """``value`` as a finite float, or None when it is not a number."""
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        return None
    return float(value)


def _cycle_from_record(data: object) -> _YtdCycle | None:
    """The persisted cycle, or None when the record does not describe one.

    The file sits in .storage where anyone can edit it. A field of the
    wrong type raised out of the fold on every setup attempt, which left
    the entry retrying for good; a record that was not a mapping failed
    the setup outright. Either is worth one fresh cycle, not the entry.
    """
    if not isinstance(data, dict):
        return None
    meter = data.get("meter")
    year = data.get("year")
    basis = data.get("basis")
    if meter is not None and not isinstance(meter, str):
        return None
    if basis is not None and not isinstance(basis, str):
        return None
    if year is not None and (isinstance(year, bool) or not isinstance(year, int)):
        return None
    figures = {key: data.get(key) for key in ("m3", "cost", "offset_m3", "recorder_hwm", "seen_at")}
    if any(value is not None and _figure(value) is None for value in figures.values()):
        return None
    return _YtdCycle(
        meter=meter,
        year=year,
        m3=_figure(figures["m3"]),
        cost=_figure(figures["cost"]),
        offset_m3=_figure(figures["offset_m3"]),
        basis=basis,
        recorder_hwm=_figure(figures["recorder_hwm"]),
        # No stamp means nothing has been seen on this meter since the
        # record was written, and the honest answer to "how long ago" is
        # that we do not know. Read as no gap, so the meter earns its
        # allowance back from the first reading rather than being handed
        # one on the strength of an unknown.
        seen_at=_figure(figures["seen_at"]),
    )


def _metered_from_record(data: object) -> _MeteredDays | None:
    """The persisted read of the meter's days, or None when the record
    does not describe one. The file is in .storage where anyone can edit
    it, and a bad one costs a read, not the entry."""
    if not isinstance(data, dict):
        return None
    meter = data.get("meter")
    stored = data.get("days")
    if not isinstance(meter, str) or not isinstance(stored, dict):
        return None
    try:
        read_on = date.fromisoformat(str(data.get("read_on")))
        days = {date.fromisoformat(str(day)): _figure(m3) for day, m3 in stored.items()}
    except ValueError:
        return None
    if any(m3 is None for m3 in days.values()):
        return None
    return _MeteredDays(
        meter=meter,
        read_on=read_on,
        days={day: m3 for day, m3 in days.items() if m3 is not None},
    )


def _numeric_state(state: State | None) -> float | None:
    """Return ``state``'s numeric value, or ``None`` if not usable.

    Filters the unavailable / unknown sentinels and any non-numeric
    payload so a flapping meter never pushes a garbage YTD figure.
    """
    if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
        return None
    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return None
    # "inf", "nan" and an overflowing exponent all parse. Two infinite
    # readings pinned the year at infinity, which the sensors refused to
    # publish until a restart.
    return value if math.isfinite(value) else None


def _state_volume_m3(state: State | None) -> float | None:
    """Return ``state``'s reading converted to cubic metres, or ``None``.

    The YTD / running-cost math works in m³, but HA permits a
    ``water`` sensor (the explicit override and the Energy-dashboard
    auto-pick alike) to report litres, gallons, ft³, etc. Read the
    meter's own ``unit_of_measurement`` and convert so a non-m³ meter
    is not silently billed ~1000× too high. A reading with no unit, or
    in ASCII ``m3``, is assumed to already be m³; a unit we cannot
    convert to a volume is rejected so the YTD sensors stay unknown
    rather than publish a garbage figure. The set that needs no
    conversion is shared with the recorder-side guard, which has to
    accept exactly the same units.
    """
    value = _numeric_state(state)
    if value is None or state is None:
        return None
    unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
    if unit in _ALREADY_CUBIC_METRES:
        return value
    try:
        return VolumeConverter.convert(value, unit, UnitOfVolume.CUBIC_METERS)
    except HomeAssistantError:
        _LOGGER.debug("meter unit %r is not a convertible volume; ignoring reading", unit)
        return None


async def _discover_energy_water_meter(hass: HomeAssistant) -> tuple[str | None, int]:
    """Return the first ``water`` source's ``stat_energy_from`` from HA's
    Energy dashboard, and how many water sources it holds.

    The count comes back with the meter because the caller has to say so:
    the dashboard's own order decides which of several is billed, and that
    reflects the order they were added, not which one the utility
    invoices. ``(None, 0)`` when no water source is configured, or the
    energy component is unavailable.

    Wraps every failure mode -- ImportError on old HA without the
    energy component, manager raising on a fresh install, malformed
    source dicts -- so a coordinator tick never crashes on this path.
    """
    try:
        # async_get_manager is the documented public entry point but is not
        # listed in homeassistant.components.energy.__all__, so mypy --strict
        # flags it; the ignore matches the recorder pattern in this file.
        from homeassistant.components.energy import (  # type: ignore[attr-defined]
            async_get_manager,
        )
    except ImportError:
        return None, 0
    try:
        # The manager is a singleton behind an asyncio.Event that is only
        # set once its first load succeeds. A failed read of
        # .storage/energy -- an EIO on the SD card is the classic one --
        # leaves the event unset forever, and every later caller waits on
        # it. Bound the wait so a poisoned singleton costs one tick
        # instead of wedging the coordinator for the life of the process.
        async with asyncio.timeout(_ENERGY_MANAGER_TIMEOUT_S):
            manager = await async_get_manager(hass)
    except Exception as err:  # a timeout, or whatever the energy component surfaced
        _LOGGER.debug("energy manager unavailable: %s", err)
        return None, 0
    data = getattr(manager, "data", None)
    if not data:
        return None, 0
    stats = [
        str(source["stat_energy_from"])
        for source in data.get("energy_sources") or []
        if isinstance(source, dict)
        and source.get("type") == "water"
        and source.get("stat_energy_from")
    ]
    if not stats:
        return None, 0
    if len(stats) > 1:
        # One meter is what the YTD helpers are built around: they take a
        # single statistic id, and the live path tracks one entity. A
        # household with two water meters gets the first and no hint that
        # the rest are missing from the bill, so say so once per tick at
        # a level that reaches the log by default.
        # Without the entity ids: diagnostics redact the meter, and this
        # line reaches the default log that users attach to issues.
        _LOGGER.warning(
            "Energy dashboard lists %d water meters; billing the first one listed. "
            "Set the water meter explicitly in the integration options to choose.",
            len(stats),
        )
    return stats[0], len(stats)


# Units the recorder hands back untouched and which need no conversion,
# because the figures behind them already are cubic metres. ``None`` is a
# sensor with no unit, which _state_volume_m3 reads as m3 on the live
# side; ``m3`` is the ASCII spelling of the same thing.
async def _refuse_an_unconvertible_unit(hass: HomeAssistant, instance: Any, entity_id: str) -> None:
    """Stop before reading a statistic Home Assistant cannot put into m³.

    The query below asks the recorder for cubic metres, and the recorder
    obliges only for a unit its volume converter knows. For anything else
    it returns the figures untouched and says nothing, so a meter labelled
    ``l`` rather than ``L`` -- which Home Assistant only warns about, and
    still records statistics for -- was summed as though litres were
    cubic metres: a 100 m3 year published 100000 m3 and a bill of about
    1.04 million EUR.

    The live path already rejects such a meter, which is what made this
    reachable: with no usable reading, every tick fell through to the
    recorder. So the two halves now agree, and the year reports nothing
    rather than something absurd.

    Agreeing means agreeing on what passes, too, which is why both
    halves read the same ``_ALREADY_CUBIC_METRES``: a reading with no
    unit at all, and one in ASCII ``m3``, are cubic metres already, so
    there is nothing to convert and nothing to get wrong. Spelled out
    separately the two sets drifted apart, and a meter labelled ``m3``
    was refused by the live path while this one took it, which left the
    year anchored at zero on an install with no statistics yet.
    """
    try:
        from homeassistant.components.recorder.statistics import get_metadata
    except ImportError:
        return
    try:
        metadata = await instance.async_add_executor_job(
            partial(get_metadata, hass, statistic_ids={entity_id})
        )
    except Exception as err:
        # Unreadable metadata is unreadable, and guessing that the unit is
        # fine is exactly the guess this exists to stop.
        raise RecorderUnavailable(f"could not read the unit of {entity_id}: {err}") from err
    entry = metadata.get(entity_id)
    if entry is None:
        # No statistic yet. There is nothing to convert and nothing to
        # misread; the empty answer below is the right one.
        return
    unit = entry[1].get("unit_of_measurement")
    if unit in VolumeConverter.VALID_UNITS or unit in _ALREADY_CUBIC_METRES:
        return
    raise RecorderUnavailable(
        f"{entity_id} records statistics in {unit!r}, which Home Assistant cannot "
        f"convert to {UnitOfVolume.CUBIC_METERS} and which is not cubic metres "
        f"already; set the meter's unit to one of "
        f"{sorted(str(u) for u in VolumeConverter.VALID_UNITS)}"
    )


async def _recorder_daily_rows(
    hass: HomeAssistant, entity_id: str, start: date, end: date
) -> list[Any]:
    """Return the daily statistics buckets for ``entity_id`` over ``[start, end]``.

    Wraps :func:`statistics_during_period` via the recorder's executor so
    the SQLite query never runs on the event loop.

    Returns an empty list when there is nothing to read: an empty period, or
    no recorder to read it from. Raises :class:`RecorderUnavailable` only
    when a recorder that is running could not answer this query.

    The absent-recorder cases belong with the empty period rather than with
    the failure, because they never resolve: reporting them as unreadable
    leaves the caller waiting for a recovery that cannot come.

    Asks for the ``change`` field, which the recorder defines as the
    delta of the cumulative ``sum`` between the bucket's first and
    last sample. Reading ``sum`` directly would yield the all-time
    running total -- summing those would multiply the figure by however
    many years of meter history exist. ``sum`` comes along anyway
    because the first bucket's ``change`` is only meaningful next to
    it: see :func:`_recorder_ytd_m3`.
    """
    try:
        # mypy --strict flags both names because the recorder module
        # does not re-export them via __all__; they're public per HA's
        # docs and import-time errors degrade gracefully via the
        # ImportError handler below.
        from homeassistant.components.recorder import (  # type: ignore[attr-defined]
            get_instance,
        )
        from homeassistant.components.recorder.statistics import (
            statistics_during_period,
        )
    except ImportError:
        # No recorder component at all: there are no statistics to read and
        # there never will be, so the year starts here rather than being
        # treated as unreadable forever.
        return []

    try:
        instance = get_instance(hass)
    except Exception as err:
        # Importable but not running: an install without default_config that
        # never enabled the recorder, or one whose recorder failed to start.
        # manifest.json lists recorder under after_dependencies, so a
        # configured recorder is always set up before this integration and
        # this cannot be a startup race. It is the same answer as no recorder
        # component at all, and it has to be, or such an install could never
        # anchor a year and both YTD sensors would sit unknown forever.
        _LOGGER.debug("no recorder instance for %s: %s", entity_id, err)
        return []

    await _refuse_an_unconvertible_unit(hass, instance, entity_id)

    start_dt = dt_util.start_of_local_day(start).astimezone(UTC)
    end_dt = dt_util.start_of_local_day(end).astimezone(UTC) + timedelta(days=1)
    try:
        stats = await instance.async_add_executor_job(
            statistics_during_period,
            hass,
            start_dt,
            end_dt,
            {entity_id},
            "day",
            # Normalise the change deltas to m³ regardless of the meter's
            # own unit (HA permits water sensors in L / gal / ft³ / CCF as
            # well as m³); the recorder converts via the statistic's unit
            # class. Without this a litre-reporting meter would be summed
            # as if it were already cubic metres -- ~1000× too high.
            # Asking is not enough on its own: the recorder hands back
            # whatever it cannot convert, unconverted and unremarked, which
            # is why the unit is checked above before the query runs.
            {VolumeConverter.UNIT_CLASS: UnitOfVolume.CUBIC_METERS},
            # ``state`` is the register at the end of the bucket, which is
            # what a day's change is measured against: see
            # :func:`_change_exceeds_the_register`.
            {"change", "sum", "state"},
        )
    except Exception as err:
        _LOGGER.debug("recorder query for %s failed: %s", entity_id, err)
        raise RecorderUnavailable(str(err)) from err

    rows: list[Any] = list(stats.get(entity_id, []))
    return rows


async def _recorder_ytd_m3(hass: HomeAssistant, entity_id: str, start: date, end: date) -> float:
    """Sum daily ``change`` deltas for ``entity_id`` over ``[start, end]``.

    Returns the period's consumption, and ``0.0`` when there is nothing to
    read. Raises :class:`RecorderUnavailable` only when a recorder that is
    running could not answer the query.

    Those are different answers and the caller has to tell them apart: a
    year with no statistics may be anchored at zero, a query that failed may
    not, or a database hiccup would discard consumption already reported.
    Collapsing both into ``None`` is what every year-stamp and deferral
    guard in this module was re-deriving one call later.
    """
    rows = await _recorder_daily_rows(hass, entity_id, start, end)
    admitted, refused = _admitted_changes(rows, entity_id, start, end, level=logging.WARNING)
    if not admitted and refused > _REFUSALS_BEFORE_UNREADABLE:
        # Every bucket the year had was refused, and there were enough of
        # them to mean something. A handful is not enough: on 1 and 2
        # January a year has one or two buckets, and if a reset or a
        # backwards day is what they hold, the year really has used
        # nothing yet and anchoring it at zero is right.
        raise RecorderUnavailable(
            f"every one of {refused} daily buckets for {entity_id} was refused; "
            "the year cannot be read rather than being empty"
        )
    # No admitted change is negative any more, but the floor stays: it
    # costs nothing and the sensor must never read negative.
    return max(0.0, sum(m3 for _bucket, m3 in admitted))


def _admitted_changes(
    rows: list[Any], entity_id: str, start: date, end: date, *, level: int
) -> tuple[list[tuple[float | None, float]], int]:
    """The daily changes in ``rows`` over ``[start, end]`` that read as water.

    Returns each admitted change with the start of the bucket it was
    booked in, and how many buckets a guard refused. A bucket refused for
    claiming more than its days could hold is logged at ``level``.
    """
    # The first-bucket trim below is not a refusal: it is a boundary
    # artefact, not evidence about the year. A year every guard rejects
    # sums to the same 0.0 as a year with no statistics at all, and the
    # caller may anchor an empty year at zero but not an unreadable one: a
    # cumulative meter that republishes 0 on a nightly reconnect leaves
    # every bucket carrying the whole register, all of them dropped, and
    # the year restarted at zero with the water already used lost until
    # January.
    admitted: list[tuple[float | None, float]] = []
    refused = 0
    # A register drop waiting for the bucket after it, see below.
    pending_drop = 0.0
    # Asking for a day period makes Home Assistant re-align the end of the
    # window to the following local midnight, and the end handed over is
    # already midnight, so the query comes back one day longer than it was
    # asked for. _recorder_full_year_m3 drops the overshoot by bucket and
    # this did not: a clock that ran ahead before NTP corrected it leaves a
    # bucket dated tomorrow, and on 31 December tomorrow is next year.
    # Measured as the next local midnight rather than a fixed 86400, or the
    # 23-hour day the clocks go forward on would fall short of the cut.
    after_end = dt_util.start_of_local_day(end + timedelta(days=1)).timestamp()
    # The day before the window, so the first bucket in it counts as
    # following on rather than as arriving out of nowhere. Days with no
    # bucket of their own sit between this and the next one, and their
    # water is in whichever bucket comes next.
    previous = dt_util.start_of_local_day(start).timestamp() - _SECONDS_PER_DAY
    for index, row in enumerate(rows):
        delta = row.get("change")
        if delta is None:
            continue
        bucket = row.get("start")
        if bucket is not None and bucket >= after_end:
            continue
        gap_days = 0.0
        if bucket is not None:
            gap_days = max(0.0, (bucket - previous) / _SECONDS_PER_DAY - 1.0)
            previous = bucket
        if index == 0 and _change_is_the_whole_register(row):
            # The recorder builds ``change`` by subtracting the sum it
            # finds immediately before the window, and falls back to zero
            # when it finds none. The first bucket's change is then the
            # meter's entire running total rather than that day's
            # consumption, and billing it into the window inflates the
            # year by every cubic metre the meter has ever measured.
            #
            # It reads the same whether the earlier rows were purged or
            # the meter is genuinely new, so the bucket is dropped either
            # way: one missing day beats an unbounded over-count that
            # persists until the year turns.
            _LOGGER.debug(
                "%s has no bucket before %s; dropping the first day rather than"
                " billing the meter's running total into the year",
                entity_id,
                start,
            )
            # Deliberately not counted as a refusal. It is a boundary trim
            # every healthy year takes at most once, and counting it made a
            # meter whose statistics start today, whose only bucket is this
            # one, look like a year nothing could read: the year then
            # refused to anchor at all where it used to anchor at zero.
            continue
        if delta < 0:
            # A register that went backwards is not consumption, and
            # subtracting it from the rest of the year would erase months
            # of water that was really used. It is held against the bucket
            # that follows it instead: a dip that recovers the next day (a
            # `total` meter rebooting across midnight) nets to the water
            # actually used, while a genuine swap or a lost run-up leaves
            # the pair negative and is dropped whole.
            pending_drop += float(delta)
            refused += 1
            continue
        if pending_drop < 0.0:
            netted = float(delta) + pending_drop
            pending_drop = 0.0
            if netted <= 0.0:
                _LOGGER.debug("%s: dropping a register drop and its follow-up bucket", entity_id)
                refused += 1
                continue
            if _exceeds_a_day(netted, entity_id, "netted", gap_days, level=level):
                refused += 1
                continue
            admitted.append((bucket, netted))
            continue
        if _change_exceeds_the_register(row):
            # A register cannot consume more than it reads. Home Assistant
            # treats a numeric dip on a total_increasing meter as a reset
            # and then adds the whole recovered reading to the sum, so a
            # meter that briefly reported 0 leaves a day whose change is
            # its entire register. Billed into the year that became the
            # high-water mark and pinned both sensors until January.
            _LOGGER.debug(
                "%s: dropping a bucket whose change %s exceeds the register %s",
                entity_id,
                delta,
                row.get("state"),
            )
            refused += 1
            continue
        if _exceeds_a_day(float(delta), entity_id, "single", gap_days, level=level):
            refused += 1
            continue
        admitted.append((bucket, float(delta)))
    return admitted, refused


def _exceeds_a_day(
    change: float, entity_id: str, kind: str, gap_days: float = 0.0, *, level: int
) -> bool:
    """Whether a bucket claims more water than the days behind it can hold.

    The live path holds a single report that climbs more than
    ``_MAX_STEP_M3``, plus whatever the meter's absence could have added,
    until the next reading agrees with it. The recorder path had no bound of
    any kind, so the same physical event was arbitrated when it arrived as a
    reading and billed on sight when it arrived as a statistics row.

    Two shapes reach here that :func:`_change_exceeds_the_register` cannot
    see, because it compares a day against its own register rather than
    against a day. A counter re-based onto the real meter reading leaves a
    bucket whose change is the whole re-base but whose register is larger
    still, so the shape test passes it. And a reset bucket that follows a
    negative day is netted rather than checked, so one glitch day carried
    4050 m3 into a year that had used half of one.

    A day is dropped rather than held: there is no next reading to confirm
    it against, and the year's figure is a high-water mark, so admitting
    one bad day pins the bill until January.

    ``gap_days`` is how many days with no bucket of their own sit behind
    this one. A bucket is not always one day of water: Home Assistant
    carries a meter's running total across a gap and attributes the whole
    of it to the bucket the meter comes back in, so the day a meter returns
    from an outage holds the outage. Read as one day it looked like a
    re-based register and was dropped, and losing it cost the whole absence
    rather than the one day this used to say. The gap buys room at the rate
    a household plausibly draws, which is generous enough to keep a real
    catch-up and far too mean to let a re-based register through: a
    register carrying 4050 m3 is still refused after a year out of sight.
    """
    allowance = _IMPLAUSIBLE_JUMP_M3 + max(0.0, gap_days) * _AWAY_M3_PER_DAY
    if change <= allowance:
        return False
    _LOGGER.log(
        level,
        "%s: ignoring a %s change of %.1f m3 over %.0f day(s); no household uses "
        "that much, so it reads as a re-based or reset register rather than water",
        entity_id,
        kind,
        change,
        gap_days + 1.0,
    )
    return True


def _change_exceeds_the_register(row: Any) -> bool:
    """Whether ``row`` claims more consumption than its register shows.

    True when the bucket's change is at least the register reading at its
    end, which no monotonic meter can produce in a day: it is the shape
    the recorder's reset arithmetic leaves behind after a dip.
    """
    change = row.get("change")
    state = row.get("state")
    if change is None or state is None:
        return False
    return float(change) > 0.0 and float(change) >= float(state)


def _change_is_the_whole_register(row: Any) -> bool:
    """Whether ``row``'s change is really the meter's cumulative total.

    True when the recorder had no earlier sum to subtract, which it
    reports by leaving ``change`` equal to ``sum``.
    """
    change = row.get("change")
    total = row.get("sum")
    if change is None or total is None:
        return False
    return bool(total) and abs(float(change) - float(total)) < 1e-9


async def _recorder_full_year_m3(hass: HomeAssistant, entity_id: str, year: int) -> float | None:
    """Return ``year``'s metered consumption, or ``None`` if it is not a whole year.

    Only a year the meter has statistics on both sides of can be read as a
    full one. A meter that first reported in June produces a June-to-December
    figure indistinguishable from a frugal year, and offering that as the
    yearly consumption would understate the projection for as long as the
    user kept it. So the window opens in the previous December: a bucket
    before 1 January proves the meter was already running when the year
    started, and a bucket in the year's own December proves it was still
    running when the year ended.

    Asking for history on either side rather than for a bucket dated
    1 January is deliberate. A meter reports when water moves, so a quiet
    day has no bucket at all, and a household away over New Year would fail
    the stricter test while having a perfectly complete year. The days in
    between have to be there too: a meter that was unavailable from
    January to November and came back in December had history on both
    sides and offered December's water as the year. A bucket on two days
    in three is the bar, which a household away for the summer clears and
    a meter installed in June does not.

    A negative daily delta means the recorded register went backwards. On a
    ``total`` meter that is what replacing the meter looks like, and the
    deltas around it no longer describe one meter's consumption, so the year
    is not offered rather than offered wrong. A ``total_increasing`` meter
    never produces one: Home Assistant reads the drop as the start of a new
    cycle and its running sum climbs straight through, which already gives
    this the figure it wants.
    """
    rows = await _recorder_daily_rows(hass, entity_id, date(year - 1, 12, 1), date(year, 12, 31))
    # Daily buckets start at local midnight, so each of these lands exactly
    # on a bucket boundary. The upper one is not defensive: asking for a
    # day period makes Home Assistant re-align the end of the window to the
    # following local midnight, and the end handed over is already midnight,
    # so it gains a whole day and the query returns 1 January of the year
    # after. Summing that would count a day that belongs to the next year,
    # and a meter replaced on New Year's day would put its negative delta in
    # that bucket and have the whole year refused for it.
    jan1 = dt_util.start_of_local_day(date(year, 1, 1)).timestamp()
    dec1 = dt_util.start_of_local_day(date(year, 12, 1)).timestamp()
    next_year = dt_util.start_of_local_day(date(year + 1, 1, 1)).timestamp()
    before_year = False
    into_december = False
    days = 0
    total = 0.0
    # The day before the window, so its first bucket counts as following on.
    # Kept across the December rows as well: a bucket on 20 December says the
    # meter was reporting then, which is what makes the gap to the next one
    # measurable at all.
    previous = dt_util.start_of_local_day(date(year - 1, 12, 1)).timestamp() - _SECONDS_PER_DAY
    for row in rows:
        bucket = row.get("start")
        if bucket is None:
            continue
        gap_days = max(0.0, (bucket - previous) / _SECONDS_PER_DAY - 1.0)
        previous = bucket
        if bucket < jan1:
            before_year = True
            continue
        if bucket >= next_year:
            continue
        if bucket >= dec1:
            into_december = True
        delta = row.get("change")
        if delta is None:
            continue
        if delta < 0:
            return None
        if _change_exceeds_the_register(row):
            # The same reset arithmetic as above; a year that carries the
            # whole register as one day's water is not a year to offer.
            return None
        if _exceeds_a_day(float(delta), entity_id, "full-year", gap_days, level=logging.WARNING):
            # _change_exceeds_the_register is a shape test and by
            # construction only catches a same-day reset: a counter
            # re-based onto the real meter reading leaves a bucket whose
            # register is larger still and sails through it. The daily
            # bound is in the year-to-date reader and was never reached
            # from here, so this offered 1262 m3 and a 6791.93 EUR
            # projection where the household had used 82 m3 and owed
            # 479.60, and accepting the Repair wrote it into the options.
            return None
        days += 1
        total += float(delta)
    days_in_year = 366 if calendar.isleap(year) else 365
    if not (before_year and into_december) or not _enough_days(days, days_in_year):
        return None
    return total


def _enough_days(days: int, length: int) -> bool:
    """Whether buckets on ``days`` of a period's ``length`` days cover it.

    Two days in three, which a household away for the summer clears and a
    meter that was down for most of the period does not.
    """
    return 3 * days >= 2 * length


def _metered_m3(days: Mapping[date, float], start: date, end: date) -> float | None:
    """What the meter recorded over ``[start, end]``, or ``None`` unless it
    recorded all of it.

    ``days`` holds each day's admitted water. The window is judged the way
    :func:`_recorder_full_year_m3` judges a calendar year: a bucket in the
    month before it proves the meter was already running when it opened,
    one in its last month that it still was when it closed, and buckets on
    two days in three in between that it was not away for most of it. An
    empty window holds no water.
    """
    if end < start:
        return 0.0
    month = timedelta(days=31)
    if not any(start - month <= day < start for day in days):
        return None
    if not any(end - month < day <= end for day in days):
        return None
    inside = [m3 for day, m3 in days.items() if start <= day <= end]
    if not _enough_days(len(inside), (end - start).days + 1):
        return None
    return sum(inside)


def _rolling_year_m3(days: Mapping[date, float], today: date) -> float | None:
    """What the meter recorded over the 365 days before ``today``.

    Closed days only: the figure is read once a tick, and a part of today
    frozen in it until the next one would be neither a day nor nothing.
    """
    return _metered_m3(days, today - timedelta(days=365), today - timedelta(days=1))


def _rest_of_year_m3(days: Mapping[date, float], today: date) -> float | None:
    """What the meter recorded last year from tomorrow's date to 31 December.

    The stand-in for what the rest of this year will use. Water follows the
    household's own season, a garden in summer or a pool filled in May, so
    last year's same days say more about it than a share of a yearly total.
    """
    tomorrow = today + timedelta(days=1)
    try:
        start = tomorrow.replace(year=tomorrow.year - 1)
    except ValueError:  # 29 February has no twin
        start = date(tomorrow.year - 1, 2, 28)
    rest = _metered_m3(days, start, date(today.year - 1, 12, 31))
    if rest is not None and calendar.isleap(today.year - 1):
        leap_day = date(today.year - 1, 2, 29)
        if start <= leap_day:
            # Nor has last year's in a year without one.
            rest -= days.get(leap_day, 0.0)
    return rest
