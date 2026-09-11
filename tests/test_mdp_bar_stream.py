"""Tests for the mdp.market_bar@2 ordered stream (lane A4).

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
tests/test_mdp_bar_stream.py -q   (from the lane worktree root)

Covers: interval-disjointness fail-closed (overlap + duplicate + backwards
delivery), per-identity separation (raw vs adjusted never collide), stream
ordering, the available-time no-lookahead gate, gap accounting (completeness
GAPS_PRESENT with sorted gap reasons) and the replay_bars check toggles.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import bar_stream, bars, models  # noqa: E402

OPEN_NS = 1_700_000_100_000_000_000
INTERVAL_NS = 60_000_000_000
RAW_SHA = hashlib.sha256(b"raw0").hexdigest()
MANIFEST_SHA = hashlib.sha256(b"manifest0").hexdigest()


def bar_fields_at(index: int, **overrides) -> dict:
    open_ns = OPEN_NS + index * INTERVAL_NS
    fields = dict(
        schema_version=bars.SCHEMA_VERSION,
        source_id="SRC", provider_id="PROV", venue="VEN",
        instrument_id="BTCUSDT", asset_class="crypto_perpetual",
        bar_type="1m-LAST", interval_ns=INTERVAL_NS,
        open_time_utc_ns=open_ns,
        close_time_utc_ns=open_ns + INTERVAL_NS - 1_000_000,
        available_time_utc_ns=open_ns + INTERVAL_NS,
        open="26495.5", high="26500.0", low="26490.0", close="26498.5",
        volume="123.456", quote_volume="3274890.123", trade_count=812,
        taker_buy_base="61.728", taker_buy_quote="1637445.061",
        price_precision=1, size_precision=3,
        adjustment_mode="RAW",
        quality_status="VALID", reason_codes=[],
        raw_sha256=hashlib.sha256(f"raw{index}".encode()).hexdigest(),
        manifest_sha256=MANIFEST_SHA,
        normalizer_version="2",
    )
    fields.update(overrides)
    return fields


def bar_at(index: int, **overrides) -> dict:
    return bars.build_bar(bar_fields_at(index, **overrides))


# --- disjointness fail-closed ---------------------------------------------------


def test_duplicate_interval_fails_closed_not_quarantine():
    with pytest.raises(bars.BarIntervalError, match="BAR_INTERVAL_DUPLICATE"):
        bar_stream.normalize_bar_stream([bar_at(0), bar_at(0)])


def test_overlapping_interval_fails_closed():
    # second bar starts INSIDE the first interval (30s into the minute)
    overlap = bar_fields_at(0)
    overlap["open_time_utc_ns"] = OPEN_NS + 30_000_000_000
    overlap["close_time_utc_ns"] = OPEN_NS + 59_000_000_000
    overlap["available_time_utc_ns"] = OPEN_NS + 60_000_000_000
    with pytest.raises(bars.BarIntervalError, match="BAR_INTERVAL_OVERLAP"):
        bar_stream.normalize_bar_stream([bar_at(0), bars.build_bar(overlap)])


def test_backwards_delivery_fails_closed_ordering():
    with pytest.raises(bars.BarIntervalError, match="BAR_INTERVAL_OVERLAP"):
        bar_stream.normalize_bar_stream([bar_at(1), bar_at(0)])


def test_identity_separation_raw_vs_adjusted_never_collide():
    adjusted = bar_at(0, adjustment_mode="CORP_ACTION_ADJUSTED",
                      corporate_action_ref="corp://split/2026-06-09/4:1")
    result = bar_stream.normalize_bar_stream([bar_at(0), bars.build_bar(adjusted)])
    assert result["bar_count"] == 2
    other_instrument = bar_at(0, instrument_id="ETHUSDT")
    result = bar_stream.normalize_bar_stream([bar_at(0), other_instrument])
    assert result["bar_count"] == 2


def test_structurally_invalid_bar_fails_closed():
    broken = bar_fields_at(0)
    broken["high"] = "26400.0"  # high < low -> BAR_OHLC_ORDER_VIOLATION
    with pytest.raises(bars.BarError, match="BAR_OHLC_ORDER_VIOLATION"):
        bar_stream.normalize_bar_stream([bars.build_bar(broken)])


# --- no-lookahead available_time gate --------------------------------------------


def test_available_time_no_lookahead_gate_fail_closed():
    # bar 0 available late (legal: available >= close); bar 1 available at its
    # close (legal alone) — but EARLIER than bar 0's availability in the same
    # delivered stream: the stream could not have had that evidence.
    early_b1 = bar_fields_at(1)
    early_b1["available_time_utc_ns"] = OPEN_NS + INTERVAL_NS - 1_000_000
    with pytest.raises(bars.BarError, match="IMPOSSIBLE_TIME_ORDER"):
        bar_stream.normalize_bar_stream([
            bar_at(0, available_time_utc_ns=OPEN_NS + 200_000_000_000),
            bars.build_bar(early_b1),
        ])


def test_monotonic_availability_streams_clean():
    result = bar_stream.normalize_bar_stream([
        bar_at(0, available_time_utc_ns=OPEN_NS + 120_000_000_000),
        bar_at(1),
    ])
    assert result["completeness_status"] == "COMPLETE"


# --- gap accounting ---------------------------------------------------------------


def test_gap_accounting_gaps_present_with_sorted_reasons():
    result = bar_stream.normalize_bar_stream(
        [bar_at(i) for i in (0, 1, 3)])  # slot 2 missing
    assert result["completeness_status"] == "GAPS_PRESENT"
    assert result["gap_reasons"] == ["SEQUENCE_GAP"]
    assert len(result["gaps"]) == 1
    gap = result["gaps"][0]
    assert gap["missing_interval_count"] == 1
    assert gap["missing_open_time_utc_ns"] == OPEN_NS + 2 * INTERVAL_NS
    assert gap["instrument_id"] == "BTCUSDT"
    assert gap["adjustment_mode"] == "RAW"
    # multiple gaps keep reasons sorted and unique
    result = bar_stream.normalize_bar_stream([bar_at(i) for i in (0, 3, 6)])
    assert result["gap_reasons"] == ["SEQUENCE_GAP"]
    assert result["completeness_status"] == "GAPS_PRESENT"


def test_contiguous_stream_complete_and_digest_matches_canonical_bytes():
    stream = [bar_at(i) for i in (0, 1, 2)]
    result = bar_stream.normalize_bar_stream(stream)
    assert result["completeness_status"] == "COMPLETE"
    assert result["gap_reasons"] == []
    assert result["bar_count"] == 3
    assert result["stream_digest"] == hashlib.sha256(
        models.stream_bytes(result["bars"])).hexdigest()
    assert result["stream_byte_length"] == len(models.stream_bytes(stream))


def test_empty_stream_is_complete_vacuously():
    result = bar_stream.normalize_bar_stream([])
    assert result["bar_count"] == 0
    assert result["completeness_status"] == "COMPLETE"


# --- replay_bars --------------------------------------------------------------------


def test_replay_bars_default_checks_all_run():
    result = bar_stream.replay_bars([bar_at(i) for i in (0, 1, 2)])
    assert result["input_complete"] is True
    assert result["checks_run"] == bar_stream.DEFAULT_CHECKS
    assert result["checks_disabled"] == ()
    assert result["completeness_status"] == "COMPLETE"


def test_replay_bars_check_toggles_and_verbatim_recording():
    gapped = [bar_at(i) for i in (0, 2)]
    result = bar_stream.replay_bars(gapped, checks={"gap_accounting": False})
    assert "gap_accounting" in result["checks_disabled"]
    assert "gap_accounting" not in result["checks_run"]
    assert result["checks"] == {"gap_accounting": False}
    # a skipped gap accounting is NEVER reported as a silent COMPLETE
    assert result["completeness_status"] is None
    assert result["gap_reasons"] == []


def test_replay_bars_rejects_unknown_and_forced_checks():
    with pytest.raises(ValueError, match="unknown check"):
        bar_stream.replay_bars([], checks={"not_a_check": True})
    with pytest.raises(ValueError, match="structural_validation"):
        bar_stream.replay_bars([], checks={"structural_validation": False})
    with pytest.raises(ValueError, match="bool"):
        bar_stream.replay_bars([], checks={"ordering": "yes"})
    with pytest.raises(ValueError, match="dict"):
        bar_stream.replay_bars([], checks=["ordering"])
