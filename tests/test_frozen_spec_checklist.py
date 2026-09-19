"""The 21 mandated conformance tests for Teaser Model v1.0.

Each test is numbered to match the Phase 1 assignment checklist. These exist to prove the
implementation is faithful to ``TEASER_MODEL_V1_0.md``. If one of them fails, the code is
wrong — never the test, and never the spec.
"""

from __future__ import annotations

import math

import pytest
from conftest import stub_leg, stub_ticket

from teaser_model_v1.engine.geometry import (
    classify_geometry,
    is_primary,
    passes_total_guardrail,
    teased_spread,
)
from teaser_model_v1.engine.constants import Geometry
from teaser_model_v1.engine.legs import build_leg
from teaser_model_v1.engine.presentation import format_probability_pct
from teaser_model_v1.engine.pricing import (
    break_even_probability,
    ev_per_unit,
    profit_from_american_odds,
)
from teaser_model_v1.engine.probability import (
    key_number_bump,
    key_numbers_crossed,
    p_est,
    p_raw,
    sigma,
)
from teaser_model_v1.engine.tickets import (
    generate_tickets,
    rank_tickets,
    select_live_tickets,
    ticket_probability,
)


# ---------------------------------------------------------------------------- 1-4
# The four primary NFL geometries.


def test_01_nfl_dog_plus_1_5_to_plus_7_5_is_primary():
    assert is_primary("NFL", 1.5)
    assert teased_spread(1.5) == pytest.approx(7.5)


def test_02_nfl_dog_plus_2_5_to_plus_8_5_is_primary():
    assert is_primary("NFL", 2.5)
    assert teased_spread(2.5) == pytest.approx(8.5)


def test_03_nfl_favorite_minus_7_5_to_minus_1_5_is_primary():
    assert is_primary("NFL", -7.5)
    assert teased_spread(-7.5) == pytest.approx(-1.5)


def test_04_nfl_favorite_minus_8_5_to_minus_2_5_is_primary():
    assert is_primary("NFL", -8.5)
    assert teased_spread(-8.5) == pytest.approx(-2.5)


# ---------------------------------------------------------------------------- 5-7
# Whole numbers and +3 are secondary.


def test_05_nfl_plus_2_is_secondary_not_primary():
    assert not is_primary("NFL", 2)
    assert classify_geometry("NFL", 2) is Geometry.SECONDARY
    assert build_leg("g1-A", "NFL", "A", 2, 44).secondary_reason == "whole_number_line"


def test_06_nfl_minus_8_is_secondary_not_primary():
    assert not is_primary("NFL", -8)
    assert classify_geometry("NFL", -8) is Geometry.SECONDARY
    assert build_leg("g1-B", "NFL", "B", -8, 44).secondary_reason == "whole_number_line"


@pytest.mark.parametrize("league", ["NFL", "CFB"])
def test_07_plus_3_is_not_primary(league):
    assert not is_primary(league, 3)
    assert not is_primary(league, -3)


# ---------------------------------------------------------------------------- 8-11
# Total guardrails, inclusive.


def test_08_nfl_total_47_qualifies():
    assert passes_total_guardrail("NFL", 47)
    assert build_leg("g2-A", "NFL", "A", 1.5, 47).qualifies_primary


def test_09_nfl_total_47_5_fails():
    assert not passes_total_guardrail("NFL", 47.5)
    assert not build_leg("g2-B", "NFL", "B", 1.5, 47.5).qualifies_primary


def test_10_cfb_total_52_qualifies_for_its_paper_track():
    assert passes_total_guardrail("CFB", 52)
    leg = build_leg("c1-A", "CFB", "A", 1.5, 52)
    assert leg.total_ok
    # College football is paper/research only in its entirety.
    assert leg.geometry is Geometry.SECONDARY
    assert leg.secondary_reason == "cfb_paper_track_primary_shape"


def test_11_cfb_total_52_5_fails():
    assert not passes_total_guardrail("CFB", 52.5)
    assert not build_leg("c1-B", "CFB", "B", 1.5, 52.5).total_ok


# ---------------------------------------------------------------------------- 12
# sigma / P_raw on a hand-checkable example.


def test_12_sigma_and_p_raw_hand_checkable():
    # total = 40  ->  sigma = 0.30 * 40 = 12.0  ->  z = 6 / 12 = 0.5
    # Phi(0.5) = 0.69146246127401310
    assert sigma(40) == pytest.approx(12.0, abs=1e-12)
    assert p_raw(40) == pytest.approx(0.6914624612740131, abs=1e-12)

    # A second, independent hand check: total = 30 -> sigma = 9 -> z = 2/3
    assert sigma(30) == pytest.approx(9.0, abs=1e-12)
    assert p_raw(30) == pytest.approx(0.7475074624530771, abs=1e-12)


