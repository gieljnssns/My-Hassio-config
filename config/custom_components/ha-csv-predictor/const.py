"""Constants for HA CSV Predictor."""
# Base component constants
NAME = "HA CSV Predictor"
DOMAIN = "ha_csv_predictor"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.0"

ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/gieljnssns/ha-csv-predictor/issues"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
# BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
# BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
# SWITCH = "switch"
# PLATFORMS = [BINARY_SENSOR, SENSOR, SWITCH]
PLATFORMS = [SENSOR]

# Configuration and options
CONF_ENABLED = "enabled"
CONF_CSV_PATH = "csv_path"
CONF_DATA = "data"
CONF_TARGET_VARIABLE = "target_variable"
CONF_INDEPENDENT_VARIABLES = "independent_variables"
CONF_DEPENDENT_VARIABLE = "dependent_variable"
CONF_NEW_VARIABLES = "new_variables"

SERVICE_PREDICT = "predict"

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
