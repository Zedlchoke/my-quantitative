"""Tests for the crypto kline adapter (lane A5, MDP-V2, synthetic only).

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
tests/test_mdp_adapter_crypto.py -q   (from the lane worktree root)

Covers (mandatory A5 matrix): the happy-path kline -> mdp.market_bar@2
mapping with hand-computed nanosecond conversions and verbatim provider
decimal strings; ms->ns conversion EXACTLY ONCE (structural single-site pin
+ already-ns records fail closed); the frozen close-time rule (close =
open + interval - 1 ms, available = close); one-bar decision lag; unknown
instrument fail-closed; malformed-record quarantine with reason codes
(counted, never dropped); interval duplicate/overlap FAIL-CLOSED
(BarIntervalError); 24/7 gap accounting (interior drop -> GAPS_PRESENT);
the 1m->2m aggregation frozen boundary (refuses provider-native labeling);
and the decision-schedule leak guard (no PnL-family keys/values).

Hermetic: synthetic records only, no network, hand-computed expectations.
"""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import bars, models  # noqa: E402
from market_data_plane.adapters.crypto import kline  # noqa: E402

# --- hand-computed constants ---------------------------------------------------
# 1735689600000 ms = 2025-01-01T00:00:00Z; ns = ms * 1_000_000 (converted by
# hand here — the adapter's own helper is under test, not trusted).

T0_MS = 1_735_689_600_000
T0_NS = 1_735_689_600_000_000_000
MIN_MS = 60_000
INTERVAL_NS = 60_000_000_000
CLOSE_NS_T0 = T0_NS + INTERVAL_NS - 1_000_000  # 1735689659999000000
MANIFEST_SHA = hashlib.sha256(b"manifest-A5").hexdigest()

DENYLIST_RE = re.compile(r"pnl|profit|return|sharpe|drawdown|cost|fee",
                         re.IGNORECASE)

BASE_PRICES = dict(
    open="42000.00000000", high="42100.50000000", low="41950.25000000",
    close="42050.75000000", volume="123.45678900",
    quote_asset_volume="5187000.12345600", number_of_trades=152,
    taker_buy_base_volume="61.72839400",
    taker_buy_quote_volume="2593500.06172800",
)


def make_context(interval_ns=INTERVAL_NS, price_precision=8, size_precision=8,
                 symbols=("BTCUSDT",), **overrides) -> kline.AdapterContext:
    instruments = {
        symbol: kline.InstrumentSpec(
            symbol=symbol, price_precision=price_precision,
            size_precision=size_precision)
        for symbol in symbols
    }
    overrides.setdefault("manifest_sha256", MANIFEST_SHA)
    return kline.AdapterContext(
        instruments=instruments, interval_ns=interval_ns, **overrides)


def make_record(open_ms=T0_MS, symbol="BTCUSDT", **overrides) -> dict:
    record = dict(open_time=open_ms, **BASE_PRICES)
    # close_time derives from open_time unless supplied explicitly (already-ns
    # records override both)
    if "close_time" not in overrides:
        record["close_time"] = open_ms + MIN_MS - 1
    if symbol is not None:
        record["symbol"] = symbol
    record.update(overrides)
    return record


def make_records(count=5, symbol="BTCUSDT", **overrides) -> list[dict]:
    return [make_record(open_ms=T0_MS + k * MIN_MS, symbol=symbol, **overrides)
            for k in range(count)]


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


# --- namespace package import (PEP 420, no __init__.py) --------------------------


def test_namespace_package_import_without_init_py():
    import market_data_plane.adapters.crypto as pkg
    assert getattr(pkg, "__file__", None) is None  # PEP 420 namespace package
    assert kline.__file__.endswith(
        str(Path("market_data_plane") / "adapters" / "crypto" / "kline.py"))
    # the frozen interface is reachable exactly as the freeze prescribes
    for name in ("normalize_bar", "normalize_stream", "check_coverage",
                 "project_decision_schedule"):
        assert callable(getattr(kline, name))


# --- happy path: one kline -> exact bar dict ---------------------------------------


