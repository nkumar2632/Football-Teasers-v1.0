"""League normalization.

Maps the many spellings a data source may use onto the two league codes v1.0 knows
about: ``NFL`` and ``CFB``. Unknown values raise rather than defaulting, because a
silent default would route a college game through NFL parameters.
"""

from __future__ import annotations

from teaser_model_v1.engine.constants import CFB, NFL

_NFL_ALIASES = frozenset(
    {
        "nfl",
        "national football league",
        "pro",
        "profootball",
        "pro football",
    }
)

_CFB_ALIASES = frozenset(
    {
        "cfb",
        "ncaa",
        "ncaaf",
        "ncaa football",
        "college",
        "college football",
        "cfp",
    }
)


class UnknownLeagueError(ValueError):
    """Raised when a league string cannot be normalized to NFL or CFB."""


def normalize_league(value: str) -> str:
    """Return ``NFL`` or ``CFB`` for *value*.

    Case- and whitespace-insensitive; underscores, hyphens and dots are treated as
    spaces. Raises :class:`UnknownLeagueError` for anything unrecognised — v1.0 covers
    exactly two leagues and guessing a third would be a silent model change.
    """
    if value is None:
        raise UnknownLeagueError("league is None")
    if not isinstance(value, str):
        raise UnknownLeagueError(f"league must be a string, got {type(value).__name__}")

    cleaned = value.strip().lower()
    for ch in ("_", "-", "."):
        cleaned = cleaned.replace(ch, " ")
    cleaned = " ".join(cleaned.split())

    if cleaned in _NFL_ALIASES:
        return NFL
    if cleaned in _CFB_ALIASES:
        return CFB
    raise UnknownLeagueError(f"unrecognised league: {value!r}")
