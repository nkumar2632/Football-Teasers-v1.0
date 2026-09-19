"""Calibration buckets, statistics and expected-wins arithmetic."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from teaser_model_v1.analysis.calibration import (
    P_EST_BUCKETS,
    PRIMARY_SHAPE_ORDER,
    TOTAL_BUCKETS,
    brier_score,
    calibration_slope_is_reasonable,
    clopper_pearson_interval,
    expected_versus_actual,
    p_est_bucket,
    shape_label,
    summarise_by,
    summarise_group,
    total_bucket,
)


# ---------------------------------------------------------------------------------------
# Predeclared bucket boundaries.
# ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "total,expected",
    [
        (30, "<=40"),
        (40, "<=40"),  # inclusive upper
        (40.5, "40.5-43"),  # inclusive lower
        (43, "40.5-43"),
        (43.5, "43.5-45"),
        (45, "43.5-45"),
        (45.5, "45.5-47"),
        (47, "45.5-47"),  # the guardrail boundary itself qualifies
        (47.5, "out-of-range"),
    ],
)
def test_total_bucket_boundaries(total, expected):
    assert total_bucket(total) == expected


@pytest.mark.parametrize(
    "p,expected",
    [
        (0.50, "<70%"),
        (0.6999, "<70%"),
        (0.70, "70-71.9%"),  # lower inclusive
        (0.7199, "70-71.9%"),
        (0.72, "72-73.9%"),  # upper exclusive
        (0.7399, "72-73.9%"),
        (0.74, ">=74%"),
        (0.95, ">=74%"),
    ],
)
def test_p_est_bucket_boundaries(p, expected):
    assert p_est_bucket(p) == expected


def test_buckets_partition_the_space_without_gaps_or_overlap():
    for value in [x / 1000 for x in range(0, 1001)]:
        assert p_est_bucket(value) != "out-of-range"
    labels = [label for label, _, _ in P_EST_BUCKETS]
    assert labels == ["<70%", "70-71.9%", "72-73.9%", ">=74%"]
    assert [label for label, _, _ in TOTAL_BUCKETS] == [
        "<=40",
        "40.5-43",
        "43.5-45",
        "45.5-47",
    ]


def test_shape_labels():
    assert shape_label(1.5) == "+1.5"
    assert shape_label(-8.5) == "-8.5"
    assert PRIMARY_SHAPE_ORDER == ("+1.5", "+2.5", "-7.5", "-8.5")


# ---------------------------------------------------------------------------------------
# Statistics.
# ---------------------------------------------------------------------------------------


def test_clopper_pearson_known_values():
    low, high = clopper_pearson_interval(0, 10)
    assert low == 0.0
    assert high == pytest.approx(0.3085, abs=1e-3)

    low, high = clopper_pearson_interval(10, 10)
    assert low == pytest.approx(0.6915, abs=1e-3)
    assert high == 1.0

    low, high = clopper_pearson_interval(5, 10)
    assert low == pytest.approx(0.1871, abs=1e-3)
    assert high == pytest.approx(0.8129, abs=1e-3)


def test_clopper_pearson_handles_empty_samples():
    low, high = clopper_pearson_interval(0, 0)
    assert math.isnan(low) and math.isnan(high)


def test_brier_score():
    # Perfect forecasts.
    assert brier_score([1.0, 0.0], [1, 0]) == pytest.approx(0.0)
    # Constant 50% forecast.
    assert brier_score([0.5, 0.5], [1, 0]) == pytest.approx(0.25)
    # Worked example.
    assert brier_score([0.75, 0.75], [1, 0]) == pytest.approx(
        ((0.75 - 1) ** 2 + 0.75**2) / 2
    )


def test_summarise_group_computes_gap_as_actual_minus_predicted():
    frame = pd.DataFrame({"p_est": [0.75, 0.75, 0.75, 0.75], "won": [1, 1, 1, 0]})
    result = summarise_group("test", frame)
    assert result.n == 4
    assert result.wins == 3
    assert result.hit_rate == pytest.approx(0.75)
    assert result.mean_p_est == pytest.approx(0.75)
    assert result.calibration_gap == pytest.approx(0.0)
    assert result.low_sample is True  # N=4 < 20


def test_calibration_gap_sign_convention():
    # Won more often than predicted -> positive gap.
    frame = pd.DataFrame({"p_est": [0.70] * 10, "won": [1] * 9 + [0]})
    assert summarise_group("x", frame).calibration_gap == pytest.approx(0.20)
    # Won less often than predicted -> negative gap.
    frame = pd.DataFrame({"p_est": [0.70] * 10, "won": [1] * 5 + [0] * 5})
    assert summarise_group("x", frame).calibration_gap == pytest.approx(-0.20)


def test_empty_predeclared_buckets_are_reported_not_dropped():
    frame = pd.DataFrame({"p_est": [0.75, 0.76], "won": [1, 0], "b": [">=74%", ">=74%"]})
    out = summarise_by(frame, "b", [label for label, _, _ in P_EST_BUCKETS])
    assert list(out["group"]) == ["<70%", "70-71.9%", "72-73.9%", ">=74%"]
    assert out.loc[out["group"] == "<70%", "n"].iloc[0] == 0
    assert out.loc[out["group"] == ">=74%", "n"].iloc[0] == 2


def test_expected_versus_actual():
    frame = pd.DataFrame({"p_est": [0.8, 0.7, 0.6], "won": [1, 1, 0]})
    result = expected_versus_actual(frame)
    assert result["n"] == 3
    assert result["expected_wins"] == pytest.approx(2.1)
    assert result["actual_wins"] == 2
    assert result["actual_minus_expected"] == pytest.approx(-0.1)
    assert result["actual_hit_rate"] == pytest.approx(2 / 3)


def test_calibration_slope_gate_rejects_narrow_predictor_and_small_n():
    narrow = pd.DataFrame({"p_est": [0.74, 0.75, 0.76] * 10, "won": [1, 0, 1] * 10})
    ok, reason = calibration_slope_is_reasonable(narrow)
    assert ok is False
    assert "P_est spans only" in reason
    assert "below the 500" in reason

    wide = pd.DataFrame({"p_est": [0.40 + i / 1000 for i in range(600)],
                         "won": [i % 2 for i in range(600)]})
    ok, reason = calibration_slope_is_reasonable(wide)
    assert ok is True
