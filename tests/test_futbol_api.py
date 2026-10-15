from datetime import date
from unittest.mock import MagicMock

import httpx
import pytest
import pytest_asyncio

from app.core.utils import FUTBOL_URL
from app.main import app

DATE_DETAIL = "Use date format: DD-MM-YYYY (e.g. 06-07-2026 or 06/07/2026)"


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def make_game(**overrides):
    game = {
        "id": "123",
        "status": {"name": "finished"},
        "start_time": "06-07-2026 21:00",
        "scores": [2, 1],
        "teams": [
            {
                "name": "Boca",
                "goals": [
                    {
                        "player_name": "Ascacibar",
                        "time_to_display": "25'",
                        "own_goal": False,
                        "penalty": False,
                    }
                ],
            },
            {
                "name": "River",
                "goals": [
                    {
                        "player_name": "Almada",
                        "time_to_display": "10'",
                        "own_goal": False,
                        "penalty": False,
                    }
                ],
            },
        ],
        "agg_scores": [3, 2],
        "penalties": [1, 3],
        "game_time": None,
        # "to_qualify": "home",
    }
    game.update(overrides)
    return game


def make_payload():
    return {
        "leagues": [
            {"url_name": "conmebol-libertadores", "games": [make_game()]},
            # not present in LEAGUES, must be filtered out
            {"url_name": "unknown-league", "games": [make_game(id="999")]},
        ]
    }


EXPECTED_MATCH = {
    "id": "123",
    "league": "Conmebol Libertadores",
    "home_team": "Boca",
    "away_team": "River",
    "home_score": 2,
    "away_score": 1,
    "status": "finished",
    "minute": -1,
    "kickoff": "2026-07-06T21:00:00+00:00",
    "agg_home_score": 3,
    "agg_away_score": 2,
    "home_penalties": 1,
    "away_penalties": 3,
    "home_scorers": ["Ascacibar 25'"],
    "away_scorers": ["Almada 10'"],
}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("route", "day"),
    [("yesterday", "yesterday"), ("today", "today"), ("tomorrow", "tomorrow")],
)
async def test_keyword_route_fetches_expected_date(client, monkeypatch, route, day):
    target = date(2026, 10, 9)
    resolve_date = MagicMock(return_value=target)
    fetch_json = MagicMock(return_value=make_payload())
    monkeypatch.setattr("app.services.futbol.resolve_date", resolve_date)
    monkeypatch.setattr("app.core.futbol.fetch_json", fetch_json)

    response = await client.get(f"/api/v1/futbol/matches/{route}")

    assert response.status_code == 200
    resolve_date.assert_called_once_with(day)
    fetch_json.assert_called_once_with(f"{FUTBOL_URL}/09-10-2026/")
    print("expected: ", EXPECTED_MATCH)
    print("response: ", response.json())
    assert response.json() == [EXPECTED_MATCH]


@pytest.mark.asyncio
async def test_explicit_date_route_returns_mapped_payload(client, monkeypatch):
    fetch_json = MagicMock(return_value=make_payload())
    monkeypatch.setattr("app.core.futbol.fetch_json", fetch_json)

    response = await client.get("/api/v1/futbol/matches/06-07-2026")

    assert response.status_code == 200
    fetch_json.assert_called_once_with(f"{FUTBOL_URL}/06-07-2026/")
    assert response.json() == [EXPECTED_MATCH]


@pytest.mark.asyncio
async def test_slash_date_route_is_normalized(client, monkeypatch):
    fetch_json = MagicMock(return_value=make_payload())
    monkeypatch.setattr("app.core.futbol.fetch_json", fetch_json)

    response = await client.get("/api/v1/futbol/matches/06/07/2026")

    assert response.status_code == 200
    fetch_json.assert_called_once_with(f"{FUTBOL_URL}/06-07-2026/")
    assert response.json() == [EXPECTED_MATCH]


@pytest.mark.asyncio
async def test_empty_provider_response_returns_empty_list(client, monkeypatch):
    fetch_json = MagicMock(return_value={"leagues": []})
    monkeypatch.setattr("app.core.futbol.fetch_json", fetch_json)

    response = await client.get("/api/v1/futbol/matches/06-07-2026")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_missing_start_time_returns_null_kickoff(client, monkeypatch):
    payload = {
        "leagues": [{"url_name": "laliga", "games": [make_game(start_time=None)]}]
    }
    monkeypatch.setattr("app.core.futbol.fetch_json", MagicMock(return_value=payload))

    response = await client.get("/api/v1/futbol/matches/06-07-2026")

    assert response.status_code == 200
    assert response.json()[0]["kickoff"] is None
    assert response.json()[0]["minute"] == -1


@pytest.mark.asyncio
@pytest.mark.parametrize("day", ["not-a-date", "31-02-2026", "06.07.2026"])
async def test_invalid_date_returns_400_without_fetching(client, monkeypatch, day):
    fetch_json = MagicMock()
    monkeypatch.setattr("app.core.futbol.fetch_json", fetch_json)

    response = await client.get(f"/api/v1/futbol/matches/{day}")

    assert response.status_code == 400
    assert response.json() == {"detail": DATE_DETAIL}
    fetch_json.assert_not_called()


@pytest.mark.asyncio
async def test_provider_failure_returns_500(monkeypatch):
    monkeypatch.setattr(
        "app.core.futbol.fetch_json", MagicMock(side_effect=ConnectionError("down"))
    )
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/futbol/matches/06-07-2026")

    assert response.status_code == 500
