"""Price handling: no invented prices, and hypothetical prices can never go live."""

from __future__ import annotations

import pytest
from conftest import stub_leg

from teaser_model_v1.engine.pricing import (
    american_odds_from_profit,
    break_even_probability,
    fair_break_even_profit,
    profit_from_american_odds,
)
from teaser_model_v1.engine.presentation import format_hypothetical_price_note
from teaser_model_v1.engine.tickets import generate_tickets, select_live_tickets
from teaser_model_v1.engine.weekly import construct_week


def legs(n=3, p=0.75):
    return [stub_leg(chr(ord("a") + i), p) for i in range(n)]


def test_no_price_means_no_ev_and_no_placement_eligibility():
    tickets = generate_tickets(legs(), profit_by_size=None)
    assert tickets, "tickets must still be constructed and displayed without a price"
    for ticket in tickets:
        assert ticket.profit is None
        assert ticket.ev is None
        assert ticket.break_even is None
        assert not ticket.is_positive_ev
        assert not ticket.placement_eligible
    assert select_live_tickets(tickets).n_selected == 0


def test_a_fair_break_even_price_is_always_available_without_inventing_a_price():
    tickets = generate_tickets(legs(), profit_by_size=None)
    ticket = tickets[0]
    fair = ticket.fair_break_even_profit
    assert fair > 0
    # By construction, EV at exactly the fair price is zero.
    assert break_even_probability(fair) == pytest.approx(ticket.p_ticket, abs=1e-12)


def test_hypothetical_prices_are_flagged_and_never_placement_eligible():
    tickets = generate_tickets(
        legs(p=0.85),
        {2: 0.9, 3: 2.0},
        price_is_hypothetical=True,
        price_provenance="sensitivity_scenario",
    )
    positives = [t for t in tickets if t.is_positive_ev]
    assert positives, "this scenario should produce positive EV at the hypothetical price"
    for ticket in positives:
        assert ticket.price_is_hypothetical
        assert not ticket.placement_eligible
    assert select_live_tickets(tickets).n_selected == 0


def test_weekly_result_notes_flag_hypothetical_and_missing_prices():
    from conftest import make_leg

    board = [make_leg(f"L{i}", 1.5, 40 + i) for i in range(4)]

    no_price = construct_week(board, None)
    assert any("no teaser price" in n.lower() for n in no_price.notes)

    hypo = construct_week(board, {2: 0.9, 3: 2.0}, price_is_hypothetical=True)
    assert any("hypothetical" in n.lower() for n in hypo.notes)
    assert hypo.n_placed == 0


def test_american_odds_round_trip():
    for odds in (-120, -110, 100, 160, 250, -300):
        profit = profit_from_american_odds(odds)
        assert american_odds_from_profit(profit) == pytest.approx(odds, abs=1e-9)


def test_fair_break_even_profit_is_inverse_of_break_even_probability():
    for p in (0.4, 0.5, 0.55, 0.72, 0.9):
        assert break_even_probability(fair_break_even_profit(p)) == pytest.approx(
            p, abs=1e-12
        )


def test_hypothetical_price_note_is_explicit():
    note = format_hypothetical_price_note(-120)
    assert "HYPOTHETICAL" in note
    assert "-120" in note


def test_impossible_prices_raise():
    with pytest.raises(ValueError):
        break_even_probability(-1.0)
    with pytest.raises(ValueError):
        profit_from_american_odds(0)
