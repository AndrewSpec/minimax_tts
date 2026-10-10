"""MiniMax client with bounded requests and strict stream completion checks."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Any

import aiohttp

from .const import API_HOSTS

RECEIVE_TIMEOUT = 60
REQUEST_TIMEOUT = 300
MAX_TEXT_LENGTH = 10000


class MiniMaxError(Exception):
    """A safe error that contains neither API credentials nor submitted text."""


class MiniMaxAuthError(MiniMaxError):
    """Invalid API credentials."""


def check_response(response: Any) -> dict:
    if not isinstance(response, dict):
        raise MiniMaxError("Invalid API response")
    status = response.get("base_resp")
    if status is None:
        status = {}
    if not isinstance(status, dict):
        raise MiniMaxError("Invalid API status")
    code = status.get("status_code", 0)
    if code == 1004:
        raise MiniMaxAuthError("MiniMax authentication failed")
    if code or response.get("event") in {"task_failed", "task_error"}:
        # Do not include status_msg: upstream errors can echo submitted text.
        raise MiniMaxError(f"MiniMax request failed (code {code})")
    return response


class MiniMaxWebSocketClient:
    """Use Home Assistant's shared aiohttp session without closing it."""

    def __init__(
        self, session: aiohttp.ClientSession, api_key: str, region: str = "global"
    ) -> None:
        self._session = session
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._host = API_HOSTS[region]

    async def get_voices(self) -> dict[str, str]:
        """Validate credentials and fetch system, cloned and generated voices."""
        try:
            async with asyncio.timeout(30):
                async with self._session.post(
                    f"https://{self._host}/v1/get_voice",
                    headers=self._headers,
                    json={"voice_type": "all"},
                    allow_redirects=False,
                ) as response:
                    if response.status in (401, 403):
                        raise MiniMaxAuthError("MiniMax authentication failed")
                    response.raise_for_status()
                    data = check_response(await response.json())
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise MiniMaxError("Unable to retrieve MiniMax voices") from err
        voices = {}
        for group in ("system_voice", "voice_cloning", "voice_generation"):
            items = data.get(group) or []
            if not isinstance(items, list):
                raise MiniMaxError("Invalid voice list")
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("voice_id"), str):
                    voices[item["voice_id"]] = (
                        item.get("voice_name") or item["voice_id"]
                    )
        return voices

    async def _receive(self, ws: aiohttp.ClientWebSocketResponse) -> dict:
        async with asyncio.timeout(RECEIVE_TIMEOUT):
            message = await ws.receive()
        if message.type != aiohttp.WSMsgType.TEXT:
            raise MiniMaxError("MiniMax connection closed before completion")
        try:
            return check_response(json.loads(message.data))
        except (ValueError, TypeError) as err:
            raise MiniMaxError("Invalid MiniMax JSON response") from err

    async def stream(
        self, texts: AsyncIterator[str], payload: dict
    ) -> AsyncIterator[bytes]:
        """Stream each text segment on one connection, respecting backpressure.

        A final marker completes one segment, not the entire input stream.
        The context managers close the socket on cancellation or generator close.
        """
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.ws_connect(
                    f"wss://{self._host}/ws/v1/t2a_v2",
                    headers=self._headers,
                    max_msg_size=16 * 1024 * 1024,
                ) as ws:
                    if (await self._receive(ws)).get("event") != "connected_success":
                        raise MiniMaxError("Missing MiniMax connection acknowledgement")
                    await ws.send_json(payload)
                    if (await self._receive(ws)).get("event") != "task_started":
                        raise MiniMaxError("Missing MiniMax task acknowledgement")
                    sent_text = False
                    async for text in texts:
                        if not text.strip():
                            continue
                        if len(text) > MAX_TEXT_LENGTH:
                            raise MiniMaxError("Text segment exceeds 10000 characters")
                        sent_text = True
                        await ws.send_json({"event": "task_continue", "text": text})
                        received_audio = False
                        while True:
                            response = await self._receive(ws)
                            data = response.get("data")
                            if data is None:
                                data = {}
                            if not isinstance(data, dict):
                                raise MiniMaxError("Invalid MiniMax audio response")
                            if audio_hex := data.get("audio"):
                                try:
                                    audio = bytes.fromhex(audio_hex)
                                except (ValueError, TypeError) as err:
                                    raise MiniMaxError(
                                        "Invalid MiniMax audio encoding"
                                    ) from err
                                if audio:
                                    received_audio = True
                                    yield audio
                            if response.get("is_final") is True:
                                if not received_audio:
                                    raise MiniMaxError("MiniMax returned empty audio")
                                break
                            if response.get("event") == "task_finished":
                                raise MiniMaxError(
                                    "MiniMax finished before completing the text"
                                )
                    if not sent_text:
                        raise MiniMaxError("No text to synthesize")
                    await ws.send_json({"event": "task_finish"})
        except aiohttp.WSServerHandshakeError as err:
            if err.status in (401, 403):
                raise MiniMaxAuthError("MiniMax authentication failed") from err
            raise MiniMaxError("MiniMax WebSocket handshake failed") from err
        except (aiohttp.ClientError, TimeoutError) as err:
            raise MiniMaxError("MiniMax connection failed or timed out") from err

    async def synthesize(self, text: str, payload: dict) -> bytes:
        """Return audio only when the entire response is valid and complete."""
        if not text.strip() or len(text) > MAX_TEXT_LENGTH:
            raise MiniMaxError("Text must contain between 1 and 10000 characters")

        async def messages():
            yield text

        async with aclosing(self.stream(messages(), payload)) as stream:
            return b"".join([chunk async for chunk in stream])
