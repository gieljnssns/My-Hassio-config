"""A conversation agent that routes spoken commands through Jev.

What this does that a sentence matcher cannot: it understands a command that was
not phrased the way the template expected. What it does that an LLM agent does not:
it runs one typed request, costs a fraction of a cent, and hands back a confidence
figure the router can refuse to act on.

Three things shape the design.

The house it sees is the Assist exposure list and nothing wider. The user already
decided which entities a voice assistant may touch.

Every command it understands runs a built-in intent, not a service call. Intents
carry Home Assistant's own matching, its own spoken responses in every supported
language, and its own permission checks. Reimplementing that would mean
reimplementing it worse.

Anything it is not sure about goes to the fallback agent whole, with no partial
action taken first. A voice assistant that half-acts is worse than one that says
it did not understand.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Literal

from homeassistant.components import conversation
from homeassistant.components.conversation.models import AbstractConversationAgent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_DEVICE_CLASS, MATCH_ALL
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import intent as ha_intent
from homeassistant.helpers import template, translation
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util
from homeassistant.util import language as language_util
from jevclient import JevAuthError, JevError

from .const import (
    CONF_ALLOW_WHOLE_HOME,
    CONF_FALLBACK_AGENT,
    CONF_MIN_CONFIDENCE,
    DEFAULT_MIN_CONFIDENCE,
    DOMAIN,
    MAX_CONVERSATION_ENTITIES,
)
from .coordinator import JevRuntimeData
from .entity import build_device_info
from .interpret import build_questions, interpret
from .snapshot import async_snapshot

_LOGGER = logging.getLogger(__name__)

# Used when a translation is missing, so a missing key is still a sentence rather
# than a blank reply. Kept in step with strings.json by a test.
_FALLBACK = {
    "not_understood": "Sorry, I did not understand that.",
    "whole_house": (
        "That would affect the whole house. Say which room or which device you mean."
    ),
    "which_kind": (
        "Which kind of thing do you mean? Say the lights, or the switches, or name "
        "a room."
    ),
    "intent_failed": "Sorry, that did not work.",
    "already_on": "{name} is already on.",
    "already_off": "{name} is already off.",
    "query_not_found": "I could not find that.",
    "budget_spent": "The daily token budget is spent, so I cannot do that today.",
    "auth_failed": "TypeSafe rejected the API key. Check it in the Jev settings.",
    "unavailable": "TypeSafe did not answer. Try again in a moment.",
}

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([JevConversationEntity(entry)])


class JevConversationEntity(conversation.ConversationEntity, AbstractConversationAgent):
    """Routes one sentence, then gets out of the way."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = conversation.ConversationEntityFeature.CONTROL

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_conversation"
        runtime: JevRuntimeData = entry.runtime_data
        self._attr_device_info = build_device_info(entry.entry_id, runtime)

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Whatever the intents support.

        Jev reads the sentence and Home Assistant speaks the reply, so the limit is
        the intent layer's, not ours.
        """
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self._entry, self)

    async def async_will_remove_from_hass(self) -> None:
        conversation.async_unset_agent(self.hass, self._entry)
        await super().async_will_remove_from_hass()

    # --- options ---

    @property
    def _min_confidence(self) -> float:
        return float(self._entry.options.get(CONF_MIN_CONFIDENCE, DEFAULT_MIN_CONFIDENCE))

    @property
    def _fallback_agent(self) -> str | None:
        agent = self._entry.options.get(CONF_FALLBACK_AGENT)
        # Pointing the fallback at this entity would recurse until something gave
        # way. Refusing it here is cheaper than detecting the loop later.
        if not agent or agent == self.entity_id:
            return None
        # Another Jev agent is the same loop one step removed: two entries that fall
        # back to each other pass the sentence between them and pay each time.
        registered = er.async_get(self.hass).async_get(agent)
        entry = self.hass.config_entries.async_get_entry(agent)
        if (registered and registered.platform == DOMAIN) or (
            entry and entry.domain == DOMAIN
        ):
            return None
        return str(agent)

    @property
    def _allow_whole_home(self) -> bool:
        return bool(self._entry.options.get(CONF_ALLOW_WHOLE_HOME, False))

    # --- the router ---

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        runtime: JevRuntimeData = self._entry.runtime_data

        # The budget covers voice as well as sensors, because a satellite that
        # mishears a wake word all night is exactly the runaway it exists to stop.
        runtime.usage.roll_over(dt_util.now().date())
        if runtime.usage.would_exceed():
            return await self._fall_back(
                user_input, "the daily token budget is spent", "budget_spent"
            )

        snapshot = async_snapshot(self.hass, MAX_CONVERSATION_ENTITIES)
        if not snapshot.entities:
            return await self._fall_back(user_input, "no entities are exposed to Assist")

        questions = build_questions(user_input.text, snapshot, MAX_CONVERSATION_ENTITIES)
        state = snapshot.as_state() | {"command": user_input.text}

        try:
            response = await runtime.client.ask(state, questions)
        except JevAuthError as err:
            _LOGGER.error("TypeSafe rejected the API key: %s", err)
            self._entry.async_start_reauth(self.hass)
            return await self._fall_back(
                user_input, "the API key was rejected", "auth_failed"
            )
        except JevError as err:
            _LOGGER.warning("TypeSafe did not answer: %s", err)
            return await self._fall_back(
                user_input, f"TypeSafe did not answer: {err}", "unavailable"
            )

        runtime.usage.record(response.usage.input_tokens)
        runtime.model_version = response.model or runtime.model_version
        runtime.usage.notify()

        decision = interpret(response, user_input.text, snapshot, self._min_confidence)
        runtime.conversation_traces.appendleft(
            {
                "text": user_input.text,
                "latency_ms": response.latency_ms,
                "input_tokens": response.usage.input_tokens,
                "exposed_entities": len(snapshot.entities),
                **asdict(decision),
            }
        )

        if decision.already_satisfied is not None:
            name, settled = decision.already_satisfied
            return await self._speak(user_input, f"already_{settled}", name=name)

        if decision.should_fall_back:
            return await self._fall_back(user_input, decision.reason)

        # The whole-home gate. "Turn everything off" is a real command and a
        # harmless one. "Turn everything on" at 3am, from a sentence the model was
        # only somewhat sure about, is not something to do silently. Off is allowed
        # because its worst case is a dark house; anything else asks first.
        if decision.targets_everything:
            if not self._allow_whole_home and decision.action != "turn_off":
                return await self._speak(user_input, "whole_house")
            # Home Assistant refuses "all" with no kind of device beside it, and an
            # unbounded command is not something to infer from one sentence anyway.
            if "domain" not in decision.slots:
                return await self._speak(user_input, "which_kind")

        assert decision.intent_type is not None
        try:
            intent_response = await ha_intent.async_handle(
                self.hass,
                DOMAIN,
                decision.intent_type,
                decision.slots,
                user_input.text,
                user_input.context,
                language=user_input.language,
                assistant=conversation.DOMAIN,
                device_id=user_input.device_id,
                satellite_id=user_input.satellite_id,
                conversation_agent_id=user_input.agent_id,
            )
        except ha_intent.MatchFailedError as err:
            # The model named something the intent layer could not find. That is a
            # miss, not a failure, so the fallback agent gets the sentence intact.
            _LOGGER.debug("intent %s matched nothing: %s", decision.intent_type, err)
            return await self._fall_back(user_input, "the named target was not found")
        except ha_intent.IntentError as err:
            _LOGGER.error("intent %s failed: %s", decision.intent_type, err)
            return await self._speak(user_input, "intent_failed")

        # Only a state question needs our lines, and loading them reads translations.
        if intent_response.response_type is ha_intent.IntentResponseType.QUERY_ANSWER:
            language = user_input.language or self.hass.config.language
            await _speak_the_answer(
                self.hass, intent_response, language, await self._lines(language)
            )
        return conversation.ConversationResult(
            response=intent_response, conversation_id=user_input.conversation_id
        )

    # --- the two ways out ---

    async def _fall_back(
        self,
        user_input: conversation.ConversationInput,
        why: str,
        line: str = "not_understood",
    ) -> conversation.ConversationResult:
        """Hand the whole sentence to the configured agent, having done nothing.

        With no agent to hand it to, say why, so a spent budget or a rejected key
        is not heard as a sentence the model failed to understand.
        """
        agent = self._fallback_agent
        _LOGGER.debug("falling back to %s because %s", agent or "nobody", why)
        if agent is None:
            return await self._speak(user_input, line)
        result = await conversation.async_converse(
            self.hass,
            user_input.text,
            user_input.conversation_id,
            user_input.context,
            language=user_input.language,
            agent_id=agent,
            device_id=user_input.device_id,
            satellite_id=user_input.satellite_id,
            extra_system_prompt=user_input.extra_system_prompt,
        )
        return result

    async def _lines(self, language: str) -> dict[str, str]:
        """This agent's own lines, in the language the pipeline is speaking.

        The intent layer localises its own replies, so anything this agent says
        itself has to be localised here or a Dutch pipeline answers in English.
        The English text is the last resort, so a missing key is still a sentence.

        This integration translates 13 languages. Home Assistant words two of these
        lines in all 63 that home-assistant-intents carries, so a pipeline speaking
        one of the other 50 hears a sentence rather than English. Our own wording
        wins wherever we have it.
        """
        ours = await translation.async_get_translations(
            self.hass, language, "common", [DOMAIN]
        )
        # The cache loads English underneath every language, so a language this
        # integration has not translated comes back as its English text rather than
        # missing. Two identical dictionaries is what tells those apart.
        shipped = None
        if not language_util.matches(language, {"en"}) and ours == (
            await translation.async_get_translations(self.hass, "en", "common", [DOMAIN])
        ):
            shipped = await _shipped(self.hass, language)
        lines = {}
        for key, fallback in _FALLBACK.items():
            text = None
            if shipped is not None and (name := _SHIPPED_SENTENCE.get(key)):
                text = shipped.errors.get(name)
            lines[key] = text or ours.get(f"component.{DOMAIN}.common.{key}", fallback)
        return lines

    async def _speak(
        self,
        user_input: conversation.ConversationInput,
        key: str,
        **placeholders: str,
    ) -> conversation.ConversationResult:
        """Say one of our own lines, with its placeholders filled in."""
        language = user_input.language or self.hass.config.language
        text = (await self._lines(language))[key]
        response = ha_intent.IntentResponse(language=user_input.language)
        response.async_set_speech(text.format(**placeholders))
        return conversation.ConversationResult(
            response=response, conversation_id=user_input.conversation_id
        )


# A template that compares the state against an English word writes the state word
# itself, in its own language. Hand it a translated one and every branch falls
# through. Measured against home-assistant-intents 2026.8.28: 3 of the 47 templates
# do this, Polish, Russian and Thai.
_COMPARES_STATE = re.compile(r"""==\s*['"](?:on|off|open|closed|locked|unlocked)['"]""")

