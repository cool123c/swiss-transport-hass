"""Config flow for Swiss Transport integration."""
from __future__ import annotations

import logging

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .const import DOMAIN, API_BASE, CONF_STATION, CONF_LIMIT

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .const import DOMAIN, API_BASE, CONF_STATION, CONF_LIMIT

_LOGGER = logging.getLogger(__name__)


class SwissTransportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Swiss Transport."""

    VERSION = 1

    def __init__(self):
        self._stations: dict[str, dict] = {}

    async def async_step_user(self, user_input=None):
        """Ask the user for a station name to search for."""
        errors = {}

        if user_input is not None:
            query = user_input.get(CONF_STATION)
            limit = user_input.get(CONF_LIMIT, 5)

            session = async_get_clientsession(self.hass)
            url = f"{API_BASE}/locations?query={query}"
            try:
                async with session.get(url, timeout=15) as resp:
                    if resp.status != 200:
                        _LOGGER.debug("Locations request returned status %s", resp.status)
                        errors["base"] = "cannot_connect"
                    else:
                        data = await resp.json()
                        locations = data.get("stations") or data.get("stations")
            except Exception as exc:
                _LOGGER.exception("Error fetching station locations: %s", exc)
                errors["base"] = "cannot_connect"
                locations = None

            if not errors:
                if not locations:
                    errors["station"] = "not_found"
                elif len(locations) == 1:
                    # Single match -> create entry
                    station_obj = locations[0]
                    unique_id = f"{station_obj.get('id') or station_obj.get('name')}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()
                    title = station_obj.get("name") or query
                    return self.async_create_entry(
                        title=title,
                        data={
                            CONF_STATION: station_obj.get("name"),
                            CONF_LIMIT: int(limit),
                        },
                    )
                else:
                    # Multiple matches -> present choices
                    options = {}
                    self._stations = {}
                    for s in locations:
                        # build a key for selection; prefer id if available
                        key = str(s.get("id") or s.get("name"))
                        label = s.get("name")
                        if s.get("distance") is not None:
                            label = f"{label} ({s.get('distance')} m)"
                        options[key] = label
                        self._stations[key] = s

                    # store limit for later
                    self._limit = int(limit)

                    schema = vol.Schema({vol.Required("station_select"): vol.In(options)})
                    return self.async_show_form(
                        step_id="select",
                        data_schema=schema,
                        description_placeholders={"query": query},
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_STATION): str,
                vol.Optional(CONF_LIMIT, default=5): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_select(self, user_input=None):
        """Handle selection of a station from the previous search."""
        if user_input is None:
            return self.async_abort(reason="no_selection")

        key = user_input.get("station_select")
        station_obj = self._stations.get(str(key))
        if not station_obj:
            return self.async_abort(reason="not_found")

        unique_id = f"{station_obj.get('id') or station_obj.get('name')}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        title = station_obj.get("name")
        return self.async_create_entry(
            title=title,
            data={
                CONF_STATION: station_obj.get("name"),
                CONF_LIMIT: int(getattr(self, "_limit", 5)),
            },
        )
