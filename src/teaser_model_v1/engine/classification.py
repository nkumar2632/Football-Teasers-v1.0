"""The two independent classification dimensions, held in one immutable value object.

Teaser Model v1.0 classifies a leg along **two dimensions that must never be conflated**:

============  ==========================  ===============================================
Dimension     Values                      Determined by
============  ==========================  ===============================================
Geometry      ``PRIMARY`` / ``SECONDARY``  the shape of the line, alone
Track         ``LIVE`` / ``PAPER``         the league, plus the geometry class
============  ==========================  ===============================================

The primary geometry is the same structure in both leagues::

    dog       +1.5 -> +7.5        favorite   -7.5 -> -1.5
    dog       +2.5 -> +8.5        favorite   -8.5 -> -2.5

What differs between leagues is the *track*, not the geometry:

===========================  ===============  =======
Leg                          geometry_class   track
===========================  ===============  =======
NFL +2.5 -> +8.5             PRIMARY          LIVE
CFB +2.5 -> +8.5             PRIMARY          PAPER
NFL +4.5 -> +10.5            SECONDARY        PAPER
CFB +4.5 -> +10.5            SECONDARY        PAPER
===========================  ===============  =======

All college football remains paper-only for the whole of the v1.0 2026 season, but **CFB
primary geometry must stay distinguishable from CFB secondary geometry** so that research
on the paper track can tell them apart.
"""

from __future__ import annotations

from dataclasses import dataclass

from teaser_model_v1.engine.constants import (
    LIVE_LEAGUES,
    PRIMARY_SPREADS,
    Geometry,
    Track,
)
from teaser_model_v1.engine.leagues import normalize_league
from teaser_model_v1.engine.numeric import is_whole_number, to_decimal


@dataclass(frozen=True)
class LegClassification:
    """The full v1.0 classification of one leg: two dimensions, never merged into one.

    ``geometry_class`` and ``track`` are different enum types with no shared members, so
    no comparison, dict key, or serialisation round-trip can silently swap one for the
    other.
    """

    geometry_class: Geometry
    track: Track
    secondary_reason: str | None = None

    @property
    def is_primary(self) -> bool:
        """Geometry only. True for CFB primary geometry as well as NFL primary geometry."""
        return self.geometry_class is Geometry.PRIMARY

    @property
    def is_live_track(self) -> bool:
        """Track only. True only for NFL primary geometry."""
        return self.track is Track.LIVE

    @property
    def is_paper_track(self) -> bool:
        return self.track is Track.PAPER

    def label(self) -> str:
        """``'PRIMARY/PAPER'`` — both dimensions, always shown together."""
        return f"{self.geometry_class.value}/{self.track.value}"


def geometry_class_for(spread) -> Geometry:
    """Classify the **shape** of a line. League-independent by design.

    PRIMARY for exactly +1.5, +2.5, -7.5 and -8.5. Everything else is SECONDARY — in
    particular whole-number lines such as +2 or -8, and +3.
    """
    return (
        Geometry.PRIMARY
        if to_decimal(spread) in PRIMARY_SPREADS
        else Geometry.SECONDARY
    )


def track_for(league: str, spread) -> Track:
    """Determine the **operational track**: LIVE only for NFL primary geometry.

    Everything else is PAPER — NFL secondary geometry, all college football (primary
    geometry included), and the entirety of the 2026 season.
    """
    lg = normalize_league(league)
    if lg in LIVE_LEAGUES and geometry_class_for(spread) is Geometry.PRIMARY:
        return Track.LIVE
    return Track.PAPER


def secondary_reason_for(spread) -> str | None:
    """Why a leg's *shape* is secondary. ``None`` for primary shapes.

    Deliberately league-independent: the reason describes the geometry, and a CFB leg is
    not secondary "because it is CFB" — CFB legs are paper because of their *track*.
    """
    if geometry_class_for(spread) is Geometry.PRIMARY:
        return None
    return "whole_number_line" if is_whole_number(spread) else "other_half_point_shape"


def classify(league: str, spread) -> LegClassification:
    """Classify a leg along both dimensions at once."""
    return LegClassification(
        geometry_class=geometry_class_for(spread),
        track=track_for(league, spread),
        secondary_reason=secondary_reason_for(spread),
    )
