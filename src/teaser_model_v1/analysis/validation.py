"""Phase 2B validation statistics: group comparison and monotonicity.

These test **hypotheses declared in advance** against seasons the hypotheses were not
generated from. Nothing here may change the frozen model, whichever way a result falls.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, spearmanr

from teaser_model_v1.analysis.calibration import (
    DOG_SHAPES,
    FAVORITE_SHAPES,
    clopper_pearson_interval,
)

#: Haldane-Anscombe correction, applied only when a zero cell makes the odds ratio
#: undefined. Its use is always reported alongside the number.
HALDANE_CORRECTION = 0.5


@dataclass(frozen=True)
class TwoGroupComparison:
    """Comparison of realized hit rates between two disjoint groups of legs."""

    label_a: str
    label_b: str
    n_a: int
    wins_a: int
    n_b: int
    wins_b: int
    rate_a: float
    rate_b: float
    difference_pp: float
    odds_ratio: float
    or_ci_low: float
    or_ci_high: float
    or_corrected: bool
    fisher_p: float

    def as_dict(self) -> dict:
        return {
            "group_a": self.label_a,
            "n_a": self.n_a,
            "wins_a": self.wins_a,
            "hit_rate_a": self.rate_a,
            "group_b": self.label_b,
            "n_b": self.n_b,
            "wins_b": self.wins_b,
            "hit_rate_b": self.rate_b,
            "difference_pp": self.difference_pp,
            "odds_ratio_a_over_b": self.odds_ratio,
            "or_ci95_low": self.or_ci_low,
            "or_ci95_high": self.or_ci_high,
            "or_zero_cell_corrected": self.or_corrected,
            "fisher_exact_p_two_sided": self.fisher_p,
        }


def compare_two_groups(
    frame_a: pd.DataFrame, frame_b: pd.DataFrame, label_a: str, label_b: str
) -> TwoGroupComparison:
    """Compare hit rates in two groups: difference, odds ratio with CI, Fisher exact.

    Fisher's exact test is used rather than a chi-square because the cells are small.
    The odds ratio interval is the Woolf log interval; if any cell is zero the odds ratio
    is undefined and a Haldane-Anscombe 0.5 correction is applied, flagged by
    ``or_corrected``.
    """
    n_a, n_b = len(frame_a), len(frame_b)
    wins_a = int(frame_a["won"].sum()) if n_a else 0
    wins_b = int(frame_b["won"].sum()) if n_b else 0
    losses_a, losses_b = n_a - wins_a, n_b - wins_b

    rate_a = wins_a / n_a if n_a else float("nan")
    rate_b = wins_b / n_b if n_b else float("nan")

    table = [[wins_a, losses_a], [wins_b, losses_b]]
    if n_a and n_b:
        _, fisher_p = fisher_exact(table, alternative="two-sided")
    else:
        fisher_p = float("nan")

    cells = [wins_a, losses_a, wins_b, losses_b]
    corrected = any(cell == 0 for cell in cells)
    if n_a == 0 or n_b == 0:
        odds_ratio = or_low = or_high = float("nan")
    else:
        adj = [c + HALDANE_CORRECTION for c in cells] if corrected else [float(c) for c in cells]
        a, b, c, d = adj
        odds_ratio = (a * d) / (b * c)
        se = math.sqrt(sum(1.0 / value for value in adj))
        or_low = math.exp(math.log(odds_ratio) - 1.96 * se)
        or_high = math.exp(math.log(odds_ratio) + 1.96 * se)

    return TwoGroupComparison(
        label_a=label_a,
        label_b=label_b,
        n_a=n_a,
        wins_a=wins_a,
        n_b=n_b,
        wins_b=wins_b,
        rate_a=rate_a,
        rate_b=rate_b,
        difference_pp=(rate_a - rate_b) * 100.0 if n_a and n_b else float("nan"),
        odds_ratio=odds_ratio,
        or_ci_low=or_low,
        or_ci_high=or_high,
        or_corrected=corrected,
        fisher_p=float(fisher_p),
    )


def dog_favorite_comparison(frame: pd.DataFrame, label: str = "") -> TwoGroupComparison:
    """Compare primary underdog legs against primary favorite legs."""
    dogs = frame[frame["shape"].isin(DOG_SHAPES)]
    favorites = frame[frame["shape"].isin(FAVORITE_SHAPES)]
    prefix = f"{label} " if label else ""
    return compare_two_groups(
        dogs, favorites, f"{prefix}dogs (+1.5, +2.5)", f"{prefix}favorites (-7.5, -8.5)"
    )


def group_interval_row(frame: pd.DataFrame, label: str) -> dict:
    """N, mean P_est, hit rate, calibration gap and exact 95% interval for one group."""
    n = len(frame)
    if n == 0:
        return {
            "group": label,
            "n": 0,
            "mean_p_est": float("nan"),
            "wins": 0,
            "actual_hit_rate": float("nan"),
            "calibration_gap": float("nan"),
            "ci95_low": float("nan"),
            "ci95_high": float("nan"),
        }
    wins = int(frame["won"].sum())
    mean_p = float(frame["p_est"].mean())
    rate = wins / n
    low, high = clopper_pearson_interval(wins, n)
    return {
        "group": label,
        "n": n,
        "mean_p_est": mean_p,
        "wins": wins,
        "actual_hit_rate": rate,
        "calibration_gap": rate - mean_p,
        "ci95_low": low,
        "ci95_high": high,
    }


# ---------------------------------------------------------------------------------------
# Monotonicity
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class MonotonicityResult:
    """Whether realized hit rates follow the ordering the frozen P_est predicts.

    This is an **ordering check**, not a fitted trend. No line is estimated.
    """

    buckets: tuple
    predicted_order: tuple
    realized_order: tuple
    n_comparable: int
    adjacent_pairs: int
    concordant_pairs: int
    inversions: tuple
    perfectly_monotone: bool
    spearman_rho: float
    spearman_p: float

    def summary(self) -> str:
        if self.n_comparable < 2:
            return "Not assessable: fewer than two non-empty buckets."
        if self.perfectly_monotone:
            return (
                f"Realized hit rates are perfectly monotone in the predicted direction "
                f"across {self.n_comparable} non-empty buckets "
                f"({self.concordant_pairs}/{self.adjacent_pairs} adjacent pairs ordered "
                "as predicted)."
            )
        return (
            f"Realized hit rates are NOT monotone in the predicted direction: "
            f"{self.concordant_pairs}/{self.adjacent_pairs} adjacent pairs ordered as "
            f"predicted. Inversions at: {', '.join(self.inversions)}."
        )


def assess_monotonicity(bucket_table: pd.DataFrame, bucket_column: str = "bucket") -> MonotonicityResult:
    """Check whether realized hit rates are ordered as the frozen P_est predicts.

    The frozen model predicts a *decreasing* hit rate as the game total rises, because
    sigma = 0.30 x total and P_est falls as sigma grows. Empty buckets are skipped, not
    imputed. Spearman's rho is reported as a descriptive rank statistic; it fits nothing.
    """
    usable = bucket_table[bucket_table["n"] > 0].reset_index(drop=True)
    labels = tuple(usable[bucket_column])
    predicted = tuple(usable["mean_p_est"])
    realized = tuple(usable["actual_hit_rate"])
    n = len(usable)

    if n < 2:
        return MonotonicityResult(
            labels, predicted, realized, n, 0, 0, (), False, float("nan"), float("nan")
        )

    adjacent = n - 1
    concordant = 0
    inversions = []
    for i in range(adjacent):
        predicted_drop = predicted[i] >= predicted[i + 1]
        realized_drop = realized[i] >= realized[i + 1]
        if predicted_drop == realized_drop:
            concordant += 1
        else:
            inversions.append(f"{labels[i]} -> {labels[i + 1]}")

    if n >= 3:
        rho, p_value = spearmanr(predicted, realized)
    else:
        rho, p_value = float("nan"), float("nan")

    return MonotonicityResult(
        buckets=labels,
        predicted_order=predicted,
        realized_order=realized,
        n_comparable=n,
        adjacent_pairs=adjacent,
        concordant_pairs=concordant,
        inversions=tuple(inversions),
        perfectly_monotone=concordant == adjacent,
        spearman_rho=float(rho) if not (isinstance(rho, float) and np.isnan(rho)) else float("nan"),
        spearman_p=float(p_value) if not (isinstance(p_value, float) and np.isnan(p_value)) else float("nan"),
    )
