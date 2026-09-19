"""Phase 4: grading-time board, ticket construction, selection and eligibility."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from teaser_model_v1.engine.constants import MAX_UNITS_PER_LEG_PER_WEEK
from teaser_model_v1.live.card import (
    NO_TICKET_MESSAGE,
    STATUS_NO_TICKET,
    STATUS_PROPOSED,
    UNAVAILABLE,
    exposure_violations,
    grade_week,
    ticket_key_for,
)
from teaser_model_v1.live.schemas import (
    MarketQuote,
    MarketSnapshot,
    TeaserPriceQuote,
    TeaserPriceSnapshot,
)

EASTERN = timezone(timedelta(hours=-4))
KICKOFF = datetime(2026, 9, 20, 13, 0, tzinfo=EASTERN)
CAPTURED = datetime(2026, 9, 19, 10, 0, tzinfo=EASTERN)


def board(rows, captured_at=CAPTURED):
    """rows: (away, home, team, spread, total)."""
    quotes = tuple(
        MarketQuote(
            game_id=f"2026_03_{away}_{home}", season=2026, week=3, kickoff=KICKOFF,
            home_team=home, away_team=away, team=team, spread=spread, total=total,
            sportsbook="BookX", captured_at=captured_at, ingestion_method="test",
        )
        for away, home, team, spread, total in rows
    )
    return MarketSnapshot(
        season=2026, week=3, captured_at=captured_at, sportsbook="BookX",
        ingestion_method="test", quotes=quotes,
    )


def prices(two=-120, three=140, captured_at=CAPTURED, sizes=(2, 3)):
    quotes = []
    if 2 in sizes:
        quotes.append(TeaserPriceQuote(ticket_size=2, sportsbook="BookX",
                                       captured_at=captured_at, american_odds=two))
    if 3 in sizes:
        quotes.append(TeaserPriceQuote(ticket_size=3, sportsbook="BookX",
                                       captured_at=captured_at, american_odds=three))
    return TeaserPriceSnapshot(season=2026, week=3, captured_at=captured_at,
                               sportsbook="BookX", quotes=tuple(quotes))


FIVE_PRIMARY = [
    ("BUF", "MIA", "MIA", "2.5", "40.5"),
    ("NYJ", "NE", "NE", "1.5", "42.5"),
    ("DAL", "PHI", "PHI", "-7.5", "43.5"),
    ("GB", "CHI", "CHI", "2.5", "45.5"),
    ("SF", "SEA", "SEA", "-8.5", "46.5"),
]


# ---- 7-10. geometry and guardrail classification ---------------------------------------


@pytest.mark.parametrize("spread", ["1.5", "2.5", "-7.5", "-8.5"])
def test_the_four_primary_shapes_qualify(spread):
    card = grade_week(board([("BUF", "MIA", "MIA", spread, "44.5")]), prices())
    assert card.n_qualifying == 1
    assert card.qualifying_legs[0].geometry_class == "PRIMARY"
    assert card.qualifying_legs[0].track == "LIVE"


@pytest.mark.parametrize("spread", ["2.0", "-8.0", "3.0", "-3.0", "1.0"])
def test_whole_number_lines_are_not_primary(spread):
    card = grade_week(board([("BUF", "MIA", "MIA", spread, "44.5")]), prices())
    assert card.n_qualifying == 0


@pytest.mark.parametrize("spread", ["3.5", "-4.5", "6.5", "-9.5"])
def test_other_half_point_shapes_are_not_primary(spread):
    assert grade_week(board([("BUF", "MIA", "MIA", spread, "44.5")]), prices()).n_qualifying == 0


def test_total_47_qualifies_and_47_5_fails():
    assert grade_week(board([("BUF", "MIA", "MIA", "2.5", "47")]), prices()).n_qualifying == 1
    assert grade_week(board([("BUF", "MIA", "MIA", "2.5", "47.5")]), prices()).n_qualifying == 0


def test_a_primary_shape_over_the_cap_is_excluded_but_the_week_still_grades():
    rows = FIVE_PRIMARY + [("KC", "DEN", "DEN", "2.5", "49.5")]
    card = grade_week(board(rows), prices())
    assert card.n_qualifying == 5
    assert "DEN" not in {leg.team for leg in card.qualifying_legs}


# ---- 11. top-four ranking ---------------------------------------------------------------


def test_top_four_is_by_p_est_descending():
    card = grade_week(board(FIVE_PRIMARY), prices())
    assert [leg.rank for leg in card.qualifying_legs] == [1, 2, 3, 4, 5]
    p_values = [leg.p_est for leg in card.qualifying_legs]
    assert p_values == sorted(p_values, reverse=True)
    assert len(card.top_legs) == 4
    # Lowest total wins: SEA at 46.5 is the one dropped.
    assert "SEA" not in {leg.team for leg in card.top_legs}


def test_displayed_probability_is_whole_percent():
    card = grade_week(board(FIVE_PRIMARY), prices())
    for leg in card.qualifying_legs:
        assert leg.displayed_probability.endswith("%")
        assert "." not in leg.displayed_probability


# ---- 12. combination counts -------------------------------------------------------------


def test_four_legs_give_six_two_team_and_four_three_team():
    card = grade_week(board(FIVE_PRIMARY), prices())
    assert sum(1 for t in card.tickets if t.n_legs == 2) == 6
    assert sum(1 for t in card.tickets if t.n_legs == 3) == 4


def test_two_legs_give_exactly_one_ticket():
    card = grade_week(board(FIVE_PRIMARY[:2]), prices())
    assert len(card.tickets) == 1 and card.tickets[0].n_legs == 2


def test_fewer_than_two_legs_gives_no_constructible_ticket():
    card = grade_week(board(FIVE_PRIMARY[:1]), prices())
    assert card.tickets == ()
    assert card.status == STATUS_NO_TICKET
    assert NO_TICKET_MESSAGE in card.notes
    assert card.n_qualifying == 1  # still recorded


def test_zero_qualifying_legs_is_still_a_graded_week():
    card = grade_week(board([("BUF", "MIA", "MIA", "3.5", "44.5")]), prices())
    assert card.n_qualifying == 0
    assert card.status == STATUS_NO_TICKET
    assert card.games_scanned == 1


# ---- 13-15. break-even, EV, eligibility -------------------------------------------------


def test_break_even_and_ev_come_from_the_real_price():
    card = grade_week(board(FIVE_PRIMARY), prices(two=-120))
    ticket = next(t for t in card.tickets if t.n_legs == 2)
    # -120 -> profit 100/120; break-even = 1/(1+profit) = 120/220
    assert float(ticket.break_even) == pytest.approx(120 / 220)
    expected_ev = ticket.p_ticket * (100 / 120) - (1 - ticket.p_ticket)
    assert float(ticket.ev_per_unit) == pytest.approx(expected_ev)


def test_negative_ev_tickets_are_displayed_but_never_selected():
    card = grade_week(board(FIVE_PRIMARY), prices(two=-200, three=100))
    assert card.tickets, "tickets must still be displayed"
    assert all(t.status == "NEGATIVE_EV" for t in card.tickets)
    assert card.selected_ticket_keys == ()


def test_missing_price_makes_ev_unavailable_and_blocks_placement():
    card = grade_week(board(FIVE_PRIMARY), prices(sizes=(2,)))
    three = [t for t in card.tickets if t.n_legs == 3]
    assert three, "3-team tickets are still constructed and displayed"
    for ticket in three:
        assert ticket.break_even == UNAVAILABLE
        assert ticket.ev_per_unit == UNAVAILABLE
        assert "NO_PRICE" in ticket.status
        assert not ticket.selected


def test_no_price_snapshot_at_all_blocks_every_placement():
    card = grade_week(board(FIVE_PRIMARY), None)
    assert card.tickets
    assert card.selected_ticket_keys == ()
    assert all(t.ev_per_unit == UNAVAILABLE for t in card.tickets)
    assert card.price_snapshot_id == ""


# ---- 16-17. greedy exposure cap ---------------------------------------------------------


def test_selection_respects_the_two_unit_cap():
    card = grade_week(board(FIVE_PRIMARY), prices(two=-110, three=180))
    assert card.exposure
    assert max(card.exposure.values()) <= MAX_UNITS_PER_LEG_PER_WEEK
    assert exposure_violations(card.exposure) == {}


def test_selection_walks_in_descending_ev_order():
    card = grade_week(board(FIVE_PRIMARY), prices(two=-110, three=180))
    selected = [t for t in card.tickets if t.selected]
    evs = [float(t.ev_per_unit) for t in selected]
    assert evs == sorted(evs, reverse=True)


def test_every_selected_ticket_is_positive_ev():
    card = grade_week(board(FIVE_PRIMARY), prices(two=-110, three=180))
    assert all(t.status == "POSITIVE_EV" for t in card.selected_tickets)


def test_exposure_matches_the_selected_tickets():
    card = grade_week(board(FIVE_PRIMARY), prices(two=-110, three=180))
    for leg_id, units in card.exposure.items():
        assert units == sum(1 for t in card.selected_tickets if leg_id in t.leg_ids)


# ---- card identity and provenance -------------------------------------------------------


def test_card_is_proposed_not_placed():
    card = grade_week(board(FIVE_PRIMARY), prices())
    assert card.status == STATUS_PROPOSED
    assert "PROPOSED" in card.to_dict()["placement_status"]
    assert "not been wagered" in card.to_dict()["placement_status"].lower() or \
           "nothing has been wagered" in card.to_dict()["placement_status"].lower()


def test_card_records_both_snapshot_ids():
    market, price = board(FIVE_PRIMARY), prices()
    card = grade_week(market, price)
    assert card.market_snapshot_id == market.snapshot_id
    assert card.price_snapshot_id == price.snapshot_id
    for leg in card.qualifying_legs:
        assert leg.market_snapshot_id == market.snapshot_id


def test_card_id_is_content_derived():
    market, price = board(FIVE_PRIMARY), prices()
    first = grade_week(market, price, graded_at=CAPTURED)
    second = grade_week(market, price, graded_at=CAPTURED)
    assert first.card_id == second.card_id


def test_ticket_key_is_order_independent():
    assert ticket_key_for(["b", "a"]) == ticket_key_for(["a", "b"])


def test_mismatched_price_week_is_refused():
    wrong = TeaserPriceSnapshot(
        season=2026, week=4, captured_at=CAPTURED, sportsbook="BookX",
        quotes=(TeaserPriceQuote(ticket_size=2, sportsbook="BookX",
                                 captured_at=CAPTURED, american_odds=-120),),
    )
    with pytest.raises(ValueError, match="different season/week"):
        grade_week(board(FIVE_PRIMARY), wrong)
