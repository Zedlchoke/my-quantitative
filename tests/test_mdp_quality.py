"""Quality classification tests (frozen semantics) incl. golden 3.

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
tests/test_mdp_quality.py -q   (from the lane worktree root)
"""

from __future__ import annotations

import copy
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import models, quality, reason_codes  # noqa: E402


def trade(**overrides):
    fields = dict(
        raw_id="raw-1", source_id="src-1", venue="BINANCE",
        instrument_id="BTCUSDT", asset_class="crypto", event_type="TRADE",
        exchange_time_utc_ns=100, receive_time_utc_ns=200,
        available_time_utc_ns=300, sequence_number=1,
        price="100.00", quantity="1.0", side="buy",
        price_precision=2, size_precision=1,
        raw_sha256=hashlib.sha256(b"raw").hexdigest(),
        manifest_sha256=hashlib.sha256(b"manifest").hexdigest(),
        normalizer_version="mdp-normalizer@1",
    )
    fields.update(overrides)
    return models.build_event(fields)


def quote(**overrides):
    fields = dict(
        raw_id="raw-q", source_id="src-1", venue="NYSE",
        instrument_id="XYZ", asset_class="stocks", event_type="QUOTE",
        exchange_time_utc_ns=100, receive_time_utc_ns=200,
        available_time_utc_ns=300, sequence_number=1,
        bid_price="100.005", ask_price="100.006",
        bid_size="10", ask_size="10",
        price_precision=3, size_precision=0,
        raw_sha256=hashlib.sha256(b"raw-q").hexdigest(),
        manifest_sha256=hashlib.sha256(b"manifest-q").hexdigest(),
        normalizer_version="mdp-normalizer@1",
    )
    fields.update(overrides)
    return models.build_event(fields)


def params(eval_time=10**9, staleness=10**9, **kw):
    return quality.QualityParams(evaluation_time_ns=eval_time,
                                 staleness_threshold_ns=staleness, **kw)


# --- golden 3: crossed vs valid quote ---------------------------------------


def test_golden_crossed_and_locked_quotes_rejected_valid_quote_ok():
    crossed = models.build_event(quote(bid_price="100.005",
                                       ask_price="100.005"))  # locked == crossed
    status, codes = quality.evaluate(crossed, {}, params())
    assert status == "INVALID"
    assert "CROSSED_QUOTE" in codes

    crossed = models.build_event(quote(bid_price="100.006",
                                       ask_price="100.005"))
    status, codes = quality.evaluate(crossed, {}, params())
    assert status == "INVALID"
    assert "CROSSED_QUOTE" in codes

    valid = models.build_event(quote(bid_price="100.005",
                                     ask_price="100.006"))
    status, codes = quality.evaluate(valid, {}, params())
    assert status == "VALID"
    assert codes == []


def test_crossed_quote_is_single_venue_rule_by_construction():
    # evaluate() sees ONE event; cross-venue disagreement can therefore never
    # be coded CROSSED_QUOTE here (consolidated BBO contributors own that).
    event = quote()
    assert event["venue"] == "NYSE"  # one venue+instrument per evaluation
    status, codes = quality.evaluate(event, {}, params())
    assert status == "VALID"


# --- staleness: explicit threshold, equality boundary -----------------------


def test_staleness_explicit_threshold_and_equality_boundary():
    event = quote(exchange_time_utc_ns=1000, receive_time_utc_ns=1100,
                  available_time_utc_ns=1200)
    # age == threshold: NOT stale ("older than the threshold" is strict)
    status, codes = quality.evaluate(
        event, {}, params(eval_time=1500, staleness=500))
    assert status == "VALID" and "STALE_QUOTE" not in codes
    # age == threshold + 1: stale
    status, codes = quality.evaluate(
        event, {}, params(eval_time=1501, staleness=500))
    assert status == "SUSPECT" and codes == ["STALE_QUOTE"]
    # staleness applies to quotes only
    t = trade(exchange_time_utc_ns=1000, receive_time_utc_ns=1100,
              available_time_utc_ns=1200)
    status, codes = quality.evaluate(t, {}, params(eval_time=10**9,
                                                   staleness=1))
    assert status == "VALID" and "STALE_QUOTE" not in codes


# --- sequence rules: gated on manifest semantics ----------------------------


