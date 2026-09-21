"""Adds config flow for Waze Alerts."""

from __future__ import annotations

from typing import TYPE_CHECKING

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_RADIUS
from homeassistant.core import callback

from .const import CATEGORIES, CONF_CATEGORY, DEFAULT_CATEGORY, DEFAULT_RADIUS, DOMAIN

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult


class WazeAlertsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Waze Alerts."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="Waze Alerts", data=user_input)

        # Haal beschikbare device_trackers op
        device_trackers = list(self.hass.states.async_entity_ids("device_tracker"))
        if not device_trackers:
            errors["base"] = "no_device_trackers_available"
        # Stel het formulier samen
        schema = vol.Schema(
            {
                vol.Required("device_tracker"): vol.In(device_trackers),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Define the options flow for updates."""
        return WazeAlertsOptionsFlowHandler(config_entry)


class WazeAlertsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Waze Alerts."""

    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        radius = self.config_entry.options.get(CONF_RADIUS, DEFAULT_RADIUS)
        categories = self.config_entry.options.get(CONF_CATEGORY, [DEFAULT_CATEGORY])

        schema = vol.Schema(
            {
                vol.Required(CONF_RADIUS, default=radius): vol.Coerce(int),
                vol.Required(CONF_CATEGORY, default=categories): vol.All(
                    cv.multi_select(CATEGORIES), vol.Length(min=1)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
