import json
import logging
import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

class MiniMaxWebSocketClient:
    def __init__(self, hass, api_key: str, model: str, voice: str, language: str, speed: float, vol: float, pitch: int):
        self._hass = hass
        self._api_key = api_key
        self._voice = voice
        self._model = model
        self._language = language
        self._file_format = "mp3"
        self._speed = speed
        self._vol = vol
        self._pitch = pitch
        self._url = "wss://api.minimax.io/ws/v1/t2a_v2"

    async def synthesize(self, text: str) -> bytes:

        session = async_get_clientsession(self._hass)
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        full_audio_bytes = b""

        try:
            async with session.ws_connect(self._url, headers=headers) as ws:
                _LOGGER.debug("Connected to MiniMax WebSocket")

                start_payload = {
                    "event": "task_start",
                    "model": self._model,
                    "voice_setting": {
                        "voice_id": self._voice,
                        "speed": self._speed,
                        "vol": self._vol,
                        "pitch": int(self._pitch),
                        "english_normalization": False
                    },
                    "audio_setting": {
                        "sample_rate": 32000,
                        "bitrate": 128000,
                        "format": self._file_format,
                        "channel": 1,
                    }
                }
                await ws.send_json(start_payload)
                _LOGGER.debug("Wysłano task_start: %s", start_payload)

                is_started = False
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            resp = json.loads(msg.data)
                            event = resp.get("event")
                            
                            if event == "task_started":
                                _LOGGER.debug("Confirmed task_started")
                                is_started = True
                                break
                            
                            if event == "task_error":
                                _LOGGER.error("API error: %s", resp)
                                return None
                        except ValueError:
                            continue
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        _LOGGER.error("WebSocket error during task_start: %s", msg.data)
                        return None

                if not is_started:
                    _LOGGER.error("Could not start sesion (missing task_started)")
                    return None

                continue_payload = {
                    "event": "task_continue",
                    "text": text
                }
                await ws.send_json(continue_payload)
                _LOGGER.debug("Text send (task_continue)")

                finish_payload = {"event": "task_finish"}
                await ws.send_json(finish_payload)

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                        except ValueError:
                            continue

                        if data.get("event") == "task_error":
                            _LOGGER.error("API error: %s", data)
                            break

                        if "data" in data and "audio" in data["data"]:
                            audio_hex = data["data"]["audio"]
                            if audio_hex:
                                chunk = bytes.fromhex(audio_hex)
                                full_audio_bytes += chunk

                        if data.get("is_final") or data.get("event") == "task_finished":
                            _LOGGER.debug("End of audio stream")
                            break

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        _LOGGER.error("WebSocket connection error while downloading audio")
                        break

        except Exception as e:
            _LOGGER.exception("Critical exception in client: %s", e)
            return None

        if not full_audio_bytes:
            _LOGGER.warning("Recieved empty audio data")
            return None

        return full_audio_bytes