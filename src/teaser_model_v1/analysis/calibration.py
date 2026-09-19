"""Calibration measurement: buckets, hit rates, Brier score, expected wins.

Every bucket boundary in this module is **predeclared** and frozen before any outcome was
observed. Do not redesign a bucket because of what the results look like, and do not merge
a low-sample bucket into its neighbour after the fact — report it and mark it low-sample.

Nothing here fits or recalibrates anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import numpy as np
import pandas as pd
from scipy.stats import beta

from teaser_model_v1.engine.numeric import to_decimal

#: Sample size below which a row is marked low-sample rather than merged away.
LOW_SAMPLE_N = 20


# ---------------------------------------------------------------------------------------
# Predeclared buckets
# ---------------------------------------------------------------------------------------

#: Game-total buckets, inclusive lower / inclusive upper, in points.
TOTAL_BUCKETS: tuple[tuple[str, Decimal | None, Decimal | None], ...] = (
    ("<=40", None, Decimal("40")),
    ("40.5-43", Decimal("40.5"), Decimal("43")),
    ("43.5-45", Decimal("43.5"), Decimal("45")),
    ("45.5-47", Decimal("45.5"), Decimal("47")),
)

#: P_est buckets, inclusive lower / exclusive upper, as probabilities.
P_EST_BUCKETS: tuple[tuple[str, float | None, float | None], ...] = (
    ("<70%", None, 0.70),
    ("70-71.9%", 0.70, 0.72),
    ("72-73.9%", 0.72, 0.74),
    (">=74%", 0.74, None),
)

#: The four primary shapes, in the order they are reported.
PRIMARY_SHAPE_ORDER = ("+1.5", "+2.5", "-7.5", "-8.5")

SHAPE_LABELS = {
    Decimal("1.5"): "+1.5",
    Decimal("2.5"): "+2.5",
    Decimal("-7.5"): "-7.5",
    Decimal("-8.5"): "-8.5",
}

SHAPE_DESCRIPTIONS = {
    "+1.5": "+1.5 -> +7.5",
    "+2.5": "+2.5 -> +8.5",
    "-7.5": "-7.5 -> -1.5",
    "-8.5": "-8.5 -> -2.5",
}


def total_bucket(total) -> str:
    """Assign a game total to its predeclared bucket. Returns ``'out-of-range'`` above 47."""
    value = to_decimal(total)
    for label, low, high in TOTAL_BUCKETS:
        if (low is None or value >= low) and (high is None or value <= high):
            return label
    return "out-of-range"


def p_est_bucket(p_est: float) -> str:
    """Assign a P_est to its predeclared bucket. Lower bound inclusive, upper exclusive."""
    value = float(p_est)
    for label, low, high in P_EST_BUCKETS:
        if (low is None or value >= low) and (high is None or value < high):
            return label
    return "out-of-range"


def shape_label(spread) -> str:
    """``'+2.5'`` for the primary shapes; the raw value otherwise."""
    value = to_decimal(spread)
    return SHAPE_LABELS.get(value, str(value))


# ---------------------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------------------


def clopper_pearson_interval(wins: int, n: int, confidence: float = 0.95) -> tuple:
    """Exact (Clopper-Pearson) binomial confidence interval for a hit rate.

    Exact rather than normal-approximation, because several primary shapes have very small
    N and a normal interval would be meaningless there. Returns ``(nan, nan)`` for n == 0.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    alpha = 1.0 - confidence
    lower = 0.0 if wins == 0 else float(beta.ppf(alpha / 2, wins, n - wins + 1))
    upper = 1.0 if wins == n else float(beta.ppf(1 - alpha / 2, wins + 1, n - wins))
    return (lower, upper)


def brier_score(p_est, outcomes) -> float:
    """Mean squared error between predicted probability and the 0/1 outcome.

    Lower is better. 0.25 is the score of a constant 50% forecast.
    """
    p = np.asarray(list(p_est), dtype=float)
    y = np.asarray(list(outcomes), dtype=float)
    if p.size == 0:
        return float("nan")
    return float(np.mean((p - y) ** 2))


