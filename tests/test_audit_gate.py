"""The data-quality gate must actually stop a rounded dataset.

An audit that passes everything is worthless. These tests prove the gate fires.
"""

from __future__ import annotations

import pandas as pd
import pytest

from teaser_model_v1.audit.data_quality import FAIL, PASS, WARN, audit_games
from teaser_model_v1.ingest import nflverse


def build_games(spreads, totals=None, *, season=2024):
    """Synthesise a games frame with the given spread_line values."""
    totals = totals or [44.5] * len(spreads)
    rows = []
    for i, (spread, total) in enumerate(zip(spreads, totals)):
        home, away = 24, 17
        rows.append(
            {
                "game_id": f"{season}_{i:02d}_A{i}_B{i}",
                "season": season,
                "game_type": "REG",
                "week": (i % 18) + 1,
                "gameday": f"{season}-09-08",
                "away_team": f"A{i}",
                "home_team": f"B{i}",
                "away_score": away,
                "home_score": home,
                "result": home - away,
                "total": home + away,
                "spread_line": spread,
                "total_line": total,
            }
        )
    return pd.DataFrame(rows)


def run_audit(games):
    legs = nflverse.to_legs(games)
    return audit_games(
        games,
        legs,
        dataset="synthetic",
        line_provenance="archived_reference_line",
    )


def check(report, name):
    return next(c for c in report.checks if c.name == name)


def test_a_clean_half_point_dataset_passes():
    spreads = [1.5, 2.5, -7.5, -8.5, 3.5, -3.5, 6.5, -1.5, 2.5, 7.5]
    report = run_audit(build_games(spreads))
    assert report.verdict == PASS


def test_a_source_that_rounded_half_points_to_integers_FAILS():
    # Exactly the failure mode spec §12 calls out: +2.5 -> +3, -7.5 -> -8.
    spreads = [2.0, 3.0, -8.0, -9.0, 4.0, -4.0, 7.0, -2.0, 3.0, 8.0]
    report = run_audit(build_games(spreads))

    assert report.verdict == FAIL
    failed = {c.name for c in report.failed_critical}
    assert "spread_half_point_share" in failed
    assert "primary_geometry_present" in failed


def test_a_source_that_averages_books_off_the_half_point_grid_FAILS():
    spreads = [1.25, 2.75, -7.25, -8.75, 3.5, -3.5, 6.5, -1.5, 2.5, 7.5]
    report = run_audit(build_games(spreads))
    assert report.verdict == FAIL
    assert "spreads_on_half_point_grid" in {c.name for c in report.failed_critical}


def test_missing_lines_fail_the_gate():
    games = build_games([1.5, 2.5, -7.5, -8.5, 3.5, -3.5, 6.5, -1.5, 2.5, 7.5])
    games.loc[0:3, "spread_line"] = None
    report = run_audit(games)
    assert report.verdict == FAIL
    assert "missing_spreads" in {c.name for c in report.failed_critical}


def test_duplicate_games_fail_the_gate():
    games = build_games([1.5, 2.5, -7.5, -8.5, 3.5, -3.5])
    games = pd.concat([games, games.iloc[[0]]], ignore_index=True)
    report = run_audit(games)
    assert report.verdict == FAIL
    assert "duplicate_games" in {c.name for c in report.failed_critical}


def test_impossible_values_fail_the_gate():
    games = build_games([1.5, 2.5, -7.5, -8.5, 3.5, -3.5])
    games.loc[0, "total_line"] = 0.0
    games.loc[1, "spread_line"] = 99.5
    report = run_audit(games)
    assert report.verdict == FAIL
    assert "impossible_values" in {c.name for c in report.failed_critical}


def test_score_bookkeeping_mismatch_is_caught():
    games = build_games([1.5, 2.5, -7.5, -8.5, 3.5, -3.5])
    games.loc[0, "total"] = 999
    report = run_audit(games)
    assert report.verdict == FAIL


def test_key_number_collapse_is_caught():
    # Whole numbers present at 3 and 7, no half-points anywhere near them.
    spreads = [3.0, 3.0, 7.0, 7.0, 1.5, 2.5, -7.5, -8.5, 1.5, 2.5]
    report = run_audit(build_games(spreads))
    collapse = check(report, "key_numbers_not_collapsed")
    assert collapse.status == FAIL


def test_cross_season_composition_shift_warns_without_blocking():
    clean = [1.5, 2.5, -7.5, -8.5, 3.5, -3.5, 6.5, -1.5, 2.5, 7.5]
    mixed = [1.5, 2.5, -7.5, -8.5, 3.0, -3.0, 6.0, -1.0, 2.0, 7.0]
    games = pd.concat(
        [build_games(clean, season=2024), build_games(mixed, season=2025)],
        ignore_index=True,
    )
    report = run_audit(games)
    consistency = check(report, "season_composition_consistency")
    assert consistency.status == WARN
    assert not consistency.critical
    assert report.verdict == PASS  # non-critical: it informs, it does not block


def test_calling_a_line_a_true_close_is_flagged():
    games = build_games([1.5, 2.5, -7.5, -8.5, 3.5, -3.5])
    legs = nflverse.to_legs(games)
    report = audit_games(
        games,
        legs,
        dataset="synthetic",
        line_provenance="true_timestamped_close",
    )
    assert check(report, "line_provenance_is_honest").status == WARN
