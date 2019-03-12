"""
Platform that supports scanning iCloud.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.icloud/


Notes:
1. Changes to the icloud device_tracker were first inspired by icloud2.py
   developed by Walt Howd.
    -
"""

#pylint: disable=bad-whitespace, bad-indentation
#pylint: disable=bad-continuation, import-error, invalid-name, bare-except
#pylint: disable=too-many-arguments, too-many-statements, too-many-branches
#pylint: disable=too-many-locals, too-many-return-statements
#pylint: disable=unused-argument, unused-variable
#pylint: disable=too-many-instance-attributes, too-many-lines

import logging
import os
import time
import voluptuous as vol

from   homeassistant.const                import CONF_USERNAME, CONF_PASSWORD
from   homeassistant.components.device_tracker import (
          PLATFORM_SCHEMA, DOMAIN, ATTR_ATTRIBUTES, DeviceScanner)
from   homeassistant.components.zone.zone import active_zone
from   homeassistant.helpers.event        import track_utc_time_change
import homeassistant.helpers.config_validation as cv
from   homeassistant.util                 import slugify
import homeassistant.util.dt              as dt_util
from   homeassistant.util.location        import distance
import WazeRouteCalculator

VERSION = '0.86.1'      #Custom Component Updater 

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['pyicloud==0.9.1']

CONF_ACCOUNTNAME            = 'account_name'
CONF_INCLUDE_DEVICETYPES    = 'include_device_types'
CONF_EXCLUDE_DEVICETYPES    = 'exclude_device_types'
CONF_INCLUDE_DEVICES        = 'include_devices'
CONF_EXCLUDE_DEVICES        = 'exclude_devices'
CONF_INCLUDE_DEVICETYPE     = 'include_device_type'
CONF_EXCLUDE_DEVICETYPE     = 'exclude_device_type'
CONF_INCLUDE_DEVICE         = 'include_device'
CONF_EXCLUDE_DEVICE         = 'exclude_device'
CONF_FILTER_DEVICES         = 'filter_devices'
CONF_DEVICENAME             = 'device_name'
CONF_UNIT_OF_MEASUREMENT    = 'unit_of_measurement'
CONF_INTERVAL               = 'interval'
CONF_INZONE_INTERVAL        = 'inzone_interval'
CONF_MAX_INTERVAL           = 'max_interval'
CONF_TRAVEL_TIME_FACTOR     = 'travel_time_factor'
CONF_GPS_ACCURACY_THRESHOLD = 'gps_accuracy_threshold'
CONF_IGNORE_GPS_INZONE      = 'ignore_gps_accuracy_inzone'
CONF_HIDE_GPS_COORDINATES   = 'hide_gps_coordinates'
CONF_WAZE_REGION            = 'waze_region'
CONF_WAZE_MAX_DISTANCE      = 'waze_max_distance'
CONF_WAZE_MIN_DISTANCE      = 'waze_min_distance'
CONF_WAZE_REALTIME          = 'waze_realtime'
CONF_DISTANCE_METHOD        = 'distance_method'
CONF_COMMAND                = 'command'

# entity attributes
ATTR_BATTERY             = 'battery'
ATTR_DISTANCE            = 'distance'
ATTR_CALC_DISTANCE       = 'calc_distance'
ATTR_WAZE_DISTANCE       = 'waze_distance'
ATTR_WAZE_TIME           = 'travel_time'
ATTR_DIR_OF_TRAVEL       = 'dir_of_travel'
ATTR_DEVICESTATUS        = 'device_status'
ATTR_LOWPOWERMODE        = 'low_power_mode'
ATTR_BATTERYSTATUS       = 'battery_status'
ATTR_TRACKED_DEVICES     = 'tracked_devices'
ATTR_AUTHENTICATED       = 'authenticated'
ATTR_LAST_UPDATE_TIME    = 'last_update'
ATTR_NEXT_UPDATE_TIME    = 'next_update'
ATTR_LAST_LOCATED        = 'last_located'
ATTR_INFO                = 'info'
ATTR_GPS_ACCURACY        = 'gps_accuracy'
ATTR_LATITUDE            = 'latitude'
ATTR_LONGITUDE           = 'longitude'
ATTR_POLL_COUNT          = 'poll_count'

#icloud_update commands
CMD_ERROR    = 1
CMD_INTERVAL = 2
CMD_PAUSE    = 3
CMD_RESUME   = 4
CMD_WAZE     = 5

#Waze status codes
WAZE_REGIONS      = ['US', 'NA', 'EU', 'IL']
WAZE_USED         = 0
WAZE_NOT_USED     = 1
WAZE_PAUSED       = 2
WAZE_OUT_OF_RANGE = 3
WAZE_ERROR        = 4

# If the location data is old during the _update_tracked_devices routine,
# it will retry polling the device (or all devices) after 3 seconds,
# up to 4 times. If the data is still old, it will set the next normal
# interval to C_LOCATION_ISOLD_INTERVAL and keep track of the number of
# times it overrides the normal polling interval. If it is still old after
# C_MAX_LOCATION_ISOLD_CNT retries, the normal intervl will be used and
# the cycle starts over on the next poll. This will prevent a constant
# repolling if the location data is always old.
C_LOCATION_ISOLD_INTERVAL = 15
C_MAX_LOCATION_ISOLD_CNT = 4


ICLOUDTRACKERS = {}

_CONFIGURING = {}

DEVICESTATUSSET = ['deviceModel', 'rawDeviceModel', 'deviceStatus',
                    'deviceClass', 'batteryLevel', 'id', 'lowPowerMode',
                    'deviceDisplayName', 'name', 'batteryStatus', 'fmlyShare',
                    'location',
                    'locationCapable', 'locationEnabled', 'isLocating',
                    'remoteLock', 'activationLocked', 'lockedTimestamp',
                    'lostModeCapable', 'lostModeEnabled', 'locFoundEnabled',
                    'lostDevice', 'lostTimestamp',
                    'remoteWipe', 'wipeInProgress', 'wipedTimestamp',
                    'isMac']

DEVICESTATUSCODES = {
    '200': 'online',
    '201': 'offline',
    '203': 'pending',
    '204': 'unregistered',
}

SERVICE_SCHEMA = vol.Schema({
    vol.Optional(CONF_ACCOUNTNAME): vol.All(cv.ensure_list, [cv.slugify]),
    vol.Optional(CONF_DEVICENAME): cv.slugify,
    vol.Optional(CONF_INTERVAL): cv.slugify,
    vol.Optional(CONF_COMMAND): cv.string
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_ACCOUNTNAME): cv.slugify,
    vol.Optional(ATTR_AUTHENTICATED): cv.string,
    #-----►►General Attributes ----------
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default='mi'): cv.slugify,
    vol.Optional(CONF_INZONE_INTERVAL, default='2 hrs'): cv.string,
    vol.Optional(CONF_MAX_INTERVAL, default=0): cv.string,
    vol.Optional(CONF_TRAVEL_TIME_FACTOR, default=.60): cv.string,
    vol.Optional(CONF_GPS_ACCURACY_THRESHOLD, default=100): cv.string,
    vol.Optional(ATTR_GPS_ACCURACY): cv.slugify,
    vol.Optional(CONF_IGNORE_GPS_INZONE, default=True): cv.boolean,
    vol.Optional(CONF_HIDE_GPS_COORDINATES, default=False): cv.boolean,
    #-----►►Filter, Include, Exclude Devices ----------
    vol.Optional(CONF_INCLUDE_DEVICETYPES): \
                                    vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_INCLUDE_DEVICETYPE): \
                                    vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_INCLUDE_DEVICES): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_INCLUDE_DEVICE): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_EXCLUDE_DEVICETYPES): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_EXCLUDE_DEVICETYPE): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_EXCLUDE_DEVICES): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_EXCLUDE_DEVICE): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_FILTER_DEVICES): cv.slugify,
    vol.Optional(ATTR_TRACKED_DEVICES): cv.string,
    #-----►►Location Attributes  ----------
    vol.Optional(ATTR_LAST_UPDATE_TIME): cv.slugify,
    vol.Optional(ATTR_NEXT_UPDATE_TIME): cv.slugify,
    vol.Optional(ATTR_LAST_LOCATED): cv.slugify,
    vol.Optional(ATTR_DIR_OF_TRAVEL): cv.slugify,
    vol.Optional(ATTR_INFO): cv.string,
    #-----►►Waze Attributes ----------
    vol.Optional(CONF_DISTANCE_METHOD, default='waze'): cv.string,
    vol.Optional(CONF_WAZE_REGION, default='US'): cv.string,
    vol.Optional(CONF_WAZE_MAX_DISTANCE, default=1000): cv.string,
    vol.Optional(CONF_WAZE_MIN_DISTANCE, default=1): cv.string,
    vol.Optional(CONF_WAZE_REALTIME, default=False): cv.boolean,
    vol.Optional(CONF_COMMAND): cv.string
})

def combine_config_filter_parms(parm_devices, parm_device):
    '''
    Return a concatinated configuration parms string. 
        include_device + include_devices
        exclude_device + exclude_devices
        include_device_type + include_device_types
        exclude_device + exclude_device_types
        
    Returned the combine the two lists (p1 & p2)
    '''
    combined_list = []
    if parm_devices:
        for item in parm_devices:
            combined_list.append(item.lower())
    if parm_device:
        for item in parm_device:
            combined_list.append(item.lower())

    return  combined_list

#--------------------------------------------------------------------
def setup_scanner(hass, config: dict, see, discovery_info=None):
    """Set up the iCloud Scanner."""
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    account  = config.get(CONF_ACCOUNTNAME,
                         slugify(username.partition('@')[0]))

    include_device_types = combine_config_filter_parms(config.get(
            CONF_INCLUDE_DEVICETYPES),
            config.get(CONF_INCLUDE_DEVICETYPE))
    include_devices = combine_config_filter_parms(config.get(
            CONF_INCLUDE_DEVICES),
            config.get(CONF_INCLUDE_DEVICE))
    exclude_device_types = combine_config_filter_parms(
            config.get(CONF_EXCLUDE_DEVICETYPES),
            config.get(CONF_EXCLUDE_DEVICETYPE))
    exclude_devices = combine_config_filter_parms(
            config.get(CONF_EXCLUDE_DEVICES),
            config.get(CONF_EXCLUDE_DEVICE))
    filter_devices = config.get(CONF_FILTER_DEVICES) 

    if config.get(CONF_MAX_INTERVAL) == '0':
        inzone_interval = config.get(CONF_INZONE_INTERVAL)
    else:
        inzone_interval = config.get(CONF_MAX_INTERVAL)
 
    max_interval           = config.get(CONF_MAX_INTERVAL)
    gps_accuracy_threshold = config.get(CONF_GPS_ACCURACY_THRESHOLD)
    ignore_gps_inzone_flag = config.get(CONF_IGNORE_GPS_INZONE)
    hide_gps_coordinates   = config.get(CONF_HIDE_GPS_COORDINATES)
    unit_of_measurement    = config.get(CONF_UNIT_OF_MEASUREMENT)
    distance_method        = config.get(CONF_DISTANCE_METHOD)
    waze_region            = config.get(CONF_WAZE_REGION)
    waze_max_distance      = config.get(CONF_WAZE_MAX_DISTANCE)
    waze_min_distance      = config.get(CONF_WAZE_MIN_DISTANCE)
    travel_time_factor     = config.get(CONF_TRAVEL_TIME_FACTOR)
    waze_realtime          = config.get(CONF_WAZE_REALTIME)

    if waze_region not in WAZE_REGIONS:
        log_msg = ("Invalid Waze Region ({}). Valid Values are: "\
                      "NA=US or North America, EU=Europe, IL=Isreal",
                      waze_region) 
        self._LOGGER_error_msg(log_msg)

        waze_region       = 'US'
        waze_max_distance = 0
        waze_min_distance = 0

    icloudaccount = Icloud(hass, see, username, password, account,
        include_device_types, include_devices,
        exclude_device_types, exclude_devices, filter_devices,
        inzone_interval, gps_accuracy_threshold, hide_gps_coordinates,
        ignore_gps_inzone_flag,
        unit_of_measurement, travel_time_factor, distance_method,
        waze_region, waze_realtime, waze_max_distance, waze_min_distance)

    if icloudaccount.api:
        ICLOUDTRACKERS[account] = icloudaccount

    else:
        log_msg = ("No ICLOUDTRACKERS added") 
        self._LOGGER_error_msg(log_msg)

        return False

#--------------------------------------------------------------------
    def lost_iphone(call):
        """Call the lost iPhone function if the device is found."""
        accounts = call.data.get(CONF_ACCOUNTNAME, ICLOUDTRACKERS)
        devicename = call.data.get(CONF_DEVICENAME)
        for account in accounts:
            if account in ICLOUDTRACKERS:
                ICLOUDTRACKERS[account].lost_iphone(devicename)
    hass.services.register(DOMAIN, 'icloud_lost_iphone', lost_iphone,
                           schema=SERVICE_SCHEMA)

