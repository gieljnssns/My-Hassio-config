"""Store and fetch weather data from OpenMeteo API.

This module provides the WeatherStore class, which:
- Fetches weather data from OpenMeteo API
- Caches the data for efficient retrieval
- Handles historical data queries when needed
- Manages data updates and serialization
"""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import override

import aiohttp
import pandas as pd

from .const import log
from .datastore import DataStore


class WeatherStore(DataStore):
    """Fetches and caches weather data from OpenMeteo."""

    data: pd.DataFrame
    storage_dir: str | None

    update_lock: asyncio.Lock

    def __init__(
        self,
        key: str,
        lat: float,
        lon: float,
        storage_dir: str | None = None,
        openmeteo_api_key: str | None = None,
        openmeteo_weather_models: str | None = None,
    ) -> None:
        """Initialize the WeatherStore with location and storage settings.

        Args:
            key: Unique identifier for the weather store.
            lat: Latitude of the location.
            lon: Longitude of the location.
            storage_dir: Directory to store weather data (optional).
            openmeteo_api_key: Optional OpenMeteo API key for authenticated requests.
            openmeteo_weather_models: Optional comma-separated string of OpenMeteo weather model codes (e.g., "en_DE,fr_FR").
        """
        super().__init__(storage_dir, f"weather_{key}_v1")
        self.key = key
        self.lat = lat
        self.lon = lon
        self.openmeteo_api_key = openmeteo_api_key
        self.openmeteo_weather_models = openmeteo_weather_models
        self.update_lock = asyncio.Lock()

    @override
    def get_next_horizon_revalidation_time(self) -> datetime | None:
        return self.last_updated + timedelta(hours=6)

    async def refresh_range(self, rstart: datetime, rend: datetime) -> bool:
        """Refetches data for the given range. If successful, replace old data."""
        async with self.update_lock:
            updated = False
            if self.needs_history_query(rstart):
                host = "historical-forecast-api.open-meteo.com"
            else:
                host = "api.open-meteo.com"

            params = {
                "latitude": self.lat,
                "longitude": self.lon,
                "azimuth": 0,
                "tilt": 0,
                "start_date": rstart.date().isoformat(),
                "end_date": rend.date().isoformat(),
                "minutely_15": "temperature_2m,global_tilted_irradiance,relative_humidity_2m,precipitation,visibility,cloud_cover_low,cloud_cover_mid,cloud_cover_high,snow_depth,wind_speed_10m,diffuse_radiation,shortwave_radiation,direct_radiation",
                "timezone": "UTC",
            }

            # Add optional parameters if provided
            if self.openmeteo_api_key:
                params["apikey"] = self.openmeteo_api_key
            if self.openmeteo_weather_models:
                params["models"] = self.openmeteo_weather_models

            base_url = f"https://{host}/v1/forecast"
            url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            log.debug("%s: fetching weather data: %s", self.key, url)

            try:
                async with (
                    aiohttp.ClientSession() as session,
                    session.get(base_url, params=params) as resp,
                ):
                    data = await resp.text()
                    fc = json.loads(data)

                    df = pd.DataFrame.from_dict(fc["minutely_15"])

                    df["time"] = pd.to_datetime(df["time"], utc=True)
                    df.set_index("time", inplace=True)

                    updated = self._update_data(df) or updated
            except Exception as e:
                log.warning(
                    "%s: failed to fetch weather data: error: %s", self.key, str(e)
                )
                raise
            finally:
                if updated:
                    log.debug("%s: weather data updated", self.key)
                    self.data.sort_index(inplace=True)
                    await self.serialize()

            return updated

    async def fetch_missing_data(self, start: datetime, end: datetime) -> bool:
        """Fetch any data between the given timestamps thats missing."""
        start = start.astimezone(UTC)
        end = end.astimezone(UTC)

        updated = False

        for rstart, rend in self.gen_missing_date_ranges(start, end):
            updated = await self.refresh_range(rstart, rend) or updated

        return updated

    @override
    def gen_missing_date_ranges(
        self, start: datetime, end: datetime
    ) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
        # a random hour of the day so we can easily check if we already have that day.
        # OpenMeteo only has full day queries anyway.
        start = start.replace(hour=12, minute=0, second=0, microsecond=0)
        end = end.replace(hour=12, minute=0, second=0, microsecond=0)

        curr = start
        result = []

        rangestart = None
        while curr <= end:
            next_day = curr + timedelta(days=1)

            apiswitch = rangestart is not None and self.needs_history_query(
                rangestart
            ) != self.needs_history_query(next_day)

            if rangestart is not None and (
                next_day in self.data.index
                or next_day > end
                or apiswitch
                or (curr - rangestart).total_seconds() > 60 * 60 * 24 * 90
            ):
                # We have the next timeslot already OR its the last timeslot OR the current range exceeds 90 days (max for openmeteo) OR we need to change APIs
                result.append((pd.to_datetime(rangestart), pd.to_datetime(curr)))
                rangestart = None

            if rangestart is None and curr not in self.data.index:
                rangestart = curr

            curr = next_day
        return result

    def needs_history_query(self, dt: datetime) -> bool:
        """If query is older than 90 days, we need OpenMeteo's historical data API. We switch to historical API at 60 days to be safe."""
        cutoff = datetime.now(UTC) - timedelta(days=60)
        return dt < cutoff
