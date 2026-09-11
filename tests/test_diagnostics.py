"""Tests for Oelo Lights diagnostics."""

from __future__ import annotations

from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.oelo_lights.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import MOCK_CONTROLLER_DATA, MOCK_IP


async def test_diagnostics_redacts_ip_address(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """The controller IP is redacted and coordinator state is reported.

    The IP is the only identifying value in the entry, so a diagnostics file
    users attach to a bug report must not leak it.
    """
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert result["entry"]["data"][CONF_IP_ADDRESS] == "**REDACTED**"
    assert MOCK_IP not in str(result["entry"]["data"])
    assert result["entry"]["title"] == mock_config_entry.title
    assert result["entry"]["version"] == mock_config_entry.version
    assert result["entry"]["options"] == {}

    assert result["coordinator"]["last_update_success"] is True
    assert result["coordinator"]["data"] == MOCK_CONTROLLER_DATA
    assert result["coordinator"]["update_interval"] == "0:00:30"
