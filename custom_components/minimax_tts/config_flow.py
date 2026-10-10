"""Configuration, options and credential recovery for MiniMax TTS."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    API_HOSTS,
    BITRATES,
    DEFAULTS,
    DOMAIN,
    EMOTIONS,
    SAMPLE_RATES,
    SUPPORTED_LANGUAGES,
    TTS_MODELS,
)
from .settings import build_payload, default_options, nonempty, settings_for_entry
from .websocket_client import MiniMaxAuthError, MiniMaxError, MiniMaxWebSocketClient


def select(options, custom=False):
    return SelectSelector(
        SelectSelectorConfig(
            options=options,
            mode=SelectSelectorMode.DROPDOWN,
            custom_value=custom,
        )
    )


def schema(values, voices=None, credentials=True):
    fields = {}
    if credentials:
        fields[vol.Required("api_key", default=values.get("api_key", ""))] = (
            TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
        )
        fields[vol.Required("region", default=values["region"])] = select(
            list(API_HOSTS)
        )
    fields.update(
        {
            vol.Required("name", default=values["name"]): str,
            vol.Required("model", default=values["model"]): select(TTS_MODELS),
            vol.Required("voice_id", default=values["voice_id"]): select(
                [
                    {"value": key, "label": f"{label} ({key})"}
                    for key, label in (voices or {}).items()
                ],
                True,
            )
            if voices
            else str,
            vol.Required("language", default=values["language"]): select(
                [
                    {"label": name, "value": code}
                    for name, code in SUPPORTED_LANGUAGES.items()
                ]
            ),
            vol.Required("emotion", default=values["emotion"]): select(EMOTIONS),
            vol.Required(
                "english_normalization", default=values["english_normalization"]
            ): BooleanSelector(),
        }
    )
    for key, minimum, maximum, step in (
        ("speed", 0.5, 2, 0.05),
        ("vol", 0.01, 10, 0.01),
        ("pitch", -12, 12, 1),
    ):
        fields[vol.Required(key, default=values[key])] = NumberSelector(
            NumberSelectorConfig(
                min=minimum,
                max=maximum,
                step=step,
                mode=NumberSelectorMode.BOX,
            )
        )
    for key, choices in (
        ("sample_rate", SAMPLE_RATES),
        ("bitrate", BITRATES),
        ("channel", [1, 2]),
    ):
        fields[vol.Required(key, default=str(values[key]))] = select(
            [str(value) for value in choices]
        )
    return vol.Schema(fields)


def normalize(user_input):
    values = dict(user_input)
    for key in ("api_key", "name", "voice_id"):
        if key in values:
            values[key] = nonempty(values[key])
    for key in ("sample_rate", "bitrate", "channel"):
        if key in values:
            values[key] = int(values[key])
    return values


async def validate(hass, values):
    build_payload(values["language"], default_options(values))
    client = MiniMaxWebSocketClient(
        async_get_clientsession(hass), values["api_key"], values["region"]
    )
    return await client.get_voices()


class MiniMaxTTSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MiniMaxOptionsFlow()

    async def async_step_user(self, user_input=None):
        errors = {}
        values = DEFAULTS.copy()
        if user_input is not None:
            values.update(user_input)
            try:
                values = normalize(values)
                await validate(self.hass, values)
            except MiniMaxAuthError:
                errors["base"] = "invalid_auth"
            except MiniMaxError:
                errors["base"] = "cannot_connect"
            except vol.Invalid, ValueError:
                errors["base"] = "invalid_settings"
            else:
                return self.async_create_entry(title=values["name"], data=values)
        return self.async_show_form(
            step_id="user", data_schema=schema(values), errors=errors
        )

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        entry = self._get_reauth_entry()
        values = settings_for_entry(entry)
        errors = {}
        if user_input is not None:
            try:
                values.update(normalize(user_input))
                # Credential repair must not be blocked by unrelated legacy settings.
                client = MiniMaxWebSocketClient(
                    async_get_clientsession(self.hass),
                    values["api_key"],
                    values["region"],
                )
                await client.get_voices()
            except MiniMaxAuthError:
                errors["base"] = "invalid_auth"
            except MiniMaxError:
                errors["base"] = "cannot_connect"
            except vol.Invalid:
                errors["base"] = "invalid_settings"
            else:
                # Older versions stored keys in options, which override entry.data.
                options = {
                    key: value
                    for key, value in entry.options.items()
                    if key not in {"api_key", "region"}
                }
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        "api_key": values["api_key"],
                        "region": values["region"],
                    },
                    options=options,
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required("api_key"): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                    vol.Required("region", default=values["region"]): select(
                        list(API_HOSTS)
                    ),
                }
            ),
        )


class MiniMaxOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        values = settings_for_entry(self.config_entry)
        errors = {}
        if user_input is not None:
            values.update(user_input)
            try:
                values = normalize(values)
                await validate(self.hass, values)
            except MiniMaxAuthError:
                errors["base"] = "invalid_auth"
            except MiniMaxError:
                errors["base"] = "cannot_connect"
            except vol.Invalid, ValueError:
                errors["base"] = "invalid_settings"
            else:
                return self.async_create_entry(title="", data=values)
        runtime = getattr(self.config_entry, "runtime_data", None)
        return self.async_show_form(
            step_id="init",
            data_schema=schema(values, runtime.voices if runtime else None),
            errors=errors,
        )
