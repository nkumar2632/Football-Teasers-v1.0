#!/usr/bin/env python3
"""Ingest NFL game/line data from nflverse/nfldata into data/raw and data/processed.

Phase 1 scope: NFL 2024 and 2025 only.

The raw source file is snapshotted verbatim into ``data/raw/`` together with a manifest
recording its SHA-256, the upstream commit it came from, and — importantly — what the
source documentation does and does not claim about its line fields.

Usage:
    python scripts/ingest_nfl.py --from-clone /path/to/nfldata
    python scripts/ingest_nfl.py --from-url          # downloads games.csv
    python scripts/ingest_nfl.py --from-file games.csv
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teaser_model_v1.ingest import nflverse  # noqa: E402
from teaser_model_v1.ingest.provenance import (  # noqa: E402
    SourceManifest,
    sha256_file,
    utc_now_iso,
)

SEASONS = (2024, 2025)
RAW_NAME = "nflverse_nfldata_games.csv"


def _upstream_commit(clone: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(clone), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def acquire(args, raw_path: Path) -> str | None:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if args.from_clone:
        clone = Path(args.from_clone)
        shutil.copyfile(clone / "data" / "games.csv", raw_path)
        return _upstream_commit(clone)
    if args.from_file:
        shutil.copyfile(Path(args.from_file), raw_path)
        return None
    urllib.request.urlretrieve(nflverse.SOURCE_RAW_URL, raw_path)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--from-clone", help="path to a local nflverse/nfldata clone")
    group.add_argument("--from-file", help="path to an already-downloaded games.csv")
    group.add_argument(
        "--from-url", action="store_true", help="download games.csv from GitHub"
    )
    parser.add_argument(
        "--seasons",
        type=int,
        nargs="+",
        default=list(SEASONS),
        help="seasons to extract (Phase 1: 2024 2025)",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="filename tag for the processed outputs; defaults to the joined season list",
    )
    args = parser.parse_args()

    raw_path = ROOT / "data" / "raw" / RAW_NAME
    commit = acquire(args, raw_path)

    games = nflverse.load_games(raw_path)
    subset = nflverse.filter_seasons(games, args.seasons)
    played = nflverse.played_games(subset)
    legs = nflverse.to_legs(played)

    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    tag = args.tag or "_".join(str(s) for s in args.seasons)
    games_out = processed / f"nfl_games_{tag}.csv"
    legs_out = processed / f"nfl_legs_{tag}.csv"
    played.to_csv(games_out, index=False)
    legs.to_csv(legs_out, index=False)

    manifest = SourceManifest(
        dataset=f"NFL games {tag}",
        source_name=nflverse.SOURCE_NAME,
        source_url=nflverse.SOURCE_URL,
        source_commit=commit,
        retrieved_at_utc=utc_now_iso(),
        local_path=str(raw_path.relative_to(ROOT)),
        sha256=sha256_file(raw_path),
        rows=int(len(games)),
        line_provenance=nflverse.LINE_PROVENANCE,
        line_provenance_justification=nflverse.LINE_PROVENANCE_JUSTIFICATION,
        documented_fields=nflverse.LINE_FIELD_DOCS,
        caveats=[
            "spread_line/total_line have no documented capture timestamp. They are "
            "archived reference lines, NOT a close of any kind.",
            "The source aggregates lines historically; the exact sportsbook is not "
            "recorded per game.",
            "No teaser menu prices are present in this source. None have been invented.",
        ],
    )
    manifest_path = raw_path.with_suffix(".manifest.json")
    manifest.write(manifest_path)

    print(f"raw snapshot : {raw_path.relative_to(ROOT)}  (sha256 {manifest.sha256[:12]}…)")
    print(f"manifest     : {manifest_path.relative_to(ROOT)}")
    print(f"games        : {games_out.relative_to(ROOT)}  ({len(played)} rows)")
    print(f"legs         : {legs_out.relative_to(ROOT)}  ({len(legs)} rows)")
    print(f"line provenance: {manifest.line_provenance}")
    if len(subset) != len(played):
        print(
            f"note: {len(subset) - len(played)} scheduled-but-unplayed rows excluded "
            "(not imputed)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
