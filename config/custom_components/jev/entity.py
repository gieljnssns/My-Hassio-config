"""Shared entity base.

Every platform builds its DeviceInfo here and nowhere else. Two platforms each
inventing their own for the same device makes the registry entry flip-flop with
load order.
"""

from __future__ import annotations

from collections.abc import Iterable

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JevCoordinator, JevRuntimeData


def build_device_info(entry_id: str, runtime: JevRuntimeData) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        entry_type=DeviceEntryType.SERVICE,
        manufacturer="TypeSafe",
        name="Jev",
        model="System One",
        sw_version=runtime.model_version,
        configuration_url="https://docs.typesafe.ai/introduction",
    )


@callback
def async_remove_stale_entities(
    hass: HomeAssistant, entry_id: str, domain: str, entities: Iterable[Entity]
) -> None:
    """Remove what this entry once provided on one platform and no longer does.

    A question deleted in the form, a threshold cleared or a YAML question taken
    out otherwise leaves its entity in the registry, restored and unavailable,
    until somebody deletes it by hand.
    """
    current = {entity.unique_id for entity in entities}
    registry = er.async_get(hass)
    for registered in er.async_entries_for_config_entry(registry, entry_id):
        if registered.domain == domain and registered.unique_id not in current:
            registry.async_remove(registered.entity_id)


class JevQuestionEntity(CoordinatorEntity[JevCoordinator]):
    """An entity backed by one question inside one context."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: JevCoordinator, entry_id: str, question_key: str
    ) -> None:
        super().__init__(coordinator)
        self._question_key = question_key
        self._attr_device_info = build_device_info(entry_id, coordinator.runtime)

    @property
    def available(self) -> bool:
        """Unavailable until an answer to this exact question has arrived.

        A missing answer is missing data, not a value, so nothing is invented here.
        """
        return (
            super().available
            and self.coordinator.data is not None
            and self._question_key in self.coordinator.data
        )


class JevUsageEntity(Entity):
    """An entity reading the config entry's usage account rather than a coordinator."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry_id: str, runtime: JevRuntimeData) -> None:
        self._runtime = runtime
        self._attr_device_info = build_device_info(entry_id, runtime)

    async def async_added_to_hass(self) -> None:
        self._runtime.usage.listeners.append(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        if self.async_write_ha_state in self._runtime.usage.listeners:
            self._runtime.usage.listeners.remove(self.async_write_ha_state)
