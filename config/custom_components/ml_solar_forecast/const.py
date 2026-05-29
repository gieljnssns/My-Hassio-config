"""Constants and configuration for the Machine Learning Solar Forecast integration."""

import logging

# Integration metadata
DOMAIN = "ml_solar_forecast"
NAME = "Machine Learning Solar Forecast"
VERSION = "0.0.0.dev0"

# Service names
SERVICE_NAME_GET_FORECAST = "get_forecast"
SERVICE_DATA_START = "start"
SERVICE_DATA_END = "end"

# Configuration keys
CONF_LOCATION = "location"
CONF_PRODUCTION_ENTITY = "production_entity"
CONF_TRAINING_DAYS = "training_days"
CONF_MAX_INVERTER_POWER_W = "max_inverter_power_w"
CONF_OPENMETEO_API_KEY = "openmeteo_api_key"
CONF_OPENMETEO_WEATHER_MODELS = "openmeteo_weather_models"
CONF_APP_HOSTNAME = "app_hostname"
CONF_INFLUX_HOST = "influx_host"
CONF_INFLUX_ENTITY = "influx_entity"
CONF_INFLUX_PORT = "influx_port"
CONF_INFLUX_DB = "influx_db"
CONF_INFLUX_USER = "influx_user"
CONF_INFLUX_PASS = "influx_pass"
CONF_USE_INFLUX = "use_influx"

# Defaults
DEFAULT_TRAINING_DAYS = 180
DEFAULT_APP_HOSTNAME = "http://localhost:14760"
DEFAULT_INFLUX_HOST = "localhost"
MIN_TRAINING_DAYS = 30
MIN_POWER_THRESHOLD_W = 15

# # OpenMeteo API settings
# OPENMETEO_HISTORY_CUTOFF_DAYS = 60
# OPENMETEO_MAX_RANGE_DAYS = 90
# OPENMETEO_HORIZON_REVALIDATION_HOURS = 6

# Update intervals
UPDATE_INTERVAL_MINUTES = 60

# Logging
log = logging.getLogger(__package__)
