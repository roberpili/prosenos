import asyncio
from unittest.mock import AsyncMock

import pytest
from curl_cffi.requests.exceptions import RequestException, Timeout

from app.domain.enums import Sport
from app.domain.schemas.game import FutbolScraperGame
from app.services import poller


class StopLoop(Exception):
    pass


def stop_after(n: int):
    calls = 0

    async def fake_sleep(_: float) -> None:
        nonlocal calls
        calls += 1
        if calls >= n:
            raise StopLoop

    return fake_sleep


def make_game(**overrides):
    defaults = {
        "id": "1",
        "league": "L",
        "home_team": "A",
        "away_team": "B",
        "home_score": 0,
        "away_score": 0,
        "status": "live",
        "minute": 1,
        "kickoff": None,
    }
    return FutbolScraperGame(**dict(defaults, **overrides))


@pytest.fixture
def broadcast(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(poller.manager, "broadcast", mock)
    return mock


def test_broadcasts_only_when_data_changes(monkeypatch, broadcast):
    g1 = make_game(home_score=0, away_score=0, status="live")
    g2 = make_game(home_score=1, away_score=0, status="live")

    fetch = AsyncMock(side_effect=[[g1], [g1], [g2]])
    monkeypatch.setattr(poller.asyncio, "sleep", stop_after(3))

    with pytest.raises(StopLoop):
        asyncio.run(poller.poll_live(Sport.FUTBOL, fetch))

    assert broadcast.await_count == 2
    first, second = (call.args[0] for call in broadcast.await_args_list)
    assert first == {
        "type": "live_update",
        "sport": Sport.FUTBOL,
        "matches": [g1.model_dump(mode="json")],
    }
    assert second["matches"] == [g2.model_dump(mode="json")]


def test_first_poll_with_empty_result_does_not_broadcast(monkeypatch, broadcast):
    fetch = AsyncMock(return_value=[])
    monkeypatch.setattr(poller.asyncio, "sleep", stop_after(2))

    with pytest.raises(StopLoop):
        asyncio.run(poller.poll_live(Sport.FUTBOL, fetch))

    broadcast.assert_not_awaited()


def test_loop_survives_exceptions(monkeypatch, broadcast, caplog):
    game = make_game()

    fetch = AsyncMock(side_effect=[RuntimeError("scrape failed"), [game]])
    monkeypatch.setattr(poller.asyncio, "sleep", stop_after(2))

    with pytest.raises(StopLoop):
        asyncio.run(poller.poll_live(Sport.FUTBOL, fetch))

    assert "live poll failed" in caplog.text
    broadcast.assert_awaited_once()


def test_failed_broadcast_is_retried_next_tick(monkeypatch, broadcast):
    game = make_game()
    failing_broadcast = AsyncMock(side_effect=[ConnectionError, None])
    monkeypatch.setattr(poller.manager, "broadcast", failing_broadcast)
    fetch = AsyncMock(return_value=[game])
    monkeypatch.setattr(poller.asyncio, "sleep", stop_after(2))

    with pytest.raises(StopLoop):
        asyncio.run(poller.poll_live(Sport.FUTBOL, fetch))

    assert failing_broadcast.await_count == 2


def test_timeout_is_handled_and_poll_continues(monkeypatch, broadcast, caplog):
    game = make_game()

    fetch = AsyncMock(side_effect=[Timeout("slow"), [game]])
    monkeypatch.setattr(poller.asyncio, "sleep", stop_after(2))

    with pytest.raises(StopLoop):
        asyncio.run(poller.poll_live(Sport.FUTBOL, fetch))

    assert "timeout getting live matches" in caplog.text
    broadcast.assert_awaited_once()


def test_request_exception_is_handled_and_poll_continues(
    monkeypatch, broadcast, caplog
):
    game = make_game()

    fetch = AsyncMock(side_effect=[RequestException("network"), [game]])
    monkeypatch.setattr(poller.asyncio, "sleep", stop_after(2))

    with pytest.raises(StopLoop):
        asyncio.run(poller.poll_live(Sport.FUTBOL, fetch))

    assert "red/curl error polling" in caplog.text
    broadcast.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancelled_error_propagates(monkeypatch):
    fetch = AsyncMock(side_effect=[asyncio.CancelledError()])
    monkeypatch.setattr(poller.asyncio, "sleep", stop_after(1))

    with pytest.raises(asyncio.CancelledError):
        await poller.poll_live(Sport.FUTBOL, fetch)
