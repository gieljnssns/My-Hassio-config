"""Sample API Client."""

from __future__ import annotations

import aiohttp
import logging
import random
from homeassistant.const import __version__ as HA_VERSION
from typing import Final
from .const import BASE_URL
from .helper import calculate_bounding_box

_LOGGER = logging.getLogger(__name__)


async def fetch_alerts(lat: float, lon: float, radius: float):
    """
    Fetch alerts from Waze Live Map API based on the given coordinates and radius.

    :param latitude: Latitude of the center point.
    :param longitude: Longitude of the center point.
    :param radius_km: Radius in kilometers to search for alerts.
    :return: A dictionary containing a list of alerts.
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

    _USER_AGENT_LIST: Final[list[str]] = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
        'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    ]

    # # Create session with proper headers to prevent 403 errors
    # headers = {
    #     "User-Agent": f"HassOS/{HA_VERSION} (WazeAlerts/1.0)",
    #     "Accept": "application/json",
    #     "Accept-Encoding": "gzip, deflate",
    #     "Accept-Language": "en-US,en;q=0.9",
    # }

    def _get_random_user_agent() -> str:
        """Return a random user agent from the list."""
        return random.choice(_USER_AGENT_LIST)


    def _get_browser_headers() -> dict[str, str]:
        """Return headers that mimic a real browser request."""
        return {
            "User-Agent": _get_random_user_agent(),
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.buienalarm.nl/",
            "Origin": "https://www.buienalarm.nl",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

    async with aiohttp.ClientSession() as session:
        response = None
        retries = 3
        for attempt in range(retries):
            try:
                headers = _get_browser_headers()
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 429:
                        # Rate limited - wait before retrying
                        wait_time = 2 ** attempt
                        _LOGGER.warning(
                            f"Rate limited by Waze API. Waiting {wait_time}s before retry {attempt + 1}"
                        )
                        await aiohttp.ClientSession().sleep(wait_time)
                    else:
                        msg = f"Failed to fetch alerts: {response.status}"
                        raise WazeResponseError(msg)
            except aiohttp.ClientError:
                if attempt < retries - 1:
                    wait_time = 1
                    await aiohttp.ClientSession().sleep(wait_time)
                else:
                    raise

        if response and response.status != 200:
            msg = f"Failed to fetch alerts: {response.status}"
            raise WazeResponseError(msg)

        raise WazeResponseError("Unable to connect to Waze API after retries")


class WazeClientError(Exception):
    """Algemene fout voor de Waze-client."""


class WazeResponseError(WazeClientError):
    """Fout bij verwerken van de API-response."""
