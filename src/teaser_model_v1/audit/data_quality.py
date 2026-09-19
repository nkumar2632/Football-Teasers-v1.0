"""Mandatory data-quality audit.

Specification §12 makes half-point fidelity a hard requirement: a source that rounds
``+2.5`` to ``+3`` or ``-7.5`` to ``-8`` is unsuitable for this model, full stop. This
module measures that and issues an explicit PASS / FAIL.

**The thresholds in :class:`Thresholds` are data-quality gates, not model parameters.**
They were fixed in advance of looking at any strategy result and describe what a dataset
must look like to be *usable*. They never enter the model and must not be tuned to make a
dataset pass.

If the audit FAILs, stop. Do not run the model anyway.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal

import numpy as np
import pandas as pd

from teaser_model_v1.engine.numeric import is_half_point, on_half_point_grid, to_decimal

PRIMARY_LEG_SPREADS = (Decimal("1.5"), Decimal("2.5"), Decimal("-7.5"), Decimal("-8.5"))

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"


@dataclass(frozen=True)
class Thresholds:
    """Pre-registered usability gates. Do not tune these to make data pass.

    ``min_half_point_share``: a source that had rounded half-points away would show a
    share at or near zero. A genuine NFL spread market posts roughly half its lines on
    half-points, so 0.40 is a wide, deliberately forgiving floor that still catches a
    rounded source.

    ``max_missing_share``: missing lines among played games.

    ``max_abs_spread`` / ``max_total`` / ``min_total``: envelopes outside which a value is
    not a plausible NFL number and is treated as a data error.
    """

    min_half_point_share: float = 0.40
    max_missing_share: float = 0.01
    #: Cross-season gap in half-point share above which the source's rounding behaviour
    #: is flagged as having changed between seasons (non-blocking).
    max_season_composition_gap: float = 0.20
    max_abs_spread: float = 30.0
    min_total: float = 20.0
    max_total: float = 80.0


@dataclass
class Check:
    name: str
    status: str
    detail: str
    critical: bool = True
    data: dict = field(default_factory=dict)


@dataclass
class AuditReport:
    dataset: str
    seasons: list
    checks: list
    tables: dict
    notes: list
    thresholds: Thresholds

    @property
    def failed_critical(self) -> list:
        return [c for c in self.checks if c.critical and c.status == FAIL]

    @property
    def warnings(self) -> list:
        return [c for c in self.checks if c.status == WARN]

    @property
    def verdict(self) -> str:
        return FAIL if self.failed_critical else PASS


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def _decimals(series: pd.Series) -> list:
    return [to_decimal(v) for v in series.dropna().tolist()]


def _share(numerator: int, denominator: int) -> float:
    return float(numerator) / denominator if denominator else float("nan")


def _counter_frame(values, name: str) -> pd.DataFrame:
    counts = Counter(values)
    frame = pd.DataFrame(
        sorted(((str(k), v) for k, v in counts.items()), key=lambda kv: Decimal(kv[0])),
        columns=[name, "count"],
    )
    total = frame["count"].sum()
    frame["share"] = frame["count"] / total if total else np.nan
    return frame


# --------------------------------------------------------------------------------------
# The audit
# --------------------------------------------------------------------------------------


def audit_games(
    games: pd.DataFrame,
    legs: pd.DataFrame,
    *,
    dataset: str,
    line_provenance: str,
    provenance_notes: list[str] | None = None,
    thresholds: Thresholds | None = None,
) -> AuditReport:
    """Audit an NFL games frame and its exploded legs frame.

    ``games`` is one row per game with the original source columns; ``legs`` is the
    two-rows-per-game frame from :func:`teaser_model_v1.ingest.nflverse.to_legs`.
    """
    th = thresholds or Thresholds()
    checks: list[Check] = []
    tables: dict[str, pd.DataFrame] = {}
    notes = list(provenance_notes or [])
    seasons = sorted(int(s) for s in games["season"].dropna().unique())

    n_games = len(games)

    # ---- Games by season ------------------------------------------------------------
    by_season = (
        games.groupby(["season", "game_type"]).size().rename("games").reset_index()
    )
    tables["games_by_season_and_type"] = by_season
    tables["games_by_season"] = (
        games.groupby("season").size().rename("games").reset_index()
    )

    # ---- Played vs scheduled --------------------------------------------------------
    unplayed = games[games["home_score"].isna() | games["away_score"].isna()]
    checks.append(
        Check(
            "final_scores_present",
            PASS if unplayed.empty else FAIL,
            f"{len(unplayed)} of {n_games} games have no final score.",
            data={"unplayed": len(unplayed)},
        )
    )

    # ---- Missing spreads / totals ---------------------------------------------------
    missing_spread = int(games["spread_line"].isna().sum())
    missing_total = int(games["total_line"].isna().sum())
    for label, count in (("spread", missing_spread), ("total", missing_total)):
        share = _share(count, n_games)
        checks.append(
            Check(
                f"missing_{label}s",
                PASS if share <= th.max_missing_share else FAIL,
                f"{count} of {n_games} games missing {label}_line ({share:.3%}); "
                f"gate is <= {th.max_missing_share:.1%}.",
                data={"missing": count, "share": share},
            )
        )

    # ---- Duplicate games ------------------------------------------------------------
    dup_ids = games["game_id"][games["game_id"].duplicated(keep=False)]
    dup_matchups = games[
        games.duplicated(subset=["season", "week", "home_team", "away_team"], keep=False)
    ]
    checks.append(
        Check(
            "duplicate_games",
            PASS if dup_ids.empty and dup_matchups.empty else FAIL,
            f"{dup_ids.nunique()} duplicated game_id values; "
            f"{len(dup_matchups)} rows duplicating season/week/home/away.",
            data={
                "duplicate_game_ids": int(dup_ids.nunique()),
                "duplicate_matchup_rows": int(len(dup_matchups)),
            },
        )
    )

    # ---- Spread increment distribution ----------------------------------------------
    spread_decimals = _decimals(games["spread_line"])
    leg_spreads = _decimals(legs["spread"])

    tables["spread_line_distribution"] = _counter_frame(
        spread_decimals, "spread_line (home-favoured-by)"
    )
    tables["leg_spread_distribution"] = _counter_frame(
        leg_spreads, "leg spread (team perspective)"
    )

    fractional = Counter(str(abs(d) % Decimal(1)) for d in spread_decimals)
    tables["spread_fractional_part"] = pd.DataFrame(
        sorted(fractional.items()), columns=["fractional_part", "count"]
    )

    off_grid = [d for d in spread_decimals if not on_half_point_grid(d)]
    checks.append(
        Check(
            "spreads_on_half_point_grid",
            PASS if not off_grid else FAIL,
            f"{len(off_grid)} spread values are not multiples of 0.5"
            + (f" (e.g. {sorted(set(map(str, off_grid)))[:5]})" if off_grid else "."),
            data={"off_grid": len(off_grid)},
        )
    )

    # ---- Half-point share -----------------------------------------------------------
    n_spreads = len(spread_decimals)
    n_half = sum(1 for d in spread_decimals if is_half_point(d))
    half_share = _share(n_half, n_spreads)
    checks.append(
        Check(
            "spread_half_point_share",
            PASS if half_share >= th.min_half_point_share else FAIL,
            f"{n_half} of {n_spreads} spreads end in .5 ({half_share:.2%}); "
            f"gate is >= {th.min_half_point_share:.0%}. A source that rounded half-points "
            f"away would sit near 0%.",
            data={"half_point": n_half, "share": half_share},
        )
    )

    per_season_half = []
    for season in seasons:
        vals = _decimals(games.loc[games["season"] == season, "spread_line"])
        per_season_half.append(
            {
                "season": season,
                "spreads": len(vals),
                "half_point": sum(1 for d in vals if is_half_point(d)),
                "half_point_share": _share(
                    sum(1 for d in vals if is_half_point(d)), len(vals)
                ),
                "integer": sum(1 for d in vals if not is_half_point(d)),
            }
        )
    tables["half_point_share_by_season"] = pd.DataFrame(per_season_half)

    worst_season = min(
        per_season_half, key=lambda r: r["half_point_share"], default=None
    )
    if worst_season is not None:
        checks.append(
            Check(
                "spread_half_point_share_every_season",
                PASS
                if worst_season["half_point_share"] >= th.min_half_point_share
                else FAIL,
                f"Lowest single-season half-point share is "
                f"{worst_season['half_point_share']:.2%} in {worst_season['season']}; "
                f"gate is >= {th.min_half_point_share:.0%}.",
                data=worst_season,
            )
        )

    # ---- Cross-season composition consistency ---------------------------------------
    # A source whose line-rounding behaviour changes between seasons will silently change
    # how many legs land on primary geometry. That is a provenance fact about the data,
    # not a model effect, so it must be surfaced rather than averaged away.
    total_half_by_season = {
        season: _share(
            sum(
                1
                for d in _decimals(games.loc[games["season"] == season, "total_line"])
                if is_half_point(d)
            ),
            int((games["season"] == season).sum()),
        )
        for season in seasons
    }
    spread_half_by_season = {r["season"]: r["half_point_share"] for r in per_season_half}
    tables["composition_by_season"] = pd.DataFrame(
        [
            {
                "season": season,
                "spread_half_point_share": spread_half_by_season[season],
                "total_half_point_share": total_half_by_season[season],
            }
            for season in seasons
        ]
    )

    composition_gaps = []
    for label, mapping in (
        ("spread", spread_half_by_season),
        ("total", total_half_by_season),
    ):
        if len(mapping) > 1:
            gap = max(mapping.values()) - min(mapping.values())
            if gap > th.max_season_composition_gap:
                composition_gaps.append(
                    f"{label} half-point share varies by {gap:.1%} across seasons "
                    f"({ {k: round(v, 3) for k, v in mapping.items()} })."
                )
    checks.append(
        Check(
            "season_composition_consistency",
            PASS if not composition_gaps else WARN,
            "Half-point composition is consistent across seasons."
            if not composition_gaps
            else " ".join(composition_gaps)
            + " This indicates a change in the upstream line feed between seasons. It does "
            "NOT round half-points away (the fidelity gates still pass), but leg counts are "
            "not comparable across seasons and must be reported per season, never pooled "
            "silently. For NFL 2024 vs 2025 this was investigated in full: see "
            "reports/nfl_line_composition_investigation.md.",
            critical=False,
            data={"gaps": composition_gaps},
        )
    )

    # ---- Counts of the four primary shapes ------------------------------------------
    leg_counter = Counter(leg_spreads)
    primary_rows = []
    for spread in PRIMARY_LEG_SPREADS:
        per_season = {
            season: sum(
                1
                for d in _decimals(legs.loc[legs["season"] == season, "spread"])
                if d == spread
            )
            for season in seasons
        }
        primary_rows.append(
            {
                "leg_spread": str(spread),
                "legs_total": leg_counter.get(spread, 0),
                **{f"legs_{s}": v for s, v in per_season.items()},
            }
        )
    tables["primary_geometry_counts"] = pd.DataFrame(primary_rows)

    zero_shapes = [r["leg_spread"] for r in primary_rows if r["legs_total"] == 0]
    checks.append(
        Check(
            "primary_geometry_present",
            PASS if not zero_shapes else FAIL,
            "All four primary shapes appear in the data."
            if not zero_shapes
            else f"Primary shapes absent entirely: {zero_shapes}.",
            data={"absent": zero_shapes},
        )
    )

    missing_season_shape = [
        (r["leg_spread"], s)
        for r in primary_rows
        for s in seasons
        if r.get(f"legs_{s}", 0) == 0
    ]
    checks.append(
        Check(
            "primary_geometry_present_every_season",
            PASS if not missing_season_shape else WARN,
            "Every primary shape appears in every season."
            if not missing_season_shape
            else f"Primary shape absent in a season: {missing_season_shape}. "
            "Not necessarily an error — these are genuinely thin lines.",
            critical=False,
            data={"absent": missing_season_shape},
        )
    )

    # ---- Integer vs half-point frequency, including at the key numbers ---------------
    integer_share = 1.0 - half_share
    tables["integer_vs_half_point"] = pd.DataFrame(
        [
            {"kind": "half-point (.5)", "count": n_half, "share": half_share},
            {
                "kind": "integer (.0)",
                "count": n_spreads - n_half,
                "share": integer_share,
            },
        ]
    )

    # Pairs of (whole number, adjacent half-point) that matter to this model's geometry.
    # If a whole number is present in the data but the half-point beside it never appears
    # at all, the source collapsed that half-point into the integer.
    key_pairs = [
        (Decimal("2"), Decimal("1.5")),
        (Decimal("2"), Decimal("2.5")),
        (Decimal("3"), Decimal("2.5")),
        (Decimal("3"), Decimal("3.5")),
        (Decimal("7"), Decimal("6.5")),
        (Decimal("7"), Decimal("7.5")),
        (Decimal("8"), Decimal("7.5")),
        (Decimal("8"), Decimal("8.5")),
        (Decimal("9"), Decimal("8.5")),
    ]
    abs_counter = Counter(abs(d) for d in spread_decimals)
    tables["key_number_pairs"] = pd.DataFrame(
        [
            {
                "whole": str(whole),
                "count_whole": abs_counter.get(whole, 0),
                "adjacent_half": str(half),
                "count_half": abs_counter.get(half, 0),
            }
            for whole, half in key_pairs
        ]
    )

    collapsed = [
        f"|{half}| (beside |{whole}|)"
        for whole, half in key_pairs
        if abs_counter.get(whole, 0) > 0 and abs_counter.get(half, 0) == 0
    ]
    checks.append(
        Check(
            "key_numbers_not_collapsed",
            PASS if not collapsed else FAIL,
            "Every whole number present in the data still has its adjacent half-point "
            "represented."
            if not collapsed
            else f"Half-point values never appear next to a populated whole number: "
            f"{collapsed}. This is the signature of a source that rounded to integers.",
            data={"collapsed": collapsed},
        )
    )

    # ---- Total distribution ---------------------------------------------------------
    total_decimals = _decimals(games["total_line"])
    tables["total_line_distribution"] = _counter_frame(total_decimals, "total_line")
    n_total_half = sum(1 for d in total_decimals if is_half_point(d))
    total_half_share = _share(n_total_half, len(total_decimals))
    tables["total_line_summary"] = pd.DataFrame(
        [
            {
                "season": season,
                "n": int((games["season"] == season).sum()),
                "min": float(games.loc[games["season"] == season, "total_line"].min()),
                "p25": float(
                    games.loc[games["season"] == season, "total_line"].quantile(0.25)
                ),
                "median": float(
                    games.loc[games["season"] == season, "total_line"].median()
                ),
                "p75": float(
                    games.loc[games["season"] == season, "total_line"].quantile(0.75)
                ),
                "max": float(games.loc[games["season"] == season, "total_line"].max()),
                "mean": float(games.loc[games["season"] == season, "total_line"].mean()),
                "half_point_share": _share(
                    sum(
                        1
                        for d in _decimals(
                            games.loc[games["season"] == season, "total_line"]
                        )
                        if is_half_point(d)
                    ),
                    int((games["season"] == season).sum()),
                ),
                "at_or_below_47": int(
                    (games.loc[games["season"] == season, "total_line"] <= 47).sum()
                ),
            }
            for season in seasons
        ]
    )
    checks.append(
        Check(
            "total_half_point_share",
            PASS if total_half_share >= th.min_half_point_share else WARN,
            f"{n_total_half} of {len(total_decimals)} totals end in .5 "
            f"({total_half_share:.2%}). Totals do not gate the model the way spreads do, "
            f"but a near-zero share would still indicate rounding.",
            critical=False,
            data={"share": total_half_share},
        )
    )

    off_grid_totals = [d for d in total_decimals if not on_half_point_grid(d)]
    checks.append(
        Check(
            "totals_on_half_point_grid",
            PASS if not off_grid_totals else FAIL,
            f"{len(off_grid_totals)} total values are not multiples of 0.5.",
            data={"off_grid": len(off_grid_totals)},
        )
    )

    # ---- Suspicious rounding patterns -----------------------------------------------
    suspicious: list[str] = []
    if integer_share > 0.60:
        suspicious.append(
            f"Integer spreads make up {integer_share:.1%} of the book — unusually high."
        )
    whole_only_seasons = [
        r["season"] for r in per_season_half if r["half_point_share"] == 0.0
    ]
    if whole_only_seasons:
        suspicious.append(f"Seasons with no half-point spreads at all: {whole_only_seasons}.")
    quarter_points = [d for d in spread_decimals if not on_half_point_grid(d)]
    if quarter_points:
        suspicious.append(
            f"{len(quarter_points)} spreads off the 0.5 grid — possible averaging of "
            "multiple books, which destroys the exact posted line."
        )
    # A source that rounded to the nearest integer typically leaves 3.0/7.0 piles far in
    # excess of their neighbours.
    for key in (Decimal("3"), Decimal("7")):
        neighbours = abs_counter.get(key - Decimal("0.5"), 0) + abs_counter.get(
            key + Decimal("0.5"), 0
        )
        here = abs_counter.get(key, 0)
        if neighbours and here > 4 * neighbours:
            suspicious.append(
                f"|{key}| appears {here} times against {neighbours} at the adjacent "
                "half-points — consistent with integer rounding."
            )
    checks.append(
        Check(
            "suspicious_rounding_patterns",
            PASS if not suspicious else WARN,
            "No suspicious rounding patterns detected."
            if not suspicious
            else " ".join(suspicious),
            critical=False,
            data={"patterns": suspicious},
        )
    )

    # ---- Obvious impossible values --------------------------------------------------
    impossible: list[str] = []
    played = games[games["home_score"].notna() & games["away_score"].notna()]

    neg_scores = played[(played["home_score"] < 0) | (played["away_score"] < 0)]
    if len(neg_scores):
        impossible.append(f"{len(neg_scores)} games with a negative score.")

    score_mismatch = played[
        (played["home_score"] + played["away_score"] - played["total"]).abs() > 1e-9
    ]
    if len(score_mismatch):
        impossible.append(
            f"{len(score_mismatch)} games where home+away score != reported total."
        )

    result_mismatch = played[
        (played["home_score"] - played["away_score"] - played["result"]).abs() > 1e-9
    ]
    if len(result_mismatch):
        impossible.append(
            f"{len(result_mismatch)} games where home-away score != reported result."
        )

    wild_spreads = games[games["spread_line"].abs() > th.max_abs_spread]
    if len(wild_spreads):
        impossible.append(
            f"{len(wild_spreads)} spreads with |value| > {th.max_abs_spread}."
        )

    wild_totals = games[
        (games["total_line"] < th.min_total) | (games["total_line"] > th.max_total)
    ]
    if len(wild_totals):
        impossible.append(
            f"{len(wild_totals)} totals outside [{th.min_total}, {th.max_total}]."
        )

    nonpositive_totals = games[games["total_line"] <= 0]
    if len(nonpositive_totals):
        impossible.append(
            f"{len(nonpositive_totals)} totals <= 0 (sigma would be undefined)."
        )

    checks.append(
        Check(
            "impossible_values",
            PASS if not impossible else FAIL,
            "No impossible values found."
            if not impossible
            else " ".join(impossible),
            data={"issues": impossible},
        )
    )

    # ---- Provenance -----------------------------------------------------------------
    checks.append(
        Check(
            "line_provenance_is_honest",
            PASS if line_provenance != "true_timestamped_close" else WARN,
            f"Lines are labelled '{line_provenance}'. "
            "'true_timestamped_close' is only permitted when the source documents a "
            "capture time before kickoff.",
            critical=False,
            data={"line_provenance": line_provenance},
        )
    )

    return AuditReport(
        dataset=dataset,
        seasons=seasons,
        checks=checks,
        tables=tables,
        notes=notes,
        thresholds=th,
    )
