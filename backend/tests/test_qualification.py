from app.models import Fixture, SeasonRules, Standing
from app.ocr import ScoreboardExtractor
from app.qualification import analyze


def test_mixed_outcomes_produce_possible_status():
    standings = [
        Standing("CSK", 12, 6, 6, 0, 12, 0.1),
        Standing("GT", 12, 8, 4, 0, 16, 0.2),
        Standing("RCB", 12, 5, 7, 0, 10, -0.1),
        Standing("MI", 12, 4, 8, 0, 8, -0.2),
    ]
    fixtures = [Fixture("CSK", "RCB"), Fixture("GT", "MI"), Fixture("GT", "RCB")]
    result = analyze(standings, fixtures, "CSK", SeasonRules(2026, playoff_teams=2))
    assert result.status == "POSSIBLE"
    assert result.scenarios_analyzed == 27
    assert result.qualifying_scenarios > 0
    assert result.elimination_scenarios > 0


def test_no_remaining_matches_can_be_guaranteed_or_eliminated():
    standings = [
        Standing("CSK", 14, 8, 6, 0, 16, 0.1),
        Standing("GT", 14, 7, 7, 0, 14, 0.2),
        Standing("RCB", 14, 6, 8, 0, 12, -0.1),
    ]
    result = analyze(standings, [], "CSK", SeasonRules(2026, playoff_teams=2))
    assert result.status == "GUARANTEED"
    assert result.scenarios_analyzed == 1


def test_ocr_parser_normalizes_standings_row():
    row = ScoreboardExtractor._parse_line(["1", "CSK", "12", "6", "6", "0", "12", "+0.321"])
    assert row == {
        "team": "CSK",
        "played": 12,
        "wins": 6,
        "losses": 6,
        "no_results": 0,
        "points": 12,
        "nrr": 0.321,
    }
