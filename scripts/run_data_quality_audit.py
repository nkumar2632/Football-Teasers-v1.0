#!/usr/bin/env python3
"""Run the mandatory data-quality audit on the ingested NFL data.

This must pass before any strategy calculation is run. It produces
``reports/DATA_QUALITY_NFL_<seasons>.md`` and a machine-readable JSON alongside it, and
exits non-zero on FAIL so a pipeline cannot walk past it.

Usage:
    python scripts/run_data_quality_audit.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teaser_model_v1.audit.data_quality import FAIL, audit_games  # noqa: E402
from teaser_model_v1.audit.report import write_report  # noqa: E402
from teaser_model_v1.ingest import nflverse  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", type=int, nargs="+", default=[2024, 2025])
    parser.add_argument(
        "--tag",
        default=None,
        help="filename tag of the processed inputs; defaults to the joined season list",
    )
    parser.add_argument(
        "--per-season",
        action="store_true",
        help=(
            "audit each season independently and write one report per season. "
            "The gate is applied unchanged; a season that fails is reported as failing."
        ),
    )
    args = parser.parse_args()

    tag = args.tag or "_".join(str(s) for s in args.seasons)
    games = pd.read_csv(ROOT / "data" / "processed" / f"nfl_games_{tag}.csv")
    legs = pd.read_csv(ROOT / "data" / "processed" / f"nfl_legs_{tag}.csv")

    manifest_path = ROOT / "data" / "raw" / "nflverse_nfldata_games.manifest.json"
    manifest = json.loads(manifest_path.read_text())

    notes = [
        f"Source: {manifest['source_name']} — {manifest['source_url']}",
        f"Upstream commit: {manifest['source_commit'] or 'not recorded'}",
        f"Retrieved (UTC): {manifest['retrieved_at_utc']}",
        f"Raw snapshot: `{manifest['local_path']}` (sha256 `{manifest['sha256']}`)",
        f"Line provenance label: **{manifest['line_provenance']}**. "
        f"{manifest['line_provenance_justification']}",
        "Documented meaning of `spread_line`: "
        + manifest["documented_fields"]["spread_line"],
        "Documented meaning of `total_line`: "
        + manifest["documented_fields"]["total_line"],
    ] + [f"Caveat: {c}" for c in manifest["caveats"]]

    limitations = [
        "The source provides one spread and one total per game. It does not provide an "
        "opening line, a line-movement history, a per-book line, or a capture timestamp, "
        "so CLV and line-movement measurement (spec §11, market-quality track) cannot be "
        "computed from this source at all.",
        "No teaser menu prices exist in this source. Per spec §7, none have been "
        "invented: historical work must test hit rate and calibration directly, report "
        "fair break-even pricing, and run sensitivity analysis at explicitly "
        "hypothetical prices.",
        "The sportsbook behind each archived line is not identified.",
        "Because the lines are archived reference lines rather than a documented close, "
        "they are suitable as a *grading* line for backtesting geometry and calibration, "
        "and are NOT suitable for any CLV claim.",
    ]

    report = audit_games(
        games,
        legs,
        dataset=f"NFL {', '.join(str(s) for s in args.seasons)} — nflverse/nfldata",
        line_provenance=nflverse.LINE_PROVENANCE,
        provenance_notes=notes,
    )

    md_path = ROOT / "reports" / f"DATA_QUALITY_NFL_{tag}.md"
    write_report(
        report,
        md_path,
        md_path.with_suffix(".json"),
        header_notes=limitations,
    )

    print(f"verdict: {report.verdict}")
    for check in report.checks:
        print(f"  [{check.status:4}] {check.name}: {check.detail}")
    print(f"\nwritten: {md_path.relative_to(ROOT)}")

    failed_seasons = []
    if args.per_season:
        print("\n=== per-season audits (gate applied unchanged) ===")
        for season in sorted(int(s) for s in games["season"].unique()):
            season_games = games[games["season"] == season]
            season_legs = legs[legs["season"] == season]
            season_report = audit_games(
                season_games,
                season_legs,
                dataset=f"NFL {season} — nflverse/nfldata",
                line_provenance=nflverse.LINE_PROVENANCE,
                provenance_notes=notes,
            )
            season_path = ROOT / "reports" / f"DATA_QUALITY_NFL_{season}.md"
            write_report(
                season_report,
                season_path,
                season_path.with_suffix(".json"),
                header_notes=limitations,
            )
            verdict = season_report.verdict
            if verdict == FAIL:
                failed_seasons.append(season)
            print(f"  {season}: {verdict}  -> {season_path.relative_to(ROOT)}")
            for check in season_report.failed_critical:
                print(f"      FAIL {check.name}: {check.detail}")
            for check in season_report.warnings:
                print(f"      WARN {check.name}: {check.detail}")

    if report.verdict == FAIL or failed_seasons:
        if failed_seasons:
            print(
                f"\nSTOP for season(s) {failed_seasons}. The data-quality gate failed. "
                "Do not run the model on those seasons."
            )
        else:
            print("\nSTOP. Data-quality audit FAILED. Do not run the model on this dataset.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
