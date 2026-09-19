"""Weekly construction: eligibility, top-four, combination set, and the weekly counts."""

from __future__ import annotations

import pytest
from conftest import make_leg

from teaser_model_v1.engine.legs import eligible_primary_nfl_legs
from teaser_model_v1.engine.tickets import generate_tickets, select_top_legs
from teaser_model_v1.engine.weekly import construct_week


def board(spreads_totals, league="NFL"):
    return [
        make_leg(f"L{i}", spread, total, league=league)
        for i, (spread, total) in enumerate(spreads_totals)
    ]


def test_eligibility_requires_primary_geometry_and_guardrail():
    legs = board(
        [
            (1.5, 40),  # eligible
            (2.5, 47),  # eligible (boundary)
            (-7.5, 47.5),  # total too high
            (2.0, 40),  # whole number -> secondary
            (3.5, 40),  # not primary
            (-8.5, 44),  # eligible
        ]
    )
    eligible = eligible_primary_nfl_legs(legs)
    assert {leg.leg_id for leg in eligible} == {"L0", "L1", "L5"}


def test_cfb_legs_never_enter_the_live_primary_pool():
    legs = board([(1.5, 40), (-7.5, 44)], league="CFB")
    assert eligible_primary_nfl_legs(legs) == []


def test_top_four_selection_is_by_p_est_descending():
    # Lower total -> smaller sigma -> higher P_raw. All five cross both key numbers.
    legs = board([(1.5, 46), (1.5, 44), (1.5, 42), (1.5, 40), (1.5, 38)])
    top = select_top_legs(eligible_primary_nfl_legs(legs))

    assert len(top) == 4
    assert [leg.leg_id for leg in top] == ["L4", "L3", "L2", "L1"]
    assert [leg.p_est for leg in top] == sorted(
        (leg.p_est for leg in top), reverse=True
    )


def test_fewer_than_two_qualifying_legs_means_no_ticket():
    result = construct_week(board([(1.5, 40), (3.5, 40), (2.0, 40)]), {2: 0.9, 3: 2.0})
    assert result.n_qualifying_primary_legs == 1
    assert result.tickets == ()
    assert result.n_placed == 0
    assert any("no primary ticket" in note.lower() for note in result.notes)


def test_zero_qualifying_legs_is_recorded_not_dropped():
    result = construct_week(board([(3.5, 40), (-3.0, 44)]), {2: 0.9, 3: 2.0})
    assert result.n_qualifying_primary_legs == 0
    assert result.counts()["n_qualifying_primary_legs"] == 0
    assert result.n_tickets_constructed == 0


def test_all_two_and_three_team_combinations_from_the_top_four():
    legs = board([(1.5, 40), (2.5, 41), (-7.5, 42), (-8.5, 43), (1.5, 44)])
    result = construct_week(legs, {2: 0.9, 3: 2.0})

    assert len(result.top_legs) == 4
    assert result.n_tickets_constructed == 10  # C(4,2)=6 plus C(4,3)=4
    assert sum(1 for t in result.tickets if t.n_legs == 2) == 6
    assert sum(1 for t in result.tickets if t.n_legs == 3) == 4

    # Only the top four legs may appear on a ticket.
    top_ids = {leg.leg_id for leg in result.top_legs}
    for ticket in result.tickets:
        assert set(ticket.leg_ids) <= top_ids


def test_exactly_two_qualifying_legs_yields_one_two_team_ticket():
    result = construct_week(board([(1.5, 40), (2.5, 41)]), {2: 0.9, 3: 2.0})
    assert result.n_tickets_constructed == 1
    assert result.tickets[0].n_legs == 2


def test_exactly_three_qualifying_legs_yields_four_tickets():
    result = construct_week(board([(1.5, 40), (2.5, 41), (-7.5, 42)]), {2: 0.9, 3: 2.0})
    assert result.n_tickets_constructed == 4


def test_weekly_counts_are_complete():
    legs = board([(1.5, 38), (2.5, 39), (-7.5, 40), (-8.5, 41)])
    result = construct_week(legs, {2: 0.9, 3: 2.0}, season=2025, week=3)
    counts = result.counts()
    assert set(counts) == {
        "season",
        "week",
        "n_qualifying_primary_legs",
        "n_tickets_constructed",
        "n_positive_ev_tickets",
        "n_placed",
    }
    assert counts["season"] == 2025 and counts["week"] == 3
    assert counts["n_placed"] <= counts["n_positive_ev_tickets"]