@dataclass(frozen=True)
class GroupResult:
    """Calibration of one group of legs. Purely descriptive."""

    label: str
    n: int
    mean_p_est: float
    wins: int
    hit_rate: float
    calibration_gap: float
    ci_low: float
    ci_high: float
    low_sample: bool

    def as_dict(self) -> dict:
        return {
            "group": self.label,
            "n": self.n,
            "mean_p_est": self.mean_p_est,
            "wins": self.wins,
            "actual_hit_rate": self.hit_rate,
            "calibration_gap": self.calibration_gap,
            "ci95_low": self.ci_low,
            "ci95_high": self.ci_high,
            "low_sample": self.low_sample,
        }


def summarise_group(label: str, frame: pd.DataFrame) -> GroupResult:
    """Summarise one group. ``frame`` needs ``p_est`` and ``won`` (0/1) columns.

    ``calibration_gap = actual hit rate - mean P_est``. Positive means the legs won more
    often than the frozen model expected.
    """
    n = len(frame)
    if n == 0:
        return GroupResult(label, 0, float("nan"), 0, float("nan"), float("nan"),
                           float("nan"), float("nan"), True)
    mean_p = float(frame["p_est"].mean())
    wins = int(frame["won"].sum())
    hit_rate = wins / n
    low, high = clopper_pearson_interval(wins, n)
    return GroupResult(
        label=label,
        n=n,
        mean_p_est=mean_p,
        wins=wins,
        hit_rate=hit_rate,
        calibration_gap=hit_rate - mean_p,
        ci_low=low,
        ci_high=high,
        low_sample=n < LOW_SAMPLE_N,
    )


def summarise_by(frame: pd.DataFrame, column: str, order) -> pd.DataFrame:
    """Summarise a frame grouped by *column*, emitting every label in *order*.

    Labels with no rows are emitted as empty rows rather than dropped — predeclared
    buckets stay visible even when they turn out to be empty.
    """
    rows = [
        summarise_group(label, frame[frame[column] == label]).as_dict() for label in order
    ]
    return pd.DataFrame(rows)


def expected_versus_actual(frame: pd.DataFrame) -> dict:
    """Simple expected wins = sum(P_est), against actual wins. No fitting."""
    expected = float(frame["p_est"].sum())
    actual = int(frame["won"].sum())
    n = len(frame)
    return {
        "n": n,
        "expected_wins": expected,
        "actual_wins": actual,
        "actual_minus_expected": actual - expected,
        "mean_p_est": float(frame["p_est"].mean()) if n else float("nan"),
        "actual_hit_rate": actual / n if n else float("nan"),
        "brier_score": brier_score(frame["p_est"], frame["won"]),
    }


def calibration_slope_is_reasonable(frame: pd.DataFrame, *, min_n: int = 500,
                                    min_spread: float = 0.10) -> tuple[bool, str]:
    """Decide whether fitting a calibration intercept/slope is statistically defensible.

    A logistic calibration fit needs both a decent sample and real spread in the predictor.
    With a narrow P_est range the slope is essentially unidentified and any number reported
    would be noise dressed as a finding. Returns ``(ok, reason)``; when False the caller
    must omit the statistic explicitly rather than reporting it with a caveat.
    """
    n = len(frame)
    if n == 0:
        return False, "no legs in the sample"
    spread = float(frame["p_est"].max() - frame["p_est"].min())
    problems = []
    if n < min_n:
        problems.append(f"N = {n} is below the {min_n} needed for a stable logistic fit")
    if spread < min_spread:
        problems.append(
            f"P_est spans only {spread:.4f} "
            f"({frame['p_est'].min():.4f}-{frame['p_est'].max():.4f}), "
            f"below the {min_spread:.2f} needed to identify a slope"
        )
    if problems:
        return False, "; ".join(problems)
    return True, "sample size and predictor spread are adequate"
