"""Phase 4: the live layer must not be able to change the frozen model.

Two guarantees:

* frozen constants are immutable containers and are not reassigned anywhere in `live/`
  or `cli/`;
* engine outputs are bit-identical to the values Phase 3 was built on.
"""

from __future__ import annotations

import ast
import math
from decimal import Decimal
from pathlib import Path

import pytest

from teaser_model_v1.engine import constants
from teaser_model_v1.engine.geometry import passes_total_guardrail, teased_spread
from teaser_model_v1.engine.legs import build_leg
from teaser_model_v1.engine.pricing import break_even_probability, ev_per_unit
from teaser_model_v1.engine.probability import key_numbers_crossed, p_est, p_raw, sigma
from teaser_model_v1.engine.tickets import ticket_probability

SRC = Path(__file__).resolve().parents[1] / "src" / "teaser_model_v1"
LIVE_DIRS = (SRC / "live", SRC / "cli")

#: Names in engine.constants that define the frozen model.
FROZEN_NAMES = (
    "TEASER_POINTS", "SIGMA_TOTAL_COEFFICIENT", "PRIMARY_SPREADS", "PRIMARY_NFL_SPREADS",
    "LIVE_LEAGUES", "TOTAL_GUARDRAIL", "KEY_NUMBERS", "KEY_NUMBERS_V1_0",
    "BUMP_BOTH", "BUMP_ONE", "BUMP_NONE", "TOP_N_LEGS", "TICKET_SIZES",
    "MIN_LEGS_FOR_ANY_TICKET", "UNITS_PER_TICKET", "MAX_UNITS_PER_LEG_PER_WEEK",
)


# ---- 30. no live module can mutate frozen constants -------------------------------------


def test_frozen_constants_hold_their_specified_values():
    assert constants.TEASER_POINTS == 6
    assert constants.SIGMA_TOTAL_COEFFICIENT == Decimal("0.30")
    assert constants.PRIMARY_SPREADS == frozenset(
        {Decimal("1.5"), Decimal("2.5"), Decimal("-7.5"), Decimal("-8.5")}
    )
    assert constants.TOTAL_GUARDRAIL["NFL"] == Decimal("47")
    assert constants.TOTAL_GUARDRAIL["CFB"] == Decimal("52")
    assert constants.KEY_NUMBERS_V1_0 == {3, 7}
    assert constants.BUMP_BOTH == {"NFL": 0.07, "CFB": 0.04}
    assert constants.BUMP_ONE == {"NFL": 0.04, "CFB": 0.02}
    assert constants.TOP_N_LEGS == 4
    assert constants.TICKET_SIZES == (2, 3)
    assert constants.MAX_UNITS_PER_LEG_PER_WEEK == 2
    assert constants.UNITS_PER_TICKET == 1


def test_the_primary_spread_set_cannot_be_mutated():
    with pytest.raises(AttributeError):
        constants.PRIMARY_SPREADS.add(Decimal("3.5"))
    with pytest.raises(AttributeError):
        constants.LIVE_LEAGUES.add("CFB")
    with pytest.raises((AttributeError, TypeError)):
        constants.TICKET_SIZES.append(4)


