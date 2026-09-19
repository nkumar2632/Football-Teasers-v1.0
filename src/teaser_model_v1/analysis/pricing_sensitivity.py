"""Phase 3 — pricing requirements and hypothetical price sensitivity.

**No actual historical teaser menu prices exist for this source, and none are invented.**
Every price in this module is either

* a **model-implied fair price**, derived from the frozen `P_ticket` and therefore a
  statement about the model, not about any sportsbook; or
* an **explicitly hypothetical analytical grid point**, which is a what-if and must be
  labelled as such in every output.

Nothing here is a realized return, a backtested sportsbook result, or evidence about what
any book offered. Frozen Teaser Model v1.0 is unchanged: `P_ticket` stays the product of
leg `P_est` values, with no correlation adjustment (Phase 2C found only weak evidence
against independence, which is not grounds for changing a frozen model).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from teaser_model_v1.engine.legs import build_leg, eligible_live_primary_legs
from teaser_model_v1.engine.pricing import (
    american_odds_from_profit,
    break_even_probability,
    fair_break_even_profit,
    profit_from_american_odds,
)
from teaser_model_v1.engine.tickets import (
    Ticket,
    generate_tickets,
    select_live_tickets,
    select_top_legs,
)

#: The mandatory label for every hypothetical-price result.
HYPOTHETICAL_LABEL = (
    "**HYPOTHETICAL HISTORICAL SENSITIVITY** — assumes this teaser price was available "
    "for every qualifying historical ticket. **Actual historical teaser prices are "
    "unknown.** This is not a backtested sportsbook return and not a realized ROI."
)

#: Analytical grid points only. NOT a claim that these prices were common or available.
GRID_2TEAM = (-100, -110, -120, -130, -140, -150)
GRID_3TEAM = (100, 110, 120, 130, 140, 150, 160, 170, 180)

#: Combined matrix axes.
MATRIX_2TEAM = (-110, -120, -130, -140)
MATRIX_3TEAM = (120, 140, 160, 180)

DEFAULT_SEED = 20260919
DEFAULT_BOOTSTRAP = 50_000


def _research_eligibility(ticket: Ticket) -> bool:
    """Positive EV, ignoring the hypothetical-price flag.

    Used **only** to drive the frozen greedy over a hypothetical grid. It is not a live
    eligibility rule and can never designate a real bet.
    """
    return ticket.is_positive_ev


# ---------------------------------------------------------------------------------------
# Fair price (model-implied)
# ---------------------------------------------------------------------------------------


def fair_price_rows(tickets: pd.DataFrame) -> pd.DataFrame:
    """Model-implied fair price for every generated ticket.

        fair net profit per unit = (1 - P_ticket) / P_ticket

    The break-even probability at that price is `P_ticket` itself, by construction.
    This is **A: MODEL-IMPLIED FAIR PRICE**. It says what the frozen model thinks a ticket
    is worth. It is not a price anyone offered and not a historical outcome.
    """
    if tickets.empty:
        return tickets.assign(
            fair_profit=[], fair_decimal_odds=[], fair_american_odds=[],
            break_even_probability=[],
        )
    p = tickets["predicted_p_ticket"].astype(float)
    fair_profit = p.map(fair_break_even_profit)
    return tickets.assign(
        fair_profit=fair_profit,
        fair_decimal_odds=1.0 + fair_profit,
        fair_american_odds=fair_profit.map(american_odds_from_profit),
        break_even_probability=fair_profit.map(break_even_probability),
    )


def fair_price_distribution(tickets: pd.DataFrame, label: str) -> pd.DataFrame:
    """Min / p25 / median / p75 / max of the model-implied fair price, by ticket size."""
    priced = fair_price_rows(tickets)
    rows = []
    for size in (2, 3):
        subset = priced[priced["n_legs"] == size]
        if subset.empty:
            continue
        row = {"block": label, "ticket_size": f"{size}-team", "n_tickets": len(subset)}
        for name, column in (
            ("p_ticket", "predicted_p_ticket"),
            ("fair_profit", "fair_profit"),
            ("fair_decimal", "fair_decimal_odds"),
            ("fair_american", "fair_american_odds"),
        ):
            values = subset[column].astype(float)
            row[f"{name}_min"] = float(values.min())
            row[f"{name}_p25"] = float(values.quantile(0.25))
            row[f"{name}_median"] = float(values.median())
            row[f"{name}_p75"] = float(values.quantile(0.75))
            row[f"{name}_max"] = float(values.max())
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# Scenario execution — the frozen algorithm at a hypothetical price
# ---------------------------------------------------------------------------------------


@dataclass
class ScenarioResult:
    """Outcome of running the frozen procedure over one hypothetical price point."""

    label: str
    profit_by_size: dict
    selected: pd.DataFrame
    weekly: pd.DataFrame
    flat: bool

    def summary(self) -> dict:
        selected, weekly = self.selected, self.weekly
        units = float(len(selected))
        wins = int(selected["won"].sum()) if len(selected) else 0
        losses = len(selected) - wins
        profit_loss = (
            float((selected["won"] * selected["profit"] - (1 - selected["won"])).sum())
            if len(selected)
            else 0.0
        )
        betting_weeks = int((weekly["n_selected"] > 0).sum())
        return {
            "label": self.label,
            "procedure": "flat eligibility (control)" if self.flat else "frozen greedy + cap",
            "price_2team": self.profit_by_size.get(2),
            "price_3team": self.profit_by_size.get(3),
            "eligible_positive_ev_tickets": int(weekly["n_positive_ev"].sum()),
            "tickets_selected": len(selected),
            "betting_weeks": betting_weeks,
            "weeks_with_construction": int((weekly["n_tickets"] > 0).sum()),
            "zero_bet_weeks": int((weekly["n_selected"] == 0).sum()),
            "units_staked": units,
            "wins": wins,
            "losses": losses,
            "outcome_hit_rate": wins / units if units else float("nan"),
            "hypothetical_profit_loss": profit_loss,
            "hypothetical_roi": profit_loss / units if units else float("nan"),
        }


def _week_legs(group: pd.DataFrame) -> list:
    return [
        build_leg(
            leg_id=row.leg_id,
            league=row.league,
            team=row.team,
            spread=row.archived_reference_line,
            game_total=row.game_total,
            game_id=row.game_id,
            season=int(row.season),
            week=int(row.week),
        )
        for row in group.itertuples(index=False)
    ]


@dataclass
class PreparedBoard:
    """The frozen weekly construction, built once and reused across price points.

    Leg construction and the top-four ranking are **outcome- and price-independent**, so
    they are computed once. Only the price-dependent steps — break-even, EV, the positive-EV
    filter, the EV ordering and the exposure walk — are recomputed per price. This is a
    caching optimisation, not a change to the procedure: a test asserts a prepared run and
    a direct run agree exactly.
    """

    weeks: list
    outcome: dict
    side: dict


def prepare_board(qualifying: pd.DataFrame) -> PreparedBoard:
    """Build each week's top-four legs once."""
    weeks = []
    for (season, week), group in qualifying.groupby(["season", "week"]):
        legs = _week_legs(group)
        top = select_top_legs(eligible_live_primary_legs(legs))
        weeks.append((int(season), int(week), len(group), top))
    return PreparedBoard(
        weeks=weeks,
        outcome=dict(zip(qualifying["leg_id"], qualifying["won"])),
        side=dict(zip(qualifying["leg_id"], qualifying["side_class"])),
    )


