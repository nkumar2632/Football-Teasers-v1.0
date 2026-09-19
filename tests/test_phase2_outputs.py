"""Integration checks on the real Phase 2 outputs.

Skipped when the processed data has not been generated, so the suite still runs on a
fresh checkout.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from teaser_model_v1.analysis.backtest import build_leg_records, run_season
from teaser_model_v1.analysis.grading import assert_no_primary_push

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

pytestmark = pytest.mark.skipif(
    not (PROCESSED / "nfl_legs_2024_2025.csv").exists(),
    reason="processed NFL data not present; run scripts/ingest_nfl.py first",
)


@pytest.fixture(scope="module")
def real():
    games = pd.read_csv(PROCESSED / "nfl_games_2024_2025.csv")
    legs = pd.read_csv(PROCESSED / "nfl_legs_2024_2025.csv")
    return build_leg_records(legs), games


def test_no_primary_leg_pushes_in_the_real_data(real):
    records, _ = real
    assert_no_primary_push(records.to_dict("records"))


def test_every_qualifying_leg_satisfies_the_frozen_filters(real):
    records, games = real
    for season in (2024, 2025):
        qualifying = run_season(records, games, season)["qualifying"]
        assert (qualifying["geometry_class"] == "PRIMARY").all()
        assert (qualifying["track"] == "LIVE").all()
        assert (qualifying["game_total"] <= 47).all()
        assert (qualifying["key_numbers_crossed"] == 2).all()
        assert (qualifying["bump"].round(10) == 0.07).all()
        assert (qualifying["p_est"] - (qualifying["p_raw"] + qualifying["bump"])).abs().max() < 1e-12
        assert set(qualifying["outcome"]) <= {"WIN", "LOSS"}
        # Every teased primary line is a half-point, so no cover margin can be zero.
        assert (qualifying["cover_margin"] != 0).all()


def test_teased_lines_are_exactly_the_four_primary_targets(real):
    records, games = real
    for season in (2024, 2025):
        qualifying = run_season(records, games, season)["qualifying"]
        assert set(qualifying["teased_line"]) <= {7.5, 8.5, -1.5, -2.5}


def test_weekly_counts_reconcile_with_the_leg_rows(real):
    records, games = real
    for season in (2024, 2025):
        result = run_season(records, games, season)
        weekly, qualifying = result["weekly"], result["qualifying"]
        assert weekly["n_qualifying_legs"].sum() == len(qualifying)
        # Every week in the schedule appears, including zero-qualifier weeks.
        assert len(weekly) == games.loc[games["season"] == season, "week"].nunique()


def test_ticket_counts_match_the_combinatorics_of_each_week(real):
    from math import comb

    records, games = real
    for season in (2024, 2025):
        result = run_season(records, games, season)
        weekly, tickets = result["weekly"], result["tickets"]
        expected_2 = sum(comb(min(n, 4), 2) for n in weekly["n_qualifying_legs"] if n >= 2)
        expected_3 = sum(comb(min(n, 4), 3) for n in weekly["n_qualifying_legs"] if n >= 3)
        assert int((tickets["n_legs"] == 2).sum()) == expected_2
        assert int((tickets["n_legs"] == 3).sum()) == expected_3


def test_no_ticket_contains_two_legs_from_the_same_game(real):
    records, games = real
    for season in (2024, 2025):
        tickets = run_season(records, games, season)["tickets"]
        assert not tickets["same_game_legs"].any()


def test_a_ticket_wins_exactly_when_all_its_legs_win(real):
    records, games = real
    for season in (2024, 2025):
        result = run_season(records, games, season)
        tickets = result["tickets"]
        assert (tickets["won"] == (tickets["n_legs_winning"] == tickets["n_legs"]).astype(int)).all()


def test_phase2_outputs_carry_no_price_ev_or_roi_column():
    """Phase 2 is calibration only; no pricing may leak into its outputs."""
    forbidden = ("price", "ev", "roi", "profit", "break_even", "odds", "stake", "unit")
    for path in PROCESSED.glob("phase2_*.csv"):
        columns = [c.lower() for c in pd.read_csv(path, nrows=0).columns]
        for column in columns:
            assert not any(
                token == column or column.startswith(token + "_") or column.endswith("_" + token)
                for token in forbidden
            ), f"{path.name} carries pricing column {column!r}"


def test_reports_never_describe_the_line_as_a_close():
    for name in (
        "phase2_nfl_2024_calibration.md",
        "phase2_nfl_2025_calibration.md",
        "phase2_nfl_comparison.md",
    ):
        path = ROOT / "reports" / name
        if not path.exists():
            pytest.skip(f"{name} not generated yet")
        text = path.read_text().lower()
        assert "archived reference line" in text or "archived_reference_line" in text
        assert "true_timestamped_close" not in text
        # Any mention of "closing line" must be a denial, not a claim.
        for line in text.splitlines():
            if "closing line" in line:
                assert "not" in line, f"unqualified 'closing line' in {name}: {line}"


def test_real_run_is_reproducible(real):
    records, games = real
    first = run_season(records, games, 2025)
    second = run_season(records, games, 2025)
    for key in ("qualifying", "weekly", "top_legs", "tickets"):
        pd.testing.assert_frame_equal(
            first[key].reset_index(drop=True), second[key].reset_index(drop=True)
        )
