from datetime import date

from app.core.adapters import nba_adapter
from app.core.utils import build_date_url, fetch_json, resolve_date
from app.domain.enums import Sport
from app.domain.schemas.match import NBAMatch
from app.mappers import map_nba_matches


def fetch_nba_matches(url: str) -> list[NBAMatch]:
    response = nba_adapter.validate_python(fetch_json(url))
    return map_nba_matches(response.events)


def get_nba_matches_by_date(target_date: date) -> list[NBAMatch]:
    url = build_date_url(target_date, Sport.NBA)
    return fetch_nba_matches(url)


def get_today_nba_matches() -> list[NBAMatch]:
    return get_nba_matches_by_date(resolve_date())


def get_yesterday_nba_matches() -> list[NBAMatch]:
    return get_nba_matches_by_date(resolve_date(-1))


def get_tomorrow_nba_matches() -> list[NBAMatch]:
    return get_nba_matches_by_date(resolve_date(1))
