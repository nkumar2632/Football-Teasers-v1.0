#!/usr/bin/env python3
"""Line-composition investigation across seasons (provenance only, no model outcomes).

Answers "how are the lines shaped, season by season" from the raw snapshot in
``data/raw/``. Deliberately touches no score, no margin, and no model function: this is a
provenance tool and must remain runnable before any model-performance work.

The git-history portion of the investigation needs a deep clone of the source repository
and is documented in ``reports/nfl_line_composition_investigation.md`` with the exact
commands used; it is not reproduced here.

Usage:
    python scripts/investigate_line_composition.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teaser_model_v1.engine.numeric import is_half_point, to_decimal  # noqa: E402
from teaser_model_v1.ingest import nflverse  # noqa: E402

PRIMARY_ABS = ("1.5", "2.5", "7.5", "8.5")


def season_composition(games: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for season, part in games.groupby("season"):
        part = part[part["spread_line"].notna() & part["total_line"].notna()]
        if part.empty:
            continue
        spreads = [to_decimal(v) for v in part["spread_line"]]
        totals = [to_decimal(v) for v in part["total_line"]]
        rows.append(
            {
                "season": int(season),
                "games": len(part),
                "spread_half_share": sum(map(is_half_point, spreads)) / len(spreads),
                "spread_integers": sum(1 for d in spreads if not is_half_point(d)),
                "total_half_share": sum(map(is_half_point, totals)) / len(totals),
                "total_integers": sum(1 for d in totals if not is_half_point(d)),
            }
        )
    return pd.DataFrame(rows).sort_values("season")


def integer_spread_values(games: pd.DataFrame, seasons) -> pd.DataFrame:
    rows = []
    for season in seasons:
        part = games[(games["season"] == season) & games["spread_line"].notna()]
        ints = part.loc[part["spread_line"] % 1 == 0, "spread_line"].abs()
        counts = ints.value_counts().sort_index()
        rows.append(
            {
                "season": int(season),
                "distinct_integer_values": len(counts),
                "values": ", ".join(f"{int(v)}({c})" for v, c in counts.items()) or "none",
            }
        )
    return pd.DataFrame(rows)


def primary_shape_counts(legs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for season, part in legs.groupby("season"):
        row = {"season": int(season), "legs": len(part)}
        for shape in PRIMARY_ABS:
            for sign in ("+", "-"):
                value = to_decimal(f"{sign}{shape}")
                row[f"{sign}{shape}"] = sum(
                    1 for v in part["spread"] if to_decimal(v) == value
                )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("season")


def main() -> int:
    raw = ROOT / "data" / "raw" / "nflverse_nfldata_games.csv"
    games = nflverse.load_games(raw)

    comp = season_composition(games)
    print("=== Line composition by season (all seasons in the snapshot) ===")
    print(comp.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    print("\n=== Integer spread values present, recent seasons ===")
    recent = [s for s in (2022, 2023, 2024, 2025, 2026) if s in set(comp["season"])]
    print(integer_spread_values(games, recent).to_string(index=False))

    print("\n=== Primary-geometry leg counts, NFL 2024 vs 2025 ===")
    subset = nflverse.played_games(nflverse.filter_seasons(games, [2024, 2025]))
    print(primary_shape_counts(nflverse.to_legs(subset)).to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
