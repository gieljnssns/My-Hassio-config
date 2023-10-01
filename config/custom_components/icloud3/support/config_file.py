
from ..global_variables     import GlobalVariables as Gb
from ..const                import (
                                    ICLOUD3, APPLE_SPECIAL_ICLOUD_SERVER_COUNTRY_CODE,
                                    RARROW, HHMMSS_ZERO, DATETIME_ZERO, NONE_FNAME, INACTIVE_DEVICE,
                                    ICLOUD, FAMSHR, FMF,
                                    CONF_PARAMETER_TIME_STR,
                                    CONF_INZONE_INTERVALS, CONF_MAX_INTERVAL, CONF_EXIT_ZONE_INTERVAL,
                                    CONF_IOSAPP_ALIVE_INTERVAL,
                                    CONF_IC3_VERSION, VERSION, CONF_EVLOG_CARD_DIRECTORY, CONF_EVLOG_CARD_PROGRAM,
                                    CONF_UPDATE_DATE, CONF_VERSION_INSTALL_DATE, CONF_PASSWORD, CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX,
                                    CONF_DEVICES, CONF_SETUP_ICLOUD_SESSION_EARLY,
                                    CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT, CONF_LOG_LEVEL,
                                    CONF_DATA_SOURCE, CONF_DISPLAY_GPS_LAT_LONG,
                                    CONF_FAMSHR_DEVICENAME, CONF_FMF_EMAIL, CONF_IOSAPP_DEVICE, CONF_TRACKING_MODE,
                                    CONF_STAT_ZONE_FNAME, CONF_DEVICE_TRACKER_STATE_SOURCE,
                                    CF_DEFAULT_IC3_CONF_FILE,
                                    DEFAULT_PROFILE_CONF, DEFAULT_TRACKING_CONF, DEFAULT_GENERAL_CONF,
                                    DEFAULT_SENSORS_CONF,
                                    HOME_DISTANCE, CONF_SENSORS_TRACKING_DISTANCE,
                                    CONF_SENSORS_DEVICE, BATTERY_STATUS,
                                    CONF_WAZE_USED, CONF_WAZE_REGION, CONF_WAZE_MAX_DISTANCE, CONF_DISTANCE_METHOD,
                                    WAZE_SERVERS_BY_COUNTRY_CODE, WAZE_SERVERS_FNAME,
                                    CONF_EXCLUDED_SENSORS, CONF_OLD_LOCATION_ADJUSTMENT, CONF_DISTANCE_BETWEEN_DEVICES,
                                    CONF_EVLOG_BTNCONFIG_URL,
                                    RANGE_DEVICE_CONF, RANGE_GENERAL_CONF, MIN, MAX, STEP, RANGE_UM,
                                    )

from ..support              import start_ic3
from ..support              import waze
from ..helpers.common       import (instr, ordereddict_to_dict, )
from ..helpers.messaging    import (log_exception, _trace, _traceha, log_info_msg,
                                    close_reopen_ic3_log_file, )
from ..helpers.time_util    import (datetime_now, )

import os
import json
import base64

import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")


