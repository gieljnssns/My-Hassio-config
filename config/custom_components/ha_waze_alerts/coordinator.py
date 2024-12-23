"""DataUpdateCoordinator for ha-waze-alerts."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import CONF_RADIUS
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import fetch_alerts
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from homeassistant.core import Event, EventStateChangedData


class WazeAlertsCoordinator(DataUpdateCoordinator):
    """Custom coordinator to fetch data for Waze Alerts."""

    def __init__(self, hass, config_entry):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Waze Alerts Coordinator",
            update_interval=None,  # Updates triggered manually
        )
        self.config_entry = config_entry

        async def location_changed(event: Event[EventStateChangedData]) -> None:
            if not hass.data[DOMAIN][config_entry.entry_id]["enabled"]:
                return  # Volgen is uitgeschakeld
            entity_id = event.data["entity_id"]
            old_state = event.data["old_state"]
            new_state = event.data["new_state"]
            if not old_state or not new_state:
                return
            new_lat = new_state.attributes.get("latitude")
            new_lon = new_state.attributes.get("longitude")

            if new_lat and new_lon:
                _LOGGER.info("%s moved to: %s, %s", entity_id, new_lat, new_lon)

                # Call helper to send location
                await self._async_update_data(lat=new_lat, lon=new_lon)

        async_track_state_change_event(
            hass, config_entry.data["device_tracker"], location_changed
        )

    async def _async_update_data(self, lat: float, lon: float) -> dict:
        """Fetch data from the API."""
        radius = self.config_entry.options[CONF_RADIUS]
        try:
            data = await fetch_alerts(lat, lon, radius)
            self.async_set_updated_data(data)
        except Exception as e:
            _LOGGER.exception("Error fetching data: %s", e)
            raise
        return data
