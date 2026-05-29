"""Coordinator for the ML Solar Forecast integration.

This module provides the MLSolarForecastCoordinator class, which handles:
- Data fetching and updating for solar power forecasting
- Model training and prediction using LightGBM
- Weather data collection and processing
- Integration with Home Assistant's recorder for historical data
"""

import asyncio
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
from astral import Observer, sun
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import recorder
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

# from influxdb import InfluxDBClient
from .const import (
    CONF_APP_HOSTNAME,
    CONF_INFLUX_DB,
    CONF_INFLUX_ENTITY,
    CONF_INFLUX_HOST,
    CONF_INFLUX_PASS,
    CONF_INFLUX_PORT,
    CONF_INFLUX_USER,
    CONF_LOCATION,
    CONF_MAX_INVERTER_POWER_W,
    CONF_OPENMETEO_API_KEY,
    CONF_OPENMETEO_WEATHER_MODELS,
    CONF_PRODUCTION_ENTITY,
    CONF_TRAINING_DAYS,
    CONF_USE_INFLUX,
    DOMAIN,
    log,
)
from .lgbm import LGBM
from .weatherstore import WeatherStore


class MLSolarForecastCoordinator(DataUpdateCoordinator):
    """The coordinator for fetching updates."""

    def __init__(self, hass: HomeAssistant, config: ConfigEntry) -> None:
        """Init the coordinator."""
        super().__init__(
            hass,
            log,
            name=DOMAIN,
            config_entry=config,
            update_interval=timedelta(minutes=60),
        )

        self.hass = hass
        self.config = config
        if config.data[CONF_USE_INFLUX]:
            self.key: str = config.data[CONF_INFLUX_ENTITY]
        else:
            self.key: str = config.data[CONF_PRODUCTION_ENTITY]
        self.lat: float = config.data[CONF_LOCATION]["latitude"]
        self.lon: float = config.data[CONF_LOCATION]["longitude"]

        self.weatherstore = WeatherStore(
            self.key,
            self.lat,
            self.lon,
            hass.config.path("ml-solar-forecast"),
            config.data.get(CONF_OPENMETEO_API_KEY),
            config.data.get(CONF_OPENMETEO_WEATHER_MODELS),
        )
        self.lgbm = LGBM(
            f"ml-solar-forecast-{self.key}",
            config.data[CONF_APP_HOSTNAME],
        )
        # force retrain initially
        self.last_train_time: datetime = datetime.now(UTC) - timedelta(days=1)

        self.curr_forecast: pd.DataFrame | None = None
        self.update_lock = asyncio.Lock()

    async def get_current_forecast(self) -> pd.DataFrame | None:
        """Get the current forecast data.

        If no forecast data is currently available, update the forecast data first.
        Returns the forecast data containing energy production in watt-hours (Wh) for each time period.
        """
        if self.curr_forecast is None:
            await self._async_update_data()
        return self.curr_forecast

    async def _async_update_data(self) -> pd.DataFrame | None:
        """Update data."""
        log.debug("updating forecast for %s", self.key)

        async with self.update_lock:
            if len(self.weatherstore.data) == 0:
                await self.weatherstore.load()

            # Retrain nightly
            if (
                not await self.lgbm.is_trained()
                or self.last_train_time.date() != datetime.now(UTC).date()
            ):
                await self.retrain_model()

            # for actual forecasting, start from beginning of today
            today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            end = today + timedelta(days=14)
            fcstart = today - timedelta(days=60)

            log.debug(f"{self.key}: refreshing weather data {today} -> {end}")
            await self.weatherstore.refresh_range(today, end)
            log.debug(f"{self.key}: preparing data: {fcstart} -> {end}")
            data = await self._prepare_dataframe(fcstart, end, False)

            log.debug(f"{self.key}: computing forecast...")
            forecast = await self.lgbm.predict(data, "power")
            # re-join original data so we have elevation levels to launder data
            forecast = pd.concat([data, forecast], axis=1)
            forecast = self.data_laundry(forecast)

            self.curr_forecast = forecast[["power"]]
            log.debug(f"{self.key}: forecast update done")

        return self.curr_forecast

    async def retrain_model(self):
        """Retrain the LightGBM model with historical data.

        This method collects historical solar production data and retrains the model
        to improve future predictions. It is called nightly to incorporate new data.
        """
        end_time = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(days=self.config.data[CONF_TRAINING_DAYS])

        log.info(
            f"{self.key}: retraining forecast model {start_time} -> {end_time}. preparing data.."
        )

        data = await self._prepare_dataframe(start_time, end_time, True)
        data = data.dropna()

        log.debug(f"{self.key}: training model...")
        await self.lgbm.train(data, "power")
        log.debug(f"{self.key}: model retrain done.")
        self.last_train_time = datetime.now(UTC)

    async def _prepare_dataframe(
        self, start_time: datetime, end_time: datetime, with_power: bool
    ) -> pd.DataFrame:

        data = await self.weatherstore.get_data(start_time, end_time)
        data = data.copy()

        def prepare_sync(data: pd.DataFrame) -> pd.DataFrame:
            # Interpolate weather data to 5-minute intervals if using InfluxDB
            if self.config.data.get(CONF_USE_INFLUX, False):
                data = (
                    data.infer_objects(copy=False)
                    .resample("5min")
                    .interpolate("linear")
                )
            # Round values after interpolation according to specified decimal places
            # temperature_2m(1)  global_tilted_irradiance(1)  relative_humidity_2m(0)  precipitation(1)  visibility(0)
            # cloud_cover_low(0)  cloud_cover_mid(0)  cloud_cover_high(0)  snow_depth(1)  wind_speed_10m(1)  diffuse_radiation(0)
            # shortwave_radiation(0)  direct_radiation(0)
            rounding_config = {
                "temperature_2m": 1,
                "global_tilted_irradiance": 1,
                "relative_humidity_2m": 0,
                "precipitation": 1,
                "visibility": 0,
                "cloud_cover_low": 0,
                "cloud_cover_mid": 0,
                "cloud_cover_high": 0,
                "snow_depth": 1,
                "wind_speed_10m": 1,
                "diffuse_radiation": 0,
                "shortwave_radiation": 0,
                "direct_radiation": 0,
            }

            for col, decimals in rounding_config.items():
                if col in data.columns:
                    # Coerce to numeric in case dtype is still object after interpolation
                    data[col] = pd.to_numeric(data[col], errors="coerce")
                    if decimals == 1:
                        data[col] = data[col].round(decimals)
                    else:
                        data[col] = data[col].round(decimals).astype("Int64")

            observer = Observer(latitude=self.lat, longitude=self.lon)

            data["azimuth"] = list(data.index.map(lambda t: sun.azimuth(observer, t)))
            data["elevation"] = list(
                data.index.map(lambda t: sun.elevation(observer, t))
            )
            # Add hour as feature instead of using full timestamp
            data["hour"] = data.index.hour
            # Add cosine/sine features for daily solar cycle (helps model generalize across days)
            # 0.0 at sunset, 1.0 at noon, -1.0 at sunrise
            data["solar_phase"] = np.cos(np.pi / 12 * (data.index.hour - 6))
            # Cloud cover trend (rapid cloud movement causes big forecast errors)
            data["cloud_covers"] = 0
            if "cloud_cover_low" in data.columns:
                data["cloud_covers"] = (
                    data["cloud_cover_low"]
                    + data.get("cloud_cover_mid", 0)
                    + data.get("cloud_cover_high", 0)
                )
            # Add precipitation probability if available
            if "precipitation_probability" in data.columns:
                data["precipitation_probability"] = data[
                    "precipitation_probability"
                ].round(0)
            # Add humidity * temperature interaction (hot + humid = often clouds)
            if (
                "temperature_2m" in data.columns
                and "relative_humidity_2m" in data.columns
            ):
                data["humidheat"] = (
                    data["temperature_2m"] * 0.3 + data["relative_humidity_2m"] / 100
                )
            # Add wind direction as cosine feature (helps generalize across locations)
            # Wind direction is 0-360, convert to cosine for periodic representation
            # (directional gradient from previous hour)
            data["wind_direction_change"] = 0
            if "wind_direction_10m" in data.columns:
                data["wind_direction_change"] = (
                    data.index.shift(-1).wind_direction_10m - data["wind_direction_10m"]
                )
            # Add direct radiation to global tilted (model learns their correlation and handles missing values)
            if (
                "direct_radiation" in data.columns
                and "global_tilted_irradiance" in data.columns
            ):
                data["direct_ratio"] = np.nan_to_num(
                    data["direct_radiation"] / data["global_tilted_irradiance"], nan=0.0
                )
            # Add diffuse radiation to global tilted (cloud fraction on the panel)
            if (
                "diffuse_radiation" in data.columns
                and "global_tilted_irradiance" in data.columns
            ):
                data["diffuse_ratio"] = np.nan_to_num(
                    data["diffuse_radiation"] / data["global_tilted_irradiance"],
                    nan=0.0,
                )
            return data.dropna()

        data = await asyncio.to_thread(prepare_sync, data)

        if with_power:
            power = await self._collect_solar_history(start_time, end_time)
            data = await asyncio.to_thread(lambda: pd.concat([data, power], axis=1))
            data = self.data_laundry(data)
            data = await asyncio.to_thread(lambda: data.dropna())
        return data

    def data_laundry(self, df: pd.DataFrame):
        """Cleans up data to matchs some basic assumptions.

        - Remove negative power
        - ensure power is 0 at night
        - remove power > inverter output.
        - power is integer
        """

        df["power"] = df["power"].clip(lower=0)

        max_power = self.config.data.get(CONF_MAX_INVERTER_POWER_W)
        if max_power is not None:
            df.loc[df["power"] > max_power] = np.nan

        if "elevation" in df.columns:
            df.loc[df["elevation"] <= 0, "power"] = 0

        df["power"] = df["power"].round(0).astype("Int64")

        return df

    async def _collect_solar_history(self, start_time: datetime, end_time: datetime):
        log.info(
            f"{self.key} fetching production statistics {start_time} -> {end_time}"
        )
        if self.config.data.get(CONF_USE_INFLUX, False):
            return await self._collect_solar_history_influx(
                start_time,
                end_time,
            )

        return await self._collect_recorder_history(
            start_time,
            end_time,
        )

    async def _collect_recorder_history(
        self, start_time: datetime, end_time: datetime
    ) -> pd.DataFrame:

        entity_id = self.config.data[CONF_PRODUCTION_ENTITY]

        statistic_id = {entity_id}
        types = {"sum"}
        units = {"energy": "Wh"}

        recorder_instance = recorder.get_instance(self.hass)

        df = pd.DataFrame()

        if end_time > start_time:
            # Fetch remaining required time from hourly data and spline it
            stats = await recorder_instance.async_add_executor_job(
                statistics_during_period,
                self.hass,
                start_time,
                end_time,
                statistic_id,
                "hour",
                units,
                types,
            )
            df = pd.DataFrame()
            df["time"] = [
                pd.Timestamp(r["start"], tz=UTC, unit="s") for r in stats[entity_id]
            ]
            df["power"] = [r["sum"] for r in stats[entity_id]]
            df = df.set_index("time")
            df["power"] = df["power"].diff()

            # For now, learning only runs on hourly aggregates instead of 15 minute intervals.
            # Since for one hour, 1W=1Wh, we just interpret our learning data as "watts" instead of "watt-hours".
            # -> the model predicts watts, we just divide by 4 in the forecast if needed

            df = await asyncio.to_thread(
                lambda: df.shift(30, "min").resample("15min").interpolate("cubic")
            )

        df["power"] = df["power"].clip(lower=0).apply(lambda p: 0 if p < 15 else p)
        return df.dropna()

    async def _collect_solar_history_influx(
        self, start_time: datetime, end_time: datetime
    ) -> pd.DataFrame:
        # Use the synchronous client inside the thread

        def query():
            try:
                # Initialize client inside the thread
                client = self._init_influx_client_sync()

                sensor = self.config.data[CONF_INFLUX_ENTITY]
                entity = (
                    sensor.replace("sensor.", "")
                    if sensor.startswith("sensor.")
                    else sensor
                )

                q = f"""
                SELECT mean("value") as power
                FROM "W"
                WHERE "entity_id" = '{entity}'
                  AND time >= '{start_time.isoformat()}'
                  AND time <= '{end_time.isoformat()}'
                GROUP BY time(5m) FILL(previous)
                """

                log.debug(f"Executing InfluxDB query: {q}")
                result = client.query(q)

                rows = list(result.get_points())
                log.debug(f"Query rows: {len(rows)}")

                df = pd.DataFrame(rows)
                log.debug(f"DataFrame shape: {df.shape}")
                log.debug(f"DataFrame columns: {list(df.columns)}")

                if df.empty:
                    log.warning(
                        f"No data found for entity '{entity}' in period {start_time} to {end_time}"
                    )
                    return pd.DataFrame(columns=["power"])

                df["time"] = pd.to_datetime(df["time"], utc=True)
                df.set_index("time", inplace=True)

                log.debug(f"Final DataFrame shape: {df.shape}")
                return df[["power"]]

            except Exception as e:
                # Debug logging for configuration values
                log.debug(
                    "InfluxDB config: host=%s, port=%s, user=%s, db=%s",
                    self.config.data.get(CONF_INFLUX_HOST, "Not set"),
                    self.config.data.get(CONF_INFLUX_PORT, "Not set"),
                    self.config.data.get(CONF_INFLUX_USER, "Not set"),
                    self.config.data.get(CONF_INFLUX_DB, "Not set"),
                )
                log.error("Failed to query InfluxDB: %s", e)
                return pd.DataFrame(columns=["power"])

        df = await asyncio.to_thread(query)
        log.debug(f"Final power dataframe shape: {df.shape}")
        log.debug(f"Final power dataframe head: {df.head()}")

        df["power"] = df["power"].clip(lower=0).fillna(0).astype(int)

        return df

    def _init_influx_client_sync(self):
        """Initialize InfluxDB client connection synchronously."""
        try:
            from influxdb import InfluxDBClient
        except ImportError:
            self.logger.error(
                "InfluxDB client not installed. Install with: pip install influxdb"
            )
            return None

        try:
            client = InfluxDBClient(
                host=self.config.data[CONF_INFLUX_HOST],
                port=int(self.config.data[CONF_INFLUX_PORT]),
                username=self.config.data[CONF_INFLUX_USER],
                password=self.config.data[CONF_INFLUX_PASS],
                database=self.config.data[CONF_INFLUX_DB],
            )
            # Test connection
            client.ping()
            self.logger.debug(
                f"Successfully connected to InfluxDB at {self.config.data[CONF_INFLUX_HOST]}:{int(self.config.data[CONF_INFLUX_PORT])}"
            )

            return client
        except Exception as e:
            self.logger.error(f"Failed to connect to InfluxDB: {e}")
            return None

    async def _init_influx_client(self):
        """Initialize InfluxDB client connection."""
        try:
            from influxdb import InfluxDBClient
        except ImportError:
            self.logger.error(
                "InfluxDB client not installed. Install with: pip install influxdb"
            )
            return None

        try:
            client = InfluxDBClient(
                host=self.config.data[CONF_INFLUX_HOST],
                port=self.config.data[CONF_INFLUX_PORT],
                username=self.config.data[CONF_INFLUX_USER],
                password=self.config.data[CONF_INFLUX_PASS],
                database=self.config.data[CONF_INFLUX_DB],
            )
            # Test connection
            await self.hass.async_add_executor_job(client.ping)
            self.logger.debug(
                f"Successfully connected to InfluxDB at {self.config.data[CONF_INFLUX_HOST]}:{self.config.data[CONF_INFLUX_PORT]}"
            )

            return client
        except Exception as e:
            self.logger.error(f"Failed to connect to InfluxDB: {e}")
            return None
