"""Config flow for AnythingLLM Conversation integration."""

from __future__ import annotations

import logging
import types
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_BASE_URL,
    CONF_WORKSPACE_SLUG,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_ATTACH_USERNAME,
    CONF_THREAD_SLUG,
    CONF_ENABLE_AGENT_PREFIX,
    CONF_AGENT_KEYWORDS,
    CONF_ENABLE_HEALTH_CHECK,
    CONF_HEALTH_CHECK_TIMEOUT,
    DEFAULT_HEALTH_CHECK_TIMEOUT,
    CONF_CHAT_TIMEOUT,
    DEFAULT_CHAT_TIMEOUT,
    DEFAULT_ATTACH_USERNAME,
    DEFAULT_WORKSPACE_SLUG,
    DEFAULT_CONF_BASE_URL,
    DEFAULT_CONVERSATION_NAME,
    DEFAULT_MAX_TOKENS,
    DEFAULT_NAME,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DEFAULT_THREAD_SLUG,
    DEFAULT_ENABLE_AGENT_PREFIX,
    DEFAULT_AGENT_KEYWORDS,
    DEFAULT_ENABLE_HEALTH_CHECK,
    DOMAIN,
)
from .helpers import get_anythingllm_client, sanitize_slug

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default="AnythingLLM"): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_BASE_URL, default=DEFAULT_CONF_BASE_URL): str,
        vol.Optional(CONF_WORKSPACE_SLUG, default=DEFAULT_WORKSPACE_SLUG, description="AnythingLLM Workspace Slug"): str,
        vol.Optional(CONF_ENABLE_HEALTH_CHECK, default=DEFAULT_ENABLE_HEALTH_CHECK, description="Enable health check"): bool,
        vol.Optional(
            CONF_HEALTH_CHECK_TIMEOUT,
            default=DEFAULT_HEALTH_CHECK_TIMEOUT,
            description="Health check timeout (seconds)"
        ): NumberSelector(NumberSelectorConfig(min=1, max=120, step=0.5)),
        vol.Optional(
            CONF_CHAT_TIMEOUT,
            default=DEFAULT_CHAT_TIMEOUT,
            description="Chat completion timeout (seconds)"
        ): NumberSelector(NumberSelectorConfig(min=5, max=600, step=1)),
    }
)

DEFAULT_OPTIONS = types.MappingProxyType(
    {
        CONF_PROMPT: DEFAULT_PROMPT,
        CONF_WORKSPACE_SLUG: DEFAULT_WORKSPACE_SLUG,
        CONF_MAX_TOKENS: DEFAULT_MAX_TOKENS,
        CONF_TEMPERATURE: DEFAULT_TEMPERATURE,
        CONF_ATTACH_USERNAME: DEFAULT_ATTACH_USERNAME,
        CONF_THREAD_SLUG: DEFAULT_THREAD_SLUG,
        CONF_ENABLE_AGENT_PREFIX: DEFAULT_ENABLE_AGENT_PREFIX,
        CONF_AGENT_KEYWORDS: DEFAULT_AGENT_KEYWORDS,
        CONF_ENABLE_HEALTH_CHECK: DEFAULT_ENABLE_HEALTH_CHECK,
        CONF_HEALTH_CHECK_TIMEOUT: DEFAULT_HEALTH_CHECK_TIMEOUT,
        CONF_CHAT_TIMEOUT: DEFAULT_CHAT_TIMEOUT,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    api_key = data[CONF_API_KEY]
    base_url = data.get(CONF_BASE_URL, DEFAULT_CONF_BASE_URL)
    raw_slug = data.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
    workspace_slug = sanitize_slug(raw_slug)

    # Ensure timeouts are float
    health_check_timeout = float(data.get(CONF_HEALTH_CHECK_TIMEOUT, DEFAULT_HEALTH_CHECK_TIMEOUT))
    chat_timeout = float(data.get(CONF_CHAT_TIMEOUT, DEFAULT_CHAT_TIMEOUT))

    await get_anythingllm_client(
        hass=hass,
        api_key=api_key,
        base_url=base_url,
        workspace_slug=workspace_slug,
        health_check_timeout=health_check_timeout,
        chat_timeout=chat_timeout,
    )


def _build_reconfigure_schema(data: dict[str, Any]) -> vol.Schema:
    """Build the reconfigure form schema pre-filled with current values."""
    return vol.Schema(
        {
            vol.Required(
                CONF_API_KEY,
                default=data.get(CONF_API_KEY, ""),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Optional(
                CONF_BASE_URL,
                default=data.get(CONF_BASE_URL, DEFAULT_CONF_BASE_URL),
            ): str,
            vol.Optional(
                CONF_WORKSPACE_SLUG,
                default=data.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG),
            ): str,
            vol.Optional(
                CONF_ENABLE_HEALTH_CHECK,
                default=data.get(CONF_ENABLE_HEALTH_CHECK, DEFAULT_ENABLE_HEALTH_CHECK),
            ): BooleanSelector(),
            vol.Optional(
                CONF_HEALTH_CHECK_TIMEOUT,
                default=data.get(CONF_HEALTH_CHECK_TIMEOUT, DEFAULT_HEALTH_CHECK_TIMEOUT),
            ): NumberSelector(NumberSelectorConfig(min=1, max=120, step=0.5)),
            vol.Optional(
                CONF_CHAT_TIMEOUT,
                default=data.get(CONF_CHAT_TIMEOUT, DEFAULT_CHAT_TIMEOUT),
            ): NumberSelector(NumberSelectorConfig(min=5, max=600, step=1)),
        }
    )


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AnythingLLM Conversation."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            await validate_input(self.hass, user_input)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception: %s", err)
            errors["base"] = "cannot_connect"
        else:
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data={
                    **user_input,
                    CONF_HEALTH_CHECK_TIMEOUT: float(user_input.get(CONF_HEALTH_CHECK_TIMEOUT, DEFAULT_HEALTH_CHECK_TIMEOUT)),
                    CONF_CHAT_TIMEOUT: float(user_input.get(CONF_CHAT_TIMEOUT, DEFAULT_CHAT_TIMEOUT)),
                },
                subentries=[
                    {
                        "subentry_type": "conversation",
                        "data": {
                            **DEFAULT_OPTIONS,
                            CONF_WORKSPACE_SLUG: user_input.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG),
                        },
                        "title": DEFAULT_CONVERSATION_NAME,
                        "unique_id": None,
                    }
                ],
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        entry = self._get_reconfigure_entry()
        
        if user_input is not None:
            errors = {}
            try:
                await validate_input(self.hass, user_input)
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data=user_input,
                )
            
            # Show form again with errors
            reconfigure_schema = _build_reconfigure_schema(user_input)
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=reconfigure_schema,
                errors=errors,
            )
        
        # Initial display - populate with current values
        reconfigure_schema = _build_reconfigure_schema(entry.data)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=reconfigure_schema,
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {"conversation": AnythingLLMSubentryFlowHandler}


