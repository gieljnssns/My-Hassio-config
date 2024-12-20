import logging
from datetime import datetime

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from ..utils.misc import async_resolve_entity_id_from_unique_id, get_config_value
from ..entity import SmoothingAnalyticsEntity
from ..const import (
    DEFAULT_EMA_DESIRED_TIME_TO_95,
    DOMAIN,
    ICON
)


_LOGGER = logging.getLogger(__name__)


def calculate_alpha(desired_time_to_95, update_interval):
    """Calculate alpha for Exponential Moving Average (EMA) based on smoothing window and update interval."""

    # Calculate the number of updates in the smoothing window
    number_of_updates_needed = desired_time_to_95 / update_interval

    # Calculate alpha based on the number of updates needed
    return 2 / (number_of_updates_needed + 1)


def ema_filter(value, previous_value, alpha):
    """Apply Exponential Moving Average (EMA) filter using the given alpha"""
    return alpha * value + (1 - alpha) * previous_value


class EmaSensor(SmoothingAnalyticsEntity, RestoreEntity):
    """Exponential Moving Average (EMA) filtered sensor with persistent state and device support, based on unique_id."""

    # Define the attributes of the entity
    _attr_icon = ICON
    _attr_has_entity_name = True

    def __init__(self, input_unique_id, desired_time_to_95, sensor_hash, config_entry):
        super().__init__(config_entry)
        self._input_unique_id = input_unique_id
        self._desired_time_to_95 = desired_time_to_95
        self._sensor_hash = sensor_hash
        self._state = None
        self._previous_value = None
        self._last_updated = None
        self._input_entity_id = None
        self._unit_of_measurement = None
        self._device_class = None
        self._state_class = None
        self._last_reset = None
        self._config_entry = config_entry
        self._unique_id = f"sas_ema_{sensor_hash}"
        self._update_interval = 1
        self._update_settings()

    def _update_settings(self):
        """Fetch updated settings from config_entry."""
        self._desired_time_to_95 = get_config_value(self._config_entry,
            "desired_time_to_95", DEFAULT_EMA_DESIRED_TIME_TO_95
        )

        # Recalculate alpha based on the new settings
        if self._update_interval is not None:
            self._alpha = calculate_alpha(
                self._desired_time_to_95, self._update_interval
            )

        # Log updated settings
        _LOGGER.debug(
            f"Updated EMA settings: desired_time_to_95={self._desired_time_to_95}, _update_interval={self._update_interval}, alpha={self._alpha}"
        )

    @property
    def name(self):
        return f"EMA Filtered Sensor {self._sensor_hash}"

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def device_class(self):
        return self._device_class

    @property
    def state_class(self):
        return self._state_class

    @property
    def last_reset(self):
        return self._last_reset

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""

        return {
            "alpha": self._alpha,
            "desired_time_to_95": self._desired_time_to_95,
            "input_entity_id": self._input_entity_id,
            "input_unique_id": self._input_unique_id,
            "last_updated": self._last_updated,
            "number_of_updates_needed": self._desired_time_to_95
            / self._update_interval,
            "previous_value": self._previous_value,
            "sensor_hash": self._sensor_hash,
            "sensor_update_interval": self._update_interval,
            "type": "ema",
            "unique_id": self._unique_id,
        }

    async def async_update(self):
        """Manually trigger the sensor update."""
        await self._handle_update(event=None)

    async def _handle_update(self, event):
        """Handle the sensor state update (for both manual and state change)."""

        # Get the current time
        now = datetime.now()

        # Calculate the update interval to be used
        if self._last_updated is not None:
            self._update_interval = (
                now - datetime.fromisoformat(self._last_updated)
            ).total_seconds()

        # Ensure settings are reloaded if config is changed.
        self._update_settings()

        # Check if the input_entity_id has been resolved from unique_id
        if not self._input_entity_id:
            await self._resolve_input_entity_id()

        # Continue if input_entity_id is available
        if not self._input_entity_id:
            _LOGGER.warning(f"Entity with unique_id {self._input_unique_id} not found.")
            return

        # Fetch the current value from the input sensor
        input_state = self.hass.states.get(self._input_entity_id)
        if input_state is None or input_state.state is None:
            _LOGGER.warning(
                f"Sensor {self._input_entity_id} not ready or not found. Skipping EMA sensor update."
            )
            return
        try:
            input_value = float(input_state.state)
        except ValueError:
            _LOGGER.warning(
                f"Invalid value from {self._input_entity_id}: {input_state.state}"
            )
            return

        # Fetch unit_of_measurement and device_class from the input sensor
        self._unit_of_measurement = input_state.attributes.get("unit_of_measurement")
        self._device_class = input_state.attributes.get("device_class")
        self._state_class = input_state.attributes.get("state_class")

        # Update the previous EMA value to the new EMA value
        self._previous_value = self._state

        # Apply EMA filter using pre-calculated alpha
        if self._previous_value is not None:
            self._state = round(
                ema_filter(input_value, self._previous_value, self._alpha), 2
            )
        else:
            self._state = input_value

        # Update count and last update time
        self._last_updated = now.isoformat()

        # Trigger an update in Home Assistant
        self.async_write_ha_state()

    async def _resolve_input_entity_id(self):
        """Resolve the entity_id from the unique_id using entity_registry."""

        # Resolve the entity_id from the unique_id
        registry = er.async_get(self.hass)

        # Resolve the entity_id from the unique_id
        entry = registry.async_get_entity_id("sensor", DOMAIN, self._input_unique_id)

        # Store the resolved entity_id
        if entry:
            self._input_entity_id = entry

            _LOGGER.debug(
                f"Resolved entity_id for unique_id {self._input_unique_id}: {self._input_entity_id}"
            )
        else:
            _LOGGER.warning(
                f"Entity with unique_id {self._input_unique_id} not found in registry."
            )

    async def async_added_to_hass(self):
        """Handle the sensor being added to Home Assistant."""

        # Restore the previous state from persistent storage
        old_state = await self.async_get_last_state()

        if old_state is not None:
            _LOGGER.info(f"Restoring state for {self._unique_id}")

            try:
                self._state = round(float(old_state.state), 2)
                self._previous_value = float(self._state)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    f"Could not restore state for {self._unique_id}, invalid value: {old_state.state}"
                )
                self._state = None
                self._previous_value = None

            self._last_updated = old_state.attributes.get("last_updated", None)
            self._update_interval = old_state.attributes.get("update_interval", 1)
        else:
            _LOGGER.info(
                f"No previous state found for {self._unique_id}, starting fresh."
            )

        # Check if the input_entity_id has been resolved from unique_id
        if not self._input_entity_id:
            _LOGGER.debug(f"Resolving entity_id for unique_id {self._input_unique_id}")
            await self._resolve_input_entity_id()

        # Continue if input_entity_id is available
        if not self._input_entity_id:
            _LOGGER.warning(
                f"Entity with unique_id {self._input_unique_id} not found. Unable to track state changes."
            )
            return

        # Start listening for state changes of the input sensor
        if self._input_entity_id:
            _LOGGER.info(
                f"Starting to track state changes for entity_id {self._input_entity_id}"
            )
            async_track_state_change_event(
                self.hass, [self._input_entity_id], self._handle_update
            )
        else:
            _LOGGER.error(
                f"Failed to track state changes, input_entity_id is not resolved."
            )
