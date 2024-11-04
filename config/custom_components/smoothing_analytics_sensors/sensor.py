import logging

from .const import (
    DEFAULT_EMA_DESIRED_TIME_TO_95,
    DEFAULT_LOW_PASS,
    DEFAULT_MEDIAN_SIZE,
    DOMAIN,
)
from .custom_sensors.ema_sensor import EmaSensor
from .custom_sensors.lowpass_sensor import LowpassSensor
from .custom_sensors.median_sensor import MedianSensor
from .utils.misc import get_config_value, generate_md5_hash

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Smoothing Analytics sensors from a config entry."""
    config = config_entry.data

    # Extract configuration parameters
    input_sensor = config.get("input_sensor")

    lowpass_time_constant = get_config_value(
        config_entry, "lowpass_time_constant", DEFAULT_LOW_PASS
    )

    median_sampling_size = get_config_value(
        config_entry, "median_sampling_size", DEFAULT_MEDIAN_SIZE
    )

    desired_time_to_95 = get_config_value(
        config_entry, "desired_time_to_95", DEFAULT_EMA_DESIRED_TIME_TO_95
    )

    # Generate a unique hash based on the input sensor
    sensor_hash = generate_md5_hash(input_sensor)

    # Unique input IDs for median and EMA sensors for stacking purposes
    median_unique_id = f"sas_lowpass_{sensor_hash}"
    ema_unique_id = f"sas_median_{sensor_hash}"

    # Create the lowpass from the input sensor
    lowpass_sensor = LowpassSensor(
        input_sensor, lowpass_time_constant, sensor_hash, config_entry
    )

    # Create the median, and ema sensors using the unique IDs
    median_sensor = MedianSensor(
        median_unique_id, median_sampling_size, sensor_hash, config_entry
    )

    ema_sensor = EmaSensor(
        ema_unique_id, desired_time_to_95, sensor_hash, config_entry
    )

    # Add sensors to Home Assistant
    async_add_entities([lowpass_sensor, median_sensor, ema_sensor])

    # Store reference to the platform to handle unloads later
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][config_entry.entry_id] = async_add_entities


async def async_unload_entry(hass, entry):
    """Handle unloading of an entry."""
    platform = hass.data[DOMAIN].get(entry.entry_id)
    if platform:
        return await platform.async_remove_entry(entry)
    return False
