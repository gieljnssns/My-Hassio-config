"""Smart Heating Predictor Integration for Home Assistant"""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "select", "number"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Smart Heating Predictor component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Heating Predictor from a config entry."""
    coordinator = SmartHeatingCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    await async_setup_services(hass, coordinator)
    
    # Register reload service
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_setup_services(hass: HomeAssistant, coordinator: SmartHeatingCoordinator) -> None:
    """Register integration services."""
    
    async def set_schedule_slot(call):
        """Set schedule slot."""
        day = call.data.get("day")
        hour = call.data.get("hour")
        target_temp = call.data.get("target_temp")
        room = call.data.get("room", "default")
        
        key = f"{day}_{hour}_{room}"
        coordinator.schedule[key] = target_temp
        await coordinator.async_request_refresh()
        
        _LOGGER.info(f"Schedule slot set: {key} = {target_temp}°C")
    
    async def set_learning_mode(call):
        """Set learning mode."""
        mode = call.data.get("mode")
        coordinator.predictor.learning_mode = mode
        await coordinator.async_request_refresh()
        
        _LOGGER.info(f"Learning mode set to: {mode}")
    
    async def trigger_training(call):
        """Trigger immediate model training."""
        await hass.async_add_executor_job(coordinator.predictor.train_model)
        await coordinator.async_request_refresh()
        
        _LOGGER.info("Manual training triggered")
    
    async def clear_training_data(call):
        """Clear all training data."""
        coordinator.predictor.training_data = []
        coordinator.predictor.is_trained = False
        await coordinator.async_request_refresh()
        
        _LOGGER.info("Training data cleared")
    
    hass.services.async_register(DOMAIN, "set_schedule_slot", set_schedule_slot)
    hass.services.async_register(DOMAIN, "set_learning_mode", set_learning_mode)
    hass.services.async_register(DOMAIN, "trigger_training", trigger_training)
    hass.services.async_register(DOMAIN, "clear_training_data", clear_training_data)
