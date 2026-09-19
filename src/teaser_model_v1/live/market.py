"""Market ingestion: a first-class manual path, plus an optional provider adapter hook.

The manual path is **required infrastructure and must always work**, with no API key, no
network and no vendor account. The adapter interface exists so a feed can be attached
later; nothing in this package depends on one existing.
"""

from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from teaser_model_v1.live.provenance import require_aware, utc_now
from teaser_model_v1.live.schemas import (
    MarketQuote,
    MarketSnapshot,
    MarketValidationError,
    normalize_team,
)

#: Columns the manual CSV template uses. ``game_id`` and ``kickoff`` may be omitted and
#: derived, but supplying them is preferred.
TEMPLATE_COLUMNS = (
    "game_id",
    "season",
    "week",
    "kickoff",
    "away_team",
    "home_team",
    "team",
    "spread",
    "total",
    "sportsbook",
    "captured_at",
    "source_reference",
    "raw_source_value",
    "notes",
)

TEMPLATE_HELP = """\
# Manual NFL market input for frozen Teaser Model v1.0.
#
# One row per SIDE you want considered. Two rows per game gives both sides.
#   spread   : from this team's perspective. +2.5 means receiving 2.5.
#              Must be an exact multiple of 0.5. Never round or average books.
#   total    : the game total, exact multiple of 0.5.
#   kickoff / captured_at : ISO-8601 WITH an offset, e.g. 2026-09-20T13:00:00-04:00
#              A timestamp without an offset is rejected, not assumed.
#   sportsbook : the book this line came from.
#
# Delete these comment lines or leave them; lines starting with # are ignored.
"""


def write_template(path: Path | str, *, season: int, week: int) -> Path:
    """Write an empty manual-input CSV with a worked example row."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        handle.write(TEMPLATE_HELP)
        writer = csv.DictWriter(handle, fieldnames=list(TEMPLATE_COLUMNS))
        writer.writeheader()
        writer.writerow(
            {
                "game_id": f"{season}_{week:02d}_AWAY_HOME",
                "season": season,
                "week": week,
                "kickoff": "2026-09-20T13:00:00-04:00",
                "away_team": "BUF",
                "home_team": "MIA",
                "team": "MIA",
                "spread": "2.5",
                "total": "44.5",
                "sportsbook": "EXAMPLE_BOOK",
                "captured_at": "2026-09-19T10:00:00-04:00",
                "source_reference": "screenshot-or-url",
                "raw_source_value": "MIA +2.5 (o/u 44.5)",
                "notes": "EXAMPLE ROW - delete before use",
            }
        )
    return path


def _derive_game_id(row: dict) -> str:
    return (
        f"{int(row['season'])}_{int(row['week']):02d}_"
        f"{normalize_team(row['away_team'])}_{normalize_team(row['home_team'])}"
    )


def read_market_csv(
    path: Path | str,
    *,
    sportsbook: str | None = None,
    captured_at: datetime | str | None = None,
    label: str = "",
    ingestion_method: str = "manual_csv",
    notes: str = "",
) -> MarketSnapshot:
    """Read, validate and freeze a manual market file into one snapshot.

    Every failure is reported with its row number rather than being skipped: a silently
    dropped line is a missing leg, and a missing leg changes the card.
    """
    path = Path(path)
    rows, problems = [], []

    with path.open(newline="") as handle:
        lines = [line for line in handle if not line.lstrip().startswith("#")]
    reader = csv.DictReader(lines)

    for number, row in enumerate(reader, start=2):
        if not any((value or "").strip() for value in row.values()):
            continue
        if (row.get("notes") or "").strip().upper().startswith("EXAMPLE ROW"):
            continue
        try:
            season = int(row["season"])
            week = int(row["week"])
            game_id = (row.get("game_id") or "").strip() or _derive_game_id(row)
            quote = MarketQuote(
                game_id=game_id,
                season=season,
                week=week,
                kickoff=require_aware(row["kickoff"], field=f"row {number} kickoff"),
                home_team=row["home_team"],
                away_team=row["away_team"],
                team=row["team"],
                spread=(row["spread"] or "").strip(),
                total=(row["total"] or "").strip(),
                sportsbook=(sportsbook or row.get("sportsbook") or "").strip(),
                captured_at=require_aware(
                    captured_at or row["captured_at"], field=f"row {number} captured_at"
                ),
                ingestion_method=ingestion_method,
                source_reference=(row.get("source_reference") or "").strip(),
                raw_source_value=(row.get("raw_source_value") or "").strip(),
                notes=(row.get("notes") or "").strip(),
            )
            rows.append(quote)
        except (KeyError, ValueError, TypeError, MarketValidationError) as exc:
            problems.append(f"  row {number}: {exc}")

    if problems:
        raise MarketValidationError(
            f"{len(problems)} row(s) in {path.name} could not be accepted:\n"
            + "\n".join(problems)
        )
    if not rows:
        raise MarketValidationError(f"{path.name} contains no usable market rows")

    seasons = {quote.season for quote in rows}
    weeks = {quote.week for quote in rows}
    if len(seasons) != 1 or len(weeks) != 1:
        raise MarketValidationError(
            f"one snapshot must cover one season and week; found {sorted(seasons)} / "
            f"{sorted(weeks)}"
        )

    books = {quote.sportsbook for quote in rows}
    captures = {quote.captured_at for quote in rows}

    return MarketSnapshot(
        season=rows[0].season,
        week=rows[0].week,
        captured_at=max(captures),
        sportsbook=books.pop() if len(books) == 1 else "MIXED",
        ingestion_method=ingestion_method,
        quotes=tuple(rows),
        label=label,
        notes=notes,
    )


# ---------------------------------------------------------------------------------------
# Optional provider adapters
# ---------------------------------------------------------------------------------------


class MarketProvider(ABC):
    """Interface a live odds feed can implement later.

    Deliberately abstract and unimplemented. No paid provider is wired in, no credentials
    are read or fabricated, and **no part of the weekly workflow requires one**: the manual
    CSV path is the supported route until a real feed is configured.

    An implementation must return quotes that already satisfy the schema's validation —
    exact half-points, timezone-aware timestamps, a named sportsbook — or raise.
    """

    name: str = "unconfigured"

    @abstractmethod
    def fetch(self, season: int, week: int) -> MarketSnapshot:
        """Return a validated snapshot for the requested week."""

    def describe(self) -> dict:
        return {"provider": self.name, "configured": False}


class NoProviderConfigured(MarketProvider):
    """The default: there is no feed, and the manual path is the way in."""

    name = "none"

    def fetch(self, season: int, week: int) -> MarketSnapshot:
        raise NotImplementedError(
            "No market provider is configured. Use the manual CSV path: "
            "`teaser-live market-template` then `teaser-live ingest-market`."
        )


def available_providers() -> dict:
    """Registry of adapters. Empty by design until one is genuinely configured."""
    return {"none": NoProviderConfigured()}
