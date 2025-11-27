"""Platform for Oelo Lights integration."""
from __future__ import annotations

import asyncio
import logging
import urllib.parse
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, config_validation as cv, entity_platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.storage import Store

from .const import (
    DEBOUNCE_INTERVAL,
    DEFAULT_BRIGHTNESS,
    DEFAULT_COLOR,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_COLORS,
    MODE_CUSTOM,
    MODE_PRESET,
    NUM_ZONES,
    PATTERN_TYPE_CUSTOM,
    PATTERN_TYPE_OFF,
    STORAGE_KEY_BASE,
    STORAGE_VERSION,
)
from .coordinator import OeloDataUpdateCoordinator
from .patterns import get_preset, get_preset_names

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Oelo Light entities from a config entry."""
    ip_address = entry.data[CONF_IP_ADDRESS]
    session = aiohttp_client.async_get_clientsession(hass)

    coordinator = OeloDataUpdateCoordinator(hass, session, ip_address)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})

    storage_key = f"{STORAGE_KEY_BASE}_{entry.entry_id}"
    store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, storage_key)
    stored_data = await store.async_load() or {}

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "store": store,
        "stored_entity_data": stored_data,
    }

    entities = [
        OeloLight(
            coordinator=coordinator,
            zone=zone,
            entry=entry,
            restored_last_command=stored_data.get(f"zone_{zone}_last_command"),
        )
        for zone in range(1, NUM_ZONES + 1)
    ]
    async_add_entities(entities, update_before_add=True)

    # Register the control service
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "control_lights",
        {
            vol.Required("mode"): vol.In([MODE_PRESET, MODE_CUSTOM]),
            vol.Optional("target_zones"): cv.ensure_list,
            vol.Optional("preset_name"): cv.string,
            vol.Optional("custom_pattern_type", default=PATTERN_TYPE_CUSTOM): cv.string,
            vol.Optional("colors"): vol.All(cv.ensure_list, vol.Length(max=MAX_COLORS)),
            vol.Optional("speed", default=1): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            vol.Optional("gap", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        },
        "async_control_oelo_lights",
    )


class OeloLight(LightEntity, RestoreEntity):
    """Representation of an Oelo Light zone."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(
        self,
        coordinator: OeloDataUpdateCoordinator,
        zone: int,
        entry: ConfigEntry,
        restored_last_command: str | None = None,
    ) -> None:
        """Initialize an Oelo Light entity."""
        self.coordinator = coordinator
        self._zone = zone
        self._entry = entry
        self._state = False
        self._brightness: int = DEFAULT_BRIGHTNESS
        self._rgb_color: tuple[int, int, int] = DEFAULT_COLOR
        self._intended_effect: str | None = None
        self._last_successful_command: str | None = restored_last_command

        # Debouncing state
        self._pending_command_url: str | None = None
        self._pending_command_future: asyncio.Future[bool] | None = None
        self._debounce_task: asyncio.Task[None] | None = None

        # Entity attributes
        self._attr_unique_id = f"{entry.entry_id}_zone_{zone}"
        self._attr_name = f"Zone {zone}"
        self._attr_available = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="Oelo",
            model="Light Controller",
            configuration_url=f"http://{self.coordinator.ip}/",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._attr_available

    @property
    def is_on(self) -> bool | None:
        """Return True if the light is on."""
        return self._state if self.available else None

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        return self._brightness if self.available else None

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the RGB color value."""
        return self._rgb_color if self.available else None

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        if not self.available or not self.is_on:
            return None
        return self._intended_effect

    @property
    def effect_list(self) -> list[str] | None:
        """Return the list of available effects."""
        return get_preset_names() if self.available else None

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()
        self.coordinator.async_add_listener(self._handle_coordinator_update)

        last_state = await self.async_get_last_state()
        if last_state:
            self._state = last_state.state == STATE_ON
            self._brightness = last_state.attributes.get(ATTR_BRIGHTNESS, DEFAULT_BRIGHTNESS)
            self._intended_effect = last_state.attributes.get(ATTR_EFFECT)

            rgb_restored = last_state.attributes.get(ATTR_RGB_COLOR)
            if self._is_valid_rgb(rgb_restored):
                self._rgb_color = tuple(int(c) for c in rgb_restored)  # type: ignore[misc]
            else:
                self._rgb_color = DEFAULT_COLOR

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity is being removed."""
        if self._debounce_task:
            self._debounce_task.cancel()

    async def async_update(self) -> None:
        """Request a coordinator refresh."""
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.last_update_success:
            if self._attr_available:
                self._attr_available = False
                self.async_write_ha_state()
            return

        zone_data = self._get_zone_data()
        if not zone_data:
            self._attr_available = False
            self.async_write_ha_state()
            return

        current_pattern = zone_data.get("pattern")
        is_on = current_pattern != PATTERN_TYPE_OFF
        state_changed = self._state != is_on

        if not self._attr_available:
            self._attr_available = True

        if state_changed:
            self._state = is_on
            if not is_on:
                self._intended_effect = None

        self.async_write_ha_state()

    def _get_zone_data(self) -> dict[str, Any] | None:
        """Get data for this zone from coordinator."""
        data = self.coordinator.data
        if not data:
            return None

        for item in data:
            if isinstance(item, dict) and item.get("num") == self._zone:
                return item
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        url_to_send: str | None = None
        effect_to_set: str | None = self._intended_effect
        rgb_to_set: tuple[int, int, int] = self._rgb_color
        brightness_to_set = kwargs.get(ATTR_BRIGHTNESS, self._brightness) or DEFAULT_BRIGHTNESS
        brightness_to_set = max(0, min(brightness_to_set, 255))
        brightness_factor = brightness_to_set / 255.0

        if ATTR_RGB_COLOR in kwargs:
            rgb_to_set = tuple(kwargs[ATTR_RGB_COLOR])  # type: ignore[assignment]
            effect_to_set = None
            url_to_send = self._build_color_url(rgb_to_set, brightness_factor)

        elif ATTR_EFFECT in kwargs:
            selected_effect = kwargs[ATTR_EFFECT]
            preset = get_preset(selected_effect)
            if preset:
                effect_to_set = selected_effect
                url_to_send = self._build_preset_url(preset, brightness_factor)

        elif not self._state:
            # Turning on without specific params
            if self._last_successful_command:
                url_to_send = self._adjust_colors_in_url(
                    self._last_successful_command, brightness_factor
                )
            else:
                rgb_to_set = DEFAULT_COLOR
                url_to_send = self._build_color_url(rgb_to_set, brightness_factor)

        if url_to_send:
            success = await self._buffered_send_request(url_to_send)
            if success:
                self._state = True
                self._brightness = brightness_to_set
                self._rgb_color = rgb_to_set
                self._intended_effect = effect_to_set
                self._last_successful_command = url_to_send
                self.async_write_ha_state()
            else:
                _LOGGER.warning("Failed to send command to Oelo controller")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        url_params = self._build_base_params(PATTERN_TYPE_OFF, [(0, 0, 0)])
        url = f"http://{self.coordinator.ip}/setPattern?{urllib.parse.urlencode(url_params)}"

        success = await self._buffered_send_request(url)
        if success:
            self._state = False
            self.async_write_ha_state()
        else:
            _LOGGER.warning("Failed to turn off Oelo light")

    async def async_control_oelo_lights(
        self,
        mode: str,
        target_zones: list[int] | None = None,
        preset_name: str | None = None,
        custom_pattern_type: str = PATTERN_TYPE_CUSTOM,
        colors: list[list[int]] | None = None,
        speed: int = 1,
        gap: int = 0,
    ) -> None:
        """Handle the control_lights service call."""
        zone_list = [str(z) for z in target_zones] if target_zones else [str(self._zone)]
        zones_str = ",".join(zone_list)
        num_zones = len(zone_list)

        url_to_send: str | None = None
        effect_name: str | None = None

        if mode == MODE_PRESET:
            if not preset_name:
                _LOGGER.error("Preset name required for Preset mode")
                return

            preset = get_preset(preset_name)
            if not preset:
                _LOGGER.error("Preset '%s' not found", preset_name)
                return

            url_to_send = self._build_preset_url(
                preset,
                brightness_factor=1.0,
                zones_str=zones_str,
                num_zones=num_zones,
                speed_override=speed if speed != 1 else None,
                gap_override=gap if gap != 0 else None,
            )
            effect_name = preset_name
            if preset.colors:
                self._rgb_color = preset.colors[0]

        elif mode == MODE_CUSTOM:
            if not colors:
                _LOGGER.error("Colors required for Custom mode")
                return

            validated_colors = self._validate_colors(colors)
            if not validated_colors:
                _LOGGER.error("Invalid colors provided")
                return

            url_to_send = self._build_custom_url(
                pattern_type=custom_pattern_type,
                colors=validated_colors,
                zones_str=zones_str,
                num_zones=num_zones,
                speed=speed,
                gap=gap,
            )
            effect_name = custom_pattern_type
            self._rgb_color = validated_colors[0]

        if url_to_send:
            success = await self._buffered_send_request(url_to_send)
            if success:
                self._state = True
                self._intended_effect = effect_name
                self._last_successful_command = url_to_send
                await self._save_last_command()
                self.async_write_ha_state()
            else:
                _LOGGER.error("Failed to execute control_lights command")

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------

    @staticmethod
    def _is_valid_rgb(value: Any) -> bool:
        """Check if value is a valid RGB tuple/list."""
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            return False
        try:
            return all(isinstance(int(c), int) for c in value)
        except (ValueError, TypeError):
            return False

    def _validate_colors(
        self, colors: list[list[int]]
    ) -> list[tuple[int, int, int]] | None:
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
        self,
        pattern_type: str,
        colors: list[tuple[int, int, int]],
        zones_str: str | None = None,
        num_zones: int = 1,
        speed: int = 0,
        gap: int = 0,
    ) -> dict[str, Any]:
        """Build base URL parameters for setPattern endpoint."""
        color_values = []
        for rgb in colors:
            color_values.extend(rgb)

        return {
            "patternType": pattern_type,
            "num_zones": num_zones,
            "zones": zones_str or str(self._zone),
            "num_colors": len(colors),
            "colors": ",".join(map(str, color_values)),
            "direction": "F",
            "speed": speed,
            "gap": gap,
            "other": 0,
            "pause": 0,
        }

    def _build_color_url(
        self,
        rgb: tuple[int, int, int],
        brightness_factor: float,
    ) -> str:
        """Build URL for a single color command."""
        scaled = self._scale_color(rgb, brightness_factor)
        params = self._build_base_params(PATTERN_TYPE_CUSTOM, [scaled])
        return f"http://{self.coordinator.ip}/setPattern?{urllib.parse.urlencode(params)}"

    def _build_preset_url(
        self,
        preset: Any,  # PatternConfig
        brightness_factor: float,
        zones_str: str | None = None,
        num_zones: int = 1,
        speed_override: int | None = None,
        gap_override: int | None = None,
    ) -> str:
        """Build URL for a preset pattern command."""
        scaled_colors = [self._scale_color(c, brightness_factor) for c in preset.colors]
        params = self._build_base_params(
            pattern_type=preset.pattern_type,
            colors=scaled_colors,
            zones_str=zones_str,
            num_zones=num_zones,
            speed=speed_override if speed_override is not None else preset.speed,
            gap=gap_override if gap_override is not None else preset.gap,
        )
        return f"http://{self.coordinator.ip}/setPattern?{urllib.parse.urlencode(params)}"

    def _build_custom_url(
        self,
        pattern_type: str,
        colors: list[tuple[int, int, int]],
        zones_str: str,
        num_zones: int,
        speed: int,
        gap: int,
    ) -> str:
        """Build URL for a custom pattern command."""
        params = self._build_base_params(
            pattern_type=pattern_type,
            colors=colors,
            zones_str=zones_str,
            num_zones=num_zones,
            speed=speed,
            gap=gap,
        )
        return f"http://{self.coordinator.ip}/setPattern?{urllib.parse.urlencode(params)}"

    @staticmethod
    def _scale_color(
        rgb: tuple[int, int, int], factor: float
    ) -> tuple[int, int, int]:
        """Scale RGB color by brightness factor."""
        return tuple(  # type: ignore[return-value]
            max(0, min(int(round(c * factor)), 255)) for c in rgb
        )

    def _adjust_colors_in_url(self, url: str, brightness_factor: float) -> str:
        """Adjust color values in an existing URL by brightness factor."""
        try:
            parsed = urllib.parse.urlparse(url)
            query = urllib.parse.parse_qs(parsed.query)

            if "colors" in query:
                color_values = [int(c) for c in query["colors"][0].split(",")]
                scaled = [max(0, min(int(round(v * brightness_factor)), 255)) for v in color_values]
                query["colors"] = [",".join(map(str, scaled))]
                new_query = urllib.parse.urlencode(query, doseq=True)
                return urllib.parse.urlunparse(parsed._replace(query=new_query))
        except (ValueError, KeyError, IndexError) as err:
            _LOGGER.debug("Failed to adjust colors in URL: %s", err)

        return url

    async def _save_last_command(self) -> None:
        """Save the last successful command to persistent storage."""
        if not self.hass:
            return

        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
        if not entry_data:
            return

        store: Store[dict[str, Any]] | None = entry_data.get("store")
        stored_data: dict[str, Any] | None = entry_data.get("stored_entity_data")

        if not store or stored_data is None:
            return

        entity_key = f"zone_{self._zone}_last_command"

        if self._last_successful_command is None:
            stored_data.pop(entity_key, None)
        else:
            stored_data[entity_key] = self._last_successful_command

        try:
            await store.async_save(stored_data)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Failed to save last command to storage: %s", err)

    async def _buffered_send_request(self, url: str) -> bool:
        """Send a request with debouncing to avoid overwhelming the controller."""
        loop = asyncio.get_running_loop()

        # Cancel any pending request
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
        if self._pending_command_future and not self._pending_command_future.done():
            self._pending_command_future.cancel()

        self._pending_command_url = url
        self._pending_command_future = loop.create_future()
        self._debounce_task = loop.create_task(self._debounce_and_send())

        try:
            return await self._pending_command_future
        except asyncio.CancelledError:
            return False

    async def _debounce_and_send(self) -> None:
        """Wait for debounce interval then send the pending command."""
        try:
            await asyncio.sleep(DEBOUNCE_INTERVAL)

            url = self._pending_command_url
            future = self._pending_command_future

            if not url or not future or future.cancelled():
                return

            async with asyncio.timeout(DEFAULT_TIMEOUT):
                async with self.coordinator.session.get(url) as response:
                    response.raise_for_status()
                    if not future.done():
                        future.set_result(True)

        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout sending command to Oelo controller")
            if self._pending_command_future and not self._pending_command_future.done():
                self._pending_command_future.set_result(False)
        except aiohttp.ClientError as err:
            _LOGGER.warning("Error sending command to Oelo controller: %s", err)
            if self._pending_command_future and not self._pending_command_future.done():
                self._pending_command_future.set_result(False)
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Unexpected error sending command: %s", err)
            if self._pending_command_future and not self._pending_command_future.done():
                self._pending_command_future.set_result(False)