from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.light import (ColorMode, LightEntity, ATTR_BRIGHTNESS, ATTR_RGB_COLOR, ATTR_COLOR_TEMP_KELVIN)
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import GoveeAPI
from .const import DOMAIN
from .coordinator import GoveeCoordinator

import logging
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up a Lights."""
    # This gets the data update coordinator from hass.data as specified in your __init__.py
    coordinator: GoveeCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ].coordinator

    async_add_entities([
        GoveeBluetoothLight(coordinator)
    ], True)


class GoveeBluetoothLight(CoordinatorEntity, LightEntity):

    _attr_supported_color_modes = {ColorMode.RGB, ColorMode.COLOR_TEMP}
    _attr_min_color_temp_kelvin = 2200
    _attr_max_color_temp_kelvin = 6500

    def __init__(self, coordinator: GoveeCoordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._attr_name = coordinator.device_name
        self._attr_unique_id = f"{coordinator.device_address}"
        self._attr_device_info = DeviceInfo(
            #only generate device once!
            manufacturer="GOVEE",
            model=coordinator.device_name,
            serial_number=coordinator.device_address,
            identifiers={(DOMAIN, coordinator.device_address)}
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def brightness(self):
        """Return the current brightness. 1-255"""
        return self.coordinator.data.brightness

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self.coordinator.data.state

    @property
    def rgb_color(self) -> bool | None:
        """Return the current rgw color."""
        return self.coordinator.data.color

    @property
    def color_temp_kelvin(self) -> int | None:
        return self.coordinator.data.color_temp_kelvin

    @property
    def color_mode(self) -> ColorMode:
        """Return the current color mode."""
        if self.color_temp_kelvin:
            return ColorMode.COLOR_TEMP
        return ColorMode.RGB

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        await self.coordinator.setStateBuffered(True)

        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
            await self.coordinator.setBrightnessBuffered(brightness)

        if ATTR_RGB_COLOR in kwargs:
            red, green, blue = kwargs.get(ATTR_RGB_COLOR)
            await self.coordinator.setColorBuffered(red, green, blue)

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
            await self.coordinator.setColorTempBuffered(kelvin)

        await self.coordinator.sendPacketBuffer()

    
    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        await self.coordinator.setStateBuffered(False)
        await self.coordinator.sendPacketBuffer()
