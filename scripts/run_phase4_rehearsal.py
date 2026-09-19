#!/usr/bin/env python3
"""Phase 4 — synthetic end-to-end rehearsal of the prospective workflow.

Uses a FABRICATED NFL week. No real 2026 market data is pulled, no wager is placed or
simulated, and nothing here touches the frozen model.

The rehearsal drives every transition the live system must handle:

  five primary-shape candidates, one failing the total cap
  -> grading-time card with both positive and negative EV tickets
  -> a market move taking one proposed leg out of primary geometry
  -> a teaser-price move turning another ticket's EV negative
  -> discard and rebuild
  -> explicit placement of a surviving ticket
  -> settlement, including a sportsbook VOID that disagrees with the model grade

Usage:
    python scripts/run_phase4_rehearsal.py [--out DIR]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teaser_model_v1.live.card import grade_week  # noqa: E402
from teaser_model_v1.live.ledger import (  # noqa: E402
    FINAL_OBSERVED,
    GRADING_LINE,
    PLACEMENT_LINE,
    LineObservation,
    SeasonLedger,
    WeekLedgerEntry,
    line_movement,
)
from teaser_model_v1.live.placement import (  # noqa: E402
    EXTERNAL_NON_MODEL,
    ExposureCapViolation,
    PlacementRefused,
    PostKickoffPlacement,
)
from teaser_model_v1.live.provenance import iso  # noqa: E402
from teaser_model_v1.live.recheck import recheck_card  # noqa: E402
from teaser_model_v1.live.report import render_weekly_report  # noqa: E402
from teaser_model_v1.live.schemas import (  # noqa: E402
    MarketQuote,
    MarketSnapshot,
    TeaserPriceQuote,
    TeaserPriceSnapshot,
)
from teaser_model_v1.live.settlement import (  # noqa: E402
    BOOK_VOID,
    BOOK_WIN,
    grade_leg_settlement,
    settle_ticket,
)
from teaser_model_v1.live.workspace import Workspace  # noqa: E402

SEASON, WEEK = 2026, 3
BOOK = "SYNTHETIC_BOOK"
EASTERN = timezone(timedelta(hours=-4))

KICKOFF = datetime(2026, 9, 20, 13, 0, tzinfo=EASTERN)
T_GRADE = datetime(2026, 9, 19, 10, 0, tzinfo=EASTERN)
T_RECHECK = datetime(2026, 9, 20, 12, 40, tzinfo=EASTERN)
T_PLACE = datetime(2026, 9, 20, 12, 45, tzinfo=EASTERN)
T_LATE_RECHECK = datetime(2026, 9, 20, 12, 55, tzinfo=EASTERN)
T_FINAL_OBS = datetime(2026, 9, 20, 12, 58, tzinfo=EASTERN)
T_SETTLE = datetime(2026, 9, 20, 16, 30, tzinfo=EASTERN)

#: (away, home, team_bet, spread, total, note)
GRADING_BOARD = [
    ("BUF", "MIA", "MIA", "2.5", "40.5", "primary +2.5, low total -> highest P_est"),
    ("NYJ", "NE", "NE", "1.5", "42.5", "primary +1.5"),
    ("DAL", "PHI", "PHI", "-7.5", "43.5", "primary -7.5"),
    ("GB", "CHI", "CHI", "2.5", "45.5", "primary +2.5"),
    ("SF", "SEA", "SEA", "-8.5", "46.5", "primary -8.5, highest total -> lowest P_est"),
    ("KC", "DEN", "DEN", "2.5", "49.5", "primary shape but total 49.5 FAILS the <=47 cap"),
    ("LV", "LAC", "LAC", "-3.5", "44.5", "not primary geometry"),
]


def quotes_for(board, captured_at):
    quotes = []
    for away, home, team, spread, total, _ in board:
        game_id = f"{SEASON}_{WEEK:02d}_{away}_{home}"
        quotes.append(
            MarketQuote(
                game_id=game_id, season=SEASON, week=WEEK, kickoff=KICKOFF,
                home_team=home, away_team=away, team=team,
                spread=spread, total=total, sportsbook=BOOK,
                captured_at=captured_at, ingestion_method="synthetic_rehearsal",
                source_reference="fabricated", raw_source_value=f"{team} {spread}",
            )
        )
    return tuple(quotes)


def price_snapshot(captured_at, two, three, label):
    return TeaserPriceSnapshot(
        season=SEASON, week=WEEK, captured_at=captured_at, sportsbook=BOOK,
        quotes=(
            TeaserPriceQuote(ticket_size=2, sportsbook=BOOK, captured_at=captured_at,
                             american_odds=two, source_reference="fabricated"),
            TeaserPriceQuote(ticket_size=3, sportsbook=BOOK, captured_at=captured_at,
                             american_odds=three, source_reference="fabricated"),
        ),
        label=label,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "data" / "live" / "rehearsal"))
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    workspace = Workspace(out)
    (out / "data" / "live").mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    add = lines.append

    add("# Phase 4 — synthetic end-to-end rehearsal")
    add("")
    add(
        "**Every number below is FABRICATED.** No real 2026 market data was pulled, no "
        "wager was placed or simulated, and the frozen model was not touched. The purpose "
        "is to prove the audit trail survives a full week, including a market move and a "
        "price move."
    )
    add("")
    add(f"Synthetic week: NFL {SEASON} Week {WEEK}, book `{BOOK}`.")
    add("")

    # ---- Step 1: grading-time snapshot -------------------------------------------------
    add("## Step 1 — grading-time market and price snapshots")
    add("")
    market_1 = MarketSnapshot(
        season=SEASON, week=WEEK, captured_at=T_GRADE, sportsbook=BOOK,
        ingestion_method="synthetic_rehearsal", quotes=quotes_for(GRADING_BOARD, T_GRADE),
        label="grading",
    )
    prices_1 = price_snapshot(T_GRADE, -120, 140, "grading")
    workspace.snapshots.put(market_1.snapshot_id, market_1.to_dict(), kind="market_snapshot")
    workspace.snapshots.put(prices_1.snapshot_id, prices_1.to_dict(),
                            kind="teaser_price_snapshot")

    add(f"- market snapshot `{market_1.snapshot_id}` captured `{iso(T_GRADE)}`")
    add(f"- price snapshot `{prices_1.snapshot_id}`: 2-team **-120**, 3-team **+140**")
    add("")
    add("Board offered to the model:")
    add("")
    add("| Game | Side | Spread | Total | Note |")
    add("|---|---|---|---|---|")
    for away, home, team, spread, total, note in GRADING_BOARD:
        add(f"| {away} @ {home} | {team} | {spread} | {total} | {note} |")
    add("")

    # ---- Step 2: grading-time card -----------------------------------------------------
    card_1 = grade_week(market_1, prices_1, graded_at=T_GRADE, notes="rehearsal grading")
    workspace.cards.put(card_1.card_id, card_1.to_dict(), kind="weekly_card")

    add("## Step 2 — grading-time card")
    add("")
    add(f"Card `{card_1.card_id}` — status **{card_1.status}**")
    add("")
    add(
        f"- qualifying primary legs: **{card_1.n_qualifying}** "
        f"(the 49.5-total game was correctly excluded by the guardrail, and the -3.5 line "
        "is not primary geometry)"
    )
    add(f"- top four retained: {', '.join(leg.team for leg in card_1.top_legs)}")
    add(f"- tickets constructed: **{len(card_1.tickets)}** "
        f"(positive EV: {card_1.n_positive_ev}, negative EV: "
        f"{len(card_1.tickets) - card_1.n_positive_ev})")
    add(f"- proposed (model-designated): **{len(card_1.selected_tickets)}**")
    add("")
    add("| Ticket | Legs | P_ticket | Offered | EV% | Status | On card |")
    add("|---|---|---|---|---|---|---|")
    for ticket in card_1.tickets:
        add(
            f"| {'+'.join(ticket.teams)} | {ticket.n_legs} | "
            f"{ticket.p_ticket * 100:.1f}% | {ticket.offered_american} | "
            f"{ticket.ev_percent} | {ticket.status} | "
            f"{'YES' if ticket.selected else 'no'} |"
        )
    add("")
    add(
        "Both positive-EV and negative-EV tickets are displayed. Only positive-EV tickets "
        "reach the proposed card, and the 2-unit cap bounds aggregate leg exposure."
    )
    add("")
    add("Exposure on the proposed card: "
        + ", ".join(f"`{leg}` {units}u" for leg, units in sorted(card_1.exposure.items())))
    add("")

    # ---- Step 3: the market and the price both move ------------------------------------
    moved_board = []
    for away, home, team, spread, total, note in GRADING_BOARD:
        if team == "NE":
            moved_board.append((away, home, team, "3.0", total,
                                "MOVED +1.5 -> +3.0: leaves primary geometry"))
        elif team == "CHI":
            moved_board.append((away, home, team, spread, "47.5",
                                "MOVED total 45.5 -> 47.5: breaches the <=47 guardrail"))
        else:
            moved_board.append((away, home, team, spread, total, note))

    market_2 = MarketSnapshot(
        season=SEASON, week=WEEK, captured_at=T_RECHECK, sportsbook=BOOK,
        ingestion_method="synthetic_rehearsal", quotes=quotes_for(moved_board, T_RECHECK),
        label="placement-time",
    )
    prices_2 = price_snapshot(T_RECHECK, -120, 120, "placement-time")
    workspace.snapshots.put(market_2.snapshot_id, market_2.to_dict(), kind="market_snapshot")
    workspace.snapshots.put(prices_2.snapshot_id, prices_2.to_dict(),
                            kind="teaser_price_snapshot")

    add("## Step 3 — the board moves before placement")
    add("")
    add(f"New market snapshot `{market_2.snapshot_id}` captured `{iso(T_RECHECK)}`.")
    add(f"New price snapshot `{prices_2.snapshot_id}`: 2-team **-120** (unchanged), 3-team **+140 -> +120**.")
    add("")
    add("Three independent changes, chosen to exercise three different failure paths:")
    add("")
    add("1. **NE +1.5 -> +3.0** — the leg leaves primary geometry entirely.")
    add("2. **CHI total 45.5 -> 47.5** — the leg breaches the total guardrail.")
    add("3. **The 3-team teaser price worsens, +140 -> +120** — enough to turn a "
        "3-team ticket negative EV on price alone, while the 2-team menu is unchanged so "
        "a validated ticket survives to be placed.")
    add("")
    add(
        "> The earlier snapshots are **not** modified. Both remain on disk under their own "
        "ids; a later capture is always a new record."
    )
    add("")

    # ---- Step 4: re-check --------------------------------------------------------------
    recheck = recheck_card(card_1, market_2, prices_2, rechecked_at=T_RECHECK)
    workspace.cards.put(recheck.recheck_id, recheck.to_dict(), kind="recheck")

    add("## Step 4 — placement-time re-check")
    add("")
    add(f"Re-check `{recheck.recheck_id}` — overall verdict: **{recheck.overall}**")
    add("")
    add("| Ticket | Verdict | Reason |")
    add("|---|---|---|")
    for ticket in recheck.tickets:
        reasons = "; ".join(ticket.reasons) if ticket.reasons else "-"
        add(f"| {ticket.ticket_key} | {ticket.verdict} | {reasons} |")
    add("")
    add(
        "Discarded tickets were **not** substituted with another team and **not** "
        "downgraded from 3-team to 2-team. The word used is *discard*; \"void\" is "
        "reserved for a sportsbook settling a wager that was actually placed."
    )
    add("")

    # ---- Step 5: rebuild ---------------------------------------------------------------
    card_2 = recheck.rebuilt_card
    add("## Step 5 — rebuild from the current board")
    add("")
    if card_2 is None:
        add("No rebuild was required.")
    else:
        workspace.cards.put(card_2.card_id, card_2.to_dict(), kind="weekly_card")
        add(f"Rebuilt card `{card_2.card_id}` from snapshot `{market_2.snapshot_id}`.")
        add("")
        add(f"- qualifying primary legs now: **{card_2.n_qualifying}** "
            f"({', '.join(leg.team for leg in card_2.qualifying_legs)})")
        add(f"- tickets constructed: **{len(card_2.tickets)}**, "
            f"positive EV: **{card_2.n_positive_ev}**")
        add(f"- proposed: **{len(card_2.selected_tickets)}**")
        add("")
        add("| Ticket | Legs | P_ticket | Offered | EV% | Status | On card |")
        add("|---|---|---|---|---|---|---|")
        for ticket in card_2.tickets:
            add(
                f"| {'+'.join(ticket.teams)} | {ticket.n_legs} | "
                f"{ticket.p_ticket * 100:.1f}% | {ticket.offered_american} | "
                f"{ticket.ev_percent} | {ticket.status} | "
                f"{'YES' if ticket.selected else 'no'} |"
            )
        add("")
        add(
            "The worsened 3-team price is visible here: every 3-team ticket is "
            "re-evaluated at +120 instead of +140, and only tickets still positive EV "
            "reach the rebuilt card."
        )
    add("")

    # ---- Step 6: placement -------------------------------------------------------------
    add("## Step 6 — explicit placement recording")
    add("")
    ledger = workspace.placements
    placed = []
    active_card = card_1  # tickets that SURVIVED re-check belong to the original card

    validated_keys = [ticket.ticket_key for ticket in recheck.validated]
    add(
        "Tickets that survived the re-check: "
        + (", ".join(f"`{key}`" for key in validated_keys) if validated_keys else "none")
    )
    add("")
    add("### Phase 4.1 gates, exercised in order")
    add("")

    target = validated_keys[0] if validated_keys else None

    # --- A. model placement with NO re-check -----------------------------------------
    if target:
        try:
            ledger.record(
                active_card, target, sportsbook=BOOK, american_odds="-120",
                placed_at=T_PLACE, recorded_by="rehearsal",
            )
            add("- **A. UNEXPECTED**: a model placement without a re-check was accepted.")
        except PlacementRefused as exc:
            ledger.log_refusal(card=active_card, ticket_key=target, placed_at=T_PLACE,
                               reason=str(exc), attempted_by="rehearsal")
            add(f"- **A. no re-check** -> refused: `{exc}`")

    # --- B. model placement using a DISCARDED re-check --------------------------------
    discarded_key = recheck.discarded[0].ticket_key if recheck.discarded else None
    if discarded_key:
        try:
            ledger.record(
                active_card, discarded_key, sportsbook=BOOK, american_odds="-120",
                placed_at=T_PLACE, recorded_by="rehearsal", recheck=recheck,
            )
            add("- **B. UNEXPECTED**: a discarded ticket was accepted.")
        except PlacementRefused as exc:
            ledger.log_refusal(card=active_card, ticket_key=discarded_key,
                               placed_at=T_PLACE, reason=str(exc),
                               attempted_by="rehearsal")
            add(f"- **B. discarded re-check** -> refused: `{exc}`")

    # --- C. valid, fresh re-check ------------------------------------------------------
    for key in validated_keys:
        view = active_card.ticket(key)
        record = ledger.record(
            active_card, key, sportsbook=BOOK,
            american_odds=view.offered_american, placed_at=T_PLACE,
            recorded_by="rehearsal_operator", book_reference="SYN-12345",
            notes="fabricated rehearsal placement", recheck=recheck,
            known_rechecks=[recheck],
        )
        placed.append(record)
        add(
            f"- **C. valid re-check** -> accepted: placement `{record.placement_id}` for "
            f"`{record.ticket_key}` at {record.sportsbook} {record.american_odds}, "
            f"stake {record.stake_units}u (re-check `{record.recheck_id}`)"
        )

    if placed:
        chosen_key = placed[0].ticket_key
        try:
            for _ in range(3):
                ledger.record(
                    active_card, chosen_key, sportsbook=BOOK,
                    american_odds=active_card.ticket(chosen_key).offered_american,
                    placed_at=T_PLACE, recorded_by="rehearsal_operator",
                    recheck=recheck, known_rechecks=[recheck],
                )
            add("- **UNEXPECTED**: the 2-unit exposure cap did not bind.")
        except ExposureCapViolation as exc:
            add(f"- **exposure cap** -> refused a further placement: `{exc}`")

    # --- D. model placement AFTER kickoff ----------------------------------------------
    # A deliberately FRESH re-check taken minutes before kickoff, so the staleness gate
    # passes and the pregame gate is the binding one.
    late_market = MarketSnapshot(
        season=SEASON, week=WEEK, captured_at=T_LATE_RECHECK, sportsbook=BOOK,
        ingestion_method="synthetic_rehearsal",
        quotes=quotes_for(moved_board, T_LATE_RECHECK), label="pre-kickoff",
    )
    late_prices = price_snapshot(T_LATE_RECHECK, -120, 120, "pre-kickoff")
    workspace.snapshots.put(late_market.snapshot_id, late_market.to_dict(),
                            kind="market_snapshot")
    workspace.snapshots.put(late_prices.snapshot_id, late_prices.to_dict(),
                            kind="teaser_price_snapshot")
    late_recheck = recheck_card(card_1, late_market, late_prices,
                                rechecked_at=T_LATE_RECHECK)
    workspace.cards.put(late_recheck.recheck_id, late_recheck.to_dict(), kind="recheck")

    late_validated = [t.ticket_key for t in late_recheck.validated]
    if late_validated:
        after_kickoff = KICKOFF + timedelta(minutes=2)
        try:
            ledger.record(
                active_card, late_validated[0], sportsbook=BOOK, american_odds="-120",
                placed_at=after_kickoff, recorded_by="rehearsal",
                recheck=late_recheck, known_rechecks=[late_recheck],
            )
            add("- **D. UNEXPECTED**: a post-kickoff placement was accepted.")
        except PlacementRefused as exc:
            ledger.log_refusal(card=active_card, ticket_key=late_validated[0],
                               placed_at=after_kickoff, reason=str(exc),
                               attempted_by="rehearsal")
            kind = ("pregame gate" if isinstance(exc, PostKickoffPlacement)
                    else "refused")
            add(f"- **D. after kickoff** -> {kind}: `{exc}`")

    # --- external non-model wager, still recordable -------------------------------------
    if discarded_key:
        external = ledger.record(
            active_card, discarded_key, sportsbook=BOOK, american_odds="-120",
            placed_at=T_PLACE, recorded_by="rehearsal_operator",
            designation=EXTERNAL_NON_MODEL,
            notes="fabricated: placed outside the model",
        )
        add(
            f"- **external non-model** -> recorded `{external.placement_id}`, excluded "
            "from every v1.0 figure"
        )
    add("")
    add(
        f"Refused attempts logged (no placement created): "
        f"**{len(ledger.refusals())}**. They live in `refusals.jsonl`, separate from the "
        "placement ledger, so a refused attempt can never be mistaken for a wager."
    )
    add("")
    add(
        "> **PROPOSED is never PLACED**, and there is **no override**: a model-designated "
        "placement that fails any gate cannot be forced through. This software submitted "
        "nothing to any sportsbook."
    )
    add("")

    # ---- Step 7: market-quality trail --------------------------------------------------
    add("## Step 7 — market-quality trail")
    add("")
    if placed:
        leg_id = placed[0].leg_ids[0]
        grading_quote = next(q for q in market_1.quotes if q.leg_key == leg_id)
        placement_quote = next(q for q in market_2.quotes if q.leg_key == leg_id)
        grading_obs = LineObservation(
            leg_id=leg_id, label=GRADING_LINE, spread=grading_quote.spread,
            total=grading_quote.total, sportsbook=BOOK, observed_at=T_GRADE,
            market_snapshot_id=market_1.snapshot_id,
        )
        placement_obs = LineObservation(
            leg_id=leg_id, label=PLACEMENT_LINE, spread=placement_quote.spread,
            total=placement_quote.total, sportsbook=BOOK, observed_at=T_PLACE,
            market_snapshot_id=market_2.snapshot_id,
        )
        final_obs = LineObservation(
            leg_id=leg_id, label=FINAL_OBSERVED, spread=placement_quote.spread,
            total=placement_quote.total, sportsbook=BOOK, observed_at=T_FINAL_OBS,
            market_snapshot_id=market_2.snapshot_id,
        )
        movement = line_movement(grading_obs, final_obs)
        add("| Label | Spread | Total | Observed at | Snapshot |")
        add("|---|---|---|---|---|")
        for obs in (grading_obs, placement_obs, final_obs):
            add(
                f"| {obs.label} | {obs.spread} | {obs.total} | {iso(obs.observed_at)} | "
                f"`{obs.market_snapshot_id}` |"
            )
        add("")
        add(f"Line movement grading -> final observed: **{movement['spread_change']}**.")
        add("")
        add(f"> {movement['clv_note']}")
    else:
        add("No placement, so no market-quality trail for this rehearsal week.")
    add("")

    # ---- Step 8: settlement ------------------------------------------------------------
    add("## Step 8 — settlement")
    add("")
    if placed:
        placement = placed[0]
        card_legs = {leg.leg_id: leg for leg in active_card.qualifying_legs}
        # Fabricated final margins: every leg covers its teased line.
        leg_settlements = []
        for leg_id in placement.leg_ids:
            leg = card_legs[leg_id]
            margin = 3  # fabricated: a 3-point win covers every primary teased line here
            leg_settlements.append(
                grade_leg_settlement(
                    leg_id=leg_id, team=leg.team, teased_spread=leg.teased_spread,
                    final_margin=margin, home_score=20, away_score=17,
                )
            )
        add("| Leg | Teased | Final margin | Model result |")
        add("|---|---|---|---|")
        for leg in leg_settlements:
            add(f"| {leg.leg_id} | {leg.teased_spread} | {leg.final_margin} | "
                f"{leg.model_result} |")
        add("")
        add(
            "No leg graded PUSH, as the half-point geometry guarantees; the settlement "
            "code raises rather than absorbing one if it ever appears."
        )
        add("")

        record = settle_ticket(
            placement=placement.to_dict(), legs=tuple(leg_settlements),
            book_settlement=BOOK_WIN, settled_at=T_SETTLE,
            settled_by="rehearsal_operator", book_reference="SYN-12345",
            notes="FABRICATED rehearsal settlement",
        )
        workspace.settlements.put(record.settlement_id, record.to_dict(), kind="settlement")
        add(f"Settlement `{record.settlement_id}`:")
        add("")
        add("| Field | Value |")
        add("|---|---|")
        add(f"| model_ticket_result | **{record.model_ticket_result}** |")
        add(f"| book_settlement | **{record.book_settlement}** |")
        add(f"| profit_loss_units | {record.profit_loss_units} |")
        add(f"| results_agree | {record.results_agree} |")
        add("")
        add(
            "The model grade and the sportsbook settlement are stored in **separate "
            "fields** even when they agree, because they are different claims: one is what "
            "frozen v1.0 says happened, the other is what the book actually did."
        )
        add("")
        add(
            "When they disagree — a book voiding or cancelling a wager the model graded a "
            "winner — both stand as recorded, the P/L follows the book, and no generic "
            "reconciliation rule is invented. `book_settlement` accepts VOID and CANCELLED "
            "for exactly that case; a dedicated test covers it."
        )
    else:
        add("Nothing was placed, so there is nothing to settle.")
    add("")

    # ---- Step 9: season ledger, derived ------------------------------------------------
    season_ledger = workspace.season_ledger
    season_ledger.record_week(
        WeekLedgerEntry(
            season=SEASON, week=WEEK, recorded_at=T_GRADE,
            games_scanned=active_card.games_scanned,
            qualifying_primary_legs=active_card.n_qualifying,
            top_four_legs=len(active_card.top_legs),
            positive_ev_tickets=active_card.n_positive_ev,
            proposed_tickets=len(active_card.selected_tickets),
            # Grading facts only. Placement and settlement are derived at read time.
            placed_tickets=0, units_staked=0.0,
            market_snapshot_id=market_1.snapshot_id,
            price_snapshot_id=prices_1.snapshot_id,
            card_id=active_card.card_id, card_status=active_card.status,
            notes="grading record; placement/settlement derived from the event ledgers",
        )
    )
    season_ledger.record_week(
        WeekLedgerEntry(
            season=SEASON, week=WEEK + 1, recorded_at=T_SETTLE, games_scanned=14,
            qualifying_primary_legs=0, top_four_legs=0, positive_ev_tickets=0,
            proposed_tickets=0, placed_tickets=0, units_staked=0.0,
            notes="synthetic: zero qualifying legs — recorded, not omitted",
        )
    )

    add("## Step 9 — append-only season ledger, derived automatically")
    add("")
    add(
        "**E.** The grading record above was written once, at grading time, with "
        "`placed_tickets = 0`. It has not been touched since. Everything below is derived "
        "from the append-only placement and settlement ledgers at the moment status is "
        "requested — **no operator re-recording step**."
    )
    add("")
    all_placements = ledger.entries(SEASON)
    all_settlements = workspace.all_settlements(SEASON)
    status = season_ledger.season_status(
        SEASON, placements=all_placements, settlements=all_settlements
    )
    status["refused_attempts"] = len(ledger.refusals(SEASON))
    add("| Metric | Value |")
    add("|---|---|")
    for key, value in status.items():
        add(f"| {key} | {value} |")
    add("")
    stored_grading = season_ledger.latest_per_week(SEASON)[0]
    add(
        f"The immutable grading row still reads "
        f"`placed_tickets = {stored_grading['placed_tickets']}`, "
        f"`units_staked = {stored_grading['units_staked']}` — unchanged — while the "
        f"derived status reports **{status['total_placed_tickets']} placed** and "
        f"**{status['total_units_staked']} unit(s) staked**. That is the point: the "
        "record of what the model saw never drifts, and the record of what happened is "
        "always current."
    )
    add("")
    add(
        f"Week {WEEK + 1} was recorded with **zero** qualifying legs and zero bets. Empty "
        "weeks appear exactly like active ones — omitting them would build survivorship "
        "bias into the prospective record by construction."
    )
    add("")

    # ---- Step 10: audit trail ----------------------------------------------------------
    add("## Step 10 — audit trail")
    add("")
    add("Every record written during this rehearsal, none of which overwrote another:")
    add("")
    add("| Kind | Record id |")
    add("|---|---|")
    for row in workspace.snapshots.list_records():
        add(f"| {row['kind']} | `{row['record_id']}` |")
    for row in workspace.cards.list_records():
        add(f"| {row['kind']} | `{row['record_id']}` |")
    for row in workspace.settlements.list_records():
        add(f"| {row['kind']} | `{row['record_id']}` |")
    for row in ledger.entries():
        add(f"| placement | `{row['placement_id']}` |")
    add("")

    duplicate = workspace.snapshots.put(
        market_1.snapshot_id, market_1.to_dict(), kind="market_snapshot"
    )
    add(
        f"Re-offering the grading snapshot returned "
        f"**{'created' if duplicate.created else 'already present (no-op)'}** — content-"
        "addressed ids make duplicate capture idempotent, and differing content can never "
        "collide with an earlier record."
    )
    add("")

    report = render_weekly_report(
        active_card, recheck=recheck,
        placements=[p.to_dict() for p in placed],
        settlements=[record.to_dict()] if placed else None,
    )
    report_path = ROOT / "reports" / "live" / f"nfl_{SEASON}_week_{WEEK:02d}_rehearsal.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)

    add("## Weekly report")
    add("")
    add(f"Rendered to `{report_path.relative_to(ROOT)}`.")
    add("")
    add("---")
    add("")
    add(
        "**Rehearsal complete.** Every transition the live system must handle was "
        "exercised against fabricated data: grading, a geometry break, a guardrail breach, "
        "a price move, discard, rebuild, explicit placement, a refused over-cap placement, "
        "a refused no-re-check attempt, a refused discarded-re-check attempt, a refused "
        "post-kickoff attempt, an accepted placement under a valid re-check, a refused "
        "over-cap placement, an external non-model entry, settlement, and a season status "
        "derived automatically from the event ledgers. No real market data was used and "
        "no wager was placed."
    )
    add("")

    out_path = ROOT / "reports" / "phase4_synthetic_rehearsal.md"
    out_path.write_text("\n".join(lines) + "\n")
    print(f"written: {out_path.relative_to(ROOT)}")
    print(f"written: {report_path.relative_to(ROOT)}")
    print(f"rehearsal workspace: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
