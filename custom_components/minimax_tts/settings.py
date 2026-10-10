"""Validate settings before making a billable synthesis request."""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite
from typing import Any

import voluptuous as vol

from .const import (
    BITRATES,
    DEFAULTS,
    EMOTIONS,
    LANGUAGE_BOOST,
    LEGACY_UNSUPPORTED_LANGUAGES,
    SAMPLE_RATES,
    SOUND_EFFECTS,
    SUPPORTED_LANGUAGES,
    TTS_MODELS,
)


def nonempty(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise vol.Invalid("A non-empty string is required")
    return value.strip()


def integer(value: Any) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        or int(value) != value
    ):
        raise vol.Invalid("An integer is required")
    return int(value)


def number(value: Any) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
    ):
        raise vol.Invalid("A finite number is required")
    return float(value)


OPTION_SCHEMA = vol.Schema(
    {
        vol.Optional("voice"): nonempty,
        vol.Optional("model"): vol.In(TTS_MODELS),
        vol.Optional("speed"): vol.All(number, vol.Range(min=0.5, max=2)),
        vol.Optional("vol"): vol.All(
            number, vol.Range(min=0, max=10, min_included=False)
        ),
        vol.Optional("pitch"): vol.All(integer, vol.Range(min=-12, max=12)),
        vol.Optional("emotion"): vol.In(EMOTIONS),
        vol.Optional("english_normalization"): bool,
        vol.Optional("sample_rate"): vol.All(integer, vol.In(SAMPLE_RATES)),
        vol.Optional("bitrate"): vol.All(integer, vol.In(BITRATES)),
        vol.Optional("channel"): vol.All(integer, vol.In([1, 2])),
        vol.Optional("pronunciation_dict"): {vol.Required("tone"): [nonempty]},
        vol.Optional("voice_modify"): {
            vol.Optional("pitch"): vol.All(integer, vol.Range(min=-100, max=100)),
            vol.Optional("intensity"): vol.All(integer, vol.Range(min=-100, max=100)),
            vol.Optional("timbre"): vol.All(integer, vol.Range(min=-100, max=100)),
            vol.Optional("sound_effects"): vol.In(SOUND_EFFECTS),
        },
    }
)
OPTION_NAMES = [str(key.schema) for key in OPTION_SCHEMA.schema]


def settings_for_entry(entry) -> dict[str, Any]:
    settings = DEFAULTS | dict(entry.data) | dict(entry.options)
    settings["language"] = SUPPORTED_LANGUAGES.get(
        settings["language"], settings["language"]
    )
    return settings


def default_options(settings: Mapping[str, Any]) -> dict[str, Any]:
    return {key: settings[key] for key in OPTION_NAMES if key in settings} | {
        "voice": settings["voice_id"]
    }


def build_payload(language: str, options: Mapping[str, Any]) -> dict[str, Any]:
    """Convert Home Assistant options to the MiniMax task_start payload."""
    # These are handled by HA's transcoder, not by MiniMax.
    options = {
        key: value for key, value in options.items() if not key.startswith("preferred_")
    }
    values = OPTION_SCHEMA(options)
    if language not in LANGUAGE_BOOST:
        raise vol.Invalid("Unsupported language")
    if (
        values["model"].startswith("speech-02")
        and language in LEGACY_UNSUPPORTED_LANGUAGES
    ):
        raise vol.Invalid("This language requires a speech-2.6 or speech-2.8 model")
    if values.get("emotion") in {"fluent", "whisper"} and not values[
        "model"
    ].startswith("speech-2.6"):
        raise vol.Invalid("fluent and whisper require a speech-2.6 model")
    voice = {
        key: values[key] for key in ("speed", "vol", "pitch", "english_normalization")
    }
    voice["voice_id"] = values["voice"]
    if values.get("emotion", "auto") != "auto":
        voice["emotion"] = values["emotion"]
    payload = {
        "event": "task_start",
        "model": values["model"],
        "language_boost": LANGUAGE_BOOST[language],
        "voice_setting": voice,
        "audio_setting": {
            "format": "mp3",
            **{key: values[key] for key in ("sample_rate", "bitrate", "channel")},
        },
    }
    for key in ("pronunciation_dict", "voice_modify"):
        if values.get(key):
            payload[key] = values[key]
    return payload
