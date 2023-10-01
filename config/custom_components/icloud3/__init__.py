"""GitHub Custom Component."""
import asyncio

# from homeassistant.components import history
# from homeassistant.const import CONF_DOMAINS, CONF_ENTITIES, CONF_EXCLUDE, CONF_INCLUDE


from homeassistant.config_entries   import ConfigEntry
from homeassistant.const            import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from homeassistant.core             import HomeAssistant
from homeassistant.helpers.typing   import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import homeassistant.util.location  as ha_location_info
import os
import logging


from .const import (DOMAIN, PLATFORMS, ICLOUD3, MODE_PLATFORM, MODE_INTEGRATION, CONF_VERSION,
                    CONF_SETUP_ICLOUD_SESSION_EARLY, CONF_EVLOG_BTNCONFIG_URL,
                    SENSOR_EVENT_LOG_NAME, SENSOR_WAZEHIST_TRACK_NAME,
                    EVLOG_IC3_STARTING, VERSION, )

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

# from .const_sensor import (HA_EXCLUDE_SENSORS, )

from .global_variables              import GlobalVariables as Gb
from .helpers.messaging             import (_trace, _traceha, open_ic3_log_file,
                                            post_alert, post_startup_alert,
                                            log_info_msg, log_debug_msg, log_error_msg, log_exception)
from .support.v2v3_config_migration import iCloud3_v2v3ConfigMigration
from .support                       import start_ic3
from .support                       import config_file
from .support                       import restore_state
from .support.service_handler       import register_icloud3_services
from .support                       import pyicloud_ic3_interface
from .support                       import event_log
from .support                       import recorder_prefilter
from .icloud3_main                  import iCloud3
from .                              import config_flow

_HA_LOGGER = logging.getLogger(__name__)
Gb.HALogger = _LOGGER = logging.getLogger('icloud3')