def test_happy_path_single_kline_exact_bar_dict():
    context = make_context()
    record = make_record()
    bar = kline.normalize_bar(record, context)

    # exact frozen bar field list, hand-verified ns conversions
    assert list(bar.keys()) == list(bars.BAR_FIELDS)
    assert bar["open_time_utc_ns"] == T0_NS
    assert bar["close_time_utc_ns"] == CLOSE_NS_T0
    assert bar["available_time_utc_ns"] == CLOSE_NS_T0
    assert bar["interval_ns"] == INTERVAL_NS
    assert bar["bar_type"] == "1m-LAST"

    # provider decimal strings preserved EXACTLY as passed (8dp fits the
    # declared precision 8 — no trailing-zero normalisation, no floats)
    assert bar["open"] == "42000.00000000"
    assert bar["high"] == "42100.50000000"
    assert bar["low"] == "41950.25000000"
    assert bar["close"] == "42050.75000000"
    assert bar["volume"] == "123.45678900"
    assert bar["quote_volume"] == "5187000.12345600"
    assert bar["trade_count"] == 152
    assert bar["taker_buy_base"] == "61.72839400"
    assert bar["taker_buy_quote"] == "2593500.06172800"

    # frozen crypto identity from the context table
    assert bar["venue"] == "BINANCE_USDM"
    assert bar["instrument_id"] == "BTCUSDT"
    assert bar["asset_class"] == "crypto_perpetual"
    assert bar["adjustment_mode"] == "RAW"
    assert bar["corporate_action_ref"] is None
    assert bar["completeness_status"] == "COMPLETE"
    assert bar["reason_codes"] == []
    assert bar["manifest_sha256"] == MANIFEST_SHA
    assert bar["normalizer_version"] == "2"
    assert bar["raw_id"] == bar["raw_sha256"]

    # raw_sha256 golden: sha256 of the canonical bytes of the record EXACTLY
    # as passed, recomputed here by hand (not via the adapter)
    expected_raw_sha = hashlib.sha256(canonical(record).encode("utf-8")).hexdigest()
    assert bar["raw_sha256"] == expected_raw_sha

    # bar_id golden: sha256 of the canonical frozen identity tuple
    identity = {
        "schema_version": "mdp.market_bar@2",
        "source_id": "binance_usdm_kline",
        "provider_id": "BINANCE",
        "venue": "BINANCE_USDM",
        "instrument_id": "BTCUSDT",
        "asset_class": "crypto_perpetual",
        "bar_type": "1m-LAST",
        "interval_ns": INTERVAL_NS,
        "open_time_utc_ns": T0_NS,
        "adjustment_mode": "RAW",
    }
    expected_bar_id = hashlib.sha256(canonical(identity).encode("utf-8")).hexdigest()
    assert bar["bar_id"] == expected_bar_id

    # the bar is canonical: re-validates idempotently, input never mutated
    assert bars.validate_bar(bar) == bar
    assert record["open_time"] == T0_MS  # untouched


def test_provider_decimal_strings_survive_verbatim_eighth_decimals():
    # '0.00347000' must stay EXACTLY '0.00347000' at declared precision 8
    context = make_context()
    record = make_record(
        open="0.00347000", high="0.00348000", low="0.00346000",
        close="0.00347500", volume="1000.00000000",
        quote_asset_volume="3.47100000", taker_buy_base_volume="500.00000000",
        taker_buy_quote_volume="1.73550000")
    bar = kline.normalize_bar(record, context)
    assert bar["open"] == "0.00347000"
    assert bar["volume"] == "1000.00000000"
    # precision beyond the declaration is BAR_PRECISION_LOSS (fail closed)
    with pytest.raises(bars.BarError, match="BAR_PRECISION_LOSS"):
        kline.normalize_bar(make_record(close="42050.750000001"), context)


def test_raw_bytes_rule_is_key_order_independent_and_exact():
    context = make_context()
    record = make_record()
    reordered = {key: record[key] for key in reversed(list(record.keys()))}
    bar_a = kline.normalize_bar(record, context)
    bar_b = kline.normalize_bar(reordered, context)
    assert bar_a["raw_sha256"] == bar_b["raw_sha256"]
    assert bar_a["bar_id"] == bar_b["bar_id"]
    expected = hashlib.sha256(canonical(record).encode("utf-8")).hexdigest()
    assert bar_a["raw_sha256"] == expected


