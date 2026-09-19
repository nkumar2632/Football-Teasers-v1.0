"""Settlement of actually-placed wagers.

Two results are recorded **separately and never merged**:

* ``model_result`` — what frozen v1.0 says happened, graded from the final score against
  the teased line. For live-primary half-point geometry this is WIN or LOSS; a PUSH is
  impossible and is surfaced as an error rather than absorbed.
* ``book_settlement`` — what the sportsbook actually did, in the book's own vocabulary,
  including VOID or CANCELLED.

These can legitimately disagree — a book may void a wager the model graded a winner. When
they do, both stand as recorded; no generic rule is invented to reconcile them.

"Void" belongs only here, to a wager that was actually placed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from teaser_model_v1.analysis.grading import Outcome, grade_teased_leg
from teaser_model_v1.live.provenance import iso, new_record_id, require_aware
from teaser_model_v1.live.schemas import MarketValidationError

#: Sportsbook settlement vocabulary. The model never produces these; only a book does.
BOOK_WIN = "WIN"
BOOK_LOSS = "LOSS"
BOOK_PUSH = "PUSH"
BOOK_VOID = "VOID"
BOOK_CANCELLED = "CANCELLED"
BOOK_SETTLEMENTS = frozenset(
    {BOOK_WIN, BOOK_LOSS, BOOK_PUSH, BOOK_VOID, BOOK_CANCELLED}
)


class PrimaryPushInSettlement(AssertionError):
    """A live-primary leg graded PUSH, which the half-point geometry makes impossible."""


@dataclass(frozen=True)
class LegSettlement:
    leg_id: str
    team: str
    teased_spread: str
    home_score: int | None
    away_score: int | None
    final_margin: int | None
    model_result: str
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "leg_id": self.leg_id,
            "team": self.team,
            "teased_spread": self.teased_spread,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "final_margin": self.final_margin,
            "model_result": self.model_result,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class SettlementRecord:
    """Settlement of one placed wager."""

    placement_id: str
    season: int
    week: int
    settled_at: datetime
    legs: tuple
    model_ticket_result: str
    book_settlement: str
    profit_loss_units: float
    settled_by: str = ""
    book_reference: str = ""
    notes: str = ""
    settlement_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "settled_at", require_aware(self.settled_at, field="settled_at"))
        if self.book_settlement not in BOOK_SETTLEMENTS:
            raise MarketValidationError(
                f"book_settlement must be one of {sorted(BOOK_SETTLEMENTS)}, "
                f"got {self.book_settlement!r}"
            )
        if not self.settlement_id:
            object.__setattr__(
                self, "settlement_id",
                new_record_id(f"stl_{self.season}w{self.week:02d}", self._hash_payload()),
            )

    def _hash_payload(self) -> dict:
        return {
            "kind": "settlement",
            "placement_id": self.placement_id,
            "season": self.season,
            "week": self.week,
            "settled_at": iso(self.settled_at),
            "legs": [leg.to_dict() for leg in self.legs],
            "model_ticket_result": self.model_ticket_result,
            "book_settlement": self.book_settlement,
            "profit_loss_units": self.profit_loss_units,
            "settled_by": self.settled_by,
            "book_reference": self.book_reference,
        }

    def to_dict(self) -> dict:
        payload = self._hash_payload()
        payload["settlement_id"] = self.settlement_id
        payload["notes"] = self.notes
        payload["results_agree"] = self.results_agree
        return payload

    @property
    def results_agree(self) -> bool:
        """Whether the model's grade and the book's settlement coincide."""
        return self.model_ticket_result == self.book_settlement


def grade_leg_settlement(
    *,
    leg_id: str,
    team: str,
    teased_spread,
    final_margin: int,
    home_score: int | None = None,
    away_score: int | None = None,
    allow_push: bool = False,
    notes: str = "",
) -> LegSettlement:
    """Grade one placed leg from the final score, per frozen v1.0.

    ``final_margin`` is signed from *team*'s perspective. A PUSH on live-primary geometry
    is impossible and raises unless ``allow_push`` is set, which exists only so a
    non-primary or corrected record can be captured deliberately.
    """
    outcome = grade_teased_leg(final_margin, teased_spread)
    if outcome is Outcome.PUSH and not allow_push:
        raise PrimaryPushInSettlement(
            f"{leg_id}: teased line {teased_spread} against margin {final_margin} graded "
            "PUSH. Every live-primary teased line is a half-point, so this cannot happen — "
            "check the recorded line and score before continuing."
        )
    return LegSettlement(
        leg_id=leg_id,
        team=team,
        teased_spread=str(teased_spread),
        home_score=home_score,
        away_score=away_score,
        final_margin=final_margin,
        model_result=outcome.value,
        notes=notes,
    )


def settle_ticket(
    *,
    placement: dict,
    legs: tuple,
    book_settlement: str,
    settled_at: datetime,
    profit_loss_units: float | None = None,
    settled_by: str = "",
    book_reference: str = "",
    notes: str = "",
) -> SettlementRecord:
    """Settle one placed wager, keeping the model grade and the book result separate.

    ``profit_loss_units`` should be what the book actually paid. If omitted it is derived
    from the recorded price for a clean WIN/LOSS, and left at 0 for VOID or CANCELLED —
    but a supplied value always wins, because the book's arithmetic is the truth for a
    placed wager.
    """
    model_result = (
        "WIN" if all(leg.model_result == "WIN" for leg in legs) else "LOSS"
    )

    if profit_loss_units is None:
        if book_settlement in (BOOK_VOID, BOOK_CANCELLED, BOOK_PUSH):
            profit_loss_units = 0.0
        else:
            stake = float(placement.get("stake_units", 1.0))
            american = Decimal(str(placement.get("american_odds", "0")))
            if american == 0:
                raise MarketValidationError(
                    "cannot derive profit/loss without a recorded price; supply "
                    "profit_loss_units explicitly"
                )
            profit_per_unit = (
                american / Decimal(100) if american > 0 else Decimal(100) / abs(american)
            )
            profit_loss_units = (
                float(profit_per_unit) * stake if book_settlement == BOOK_WIN else -stake
            )

    return SettlementRecord(
        placement_id=placement["placement_id"],
        season=placement["season"],
        week=placement["week"],
        settled_at=settled_at,
        legs=tuple(legs),
        model_ticket_result=model_result,
        book_settlement=book_settlement,
        profit_loss_units=float(profit_loss_units),
        settled_by=settled_by,
        book_reference=book_reference,
        notes=notes,
    )
