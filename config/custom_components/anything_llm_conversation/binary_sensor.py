"""AnythingLLM connectivity binary sensor."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .helpers import AnythingLLMClient

_LOGGER = logging.getLogger(__name__)

type AnythingLLMConfigEntry = ConfigEntry[AnythingLLMClient]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AnythingLLMConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the AnythingLLM connectivity sensor for a config entry."""
    async_add_entities([AnythingLLMConnectivitySensor(entry)])


class AnythingLLMConnectivitySensor(BinarySensorEntity):
    """Binary sensor showing whether the AnythingLLM primary endpoint is reachable."""

    _attr_has_entity_name = True
    _attr_name = "Connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, entry: AnythingLLMConfigEntry) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_connectivity"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="AnythingLLM Server",
            manufacturer="AnythingLLM",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self) -> bool | None:
        """Return True when the primary endpoint is reachable."""
        return self._entry.runtime_data._primary_healthy

    async def async_added_to_hass(self) -> None:
        """Register health callback so the sensor updates immediately on change."""
        self._entry.runtime_data.add_health_listener(self._on_health_change)

    async def async_will_remove_from_hass(self) -> None:
        """Deregister health callback on removal."""
        self._entry.runtime_data.remove_health_listener(self._on_health_change)

    @callback
    def _on_health_change(self, healthy: bool | None) -> None:
        """Push updated state to HA when health status changes."""
        self.async_write_ha_state()