# --- ms -> ns conversion EXACTLY ONCE -----------------------------------------------


def test_ms_to_ns_conversion_happens_exactly_once_structural_and_behavioral():
    source = inspect.getsource(kline)
    # exactly one conversion literal in the whole module: the frozen constant
    assert source.count("1_000_000") == 1
    helper_source = inspect.getsource(kline._ms_to_ns)
    assert "* _MS_TO_NS" in helper_source  # the only multiplication site
    # no conversion literal may hide inside the mapping/coverage/schedule code
    for fn in (kline.normalize_bar, kline.normalize_stream, kline.check_coverage,
               kline.project_decision_schedule, kline.aggregate_bars):
        assert "1_000_000" not in inspect.getsource(fn)

    # behavioral: an ALREADY-CONVERTED nanosecond record fails closed instead
    # of being double-scaled
    context = make_context()
    ns_record = make_record(
        open_ms=None, open_time=T0_NS,
        close_time=T0_NS + INTERVAL_NS - 1_000_000)
    with pytest.raises(bars.BarError, match="IMPOSSIBLE_TIME_ORDER"):
        kline.normalize_bar(ns_record, context)
    with pytest.raises(bars.BarError, match="IMPOSSIBLE_TIME_ORDER"):
        kline.normalize_bar(make_record(close_time=T0_NS), context)
    # non-integer epochs fail closed too
    with pytest.raises(bars.BarError, match="MALFORMED_SHAPE"):
        kline.normalize_bar(make_record(open_time="1735689600000"), context)
    with pytest.raises(bars.BarError, match="MALFORMED_SHAPE"):
        kline.normalize_bar(make_record(open_time=1735689600000.0), context)


# --- close-time rule, availability, and the interval clock ---------------------------


def test_close_time_rule_available_equals_close_and_grid_alignment():
    interval_15m = 15 * INTERVAL_NS
    context = make_context(interval_ns=interval_15m)
    bar = kline.normalize_bar(make_record(close_time=T0_MS + 899_999), context)
    assert bar["close_time_utc_ns"] == T0_NS + interval_15m - 1_000_000
    assert bar["available_time_utc_ns"] == bar["close_time_utc_ns"]
    # a record close_time disagreeing with the frozen rule fails closed
    with pytest.raises(bars.BarError, match="IMPOSSIBLE_TIME_ORDER"):
        kline.normalize_bar(make_record(close_time=T0_MS + MIN_MS - 2), context)
    with pytest.raises(bars.BarError, match="IMPOSSIBLE_TIME_ORDER"):
        kline.normalize_bar(make_record(close_time=T0_MS + MIN_MS), context)
    # kline opens are interval-grid multiples; a misaligned open fails closed
    with pytest.raises(bars.BarError, match="aligned to the"):
        kline.normalize_bar(
            make_record(open_ms=T0_MS + 30_000,
                        close_time=T0_MS + 30_000 + MIN_MS - 1), context)
    # the context pins the CLOSE_TIME availability rule and refuses others
    assert kline.AVAILABILITY_CLOSE_TIME == "CLOSE_TIME"
    with pytest.raises(bars.BarError, match="CLOSE_TIME"):
        make_context(availability_rule="PUBLICATION_LAG")
    with pytest.raises(bars.BarError, match="hex sha256"):
        make_context(manifest_sha256="not-a-sha")
    with pytest.raises(bars.BarError, match="int > 0"):
        make_context(interval_ns=0)


# --- unknown instrument fails closed; malformed records quarantined ------------------


