"""The on-disk workspace: where each kind of prospective record lives.

Layout::

    data/live/input/        operator-filled CSV templates
    data/live/snapshots/    immutable market and teaser-price snapshots
    data/live/cards/        graded weekly cards and re-check records
    data/live/placements/   the append-only placement ledger
    data/live/settlements/  settlement records
    data/live/season_ledger.jsonl   every week, including empty ones
    reports/live/           human-readable weekly reports
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from teaser_model_v1.live.ledger import SeasonLedger
from teaser_model_v1.live.placement import PlacementLedger
from teaser_model_v1.live.snapshot import AppendOnlyStore


@dataclass
class Workspace:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    @property
    def live_root(self) -> Path:
        return self.root / "data" / "live"

    @property
    def input_dir(self) -> Path:
        path = self.live_root / "input"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def snapshots(self) -> AppendOnlyStore:
        return AppendOnlyStore(self.live_root / "snapshots")

    @property
    def cards(self) -> AppendOnlyStore:
        return AppendOnlyStore(self.live_root / "cards")

    @property
    def settlements(self) -> AppendOnlyStore:
        return AppendOnlyStore(self.live_root / "settlements")

    @property
    def placements(self) -> PlacementLedger:
        return PlacementLedger(self.live_root / "placements" / "placements.jsonl")

    @property
    def season_ledger(self) -> SeasonLedger:
        return SeasonLedger(self.live_root / "season_ledger.jsonl")

    @property
    def corrections(self) -> AppendOnlyStore:
        return AppendOnlyStore(self.live_root / "corrections")

    @property
    def reports_dir(self) -> Path:
        path = self.root / "reports" / "live"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def rechecks_for_card(self, card_id: str) -> list:
        """Every stored re-check for a card, oldest first.

        Used to prove a supplied re-check is the most recent applicable one.
        """
        from teaser_model_v1.live.rehydrate import recheck_from_dict

        results = []
        for row in self.cards.list_records("recheck"):
            payload = self.cards.get(row["record_id"])
            if payload.get("original_card_id") == card_id:
                results.append(recheck_from_dict(payload))
        return sorted(results, key=lambda r: r.rechecked_at)

    def all_settlements(self, season: int | None = None) -> list:
        """Every stored settlement, optionally filtered to a season."""
        rows = []
        for row in self.settlements.list_records("settlement"):
            payload = self.settlements.get(row["record_id"])
            if season is None or payload.get("season") == season:
                rows.append(payload)
        return rows

    def latest_card(self, season: int, week: int):
        """Most recently stored card for a week, or None."""
        rows = [
            row for row in self.cards.list_records("weekly_card")
            if row["record_id"].startswith(f"card_{season}w{week:02d}")
        ]
        return self.cards.get(rows[-1]["record_id"]) if rows else None