def test_sequence_gap_only_when_contiguous():
    event = trade(sequence_number=5)
    ctx = {"sequence_semantics": "CONTIGUOUS", "last_sequence_number": 1}
    status, codes = quality.evaluate(event, ctx, params())
    assert status == "SUSPECT" and codes == ["SEQUENCE_GAP"]

    # with sequence_semantics=NONE a jump is not missing data
    ctx_none = {"sequence_semantics": "NONE", "last_sequence_number": 1}
    status, codes = quality.evaluate(event, ctx_none, params())
    assert status == "VALID" and codes == []

    # absent semantics: no sequence check at all
    status, codes = quality.evaluate(event, {}, params())
    assert status == "VALID" and codes == []

    # contiguous next sequence is clean
    ok = trade(sequence_number=2)
    status, codes = quality.evaluate(ok, ctx, params())
    assert status == "VALID"


def test_sequence_reset_evidenced_vs_unevidenced():
    event = trade(sequence_number=1)
    ctx = {"sequence_semantics": "CONTIGUOUS", "last_sequence_number": 9,
           "sequence_reset_evidenced": True}
    status, codes = quality.evaluate(event, ctx, params())
    assert status == "SUSPECT" and "SEQUENCE_RESET" in codes

    ctx["sequence_reset_evidenced"] = False
    status, codes = quality.evaluate(event, ctx, params())
    assert status == "INVALID" and codes == ["SOURCE_RESET_UNEVIDENCED"]


def test_null_sequence_under_contiguous_is_manifest_mismatch():
    event = trade(sequence_number=None)
    ctx = {"sequence_semantics": "CONTIGUOUS"}
    status, codes = quality.evaluate(event, ctx, params())
    assert status == "INVALID" and codes == ["MANIFEST_MISMATCH"]


# --- out-of-order delivery: gated on ordered_delivery -----------------------


def test_out_of_order_only_when_manifest_declares_ordered():
    event = trade(receive_time_utc_ns=100)
    ctx = {"ordered_delivery": True, "last_receive_time_ns": 500}
    status, codes = quality.evaluate(event, ctx, params())
    assert status == "SUSPECT" and codes == ["OUT_OF_ORDER_DELIVERY"]

    # equality is not out-of-order; replay sorting is deterministic, never deletes
    ctx["last_receive_time_ns"] = 100
    status, codes = quality.evaluate(event, ctx, params())
    assert status == "VALID"

    ctx["last_receive_time_ns"] = 99
    status, codes = quality.evaluate(event, ctx, params())
    assert status == "VALID"

    # not declared ordered -> never flagged
    status, codes = quality.evaluate(event, {"last_receive_time_ns": 500},
                                     params())
    assert status == "VALID"


# --- impossible time order / negatives / unknown instrument -----------------


def test_impossible_time_order_and_negative_flags():
    bad = copy.deepcopy(trade())
    bad["exchange_time_utc_ns"] = bad["available_time_utc_ns"] + 1
    status, codes = quality.evaluate(bad, {}, params())
    assert status == "INVALID" and codes == ["IMPOSSIBLE_TIME_ORDER"]

    neg_price = copy.deepcopy(trade())
    neg_price["price"] = "-1.00"
    status, codes = quality.evaluate(neg_price, {}, params())
    assert status == "INVALID" and "NEGATIVE_PRICE" in codes
    neg_size = copy.deepcopy(quote())
    neg_size["bid_size"] = "-1"
    status, codes = quality.evaluate(neg_size, {}, params())
    assert status == "INVALID" and "NEGATIVE_SIZE" in codes


def test_unknown_instrument_via_explicit_registry_parameter():
    registry = frozenset({"BTCUSDT", "ETHUSDT"})
    status, codes = quality.evaluate(trade(), {}, params(instrument_registry=registry))
    assert status == "VALID"
    status, codes = quality.evaluate(
        trade(instrument_id="DOGE"), {}, params(instrument_registry=registry))
    assert status == "INVALID" and codes == ["UNKNOWN_INSTRUMENT"]
    # registry None disables the check
    status, codes = quality.evaluate(trade(instrument_id="DOGE"), {}, params())
    assert status == "VALID"


# --- duplicates: bookkeeping via DedupeIndex --------------------------------


def test_duplicate_event_is_bookkeeping_and_keeps_valid_status():
    index = quality.DedupeIndex()
    ctx = {"dedupe_index": index}
    first = trade()
    status, codes = quality.evaluate(first, ctx, params())
    assert status == "VALID" and codes == []
    status, codes = quality.evaluate(first, ctx, params())
    assert codes == ["DUPLICATE_EVENT"]
    assert status == "VALID"  # bookkeeping class never raises the status
    assert len(index) == 1

    # a rejection code alongside a duplicate still wins
    neg = copy.deepcopy(first)
    neg["price"] = "-1.00"  # raw mutation: evaluate's structural check rejects
    status, codes = quality.evaluate(neg, ctx, params())
    assert status == "INVALID" and codes == ["NEGATIVE_PRICE"]


