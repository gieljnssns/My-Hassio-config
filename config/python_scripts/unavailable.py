##########################################################################################
# Python script to replace formely used template sensor, which causes havoc in HA 115
# https://community.home-assistant.io/t/develop-and-rebuild-template-sensor-to-python-script/228699
# thanks to @VDRainer for providing most of the code here, and persevering my thoughts and
# questions
# 23 sep 2020 @mariusthvdb
##########################################################################################

# excludes based on certain conditions
# if hass.states.get("binary_sensor.outside_daylight_sensor").state == "on":
#     exclude_conditional_entities = ["light.parking_light"]
# else:
#     exclude_conditional_entities = []

# excludes based on certain conditions
exclude_conditional_entities = []

exclude_entities = []


excludes = exclude_conditional_entities + exclude_entities

exclude_groups = [
    "group.ignored_entities"
]  # configured in HA group outside this python script
exclude_domains = ["automation", "geo_location", "group"]

# some variables
count_unfiltered = 0
count_all = 0
count_none = 0
count_unavailable = 0
# count_unknown = 0
count_sensors = 0

list_unfiltered = []
list_all = []
list_none = []
list_unavailable = []
# list_unknown = []
list_sensors = []


attributes = {}

# create unfiltered list to fine-tune filtering
for entity_id in hass.states.entity_ids():
    state = hass.states.get(entity_id).state
    if state in ["none", "unavailable"]:
        list_unfiltered.append(entity_id)
        count_unfiltered = count_unfiltered + 1

# add groups entities to exclude_entities list
for group in exclude_groups:
    for entity_id in hass.states.get(group).attributes["entity_id"]:
        excludes.append(entity_id)

# iterate over all entities
for entity_id in hass.states.entity_ids():
    domain = entity_id.split(".")[0]
    if entity_id not in excludes and domain not in exclude_domains:
        state = hass.states.get(entity_id).state
        if state in ["none", "unavailable"]:
            count_all = count_all + 1
            list_all.append(entity_id)
            if state == "none":
                count_none = count_none + 1
                list_none.append(entity_id)
            elif state == "unavailable":
                count_unavailable = count_unavailable + 1
                list_unavailable.append(entity_id)
            # elif state == "unknown":
            #     count_unknown = count_unknown + 1
            #     list_unknown.append(entity_id)
            if domain == "sensor":
                count_sensors = count_sensors + 1
                list_sensors.append(entity_id)

# build the attributes
if count_all > 0:
    icon = "mdi:thumb-down"
    icon_color = "red"
    attributes["all_entities"] = ",\n".join(sorted(list_all))
else:
    icon = "mdi:thumb-up"
    icon_color = "green"
    attributes["all_entities"] = "All entities OK!"

attributes["all_count"] = count_all
if count_none > 0:
    attributes["none_entities"] = ",\n".join(sorted(list_none))
else:
    attributes["none_entities"] = "No None entities"

attributes["none_count"] = count_none
if count_unavailable > 0:
    attributes["unavailable_entities"] = ",\n".join(sorted(list_unavailable))
else:
    attributes["unavailable_entities"] = "No Unavailable entities"

attributes["unavailable_count"] = count_unavailable
# if count_unknown > 0:
#     attributes["unknown_entities"] = ",\n".join(sorted(list_unknown))
# else:
#     attributes["unknown_entities"] = "No Unknown entities"

# attributes["unknown_count"] = count_unknown
if count_sensors > 0:
    attributes["sensors_entities"] = ",\n".join(sorted(list_sensors))
else:
    attributes["sensors_entities"] = "All sensors Ok"

attributes["sensors_count"] = count_sensors
if count_unfiltered > 0:
    attributes["unfiltered_entities"] = ",\n".join(sorted(list_unfiltered))
else:
    attributes["unfiltered_entities"] = "All and Unfiltered Ok"


attributes["unfiltered_count"] = count_unfiltered
attributes["friendly_name"] = "Unavailable"
attributes["icon"] = icon
attributes["icon_color"] = icon_color
attributes["unit_of_measurement"] = "st"

# set the sensor
hass.states.set("sensor.uun_ordered", count_all, attributes)

# How it all started
# count = 0
# attributes = {}
#
# for entity_id in hass.states.entity_ids():
#     state = hass.states.get(entity_id).state
#     if state in ['unknown']:
#         attributes[entity_id] = state
#         count = count + 1
#
# attributes['friendly_name'] = 'Unavailable Entities'
# attributes['icon'] = 'mdi:message-alert-outline'
#
# hass.states.set('sensor.unavailable_entities', count, attributes)
