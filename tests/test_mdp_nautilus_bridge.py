"""Tests for the MDP-V1 nautilus bridge (lane A8, frozen mapping).

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
tests/test_mdp_nautilus_bridge.py tests/test_mdp_models.py -q   (lane worktree)

Covers the frozen nautilus_bridge_contract: lossless decimal round-trips
(goldens over every fixture event), exact ns timestamp mapping, the quality
gate (INVALID/QUARANTINED raise or diagnostic-only exclude+record; SUSPECT
streams only with a recorded sidecar), no-lookahead, BAR_NOT_MAPPED_IN_V1,
cross-asset fixture conversion, and nautilus_trader import isolation.
"""

from __future__ import annotations

import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from market_data_plane import models  # noqa: E402
from market_data_plane import nautilus_bridge as nb  # noqa: E402
from mdp_bridge_fixtures import (  # noqa: E402
    crypto_trades,
    forex_quotes,
    stocks_trades_quotes,
)

PYTHON = sys.executable
RESEARCH_DIR = Path(__file__).resolve().parents[1] / "research"


# --- nautilus instruments (lazy: only tests import nautilus_trader eagerly) --


def _instruments():
    from decimal import Decimal

    from nautilus_trader.model.currencies import USD
    from nautilus_trader.model.enums import AssetClass
    from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
    from nautilus_trader.model.instruments.cfd import Cfd
    from nautilus_trader.model.objects import Price, Quantity
    from nautilus_trader.test_kit.providers import TestInstrumentProvider

    crypto = TestInstrumentProvider.btcusdt_perp_binance()
    fx = TestInstrumentProvider.default_fx_ccy("EUR/USD")
    stock = Cfd(
        InstrumentId(Symbol("AAPL"), Venue("XNAS")), Symbol("AAPL"),
        AssetClass.EQUITY, USD,
        stocks_trades_quotes.PRICE_PRECISION,
        stocks_trades_quotes.SIZE_PRECISION,
        Price(Decimal("0.01"), stocks_trades_quotes.PRICE_PRECISION),
        Quantity(Decimal("0.1"), stocks_trades_quotes.SIZE_PRECISION),
        0, 0,
    )
    return crypto, fx, stock


CRYPTO_INST, FX_INST, STOCK_INST = _instruments()


# --- fixture legality --------------------------------------------------------

def test_fixtures_are_contract_legal_27_field_envelopes():
    for module in (crypto_trades, forex_quotes, stocks_trades_quotes):
        events = module.events()
        assert len(events) >= 20
        for event in events:
            assert set(event.keys()) == set(models.ENVELOPE_FIELDS)
            assert len(event) == 27
            # models.validate_event recomputation is the contract check
            assert models.validate_event(event) == event


def test_fixture_instrument_metadata_matches_nautilus_instruments():
    for module, instrument in ((crypto_trades, CRYPTO_INST),
                               (forex_quotes, FX_INST),
                               (stocks_trades_quotes, STOCK_INST)):
        meta = module.instrument_metadata()
        assert meta["instrument_id"] == str(instrument.id)
        assert meta["price_precision"] == instrument.price_precision
        assert meta["size_precision"] == instrument.size_precision
        assert meta["data_authority"].startswith("NONE")


# --- round-trip precision goldens (every fixture event) ----------------------

# SUSPECT events stream ONLY with a recorded sidecar (freeze), so every
# streaming conversion in these tests passes an explicit BridgeDiagnostics sink.


def _assert_decimal_round_trip(obj, event_value: str, precision: int,
                               field: str, event_id: str) -> None:
    # str(Price/Quantity) is the fixed-point expansion at the given precision
    rendered = str(obj)
    expected = format(Decimal(event_value), f".{precision}f")
    assert rendered == expected, (field, event_id, rendered, expected)
    # and the exact Decimal value survives (no binary-float artefacts)
    assert Decimal(rendered) == Decimal(event_value)


def test_golden_crypto_trade_round_trip_exact_strings():
    for event in crypto_trades.events():
        tick = nb.to_trade_tick(event, CRYPTO_INST,
                                diagnostics=nb.BridgeDiagnostics())
        _assert_decimal_round_trip(
            tick.price, event["price"], CRYPTO_INST.price_precision,
            "price", event["event_id"])
        _assert_decimal_round_trip(
            tick.size, event["quantity"], CRYPTO_INST.size_precision,
            "quantity", event["event_id"])


