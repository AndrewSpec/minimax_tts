"""Home Assistant TTS entity, including streaming input from Assist."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from contextlib import aclosing

import voluptuous as vol
from homeassistant.components.tts import (
    TextToSpeechEntity,
    TTSAudioRequest,
    TTSAudioResponse,
    Voice,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LEGACY_UNSUPPORTED_LANGUAGES, SUPPORTED_LANGUAGES
from .settings import OPTION_NAMES, build_payload, default_options, settings_for_entry
from .websocket_client import MiniMaxAuthError, MiniMaxError

PARALLEL_UPDATES = 0
_SENTENCE_END = re.compile(r"[.!?。！？]\s+|\n+")


async def text_segments(messages: AsyncIterator[str]) -> AsyncIterator[str]:
    """Buffer partial words from an LLM until a sentence boundary is available."""
    buffer = ""
    async for message in messages:
        buffer += message
        while buffer:
            match = _SENTENCE_END.search(buffer)
            if match and match.end() <= 8000:
                end = match.end()
            elif len(buffer) >= 8000:
                end = buffer.rfind(" ", 0, 8000)
                if end <= 0:
                    end = 8000
            else:
                break
            if segment := buffer[:end].strip():
                yield segment
            buffer = buffer[end:]
    if buffer.strip():
        yield buffer.strip()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([MiniMaxTTSEntity(config_entry)])


class MiniMaxTTSEntity(TextToSpeechEntity):
    _attr_supported_options = OPTION_NAMES

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry
        self._client = config_entry.runtime_data.client
        settings = settings_for_entry(config_entry)
        self._attr_unique_id = config_entry.entry_id
        self._attr_name = settings["name"]
        self._attr_default_language = settings["language"]
        self._attr_default_options = default_options(settings)
        self._attr_supported_languages = [
            code
            for code in SUPPORTED_LANGUAGES.values()
            if not (
                settings["model"].startswith("speech-02")
                and code in LEGACY_UNSUPPORTED_LANGUAGES
            )
        ]
        voices = {
            settings["voice_id"]: settings["voice_id"],
            **config_entry.runtime_data.voices,
        }
        self._voices = [Voice(key, name) for key, name in voices.items()]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=settings["name"],
            manufacturer="MiniMax",
            model=settings["model"],
            entry_type=DeviceEntryType.SERVICE,
        )

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice]:
        return self._voices if language in self.supported_languages else []

    def _payload(self, language, options):
        try:
            return build_payload(
                language or self.default_language,
                dict(self.default_options) | (options or {}),
            )
        except vol.Invalid as err:
            raise HomeAssistantError(f"Invalid MiniMax TTS settings: {err}") from err

    def _auth_failed(self):
        self._config_entry.async_start_reauth(self.hass)

    async def async_get_tts_audio(self, message, language, options=None):
        payload = self._payload(language, options)
        try:
            return "mp3", await self._client.synthesize(message, payload)
        except MiniMaxAuthError as err:
            self._auth_failed()
            raise HomeAssistantError(str(err)) from err
        except MiniMaxError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_stream_tts_audio(
        self, request: TTSAudioRequest
    ) -> TTSAudioResponse:
        payload = self._payload(request.language, request.options)

        async def audio_stream():
            try:
                async with aclosing(text_segments(request.message_gen)) as segments:
                    async with aclosing(
                        self._client.stream(segments, payload)
                    ) as stream:
                        async for chunk in stream:
                            yield chunk
            except MiniMaxAuthError as err:
                self._auth_failed()
                raise HomeAssistantError(str(err)) from err
            except MiniMaxError as err:
                raise HomeAssistantError(str(err)) from err

        return TTSAudioResponse("mp3", audio_stream())
