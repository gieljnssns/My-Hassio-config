"""System health: can this Home Assistant reach the API at all."""

from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant, callback
from jevclient import DEFAULT_BASE_URL

from .const import DOMAIN


@callback
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    # The endpoint this instance actually talks to, not the published one: a
    # self-hosted endpoint being unreachable is the case this panel is for. The panel
    # holds one answer, so with several entries the first loaded one is the one shown.
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    base_url = (
        entries[0].data.get(CONF_URL, DEFAULT_BASE_URL) if entries else DEFAULT_BASE_URL
    )
    return {
        "reachable": system_health.async_check_can_reach_url(hass, base_url),
    }
