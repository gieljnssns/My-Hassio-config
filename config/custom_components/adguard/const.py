"""Constants for the AdGuard Home integration."""
import logging

DOMAIN = "adguard"

LOGGER = logging.getLogger(__package__)

DATA_ADGUARD_CLIENT = "adguard_client"
DATA_ADGUARD_VERSION = "adguard_version"

CONF_FORCE = "force"
CONF_LIST_TYPE = "list_type"

LIST_TYPES = ["blocklist", "allowlist"]

SERVICE_ADD_URL = "add_url"
SERVICE_DISABLE_URL = "disable_url"
SERVICE_ENABLE_URL = "enable_url"
SERVICE_REFRESH = "refresh"
SERVICE_REMOVE_URL = "remove_url"
