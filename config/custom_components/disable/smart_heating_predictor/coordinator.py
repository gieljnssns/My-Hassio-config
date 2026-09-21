"""Data coordinator for Smart Heating Predictor"""
from datetime import timedelta, datetime
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import logging
import os
from .ml_engine import HeatingPredictor
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class SmartHeatingCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Smart Heating Predictor data."""
    
    def __init__(self, hass, config_entry):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Smart Heating Predictor",
            update_interval=timedelta(minutes=5),
        )
        self.config_entry = config_entry
        
        # Initialize ML predictor
        model_path = os.path.join(hass.config.config_dir, "smart_heating_model.pkl")
        self.predictor = HeatingPredictor(hass, hass.config.config_dir)
        self.predictor.load_model(model_path)
        self._model_path = model_path
        self._last_training = None
        
        self.schedule = {}
        self.thermostats = config_entry.options.get("thermostats", [])
        self.weather_entity = config_entry.options.get("weather_entity")
        self.outdoor_temp_sensor = config_entry.options.get("outdoor_temp_sensor")
        self.outdoor_humidity_sensor = config_entry.options.get("outdoor_humidity_sensor")
        self.anomalies = []
        self.last_temps = {}
        self.predictions = {}
        self.anomaly_detection_enabled = True
        
    async def _async_update_data(self):
        """Update data."""
        current_time = datetime.now()
        
        # Collect thermostat data
        thermostat_data = await self._collect_thermostat_data()
        
        # Get weather data
        weather_data = await self._get_weather_data()
        
        # Check for anomalies if enabled
        if self.anomaly_detection_enabled:
            await self._check_anomalies(thermostat_data)
        
        # In learning mode, collect training data
        if self.predictor.learning_mode:
            await self._collect_training_data(thermostat_data, weather_data)
        else:
            # In operation mode, make predictions
            await self._execute_predictions(thermostat_data, weather_data)
        
        # Train model at night (3:00-4:00) if in learning mode
        training_hour = 3
        if (current_time.hour == training_hour and self.predictor.learning_mode and 
            (self._last_training is None or (current_time - self._last_training).days >= 1)):
            success = await self.hass.async_add_executor_job(self.predictor.train_model)
            if success:
                await self.hass.async_add_executor_job(self.predictor.save_model, self._model_path)
                self._last_training = current_time
        
        return {
            'thermostat_data': thermostat_data,
            'weather_data': weather_data,
            'anomalies': self.anomalies,
            'learning_mode': self.predictor.learning_mode,
            'is_trained': self.predictor.is_trained,
            'predictions': self.predictions
        }
    
    async def _collect_thermostat_data(self):
        """Collect data from thermostats."""
        data = {}
        for thermostat_id in self.thermostats:
            state = self.hass.states.get(thermostat_id)
            if state:
                data[thermostat_id] = {
                    'current_temp': float(state.attributes.get('current_temperature', 20)),
                    'target_temp': float(state.attributes.get('temperature', 20)),
                    'temp_delta': float(state.attributes.get('temperature', 20)) - float(state.attributes.get('current_temperature', 20)),
                    'state': state.state
                }
        return data
    
    async def _get_weather_data(self):
        """Get weather data from sensors or weather entity."""
        outdoor_temp = 15.0
        outdoor_humidity = 50.0
        
        # Try outdoor temperature sensor first
        if self.outdoor_temp_sensor:
            temp_state = self.hass.states.get(self.outdoor_temp_sensor)
            if temp_state:
                try:
                    outdoor_temp = float(temp_state.state)
                except (ValueError, TypeError):
                    pass
        
        # Try outdoor humidity sensor
        if self.outdoor_humidity_sensor:
            humidity_state = self.hass.states.get(self.outdoor_humidity_sensor)
            if humidity_state:
                try:
                    outdoor_humidity = float(humidity_state.state)
                except (ValueError, TypeError):
                    pass
        
        # Fallback to weather entity if sensors not configured
        if not self.outdoor_temp_sensor and self.weather_entity:
            weather_state = self.hass.states.get(self.weather_entity)
            if weather_state:
                outdoor_temp = float(weather_state.attributes.get('temperature', outdoor_temp))
                outdoor_humidity = float(weather_state.attributes.get('humidity', outdoor_humidity))
        
        return {
            'outdoor_temp': outdoor_temp,
            'outdoor_humidity': outdoor_humidity
        }
    
    async def _check_anomalies(self, thermostat_data):
        """Check for anomalies in temperature changes."""
        current_time = datetime.now()
        
        for thermostat_id, data in thermostat_data.items():
            current_temp = data['current_temp']
            
            # Check if we have previous temperature data
            if thermostat_id in self.last_temps:
                last_temp, last_time = self.last_temps[thermostat_id]
                time_diff = (current_time - last_time).total_seconds() / 60  # minutes
                
                if time_diff > 0:
                    temp_change_rate = (current_temp - last_temp) / time_diff
                    
                    # Detect anomaly
                    if abs(temp_change_rate) > self.predictor.anomaly_threshold:
                        self.anomalies.append({
                            'thermostat_id': thermostat_id,
                            'time': current_time.isoformat(),
                            'change_rate': temp_change_rate,
                            'type': 'rapid_change'
                        })
            
            # Update last temperature
            self.last_temps[thermostat_id] = (current_temp, current_time)
        
        # Keep only recent anomalies (last 24 hours)
        cutoff_time = current_time - timedelta(hours=24)
        self.anomalies = [
            a for a in self.anomalies 
            if datetime.fromisoformat(a['time']) > cutoff_time
        ]
    
    async def _collect_training_data(self, thermostat_data, weather_data):
        """Collect training data in learning mode."""
        current_time = datetime.now()
        
        for thermostat_id, data in thermostat_data.items():
            features = self.predictor.collect_features(
                data,
                weather_data['outdoor_temp'],
                weather_data['outdoor_humidity'],
                data['target_temp'],
                current_time
            )
            
            # Calculate actual heat-on time (simplified)
            if data['temp_delta'] > 0:
                estimated_time = abs(data['temp_delta']) * 10  # rough estimate
                self.predictor.add_training_sample(features, estimated_time)
    
    async def _execute_predictions(self, thermostat_data, weather_data):
        """Execute predictions in operation mode."""
        current_time = datetime.now()
        
        for thermostat_id, data in thermostat_data.items():
            features = self.predictor.collect_features(
                data,
                weather_data['outdoor_temp'],
                weather_data['outdoor_humidity'],
                data['target_temp'],
                current_time
            )
            
            preheat_time = self.predictor.predict_preheat_time(features)
            self.predictions[thermostat_id] = {
                'preheat_time': preheat_time,
                'current_temp': data['current_temp'],
                'target_temp': data['target_temp'],
                'outdoor_temp': weather_data['outdoor_temp']
            }
