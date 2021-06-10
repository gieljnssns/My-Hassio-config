##########################################################################################
# Python script to count low battery entities
# Based on https://community.home-assistant.io/t/develop-and-rebuild-template-sensor-to-python-script/228699/13 and
# https://community.home-assistant.io/t/script-to-warn-on-low-battery/189891/16
##########################################################################################

attributes = {}

list_device_tracker_battery_entities = []
list_friendly_device_tracker_battery_entities = []
list_sensor_battery_entities = []
list_friendly_sensor_battery_entities = []
list_binary_sensor_battery_entities = []
list_friendly_binary_sensor_battery_entities = []
list_climate_battery_entities = []
list_friendly_climate_battery_entities = []


def persistent_warning_message(devices):
    devices = "\n".join(devices)
    service_data = {
        "title": "Low Battery",
        "notification_id": "low_battery",
        "message": f"{devices}\n",
    }
    hass.services.call("persistent_notification", "create", service_data, False)
    logger.info(service_data["message"])


def get_battery_entities():
    def get_device_tracker_battery_entities():
        out = {}
        for entity_id in hass.states.entity_ids("device_tracker"):
            state = hass.states.get(entity_id)
            if "battery_level" in state.attributes:
                friendly_name = state.attributes["friendly_name"]
                list_friendly_device_tracker_battery_entities.append(friendly_name)
                list_device_tracker_battery_entities.append(entity_id)
                out.update({entity_id: state.attributes["battery_level"]})
        return out

    def get_sensor_battery_entities():
        out = {}
        for entity_id in hass.states.entity_ids("sensor"):
            state = hass.states.get(entity_id)
            if (
                state.attributes.get("device_class") is "battery"
                and "is_charging" not in state.attributes
                and "charging" not in state.state
                and "discharging" not in state.state
                and "unavailable" not in state.state
                and "unknown" not in state.state
            ):
                friendly_name = state.attributes["friendly_name"]
                list_friendly_sensor_battery_entities.append(friendly_name)
                list_sensor_battery_entities.append(entity_id)
                out.update({entity_id: int(state.state)})
        return out

    def get_binary_sensor_battery_entities():
        out = {}
        for entity_id in hass.states.entity_ids("binary_sensor"):
            state = hass.states.get(entity_id)
            if "battery_level" in state.attributes:
                friendly_name = state.attributes["friendly_name"]
                list_friendly_binary_sensor_battery_entities.append(friendly_name)
                list_binary_sensor_battery_entities.append(entity_id)
                out.update({entity_id: state.attributes["battery_level"]})
        return out

    # def get_climate_battery_entities():
    #     out = {}
    #     for entity_id in hass.states.entity_ids("climate"):
    #         state = hass.states.get(entity_id)

    #         if "battery_level" in state.attributes:
    #             friendly_name = state.attributes["friendly_name"]
    #             list_friendly_climate_battery_entities.append(friendly_name)
    #             list_climate_battery_entities.append(entity_id)
    #             out.update({entity_id: state.attributes["battery_level"]})
    #     return out

    entities = {}
    entities.update(get_device_tracker_battery_entities())
    entities.update(get_sensor_battery_entities())
    entities.update(get_binary_sensor_battery_entities())
    # entities.update(get_climate_battery_entities())
    return entities


def get_low_battery_entities(battery_entities, threshold):
    if len(battery_entities) is 0:
        return None
    return [
        "".join(entity_id + ": " + str(value) + "%")
        for entity_id, value in battery_entities.items()
        if value < threshold
    ]


threshold = data.get("threshold", 10)
low_battery_devices = get_low_battery_entities(get_battery_entities(), threshold)
if len(low_battery_devices) > 0:
    persistent_warning_message(low_battery_devices)

if len(low_battery_devices) > 0:
    icon = "mdi:battery-10"
    icon_color = "red"
    attributes["all_entities"] = ",\n".join(sorted(low_battery_devices))
else:
    icon = "mdi:thumb-up"
    icon_color = "green"
    attributes["all_entities"] = "All entities OK!"

attributes["friendly_name"] = "Low battery"
attributes["battery_sensors"] = ",\n".join(
    sorted(list_friendly_sensor_battery_entities)
)
attributes["battery_binary_sensors"] = ",\n".join(
    sorted(list_friendly_binary_sensor_battery_entities)
)
attributes["battery_trackers"] = ",\n".join(
    sorted(list_friendly_device_tracker_battery_entities)
)
attributes["battery_climate"] = ",\n".join(
    sorted(list_friendly_climate_battery_entities)
)
attributes["icon"] = icon
attributes["icon_color"] = icon_color

# set the sensor
hass.states.set("sensor.low_battery", len(low_battery_devices), attributes)