def test_golden_forex_quote_round_trip_exact_strings():
    for event in forex_quotes.events():
        tick = nb.to_quote_tick(event, FX_INST,
                                diagnostics=nb.BridgeDiagnostics())
        for obj_field, event_field in (
                (tick.bid_price, "bid_price"), (tick.ask_price, "ask_price"),
                (tick.bid_size, "bid_size"), (tick.ask_size, "ask_size")):
            precision = (FX_INST.price_precision
                         if event_field.endswith("price") else
                         FX_INST.size_precision)
            _assert_decimal_round_trip(
                obj_field, event[event_field], precision,
                event_field, event["event_id"])


def test_golden_stock_trades_and_quotes_round_trip_exact_strings():
    for event in stocks_trades_quotes.events():
        sink = nb.BridgeDiagnostics()
        if event["event_type"] == "TRADE":
            tick = nb.to_trade_tick(event, STOCK_INST, diagnostics=sink)
            pairs = ((tick.price, "price", STOCK_INST.price_precision),
                     (tick.size, "quantity", STOCK_INST.size_precision))
        else:
            tick = nb.to_quote_tick(event, STOCK_INST, diagnostics=sink)
            pairs = ((tick.bid_price, "bid_price", STOCK_INST.price_precision),
                     (tick.ask_price, "ask_price", STOCK_INST.price_precision),
                     (tick.bid_size, "bid_size", STOCK_INST.size_precision),
                     (tick.ask_size, "ask_size", STOCK_INST.size_precision))
        for obj, field, precision in pairs:
            _assert_decimal_round_trip(obj, event[field], precision, field,
                                       event["event_id"])


def test_precision_drift_at_instrument_precision_raises_never_rounds():
    # event-legal (2dp) but not representable at the instrument's 1dp price
    event = dict(crypto_trades.events()[0])
    event["price_precision"] = 2
    event["price"] = "26500.25"
    event.pop("event_id")  # identity is re-derived for the mutated copy
    event = models.validate_event(event)
    with pytest.raises(nb.BridgePrecisionError, match="never rounds silently"):
        nb.to_trade_tick(event, CRYPTO_INST)


def test_trailing_zero_beyond_precision_is_losslessly_normalised():
    # '26500.20' at event precision 2 -> '26500.2' at instrument precision 1
    event = dict(crypto_trades.events()[0])
    event["price_precision"] = 2
    event["price"] = "26500.20"
    event.pop("event_id")
    event = models.validate_event(event)
    tick = nb.to_trade_tick(event, CRYPTO_INST)
    assert str(tick.price) == "26500.2"


# --- timestamp mapping exactness --------------------------------------------

def test_timestamp_mapping_exact_ns_and_no_now():
    for module, quote_instrument, trade_instrument in (
            (crypto_trades, None, CRYPTO_INST),
            (forex_quotes, FX_INST, None),
            (stocks_trades_quotes, STOCK_INST, STOCK_INST)):
        for event in module.events():
            sink = nb.BridgeDiagnostics()
            if event["event_type"] == "QUOTE":
                tick = nb.to_quote_tick(event, quote_instrument,
                                        diagnostics=sink)
            else:
                tick = nb.to_trade_tick(event, trade_instrument,
                                        diagnostics=sink)
            assert isinstance(tick.ts_event, int)
            assert isinstance(tick.ts_init, int)
            assert tick.ts_event == event["exchange_time_utc_ns"]
            assert tick.ts_init == event["available_time_utc_ns"]


# --- quality gate ------------------------------------------------------------


def test_invalid_and_quarantined_raise_without_diagnostic_only():
    # (event, matching instrument) pairs — the gate fires before any
    # instrument-identity complaint is even reachable for a matching pair.
    bad = [(crypto_trades.invalid_event(), CRYPTO_INST),
           (crypto_trades.quarantined_event(), CRYPTO_INST),
           (forex_quotes.invalid_event(), FX_INST),
           (forex_quotes.quarantined_event(), FX_INST),
           (stocks_trades_quotes.invalid_event(), STOCK_INST),
           (stocks_trades_quotes.quarantined_event(), STOCK_INST)]
    for event, instrument in bad:
        mapper = nb.to_quote_tick if event["event_type"] == "QUOTE" \
            else nb.to_trade_tick
        with pytest.raises(nb.BridgeQualityError,
                           match=event["quality_status"]):
            mapper(event, instrument)
        with pytest.raises(nb.BridgeQualityError):
            nb.convert_stream([event], instrument)


