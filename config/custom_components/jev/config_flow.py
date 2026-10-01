"""Config and options flow.

Setup makes one real request. It costs a few thousandths of a cent and it is the
only way to tell a working key from a typed one before entities appear. The request
goes to whichever endpoint the entry names, so the same request proves the address
as well as the key.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from jevclient import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    USD_PER_MILLION_INPUT_TOKENS,
    JevAuthError,
    JevClient,
    JevError,
    JevResponseError,
    JevValidationError,
    Noul,
)
from yarl import URL

from .const import (
    CONF_ADVANCED,
    CONF_ALLOW_WHOLE_HOME,
    CONF_DAILY_TOKEN_BUDGET,
    CONF_FALLBACK_AGENT,
    CONF_MIN_CONFIDENCE,
    CONF_MODEL,
    CONF_PRICE_PER_MILLION,
    DEFAULT_MIN_CONFIDENCE,
    DOMAIN,
    OPENROUTER_BASE_URL,
    SUBENTRY_QUESTION,
)
from .identity import entry_unique_id
from .subentry import JevQuestionSubentryFlow

# The placeholders every form that can show the not_found error needs.
FORM_PLACEHOLDERS = {"openrouter_url": OPENROUTER_BASE_URL}

# Collapsed, so the common setup is one field. Both of these only matter to
# someone running their own endpoint, and either one cleared is the default.
ADVANCED_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_URL, default=DEFAULT_BASE_URL): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
        ),
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): str,
    }
)

# Optional, not because TypeSafe takes an empty key, but because an endpoint of
# your own may need none. An empty key against the published address is refused
# below rather than sent.
STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_API_KEY, default=""): str,
        vol.Required(CONF_ADVANCED): section(ADVANCED_SCHEMA, {"collapsed": True}),
    }
)

# Reauth is a rejected credential, not a moved address, so it asks for the key alone
# and leaves the endpoint where it is. An endpoint that moved is a reconfigure.
STEP_REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): str})


def _normalised_url(raw: str | None) -> str:
    """The endpoint to store, or ValueError naming what is wrong with it.

    Empty means the published API, so clearing the field is how you go back.

    A space is refused before yarl sees it. yarl keeps one inside the host, and a
    host of " gateway.local" is truthy, so the check below would pass a typo on to
    a request that can only fail.

    jevclient appends /v1/systemone to whatever it is given, which is why a path is
    allowed: a reverse proxy can mount the API under one. A query or a fragment
    cannot survive that concatenation. Credentials in the URL are refused because
    diagnostics redacts secrets by key name and would not see these.
    """
    if not (text := (raw or "").strip()):
        return DEFAULT_BASE_URL
    if any(character.isspace() for character in text):
        raise ValueError("the address cannot contain a space")
    url = URL(text)
    if url.scheme not in ("http", "https"):
        raise ValueError("the address needs to start with http:// or https://")
    if not url.host:
        raise ValueError("the address names no host")
    if url.query_string or url.fragment:
        raise ValueError("a query or a fragment cannot be part of a base address")
    if url.user or url.password:
        raise ValueError("a username or password in the address is not supported")
    return str(url).rstrip("/")


def _normalised_model(raw: str | None) -> str:
    """The model to ask for, or ValueError. Empty means the published default.

    The id is opaque to us, so only a paste error is checked here. Whether the
    endpoint knows it is settled by the request below.
    """
    if not (text := (raw or "").strip()):
        return DEFAULT_MODEL
    if any(character.isspace() for character in text):
        raise ValueError("the model id cannot contain a space")
    return text


def _credentials(user_input: dict[str, Any]) -> tuple[str, str, str, dict[str, str]]:
    """The key, the address and the model out of one submitted form.

    Every field is checked before the request that would use them, so two typos
    are two messages on one submit rather than one per attempt.
    """
    api_key = (user_input.get(CONF_API_KEY) or "").strip()
    base_url, model, errors = _advanced(user_input)
    if not api_key and base_url == DEFAULT_BASE_URL:
        # The published API answers 401 to a request with no key, so an empty key
        # here is a mistake that can be named without spending a request on it.
        errors[CONF_API_KEY] = "key_required"
    return api_key, base_url, model, errors


def _advanced(user_input: dict[str, Any]) -> tuple[str, str, dict[str, str]]:
    """The address and the model out of the section, with what is wrong with them.

    Both are checked, so two typos are reported once rather than one per submit.
    A field that failed falls back to the default and is named in the errors.
    """
    values = user_input.get(CONF_ADVANCED) or {}
    errors: dict[str, str] = {}
    try:
        base_url = _normalised_url(values.get(CONF_URL))
    except ValueError:
        base_url, errors[CONF_URL] = DEFAULT_BASE_URL, "invalid_url"
    try:
        model = _normalised_model(values.get(CONF_MODEL))
    except ValueError:
        model, errors[CONF_MODEL] = DEFAULT_MODEL, "invalid_model"
    return base_url, model, errors


def _stored(entry: ConfigEntry) -> tuple[str, str]:
    """What an entry already talks to.

    Entries made before these were configurable carry neither, and mean the
    published API and its default model, which is what they have always used.
    """
    return (
        entry.data.get(CONF_URL, DEFAULT_BASE_URL),
        entry.data.get(CONF_MODEL, DEFAULT_MODEL),
    )


def _suggest(base_url: str, model: str) -> dict[str, Any]:
    """Section values shaped the way add_suggested_values_to_schema reads them."""
    return {CONF_ADVANCED: {CONF_URL: base_url, CONF_MODEL: model}}


class JevConfigFlow(ConfigFlow, domain=DOMAIN):
    """Take an API key and the address to send it to, and prove the pair works."""

    VERSION = 1
    # 2: the unique id hashes the endpoint with the key. async_migrate_entry moves
    # entries written before that.
    MINOR_VERSION = 2

    async def _async_validate(
        self, api_key: str, base_url: str, model: str
    ) -> str | None:
        """Return an error key, or None when that endpoint answers this request."""
        client = JevClient(
            api_key,
            session=async_get_clientsession(self.hass),
            base_url=base_url,
            model=model,
        )
        try:
            await client.ask("ok", {"probe": Noul("Is this text in English?")})
        except JevAuthError:
            return "invalid_auth"
        except JevValidationError:
            # The probe's question is fixed, so the model id is the only part of
            # this request a typo can reach.
            return "invalid_model"
        except JevResponseError as err:
            # A 404 means the host answered and has nothing on that path, which
            # "could not reach the API" describes wrongly. It is what an address
            # carrying the request path already, or a gateway mounted elsewhere,
            # comes back as. jevclient does not expose the status, only its own
            # message, so tests/test_config_flow.py drives a real JevClient
            # against a 404 body: a message change fails there, not in the field.
            if str(err).startswith("HTTP 404"):
                return "not_found"
            return "cannot_connect"
        except JevError:
            return "cannot_connect"
        return None

    async def _async_update_credentials(
        self, entry: ConfigEntry, updates: dict[str, Any]
    ) -> ConfigFlowResult:
        """Store validated credentials on an existing entry, unique id and all.

        The unique id is the hash of the endpoint and the key, so a swap of
        either has to move it. Left where it was, it went on guarding the retired
        pair and stopped guarding the one now in use: a second entry could then be
        added with the same key.

        _abort_if_unique_id_configured is not the guard here, because it counts
        this entry too and re-entering the same key is a legal no-op. Only
        another entry already holding the new key is a collision.
        """
        new_id = entry_unique_id(
            # Reauth changes the key alone and leaves the endpoint where it is.
            updates.get(CONF_URL, _stored(entry)[0]),
            updates[CONF_API_KEY],
        )
        for other in self._async_current_entries(include_ignore=True):
            if other.entry_id != entry.entry_id and other.unique_id == new_id:
                return self.async_abort(reason="already_configured")
        await self.async_set_unique_id(new_id)
        return self.async_update_reload_and_abort(
            entry, unique_id=new_id, data_updates=updates
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key, base_url, model, errors = _credentials(user_input)
            if not errors:
                await self.async_set_unique_id(entry_unique_id(base_url, api_key))
                self._abort_if_unique_id_configured()
                if error := await self._async_validate(api_key, base_url, model):
                    errors["base"] = error
                else:
                    return self.async_create_entry(
                        title="Jev",
                        data={
                            CONF_API_KEY: api_key,
                            CONF_URL: base_url,
                            CONF_MODEL: model,
                        },
                    )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_SCHEMA,
                # The address is handed back after a failure so it does not have to
                # be retyped. The key is not: it is a secret, and the form is where
                # it is being corrected.
                # What was typed, not what it normalised to, so a bad value comes
                # back to be corrected rather than silently replaced.
                {CONF_ADVANCED: user_input.get(CONF_ADVANCED, {})} if user_input else {},
            ),
            errors=errors,
            description_placeholders=FORM_PLACEHOLDERS,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            entry = self._get_reauth_entry()
            base_url, model = _stored(entry)
            # The same rules as the first form. A pasted key with a trailing
            # newline was stored as it was and hashed into the unique id with it.
            api_key = (user_input.get(CONF_API_KEY) or "").strip()
            if not api_key and base_url == DEFAULT_BASE_URL:
                errors[CONF_API_KEY] = "key_required"
            elif error := await self._async_validate(api_key, base_url, model):
                errors["base"] = error
            else:
                return await self._async_update_credentials(
                    entry, {CONF_API_KEY: api_key}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_SCHEMA,
            errors=errors,
            description_placeholders=FORM_PLACEHOLDERS,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Swap the key or the endpoint without losing the entities and their history."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key, base_url, model, errors = _credentials(user_input)
            # The form never shows the key back, so an empty field while the
            # address stays put means keep it. A new address gets no key it was not
            # given, because the key would travel to a host the user did not pick
            # it for.
            if not api_key and base_url == _stored(entry)[0]:
                api_key = entry.data.get(CONF_API_KEY, "")
                errors.pop(CONF_API_KEY, None)
            if not errors:
                if error := await self._async_validate(api_key, base_url, model):
                    errors["base"] = error
                else:
                    return await self._async_update_credentials(
                        entry,
                        {
                            CONF_API_KEY: api_key,
                            CONF_URL: base_url,
                            CONF_MODEL: model,
                        },
                    )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_SCHEMA,
                # The key is never shown back, the section always is: neither field
                # is a secret, and retyping them to change only the key is a way to
                # get them wrong.
                _suggest(*_stored(entry)),
            ),
            errors=errors,
            description_placeholders=FORM_PLACEHOLDERS,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: Any) -> JevOptionsFlow:
        return JevOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Questions are added one at a time, in the UI, without a YAML file."""
        return {SUBENTRY_QUESTION: JevQuestionSubentryFlow}


class JevOptionsFlow(OptionsFlow):
    """Spending limits and how the conversation agent should behave.

    The budget is a tripwire, not a quota to run against: put it past anything a
    working configuration would ever use, so only a runaway touches it.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_DAILY_TOKEN_BUDGET,
                    default=options.get(CONF_DAILY_TOKEN_BUDGET, 0),
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
                vol.Optional(
                    CONF_PRICE_PER_MILLION,
                    default=options.get(
                        CONF_PRICE_PER_MILLION, USD_PER_MILLION_INPUT_TOKENS
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional(
                    CONF_FALLBACK_AGENT,
                    description={"suggested_value": options.get(CONF_FALLBACK_AGENT)},
                ): selector.ConversationAgentSelector(
                    selector.ConversationAgentSelectorConfig()
                ),
                vol.Optional(
                    CONF_MIN_CONFIDENCE,
                    default=options.get(CONF_MIN_CONFIDENCE, DEFAULT_MIN_CONFIDENCE),
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
                vol.Optional(
                    CONF_ALLOW_WHOLE_HOME,
                    default=options.get(CONF_ALLOW_WHOLE_HOME, False),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