#--------------------------------------------------------------------

    def update_icloud(call):
        """Call the update function of an iCloud account."""
        accounts   = call.data.get(CONF_ACCOUNTNAME, ICLOUDTRACKERS)
        devicename = call.data.get(CONF_DEVICENAME)
        command    = call.data.get(CONF_COMMAND)

        for account in accounts:
            if account in ICLOUDTRACKERS:
                ICLOUDTRACKERS[account].update_icloud(devicename, command)

    hass.services.register(DOMAIN, 'icloud_update', update_icloud,
                           schema=SERVICE_SCHEMA)


#--------------------------------------------------------------------
    def reset_account_icloud(call):
        """Reset an iCloud account."""
        accounts = call.data.get(CONF_ACCOUNTNAME, ICLOUDTRACKERS)
        for account in accounts:
            if account in ICLOUDTRACKERS:
                ICLOUDTRACKERS[account].reset_account_icloud()

    hass.services.register(DOMAIN, 'icloud_reset_account',
                reset_account_icloud, schema=SERVICE_SCHEMA)
#--------------------------------------------------------------------
    def setinterval(call):
        """Call the update function of an iCloud account."""
        accounts = call.data.get(CONF_ACCOUNTNAME, ICLOUDTRACKERS)
        interval = call.data.get(CONF_INTERVAL)
        devicename = call.data.get(CONF_DEVICENAME)

        for account in accounts:
            if account in ICLOUDTRACKERS:
                ICLOUDTRACKERS[account].setinterval(interval, devicename)

    hass.services.register(DOMAIN, 'icloud_set_interval',
                setinterval, schema=SERVICE_SCHEMA)


    # Tells the bootstrapper that the component was successfully initialized
    return True


#====================================================================
class Icloud(DeviceScanner):
    """Representation of an iCloud account."""

    def __init__(self, hass, see, username, password, account,
        include_device_types, include_devices,
        exclude_device_types, exclude_devices, filter_devices,
        inzone_interval, gps_accuracy_threshold, hide_gps_coordinates,
        ignore_gps_inzone_flag,
        unit_of_measurement, travel_time_factor, distance_method,
        waze_region, waze_realtime, waze_max_distance, waze_min_distance):

        """Initialize an iCloud account."""
        self.hass          = hass
        self.username      = username
        self.password      = password
        self.api           = None
        self.accountname   = account      #name
        self.see           = see
        self.friendly_name = {}           #name made from status['name']
        self.reset_icloud_account_request_flag = False
        self.authenticated_time = ''
        
        #string set using the update_icloud command to pass debug commands
        #into icloud3 to monitor operations or to set test variables
        #   gps - set gps acuracy to 234
        #   old - set isold_cnt to 4
        #   interval - toggle display of interval calulation method in info fld
        #   log - log 'debug' messages to the log file under the 'info' type
        self.debug_control        = ''
        self.write_log_debug_msgs_flag       = False
        self.attributes_initialized_flag = False

        self.include_device_types = include_device_types
        self.exclude_device_types = exclude_device_types
        if filter_devices:      #for iCloud2 compatiblity
            self.include_devices      = filter_devices
        else:
            self.include_devices      = include_devices
            not filter_devices

        self.exclude_devices      = exclude_devices

        self.tracked_devices       = {}
        self.seen_this_device_flag = {}
        self.inzone_interval = self._time_str_to_seconds(
                                     inzone_interval)
        self.gps_accuracy_threshold  = int(gps_accuracy_threshold)
        self.ignore_gps_inzone_flag  = ignore_gps_inzone_flag
        self.hide_gps_coordinates    = hide_gps_coordinates

        self.unit_of_measurement     = unit_of_measurement
        self.travel_time_factor      = float(travel_time_factor)

        #Define variables, lists & tables
        if unit_of_measurement == 'mi':
            self.time_format         = '%I:%M:{}'
            self.date_time_format    = '%x %-I:%M:{}'
            self.km_mi_factor        = 0.62137
        else:
            self.time_format         = '%H:%M:{}'
            self.date_time_format    = '%x %H:%M:{}'
            self.km_mi_factor        = 1

        self.last_state                  = {}
        self.current_state               = {}
        self.this_update_seconds         = 0
        self.overrideinterval_seconds    = {}
        self.interval_seconds            = {}
        self.interval_str                = {}
        self.went_3km                    = {} #if more than 2 km/mi, probably driving
        self.last_update_time            = {}
        self.last_update_seconds         = {}
        self.next_update_seconds         = {}
        self.next_update_time            = {}
        self.poll_count                  = {}
        self.poll_count_yesterday        = {}
        self.location_isold_cnt          = {}    # override interval while < 4

        self.tracked_devicenames_all     = ''
        self.immediate_retry_flag        = False
        self.time_zone_offset_seconds    = 0
        self.setinterval_cmd_devicename  = None
        self.device_being_updated_flag   = {}
        self.device_being_updated_retry_cnt = {}
        self.update_in_process_flag      = False
        self.dist_from_home_small_move_total = {}
        #get home zone location
        self.zone_home        = self.hass.states.get('zone.home').attributes
        self.zone_home_lat    = self.zone_home['latitude']
        self.zone_home_long   = self.zone_home['longitude']
        self.zone_home_radius = round(self.zone_home['radius']/1000, 4)
        self.zone_home_radius_near = round(self.zone_home_radius * 5, 2)

        #used to calculate distance traveled since last poll
        self.last_lat       = {}
        self.last_long      = {}
        self.stationary_cnt = {}
        self.waze_time      = {}
        self.waze_dist      = {}
        self.calc_dist      = {}
        self.dist           = {}

        self.state_change_flag      = {}
        self.poor_gps_accuracy_flag = {}
        self.poor_gps_accuracy_cnt  = {}

        #Setup Waze parameters
        self.distance_method_waze_flag = (distance_method.lower() == 'waze')

        #ok=0, not used=1, paused=2, out-of-range=3, error=4
        if self.distance_method_waze_flag:
            self.waze_status = WAZE_USED
        else:
            self.waze_status = WAZE_NOT_USED

        self.waze_region         = waze_region
        self.waze_min_distance   = self._mi_to_km(float(waze_min_distance))
        self.waze_max_distance   = self._mi_to_km(float(waze_max_distance))
        self.waze_max_dist_save  = self.waze_max_distance
        self.waze_realtime       = waze_realtime

        self._verification_code  = None
        self._trusted_device     = None
        self._trusted_device_id  = None
        self._valid_trusted_device_ids = None

        self._attrs                   = {}
        self._attrs[CONF_ACCOUNTNAME] = account     #name

        self.reset_account_icloud()

        #add HA event that will call the _device_polling_15_sec_timer_loop function every 15 seconds
        #that will check a iphone's location if the time interval
        #has passed. If so, update all tracker attributes for all phones
        #being tracked with the new information.

        track_utc_time_change(self.hass, self._device_polling_15_sec_timer_loop,
                              second=[0, 15, 30, 45])

#--------------------------------------------------------------------
    def reset_account_icloud(self):
        """Reset an iCloud account."""
        from pyicloud import PyiCloudService
        from pyicloud.exceptions import (
            PyiCloudFailedLoginException, PyiCloudNoDevicesException)

        log_msg = ("►►► ICLOUD3.PY INITIALIZING ACCOUNT "
                     "{} as {}").format(self.username, self.accountname)
        self._LOGGER_info_msg(log_msg)

        self.time_zone_offset_seconds = self._calculate_time_zone_offset()

        icloud_dir = self.hass.config.path('icloud')
        if not os.path.exists(icloud_dir):
            os.makedirs(icloud_dir)

        try:
            self.api = PyiCloudService(self.username, self.password,
                       cookie_directory=icloud_dir, verify=True)
        except PyiCloudFailedLoginException as error:
            self.api = None
            log_msg = ("Error logging into iCloud Service: {}").format(error) 
            self._LOGGER_error_msg(log_msg)

            return

        log_msg = ("Authentication for {} as {} successful").format(
                        self.username, self.accountname) 
        self._LOGGER_info_msg(log_msg)
 
        try:
            self.authenticated_time       = \
                            dt_util.now().strftime(self.date_time_format)
            self.tracked_devices          = {}
            self.device_type              = {}
            self.overrideinterval_seconds = {}
            self.tracking_device_flag     = {}

            log_msg = ("Waze Settings: Region={}, Realtime={}, "
                          "MaxDistance={}, MinDistance={}").format(
                          self.waze_region, self.waze_realtime,
                          self.waze_max_distance, self.waze_min_distance) 
            self._LOGGER_info_msg(log_msg)

            log_msg = ("Filters: include_device_types={},"
                         " include_devices={}, exclude_device_types={},"
                         " exclude_devices={}").format(
                         self.include_device_types, self.include_devices,
                         self.exclude_device_types, self.exclude_devices) 
            self._LOGGER_info_msg(log_msg)

            log_msg = ("Initializing Device Tracking for user {}",
                            self.username) 
            self._LOGGER_info_msg(log_msg)

            self.tracked_devicenames_all = ''
            for device in self.api.devices:
                status      = device.status(DEVICESTATUSSET)
                location    = status['location']
                devicename  = slugify(status['name'].replace(' ', '', 99))
                device_type = status['deviceClass'].lower()

                if location is None:
                    log_msg = ("Not tracking {}/{}, No location "
                                 "information").format(
                                 self.accountname, devicename) 
                    self._LOGGER_info_msg(log_msg)

                    tracking_flag = False
                elif status['locationEnabled'] is False:
                    log_msg = ("Not tracking {}/{}, Location Disabled").format(
                                 self.accountname, devicename) 
                    self._LOGGER_info_msg(log_msg)

                    tracking_flag = False
                elif status['deviceStatus'] == '204':
                    log_msg = ("Not tracking {}/{}, Unregistered "
                                 "Device (Status=204)").format(
                                 self.accountname, devicename) 
                    self._LOGGER_info_msg(log_msg)

                    tracking_flag = False
                elif devicename in self.tracking_device_flag:
                    log_msg = ("Not tracking {}/{}, Multiple "
                                 "devices with same name").format(
                                 self.accountname, devicename) 
                    self._LOGGER_info_msg(log_msg)

                    tracking_flag = False
                else:
                    tracking_flag = self._check_tracking_this_device(
                                    devicename, device_type)

                self.tracking_device_flag[devicename] = tracking_flag
                if tracking_flag is False:
                    continue

                self.tracked_devicenames_all = '{}{}/{}, '.\
                            format(self.tracked_devicenames_all, self.accountname, 
                            devicename)
                       
                self.tracked_devices[devicename] = device
                self.device_type[devicename]     = device_type

                #state
                self.last_state[devicename]        = \
                                        self._get_current_state(devicename)
                self.current_state[devicename]     = \
                                        self.last_state[devicename]
                self.state_change_flag[devicename]      = False
                self.device_being_updated_flag[devicename] = False
                self.device_being_updated_retry_cnt[devicename] = 0
                self.seen_this_device_flag[devicename]  = False
                self.went_3km[devicename]               = False

                #times, flags
                self.last_update_time[devicename]     = '00:00:00'
                self.last_update_seconds[devicename]  = 0
                self.next_update_time[devicename]     = '00:00:00'
                self.next_update_seconds[devicename]  = 0
                self.poll_count[devicename]           = 0
                self.poll_count_yesterday[devicename] = 0

                #interval, distances, times
                self.overrideinterval_seconds[devicename] = 0
                self.interval_seconds[devicename]    = 0
                self.interval_str[devicename]        = '0 sec'
                self.waze_time[devicename]           = 0
                self.waze_dist[devicename]           = 0
                self.calc_dist[devicename]           = 0
                self.dist[devicename]                = 0
                self.dist_from_home_small_move_total[devicename] = 0

                #location, gps
                self.stationary_cnt[devicename]       = 0
                self.location_isold_cnt[devicename]   = 0
                self.last_lat[devicename]             = self.zone_home_lat
                self.last_long[devicename]            = self.zone_home_long
                self.poor_gps_accuracy_flag[devicename] = False
                self.poor_gps_accuracy_cnt[devicename]  = 0

                #Create stationary zone for devicename
                #Try take first name of user (strip off punctuation)
                user_name = status['name'].split(" ")
                user_name = user_name[0].split("'")
                user_name = user_name[0].split('-')
                self.friendly_name[devicename] = user_name[0]

                #create dynamic zone used by ios app when stationary
                self._update_dynamic_stationary_zone(devicename, 0, 180)
                
                #Initialize the new attributes
                kwargs                         = {}
                attrs                          = {}
                attrs[ATTR_AUTHENTICATED]      = ''
                attrs[ATTR_LAST_UPDATE_TIME]   = '00:00:00'
                attrs[ATTR_NEXT_UPDATE_TIME]   = '00:00:00'
                attrs[ATTR_LAST_LOCATED]       = '00:00:00'
                attrs[ATTR_DISTANCE]           = 0
                attrs[ATTR_WAZE_TIME]          = ''
                attrs[ATTR_CALC_DISTANCE]      = 0
                attrs[ATTR_WAZE_DISTANCE]      = 0
                attrs[ATTR_POLL_COUNT]         = 0
                attrs[ATTR_DIR_OF_TRAVEL]      = ''
                attrs[ATTR_INFO]               = ''

                attrs[ATTR_TRACKED_DEVICES]    = self.tracked_devicenames_all[:-2]
                attrs[CONF_TRAVEL_TIME_FACTOR] = self.travel_time_factor
                attrs[CONF_WAZE_MIN_DISTANCE]  = \
                        self._km_to_mi(self.waze_min_distance)
                attrs[CONF_WAZE_MAX_DISTANCE]  = \
                        self._km_to_mi(self.waze_max_distance)

                self._update_device_attributes(devicename, kwargs, attrs)

            log_msg = ("Tracking Devices {}").format(self.tracked_devicenames_all[:-2]) 
            self._LOGGER_info_msg(log_msg)

        except PyiCloudNoDevicesException:
            log_msg = ('No iCloud Devices found!') 
            self._LOGGER_error_msg(log_msg)

        self.reset_icloud_account_request_flag = False

