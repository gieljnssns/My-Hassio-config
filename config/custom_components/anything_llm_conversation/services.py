"""Services for the AnythingLLM conversation component."""

import logging

import voluptuous as vol

from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_BASE_URL,
    CONF_WORKSPACE_SLUG,
    DEFAULT_CONF_BASE_URL,
    DOMAIN,
)
from .helpers import get_anythingllm_client

CHANGE_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry"): selector.ConfigEntrySelector(
            {
                "integration": DOMAIN,
            }
        ),
        vol.Optional(CONF_API_KEY): cv.string,
        vol.Optional(CONF_BASE_URL): cv.string,
        vol.Optional(CONF_WORKSPACE_SLUG): cv.string,
    }
)

_LOGGER = logging.getLogger(__package__)


async def async_setup_services(hass: HomeAssistant, config: ConfigType) -> None:
    """Set up services for the extended openai conversation component."""

    async def change_config(call: ServiceCall) -> None:
        """Change configuration."""
        entry_id = call.data["config_entry"]
        entry = hass.config_entries.async_get_entry(entry_id)
        if not entry or entry.domain != DOMAIN:
            raise HomeAssistantError(f"Config entry {entry_id} not found")

        updates = {}
        for key in [
            CONF_API_KEY,
            CONF_BASE_URL,
        ]:
            if key in call.data:
                updates[key] = call.data[key]

        if not updates:
            return

        new_data = entry.data.copy()
        new_data.update(updates)

        _LOGGER.debug("Updating config entry %s", entry_id)

        base_url = new_data.get(CONF_BASE_URL)
        if base_url == DEFAULT_CONF_BASE_URL:
            base_url = None
            new_data.pop(CONF_BASE_URL)

        await get_anythingllm_client(
            hass=hass,
            api_key=new_data[CONF_API_KEY],
            base_url=new_data.get(CONF_BASE_URL, DEFAULT_CONF_BASE_URL),
            workspace_slug=new_data.get(CONF_WORKSPACE_SLUG, "default"),
        )

        hass.config_entries.async_update_entry(entry, data=new_data)

    hass.services.async_register(
        DOMAIN,
        "change_config",
        change_config,
        schema=CHANGE_CONFIG_SCHEMA,
    )
