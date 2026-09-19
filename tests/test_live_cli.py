"""Phase 4: manual ingestion round-trip, CLI wiring, and the end-to-end rehearsal."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from teaser_model_v1.live.market import (
    MarketProvider,
    NoProviderConfigured,
    available_providers,
    read_market_csv,
    write_template,
)
from teaser_model_v1.live.pricing import read_price_csv, write_price_template
from teaser_model_v1.live.rehydrate import card_from_dict, market_from_dict, prices_from_dict
from teaser_model_v1.live.schemas import MarketValidationError
from teaser_model_v1.live.workspace import Workspace

ROOT = Path(__file__).resolve().parents[1]
EASTERN = timezone(timedelta(hours=-4))

MARKET_ROWS = """\
game_id,season,week,kickoff,away_team,home_team,team,spread,total,sportsbook,captured_at,source_reference,raw_source_value,notes
2026_03_BUF_MIA,2026,3,2026-09-20T13:00:00-04:00,BUF,MIA,MIA,2.5,44.5,BookX,2026-09-19T10:00:00-04:00,url,MIA +2.5,
2026_03_NYJ_NE,2026,3,2026-09-20T13:00:00-04:00,NYJ,NE,NE,1.5,42.5,BookX,2026-09-19T10:00:00-04:00,url,NE +1.5,
2026_03_DAL_PHI,2026,3,2026-09-20T16:25:00-04:00,DAL,PHI,PHI,-7.5,43.5,BookX,2026-09-19T10:00:00-04:00,url,PHI -7.5,
"""

PRICE_ROWS = """\
ticket_size,american_odds,decimal_odds,sportsbook,captured_at,source_reference,notes
2,-120,,BookX,2026-09-19T10:05:00-04:00,screenshot,
3,+140,,BookX,2026-09-19T10:05:00-04:00,screenshot,
"""


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


# ---- manual ingestion -------------------------------------------------------------------


def test_manual_market_csv_round_trip(tmp_path):
    snapshot = read_market_csv(write(tmp_path / "m.csv", MARKET_ROWS))
    assert len(snapshot.quotes) == 3
    assert snapshot.season == 2026 and snapshot.week == 3
    assert str(snapshot.quotes[0].spread) == "2.5"
    assert snapshot.snapshot_id.startswith("mkt_2026w03_")


def test_template_is_usable_and_its_example_row_is_ignored(tmp_path):
    path = write_template(tmp_path / "t.csv", season=2026, week=3)
    text = path.read_text()
    assert "EXAMPLE ROW" in text
    with pytest.raises(MarketValidationError, match="no usable market rows"):
        read_market_csv(path)


def test_ingestion_reports_the_offending_row_rather_than_skipping_it(tmp_path):
    broken = MARKET_ROWS.replace("2.5,44.5", "2.25,44.5")
    with pytest.raises(MarketValidationError) as exc:
        read_market_csv(write(tmp_path / "m.csv", broken))
    assert "row 2" in str(exc.value)
    assert "not a multiple of 0.5" in str(exc.value)


def test_a_naive_timestamp_in_the_csv_is_rejected(tmp_path):
    broken = MARKET_ROWS.replace("2026-09-19T10:00:00-04:00", "2026-09-19T10:00:00", 1)
    with pytest.raises(MarketValidationError, match="no timezone"):
        read_market_csv(write(tmp_path / "m.csv", broken))


def test_an_unknown_team_is_rejected(tmp_path):
    broken = MARKET_ROWS.replace(",BUF,MIA,MIA,", ",BUF,ZZZ,MIA,", 1)
    with pytest.raises(MarketValidationError):
        read_market_csv(write(tmp_path / "m.csv", broken))


def test_a_duplicate_side_in_one_file_is_rejected(tmp_path):
    duplicated = MARKET_ROWS + MARKET_ROWS.splitlines()[1] + "\n"
    with pytest.raises(MarketValidationError, match="duplicate quote"):
        read_market_csv(write(tmp_path / "m.csv", duplicated))


def test_mixed_weeks_in_one_snapshot_are_rejected(tmp_path):
    mixed = MARKET_ROWS.replace("2026_03_NYJ_NE,2026,3,", "2026_04_NYJ_NE,2026,4,", 1)
    with pytest.raises(MarketValidationError, match="one season and week"):
        read_market_csv(write(tmp_path / "m.csv", mixed))


def test_price_csv_round_trip(tmp_path):
    prices = read_price_csv(write(tmp_path / "p.csv", PRICE_ROWS), season=2026, week=3)
    assert set(prices.profit_by_size()) == {2, 3}
    assert str(prices.quote_for(2).american_odds) == "-120"
    assert prices.snapshot_id.startswith("prc_2026w03_")


def test_price_csv_rejects_both_odds_formats_at_once(tmp_path):
    broken = PRICE_ROWS.replace("2,-120,,", "2,-120,1.8333,", 1)
    with pytest.raises(MarketValidationError, match="not both"):
        read_price_csv(write(tmp_path / "p.csv", broken), season=2026, week=3)


def test_an_empty_price_file_is_refused(tmp_path):
    path = write_price_template(tmp_path / "p.csv")
    with pytest.raises(MarketValidationError, match="no usable price rows"):
        read_price_csv(path, season=2026, week=3)


# ---- provider adapter --------------------------------------------------------------------


def test_no_provider_is_configured_and_manual_stays_first_class():
    providers = available_providers()
    assert set(providers) == {"none"}
    assert isinstance(providers["none"], NoProviderConfigured)
    with pytest.raises(NotImplementedError, match="manual CSV path"):
        providers["none"].fetch(2026, 3)


def test_the_provider_interface_is_abstract():
    with pytest.raises(TypeError):
        MarketProvider()


# ---- rehydration -------------------------------------------------------------------------


def test_snapshots_and_cards_survive_a_store_round_trip(tmp_path):
    from teaser_model_v1.live.card import grade_week

    workspace = Workspace(tmp_path)
    market = read_market_csv(write(tmp_path / "m.csv", MARKET_ROWS))
    prices = read_price_csv(write(tmp_path / "p.csv", PRICE_ROWS), season=2026, week=3)
    workspace.snapshots.put(market.snapshot_id, market.to_dict(), kind="market_snapshot")
    workspace.snapshots.put(prices.snapshot_id, prices.to_dict(),
                            kind="teaser_price_snapshot")

    restored_market = market_from_dict(workspace.snapshots.get(market.snapshot_id))
    restored_prices = prices_from_dict(workspace.snapshots.get(prices.snapshot_id))
    assert restored_market.snapshot_id == market.snapshot_id
    assert restored_prices.profit_by_size() == prices.profit_by_size()

    card = grade_week(restored_market, restored_prices)
    workspace.cards.put(card.card_id, card.to_dict(), kind="weekly_card")
    restored_card = card_from_dict(workspace.cards.get(card.card_id))
    assert restored_card.card_id == card.card_id
    assert [leg.p_est for leg in restored_card.qualifying_legs] == [
        leg.p_est for leg in card.qualifying_legs
    ]


def test_an_edited_snapshot_file_fails_its_own_hash(tmp_path):
    workspace = Workspace(tmp_path)
    market = read_market_csv(write(tmp_path / "m.csv", MARKET_ROWS))
    workspace.snapshots.put(market.snapshot_id, market.to_dict(), kind="market_snapshot")
    payload = workspace.snapshots.get(market.snapshot_id)
    payload["quotes"][0]["spread"] = "3.5"  # tamper
    with pytest.raises(ValueError, match="content hash"):
        market_from_dict(payload)


# ---- CLI ----------------------------------------------------------------------------------


def run_cli(*args, root: Path):
    return subprocess.run(
        [sys.executable, str(ROOT / "src" / "teaser_model_v1" / "cli" / "live.py"),
         "--root", str(root), *args],
        capture_output=True, text=True,
    )


def test_cli_help_states_it_never_places_a_wager():
    result = run_cli("--help", root=ROOT)
    assert result.returncode == 0
    assert "never places a wager" in result.stdout


def test_cli_dry_run_writes_nothing(tmp_path):
    market_file = write(tmp_path / "m.csv", MARKET_ROWS)
    result = run_cli("ingest-market", "--file", str(market_file), "--dry-run", root=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "nothing written" in result.stdout
    assert not (tmp_path / "data" / "live" / "snapshots" / "index.jsonl").exists()


def test_cli_full_ingest_and_grade(tmp_path):
    market_file = write(tmp_path / "m.csv", MARKET_ROWS)
    price_file = write(tmp_path / "p.csv", PRICE_ROWS)

    result = run_cli("ingest-market", "--file", str(market_file), root=tmp_path)
    assert result.returncode == 0, result.stderr
    market_id = next(
        line.split(": ")[1].strip() for line in result.stdout.splitlines()
        if line.startswith("snapshot id")
    )

    result = run_cli("ingest-prices", "--file", str(price_file),
                     "--season", "2026", "--week", "3", root=tmp_path)
    assert result.returncode == 0, result.stderr
    price_id = next(
        line.split(": ")[1].strip() for line in result.stdout.splitlines()
        if line.startswith("snapshot id")
    )

    result = run_cli("grade-week", "--season", "2026", "--week", "3",
                     "--market", market_id, "--prices", price_id, root=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "qualifying primary legs: 3" in result.stdout

    result = run_cli("season-status", "--season", "2026", root=tmp_path)
    assert result.returncode == 0, result.stderr
    status = json.loads(result.stdout.split("\n\n")[0])
    assert status["weeks_recorded"] == 1
    assert status["total_placed_tickets"] == 0


def test_cli_ingesting_the_same_file_twice_is_a_no_op(tmp_path):
    market_file = write(tmp_path / "m.csv", MARKET_ROWS)
    run_cli("ingest-market", "--file", str(market_file), root=tmp_path)
    result = run_cli("ingest-market", "--file", str(market_file), root=tmp_path)
    assert "already stored (no-op)" in result.stdout


# ---- 16. synthetic end-to-end rehearsal ----------------------------------------------------


def test_the_synthetic_rehearsal_runs_end_to_end(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_phase4_rehearsal.py"),
         "--out", str(tmp_path / "rehearsal")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    report = (ROOT / "reports" / "phase4_synthetic_rehearsal.md").read_text()
    for marker in (
        "DISCARD — REBUILD REQUIRED",
        "VALIDATED",
        "model_ticket_result",
        "book_settlement",
        "weeks_with_zero_qualifying_legs",
        # Phase 4.1 gates, cases A-E.
        "**A. no re-check** -> refused",
        "**B. discarded re-check** -> refused",
        "**C. valid re-check** -> accepted",
        "**D. after kickoff** -> pregame gate",
        "derived from the append-only placement and settlement ledgers",
        "exposure cap** -> refused",
        "external non-model** -> recorded",
        "Refused attempts logged (no placement created)",
    ):
        assert marker in report, f"rehearsal did not exercise: {marker}"
    assert "UNEXPECTED" not in report
