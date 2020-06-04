"""
Support for Netatmo Smart Thermostat.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.netatmo/
"""
import logging
from datetime import timedelta
import voluptuous as vol

from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE
from homeassistant.components.climate import (
    STATE_HEAT, STATE_IDLE, ClimateDevice, PLATFORM_SCHEMA,
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_OPERATION_MODE, SUPPORT_AWAY_MODE)
from homeassistant.util import Throttle
# from homeassistant.loader import get_component
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = [
    'https://github.com/gieljnssns/netatmo-api-python/archive/'
    'dev-thermostat.zip#lnetatmo==0.9.2.1.1']

DEPENDENCIES = ['netatmo']

_LOGGER = logging.getLogger(__name__)

CONF_RELAY = 'relay'
CONF_THERMOSTAT = 'thermostat'

# DEFAULT_AWAY_TEMPERATURE = 14
# # The default offeset is 2 hours (when you use the thermostat itself)
DEFAULT_TIME_OFFSET = 7200
# # Return cached results if last scan was less then this time ago
# # NetAtmo Data is uploaded to server every hour
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_RELAY): cv.string,
    vol.Optional(CONF_THERMOSTAT, default=[]):
        vol.All(cv.ensure_list, [cv.string]),
})

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE |
                 SUPPORT_AWAY_MODE)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the NetAtmo Thermostat."""
    # netatmo = get_component('netatmo')
    netatmo = hass.components.netatmo
    device = config.get(CONF_RELAY)

    import lnetatmo
    try:
        data = ThermostatData(netatmo.NETATMO_AUTH, device)
        for module_name in data.get_module_names():
            if (
                CONF_THERMOSTAT in config
                and config[CONF_THERMOSTAT] != []
                and module_name not in config[CONF_THERMOSTAT]
            ):
                continue
            add_devices([NetatmoThermostat(data, module_name, device)], True)
    except lnetatmo.NoDevice:
        return None


class NetatmoThermostat(ClimateDevice):
    """Representation a Netatmo thermostat."""

    def __init__(self, data, module_name, device):
        """Initialize the sensor."""
        self._data = data
        self._state = None
        self._device = device
        self._name = module_name
        self.module_id = data.thermostatdata.moduleByName(module=module_name,
                                                          device=device)['_id']
        self.device_id = data.thermostatdata.deviceByName(device=device)['_id']
        print(self.device_id)
        print(self.module_id)
        self._unique_id = "Netatmo_thermostat {0} - {1}".format(self._name,
                                                                self.module_id)
        # print(self._unique_id)
        self._target_temperature = None
        self._current_temperature = None
        self._operation = None
        self._away = None

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the device."""
        return self.current_operation

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        # return self._data.thermostatdata.temp
        # return self._data.thermostatdata.currentTemp(module=self._name)
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def current_operation(self):
        """Return the current state of the thermostat."""
        state = self._operation
        if state == 0:
            return STATE_IDLE
        elif state == 100:
            return STATE_HEAT

    @property
    def is_away_mode_on(self):
        """Return true if away mode is on."""
        return self._away

    def turn_away_mode_on(self):
        """Turn away on."""
        mode = "away"
        temp = None
        self._data.thermostatdata.setthermpoint(mode, temp, endTimeOffset=None, device_id=self.device_id, module_id=self.module_id)
        self._away = True

    def turn_away_mode_off(self):
        """Turn away off."""
        mode = "program"
        temp = None
        self._data.thermostatdata.setthermpoint(mode, temp, endTimeOffset=None, device_id=self.device_id, module_id=self.module_id)
        self._away = False

    def set_temperature(self, **kwargs):
        """Set new target temperature for 2 hours."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        mode = "manual"
        self._data.thermostatdata.setthermpoint(
            mode, temperature, DEFAULT_TIME_OFFSET, device_id=self.device_id, module_id=self.module_id)
        self._target_temperature = temperature
        self._away = False
        self.update()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from NetAtmo API and updates the states."""
        self._data.update()
        self._target_temperature = self._data.thermostatdata.setpoints(module=self._name, device=self._device)
        # self._target_temperature = self._data.thermostatdata.setpoint_temp
        self._away = self._data.thermostatdata.away(module=self._name, device=self._device) == 'away'
        # self._away = self._data.thermostatdata.setpoint_mode == 'away'
        self._current_temperature = self._data.thermostatdata.currentTemp(module=self._name, device=self._device)
        self._operation = self._data.thermostatdata.operation(module=self._name, device=self._device)


class ThermostatData(object):
    """Get the latest data from Netatmo."""

    def __init__(self, auth, device=None):
        """Initialize the data object."""
        self.auth = auth
        self.thermostatdata = None
        self.module_names = []
        self.device = device

    def get_module_names(self):
        """Return all module available on the API as a list."""
        self.update()
        if not self.device:
            for device in self.thermostatdata.modules:
                for module in self.thermostatdata.modules[device].values():
                    self.module_names.append(module['module_name'])
        else:
            for module in self.thermostatdata.modules[self.device].values():
                self.module_names.append(module['module_name'])
        return self.module_names

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Call the NetAtmo API to update the data."""
        import lnetatmo
        self.thermostatdata = lnetatmo.ThermostatData(self.auth)
