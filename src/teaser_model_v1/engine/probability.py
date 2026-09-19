"""The v1.0 probability model.

Frozen. See ``TEASER_MODEL_V1_0.md`` §5.

    sigma = 0.30 * game_total
    P_raw = standard_normal_CDF(6 / sigma)
    P_est = P_raw + key_number_bump

Everything here returns full internal precision. Rounding happens only in
:mod:`teaser_model_v1.engine.presentation`, and the rounded number must always carry the
label "model-estimated hit probability".
"""

from __future__ import annotations

from decimal import Decimal

from scipy.stats import norm

from teaser_model_v1.engine.constants import (
    BUMP_BOTH,
    BUMP_NONE,
    BUMP_ONE,
    KEY_NUMBERS,
    SIGMA_TOTAL_COEFFICIENT,
    TEASER_POINTS,
)
from teaser_model_v1.engine.leagues import normalize_league
from teaser_model_v1.engine.numeric import to_decimal


def sigma(total) -> float:
    """sigma = 0.30 * game_total.

    Raises for a non-positive total: a zero or negative total would make ``6 / sigma``
    undefined, and silently substituting a floor value would be a model change.
    """
    t = to_decimal(total)
    if t <= 0:
        raise ValueError(f"game total must be positive, got {total!r}")
    return float(SIGMA_TOTAL_COEFFICIENT * t)


def p_raw(total, teaser_points: int = TEASER_POINTS) -> float:
    """P_raw = standard_normal_CDF(6 / sigma)."""
    return float(norm.cdf(teaser_points / sigma(total)))


def key_numbers_crossed(
    spread, league: str, teaser_points: int = TEASER_POINTS
) -> int:
    """Count how many of the league's key numbers the teaser crosses.

    A bet on a team at line ``L`` wins when that team's signed margin satisfies
    ``margin + L > 0``. Teasing ``L`` to ``L + 6`` newly covers exactly the signed
    margins in the half-open interval ``(-L - 6, -L]``. A key number ``k`` is crossed
    when a margin of ``k`` or ``-k`` falls in that interval — i.e. when the teaser turns
    that margin from a loss or push into a win.

    The interval is open at the bottom and closed at the top because a margin equal to
    the teased line is a push, not a win, while a margin equal to the original line was a
    push before and is a win afterwards.

    All four primary NFL geometries cross both key numbers (3 and 7) under this rule.
    """
    lg = normalize_league(league)
    line = to_decimal(spread)
    points = to_decimal(teaser_points)

    lower = -line - points  # exclusive
    upper = -line  # inclusive

    crossed = 0
    for key in KEY_NUMBERS[lg]:
        k = to_decimal(key)
        if (lower < k <= upper) or (lower < -k <= upper):
            crossed += 1
    return crossed


def key_number_bump(league: str, crossings: int) -> float:
    """Return the provisional key-number bump for *crossings* key numbers crossed.

    NFL: both +0.07, one +0.04. CFB: both +0.04, one +0.02. Neither: +0.00.

    PROVISIONAL DOES NOT MEAN EDITABLE — no proposed CFB bump correction is applied.
    """
    lg = normalize_league(league)
    if crossings < 0:
        raise ValueError(f"crossings must be non-negative, got {crossings}")
    if crossings == 0:
        return BUMP_NONE[lg]
    if crossings == 1:
        return BUMP_ONE[lg]
    return BUMP_BOTH[lg]


def bump_for_leg(league: str, spread, teaser_points: int = TEASER_POINTS) -> float:
    """Convenience wrapper: crossings then bump, for one leg."""
    return key_number_bump(
        league, key_numbers_crossed(spread, league, teaser_points=teaser_points)
    )


def p_est(league: str, spread, total, teaser_points: int = TEASER_POINTS) -> float:
    """P_est = P_raw + key-number bump. Full internal precision, never rounded here.

    Deliberately **not** clipped to [0, 1]: the specification says ``P_est = P_raw + bump``
    and clipping would be a silent reinterpretation. ``P_est > 1`` is arithmetically
    possible only at absurdly low totals (below roughly 13.5) and is surfaced by
    :func:`p_est_is_degenerate` rather than quietly repaired.
    """
    return p_raw(total, teaser_points=teaser_points) + bump_for_leg(
        league, spread, teaser_points=teaser_points
    )


def p_est_is_degenerate(value: float) -> bool:
    """True when a P_est falls outside [0, 1] and therefore signals bad input data."""
    return not (0.0 <= value <= 1.0)
