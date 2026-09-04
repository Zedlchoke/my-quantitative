"""V13 P0 crypto compatibility proof: offline tests, synthetic fixtures only.

No network, no downloads, no real data files.  Every fixture row below is
built in-process and mirrors the STAGED SHAPES of the frozen loaders
(``research/funding_pit.py``, ``research/funding_settlements_v10.py``,
``research/v12/data_contract.py``, ``data/derivatives.py``) so the mapping is
proved against the conventions the frozen code actually consumes.

Binding pins (PLAN_crypto_v13.md section 6 P0):

1. a decision evaluated at time T can never read a record whose
   ``available_time_utc > T``;
2. each authorized dataset mapping stamps availability with the TRUE dataset
   class (bar close / settlement / OI snapshot / mark snapshot), never with
   retrieval time;
3. unsupported dataset types are refused fail-closed.
"""

from datetime import datetime, timedelta, timezone

import pytest

from research.data_fusion.crypto_compat import (
    AUTHORIZED_DATASET_TYPES,
    AVAILABILITY_SEMANTICS,
    CryptoCompatContext,
    CryptoCompatError,
    UnsupportedDatasetError,
    map_row,
    map_rows,
)
from research.data_fusion.models import NormalizedRecord
from research.data_fusion.pit import select_asof

UTC = timezone.utc


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=UTC)


BAR_CLOSE = utc(2026, 1, 15, 4, 15)          # 15m slot boundary (bar close)
FUNDING_SETTLE = utc(2026, 1, 15, 8)         # native settlement stamp
DECISION_MID = utc(2026, 1, 15, 12)          # between the two settlements
FUNDING_SETTLE_LATE = utc(2026, 1, 15, 16)   # later settlement (NOT readable at 12:00)
OI_SNAPSHOT = utc(2026, 1, 15, 4, 55)        # OI snapshot stamp
MARK_KLINE_CLOSE = utc(2026, 1, 15, 4, 15)   # mark kline close time
RETRIEVED = utc(2026, 1, 15, 20)             # the only time retrieval is honest

BAR_CLOSE_NS = int(BAR_CLOSE.timestamp()) * 1_000_000_000
FUNDING_SETTLE_MS = int(FUNDING_SETTLE.timestamp()) * 1_000
FUNDING_SETTLE_LATE_MS = int(FUNDING_SETTLE_LATE.timestamp()) * 1_000
OI_SNAPSHOT_MS = int(OI_SNAPSHOT.timestamp()) * 1_000
MARK_OPEN_MS = int(utc(2026, 1, 15, 4, 0).timestamp()) * 1_000
MARK_KLINE_CLOSE_MS = int(MARK_KLINE_CLOSE.timestamp()) * 1_000

SYNTHETIC_SHA = "c" * 64


@pytest.fixture
def context() -> CryptoCompatContext:
    return CryptoCompatContext(
        symbol="BTCUSDT",
        retrieved_time_utc=RETRIEVED,
        raw_path="funding_data/scan_2026/BTCUSDT/funding.json",
        raw_sha256=SYNTHETIC_SHA,
    )


def bar_row() -> dict:
    return {"ts_event": BAR_CLOSE_NS, "open": "100.0", "high": "101.0", "low": "99.0",
            "close": "100.5", "volume": "12.5"}


def funding_row(stamp_ms: int = FUNDING_SETTLE_MS, rate: str = "0.0001") -> dict:
    return {"fundingTime": stamp_ms, "fundingRate": rate}


def oi_history_row() -> dict:
    return {"timestamp": OI_SNAPSHOT_MS, "sumOpenInterest": "52300.125"}


def oi_consolidated_row() -> dict:
    return {"create_time": "2026-01-15T04:55:00Z", "sum_open_interest": 52300.125}


def mark_kline_row() -> list:
    # Binance markPriceKlines layout: [open_time, o, h, l, c, v, close_time, ...]
    return [MARK_OPEN_MS, "100.1", "100.9", "100.0", "100.4", "7.0",
            MARK_KLINE_CLOSE_MS, "700.0", 3, "1.0", "3.0", "0"]


def mark_snapshot_row() -> dict:
    return {"timestamp": OI_SNAPSHOT_MS, "markPrice": "100.25"}


