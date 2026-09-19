"""Historical backtest assembly: legs frame, weekly construction, ticket enumeration.

Uses the frozen engine for every model decision. This module only arranges data and counts
outcomes; it contains no model rule of its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import pandas as pd

from teaser_model_v1.analysis.calibration import (
    p_est_bucket,
    shape_label,
    side_class,
    total_bucket,
)
from teaser_model_v1.analysis.grading import Outcome, grade_leg
from teaser_model_v1.engine.constants import TICKET_SIZES, TOP_N_LEGS
from teaser_model_v1.engine.legs import build_leg, eligible_live_primary_legs
from teaser_model_v1.engine.tickets import select_top_legs, ticket_probability

LEG_COLUMNS = [
    "leg_id",
    "season",
    "week",
    "game_type",
    "gameday",
    "game_id",
    "league",
    "team",
    "opponent",
    "side",
    "archived_reference_line",
    "source_spread_line",
    "teased_line",
    "game_total",
    "geometry_class",
    "track",
    "shape",
    "side_class",
    "secondary_reason",
    "key_numbers_crossed",
    "p_raw",
    "bump",
    "p_est",
    "total_ok",
    "final_margin",
    "home_score",
    "away_score",
    "outcome",
    "won",
    "cover_margin",
    "total_bucket",
    "p_est_bucket",
    "line_provenance",
]


def build_leg_records(legs_frame: pd.DataFrame, league: str = "NFL") -> pd.DataFrame:
    """Turn the processed legs frame into fully classified, graded leg records.

    One row per (game, side). Every row preserves its source line, the frozen model's
    classification and probability components, the final margin, and the graded outcome.
    """
    records = []
    for row in legs_frame.itertuples(index=False):
        leg = build_leg(
            leg_id=row.leg_id,
            league=league,
            team=row.team,
            spread=row.spread,
            game_total=row.total_line,
            game_id=row.game_id,
            opponent=row.opponent,
            season=int(row.season),
            week=int(row.week),
            provenance=getattr(row, "line_provenance", None),
        )
        outcome = grade_leg(leg, row.margin)
        records.append(
            {
                "leg_id": leg.leg_id,
                "season": leg.season,
                "week": leg.week,
                "game_type": getattr(row, "game_type", None),
                "gameday": getattr(row, "gameday", None),
                "game_id": leg.game_id,
                "league": leg.league,
                "team": leg.team,
                "opponent": leg.opponent,
                "side": row.side,
                # Named for what it is. This is NOT a closing line.
                "archived_reference_line": float(leg.spread),
                "source_spread_line": float(row.source_spread_line),
                "teased_line": float(leg.teased_spread),
                "game_total": float(leg.game_total),
                "geometry_class": leg.geometry_class.value,
                "track": leg.track.value,
                "shape": shape_label(leg.spread),
                # Descriptive reporting label only; the frozen model treats all four
                # primary shapes identically.
                "side_class": side_class(leg.spread),
                "secondary_reason": leg.secondary_reason,
                "key_numbers_crossed": leg.key_numbers_crossed,
                "p_raw": leg.p_raw,
                "bump": leg.bump,
                "p_est": leg.p_est,
                "total_ok": leg.total_ok,
                "final_margin": int(row.margin),
                "home_score": int(row.home_score),
                "away_score": int(row.away_score),
                "outcome": outcome.value,
                "won": outcome.as_int,
                "cover_margin": float(row.margin) + float(leg.teased_spread),
                "total_bucket": total_bucket(leg.game_total),
                "p_est_bucket": p_est_bucket(leg.p_est),
                "line_provenance": getattr(row, "line_provenance", None),
            }
        )
    return pd.DataFrame(records, columns=LEG_COLUMNS)


def primary_before_guardrail(records: pd.DataFrame) -> pd.DataFrame:
    """Primary-geometry legs, before the total guardrail is applied."""
    return records[records["geometry_class"] == "PRIMARY"].copy()


def qualifying_primary(records: pd.DataFrame) -> pd.DataFrame:
    """Primary-geometry legs that also pass the league total guardrail."""
    frame = primary_before_guardrail(records)
    return frame[frame["total_ok"]].copy()


# ---------------------------------------------------------------------------------------
# Weekly construction
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class WeekBacktest:
    season: int
    week: int
    qualifying: pd.DataFrame
    top_legs: pd.DataFrame
    tickets: list


def season_weeks(games: pd.DataFrame, season: int) -> list[int]:
    """Every week that actually appears in the source for *season*, in order.

    Weeks are taken from the schedule, not from the qualifying legs, so that weeks with
    zero qualifying legs are counted rather than silently skipped.
    """
    return sorted(int(w) for w in games.loc[games["season"] == season, "week"].unique())


def week_top_legs(week_records: pd.DataFrame) -> pd.DataFrame:
    """Rank a week's qualifying legs by full-precision P_est and keep the frozen top four.

    Delegates to the engine so the ranking and tiebreak rules are the frozen ones.
    """
    legs = [
        build_leg(
            leg_id=row.leg_id,
            league=row.league,
            team=row.team,
            spread=row.archived_reference_line,
            game_total=row.game_total,
            game_id=row.game_id,
            season=int(row.season),
            week=int(row.week),
        )
        for row in week_records.itertuples(index=False)
    ]
    chosen = select_top_legs(eligible_live_primary_legs(legs), top_n=TOP_N_LEGS)
    chosen_ids = [leg.leg_id for leg in chosen]
    ordered = week_records.set_index("leg_id").loc[chosen_ids].reset_index()
    ordered["rank"] = range(1, len(ordered) + 1)
    return ordered


def enumerate_tickets(top_legs: pd.DataFrame, ticket_sizes=TICKET_SIZES) -> list[dict]:
    """All 2-team and 3-team combinations from a week's top legs, graded.

    No price is attached and no EV is computed: Phase 2 is calibration only.
    """
    tickets = []
    rows = list(top_legs.itertuples(index=False))
    for size in ticket_sizes:
        if size > len(rows):
            continue
        for combo in combinations(rows, size):
            predicted = ticket_probability(leg.p_est for leg in combo)
            won = all(leg.outcome == Outcome.WIN.value for leg in combo)
            game_ids = [leg.game_id for leg in combo]
            tickets.append(
                {
                    "season": int(combo[0].season),
                    "week": int(combo[0].week),
                    "n_legs": size,
                    "leg_ids": "|".join(leg.leg_id for leg in combo),
                    "teams": "|".join(str(leg.team) for leg in combo),
                    "shapes": "|".join(leg.shape for leg in combo),
                    "game_ids": "|".join(str(g) for g in game_ids),
                    "predicted_p_ticket": predicted,
                    "outcome": "WIN" if won else "LOSS",
                    "won": int(won),
                    "n_legs_winning": sum(
                        1 for leg in combo if leg.outcome == Outcome.WIN.value
                    ),
                    "same_game_legs": len(game_ids) != len(set(game_ids)),
                }
            )
    return tickets


def run_season(records: pd.DataFrame, games: pd.DataFrame, season: int) -> dict:
    """Run the frozen weekly construction across one season.

    Returns the qualifying legs, the per-week summary (including zero-qualifier weeks),
    the selected top-four legs and every constructible ticket.
    """
    qualifying = qualifying_primary(records)
    qualifying = qualifying[qualifying["season"] == season]

    weekly_rows = []
    all_top = []
    all_tickets = []

    for week in season_weeks(games, season):
        week_records = qualifying[qualifying["week"] == week]
        n = len(week_records)
        top = week_top_legs(week_records) if n else week_records.iloc[0:0].copy()
        tickets = enumerate_tickets(top) if len(top) >= 2 else []

        if len(top):
            all_top.append(top)
        all_tickets.extend(tickets)

        weekly_rows.append(
            {
                "season": season,
                "week": week,
                "n_qualifying_legs": n,
                "n_top_legs": len(top),
                "constructible": len(top) >= 2,
                "n_tickets_2team": sum(1 for t in tickets if t["n_legs"] == 2),
                "n_tickets_3team": sum(1 for t in tickets if t["n_legs"] == 3),
                "n_legs_winning": int(week_records["won"].sum()) if n else 0,
            }
        )

    top_frame = (
        pd.concat(all_top, ignore_index=True)
        if all_top
        else qualifying.iloc[0:0].assign(rank=pd.Series(dtype=int))
    )

    return {
        "season": season,
        "qualifying": qualifying,
        "weekly": pd.DataFrame(weekly_rows),
        "top_legs": top_frame,
        "tickets": pd.DataFrame(all_tickets),
    }
