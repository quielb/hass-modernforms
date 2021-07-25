"""The ModernForms integration."""
from __future__ import annotations

import logging
import modernforms as mf
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["light", "fan"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ModernForms from a config entry."""
    _LOGGER.debug("Starting async_setup_entry with config_entry:\n%s", entry.as_dict())

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})

    device = await hass.async_add_executor_job(mf.ModernFormsFan, entry.data[CONF_HOST])

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            return await hass.async_add_executor_job(device.get_device_state)
        except (mf.exceptions.ConnectionError, mf.exceptions.Timeout) as error:
            raise UpdateFailed(f"Fetch of data failed: {error}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("Data from initial coordinator fetch:\n%s", coordinator.data)

    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    hass.data[DOMAIN][entry.entry_id]["device"] = device
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


class ModernFormsEntity(CoordinatorEntity, Entity):
    """Define a base ModernForms Device."""

    def __init__(self, hass, entry, platform):
        self._coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        self._entry_id = entry.entry_id
        self._name = self._coordinator.data.get(
            "name", self._coordinator.data["deviceName"]
        )
        self._attr_unique_id = self._coordinator.data["clientId"] + "-" + platform
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._coordinator.data["clientId"])},
            "name": self._coordinator.data.get(
                "name", self._coordinator.data["deviceName"]
            ),
            "manufacturer": "Modern Forms",
            "sw_version": self._coordinator.data["firmwareVersion"],
            "model": self._coordinator.data["fanType"],
        }
        super().__init__(self._coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