#--------------------------------------------------------------------
    def icloud_need_trusted_device(self):
        """We need a trusted device."""
        configurator = self.hass.components.configurator
        if self.accountname in _CONFIGURING:
            return

        devicesstring = ''
        if self._valid_trusted_device_ids == 'Invalid Entry':
            devicesstring = '\n\n'\
                '----------------------------------------------\n'\
                '●●● Previous Trusted Device Id Entry is Invalid ●●●\n\n\n' \
                '----------------------------------------------\n\n\n'
            self._valid_trusted_device_ids = None

        devices = self.api.trusted_devices

        for i, device in enumerate(devices):
            devicename = "\n....Device Id={} for {} ({})". \
                        format(i, device.get('phoneNumber'), \
                        device.get('deviceName'))
            devicesstring += "{}; ".format(devicename)
            self._valid_trusted_device_ids = "{},{}".\
                        format(i, self._valid_trusted_device_ids)

        description_msg = 'Please choose the Trusted Device Id to receive ' \
                  'the verification code via a text message. \n\n {}' \
                  .format(devicesstring)

        _CONFIGURING[self.accountname] = configurator.request_config(
            'iCloud Select Trusted Device for: {}'.format(self.accountname),
            self.icloud_trusted_device_callback,
            description    = (description_msg),
            entity_picture = "/static/images/config_icloud.png",
            submit_caption = 'Confirm',
            fields         = [{'id': 'trusted_device', \
                               'name': 'Trusted Device'}]
        )

#--------------------------------------------------------------------
    def icloud_trusted_device_callback(self, callback_data):
        """Handle chosen trusted devices."""
        self._trusted_device_id = int(callback_data.get('trusted_device'))
        self._trusted_device    = \
                    self.api.trusted_devices[self._trusted_device_id]

        log_msg = ("id={}, Valid={}").format(
                    self._trusted_device_id, self._valid_trusted_device_ids) 
        self._LOGGER_error_msg(log_msg)

        if self.accountname in _CONFIGURING:
            request_id   = _CONFIGURING.pop(self.accountname)
            configurator = self.hass.components.configurator
            configurator.request_done(request_id)

        if str(self._trusted_device_id) not in self._valid_trusted_device_ids:
            log_msg = ("Invalid Trusted Device ID. Valid IDs={}, "\
                          "Entered={}").format(\
                          self._valid_trusted_device_ids,
                          self._trusted_device_id) 
            self._LOGGER_error_msg(log_msg)

            self._trusted_device = None
            self._valid_trusted_device_ids = 'Invalid Entry'
            self.icloud_need_trusted_device()

        elif not self.api.send_verification_code(self._trusted_device):
            log_msg = ("Failed to send verification code") 
            self._LOGGER_error_msg(log_msg)

            self._trusted_device = None
            self._valid_trusted_device_ids = None

        else:
            # Get the verification code, Trigger the next step immediately
            self.icloud_need_verification_code()

#------------------------------------------------------
    def icloud_need_verification_code(self):
        """Return the verification code."""
        configurator = self.hass.components.configurator
        if self.accountname in _CONFIGURING:
            return

        _CONFIGURING[self.accountname] = configurator.request_config(
            'iCloud Enter Verification Code for: {}'.format(self.accountname),
            self.icloud_verification_callback,
            description    = ('Please enter the validation code:'),
            entity_picture = "/static/images/config_icloud.png",
            submit_caption = 'Confirm',
            fields         = [{'id': 'code', \
                               'name': 'Verification Code'}]
        )

#--------------------------------------------------------------------
    def icloud_verification_callback(self, callback_data):
        """Handle the chosen trusted device."""
        from pyicloud.exceptions import PyiCloudException
        self._verification_code = callback_data.get('code')

        try:
            if not self.api.validate_verification_code(
                    self._trusted_device, self._verification_code):
                raise PyiCloudException('Unknown failure')
        except PyiCloudException as error:
            # Reset to the initial 2FA state to allow the user to retry
            log_msg = ("Failed to verify verification code: {}").format(error) 
            self._LOGGER_error_msg(log_msg)

            self._trusted_device = None
            self._verification_code = None

            # Trigger the next step immediately
            self.icloud_need_trusted_device()

        if self.accountname in _CONFIGURING:
            request_id   = _CONFIGURING.pop(self.accountname)
            configurator = self.hass.components.configurator
            configurator.request_done(request_id)


#########################################################
#
#   This function is called every 15 seconds by HA. Cycle through all
#   of the iCloud devices to see if any of the ones being tracked need
#   to be updated. If so, we might as well update the information for
#   all of the devices being tracked since PyiCloud gets data for
#   every device in the account.
#
#########################################################

    def _device_polling_15_sec_timer_loop(self, now):
        """Keep the API alive. Will be called by HA every 15 seconds"""

        self.this_update_seconds = \
                self._time_to_seconds(dt_util.now().strftime('%X'))
        this_update_time = dt_util.now().strftime(self.time_format)

        if self.api is None:
            log_msg = ("►►ICLOUD API ERROR, no Device API information "
                            "for devices. Resetting iCloud")
            self._LOGGER_error_msg(log_msg)

            self.reset_account_icloud()

        elif self.reset_icloud_account_request_flag:    #via service call
            self.reset_account_icloud()

        if self.api is None:
            log_msg = ("►►ICLOUD RESET FAILED, no Device API information "
                            "after reset")
            self._LOGGER_error_msg(log_msg)

            return

        if self.api.requires_2fa:
            from pyicloud.exceptions import PyiCloudException
            try:
                if self._trusted_device is None:
                    self.icloud_need_trusted_device()
                    return

                if self._verification_code is None:
                    self.icloud_need_verification_code()
                    return

                self.api.authenticate()
                self.authenticated_time = \
                            dt_util.now().strftime(self.date_time_format)

                log_msg = ("iCloud Authentication, Devices={}").format(
                    self.api.devices) 
                self._LOGGER_info_msg(log_msg)

                if self.api.requires_2fa:
                    raise Exception('Unknown failure')

                self._trusted_device    = None
                self._verification_code = None
            except PyiCloudException as error:
                log_msg = ("►►Error setting up 2FA: {}").format(error)
            self._LOGGER_error_msg(log_msg)

        try:

            #Set update in process flag used in the 'icloud_update' external
            #command service call. Otherwise, the service call might be
            #overwritten if we are doing an update when it was started.
            device_needs_updating_flag = False
            for devicename in self.tracked_devices:
                if (self.tracking_device_flag.get(devicename) is False or
                   self.next_update_time.get(devicename) == 'Paused'):
                    continue

                current_state = self._get_current_state(devicename)

                # If the state changed since last poll, force an update
                # This can be done via device_tracker.see service call
                # with a different location_name in an automation or
                # from entering a zone via the IOS App.
                if current_state != self.last_state.get(devicename):
                    log_msg = ("Zone Change Detected for {}, "
                         "From={}, To={}").format(devicename,
                         self.last_state.get(devicename), current_state) 
                    self._LOGGER_info_msg(log_msg)

                    log_msg = ("►►►►DEVICE STATE CHANGED ~~{}/{}~~, "
                         "From={}, To={} <WARN>").format(self.accountname, devicename,
                         self.last_state.get(devicename), current_state) 
                    self._LOGGER_debug_msg(log_msg)

                    self.state_change_flag[devicename]   = True
                    if 'nearzone' in current_state.lower():
                        current_state = 'near_zone'
                    self.current_state[devicename]       = current_state
                    self.stationary_cnt[devicename]      = 0
                    self.next_update_seconds[devicename] = 0

                    attrs  = {}
                    kwargs = {}
                    attrs[CONF_INTERVAL]           = '0 sec'
                    attrs[ATTR_NEXT_UPDATE_TIME]   = '00:00:00'

                    self._update_device_attributes(devicename, kwargs, attrs)

                #This flag will be 'true' if the last update for this device
                #was not completed. Do another update now.
                if (self.device_being_updated_flag.get(devicename) and
                    self.device_being_updated_retry_cnt.get(devicename) > 4):
                    self.device_being_updated_flag[devicename] = False
                    self.device_being_updated_retry_cnt[devicename] = 0
                    
                    log_msg = ("►►CANCELING RETRY for device {}").format(
                                    devicename) 
                    self._LOGGER_info_msg(log_msg)
                    
                if self.device_being_updated_flag.get(devicename):
                    self.device_being_updated_retry_cnt[devicename] += 1
                    log_msg = ("►►RETRYING UPDATE - Device update was not "
                                    "completed in last cycle ~~{}~~ ").format(
                                    devicename) 
                    self._LOGGER_info_msg(log_msg)

                    device_needs_updating_flag = True

                elif (self.this_update_seconds >=
                            self.next_update_seconds.get(devicename)):
                    device_needs_updating_flag = True

            if device_needs_updating_flag:
                self._wait_if_update_in_process()
                self.update_in_process_flag = True
                self._update_tracked_devices()

            self.update_in_process_flag = False

        except ValueError:
            log_msg = ("►►ICLOUD API ERROR, Error={}").format(ValueError)
            self._LOGGER_error_msg(log_msg)

            self.api.authenticate()           #Reset iCloud
            self.authenticated_time = \
                            dt_util.now().strftime(self.date_time_format)
            self._update_tracked_devices()    #Retry update devices
            self.update_in_process_flag = False

#########################################################
#
#   Cycle through all iCloud devices and update the information for the devices
#   being tracked
#     ●►●◄►●▬▲▼◀►►●◀ oPhone=►▶
#########################################################

    def _update_tracked_devices(self, arg_devicename=None):
        """
        Request device information from iCloud (if needed) and update
        device_tracker information.
        """

        from pyicloud.exceptions import PyiCloudNoDevicesException

        try:
            for devicename in self.tracked_devices:
                log_msg = ("►►ICLOUD DEVICE Loop "
                            "Arg_devicename={}, Devicename={}").format(
                            arg_devicename, devicename) 
                self._LOGGER_debug_msg(log_msg)

                if arg_devicename and devicename != arg_devicename:
                    continue

                if self.next_update_time.get(devicename) == 'Paused':
                    continue

                log_msg = ("▼▼▼▼▼ UPDATE DEVICE <START> - "
                        "{}/{} ({}) ▼▼▼▼▼ <WARN>").format(self.accountname,
                        devicename, self.current_state.get(devicename))
                self._LOGGER_debug_msg(log_msg)

                try:
                    device = self.tracked_devices.get(devicename)
                    log_msg = ("►►ICLOUD DEVICE DATA, Device={}").format(
                                device) 
                    self._LOGGER_debug_msg(log_msg)

                    status = device.status(DEVICESTATUSSET)
                    log_msg = ("►►ICLOUD DEVICE DATA, Status={}").format(
                                status) 
                    self._LOGGER_debug_msg(log_msg)

                except:
