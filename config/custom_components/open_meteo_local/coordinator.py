"""DataUpdateCoordinator for the Open-Meteo integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse

from homeassistant.components.weather import (
    ATTR_FORECAST_CLOUD_COVERAGE as CLOUD_COVERAGE,
    ATTR_FORECAST_CONDITION as CONDITION,
    ATTR_FORECAST_HUMIDITY as HUMIDITY,
    ATTR_FORECAST_NATIVE_APPARENT_TEMP as NATIVE_APPARENT_TEMP,
    ATTR_FORECAST_NATIVE_DEW_POINT as NATIVE_DEW_POINT,
    ATTR_FORECAST_NATIVE_PRECIPITATION as NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_PRESSURE as NATIVE_PRESSURE,
    ATTR_FORECAST_NATIVE_TEMP as NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW as NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_GUST_SPEED as NATIVE_WIND_GUST_SPEED,
    ATTR_FORECAST_NATIVE_WIND_SPEED as NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY as PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_UV_INDEX as UV_INDEX,
    ATTR_FORECAST_WIND_BEARING as WIND_BEARING,
    Forecast,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, CONF_ZONE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    FLATBUFFERS_ERROR_MARKER,
    FLATBUFFERS_PREFIX,
    LOGGER,
    OPEN_METEO_URL,
    SCAN_INTERVAL,
    resolve_condition,
)

type OpenMeteoConfigEntry = ConfigEntry[OpenMeteoDataUpdateCoordinator]

# (api_field_name, data_key, value_converter)
# data_key=None: condition computation only (weather_code / is_day)
# _CURRENT_MAP → OpenMeteoData field names; _DAILY/_HOURLY_MAP → HA forecast attribute keys
_CURRENT_MAP: tuple[tuple[str, str | None, type], ...] = (
    ("weather_code", None, int),
    ("is_day", None, bool),
    ("cloud_cover", "cloud_coverage", int),
    ("relative_humidity_2m", "humidity", float),
    ("apparent_temperature", "apparent_temperature", float),
    ("dew_point_2m", "dew_point", float),
    ("pressure_msl", "pressure", float),
    ("temperature_2m", "temperature", float),
    ("visibility", "visibility", float),
    ("wind_gusts_10m", "wind_gust_speed", float),
    ("wind_speed_10m", "wind_speed", float),
    ("uv_index", "uv_index", float),
    ("wind_direction_10m", "wind_bearing", float),
)

# (api_field_name, forecast_ha_key, value_converter)
# ha_key=None: condition computation only (weather_code / is_day)
_DAILY_MAP: tuple[tuple[str, str | None, type], ...] = (
    ("weather_code", None, int),
    ("cloud_cover_mean", CLOUD_COVERAGE, int),
    ("relative_humidity_2m_mean", HUMIDITY, float),
    ("apparent_temperature_mean", NATIVE_APPARENT_TEMP, float),
    ("dew_point_2m_mean", NATIVE_DEW_POINT, float),
    ("precipitation_sum", NATIVE_PRECIPITATION, float),
    ("pressure_msl_mean", NATIVE_PRESSURE, float),
    ("temperature_2m_max", NATIVE_TEMP, float),
    ("temperature_2m_min", NATIVE_TEMP_LOW, float),
    ("wind_gusts_10m_max", NATIVE_WIND_GUST_SPEED, float),
    ("wind_speed_10m_max", NATIVE_WIND_SPEED, float),
    ("precipitation_probability_max", PRECIPITATION_PROBABILITY, int),
    ("uv_index_max", UV_INDEX, float),
    ("wind_direction_10m_dominant", WIND_BEARING, float),
)

_HOURLY_MAP: tuple[tuple[str, str | None, type], ...] = (
    ("weather_code", None, int),
    ("is_day", None, bool),
    ("cloud_cover", CLOUD_COVERAGE, int),
    ("relative_humidity_2m", HUMIDITY, float),
    ("apparent_temperature", NATIVE_APPARENT_TEMP, float),
    ("dew_point_2m", NATIVE_DEW_POINT, float),
    ("precipitation", NATIVE_PRECIPITATION, float),
    ("pressure_msl", NATIVE_PRESSURE, float),
    ("temperature_2m", NATIVE_TEMP, float),
    ("wind_gusts_10m", NATIVE_WIND_GUST_SPEED, float),
    ("wind_speed_10m", NATIVE_WIND_SPEED, float),
    ("precipitation_probability", PRECIPITATION_PROBABILITY, int),
    ("uv_index", UV_INDEX, float),
    ("wind_direction_10m", WIND_BEARING, float),
)


@dataclass
class OpenMeteoData:
    """Dataclass for Open-Meteo weather data."""

    condition: str | None
    temperature: float | None
    humidity: float | None
    dew_point: float | None
    apparent_temperature: float | None
    cloud_coverage: int | None
    pressure: float | None
    visibility: float | None
    wind_speed: float | None
    wind_bearing: float | None
    wind_gust_speed: float | None
    uv_index: float | None
    daily_forecast: list[Forecast] = field(default_factory=list)
    hourly_forecast: list[Forecast] = field(default_factory=list)


class OpenMeteoDataUpdateCoordinator(DataUpdateCoordinator[OpenMeteoData]):
    """A Open-Meteo Data Update Coordinator."""

    config_entry: OpenMeteoConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: OpenMeteoConfigEntry) -> None:
        """Initialize the Open-Meteo coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{config_entry.data[CONF_ZONE]}",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> OpenMeteoData:
        """Fetch data from Open-Meteo."""
        if (zone := self.hass.states.get(self.config_entry.data[CONF_ZONE])) is None:
            raise UpdateFailed(f"Zone '{self.config_entry.data[CONF_ZONE]}' not found")

        params = {
            "latitude": zone.attributes[ATTR_LATITUDE],
            "longitude": zone.attributes[ATTR_LONGITUDE],
            "current": ",".join(f for f, *_ in _CURRENT_MAP),
            "daily": ",".join(f for f, *_ in _DAILY_MAP),
            "hourly": ",".join(f for f, *_ in _HOURLY_MAP),
            # Required by: https://github.com/open-meteo/open-meteo/issues/699
            "forecast_hours": "168",
            "format": "flatbuffers",
            "precipitation_unit": "mm",
            "temperature_unit": "celsius",
            "timezone": "auto",
            "wind_speed_unit": "kmh",
        }

        try:
            session = async_get_clientsession(self.hass)
            async with session.get(OPEN_METEO_URL, params=params) as http_response:
                http_response.raise_for_status()
                data = await http_response.read()
        except Exception as err:
            raise UpdateFailed("Open-Meteo API communication error") from err

        # Parse the first length-prefixed FlatBuffers frame.
        # Additional frames are ignored with a warning.
        total = len(data)
        if total < FLATBUFFERS_PREFIX:
            raise UpdateFailed("Malformed response frame header")

        length = int.from_bytes(data[:FLATBUFFERS_PREFIX], byteorder="little")
        if length == FLATBUFFERS_ERROR_MARKER:
            raise UpdateFailed(data.decode())
        if length <= 0:
            raise UpdateFailed("Malformed response frame length")

        frame_end = FLATBUFFERS_PREFIX + length
        if frame_end > total:
            raise UpdateFailed("Malformed response frame length")

        response = WeatherApiResponse.GetRootAs(data, FLATBUFFERS_PREFIX)

        if frame_end < total:
            LOGGER.warning(
                "Received %s extra bytes from Open-Meteo for %s; using first frame only",
                total - frame_end,
                self.config_entry.data[CONF_ZONE],
            )

        tz = timezone(timedelta(seconds=response.UtcOffsetSeconds()))

        # Current weather
        condition: str | None = None
        current_fields: dict[str, float | None] = {
            data_key: None for _, data_key, _ in _CURRENT_MAP if data_key is not None
        }
        if (current := response.Current()) is not None:
            condition = resolve_condition(
                int(current.Variables(0).Value()),
                bool(current.Variables(1).Value()),
            )
            for j, (_, data_key, conv) in enumerate(_CURRENT_MAP):
                if data_key is not None:
                    current_fields[data_key] = conv(current.Variables(j).Value())

        # Daily forecast
        daily_forecast: list[Forecast] = []
        if (daily := response.Daily()) is not None:
            daily_forecast = [
                Forecast(datetime=datetime.fromtimestamp(ts, tz=tz).isoformat())
                for ts in range(daily.Time(), daily.TimeEnd(), daily.Interval())
            ]
            wc = daily.Variables(0)
            for i, entry in enumerate(daily_forecast):
                entry[CONDITION] = resolve_condition(int(wc.Values(i)))
            for j, (_, ha_key, conv) in enumerate(_DAILY_MAP):
                if ha_key is not None:
                    var = daily.Variables(j)
                    for i, entry in enumerate(daily_forecast):
                        entry[ha_key] = conv(var.Values(i))

        # Hourly forecast
        hourly_forecast: list[Forecast] = []
        if (hourly := response.Hourly()) is not None:
            hourly_forecast = [
                Forecast(datetime=datetime.fromtimestamp(ts, tz=tz).isoformat())
                for ts in range(hourly.Time(), hourly.TimeEnd(), hourly.Interval())
            ]
            wc_h, is_day_h = hourly.Variables(0), hourly.Variables(1)
            for i, entry in enumerate(hourly_forecast):
                entry[CONDITION] = resolve_condition(
                    int(wc_h.Values(i)), bool(is_day_h.Values(i))
                )
            for j, (_, ha_key, conv) in enumerate(_HOURLY_MAP):
                if ha_key is not None:
                    var = hourly.Variables(j)
                    for i, entry in enumerate(hourly_forecast):
                        entry[ha_key] = conv(var.Values(i))

        return OpenMeteoData(
            condition=condition,
            **current_fields,
            daily_forecast=daily_forecast,
            hourly_forecast=hourly_forecast,
        )
