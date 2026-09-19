"""Phase 4.1: mandatory re-check, pregame enforcement, derived season status.

These are the gates that stand between a proposed card and a v1.0 model-designated wager.
Each is tested for the failure it exists to prevent, not just the happy path.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tests.test_live_card import FIVE_PRIMARY, board, prices
from teaser_model_v1.live.card import grade_week
from teaser_model_v1.live.ledger import SeasonLedger, WeekLedgerEntry
from teaser_model_v1.live.placement import (
    EXTERNAL_NON_MODEL,
    MAX_PRICE_LAG,
    MAX_RECHECK_AGE,
    MODEL_DESIGNATED,
    ExposureCapViolation,
    PlacementLedger,
    PlacementRefused,
    PostKickoffPlacement,
)
from teaser_model_v1.live.recheck import recheck_card
from teaser_model_v1.live.settlement import (
    BOOK_LOSS,
    BOOK_VOID,
    BOOK_WIN,
    grade_leg_settlement,
    settle_ticket,
)

EASTERN = timezone(timedelta(hours=-4))
KICKOFF = datetime(2026, 9, 20, 13, 0, tzinfo=EASTERN)  # matches test_live_card.board()
GRADED = datetime(2026, 9, 19, 10, 0, tzinfo=EASTERN)
RECHECKED = datetime(2026, 9, 20, 12, 40, tzinfo=EASTERN)
PLACED = datetime(2026, 9, 20, 12, 45, tzinfo=EASTERN)


@pytest.fixture
def card():
    return grade_week(board(FIVE_PRIMARY), prices(two=-110, three=180), graded_at=GRADED)


@pytest.fixture
def ledger(tmp_path):
    return PlacementLedger(tmp_path / "placements.jsonl")


def clean_recheck(card, *, at=RECHECKED, price_at=None, board_at=None):
    return recheck_card(
        card,
        board(FIVE_PRIMARY, captured_at=board_at or at),
        prices(two=-110, three=180, captured_at=price_at or at),
        rechecked_at=at,
    )


def moved(team, spread=None, total=None):
    return [
        (away, home, side, spread or old_spread, total or old_total)
        if side == team else (away, home, side, old_spread, old_total)
        for away, home, side, old_spread, old_total in FIVE_PRIMARY
    ]


def place(ledger, card, ticket_key, *, recheck, placed_at=PLACED, **kwargs):
    defaults = dict(sportsbook="BookX", american_odds="-110", recorded_by="operator")
    defaults.update(kwargs)
    return ledger.record(card, ticket_key, recheck=recheck, placed_at=placed_at, **defaults)


# =======================================================================================
# 1. Mandatory re-check
# =======================================================================================


def test_model_placement_without_a_recheck_fails(ledger, card):
    ticket = card.selected_tickets[0]
    with pytest.raises(PlacementRefused, match="requires a placement-time re-check"):
        ledger.record(card, ticket.ticket_key, sportsbook="BookX", american_odds="-110",
                      placed_at=PLACED, recorded_by="operator")
    assert ledger.entries() == []


def test_model_placement_with_a_discarded_recheck_fails(ledger, card):
    result = recheck_card(
        card, board(moved("NE", spread="3.0"), captured_at=RECHECKED),
        prices(two=-110, three=180, captured_at=RECHECKED), rechecked_at=RECHECKED,
    )
    discarded = result.discarded[0]
    with pytest.raises(PlacementRefused, match="DISCARDED at re-check"):
        place(ledger, card, discarded.ticket_key, recheck=result)
    assert ledger.entries() == []


def test_a_recheck_for_a_different_card_fails(ledger, card):
    other_card = grade_week(
        board(FIVE_PRIMARY[:3]), prices(two=-110, three=180), graded_at=GRADED
    )
    foreign = clean_recheck(other_card)
    with pytest.raises(PlacementRefused, match="is for card"):
        place(ledger, card, card.selected_tickets[0].ticket_key, recheck=foreign)


def test_a_recheck_that_omits_the_ticket_fails(ledger, card):
    keys = (card.selected_tickets[0].ticket_key,)
    partial = recheck_card(
        card, board(FIVE_PRIMARY, captured_at=RECHECKED),
        prices(two=-110, three=180, captured_at=RECHECKED),
        rechecked_at=RECHECKED, tickets_to_check=keys,
    )
    other = next(t for t in card.selected_tickets if t.ticket_key not in keys)
    with pytest.raises(PlacementRefused, match="not covered by re-check"):
        place(ledger, card, other.ticket_key, recheck=partial)


def test_a_stale_recheck_fails(ledger, card):
    # Re-check early enough that "stale" still lands before kickoff; otherwise the
    # pregame gate would mask the staleness gate.
    early = KICKOFF - timedelta(hours=1)
    result = clean_recheck(card, at=early)
    too_late = early + MAX_RECHECK_AGE + timedelta(minutes=1)
    assert too_late < KICKOFF, "the fixture must still be pregame"
    with pytest.raises(PlacementRefused, match="old at the moment of placement"):
        place(ledger, card, card.selected_tickets[0].ticket_key,
              recheck=result, placed_at=too_late)
    assert ledger.entries() == []


def test_a_superseded_recheck_fails(ledger, card):
    older = clean_recheck(card, at=RECHECKED)
    newer = clean_recheck(card, at=RECHECKED + timedelta(minutes=5))
    with pytest.raises(PlacementRefused, match="superseded by"):
        place(ledger, card, card.selected_tickets[0].ticket_key,
              recheck=older, known_rechecks=[older, newer])


def test_the_most_recent_recheck_is_accepted(ledger, card):
    older = clean_recheck(card, at=RECHECKED - timedelta(minutes=10))
    newer = clean_recheck(card, at=RECHECKED)
    record = place(ledger, card, card.selected_tickets[0].ticket_key,
                   recheck=newer, known_rechecks=[older, newer])
    assert record.counts_toward_model


def test_a_recheck_against_the_grading_snapshot_is_impossible(card):
    from teaser_model_v1.live.recheck import StaleSnapshotError

    with pytest.raises(StaleSnapshotError):
        recheck_card(card, board(FIVE_PRIMARY), prices(two=-110, three=180))


def test_a_recheck_without_a_price_snapshot_fails(ledger, card):
    result = recheck_card(card, board(FIVE_PRIMARY, captured_at=RECHECKED), None,
                          rechecked_at=RECHECKED)
    with pytest.raises(PlacementRefused):
        place(ledger, card, card.selected_tickets[0].ticket_key, recheck=result)


def test_a_non_contemporaneous_price_fails(ledger, card):
    stale_price_at = RECHECKED - MAX_PRICE_LAG - timedelta(minutes=5)
    result = clean_recheck(card, at=RECHECKED, price_at=stale_price_at)
    with pytest.raises(PlacementRefused, match="not contemporaneous"):
        place(ledger, card, card.selected_tickets[0].ticket_key, recheck=result)


def test_a_valid_recheck_succeeds(ledger, card):
    result = clean_recheck(card)
    record = place(ledger, card, card.selected_tickets[0].ticket_key, recheck=result)
    assert record.counts_toward_model
    assert record.recheck_id == result.recheck_id
    assert len(ledger.model_entries()) == 1


def test_external_non_model_entry_remains_possible_without_a_recheck(ledger, card):
    unproposed = next(t for t in card.tickets if not t.selected)
    record = ledger.record(
        card, unproposed.ticket_key, sportsbook="BookX", american_odds="-110",
        placed_at=PLACED, recorded_by="operator", designation=EXTERNAL_NON_MODEL,
    )
    assert not record.counts_toward_model
    assert ledger.model_entries() == []
    assert len(ledger.entries()) == 1


def test_there_is_no_override_flag_for_model_designation():
    """No parameter may force an invalid ticket through as MODEL_DESIGNATED."""
    import inspect

    signature = inspect.signature(PlacementLedger.record)
    for banned in ("force", "allow_unproposed", "override", "skip_recheck", "ignore"):
        assert banned not in signature.parameters, f"override parameter {banned!r} exists"

    source = (
        __import__("teaser_model_v1.live.placement", fromlist=["x"]).__file__
    )
    text = open(source).read()
    assert "allow_unproposed" not in text


def test_refusals_are_logged_but_create_no_placement(ledger, card):
    ticket = card.selected_tickets[0]
    with pytest.raises(PlacementRefused):
        ledger.record(card, ticket.ticket_key, sportsbook="BookX", american_odds="-110",
                      placed_at=PLACED, recorded_by="operator")
    ledger.log_refusal(card=card, ticket_key=ticket.ticket_key, placed_at=PLACED,
                       reason="no re-check supplied", attempted_by="operator")
    assert ledger.entries() == []
    refusals = ledger.refusals()
    assert len(refusals) == 1
    assert refusals[0]["placement_created"] is False


# =======================================================================================
# 2. Post-kickoff placement is blocked
# =======================================================================================


def test_one_second_before_kickoff_succeeds(ledger, card):
    just_before = KICKOFF - timedelta(seconds=1)
    result = clean_recheck(card, at=just_before - timedelta(minutes=1))
    record = place(ledger, card, card.selected_tickets[0].ticket_key,
                   recheck=result, placed_at=just_before)
    assert record.counts_toward_model


def test_exactly_at_kickoff_fails(ledger, card):
    result = clean_recheck(card, at=KICKOFF - timedelta(minutes=5))
    with pytest.raises(PostKickoffPlacement, match="not pregame"):
        place(ledger, card, card.selected_tickets[0].ticket_key,
              recheck=result, placed_at=KICKOFF)
    assert ledger.entries() == []


def test_after_kickoff_fails(ledger, card):
    result = clean_recheck(card, at=KICKOFF - timedelta(minutes=5))
    with pytest.raises(PostKickoffPlacement):
        place(ledger, card, card.selected_tickets[0].ticket_key,
              recheck=result, placed_at=KICKOFF + timedelta(minutes=20))


def test_one_started_leg_fails_the_whole_three_team_ticket(ledger, card):
    """A 3-team ticket with a single kicked-off leg is refused entirely."""
    early = KICKOFF - timedelta(hours=3)
    rows = [
        (away, home, side, spread, total)
        for away, home, side, spread, total in FIVE_PRIMARY
    ]
    market = board(rows, captured_at=GRADED)
    # Rebuild with one game kicking off earlier than the rest.
    from teaser_model_v1.live.schemas import MarketQuote, MarketSnapshot

    quotes = []
    for quote in market.quotes:
        kickoff = early if quote.team == "MIA" else KICKOFF
        quotes.append(
            MarketQuote(
                game_id=quote.game_id, season=quote.season, week=quote.week,
                kickoff=kickoff, home_team=quote.home_team, away_team=quote.away_team,
                team=quote.team, spread=quote.spread, total=quote.total,
                sportsbook=quote.sportsbook, captured_at=quote.captured_at,
                ingestion_method=quote.ingestion_method,
            )
        )
    staggered = MarketSnapshot(
        season=2026, week=3, captured_at=GRADED, sportsbook="BookX",
        ingestion_method="test", quotes=tuple(quotes),
    )
    staggered_card = grade_week(staggered, prices(two=-110, three=180), graded_at=GRADED)

    three_team = [t for t in staggered_card.tickets if t.n_legs == 3 and "MIA" in t.teams]
    if not three_team:
        pytest.skip("fixture produced no 3-team ticket containing the early game")

    later_quotes = tuple(
        MarketQuote(
            game_id=q.game_id, season=q.season, week=q.week, kickoff=q.kickoff,
            home_team=q.home_team, away_team=q.away_team, team=q.team,
            spread=q.spread, total=q.total, sportsbook=q.sportsbook,
            captured_at=early - timedelta(minutes=10),
            ingestion_method=q.ingestion_method,
        )
        for q in quotes
    )
    later_market = MarketSnapshot(
        season=2026, week=3, captured_at=early - timedelta(minutes=10),
        sportsbook="BookX", ingestion_method="test", quotes=later_quotes,
    )
    result = recheck_card(
        staggered_card, later_market,
        prices(two=-110, three=180, captured_at=early - timedelta(minutes=10)),
        rechecked_at=early - timedelta(minutes=10),
        tickets_to_check=(three_team[0].ticket_key,),
    )
    # Placement after the MIA game has started, but before the others.
    with pytest.raises(PostKickoffPlacement):
        place(ledger, staggered_card, three_team[0].ticket_key,
              recheck=result, placed_at=early + timedelta(minutes=5))


def test_an_in_game_market_snapshot_is_refused(ledger, card):
    """The validating snapshot must itself be pregame, not merely the placement.

    Constructed so the placement is comfortably pregame while the board it was validated
    against was captured after kickoff — an in-game line the model was never specified
    against.
    """
    result = clean_recheck(
        card, at=RECHECKED, board_at=KICKOFF + timedelta(minutes=10),
    )
    with pytest.raises(PostKickoffPlacement, match="in-game line"):
        place(ledger, card, card.selected_tickets[0].ticket_key,
              recheck=result, placed_at=PLACED)
    assert ledger.entries() == []


def test_external_wagers_are_not_subject_to_the_kickoff_gate(ledger, card):
    """An outside wager is recorded as reported; it is excluded from v1.0 anyway."""
    record = ledger.record(
        card, card.selected_tickets[0].ticket_key, sportsbook="BookX",
        american_odds="-110", placed_at=KICKOFF + timedelta(hours=1),
        recorded_by="operator", designation=EXTERNAL_NON_MODEL,
    )
    assert not record.counts_toward_model


# =======================================================================================
# 3. Season status derived from the ledgers
# =======================================================================================


@pytest.fixture
def season(tmp_path):
    return SeasonLedger(tmp_path / "season.jsonl")


def grading_entry(card, week=3):
    return WeekLedgerEntry(
        season=card.season, week=week, recorded_at=GRADED,
        games_scanned=card.games_scanned,
        qualifying_primary_legs=card.n_qualifying,
        top_four_legs=len(card.top_legs),
        positive_ev_tickets=card.n_positive_ev,
        proposed_tickets=len(card.selected_tickets),
        placed_tickets=0, units_staked=0.0, card_id=card.card_id,
    )


def test_status_reflects_a_placement_with_no_synchronisation_step(season, ledger, card):
    season.record_week(grading_entry(card))
    status = season.season_status(2026, placements=ledger.entries(), settlements=[])
    assert status["total_placed_tickets"] == 0
    assert status["total_units_staked"] == 0.0

    place(ledger, card, card.selected_tickets[0].ticket_key, recheck=clean_recheck(card))

    # No re-recording of the week: status is derived from the ledger at read time.
    status = season.season_status(2026, placements=ledger.entries(), settlements=[])
    assert status["total_placed_tickets"] == 1
    assert status["total_units_staked"] == 1.0
    assert status["unsettled_tickets"] == 1
    assert status["total_profit_loss_units"] == 0.0


def test_status_reflects_settlement_immediately(season, ledger, card):
    season.record_week(grading_entry(card))
    placement = place(ledger, card, card.selected_tickets[0].ticket_key,
                      recheck=clean_recheck(card))
    legs = tuple(
        grade_leg_settlement(leg_id=leg_id, team="X", teased_spread="7.5", final_margin=3)
        for leg_id in placement.leg_ids
    )
    settlement = settle_ticket(
        placement=placement.to_dict(), legs=legs, book_settlement=BOOK_WIN,
        settled_at=KICKOFF + timedelta(hours=4),
    )

    status = season.season_status(
        2026, placements=ledger.entries(), settlements=[settlement.to_dict()]
    )
    assert status["settled_tickets"] == 1
    assert status["unsettled_tickets"] == 0
    assert status["total_wins"] == 1
    assert status["total_losses"] == 0
    assert status["total_profit_loss_units"] == pytest.approx(100 / 110)


def test_a_loss_and_a_void_are_counted_distinctly(season, ledger, card):
    season.record_week(grading_entry(card))
    placements, settlements = [], []
    check = clean_recheck(card)
    for index, ticket in enumerate(card.selected_tickets[:2]):
        placement = place(ledger, card, ticket.ticket_key, recheck=check)
        placements.append(placement)
        legs = tuple(
            grade_leg_settlement(leg_id=leg_id, team="X", teased_spread="7.5",
                                 final_margin=-20)
            for leg_id in placement.leg_ids
        )
        settlements.append(
            settle_ticket(
                placement=placement.to_dict(), legs=legs,
                book_settlement=BOOK_LOSS if index == 0 else BOOK_VOID,
                settled_at=KICKOFF + timedelta(hours=4),
                profit_loss_units=None if index == 0 else 0.0,
            ).to_dict()
        )

    status = season.season_status(2026, placements=ledger.entries(), settlements=settlements)
    assert status["total_losses"] == 1
    assert status["total_voided_or_cancelled"] == 1
    assert status["total_wins"] == 0
    assert status["total_profit_loss_units"] == pytest.approx(-1.0)


def test_external_placements_are_excluded_from_model_figures(season, ledger, card):
    season.record_week(grading_entry(card))
    place(ledger, card, card.selected_tickets[0].ticket_key, recheck=clean_recheck(card))
    unproposed = next(t for t in card.tickets if not t.selected)
    ledger.record(card, unproposed.ticket_key, sportsbook="BookX", american_odds="-110",
                  placed_at=PLACED, recorded_by="operator", designation=EXTERNAL_NON_MODEL)

    status = season.season_status(2026, placements=ledger.entries(), settlements=[])
    assert status["total_placed_tickets"] == 1
    assert status["external_non_model_placements"] == 1
    assert status["total_units_staked"] == 1.0


def test_zero_bet_weeks_still_appear_in_the_derived_view(season, ledger, card):
    season.record_week(grading_entry(card, week=3))
    season.record_week(WeekLedgerEntry(
        season=2026, week=4, recorded_at=GRADED, games_scanned=14,
        qualifying_primary_legs=0, top_four_legs=0, positive_ev_tickets=0,
        proposed_tickets=0, placed_tickets=0, units_staked=0.0,
    ))
    place(ledger, card, card.selected_tickets[0].ticket_key, recheck=clean_recheck(card))

    weeks = season.derive_weeks(2026, placements=ledger.entries(), settlements=[])
    assert [row["week"] for row in weeks] == [3, 4]
    assert weeks[0]["placed_tickets"] == 1
    assert weeks[1]["placed_tickets"] == 0
    assert weeks[1]["qualifying_primary_legs"] == 0

    status = season.season_status(2026, placements=ledger.entries(), settlements=[])
    assert status["weeks_recorded"] == 2
    assert status["weeks_with_zero_placements"] == 1


def test_the_immutable_grading_record_is_never_altered_by_placement(season, ledger, card):
    entry = season.record_week(grading_entry(card))
    place(ledger, card, card.selected_tickets[0].ticket_key, recheck=clean_recheck(card))
    stored = season.latest_per_week(2026)[0]
    assert stored["placed_tickets"] == entry["placed_tickets"] == 0
    assert stored["units_staked"] == 0.0
    # ...while the derived view shows the real activity.
    derived = season.derive_weeks(2026, placements=ledger.entries(), settlements=[])[0]
    assert derived["placed_tickets"] == 1
