"""
Custom integration to integrate Waze Alerts with Home Assistant.

For more details about this integration, please refer to
https://github.com/gieljnssns/ha-waze-alerts
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .const import DOMAIN
from .coordinator import WazeAlertsCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Location Tracker."""
    _LOGGER.info("Initializing Location Tracker.")
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Location Tracker from a config entry."""
    _LOGGER.info("Setting up entry for Location Tracker.")

    # Maak de DataUpdateCoordinator aan
    coordinator = WazeAlertsCoordinator(hass, entry)
    # await coordinator.async_config_entry_first_refresh()

    # Sla de coördinator op
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "enabled": True,
    }

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
