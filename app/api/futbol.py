from fastapi.routing import APIRouter

from app.domain.schemas.game import FutbolScraperGame
from app.services.futbol import get_futbol_matches

router = APIRouter(prefix="/api/v1/matches", tags=["matches"])


@router.get("/yesterday")
async def yesterday_matches() -> list[FutbolScraperGame]:
    return await get_futbol_matches("yesterday")


@router.get("/today")
async def today_matches() -> list[FutbolScraperGame]:
    return await get_futbol_matches("today")


@router.get("/{day:path}")
async def matches(day: str) -> list[FutbolScraperGame]:
    day = day.replace("/", "-")
    return await get_futbol_matches(day)
