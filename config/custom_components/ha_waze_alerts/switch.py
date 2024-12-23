"""Switch platform for ha-waze-alerts."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    """Setup de switch."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([WazeAlertsSwitch(data)])


class WazeAlertsSwitch(SwitchEntity):
    """Switch to enable or disable tracking."""

    def __init__(self, data) -> None:
        self._data = data
        self._is_on = data["enabled"]

    @property
    def unique_id(self):
        """Een unieke ID voor de switch."""
        return f"{self._data['coordinator'].config_entry.entry_id}_switch"

    @property
    def name(self):
        return "Waze Alerts Tracking"

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        self._is_on = True
        self._data["enabled"] = True

    async def async_turn_off(self, **kwargs):
        self._is_on = False
        self._data["enabled"] = False
