from __future__ import annotations
import logging

from homeassistant.components.tts import TextToSpeechEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .websocket_client import MiniMaxWebSocketClient

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_MODEL,
    CONF_VOICE_ID,
    CONF_TTS_NAME,
    CONF_SPEED,
    CONF_VOL,
    CONF_PITCH,
    CONF_DEFAULT_VOICE,
    CONF_DEFAULT_MODEL,
    CONF_DEFAULT_TTS_NAME,
    CONF_DEFAULT_LANGUAGE,
    CONF_DEFAULT_SPEED,
    CONF_DEFAULT_VOL,
    CONF_DEFAULT_PITCH,
    SUPPORTED_LANGUAGES
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([MiniMaxTTSEntity(hass, config_entry)])


class MiniMaxTTSEntity(TextToSpeechEntity):

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        self.hass = hass
        self._config_entry = config_entry
        self._attr_unique_id = config_entry.entry_id

        self._attr_name = config_entry.options.get(
            CONF_TTS_NAME,
            config_entry.data.get(CONF_TTS_NAME, CONF_DEFAULT_TTS_NAME)
        )

        raw_language = config_entry.options.get(
            CONF_LANGUAGE,
            config_entry.data.get(CONF_LANGUAGE, CONF_DEFAULT_LANGUAGE)
        )
        
        if raw_language in SUPPORTED_LANGUAGES:
            self._language = SUPPORTED_LANGUAGES[raw_language]
        else:
            self._language = raw_language

        self._api_key = config_entry.options.get(
            CONF_API_KEY,
            config_entry.data.get(CONF_API_KEY, "")
        )

        self._model = config_entry.options.get(
            CONF_MODEL,
            config_entry.data.get(CONF_MODEL, CONF_DEFAULT_MODEL)
        )

        self._voice = config_entry.options.get(
            CONF_VOICE_ID,
            config_entry.data.get(CONF_VOICE_ID, CONF_DEFAULT_VOICE)
        )

        self._attr_supported_languages = list(SUPPORTED_LANGUAGES.values())

        _LOGGER.debug(
            "MiniMax Init -> Lang: %s, Voice: %s, Model: %s", 
            self._language, self._voice, self._model
        )

        self._speed = config_entry.options.get(
            CONF_SPEED, config_entry.data.get(CONF_SPEED, CONF_DEFAULT_SPEED)
        )
        self._vol = config_entry.options.get(
            CONF_VOL, config_entry.data.get(CONF_VOL, CONF_DEFAULT_VOL)
        )
        self._pitch = config_entry.options.get(
            CONF_PITCH, config_entry.data.get(CONF_PITCH, CONF_DEFAULT_PITCH)
        )

        self._client = MiniMaxWebSocketClient(
            self.hass, 
            self._api_key, 
            self._model, 
            self._voice, 
            self._language,
            self._speed,
            self._vol,
            self._pitch
        )

    @property
    def default_language(self):
        return self._language

    async def async_get_tts_audio(self, message, language, options=None):
        audio = await self._client.synthesize(message)

        if audio:
            return "mp3", audio
        
        return None, None