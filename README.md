# MiniMax TTS for Home Assistant

Custom Home Assistant text-to-speech integration using MiniMax's WebSocket API.
Install through HACS as a custom repository. Version 1.1 requires **Home Assistant
2026.10.0 or newer**; the automated tests run against 2026.10.0.

## Features

- `tts.speak`, Home Assistant's audio cache, media players and Assist pipelines.
- Streaming text input and audio output for Assist: synthesis starts after a
  sentence arrives, without waiting for the entire LLM response. Playback latency
  also depends on the player/satellite and Home Assistant's audio processing.
- System, cloned and generated voices from your account, exposed to Assist and
  the integration's options. Custom voice IDs remain accepted.
- Per-message voice, model, speed, volume, pitch, emotion, English normalization,
  audio quality, pronunciation dictionary and voice effects.
- Language selection is sent as MiniMax `language_boost`, including Polish and
  automatic detection. Older speech-02 models exclude Persian, Filipino and Tamil.
- Credential validation, reauthentication, setup retries, timeouts and diagnostics
  without API keys, custom voice IDs or spoken text.
- Multiple independent entries, for example different default voices or models.

## Installation and upgrade

1. In HACS, open **Custom repositories** from the menu.
2. Add `https://github.com/AndrewSpec/minimax_tts`, category **Integration**.
3. Download MiniMax TTS and restart Home Assistant.
4. Open **Settings → Devices & services → Add integration → MiniMax TTS**.
5. Enter your API key, account region and voice ID. The key is checked using
   `get_voice`; setup does not generate a billable TTS sample.
6. After setup, open **Configure** to select a voice from the account's list.
   Reload the integration after creating new voices to refresh that list.

