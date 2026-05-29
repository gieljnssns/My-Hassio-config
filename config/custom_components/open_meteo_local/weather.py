"""Support for Open-Meteo weather."""

from __future__ import annotations

from homeassistant.components.weather import (
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import OpenMeteoConfigEntry, OpenMeteoDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenMeteoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Open-Meteo weather entity based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities([OpenMeteoWeatherEntity(entry=entry, coordinator=coordinator)])


class OpenMeteoWeatherEntity(
    SingleCoordinatorWeatherEntity[OpenMeteoDataUpdateCoordinator]
):
    """Defines an Open-Meteo weather entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_visibility_unit = UnitOfLength.METERS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(
        self,
        *,
        entry: OpenMeteoConfigEntry,
        coordinator: OpenMeteoDataUpdateCoordinator,
    ) -> None:
        """Initialize Open-Meteo weather entity."""
        super().__init__(coordinator=coordinator)
        self._attr_unique_id = entry.entry_id

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Open-Meteo",
            name=entry.title,
        )

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        return self.coordinator.data.condition

    @property
    def native_temperature(self) -> float | None:
        """Return the platform temperature."""
        return self.coordinator.data.temperature

    @property
    def humidity(self) -> float | None:
        """Return the humidity."""
        return self.coordinator.data.humidity

    @property
    def native_dew_point(self) -> float | None:
        """Return the dew point."""
        return self.coordinator.data.dew_point

    @property
    def native_apparent_temperature(self) -> float | None:
        """Return the apparent temperature."""
        return self.coordinator.data.apparent_temperature

    @property
    def cloud_coverage(self) -> float | None:
        """Return the cloud coverage."""
        return self.coordinator.data.cloud_coverage

    @property
    def native_pressure(self) -> float | None:
        """Return the pressure."""
        return self.coordinator.data.pressure

    @property
    def native_visibility(self) -> float | None:
        """Return the visibility."""
        return self.coordinator.data.visibility

    @property
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        return self.coordinator.data.wind_speed

    @property
    def wind_bearing(self) -> float | str | None:
        """Return the wind bearing."""
        return self.coordinator.data.wind_bearing

    @property
    def native_wind_gust_speed(self) -> float | None:
        """Return the wind gust speed."""
        return self.coordinator.data.wind_gust_speed

    @property
    def uv_index(self) -> float | None:
        """Return the UV index."""
        return self.coordinator.data.uv_index

    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        return self.coordinator.data.daily_forecast or None

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast in native units."""
        return self.coordinator.data.hourly_forecast or None
