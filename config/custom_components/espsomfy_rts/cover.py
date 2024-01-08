"""Support for ESPSomfy RTS Shades and Blinds."""
from __future__ import annotations

from typing import Any, Final
import voluptuous as vol
from collections.abc import Mapping

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.components.group.cover import CoverGroup
from homeassistant.config_entries import (ConfigEntry, ConfigEntries)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import make_entity_service_schema
from homeassistant.helpers import entity_platform, entity_registry
from homeassistant.helpers.entity_registry import async_entries_for_config_entry

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util


from .const import DOMAIN, EVT_CONNECTED, EVT_SHADEREMOVED, EVT_SHADESTATE, EVT_SHADECOMMAND
from .controller import ESPSomfyController
from .entity import ESPSomfyEntity

SVC_OPEN_SHADE = "open_shade"
SVC_CLOSE_SHADE = "close_shade"
SVC_STOP_SHADE = "stop_shade"
SVC_SET_SHADE_POS = "set_shade_position"
SVC_TILT_OPEN = "tilt_open"
SVC_TILT_CLOSE = "tilt_close"
SVC_SET_TILT_POS = "set_tilt_position"
SVC_SET_CURRENT_POS = "set_current_position"
SVC_SET_CURRENT_TILT_POS = "set_current_tilt_position"
SVC_SET_SUNNY = "set_sunny"
SVC_SET_WINDY = "set_windy"

KEY_OPEN_CLOSE = "open_close"
KEY_STOP = "stop"
KEY_POSITION = "position"
ATTR_SUNNY = "sunny"
ATTR_WINDY = "windy"

POSITION_SERVICE_SCHEMA: Final = make_entity_service_schema(
    {vol.Required(ATTR_POSITION): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            )}
)
TILT_POSITION_SERVICE_SCHEMA: Final = make_entity_service_schema(
    {vol.Required(ATTR_TILT_POSITION): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            )}
)
SUNNY_SERVICE_SCHEMA: Final = make_entity_service_schema(
    {vol.Required(ATTR_SUNNY): vol.All(vol.Coerce(bool))}
)
WINDY_SERVICE_SCHEMA: Final = make_entity_service_schema(
    {vol.Required(ATTR_WINDY): vol.All(vol.Coerce(bool))}
)



