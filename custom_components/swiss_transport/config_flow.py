"""Config flow for Swiss Transport integration."""
from __future__ import annotations

import logging

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .const import DOMAIN, API_BASE, CONF_STATION, CONF_LIMIT

_LOGGER = logging.getLogger(__name__)


class SwissTransportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Swiss Transport."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step when a user adds the integration."""
        errors = {}

        if user_input is not None:
            station = user_input.get(CONF_STATION)
            limit = user_input.get(CONF_LIMIT, 5)

            # try to validate station via API
            session = async_get_clientsession(self.hass)
            url = f"{API_BASE}/locations?query={station}"
            try:
                async with session.get(url) as resp:
                    data = await resp.json()
            except Exception as exc:  # network / json error
                _LOGGER.debug("Error fetching station locations: %s", exc)
                errors["base"] = "cannot_connect"
            else:
                locations = data.get("stations") or data.get("stations")
                if not locations:
                    errors["station"] = "not_found"
                else:
                    # take first match
                    station_obj = locations[0]
                    unique_id = f"{station_obj.get('id') or station_obj.get('name')}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    title = station_obj.get("name") or station
                    return self.async_create_entry(
                        title=title,
                        data={
                            CONF_STATION: station_obj.get("name"),
                            CONF_LIMIT: int(limit),
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_STATION): str,
                vol.Optional(CONF_LIMIT, default=5): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
