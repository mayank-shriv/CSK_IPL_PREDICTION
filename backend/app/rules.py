from .models import SeasonRules


# Season data is intentionally explicit. Add a verified source before exposing a season.
SEASON_RULES = {
    2026: SeasonRules(
        season=2026,
        source_name="IPL season configuration (verify against official IPL/BCCI release)",
        source_url=None,
        rules_version="2026-draft",
    )
}


def get_season_rules(season: int) -> SeasonRules:
    try:
        return SEASON_RULES[season]
    except KeyError as exc:
        raise ValueError(f"No verified rules are configured for IPL {season}.") from exc
