"""Sensor platform for Smart Heating Predictor"""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        LearningProgressSensor(coordinator),
        TrainingSamplesSensor(coordinator),
        RecommendedLearningTimeSensor(coordinator),
    ]
    
    # Add prediction sensors for each thermostat
    for thermostat_id in coordinator.thermostats:
        sensors.append(PreheatPredictionSensor(coordinator, thermostat_id))
    
    async_add_entities(sensors)


class LearningProgressSensor(CoordinatorEntity, SensorEntity):
    """Learning progress sensor."""
    
    def __init__(self, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._attr_name = "Smart Heating Learning Progress"
        self._attr_unique_id = f"{DOMAIN}_learning_progress"
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:school"
    
    @property
    def native_value(self):
        """Return progress percentage."""
        samples = len(self.coordinator.predictor.training_data)
        target = 100 * len(self.coordinator.thermostats)
        return min(100, int((samples / target) * 100)) if target > 0 else 0


class TrainingSamplesSensor(CoordinatorEntity, SensorEntity):
    """Training samples counter."""
    
    def __init__(self, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._attr_name = "Smart Heating Training Samples"
        self._attr_unique_id = f"{DOMAIN}_training_samples"
        self._attr_icon = "mdi:database"
    
    @property
    def native_value(self):
        """Return number of training samples."""
        return len(self.coordinator.predictor.training_data)


class RecommendedLearningTimeSensor(CoordinatorEntity, SensorEntity):
    """Recommended learning time sensor."""
    
    def __init__(self, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._attr_name = "Smart Heating Recommended Learning Time"
        self._attr_unique_id = f"{DOMAIN}_learning_time"
        self._attr_icon = "mdi:clock-outline"
    
    @property
    def native_value(self):
        """Return recommended days."""
        samples = len(self.coordinator.predictor.training_data)
        target = 100 * len(self.coordinator.thermostats)
        if samples >= target:
            return "Ready"
        days_left = max(1, int((target - samples) / 10))
        return f"{days_left} days"


class PreheatPredictionSensor(CoordinatorEntity, SensorEntity):
    """Preheat time prediction sensor."""
    
    def __init__(self, coordinator, thermostat_id):
        """Initialize."""
        super().__init__(coordinator)
        self._thermostat_id = thermostat_id
        name = thermostat_id.replace("climate.", "").replace("_", " ").title()
        self._attr_name = f"Preheat Time {name}"
        self._attr_unique_id = f"{DOMAIN}_preheat_{thermostat_id}"
        self._attr_native_unit_of_measurement = "min"
        self._attr_icon = "mdi:timer"
    
    @property
    def native_value(self):
        """Return predicted preheat time."""
        if not self.coordinator.predictor.is_trained:
            return None
        return 30  # Simplified - would calculate from prediction
