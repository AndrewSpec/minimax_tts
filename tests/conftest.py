"""Use real HA classes; replace only external HTTP/WebSocket transport."""

from types import MappingProxyType
from unittest.mock import AsyncMock

import pytest
from homeassistant.config_entries import ConfigEntry

from custom_components.minimax_tts import MiniMaxRuntimeData
from custom_components.minimax_tts.const import DEFAULTS


@pytest.fixture
def entry():
    entry = ConfigEntry(
        domain="minimax_tts",
        title="MiniMax",
        version=1,
        minor_version=1,
        data=DEFAULTS | {"api_key": "secret", "language": "pl"},
        options={},
        source="user",
        unique_id=None,
        discovery_keys=MappingProxyType({}),
        subentries_data=[],
    )
    entry.runtime_data = MiniMaxRuntimeData(AsyncMock(), {"custom": "My voice"})
    return entry
