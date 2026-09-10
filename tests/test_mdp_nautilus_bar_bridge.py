"""Tests for the nautilus 1.230.0 bar bridge (lane A4, mdp.market_bar@2).

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
tests/test_mdp_nautilus_bar_bridge.py -q   (from the lane worktree root)

Covers: the @1-event refusal (NotImplementedError with the frozen
BAR_NOT_MAPPED_IN_V1 message — bars are NOT mapped from mdp.market_event@1),
the additive @2 lossless-or-raise mapping to nautilus_trader 1.230.0 Bar
(hand-computed round trip at the declared precisions), the quality gate
(QUARANTINED refused; diagnostic-only exclude+record; SUSPECT streams only
with a recorded sidecar), the no-lookahead available-time gate, the uint64 ns
limit, the null NOT_EVALUABLE volume refusal (never zero), declared-vs-
instrument precision mismatch, derived/explicit nautilus BarType rules, and
the quote/trade paths rejecting bar-shaped input.
"""

from __future__ import annotations

import hashlib
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import bars, models  # noqa: E402
from market_data_plane import nautilus_bridge as nb  # noqa: E402
from nautilus_trader.model.data import Bar  # noqa: E402
from nautilus_trader.test_kit.providers import TestInstrumentProvider  # noqa: E402

OPEN_NS = 1_700_000_100_000_000_000
INTERVAL_NS = 900_000_000_000  # 15 minutes
CLOSE_NS = OPEN_NS + INTERVAL_NS - 1_000_000
AVAILABLE_NS = OPEN_NS + INTERVAL_NS
RAW_SHA = hashlib.sha256(b"raw0").hexdigest()
MANIFEST_SHA = hashlib.sha256(b"manifest0").hexdigest()

CRYPTO_INST = TestInstrumentProvider.btcusdt_perp_binance()  # price 1, size 3


def bar_fields(**overrides) -> dict:
    fields = dict(
        schema_version=bars.SCHEMA_VERSION,
        source_id="SRC", provider_id="PROV", venue="BINANCE",
        instrument_id="BTCUSDT-PERP.BINANCE", asset_class="crypto_perpetual",
        bar_type="15m-LAST", interval_ns=INTERVAL_NS,
        open_time_utc_ns=OPEN_NS,
        close_time_utc_ns=CLOSE_NS,
        available_time_utc_ns=AVAILABLE_NS,
        open="26495.5", high="26500.0", low="26490.0", close="26498.5",
        volume="123.456", quote_volume="3274890.123", trade_count=812,
        taker_buy_base="61.728", taker_buy_quote="1637445.061",
        price_precision=1, size_precision=3,
        adjustment_mode="RAW", corporate_action_ref=None,
        quality_status="VALID", reason_codes=[],
        raw_sha256=RAW_SHA, manifest_sha256=MANIFEST_SHA,
        normalizer_version="2",
    )
    fields.update(overrides)
    return fields


def canonical_bar(**overrides) -> dict:
    return bars.build_bar(bar_fields(**overrides))


# --- @1 events stay bar-free ------------------------------------------------------


def test_to_bar_refuses_market_event_inputs_with_frozen_message():
    event = models.build_event(dict(
        raw_id="r0", source_id="SRC", venue="VEN", instrument_id="INST",
        asset_class="crypto", event_type="TRADE",
        exchange_time_utc_ns=1, receive_time_utc_ns=2, available_time_utc_ns=3,
        sequence_number=0, price="10.0", quantity="1.0", side="buy",
        price_precision=1, size_precision=1,
        raw_sha256=hashlib.sha256(b"x").hexdigest(),
        manifest_sha256=hashlib.sha256(b"y").hexdigest(),
        normalizer_version="1"))
    with pytest.raises(NotImplementedError) as excinfo:
        nb.to_bar(event, CRYPTO_INST)
    assert str(excinfo.value) == nb.BAR_NOT_MAPPED_IN_V1
    assert nb.BAR_NOT_MAPPED_IN_V1 == (
        "mdp.market_event@1 has no BAR type; OHLCV can never become quotes/depth")


# --- lossless round trip at the declared precisions --------------------------------


