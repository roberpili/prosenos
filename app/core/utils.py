import os
from datetime import UTC, date, datetime, timedelta
from typing import cast
from urllib.parse import urlencode
from venv import logger

from curl_cffi import Session
from dotenv import load_dotenv

from app.domain.enums import Sport

_ = load_dotenv()

FUTBOL_URL = os.getenv("SCRAPE_FUTBOL_URL")
if not FUTBOL_URL:
    raise ValueError("SCRAPE_FUTBOL_URL environment variable not set")

NBA_URL = os.getenv("SCRAPE_NBA_URL")
if not NBA_URL:
    raise ValueError("SCRAPE_NBA_URL environment variable not set")


def build_date_url(match_date: date, sport: Sport) -> str:
    if sport == Sport.NBA:
        query = urlencode({"dates": match_date.strftime("%Y%m%d")})
        return f"{NBA_URL}?{query}"

    formatted = match_date.strftime("%d-%m-%Y")
    return f"{FUTBOL_URL}/{formatted}/"


def fetch_json(url: str) -> dict[str, object]:
    session = Session(impersonate="firefox133")
    response = session.get(url, headers={"X-VER": "1.11.7.5"}, timeout=30)
    if response.status_code >= 400:
        logger.error(
            "https %s for %s\nresponse: %s",
            response.status_code,
            response.url,
            response.text[:500],
        )
    response.raise_for_status()
    return cast(dict[str, object], response.json())  # pyright: ignore[reportUnknownMemberType]


def resolve_date(offset_days: int = 0) -> date:
    return datetime.now(UTC).date() + timedelta(days=offset_days)