#-------------------------------------------------------------------------------------------
def load_storage_icloud3_configuration_file():

    if os.path.exists(Gb.ha_storage_icloud3) is False:
        os.makedirs(Gb.ha_storage_icloud3)

    if os.path.exists(Gb.icloud3_config_filename) is False:
        _LOGGER.info(f"Creating Configuration File-{Gb.icloud3_config_filename}")

        Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()
        build_initial_config_file_structure()
        write_storage_icloud3_configuration_file()

    success = read_storage_icloud3_configuration_file()

    if success:
        write_storage_icloud3_configuration_file('_backup')

    else:
        datetime = datetime_now().replace('-', '.').replace(':', '.').replace(' ', '-')
        json_errors_filename = f"{Gb.icloud3_config_filename}_errors_{datetime}"
        log_msg = ( f"iCloud3 Error > Configuration file failed to load, JSON Errors were encountered. "
                    f"Configuration file with errors was saved to `{json_errors_filename}`. "
                    f"Will restore from `configuration_backup` file")
        _LOGGER.warning(log_msg)
        os.rename(Gb.icloud3_config_filename, json_errors_filename)
        success = read_storage_icloud3_configuration_file('_backup')

        if success:
            log_msg = ("Restore from backup configuration file was successful")
            _LOGGER.warning(log_msg)

            write_storage_icloud3_configuration_file()

        else:
            _LOGGER.error(f"iCloud3{RARROW}Restore from backup configuration file failed")
            _LOGGER.error(f"iCloud3{RARROW}Recreating configuration file with default parameters-"
                            f"{Gb.icloud3_config_filename}")
            build_initial_config_file_structure()
            Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()
            write_storage_icloud3_configuration_file()
            read_storage_icloud3_configuration_file()

    config_file_check_new_ic3_version()
    config_file_check_range_values()
    count_device_tracking_methods_configured()

    if CONF_LOG_LEVEL in Gb.conf_general:
        start_ic3.set_log_level(Gb.conf_general[CONF_LOG_LEVEL])

    Gb.www_evlog_js_directory = Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]
    Gb.www_evlog_js_filename  = f"{Gb.www_evlog_js_directory}/{Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM]}"

    return

#-------------------------------------------------------------------------------------------
def read_storage_icloud3_configuration_file(filename_suffix=''):
    '''
    Read the config/.storage/.icloud3.configuration file and extract the
    data into the Global Variables

    Parameters:
        filename_suffix: A suffix added to the filename that allows saving multiple copies of
                            the configuration file
    '''

    try:
        filename = f"{Gb.icloud3_config_filename}{filename_suffix}"
        with open(filename, 'r') as f:
            Gb.conf_file_data = json.load(f)

            Gb.conf_profile   = Gb.conf_file_data['profile']
            Gb.conf_data      = Gb.conf_file_data['data']

            Gb.conf_tracking  = Gb.conf_data['tracking']
            Gb.conf_devices   = Gb.conf_data['tracking']['devices']
            Gb.conf_general   = Gb.conf_data['general']
            Gb.conf_sensors   = Gb.conf_data['sensors']
            Gb.log_level      = Gb.conf_general[CONF_LOG_LEVEL]

            Gb.conf_tracking[CONF_PASSWORD] = decode_password(Gb.conf_tracking[CONF_PASSWORD])
            if instr(Gb.conf_tracking[CONF_DATA_SOURCE], FMF):
                Gb.conf_tracking[CONF_DATA_SOURCE].pop(FMF)

            try:
                config_file_add_new_parameters()

            except Exception as err:
                log_exception(err)
                _LOGGER.error("iCloud3 > An error occured verifying the iCloud3 Configuration File. Will continue.")

        return True

    except Exception as err:
        log_exception(err)

    return False

#--------------------------------------------------------------------
def count_device_tracking_methods_configured():
    '''
    Count the number of devices that have been configured for the famshr,
    fmf and ios app tracking methods. This will be compared to the actual
    number of devices returned from iCloud during setup in PyiCloud. Sometmes,
    iCloud does not return all devices in the FamShr list and a refresh/retry
    is needed.
    '''
    try:
        Gb.conf_famshr_device_cnt = 0
        Gb.conf_fmf_device_cnt    = 0
        Gb.conf_iosapp_device_cnt = 0

        for conf_device in Gb.conf_devices:
            if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
                continue

            if conf_device[CONF_FAMSHR_DEVICENAME].startswith(NONE_FNAME) is False:
                Gb.conf_famshr_device_cnt += 1

            if conf_device[CONF_FMF_EMAIL].startswith(NONE_FNAME) is False:
                Gb.conf_fmf_device_cnt += 1

            if conf_device[CONF_IOSAPP_DEVICE].startswith(NONE_FNAME) is False:
                Gb.conf_iosapp_device_cnt += 1

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def config_file_check_new_ic3_version():
    '''
    Check to see if this is a new iCloud3 version
    '''
    update_config_file_flag = False
    if Gb.conf_profile[CONF_IC3_VERSION] != VERSION:
        Gb.conf_profile[CONF_IC3_VERSION] = VERSION
        Gb.conf_profile[CONF_VERSION_INSTALL_DATE] = datetime_now()
        update_config_file_flag = True

    elif Gb.conf_profile[CONF_VERSION_INSTALL_DATE] == DATETIME_ZERO:
        Gb.conf_profile[CONF_VERSION_INSTALL_DATE] = datetime_now()
        update_config_file_flag = True

    if update_config_file_flag:
        write_storage_icloud3_configuration_file()