def test_lossless_round_trip_hand_computed_bar_at_declared_precision():
    bar = canonical_bar()
    nautilus_bar = nb.to_bar(bar, CRYPTO_INST)
    assert isinstance(nautilus_bar, Bar)
    assert str(nautilus_bar.bar_type) == "BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    # every decimal renders exactly at the declared precision, no drift
    assert str(nautilus_bar.open) == format(Decimal("26495.5"), ".1f") == "26495.5"
    assert str(nautilus_bar.high) == format(Decimal("26500.0"), ".1f") == "26500.0"
    assert str(nautilus_bar.low) == format(Decimal("26490.0"), ".1f") == "26490.0"
    assert str(nautilus_bar.close) == format(Decimal("26498.5"), ".1f") == "26498.5"
    assert str(nautilus_bar.volume) == format(Decimal("123.456"), ".3f") == "123.456"
    assert Decimal(str(nautilus_bar.open)) == Decimal("26495.5")
    assert Decimal(str(nautilus_bar.volume)) == Decimal("123.456")
    # ts_event = bar completion (close), ts_init = availability (no lookahead)
    assert nautilus_bar.ts_event == CLOSE_NS
    assert nautilus_bar.ts_init == AVAILABLE_NS
    assert isinstance(nautilus_bar.ts_event, int)
    assert isinstance(nautilus_bar.ts_init, int)


def test_bar_type_explicit_string_and_object_override():
    bar = canonical_bar()
    from_str = nb.to_bar(bar, CRYPTO_INST,
                         bar_type="BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL")
    assert str(from_str.bar_type) == "BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    from_object = nb.to_bar(bar, CRYPTO_INST, bar_type=from_str.bar_type)
    assert str(from_object.bar_type) == str(from_str.bar_type)
    one_minute = canonical_bar(interval_ns=60_000_000_000,
                               bar_type="1m-LAST",
                               close_time_utc_ns=OPEN_NS + 60_000_000_000 - 1_000_000,
                               available_time_utc_ns=OPEN_NS + 60_000_000_000)
    assert str(nb.to_bar(one_minute, CRYPTO_INST).bar_type) == \
        "BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"
    half_second = canonical_bar(interval_ns=500_000_000,
                                bar_type="500ms-LAST",
                                close_time_utc_ns=OPEN_NS + 500_000_000 - 1,
                                available_time_utc_ns=OPEN_NS + 500_000_000)
    assert str(nb.to_bar(half_second, CRYPTO_INST).bar_type) == \
        "BTCUSDT-PERP.BINANCE-500-MILLISECOND-LAST-EXTERNAL"


def test_unrepresentable_interval_refused_never_rounded():
    with pytest.raises(nb.NautilusBridgeError, match="never rounds the interval"):
        nb.to_bar(canonical_bar(interval_ns=7, bar_type="7ns"), CRYPTO_INST)
    with pytest.raises(nb.NautilusBridgeError, match="representable"):
        # 90 s: no qualifying nautilus step (SECOND steps must divide 60)
        nb.to_bar(canonical_bar(interval_ns=90_000_000_000, bar_type="90s-LAST",
                                close_time_utc_ns=OPEN_NS + 90_000_000_000 - 1,
                                available_time_utc_ns=OPEN_NS + 90_000_000_000),
                  CRYPTO_INST)


# --- precision / identity fail-closed ------------------------------------------------


def test_declared_precision_mismatch_with_instrument_refused():
    # contract-legal 2dp bar, but the instrument trades at 1dp: refuse, never
    # re-render at a different precision
    bar = canonical_bar(price_precision=2, open="26495.55", high="26500.00",
                        low="26490.00", close="26498.55")
    with pytest.raises(nb.BridgePrecisionError, match="precision/identity"):
        nb.to_bar(bar, CRYPTO_INST)


def test_instrument_identity_mismatch_refused():
    from nautilus_trader.test_kit.providers import TestInstrumentProvider
    fx = TestInstrumentProvider.default_fx_ccy("EUR/USD")
    with pytest.raises(nb.NautilusBridgeError, match="instrument_id"):
        nb.to_bar(canonical_bar(), fx)


# --- quality gate ----------------------------------------------------------------------