#                   No icloud data, reauthenticate (status=None)
                    self.api.authenticate()
                    self.authenticated_time = \
                            dt_util.now().strftime(self.date_time_format)
                    device = self.tracked_devices.get(devicename)
                    status = device.status(DEVICESTATUSSET)
                    log_msg = ("Reauthenticated iCloud account for e {}/{}").format(
                            self.accountname, devicename) 
                    self._LOGGER_info_msg(log_msg)

                    if status is None:
                        log_msg = ("iCloud Reauthentication Error,"
                            "No data available for {}, Aborting").format(devicename)
                        self._LOGGER_error_msg(log_msg)

                        self.authenticated_time = ''
                        return

                try:
                    location   = status['location']
                    devicename = slugify(status['name'].replace(' ', '', 99))
                    battery    = int(status.get('batteryLevel', 0) * 100)

                    #Make log file entry for device status data & location data
    #                self._log_device_status_attrubutes(status)

                    if self.device_being_updated_flag.get(devicename):
                        update_msg = "Last update not completed, retrying"
                    else:
                        update_msg = "Updating"
                    update_msg = "● {} {} ●".format(update_msg, status['name'])

                    attrs  = {}
                    kwargs = {}
                    attrs[ATTR_INFO] = update_msg
                    self._update_device_attributes(devicename, kwargs, attrs)

                    #set device being updated flag. This is checked in the
                    #'_device_polling_15_sec_timer_loop' loop to make sure the last update
                    #completed successfully (Waze has a compile error bug that will
                    #kill update and everything will sit there until the next poll.
                    #if this is still set in '_device_polling_15_sec_timer_loop', repoll
                    #immediately!!!
                    self.device_being_updated_flag[devicename] = True

                    c = float(self.poll_count.get(devicename)) + 1
                    self.poll_count[devicename] = c

                    if not location:
                        attrs    = {}
                        attrs[CONF_INTERVAL] = 'Error: No Location Data'
                        time_stamp = 'No Location Data'
                        self.last_state[devicename] = 'unknown'

                    else:
                        # If old, this function will sleep for 2 seconds, then
                        # do another poll, up to 4 times before returning with
                        # the last location data.
                        if location['isOld'] or 'old' in self.debug_control:
                            location = self._retry_setup_location_data(
                                        device, devicename, location)

                        time_stamp = self._timestamp_to_time(location['timeStamp'])
                        latitude     = location[ATTR_LATITUDE]
                        longitude    = location[ATTR_LONGITUDE]
                        gps_accuracy = int(location['horizontalAccuracy'])

                        location_isold_flag, isold_cnt = \
                                self._check_isold_status(devicename,
                                            location['isOld'],
                                            location['timeStamp'])

                        log_msg = ("►►LOCATION DATA ~~{}~~, "
                              "TimeStamp={}({}), Long={}, "
                              "Lat={}, isOldFlag={}, isOldRetryCnt={}, GPS={}").format(
                              devicename, location['timeStamp'], time_stamp,
                              longitude, latitude,
                              location_isold_flag, isold_cnt, gps_accuracy) 
                        self._LOGGER_debug_msg(log_msg)

                        if 'gps' in self.debug_control:
                            gps_accuracy = 234 #debug

                        self.poor_gps_accuracy_flag[devicename] = \
                                (gps_accuracy > self.gps_accuracy_threshold)

                        if not self.poor_gps_accuracy_flag.get(devicename):
                            self.poor_gps_accuracy_cnt[devicename] = 0

                        #Calculate polling interval and setup location attributes
                        attrs = self._determine_interval(devicename,
                                      latitude, longitude, battery,
                                      gps_accuracy, location_isold_flag)

                        # Double check state, it can be wrong during ha startup
                        if self.last_state.get(devicename) == 'unknown':
                            current_zone = self._get_current_zone(devicename,
                                            latitude, longitude)
                            self.last_state[devicename]    = current_zone
                            self.current_state[devicename] = current_zone

                    # End of 'if not location:' statement

                    log_msg = ("►►LOCATION ATTRIBUTES, State={}, Attrs={}",
                                    self.last_state.get(devicename), attrs) 
                    self._LOGGER_debug_msg(log_msg)

                    attrs[CONF_ACCOUNTNAME]     = self.accountname
                    attrs[ATTR_AUTHENTICATED]   = self.authenticated_time
                    attrs[ATTR_LAST_LOCATED]    = time_stamp
                    attrs[ATTR_DEVICESTATUS]    = DEVICESTATUSCODES.get(
                                    status['deviceStatus'], 'error')
                    attrs[ATTR_LOWPOWERMODE]    = status['lowPowerMode']
                    attrs[ATTR_BATTERYSTATUS]   = status['batteryStatus']
                    attrs[ATTR_TRACKED_DEVICES] = self.tracked_devicenames_all[:-2]

                    if self.poor_gps_accuracy_cnt.get(devicename) > 0:
                        attrs[ATTR_POLL_COUNT]  = "{}-GPS".format(\
                                self.poor_gps_accuracy_cnt.get(devicename))
                    elif self.stationary_cnt.get(devicename) > 0:
                        attrs[ATTR_POLL_COUNT]  = "{}-Statnry".format(\
                                self.stationary_cnt.get(devicename))
                    elif self.location_isold_cnt.get(devicename) > 0:
                        attrs[ATTR_POLL_COUNT]  = "{}-OldLoc".format(\
                                self.location_isold_cnt.get(devicename))
                    else:
                        attrs[ATTR_POLL_COUNT]  = \
                                int(self.poll_count.get(devicename))

                    kwargs              = {}
                    kwargs['host_name'] = status['name']
                    kwargs['battery']   = int(battery)

                    self._update_device_attributes(devicename, kwargs, attrs)

                    self.seen_this_device_flag[devicename]  = True
                    
                    #DEVICE ATTRS UPDATED
                    log_msg = ("iCloud Device Updated, {}, "
                             "State={}, Interval={}, TravelTime={}, "
                             "Distance={}, NextUpdate={},  Direction={}, "
                             "PollCnt={}, GPSAccuracy={}").format(
                             devicename, self.last_state.get(devicename),
                             attrs[CONF_INTERVAL],
                             attrs[ATTR_WAZE_TIME], attrs[ATTR_DISTANCE],
                             attrs[ATTR_NEXT_UPDATE_TIME],
                             attrs[ATTR_DIR_OF_TRAVEL],
                             attrs[ATTR_POLL_COUNT], attrs[ATTR_GPS_ACCURACY])
                    self._LOGGER_info_msg(log_msg)

                    self.device_being_updated_flag[devicename] = False

                except:
                    log_msg = ("Error Updating Device {}").format(devicename)
                    self._LOGGER_error_msg(log_msg)
                    
                    if status:
                        status = device.status(DEVICESTATUSSET)
                        log_msg = ("►►ICLOUD DEVICE DATA, Status={}").format(
                                    status)
                    else:
                        log_msg = "No device data available"
                    self._LOGGER_error_msg(log_msg)


                log_msg = ("▲▲▲▲▲ UPDATING DEVICE <END> - "
                        "{}/{} ({}) ▲▲▲▲▲ <WARN>").format(self.accountname,
                        devicename, self.current_state.get(devicename))
                self._LOGGER_debug_msg(log_msg)
                   

        except PyiCloudNoDevicesException:
            log_msg = ("No iCloud Devices found")
            self._LOGGER_error_msg(log_msg)


#########################################################
#
#   Calculate polling interval based on zone, distance from home and
#   battery level. Setup triggers for next poll
#
#########################################################

    def _determine_interval(self, devicename, latitude, longitude,
                                battery, gps_accuracy,
                                location_isold_flag):
        """Calculate new interval. Return location based attributes"""

        location_data = self._get_device_distance_data(devicename,
                                    latitude, longitude, gps_accuracy,
                                    location_isold_flag)

        current_zone              = location_data[0]
        dir_of_travel             = location_data[1]
        dist_from_home            = location_data[2]
        dist_from_home_moved      = location_data[3]
        dist_last_poll_move       = location_data[4]
        waze_dist_from_home       = location_data[5]
        calc_dist_from_home       = location_data[6]
        waze_dist_from_home_moved = location_data[7]
        calc_dist_from_home_moved = location_data[8]
        waze_dist_last_poll_moved = location_data[9]
        calc_dist_last_poll_moved = location_data[10]
        waze_time_from_home       = location_data[11]
        last_dist_from_home       = location_data[12]
        last_dir_of_travel        = location_data[13]
        dir_of_trav_msg           = location_data[14]

        log_msg = ("►►DETERMINE INTERVAL <START> ~~{}~~, "
                      "location_data={}").format(devicename, location_data) 
        self._LOGGER_debug_msg(log_msg)

#       the following checks the distance from home and assigns a
#       polling interval in minutes.  It assumes a varying speed and
#       is generally set so it will poll one or twice for each distance
#       group. When it gets real close to home, it switches to once
#       each 15 seconds so the distance from home will be calculated
#       more often and can then be used for triggering automations
#       when you are real close to home. When home is reached,
#       the distance will be 0.

        calc_interval = round(self._km_to_mi(dist_from_home) / 1.5, 0) * 60
        if self.waze_status == WAZE_USED:
            waze_interval = \
                round(waze_time_from_home * 60 * self.travel_time_factor , 0)
        else:
            waze_interval = 0
        interval = 15
        interval_multiplier = 1

        log_method  = ''
        log_msg     = ''
        log_value   = ''
        inzone_flag          = (current_zone != 'not_home')
        inzone_home_flag     = (current_zone == 'home')
        was_inzone_flag      = (self.last_state.get(devicename) != 'not_home')
        was_inzone_home_flag = (self.last_state.get(devicename) == 'home')

        #Note: If current_state is 'near_zone', it is reset to 'not_home' when
        #updating the device_tracker state so it will not trigger a state chng
        if self.state_change_flag.get(devicename):
            #entered 'home' zone
#            if current_zone == 'home':
            if inzone_home_flag:
                interval = 15
                dir_of_travel = 'towards'
                log_method="1-EnterHomeZone"

            #entered 'near_zone' zone if close to 'home' and last is 'not_home'
#            elif (current_zone == 'near_zone' and calc_dist_from_home < 2 and
#                    self.last_state.get(devicename) == 'not_home'):
            elif (current_zone == 'near_zone' and calc_dist_from_home < 2 and
                    not was_inzone_flag):
                interval = 15
                dir_of_travel = 'NearZone'
                log_method="1z-EnterHomeNearZone"

            #entered 'near_zone' zone if close to 'home' and last is 'not_home'
#            elif (self.current_state.get(devicename) == 'near_zone' and
#                    calc_dist_from_home < 2 and
#                    self.last_state.get(devicename) == 'not_home'):
            elif (self.current_state.get(devicename) == 'near_zone' and
                    calc_dist_from_home < 2 and
                    was_inzone_flag):
                interval = 15
                dir_of_travel = 'NearZone'
                log_method="1s-EnterHomeNearZone"

            #exited 'home' zone
#            elif (current_zone == 'not_home' and
#                   self.last_state.get(devicename) == 'home'):
            elif (not inzone_flag and was_inzone_home_flag):
                interval = 300
                dir_of_travel = 'away_from'
                log_method="1-ExitHomeZone"

            #exited 'other' zone
#            elif (current_zone == 'not_home' and
#                   self.last_state.get(devicename) != 'not_home'):
            elif (not inzone_flag and was_inzone_flag):
                interval = 150
                dir_of_travel = 'left_zone'
                log_method="1-ExitZone"

            #entered 'other' zone
            else:
                interval = 150
                log_method="1-ZoneChanged"

            log_msg = 'Zone={}-->{}/{}'.format(self.last_state.get(devicename),
                                current_zone,
                                self.current_state.get(devicename))

        elif (self.poor_gps_accuracy_flag.get(devicename) and
                (inzone_flag and not self.ignore_gps_inzone_flag) and 
                dist_from_home > 2):
            interval   = 60      #poor accuracy, try again in 1 minute
            log_method = '2-PoorGPS'

        elif self.overrideinterval_seconds.get(devicename) > 0:
            interval   = self.overrideinterval_seconds.get(devicename)
            log_method = '3-Override'

#        elif (current_zone == 'home' or dist_from_home < .05):
        elif (inzone_home_flag or dist_from_home < .05):
            interval   = self.inzone_interval
            log_method = '4-InZone'
            log_msg    = 'Zone={}'.format(current_zone)

        elif location_isold_flag:
            if self.location_isold_cnt.get(devicename) % 2 == 0:
                interval = 15       #Old location=try again soon
            elif self.location_isold_cnt.get(devicename) % 10 == 0:
                interval = 600      #Old with lots of retrys, take a break
            log_method   = '5-LoctionOld'
            log_msg      = 'Cnt={}'.format(\
                                self.location_isold_cnt.get(devicename))

        elif current_zone == 'near_zone':
            interval = 15
            log_method = '6-NearZone'
            log_msg    = 'Zone={}, Dir={}'.format(current_zone, dir_of_travel)

