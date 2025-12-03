"""Binary sensor platform for Smart Heating Predictor"""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup binary sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        AnomalyDetectedSensor(coordinator),
        ModelTrainedSensor(coordinator),
    ])

class AnomalyDetectedSensor(CoordinatorEntity, BinarySensorEntity):
    """Anomaly detection binary sensor."""
    
    def __init__(self, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_name = "Smart Heating Anomaly Detected"
        self._attr_unique_id = f"{DOMAIN}_anomaly_detected"
        self._attr_device_class = "problem"
        self._attr_icon = "mdi:alert-circle"
    
    @property
    def is_on(self):
        """Return true if anomaly detected recently."""
        return len(self.coordinator.anomalies) > 0

class ModelTrainedSensor(CoordinatorEntity, BinarySensorEntity):
    """Model trained status binary sensor."""
    
    def __init__(self, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_name = "Smart Heating Model Trained"
        self._attr_unique_id = f"{DOMAIN}_model_trained"
        self._attr_icon = "mdi:check-circle"
    
    @property
    def is_on(self):
        """Return true if model is trained."""
        return self.coordinator.predictor.is_trained
