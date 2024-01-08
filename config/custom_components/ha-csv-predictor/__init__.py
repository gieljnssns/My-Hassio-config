"""Custom integration to integrate HA CSV Predictor with Home Assistant.

For more details about this integration, please refer to
https://github.com/gieljnssns/ha-csv-predictor
"""
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform,
)
from homeassistant.core import Config, HomeAssistant
from homeassistant.helpers import config_validation as cv

# from homeassistant.helpers.aiohttp_client import async_get_clientsession
# from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
# from homeassistant.helpers.update_coordinator import UpdateFailed
# from .api import HaCsvPredictorApiClient
# from .const import CONF_PASSWORD
# from .const import CONF_USERNAME
from .const import CONF_DEPENDENT_VARIABLE

SERVICE_PREDICT_SCHEMA = vol.Schema({vol.Required(CONF_DEPENDENT_VARIABLE): cv.string})

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)

PLATFORMS = [Platform.SENSOR]


# async def async_setup(hass: HomeAssistant, config: Config):
#     """Set up this integration using YAML is not supported."""
#     return True


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    # print("init async_setup_entry")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

    # entry.async_on_unload(entry.add_update_listener(async_update_entry))
    # return True
    # if DOMAIN not in hass.data:
    #     hass.data[DOMAIN] = {}
    # hass.data.setdefault(DOMAIN, {})
    # hass.data[DOMAIN][entry.entry_id] = coordinator = BlueprintDataUpdateCoordinator(
    #     hass=hass,
    #     client=IntegrationBlueprintApiClient(
    #         username=entry.data[CONF_USERNAME],
    #         password=entry.data[CONF_PASSWORD],
    #         session=async_get_clientsession(hass),
    #     ),
    # )
    # # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    # await coordinator.async_config_entry_first_refresh()

    # await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # entry.async_on_unload(entry.add_update_listener(async_reload_entry))


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update a given config entry."""
    # print("init async_update_entry")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # print("init async_unload_entry")
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return ok

    # @callback
    # def register_entity_services() -> None:
    #     """Register the different entity services."""
    #     print("init register_entity_services")
    #     platform = entity_platform.async_get_current_platform()
    #     platform.async_register_entity_service(
    #         SERVICE_PREDICT,
    #         {vol.Required(CONF_INDEPENDENT_VARIABLES): validate_is_number},  # type: ignore
    #         "predict",
    #     )

    # async def predict(call: ServiceCall) -> None:
    #     """Service call to add a new filter subscription to AdGuard Home."""
    #     await adguard.filtering.add_url(
    #         allowlist=False, name=call.data[CONF_NAME], url=call.data[CONF_URL]
    #     )

    # hass.services.async_register(
    #     DOMAIN, SERVICE_PREDICT, predict, schema=SERVICE_PREDICT_SCHEMA
    # )

    # return True


# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Handle removal of an entry."""
#     if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
#         hass.data[DOMAIN].pop(entry.entry_id)
#     return unloaded


# async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
#     """Reload config entry."""
#     await async_unload_entry(hass, entry)
#     await async_setup_entry(hass, entry)

# async def async_setup(hass: HomeAssistant, config: Config):
#     """Set up this integration using YAML is not supported."""
#     return True

# def _get_full_path(hass: HomeAssistant, path: str) -> str:
#     """Check if path is valid, allowed and return full path."""
#     print("get full path")
#     get_path = pathlib.Path(path)
#     if not get_path.exists() or not get_path.is_file():
#         raise ConfigEntryNotReady(f"Can not access file {path}")

#     if not hass.config.is_allowed_path(path):
#         raise ConfigEntryNotReady(f"Filepath {path} is not valid or allowed")

#     return str(get_path.absolute())


# async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
#     """Set up this integration using UI."""
#     print("async_setup_entry")
#     if hass.data.get(DOMAIN) is None:
#         hass.data.setdefault(DOMAIN, {})
#         _LOGGER.info(STARTUP_MESSAGE)

#     full_path = await hass.async_add_executor_job(
#         _get_full_path, hass, entry.data[CONF_FILE_PATH]
#     )
#     coordinator = FileSizeCoordinator(hass, full_path)
#     await coordinator.async_config_entry_first_refresh()

#     await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
#     return True


# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Unload a config entry."""
#     return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
