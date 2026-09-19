"""Price, break-even and EV.

Frozen. See ``TEASER_MODEL_V1_0.md`` §7.

    profit      = net profit per 1 unit staked
    break_even  = 1 / (1 + profit)
    EV_per_unit = P_ticket * profit - (1 - P_ticket)

Historical teaser menu prices may be unavailable. **Never invent one.** A ticket with no
price has no EV; it has a fair break-even price, which is a different object and is
labelled as such.
"""

from __future__ import annotations


def break_even_probability(profit: float) -> float:
    """break_even = 1 / (1 + profit), where *profit* is net profit per 1 unit staked.

    A -120 price pays 100/120 = 0.8333 per unit, so break_even = 0.5455.
    """
    profit = float(profit)
    if profit <= -1.0:
        raise ValueError(f"profit must exceed -1 unit, got {profit!r}")
    return 1.0 / (1.0 + profit)


def fair_break_even_profit(p_ticket: float) -> float:
    """The net profit per unit at which a ticket of probability *p_ticket* breaks even.

    This is the inverse of :func:`break_even_probability` and is the honest thing to
    report when no real teaser price exists: "this ticket needs +X to break even", rather
    than an EV computed against a price nobody offered.
    """
    p = float(p_ticket)
    if not 0.0 < p <= 1.0:
        raise ValueError(f"p_ticket must be in (0, 1], got {p_ticket!r}")
    return (1.0 - p) / p


def ev_per_unit(p_ticket: float, profit: float) -> float:
    """EV_per_unit = P_ticket * profit - (1 - P_ticket). Full internal precision."""
    p = float(p_ticket)
    return p * float(profit) - (1.0 - p)


def profit_from_american_odds(american_odds: float) -> float:
    """Convert an American price to net profit per 1 unit staked.

    ``-120`` -> ``0.8333...``; ``+160`` -> ``1.6``. This is a units conversion, not a
    model assumption: it converts a price that was actually observed (or an explicitly
    hypothetical one) into the ``profit`` term the spec uses.
    """
    odds = float(american_odds)
    if odds == 0:
        raise ValueError("American odds of 0 are not a price")
    if odds > 0:
        return odds / 100.0
    return 100.0 / abs(odds)


def american_odds_from_profit(profit: float) -> float:
    """Inverse of :func:`profit_from_american_odds`, for reporting fair prices."""
    p = float(profit)
    if p <= 0:
        raise ValueError(f"profit must be positive to express as American odds, got {p!r}")
    if p >= 1.0:
        return p * 100.0
    return -100.0 / p
