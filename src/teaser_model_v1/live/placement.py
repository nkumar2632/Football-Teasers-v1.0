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
from datetime import datetime, timedelta
from pathlib import Path

from teaser_model_v1.engine.constants import MAX_UNITS_PER_LEG_PER_WEEK, UNITS_PER_TICKET
from teaser_model_v1.live.card import WeeklyCard, exposure_after, exposure_violations
from teaser_model_v1.live.provenance import iso, new_record_id, require_aware, utc_now
from teaser_model_v1.live.schemas import MarketValidationError

#: How stale the validating re-check may be at the moment of placement. Beyond this the
#: board is no longer demonstrably current and the operator must re-check again.
MAX_RECHECK_AGE = timedelta(minutes=30)

#: How far the teaser-price capture may lag the re-check and still count as
#: contemporaneous. EV is only as good as the price it was computed from.
MAX_PRICE_LAG = timedelta(minutes=30)

#: Marks a wager the operator made outside the model. Recorded for completeness and
#: excluded from every v1.0 performance number.
EXTERNAL_NON_MODEL = "EXTERNAL_NON_MODEL"
MODEL_DESIGNATED = "MODEL_DESIGNATED"


class ExposureCapViolation(ValueError):
    """Raised when a placement would break the frozen 2-unit-per-leg weekly cap."""


class PlacementRefused(ValueError):
    """Raised when a placement cannot be recorded as model-designated.

    There is deliberately **no override**. A model-designated placement that fails any
    check cannot be forced through; the operator either re-checks against a current board
    or records the wager as EXTERNAL_NON_MODEL, where it is excluded from v1.0 results.
    """


