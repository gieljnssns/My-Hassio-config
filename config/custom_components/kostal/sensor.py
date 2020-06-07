"""Support for Kostal Piko inverters."""
from datetime import timedelta
import logging

from kostalpyko.kostalpyko import Piko

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_USERNAME, CONF_PASSWORD, CONF_HOST, CONF_MONITORED_CONDITIONS, CONF_NAME)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "kostal_piko"

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
    'status': ['Status', None, 'mdi:solar-power'],
}


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_MONITORED_CONDITIONS):
        vol.All(cv.ensure_list, [vol.In(list(SENSOR_TYPES))]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Piko inverter."""
    piko = Piko(config[CONF_HOST],
                config[CONF_USERNAME],
                config[CONF_PASSWORD])

    dev = []
    data = PikoData(piko)
    for sensor in config[CONF_MONITORED_CONDITIONS]:
        dev.append(PikoInverter(data, sensor, config[CONF_NAME]))

    add_entities(dev)


class PikoInverter(Entity):
    """Representation of a Piko inverter."""

    def __init__(self, piko_data, sensor_type, name):
        """Initialize the sensor."""
        self._sensor = SENSOR_TYPES[sensor_type][0]
        self._name = name
        self.type = sensor_type
        self.piko = piko_data
        self._state = None
        self._unit_of_measurement = SENSOR_TYPES[self.type][1]
        self._icon = SENSOR_TYPES[self.type][2]
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self._name, self._sensor)

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
        """Update data."""
        self.piko.update()
        data = self.piko.data
        ba_data = self.piko.ba_data
        if ba_data is not None:
            if self.type == 'solar_generator_power':
                if len(ba_data) > 1:
                    self._state = ba_data[5]
                else:
                    return "No BA sensor installed"
            elif self.type == 'consumption_phase_1':
                if len(ba_data) > 1:
                    self._state = ba_data[8]
                else:
                    return "No BA sensor installed"
            elif self.type == 'consumption_phase_2':
                if len(ba_data) > 1:
                    self._state = ba_data[9]
                else:
                    return "No BA sensor installed"
            elif self.type == 'consumption_phase_3':
                if len(ba_data) > 1:
                    self._state = ba_data[10]
                else:
                    return "No BA sensor installed"
        if data is not None:
            if self.type == 'current_power':
                if len(data) > 1:
                    self._state = data[0]
                else:
                    return None
            elif self.type == 'total_energy':
                if len(data) > 1:
                    self._state = data[1]
                else:
                    return None
            elif self.type == 'daily_energy':
                if len(data) > 1:
                    self._state = data[2]
                else:
                    return None
            elif self.type == 'string1_voltage':
                if len(data) > 1:
                    self._state = data[3]
                else:
                    return None
            elif self.type == 'string1_current':
                if len(data) > 1:
                    self._state = data[5]
            elif self.type == 'string2_voltage':
                if len(data) > 1:
                    self._state = data[7]
                else:
                    return None
            elif self.type == 'string2_current':
                if len(data) > 1:
                    self._state = data[9]
                else:
                    return None
            elif self.type == 'string3_voltage':
                if len(data) > 1:
                    self._state = data[0]
                else:
                    return None
            elif self.type == 'string3_current':
                if len(data) > 1:
                    self._state = data[0]
                else:
                    return None
            elif self.type == 'l1_voltage':
                if len(data) > 1:
                    self._state = data[4]
                else:
                    return None
            elif self.type == 'l1_power':
                if len(data) > 1:
                    self._state = data[6]
                else:
                    return None
            elif self.type == 'l2_voltage':
                if len(data) > 1:
                    self._state = data[8]
                else:
                    return None
            elif self.type == 'l2_power':
                if len(data) > 1:
                    self._state = data[10]
                else:
                    return None
            elif self.type == 'l3_voltage':
                if len(data) > 1:
                    if len(data) < 15:
                        # 2 Strings
                        self._state = data[11]
                    else:
                        # 3 Strings
                        self._state = data[12]
                else:
                    return None
            elif self.type == 'l3_power':
                if len(data) > 1:
                    if len(data) < 15:
                        # 2 Strings
                        self._state = data[12]
                    else:
                        # 3 Strings
                        self._state = data[14]
                else:
                    return None
            elif self.type == 'status':
                if len(data) > 1:
                    if len(data) < 15:
                        # 2 Strings
                        self._state = data[13]
                    else:
                        # 3 Strings
                        self._state = data[15]
                else:
                    return None


class PikoData(Entity):
    """Representation of a Piko inverter."""
    def __init__(self, piko):
        """Initialize the data object."""
        self.data = []
        self.ba_data = []
        self.piko = piko
    
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update inverter data."""
        self.data = self.piko._get_raw_content()
        self.ba_data = self.piko._get_content_of_own_consumption()
        _LOGGER.debug(self.data)
        _LOGGER.debug(self.ba_data)
