"""Constants for ha-waze-alerts."""

from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)
PLATFORMS = [Platform.GEO_LOCATION, Platform.SENSOR, Platform.SWITCH]
DOMAIN = "ha_waze_alerts"
BASE_URL = "https://www.waze.com/live-map/api/georss"
DEFAULT_RADIUS = 2500  # in meters
DEFAULT_CATEGORY = "POLICE"
CONF_CATEGORY = "category"
CATEGORIES = [
    "ACCIDENT",
    "JAM",
    "POLICE",
    "WEATHERHAZARD",
    "HAZARD",
    "CONSTRUCTION",
    "ROAD_CLOSED",
]
