#!/usr/bin/env python3
"""Convert one week of nflverse/nfldata into a live-layer market snapshot.

Provenance discipline: nflverse/nfldata is a **data feed, not a sportsbook**. Its
``spread_line``/``total_line`` carry no book attribution and no documented capture time,
so the snapshot is labelled as a reference feed and the report must never present it as a
sportsbook's board. It is a clearly identified source, which is what the shadow run needs;
it is not a price source, so no teaser price comes from it.

Only games that have **not kicked off** are included — a pregame model cannot grade a game
that has started.

Usage:
    python scripts/ingest_nflverse_week_to_live.py --season 2026 --week 2 \
        --clone /home/user/nflverse/nfldata
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teaser_model_v1.live.market import TEMPLATE_COLUMNS, read_market_csv  # noqa: E402
from teaser_model_v1.live.workspace import Workspace  # noqa: E402

#: nfldata gametime is US Eastern. September is EDT (UTC-4).
EASTERN_EDT = timezone(timedelta(hours=-4))

SOURCE_NAME = "nflverse/nfldata games.csv (reference feed, NOT a sportsbook)"


def feed_commit(clone: Path) -> tuple:
    out = subprocess.run(
        ["git", "-C", str(clone), "log", "-1", "--format=%H|%cI"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    sha, when = out.split("|")
    return sha, when


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--clone", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    clone = Path(args.clone)
    sha, captured_at = feed_commit(clone)

    games = pd.read_csv(clone / "data" / "games.csv")
    week = games[(games["season"] == args.season) & (games["week"] == args.week)].copy()
    if week.empty:
        print(f"no games for {args.season} week {args.week}")
        return 1

    played = week[week["home_score"].notna()]
    pregame = week[week["home_score"].isna()].copy()
    missing = pregame[pregame["spread_line"].isna() | pregame["total_line"].isna()]
    pregame = pregame.drop(missing.index)

    print(f"{args.season} week {args.week}: {len(week)} games")
    print(f"  already played (excluded, post-kickoff): {len(played)}")
    print(f"  pregame with lines: {len(pregame)}")
    print(f"  pregame WITHOUT lines (excluded): {len(missing)}")

    rows = []
    for row in pregame.itertuples(index=False):
        kickoff = datetime.strptime(
            f"{row.gameday} {row.gametime}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=EASTERN_EDT)
        # spread_line is "home favoured by N"; each side is quoted from its own view.
        for side, team, spread in (
            ("home", row.home_team, -row.spread_line),
            ("away", row.away_team, row.spread_line),
        ):
            rows.append({
                "game_id": row.game_id,
                "season": int(row.season),
                "week": int(row.week),
                "kickoff": kickoff.isoformat(),
                "away_team": row.away_team,
                "home_team": row.home_team,
                "team": team,
                "spread": f"{spread:g}",
                "total": f"{row.total_line:g}",
                "sportsbook": "NFLVERSE_NFLDATA_FEED",
                "captured_at": captured_at,
                "source_reference": f"nflverse/nfldata@{sha[:12]}",
                "raw_source_value": f"spread_line={row.spread_line:g} total_line={row.total_line:g}",
                "notes": "reference feed; no book attribution, no documented capture time",
            })

    out = Path(args.out) if args.out else (
        Workspace(ROOT).input_dir
        / f"nfl_{args.season}_week_{args.week:02d}_market_nflverse.csv"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as handle:
        handle.write(
            f"# Source: {SOURCE_NAME}\n"
            f"# Commit: {sha}\n"
            f"# Feed last updated: {captured_at}\n"
            "# This is a DATA FEED, not a sportsbook. No teaser prices come from it.\n"
        )
        writer = csv.DictWriter(handle, fieldnames=list(TEMPLATE_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    snapshot = read_market_csv(
        out, ingestion_method="nflverse_reference_feed",
        label=f"{args.season} week {args.week} pregame",
        notes=f"nflverse/nfldata@{sha[:12]}; reference feed, not a sportsbook",
    )
    workspace = Workspace(ROOT)
    result = workspace.snapshots.put(
        snapshot.snapshot_id, snapshot.to_dict(), kind="market_snapshot"
    )
    print(f"\nmarket CSV : {out.relative_to(ROOT)}")
    print(f"snapshot id: {snapshot.snapshot_id}")
    print(f"quotes     : {len(snapshot.quotes)} across {len(snapshot.games)} games")
    print("stored" if result.created else "identical snapshot already stored (no-op)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
