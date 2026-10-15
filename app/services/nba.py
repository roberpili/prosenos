import asyncio
import logging
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException, status

from app.core.nba import get_nba_matches_by_date
from app.domain.enums import Sport
from app.domain.schemas.game import NBAScraperGame
from app.domain.schemas.match import NBAMatch
from app.services.poller import poll_live

logger = logging.getLogger(__name__)
POLL_INTERVAL = 15

_DATE_FORMAT = "%d-%m-%Y"


def _resolve_date(day: str) -> date:
    if day == "yesterday":
        return datetime.now(UTC).date() - timedelta(days=1)

    if day == "tomorrow":
        return datetime.now(UTC).date() + timedelta(days=1)

    if day == "today":
        return datetime.now(UTC).date()

    normalized = day.replace("/", "-")

    try:
        return datetime.strptime(normalized, _DATE_FORMAT).replace(tzinfo=UTC).date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use date format: DD-MM-YYYY (e.g. 06-07-2026 or 06/07/2026)",
        ) from None


def _to_nba_scraper_game(match: NBAMatch) -> NBAScraperGame:
    return NBAScraperGame(
        id=match.id,
        season_staus=match.season_status,
        home_team=match.home_team,
        away_team=match.away_team,
        home_score=match.home_score,
        away_score=match.away_score,
        status=match.status,
        kickoff=match.kickoff.isoformat() if match.kickoff else None,
        quarter=match.quarter,
        clock=match.clock,
        overtime=match.overtime,
    )


async def get_nba_matches(day: str) -> list[NBAScraperGame]:
    target_date = _resolve_date(day)
    matches = await asyncio.to_thread(get_nba_matches_by_date, target_date)
    return [_to_nba_scraper_game(match) for match in matches]


async def poll_live_nba_matches() -> None:
    await poll_live(Sport.NBA, lambda: get_nba_matches("today"))