#        elif (current_zone != 'not_home' and
#                    self.inzone_interval > waze_interval):
        elif (inzone_flag and self.inzone_interval > waze_interval):
            interval   = self.inzone_interval
            log_method = '7-InZone'
            log_msg    = 'Zone={}'.format(current_zone)

        elif dir_of_travel in ('left_zone', 'unknown'):
            interval = 150
            if inzone_home_flag:
                dir_of_travel = 'away_from'
            else:
                dir_of_travel = 'unknown'
            log_method = '8-NeedInfo'
            log_msg    = 'ZoneLeft={}'.format(current_zone)

        elif dist_from_home < 2.5 and self.went_3km.get(devicename):
            interval   = 15             #1.5 mi=real close and driving
            log_method = '10a-Dist < 2.5km(1.5mi)'

        elif dist_from_home < 3.5:      #2 mi=30 sec
            interval   = 30
            log_method = '10b-Dist < 3.5km(2mi)'

        elif waze_time_from_home > 5 and waze_interval > 0:
            interval   = waze_interval
            log_method = '10c-WazeTime'
            log_msg    = 'TimeFmHome={}'.format(waze_time_from_home)

        elif dist_from_home < 5:        #3 mi=1 min
            interval   = 60
            log_method = '10d-Dist < 5km(3mi)'

        elif dist_from_home < 8:        #5 mi=2 min
            interval   = 120
            log_method = '10e-Dist < 8km(5mi)'

        elif dist_from_home < 12:       #7.5 mi=3 min
            interval   = 180
            log_method = '10f-Dist < 12km(7mi)'

        elif dist_from_home < 20:       #12 mi=10 min
            interval   = 600
            log_method = '10g-Dist < 20km(12mi)'

        elif dist_from_home < 40:       #25 mi=15 min
            interval   = 900
            log_method = '10h-Dist < 40km(25mi)'

        elif dist_from_home > 150:      #90 mi=1 hr
            interval   = 3600
            log_method = '10i-Dist > 150km(90mi)'

        else:
            interval   = calc_interval
            log_method = '12-Calculated'
            log_msg    = 'Value={}/1.5'.format(self._km_to_mi(dist_from_home))

        stationary_cnt = 0

        if dir_of_travel == 'stationary':
            stationary_cnt = self.stationary_cnt.get(devicename) + 1

            if stationary_cnt == 1:
                self._update_dynamic_stationary_zone(devicename,
                        latitude, longitude)
                log_method_im = "●Set.Stationary.Zone"

        elif (dir_of_travel == 'away_from' and
                    not self.distance_method_waze_flag):
            interval_multiplier = 2    #calc-increase timer
            log_method_im = '23-Away(Calc)'

        elif dir_of_travel == 'unknown' and interval > 180:
            interval = 180

        self.stationary_cnt[devicename] = stationary_cnt

        #not stationary, make sure old Stationary Zone location is reset
        if (last_dir_of_travel == 'stationary' and
                dir_of_travel != 'stationary'):
            self._update_dynamic_stationary_zone(devicename, 0, 0)

        #if changed zones on this poll, clear flags and reset multiplier
        if self.state_change_flag.get(devicename):
            self.state_change_flag[devicename] = False
            interval_multiplier = 1

        #Check accuracy again to make sure nothing changed, update counter
        if self.poor_gps_accuracy_flag.get(devicename):
            interval_multiplier = 1
            gps_cnt = self.poor_gps_accuracy_cnt.get(devicename) + 1
            self.poor_gps_accuracy_cnt[devicename] = gps_cnt

        #Real close, final check to make sure interval is not adjusted
        if interval <= 60 or \
                (battery > 0 and battery <= 33 and interval >= 120):
            interval_multiplier = 1

        interval     = interval * interval_multiplier
        interval, x  = divmod(interval, 15)
        interval     = interval * 15
        interval_str = self._seconds_to_time_str(interval)

        interval_debug_msg = "●Interval={} ({}, {}), ●DirOfTrav={}, " \
                             "●State={}/{}".\
                    format(interval_str, log_method, log_msg, dir_of_trav_msg,
                    self.current_state.get(devicename),
                    self.last_state.get(devicename))

        if interval_multiplier != 1:
           interval_debug_msg = "{}, Multiplier={}({})".format(\
                    interval_debug_msg, interval_multiplier, log_method_im)

        #check if next update is past midnight (next day), if so, adjust it
        next_poll = self.this_update_seconds + interval
        if next_poll >= 86400:
            next_poll -= 86400
            self.poll_count_yesterday[devicename] = self.poll_count[devicename]
            self.poll_count[devicename] = 1

        # Update all dates and other fields
        self.interval_seconds[devicename]    = interval
        self.next_update_seconds[devicename] = next_poll
        self.next_update_time[devicename]    = \
                    self._seconds_to_time(next_poll)
        self.last_update_time[devicename]    = \
                    self._seconds_to_time(self.this_update_seconds)
        self.last_update_seconds[devicename] = self.this_update_seconds
        self.interval_str[devicename]        = interval_str

        #if more than 3km(1.8mi) then assume driving, used later above
        if dist_from_home > 3:                # 1.8 mi
            self.went_3km[devicename] = True
        elif dist_from_home < .03:            # home, reset flag
             self.went_3km[devicename] = False

        info = self._setup_info_attr(devicename, battery, gps_accuracy,
                                stationary_cnt, dist_last_poll_move,
                                current_zone, location_isold_flag)

        log_msg = ("►►INTERVAL FORMULA, {}").format(interval_debug_msg) 
        self._LOGGER_debug_msg(log_msg)

        if 'interval' not in self.debug_control:
            interval_debug_msg = ''

        log_msg = ("►►DETERMINE INTERVAL <COMPLETE>,  ~~{}~~, "
                      "This poll: {}({}), Last Update: {}({}), "
                      "Next Update: {}({}),  Interval: {}*{}, "
                      "OverrideInterval={}, DistTraveled={}").format(
                      devicename,
                      self._seconds_to_time(self.this_update_seconds),
                      self.this_update_seconds,
                      self.last_update_time.get(devicename),
                      self.last_update_seconds.get(devicename),
                      self.next_update_time.get(devicename),
                      self.next_update_seconds.get(devicename),
                      self.interval_str.get(devicename),
                      interval_multiplier,
                      self.overrideinterval_seconds.get(devicename),
                      dist_last_poll_move) 
        self._LOGGER_debug_msg(log_msg)

        #if 'NearZone' zone, do not change the state
        if current_zone == 'near_zone':
            current_zone = 'not_home'

        self.last_state[devicename] = current_zone
        attrs = {}

        log_msg = ("►►DIR OF TRAVEL ATTRS, Direction={}, LastDir={}, "
                       "Dist={}, LastDist={}, SelfDist={}, Moved={},"
                       "WazeMoved={}").format(
                       dir_of_travel, last_dir_of_travel, dist_from_home,
                       last_dist_from_home, self.dist.get(devicename),
                       dist_from_home_moved, waze_dist_from_home_moved) 
        self._LOGGER_debug_msg(log_msg)

        #if poor gps and moved less than 1km, redisplay last distances
        if (self.poor_gps_accuracy_flag.get(devicename) and
                        dist_last_poll_move < 1):
            dist_from_home      = self.dist.get(devicename)
            waze_dist_from_home = self.waze_dist.get(devicename)
            calc_dist_from_home = self.calc_dist.get(devicename)
            waze_time_msg       = self.waze_time.get(devicename)

        else:
            waze_time_msg       = self._format_waze_time_msg(devicename,
                                            waze_time_from_home,
                                            waze_dist_from_home)
            dist_from_home      = self._km_to_mi(dist_from_home)
            waze_dist_from_home = self._km_to_mi(waze_dist_from_home)
            calc_dist_from_home = self._km_to_mi(calc_dist_from_home)

            #save for next poll if poor gps
            self.dist     [devicename] = dist_from_home
            self.waze_dist[devicename] = waze_dist_from_home
            self.waze_time[devicename] = waze_time_msg
            self.calc_dist[devicename] = calc_dist_from_home

        attrs[CONF_INTERVAL]           = interval_str
        attrs[ATTR_LAST_UPDATE_TIME]   = \
                    self._seconds_to_time(self.this_update_seconds)
        attrs[ATTR_NEXT_UPDATE_TIME]   = \
                    self._seconds_to_time(next_poll)

        attrs[ATTR_WAZE_TIME]         = waze_time_msg
        attrs[ATTR_DISTANCE]          = dist_from_home
        attrs[ATTR_CALC_DISTANCE]     = calc_dist_from_home
        attrs[ATTR_WAZE_DISTANCE]     = waze_dist_from_home
        attrs[ATTR_DIR_OF_TRAVEL]     = dir_of_travel

        attrs[ATTR_GPS_ACCURACY]      = gps_accuracy
        if self.hide_gps_coordinates and current_zone == 'not_home':
            attrs[ATTR_LATITUDE]      = 90
            attrs[ATTR_LONGITUDE]     = 0
        else:
            attrs[ATTR_LATITUDE]      = latitude
            attrs[ATTR_LONGITUDE]     = longitude

        attrs[ATTR_INFO]              = interval_debug_msg + info

        log_msg = ("►►DETERMINE INTERVAL <EXIT> ~~{}~~, "
                      "location_attributes={}").format(devicename, attrs) 
        self._LOGGER_debug_msg(log_msg)

        return attrs

#########################################################
#
#   UPDATE DEVICE ATTRIBUTESNS
#
#########################################################
    def _get_current_state(self, devicename):
        """
        Get current state of the device_tracker entity
        (home, away, other state)
        """

        entity_id = self._format_entity_id(devicename)
        try:
            device_state = self.hass.states.get(entity_id).state

            if device_state:
                return device_state

            return 'not_home'

        except:
            return 'unknown'

#--------------------------------------------------------------------
    def _update_device_attributes(self, devicename, kwargs: str=None,
                        attrs: str=None):
        """
        Update the device and attributes with new information
        On Entry, kwargs = {} or contains the base attributes
        """

        if not kwargs:
            kwargs = {}
        if not attrs:
            attrs  = {}

        #Capitalize and reformat state if not Home or Away
        state = self.last_state.get(devicename)
        if state not in ('home', 'not_home'):
            state = state.replace('_', ' ', 99)
            state = state.title()
            self.last_state[devicename] = state

#        if self.current_state.get(devicename).lower() == 'unknown':
        self.current_state[devicename] = state

        kwargs['dev_id']         = devicename
        kwargs['location_name']  = state
        kwargs[ATTR_ATTRIBUTES]  = attrs

        self.see(**kwargs)

        return
#--------------------------------------------------------------------
    def _get_device_attributes(self, devicename):
        """ Get attributes of the device """

        try:
            entity_id = self._format_entity_id(devicename)

            return self.hass.states.get(entity_id).attributes
        except:
            return "<<<No attributes>>>"
#--------------------------------------------------------------------
    def _get_current_zone(self, devicename, latitude, longitude):
        """ Get current zone of the device based on the location """

        current_zone = active_zone(self.hass, latitude, longitude)

        #Example current_zone:
        #<state zone.home=zoning; hidden=True, latitude=27.726639,
        #longitude=-80.3904565, radius=40.0, friendly_name=Home, icon=mdi:home,
        #beacon=uuid=9AC56DEE-E6F3-4446-A2BC-9A68D06BC0BB, major=1, minor=1

#        log_msg = ("►►GET CURRENT ZONE, Zone={}, Lat={}, Long={}, "
#                        "TriggerState={}").format(
#                    current_zone, latitude, longitude,
#                    self.current_state.get(devicename)) 
#        self._LOGGER_debug_msg(log_msg)

        if current_zone:
            current_zone = current_zone.attributes.get('friendly_name')

            #Override 'NearZone' zone name, will be reset later to not_home
            if 'nearzone' in current_zone.lower():
                current_zone = 'near_zone'
        else:
            current_zone = 'not_home'

        log_msg = ("►►GET CURRENT ZONE, Zone={}, Lat={}, Long={}, "
                        "TriggerState={}").format(
                    current_zone, latitude, longitude,
                    self.current_state.get(devicename))
        self._LOGGER_debug_msg(log_msg)

        return current_zone.lower()
#--------------------------------------------------------------------
    def _wait_if_update_in_process(self, arg_devicename=None):
        #An update is in process, must wait until done
        wait_cnt = 0
        while self.update_in_process_flag:
            wait_cnt += 1
            if arg_devicename:
                #now_seconds = dt_util.now().strftime('%-S')
                attrs                = {}
                attrs[CONF_INTERVAL] = ("►WAIT-{}").format(wait_cnt)  #now_seconds)

                kwargs = {}
                self._update_device_attributes(arg_devicename, kwargs, attrs)
            time.sleep(2)

#--------------------------------------------------------------------
    def _update_dynamic_stationary_zone(self, devicename,
                latitude: float, longitude: float):
        """ Create/update dynamic stationary zone """

        zone_name = devicename + "_stationary"

        attrs = {}
        attrs["hidden"]        = True
        attrs["name"]          = zone_name
        attrs["friendly_name"] = "Stationary"  #self.friendly_name.get(devicename)
        attrs["radius"]        = round(self.zone_home_radius*1000, 0)
        attrs["icon"]          = "mdi:account"
        attrs["latitude"]      = round(latitude, 6)
        attrs["longitude"]     = round(longitude, 6)

        self.hass.states.set("zone." + zone_name, "zoning", attrs)

        log_msg = ("Update Stationary Zone for {}, Lat={}, Long={}",
                    devicename, latitude, longitude) 
        self._LOGGER_info_msg(log_msg)

#--------------------------------------------------------------------
    def _format_entity_id(self, devicename):

        return '{}.{}'.format(DOMAIN, devicename)
#--------------------------------------------------------------------
    def _TRACE_ATTRS(self, devicename, lineno):
        all_attrs  = self._get_device_attributes(devicename)
        log_msg = ("►►Attrs►►{}={}").format(lineno, all_attrs) 
        self._LOGGER_debug_msg(log_msg)

        if len(all_attrs) ==  0:
            log_msg = ("►►►►►► Attrs Empty ►►►►►►") 
            self._LOGGER_debug_msg(log_msg)

        return
