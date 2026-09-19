"""Phase 3: price conversion, fair price, price-dependent selection, frontier, bootstrap."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from teaser_model_v1.analysis.pricing_sensitivity import (
    DEFAULT_SEED,
    GRID_2TEAM,
    GRID_3TEAM,
    HYPOTHETICAL_LABEL,
    breakeven_frontier,
    fair_price_distribution,
    fair_price_rows,
    prepare_board,
    run_scenario,
    scenario_at_american,
    week_cluster_bootstrap_roi,
)
from teaser_model_v1.engine.pricing import (
    american_odds_from_profit,
    break_even_probability,
    ev_per_unit,
    fair_break_even_profit,
    profit_from_american_odds,
)
from teaser_model_v1.engine.tickets import (
    Ticket,
    _is_placement_eligible,
    generate_tickets,
    select_live_tickets,
)


# ---------------------------------------------------------------------------------------
# Price conversion.
# ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "american,profit",
    [(-100, 1.0), (100, 1.0), (-110, 100 / 110), (-120, 100 / 120),
     (-150, 100 / 150), (120, 1.2), (160, 1.6), (180, 1.8)],
)
def test_american_to_profit(american, profit):
    assert profit_from_american_odds(american) == pytest.approx(profit)


@pytest.mark.parametrize("american", [-110, -120, -130, -140, -150,
                                      100, 120, 140, 160, 180, 250])
def test_american_round_trip(american):
    profit = profit_from_american_odds(american)
    assert american_odds_from_profit(profit) == pytest.approx(american, abs=1e-9)


def test_plus_and_minus_100_are_the_same_price():
    """Even money has two spellings; the conversion canonicalises to +100.

    This is a property of the notation, not a rounding artifact, and it is why -100 is
    excluded from the round-trip parametrisation above.
    """
    assert profit_from_american_odds(-100) == pytest.approx(1.0)
    assert profit_from_american_odds(100) == pytest.approx(1.0)
    assert american_odds_from_profit(1.0) == pytest.approx(100.0)


def test_decimal_odds_is_one_plus_net_profit():
    for american in (-110, -130, 140, 180):
        profit = profit_from_american_odds(american)
        assert (1.0 + profit) == pytest.approx(1.0 + profit)
        # -110 pays 1.909 decimal.
    assert 1.0 + profit_from_american_odds(-110) == pytest.approx(1.9090909, abs=1e-6)
    assert 1.0 + profit_from_american_odds(160) == pytest.approx(2.6)


def test_grids_are_the_declared_analytical_points():
    assert GRID_2TEAM == (-100, -110, -120, -130, -140, -150)
    assert GRID_3TEAM == (100, 110, 120, 130, 140, 150, 160, 170, 180)
    assert "HYPOTHETICAL" in HYPOTHETICAL_LABEL
    assert "not a backtested sportsbook return" in HYPOTHETICAL_LABEL


# ---------------------------------------------------------------------------------------
# Fair price.
# ---------------------------------------------------------------------------------------


def test_fair_profit_is_the_inverse_odds_of_p_ticket():
    assert fair_break_even_profit(0.5) == pytest.approx(1.0)
    assert fair_break_even_profit(0.75) == pytest.approx(1 / 3)
    assert fair_break_even_profit(0.4) == pytest.approx(1.5)


def test_break_even_at_the_fair_price_is_p_ticket_itself():
    for p in (0.35, 0.43, 0.5, 0.57, 0.62):
        assert break_even_probability(fair_break_even_profit(p)) == pytest.approx(p)


def test_ev_is_exactly_zero_at_the_fair_price():
    for p in (0.40, 0.5654, 0.73):
        assert ev_per_unit(p, fair_break_even_profit(p)) == pytest.approx(0.0, abs=1e-12)


def test_fair_price_rows_are_internally_consistent():
    tickets = pd.DataFrame({"n_legs": [2, 3], "predicted_p_ticket": [0.5654, 0.4265]})
    priced = fair_price_rows(tickets)
    assert priced["fair_decimal_odds"].iloc[0] == pytest.approx(
        1.0 + priced["fair_profit"].iloc[0]
    )
    assert priced["break_even_probability"].iloc[0] == pytest.approx(0.5654)
    # A 2-team ticket around 56.5% is fair near -130.
    assert priced["fair_american_odds"].iloc[0] == pytest.approx(-130.1, abs=1.0)
    # A 3-team ticket around 42.7% is fair near +134.
    assert priced["fair_american_odds"].iloc[1] == pytest.approx(134.4, abs=1.0)


def test_fair_price_distribution_quantiles():
    tickets = pd.DataFrame({"n_legs": [2] * 5,
                            "predicted_p_ticket": [0.50, 0.55, 0.60, 0.65, 0.70]})
    table = fair_price_distribution(tickets, "t")
    row = table.iloc[0]
    assert row["n_tickets"] == 5
    assert row["p_ticket_median"] == pytest.approx(0.60)
    # Higher P_ticket means a shorter fair price, so the min profit pairs with max P.
    assert row["fair_profit_max"] == pytest.approx(1.0)
    assert row["fair_profit_min"] == pytest.approx((1 - 0.70) / 0.70)


# ---------------------------------------------------------------------------------------
# Positive-EV classification at the boundary.
# ---------------------------------------------------------------------------------------


def make_ticket(p, profit, n_legs=2, hypothetical=True):
    from conftest import stub_leg

    legs = tuple(stub_leg(f"L{i}", p ** (1 / n_legs)) for i in range(n_legs))
    return Ticket(
        legs=legs, p_ticket=p, profit=profit,
        break_even=break_even_probability(profit),
        ev=ev_per_unit(p, profit), price_is_hypothetical=hypothetical,
    )


def test_exact_zero_ev_is_not_positive_ev():
    p = 0.5654
    ticket = make_ticket(p, fair_break_even_profit(p))
    assert ticket.ev == pytest.approx(0.0, abs=1e-15)
    assert not ticket.is_positive_ev
    assert not ticket.placement_eligible


def test_just_above_and_below_the_fair_price():
    p = 0.5654
    fair = fair_break_even_profit(p)
    assert make_ticket(p, fair + 1e-6).is_positive_ev
    assert not make_ticket(p, fair - 1e-6).is_positive_ev


def test_a_hypothetical_price_never_confers_placement_eligibility():
    ticket = make_ticket(0.60, 1.0, hypothetical=True)
    assert ticket.is_positive_ev
    assert not ticket.placement_eligible


def test_the_default_selection_predicate_is_still_the_frozen_one():
    """The research hook must not have changed live behaviour."""
    hypothetical = make_ticket(0.60, 1.0, hypothetical=True)
    real = make_ticket(0.60, 1.0, hypothetical=False)
    assert select_live_tickets([hypothetical]).n_selected == 0
    assert select_live_tickets([real]).n_selected == 1
    assert _is_placement_eligible(real) and not _is_placement_eligible(hypothetical)


# ---------------------------------------------------------------------------------------
# Greedy under mixed 2-team / 3-team prices.
# ---------------------------------------------------------------------------------------


def legs_frame(rows):
    """rows: (leg_id, week, p_est_driver_total, won, side)."""
    return pd.DataFrame(
        [
            {
                "leg_id": leg_id,
                "league": "NFL",
                "team": leg_id,
                "season": 2020,
                "week": week,
                "game_id": f"g-{leg_id}",
                "archived_reference_line": 2.5,
                "game_total": total,
                "won": won,
                "side_class": side,
            }
            for leg_id, week, total, won, side in rows
        ]
    )


@pytest.fixture
def four_leg_week():
    return legs_frame(
        [
            ("a", 1, 38.0, 1, "DOG"),
            ("b", 1, 40.0, 1, "DOG"),
            ("c", 1, 42.0, 1, "FAVORITE"),
            ("d", 1, 44.0, 0, "FAVORITE"),
        ]
    )


def test_ticket_size_ranking_flips_with_the_price_pair(four_leg_week):
    """A 3-team ticket can outrank a 2-team ticket, or not, depending on the prices."""
    board = prepare_board(four_leg_week)

    cheap_three = run_scenario(
        four_leg_week,
        {2: profit_from_american_odds(-150), 3: profit_from_american_odds(180)},
        board=board,
    )
    dear_three = run_scenario(
        four_leg_week,
        {2: profit_from_american_odds(-100), 3: profit_from_american_odds(100)},
        board=board,
    )

    first_cheap = cheap_three.selected.iloc[0]["n_legs"]
    first_dear = dear_three.selected.iloc[0]["n_legs"]
    assert first_cheap == 3, "a generous 3-team price should top the EV ranking"
    assert first_dear == 2, "a poor 3-team price should drop it below the 2-team tickets"


def test_exposure_cap_binds_in_a_four_leg_week(four_leg_week):
    result = scenario_at_american(four_leg_week, american_2team=-110)
    assert result.weekly["max_leg_exposure"].max() <= 2
    # Greedy takes (a,b), (a,c), (b,c); every ticket containing d is then skipped.
    chosen = set(result.selected["leg_ids"])
    assert chosen == {"a|b", "a|c", "b|c"}


def test_flat_control_keeps_everything_the_cap_skips(four_leg_week):
    frozen = scenario_at_american(four_leg_week, american_2team=-110)
    flat = scenario_at_american(four_leg_week, american_2team=-110, flat=True)
    assert len(flat.selected) == 6      # all C(4,2) pairs are positive EV here
    assert len(frozen.selected) == 3
    assert set(frozen.selected["leg_ids"]) < set(flat.selected["leg_ids"])


def test_price_changes_the_selected_set(four_leg_week):
    generous = scenario_at_american(four_leg_week, american_2team=-100)
    punitive = scenario_at_american(four_leg_week, american_2team=-150)
    assert len(generous.selected) >= len(punitive.selected)
    assert generous.summary()["eligible_positive_ev_tickets"] >= punitive.summary()[
        "eligible_positive_ev_tickets"
    ]


def test_unpriced_ticket_size_is_never_selected(four_leg_week):
    """Pricing only 2-team leaves 3-team unpriced, hence never positive EV."""
    result = run_scenario(four_leg_week, {2: profit_from_american_odds(-110)})
    assert set(result.selected["n_legs"]) == {2}


def test_scenario_profit_and_loss_arithmetic(four_leg_week):
    result = scenario_at_american(four_leg_week, american_2team=-110)
    profit = profit_from_american_odds(-110)
    summary = result.summary()
    # a, b, c all won; d lost. Selected are ab, ac, bc -> all three win.
    assert summary["wins"] == 3 and summary["losses"] == 0
    assert summary["hypothetical_profit_loss"] == pytest.approx(3 * profit)
    assert summary["hypothetical_roi"] == pytest.approx(profit)


def test_a_week_with_one_qualifying_leg_constructs_nothing():
    frame = legs_frame([("a", 1, 40.0, 1, "DOG")])
    result = scenario_at_american(frame, american_2team=-110)
    assert result.selected.empty
    assert result.weekly.iloc[0]["n_tickets"] == 0
    assert result.summary()["zero_bet_weeks"] == 1


def test_prepared_board_matches_a_direct_run(four_leg_week):
    board = prepare_board(four_leg_week)
    direct = scenario_at_american(four_leg_week, american_2team=-120).summary()
    cached = scenario_at_american(four_leg_week, american_2team=-120,
                                  board=board).summary()
    assert direct == cached


# ---------------------------------------------------------------------------------------
# Break-even frontier.
# ---------------------------------------------------------------------------------------


@pytest.fixture
def frontier_board():
    rows = []
    for week in range(1, 13):
        rows.append((f"w{week}a", week, 40.0, 1 if week % 3 else 0, "DOG"))
        rows.append((f"w{week}b", week, 42.0, 1 if week % 2 else 0, "DOG"))
    return legs_frame(rows)


def test_frontier_is_reproducible(frontier_board):
    first = breakeven_frontier(frontier_board, 2, block="t", step=0.02)
    second = breakeven_frontier(frontier_board, 2, block="t", step=0.02)
    assert first.crossing_profit == second.crossing_profit
    assert first.tickets_at_crossing == second.tickets_at_crossing
    pd.testing.assert_frame_equal(first.curve, second.curve)


def test_frontier_crossing_gives_non_negative_profit(frontier_board):
    frontier = breakeven_frontier(frontier_board, 2, block="t", step=0.02)
    assert frontier.crossing_profit is not None
    at_crossing = run_scenario(
        frontier_board, {2: frontier.crossing_profit}
    ).summary()
    assert at_crossing["hypothetical_profit_loss"] >= -1e-9
    just_below = run_scenario(
        frontier_board, {2: frontier.crossing_profit - 0.02}
    ).summary()
    assert (
        just_below["hypothetical_profit_loss"] < 0
        or just_below["tickets_selected"] == 0
    )


def test_frontier_curve_is_monotone_in_units_of_price(frontier_board):
    """A better payout can only make more tickets positive EV, never fewer."""
    frontier = breakeven_frontier(frontier_board, 2, block="t", step=0.05)
    counts = frontier.curve["tickets_selected"].to_numpy()
    assert (np.diff(counts) >= 0).all()


def test_frontier_reports_when_nothing_ever_breaks_even():
    """All legs lose: no price in range can produce non-negative profit."""
    rows = []
    for week in range(1, 6):
        rows.append((f"w{week}a", week, 40.0, 0, "DOG"))
        rows.append((f"w{week}b", week, 42.0, 0, "DOG"))
    frontier = breakeven_frontier(legs_frame(rows), 2, block="t", step=0.1)
    assert frontier.crossing_profit is None
    assert "negative" in frontier.note.lower()


def test_model_implied_fair_and_historical_breakeven_are_distinct_objects(frontier_board):
    """They answer different questions and must not be conflated."""
    tickets = pd.DataFrame({"n_legs": [2], "predicted_p_ticket": [0.5654]})
    model_implied = fair_price_rows(tickets)["fair_american_odds"].iloc[0]
    historical = breakeven_frontier(frontier_board, 2, block="t", step=0.02)
    assert historical.crossing_american is not None
    # Nothing forces them to agree; the test simply pins that both exist separately.
    assert isinstance(model_implied, float)
    assert isinstance(historical.crossing_american, float)


# ---------------------------------------------------------------------------------------
# Bootstrap.
# ---------------------------------------------------------------------------------------


def weekly_frame(n_weeks, pl_per_week=0.5, units_per_week=2.0):
    """Weeks with varied P/L, so the bootstrap distribution is not degenerate.

    A frame where every week carries the same magnitude produces a discrete ROI
    distribution whose percentiles can coincide across seeds; that would make a
    seed-sensitivity test vacuous rather than meaningful.
    """
    rng = np.random.default_rng(12345)
    jitter = rng.normal(0.0, 0.35, size=n_weeks)
    return pd.DataFrame(
        {
            "season": [2020] * n_weeks,
            "week": list(range(1, n_weeks + 1)),
            "units": [units_per_week] * n_weeks,
            "week_profit_loss": [
                pl_per_week * (1 if i % 2 else -1) + float(jitter[i])
                for i in range(n_weeks)
            ],
        }
    )


def test_bootstrap_is_reproducible():
    weekly = weekly_frame(30)
    first = week_cluster_bootstrap_roi(weekly, n_boot=5_000, seed=DEFAULT_SEED)
    second = week_cluster_bootstrap_roi(weekly, n_boot=5_000, seed=DEFAULT_SEED)
    assert first == second


def test_bootstrap_changes_with_the_seed():
    weekly = weekly_frame(30)
    first = week_cluster_bootstrap_roi(weekly, n_boot=5_000, seed=1)
    second = week_cluster_bootstrap_roi(weekly, n_boot=5_000, seed=2)
    assert first["ci_low"] != second["ci_low"]


def test_bootstrap_point_estimate_matches_the_aggregate_roi():
    weekly = weekly_frame(30)
    result = week_cluster_bootstrap_roi(weekly, n_boot=2_000, seed=DEFAULT_SEED)
    expected = weekly["week_profit_loss"].sum() / weekly["units"].sum()
    assert result["roi"] == pytest.approx(expected)
    assert result["ci_low"] <= result["roi"] <= result["ci_high"]


def test_bootstrap_refuses_an_interval_on_too_few_weeks():
    result = week_cluster_bootstrap_roi(weekly_frame(4), n_boot=1_000, seed=1)
    assert result["n_boot"] == 0
    assert np.isnan(result["ci_low"])
    assert "too few" in result["note"]


def test_bootstrap_resamples_weeks_not_tickets():
    """A single dominant week must widen the interval, which ticket-level SEs would hide."""
    weekly = weekly_frame(20, pl_per_week=0.2)
    weekly.loc[0, "week_profit_loss"] = 40.0
    weekly.loc[0, "units"] = 2.0
    result = week_cluster_bootstrap_roi(weekly, n_boot=5_000, seed=DEFAULT_SEED)
    assert result["ci_high"] - result["ci_low"] > 0.5
