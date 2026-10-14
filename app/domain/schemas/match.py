from datetime import datetime

from pydantic import BaseModel


class Match(BaseModel):
    id: str
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None
    status: str
    kickoff: datetime | None = None


class FutbolMatch(Match):
    league: str
    minute: int
    agg_home_score: int | None
    agg_away_score: int | None
    home_penalties: int | None
    away_penalties: int | None
    qualifies: str | None
    home_scorers: list[str]
    away_scorers: list[str]


class NBAMatch(Match):
    clock: str | None
    season_status: str | None
    overtime: bool
    quarter: int | None
