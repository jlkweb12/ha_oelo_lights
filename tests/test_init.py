"""Tests for Oelo Lights setup, teardown and the control_lights service."""

from __future__ import annotations

from unittest.mock import patch

import aiohttp
import pytest
import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.oelo_lights.const import DOMAIN, MODE_PRESET
from custom_components.oelo_lights.patterns import PRESET_PATTERNS

from .conftest import MOCK_CONTROLLER_DATA, MOCK_IP

SERVICE = "control_lights"
SECOND_IP = "192.168.1.51"


def _command_ips(mocker: AiohttpClientMocker) -> list[str]:
    """Return the controller IPs that received a /setPattern command.

    Coordinator polling also hits /getController, so only command endpoints
    identify where a service call was actually delivered.
    """
    return [
        url.host for _method, url, _data, _headers in mocker.mock_calls if "setPattern" in url.path
    ]


async def _setup(hass: HomeAssistant, entry: MockConfigEntry, mocker: AiohttpClientMocker) -> None:
    """Add and set up a config entry with a reachable controller."""
    mocker.get(f"http://{entry.data[CONF_IP_ADDRESS]}/getController", json=MOCK_CONTROLLER_DATA)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def _entity_for(hass: HomeAssistant, entry: MockConfigEntry) -> str:
    """Return one light entity id belonging to the given entry."""
    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert entities, "entry produced no entities"
    return entities[0].entity_id


async def test_setup_entry_succeeds(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A reachable controller loads the entry and registers the service."""
    await _setup(hass, mock_config_entry, aioclient_mock)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hass.services.has_service(DOMAIN, SERVICE)


async def test_setup_entry_retries_when_unreachable(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """An unreachable controller defers setup rather than failing permanently."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", exc=aiohttp.ClientError("unreachable"))
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry_removes_service(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Unloading the last entry tears down the domain service."""
    await _setup(hass, mock_config_entry, aioclient_mock)

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    assert not hass.services.has_service(DOMAIN, SERVICE)


async def test_service_keeps_registered_while_an_entry_remains(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Unloading one of two entries leaves the service available."""
    second = MockConfigEntry(
        domain=DOMAIN,
        title=f"Oelo Lights ({SECOND_IP})",
        data={CONF_IP_ADDRESS: SECOND_IP},
        unique_id=SECOND_IP,
    )
    await _setup(hass, mock_config_entry, aioclient_mock)
    await _setup(hass, second, aioclient_mock)

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, SERVICE)


async def test_service_sends_preset_command(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A preset call issues a request to the configured controller."""
    await _setup(hass, mock_config_entry, aioclient_mock)
    preset = next(iter(PRESET_PATTERNS))
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)
    aioclient_mock.get(f"http://{MOCK_IP}/setPattern", text="ok")

    await hass.services.async_call(
        DOMAIN,
        SERVICE,
        {
            "mode": MODE_PRESET,
            "preset_name": preset,
            "target_zones": ["1"],
            "entity_id": _entity_for(hass, mock_config_entry),
        },
        blocking=True,
    )

    assert _command_ips(aioclient_mock) == [MOCK_IP]


async def test_service_ignores_unknown_preset(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """An unknown preset name is logged and dropped, not raised.

    The command endpoint is registered so that a request would be recorded.
    Asserting on an *unregistered* endpoint would be vacuous: an unmatched
    request raises inside the entity and is swallowed, leaving mock_calls empty
    whether or not the integration tried to send anything.
    """
    await _setup(hass, mock_config_entry, aioclient_mock)
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)
    aioclient_mock.get(f"http://{MOCK_IP}/setPattern", text="ok")

    await hass.services.async_call(
        DOMAIN,
        SERVICE,
        {
            "mode": MODE_PRESET,
            "preset_name": "No Such Preset",
            "target_zones": ["1"],
            "entity_id": _entity_for(hass, mock_config_entry),
        },
        blocking=True,
    )

    assert _command_ips(aioclient_mock) == []


async def test_service_dispatches_per_targeted_entity(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """With two controllers, each target reaches its own controller.

    `control_lights` is served by the light platform's entity service, so the
    targeted entity - not the order the entries were set up in - decides which
    controller receives the command.
    """
    second = MockConfigEntry(
        domain=DOMAIN,
        title=f"Oelo Lights ({SECOND_IP})",
        data={CONF_IP_ADDRESS: SECOND_IP},
        unique_id=SECOND_IP,
    )
    await _setup(hass, mock_config_entry, aioclient_mock)
    await _setup(hass, second, aioclient_mock)
    preset = next(iter(PRESET_PATTERNS))

    for entry, expected_ip in ((mock_config_entry, MOCK_IP), (second, SECOND_IP)):
        aioclient_mock.clear_requests()
        for ip in (MOCK_IP, SECOND_IP):
            aioclient_mock.get(f"http://{ip}/getController", json=MOCK_CONTROLLER_DATA)
            aioclient_mock.get(f"http://{ip}/setPattern", text="ok")

        await hass.services.async_call(
            DOMAIN,
            SERVICE,
            {
                "mode": MODE_PRESET,
                "preset_name": preset,
                "target_zones": ["1"],
                "entity_id": _entity_for(hass, entry),
            },
            blocking=True,
        )

        assert _command_ips(aioclient_mock) == [expected_ip]


async def test_service_requires_a_target(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A call with no entity/device/area target is rejected.

    `__init__.py` also defines a target-free domain service. On a successful
    setup the light platform registers the same service name first, so the
    `if not has_service(...)` guard skips the domain handler and a target is
    mandatory - the behaviour asserted here.

    This is not guaranteed: if the light platform fails to set up, the entry
    still loads and the domain handler IS registered, accepting target-free
    calls and rejecting entity-targeted ones (its schema has no entity_id key).
    See test_domain_service_registers_when_platform_fails.
    """
    await _setup(hass, mock_config_entry, aioclient_mock)

    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE,
            {
                "mode": MODE_PRESET,
                "preset_name": next(iter(PRESET_PATTERNS)),
                "target_zones": ["1"],
            },
            blocking=True,
        )


async def test_domain_service_registers_when_platform_fails(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A failed light platform leaves the target-free domain handler registered.

    `async_forward_entry_setups` does not propagate a platform failure, so the
    entry still loads, no entity service is registered, and the `has_service`
    guard in `async_setup_entry` lets the domain handler through. The result is
    that the same service name has two possible handlers with incompatible
    schemas, decided by whether platform setup happened to succeed.
    """
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)
    aioclient_mock.get(f"http://{MOCK_IP}/setPattern", text="ok")
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.oelo_lights.light.Store.async_load",
        side_effect=HomeAssistantError("corrupt store"),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert not er.async_entries_for_config_entry(er.async_get(hass), mock_config_entry.entry_id), (
        "platform was expected to fail, producing no entities"
    )
    assert hass.services.has_service(DOMAIN, SERVICE)

    # The domain handler accepts a call with no target, which the entity service
    # would reject outright.
    await hass.services.async_call(
        DOMAIN,
        SERVICE,
        {"mode": MODE_PRESET, "preset_name": next(iter(PRESET_PATTERNS)), "target_zones": ["3"]},
        blocking=True,
    )

    assert _command_ips(aioclient_mock) == [MOCK_IP]
