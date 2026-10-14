from app.domain.schemas.game import FutbolScraperGame


def check_if_finished(match: FutbolScraperGame) -> bool:
    has_scores = match.home_score is not None and match.away_score is not None

    if match.status == "finished":
        return has_scores

    # if match.status == "Por penales":
    #     return has_scores and match.qualifies is not None and match.qualifies > 0

    return False


# def map_match_to_game(match: ScraperGame, ext_id: str, sport: str) -> GameModel:
#     played_at = None
#     if match.kickoff:
#         with suppress(ValueError, TypeError):
#             played_at = datetime.fromisoformat(match.kickoff)

#     return GameModel(
#         external_id=ext_id,
#         sport=sport,
#         league=match.league,
#         home_team=match.home_team,
#         away_team=match.away_team,
#         home_score=match.home_score,
#         away_score=match.away_score,
#         status=match.status,
#         minute=match.minute,
#         played_at=played_at,
#         agg_home_score=match.agg_home_score,
#         agg_away_score=match.agg_away_score,
#         home_penalties=match.home_penalties,
#         away_penalties=match.away_penalties,
#         qualifies=match.qualifies,
#         home_scorers=match.home_scorers,
#         away_scorers=match.away_scorers,
#     )
