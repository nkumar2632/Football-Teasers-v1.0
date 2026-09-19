"""The teaser leg: an immutable value object carrying its own v1.0 classification.

A :class:`Leg` is pure data plus the frozen model's verdict on it. It knows nothing about
where its numbers came from; ingestion lives in :mod:`teaser_model_v1.ingest`.

The leg's classification is held as a single
:class:`~teaser_model_v1.engine.classification.LegClassification` value carrying **both**
dimensions — geometry class and operational track. They are never stored as one field and
never inferred from each other.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable, Sequence

from teaser_model_v1.engine.classification import LegClassification, classify
from teaser_model_v1.engine.constants import CFB, NFL, TEASER_POINTS, Geometry, Track
from teaser_model_v1.engine.geometry import passes_total_guardrail, teased_spread
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
    classification: LegClassification = LegClassification(
        geometry_class=Geometry.SECONDARY, track=Track.PAPER
    )
    total_ok: bool = False
    key_numbers_crossed: int = 0
    bump: float = 0.0
    p_raw: float = 0.0
    p_est: float = 0.0

    # ---- Dimension 1: geometry class -------------------------------------------------

    @property
    def geometry_class(self) -> Geometry:
        """PRIMARY or SECONDARY — the shape of the line, in either league."""
        return self.classification.geometry_class

    @property
    def is_primary_geometry(self) -> bool:
        """True for CFB primary geometry as well as NFL primary geometry."""
        return self.classification.is_primary

    @property
    def secondary_reason(self) -> str | None:
        return self.classification.secondary_reason

    # ---- Dimension 2: operational track ----------------------------------------------

    @property
    def track(self) -> Track:
        """LIVE or PAPER — only NFL primary geometry is LIVE."""
        return self.classification.track

    @property
    def is_live_track(self) -> bool:
        return self.classification.is_live_track

    # ---- Combined eligibility --------------------------------------------------------

    @property
    def qualifies_primary(self) -> bool:
        """Primary **geometry** and inside the league total guardrail.

        League-independent: a CFB primary leg inside the CFB guardrail qualifies here.
        This is a research-track question. It is *not* live eligibility.
        """
        return self.is_primary_geometry and self.total_ok

    @property
    def qualifies_live_primary(self) -> bool:
        """Live eligibility: NFL primary geometry inside the NFL guardrail."""
        return self.is_live_track and self.total_ok

    def classification_label(self) -> str:
        """``'PRIMARY/PAPER'`` — both dimensions, always reported together."""
        return self.classification.label()

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
        classification=classify(lg, spread_d),
        total_ok=passes_total_guardrail(lg, total_d),
        key_numbers_crossed=crossings,
        bump=bump_for_leg(lg, spread_d, teaser_points=teaser_points),
        p_raw=p_raw(total_d, teaser_points=teaser_points),
        p_est=p_est(lg, spread_d, total_d, teaser_points=teaser_points),
    )


def eligible_live_primary_legs(legs: Iterable[Leg]) -> list[Leg]:
    """Filter to legs eligible for the **live** track: NFL primary geometry, total OK.

    This is the filter the frozen weekly construction uses. CFB primary legs are
    deliberately excluded — not because they are not primary geometry, but because they
    are on the paper track.
    """
    return [leg for leg in legs if leg.qualifies_live_primary]


#: Retained name from Phase 1. Identical behaviour to
#: :func:`eligible_live_primary_legs`; the newer name states which dimension it filters on.
eligible_primary_nfl_legs = eligible_live_primary_legs


def primary_geometry_legs(legs: Iterable[Leg], league: str | None = None) -> list[Leg]:
    """Filter to legs with primary **geometry**, in either league, total guardrail applied.

    Research helper for the paper track — it is how CFB primary geometry stays visible and
    distinguishable from CFB secondary geometry. It confers no live eligibility.
    """
    lg = normalize_league(league) if league is not None else None
    return [
        leg
        for leg in legs
        if leg.qualifies_primary and (lg is None or leg.league == lg)
    ]


def paper_track_legs(legs: Iterable[Leg]) -> list[Leg]:
    """Every leg on the paper/research track: NFL secondary plus all college football."""
    return [leg for leg in legs if not leg.is_live_track]


def legs_by_classification(legs: Iterable[Leg]) -> dict[tuple[str, str, str], list[Leg]]:
    """Group legs by ``(league, geometry_class, track)``.

    The grouping key keeps both dimensions explicit, so a research cut can never collapse
    "CFB primary" into "CFB secondary" or into "NFL primary".
    """
    grouped: dict[tuple[str, str, str], list[Leg]] = {}
    for leg in legs:
        key = (leg.league, leg.geometry_class.value, leg.track.value)
        grouped.setdefault(key, []).append(leg)
    return grouped


def legs_by_game(legs: Sequence[Leg]) -> dict[str | None, list[Leg]]:
    """Group legs by ``game_id``. Used by reporting, never by the frozen selection rules."""
    grouped: dict[str | None, list[Leg]] = {}
    for leg in legs:
        grouped.setdefault(leg.game_id, []).append(leg)
    return grouped
