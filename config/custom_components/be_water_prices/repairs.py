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

"""Repairs flow handlers for this integration's two Repair cards.

`snapshot_stale`: the coordinator raises it under Settings -> Repairs
when the last successful tariff fetch has aged out
(:data:`SNAPSHOT_STALE_AFTER_DAYS` days) or the parsed
``valid_until`` has already passed. Clicking the card opens a flow
that triggers an immediate coordinator refresh; the issue auto-clears
in :func:`coordinator._sync_repair_issue` when the next fetch returns
a fresh snapshot.

`projection_outdated`: raised when a whole year the meter measured
disagrees with the yearly consumption the projected-cost sensor is
configured with. Clicking the card writes the measured figure into the
options, which reloads the entry and moves the sensor.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import issue_registry as ir

from .const import CONF_CONSUMPTION_M3_PER_YEAR, DOMAIN


class SnapshotStaleRepairFlow(RepairsFlow):
    """Confirm + retry the tariff fetch for one stale-snapshot entry."""

    def __init__(self, entry_id: str) -> None:
        self._entry_id = entry_id

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # The Repairs manager starts the flow with the issue id as its init
        # data, so user_input is already a dict on the very first call and
        # a single step would run its action before anyone saw a form.
        # Hand straight over to a named step, as ConfirmRepairFlow does.
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Forward the issue's placeholders so the form's title and
        # description, and the abort message below, render
        # {utility}/{age_days}/{valid_until}/{last_error} instead of
        # literal braces. HA does not auto-forward issue placeholders to
        # fix-flow steps (see ConfirmRepairFlow); mirror that lookup here.
        issue_registry = ir.async_get(self.hass)
        placeholders = None
        if issue := issue_registry.async_get_issue(self.handler, self.issue_id):
            placeholders = issue.translation_placeholders
        if user_input is None:
            return self.async_show_form(step_id="confirm", description_placeholders=placeholders)
        coordinator = self.hass.data.get(DOMAIN, {}).get(self._entry_id)
        if coordinator is not None:
            await coordinator.async_refresh()
        if coordinator is None or coordinator.data is None or coordinator.data.snapshot_stale:
            # Completing the flow makes the Repairs manager delete the
            # issue. That is right once the refresh has cleared it, but on
            # a retry that did not help it would hide the card until the
            # next daily tick recreated it. Aborting leaves it in place.
            return self.async_abort(reason="still_stale", description_placeholders=placeholders)
        # The refresh returned a fresh snapshot, so _sync_repair_issue has
        # already deleted the issue; close the flow normally.
        return self.async_create_entry(title="", data={})


class ProjectionOutdatedRepairFlow(RepairsFlow):
    """Confirm writing a measured year into one entry's consumption option."""

    def __init__(self, entry_id: str, consumption_m3: int) -> None:
        self._entry_id = entry_id
        self._consumption_m3 = consumption_m3

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Same reason as the stale-snapshot flow: the manager's init data
        # arrives as user_input, so acting in this step would write the
        # option the moment the card is opened.
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Same placeholder forwarding as the stale-snapshot flow: HA does
        # not hand an issue's placeholders to its fix-flow steps, so the
        # form would render literal {year} / {metered} braces without this.
        issue_registry = ir.async_get(self.hass)
        placeholders = None
        if issue := issue_registry.async_get_issue(self.handler, self.issue_id):
            placeholders = issue.translation_placeholders
        if user_input is None:
            return self.async_show_form(step_id="confirm", description_placeholders=placeholders)
        entry = self.hass.config_entries.async_get_entry(self._entry_id)
        if entry is None or not self._consumption_m3:
            # The entry was removed while the card sat there, or the issue
            # carries no figure to write. Abort rather than complete: a
            # completed flow deletes the issue, which would hide the card
            # without having changed anything.
            return self.async_abort(reason="cannot_apply", description_placeholders=placeholders)
        self.hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, CONF_CONSUMPTION_M3_PER_YEAR: self._consumption_m3},
        )
        # Writing the options fires the update listener, which reloads the
        # entry; the fresh coordinator re-runs the check against the new
        # figure and finds nothing to raise.
        return self.async_create_entry(title="", data={})


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Wire each issue id to the flow that fixes it."""
    payload = data or {}
    entry_id = str(payload.get("entry_id") or "")
    if issue_id.startswith("projection_outdated_"):
        offer = payload.get("consumption_m3")
        return ProjectionOutdatedRepairFlow(
            entry_id=entry_id,
            consumption_m3=int(offer) if isinstance(offer, int | float) else 0,
        )
    return SnapshotStaleRepairFlow(entry_id=entry_id)
