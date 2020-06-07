"""Support for Tahoma scenes."""
import logging

from homeassistant.components.scene import Scene

from . import DOMAIN as TAHOMA_DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Tahoma scenes."""
    if discovery_info is None:
        return
    controller = hass.data[TAHOMA_DOMAIN]["controller"]
    scenes = []
    for scene in hass.data[TAHOMA_DOMAIN]["scenes"]:
        scenes.append(TahomaScene(scene, controller))
    add_entities(scenes, True)


class TahomaScene(Scene):
    """Representation of a Tahoma scene entity."""

    def __init__(self, tahoma_scene, controller):
        """Initialize the scene."""
        self.tahoma_scene = tahoma_scene
        self.controller = controller
        self._name = self.tahoma_scene.name

    def activate(self):
        """Activate the scene."""
        self.controller.launch_action_group(self.tahoma_scene.oid)

    @property
    def name(self):
        """Return the name of the scene."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the state attributes of the scene."""
        return {"tahoma_scene_oid": self.tahoma_scene.oid}
