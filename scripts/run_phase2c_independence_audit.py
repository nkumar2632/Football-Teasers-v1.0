#!/usr/bin/env python3
"""Phase 2C — audit of the independence assumption behind ticket probability.

Diagnostic only. No EV, no ROI, no price, no fitted probability, no correction applied.
Teaser Model v1.0 is unchanged; `P_ticket` remains the product of leg `P_est` values.

Usage:
    python scripts/run_phase2c_independence_audit.py [--sims 100000]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teaser_model_v1.analysis.backtest import build_leg_records, run_season  # noqa: E402
from teaser_model_v1.analysis.dependence import (  # noqa: E402
    DEFAULT_SEED,
    DEFAULT_SIMULATIONS,
    MIN_STRATUM_SIZE,
    all_win_summary,
    make_block,
    monte_carlo_null,
    overlap_stats,
    pair_summary,
    permutation_test,
    same_week_pairs,
    week_all_win,
    week_bootstrap_ticket_rate,
)

PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

VALIDATION = tuple(range(2018, 2024))
ALL_SEASONS = tuple(range(2018, 2026))

FROZEN = (
    "**Teaser Model v1.0 is unchanged by this audit.** `P_ticket` remains the product of "
    "leg `P_est` values. Nothing here fits a probability, applies a correlation "
    "correction, or proposes a new formula."
)
NO_PRICE = (
    "No teaser prices exist in this source and none have been invented. No EV, ROI or "
    "payout figure appears anywhere in this phase."
)
REGIME = (
    "**Three source regimes.** 2018-2023 and 2024 sit on the pre-2025 archived line feed; "
    "2025 sits on a different feed. Blocks are reported separately; the all-years row is "
    "supplementary. See `reports/nfl_line_composition_investigation.md`."
)
PROVENANCE = (
    "Lines are archived reference lines with no documented capture time. They are not "
    "closing lines."
)
OVERLAP_WARNING = (
    "> Tickets are **not independent observations**. Within a week they share legs, and "
    "shared legs are exactly the mechanism under test. Every interval below that concerns "
    "a ticket statistic is either a simulation interval over the whole board or a "
    "week-clustered bootstrap; no standard error treats tickets as independent draws."
)


def md(frame: pd.DataFrame, raw_cols=None) -> str:
    kwargs = {"index": False, "floatfmt": ".4g"}
    if raw_cols:
        kwargs["disable_numparse"] = raw_cols
    return frame.to_markdown(**kwargs)


def load_runs() -> dict:
    runs = {}
    for tag, seasons in (("2018_2023", VALIDATION), ("2024_2025", (2024, 2025))):
        games = pd.read_csv(PROCESSED / f"nfl_games_{tag}.csv")
        records = build_leg_records(pd.read_csv(PROCESSED / f"nfl_legs_{tag}.csv"))
        for season in seasons:
            runs[season] = run_season(records, games, season)
    return runs


def concat(runs, seasons, key):
    return pd.concat([runs[s][key] for s in seasons], ignore_index=True)


def build_blocks(runs) -> dict:
    blocks = {}
    for season in ALL_SEASONS:
        blocks[str(season)] = make_block(
            str(season), runs[season]["qualifying"], runs[season]["tickets"]
        )
    blocks["2018-2023 validation"] = make_block(
        "2018-2023 validation",
        concat(runs, VALIDATION, "qualifying"),
        concat(runs, VALIDATION, "tickets"),
    )
    blocks["2024"] = blocks["2024"]
    blocks["2025"] = blocks["2025"]
    blocks["SUPPLEMENTARY 2018-2025 all years"] = make_block(
        "SUPPLEMENTARY 2018-2025 all years",
        concat(runs, ALL_SEASONS, "qualifying"),
        concat(runs, ALL_SEASONS, "tickets"),
    )
    return blocks


MAIN_BLOCKS = ("2018-2023 validation", "2024", "2025", "SUPPLEMENTARY 2018-2025 all years")


# ---------------------------------------------------------------------------------------
# Section 1 — reproduce the anomaly
# ---------------------------------------------------------------------------------------


def anomaly_table(blocks, labels) -> pd.DataFrame:
    rows = []
    for label in labels:
        block = blocks[label]
        legs, tickets = block.legs, block.tickets
        row = {
            "block": label,
            "qualifying_legs": len(legs),
            "mean_leg_p_est": float(legs["p_est"].mean()),
            "actual_leg_hit_rate": float(legs["won"].mean()),
            "leg_gap_pp": float((legs["won"].mean() - legs["p_est"].mean()) * 100),
        }
        for size in (2, 3):
            subset = tickets[tickets["n_legs"] == size]
            row[f"n_{size}team"] = len(subset)
            row[f"mean_product_p_{size}team"] = (
                float(subset["predicted_p_ticket"].mean()) if len(subset) else float("nan")
            )
            row[f"realized_{size}team"] = (
                float(subset["won"].mean()) if len(subset) else float("nan")
            )
            row[f"gap_pp_{size}team"] = (
                float((subset["won"].mean() - subset["predicted_p_ticket"].mean()) * 100)
                if len(subset)
                else float("nan")
            )
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------------------


def ticket_leg_frame(block) -> pd.DataFrame:
    """The distinct legs that actually appear on at least one ticket in the block."""
    used = {leg for ids in block.tickets["leg_ids"] for leg in ids.split("|")}
    return block.legs[block.legs["leg_id"].isin(used)].drop_duplicates("leg_id")


def marginal_benchmark(blocks, labels) -> pd.DataFrame:
    """Compare observed ticket rates against r^k, where r is the realized leg hit rate.

    ``r`` is the hit rate of the legs that actually appear on tickets. ``r^k`` is what a
    k-leg ticket would hit if those same legs were arranged **independently** across the
    board. It uses no `P_est` at all, so it isolates arrangement from calibration: if the
    observed rate exceeds r^k, the wins are more clustered than a random arrangement of
    the same wins, whatever the frozen probabilities say.
    """
    rows = []
    for label in labels:
        block = blocks[label]
        used = ticket_leg_frame(block)
        r = float(used["won"].mean()) if len(used) else float("nan")
        for size in (2, 3):
            subset = block.tickets[block.tickets["n_legs"] == size]
            if subset.empty:
                continue
            rows.append(
                {
                    "block": label,
                    "ticket_size": f"{size}-team",
                    "ticket_leg_hit_rate_r": r,
                    "independence_benchmark_r_pow_k": r**size,
                    "product_of_P_est": float(subset["predicted_p_ticket"].mean()),
                    "observed": float(subset["won"].mean()),
                    "observed_minus_r_pow_k_pp": (float(subset["won"].mean()) - r**size) * 100,
                }
            )
    return pd.DataFrame(rows)


def week_size_decomposition(week_frame: pd.DataFrame) -> pd.DataFrame:
    """Where the ticket-level excess sits, broken out by how many legs a week carried."""
    rows = []
    for n_legs, group in week_frame.groupby("n_legs"):
        row = {
            "week_size": int(n_legs),
            "weeks": len(group),
            "expected_all_win_weeks": float(group["expected_all_win_prob"].sum()),
            "actual_all_win_weeks": int(group["all_win"].sum()),
        }
        for size in (2, 3):
            tickets = group.get(f"tickets_{size}team")
            wins = group.get(f"ticket_wins_{size}team")
            if tickets is None or float(tickets.fillna(0).sum()) == 0:
                row[f"n_{size}team"] = 0
                row[f"rate_{size}team"] = float("nan")
            else:
                total = float(tickets.fillna(0).sum())
                row[f"n_{size}team"] = int(total)
                row[f"rate_{size}team"] = float(wins.fillna(0).sum()) / total
        rows.append(row)
    return pd.DataFrame(rows)


def write_audit_report(blocks, runs, pairs_by_block, week_frames, mc_results,
                       perm_results, args):
    lines: list[str] = []
    add = lines.append

    add("# Phase 2C — independence audit of ticket probability")
    add("")
    add(FROZEN)
    add("")
    for note in (NO_PRICE, REGIME, PROVENANCE):
        add(f"- {note}")
    add("")
    add(
        "The question: can the Phase 2B ticket-level excess arise from (1) sampling "
        "variation, (2) overlapping ticket construction, (3) leg-level miscalibration — or "
        "does it require (4) genuine positive dependence among qualifying legs in the same "
        "NFL week?"
    )
    add("")
    add(OVERLAP_WARNING)
    add("")

    add("## 1. The anomaly, reproduced")
    add("")
    add("### Per season")
    add("")
    add(md(anomaly_table(blocks, [str(s) for s in ALL_SEASONS])))
    add("")
    add("### By block")
    add("")
    add(md(anomaly_table(blocks, MAIN_BLOCKS)))
    add("")
    add(
        "The pattern to explain: leg-level gaps are small and mostly negative, while "
        "ticket-level gaps — especially 3-team — are positive. If legs were independent, a "
        "negative leg gap could not produce a positive ticket gap."
    )
    add("")

    add("## 2. Same-week residual dependence")
    add("")
    add(
        "For every qualifying leg, `residual = outcome - P_est`. For every unordered pair "
        "of qualifying legs in the same (season, week) and different games:"
    )
    add("")
    add(
        "- `mean_resid_product` estimates the average within-week covariance of outcomes. "
        "Under independence its expectation is zero."
    )
    add(
        "- `mean_pair_correlation` normalises each product by "
        "`sqrt(p_a(1-p_a) p_b(1-p_b))`, giving a correlation-scale average."
    )
    add(
        "- The interval is a **week-clustered bootstrap** (10,000 resamples of weeks, not "
        "of pairs), because pairs inside a week are the object under test."
    )
    add("")
    add(md(pd.DataFrame([pairs_by_block[label] for label in
                         [str(s) for s in ALL_SEASONS] + list(MAIN_BLOCKS)])))
    add("")
    total_pairs = pairs_by_block["SUPPLEMENTARY 2018-2025 all years"]["n_pairs"]
    add(
        f"All {total_pairs} same-week pairs are different-game pairs by construction: the "
        "primary set contains no complementary pair, so one game can never contribute two "
        "primary legs."
    )
    add("")

    add("## 3. Week-level all-win analysis")
    add("")
    add(
        "For each week with at least two qualifying primary legs, the independence "
        "expectation that **all** of that week's qualifying legs win is `product(P_i)` over "
        "all of them — not just the top four."
    )
    add("")
    for label in MAIN_BLOCKS:
        add(f"### {label}")
        add("")
        add(md(all_win_summary(week_frames[label], label), raw_cols=[1]))
        add("")

    add("### 3a. A benchmark that uses no P_est at all")
    add("")
    add(
        "The Monte Carlo null assumes `P_est` is calibrated. A benchmark free of that "
        "assumption: let `r` be the realized hit rate of the legs that actually appear on "
        "tickets. If those same wins were arranged independently across the board, a k-leg "
        "ticket would hit at `r^k`. Comparing the observed rate to `r^k` isolates "
        "**arrangement** from **calibration**."
    )
    add("")
    add(md(marginal_benchmark(blocks, MAIN_BLOCKS)))
    add("")
    add(
        "Note that `r` is *below* the mean `P_est` in most blocks: the legs that reach "
        "tickets did not out-perform. So the top-four selection cannot be what lifts the "
        "ticket rates. These `r^k` values are also, to three decimals, where the "
        "permutation distributions in `reports/phase2c_permutation.md` centre — which is "
        "the expected behaviour and a useful cross-check on that test."
    )
    add("")

    add("### 3b. Where the excess sits, by week size")
    add("")
    add(
        "This matters for how much the ticket statistics can bear. A week with four "
        "qualifying legs contributes ten tickets; a week with two contributes one. The "
        "ticket-level statistics are therefore dominated by large weeks, while the "
        "all-win-week statistic counts every week once."
    )
    add("")
    for label in MAIN_BLOCKS:
        frame = week_frames[label]
        if frame.empty:
            continue
        add(f"**{label}**")
        add("")
        add(md(week_size_decomposition(frame)))
        add("")

    add("## 4. Ticket overlap and effective sample size")
    add("")
    add(
        "The nominal ticket count overstates how much independent information the tickets "
        "carry, because each selected leg appears in several of them."
    )
    add("")
    add(md(pd.DataFrame([overlap_stats(blocks[label]) for label in MAIN_BLOCKS])))
    add("")
    add("### Week-clustered bootstrap intervals for the ticket hit rates")
    add("")
    add(
        "Resampling unit is the **week**, with replacement, 10,000 draws. A naive interval "
        "treating each ticket as an independent observation would be narrower and wrong."
    )
    add("")
    boot = []
    for label in MAIN_BLOCKS:
        for size in (2, 3):
            boot.append(week_bootstrap_ticket_rate(blocks[label], size, seed=args.seed))
    add(md(pd.DataFrame(boot)))
    add("")

    add("## 5. Dog/favorite composition as a candidate explanation")
    add("")
    add(
        "Phase 2B found primary dogs out-hitting primary favorites. If successful weeks "
        "simply contained more dogs, that composition — not dependence — could produce the "
        "ticket excess. Weeks are binned by dog fraction; bins were fixed before the "
        "results were read."
    )
    add("")
    for label in MAIN_BLOCKS:
        frame = week_frames[label]
        if frame.empty:
            continue
        bins = pd.cut(
            frame["dog_fraction"],
            [-0.01, 0.499, 0.999, 1.0],
            labels=["<50% dogs", "50-99% dogs", "100% dogs"],
        )
        summary = (
            frame.assign(bin=bins)
            .groupby("bin", observed=False)
            .apply(
                lambda g: pd.Series(
                    {
                        "weeks": len(g),
                        "legs": int(g["n_legs"].sum()),
                        "mean_dog_fraction": float(g["dog_fraction"].mean()) if len(g) else np.nan,
                        "mean_week_hit_rate": float(g["week_hit_rate"].mean()) if len(g) else np.nan,
                        "expected_all_win_weeks": float(g["expected_all_win_prob"].sum()),
                        "actual_all_win_weeks": int(g["all_win"].sum()),
                        "actual_minus_expected": float(
                            g["all_win"].sum() - g["expected_all_win_prob"].sum()
                        ),
                    }
                ),
                include_groups=False,
            )
            .reset_index()
        )
        add(f"### {label}")
        add("")
        add(md(summary, raw_cols=[0]))
        add("")

    add(
        "**Finding: dog composition does not account for the ticket-level excess.** The "
        "all-win surplus is not ordered by dog fraction in any block. In the 2018-2023 "
        "validation block the 100%-dog weeks came in *below* expectation (6 actual against "
        "8.2 expected) while the mixed weeks were slightly above; across all years every "
        "bin sits within roughly one week of its expectation. Whatever drives the ticket "
        "statistics, it is not that successful weeks simply carried more dogs. Scheme P2 "
        "in the permutation report tests the same channel a second way, by permuting "
        "within DOG/FAVORITE strata, and the excess survives there too."
    )
    add("")

    add("## 6. Evidence assessment")
    add("")
    add(
        "The four candidate explanations from the Phase 2C brief, against what the "
        "diagnostics actually show:"
    )
    add("")

    verdict_rows = []
    for label in MAIN_BLOCKS:
        pair = pairs_by_block[label]
        mc = mc_results[label]
        p1 = perm_results["P1"][label]
        p2 = perm_results["P2"][label]
        verdict_rows.append(
            {
                "block": label,
                "mean_resid_product": pair["mean_resid_product"],
                "resid_ci_excludes_zero": (
                    "yes (+)" if pair["boot_ci_low"] > 0
                    else "yes (-)" if pair["boot_ci_high"] < 0
                    else "no"
                ),
                "mc_p_2team": mc["2team"]["p_value_one_sided"] if "2team" in mc else float("nan"),
                "mc_p_3team": mc["3team"]["p_value_one_sided"] if "3team" in mc else float("nan"),
                "permP1_p_2team": p1["2team"]["p_value_one_sided"] if "2team" in p1 else float("nan"),
                "permP1_p_3team": p1["3team"]["p_value_one_sided"] if "3team" in p1 else float("nan"),
                "permP2_p_3team": p2["3team"]["p_value_one_sided"] if "3team" in p2 else float("nan"),
                "allwin_perm_p": p1["all_win_weeks"]["p_value_one_sided"],
            }
        )
    add(md(pd.DataFrame(verdict_rows)))
    add("")
    add("### 1. Sampling variation — NOT excluded")
    add("")
    add(
        "The Monte Carlo null, which lets the board vary as a whole, does not reject "
        "independence in any block at conventional levels. The ticket-level excess sits "
        "inside its 95% simulation interval everywhere."
    )
    add("")
    add("### 2. Overlapping ticket construction — EXCLUDED as the sole cause")
    add("")
    add(
        "Both the Monte Carlo and the permutation rebuild the identical fixed ticket set "
        "from resampled leg outcomes, so overlap is reproduced exactly in the null "
        "distribution. Overlap widens those distributions; it does not shift their centre. "
        "It therefore cannot by itself explain an observed value above the centre."
    )
    add("")
    add("### 3. Leg-level miscalibration — EXCLUDED as the sole cause")
    add("")
    add(
        "The `r^k` benchmark in §3a uses no `P_est` at all, and the permutation test "
        "conditions on the realized win count. Both still show the 2018-2023 and 2025 "
        "excess. Moreover the legs that reach tickets hit *below* their mean `P_est`, so "
        "miscalibration runs against the observed direction, not with it."
    )
    add("")
    add("### 4. Genuine positive within-week dependence — SUPPORTED, WEAKLY")
    add("")
    add(
        "Under the calibration-neutral permutation the 2018-2023 block shows an excess at "
        "p = 0.020 (2-team) and p = 0.005 (3-team), and 2025 shows an all-win-week excess "
        "at p = 0.012. The same-week residual product is positive in 2025 with a "
        "week-clustered interval excluding zero."
    )
    add("")
    add("**But the evidence does not hang together, for four reasons:**")
    add("")
    add(
        "1. **The direction reverses by regime.** 2024 runs negative on every statistic, "
        "with a same-week residual product whose clustered interval excludes zero on the "
        "*negative* side. A common weekly shock does not switch sign between adjacent "
        "seasons."
    )
    add(
        "2. **The statistics disagree within a regime.** In 2018-2023 the ticket "
        "statistics are significant while the overlap-free all-win-week count is not "
        "(28 observed against 27.2 permuted, p = 0.45). In 2025 the reverse holds: "
        "all-win weeks are significant while the ticket statistics are not."
    )
    add(
        "3. **The signal is not uniform across week sizes, as a common shock would "
        "require.** In 2018-2023, weeks with exactly two qualifying legs went 9 of 27 "
        "all-win against 15.1 expected — a large deficit — while weeks with four legs went "
        "6 of 9 against 2.9 expected. Positive dependence should lift both."
    )
    add(
        "4. **Very few independent clusters carry the result.** The 2018-2023 "
        "ticket-level excess rests on nine four-leg weeks contributing 90 of that block's "
        "247 tickets. The effective sample is weeks, not tickets, and the decisive weeks "
        "number single digits."
    )
    add("")
    add(
        "**Verdict: WEAK evidence for positive within-week dependence.** It is more than "
        "absent — two independent calibration-neutral tests reject the random-arrangement "
        "null in two of three regimes, and the two mechanical explanations (overlap, "
        "miscalibration) are ruled out as sole causes. It is less than moderate — the sign "
        "reverses across regimes, the overlap-free and ticket-weighted statistics "
        "contradict each other within regimes, the week-size pattern is inconsistent with "
        "a common shock, and a handful of week-clusters drives the result."
    )
    add("")
    add(
        "No operational consequence follows. This is recorded as a research diagnostic in "
        "`RESEARCH_QUEUE.md` R-08. The frozen ticket formula is unchanged."
    )
    add("")

    add("## 7. Machine-readable outputs")
    add("")
    add("- `data/processed/phase2c_week_diagnostics.csv` — one row per qualifying week, "
        "with per-week ticket counts, wins, dog composition and all-win indicator")
    add("- `data/processed/phase2c_same_week_pairs.csv` — every same-week leg pair")
    add("- `data/processed/phase2c_monte_carlo.csv`, `phase2c_permutation.csv` — every "
        "simulated statistic, each row carrying its seed, simulation count and (for the "
        "permutation) stratum counts and legs held fixed")
    add("")
    add("See `reports/phase2c_monte_carlo.md` and `reports/phase2c_permutation.md`.")
    add("")

    path = REPORTS / "phase2c_independence_audit.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"written: {path.relative_to(ROOT)}")


def write_monte_carlo_report(results, blocks, args):
    lines: list[str] = []
    add = lines.append

    add("# Phase 2C — Monte Carlo null on the exact historical board")
    add("")
    add(FROZEN)
    add("")
    add(
        f"**Design.** Each qualifying leg keeps its actual frozen `P_est`. Under the null "
        f"that leg outcomes are independent `Bernoulli(P_est)` draws, "
        f"{args.sims:,} complete blocks are simulated. Each leg's week and `P_est` are "
        "preserved, and **the frozen top-four ticket set is held fixed**, so the historical "
        "overlap is reproduced exactly: where four legs generated six 2-team and four "
        "3-team tickets, the simulation generates those same overlapping tickets from the "
        "simulated leg outcomes."
    )
    add("")
    add(
        f"Seed `{args.seed}`, fixed. Re-running reproduces every number; a test asserts it."
    )
    add("")
    add(
        "The one-sided Monte Carlo probability is "
        "`(1 + #{simulated >= observed}) / (1 + n_sims)`."
    )
    add("")
    add(
        "**What this null assumes.** It takes `P_est` to be correctly calibrated. If the "
        "frozen model systematically under-states leg probabilities, this test can register "
        "that miscalibration as apparent dependence. The permutation test in "
        "`reports/phase2c_permutation.md` drops that assumption."
    )
    add("")
    add(OVERLAP_WARNING)
    add("")

    for size in (2, 3):
        add(f"## {size}-team tickets")
        add("")
        rows = []
        for label in MAIN_BLOCKS:
            stats = results[label].get(f"{size}team")
            if stats:
                rows.append({"block": label, **stats})
        add(md(pd.DataFrame(rows)))
        add("")

    add("## All-win weeks")
    add("")
    add(
        "A statistic free of ticket overlap: the number of weeks in which every qualifying "
        "leg won, against the independence expectation."
    )
    add("")
    add(md(pd.DataFrame([{"block": label, **results[label]["all_win_weeks"]}
                         for label in MAIN_BLOCKS])))
    add("")

    add("## Leg-win totals (sanity check on the null)")
    add("")
    add(
        "The simulated leg-win totals show where the observed leg count sits inside the "
        "null. This is the leg-level calibration channel, isolated from any ticket effect."
    )
    add("")
    add(md(pd.DataFrame([{"block": label, **results[label]["leg_wins"]}
                         for label in MAIN_BLOCKS])))
    add("")

    add("## Reading these results")
    add("")
    add(
        "The simulation interval is wide because it lets the **total** number of leg wins "
        "vary binomially as well as their arrangement. It therefore answers: *could this "
        "whole board, overlap included, have come out this way by chance under "
        "independence?* It does not isolate clustering. The permutation test conditions on "
        "the realized win total and isolates arrangement; the two answer different "
        "questions and should be read together."
    )
    add("")

    path = REPORTS / "phase2c_monte_carlo.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"written: {path.relative_to(ROOT)}")


def write_permutation_report(results, args):
    lines: list[str] = []
    add = lines.append

    add("# Phase 2C — calibration-neutral permutation test")
    add("")
    add(FROZEN)
    add("")
    add("## Permutation schemes, declared before the results were computed")
    add("")
    add(
        "Both schemes below were fixed in `src/teaser_model_v1/analysis/dependence.py` "
        "before either was run, and **both are reported regardless of what they show.** "
        "Neither was chosen after seeing which produced significance."
    )
    add("")
    add(
        "**P1 — season-level free permutation (primary).** Within each season, permute the "
        "observed WIN/LOSS labels among all qualifying primary legs. Each season's marginal "
        "win count is preserved exactly. The permutation is not confined within a week, so "
        "the association between a leg's week and its outcome is destroyed."
    )
    add("")
    add(
        "**P2 — season x side_class stratified permutation (secondary).** As P1, but "
        "permuting within (season, DOG/FAVORITE) strata, so week-level dog/favorite "
        "composition cannot manufacture clustering. Strata with fewer than "
        f"{MIN_STRATUM_SIZE} legs are held fixed; the count of held-fixed legs is reported."
    )
    add("")
    add(
        "**Why not a finer stratification.** The preferred stratification by shape and "
        "total bucket is not defensible at this sample size: seasons carry 23-63 qualifying "
        "legs, so a 16-cell scheme would leave most cells with 0-2 legs and the permutation "
        "would be close to the identity. Per the Phase 2C instruction, the simplest "
        "defensible scheme is used and the limitation stated here rather than worked around."
    )
    add("")
    add(
        f"{args.sims:,} permutations per block per scheme, seed `{args.seed}`, fixed. "
        "The one-sided probability is `(1 + #{permuted >= observed}) / (1 + n_sims)`."
    )
    add("")
    add(
        "**What this test does and does not assume.** It does **not** assume `P_est` is "
        "calibrated: it conditions on the realized number of wins and asks only whether "
        "those wins are more clustered within weeks than a random reallocation of the same "
        "wins would produce. That makes it the right instrument for separating dependence "
        "from leg-level miscalibration."
    )
    add("")
    add(OVERLAP_WARNING)
    add("")

    for scheme in ("P1", "P2"):
        add(f"## Scheme {scheme}")
        add("")
        add(md(pd.DataFrame([
            {
                "block": label,
                "n_legs": results[scheme][label]["n_legs"],
                "strata": results[scheme][label]["strata"],
                "permutable_strata": results[scheme][label]["permutable_strata"],
                "legs_held_fixed": results[scheme][label]["legs_held_fixed"],
            }
            for label in MAIN_BLOCKS
        ])))
        add("")
        for size in (2, 3):
            rows = []
            for label in MAIN_BLOCKS:
                stats = results[scheme][label].get(f"{size}team")
                if stats:
                    rows.append({"block": label, **stats})
            if rows:
                add(f"### {scheme} — {size}-team tickets")
                add("")
                add(md(pd.DataFrame(rows)))
                add("")
        add(f"### {scheme} — all-win weeks")
        add("")
        add(md(pd.DataFrame([{"block": label, **results[scheme][label]["all_win_weeks"]}
                             for label in MAIN_BLOCKS])))
        add("")

    add("## Limitations")
    add("")
    add(
        "- P1 reallocates outcomes across legs with different `P_est` values, so it "
        "preserves the season's win total but not its composition by total or shape."
    )
    add(
        "- P2 removes the dog/favorite channel but is coarser than the shape x total scheme "
        "the instruction prefers, for the sample-size reason stated above."
    )
    add(
        "- Permuting within a season means a season with an unusual win total is treated as "
        "given. That is the intent — the test is about arrangement, not level — but it "
        "means the test says nothing about leg-level calibration."
    )
    add(
        "- Ticket statistics remain overlapping; the permutation distribution accounts for "
        "that overlap because it rebuilds the same fixed ticket set each time."
    )
    add("")
    add("## What follows from this")
    add("")
    add(
        "Nothing, operationally. This is a diagnostic recorded in `RESEARCH_QUEUE.md` R-08. "
        "No correlation correction is applied, no ticket probability is altered, and no new "
        "live formula is proposed."
    )
    add("")

    path = REPORTS / "phase2c_permutation.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"written: {path.relative_to(ROOT)}")


# ---------------------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sims", type=int, default=DEFAULT_SIMULATIONS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    runs = load_runs()
    blocks = build_blocks(runs)

    # Week diagnostics and pairs, per block.
    def week_ticket_counts(tickets: pd.DataFrame) -> pd.DataFrame:
        if tickets.empty:
            return pd.DataFrame(columns=["season", "week"])
        pivot = (
            tickets.groupby(["season", "week", "n_legs"])
            .agg(tickets=("won", "size"), ticket_wins=("won", "sum"),
                 mean_product=("predicted_p_ticket", "mean"))
            .reset_index()
            .pivot(index=["season", "week"], columns="n_legs",
                   values=["tickets", "ticket_wins", "mean_product"])
        )
        pivot.columns = [f"{a}_{b}team" for a, b in pivot.columns]
        return pivot.reset_index()

    week_frames, pairs_frames, pairs_by_block = {}, {}, {}
    for label in [str(s) for s in ALL_SEASONS] + list(MAIN_BLOCKS):
        block = blocks[label]
        frame = week_all_win(block.legs)
        counts = week_ticket_counts(block.tickets)
        if not frame.empty and not counts.empty:
            frame = frame.merge(counts, on=["season", "week"], how="left")
        week_frames[label] = frame
        pairs_frames[label] = same_week_pairs(block.legs)
        pairs_by_block[label] = pair_summary(pairs_frames[label], label, seed=args.seed)

    all_label = "SUPPLEMENTARY 2018-2025 all years"
    week_frames[all_label].to_csv(PROCESSED / "phase2c_week_diagnostics.csv", index=False)
    pairs_frames[all_label].to_csv(PROCESSED / "phase2c_same_week_pairs.csv", index=False)

    print(f"simulating {args.sims:,} draws per block, seed {args.seed} ...")
    mc_results = {label: monte_carlo_null(blocks[label], n_sims=args.sims, seed=args.seed)
                  for label in MAIN_BLOCKS}
    perm_results = {
        scheme: {
            label: permutation_test(blocks[label], scheme=scheme, n_sims=args.sims,
                                    seed=args.seed)
            for label in MAIN_BLOCKS
        }
        for scheme in ("P1", "P2")
    }

    # Every simulation row carries its own run metadata, so a reader can audit
    # reproducibility and permutation integrity from the CSV alone rather than having to
    # cross-reference the markdown reports.
    rows = []
    for label in MAIN_BLOCKS:
        result = mc_results[label]
        meta = {"n_sims": result["n_sims"], "seed": result["seed"],
                "n_legs": int(blocks[label].legs.shape[0])}
        for size in (2, 3):
            stats = result.get(f"{size}team")
            if stats:
                rows.append({"block": label, "statistic": f"{size}-team hit rate",
                             **stats, **meta})
        rows.append({"block": label, "statistic": "all-win weeks",
                     **result["all_win_weeks"], **meta})
        rows.append({"block": label, "statistic": "leg wins",
                     **result["leg_wins"], **meta})
    pd.DataFrame(rows).to_csv(PROCESSED / "phase2c_monte_carlo.csv", index=False)

    rows = []
    for scheme in ("P1", "P2"):
        for label in MAIN_BLOCKS:
            result = perm_results[scheme][label]
            meta = {
                "n_sims": result["n_sims"],
                "seed": result["seed"],
                "n_legs": result["n_legs"],
                "strata": result["strata"],
                "permutable_strata": result["permutable_strata"],
                "legs_held_fixed": result["legs_held_fixed"],
            }
            for size in (2, 3):
                stats = result.get(f"{size}team")
                if stats:
                    rows.append({"scheme": scheme, "block": label,
                                 "statistic": f"{size}-team hit rate", **stats, **meta})
            rows.append({"scheme": scheme, "block": label, "statistic": "all-win weeks",
                         **result["all_win_weeks"], **meta})
    pd.DataFrame(rows).to_csv(PROCESSED / "phase2c_permutation.csv", index=False)

    write_audit_report(blocks, runs, pairs_by_block, week_frames, mc_results,
                       perm_results, args)
    write_monte_carlo_report(mc_results, blocks, args)
    write_permutation_report(perm_results, args)

    print("\n=== digest ===")
    for label in MAIN_BLOCKS:
        mc2, mc3 = mc_results[label].get("2team"), mc_results[label].get("3team")
        p1_2 = perm_results["P1"][label].get("2team")
        p1_3 = perm_results["P1"][label].get("3team")
        print(f"\n{label}")
        if mc2:
            print(f"  2-team obs {mc2['observed_hit_rate']:.4f}  MC mean {mc2['sim_mean']:.4f} "
                  f"p={mc2['p_value_one_sided']:.4f}   perm P1 mean {p1_2['perm_mean']:.4f} "
                  f"p={p1_2['p_value_one_sided']:.4f}")
        if mc3:
            print(f"  3-team obs {mc3['observed_hit_rate']:.4f}  MC mean {mc3['sim_mean']:.4f} "
                  f"p={mc3['p_value_one_sided']:.4f}   perm P1 mean {p1_3['perm_mean']:.4f} "
                  f"p={p1_3['p_value_one_sided']:.4f}")
        aw = mc_results[label]["all_win_weeks"]
        print(f"  all-win weeks obs {aw['observed']} vs MC {aw['sim_mean']:.2f} p={aw['p_value_one_sided']:.4f}")
        pair = pairs_by_block[label]
        print(f"  pairs n={pair['n_pairs']} mean resid product {pair['mean_resid_product']:+.5f} "
              f"CI [{pair['boot_ci_low']:+.5f}, {pair['boot_ci_high']:+.5f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
