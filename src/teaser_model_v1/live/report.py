"""Human-readable weekly report.

Design goal: make **stale versus current data obvious at a glance**. Every section names
the snapshot it came from and when that snapshot was taken, and the re-check and placement
status are stated explicitly rather than implied.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from teaser_model_v1.engine.presentation import PROBABILITY_LABEL
from teaser_model_v1.live.card import NO_TICKET_MESSAGE, WeeklyCard
from teaser_model_v1.live.provenance import iso, utc_now
from teaser_model_v1.live.recheck import DISCARD_REBUILD, NOT_YET_RECHECKED, RecheckResult

NOT_PLACED = "NOT PLACED — nothing has been wagered"


def _table(header, rows) -> str:
    widths = [len(str(column)) for column in header]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(str(cell)))
    line = "| " + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(header)) + " |"
    rule = "|" + "|".join("-" * (width + 2) for width in widths) + "|"
    body = [
        "| " + " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)) + " |"
        for row in rows
    ]
    return "\n".join([line, rule, *body])


def render_weekly_report(
    card: WeeklyCard,
    *,
    recheck: RecheckResult | None = None,
    placements: list | None = None,
    settlements: list | None = None,
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or utc_now()
    placements = placements or []
    settlements = settlements or []
    lines: list[str] = []
    add = lines.append

    add(f"# NFL {card.season} Week {card.week} — Teaser Model v1.0 live card")
    add("")
    add(f"Report generated: `{iso(generated_at)}`")
    add("")
    add("> Frozen Teaser Model v1.0. Nothing in this system places a wager.")
    add("")

    add("## Market snapshot")
    add("")
    add(_table(
        ["field", "value"],
        [
            ["sportsbook / source", card.sportsbook],
            ["market snapshot", card.market_snapshot_id],
            ["teaser price snapshot", card.price_snapshot_id or "NONE — EV UNAVAILABLE"],
            ["graded at", iso(card.graded_at)],
            ["games scanned", card.games_scanned],
            ["qualifying primary legs", card.n_qualifying],
        ],
    ))
    add("")
    if not card.price_snapshot_id:
        add(
            "> **No actual teaser price was supplied.** Ticket probabilities are shown, "
            "but break-even and EV are UNAVAILABLE and **no ticket is placement-eligible**."
        )
        add("")

    add("## Primary legs")
    add("")
    if card.qualifying_legs:
        add(_table(
            ["Rank", "Team", "Opp", "Original", "Teased", "Total", "P_est"],
            [
                [
                    leg.rank, leg.team, leg.opponent, str(leg.spread),
                    str(leg.teased_spread), str(leg.total), leg.displayed_probability,
                ]
                for leg in card.qualifying_legs
            ],
        ))
        add("")
        add(f"P_est shown as a whole percent: *{PROBABILITY_LABEL}*.")
        add("")
        top_ids = {leg.leg_id for leg in card.top_legs}
        add(
            f"Top four retained for construction: "
            f"{', '.join(leg.team for leg in card.qualifying_legs if leg.leg_id in top_ids)}"
            if top_ids else "No legs retained."
        )
    else:
        add("No qualifying primary legs this week. **Recorded as zero.**")
    add("")

    add("## Ticket board")
    add("")
    if card.tickets:
        add(_table(
            ["Ticket", "Legs", "P_ticket", "Offered", "Break-even", "EV%", "Status", "On card"],
            [
                [
                    "+".join(ticket.teams), ticket.n_legs,
                    f"{ticket.p_ticket * 100:.1f}%",
                    ticket.offered_american,
                    (ticket.break_even if ticket.break_even == "UNAVAILABLE"
                     else f"{float(ticket.break_even) * 100:.1f}%"),
                    ticket.ev_percent, ticket.status,
                    "YES" if ticket.selected else "no",
                ]
                for ticket in card.tickets
            ],
        ))
        add("")
        add(
            "Every constructible ticket is shown, including negative-EV ones. "
            "**\"Best available\" does not mean positive EV.**"
        )
    else:
        add(f"**{NO_TICKET_MESSAGE}**")
        add("")
        add(
            f"Qualifying legs this week: {card.n_qualifying}. At least two are required. "
            "This week is still recorded in the season ledger."
        )
    add("")

    add("## Proposed live card")
    add("")
    if card.selected_tickets:
        add(_table(
            ["Ticket", "Legs", "Stake", "EV%", "Offered"],
            [
                ["+".join(t.teams), t.n_legs, "1 unit", t.ev_percent, t.offered_american]
                for t in card.selected_tickets
            ],
        ))
        add("")
        add("Aggregate leg exposure:")
        add("")
        add(_table(
            ["Leg", "Units"],
            [[leg, units] for leg, units in sorted(card.exposure.items())],
        ))
        add("")
        add(f"Card id: `{card.card_id}` — **PROPOSED ONLY. This is not a wager.**")
    else:
        add("No positive-EV ticket is model-designated this week.")
    add("")

    add("## Re-check status")
    add("")
    if recheck is None:
        add(f"**{NOT_YET_RECHECKED}**")
        add("")
        add(
            "> The card above was graded against "
            f"`{card.market_snapshot_id}` at `{iso(card.graded_at)}`. "
            "**Treat it as stale until re-checked against a current snapshot.**"
        )
    else:
        add(f"**{recheck.overall}** — re-checked at `{iso(recheck.rechecked_at)}`")
        add("")
        add(_table(
            ["Ticket", "Verdict", "Reason"],
            [
                [ticket.ticket_key, ticket.verdict,
                 "; ".join(ticket.reasons) if ticket.reasons else "-"]
                for ticket in recheck.tickets
            ],
        ))
        add("")
        add(f"New market snapshot: `{recheck.new_market_snapshot_id}`")
        add(f"New price snapshot: `{recheck.new_price_snapshot_id or 'NONE'}`")
        if recheck.any_discarded:
            add("")
            add(
                "> Discarded tickets are **not** substituted and **not** downgraded. "
                "The card was rebuilt from the current board: "
                f"`{recheck.rebuilt_card.card_id if recheck.rebuilt_card else 'n/a'}`."
            )
    add("")

    add("## Placement status")
    add("")
    if placements:
        add(_table(
            ["Placement", "Ticket", "Book", "Odds", "Stake", "Placed at", "Designation"],
            [
                [
                    row["placement_id"], row["ticket_key"], row["sportsbook"],
                    row["american_odds"], row["stake_units"], row["placed_at"],
                    row["designation"],
                ]
                for row in placements
            ],
        ))
        add("")
        add("**ACTUALLY PLACED** — as recorded manually by the operator.")
    else:
        add(f"**{NOT_PLACED}**")
        add("")
        add(
            "A proposed card is never a placement. Nothing counts as wagered until it is "
            "explicitly recorded."
        )
    add("")

    if settlements:
        add("## Settlement")
        add("")
        add(_table(
            ["Placement", "Model result", "Book settlement", "P/L (units)", "Agree"],
            [
                [
                    row["placement_id"], row["model_ticket_result"],
                    row["book_settlement"], row["profit_loss_units"],
                    "yes" if row["results_agree"] else "NO",
                ]
                for row in settlements
            ],
        ))
        add("")
        add(
            "Model grade and sportsbook settlement are recorded separately and are never "
            "reconciled by a generic rule."
        )
        add("")

    return "\n".join(lines) + "\n"


def write_weekly_report(card: WeeklyCard, path: Path | str, **kwargs) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_weekly_report(card, **kwargs))
    return path