Get a key from the [MiniMax console](https://platform.minimax.io/user-center/basic-information/interface-key).
Copy a voice ID from the MiniMax Audio voice menu. Choose `global` for
`api.minimax.io`, or `china` for an account on `api.minimaxi.com`.

When upgrading from 1.0, existing entry IDs, entity unique IDs, voice, model and
other saved settings are retained. Existing entries are not switched to a new
model. New entries default to `speech-2.8-hd`. If authentication fails, Home
Assistant offers a reauthentication form; the integration also handles keys that
older versions saved in options. Settings changes reload the integration.

The repository root is the directory containing this README, `hacs.json` and
`custom_components/`. Publish that directory's contents, without an extra outer
`minimax_tts/` folder. Releases are optional; HACS can use the default branch.

## Usage

Replace the entity IDs with those from your installation:

```yaml
action: tts.speak
target:
  entity_id: tts.minimax_audio_tts
data:
  media_player_entity_id: media_player.salon
  message: "Pralka skończyła pracę."
  language: pl
  cache: true
  options:
    voice: English_MaturePartner
    model: speech-2.8-turbo
    speed: 1.05
    vol: 1.0
    pitch: 0
    emotion: happy
```

`voice` is the standard Home Assistant per-message option; the integration's
configuration field is named `voice_id`. Omitted options use the configured
values. Default synthesis options participate in HA's cache key, so changing a
voice or model does not reuse audio generated with the old settings.

To use Assist, select the MiniMax TTS entity, language and voice in the voice
assistant's text-to-speech settings. Incoming partial words are buffered into
sentences and sent sequentially over one WebSocket connection. Cancelling the
stream closes the connection.

## Models and options

Supported models: `speech-2.8-hd`, `speech-2.8-turbo`, `speech-2.6-hd`,
`speech-2.6-turbo`, `speech-02-hd`, `speech-02-turbo`.

| `tts.speak` option | Values | Default for new entries |
| --- | --- | --- |
| `voice` | System, cloned or generated voice ID | `English_MaturePartner` |
| `model` | One of the models above | `speech-2.8-hd` |
| `speed` | 0.5–2.0 | 1.0 |
| `vol` | Greater than 0, up to 10 | 1.0 |
| `pitch` | Integer, −12 to 12 | 0 |
| `emotion` | `auto`, `happy`, `sad`, `angry`, `fearful`, `disgusted`, `surprised`, `calm`, `fluent`, `whisper` | `auto` |
| `english_normalization` | Boolean | false |
| `sample_rate` | 8000, 16000, 22050, 24000, 32000, 44100 Hz | 32000 |
| `bitrate` | 32000, 64000, 128000, 256000 bit/s | 128000 |
| `channel` | 1 (mono), 2 (stereo) | 1 |
| `pronunciation_dict` | Mapping with a `tone` list | Omitted |
| `voice_modify` | Mapping with effects below | Omitted |

`fluent` and `whisper` are restricted to speech-2.6 models, following the documented
API restrictions. `auto` omits the emotion field and lets MiniMax choose.
The form supports volume from 0.01 to 10; YAML accepts any positive value up to 10.

Advanced options are supplied per message:

```yaml
options:
  pronunciation_dict:
    tone:
      - "HA/Home Assistant"
  voice_modify:
    pitch: 0
    intensity: 10
    timbre: -10
    sound_effects: lofi_telephone
```

Voice-effect `pitch`, `intensity` and `timbre` accept integers from −100 to 100;
they are separate from the normal pitch control. `sound_effects` can be
`spacious_echo`, `auditorium_echo`, `lofi_telephone` or `robotic`.

Text can contain MiniMax pause markers, for example
`"Uwaga. <#0.5#> Drzwi są otwarte."`. Speech-2.8 also supports interjections such as
`(laughs)` and `(sighs)`. These are MiniMax text controls, not SSML.

## Limits and troubleshooting

- Output is MP3 for compatibility with media players and streaming voice effects.
  HA's `preferred_format` and other `preferred_*` options can request downstream
  transcoding; they do not change the MiniMax output format.
- A one-shot request accepts up to 10,000 characters. Streaming input is split
  into segments of at most 8,000 characters, preferably at sentence/word boundaries.
  A request has a 5-minute deadline and waits at most 60 seconds for an API frame.
- Interrupted, malformed and empty responses raise an error. One-shot synthesis
  never returns partial audio as a successful result. Already played streaming
  audio cannot be recalled if a later segment fails.
- Requests are not automatically repeated after synthesis starts, avoiding
  accidental duplicate billing. API errors include their numeric status code.
- The voice-list endpoint must be available at setup. Temporary failures trigger
  Home Assistant's setup retry; invalid credentials trigger reauthentication.
- Diagnostics contain only synthesis settings and the voice count. No credentials
  or spoken messages are logged by this integration.
- Cloning/designing voices, uploading files, subtitle export, voice mixing and
  long-form asynchronous synthesis are outside this TTS integration. Existing
  cloned/designed voices can be used by ID. Manage them in MiniMax's console.

## Development

```sh
python3.14 -m venv .venv
. .venv/bin/activate
pip install -r requirements-test.txt
pytest -q
ruff check .
ruff format --check .
```

Tests use real Home Assistant classes and mocked API transport. They cover audio
completion, failures, cancellation, language/options, streaming, setup, options
and credential recovery. They do **not** replace a live API/player smoke test.
GitHub Actions also runs HACS validation and hassfest after the changes are pushed.

## API references

- [MiniMax WebSocket TTS](https://platform.minimax.io/docs/api-reference/speech-t2a-websocket)
- [MiniMax voice list](https://platform.minimax.io/docs/api-reference/voice-management-get)
- [Home Assistant TTS entities](https://developers.home-assistant.io/docs/core/entity/tts/)
- [HACS integration requirements](https://www.hacs.xyz/docs/publish/integration/)

## Support My Work

If you find this integration useful, you can support my work by buying me a coffee:

<a href="https://buycoffee.to/andrewspec" target="_blank"><img src="https://buycoffee.to/static/img/share/share-button-primary.png" style="width: 351px; height: 92px" alt="Buy me a coffee on buycoffee.to"></a>