def test_unknown_symbol_fails_closed():
    context = make_context(symbols=("BTCUSDT",))
    with pytest.raises(bars.BarError, match="UNKNOWN_INSTRUMENT"):
        kline.normalize_bar(make_record(symbol="ETHUSDT"), context)
    # in a stream the same failure is quarantined with the frozen code and
    # counted — never silently dropped
    result = kline.normalize_stream(
        [make_record(), make_record(open_ms=T0_MS + MIN_MS, symbol="ETHUSDT")],
        context)
    assert result.total_count == 2
    assert result.accepted_count == 1
    assert result.quarantined_count == 1
    assert result.quarantined[0]["reason_code"] == "UNKNOWN_INSTRUMENT"
    assert result.quarantined[0]["instrument_id"] == "ETHUSDT"
    assert result.quarantined[0]["input_index"] == 1
    assert result.quarantined[0]["raw_sha256"] is not None
    assert len(result.bars) == 1


def test_malformed_records_quarantined_with_reason_codes_counted_not_dropped():
    context = make_context()
    records = make_records(count=3)
    del records[1]["high"]                                # missing field
    records[2]["stray_field"] = "nope"                    # unknown field
    result = kline.normalize_stream(records, context)
    assert result.total_count == 3
    assert result.accepted_count == 1
    assert result.quarantined_count == 2
    codes = [entry["reason_code"] for entry in result.quarantined]
    assert codes == ["MISSING_REQUIRED_FIELD", "MALFORMED_SHAPE"]
    for entry in result.quarantined:
        assert entry["message"]
        assert entry["input_index"] in (1, 2)
    # float prices are refused by the bar model (no floats in the bar model)
    float_result = kline.normalize_stream(
        [make_record(open=42000.5)], context)
    assert float_result.quarantined_count == 1
    assert float_result.quarantined[0]["reason_code"] == "MALFORMED_SHAPE"
    assert float_result.accepted_count == 0
    # a non-mapping record is quarantined, not fatal
    junk = kline.normalize_stream([make_record(), "not-a-record"], context)
    assert junk.accepted_count == 1
    assert junk.quarantined[0]["reason_code"] == "MALFORMED_SHAPE"
    # input order is preserved in the accepted bars
    ordered = kline.normalize_stream(make_records(count=3), context)
    assert [b["open_time_utc_ns"] for b in ordered.bars] == \
        [T0_NS + k * INTERVAL_NS for k in range(3)]


def test_multi_symbol_context_without_envelope_is_ambiguous():
    context = make_context(symbols=("BTCUSDT", "ETHUSDT"))
    with pytest.raises(bars.BarError, match="MISSING_REQUIRED_FIELD"):
        kline.normalize_bar(make_record(symbol=None), context)


# --- duplicates / overlaps FAIL CLOSED (BarIntervalError) -----------------------------


def test_duplicate_kline_fails_closed_with_bar_interval_error():
    context = make_context()
    records = [make_record(), make_record()]  # same open_time twice
    with pytest.raises(bars.BarIntervalError, match="BAR_INTERVAL_DUPLICATE"):
        kline.normalize_stream(records, context)


def test_overlapping_kline_fails_closed_with_bar_interval_error():
    context = make_context()
    # a mid-interval open is structurally impossible for grid-aligned
    # klines: the per-record alignment check quarantines it (MALFORMED_SHAPE)
    # before the stream sees it — fail closed, never admitted
    misaligned = kline.normalize_stream(
        [make_record(),
         make_record(open_ms=T0_MS + 30_000,
                     close_time=T0_MS + 30_000 + MIN_MS - 1)], context)
    assert misaligned.accepted_count == 1
    assert misaligned.quarantined[0]["reason_code"] == "MALFORMED_SHAPE"
    # backwards delivery inside the same identity is BAR_INTERVAL_OVERLAP
    # (fail closed at stream level, never quarantine)
    with pytest.raises(bars.BarIntervalError, match="BAR_INTERVAL_OVERLAP"):
        kline.normalize_stream(
            [make_record(open_ms=T0_MS + MIN_MS), make_record()], context)
    # a non-grid duplicate of the interval clock fails closed as well
    with pytest.raises(bars.BarIntervalError, match="BAR_INTERVAL_OVERLAP"):
        kline.normalize_stream(
            [make_record(open_ms=T0_MS + 2 * MIN_MS),
             make_record(open_ms=T0_MS + MIN_MS)], context)


# --- 24/7 gap accounting ----------------------------------------------------------------


