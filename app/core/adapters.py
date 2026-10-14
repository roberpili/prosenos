from pydantic import TypeAdapter

from app.domain.schemas.data import FutbolMatchesResponse, NBAScoreboardResponse

futbol_adapter = TypeAdapter(FutbolMatchesResponse)
nba_adapter = TypeAdapter(NBAScoreboardResponse)
