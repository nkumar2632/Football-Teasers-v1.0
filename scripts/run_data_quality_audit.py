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
    args = parser.parse_args()

    tag = "_".join(str(s) for s in args.seasons)
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

    if report.verdict == FAIL:
        print("\nSTOP. Data-quality audit FAILED. Do not run the model on this dataset.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