def test_interior_drop_produces_gap_and_gaps_present_completeness():
    context = make_context()
    records = make_records(count=5)
    del records[2]  # drop the interior kline at T0 + 2m
    result = kline.normalize_stream(records, context)
    assert result.accepted_count == 4
    assert result.total_count == 4
    assert result.quarantined_count == 0
    assert result.completeness_status == "GAPS_PRESENT"
    assert result.gap_reasons == ("SEQUENCE_GAP",)
    assert len(result.gaps) == 1
    assert result.gaps[0]["instrument_id"] == "BTCUSDT"
    assert result.gaps[0]["missing_open_time_utc_ns"] == T0_NS + 2 * INTERVAL_NS
    assert result.gaps[0]["missing_interval_count"] == 1


def test_check_coverage_continuous_247_expected_slots_and_classification():
    context = make_context()

    # complete 5-bar window: expected == observed, no gaps
    full = kline.normalize_stream(make_records(count=5), context)
    report = kline.check_coverage(full, context)
    assert report.calendar == "CONTINUOUS_24_7"
    assert report.interval_ns == INTERVAL_NS
    assert report.expected_slots == 5
    assert report.observed_bars == 5
    assert report.completeness_status == "COMPLETE"
    assert report.unexplained_missing_slots == 0
    assert report.gap_count == 0
    assert report.duplicate_count == 0  # structurally impossible upstream
    assert "fail closed" in report.duplicate_invariant
    row = report.instrument_reports[0]
    assert row.first_open_time_utc_ns == T0_NS
    assert row.last_open_time_utc_ns == T0_NS + 4 * INTERVAL_NS

    # interior drop: one UNEXPLAINED missing slot
    dropped = make_records(count=5)
    del dropped[2]
    dropped_result = kline.normalize_stream(dropped, context)
    dropped_report = kline.check_coverage(dropped_result, context)
    assert dropped_report.expected_slots == 5
    assert dropped_report.observed_bars == 4
    assert dropped_report.unexplained_missing_slots == 1
    assert dropped_report.explained_missing_slots == 0
    assert dropped_report.completeness_status == "GAPS_PRESENT"

    # quarantined record on a slot: the gap is quarantine-EXPLAINED
    strict = make_context(price_precision=2)
    precise = make_records(count=5, close="42050.75", open="42000.00",
                           high="42100.50", low="41950.25")
    precise[2] = make_record(open_ms=T0_MS + 2 * MIN_MS, close="42050.755",
                             open="42000.00", high="42100.50",
                             low="41950.25")  # 3dp at declared precision 2
    strict_result = kline.normalize_stream(precise, strict)
    assert strict_result.quarantined_count == 1
    assert strict_result.quarantined[0]["reason_code"] == "BAR_PRECISION_LOSS"
    assert strict_result.quarantined[0]["open_time_utc_ns"] == \
        T0_NS + 2 * INTERVAL_NS
    strict_report = kline.check_coverage(strict_result, strict)
    assert strict_report.expected_slots == 5
    assert strict_report.observed_bars == 4
    assert strict_report.explained_missing_slots == 1
    assert strict_report.unexplained_missing_slots == 0
    assert strict_report.quarantined_records == 1
    assert strict_report.completeness_status == "GAPS_PRESENT"

    # empty stream coverage is vacuously complete, never a silent claim
    empty = kline.normalize_stream([], context)
    empty_report = kline.check_coverage(empty, context)
    assert empty_report.expected_slots == 0
    assert empty_report.observed_bars == 0
    assert empty_report.completeness_status == "COMPLETE"


# --- 1m -> 2m aggregation (frozen boundary; provider-native NOT claimed) ----------------


def _agg_source_bars(context):
    r0 = make_record(
        open="100.00000000", high="101.00000000", low="99.50000000",
        close="100.50000000", volume="1.50000000",
        quote_asset_volume="151.50000000", number_of_trades=10,
        taker_buy_base_volume="0.60000000",
        taker_buy_quote_volume="60.60000000")
    r1 = make_record(
        open_ms=T0_MS + MIN_MS, close_time=T0_MS + MIN_MS + MIN_MS - 1,
        open="100.50000000", high="102.00000000", low="100.00000000",
        close="101.50000000", volume="2.00000000",
        quote_asset_volume="203.50000000", number_of_trades=15,
        taker_buy_base_volume="1.10000000",
        taker_buy_quote_volume="111.60000000")
    return [kline.normalize_bar(r0, context),
            kline.normalize_bar(r1, context)], [r0, r1]


