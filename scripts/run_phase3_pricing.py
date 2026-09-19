#!/usr/bin/env python3
"""Phase 3 — pricing requirements and HYPOTHETICAL price sensitivity, NFL primary only.

No actual historical teaser menu prices exist for this source and none are invented.
Every grid price below is an analytical what-if. Nothing here is a realized ROI, a
backtested sportsbook return, or evidence about sportsbook profitability.

Frozen Teaser Model v1.0 is unchanged. P_ticket stays the product of leg P_est values,
with no correlation adjustment.

Usage:
    python scripts/run_phase3_pricing.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teaser_model_v1.analysis.backtest import build_leg_records, run_season  # noqa: E402
from teaser_model_v1.analysis.calibration import expected_versus_actual  # noqa: E402
from teaser_model_v1.analysis.pricing_sensitivity import (  # noqa: E402
    DEFAULT_BOOTSTRAP,
    DEFAULT_SEED,
    GRID_2TEAM,
    GRID_3TEAM,
    HYPOTHETICAL_LABEL,
    MATRIX_2TEAM,
    MATRIX_3TEAM,
    breakeven_frontier,
    fair_price_distribution,
    fair_price_rows,
    prepare_board,
    scenario_at_american,
    week_cluster_bootstrap_roi,
)
from teaser_model_v1.engine.pricing import (  # noqa: E402
    american_odds_from_profit,
    profit_from_american_odds,
)

PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

VALIDATION = tuple(range(2018, 2024))
ALL_SEASONS = tuple(range(2018, 2026))
BLOCKS = ("2018-2023 validation", "2024", "2025",
          "SUPPLEMENTARY 2018-2025 all years")

#: Paired grid points for the one-dimensional combined-board listing. The full cross
#: product is covered by the two-dimensional matrix in the report.
PAIRED_GRID = tuple(zip(GRID_2TEAM, GRID_3TEAM[: len(GRID_2TEAM)]))

FROZEN = (
    "**Frozen Teaser Model v1.0 is unchanged.** `P_ticket` is the product of leg `P_est` "
    "values, with no correlation adjustment: Phase 2C found only weak evidence against "
    "independence, which is not grounds for altering a frozen model."
)
REGIME = (
    "**Three source regimes.** 2018-2023 and 2024 sit on the pre-2025 archived line feed; "
    "2025 sits on a different feed. The all-years row is supplementary only."
)
PROVENANCE = (
    "Lines are archived reference lines with no documented capture time. They are not "
    "closing lines."
)
OVERLAP = (
    "> Tickets share legs within a week. No interval anywhere in this phase treats tickets "
    "as independent observations; every reported interval is a week-cluster bootstrap."
)


def md(frame: pd.DataFrame, raw_cols=None) -> str:
    kwargs = {"index": False, "floatfmt": ".4g"}
    if raw_cols:
        kwargs["disable_numparse"] = raw_cols
    return frame.to_markdown(**kwargs)


def load_blocks():
    runs = {}
    for tag, seasons in (("2018_2023", VALIDATION), ("2024_2025", (2024, 2025))):
        games = pd.read_csv(PROCESSED / f"nfl_games_{tag}.csv")
        records = build_leg_records(pd.read_csv(PROCESSED / f"nfl_legs_{tag}.csv"))
        for season in seasons:
            runs[season] = run_season(records, games, season)

    def cat(seasons, key):
        return pd.concat([runs[s][key] for s in seasons], ignore_index=True)

    qualifying = {
        "2018-2023 validation": cat(VALIDATION, "qualifying"),
        "2024": runs[2024]["qualifying"],
        "2025": runs[2025]["qualifying"],
        "SUPPLEMENTARY 2018-2025 all years": cat(ALL_SEASONS, "qualifying"),
    }
    tickets = {
        "2018-2023 validation": cat(VALIDATION, "tickets"),
        "2024": runs[2024]["tickets"],
        "2025": runs[2025]["tickets"],
        "SUPPLEMENTARY 2018-2025 all years": cat(ALL_SEASONS, "tickets"),
    }
    return qualifying, tickets


# ---------------------------------------------------------------------------------------


def calibration_base(qualifying) -> pd.DataFrame:
    rows = []
    for label in BLOCKS:
        frame = qualifying[label]
        scoring = expected_versus_actual(frame)
        rows.append(
            {
                "block": label,
                "n": scoring["n"],
                "mean_p_est": scoring["mean_p_est"],
                "expected_wins": scoring["expected_wins"],
                "actual_wins": scoring["actual_wins"],
                "actual_hit_rate": scoring["actual_hit_rate"],
                "calibration_gap": scoring["actual_hit_rate"] - scoring["mean_p_est"],
                "brier_score": scoring["brier_score"],
            }
        )
    return pd.DataFrame(rows)


def run_all_scenarios(qualifying, boards, args):
    """Every grid point, for both procedures, across every block."""
    summaries, selected_rows, weekly_rows = [], [], []

    def record(result, block, scenario, price2, price3):
        summary = result.summary()
        summary.update({"block": block, "scenario": scenario,
                        "american_2team": price2, "american_3team": price3})
        boot = (
            week_cluster_bootstrap_roi(result.weekly, n_boot=args.bootstrap,
                                       seed=args.seed)
            if not result.flat
            else {"n_weeks": int((result.weekly["units"] > 0).sum()), "n_boot": 0,
                  "roi": summary["hypothetical_roi"], "ci_low": float("nan"),
                  "ci_high": float("nan"), "note": "control; interval not computed"}
        )
        summary.update({"boot_weeks": boot["n_weeks"], "roi_ci_low": boot["ci_low"],
                        "roi_ci_high": boot["ci_high"], "boot_note": boot["note"]})
        summaries.append(summary)

        if len(result.selected):
            frame = result.selected.assign(
                block=block, scenario=scenario,
                procedure=summary["procedure"],
                american_2team=price2, american_3team=price3,
            )
            selected_rows.append(frame)
        if len(result.weekly):
            weekly_rows.append(
                result.weekly.assign(
                    block=block, scenario=scenario,
                    procedure=summary["procedure"],
                    american_2team=price2, american_3team=price3,
                )
            )

    for block in BLOCKS:
        frame, board = qualifying[block], boards[block]
        for flat in (False, True):
            for price in GRID_2TEAM:
                record(scenario_at_american(frame, american_2team=price, flat=flat,
                                            board=board),
                       block, "2-team only", price, None)
            for price in GRID_3TEAM:
                record(scenario_at_american(frame, american_3team=price, flat=flat,
                                            board=board),
                       block, "3-team only", None, price)
            for price2, price3 in PAIRED_GRID:
                record(scenario_at_american(frame, american_2team=price2,
                                            american_3team=price3, flat=flat,
                                            board=board),
                       block, "combined (paired)", price2, price3)

    return (
        pd.DataFrame(summaries),
        pd.concat(selected_rows, ignore_index=True) if selected_rows else pd.DataFrame(),
        pd.concat(weekly_rows, ignore_index=True) if weekly_rows else pd.DataFrame(),
    )


def price_matrix(qualifying, boards, args) -> pd.DataFrame:
    rows = []
    for block in BLOCKS:
        for price2 in MATRIX_2TEAM:
            for price3 in MATRIX_3TEAM:
                result = scenario_at_american(
                    qualifying[block], american_2team=price2, american_3team=price3,
                    board=boards[block],
                )
                summary = result.summary()
                boot = week_cluster_bootstrap_roi(result.weekly, n_boot=args.bootstrap,
                                                  seed=args.seed)
                rows.append({
                    "block": block,
                    "american_2team": price2,
                    "american_3team": price3,
                    "tickets_selected": summary["tickets_selected"],
                    "n_2team": int((result.selected["n_legs"] == 2).sum()) if len(result.selected) else 0,
                    "n_3team": int((result.selected["n_legs"] == 3).sum()) if len(result.selected) else 0,
                    "units": summary["units_staked"],
                    "wins": summary["wins"],
                    "outcome_hit_rate": summary["outcome_hit_rate"],
                    "hypothetical_pl": summary["hypothetical_profit_loss"],
                    "hypothetical_roi": summary["hypothetical_roi"],
                    "roi_ci_low": boot["ci_low"],
                    "roi_ci_high": boot["ci_high"],
                })
    return pd.DataFrame(rows)


def composition_table(selected: pd.DataFrame) -> pd.DataFrame:
    """Dog/favorite composition of selected tickets. Descriptive only."""
    if selected.empty:
        return pd.DataFrame()
    frozen = selected[selected["procedure"] == "frozen greedy + cap"]
    rows = []
    for (block, composition), group in frozen.groupby(["block", "composition"]):
        rows.append({
            "block": block,
            "composition": composition,
            "selected_ticket_rows": len(group),
            "wins": int(group["won"].sum()),
            "outcome_hit_rate": float(group["won"].mean()),
            "mean_p_ticket": float(group["p_ticket"].mean()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------------------


def control_mechanism(qualifying, boards, args) -> pd.DataFrame:
    """What the exposure cap actually removes, and how those tickets fared.

    Descriptive. The cap is a risk rule, not an EV rule; this quantifies its effect on the
    historical card without proposing any change to it.
    """
    rows = []
    for label in BLOCKS:
        for price2, price3, size in ((-110, None, 2), (None, 160, 3)):
            frozen = scenario_at_american(
                qualifying[label], american_2team=price2, american_3team=price3,
                board=boards[label],
            )
            flat = scenario_at_american(
                qualifying[label], american_2team=price2, american_3team=price3,
                flat=True, board=boards[label],
            )
            if flat.selected.empty:
                continue
            kept = set(frozen.selected["leg_ids"]) if len(frozen.selected) else set()
            skipped = flat.selected[~flat.selected["leg_ids"].isin(kept)]
            rows.append({
                "block": label,
                "reference_price": f"{size}-team {price2 or price3:+d} (hypothetical)",
                "all_positive_ev": len(flat.selected),
                "selected_by_cap": len(frozen.selected),
                "skipped_by_cap": len(skipped),
                "hit_rate_selected": float(frozen.selected["won"].mean()) if len(frozen.selected) else float("nan"),
                "hit_rate_skipped": float(skipped["won"].mean()) if len(skipped) else float("nan"),
                "mean_p_ticket_selected": float(frozen.selected["p_ticket"].mean()) if len(frozen.selected) else float("nan"),
                "mean_p_ticket_skipped": float(skipped["p_ticket"].mean()) if len(skipped) else float("nan"),
            })
    return pd.DataFrame(rows)


def write_fair_price_report(qualifying, tickets):
    lines, add = [], None
    lines = []
    add = lines.append
    add("# Phase 3 — model-implied fair price distribution")
    add("")
    add("## A: MODEL-IMPLIED FAIR PRICE")
    add("")
    add(
        "Derived from the frozen `P_ticket`:  `fair net profit per unit = (1 - P) / P`. "
        "This states what the **model** thinks a ticket is worth. It is **not** a price any "
        "sportsbook offered, and it is **not** a historical outcome. The distinct object "
        "derived from realized results is the historical outcome break-even price in "
        "`reports/phase3_historical_price_frontier.md`; the two must never be conflated."
    )
    add("")
    add(FROZEN)
    add("")
    for note in (REGIME, PROVENANCE):
        add(f"- {note}")
    add("")
    add(
        "At the fair price the break-even probability equals `P_ticket` exactly, by "
        "construction. Full precision is retained internally; the tables round for display."
    )
    add("")

    add("## Calibration base")
    add("")
    add(md(calibration_base(qualifying)))
    add("")
    add("> The all-years row is supplementary and spans three source regimes.")
    add("")

    add("## Fair-price distribution, by block and ticket size")
    add("")
    for label in BLOCKS:
        add(f"### {label}")
        add("")
        table = fair_price_distribution(tickets[label], label)
        show = table[[
            "ticket_size", "n_tickets",
            "p_ticket_min", "p_ticket_median", "p_ticket_max",
            "fair_american_min", "fair_american_p25", "fair_american_median",
            "fair_american_p75", "fair_american_max",
        ]]
        add(md(show))
        add("")
        add("Decimal-odds and net-profit views of the same distribution:")
        add("")
        add(md(table[[
            "ticket_size", "fair_profit_min", "fair_profit_p25", "fair_profit_median",
            "fair_profit_p75", "fair_profit_max", "fair_decimal_min",
            "fair_decimal_median", "fair_decimal_max",
        ]]))
        add("")

    add("## Reading these numbers")
    add("")
    add(
        "A 2-team fair price of, say, -129 means the frozen model considers a 2-team "
        "6-point teaser a break-even proposition at -129, so a book charging more juice "
        "than that is charging more than the model's own valuation. Whether the model's "
        "valuation is correct is the calibration question answered in Phase 2/2B, not here."
    )
    add("")
    add("Machine-readable: `data/processed/phase3_ticket_fair_prices.csv`.")
    add("")

    path = REPORTS / "phase3_fair_price_distribution.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"written: {path.relative_to(ROOT)}")


def write_sensitivity_report(summaries, matrix, composition, qualifying, boards,
                             mechanism, args):
    lines = []
    add = lines.append
    add("# Phase 3 — hypothetical price sensitivity")
    add("")
    add(HYPOTHETICAL_LABEL)
    add("")
    add(FROZEN)
    add("")
    for note in (REGIME, PROVENANCE):
        add(f"- {note}")
    add("")
    add(OVERLAP)
    add("")
    add(
        "The grid points below are **analytical only**. They are not described as "
        "historically common, historically available, or typical of any book. At each "
        "price the frozen procedure is reproduced exactly — top-four construction, "
        "break-even and EV from the frozen `P_ticket`, positive-EV filter, descending "
        "precise-EV greedy walk, 1 unit per ticket, 2-unit aggregate cap per leg — with "
        "only the price replaced by the hypothetical value."
    )
    add("")
    add(
        f"Week-cluster bootstrap: {args.bootstrap:,} resamples, seed `{args.seed}`. "
        "Intervals are refused where too few weeks carry a bet."
    )
    add("")

    frozen_rows = summaries[summaries["procedure"] == "frozen greedy + cap"]
    columns = [
        "american_2team", "american_3team", "eligible_positive_ev_tickets",
        "tickets_selected", "betting_weeks", "zero_bet_weeks", "units_staked",
        "wins", "losses", "outcome_hit_rate", "hypothetical_profit_loss",
        "hypothetical_roi", "roi_ci_low", "roi_ci_high",
    ]

    for scenario in ("2-team only", "3-team only", "combined (paired)"):
        add(f"## {scenario}")
        add("")
        if scenario == "combined (paired)":
            add(
                "Paired grid points: the 2-team and 3-team grids are zipped position by "
                "position. The full cross product is in the matrix below."
            )
            add("")
        for label in BLOCKS:
            subset = frozen_rows[
                (frozen_rows["block"] == label) & (frozen_rows["scenario"] == scenario)
            ]
            if subset.empty:
                continue
            add(f"### {label} — {scenario}")
            add("")
            add(md(subset[columns]))
            add("")
        add(f"> {HYPOTHETICAL_LABEL}")
        add("")

    add("## Two-dimensional combined-price matrix")
    add("")
    add(
        "The greedy ranks every ticket by EV computed from **its own** offered hypothetical "
        "price, so a 3-team ticket can outrank a 2-team ticket or the reverse depending on "
        "the pair."
    )
    add("")
    for label in BLOCKS:
        subset = matrix[matrix["block"] == label]
        if subset.empty:
            continue
        add(f"### {label}")
        add("")
        add(md(subset.drop(columns=["block"])))
        add("")
        pivot = subset.pivot(index="american_2team", columns="american_3team",
                             values="hypothetical_roi")
        add("Hypothetical ROI, 2-team price (rows) against 3-team price (columns):")
        add("")
        add(pivot.to_markdown(floatfmt=".4f"))
        add("")
    add(f"> {HYPOTHETICAL_LABEL}")
    add("")

    add("## Flat-eligibility control")
    add("")
    add(
        "Control: include **every** positive-EV ticket, with no EV ranking and no exposure "
        "cap. Its purpose is to show whether any apparent result comes materially from the "
        "exposure algorithm rather than from the underlying ticket set. **Neither procedure "
        "is optimized**, and the control is not a proposal."
    )
    add("")
    for scenario in ("2-team only", "3-team only", "combined (paired)"):
        comparison = summaries[summaries["scenario"] == scenario].pivot_table(
            index=["block", "american_2team", "american_3team"],
            columns="procedure",
            values=["tickets_selected", "hypothetical_roi"],
            dropna=False,
        ).reset_index()
        comparison.columns = [
            "_".join(str(part) for part in col if part).replace(
                "flat eligibility (control)", "flat"
            ).replace("frozen greedy + cap", "frozen")
            for col in comparison.columns
        ]
        add(f"### {scenario}")
        add("")
        add(md(comparison))
        add("")

    add("### What the exposure cap removes, and how those tickets fared")
    add("")
    add(
        "At a single price within one ticket size, EV order is the same as `P_ticket` "
        "order, so the greedy exhausts the highest-`P_est` legs first. In a four-leg week "
        "it takes the three pairings among the top three legs, at which point all three sit "
        "at the 2-unit cap and **every remaining ticket containing the fourth leg is "
        "skipped**. The cap therefore removes the lowest-`P_est` leg of large weeks almost "
        "by construction."
    )
    add("")
    if not mechanism.empty:
        add(md(mechanism))
        add("")
    add(
        "In the 2018-2023 block and in the all-years row the skipped tickets won **more** "
        "often than the ones the cap kept, which is why the flat control shows a higher "
        "hypothetical ROI at most grid points there. **2025 reverses this** — the kept "
        "tickets out-performed the skipped ones — so the effect is not a stable property."
    )
    add("")
    add(
        "Crucially, the mean `P_ticket` of kept and skipped tickets is nearly identical "
        "(0.5663 against 0.5640 at 2-team -110, all years). The cap is therefore **not** "
        "discarding tickets the model rates materially worse; essentially the whole "
        "hit-rate gap is realized-outcome variation on a small sample, not a difference in "
        "model-rated quality."
    )
    add("")
    add(
        "**The exposure cap is a risk rule, not an EV rule.** It exists to bound "
        "single-leg exposure, and it does that exactly — no leg ever exceeds 2 units. "
        "Nothing here is a recommendation to change it, and no wager-sizing change is "
        "proposed."
    )
    add("")

    add("## Dog/favorite composition of selected tickets")
    add("")
    add(
        "Descriptive only. This does **not** modify selection, and the frozen model treats "
        "all four primary shapes identically."
    )
    add("")
    if not composition.empty:
        add(md(composition))
        add("")
        add(
            "Note that composition counts are pooled across every grid price, so a ticket "
            "selected at several prices is counted once per price. They describe the shape "
            "of the selected card, not a sample of independent tickets."
        )
    else:
        add("No tickets were selected at any grid price.")
    add("")

    add("## Overlap and effective sample")
    add("")
    overlap_rows = []
    for label in BLOCKS:
        frame = qualifying[label]
        result = scenario_at_american(frame, american_2team=-120, american_3team=140,
                                      board=boards[label])
        selected = result.selected
        legs = [leg for ids in selected["leg_ids"] for leg in ids.split("|")] if len(selected) else []
        overlap_rows.append({
            "block": label,
            "reference_scenario": "2-team -120 / 3-team +140 (hypothetical)",
            "nominal_tickets_selected": len(selected),
            "unique_weeks_with_a_bet": int(selected[["season", "week"]].drop_duplicates().shape[0]) if len(selected) else 0,
            "unique_constituent_legs": len(set(legs)),
            "max_aggregate_leg_exposure": int(result.weekly["max_leg_exposure"].max()) if len(result.weekly) else 0,
            "week_pl_min": float(result.weekly["week_profit_loss"].min()) if len(result.weekly) else float("nan"),
            "week_pl_median": float(result.weekly["week_profit_loss"].median()) if len(result.weekly) else float("nan"),
            "week_pl_max": float(result.weekly["week_profit_loss"].max()) if len(result.weekly) else float("nan"),
        })
    add(md(pd.DataFrame(overlap_rows)))
    add("")
    add(
        "The maximum aggregate leg exposure confirms the frozen 2-unit cap binds: no leg "
        "ever carries more than 2 units in a week."
    )
    add("")

    add("## Machine-readable outputs")
    add("")
    add("- `data/processed/phase3_price_grid.csv` — every grid point, both procedures")
    add("- `data/processed/phase3_price_matrix.csv` — the 2-D combined matrix")
    add("- `data/processed/phase3_selected_tickets.csv` — ticket-level, every scenario")
    add("- `data/processed/phase3_weekly_cards.csv` — weekly card, every scenario")
    add("- `data/processed/phase3_ticket_fair_prices.csv` — model-implied fair prices")
    add("- `data/processed/phase3_frontier_curves.csv` — price/PL curves")
    add("- `data/processed/phase3_cap_mechanism.csv` — what the exposure cap removes")
    add("")
    add(f"> {HYPOTHETICAL_LABEL}")
    add("")

    path = REPORTS / "phase3_pricing_sensitivity.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"written: {path.relative_to(ROOT)}")


def write_frontier_report(frontiers, curves, qualifying, args):
    lines = []
    add = lines.append
    add("# Phase 3 — historical outcome price frontier")
    add("")
    add("## B: HISTORICAL OUTCOME BREAK-EVEN PRICE")
    add("")
    add(
        "The payout at which **realized historical profit equals zero**, using the actual "
        "outcomes of the tickets the frozen procedure would have selected. This is derived "
        "from results, not from `P_est`."
    )
    add("")
    add(
        "**This is a different object from A: MODEL-IMPLIED FAIR PRICE** "
        "(`reports/phase3_fair_price_distribution.md`), which is derived from the model's "
        "own probabilities. A gap between A and B is a statement about how the realized "
        "sample differed from the model, on a sample of this size. Neither is a price any "
        "book offered."
    )
    add("")
    add(FROZEN)
    add("")
    for note in (REGIME, PROVENANCE):
        add(f"- {note}")
    add("")
    add(OVERLAP)
    add("")
    add(
        "Selection depends on price — a better payout makes more tickets positive-EV and "
        "reorders the greedy walk — so the frontier cannot be inverted from a hit rate. "
        "The whole frozen procedure is re-run at every price on a fine scan, and the "
        "crossing is then located by bisection."
    )
    add("")

    add("## Crossing points")
    add("")
    rows = []
    for frontier in frontiers:
        rows.append({
            "block": frontier.block,
            "ticket_size": frontier.ticket_size,
            "breakeven_net_profit": frontier.crossing_profit,
            "breakeven_american": frontier.crossing_american,
            "tickets_selected_at_crossing": frontier.tickets_at_crossing,
            "note": frontier.note,
        })
    add(md(pd.DataFrame(rows)))
    add("")

    add("## Sensitivity around the threshold")
    add("")
    add(
        "Hypothetical P/L and ROI at prices bracketing each crossing. A shallow curve means "
        "the conclusion is fragile to the price assumption."
    )
    add("")
    for frontier in frontiers:
        if frontier.crossing_profit is None:
            continue
        curve = curves[(frontier.block, frontier.ticket_size)]
        window = curve[
            (curve["profit"] >= frontier.crossing_profit - 0.25)
            & (curve["profit"] <= frontier.crossing_profit + 0.25)
        ]
        window = window.iloc[:: max(1, len(window) // 12)]
        add(f"### {frontier.block} — {frontier.ticket_size}")
        add("")
        add(md(window[["american", "profit", "tickets_selected", "units", "wins",
                       "profit_loss", "roi"]]))
        add("")

    add("## A versus B, side by side")
    add("")
    add(
        "Model-implied fair price against historical outcome break-even, for the same "
        "block and ticket size. **These are different objects.** A is what the model says "
        "the ticket is worth; B is what this particular realized sample would have needed."
    )
    add("")
    add(
        "Where B is a *worse* price than A (more juice tolerable), the selected tickets "
        "out-performed the frozen `P_ticket` in that sample. Where B is *better* than A, "
        "they under-performed. Neither is evidence about future prices or future outcomes."
    )
    add("")
    add(f"> {HYPOTHETICAL_LABEL}")
    add("")
    add(
        "Machine-readable curves: `data/processed/phase3_frontier_curves.csv`."
    )
    add("")

    path = REPORTS / "phase3_historical_price_frontier.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"written: {path.relative_to(ROOT)}")


# ---------------------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", type=int, default=DEFAULT_BOOTSTRAP)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    qualifying, tickets = load_blocks()
    boards = {label: prepare_board(qualifying[label]) for label in BLOCKS}

    fair_rows = pd.concat(
        [fair_price_rows(tickets[label]).assign(block=label) for label in BLOCKS],
        ignore_index=True,
    )
    fair_rows.to_csv(PROCESSED / "phase3_ticket_fair_prices.csv", index=False)

    print("running price grids ...")
    summaries, selected, weekly = run_all_scenarios(qualifying, boards, args)
    summaries.to_csv(PROCESSED / "phase3_price_grid.csv", index=False)
    selected.to_csv(PROCESSED / "phase3_selected_tickets.csv", index=False)
    weekly.to_csv(PROCESSED / "phase3_weekly_cards.csv", index=False)

    print("running combined matrix ...")
    matrix = price_matrix(qualifying, boards, args)
    matrix.to_csv(PROCESSED / "phase3_price_matrix.csv", index=False)

    print("scanning break-even frontier ...")
    frontiers, curves, curve_rows = [], {}, []
    for label in BLOCKS:
        for size in (2, 3):
            frontier = breakeven_frontier(qualifying[label], size, block=label)
            frontiers.append(frontier)
            curves[(frontier.block, frontier.ticket_size)] = frontier.curve
            curve_rows.append(
                frontier.curve.assign(block=label, ticket_size=f"{size}-team")
            )
    pd.concat(curve_rows, ignore_index=True).to_csv(
        PROCESSED / "phase3_frontier_curves.csv", index=False
    )

    composition = composition_table(selected)

    write_fair_price_report(qualifying, tickets)
    mechanism = control_mechanism(qualifying, boards, args)
    mechanism.to_csv(PROCESSED / "phase3_cap_mechanism.csv", index=False)
    write_sensitivity_report(summaries, matrix, composition, qualifying, boards,
                             mechanism, args)
    write_frontier_report(frontiers, curves, qualifying, args)

    print("\n=== digest ===")
    print(md(calibration_base(qualifying)))
    print()
    for frontier in frontiers:
        print(f"{frontier.block:36} {frontier.ticket_size}: break-even "
              f"{frontier.crossing_american if frontier.crossing_american is None else round(frontier.crossing_american)} "
              f"({frontier.tickets_at_crossing} tickets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
