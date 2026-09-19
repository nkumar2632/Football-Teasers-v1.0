"""Human-readable weekly report — **presentation only**.

Phase 4.2. This module formats what the grading layer already decided. It computes no
probability, ranks nothing, selects nothing and never re-derives a model value. Every
number it prints is read straight off the :class:`WeeklyCard` the engine produced.

Two design goals, in this order:

1. **Stale versus current data must be obvious at a glance.** The operational badge, the
   re-check status and the placement status sit at the top; snapshot ids and provenance sit
   at the bottom where they belong for an audit rather than a glance.
2. **It has to read on a phone.** Few columns, short headers, one decimal place. Full
   precision is preserved in the stored record and reprinted in the audit section, never
   discarded.

Status colour is never the only signal: every indicator carries its text label, so the
report is legible in a monochrome terminal, in a screen reader, and to a colour-blind
reader.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from teaser_model_v1.engine.presentation import PROBABILITY_LABEL
from teaser_model_v1.live.card import NO_TICKET_MESSAGE, WeeklyCard
from teaser_model_v1.live.provenance import iso, utc_now
from teaser_model_v1.live.recheck import DISCARD_REBUILD, NOT_YET_RECHECKED, RecheckResult

NOT_PLACED = "NOT PLACED — nothing has been wagered"

UNAVAILABLE = "UNAVAILABLE"

# --------------------------------------------------------------------------------------
# Status indicators. Colour is decoration; the text label is the signal.
# --------------------------------------------------------------------------------------

GREEN, AMBER, RED, GRAY, BLUE = "🟢", "🟡", "🔴", "⚪", "🔵"

BADGE_PLACED = f"{GREEN} **PLACED**"
BADGE_SHADOW = f"{BLUE} **SHADOW — NOT PLACED**"
BADGE_VALIDATED = f"{GREEN} **VALIDATED**"
BADGE_PENDING = f"{AMBER} **PENDING RECHECK**"
BADGE_DISCARD = f"{RED} **DISCARD — REBUILD**"
BADGE_PAPER = f"{GRAY} **PAPER — NOT LIVE**"

VERDICT_PENDING = "PENDING"


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


def _signed(value) -> str:
    """Render a betting number with an explicit sign. **Display only.**

    A spread or an American price is ambiguous without its sign: ``2.5`` could be read as
    either side of the game, and ``170`` could be read as ``-170``. The stored record keeps
    the value exactly as the grading layer wrote it; this only changes how it is printed.
    Zero is left unsigned, and UNAVAILABLE passes straight through.
    """
    text = str(value).strip()
    if not text or text == UNAVAILABLE:
        return text or UNAVAILABLE
    if text[0] in "+-":
        return text
    try:
        number = float(text)
    except ValueError:
        return text
    return f"+{text}" if number > 0 else text


def _pct(value, places: int = 1) -> str:
    """Format a 0-1 probability as a percentage. Never used to compute anything."""
    return f"{float(value) * 100:.{places}f}%"


def _pct_str(stored: str, places: int = 1) -> str:
    """Re-format a stored percentage string to fewer places, passing UNAVAILABLE through."""
    if not stored or stored == UNAVAILABLE:
        return UNAVAILABLE
    try:
        return f"{float(str(stored).rstrip('%')):.{places}f}%"
    except ValueError:
        return str(stored)


def _break_even(stored: str) -> str:
    if not stored or stored == UNAVAILABLE:
        return UNAVAILABLE
    try:
        return _pct(float(stored))
    except ValueError:
        return str(stored)


def _is_positive_ev(ticket) -> bool:
    """Read the status the grading layer already assigned. Does not recompute EV."""
    return "POSITIVE" in str(ticket.status).upper()


def _bold(text, emphasise: bool) -> str:
    return f"**{text}**" if emphasise else str(text)


def _team_of(leg_id: str) -> str:
    return leg_id.split("-")[-1]


def _badges(card: WeeklyCard, recheck: RecheckResult | None, placements: list) -> list[str]:
    """The operational badge row.

    Two independent dimensions, deliberately not collapsed into one value:
    *placement state* (has anything actually been wagered) and *re-check state* (is this
    card still current). A card can be validated and unplaced, or stale and unplaced, and
    the operator needs to see which.
    """
    badges = [BADGE_PLACED if placements else BADGE_SHADOW]
    if recheck is None:
        badges.append(BADGE_PENDING)
    elif recheck.any_discarded:
        badges.append(BADGE_DISCARD)
    elif str(recheck.overall).upper().startswith("VALID"):
        badges.append(BADGE_VALIDATED)
    else:
        badges.append(f"{AMBER} **{recheck.overall}**")
    return badges


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

    # ---- 1. Header -------------------------------------------------------------------
    add(f"# NFL Teaser v1.0 — {card.season} Week {card.week}")
    add("")
    add(" · ".join(_badges(card, recheck, placements)))
    add("")
    recheck_cell = (
        NOT_YET_RECHECKED if recheck is None
        else f"{recheck.overall} · `{iso(recheck.rechecked_at)}`"
    )
    add(_table(
        ["", ""],
        [
            ["**Sportsbook**", card.sportsbook],
            ["**Graded**", f"`{iso(card.graded_at)}`"],
            ["**Re-check**", recheck_cell],
            ["**Games scanned**", card.games_scanned],
            ["**Qualifying legs**", card.n_qualifying],
        ],
    ))
    add("")
    add("> Frozen Teaser Model v1.0. Nothing in this system places a wager.")
    add("")
    if not card.price_snapshot_id:
        add(
            "> **No actual teaser price was supplied.** Ticket probabilities are shown, "
            "but break-even and EV are UNAVAILABLE and **no ticket is placement-eligible**."
        )
        add("")

    # ---- 2. Qualifying legs ----------------------------------------------------------
    add("## Qualifying legs")
    add("")
    if card.qualifying_legs:
        add(_table(
            ["Rank", "Team", "Original → Teased", "Total", "P_est"],
            [
                [
                    leg.rank,
                    leg.team,
                    f"{_signed(leg.spread)} → {_signed(leg.teased_spread)}",
                    leg.total,
                    _pct(leg.p_est),
                ]
                for leg in card.qualifying_legs
            ],
        ))
        add("")
        top_ids = {leg.leg_id for leg in card.top_legs}
        retained = [leg.team for leg in card.qualifying_legs if leg.leg_id in top_ids]
        add(f"Top four retained: **{', '.join(retained)}**" if retained else "No legs retained.")
        add("")
        add(f"P_est is a *{PROBABILITY_LABEL}*, shown to one decimal place. "
            "Full precision is preserved in the stored record and listed under Audit.")
    else:
        add("No qualifying primary legs this week. **Recorded as zero.**")
    add("")

    # ---- 3. Proposed card ------------------------------------------------------------
    add("## Proposed card")
    add("")
    if card.selected_tickets:
        add(
            "**Every ticket below is POSITIVE EV at the offered price.** The frozen "
            "selection admits nothing else — a negative-EV ticket can never reach this "
            "table."
        )
        add("")
        add(_table(
            ["Ticket", "Price", "P_ticket", "Break-even", "EV%", "Status", "Stake"],
            [
                [
                    _bold("+".join(t.teams), True),
                    _signed(t.offered_american),
                    _pct(t.p_ticket),
                    _break_even(t.break_even),
                    _bold(_pct_str(t.ev_percent), _is_positive_ev(t)),
                    f"{GREEN} {_bold(t.status, _is_positive_ev(t))}",
                    "1u",
                ]
                for t in card.selected_tickets
            ],
        ))
        add("")
        # Displayed in board-rank order so it reads in the same sequence as the legs
        # table above. Ordering only — the units come straight from card.exposure.
        rank_of = {leg.leg_id: leg.rank for leg in card.qualifying_legs}
        by_rank = sorted(card.exposure.items(), key=lambda kv: (rank_of.get(kv[0], 99), kv[0]))
        add("Leg exposure: " + " · ".join(
            f"**{_team_of(leg)} {units}u**" for leg, units in by_rank
        ))
        add("")
        add(f"Card `{card.card_id}` — **PROPOSED ONLY. This is not a wager.**")
    elif card.tickets:
        add("No positive-EV ticket is model-designated this week.")
    else:
        add(f"**{NO_TICKET_MESSAGE}**")
        add("")
        add(
            f"Qualifying legs this week: {card.n_qualifying}. At least two are required. "
            "This week is still recorded in the season ledger."
        )
    add("")

    # ---- 4. Full ticket board --------------------------------------------------------
    if card.tickets:
        add("## Full ticket board")
        add("")
        add(_table(
            ["Ticket", "Price", "P_ticket", "Break-even", "EV%", "Status"],
            [
                [
                    _bold("+".join(t.teams), t.selected),
                    _signed(t.offered_american),
                    _pct(t.p_ticket),
                    _break_even(t.break_even),
                    _bold(_pct_str(t.ev_percent), _is_positive_ev(t)),
                    f"{GREEN if _is_positive_ev(t) else GRAY} {t.status}",
                ]
                for t in card.tickets
            ],
        ))
        add("")
        add(
            "Every constructible ticket is shown, including negative-EV ones. "
            "**\"Best available\" does not mean positive EV.** Bold ticket = on the "
            "proposed card."
        )
        add("")

    # ---- 5. Re-check -----------------------------------------------------------------
    add("## Re-check")
    add("")
    if recheck is None:
        add(f"{AMBER} **{NOT_YET_RECHECKED}**")
        add("")
        if card.selected_tickets:
            add(_table(
                ["Proposed ticket", "Verdict"],
                [
                    ["+".join(t.teams), f"{AMBER} {VERDICT_PENDING}"]
                    for t in card.selected_tickets
                ],
            ))
            add("")
        add(
            "> The card above was graded against "
            f"`{card.market_snapshot_id}` at `{iso(card.graded_at)}`. "
            "**Treat it as stale until re-checked against a current snapshot.**"
        )
    else:
        headline = BADGE_DISCARD if recheck.any_discarded else (
            BADGE_VALIDATED if str(recheck.overall).upper().startswith("VALID")
            else f"{AMBER} **{recheck.overall}**"
        )
        add(f"{headline} — re-checked `{iso(recheck.rechecked_at)}`")
        add("")
        add(_table(
            ["Ticket", "Verdict", "Reason"],
            [
                [
                    "+".join(_team_of(x) for x in ticket.ticket_key.split("|")),
                    f"{RED if ticket.verdict == DISCARD_REBUILD else GREEN} {ticket.verdict}",
                    "; ".join(ticket.reasons) if ticket.reasons else "-",
                ]
                for ticket in recheck.tickets
            ],
        ))
        if recheck.any_discarded:
            add("")
            add(
                "> Discarded tickets are **not** substituted and **not** downgraded. "
                "The card was rebuilt from the current board: "
                f"`{recheck.rebuilt_card.card_id if recheck.rebuilt_card else 'n/a'}`."
            )
    add("")

    # ---- Placement -------------------------------------------------------------------
    add("## Placement")
    add("")
    if placements:
        add(f"{GREEN} **ACTUALLY PLACED** — as recorded manually by the operator.")
        add("")
        add(_table(
            ["Ticket", "Book", "Odds", "Stake", "Placed at", "Designation"],
            [
                [
                    "+".join(_team_of(x) for x in row["ticket_key"].split("|")),
                    row["sportsbook"], _signed(row["american_odds"]), row["stake_units"],
                    row["placed_at"], row["designation"],
                ]
                for row in placements
            ],
        ))
    else:
        add(f"{BLUE} **{NOT_PLACED}**")
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

    # ---- 6. Audit details (bottom, not top) ------------------------------------------
    add("---")
    add("")
    add("## Audit")
    add("")
    add(_table(
        ["field", "value"],
        [
            ["card id", f"`{card.card_id}`"],
            ["market snapshot", f"`{card.market_snapshot_id}`"],
            ["teaser price snapshot",
             f"`{card.price_snapshot_id}`" if card.price_snapshot_id
             else "NONE — EV UNAVAILABLE"],
            ["sportsbook / source", card.sportsbook],
            ["graded at", f"`{iso(card.graded_at)}`"],
            ["report generated", f"`{iso(generated_at)}`"],
            ["card status", card.status],
            ["games scanned", card.games_scanned],
        ],
    ))
    add("")
    if card.notes:
        add(f"Source notes: {card.notes}")
        add("")
    if card.qualifying_legs:
        add("### Full-precision legs")
        add("")
        add(_table(
            ["Leg id", "Opp", "Total", "P_raw", "Bump", "P_est"],
            [
                [
                    f"`{leg.leg_id}`", leg.opponent, leg.total,
                    repr(leg.p_raw), leg.bump, repr(leg.p_est),
                ]
                for leg in card.qualifying_legs
            ],
        ))
        add("")
    if card.tickets:
        add("### Full-precision tickets")
        add("")
        add(_table(
            ["Ticket", "P_ticket", "Break-even", "EV%"],
            [
                ["+".join(t.teams), repr(t.p_ticket), t.break_even, t.ev_percent]
                for t in card.tickets
            ],
        ))
        add("")
    if card.exposure:
        add("### Exposure by leg id")
        add("")
        add(_table(
            ["Leg id", "Units"],
            [[f"`{leg}`", units] for leg, units in sorted(card.exposure.items())],
        ))
        add("")
    add(
        "Presentation only: this report formats the stored card and derives no model "
        "value. Probabilities, EV, selection and exposure are read from "
        f"`{card.card_id}` exactly as the grading layer wrote them."
    )

    return "\n".join(lines) + "\n"


def write_weekly_report(card: WeeklyCard, path: Path | str, **kwargs) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_weekly_report(card, **kwargs))
    return path