# --------------------------------------------------------------------------- #
# 1. THE PIN: no read at T of a record with available_time_utc > T
# --------------------------------------------------------------------------- #
def test_pin_decision_at_T_never_reads_later_available_record(context):
    v1 = map_row("funding", funding_row(rate="0.0001"), context)
    v2 = map_row(
        "funding", funding_row(stamp_ms=FUNDING_SETTLE_LATE_MS, rate="0.0002"), context
    )
    assert v1.available_time_utc == FUNDING_SETTLE
    assert v2.available_time_utc == FUNDING_SETTLE_LATE

    # Before the first settlement exists at all: nothing is readable.
    assert select_asof([v1, v2], utc(2026, 1, 15, 7, 59, 59, 999000)) is None
    # At the midday decision the later settlement (16:00 > 12:00) MUST NOT be
    # readable; only the already-settled v1 is.
    winner = select_asof([v1, v2], DECISION_MID)
    assert winner is v1
    assert not v2.eligible_at(DECISION_MID)
    # Even with the later record sorted first, the pin holds.
    assert select_asof([v2, v1], DECISION_MID) is v1
    # Only once T reaches the later stamp does it become readable.
    assert select_asof([v1, v2], FUNDING_SETTLE_LATE) is v2


def test_pin_bar_record_unreadable_before_its_close_time(context):
    record = map_row("bars", bar_row(), context)
    assert record.available_time_utc == BAR_CLOSE
    assert not record.eligible_at(BAR_CLOSE - timedelta(microseconds=1))
    assert record.eligible_at(BAR_CLOSE)


def test_pin_over_snapshot_series_via_vintage_series(context):
    """As-of over a full funding series never surfaces a future settlement."""
    from research.data_fusion.pit import VintageSeries

    rows = [
        funding_row(stamp_ms=int(utc(2026, 1, 15, h).timestamp()) * 1_000, rate=f"0.000{h}")
        for h in (8, 16)
    ]
    records = map_rows("funding", rows, context)
    series = VintageSeries.started_by(records[0])
    for record in records[1:]:
        series = series.append(record)
    # Decision before the first staged settlement: nothing readable.
    assert series.select(utc(2026, 1, 15, 4)) is None
    # Midday decision: only the 08:00 settlement, never the 16:00 one.
    winner = series.select(DECISION_MID)
    assert winner.available_time_utc == utc(2026, 1, 15, 8)
    for record in records:
        if record.available_time_utc > DECISION_MID:
            assert not record.eligible_at(DECISION_MID)


# --------------------------------------------------------------------------- #
# 2. each authorized mapping carries the TRUE availability stamp class
# --------------------------------------------------------------------------- #
def test_bars_availability_is_bar_close_time(context):
    record = map_row("bars", bar_row(), context)
    assert AVAILABILITY_SEMANTICS["bars"] == "bar_close_time"
    assert record.available_time_utc == BAR_CLOSE
    assert record.event_time_utc == BAR_CLOSE
    assert record.dataset_id == "crypto_bars"
    assert record.field == "close"
    assert record.unit == "USDT"
    assert record.logical_key == ("crypto_bars", "BTCUSDT", "close")


def test_funding_availability_is_settlement_stamp(context):
    record = map_row("funding", funding_row(), context)
    assert AVAILABILITY_SEMANTICS["funding"] == "funding_settlement_stamp"
    assert record.available_time_utc == FUNDING_SETTLE
    assert record.event_time_utc == FUNDING_SETTLE
    assert record.field == "funding_rate"
    assert record.value == pytest.approx(0.0001)


def test_open_interest_availability_is_snapshot_stamp(context):
    for row in (oi_history_row(), oi_consolidated_row()):
        record = map_row("open_interest", row, context)
        assert AVAILABILITY_SEMANTICS["open_interest"] == "oi_snapshot_stamp"
        assert record.available_time_utc == OI_SNAPSHOT
        assert record.field == "open_interest"


