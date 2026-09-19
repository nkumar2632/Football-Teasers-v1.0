"""Ingestion: side-perspective spreads, preserved source fields, honest provenance."""

from __future__ import annotations

import pandas as pd
import pytest

from teaser_model_v1.ingest import nflverse
from teaser_model_v1.ingest.provenance import (
    ARCHIVED_REFERENCE_LINE,
    TRUE_TIMESTAMPED_CLOSE,
)


@pytest.fixture
def games():
    return pd.DataFrame(
        [
            {
                "game_id": "2024_01_AAA_BBB",
                "season": 2024,
                "game_type": "REG",
                "week": 1,
                "gameday": "2024-09-08",
                "away_team": "AAA",
                "home_team": "BBB",
                "away_score": 20,
                "home_score": 23,
                "result": 3,
                "total": 43,
                "spread_line": 1.5,  # home favoured by 1.5
                "total_line": 44.5,
            },
            {
                "game_id": "2024_01_CCC_DDD",
                "season": 2024,
                "game_type": "REG",
                "week": 1,
                "gameday": "2024-09-08",
                "away_team": "CCC",
                "home_team": "DDD",
                "away_score": 31,
                "home_score": 17,
                "result": -14,
                "total": 48,
                "spread_line": -7.5,  # away favoured by 7.5
                "total_line": 46.0,
            },
        ]
    )


def test_spread_is_flipped_to_the_perspective_of_the_team_being_bet(games):
    legs = nflverse.to_legs(games)
    by_id = {row["leg_id"]: row for _, row in legs.iterrows()}

    # spread_line = +1.5 means the HOME team is favoured by 1.5.
    assert by_id["2024_01_AAA_BBB-BBB"]["spread"] == pytest.approx(-1.5)
    assert by_id["2024_01_AAA_BBB-AAA"]["spread"] == pytest.approx(1.5)

    # spread_line = -7.5 means the AWAY team is favoured by 7.5.
    assert by_id["2024_01_CCC_DDD-CCC"]["spread"] == pytest.approx(-7.5)
    assert by_id["2024_01_CCC_DDD-DDD"]["spread"] == pytest.approx(7.5)


def test_margins_are_from_the_teams_own_perspective(games):
    legs = nflverse.to_legs(games)
    by_id = {row["leg_id"]: row for _, row in legs.iterrows()}
    assert by_id["2024_01_AAA_BBB-BBB"]["margin"] == 3
    assert by_id["2024_01_AAA_BBB-AAA"]["margin"] == -3
    assert by_id["2024_01_CCC_DDD-CCC"]["margin"] == 14


def test_source_fields_are_preserved_alongside_derived_ones(games):
    legs = nflverse.to_legs(games)
    assert (legs["source_spread_line"] == legs["spread_line"]).all()
    for col in ("game_id", "season", "week", "home_team", "away_team", "total_line"):
        assert col in legs.columns


def test_every_game_becomes_exactly_two_legs(games):
    legs = nflverse.to_legs(games)
    assert len(legs) == 2 * len(games)
    assert legs["leg_id"].is_unique


def test_lines_are_labelled_archived_reference_not_a_close(games):
    legs = nflverse.to_legs(games)
    assert (legs["line_provenance"] == ARCHIVED_REFERENCE_LINE).all()
    assert nflverse.LINE_PROVENANCE == ARCHIVED_REFERENCE_LINE
    assert nflverse.LINE_PROVENANCE != TRUE_TIMESTAMPED_CLOSE


def test_source_documentation_makes_no_closing_claim():
    # Guard against a future session quietly upgrading the provenance label.
    for text in nflverse.LINE_FIELD_DOCS.values():
        assert "clos" not in text.lower()
    assert "no claim about capture time" in nflverse.LINE_PROVENANCE_JUSTIFICATION


def test_unplayed_games_are_excluded_not_imputed(games):
    scheduled = games.copy()
    scheduled.loc[0, ["home_score", "away_score", "result", "total"]] = None
    played = nflverse.played_games(scheduled)
    assert len(played) == 1
    assert played.iloc[0]["game_id"] == "2024_01_CCC_DDD"


def test_missing_required_columns_raise(tmp_path, games):
    path = tmp_path / "games.csv"
    games.drop(columns=["spread_line"]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="missing required columns"):
        nflverse.load_games(path)
