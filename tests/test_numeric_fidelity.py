"""Half-point fidelity is critical; these tests guard the arithmetic that protects it."""

from __future__ import annotations

from decimal import Decimal

import pytest

from teaser_model_v1.engine.geometry import (
    is_primary_geometry,
    passes_total_guardrail,
    teased_spread,
)
from teaser_model_v1.engine.numeric import (
    is_half_point,
    is_whole_number,
    on_half_point_grid,
    to_decimal,
)


@pytest.mark.parametrize("value", [1.5, "1.5", Decimal("1.5")])
def test_primary_membership_is_type_agnostic(value):
    assert is_primary_geometry("NFL", value)
    assert is_primary_geometry("CFB", value)


def test_float_spreads_do_not_drift():
    assert to_decimal(2.5) == Decimal("2.5")
    assert to_decimal(-8.5) == Decimal("-8.5")
    assert to_decimal(47.5) == Decimal("47.5")
    # Binary floats are not exact decimals: Decimal(float) exposes the full expansion,
    # while to_decimal() goes through repr and lands on the value a sportsbook posted.
    assert Decimal(0.1) != Decimal("0.1")
    assert to_decimal(0.1) == Decimal("0.1")
    # And float arithmetic really does drift off the half-point grid.
    assert (2.5 - 0.1 - 0.1 - 0.1) != 2.2
    assert to_decimal(2.5 - 0.1 - 0.1 - 0.1) != Decimal("2.2")


def test_teased_spread_is_exact():
    assert teased_spread(1.5) == Decimal("7.5")
    assert teased_spread(2.5) == Decimal("8.5")
    assert teased_spread(-7.5) == Decimal("-1.5")
    assert teased_spread(-8.5) == Decimal("-2.5")


def test_guardrail_boundary_is_exact_and_inclusive():
    assert passes_total_guardrail("NFL", Decimal("47"))
    assert passes_total_guardrail("NFL", 46.5)
    assert not passes_total_guardrail("NFL", Decimal("47.5"))
    assert passes_total_guardrail("CFB", Decimal("52"))
    assert not passes_total_guardrail("CFB", Decimal("52.5"))


def test_half_point_helpers():
    assert is_half_point(2.5) and is_half_point(-8.5)
    assert not is_half_point(3)
    assert is_whole_number(-8) and not is_whole_number(-8.5)
    assert on_half_point_grid(2.5) and on_half_point_grid(3)
    assert not on_half_point_grid(2.25)


def test_bool_is_rejected_as_a_line_value():
    with pytest.raises(TypeError):
        to_decimal(True)
