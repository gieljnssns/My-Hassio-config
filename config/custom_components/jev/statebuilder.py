"""Turn picked entities, devices and areas into the state Jev reads.

The docs are explicit that a JSON object beats a flattened sentence, because the
model reads the field names as labels. So an entity becomes a small record with its
name, its value, its unit and where it lives, rather than a line of prose someone
has to template by hand.
"""

from __future__ import annotations

from typing import Any

from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
)
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.target import (
    TargetSelection,
    async_extract_referenced_entity_ids,
)
from homeassistant.util import dt as dt_util

from .const import DOMAIN, MAX_TARGET_ENTITIES

# Attributes worth sending for every entity. Everything else is skipped: a weather
# forecast or a media player's picture is thousands of tokens of noise, and the
# caller pays for every one of them.
_ALWAYS = (ATTR_DEVICE_CLASS, ATTR_UNIT_OF_MEASUREMENT)
# Left out even when every attribute is asked for. A camera's access token is a live
# credential, an entity picture URL often carries one, and a location is where the
# person is. None of them helps Jev judge a state, and all of them are billed.
_NEVER = frozenset(
    {"access_token", "entity_picture", "latitude", "longitude", "gps_accuracy"}
)


@callback
def _area_name(
    entity_id: str,
    entities: er.EntityRegistry,
    devices: dr.DeviceRegistry,
    areas: ar.AreaRegistry,
) -> str | None:
    entry = entities.async_get(entity_id)
    if entry is None:
        return None
    area_id = entry.area_id
    if area_id is None and entry.device_id:
        device = devices.async_get(entry.device_id)
        area_id = device.area_id if device else None
    if area_id is None:
        return None
    area = areas.async_get_area(area_id)
    return area.name if area else None


@callback
def _describe(
    state: State,
    entities: er.EntityRegistry,
    devices: dr.DeviceRegistry,
    areas: ar.AreaRegistry,
    include_attributes: bool,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "entity_id": state.entity_id,
        # Sent verbatim, including unavailable and unknown. That a sensor has
        # stopped reporting is a fact the question may turn on, and replacing it
        # with a guess would be worse than saying so.
        "state": state.state,
    }
    # Only when it says something the entity id does not. An entity with no
    # friendly name would otherwise carry its id twice, and both copies are billed.
    if (name := state.attributes.get(ATTR_FRIENDLY_NAME)) and name != state.entity_id:
        record["name"] = name
    for attribute in _ALWAYS:
        if (value := state.attributes.get(attribute)) is not None:
            record[attribute] = value
    if area := _area_name(state.entity_id, entities, devices, areas):
        record["area"] = area
    record["changed"] = dt_util.get_age(state.last_changed) + " ago"
    if include_attributes:
        record["attributes"] = {
            k: v
            for k, v in state.attributes.items()
            if k not in (ATTR_FRIENDLY_NAME, *_ALWAYS) and k not in _NEVER
        }
    return record


@callback
def async_entity_records(
    hass: HomeAssistant,
    selector: dict[str, Any],
    include_attributes: bool = False,
) -> list[dict[str, Any]]:
    """Resolve a target selector and describe every entity behind it."""
    selected = async_extract_referenced_entity_ids(
        hass, TargetSelection(selector), expand_group=True
    )
    missing = {
        "device": selected.missing_devices,
        "area": selected.missing_areas,
        "floor": selected.missing_floors,
        "label": selected.missing_labels,
    }
    if gone := {kind: sorted(ids) for kind, ids in missing.items() if ids}:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="missing_targets",
            translation_placeholders={"targets": str(gone)},
        )

    entity_ids = sorted(selected.referenced | selected.indirectly_referenced)
    if not entity_ids:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="empty_target"
        )
    if len(entity_ids) > MAX_TARGET_ENTITIES:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="too_many_entities",
            translation_placeholders={
                "count": str(len(entity_ids)),
                "limit": str(MAX_TARGET_ENTITIES),
            },
        )

    entities = er.async_get(hass)
    devices = dr.async_get(hass)
    areas = ar.async_get(hass)
    records = []
    for entity_id in entity_ids:
        if (state := hass.states.get(entity_id)) is None:
            continue
        records.append(_describe(state, entities, devices, areas, include_attributes))
    # Entity ids that exist in no state are referenced without being missing, so
    # the check above lets them through. Asking about an empty list is still billed.
    if not records:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="empty_target"
        )
    return records


@callback
def async_build_state(
    hass: HomeAssistant,
    text: Any | None,
    selector: dict[str, Any] | None,
    include_attributes: bool = False,
) -> Any:
    """Compose what gets sent as `state`.

    Text on its own goes as it is, which keeps every existing automation working.
    As soon as entities are involved the state becomes an object, because the model
    reads field names as labels and a list of readings needs them.
    """
    if not selector:
        return text
    records = async_entity_records(hass, selector, include_attributes)
    payload: dict[str, Any] = {
        "now": dt_util.now().strftime("%Y-%m-%d %H:%M %A"),
        "entities": records,
    }
    if text:
        payload["note"] = text
    return payload
