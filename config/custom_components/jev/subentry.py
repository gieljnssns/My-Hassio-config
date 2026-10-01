"""Questions built in the UI, one subentry each.

The YAML surface makes you declare a context: a named group of questions that
share one API call. That grouping is not a preference, it is derivable. TypeSafe
takes one state and N questions, so two questions can share a call exactly when
they describe the same state, and cannot when they do not, whatever the user
writes. A UI that asks for it would be asking the user to hand back an answer the
integration already has.

So a subentry is one question, carrying what it looks at and how often. The call
grouping is computed from those fields at setup, which keeps the measured saving
(three questions took 712 ms, a hundred took 714) without putting the word
"context" in front of anyone.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from hashlib import sha256
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import SectionConfig, section
from homeassistant.exceptions import (
    HomeAssistantError,
    ServiceValidationError,
    TemplateError,
)
from homeassistant.helpers import selector, translation
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util
from jevclient import (
    Answer,
    ChoiceAnswer,
    JevAuthError,
    JevError,
    NoulAnswer,
    ScoreAnswer,
)

from .const import (
    CONF_BACKGROUND,
    CONF_CRITERIA,
    CONF_FALSE,
    CONF_FALSE_MEANS,
    CONF_INCLUDE_ATTRIBUTES,
    CONF_INSTRUCTIONS,
    CONF_LEVELS_TEXT,
    CONF_OPTIONS_TEXT,
    CONF_STATE_TEMPLATE,
    CONF_TARGET,
    CONF_THRESHOLD,
    CONF_TRIGGER_ENTITIES,
    CONF_TRUE,
    CONF_TRUE_MEANS,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    MIN_UPDATE_INTERVAL_SECONDS,
    SUBENTRY_QUESTION,
    TYPE_CHOICE,
    TYPE_NOUL,
    TYPE_SCORE,
)
from .models import ContextConfig, build_question, build_question_config
from .statebuilder import async_build_state

# --- turning a text box into criteria ---


def parse_options(text: str) -> dict[str, Any]:
    """Read `option: what it means` lines into the criteria a Choice takes.

    A text box rather than a repeating row editor, because the list is usually
    three items long and a text box can be pasted into. The description after the
    colon is optional; an option on its own is a bare option with no gloss.
    """
    options: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        name, sep, description = line.partition(":")
        options[name.strip()] = (
            description.strip() if sep and description.strip() else None
        )
    return options


def option_problem(text: str) -> str | None:
    """Why this option list cannot be used, or None.

    An empty name and a repeated name both parse into a dictionary without
    complaint, and both lose an option on the way: two lines reading `a: one`
    and `a: two` arrive as one option. Silently asking a different question than
    the one on screen is worse than refusing to save.
    """
    names = [line.partition(":")[0].strip() for line in text.splitlines() if line.strip()]
    if any(not name for name in names):
        return "option_name_empty"
    if len(set(names)) != len(names):
        return "option_name_duplicate"
    return None


def parse_levels(text: str) -> list[str]:
    """Read one level per line, lowest first, which is the order Score reads."""
    return [line.strip() for line in text.splitlines() if line.strip()]


# --- the forms ---

# The form reads top to bottom in the order a question is actually thought out:
# what it is called, what it asks, the shape of the answer, then what it looks at.
# The plumbing goes in a collapsed section, because a schedule with a sensible
# default is not a decision anyone should have to make to add their first question.

_ASKS = {
    vol.Required(CONF_NAME): selector.TextSelector(),
    vol.Required(CONF_INSTRUCTIONS): selector.TextSelector(
        selector.TextSelectorConfig(multiline=True)
    ),
}

_LOOKS_AT = {
    vol.Optional(CONF_TARGET): selector.TargetSelector(),
    vol.Optional(CONF_STATE_TEMPLATE): selector.TemplateSelector(),
    vol.Optional(CONF_BACKGROUND): selector.TextSelector(
        selector.TextSelectorConfig(multiline=True)
    ),
}

_ADVANCED = vol.Schema(
    {
        vol.Optional(CONF_TRIGGER_ENTITIES): selector.EntitySelector(
            selector.EntitySelectorConfig(multiple=True)
        ),
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_SECONDS
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=MIN_UPDATE_INTERVAL_SECONDS,
                max=86400,
                unit_of_measurement="seconds",
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
        vol.Optional(CONF_INCLUDE_ATTRIBUTES, default=False): selector.BooleanSelector(),
    }
)

SECTION_ADVANCED = "advanced"


def _schema(answer_shape: dict[Any, Any]) -> vol.Schema:
    """One form: what it asks, the answer it wants, what it reads, then plumbing."""
    return vol.Schema(
        {
            **_ASKS,
            **answer_shape,
            **_LOOKS_AT,
            vol.Required(SECTION_ADVANCED): section(
                _ADVANCED, SectionConfig(collapsed=True)
            ),
        }
    )


SCHEMAS: dict[str, vol.Schema] = {
    TYPE_NOUL: _schema(
        {
            vol.Optional(CONF_TRUE_MEANS): selector.TextSelector(),
            vol.Optional(CONF_FALSE_MEANS): selector.TextSelector(),
            vol.Optional(CONF_THRESHOLD): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=1, step=0.01, mode=selector.NumberSelectorMode.BOX
                )
            ),
        }
    ),
    TYPE_CHOICE: _schema(
        {
            vol.Required(CONF_OPTIONS_TEXT): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
        }
    ),
    TYPE_SCORE: _schema(
        {
            vol.Required(CONF_LEVELS_TEXT): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
        }
    ),
}


def flatten(user_input: dict[str, Any]) -> dict[str, Any]:
    """Lift the collapsed section back up.

    A section arrives nested under its own key. Storing it that way would put the
    form's layout into the saved data, so every reader downstream would have to
    know which fields happened to be collapsed on the day it was added.
    """
    merged = {k: v for k, v in user_input.items() if k != SECTION_ADVANCED}
    merged.update(user_input.get(SECTION_ADVANCED) or {})
    return merged


_ADVANCED_KEYS = (CONF_TRIGGER_ENTITIES, CONF_SCAN_INTERVAL, CONF_INCLUDE_ATTRIBUTES)


def nest(data: dict[str, Any]) -> dict[str, Any]:
    """The inverse, for filling the form in again when editing."""
    return {
        **{k: v for k, v in data.items() if k not in _ADVANCED_KEYS},
        SECTION_ADVANCED: {k: data[k] for k in _ADVANCED_KEYS if k in data},
    }


# A state longer than this is summarised instead of shown. The point of the
# preview is to catch a state that does not say what you assumed, and nobody
# reads 250 entity records looking for that.
PREVIEW_CHARS = 1800


async def build_preview(hass: HomeAssistant, data: dict[str, Any]) -> tuple[str, Any]:
    """Exactly what this question will send, rendered now.

    The main way a question disappoints is that the state did not say what its
    author assumed. Today you find that out by turning on debug logging and
    reading the next evaluation. Here it is on screen before the question exists.

    Errors are shown rather than raised, because a target holding 300 entities or
    a template with a typo is precisely what this screen is for.
    """
    template_text: str | None = None
    raw = data.get(CONF_STATE_TEMPLATE)
    if raw:
        try:
            template_text = Template(str(raw), hass).async_render(parse_result=False)
        except TemplateError as err:
            say = await _translator(hass)
            return say("preview_template_error", reason=str(err)), None
    try:
        state = async_build_state(
            hass,
            template_text,
            data.get(CONF_TARGET) or None,
            bool(data.get(CONF_INCLUDE_ATTRIBUTES)),
        )
    except (ServiceValidationError, HomeAssistantError) as err:
        return await _readable(hass, err), None

    shown = state if isinstance(state, str) else json.dumps(state, indent=2, default=str)
    if len(shown) <= PREVIEW_CHARS:
        return shown, state
    entities = (
        len(state["entities"]) if isinstance(state, dict) and "entities" in state else 0
    )
    return (
        f"{shown[:PREVIEW_CHARS]}\n\n... {len(shown) - PREVIEW_CHARS} more characters"
        f"{f', {entities} entities in total' if entities else ''}.",
        state,
    )


async def _readable(hass: HomeAssistant, err: Exception) -> str:
    """The error as a sentence rather than as a key.

    str() on one of these resolves the key too, but through a cache this does not
    control, and an uncached lookup returns the bare key. "too_many_entities" on
    screen is worse than the sentence it stands for, so the catalogue is read
    directly and str() is only the fallback.
    """
    key = getattr(err, "translation_key", None)
    if key:
        strings = await translation.async_get_translations(
            hass, hass.config.language, "exceptions", [DOMAIN]
        )
        message = strings.get(f"component.{DOMAIN}.exceptions.{key}.message")
        if message:
            placeholders = getattr(err, "translation_placeholders", None) or {}
            try:
                return message.format(**placeholders)
            except (KeyError, IndexError):
                return message
    return str(err)


# Shown when a translation is missing, so a missing key is still a sentence
# rather than a blank line. A test keeps this in step with strings.json.
_PREVIEW_FALLBACK = {
    "preview_alone": "Sent as its own request.",
    "preview_grouped": "Sent in one request together with: {others}.",
    "preview_cost": (
        "Asked once for this preview: {tokens} input tokens, about ${cost}, {ms} ms."
    ),
    "preview_threshold_over": (
        "That is above your threshold of {threshold}, so the binary "
        "sensor would be **on** right now."
    ),
    "preview_threshold_under": (
        "That is below your threshold of {threshold}, so the binary "
        "sensor would be **off** right now."
    ),
    "preview_winner": "Winner **{choice}**, confidence {confidence}.",
    "preview_score": (
        "Score **{score}**, nearest level **{level}**, confidence {confidence}."
    ),
    "preview_undrawable": "The answer came back in a shape this version cannot draw.",
    "preview_unbuildable": "That question cannot be built yet: {reason}",
    "preview_rejected": "TypeSafe rejected the API key, so there is no trial answer.",
    "preview_failed": "No trial answer: {reason}",
    "preview_mismatched": "The API answered, but not to the question that was asked.",
    "preview_template_error": "The template does not render: {reason}",
    "preview_over_budget": (
        "The daily token budget is spent, so there is no trial answer. "
        "The question still saves."
    ),
    "preview_nothing_yet": "No trial answer: there is nothing to ask about yet.",
}


async def _translator(hass: HomeAssistant) -> Callable[..., str]:
    """Load this integration's sentences once, then format them by key.

    Everything the preview puts on screen goes through here. _PREVIEW_FALLBACK is
    the last resort, so a missing key is still a sentence rather than a blank
    line, and a test keeps the two in step.
    """
    strings = await translation.async_get_translations(
        hass, hass.config.language, "common", [DOMAIN]
    )

    def say(key: str, **placeholders: str) -> str:
        template = strings.get(
            f"component.{DOMAIN}.common.{key}", _PREVIEW_FALLBACK.get(key, key)
        )
        try:
            return template.format(**placeholders)
        except (KeyError, IndexError):
            return template

    return say


BAR_WIDTH = 18


def _bar(fraction: float) -> str:
    """A probability as something readable at a glance.

    Numbers in a column are hard to rank by eye. A bar next to them is not, and a
    distribution is exactly the thing a user needs to rank rather than read.
    """
    filled = max(0, min(BAR_WIDTH, round(fraction * BAR_WIDTH)))
    return "\u2588" * filled + "\u2591" * (BAR_WIDTH - filled)


def render_answer(
    answer: Answer, threshold: float | None, say: Callable[..., str]
) -> str:
    """The trial answer, drawn rather than dumped.

    `say` resolves a key against the loaded catalogue. Everything here is a
    sentence someone reads, so none of it can be a literal.
    """
    if isinstance(answer, NoulAnswer):
        lines = [f"`{_bar(answer.noul)}`  **{answer.noul:.2f}**"]
        if threshold is not None:
            over = answer.noul >= threshold
            key = "preview_threshold_over" if over else "preview_threshold_under"
            lines.append("\n" + say(key, threshold=f"{threshold:g}"))
        return "\n".join(lines)

    if isinstance(answer, ChoiceAnswer):
        rows = sorted(answer.probabilities.items(), key=lambda kv: -kv[1])
        drawn = "\n".join(
            f"`{_bar(p)}` {p:.2f}  "
            f"{'**' + name + '**' if name == answer.choice else name}"
            for name, p in rows
        )
        return (
            drawn
            + "\n\n"
            + say(
                "preview_winner",
                choice=answer.choice,
                confidence=f"{answer.confidence:.2f}",
            )
        )

    if isinstance(answer, ScoreAnswer):
        rows = sorted(answer.probabilities.items(), key=lambda kv: kv[0])
        drawn = "\n".join(
            f"`{_bar(p)}` {p:.2f}  {answer.legend.get(level, level)}" for level, p in rows
        )
        return (
            drawn
            + "\n\n"
            + say(
                "preview_score",
                score=f"{answer.score:.2f}",
                level=str(answer.nearest_level),
                confidence=f"{answer.confidence:.2f}",
            )
        )
    return say("preview_undrawable")


async def try_answer(
    hass: HomeAssistant, entry: ConfigEntry, data: dict[str, Any], state: Any
) -> str:
    """Ask the question once, now, so the form can show what it answers.

    A state preview says what the model will read. It does not say whether the
    question works, and a question that reads a perfect state and still answers
    0.5 is the common disappointment. One call costs a few hundred input tokens,
    so the answer is worth more than the fraction of a cent it costs.
    """
    say = await _translator(hass)
    usage = entry.runtime_data.usage
    usage.roll_over(dt_util.now().date())
    # The budget is a tripwire, and a preview that spends past it is a hole in
    # the fence. The form still saves; it just does not get a trial answer.
    if usage.would_exceed():
        return say("preview_over_budget")
    try:
        question = build_question(_as_raw_question(data))
    except (KeyError, ValueError) as err:
        return say("preview_unbuildable", reason=str(err))
    try:
        response = await entry.runtime_data.client.ask(state, {"preview": question})
    except JevAuthError:
        return say("preview_rejected")
    except JevError as err:
        return say("preview_failed", reason=str(err))

    usage.record(response.usage.input_tokens)
    usage.notify()

    answer = response.answers.get("preview")
    if answer is None:
        return say("preview_mismatched")
    drawn = render_answer(answer, data.get(CONF_THRESHOLD), say)
    cost = response.usage.input_tokens / 1_000_000 * usage.price_per_million
    footer = say(
        "preview_cost",
        tokens=str(response.usage.input_tokens),
        cost=f"{cost:.6f}",
        ms=f"{response.latency_ms:.0f}",
    )
    return f"{drawn}\n\n_{footer}_"


async def describe_grouping(
    hass: HomeAssistant,
    entry: ConfigEntry,
    data: dict[str, Any],
    editing: str | None,
) -> str:
    """Which other questions this one will share its request with.

    The grouping is derived rather than declared, which is right and also
    invisible. Saying it out loud here is what makes it something a user can
    reason about instead of a surprise on the bill.
    """
    key = _call_key(data)
    others = [
        s.title
        for s in entry.subentries.values()
        if s.subentry_type == SUBENTRY_QUESTION
        and s.subentry_id != editing
        and _call_key(dict(s.data)) == key
    ]
    say = await _translator(hass)
    if not others:
        return say("preview_alone")
    return say("preview_grouped", others=", ".join(sorted(others)))


class JevQuestionSubentryFlow(ConfigSubentryFlow):
    """Add or edit one question without touching a file."""

    _pending: dict[str, Any]
    _editing: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Pick what kind of answer you want back."""
        return self.async_show_menu(
            step_id="user", menu_options=[TYPE_NOUL, TYPE_CHOICE, TYPE_SCORE]
        )

    async def async_step_noul(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        return await self._async_type_step(TYPE_NOUL, user_input)

    async def async_step_choice(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        return await self._async_type_step(TYPE_CHOICE, user_input)

    async def async_step_score(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        return await self._async_type_step(TYPE_SCORE, user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Edit an existing question, on the form for the type it already is."""
        current = self._get_reconfigure_subentry()
        return await self._async_question_form(
            "reconfigure",
            current.data["type"],
            user_input,
            editing=current.subentry_id,
            suggested=dict(current.data),
        )

    async def _async_type_step(
        self, kind: str, user_input: dict[str, Any] | None
    ) -> SubentryFlowResult:
        return await self._async_question_form(kind, kind, user_input)

    async def _async_question_form(
        self,
        step_id: str,
        kind: str,
        user_input: dict[str, Any] | None,
        *,
        editing: str | None = None,
        suggested: dict[str, Any] | None = None,
    ) -> SubentryFlowResult:
        """Show the form for one kind of question, check it, then go to the preview."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = flatten(user_input)
            errors = _validate(kind, user_input)
            if not errors:
                self._pending = {**user_input, "type": kind}
                self._editing = editing
                return await self.async_step_preview()
            suggested = user_input
        schema = SCHEMAS[kind]
        if suggested is not None:
            schema = self.add_suggested_values_to_schema(schema, nest(suggested))
        return self.async_show_form(
            step_id=step_id, data_schema=schema, errors=errors or None
        )

    async def async_step_preview(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Show the state this question will send, then save it."""
        if user_input is None:
            entry = self._get_entry()
            shown, state = await build_preview(self.hass, self._pending)
            answer = (
                await try_answer(self.hass, entry, self._pending, state)
                if state is not None
                else (await _translator(self.hass))("preview_nothing_yet")
            )
            return self.async_show_form(
                step_id="preview",
                data_schema=vol.Schema({}),
                description_placeholders={
                    "state": shown,
                    "grouping": await describe_grouping(
                        self.hass, entry, self._pending, self._editing
                    ),
                    "answer": answer,
                },
            )
        title = self._pending[CONF_NAME]
        if self._editing is None:
            return self.async_create_entry(title=title, data=self._pending)
        current = self._get_reconfigure_subentry()
        return self.async_update_and_abort(
            self._get_entry(), current, data=self._pending, title=title
        )


def _validate(kind: str, user_input: dict[str, Any]) -> dict[str, str]:
    """Catch what a selector cannot, with the message naming the field.

    The limits are the library's own, and an error that names the limit and the
    ask is the one an automation author can act on.
    """
    errors: dict[str, str] = {}
    # The target picker submits {"entity_id": []} once something was picked and
    # removed again. That is as empty as no target at all.
    target = user_input.get(CONF_TARGET) or {}
    if not any(target.values()) and not user_input.get(CONF_STATE_TEMPLATE):
        errors["base"] = "nothing_to_judge"
    if kind == TYPE_CHOICE:
        text = user_input.get(CONF_OPTIONS_TEXT, "")
        if problem := option_problem(text):
            errors[CONF_OPTIONS_TEXT] = problem
        elif not 2 <= len(parse_options(text)) <= 255:
            errors[CONF_OPTIONS_TEXT] = "choice_options_out_of_range"
    if kind == TYPE_SCORE:
        levels = parse_levels(user_input.get(CONF_LEVELS_TEXT, ""))
        if not 2 <= len(levels) <= 10:
            errors[CONF_LEVELS_TEXT] = "score_levels_out_of_range"
    return errors


# --- turning subentries into the contexts the coordinator already runs ---


def _as_raw_question(data: dict[str, Any]) -> dict[str, Any]:
    """The subentry's fields in the shape build_question_config already reads."""
    raw: dict[str, Any] = {
        CONF_NAME: data[CONF_NAME],
        "type": data["type"],
        CONF_INSTRUCTIONS: data[CONF_INSTRUCTIONS],
    }
    for optional in (CONF_BACKGROUND, CONF_THRESHOLD):
        if data.get(optional) not in (None, ""):
            raw[optional] = data[optional]
    # The form calls these true_means and false_means. build_question reads true
    # and false, which is what the YAML surface has always used. Without this
    # mapping the two fields were collected, stored, and then dropped before the
    # payload was built, so filling them in did nothing at all.
    for form_field, api_field in (
        (CONF_TRUE_MEANS, CONF_TRUE),
        (CONF_FALSE_MEANS, CONF_FALSE),
    ):
        if data.get(form_field) not in (None, ""):
            raw[api_field] = data[form_field]
    if data["type"] == TYPE_CHOICE:
        raw[CONF_CRITERIA] = parse_options(data[CONF_OPTIONS_TEXT])
    elif data["type"] == TYPE_SCORE:
        raw[CONF_CRITERIA] = parse_levels(data[CONF_LEVELS_TEXT])
    return raw


def _question_key(subentry: Any) -> str:
    """The stable key behind one question's entities.

    The subentry id and nothing else. It was the id plus the slugified title,
    which read nicely and moved when the title did: renaming a question changed
    its key, which changed its unique_id, which orphaned the entity and threw
    away its history. A key is an identity, not a label.
    """
    return f"ui_{subentry.subentry_id.lower()}"


def _canonical_target(target: Any) -> Any:
    """A target in a fixed order, so two identical ones compare equal.

    The picker returns lists, and two questions aimed at the same entities in a
    different order produced different keys and so two API calls where one would
    have done.
    """
    if not isinstance(target, dict):
        return target or {}
    return {
        key: sorted(value) if isinstance(value, list) else value
        for key, value in sorted(target.items())
    }


def _call_key(data: dict[str, Any]) -> str:
    """What decides whether two questions can share a request.

    Same readings, same note, same schedule. Anything else has to be its own call,
    because the API takes one state per request.
    """
    return json.dumps(
        [
            _canonical_target(data.get(CONF_TARGET)),
            data.get(CONF_STATE_TEMPLATE) or "",
            bool(data.get(CONF_INCLUDE_ATTRIBUTES)),
            sorted(data.get(CONF_TRIGGER_ENTITIES) or []),
            int(data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS)),
        ],
        sort_keys=True,
    )


def async_contexts_from_subentries(
    hass: HomeAssistant, entry: ConfigEntry
) -> list[ContextConfig]:
    """Group the configured questions into as few API calls as they allow."""
    grouped: dict[str, list[Any]] = {}
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_QUESTION:
            continue
        grouped.setdefault(_call_key(dict(subentry.data)), []).append(subentry)

    contexts: list[ContextConfig] = []
    for index, (call_key, subentries) in enumerate(sorted(grouped.items())):
        first = dict(subentries[0].data)
        raw_template = first.get(CONF_STATE_TEMPLATE)
        template = Template(raw_template, hass) if raw_template else None
        # Named for the questions in it rather than by a number, so a log line and
        # the latency sensor both say something a reader recognises.
        name = subentries[0].title if len(subentries) == 1 else f"Group {index + 1}"
        contexts.append(
            ContextConfig(
                # The latency and payload unique ids are built from this. The
                # name and the index both move when another question is added,
                # which orphaned those entities, so the key is the call key itself.
                key="ui_" + sha256(call_key.encode()).hexdigest()[:12],
                name=name,
                template=template,
                selector=first.get(CONF_TARGET) or None,
                include_attributes=bool(first.get(CONF_INCLUDE_ATTRIBUTES)),
                questions=[
                    build_question_config(
                        _as_raw_question(dict(s.data)),
                        _question_key(s),
                    )
                    for s in subentries
                ],
                scan_interval=int(
                    first.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS)
                ),
                trigger_entities=list(first.get(CONF_TRIGGER_ENTITIES) or []),
            )
        )
    return contexts