def run_scenario(
    qualifying: pd.DataFrame,
    profit_by_size: dict,
    *,
    label: str = "",
    flat: bool = False,
    board: "PreparedBoard | None" = None,
) -> ScenarioResult:
    """Run the frozen weekly procedure at a hypothetical price and grade the result.

    Reproduces the live placement algorithm exactly, except that the price is hypothetical:

    1. frozen top-four leg construction within each week;
    2. all 2-team and 3-team combinations;
    3. break-even and EV recomputed from the frozen `P_ticket` at the offered price;
    4. positive-EV tickets walked in descending internally precise EV order;
    5. a 1-unit ticket added only while every constituent leg stays at <= 2 aggregate units.

    With ``flat=True`` the control is run instead: every positive-EV ticket is included,
    with no ranking and no exposure cap. Neither procedure is optimized.
    """
    if board is None:
        board = prepare_board(qualifying)
    outcome, side = board.outcome, board.side

    selected_rows, weekly_rows = [], []

    for season, week, n_qualifying, top in board.weeks:
        tickets = generate_tickets(
            top, profit_by_size, price_is_hypothetical=True,
            price_provenance="hypothetical analytical grid point",
        )
        positive = [t for t in tickets if _research_eligibility(t)]

        if flat:
            chosen = list(positive)
            exposure: dict[str, int] = {}
            for ticket in chosen:
                for leg in ticket.legs:
                    exposure[leg.leg_id] = exposure.get(leg.leg_id, 0) + 1
        else:
            result = select_live_tickets(tickets, eligibility=_research_eligibility)
            chosen = list(result.selected)
            exposure = result.exposure

        for ticket in chosen:
            legs_won = [int(outcome[leg.leg_id]) for leg in ticket.legs]
            sides = [side[leg.leg_id] for leg in ticket.legs]
            won = int(all(legs_won))
            selected_rows.append(
                {
                    "season": season,
                    "week": week,
                    "n_legs": ticket.n_legs,
                    "leg_ids": "|".join(ticket.leg_ids),
                    "p_ticket": ticket.p_ticket,
                    "profit": ticket.profit,
                    "break_even": ticket.break_even,
                    "ev_per_unit": ticket.ev,
                    "won": won,
                    "legs_winning": sum(legs_won),
                    "composition": (
                        "all-dog" if all(s == "DOG" for s in sides)
                        else "all-favorite" if all(s == "FAVORITE" for s in sides)
                        else "mixed"
                    ),
                    "unit_result": (ticket.profit if won else -1.0),
                }
            )

        week_units = len(chosen)
        week_pl = sum(
            (ticket.profit if all(int(outcome[leg.leg_id]) for leg in ticket.legs) else -1.0)
            for ticket in chosen
        )
        weekly_rows.append(
            {
                "season": season,
                "week": week,
                "n_qualifying_legs": n_qualifying,
                "n_top_legs": len(top),
                "n_tickets": len(tickets),
                "n_positive_ev": len(positive),
                "n_selected": week_units,
                "max_leg_exposure": max(exposure.values()) if exposure else 0,
                "units": float(week_units),
                "wins": sum(
                    1 for t in chosen
                    if all(int(outcome[leg.leg_id]) for leg in t.legs)
                ),
                "week_profit_loss": float(week_pl),
            }
        )

    selected = pd.DataFrame(selected_rows)
    weekly = pd.DataFrame(weekly_rows)
    if weekly.empty:
        weekly = pd.DataFrame(
            columns=["season", "week", "n_qualifying_legs", "n_top_legs", "n_tickets",
                     "n_positive_ev", "n_selected", "max_leg_exposure", "units", "wins",
                     "week_profit_loss"]
        )
    return ScenarioResult(label=label, profit_by_size=dict(profit_by_size),
                          selected=selected, weekly=weekly, flat=flat)


