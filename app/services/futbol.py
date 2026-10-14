import asyncio

from app.core.futbol import get_futbol_matches_by_date
from app.domain.enums import Sport
from app.domain.schemas.game import FutbolScraperGame
from app.domain.schemas.match import FutbolMatch
from app.helpers import resolve_date
from app.services.poller import poll_live


def _to_futbol_scraper_game(match: FutbolMatch) -> FutbolScraperGame:
    return FutbolScraperGame(
        id=match.id,
        league=match.league,
        home_team=match.home_team,
        away_team=match.away_team,
        home_score=match.home_score,
        away_score=match.away_score,
        status=match.status,
        minute=match.minute,
        kickoff=match.kickoff.isoformat() if match.kickoff else None,
        agg_home_score=match.agg_home_score,
        agg_away_score=match.agg_away_score,
        home_penalties=match.home_penalties,
        away_penalties=match.away_penalties,
        home_scorers=match.home_scorers,
        away_scorers=match.away_scorers,
    )


async def get_futbol_matches(day: str) -> list[FutbolScraperGame]:
    target_date = resolve_date(day)
    matches = await asyncio.to_thread(get_futbol_matches_by_date, target_date)
    return [_to_futbol_scraper_game(match) for match in matches]


async def poll_live_futbol_matches() -> None:
    await poll_live(Sport.FUTBOL, lambda: get_futbol_matches("today"))
