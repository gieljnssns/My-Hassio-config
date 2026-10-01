"""Ask Jev typed questions about the state of your house.

One context is one API call. Every question attached to a context is evaluated in
isolation against the same rendered state, so questions batch almost for free in
time. They are not free in money: question text is billed as input tokens.
"""

from __future__ import annotations

import ipaddress
import logging
from datetime import datetime
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_URL,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify
from jevclient import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    USD_PER_MILLION_INPUT_TOKENS,
    JevAuthError,
    JevClient,
    JevError,
    Noul,
)
from yarl import URL

from .const import (
    CONF_BACKGROUND,
    CONF_CRITERIA,
    CONF_DAILY_TOKEN_BUDGET,
    CONF_ENTITIES,
    CONF_FALSE,
    CONF_INCLUDE_ATTRIBUTES,
    CONF_INSTRUCTIONS,
    CONF_MODEL,
    CONF_PRICE_PER_MILLION,
    CONF_QUESTIONS,
    CONF_STATE_TEMPLATE,
    CONF_THRESHOLD,
    CONF_TRIGGER_ENTITIES,
    CONF_TRUE,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    ISSUE_BUDGET_EXCEEDED,
    MIN_UPDATE_INTERVAL_SECONDS,
    STORAGE_VERSION,
    TYPE_CHOICE,
    TYPE_NOUL,
    TYPE_SCORE,
)
from .coordinator import JevCoordinator, JevRuntimeData, UsageAccount
from .identity import entry_unique_id
from .models import ENTRY, ContextConfig, build_question_config
from .services import async_register_services
from .subentry import async_contexts_from_subentries

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.AI_TASK,
    Platform.BINARY_SENSOR,
    Platform.CONVERSATION,
    Platform.SENSOR,
]

type JevConfigEntry = ConfigEntry[JevRuntimeData]


def _check_question_shape(raw: dict[str, Any]) -> dict[str, Any]:
    """Reject a question the API would reject, and say which field is wrong.

    The round trip would cost a request and return a 422 naming a field the user
    never wrote, so the check belongs here.
    """
    kind = raw["type"]
    criteria = raw.get(CONF_CRITERIA)
    name = raw.get(CONF_NAME, "?")
    if kind == TYPE_NOUL:
        if criteria is not None:
            raise vol.Invalid(
                f"question {name!r}: a noul takes 'true:' and 'false:' descriptions, "
                f"not 'criteria:'"
            )
    elif kind == TYPE_CHOICE:
        if not isinstance(criteria, dict) or not 2 <= len(criteria) <= 255:
            raise vol.Invalid(
                f"question {name!r}: a choice needs 'criteria:' as a mapping of 2 to "
                f"255 options to a description (or to nothing), got "
                f"{len(criteria) if isinstance(criteria, dict) else 'none'}"
            )
    elif kind == TYPE_SCORE:
        if not isinstance(criteria, list) or not 2 <= len(criteria) <= 10:
            raise vol.Invalid(
                f"question {name!r}: a score needs 'criteria:' as an ordered list of "
                f"2 to 10 levels, lowest first, got "
                f"{len(criteria) if isinstance(criteria, list) else 'none'}"
            )
    if kind != TYPE_NOUL and (raw.get(CONF_TRUE) or raw.get(CONF_FALSE)):
        raise vol.Invalid(f"question {name!r}: 'true:' and 'false:' apply to a noul only")
    if kind != TYPE_NOUL and raw.get(CONF_THRESHOLD) is not None:
        raise vol.Invalid(
            f"question {name!r}: 'threshold:' makes a binary sensor out of a noul, "
            f"and applies to a noul only"
        )
    return raw


