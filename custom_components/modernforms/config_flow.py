"""Config flow for ModernForms integration."""
from __future__ import annotations

import logging
from typing import Any
import modernforms as mf

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({"host": str})


async def validate_input(hass, CONF_HOST):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    device = await hass.async_add_executor_job(mf.ModernFormsFan, CONF_HOST)
    try:
        device_data = await hass.async_add_executor_job(device.get_device_state)
    except (mf.exceptions.ConnectionError, mf.exceptions.Timeout):
        raise CannotConnect
    else:
        return device_data


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ModernForms."""

    VERSION = 1

    host = None
    device_info = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:

            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        self.host = user_input[CONF_HOST]
        errors = {}

        try:
            self.device_info = await validate_input(self.hass, self.host)
            self.device_info[CONF_HOST] = self.host
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(self.device_info["clientId"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self.device_info["deviceName"], data=self.device_info
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_zeroconf(self, discovery_info):
        """Handle discovery by zeroconf."""
        _LOGGER.debug("Starting zeroconf config flow with info:\n%s", discovery_info)

        self.host = discovery_info[CONF_HOST]
        self.device_info = await validate_input(self.hass, self.host)
        self.device_info[CONF_HOST] = self.host
        self.context["title"] = self.device_info["deviceName"]
        # exit if already configured
        await self.async_set_unique_id(self.device_info["clientId"])
        self._abort_if_unique_id_configured(updates={CONF_HOST: self.host})

        self.context["title_placeholders"] = {"name": self.device_info["deviceName"]}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input=None):
        """Handle user-confirmation of discovered device."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title=self.device_info["deviceName"], data=self.device_info
            )

        self._set_confirm_only()

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "model": self.device_info["fanType"],
                "name": self.device_info["deviceName"],
            },
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