#--------------------------------------------------------------------
def config_file_add_new_parameters():
    '''
    Fix configuration file errors or add any new fields
    '''

    update_config_file_flag = False

    # Fix time format from migration (b1)
    if instr(Gb.conf_data['general'][CONF_TIME_FORMAT], '-hour-hour'):
        Gb.conf_data['general'][CONF_TIME_FORMAT].replace('-hour-hour', '-hour')
        update_config_file_flag = True

    if Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY].startswith('www/') is False:
        Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY] = f"www/{Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]}"

    # Remove tracking_from_zone item from sensors list which shouldn't have been added (b3)
    if BATTERY_STATUS in Gb.conf_sensors[CONF_SENSORS_DEVICE]:
        Gb.conf_sensors[CONF_SENSORS_DEVICE].pop(BATTERY_STATUS, None)
        update_config_file_flag = True

    if 'tracking_by_zones' in Gb.conf_sensors:
        Gb.conf_sensors.pop('tracking_by_zones', None)
        update_config_file_flag = True

    # Update parameters for each device
    for conf_device in Gb.conf_devices:
        # beta 16 - Remove the device's stat zone friendly name since stat zones are ho longet
        # associated with a device
        if CONF_STAT_ZONE_FNAME in conf_device:
            conf_device.pop(CONF_STAT_ZONE_FNAME)
            update_config_file_flag = True

    # Add sensors.HOME_DISTANCE sensor to conf_sensors
    if HOME_DISTANCE not in Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE]:
        Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE].append(HOME_DISTANCE)
        update_config_file_flag = True

    # Add tracking.CONF_SETUP_ICLOUD_SESSION_EARLY
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_tracking, CONF_SETUP_ICLOUD_SESSION_EARLY, True)
            or update_config_file_flag)

    # Add sensors.CONF_EXCLUDED_SENSORS
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_sensors, CONF_EXCLUDED_SENSORS, ['None'])
            or update_config_file_flag)

    # Add general.CONF_OLD_LOCATION_ADJUSTMENT
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_OLD_LOCATION_ADJUSTMENT, HHMMSS_ZERO)
            or update_config_file_flag)

    # Add generalCONF_DISTANCE_BETWEEN_DEVICES
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_DISTANCE_BETWEEN_DEVICES, True)
            or update_config_file_flag)

    # Add general.CONF_EXIT_ZONE_INTERVAL
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_EXIT_ZONE_INTERVAL, 3)
            or update_config_file_flag)

    # Add profile.CONF_VERSION_INSTALL_DATE
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_profile, CONF_VERSION_INSTALL_DATE, DATETIME_ZERO)
            or update_config_file_flag)

    # Remove CONF_ZONE_SENSOR_EVLOG_FORMAT, Add CONF_ZONE_SENSOR_EVLOG_FORMAT
    dtf = 'zone'
    if 'zone_sensor_evlog_format' in Gb.conf_general:
        dtf = 'fname' if Gb.conf_general['zone_sensor_evlog_format'] else 'zone'
        Gb.conf_general.pop('zone_sensor_evlog_format')

    # Change Waze server codes
    if Gb.conf_general[CONF_WAZE_REGION].lower() in ['na']:
        Gb.conf_general[CONF_WAZE_REGION] = 'us'
        update_config_file_flag = True
    elif Gb.conf_general[CONF_WAZE_REGION].lower() in ['eu', 'au']:
        Gb.conf_general[CONF_WAZE_REGION] = 'row'
        update_config_file_flag = True

    # Change all time fields from hh:mm:ss to minutes (b12)
    update_config_file_flag = (_convert_hhmmss_to_minutes(Gb.conf_general)
            or update_config_file_flag)
    update_config_file_flag = (_convert_hhmmss_to_minutes(Gb.conf_general[CONF_INZONE_INTERVALS])
            or update_config_file_flag)
    for conf_device in Gb.conf_devices:
        update_config_file_flag = (_convert_hhmmss_to_minutes(conf_device)
                or update_config_file_flag)

    # Change StatZone friendly Name (b16)
    if instr(Gb.conf_general[CONF_STAT_ZONE_FNAME], '[name]'):
        Gb.conf_general[CONF_STAT_ZONE_FNAME] = 'StatZon#'
        update_config_file_flag = True

    # Add general.Display GPS coordinates Flag (b17)
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_DISPLAY_GPS_LAT_LONG, True)
            or update_config_file_flag)

    if 'device_tracker_state_format' in Gb.conf_general:
        Gb.conf_general.pop('device_tracker_state_format')

    # Change icloud to famshr since fmf no longer works (b16d)
    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD):
        Gb.conf_tracking[CONF_DATA_SOURCE] = \
            Gb.conf_tracking[CONF_DATA_SOURCE].replace(ICLOUD, FAMSHR)
        update_config_file_flag = True

          # Remove profile.CONF_HA_CONFIG_IC3_URL that is used by EvLog to open Configuration Wizard (b20)
    if 'ha_config_ic3_url' in Gb.conf_profile:
        Gb.conf_profile.pop('ha_config_ic3_url')
        update_config_file_flag = True

    # Add profile.CONF_EVLOG_BTNCONFIG_URL that is used by EvLog to open HA iCloud3 Configure screen (b20)
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_profile, CONF_EVLOG_BTNCONFIG_URL, '')
            or update_config_file_flag)

    # Add profile.event_log_version that is being used, set via action/event_log_version svc call (b20)
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_profile, 'event_log_version', '')
            or update_config_file_flag)

    # Add general.CONF_DEVICE_TRACKER_STATE_SOURCE, b20
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_DEVICE_TRACKER_STATE_SOURCE, 'ic3_fname')
            or update_config_file_flag)
    if Gb.conf_general[CONF_DEVICE_TRACKER_STATE_SOURCE] == ICLOUD3:
        Gb.conf_general[CONF_DEVICE_TRACKER_STATE_SOURCE] = 'ic3_fname'
        update_config_file_flag = True

    if update_config_file_flag:
        write_storage_icloud3_configuration_file()

    return True

#--------------------------------------------------------------------
def config_file_check_range_values():
    '''
    Check the min and max value of the items that have a range in config_flow to make
    sure the actual value in the config file is within the min-max range
    '''
    try:
        range_errors = {}
        range_errors.update({pname: range[MIN]   for pname, range in RANGE_GENERAL_CONF.items()
                                                        if Gb.conf_general[pname] < range[MIN]})
        range_errors.update({pname: range[MAX]   for pname, range in RANGE_GENERAL_CONF.items()
                                                        if Gb.conf_general[pname] > range[MAX]})
        for pname, pvalue in range_errors.items():
            log_info_msg(   f"iCloud3 Config Parameter out of range, resetting to valid value, "
                            f"Parameter-{pname}, From-{Gb.conf_general[pname]}, To-{pvalue}")
            Gb.conf_general[pname] = pvalue

        if range_errors != {}:
            write_storage_icloud3_configuration_file()

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def _convert_hhmmss_to_minutes(conf_group):

    time_fields = {pname: _hhmmss_to_minutes(pvalue)
                            for pname, pvalue in conf_group.items()
                            if (pname in CONF_PARAMETER_TIME_STR
                                    and instr(str(pvalue), ':'))}
    if time_fields != {}:
        conf_group.update(time_fields)
        return True

    return False

