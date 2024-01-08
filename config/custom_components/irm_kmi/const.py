"""Constants for the IRM KMI integration."""
from typing import Final

from homeassistant.components.weather import (ATTR_CONDITION_CLEAR_NIGHT,
                                              ATTR_CONDITION_CLOUDY,
                                              ATTR_CONDITION_EXCEPTIONAL,
                                              ATTR_CONDITION_FOG,
                                              ATTR_CONDITION_LIGHTNING_RAINY,
                                              ATTR_CONDITION_PARTLYCLOUDY,
                                              ATTR_CONDITION_POURING,
                                              ATTR_CONDITION_RAINY,
                                              ATTR_CONDITION_SNOWY,
                                              ATTR_CONDITION_SNOWY_RAINY,
                                              ATTR_CONDITION_SUNNY)
from homeassistant.const import Platform

DOMAIN: Final = 'irm_kmi'
PLATFORMS: Final = [Platform.WEATHER, Platform.CAMERA]
CONFIG_FLOW_VERSION = 3

OUT_OF_BENELUX: Final = ["außerhalb der Benelux (Brussels)",
                         "Hors de Belgique (Bxl)",
                         "Outside the Benelux (Brussels)",
                         "Buiten de Benelux (Brussel)"]
LANGS: Final = ['en', 'fr', 'nl', 'de']

OPTION_STYLE_STD: Final = 'standard_style'
OPTION_STYLE_CONTRAST: Final = 'contrast_style'
OPTION_STYLE_YELLOW_RED: Final = 'yellow_red_style'
OPTION_STYLE_SATELLITE: Final = 'satellite_style'
CONF_STYLE: Final = "style"

CONF_STYLE_OPTIONS: Final = [
    OPTION_STYLE_STD,
    OPTION_STYLE_CONTRAST,
    OPTION_STYLE_YELLOW_RED,
    OPTION_STYLE_SATELLITE
]

CONF_DARK_MODE: Final = "dark_mode"

STYLE_TO_PARAM_MAP: Final = {
    OPTION_STYLE_STD: 1,
    OPTION_STYLE_CONTRAST: 2,
    OPTION_STYLE_YELLOW_RED: 3,
    OPTION_STYLE_SATELLITE: 4
}

CONF_USE_DEPRECATED_FORECAST: Final = 'use_deprecated_forecast_attribute'
OPTION_DEPRECATED_FORECAST_NOT_USED: Final = 'do_not_use_deprecated_forecast'
OPTION_DEPRECATED_FORECAST_DAILY: Final = 'daily_in_deprecated_forecast'
OPTION_DEPRECATED_FORECAST_HOURLY: Final = 'hourly_in_use_deprecated_forecast'

CONF_USE_DEPRECATED_FORECAST_OPTIONS: Final = [
    OPTION_DEPRECATED_FORECAST_NOT_USED,
    OPTION_DEPRECATED_FORECAST_DAILY,
    OPTION_DEPRECATED_FORECAST_HOURLY
]

# map ('ww', 'dayNight') tuple from IRM KMI to HA conditions
IRM_KMI_TO_HA_CONDITION_MAP: Final = {
    (0, 'd'): ATTR_CONDITION_SUNNY,
    (0, 'n'): ATTR_CONDITION_CLEAR_NIGHT,
    (1, 'd'): ATTR_CONDITION_SUNNY,
    (1, 'n'): ATTR_CONDITION_CLEAR_NIGHT,
    (2, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (2, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (3, 'd'): ATTR_CONDITION_PARTLYCLOUDY,
    (3, 'n'): ATTR_CONDITION_PARTLYCLOUDY,
    (4, 'd'): ATTR_CONDITION_POURING,
    (4, 'n'): ATTR_CONDITION_POURING,
    (5, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (5, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (6, 'd'): ATTR_CONDITION_POURING,
    (6, 'n'): ATTR_CONDITION_POURING,
    (7, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (7, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (8, 'd'): ATTR_CONDITION_SNOWY_RAINY,
    (8, 'n'): ATTR_CONDITION_SNOWY_RAINY,
    (9, 'd'): ATTR_CONDITION_SNOWY_RAINY,
    (9, 'n'): ATTR_CONDITION_SNOWY_RAINY,
    (10, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (10, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (11, 'd'): ATTR_CONDITION_SNOWY,
    (11, 'n'): ATTR_CONDITION_SNOWY,
    (12, 'd'): ATTR_CONDITION_SNOWY,
    (12, 'n'): ATTR_CONDITION_SNOWY,
    (13, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (13, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (14, 'd'): ATTR_CONDITION_CLOUDY,
    (14, 'n'): ATTR_CONDITION_CLOUDY,
    (15, 'd'): ATTR_CONDITION_CLOUDY,
    (15, 'n'): ATTR_CONDITION_CLOUDY,
    (16, 'd'): ATTR_CONDITION_POURING,
    (16, 'n'): ATTR_CONDITION_POURING,
    (17, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (17, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (18, 'd'): ATTR_CONDITION_RAINY,
    (18, 'n'): ATTR_CONDITION_RAINY,
    (19, 'd'): ATTR_CONDITION_POURING,
    (19, 'n'): ATTR_CONDITION_POURING,
    (20, 'd'): ATTR_CONDITION_SNOWY_RAINY,
    (20, 'n'): ATTR_CONDITION_SNOWY_RAINY,
    (21, 'd'): ATTR_CONDITION_EXCEPTIONAL,
    (21, 'n'): ATTR_CONDITION_EXCEPTIONAL,
    (22, 'd'): ATTR_CONDITION_SNOWY,
    (22, 'n'): ATTR_CONDITION_SNOWY,
    (23, 'd'): ATTR_CONDITION_SNOWY,
    (23, 'n'): ATTR_CONDITION_SNOWY,
    (24, 'd'): ATTR_CONDITION_FOG,
    (24, 'n'): ATTR_CONDITION_FOG,
    (25, 'd'): ATTR_CONDITION_FOG,
    (25, 'n'): ATTR_CONDITION_FOG,
    (26, 'd'): ATTR_CONDITION_FOG,
    (26, 'n'): ATTR_CONDITION_FOG,
    (27, 'd'): ATTR_CONDITION_EXCEPTIONAL,
    (27, 'n'): ATTR_CONDITION_EXCEPTIONAL
}
