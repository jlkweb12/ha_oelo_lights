"""The Oelo Lights integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_IP_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN
from .coordinator import OeloDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LIGHT]

SERVICE_CONTROL_LIGHTS = "control_lights"

# The control_lights service is registered by the light platform as an entity
# service (see light.py), so that a call is routed to the targeted entity and
# reaches that entity's own controller. This module deliberately registers no
# service of its own: a second registration under the same name would shadow or
# be shadowed by the platform's depending on setup order.


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Oelo Lights from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    ip_address = entry.data[CONF_IP_ADDRESS]
    session = aiohttp_client.async_get_clientsession(hass)

    # Create coordinator and test connection before forwarding to platforms
    coordinator = OeloDataUpdateCoordinator(hass, session, ip_address)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:  # noqa: BLE001
        raise ConfigEntryNotReady(
            f"Unable to connect to Oelo controller at {ip_address}: {err}"
        ) from err

    # Store coordinator in hass.data for use by platforms
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

        # Home Assistant does not remove a platform's entity service when the
        # platform unloads, so the last entry out has to clear it. Only loaded
        # entries are counted: one sitting in SETUP_RETRY has no entities for
        # the service to address.
        others_loaded = any(
            other.entry_id != entry.entry_id and other.state is ConfigEntryState.LOADED
            for other in hass.config_entries.async_entries(DOMAIN)
        )
        if not others_loaded and hass.services.has_service(DOMAIN, SERVICE_CONTROL_LIGHTS):
            hass.services.async_remove(DOMAIN, SERVICE_CONTROL_LIGHTS)

    return unload_ok
