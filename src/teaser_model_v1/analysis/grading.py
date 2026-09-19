"""Grading a teaser leg against an actual final score.

A bet on a team at teased line ``L'`` wins when that team's signed margin satisfies
``margin + L' > 0``, pushes at ``== 0``, and loses at ``< 0``. The margin is signed from
the perspective of the team being bet.

**Invariant.** Every live-primary teased line is a half-point (+7.5, +8.5, -1.5, -2.5) and
every NFL final margin is an integer, so ``margin + L'`` can never be zero. A primary leg
can therefore never grade PUSH. :func:`assert_no_primary_push` enforces this, and a
violation means the data or the geometry classification is wrong — not that the rule needs
relaxing.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from teaser_model_v1.engine.constants import Geometry
from teaser_model_v1.engine.numeric import to_decimal


class Outcome(Enum):
    """Graded result of a single teased leg."""

    WIN = "WIN"
    LOSS = "LOSS"
    PUSH = "PUSH"

    @property
    def as_int(self) -> int | None:
        """1 for WIN, 0 for LOSS, ``None`` for PUSH (excluded from scoring)."""
        return {Outcome.WIN: 1, Outcome.LOSS: 0, Outcome.PUSH: None}[self]


class PrimaryPushError(AssertionError):
    """Raised when a primary-geometry leg grades PUSH, which must be impossible."""


def grade_teased_leg(margin, teased_spread) -> Outcome:
    """Grade one teased leg from the signed margin of the team being bet.

    ``margin`` is (this team's score - opponent's score). ``teased_spread`` is the line
    *after* the 6-point teaser, from the same team's perspective.

    Examples:
        A +1.5 dog teased to +7.5 losing by 7 -> -7 + 7.5 = +0.5 -> WIN.
        A -7.5 favorite teased to -1.5 winning by 1 -> 1 - 1.5 = -0.5 -> LOSS.
    """
    result = to_decimal(margin) + to_decimal(teased_spread)
    if result > 0:
        return Outcome.WIN
    if result < 0:
        return Outcome.LOSS
    return Outcome.PUSH


def grade_leg(leg, margin) -> Outcome:
    """Grade a :class:`~teaser_model_v1.engine.legs.Leg` against a signed margin."""
    return grade_teased_leg(margin, leg.teased_spread)


def cover_margin(margin, teased_spread) -> Decimal:
    """Signed distance by which the teased line was beaten. Positive means a win."""
    return to_decimal(margin) + to_decimal(teased_spread)


def assert_no_primary_push(records) -> None:
    """Enforce the no-PUSH invariant over graded records.

    *records* is an iterable of mappings carrying at least ``geometry_class`` and
    ``outcome``. Raises :class:`PrimaryPushError` naming every offending row, so the
    caller stops rather than quietly dropping or reclassifying it.
    """
    offenders = [
        record
        for record in records
        if str(record.get("geometry_class")) in (Geometry.PRIMARY.value, "PRIMARY")
        and str(record.get("outcome")) in (Outcome.PUSH.value, "PUSH")
    ]
    if offenders:
        lines = "\n".join(
            "  "
            + ", ".join(
                f"{key}={record.get(key)}"
                for key in (
                    "leg_id",
                    "season",
                    "week",
                    "team",
                    "archived_reference_line",
                    "teased_line",
                    "margin",
                )
            )
            for record in offenders
        )
        raise PrimaryPushError(
            f"{len(offenders)} primary leg(s) graded PUSH, which must be impossible "
            f"because every primary teased line is a half-point:\n{lines}"
        )
