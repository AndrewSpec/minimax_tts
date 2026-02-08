from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_TTS_NAME


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_forward_entry_setups(entry, ["tts"])
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, ["tts"])

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    
    new_name = entry.options.get(CONF_TTS_NAME)
    
    if new_name:
        hass.config_entries.async_update_entry(entry, title=new_name)
    
    await hass.config_entries.async_reload(entry.entry_id)