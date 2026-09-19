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


class Geometry(Enum):
    """**Dimension 1 of 2: geometry class.**

    A structural property of the line shape alone. The primary geometry is the same
    structure in both leagues:

        dog      +1.5 -> +7.5        favorite  -7.5 -> -1.5
        dog      +2.5 -> +8.5        favorite  -8.5 -> -2.5

    This says nothing about whether a leg may be bet. That is the *track*.
    """

    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"


class Track(Enum):
    """**Dimension 2 of 2: operational track.**

    LIVE is reserved for NFL primary geometry. Everything else is paper/research only:
    NFL secondary geometry, *all* college football (including CFB primary geometry), and
    the entirety of the 2026 season (see ``TEASER_MODEL_V1_0.md`` §1).

    This says nothing about the shape of the line. That is the *geometry class*.
    """

    LIVE = "LIVE"
    PAPER = "PAPER"


# Geometry and Track are deliberately plain Enums rather than str-Enums, and share no
# members. ``Geometry.PRIMARY == Track.LIVE`` is False and ``Geometry.PRIMARY == "PRIMARY"``
# is False, so the two dimensions cannot be conflated by accident or by a stray string
# comparison. CFB primary geometry is PRIMARY *and* PAPER, and must stay distinguishable
# from CFB secondary geometry for research.


# --------------------------------------------------------------------------------------
# Teaser mechanics
# --------------------------------------------------------------------------------------

#: The only teaser size in v1.0. Six points. Not four, not seven.
TEASER_POINTS = 6

# --------------------------------------------------------------------------------------
# Primary NFL geometry (half-point lines only)
# --------------------------------------------------------------------------------------

#: Pre-teaser spreads, from the perspective of the team being bet, that constitute the
#: primary geometry:
#:      +1.5 -> +7.5,  +2.5 -> +8.5,  -7.5 -> -1.5,  -8.5 -> -2.5
#:
#: This is a structural property of the line and is the SAME set in both leagues. It is
#: the operational *track*, not the geometry class, that restricts live play to the NFL.
#: Stored as Decimal so that membership testing never depends on binary float equality.
PRIMARY_SPREADS = frozenset(
    {Decimal("1.5"), Decimal("2.5"), Decimal("-7.5"), Decimal("-8.5")}
)

#: Deprecated alias retained so older references keep working. Prefer PRIMARY_SPREADS:
#: the set is not NFL-specific, only the LIVE track is.
PRIMARY_NFL_SPREADS = PRIMARY_SPREADS

#: Leagues whose primary geometry may be placed live. Everything else is paper.
LIVE_LEAGUES = frozenset({NFL})

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

#: FROZEN v1.0 KEY NUMBERS: exactly {3, 7}, in both leagues.
#:
#: This is fixed by the specification (TEASER_MODEL_V1_0.md §5). It is not a tunable
#: parameter and not an open question. All four primary geometries cross both of these,
#: which is the structural rationale for the primary geometry.
#:
#: 10 IS NOT A v1.0 KEY NUMBER. Whether college football warrants separate treatment of
#: 10 is a research question only (RESEARCH_QUEUE.md R-03) and must not be implemented.
KEY_NUMBERS = {
    NFL: (3, 7),
    CFB: (3, 7),
}

#: The frozen key-number set, league-independent, for direct assertion in tests.
KEY_NUMBERS_V1_0 = frozenset({3, 7})

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