def _hhmmss_to_minutes(hhmmss):
        hhmmss_parts = hhmmss.split(':')
        return int(hhmmss_parts[0])*60 + int(hhmmss_parts[1])

#--------------------------------------------------------------------
def _add_config_file_parameter(conf_section, conf_parameter, default_value):
    '''
    Update the configuration file with a new field if it is not in the file.

    Return:
        True - File was updated
        False - File was not updated
    '''

    if conf_parameter not in conf_section:
        if conf_section is Gb.conf_tracking:
            _insert_into_conf_tracking(conf_parameter, default_value)
        else:
            conf_section[conf_parameter] = default_value
        return True

    return False

#--------------------------------------------------------------------
def _insert_into_conf_tracking(new_item, initial_value):
    '''
    Add item to conf_tracking before the devices element
    '''
    pos = list(Gb.conf_tracking.keys()).index(CONF_DEVICES) - 1
    items = list(Gb.conf_tracking.items())
    items.insert(pos, (new_item, initial_value ))
    Gb.conf_tracking = dict(items)

#--------------------------------------------------------------------
def write_storage_icloud3_configuration_file(filename_suffix=''):
    '''
    Update the config/.storage/.icloud3.configuration file

    Parameters:
        filename_suffix: A suffix added to the filename that allows saving multiple copies of
                            the configuration file
    '''

    try:
        filename = f"{Gb.icloud3_config_filename}{filename_suffix}"
        with open(filename, 'w', encoding='utf8') as f:
            Gb.conf_profile[CONF_UPDATE_DATE] = datetime_now()

            Gb.conf_data['tracking']['devices'] = Gb.conf_devices
            Gb.conf_data['tracking']        = Gb.conf_tracking
            Gb.conf_data['general']         = Gb.conf_general
            Gb.conf_data['sensors']         = Gb.conf_sensors

            Gb.conf_file_data['profile']    = Gb.conf_profile
            Gb.conf_file_data['data']       = Gb.conf_data

            decoded_password = Gb.conf_tracking[CONF_PASSWORD]
            Gb.conf_tracking[CONF_PASSWORD] = encode_password(Gb.conf_tracking[CONF_PASSWORD])

            json.dump(Gb.conf_file_data, f, indent=4, ensure_ascii=False)

            Gb.conf_tracking[CONF_PASSWORD] = decoded_password

        close_reopen_ic3_log_file()

        return True

    except Exception as err:
        log_exception(err)

    return False

#--------------------------------------------------------------------
def encode_password(password):
    '''
    Determine if the password is encoded.

    Return:
        Decoded password
    '''
    try:
        if (password == '' or Gb.encode_password_flag is False):
            return password

        return f"««{base64_encode(password)}»»"

    except Exception as err:
        log_exception(err)
        password = password.replace('««', '').replace('»»', '')
        return password

def base64_encode(string):
    """
    Encode the string via base64 encoder
    """
    # encoded = base64.urlsafe_b64encode(string)
    # return encoded.rstrip("=")

    string_bytes = string.encode('ascii')
    base64_bytes = base64.b64encode(string_bytes)
    return base64_bytes.decode('ascii')

#--------------------------------------------------------------------
def decode_password(password):
    '''
    Determine if the password is encoded.

    Return:
        Decoded password
    '''
    try:
        if (password.startswith('««') or password.endswith('»»')):
            password = password.replace('««', '').replace('»»', '')
            return base64_decode(password)

    except Exception as err:
        log_exception(err)
        password = password.replace('««', '').replace('»»', '')

    return password

def base64_decode(string):
    """
    Decode the string via base64 decoder
    """
    # padding = 4 - (len(string) % 4)
    # string = string + ("=" * padding)
    # return base64.urlsafe_b64decode(string)

    base64_bytes = string.encode('ascii')
    string_bytes = base64.b64decode(base64_bytes)
    return string_bytes.decode('ascii')

