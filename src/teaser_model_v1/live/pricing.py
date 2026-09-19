"""Capture of the ACTUAL sportsbook teaser menu.

The distinction this module exists to enforce:

* An **actual price** was observed at a named book at a recorded moment. It makes
  break-even and EV computable, and it is the only thing that can make a ticket
  placement-eligible.
* A **hypothetical price** is a what-if. Phase 3 used them for sensitivity analysis. One
  can never reach this module, and the engine independently refuses to treat a
  hypothetically-priced ticket as placement-eligible.

If no real price is supplied for a ticket size, the tickets of that size still display
their `P_ticket` — but break-even and EV are **UNAVAILABLE**, and they are not eligible.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from teaser_model_v1.live.provenance import require_aware
from teaser_model_v1.live.schemas import (
    MarketValidationError,
    TeaserPriceQuote,
    TeaserPriceSnapshot,
)

PRICE_COLUMNS = (
    "ticket_size",
    "american_odds",
    "decimal_odds",
    "sportsbook",
    "captured_at",
    "source_reference",
    "notes",
)

PRICE_TEMPLATE_HELP = """\
# ACTUAL teaser menu prices for frozen Teaser Model v1.0.
#
# Record the price the sportsbook is really showing for a 6-POINT teaser.
#   ticket_size   : 2 or 3
#   american_odds : e.g. -120 for a 2-team, +140 for a 3-team.  OR
#   decimal_odds  : e.g. 1.8333.  Supply exactly one of the two; the other is derived.
#   captured_at   : ISO-8601 WITH offset, e.g. 2026-09-20T12:40:00-04:00
#
# Do NOT enter a price you have not actually seen. A size you leave out simply has no
# price: its tickets will show a probability but no EV, and cannot be placed by the model.
"""


def write_price_template(path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        handle.write(PRICE_TEMPLATE_HELP)
        writer = csv.DictWriter(handle, fieldnames=list(PRICE_COLUMNS))
        writer.writeheader()
        writer.writerow({
            "ticket_size": 2, "american_odds": "-120", "decimal_odds": "",
            "sportsbook": "EXAMPLE_BOOK", "captured_at": "2026-09-20T12:40:00-04:00",
            "source_reference": "screenshot", "notes": "EXAMPLE ROW - delete before use",
        })
        writer.writerow({
            "ticket_size": 3, "american_odds": "+140", "decimal_odds": "",
            "sportsbook": "EXAMPLE_BOOK", "captured_at": "2026-09-20T12:40:00-04:00",
            "source_reference": "screenshot", "notes": "EXAMPLE ROW - delete before use",
        })
    return path


def read_price_csv(
    path: Path | str,
    *,
    season: int,
    week: int,
    label: str = "",
    notes: str = "",
) -> TeaserPriceSnapshot:
    """Read and validate an actual teaser menu into one immutable price snapshot."""
    path = Path(path)
    with path.open(newline="") as handle:
        lines = [line for line in handle if not line.lstrip().startswith("#")]
    reader = csv.DictReader(lines)

    quotes, problems = [], []
    for number, row in enumerate(reader, start=2):
        if not any((value or "").strip() for value in row.values()):
            continue
        if (row.get("notes") or "").strip().upper().startswith("EXAMPLE ROW"):
            continue
        try:
            american = (row.get("american_odds") or "").strip()
            decimal_odds = (row.get("decimal_odds") or "").strip()
            if american and decimal_odds:
                raise MarketValidationError(
                    "supply american_odds OR decimal_odds, not both"
                )
            quotes.append(
                TeaserPriceQuote(
                    ticket_size=int(row["ticket_size"]),
                    sportsbook=(row.get("sportsbook") or "").strip(),
                    captured_at=require_aware(
                        row["captured_at"], field=f"row {number} captured_at"
                    ),
                    american_odds=american or None,
                    decimal_odds=decimal_odds or None,
                    source_reference=(row.get("source_reference") or "").strip(),
                    notes=(row.get("notes") or "").strip(),
                )
            )
        except (KeyError, ValueError, TypeError, MarketValidationError) as exc:
            problems.append(f"  row {number}: {exc}")

    if problems:
        raise MarketValidationError(
            f"{len(problems)} price row(s) in {path.name} could not be accepted:\n"
            + "\n".join(problems)
        )
    if not quotes:
        raise MarketValidationError(
            f"{path.name} contains no usable price rows. Without a real price no ticket "
            "can be placement-eligible."
        )

    books = {quote.sportsbook for quote in quotes}
    return TeaserPriceSnapshot(
        season=season,
        week=week,
        captured_at=max(quote.captured_at for quote in quotes),
        sportsbook=books.pop() if len(books) == 1 else "MIXED",
        quotes=tuple(quotes),
        label=label,
        notes=notes,
    )


def price_from_american(
    *,
    ticket_size: int,
    american_odds,
    sportsbook: str,
    captured_at: datetime,
    source_reference: str = "",
    notes: str = "",
) -> TeaserPriceQuote:
    """Build one actual-price quote directly (used by the CLI and tests)."""
    return TeaserPriceQuote(
        ticket_size=ticket_size,
        sportsbook=sportsbook,
        captured_at=captured_at,
        american_odds=american_odds,
        source_reference=source_reference,
        notes=notes,
    )
