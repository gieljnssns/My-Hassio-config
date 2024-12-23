"""Sensor platform for Waze Alerts."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CATEGORY, DOMAIN
from .coordinator import WazeAlertsCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup sensors for each category."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    categories = entry.options.get(CONF_CATEGORY, [])
    if coordinator.data is None:
        coordinator.data = {"alerts": []}
    sensors = [
        WazeAlertsSensor(coordinator, entry, category) for category in categories
    ]

    async_add_entities(sensors)


class WazeAlertsSensor(CoordinatorEntity[WazeAlertsCoordinator], SensorEntity):
    """Sensor for a specific category."""

    def __init__(
        self,
        coordinator: WazeAlertsCoordinator,
        config_entry: ConfigEntry,
        category: str,
    ) -> None:
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._state = 0
        self._attributes = {}
        self._category = category
        self._alerts = []

    @property
    def unique_id(self) -> str:
        """Een unieke ID voor de sensor."""
        return f"{self.coordinator.config_entry.entry_id}_sensor_{self._category}"

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @property
    def name(self) -> str:
        return f"Waze Alerts - {self._category}"

    @property
    def state(self):
        return self._state

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data.get("alerts", [])
        if not data:
            return

        # Filter alerts by the configured category
        filtered_alerts = [
            alert for alert in data if alert.get("type") == self._category
        ]

        self._state = len(filtered_alerts)
        self._alerts = filtered_alerts
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes for the sensor."""
        return {
            "alerts": [
                {
                    "latitude": alert.get("location", {}).get("y"),
                    "longitude": alert.get("location", {}).get("x"),
                    "description": alert.get("subtype"),
                }
                for alert in self._alerts
            ]
        }
