"""Fixtures for Oelo Lights tests."""

from __future__ import annotations

import pytest
from homeassistant.const import CONF_IP_ADDRESS
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.oelo_lights.const import DOMAIN

MOCK_IP = "192.168.1.50"

# A /getController payload shaped the way the integration actually reads it:
# OeloLight._get_zone_data() matches on an int "num" and the state is derived
# from "pattern" (PATTERN_TYPE_OFF means off). One entry per zone, so every
# entity resolves its own data instead of going unavailable.
MOCK_CONTROLLER_DATA: list[dict] = [
    {
        "num": zone,
        "pattern": "stationary",
        "colors": [[255, 255, 255]],
        "speed": 0,
        "gap": 0,
    }
    for zone in range(1, 7)
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
