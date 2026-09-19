#!/usr/bin/env python3
"""``teaser-live`` — the weekly operator CLI for frozen Teaser Model v1.0.

    teaser-live market-template   --season 2026 --week 3
    teaser-live price-template    --season 2026 --week 3
    teaser-live ingest-market     --file ... [--dry-run]
    teaser-live ingest-prices     --file ... --season --week [--dry-run]
    teaser-live grade-week        --season --week --market ID --prices ID
    teaser-live show-card         --season --week [--card ID]
    teaser-live recheck           --card ID --market ID [--prices ID]
    teaser-live record-placement  --card ID --ticket KEY --book --odds --placed-at --by
    teaser-live settle            --placement ID --leg ... --book-settlement ...
    teaser-live season-status     --season 2026
    teaser-live correct           --supersedes ID --reason ... --by ...

**NO COMMAND PLACES A WAGER.** `record-placement` records a wager the operator has already
made; nothing here talks to a sportsbook.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from teaser_model_v1.live.card import grade_week  # noqa: E402
from teaser_model_v1.live.ledger import SeasonLedger, WeekLedgerEntry  # noqa: E402
from teaser_model_v1.live.market import read_market_csv, write_template  # noqa: E402
from teaser_model_v1.live.placement import (  # noqa: E402
    EXTERNAL_NON_MODEL,
    MODEL_DESIGNATED,
)
from teaser_model_v1.live.pricing import read_price_csv, write_price_template  # noqa: E402
from teaser_model_v1.live.provenance import require_aware, utc_now  # noqa: E402
from teaser_model_v1.live.recheck import recheck_card  # noqa: E402
from teaser_model_v1.live.report import write_weekly_report  # noqa: E402
from teaser_model_v1.live.rehydrate import (  # noqa: E402
    card_from_dict,
    market_from_dict,
    prices_from_dict,
)
from teaser_model_v1.live.settlement import (  # noqa: E402
    grade_leg_settlement,
    settle_ticket,
)
from teaser_model_v1.live.snapshot import correction_record  # noqa: E402
from teaser_model_v1.live.workspace import Workspace

BANNER = "teaser-live — records and reports only. This tool never places a wager."


def _workspace(args) -> Workspace:
    return Workspace(Path(args.root) if args.root else ROOT)


# ---------------------------------------------------------------------------------------


def cmd_market_template(args) -> int:
    workspace = _workspace(args)
    path = workspace.input_dir / f"nfl_{args.season}_week_{args.week:02d}_market.csv"
    write_template(path, season=args.season, week=args.week)
    print(f"wrote manual market template: {path}")
    print("Fill one row per SIDE. Timestamps need an explicit UTC offset.")
    return 0


def cmd_price_template(args) -> int:
    workspace = _workspace(args)
    path = workspace.input_dir / f"nfl_{args.season}_week_{args.week:02d}_prices.csv"
    write_price_template(path)
    print(f"wrote teaser price template: {path}")
    print("Record only prices you have ACTUALLY seen on the book's menu.")
    return 0


def cmd_ingest_market(args) -> int:
    workspace = _workspace(args)
    snapshot = read_market_csv(
        args.file, sportsbook=args.book, label=args.label or "", notes=args.notes or ""
    )
    print(f"validated {len(snapshot.quotes)} quotes across {len(snapshot.games)} games")
    print(f"snapshot id: {snapshot.snapshot_id}")
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0
    result = workspace.snapshots.put(
        snapshot.snapshot_id, snapshot.to_dict(), kind="market_snapshot"
    )
    print("stored" if result.created else "identical snapshot already stored (no-op)")
    return 0


def cmd_ingest_prices(args) -> int:
    workspace = _workspace(args)
    snapshot = read_price_csv(
        args.file, season=args.season, week=args.week,
        label=args.label or "", notes=args.notes or "",
    )
    for quote in snapshot.quotes:
        print(
            f"  {quote.ticket_size}-team: {quote.american_odds} "
            f"(decimal {quote.decimal_odds}, net profit {quote.net_profit_per_unit})"
        )
    print(f"snapshot id: {snapshot.snapshot_id}")
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0
    result = workspace.snapshots.put(
        snapshot.snapshot_id, snapshot.to_dict(), kind="teaser_price_snapshot"
    )
    print("stored" if result.created else "identical snapshot already stored (no-op)")
    return 0


def cmd_grade_week(args) -> int:
    workspace = _workspace(args)
    market = market_from_dict(workspace.snapshots.get(args.market))
    prices = prices_from_dict(workspace.snapshots.get(args.prices)) if args.prices else None

    card = grade_week(market, prices, notes=args.notes or "")
    print(f"card id: {card.card_id}   status: {card.status}")
    print(f"qualifying primary legs: {card.n_qualifying}")
    print(f"tickets constructed: {len(card.tickets)}  positive EV: {card.n_positive_ev}")
    print(f"proposed (model-designated): {len(card.selected_tickets)}")
    if not card.tickets:
        print("NO CONSTRUCTIBLE LIVE PRIMARY TICKET")

    if args.dry_run:
        print("--dry-run: nothing written")
        return 0

    workspace.cards.put(card.card_id, card.to_dict(), kind="weekly_card")
    report = write_weekly_report(
        card, workspace.reports_dir / f"nfl_{card.season}_week_{card.week:02d}.md"
    )
    print(f"report: {report}")

    workspace.season_ledger.record_week(
        WeekLedgerEntry(
            season=card.season, week=card.week, recorded_at=utc_now(),
            games_scanned=card.games_scanned,
            qualifying_primary_legs=card.n_qualifying,
            top_four_legs=len(card.top_legs),
            positive_ev_tickets=card.n_positive_ev,
            proposed_tickets=len(card.selected_tickets),
            # Placement and settlement facts are NOT copied here; they are derived from
            # the append-only ledgers whenever status is read.
            placed_tickets=0, units_staked=0.0,
            market_snapshot_id=card.market_snapshot_id,
            price_snapshot_id=card.price_snapshot_id,
            card_id=card.card_id, card_status=card.status,
            notes="graded; nothing placed",
        )
    )
    print("season ledger updated (week recorded even if empty)")
    print("placement/settlement status is derived at read time; no re-recording needed")
    return 0


def cmd_show_card(args) -> int:
    workspace = _workspace(args)
    payload = (
        workspace.cards.get(args.card) if args.card
        else workspace.latest_card(args.season, args.week)
    )
    if payload is None:
        print(f"no card stored for {args.season} week {args.week}")
        return 1
    card = card_from_dict(payload)
    placements = workspace.placements.entries(card.season, card.week)
    placement_ids = {row["placement_id"] for row in placements}
    settlements = [
        row for row in workspace.all_settlements(card.season)
        if row.get("placement_id") in placement_ids
    ]
    print(write_weekly_report(
        card,
        workspace.reports_dir / f"nfl_{card.season}_week_{card.week:02d}.md",
        placements=placements,
        settlements=settlements,
    ))
    return 0


def cmd_recheck(args) -> int:
    workspace = _workspace(args)
    card = card_from_dict(workspace.cards.get(args.card))
    market = market_from_dict(workspace.snapshots.get(args.market))
    prices = prices_from_dict(workspace.snapshots.get(args.prices)) if args.prices else None

    result = recheck_card(card, market, prices)
    print(f"re-check {result.recheck_id}: {result.overall}")
    for ticket in result.tickets:
        print(f"  {ticket.ticket_key}: {ticket.verdict}")
        for reason in ticket.reasons:
            print(f"      - {reason}")
    if result.rebuilt_card:
        print(f"rebuilt card: {result.rebuilt_card.card_id}")
        print("Discarded tickets were NOT substituted and NOT downgraded.")

    if args.dry_run:
        print("--dry-run: nothing written")
        return 0

    workspace.cards.put(result.recheck_id, result.to_dict(), kind="recheck")
    if result.rebuilt_card:
        workspace.cards.put(
            result.rebuilt_card.card_id, result.rebuilt_card.to_dict(), kind="weekly_card"
        )
    return 0


def cmd_record_placement(args) -> int:
    from teaser_model_v1.live.placement import PlacementRefused
    from teaser_model_v1.live.rehydrate import recheck_from_dict

    workspace = _workspace(args)
    card = card_from_dict(workspace.cards.get(args.card))
    ledger = workspace.placements
    placed_at = require_aware(args.placed_at, field="--placed-at")
    designation = EXTERNAL_NON_MODEL if args.external else MODEL_DESIGNATED

    recheck = recheck_from_dict(workspace.cards.get(args.recheck)) if args.recheck else None

    if designation == MODEL_DESIGNATED:
        if recheck is None:
            print(
                "REFUSED: a model-designated placement requires --recheck.\n"
                "  Run `recheck` against a current market and teaser-price snapshot first.\n"
                "  There is no override. Use --external to record a non-model wager."
            )
            ledger.log_refusal(
                card=card, ticket_key=args.ticket, placed_at=placed_at,
                reason="no re-check supplied", attempted_by=args.by,
            )
            return 2
        try:
            # Validate BEFORE writing anything.
            ledger.validate_model_placement(
                card, args.ticket, placed_at=placed_at, recheck=recheck,
                known_rechecks=workspace.rechecks_for_card(card.card_id),
                stake_units=args.stake,
            )
        except (PlacementRefused, ValueError) as exc:
            print(f"REFUSED: {exc}")
            ledger.log_refusal(
                card=card, ticket_key=args.ticket, placed_at=placed_at,
                reason=str(exc), attempted_by=args.by,
            )
            print("No placement record was written. The attempt is logged in refusals.jsonl.")
            return 2

    record = ledger.record(
        card, args.ticket,
        recheck=recheck,
        known_rechecks=workspace.rechecks_for_card(card.card_id),
        sportsbook=args.book,
        american_odds=args.odds,
        placed_at=placed_at,
        recorded_by=args.by,
        stake_units=args.stake,
        designation=designation,
        book_reference=args.reference or "",
        notes=args.notes or "",
    )
    print(f"RECORDED PLACEMENT {record.placement_id}")
    print(f"  ticket {record.ticket_key} at {record.sportsbook} {record.american_odds}")
    print(f"  designation: {record.designation}")
    print("  (this records a wager you already made; nothing was submitted)")
    return 0


def cmd_settle(args) -> int:
    workspace = _workspace(args)
    placement = next(
        (row for row in workspace.placements.entries()
         if row["placement_id"] == args.placement), None
    )
    if placement is None:
        print(f"no placement {args.placement}")
        return 1

    legs = []
    for spec in args.leg:
        leg_id, team, teased, margin = spec.split(":")
        legs.append(
            grade_leg_settlement(
                leg_id=leg_id, team=team, teased_spread=teased,
                final_margin=int(margin),
            )
        )

    record = settle_ticket(
        placement=placement, legs=tuple(legs),
        book_settlement=args.book_settlement,
        settled_at=require_aware(args.settled_at, field="--settled-at"),
        profit_loss_units=args.profit_loss,
        settled_by=args.by, book_reference=args.reference or "",
        notes=args.notes or "",
    )
    workspace.settlements.put(record.settlement_id, record.to_dict(), kind="settlement")
    print(f"settled {record.settlement_id}")
    print(f"  model result:      {record.model_ticket_result}")
    print(f"  book settlement:   {record.book_settlement}")
    print(f"  profit/loss units: {record.profit_loss_units}")
    if not record.results_agree:
        print("  NOTE: model grade and book settlement differ; both stand as recorded.")
    return 0


def cmd_season_status(args) -> int:
    workspace = _workspace(args)
    placements = workspace.placements.entries(args.season)
    settlements = workspace.all_settlements(args.season)
    status = workspace.season_ledger.season_status(
        args.season, placements=placements, settlements=settlements
    )
    status["refused_attempts"] = len(workspace.placements.refusals(args.season))
    print(json.dumps(status, indent=2))
    if args.by_week:
        print()
        print(json.dumps(
            workspace.season_ledger.derive_weeks(
                args.season, placements=placements, settlements=settlements
            ),
            indent=2,
        ))
    print(
        "\nPlacement and settlement figures are derived from the append-only ledgers at "
        "read time; no re-recording is needed to synchronise them."
    )
    print("Weeks with zero qualifying legs and zero bets are included above.")
    return 0


def cmd_correct(args) -> int:
    workspace = _workspace(args)
    record = correction_record(
        supersedes_id=args.supersedes, reason=args.reason,
        corrected_by=args.by, replacement_id=args.replacement or "",
        notes=args.notes or "",
    )
    record_id = f"cor_{args.supersedes}"
    workspace.corrections.put(record_id, record, kind="correction")
    print(f"correction recorded: {record_id}")
    print("The original record is unchanged; history is never rewritten.")
    return 0


# ---------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="teaser-live", description=BANNER)
    parser.add_argument("--root", default=None, help="repository root (default: detected)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add(name, handler, help_text):
        sub = subparsers.add_parser(name, help=help_text)
        sub.set_defaults(handler=handler)
        return sub

    sub = add("market-template", cmd_market_template, "write a manual market CSV template")
    sub.add_argument("--season", type=int, required=True)
    sub.add_argument("--week", type=int, required=True)

    sub = add("price-template", cmd_price_template, "write a teaser price CSV template")
    sub.add_argument("--season", type=int, required=True)
    sub.add_argument("--week", type=int, required=True)

    sub = add("ingest-market", cmd_ingest_market, "validate and store a market snapshot")
    sub.add_argument("--file", required=True)
    sub.add_argument("--book", default=None)
    sub.add_argument("--label", default=None)
    sub.add_argument("--notes", default=None)
    sub.add_argument("--dry-run", action="store_true")

    sub = add("ingest-prices", cmd_ingest_prices, "validate and store an ACTUAL teaser menu")
    sub.add_argument("--file", required=True)
    sub.add_argument("--season", type=int, required=True)
    sub.add_argument("--week", type=int, required=True)
    sub.add_argument("--label", default=None)
    sub.add_argument("--notes", default=None)
    sub.add_argument("--dry-run", action="store_true")

    sub = add("grade-week", cmd_grade_week, "build the frozen weekly board and proposed card")
    sub.add_argument("--season", type=int, required=True)
    sub.add_argument("--week", type=int, required=True)
    sub.add_argument("--market", required=True)
    sub.add_argument("--prices", default=None)
    sub.add_argument("--notes", default=None)
    sub.add_argument("--dry-run", action="store_true")

    sub = add("show-card", cmd_show_card, "print the weekly report")
    sub.add_argument("--season", type=int, required=True)
    sub.add_argument("--week", type=int, required=True)
    sub.add_argument("--card", default=None)

    sub = add("recheck", cmd_recheck, "placement-time re-check against a NEW snapshot")
    sub.add_argument("--card", required=True)
    sub.add_argument("--market", required=True)
    sub.add_argument("--prices", default=None)
    sub.add_argument("--dry-run", action="store_true")

    sub = add("record-placement", cmd_record_placement,
              "record a wager YOU already placed (submits nothing)")
    sub.add_argument("--card", required=True)
    sub.add_argument("--ticket", required=True)
    sub.add_argument("--book", required=True)
    sub.add_argument("--odds", required=True)
    sub.add_argument("--placed-at", required=True, dest="placed_at")
    sub.add_argument("--by", required=True)
    sub.add_argument("--stake", type=float, default=1.0)
    sub.add_argument("--external", action="store_true",
                     help="mark as a non-model wager, excluded from v1.0 performance")
    sub.add_argument("--recheck", default=None,
                     help="REQUIRED for a model-designated placement; the ticket must be "
                          "VALIDATED in it and the re-check must be current and pregame")
    sub.add_argument("--reference", default=None)
    sub.add_argument("--notes", default=None)

    sub = add("settle", cmd_settle, "settle a placed wager")
    sub.add_argument("--placement", required=True)
    sub.add_argument("--leg", action="append", required=True,
                     metavar="LEG_ID:TEAM:TEASED:MARGIN")
    sub.add_argument("--book-settlement", required=True, dest="book_settlement")
    sub.add_argument("--settled-at", required=True, dest="settled_at")
    sub.add_argument("--profit-loss", type=float, default=None, dest="profit_loss")
    sub.add_argument("--by", default="")
    sub.add_argument("--reference", default=None)
    sub.add_argument("--notes", default=None)

    sub = add("season-status", cmd_season_status, "season totals, including empty weeks")
    sub.add_argument("--season", type=int, required=True)
    sub.add_argument("--by-week", action="store_true", dest="by_week")

    sub = add("correct", cmd_correct, "supersede a record without rewriting it")
    sub.add_argument("--supersedes", required=True)
    sub.add_argument("--reason", required=True)
    sub.add_argument("--by", required=True)
    sub.add_argument("--replacement", default=None)
    sub.add_argument("--notes", default=None)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
