import os
from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from typing import cast

from fastapi import HTTPException, status

from app.constants import ARGENTINA_TZ
from app.domain.schemas.data import FutbolTeam

_DATE_FORMAT = "%d-%m-%Y"


# mappers
def to_int_pair(values: Sequence[int | None] | None) -> tuple[int | None, int | None]:
    if not values or len(values) < 2:
        return None, None
    first, second = values[0], values[1]
    return (
        int(first) if first is not None else None,
        int(second) if second is not None else None,
    )


def format_scorers(team: FutbolTeam) -> list[str]:
    return [
        f"{g.player_name} {g.time_to_display}"
        + (" (og)" if getattr(g, "own_goal", False) else "")
        + (" (pen" if getattr(g, "penalty", False) else "")
        for g in team.goals
    ]


def format_league_name(url_name: str) -> str:
    return url_name.replace("-", " ").title()


def parse_nba_kickoff(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def parse_futbol_kickoff(value: str) -> datetime:
    print(f"backend raw: {value!r}")
    print(f"system tz: {time.tzname}, TZ env: {os.environ.get('TZ')!r}")
    print(f"ARGENTINA_TZ: {ARGENTINA_TZ!r}")

    naive = datetime.strptime(value, "%d-%m-%Y %H:%M")
    local = naive.replace(tzinfo=ARGENTINA_TZ)
    print(f"parsed local: {local.isoformat()} (offset {local.utcoffset()})")

    utc_result = local.astimezone(UTC)
    print(f"parsed utc: {utc_result.isoformat()}")
    return utc_result


def resolve_date(day: str) -> date:
    today = datetime.now(ARGENTINA_TZ).date()
    offsets = {"yesterday": -1, "today": 0, "tomorrow": 1}

    if day in offsets:
        return today + timedelta(days=offsets[day])

    normalized = day.replace("/", "-")

    try:
        return datetime.strptime(normalized, _DATE_FORMAT).date()  # noqa: DTZ007
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use date format: DD-MM-YYYY (e.g. 06-07-2026 or 06/07/2026)",
        ) from None


def as_dict(value: object) -> dict[str, object]:
    return cast(dict[str, object], value)


def score_to_int(value: object) -> int:
    return int(value) if isinstance(value, (str, int, float)) else 0
