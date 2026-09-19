"""Geometry class and operational track: two independent dimensions.

These are the Phase 1.5 regression tests for the corrected CFB interpretation. Phase 1
wrongly collapsed the two dimensions and classified every CFB leg as SECONDARY. Primary
geometry is the same structure in both leagues; what differs is the track.
"""

from __future__ import annotations

import pytest

from teaser_model_v1.engine.classification import (
    LegClassification,
    classify,
    geometry_class_for,
    secondary_reason_for,
)
from teaser_model_v1.engine.constants import Geometry, Track
from teaser_model_v1.engine.geometry import (
    classify_geometry,
    is_live_track,
    is_primary_geometry,
    secondary_label,
    shape_matches_primary_geometry,
    track_for,
)
from teaser_model_v1.engine.legs import build_leg

PRIMARY_SHAPES = (1.5, 2.5, -7.5, -8.5)
SECONDARY_SHAPES = (1.0, 2.0, 3.0, -8.0, -7.0, 3.5, -3.5, 4.5, 6.5, -9.5, 0.5)


# ---------------------------------------------------------------------------------------
# The four-case matrix from the corrected specification reading.
# ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "league,spread,expected_geometry,expected_track",
    [
        # NFL +2.5 -> +8.5 : PRIMARY / LIVE
        ("NFL", 2.5, Geometry.PRIMARY, Track.LIVE),
        # CFB +2.5 -> +8.5 : PRIMARY / PAPER
        ("CFB", 2.5, Geometry.PRIMARY, Track.PAPER),
        # NFL +4.5 -> +10.5 : SECONDARY / PAPER
        ("NFL", 4.5, Geometry.SECONDARY, Track.PAPER),
        # CFB +4.5 -> +10.5 : SECONDARY / PAPER
        ("CFB", 4.5, Geometry.SECONDARY, Track.PAPER),
    ],
)
def test_classification_matrix(league, spread, expected_geometry, expected_track):
    result = classify(league, spread)
    assert result.geometry_class is expected_geometry
    assert result.track is expected_track
    assert classify_geometry(league, spread) is expected_geometry
    assert track_for(league, spread) is expected_track


def test_nfl_primary_is_live():
    leg = build_leg("n1", "NFL", "A", 2.5, 44)
    assert leg.geometry_class is Geometry.PRIMARY
    assert leg.track is Track.LIVE
    assert leg.classification_label() == "PRIMARY/LIVE"
    assert leg.qualifies_primary and leg.qualifies_live_primary


def test_cfb_primary_is_primary_geometry_on_the_paper_track():
    leg = build_leg("c1", "CFB", "A", 2.5, 50)
    assert leg.geometry_class is Geometry.PRIMARY
    assert leg.is_primary_geometry
    assert leg.secondary_reason is None
    assert leg.track is Track.PAPER
    assert not leg.is_live_track
    assert leg.classification_label() == "PRIMARY/PAPER"
    # Qualifies for research, never for live placement.
    assert leg.qualifies_primary
    assert not leg.qualifies_live_primary


def test_nfl_secondary_is_paper():
    leg = build_leg("n2", "NFL", "A", 4.5, 44)
    assert leg.geometry_class is Geometry.SECONDARY
    assert leg.track is Track.PAPER
    assert leg.classification_label() == "SECONDARY/PAPER"
    assert not leg.qualifies_primary and not leg.qualifies_live_primary


def test_cfb_secondary_is_paper():
    leg = build_leg("c2", "CFB", "A", 4.5, 50)
    assert leg.geometry_class is Geometry.SECONDARY
    assert leg.track is Track.PAPER
    assert leg.classification_label() == "SECONDARY/PAPER"
    assert not leg.qualifies_primary and not leg.qualifies_live_primary


def test_cfb_primary_stays_distinguishable_from_cfb_secondary():
    """The specific defect Phase 1 had: both collapsed to SECONDARY."""
    primary = build_leg("c1", "CFB", "A", 2.5, 50)
    secondary = build_leg("c2", "CFB", "B", 4.5, 50)

    assert primary.geometry_class is not secondary.geometry_class
    assert primary.classification_label() != secondary.classification_label()
    # ...while both remain on the same, paper, track.
    assert primary.track is secondary.track is Track.PAPER


# ---------------------------------------------------------------------------------------
# The dimensions must not be conflatable.
# ---------------------------------------------------------------------------------------


def test_geometry_and_track_are_distinct_types_that_never_compare_equal():
    assert Geometry.PRIMARY != Track.LIVE
    assert Geometry.SECONDARY != Track.PAPER
    # Nor are they bare strings that could be crossed with each other by accident.
    assert Geometry.PRIMARY != "PRIMARY"
    assert Track.LIVE != "LIVE"
    assert set(Geometry).isdisjoint(set(Track))


def test_classification_carries_both_dimensions_and_is_immutable():
    result = classify("CFB", 2.5)
    assert isinstance(result, LegClassification)
    with pytest.raises(Exception):
        result.track = Track.LIVE  # frozen dataclass


def test_geometry_class_is_league_independent():
    for spread in PRIMARY_SHAPES + SECONDARY_SHAPES:
        assert classify_geometry("NFL", spread) is classify_geometry("CFB", spread)
        assert geometry_class_for(spread) is classify_geometry("NFL", spread)


def test_only_nfl_primary_is_ever_live():
    for spread in PRIMARY_SHAPES:
        assert is_live_track("NFL", spread)
        assert not is_live_track("CFB", spread)
    for spread in SECONDARY_SHAPES:
        assert not is_live_track("NFL", spread)
        assert not is_live_track("CFB", spread)


# ---------------------------------------------------------------------------------------
# Shape-level facts.
# ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("spread", PRIMARY_SHAPES)
@pytest.mark.parametrize("league", ["NFL", "CFB"])
def test_primary_shapes(spread, league):
    assert shape_matches_primary_geometry(spread)
    assert is_primary_geometry(league, spread)
    assert secondary_label(league, spread) is None


@pytest.mark.parametrize("spread", SECONDARY_SHAPES)
@pytest.mark.parametrize("league", ["NFL", "CFB"])
def test_non_primary_shapes(spread, league):
    assert not shape_matches_primary_geometry(spread)
    assert not is_primary_geometry(league, spread)
    assert secondary_label(league, spread) is not None
    assert track_for(league, spread) is Track.PAPER


def test_secondary_reasons_describe_the_shape_not_the_league():
    for league in ("NFL", "CFB"):
        assert secondary_label(league, 2) == "whole_number_line"
        assert secondary_label(league, -8) == "whole_number_line"
        assert secondary_label(league, 3.5) == "other_half_point_shape"
        assert secondary_label(league, 4.5) == "other_half_point_shape"
    assert secondary_reason_for(2) == "whole_number_line"
    assert secondary_reason_for(2.5) is None


def test_no_single_game_can_produce_two_primary_legs():
    """A derived fact worth pinning down: the primary set has no complementary pair.

    If one side of a game sits on a primary shape, the other side is its negation, and
    -1.5, -2.5, +7.5 and +8.5 are all outside the primary set. So a game contributes at
    most one primary leg, and no ticket can ever contain both sides of the same game.
    """
    from teaser_model_v1.engine.constants import PRIMARY_SPREADS

    for spread in PRIMARY_SPREADS:
        assert -spread not in PRIMARY_SPREADS
