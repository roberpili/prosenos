from fastapi.routing import APIRouter

from app.domain.schemas.game import NBAScraperGame
from app.services.nba import get_nba_matches

router = APIRouter(prefix="/api/v1/nba/matches", tags=["nba_matches"])


@router.get("/yesterday")
async def yesterday_nba_matches() -> list[NBAScraperGame]:
    return await get_nba_matches("yesterday")


@router.get("/tomorrow")
async def tomorrow_nba_matches() -> list[NBAScraperGame]:
    return await get_nba_matches("tomorrow")


@router.get("/today")
async def today_nba_matches() -> list[NBAScraperGame]:
    return await get_nba_matches("today")


@router.get("/{day:path}")
async def nba_matches(day: str) -> list[NBAScraperGame]:
    day = day.replace("/", "-")
    return await get_nba_matches(day)
