"""The HA-ML Solar Forecast integration."""

from datetime import UTC, datetime, timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    SERVICE_DATA_END,
    SERVICE_DATA_START,
    SERVICE_NAME_GET_FORECAST,
    log,
)
from .coordinator import MLSolarForecastCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_SCHEMA_GET_FORECAST = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Optional(SERVICE_DATA_START): cv.datetime,
        vol.Optional(SERVICE_DATA_END): cv.datetime,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up configured integration."""

    async def async_get_forecast(call: ServiceCall) -> dict[str, float]:
        """Handle get_forecast service call.
        Returns:
            Dictionary mapping ISO timestamp strings to power values in local time.
        """
        entry_id = call.data["entry_id"]
        coordinator = hass.data[DOMAIN].get(entry_id)
        if coordinator is None:
            log.error("entry_id %s is not valid", entry_id)
            raise ValueError(f"Invalid entry_id: {entry_id}")

        try:
            log.debug("getting forecast for entry_id %s", entry_id)
            fc = await coordinator.get_current_forecast()
            if fc is None or fc.empty:
                log.warning("No forecast data available for entry_id %s", entry_id)
                return {}

            local_tz = dt_util.get_time_zone(hass.config.time_zone)

            # Parse start/end times with defaults in local time
            start = call.data.get(SERVICE_DATA_START)
            end = call.data.get(SERVICE_DATA_END)

            if not start:
                start = datetime.now(local_tz).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            if not end:
                end = datetime.now(local_tz).replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=14)

            # Intern blijft alles UTC voor de filtering
            start_utc = start.astimezone(UTC)
            end_utc = end.astimezone(UTC)

            # Filter forecast data
            data = fc.loc[start_utc:end_utc]

            def convert_and_serialize(df: pd.DataFrame) -> dict:
                local_df = df.copy()
                local_df.index = local_df.index.tz_convert(local_tz)
                return {
                    k.isoformat(): v for k, v in local_df["power"].to_dict().items()
                }

            return await hass.async_add_executor_job(convert_and_serialize, data)
            # # Converteer index naar locale tijd voor de output
            # data = data.copy()
            # data.index = data.index.tz_convert(local_tz)

            # return {k.isoformat(): v for k, v in data["power"].to_dict().items()}

        except Exception as e:
            log.error("Error getting forecast for entry_id %s: %s", entry_id, e)
            raise

    # async def async_get_forecast(call: ServiceCall) -> dict[str, float]:
    #     """Handle get_forecast service call.

    #     Returns:
    #         Dictionary mapping ISO timestamp strings to power values in Watts.

    #     Raises:
    #         ValueError: If entry_id is invalid or no forecast data available.
    #     """
    #     entry_id = call.data["entry_id"]
    #     coordinator = hass.data[DOMAIN].get(entry_id)

    #     if coordinator is None:
    #         log.error("entry_id %s is not valid", entry_id)
    #         raise ValueError(f"Invalid entry_id: {entry_id}")

    #     try:
    #         log.debug("getting forecast for entry_id %s", entry_id)
    #         fc = await coordinator.get_current_forecast()

    #         if fc is None or fc.empty:
    #             log.warning("No forecast data available for entry_id %s", entry_id)
    #             return {}

    #         # Parse start/end times with defaults
    #         start = call.data.get(SERVICE_DATA_START)
    #         end = call.data.get(SERVICE_DATA_END)

    #         if not start:
    #             start = datetime.now(UTC).replace(
    #                 hour=0, minute=0, second=0, microsecond=0
    #             )
    #         if not end:
    #             end = datetime.now(UTC).replace(
    #                 hour=0, minute=0, second=0, microsecond=0
    #             ) + timedelta(days=14)

    #         start = start.astimezone(UTC)
    #         end = end.astimezone(UTC)

    #         # Filter forecast data for requested range
    #         data = fc.loc[start:end]

    #         return {k.isoformat(): v for k, v in data["power"].to_dict().items()}

    #     except Exception as e:
    #         log.error("Error getting forecast for entry_id %s: %s", entry_id, e)
    #         raise

    hass.services.async_register(
        DOMAIN,
        SERVICE_NAME_GET_FORECAST,
        async_get_forecast,
        schema=SERVICE_SCHEMA_GET_FORECAST,
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA-ML Solar Forecast from a config entry."""
    coordinator = MLSolarForecastCoordinator(hass, entry)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as e:
        log.error(
            "Failed to initialize coordinator for entry %s: %s", entry.entry_id, e
        )
        return False

    # Store coordinator
    entry.coordinator = coordinator
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])

    # Register update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform.SENSOR]
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)