def test_dedupe_index_api():
    index = quality.DedupeIndex(["a", "b"])
    assert index.seen("a") and "b" in index and not index.seen("c")
    index.add("c")
    assert len(index) == 3


# --- statistical anomaly: diagnostic, |z|>6 on log price change -------------


def test_statistical_anomaly_z_score_rule():
    history = (100.0, 100.1, 100.2, 100.1, 100.15, 100.05, 100.1)
    p = params(recent_prices=history)
    calm = trade(price="100.11")
    status, codes = quality.evaluate(calm, {}, p)
    assert "STATISTICAL_ANOMALY" not in codes

    spike = trade(price="200")
    status, codes = quality.evaluate(spike, {}, p)
    assert "STATISTICAL_ANOMALY" in codes
    assert status == "SUSPECT"  # diagnostic suspect, never silent deletion

    # threshold equality uses strict >: build a case with |z| slightly > 6
    # by construction and one with tiny deviation inside the rule's guard
    short = params(recent_prices=(100.0, 100.1))
    status, codes = quality.evaluate(trade(price="100.2"), {}, short)
    assert codes == []  # too few prior changes -> rule abstains

    zero_dispersion = params(recent_prices=(100.0, 100.0, 100.0, 100.0))
    status, codes = quality.evaluate(trade(price="100.1"), {}, zero_dispersion)
    assert codes == []  # std == 0 -> abstain (never guess)

    # quote mid is the reference for quotes
    qhist = (10.0, 10.001, 10.002, 10.0015, 10.0008)
    qp = params(recent_prices=qhist)
    wild = quote(bid_price="50.000", ask_price="50.001",
                 price_precision=3)
    status, codes = quality.evaluate(wild, {}, qp)
    assert "STATISTICAL_ANOMALY" in codes


# --- structural passthrough + multiple codes + status precedence ------------


def test_structurally_invalid_event_returns_frozen_code():
    status, codes = quality.evaluate({"junk": True}, {}, params())
    assert status == "INVALID" and codes == ["MALFORMED_SHAPE"]
    status, codes = quality.evaluate(None, {}, params())
    assert status == "INVALID" and codes == ["MALFORMED_SHAPE"]


def test_multiple_codes_accumulate_and_rejection_wins():
    # crossed (reject) + stale (suspect) + gap (suspect) -> INVALID, all codes
    event = quote(bid_price="1.000", ask_price="1.000",
                  exchange_time_utc_ns=1000, receive_time_utc_ns=1100,
                  available_time_utc_ns=1200, sequence_number=7)
    ctx = {"sequence_semantics": "CONTIGUOUS", "last_sequence_number": 1}
    status, codes = quality.evaluate(event, ctx,
                                     params(eval_time=1000 + 500 + 1,
                                            staleness=500))
    assert status == "INVALID"
    assert codes == sorted({"CROSSED_QUOTE", "STALE_QUOTE", "SEQUENCE_GAP"})


def test_evaluate_is_pure_over_inputs():
    event = quote()
    ctx = {"sequence_semantics": "CONTIGUOUS", "last_sequence_number": 0,
           "ordered_delivery": True, "last_receive_time_ns": 500}
    p = params(eval_time=10**9, staleness=10**9)  # staleness ruled out
    event_snapshot = copy.deepcopy(event)
    ctx_snapshot = dict(ctx)
    for _ in range(3):
        status, codes = quality.evaluate(event, ctx, p)
    assert status == "SUSPECT" and codes == ["OUT_OF_ORDER_DELIVERY"]
    assert event == event_snapshot
    assert ctx == ctx_snapshot
    # repeated evaluation is deterministic (pure function of inputs + explicit state)
    assert quality.evaluate(event, ctx, p) == (status, codes)


def test_classify_helper_writes_status_and_codes():
    event = quote(bid_price="1.000", ask_price="1.000")
    classified = quality.classify_with_reason_codes(event, {}, params())
    assert classified["quality_status"] == "INVALID"
    assert classified["reason_codes"] == ["CROSSED_QUOTE"]
    # identity untouched by classification
    assert classified["event_id"] == event["event_id"]
