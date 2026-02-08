from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    SelectSelector, 
    SelectSelectorConfig, 
    SelectSelectorMode,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode
)
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
    SUPPORTED_LANGUAGES,
    TTS_MODELS
)

LANGUAGE_OPTIONS = [
    {"label": name, "value": code} 
    for name, code in SUPPORTED_LANGUAGES.items()
]

class MiniMaxTTSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MiniMaxOptionsFlow()

    async def async_step_user(self, user_input=None):

        if user_input is not None:
            custom_title = user_input.get(CONF_TTS_NAME, "MiniMax TTS")
            return self.async_create_entry(
                title=custom_title,
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_TTS_NAME, default=CONF_DEFAULT_TTS_NAME): str,
                vol.Required(CONF_MODEL, default=CONF_DEFAULT_MODEL): vol.In(TTS_MODELS),
                vol.Required(CONF_VOICE_ID, default=CONF_DEFAULT_VOICE): str,
                vol.Required(CONF_LANGUAGE, default=CONF_DEFAULT_LANGUAGE): SelectSelector(
                    SelectSelectorConfig(
                        options=LANGUAGE_OPTIONS,
                        mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Required(CONF_SPEED, default=CONF_DEFAULT_SPEED): NumberSelector(
                    NumberSelectorConfig(min=0.5, max=2.0, step=0.1, mode=NumberSelectorMode.SLIDER)
                ),

                vol.Required(CONF_VOL, default=CONF_DEFAULT_VOL): NumberSelector(
                    NumberSelectorConfig(min=0.1, max=2.0, step=0.1, mode=NumberSelectorMode.SLIDER)
                ),

                vol.Required(CONF_PITCH, default=CONF_DEFAULT_PITCH): NumberSelector(
                    NumberSelectorConfig(min=-10, max=10, step=1, mode=NumberSelectorMode.SLIDER)
                ),

            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)


class MiniMaxOptionsFlow(config_entries.OptionsFlow):

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)


        api_key = self.config_entry.options.get(
            CONF_API_KEY, 
            self.config_entry.data.get(CONF_API_KEY, '')
        )

        tts_name = self.config_entry.options.get(
            CONF_TTS_NAME, 
            self.config_entry.data.get(CONF_TTS_NAME, CONF_DEFAULT_TTS_NAME)
        )

        model = self.config_entry.options.get(
            CONF_MODEL, 
            self.config_entry.data.get(CONF_MODEL, CONF_DEFAULT_MODEL)
        )

        voice_id = self.config_entry.options.get(
            CONF_VOICE_ID, 
            self.config_entry.data.get(CONF_VOICE_ID, CONF_DEFAULT_VOICE)
        )

        current_language = self.config_entry.options.get(
            CONF_LANGUAGE, 
            self.config_entry.data.get(CONF_LANGUAGE, CONF_DEFAULT_LANGUAGE)
        )
        current_speed = self.config_entry.options.get(
            CONF_SPEED, self.config_entry.data.get(CONF_SPEED, CONF_DEFAULT_SPEED)
        )
        current_vol = self.config_entry.options.get(
            CONF_VOL, self.config_entry.data.get(CONF_VOL, CONF_DEFAULT_VOL)
        )
        current_pitch = self.config_entry.options.get(
            CONF_PITCH, self.config_entry.data.get(CONF_PITCH, CONF_DEFAULT_PITCH)
        )

        options_schema = vol.Schema({
            vol.Required(CONF_API_KEY, default=api_key): str,
            vol.Required(CONF_TTS_NAME, default=tts_name): str,
            vol.Required(CONF_MODEL, default=model):  vol.In(TTS_MODELS),
            vol.Required(CONF_VOICE_ID, default=voice_id): str,
            vol.Required(
                CONF_LANGUAGE, 
                default=current_language
            ): SelectSelector(
                SelectSelectorConfig(
                    options=LANGUAGE_OPTIONS,
                    mode=SelectSelectorMode.DROPDOWN
                )
            ),
            vol.Required(CONF_SPEED, default=current_speed): NumberSelector(
                NumberSelectorConfig(min=0.5, max=2.0, step=0.1, mode=NumberSelectorMode.SLIDER)
            ),

            vol.Required(CONF_VOL, default=current_vol): NumberSelector(
                NumberSelectorConfig(min=0.1, max=2.0, step=0.1, mode=NumberSelectorMode.SLIDER)
            ),

            vol.Required(CONF_PITCH, default=current_pitch): NumberSelector(
                NumberSelectorConfig(min=-10, max=10, step=1, mode=NumberSelectorMode.SLIDER)
            ),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema
        )