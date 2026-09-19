"""Grading-time board and PROPOSED live card.

Every model decision here is delegated to :mod:`teaser_model_v1.engine`:

* geometry and the total guardrail — ``build_leg`` / ``eligible_live_primary_legs``
* ranking and the top four — ``select_top_legs``
* combinations and EV — ``generate_tickets``
* the positive-EV, descending-EV, 2-unit-capped walk — ``select_live_tickets``

This module contributes no model rule of its own. It arranges inputs, records provenance,
and formats output.

A card produced here is **PROPOSED**. It is not a bet, not a placement, and not evidence
that anything was wagered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from teaser_model_v1.engine.constants import (
    MAX_UNITS_PER_LEG_PER_WEEK,
    MIN_LEGS_FOR_ANY_TICKET,
    TOP_N_LEGS,
    UNITS_PER_TICKET,
)
from teaser_model_v1.engine.legs import build_leg, eligible_live_primary_legs
from teaser_model_v1.engine.presentation import PROBABILITY_LABEL, format_probability_pct
from teaser_model_v1.engine.tickets import (
    generate_tickets,
    rank_tickets,
    select_live_tickets,
    select_top_legs,
)
from teaser_model_v1.live.provenance import iso, new_record_id, utc_now
from teaser_model_v1.live.schemas import MarketSnapshot, TeaserPriceSnapshot

NO_TICKET_MESSAGE = "NO CONSTRUCTIBLE LIVE PRIMARY TICKET"
UNAVAILABLE = "UNAVAILABLE"

#: A card's lifecycle status. PROPOSED never becomes PLACED on its own.
STATUS_PROPOSED = "PROPOSED"
STATUS_NO_TICKET = "NO_CONSTRUCTIBLE_TICKET"


@dataclass(frozen=True)
class GradedLeg:
    """One qualifying primary leg, as the frozen model sees it."""

    rank: int
    leg_id: str
    game_id: str
    team: str
    opponent: str
    spread: Decimal
    teased_spread: Decimal
    total: Decimal
    geometry_class: str
    track: str
    key_numbers_crossed: int
    p_raw: float
    bump: float
    p_est: float
    kickoff: str
    sportsbook: str
    market_snapshot_id: str

    @property
    def displayed_probability(self) -> str:
        """Whole-percent display. The label is mandatory wherever this appears."""
        return format_probability_pct(self.p_est)

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "leg_id": self.leg_id,
            "game_id": self.game_id,
            "team": self.team,
            "opponent": self.opponent,
            "spread": str(self.spread),
            "teased_spread": str(self.teased_spread),
            "total": str(self.total),
            "geometry_class": self.geometry_class,
            "track": self.track,
            "key_numbers_crossed": self.key_numbers_crossed,
            "p_raw": repr(self.p_raw),
            "bump": repr(self.bump),
            "p_est": repr(self.p_est),
            "displayed_probability": self.displayed_probability,
            "probability_label": PROBABILITY_LABEL,
            "kickoff": self.kickoff,
            "sportsbook": self.sportsbook,
            "market_snapshot_id": self.market_snapshot_id,
        }


@dataclass(frozen=True)
class TicketView:
    """One constructible ticket with its pricing, shown whether or not it is positive EV."""

    ticket_key: str
    n_legs: int
    leg_ids: tuple
    teams: tuple
    p_ticket: float
    offered_american: str
    offered_decimal: str
    net_profit_per_unit: str
    break_even: str
    ev_per_unit: str
    ev_percent: str
    status: str
    selected: bool
    price_snapshot_id: str

    def to_dict(self) -> dict:
        return {
            "ticket_key": self.ticket_key,
            "n_legs": self.n_legs,
            "leg_ids": list(self.leg_ids),
            "teams": list(self.teams),
            "p_ticket": repr(self.p_ticket),
            "displayed_probability": format_probability_pct(self.p_ticket),
            "offered_american": self.offered_american,
            "offered_decimal": self.offered_decimal,
            "net_profit_per_unit": self.net_profit_per_unit,
            "break_even": self.break_even,
            "ev_per_unit": self.ev_per_unit,
            "ev_percent": self.ev_percent,
            "status": self.status,
            "selected": self.selected,
            "price_snapshot_id": self.price_snapshot_id,
        }


@dataclass(frozen=True)
class WeeklyCard:
    """The grading-time output: qualifying legs, the full ticket board, and a proposal."""

    season: int
    week: int
    graded_at: datetime
    market_snapshot_id: str
    price_snapshot_id: str
    sportsbook: str
    games_scanned: int
    qualifying_legs: tuple
    top_legs: tuple
    tickets: tuple
    selected_ticket_keys: tuple
    exposure: dict
    status: str
    card_id: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.card_id:
            object.__setattr__(
                self, "card_id",
                new_record_id(f"card_{self.season}w{self.week:02d}", self._hash_payload()),
            )

    def _hash_payload(self) -> dict:
        return {
            "kind": "weekly_card",
            "season": self.season,
            "week": self.week,
            "graded_at": iso(self.graded_at),
            "market_snapshot_id": self.market_snapshot_id,
            "price_snapshot_id": self.price_snapshot_id,
            "sportsbook": self.sportsbook,
            "games_scanned": self.games_scanned,
            "qualifying_legs": [leg.to_dict() for leg in self.qualifying_legs],
            "top_legs": [leg.leg_id for leg in self.top_legs],
            "tickets": [ticket.to_dict() for ticket in self.tickets],
            "selected_ticket_keys": list(self.selected_ticket_keys),
            "exposure": dict(sorted(self.exposure.items())),
            "status": self.status,
        }

    def to_dict(self) -> dict:
        payload = self._hash_payload()
        payload["card_id"] = self.card_id
        payload["notes"] = self.notes
        payload["placement_status"] = "PROPOSED — nothing has been wagered"
        return payload

    @property
    def n_qualifying(self) -> int:
        return len(self.qualifying_legs)

    @property
    def n_positive_ev(self) -> int:
        return sum(1 for ticket in self.tickets if ticket.status == "POSITIVE_EV")

    @property
    def selected_tickets(self) -> tuple:
        keys = set(self.selected_ticket_keys)
        return tuple(t for t in self.tickets if t.ticket_key in keys)

    def ticket(self, ticket_key: str) -> TicketView | None:
        for view in self.tickets:
            if view.ticket_key == ticket_key:
                return view
        return None


def ticket_key_for(leg_ids) -> str:
    """Stable identity for a ticket: its legs, order-independent."""
    return "|".join(sorted(leg_ids))


def _legs_from_snapshot(market: MarketSnapshot) -> list:
    return [
        build_leg(
            leg_id=quote.leg_key,
            league="NFL",
            team=quote.team,
            spread=quote.spread,
            game_total=quote.total,
            game_id=quote.game_id,
            opponent=quote.opponent,
            season=quote.season,
            week=quote.week,
            provenance=f"market_snapshot:{market.snapshot_id}",
            extra={"kickoff": iso(quote.kickoff), "sportsbook": quote.sportsbook},
        )
        for quote in market.quotes
    ]


def grade_week(
    market: MarketSnapshot,
    prices: TeaserPriceSnapshot | None,
    *,
    graded_at: datetime | None = None,
    notes: str = "",
) -> WeeklyCard:
    """Build the frozen v1.0 weekly board from one market and one actual-price snapshot.

    ``prices`` may be ``None`` or may omit a ticket size. In that case those tickets are
    still constructed and displayed with their probability, but break-even and EV are
    ``UNAVAILABLE`` and they can never be placement-eligible.
    """
    graded_at = graded_at or utc_now()
    if prices is not None and (prices.season, prices.week) != (market.season, market.week):
        raise ValueError(
            "price snapshot is for a different season/week than the market snapshot"
        )

    legs = _legs_from_snapshot(market)
    qualifying = eligible_live_primary_legs(legs)
    ranked = sorted(qualifying, key=lambda leg: leg.sort_key())

    graded = tuple(
        GradedLeg(
            rank=position,
            leg_id=leg.leg_id,
            game_id=leg.game_id or "",
            team=leg.team,
            opponent=leg.opponent or "",
            spread=leg.spread,
            teased_spread=leg.teased_spread,
            total=leg.game_total,
            geometry_class=leg.geometry_class.value,
            track=leg.track.value,
            key_numbers_crossed=leg.key_numbers_crossed,
            p_raw=leg.p_raw,
            bump=leg.bump,
            p_est=leg.p_est,
            kickoff=leg.extra.get("kickoff", ""),
            sportsbook=leg.extra.get("sportsbook", market.sportsbook),
            market_snapshot_id=market.snapshot_id,
        )
        for position, leg in enumerate(ranked, start=1)
    )

    top = select_top_legs(qualifying, top_n=TOP_N_LEGS)
    top_graded = tuple(leg for leg in graded if leg.leg_id in {t.leg_id for t in top})

    if len(top) < MIN_LEGS_FOR_ANY_TICKET:
        return WeeklyCard(
            season=market.season,
            week=market.week,
            graded_at=graded_at,
            market_snapshot_id=market.snapshot_id,
            price_snapshot_id=prices.snapshot_id if prices else "",
            sportsbook=market.sportsbook,
            games_scanned=len(market.games),
            qualifying_legs=graded,
            top_legs=top_graded,
            tickets=(),
            selected_ticket_keys=(),
            exposure={},
            status=STATUS_NO_TICKET,
            notes=notes or NO_TICKET_MESSAGE,
        )

    profit_by_size = prices.profit_by_size() if prices else {}
    # price_is_hypothetical=False: these are ACTUAL observed menu prices.
    tickets = generate_tickets(
        top,
        profit_by_size,
        price_is_hypothetical=False,
        price_provenance=prices.snapshot_id if prices else "",
    )
    selection = select_live_tickets(tickets)
    selected_keys = {ticket_key_for(t.leg_ids) for t in selection.selected}

    views = []
    for ticket in rank_tickets(tickets):
        key = ticket_key_for(ticket.leg_ids)
        quote = prices.quote_for(ticket.n_legs) if prices else None
        if ticket.ev is None:
            status = "NO_PRICE — not placement-eligible"
            offered_american = offered_decimal = net_profit = UNAVAILABLE
            break_even = ev = ev_percent = UNAVAILABLE
        else:
            status = "POSITIVE_EV" if ticket.is_positive_ev else "NEGATIVE_EV"
            offered_american = str(quote.american_odds) if quote else UNAVAILABLE
            offered_decimal = str(quote.decimal_odds) if quote else UNAVAILABLE
            net_profit = repr(ticket.profit)
            break_even = repr(ticket.break_even)
            ev = repr(ticket.ev)
            ev_percent = f"{ticket.ev * 100:.2f}%"
        views.append(
            TicketView(
                ticket_key=key,
                n_legs=ticket.n_legs,
                leg_ids=ticket.leg_ids,
                teams=tuple(leg.team for leg in ticket.legs),
                p_ticket=ticket.p_ticket,
                offered_american=offered_american,
                offered_decimal=offered_decimal,
                net_profit_per_unit=net_profit,
                break_even=break_even,
                ev_per_unit=ev,
                ev_percent=ev_percent,
                status=status,
                selected=key in selected_keys,
                price_snapshot_id=prices.snapshot_id if prices else "",
            )
        )

    return WeeklyCard(
        season=market.season,
        week=market.week,
        graded_at=graded_at,
        market_snapshot_id=market.snapshot_id,
        price_snapshot_id=prices.snapshot_id if prices else "",
        sportsbook=market.sportsbook,
        games_scanned=len(market.games),
        qualifying_legs=graded,
        top_legs=top_graded,
        tickets=tuple(views),
        selected_ticket_keys=tuple(
            view.ticket_key for view in views if view.selected
        ),
        exposure=dict(selection.exposure),
        status=STATUS_PROPOSED,
        notes=notes,
    )


def exposure_after(existing: dict, leg_ids, units: int = UNITS_PER_TICKET) -> dict:
    """Aggregate leg exposure once *leg_ids* are added."""
    updated = dict(existing)
    for leg_id in leg_ids:
        updated[leg_id] = updated.get(leg_id, 0) + units
    return updated


def exposure_violations(exposure: dict, cap: int = MAX_UNITS_PER_LEG_PER_WEEK) -> dict:
    """Legs over the frozen aggregate cap, if any."""
    return {leg: units for leg, units in exposure.items() if units > cap}
