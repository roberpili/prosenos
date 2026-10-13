from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocket

import app.services.connection_manager as connection_module
from app.domain.enums import Sport
from app.services.connection_manager import ConnectionManager


def make_message():
    return {
        "type": "live_update",
        "sport": Sport.FUTBOL,
        "matches": [],
    }


@pytest.mark.asyncio
async def test_connect_without_last_state():
    manager = ConnectionManager()
    websocket = MagicMock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()

    await manager.connect(websocket)

    websocket.accept.assert_awaited_once()
    assert websocket in manager.active
    websocket.send_json.assert_not_awaited()


@pytest.mark.asyncio
async def test_connect_replays_last_state():
    manager = ConnectionManager()
    message = make_message()
    manager.last_state = message

    websocket = MagicMock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()

    await manager.connect(websocket)

    websocket.send_json.assert_awaited_once_with(message)
    assert websocket in manager.active


@pytest.mark.asyncio
async def test_connect_disconnects_on_replay_failure():
    manager = ConnectionManager()
    manager.last_state = make_message()

    websocket = MagicMock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock(side_effect=RuntimeError("closed"))

    await manager.connect(websocket)

    assert websocket not in manager.active


def test_disconnect_removes_known_websocket():
    manager = ConnectionManager()
    websocket = MagicMock(spec=WebSocket)

    manager.active.append(websocket)
    manager.disconnect(websocket)

    assert websocket not in manager.active


def test_disconnect_ignores_unknown_websocket():
    manager = ConnectionManager()
    websocket = MagicMock(spec=WebSocket)

    manager.disconnect(websocket)

    assert websocket not in manager.active


@pytest.mark.asyncio
async def test_send_returns_false_on_timeout(monkeypatch):
    manager = ConnectionManager()
    websocket = MagicMock(spec=WebSocket)
    websocket.send_json = MagicMock(return_value=None)
    monkeypatch.setattr(
        connection_module.asyncio, "wait_for", AsyncMock(side_effect=TimeoutError)
    )

    assert await manager._send(websocket, make_message()) is False


@pytest.mark.asyncio
async def test_broadcast_updates_last_state_and_disconnects_failures():
    manager = ConnectionManager()
    good = MagicMock(spec=WebSocket)
    good.send_json = AsyncMock()
    bad = MagicMock(spec=WebSocket)
    bad.send_json = AsyncMock(side_effect=RuntimeError("closed"))

    manager.active.extend([good, bad])
    message = make_message()

    await manager.broadcast(message)

    assert manager.last_state == message
    good.send_json.assert_awaited_once_with(message)
    bad.send_json.assert_awaited_once_with(message)
    assert good in manager.active
    assert bad not in manager.active


@pytest.mark.asyncio
async def test_broadcast_replays_to_new_client():
    manager = ConnectionManager()
    message = make_message()

    await manager.broadcast(message)

    websocket = MagicMock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()

    await manager.connect(websocket)

    websocket.send_json.assert_awaited_once_with(message)
