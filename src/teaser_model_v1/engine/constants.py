"""Frozen constants for Teaser Model v1.0.

DO NOT TUNE ANY VALUE IN THIS FILE.

Every constant here is transcribed from ``TEASER_MODEL_V1_0.md``. Changing one is a
model change, not a code change, and is forbidden for the whole of the 2026 season
(see ``AGENTS.md``). Proposed changes go in ``RESEARCH_QUEUE.md``.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

MODEL_VERSION = "v1.0"

# --------------------------------------------------------------------------------------
# Leagues
# --------------------------------------------------------------------------------------

NFL = "NFL"
CFB = "CFB"
LEAGUES = (NFL, CFB)


class Track(str, Enum):
    """Which track a leg belongs to.

    LIVE is reserved for NFL primary geometry. Everything else is paper/research only,
    including the entirety of the 2026 season (see ``TEASER_MODEL_V1_0.md`` §1).
    """

    LIVE = "LIVE"
    PAPER = "PAPER"


class Geometry(str, Enum):
    """Geometry classification of a single teaser leg."""

    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"


# --------------------------------------------------------------------------------------
# Teaser mechanics
# --------------------------------------------------------------------------------------

#: The only teaser size in v1.0. Six points. Not four, not seven.
TEASER_POINTS = 6

# --------------------------------------------------------------------------------------
# Primary NFL geometry (half-point lines only)
# --------------------------------------------------------------------------------------

#: Pre-teaser spreads, from the perspective of the team being bet, that constitute the
#: primary NFL geometry:
#:      +1.5 -> +7.5,  +2.5 -> +8.5,  -7.5 -> -1.5,  -8.5 -> -2.5
#: Stored as Decimal so that membership testing never depends on binary float equality.
PRIMARY_NFL_SPREADS = frozenset(
    {Decimal("1.5"), Decimal("2.5"), Decimal("-7.5"), Decimal("-8.5")}
)

# --------------------------------------------------------------------------------------
# Total guardrails (inclusive)
# --------------------------------------------------------------------------------------

TOTAL_GUARDRAIL = {
    NFL: Decimal("47"),
    CFB: Decimal("52"),
}

# --------------------------------------------------------------------------------------
# Probability model
# --------------------------------------------------------------------------------------

#: sigma = 0.30 * game_total
SIGMA_TOTAL_COEFFICIENT = Decimal("0.30")

#: Key numbers used by the key-number bump. The written specification states the bump
#: sizes but does not enumerate the key numbers; see AMBIGUITIES.md A-1. All four primary
#: NFL geometries cross both of these, which is the stated rationale for the geometry.
KEY_NUMBERS = {
    NFL: (3, 7),
    CFB: (3, 7),
}

#: Provisional key-number bump, by league. PROVISIONAL DOES NOT MEAN EDITABLE.
#: No proposed CFB bump correction is hard-coded here; these are the specified values.
BUMP_BOTH = {NFL: 0.07, CFB: 0.04}
BUMP_ONE = {NFL: 0.04, CFB: 0.02}
BUMP_NONE = {NFL: 0.00, CFB: 0.00}

# --------------------------------------------------------------------------------------
# Weekly construction
# --------------------------------------------------------------------------------------

#: Retain the top four eligible primary legs, ranked by P_est.
TOP_N_LEGS = 4

#: Display all 2-team and 3-team combinations from those top four.
TICKET_SIZES = (2, 3)

#: If fewer than two legs qualify, no primary ticket can be constructed.
MIN_LEGS_FOR_ANY_TICKET = 2

# --------------------------------------------------------------------------------------
# Exposure rule
# --------------------------------------------------------------------------------------

UNITS_PER_TICKET = 1
MAX_UNITS_PER_LEG_PER_WEEK = 2
