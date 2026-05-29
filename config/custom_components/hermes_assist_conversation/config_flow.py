"""Config flow for Hermes Assist Conversation."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_URL, DEFAULT_NAME, DEFAULT_URL, DOMAIN


async def _validate_url(hass: HomeAssistant, url: str) -> None:
    """Lightly validate that the bridge is reachable."""
    session = async_get_clientsession(hass)
    async with session.get(f"{url.rstrip('/')}/health", timeout=10) as resp:
        if resp.status != 200:
            raise ValueError(f"Bridge returned HTTP {resp.status}")


class HermesAssistConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hermes Assist Conversation."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            try:
                await _validate_url(self.hass, url)
            except Exception:  # noqa: BLE001 - report friendly setup error
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id("hermes_assist_conversation")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME) or DEFAULT_NAME,
                    data={
                        CONF_NAME: user_input.get(CONF_NAME) or DEFAULT_NAME,
                        CONF_URL: url,
                        CONF_API_KEY: user_input[CONF_API_KEY],
                    },
                )

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_URL, default=DEFAULT_URL): str,
                vol.Required(CONF_API_KEY): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
