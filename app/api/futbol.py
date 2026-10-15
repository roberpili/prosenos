from fastapi.routing import APIRouter

from app.domain.schemas.game import FutbolScraperGame
from app.services.futbol import get_futbol_matches

router = APIRouter(prefix="/api/v1/futbol/matches", tags=["futbol_matches"])


@router.get("/yesterday")
async def yesterday_futbol_matches() -> list[FutbolScraperGame]:
    return await get_futbol_matches("yesterday")


@router.get("/tomorrow")
async def tomorrow_futbol_matches() -> list[FutbolScraperGame]:
    return await get_futbol_matches("tomorrow")


@router.get("/today")
async def today_futbol_matches() -> list[FutbolScraperGame]:
    return await get_futbol_matches("today")


@router.get("/{day:path}")
async def futbol_matches(day: str) -> list[FutbolScraperGame]:
    day = day.replace("/", "-")
    return await get_futbol_matches(day)
