"""Thermal Analysis integration for Home Assistant."""
import logging
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "thermal_analysis"
PLATFORMS = [Platform.SENSOR]

# Configuration keys
CONF_INDOOR_TEMP = "indoor_temp_sensor"
CONF_OUTDOOR_TEMP = "outdoor_temp_sensor"
CONF_HP_POWER = "heat_pump_power_sensor"
CONF_SOLAR_POWER = "solar_power_sensor"
CONF_HP_THRESHOLD = "heat_pump_threshold"
CONF_COP = "coefficient_of_performance"
CONF_FLOW_FORWARD = "flow_forward_temp_sensor"
CONF_FLOW_RETURN = "flow_return_temp_sensor"

# Service schema
SERVICE_PREDICT_RUNTIME_SCHEMA = vol.Schema({
    vol.Required("outdoor_temp_forecast"): vol.All(cv.ensure_list, [vol.Coerce(float)]),
    vol.Required("solar_power_forecast"): vol.All(cv.ensure_list, [vol.Coerce(float)]),
    vol.Optional("target_temperature", default=20.0): vol.Coerce(float),
})

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Thermal Analysis from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    async def handle_predict_runtime(call: ServiceCall) -> None:
        """Handle the prediction service."""
        outdoor_temp_forecast = call.data["outdoor_temp_forecast"]
        solar_forecast = call.data["solar_power_forecast"]
        target_temp = call.data.get("target_temperature", 20.0)
        
        _LOGGER.info(f"Prediction service called with {len(outdoor_temp_forecast)} data points")
        
        # Get the sensor and update it
        for entry_id in hass.data[DOMAIN]:
            if entry_id == "services_registered":
                continue
            sensor = hass.data[DOMAIN].get(f"{entry_id}_runtime_sensor")
            if sensor:
                await sensor.update_forecast(outdoor_temp_forecast, solar_forecast, target_temp)
                break
        else:
            _LOGGER.error("Runtime sensor not found")
    
    # Register service only once
    if not hass.data[DOMAIN].get("services_registered"):
        hass.services.async_register(
            DOMAIN,
            "predict_runtime",
            handle_predict_runtime,
            schema=SERVICE_PREDICT_RUNTIME_SCHEMA,
        )
        hass.data[DOMAIN]["services_registered"] = True
        _LOGGER.info("Service 'predict_runtime' registered")
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok