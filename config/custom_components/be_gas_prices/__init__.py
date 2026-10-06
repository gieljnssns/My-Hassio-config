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

"""The Belgian Gas Prices integration."""

from __future__ import annotations

from datetime import date, datetime

import voluptuous as vol
from homeassistant.config_entries import (
    SIGNAL_CONFIG_ENTRY_CHANGED,
    ConfigEntry,
    ConfigEntryChange,
    ConfigEntryState,
)
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ConfigEntryError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util
from homeassistant.util.json import JsonValueType

from .backfill import backfill_once_a_year, backfill_prices
from .const import CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE, DOMAIN, PLATFORMS, STORAGE_VERSION
from .coordinator import GasCoordinator
from .daily_ranking import ranking_minute
from .issues import clear_issues
from .providers.base import ExtractorError

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_REFRESH = "refresh"
SERVICE_BACKFILL = "backfill_statistics"
_REFRESH_SCHEMA = vol.Schema({vol.Optional("entry_id"): cv.string})
_BACKFILL_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Optional("start_date"): cv.date,
        vol.Optional("clear", default=False): cv.boolean,
    }
)

type GasConfigEntry = ConfigEntry[GasCoordinator]


def _loaded_coordinators(hass: HomeAssistant, entry_id: str | None) -> list[GasCoordinator]:
    coordinators = [
        entry.runtime_data
        for entry in hass.config_entries.async_loaded_entries(DOMAIN)
        if entry_id is None or entry.entry_id == entry_id
    ]
    if entry_id is not None and not coordinators:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_entry",
            translation_placeholders={"entry_id": entry_id},
        )
    return coordinators


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the services once, whatever the number of entries."""

    @callback
    def _entry_changed(_change: ConfigEntryChange, entry: ConfigEntry) -> None:
        # An entry whose setup was retrying is not unloaded when it is
        # disabled, only stopped: its Repairs cards go with it here.
        if entry.domain == DOMAIN and entry.state is ConfigEntryState.NOT_LOADED:
            clear_issues(hass, entry.entry_id)

    async_dispatcher_connect(hass, SIGNAL_CONFIG_ENTRY_CHANGED, _entry_changed)

    async def _refresh(call: ServiceCall) -> None:
        for coordinator in _loaded_coordinators(hass, call.data.get("entry_id")):
            await coordinator.async_force_refresh()

    async def _backfill(call: ServiceCall) -> ServiceResponse:
        entry_id = call.data.get("entry_id")
        if call.data["clear"] and entry_id is None:
            # A clear deletes a sensor's statistics whole; one careless call
            # must not do that to every entry at once.
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="clear_needs_entry"
            )
        today = dt_util.now().date()
        earliest = date(today.year - 1, 1, 1)
        asked = call.data.get("start_date")
        if asked is not None and asked < earliest:
            # The card archive keeps a year of cards: an older month has no
            # card to be priced on, and an absurd date would only stall.
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="start_date_too_early",
                translation_placeholders={"earliest": earliest.isoformat()},
            )
        if asked is not None and asked > today:
            # Nothing to write, and a clear first would delete the history
            # for nothing.
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="start_date_in_future"
            )
        written: dict[str, JsonValueType] = {}
        for coordinator in _loaded_coordinators(hass, entry_id):
            start = asked or coordinator.window_start(today)
            written.update(
                await backfill_prices(hass, coordinator, start, clear=call.data["clear"])
            )
        return {"rows": written}

    hass.services.async_register(DOMAIN, SERVICE_REFRESH, _refresh, schema=_REFRESH_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_BACKFILL,
        _backfill,
        schema=_BACKFILL_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: GasConfigEntry) -> bool:
    try:
        coordinator = GasCoordinator(hass, entry)
    except ExtractorError as err:
        # A supplier this release no longer carries: retrying cannot help.
        raise ConfigEntryError(str(err)) from err
    if coordinator.extractor.images_only and not entry.data.get(
        CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE
    ):
        # No card of this supplier can be read here, and the entry keeps the
        # archive's reading out: retrying would only download the card.
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="card_archive_needed",
            translation_placeholders={"supplier": coordinator.extractor.label},
        )
    if coordinator.contract not in {c.id for c in coordinator.extractor.contracts}:
        # A contract its supplier withdrew: no card of it is read any more,
        # and the entry is set up again once its settings name another.
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="contract_withdrawn",
            translation_placeholders={
                "contract": coordinator.extractor.withdrawn.get(
                    coordinator.contract, coordinator.contract
                )
            },
        )
    await coordinator.async_load_persistent()
    entry.runtime_data = coordinator
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))

    running: set[str] = set()

    def _maybe_backfill() -> None:
        # One run at a time; each returns at once when nothing it draws
        # from has moved since the last one.
        if running:
            return
        running.add(entry.entry_id)

        async def _run() -> None:
            try:
                await backfill_once_a_year(hass, coordinator)
            finally:
                running.discard(entry.entry_id)

        entry.async_create_background_task(hass, _run(), f"{DOMAIN} price history")

    entry.async_on_unload(coordinator.async_add_listener(_maybe_backfill))
    _maybe_backfill()

    # The hourly tick alone would miss a minute late in the day's last hour
    # whenever it lands earlier in that hour, day after day.
    minute = ranking_minute(entry.entry_id)

    @callback
    def _rank_at_its_minute(_now: datetime) -> None:
        coordinator.maybe_rank(dt_util.now().date())

    entry.async_on_unload(
        async_track_time_change(
            hass, _rank_at_its_minute, hour=minute // 60, minute=minute % 60, second=0
        )
    )
    return True


async def _async_reload(hass: HomeAssistant, entry: GasConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GasConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        clear_issues(hass, entry.entry_id)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: GasConfigEntry) -> None:
    """Drop the entry's store and Repairs cards with the entry, so a re-add
    starts clean. An entry removed while its setup was retrying was never
    unloaded, which is where the cards are cleared otherwise."""
    clear_issues(hass, entry.entry_id)
    await Store[dict[str, object]](
        hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
    ).async_remove()
