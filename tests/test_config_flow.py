from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components.minimax_tts import (
    async_setup_entry,
    async_unload_entry,
    update_listener,
)
from custom_components.minimax_tts.config_flow import (
    MiniMaxOptionsFlow,
    MiniMaxTTSConfigFlow,
    schema,
)
from custom_components.minimax_tts.const import DEFAULTS
from custom_components.minimax_tts.settings import settings_for_entry
from custom_components.minimax_tts.websocket_client import (
    MiniMaxAuthError,
    MiniMaxError,
)


@pytest.fixture(autouse=True)
def mock_session():
    with (
        patch(
            "custom_components.minimax_tts.async_get_clientsession",
            return_value=MagicMock(),
        ),
        patch(
            "custom_components.minimax_tts.config_flow.async_get_clientsession",
            return_value=MagicMock(),
        ),
    ):
        yield


@pytest.mark.parametrize(
    "error,expected",
    [
        (MiniMaxAuthError("bad"), "invalid_auth"),
        (MiniMaxError("network"), "cannot_connect"),
    ],
)
async def test_user_flow_errors_and_retry(error, expected):
    flow = MiniMaxTTSConfigFlow()
    flow.hass = MagicMock()
    with patch(
        "custom_components.minimax_tts.config_flow.validate",
        new=AsyncMock(side_effect=error),
    ):
        result = await flow.async_step_user(DEFAULTS | {"api_key": "secret"})
        assert result["errors"] == {"base": expected}
    with patch(
        "custom_components.minimax_tts.config_flow.validate",
        new=AsyncMock(return_value={}),
    ):
        result = await flow.async_step_user(DEFAULTS | {"api_key": " secret "})
        assert result["type"] == "create_entry"
        assert result["data"]["api_key"] == "secret"


async def test_initial_form_and_blank_key():
    flow = MiniMaxTTSConfigFlow()
    flow.hass = MagicMock()
    form = await flow.async_step_user()
    assert form["type"] == "form"
    result = await flow.async_step_user(DEFAULTS | {"api_key": " "})
    assert result["errors"] == {"base": "invalid_settings"}


def test_form_defaults_validate_and_normalize():
    result = schema(DEFAULTS | {"api_key": "secret"})({})
    assert result["sample_rate"] == "32000"
    assert result["voice_id"] == DEFAULTS["voice_id"]


async def test_options_keep_existing_values(entry):
    flow = MiniMaxOptionsFlow()
    flow.hass = MagicMock()
    flow.handler = entry.entry_id
    flow.hass.config_entries.async_get_known_entry.return_value = entry
    form = await flow.async_step_init()
    assert form["type"] == "form"
    with patch(
        "custom_components.minimax_tts.config_flow.validate",
        new=AsyncMock(return_value={}),
    ):
        result = await flow.async_step_init({"speed": 1.5})
    assert result["data"]["speed"] == 1.5
    assert result["data"]["language"] == "pl"
    assert result["data"]["api_key"] == "secret"


async def test_reauth_removes_old_options_key(entry):
    flow = MiniMaxTTSConfigFlow()
    flow.hass = MagicMock()
    # An actual entry with legacy options is returned by the real flow helper.
    object.__setattr__(
        entry, "options", {"api_key": "old-option-key", "region": "china", "speed": 1.5}
    )
    with (
        patch.object(flow, "_get_reauth_entry", return_value=entry),
        patch.object(
            flow, "async_update_reload_and_abort", return_value={"type": "abort"}
        ) as update,
        patch(
            "custom_components.minimax_tts.config_flow.MiniMaxWebSocketClient.get_voices",
            new=AsyncMock(return_value={}),
        ),
    ):
        await flow.async_step_reauth_confirm({"api_key": "new-key", "region": "global"})
    assert update.call_args.kwargs["data_updates"] == {
        "api_key": "new-key",
        "region": "global",
    }
    assert update.call_args.kwargs["options"] == {"speed": 1.5}


@pytest.mark.parametrize(
    "error,expected",
    [
        (MiniMaxAuthError("bad"), ConfigEntryAuthFailed),
        (MiniMaxError("network"), ConfigEntryNotReady),
    ],
)
async def test_setup_auth_and_retry(entry, error, expected):
    hass = MagicMock()
    with patch(
        "custom_components.minimax_tts.MiniMaxWebSocketClient.get_voices",
        new=AsyncMock(side_effect=error),
    ):
        with pytest.raises(expected):
            await async_setup_entry(hass, entry)
    hass.config_entries.async_forward_entry_setups.assert_not_called()


async def test_setup_unload_and_reload(entry):
    hass = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.config_entries.async_reload = AsyncMock()
    with patch(
        "custom_components.minimax_tts.MiniMaxWebSocketClient.get_voices",
        new=AsyncMock(return_value={"x": "Voice"}),
    ):
        assert await async_setup_entry(hass, entry)
    assert entry.runtime_data.voices == {"x": "Voice"}
    assert await async_unload_entry(hass, entry)
    await update_listener(hass, entry)
    hass.config_entries.async_reload.assert_awaited_once_with(entry.entry_id)


def test_legacy_language_label(entry):
    object.__setattr__(
        entry, "options", {"language": "Polish (Polski)", "model": "speech-02-hd"}
    )
    settings = settings_for_entry(entry)
    assert settings["language"] == "pl"
    assert settings["model"] == "speech-02-hd"
