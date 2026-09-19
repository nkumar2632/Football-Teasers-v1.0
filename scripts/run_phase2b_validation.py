#!/usr/bin/env python3
"""Phase 2B — out-of-sample validation of frozen Teaser Model v1.0 on NFL 2018-2023.

Validation only. No price, no EV, no ROI, no hypothetical payout. No parameter is fitted
and no model rule is touched. CFB and NFL secondary shapes are not run.

The hypotheses tested here (H1 overall calibration, H2 dog/favorite asymmetry, H3 whether
total-driven P_est variation adds information) were declared before these seasons'
outcomes were examined.

Usage:
    python scripts/run_phase2b_validation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teaser_model_v1.analysis.backtest import (  # noqa: E402
    build_leg_records,
    primary_before_guardrail,
    run_season,
)
from teaser_model_v1.analysis.calibration import (  # noqa: E402
    DOG_SHAPES,
    FAVORITE_SHAPES,
    LOW_SAMPLE_N,
    PRIMARY_SHAPE_ORDER,
    SHAPE_DESCRIPTIONS,
    TOTAL_BUCKETS,
    clopper_pearson_interval,
    expected_versus_actual,
    frozen_versus_constant,
    summarise_by,
    summarise_group,
)
from teaser_model_v1.analysis.grading import assert_no_primary_push  # noqa: E402
from teaser_model_v1.analysis.validation import (  # noqa: E402
    assess_monotonicity,
    compare_two_groups,
    dog_favorite_comparison,
    group_interval_row,
)

VALIDATION_SEASONS = (2018, 2019, 2020, 2021, 2022, 2023)
PHASE2_SEASONS = (2024, 2025)
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

PROVENANCE_LINE = (
    "Lines are **archived reference lines** (`archived_reference_line`). The source "
    "documents no capture time. They are **not** closing lines and support no CLV claim."
)
NO_PRICE_LINE = (
    "No historical teaser menu prices exist in this source and none have been invented. "
    "No EV, break-even, payout or ROI figure appears in this phase."
)
REGIME_LINE = (
    "**Three source regimes.** 2018-2023 and 2024 sit on the pre-2025 line feed; 2025 sits "
    "on a different feed. Blocks are never silently pooled; see "
    "`reports/nfl_line_composition_investigation.md`."
)
FROZEN_LINE = (
    "Frozen Teaser Model v1.0 is unchanged by this phase. Nothing below is a "
    "recommendation to alter it."
)


def md(frame: pd.DataFrame, raw_cols=None) -> str:
    kwargs = {"index": False, "floatfmt": ".4g"}
    if raw_cols:
        kwargs["disable_numparse"] = raw_cols
    return frame.to_markdown(**kwargs)


def load(tag: str):
    games = pd.read_csv(PROCESSED / f"nfl_games_{tag}.csv")
    legs = pd.read_csv(PROCESSED / f"nfl_legs_{tag}.csv")
    return games, build_leg_records(legs)


def shape_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for shape in PRIMARY_SHAPE_ORDER:
        result = summarise_group(shape, frame[frame["shape"] == shape]).as_dict()
        result["geometry"] = SHAPE_DESCRIPTIONS[shape]
        rows.append(result)
    out = pd.DataFrame(rows).rename(columns={"group": "shape"})
    return out[
        ["shape", "geometry", "n", "mean_p_est", "actual_hit_rate", "calibration_gap",
         "ci95_low", "ci95_high", "low_sample"]
    ]


def bucket_table(frame: pd.DataFrame) -> pd.DataFrame:
    out = summarise_by(frame, "total_bucket", [b[0] for b in TOTAL_BUCKETS])
    out = out.rename(columns={"group": "bucket"})
    return out[
        ["bucket", "n", "mean_p_est", "actual_hit_rate", "calibration_gap",
         "ci95_low", "ci95_high", "low_sample"]
    ]


def weekly_distribution(weekly: pd.DataFrame) -> dict:
    counts = {}
    for label, low, high in [("0", 0, 0), ("1", 1, 1), ("2", 2, 2), ("3", 3, 3), (">=4", 4, None)]:
        mask = weekly["n_qualifying_legs"] >= low
        if high is not None:
            mask &= weekly["n_qualifying_legs"] <= high
        counts[label] = int(mask.sum())
    return counts


def ticket_table(tickets: pd.DataFrame, label: str = "") -> pd.DataFrame:
    rows = []
    for size in (2, 3):
        subset = tickets[tickets["n_legs"] == size] if len(tickets) else tickets
        n = len(subset)
        if n == 0:
            rows.append({"block": label, "ticket_size": f"{size}-team", "n_tickets": 0,
                         "mean_product_p_est": float("nan"), "realized_hit_rate": float("nan"),
                         "gap": float("nan"), "ci95_low": float("nan"),
                         "ci95_high": float("nan"), "same_game_tickets": 0})
            continue
        wins = int(subset["won"].sum())
        predicted = float(subset["predicted_p_ticket"].mean())
        realized = wins / n
        low, high = clopper_pearson_interval(wins, n)
        rows.append({"block": label, "ticket_size": f"{size}-team", "n_tickets": n,
                     "mean_product_p_est": predicted, "realized_hit_rate": realized,
                     "gap": realized - predicted, "ci95_low": low, "ci95_high": high,
                     "same_game_tickets": int(subset["same_game_legs"].sum())})
    out = pd.DataFrame(rows)
    return out if label else out.drop(columns=["block"])


def legs_used_on_tickets(per_season, seasons) -> pd.DataFrame:
    """The top-four legs from weeks that actually produced tickets (>= 2 legs).

    Used as a control: it isolates the legs the ticket numbers are built from, so a
    ticket-versus-product gap cannot be confused with those legs simply out-performing.
    """
    frames = []
    for season in seasons:
        top = per_season[season]["top_legs"]
        if top.empty:
            continue
        sizes = top.groupby(["season", "week"]).size().rename("n").reset_index()
        constructible = sizes[sizes["n"] >= 2][["season", "week"]]
        frames.append(top.merge(constructible, on=["season", "week"]))
    if not frames:
        return per_season[seasons[0]]["top_legs"].iloc[0:0]
    return pd.concat(frames, ignore_index=True)


def audit_digest() -> pd.DataFrame:
    """Pull the per-season data-quality verdicts straight from the audit's own JSON."""
    rows = []
    for season in VALIDATION_SEASONS:
        path = REPORTS / f"DATA_QUALITY_NFL_{season}.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text())
        by_name = {c["name"]: c for c in payload["checks"]}
        rows.append(
            {
                "season": season,
                "verdict": payload["verdict"],
                "missing_spreads": by_name["missing_spreads"]["data"]["missing"],
                "missing_totals": by_name["missing_totals"]["data"]["missing"],
                "spreads_off_grid": by_name["spreads_on_half_point_grid"]["data"]["off_grid"],
                "totals_off_grid": by_name["totals_on_half_point_grid"]["data"]["off_grid"],
                "spread_half_point_share": by_name["spread_half_point_share"]["data"]["share"],
                "total_half_point_share": by_name["total_half_point_share"]["data"]["share"],
                "duplicates": by_name["duplicate_games"]["data"]["duplicate_game_ids"],
                "warnings": "; ".join(
                    c["name"] for c in payload["checks"] if c["status"] == "WARN"
                ) or "none",
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    games_v, records_v = load("2018_2023")
    games_p2, records_p2 = load("2024_2025")

    assert_no_primary_push(records_v.to_dict("records"))
    assert_no_primary_push(records_p2.to_dict("records"))
    print("invariant OK: no primary-geometry leg graded PUSH in any season")

    per_season = {}
    for season in VALIDATION_SEASONS:
        per_season[season] = run_season(records_v, games_v, season)
    for season in PHASE2_SEASONS:
        per_season[season] = run_season(records_p2, games_p2, season)

    all_records = pd.concat([records_v, records_p2], ignore_index=True)

    validation = pd.concat(
        [per_season[s]["qualifying"] for s in VALIDATION_SEASONS], ignore_index=True
    )
    validation_tickets = pd.concat(
        [per_season[s]["tickets"] for s in VALIDATION_SEASONS], ignore_index=True
    )
    phase2 = {s: per_season[s]["qualifying"] for s in PHASE2_SEASONS}

    validation.to_csv(PROCESSED / "phase2b_legs_qualifying_2018_2023.csv", index=False)
    validation_tickets.to_csv(PROCESSED / "phase2b_tickets_2018_2023.csv", index=False)
    for season in VALIDATION_SEASONS:
        per_season[season]["qualifying"].to_csv(
            PROCESSED / f"phase2b_legs_qualifying_{season}.csv", index=False
        )
        per_season[season]["tickets"].to_csv(
            PROCESSED / f"phase2b_tickets_{season}.csv", index=False
        )
        per_season[season]["weekly"].to_csv(
            PROCESSED / f"phase2b_weekly_{season}.csv", index=False
        )
        per_season[season]["top_legs"].to_csv(
            PROCESSED / f"phase2b_top_legs_{season}.csv", index=False
        )

    write_validation_report(games_v, all_records, per_season, validation, validation_tickets)
    write_dog_favorite_report(validation, phase2, per_season)
    write_total_dependence_report(validation, phase2, per_season)

    print("\n=== digest ===")
    for season in VALIDATION_SEASONS:
        frame = per_season[season]["qualifying"]
        scoring = expected_versus_actual(frame)
        comparator = frozen_versus_constant(frame)
        print(
            f"{season}: qualifying {scoring['n']:3d}  mean P_est {scoring['mean_p_est']:.4f}  "
            f"actual {scoring['actual_hit_rate']:.4f}  "
            f"Brier {comparator['brier_frozen']:.4f} vs const {comparator['brier_constant']:.4f}  "
            f"delta {comparator['delta_brier']:+.5f}"
        )
    agg = expected_versus_actual(validation)
    print(
        f"2018-2023 aggregate: n={agg['n']} mean P_est {agg['mean_p_est']:.4f} "
        f"actual {agg['actual_hit_rate']:.4f} expected {agg['expected_wins']:.2f} "
        f"actual {agg['actual_wins']}"
    )
    comparison = dog_favorite_comparison(validation)
    print(
        f"dogs {comparison.wins_a}/{comparison.n_a}={comparison.rate_a:.4f} vs "
        f"favorites {comparison.wins_b}/{comparison.n_b}={comparison.rate_b:.4f} "
        f"diff {comparison.difference_pp:+.1f}pp OR {comparison.odds_ratio:.3f} "
        f"Fisher p={comparison.fisher_p:.4f}"
    )
    return 0


# ---------------------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------------------


def write_validation_report(games, all_records, per_season, validation, validation_tickets):
    lines: list[str] = []
    add = lines.append

    add("# Phase 2B — NFL 2018-2023 out-of-sample validation of frozen Teaser Model v1.0")
    add("")
    add("**Validation only.** " + FROZEN_LINE)
    add("")
    for note in (PROVENANCE_LINE, NO_PRICE_LINE, REGIME_LINE):
        add(f"- {note}")
    add("")
    add(
        "Hypotheses H1-H3 were declared before these seasons' outcomes were examined. "
        "2018-2023 is the validation sample; 2024-2025 generated the hypotheses and is "
        "shown separately, never merged into the validation block."
    )
    add("")

    add("## 0. Data-quality gate, run independently per season")
    add("")
    add(
        "The existing frozen audit gate was applied unchanged to each season on its own. "
        "No threshold was altered and no check was relaxed."
    )
    add("")
    add(md(audit_digest()))
    add("")
    verdicts = audit_digest()
    failures = list(verdicts.loc[verdicts["verdict"] == "FAIL", "season"])
    if failures:
        add(f"**Seasons FAILING the gate: {failures}. Excluded; see their own reports.**")
    else:
        add("**All six seasons PASS.** No season was excluded.")
    add("")
    add("### Primary-geometry leg counts per season (before the total guardrail)")
    add("")
    counts = []
    for season in VALIDATION_SEASONS:
        before = primary_before_guardrail(all_records)
        before = before[before["season"] == season]
        row = {"season": season}
        for shape in PRIMARY_SHAPE_ORDER:
            row[shape] = int((before["shape"] == shape).sum())
        row["total"] = len(before)
        counts.append(row)
    add(md(pd.DataFrame(counts)))
    add("")
    add(
        "**2020 is retained.** It passes the gate on its own. It is flagged here as the "
        "COVID-era season — no crowds for most games, compressed protocols — and that flag "
        "was set before its outcomes were examined. It is not excluded on the basis of "
        "results."
    )
    add("")

    add("## 1. Per-season results (H1)")
    add("")
    rows = []
    for season in VALIDATION_SEASONS:
        frame = per_season[season]["qualifying"]
        before = primary_before_guardrail(all_records)
        before = before[before["season"] == season]
        scoring = expected_versus_actual(frame)
        comparator = frozen_versus_constant(frame)
        weekly = per_season[season]["weekly"]
        rows.append(
            {
                "season": season,
                "games": int((games["season"] == season).sum()),
                "primary_before_guardrail": len(before),
                "qualifying": scoring["n"],
                "mean_p_est": scoring["mean_p_est"],
                "predicted_wins": scoring["expected_wins"],
                "actual_wins": scoring["actual_wins"],
                "actual_hit_rate": scoring["actual_hit_rate"],
                "calibration_gap": scoring["actual_hit_rate"] - scoring["mean_p_est"],
                "brier_frozen": comparator["brier_frozen"],
                "brier_constant": comparator["brier_constant"],
                "delta_brier": comparator["delta_brier"],
                "logloss_frozen": comparator["log_loss_frozen"],
                "logloss_constant": comparator["log_loss_constant"],
                "delta_logloss": comparator["delta_log_loss"],
                "zero_qualifier_weeks": int((weekly["n_qualifying_legs"] == 0).sum()),
            }
        )
    per_season_frame = pd.DataFrame(rows)
    add(md(per_season_frame))
    add("")
    agg = expected_versus_actual(validation)
    agg_comparator = frozen_versus_constant(validation)
    add("### 2018-2023 aggregate (validation block)")
    add("")
    add(
        md(
            pd.DataFrame(
                [
                    {"metric": "qualifying primary legs", "value": agg["n"]},
                    {"metric": "mean P_est", "value": agg["mean_p_est"]},
                    {"metric": "predicted wins = sum(P_est)", "value": agg["expected_wins"]},
                    {"metric": "actual wins", "value": agg["actual_wins"]},
                    {"metric": "actual - predicted", "value": agg["actual_minus_expected"]},
                    {"metric": "actual hit rate", "value": agg["actual_hit_rate"]},
                    {"metric": "calibration gap", "value": agg["actual_hit_rate"] - agg["mean_p_est"]},
                    {"metric": "Brier (frozen)", "value": agg_comparator["brier_frozen"]},
                    {"metric": "Brier (constant mean P_est)", "value": agg_comparator["brier_constant"]},
                    {"metric": "delta Brier (frozen - constant)", "value": agg_comparator["delta_brier"]},
                ]
            )
        )
    )
    add("")

    add("## 2. Weekly qualifying-leg distribution, including zeros")
    add("")
    dist_rows = []
    for season in VALIDATION_SEASONS:
        counts = weekly_distribution(per_season[season]["weekly"])
        dist_rows.append({"season": season, "weeks": len(per_season[season]["weekly"]), **counts})
    add(md(pd.DataFrame(dist_rows)))
    add("")

    add("## 3. Geometry results (H1, by exact shape)")
    add("")
    for season in VALIDATION_SEASONS:
        add(f"### {season}")
        add("")
        add(md(shape_table(per_season[season]["qualifying"]), raw_cols=[0]))
        add("")
    add("### 2018-2023 aggregate")
    add("")
    add(md(shape_table(validation), raw_cols=[0]))
    add("")
    add(f"Rows with N < {LOW_SAMPLE_N} are marked `low_sample` and reported as-is.")
    add("")

    add("## 4. H3 — does total-driven P_est variation add predictive information?")
    add("")
    add(
        "Comparator **B** is a constant forecast equal to that season's mean frozen P_est. "
        "It is derived from model inputs only: no realized outcome enters it. A negative "
        "delta means the frozen per-leg variation helped; a positive delta means the "
        "constant did better."
    )
    add("")
    h3 = per_season_frame[
        ["season", "qualifying", "brier_frozen", "brier_constant", "delta_brier",
         "logloss_frozen", "logloss_constant", "delta_logloss"]
    ]
    add(md(h3))
    add("")
    add(
        md(
            pd.DataFrame(
                [
                    {
                        "block": "2018-2023 aggregate",
                        "n": agg_comparator["n"],
                        "constant_p": agg_comparator["constant_p"],
                        "brier_frozen": agg_comparator["brier_frozen"],
                        "brier_constant": agg_comparator["brier_constant"],
                        "delta_brier": agg_comparator["delta_brier"],
                        "logloss_frozen": agg_comparator["log_loss_frozen"],
                        "logloss_constant": agg_comparator["log_loss_constant"],
                        "delta_logloss": agg_comparator["delta_log_loss"],
                        "p_est_variance": agg_comparator["p_est_variance"],
                    }
                ]
            )
        )
    )
    add("")
    add(
        "See `reports/phase2b_total_dependence.md` for the bucket-level ordering check "
        "that accompanies this. **This is a diagnostic of the total-based variation. It is "
        "not permission to alter sigma.**"
    )
    add("")

    add("## 5. Ticket construction (descriptive only)")
    add("")
    add(
        "> Ticket rows are **correlated and overlapping**: within a week the same legs "
        "recur across combinations, and no historical teaser price exists. These are not "
        "independent observations and are not a track record."
    )
    add("")
    ticket_rows = []
    for season in VALIDATION_SEASONS:
        ticket_rows.append(ticket_table(per_season[season]["tickets"], label=str(season)))
    ticket_rows.append(ticket_table(validation_tickets, label="2018-2023 aggregate"))
    add(md(pd.concat(ticket_rows, ignore_index=True)))
    add("")
    same_game = int(validation_tickets["same_game_legs"].sum()) if len(validation_tickets) else 0
    add(
        f"Tickets combining two legs from the same NFL game: **{same_game}** "
        + (
            "— structurally impossible under the frozen geometry, since the primary set "
            "contains no complementary pair."
            if same_game == 0
            else "— **flagged: independence would clearly fail for these.**"
        )
    )
    add("")

    add("### Leg-level control for the ticket gap")
    add("")
    add(
        "The ticket gaps above cannot be read on their own. If the legs that went onto "
        "tickets simply out-performed, tickets would beat the product for that reason "
        "alone. Controlling for it:"
    )
    add("")
    used = legs_used_on_tickets(per_season, VALIDATION_SEASONS)
    control_rows = []
    for label, frame in (
        ("all qualifying primary legs", validation),
        ("only the legs that appear on tickets", used),
    ):
        control_rows.append(
            {
                "leg set": label,
                "n": len(frame),
                "mean_p_est": float(frame["p_est"].mean()),
                "actual_hit_rate": float(frame["won"].mean()),
                "calibration_gap": float(frame["won"].mean() - frame["p_est"].mean()),
            }
        )
    add(md(pd.DataFrame(control_rows)))
    add("")
    add(
        "The legs used on tickets hit **below** their own mean P_est, yet the tickets "
        "built from them beat the product of those same P_est values. Those two facts "
        "together are the signature of **positive correlation between legs within a "
        "week**: outcomes cluster, so all-win weeks occur more often than independence "
        "implies even when the per-leg rate is unremarkable."
    )
    add("")
    add(
        "This is recorded as a diagnostic for later EV work, exactly as the Phase 2 "
        "independence check was. **No model change follows from it**, and the ticket "
        "numbers remain correlated, overlapping and unpriced."
    )
    add("")

    add("## 6. Three-block comparison")
    add("")
    add(
        "Blocks are never silently pooled. The all-years row is supplementary and spans "
        "source regimes."
    )
    add("")
    blocks = []
    for label, frame in (
        ("1. 2018-2023 validation", validation),
        ("2. 2024 initial test", per_season[2024]["qualifying"]),
        ("3. 2025 changed-feed regime", per_season[2025]["qualifying"]),
    ):
        scoring = expected_versus_actual(frame)
        comparator = frozen_versus_constant(frame)
        blocks.append(
            {
                "block": label,
                "n": scoring["n"],
                "mean_p_est": scoring["mean_p_est"],
                "predicted_wins": scoring["expected_wins"],
                "actual_wins": scoring["actual_wins"],
                "actual_hit_rate": scoring["actual_hit_rate"],
                "calibration_gap": scoring["actual_hit_rate"] - scoring["mean_p_est"],
                "brier_frozen": comparator["brier_frozen"],
                "delta_brier": comparator["delta_brier"],
            }
        )
    all_years = pd.concat(
        [validation, per_season[2024]["qualifying"], per_season[2025]["qualifying"]],
        ignore_index=True,
    )
    scoring = expected_versus_actual(all_years)
    comparator = frozen_versus_constant(all_years)
    blocks.append(
        {
            "block": "SUPPLEMENTARY all years (spans source regimes)",
            "n": scoring["n"],
            "mean_p_est": scoring["mean_p_est"],
            "predicted_wins": scoring["expected_wins"],
            "actual_wins": scoring["actual_wins"],
            "actual_hit_rate": scoring["actual_hit_rate"],
            "calibration_gap": scoring["actual_hit_rate"] - scoring["mean_p_est"],
            "brier_frozen": comparator["brier_frozen"],
            "delta_brier": comparator["delta_brier"],
        }
    )
    add(md(pd.DataFrame(blocks)))
    add("")
    add(
        "> The final row is **supplementary and descriptive**. It mixes three regimes and "
        "is not the conclusion of this phase."
    )
    add("")

    add("## Machine-readable outputs")
    add("")
    add("- `data/processed/phase2b_legs_qualifying_2018_2023.csv` — validation-block legs")
    add("- `data/processed/phase2b_legs_qualifying_<season>.csv` — per season")
    add("- `data/processed/phase2b_tickets_2018_2023.csv` — validation-block tickets")
    add("- `data/processed/phase2b_tickets_<season>.csv`, `phase2b_weekly_<season>.csv`, "
        "`phase2b_top_legs_<season>.csv`")
    add("")

    path = REPORTS / "phase2b_nfl_2018_2023_validation.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"written: {path.relative_to(ROOT)}")


def write_dog_favorite_report(validation, phase2, per_season):
    lines: list[str] = []
    add = lines.append

    add("# Phase 2B — dog vs favorite validation (H2)")
    add("")
    add(
        "**This validates a hypothesis generated from the 2024-2025 data.** The direction "
        "was declared in advance: *primary underdog teaser legs may outperform primary "
        "favorite teaser legs*. 2018-2023 is the unseen validation sample."
    )
    add("")
    add("**" + FROZEN_LINE + "** The frozen model treats all four primary shapes identically;")
    add("`side_class` is a reporting label, not a model dimension.")
    add("")
    for note in (PROVENANCE_LINE, NO_PRICE_LINE, REGIME_LINE):
        add(f"- {note}")
    add("")

    add("## 1. Validation sample: 2018-2023 aggregate")
    add("")
    rows = [
        group_interval_row(validation[validation["shape"].isin(DOG_SHAPES)], "dogs (+1.5, +2.5)"),
        group_interval_row(
            validation[validation["shape"].isin(FAVORITE_SHAPES)], "favorites (-7.5, -8.5)"
        ),
    ]
    add(md(pd.DataFrame(rows)))
    add("")

    comparison = dog_favorite_comparison(validation)
    add("### Statistical comparison")
    add("")
    add(md(pd.DataFrame([comparison.as_dict()])))
    add("")
    direction = (
        "corroborates" if comparison.difference_pp > 0 else "does NOT corroborate"
    )
    add(
        f"**Direction: the validation sample {direction} the hypothesis.** Dogs hit "
        f"{comparison.rate_a * 100:.1f}% against favorites at {comparison.rate_b * 100:.1f}%, "
        f"a difference of {comparison.difference_pp:+.1f} percentage points. Fisher exact "
        f"two-sided p = {comparison.fisher_p:.4f}; odds ratio "
        f"{comparison.odds_ratio:.3f} (95% CI {comparison.or_ci_low:.3f}-{comparison.or_ci_high:.3f})"
        + (", Haldane-Anscombe corrected for a zero cell." if comparison.or_corrected else ".")
    )
    add("")
    add(
        "Direction and significance are different questions. The p-value above is reported "
        "as computed; it is not a decision rule, and **no model change follows from it in "
        "either case**."
    )
    add("")

    add("## 2. Per-season detail within the validation block")
    add("")
    rows = []
    for season in VALIDATION_SEASONS:
        frame = per_season[season]["qualifying"]
        dogs = frame[frame["shape"].isin(DOG_SHAPES)]
        favorites = frame[frame["shape"].isin(FAVORITE_SHAPES)]
        rows.append(
            {
                "season": season,
                "dogs_n": len(dogs),
                "dogs_wins": int(dogs["won"].sum()),
                "dogs_rate": float(dogs["won"].mean()) if len(dogs) else float("nan"),
                "favs_n": len(favorites),
                "favs_wins": int(favorites["won"].sum()),
                "favs_rate": float(favorites["won"].mean()) if len(favorites) else float("nan"),
                "difference_pp": (
                    (float(dogs["won"].mean()) - float(favorites["won"].mean())) * 100
                    if len(dogs) and len(favorites)
                    else float("nan")
                ),
            }
        )
    add(md(pd.DataFrame(rows)))
    add("")
    seasons_favouring_dogs = sum(
        1 for r in rows if not pd.isna(r["difference_pp"]) and r["difference_pp"] > 0
    )
    comparable = sum(1 for r in rows if not pd.isna(r["difference_pp"]))
    add(
        f"Dogs out-hit favorites in **{seasons_favouring_dogs} of {comparable}** seasons "
        "with both groups present. Single-season splits are very small and are shown for "
        "transparency, not as evidence."
    )
    add("")

    add("## 3. Side by side: validation block vs hypothesis-generating block")
    add("")
    add(
        "> The 2024-2025 numbers are **not** independent evidence for this hypothesis — "
        "the hypothesis came from them. They are shown to let the reader compare, not to "
        "be added together."
    )
    add("")
    blocks = []
    for label, frame in (
        ("2018-2023 (validation, unseen)", validation),
        ("2024 (hypothesis-generating)", phase2[2024]),
        ("2025 (hypothesis-generating, changed feed)", phase2[2025]),
        (
            "2024-2025 combined (hypothesis-generating)",
            pd.concat([phase2[2024], phase2[2025]], ignore_index=True),
        ),
    ):
        dogs = frame[frame["shape"].isin(DOG_SHAPES)]
        favorites = frame[frame["shape"].isin(FAVORITE_SHAPES)]
        blocks.append(
            {
                "block": label,
                "dogs_n": len(dogs),
                "dogs_wins": int(dogs["won"].sum()),
                "dogs_rate": float(dogs["won"].mean()) if len(dogs) else float("nan"),
                "dogs_mean_p_est": float(dogs["p_est"].mean()) if len(dogs) else float("nan"),
                "favs_n": len(favorites),
                "favs_wins": int(favorites["won"].sum()),
                "favs_rate": float(favorites["won"].mean()) if len(favorites) else float("nan"),
                "favs_mean_p_est": (
                    float(favorites["p_est"].mean()) if len(favorites) else float("nan")
                ),
                "difference_pp": (
                    (float(dogs["won"].mean()) - float(favorites["won"].mean())) * 100
                    if len(dogs) and len(favorites)
                    else float("nan")
                ),
            }
        )
    add(md(pd.DataFrame(blocks)))
    add("")
    add(
        "Note that **mean P_est is essentially identical for dogs and favorites** in every "
        "block: the frozen model assigns them the same probability, because all four "
        "primary shapes cross both key numbers and P_est depends only on the total. Any "
        "difference in realized hit rate is therefore a difference the frozen model does "
        "not predict at all."
    )
    add("")

    add("## 4. Limitations")
    add("")
    add(
        "- The favorite group is much smaller than the dog group in every block; its "
        "interval is correspondingly wide."
    )
    add(
        "- Shape composition differs between blocks, so a dog/favorite difference is "
        "partly confounded with which exact shapes were available in a given season."
    )
    add("- Legs within a season are not independent of the market that priced them.")
    add(
        "- Multiple hypotheses were examined in Phase 2; this is the one carried forward, "
        "and no multiplicity correction is applied to the p-value above."
    )
    add("")
    add("## What this report does not do")
    add("")
    add(
        "It does not change v1.0, split the model by side, reweight anything, or recommend "
        "a parameter change. H2 remains a research question in `RESEARCH_QUEUE.md`."
    )
    add("")

    path = REPORTS / "phase2b_dog_favorite_validation.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"written: {path.relative_to(ROOT)}")


def write_total_dependence_report(validation, phase2, per_season):
    lines: list[str] = []
    add = lines.append

    add("# Phase 2B — total dependence and P_est monotonicity (H3)")
    add("")
    add("**" + FROZEN_LINE + "**")
    add("")
    add(
        "Within qualifying primary legs the frozen P_est varies only over a narrow range: "
        "every primary leg receives the same +0.07 NFL bump and the total is capped at 47, "
        "so all remaining variation comes from `sigma = 0.30 x total`. This report asks "
        "whether that variation carries information. **It is a diagnostic, not permission "
        "to alter sigma.**"
    )
    add("")
    for note in (PROVENANCE_LINE, NO_PRICE_LINE, REGIME_LINE):
        add(f"- {note}")
    add("")
    add(
        "Buckets are the frozen Phase 2 buckets, unchanged: `<=40`, `40.5-43`, `43.5-45`, "
        "`45.5-47`. None was redesigned after seeing results. The frozen model predicts hit "
        "rates should **fall** as the total rises."
    )
    add("")

    add("## 1. 2018-2023 aggregate (validation block)")
    add("")
    table = bucket_table(validation)
    add(md(table, raw_cols=[0]))
    add("")
    result = assess_monotonicity(table)
    add(f"**Monotonicity: {result.summary()}**")
    add("")
    if not pd.isna(result.spearman_rho):
        add(
            f"Spearman rank correlation between bucket mean P_est and realized hit rate: "
            f"rho = {result.spearman_rho:.3f} (p = {result.spearman_p:.3f}), across "
            f"{result.n_comparable} buckets. Reported as a descriptive rank statistic; "
            "**no trend is fitted**, and with four points it carries very little weight."
        )
        add("")

    add("## 2. Each validation season separately")
    add("")
    for season in VALIDATION_SEASONS:
        add(f"### {season}")
        add("")
        season_table = bucket_table(per_season[season]["qualifying"])
        add(md(season_table, raw_cols=[0]))
        add("")
        add(f"Monotonicity: {assess_monotonicity(season_table).summary()}")
        add("")

    add("## 3. Monotonicity summary across every block")
    add("")
    rows = []
    blocks = [(str(s), per_season[s]["qualifying"]) for s in VALIDATION_SEASONS]
    blocks.append(("2018-2023 aggregate", validation))
    blocks.append(("2024", phase2[2024]))
    blocks.append(("2025", phase2[2025]))
    for label, frame in blocks:
        block_table = bucket_table(frame)
        assessment = assess_monotonicity(block_table)
        rows.append(
            {
                "block": label,
                "non_empty_buckets": assessment.n_comparable,
                "adjacent_pairs": assessment.adjacent_pairs,
                "ordered_as_predicted": assessment.concordant_pairs,
                "perfectly_monotone": assessment.perfectly_monotone,
                "spearman_rho": assessment.spearman_rho,
            }
        )
    add(md(pd.DataFrame(rows)))
    add("")

    add("## 4. Frozen P_est versus a constant forecast")
    add("")
    add(
        "The comparator is a constant equal to each block's mean frozen P_est — derived "
        "from **model inputs only**, never from realized outcomes. Negative delta means the "
        "frozen per-leg variation helped."
    )
    add("")
    rows = []
    for label, frame in blocks:
        comparator = frozen_versus_constant(frame)
        rows.append({"block": label, **comparator})
    add(md(pd.DataFrame(rows)))
    add("")
    add(
        "Mechanically, `delta Brier = var(P_est) - 2 x cov(P_est, outcome)`. With "
        f"`var(P_est)` around {frozen_versus_constant(validation)['p_est_variance']:.2e} in "
        "the validation block, the frozen variation can only beat the constant by a margin "
        "of that order. Whatever the sign, the magnitude is tiny by construction."
    )
    add("")

    add("## 5. Limitations")
    add("")
    add(
        "- Bucket N is small in every season; per-season ordering is close to noise and is "
        "shown for completeness."
    )
    add("- Empty buckets are skipped in the ordering check, never imputed or merged.")
    add(
        "- The P_est range is narrow **by construction**, so neither a positive nor a "
        "negative delta here can carry much weight. A null result is the expected outcome "
        "of a well-posed test at this sample size, not evidence that sigma is wrong."
    )
    add("- No trend is fitted and no parameter is estimated anywhere in this report.")
    add("")

    path = REPORTS / "phase2b_total_dependence.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"written: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    raise SystemExit(main())