#-------------------------------------------------------------------------------------------
def load_icloud3_ha_config_yaml(ha_config_yaml):


    Gb.ha_config_yaml_icloud3_platform = {}
    if ha_config_yaml == '':
        return

    ha_config_yaml_devtrkr_platforms = ordereddict_to_dict(ha_config_yaml)['device_tracker']

    ic3_ha_config_yaml = {}
    for ha_config_yaml_platform in ha_config_yaml_devtrkr_platforms:
        if ha_config_yaml_platform['platform'] == 'icloud3':
            ic3_ha_config_yaml = ha_config_yaml_platform.copy()
            break

    Gb.ha_config_yaml_icloud3_platform = ordereddict_to_dict(ic3_ha_config_yaml)

#--------------------------------------------------------------------
def build_initial_config_file_structure():
    '''
    Create the initial data structure of the ic3 config file

    |---profile
    |---data
        |---tracking
            |---devices
        |---general
            |---parameters
        |---sensors

    '''

    Gb.conf_profile   = DEFAULT_PROFILE_CONF.copy()
    Gb.conf_tracking  = DEFAULT_TRACKING_CONF.copy()
    Gb.conf_devices   = []
    Gb.conf_general   = DEFAULT_GENERAL_CONF.copy()
    Gb.conf_sensors   = DEFAULT_SENSORS_CONF.copy()
    Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()

    Gb.conf_data['tracking']        = Gb.conf_tracking
    Gb.conf_data['tracking']['devices'] = Gb.conf_devices
    Gb.conf_data['general']         = Gb.conf_general
    Gb.conf_data['sensors']         = Gb.conf_sensors

    Gb.conf_file_data['profile']    = Gb.conf_profile
    Gb.conf_file_data['data']       = Gb.conf_data


    # Verify general parameters and make any necessary corrections
    try:
        if Gb.country_code in APPLE_SPECIAL_ICLOUD_SERVER_COUNTRY_CODE:
            Gb.conf_tracking[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX] = Gb.country_code

        if Gb.config and Gb.config.units['name'] != 'Imperial':
            Gb.conf_general[CONF_UNIT_OF_MEASUREMENT] = 'km'
            Gb.conf_general[CONF_TIME_FORMAT] = '24-hour'

        elif Gb.ha_use_metric:
            Gb.conf_general[CONF_UNIT_OF_MEASUREMENT] = 'km'
            Gb.conf_general[CONF_TIME_FORMAT] = '24-hour'

    except:
        pass


#--------------------------------------------------------------------
def count_lines_of_code(start_directory, total_file_lines=0, total_code_lines=0, begin_start=None):

    if begin_start is None:
        log_info_msg(f"Lines Of Code Count - {start_directory}")
        log_info_msg(" ")
        log_info_msg("---All Lines---     ---Code Lines---   Module")
        log_info_msg("Total     Lines     Total     Lines")
        #           ("11111111  22222222  33333333  44444444

    for file_name in os.listdir(start_directory):
        file_name = os.path.join(start_directory, file_name)
        if os.path.isfile(file_name):
            if file_name.endswith('.py') or file_name.endswith('.js'):
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    line_cnt = len(lines)
                    total_file_lines += line_cnt
                    code_cnt = 0
                    for line in lines:
                        if line is not None and len(line.strip()) > 3:
                            if (line.startswith("'")
                                    or line.startswith('#')):
                                continue

                        code_cnt += 1

                    total_code_lines += code_cnt

                    if begin_start is not None:
                        reldir_of_file_name = '.' + file_name.replace(begin_start, '')
                    else:
                        reldir_of_file_name = '.' + file_name.replace(start_directory, '')

                    log_info_msg(   f"{total_file_lines:<9} {line_cnt:<9} {total_code_lines:<9} "
                                    f"{code_cnt:<8} {reldir_of_file_name}")

    for file_name in os.listdir(start_directory):
        file_name = os.path.join(start_directory, file_name)
        if os.path.isdir(file_name):
            total_file_lines, total_code_lines = \
                count_lines_of_code(file_name, total_file_lines, total_code_lines, begin_start=start_directory)

    return total_file_lines, total_code_lines