#########################################################
#
#   UPDATE DEVICE LOCATION & INFORMATION ATTRIBUTE FUNCTIONS
#
#########################################################

    def _get_device_distance_data(self, devicename, latitude, longitude,
                                gps_accuracy, location_isold_flag):
        """ Determine the location of the device.
            Returns:
                - current_zone (current zone from lat & long)
                  set to 'home' if distance < home zone radius
                - dist_from_home (mi or km)
                - dist_traveled (since last poll)
                - dir_of_travel (towards, away_from, stationary, in_zone,
                                       left_zone, near_home)
        """

        log_msg = ("►►GET DEVICE DISTANCE/DIRECTION ~~{}~~").format(devicename) 
        self._LOGGER_debug_msg(log_msg)

        last_dir_of_travel     = 'unknown'
        last_dist_from_home    = 0
        last_waze_time         = 0
        last_lat               = self.zone_home_lat
        last_long              = self.zone_home_long

        if self.seen_this_device_flag.get(devicename):
            attrs = self._get_device_attributes(devicename)

            log_msg = ("►►ATTRIBUTES ~~{}~~ {}").format(devicename,
                            attrs) 
            self._LOGGER_debug_msg(log_msg)

            if attrs[ATTR_DISTANCE] is not None:
                last_dist_from_home_s  = attrs[ATTR_DISTANCE]
                last_dist_from_home    = \
                                self._mi_to_km(float(last_dist_from_home_s))

                last_waze_time     = attrs[ATTR_WAZE_TIME]
                last_dir_of_travel = attrs[ATTR_DIR_OF_TRAVEL]
                last_dir_of_travel = last_dir_of_travel.replace('*', '', 99)
                last_lat           = self.last_lat.get(devicename)
                last_long          = self.last_long.get(devicename)

        #get last interval
        interval_str = self.interval_str.get(devicename)
        interval = self._time_str_to_seconds(interval_str)

        this_lat  = latitude
        this_long = longitude

        current_zone = self._get_current_zone(devicename, this_lat, this_long)

        log_msg = ("►►LAT-LONG GPS INITIALIZED >>> {}, "
              "this_lat={}, this_long={}, "
              "last_lat={}, last_long={}, "
              "latitude={}, longitude={}, "
              "GPS.Accur={}, GPS.Threshold={}").format(current_zone,
              this_lat, this_long, last_lat, last_long, latitude, longitude,
              gps_accuracy, self.gps_accuracy_threshold) 
        self._LOGGER_debug_msg(log_msg)

        # Get Waze distance & time
        #   Will return [error, 0, 0, 0] if error
        #               [out_of_range, dist, time, info] if
        #                           last_dist_from_home >
        #                           last distance from home
        #               [ok, 0, 0, 0]  if zone=home
        #               [ok, distFmHome, timeFmHome, info] if OK

        calc_dist_from_home       = self._calc_distance(this_lat, this_long,
                                    self.zone_home_lat, self.zone_home_long)
        calc_dist_last_poll_moved = self._calc_distance(last_lat, last_long,
                                    this_lat, this_long)
        calc_dist_from_home_moved = round(calc_dist_from_home
                                     - last_dist_from_home, 2)

        #Make sure distance and zone are correct for 'home'
        if calc_dist_from_home < .05 or current_zone == 'home':
            current_zone              = 'home'
            calc_dist_from_home       = 0
            calc_dist_last_poll_moved = 0
            calc_dist_from_home_moved = 0

        #Use Calc if close to home, Waze not accurate when close
        if calc_dist_from_home <= 1:
            self.waze_status          = WAZE_PAUSED
            waze_dist_from_home       = calc_dist_from_home
            waze_time_from_home       = 0
            waze_dist_last_poll_moved = calc_dist_last_poll_moved
            waze_dist_from_home_moved = calc_dist_from_home_moved

        elif self.distance_method_waze_flag:
            self.waze_status          = WAZE_USED
            waze_dist_time_info = self._get_waze_data(devicename,
                                            this_lat, this_long,
                                            last_lat, last_long, current_zone,
                                            last_dist_from_home)
            self.waze_status          = waze_dist_time_info[0]
            waze_dist_from_home       = waze_dist_time_info[1]
            waze_time_from_home       = waze_dist_time_info[2]
            waze_dist_last_poll_moved = waze_dist_time_info[3]
            waze_dist_from_home_moved = round(waze_dist_from_home
                                        - last_dist_from_home, 2)

        #don't reset data if poor gps, use the best we have
#        if ((current_zone == 'home' or dist_from_home < .05) and
#                    not self.poor_gps_accuracy_flag.get(devicename)):
        if current_zone == 'home':
            distance_method      = 'Home'
            dist_from_home       = 0
            dist_last_poll_moved = 0
            dist_from_home_moved = 0
        elif self.waze_status == WAZE_USED:
            distance_method      = 'Waze'
            dist_from_home       = waze_dist_from_home
            dist_last_poll_moved = waze_dist_last_poll_moved
            dist_from_home_moved = waze_dist_from_home_moved
        else:
            distance_method      = 'Calc'
            dist_from_home       = calc_dist_from_home
            dist_last_poll_moved = calc_dist_last_poll_moved
            dist_from_home_moved = calc_dist_from_home_moved

        self.last_lat[devicename]  = this_lat
        self.last_long[devicename] = this_long

        log_msg = ("►►DISTANCES CALCULATED, "
              "Zone={}, Method={}, ZoneRadius={}, LastDistFmHome={} "
              "WazeStatus={}").format(
              current_zone, distance_method, self.zone_home_radius,
              last_dist_from_home, self.waze_status) 
        self._LOGGER_debug_msg(log_msg)
        log_msg = ("►►DISTANCES ...Waze    >>>, "
              "WazeFromHome={}, WazeLastPollMoved={}, WazeFromHomeMoved={}, "
              "WazeTimeFmHome={}").format(
              waze_dist_from_home, waze_dist_last_poll_moved,
              waze_dist_from_home_moved, waze_time_from_home) 
        self._LOGGER_debug_msg(log_msg)
        log_msg = ("►►DISTANCES ...Calc    >>>, "
              "CalcFromHome={}, CalcLastPollMoved={}, CalcFromHomeMoved={}").format(
              calc_dist_from_home, calc_dist_last_poll_moved,
              calc_dist_from_home_moved) 
        self._LOGGER_debug_msg(log_msg)

        #if didn't move far enough to determine towards or away_from,
        #keep the current distance and add it to the distance on the next
        #poll
        if (dist_from_home_moved > -.3 and dist_from_home_moved < .3):
            dist_from_home_moved += \
                    self.dist_from_home_small_move_total.get(devicename)
            self.dist_from_home_small_move_total[devicename] = \
                    dist_from_home_moved
        else:
             self.dist_from_home_small_move_total[devicename] = 0

        dir_of_travel   = ''
        dir_of_trav_msg = ''
        if self.poor_gps_accuracy_flag.get(devicename):
            dir_of_travel   = 'Poor.GPS'
            dir_of_trav_msg = ("Poor.GPS={}").format(gps_accuracy)

        elif current_zone not in ('not_home', 'near_zone'):
            dir_of_travel   = 'in_zone'
            dir_of_trav_msg = ("Zone={}").format(current_zone)

        elif last_dir_of_travel == "in_zone":
            dir_of_travel   = 'left_zone'
            dir_of_trav_msg = ("LastZone={}").format(last_dir_of_travel)

        elif dist_from_home_moved <= -.3:            #.18 mi
            dir_of_travel   = 'towards'
            dir_of_trav_msg = ("Dist={}").format(dist_from_home_moved)

        elif dist_from_home_moved >= .3:             #.18 mi
            dir_of_travel   = 'away_from'
            dir_of_trav_msg = ("Dist={}").format(dist_from_home_moved)

        elif (abs(dist_from_home_moved) < .06 and
                dist_from_home > 3 and last_dir_of_travel != 'unknown' and
                'zone' not in last_dir_of_travel and
                not location_isold_flag):
#                last_dir_of_travel in \
#                    'stationary, towards, away_from, left_zone':
            dir_of_travel   = 'stationary'
            dir_of_trav_msg = "LastDirTrav={}, DistFmHome={}, " \
                                  "Moved={}, State={}, isOld={}". \
                                  format(last_dir_of_travel,
                                  dist_from_home, dist_from_home_moved,
                                  self.last_state.get(devicename),
                                  location_isold_flag)
        else:
            #didn't move far enough to tell current direction
            dir_of_travel   = ("{}*").format(last_dir_of_travel)
            dir_of_trav_msg = ("Moved={}").format(dist_from_home_moved)

        dir_of_trav_msg = ("{} ({})").format(dir_of_travel, dir_of_trav_msg)

        log_msg = ("►►DIR OF TRAVEL DETERMINED, {}").format(dir_of_trav_msg) 
        self._LOGGER_debug_msg(log_msg)

        log_msg = ("►►GET DEVICE DISTANCE/DIRECTION RESULTS ~~{}~~, "
                    "CurrentZone={}, DistFmHome={}, DistFmHomeMoved={}, "
                    "DistLastPollMoved={}").format(
                    devicename, current_zone, dist_from_home,
                    dist_from_home_moved, dist_last_poll_moved) 
        self._LOGGER_debug_msg(log_msg)

        return (current_zone, dir_of_travel,
                dist_from_home, dist_from_home_moved, dist_last_poll_moved,
                waze_dist_from_home, calc_dist_from_home,
                waze_dist_from_home_moved, calc_dist_from_home_moved,
                waze_dist_last_poll_moved, calc_dist_last_poll_moved,
                waze_time_from_home, last_dist_from_home, last_dir_of_travel,
                dir_of_trav_msg)

#--------------------------------------------------------------------
    def _setup_info_attr(self, devicename, battery, gps_accuracy, \
                            stationary_cnt, dist_last_poll_moved, \
                            current_zone, location_isold_flag):

        """ Initialize info attribute with battery information
            Returns:
                - info
        """

        if self.overrideinterval_seconds.get(devicename) > 0:
            info = '●Overriding.Interval'
        else:
            info = ''

        #Symbols = ▶¦▶ ●►◄▬▲▼◀▶ oPhone=►▶

        if self.write_log_debug_msgs_flag:
            info = '{} ●Debug.log-on'.format(info)

        if gps_accuracy > int(self.gps_accuracy_threshold):
            info = '{} ●Poor.GPS.Accuracy-{}({})'.format(info, gps_accuracy,
                        self.poor_gps_accuracy_cnt.get(devicename))
            if current_zone != 'not_home' and self.ignore_gps_accuracy_inzone:
                info = '{}-Ignored'.format(info)

        if current_zone == 'not_home' and dist_last_poll_moved > 0:
            info = '{} ●Traveled-{}{}'.format(info, dist_last_poll_moved,
                        self.unit_of_measurement)

        if current_zone == 'near_zone':
            info = '{} ●NearZone'.format(info)

        if battery > 0:
            info = '{} ●Battery-{}%'.format(info, battery)

        if stationary_cnt >0:
            info = '{} ●Stationary.Cnt-{}'.format(info, stationary_cnt)

        isold_cnt = self.location_isold_cnt.get(devicename)
        if isold_cnt > 0:
            info = '{} ●Old.Location-{}'.format(info, isold_cnt)

        if self.distance_method_waze_flag:
            if self.waze_status == WAZE_PAUSED:
                info = '{} ●Waze.Paused'.format(info)
            elif self.waze_status == WAZE_ERROR:
                info = '{} ●Waze.Error'.format(info)
            elif self.waze_status == WAZE_OUT_OF_RANGE:
                info = '{} ●Waze.Range-({}-{})'.format(info,
                            self._km_to_mi(self.waze_min_distance),
                            self._km_to_mi(self.waze_max_distance))

        return info
#--------------------------------------------------------------------
    def _retry_setup_location_data(self, device, devicename, location):
        """
        See if location data isOld=true. If so, sleep for 2 seconds
        and then get data from icloud again. Do this 5 times. If location
        isOld is still true, return to the update_data routine with
        the location data last found.
        """

        log_msg = ("►►RETRY SET LOCATION DATA STARTED ~~{}~~, Device={}",
                devicename, device) 
        self._LOGGER_debug_msg(log_msg)

        location_retry_cnt = 0
        isold_flag = True
        while isold_flag and location_retry_cnt < 4:
            try:
                time.sleep(2)
                location_retry_cnt += 1
                status   = device.status(DEVICESTATUSSET)
                location = self.tracked_devices[devicename].location()
 #               location = status['location']
                isold_flag = location['isOld']
                if 'old' in self.debug_control:
                    isold_flag = True     #debug

                log_msg = ("►►RETRY SET LOCATION DATA({}) ~~{}~~, "
                              "Timestamp={}({}), Next Update: {}({}), "
                              "This poll: {}({}), isOld={}, "
                              "Location={}").format(
                              location_retry_cnt, devicename,
                              self._timestamp_to_time(location['timeStamp']),
                              location['timeStamp'],
                              self.next_update_time.get(devicename),
                              self.next_update_seconds.get(devicename),
                              self._seconds_to_time(self.this_update_seconds),
                              self.this_update_seconds,
                              location['isOld'], location) 
                self._LOGGER_debug_msg(log_msg)
            except:
                log_msg = ("►►RETRY SET LOCATION DATA-Unknown "
                              "Exception, Cnt={}").format(location_retry_cnt) 
                self._LOGGER_debug_msg(log_msg)
        return location