def test_mark_price_availability_is_snapshot_stamp(context):
    assert AVAILABILITY_SEMANTICS["mark_price"] == "mark_snapshot_stamp"
    kline = map_row("mark_price", mark_kline_row(), context)
    # a kline snapshot is only complete at its close, never at its open
    assert kline.available_time_utc == MARK_KLINE_CLOSE
    assert kline.available_time_utc != utc(2026, 1, 15, 4, 0)
    direct = map_row("mark_price", mark_snapshot_row(), context)
    assert direct.available_time_utc == OI_SNAPSHOT


def test_retrieval_time_never_substitutes_for_availability(context):
    """A late retrieval must not move availability; an early one is refused."""
    very_late = CryptoCompatContext(
        symbol="BTCUSDT",
        retrieved_time_utc=utc(2027, 6, 1),
        raw_path="bars/x.parquet",
        raw_sha256=SYNTHETIC_SHA,
    )
    record = map_row("bars", bar_row(), very_late)
    assert record.available_time_utc == BAR_CLOSE
    assert record.retrieved_time_utc == utc(2027, 6, 1)
    early = CryptoCompatContext(
        symbol="BTCUSDT",
        retrieved_time_utc=utc(2026, 1, 15, 7),
        raw_path="funding/x.json",
        raw_sha256=SYNTHETIC_SHA,
    )
    with pytest.raises(CryptoCompatError, match="must never substitute"):
        map_row("funding", funding_row(), early)


def test_all_four_mappings_produce_valid_fusion_records(context):
    produced = {
        "bars": map_row("bars", bar_row(), context),
        "funding": map_row("funding", funding_row(), context),
        "open_interest": map_row("open_interest", oi_history_row(), context),
        "mark_price": map_row("mark_price", mark_kline_row(), context),
    }
    assert set(produced) == set(AUTHORIZED_DATASET_TYPES)
    for record in produced.values():
        assert isinstance(record, NormalizedRecord)
        assert record.available_time_utc <= record.retrieved_time_utc
        assert record.available_time_utc == record.event_time_utc
        assert record.canonical_bytes()


# --------------------------------------------------------------------------- #
# 3. unsupported dataset types are refused fail-closed
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad_type", ["liquidations", "taker_flow", "BARS", "Bars", "", None])
def test_unsupported_dataset_type_refused(context, bad_type):
    with pytest.raises(UnsupportedDatasetError, match="authorized types only"):
        map_row(bad_type, bar_row(), context)


def test_refusal_message_lists_exactly_the_authorized_four(context):
    with pytest.raises(UnsupportedDatasetError) as excinfo:
        map_row("orderbook", bar_row(), context)
    for name in sorted(AUTHORIZED_DATASET_TYPES):
        assert name in str(excinfo.value)


def test_map_rows_refuses_unknown_type_before_touching_rows(context):
    with pytest.raises(UnsupportedDatasetError):
        map_rows("not_a_dataset", [bar_row()], context)


# --------------------------------------------------------------------------- #
# 4. malformed rows and contexts are refused fail-closed
# --------------------------------------------------------------------------- #
def test_missing_funding_stamp_refused(context):
    with pytest.raises(CryptoCompatError, match="fundingTime"):
        map_row("funding", {"fundingRate": "0.0001"}, context)


def test_non_integral_epoch_refused(context):
    with pytest.raises(CryptoCompatError, match="integral"):
        map_row("funding", {"fundingTime": 1.5, "fundingRate": "0.0001"}, context)


def test_naive_consolidated_oi_stamp_refused(context):
    row = {"create_time": "2026-01-15 04:55:00", "sum_open_interest": 1.0}
    with pytest.raises(CryptoCompatError, match="naive"):
        map_row("open_interest", row, context)


def test_unknown_bar_field_refused(context):
    with pytest.raises(CryptoCompatError, match="unsupported bar field"):
        map_row("bars", bar_row(), context, field="count")


def test_mark_kline_too_short_refused(context):
    with pytest.raises(CryptoCompatError, match="7 elements"):
        map_row("mark_price", [MARK_OPEN_MS, "1", "2", "0.5", "1.0", "9"], context)


def test_lowercase_symbol_context_refused():
    with pytest.raises(CryptoCompatError, match="UPPERCASE"):
        CryptoCompatContext(
            symbol="btcusdt",
            retrieved_time_utc=RETRIEVED,
            raw_path="x.json",
            raw_sha256=SYNTHETIC_SHA,
        )
