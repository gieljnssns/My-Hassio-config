"""Binary sensors: a noul above its threshold, and the budget tripwire."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from jevclient import NoulAnswer

from .const import CONF_THRESHOLD
from .coordinator import JevCoordinator, JevRuntimeData
from .entity import JevQuestionEntity, JevUsageEntity, async_remove_stale_entities
from .models import QuestionConfig

# Same as the sensor platform: these read answers a coordinator already
# fetched and perform no I/O of their own.
PARALLEL_UPDATES = 0

if TYPE_CHECKING:
    from . import JevConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JevConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    entities: list[Any] = [JevBudgetSensor(entry.entry_id, runtime)]
    for coordinator in runtime.coordinators.values():
        entities.extend(
            JevThresholdSensor(coordinator, entry.entry_id, question)
            for question in coordinator.context_config.questions
            if question.wants_binary_sensor
        )
    async_remove_stale_entities(hass, entry.entry_id, BINARY_SENSOR_DOMAIN, entities)
    async_add_entities(entities)


def threshold_unique_id(entry_id: str, question: QuestionConfig) -> str:
    return f"{entry_id}_{question.key}_threshold"


class JevThresholdSensor(JevQuestionEntity, BinarySensorEntity):
    """A noul compared against the threshold configured for it.

    The probability stays on the matching sensor. This exists so an automation can
    trigger on a state change instead of re-deciding the threshold in a template.
    """

    def __init__(
        self, coordinator: JevCoordinator, entry_id: str, question: QuestionConfig
    ) -> None:
        super().__init__(coordinator, entry_id, question.key)
        # `or 0.5` rewrote a configured 0 into 0.5, because 0 is falsy. The picker
        # allows 0, wants_binary_sensor accepts it, and the config-flow preview
        # reported "above your threshold of 0" while the entity it created
        # reported off. Only a missing threshold takes the default.
        self._threshold = 0.5 if question.threshold is None else question.threshold
        self._attr_name = question.name
        self._attr_unique_id = threshold_unique_id(entry_id, question)

    @property
    def is_on(self) -> bool | None:
        answer = (self.coordinator.data or {}).get(self._question_key)
        if not isinstance(answer, NoulAnswer):
            return None
        return answer.noul >= self._threshold

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        answer = (self.coordinator.data or {}).get(self._question_key)
        if not isinstance(answer, NoulAnswer):
            return None
        return {"probability": round(answer.noul, 3), CONF_THRESHOLD: self._threshold}


class JevBudgetSensor(JevUsageEntity, BinarySensorEntity):
    """On when the daily token budget has stopped evaluations."""

    _attr_translation_key = "daily_budget_exceeded"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, entry_id: str, runtime: JevRuntimeData) -> None:
        super().__init__(entry_id, runtime)
        self._attr_unique_id = f"{entry_id}_budget_exceeded"

    @property
    def is_on(self) -> bool:
        return self._runtime.usage.budget_exceeded

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        usage = self._runtime.usage
        return {
            "daily_token_budget": usage.budget or None,
            "input_tokens_today": usage.input_tokens,
        }
