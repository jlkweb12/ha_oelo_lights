"""Fixtures for Oelo Lights tests."""

from __future__ import annotations

import pytest
from homeassistant.const import CONF_IP_ADDRESS
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.oelo_lights.const import DOMAIN

MOCK_IP = "192.168.1.50"

# A minimal but realistic /getController payload: the integration only requires
# that the response decodes to a list.
MOCK_CONTROLLER_DATA: list[dict] = [
    {
        "zone": "1",
        "power": "on",
        "brightness": 255,
        "colors": [[255, 255, 255]],
        "motion": "stationary",
        "speed": 0,
        "gap": 0,
    }
]


@pytest.fixture
def custom_integration(enable_custom_integrations: None) -> None:
    """Allow Home Assistant to load this custom integration.

    Requested explicitly rather than autouse: the pure-logic tests are sync and
    must not pull in the async `hass` fixture that this depends on.
    """
    return None


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a config entry for the integration."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"Oelo Lights ({MOCK_IP})",
        data={CONF_IP_ADDRESS: MOCK_IP},
        unique_id=MOCK_IP,
    )
