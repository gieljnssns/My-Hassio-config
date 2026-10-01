"""Platform for sensor integration."""
from __future__ import annotations
from datetime import datetime, timezone
import enum
import logging
from typing import cast, Any
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorEntityDescription, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from .coordinator import BrewfatherCoordinator, BrewfatherCoordinatorData
from .const import (
    DOMAIN,
    COORDINATOR,
    CONF_ALL_BATCH_INFO_SENSOR
)

_LOGGER = logging.getLogger(__name__)
SENSOR_PREFIX = "Brewfather"

class SensorUpdateData:
    state: Any
    attr_available: bool
    extra_state_attributes: dict[str, Any]
    
    def __init__(self):
        self.state = None
        self.attr_available = False
        self.extra_state_attributes = {}

class BrewfatherStatusSensor(CoordinatorEntity, SensorEntity):
    """Brewfather integration status sensor."""
    
    def __init__(
        self, 
        coordinator: BrewfatherCoordinator,
        entry: ConfigEntry,
        entity_description: SensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, context=None)
        self.entity_description = entity_description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{entity_description.key}"
        self._attr_name = f"{SENSOR_PREFIX} {entity_description.name}"

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        if not self.coordinator.last_update_success:
            return "disconnected"
        elif self._entry.data.get("custom_stream_enabled", False):
            return "monitoring"
        else:
            return "connected"
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = {
            "api_connection": "✅ Connected" if self.coordinator.last_update_success else "❌ Disconnected",
            "last_update": self.coordinator.last_update_success_time.isoformat() if self.coordinator.last_update_success_time else None,
        }
        
        if self._entry.data.get("custom_stream_enabled", False):
            attrs["custom_stream"] = "✅ Enabled"
            entity_name = self._entry.data.get("custom_stream_temperature_entity_name")
            if entity_name:
                entity = self.hass.states.get(entity_name)
                if entity:
                    unit = entity.attributes.get("unit_of_measurement", "°C")
                    attrs["temperature_entity"] = f"🌡️ {entity_name} ({unit})"
                    attrs["last_temperature"] = f"{entity.state}{unit}"
            
            # Add gravity info if configured
            gravity_entity_name = self._entry.data.get("custom_stream_gravity_entity_name")
            if gravity_entity_name:
                gravity_entity = self.hass.states.get(gravity_entity_name)
                if gravity_entity:
                    attrs["gravity_entity"] = f"🍺 {gravity_entity_name}"
                    attrs["last_gravity"] = f"{gravity_entity.state}"
        else:
            attrs["custom_stream"] = "⚪ Disabled"
            
        return attrs

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        if not self.coordinator.last_update_success:
            return "mdi:beer-off"
        elif self._entry.data.get("custom_stream_enabled", False):
            return "mdi:beer-outline"
        else:
            return "mdi:beer"

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the sensor platforms."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    sensors = []

    # Add status sensor for UX improvement
    status_description = SensorEntityDescription(
        key="status",
        name="Integration Status",
        icon="mdi:beer",
    )
    sensors.append(BrewfatherStatusSensor(coordinator, entry, status_description))

    sensors.append(
        BrewfatherSensor(
            coordinator,
            SensorKinds.fermenting_name,
            SensorEntityDescription(
                key="recipe_name",
                name="Recipe name",
                icon="mdi:glass-mug",
            )
        )
    )

    sensors.append(
        BrewfatherSensor(
            coordinator,
            SensorKinds.fermenting_current_temperature,
            SensorEntityDescription(
                key="target_temperature",
                name="Target temperature",
                icon="mdi:thermometer",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            )
        )
    )

    sensors.append(
        BrewfatherSensor(
            coordinator,
            SensorKinds.fermenting_next_temperature,
            SensorEntityDescription(
                key="upcoming_target_temperature",
                name="Upcoming target temperature",
                icon="mdi:thermometer-chevron-up",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS, #Should we support fahrenheit?
                device_class=SensorDeviceClass.TEMPERATURE,
            )
        )
    )

    sensors.append(
        BrewfatherSensor(
            coordinator,
            SensorKinds.fermenting_next_date,
            SensorEntityDescription(
                key="upcoming_target_temperature_change",
                name="Upcoming target temperature change",
                icon="mdi:clock",
                device_class=SensorDeviceClass.TIMESTAMP,
            )
        )
    )

    sensors.append(
        BrewfatherSensor(
            coordinator,
            SensorKinds.fermenting_last_reading,
            SensorEntityDescription(
                key="last_reading",
                name="Last reading",
                icon="mdi:chart-line",
                state_class=SensorStateClass.MEASUREMENT,
            )
        )
    )

    all_batch_info_sensor = entry.data.get(CONF_ALL_BATCH_INFO_SENSOR, False)
    if all_batch_info_sensor:
        sensors.append(
            BrewfatherSensor(
                coordinator,
                SensorKinds.all_batch_info,
                SensorEntityDescription(
                    key="all_batches_data",
                    name="All batches data",
                    icon="mdi:database",
                )
            )
        ) 

    sensors.append(
        BrewfatherSensor(
            coordinator,
            SensorKinds.fermenting_start_date,
            SensorEntityDescription(
                key="fermentation_start_date",
                name="Fermentation start",
                icon="mdi:clock",
                device_class=SensorDeviceClass.TIMESTAMP,
            )
        )
    )

    sensors.append(
        BrewfatherSensor(
            coordinator,
            SensorKinds.batch_notes,
            SensorEntityDescription(
                key="batch_notes",
                name="Batch notes",
                icon="mdi:note-text",
            )
        )
    )

    sensors.append(
        BrewfatherSensor(
            coordinator,
            SensorKinds.events,
            SensorEntityDescription(
                key="events",
                name="Events",
                icon="mdi:calendar-clock",
            )
        )
    )

    sensors.extend([
        BrewfatherSensor(
            coordinator,
            SensorKinds.brewtracker_status,
            SensorEntityDescription(
                key="brewtracker_status",
                name="Brew Tracker status",
                icon="mdi:timeline-clock",
            )
        ),
        BrewfatherSensor(
            coordinator,
            SensorKinds.brewtracker_stage,
            SensorEntityDescription(
                key="brewtracker_stage",
                name="Brew Tracker stage",
                icon="mdi:clipboard-list",
            )
        ),
        BrewfatherSensor(
            coordinator,
            SensorKinds.brewtracker_step,
            SensorEntityDescription(
                key="brewtracker_step",
                name="Brew Tracker step",
                icon="mdi:format-list-checks",
            )
        ),
        BrewfatherSensor(
            coordinator,
            SensorKinds.brewtracker_progress,
            SensorEntityDescription(
                key="brewtracker_progress",
                name="Brew Tracker progress",
                icon="mdi:progress-clock",
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            )
        ),
        BrewfatherSensor(
            coordinator,
            SensorKinds.brewtracker_time_remaining,
            SensorEntityDescription(
                key="brewtracker_time_remaining",
                name="Brew Tracker time remaining",
                icon="mdi:timer-sand",
                native_unit_of_measurement="s",
                state_class=SensorStateClass.MEASUREMENT,
            )
        ),
        BrewfatherSensor(
            coordinator,
            SensorKinds.brewtracker_next_step,
            SensorEntityDescription(
                key="brewtracker_next_step",
                name="Brew Tracker next step",
                icon="mdi:skip-next",
            )
        ),
        BrewfatherSensor(
            coordinator,
            SensorKinds.brewtracker_raw,
            SensorEntityDescription(
                key="brewtracker_raw",
                name="Brew Tracker raw",
                icon="mdi:database-search",
            )
        ),
    ])

    async_add_entities(sensors, update_before_add=False)


