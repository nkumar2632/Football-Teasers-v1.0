"""The teaser leg: an immutable value object carrying its own v1.0 classification.

A :class:`Leg` is pure data plus the frozen model's verdict on it. It knows nothing about
where its numbers came from; ingestion lives in :mod:`teaser_model_v1.ingest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable, Sequence

from teaser_model_v1.engine.constants import TEASER_POINTS, Geometry, Track
from teaser_model_v1.engine.geometry import (
    classify_geometry,
    passes_total_guardrail,
    secondary_label,
    teased_spread,
    track_for,
)
from teaser_model_v1.engine.leagues import normalize_league
from teaser_model_v1.engine.numeric import to_decimal
from teaser_model_v1.engine.probability import (
    bump_for_leg,
    key_numbers_crossed,
    p_est,
    p_raw,
)


@dataclass(frozen=True)
class Leg:
    """One side of one game, teased 6 points.

    ``spread`` is the pre-teaser line **from this team's perspective**: positive means
    receiving points.

    ``provenance`` records where the line came from. It is a free-text tag such as
    ``archived_reference_line``; do not write ``true_timestamped_close`` into it unless
    the source documentation proves the line was the last market price before kickoff.
    """

    leg_id: str
    league: str
    team: str
    spread: Decimal
    game_total: Decimal

    # Context (optional, carried through for reporting and joins)
    game_id: str | None = None
    opponent: str | None = None
    season: int | None = None
    week: int | None = None
    provenance: str | None = None
    extra: dict = field(default_factory=dict, compare=False, repr=False)

    # Derived by build_leg()
    teased_spread: Decimal = Decimal(0)
    geometry: Geometry = Geometry.SECONDARY
    secondary_reason: str | None = None
    geometry_track: Track = Track.PAPER
    total_ok: bool = False
    key_numbers_crossed: int = 0
    bump: float = 0.0
    p_raw: float = 0.0
    p_est: float = 0.0

    @property
    def is_primary(self) -> bool:
        return self.geometry is Geometry.PRIMARY

    @property
    def qualifies_primary(self) -> bool:
        """Primary geometry **and** inside the league total guardrail."""
        return self.is_primary and self.total_ok

    def sort_key(self) -> tuple:
        """Deterministic ranking key: P_est descending, then leg_id ascending.

        The leg_id term is a *determinism device*, not a model rule — the specification
        ranks legs by P_est and says nothing about exact ties. Using a stable, data-derived
        tiebreak keeps weekly output reproducible instead of dependent on row order.
        See AMBIGUITIES.md A-4.
        """
        return (-self.p_est, self.leg_id)


def build_leg(
    leg_id: str,
    league: str,
    team: str,
    spread,
    game_total,
    *,
    game_id: str | None = None,
    opponent: str | None = None,
    season: int | None = None,
    week: int | None = None,
    provenance: str | None = None,
    extra: dict | None = None,
    teaser_points: int = TEASER_POINTS,
) -> Leg:
    """Construct a :class:`Leg` and apply the frozen v1.0 classification to it."""
    lg = normalize_league(league)
    spread_d = to_decimal(spread)
    total_d = to_decimal(game_total)

    crossings = key_numbers_crossed(spread_d, lg, teaser_points=teaser_points)

    return Leg(
        leg_id=str(leg_id),
        league=lg,
        team=team,
        spread=spread_d,
        game_total=total_d,
        game_id=game_id,
        opponent=opponent,
        season=season,
        week=week,
        provenance=provenance,
        extra=dict(extra or {}),
        teased_spread=teased_spread(spread_d, teaser_points=teaser_points),
        geometry=classify_geometry(lg, spread_d),
        secondary_reason=secondary_label(lg, spread_d),
        geometry_track=track_for(lg, spread_d),
        total_ok=passes_total_guardrail(lg, total_d),
        key_numbers_crossed=crossings,
        bump=bump_for_leg(lg, spread_d, teaser_points=teaser_points),
        p_raw=p_raw(total_d, teaser_points=teaser_points),
        p_est=p_est(lg, spread_d, total_d, teaser_points=teaser_points),
    )


def eligible_primary_nfl_legs(legs: Iterable[Leg]) -> list[Leg]:
    """Filter to legs that qualify for the live primary NFL track.

    Requires NFL, primary geometry, and the NFL total guardrail. Order is not imposed
    here; :func:`~teaser_model_v1.engine.tickets.select_top_legs` does the ranking.
    """
    return [leg for leg in legs if leg.league == "NFL" and leg.qualifies_primary]


def legs_by_game(legs: Sequence[Leg]) -> dict[str | None, list[Leg]]:
    """Group legs by ``game_id``. Used by reporting, never by the frozen selection rules."""
    grouped: dict[str | None, list[Leg]] = {}
    for leg in legs:
        grouped.setdefault(leg.game_id, []).append(leg)
    return grouped
