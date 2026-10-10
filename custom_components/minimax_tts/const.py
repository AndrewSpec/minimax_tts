DOMAIN = "minimax_tts"

CONF_API_KEY = "api_key"
CONF_MODEL = "model"
CONF_VOICE_ID = "voice_id"
CONF_TTS_NAME = "name"
CONF_SPEED = "speed"
CONF_VOL = "vol"
CONF_PITCH = "pitch"
CONF_LANGUAGE = "language"

CONF_DEFAULT_VOICE = "English_MaturePartner"
CONF_DEFAULT_MODEL = "speech-02-hd"
CONF_DEFAULT_TTS_NAME = "MiniMax Audio TTS"
CONF_DEFAULT_LANGUAGE = "en"
CONF_DEFAULT_SPEED = 1.0
CONF_DEFAULT_VOL = 1.0
CONF_DEFAULT_PITCH = 0

SUPPORTED_LANGUAGES = {
    "Afrikaans (Afrikaans)": "af",
    "Arabic (العربية)": "ar",
    "Bulgarian (Български)": "bg",
    "Cantonese (粵語)": "yue",
    "Catalan (Català)": "ca",
    "Chinese (中文)": "zh",
    "Croatian (Hrvatski)": "hr",
    "Czech (Čeština)": "cs",
    "Danish (Dansk)": "da",
    "Dutch (Nederlands)": "nl",
    "English (English)": "en",
    "Filipino (Tagalog)": "tl",
    "Finnish (Suomi)": "fi",
    "French (Français)": "fr",
    "German (Deutsch)": "de",
    "Greek (Ελληνικά)": "el",
    "Hebrew (עברית)": "he",
    "Hindi (हिन्दी)": "hi",
    "Hungarian (Magyar)": "hu",
    "Indonesian (Bahasa Indonesia)": "id",
    "Italian (Italiano)": "it",
    "Japanese (日本語)": "ja",
    "Korean (한국어)": "ko",
    "Malay (Bahasa Melayu)": "ms",
    "Norwegian (Norsk)": "no",
    "Norwegian Nynorsk (Norsk Nynorsk)": "nn",
    "Persian (فارسی)": "fa",
    "Polish (Polski)": "pl",
    "Portuguese (Português)": "pt",
    "Romanian (Română)": "ro",
    "Russian (Русский)": "ru",
    "Slovak (Slovenčina)": "sk",
    "Slovenian (Slovenščina)": "sl",
    "Spanish (Español)": "es",
    "Swedish (Svenska)": "sv",
    "Tamil (தமிழ்)": "ta",
    "Thai (ไทย)": "th",
    "Turkish (Türkçe)": "tr",
    "Ukrainian (Українська)": "uk",
    "Vietnamese (Tiếng Việt)": "vi",
}


TTS_MODELS = [
    "speech-2.8-hd",
    "speech-2.6-hd",
    "speech-2.8-turbo",
    "speech-2.6-turbo",
    "speech-02-hd",
    "speech-02-turbo",
]
# API language names are not ISO language codes.
LANGUAGE_BOOST = {
    code: name.split(" (")[0] for name, code in SUPPORTED_LANGUAGES.items()
}
LANGUAGE_BOOST.update({"yue": "Chinese,Yue", "nn": "Nynorsk", "auto": "auto"})
SUPPORTED_LANGUAGES["Auto-detect"] = "auto"
LEGACY_UNSUPPORTED_LANGUAGES = {"fa", "tl", "ta"}

CONF_REGION = "region"
API_HOSTS = {"global": "api.minimax.io", "china": "api.minimaxi.com"}
EMOTIONS = [
    "auto",
    "happy",
    "sad",
    "angry",
    "fearful",
    "disgusted",
    "surprised",
    "calm",
    "fluent",
    "whisper",
]
SAMPLE_RATES = [8000, 16000, 22050, 24000, 32000, 44100]
BITRATES = [32000, 64000, 128000, 256000]
SOUND_EFFECTS = ["spacious_echo", "auditorium_echo", "lofi_telephone", "robotic"]
DEFAULTS = {
    CONF_TTS_NAME: CONF_DEFAULT_TTS_NAME,
    CONF_MODEL: "speech-2.8-hd",
    CONF_VOICE_ID: CONF_DEFAULT_VOICE,
    CONF_LANGUAGE: CONF_DEFAULT_LANGUAGE,
    CONF_SPEED: CONF_DEFAULT_SPEED,
    CONF_VOL: CONF_DEFAULT_VOL,
    CONF_PITCH: CONF_DEFAULT_PITCH,
    CONF_REGION: "global",
    "emotion": "auto",
    "english_normalization": False,
    "sample_rate": 32000,
    "bitrate": 128000,
    "channel": 1,
}
