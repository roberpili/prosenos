from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class ExternalNBAGame(BaseModel):
    id: str
    date: str
    name: str | None = None
    competitions: list[dict[str, object]] = Field(default_factory=list)
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class NBAScraperGame(BaseModel):
    id: str
    season_staus: str | None = None
    home_team: str
    away_team: str
    home_score: int | None = None
    away_score: int | None = None
    status: str
    quarter: int | None = None
    kickoff: str | None = None
    clock: str | None = None
    overtime: bool | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class FutbolScraperGame(BaseModel):
    id: str
    league: str
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None
    status: str
    minute: int | None
    kickoff: str | None
    agg_home_score: int | None = None
    agg_away_score: int | None = None
    home_penalties: int | None = None
    away_penalties: int | None = None
    home_scorers: list[str] = []
    away_scorers: list[str] = []

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