def test_invalid_and_quarantined_diagnostic_only_excluded_and_recorded():
    for event, instrument in ((crypto_trades.invalid_event(), CRYPTO_INST),
                              (crypto_trades.quarantined_event(), CRYPTO_INST),
                              (forex_quotes.invalid_event(), FX_INST),
                              (stocks_trades_quotes.quarantined_event(),
                               STOCK_INST)):
        sink = nb.BridgeDiagnostics()
        result = nb.to_trade_tick(event, instrument, diagnostic_only=True,
                                  diagnostics=sink) if \
            event["event_type"] == "TRADE" else \
            nb.to_quote_tick(event, instrument, diagnostic_only=True,
                             diagnostics=sink)
        assert result is None  # excluded from the conversion output
        records = sink.by_action(nb.ACTION_REJECTED_EXCLUDED)
        assert len(records) == 1
        assert records[0].event_id == event["event_id"]
        assert records[0].quality_status == event["quality_status"]
        assert tuple(records[0].reason_codes) == tuple(event["reason_codes"])


def test_diagnostic_only_without_sink_is_refused_never_silent():
    for event, instrument in ((crypto_trades.invalid_event(), CRYPTO_INST),
                              (forex_quotes.quarantined_event(), FX_INST)):
        matcher = event["event_type"] == "TRADE"
        with pytest.raises(nb.NautilusBridgeError, match="never silent"):
            if matcher:
                nb.to_trade_tick(event, instrument, diagnostic_only=True)
            else:
                nb.to_quote_tick(event, instrument, diagnostic_only=True)


def test_suspect_streams_with_recorded_sidecar_status():
    for module, instrument in ((crypto_trades, CRYPTO_INST),
                               (forex_quotes, FX_INST),
                               (stocks_trades_quotes, STOCK_INST)):
        suspects = [e for e in module.events()
                    if e["quality_status"] == "SUSPECT"]
        assert suspects, module.__name__
        for event in suspects:
            sink = nb.BridgeDiagnostics()
            if event["event_type"] == "TRADE":
                tick = nb.to_trade_tick(event, instrument, diagnostics=sink)
            else:
                tick = nb.to_quote_tick(event, instrument, diagnostics=sink)
            assert tick is not None  # SUSPECT streams
            records = sink.by_action(nb.ACTION_SUSPECT_STREAMED)
            assert len(records) == 1
            assert records[0].quality_status == "SUSPECT"
            assert records[0].event_id == event["event_id"]


def test_suspect_without_sidecar_sink_is_refused():
    event = crypto_trades.events()[13]
    assert event["quality_status"] == "SUSPECT"
    with pytest.raises(nb.BridgeQualityError, match="sidecar"):
        nb.to_trade_tick(event, CRYPTO_INST)


def test_valid_events_stream_and_record_converted_when_sink_given():
    sink = nb.BridgeDiagnostics()
    events = [e for e in crypto_trades.events()
              if e["quality_status"] == "VALID"]
    ticks = nb.convert_stream(events, CRYPTO_INST, diagnostics=sink)
    assert len(ticks) == len(events)
    converted = sink.by_action(nb.ACTION_CONVERTED)
    assert [r.event_id for r in converted] == [e["event_id"] for e in events]


# --- no lookahead ------------------------------------------------------------


def test_ts_event_after_ts_init_raises_no_lookahead():
    base = crypto_trades.events()[0]
    mutated = dict(base)
    mutated["exchange_time_utc_ns"] = base["available_time_utc_ns"] + 1
    with pytest.raises(nb.BridgeLookaheadError, match="no-lookahead"):
        nb.to_trade_tick(mutated, CRYPTO_INST)
    with pytest.raises(nb.BridgeLookaheadError):
        nb.to_quote_tick(mutated, CRYPTO_INST)


def test_negative_timestamps_refused_uint64_ns():
    base = crypto_trades.events()[0]
    for field in ("exchange_time_utc_ns", "available_time_utc_ns"):
        mutated = dict(base)
        mutated[field] = -1
        with pytest.raises(nb.NautilusBridgeError, match="uint64"):
            nb.to_trade_tick(mutated, CRYPTO_INST)


# --- bar mapping frozen out of @1 --------------------------------------------


def test_to_bar_raises_the_frozen_not_mapped_message():
    with pytest.raises(NotImplementedError) as excinfo:
        nb.to_bar(crypto_trades.events()[0], CRYPTO_INST)
    assert str(excinfo.value) == nb.BAR_NOT_MAPPED_IN_V1
    assert nb.BAR_NOT_MAPPED_IN_V1 == (
        "mdp.market_event@1 has no BAR type; OHLCV can never become quotes/depth")


# --- cross-asset conversion + mapping details --------------------------------


