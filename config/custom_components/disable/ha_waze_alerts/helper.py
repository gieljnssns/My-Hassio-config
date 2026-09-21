"""Helper for Waze alerts."""

import logging
from math import cos, radians

_LOGGER = logging.getLogger(__name__)


def calculate_bounding_box(latitude, longitude, radius):
    # Haversine-formule voor een bounding box
    radius_km = radius / 1000
    lat_diff = radius_km / 111  # 111 km per graad latitude
    lon_diff = radius_km / (111 * cos(radians(latitude)))
    top = latitude + lat_diff
    bottom = latitude - lat_diff
    left = longitude - lon_diff
    right = longitude + lon_diff
    return top, bottom, left, right
