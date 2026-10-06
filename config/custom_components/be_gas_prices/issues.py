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

"""The Repairs cards an entry raises and clears.

Each card is raised from the state the tick left behind and deleted as soon
as that state clears, so none outlives the problem it names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import GasCoordinator

# A failed fetch is usually a transient outage the next tick recovers; the
# card saying the layout may have changed waits for this many in a row.
EXTRACTOR_ISSUE_THRESHOLD = 2

ISSUES = (
    "snapshot_stale",
    "extractor_failed",
    "card_unreadable",
    "card_read_by_ocr",
    "meter_unit",
    "several_meters",
)


def issue_id(entry_id: str, name: str) -> str:
    return f"{name}_{entry_id}"


def _sync(
    hass: HomeAssistant,
    entry_id: str,
    name: str,
    active: bool,
    placeholders: dict[str, str],
    *,
    fixable: bool = False,
) -> None:
    key = issue_id(entry_id, name)
    if not active:
        ir.async_delete_issue(hass, DOMAIN, key)
        return
    ir.async_create_issue(
        hass,
        DOMAIN,
        key,
        is_fixable=fixable,
        severity=ir.IssueSeverity.WARNING,
        translation_key=name,
        translation_placeholders=placeholders,
        data={"entry_id": entry_id},
    )


def sync_issues(hass: HomeAssistant, coordinator: GasCoordinator) -> None:
    """Raise or clear every card of the coordinator's entry."""
    entry = coordinator.entry
    base = {"entry": entry.title, "supplier": coordinator.extractor.label}
    stale = coordinator.snapshot_stale()
    _sync(
        hass,
        entry.entry_id,
        "snapshot_stale",
        stale,
        {**base, "error": coordinator.last_error or "-"},
        fixable=True,
    )
    _sync(
        hass,
        entry.entry_id,
        "extractor_failed",
        coordinator.failures >= EXTRACTOR_ISSUE_THRESHOLD and not coordinator.card_unreadable,
        {**base, "error": coordinator.last_error or "-"},
    )
    _sync(hass, entry.entry_id, "card_unreadable", coordinator.card_unreadable, base)
    # The card cannot be read here either way, but while the archive's OCR
    # reading prices the entry, that is what the user needs to know.
    _sync(hass, entry.entry_id, "card_read_by_ocr", coordinator.card_read_by_ocr, base)
    _sync(
        hass,
        entry.entry_id,
        "meter_unit",
        bool(coordinator.meter_error),
        {**base, "error": coordinator.meter_error or "-"},
    )
    _sync(
        hass,
        entry.entry_id,
        "several_meters",
        coordinator.meter_count > 1,
        {**base, "count": str(coordinator.meter_count)},
    )


def clear_issues(hass: HomeAssistant, entry_id: str) -> None:
    for name in ISSUES:
        ir.async_delete_issue(hass, DOMAIN, issue_id(entry_id, name))
