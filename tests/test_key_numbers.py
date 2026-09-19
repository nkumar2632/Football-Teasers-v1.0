"""Frozen v1.0 key numbers: exactly {3, 7}.

This is an implementation clarification of the frozen specification, not a parameter
change. 10 is NOT a v1.0 key number in either league — whether college football warrants
separate treatment of 10 is a research question (RESEARCH_QUEUE.md R-03) and must not be
implemented.
"""

from __future__ import annotations

import pytest

from teaser_model_v1.engine.constants import CFB, KEY_NUMBERS, KEY_NUMBERS_V1_0, NFL
from teaser_model_v1.engine.probability import (
    bump_for_leg,
    key_number_bump,
    key_numbers_crossed,
)


def test_key_numbers_are_exactly_three_and_seven():
    assert KEY_NUMBERS_V1_0 == {3, 7}
    assert set(KEY_NUMBERS[NFL]) == {3, 7}
    assert set(KEY_NUMBERS[CFB]) == {3, 7}


def test_key_numbers_are_identical_in_both_leagues():
    assert set(KEY_NUMBERS[NFL]) == set(KEY_NUMBERS[CFB])


@pytest.mark.parametrize("league", [NFL, CFB])
def test_ten_is_not_a_v1_0_key_number(league):
    assert 10 not in KEY_NUMBERS[league]
    assert 10 not in KEY_NUMBERS_V1_0

    # A shape that would cross 10 but neither 3 nor 7 must score zero crossings, and
    # therefore receive no bump at all.
    #   +7.5 -> +13.5 newly covers margins in (-13.5, -7.5]: contains -10, not -7 or -3.
    assert key_numbers_crossed(7.5, league) == 0
    assert bump_for_leg(league, 7.5) == pytest.approx(0.0)


@pytest.mark.parametrize("league", [NFL, CFB])
def test_no_extra_key_numbers_are_smuggled_in(league):
    assert len(KEY_NUMBERS[league]) == 2


# ---------------------------------------------------------------------------------------
# Crossing counts mandated by the Phase 1.5 correction.
# ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("league", [NFL, CFB])
def test_plus_2_5_to_plus_8_5_crosses_both(league):
    # Newly covered margins: (-8.5, -2.5] -> -8..-3, containing both -3 and -7.
    assert key_numbers_crossed(2.5, league) == 2


@pytest.mark.parametrize("league", [NFL, CFB])
def test_minus_8_5_to_minus_2_5_crosses_both(league):
    # Newly covered margins: (2.5, 8.5] -> 3..8, containing both 3 and 7.
    assert key_numbers_crossed(-8.5, league) == 2


@pytest.mark.parametrize("league", [NFL, CFB])
def test_plus_4_5_to_plus_10_5_crosses_seven_but_not_three(league):
    """+4.5 -> +10.5 is a ONE-key-number shape under frozen v1.0.

    Newly covered margins: (-10.5, -4.5] -> -10..-5. That contains -7 but not -3.
    It also contains -10, which is *not* a v1.0 key number and earns nothing.
    """
    assert key_numbers_crossed(4.5, league) == 1

    expected = {NFL: 0.04, CFB: 0.02}[league]
    assert key_number_bump(league, 1) == pytest.approx(expected)
    assert bump_for_leg(league, 4.5) == pytest.approx(expected)


@pytest.mark.parametrize("league", [NFL, CFB])
def test_all_four_primary_shapes_cross_both_in_both_leagues(league):
    for spread in (1.5, 2.5, -7.5, -8.5):
        assert key_numbers_crossed(spread, league) == 2


@pytest.mark.parametrize(
    "spread,expected",
    [
        (1.5, 2),  # (-7.5, -1.5] -> -7..-2 : both
        (2.5, 2),  # (-8.5, -2.5] -> -8..-3 : both
        (-7.5, 2),  # (1.5, 7.5]  -> 2..7   : both
        (-8.5, 2),  # (2.5, 8.5]  -> 3..8   : both
        (4.5, 1),  # (-10.5, -4.5] -> -10..-5 : 7 only
        (-4.5, 1),  # (-1.5, 4.5] -> -1..4    : 3 only
        (-2.0, 1),  # (-4, 2]     -> -3..2    : 3 only
        (0.5, 1),  # (-6.5, -0.5] -> -6..-1   : 3 only
        (7.5, 0),  # (-13.5, -7.5] -> -13..-8 : neither
        (10.0, 0),  # (-16, -10]  -> -15..-10 : neither
    ],
)
def test_crossing_counts_on_a_range_of_shapes(spread, expected):
    assert key_numbers_crossed(spread, NFL) == expected
