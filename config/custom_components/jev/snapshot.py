"""What the house looks like to Assist.

Only entities the user exposed to Assist are described here. That boundary is the
user's, not ours: they already decided which entities a voice assistant may see, and
a spoken command is not a reason to widen it.

This applies to the voice path alone. The four service actions send whatever the
caller targets, exposed or not, because an automation names its entities on purpose.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.components.conversation import DOMAIN as CONVERSATION_DOMAIN
from homeassistant.components.homeassistant.exposed_entities import async_should_expose
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import floor_registry as fr

# Domains a spoken command can act on through a built-in intent. Anything else is
# left to the fallback agent rather than half-handled here.
#
# lock is deliberately absent. Home Assistant maps turn_on to lock.lock and turn_off
# to lock.unlock (homeassistant/components/intent/__init__.py, "# on = lock"), which
# is the opposite way round from how anyone says it, and a probability with no
# reasoning should not be deciding whether a door opens. Ask the fallback agent.
CONTROLLABLE = (
    "light",
    "switch",
    "fan",
    "cover",
    "media_player",
    "climate",
    "vacuum",
    "input_boolean",
    "scene",
    "script",
)

# Covers that open a way into the house, left out for the reason lock is: "open the
# garage" matched at the 0.6 default floor would open it.
ENTRANCE_COVERS = ("door", "garage", "gate")


@dataclass(slots=True)
class ExposedEntity:
    """One entity, as the model will see it."""

    entity_id: str
    name: str
    domain: str
    area: str | None
    state: str
    # Home Assistant matches areas by id, and the model reads them by name.
    area_id: str | None = None

    def as_option(self) -> str:
        where = f", in the {self.area}" if self.area else ""
        return f"{self.name}{where} ({self.domain}, currently {self.state})"


@dataclass(slots=True)
class HomeSnapshot:
    """Everything one request is allowed to know about the house."""

    entities: list[ExposedEntity] = field(default_factory=list)
    areas: list[str] = field(default_factory=list)
    floors: list[str] = field(default_factory=list)

    @property
    def domains(self) -> list[str]:
        return sorted({e.domain for e in self.entities})

    def by_id(self, entity_id: str) -> ExposedEntity | None:
        return next((e for e in self.entities if e.entity_id == entity_id), None)

    def in_area(self, area: str, domain: str | None = None) -> list[ExposedEntity]:
        return [
            e
            for e in self.entities
            if e.area == area and (domain is None or e.domain == domain)
        ]

    def as_state(self) -> dict[str, object]:
        """The shape sent to TypeSafe, with field names the model reads as labels."""
        return {
            "entities": [
                {
                    "entity_id": e.entity_id,
                    "name": e.name,
                    "domain": e.domain,
                    "area": e.area or "unassigned",
                    "state": e.state,
                }
                for e in self.entities
            ],
            "areas": self.areas,
            "floors": self.floors,
        }


@callback
def async_snapshot(hass: HomeAssistant, limit: int) -> HomeSnapshot:
    """Collect the exposed, controllable entities, newest registry state."""
    entities = er.async_get(hass)
    devices = dr.async_get(hass)
    areas = ar.async_get(hass)
    floors = fr.async_get(hass)

    def area_id_of(entity_id: str) -> str | None:
        entry = entities.async_get(entity_id)
        if entry is None:
            return None
        if entry.area_id is not None:
            return entry.area_id
        if entry.device_id:
            device = devices.async_get(entry.device_id)
            return device.area_id if device else None
        return None

    found: list[ExposedEntity] = []
    for state in hass.states.async_all(CONTROLLABLE):
        if not async_should_expose(hass, CONVERSATION_DOMAIN, state.entity_id):
            continue
        if (
            state.domain == "cover"
            and state.attributes.get("device_class") in ENTRANCE_COVERS
        ):
            continue
        area_id = area_id_of(state.entity_id)
        area = areas.async_get_area(area_id) if area_id else None
        found.append(
            ExposedEntity(
                entity_id=state.entity_id,
                name=state.name,
                domain=state.domain,
                area=area.name if area else None,
                state=state.state,
                area_id=area.id if area else None,
            )
        )
    # Sorted so the option list is stable between requests, which makes a trace
    # readable when the same command is tried twice.
    found.sort(key=lambda e: e.entity_id)
    found = found[:limit]
    # Counted after the cap, so a room that only had entities past the limit is not
    # offered as somewhere the command could go.
    used_area_ids = {e.area_id for e in found if e.area_id}

    # Only rooms that hold something the agent may act on.
    #
    # Measured on a development instance: the registry held Kitchen, Bedroom and
    # Living Room from
    # real devices alongside the three test rooms. Offering all six let "kill the
    # lights in the kitchen" come back as area=Kitchen at 0.98 confidence, which was
    # the right answer to the question asked and named a room holding nothing
    # exposed. The intent then matched nothing and the sentence fell back. A room
    # the agent cannot act in is not an option, it is a trap.
    used_areas = [areas.async_get_area(a) for a in used_area_ids]
    used_floor_ids = {a.floor_id for a in used_areas if a and a.floor_id}

    return HomeSnapshot(
        entities=found,
        areas=sorted(a.name for a in used_areas if a),
        floors=sorted(
            f.name for f in floors.async_list_floors() if f.floor_id in used_floor_ids
        ),
    )