#########################################################
#
#   DEVICE SETUP SUPPORT FUNCTIONS
#
#########################################################

    def _check_tracking_this_device(self, devicename, device_type):
        ''' Validate device tracking via include/exclude filters '''

        # An entity will not be created by see() when track=false in
        # 'known_devices.yaml', but we need to see() it at least once

        entity_id = self._format_entity_id(devicename)
        
        #devicename in 'excluded_devices' parameter ==> Don't Track
        if devicename in self.exclude_devices:
            log_msg = ("Not tracking {}/{}, Failed "
                        "'exclude_devices' filter ({})").format(
                        self.accountname, devicename, self.exclude_devices) 
            self._LOGGER_info_msg(log_msg)

            return False

        #devicename in 'include_devices' parameter ==> Track
        elif devicename in self.include_devices:
            log_msg = ("Tracking {}/{}, Passed "
                        "'include_devices' filter ({})").format(
                        self.accountname, devicename, self.include_devices) 
            self._LOGGER_info_msg(log_msg)

            return True

        #devicetype in 'include_device_types' parameter ==> Track
        elif device_type in self.include_device_types:
            log_msg = ("Tracking {}/{}, Passed "
                        "'include_device_type' filter ({})").format(
                        self.accountname, devicename, device_type) 
            self._LOGGER_info_msg(log_msg)

            return True

        #devicetype in 'exclude_device_types' parameter ==> Don't Track
        elif device_type in self.exclude_device_types:
            log_msg = ("Not tracking {}/{}, Failed "
                         "'exclude_device_types' filter ({})").format(
                         self.accountname, devicename,
                         self.exclude_device_types) 
            self._LOGGER_info_msg(log_msg)

            return False

        #neither 'include_device_types' nor 'exclude_device_types' parameter
        #and devicename not in 'include_devices' parameter    ==> Don't Track
        elif (not self.include_device_types and
                not self.exclude_device_types and
                self.include_devices):
            log_msg = ("Not tracking {}/{}, Failed "
                        "'include devices' filter ({})").format(
                        self.accountname, devicename,
                        self.include_devices) 
            self._LOGGER_info_msg(log_msg)

            return False

        #'include_device_types parameter and
        #devicename in 'exclude_device'                    ==> Don't Track
        elif (self.include_device_types and
                devicename in self.exclude_devices):
            log_msg = ("Not tracking {}/{}, Failed "
                        "'include_device_types' filter ({})").format(
                        self.accountname, devicename,
                        self.include_device_types) 
            self._LOGGER_info_msg(log_msg)

            return False

        #unknown device ==> Don't Track
        elif entity_id is None:
            log_msg = ("Not tracking {}/{}, Unknown device").format(
                        self.accountname, devicename) 
            self._LOGGER_info_msg(log_msg)

            return False

        log_msg = ("Not tracking {}/{}, Did not match any tracking "
                    "filters, Type={}").format(self.accountname, devicename, device_type) 
        self._LOGGER_info_msg(log_msg)

        return False

#--------------------------------------------------------------------
    def _check_isold_status(self, devicename, arg_location_isold_flag,
                            time_stamp):
        """
        Check if the location isold flag is set by the iCloud service or if
        the current timestamp is the same as the timestamp on the previous
        poll. If so, we want to retry locating device
        5 times and then use normal interval. But keep track of count for
        determining the interval.
        """
        isold_cnt = 0
        location_isold_flag = arg_location_isold_flag
        if 'old' in self.debug_control:
            location_isold_flag = True   #debug

#        last_attrs       = self._get_device_attributes(devicename)
#        last_time_stamp  = last_attrs[ATTR_LAST_LOCATED]
        time_test_secs   = self.this_update_seconds - 90
        time_stamp_secs  = self._timestamp_to_seconds(time_stamp)

        if time_stamp_secs < time_test_secs:
            location_isold_flag = True

        if location_isold_flag:
            isold_cnt = self.location_isold_cnt.get(devicename) + 1
            self.location_isold_cnt[devicename] = isold_cnt

            if isold_cnt % 5 == 0:
                location_isold_flag = False
                self.location_isold_cnt[devicename] = 0

        elif self.location_isold_cnt.get(devicename) > 0:
            self.location_isold_cnt[devicename] = 0

        return location_isold_flag, isold_cnt
#--------------------------------------------------------------------

    def _log_device_status_attrubutes(self, status):

        """
        Status={'batteryLevel': 1.0, 'deviceDisplayName': 'iPhone X',
        'deviceStatus': '200', 'name': 'Gary-iPhone',
        'deviceModel': 'iphoneX-1-2-0', 'rawDeviceModel': 'iPhone10,6',
        'deviceClass': 'iPhone',
        'id':'qyXlfsz1BIOGxcqDxDleX63Mr63NqBxvJcajuZT3y05RyahM3/OMpuHYVN
        SUzmWV', 'lowPowerMode': False, 'batteryStatus': 'NotCharging',
        'fmlyShare': False, 'location': {'isOld': False,
        'isInaccurate': False, 'altitude': 0.0, 'positionType': 'GPS'
        'latitude': 27.726843548976, 'floorLevel': 0,
        'horizontalAccuracy': 48.00000000000001,
        'locationType': '', 'timeStamp': 1539662398966,
        'locationFinished': False, 'verticalAccuracy': 0.0,
        'longitude': -80.39036092533418}, 'locationCapable': True,
        'locationEnabled': True, 'isLocating': True, 'remoteLock': None,
        'activationLocked': True, 'lockedTimestamp': None,
        'lostModeCapable': True, 'lostModeEnabled': False,
        'locFoundEnabled': False, 'lostDevice': None,
        'lostTimestamp': '', 'remoteWipe': None,
        'wipeInProgress': False, 'wipedTimestamp': None, 'isMac': False}
        """

        log_msg = ("►►DEVICE DATA, STATUS={}, ▶deviceDisplayName={}").format(
                status, status['deviceDisplayName']) 
        self._LOGGER_debug_msg(log_msg)

        location = status['location']

        log_msg = ("►►DEVICE STATUS, ●deviceDisplayName={}, "
                "●deviceStatus={}, ●name={}, ●deviceClass={}, "
                "●batteryLevel={}, ●batteryStatus={}, "
                "●isOld={}, ●positionType={}, ●latitude={}, ●longitude={}, "
                "●horizontalAccuracy={}, ●timeStamp={}({})").format(
                status['deviceDisplayName'], status['deviceStatus'],
                status['name'], status['deviceClass'],
                status['batteryLevel'], status['batteryStatus'],
                location['isOld'], location['positionType'],
                location['latitude'], location['longitude'],
                location['horizontalAccuracy'], location['timeStamp'],
                self._timestamp_to_time(location['timeStamp']))
        self._LOGGER_debug_msg(log_msg)
        return True

#########################################################
#
#   WAZE ROUTINES
#
#########################################################

    def _get_waze_data(self, devicename,
                            this_lat, this_long, last_lat,
                            last_long, current_zone, last_dist_from_home):

        if current_zone == 'home':
            return (WAZE_USED, 0, 0, 0)
        elif self.waze_status == WAZE_PAUSED:
            return (WAZE_PAUSED, 0, 0, 0)

        #Last distance outside of Waze outside of range
#        elif (last_dist_from_home >= self.waze_max_distance) or \
#             (last_dist_from_home <= self.waze_min_distance):
#            return (WAZE_OUT_OF_RANGE,0, 0, 0)

        waze_from_home = self._get_waze_distance(devicename,
                                this_lat, this_long,
                                self.zone_home_lat, self.zone_home_long)

        waze_from_last_poll = self._get_waze_distance(devicename,
                                last_lat, last_long,
                                this_lat, this_long)

        waze_status         =  waze_from_home[0]
        waze_dist_from_home = self._round_to_zero(waze_from_home[1])
        waze_time_from_home = self._round_to_zero(waze_from_home[2])
        waze_dist_last_poll = self._round_to_zero(waze_from_last_poll[1])

        if waze_dist_from_home == 0:
            waze_time_from_home = 0
        else:
            waze_time_from_home = self._round_to_zero(waze_from_home[2])

        if ((waze_dist_from_home > self.waze_max_distance) or
             (waze_dist_from_home < self.waze_min_distance)):

            waze_status = WAZE_OUT_OF_RANGE

        log_msg = ("►►WAZE DISTANCES CALCULATED>, "
          "Status={}, DistFromHome={}, TimeFromHome={}, "
          " DistLastPoll={}, "
          "WazeFromHome={}, WazeFromLastPoll={}").format(
          waze_status, waze_dist_from_home, waze_time_from_home,
          waze_dist_last_poll, waze_from_home, waze_from_last_poll) 
        self._LOGGER_debug_msg(log_msg)

        return (waze_status, waze_dist_from_home, waze_time_from_home,
                waze_dist_last_poll)

#--------------------------------------------------------------------
    def _get_waze_distance(self, devicename, from_lat, from_long, to_lat,
                        to_long):
        """
        See https://github.com/kovacsbalu/WazeRouteCalculator
        Region=EU (Europe), US or NA (North America), IL (Israel)

        Example:
            from_address = 'Budapest, Hungary'
            to_address = 'Gyor, Hungary'
            region = 'EU'
            route = WazeRouteCalculator.WazeRouteCalculator(from_address, to_address, region)
            route.calc_route_info()
            route_time, route_distance = route.calc_route_info()

        Example output:
            From: Budapest, Hungary - to: Gyor, Hungary
            Time 72.42 minutes, distance 121.33 km.
            (72.41666666666667, 121.325)

        See https://github.com/home-assistant/home-assistant/blob
        /master/homeassistant/components/sensor/waze_travel_time.py
        """

        try:
            from_loc = '{},{}'.format(from_lat, from_long)
            to_loc   = '{},{}'.format(to_lat, to_long)

            route = WazeRouteCalculator.WazeRouteCalculator(
                    from_loc, to_loc, self.waze_region)

            if route:
                route_time, route_distance = \
                        route.calc_route_info(self.waze_realtime)
                route_time     = round(route_time, 0)
                route_distance = round(route_distance, 2)

            #no route information so use last data calculated but adjust
            #waze time by last interval. Calculate time percentage changed
            #based on interval and calculate adjusted distance. Maybe it will
            #be close.
            else:
                interval_min   = self.interval_seconds.get(devicename) / 60
                route_time     = self.waze_time.get(devicename) - interval_min
                dist_factor    = route_time / interval_min
                route_distance = self.waze_dist.get(devicename) * interval_min

            return (WAZE_USED, route_distance, route_time)

        except WazeRouteCalculator.WRCError as exp:
            log_msg = ("►►Error on retrieving data: {}").format(exp) 
            self._LOGGER_error_msg(log_msg)

            return (WAZE_ERROR, 0, 0)

        except KeyError:
            log_msg = ("►►Error retrieving data from server") 
            self._LOGGER_error_msg(log_msg)

            return (WAZE_ERROR, 0, 0)
#--------------------------------------------------------------------
    def _format_waze_time_msg(self, devicename, waze_time_from_home,
                                waze_dist_from_home):
        """ return the message displayed in the waze time field ►►   """

        if (waze_dist_from_home == 0 or
                    self.waze_status == WAZE_NOT_USED or
                    self.waze_status == WAZE_PAUSED):
            waze_time_msg = ''
        elif self.poor_gps_accuracy_flag.get(devicename):
            waze_time_msg = '●BADGPS●'
        elif self.waze_status == WAZE_OUT_OF_RANGE:
            waze_time_msg = '●RANGE●'
        elif self.waze_status == WAZE_USED:   #Waze used on this poll

            #Display time to the nearest minute if more than 3 min away
            t = waze_time_from_home * 60
            r = 0
            if t > 180:
              t, r = divmod(t, 60)
              t = t + 1 if r > 30 else t
              t = t * 60

            waze_time_msg = self._seconds_to_time_str(t)

        elif self.waze_status == WAZE_ERROR:
            waze_time_msg = '●ERROR●'

        return waze_time_msg
#########################################################
#
#   _LOGGER MESSAGE ROUTINES
#
#########################################################

    def _LOGGER_info_msg(self, msg):
        _LOGGER.info(msg)
        
    def _LOGGER_error_msg(self, msg):
        _LOGGER.error(msg)

    def _LOGGER_debug_msg(self, msg):
        if self.write_log_debug_msgs_flag:
            _LOGGER.info(msg)
        else:
            _LOGGER.debug(msg)