# Home Assistant words these two in all 63 languages the intents package carries,
# against the 13 this integration translates. Saying what stock Assist says is the
# same choice the state answer makes.
_SHIPPED_SENTENCE = {"not_understood": "no_intent", "intent_failed": "handle_error"}


@dataclass(frozen=True, slots=True)
class _Shipped:
    """One language's share of home-assistant-intents."""

    state_answer: str | None
    writes_the_state_word: bool
    errors: Mapping[str, str]


# Read once per language, keyed by the language that was asked for rather than the
# variant it matched, so "it" and "it-IT" cost one load each. None means the
# package carries nothing for it and this agent falls back to English.
_SHIPPED: dict[str, _Shipped | None] = {}


def _load_shipped(language: str) -> _Shipped | None:
    """Read one language out of home-assistant-intents, in the executor.

    The package ships the answer template for a state question and the error
    sentences, both written by the people who translate the rest of Assist. Polish
    inflects the adjective by the last letter of the device name, Russian writes the
    state word in Russian, and German turns 21.5 into 21,5 Grad. None of that could
    be got right from a string table of this integration's own, and all of it reaches
    languages this integration does not translate.
    """
    try:
        from home_assistant_intents import (
            get_intents,
            get_languages,
        )
    except ImportError:  # pragma: no cover - the conversation integration installs it
        return None
    matches = language_util.matches(language, set(get_languages()))
    if not matches:
        return None
    intents = get_intents(matches[0])
    if not intents:
        return None
    responses = intents.get("responses", {})
    answer = responses.get("intents", {}).get("HassGetState", {}).get("one")
    if not isinstance(answer, str):
        answer = None
    return _Shipped(
        state_answer=answer,
        writes_the_state_word=bool(answer and _COMPARES_STATE.search(answer)),
        errors={
            key: text
            for key, text in responses.get("errors", {}).items()
            if isinstance(text, str) and text.strip()
        },
    )


