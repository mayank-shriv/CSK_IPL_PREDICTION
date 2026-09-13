from itertools import product
from copy import deepcopy

from .models import Fixture, QualificationResult, Scenario, SeasonRules, Standing


def _rank(standings: dict[str, Standing], rules: SeasonRules) -> list[Standing]:
    # Points are deterministic; tied points remain NRR-dependent because future margins are unknown.
    return sorted(standings.values(), key=lambda row: (row.points, row.nrr or 0), reverse=True)


def analyze(
    current_standings: list[Standing],
    remaining_matches: list[Fixture],
    selected_team: str,
    rules: SeasonRules,
    max_scenarios: int = 100_000,
) -> QualificationResult:
    if selected_team not in {row.team for row in current_standings}:
        raise ValueError("Selected team is not present in the standings.")
    if any(f.team_a == f.team_b for f in remaining_matches):
        raise ValueError("A fixture cannot contain the same team twice.")
    if len(remaining_matches) and 3 ** len(remaining_matches) > max_scenarios:
        raise ValueError(f"This analysis has more than {max_scenarios:,} scenarios; reduce remaining fixtures.")

    base = {row.team: deepcopy(row) for row in current_standings}
    team_matches = sum(selected_team in (match.team_a, match.team_b) for match in remaining_matches)
    outcomes = list(product(("A_WIN", "B_WIN", "NO_RESULT"), repeat=len(remaining_matches)))
    scenarios: list[Scenario] = []

    for outcome_set in outcomes:
        simulated = deepcopy(base)
        for fixture, outcome in zip(remaining_matches, outcome_set):
            first, second = simulated[fixture.team_a], simulated[fixture.team_b]
            first.played += 1
            second.played += 1
            if outcome == "A_WIN":
                first.wins += 1
                second.losses += 1
                first.points += rules.points_for_win
                second.points += rules.points_for_loss
            elif outcome == "B_WIN":
                second.wins += 1
                first.losses += 1
                second.points += rules.points_for_win
                first.points += rules.points_for_loss
            else:
                first.no_results += 1
                second.no_results += 1
                first.points += rules.points_for_no_result
                second.points += rules.points_for_no_result

        ranked = _rank(simulated, rules)
        position = next(index for index, row in enumerate(ranked, start=1) if row.team == selected_team)
        cutoff_points = ranked[rules.playoff_teams - 1].points
        tied_at_cutoff = position <= rules.playoff_teams and any(
            row.points == cutoff_points for row in ranked[rules.playoff_teams:]
        )
        scenarios.append(Scenario(
            outcomes=list(outcome_set),
            points={team: row.points for team, row in simulated.items()},
            position=position,
            qualifies=position <= rules.playoff_teams,
            nrr_dependency=tied_at_cutoff,
        ))

    qualifying = [scenario for scenario in scenarios if scenario.qualifies]
    eliminated = [scenario for scenario in scenarios if not scenario.qualifies]
    best = min(scenario.position for scenario in scenarios)
    worst = max(scenario.position for scenario in scenarios)
    current = base[selected_team].points
    maximum = current + team_matches * rules.points_for_win
    nrr_dependency = any(scenario.nrr_dependency for scenario in scenarios)

    if not qualifying:
        status = "ELIMINATED"
    elif not eliminated and not nrr_dependency:
        status = "GUARANTEED"
    else:
        status = "POSSIBLE"

    explanation = _explanation(status, selected_team, current, maximum, team_matches, nrr_dependency, rules)
    warnings = []
    if nrr_dependency:
        warnings.append("Some qualifying outcomes finish teams on tied points; future NRR cannot be derived from this table alone.")
    if rules.rules_version.endswith("draft"):
        warnings.append("Season rules are a draft configuration and must be verified against the official IPL/BCCI release.")

    return QualificationResult(
        status=status,
        selected_team=selected_team,
        current_points=current,
        maximum_points=maximum,
        matches_remaining=team_matches,
        best_position=best,
        worst_position=worst,
        scenarios_analyzed=len(scenarios),
        qualifying_scenarios=len(qualifying),
        elimination_scenarios=len(eliminated),
        required_wins=max(0, (rules.playoff_teams - 1) if not qualifying else 0),
        nrr_dependency=nrr_dependency,
        explanation=explanation,
        qualifying_examples=qualifying[:3],
        elimination_examples=eliminated[:3],
        warnings=warnings,
    )


def _explanation(status: str, team: str, current: int, maximum: int, matches: int, nrr: bool, rules: SeasonRules) -> str:
    if status == "ELIMINATED":
        return f"{team} cannot reach the top {rules.playoff_teams} in any remaining-results combination."
    if status == "GUARANTEED":
        return f"{team} qualifies in every remaining-results combination, finishing between the best and worst positions shown."
    suffix = " NRR may decide tied points." if nrr else ""
    return f"{team} can still qualify: {current} current points, up to {maximum} points after {matches} remaining matches.{suffix}"