QUESTION_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_NAME): cv.string,
            vol.Required("type"): vol.In([TYPE_NOUL, TYPE_CHOICE, TYPE_SCORE]),
            # instructions and every criteria value take a string, an object or
            # an array. The model is trained to read structure, so a rubric with
            # what/not_for/examples per option can go in as JSON rather than being
            # flattened into one sentence.
            vol.Required(CONF_INSTRUCTIONS): ENTRY,
            vol.Optional(CONF_TRUE): ENTRY,
            vol.Optional(CONF_FALSE): ENTRY,
            vol.Optional(CONF_CRITERIA): vol.Any(
                {cv.string: vol.Any(ENTRY, None)}, [ENTRY]
            ),
            vol.Optional(CONF_THRESHOLD): vol.All(
                vol.Coerce(float), vol.Range(min=0.0, max=1.0)
            ),
            vol.Optional(CONF_BACKGROUND): vol.Any(cv.string, dict, list),
        }
    ),
    _check_question_shape,
)

# A list of entity ids is the short form of the full picker, which is what almost
# everyone wants to write.
TARGET_SCHEMA = vol.Schema(
    {
        vol.Optional("entity_id"): cv.entity_ids,
        vol.Optional("device_id"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("area_id"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("floor_id"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("label_id"): vol.All(cv.ensure_list, [cv.string]),
    }
)


def _entities_to_selector(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        validated: dict[str, Any] = TARGET_SCHEMA(value)
        return validated
    return {"entity_id": cv.entity_ids(value)}


def _check_context_has_input(raw: dict[str, Any]) -> dict[str, Any]:
    if not raw.get(CONF_STATE_TEMPLATE) and not raw.get(CONF_ENTITIES):
        raise vol.Invalid(
            f"context {raw.get(CONF_NAME, '?')!r}: give it 'entities:' to look at, "
            f"'state:' to write the text yourself, or both"
        )
    return raw


def _first_duplicate_slug(names: list[str]) -> tuple[str, str] | None:
    """The first pair of names that slugify the same, in the order written.

    Names become keys through slugify, so 'Laundry forgotten' and
    'laundry-forgotten' are the same key even though they read as two questions.
    """
    seen: dict[str, str] = {}
    for name in names:
        key = slugify(name)
        if key in seen:
            return seen[key], name
        seen[key] = name
    return None


def _check_question_names_unique(raw: dict[str, Any]) -> dict[str, Any]:
    """Reject two questions in one context whose names give the same key.

    The key is what the API answer is keyed by and what the entity's unique_id is
    built from, so a collision sent one question instead of two and let Home
    Assistant drop the second entity. The user paid for a question never asked.
    """
    pair = _first_duplicate_slug([q[CONF_NAME] for q in raw[CONF_QUESTIONS]])
    if pair is not None:
        raise vol.Invalid(
            f"context {raw.get(CONF_NAME, '?')!r}: questions {pair[0]!r} and "
            f"{pair[1]!r} both become the key {slugify(pair[1])!r}, so only one of "
            f"them would be asked. Give them names that differ by more than "
            f"punctuation or case"
        )
    return raw


def _check_context_names_unique(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reject two contexts whose names give the same key.

    The second one replaced the first in the coordinator map. The first still had
    a live trigger and a debouncer that unload never reached, because unload walks
    that same map.
    """
    pair = _first_duplicate_slug([c[CONF_NAME] for c in contexts])
    if pair is not None:
        raise vol.Invalid(
            f"contexts {pair[0]!r} and {pair[1]!r} both become the key "
            f"{slugify(pair[1])!r}, so only the second one would run. Give them "
            f"names that differ by more than punctuation or case"
        )
    return contexts


CONTEXT_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_STATE_TEMPLATE): cv.template,
            vol.Optional(CONF_ENTITIES): _entities_to_selector,
            vol.Optional(CONF_INCLUDE_ATTRIBUTES, default=False): cv.boolean,
            vol.Optional(
                CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_SECONDS
            ): vol.All(vol.Coerce(int), vol.Range(min=MIN_UPDATE_INTERVAL_SECONDS)),
            vol.Optional(CONF_TRIGGER_ENTITIES, default=[]): cv.entity_ids,
            vol.Required(CONF_QUESTIONS): vol.All(
                cv.ensure_list, [QUESTION_SCHEMA], vol.Length(min=1)
            ),
        }
    ),
    _check_context_has_input,
    _check_question_names_unique,
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [CONTEXT_SCHEMA], _check_context_names_unique)},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Read the YAML contexts. The API key itself comes from the config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["yaml"] = config.get(DOMAIN, [])
    async_register_services(hass)
    return True


def _build_contexts(hass: HomeAssistant, entry: JevConfigEntry) -> list[ContextConfig]:
    """The YAML contexts, for the one entry that owns them.

    YAML does not name an entry. Given to every entry, each context was asked once
    per entry and billed that many times, so only the first enabled entry gets them.
    """
    owner = next(
        (e for e in hass.config_entries.async_entries(DOMAIN) if e.disabled_by is None),
        None,
    )
    if owner is None or owner.entry_id != entry.entry_id:
        return []
    contexts: list[ContextConfig] = []
    for raw in hass.data[DOMAIN].get("yaml", []):
        context_key = slugify(raw[CONF_NAME])
        questions = [
            build_question_config(q, f"{context_key}_{slugify(q[CONF_NAME])}")
            for q in raw[CONF_QUESTIONS]
        ]
        template = raw.get(CONF_STATE_TEMPLATE)
        if template is not None:
            template.hass = hass
        contexts.append(
            ContextConfig(
                key=context_key,
                name=raw[CONF_NAME],
                template=template,
                selector=raw.get(CONF_ENTITIES),
                include_attributes=raw[CONF_INCLUDE_ATTRIBUTES],
                questions=questions,
                scan_interval=raw[CONF_SCAN_INTERVAL],
                trigger_entities=raw[CONF_TRIGGER_ENTITIES],
            )
        )
    return contexts


def _warn_if_key_travels_in_clear(base_url: str, api_key: str) -> None:
    """Say so, once per setup, when the key is sent over plain HTTP.

    Authorization is a bearer header, so an http endpoint puts the key on the wire
    in clear. On a LAN that is a deliberate trade and not this integration's call to
    refuse, but it is not something to leave unsaid either. Loopback is exempt: that
    traffic never reaches a network, and an entry with no key sends no header to
    read.
    """
    if not api_key:
        return
    url = URL(base_url)
    if url.scheme != "http" or not (host := url.host):
        return
    if host == "localhost":
        return
    try:
        if ipaddress.ip_address(host).is_loopback:
            return
    except ValueError:
        pass
    _LOGGER.warning(
        "The API key is sent to %s in clear, because %s is a plain HTTP address. "
        "Anything that can see that traffic can read the key. Use https, or keep "
        "the endpoint on a network you trust",
        base_url,
        url.scheme,
    )


async def async_migrate_entry(hass: HomeAssistant, entry: JevConfigEntry) -> bool:
    """Move an entry's unique id to the endpoint-and-key hash.

    Until 1.14.0 it hashed the key alone. Recomputing it here, rather than at the
    next reconfigure, is what keeps the duplicate guard working: the flow compares
    the id it computes for a new entry against the ids already stored, and an
    entry still in the old format matches nothing, so the same key could be added
    a second time.
    """
    if entry.minor_version < 2:
        hass.config_entries.async_update_entry(
            entry,
            unique_id=entry_unique_id(
                entry.data.get(CONF_URL, DEFAULT_BASE_URL),
                entry.data.get(CONF_API_KEY, ""),
            ),
            minor_version=2,
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: JevConfigEntry) -> bool:
    """Set up one API key, its usage account and a coordinator per context."""
    # Entries made before these were configurable carry neither, and mean the
    # published API and its default model, which is what they have always used.
    base_url = entry.data.get(CONF_URL, DEFAULT_BASE_URL)
    # An entry that names an endpoint of its own may hold no key at all.
    api_key = entry.data.get(CONF_API_KEY, "")
    _warn_if_key_travels_in_clear(base_url, api_key)
    model = entry.data.get(CONF_MODEL, DEFAULT_MODEL)
    client = JevClient(
        api_key,
        session=async_get_clientsession(hass),
        base_url=base_url,
        model=model,
    )
    store: Store[dict[str, Any]] = Store(
        hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}.usage"
    )
    usage = UsageAccount(
        day=dt_util.now().date(),
        budget=entry.options.get(CONF_DAILY_TOKEN_BUDGET, 0),
        price_per_million=entry.options.get(
            CONF_PRICE_PER_MILLION, USD_PER_MILLION_INPUT_TOKENS
        ),
        store=store,
        hass=hass,
        entry_id=entry.entry_id,
    )
    usage.restore(await store.async_load())
    # Before 1.10.0 every entry raised this warning under one shared id and
    # nothing ever deleted it. Clear that one, once, on the way past.
    ir.async_delete_issue(hass, DOMAIN, ISSUE_BUDGET_EXCEEDED)
    # An options change reloads the entry, which builds this account fresh with
    # the new budget and the flag clear. The repair issue lives in the registry
    # and survives that, so setting it from the restored count here is what makes
    # "raise the budget in the options" actually work. Clearing it outright would
    # be wrong: the count is restored too, and the probe below can fail, which
    # leaves an exhausted budget with nothing on screen to say so.
    usage.set_budget_exceeded(usage.would_exceed(), used=usage.input_tokens)
    runtime = JevRuntimeData(client=client, usage=usage, model=model)
    entry.runtime_data = runtime

    # The day otherwise turns over at the first call after midnight, so a quiet
    # night kept yesterday's spend on the usage sensors, and a spent budget kept
    # its repair issue, until something asked.
    @callback
    def _new_day(now: datetime) -> None:
        usage.roll_over(now.date())
        usage.notify()

    entry.async_on_unload(
        async_track_time_change(hass, _new_day, hour=0, minute=0, second=0)
    )

    # Prove the service answers before entities appear. One noul against a two word
    # state costs about 40 input tokens, well under a thousandth of a cent, and it
    # is the difference between a clear "cannot reach TypeSafe" and a house full of
    # entities that never populate. It is billed like any other call, so it counts
    # against the day, and a spent budget skips it.
    try:
        if not usage.would_exceed():
            response = await client.ask("ok", {"probe": Noul("Is this text in English?")})
            # No payload size: this request is mostly fixed overhead, and its ratio
            # of bytes to tokens would skew the estimate for the real ones.
            usage.record(response.usage.input_tokens)
    except JevAuthError as err:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="auth_rejected",
            translation_placeholders={"reason": str(err)},
        ) from err
    except JevError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="ask_failed",
            translation_placeholders={"reason": str(err)},
        ) from err

    contexts = _build_contexts(hass, entry) + async_contexts_from_subentries(hass, entry)
    for context in contexts:
        coordinator = JevCoordinator(hass, entry, runtime, context)
        runtime.coordinators[context.key] = coordinator
        # Deliberately not async_config_entry_first_refresh: that aborts setup when
        # the first evaluation fails, and the two ways it fails are a spent budget
        # and an unreachable API. Both are states the user needs to see explained,
        # and the budget and usage entities that explain them only exist once setup
        # finishes. Answers stay unavailable instead. A context whose entities are
        # all disabled has no reader for the answer, so it is not asked at all.
        if not coordinator.nobody_reads():
            await coordinator.async_refresh()
        await coordinator.async_setup_triggers()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: JevConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: JevConfigEntry) -> bool:
    """Unload platforms and stop every trigger listener this entry created."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        for coordinator in entry.runtime_data.coordinators.values():
            coordinator.async_shutdown_triggers()
        await entry.runtime_data.usage.async_flush()
    return unloaded
