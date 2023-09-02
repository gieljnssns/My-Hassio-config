"""Support for AdGuard Home sensors."""
import logging
from datetime import timedelta

from . import adguardhome

# from adguardhome import AdGuardHomeConnectionError

from . import AdGuardHomeDeviceEntity
from .const import (
    DATA_ADGUARD_CLIENT,
    DATA_ADGUARD_VERION,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, TIME_MILLISECONDS
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.typing import HomeAssistantType

SCAN_INTERVAL = timedelta(seconds=30)
PARALLEL_UPDATES = 4

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up AdGuard Home sensor based on a config entry."""
    adguard = hass.data[DOMAIN][DATA_ADGUARD_CLIENT]

    try:
        version = await adguard.version()
    except adguardhome.AdGuardHomeConnectionError as exception:
        raise PlatformNotReady from exception

    hass.data[DOMAIN][DATA_ADGUARD_VERION] = version

    sensors = [
        AdGuardHomeDNSQueriesSensor(adguard),
        AdGuardHomeBlockedFilteringSensor(adguard),
        AdGuardHomeBlockedClientsSensor(adguard),
        AdGuardHomePercentageBlockedSensor(adguard),
        AdGuardHomeReplacedParentalSensor(adguard),
        AdGuardHomeReplacedSafeBrowsingSensor(adguard),
        AdGuardHomeReplacedSafeSearchSensor(adguard),
        AdGuardHomeAverageProcessingTimeSensor(adguard),
        AdGuardHomeRulesCountSensor(adguard),
    ]

    async_add_entities(sensors, True)


class AdGuardHomeSensor(AdGuardHomeDeviceEntity):
    """Defines a AdGuard Home sensor."""

    def __init__(
        self,
        adguard,
        name: str,
        icon: str,
        measurement: str,
        unit_of_measurement: str,
        enabled_default: bool = True,
    ) -> None:
        """Initialize AdGuard Home sensor."""
        self._state = None
        self._unit_of_measurement = unit_of_measurement
        self.measurement = measurement

        super().__init__(adguard, name, icon, enabled_default)

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return "_".join(
            [
                DOMAIN,
                self.adguard.host,
                str(self.adguard.port),
                "sensor",
                self.measurement,
            ]
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit this state is expressed in."""
        return self._unit_of_measurement


class AdGuardHomeDNSQueriesSensor(AdGuardHomeSensor):
    """Defines a AdGuard Home DNS Queries sensor."""

    def __init__(self, adguard):
        """Initialize AdGuard Home sensor."""
        super().__init__(
            adguard, "AdGuard DNS Queries", "mdi:magnify", "dns_queries", "queries"
        )

    async def _adguard_update(self) -> None:
        """Update AdGuard Home entity."""
        self._state = await self.adguard.stats.dns_queries()


class AdGuardHomeBlockedFilteringSensor(AdGuardHomeSensor):
    """Defines a AdGuard Home blocked by filtering sensor."""

    def __init__(self, adguard):
        """Initialize AdGuard Home sensor."""
        super().__init__(
            adguard,
            "AdGuard DNS Queries Blocked",
            "mdi:magnify-close",
            "blocked_filtering",
            "queries",
            enabled_default=False,
        )

    async def _adguard_update(self) -> None:
        """Update AdGuard Home entity."""
        self._state = await self.adguard.stats.blocked_filtering()


class AdGuardHomeBlockedClientsSensor(AdGuardHomeSensor):
    """Defines a AdGuard Home blocked clients sensor."""

    def __init__(self, adguard):
        """Initialize AdGuard Home sensor."""
        super().__init__(
            adguard,
            "AdGuard Clients Blocked",
            "mdi:magnify-close",
            "blocked_clients",
            "clients",
            # update_interval=timedelta(seconds=10)
            # enabled_default=False,
        )

    async def _adguard_update(self) -> None:
        """Update AdGuard Home entity."""
        clients = await self.adguard.client.disallowed_clients()
        self._state = len(clients)
        # self._state = len(self.adguard.client._disallowed_clients)

    @property
    def device_state_attributes(self):
        """Return the client state attributes."""
        client = self.adguard.client
        return {
            # "test": len(self.adguard.client._disallowed_clients),
            "disallowed_clients": client._disallowed_clients
            # "test3": client._response,
        }


class AdGuardHomePercentageBlockedSensor(AdGuardHomeSensor):
    """Defines a AdGuard Home blocked percentage sensor."""

    def __init__(self, adguard):
        """Initialize AdGuard Home sensor."""
        super().__init__(
            adguard,
            "AdGuard DNS Queries Blocked Ratio",
            "mdi:magnify-close",
            "blocked_percentage",
            PERCENTAGE,
        )

    async def _adguard_update(self) -> None:
        """Update AdGuard Home entity."""
        percentage = await self.adguard.stats.blocked_percentage()
        self._state = f"{percentage:.2f}"


class AdGuardHomeReplacedParentalSensor(AdGuardHomeSensor):
    """Defines a AdGuard Home replaced by parental control sensor."""

    def __init__(self, adguard):
        """Initialize AdGuard Home sensor."""
        super().__init__(
            adguard,
            "AdGuard Parental Control Blocked",
            "mdi:human-male-girl",
            "blocked_parental",
            "requests",
        )

    async def _adguard_update(self) -> None:
        """Update AdGuard Home entity."""
        self._state = await self.adguard.stats.replaced_parental()


class AdGuardHomeReplacedSafeBrowsingSensor(AdGuardHomeSensor):
    """Defines a AdGuard Home replaced by safe browsing sensor."""

    def __init__(self, adguard):
        """Initialize AdGuard Home sensor."""
        super().__init__(
            adguard,
            "AdGuard Safe Browsing Blocked",
            "mdi:shield-half-full",
            "blocked_safebrowsing",
            "requests",
        )

    async def _adguard_update(self) -> None:
        """Update AdGuard Home entity."""
        self._state = await self.adguard.stats.replaced_safebrowsing()


class AdGuardHomeReplacedSafeSearchSensor(AdGuardHomeSensor):
    """Defines a AdGuard Home replaced by safe search sensor."""

    def __init__(self, adguard):
        """Initialize AdGuard Home sensor."""
        super().__init__(
            adguard,
            "AdGuard Safe Searches Enforced",
            "mdi:shield-search",
            "enforced_safesearch",
            "requests",
        )

    async def _adguard_update(self) -> None:
        """Update AdGuard Home entity."""
        self._state = await self.adguard.stats.replaced_safesearch()


class AdGuardHomeAverageProcessingTimeSensor(AdGuardHomeSensor):
    """Defines a AdGuard Home average processing time sensor."""

    def __init__(self, adguard):
        """Initialize AdGuard Home sensor."""
        super().__init__(
            adguard,
            "AdGuard Average Processing Speed",
            "mdi:speedometer",
            "average_speed",
            TIME_MILLISECONDS,
        )

    async def _adguard_update(self) -> None:
        """Update AdGuard Home entity."""
        average = await self.adguard.stats.avg_processing_time()
        self._state = f"{average:.2f}"


class AdGuardHomeRulesCountSensor(AdGuardHomeSensor):
    """Defines a AdGuard Home rules count sensor."""

    def __init__(self, adguard):
        """Initialize AdGuard Home sensor."""
        super().__init__(
            adguard,
            "AdGuard Rules Count",
            "mdi:counter",
            "rules_count",
            "rules",
            enabled_default=False,
        )

    async def _adguard_update(self) -> None:
        """Update AdGuard Home entity."""
        self._state = await self.adguard.filtering.rules_count()
