from app.domain.schemas.game import FutbolScraperGame
from app.services.helpers import check_if_finished


def make_game(**overrides):
    defaults = {
        "id": "1",
        "league": "L",
        "home_team": "A",
        "away_team": "B",
        "home_score": 1,
        "away_score": 0,
        "status": "live",
        "minute": 1,
        "kickoff": None,
    }
    return FutbolScraperGame(**dict(defaults, **overrides))


def test_check_if_finished_true_when_finished_with_scores():
    game = make_game(status="finished", home_score=2, away_score=1)

    assert check_if_finished(game) is True


def test_check_if_finished_false_when_finished_without_scores():
    game = make_game(status="finished", home_score=None, away_score=1)

    assert check_if_finished(game) is False


def test_check_if_finished_false_for_non_finished_statuses():
    for status in ("live", "scheduled", "postponed", ""):
        game = make_game(status=status, home_score=2, away_score=1)

        assert check_if_finished(game) is False
