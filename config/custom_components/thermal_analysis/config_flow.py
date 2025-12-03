"""Config flow for Thermal Analysis integration."""
import logging
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector

from . import (
    DOMAIN,
    CONF_INDOOR_TEMP,
    CONF_OUTDOOR_TEMP,
    CONF_HP_POWER,
    CONF_SOLAR_POWER,
    CONF_HP_THRESHOLD,
    CONF_COP,
    CONF_FLOW_FORWARD,
    CONF_FLOW_RETURN,
)

_LOGGER = logging.getLogger(__name__)

class ThermalAnalysisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Thermal Analysis."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate that sensors exist
            for key in [CONF_INDOOR_TEMP, CONF_OUTDOOR_TEMP, CONF_HP_POWER, CONF_SOLAR_POWER]:
                if user_input.get(key):
                    state = self.hass.states.get(user_input[key])
                    if state is None:
                        errors[key] = "sensor_not_found"

            if not errors:
                return self.async_create_entry(
                    title="Thermal Analysis",
                    data=user_input,
                )

        # Build the schema
        data_schema = vol.Schema({
            vol.Required(CONF_INDOOR_TEMP): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_OUTDOOR_TEMP): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_HP_POWER): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_SOLAR_POWER): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(CONF_FLOW_FORWARD): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(CONF_FLOW_RETURN): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_HP_THRESHOLD, default=3.0): vol.Coerce(float),
            vol.Required(CONF_COP, default=4.66): vol.Coerce(float),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ThermalAnalysisOptionsFlow(config_entry)


class ThermalAnalysisOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Thermal Analysis."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema({
            vol.Required(
                CONF_INDOOR_TEMP,
                default=self.config_entry.data.get(CONF_INDOOR_TEMP)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(
                CONF_OUTDOOR_TEMP,
                default=self.config_entry.data.get(CONF_OUTDOOR_TEMP)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(
                CONF_HP_POWER,
                default=self.config_entry.data.get(CONF_HP_POWER)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(
                CONF_SOLAR_POWER,
                default=self.config_entry.data.get(CONF_SOLAR_POWER)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(
                CONF_FLOW_FORWARD,
                default=self.config_entry.data.get(CONF_FLOW_FORWARD)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(
                CONF_FLOW_RETURN,
                default=self.config_entry.data.get(CONF_FLOW_RETURN)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(
                CONF_HP_THRESHOLD,
                default=self.config_entry.data.get(CONF_HP_THRESHOLD, 3.0)
            ): vol.Coerce(float),
            vol.Required(
                CONF_COP,
                default=self.config_entry.data.get(CONF_COP, 4.66)
            ): vol.Coerce(float),
        })

        return self.async_show_form(step_id="init", data_schema=data_schema)