"""Diagnostics deliberately omit credentials, voice IDs and spoken content."""

from .settings import settings_for_entry


async def async_get_config_entry_diagnostics(hass, entry):
    settings = settings_for_entry(entry)
    runtime = getattr(entry, "runtime_data", None)
    return {
        "settings": {
            key: settings[key]
            for key in (
                "model",
                "language",
                "region",
                "speed",
                "vol",
                "pitch",
                "emotion",
                "english_normalization",
                "sample_rate",
                "bitrate",
                "channel",
            )
        },
        "voice_count": len(runtime.voices) if runtime else None,
    }