class PostKickoffPlacement(PlacementRefused):
    """Raised when a model-designated placement would land at or after kickoff.

    v1.0 is a **pregame** teaser model. Placing into a started game would price the wager
    off a live market the model was never specified against.
    """


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
    #: The re-check that authorised this placement. Always set for MODEL_DESIGNATED.
    recheck_id: str = ""
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
            "recheck_id": self.recheck_id,
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
    """Append-only ledger of actual placements, plus an append-only log of refusals.

    A refused attempt creates **no placement record**. It is logged separately so the
    audit trail shows what was tried and why it was rejected, without any risk of a
    refused wager being mistaken for a placed one.
    """

    def __init__(self, path: Path | str):
        from teaser_model_v1.live.snapshot import AppendOnlyLedger

        self._ledger = AppendOnlyLedger(path)
        self._refusals = AppendOnlyLedger(Path(path).with_name("refusals.jsonl"))

    @property
    def refusals_path(self) -> Path:
        return self._refusals.path

    def refusals(self, season: int | None = None, week: int | None = None) -> list:
        rows = self._refusals.entries()
        if season is not None:
            rows = [row for row in rows if row.get("season") == season]
        if week is not None:
            rows = [row for row in rows if row.get("week") == week]
        return rows

    def log_refusal(self, *, card, ticket_key: str, placed_at, reason: str,
                    attempted_by: str = "", designation: str = MODEL_DESIGNATED) -> dict:
        """Record a refused attempt. This is NOT a placement and never counts as one."""
        return self._refusals.append(
            {
                "kind": "placement_refused",
                "season": card.season,
                "week": card.week,
                "card_id": card.card_id,
                "ticket_key": ticket_key,
                "designation": designation,
                "attempted_placed_at": iso(require_aware(placed_at, field="placed_at"))
                if placed_at else "",
                "attempted_by": attempted_by,
                "reason": reason,
                "logged_at": iso(utc_now()),
                "placement_created": False,
            }
        )

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

    def validate_model_placement(
        self,
        card,
        ticket_key: str,
        *,
        placed_at: datetime,
        recheck,
        known_rechecks=None,
        stake_units: float = float(UNITS_PER_TICKET),
    ) -> dict:
        """Run every model-designated gate and raise on the first failure.

        Separated from :meth:`record` so the CLI can refuse **before** writing anything.
        Returns the projected exposure when every gate passes.

        The gates, in order:

        1. the ticket exists on the card and was **proposed** by the frozen selection;
        2. a re-check is supplied — it is mandatory, with no override;
        3. that re-check is for this card and covers this ticket;
        4. it is the most recent applicable re-check;
        5. its verdict for this ticket is VALIDATED;
        6. it used a genuinely later market snapshot than grading;
        7. it used a contemporaneous **actual** teaser-price snapshot;
        8. it is not stale relative to the moment of placement;
        9. placement and both snapshots precede kickoff for **every** constituent game;
        10. the 2-unit aggregate exposure cap still holds.
        """
        view = card.ticket(ticket_key)
        if view is None:
            raise PlacementRefused(
                f"ticket {ticket_key} is not on card {card.card_id}. A placement must "
                "reference a ticket the model actually constructed."
            )
        if not view.selected:
            raise PlacementRefused(
                f"ticket {ticket_key} was NOT on the proposed card "
                f"(status: {view.status}). A model-designated placement must be one the "
                "frozen selection proposed. Record it as EXTERNAL_NON_MODEL if you placed "
                "it anyway."
            )

        # ---- 2. the re-check is mandatory ------------------------------------------
        if recheck is None:
            raise PlacementRefused(
                "a model-designated placement requires a placement-time re-check. "
                "Run `recheck` against a current market and teaser-price snapshot and "
                "pass its id. There is no override: record the wager as "
                "EXTERNAL_NON_MODEL if you placed it without re-checking."
            )

        # ---- 3. it must belong to this card and cover this ticket ------------------
        if recheck.original_card_id != card.card_id:
            raise PlacementRefused(
                f"re-check {recheck.recheck_id} is for card "
                f"{recheck.original_card_id}, not {card.card_id}."
            )
        verdict = recheck.verdict_for(ticket_key)
        if verdict is None:
            raise PlacementRefused(
                f"ticket {ticket_key} was not covered by re-check "
                f"{recheck.recheck_id}. Re-check it against the current board before "
                "recording a placement."
            )

        # ---- 4. it must be the most recent applicable re-check ---------------------
        for other in known_rechecks or ():
            if other.original_card_id != card.card_id:
                continue
            if other.verdict_for(ticket_key) is None:
                continue
            if other.rechecked_at > recheck.rechecked_at:
                raise PlacementRefused(
                    f"re-check {recheck.recheck_id} is superseded by "
                    f"{other.recheck_id} (re-checked {other.rechecked_at.isoformat()}). "
                    "Use the most recent re-check for this ticket."
                )

        # ---- 5. the verdict must be VALIDATED ---------------------------------------
        if verdict != "VALIDATED":
            reasons = "; ".join(recheck.reasons_for(ticket_key)) or "see the re-check record"
            raise PlacementRefused(
                f"ticket {ticket_key} was DISCARDED at re-check {recheck.recheck_id}: "
                f"{reasons}. A discarded ticket is never reused, substituted or "
                "downgraded — rebuild from the current board."
            )

        # ---- 6. the market snapshot must genuinely post-date grading ----------------
        if recheck.new_market_snapshot_id == card.market_snapshot_id:
            raise PlacementRefused(
                f"re-check {recheck.recheck_id} used the same market snapshot the card "
                "was graded from. A re-check must validate against a NEW board."
            )
        if (
            recheck.new_market_captured_at is not None
            and recheck.new_market_captured_at <= card.graded_at
        ):
            raise PlacementRefused(
                f"re-check {recheck.recheck_id} used a market snapshot captured at "
                f"{recheck.new_market_captured_at.isoformat()}, which is not later than "
                f"grading at {card.graded_at.isoformat()}."
            )

        # ---- 7. a contemporaneous ACTUAL price ---------------------------------------
        if not recheck.new_price_snapshot_id:
            raise PlacementRefused(
                f"re-check {recheck.recheck_id} had no teaser-price snapshot. EV cannot "
                "be confirmed without an actual captured price, so the ticket is not "
                "placement-eligible."
            )
        if recheck.new_price_captured_at is not None:
            lag = abs(recheck.rechecked_at - recheck.new_price_captured_at)
            if lag > MAX_PRICE_LAG:
                raise PlacementRefused(
                    f"the teaser price used by re-check {recheck.recheck_id} was captured "
                    f"{lag} away from the re-check; it is not contemporaneous "
                    f"(limit {MAX_PRICE_LAG}). Re-capture the menu."
                )

        # ---- 8. the re-check must not be stale ---------------------------------------
        age = placed_at - recheck.rechecked_at
        if age < timedelta(0):
            raise PlacementRefused(
                f"placement at {placed_at.isoformat()} precedes re-check "
                f"{recheck.recheck_id} at {recheck.rechecked_at.isoformat()}."
            )
        if age > MAX_RECHECK_AGE:
            raise PlacementRefused(
                f"re-check {recheck.recheck_id} is {age} old at the moment of placement "
                f"(limit {MAX_RECHECK_AGE}). The board is no longer demonstrably current; "
                "re-check again."
            )

        # ---- 9. everything must precede kickoff --------------------------------------
        self._require_pregame(card, view, placed_at=placed_at, recheck=recheck)

        # ---- 10. the exposure cap ------------------------------------------------------
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
        return projected

    @staticmethod
    def _require_pregame(card, view, *, placed_at: datetime, recheck) -> None:
        """Every constituent game must still be pregame. One started leg fails the ticket.

        Checked against the kickoff on the **current** board where the re-check supplies
        one, falling back to the graded card. Placement, the validating market snapshot and
        the teaser-price snapshot must all strictly precede kickoff; exactly at kickoff
        fails, because the game has started.
        """
        kickoffs = dict(getattr(recheck, "leg_kickoffs", {}) or {})
        for leg in card.qualifying_legs:
            kickoffs.setdefault(leg.leg_id, leg.kickoff)

        for leg_id in view.leg_ids:
            raw = kickoffs.get(leg_id)
            if not raw:
                raise PlacementRefused(
                    f"no kickoff time is recorded for leg {leg_id}; a pregame model "
                    "cannot confirm the game has not started."
                )
            kickoff = require_aware(raw, field=f"{leg_id} kickoff")

            if placed_at >= kickoff:
                raise PostKickoffPlacement(
                    f"leg {leg_id} kicked off at {kickoff.isoformat()}; placement at "
                    f"{placed_at.isoformat()} is not pregame. v1.0 is a pregame model and "
                    "will not price a wager off a live market. If one leg of a multi-team "
                    "ticket has started, the whole ticket is refused."
                )
            if (
                recheck.new_market_captured_at is not None
                and recheck.new_market_captured_at >= kickoff
            ):
                raise PostKickoffPlacement(
                    f"the validating market snapshot was captured at "
                    f"{recheck.new_market_captured_at.isoformat()}, at or after kickoff "
                    f"for {leg_id} ({kickoff.isoformat()}). That is an in-game line."
                )
            if (
                recheck.new_price_captured_at is not None
                and recheck.new_price_captured_at >= kickoff
            ):
                raise PostKickoffPlacement(
                    f"the teaser price was captured at "
                    f"{recheck.new_price_captured_at.isoformat()}, at or after kickoff "
                    f"for {leg_id} ({kickoff.isoformat()}). That is an in-game price."
                )

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
        recheck=None,
        known_rechecks=None,
    ) -> PlacementRecord:
        """Record an actual placement. This is the ONLY way a wager enters the record.

        A **MODEL_DESIGNATED** placement must pass every gate in
        :meth:`validate_model_placement`, including a mandatory, current, VALIDATED
        re-check and a pregame timestamp. **There is no override flag.**

        A wager made outside the model is recordable with
        ``designation=EXTERNAL_NON_MODEL``. It is stored for completeness, is exempt from
        the model gates, and is excluded from every v1.0 performance figure.
        """
        placed_at = require_aware(placed_at, field="placed_at")
        view = card.ticket(ticket_key)

        if designation == MODEL_DESIGNATED:
            projected = self.validate_model_placement(
                card, ticket_key, placed_at=placed_at, recheck=recheck,
                known_rechecks=known_rechecks, stake_units=stake_units,
            )
        else:
            if view is None:
                raise PlacementRefused(
                    f"ticket {ticket_key} is not on card {card.card_id}."
                )
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
            recheck_id=getattr(recheck, "recheck_id", "") if recheck else "",
        )
        self._ledger.append(record.to_dict())
        return record
