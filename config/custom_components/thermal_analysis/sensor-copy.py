"""Thermal Analysis sensors."""
import logging
from datetime import datetime, timedelta
from typing import Optional
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import linregress

from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.recorder import get_instance, history
from homeassistant.util import dt as dt_util
from homeassistant.const import UnitOfPower, UnitOfEnergy, UnitOfTime, UnitOfTemperature

from . import (
    DOMAIN,
    CONF_INDOOR_TEMP,
    CONF_OUTDOOR_TEMP,
    CONF_HP_POWER,
    CONF_SOLAR_POWER,
    CONF_HP_THRESHOLD,
    CONF_COP,
    CONF_FLOW_FORWARD,
    CONF_FLOW_RETURN,
)

_LOGGER = logging.getLogger(__name__)

# Constants
C_WATER = 4186  # J/(kg·K)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the thermal analysis sensors."""
    
    config = hass.data[DOMAIN][entry.entry_id]
    
    # Create all sensors
    sensors = [
        ThermalParameterSensor(
            hass, config, entry.entry_id,
            "UA Value", "ua_value", "W/K", "mdi:fire"
        ),
        ThermalParameterSensor(
            hass, config, entry.entry_id,
            "Thermal Mass", "thermal_mass", "MJ/K", "mdi:weight"
        ),
        ThermalParameterSensor(
            hass, config, entry.entry_id,
            "Time Constant", "time_constant", "h", "mdi:timer-sand"
        ),
        ThermalParameterSensor(
            hass, config, entry.entry_id,
            "Estimated Flow Rate", "flow_rate", "L/s", "mdi:pipe"
        ),
        HeatPumpRuntimeSensor(hass, config, entry.entry_id),
    ]
    
    async_add_entities(sensors, True)
    
    # Store the runtime sensor for the service
    hass.data[DOMAIN][f"{entry.entry_id}_runtime_sensor"] = sensors[-1]
    
    _LOGGER.info("Thermal Analysis sensors created")


