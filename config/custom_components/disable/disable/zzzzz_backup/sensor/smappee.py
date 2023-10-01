"""
Support for monitoring a Smappee energy sensor.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.smappee/
"""
import logging
from datetime import timedelta

from homeassistant.components.smappee import DATA_SMAPPEE
from homeassistant.helpers.entity import Entity

DEPENDENCIES = ['smappee']

_LOGGER = logging.getLogger(__name__)

SENSOR_PREFIX = 'Smappee'
SENSOR_TYPES = {
    'solar':
        ['Solar', 'mdi:white-balance-sunny', 'local', 'W', 'solar'],
    'active_power':
        ['Active Power', 'mdi:power-plug', 'local', 'W', 'active_power'],
    'current':
        ['Current', 'mdi:gauge', 'local', 'A', 'current'],
    'voltage':
        ['Voltage', 'mdi:gauge', 'local', 'V', 'voltage'],
    'active_cosfi':
        ['Power Factor', 'mdi:gauge', 'local', '%', 'active_cosfi'],
    'alwayson_today':
        ['Always On Today', 'mdi:gauge', 'remote', 'W', 'alwaysOn'],
    'solar_today':
        ['Solar Today', 'mdi:white-balance-sunny', 'remote', 'kWh', 'solar'],
    'power_today':
        ['Power Today', 'mdi:power-plug', 'remote', 'kWh', 'consumption']
}

SCAN_INTERVAL = timedelta(seconds=30)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Smappee sensor."""
    smappee = hass.data[DATA_SMAPPEE]

    dev = []
    if smappee.is_remote_active:
        for sensor in SENSOR_TYPES:
            if 'remote' in SENSOR_TYPES[sensor]:
                for location_id in smappee.locations.keys():
                    dev.append(SmappeeSensor(smappee, location_id, sensor))

    if smappee.is_local_active:
        for sensor in SENSOR_TYPES:
            if 'local' in SENSOR_TYPES[sensor]:
                if smappee.is_remote_active:
                    for location_id in smappee.locations.keys():
                        dev.append(SmappeeSensor(smappee, location_id, sensor))
                else:
                    dev.append(SmappeeSensor(smappee, None, sensor))
    add_devices(dev, True)


class SmappeeSensor(Entity):
    """Implementation of a Smappee sensor."""

    def __init__(self, smappee, location_id, sensor):
        """Initialize the sensor."""
        self._smappee = smappee
        self._location_id = location_id
        self._sensor = sensor
        self.data = None
        self._state = None
        self._name = SENSOR_TYPES[self._sensor][0]
        self._icon = SENSOR_TYPES[self._sensor][1]
        self._unit_of_measurement = SENSOR_TYPES[self._sensor][3]
        self._smappe_name = SENSOR_TYPES[self._sensor][4]

    @property
    def name(self):
        """Return the name of the sensor."""
        if self._location_id:
            location_name = self._smappee.locations[self._location_id]
        else:
            location_name = 'Local'

        return "{} {} {}".format(SENSOR_PREFIX,
                                 location_name,
                                 self._name)

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        if self._location_id:
            attr['Location Id'] = self._location_id
            attr['Location Name'] = self._smappee.locations[self._location_id]
        return attr

    def update(self):
        """Get the latest data from Smappee and update the state."""
        self._smappee.update()

        # if self._sensor in ['alwayson_today', 'solar_today', 'power_today']:
        #     data = self._smappee.consumption[self._location_id]
        #     if data:
        #         consumption = data.get('consumptions')[-1]
        #         _LOGGER.debug("%s %s", self._sensor, consumption)
        #         value = consumption.get(self._smappe_name)
        #         self._state = round(value / 1000, 2)
        if self._sensor in ['solar_today', 'power_today']:
            data = self._smappee.consumption[self._location_id]
            if data:
                try:
                    consumption = data.get('consumptions')[-1]
                    _LOGGER.debug("%s %s", self._sensor, consumption)
                    value = consumption.get(self._smappe_name)
                    self._state = round(value / 1000, 2)
                except IndexError:
                    self._state = 0
        elif self._sensor == 'alwayson_today':
            data = self._smappee.get_consumption(
                self._location_id, aggregation=1, delta=30)
            _LOGGER.debug("%s %s", self._sensor, data)
            if data:
                consumption = data.get('consumptions')[-1]
                self._state = consumption.get(self._smappe_name)
        elif self._sensor == 'active_cosfi':
            cosfi = self._smappee.active_cosfi()
            _LOGGER.debug("%s %s", self._sensor, cosfi)
            if cosfi:
                self._state = round(cosfi, 2)
        elif self._sensor == 'current':
            current = self._smappee.active_current()
            _LOGGER.debug("%s %s", self._sensor, current)
            if current:
                self._state = round(current, 2)
        elif self._sensor == 'voltage':
            voltage = self._smappee.active_voltage()
            _LOGGER.debug("%s %s", self._sensor, voltage)
            if voltage:
                self._state = round(voltage, 3)
        elif self._sensor == 'active_power':
            data = self._smappee.instantaneous
            _LOGGER.debug("%s %s", self._sensor, data)
            if data:
                value1 = [float(i['value']) for i in data
                          if i['key'].endswith('phase0ActivePower')]
                value2 = [float(i['value']) for i in data
                          if i['key'].endswith('phase1ActivePower')]
                value3 = [float(i['value']) for i in data
                          if i['key'].endswith('phase2ActivePower')]
                active_power = sum(value1 + value2 + value3) / 1000
                if active_power < 0:
                    active_power = 0
                self._state = round(active_power, 2)
        elif self._sensor == 'solar':
            data = self._smappee.instantaneous
            _LOGGER.debug("%s %s", self._sensor, data)
            if data:
                value1 = [float(i['value']) for i in data
                          if i['key'].endswith('phase3ActivePower')]
                value2 = [float(i['value']) for i in data
                          if i['key'].endswith('phase4ActivePower')]
                value3 = [float(i['value']) for i in data
                          if i['key'].endswith('phase5ActivePower')]
                power = sum(value1 + value2 + value3) / 1000
                if power < 0:
                    power = 0
                self._state = round(power, 2)
