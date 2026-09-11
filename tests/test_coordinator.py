"""Tests for the Oelo data update coordinator."""

from __future__ import annotations

import aiohttp
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.oelo_lights.coordinator import OeloDataUpdateCoordinator

from .conftest import MOCK_CONTROLLER_DATA, MOCK_IP

URL = f"http://{MOCK_IP}/getController"


def _coordinator(hass: HomeAssistant) -> OeloDataUpdateCoordinator:
    return OeloDataUpdateCoordinator(hass, async_get_clientsession(hass), MOCK_IP)


async def test_update_returns_controller_list(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A well-formed response is returned verbatim."""
    aioclient_mock.get(URL, json=MOCK_CONTROLLER_DATA)

    assert await _coordinator(hass)._async_update_data() == MOCK_CONTROLLER_DATA


async def test_update_rejects_non_list_payload(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A JSON object instead of a list is an UpdateFailed, not a crash."""
    aioclient_mock.get(URL, json={"unexpected": "shape"})

    with pytest.raises(UpdateFailed, match="did not return a list"):
        await _coordinator(hass)._async_update_data()


async def test_update_raises_on_http_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A non-2xx status is surfaced as UpdateFailed via raise_for_status."""
    aioclient_mock.get(URL, status=500)

    with pytest.raises(UpdateFailed):
        await _coordinator(hass)._async_update_data()


async def test_update_raises_on_timeout(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A timeout is reported distinctly."""
    aioclient_mock.get(URL, exc=TimeoutError())

    with pytest.raises(UpdateFailed, match="Timeout"):
        await _coordinator(hass)._async_update_data()


async def test_update_raises_on_client_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A transport failure is reported with the underlying message."""
    aioclient_mock.get(URL, exc=aiohttp.ClientError("boom"))

    with pytest.raises(UpdateFailed, match="boom"):
        await _coordinator(hass)._async_update_data()


async def test_coordinator_identity(hass: HomeAssistant) -> None:
    """The coordinator records the controller it polls."""
    coordinator = _coordinator(hass)

    assert coordinator.ip == MOCK_IP
    assert MOCK_IP in coordinator.name
    assert coordinator.update_interval.total_seconds() == 30
