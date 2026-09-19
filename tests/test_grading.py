"""Historical outcome grading, sign conventions, and the no-PUSH invariant."""

from __future__ import annotations

import pytest

from teaser_model_v1.analysis.grading import (
    Outcome,
    PrimaryPushError,
    assert_no_primary_push,
    cover_margin,
    grade_leg,
    grade_teased_leg,
)
from teaser_model_v1.engine.constants import PRIMARY_SPREADS, TEASER_POINTS
from teaser_model_v1.engine.legs import build_leg


# ---------------------------------------------------------------------------------------
# Underdog sign convention: +1.5 -> +7.5 and +2.5 -> +8.5
# ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "margin,expected",
    [
        (14, Outcome.WIN),  # won outright
        (1, Outcome.WIN),
        (0, Outcome.WIN),  # a tie still covers +7.5
        (-1, Outcome.WIN),
        (-7, Outcome.WIN),  # lost by 7, teased line is +7.5 -> WIN
        (-8, Outcome.LOSS),  # lost by 8 -> LOSS
        (-21, Outcome.LOSS),
    ],
)
def test_underdog_plus_1_5_teased_to_plus_7_5(margin, expected):
    assert grade_teased_leg(margin, 7.5) is expected


@pytest.mark.parametrize(
    "margin,expected",
    [
        (-8, Outcome.WIN),  # lost by 8, teased line +8.5 -> WIN
        (-9, Outcome.LOSS),
    ],
)
def test_underdog_plus_2_5_teased_to_plus_8_5(margin, expected):
    assert grade_teased_leg(margin, 8.5) is expected


# ---------------------------------------------------------------------------------------
# Favorite sign convention: -7.5 -> -1.5 and -8.5 -> -2.5
# ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "margin,expected",
    [
        (21, Outcome.WIN),
        (2, Outcome.WIN),  # won by 2, must clear 1.5 -> WIN
        (1, Outcome.LOSS),  # won by 1, does not clear 1.5 -> LOSS
        (0, Outcome.LOSS),  # a tie loses a favorite leg
        (-3, Outcome.LOSS),
    ],
)
def test_favorite_minus_7_5_teased_to_minus_1_5(margin, expected):
    assert grade_teased_leg(margin, -1.5) is expected


@pytest.mark.parametrize(
    "margin,expected",
    [
        (3, Outcome.WIN),  # won by 3, clears 2.5
        (2, Outcome.LOSS),  # won by 2, does not clear 2.5
    ],
)
def test_favorite_minus_8_5_teased_to_minus_2_5(margin, expected):
    assert grade_teased_leg(margin, -2.5) is expected


def test_the_two_sides_of_a_game_are_graded_with_opposite_margins():
    # Home wins by 3. The home leg sees +3, the away leg sees -3.
    home = grade_teased_leg(3, -1.5)  # home was -7.5, teased to -1.5
    away = grade_teased_leg(-3, 7.5)  # away was +1.5, teased to +7.5
    assert home is Outcome.WIN
    assert away is Outcome.WIN  # both sides can win a 6-point teaser: that is the point


def test_grade_leg_uses_the_legs_own_teased_spread():
    leg = build_leg("g-A", "NFL", "A", 1.5, 44)
    assert float(leg.teased_spread) == 7.5
    assert grade_leg(leg, -7) is Outcome.WIN
    assert grade_leg(leg, -8) is Outcome.LOSS


def test_cover_margin_is_signed_distance_from_the_teased_line():
    assert float(cover_margin(-7, 7.5)) == pytest.approx(0.5)
    assert float(cover_margin(-8, 7.5)) == pytest.approx(-0.5)


def test_outcome_as_int_mapping():
    assert Outcome.WIN.as_int == 1
    assert Outcome.LOSS.as_int == 0
    assert Outcome.PUSH.as_int is None


# ---------------------------------------------------------------------------------------
# The no-PUSH invariant for live-primary geometry.
# ---------------------------------------------------------------------------------------


def test_primary_geometry_can_never_push_across_every_plausible_margin():
    """Exhaustive: all four shapes against every NFL margin from -60 to +60."""
    for spread in PRIMARY_SPREADS:
        teased = spread + TEASER_POINTS
        for margin in range(-60, 61):
            assert grade_teased_leg(margin, teased) is not Outcome.PUSH


def test_a_whole_number_secondary_shape_CAN_push():
    """Contrast case, to show the invariant is a property of the geometry, not the code.

    -8 teased to -2 pushes on a 2-point win. This is exactly why whole numbers are
    secondary.
    """
    assert grade_teased_leg(2, -2.0) is Outcome.PUSH


def test_assert_no_primary_push_passes_on_clean_records():
    records = [
        {"geometry_class": "PRIMARY", "outcome": "WIN"},
        {"geometry_class": "PRIMARY", "outcome": "LOSS"},
        {"geometry_class": "SECONDARY", "outcome": "PUSH"},  # allowed: not primary
    ]
    assert_no_primary_push(records) is None


def test_assert_no_primary_push_raises_and_names_the_offender():
    records = [
        {"geometry_class": "PRIMARY", "outcome": "WIN", "leg_id": "ok"},
        {
            "geometry_class": "PRIMARY",
            "outcome": "PUSH",
            "leg_id": "2024_01_AAA_BBB-AAA",
            "season": 2024,
            "week": 1,
            "team": "AAA",
            "archived_reference_line": 2.0,
            "teased_line": 8.0,
            "margin": -8,
        },
    ]
    with pytest.raises(PrimaryPushError) as excinfo:
        assert_no_primary_push(records)
    assert "2024_01_AAA_BBB-AAA" in str(excinfo.value)
    assert "1 primary leg(s) graded PUSH" in str(excinfo.value)
