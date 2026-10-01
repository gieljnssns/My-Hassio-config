"""The actions.

One action per question type, because a mapping of question objects is a lot to ask
of someone writing their first automation, and three quarters of the uses only ever
need one question. `jev.ask` stays for the case the other three cannot express:
several questions about the same state, answered in one request.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import (
    HomeAssistantError,
    ServiceValidationError,
    TemplateError,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util
from jevclient import (
    MAX_CHOICE_OPTIONS,
    MAX_SCORE_LEVELS,
    MIN_CHOICE_OPTIONS,
    MIN_SCORE_LEVELS,
    Choice,
    ChoiceAnswer,
    JevAuthError,
    JevError,
    JevResponse,
    Noul,
    NoulAnswer,
    Question,
    Score,
    ScoreAnswer,
)

if TYPE_CHECKING:
    from . import JevConfigEntry

from .const import (
    ATTR_ANSWERS,
    ATTR_CONFIG_ENTRY,
    ATTR_LATENCY_MS,
    ATTR_QUESTIONS,
    ATTR_USAGE,
    CONF_BACKGROUND,
    CONF_FALSE_MEANS,
    CONF_INCLUDE_ATTRIBUTES,
    CONF_INSTRUCTIONS,
    CONF_LEVELS,
    CONF_OPTION_DESCRIPTIONS,
    CONF_OPTIONS,
    CONF_STATE_TEMPLATE,
    CONF_THRESHOLD,
    CONF_TRUE_MEANS,
    DOMAIN,
    SERVICE_ASK,
    SERVICE_CHOICE,
    SERVICE_NOUL,
    SERVICE_SCORE,
    TYPE_CHOICE,
    TYPE_NOUL,
    TYPE_SCORE,
)
from .models import ENTRY, build_question, compose_instructions
from .payload import payload_bytes
from .statebuilder import async_build_state

_LOGGER = logging.getLogger(__name__)

# What the target picker puts in call.data, which must not reach the question body.
TARGET_KEYS = ("entity_id", "device_id", "area_id", "floor_id", "label_id")

_BASE = {
    vol.Optional(CONF_STATE_TEMPLATE): vol.Any(cv.string, dict, list),
    vol.Optional(CONF_BACKGROUND): ENTRY,
    vol.Optional(ATTR_CONFIG_ENTRY): cv.string,
    vol.Optional(CONF_INCLUDE_ATTRIBUTES, default=False): cv.boolean,
    vol.Required(CONF_INSTRUCTIONS): ENTRY,
    **cv.TARGET_SERVICE_FIELDS,
}

NOUL_SCHEMA = vol.Schema(
    {
        **_BASE,
        vol.Optional(CONF_TRUE_MEANS): ENTRY,
        vol.Optional(CONF_FALSE_MEANS): ENTRY,
        vol.Optional(CONF_THRESHOLD, default=0.5): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=1.0)
        ),
    }
)

CHOICE_SCHEMA = vol.Schema(
    {
        **_BASE,
        vol.Required(CONF_OPTIONS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_OPTION_DESCRIPTIONS, default={}): dict,
    }
)

SCORE_SCHEMA = vol.Schema(
    {
        **_BASE,
        vol.Required(CONF_LEVELS): vol.All(cv.ensure_list, [ENTRY]),
    }
)

ASK_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_STATE_TEMPLATE): vol.Any(cv.string, dict, list),
        # An empty mapping is still a billed request, answered with nothing.
        vol.Required(ATTR_QUESTIONS): vol.All(
            vol.Schema({cv.string: dict}), vol.Length(min=1)
        ),
        vol.Optional(ATTR_CONFIG_ENTRY): cv.string,
        vol.Optional(CONF_INCLUDE_ATTRIBUTES, default=False): cv.boolean,
        **cv.TARGET_SERVICE_FIELDS,
    }
)


def _render(hass: HomeAssistant, value: Any) -> Any:
    """Render a template that reached us unrendered.

    A script renders action data before we see it, so this only fires for a call
    made straight from the developer tools or the REST API, where nothing else
    would. Anything already rendered no longer contains the markers.
    """
    if not isinstance(value, str) or ("{{" not in value and "{%" not in value):
        return value
    try:
        return Template(value, hass).async_render(parse_result=False)
    except TemplateError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="template_failed",
            translation_placeholders={"reason": str(err)},
        ) from err


def _typed(answer: Any, expected: type, question_type: str) -> Any:
    """The API is schema-guaranteed, so this only fires if that guarantee breaks.

    A bare assert would say nothing about what arrived, and disappears entirely
    under python -O.
    """
    if not isinstance(answer, expected):
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="wrong_answer_type",
            translation_placeholders={
                "question_type": question_type,
                "got": type(answer).__name__,
            },
        )
    return answer


def _instructions(call: ServiceCall) -> Any:
    return compose_instructions(
        call.data[CONF_INSTRUCTIONS], call.data.get(CONF_BACKGROUND)
    )


def _entry(hass: HomeAssistant, call: ServiceCall) -> JevConfigEntry:
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    if wanted := call.data.get(ATTR_CONFIG_ENTRY):
        entries = [e for e in entries if e.entry_id == wanted]
    if not entries:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="no_entry"
        )
    # Each entry has its own key and budget, so taking the first would bill
    # whichever one happened to load first.
    if len(entries) > 1:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_ambiguous",
            translation_placeholders={
                "entries": ", ".join(sorted(e.title for e in entries))
            },
        )
    return entries[0]


async def _ask(
    hass: HomeAssistant, call: ServiceCall, questions: dict[str, Question]
) -> JevResponse:
    """Send one request and account for what it cost."""
    entry = _entry(hass, call)
    selector = {
        key: value for key, value in call.data.items() if key in TARGET_KEYS and value
    }
    if not selector and not call.data.get(CONF_STATE_TEMPLATE):
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="nothing_to_judge"
        )
    state = async_build_state(
        hass,
        _render(hass, call.data.get(CONF_STATE_TEMPLATE)),
        selector,
        call.data[CONF_INCLUDE_ATTRIBUTES],
    )
    _LOGGER.debug(
        "asking %s question(s) about a %s state: %s",
        len(questions),
        type(state).__name__,
        state,
    )
    request_bytes = payload_bytes(state, questions, entry.runtime_data.model)
    try:
        response = await entry.runtime_data.client.ask(state, questions)
    except JevAuthError as err:
        entry.async_start_reauth(hass)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="auth_rejected",
            translation_placeholders={"reason": str(err)},
        ) from err
    except JevError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="ask_failed",
            translation_placeholders={"reason": str(err)},
        ) from err
    usage = entry.runtime_data.usage
    usage.roll_over(dt_util.now().date())
    usage.record(response.usage.input_tokens, request_bytes)
    entry.runtime_data.model_version = response.model or entry.runtime_data.model_version
    usage.notify()
    return response


def _envelope(response: JevResponse) -> dict[str, Any]:
    return {
        "model": response.model,
        ATTR_LATENCY_MS: round(response.latency_ms, 1),
        ATTR_USAGE: {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }


def answer_as_dict(answer: Any) -> dict[str, Any]:
    """Flatten one answer so a template can read it without knowing the classes."""
    if isinstance(answer, NoulAnswer):
        return {"type": TYPE_NOUL, "noul": answer.noul}
    if isinstance(answer, ChoiceAnswer):
        return {
            "type": TYPE_CHOICE,
            "choice": answer.choice,
            "probabilities": answer.probabilities,
            "confidence": answer.confidence,
        }
    if isinstance(answer, ScoreAnswer):
        return {
            "type": TYPE_SCORE,
            "score": answer.score,
            "normalized": round(answer.normalized, 4),
            "nearest_level": answer.nearest_level,
            "legend": answer.legend,
            "probabilities": answer.probabilities,
            "confidence": answer.confidence,
        }
    # Reached only if the client grows a fourth answer type, which a user meets as
    # a library upgrade rather than as a bug in their configuration.
    raise HomeAssistantError(
        translation_domain=DOMAIN,
        translation_key="unreadable_answer",
        translation_placeholders={"kind": type(answer).__name__},
    )


def async_register_services(hass: HomeAssistant) -> None:
    """Register all four actions once, the first time the component loads."""
    if hass.services.has_service(DOMAIN, SERVICE_NOUL):
        return

    async def _noul(call: ServiceCall) -> ServiceResponse:
        question = Noul(
            _instructions(call),
            true=call.data.get(CONF_TRUE_MEANS),
            false=call.data.get(CONF_FALSE_MEANS),
        )
        response = await _ask(hass, call, {"answer": question})
        answer = _typed(response.answers["answer"], NoulAnswer, TYPE_NOUL)
        threshold = call.data[CONF_THRESHOLD]
        return {
            "noul": answer.noul,
            # The docs are explicit that a value near 0.5 means the model cannot
            # tell, not that the answer is halfway true, so the boolean is the
            # caller's threshold and nothing more.
            "is_true": answer.noul >= threshold,
            "threshold": threshold,
            **_envelope(response),
        }

    async def _choice(call: ServiceCall) -> ServiceResponse:
        descriptions = call.data[CONF_OPTION_DESCRIPTIONS]
        criteria = {
            option: descriptions.get(option) for option in call.data[CONF_OPTIONS]
        }
        try:
            question = Choice(_instructions(call), criteria)
        except ValueError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="choice_options_out_of_range",
                translation_placeholders={
                    "min": str(MIN_CHOICE_OPTIONS),
                    "max": str(MAX_CHOICE_OPTIONS),
                    "count": str(len(criteria)),
                },
            ) from err
        response = await _ask(hass, call, {"answer": question})
        answer = _typed(response.answers["answer"], ChoiceAnswer, TYPE_CHOICE)
        return {
            "choice": answer.choice,
            "confidence": answer.confidence,
            "probabilities": answer.probabilities,
            **_envelope(response),
        }

    async def _score(call: ServiceCall) -> ServiceResponse:
        try:
            question = Score(_instructions(call), call.data[CONF_LEVELS])
        except ValueError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="score_levels_out_of_range",
                translation_placeholders={
                    "min": str(MIN_SCORE_LEVELS),
                    "max": str(MAX_SCORE_LEVELS),
                    "count": str(len(call.data[CONF_LEVELS])),
                },
            ) from err
        response = await _ask(hass, call, {"answer": question})
        answer = _typed(response.answers["answer"], ScoreAnswer, TYPE_SCORE)
        return {
            "score": answer.score,
            # Two rubrics of different lengths are not comparable until each is
            # divided by its own top level, which is what a weighted composite needs.
            "normalized": round(answer.normalized, 4),
            "nearest_level": answer.nearest_level,
            "confidence": answer.confidence,
            "legend": answer.legend,
            "probabilities": answer.probabilities,
            **_envelope(response),
        }

    async def _ask_many(call: ServiceCall) -> ServiceResponse:
        questions: dict[str, Question] = {}
        for key, raw in call.data[ATTR_QUESTIONS].items():
            if "type" not in raw or CONF_INSTRUCTIONS not in raw:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="question_shape",
                    translation_placeholders={"key": key},
                )
            try:
                questions[key] = build_question(raw)
            except (KeyError, ValueError) as err:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="question_invalid",
                    translation_placeholders={"key": key, "reason": str(err)},
                ) from err
        response = await _ask(hass, call, questions)
        return {
            ATTR_ANSWERS: {k: answer_as_dict(v) for k, v in response.answers.items()},
            **_envelope(response),
        }

    for name, handler, schema in (
        (SERVICE_NOUL, _noul, NOUL_SCHEMA),
        (SERVICE_CHOICE, _choice, CHOICE_SCHEMA),
        (SERVICE_SCORE, _score, SCORE_SCHEMA),
        (SERVICE_ASK, _ask_many, ASK_SCHEMA),
    ):
        hass.services.async_register(
            DOMAIN, name, handler, schema=schema, supports_response=SupportsResponse.ONLY
        )
