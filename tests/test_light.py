"""Tests for OeloLight behaviour, covering previously broken paths."""

from __future__ import annotations

import asyncio
import urllib.parse

import aiohttp
import pytest
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_EFFECT, ATTR_RGB_COLOR
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, mock_restore_cache
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.oelo_lights.const import (
    DEFAULT_COLOR,
    DOMAIN,
    MODE_CUSTOM,
    MODE_PRESET,
)

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


async def _refresh(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Force a coordinator update so entity listeners run.

    Entities are added with update_before_add=True, but the coordinator
    listener is only attached in async_added_to_hass - after that first
    refresh. So _handle_coordinator_update does not run during setup, and a
    second refresh is required to observe controller state.
    """
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_refresh()
    await hass.async_block_till_done()


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


async def test_turn_off_sends_off_pattern(
    hass: HomeAssistant, light_entity: str, aioclient_mock: AiohttpClientMocker
) -> None:
    """Turning off sends the off pattern and clears the state."""
    await _turn_on(hass, light_entity, rgb_color=[255, 0, 0], brightness=255)

    await hass.services.async_call("light", "turn_off", {"entity_id": light_entity}, blocking=True)
    await hass.async_block_till_done()

    last = [str(url) for _m, url, _d, _h in aioclient_mock.mock_calls if "setPattern" in url.path][
        -1
    ]
    assert "patternType=off" in last
    assert hass.states.get(light_entity).state == STATE_OFF


async def test_effect_is_applied_and_reported(
    hass: HomeAssistant, light_entity: str, aioclient_mock: AiohttpClientMocker
) -> None:
    """Selecting an effect sends its pattern and reports it back."""
    effect = "Solid Color: Blue"

    await _turn_on(hass, light_entity, effect=effect)

    state = hass.states.get(light_entity)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_EFFECT] == effect
    assert _sent_colors(aioclient_mock)[-1] == "0,0,255"


async def test_effect_then_brightness_keeps_effect(
    hass: HomeAssistant, light_entity: str, aioclient_mock: AiohttpClientMocker
) -> None:
    """A brightness change after an effect re-sends that effect, scaled.

    This is the path that previously sent nothing at all, and it must rebuild
    from the preset rather than from the last scaled URL.
    """
    await _turn_on(hass, light_entity, effect="Solid Color: Blue", brightness=255)
    assert _sent_colors(aioclient_mock)[-1] == "0,0,255"

    await _turn_on(hass, light_entity, brightness=128)

    assert _sent_colors(aioclient_mock)[-1] == "0,0,128"
    assert hass.states.get(light_entity).attributes[ATTR_EFFECT] == "Solid Color: Blue"


async def test_unknown_effect_sends_nothing(
    hass: HomeAssistant, light_entity: str, aioclient_mock: AiohttpClientMocker
) -> None:
    """An effect name with no preset produces no command."""
    before = len(_sent_colors(aioclient_mock))

    await _turn_on(hass, light_entity, effect="No Such Effect")

    assert len(_sent_colors(aioclient_mock)) == before


async def test_entities_follow_controller_pattern(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A coordinator refresh derives on/off per zone from the `pattern` field."""
    payload = [dict(item) for item in MOCK_CONTROLLER_DATA]
    payload[0]["pattern"] = "off"
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=payload)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    await _refresh(hass, mock_config_entry)

    entities = sorted(
        e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), mock_config_entry.entry_id)
    )

    assert hass.states.get(entities[0]).state == STATE_OFF
    assert hass.states.get(entities[1]).state == STATE_ON


async def test_entities_go_unavailable_when_zone_missing(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A zone absent from the controller payload becomes unavailable."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=[MOCK_CONTROLLER_DATA[0]])
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    await _refresh(hass, mock_config_entry)

    entities = sorted(
        e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), mock_config_entry.entry_id)
    )

    assert hass.states.get(entities[0]).state == STATE_ON
    assert hass.states.get(entities[5]).state == STATE_UNAVAILABLE