def scenario_at_american(
    qualifying: pd.DataFrame,
    *,
    american_2team: float | None = None,
    american_3team: float | None = None,
    label: str = "",
    flat: bool = False,
    board: "PreparedBoard | None" = None,
) -> ScenarioResult:
    """Convenience wrapper taking hypothetical American prices."""
    profit_by_size = {}
    if american_2team is not None:
        profit_by_size[2] = profit_from_american_odds(american_2team)
    if american_3team is not None:
        profit_by_size[3] = profit_from_american_odds(american_3team)
    return run_scenario(qualifying, profit_by_size, label=label, flat=flat, board=board)


# ---------------------------------------------------------------------------------------
# Historical outcome break-even frontier
# ---------------------------------------------------------------------------------------


@dataclass
class FrontierResult:
    """Where realized profit crosses zero, given the frozen selection procedure.

    This is **B: HISTORICAL OUTCOME BREAK-EVEN PRICE**, derived from realized results. It
    is a different object from the model-implied fair price and must never be conflated
    with it.
    """

    block: str
    ticket_size: str
    crossing_profit: float | None
    crossing_american: float | None
    tickets_at_crossing: int
    curve: pd.DataFrame
    note: str


def breakeven_frontier(
    qualifying: pd.DataFrame,
    size: int,
    *,
    block: str,
    profit_low: float = 0.30,
    profit_high: float = 3.00,
    step: float = 0.005,
    refine_step: float = 1e-4,
) -> FrontierResult:
    """Scan the offered price and find where realized profit crosses zero.

    Selection itself depends on price — a better payout makes more tickets positive-EV and
    changes the EV ordering the greedy walks — so this cannot be inverted from a hit rate.
    The price is scanned, the whole frozen procedure re-run at each point, and the crossing
    located by scan then bisection.
    """
    board = prepare_board(qualifying)
    grid = np.arange(profit_low, profit_high + step / 2, step)
    rows = []
    for profit in grid:
        result = run_scenario(qualifying, {size: float(profit)}, board=board)
        summary = result.summary()
        rows.append(
            {
                "profit": float(profit),
                "american": american_odds_from_profit(float(profit)),
                "tickets_selected": summary["tickets_selected"],
                "units": summary["units_staked"],
                "wins": summary["wins"],
                "profit_loss": summary["hypothetical_profit_loss"],
                "roi": summary["hypothetical_roi"],
            }
        )
    curve = pd.DataFrame(rows)

    active = curve[curve["tickets_selected"] > 0]
    if active.empty:
        return FrontierResult(block, f"{size}-team", None, None, 0, curve,
                              "No ticket is positive EV anywhere on the scanned range.")

    negative = active[active["profit_loss"] < 0]
    positive = active[active["profit_loss"] >= 0]
    if positive.empty:
        return FrontierResult(
            block, f"{size}-team", None, None, 0, curve,
            f"Realized profit stays negative across the whole scanned range "
            f"(up to {american_odds_from_profit(float(grid[-1])):+.0f}).",
        )
    if negative.empty:
        first = active.iloc[0]
        return FrontierResult(
            block, f"{size}-team", float(first["profit"]), float(first["american"]),
            int(first["tickets_selected"]), curve,
            "Realized profit is non-negative from the lowest price at which any ticket "
            "is selected; the crossing lies at or below the scanned range.",
        )

    lo = float(negative["profit"].max())
    hi = float(positive[positive["profit"] > lo]["profit"].min())
    while hi - lo > refine_step:
        mid = (lo + hi) / 2.0
        summary = run_scenario(qualifying, {size: mid}, board=board).summary()
        if summary["tickets_selected"] == 0 or summary["hypothetical_profit_loss"] < 0:
            lo = mid
        else:
            hi = mid
    final = run_scenario(qualifying, {size: hi}, board=board).summary()
    return FrontierResult(
        block, f"{size}-team", hi, american_odds_from_profit(hi),
        final["tickets_selected"], curve,
        "Crossing located by scan then bisection; the frozen procedure is re-run at every "
        "price, so selection changes along the curve.",
    )


