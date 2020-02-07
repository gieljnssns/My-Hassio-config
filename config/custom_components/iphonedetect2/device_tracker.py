"""
From : https://community.home-assistant.io/t/iphone-device-tracker-on-linux/13698
Tracks iPhones by sending a udp message to port 5353.
An entry in the arp cache is then made and checked.

device_tracker:
  - platform: iphonedetect
    hosts:
      host_one: 192.168.2.12
      host_two: 192.168.2.25
"""
import logging
import subprocess
import sys
import re
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.device_tracker import (
    PLATFORM_SCHEMA)
from homeassistant.components.device_tracker.const import (
    CONF_SCAN_INTERVAL, SCAN_INTERVAL, SOURCE_TYPE_ROUTER)

from homeassistant import util
from homeassistant import const

import socket

__version__ = '1.2.1'

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(const.CONF_HOSTS): {cv.string: cv.string},
})


class Host:
    """Host object with arp detection."""

    def __init__(self, ip_address, dev_id, hass, config):
        """Initialize the Host."""
        self.hass = hass
        self.ip_address = ip_address
        self.dev_id = dev_id

    def detectiphone(self):
        """Send udp message to port 5353 
           and return True if an arp chache entry is made success.
        """
        aSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        aSocket.settimeout(1)
        addr = (self.ip_address, 5353)
        message = b'Steve Jobs'
        aSocket.sendto(message, addr)

        try:
            output = subprocess.check_output('ip neigh show to ' + self.ip_address, shell=True)
            _LOGGER.debug("ip n output for %s is %s", self.ip_address, output.decode('utf-8'))
        except subprocess.CalledProcessError:
            _LOGGER.error("Could not send ip n command")
            try:
                output = subprocess.check_output('arp -na|grep ' + self.ip_address, shell=True)
                _LOGGER.debug("arp output for %s is %s", self.ip_address, output.decode('utf-8'))
            except subprocess.CalledProcessError:
                _LOGGER.fatal("Could not send arp command")
                return False
        finally:
            mac = re.compile(r'(?:[0-9a-fA-F]:?){12}')
            output = output.decode('utf-8')
            if re.findall(mac, output):
                _LOGGER.info("Device %s (%s) is HOME", self.dev_id, self.ip_address)
                return True
            else:
                _LOGGER.info("Device %s (%s) is AWAY", self.dev_id, self.ip_address)
                return False
        # try:
        #     output = subprocess.check_output('ip n|grep '+self.ip_address, shell=True)
        #     output = output.decode('utf-8').split(' ')
        #     if len(output[4].split(':')) == 6:
        #         return True
        # except subprocess.CalledProcessError:
        #     try:
        #         output = subprocess.check_output('arp -na|grep '+self.ip_address, shell=True)
        #         output = output.decode('utf-8').split(' ')
        #         if len(output[3].split(':')) == 6:
        #             return True
        #     except subprocess.CalledProcessError as error:
        #         _LOGGER.fatal("Could not send command, got %s", error)
        #         return False


    def update(self, see):
        """Update device state by sending one or more ping messages."""
        if self.detectiphone():
            see(dev_id=self.dev_id, source_type=SOURCE_TYPE_ROUTER)
            return True

def setup_scanner(hass, config, see, discovery_info=None):
    """Set up the Host objects and return the update function."""
    hosts = [Host(ip, dev_id, hass, config) for (dev_id, ip) in
             config[const.CONF_HOSTS].items()]
    interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)

    _LOGGER.debug("Started iphonedetect2 with interval=%s on hosts: %s",
                  interval, ",".join([host.ip_address for host in hosts]))
    
    def update_interval(now):
        """Update all the hosts on every interval time."""
        try:
            for host in hosts:
                host.update(see)
        finally:
            hass.helpers.event.track_point_in_utc_time(
                update_interval, util.dt.utcnow() + interval)

    update_interval(None)
    return True
