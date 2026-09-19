"""Record types for the prospective operations layer.

Every record is an immutable value object that serialises to canonical JSON. Decimals stay
exact, timestamps stay timezone-aware, and nothing here interprets the model — geometry and
probability come from :mod:`teaser_model_v1.engine`.

The market schema is **provider-neutral**: it describes what a line looked like and where
it came from, not which vendor supplied it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal

from teaser_model_v1.engine.constants import TEASER_POINTS
from teaser_model_v1.engine.numeric import on_half_point_grid, to_decimal
from teaser_model_v1.live.provenance import canonical_json, iso, new_record_id, require_aware

#: The 32 current NFL clubs, in the abbreviation style this project's data uses.
NFL_TEAMS = frozenset(
    {
        "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
        "GB", "HOU", "IND", "JAX", "KC", "LA", "LAC", "LV", "MIA", "MIN", "NE", "NO",
        "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS",
    }
)

#: Historical relocations, accepted on input and normalised forward.
TEAM_ALIASES = {
    "OAK": "LV", "SD": "LAC", "STL": "LA", "LAR": "LA", "WSH": "WAS", "JAC": "JAX",
    "ARZ": "ARI", "BLT": "BAL", "CLV": "CLE", "HST": "HOU",
}

#: Plausibility envelope for an NFL market. Outside this a value is treated as an entry
#: error, not as a line. These are input-validation guards, not model parameters.
MAX_ABS_SPREAD = Decimal("30")
MIN_TOTAL = Decimal("20")
MAX_TOTAL = Decimal("80")

# TEASER_POINTS is imported from the frozen engine, never redefined here: a second
# definition could drift out of step with the specification.


class MarketValidationError(ValueError):
    """Raised when a market row cannot be trusted as a line."""


def normalize_team(value: str) -> str:
    """Upper-case, alias-resolve and validate an NFL team code."""
    if not isinstance(value, str) or not value.strip():
        raise MarketValidationError(f"team is missing or not a string: {value!r}")
    code = value.strip().upper()
    code = TEAM_ALIASES.get(code, code)
    if code not in NFL_TEAMS:
        raise MarketValidationError(f"unrecognised NFL team code: {value!r}")
    return code


def validate_spread(value, *, field_name: str = "spread") -> Decimal:
    """Exact Decimal spread on the 0.5 grid, inside a plausible envelope.

    A value off the half-point grid is rejected outright: an averaged or rounded line
    destroys the half-point fidelity this model depends on.
    """
    spread = to_decimal(value)
    if not on_half_point_grid(spread):
        raise MarketValidationError(
            f"{field_name} {spread} is not a multiple of 0.5. A rounded or averaged line "
            "is unusable for this model."
        )
    if abs(spread) > MAX_ABS_SPREAD:
        raise MarketValidationError(f"{field_name} {spread} is outside +/-{MAX_ABS_SPREAD}")
    return spread


def validate_total(value, *, field_name: str = "total") -> Decimal:
    total = to_decimal(value)
    if not on_half_point_grid(total):
        raise MarketValidationError(f"{field_name} {total} is not a multiple of 0.5")
    if not (MIN_TOTAL <= total <= MAX_TOTAL):
        raise MarketValidationError(
            f"{field_name} {total} is outside the plausible range [{MIN_TOTAL}, {MAX_TOTAL}]"
        )
    return total


# ---------------------------------------------------------------------------------------
# Market
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class MarketQuote:
    """One side of one game as quoted by one book at one moment.

    ``spread`` is from ``team``'s perspective: positive means receiving points.
    ``raw_source_value`` preserves exactly what the operator or feed supplied, before any
    normalisation, so a transcription question can always be settled later.
    """

    game_id: str
    season: int
    week: int
    kickoff: datetime
    home_team: str
    away_team: str
    team: str
    spread: Decimal
    total: Decimal
    sportsbook: str
    captured_at: datetime
    ingestion_method: str
    source_reference: str = ""
    raw_source_value: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "home_team", normalize_team(self.home_team))
        object.__setattr__(self, "away_team", normalize_team(self.away_team))
        object.__setattr__(self, "team", normalize_team(self.team))
        object.__setattr__(self, "spread", validate_spread(self.spread))
        object.__setattr__(self, "total", validate_total(self.total))
        object.__setattr__(self, "kickoff", require_aware(self.kickoff, field="kickoff"))
        object.__setattr__(
            self, "captured_at", require_aware(self.captured_at, field="captured_at")
        )
        if self.home_team == self.away_team:
            raise MarketValidationError(f"{self.game_id}: home and away are the same team")
        if self.team not in (self.home_team, self.away_team):
            raise MarketValidationError(
                f"{self.game_id}: quoted team {self.team} is not in this game"
            )
        if not str(self.sportsbook).strip():
            raise MarketValidationError(f"{self.game_id}: sportsbook is required")
        if not str(self.ingestion_method).strip():
            raise MarketValidationError(f"{self.game_id}: ingestion_method is required")

    @property
    def opponent(self) -> str:
        return self.away_team if self.team == self.home_team else self.home_team

    @property
    def leg_key(self) -> str:
        return f"{self.game_id}-{self.team}"

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["spread"] = str(self.spread)
        payload["total"] = str(self.total)
        payload["kickoff"] = iso(self.kickoff)
        payload["captured_at"] = iso(self.captured_at)
        return payload


@dataclass(frozen=True)
class MarketSnapshot:
    """An immutable set of quotes captured together.

    A later capture is a **new snapshot**, never an edit of this one.
    """

    season: int
    week: int
    captured_at: datetime
    sportsbook: str
    ingestion_method: str
    quotes: tuple
    label: str = ""
    notes: str = ""
    snapshot_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "captured_at", require_aware(self.captured_at, field="captured_at")
        )
        object.__setattr__(self, "quotes", tuple(self.quotes))
        seen = set()
        for quote in self.quotes:
            if quote.leg_key in seen:
                raise MarketValidationError(
                    f"duplicate quote for {quote.leg_key} in one snapshot"
                )
            seen.add(quote.leg_key)
            if (quote.season, quote.week) != (self.season, self.week):
                raise MarketValidationError(
                    f"{quote.leg_key}: season/week does not match the snapshot"
                )
        if not self.snapshot_id:
            object.__setattr__(
                self, "snapshot_id", new_record_id(f"mkt_{self.season}w{self.week:02d}",
                                                   self._hash_payload())
            )

    def _hash_payload(self) -> dict:
        return {
            "kind": "market_snapshot",
            "season": self.season,
            "week": self.week,
            "captured_at": iso(self.captured_at),
            "sportsbook": self.sportsbook,
            "ingestion_method": self.ingestion_method,
            "label": self.label,
            "quotes": [quote.to_dict() for quote in self.quotes],
        }

    @property
    def games(self) -> tuple:
        return tuple(sorted({quote.game_id for quote in self.quotes}))

    def to_dict(self) -> dict:
        payload = self._hash_payload()
        payload["snapshot_id"] = self.snapshot_id
        payload["notes"] = self.notes
        return payload

    def canonical(self) -> str:
        return canonical_json(self.to_dict())


# ---------------------------------------------------------------------------------------
# Teaser price
# ---------------------------------------------------------------------------------------


def american_to_decimal(american: float) -> Decimal:
    """American price to decimal odds, exactly."""
    value = to_decimal(american)
    if value == 0:
        raise MarketValidationError("American odds of 0 are not a price")
    if value > 0:
        return Decimal(1) + value / Decimal(100)
    return Decimal(1) + Decimal(100) / abs(value)


def decimal_to_american(decimal_odds) -> Decimal:
    """Decimal odds to American price."""
    value = to_decimal(decimal_odds)
    if value <= 1:
        raise MarketValidationError(f"decimal odds must exceed 1.0, got {value}")
    profit = value - Decimal(1)
    if profit >= 1:
        return profit * Decimal(100)
    return -Decimal(100) / profit


@dataclass(frozen=True)
class TeaserPriceQuote:
    """An **actual** teaser menu price observed at a sportsbook.

    This is the object the historical work never had. It is what makes break-even and EV
    computable, and therefore what makes a ticket placement-eligible at all.
    """

    ticket_size: int
    sportsbook: str
    captured_at: datetime
    american_odds: Decimal | None = None
    decimal_odds: Decimal | None = None
    teaser_points: int = TEASER_POINTS
    source_reference: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "captured_at", require_aware(self.captured_at, field="captured_at")
        )
        if self.ticket_size not in (2, 3):
            raise MarketValidationError(
                f"ticket_size must be 2 or 3, got {self.ticket_size}"
            )
        if self.teaser_points != TEASER_POINTS:
            raise MarketValidationError(
                f"this project operates {TEASER_POINTS}-point teasers only; "
                f"got {self.teaser_points}"
            )
        if self.american_odds is None and self.decimal_odds is None:
            raise MarketValidationError(
                "supply the offered price as American or decimal odds"
            )
        if self.american_odds is not None:
            american = to_decimal(self.american_odds)
            object.__setattr__(self, "american_odds", american)
            object.__setattr__(self, "decimal_odds", american_to_decimal(american))
        else:
            decimal_odds = to_decimal(self.decimal_odds)
            object.__setattr__(self, "decimal_odds", decimal_odds)
            object.__setattr__(self, "american_odds", decimal_to_american(decimal_odds))
        if not str(self.sportsbook).strip():
            raise MarketValidationError("sportsbook is required on a teaser price")

    @property
    def net_profit_per_unit(self) -> Decimal:
        """Canonical net profit per 1 unit staked."""
        return self.decimal_odds - Decimal(1)

    def to_dict(self) -> dict:
        return {
            "ticket_size": self.ticket_size,
            "teaser_points": self.teaser_points,
            "sportsbook": self.sportsbook,
            "captured_at": iso(self.captured_at),
            "american_odds": str(self.american_odds),
            "decimal_odds": str(self.decimal_odds),
            "net_profit_per_unit": str(self.net_profit_per_unit),
            "source_reference": self.source_reference,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class TeaserPriceSnapshot:
    """The teaser menu as observed at one moment. Immutable; a later capture is new."""

    season: int
    week: int
    captured_at: datetime
    sportsbook: str
    quotes: tuple
    label: str = ""
    notes: str = ""
    snapshot_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "captured_at", require_aware(self.captured_at, field="captured_at")
        )
        object.__setattr__(self, "quotes", tuple(self.quotes))
        seen = set()
        for quote in self.quotes:
            if quote.ticket_size in seen:
                raise MarketValidationError(
                    f"two prices supplied for a {quote.ticket_size}-team teaser in one "
                    "snapshot; capture one menu per snapshot"
                )
            seen.add(quote.ticket_size)
        if not self.snapshot_id:
            object.__setattr__(
                self, "snapshot_id",
                new_record_id(f"prc_{self.season}w{self.week:02d}", self._hash_payload()),
            )

    def _hash_payload(self) -> dict:
        return {
            "kind": "teaser_price_snapshot",
            "season": self.season,
            "week": self.week,
            "captured_at": iso(self.captured_at),
            "sportsbook": self.sportsbook,
            "label": self.label,
            "quotes": [quote.to_dict() for quote in self.quotes],
        }

    def profit_by_size(self) -> dict:
        """``{ticket_size: net profit per unit}`` for the engine.

        A size absent from the menu is absent here, so the engine leaves its EV undefined
        and those tickets can never be placement-eligible.
        """
        return {q.ticket_size: float(q.net_profit_per_unit) for q in self.quotes}

    def quote_for(self, ticket_size: int):
        for quote in self.quotes:
            if quote.ticket_size == ticket_size:
                return quote
        return None

    def to_dict(self) -> dict:
        payload = self._hash_payload()
        payload["snapshot_id"] = self.snapshot_id
        payload["notes"] = self.notes
        return payload
