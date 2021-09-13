"""Support for Solar inverter Modbus."""
from typing import Any, Union

import logging

import voluptuous as vol

from homeassistant.components.sensor import (
    DEVICE_CLASSES_SCHEMA as SENSOR_DEVICE_CLASSES_SCHEMA,
)

from homeassistant.const import (
    # ATTR_STATE,
    CONF_ADDRESS,
    CONF_DELAY,
    CONF_DEVICE_CLASS,
    CONF_HOST,
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    CONF_OFFSET,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE,
    CONF_STRUCTURE,
    CONF_TIMEOUT,
    # CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
)
import homeassistant.helpers.config_validation as cv

from .const import (
    # ATTR_ADDRESS,
    # ATTR_HUB,
    # ATTR_UNIT,
    # ATTR_VALUE,
    CALL_TYPE_REGISTER_HOLDING,
    CALL_TYPE_REGISTER_INPUT,
    CONF_BRAND,
    CONF_COUNT,
    CONF_DATA_TYPE,
    CONF_INPUT_TYPE,
    CONF_PRECISION,
    CONF_REVERSE_ORDER,
    CONF_SCALE,
    CONF_SENSORS,
    DATA_TYPE_CUSTOM,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_STRING,
    DATA_TYPE_UINT,
    DEFAULT_HUB,
    DEFAULT_SCAN_INTERVAL,
    SOLAR_INVERTER_MODBUS_DOMAIN as DOMAIN,
)

from .huawei_const import HUAWEI_SENSORS

from .solaredge_const import SOLAREDGE_SENSORS

SENSORS = HUAWEI_SENSORS.copy()
SENSORS.update(SOLAREDGE_SENSORS)

from .modbus import modbus_setup

BASE_SCHEMA = vol.Schema({vol.Optional(CONF_NAME, default=DEFAULT_HUB): cv.string})


def number(value: Any) -> Union[int, float]:
    """Coerce a value to number without losing precision."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value

    try:
        value = int(value)
        return value
    except (TypeError, ValueError):
        pass
    try:
        value = float(value)
        return value
    except (TypeError, ValueError) as err:
        raise vol.Invalid(f"invalid number {value}") from err


BASE_COMPONENT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_SLAVE): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL): cv.positive_int,
    }
)


SENSOR_SCHEMA = BASE_COMPONENT_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESS): cv.positive_int,
        vol.Optional(CONF_COUNT, default=1): cv.positive_int,
        vol.Optional(CONF_DATA_TYPE, default=DATA_TYPE_INT): vol.In(
            [
                DATA_TYPE_INT,
                DATA_TYPE_UINT,
                DATA_TYPE_FLOAT,
                DATA_TYPE_STRING,
                DATA_TYPE_CUSTOM,
            ]
        ),
        vol.Optional(CONF_DEVICE_CLASS): SENSOR_DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_OFFSET, default=0): number,
        vol.Optional(CONF_PRECISION, default=0): cv.positive_int,
        vol.Optional(CONF_INPUT_TYPE, default=CALL_TYPE_REGISTER_HOLDING): vol.In(
            [CALL_TYPE_REGISTER_HOLDING, CALL_TYPE_REGISTER_INPUT]
        ),
        vol.Optional(CONF_REVERSE_ORDER, default=False): cv.boolean,
        vol.Optional(CONF_SCALE, default=1): number,
        vol.Optional(CONF_STRUCTURE): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
    }
)

MODBUS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_HUB): cv.string,
        vol.Optional(CONF_TIMEOUT, default=3): cv.socket_timeout,
        vol.Optional(CONF_SLAVE): cv.positive_int,
        vol.Optional(CONF_DELAY, default=0): cv.positive_int,
        vol.Optional(CONF_SENSORS): vol.All(cv.ensure_list, [SENSOR_SCHEMA]),
        vol.Optional(CONF_MONITORED_CONDITIONS): vol.All(
            cv.ensure_list, [vol.In(SENSORS)]
        ),
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): cv.positive_int,
    }
)

ETHERNET_SCHEMA = MODBUS_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.port,
        vol.Required(CONF_BRAND): vol.Any("huawei", "solaredge"),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Any(ETHERNET_SCHEMA),
            ],
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Set up Modbus component."""
    return modbus_setup(
        hass,
        config,
    )
