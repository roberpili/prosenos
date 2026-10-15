from datetime import date
from unittest.mock import MagicMock

import httpx
import pytest
import pytest_asyncio

from app.core.utils import NBA_URL
from app.main import app

DATE_DETAIL = "Use date format: DD-MM-YYYY (e.g. 06-07-2026 or 06/07/2026)"


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def make_competition(
    *,
    home_score="110",
    away_score="104",
    display_clock="0:00",
    status_name="STATUS_FINAL",
    home_team="Atlanta Hawks",
    away_team="Boston Celtics",
):
    home = {"homeAway": "home", "team": {"displayName": home_team}}
    away = {"homeAway": "away", "team": {"displayName": away_team}}
    if home_score is not None:
        home["score"] = home_score
    if away_score is not None:
        away["score"] = away_score

    status = {"type": {"name": status_name}}
    if display_clock is not None:
        status["displayClock"] = display_clock

    return {"competitors": [home, away], "status": status}


def make_event(**overrides):
    event = {
        "id": "401",
        "date": "2026-10-15T23:30:00Z",
        "name": "Hawks vs Celtics",
        "competitions": [make_competition()],
    }
    event.update(overrides)
    return event


def make_payload(events=None):
    return {"events": events if events is not None else [make_event()]}


EXPECTED_EVENT = {
    "id": "401",
    "season_staus": None,
    "home_team": "Atlanta Hawks",
    "away_team": "Boston Celtics",
    "home_score": 110,
    "away_score": 104,
    "status": "STATUS_FINAL",
    "quarter": None,
    "kickoff": "2026-10-15T23:30:00+00:00",
    "clock": "0:00",
    "overtime": False,
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
    monkeypatch.setattr("app.services.nba._resolve_date", resolve_date)
    monkeypatch.setattr("app.core.nba.fetch_json", fetch_json)

    response = await client.get(f"/api/v1/nba/matches/{route}")

    assert response.status_code == 200
    resolve_date.assert_called_once_with(day)
    fetch_json.assert_called_once_with(f"{NBA_URL}?dates=20261009")
    assert response.json() == [EXPECTED_EVENT]


@pytest.mark.asyncio
async def test_explicit_date_route_returns_mapped_payload(client, monkeypatch):
    fetch_json = MagicMock(return_value=make_payload())
    monkeypatch.setattr("app.core.nba.fetch_json", fetch_json)

    response = await client.get("/api/v1/nba/matches/06-07-2026")

    assert response.status_code == 200
    fetch_json.assert_called_once_with(f"{NBA_URL}?dates=20260706")
    assert response.json() == [EXPECTED_EVENT]


@pytest.mark.asyncio
async def test_slash_date_route_is_normalized(client, monkeypatch):
    fetch_json = MagicMock(return_value=make_payload())
    monkeypatch.setattr("app.core.nba.fetch_json", fetch_json)

    response = await client.get("/api/v1/nba/matches/06/07/2026")

    assert response.status_code == 200
    fetch_json.assert_called_once_with(f"{NBA_URL}?dates=20260706")
    assert response.json() == [EXPECTED_EVENT]


@pytest.mark.asyncio
async def test_multiple_events_are_returned_in_order(client, monkeypatch):
    payload = make_payload(
        [
            make_event(id="401"),
            make_event(id="402", date="2026-10-16T00:00:00Z"),
        ]
    )
    monkeypatch.setattr("app.core.nba.fetch_json", MagicMock(return_value=payload))

    response = await client.get("/api/v1/nba/matches/06-07-2026")

    assert response.status_code == 200
    assert [game["id"] for game in response.json()] == ["401", "402"]


@pytest.mark.asyncio
async def test_empty_scoreboard_returns_empty_list(client, monkeypatch):
    monkeypatch.setattr(
        "app.core.nba.fetch_json", MagicMock(return_value={"events": []})
    )

    response = await client.get("/api/v1/nba/matches/06-07-2026")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_missing_score_defaults_to_zero(client, monkeypatch):
    payload = make_payload(
        [make_event(competitions=[make_competition(home_score=None, away_score=None)])]
    )
    monkeypatch.setattr("app.core.nba.fetch_json", MagicMock(return_value=payload))

    response = await client.get("/api/v1/nba/matches/06-07-2026")

    assert response.status_code == 200
    assert response.json()[0]["home_score"] == 0
    assert response.json()[0]["away_score"] == 0


@pytest.mark.asyncio
async def test_missing_display_clock_defaults_to_empty_string(client, monkeypatch):
    payload = make_payload(
        [make_event(competitions=[make_competition(display_clock=None)])]
    )
    monkeypatch.setattr("app.core.nba.fetch_json", MagicMock(return_value=payload))

    response = await client.get("/api/v1/nba/matches/06-07-2026")

    assert response.status_code == 200
    assert response.json()[0]["clock"] == ""


@pytest.mark.asyncio
@pytest.mark.parametrize("day", ["not-a-date", "31-02-2026", "06.07.2026"])
async def test_invalid_date_returns_400_without_fetching(client, monkeypatch, day):
    fetch_json = MagicMock()
    monkeypatch.setattr("app.core.nba.fetch_json", fetch_json)

    response = await client.get(f"/api/v1/nba/matches/{day}")

    assert response.status_code == 400
    assert response.json() == {"detail": DATE_DETAIL}
    fetch_json.assert_not_called()


@pytest.mark.asyncio
async def test_provider_failure_returns_500(monkeypatch):
    monkeypatch.setattr(
        "app.core.nba.fetch_json", MagicMock(side_effect=ConnectionError("down"))
    )
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/nba/matches/06-07-2026")

    assert response.status_code == 500
