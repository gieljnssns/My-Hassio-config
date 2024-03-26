""" The person_location integration process_trigger service."""

import logging
import string
from datetime import datetime, timedelta, timezone
from functools import partial

from homeassistant.components.device_tracker.const import (
    ATTR_SOURCE_TYPE,
    SOURCE_TYPE_GPS,
)
from homeassistant.components.mobile_app.const import (
    ATTR_VERTICAL_ACCURACY,
)
from homeassistant.const import (
    ATTR_ENTITY_PICTURE,
    ATTR_GPS_ACCURACY,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_ENTITY_ID,
    STATE_NOT_HOME,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.exceptions import ServiceNotFound
from homeassistant.helpers.event import (
    track_point_in_time,
)

from .const import (
    ATTR_ALTITUDE,
    ATTR_BREAD_CRUMBS,
    ATTR_COMPASS_BEARING,
    ATTR_DIRECTION,
    CONF_HOURS_EXTENDED_AWAY,
    CONF_MINUTES_JUST_ARRIVED,
    CONF_MINUTES_JUST_LEFT,
    DOMAIN,
    PERSON_LOCATION_ENTITY,
    TARGET_LOCK,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)


def setup_process_trigger(pli):
    """Initialize process_trigger service."""

    def call_rest_command_service(personName, newState):
        """(Optionally) notify HomeSeer of the state change."""

        rest_command = ""
        rest_command = (
            "homeseer_" + personName.lower() + "_" + newState.lower().replace(" ", "_")
        )
        try:
            pli.hass.services.call("rest_command", rest_command)
        except ServiceNotFound as e:
            _LOGGER.debug(
                "call_rest_command_service Exception %s = %s",
                type(e).__name__,
                str(e),
            )

    def handle_delayed_state_change(
        now, *, entity_id=None, from_state=None, to_state=None, minutes=3
    ):
        """Handle the delayed state change."""

        _LOGGER.debug(
            "[handle_delayed_state_change]"
            + " (%s) === Start === from_state = %s; to_state = %s"
            % (entity_id, from_state, to_state)
        )

        with TARGET_LOCK:
            """Lock while updating the target(entity_id)."""
            _LOGGER.debug("[handle_delayed_state_change]" + " TARGET_LOCK obtained")
            target = PERSON_LOCATION_ENTITY(entity_id, pli)

            elapsed_timespan = datetime.now(timezone.utc) - target.last_changed
            elapsed_minutes = (
                elapsed_timespan.total_seconds() + 1
            ) / 60  # fudge factor of one second

            if target.state != from_state:
                _LOGGER.debug(
                    "[handle_delayed_state_change]"
                    + " Skip update: state %s is no longer %s"
                    % (target.state, from_state)
                )
            elif elapsed_minutes < minutes:
                _LOGGER.debug(
                    "[handle_delayed_state_change]"
                    + " Skip update: state change minutes ago %s less than %s"
                    % (elapsed_minutes, minutes)
                )
            else:
                target.state = to_state

                if to_state == "Home":
                    target.attributes[ATTR_BREAD_CRUMBS] = to_state
                    target.attributes[ATTR_COMPASS_BEARING] = 0
                    target.attributes[ATTR_DIRECTION] = "home"
                elif to_state == "Away":
                    change_state_later(
                        target.entity_id,
                        "Away",
                        "Extended Away",
                        (pli.configuration[CONF_HOURS_EXTENDED_AWAY] * 60),
                    )
                    pass
                elif to_state == "Extended Away":
                    pass

                call_rest_command_service(target.personName, to_state)
                target.set_state()
        _LOGGER.debug(
            "[handle_delayed_state_change]" + " (%s) === Return ===" % (entity_id)
        )

    def change_state_later(entity_id, from_state, to_state, minutes=3):
        """Set timer to handle the delayed state change."""

        _LOGGER.debug("[change_state_later]" + " (%s) === Start ===" % (entity_id))
        point_in_time = datetime.now() + timedelta(minutes=minutes)
        remove = track_point_in_time(
            pli.hass,
            partial(
                handle_delayed_state_change,
                entity_id=entity_id,
                from_state=from_state,
                to_state=to_state,
                minutes=minutes,
            ),
            point_in_time=point_in_time,
        )
        if remove:
            _LOGGER.debug(
                "[change_state_later]"
                + " (%s) handle_delayed_state_change(, %s, %s, %d) has been scheduled"
                % (entity_id, from_state, to_state, minutes)
            )
        _LOGGER.debug("[change_state_later]" + " (%s) === Return ===" % (entity_id))

    def utc2local_naive(utc_dt):
        local = utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
        if str(local)[-6] == "-" or str(local)[-6] == "+":
            local = str(local)[:-6]  # remove offset to make it offset-naive
            local = datetime.strptime(local, "%Y-%m-%d %H:%M:%S.%f")
        _LOGGER.debug(
            "[utc2local_naive] utc = %s; local = %s",
            utc_dt,
            local,
        )
        return local

    def handle_process_trigger(call):
        """
        Handle changes of triggered device trackers and sensors.

        Input:
            - Parameters for the call:
                entity_id
                from_state
                to_state
        Output (if update is accepted):
            - Updated "sensor.<personName>_location" with <personName>'s location and status:
                Attributes:
                - selected attributes from the triggered device tracker
                - state: "Just Arrived", "Home", "Just Left", "Away", or "Extended Away"
                - person_name: <personName>
                - source: entity_id of the device tracker that triggered the automation
                - reported_state: the state reported by device tracker = "Home", "Away", or <zone>
                - friendly_name: something like "Rod (i.e. Rod's watch) is at Drew's"
                - icon: the icon that correspondes with the current zone
            - Call rest_command service to update HomeSeer: 'homeseer_<personName>_<state>'
        """

        entity_id = call.data.get(CONF_ENTITY_ID, "NONE")
        triggerFrom = call.data.get("from_state", "NONE")
        triggerTo = call.data.get("to_state", "NONE")

        if entity_id == "NONE":
            {
                _LOGGER.warning(
                    "%s is required in call of %s.process_trigger service."
                    % (CONF_ENTITY_ID, DOMAIN)
                )
            }
            return False

        trigger = PERSON_LOCATION_ENTITY(entity_id, pli)

        _LOGGER.debug(
            "(%s) === Start === from_state = %s; to_state = %s",
            trigger.entity_id,
            triggerFrom,
            triggerTo,
        )

        if trigger.entity_id == trigger.targetName:
            _LOGGER.debug(
                "(%s) Decision: skip self update: target = (%s)",
                trigger.entity_id,
                trigger.targetName,
            )
        elif ATTR_GPS_ACCURACY in trigger.attributes and (
            (trigger.attributes[ATTR_GPS_ACCURACY] == 0)
            or (trigger.attributes[ATTR_GPS_ACCURACY] >= 100)
        ):
            _LOGGER.debug(
                "(%s) Decision: skip update: gps_accuracy = %s",
                trigger.entity_id,
                trigger.attributes[ATTR_GPS_ACCURACY],
            )
        elif triggerTo in ["NotSet", STATE_UNAVAILABLE, STATE_UNKNOWN]:
            _LOGGER.debug(
                "(%s) Decision: skip update: triggerTo = %s",
                trigger.entity_id,
                triggerTo,
            )
        else:

            if "last_located" in trigger.attributes:
                last_located = trigger.attributes["last_located"]
                new_location_time = datetime.strptime(last_located, "%Y-%m-%d %H:%M:%S")
            else:
                new_location_time = utc2local_naive(
                    trigger.last_updated
                )  # HA last_updated is UTC

            if ATTR_SOURCE_TYPE in trigger.attributes:
                triggerSourceType = trigger.attributes[ATTR_SOURCE_TYPE]
            else:
                triggerSourceType = "other"
                # person entities do not indicate the source type, dig deeper:
                if "source" in trigger.attributes:
                    triggerSource = trigger.attributes["source"]
                    triggerSourceObject = pli.hass.states.get(triggerSource)
                    if triggerSourceObject is not None:
                        if ATTR_SOURCE_TYPE in triggerSourceObject.attributes:
                            triggerSourceType = triggerSourceObject.attributes[
                                ATTR_SOURCE_TYPE
                            ]

            # ---------------------------------------------------------
            # Get the current state of the target person location
            # sensor and decide if it should be updated with values
            # from the triggered device tracker:
            saveThisUpdate = False
            # ---------------------------------------------------------

            with TARGET_LOCK:
                """Lock while updating the target(trigger.targetName)."""
                _LOGGER.debug(
                    "(%s) TARGET_LOCK obtained",
                    trigger.targetName,
                )
                target = PERSON_LOCATION_ENTITY(trigger.targetName, pli)

                target.this_entity_info["trigger_count"] += 1

                if "location_time" in target.attributes:
                    old_location_time = datetime.strptime(
                        str(target.attributes["location_time"]),
                        "%Y-%m-%d %H:%M:%S.%f",
                    )
                else:
                    old_location_time = utc2local_naive(
                        target.last_updated
                    )  # HA last_updated is UTC

                _LOGGER.debug(
                    "(%s) new_location_time (from trigger) = %s; old_location_time (from target) = %s",
                    trigger.entity_id,
                    new_location_time,
                    old_location_time,
                )

                if new_location_time < old_location_time:
                    _LOGGER.debug(
                        "(%s) Decision: skip stale update: %s < %s",
                        trigger.entity_id,
                        new_location_time,
                        old_location_time,
                    )
                elif target.firstTime:
                    saveThisUpdate = True
                    _LOGGER.debug(
                        "(%s) Decision: target %s does not yet exist (normal at startup)",
                        trigger.entity_id,
                        target.entity_id,
                    )
                    oldTargetState = "none"
                else:
                    oldTargetState = target.state.lower()
                    if oldTargetState == STATE_UNKNOWN:
                        saveThisUpdate = True
                        _LOGGER.debug(
                            "(%s) Decision: accepting the first update of %s",
                            trigger.entity_id,
                            target.entity_id,
                        )
                    elif triggerSourceType == SOURCE_TYPE_GPS:  # gps device?
                        if triggerTo != triggerFrom:  # did it change zones?
                            saveThisUpdate = True  # gps changing zones is assumed to be new, correct info
                            _LOGGER.debug(
                                "(%s) Decision: trigger has changed zones",
                                trigger.entity_id,
                            )
                        else:
                            if (
                                not ("source" in target.attributes)
                                or not ("reported_state" in target.attributes)
                                or target.attributes["source"] == trigger.entity_id
                            ):  # same entity as we are following, if any?
                                saveThisUpdate = True
                                _LOGGER.debug(
                                    "(%s) Decision: continue following trigger",
                                    trigger.entity_id,
                                )
                            elif (
                                trigger.state == target.attributes["reported_state"]
                            ):  # same status as the one we are following?
                                if ATTR_VERTICAL_ACCURACY in trigger.attributes:
                                    if (
                                        not (
                                            ATTR_VERTICAL_ACCURACY in target.attributes
                                        )
                                    ) or (
                                        trigger.attributes[ATTR_VERTICAL_ACCURACY] > 0
                                        and target.attributes[ATTR_VERTICAL_ACCURACY]
                                        == 0
                                    ):  # better choice based on accuracy?
                                        saveThisUpdate = True
                                        _LOGGER.debug(
                                            "(%s) Decision: vertical_accuracy is better than %s",
                                            trigger.entity_id,
                                            target.attributes["source"],
                                        )
                                if (
                                    ATTR_GPS_ACCURACY in trigger.attributes
                                    and ATTR_GPS_ACCURACY in target.attributes
                                    and trigger.attributes[ATTR_GPS_ACCURACY]
                                    < target.attributes[ATTR_GPS_ACCURACY]
                                ):  # better choice based on accuracy?
                                    saveThisUpdate = True
                                    _LOGGER.debug(
                                        "(%s) Decision: gps_accuracy is better than %s",
                                        trigger.entity_id,
                                        target.attributes["source"],
                                    )
                    else:  # source = router or ping
                        if triggerTo != triggerFrom:  # did tracker change state?
                            if trigger.stateHomeAway == "Home":  # reporting Home
                                if (
                                    oldTargetState != "home"
                                ):  # no additional information if already Home
                                    saveThisUpdate = True
                                    _LOGGER.debug(
                                        "(%s) Decision: trigger has changed state",
                                        trigger.entity_id,
                                    )
                            else:  # reporting Away
                                if (
                                    oldTargetState == "home"
                                ):  # no additional information if already Away
                                    saveThisUpdate = True
                                    _LOGGER.debug(
                                        "(%s) Decision: trigger has changed state",
                                        trigger.entity_id,
                                    )

                # -----------------------------------------------------

                if not saveThisUpdate:
                    _LOGGER.debug(
                        "(%s) Decision: ignore update",
                        trigger.entity_id,
                    )
                else:
                    # Carry over selected attributes from trigger to target:

                    if ATTR_SOURCE_TYPE in trigger.attributes:
                        target.attributes[ATTR_SOURCE_TYPE] = trigger.attributes[
                            ATTR_SOURCE_TYPE
                        ]
                    else:
                        if ATTR_SOURCE_TYPE in target.attributes:
                            target.attributes.pop(ATTR_SOURCE_TYPE)

                    if (
                        ATTR_LATITUDE in trigger.attributes
                        and ATTR_LONGITUDE in trigger.attributes
                    ):
                        target.attributes[ATTR_LATITUDE] = trigger.attributes[
                            ATTR_LATITUDE
                        ]
                        target.attributes[ATTR_LONGITUDE] = trigger.attributes[
                            ATTR_LONGITUDE
                        ]
                    else:
                        if ATTR_LATITUDE in target.attributes:
                            target.attributes.pop(ATTR_LATITUDE)
                        if ATTR_LONGITUDE in target.attributes:
                            target.attributes.pop(ATTR_LONGITUDE)

                    if ATTR_GPS_ACCURACY in trigger.attributes:
                        target.attributes[ATTR_GPS_ACCURACY] = trigger.attributes[
                            ATTR_GPS_ACCURACY
                        ]
                    else:
                        if ATTR_GPS_ACCURACY in target.attributes:
                            target.attributes.pop(ATTR_GPS_ACCURACY)

                    if ATTR_ALTITUDE in trigger.attributes:
                        target.attributes[ATTR_ALTITUDE] = round(
                            trigger.attributes[ATTR_ALTITUDE]
                        )
                    else:
                        if ATTR_ALTITUDE in target.attributes:
                            target.attributes.pop(ATTR_ALTITUDE)

                    if ATTR_VERTICAL_ACCURACY in trigger.attributes:
                        target.attributes[ATTR_VERTICAL_ACCURACY] = trigger.attributes[
                            ATTR_VERTICAL_ACCURACY
                        ]
                    else:
                        if ATTR_VERTICAL_ACCURACY in target.attributes:
                            target.attributes.pop(ATTR_VERTICAL_ACCURACY)

                    if ATTR_ENTITY_PICTURE in trigger.attributes:
                        target.attributes[ATTR_ENTITY_PICTURE] = trigger.attributes[
                            ATTR_ENTITY_PICTURE
                        ]
                    else:
                        if ATTR_ENTITY_PICTURE in target.attributes:
                            target.attributes.pop(ATTR_ENTITY_PICTURE)

                    target.attributes["source"] = trigger.entity_id
                    target.attributes["reported_state"] = trigger.state
                    target.attributes["person_name"] = string.capwords(
                        trigger.personName
                    )
                    target.attributes["location_time"] = new_location_time.strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                    )

                    # Determine the zone and the icon to be used:

                    if trigger.state.lower() in ["away", STATE_ON, STATE_NOT_HOME]:
                        friendly_name_location = "Away"
                    elif trigger.state == "Home":
                        friendly_name_location = "Home"
                    else:
                        friendly_name_location = trigger.state

                    if "zone" in trigger.attributes:
                        reportedZone = trigger.attributes["zone"]
                    else:
                        reportedZone = (
                            trigger.state.lower().replace(" ", "_").replace("'", "_")
                        )
                    zoneEntityID = "zone." + reportedZone
                    zoneStateObject = pli.hass.states.get(zoneEntityID)
                    icon = "mdi:help-circle"
                    if zoneStateObject is None or reportedZone.lower().endswith(
                        "stationary"
                    ):
                        # Eliminate stray zone names:
                        friendly_name_location = "Away"
                    else:
                        zoneAttributesObject = zoneStateObject.attributes.copy()
                        if "friendly_name" in zoneAttributesObject:
                            friendly_name_location = zoneAttributesObject[
                                "friendly_name"
                            ]
                        if "icon" in zoneAttributesObject:
                            icon = zoneAttributesObject["icon"]

                    target.attributes["icon"] = icon
                    target.attributes["zone"] = reportedZone

                    _LOGGER.debug(
                        "(%s) zone = %s; icon = %s; friendly_name_location = %s",
                        trigger.entity_id,
                        reportedZone,
                        target.attributes["icon"],
                        friendly_name_location,
                    )

                    # Format new friendly_name and the template to be updated by geocoding:

                    previous_locality = target.this_entity_info["locality"]
                    if string.capwords(trigger.personName) == trigger.friendlyName:
                        friendly_name_identity = trigger.friendlyName
                    else:
                        friendly_name_identity = f"{string.capwords(trigger.personName)} ({trigger.friendlyName})"
                    if (
                        friendly_name_location == "Away"
                    ):  # "<identity> is in <locality>"; add new locality in geocoding
                        template = f"{friendly_name_identity} is in <locality>"
                        friendly_name = template.replace(
                            "<locality>", previous_locality
                        )
                    else:  # "<identity> is at <name>"; don't add locality
                        friendly_name = (
                            f"{friendly_name_identity} is at {friendly_name_location}"
                        )
                        template = friendly_name

                    target.attributes["friendly_name"] = friendly_name

                    ha_just_started = pli.attributes["startup"]
                    if ha_just_started:
                        _LOGGER.debug("HA just started flag is on")

                    if reportedZone == "home":
                        target.attributes[ATTR_LATITUDE] = pli.attributes[
                            "home_latitude"
                        ]
                        target.attributes[ATTR_LONGITUDE] = pli.attributes[
                            "home_longitude"
                        ]

                    # Set up something like https://philhawthorne.com/making-home-assistants-presence-detection-not-so-binary/
                    # If Home Assistant just started, just go with Home or Away as the initial state.

                    if trigger.stateHomeAway == "Home":
                        if (
                            oldTargetState in ["just left", "none"]
                            or ha_just_started
                            or (pli.configuration[CONF_MINUTES_JUST_ARRIVED] == 0)
                        ):
                            newTargetState = "Home"

                            target.attributes[ATTR_BREAD_CRUMBS] = newTargetState
                            target.attributes[ATTR_COMPASS_BEARING] = 0
                            target.attributes[ATTR_DIRECTION] = "home"

                            call_rest_command_service(
                                trigger.personName, newTargetState
                            )
                        elif oldTargetState == "home":
                            newTargetState = "Home"
                        elif oldTargetState == "just arrived":
                            newTargetState = "Just Arrived"
                        else:
                            newTargetState = "Just Arrived"
                            change_state_later(
                                target.entity_id,
                                newTargetState,
                                "Home",
                                pli.configuration[CONF_MINUTES_JUST_ARRIVED],
                            )
                            call_rest_command_service(
                                trigger.personName, newTargetState
                            )
                    else:
                        if oldTargetState != "away" and (
                            oldTargetState == "none"
                            or ha_just_started
                            or (pli.configuration[CONF_MINUTES_JUST_LEFT] == 0)
                        ):
                            newTargetState = "Away"
                            if pli.configuration[CONF_HOURS_EXTENDED_AWAY] != 0:
                                change_state_later(
                                    target.entity_id,
                                    "Away",
                                    "Extended Away",
                                    (pli.configuration[CONF_HOURS_EXTENDED_AWAY] * 60),
                                )
                            call_rest_command_service(
                                trigger.personName, newTargetState
                            )
                        elif oldTargetState == "just left":
                            newTargetState = "Just Left"
                        elif oldTargetState == "away":
                            newTargetState = "Away"
                        elif oldTargetState == "extended away":
                            newTargetState = "Extended Away"
                        else:
                            newTargetState = "Just Left"
                            change_state_later(
                                target.entity_id,
                                newTargetState,
                                "Away",
                                pli.configuration[CONF_MINUTES_JUST_LEFT],
                            )
                            call_rest_command_service(
                                trigger.personName, newTargetState
                            )

                    if ha_just_started:
                        target.attributes[ATTR_BREAD_CRUMBS] = newTargetState

                    target.state = newTargetState
                    target.attributes["version"] = f"{DOMAIN} {VERSION}"

                    target.set_state()

                    # Call service to "reverse geocode" the location.
                    # For devices at Home, this will only be done initially or on arrival.

                    if (newTargetState in ["Home", "Just Arrived"]) and (
                        oldTargetState in ["away", "extended away", "just left"]
                    ):
                        force_update = True
                    else:
                        force_update = False
                    if (
                        newTargetState != "Home"
                        or pli.attributes["startup"]
                        or force_update
                    ):
                        service_data = {
                            "entity_id": target.entity_id,
                            "friendly_name_template": template,
                            "force_update": force_update,
                        }
                        pli.hass.services.call(
                            DOMAIN, "reverse_geocode", service_data, False
                        )

                _LOGGER.debug(
                    "(%s) TARGET_LOCK release...",
                    trigger.entity_id,
                )
        _LOGGER.debug(
            "(%s) === Return ===",
            trigger.entity_id,
        )

    pli.hass.services.register(DOMAIN, "process_trigger", handle_process_trigger)
    return True
