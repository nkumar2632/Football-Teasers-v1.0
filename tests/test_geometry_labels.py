"""Secondary labelling and the league/geometry interaction."""

from __future__ import annotations

import pytest

from teaser_model_v1.engine.constants import Geometry, Track
from teaser_model_v1.engine.geometry import (
    classify_geometry,
    secondary_label,
    shape_matches_primary_geometry,
    track_for,
)


@pytest.mark.parametrize("spread", [1.5, 2.5, -7.5, -8.5])
def test_primary_shapes(spread):
    assert shape_matches_primary_geometry(spread)
    assert classify_geometry("NFL", spread) is Geometry.PRIMARY
    assert secondary_label("NFL", spread) is None
    assert track_for("NFL", spread) is Track.LIVE


@pytest.mark.parametrize("spread", [1.0, 2.0, 3.0, -8.0, -7.0, 3.5, -3.5, 6.5, -9.5, 0.5])
def test_non_primary_shapes(spread):
    assert not shape_matches_primary_geometry(spread)
    assert classify_geometry("NFL", spread) is Geometry.SECONDARY
    assert secondary_label("NFL", spread) is not None
    assert track_for("NFL", spread) is Track.PAPER


def test_whole_numbers_are_labelled_as_such():
    assert secondary_label("NFL", 2) == "whole_number_line"
    assert secondary_label("NFL", -8) == "whole_number_line"
    assert secondary_label("NFL", 3.5) == "other_half_point_shape"


def test_cfb_is_never_live_even_on_a_primary_shape():
    # All college football is paper/research only (spec §1).
    for spread in (1.5, 2.5, -7.5, -8.5):
        assert classify_geometry("CFB", spread) is Geometry.SECONDARY
        assert track_for("CFB", spread) is Track.PAPER
        assert secondary_label("CFB", spread) == "cfb_paper_track_primary_shape"
    assert secondary_label("CFB", 3.5) == "cfb_paper_track_other_shape"


def test_no_single_game_can_produce_two_primary_legs():
    """A derived fact worth pinning down: the primary set has no complementary pair.

    If one side of a game sits on a primary shape, the other side is its negation, and
    -1.5, -2.5, +7.5 and +8.5 are all outside the primary set. So a game contributes at
    most one primary leg, and no ticket can ever contain both sides of the same game.
    """
    from teaser_model_v1.engine.constants import PRIMARY_NFL_SPREADS

    for spread in PRIMARY_NFL_SPREADS:
        assert -spread not in PRIMARY_NFL_SPREADS
