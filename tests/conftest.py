"""Shared fixtures/helpers for the v1.0 engine tests."""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest  # noqa: E402

from teaser_model_v1.engine.legs import Leg, build_leg  # noqa: E402
from teaser_model_v1.engine.tickets import Ticket  # noqa: E402


def make_leg(leg_id: str, spread, total, league: str = "NFL", **kwargs) -> Leg:
    """Build a Leg with minimal ceremony."""
    return build_leg(
        leg_id=leg_id,
        league=league,
        team=kwargs.pop("team", leg_id),
        spread=spread,
        game_total=total,
        **kwargs,
    )


def stub_leg(leg_id: str, p_est: float) -> Leg:
    """A Leg with a hand-set P_est, for testing ticket maths in isolation."""
    from decimal import Decimal

    return Leg(
        leg_id=leg_id,
        league="NFL",
        team=leg_id,
        spread=Decimal("1.5"),
        game_total=Decimal("40"),
        p_est=p_est,
    )


def stub_ticket(ev: float, n_legs: int, prefix: str = "t") -> Ticket:
    """A Ticket with a hand-set EV and leg count, for testing the tie rule."""
    legs = tuple(stub_leg(f"{prefix}{i}", 0.7) for i in range(n_legs))
    return Ticket(legs=legs, p_ticket=0.7**n_legs, profit=0.9, break_even=0.5, ev=ev)


@pytest.fixture
def leg_factory():
    return make_leg
