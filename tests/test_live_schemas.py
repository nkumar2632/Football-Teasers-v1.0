"""Phase 4: market/price schemas, half-point fidelity, timestamps, immutability."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from teaser_model_v1.live.provenance import (
    NaiveTimestampError,
    canonical_json,
    content_hash,
    new_record_id,
    require_aware,
)
from teaser_model_v1.live.schemas import (
    MarketQuote,
    MarketSnapshot,
    MarketValidationError,
    TeaserPriceQuote,
    TeaserPriceSnapshot,
    american_to_decimal,
    decimal_to_american,
    normalize_team,
)
from teaser_model_v1.live.snapshot import (
    AppendOnlyLedger,
    AppendOnlyStore,
    ImmutableRecordError,
    correction_record,
)

EASTERN = timezone(timedelta(hours=-4))
KICKOFF = datetime(2026, 9, 20, 13, 0, tzinfo=EASTERN)
CAPTURED = datetime(2026, 9, 19, 10, 0, tzinfo=EASTERN)


def quote(team="MIA", spread="2.5", total="44.5", **kwargs):
    defaults = dict(
        game_id="2026_03_BUF_MIA", season=2026, week=3, kickoff=KICKOFF,
        home_team="MIA", away_team="BUF", team=team, spread=spread, total=total,
        sportsbook="BookX", captured_at=CAPTURED, ingestion_method="manual_csv",
    )
    defaults.update(kwargs)
    return MarketQuote(**defaults)


# ---- 1. half-point preservation --------------------------------------------------------


@pytest.mark.parametrize("value", ["2.5", 2.5, Decimal("2.5")])
def test_half_points_survive_every_input_type(value):
    assert quote(spread=value).spread == Decimal("2.5")


def test_half_points_are_not_rounded_anywhere():
    for spread in ("1.5", "2.5", "-7.5", "-8.5"):
        assert str(quote(team="MIA", spread=spread).spread) == spread


def test_a_line_off_the_half_point_grid_is_rejected():
    with pytest.raises(MarketValidationError, match="not a multiple of 0.5"):
        quote(spread="2.25")
    with pytest.raises(MarketValidationError, match="not a multiple of 0.5"):
        quote(total="44.75")


def test_float_input_does_not_drift():
    assert quote(spread=-8.5).spread == Decimal("-8.5")
    assert quote(total=47.0).total == Decimal("47")


def test_implausible_values_are_rejected():
    with pytest.raises(MarketValidationError):
        quote(spread="40.5")
    with pytest.raises(MarketValidationError):
        quote(total="95.5")


# ---- 2. timestamp timezone awareness ---------------------------------------------------


def test_naive_timestamps_are_refused_not_assumed():
    with pytest.raises(NaiveTimestampError):
        require_aware(datetime(2026, 9, 20, 13, 0))
    with pytest.raises(NaiveTimestampError):
        quote(captured_at="2026-09-19T10:00:00")


def test_aware_timestamps_in_several_forms_are_accepted():
    assert require_aware("2026-09-19T10:00:00-04:00").utcoffset() == timedelta(hours=-4)
    assert require_aware("2026-09-19T14:00:00Z").utcoffset() == timedelta(0)
    assert require_aware(CAPTURED) == CAPTURED


def test_kickoff_must_also_be_aware():
    with pytest.raises(NaiveTimestampError):
        quote(kickoff=datetime(2026, 9, 20, 13, 0))


# ---- teams -----------------------------------------------------------------------------


def test_team_validation_and_aliases():
    assert normalize_team("mia") == "MIA"
    assert normalize_team("OAK") == "LV"
    assert normalize_team("SD") == "LAC"
    with pytest.raises(MarketValidationError):
        normalize_team("XYZ")


def test_quoted_team_must_be_in_the_game():
    with pytest.raises(MarketValidationError, match="not in this game"):
        quote(team="DAL")


# ---- 3 & 4. immutable, append-only snapshots -------------------------------------------


def snapshot(**kwargs):
    defaults = dict(
        season=2026, week=3, captured_at=CAPTURED, sportsbook="BookX",
        ingestion_method="manual_csv",
        quotes=(quote(team="MIA"), quote(team="BUF", spread="-2.5")),
    )
    defaults.update(kwargs)
    return MarketSnapshot(**defaults)


def test_snapshot_id_is_content_derived_and_stable():
    first, second = snapshot(), snapshot()
    assert first.snapshot_id == second.snapshot_id
    assert first.snapshot_id.startswith("mkt_2026w03_")


def test_different_content_gives_a_different_id():
    later = snapshot(captured_at=CAPTURED + timedelta(hours=2))
    assert later.snapshot_id != snapshot().snapshot_id


def test_duplicate_quotes_in_one_snapshot_are_rejected():
    with pytest.raises(MarketValidationError, match="duplicate quote"):
        MarketSnapshot(
            season=2026, week=3, captured_at=CAPTURED, sportsbook="BookX",
            ingestion_method="manual_csv",
            quotes=(quote(team="MIA"), quote(team="MIA")),
        )


def test_store_is_idempotent_for_identical_content(tmp_path):
    store = AppendOnlyStore(tmp_path)
    snap = snapshot()
    first = store.put(snap.snapshot_id, snap.to_dict(), kind="market_snapshot")
    second = store.put(snap.snapshot_id, snap.to_dict(), kind="market_snapshot")
    assert first.created is True
    assert second.created is False and second.already_present
    assert len(store.list_records()) == 1


def test_store_refuses_to_rewrite_a_record(tmp_path):
    store = AppendOnlyStore(tmp_path)
    store.put("rec_1", {"a": 1}, kind="thing")
    with pytest.raises(ImmutableRecordError, match="append-only"):
        store.put("rec_1", {"a": 2}, kind="thing")
    assert store.get("rec_1") == {"a": 1}


def test_a_later_snapshot_never_replaces_an_earlier_one(tmp_path):
    store = AppendOnlyStore(tmp_path)
    first = snapshot()
    later = snapshot(captured_at=CAPTURED + timedelta(hours=3))
    store.put(first.snapshot_id, first.to_dict(), kind="market_snapshot")
    store.put(later.snapshot_id, later.to_dict(), kind="market_snapshot")
    assert len(store.list_records()) == 2
    assert store.get(first.snapshot_id)["captured_at"].endswith("10:00:00-04:00")


def test_correction_preserves_the_original(tmp_path):
    store = AppendOnlyStore(tmp_path)
    store.put("rec_1", {"spread": "2.5"}, kind="thing")
    correction = correction_record(
        supersedes_id="rec_1", reason="typo: entered 2.5, book showed 1.5",
        corrected_by="operator", replacement_id="rec_2",
    )
    store.put("cor_rec_1", correction, kind="correction")
    assert store.get("rec_1") == {"spread": "2.5"}
    assert store.get("cor_rec_1")["supersedes_id"] == "rec_1"


def test_correction_requires_a_target_and_a_reason():
    with pytest.raises(ValueError):
        correction_record(supersedes_id="", reason="x", corrected_by="me")
    with pytest.raises(ValueError):
        correction_record(supersedes_id="rec_1", reason="  ", corrected_by="me")


def test_ledger_is_append_only(tmp_path):
    ledger = AppendOnlyLedger(tmp_path / "l.jsonl")
    ledger.append({"n": 1})
    ledger.append({"n": 2})
    assert [row["n"] for row in ledger.entries()] == [1, 2]


def test_canonical_json_is_deterministic_and_exact():
    payload = {"b": Decimal("2.5"), "a": CAPTURED}
    assert canonical_json(payload) == canonical_json(dict(reversed(list(payload.items()))))
    assert '"2.5"' in canonical_json(payload)
    assert content_hash(payload) == content_hash(payload)


# ---- 5. actual vs hypothetical price ----------------------------------------------------


def test_american_and_decimal_odds_round_trip():
    assert american_to_decimal(-120) == Decimal(1) + Decimal(100) / Decimal(120)
    assert american_to_decimal(140) == Decimal("2.4")
    assert decimal_to_american(Decimal("2.4")) == Decimal("140")
    quote_2 = TeaserPriceQuote(ticket_size=2, sportsbook="BookX",
                               captured_at=CAPTURED, american_odds=-120)
    assert quote_2.net_profit_per_unit == pytest.approx(Decimal(100) / Decimal(120))


def test_decimal_input_is_normalised_to_american():
    quote_3 = TeaserPriceQuote(ticket_size=3, sportsbook="BookX",
                               captured_at=CAPTURED, decimal_odds="2.4")
    assert quote_3.american_odds == Decimal("140")


def test_price_requires_a_size_a_book_and_a_price():
    with pytest.raises(MarketValidationError):
        TeaserPriceQuote(ticket_size=4, sportsbook="B", captured_at=CAPTURED,
                         american_odds=-120)
    with pytest.raises(MarketValidationError):
        TeaserPriceQuote(ticket_size=2, sportsbook="B", captured_at=CAPTURED)
    with pytest.raises(MarketValidationError):
        TeaserPriceQuote(ticket_size=2, sportsbook="  ", captured_at=CAPTURED,
                         american_odds=-120)


def test_only_six_point_teasers_are_accepted():
    with pytest.raises(MarketValidationError, match="6-point"):
        TeaserPriceQuote(ticket_size=2, sportsbook="B", captured_at=CAPTURED,
                         american_odds=-120, teaser_points=7)


def test_two_prices_for_one_size_in_one_snapshot_is_rejected():
    quote_a = TeaserPriceQuote(ticket_size=2, sportsbook="B", captured_at=CAPTURED,
                               american_odds=-120)
    quote_b = TeaserPriceQuote(ticket_size=2, sportsbook="B", captured_at=CAPTURED,
                               american_odds=-130)
    with pytest.raises(MarketValidationError, match="two prices"):
        TeaserPriceSnapshot(season=2026, week=3, captured_at=CAPTURED,
                            sportsbook="B", quotes=(quote_a, quote_b))


def test_profit_by_size_omits_sizes_with_no_price():
    prices = TeaserPriceSnapshot(
        season=2026, week=3, captured_at=CAPTURED, sportsbook="B",
        quotes=(TeaserPriceQuote(ticket_size=2, sportsbook="B", captured_at=CAPTURED,
                                 american_odds=-120),),
    )
    assert set(prices.profit_by_size()) == {2}
    assert prices.quote_for(3) is None
