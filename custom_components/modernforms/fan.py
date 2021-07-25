"""Platform for ModernForms fan integration."""
import logging, math
import modernforms as mf

from homeassistant.components.fan import (
    SUPPORT_DIRECTION,
    SUPPORT_SET_SPEED,
    FanEntity,
)
from homeassistant.util.percentage import (
    int_states_in_range,
    ranged_value_to_percentage,
    percentage_to_ranged_value,
)

from .const import DOMAIN
from . import ModernFormsEntity

_LOGGER = logging.getLogger(__name__)
PLATFORM = "fan"
SPEED_RANGE = (1, 6)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Handle creation of entity."""
    async_add_devices([ModernFormsFan(hass, config_entry)], False)


class ModernFormsFan(ModernFormsEntity, FanEntity):
    """Representation of an ModernForms Fan."""

    def __init__(self, hass, config_entry):
        """Initialize a ModernFormsFan."""
        super().__init__(hass, config_entry, PLATFORM)
        self._config_entry = config_entry
        self._coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
        self._fan = hass.data[DOMAIN][config_entry.entry_id]["device"]

    @property
    def supported_features(self):
        """Return supported features of fan."""
        return SUPPORT_DIRECTION | SUPPORT_SET_SPEED

    @property
    def is_on(self):
        """Return state of fan."""
        return self._coordinator.data["fanOn"]

    def turn_on(
        self,
        speed: str = None,
        percentage: int = None,
        preset_mode: str = None,
        **kwargs,
    ) -> None:
        """Instruct the fan to turn on."""
        _LOGGER.debug("Attempting to turn on %s", self.entity_id)
        if self._coordinator.last_update_success:
            payload = {"fanOn": True}
            if percentage is not None:
                payload["fanSpeed"] = math.ceil(
                    percentage_to_ranged_value(SPEED_RANGE, percentage)
                )
            try:
                self._fan.set_device_state(payload)
            except (mf.exceptions.ConnectionError, mf.exceptions.Timeout):
                _LOGGER.error(
                    "%s did not respond to command. Cannot turn on.", self.entity_id
                )

    def turn_off(self, **kwargs):
        """Instruct the fan to turn off."""
        _LOGGER.debug("Attempting to turn off %s", self.entity_id)
        if self._coordinator.last_update_success:
            try:
                self._fan.fan_on = False
            except (mf.exceptions.ConnectionError, mf.exceptions.Timeout):
                _LOGGER.error(
                    "%s did not respond to command. Cannot turn off.", self.entity_id
                )

    @property
    def speed_count(self):
        """Return the number of speeds the fan supports."""
        return int_states_in_range(SPEED_RANGE)

    @property
    def percentage(self):
        """Return the current speed percentage"""
        return ranged_value_to_percentage(
            SPEED_RANGE, self._coordinator.data["fanSpeed"]
        )

    def set_percentage(self, percentage: int) -> None:
        """Set speed of Fan"""
        _LOGGER.debug("Attempting to set speed of %s", self.entity_id)
        if self._coordinator.last_update_success:
            try:
                self._fan.fan_speed = math.ceil(
                    percentage_to_ranged_value(SPEED_RANGE, percentage)
                )
            except (mf.exceptions.ConnectionError, mf.exceptions.Timeout):
                _LOGGER.error(
                    "%s did not respond to command. Cannot turn off.", self.entity_id
                )

    @property
    def current_direction(self):
        """Return the direction of the fan."""
        return self._coordinator.data["fanDirection"]

    def set_direction(self, direction):
        """Set the direction of the fan."""
        _LOGGER.debug("Attempting to change direction of %s", self.entity_id)
        if self._coordinator.last_update_success:
            try:
                self._fan.fan_direction = direction
            except (mf.exceptions.ConnectionError, mf.exceptions.Timeout):
                _LOGGER.error(
                    "%s did not respond to command. Cannot change direction.",
                    self.entity_id,
                )
