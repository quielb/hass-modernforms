"""Platform for ModernForms light integration."""
import logging
import modernforms as mf

from homeassistant.components.light import (  # PLATFORM_SCHEMA,
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)

from .const import DOMAIN
from . import ModernFormsEntity

_LOGGER = logging.getLogger(__name__)
PLATFORM = "light"


def scale_brightness_to_fan(brightness):
    """Return a brightness value the fan will accept."""
    scaled_brightness = int((brightness / 255) * 100)
    if scaled_brightness == 0:
        scaled_brightness = 1
    return scaled_brightness


def scale_brightness_to_ha(brightness):
    """Return a brightness value for the HA scale."""
    scaled_brightness = (brightness / 100) * 255
    return int(scaled_brightness)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Handle creation of entity."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_devices([ModernFormsLight(hass, config_entry)], False)


class ModernFormsLight(ModernFormsEntity, LightEntity):
    """Representation of an ModernForms Light."""

    def __init__(self, hass, config_entry):
        """Initialize a ModernFormsLight."""
        super().__init__(hass, config_entry, PLATFORM)
        self._config_entry = config_entry
        self._coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
        self._light = hass.data[DOMAIN][config_entry.entry_id]["device"]

    @property
    def supported_features(self):
        """Return supported features of light."""
        return SUPPORT_BRIGHTNESS

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return scale_brightness_to_ha(self._coordinator.data["lightBrightness"])

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._coordinator.data["lightOn"]

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        _LOGGER.debug("Attempting to turn on %s", self.entity_id)
        payload = {}
        if self._coordinator.last_update_success:
            payload["lightOn"] = True
            if "brightness" in kwargs:
                # Need to scale brightness.  HA is 0-255, light is 1-100
                brightness = kwargs.get(ATTR_BRIGHTNESS)
                scaled_brightness = scale_brightness_to_fan(brightness)
                payload["lightBrightness"] = scaled_brightness
            try:
                self._light.set_device_state(payload)
            except (mf.exceptions.ConnectionError, mf.exceptions.Timeout):
                _LOGGER.error(
                    "%s did not respond to command. Cannot turn on.", self.entity_id
                )

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        _LOGGER.debug("Attempting to turn off %s", self.entity_id)
        if self._coordinator.last_update_success:
            try:
                self._light.light_on = False
            except (mf.exceptions.ConnectionError, mf.exceptions.Timeout):
                _LOGGER.error(
                    "%s did not respond to command. Cannot turn off.", self.entity_id
                )
