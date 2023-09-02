# INFO --------------------------------------------
# This is intended to be called once manually or on startup. See blueprint.
# Automations can be deactivated correctly from the UI!
# -------------------------------------------------
from typing import Union
import datetime

# class_instances = {}
CONDITIONS = [
    ("Settled Fine"),
    ("Fine Weather"),
    ("Fine, Becoming Less Settled"),
    ("Fairly Fine, Showery Later"),
    ("Showery, Becoming More Unsettled"),
    ("Unsettled, Rain Later"),
    ("Rain at Times, Worse Later"),
    ("Rain at Times, Becoming Very Unsettled"),
    ("Very Unsettled, Rain"),
    ("Settled Fine"),
    ("Fine Weather"),
    ("Fine, Possibly Showers"),
    ("Fairly Fine, Showers Likely"),
    ("Showery, Bright Intervals"),
    ("Changeable, Some Rain"),
    ("Unsettled, Rain at Times"),
    ("Rain at Frequent Intervals"),
    ("Very Unsettled, Rain"),
    ("Stormy, Much Rain"),
    ("Settled Fine"),
    ("Fine Weather"),
    ("Becoming Fine"),
    ("Fairly Fine, Improving"),
    ("Fairly Fine, Possibly Showers Early"),
    ("Showery Early, Improving"),
    ("Changeable, Mending"),
    ("Rather Unsettled, Clearing Later"),
    ("Unsettled, Probably Improving"),
    ("Unsettled, Short Fine Intervals"),
    ("Very Unsettled, Finer at Times"),
    ("Stormy, Possibly Improving"),
    ("Stormy, Much Rain"),
]


def _get_state(entity_id: str) -> Union[str, None]:
    """
    Get the state of an entity in Home Assistant
    :param entity_id:  Name of the entity
    :return:            State if entity name is valid, else None
    """
    # get entity domain
    domain = entity_id.split(".")[0]
    try:
        entity_state = state.get(entity_id)
    except Exception as e:
        log.error(f"Could not get state from entity {entity_id}: {e}")
        return None

    if domain == "sensor":
        return entity_state
    else:
        log.error(f"Entity domain not supported: {domain}")
        return None


def _turn_off(entity_id: str) -> bool:
    """
    Switches an entity off
    :param entity_id: ID of the entity
    """
    # get entity domain
    domain = entity_id.split(".")[0]
    # check if service exists:
    if not service.has_service(domain, "turn_off"):
        log.error(
            f'Cannot switch off appliance: Service "{domain}.turn_off" does not exist.'
        )
        return False

    try:
        service.call(domain, "turn_off", entity_id=entity_id)
    except Exception as e:
        log.error(f"Cannot switch off appliance: {e}")
        return False
    else:
        return True


def _turn_on(entity_id: str) -> bool:
    """
    Switches an entity on
    :param entity_id: ID of the entity
    """
    # get entity domain
    domain = entity_id.split(".")[0]
    # check if service exists:
    if not service.has_service(domain, "turn_on"):
        log.error(
            f'Cannot switch on appliance: Service "{domain}.turn_on" does not exist.'
        )
        return False

    try:
        service.call(domain, "turn_on", entity_id=entity_id)
    except Exception as e:
        log.error(f"Cannot switch on appliance: {e}")
        return False
    else:
        return True


def _set_value(entity_id: str, value: Union[int, float, str]) -> bool:
    """
    Sets a number entity to a specific value
    :param entity_id: ID of the entity
    :param value: Numerical value
    :return:
    """
    # get entity domain
    domain = entity_id.split(".")[0]
    # check if service exists:
    if not service.has_service(domain, "set_value"):
        log.error(
            f'Cannot set value "{value}": Service "{domain}.set_value" does not exist.'
        )
        return False

    try:
        service.call(domain, "set_value", entity_id=entity_id, value=value)
    except Exception as e:
        log.error(f'Cannot set value "{value}": {e}')
        return False
    else:
        return True


