"""Adds config flow for HA CSV Predictor."""
import logging

# import os
from typing import Any
import numpy as np
import pandas as pd
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow

# from homeassistant.helpers.aiohttp_client import async_create_clientsession
# from .helpers.config_flow import DeviceNameCreator, FindEntity, FlowValidator
from homeassistant.const import (
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, State, callback

_LOGGER = logging.getLogger(__name__)
# from .api import HaCsvPredictorApiClient
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CSV_PATH,
    CONF_DEPENDENT_VARIABLE,
    CONF_INDEPENDENT_VARIABLES,
    DOMAIN,
)

# DATA_SCHEMA = vol.Schema({vol.Required(CONF_CSV_PATH): str})
print(np.__version__)


def validate_path(hass: HomeAssistant, path: str) -> str:
    """Validate path."""
    full_path = hass.config.path(path)
    try:
        pd.read_csv(full_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"CSV file not found at path: {full_path}") from e
    # get_path = pathlib.Path(path)
    # print(get_path)
    # if not get_path.exists() or not get_path.is_file():
    #     _LOGGER.error("Can not access file %s", path)
    #     raise NotValidError

    # if not hass.config.is_allowed_path(path):
    #     _LOGGER.error("Filepath %s is not allowed", path)
    #     raise NotAllowedError

    # full_path = hass.config.path(path)
    print(full_path)

    return str(full_path)


def validate_columns(csv_path: str, columns: list) -> list:
    """Validate path."""
    # full_path = hass.config.path(csv_path)
    # print(csv_path)
    # print(columns)
    # print(type(columns))
    try:
        data = pd.read_csv(csv_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"CSV file not found at path: {csv_path}") from e
    required_columns = columns.split()
    # print(required_columns)
    # print(type(required_columns))
    if not set(required_columns).issubset(data.columns):
        raise ValueError(
            f"CSV file should contain the following columns: {', '.join(required_columns)}"
        )
    # get_path = pathlib.Path(path)
    # print(get_path)
    # if not get_path.exists() or not get_path.is_file():
    #     _LOGGER.error("Can not access file %s", path)
    #     raise NotValidError

    # if not hass.config.is_allowed_path(path):
    #     _LOGGER.error("Filepath %s is not allowed", path)
    #     raise NotAllowedError

    # full_path = hass.config.path(path)
    # print(full_path)

    return required_columns


@config_entries.HANDLERS.register(DOMAIN)
class HaCsvPredictorFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for ha_csv_predictor."""

    VERSION = 1
    # CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    # @staticmethod
    # @callback
    # def async_get_options_flow(
    #     config_entry: ConfigEntry,
    # ) -> OptionsFlow:
    #     """Get the options flow for this handler."""
    #     print("async_get_options_flow")
    #     return HaCsvPredictorOptionFlowHandler(config_entry)

    async def _show_setup_form(
        self, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_CSV_PATH): str,
                    vol.Required(CONF_INDEPENDENT_VARIABLES): str,
                    vol.Required(CONF_DEPENDENT_VARIABLE): str,
                }
            ),
            errors=errors or {},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        # print("step_user")
        errors = {}

        if user_input is None:
            return await self._show_setup_form(user_input)

        self._async_abort_entries_match(
            {CONF_CSV_PATH: user_input[CONF_CSV_PATH], CONF_NAME: user_input[CONF_NAME]}
        )

        name = user_input[CONF_NAME]
        path = validate_path(self.hass, user_input[CONF_CSV_PATH])
        independent_variables = validate_columns(
            csv_path=path,
            columns=user_input.get(CONF_INDEPENDENT_VARIABLES, []),
        )
        # print(independent_variables)
        dependent_variable = validate_columns(
            csv_path=path,
            columns=user_input.get(CONF_DEPENDENT_VARIABLE, []),
        )
        return self.async_create_entry(
            title=user_input[CONF_NAME],
            data={
                CONF_NAME: name,
                CONF_CSV_PATH: path,
                CONF_INDEPENDENT_VARIABLES: independent_variables,
                CONF_DEPENDENT_VARIABLE: dependent_variable,
            },
        )
