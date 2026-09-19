"""League normalization."""

from __future__ import annotations

import pytest

from teaser_model_v1.engine.leagues import UnknownLeagueError, normalize_league


@pytest.mark.parametrize(
    "value",
    ["NFL", "nfl", " Nfl ", "National Football League", "pro football", "pro_football"],
)
def test_nfl_aliases(value):
    assert normalize_league(value) == "NFL"


@pytest.mark.parametrize(
    "value",
    ["CFB", "cfb", "NCAA", "ncaaf", "college", "College Football", "ncaa-football"],
)
def test_cfb_aliases(value):
    assert normalize_league(value) == "CFB"


@pytest.mark.parametrize("value", ["XFL", "", "footy", None, 7, "nba"])
def test_unknown_league_raises_rather_than_guessing(value):
    # Guessing would silently route a game through the wrong league's parameters.
    with pytest.raises(UnknownLeagueError):
        normalize_league(value)