# ---------------------------------------------------------------------------- 13
# Key-number bump, NFL and CFB.


def test_13a_all_four_primary_geometries_cross_both_key_numbers():
    for spread in (1.5, 2.5, -7.5, -8.5):
        assert key_numbers_crossed(spread, "NFL") == 2


def test_13b_nfl_bump_values():
    assert key_number_bump("NFL", 2) == pytest.approx(0.07)
    assert key_number_bump("NFL", 1) == pytest.approx(0.04)
    assert key_number_bump("NFL", 0) == pytest.approx(0.00)


def test_13c_cfb_bump_values():
    assert key_number_bump("CFB", 2) == pytest.approx(0.04)
    assert key_number_bump("CFB", 1) == pytest.approx(0.02)
    assert key_number_bump("CFB", 0) == pytest.approx(0.00)


def test_13d_bump_is_applied_to_p_raw():
    # -7.5 crosses both key numbers.
    assert p_est("NFL", -7.5, 40) == pytest.approx(p_raw(40) + 0.07, abs=1e-12)
    assert p_est("CFB", -7.5, 40) == pytest.approx(p_raw(40) + 0.04, abs=1e-12)

    # -2 teased to +4 newly covers margins in (-4, 2]: crosses 3 only, not 7.
    assert key_numbers_crossed(-2, "NFL") == 1
    assert p_est("NFL", -2, 40) == pytest.approx(p_raw(40) + 0.04, abs=1e-12)
    assert p_est("CFB", -2, 40) == pytest.approx(p_raw(40) + 0.02, abs=1e-12)

    # +10 teased to +16 newly covers margins in (-16, -10]: crosses neither.
    assert key_numbers_crossed(10, "NFL") == 0
    assert p_est("NFL", 10, 40) == pytest.approx(p_raw(40), abs=1e-12)


# ---------------------------------------------------------------------------- 14
# Ticket probability is the product of leg P_est values.


def test_14_ticket_probability_multiplies_legs():
    assert ticket_probability([0.7, 0.8]) == pytest.approx(0.56, abs=1e-12)
    assert ticket_probability([0.7, 0.8, 0.5]) == pytest.approx(0.28, abs=1e-12)

    legs = [stub_leg("a", 0.72), stub_leg("b", 0.66), stub_leg("c", 0.61)]
    tickets = generate_tickets(legs)
    three = next(t for t in tickets if t.n_legs == 3)
    assert three.p_ticket == pytest.approx(0.72 * 0.66 * 0.61, abs=1e-12)


# ---------------------------------------------------------------------------- 15
# break_even = 1 / (1 + profit)


def test_15_break_even_from_price():
    profit = profit_from_american_odds(-120)  # 100/120
    assert profit == pytest.approx(5 / 6, abs=1e-12)
    assert break_even_probability(profit) == pytest.approx(6 / 11, abs=1e-12)

    # Even money: profit 1.0 -> break-even 0.5
    assert break_even_probability(1.0) == pytest.approx(0.5, abs=1e-12)
    # +160 -> profit 1.6 -> 1/2.6
    assert break_even_probability(profit_from_american_odds(160)) == pytest.approx(
        1 / 2.6, abs=1e-12
    )


# ---------------------------------------------------------------------------- 16
# EV_per_unit = P_ticket * profit - (1 - P_ticket)


def test_16_ev_calculation():
    assert ev_per_unit(0.6, 5 / 6) == pytest.approx(0.1, abs=1e-12)
    assert ev_per_unit(0.5, 1.0) == pytest.approx(0.0, abs=1e-12)
    assert ev_per_unit(0.4, 5 / 6) == pytest.approx(0.4 * (5 / 6) - 0.6, abs=1e-12)

    # EV is zero exactly at the break-even probability.
    profit = 0.8333333333333333
    assert ev_per_unit(break_even_probability(profit), profit) == pytest.approx(
        0.0, abs=1e-12
    )


# ---------------------------------------------------------------------------- 17
# Negative-EV tickets stay visible but are not placement-eligible.


def test_17_negative_ev_tickets_visible_but_not_placement_eligible():
    legs = [stub_leg("a", 0.55), stub_leg("b", 0.55), stub_leg("c", 0.55)]
    tickets = generate_tickets(legs, {2: 5 / 6, 3: 1.8})

    assert len(tickets) == 4  # C(3,2) + C(3,3)
    negatives = [t for t in tickets if t.ev is not None and t.ev <= 0]
    assert negatives, "expected at least one negative-EV ticket in this scenario"

    for ticket in negatives:
        assert ticket in tickets  # still displayed / logged
        assert not ticket.placement_eligible

    assert select_live_tickets(tickets).n_selected == 0


def test_17b_zero_ev_is_not_positive_ev():
    ticket = stub_ticket(ev=0.0, n_legs=2)
    assert not ticket.is_positive_ev
    assert not ticket.placement_eligible