def test_aggregate_1m_to_2m_from_two_complete_adjacent_bars():
    context = make_context()
    source, _ = _agg_source_bars(context)
    agg = kline.aggregate_bars(
        source, 2 * INTERVAL_NS, context,
        derived_label=kline.DERIVED_PROVENANCE_LABEL)
    assert len(agg) == 1
    bar = agg[0]
    # frozen boundary: the 2m window [T0, T0+2m) from EXACTLY bars T0, T0+1m
    assert bar["open_time_utc_ns"] == T0_NS
    assert bar["close_time_utc_ns"] == T0_NS + 2 * INTERVAL_NS - 1_000_000
    assert bar["available_time_utc_ns"] == bar["close_time_utc_ns"]
    assert bar["interval_ns"] == 2 * INTERVAL_NS
    assert bar["bar_type"] == "2m-LAST"
    # hand-computed OHLC + exact decimal sums (provider strings preserved)
    assert bar["open"] == "100.00000000"
    assert bar["high"] == "102.00000000"
    assert bar["low"] == "99.50000000"
    assert bar["close"] == "101.50000000"
    assert bar["volume"] == "3.50000000"
    assert bar["quote_volume"] == "355.00000000"
    assert bar["trade_count"] == 25
    assert bar["taker_buy_base"] == "1.70000000"
    assert bar["taker_buy_quote"] == "172.20000000"
    # derived identity: raw_sha256 = sha256(canonical stream bytes of sources)
    expected_raw = hashlib.sha256(
        models.stream_bytes(list(source))).hexdigest()
    assert bar["raw_sha256"] == expected_raw
    assert bar["normalizer_version"] == "2+agg"  # in-band derived labeling
    assert bars.validate_bar(bar) == bar
    # the aggregated stream itself passes stream normalization
    from market_data_plane import bar_stream
    agg_stream = bar_stream.normalize_bar_stream(agg)
    assert agg_stream["completeness_status"] == "COMPLETE"


def test_aggregation_refuses_to_be_labeled_provider_native():
    context = make_context()
    source, _ = _agg_source_bars(context)
    for bad_label in ("PROVIDER_NATIVE", "binance", "",
                      kline.DERIVED_PROVENANCE_LABEL.lower()):
        with pytest.raises(bars.BarError, match="provider-native"):
            kline.aggregate_bars(source, 2 * INTERVAL_NS, context,
                                 derived_label=bad_label)
    # non-multiple / non-increasing targets refuse too
    with pytest.raises(bars.BarError, match="exact integer multiple"):
        kline.aggregate_bars(source, INTERVAL_NS, context,
                             derived_label=kline.DERIVED_PROVENANCE_LABEL)
    with pytest.raises(bars.BarError, match="exact integer multiple"):
        kline.aggregate_bars(source, 90 * 1_000_000_000, context,
                             derived_label=kline.DERIVED_PROVENANCE_LABEL)


def test_aggregation_incomplete_window_fails_closed_sequence_gap():
    context = make_context()
    records = make_records(count=3)
    bars3 = [kline.normalize_bar(r, context) for r in records]
    label = kline.DERIVED_PROVENANCE_LABEL
    # trailing lone bar cannot form a 2m window -> fail closed
    with pytest.raises(bars.BarError, match="SEQUENCE_GAP"):
        kline.aggregate_bars(bars3, 2 * INTERVAL_NS, context, derived_label=label)
    # a hole inside the window -> fail closed
    with pytest.raises(bars.BarError, match="SEQUENCE_GAP"):
        kline.aggregate_bars([bars3[0], bars3[2]], 2 * INTERVAL_NS, context,
                             derived_label=label)


# --- decision schedule: EXACTLY ONE completed-bar lag, schedule only -------------------


