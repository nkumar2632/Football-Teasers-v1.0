"""Backtest assembly: weekly grouping, top-four ranking, ticket enumeration, output shape."""

from __future__ import annotations

import pandas as pd
import pytest

from teaser_model_v1.analysis.backtest import (
    LEG_COLUMNS,
    build_leg_records,
    enumerate_tickets,
    primary_before_guardrail,
    qualifying_primary,
    run_season,
    season_weeks,
    week_top_legs,
)
from teaser_model_v1.analysis.grading import assert_no_primary_push


def synthetic_games(rows):
    """rows: (week, away, home, spread_line, total_line, away_score, home_score)."""
    out = []
    for i, (week, away, home, spread, total, ascore, hscore) in enumerate(rows):
        out.append(
            {
                "game_id": f"2024_{week:02d}_{away}_{home}",
                "season": 2024,
                "game_type": "REG",
                "week": week,
                "gameday": "2024-09-08",
                "away_team": away,
                "home_team": home,
                "away_score": ascore,
                "home_score": hscore,
                "result": hscore - ascore,
                "total": hscore + ascore,
                "spread_line": spread,
                "total_line": total,
            }
        )
    return pd.DataFrame(out)


def legs_from(games):
    from teaser_model_v1.ingest import nflverse

    return nflverse.to_legs(games)


@pytest.fixture
def records():
    games = synthetic_games(
        [
            # week 1: home favoured by 1.5 (home -1.5 secondary, away +1.5 primary)
            (1, "AAA", "BBB", 1.5, 40.0, 20, 23),
            # week 1: away favoured by 7.5 (away -7.5 primary), total 44
            (1, "CCC", "DDD", -7.5, 44.0, 31, 17),
            # week 1: total above the guardrail -> primary shape, fails guardrail
            (1, "EEE", "FFF", 2.5, 50.0, 20, 24),
            # week 2: no primary shapes at all
            (2, "GGG", "HHH", 3.5, 42.0, 10, 20),
            # week 3: two primary legs
            (3, "III", "JJJ", 2.5, 41.0, 17, 20),
            (3, "KKK", "LLL", -8.5, 38.0, 30, 10),
        ]
    )
    return build_leg_records(legs_from(games)), games


def test_leg_records_have_the_required_columns(records):
    frame, _ = records
    assert list(frame.columns) == LEG_COLUMNS
    for column in (
        "season",
        "week",
        "gameday",
        "team",
        "side",
        "archived_reference_line",
        "teased_line",
        "game_total",
        "geometry_class",
        "p_raw",
        "bump",
        "p_est",
        "final_margin",
        "outcome",
    ):
        assert column in frame.columns


def test_the_line_column_is_never_called_a_closing_line(records):
    frame, _ = records
    assert "archived_reference_line" in frame.columns
    assert not any("clos" in column.lower() for column in frame.columns)
    assert (frame["line_provenance"] == "archived_reference_line").all()


def test_primary_filter_before_and_after_the_guardrail(records):
    frame, _ = records
    before = primary_before_guardrail(frame)
    after = qualifying_primary(frame)

    # Primary shapes: AAA(+1.5), CCC(-7.5), EEE(+2.5, total 50), III(+2.5), KKK(-8.5)
    assert len(before) == 5
    # EEE fails the guardrail at total 50.
    assert len(after) == 4
    dropped = set(before["leg_id"]) - set(after["leg_id"])
    assert dropped == {"2024_01_EEE_FFF-EEE"}


def test_grading_matches_hand_calculation(records):
    frame, _ = records
    by_id = frame.set_index("leg_id")

    # AAA +1.5 -> +7.5, lost by 3 -> WIN
    assert by_id.loc["2024_01_AAA_BBB-AAA", "final_margin"] == -3
    assert by_id.loc["2024_01_AAA_BBB-AAA", "outcome"] == "WIN"

    # CCC -7.5 -> -1.5, won by 14 -> WIN
    assert by_id.loc["2024_01_CCC_DDD-CCC", "outcome"] == "WIN"

    # III +2.5 -> +8.5, lost by 3 -> WIN
    assert by_id.loc["2024_03_III_JJJ-III", "outcome"] == "WIN"

    # KKK -8.5 -> -2.5, won by 20 -> WIN
    assert by_id.loc["2024_03_KKK_LLL-KKK", "outcome"] == "WIN"

    # LLL +8.5 -> +14.5, lost by 20 -> LOSS
    assert by_id.loc["2024_03_KKK_LLL-LLL", "outcome"] == "LOSS"


def test_no_primary_leg_pushes_in_synthetic_data(records):
    frame, _ = records
    assert_no_primary_push(frame.to_dict("records"))


def test_p_est_components_add_up(records):
    frame, _ = records
    assert (frame["p_est"] - (frame["p_raw"] + frame["bump"])).abs().max() < 1e-12


