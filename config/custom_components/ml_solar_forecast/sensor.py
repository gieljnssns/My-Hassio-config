from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MLSolarForecastCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:

    coordinator: MLSolarForecastCoordinator = entry.coordinator
    # hass.data[DOMAIN][entry.entry_id]
    # coordinator is only updated if there are listeners. We have no entities for now - create dummy listener.
    entry.async_on_unload(coordinator.async_add_listener(lambda: None))
