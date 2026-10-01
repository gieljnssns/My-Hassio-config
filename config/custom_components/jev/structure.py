"""Turn an AI Task structure into Jev questions, and the answers back into values.

Home Assistant builds `task.structure` out of selector instances: ai_task reads the
`selector:` block of every field and calls `selector.selector(...)` on it, so what
arrives here is a BooleanSelector or a SelectSelector, not a type name. The mapping
therefore reads selector classes. Going through voluptuous_openapi to get a JSON
schema first would mean a new requirement to say the same thing.

Three selectors map onto the three question types and nothing else does. A field
this module cannot map is refused before the request, so a badly shaped task costs
nothing.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import selector
from jevclient import (
    MAX_CHOICE_OPTIONS,
    MAX_SCORE_LEVELS,
    MIN_CHOICE_OPTIONS,
    MIN_SCORE_LEVELS,
    Answer,
    Choice,
    ChoiceAnswer,
    Noul,
    NoulAnswer,
    Question,
    Score,
    ScoreAnswer,
)

from .const import DOMAIN

# Where a boolean field lands. A noul is a probability, and half is the only
# division that does not favour one answer. A question that needs another line is a
# question subentry, which carries a threshold of its own.
BOOLEAN_THRESHOLD = 0.5

# The result carries the confidence behind every field under this key, because
# GenDataTaskResult has nowhere else to put it. A field of the same name would be
# overwritten, so it is refused instead.
RESERVED_KEY = "jev"


def questions_from_structure(structure: vol.Schema) -> dict[str, Question]:
    """One question per field, in the order the task declared them."""
    questions: dict[str, Question] = {}
    for marker, value in structure.schema.items():
        key = _key(marker)
        if key == RESERVED_KEY:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="reserved_field",
                translation_placeholders={"field": RESERVED_KEY},
            )
        questions[key] = _question(key, _description(marker, key), value)
    if not questions:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="no_fields"
        )
    return questions


def values_from_answers(
    structure: vol.Schema, answers: dict[str, Answer]
) -> dict[str, Any]:
    """The answers as the values the structure asked for.

    A missing field is an error rather than a None. The caller asked for a value
    and templating one that is not there reads as an empty string.
    """
    values: dict[str, Any] = {}
    for marker, selector_instance in structure.schema.items():
        key = _key(marker)
        if key not in answers:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="answer_missing",
                translation_placeholders={"field": key},
            )
        values[key] = _value(key, selector_instance, answers[key])
    return values


def _key(marker: Any) -> str:
    """The field name out of a voluptuous marker, or out of a bare string key."""
    return str(marker.schema if isinstance(marker, vol.Marker) else marker)


def _description(marker: Any, key: str) -> str:
    """What to ask about this field.

    ai_task puts the field's `description:` on the marker. A field without one asks
    about its own name, which is worth something when the name is `window_open` and
    worth nothing when it is `value`.
    """
    description = getattr(marker, "description", None)
    return str(description) if description else key


def _question(key: str, description: str, instance: Any) -> Question:
    if isinstance(instance, selector.BooleanSelector):
        return Noul(instructions=description)
    if isinstance(instance, selector.SelectSelector):
        options = _options(key, instance)
        return Choice(instructions=description, criteria=dict.fromkeys(options))
    if isinstance(instance, selector.NumberSelector):
        return Score(instructions=description, criteria=_levels(key, instance))
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="unsupported_field",
        translation_placeholders={"field": key, "selector": type(instance).__name__},
    )


def _options(key: str, instance: selector.SelectSelector) -> list[str]:
    """The values of a select, which are what an answer comes back as.

    A select is configured either as plain strings or as value and label pairs. The
    model is shown the value in both cases, because the value is what the caller
    reads out of the result.
    """
    # Without duplicates, which count toward the minimum and are one answer.
    options: list[str] = list(
        dict.fromkeys(
            option if isinstance(option, str) else str(option["value"])
            for option in instance.config["options"]
        )
    )
    if not MIN_CHOICE_OPTIONS <= len(options) <= MAX_CHOICE_OPTIONS:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="field_options_out_of_range",
            translation_placeholders={
                "field": key,
                "count": str(len(options)),
                "min": str(MIN_CHOICE_OPTIONS),
                "max": str(MAX_CHOICE_OPTIONS),
            },
        )
    return options


def _scale(key: str, instance: selector.NumberSelector) -> tuple[float, float, float]:
    """The bottom, the top and the step of a number field.

    A number with no top is a number Jev cannot rate: a scale needs both ends. The
    box selector leaves min and max out by default, so this is the common refusal
    and it names the two fields to add.
    """
    config = instance.config
    low, high = config.get("min"), config.get("max")
    if low is None or high is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="field_needs_scale",
            translation_placeholders={
                "field": key,
                "bound": "min" if low is None else "max",
            },
        )
    if high <= low:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="field_scale_not_ordered",
            # The selector stores both ends as floats, so 10 would print as 10.0,
            # which is not what the user wrote.
            translation_placeholders={
                "field": key,
                "min": f"{low:g}",
                "max": f"{high:g}",
            },
        )
    step = config.get("step")
    # "any" means the caller wants a continuous number, so the scale gets as many
    # levels as Jev allows and the answer is mapped back without snapping.
    return float(low), float(high), 0.0 if step in (None, "any") else float(step)


def _levels(key: str, instance: selector.NumberSelector) -> list[str]:
    """The rungs of the scale, labelled with the numbers they stand for.

    Jev rates against described levels, and a bare number is a thin description. The
    field's own description carries the meaning, which is why a number field is the
    one most worth writing a sentence for.

    Every label is put through the same mapping the answer takes, so the rung the
    model picked and the number the caller reads are the same text. They are both
    visible: the value lands in the field and the label lands in
    `jev.answers.<field>.nearest_level`, and a legend saying 1.11 beside a value of
    1 reads as a bug.
    """
    low, high, step = _scale(key, instance)
    unit = instance.config.get("unit_of_measurement") or ""
    count = MAX_SCORE_LEVELS if step == 0 else round((high - low) / step) + 1
    count = max(MIN_SCORE_LEVELS, min(count, MAX_SCORE_LEVELS))
    return [
        f"{_on_scale(low, high, step, index / (count - 1))}{unit}".strip()
        for index in range(count)
    ]


def _value(key: str, instance: Any, answer: Answer) -> Any:
    if isinstance(instance, selector.BooleanSelector) and isinstance(answer, NoulAnswer):
        return answer.noul >= BOOLEAN_THRESHOLD
    if isinstance(instance, selector.SelectSelector) and isinstance(answer, ChoiceAnswer):
        return answer.choice
    if isinstance(instance, selector.NumberSelector) and isinstance(answer, ScoreAnswer):
        return _number(instance, answer)
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="answer_does_not_fit",
        translation_placeholders={
            "field": key,
            "answer": type(answer).__name__,
            "selector": type(instance).__name__,
        },
    )


def _number(instance: selector.NumberSelector, answer: ScoreAnswer) -> float | int:
    """The score put back on the caller's scale.

    `normalized` divides by the top level, so the number of levels the scale was
    cut into does not leak into the answer.
    """
    low, high, step = _scale("", instance)
    return _on_scale(low, high, step, answer.normalized)


def _on_scale(low: float, high: float, step: float, fraction: float) -> float | int:
    """A fraction of the way up the scale, as a number the field would accept.

    A step is a promise that the field only takes multiples of it, so the value is
    snapped to one. A scale cut into fewer rungs than the step allows, 0 to 100 by 1
    for instance, then lands on ten of the hundred and one legal values rather than
    on something the field would reject.
    """
    value = low + fraction * (high - low)
    if step:
        value = low + round((value - low) / step) * step
    value = min(max(value, low), high)
    return int(value) if float(value).is_integer() else round(value, 4)
