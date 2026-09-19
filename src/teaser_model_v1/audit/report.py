"""Render an :class:`~teaser_model_v1.audit.data_quality.AuditReport` as Markdown/JSON."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from teaser_model_v1.audit.data_quality import FAIL, PASS, WARN, AuditReport

_STATUS_MARK = {PASS: "PASS", FAIL: "**FAIL**", WARN: "WARN"}


def _table(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False, floatfmt=".4g")


def render_markdown(report: AuditReport, *, header_notes: list[str] | None = None) -> str:
    lines: list[str] = []
    add = lines.append

    add(f"# Data-Quality Audit — {report.dataset}")
    add("")
    add(
        "This audit runs **before** any strategy calculation. Its purpose is to decide "
        "whether the dataset preserves enough half-point fidelity to test Teaser Model "
        "v1.0 at all. It contains no model-performance results of any kind."
    )
    add("")
    add(f"**Seasons audited:** {', '.join(str(s) for s in report.seasons)}")
    add("")

    verdict = report.verdict
    add("## Verdict")
    add("")
    if verdict == PASS:
        add("### PASS")
        add("")
        add(
            "The dataset preserves half-point fidelity and is safe to use for v1.0 "
            "historical testing, subject to the limitations listed below."
        )
    else:
        add("### FAIL")
        add("")
        add(
            "**STOP.** The dataset does not meet the usability gates. Do not run the "
            "model on it. Failing checks:"
        )
        add("")
        for check in report.failed_critical:
            add(f"- `{check.name}` — {check.detail}")
    add("")

    add("## Checks")
    add("")
    add(
        _table(
            pd.DataFrame(
                [
                    {
                        "check": c.name,
                        "status": _STATUS_MARK[c.status],
                        "critical": "yes" if c.critical else "no",
                        "detail": c.detail,
                    }
                    for c in report.checks
                ]
            )
        )
    )
    add("")

    if report.warnings:
        add("### Warnings (non-blocking)")
        add("")
        for check in report.warnings:
            add(f"- `{check.name}` — {check.detail}")
        add("")

    sections = [
        ("Games by season", "games_by_season"),
        ("Games by season and type", "games_by_season_and_type"),
        ("Half-point share by season", "half_point_share_by_season"),
        ("Composition by season", "composition_by_season"),
        ("Integer vs half-point spreads", "integer_vs_half_point"),
        ("Spread fractional parts", "spread_fractional_part"),
        ("Primary-geometry leg counts", "primary_geometry_counts"),
        ("Key-number pairs (whole vs half)", "key_number_pairs"),
        ("Total line summary", "total_line_summary"),
        ("Spread increment distribution (source field)", "spread_line_distribution"),
        ("Leg spread distribution (team perspective)", "leg_spread_distribution"),
        ("Total line distribution", "total_line_distribution"),
    ]
    add("## Tables")
    add("")
    for title, key in sections:
        if key not in report.tables:
            continue
        add(f"### {title}")
        add("")
        add(_table(report.tables[key]))
        add("")

    add("## Thresholds used")
    add("")
    add(
        "These are **pre-registered data-quality gates, not model parameters.** They "
        "describe what a dataset must look like to be usable, were fixed before any "
        "strategy result was computed, and must never be tuned to make a dataset pass."
    )
    add("")
    add(_table(pd.DataFrame([asdict(report.thresholds)])))
    add("")

    add("## Source and provenance notes")
    add("")
    for note in report.notes:
        add(f"- {note}")
    add("")

    if header_notes:
        add("## Limitations")
        add("")
        for note in header_notes:
            add(f"- {note}")
        add("")

    return "\n".join(lines) + "\n"


def write_report(
    report: AuditReport,
    markdown_path: str | Path,
    json_path: str | Path | None = None,
    *,
    header_notes: list[str] | None = None,
) -> Path:
    markdown_path = Path(markdown_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(report, header_notes=header_notes))

    if json_path is not None:
        json_path = Path(json_path)
        payload = {
            "dataset": report.dataset,
            "seasons": report.seasons,
            "verdict": report.verdict,
            "thresholds": asdict(report.thresholds),
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "critical": c.critical,
                    "detail": c.detail,
                    "data": c.data,
                }
                for c in report.checks
            ],
            "notes": report.notes,
        }
        json_path.write_text(json.dumps(payload, indent=2, default=str) + "\n")

    return markdown_path
