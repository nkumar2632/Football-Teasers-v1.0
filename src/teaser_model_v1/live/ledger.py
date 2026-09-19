"""Prospective market-quality record and the append-only season ledger.

Two separate tracks, exactly as the specification requires (§11 of the frozen spec):

* **Market quality** — which line we graded on, which line we placed on, what the market
  looked like last before kickoff, and the timestamp and book for each.
* **Model quality** — `P_est`, the outcome, and calibration.

CLV does not validate probability calibration, so the two never share a table.

Naming discipline: the last observed pre-kickoff line is
``final_observed_market_snapshot``, **not** a closing line. It is called a close only if a
source genuinely documents it as the last market price before kickoff, which no source in
this project currently does.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from teaser_model_v1.engine.numeric import to_decimal
from teaser_model_v1.live.provenance import iso, require_aware
from teaser_model_v1.live.snapshot import AppendOnlyLedger

#: Provenance labels for a line, in increasing strength of claim.
GRADING_LINE = "grading_line"
PLACEMENT_LINE = "placement_line"
FINAL_OBSERVED = "final_observed_market_snapshot"
#: Reserved. Use only where a source documents a true pre-kickoff close.
TRUE_TIMESTAMPED_CLOSE = "true_timestamped_close"


@dataclass(frozen=True)
class LineObservation:
    """One line, with the provenance label its evidence actually supports."""

    leg_id: str
    label: str
    spread: Decimal
    total: Decimal
    sportsbook: str
    observed_at: datetime
    market_snapshot_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "spread", to_decimal(self.spread))
        object.__setattr__(self, "total", to_decimal(self.total))
        object.__setattr__(
            self, "observed_at", require_aware(self.observed_at, field="observed_at")
        )
        if self.label == TRUE_TIMESTAMPED_CLOSE:
            raise ValueError(
                "true_timestamped_close may only be used where the source documents the "
                "last market price before kickoff. Use final_observed_market_snapshot."
            )

    def to_dict(self) -> dict:
        return {
            "leg_id": self.leg_id,
            "label": self.label,
            "spread": str(self.spread),
            "total": str(self.total),
            "sportsbook": self.sportsbook,
            "observed_at": iso(self.observed_at),
            "market_snapshot_id": self.market_snapshot_id,
        }


def line_movement(earlier: LineObservation, later: LineObservation) -> dict:
    """Movement between two observations of the same leg.

    Reported as a signed change in the leg's own spread. This is **line movement**, not
    CLV: CLV requires a defensible closing reference, which
    ``final_observed_market_snapshot`` is not.
    """
    if earlier.leg_id != later.leg_id:
        raise ValueError("line movement compares two observations of the SAME leg")
    return {
        "leg_id": earlier.leg_id,
        "from_label": earlier.label,
        "to_label": later.label,
        "from_spread": str(earlier.spread),
        "to_spread": str(later.spread),
        "spread_change": str(later.spread - earlier.spread),
        "from_total": str(earlier.total),
        "to_total": str(later.total),
        "total_change": str(later.total - earlier.total),
        "from_observed_at": iso(earlier.observed_at),
        "to_observed_at": iso(later.observed_at),
        "clv_computed": False,
        "clv_note": (
            "CLV is not computed: the later observation is a "
            "final_observed_market_snapshot, not a documented close. Computing CLV "
            "against it would overstate what the provenance supports."
        ),
    }


@dataclass(frozen=True)
class WeekLedgerEntry:
    """One week of the prospective record — including weeks with nothing to bet.

    Zero-qualifier and zero-bet weeks are recorded exactly like any other. Omitting them
    would create survivorship bias in the prospective track by construction.
    """

    season: int
    week: int
    recorded_at: datetime
    games_scanned: int
    qualifying_primary_legs: int
    top_four_legs: int
    positive_ev_tickets: int
    proposed_tickets: int
    placed_tickets: int
    units_staked: float
    market_snapshot_id: str = ""
    price_snapshot_id: str = ""
    card_id: str = ""
    card_status: str = ""
    wins: int = 0
    losses: int = 0
    profit_loss_units: float = 0.0
    settled_tickets: int = 0
    sum_p_ticket: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "kind": "week_ledger_entry",
            "season": self.season,
            "week": self.week,
            "recorded_at": iso(require_aware(self.recorded_at, field="recorded_at")),
            "games_scanned": self.games_scanned,
            "qualifying_primary_legs": self.qualifying_primary_legs,
            "top_four_legs": self.top_four_legs,
            "positive_ev_tickets": self.positive_ev_tickets,
            "proposed_tickets": self.proposed_tickets,
            "placed_tickets": self.placed_tickets,
            "units_staked": self.units_staked,
            "market_snapshot_id": self.market_snapshot_id,
            "price_snapshot_id": self.price_snapshot_id,
            "card_id": self.card_id,
            "card_status": self.card_status,
            "wins": self.wins,
            "losses": self.losses,
            "settled_tickets": self.settled_tickets,
            "profit_loss_units": self.profit_loss_units,
            "model_expected_wins": self.sum_p_ticket,
            "actual_minus_expected": self.wins - self.sum_p_ticket,
            "notes": self.notes,
        }


class SeasonLedger:
    """Append-only season record. Every week appears, including empty ones."""

    def __init__(self, path: Path | str):
        self._ledger = AppendOnlyLedger(path)

    @property
    def path(self) -> Path:
        return self._ledger.path

    def record_week(self, entry: WeekLedgerEntry) -> dict:
        return self._ledger.append(entry.to_dict())

    def entries(self, season: int | None = None) -> list:
        rows = self._ledger.entries()
        if season is not None:
            rows = [row for row in rows if row.get("season") == season]
        return rows

    def latest_per_week(self, season: int) -> list:
        """The most recent entry for each week, since a week can be re-recorded."""
        latest: dict[int, dict] = {}
        for row in self.entries(season):
            latest[row["week"]] = row
        return [latest[week] for week in sorted(latest)]

    def season_status(self, season: int, *, placements=None, settlements=None) -> dict:
        """Season totals, with placement and settlement facts **derived at read time**.

        The grading ledger records what the model saw and proposed — immutable, written
        once when the week was graded. Placement and settlement facts are *not* copied
        into it, because that would go stale the moment the operator placed or settled
        anything. Instead they are derived from the append-only placement and settlement
        ledgers every time status is requested.

        The operator therefore never has to re-record a week merely to synchronise it.

        Only MODEL_DESIGNATED placements count toward v1.0 figures; external wagers are
        reported separately.
        """
        weeks = self.latest_per_week(season)
        placements = [p for p in (placements or []) if p.get("season") == season]
        settlements = list(settlements or [])

        model = [p for p in placements if p.get("designation") == "MODEL_DESIGNATED"]
        external = [p for p in placements if p.get("designation") != "MODEL_DESIGNATED"]
        model_ids = {p["placement_id"] for p in model}
        model_settlements = [
            s for s in settlements if s.get("placement_id") in model_ids
        ]

        by_week = self.derive_weeks(season, placements=placements, settlements=settlements)

        return {
            "season": season,
            "weeks_recorded": len(weeks),
            "weeks_with_zero_qualifying_legs": sum(
                1 for row in weeks if row["qualifying_primary_legs"] == 0
            ),
            "weeks_with_no_constructible_ticket": sum(
                1 for row in weeks if row["proposed_tickets"] == 0
            ),
            "weeks_with_zero_placements": sum(
                1 for row in by_week if row["placed_tickets"] == 0
            ),
            "total_qualifying_legs": sum(row["qualifying_primary_legs"] for row in weeks),
            "total_positive_ev_tickets": sum(row["positive_ev_tickets"] for row in weeks),
            "total_proposed_tickets": sum(row["proposed_tickets"] for row in weeks),
            # Derived from the placement ledger, never from the grading record.
            "total_placed_tickets": len(model),
            "total_units_staked": float(sum(p.get("stake_units", 0) for p in model)),
            "total_wins": sum(
                1 for s in model_settlements if s.get("book_settlement") == "WIN"
            ),
            "total_losses": sum(
                1 for s in model_settlements if s.get("book_settlement") == "LOSS"
            ),
            "total_voided_or_cancelled": sum(
                1 for s in model_settlements
                if s.get("book_settlement") in ("VOID", "CANCELLED", "PUSH")
            ),
            "settled_tickets": len(model_settlements),
            "unsettled_tickets": len(model) - len(model_settlements),
            "total_profit_loss_units": float(
                sum(s.get("profit_loss_units", 0.0) for s in model_settlements)
            ),
            "model_expected_wins": float(
                sum(float(p.get("p_ticket") or 0.0) for p in model)
            ),
            "external_non_model_placements": len(external),
            "refused_attempts": 0,
        }

    def derive_weeks(self, season: int, *, placements=None, settlements=None) -> list:
        """Per-week view combining the immutable grading record with derived activity."""
        placements = [p for p in (placements or []) if p.get("season") == season]
        settlements = list(settlements or [])
        settlement_by_placement = {
            s["placement_id"]: s for s in settlements if "placement_id" in s
        }

        rows = []
        for entry in self.latest_per_week(season):
            week = entry["week"]
            week_model = [
                p for p in placements
                if p.get("week") == week and p.get("designation") == "MODEL_DESIGNATED"
            ]
            week_external = [
                p for p in placements
                if p.get("week") == week and p.get("designation") != "MODEL_DESIGNATED"
            ]
            week_settlements = [
                settlement_by_placement[p["placement_id"]]
                for p in week_model
                if p["placement_id"] in settlement_by_placement
            ]
            rows.append(
                {
                    # Immutable grading facts, exactly as recorded.
                    "season": season,
                    "week": week,
                    "games_scanned": entry["games_scanned"],
                    "qualifying_primary_legs": entry["qualifying_primary_legs"],
                    "top_four_legs": entry["top_four_legs"],
                    "positive_ev_tickets": entry["positive_ev_tickets"],
                    "proposed_tickets": entry["proposed_tickets"],
                    "card_id": entry.get("card_id", ""),
                    # Derived at read time from the append-only ledgers.
                    "placed_tickets": len(week_model),
                    "units_staked": float(
                        sum(p.get("stake_units", 0) for p in week_model)
                    ),
                    "settled_tickets": len(week_settlements),
                    "wins": sum(
                        1 for s in week_settlements if s.get("book_settlement") == "WIN"
                    ),
                    "losses": sum(
                        1 for s in week_settlements if s.get("book_settlement") == "LOSS"
                    ),
                    "profit_loss_units": float(
                        sum(s.get("profit_loss_units", 0.0) for s in week_settlements)
                    ),
                    "model_expected_wins": float(
                        sum(float(p.get("p_ticket") or 0.0) for p in week_model)
                    ),
                    "external_non_model_placements": len(week_external),
                }
            )
        return rows
