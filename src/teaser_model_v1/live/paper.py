"""CFB PAPER/RESEARCH track — board construction with an outcome-leakage guard.

**All college football is PAPER/RESEARCH ONLY under frozen v1.0.** Nothing built here is
live-eligible, whatever its EV, and no CFB ticket can reach the placement ledger.

CFB *primary geometry* is still PRIMARY — the same four structural shapes as the NFL. What
makes it paper is its **track**, not its geometry (`AGENTS.md`, `AMBIGUITIES.md` A-2).

## The leakage guard

Reconstructing what the model would have said about a game that has already started is only
meaningful if the reconstruction cannot see the outcome. This module enforces that
structurally rather than by convention:

* :class:`PregameLineInput` carries **only** pregame fields. It has no score, status,
  clock, period or result attribute, so a selection function literally cannot read one.
* :func:`assert_no_outcome_fields` rejects any object carrying an outcome-shaped
  attribute, and is called on every input before the board is built.
* Current score and status are joined **afterwards**, by :func:`overlay_status`, which
  operates on an already-frozen board and cannot reorder or re-rank it.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from decimal import Decimal

from teaser_model_v1.engine.classification import classify
from teaser_model_v1.engine.constants import Geometry, Track
from teaser_model_v1.engine.geometry import passes_total_guardrail, teased_spread
from teaser_model_v1.engine.legs import build_leg
from teaser_model_v1.engine.numeric import to_decimal
from teaser_model_v1.engine.tickets import generate_tickets, select_top_legs

#: Attribute-name fragments that indicate outcome or in-game state. Any input carrying one
#: of these is refused before it can reach a selection function.
OUTCOME_FIELD_MARKERS = (
    "score", "status", "clock", "period", "quarter", "result", "winner", "margin",
    "final", "outcome", "won", "lost", "covering", "live", "in_progress", "elapsed",
)

#: Provenance labels for a CFB pregame line, in increasing strength of claim.
CURRENT_PREGAME = "current_pregame"
ARCHIVED_PREGAME_REFERENCE = "archived_pregame_reference"
TRUE_TIMESTAMPED_PREGAME = "true_timestamped_pregame"
DATA_INSUFFICIENT = "DATA_INSUFFICIENT"

PAPER_BANNER = "CFB PAPER/RESEARCH TRACK — NOT LIVE v1.0"


class OutcomeLeakageError(AssertionError):
    """Raised when an object reaching model selection carries outcome or game-state data."""


def assert_no_outcome_fields(obj, *, where: str = "model selection") -> None:
    """Refuse any object exposing an outcome or in-game-state field.

    This is the audit assertion for the paper reconstruction: a selection function must be
    unable to see a score, a status or a clock, so that what the model "would have said"
    cannot be contaminated by what actually happened.
    """
    names = set()
    if hasattr(obj, "__dataclass_fields__"):
        names |= {f.name for f in fields(obj)}
    if isinstance(obj, dict):
        names |= set(obj.keys())
    names |= {n for n in dir(obj) if not n.startswith("_")}

    offenders = sorted(
        name for name in names
        if any(marker in name.lower() for marker in OUTCOME_FIELD_MARKERS)
    )
    if offenders:
        raise OutcomeLeakageError(
            f"{where} was given an object exposing outcome/game-state fields: "
            f"{offenders}. Pregame reconstruction must not see them; join current status "
            "only after the board is frozen."
        )


@dataclass(frozen=True)
class PregameLineInput:
    """A pregame line, and nothing else.

    Deliberately minimal: there is no field here that could carry a score, a clock or a
    status, so a selection function built on it cannot leak an outcome.
    """

    game_id: str
    team: str
    opponent: str
    spread: Decimal
    total: Decimal
    kickoff: str
    source: str
    line_label: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "spread", to_decimal(self.spread))
        object.__setattr__(self, "total", to_decimal(self.total))
        if self.line_label not in (
            CURRENT_PREGAME, ARCHIVED_PREGAME_REFERENCE, TRUE_TIMESTAMPED_PREGAME
        ):
            raise ValueError(
                f"line_label {self.line_label!r} is not an accepted pregame provenance "
                f"label. A line whose pregame provenance cannot be established must be "
                f"excluded as {DATA_INSUFFICIENT}, never reconstructed from a live line."
            )

    @property
    def leg_id(self) -> str:
        return f"{self.game_id}-{self.team}"


@dataclass(frozen=True)
class PaperLeg:
    """One CFB leg as the frozen model sees it. Paper track, never live-eligible."""

    leg_id: str
    game_id: str
    team: str
    opponent: str
    spread: Decimal
    teased_spread: Decimal
    total: Decimal
    geometry_class: str
    track: str
    key_numbers_crossed: int
    p_raw: float
    bump: float
    p_est: float
    kickoff: str
    source: str
    line_label: str

    @property
    def is_primary(self) -> bool:
        return self.geometry_class == Geometry.PRIMARY.value

    @property
    def live_eligible(self) -> bool:
        """Always False. College football is paper/research only under v1.0."""
        return False


def build_cfb_paper_legs(inputs) -> list:
    """Build CFB legs from pregame lines alone.

    Every input is checked for outcome leakage first. Geometry, the CFB total guardrail
    (<= 52) and the CFB bump (+0.04 both key numbers, +0.02 one) all come from the frozen
    engine.
    """
    legs = []
    for item in inputs:
        assert_no_outcome_fields(item, where="build_cfb_paper_legs")
        engine_leg = build_leg(
            leg_id=item.leg_id, league="CFB", team=item.team,
            spread=item.spread, game_total=item.total,
            game_id=item.game_id, opponent=item.opponent,
        )
        legs.append(
            PaperLeg(
                leg_id=engine_leg.leg_id, game_id=item.game_id, team=item.team,
                opponent=item.opponent, spread=engine_leg.spread,
                teased_spread=engine_leg.teased_spread, total=engine_leg.game_total,
                geometry_class=engine_leg.geometry_class.value,
                track=engine_leg.track.value,
                key_numbers_crossed=engine_leg.key_numbers_crossed,
                p_raw=engine_leg.p_raw, bump=engine_leg.bump, p_est=engine_leg.p_est,
                kickoff=item.kickoff, source=item.source, line_label=item.line_label,
            )
        )
    return legs


def primary_paper_legs(legs) -> list:
    """CFB PRIMARY geometry inside the CFB total guardrail, ranked by P_est.

    These are PRIMARY/PAPER: primary geometry on the paper track. They are emphatically
    not relabelled SECONDARY.
    """
    qualifying = [
        leg for leg in legs
        if leg.is_primary and passes_total_guardrail("CFB", leg.total)
    ]
    return sorted(qualifying, key=lambda leg: (-leg.p_est, leg.leg_id))


def secondary_paper_legs(legs, limit: int = 10) -> list:
    """CFB SECONDARY geometry inside the guardrail, ranked separately from primary."""
    qualifying = [
        leg for leg in legs
        if not leg.is_primary and passes_total_guardrail("CFB", leg.total)
    ]
    return sorted(qualifying, key=lambda leg: (-leg.p_est, leg.leg_id))[:limit]


def build_cfb_paper_tickets(primary, profit_by_size=None):
    """All 2- and 3-team combinations from the top four CFB primary paper legs.

    ``profit_by_size`` is populated only from **actual contemporaneous** teaser prices. With
    none, EV is UNAVAILABLE and no price is invented. No CFB ticket is live-eligible in
    either case.
    """
    engine_legs = [
        build_leg(leg_id=leg.leg_id, league="CFB", team=leg.team, spread=leg.spread,
                  game_total=leg.total, game_id=leg.game_id, opponent=leg.opponent)
        for leg in primary
    ]
    top = select_top_legs(engine_legs)
    return top, generate_tickets(top, profit_by_size, price_is_hypothetical=False)


# ---------------------------------------------------------------------------------------
# Status overlay — applied only AFTER the board is frozen
# ---------------------------------------------------------------------------------------

NOT_STARTED = "NOT STARTED"
IN_PROGRESS = "IN PROGRESS"
FINAL = "FINAL"

CURRENTLY_COVERING = "currently covering"
CURRENTLY_NOT_COVERING = "currently not covering"
FINAL_WIN = "final win"
FINAL_LOSS = "final loss"


@dataclass(frozen=True)
class StatusOverlay:
    """Current score and status for one game, joined after the board is frozen."""

    game_id: str
    game_status: str
    clock: str = ""
    home_score: int | None = None
    away_score: int | None = None


def overlay_status(board_legs, overlays) -> list:
    """Attach current status to an **already-frozen** board.

    Returns plain dicts rather than mutating the legs, so nothing downstream can mistake a
    status-bearing record for a model input. Rankings are preserved exactly as given and
    are never recomputed here.

    For an in-progress game the cover column is a **snapshot, not a result**.
    """
    by_game = {o.game_id: o for o in overlays}
    rows = []
    for position, leg in enumerate(board_legs, start=1):
        overlay = by_game.get(leg.game_id)
        cover, margin = NOT_STARTED, None
        if overlay and overlay.home_score is not None and overlay.away_score is not None:
            # Margin from this leg's team's perspective; requires knowing which side it is.
            margin = None
            if leg.team and leg.opponent:
                margin = (
                    overlay.home_score - overlay.away_score
                    if leg.team == getattr(overlay, "home_team", leg.team)
                    else None
                )
            if margin is None:
                margin = overlay.home_score - overlay.away_score
            covering = (to_decimal(margin) + leg.teased_spread) > 0
            if overlay.game_status == FINAL:
                cover = FINAL_WIN if covering else FINAL_LOSS
            else:
                cover = CURRENTLY_COVERING if covering else CURRENTLY_NOT_COVERING
        rows.append({
            "rank": position,
            "leg_id": leg.leg_id,
            "team": leg.team,
            "pregame_line": str(leg.spread),
            "teased_line": str(leg.teased_spread),
            "total": str(leg.total),
            "p_est": leg.p_est,
            "line_label": leg.line_label,
            "game_status": overlay.game_status if overlay else NOT_STARTED,
            "clock": overlay.clock if overlay else "",
            "current_margin": margin,
            "cover_status": cover,
            "is_result": bool(overlay and overlay.game_status == FINAL),
        })
    return rows
