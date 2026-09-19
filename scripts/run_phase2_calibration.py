#!/usr/bin/env python3
"""Phase 2 — calibration of frozen Teaser Model v1.0 against NFL 2024 and 2025 outcomes.

Calibration only. This script attaches no price, computes no EV, and reports no ROI.

It stops hard if any primary-geometry leg grades PUSH, which the geometry makes impossible.

Usage:
    python scripts/run_phase2_calibration.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teaser_model_v1.analysis.backtest import (  # noqa: E402
    build_leg_records,
    primary_before_guardrail,
    qualifying_primary,
    run_season,
)
from teaser_model_v1.analysis.calibration import (  # noqa: E402
    LOW_SAMPLE_N,
    P_EST_BUCKETS,
    PRIMARY_SHAPE_ORDER,
    SHAPE_DESCRIPTIONS,
    TOTAL_BUCKETS,
    brier_score,
    calibration_slope_is_reasonable,
    clopper_pearson_interval,
    expected_versus_actual,
    summarise_by,
    summarise_group,
)
from teaser_model_v1.analysis.grading import assert_no_primary_push  # noqa: E402

SEASONS = (2024, 2025)
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

PROVENANCE_LINE = (
    "Lines are **archived reference lines** (`archived_reference_line`). The source "
    "documents no capture time; commit-history inspection shows the value is whatever a "
    "periodic scrape caught last before the final score landed. It is **not** a closing "
    "line and supports no CLV claim."
)

REGIME_LINE = (
    "**2024 and 2025 run on different upstream line feeds.** Opportunity counts are not "
    "comparable across the two seasons, and differences in leg volume are a property of "
    "the data source, not of the model. See "
    "`reports/nfl_line_composition_investigation.md`."
)

NO_PRICE_LINE = (
    "No historical teaser menu prices exist in this source and none have been invented. "
    "No EV, break-even or ROI figure appears in this phase."
)


def md(frame: pd.DataFrame, raw_cols=None) -> str:
    """Markdown table. *raw_cols* are column indices tabulate must not parse as numbers.

    Shape labels like ``+1.5`` are strings and must stay strings, or the leading sign is
    lost and a favorite shape becomes indistinguishable from an underdog one.
    """
    kwargs = {"index": False, "floatfmt": ".4g"}
    if raw_cols:
        kwargs["disable_numparse"] = raw_cols
    return frame.to_markdown(**kwargs)


def pct(value) -> str:
    return "—" if pd.isna(value) else f"{value * 100:.1f}%"


def signed_pct(value) -> str:
    return "—" if pd.isna(value) else f"{value * 100:+.1f}pp"


# ---------------------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------------------


def season_summary(records, games, season, season_run) -> dict:
    games_season = games[games["season"] == season]
    before = primary_before_guardrail(records)
    before = before[before["season"] == season]
    after = season_run["qualifying"]
    weekly = season_run["weekly"]

    return {
        "season": season,
        "games_in_source": len(games_season),
        "legs_in_source": len(records[records["season"] == season]),
        "primary_legs_before_total_filter": len(before),
        "qualifying_primary_legs": len(after),
        "dropped_by_guardrail": len(before) - len(after),
        "weeks": len(weekly),
        "zero_qualifier_weeks": int((weekly["n_qualifying_legs"] == 0).sum()),
        "mean_qualifying_legs_per_week": float(weekly["n_qualifying_legs"].mean()),
        "median_qualifying_legs_per_week": float(weekly["n_qualifying_legs"].median()),
        "max_qualifying_legs_in_a_week": int(weekly["n_qualifying_legs"].max()),
    }


def shape_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for shape in PRIMARY_SHAPE_ORDER:
        subset = frame[frame["shape"] == shape]
        result = summarise_group(shape, subset).as_dict()
        result["geometry"] = SHAPE_DESCRIPTIONS[shape]
        rows.append(result)
    out = pd.DataFrame(rows)
    out = out.rename(columns={"group": "shape"})
    return out[
        [
            "shape",
            "geometry",
            "n",
            "mean_p_est",
            "actual_hit_rate",
            "calibration_gap",
            "ci95_low",
            "ci95_high",
            "low_sample",
        ]
    ]


def bucket_table(frame: pd.DataFrame, column: str, order) -> pd.DataFrame:
    out = summarise_by(frame, column, order)
    out = out.rename(columns={"group": "bucket"})
    return out[
        [
            "bucket",
            "n",
            "mean_p_est",
            "actual_hit_rate",
            "calibration_gap",
            "ci95_low",
            "ci95_high",
            "low_sample",
        ]
    ]


def weekly_distribution(weekly: pd.DataFrame) -> pd.DataFrame:
    buckets = [("0", 0, 0), ("1", 1, 1), ("2", 2, 2), ("3", 3, 3), (">=4", 4, None)]
    rows = []
    for label, low, high in buckets:
        mask = weekly["n_qualifying_legs"] >= low
        if high is not None:
            mask &= weekly["n_qualifying_legs"] <= high
        rows.append({"qualifying_legs_in_week": label, "weeks": int(mask.sum())})
    return pd.DataFrame(rows)


def ticket_table(tickets: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for size in (2, 3):
        subset = tickets[tickets["n_legs"] == size] if len(tickets) else tickets
        n = len(subset)
        if n == 0:
            rows.append(
                {
                    "ticket_size": f"{size}-team",
                    "n_tickets": 0,
                    "mean_predicted_p_ticket": float("nan"),
                    "realized_hit_rate": float("nan"),
                    "gap": float("nan"),
                    "ci95_low": float("nan"),
                    "ci95_high": float("nan"),
                    "same_game_tickets": 0,
                }
            )
            continue
        wins = int(subset["won"].sum())
        predicted = float(subset["predicted_p_ticket"].mean())
        realized = wins / n
        low, high = clopper_pearson_interval(wins, n)
        rows.append(
            {
                "ticket_size": f"{size}-team",
                "n_tickets": n,
                "mean_predicted_p_ticket": predicted,
                "realized_hit_rate": realized,
                "gap": realized - predicted,
                "ci95_low": low,
                "ci95_high": high,
                "same_game_tickets": int(subset["same_game_legs"].sum()),
            }
        )
    return pd.DataFrame(rows)


def limitations_block(per_season, pooled_qualifying) -> list[str]:
    """Limitations and anomalies, computed from the data rather than asserted."""
    lines = []
    add = lines.append

    add("## Limitations and anomalies")
    add("")
    add(
        "1. **Sample size.** "
        + ", ".join(
            f"{s}: {len(per_season[s]['qualifying'])} qualifying primary legs"
            for s in SEASONS
        )
        + f" ({len(pooled_qualifying)} across both). At these counts a shape-level hit "
        "rate has a confidence interval tens of percentage points wide, which is why "
        "every table carries an exact interval. Individual shape gaps are not "
        "distinguishable from noise."
    )
    add("")
    add(
        "2. **Two source regimes.** The seasons are not a homogeneous sample. Pooled rows "
        "are supplementary only."
    )
    add("")

    thin = []
    for season in SEASONS:
        frame = per_season[season]["qualifying"]
        for shape in PRIMARY_SHAPE_ORDER:
            n = int((frame["shape"] == shape).sum())
            if n < LOW_SAMPLE_N:
                thin.append(f"{season} {shape}: N={n}")
    add(
        "3. **Thin shapes.** Reported as-is, never merged: "
        + "; ".join(thin)
        + ". These carry essentially no calibration information on their own."
    )
    add("")

    playoff_note = []
    for season in SEASONS:
        weekly = per_season[season]["weekly"]
        post = weekly[weekly["week"] > 18]
        playoff_note.append(
            f"{season}: {int(post['n_qualifying_legs'].sum())} qualifying legs across "
            f"{len(post)} postseason weeks"
        )
    add(
        "4. **Postseason weeks contribute almost nothing.** "
        + "; ".join(playoff_note)
        + ". Playoff games rarely combine primary geometry with a total at or below 47, "
        "so the weekly distribution is effectively a regular-season distribution with "
        "structural zeros appended. This is a property of the frozen filters, not a data "
        "defect."
    )
    add("")
    add(
        "5. **P_est occupies a narrow band by construction.** Every qualifying primary leg "
        "crosses both key numbers, so the bump is a constant +0.07 and P_est is a monotone "
        "function of the total alone. Combined with the total ≤ 47 guardrail, observed "
        f"P_est spans {pooled_qualifying['p_est'].min():.4f}-"
        f"{pooled_qualifying['p_est'].max():.4f}. Two of the four predeclared P_est "
        "buckets are therefore structurally unreachable for qualifying legs and are "
        "reported empty. No bucket was redesigned."
    )
    add("")
    add(
        "6. **Ticket rows are not independent observations.** Within a week the same legs "
        "recur across combinations, and no historical teaser price exists. Ticket hit "
        "rates are descriptive only."
    )
    add("")
    add(
        "7. **No market-quality measurement is possible from this source.** Lines carry no "
        "documented capture time, so CLV and line movement are out of reach. That track "
        "requires our own timestamped capture during 2026."
    )
    add("")
    return lines


# ---------------------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------------------


def season_report(season, summary, qualifying, season_run) -> str:
    weekly = season_run["weekly"]
    tickets = season_run["tickets"]
    scoring = expected_versus_actual(qualifying)
    slope_ok, slope_reason = calibration_slope_is_reasonable(qualifying)

    lines: list[str] = []
    add = lines.append

    add(f"# Phase 2 — NFL {season} calibration of frozen Teaser Model v1.0")
    add("")
    add(
        "**Calibration only.** No price, no EV, no ROI. Every probability below is a "
        "**model-estimated hit probability**, never an objective or true probability."
    )
    add("")
    add(f"- {PROVENANCE_LINE}")
    add(f"- {NO_PRICE_LINE}")
    add(f"- {REGIME_LINE}")
    add("")

    add("## A. Season summary")
    add("")
    add(
        md(
            pd.DataFrame(
                [{"metric": k, "value": v} for k, v in summary.items() if k != "season"]
            )
        )
    )
    add("")

    add("## B. Results by exact primary shape")
    add("")
    add("Calibration gap = actual hit rate − mean P_est. Positive means the legs won more")
    add("often than the frozen model expected. Intervals are exact (Clopper–Pearson) 95%.")
    add("")
    add(md(shape_table(qualifying), raw_cols=[0]))
    add("")
    add(f"Rows with N < {LOW_SAMPLE_N} are marked `low_sample` and are reported as-is; no")
    add("bucket was merged after seeing outcomes.")
    add("")

    add("## C. Results by game-total bucket")
    add("")
    add(md(bucket_table(qualifying, "total_bucket", [b[0] for b in TOTAL_BUCKETS]), raw_cols=[0]))
    add("")

    add("## D. Results by predeclared P_est bucket")
    add("")
    add("Buckets were fixed before any outcome was observed. Empty buckets are left empty.")
    add("")
    add(md(bucket_table(qualifying, "p_est_bucket", [b[0] for b in P_EST_BUCKETS]), raw_cols=[0]))
    add("")

    add("## E. Proper scoring")
    add("")
    add(
        md(
            pd.DataFrame(
                [
                    {"metric": "qualifying primary legs", "value": scoring["n"]},
                    {"metric": "mean P_est", "value": scoring["mean_p_est"]},
                    {"metric": "expected wins = sum(P_est)", "value": scoring["expected_wins"]},
                    {"metric": "actual wins", "value": scoring["actual_wins"]},
                    {"metric": "actual − expected", "value": scoring["actual_minus_expected"]},
                    {"metric": "actual hit rate", "value": scoring["actual_hit_rate"]},
                    {"metric": "Brier score", "value": scoring["brier_score"]},
                ]
            )
        )
    )
    add("")
    if slope_ok:
        add("Calibration intercept/slope: sample is adequate; see the comparison report.")
    else:
        add(
            f"**Calibration intercept/slope omitted.** {slope_reason.capitalize()}. "
            "Reporting a slope here would be noise presented as a finding, so it is left "
            "out rather than caveated."
        )
    add("")

    add("## F. Weekly top-four construction")
    add("")
    add("Legs ranked within each week by full-precision P_est; top four retained.")
    add("No EV or pricing is attached in Phase 2.")
    add("")
    add(md(weekly_distribution(weekly), raw_cols=[0]))
    add("")
    add(
        f"- Constructible weeks (≥2 qualifying legs): "
        f"**{int(weekly['constructible'].sum())}** of {len(weekly)}"
    )
    add(f"- 2-team tickets constructible: **{int(weekly['n_tickets_2team'].sum())}**")
    add(f"- 3-team tickets constructible: **{int(weekly['n_tickets_3team'].sum())}**")
    add("")
    add("### Per-week detail")
    add("")
    add(md(weekly))
    add("")

    add("## G. Ticket hit rates and independence diagnostic")
    add("")
    add(
        "> **Descriptive only.** These tickets are not independent observations: no "
        "historical teaser price exists, tickets within a week are correlated, and the "
        "same legs appear in many combinations. Do not read these as a track record."
    )
    add("")
    add(md(ticket_table(tickets)))
    add("")
    same_game = int(tickets["same_game_legs"].sum()) if len(tickets) else 0
    add(
        f"- Tickets combining two legs from the same NFL game: **{same_game}**. "
        + (
            "Zero, as the frozen geometry requires: the primary set contains no "
            "complementary pair, so a game can contribute at most one primary leg."
            if same_game == 0
            else "**Non-zero — independence would clearly fail for these. Flagged.**"
        )
    )
    add("")

    add("## Limitations")
    add("")
    add(
        f"- Sample: **{len(qualifying)} qualifying primary legs** in {season}. Confidence "
        "intervals in every table above are wide; individual shape and bucket gaps are not "
        "distinguishable from noise at this size."
    )
    add(
        "- P_est spans only "
        f"{qualifying['p_est'].min():.4f}-{qualifying['p_est'].max():.4f} by construction "
        "(constant bump, total capped at 47), so two predeclared P_est buckets are "
        "structurally unreachable and reported empty."
    )
    add(
        f"- Postseason weeks contribute "
        f"{int(weekly[weekly['week'] > 18]['n_qualifying_legs'].sum())} qualifying legs; "
        "the weekly distribution is effectively regular-season with structural zeros."
    )
    add("- Ticket rows are correlated and unpriced; see §G.")
    add("- No CLV or line-movement measurement is possible from this source.")
    add("")
    add("## Machine-readable outputs")
    add("")
    add(f"- `data/processed/phase2_legs_all_{season}.csv` — every graded leg")
    add(f"- `data/processed/phase2_legs_qualifying_{season}.csv` — qualifying primary legs")
    add(f"- `data/processed/phase2_top_legs_{season}.csv` — weekly top-four selections")
    add(f"- `data/processed/phase2_tickets_{season}.csv` — every constructible ticket")
    add(f"- `data/processed/phase2_weekly_{season}.csv` — weekly counts including zeros")
    add("")
    return "\n".join(lines) + "\n"


def comparison_report(summaries, per_season, pooled_qualifying, pooled_tickets) -> str:
    lines: list[str] = []
    add = lines.append

    add("# Phase 2 — NFL 2024 vs 2025 comparison")
    add("")
    add("**Calibration only.** No price, no EV, no ROI.")
    add("")
    add(f"- {REGIME_LINE}")
    add(f"- {PROVENANCE_LINE}")
    add(f"- {NO_PRICE_LINE}")
    add("")

    add("## A. Season summaries, side by side")
    add("")
    metrics = [k for k in summaries[SEASONS[0]] if k != "season"]
    add(
        md(
            pd.DataFrame(
                [
                    {"metric": m, **{str(s): summaries[s][m] for s in SEASONS}}
                    for m in metrics
                ]
            )
        )
    )
    add("")
    add(
        "> Do **not** read the difference in opportunity count as model performance. The "
        "2025 feed places far more lines on ±1.5 and ±8.5 than the 2024 feed did, for "
        "reasons documented in the line-composition investigation."
    )
    add("")

    add("## B. Shape-level calibration, by season")
    add("")
    for season in SEASONS:
        add(f"### {season}")
        add("")
        add(md(shape_table(per_season[season]["qualifying"]), raw_cols=[0]))
        add("")

    add("### Supplementary: 2024+2025 pooled")
    add("")
    add(
        "> **Supplementary descriptive statistic only. Spans two source regimes.** This "
        "row is not the primary conclusion of Phase 2 and must not be quoted as though it "
        "were a single homogeneous sample."
    )
    add("")
    add(md(shape_table(pooled_qualifying), raw_cols=[0]))
    add("")

    add("## C. Total-bucket calibration, by season")
    add("")
    for season in SEASONS:
        add(f"### {season}")
        add("")
        add(md(bucket_table(per_season[season]["qualifying"], "total_bucket",
                            [b[0] for b in TOTAL_BUCKETS]), raw_cols=[0]))
        add("")

    add("## D. P_est-bucket calibration, by season")
    add("")
    for season in SEASONS:
        add(f"### {season}")
        add("")
        add(md(bucket_table(per_season[season]["qualifying"], "p_est_bucket",
                            [b[0] for b in P_EST_BUCKETS]), raw_cols=[0]))
        add("")

    add("## E. Proper scoring, by season")
    add("")
    rows = []
    for season in SEASONS:
        scoring = expected_versus_actual(per_season[season]["qualifying"])
        rows.append({"season": season, **scoring})
    pooled_scoring = expected_versus_actual(pooled_qualifying)
    rows.append({"season": "pooled (2 regimes)", **pooled_scoring})
    add(md(pd.DataFrame(rows)))
    add("")
    slope_ok, slope_reason = calibration_slope_is_reasonable(pooled_qualifying)
    if not slope_ok:
        add(
            f"**Calibration intercept/slope omitted for every cut, pooled included.** "
            f"{slope_reason.capitalize()}."
        )
        add("")
        add(
            "The reason is structural, not incidental: every qualifying primary leg "
            "crosses both key numbers, so the bump is a constant and P_est is a monotone "
            "function of the game total alone. With the guardrail capping totals at 47, "
            "P_est occupies a narrow band. A logistic slope fitted across that band would "
            "be dominated by noise."
        )
        add("")

    add("## F. Weekly qualifying-leg distribution, by season")
    add("")
    dist = pd.DataFrame({"qualifying_legs_in_week": ["0", "1", "2", "3", ">=4"]})
    for season in SEASONS:
        counts = weekly_distribution(per_season[season]["weekly"])
        dist[str(season)] = counts["weeks"].values
    add(md(dist, raw_cols=[0]))
    add("")

    add("## G. Ticket diagnostics, by season")
    add("")
    add(
        "> **Descriptive only**, for all the reasons in the season reports: no prices, "
        "correlated tickets within a week, repeated legs across combinations."
    )
    add("")
    for season in SEASONS:
        add(f"### {season}")
        add("")
        add(md(ticket_table(per_season[season]["tickets"])))
        add("")

    add("### Supplementary: pooled tickets (two regimes)")
    add("")
    add(md(ticket_table(pooled_tickets)))
    add("")

    add("## H. Independence diagnostic")
    add("")
    add(
        "The frozen ticket formula multiplies leg P_est values, which assumes "
        "independence. Comparing the product against the realized rate:"
    )
    add("")
    rows = []
    for season in SEASONS:
        table = ticket_table(per_season[season]["tickets"])
        for _, row in table.iterrows():
            rows.append(
                {
                    "season": season,
                    "ticket_size": row["ticket_size"],
                    "n_tickets": row["n_tickets"],
                    "predicted (product of P_est)": row["mean_predicted_p_ticket"],
                    "realized": row["realized_hit_rate"],
                    "gap": row["gap"],
                    "same_game_tickets": row["same_game_tickets"],
                }
            )
    add(md(pd.DataFrame(rows)))
    add("")
    total_same_game = int(pooled_tickets["same_game_legs"].sum()) if len(pooled_tickets) else 0
    add(
        f"**Tickets containing two legs from the same NFL game: {total_same_game}.** "
        + (
            "This is a structural consequence of the frozen geometry, not luck: the "
            "primary set {+1.5, +2.5, −7.5, −8.5} contains no complementary pair, so if "
            "one side of a game is primary the other side cannot be. Independence is "
            "therefore not violated by same-game pairing in any week."
            if total_same_game == 0
            else "**Flagged separately — independence would clearly fail for these.**"
        )
    )
    add("")
    add(
        "This diagnostic is recorded for later EV work. **No model change follows from "
        "it.** The v1.0 ticket formula stays as specified."
    )
    add("")
    lines.extend(limitations_block(per_season, pooled_qualifying))

    add("## What Phase 2 does not contain")
    add("")
    add("No price, EV, break-even or ROI figure. No hypothetical-price sensitivity.")
    add("No CFB. No secondary NFL shapes. No fitted or recalibrated parameter.")
    add("No recommended model change. Teaser Model v1.0 is unchanged by this phase.")
    add("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------------------


def main() -> int:
    games = pd.read_csv(PROCESSED / "nfl_games_2024_2025.csv")
    legs_frame = pd.read_csv(PROCESSED / "nfl_legs_2024_2025.csv")

    records = build_leg_records(legs_frame)

    # Hard stop: a primary leg must never be able to push.
    assert_no_primary_push(records.to_dict("records"))
    print("invariant OK: no primary-geometry leg graded PUSH")

    summaries, per_season = {}, {}
    for season in SEASONS:
        season_run = run_season(records, games, season)
        summaries[season] = season_summary(records, games, season, season_run)
        per_season[season] = season_run

        records[records["season"] == season].to_csv(
            PROCESSED / f"phase2_legs_all_{season}.csv", index=False
        )
        season_run["qualifying"].to_csv(
            PROCESSED / f"phase2_legs_qualifying_{season}.csv", index=False
        )
        season_run["top_legs"].to_csv(
            PROCESSED / f"phase2_top_legs_{season}.csv", index=False
        )
        season_run["tickets"].to_csv(
            PROCESSED / f"phase2_tickets_{season}.csv", index=False
        )
        season_run["weekly"].to_csv(
            PROCESSED / f"phase2_weekly_{season}.csv", index=False
        )

        path = REPORTS / f"phase2_nfl_{season}_calibration.md"
        path.write_text(
            season_report(season, summaries[season], season_run["qualifying"], season_run)
        )
        print(f"written: {path.relative_to(ROOT)}")

    pooled_qualifying = pd.concat(
        [per_season[s]["qualifying"] for s in SEASONS], ignore_index=True
    )
    pooled_tickets = pd.concat(
        [per_season[s]["tickets"] for s in SEASONS], ignore_index=True
    )

    path = REPORTS / "phase2_nfl_comparison.md"
    path.write_text(
        comparison_report(summaries, per_season, pooled_qualifying, pooled_tickets)
    )
    print(f"written: {path.relative_to(ROOT)}")

    # Console digest
    print("\n=== digest ===")
    for season in SEASONS:
        s = summaries[season]
        scoring = expected_versus_actual(per_season[season]["qualifying"])
        print(
            f"{season}: primary before guardrail {s['primary_legs_before_total_filter']}, "
            f"qualifying {s['qualifying_primary_legs']}, "
            f"mean P_est {scoring['mean_p_est']:.4f}, "
            f"actual {scoring['actual_hit_rate']:.4f}, "
            f"expected wins {scoring['expected_wins']:.2f} vs actual {scoring['actual_wins']}, "
            f"Brier {scoring['brier_score']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