async def _shipped(hass: HomeAssistant, language: str) -> _Shipped | None:
    """What home-assistant-intents carries for a language, loaded once."""
    if language not in _SHIPPED:
        _SHIPPED[language] = await hass.async_add_executor_job(_load_shipped, language)
    return _SHIPPED[language]


async def _state_word(hass: HomeAssistant, state: State, language: str) -> str | None:
    """Home Assistant's own word for this state, or None when it has none.

    The three keys `async_translate_state` reads, in its order: the entity's own
    translation key, then the device class, then the domain's default. That helper
    cannot be called here, because it reads `hass.config.language`, which is the
    language of the user interface and not the one this pipeline speaks.

    The device class layer is what makes a door answer "aperto" rather than
    "acceso", and a motion sensor "rilevato" rather than "on".

    Lower case, because the shipped words are interface labels and are capitalised
    for a badge. The finished sentence gets its first letter back below.
    """
    domain = state.domain
    entry = er.async_get(hass).async_get(state.entity_id)
    if entry is not None and entry.translation_key is not None:
        own = await translation.async_get_translations(
            hass, language, "entity", {entry.platform}
        )
        key = (
            f"component.{entry.platform}.entity.{domain}"
            f".{entry.translation_key}.state.{state.state}"
        )
        if word := own.get(key):
            return word.lower()
    words = await translation.async_get_translations(
        hass, language, "entity_component", {domain}
    )
    if (device_class := state.attributes.get(ATTR_DEVICE_CLASS)) is not None:
        key = f"component.{domain}.entity_component.{device_class}.state.{state.state}"
        if word := words.get(key):
            return word.lower()
    word = words.get(f"component.{domain}.entity_component._.state.{state.state}")
    return word.lower() if word else None


