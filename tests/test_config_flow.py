"""Tests for the Oelo Lights config flow."""

from __future__ import annotations

import aiohttp
import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.oelo_lights.config_flow import is_valid_ip
from custom_components.oelo_lights.const import DOMAIN

from .conftest import MOCK_CONTROLLER_DATA, MOCK_IP


@pytest.mark.parametrize(
    "ip",
    ["192.168.1.50", "10.0.0.1", "0.0.0.0", "255.255.255.255", "  192.168.1.50  "],
)
def test_is_valid_ip_accepts(ip: str) -> None:
    """Well-formed IPv4 addresses are accepted, including padded input."""
    assert is_valid_ip(ip) is True


@pytest.mark.parametrize(
    "ip",
    [
        "",
        "192.168.1",
        "192.168.1.256",
        "256.1.1.1",
        "192.168.1.1.1",
        "oelo.local",
        "192.168.1.-1",
        "1.1.1.1a",
        "::1",
    ],
)
def test_is_valid_ip_rejects(ip: str) -> None:
    """Malformed addresses and hostnames are rejected."""
    assert is_valid_ip(ip) is False


async def _start_flow(hass: HomeAssistant, ip: str) -> dict:
    """Run the user step with the given IP."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    return await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_IP_ADDRESS: ip})


async def test_user_flow_creates_entry(
    hass: HomeAssistant,
    custom_integration: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A reachable controller produces a config entry."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)

    result = await _start_flow(hass, MOCK_IP)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Oelo Lights ({MOCK_IP})"
    assert result["data"] == {CONF_IP_ADDRESS: MOCK_IP}
    assert result["result"].unique_id == MOCK_IP


async def test_user_flow_strips_whitespace(
    hass: HomeAssistant,
    custom_integration: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Surrounding whitespace is stripped before the entry is stored."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)

    result = await _start_flow(hass, f"  {MOCK_IP}  ")

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_IP_ADDRESS: MOCK_IP}


async def test_user_flow_invalid_ip(hass: HomeAssistant, custom_integration: None) -> None:
    """A malformed IP is reported on the form without any network call."""
    result = await _start_flow(hass, "not-an-ip")

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_ip"}


async def test_user_flow_non_list_response(
    hass: HomeAssistant,
    custom_integration: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 200 response that is not a list is treated as an invalid response."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json={"unexpected": "shape"})

    result = await _start_flow(hass, MOCK_IP)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_response"}


async def test_user_flow_http_error(
    hass: HomeAssistant,
    custom_integration: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A non-200 status surfaces as cannot_connect."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", status=500)

    result = await _start_flow(hass, MOCK_IP)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_client_error(
    hass: HomeAssistant,
    custom_integration: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A transport-level failure surfaces as cannot_connect."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", exc=aiohttp.ClientError("boom"))

    result = await _start_flow(hass, MOCK_IP)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_timeout(
    hass: HomeAssistant,
    custom_integration: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A timeout is reported distinctly from a connection failure."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", exc=TimeoutError())

    result = await _start_flow(hass, MOCK_IP)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "timeout"}


async def test_user_flow_unexpected_error(
    hass: HomeAssistant,
    custom_integration: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """An unexpected exception is caught and reported as unknown."""
    aioclient_mock.get(f"http://{MOCK_IP}/getController", exc=ValueError("surprise"))

    result = await _start_flow(hass, MOCK_IP)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_user_flow_aborts_on_duplicate(
    hass: HomeAssistant,
    custom_integration: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Configuring the same controller twice aborts instead of duplicating."""
    mock_config_entry.add_to_hass(hass)
    aioclient_mock.get(f"http://{MOCK_IP}/getController", json=MOCK_CONTROLLER_DATA)

    result = await _start_flow(hass, MOCK_IP)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