#########################################################
#
#   TIME & DISTANCE UTILITY ROUTINES
#
#########################################################

    def _seconds_to_time(self, seconds):
        """ Convert seconds to hh:mm:ss """
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if self.unit_of_measurement == 'mi' and h > 12:
            h = h - 12
        h = 12 if h == 0 else h

        return "%d:%02d:%02d" % (h, m, s)

#--------------------------------------------------------------------
    @staticmethod
    def _time_to_seconds(hhmmss):
        """ Convert hh:mm:ss into seconds """
        if hhmmss:
            s = hhmmss.split(":")
            tts_seconds = int(s[0]) * 3600 + int(s[1]) * 60 + int(s[2])
        else:
            tts_seconds = 0

        return tts_seconds

#--------------------------------------------------------------------
    @staticmethod
    def _seconds_to_time_str(time_sec):
        """ Create the time string from seconds """
        if time_sec < 60:
            time_str = str(time_sec) + " sec"
        elif time_sec < 3600:
            time_str = str(round(time_sec/60, 1)) + " min"
        elif time_sec == 3600:
            time_str = "1 hr"
        else:
            time_str = str(round(time_sec/3600, 1)) + " hrs"

        # xx.0 min/hr --> xx min/hr
        time_str = time_str.replace('.0 ', ' ')
        return time_str

#--------------------------------------------------------------------
    @staticmethod
    def _time_str_to_seconds(time_str='30 min'):
        """
        Calculate the seconds in the time string.
        The time attribute is in the form of '15 sec' ',
        '2 min', '60 min', etc
        """

        s1 = str(time_str).replace('_', ' ') + " min"
        time_part = float((s1.split(" ")[0]))
        text_part = s1.split(" ")[1]

        if text_part == 'sec':
            time_sec = time_part
        elif text_part == 'min':
            time_sec = time_part * 60
        elif text_part == 'hrs':
            time_sec = time_part * 3600
        elif text_part in ('hr', 'hrs'):
            time_sec = time_part * 3600
        else:
            time_sec = 1200      #default to 20 minutes

        return time_sec

#--------------------------------------------------------------------
    def _timestamp_to_time(self, utc_timestamp):
        """
        Convert iCloud timeStamp into the local time zone and
        return hh:mm:ss
        """

        ts_local = int(float(utc_timestamp)/1000) + \
                self.time_zone_offset_seconds

        ts_str = dt_util.utc_from_timestamp(
                ts_local).strftime(self.time_format)
        if ts_str[0] == "0":
            ts_str = ts_str[1:]

        return ts_str

#--------------------------------------------------------------------
    def _timestamp_to_seconds(self, utc_timestamp):
        """
        Convert timeStamp into the local time zone and
        return time in seconds
        """

        ts_local = int(float(utc_timestamp)/1000) + \
                self.time_zone_offset_seconds

        ts_str = dt_util.utc_from_timestamp(ts_local).strftime('%X')
        if ts_str[0] == "0":
            ts_str = ts_str[1:]

        t_sec = self._time_to_seconds(ts_str)
       # if self.this_update_secs > 43200: t_sec = t_sec + 43200
        log_msg = ("_timestamp_to_seconds, ts_str={},"
                         " Seconds={}").format(
                          ts_str, t_sec) 
        self._LOGGER_debug_msg(log_msg)
        return t_sec

#--------------------------------------------------------------------
    @staticmethod
    def _calculate_time_zone_offset():
        """ Calculate time zone offset seconds """
        try:
            local_zone_offset = dt_util.now().strftime('%z')
            local_zone_offset_seconds = int(local_zone_offset[1:3])*3600 + \
                        int(local_zone_offset[3:5])*60
            if local_zone_offset[:1] == "-":
                local_zone_offset_seconds = -1*local_zone_offset_seconds

#            log_msg = ("►►TIME ZONE OFFSET, Local Zone Offset: {},"
#                         " Seconds Offset: {}").format(
#                          local_zone_offset, local_zone_offset_seconds) 
#            self._LOGGER_debug_msg(log_msg)
        except:
            local_zone_offset_seconds = 0

        return local_zone_offset_seconds

#--------------------------------------------------------------------
    def _km_to_mi(self, arg_distance):
        if arg_distance:
            return round(arg_distance * self.km_mi_factor, 2)
        else:
            return 0

    def _mi_to_km(self, arg_distance):
        if arg_distance:
            return round(arg_distance / self.km_mi_factor, 2)
        else:
            return 0

#--------------------------------------------------------------------
    @staticmethod
    def _calc_distance(from_lat, from_long, to_lat, to_long):
        d = round(distance(from_lat, from_long, to_lat, to_long) / 1000, 2)
        if d < .05:
            d = 0
        return d

#--------------------------------------------------------------------
    @staticmethod
    def _round_to_zero(arg_distance):
        if arg_distance < .05:
            arg_distance = 0
        return round(arg_distance, 2)

#--------------------------------------------------------------------
    def _add_comma_to_str(self, text):
        """ Add a comma to info if it is not an empty string """
        if text:
            return '{}, '.format(text)
        return ''

#########################################################
#
#   ICLOUD ROUTINES
#
#########################################################

    def lost_iphone(self, devicename):
        """Call the lost iPhone function if the device is found."""
        if self.api is None:
            return

        self.api.authenticate()
        self.authenticated_time = \
                    dt_util.now().strftime(self.date_time_forma)

        for device in self.api.devices:
            if devicename is None or device == self.tracked_devices[devicename]:
                device.play_sound()

#--------------------------------------------------------------------
    def update_icloud(self, arg_devicename=None, arg_command=None):
        """
        Authenticate against iCloud and scan for devices.


        Commands:
        - waze reset range = reset the min-max rnge to defaults (1-1000)
        - waze toggle      = toggle waze on or off
        - pause            = stop polling for the devicename or all devices
        - resume           = resume polling devicename or all devices, reset
                             the interval override to normal interval
                             calculations
        - pause-resume     = same as above but toggles between pause and resume
        - zone xxxx        = updates the devie state to xxxx and updates all
                             of the iloud3 attributes. This does the see
                             service call and then an update.
        - reset            = reset everything and rescans all of the devices
        - debug interval   = displays the interval formula being used
        - debug gps        = simulates bad gps accuracy
        - debug old        = simulates that the location informaiton is old
        - info xxx         = the same as 'debug'
        """

        arg_command         = ("{} .").format(arg_command)
        arg_command_cmd     = arg_command.split(' ')[0].lower()
        arg_command_parm    = arg_command.split(' ')[1]       #original value
        arg_command_parmlow = arg_command_parm.lower()

        log_msg = ("iCloud Command Request, Device '{}', Command '{}' <WARN>").format(
                arg_devicename, arg_command) 
        self._LOGGER_info_msg(log_msg)


        if arg_command_cmd == 'waze':   #and self.distance_method_waze_flag:
            if arg_command_parmlow == 'reset_range':
                self.waze_min_distance = 0
                self.waze_max_distance = 99999
                self.waze_status  = WAZE_USED
            elif self.waze_status == WAZE_USED:
                self.waze_status  = WAZE_PAUSED
            else:
                self.waze_status = WAZE_USED

        elif arg_command_cmd == 'zone':     #parmeter is the new zone
            if 'home' in arg_command_parmlow:    #home/not_home is lower case
                arg_command_parm = arg_command_parmlow

            kwargs = {}
            attrs  = {}

            self._wait_if_update_in_process(arg_devicename)
            self._update_tracked_devices(arg_devicename)

            self.update_in_process_flag = False

            return

        #loop through all devices being tracked and update the attributes
        #Set various flags if pausing or resuming that will be processed
        #by the next poll in '_device_polling_15_sec_timer_loop'
        device_time_adj = 0
        for devicename in self.tracked_devices:
            if arg_devicename and devicename != arg_devicename:
                continue

            device_time_adj += 3

            now_seconds = self._time_to_seconds(dt_util.now().strftime('%X'))
            x, update_in_secs = divmod(now_seconds, 15)
            update_in_secs = 15 - update_in_secs + device_time_adj

            attrs = {}

            if arg_command_cmd in ('debug', 'info'):
                arg_command_cmd = 'resume'      #force retart for changes
    
                if arg_command_parm == 'logging':
                    self.write_log_debug_msgs_flag = \
                            (not self.write_log_debug_msgs_flag) 
                elif arg_command_parm in self.debug_control:
                    self.debug_control = ''
                else:
                    self.debug_control = arg_command_parm
                attrs[ATTR_INFO] = '● {} ●'.format(self.debug_control)
                
            elif arg_command_cmd == 'pause-resume':
                if self.next_update_time[devicename] == 'Paused':
                    arg_command_cmd = 'resume'
                else:
                    arg_command_cmd = 'pause'

            if arg_command_cmd == 'pause':
                cmd_type = CMD_PAUSE
                self.next_update_seconds[devicename] = 99999
                self.next_update_time[devicename]    = 'Paused'
                attrs[CONF_INTERVAL]                 ='●PAUSE●'

            elif arg_command_cmd == 'resume':
                cmd_type = CMD_RESUME
                self.next_update_time[devicename]         = '00:00:00'
                self.next_update_seconds[devicename]      = 0
                self.overrideinterval_seconds[devicename] = 0
                attrs[ATTR_NEXT_UPDATE_TIME]              = '00:00:00'
                attrs[CONF_INTERVAL]  = '►IN-{}s'.format(update_in_secs)

            elif arg_command_cmd == 'waze':
                cmd_type = CMD_WAZE
                if self.next_update_time[devicename] != 'Paused':
                    self.next_update_time[devicename]         = '00:00:00'
                    self.next_update_seconds[devicename]      = 0
                    self.overrideinterval_seconds[devicename] = 0
                    attrs[ATTR_NEXT_UPDATE_TIME]              = '00:00:00'

                if self.waze_status == WAZE_PAUSED:
                    attrs[ATTR_WAZE_TIME] = ''      #●WAZEOFF●'
                elif self.next_update_time[devicename] == 'Paused':
                    attrs[ATTR_WAZE_TIME] = ''
                else:
                    attrs[ATTR_WAZE_TIME] = '►IN-{}s'.\
                                            format(update_in_secs)

            elif arg_command_cmd == 'reset':
                self.reset_icloud_account_request_flag = True
                attrs[ATTR_INFO] = '● ICLOUD RESET REQUESTED ●'.\
                                            format(arg_command)

            else:
                cmd_type = CMD_ERROR
                attrs[ATTR_INFO] = '● INVALID COMMAND ({}) ●'.\
                                            format(arg_command)

            kwargs = {}
            self._update_device_attributes(devicename, kwargs, attrs)

        #end for devicename in devs loop

#--------------------------------------------------------------------
    def setinterval(self, arg_interval=None, arg_devicename=None):
        """
        Set the interval or process the action command of the given devices.
            'interval' has the following options:
                - 15               = 15 minutes
                - 15 min           = 15 minutes
                - 15 sec           = 15 seconds
                - 5 hrs            = 5 hours
                - Pause            = Pause polling for all devices
                                     (or specific device if devicename
                                      is specified)
                - Resume            = Resume polling for all devices
                                     (or specific device if devicename
                                      is specified)
                - Waze              = Toggle Waze on/off
        """

        if arg_interval is not None:
            cmd_type = CMD_INTERVAL
            new_interval = arg_interval.lower().replace('_', ' ')

#       loop through all devices being tracked and
#       update the attributes. Set various flags if pausing or resuming
#       that will be processed by the next poll in '_device_polling_15_sec_timer_loop'
        device_time_adj = 0
        for devicename in self.tracked_devices:
            if arg_devicename and devicename != arg_devicename:
                continue

            device_time_adj += 3

            self._wait_if_update_in_process()

            log_msg = ("►►SET INTERVAL COMMAND Start {}, "
                          "ArgDevname={}, ArgInterval={}"
                          "Old/New Interval: {}/{}").format(
                          devicename, arg_devicename, arg_interval,
                          self.interval_str.get(devicename), new_interval) 
            self._LOGGER_debug_msg(log_msg)

            self.next_update_time[devicename]         = '00:00:00'
            self.next_update_seconds[devicename]      = 0
            self.overrideinterval_seconds[devicename] = 0

            self.interval_str[devicename] = new_interval
            self.overrideinterval_seconds[devicename] = \
                    self._time_str_to_seconds(new_interval)

            now_seconds = \
                self._time_to_seconds(dt_util.now().strftime('%X'))
            x, update_in_secs = divmod(now_seconds, 15)
            time_suffix = 15 - update_in_secs + device_time_adj

            kwargs = {}
            attrs  = {}
            attrs[CONF_INTERVAL] = ("►IN-{}s").format(time_suffix)

            self._update_device_attributes(devicename, kwargs, attrs)

            log_msg = ("►►SET INTERVAL COMMAND END {}").format(devicename) 
            self._LOGGER_debug_msg(log_msg)

#--------------------------------------------------------------------
