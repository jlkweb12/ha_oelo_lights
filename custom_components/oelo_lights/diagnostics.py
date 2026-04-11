"""Diagnostics support for Oelo Lights."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import OeloDataUpdateCoordinator

TO_REDACT = {CONF_IP_ADDRESS}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: OeloDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    return {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
            "data": coordinator.data,
        },
    }