class _SpokenState(template.TemplateState):
    """A state whose `state_with_unit` reads in the language being spoken.

    The answer templates reach the state only through this property, so one
    substitution here turns "Luce Tavolo è off" into "Luce Tavolo è spento" without
    touching the sentence. A numeric state has no translation, so a sensor keeps
    its rounded value and its unit.
    """

    __slots__ = ("_word",)

    def __init__(self, hass: HomeAssistant, state: State, word: str | None) -> None:
        """Carry the translated word, or None to leave the state as it is."""
        super().__init__(hass, state)
        self._word = word

    @property
    def state_with_unit(self) -> str:
        """The state in the spoken language, or Home Assistant's own formatting."""
        if self._word is None:
            return super().state_with_unit
        return self._word


async def _render_state_answer(
    hass: HomeAssistant,
    matched: list[State],
    unmatched: list[State],
    language: str,
) -> str | None:
    """The sentence the default agent would have said, or None if it cannot."""
    shipped = await _shipped(hass, language)
    if shipped is None or shipped.state_answer is None:
        return None
    words: dict[str, str | None] = {}
    if not shipped.writes_the_state_word:
        for state in (*matched, *unmatched):
            words[state.entity_id] = await _state_word(hass, state, language)

    def spoken(state: State) -> _SpokenState:
        return _SpokenState(hass, state, words.get(state.entity_id))

    answer = template.Template(shipped.state_answer, hass)
    query = {
        "matched": [spoken(state) for state in matched],
        "unmatched": [spoken(state) for state in unmatched],
    }
    parts = []
    for state in matched:
        try:
            rendered = answer.async_render(
                {
                    "slots": {"name": state.name},
                    "state": spoken(state),
                    "query": query,
                },
                parse_result=False,
            )
        except TemplateError as err:
            _LOGGER.debug("the %s state answer did not render: %s", language, err)
            return None
        # The templates are written over several lines and indented. The default
        # agent collapses that the same way before speaking it.
        sentence = " ".join(str(rendered).split())
        if not sentence:
            continue
        # Brazilian Portuguese answers with the state alone and Russian answers
        # "Выключено", both without the name, because the default agent reaches this
        # template only after the user named one device. Several answers in a row
        # need the name back or they say nothing about which device is which.
        if len(matched) > 1 and state.name.casefold() not in sentence.casefold():
            sentence = f"{state.name}: {sentence}"
        # Every template capitalises the device name, so a sentence that starts with
        # the state word instead, as the Brazilian Portuguese one does, would start
        # in lower case. Only the first character moves: `str.capitalize` would lower
        # the rest of the sentence.
        parts.append(sentence[0].upper() + sentence[1:])
    return ", ".join(parts) if parts else None


async def _speak_the_answer(
    hass: HomeAssistant,
    response: ha_intent.IntentResponse,
    language: str,
    say: dict[str, str],
) -> None:
    """Say what a state question found, in the language the pipeline is speaking.

    `HassGetState` fills in the matched states and stops. The spoken sentence is
    normally written by the default agent's response templates, which run only for
    sentences the default agent itself matched, so routing the intent here leaves a
    correct answer nobody hears. This renders the same template the default agent
    would have used. An English sentence is the last resort, for a language the
    intents package does not carry.
    """
    if response.response_type is not ha_intent.IntentResponseType.QUERY_ANSWER:
        return
    if response.speech:
        return
    matched = response.matched_states
    if not matched:
        response.async_set_speech(say["query_not_found"])
        return
    spoken = await _render_state_answer(
        hass, list(matched), list(response.unmatched_states), language
    )
    if spoken is None:
        spoken = ", ".join(f"{state.name} is {state.state}" for state in matched) + "."
    response.async_set_speech(spoken)
