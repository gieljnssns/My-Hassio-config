# Smart Heating Predictor Configuration Flow
# Author: prezes9732

from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

class SmartHeatingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Heating Predictor."""
    
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Smart Heating Predictor", data=user_input)
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return SmartHeatingOptionsFlow(config_entry)


class SmartHeatingOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Smart Heating Predictor."""
    
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
    
    async def async_step_init(self, user_input=None):
        """Manage the main options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["thermostats", "sensors", "schedule", "advanced"]
        )
    
    async def async_step_thermostats(self, user_input=None):
        """Configure thermostats."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        # Get available climate entities
        climate_entities = [
            entity_id for entity_id in self.hass.states.async_entity_ids()
            if entity_id.startswith('climate.')
        ]
        
        return self.async_show_form(
            step_id="thermostats",
            data_schema=vol.Schema({
                vol.Optional("thermostats", default=self.config_entry.options.get("thermostats", [])): 
                    cv.multi_select(climate_entities),
            })
        )
    
    async def async_step_sensors(self, user_input=None):
        """Configure weather sensors."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        # Get available weather and sensor entities
        weather_entities = [
            entity_id for entity_id in self.hass.states.async_entity_ids()
            if entity_id.startswith('weather.')
        ]
        
        temp_sensors = [
            entity_id for entity_id in self.hass.states.async_entity_ids()
            if entity_id.startswith('sensor.') and 'temp' in entity_id.lower()
        ]
        
        humidity_sensors = [
            entity_id for entity_id in self.hass.states.async_entity_ids()
            if entity_id.startswith('sensor.') and ('humidity' in entity_id.lower() or 'humid' in entity_id.lower())
        ]
        
        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema({
                vol.Optional("weather_entity", default=self.config_entry.options.get("weather_entity")): 
                    vol.In(weather_entities),
                vol.Optional("outdoor_temp_sensor", default=self.config_entry.options.get("outdoor_temp_sensor")): 
                    vol.In(temp_sensors),
                vol.Optional("outdoor_humidity_sensor", default=self.config_entry.options.get("outdoor_humidity_sensor")): 
                    vol.In(humidity_sensors),
            })
        )
    
    async def async_step_schedule(self, user_input=None):
        """Configure schedule settings."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        return self.async_show_form(
            step_id="schedule",
            data_schema=vol.Schema({
                vol.Optional("comfort_temp", default=self.config_entry.options.get("comfort_temp", 21.0)): 
                    vol.Coerce(float),
                vol.Optional("eco_temp", default=self.config_entry.options.get("eco_temp", 18.0)): 
                    vol.Coerce(float),
                vol.Optional("night_temp", default=self.config_entry.options.get("night_temp", 16.0)): 
                    vol.Coerce(float),
            })
        )
    
    async def async_step_advanced(self, user_input=None):
        """Configure advanced ML settings."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema({
                vol.Optional("learning_mode", default=self.config_entry.options.get("learning_mode", True)): 
                    bool,
                vol.Optional("learning_days", default=self.config_entry.options.get("learning_days", 14)): 
                    vol.All(vol.Coerce(int), vol.Range(min=7, max=60)),
                vol.Optional("training_hour", default=self.config_entry.options.get("training_hour", 3)): 
                    vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
                vol.Optional("anomaly_threshold", default=self.config_entry.options.get("anomaly_threshold", 2.5)): 
                    vol.All(vol.Coerce(float), vol.Range(min=0.5, max=5.0)),
            })
        )