async def test_unavailable_entity_reports_no_attributes(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """An unavailable zone exposes no on/brightness/rgb/effect values."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=[MOCK_CONTROLLER_DATA[0]])
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    await _refresh(hass, mock_config_entry)

    entity_id = sorted(
        e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), mock_config_entry.entry_id)
    )[5]
    state = hass.states.get(entity_id)

    assert state.state == STATE_UNAVAILABLE
    assert ATTR_BRIGHTNESS not in state.attributes
    assert ATTR_RGB_COLOR not in state.attributes


async def test_entities_go_unavailable_when_controller_fails(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A failed poll marks every zone unavailable."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    aioclient_mock.clear_requests()
    aioclient_mock.get(f"http://{MOCK_IP}/getController", exc=aiohttp.ClientError("down"))
    await _refresh(hass, mock_config_entry)

    entity_id = sorted(
        e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), mock_config_entry.entry_id)
    )[0]
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_service_custom_mode_sends_given_colors(
    hass: HomeAssistant, light_entity: str, aioclient_mock: AiohttpClientMocker
) -> None:
    """Custom mode forwards validated colors and pattern settings."""
    await hass.services.async_call(
        DOMAIN,
        "control_lights",
        {
            "mode": MODE_CUSTOM,
            "entity_id": light_entity,
            "target_zones": ["1"],
            "colors": [[10, 20, 30], [40, 50, 60]],
            "custom_pattern_type": "chase",
            "speed": 5,
            "gap": 2,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    url = [str(u) for _m, u, _d, _h in aioclient_mock.mock_calls if "setPattern" in u.path][-1]
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert query["colors"][0] == "10,20,30,40,50,60"
    assert query["num_colors"][0] == "2"
    assert query["patternType"][0] == "chase"
    assert query["speed"][0] == "5"
    assert query["gap"][0] == "2"


async def test_service_custom_mode_rejects_bad_colors(
    hass: HomeAssistant, light_entity: str, aioclient_mock: AiohttpClientMocker
) -> None:
    """Unusable color values produce no command."""
    before = len(_sent_colors(aioclient_mock))

    await hass.services.async_call(
        DOMAIN,
        "control_lights",
        {
            "mode": MODE_CUSTOM,
            "entity_id": light_entity,
            "target_zones": ["1"],
            "colors": [["x", "y", "z"]],
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(_sent_colors(aioclient_mock)) == before


async def test_service_does_not_mark_untargeted_zone_on(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Targeting zone 1 but addressing zone 2 leaves zone 1's state alone.

    Regression: the entity the call was routed through was marked on with the
    preset's effect even though the command addressed a different zone.
    """
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)
    aioclient_mock.get(f"http://{MOCK_IP}/setPattern", text="ok")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    entities = sorted(
        e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), mock_config_entry.entry_id)
    )

    await hass.services.async_call(
        DOMAIN,
        "control_lights",
        {
            "mode": MODE_PRESET,
            "entity_id": entities[0],
            "target_zones": ["2"],
            "preset_name": "Solid Color: Blue",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    url = [str(u) for _m, u, _d, _h in aioclient_mock.mock_calls if "setPattern" in u.path][-1]
    assert "zones=2" in url
    assert hass.states.get(entities[0]).attributes.get(ATTR_EFFECT) is None


async def test_send_failure_leaves_state_unchanged(
    hass: HomeAssistant, light_entity: str, aioclient_mock: AiohttpClientMocker
) -> None:
    """A controller error must not move the entity to on."""
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)
    aioclient_mock.get(f"http://{MOCK_IP}/setPattern", exc=aiohttp.ClientError("nope"))

    await _turn_on(hass, light_entity, rgb_color=[1, 2, 3])

    assert hass.states.get(light_entity).state == STATE_OFF


async def test_state_is_restored_after_restart(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Brightness, color and effect survive a restart via RestoreEntity.

    The brightness fix rebuilds commands from this restored intent, so a wrong
    restore would reintroduce the compounding bug after every restart.
    """
    mock_restore_cache(
        hass,
        [
            State(
                "light.oelo_lights_192_168_1_50_zone_1",
                STATE_ON,
                {
                    ATTR_BRIGHTNESS: 100,
                    ATTR_RGB_COLOR: (12, 34, 56),
                    ATTR_EFFECT: "Solid Color: Blue",
                },
            )
        ],
    )
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("light.oelo_lights_192_168_1_50_zone_1")
    assert state.attributes[ATTR_BRIGHTNESS] == 100
    assert state.attributes[ATTR_RGB_COLOR] == (12, 34, 56)


async def test_invalid_restored_color_falls_back_to_default(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A corrupt restored rgb_color falls back instead of propagating."""
    mock_restore_cache(
        hass,
        [
            State(
                "light.oelo_lights_192_168_1_50_zone_1",
                STATE_ON,
                {ATTR_BRIGHTNESS: 100, ATTR_RGB_COLOR: ("bad", None, 3)},
            )
        ],
    )
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("light.oelo_lights_192_168_1_50_zone_1")
    assert state.attributes[ATTR_RGB_COLOR] == DEFAULT_COLOR
