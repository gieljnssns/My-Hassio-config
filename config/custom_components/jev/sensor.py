"""Sensors: one per question, plus the usage receipts for the config entry."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util
from jevclient import ChoiceAnswer, NoulAnswer, ScoreAnswer

from .const import (
    ATTR_CONFIDENCE,
    ATTR_LEGEND,
    ATTR_NEAREST_LEVEL,
    ATTR_PROBABILITIES,
    ATTR_QUESTIONS,
    ATTR_STATE_TEXT,
    TYPE_CHOICE,
    TYPE_NOUL,
    TYPE_SCORE,
)
from .coordinator import JevCoordinator, JevRuntimeData
from .entity import JevQuestionEntity, JevUsageEntity, async_remove_stale_entities
from .models import QuestionConfig

# Every sensor reads an answer a coordinator already fetched, so there is
# nothing to serialise: no sensor performs I/O of its own.
PARALLEL_UPDATES = 0

if TYPE_CHECKING:
    from . import JevConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JevConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    entities: list[Any] = []
    for coordinator in runtime.coordinators.values():
        for question in coordinator.context_config.questions:
            entities.append(JevQuestionSensor(coordinator, entry.entry_id, question))
        entities.append(JevLatencySensor(coordinator, entry.entry_id))
        entities.append(JevPayloadSensor(coordinator, entry.entry_id))
    entities.extend(
        [
            JevCallsSensor(entry.entry_id, runtime),
            JevInputTokensSensor(entry.entry_id, runtime),
            JevCostSensor(entry.entry_id, runtime),
        ]
    )
    async_remove_stale_entities(hass, entry.entry_id, SENSOR_DOMAIN, entities)
    async_add_entities(entities)


class JevQuestionSensor(JevQuestionEntity, SensorEntity):
    """The answer to one question.

    A noul reads as the probability of yes, a score as a probability-weighted level
    which can land between two levels, and a choice as the winning option.
    """

    def __init__(
        self, coordinator: JevCoordinator, entry_id: str, question: QuestionConfig
    ) -> None:
        super().__init__(coordinator, entry_id, question.key)
        self._question = question
        self._attr_name = question.name
        self._attr_unique_id = f"{entry_id}_{question.key}"
        if question.kind == TYPE_CHOICE:
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = question.options
        else:
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_suggested_display_precision = 2

    @property
    def native_value(self) -> float | str | None:
        answer = (self.coordinator.data or {}).get(self._question_key)
        if answer is None:
            return None
        if isinstance(answer, NoulAnswer):
            return round(answer.noul, 3)
        if isinstance(answer, ChoiceAnswer):
            return answer.choice
        if isinstance(answer, ScoreAnswer):
            return round(answer.score, 3)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        answer = (self.coordinator.data or {}).get(self._question_key)
        if answer is None:
            return None
        if isinstance(answer, NoulAnswer):
            # A noul carries no confidence: the probability is the whole answer.
            return {"question_type": TYPE_NOUL}
        if isinstance(answer, ChoiceAnswer):
            return {
                "question_type": TYPE_CHOICE,
                ATTR_CONFIDENCE: round(answer.confidence, 3),
                ATTR_PROBABILITIES: {
                    k: round(v, 4) for k, v in answer.probabilities.items()
                },
            }
        if isinstance(answer, ScoreAnswer):
            return {
                "question_type": TYPE_SCORE,
                ATTR_CONFIDENCE: round(answer.confidence, 3),
                ATTR_PROBABILITIES: {
                    k: round(v, 4) for k, v in answer.probabilities.items()
                },
                ATTR_LEGEND: answer.legend,
                ATTR_NEAREST_LEVEL: answer.nearest_level,
            }
        return None


class _JevContextSensor(JevQuestionEntity, SensorEntity):
    """A diagnostic sensor about one context as a whole, not one of its questions."""

    _suffix: str

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    # Off by default. The payload sensor's attributes carry the whole request, and
    # a 150 entity target renders about 17 kB of state, which every open dashboard
    # would then be pushed on every evaluation. Somebody auditing a context turns
    # these on; nobody else pays for them.
    _attr_entity_registry_enabled_default = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: JevCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, question_key="")
        # The context name is the user's own word, so it travels as a placeholder
        # rather than being baked into an untranslatable string.
        self._attr_translation_key = f"context_{self._suffix}"
        self._attr_translation_placeholders = {"context": coordinator.context_config.name}
        self._attr_unique_id = (
            f"{entry_id}_{coordinator.context_config.key}_{self._suffix}"
        )

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success


class JevLatencySensor(_JevContextSensor):
    """How long the last evaluation of this context took."""

    _suffix = "latency"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS

    @property
    def native_value(self) -> float | None:
        if self.coordinator.last_latency_ms is None:
            return None
        return round(self.coordinator.last_latency_ms)


class JevPayloadSensor(_JevContextSensor):
    """What this context last sent, and how big it was.

    The rendered state was only in the diagnostics download until now, which means
    reading it took a file and a text editor. Here it is one attribute, which is
    what somebody wants when an answer surprises them or when they are deciding
    whether a target is sending more of the house than they meant to.

    The size is the state because a state is capped at 255 characters and the text
    is not. The size is also the number worth a graph: it is what the request costs,
    up to the endpoint's tokeniser.
    """

    # The recorder would otherwise write a copy of the house state on every
    # evaluation. A context running every 300 seconds is 288 copies a day, of the
    # exact text this integration exists to keep an eye on.
    _unrecorded_attributes = frozenset({ATTR_STATE_TEXT, ATTR_QUESTIONS})

    _suffix = "payload"
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = UnitOfInformation.BYTES

    @property
    def native_value(self) -> int | None:
        return self.coordinator.last_payload_bytes

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """The last request that was answered.

        A failed evaluation leaves the previous one standing, because the
        coordinator only assigns these after a reply arrives. That is the right
        behaviour here: the last thing actually sent is what somebody is looking
        for, not the thing that never went.
        """
        return {
            ATTR_STATE_TEXT: self.coordinator.last_state_text,
            ATTR_QUESTIONS: {
                question.key: question.question.as_payload()
                for question in self.coordinator.context_config.questions
            },
        }


class JevCallsSensor(JevUsageEntity, SensorEntity):
    """Calls made today. Resets at midnight, local time."""

    _attr_translation_key = "calls_today"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, entry_id: str, runtime: JevRuntimeData) -> None:
        super().__init__(entry_id, runtime)
        self._attr_unique_id = f"{entry_id}_calls_today"

    @property
    def native_value(self) -> int:
        return self._runtime.usage.calls


class JevInputTokensSensor(JevUsageEntity, SensorEntity):
    """Input tokens today, as reported by the API rather than estimated.

    Question text is billed as input, so this rises with the number of questions
    per context, not only with the size of the state.
    """

    _attr_translation_key = "input_tokens_today"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "tokens"

    def __init__(self, entry_id: str, runtime: JevRuntimeData) -> None:
        super().__init__(entry_id, runtime)
        self._attr_unique_id = f"{entry_id}_input_tokens_today"

    @property
    def native_value(self) -> int:
        return self._runtime.usage.input_tokens

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        usage = self._runtime.usage
        return {"daily_token_budget": usage.budget or None}


class JevCostSensor(JevUsageEntity, SensorEntity):
    """Estimated spend today.

    The token count is measured; the money is an estimate, because the price per
    million is a setting and TypeSafe can change theirs.
    """

    _attr_translation_key = "estimated_cost_today"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.MONETARY
    # Monetary allows total only. A price change moves today's figure both ways,
    # so it is not total_increasing either. last_reset tells statistics where
    # each day starts.
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "USD"
    _attr_suggested_display_precision = 4

    def __init__(self, entry_id: str, runtime: JevRuntimeData) -> None:
        super().__init__(entry_id, runtime)
        self._attr_unique_id = f"{entry_id}_estimated_cost_today"

    @property
    def native_value(self) -> float:
        return round(self._runtime.usage.estimated_cost, 6)

    @property
    def last_reset(self) -> datetime:
        return dt_util.start_of_local_day(self._runtime.usage.day)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"price_per_million_input_tokens": self._runtime.usage.price_per_million}
