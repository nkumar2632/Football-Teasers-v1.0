"""Integrity tests for the CFB paper track and the NFL prospective shadow run."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from teaser_model_v1.engine.constants import Geometry, Track
from teaser_model_v1.live.card import grade_week
from teaser_model_v1.live.paper import (
    ARCHIVED_PREGAME_REFERENCE,
    CURRENT_PREGAME,
    DATA_INSUFFICIENT,
    FINAL,
    IN_PROGRESS,
    OutcomeLeakageError,
    PregameLineInput,
    StatusOverlay,
    assert_no_outcome_fields,
    build_cfb_paper_legs,
    build_cfb_paper_tickets,
    overlay_status,
    primary_paper_legs,
    secondary_paper_legs,
)
from teaser_model_v1.live.placement import MODEL_DESIGNATED, PlacementLedger, PlacementRefused
from teaser_model_v1.live.rehydrate import card_from_dict, market_from_dict
from teaser_model_v1.live.workspace import Workspace

ROOT = Path(__file__).resolve().parents[1]


def pregame(team="ALA", opponent="FSU", spread="2.5", total="48.5",
            label=CURRENT_PREGAME, game_id="g1"):
    return PregameLineInput(
        game_id=game_id, team=team, opponent=opponent, spread=spread, total=total,
        kickoff="2026-09-19T15:30:00-04:00", source="TEST_SOURCE", line_label=label,
    )


# =======================================================================================
# 1. A started game can never use a live line for pregame reconstruction
# =======================================================================================


def test_only_pregame_provenance_labels_are_accepted():
    for label in (CURRENT_PREGAME, ARCHIVED_PREGAME_REFERENCE, "true_timestamped_pregame"):
        assert pregame(label=label).line_label == label


@pytest.mark.parametrize("label", ["live", "in_game", "current_live_line", "closing_line",
                                   DATA_INSUFFICIENT, ""])
def test_a_live_or_unproven_line_label_is_refused(label):
    with pytest.raises(ValueError, match="pregame provenance"):
        pregame(label=label)


def test_the_error_names_the_data_insufficient_route():
    with pytest.raises(ValueError, match="DATA_INSUFFICIENT"):
        pregame(label="live_line")


# =======================================================================================
# 2. Score/status fields cannot reach model selection
# =======================================================================================


def test_the_pregame_input_type_carries_no_outcome_field():
    assert_no_outcome_fields(pregame())
    names = {f for f in pregame().__dataclass_fields__}
    for banned in ("score", "status", "clock", "result", "margin"):
        assert not any(banned in n for n in names)


def test_an_object_carrying_a_score_is_refused_by_the_guard():
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class Leaky:
        game_id: str = "g1"
        team: str = "ALA"
        spread: str = "2.5"
        total: str = "48.5"
        home_score: int = 21

    with pytest.raises(OutcomeLeakageError, match="home_score"):
        assert_no_outcome_fields(Leaky())


@pytest.mark.parametrize("field_name", ["home_score", "game_status", "clock", "result",
                                        "final_margin", "is_covering", "quarter"])
def test_every_outcome_shaped_field_is_caught(field_name):
    with pytest.raises(OutcomeLeakageError):
        assert_no_outcome_fields({field_name: 1, "spread": "2.5"})


def test_building_a_board_rejects_a_leaky_input():
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class Leaky:
        game_id: str = "g1"
        team: str = "ALA"
        opponent: str = "FSU"
        spread: str = "2.5"
        total: str = "48.5"
        kickoff: str = ""
        source: str = "x"
        line_label: str = CURRENT_PREGAME
        final_score: str = "21-17"

    with pytest.raises(OutcomeLeakageError):
        build_cfb_paper_legs([Leaky()])


def test_selection_is_identical_regardless_of_what_happened():
    """The board depends only on the pregame line, by construction."""
    inputs = [
        pregame(team="ALA", spread="2.5", total="44.5", game_id="g1"),
        pregame(team="LSU", spread="1.5", total="48.5", game_id="g2"),
        pregame(team="UGA", spread="-7.5", total="50.5", game_id="g3"),
    ]
    first = primary_paper_legs(build_cfb_paper_legs(inputs))
    second = primary_paper_legs(build_cfb_paper_legs(inputs))
    assert [leg.leg_id for leg in first] == [leg.leg_id for leg in second]

    # Applying an overlay afterwards must not reorder anything.
    overlays = [
        StatusOverlay(game_id="g1", game_status=FINAL, home_score=3, away_score=40),
        StatusOverlay(game_id="g2", game_status=FINAL, home_score=50, away_score=0),
    ]
    rows = overlay_status(first, overlays)
    assert [row["leg_id"] for row in rows] == [leg.leg_id for leg in first]
    assert [row["rank"] for row in rows] == [1, 2, 3]


def test_an_in_progress_cover_is_flagged_as_not_a_result():
    legs = primary_paper_legs(build_cfb_paper_legs([pregame(game_id="g1")]))
    rows = overlay_status(
        legs,
        [StatusOverlay(game_id="g1", game_status=IN_PROGRESS, clock="Q3 4:12",
                       home_score=20, away_score=17)],
    )
    assert rows[0]["game_status"] == IN_PROGRESS
    assert rows[0]["is_result"] is False
    assert "currently" in rows[0]["cover_status"]


# =======================================================================================
# 3. CFB primary geometry stays PRIMARY / PAPER
# =======================================================================================


@pytest.mark.parametrize("spread", ["1.5", "2.5", "-7.5", "-8.5"])
def test_cfb_primary_geometry_is_primary_on_the_paper_track(spread):
    leg = build_cfb_paper_legs([pregame(spread=spread, total="44.5")])[0]
    assert leg.geometry_class == Geometry.PRIMARY.value
    assert leg.track == Track.PAPER.value
    assert leg.is_primary
    assert not leg.live_eligible


def test_cfb_primary_is_not_relabelled_secondary():
    legs = build_cfb_paper_legs([
        pregame(spread="2.5", total="44.5", game_id="g1"),
        pregame(spread="4.5", total="44.5", game_id="g2"),
    ])
    primary = primary_paper_legs(legs)
    secondary = secondary_paper_legs(legs)
    assert [leg.spread for leg in primary] == [Decimal("2.5")]
    assert [leg.spread for leg in secondary] == [Decimal("4.5")]
    assert set(l.leg_id for l in primary).isdisjoint(l.leg_id for l in secondary)


def test_the_cfb_guardrail_is_52_not_47():
    assert primary_paper_legs(build_cfb_paper_legs([pregame(total="52")]))
    assert not primary_paper_legs(build_cfb_paper_legs([pregame(total="52.5")]))
    # A total between the two guardrails qualifies for CFB and would not for the NFL.
    assert primary_paper_legs(build_cfb_paper_legs([pregame(total="50.5")]))


def test_the_cfb_bump_is_the_frozen_cfb_value():
    leg = build_cfb_paper_legs([pregame(spread="2.5", total="44.5")])[0]
    assert leg.key_numbers_crossed == 2
    assert leg.bump == pytest.approx(0.04)
    assert leg.p_est == pytest.approx(leg.p_raw + 0.04)

    one_key = build_cfb_paper_legs([pregame(spread="4.5", total="44.5")])[0]
    assert one_key.key_numbers_crossed == 1
    assert one_key.bump == pytest.approx(0.02)


# =======================================================================================
# 4. No CFB wager can reach placement
# =======================================================================================


def test_no_cfb_leg_is_ever_live_eligible():
    for spread in ("1.5", "2.5", "-7.5", "-8.5", "4.5"):
        leg = build_cfb_paper_legs([pregame(spread=spread)])[0]
        assert not leg.live_eligible
        assert leg.track == Track.PAPER.value


def test_cfb_tickets_are_never_placement_eligible_even_with_a_real_price():
    inputs = [
        pregame(team="ALA", spread="2.5", total="44.5", game_id="g1"),
        pregame(team="LSU", spread="1.5", total="45.5", game_id="g2"),
        pregame(team="UGA", spread="-7.5", total="46.5", game_id="g3"),
    ]
    primary = primary_paper_legs(build_cfb_paper_legs(inputs))
    _, tickets = build_cfb_paper_tickets(primary, {2: 0.9, 3: 2.0})
    assert tickets
    for ticket in tickets:
        # The frozen engine keeps every CFB leg on the PAPER track...
        assert all(leg.track is Track.PAPER for leg in ticket.legs)
        assert all(not leg.is_live_track for leg in ticket.legs)


def test_a_cfb_leg_cannot_enter_the_nfl_live_pool():
    from teaser_model_v1.engine.legs import build_leg, eligible_live_primary_legs

    cfb = build_leg("c1", "CFB", "ALA", "2.5", "44.5")
    assert eligible_live_primary_legs([cfb]) == []


def test_cfb_tickets_have_no_price_when_none_was_captured():
    inputs = [
        pregame(team="ALA", spread="2.5", total="44.5", game_id="g1"),
        pregame(team="LSU", spread="1.5", total="45.5", game_id="g2"),
    ]
    primary = primary_paper_legs(build_cfb_paper_legs(inputs))
    _, tickets = build_cfb_paper_tickets(primary, None)
    assert tickets
    for ticket in tickets:
        assert ticket.ev is None
        assert ticket.break_even is None
        assert not ticket.placement_eligible


# =======================================================================================
# 5-7. NFL prospective shadow run
# =======================================================================================

SHADOW_CARD = "card_2026w02_665ac88b756c"
SHADOW_MARKET = "mkt_2026w02_f544808f1a87"

shadow = pytest.mark.skipif(
    not (ROOT / "data" / "live" / "cards" / f"{SHADOW_CARD}.json").exists(),
    reason="shadow run not generated",
)


@pytest.fixture
def workspace():
    return Workspace(ROOT)


@shadow
def test_the_grading_snapshot_is_immutable_and_content_addressed(workspace):
    payload = workspace.snapshots.get(SHADOW_MARKET)
    snapshot = market_from_dict(payload)          # re-verifies the content hash
    assert snapshot.snapshot_id == SHADOW_MARKET

    # Re-offering identical content is a no-op; different content cannot collide.
    result = workspace.snapshots.put(SHADOW_MARKET, payload, kind="market_snapshot")
    assert result.already_present

    from teaser_model_v1.live.snapshot import ImmutableRecordError

    tampered = dict(payload)
    tampered["notes"] = "changed"
    with pytest.raises(ImmutableRecordError):
        workspace.snapshots.put(SHADOW_MARKET, tampered, kind="market_snapshot")


@shadow
def test_the_shadow_board_is_entirely_pregame(workspace):
    snapshot = market_from_dict(workspace.snapshots.get(SHADOW_MARKET))
    captured = snapshot.captured_at
    for quote in snapshot.quotes:
        assert quote.kickoff > captured, f"{quote.leg_key} was captured after kickoff"


@shadow
def test_missing_teaser_prices_make_ev_unavailable_and_block_eligibility(workspace):
    card = card_from_dict(workspace.cards.get(SHADOW_CARD))
    assert card.price_snapshot_id == ""
    assert card.tickets, "tickets are still constructed and displayed"
    for ticket in card.tickets:
        assert ticket.ev_per_unit == "UNAVAILABLE"
        assert ticket.break_even == "UNAVAILABLE"
        assert ticket.offered_american == "UNAVAILABLE"
        assert "NO_PRICE" in ticket.status
        assert not ticket.selected
    assert card.selected_ticket_keys == ()
    assert card.n_positive_ev == 0


@shadow
def test_the_shadow_card_respects_the_frozen_screen(workspace):
    card = card_from_dict(workspace.cards.get(SHADOW_CARD))
    for leg in card.qualifying_legs:
        assert leg.geometry_class == "PRIMARY"
        assert leg.track == "LIVE"
        assert Decimal(leg.total) <= Decimal("47")
        assert Decimal(leg.spread) in {
            Decimal("1.5"), Decimal("2.5"), Decimal("-7.5"), Decimal("-8.5")
        }
        assert leg.key_numbers_crossed == 2
        assert leg.bump == pytest.approx(0.07)
        assert leg.p_est == pytest.approx(leg.p_raw + 0.07)
    assert len(card.top_legs) <= 4


@shadow
def test_no_placement_and_no_units_were_recorded(workspace):
    assert workspace.placements.entries(2026) == []
    assert workspace.placements.model_entries(2026) == []
    status = workspace.season_ledger.season_status(
        2026, placements=workspace.placements.entries(2026),
        settlements=workspace.all_settlements(2026),
    )
    assert status["total_placed_tickets"] == 0
    assert status["total_units_staked"] == 0.0


@shadow
def test_no_recheck_was_performed_for_the_shadow_week(workspace):
    """Grading and the placement-time re-check are separate events."""
    card = card_from_dict(workspace.cards.get(SHADOW_CARD))
    assert workspace.rechecks_for_card(card.card_id) == []


@shadow
def test_a_shadow_ticket_cannot_be_placed_without_price_and_recheck(workspace, tmp_path):
    card = card_from_dict(workspace.cards.get(SHADOW_CARD))
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    ticket = card.tickets[0]
    with pytest.raises(PlacementRefused):
        ledger.record(card, ticket.ticket_key, sportsbook="AnyBook",
                      american_odds="-120",
                      placed_at=datetime(2026, 9, 20, 12, 0,
                                         tzinfo=timezone(timedelta(hours=-4))),
                      recorded_by="test", designation=MODEL_DESIGNATED)
    assert ledger.entries() == []
