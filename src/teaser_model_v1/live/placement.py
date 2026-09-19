"""The placement ledger: what was ACTUALLY wagered.

Two rules govern this module:

1. **Nothing is placed unless a human explicitly records it.** There is no path from
   PROPOSED to PLACED that does not pass through an operator action. A proposed card is a
   suggestion; this ledger is the only record of a real wager.
2. **This software never submits a wager.** It writes rows describing what the operator
   says they did at a sportsbook.

The ledger is append-only. A mistaken entry is superseded by a correction record; the
original row stays.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from teaser_model_v1.engine.constants import MAX_UNITS_PER_LEG_PER_WEEK, UNITS_PER_TICKET
from teaser_model_v1.live.card import WeeklyCard, exposure_after, exposure_violations
from teaser_model_v1.live.provenance import iso, new_record_id, require_aware, utc_now
from teaser_model_v1.live.schemas import MarketValidationError

#: Marks a wager the operator made outside the model. Recorded for completeness and
#: excluded from every v1.0 performance number.
EXTERNAL_NON_MODEL = "EXTERNAL_NON_MODEL"
MODEL_DESIGNATED = "MODEL_DESIGNATED"


class ExposureCapViolation(ValueError):
    """Raised when a placement would break the frozen 2-unit-per-leg weekly cap."""


class PlacementRefused(ValueError):
    """Raised when a placement cannot be recorded as model-designated."""


@dataclass(frozen=True)
class PlacementRecord:
    """One actually-placed wager, as reported by the operator."""

    season: int
    week: int
    ticket_key: str
    leg_ids: tuple
    sportsbook: str
    american_odds: str
    stake_units: float
    placed_at: datetime
    market_snapshot_id: str
    price_snapshot_id: str
    card_id: str
    p_ticket: str
    break_even: str
    ev_at_placement: str
    exposure_after: dict
    designation: str = MODEL_DESIGNATED
    recorded_by: str = ""
    book_reference: str = ""
    notes: str = ""
    placement_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "placed_at", require_aware(self.placed_at, field="placed_at"))
        object.__setattr__(self, "leg_ids", tuple(self.leg_ids))
        if not self.sportsbook.strip():
            raise PlacementRefused("a placement must name the sportsbook")
        if self.stake_units <= 0:
            raise PlacementRefused("stake must be positive")
        if not self.placement_id:
            object.__setattr__(
                self, "placement_id",
                new_record_id(f"plc_{self.season}w{self.week:02d}", self._hash_payload()),
            )

    def _hash_payload(self) -> dict:
        return {
            "kind": "placement",
            "season": self.season,
            "week": self.week,
            "ticket_key": self.ticket_key,
            "leg_ids": list(self.leg_ids),
            "sportsbook": self.sportsbook,
            "american_odds": self.american_odds,
            "stake_units": self.stake_units,
            "placed_at": iso(self.placed_at),
            "market_snapshot_id": self.market_snapshot_id,
            "price_snapshot_id": self.price_snapshot_id,
            "card_id": self.card_id,
            "designation": self.designation,
            "recorded_by": self.recorded_by,
            "book_reference": self.book_reference,
        }

    def to_dict(self) -> dict:
        payload = self._hash_payload()
        payload.update(
            {
                "placement_id": self.placement_id,
                "p_ticket": self.p_ticket,
                "break_even": self.break_even,
                "ev_at_placement": self.ev_at_placement,
                "exposure_after": dict(sorted(self.exposure_after.items())),
                "n_legs": len(self.leg_ids),
                "notes": self.notes,
            }
        )
        return payload

    @property
    def counts_toward_model(self) -> bool:
        return self.designation == MODEL_DESIGNATED


class PlacementLedger:
    """Append-only ledger of actual placements, one file per season."""

    def __init__(self, path: Path | str):
        from teaser_model_v1.live.snapshot import AppendOnlyLedger

        self._ledger = AppendOnlyLedger(path)

    @property
    def path(self) -> Path:
        return self._ledger.path

    def entries(self, season: int | None = None, week: int | None = None) -> list:
        rows = self._ledger.entries()
        if season is not None:
            rows = [row for row in rows if row.get("season") == season]
        if week is not None:
            rows = [row for row in rows if row.get("week") == week]
        return rows

    def model_entries(self, season: int | None = None, week: int | None = None) -> list:
        return [
            row
            for row in self.entries(season, week)
            if row.get("designation") == MODEL_DESIGNATED
        ]

    def current_exposure(self, season: int, week: int) -> dict:
        """Aggregate model-designated units per leg for the week."""
        exposure: dict[str, float] = {}
        for row in self.model_entries(season, week):
            for leg_id in row.get("leg_ids", []):
                exposure[leg_id] = exposure.get(leg_id, 0) + row.get("stake_units", 0)
        return exposure

    def record(
        self,
        card: WeeklyCard,
        ticket_key: str,
        *,
        sportsbook: str,
        american_odds: str,
        placed_at: datetime,
        recorded_by: str,
        stake_units: float = float(UNITS_PER_TICKET),
        designation: str = MODEL_DESIGNATED,
        book_reference: str = "",
        notes: str = "",
        allow_unproposed: bool = False,
        recheck=None,
    ) -> PlacementRecord:
        """Record an actual placement. This is the ONLY way a wager enters the record.

        A model-designated placement must correspond to a ticket the card actually
        proposed, and must not break the frozen 2-unit aggregate cap.

        ``recheck`` is the placement-time re-check result, when one has been run. If it is
        supplied, the ticket must be **VALIDATED** in it: a ticket the re-check discarded
        is stale, and the frozen rule is to rebuild rather than reuse it. Supplying the
        re-check is strongly preferred, since the specification requires a re-check
        immediately before any real wager.

        A wager the operator made outside the model is recordable with
        ``designation=EXTERNAL_NON_MODEL``; it is stored for completeness and excluded
        from every v1.0 performance figure.
        """
        view = card.ticket(ticket_key)
        if view is None:
            raise PlacementRefused(
                f"ticket {ticket_key} is not on card {card.card_id}. A placement must "
                "reference a ticket the model actually constructed."
            )

        if designation == MODEL_DESIGNATED:
            if recheck is not None:
                verdicts = {t.ticket_key: t.verdict for t in recheck.tickets}
                verdict = verdicts.get(ticket_key)
                if verdict is None:
                    raise PlacementRefused(
                        f"ticket {ticket_key} was not covered by re-check "
                        f"{recheck.recheck_id}. Re-check it against the current board "
                        "before recording a placement."
                    )
                if verdict != "VALIDATED":
                    raise PlacementRefused(
                        f"ticket {ticket_key} was DISCARDED at re-check "
                        f"{recheck.recheck_id}: "
                        f"{'; '.join(t.reasons[0] for t in recheck.tickets if t.ticket_key == ticket_key and t.reasons) or 'see re-check record'}. "
                        "A discarded ticket is never reused, substituted or downgraded — "
                        "rebuild from the current board."
                    )
            if not view.selected and not allow_unproposed:
                raise PlacementRefused(
                    f"ticket {ticket_key} was NOT on the proposed card "
                    f"(status: {view.status}). A model-designated placement must be one "
                    "the frozen selection proposed. Record it as EXTERNAL_NON_MODEL if you "
                    "placed it anyway."
                )
            projected = exposure_after(
                self.current_exposure(card.season, card.week), view.leg_ids, stake_units
            )
            violations = exposure_violations(projected, MAX_UNITS_PER_LEG_PER_WEEK)
            if violations:
                raise ExposureCapViolation(
                    "this placement would exceed the frozen "
                    f"{MAX_UNITS_PER_LEG_PER_WEEK}-unit weekly cap on "
                    f"{', '.join(f'{leg} ({units} units)' for leg, units in sorted(violations.items()))}. "
                    "Record it as EXTERNAL_NON_MODEL if you placed it outside the model."
                )
        else:
            projected = exposure_after(
                self.current_exposure(card.season, card.week), view.leg_ids, 0
            )

        record = PlacementRecord(
            season=card.season,
            week=card.week,
            ticket_key=ticket_key,
            leg_ids=view.leg_ids,
            sportsbook=sportsbook,
            american_odds=american_odds,
            stake_units=stake_units,
            placed_at=placed_at,
            market_snapshot_id=card.market_snapshot_id,
            price_snapshot_id=card.price_snapshot_id,
            card_id=card.card_id,
            p_ticket=repr(view.p_ticket),
            break_even=view.break_even,
            ev_at_placement=view.ev_per_unit,
            exposure_after=projected,
            designation=designation,
            recorded_by=recorded_by,
            book_reference=book_reference,
            notes=notes,
        )
        self._ledger.append(record.to_dict())
        return record
