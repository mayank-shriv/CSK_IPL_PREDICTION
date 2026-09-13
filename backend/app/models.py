from dataclasses import dataclass, field
from typing import Literal

Outcome = Literal["A_WIN", "B_WIN", "NO_RESULT"]


@dataclass
class Standing:
    team: str
    played: int
    wins: int
    losses: int
    no_results: int
    points: int
    nrr: float | None = None


@dataclass(frozen=True)
class Fixture:
    team_a: str
    team_b: str
    label: str | None = None


@dataclass(frozen=True)
class SeasonRules:
    season: int
    playoff_teams: int = 4
    points_for_win: int = 2
    points_for_loss: int = 0
    points_for_no_result: int = 1
    tie_break_rules: tuple[str, ...] = ("net_run_rate",)
    source_name: str = "IPL official competition rules"
    source_url: str | None = None
    rules_version: str = "unverified-season-config"


@dataclass
class Scenario:
    outcomes: list[str]
    points: dict[str, int]
    position: int
    qualifies: bool
    nrr_dependency: bool = False


@dataclass
class QualificationResult:
    status: str
    selected_team: str
    current_points: int
    maximum_points: int
    matches_remaining: int
    best_position: int
    worst_position: int
    scenarios_analyzed: int
    qualifying_scenarios: int
    elimination_scenarios: int
    required_wins: int
    nrr_dependency: bool
    explanation: str
    qualifying_examples: list[Scenario] = field(default_factory=list)
    elimination_examples: list[Scenario] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
