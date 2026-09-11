"""Tests for OeloLight behaviour, covering previously broken paths."""

from __future__ import annotations

import asyncio
import urllib.parse

import pytest
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_RGB_COLOR
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from .conftest import MOCK_CONTROLLER_DATA, MOCK_IP


@pytest.fixture
async def light_entity(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> str:
    """Set up the integration and return zone 1's entity id."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)
    aioclient_mock.get(f"http://{MOCK_IP}/setPattern", text="ok")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    entities = er.async_entries_for_config_entry(er.async_get(hass), mock_config_entry.entry_id)
    return sorted(e.entity_id for e in entities)[0]


def _sent_colors(mocker: AiohttpClientMocker) -> list[str]:
    """Return the `colors` parameter of every command sent, in order."""
    out = []
    for _method, url, _data, _headers in mocker.mock_calls:
        if "setPattern" not in url.path:
            continue
        query = urllib.parse.parse_qs(urllib.parse.urlparse(str(url)).query)
        out.append(query["colors"][0])
    return out


async def _turn_on(hass: HomeAssistant, entity_id: str, **data) -> None:
    await hass.services.async_call(
        "light", "turn_on", {"entity_id": entity_id, **data}, blocking=True
    )
    await hass.async_block_till_done()


async def test_brightness_only_change_while_on_is_sent(
    hass: HomeAssistant, light_entity: str, aioclient_mock: AiohttpClientMocker
) -> None:
    """Changing only brightness on an already-on light sends a command.

    Regression: the turn-on branches only matched RGB, effect, or off->on, so a
    brightness-only change produced no command and the UI snapped back.
    """
    await _turn_on(hass, light_entity, rgb_color=[255, 0, 0], brightness=255)
    assert _sent_colors(aioclient_mock)[-1] == "255,0,0"

    before = len(_sent_colors(aioclient_mock))
    await _turn_on(hass, light_entity, brightness=64)

    colors = _sent_colors(aioclient_mock)
    assert len(colors) == before + 1, "brightness-only change sent no command"
    assert colors[-1] == "64,0,0"
    assert hass.states.get(light_entity).attributes[ATTR_BRIGHTNESS] == 64


async def test_brightness_does_not_compound_across_off_on(
    hass: HomeAssistant, light_entity: str, aioclient_mock: AiohttpClientMocker
) -> None:
    """Brightness applies to the base color, not to the last scaled command.

    Regression: the stored command already had brightness baked in and was
    scaled again on the next turn-on, halving the color every off/on cycle.
    """
    await _turn_on(hass, light_entity, rgb_color=[255, 0, 0], brightness=128)
    assert _sent_colors(aioclient_mock)[-1] == "128,0,0"

    await hass.services.async_call("light", "turn_off", {"entity_id": light_entity}, blocking=True)
    await hass.async_block_till_done()

    await _turn_on(hass, light_entity, brightness=128)
    assert _sent_colors(aioclient_mock)[-1] == "128,0,0", "brightness compounded"

    # And a third cycle must not drift either.
    await hass.services.async_call("light", "turn_off", {"entity_id": light_entity}, blocking=True)
    await hass.async_block_till_done()
    await _turn_on(hass, light_entity, brightness=128)
    assert _sent_colors(aioclient_mock)[-1] == "128,0,0"


async def test_rgb_is_preserved_at_full_brightness(
    hass: HomeAssistant, light_entity: str, aioclient_mock: AiohttpClientMocker
) -> None:
    """A full-brightness turn-on sends the requested color unscaled."""
    await _turn_on(hass, light_entity, rgb_color=[10, 200, 30], brightness=255)

    assert _sent_colors(aioclient_mock)[-1] == "10,200,30"
    state = hass.states.get(light_entity)
    assert state.attributes[ATTR_RGB_COLOR] == (10, 200, 30)


async def test_pending_command_does_not_hang_on_unload(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Unloading while a command is debounced resolves the waiting caller.

    Regression: removal cancelled the debounce task but left the future
    unresolved, so the caller awaited it forever.
    """
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)
    aioclient_mock.get(f"http://{MOCK_IP}/setPattern", text="ok")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    entity_id = sorted(
        e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), mock_config_entry.entry_id)
    )[0]

    task = hass.async_create_task(
        hass.services.async_call(
            "light", "turn_on", {"entity_id": entity_id, "brightness": 200}, blocking=True
        )
    )
    # Yield just enough for the call to reach the debouncer, but stay inside the
    # DEBOUNCE_INTERVAL window so the command is still pending at unload.
    # async_block_till_done() here would let the send complete and the hang
    # would never be exercised.
    await asyncio.sleep(0.05)

    # Every await here is bounded. Without the fix the unresolved future blocks
    # unload itself, so an unbounded version of this test hangs the run instead
    # of failing it.
    try:
        async with asyncio.timeout(20):
            assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
            await hass.async_block_till_done()
    except TimeoutError:
        task.cancel()
        pytest.fail("unload blocked on an unresolved pending command")

    # The only failure mode under test is hanging: the caller must stop waiting
    # once the entity is gone, whether it returns or raises.
    try:
        await asyncio.wait_for(task, timeout=10)
    except TimeoutError:
        pytest.fail("pending command never resolved after unload")
    except Exception:  # noqa: BLE001 - any resolution is acceptable, a hang is not
        pass
