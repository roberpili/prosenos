from datetime import date

from app.core.adapters import futbol_adapter
from app.core.utils import build_date_url, fetch_json, resolve_date
from app.domain.enums import Sport
from app.domain.schemas.data import FutbolMatchesResponse
from app.domain.schemas.match import FutbolMatch
from app.mappers import map_futbol_matches


def fetch_futbol_matches(url: str) -> FutbolMatchesResponse:
    return futbol_adapter.validate_python(fetch_json(url))


def get_futbol_matches_by_date(target_date: date) -> list[FutbolMatch]:
    url = build_date_url(target_date, Sport.FUTBOL)
    return map_futbol_matches(fetch_futbol_matches(url))


def get_today_futbol_matches() -> list[FutbolMatch]:
    return get_futbol_matches_by_date(resolve_date())


def get_yesterday_futbol_matches() -> list[FutbolMatch]:
    return get_futbol_matches_by_date(resolve_date(-1))


def get_tomorrow_futbol_matches() -> list[FutbolMatch]:
    return get_futbol_matches_by_date(resolve_date(1))
