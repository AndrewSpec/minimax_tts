import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.minimax_tts import websocket_client as module
from custom_components.minimax_tts.websocket_client import (
    MiniMaxAuthError,
    MiniMaxError,
    MiniMaxWebSocketClient,
)


def connection(responses):
    ws = AsyncMock()
    ws.receive.side_effect = [
        SimpleNamespace(type=aiohttp.WSMsgType.TEXT, data=json.dumps(item))
        if isinstance(item, (dict, list))
        else item
        for item in responses
    ]
    context = AsyncMock()
    context.__aenter__.return_value = ws
    session = MagicMock()
    session.ws_connect.return_value = context
    return MiniMaxWebSocketClient(session, "secret"), ws, context


def handshake():
    return [{"event": "connected_success"}, {"event": "task_started"}]


async def test_audio_and_final_chunk_are_combined():
    client, ws, context = connection(
        handshake()
        + [
            {"data": {"audio": "6162"}},
            {"data": {"audio": "6364"}, "is_final": True},
        ]
    )
    assert await client.synthesize("Hello", {"event": "task_start"}) == b"abcd"
    assert [call.args[0]["event"] for call in ws.send_json.call_args_list] == [
        "task_start",
        "task_continue",
        "task_finish",
    ]
    context.__aexit__.assert_awaited_once()


@pytest.mark.parametrize(
    "bad",
    [
        {"event": "task_failed", "base_resp": {"status_code": 1002}},
        {"base_resp": {"status_code": 2013}},
        {"data": {"audio": "not hex"}},
        {"event": "task_finished"},
        {"data": [], "is_final": True},
        SimpleNamespace(type=aiohttp.WSMsgType.CLOSED, data=None),
        SimpleNamespace(type=aiohttp.WSMsgType.ERROR, data=None),
        SimpleNamespace(type=aiohttp.WSMsgType.TEXT, data="not json"),
        [],
    ],
)
async def test_partial_audio_is_never_returned_as_success(bad):
    client, _, context = connection(handshake() + [{"data": {"audio": "61"}}, bad])
    with pytest.raises(MiniMaxError):
        await client.synthesize("Hello", {})
    context.__aexit__.assert_awaited_once()


async def test_auth_code_and_empty_audio():
    client, _, _ = connection([{"base_resp": {"status_code": 1004}}])
    with pytest.raises(MiniMaxAuthError):
        await client.synthesize("Hello", {})
    client, _, _ = connection(handshake() + [{"data": None, "is_final": True}])
    with pytest.raises(MiniMaxError, match="empty audio"):
        await client.synthesize("Hello", {})


async def test_segment_final_does_not_end_input_stream():
    client, ws, _ = connection(
        handshake()
        + [
            {"data": {"audio": "61"}, "is_final": True},
            {"data": {"audio": "62"}, "is_final": True},
        ]
    )

    async def texts():
        yield "One."
        yield "Two."

    assert b"".join([chunk async for chunk in client.stream(texts(), {})]) == b"ab"
    assert [
        call.args[0]["text"]
        for call in ws.send_json.call_args_list
        if "text" in call.args[0]
    ] == ["One.", "Two."]


async def test_generator_close_releases_socket():
    client, _, context = connection(handshake() + [{"data": {"audio": "61"}}])

    async def texts():
        yield "One."

    stream = client.stream(texts(), {})
    assert await anext(stream) == b"a"
    await stream.aclose()
    context.__aexit__.assert_awaited_once()


async def test_receive_timeout_and_cancellation_release_socket(monkeypatch):
    client, ws, context = connection([])
    ws.receive.side_effect = None

    async def hang():
        await asyncio.Event().wait()

    ws.receive.side_effect = hang
    monkeypatch.setattr(module, "RECEIVE_TIMEOUT", 0.01)
    with pytest.raises(MiniMaxError, match="timed out"):
        await client.synthesize("Hello", {})
    context.__aexit__.assert_awaited_once()
    monkeypatch.setattr(module, "RECEIVE_TIMEOUT", 60)
    task = asyncio.create_task(client.synthesize("Hello", {}))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert context.__aexit__.await_count == 2


@pytest.mark.parametrize("text", ["", "  ", "x" * 10001])
async def test_invalid_text_does_not_connect(text):
    client, _, _ = connection([])
    with pytest.raises(MiniMaxError):
        await client.synthesize(text, {})
    client._session.ws_connect.assert_not_called()


async def test_get_voices_all_categories_and_nulls():
    response = AsyncMock()
    response.status = 200
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "system_voice": [{"voice_id": "a", "voice_name": "System"}],
        "voice_cloning": [{"voice_id": "b"}],
        "voice_generation": None,
        "base_resp": {"status_code": 0},
    }
    context = AsyncMock()
    context.__aenter__.return_value = response
    session = MagicMock()
    session.post.return_value = context
    client = MiniMaxWebSocketClient(session, "secret")
    assert await client.get_voices() == {"a": "System", "b": "b"}
    response.status = 401
    with pytest.raises(MiniMaxAuthError):
        await client.get_voices()
