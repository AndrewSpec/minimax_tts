from unittest.mock import AsyncMock, MagicMock

import pytest
import voluptuous as vol
from homeassistant.components.tts import TTSAudioRequest
from homeassistant.exceptions import HomeAssistantError

from custom_components.minimax_tts.const import DEFAULTS
from custom_components.minimax_tts.diagnostics import async_get_config_entry_diagnostics
from custom_components.minimax_tts.settings import build_payload, default_options
from custom_components.minimax_tts.tts import MiniMaxTTSEntity, text_segments
from custom_components.minimax_tts.websocket_client import MiniMaxAuthError


async def test_language_options_and_existing_id(entry):
    entity = MiniMaxTTSEntity(entry)
    entry.runtime_data.client.synthesize.return_value = b"audio"
    assert entity.unique_id == entry.entry_id
    assert await entity.async_get_tts_audio(
        "Hello", "de", {"voice": "custom", "speed": 1.5}
    ) == ("mp3", b"audio")
    payload = entry.runtime_data.client.synthesize.call_args.args[1]
    assert payload["language_boost"] == "German"
    assert payload["voice_setting"]["voice_id"] == "custom"
    assert payload["voice_setting"]["speed"] == 1.5
    assert entity.default_options["speed"] == 1
    assert "voice" in entity.supported_options
    assert entity.async_get_supported_voices("pl")[0].voice_id == DEFAULTS["voice_id"]


@pytest.mark.parametrize(
    "override",
    [
        {"speed": float("nan")},
        {"pitch": float("inf")},
        {"speed": 0},
        {"vol": 0},
        {"vol": 11},
        {"pitch": 1.5},
        {"pitch": 13},
        {"emotion": "whisper"},
        {"sample_rate": 123},
        {"channel": True},
        {"voice_modify": {"pitch": 101}},
        {"unknown": 3},
        {"english_normalization": "false"},
    ],
)
def test_invalid_options_rejected(override):
    with pytest.raises(vol.Invalid):
        build_payload("pl", default_options(DEFAULTS) | override)


def test_language_mapping_and_advanced_options():
    options = default_options(DEFAULTS) | {
        "emotion": "happy",
        "pronunciation_dict": {"tone": ["HA/Home Assistant"]},
        "voice_modify": {"sound_effects": "robotic"},
    }
    payload = build_payload("yue", options)
    assert payload["language_boost"] == "Chinese,Yue"
    assert payload["voice_setting"]["emotion"] == "happy"
    assert payload["pronunciation_dict"] == options["pronunciation_dict"]
    assert (
        "emotion" not in build_payload("nn", default_options(DEFAULTS))["voice_setting"]
    )
    with pytest.raises(vol.Invalid):
        build_payload("fa", options | {"model": "speech-02-hd"})
    assert build_payload(
        "pl", options | {"model": "speech-2.6-hd", "emotion": "whisper"}
    )


async def test_diagnostics_exclude_secrets(entry):
    output = await async_get_config_entry_diagnostics(None, entry)
    assert "secret" not in str(output)
    assert "voice_id" not in str(output)
    assert output["voice_count"] == 1


async def test_streaming_starts_before_input_finishes(entry):
    entity = MiniMaxTTSEntity(entry)

    async def messages():
        yield "Pierwsze zdanie. "
        yield "Drugie zda"
        yield "nie."

    received = []

    async def stream(texts, payload):
        async for segment in texts:
            received.append(segment)
            yield b"audio"

    entry.runtime_data.client.stream = stream
    response = await entity.async_stream_tts_audio(
        TTSAudioRequest("pl", {}, messages())
    )
    assert await anext(response.data_gen) == b"audio"
    assert received == ["Pierwsze zdanie."]
    assert b"".join([chunk async for chunk in response.data_gen]) == b"audio"
    assert received == ["Pierwsze zdanie.", "Drugie zdanie."]


async def test_long_stream_is_split_without_losing_words():
    text = "word " * 5000

    async def messages():
        yield text

    segments = [part async for part in text_segments(messages())]
    assert all(len(part) <= 8000 for part in segments)
    assert " ".join(segments).split() == text.split()


async def test_auth_failure_starts_reauth(entry):
    entity = MiniMaxTTSEntity(entry)
    entity.hass = MagicMock()
    entry.runtime_data.client.synthesize = AsyncMock(
        side_effect=MiniMaxAuthError("Invalid key")
    )
    from unittest.mock import patch

    with patch.object(type(entry), "async_start_reauth") as reauth:
        with pytest.raises(HomeAssistantError):
            await entity.async_get_tts_audio("Hello", "pl")
        reauth.assert_called_once()
