"""The AnythingLLM Conversation integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_BASE_URL,
    CONF_WORKSPACE_SLUG,
    CONF_FAILOVER_BASE_URL,
    CONF_FAILOVER_API_KEY,
    CONF_FAILOVER_WORKSPACE_SLUG,
    CONF_FAILOVER_THREAD_SLUG,
    CONF_ENABLE_HEALTH_CHECK,
    DEFAULT_ENABLE_HEALTH_CHECK,
    DOMAIN,
)
from .helpers import AnythingLLMClient, get_anythingllm_client
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CONVERSATION]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type AnythingLLMConfigEntry = ConfigEntry[AnythingLLMClient]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up AnythingLLM Conversation."""
    await async_migrate_integration(hass)
    await async_setup_services(hass, config)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: AnythingLLMConfigEntry
) -> bool:
    """Set up AnythingLLM Conversation from a config entry."""

    try:
        client = await get_anythingllm_client(
            hass=hass,
            api_key=entry.data[CONF_API_KEY],
            base_url=entry.data.get(CONF_BASE_URL),
            workspace_slug=entry.data.get(CONF_WORKSPACE_SLUG),
            failover_api_key=entry.data.get(CONF_FAILOVER_API_KEY),
            failover_base_url=entry.data.get(CONF_FAILOVER_BASE_URL),
            failover_workspace_slug=entry.data.get(CONF_FAILOVER_WORKSPACE_SLUG),
            failover_thread_slug=entry.options.get(CONF_FAILOVER_THREAD_SLUG),
            enable_health_check=entry.data.get(CONF_ENABLE_HEALTH_CHECK, DEFAULT_ENABLE_HEALTH_CHECK),
        )
    except Exception as err:
        _LOGGER.error("Failed to connect to AnythingLLM: %s", err)
        raise ConfigEntryNotReady(err) from err

    entry.runtime_data = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload AnythingLLM."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_integration(hass: HomeAssistant) -> None:
    """Migrate integration entry structure."""

    # Make sure we get enabled config entries first
    entries = sorted(
        hass.config_entries.async_entries(DOMAIN),
        key=lambda e: e.disabled_by is not None,
    )
    if not any(entry.version == 1 for entry in entries):
        return

    for entry in entries:
        _LOGGER.warning(
            "Migrating AnythingLLM Conversation config entry %s from version %s to version 2",
            entry.entry_id,
            entry.version,
        )
        subentry = ConfigSubentry(
            data=entry.options,
            subentry_type="conversation",
            title=entry.title,
            unique_id=None,
        )
        hass.config_entries.async_add_subentry(entry, subentry)
        hass.config_entries.async_update_entry(
            entry, title=entry.title, options={}, version=2
        )