def test_quarantined_bar_refused():
    bar = canonical_bar(quality_status="QUARANTINED")
    with pytest.raises(nb.BridgeQualityError, match="QUARANTINED"):
        nb.to_bar(bar, CRYPTO_INST)
    with pytest.raises(nb.NautilusBridgeError, match="never silent"):
        nb.to_bar(bar, CRYPTO_INST, diagnostic_only=True)


def test_quarantined_bar_diagnostic_only_excluded_and_recorded():
    bar = canonical_bar(quality_status="QUARANTINED",
                        reason_codes=["BAR_OHLC_ORDER_VIOLATION"])
    sink = nb.BridgeDiagnostics()
    assert nb.to_bar(bar, CRYPTO_INST, diagnostic_only=True,
                     diagnostics=sink) is None
    records = sink.by_action(nb.ACTION_REJECTED_EXCLUDED)
    assert len(records) == 1
    assert records[0].event_id == bar["bar_id"]
    assert records[0].event_type == bars.SCHEMA_VERSION
    assert records[0].quality_status == "QUARANTINED"
    assert tuple(records[0].reason_codes) == ("BAR_OHLC_ORDER_VIOLATION",)


def test_suspect_bar_streams_only_with_recorded_sidecar():
    bar = canonical_bar(quality_status="SUSPECT",
                        reason_codes=["BAR_OUTSIDE_CALENDAR"])
    with pytest.raises(nb.BridgeQualityError, match="sidecar"):
        nb.to_bar(bar, CRYPTO_INST)
    sink = nb.BridgeDiagnostics()
    streamed = nb.to_bar(bar, CRYPTO_INST, diagnostics=sink)
    assert streamed is not None
    records = sink.by_action(nb.ACTION_SUSPECT_STREAMED)
    assert len(records) == 1
    assert records[0].quality_status == "SUSPECT"
    assert records[0].event_id == bar["bar_id"]


# --- timestamps: no-lookahead + uint64 --------------------------------------------------


def test_available_time_before_close_refused_no_lookahead():
    mutated = dict(canonical_bar())
    mutated["available_time_utc_ns"] = mutated["close_time_utc_ns"] - 1
    with pytest.raises(nb.BridgeLookaheadError, match="no-lookahead"):
        nb.to_bar(mutated, CRYPTO_INST)


def test_negative_timestamps_refused_uint64_ns():
    for field in ("close_time_utc_ns", "available_time_utc_ns"):
        mutated = dict(canonical_bar())
        mutated[field] = -1
        with pytest.raises(nb.NautilusBridgeError, match="uint64"):
            nb.to_bar(mutated, CRYPTO_INST)


# --- null NOT_EVALUABLE volume: never zero ------------------------------------------------


def test_not_evaluable_volume_refused_never_substituted_with_zero():
    bar = canonical_bar(volume=None)
    assert bar["volume"] is None
    assert bar["completeness_status"] == "NOT_EVALUABLE"
    with pytest.raises(nb.NautilusBridgeError, match="never substitutes zero"):
        nb.to_bar(bar, CRYPTO_INST)
    # an explicitly reported zero-volume bar is provider evidence and streams
    zero = canonical_bar(volume="0.000", trade_count=0)
    assert str(nb.to_bar(zero, CRYPTO_INST).volume) == "0.000"


# --- input hygiene -------------------------------------------------------------------------


def test_non_dict_and_non_bar_inputs_refused():
    with pytest.raises(nb.NautilusBridgeError, match="mdp.market_bar@2"):
        nb.to_bar("not-a-dict", CRYPTO_INST)
    with pytest.raises(NotImplementedError):
        nb.to_bar({"schema_version": "something-else"}, CRYPTO_INST)


def test_quote_and_trade_paths_reject_bar_shaped_input():
    bar = canonical_bar()
    with pytest.raises(nb.NautilusBridgeError):
        nb.to_quote_tick(bar, CRYPTO_INST)
    with pytest.raises(nb.NautilusBridgeError):
        nb.to_trade_tick(bar, CRYPTO_INST)
    # and the mdp.market_event@1 validator itself rejects the bar dict
    with pytest.raises(models.MarketDataPlaneError):
        models.validate_event(bar)
