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


@dataclass
class OpenMeteoData:
    """Dataclass for Open-Meteo weather data."""

    condition: str | None
    temperature: float | None
    humidity: float | None
    dew_point: float | None
    apparent_temperature: float | None
    cloud_coverage: float | None
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
            "current": "weather_code,is_day,temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,cloud_cover,pressure_msl,visibility,wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_direction_10m_dominant,wind_gusts_10m_max,uv_index_max",
            "hourly": "weather_code,is_day,temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation,precipitation_probability,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index",
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

        # Parse length-prefixed FlatBuffers frames
        responses: list[WeatherApiResponse] = []
        total = len(data)
        pos = 0
        while pos < total:
            length = int.from_bytes(
                data[pos : pos + FLATBUFFERS_PREFIX], byteorder="little"
            )
            if length == FLATBUFFERS_ERROR_MARKER:
                raise UpdateFailed(data[pos:total].decode())
            responses.append(
                WeatherApiResponse.GetRootAs(data, pos + FLATBUFFERS_PREFIX)
            )
            pos += length + FLATBUFFERS_PREFIX

        response = responses[0]
        tz = timezone(timedelta(seconds=response.UtcOffsetSeconds()))

        # Current weather — variable order matches "current" list above
        condition: str | None = None
        temperature: float | None = None
        humidity: float | None = None
        dew_point: float | None = None
        apparent_temperature: float | None = None
        cloud_coverage: float | None = None
        pressure: float | None = None
        visibility: float | None = None
        wind_speed: float | None = None
        wind_bearing: float | None = None
        wind_gust_speed: float | None = None
        uv_index: float | None = None
        if (current := response.Current()) is not None:
            condition = resolve_condition(
                int(current.Variables(0).Value()),
                bool(current.Variables(1).Value()),
            )
            temperature = current.Variables(2).Value()
            humidity = current.Variables(3).Value()
            dew_point = current.Variables(4).Value()
            apparent_temperature = current.Variables(5).Value()
            cloud_coverage = current.Variables(6).Value()
            pressure = current.Variables(7).Value()
            visibility = current.Variables(8).Value()
            wind_speed = current.Variables(9).Value()
            wind_bearing = current.Variables(10).Value()
            wind_gust_speed = current.Variables(11).Value()
            uv_index = current.Variables(12).Value()

        # Daily forecast — variable order matches "daily" list above
        daily_forecast: list[Forecast] = []
        if (daily := response.Daily()) is not None:
            weather_code = daily.Variables(0)
            temp_max = daily.Variables(1)
            temp_min = daily.Variables(2)
            apparent_temp_max = daily.Variables(3)
            precip_sum = daily.Variables(4)
            precip_prob_max = daily.Variables(5)
            wind_spd = daily.Variables(6)
            wind_dir = daily.Variables(7)
            wind_gust_max = daily.Variables(8)
            uv_index_max = daily.Variables(9)
            for i, ts in enumerate(
                range(daily.Time(), daily.TimeEnd(), daily.Interval())
            ):
                _dt = datetime.fromtimestamp(ts, tz=tz)
                entry: Forecast = Forecast(datetime=_dt.isoformat())
                entry[CONDITION] = resolve_condition(int(weather_code.Values(i)))
                entry[NATIVE_TEMP] = temp_max.Values(i)
                entry[NATIVE_TEMP_LOW] = temp_min.Values(i)
                entry[NATIVE_APPARENT_TEMP] = apparent_temp_max.Values(i)
                entry[NATIVE_PRECIPITATION] = precip_sum.Values(i)
                entry[PRECIPITATION_PROBABILITY] = int(precip_prob_max.Values(i))
                entry[NATIVE_WIND_SPEED] = wind_spd.Values(i)
                entry[WIND_BEARING] = wind_dir.Values(i)
                entry[NATIVE_WIND_GUST_SPEED] = wind_gust_max.Values(i)
                entry[UV_INDEX] = uv_index_max.Values(i)
                daily_forecast.append(entry)

        # Hourly forecast — variable order matches "hourly" list above
        hourly_forecast: list[Forecast] = []
        if (hourly := response.Hourly()) is not None:
            weather_code_h = hourly.Variables(0)
            is_day_h = hourly.Variables(1)
            temperature_2m = hourly.Variables(2)
            humidity_h = hourly.Variables(3)
            dew_point_h = hourly.Variables(4)
            apparent_temp_h = hourly.Variables(5)
            precipitation = hourly.Variables(6)
            precip_prob_h = hourly.Variables(7)
            cloud_cover_h = hourly.Variables(8)
            pressure_h = hourly.Variables(9)
            wind_spd_h = hourly.Variables(10)
            wind_dir_h = hourly.Variables(11)
            wind_gust_h = hourly.Variables(12)
            uv_index_h = hourly.Variables(13)
            for i, ts in enumerate(
                range(hourly.Time(), hourly.TimeEnd(), hourly.Interval())
            ):
                _dt = datetime.fromtimestamp(ts, tz=tz)
                entry = Forecast(datetime=_dt.isoformat())
                entry[CONDITION] = resolve_condition(
                    int(weather_code_h.Values(i)),
                    bool(is_day_h.Values(i)),
                )
                entry[NATIVE_TEMP] = temperature_2m.Values(i)
                entry[HUMIDITY] = humidity_h.Values(i)
                entry[NATIVE_DEW_POINT] = dew_point_h.Values(i)
                entry[NATIVE_APPARENT_TEMP] = apparent_temp_h.Values(i)
                entry[NATIVE_PRECIPITATION] = precipitation.Values(i)
                entry[PRECIPITATION_PROBABILITY] = int(precip_prob_h.Values(i))
                entry[CLOUD_COVERAGE] = int(cloud_cover_h.Values(i))
                entry[NATIVE_PRESSURE] = pressure_h.Values(i)
                entry[NATIVE_WIND_SPEED] = wind_spd_h.Values(i)
                entry[WIND_BEARING] = wind_dir_h.Values(i)
                entry[NATIVE_WIND_GUST_SPEED] = wind_gust_h.Values(i)
                entry[UV_INDEX] = uv_index_h.Values(i)
                hourly_forecast.append(entry)

        return OpenMeteoData(
            condition=condition,
            temperature=temperature,
            humidity=humidity,
            dew_point=dew_point,
            apparent_temperature=apparent_temperature,
            cloud_coverage=cloud_coverage,
            pressure=pressure,
            visibility=visibility,
            wind_speed=wind_speed,
            wind_bearing=wind_bearing,
            wind_gust_speed=wind_gust_speed,
            uv_index=uv_index,
            daily_forecast=daily_forecast,
            hourly_forecast=hourly_forecast,
        )
