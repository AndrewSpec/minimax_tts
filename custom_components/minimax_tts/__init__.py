"""MiniMax text-to-speech integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .settings import settings_for_entry
from .websocket_client import MiniMaxAuthError, MiniMaxError, MiniMaxWebSocketClient

PLATFORMS = [Platform.TTS]


@dataclass
class MiniMaxRuntimeData:
    client: MiniMaxWebSocketClient
    voices: dict[str, str]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    settings = settings_for_entry(entry)
    client = MiniMaxWebSocketClient(
        async_get_clientsession(hass), settings["api_key"], settings["region"]
    )
    try:
        voices = await client.get_voices()
    except MiniMaxAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except MiniMaxError as err:
        raise ConfigEntryNotReady(str(err)) from err
    entry.runtime_data = MiniMaxRuntimeData(client, voices)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    name = settings_for_entry(entry)["name"]
    if entry.title != name:
        hass.config_entries.async_update_entry(entry, title=name)
    await hass.config_entries.async_reload(entry.entry_id)
