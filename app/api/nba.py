from fastapi.routing import APIRouter

from app.domain.schemas.game import NBAScraperGame
from app.domain.schemas.leaderboard import NBAStandings
from app.services.nba import get_nba_leaderboard, get_nba_matches

router = APIRouter(prefix="/api/v1/nba", tags=["nba_endpoints"])


@router.get("/matches/yesterday")
async def yesterday_nba_matches() -> list[NBAScraperGame]:
    return await get_nba_matches("yesterday")


@router.get("/matches/tomorrow")
async def tomorrow_nba_matches() -> list[NBAScraperGame]:
    return await get_nba_matches("tomorrow")


@router.get("/matches/today")
async def today_nba_matches() -> list[NBAScraperGame]:
    return await get_nba_matches("today")


@router.get("/matches/{day:path}")
async def nba_matches(day: str) -> list[NBAScraperGame]:
    day = day.replace("/", "-")
    return await get_nba_matches(day)


# leaderboard
@router.get("/leaderboard")
async def nba_leaderboard() -> NBAStandings:
    return await get_nba_leaderboard()