def test_weekly_grouping_includes_zero_qualifier_weeks(records):
    frame, games = records
    result = run_season(frame, games, 2024)
    weekly = result["weekly"]

    assert list(weekly["week"]) == [1, 2, 3]
    assert season_weeks(games, 2024) == [1, 2, 3]

    counts = dict(zip(weekly["week"], weekly["n_qualifying_legs"]))
    assert counts == {1: 2, 2: 0, 3: 2}
    # Week 2 is present with a zero, not missing.
    assert 2 in counts


def test_weeks_with_fewer_than_two_qualifying_legs_construct_nothing():
    games = synthetic_games([(1, "AAA", "BBB", 1.5, 40.0, 20, 23)])
    frame = build_leg_records(legs_from(games))
    result = run_season(frame, games, 2024)
    assert result["weekly"].iloc[0]["n_qualifying_legs"] == 1
    assert not result["weekly"].iloc[0]["constructible"]
    assert result["tickets"].empty


def test_top_four_ranking_is_by_p_est_descending():
    # Five primary legs in one week; lower total -> higher P_est.
    games = synthetic_games(
        [
            (1, "A1", "B1", 1.5, 46.0, 10, 13),
            (1, "A2", "B2", 1.5, 44.0, 10, 13),
            (1, "A3", "B3", 1.5, 42.0, 10, 13),
            (1, "A4", "B4", 1.5, 40.0, 10, 13),
            (1, "A5", "B5", 1.5, 38.0, 10, 13),
        ]
    )
    frame = qualifying_primary(build_leg_records(legs_from(games)))
    top = week_top_legs(frame)

    assert len(top) == 4
    assert list(top["rank"]) == [1, 2, 3, 4]
    assert list(top["game_total"]) == [38.0, 40.0, 42.0, 44.0]
    assert list(top["p_est"]) == sorted(top["p_est"], reverse=True)
    # The 46.0 leg is the one dropped.
    assert 46.0 not in set(top["game_total"])


def test_ticket_enumeration_counts_and_grading():
    games = synthetic_games(
        [
            (1, "A1", "B1", 1.5, 38.0, 10, 13),  # A1 +1.5 -> +7.5, lost by 3 -> WIN
            (1, "A2", "B2", 1.5, 40.0, 10, 13),  # WIN
            (1, "A3", "B3", 1.5, 42.0, 10, 13),  # WIN
            (1, "A4", "B4", 1.5, 44.0, 10, 30),  # lost by 20 -> LOSS
        ]
    )
    frame = qualifying_primary(build_leg_records(legs_from(games)))
    top = week_top_legs(frame)
    tickets = enumerate_tickets(top)

    assert len(tickets) == 10  # C(4,2)=6 plus C(4,3)=4
    assert sum(1 for t in tickets if t["n_legs"] == 2) == 6
    assert sum(1 for t in tickets if t["n_legs"] == 3) == 4

    # Three winners and one loser: 2-team tickets avoiding the loser = C(3,2) = 3.
    assert sum(1 for t in tickets if t["n_legs"] == 2 and t["won"]) == 3
    # 3-team tickets avoiding the loser = C(3,3) = 1.
    assert sum(1 for t in tickets if t["n_legs"] == 3 and t["won"]) == 1


def test_ticket_probability_is_the_product_of_leg_p_est():
    games = synthetic_games(
        [
            (1, "A1", "B1", 1.5, 38.0, 10, 13),
            (1, "A2", "B2", 1.5, 40.0, 10, 13),
        ]
    )
    frame = qualifying_primary(build_leg_records(legs_from(games)))
    top = week_top_legs(frame)
    tickets = enumerate_tickets(top)
    assert len(tickets) == 1
    expected = float(top["p_est"].iloc[0]) * float(top["p_est"].iloc[1])
    assert tickets[0]["predicted_p_ticket"] == pytest.approx(expected, abs=1e-12)


def test_no_ticket_can_contain_both_sides_of_one_game(records):
    frame, games = records
    result = run_season(frame, games, 2024)
    if not result["tickets"].empty:
        assert not result["tickets"]["same_game_legs"].any()


def test_outputs_are_reproducible(records):
    """Running the same inputs twice must produce byte-identical frames."""
    frame, games = records
    first = run_season(frame, games, 2024)
    second = run_season(build_leg_records(legs_from(games)), games, 2024)

    for key in ("qualifying", "weekly", "top_legs", "tickets"):
        left = first[key].reset_index(drop=True)
        right = second[key].reset_index(drop=True)
        pd.testing.assert_frame_equal(left, right)


def test_csv_round_trip_is_stable(records, tmp_path):
    frame, games = records
    result = run_season(frame, games, 2024)
    path = tmp_path / "legs.csv"
    result["qualifying"].to_csv(path, index=False)
    reloaded = pd.read_csv(path)
    assert len(reloaded) == len(result["qualifying"])
    assert list(reloaded.columns) == list(result["qualifying"].columns)
    assert reloaded["p_est"].sum() == pytest.approx(
        result["qualifying"]["p_est"].sum(), abs=1e-9
    )