successful_startup = True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
#
#   PLATFORM MODE - STARTED FROM CONFIGURATION.YAML 'DEVICE_TRACKER/PLATFORM: ICLOUD3 STATEMENT
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Old way of setting up the iCloud tracker with platform: icloud3 statement."""
    hass.data.setdefault(DOMAIN, {})
    Gb.hass   = hass
    Gb.config = config

    try:
        device_trackers = config.get('device_tracker')
        if device_trackers:
            for tracker in device_trackers:
                if tracker['platform'] == DOMAIN:
                    Gb.ha_config_platform_stmt = True
                    Gb.operating_mode = MODE_PLATFORM

                    # Initialize the config/.storage/icloud3/configuration file before the config_glow
                    # has set up the integration
                    start_ic3.initialize_directory_filenames()
                    config_file.load_storage_icloud3_configuration_file()

                    if Gb.conf_profile[CONF_VERSION] == 1:
                        _HA_LOGGER.info(f"Initializing iCloud3 {VERSION} - Remove Platform: iCloud3 statement")

    except Exception as err:
        log_exception(err)


    return True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SETUP PROCESS TO START ICLOUD3
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def start_icloud3(event=None):
    Gb.initial_icloud3_loading_flag = True
    log_debug_msg('START iCloud3 Initial Load Executor Job (iCloud3.start_icloud3)')
    icloud3_started = await Gb.hass.async_add_executor_job(Gb.iCloud3.start_icloud3)

    if icloud3_started:
        log_info_msg(f"iCloud3 {Gb.version} started")
    else:
        log_error_msg(f"iCloud3 {Gb.version} Initialization Failed")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
#
#   INTEGRATION MODE - STARTED FROM CONFIGURATION > INTEGRATIONS ENTRY
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """ Set up the iCloud3 integration from a ConfigEntry integration """

    try:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.unique_id] = DOMAIN
        if entry.unique_id is None:
            hass.config_entries.async_update_entry(entry, unique_id=DOMAIN)
        hass_data = dict(entry.data)

        # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
        # unsub_options_update_listener = entry.add_update_listener(options_update_listener)
        # hass_data["unsub_options_update_listener"] = unsub_options_update_listener
        # hass.data[DOMAIN][entry.entry_id] = hass_data

        Gb.hass           = hass
        Gb.config_entry   = entry
        Gb.entry_id       = entry.entry_id
        Gb.operating_mode = MODE_INTEGRATION

        if Gb.restart_ha_flag:
            log_error_msg("iCloud3 > Waiting for HA restart to remove legacy devices before continuing")
            return False

        await async_get_ha_location_info(hass)

        Gb.PyiCloud = None

        recorder_prefilter.add_filter(hass, [SENSOR_EVENT_LOG_NAME, SENSOR_WAZEHIST_TRACK_NAME])
        start_ic3.initialize_directory_filenames()
        config_file.load_storage_icloud3_configuration_file()
        start_ic3.set_log_level(Gb.log_level)
        open_ic3_log_file(new_log_file=Gb.log_debug_flag)
        # config_file.count_lines_of_code(Gb.icloud3_directory)

        Gb.evlog_btnconfig_url = Gb.conf_profile[CONF_EVLOG_BTNCONFIG_URL].strip()
        Gb.evlog_version       = Gb.conf_profile['event_log_version']
        Gb.EvLog = event_log.EventLog(Gb.hass)
        log_info_msg(f"Setting up iCloud3 {VERSION} - Using Integration method")

        Gb.start_icloud3_inprocess_flag = True

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try:
            # _traceha(f"{Gb.hass.data.keys()=}")

            pass

        except Exception as err:
            log_exception(err)
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        start_ic3.initialize_icloud_data_source()
        restore_state.load_storage_icloud3_restore_state_file()

        # Create  device_tracker entities
        if Gb.conf_devices != []:
            await hass.config_entries.async_forward_entry_setups(entry, ['device_tracker'])

        # Create sensor entities
        await hass.config_entries.async_forward_entry_setups(entry, ['sensor'])

        # Do not start if loading/initialization failed
        if successful_startup is False:
            log_error_msg(f"iCloud3 Initialization Failed, configuration file "
                            f"{Gb.icloud3_config_filename} failed to load.")
            log_error_msg("Verify the configuration file and delete it manually if necessary")
            return False

        # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
        unsub_options_update_listener = entry.add_update_listener(options_update_listener)
        hass_data["unsub_options_update_listener"] = unsub_options_update_listener
        hass.data[DOMAIN][entry.entry_id] = hass_data

    except Exception as err:
        log_exception(err)
        return False

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    #   SETUP PROCESS TO START ICLOUD3
    #
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    Gb.EvLog.display_user_message('iCloud3 is Starting')
    Gb.EvLog.post_event(f"{EVLOG_IC3_STARTING}Initializing iCloud3 v{Gb.version} > "
                        f"{dt_util.now().strftime('%A, %b %d')}")

    Gb.iCloud3  = iCloud3()

    # These will run concurrently while HA is starting everything else
    Gb.EvLog.post_event('Start HA Startup/Stop Listeners')
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_ic3.ha_startup_completed)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, start_ic3.ha_stopping)

    Gb.EvLog.post_event('Start iCloud3 Services Executor Job')
    hass.async_add_executor_job(register_icloud3_services)
    # hass.async_add_executor_job(service_handler.register_icloud3_services)

    if (Gb.primary_data_source_ICLOUD and Gb.conf_tracking[CONF_SETUP_ICLOUD_SESSION_EARLY]):
        Gb.EvLog.post_event('Start iCloud Account Session Executor Job')
        hass.async_add_executor_job(pyicloud_ic3_interface.create_PyiCloudService_executor_job)

    Gb.initial_icloud3_loading_flag = True
    log_debug_msg('START iCloud3 Initial Load Executor Job (iCloud3.start_icloud3)')

    icloud3_started = await Gb.hass.async_add_executor_job(Gb.iCloud3.start_icloud3)

    if icloud3_started:
        log_info_msg(f"iCloud3 {Gb.version} started")
    else:
        log_error_msg(f"iCloud3 {Gb.version} Initialization Failed")

    return True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)

#-------------------------------------------------------------------------------------------
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, "sensor")]))

    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

#-------------------------------------------------------------------------------------------
async def async_get_ha_location_info(hass):
    if location_info := await ha_location_info.async_detect_location_info(
            async_get_clientsession(hass)):

        Gb.ha_location_info = {
            "country_code": location_info.country_code,
            "region_code": location_info.region_code,
            "zip_code": location_info.zip_code,
            "region_name": location_info.region_name,
            "city": location_info.city,
            "time_zone": location_info.time_zone,
            "latitude": location_info.latitude,
            "longitude": location_info.longitude,
            "use_metric": location_info.use_metric,
        }

        try:
            Gb.country_code = Gb.ha_location_info.country_code.lower()
            Gb.use_metric   = Gb.ha_location_info.use_metric
        except Exception as err:
            pass
