from pydantic import BaseModel, Field

from app.domain.schemas.game import ExternalNBAGame


# shared
class Status(BaseModel):
    name: str


class BaseTeam(BaseModel):
    name: str


# futbol ones
class GoalEvent(BaseModel):
    player_name: str
    time_to_display: str | None = None
    own_goal: bool = False
    penalty: bool = False


class FutbolTeam(BaseTeam):
    goals: list[GoalEvent] = Field(default_factory=list)


# game data
class FutbolGameData(BaseModel):
    id: str
    status: Status
    start_time: str | None = None
    scores: list[int | None] = Field(default_factory=list)
    teams: tuple[FutbolTeam, FutbolTeam]
    agg_scores: list[int] | None = None
    penalties: list[int] | None = None
    game_time: int | None = None
    to_qualify: str | None = None


class NBAGameData(BaseModel):
    id: str
    status: Status
    start_time: str | None = None
    scores: list[int | None] = Field(default_factory=list)
    teams: tuple[BaseTeam, BaseTeam]
    quarter: int | None = None
    clock: str | None = None
    overtime: bool | None = None
    season_status: str | None = None


# response models
class FutbolLeague(BaseModel):
    url_name: str
    games: list[FutbolGameData]


class FutbolMatchesResponse(BaseModel):
    leagues: list[FutbolLeague]


class NBAScoreboardResponse(BaseModel):
    events: list[ExternalNBAGame] = Field(default_factory=list)
