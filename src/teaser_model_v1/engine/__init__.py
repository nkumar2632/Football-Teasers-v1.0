"""Frozen computation engine for Teaser Model v1.0.

Pure functions only. No I/O, no network, no pandas dependency in the core maths.
Every value here is specified by ``TEASER_MODEL_V1_0.md``.
"""

from teaser_model_v1.engine.constants import (
    BUMP_BOTH,
    BUMP_NONE,
    BUMP_ONE,
    CFB,
    KEY_NUMBERS,
    MAX_UNITS_PER_LEG_PER_WEEK,
    MIN_LEGS_FOR_ANY_TICKET,
    NFL,
    PRIMARY_NFL_SPREADS,
    SIGMA_TOTAL_COEFFICIENT,
    TEASER_POINTS,
    TICKET_SIZES,
    TOP_N_LEGS,
    TOTAL_GUARDRAIL,
    UNITS_PER_TICKET,
    Geometry,
    Track,
)
from teaser_model_v1.engine.geometry import (
    classify_geometry,
    is_primary,
    passes_total_guardrail,
    secondary_label,
    shape_matches_primary_geometry,
    teased_spread,
)
from teaser_model_v1.engine.leagues import normalize_league
from teaser_model_v1.engine.legs import Leg, build_leg, eligible_primary_nfl_legs
from teaser_model_v1.engine.presentation import (
    PROBABILITY_LABEL,
    format_hypothetical_price_note,
    format_probability_pct,
)
from teaser_model_v1.engine.pricing import (
    break_even_probability,
    ev_per_unit,
    profit_from_american_odds,
)
from teaser_model_v1.engine.probability import (
    key_numbers_crossed,
    key_number_bump,
    p_est,
    p_raw,
    sigma,
)
from teaser_model_v1.engine.tickets import (
    Ticket,
    generate_tickets,
    select_top_legs,
    select_live_tickets,
    ticket_probability,
)

__all__ = [
    "BUMP_BOTH",
    "BUMP_NONE",
    "BUMP_ONE",
    "CFB",
    "Geometry",
    "KEY_NUMBERS",
    "Leg",
    "MAX_UNITS_PER_LEG_PER_WEEK",
    "MIN_LEGS_FOR_ANY_TICKET",
    "NFL",
    "PROBABILITY_LABEL",
    "PRIMARY_NFL_SPREADS",
    "SIGMA_TOTAL_COEFFICIENT",
    "TEASER_POINTS",
    "TICKET_SIZES",
    "TOP_N_LEGS",
    "TOTAL_GUARDRAIL",
    "Ticket",
    "Track",
    "UNITS_PER_TICKET",
    "break_even_probability",
    "build_leg",
    "classify_geometry",
    "eligible_primary_nfl_legs",
    "ev_per_unit",
    "format_hypothetical_price_note",
    "format_probability_pct",
    "generate_tickets",
    "is_primary",
    "key_number_bump",
    "key_numbers_crossed",
    "normalize_league",
    "p_est",
    "p_raw",
    "passes_total_guardrail",
    "profit_from_american_odds",
    "secondary_label",
    "select_live_tickets",
    "select_top_legs",
    "shape_matches_primary_geometry",
    "sigma",
    "teased_spread",
    "ticket_probability",
]
