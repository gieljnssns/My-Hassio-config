"""The Local OpenAI LLM integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components.conversation import DOMAIN as CONVERSATION_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import service
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.typing import ConfigType
from openai import AsyncOpenAI, AuthenticationError, OpenAIError

from .const import CONF_BASE_URL, DOMAIN, LOGGER

PLATFORMS = [Platform.AI_TASK, Platform.CONVERSATION]

type LocalAiConfigEntry = ConfigEntry[AsyncOpenAI]


async def async_setup_entry(hass: HomeAssistant, entry: LocalAiConfigEntry) -> bool:
    """Set up Local OpenAI LLM from a config entry."""
    client = AsyncOpenAI(
        base_url=entry.data[CONF_BASE_URL],
        api_key=entry.data.get(CONF_API_KEY, ""),
        http_client=get_async_client(hass),
    )

    # Cache current platform data which gets added to each request (caching done by library)
    _ = await hass.async_add_executor_job(client.platform_headers)

    try:
        async for _ in client.with_options(timeout=10.0).models.list():
            break
    except AuthenticationError as err:
        LOGGER.error("Invalid API key: %s", err)
        raise ConfigEntryError("Invalid API key") from err
    except OpenAIError as err:
        raise ConfigEntryNotReady(err) from err

    entry.runtime_data = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: LocalAiConfigEntry
) -> None:
    """Handle update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: LocalAiConfigEntry) -> bool:
    """Unload Local OpenAI LLM."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up is called when Home Assistant is loading our component."""
    service.async_register_platform_entity_service(
        hass=hass,
        service_domain=DOMAIN,
        service_name="add_to_weaviate",
        entity_domain=CONVERSATION_DOMAIN,
        schema={
            vol.Required("query"): str,
            vol.Required("content"): str,
            vol.Optional("identifier"): str,
        },
        func=upsert_data_in_weaviate,
    )
    return True


async def upsert_data_in_weaviate(entity, service_call):
    """Service action to add content to Weaviate."""
    await entity.upsert_data_in_weaviate(
        query=service_call.data.get("query"),
        content=service_call.data.get("content"),
        identifier=service_call.data.get("identifier"),
    )