def test_decision_schedule_five_bars_four_rows_exact_one_bar_lag():
    context = make_context()
    result = kline.normalize_stream(make_records(count=5), context)
    rows = kline.project_decision_schedule(result, context)
    assert len(rows) == 4  # 5 bars -> 4 decision rows
    for i, row in enumerate(rows):
        ref_close = T0_NS + i * INTERVAL_NS + INTERVAL_NS - 1_000_000
        assert row["decision_utc_ns"] == ref_close  # decision at bar i close
        assert row["instrument_id"] == "BTCUSDT"
        assert row["reference_bar_open_time_utc_ns"] == T0_NS + i * INTERVAL_NS
        assert row["reference_bar_close_time_utc_ns"] == ref_close
        assert row["reference_bar_available_time_utc_ns"] == ref_close
        # the forward bar closes strictly after the decision (no lookahead)
        assert ref_close < T0_NS + (i + 2) * INTERVAL_NS - 1_000_000
        assert row["schedule_target"] == kline.SCHEDULE_TARGET_PLACEHOLDER
        assert row["schedule_signal"] == kline.SCHEDULE_SIGNAL_PLACEHOLDER
        assert kline.SCHEDULE_TARGET_PLACEHOLDER == "SCHEDULE_TARGET_PLACEHOLDER"
    # 1 bar -> 0 rows; empty -> 0 rows
    single = kline.normalize_stream(make_records(count=1), context)
    assert kline.project_decision_schedule(single, context) == []
    assert kline.project_decision_schedule(
        kline.normalize_stream([], context), context) == []


def test_decision_schedule_leak_guard_no_pnl_family_keys_or_values():
    context = make_context()
    result = kline.normalize_stream(make_records(count=5), context)
    rows = kline.project_decision_schedule(result, context)
    assert rows
    allowed_keys = {
        "decision_utc_ns", "instrument_id",
        "reference_bar_open_time_utc_ns", "reference_bar_close_time_utc_ns",
        "reference_bar_available_time_utc_ns",
        "schedule_target", "schedule_signal",
    }
    for row in rows:
        assert set(row.keys()) == allowed_keys
        for key, value in row.items():
            assert not DENYLIST_RE.search(key)
            # no numeric quantity beyond timestamps/ids/constants:
            # values are exact ints (timestamps) or declared constant strings
            assert isinstance(value, (int, str))
            assert not isinstance(value, bool)
            assert not isinstance(value, float)
        if isinstance(row["instrument_id"], str):
            assert not DENYLIST_RE.search(row["instrument_id"])
        for name in ("schedule_target", "schedule_signal"):
            assert not DENYLIST_RE.search(row[name])


# --- context / spec frozenness and identity assertion -----------------------------------


def test_context_and_spec_are_frozen_and_fail_closed():
    context = make_context()
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.interval_ns = INTERVAL_NS * 2
    spec = kline.InstrumentSpec(symbol="BTCUSDT", price_precision=8,
                                size_precision=8)
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.price_precision = 2
    # frozen crypto identity asserted at construction
    with pytest.raises(bars.BarError, match="BINANCE_USDM"):
        kline.InstrumentSpec(symbol="BTCUSDT", price_precision=8,
                             size_precision=8, venue="BINANCE_SPOT")
    with pytest.raises(bars.BarError, match="crypto_perpetual"):
        kline.InstrumentSpec(symbol="BTCUSDT", price_precision=8,
                             size_precision=8, asset_class="crypto_spot")
    with pytest.raises(bars.BarError, match="int >= 1"):
        kline.InstrumentSpec(symbol="BTCUSDT", price_precision=0, size_precision=8)
    # an instrument table entry that is not an InstrumentSpec fails closed
    with pytest.raises(bars.BarError, match="InstrumentSpec"):
        kline.AdapterContext(
            instruments={"BTCUSDT": "not-a-spec"}, interval_ns=INTERVAL_NS,
            manifest_sha256=MANIFEST_SHA)
    # schedule placeholders are declared constants
    assert kline.SCHEDULE_TARGET_PLACEHOLDER != kline.SCHEDULE_SIGNAL_PLACEHOLDER
