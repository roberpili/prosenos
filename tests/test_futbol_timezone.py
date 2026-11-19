import os
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
import pytest_asyncio

import app.helpers as helpers
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("11-11-2026 15:00", datetime(2026, 11, 11, 18, 0, tzinfo=UTC)),
        ("11-11-2026 17:00", datetime(2026, 11, 11, 20, 0, tzinfo=UTC)),
        ("11-11-2026 00:00", datetime(2026, 11, 11, 3, 0, tzinfo=UTC)),
        # crossing midnight in UTC must advance the date
        ("11-11-2026 23:59", datetime(2026, 11, 12, 2, 59, tzinfo=UTC)),
    ],
)
def test_parse_futbol_kickoff_converts_argentina_local_to_utc(raw, expected):
    parsed = helpers.parse_futbol_kickoff(raw)

    assert parsed == expected
    assert parsed.utcoffset() == expected.utcoffset()
    assert parsed.isoformat() == expected.isoformat()


def test_parse_futbol_kickoff_does_not_treat_provider_time_as_utc():
    parsed = helpers.parse_futbol_kickoff("11-11-2026 15:00")

    assert parsed != datetime(2026, 11, 11, 15, 0, tzinfo=UTC)
    assert parsed == datetime(2026, 11, 11, 18, 0, tzinfo=UTC)


def test_parse_futbol_kickoff_is_independent_of_process_timezone():
    script = (
        "from app.helpers import parse_futbol_kickoff; "
        "print(parse_futbol_kickoff('11-11-2026 15:00').isoformat())"
    )
    outputs = {}

    for tz in ("UTC", "America/New_York", "Europe/London"):
        env = {**os.environ, "TZ": tz}
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, result.stderr
        outputs[tz] = result.stdout.strip().splitlines()[-1]

    assert set(outputs.values()) == {"2026-11-11T18:00:00+00:00"}


def test_resolve_date_uses_argentina_calendar_day(monkeypatch):
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            instant = datetime(2026, 11, 11, 2, 0, tzinfo=UTC)
            return instant.astimezone(tz) if tz else instant

    monkeypatch.setattr(helpers, "datetime", FrozenDateTime)

    # 02:00 UTC is still 23:00 on 10-11 in Argentina.
    assert helpers.resolve_date("today") == date(2026, 11, 10)
    assert helpers.resolve_date("tomorrow") == date(2026, 11, 11)


def make_payload(start_time: str = "11-11-2026 15:00"):
    return {
        "leagues": [
            {
                "url_name": "conmebol-libertadores",
                "games": [
                    {
                        "id": "123",
                        "status": {"name": "scheduled"},
                        "start_time": start_time,
                        "scores": [0, 0],
                        "teams": [
                            {"name": "Boca", "goals": []},
                            {"name": "River", "goals": []},
                        ],
                    }
                ],
            }
        ]
    }


@pytest.mark.asyncio
async def test_futbol_api_serializes_kickoff_as_utc(client, monkeypatch):
    monkeypatch.setattr(
        "app.core.futbol.fetch_json", MagicMock(return_value=make_payload())
    )

    response = await client.get("/api/v1/futbol/matches/11-11-2026")

    assert response.status_code == 200
    assert response.json()[0]["kickoff"] == "2026-11-11T18:00:00+00:00"