def _get_num_state(
    entity_id: str, return_on_error: Union[float, None] = None
) -> Union[float, None]:
    return _validate_number(_get_state(entity_id), return_on_error)


def _validate_number(
    num: Union[float, str], return_on_error: Union[float, None] = None
) -> Union[float, None]:
    """
    Validate, if the passed variable is a number between 0 and 1000000.
    :param num:             Number
    :param return_on_error: Value to return in case of error
    :return:                Number if valid, else None
    """
    min_v = -1000000
    max_v = 1000000
    try:
        if min_v <= float(num) <= max_v:
            return float(num)
        else:
            raise Exception(f"{float(num)} not in range: [{min_v}, {max_v}]")
    except Exception as e:
        log.error(f"{num=} is not a valid number between 0 and 1000000: {e}")
        return return_on_error


# def _replace_vowels(input: str) -> str:
#     """
#     Function to replace lowercase vowels in a string
#     :param input:   Input string
#     :return:        String with replaced vowels
#     """
#     vowel_replacement = {"ä": "a", "ö": "o", "ü": "u"}
#     res = [vowel_replacement[v] if v in vowel_replacement else v for v in input]
#     return "".join(res)


# @time_trigger("cron(0 0 * * *)")
# def reset_midnight():
#     log.info("Resetting 'switched_on_today' instance variables.")
#     for e in LocalWeather.instances.copy().values():
#         inst = e["instance"]
#         inst.switched_on_today = False


@service
def local_weather(
    language,
    temperature,
    temperaturechange,
    pressure,
    pressurechange,
    sea_pressure,
    height,
    wind_direction,
    wind_speed,
):
    return LocalWeather(
        language,
        temperature,
        temperaturechange,
        pressure,
        pressurechange,
        sea_pressure,
        height,
        wind_direction,
        wind_speed,
    )


