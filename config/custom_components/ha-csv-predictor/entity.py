"""HaCsvPredictorEntity class."""
from __future__ import annotations

# from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, Entity

# from .const import ATTRIBUTION
from .const import (
    # CONF_CSV_PATH,
    # CONF_DEPENDENT_VARIABLE,
    # CONF_INDEPENDENT_VARIABLES,
    DOMAIN,
)

# from .const import NAME
# from .const import VERSION


class HaCsvPredictorEntity(Entity):
    """Defines a base HA CSV Predictor entity."""

    def __init__(self, entry: ConfigEntry):
        """Initialize the AdGuard Home entity."""
        # print("HaCsvPredictorEntity(Entity) init")
        self._entry = entry

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self._entry.entry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this AdGuard Home instance."""

        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={
                (  # type: ignore[arg-type]
                    DOMAIN,
                    self._entry.title,
                    # self._entry.data[CONF_CSV_PATH],
                    # self._entry.data[CONF_INDEPENDENT_VARIABLES],
                    # self._entry.data[CONF_DEPENDENT_VARIABLE],
                )
            },
            manufacturer="Test",
            name="HA CSV Predictor",
            # sw_version=self.hass.data[DOMAIN][self._entry.entry_id].get(
            #     DATA_ADGUARD_VERSION
            # ),
            # configuration_url=config_url,
        )
