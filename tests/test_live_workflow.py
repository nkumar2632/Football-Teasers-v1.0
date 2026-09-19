"""Phase 4: re-check, placement ledger, settlement, report, season ledger, isolation."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from tests.test_live_card import FIVE_PRIMARY, board, prices  # noqa: F401
from teaser_model_v1.live.card import grade_week
from teaser_model_v1.live.ledger import (
    FINAL_OBSERVED,
    GRADING_LINE,
    TRUE_TIMESTAMPED_CLOSE,
    LineObservation,
    SeasonLedger,
    WeekLedgerEntry,
    line_movement,
)
from teaser_model_v1.live.placement import (
    EXTERNAL_NON_MODEL,
    MODEL_DESIGNATED,
    ExposureCapViolation,
    PlacementLedger,
    PlacementRefused,
)
from teaser_model_v1.live.recheck import (
    DISCARD_REBUILD,
    NOT_YET_RECHECKED,
    StaleSnapshotError,
    VALIDATED,
    recheck_card,
)
from teaser_model_v1.live.report import NOT_PLACED, render_weekly_report
from teaser_model_v1.live.settlement import (
    BOOK_CANCELLED,
    BOOK_VOID,
    BOOK_WIN,
    PrimaryPushInSettlement,
    grade_leg_settlement,
    settle_ticket,
)

EASTERN = timezone(timedelta(hours=-4))
CAPTURED = datetime(2026, 9, 19, 10, 0, tzinfo=EASTERN)
LATER = datetime(2026, 9, 20, 12, 40, tzinfo=EASTERN)
PLACED_AT = datetime(2026, 9, 20, 12, 45, tzinfo=EASTERN)
SETTLED_AT = datetime(2026, 9, 20, 16, 30, tzinfo=EASTERN)


def moved(team, spread=None, total=None):
    rows = []
    for away, home, side, old_spread, old_total in FIVE_PRIMARY:
        if side == team:
            rows.append((away, home, side, spread or old_spread, total or old_total))
        else:
            rows.append((away, home, side, old_spread, old_total))
    return rows


@pytest.fixture
def card():
    return grade_week(board(FIVE_PRIMARY), prices(two=-110, three=180), graded_at=CAPTURED)


def valid_recheck(card):
    """A clean re-check: later board, contemporaneous price, everything VALIDATED."""
    return recheck_card(
        card,
        board(FIVE_PRIMARY, captured_at=LATER),
        prices(two=-110, three=180, captured_at=LATER),
        rechecked_at=LATER,
    )


def place(ledger, card, ticket_key, *, recheck=None, **kwargs):
    """Record a model-designated placement with the mandatory re-check supplied."""
    defaults = dict(
        sportsbook="BookX", american_odds="-110", placed_at=PLACED_AT,
        recorded_by="operator",
    )
    defaults.update(kwargs)
    return ledger.record(card, ticket_key,
                         recheck=recheck if recheck is not None else valid_recheck(card),
                         **defaults)


# ---- 18-22. re-check --------------------------------------------------------------------


def test_recheck_requires_a_new_market_snapshot(card):
    with pytest.raises(StaleSnapshotError, match="NEW market snapshot"):
        recheck_card(card, board(FIVE_PRIMARY), prices(two=-110, three=180))


def test_recheck_invalidates_a_line_that_moved_off_primary_geometry(card):
    new_market = board(moved("NE", spread="3.0"), captured_at=LATER)
    result = recheck_card(card, new_market, prices(two=-110, three=180, captured_at=LATER),
                          rechecked_at=LATER)
    affected = [t for t in result.tickets if any("NE" in leg for leg in t.leg_ids)]
    assert affected
    for ticket in affected:
        assert ticket.verdict == DISCARD_REBUILD
        assert any("not primary geometry" in reason for reason in ticket.reasons)


def test_recheck_invalidates_a_total_that_crossed_the_guardrail(card):
    new_market = board(moved("CHI", total="47.5"), captured_at=LATER)
    result = recheck_card(card, new_market, prices(two=-110, three=180, captured_at=LATER),
                          rechecked_at=LATER)
    affected = [t for t in result.tickets if any("CHI" in leg for leg in t.leg_ids)]
    if affected:
        for ticket in affected:
            assert ticket.verdict == DISCARD_REBUILD
            assert any("guardrail" in reason for reason in ticket.reasons)


def test_recheck_invalidates_a_ticket_whose_price_turns_ev_negative(card):
    unchanged = board(FIVE_PRIMARY, captured_at=LATER)
    result = recheck_card(card, unchanged, prices(two=-300, three=100, captured_at=LATER),
                          rechecked_at=LATER)
    assert result.any_discarded
    for ticket in result.discarded:
        assert any("no longer positive EV" in reason for reason in ticket.reasons)


def test_recheck_flags_a_leg_that_vanished_from_the_market(card):
    survivors = [row for row in FIVE_PRIMARY if row[2] != "MIA"]
    result = recheck_card(card, board(survivors, captured_at=LATER),
                          prices(two=-110, three=180, captured_at=LATER),
                          rechecked_at=LATER)
    affected = [t for t in result.tickets if any("MIA" in leg for leg in t.leg_ids)]
    for ticket in affected:
        assert ticket.verdict == DISCARD_REBUILD
        assert any("disappeared" in reason for reason in ticket.reasons)


def test_a_missing_current_price_discards_rather_than_assuming_the_old_one(card):
    result = recheck_card(card, board(FIVE_PRIMARY, captured_at=LATER), None,
                          rechecked_at=LATER)
    assert result.any_discarded
    assert all("no current price" in " ".join(t.reasons) for t in result.discarded)


def test_a_discarded_three_team_ticket_is_never_downgraded(card):
    three_team = [t for t in card.tickets if t.n_legs == 3 and t.selected]
    keys = tuple(t.ticket_key for t in three_team) or tuple(
        t.ticket_key for t in card.tickets if t.n_legs == 3
    )
    new_market = board(moved("NE", spread="3.0"), captured_at=LATER)
    result = recheck_card(card, new_market, prices(two=-110, three=180, captured_at=LATER),
                          rechecked_at=LATER, tickets_to_check=keys)
    for ticket in result.tickets:
        # A discarded 3-team ticket stays a 3-team ticket in the record.
        assert ticket.n_legs == 3
    # Nothing in the result proposes a 2-leg replacement for a 3-leg ticket.
    assert all(t.n_legs == 3 for t in result.tickets)


def test_a_discard_triggers_a_rebuild_from_the_new_snapshot(card):
    new_market = board(moved("NE", spread="3.0"), captured_at=LATER)
    result = recheck_card(card, new_market, prices(two=-110, three=180, captured_at=LATER),
                          rechecked_at=LATER)
    assert result.any_discarded
    assert result.rebuilt_card is not None
    assert result.rebuilt_card.market_snapshot_id == new_market.snapshot_id
    assert result.rebuilt_card.card_id != card.card_id
    assert "NE" not in {leg.team for leg in result.rebuilt_card.qualifying_legs}


def test_no_rebuild_when_everything_validates(card):
    result = recheck_card(card, board(FIVE_PRIMARY, captured_at=LATER),
                          prices(two=-110, three=180, captured_at=LATER),
                          rechecked_at=LATER)
    assert result.overall == VALIDATED
    assert result.rebuilt_card is None


# ---- 23-24. PROPOSED is not PLACED ------------------------------------------------------


def test_a_proposed_card_creates_no_placement(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    assert ledger.entries() == []
    assert card.selected_tickets, "the card does propose tickets"
    assert ledger.entries() == [], "proposing must never create a placement"


def test_placement_requires_an_explicit_call(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    ticket = card.selected_tickets[0]
    record = place(ledger, card, ticket.ticket_key)
    assert len(ledger.entries()) == 1
    assert record.counts_toward_model
    assert record.placement_id.startswith("plc_2026w03_")


def test_an_unproposed_ticket_cannot_be_model_designated(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    unproposed = next(t for t in card.tickets if not t.selected)
    with pytest.raises(PlacementRefused, match="NOT on the proposed card"):
        place(ledger, card, unproposed.ticket_key)


def test_an_unknown_ticket_is_refused(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    with pytest.raises(PlacementRefused, match="not on card"):
        place(ledger, card, "nonsense|key")


def test_exposure_cap_blocks_a_third_unit_on_one_leg(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    ticket = card.selected_tickets[0]
    check = valid_recheck(card)
    for _ in range(2):
        place(ledger, card, ticket.ticket_key, recheck=check)
    with pytest.raises(ExposureCapViolation, match="2-unit weekly cap"):
        place(ledger, card, ticket.ticket_key, recheck=check)
    assert max(ledger.current_exposure(2026, 3).values()) <= 2


def test_an_external_bet_is_recorded_but_excluded_from_model_performance(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    unproposed = next(t for t in card.tickets if not t.selected)
    record = ledger.record(
        card, unproposed.ticket_key, sportsbook="BookX", american_odds="-110",
        placed_at=PLACED_AT, recorded_by="operator", designation=EXTERNAL_NON_MODEL,
    )
    assert not record.counts_toward_model
    assert len(ledger.entries()) == 1
    assert ledger.model_entries() == []
    assert ledger.current_exposure(2026, 3) == {}


def test_a_ticket_discarded_at_recheck_cannot_be_placed(tmp_path, card):
    """The defect the synthetic rehearsal exposed: stale tickets must not be reusable."""
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    new_market = board(moved("NE", spread="3.0"), captured_at=LATER)
    result = recheck_card(card, new_market, prices(two=-110, three=180, captured_at=LATER),
                          rechecked_at=LATER)
    discarded = result.discarded[0]
    with pytest.raises(PlacementRefused, match="DISCARDED at re-check"):
        place(ledger, card, discarded.ticket_key, recheck=result)


def test_a_validated_ticket_can_be_placed_with_the_recheck_attached(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    new_market = board(moved("NE", spread="3.0"), captured_at=LATER)
    result = recheck_card(card, new_market, prices(two=-110, three=180, captured_at=LATER),
                          rechecked_at=LATER)
    assert result.validated, "the fixture should leave at least one ticket valid"
    record = place(ledger, card, result.validated[0].ticket_key, recheck=result)
    assert record.counts_toward_model
    assert record.recheck_id == result.recheck_id


def test_a_ticket_absent_from_the_recheck_is_refused(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    keys = (card.selected_tickets[0].ticket_key,)
    result = recheck_card(card, board(FIVE_PRIMARY, captured_at=LATER),
                          prices(two=-110, three=180, captured_at=LATER),
                          rechecked_at=LATER, tickets_to_check=keys)
    other = next(t for t in card.selected_tickets if t.ticket_key not in keys)
    with pytest.raises(PlacementRefused, match="not covered by re-check"):
        place(ledger, card, other.ticket_key, recheck=result)


def test_placement_requires_a_book_and_a_positive_stake(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    ticket = card.selected_tickets[0]
    with pytest.raises(PlacementRefused):
        place(ledger, card, ticket.ticket_key, sportsbook="  ")
    with pytest.raises(PlacementRefused):
        place(ledger, card, ticket.ticket_key, stake_units=0)


# ---- 26-27. settlement ------------------------------------------------------------------


def test_model_grading_is_separate_from_book_settlement(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    ticket = card.selected_tickets[0]
    placement = place(ledger, card, ticket.ticket_key)
    legs = tuple(
        grade_leg_settlement(leg_id=leg_id, team=leg_id.split("-")[-1],
                             teased_spread="7.5", final_margin=3)
        for leg_id in placement.leg_ids
    )
    record = settle_ticket(placement=placement.to_dict(), legs=legs,
                           book_settlement=BOOK_VOID, settled_at=SETTLED_AT,
                           profit_loss_units=0.0)
    assert record.model_ticket_result == "WIN"
    assert record.book_settlement == BOOK_VOID
    assert record.results_agree is False
    assert record.profit_loss_units == 0.0


def test_a_cancelled_game_records_the_books_own_result(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    ticket = card.selected_tickets[0]
    placement = place(ledger, card, ticket.ticket_key)
    legs = tuple(
        grade_leg_settlement(leg_id=leg_id, team="X", teased_spread="7.5", final_margin=-20)
        for leg_id in placement.leg_ids
    )
    record = settle_ticket(placement=placement.to_dict(), legs=legs,
                           book_settlement=BOOK_CANCELLED, settled_at=SETTLED_AT)
    assert record.model_ticket_result == "LOSS"
    assert record.book_settlement == BOOK_CANCELLED
    assert record.profit_loss_units == 0.0


def test_profit_is_derived_from_the_recorded_price_on_a_win(tmp_path, card):
    ledger = PlacementLedger(tmp_path / "p.jsonl")
    ticket = card.selected_tickets[0]
    placement = place(ledger, card, ticket.ticket_key)
    legs = tuple(
        grade_leg_settlement(leg_id=leg_id, team="X", teased_spread="7.5", final_margin=3)
        for leg_id in placement.leg_ids
    )
    record = settle_ticket(placement=placement.to_dict(), legs=legs,
                           book_settlement=BOOK_WIN, settled_at=SETTLED_AT)
    assert record.profit_loss_units == pytest.approx(100 / 110)


def test_a_primary_leg_can_never_settle_as_a_push():
    with pytest.raises(PrimaryPushInSettlement):
        grade_leg_settlement(leg_id="g-A", team="A", teased_spread="-2.0", final_margin=2)
    # ...and the half-point geometry never produces one.
    for teased, margin in (("7.5", -7), ("8.5", -8), ("-1.5", 2), ("-2.5", 3)):
        assert grade_leg_settlement(leg_id="g", team="A", teased_spread=teased,
                                    final_margin=margin).model_result in {"WIN", "LOSS"}


def test_an_invalid_book_settlement_is_refused(tmp_path, card):
    from teaser_model_v1.live.schemas import MarketValidationError

    ledger = PlacementLedger(tmp_path / "p.jsonl")
    ticket = card.selected_tickets[0]
    placement = place(ledger, card, ticket.ticket_key)
    legs = (grade_leg_settlement(leg_id="g", team="A", teased_spread="7.5", final_margin=3),)
    with pytest.raises(MarketValidationError):
        settle_ticket(placement=placement.to_dict(), legs=legs,
                      book_settlement="SORT_OF_WON", settled_at=SETTLED_AT)


# ---- 11 (spec). market-quality naming ---------------------------------------------------


def test_a_final_observation_is_never_called_a_close():
    with pytest.raises(ValueError, match="true_timestamped_close"):
        LineObservation(leg_id="g", label=TRUE_TIMESTAMPED_CLOSE, spread="2.5",
                        total="44.5", sportsbook="BookX", observed_at=CAPTURED,
                        market_snapshot_id="mkt_1")


def test_line_movement_declines_to_compute_clv():
    earlier = LineObservation(leg_id="g", label=GRADING_LINE, spread="2.5", total="44.5",
                              sportsbook="BookX", observed_at=CAPTURED,
                              market_snapshot_id="mkt_1")
    later = LineObservation(leg_id="g", label=FINAL_OBSERVED, spread="1.5", total="45.5",
                            sportsbook="BookX", observed_at=LATER,
                            market_snapshot_id="mkt_2")
    movement = line_movement(earlier, later)
    assert movement["spread_change"] == "-1.0"
    assert movement["total_change"] == "1.0"
    assert movement["clv_computed"] is False
    assert "not a documented close" in movement["clv_note"]


def test_line_movement_refuses_to_compare_different_legs():
    a = LineObservation(leg_id="g1", label=GRADING_LINE, spread="2.5", total="44.5",
                        sportsbook="B", observed_at=CAPTURED, market_snapshot_id="m")
    b = LineObservation(leg_id="g2", label=FINAL_OBSERVED, spread="2.5", total="44.5",
                        sportsbook="B", observed_at=LATER, market_snapshot_id="m")
    with pytest.raises(ValueError, match="SAME leg"):
        line_movement(a, b)


# ---- 25. zero-bet weeks -----------------------------------------------------------------


def test_zero_qualifier_and_zero_bet_weeks_appear_in_the_ledger(tmp_path):
    ledger = SeasonLedger(tmp_path / "season.jsonl")
    ledger.record_week(WeekLedgerEntry(
        season=2026, week=1, recorded_at=CAPTURED, games_scanned=16,
        qualifying_primary_legs=0, top_four_legs=0, positive_ev_tickets=0,
        proposed_tickets=0, placed_tickets=0, units_staked=0.0,
    ))
    ledger.record_week(WeekLedgerEntry(
        season=2026, week=2, recorded_at=CAPTURED, games_scanned=15,
        qualifying_primary_legs=3, top_four_legs=3, positive_ev_tickets=2,
        proposed_tickets=2, placed_tickets=0, units_staked=0.0,
    ))
    status = ledger.season_status(2026)
    assert status["weeks_recorded"] == 2
    assert status["weeks_with_zero_qualifying_legs"] == 1
    assert status["weeks_with_zero_placements"] == 2
    assert status["total_placed_tickets"] == 0


def test_season_status_counts_every_week_not_just_active_ones(tmp_path):
    ledger = SeasonLedger(tmp_path / "season.jsonl")
    for week in range(1, 6):
        ledger.record_week(WeekLedgerEntry(
            season=2026, week=week, recorded_at=CAPTURED, games_scanned=16,
            qualifying_primary_legs=0 if week % 2 else 2,
            top_four_legs=0 if week % 2 else 2,
            positive_ev_tickets=0, proposed_tickets=0, placed_tickets=0,
            units_staked=0.0,
        ))
    assert ledger.season_status(2026)["weeks_recorded"] == 5
    assert len(ledger.latest_per_week(2026)) == 5


# ---- 28. reproducible report ------------------------------------------------------------


def test_report_is_reproducible(card):
    first = render_weekly_report(card, generated_at=CAPTURED)
    second = render_weekly_report(card, generated_at=CAPTURED)
    assert first == second


def test_report_marks_an_unchecked_card_as_stale(card):
    text = render_weekly_report(card, generated_at=CAPTURED)
    assert NOT_YET_RECHECKED in text
    assert "stale until re-checked" in text
    assert NOT_PLACED in text


def test_report_shows_discard_and_rebuild(card):
    new_market = board(moved("NE", spread="3.0"), captured_at=LATER)
    result = recheck_card(card, new_market, prices(two=-110, three=180, captured_at=LATER),
                          rechecked_at=LATER)
    text = render_weekly_report(card, recheck=result, generated_at=LATER)
    assert DISCARD_REBUILD in text
    assert "not** substituted" in text or "not substituted" in text


def test_report_states_no_constructible_ticket():
    card = grade_week(board(FIVE_PRIMARY[:1]), prices(), graded_at=CAPTURED)
    text = render_weekly_report(card, generated_at=CAPTURED)
    assert "NO CONSTRUCTIBLE LIVE PRIMARY TICKET" in text


def test_report_warns_when_no_price_was_supplied():
    card = grade_week(board(FIVE_PRIMARY), None, graded_at=CAPTURED)
    text = render_weekly_report(card, generated_at=CAPTURED)
    assert "No actual teaser price was supplied" in text
    assert "no ticket is placement-eligible" in text.lower()


# ---- Phase 4.2 presentation invariants ---------------------------------------------------
#
# The report is a VIEW. These tests pin the property that matters: it must not move a
# single model value. They are deliberately written against the card, not against golden
# text, so the layout can keep evolving while the numbers stay nailed down.


from teaser_model_v1.live.report import _signed


def _cells(line):
    return [c.strip().replace("**", "") for c in line.strip().strip("|").split("|")]


def _rows(text, first_header):
    out, on = [], False
    for line in text.splitlines():
        if line.startswith("|") and _cells(line)[0] == first_header:
            on = True
            continue
        if on:
            if not line.startswith("|"):
                break
            if set(line) <= set("|- "):
                continue
            out.append(_cells(line))
    return out


def _section(text, heading):
    start = text.index(heading)
    end = text.find("\n## ", start + 1)
    return text[start: end if end != -1 else len(text)]


def test_report_legs_match_the_card_exactly(card):
    text = render_weekly_report(card, generated_at=CAPTURED)
    rows = _rows(text, "Rank")
    assert len(rows) == len(card.qualifying_legs)
    for row, leg in zip(rows, card.qualifying_legs):
        original, teased = (part.strip() for part in row[2].split("→"))
        assert int(row[0]) == leg.rank
        assert row[1] == leg.team
        # Signed rendering of the stored value — the sign is display, the number is not.
        assert original == _signed(leg.spread)
        assert teased == _signed(leg.teased_spread)
        assert row[3] == str(leg.total)
        # P_est is displayed to 1dp; it must be exactly that rendering of the stored
        # full-precision value — not a separately computed number.
        assert row[4] == f"{leg.p_est * 100:.1f}%"


def test_report_ticket_board_matches_the_card_exactly(card):
    text = render_weekly_report(card, generated_at=CAPTURED)
    rows = _rows(_section(text, "## Full ticket board"), "Ticket")
    assert len(rows) == len(card.tickets)
    for row, ticket in zip(rows, card.tickets):
        assert row[0] == "+".join(ticket.teams)
        assert row[1] == _signed(ticket.offered_american)
        assert row[2] == f"{ticket.p_ticket * 100:.1f}%"
        if ticket.break_even != "UNAVAILABLE":
            assert row[3] == f"{float(ticket.break_even) * 100:.1f}%"
        if ticket.ev_percent != "UNAVAILABLE":
            assert row[4] == f"{float(ticket.ev_percent.rstrip('%')):.1f}%"
        assert row[5].endswith(ticket.status)


def test_report_shows_negative_ev_tickets_too(card):
    """The board must never hide a losing ticket behind the proposed card."""
    text = render_weekly_report(card, generated_at=CAPTURED)
    board_rows = _rows(_section(text, "## Full ticket board"), "Ticket")
    assert {r[0] for r in board_rows} == {"+".join(t.teams) for t in card.tickets}


def test_report_selected_set_and_exposure_are_unchanged(card):
    text = render_weekly_report(card, generated_at=CAPTURED)
    shown = {r[0] for r in _rows(_section(text, "## Full ticket board"), "Ticket")
             if "**" in "".join(r)} or None
    # exposure line: "Leg exposure: TB 2u · ATL 2u"
    line = next(l for l in text.splitlines() if l.startswith("Leg exposure:"))
    parsed = {}
    for part in line.split(":", 1)[1].split("·"):
        team, units = part.replace("**", "").strip().rsplit(" ", 1)
        parsed[team.strip()] = int(units.rstrip("u"))
    assert parsed == {leg.split("-")[-1]: units for leg, units in card.exposure.items()}
    assert sum(parsed.values()) == sum(card.exposure.values())


def test_report_badges_cover_every_operational_state(card):
    from teaser_model_v1.live.report import (
        BADGE_DISCARD, BADGE_PENDING, BADGE_PLACED, BADGE_SHADOW, BADGE_VALIDATED,
    )
    unchecked = render_weekly_report(card, generated_at=CAPTURED)
    assert BADGE_SHADOW in unchecked and BADGE_PENDING in unchecked

    same = recheck_card(card, board(FIVE_PRIMARY, captured_at=LATER),
                        prices(two=-110, three=180, captured_at=LATER), rechecked_at=LATER)
    assert BADGE_VALIDATED in render_weekly_report(card, recheck=same, generated_at=LATER)

    broken = recheck_card(card, board(moved("NE", spread="3.0"), captured_at=LATER),
                          prices(two=-110, three=180, captured_at=LATER), rechecked_at=LATER)
    assert BADGE_DISCARD in render_weekly_report(card, recheck=broken, generated_at=LATER)

    placed = [{
        "placement_id": "plc_x", "ticket_key": "a|b", "sportsbook": "BOOK",
        "american_odds": "-110", "stake_units": 1, "placed_at": "2026-09-20T12:45:00-04:00",
        "designation": "MODEL_DESIGNATED",
    }]
    assert BADGE_PLACED in render_weekly_report(card, placements=placed, generated_at=CAPTURED)


def test_report_never_signals_with_colour_alone(card):
    """Every status indicator carries its text label, not just a coloured dot."""
    from teaser_model_v1.live.report import AMBER, BLUE, GRAY, GREEN, RED
    text = render_weekly_report(card, generated_at=CAPTURED)
    for line in text.splitlines():
        for dot in (GREEN, AMBER, RED, GRAY, BLUE):
            if dot in line:
                after = line.split(dot, 1)[1].replace("*", "").strip()
                assert after and after[0].isalpha(), f"bare colour indicator in: {line!r}"


def test_report_puts_audit_details_below_the_card(card):
    """Snapshot ids belong at the bottom; the operational state belongs at the top."""
    text = render_weekly_report(card, generated_at=CAPTURED)
    assert text.index("## Proposed card") < text.index("## Full ticket board")
    assert text.index("## Full ticket board") < text.index("## Audit")
    assert text.index("## Audit") > text.index(card.market_snapshot_id)  # header-free top
    assert text.rindex(card.market_snapshot_id) > text.index("## Audit")


def test_report_pending_verdict_is_shown_per_proposed_ticket(card):
    from teaser_model_v1.live.report import VERDICT_PENDING
    text = render_weekly_report(card, generated_at=CAPTURED)
    section = _section(text, "## Re-check")
    for ticket in card.selected_tickets:
        assert "+".join(ticket.teams) in section
    assert section.count(VERDICT_PENDING) >= len(card.selected_tickets)


# ---- Phase 4.2b explicit-sign and positive-EV presentation -------------------------------


def test_signed_helper_rules():
    """Display-only sign rendering. Never mutates the value, only how it prints."""
    assert _signed("2.5") == "+2.5"
    assert _signed("-8.5") == "-8.5"
    assert _signed("+8.5") == "+8.5"          # already signed, left alone
    assert _signed("170") == "+170"
    assert _signed("-110") == "-110"
    assert _signed("100") == "+100"
    assert _signed("0") == "0"                # pick'em takes no sign
    assert _signed("UNAVAILABLE") == "UNAVAILABLE"
    assert _signed("") == "UNAVAILABLE"
    # The numeric content must survive untouched.
    for raw in ("2.5", "-8.5", "170", "-110", "0"):
        assert float(_signed(raw)) == float(raw)


def test_report_positive_spreads_keep_their_plus_sign(card):
    text = render_weekly_report(card, generated_at=CAPTURED)
    rows = _rows(text, "Rank")
    signed_seen = False
    for row, leg in zip(rows, card.qualifying_legs):
        original, teased = (part.strip() for part in row[2].split("→"))
        for shown, stored in ((original, leg.spread), (teased, leg.teased_spread)):
            if float(stored) > 0:
                assert shown.startswith("+"), f"unsigned positive spread {shown!r}"
                signed_seen = True
            elif float(stored) < 0:
                assert shown.startswith("-")
            assert float(shown) == float(stored)
    assert signed_seen, "fixture must contain at least one positive spread"


def test_report_positive_american_odds_keep_their_plus_sign(card):
    text = render_weekly_report(card, generated_at=CAPTURED)
    rows = _rows(_section(text, "## Full ticket board"), "Ticket")
    signed_seen = False
    for row, ticket in zip(rows, card.tickets):
        if ticket.offered_american == "UNAVAILABLE":
            continue
        shown = row[1]
        if float(ticket.offered_american) > 0:
            assert shown.startswith("+"), f"unsigned positive price {shown!r}"
            signed_seen = True
        else:
            assert shown.startswith("-")
        assert float(shown) == float(ticket.offered_american)
    assert signed_seen, "fixture must contain at least one plus-money price"


def test_proposed_card_visibly_marks_every_ticket_positive_ev(card):
    """A reader must not have to infer positive EV from the selection rule."""
    text = render_weekly_report(card, generated_at=CAPTURED)
    section = _section(text, "## Proposed card")
    assert "POSITIVE EV" in section.upper()
    rows = _rows(section, "Ticket")
    assert rows, "fixture must propose at least one ticket"
    assert len(rows) == len(card.selected_tickets)
    for row, ticket in zip(rows, card.selected_tickets):
        assert row[0] == "+".join(ticket.teams)
        assert "POSITIVE" in row[5].upper(), f"no positive-EV marker in {row!r}"
        assert row[5].endswith(ticket.status)
        assert row[6] == "1u"
    # And the claim must be true of the stored card, not merely printed.
    assert all("POSITIVE" in t.status.upper() for t in card.selected_tickets)


# ---- Research view: all 6-point teaser legs -----------------------------------------------
#
# The whole point of this table is that it is inert. These tests pin that: it shows every
# side, it never promotes one, and it cannot move the card.


def _teased(snapshot=None):
    from teaser_model_v1.live.research import teased_board_rows
    return teased_board_rows(snapshot if snapshot is not None else board(FIVE_PRIMARY))


def test_teased_board_covers_every_side_on_the_board():
    snapshot = board(FIVE_PRIMARY)
    rows = _teased(snapshot)
    assert len(rows) == len(snapshot.quotes)
    assert {r.team for r in rows} == {q.team for q in snapshot.quotes}


def test_teased_board_never_promotes_a_secondary_leg():
    """The headline invariant: P_est cannot buy eligibility."""
    for row in _teased():
        if row.geometry_class == "SECONDARY":
            assert row.track == "PAPER", f"{row.team} promoted to {row.track}"
            assert not row.on_live_board
            assert not row.is_primary_live
    # And it holds no matter how high P_est runs.
    hottest = max(_teased(), key=lambda r: r.p_est)
    if hottest.geometry_class == "SECONDARY":
        assert hottest.track == "PAPER"


def test_teased_board_keeps_whole_number_geometry_secondary():
    from teaser_model_v1.engine.numeric import is_whole_number
    seen = False
    for row in _teased(board(moved("NE", spread="3.0"))):
        if is_whole_number(row.spread):
            assert row.geometry_class == "SECONDARY"
            assert row.track == "PAPER"
            seen = True
    assert seen, "fixture must contain a whole-number line"


def test_teased_board_shows_guardrail_failures_rather_than_hiding_them():
    from teaser_model_v1.live.research import FAILS_GUARDRAIL
    rows = _teased(board(moved("NE", total="55.0")))
    over = [r for r in rows if float(r.total) > 47]
    assert over, "fixture must contain a game over the total guardrail"
    for row in over:
        assert FAILS_GUARDRAIL in row.exclusion_reason
        assert not row.on_live_board


def test_teased_board_flags_push_capable_legs_with_the_exact_label():
    from teaser_model_v1.engine.numeric import is_whole_number
    from teaser_model_v1.live.report import render_weekly_report
    from teaser_model_v1.live.research import PUSH_NOT_MODELED
    snapshot = board(moved("NE", spread="3.0"))
    rows = _teased(snapshot)
    pushable = [r for r in rows if r.can_push]
    assert pushable, "fixture must contain a teased line that can push"
    for row in rows:
        assert row.can_push == is_whole_number(row.teased_spread)
    card = grade_week(snapshot, prices(two=-110, three=180), graded_at=CAPTURED)
    text = render_weekly_report(card, teased_board=rows, generated_at=CAPTURED)
    assert PUSH_NOT_MODELED in text
    assert PUSH_NOT_MODELED == "RESEARCH P_est — PUSH SETTLEMENT NOT MODELED"


def test_teased_board_sort_is_primary_live_first_then_p_est():
    rows = _teased()
    flags = [r.is_primary_live for r in rows]
    assert flags == sorted(flags, reverse=True), "PRIMARY/LIVE must lead"
    for group in (True, False):
        block = [r.p_est for r in rows if r.is_primary_live is group]
        assert block == sorted(block, reverse=True)


def test_teased_board_cannot_change_the_card():
    """Rendering the research view must leave every card-derived section identical."""
    from teaser_model_v1.live.report import render_weekly_report
    snapshot = board(FIVE_PRIMARY)
    card = grade_week(snapshot, prices(two=-110, three=180), graded_at=CAPTURED)
    without = render_weekly_report(card, generated_at=CAPTURED)
    with_view = render_weekly_report(card, teased_board=_teased(snapshot),
                                     generated_at=CAPTURED)
    # Everything above the research section is byte-identical.
    head = "## All 6-point teaser legs"
    assert head not in without
    assert with_view[: with_view.index("---\n\n" + head)] == without[: without.index("---\n\n## Audit")]
    # And the card itself is untouched by the view.
    assert card.selected_ticket_keys == grade_week(
        snapshot, prices(two=-110, three=180), graded_at=CAPTURED).selected_ticket_keys
    assert card.exposure == grade_week(
        snapshot, prices(two=-110, three=180), graded_at=CAPTURED).exposure


def test_teased_board_p_est_is_the_engines_value_shown_to_one_decimal():
    from teaser_model_v1.engine.legs import build_leg
    from teaser_model_v1.live.report import _pct
    snapshot = board(FIVE_PRIMARY)
    by_team = {q.team: q for q in snapshot.quotes}
    for row in _teased(snapshot):
        quote = by_team[row.team]
        engine_leg = build_leg(leg_id="x", league="NFL", team=row.team,
                               spread=quote.spread, game_total=quote.total)
        assert row.p_est == engine_leg.p_est          # full precision preserved
        assert row.teased_spread == engine_leg.teased_spread
        assert row.key_numbers_crossed == engine_leg.key_numbers_crossed
        assert _pct(row.p_est) == f"{engine_leg.p_est * 100:.1f}%"


def test_secondary_push_legs_are_never_presented_as_comparable_win_probabilities():
    """A push-capable secondary value must not be able to masquerade as a P_est.

    The failure this guards against is a reader running their eye down one column and
    concluding a paper leg "beats" the live card. Structurally: nothing secondary may
    appear in the P_est column, the value must be named a research score, and the
    non-comparability must be stated in words rather than implied by a symbol.
    """
    from teaser_model_v1.live.report import render_weekly_report
    from teaser_model_v1.live.research import (
        NOT_COMPARABLE_NOTE, PRIMARY_VALUE_LABEL, PUSH_NOT_MODELED, RESEARCH_SCORE_LABEL,
    )
    snapshot = board(moved("NE", spread="3.0"))
    rows = _teased(snapshot)
    card = grade_week(snapshot, prices(two=-110, three=180), graded_at=CAPTURED)
    text = render_weekly_report(card, teased_board=rows, generated_at=CAPTURED)
    section = _section(text, "## All 6-point teaser legs")

    pushable = [r for r in rows if r.can_push and not r.is_primary_live]
    assert pushable, "fixture must contain a push-capable secondary leg"

    # Locate the two value columns by name, and prove they are distinct columns.
    header = next(
        line for line in section.splitlines()
        if line.startswith("|") and PRIMARY_VALUE_LABEL in line
    )
    columns = _cells(header)
    p_est_at = columns.index(PRIMARY_VALUE_LABEL)
    score_at = columns.index(RESEARCH_SCORE_LABEL)
    assert p_est_at != score_at

    body = _rows(section, "Team")
    assert len(body) == len(rows)
    by_team = {r.team: r for r in rows}
    for cells in body:
        row = by_team[cells[0]]
        if row.is_primary_live:
            assert cells[p_est_at] != "—"
            assert cells[score_at] == "—", "a live P_est leaked into the research column"
        else:
            # The decisive assertion: no secondary value in the P_est column, ever.
            assert cells[p_est_at] == "—", f"{row.team} secondary value shown as P_est"
            assert cells[score_at] != "—"
            if row.can_push:
                assert "‡" in cells[score_at]

    # The caveat must be spelled out, not left to a symbol.
    assert RESEARCH_SCORE_LABEL in section
    assert NOT_COMPARABLE_NOTE in section
    assert PUSH_NOT_MODELED in section
    assert "not directly comparable" in section or "must not be compared" in section
    # And the old, comparability-implying phrasing must not come back.
    assert "higher P_est than a leg on the live board" not in section
