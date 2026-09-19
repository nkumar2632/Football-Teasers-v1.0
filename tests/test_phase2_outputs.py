"""Integration checks on the real Phase 2 outputs.

Skipped when the processed data has not been generated, so the suite still runs on a
fresh checkout.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
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


# ---------------------------------------------------------------------------------------
# Phase 2B: the 2018-2023 validation block.
# ---------------------------------------------------------------------------------------

VALIDATION_SEASONS = (2018, 2019, 2020, 2021, 2022, 2023)

phase2b = pytest.mark.skipif(
    not (PROCESSED / "nfl_legs_2018_2023.csv").exists(),
    reason="2018-2023 data not present; run scripts/ingest_nfl.py --seasons 2018..2023",
)


@pytest.fixture(scope="module")
def validation_real():
    games = pd.read_csv(PROCESSED / "nfl_games_2018_2023.csv")
    legs = pd.read_csv(PROCESSED / "nfl_legs_2018_2023.csv")
    return build_leg_records(legs), games


@phase2b
def test_no_primary_push_in_any_validation_season(validation_real):
    records, _ = validation_real
    assert_no_primary_push(records.to_dict("records"))


@phase2b
def test_validation_seasons_all_satisfy_the_frozen_filters(validation_real):
    records, games = validation_real
    for season in VALIDATION_SEASONS:
        qualifying = run_season(records, games, season)["qualifying"]
        assert len(qualifying) > 0
        assert (qualifying["geometry_class"] == "PRIMARY").all()
        assert (qualifying["track"] == "LIVE").all()
        assert (qualifying["game_total"] <= 47).all()
        assert (qualifying["key_numbers_crossed"] == 2).all()
        assert (qualifying["bump"].round(10) == 0.07).all()
        assert set(qualifying["outcome"]) <= {"WIN", "LOSS"}
        assert (qualifying["cover_margin"] != 0).all()
        assert set(qualifying["teased_line"]) <= {7.5, 8.5, -1.5, -2.5}


@phase2b
def test_every_validation_season_passed_the_unchanged_data_quality_gate():
    """The gate is not weakened for Phase 2B; each season must pass on its own."""
    import json

    for season in VALIDATION_SEASONS:
        path = ROOT / "reports" / f"DATA_QUALITY_NFL_{season}.json"
        if not path.exists():
            pytest.skip(f"per-season audit for {season} not generated yet")
        payload = json.loads(path.read_text())
        assert payload["verdict"] == "PASS", (
            f"{season} failed the data-quality gate: "
            f"{[c['name'] for c in payload['checks'] if c['status'] == 'FAIL']}"
        )
        # The gate itself must be the frozen one.
        assert payload["thresholds"]["min_half_point_share"] == 0.40
        assert payload["thresholds"]["max_missing_share"] == 0.01


@phase2b
def test_side_class_partitions_the_primary_shapes(validation_real):
    records, games = validation_real
    for season in VALIDATION_SEASONS:
        qualifying = run_season(records, games, season)["qualifying"]
        dogs = qualifying[qualifying["shape"].isin(("+1.5", "+2.5"))]
        favorites = qualifying[qualifying["shape"].isin(("-7.5", "-8.5"))]
        assert len(dogs) + len(favorites) == len(qualifying)
        assert (dogs["side_class"] == "DOG").all()
        assert (favorites["side_class"] == "FAVORITE").all()


@phase2b
def test_no_validation_ticket_contains_two_legs_from_one_game(validation_real):
    records, games = validation_real
    for season in VALIDATION_SEASONS:
        tickets = run_season(records, games, season)["tickets"]
        if len(tickets):
            assert not tickets["same_game_legs"].any()


@phase2b
def test_phase2b_outputs_carry_no_price_ev_or_roi_column():
    forbidden = ("price", "ev", "roi", "profit", "break_even", "odds", "stake", "unit")
    paths = list(PROCESSED.glob("phase2b_*.csv"))
    if not paths:
        pytest.skip("phase2b CSVs not generated yet")
    for path in paths:
        for column in [c.lower() for c in pd.read_csv(path, nrows=0).columns]:
            assert not any(
                token == column
                or column.startswith(token + "_")
                or column.endswith("_" + token)
                for token in forbidden
            ), f"{path.name} carries pricing column {column!r}"


@phase2b
def test_phase2b_reports_never_describe_the_line_as_a_close():
    for name in (
        "phase2b_nfl_2018_2023_validation.md",
        "phase2b_dog_favorite_validation.md",
        "phase2b_total_dependence.md",
    ):
        path = ROOT / "reports" / name
        if not path.exists():
            pytest.skip(f"{name} not generated yet")
        text = path.read_text().lower()
        assert "true_timestamped_close" not in text
        for line in text.splitlines():
            if "closing line" in line:
                assert "not" in line, f"unqualified 'closing line' in {name}: {line}"


@phase2b
def test_validation_run_is_reproducible(validation_real):
    records, games = validation_real
    first = run_season(records, games, 2021)
    second = run_season(records, games, 2021)
    for key in ("qualifying", "weekly", "top_legs", "tickets"):
        pd.testing.assert_frame_equal(
            first[key].reset_index(drop=True), second[key].reset_index(drop=True)
        )


# ---------------------------------------------------------------------------------------
# Phase 2C: independence audit outputs.
# ---------------------------------------------------------------------------------------

phase2c = pytest.mark.skipif(
    not (PROCESSED / "phase2c_permutation.csv").exists(),
    reason="Phase 2C not generated; run scripts/run_phase2c_independence_audit.py",
)


@phase2c
def test_phase2c_simulation_csvs_carry_their_run_metadata():
    """A reader must be able to audit reproducibility from the CSV alone."""
    mc = pd.read_csv(PROCESSED / "phase2c_monte_carlo.csv")
    perm = pd.read_csv(PROCESSED / "phase2c_permutation.csv")

    for frame in (mc, perm):
        for column in ("n_sims", "seed", "n_legs"):
            assert column in frame.columns
        assert (frame["n_sims"] >= 100_000).all()
        assert frame["seed"].nunique() == 1

    # Permutation integrity fields, without which the scheme cannot be checked.
    for column in ("scheme", "strata", "permutable_strata", "legs_held_fixed"):
        assert column in perm.columns
    assert set(perm["scheme"]) == {"P1", "P2"}


@phase2c
def test_phase2c_permutation_was_not_degenerate_on_the_real_blocks():
    """Every real block must have had something to permute, or its p-value means nothing."""
    perm = pd.read_csv(PROCESSED / "phase2c_permutation.csv")
    assert (perm["permutable_strata"] > 0).all()
    assert (perm["legs_held_fixed"] == 0).all()


@phase2c
def test_phase2c_p_values_are_within_the_monte_carlo_bounds():
    for name in ("phase2c_monte_carlo.csv", "phase2c_permutation.csv"):
        frame = pd.read_csv(PROCESSED / name)
        # The "leg wins" row is a descriptive distribution, not a test, so it carries no
        # p-value. Every row that does carry one must respect the +1-corrected bounds.
        tested = frame[frame["p_value_one_sided"].notna()]
        assert len(tested) > 0
        lower = 1.0 / (tested["n_sims"] + 1)
        assert (tested["p_value_one_sided"] >= lower - 1e-12).all()
        assert (tested["p_value_one_sided"] <= 1.0).all()
        assert frame.loc[frame["p_value_one_sided"].isna(), "statistic"].eq(
            "leg wins"
        ).all()


@phase2c
def test_phase2c_week_diagnostics_are_internally_consistent():
    weeks = pd.read_csv(PROCESSED / "phase2c_week_diagnostics.csv")
    assert (weeks["n_legs"] >= 2).all()
    assert (weeks["n_dogs"] + weeks["n_favorites"] == weeks["n_legs"]).all()
    assert (weeks["dog_fraction"].between(0.0, 1.0)).all()
    # all_win is exactly "every qualifying leg in the week won".
    assert (weeks["all_win"] == (weeks["wins"] == weeks["n_legs"]).astype(int)).all()
    assert (weeks["expected_all_win_prob"].between(0.0, 1.0)).all()


@phase2c
def test_phase2c_same_week_pairs_are_different_games_and_same_week():
    pairs = pd.read_csv(PROCESSED / "phase2c_same_week_pairs.csv")
    assert len(pairs) > 0
    assert (pairs["leg_a"] != pairs["leg_b"]).all()
    assert np.allclose(
        pairs["resid_product"], pairs["resid_a"] * pairs["resid_b"], atol=1e-12
    )
    assert np.allclose(pairs["expected_joint"], pairs["p_a"] * pairs["p_b"], atol=1e-12)
    assert (pairs["joint_win"] == (pairs["y_a"] * pairs["y_b"])).all()


@phase2c
def test_phase2c_outputs_carry_no_price_ev_or_roi_column():
    forbidden = ("price", "ev", "roi", "profit", "break_even", "odds", "stake", "unit")
    for path in PROCESSED.glob("phase2c_*.csv"):
        for column in [c.lower() for c in pd.read_csv(path, nrows=0).columns]:
            assert not any(
                token == column
                or column.startswith(token + "_")
                or column.endswith("_" + token)
                for token in forbidden
            ), f"{path.name} carries pricing column {column!r}"


@phase2c
def test_phase2c_reports_exist_and_avoid_closing_line_language():
    for name in (
        "phase2c_independence_audit.md",
        "phase2c_monte_carlo.md",
        "phase2c_permutation.md",
    ):
        path = ROOT / "reports" / name
        assert path.exists(), f"{name} missing"
        text = path.read_text().lower()
        assert "true_timestamped_close" not in text
        for line in text.splitlines():
            if "closing line" in line:
                assert "not" in line, f"unqualified 'closing line' in {name}: {line}"


@phase2c
def test_phase2c_monte_carlo_reproduces_on_the_real_board():
    """Re-running the simulation on the real board must reproduce the published numbers."""
    from teaser_model_v1.analysis.dependence import make_block, monte_carlo_null

    games = pd.read_csv(PROCESSED / "nfl_games_2024_2025.csv")
    records = build_leg_records(pd.read_csv(PROCESSED / "nfl_legs_2024_2025.csv"))
    run = run_season(records, games, 2025)
    block = make_block("2025", run["qualifying"], run["tickets"])

    published = pd.read_csv(PROCESSED / "phase2c_monte_carlo.csv")
    row = published[
        (published["block"] == "2025") & (published["statistic"] == "2-team hit rate")
    ].iloc[0]

    result = monte_carlo_null(block, n_sims=int(row["n_sims"]), seed=int(row["seed"]))
    assert result["2team"]["sim_mean"] == pytest.approx(row["sim_mean"], abs=1e-12)
    assert result["2team"]["p_value_one_sided"] == pytest.approx(
        row["p_value_one_sided"], abs=1e-12
    )
    assert result["2team"]["observed_hit_rate"] == pytest.approx(
        row["observed_hit_rate"], abs=1e-12
    )


# ---------------------------------------------------------------------------------------
# Phase 3: pricing sensitivity outputs.
# ---------------------------------------------------------------------------------------

phase3 = pytest.mark.skipif(
    not (PROCESSED / "phase3_price_grid.csv").exists(),
    reason="Phase 3 not generated; run scripts/run_phase3_pricing.py",
)


@phase3
def test_phase3_reports_disclaim_their_prices_correctly():
    """Each report must disclaim the right thing.

    The two grid reports carry hypothetical prices and must say so. The fair-price report
    carries no hypothetical price at all — it reports model-implied fair value — so it must
    instead disclaim that its prices were ever offered.
    """
    for name in ("phase3_pricing_sensitivity.md", "phase3_historical_price_frontier.md"):
        lowered = (ROOT / "reports" / name).read_text().lower()
        assert "hypothetical" in lowered

    fair = (ROOT / "reports" / "phase3_fair_price_distribution.md").read_text().lower()
    assert "not** a price any sportsbook offered" in fair or (
        "not a price any sportsbook offered" in fair
    )

    for name in (
        "phase3_pricing_sensitivity.md",
        "phase3_historical_price_frontier.md",
        "phase3_fair_price_distribution.md",
    ):
        path = ROOT / "reports" / name
        assert path.exists(), f"{name} missing"
        lowered = path.read_text().lower()
        # The two price objects must never be presented as the same thing.
        if "break-even" in lowered:
            assert "model-implied" in lowered or "historical outcome" in lowered
        # No unqualified claim of a realized or backtested return.
        for phrase in ("realized roi", "backtested return", "actual historical price"):
            for line in lowered.splitlines():
                if phrase in line:
                    assert any(
                        negation in line for negation in ("not ", "never", "unknown")
                    ), f"unqualified {phrase!r} in {name}: {line}"


@phase3
def test_phase3_grid_prices_are_exactly_the_declared_points():
    from teaser_model_v1.analysis.pricing_sensitivity import GRID_2TEAM, GRID_3TEAM

    grid = pd.read_csv(PROCESSED / "phase3_price_grid.csv")
    two = grid[grid["scenario"] == "2-team only"]["american_2team"].dropna().unique()
    three = grid[grid["scenario"] == "3-team only"]["american_3team"].dropna().unique()
    assert set(two) == set(float(p) for p in GRID_2TEAM)
    assert set(three) == set(float(p) for p in GRID_3TEAM)
    assert set(grid["procedure"]) == {"frozen greedy + cap", "flat eligibility (control)"}


@phase3
def test_phase3_profit_and_loss_reconciles_with_wins_and_losses():
    grid = pd.read_csv(PROCESSED / "phase3_price_grid.csv")
    single = grid[
        (grid["scenario"] == "2-team only") & (grid["tickets_selected"] > 0)
    ].copy()
    profit = 100.0 / single["american_2team"].abs()
    expected = single["wins"] * profit - single["losses"]
    assert np.allclose(single["hypothetical_profit_loss"], expected, atol=1e-9)
    assert (single["wins"] + single["losses"] == single["tickets_selected"]).all()
    assert np.allclose(
        single["hypothetical_roi"],
        single["hypothetical_profit_loss"] / single["units_staked"],
        atol=1e-12,
    )


@phase3
def test_phase3_exposure_cap_is_never_violated():
    weekly = pd.read_csv(PROCESSED / "phase3_weekly_cards.csv")
    frozen = weekly[weekly["procedure"] == "frozen greedy + cap"]
    assert (frozen["max_leg_exposure"] <= 2).all()


@phase3
def test_phase3_selected_is_always_a_subset_of_positive_ev():
    grid = pd.read_csv(PROCESSED / "phase3_price_grid.csv")
    assert (grid["tickets_selected"] <= grid["eligible_positive_ev_tickets"]).all()
    flat = grid[grid["procedure"] == "flat eligibility (control)"]
    # The control keeps everything positive EV, by definition.
    assert (flat["tickets_selected"] == flat["eligible_positive_ev_tickets"]).all()


@phase3
def test_phase3_better_prices_never_select_fewer_tickets():
    grid = pd.read_csv(PROCESSED / "phase3_price_grid.csv")
    frozen = grid[
        (grid["procedure"] == "frozen greedy + cap") & (grid["scenario"] == "3-team only")
    ]
    for _, block in frozen.groupby("block"):
        ordered = block.sort_values("american_3team")
        assert (ordered["eligible_positive_ev_tickets"].diff().dropna() >= 0).all()


@phase3
def test_phase3_fair_price_csv_is_internally_consistent():
    fair = pd.read_csv(PROCESSED / "phase3_ticket_fair_prices.csv")
    assert np.allclose(fair["fair_decimal_odds"], 1.0 + fair["fair_profit"], atol=1e-12)
    assert np.allclose(
        fair["break_even_probability"], fair["predicted_p_ticket"], atol=1e-12
    )
    assert np.allclose(
        fair["fair_profit"],
        (1 - fair["predicted_p_ticket"]) / fair["predicted_p_ticket"],
        atol=1e-12,
    )


@phase3
def test_phase3_frontier_curves_are_reproducible():
    from teaser_model_v1.analysis.pricing_sensitivity import breakeven_frontier

    games = pd.read_csv(PROCESSED / "nfl_games_2024_2025.csv")
    records = build_leg_records(pd.read_csv(PROCESSED / "nfl_legs_2024_2025.csv"))
    qualifying = run_season(records, games, 2025)["qualifying"]

    published = pd.read_csv(PROCESSED / "phase3_frontier_curves.csv")
    subset = published[
        (published["block"] == "2025") & (published["ticket_size"] == "2-team")
    ].reset_index(drop=True)

    recomputed = breakeven_frontier(qualifying, 2, block="2025").curve.reset_index(drop=True)
    assert len(recomputed) == len(subset)
    assert np.allclose(recomputed["profit_loss"], subset["profit_loss"], atol=1e-9)