def _assigned_names(path: Path) -> set:
    tree = ast.parse(path.read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    names.add(target.attr)
                elif isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            target = node.target
            if isinstance(target, ast.Attribute):
                names.add(target.attr)
            elif isinstance(target, ast.Name):
                names.add(target.id)
    return names


@pytest.mark.parametrize("directory", LIVE_DIRS, ids=lambda p: p.name)
def test_no_live_module_assigns_a_frozen_constant(directory):
    offenders = []
    for path in sorted(directory.rglob("*.py")):
        for name in _assigned_names(path) & set(FROZEN_NAMES):
            offenders.append(f"{path.relative_to(SRC)} assigns {name}")
    assert not offenders, "live code must never rebind a frozen constant:\n" + "\n".join(offenders)


@pytest.mark.parametrize("directory", LIVE_DIRS, ids=lambda p: p.name)
def test_no_live_module_imports_the_analysis_layer(directory):
    """Layering: live/ depends on engine/ only, never on historical research."""
    offenders = []
    for path in sorted(directory.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
            elif isinstance(node, ast.Import):
                module = ",".join(alias.name for alias in node.names)
            if module and ".ingest" in module:
                offenders.append(f"{path.relative_to(SRC)} imports {module}")
    assert not offenders, "\n".join(offenders)


def test_engine_modules_do_not_import_the_live_layer():
    """The frozen engine must not depend on anything above it."""
    for path in sorted((SRC / "engine").rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert ".live" not in node.module, f"{path.name} imports {node.module}"
                assert ".analysis" not in node.module, f"{path.name} imports {node.module}"


# ---- 29. engine results unchanged --------------------------------------------------------


def test_sigma_and_p_raw_are_bit_identical_to_phase_3():
    assert sigma(40) == 12.0
    assert p_raw(40) == 0.6914624612740131
    assert p_raw(30) == 0.7475074624530771
    assert p_raw(44.5) == 0.6734422108808652
    assert p_raw(47) == 0.664775519361947


@pytest.mark.parametrize(
    "spread,total,expected",
    [
        ("1.5", "40.5", 0.7592858751269063),
        ("2.5", "44.5", 0.7434422108808652),
        ("-7.5", "43.5", 0.7471593818727904),
        ("-8.5", "46.5", 0.7364412874896358),
        ("2.5", "47", 0.734775519361947),
    ],
)
def test_p_est_is_bit_identical_to_phase_3(spread, total, expected):
    assert p_est("NFL", spread, total) == expected


def test_the_frozen_bump_is_unchanged():
    for spread in ("1.5", "2.5", "-7.5", "-8.5"):
        assert key_numbers_crossed(spread, "NFL") == 2
        leg = build_leg("g-A", "NFL", "A", spread, "44.5")
        assert leg.bump == 0.07
        assert leg.p_est == leg.p_raw + leg.bump


def test_teased_spreads_are_unchanged():
    assert teased_spread("1.5") == Decimal("7.5")
    assert teased_spread("2.5") == Decimal("8.5")
    assert teased_spread("-7.5") == Decimal("-1.5")
    assert teased_spread("-8.5") == Decimal("-2.5")


def test_guardrail_boundary_is_unchanged():
    assert passes_total_guardrail("NFL", "47")
    assert not passes_total_guardrail("NFL", "47.5")


def test_ticket_probability_is_still_a_plain_product():
    """No correlation adjustment was introduced anywhere."""
    values = [0.7434422108808652, 0.7471593818727904, 0.7364412874896358]
    assert ticket_probability(values) == math.prod(values)
    # Exactly the binary-float product, not a rounded 0.56: the engine multiplies
    # and does nothing else.
    assert ticket_probability([0.7, 0.8]) == 0.7 * 0.8


def test_break_even_and_ev_are_unchanged():
    assert break_even_probability(100 / 120) == pytest.approx(120 / 220)
    assert ev_per_unit(0.6, 100 / 120) == pytest.approx(0.6 * (100 / 120) - 0.4)


def test_a_live_card_reproduces_the_engine_exactly():
    """The card's numbers must be the engine's numbers, not a re-derivation."""
    from datetime import datetime, timedelta, timezone

    from tests.test_live_card import board, prices
    from teaser_model_v1.live.card import grade_week

    card = grade_week(board([("BUF", "MIA", "MIA", "2.5", "44.5")]), prices())
    leg = card.qualifying_legs[0]
    assert leg.p_est == p_est("NFL", "2.5", "44.5")
    assert leg.p_raw == p_raw("44.5")
    assert leg.teased_spread == teased_spread("2.5")