# ---------------------------------------------------------------------------- 18
# Exposure cap: never more than 2 units on one leg.


def test_18_exposure_cap_never_exceeded():
    legs = [stub_leg(name, 0.75) for name in ("a", "b", "c", "d")]
    tickets = generate_tickets(legs, {2: 0.9, 3: 2.0})
    assert all(t.placement_eligible for t in tickets)

    result = select_live_tickets(tickets)

    assert result.exposure, "expected some tickets to be selected"
    assert max(result.exposure.values()) <= 2
    for leg_id, units in result.exposure.items():
        assert units <= 2, f"{leg_id} carried {units} units"

    # And the exposure dict really is the count of selected tickets containing each leg.
    for leg_id, units in result.exposure.items():
        assert units == sum(1 for t in result.selected if leg_id in t.leg_ids)


def test_18b_a_leg_appearing_in_many_top_tickets_is_capped_at_two():
    # Leg "a" is in every 2-team ticket below; it must still stop at 2 units.
    a, b, c, d = (stub_leg(n, 0.9) for n in ("a", "b", "c", "d"))
    tickets = generate_tickets([a, b, c, d], {2: 0.9, 3: 2.0}, ticket_sizes=(2,))
    result = select_live_tickets(tickets)
    assert result.exposure["a"] == 2


# ---------------------------------------------------------------------------- 19
# Greedy selection walks in descending precise EV order.


def test_19_greedy_selection_follows_ev_order():
    high = stub_ticket(ev=0.30, n_legs=2, prefix="h")
    mid = stub_ticket(ev=0.20, n_legs=2, prefix="m")
    low = stub_ticket(ev=0.10, n_legs=2, prefix="l")

    result = select_live_tickets([low, high, mid])
    assert [t.ev for t in result.selected] == [0.30, 0.20, 0.10]


def test_19b_greedy_skips_then_continues_down_the_list():
    # Three tickets all sharing leg "a": the top two fit, the third is skipped for
    # exposure, and a fourth ticket not containing "a" is still picked up afterwards.
    a = stub_leg("a", 0.8)
    b, c, d, e, f = (stub_leg(n, 0.8) for n in ("b", "c", "d", "e", "f"))

    from teaser_model_v1.engine.tickets import Ticket

    def tk(legs, ev):
        return Ticket(legs=tuple(legs), p_ticket=0.64, profit=0.9, break_even=0.5, ev=ev)

    t1 = tk([a, b], 0.40)
    t2 = tk([a, c], 0.30)
    t3 = tk([a, d], 0.20)  # must be skipped: "a" already at 2 units
    t4 = tk([e, f], 0.10)  # must still be selected after the skip

    result = select_live_tickets([t1, t2, t3, t4])
    assert list(result.selected) == [t1, t2, t4]
    assert list(result.skipped) == [t3]
    assert result.exposure["a"] == 2


# ---------------------------------------------------------------------------- 20
# Exact internal EV breaks displayed-rounding ties BEFORE leg count.


def test_20_exact_ev_breaks_displayed_rounding_ties_before_leg_count():
    # Both EVs display as 0.12 at two decimal places, but the 3-leg ticket is precisely
    # higher. Precise EV must win; the fewer-legs rule must NOT be reached.
    three_leg = stub_ticket(ev=0.1234567, n_legs=3, prefix="x")
    two_leg = stub_ticket(ev=0.1234566, n_legs=2, prefix="y")

    assert round(three_leg.ev, 2) == round(two_leg.ev, 2)  # displayed values tie
    assert three_leg.ev > two_leg.ev  # precise values do not

    ranked = rank_tickets([two_leg, three_leg])
    assert ranked[0] is three_leg
    assert ranked[1] is two_leg

    # And selection follows that order.
    assert list(select_live_tickets([two_leg, three_leg]).selected) == [
        three_leg,
        two_leg,
    ]


# ---------------------------------------------------------------------------- 21
# If still truly tied, fewer legs wins.


def test_21_true_tie_prefers_fewer_legs():
    three_leg = stub_ticket(ev=0.15, n_legs=3, prefix="x")
    two_leg = stub_ticket(ev=0.15, n_legs=2, prefix="y")

    assert three_leg.ev == two_leg.ev  # truly tied, not merely rounding-tied

    ranked = rank_tickets([three_leg, two_leg])
    assert ranked[0] is two_leg
    assert ranked[1] is three_leg

    # Order of the input must not matter.
    assert rank_tickets([two_leg, three_leg])[0] is two_leg


def test_21b_probability_display_is_whole_percent_and_labelled():
    # Rounding is presentation only; it must never feed back into ranking.
    assert format_probability_pct(0.6914624612740131) == "69%"
    assert format_probability_pct(0.7614624612740131) == "76%"
    assert not math.isclose(0.69, 0.6914624612740131)
