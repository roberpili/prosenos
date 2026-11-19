from typing import NotRequired, TypedDict

from pydantic import BaseModel, Field


class NBAStandingTeam(BaseModel):
    id: str
    name: str
    abbreviation: str
    logo: str
    wins: int
    losses: int
    win_percentage: float
    games_behind: float
    streak: str


class NBAStandings(BaseModel):
    eastern_conference: list[NBAStandingTeam] = Field(default_factory=list)
    western_conference: list[NBAStandingTeam] = Field(default_factory=list)


# response types
class LeaderboardLogo(TypedDict):
    href: str
    rel: list[str]


class LeaderboardTeam(TypedDict):
    id: str
    displayName: str
    abbreviation: str
    logos: list[LeaderboardLogo]


class LeaderboardStat(TypedDict):
    name: str
    value: NotRequired[float | int]
    displayValue: NotRequired[str]


class LeaderboardEntry(TypedDict):
    team: LeaderboardTeam
    stats: list[LeaderboardStat]


class LeaderboardStandings(TypedDict):
    entries: list[LeaderboardEntry]


class LeaderboardConference(TypedDict):
    abbreviation: str
    standings: LeaderboardStandings
