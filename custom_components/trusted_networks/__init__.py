from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    return True

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the integration."""
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    return True

async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    await async_unload_entry(hass, entry)  # 确保在删除前卸载
    hass.data[DOMAIN].pop(entry.entry_id, None)