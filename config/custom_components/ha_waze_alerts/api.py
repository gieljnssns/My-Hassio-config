"""Sample API Client."""

from __future__ import annotations

import aiohttp

from .const import BASE_URL
from .helper import calculate_bounding_box


async def fetch_alerts(lat: float, lon: float, radius: float):
    """
    Fetch alerts from Waze Live Map API based on the given coordinates and radius.

    :param latitude: Latitude of the center point.
    :param longitude: Longitude of the center point.
    :param radius_km: Radius in kilometers to search for alerts.
    :param alert_types: Optional list of alert types to filter.
    :return: A WazeResponse object containing a list of alerts.
    """
    env = "row"
    types = "alerts"
    # Calculate bounding box
    top, bottom, left, right = calculate_bounding_box(lat, lon, radius)

    # Build request parameters
    url = (
        f"{BASE_URL}?top={top}&bottom={bottom}&left={left}&right={right}"
        f"&env={env}&types={types}"
    )
    async with aiohttp.ClientSession() as session, session.get(url) as response:
        if response.status != 200:
            msg = f"Failed to fetch alerts: {response.status}"
            raise WazeResponseError(msg)
        return await response.json()


class WazeClientError(Exception):
    """Algemene fout voor de Waze-client."""


class WazeResponseError(WazeClientError):
    """Fout bij verwerken van de API-response."""
