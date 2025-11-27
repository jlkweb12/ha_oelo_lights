"""Config flow for Oelo Lights integration."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.helpers import aiohttp_client

from .const import DEFAULT_TIMEOUT, DOMAIN

_LOGGER = logging.getLogger(__name__)

# IP address validation regex
IP_REGEX = re.compile(
    r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_IP_ADDRESS): str,
})


def is_valid_ip(ip: str) -> bool:
    """Validate IP address format."""
    return bool(IP_REGEX.match(ip.strip()))


class OeloConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Oelo Lights."""

    VERSION = 1

    async def _test_connection(self, ip: str) -> tuple[bool, str | None]:
        """Test connection to the Oelo controller."""
        session = aiohttp_client.async_get_clientsession(self.hass)
        url = f"http://{ip}/getController"

        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json(content_type=None)
                        if isinstance(data, list):
                            return True, None
                        return False, "invalid_response"
                    return False, "cannot_connect"
        except asyncio.TimeoutError:
            return False, "timeout"
        except aiohttp.ClientError:
            return False, "cannot_connect"
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Unexpected error connecting to Oelo controller: %s", err)
            return False, "unknown"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            ip_address = user_input[CONF_IP_ADDRESS].strip()

            # Validate IP format
            if not is_valid_ip(ip_address):
                errors["base"] = "invalid_ip"
            else:
                # Check for existing entry with same IP
                await self.async_set_unique_id(ip_address)
                self._abort_if_unique_id_configured()

                # Test connection
                success, error = await self._test_connection(ip_address)
                if success:
                    return self.async_create_entry(
                        title=f"Oelo Lights ({ip_address})",
                        data={CONF_IP_ADDRESS: ip_address},
                    )
                if error:
                    errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )