"""Data update coordinator for Oelo Lights integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_TIMEOUT, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class OeloDataUpdateCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator to manage fetching Oelo controller data."""

    def __init__(
        self, hass: HomeAssistant, session: aiohttp.ClientSession, ip: str
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Oelo Controller {ip}",
            update_interval=SCAN_INTERVAL,
        )
        self.session = session
        self.ip = ip

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch data from the Oelo controller."""
        url = f"http://{self.ip}/getController"
        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json(content_type=None)
                    if not isinstance(data, list):
                        raise UpdateFailed("Controller did not return a list")
                    return data
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout communicating with Oelo controller") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Oelo controller: {err}") from err