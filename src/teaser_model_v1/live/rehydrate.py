"""Reconstruct record objects from stored JSON.

Stored records are the source of truth. Rehydration re-validates everything on the way
back in — a file that has been hand-edited into an invalid state fails here rather than
flowing silently into a card.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from teaser_model_v1.live.card import GradedLeg, TicketView, WeeklyCard
from teaser_model_v1.live.schemas import (
    MarketQuote,
    MarketSnapshot,
    TeaserPriceQuote,
    TeaserPriceSnapshot,
)


def market_from_dict(payload: dict) -> MarketSnapshot:
    quotes = tuple(
        MarketQuote(
            game_id=row["game_id"],
            season=row["season"],
            week=row["week"],
            kickoff=row["kickoff"],
            home_team=row["home_team"],
            away_team=row["away_team"],
            team=row["team"],
            spread=row["spread"],
            total=row["total"],
            sportsbook=row["sportsbook"],
            captured_at=row["captured_at"],
            ingestion_method=row["ingestion_method"],
            source_reference=row.get("source_reference", ""),
            raw_source_value=row.get("raw_source_value", ""),
            notes=row.get("notes", ""),
        )
        for row in payload["quotes"]
    )
    # Rebuild WITHOUT the stored id so the snapshot recomputes its own content hash;
    # passing the stored id would short-circuit the check and make it meaningless.
    snapshot = MarketSnapshot(
        season=payload["season"],
        week=payload["week"],
        captured_at=payload["captured_at"],
        sportsbook=payload["sportsbook"],
        ingestion_method=payload["ingestion_method"],
        quotes=quotes,
        label=payload.get("label", ""),
        notes=payload.get("notes", ""),
    )
    stored_id = payload.get("snapshot_id")
    if stored_id and snapshot.snapshot_id != stored_id:
        raise ValueError(
            f"market snapshot {stored_id} does not match its own content hash; the file "
            "may have been edited. Records are append-only and must not be modified."
        )
    return snapshot


def prices_from_dict(payload: dict) -> TeaserPriceSnapshot:
    quotes = tuple(
        TeaserPriceQuote(
            ticket_size=row["ticket_size"],
            sportsbook=row["sportsbook"],
            captured_at=row["captured_at"],
            american_odds=row.get("american_odds"),
            teaser_points=row.get("teaser_points", 6),
            source_reference=row.get("source_reference", ""),
            notes=row.get("notes", ""),
        )
        for row in payload["quotes"]
    )
    # As above: recompute the hash rather than trusting the stored id.
    snapshot = TeaserPriceSnapshot(
        season=payload["season"],
        week=payload["week"],
        captured_at=payload["captured_at"],
        sportsbook=payload["sportsbook"],
        quotes=quotes,
        label=payload.get("label", ""),
        notes=payload.get("notes", ""),
    )
    stored_id = payload.get("snapshot_id")
    if stored_id and snapshot.snapshot_id != stored_id:
        raise ValueError(
            f"price snapshot {stored_id} does not match its own content hash; the file "
            "may have been edited."
        )
    return snapshot


def card_from_dict(payload: dict) -> WeeklyCard:
    legs = tuple(
        GradedLeg(
            rank=row["rank"],
            leg_id=row["leg_id"],
            game_id=row["game_id"],
            team=row["team"],
            opponent=row["opponent"],
            spread=Decimal(row["spread"]),
            teased_spread=Decimal(row["teased_spread"]),
            total=Decimal(row["total"]),
            geometry_class=row["geometry_class"],
            track=row["track"],
            key_numbers_crossed=row["key_numbers_crossed"],
            p_raw=float(row["p_raw"]),
            bump=float(row["bump"]),
            p_est=float(row["p_est"]),
            kickoff=row["kickoff"],
            sportsbook=row["sportsbook"],
            market_snapshot_id=row["market_snapshot_id"],
        )
        for row in payload["qualifying_legs"]
    )
    top_ids = set(payload["top_legs"])
    tickets = tuple(
        TicketView(
            ticket_key=row["ticket_key"],
            n_legs=row["n_legs"],
            leg_ids=tuple(row["leg_ids"]),
            teams=tuple(row["teams"]),
            p_ticket=float(row["p_ticket"]),
            offered_american=row["offered_american"],
            offered_decimal=row["offered_decimal"],
            net_profit_per_unit=row["net_profit_per_unit"],
            break_even=row["break_even"],
            ev_per_unit=row["ev_per_unit"],
            ev_percent=row["ev_percent"],
            status=row["status"],
            selected=row["selected"],
            price_snapshot_id=row["price_snapshot_id"],
        )
        for row in payload["tickets"]
    )
    return WeeklyCard(
        season=payload["season"],
        week=payload["week"],
        graded_at=datetime.fromisoformat(payload["graded_at"]),
        market_snapshot_id=payload["market_snapshot_id"],
        price_snapshot_id=payload["price_snapshot_id"],
        sportsbook=payload["sportsbook"],
        games_scanned=payload["games_scanned"],
        qualifying_legs=legs,
        top_legs=tuple(leg for leg in legs if leg.leg_id in top_ids),
        tickets=tickets,
        selected_ticket_keys=tuple(payload["selected_ticket_keys"]),
        exposure=dict(payload["exposure"]),
        status=payload["status"],
        card_id=payload.get("card_id", ""),
        notes=payload.get("notes", ""),
    )


def recheck_from_dict(payload: dict):
    """Rebuild a re-check result well enough to gate a placement.

    Only the verdicts and reasons are needed downstream, so the legs are restored as a
    lightweight view rather than re-running the comparison.
    """
    from teaser_model_v1.live.recheck import LegRecheck, RecheckResult, TicketRecheck

    tickets = tuple(
        TicketRecheck(
            ticket_key=row["ticket_key"],
            n_legs=row["n_legs"],
            verdict=row["verdict"],
            reasons=tuple(row["reasons"]),
            legs=tuple(
                LegRecheck(
                    leg_id=leg["leg_id"], ok=leg["ok"], reasons=tuple(leg["reasons"]),
                    old_spread=leg["old_spread"], new_spread=leg["new_spread"],
                    old_total=leg["old_total"], new_total=leg["new_total"],
                    old_p_est=leg["old_p_est"], new_p_est=leg["new_p_est"],
                )
                for leg in row["legs"]
            ),
            old_ev=row["old_ev"], new_ev=row["new_ev"],
            new_break_even=row["new_break_even"], new_p_ticket=row["new_p_ticket"],
        )
        for row in payload["tickets"]
    )
    return RecheckResult(
        season=payload["season"],
        week=payload["week"],
        rechecked_at=datetime.fromisoformat(payload["rechecked_at"]),
        original_card_id=payload["original_card_id"],
        original_market_snapshot_id=payload["original_market_snapshot_id"],
        original_price_snapshot_id=payload["original_price_snapshot_id"],
        new_market_snapshot_id=payload["new_market_snapshot_id"],
        new_price_snapshot_id=payload["new_price_snapshot_id"],
        tickets=tickets,
        rebuilt_card=None,
        recheck_id=payload.get("recheck_id", ""),
    )