class AnythingLLMSubentryFlowHandler(ConfigSubentryFlow):
    """Flow for managing AnythingLLM subentries."""

    options: dict[str, Any]

    @property
    def _is_new(self) -> bool:
        """Return if this is a new subentry."""
        return self.source == "user"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a subentry, inheriting workspace slug from parent integration."""
        self.options = dict(DEFAULT_OPTIONS)
        entry = self._get_entry()
        if CONF_WORKSPACE_SLUG in entry.data:
            self.options[CONF_WORKSPACE_SLUG] = entry.data[CONF_WORKSPACE_SLUG]
        return await self.async_step_init()

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle reconfiguration of a subentry."""
        self.options = dict(self._get_reconfigure_subentry().data)
        return await self.async_step_init()

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Manage the options."""
        # abort if entry is not loaded
        if self._get_entry().state != ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        if user_input is not None:
            for _slug_key in (
                CONF_WORKSPACE_SLUG,
                CONF_THREAD_SLUG,
            ):
                if user_input.get(_slug_key):
                    user_input[_slug_key] = sanitize_slug(user_input[_slug_key])
            if self._is_new:
                title = user_input.get(CONF_NAME, DEFAULT_NAME)
                if CONF_NAME in user_input:
                    del user_input[CONF_NAME]
                return self.async_create_entry(
                    title=title,
                    data=user_input,
                )
            return self.async_update_and_abort(
                self._get_entry(),
                self._get_reconfigure_subentry(),
                data=user_input,
            )

        schema = self.anythingllm_config_option_schema(self.options)

        if self._is_new:
            schema = {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                **schema,
            }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )

    def anythingllm_config_option_schema(self, options: dict[str, Any]) -> dict:
        """Return a schema for AnythingLLM completion options."""
        entry = self._get_entry()
        return {
            vol.Optional(
                CONF_PROMPT,
                description={"suggested_value": options.get(CONF_PROMPT)},
                default=options.get(CONF_PROMPT, DEFAULT_PROMPT),
            ): TemplateSelector(),
            vol.Optional(
                CONF_MAX_TOKENS,
                description={"suggested_value": options.get(CONF_MAX_TOKENS)},
                default=options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS),
            ): int,
            vol.Optional(
                CONF_TEMPERATURE,
                description={"suggested_value": options.get(CONF_TEMPERATURE)},
                default=options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
            ): NumberSelector(NumberSelectorConfig(min=0, max=1, step=0.05)),
            vol.Optional(
                CONF_ATTACH_USERNAME,
                description={"suggested_value": options.get(CONF_ATTACH_USERNAME)},
                default=options.get(CONF_ATTACH_USERNAME, DEFAULT_ATTACH_USERNAME),
            ): BooleanSelector(),
            vol.Optional(
                CONF_WORKSPACE_SLUG,
                description={"suggested_value": options.get(CONF_WORKSPACE_SLUG)},
                default=options.get(CONF_WORKSPACE_SLUG, entry.data.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)),
            ): str,
            vol.Optional(
                CONF_THREAD_SLUG,
                description={"suggested_value": options.get(CONF_THREAD_SLUG)},
                default=options.get(CONF_THREAD_SLUG, DEFAULT_THREAD_SLUG),
            ): str,
            vol.Optional(
                CONF_ENABLE_AGENT_PREFIX,
                description={"suggested_value": options.get(CONF_ENABLE_AGENT_PREFIX)},
                default=options.get(CONF_ENABLE_AGENT_PREFIX, DEFAULT_ENABLE_AGENT_PREFIX),
            ): BooleanSelector(),
            vol.Optional(
                CONF_AGENT_KEYWORDS,
                description={"suggested_value": options.get(CONF_AGENT_KEYWORDS)},
                default=options.get(CONF_AGENT_KEYWORDS, DEFAULT_AGENT_KEYWORDS),
            ): str,
            vol.Optional(
                CONF_ENABLE_HEALTH_CHECK,
                description={"suggested_value": options.get(CONF_ENABLE_HEALTH_CHECK)},
                default=options.get(CONF_ENABLE_HEALTH_CHECK, entry.data.get(CONF_ENABLE_HEALTH_CHECK, DEFAULT_ENABLE_HEALTH_CHECK)),
            ): BooleanSelector(),
        }