async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up shades for the shade controller."""
    controller = hass.data[DOMAIN][config_entry.entry_id]
    new_shades = []

    for shade in controller.api.shades:
        try:
            # We do not want any of the dry contacts here.
            if "shadeType" in shade and not int(shade["shadeType"]) == 9:
                new_shades.append(ESPSomfyShade(controller, shade))

        except KeyError:
            pass
    if new_shades:
        async_add_entities(new_shades)

    new_groups = []
    for group in controller.api.groups:
        try:
            new_groups.append(ESPSomfyGroup(hass=hass, controller=controller, data=group))
        except KeyError:
            pass
    if new_groups:
        async_add_entities(new_groups)


    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SVC_SET_SHADE_POS,
        POSITION_SERVICE_SCHEMA,
        "async_set_cover_position",
    )
    platform.async_register_entity_service(
        SVC_SET_TILT_POS,
        TILT_POSITION_SERVICE_SCHEMA,
        "async_set_cover_tilt_position",
    )
    platform.async_register_entity_service(SVC_OPEN_SHADE, {}, "async_open_cover")
    platform.async_register_entity_service(SVC_CLOSE_SHADE, {}, "async_close_cover")
    platform.async_register_entity_service(SVC_STOP_SHADE, {}, "async_stop_cover")
    platform.async_register_entity_service(SVC_TILT_OPEN, {}, "async_tilt_open")
    platform.async_register_entity_service(SVC_TILT_CLOSE, {}, "async_tilt_close")
    platform.async_register_entity_service(SVC_SET_CURRENT_POS, POSITION_SERVICE_SCHEMA, "async_set_current_position")
    platform.async_register_entity_service(SVC_SET_CURRENT_TILT_POS, TILT_POSITION_SERVICE_SCHEMA, "async_set_current_tilt_position")
    platform.async_register_entity_service(SVC_SET_SUNNY, SUNNY_SERVICE_SCHEMA, "async_set_sunny")
    platform.async_register_entity_service(SVC_SET_WINDY, WINDY_SERVICE_SCHEMA, "async_set_windy")



class ESPSomfyGroup(CoverGroup, ESPSomfyEntity):
    """A grpi[] that is associated with a controller"""

    def __init__(self, hass: HomeAssistant, controller: ESPSomfyController, data) -> None:
        ESPSomfyEntity.__init__(self=self, controller=controller, data=data)
        self._hass = hass
        self._available = True
        self._controller = controller
        self._group_id = data["groupId"]
        self._attr_device_class = CoverDeviceClass.SHADE
        self._linked_shade_ids = []

        if "linkedShades" in data:
            for linked_shade in data["linkedShades"]:
                self._linked_shade_ids.append(int(linked_shade["shadeId"]))
        uuid = f"{controller.unique_id}_group{self._group_id}"

        entities = entity_registry.async_get(hass)
        shade_ids:list[str] = []
        for entity in async_entries_for_config_entry(entities, self._controller.config_entry_id):
            for cover_id in self._linked_shade_ids:
                if(entity.unique_id == f"{self._controller.unique_id}_{cover_id}"):
                    shade_ids.append(entity.entity_id)

        super().__init__(unique_id=uuid, name=data["name"], entities=shade_ids)

    async def async_added_to_hass(self) -> None:
        """Subscribe to device events."""
        entities = entity_registry.async_get(self._hass)
        shade_ids:list[str] = []
        for entity in async_entries_for_config_entry(entities, self._controller.config_entry_id):
            for cover_id in self._linked_shade_ids:
                if(entity.unique_id == f"{self._controller.unique_id}_{cover_id}"):
                    if hasattr(self, "_entities"):
                        if not entity.entity_id in self._entities:
                            self._entities.append(entity.entity_id)
                    elif hasattr(self, "_entity_ids"):
                        if not entity.entity_id in self._entity_ids:
                            self._entity_ids.append(entity.entity_id)
                    shade_ids.append(entity.entity_id)
        # self._entities = shade_ids
        self._attr_extra_state_attributes = {ATTR_ENTITY_ID: shade_ids}
        await super().async_added_to_hass()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if(self._controller.data["event"] == EVT_CONNECTED and "connected" in self._controller.data):
            self._available = bool(self._controller.data["connected"])
            self.async_write_ha_state()
        elif "groupId" in self._controller.data:
            if self._controller.data["groupId"] == self._group_id:
                if "linkedShades" in self._controller.data:
                    self._linked_shade_ids.clear()
                    for shade in self._controller.data["linkedShades"]:
                        self._linked_shade_ids.append(int(shade["shadeId"]))
                self._available = True
                self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Indicates whether the shade is available"""
        return self._available

    @property
    def should_poll(self) -> bool:
        """Indicates whether the group should poll for information"""
        return False
    @property
    def icon(self) -> str:
        if hasattr(self, "_attr_icon"):
            return self._attr_icon
        return "mdi:table-multiple"

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._controller.api.open_group(self._group_id)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        await self._controller.api.close_group(self._group_id)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Hold cover."""
        # print(f"Stopping Cover id#{self._shade_id}")
        await self._controller.api.stop_group(self._group_id)

class ESPSomfyShade(ESPSomfyEntity, CoverEntity):
    """A shade that is associated with a controller"""

    def __init__(self, controller: ESPSomfyController, data) -> None:
        super().__init__(controller=controller, data=data)
        self._controller = controller
        self._shade_id = data["shadeId"]
        self._position = data["position"]
        self._tilt_position = 100
        self._tilt_direction = 0
        self._attr_unique_id = f"{controller.unique_id}_{self._shade_id}"
        self._attr_name = data["name"]
        self._direction = 0
        self._available = True
        self._has_tilt = False
        self._has_lift = True
        self._flip_position = False
        self._tilt_type = 0
        self._state_attributes: dict[str, Any] = dict([])

        if "flipPosition" in data and data["flipPosition"] is True:
            self._flip_position = True

        self._attr_device_class = CoverDeviceClass.SHADE


        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        if "hasTilt" in data and data["hasTilt"] is True:
            self._attr_supported_features |= (
                CoverEntityFeature.OPEN_TILT
                | CoverEntityFeature.CLOSE_TILT
                | CoverEntityFeature.SET_TILT_POSITION
            )
            self._has_tilt = True
            self._tilt_position = data["tiltPosition"] if "tiltPosition" in data else 100
            self._tilt_direction = data["tiltDirection"] if "tiltDirecion" in data else 0
        if "tiltType" in data:
            self._tilt_type = int(data["tiltType"])
            match int(data["tiltType"]):
                case 1 | 2 | 4:
                    self._has_tilt = True
                    self._attr_supported_features |= (
                        CoverEntityFeature.OPEN_TILT
                        | CoverEntityFeature.CLOSE_TILT
                        | CoverEntityFeature.SET_TILT_POSITION
                    )
                case 3:
                    self._has_tilt = True
                    self._has_lift = False
                    self._attr_supported_features = (
                        CoverEntityFeature.OPEN_TILT
                        | CoverEntityFeature.STOP_TILT
                        | CoverEntityFeature.CLOSE_TILT
                        | CoverEntityFeature.SET_TILT_POSITION
                    )

        if "shadeType" in data:
            match int(data["shadeType"]):
                case 1:
                    self._attr_device_class = CoverDeviceClass.BLIND
                case 2 | 7 | 8:
                    self._attr_device_class = CoverDeviceClass.CURTAIN
                case 3:
                    self._attr_device_class = CoverDeviceClass.AWNING
                case 4:
                    self._attr_device_class = CoverDeviceClass.SHUTTER
                case 5:
                    self._attr_device_class = CoverDeviceClass.GARAGE
                case 6:
                    self._attr_device_class = CoverDeviceClass.GARAGE
                case 11 | 12 | 13:
                    self._attr_device_class = CoverDeviceClass.GATE
                case _:
                    self._attr_device_class = CoverDeviceClass.SHADE


        self._attr_is_closed: bool = False
        # print(f"Set up shade {self._attr_unique_id} - {self._attr_name}")

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if(self._controller.data["event"] == EVT_CONNECTED and "connected" in self._controller.data):
            self._available = bool(self._controller.data["connected"])
            self.async_write_ha_state()
        elif "shadeId" in self._controller.data:
            if self._controller.data["shadeId"] == self._shade_id:
                if self._controller.data["event"] == EVT_SHADESTATE:
                    if "remoteAddress" in self._controller.data:
                        self._state_attributes["remote_address"] = self._controller.data["remoteAddress"]
                    if "flipPosition" in self._controller.data:
                        self._flip_position = bool(self._controller.data["flipPosition"])
                    if "position" in self._controller.data:
                        self._position = int(self._controller.data["position"])
                    if "direction" in self._controller.data:
                        self._direction = int(self._controller.data["direction"])
                    if "hasTilt" in self._controller.data:
                        self._has_tilt = self._controller.data["hasTilt"]
                    if "tiltType" in self._controller.data:
                        match int(self._controller.data["tiltType"]):
                            case 1 | 2:
                                self._has_tilt = True
                            case 3:
                                self._has_tilt = True
                                self._has_lift = False
                            case _:
                                self._has_tilt = False
                                self._has_lift = True
                    if self._has_tilt is True:
                        if "tiltDirection" in self._controller.data:
                            self._tilt_direction = int(self._controller.data["tiltDirection"])
                        if "tiltPosition" in self._controller.data:
                            self._tilt_position = int(self._controller.data["tiltPosition"])
                        if "tiltTarget" in self._controller.data:
                            self._state_attributes["tilt_target"] = int(self._controller.data["tiltTarget"])
                        if "myTiltPos" in self._controller.data:
                            self._state_attributes["my_tilt_pos"] = int(self._controller.data["myTiltPos"])
                    if "target" in self._controller.data:
                        self._state_attributes["position_target"] = int(self._controller.data["target"])
                    if "mypos" in self._controller.data:
                        self._state_attributes["my_pos"] = int(self._controller.data["mypos"])

                    self._available = True
                elif self._controller.data["event"] == EVT_SHADEREMOVED:
                    self._available = False
                elif self._controller.data["event"] == EVT_SHADECOMMAND:
                    if "remoteAddress" in self._controller.data:
                        self._state_attributes["remote_address"] = self._controller.data["remoteAddress"]
                    if "cmd" in self._controller.data:
                        self._state_attributes["last_cmd"] = self._controller.data["cmd"]
                    if "source" in self._controller.data:
                        self._state_attributes["cmd_source"] = self._controller.data["source"]
                    if "sourceAddress" in self._controller.data:
                        self._state_attributes["cmd_address"] = self._controller.data["sourceAddress"]
                    self._state_attributes["cmd_fired"] = dt_util.as_timestamp(dt_util.utcnow())
                    bus_data = {
                        "entity_id": self.entity_id,
                        "event_key": EVT_SHADECOMMAND,
                        "name": self.name,
                        "source": self._state_attributes.get("cmd_source", ""),
                        "remote_address": self._state_attributes.get("remote_address", 0),
                        "source_address": self._state_attributes.get("cmd_address", 0),
                        "command": self._state_attributes.get("last_cmd", ""),
                        "timestamp": self._state_attributes.get("cmd_fired")
                    }
                    self.hass.bus.async_fire("espsomfy-rts_event", bus_data)
                self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Indicates whether the shade is available"""
        return self._available

    @property
    def should_poll(self) -> bool:
        """Indicates whether the shade should poll for information"""
        return False
    @property
    def icon(self) -> str:
        if hasattr(self, "_attr_icon"):
            return self._attr_icon
        if hasattr(self, "entity_description"):
            return self.entity_description.icon
        if self._attr_device_class == CoverDeviceClass.AWNING:
            if self.is_closed:
                return "mdi:storefront-outline"
            return "mdi:storefront"
        return None


    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of the shade."""
        if self._flip_position is True:
            if self._attr_device_class == CoverDeviceClass.AWNING:
                return 100 - self._position
            return self._position
        if self._attr_device_class == CoverDeviceClass.AWNING:
            return self._position
        return 100 - self._position

    @property
    def current_cover_tilt_position(self) -> int | None:
        """Return current position of cover tilt. 0 is closed, 100 is open."""
        if not self._has_tilt:
            return None
        if self._flip_position is True:
            return self._tilt_position
        return 100 - self._tilt_position

    @property
    def is_opening(self) -> bool:
        """Return true if cover is opening."""
        if self._tilt_type == 3:
            if self._tilt_direction == 0:
                return False
            elif self._tilt_direction == 1 and self._tilt_position < 50:
                return True
            elif self._tilt_direction == 1 and self._tilt_position >= 50:
                return False
            elif self._tilt_direction == -1 and self._tilt_position < 50:
                return False
            elif self._tilt_direction == -1 and self._tilt_position >= 50:
                return True


        if self._attr_device_class == CoverDeviceClass.AWNING:
            return self._direction == 1
        return self._direction == -1 or self._tilt_direction == -1

    @property
    def is_closing(self) -> bool:
        """Return true if cover is closing."""
        if self._tilt_type == 3:
            if self._tilt_direction == 0:
                return False
            elif self._tilt_direction == 1 and self._tilt_position < 50:
                return False
            elif self._tilt_direction == 1 and self._tilt_position >= 50:
                return True
            elif self._tilt_direction == -1 and self._tilt_position < 50:
                return True
            elif self._tilt_direction == -1 and self._tilt_position >= 50:
                return False


        if self._attr_device_class == CoverDeviceClass.AWNING:
            return self._direction == -1
        return self._direction == 1 or self._tilt_direction == 1

    @property
    def is_closed(self) -> bool:
        """Return true if cover is closed."""
        if self._tilt_type == 3:
            return self._tilt_position == 100 or self._tilt_position == 0



        if self._flip_position is True:
            if self._attr_device_class == CoverDeviceClass.AWNING:
                return self._position == 100
            return self._position == 0
        if self._attr_device_class == CoverDeviceClass.AWNING:
            return self._position == 0
        return (self._position == 100 or not self._has_lift) and (self._tilt_position == 100 or not self._has_tilt)

    @property
    def is_open(self) -> bool:
        """Return true if cover is closed."""
        if self._tilt_type == 3:
            return self._tilt_position < 100 and self._tilt_position > 0

        if self._flip_position is True:
            if self._attr_device_class == CoverDeviceClass.AWNING:
                return self._position == 0
            return self._position == 100
        if self._attr_device_class == CoverDeviceClass.AWNING:
            return self._position == 100
        return (self._position == 0  or not self._has_lift) and (self._tilt_position == 0 or not self._has_tilt)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""
        return self._state_attributes

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Set the tilt postion"""
        if self._flip_position is True:
            await self._controller.api.position_tilt(
                self._shade_id, int(kwargs[ATTR_TILT_POSITION])
            )
        else:
            await self._controller.api.position_tilt(
                self._shade_id, 100 - int(kwargs[ATTR_TILT_POSITION])
            )
    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the tilt position"""
        await self._controller.api.tilt_open(self._shade_id)

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the tilt position"""
        await self._controller.api.tilt_close(self._shade_id)

    async def async_stop_cover_tilt(self, **kwargs: Any) -> None:
        """Stop tilting a tilt only shade"""
        await self._controller.api.stop_shade(self._shade_id)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set the cover position."""
        if self._flip_position is True:
            if self._attr_device_class == CoverDeviceClass.AWNING:
                await self._controller.api.position_shade(
                    self._shade_id, 100 - int(kwargs[ATTR_POSITION])
                )
            else:
                await self._controller.api.position_shade(
                    self._shade_id, int(kwargs[ATTR_POSITION])
                )
        else:
            if self._attr_device_class == CoverDeviceClass.AWNING:
                await self._controller.api.position_shade(
                    self._shade_id, int(kwargs[ATTR_POSITION])
                )
            else:
                await self._controller.api.position_shade(
                    self._shade_id, 100 - int(kwargs[ATTR_POSITION])
                )

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        # print(f"Opening Cover id#{self._shade_id}")
        # This is ridiculous in that we need to invert these
        # if the type is an awning.
        if self._attr_device_class == CoverDeviceClass.AWNING:
            await self._controller.api.close_shade(self._shade_id)
        else:
            await self._controller.api.open_shade(self._shade_id)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        # print(f"Closing Cover id#{self._shade_id}")
        if self._attr_device_class == CoverDeviceClass.AWNING:
            await self._controller.api.open_shade(self._shade_id)
        else:
            await self._controller.api.close_shade(self._shade_id)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Hold cover."""
        # print(f"Stopping Cover id#{self._shade_id}")
        await self._controller.api.stop_shade(self._shade_id)

    async def async_set_current_position(self, **kwargs: Any) -> None:
        """Sets the current position for the device without moving it"""
        if self._flip_position is True:
            if self._attr_device_class == CoverDeviceClass.AWNING:
                await self._controller.api.set_current_position(
                    self._shade_id, 100 - int(kwargs[ATTR_POSITION])
                )
            else:
                await self._controller.api.set_current_position(
                    self._shade_id, int(kwargs[ATTR_POSITION])
                )
        else:
            if self._attr_device_class == CoverDeviceClass.AWNING:
                await self._controller.api.set_current_position(
                    self._shade_id, int(kwargs[ATTR_POSITION])
                )
            else:
                await self._controller.api.set_current_position(
                    self._shade_id, 100 - int(kwargs[ATTR_POSITION])
                )

    async def async_set_current_tilt_position(self, **kwargs: Any) -> None:
        """Sets the current position for the device without moving it"""
        await self._controller.api.set_current_tilt_position(self._shade_id, int(kwargs[ATTR_TILT_POSITION]))

    async def async_set_sunny(self, **kwargs:Any) -> None:
        """Sets the sensor value for the device by sending the appropriate frames"""
        await self._controller.api.set_sunny(self._shade_id, bool(kwargs[ATTR_SUNNY]))

    async def async_set_windy(self, **kwargs:Any) -> None:
        """Sets the sensor value for the device by sending the appropriate frames"""
        await self._controller.api.set_windy(self._shade_id, bool(kwargs[ATTR_WINDY]))
