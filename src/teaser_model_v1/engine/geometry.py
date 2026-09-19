"""Teased-spread arithmetic, the total guardrail, and geometry lookups.

Frozen. See ``TEASER_MODEL_V1_0.md`` §§2-4.

The two-dimensional classification itself lives in
:mod:`teaser_model_v1.engine.classification`; this module re-exports the geometry-side
helpers and owns the arithmetic.

All spreads are expressed **from the perspective of the team being bet**: a positive
spread means that team is receiving points (underdog), a negative spread means it is
laying them (favorite).
"""

from __future__ import annotations

from decimal import Decimal

from teaser_model_v1.engine.classification import (
    LegClassification,
    classify,
    geometry_class_for,
    secondary_reason_for,
    track_for,
)
from teaser_model_v1.engine.constants import (
    PRIMARY_SPREADS,
    TEASER_POINTS,
    TOTAL_GUARDRAIL,
    Geometry,
    Track,
)
from teaser_model_v1.engine.leagues import normalize_league
from teaser_model_v1.engine.numeric import to_decimal

__all__ = [
    "LegClassification",
    "classify",
    "classify_geometry",
    "geometry_class_for",
    "is_live_track",
    "is_primary_geometry",
    "passes_total_guardrail",
    "secondary_label",
    "secondary_reason_for",
    "shape_matches_primary_geometry",
    "teased_spread",
    "track_for",
]


def teased_spread(spread, teaser_points: int = TEASER_POINTS) -> Decimal:
    """Return the spread after applying the teaser.

    A 6-point teaser always moves the line in the bettor's favour, so from the bet's
    own perspective the arithmetic is a simple addition:

        +1.5 -> +7.5      -7.5 -> -1.5
        +2.5 -> +8.5      -8.5 -> -2.5
    """
    return to_decimal(spread) + to_decimal(teaser_points)


def shape_matches_primary_geometry(spread) -> bool:
    """True when *spread* is one of the four primary shapes: +1.5, +2.5, -7.5, -8.5.

    Identical to ``geometry_class_for(spread) is Geometry.PRIMARY``; kept as a predicate
    because "does this shape match" reads better at some call sites.
    """
    return to_decimal(spread) in PRIMARY_SPREADS


def classify_geometry(league: str, spread) -> Geometry:
    """Return the **geometry class** of a leg.

    The *league argument is accepted but does not affect the answer*: primary geometry is
    the same structure in both leagues. ``classify_geometry("CFB", 2.5)`` is
    ``Geometry.PRIMARY``, because CFB is restricted by its *track*, not by its geometry.

    Use :func:`track_for` to ask whether a leg may be played live.
    """
    normalize_league(league)  # validate, so an unknown league still raises
    return geometry_class_for(spread)


def is_primary_geometry(league: str, spread) -> bool:
    """True when the leg's shape is primary geometry, in either league."""
    return classify_geometry(league, spread) is Geometry.PRIMARY


def is_live_track(league: str, spread) -> bool:
    """True only for NFL primary geometry."""
    return track_for(league, spread) is Track.LIVE


def secondary_label(league: str, spread) -> str | None:
    """Reason string for a secondary *shape*; ``None`` for primary geometry.

    League-independent: a CFB primary leg returns ``None`` like an NFL one, because it is
    genuinely primary geometry. Its paper status is carried by the track.
    """
    normalize_league(league)
    return secondary_reason_for(spread)


def passes_total_guardrail(league: str, total) -> bool:
    """True when the game total satisfies the league guardrail (inclusive).

    NFL: ``total <= 47``. CFB: ``total <= 52``.
    """
    lg = normalize_league(league)
    return to_decimal(total) <= TOTAL_GUARDRAIL[lg]