class BrewfatherSensor(CoordinatorEntity[BrewfatherCoordinator], SensorEntity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """
    """Defines a sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        sensorKind: SensorKinds,
        description: SensorEntityDescription,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

        self._entity_description = description
        self._sensor_type = sensorKind


        # # Set Friendly name when sensor is first created
        self._attr_has_entity_name = True
        self._attr_name = f"{SENSOR_PREFIX} - {self._entity_description.name}"
        self._name = f"{SENSOR_PREFIX} - {self._entity_description.name}"

        # The unique identifier for this sensor within Home Assistant
        # has nothing to do with the entity_id, it is the internal unique_id of the sensor entity registry
        self._attr_unique_id = f"{SENSOR_PREFIX}_{self._entity_description.key}"


        self._attr_icon = self._entity_description.icon
        self._attr_state_class = self._entity_description.state_class
        self._attr_native_unit_of_measurement = self._entity_description.native_unit_of_measurement
        self._attr_device_class = self._entity_description.device_class
        #self._state = None
        self._discovery = False
        self._dev_id = {}

        brewfatherCoordinator: BrewfatherCoordinator = coordinator
        _LOGGER.debug(" __init__ | Initial refresh of the sensor data : %s", self._sensor_type.name)
        sensor_data = self._refresh_sensor_data(brewfatherCoordinator.data, self._sensor_type, self.device_class, self.entity_id)
        _LOGGER.debug(" sensor state : %s", sensor_data.state)
        _LOGGER.debug(" sensor attr available : %s", sensor_data.attr_available)
        _LOGGER.debug(" sensor attributes : %s", sensor_data.extra_state_attributes)
        self._state = sensor_data.state
        self._attr_available = sensor_data.attr_available
        self._attr_extra_state_attributes = sensor_data.extra_state_attributes
   
    @property
    def state(self) -> StateType:
        """Return the state."""
        return self._state

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._attr_available

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the sensors."""
        """Update Sensor Entity."""
        _LOGGER.debug(" _handle_coordinator_update | Updating state of the sensors : %s", self._sensor_type.name)
        #await self.coordinator.async_request_refresh()
        brewfatherCoordinator: BrewfatherCoordinator = self.coordinator
        sensor_data = self._refresh_sensor_data(brewfatherCoordinator.data, self._sensor_type, self.device_class, self.entity_id)
        _LOGGER.debug(" sensor state : %s", sensor_data.state)
        _LOGGER.debug(" sensor attr available : %s", sensor_data.attr_available)
        _LOGGER.debug(" sensor attributes : %s", sensor_data.extra_state_attributes)
        self._state = sensor_data.state
        self._attr_available = sensor_data.attr_available
        self._attr_extra_state_attributes = sensor_data.extra_state_attributes
        self.async_write_ha_state()

    @staticmethod
    def _stage(tracker: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(tracker, dict):
            return None
        stages = tracker.get("stages") or []
        index = tracker.get("stage")
        return stages[index] if isinstance(index, int) and 0 <= index < len(stages) and isinstance(stages[index], dict) else None

    @staticmethod
    def _step(stage: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(stage, dict):
            return None
        steps = stage.get("steps") or []
        index = stage.get("step")
        if isinstance(index, int) and 0 <= index < len(steps) and isinstance(steps[index], dict):
            return steps[index]
        return next((step for step in steps if isinstance(step, dict) and step.get("active") is True), None)

    @staticmethod
    def _next(tracker: dict[str, Any] | None) -> dict[str, Any] | None:
        """Return the next logical Brew Tracker step, crossing stage boundaries."""
        stage = BrewfatherSensor._stage(tracker)
        if not isinstance(stage, dict):
            return None

        steps = stage.get("steps") or []
        index = stage.get("step")
        if isinstance(index, int) and 0 <= index + 1 < len(steps) and isinstance(steps[index + 1], dict):
            return steps[index + 1]

        step = BrewfatherSensor._step(stage)
        if step is not None:
            try:
                i = steps.index(step)
            except ValueError:
                i = -1
            if i >= 0 and i + 1 < len(steps) and isinstance(steps[i + 1], dict):
                return steps[i + 1]

        if not isinstance(tracker, dict):
            return None
        stages = tracker.get("stages") or []
        stage_index = tracker.get("stage")
        if not isinstance(stage_index, int):
            return None

        for next_stage in stages[stage_index + 1:]:
            if not isinstance(next_stage, dict):
                continue
            for candidate in next_stage.get("steps") or []:
                if isinstance(candidate, dict):
                    return candidate

        return None

    @staticmethod
    def _remaining(stage: dict[str, Any] | None) -> float | None:
        if not isinstance(stage, dict):
            return None
        duration = stage.get("duration")
        position = stage.get("position")
        start = stage.get("start")
        if duration is None:
            return position
        if stage.get("paused") is True and position is not None:
            return min(max(float(position), 0), float(duration))
        if start is None:
            return None if position is None else min(max(float(position), 0), float(duration))
        elapsed = max((datetime.now(timezone.utc).timestamp() * 1000 - float(start)) / 1000, 0)
        return min(max(float(duration) - elapsed, 0), float(duration))

    @staticmethod
    def _progress(stage: dict[str, Any] | None) -> float | None:
        if not isinstance(stage, dict) or not stage.get("duration"):
            return None
        remaining = BrewfatherSensor._remaining(stage)
        if remaining is None:
            return None
        duration = float(stage["duration"])
        return round(min(max(((duration - remaining) / duration) * 100, 0), 100), 1)

    @staticmethod
    def _status(tracker: dict[str, Any] | None) -> str:
        if not isinstance(tracker, dict) or tracker.get("enabled") is not True or not tracker.get("stages"):
            return "inactive"
        if tracker.get("completed") is True:
            return "completed"
        stage = BrewfatherSensor._stage(tracker)
        return "paused" if isinstance(stage, dict) and stage.get("paused") is True else "running"

    @staticmethod
    def _base_attrs(data: BrewfatherCoordinatorData, tracker: dict[str, Any] | None) -> dict[str, Any]:
        stage = BrewfatherSensor._stage(tracker)
        step = BrewfatherSensor._step(stage)
        next_step = BrewfatherSensor._next(tracker)
        attrs = {
            "batch_id": data.batch_id,
            "brew_tracker_batch_id": data.brew_tracker_batch_id,
            "brew_tracker_batch_name": data.brew_tracker_batch_name,
            "brew_tracker_recipe_name": data.brew_tracker_recipe_name,
            "brew_tracker_batch_status": data.brew_tracker_batch_status,
            "active": BrewfatherSensor._status(tracker) != "inactive",
        }
        if isinstance(tracker, dict):
            attrs.update({
                "tracker_id": tracker.get("_id"),
                "enabled": tracker.get("enabled"),
                "completed": tracker.get("completed"),
                "status": BrewfatherSensor._status(tracker),
                "stage_index": tracker.get("stage"),
                "stage_count": len(tracker.get("stages") or []),
            })
        if stage is not None:
            stage_copy = dict(stage)
            stage_copy["remainingSeconds"] = BrewfatherSensor._remaining(stage)
            stage_copy["progressPercent"] = BrewfatherSensor._progress(stage)
            attrs["current_stage"] = stage_copy
        if step is not None:
            attrs["current_step"] = step
        if next_step is not None:
            attrs["next_step"] = next_step
        return attrs

    @staticmethod
    def _refresh_sensor_data(
        data: BrewfatherCoordinatorData,
        sensor_type: str,
        device_class: SensorDeviceClass,
        entity_id: str
    ) -> SensorUpdateData:
        """Get sensor data."""
        sensor_data = SensorUpdateData()
        if data is None:
            return sensor_data
        
        sensor_data.attr_available = True
        custom_attributes:dict[str, Any] = dict()

        if sensor_type == SensorKinds.fermenting_name:
            sensor_data.state = data.brew_name
            custom_attributes["batch_id"] = data.batch_id

            other_batches_data = []
            for other_batch_data in data.other_batches:
                other_batches_data.append({
                    "batch_id": other_batch_data.batch_id,
                    "state": other_batch_data.brew_name
                })
            if len(other_batches_data)  > 0:
                custom_attributes["other_batches"] = other_batches_data

        elif sensor_type == SensorKinds.fermenting_current_temperature:
            sensor_data.state = data.current_step_temperature
            custom_attributes["batch_id"] = data.batch_id

            other_batches_data = []
            for other_batch_data in data.other_batches:
                other_batches_data.append({
                    "batch_id": other_batch_data.batch_id,
                    "state": other_batch_data.current_step_temperature
                })
            if len(other_batches_data)  > 0:
                custom_attributes["other_batches"] = other_batches_data

        elif sensor_type == SensorKinds.fermenting_next_date:
            sensor_data.state = data.next_step_date
            custom_attributes["batch_id"] = data.batch_id

            other_batches_data = []
            for other_batch_data in data.other_batches:
                other_batches_data.append({
                    "batch_id": other_batch_data.batch_id,
                    "state": other_batch_data.next_step_date
                })
            if len(other_batches_data)  > 0:
                custom_attributes["other_batches"] = other_batches_data

        elif sensor_type == SensorKinds.fermenting_next_temperature:
            sensor_data.state = data.next_step_temperature
            custom_attributes["batch_id"] = data.batch_id

            other_batches_data = []
            for other_batch_data in data.other_batches:
                other_batches_data.append({
                    "batch_id": other_batch_data.batch_id,
                    "state": other_batch_data.next_step_temperature
                })
            if len(other_batches_data)  > 0:
                custom_attributes["other_batches"] = other_batches_data

        elif sensor_type == SensorKinds.fermenting_last_reading:
            if data.last_reading is not None:
                sensor_data.state = data.last_reading.sg
                custom_attributes["batch_id"] = data.batch_id

                custom_attributes["angle"] = data.last_reading.angle
                custom_attributes["temp"] = data.last_reading.temp
                custom_attributes["time_ms"] = data.last_reading.time
                custom_attributes["time"] = datetime.fromtimestamp(data.last_reading.time / 1000, timezone.utc)
                custom_attributes["pressure"] = data.last_reading.pressure
                
                other_batches_data = []
                for other_batch_data in data.other_batches:
                    entry = {
                        "state": other_batch_data.last_reading.sg,
                        "batch_id": other_batch_data.batch_id,
                        "angle": other_batch_data.last_reading.angle,
                        "temp": other_batch_data.last_reading.temp,
                        "time_ms": other_batch_data.last_reading.time,
                        "time": datetime.fromtimestamp(data.last_reading.time / 1000, timezone.utc),
                        "pressure": other_batch_data.last_reading.pressure,
                    }
                    other_batches_data.append(entry)
                    
                if len(other_batches_data)  > 0:
                    custom_attributes["other_batches"] = other_batches_data

        elif sensor_type == SensorKinds.all_batch_info:

            all_batches = []
            for other_batch in data.all_batches_data:
                all_batches.append(other_batch.to_attribute_entry_hassio())
                
            custom_attributes["data"] = all_batches
            sensor_data.state = len(all_batches)

        elif sensor_type == SensorKinds.fermenting_start_date:
            if data.start_date is not None:
                sensor_data.state = data.start_date
                custom_attributes["batch_id"] = data.batch_id
                
                other_batches_data = []
                for other_batch_data in data.other_batches:
                    other_batches_data.append({
                        "batch_id": other_batch_data.batch_id,
                        "state": other_batch_data.start_date
                    })
                if len(other_batches_data)  > 0:
                    custom_attributes["other_batches"] = other_batches_data

        elif sensor_type == SensorKinds.batch_notes:
            if data.batch_notes is not None:
                sensor_data.state = data.batch_notes
                custom_attributes["batch_id"] = data.batch_id
                
                other_batches_data = []
                for other_batch_data in data.other_batches:
                    if other_batch_data.batch_notes is not None:
                        other_batches_data.append({
                            "batch_id": other_batch_data.batch_id,
                            "state": other_batch_data.batch_notes
                        })
                if len(other_batches_data)  > 0:
                    custom_attributes["other_batches"] = other_batches_data

        elif sensor_type == SensorKinds.events:
            # Filter for future events that are active
            current_time = datetime.now(timezone.utc).timestamp() * 1000  # Convert to milliseconds
            future_events = []
            
            if data.events is not None:
                for event in data.events:
                    # Filter: must be in the future AND active must be True
                    if event.time is not None and event.time > current_time and event.active is True:
                        future_events.append({
                            "title": event.title,
                            "description": event.description,
                            "time": datetime.fromtimestamp(event.time / 1000, timezone.utc),
                            "time_ms": event.time,
                            "event_type": event.event_type,
                            "day_event": event.day_event,
                            "active": event.active
                        })
                
                # Sort by time
                future_events.sort(key=lambda x: x["time_ms"])
                
                sensor_data.state = len(future_events)
                custom_attributes["batch_id"] = data.batch_id
                custom_attributes["events"] = future_events
                
                # Add other batches events
                other_batches_data = []
                for other_batch_data in data.other_batches:
                    batch_future_events = []
                    if other_batch_data.events is not None:
                        for event in other_batch_data.events:
                            # Filter: must be in the future AND active must be True
                            if event.time is not None and event.time > current_time and event.active is True:
                                batch_future_events.append({
                                    "title": event.title,
                                    "description": event.description,
                                    "time": datetime.fromtimestamp(event.time / 1000, timezone.utc),
                                    "time_ms": event.time,
                                    "event_type": event.event_type,
                                    "day_event": event.day_event,
                                    "active": event.active
                                })
                        batch_future_events.sort(key=lambda x: x["time_ms"])
                    
                    if len(batch_future_events) > 0:
                        other_batches_data.append({
                            "batch_id": other_batch_data.batch_id,
                            "state": len(batch_future_events),
                            "events": batch_future_events
                        })
                
                if len(other_batches_data)  > 0:
                    custom_attributes["other_batches"] = other_batches_data

        elif sensor_type in {
            SensorKinds.brewtracker_status,
            SensorKinds.brewtracker_stage,
            SensorKinds.brewtracker_step,
            SensorKinds.brewtracker_progress,
            SensorKinds.brewtracker_time_remaining,
            SensorKinds.brewtracker_next_step,
            SensorKinds.brewtracker_raw,
        }:
            tracker = data.brew_tracker
            stage = BrewfatherSensor._stage(tracker)
            step = BrewfatherSensor._step(stage)
            next_step = BrewfatherSensor._next(tracker)
            custom_attributes = BrewfatherSensor._base_attrs(data, tracker)

            if sensor_type == SensorKinds.brewtracker_status:
                sensor_data.state = BrewfatherSensor._status(tracker)
            elif sensor_type == SensorKinds.brewtracker_stage and stage is not None:
                sensor_data.state = stage.get("name")
            elif sensor_type == SensorKinds.brewtracker_step and step is not None:
                sensor_data.state = step.get("name")
            elif sensor_type == SensorKinds.brewtracker_progress:
                sensor_data.state = BrewfatherSensor._progress(stage)
            elif sensor_type == SensorKinds.brewtracker_time_remaining:
                remaining = BrewfatherSensor._remaining(stage)
                sensor_data.state = round(remaining) if remaining is not None else None
            elif sensor_type == SensorKinds.brewtracker_next_step and next_step is not None:
                sensor_data.state = next_step.get("name")
            elif sensor_type == SensorKinds.brewtracker_raw:
                sensor_data.state = BrewfatherSensor._status(tracker)
                custom_attributes["data"] = tracker
                custom_attributes["recipe"] = data.brew_tracker_recipe

            if sensor_data.state is None:
                sensor_data.attr_available = False

        sensor_data.extra_state_attributes = custom_attributes

        # Received a datetime
        if sensor_data.state is not None and device_class == SensorDeviceClass.TIMESTAMP:
            try:
                # We cast the value, to avoid using isinstance, but satisfy
                # typechecking. The errors are guarded in this try.
                value = cast(datetime, sensor_data.state)
                if value.tzinfo is None:
                    raise ValueError(
                        f"Invalid datetime: {entity_id} provides state '{value}', "
                        "which is missing timezone information"
                    )

                if value.tzinfo != timezone.utc:
                    value = value.astimezone(timezone.utc)

                _LOGGER.debug("value %s, %s", value, value.tzinfo)

                #return value.isoformat(timespec="seconds")
                sensor_data.state =value.isoformat(timespec="seconds")
            except (AttributeError, TypeError) as err:
                raise ValueError(
                    f"Invalid datetime: {entity_id} has a timestamp device class"
                    f"but does not provide a datetime state but {type(value)}"
                ) from err
            
        return sensor_data

class SensorKinds(enum.Enum):
    fermenting_name = 1
    fermenting_current_temperature = 2
    fermenting_next_temperature = 3
    fermenting_next_date = 4
    #fermenting_batches = 5
    fermenting_last_reading = 6
    all_batch_info = 7
    fermenting_start_date = 8
    batch_notes = 9
    events = 10
    brewtracker_status = 11
    brewtracker_stage = 12
    brewtracker_step = 13
    brewtracker_progress = 14
    brewtracker_time_remaining = 15
    brewtracker_next_step = 16
    brewtracker_raw = 17
