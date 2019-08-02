"""
Support for Kostal Piko inverters.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/sensor.piko/
"""
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_USERNAME, CONF_PASSWORD, CONF_HOST, CONF_MONITORED_CONDITIONS)
from homeassistant.helpers.entity import Entity
# from homeassistant.helpers.restore_state import async_get_last_state
import homeassistant.helpers.config_validation as cv

# REQUIREMENTS = [
#     'https://github.com/gieljnssns/KostalPikoPy/archive/'
#     'master.zip#pikopy==1.1.0']

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    'solar_generator_power': ['Solar generator power', 'W', 'mdi:solar-power'],
    'consumption_phase_1': ['Consumption phase 1', 'W', 'mdi:power-socket-eu'],
    'consumption_phase_2': ['Consumption phase 2', 'W', 'mdi:power-socket-eu'],
    'consumption_phase_3': ['Consumption phase 3', 'W', 'mdi:power-socket-eu'],
    'current_power': ['Current power', 'W', 'mdi:solar-power'],
    'total_energy': ['Total energy', 'kWh', 'mdi:solar-power'],
    'daily_energy': ['Daily energy', 'kWh', 'mdi:solar-power'],
    'string1_voltage': ['String 1 voltage', 'V', 'mdi:current-ac'],
    'string1_current': ['String 1 current', 'A', 'mdi:flash'],
    'string2_voltage': ['String 2 voltage', 'V', 'mdi:current-ac'],
    'string2_current': ['String 2 current', 'A', 'mdi:flash'],
    'string3_voltage': ['String 3 voltage', 'V', 'mdi:current-ac'],
    'string3_current': ['String 3 current', 'A', 'mdi:flash'],
    'l1_voltage': ['L1 voltage', 'V', 'mdi:current-ac'],
    'l1_power': ['L1 power', 'W', 'mdi:power-plug'],
    'l2_voltage': ['L2 voltage', 'V', 'mdi:current-ac'],
    'l2_power': ['L2 power', 'W', 'mdi:power-plug'],
    'l3_voltage': ['L3 voltage', 'V', 'mdi:current-ac'],
    'l3_power': ['L3 power', 'W', 'mdi:power-plug'],
}


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_MONITORED_CONDITIONS):
        vol.All(cv.ensure_list, [vol.In(list(SENSOR_TYPES))]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Piko inverter."""
    from kostalpyko.kostalpyko import Piko

    piko = Piko(config[CONF_HOST],
                config[CONF_USERNAME],
                config[CONF_PASSWORD])

    dev = []
    for sensor in config[CONF_MONITORED_CONDITIONS]:
        dev.append(PikoInverter(piko, sensor))

    add_entities(dev)


class PikoInverter(Entity):
    """Representation of a Piko inverter."""

    def __init__(self, piko_data, sensor_type):
        """Initialize the sensor."""
        self._name = SENSOR_TYPES[sensor_type][0]
        self.type = sensor_type
        self.piko = piko_data
        self._state = None
        self._unit_of_measurement = SENSOR_TYPES[self.type][1]
        self._icon = SENSOR_TYPES[self.type][2]
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format('Kostal Piko', self._name)

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Return icon."""
        return self._icon

    def update(self):
        """Update inverter data."""
        if self.type == 'solar_generator_power':
            self._state = self.piko.get_solar_generator_power()
        elif self.type == 'consumption_phase_1':
            self._state = self.piko.get_consumption_phase_1()
        elif self.type == 'consumption_phase_2':
            self._state = self.piko.get_consumption_phase_2()
        elif self.type == 'consumption_phase_3':
            self._state = self.piko.get_consumption_phase_3()
        elif self.type == 'current_power':
            self._state = self.piko.get_current_power()
        elif self.type == 'total_energy':
            self._state = self.piko.get_total_energy()
        elif self.type == 'daily_energy':
            self._state = self.piko.get_daily_energy()
        elif self.type == 'string1_voltage':
            self._state = self.piko.get_string1_voltage()
        elif self.type == 'string1_current':
            self._state = self.piko.get_string1_current()
        elif self.type == 'string2_voltage':
            self._state = self.piko.get_string2_voltage()
        elif self.type == 'string2_current':
            self._state = self.piko.get_string2_current()
        elif self.type == 'string3_voltage':
            self._state = self.piko.get_string3_voltage()
        elif self.type == 'string3_current':
            self._state = self.piko.get_string3_current()
        elif self.type == 'l1_voltage':
            self._state = self.piko.get_l1_voltage()
        elif self.type == 'l1_power':
            self._state = self.piko.get_l1_power()
        elif self.type == 'l2_voltage':
            self._state = self.piko.get_l2_voltage()
        elif self.type == 'l2_power':
            self._state = self.piko.get_l2_power()
        elif self.type == 'l3_voltage':
            self._state = self.piko.get_l3_voltage()
        elif self.type == 'l3_power':
            self._state = self.piko.get_l3_power()
