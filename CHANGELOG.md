# Changelog

## 1.1.0

Requires Home Assistant 2026.10.0 or newer.

### Fixed
- Send selected language to MiniMax and honor per-call `tts.speak` options.
- Follow WebSocket connection/task acknowledgements and handle `task_failed`
  and nonzero `base_resp.status_code` on every frame.
- Reject empty, malformed and incomplete audio instead of returning partial success.
- Bound network waits and close WebSockets on cancellation.
- Avoid repeatedly copying the entire audio buffer for every chunk.
- Restrict unsupported language/model and emotion/model combinations.
- Correct integration metadata and provide complete English/Polish form labels.

### Added
- Assist streaming text/audio and voice discovery, including custom voices.
- Credential validation, setup retry, reauthentication and masked key input.
- API region, emotions, normalization, MP3 quality and full volume/pitch ranges.
- Per-message pronunciation dictionary and voice effects.
- HA device information and diagnostics with an explicit non-sensitive allowlist.
- Regression tests, CI for lint/tests, hassfest and HACS, and usage documentation.

### Compatibility
- Existing entry/unique IDs and saved settings are preserved.
- Default model for new entries is speech-2.8-hd; existing models are unchanged.
- Output remains MP3. No API synthesis calls were made during local tests.
