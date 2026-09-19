"""Exact-decimal helpers.

Lines and totals are half-point quantities. Comparing them as binary floats invites
``2.5 != 2.5000000000000004`` style failures, and half-point fidelity is the single most
critical data property for this model. So every line/total comparison in the engine goes
through :func:`to_decimal`, which converts via ``str`` and is therefore exact for the
decimal values a sportsbook actually posts.

Probabilities and EV are ordinary floats: the spec asks for full internal precision in the
sense of "do not round before ranking", not for arbitrary-precision arithmetic.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from numbers import Real

_HALF = Decimal("0.5")


def to_decimal(value) -> Decimal:
    """Convert *value* to an exact :class:`~decimal.Decimal`.

    Floats are routed through ``repr`` so that ``2.5`` becomes ``Decimal('2.5')`` rather
    than the exact binary expansion.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):  # bool is an int subclass; never a line value
        raise TypeError("bool is not a valid line/total value")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float) or isinstance(value, Real):
        try:
            return Decimal(repr(float(value)))
        except (InvalidOperation, ValueError, OverflowError) as exc:
            raise ValueError(f"cannot convert {value!r} to Decimal") from exc
    if isinstance(value, str):
        try:
            return Decimal(value.strip())
        except InvalidOperation as exc:
            raise ValueError(f"cannot convert {value!r} to Decimal") from exc
    raise TypeError(f"cannot convert {type(value).__name__} to Decimal")


def is_half_point(value) -> bool:
    """True when *value* ends in .5 exactly."""
    d = to_decimal(value)
    return (abs(d) % Decimal(1)) == _HALF


def is_whole_number(value) -> bool:
    """True when *value* has no fractional part."""
    d = to_decimal(value)
    return (d % Decimal(1)) == Decimal(0)


def on_half_point_grid(value) -> bool:
    """True when *value* is an exact multiple of 0.5 (the sportsbook posting grid)."""
    d = to_decimal(value)
    return (d % _HALF) == Decimal(0)