def test_cross_asset_fixtures_all_convert():
    crypto_sink, fx_sink, stock_sink = (nb.BridgeDiagnostics() for _ in range(3))
    crypto_ticks = nb.convert_stream(crypto_trades.events(), CRYPTO_INST,
                                     diagnostics=crypto_sink)
    assert len(crypto_ticks) == len(crypto_trades.events())
    fx_ticks = nb.convert_stream(forex_quotes.events(), FX_INST,
                                 diagnostics=fx_sink)
    assert len(fx_ticks) == len(forex_quotes.events())
    stock_ticks = nb.convert_stream(stocks_trades_quotes.events(), STOCK_INST,
                                    diagnostics=stock_sink)
    assert len(stock_ticks) == len(stocks_trades_quotes.events())
    # every SUSPECT in each fixture set was recorded while streaming
    for sink, module in ((crypto_sink, crypto_trades),
                         (fx_sink, forex_quotes),
                         (stock_sink, stocks_trades_quotes)):
        suspects = [e for e in module.events()
                    if e["quality_status"] == "SUSPECT"]
        assert (len(sink.by_action(nb.ACTION_SUSPECT_STREAMED))
                == len(suspects))


def test_convert_stream_preserves_input_order_never_reorders():
    events = stocks_trades_quotes.events()  # interleaved TRADE/QUOTE stream
    from nautilus_trader.model.data import QuoteTick, TradeTick

    ticks = nb.convert_stream(events, STOCK_INST,
                              diagnostics=nb.BridgeDiagnostics())
    assert len(ticks) == len(events)
    for event, tick in zip(events, ticks):
        expected_cls = QuoteTick if event["event_type"] == "QUOTE" else TradeTick
        assert isinstance(tick, expected_cls)
        assert tick.ts_event == event["exchange_time_utc_ns"]


def test_aggressor_side_mapping_buy_sell_and_absent():
    from nautilus_trader.model.enums import AggressorSide

    events = crypto_trades.events()
    by_side = {}
    for event in events:
        tick = nb.to_trade_tick(event, CRYPTO_INST,
                                diagnostics=nb.BridgeDiagnostics())
        by_side.setdefault(event["side"], tick)
    assert by_side["buy"].aggressor_side == AggressorSide.BUYER
    assert by_side["sell"].aggressor_side == AggressorSide.SELLER
    assert by_side[None].aggressor_side == AggressorSide.NO_AGGRESSOR


def test_trade_id_is_deterministic_event_id_prefix():
    # nautilus 1.230.0 caps TradeId at 36 chars; the bridge uses the
    # documented 32-char prefix of the canonical event_id.
    event = crypto_trades.events()[0]
    tick = nb.to_trade_tick(event, CRYPTO_INST)
    assert str(tick.trade_id) == event["event_id"][:nb._TRADE_ID_PREFIX_LEN]
    assert nb._TRADE_ID_PREFIX_LEN == 32


def test_event_type_and_instrument_identity_enforced():
    quote = forex_quotes.events()[0]
    trade = crypto_trades.events()[0]
    with pytest.raises(nb.NautilusBridgeError, match="QUOTE"):
        nb.to_trade_tick(quote, CRYPTO_INST)
    with pytest.raises(nb.NautilusBridgeError, match="TRADE"):
        nb.to_quote_tick(trade, FX_INST)
    with pytest.raises(nb.NautilusBridgeError, match="instrument_id"):
        nb.to_trade_tick(trade, FX_INST)  # right type, wrong instrument


def test_instrument_argument_is_mandatory_no_default():
    assert nb.requires_instrument_metadata().startswith(
        "instrument metadata is a MANDATORY bridge input")
    event = crypto_trades.events()[0]
    with pytest.raises(TypeError):
        nb.to_trade_tick(event)  # instrument has NO default
    with pytest.raises(TypeError):
        nb.to_quote_tick(event)
    with pytest.raises(nb.NautilusBridgeError, match="mandatory"):
        nb.to_trade_tick(event, instrument=None)


# --- import isolation (freeze package.import_isolation) ----------------------


def test_bridge_import_does_not_import_nautilus_trader_subprocess():
    script = (
        "import sys\n"
        f"sys.path.insert(0, {str(RESEARCH_DIR)!r})\n"
        "import market_data_plane.nautilus_bridge as nb\n"
        "heavy = [m for m in sys.modules\n"
        "         if m == 'nautilus_trader' or m.startswith('nautilus_trader.')]\n"
        "assert not heavy, heavy\n"
        "print('ISOLATION_OK')\n"
    )
    proc = subprocess.run([PYTHON, "-c", script], capture_output=True,
                          text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert "ISOLATION_OK" in proc.stdout


def test_bridge_module_has_no_top_level_nautilus_import():
    # function bodies legitimately import lazily (freeze import_isolation);
    # a column-0 nautilus import would violate it.
    source = Path(nb.__file__).read_text().splitlines()
    offenders = [line for line in source
                 if line.startswith(("from nautilus_trader",
                                     "import nautilus_trader"))]
    assert not offenders, offenders
