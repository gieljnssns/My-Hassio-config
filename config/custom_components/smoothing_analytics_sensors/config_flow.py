import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import (
    DEFAULT_EMA_DESIRED_TIME_TO_95,
    DEFAULT_LOW_PASS,
    DEFAULT_MEDIAN_SIZE,
    DOMAIN,
    NAME,
)

_LOGGER = logging.getLogger(__name__)


class SmoothingAnalyticsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Smoothing Analytics Sensors."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        self._errors = {}

        # If user_input is not None, the user has submitted the form
        if user_input is not None:
            # Validate input_sensor and other necessary fields
            if not user_input.get("input_sensor"):
                self._errors["input_sensor"] = "required"
            else:
                # Create the configuration with device_name as title
                return self.async_create_entry(
                    title=user_input.get("device_name", NAME),
                    data=user_input,
                )

        # Define the form schema
        data_schema = vol.Schema(
            {
                vol.Required("input_sensor"): selector(
                    {"entity": {"domain": "sensor"}}
                ),
                vol.Optional("device_name", default=NAME): str,
                vol.Optional(
                    "lowpass_time_constant", default=DEFAULT_LOW_PASS
                ): selector(
                    {
                        "number": {
                            "min": 1,
                            "max": 60,
                            "unit_of_measurement": "seconds",
                            "mode": "box",
                        }
                    }
                ),
                vol.Optional(
                    "median_sampling_size", default=DEFAULT_MEDIAN_SIZE
                ): selector(
                    {
                        "number": {
                            "min": 1,
                            "max": 60,
                            "unit_of_measurement": "samples",
                            "mode": "box",
                        }
                    }
                ),
                vol.Optional(
                    "desired_time_to_95", default=DEFAULT_EMA_DESIRED_TIME_TO_95
                ): selector(
                    {
                        "number": {
                            "min": 10,
                            "max": 600,
                            "unit_of_measurement": "seconds",
                            "mode": "box",
                        }
                    }
                ),
            }
        )

        # Show the form to the user
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=self._errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return SmoothingAnalyticsOptionsFlow(config_entry)


class SmoothingAnalyticsOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Smoothing Analytics Sensors."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options step."""
        if user_input is not None:
            # Update the device name in options flow
            return self.async_create_entry(
                title=user_input.get("device_name", self._config_entry.title),
                data=user_input,
            )

        # Use default values from options and translations
        data_schema = vol.Schema(
            {
                vol.Optional(
                    "device_name",
                    default=self._config_entry.options.get("device_name", NAME),
                ): str,
                vol.Optional(
                    "lowpass_time_constant",
                    default=self._config_entry.options.get(
                        "lowpass_time_constant", DEFAULT_LOW_PASS
                    ),
                ): selector(
                    {
                        "number": {
                            "min": 1,
                            "max": 60,
                            "unit_of_measurement": "seconds",
                            "mode": "box",
                        }
                    }
                ),
                vol.Optional(
                    "median_sampling_size",
                    default=self._config_entry.options.get(
                        "median_sampling_size", DEFAULT_MEDIAN_SIZE
                    ),
                ): selector(
                    {
                        "number": {
                            "min": 1,
                            "max": 60,
                            "unit_of_measurement": "samples",
                            "mode": "box",
                        }
                    }
                ),
                vol.Optional(
                    "desired_time_to_95",
                    default=self._config_entry.options.get(
                        "desired_time_to_95", DEFAULT_EMA_DESIRED_TIME_TO_95
                    ),
                ): selector(
                    {
                        "number": {
                            "min": 1,
                            "max": 600,
                            "unit_of_measurement": "seconds",
                            "mode": "box",
                        }
                    }
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
