"""Coordinator to fetch departures from transport.opendata.ch."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class SwissTransportCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch departures for a station."""

    def __init__(self, hass: HomeAssistant, station: str, limit: int = 5) -> None:
        """Initialize."""
        self.hass = hass
        self.station = station
        self.limit = int(limit)
        super().__init__(
            hass,
            _LOGGER,
            name=f"swiss_transport_{station}",
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        session = async_get_clientsession(self.hass)
        url = f"{API_BASE}/stationboard?station={self.station}&limit={self.limit}"
        try:
            async with session.get(url, timeout=30) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                data = await resp.json()
        except asyncio.TimeoutError as err:
            raise UpdateFailed(err)
        except Exception as err:
            raise UpdateFailed(err)

        # parse departures
        departures = []
        for item in data.get("stationboard", []):
            departure = {
                "name": item.get("name"),
                "category": item.get("category"),
                "number": item.get("number"),
                "to": item.get("to"),
                "stop": item.get("stop", {}).get("departure"),
                "platform": item.get("stop", {}).get("platform"),
                # include delay in minutes if present (API provides stop.delay)
                "delay": item.get("stop", {}).get("delay"),
            }
            departures.append(departure)

        return {"station": self.station, "departures": departures}
