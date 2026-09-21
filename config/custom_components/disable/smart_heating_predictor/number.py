"""Number platform for Smart Heating Predictor"""
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AnomalyThresholdNumber(coordinator)])


class AnomalyThresholdNumber(CoordinatorEntity, NumberEntity):
    """Anomaly detection threshold number entity."""
    
    def __init__(self, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._attr_name = "Smart Heating Anomaly Threshold"
        self._attr_unique_id = f"{DOMAIN}_anomaly_threshold"
        self._attr_native_min_value = 0.5
        self._attr_native_max_value = 5.0
        self._attr_native_step = 0.1
        self._attr_native_unit_of_measurement = "°C/5min"
        self._attr_icon = "mdi:thermometer-alert"
    
    @property
    def native_value(self):
        """Return current threshold."""
        return self.coordinator.predictor.anomaly_threshold
    
    async def async_set_native_value(self, value):
        """Set new threshold."""
        self.coordinator.predictor.anomaly_threshold = value
        await self.coordinator.async_request_refresh()