# ---------------------------------------------------------------------------------------
# Week-cluster bootstrap
# ---------------------------------------------------------------------------------------


def week_cluster_bootstrap_roi(
    weekly: pd.DataFrame,
    *,
    n_boot: int = DEFAULT_BOOTSTRAP,
    seed: int = DEFAULT_SEED,
    min_weeks: int = 10,
) -> dict:
    """Cluster-aware interval for a hypothetical ROI, resampling **weeks**.

    Tickets share legs within a week, so a ticket-level standard error would be wrong.
    Weeks are the resampling unit. If too few weeks carry a bet the interval is refused
    rather than reported misleadingly.
    """
    betting = weekly[weekly["units"] > 0]
    n_weeks = len(betting)
    if n_weeks < min_weeks:
        return {
            "n_weeks": n_weeks,
            "n_boot": 0,
            "roi": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "note": f"Only {n_weeks} betting weeks: too few for a meaningful interval. "
                    "No confidence interval is reported.",
        }

    pl = betting["week_profit_loss"].to_numpy(dtype=float)
    units = betting["units"].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, n_weeks, size=(n_boot, n_weeks))
    boot_pl = pl[draws].sum(axis=1)
    boot_units = units[draws].sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        boot_roi = np.where(boot_units > 0, boot_pl / boot_units, np.nan)

    return {
        "n_weeks": n_weeks,
        "n_boot": n_boot,
        "roi": float(pl.sum() / units.sum()),
        "ci_low": float(np.nanpercentile(boot_roi, 2.5)),
        "ci_high": float(np.nanpercentile(boot_roi, 97.5)),
        "note": f"Week-cluster bootstrap, {n_boot:,} resamples, seed {seed}.",
    }
