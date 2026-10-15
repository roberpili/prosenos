from typing import cast

from app.constants import LEAGUES
from app.domain.schemas.data import FutbolGameData, FutbolMatchesResponse
from app.domain.schemas.game import ExternalNBAGame
from app.domain.schemas.match import FutbolMatch, NBAMatch
from app.helpers import (
    as_dict,
    format_league_name,
    format_scorers,
    parse_futbol_kickoff,
    parse_nba_kickoff,
    score_to_int,
    to_int_pair,
)


def map_futbol_match(game: FutbolGameData, league_name: str) -> FutbolMatch:
    home_team, away_team = game.teams
    home_score, away_score = to_int_pair(game.scores)
    agg_home_score, agg_away_score = to_int_pair(game.agg_scores)
    home_penalties, away_penalties = to_int_pair(game.penalties)

    return FutbolMatch(
        id=game.id,
        league=format_league_name(league_name),
        home_team=home_team.name,
        away_team=away_team.name,
        home_score=home_score,
        away_score=away_score,
        status=game.status.name,
        minute=game.game_time or -1,
        kickoff=parse_futbol_kickoff(game.start_time) if game.start_time else None,
        agg_home_score=agg_home_score,
        agg_away_score=agg_away_score,
        home_penalties=home_penalties,
        away_penalties=away_penalties,
        # qualifies=game.to_qualify,
        home_scorers=format_scorers(home_team),
        away_scorers=format_scorers(away_team),
    )


def map_nba_match(game: ExternalNBAGame) -> NBAMatch:
    competition = game.competitions[0]
    competitors = cast(list[dict[str, object]], competition["competitors"])

    home = next(c for c in competitors if c.get("homeAway") == "home")
    away = next(c for c in competitors if c.get("homeAway") == "away")
    home_team = as_dict(home["team"])
    away_team = as_dict(away["team"])
    status = as_dict(as_dict(competition["status"])["type"])

    return NBAMatch(
        id=game.id,
        home_team=str(home_team["displayName"]),
        away_team=str(away_team["displayName"]),
        home_score=score_to_int(home.get("score")),
        away_score=score_to_int(away.get("score")),
        status=str(status["name"]),
        kickoff=parse_nba_kickoff(game.date),
        clock=str(as_dict(competition["status"]).get("displayClock", "")),
        season_status=None,
        overtime=False,
        quarter=None,
    )


def map_futbol_matches(data: FutbolMatchesResponse) -> list[FutbolMatch]:
    return [
        map_futbol_match(game, league.url_name)
        for league in data.leagues
        if league.url_name in LEAGUES
        for game in league.games
    ]


def map_nba_matches(games: list[ExternalNBAGame]) -> list[NBAMatch]:
    return [map_nba_match(game) for game in games]
