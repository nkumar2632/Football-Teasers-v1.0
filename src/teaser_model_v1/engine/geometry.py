"""Geometry classification, teased-spread arithmetic and the total guardrail.

Frozen. See ``TEASER_MODEL_V1_0.md`` §§2-4.

All spreads are expressed **from the perspective of the team being bet**: a positive
spread means that team is receiving points (underdog), a negative spread means it is
laying them (favorite).
"""

from __future__ import annotations

from decimal import Decimal

from teaser_model_v1.engine.constants import (
    CFB,
    NFL,
    PRIMARY_NFL_SPREADS,
    TEASER_POINTS,
    TOTAL_GUARDRAIL,
    Geometry,
    Track,
)
from teaser_model_v1.engine.leagues import normalize_league
from teaser_model_v1.engine.numeric import is_whole_number, to_decimal


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

    This is a league-independent test of the *shape* only. Whether a leg is actually
    classified PRIMARY also depends on the league — see :func:`classify_geometry` and
    AMBIGUITIES.md A-2.
    """
    return to_decimal(spread) in PRIMARY_NFL_SPREADS


def classify_geometry(league: str, spread) -> Geometry:
    """Classify a leg's geometry as PRIMARY or SECONDARY.

    PRIMARY requires **both**:

    * the league is NFL — the specification defines primary geometry as *NFL* primary
      geometry, and college football is paper/research only in its entirety; and
    * the pre-teaser spread is exactly +1.5, +2.5, -7.5 or -8.5.

    Everything else is SECONDARY. In particular whole-number lines such as ``+2`` or
    ``-8`` are secondary, and ``+3`` is secondary.
    """
    lg = normalize_league(league)
    if lg == NFL and shape_matches_primary_geometry(spread):
        return Geometry.PRIMARY
    return Geometry.SECONDARY


def is_primary(league: str, spread) -> bool:
    """Convenience predicate for :func:`classify_geometry`."""
    return classify_geometry(league, spread) is Geometry.PRIMARY


def secondary_label(league: str, spread) -> str | None:
    """Return a short reason string describing *why* a leg is secondary.

    Returns ``None`` for primary legs. The label is descriptive only: it records a fact
    about the leg, it does not create any new eligibility.
    """
    lg = normalize_league(league)
    d = to_decimal(spread)

    if classify_geometry(lg, d) is Geometry.PRIMARY:
        return None

    if lg == CFB:
        if shape_matches_primary_geometry(d):
            return "cfb_paper_track_primary_shape"
        return "cfb_paper_track_other_shape"

    if is_whole_number(d):
        return "whole_number_line"
    return "other_half_point_shape"


def track_for(league: str, spread) -> Track:
    """LIVE for NFL primary geometry, PAPER for everything else.

    Note that the *entire* 2026 season is paper/research per specification §1; this
    function reports the geometry-and-league track only. Season-level gating is applied
    by the caller and is recorded on :class:`~teaser_model_v1.engine.legs.Leg`.
    """
    return Track.LIVE if is_primary(league, spread) else Track.PAPER


def passes_total_guardrail(league: str, total) -> bool:
    """True when the game total satisfies the league guardrail (inclusive).

    NFL: ``total <= 47``. CFB: ``total <= 52``.
    """
    lg = normalize_league(league)
    return to_decimal(total) <= TOTAL_GUARDRAIL[lg]
