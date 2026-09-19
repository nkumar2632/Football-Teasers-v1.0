"""Placement-time re-check.

Specification §10: immediately before any real wager, re-check the current spread, teased
spread, geometry, total and exact teaser payout, and recompute `P_est`, break-even and EV.

If a constituent leg leaves primary geometry, exceeds the total guardrail, disappears from
the market or carries invalid data — or if the ticket is no longer positive EV — the
pre-placement ticket is **DISCARDED** and the card is rebuilt from the current board.

The three things this module must never do:

* substitute another team for a leg that moved;
* downgrade a 3-team ticket to a 2-team ticket;
* reuse a stale ticket.

Note the vocabulary: a ticket that fails here is **discarded**. "Void" is reserved for a
sportsbook's settlement of a wager that was actually placed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from teaser_model_v1.engine.classification import classify
from teaser_model_v1.engine.constants import Geometry, Track
from teaser_model_v1.engine.geometry import passes_total_guardrail, teased_spread
from teaser_model_v1.engine.probability import p_est
from teaser_model_v1.live.card import WeeklyCard, grade_week, ticket_key_for
from teaser_model_v1.live.provenance import iso, new_record_id, utc_now
from teaser_model_v1.live.schemas import MarketSnapshot, TeaserPriceSnapshot

VALIDATED = "VALIDATED"
DISCARD_REBUILD = "DISCARD — REBUILD REQUIRED"
NOT_YET_RECHECKED = "NOT YET RECHECKED"


class StaleSnapshotError(ValueError):
    """Raised when a re-check is attempted against the snapshot it is meant to replace."""


@dataclass(frozen=True)
class LegRecheck:
    leg_id: str
    ok: bool
    reasons: tuple
    old_spread: str
    new_spread: str
    old_total: str
    new_total: str
    old_p_est: str
    new_p_est: str

    def to_dict(self) -> dict:
        return {
            "leg_id": self.leg_id,
            "ok": self.ok,
            "reasons": list(self.reasons),
            "old_spread": self.old_spread,
            "new_spread": self.new_spread,
            "old_total": self.old_total,
            "new_total": self.new_total,
            "old_p_est": self.old_p_est,
            "new_p_est": self.new_p_est,
        }


@dataclass(frozen=True)
class TicketRecheck:
    ticket_key: str
    n_legs: int
    verdict: str
    reasons: tuple
    legs: tuple
    old_ev: str
    new_ev: str
    new_break_even: str
    new_p_ticket: str

    @property
    def leg_ids(self) -> tuple:
        """The legs this ticket is made of, in the order they were checked."""
        return tuple(leg.leg_id for leg in self.legs)

    @property
    def failing_legs(self) -> tuple:
        """Only the legs that failed, for reporting the cause of a discard."""
        return tuple(leg for leg in self.legs if not leg.ok)

    def to_dict(self) -> dict:
        return {
            "ticket_key": self.ticket_key,
            "n_legs": self.n_legs,
            "verdict": self.verdict,
            "reasons": list(self.reasons),
            "legs": [leg.to_dict() for leg in self.legs],
            "old_ev": self.old_ev,
            "new_ev": self.new_ev,
            "new_break_even": self.new_break_even,
            "new_p_ticket": self.new_p_ticket,
        }


@dataclass(frozen=True)
class RecheckResult:
    """Outcome of re-checking a proposed card against a new board."""

    season: int
    week: int
    rechecked_at: datetime
    original_card_id: str
    original_market_snapshot_id: str
    original_price_snapshot_id: str
    new_market_snapshot_id: str
    new_price_snapshot_id: str
    tickets: tuple
    rebuilt_card: WeeklyCard | None
    recheck_id: str = ""

    def __post_init__(self) -> None:
        if not self.recheck_id:
            object.__setattr__(
                self, "recheck_id",
                new_record_id(f"rck_{self.season}w{self.week:02d}", self._hash_payload()),
            )

    def _hash_payload(self) -> dict:
        return {
            "kind": "recheck",
            "season": self.season,
            "week": self.week,
            "rechecked_at": iso(self.rechecked_at),
            "original_card_id": self.original_card_id,
            "original_market_snapshot_id": self.original_market_snapshot_id,
            "original_price_snapshot_id": self.original_price_snapshot_id,
            "new_market_snapshot_id": self.new_market_snapshot_id,
            "new_price_snapshot_id": self.new_price_snapshot_id,
            "tickets": [ticket.to_dict() for ticket in self.tickets],
        }

    def to_dict(self) -> dict:
        payload = self._hash_payload()
        payload["recheck_id"] = self.recheck_id
        payload["rebuilt_card_id"] = self.rebuilt_card.card_id if self.rebuilt_card else ""
        payload["any_discarded"] = self.any_discarded
        return payload

    @property
    def validated(self) -> tuple:
        return tuple(t for t in self.tickets if t.verdict == VALIDATED)

    @property
    def discarded(self) -> tuple:
        return tuple(t for t in self.tickets if t.verdict == DISCARD_REBUILD)

    @property
    def any_discarded(self) -> bool:
        return bool(self.discarded)

    @property
    def overall(self) -> str:
        return DISCARD_REBUILD if self.any_discarded else VALIDATED


def _quote_index(market: MarketSnapshot) -> dict:
    return {quote.leg_key: quote for quote in market.quotes}


def recheck_card(
    card: WeeklyCard,
    new_market: MarketSnapshot,
    new_prices: TeaserPriceSnapshot | None,
    *,
    rechecked_at: datetime | None = None,
    tickets_to_check: tuple | None = None,
) -> RecheckResult:
    """Re-check a proposed card against a NEW market and price snapshot.

    Requires genuinely new snapshots: re-checking against the same market snapshot the card
    was graded from proves nothing, so it is refused.
    """
    rechecked_at = rechecked_at or utc_now()

    if new_market.snapshot_id == card.market_snapshot_id:
        raise StaleSnapshotError(
            "re-check requires a NEW market snapshot; this is the one the card was graded "
            "from. Capture the current board first."
        )
    if (new_market.season, new_market.week) != (card.season, card.week):
        raise ValueError("new market snapshot is for a different season/week")

    quotes = _quote_index(new_market)
    profit_by_size = new_prices.profit_by_size() if new_prices else {}

    keys = set(tickets_to_check) if tickets_to_check else set(card.selected_ticket_keys)
    checked = []

    for view in card.tickets:
        if view.ticket_key not in keys:
            continue

        leg_checks, ticket_reasons = [], []
        p_ticket = 1.0
        all_ok = True

        for leg_id in view.leg_ids:
            original = next(
                (leg for leg in card.qualifying_legs if leg.leg_id == leg_id), None
            )
            quote = quotes.get(leg_id)
            reasons = []

            if quote is None:
                reasons.append("leg has disappeared from the current market")
                leg_checks.append(
                    LegRecheck(leg_id, False, tuple(reasons),
                               str(original.spread) if original else "",
                               "", str(original.total) if original else "", "",
                               repr(original.p_est) if original else "", "")
                )
                # The reason must reach the ticket too: a discard with no stated cause
                # is useless in the audit record.
                ticket_reasons.extend(f"{leg_id}: {reason}" for reason in reasons)
                all_ok = False
                continue

            classification = classify("NFL", quote.spread)
            if classification.geometry_class is not Geometry.PRIMARY:
                reasons.append(
                    f"line moved to {quote.spread}, which is not primary geometry"
                )
            if classification.track is not Track.LIVE:
                reasons.append("leg is no longer on the LIVE track")
            if not passes_total_guardrail("NFL", quote.total):
                reasons.append(f"total moved to {quote.total}, above the NFL guardrail of 47")

            new_p = None
            if not reasons:
                new_p = p_est("NFL", quote.spread, quote.total)
                p_ticket *= new_p
            else:
                all_ok = False

            leg_checks.append(
                LegRecheck(
                    leg_id=leg_id,
                    ok=not reasons,
                    reasons=tuple(reasons),
                    old_spread=str(original.spread) if original else "",
                    new_spread=str(quote.spread),
                    old_total=str(original.total) if original else "",
                    new_total=str(quote.total),
                    old_p_est=repr(original.p_est) if original else "",
                    new_p_est=repr(new_p) if new_p is not None else "",
                )
            )
            ticket_reasons.extend(f"{leg_id}: {reason}" for reason in reasons)

        new_profit = profit_by_size.get(view.n_legs)
        if new_profit is None:
            all_ok = False
            ticket_reasons.append(
                f"no current price for a {view.n_legs}-team teaser; EV is UNAVAILABLE"
            )
            new_ev = new_break_even = ""
        elif all_ok:
            new_break_even_value = 1.0 / (1.0 + new_profit)
            new_ev_value = p_ticket * new_profit - (1.0 - p_ticket)
            new_ev, new_break_even = repr(new_ev_value), repr(new_break_even_value)
            if new_ev_value <= 0:
                all_ok = False
                ticket_reasons.append(
                    f"ticket is no longer positive EV at the current price "
                    f"(EV {new_ev_value:+.6f})"
                )
        else:
            new_ev = new_break_even = ""

        checked.append(
            TicketRecheck(
                ticket_key=view.ticket_key,
                n_legs=view.n_legs,
                verdict=VALIDATED if all_ok else DISCARD_REBUILD,
                reasons=tuple(ticket_reasons),
                legs=tuple(leg_checks),
                old_ev=view.ev_per_unit,
                new_ev=new_ev,
                new_break_even=new_break_even,
                new_p_ticket=repr(p_ticket) if all_ok else "",
            )
        )

    # A discard means rebuild from the current board — never substitute or downgrade.
    any_discarded = any(t.verdict == DISCARD_REBUILD for t in checked)
    rebuilt = (
        grade_week(new_market, new_prices, graded_at=rechecked_at,
                   notes=f"rebuilt after re-check of card {card.card_id}")
        if any_discarded
        else None
    )

    return RecheckResult(
        season=card.season,
        week=card.week,
        rechecked_at=rechecked_at,
        original_card_id=card.card_id,
        original_market_snapshot_id=card.market_snapshot_id,
        original_price_snapshot_id=card.price_snapshot_id,
        new_market_snapshot_id=new_market.snapshot_id,
        new_price_snapshot_id=new_prices.snapshot_id if new_prices else "",
        tickets=tuple(checked),
        rebuilt_card=rebuilt,
    )
