from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

import app.services.nba as nba_service
from app.domain.enums import Sport
from app.domain.schemas.game import NBAScraperGame
from app.domain.schemas.match import NBAMatch


def make_match(**overrides):
    defaults = {
        "id": "1",
        "home_team": "Hawks",
        "away_team": "Celtics",
        "home_score": 100,
        "away_score": 98,
        "status": "live",
        "kickoff": None,
        "confederation": "East",
        "clock": "10:00",
        "season_status": "regular",
        "overtime": False,
        "quarter": 2,
        "agg_home_games": 1,
        "agg_away_games": 0,
    }
    return NBAMatch(**dict(defaults, **overrides))


def make_game(**overrides):
    defaults = {
        "id": "1",
        "confederation": "East",
        "season_staus": "regular",
        "home_team": "Hawks",
        "away_team": "Celtics",
        "home_score": 100,
        "away_score": 98,
        "status": "live",
        "quarter": 2,
        "kickoff": None,
    }
    return NBAScraperGame(**dict(defaults, **overrides))


def test_resolve_date_today():
    resolved = nba_service._resolve_date("today")

    assert resolved == datetime.now(UTC).date()


def test_resolve_date_yesterday():
    resolved = nba_service._resolve_date("yesterday")

    assert resolved == datetime.now(UTC).date() - timedelta(days=1)


def test_resolve_date_explicit_hyphenated():
    assert nba_service._resolve_date("06-07-2026") == date(2026, 7, 6)


def test_resolve_date_explicit_slashed():
    assert nba_service._resolve_date("06/07/2026") == date(2026, 7, 6)


def test_resolve_date_invalid_raises_http_exception():
    for value in ("garbage", "06.07.2026", "2026-07-06"):
        with pytest.raises(HTTPException) as exc_info:
            nba_service._resolve_date(value)
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_nba_matches_resolves_date_and_maps_results(monkeypatch):
    target = date(2026, 10, 9)
    raw = [MagicMock(), MagicMock()]

    monkeypatch.setattr(nba_service, "_resolve_date", MagicMock(return_value=target))
    monkeypatch.setattr(
        nba_service, "get_nba_matches_by_date", MagicMock(return_value=raw)
    )
    monkeypatch.setattr(
        nba_service, "_to_nba_scraper_game", lambda match: f"game-{id(match)}"
    )

    result = await nba_service.get_nba_matches("today")

    nba_service._resolve_date.assert_called_once_with("today")
    nba_service.get_nba_matches_by_date.assert_called_once_with(target)
    assert result == [f"game-{id(match)}" for match in raw]


@pytest.mark.asyncio
async def test_get_nba_matches_empty(monkeypatch):
    monkeypatch.setattr(nba_service, "_resolve_date", lambda _: date(2026, 10, 9))
    monkeypatch.setattr(nba_service, "get_nba_matches_by_date", lambda _: [])

    assert await nba_service.get_nba_matches("today") == []


@pytest.mark.asyncio
async def test_get_nba_matches_raises_when_scraper_fails(monkeypatch):
    monkeypatch.setattr(
        nba_service, "_resolve_date", MagicMock(return_value=date(2026, 10, 9))
    )
    monkeypatch.setattr(
        nba_service,
        "get_nba_matches_by_date",
        MagicMock(side_effect=ConnectionError("Scraper down")),
    )

    with pytest.raises(ConnectionError, match="Scraper down"):
        await nba_service.get_nba_matches("today")


@pytest.mark.asyncio
async def test_conversion_preserves_fields():
    match = make_match(clock=None, overtime=True, quarter=4)

    game = nba_service._to_nba_scraper_game(match)

    assert game.id == match.id
    assert game.confederation == match.confederation
    assert game.season_staus == match.season_status
    assert game.home_team == match.home_team
    assert game.away_team == match.away_team
    assert game.home_score == match.home_score
    assert game.away_score == match.away_score
    assert game.status == match.status
    assert game.kickoff == (match.kickoff.isoformat() if match.kickoff else None)
    assert game.quarter == match.quarter
    assert game.agg_home_games == match.agg_home_games
    assert game.agg_away_games == match.agg_away_games


@pytest.mark.asyncio
async def test_poll_live_nba_matches_delegates_to_poller(monkeypatch):
    captured = {}

    async def fake_poll_live(sport, fetch):
        captured["sport"] = sport
        await fetch()

    monkeypatch.setattr(nba_service, "poll_live", fake_poll_live)
    monkeypatch.setattr(nba_service, "get_nba_matches", AsyncMock(return_value=[]))

    await nba_service.poll_live_nba_matches()

    assert captured["sport"] == Sport.NBA
