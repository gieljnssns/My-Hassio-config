"""Energy platform for ML Solar Forecast integration."""

from __future__ import annotations

import pandas as pd
from homeassistant.core import HomeAssistant

from .const import DOMAIN, log
from .coordinator import MLSolarForecastCoordinator


async def async_get_solar_forecast(
    hass: HomeAssistant, config_entry_id: str
) -> dict[str, dict[str, float | int]] | None:
    """Get solar forecast for a config entry ID.

    This function provides solar forecast data in the format expected by
    Home Assistant's energy dashboard. Power values are converted to energy
    by averaging adjacent 15-minute slots and dividing by 4.

    Args:
        hass: Home Assistant instance.
        config_entry_id: Configuration entry ID.

    Returns:
        Dictionary with 'wh_hours' key containing ISO timestamp to Wh mapping,
        or None if no data available or error occurred.
    """
    # Get coordinator
    coordinator = hass.data[DOMAIN].get(config_entry_id)
    if coordinator is None:
        log.warning("Config entry %s not found in %s", config_entry_id, DOMAIN)
        return None

    if not isinstance(coordinator, MLSolarForecastCoordinator):
        log.error(
            "Invalid coordinator type for %s: %s",
            config_entry_id,
            type(coordinator).__name__,
        )
        return None

    try:
        # Get prediction data
        prediction = await coordinator.get_current_forecast()

        if prediction is None or prediction.empty:
            log.warning("No forecast data available for %s", config_entry_id)
            return None

        # Weather data is at the start of each 15-minute slot
        # Average with next slot to get mean power over 15 minutes
        power = (prediction["power"] + prediction["power"].shift(-1)) / 2

        # Convert power (W) to energy (Wh) for 15-minute intervals
        # 15 minutes = 0.25 hours, so divide by 4
        energy = power / 4

        # Convert to dictionary, filtering out NaN values
        result = {
            key.isoformat(): value
            for key, value in energy.to_dict().items()
            if pd.notna(value)
        }

        log.debug(
            "Returning solar forecast for %s with %d data points",
            config_entry_id,
            len(result),
        )

        return {"wh_hours": result}

    except KeyError as e:
        log.error("Missing expected column in forecast data: %s", e)
        return None
    except Exception as e:
        log.error(
            "Error getting solar forecast for %s: %s",
            config_entry_id,
            e,
            exc_info=True,
        )
        return None
