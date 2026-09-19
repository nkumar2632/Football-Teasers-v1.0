"""Phase 2B validation statistics: comparators, group comparison, monotonicity."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from teaser_model_v1.analysis.calibration import (
    DOG_SHAPES,
    FAVORITE_SHAPES,
    brier_score,
    constant_forecast,
    frozen_versus_constant,
    log_loss,
    side_class,
)
from teaser_model_v1.analysis.validation import (
    assess_monotonicity,
    compare_two_groups,
    dog_favorite_comparison,
    group_interval_row,
)


# ---------------------------------------------------------------------------------------
# H3 comparator.
# ---------------------------------------------------------------------------------------


def test_constant_forecast_uses_only_model_inputs():
    """The comparator must be the mean P_est, never the realized hit rate."""
    frame = pd.DataFrame({"p_est": [0.74, 0.76], "won": [1, 1]})
    assert constant_forecast(frame) == pytest.approx(0.75)
    # Flipping the outcomes must not move the comparator at all.
    flipped = frame.assign(won=[0, 0])
    assert constant_forecast(flipped) == pytest.approx(constant_forecast(frame))


def test_frozen_versus_constant_delta_identity():
    """delta Brier must equal var(P_est) - 2*cov(P_est, outcome)."""
    rng = np.random.default_rng(0)
    p = rng.uniform(0.73, 0.79, size=200)
    y = (rng.uniform(size=200) < p).astype(int)
    frame = pd.DataFrame({"p_est": p, "won": y})

    result = frozen_versus_constant(frame)
    expected = np.var(p) - 2 * np.mean((p - p.mean()) * (y - y.mean()))
    assert result["delta_brier"] == pytest.approx(expected, abs=1e-12)


def test_frozen_beats_constant_when_p_est_tracks_outcomes():
    frame = pd.DataFrame({"p_est": [0.9, 0.9, 0.1, 0.1], "won": [1, 1, 0, 0]})
    result = frozen_versus_constant(frame)
    assert result["delta_brier"] < 0
    assert result["delta_log_loss"] < 0


def test_constant_beats_frozen_when_p_est_is_anti_correlated():
    frame = pd.DataFrame({"p_est": [0.9, 0.9, 0.1, 0.1], "won": [0, 0, 1, 1]})
    assert frozen_versus_constant(frame)["delta_brier"] > 0


def test_a_constant_p_est_makes_the_two_models_identical():
    frame = pd.DataFrame({"p_est": [0.75] * 6, "won": [1, 1, 1, 1, 0, 0]})
    result = frozen_versus_constant(frame)
    assert result["delta_brier"] == pytest.approx(0.0, abs=1e-15)
    assert result["delta_log_loss"] == pytest.approx(0.0, abs=1e-12)


def test_log_loss_values_and_safety():
    assert log_loss([0.5, 0.5], [1, 0]) == pytest.approx(math.log(2))
    assert log_loss([0.75], [1]) == pytest.approx(-math.log(0.75))
    # Degenerate forecasts return NaN rather than infinity.
    assert math.isnan(log_loss([0.0, 0.5], [1, 0]))
    assert math.isnan(log_loss([1.0], [1]))
    assert math.isnan(log_loss([], []))


def test_brier_and_log_loss_agree_on_direction():
    good = pd.DataFrame({"p_est": [0.8, 0.8, 0.2], "won": [1, 1, 0]})
    bad = pd.DataFrame({"p_est": [0.2, 0.2, 0.8], "won": [1, 1, 0]})
    assert brier_score(good["p_est"], good["won"]) < brier_score(bad["p_est"], bad["won"])
    assert log_loss(good["p_est"], good["won"]) < log_loss(bad["p_est"], bad["won"])


# ---------------------------------------------------------------------------------------
# Dog / favorite grouping and comparison.
# ---------------------------------------------------------------------------------------


def test_side_class_and_shape_groups_agree():
    assert DOG_SHAPES == ("+1.5", "+2.5")
    assert FAVORITE_SHAPES == ("-7.5", "-8.5")
    assert side_class(1.5) == "DOG" and side_class(2.5) == "DOG"
    assert side_class(-7.5) == "FAVORITE" and side_class(-8.5) == "FAVORITE"


def frame_for(shape, n, wins, p=0.75):
    return pd.DataFrame(
        {"shape": [shape] * n, "p_est": [p] * n, "won": [1] * wins + [0] * (n - wins)}
    )


def test_compare_two_groups_hand_checkable():
    a = pd.DataFrame({"won": [1] * 8 + [0] * 2})  # 8/10
    b = pd.DataFrame({"won": [1] * 5 + [0] * 5})  # 5/10
    result = compare_two_groups(a, b, "a", "b")

    assert result.rate_a == pytest.approx(0.8)
    assert result.rate_b == pytest.approx(0.5)
    assert result.difference_pp == pytest.approx(30.0)
    # Odds ratio = (8*5)/(2*5) = 4
    assert result.odds_ratio == pytest.approx(4.0)
    assert not result.or_corrected
    assert result.or_ci_low < result.odds_ratio < result.or_ci_high
    assert 0.0 <= result.fisher_p <= 1.0


def test_identical_groups_give_odds_ratio_one_and_p_one():
    a = pd.DataFrame({"won": [1] * 7 + [0] * 3})
    b = pd.DataFrame({"won": [1] * 7 + [0] * 3})
    result = compare_two_groups(a, b, "a", "b")
    assert result.odds_ratio == pytest.approx(1.0)
    assert result.difference_pp == pytest.approx(0.0)
    assert result.fisher_p == pytest.approx(1.0)


def test_zero_cell_is_corrected_and_flagged():
    a = pd.DataFrame({"won": [1] * 6})  # no losses
    b = pd.DataFrame({"won": [1] * 3 + [0] * 3})
    result = compare_two_groups(a, b, "a", "b")
    assert result.or_corrected is True
    assert math.isfinite(result.odds_ratio)
    assert math.isfinite(result.or_ci_low) and math.isfinite(result.or_ci_high)


def test_empty_group_yields_nan_rather_than_a_crash():
    a = pd.DataFrame({"won": pd.Series(dtype=float)})
    b = pd.DataFrame({"won": [1, 0]})
    result = compare_two_groups(a, b, "a", "b")
    assert result.n_a == 0
    assert math.isnan(result.odds_ratio)
    assert math.isnan(result.difference_pp)


def test_dog_favorite_comparison_splits_on_shape():
    frame = pd.concat(
        [
            frame_for("+1.5", 10, 9),
            frame_for("+2.5", 10, 8),
            frame_for("-7.5", 10, 5),
            frame_for("-8.5", 10, 5),
        ],
        ignore_index=True,
    )
    result = dog_favorite_comparison(frame)
    assert result.n_a == 20 and result.wins_a == 17
    assert result.n_b == 20 and result.wins_b == 10
    assert result.rate_a == pytest.approx(0.85)
    assert result.rate_b == pytest.approx(0.50)
    assert result.difference_pp == pytest.approx(35.0)


def test_group_interval_row_shape():
    row = group_interval_row(frame_for("+1.5", 10, 8), "dogs")
    assert row["n"] == 10 and row["wins"] == 8
    assert row["actual_hit_rate"] == pytest.approx(0.8)
    assert row["calibration_gap"] == pytest.approx(0.05)
    assert row["ci95_low"] < 0.8 < row["ci95_high"]


# ---------------------------------------------------------------------------------------
# Monotonicity.
# ---------------------------------------------------------------------------------------


def bucket_frame(mean_p, rates, ns=None):
    ns = ns or [10] * len(mean_p)
    return pd.DataFrame(
        {"bucket": [f"b{i}" for i in range(len(mean_p))], "n": ns,
         "mean_p_est": mean_p, "actual_hit_rate": rates}
    )


def test_perfect_monotonicity_detected():
    result = assess_monotonicity(bucket_frame([0.77, 0.75, 0.74, 0.73],
                                              [0.90, 0.80, 0.70, 0.60]))
    assert result.perfectly_monotone
    assert result.concordant_pairs == 3 and result.adjacent_pairs == 3
    assert result.inversions == ()
    assert result.spearman_rho == pytest.approx(1.0)


def test_inversion_is_located_precisely():
    result = assess_monotonicity(bucket_frame([0.77, 0.75, 0.74, 0.73],
                                              [0.90, 0.80, 0.60, 0.70]))
    assert not result.perfectly_monotone
    assert result.concordant_pairs == 2
    assert result.inversions == ("b2 -> b3",)


def test_reversed_ordering_is_fully_discordant():
    result = assess_monotonicity(bucket_frame([0.77, 0.75, 0.74, 0.73],
                                              [0.60, 0.70, 0.80, 0.90]))
    assert result.concordant_pairs == 0
    assert result.spearman_rho == pytest.approx(-1.0)


def test_empty_buckets_are_skipped_not_imputed():
    frame = bucket_frame([0.77, float("nan"), 0.74, 0.73],
                         [0.90, float("nan"), 0.70, 0.60],
                         ns=[10, 0, 10, 10])
    result = assess_monotonicity(frame)
    assert result.n_comparable == 3
    assert result.buckets == ("b0", "b2", "b3")
    assert result.perfectly_monotone


def test_fewer_than_two_buckets_is_not_assessable():
    result = assess_monotonicity(bucket_frame([0.77], [0.9], ns=[10]))
    assert result.n_comparable == 1
    assert not result.perfectly_monotone
    assert "Not assessable" in result.summary()
