from pydantic import TypeAdapter

from app.domain.schemas.data import (
    FutbolMatchesResponse,
    NBALeaderboardResponse,
    NBAScoreboardResponse,
)

futbol_adapter = TypeAdapter(FutbolMatchesResponse)
nba_adapter = TypeAdapter(NBAScoreboardResponse)
nba_leaderboard_adapter = TypeAdapter(NBALeaderboardResponse)
