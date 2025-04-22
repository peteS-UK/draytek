"""The Draytek Router integration."""

from __future__ import annotations

from asyncio import timeout
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import DraytekDataUpdateCoordinator

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
_PLATFORMS: list[Platform] = [Platform.SENSOR]


@dataclass
class DraytekData:
    """SqueezeboxData data class."""

    coordinator: DraytekDataUpdateCoordinator
    name: str


type DraytekConfigEntry = ConfigEntry[DraytekData]


# TODO Update entry annotation
async def async_setup_entry(
    hass: HomeAssistant, config_entry: DraytekConfigEntry
) -> bool:
    """Set up Draytek Router from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    coordinator = DraytekDataUpdateCoordinator(hass, config_entry)
    config_entry.runtime_data = DraytekData(
        coordinator=coordinator, name=config_entry.data[CONF_NAME]
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(config_entry, _PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: DraytekConfigEntry
) -> bool:
    """Unload a config entry."""
    config_entry.runtime_data.coordinator.snmpEngine.close_dispatcher()
    return await hass.config_entries.async_unload_platforms(config_entry, _PLATFORMS)
