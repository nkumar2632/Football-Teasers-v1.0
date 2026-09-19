"""Presentation helpers — rounding and the mandatory labels.

Rounding happens **only here**. Ranking, selection and EV comparison always use the
internally precise values.
"""

from __future__ import annotations

PROBABILITY_LABEL = "model-estimated hit probability"

HYPOTHETICAL_PRICE_NOTE = (
    "HYPOTHETICAL PRICE — not an observed teaser menu price. "
    "Shown for sensitivity analysis only."
)

NO_PRICE_NOTE = (
    "No teaser price available from the source. No EV is reported; "
    "a fair break-even price is reported instead."
)


def format_probability_pct(value: float) -> str:
    """Round a P_est or P_ticket to a whole percentage for display.

    Returns e.g. ``'69%'``. Always present this alongside
    :data:`PROBABILITY_LABEL` — never as an objective or true probability.
    """
    return f"{round(float(value) * 100)}%"


def labelled_probability(value: float) -> str:
    """``'69% (model-estimated hit probability)'``."""
    return f"{format_probability_pct(value)} ({PROBABILITY_LABEL})"


def format_hypothetical_price_note(american_odds: float) -> str:
    """Label a hypothetical teaser price. Hypothetical prices must always be labelled."""
    sign = "+" if float(american_odds) > 0 else ""
    return f"{sign}{american_odds:g} [{HYPOTHETICAL_PRICE_NOTE}]"