class ThermalParameterSensor(SensorEntity):
    """Sensor for thermal parameters."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        config: dict,
        entry_id: str,
        name: str, 
        param_type: str, 
        unit: str,
        icon: str
    ):
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self._attr_name = f"House {name}"
        self._attr_unique_id = f"thermal_{entry_id}_{param_type}"
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = icon
        self._param_type = param_type
        self._state = None
        self._attr_should_poll = True

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    async def async_update(self):
        """Update the sensor."""
        try:
            if self._param_type == "ua_value":
                self._state = await self._calculate_ua_value()
            elif self._param_type == "thermal_mass":
                mass = await self._calculate_thermal_mass()
                if mass:
                    self._state = round(mass / 1e6, 2)  # Convert to MJ/K
            elif self._param_type == "time_constant":
                ua = await self._calculate_ua_value()
                mass = await self._calculate_thermal_mass()
                if ua and mass and ua > 0:
                    self._state = round((mass / ua) / 3600, 2)  # in hours
            elif self._param_type == "flow_rate":
                self._state = await self._estimate_flow_rate()
                
        except Exception as e:
            _LOGGER.error(f"Error updating {self._param_type}: {e}")

    async def _calculate_ua_value(self) -> Optional[float]:
        """Calculate UA value from cooling periods."""
        end_time = dt_util.now()
        start_time = end_time - timedelta(days=30)
        
        sensor_indoor = self._config[CONF_INDOOR_TEMP]
        sensor_outdoor = self._config[CONF_OUTDOOR_TEMP]
        sensor_hp = self._config[CONF_HP_POWER]
        hp_threshold = self._config[CONF_HP_THRESHOLD]
        
        # Get historical data
        history_list = await get_instance(self.hass).async_add_executor_job(
            history.state_changes_during_period,
            self.hass,
            start_time,
            end_time,
            str(sensor_indoor)
        )

        # Get data for other sensors
        outdoor_history = await get_instance(self.hass).async_add_executor_job(
            history.state_changes_during_period,
            self.hass,
            start_time,
            end_time,
            str(sensor_outdoor)
        )

        hp_history = await get_instance(self.hass).async_add_executor_job(
            history.state_changes_during_period,
            self.hass,
            start_time,
            end_time,
            str(sensor_hp)
        )

        # Combine histories
        history_list = {
            sensor_indoor: history_list.get(sensor_indoor, []),
            sensor_outdoor: outdoor_history.get(sensor_outdoor, []),
            sensor_hp: hp_history.get(sensor_hp, [])
        }
        
        if not history_list:
            return None
            
        # Find cooling periods (HP off, >2 hours)
        hp_data = history_list.get(sensor_hp, [])
        indoor_data = history_list.get(sensor_indoor, [])
        outdoor_data = history_list.get(sensor_outdoor, [])
        
        if not all([hp_data, indoor_data, outdoor_data]):
            return None
        
        # Identify cooling periods
        cooling_periods = []
        hp_off_start = None
        
        for state in hp_data:
            try:
                power = float(state.state)
                if power <= hp_threshold and hp_off_start is None:
                    hp_off_start = state.last_changed
                elif power > hp_threshold and hp_off_start is not None:
                    duration = (state.last_changed - hp_off_start).total_seconds() / 3600
                    if duration >= 2:  # At least 2 hours
                        cooling_periods.append((hp_off_start, state.last_changed))
                    hp_off_start = None
            except (ValueError, AttributeError):
                continue
        
        if not cooling_periods:
            _LOGGER.warning("No cooling periods found")
            return None
        
        # Analyze cooling periods
        ua_values = []
        
        for start, end in cooling_periods[:10]:  # Analyze max 10 periods
            # Collect data for this period
            temp_indoor = []
            temp_outdoor = []
            times = []
            
            for state in indoor_data:
                if start <= state.last_changed <= end:
                    try:
                        temp_indoor.append(float(state.state))
                        times.append((state.last_changed - start).total_seconds() / 3600)
                    except ValueError:
                        continue
            
            if len(temp_indoor) < 5:
                continue
            
            # Get average outdoor temperature for this period
            outdoor_temps = [float(s.state) for s in outdoor_data 
                          if start <= s.last_changed <= end 
                          and s.state not in ['unknown', 'unavailable']]
            
            if not outdoor_temps:
                continue
                
            avg_outdoor = np.mean(outdoor_temps)
            
            # Fit exponential cooling: T(t) = T_outdoor + (T0 - T_outdoor) * exp(-t/tau)
            try:
                # Linear regression on log scale
                delta_t = np.array(temp_indoor) - avg_outdoor
                if np.any(delta_t <= 0):
                    continue
                    
                slope, intercept, r_value, _, _ = linregress(times, np.log(delta_t))
                
                if r_value**2 > 0.7:  # Good fit
                    tau = -1 / slope  # time constant in hours
                    # Estimate thermal mass (assumption: ~10 MJ/K for average house)
                    estimated_mass = 10e6  # J/K
                    ua = estimated_mass / (tau * 3600)  # W/K
                    ua_values.append(ua)
                    
            except Exception as e:
                _LOGGER.debug(f"Error fitting cooling curve: {e}")
                continue
        
        if ua_values:
            median_ua = float(np.median(ua_values))
            _LOGGER.info(f"UA value calculated: {median_ua:.1f} W/K from {len(ua_values)} periods")
            return round(median_ua, 1)
        
        return None

    async def _calculate_thermal_mass(self) -> Optional[float]:
        """Calculate thermal mass from heating periods."""
        end_time = dt_util.now()
        start_time = end_time - timedelta(days=30)
        
        sensor_indoor = self._config[CONF_INDOOR_TEMP]
        sensor_hp = self._config[CONF_HP_POWER]
        hp_threshold = self._config[CONF_HP_THRESHOLD]
        cop = self._config[CONF_COP]
        
        # Get historical data
        indoor_history = await get_instance(self.hass).async_add_executor_job(
            history.state_changes_during_period,
            self.hass,
            start_time,
            end_time,
            str(sensor_indoor)
        )

        hp_history = await get_instance(self.hass).async_add_executor_job(
            history.state_changes_during_period,
            self.hass,
            start_time,
            end_time,
            str(sensor_hp)
        )

        # Combine histories
        history_list = {
            sensor_indoor: indoor_history.get(sensor_indoor, []),
            sensor_hp: hp_history.get(sensor_hp, [])
        }
        
        if not history_list:
            return None
        
        hp_data = history_list.get(sensor_hp, [])
        indoor_data = history_list.get(sensor_indoor, [])
        
        # Find heating periods (HP on, stable heating)
        heating_periods = []
        hp_on_start = None
        
        for state in hp_data:
            try:
                power = float(state.state)
                if power > hp_threshold and hp_on_start is None:
                    hp_on_start = state.last_changed
                elif power <= hp_threshold and hp_on_start is not None:
                    duration = (state.last_changed - hp_on_start).total_seconds() / 3600
                    if 1 <= duration <= 4:  # 1-4 hour heating periods
                        heating_periods.append((hp_on_start, state.last_changed))
                    hp_on_start = None
            except (ValueError, AttributeError):
                continue
        
        if not heating_periods:
            return None
        
        mass_values = []
        
        for start, end in heating_periods[:10]:
            # Determine temperature rise
            temps_before = [float(s.state) for s in indoor_data 
                          if start - timedelta(minutes=30) <= s.last_changed <= start
                          and s.state not in ['unknown', 'unavailable']]
            temps_after = [float(s.state) for s in indoor_data 
                         if end <= s.last_changed <= end + timedelta(minutes=30)
                         and s.state not in ['unknown', 'unavailable']]
            
            if not temps_before or not temps_after:
                continue
            
            delta_t = np.mean(temps_after) - np.mean(temps_before)
            
            if delta_t < 0.2:  # Too small rise
                continue
            
            # Average power during heating
            powers = [float(s.state) for s in hp_data 
                     if start <= s.last_changed <= end
                     and s.state not in ['unknown', 'unavailable']]
            
            if not powers:
                continue
                
            avg_power = np.mean(powers) * cop  # Thermal power
            duration_sec = (end - start).total_seconds()
            
            # Energy = Power * time
            energy = avg_power * duration_sec  # Joules
            
            # C = Energy / delta_T
            mass = energy / delta_t
            mass_values.append(mass)
        
        if mass_values:
            median_mass = float(np.median(mass_values))
            _LOGGER.info(f"Thermal mass calculated: {median_mass/1e6:.1f} MJ/K from {len(mass_values)} periods")
            return round(median_mass, 0)
        
        return None

    async def _estimate_flow_rate(self) -> Optional[float]:
        """Estimate flow rate from temperature difference and power."""
        # This function only works if you have floor heating sensors
        sensor_forward = self._config.get(CONF_FLOW_FORWARD)
        sensor_return = self._config.get(CONF_FLOW_RETURN)
        
        if not sensor_forward or not sensor_return:
            return None
        
        # Get recent states
        forward_state = self.hass.states.get(sensor_forward)
        return_state = self.hass.states.get(sensor_return)
        hp_state = self.hass.states.get(self._config[CONF_HP_POWER])
        
        if not all([forward_state, return_state, hp_state]):
            return None
        
        try:
            t_forward = float(forward_state.state)
            t_return = float(return_state.state)
            hp_power = float(hp_state.state)
            cop = self._config[CONF_COP]
            
            if t_forward <= t_return or hp_power < self._config[CONF_HP_THRESHOLD]:
                return None
            
            # Q = m * c * delta_T
            # m = Q / (c * delta_T)
            thermal_power = hp_power * cop  # Watts
            delta_t = t_forward - t_return
            
            # Flow rate in kg/s = W / (J/(kg·K) * K)
            flow_kg_s = thermal_power / (C_WATER * delta_t)
            
            # Convert to L/s (1 kg water ≈ 1 L)
            flow_l_s = flow_kg_s
            
            return round(flow_l_s, 3)
            
        except (ValueError, AttributeError):
            return None


class HeatPumpRuntimeSensor(SensorEntity):
    """Sensor for predicted heat pump runtime."""

    def __init__(self, hass: HomeAssistant, config: dict, entry_id: str):
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self._attr_name = "Heat Pump Predicted Runtime Tomorrow"
        self._attr_unique_id = f"thermal_{entry_id}_predicted_runtime"
        self._attr_native_unit_of_measurement = UnitOfTime.HOURS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:clock-outline"
        self._state = None
        self._attributes = {}

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return self._attributes

    async def update_forecast(
        self, 
        outdoor_temps: list, 
        solar_powers: list, 
        target_temp: float
    ):
        """Update the forecast based on new data."""
        try:
            # Get thermal parameters
            ua_value = None
            thermal_mass = None
            
            for entity_id in self.hass.states.async_entity_ids('sensor'):
                state = self.hass.states.get(entity_id)
                if state and 'ua_value' in entity_id:
                    try:
                        ua_value = float(state.state)
                    except (ValueError, TypeError):
                        pass
                elif state and 'thermal_mass' in entity_id:
                    try:
                        thermal_mass = float(state.state) * 1e6  # Convert MJ/K to J/K
                    except (ValueError, TypeError):
                        pass
            
            if not ua_value or not thermal_mass:
                _LOGGER.error("Thermal parameters not yet available")
                self._state = None
                return
            
            if ua_value <= 0 or thermal_mass <= 0:
                _LOGGER.error("Invalid thermal parameters")
                self._state = None
                return
            
            cop = self._config[CONF_COP]
            
            # Calculate required runtime per hour
            total_runtime = 0
            hourly_runtimes = []
            
            for hour, (t_outdoor, solar_power) in enumerate(zip(outdoor_temps, solar_powers)):
                # Heat loss = UA * (T_indoor - T_outdoor)
                heat_loss = ua_value * (target_temp - t_outdoor)  # Watts
                
                # Solar gain (estimate: 30% of PV output becomes heat in house)
                solar_gain = solar_power * 0.30  # Watts
                
                # Net heat requirement
                net_heat_needed = max(0, heat_loss - solar_gain)  # Watts
                
                # Thermal power of heat pump (estimate based on average consumption)
                # Assumption: average 1500W electrical = 7000W thermal
                # TODO: Make this configurable or estimate from historical data
                hp_thermal_power = 1500 * cop  # Watts
                
                # Required runtime this hour
                if hp_thermal_power > 0:
                    runtime_fraction = net_heat_needed / hp_thermal_power
                    runtime_hour = min(1.0, runtime_fraction)  # Max 1 hour per hour
                else:
                    runtime_hour = 0
                
                total_runtime += runtime_hour
                hourly_runtimes.append({
                    'hour': hour,
                    'outdoor_temp': round(t_outdoor, 1),
                    'solar_power': round(solar_power, 0),
                    'heat_loss': round(heat_loss, 0),
                    'solar_gain': round(solar_gain, 0),
                    'net_requirement': round(net_heat_needed, 0),
                    'runtime': round(runtime_hour, 2)
                })
            
            self._state = round(total_runtime, 1)
            self._attributes = {
                'last_update': datetime.now().isoformat(),
                'target_temperature': target_temp,
                'ua_value_used': ua_value,
                'thermal_mass_used': thermal_mass / 1e6,  # MJ/K
                'cop_used': cop,
                'hourly_details': hourly_runtimes,
                'total_heat_loss_24h': round(sum(h['heat_loss'] for h in hourly_runtimes) / 1000, 1),
                'total_solar_gain_24h': round(sum(h['solar_gain'] for h in hourly_runtimes) / 1000, 1),
            }
            
            _LOGGER.info(f"Runtime prediction updated: {self._state} hours for next 24 hours")
            self.async_write_ha_state()
            
        except Exception as e:
            _LOGGER.error(f"Error calculating prediction: {e}", exc_info=True)
            self._state = None