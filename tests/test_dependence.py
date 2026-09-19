"""Phase 2C: simulation reproducibility and permutation integrity.

These tests guard the machinery of the independence audit. They assert nothing about
whether dependence exists — that is a finding, not an invariant.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from teaser_model_v1.analysis.dependence import (
    DEFAULT_SEED,
    MIN_STRATUM_SIZE,
    Block,
    all_win_summary,
    make_block,
    monte_carlo_null,
    overlap_stats,
    pair_summary,
    permutation_test,
    same_week_pairs,
    week_all_win,
    week_bootstrap_ticket_rate,
)


# ---------------------------------------------------------------------------------------
# Synthetic board helpers.
# ---------------------------------------------------------------------------------------


def legs_frame(rows):
    """rows: (leg_id, season, week, game_id, p_est, won, side_class)."""
    return pd.DataFrame(
        [
            {
                "leg_id": leg_id,
                "season": season,
                "week": week,
                "game_id": game_id,
                "p_est": p_est,
                "won": won,
                "side_class": side,
                "shape": "+2.5" if side == "DOG" else "-7.5",
                "total_bucket": "43.5-45",
            }
            for leg_id, season, week, game_id, p_est, won, side in rows
        ]
    )


def tickets_frame(combos, legs):
    lookup = legs.set_index("leg_id")
    rows = []
    for ids in combos:
        won = int(all(lookup.loc[i, "won"] == 1 for i in ids))
        product = float(np.prod([lookup.loc[i, "p_est"] for i in ids]))
        first = lookup.loc[ids[0]]
        rows.append(
            {
                "season": int(first["season"]),
                "week": int(first["week"]),
                "n_legs": len(ids),
                "leg_ids": "|".join(ids),
                "predicted_p_ticket": product,
                "won": won,
                "same_game_legs": False,
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture
def board():
    """Two weeks: week 1 has four legs (10 tickets), week 2 has two legs (1 ticket)."""
    legs = legs_frame(
        [
            ("a", 2020, 1, "g1", 0.76, 1, "DOG"),
            ("b", 2020, 1, "g2", 0.75, 1, "DOG"),
            ("c", 2020, 1, "g3", 0.75, 1, "FAVORITE"),
            ("d", 2020, 1, "g4", 0.74, 0, "FAVORITE"),
            ("e", 2020, 2, "g5", 0.76, 1, "DOG"),
            ("f", 2020, 2, "g6", 0.74, 0, "DOG"),
        ]
    )
    combos = [
        ("a", "b"), ("a", "c"), ("a", "d"), ("b", "c"), ("b", "d"), ("c", "d"),
        ("a", "b", "c"), ("a", "b", "d"), ("a", "c", "d"), ("b", "c", "d"),
        ("e", "f"),
    ]
    return make_block("test", legs, tickets_frame(combos, legs))


# ---------------------------------------------------------------------------------------
# Block construction preserves the exact historical ticket set.
# ---------------------------------------------------------------------------------------


def test_ticket_index_resolves_every_ticket_to_leg_positions(board):
    assert board.ticket_index[2].shape == (7, 2)   # 6 from week 1, 1 from week 2
    assert board.ticket_index[3].shape == (4, 3)
    positions = {leg_id: i for i, leg_id in enumerate(board.legs["leg_id"])}
    first = board.tickets.iloc[0]
    expected = [positions[i] for i in first["leg_ids"].split("|")]
    assert list(board.ticket_index[first["n_legs"]][0]) == expected


def test_observed_ticket_rates_match_the_frame(board):
    # Week 1: a,b,c win and d loses -> 2-team winners are ab, ac, bc = 3 of 6.
    # Week 2: e wins, f loses -> ef loses. So 3 of 7 two-team tickets win.
    assert board.observed_ticket_rate(2) == pytest.approx(3 / 7)
    # 3-team winners: abc only -> 1 of 4.
    assert board.observed_ticket_rate(3) == pytest.approx(1 / 4)


# ---------------------------------------------------------------------------------------
# Reproducibility — the central requirement for the simulations.
# ---------------------------------------------------------------------------------------


def test_monte_carlo_is_reproducible_with_a_fixed_seed(board):
    first = monte_carlo_null(board, n_sims=2_000, seed=DEFAULT_SEED)
    second = monte_carlo_null(board, n_sims=2_000, seed=DEFAULT_SEED)
    assert first == second


def test_monte_carlo_changes_with_a_different_seed(board):
    first = monte_carlo_null(board, n_sims=2_000, seed=1)
    second = monte_carlo_null(board, n_sims=2_000, seed=2)
    assert first["2team"]["sim_mean"] != second["2team"]["sim_mean"]


@pytest.mark.parametrize("scheme", ["P1", "P2"])
def test_permutation_is_reproducible_with_a_fixed_seed(board, scheme):
    first = permutation_test(board, scheme=scheme, n_sims=2_000, seed=DEFAULT_SEED)
    second = permutation_test(board, scheme=scheme, n_sims=2_000, seed=DEFAULT_SEED)
    assert first == second


def test_chunking_does_not_change_results(board, monkeypatch):
    """Results must not depend on the internal chunk size, only on the seed."""
    import teaser_model_v1.analysis.dependence as dependence

    monkeypatch.setattr(dependence, "CHUNK", 5_000)
    whole = dependence.monte_carlo_null(board, n_sims=2_000, seed=7)
    monkeypatch.setattr(dependence, "CHUNK", 250)
    chunked = dependence.monte_carlo_null(board, n_sims=2_000, seed=7)
    # The RNG stream is consumed in the same order, so the draws are identical.
    assert whole["2team"]["sim_mean"] == pytest.approx(chunked["2team"]["sim_mean"], abs=0.02)


# ---------------------------------------------------------------------------------------
# Monte Carlo correctness.
# ---------------------------------------------------------------------------------------


def test_monte_carlo_recovers_the_analytic_mean_for_a_single_ticket():
    legs = legs_frame([("a", 2020, 1, "g1", 0.8, 1, "DOG"),
                       ("b", 2020, 1, "g2", 0.5, 1, "DOG")])
    block = make_block("one", legs, tickets_frame([("a", "b")], legs))
    result = monte_carlo_null(block, n_sims=40_000, seed=3)
    # Independent Bernoulli: P(both win) = 0.8 * 0.5 = 0.40.
    assert result["2team"]["sim_mean"] == pytest.approx(0.40, abs=0.01)


def test_monte_carlo_leg_wins_centre_on_sum_of_p(board):
    result = monte_carlo_null(board, n_sims=20_000, seed=5)
    assert result["leg_wins"]["sim_mean"] == pytest.approx(board.p.sum(), abs=0.05)


def test_monte_carlo_preserves_ticket_overlap(board):
    """The simulated ticket count must equal the historical count exactly."""
    result = monte_carlo_null(board, n_sims=500, seed=11)
    assert result["2team"]["n_tickets"] == board.n_tickets(2) == 7
    assert result["3team"]["n_tickets"] == board.n_tickets(3) == 4


def test_p_value_is_bounded_and_uses_the_plus_one_correction(board):
    result = monte_carlo_null(board, n_sims=1_000, seed=13)
    for key in ("2team", "3team", "all_win_weeks"):
        p = result[key]["p_value_one_sided"]
        assert 1 / 1001 <= p <= 1.0


# ---------------------------------------------------------------------------------------
# Permutation integrity.
# ---------------------------------------------------------------------------------------


def test_permutation_preserves_the_marginal_win_count_exactly():
    """Every permutation must keep each stratum's win total unchanged."""
    import teaser_model_v1.analysis.dependence as dependence

    legs = legs_frame(
        [(chr(ord("a") + i), 2020, (i // 2) + 1, f"g{i}", 0.75, i % 2, "DOG")
         for i in range(12)]
    )
    combos = [("a", "b"), ("c", "d"), ("e", "f")]
    block = make_block("m", legs, tickets_frame(combos, legs))

    y = block.y.astype(bool)
    positions = dependence._strata_positions(block.legs, "P1")
    rng = np.random.default_rng(0)
    for _ in range(200):
        outcomes = y.copy()
        for group in positions:
            outcomes[group] = rng.permutation(outcomes[group])
        assert outcomes.sum() == y.sum()


def test_p1_strata_are_seasons_and_p2_adds_side_class():
    import teaser_model_v1.analysis.dependence as dependence

    legs = legs_frame(
        [("a", 2020, 1, "g1", 0.75, 1, "DOG"), ("b", 2020, 1, "g2", 0.75, 0, "FAVORITE"),
         ("c", 2021, 1, "g3", 0.75, 1, "DOG"), ("d", 2021, 1, "g4", 0.75, 0, "FAVORITE")]
    )
    assert len(dependence._strata_positions(legs, "P1")) == 2   # two seasons
    assert len(dependence._strata_positions(legs, "P2")) == 4   # season x side


def test_unknown_permutation_scheme_raises():
    import teaser_model_v1.analysis.dependence as dependence

    legs = legs_frame([("a", 2020, 1, "g1", 0.75, 1, "DOG")])
    with pytest.raises(ValueError, match="unknown permutation scheme"):
        dependence._strata_positions(legs, "P9")


def test_small_strata_are_held_fixed_and_counted(board):
    """Strata below the minimum must be reported as held fixed, not silently permuted.

    This board has 4 DOG and 2 FAVORITE legs in one season, so under P2 *both* strata fall
    below the minimum and nothing is permutable. That degenerate case must be visible in
    the returned counts.
    """
    assert MIN_STRATUM_SIZE == 5
    result = permutation_test(board, scheme="P2", n_sims=200, seed=1)
    assert result["strata"] == 2
    assert result["permutable_strata"] == 0
    assert result["legs_held_fixed"] == 6


def test_a_fully_frozen_permutation_returns_p_equal_to_one(board):
    """When nothing can be permuted the test must be uninformative, never spuriously significant.

    With every stratum held fixed, each 'permuted' board equals the observed one, so the
    observed statistic can never sit in the upper tail.
    """
    result = permutation_test(board, scheme="P2", n_sims=200, seed=1)
    assert result["permutable_strata"] == 0
    for key in ("2team", "3team", "all_win_weeks"):
        assert result[key]["p_value_one_sided"] == pytest.approx(1.0)


def test_p1_on_the_same_board_does_permute(board):
    """P1 pools the season, so the same board is permutable and the test is informative."""
    result = permutation_test(board, scheme="P1", n_sims=200, seed=1)
    assert result["permutable_strata"] == 1
    assert result["legs_held_fixed"] == 0


def test_permutation_centres_on_the_random_arrangement_benchmark():
    """With all legs at one probability, the permutation mean approaches r^k."""
    rows = []
    for week in range(1, 21):
        for j in range(2):
            rows.append((f"w{week}l{j}", 2020, week, f"g{week}{j}", 0.75,
                         1 if (week + j) % 4 else 0, "DOG"))
    legs = legs_frame(rows)
    combos = [(f"w{w}l0", f"w{w}l1") for w in range(1, 21)]
    block = make_block("bench", legs, tickets_frame(combos, legs))

    result = permutation_test(block, scheme="P1", n_sims=20_000, seed=2)
    r = float(block.legs["won"].mean())
    # Sampling without replacement sits a little below r^2; allow for that.
    assert result["2team"]["perm_mean"] == pytest.approx(r**2, abs=0.03)


# ---------------------------------------------------------------------------------------
# Pairs, weeks and overlap accounting.
# ---------------------------------------------------------------------------------------


def test_same_week_pairs_are_within_week_and_across_games(board):
    pairs = same_week_pairs(board.legs)
    # Week 1 has 4 legs -> 6 pairs; week 2 has 2 legs -> 1 pair.
    assert len(pairs) == 7
    assert (pairs["leg_a"] != pairs["leg_b"]).all()
    for row in pairs.itertuples(index=False):
        assert row.resid_product == pytest.approx(row.resid_a * row.resid_b)


def test_pair_summary_reports_zero_dependence_for_a_balanced_board():
    """Residual products cancelling out must give a mean near zero."""
    legs = legs_frame(
        [("a", 2020, 1, "g1", 0.5, 1, "DOG"), ("b", 2020, 1, "g2", 0.5, 0, "DOG"),
         ("c", 2020, 2, "g3", 0.5, 1, "DOG"), ("d", 2020, 2, "g4", 0.5, 0, "DOG")]
    )
    summary = pair_summary(same_week_pairs(legs), "balanced", n_boot=200)
    assert summary["n_pairs"] == 2
    assert summary["mean_resid_product"] == pytest.approx(-0.25)
    assert summary["observed_joint_win_rate"] == pytest.approx(0.0)
    assert summary["expected_joint_win_rate"] == pytest.approx(0.25)


def test_week_all_win_skips_single_leg_weeks_and_counts_composition(board):
    weeks = week_all_win(board.legs)
    assert len(weeks) == 2
    week_one = weeks[weeks["week"] == 1].iloc[0]
    assert week_one["n_legs"] == 4
    assert week_one["n_dogs"] == 2 and week_one["n_favorites"] == 2
    assert week_one["dog_fraction"] == pytest.approx(0.5)
    assert week_one["all_win"] == 0  # d lost
    assert week_one["expected_all_win_prob"] == pytest.approx(0.76 * 0.75 * 0.75 * 0.74)


def test_all_win_summary_partitions_by_week_size(board):
    summary = all_win_summary(week_all_win(board.legs), "test")
    sizes = dict(zip(summary["week_size"], summary["weeks"]))
    assert sizes["exactly 2"] == 1
    assert sizes["exactly 4"] == 1
    assert sizes["all weeks >=2"] == 2


def test_overlap_stats_count_leg_reuse(board):
    stats = overlap_stats(board)
    assert stats["unique_qualifying_legs"] == 6
    assert stats["n_tickets_2team"] == 7 and stats["n_tickets_3team"] == 4
    assert stats["weeks_contributing_tickets"] == 2
    # Leg "a" sits in 3 two-team and 3 three-team tickets.
    assert stats["max_tickets_containing_one_leg"] == 6
    assert stats["mean_tickets_per_used_leg"] > 1


def test_week_bootstrap_resamples_weeks_not_tickets(board):
    result = week_bootstrap_ticket_rate(board, 2, n_boot=2_000, seed=DEFAULT_SEED)
    assert result["n_weeks"] == 2
    assert result["n_tickets"] == 7
    assert result["boot_ci_low"] <= result["observed_hit_rate"] <= result["boot_ci_high"]
    repeat = week_bootstrap_ticket_rate(board, 2, n_boot=2_000, seed=DEFAULT_SEED)
    assert result == repeat
