"""Services for the AnythingLLM conversation component."""

import logging
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant.auth.permissions.const import POLICY_CONTROL
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, Unauthorized
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_BASE_URL,
    CONF_WORKSPACE_SLUG,
    CONF_HEALTH_CHECK_TIMEOUT,
    CONF_CHAT_TIMEOUT,
    DEFAULT_CONF_BASE_URL,
    DEFAULT_HEALTH_CHECK_TIMEOUT,
    DEFAULT_CHAT_TIMEOUT,
    DOMAIN,
)
from .helpers import get_anythingllm_client


def _validate_http_url(value: str) -> str:
    """Reject non-http/https URLs to prevent API key exfiltration via redirect."""
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        raise vol.Invalid(
            f"URL must use http or https scheme, got: {parsed.scheme!r}"
        )
    if not parsed.netloc:
        raise vol.Invalid("URL must include a hostname")
    return value


CHANGE_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry"): selector.ConfigEntrySelector(
            {
                "integration": DOMAIN,
            }
        ),
        vol.Optional(CONF_API_KEY): cv.string,
        vol.Optional(CONF_BASE_URL): _validate_http_url,
        vol.Optional(CONF_WORKSPACE_SLUG): cv.string,
    }
)

RESET_THREAD_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry"): selector.ConfigEntrySelector(
            {
                "integration": DOMAIN,
            }
        ),
        vol.Optional("conversation_id"): cv.string,
    }
)

_LOGGER = logging.getLogger(__package__)


async def async_setup_services(hass: HomeAssistant, config: ConfigType) -> None:
    """Set up services for the extended openai conversation component."""

    async def change_config(call: ServiceCall) -> None:
        """Change configuration. Requires admin privileges."""
        # Reject calls from non-admin users. System/automation calls have no user_id
        # and are always permitted (context.user_id is None for internal calls).
        user_id = call.context.user_id
        if user_id is not None:
            user = await hass.auth.async_get_user(user_id)
            if user is None or not user.is_admin:
                raise Unauthorized(
                    context=call.context,
                    permission=POLICY_CONTROL,
                    perm_category="config_entry",
                )

        entry_id = call.data["config_entry"]
        entry = hass.config_entries.async_get_entry(entry_id)
        if not entry or entry.domain != DOMAIN:
            raise HomeAssistantError(f"Config entry {entry_id} not found")

        updates = {}
        for key in [
            CONF_API_KEY,
            CONF_BASE_URL,
            CONF_WORKSPACE_SLUG,
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
            health_check_timeout=float(new_data.get(CONF_HEALTH_CHECK_TIMEOUT, DEFAULT_HEALTH_CHECK_TIMEOUT)),
            chat_timeout=float(new_data.get(CONF_CHAT_TIMEOUT, DEFAULT_CHAT_TIMEOUT)),
        )

        hass.config_entries.async_update_entry(entry, data=new_data)

    hass.services.async_register(
        DOMAIN,
        "change_config",
        change_config,
        schema=CHANGE_CONFIG_SCHEMA,
    )

    async def reset_thread(call: ServiceCall) -> None:
        """Clear thread slug overrides for one or all conversations."""
        entry_id = call.data["config_entry"]
        entry = hass.config_entries.async_get_entry(entry_id)
        if not entry or entry.domain != DOMAIN:
            raise HomeAssistantError(f"Config entry {entry_id} not found")

        conversation_id: str | None = call.data.get("conversation_id")

        cleared = 0
        for subentry in entry.subentries.values():
            entity = hass.data.get(f"{DOMAIN}_entity_{subentry.subentry_id}")
            if entity is not None:
                entity.reset_threads(conversation_id)
                cleared += 1

        if cleared == 0:
            _LOGGER.warning(
                "reset_thread: no loaded entities found for config entry %s", entry_id
            )

    hass.services.async_register(
        DOMAIN,
        "reset_thread",
        reset_thread,
        schema=RESET_THREAD_SCHEMA,
    )
