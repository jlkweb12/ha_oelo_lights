from __future__ import annotations

import logging
import urllib.parse
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import aiohttp_client, config_validation as cv

from .const import (
    DOMAIN,
    MAX_COLORS,
    MODE_CUSTOM,
    MODE_PRESET,
    PATTERN_TYPE_CUSTOM,
    DEFAULT_TIMEOUT,
)
from .patterns import get_preset

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LIGHT]

SERVICE_CONTROL_LIGHTS = "control_lights"

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("mode"): vol.In([MODE_PRESET, MODE_CUSTOM]),
        vol.Optional("target_zones"): cv.ensure_list,
        vol.Optional("preset_name"): cv.string,
        vol.Optional("custom_pattern_type", default=PATTERN_TYPE_CUSTOM): cv.string,
        vol.Optional("colors"): vol.All(cv.ensure_list, vol.Length(max=MAX_COLORS)),
        vol.Optional("speed", default=1): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("gap", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Oelo Lights from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the domain service if not already registered
    if not hass.services.has_service(DOMAIN, SERVICE_CONTROL_LIGHTS):
        async def handle_control_lights(call: ServiceCall) -> None:
            """Handle the control_lights service call."""
            mode = call.data["mode"]
            target_zones = call.data.get("target_zones", ["1"])
            preset_name = call.data.get("preset_name")
            custom_pattern_type = call.data.get("custom_pattern_type", PATTERN_TYPE_CUSTOM)
            colors = call.data.get("colors")
            speed = call.data.get("speed", 1)
            gap = call.data.get("gap", 0)

            # Get the IP address from the config entry
            ip_address = entry.data[CONF_IP_ADDRESS]
            session = aiohttp_client.async_get_clientsession(hass)

            zones_str = ",".join(str(z) for z in target_zones)
            num_zones = len(target_zones)

            url_to_send: str | None = None

            if mode == MODE_PRESET:
                if not preset_name:
                    _LOGGER.error("Preset name required for Preset mode")
                    return

                preset = get_preset(preset_name)
                if not preset:
                    _LOGGER.error("Preset '%s' not found", preset_name)
                    return

                url_to_send = _build_preset_url(
                    ip_address,
                    preset,
                    zones_str=zones_str,
                    num_zones=num_zones,
                    speed_override=speed if speed != 1 else None,
                    gap_override=gap if gap != 0 else None,
                )

            elif mode == MODE_CUSTOM:
                if not colors:
                    _LOGGER.error("Colors required for Custom mode")
                    return

                validated_colors = _validate_colors(colors)
                if not validated_colors:
                    _LOGGER.error("Invalid colors provided")
                    return

                url_to_send = _build_custom_url(
                    ip_address,
                    pattern_type=custom_pattern_type,
                    colors=validated_colors,
                    zones_str=zones_str,
                    num_zones=num_zones,
                    speed=speed,
                    gap=gap,
                )

            if url_to_send:
                try:
                    async with session.get(url_to_send, timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)) as response:
                        response.raise_for_status()
                        _LOGGER.debug("Successfully sent command to Oelo controller")
                except Exception as err:
                    _LOGGER.error("Failed to send command to Oelo controller: %s", err)

        hass.services.async_register(
            DOMAIN,
            SERVICE_CONTROL_LIGHTS,
            handle_control_lights,
            schema=SERVICE_SCHEMA,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Only unregister service if no more entries
    if unload_ok:
        # Check if there are other config entries still loaded
        remaining_entries = [
            e for e in hass.config_entries.async_entries(DOMAIN)
            if e.entry_id != entry.entry_id
        ]
        if not remaining_entries and hass.services.has_service(DOMAIN, SERVICE_CONTROL_LIGHTS):
            hass.services.async_remove(DOMAIN, SERVICE_CONTROL_LIGHTS)

    return unload_ok


def _validate_colors(colors: list[list[int]]) -> list[tuple[int, int, int]] | None:
    """Validate and convert a list of colors."""
    validated: list[tuple[int, int, int]] = []
    for color in colors[:MAX_COLORS]:
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            try:
                validated.append((int(color[0]), int(color[1]), int(color[2])))
            except (ValueError, TypeError):
                return None
        else:
            return None
    return validated if validated else None


def _build_base_params(
    pattern_type: str,
    colors: list[tuple[int, int, int]],
    zones_str: str,
    num_zones: int,
    speed: int,
    gap: int,
) -> dict[str, Any]:
    """Build base URL parameters for setPattern endpoint."""
    color_values = []
    for rgb in colors:
        color_values.extend(rgb)

    return {
        "patternType": pattern_type,
        "num_zones": num_zones,
        "zones": zones_str,
        "num_colors": len(colors),
        "colors": ",".join(map(str, color_values)),
        "direction": "F",
        "speed": speed,
        "gap": gap,
        "other": 0,
        "pause": 0,
    }


def _build_preset_url(
    ip_address: str,
    preset: Any,
    zones_str: str,
    num_zones: int,
    speed_override: int | None = None,
    gap_override: int | None = None,
) -> str:
    """Build URL for a preset pattern command."""
    params = _build_base_params(
        pattern_type=preset.pattern_type,
        colors=preset.colors,
        zones_str=zones_str,
        num_zones=num_zones,
        speed=speed_override if speed_override is not None else preset.speed,
        gap=gap_override if gap_override is not None else preset.gap,
    )
    return f"http://{ip_address}/setPattern?{urllib.parse.urlencode(params)}"


def _build_custom_url(
    ip_address: str,
    pattern_type: str,
    colors: list[tuple[int, int, int]],
    zones_str: str,
    num_zones: int,
    speed: int,
    gap: int,
) -> str:
    """Build URL for a custom pattern command."""
    params = _build_base_params(
        pattern_type=pattern_type,
        colors=colors,
        zones_str=zones_str,
        num_zones=num_zones,
        speed=speed,
        gap=gap,
    )
    return f"http://{ip_address}/setPattern?{urllib.parse.urlencode(params)}"