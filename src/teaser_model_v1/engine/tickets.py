"""Ticket construction, EV ranking and the greedy exposure-capped selection.

Frozen. See ``TEASER_MODEL_V1_0.md`` §§6, 8, 9.

The selection rule is a deliberate greedy walk down precise EV. **Do not replace it with a
portfolio optimizer.**
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import combinations
from typing import Callable, Iterable, Mapping, Sequence

from teaser_model_v1.engine.constants import (
    MAX_UNITS_PER_LEG_PER_WEEK,
    MIN_LEGS_FOR_ANY_TICKET,
    TICKET_SIZES,
    TOP_N_LEGS,
    UNITS_PER_TICKET,
)
from teaser_model_v1.engine.legs import Leg
from teaser_model_v1.engine.pricing import (
    break_even_probability,
    ev_per_unit,
    fair_break_even_profit,
)

ProfitSource = Mapping[int, float] | Callable[[int], float | None] | None


def ticket_probability(p_est_values: Iterable[float]) -> float:
    """P_ticket = product of constituent leg P_est values."""
    values = list(p_est_values)
    if not values:
        raise ValueError("a ticket must have at least one leg")
    return math.prod(float(v) for v in values)


@dataclass(frozen=True)
class Ticket:
    """A 2- or 3-team 6-point teaser built from primary legs.

    ``profit`` is net profit per 1 unit staked at the offered price. It is ``None`` when no
    price is available — in which case ``ev`` is ``None`` too, and the ticket is reported
    with a *fair break-even price* instead. A ticket with no price is never
    placement-eligible, because eligibility requires positive EV at an actual offered price.

    ``price_is_hypothetical`` must be True whenever ``profit`` came from a sensitivity
    scenario rather than a real observed menu price.
    """

    legs: tuple[Leg, ...]
    p_ticket: float
    profit: float | None = None
    break_even: float | None = None
    ev: float | None = None
    price_is_hypothetical: bool = False
    price_provenance: str | None = None
    extra: dict = field(default_factory=dict, compare=False, repr=False)

    @property
    def n_legs(self) -> int:
        return len(self.legs)

    @property
    def leg_ids(self) -> tuple[str, ...]:
        return tuple(leg.leg_id for leg in self.legs)

    @property
    def fair_break_even_profit(self) -> float:
        """Net profit per unit this ticket needs to break even. Always available."""
        return fair_break_even_profit(self.p_ticket)

    @property
    def is_positive_ev(self) -> bool:
        """Strictly positive EV at a known price. ``EV == 0`` is not positive."""
        return self.ev is not None and self.ev > 0.0

    @property
    def placement_eligible(self) -> bool:
        """Model-designated live-bet eligibility.

        Requires positive EV at an **actual** offered price. A hypothetical price can make
        a ticket display as positive EV in a sensitivity study, but it can never make it
        placement-eligible.

        This flag is a model designation. It is not an instruction to place a bet.
        """
        return self.is_positive_ev and not self.price_is_hypothetical

    def sort_key(self) -> tuple:
        """Ranking key per the tie rule: precise EV, then fewer legs, then stable ids.

        1. internally precise EV (descending) — never a rounded/displayed EV;
        2. if truly tied, fewer legs first;
        3. leg ids, purely to keep output reproducible (see AMBIGUITIES.md A-4).

        Tickets with no price sort last; they cannot be ranked by EV and are not
        placement-eligible.
        """
        has_ev = self.ev is not None
        return (
            0 if has_ev else 1,
            -self.ev if has_ev else 0.0,
            self.n_legs,
            self.leg_ids,
        )


def select_top_legs(legs: Sequence[Leg], top_n: int = TOP_N_LEGS) -> list[Leg]:
    """Rank eligible legs by P_est and retain the top *top_n*.

    Input should already be filtered to qualifying legs
    (:func:`~teaser_model_v1.engine.legs.eligible_live_primary_legs`); this function does
    the ranking and truncation only.
    """
    return sorted(legs, key=lambda leg: leg.sort_key())[:top_n]


def _resolve_profit(source: ProfitSource, n_legs: int) -> float | None:
    if source is None:
        return None
    if callable(source):
        return source(n_legs)
    return source.get(n_legs)


def generate_tickets(
    legs: Sequence[Leg],
    profit_by_size: ProfitSource = None,
    *,
    ticket_sizes: Sequence[int] = TICKET_SIZES,
    price_is_hypothetical: bool = False,
    price_provenance: str | None = None,
) -> list[Ticket]:
    """Build every 2-team and 3-team combination from *legs*.

    If fewer than two legs are supplied, **no ticket can be constructed** and an empty
    list is returned.

    Negative-EV tickets are returned like any other: they are displayed and logged, they
    are simply not placement-eligible.

    ``profit_by_size`` maps ticket size to net profit per unit, or is a callable taking the
    number of legs. Pass ``None`` when no real price exists — do not invent one. Any price
    that is not an actually observed menu price must be passed with
    ``price_is_hypothetical=True``.
    """
    legs = list(legs)
    if len(legs) < MIN_LEGS_FOR_ANY_TICKET:
        return []

    tickets: list[Ticket] = []
    for size in ticket_sizes:
        if size > len(legs):
            continue
        for combo in combinations(legs, size):
            p = ticket_probability(leg.p_est for leg in combo)
            profit = _resolve_profit(profit_by_size, size)
            if profit is None:
                break_even = None
                ev = None
            else:
                break_even = break_even_probability(profit)
                ev = ev_per_unit(p, profit)
            tickets.append(
                Ticket(
                    legs=tuple(combo),
                    p_ticket=p,
                    profit=profit,
                    break_even=break_even,
                    ev=ev,
                    price_is_hypothetical=price_is_hypothetical if profit is not None else False,
                    price_provenance=price_provenance if profit is not None else None,
                )
            )

    return sorted(tickets, key=lambda t: t.sort_key())


def rank_tickets(tickets: Iterable[Ticket]) -> list[Ticket]:
    """Sort tickets by the frozen tie rule. Ranking is by precise EV, never by P_est."""
    return sorted(tickets, key=lambda t: t.sort_key())


@dataclass(frozen=True)
class SelectionResult:
    """Outcome of the greedy exposure-capped walk."""

    selected: tuple[Ticket, ...]
    skipped: tuple[Ticket, ...]
    exposure: dict  # leg_id -> units

    @property
    def n_selected(self) -> int:
        return len(self.selected)


def _is_placement_eligible(ticket: "Ticket") -> bool:
    """The frozen live-eligibility predicate: positive EV at an actual offered price."""
    return ticket.placement_eligible


def select_live_tickets(
    tickets: Iterable[Ticket],
    *,
    max_units_per_leg: int = MAX_UNITS_PER_LEG_PER_WEEK,
    units_per_ticket: int = UNITS_PER_TICKET,
    eligibility: Callable[["Ticket"], bool] = _is_placement_eligible,
) -> SelectionResult:
    """Greedy exposure-capped selection of live tickets.

    Walk placement-eligible (positive-EV, real-price) tickets in descending internally
    precise EV order. Add a ticket only if doing so keeps **every** constituent leg at
    ``<= max_units_per_leg`` aggregate exposure; otherwise skip it and continue down the
    list.

    This greedy rule is intentional. It is not an approximation of an optimizer and must
    not be replaced by one.

    ``eligibility`` exists so that **research** can drive this exact algorithm over
    explicitly hypothetical prices — a historical sensitivity study cannot use the live
    predicate, because a hypothetical price can never confer placement eligibility
    (AMBIGUITIES.md A-8). The default is the frozen live predicate and is unchanged; a test
    pins that. Passing anything else marks the run as research-only, and its output must
    never be described as a live selection or as a realized return.
    """
    ordered = rank_tickets(t for t in tickets if eligibility(t))

    exposure: dict[str, int] = {}
    selected: list[Ticket] = []
    skipped: list[Ticket] = []

    for ticket in ordered:
        if all(
            exposure.get(leg.leg_id, 0) + units_per_ticket <= max_units_per_leg
            for leg in ticket.legs
        ):
            for leg in ticket.legs:
                exposure[leg.leg_id] = exposure.get(leg.leg_id, 0) + units_per_ticket
            selected.append(ticket)
        else:
            skipped.append(ticket)

    return SelectionResult(
        selected=tuple(selected), skipped=tuple(skipped), exposure=exposure
    )
