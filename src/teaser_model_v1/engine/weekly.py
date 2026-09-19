"""Weekly construction, end to end, plus the counts §11 requires us to record.

Frozen. See ``TEASER_MODEL_V1_0.md`` §§8, 9, 11.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from teaser_model_v1.engine.legs import Leg, eligible_live_primary_legs
from teaser_model_v1.engine.tickets import (
    ProfitSource,
    SelectionResult,
    Ticket,
    generate_tickets,
    select_live_tickets,
    select_top_legs,
)


@dataclass(frozen=True)
class WeeklyResult:
    """Everything the model produces for one week, plus the mandatory weekly counts."""

    season: int | None
    week: int | None
    qualifying_legs: tuple[Leg, ...]
    top_legs: tuple[Leg, ...]
    tickets: tuple[Ticket, ...]
    selection: SelectionResult | None
    notes: tuple[str, ...] = field(default_factory=tuple)

    # ---- Mandatory weekly measurement counts (§11) ----

    @property
    def n_qualifying_primary_legs(self) -> int:
        """Number of qualifying live-primary NFL legs — reported even when zero."""
        return len(self.qualifying_legs)

    @property
    def n_tickets_constructed(self) -> int:
        return len(self.tickets)

    @property
    def n_positive_ev_tickets(self) -> int:
        return sum(1 for t in self.tickets if t.is_positive_ev)

    @property
    def n_placed(self) -> int:
        """Number of tickets the model designated for placement this week."""
        return 0 if self.selection is None else self.selection.n_selected

    def counts(self) -> dict:
        return {
            "season": self.season,
            "week": self.week,
            "n_qualifying_primary_legs": self.n_qualifying_primary_legs,
            "n_tickets_constructed": self.n_tickets_constructed,
            "n_positive_ev_tickets": self.n_positive_ev_tickets,
            "n_placed": self.n_placed,
        }


def construct_week(
    legs: Sequence[Leg],
    profit_by_size: ProfitSource = None,
    *,
    season: int | None = None,
    week: int | None = None,
    price_is_hypothetical: bool = False,
    price_provenance: str | None = None,
) -> WeeklyResult:
    """Run the frozen weekly construction over one week's board.

    1. Identify eligible primary NFL legs — primary geometry on the LIVE track.
       CFB primary geometry is primary geometry, but it is on the paper track and is
       deliberately excluded here.
    2. Rank them by P_est.
    3. Retain the top four.
    4. If fewer than two qualify, no primary ticket can be constructed.
    5. Build all 2-team and 3-team combinations from those top four.
    6. Negative-EV tickets are kept for display/logging.
    7. Greedy exposure-capped selection over positive-EV tickets at a real price.
    """
    qualifying = eligible_live_primary_legs(legs)
    top = select_top_legs(qualifying)

    notes: list[str] = []
    if len(top) < 2:
        notes.append(
            "Fewer than two eligible primary legs: no primary ticket can be constructed."
        )
        return WeeklyResult(
            season=season,
            week=week,
            qualifying_legs=tuple(qualifying),
            top_legs=tuple(top),
            tickets=(),
            selection=None,
            notes=tuple(notes),
        )

    tickets = generate_tickets(
        top,
        profit_by_size,
        price_is_hypothetical=price_is_hypothetical,
        price_provenance=price_provenance,
    )

    if profit_by_size is None:
        notes.append(
            "No teaser price supplied: EV is undefined. Fair break-even prices are "
            "reported instead. No ticket is placement-eligible."
        )
    if price_is_hypothetical:
        notes.append(
            "Prices used here are HYPOTHETICAL. No ticket is placement-eligible."
        )

    selection = select_live_tickets(tickets)

    return WeeklyResult(
        season=season,
        week=week,
        qualifying_legs=tuple(qualifying),
        top_legs=tuple(top),
        tickets=tuple(tickets),
        selection=selection,
        notes=tuple(notes),
    )
