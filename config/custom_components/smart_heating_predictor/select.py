"""Select platform for Smart Heating Predictor"""
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup select platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LearningModeSelect(coordinator)])


class LearningModeSelect(CoordinatorEntity, SelectEntity):
    """Learning mode select entity."""
    
    def __init__(self, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._attr_name = "Smart Heating Mode"
        self._attr_unique_id = f"{DOMAIN}_mode"
        self._attr_options = ["Learning", "Operating"]
        self._attr_icon = "mdi:school"
    
    @property
    def current_option(self):
        """Return current mode."""
        return "Learning" if self.coordinator.predictor.learning_mode else "Operating"
    
    async def async_select_option(self, option):
        """Change the mode."""
        self.coordinator.predictor.learning_mode = (option == "Learning")
        await self.coordinator.async_request_refresh()
