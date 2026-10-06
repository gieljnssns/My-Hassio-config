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

"""The download-diagnostics payload of one entry."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_GAS_METER, CONF_POSTCODE, CONF_STATION
from .snapshot_codec import snapshot_to_json

# Where the household lives and which meter it reads are not needed to
# debug a price and should not travel with an issue report.
TO_REDACT = {CONF_POSTCODE, CONF_GAS_METER, CONF_STATION, "meter"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator = getattr(entry, "runtime_data", None)
    payload: dict[str, Any] = {"entry": async_redact_data(dict(entry.data), TO_REDACT)}
    if coordinator is None:
        return payload
    data = coordinator.data
    payload["last_error"] = coordinator.last_error
    payload["card_unreadable"] = coordinator.card_unreadable
    payload["card_read_by_ocr"] = coordinator.card_read_by_ocr
    if data is None:
        return payload
    payload["snapshot"] = None if data.snapshot is None else snapshot_to_json(data.snapshot)
    payload["state"] = async_redact_data(
        {
            "card_source": data.card_source,
            "breakdown": None if data.breakdown is None else vars(data.breakdown),
            "fixed": None if data.fixed is None else vars(data.fixed),
            "index": None if data.index is None else vars(data.index),
            "price_provisional": data.price_provisional,
            "conversion": vars(data.conversion),
            "tier": data.tier,
            "annual_kwh": data.annual_kwh,
            "annual_kwh_measured": data.annual_kwh_measured,
            "snapshot_age_hours": data.snapshot_age_hours,
            "snapshot_stale": data.snapshot_stale,
            "current_year_cost": data.current_year_cost,
            "current_month_cost": data.current_month_cost,
            "ytd_kwh": data.ytd_kwh,
            "months_on_current_card": list(data.months_on_current_card),
            "unpriced_periods": list(data.unpriced_periods),
            "rolling_year_kwh": data.rolling_year_kwh,
            "projected_year_cost": data.projected_year_cost,
            "projected_year_end_cost": data.projected_year_end_cost,
            "meter": data.meter,
        },
        TO_REDACT,
    )
    return payload