class LocalWeather:
    language = None
    temperature = None
    temperaturechange = None
    pressure = None
    pressurechange = None
    sea_pressure = None
    height = None
    wind_direction = None
    wind_speed = None

    def __init__(
        self,
        language,
        temperature,
        temperaturechange,
        pressure,
        pressurechange,
        pressure_sea,
        height,
        wind_direction,
        wind_speed,
    ):
        LocalWeather.language = language
        LocalWeather.temperature = float(temperature)
        LocalWeather.temperaturechange = float(temperaturechange)
        LocalWeather.pressure = float(pressure)
        LocalWeather.pressurechange = float(pressurechange)
        LocalWeather.pressure_sea = float(pressure_sea)
        LocalWeather.wind_direction = float(wind_direction)
        LocalWeather.wind_speed = float(wind_speed)
        LocalWeather.height = float(height)

        log.info(f"{self.log_prefix} Registered appliance.")

    def p0(self):
        p0 = LocalWeather.pressure * LocalWeather.pressure_sea - (
            LocalWeather.pressure_sea - 1
        ) * LocalWeather.pressure * (
            1
            - (
                (0.0065 * LocalWeather.height)
                / (LocalWeather.temperature + (0.0065 * LocalWeather.height) + 273.15)
            )
        ) ** (
            -5.257
        )
        return p0

    def wind_speed_fak(self):
        if LocalWeather.wind_speed < 1:
            wind_speed_fak = 0
        else:
            wind_speed_fak = 1
        return wind_speed_fak

    def wind_fak(self):
        if LocalWeather.wind_direction >= 135 and LocalWeather.wind_direction <= 225:
            wind_fak = 2
        elif LocalWeather.wind_direction >= 315 or LocalWeather.wind_direction <= 45:
            wind_fak = 0
        else:
            wind_fak = 1
        return wind_fak

    def get_current_month():
        # Get the current month
        today = datetime.date.today()
        date = datetime.datetime.strptime(str(today), "%Y-%m-%d")
        month = int(date.month)
        return month

    def forecast_zambretti(self):
        if LocalWeather.pressurechange <= (-1.0):
            trend = -1
        elif LocalWeather.pressurechange >= (1.0):
            trend = 1
        else:
            trend = 0
        # Use the Zambretti-algorithm to finally make the forecast
        # --------------------------------------------------------
        # Falling Conditions
        # ------------------
        if trend == -1:
            zambretti = (127 - 0.12 * self.p0()) | round(0) | int(0)
            if self.get_current_month() < 4 | self.get_current_month() > 9:
                zambretti = zambretti - 1
            zambretti = int(round(zambretti))
            # if zambretti == 1:
            #     forecast = "Settled Fine"
            # elif zambretti == 2:
            #     forecast = "Fine Weather"
            # elif zambretti == 3:
            #     forecast = "Fine Becoming Less Settled"
            # elif zambretti == 4:
            #     forecast = "Fairly Fine Showers Later"
            # elif zambretti == 5:
            #     forecast = "Showery Becoming unsettled"
            # elif zambretti == 6:
            #     forecast = "Unsettled, Rain later"
            # elif zambretti == 7:
            #     forecast = "Rain at times, worse later"
            # elif zambretti == 8:
            #     forecast = "Rain at times, becoming very unsettled"
            # elif zambretti == 9:
            #     forecast = "Very Unsettled, Rain"
        # Steady Conditions
        # -----------------
        elif trend == 0:
            zambretti = (144 - 0.13 * self.p0()) | round(0) | int(0)
            zambretti = int(round(zambretti))
            # if zambretti == 10:
            #     forecast = "Settled Fine"
            # elif zambretti == 11:
            #     forecast = "Fine Weather"
            # elif zambretti == 12:
            #     forecast = "Fine, Possibly showers"
            # elif zambretti == 13:
            #     forecast = "Fairly Fine, Showers likely"
            # elif zambretti == 14:
            #     forecast = "Showery Bright Intervals"
            # elif zambretti == 15:
            #     forecast = "Changeable some rain"
            # elif zambretti == 16:
            #     forecast = "Unsettled, rain at times"
            # elif zambretti == 17:
            #     forecast = "Rain at Frequent Intervals"
            # elif zambretti == 18:
            #     forecast = "Very Unsettled, Rain"
            # elif zambretti == 19:
            #     forecast = "Stormy, much rain"
        # Rising Conditions
        # -----------------
        elif trend == 1:
            zambretti = (185 - 0.16 * self.p0()) | round(0) | int(0)
            if self.get_current_month() > 4 | self.get_current_month() < 9:
                zambretti = zambretti + 1
            zambretti = int(round(zambretti))
            # if zambretti == 20:
            #     forecast = "Settled Fine"
            # elif zambretti == 21:
            #     forecast = "Fine Weather"
            # elif zambretti == 22:
            #     forecast = "Becoming Fine"
            # elif zambretti == 23:
            #     forecast = "Fairly Fine, Improving"
            # elif zambretti == 24:
            #     forecast = "Fairly Fine, Possibly showers, early"
            # elif zambretti == 25:
            #     forecast = "Showery Early, Improving"
            # elif zambretti == 26:
            #     forecast = "Changeable, Improving"
            # elif zambretti == 27:
            #     forecast = "Rather Unsettled Clearing Later"
            # elif zambretti == 28:
            #     forecast = "Unsettled, Probably Improving"
            # elif zambretti == 29:
            #     forecast = "Unsettled, short fine Intervals"
            # elif zambretti == 30:
            #     forecast = "Very Unsettled, Finer at times"
            # elif zambretti == 31:
            #     forecast = "Stormy, possibly improving"
            # elif zambretti == 32:
            #     forecast = "Stormy, much rain"

        zambretti = zambretti + self.wind_fak() * self.wind_speed_fak()

        return zambretti

    # def trigger_factory(self):
    #     # trigger every 10s
    #     @time_trigger("period(now, 10s)")
    #     def on_time():
    #         # Sanity check
    #         if not self.sanity_check():
    #             return on_time

    #         LocalWeather.on_time_counter += 1
    #         LocalWeather._update_pv_history()
    #         # ensure that control algo only runs every minute (= every 6th on_time trigger)
    #         if LocalWeather.on_time_counter % 6 != 0:
    #             return on_time
    #         LocalWeather.on_time_counter = 0

    #         # ----------------------------------- go through each appliance (highest prio to lowest) ---------------------------------------
    #         # this is for determining which devices can be switched on
    #         instances = []
    #         for a_id, e in LocalWeather.instances.copy().items():
    #             inst = e["instance"]
    #             inst.switch_interval_counter += 1
    #             log_prefix = inst.log_prefix

    #             # Check if automation is activated for specific instance
    #             if not self.automation_activated(inst.automation_id):
    #                 continue

    #             # check min bat lvl and decide whether to regard export power or solar power minus load power
    #             if LocalWeather.home_battery_level is None:
    #                 home_battery_level = 100
    #             else:
    #                 home_battery_level = _get_num_state(LocalWeather.home_battery_level)
    #             if (
    #                 home_battery_level >= LocalWeather.min_home_battery_level
    #                 or not self._force_charge_battery()
    #             ):
    #                 # home battery charge is high enough to direct solar power to appliances, if solar power is higher than load power
    #                 # calc avg based on pv excess (solar power - load power) according to specified window
    #                 avg_excess_power = int(
    #                     sum(LocalWeather.pv_history[-inst.appliance_switch_interval :])
    #                     / inst.appliance_switch_interval
    #                 )
    #                 log.debug(
    #                     f"{log_prefix} Home battery charge is sufficient ({home_battery_level}/{LocalWeather.min_home_battery_level} %)"
    #                     f" OR remaining solar forecast is higher than remaining capacity of home battery. "
    #                     f"Calculated average excess power based on >> solar power - load power <<: {avg_excess_power} W"
    #                 )

    #             else:
    #                 # home battery charge is not yet high enough OR battery force charge is necessary.
    #                 # Only use excess power (which would otherwise be exported to the grid) for appliance
    #                 # calc avg based on export power history according to specified window
    #                 avg_excess_power = int(
    #                     sum(
    #                         LocalWeather.export_history[
    #                             -inst.appliance_switch_interval :
    #                         ]
    #                     )
    #                     / inst.appliance_switch_interval
    #                 )
    #                 log.debug(
    #                     f"{log_prefix} Home battery charge is not sufficient ({home_battery_level}/{LocalWeather.min_home_battery_level} %), "
    #                     f"OR remaining solar forecast is lower than remaining capacity of home battery. "
    #                     f"Calculated average excess power based on >> export power <<: {avg_excess_power} W"
    #                 )

    #             # add instance including calculated excess power to inverted list (priority from low to high)
    #             instances.insert(
    #                 0, {"instance": inst, "avg_excess_power": avg_excess_power}
    #             )

    #             # -------------------------------------------------------------------
    #             # Determine if appliance can be turned on or current can be increased
    #             if _get_state(inst.appliance_switch) == "on":
    #                 # check if current of appliance can be increased
    #                 log.debug(f"{log_prefix} Appliance is already switched on.")
    #                 if (
    #                     avg_excess_power >= LocalWeather.min_excess_power
    #                     and inst.dynamic_current_appliance
    #                 ):
    #                     # try to increase dynamic current, because excess solar power is available
    #                     prev_amps = _get_num_state(
    #                         inst.appliance_current_set_entity,
    #                         return_on_error=inst.min_current,
    #                     )
    #                     excess_amps = (
    #                         round(
    #                             avg_excess_power
    #                             / (LocalWeather.grid_voltage * inst.phases),
    #                             1,
    #                         )
    #                         + prev_amps
    #                     )
    #                     amps = max(inst.min_current, min(excess_amps, inst.max_current))
    #                     if amps > (prev_amps + 0.09):
    #                         _set_value(inst.appliance_current_set_entity, amps)
    #                         log.info(
    #                             f"{log_prefix} Setting dynamic current appliance from {prev_amps} to {amps} A per phase."
    #                         )
    #                         diff_power = (
    #                             (amps - prev_amps)
    #                             * LocalWeather.grid_voltage
    #                             * inst.phases
    #                         )
    #                         # "restart" history by subtracting power difference from each history value within the specified time frame
    #                         self._adjust_pwr_history(inst, -diff_power)

    #             else:
    #                 # check if appliance can be switched on
    #                 if _get_state(inst.appliance_switch) != "off":
    #                     log.warning(
    #                         f"{log_prefix} Appliance state (={_get_state(inst.appliance_switch)}) is neither ON nor OFF. "
    #                         f"Assuming OFF state."
    #                     )
    #                 defined_power = (
    #                     inst.defined_current * LocalWeather.grid_voltage * inst.phases
    #                 )
    #                 if avg_excess_power >= defined_power:
    #                     log.debug(
    #                         f"{log_prefix} Average Excess power is high enough to switch on appliance."
    #                     )
    #                     if (
    #                         inst.switch_interval_counter
    #                         >= inst.appliance_switch_interval
    #                     ):
    #                         self.switch_on(inst)
    #                         inst.switch_interval_counter = 0
    #                         log.info(f"{log_prefix} Switched on appliance.")
    #                         # "restart" history by subtracting defined power from each history value within the specified time frame
    #                         self._adjust_pwr_history(inst, -defined_power)
    #                         task.sleep(1)
    #                         if inst.dynamic_current_appliance:
    #                             _set_value(
    #                                 inst.appliance_current_set_entity, inst.min_current
    #                             )
    #                     else:
    #                         log.debug(
    #                             f"{log_prefix} Cannot switch on appliance, because appliance switch interval is not reached "
    #                             f"({inst.switch_interval_counter}/{inst.appliance_switch_interval})."
    #                         )
    #                 else:
    #                     log.debug(
    #                         f"{log_prefix} Average Excess power not high enough to switch on appliance."
    #                     )
    #             # -------------------------------------------------------------------

    #         # ----------------------------------- go through each appliance (lowest prio to highest prio) ----------------------------------
    #         # this is for determining which devices need to be switched off or decreased in current
    #         prev_consumption_sum = 0
    #         for dic in instances:
    #             inst = dic["instance"]
    #             avg_excess_power = dic["avg_excess_power"] + prev_consumption_sum
    #             log_prefix = (
    #                 f"[{inst.appliance_switch} (Prio {inst.appliance_priority})]"
    #             )

    #             # -------------------------------------------------------------------
    #             if _get_state(inst.appliance_switch) == "on":
    #                 if avg_excess_power < LocalWeather.min_excess_power:
    #                     log.debug(
    #                         f"{log_prefix} Average Excess Power ({avg_excess_power} W) is less than minimum excess power "
    #                         f"({LocalWeather.min_excess_power} W)."
    #                     )

    #                     # check if current of dyn. curr. appliance can be reduced
    #                     if inst.dynamic_current_appliance:
    #                         if inst.actual_power is None:
    #                             actual_current = round(
    #                                 (
    #                                     inst.defined_current
    #                                     * LocalWeather.grid_voltage
    #                                     * inst.phases
    #                                 )
    #                                 / (LocalWeather.grid_voltage * inst.phases),
    #                                 1,
    #                             )
    #                         else:
    #                             actual_current = round(
    #                                 _get_num_state(inst.actual_power)
    #                                 / (LocalWeather.grid_voltage * inst.phases),
    #                                 1,
    #                             )
    #                         diff_current = round(
    #                             avg_excess_power
    #                             / (LocalWeather.grid_voltage * inst.phases),
    #                             1,
    #                         )
    #                         target_current = max(
    #                             inst.min_current, actual_current + diff_current
    #                         )
    #                         log.debug(
    #                             f"{log_prefix} {actual_current=}A | {diff_current=}A | {target_current=}A"
    #                         )
    #                         if inst.min_current < target_current < actual_current:
    #                             # current can be reduced
    #                             log.info(
    #                                 f"{log_prefix} Reducing dynamic current appliance from {actual_current} A to {target_current} A."
    #                             )
    #                             _set_value(
    #                                 inst.appliance_current_set_entity, target_current
    #                             )
    #                             # add released power consumption to next appliances in list
    #                             diff_power = (
    #                                 (actual_current - target_current)
    #                                 * LocalWeather.grid_voltage
    #                                 * inst.phases
    #                             )
    #                             prev_consumption_sum += diff_power
    #                             log.debug(
    #                                 f"{log_prefix} Added {diff_power=} W to prev_consumption_sum, "
    #                                 f"which is now {prev_consumption_sum} W."
    #                             )
    #                             # "restart" history by adding defined power to each history value within the specified time frame
    #                             self._adjust_pwr_history(inst, diff_power)
    #                         else:
    #                             # current cannot be reduced
    #                             # turn off appliance
    #                             power_consumption = self.switch_off(inst)
    #                             if power_consumption != 0:
    #                                 prev_consumption_sum += power_consumption
    #                                 log.debug(
    #                                     f"{log_prefix} Added {power_consumption=} W to prev_consumption_sum, "
    #                                     f"which is now {prev_consumption_sum} W."
    #                                 )

    #                     else:
    #                         # Try to switch off appliance
    #                         power_consumption = self.switch_off(inst)
    #                         if power_consumption != 0:
    #                             prev_consumption_sum += power_consumption
    #                             log.debug(
    #                                 f"{log_prefix} Added {power_consumption=} W to prev_consumption_sum, "
    #                                 f"which is now {prev_consumption_sum} W."
    #                             )
    #                 else:
    #                     log.debug(
    #                         f"{log_prefix} Average Excess Power ({avg_excess_power} W) is still greater than minimum excess power "
    #                         f"({LocalWeather.min_excess_power} W) - Doing nothing."
    #                     )

    #             else:
    #                 if _get_state(inst.appliance_switch) != "off":
    #                     log.warning(
    #                         f"{log_prefix} Appliance state (={_get_state(inst.appliance_switch)}) is neither ON nor OFF. "
    #                         f"Assuming OFF state."
    #                     )
    #                 # Note: This can misfire right after an appliance has been switched on. Generally no problem.
    #                 log.debug(f"{log_prefix} Appliance is already switched off.")
    #             # -------------------------------------------------------------------

    #     return on_time

    # @staticmethod
    # def _update_pv_history():
    #     """
    #     Update Export and PV history
    #     """
    #     try:
    #         if LocalWeather.import_export_power:
    #             # Calc values based on combined import/export power sensor
    #             import_export = int(_get_num_state(LocalWeather.import_export_power))
    #             # load_pwr = pv_pwr + import_export
    #             export_pwr = abs(min(0, import_export))
    #             excess_pwr = -import_export
    #         else:
    #             # Calc values based on separate sensors
    #             export_pwr = int(_get_num_state(LocalWeather.export_power))
    #             excess_pwr = int(
    #                 _get_num_state(LocalWeather.pv_power)
    #                 - _get_num_state(LocalWeather.load_power)
    #             )
    #     except Exception as e:
    #         log.error(f"Could not update Export/PV history!: {e}")
    #     else:
    #         LocalWeather.export_history_buffer.append(export_pwr)
    #         LocalWeather.pv_history_buffer.append(excess_pwr)

    #     # log.debug(f'Export History Buffer: {LocalWeather.export_history_buffer}')
    #     # log.debug(f'PV Excess (PV Power - Load Power) History Buffer: {LocalWeather.pv_history_buffer}')

    #     if LocalWeather.on_time_counter % 6 == 0:
    #         # enforce max. 60 minute length of history
    #         if len(LocalWeather.export_history) >= 60:
    #             LocalWeather.export_history.pop(0)
    #         if len(LocalWeather.pv_history) >= 60:
    #             LocalWeather.pv_history.pop(0)
    #         # calc avg of buffer
    #         export_avg = round(
    #             sum(LocalWeather.export_history_buffer)
    #             / len(LocalWeather.export_history_buffer)
    #         )
    #         excess_avg = round(
    #             sum(LocalWeather.pv_history_buffer)
    #             / len(LocalWeather.pv_history_buffer)
    #         )
    #         # add avg to history
    #         LocalWeather.export_history.append(export_avg)
    #         LocalWeather.pv_history.append(excess_avg)
    #         log.debug(f"Export History: {LocalWeather.export_history}")
    #         log.debug(
    #             f"PV Excess (PV Power - Load Power) History: {LocalWeather.pv_history}"
    #         )
    #         # clear buffer
    #         LocalWeather.export_history_buffer = []
    #         LocalWeather.pv_history_buffer = []

    # def sanity_check(self) -> bool:
    #     if (
    #         LocalWeather.import_export_power is not None
    #         and LocalWeather.home_battery_level is not None
    #     ):
    #         log.warning(
    #             '"Import/Export power" has been defined together with "Home Battery". This is not intended and will lead to always '
    #             "giving the home battery priority over appliances, regardless of the specified min. battery level."
    #         )
    #         return True
    #     if LocalWeather.import_export_power is not None and (
    #         LocalWeather.export_power is not None or LocalWeather.load_power is not None
    #     ):
    #         log.error(
    #             '"Import/Export power" has been defined together with either "Export power" or "Load power". This is not '
    #             'allowed. Please specify either "Import/Export power" or both "Load power" & "Export Power".'
    #         )
    #         return False
    #     if not (
    #         LocalWeather.import_export_power is not None
    #         or (
    #             LocalWeather.export_power is not None
    #             and LocalWeather.load_power is not None
    #         )
    #     ):
    #         log.error(
    #             'Either "Export power" or "Load power" have not been defined. This is not '
    #             'allowed. Please specify either "Import/Export power" or both "Load power" & "Export Power".'
    #         )
    #         return False
    #     return True

    # def switch_on(self, inst):
    #     """
    #     Switches an appliance on, if possible.
    #     :param inst:        PVExcesscontrol Class instance
    #     """
    #     if inst.appliance_once_only and inst.switched_on_today:
    #         log.debug(
    #             f'{inst.log_prefix} "Only-Run-Once-Appliance" detected - Appliance was already switched on today - '
    #             f"Not switching on again."
    #         )
    #     if _turn_on(inst.appliance_switch):
    #         inst.switched_on_today = True

    # def switch_off(self, inst) -> float:
    #     """
    #     Switches an appliance off, if possible.
    #     :param inst:        PVExcesscontrol Class instance
    #     :return:            Power consumption relief achieved through switching the appliance off (will be 0 if appliance could
    #                          not be switched off)
    #     """
    #     # Check if automation is activated for specific instance
    #     if not self.automation_activated(inst.automation_id):
    #         return 0
    #     # Do not turn off only-on-appliances
    #     if inst.appliance_on_only:
    #         log.debug(
    #             f'{inst.log_prefix} "Only-On-Appliance" detected - Not switching off.'
    #         )
    #         return 0
    #     # Do not turn off if switch interval not reached
    #     elif inst.switch_interval_counter < inst.appliance_switch_interval:
    #         log.debug(
    #             f"{inst.log_prefix} Cannot switch off appliance, because appliance switch interval is not reached "
    #             f"({inst.switch_interval_counter}/{inst.appliance_switch_interval})."
    #         )
    #         return 0
    #     else:
    #         # switch off
    #         # get last power consumption
    #         if inst.actual_power is None:
    #             power_consumption = (
    #                 inst.defined_current * LocalWeather.grid_voltage * inst.phases
    #             )
    #         else:
    #             power_consumption = _get_num_state(inst.actual_power)
    #         log.debug(
    #             f"{inst.log_prefix} Current power consumption: {power_consumption} W"
    #         )
    #         # switch off appliance
    #         _turn_off(inst.appliance_switch)
    #         log.info(f"{inst.log_prefix} Switched off appliance.")
    #         task.sleep(1)
    #         inst.switch_interval_counter = 0
    #         # "restart" history by adding defined power to each history value within the specified time frame
    #         self._adjust_pwr_history(inst, power_consumption)
    #         return power_consumption

    # def automation_activated(self, a_id):
    #     """
    #     Checks if the automation for a specific appliance is activated or not.
    #     :param a_id:    Automation ID in Home Assistant
    #     :return:        True if automation is activated, False otherwise
    #     """
    #     automation_state = _get_state(a_id)
    #     if automation_state == "off":
    #         log.debug(
    #             f"Doing nothing, because automation is not activated: State is {automation_state}."
    #         )
    #         return False
    #     elif automation_state is None:
    #         log.info(
    #             f'Automation "{a_id}" was deleted. Removing related class instance.'
    #         )
    #         del LocalWeather.instances[a_id]
    #         return False
    #     return True

    # def _adjust_pwr_history(self, inst, value):
    #     log.debug(f"Adjusting power history by {value}.")
    #     log.debug(f"Export history: {LocalWeather.export_history}")
    #     LocalWeather.export_history[-inst.appliance_switch_interval :] = [
    #         max(0, x + value)
    #         for x in LocalWeather.export_history[-inst.appliance_switch_interval :]
    #     ]
    #     log.debug(f"Adjusted export history: {LocalWeather.export_history}")
    #     log.debug(
    #         f"PV Excess (solar power - load power) history: {LocalWeather.pv_history}"
    #     )
    #     LocalWeather.pv_history[-inst.appliance_switch_interval :] = [
    #         x + value
    #         for x in LocalWeather.pv_history[-inst.appliance_switch_interval :]
    #     ]
    #     log.debug(
    #         f"Adjusted PV Excess (solar power - load power) history: {LocalWeather.pv_history}"
    #     )

    # def _force_charge_battery(self, kwh_offset: float = 1):
    #     """
    #     Calculates if the remaining solar power forecast is enough to ensure the specified min. home battery level is reached at the end
    #     of the day.
    #     :param kwh_offset:  Offset in kWh, which will be added to the calculated remaining battery capacity to ensure an earlier
    #                          triggering of a force charge
    #     :return:            True if force charge is necessary, False otherwise
    #     """
    #     if LocalWeather.home_battery_level is None:
    #         return False

    #     capacity = LocalWeather.home_battery_capacity
    #     remaining_capacity = capacity - (
    #         0.01
    #         * capacity
    #         * _get_num_state(LocalWeather.home_battery_level, return_on_error=0)
    #     )
    #     remaining_forecast = _get_num_state(
    #         LocalWeather.solar_production_forecast, return_on_error=0
    #     )
    #     if remaining_forecast <= remaining_capacity + kwh_offset:
    #         log.debug(
    #             f"Force battery charge necessary: {capacity=} kWh|{remaining_capacity=} kWh|{remaining_forecast=} kWh| "
    #             f"{kwh_offset=} kWh"
    #         )
    #         # go through appliances lowest to highest priority, and try switching them off individually
    #         for a_id, e in dict(
    #             sorted(
    #                 LocalWeather.instances.items(),
    #                 key=lambda item: item[1]["priority"],
    #             )
    #         ).items():
    #             inst = e["instance"]
    #             self.switch_off(inst)
    #         return True
    #     return False
