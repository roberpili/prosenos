from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

import app.services.futbol as futbol_service
from app.domain.enums import Sport
from app.domain.schemas.game import FutbolScraperGame
from app.domain.schemas.match import FutbolMatch


def make_match(**overrides):
    defaults = {
        "id": "1",
        "home_team": "Boca",
        "away_team": "River",
        "home_score": 1,
        "away_score": 0,
        "status": "finished",
        "kickoff": None,
        "league": "Libertadores",
        "minute": 5,
        "agg_home_score": None,
        "agg_away_score": None,
        "home_penalties": None,
        "away_penalties": None,
        "qualifies": None,
        "home_scorers": [],
        "away_scorers": [],
    }
    return FutbolMatch(**dict(defaults, **overrides))


def make_game(**overrides):
    defaults = {
        "id": "1",
        "league": "Libertadores",
        "home_team": "Boca",
        "away_team": "River",
        "home_score": 1,
        "away_score": 0,
        "status": "finished",
        "minute": 5,
        "kickoff": None,
    }
    return FutbolScraperGame(**dict(defaults, **overrides))


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


@pytest.mark.asyncio
async def test_get_futbol_matches_resolves_date_and_maps_results(monkeypatch):
    target = date(2026, 10, 9)
    raw = [MagicMock(), MagicMock()]

    monkeypatch.setattr(futbol_service, "resolve_date", MagicMock(return_value=target))
    monkeypatch.setattr(
        futbol_service, "get_futbol_matches_by_date", MagicMock(return_value=raw)
    )
    monkeypatch.setattr(
        futbol_service, "_to_futbol_scraper_game", lambda match: f"game-{id(match)}"
    )

    result = await futbol_service.get_futbol_matches("today")

    futbol_service.resolve_date.assert_called_once_with("today")
    futbol_service.get_futbol_matches_by_date.assert_called_once_with(target)
    assert result == [f"game-{id(match)}" for match in raw]


@pytest.mark.asyncio
async def test_get_futbol_matches_empty(monkeypatch):
    monkeypatch.setattr(futbol_service, "resolve_date", lambda _: date(2026, 10, 9))
    monkeypatch.setattr(futbol_service, "get_futbol_matches_by_date", lambda _: [])

    assert await futbol_service.get_futbol_matches("today") == []


@pytest.mark.asyncio
async def test_get_futbol_matches_propagates_resolve_errors(monkeypatch):
    def boom(_):
        raise ValueError("bad day")

    monkeypatch.setattr(futbol_service, "resolve_date", boom)

    with pytest.raises(ValueError):
        await futbol_service.get_futbol_matches("garbage")


@pytest.mark.asyncio
async def test_get_futbol_matches_invalid_day_raises_http_exception():
    with pytest.raises(HTTPException) as exc_info:
        await futbol_service.get_futbol_matches("not-a-date")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_futbol_matches_raises_when_scraper_fails(monkeypatch):
    monkeypatch.setattr(
        futbol_service, "resolve_date", MagicMock(return_value=date(2026, 10, 9))
    )
    monkeypatch.setattr(
        futbol_service,
        "get_futbol_matches_by_date",
        MagicMock(side_effect=ConnectionError("Scraper down")),
    )

    with pytest.raises(ConnectionError, match="Scraper down"):
        await futbol_service.get_futbol_matches("today")


@pytest.mark.asyncio
async def test_conversion_preserves_fields():
    match = make_match(home_scorers=["(P) Player 5'"], qualifies="home")

    game = futbol_service._to_futbol_scraper_game(match)

    assert game.id == match.id
    assert game.league == match.league
    assert game.home_team == match.home_team
    assert game.away_team == match.away_team
    assert game.home_score == match.home_score
    assert game.away_score == match.away_score
    assert game.status == match.status
    assert game.minute == match.minute
    assert game.kickoff == (match.kickoff.isoformat() if match.kickoff else None)
    assert game.agg_home_score == match.agg_home_score
    assert game.agg_away_score == match.agg_away_score
    assert game.home_penalties == match.home_penalties
    assert game.away_penalties == match.away_penalties
    assert game.home_scorers == match.home_scorers
    assert game.away_scorers == match.away_scorers


@pytest.mark.asyncio
async def test_poll_live_futbol_matches_delegates_to_poller(monkeypatch):
    captured = {}

    async def fake_poll_live(sport, fetch):
        captured["sport"] = sport
        await fetch()

    monkeypatch.setattr(futbol_service, "poll_live", fake_poll_live)
    monkeypatch.setattr(
        futbol_service, "get_futbol_matches", AsyncMock(return_value=[])
    )

    await futbol_service.poll_live_futbol_matches()

    assert captured["sport"] == Sport.FUTBOL
