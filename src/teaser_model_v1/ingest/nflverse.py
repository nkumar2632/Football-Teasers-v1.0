"""Ingestion of NFL game/line data from nflverse/nfldata (Lee Sharpe's ``games.csv``).

Source: https://github.com/nflverse/nfldata -> ``data/games.csv``
Documentation: ``DATASETS.md`` in that repository.

What the source documents about its line fields, verbatim:

    ``spread_line``: The spread line for the game. A positive number means the home team
    was favored by that many points, a negative number means the away team was favored by
    that many points. This lines up with the ``result`` column.

    ``total_line``: The total line for the game.

That is the *whole* documentation. It says nothing about when the line was captured. It
does not say "closing". Therefore these fields are labelled
:data:`~teaser_model_v1.ingest.provenance.ARCHIVED_REFERENCE_LINE` and **must not** be
described as a close, a true close, or a timestamped close anywhere in this project.

Original source columns are preserved on the way through; the derived columns this module
adds are all prefixed or explicitly named so they can never be mistaken for source data.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from teaser_model_v1.ingest.provenance import ARCHIVED_REFERENCE_LINE

SOURCE_NAME = "nflverse/nfldata games.csv (Lee Sharpe)"
SOURCE_URL = "https://github.com/nflverse/nfldata/blob/master/data/games.csv"
SOURCE_RAW_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"

#: The line fields we consume, and what the source documentation actually claims.
LINE_FIELD_DOCS = {
    "spread_line": (
        "The spread line for the game. A positive number means the home team was "
        "favored by that many points, a negative number means the away team was "
        "favored by that many points. No capture time is documented."
    ),
    "total_line": "The total line for the game. No capture time is documented.",
}

LINE_PROVENANCE = ARCHIVED_REFERENCE_LINE
LINE_PROVENANCE_JUSTIFICATION = (
    "nfldata DATASETS.md documents spread_line/total_line only as 'the spread line for "
    "the game' / 'the total line for the game'. It makes no claim about capture time, so "
    "the fields cannot be called a close of any kind. Commit-history inspection "
    "(reports/nfl_line_composition_investigation.md §2.4) confirms this: the row is "
    "refreshed every few hours through game week and freezes at whatever the last refresh "
    "captured when the final score lands. The lag to kickoff is irregular and "
    "undocumented, and feed dropouts leaving both fields briefly blank were observed."
)

REQUIRED_COLUMNS = (
    "game_id",
    "season",
    "game_type",
    "week",
    "gameday",
    "away_team",
    "home_team",
    "away_score",
    "home_score",
    "result",
    "total",
    "spread_line",
    "total_line",
)


def load_games(path: str | Path) -> pd.DataFrame:
    """Load the raw ``games.csv`` with original columns preserved and dtypes untouched.

    Lines and totals are read as strings first, then converted with
    :func:`pandas.to_numeric`, so that a source which had already rounded a value cannot
    be masked by dtype coercion — what was in the file is what lands in the frame.
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=True)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"games.csv is missing required columns: {missing}")

    numeric = (
        "season",
        "week",
        "away_score",
        "home_score",
        "result",
        "total",
        "spread_line",
        "total_line",
    )
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def filter_seasons(df: pd.DataFrame, seasons) -> pd.DataFrame:
    """Restrict to the requested seasons, keeping every original column."""
    return df[df["season"].isin(list(seasons))].copy()


def played_games(df: pd.DataFrame) -> pd.DataFrame:
    """Games with a final score. Scheduled-but-unplayed rows are excluded, not imputed."""
    return df[df["home_score"].notna() & df["away_score"].notna()].copy()


def to_legs(df: pd.DataFrame, league: str = "NFL") -> pd.DataFrame:
    """Explode one game row into two teaser-leg rows, one per side.

    The source stores ``spread_line`` from the home team's point of view as
    "home favoured by N". A teaser leg needs the line **from the perspective of the team
    being bet**, so:

        home leg spread = -spread_line
        away leg spread = +spread_line

    The resulting frame carries ``source_spread_line`` unchanged alongside the derived
    ``spread`` so the transformation stays auditable.

    Outcome fields are computed here only to support later calibration work; no model
    parameter may ever be fitted to them.
    """
    frames = []
    for side in ("home", "away"):
        part = df.copy()
        part["side"] = side
        part["team"] = part[f"{side}_team"]
        part["opponent"] = part["away_team"] if side == "home" else part["home_team"]
        sign = -1.0 if side == "home" else 1.0
        part["spread"] = sign * part["spread_line"]
        # Signed final margin from this team's perspective.
        part["margin"] = (
            part["home_score"] - part["away_score"]
            if side == "home"
            else part["away_score"] - part["home_score"]
        )
        frames.append(part)

    legs = pd.concat(frames, ignore_index=True)
    legs["league"] = league
    legs["leg_id"] = legs["game_id"].astype(str) + "-" + legs["team"].astype(str)
    legs["source_spread_line"] = legs["spread_line"]
    legs["game_total_line"] = legs["total_line"]
    legs["line_provenance"] = LINE_PROVENANCE

    return legs.sort_values(["season", "week", "game_id", "side"]).reset_index(drop=True)
