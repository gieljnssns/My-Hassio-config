"""Support for Tahoma sensors."""
import logging
from datetime import timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.components.tahoma import (
    DOMAIN as TAHOMA_DOMAIN, TahomaDevice)
from homeassistant.const import ATTR_BATTERY_LEVEL

DEPENDENCIES = ['tahoma']

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)

ATTR_RSSI_LEVEL = 'rssi_level'


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Tahoma controller devices."""
    controller = hass.data[TAHOMA_DOMAIN]['controller']
    devices = [
        TahomaSensor(device, controller)
        for device in hass.data[TAHOMA_DOMAIN]['devices']['sensor']
    ]

    add_entities(devices, True)


class TahomaSensor(TahomaDevice, Entity):
    """Representation of a Tahoma Sensor."""

    def __init__(self, tahoma_device, controller):
        """Initialize the sensor."""
        self.current_value = None
        self._available = False
        super().__init__(tahoma_device, controller)

    @property
    def state(self):
        """Return the name of the sensor."""
        return self.current_value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self.tahoma_device.type == 'Temperature Sensor':
            return None
        if self.tahoma_device.type == 'io:SomfyContactIOSystemSensor':
            return None
        if self.tahoma_device.type == 'io:LightIOSystemSensor':
            return 'lx'
        if self.tahoma_device.type == 'Humidity Sensor':
            return '%'
        if self.tahoma_device.type == 'rtds:RTDSContactSensor':
            return None
        if self.tahoma_device.type == 'rtds:RTDSMotionSensor':
            return None

    def update(self):
        """Update the state."""
        self.controller.get_states([self.tahoma_device])
        if self.tahoma_device.type == 'io:LightIOSystemSensor':
            self.current_value = self.tahoma_device.active_states[
                'core:LuminanceState']
            self._available = bool(self.tahoma_device.active_states.get(
                'core:StatusState') == 'available')
        elif self.tahoma_device.type == 'io:SomfyContactIOSystemSensor':
            self.current_value = self.tahoma_device.active_states[
                'core:ContactState']
            self._available = bool(self.tahoma_device.active_states.get(
                'core:StatusState') == 'available')
        elif self.tahoma_device.type == 'rtds:RTDSContactSensor':
            self.current_value = self.tahoma_device.active_states[
                'core:ContactState']
            self._available = True
        elif self.tahoma_device.type == 'rtds:RTDSMotionSensor':
            self.current_value = self.tahoma_device.active_states[
                'core:OccupancyState']
            self._available = True

        _LOGGER.debug("Update %s, value: %d", self._name, self.current_value)

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attr = {}
        super_attr = super().device_state_attributes
        if super_attr is not None:
            attr.update(super_attr)

        if 'core:RSSILevelState' in self.tahoma_device.active_states:
            attr[ATTR_RSSI_LEVEL] = \
                self.tahoma_device.active_states['core:RSSILevelState']
        if 'core:SensorDefectState' in self.tahoma_device.active_states:
            attr[ATTR_BATTERY_LEVEL] = \
                self.tahoma_device.active_states['core:SensorDefectState']
        return attr

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available
