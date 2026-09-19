"""Research view: every side on the board, teased 6 points. **Display only.**

This module answers a question the live card deliberately does not: *what does every
other side look like after a 6-point tease?* It is a lens on the board, never an input
to it.

**It cannot affect the card.** It builds legs through the frozen engine's
:func:`~teaser_model_v1.engine.legs.build_leg`, reads their classification, and returns
rows. It defines no probability formula, performs no ranking that feeds selection,
constructs no ticket, and is never consulted by grading, re-check or placement. The
top-four cut, ticket construction, EV, exposure and the proposed card are computed
entirely without it.

Two properties are load-bearing and are pinned by tests:

* **No secondary leg is ever promoted.** The track comes from the engine's
  classification, so an NFL secondary geometry is ``PAPER`` no matter how high its
  ``P_est`` runs. A high number on a secondary shape is a research observation, not an
  eligibility argument.
* **A teased line on a whole number can push**, and v1.0 does not model book-specific
  push settlement. Those rows are flagged so their ``P_est`` is never read as a
  settlement-accurate estimate.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from teaser_model_v1.engine.constants import Geometry, Track
from teaser_model_v1.engine.legs import build_leg
from teaser_model_v1.engine.numeric import is_whole_number

#: The exact label required wherever a teased line can land on the number.
PUSH_NOT_MODELED = "RESEARCH P_est — PUSH SETTLEMENT NOT MODELED"

QUALIFIES = "—"
FAILS_GUARDRAIL = "FAILS TOTAL GUARDRAIL"
SECONDARY_WHOLE = "SECONDARY GEOMETRY (whole-number line)"
SECONDARY_OTHER = "SECONDARY GEOMETRY (other half-point shape)"


@dataclass(frozen=True)
class TeasedBoardRow:
    """One side of one game, teased. Full precision kept; formatting is the report's job."""

    team: str
    opponent: str
    spread: Decimal
    teased_spread: Decimal
    total: Decimal
    key_numbers_crossed: int
    p_est: float
    geometry_class: str
    track: str
    exclusion_reason: str
    can_push: bool
    on_live_board: bool

    @property
    def is_primary_live(self) -> bool:
        return (
            self.geometry_class == Geometry.PRIMARY.value
            and self.track == Track.LIVE.value
        )


def _exclusion_reason(leg) -> str:
    """Why this side is not on the live board. Reads the engine's verdict, never re-derives."""
    reasons = []
    if not leg.is_primary_geometry:
        reasons.append(
            SECONDARY_WHOLE if leg.classification.secondary_reason == "whole_number_line"
            else SECONDARY_OTHER
        )
    if not leg.total_ok:
        reasons.append(FAILS_GUARDRAIL)
    return " · ".join(reasons) if reasons else QUALIFIES


def teased_board_rows(snapshot) -> list[TeasedBoardRow]:
    """Every quoted side, teased 6 points through the frozen engine.

    Sorted PRIMARY/LIVE first by ``P_est`` descending, then everything else by ``P_est``
    descending. This ordering is for reading only — it is not the model's ranking and
    feeds nothing.
    """
    rows: list[TeasedBoardRow] = []
    for quote in snapshot.quotes:
        leg = build_leg(
            leg_id=f"{quote.game_id}-{quote.team}",
            league="NFL",
            team=quote.team,
            spread=quote.spread,
            game_total=quote.total,
            game_id=quote.game_id,
            opponent=quote.away_team if quote.team == quote.home_team else quote.home_team,
        )
        rows.append(
            TeasedBoardRow(
                team=leg.team,
                opponent=leg.opponent or "",
                spread=leg.spread,
                teased_spread=leg.teased_spread,
                total=leg.game_total,
                key_numbers_crossed=leg.key_numbers_crossed,
                p_est=leg.p_est,
                geometry_class=leg.geometry_class.value,
                track=leg.track.value,
                exclusion_reason=_exclusion_reason(leg),
                can_push=is_whole_number(leg.teased_spread),
                on_live_board=leg.is_primary_geometry and leg.total_ok,
            )
        )
    rows.sort(key=lambda r: (not r.is_primary_live, -r.p_est, r.team))
    return rows


def teased_board_summary(rows) -> dict:
    """Highest primary, highest secondary, and any secondary that outranks a primary.

    An overlap here is an observation about two different populations, not a finding that
    the model is mis-specified and emphatically not a reason to promote anything.
    """
    primary = [r for r in rows if r.is_primary_live]
    secondary = [r for r in rows if not r.is_primary_live]
    best_primary = max(primary, key=lambda r: r.p_est, default=None)
    best_secondary = max(secondary, key=lambda r: r.p_est, default=None)
    outranking = (
        [r for r in secondary if best_primary and r.p_est > min(p.p_est for p in primary)]
        if primary else []
    )
    outranking.sort(key=lambda r: -r.p_est)
    return {
        "best_primary": best_primary,
        "best_secondary": best_secondary,
        "secondary_outranking_a_primary": outranking,
        "n_primary": len(primary),
        "n_secondary": len(secondary),
    }
