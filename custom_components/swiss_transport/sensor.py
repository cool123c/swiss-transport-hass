"""Sensor platform for Swiss Transport departures."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEFAULT_NAME, CONF_STATION, CONF_LIMIT
from .coordinator import SwissTransportCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensor from a config entry."""
    station = entry.data.get(CONF_STATION)
    limit = entry.data.get(CONF_LIMIT, 5)

    coordinator = SwissTransportCoordinator(hass, station, limit)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([SwissTransportSensor(coordinator, entry, name=entry.title)])


class SwissTransportSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing next departures for a station."""

    _attr_should_poll = False
    _attr_native_unit_of_measurement = "min"
    try:
        from homeassistant.components.sensor import SensorStateClass

        _attr_state_class = SensorStateClass.MEASUREMENT
    except Exception:
        # older HA may not have SensorStateClass
        _attr_state_class = None

    def __init__(self, coordinator: SwissTransportCoordinator, entry: ConfigEntry, name: str | None = None) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entry = entry
        self._attr_name = name or DEFAULT_NAME
        # prefer stable unique_id created in config flow, fall back to entry_id
        self._attr_unique_id = entry.unique_id or entry.entry_id

        # Device info so the sensor is grouped under a device in the UI
        try:
            self._attr_device_info = {
                "identifiers": {(DOMAIN, self._attr_unique_id)},
                "name": self._attr_name,
                "manufacturer": "Swiss Transport",
            }
        except Exception:
            self._attr_device_info = None

    @property
    def native_value(self) -> Any:
        """Return the state — minutes until next departure or unknown."""
        data = self.coordinator.data or {}
        departures = data.get("departures") or []
        if not departures:
            return None

        # take first departure stop time
        dt_str = departures[0].get("stop")
        if not dt_str:
            return None

        try:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            minutes = int((dt - now).total_seconds() / 60)
            return minutes
        except Exception:  # fallback to returning the raw time string
            return dt_str

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes with upcoming departures."""
        data = self.coordinator.data or {}
        departures = data.get("departures") or []
        return {"station": data.get("station"), "departures": departures}
