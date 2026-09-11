"""Tests for mdp.market_bar@2 (lane A4, frozen bar contract).

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
tests/test_mdp_bars.py -q   (from the lane worktree root)

Covers: the exact frozen field set (missing + extra rejected), the
decimal-string discipline (float input rejected, canonical fixed-point
persistence, BAR_PRECISION_LOSS), strict time order with the availability_rule
hook, OHLC order + positive prices, NOT_EVALUABLE nulls (never zero), the
raw/adjusted identity rules, a hand-computed bar_id golden recomputed from the
frozen identity tuple, the raw/manifest sha discipline, the frozen
mdp.bar_reason_codes@2 extension set, and the no-microstructure guarantee
(a bar dict fails the mdp.market_event@1 validator).
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import bars, models, reason_codes as _rc  # noqa: E402

OPEN_NS = 1_700_000_100_000_000_000
INTERVAL_NS = 60_000_000_000
RAW_SHA = hashlib.sha256(b"raw0").hexdigest()
MANIFEST_SHA = hashlib.sha256(b"manifest0").hexdigest()


def bar_fields(**overrides) -> dict:
    fields = dict(
        schema_version=bars.SCHEMA_VERSION,
        source_id="SRC", provider_id="PROV", venue="VEN",
        instrument_id="BTCUSDT", asset_class="crypto_perpetual",
        bar_type="1m-LAST", interval_ns=INTERVAL_NS,
        open_time_utc_ns=OPEN_NS,
        close_time_utc_ns=OPEN_NS + INTERVAL_NS - 1_000_000,
        available_time_utc_ns=OPEN_NS + INTERVAL_NS,
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


# --- exact frozen field set ---------------------------------------------------


def test_exact_frozen_field_set_order_and_missing_extra_rejected():
    bar = bars.build_bar(bar_fields())
    assert list(bar.keys()) == list(bars.BAR_FIELDS)
    assert set(bar.keys()) == set(bars.BAR_FIELDS)
    # The frozen enumeration carries 32 field NAMES (the freeze prose labels
    # the set "31"; the enumeration is authoritative — surfaced to A1).
    assert len(bars.BAR_FIELDS) == 32
    assert len(bar) == len(bars.BAR_FIELDS)
    with pytest.raises(bars.BarError, match="MISSING_REQUIRED_FIELD"):
        fields = bar_fields()
        del fields["open_time_utc_ns"]
        bars.build_bar(fields)
    with pytest.raises(bars.BarError, match="unknown bar field"):
        bars.build_bar(bar_fields(unexpected_field="x"))
    with pytest.raises(bars.BarError, match="schema_version"):
        bars.build_bar(bar_fields(schema_version=models.SCHEMA_VERSION))


def test_bar_round_trip_is_idempotent_and_never_mutates_input():
    fields = bar_fields()
    bar = bars.build_bar(fields)
    assert bars.validate_bar(bar) == bar
    assert bars.from_dict(bars.to_dict(bar)) == bar
    assert "bar_id" not in fields  # input dict untouched (no id stamped in)


# --- decimal-string discipline -------------------------------------------------


def test_float_input_rejected_no_floats_anywhere_in_the_bar_model():
    for override in ({"open": 26495.5}, {"volume": 1.0}, {"close": float(1)}):
        with pytest.raises(bars.BarError, match="float input rejected"):
            bars.build_bar(bar_fields(**override))


def test_decimal_inputs_persist_as_canonical_fixed_point_strings():
    bar = bars.build_bar(bar_fields(open=Decimal("26495.5")))
    assert bar["open"] == "26495.5"
    # trailing zeros beyond the declared precision normalise losslessly
    bar = bars.build_bar(bar_fields(open="26495.50"))
    assert bar["open"] == "26495.5"
    # a value not representable at the declared precision fails closed
    with pytest.raises(bars.BarError, match="BAR_PRECISION_LOSS"):
        bars.build_bar(bar_fields(open="26495.55"))
    with pytest.raises(bars.BarError, match="BAR_PRECISION_LOSS"):
        bars.build_bar(bar_fields(volume="123.4565"))
    with pytest.raises(bars.BarError, match="MALFORMED_SHAPE"):
        bars.build_bar(bar_fields(open="2.64955e+4"))


# --- time order (strict, evidenced relaxation hook only) -----------------------


def test_time_order_strict_fail_closed():
    with pytest.raises(bars.BarError, match="IMPOSSIBLE_TIME_ORDER"):
        bars.build_bar(bar_fields(close_time_utc_ns=OPEN_NS))  # open == close
    with pytest.raises(bars.BarError, match="IMPOSSIBLE_TIME_ORDER"):
        bars.build_bar(bar_fields(close_time_utc_ns=OPEN_NS - 1))  # open > close
    with pytest.raises(bars.BarError, match="IMPOSSIBLE_TIME_ORDER"):
        bars.build_bar(
            bar_fields(available_time_utc_ns=OPEN_NS + INTERVAL_NS - 2_000_000))


def test_availability_rule_hook_explicit_evidenced_never_silent():
    rule = lambda bar: "evidenced: VEN late-publication rule v1"  # noqa: E731
    bar = bars.build_bar(
        bar_fields(available_time_utc_ns=OPEN_NS + 1_000_000),
        availability_rule=rule)
    assert bar["available_time_utc_ns"] == OPEN_NS + 1_000_000
    # the relaxation is never silent: strict re-validation fails
    with pytest.raises(bars.BarError, match="IMPOSSIBLE_TIME_ORDER"):
        bars.validate_bar(bar)
    # an unevidenced rule (empty/None return) still fails closed
    with pytest.raises(bars.BarError, match="IMPOSSIBLE_TIME_ORDER"):
        bars.build_bar(bar_fields(available_time_utc_ns=OPEN_NS + 1_000_000),
                       availability_rule=lambda bar: "")
    with pytest.raises(bars.BarError, match="IMPOSSIBLE_TIME_ORDER"):
        bars.build_bar(bar_fields(available_time_utc_ns=OPEN_NS + 1_000_000),
                       availability_rule=lambda bar: None)
    with pytest.raises(bars.BarError, match="availability_rule"):
        bars.build_bar(bar_fields(available_time_utc_ns=OPEN_NS + 1_000_000),
                       availability_rule="strict-please")
    # the open < close leg is NEVER relaxable
    with pytest.raises(bars.BarError, match="never relaxable"):
        bars.build_bar(bar_fields(close_time_utc_ns=OPEN_NS),
                       availability_rule=rule)


# --- OHLC order + positive prices -----------------------------------------------


def test_ohlc_order_violations_rejected():
    with pytest.raises(bars.BarError, match="BAR_OHLC_ORDER_VIOLATION"):
        bars.build_bar(bar_fields(high="26498.0"))  # high < close
    with pytest.raises(bars.BarError, match="BAR_OHLC_ORDER_VIOLATION"):
        bars.build_bar(bar_fields(low="26499.0"))  # low > open
    with pytest.raises(bars.BarError, match="BAR_OHLC_ORDER_VIOLATION"):
        bars.build_bar(bar_fields(low="26499.9", high="26500.0"))


def test_nonpositive_prices_rejected():
    with pytest.raises(bars.BarError, match="BAR_NONPOSITIVE_PRICE"):
        bars.build_bar(bar_fields(open="0"))
    with pytest.raises(bars.BarError, match="BAR_NONPOSITIVE_PRICE"):
        bars.build_bar(bar_fields(close="-1.0"))
    # negative volume-class values stay NEGATIVE_SIZE (reason_codes@1)
    with pytest.raises(bars.BarError, match="NEGATIVE_SIZE"):
        bars.build_bar(bar_fields(volume="-1.0"))


# --- NOT_EVALUABLE nulls (never zero) -------------------------------------------


def test_missing_volume_class_fields_are_null_never_zero():
    bar = bars.build_bar(bar_fields(volume=None))
    assert bar["volume"] is None
    assert bar["completeness_status"] == "NOT_EVALUABLE"
    assert "BAR_VOLUME_NOT_EVALUABLE" in bar["reason_codes"]
    all_null = bars.build_bar(bar_fields(
        volume=None, quote_volume=None, trade_count=None,
        taker_buy_base=None, taker_buy_quote=None))
    assert all_null["completeness_status"] == "NOT_EVALUABLE"
    for field in bars.VOLUME_FIELDS:
        assert all_null[field] is None
    trade_count_only = bars.build_bar(bar_fields(trade_count=None))
    assert trade_count_only["completeness_status"] == "NOT_EVALUABLE"
    # an explicit zero is only legal as PROVIDER evidence, never as a
    # missingness substitute: nulls stay null after validation
    assert bars.build_bar(bar_fields())["completeness_status"] == "COMPLETE"
    assert "BAR_VOLUME_NOT_EVALUABLE" not in bars.build_bar(bar_fields())["reason_codes"]
    # contradictory completeness evidence fails closed
    with pytest.raises(bars.BarError, match="contradictory"):
        bars.build_bar(bar_fields(reason_codes=["BAR_VOLUME_NOT_EVALUABLE"]))


# --- raw vs adjusted identity ----------------------------------------------------


def test_adjustment_mode_identity_rules():
    with pytest.raises(bars.BarError, match="corporate_action_ref"):
        bars.build_bar(bar_fields(adjustment_mode="CORP_ACTION_ADJUSTED",
                                  corporate_action_ref=None))
    adjusted = bars.build_bar(bar_fields(
        adjustment_mode="CORP_ACTION_ADJUSTED",
        corporate_action_ref="corp://split/2026-06-09/4:1"))
    assert adjusted["corporate_action_ref"] == "corp://split/2026-06-09/4:1"
    with pytest.raises(bars.BarError, match="RAW bars must carry a null"):
        bars.build_bar(bar_fields(corporate_action_ref="corp://stray"))
    with pytest.raises(bars.BarError, match="adjustment_mode"):
        bars.build_bar(bar_fields(adjustment_mode="SPLIT_ADJUSTED"))
    # raw and adjusted are DIFFERENT identities (adjustment_mode in bar_id)
    raw = bars.build_bar(bar_fields())
    assert raw["bar_id"] != adjusted["bar_id"]


# --- bar_id golden (hand recomputed from the frozen tuple) -----------------------


def test_bar_id_golden_recomputed_by_hand_from_frozen_identity_tuple():
    bar = bars.build_bar(bar_fields())
    identity = {
        "schema_version": "mdp.market_bar@2",
        "source_id": "SRC",
        "provider_id": "PROV",
        "venue": "VEN",
        "instrument_id": "BTCUSDT",
        "asset_class": "crypto_perpetual",
        "bar_type": "1m-LAST",
        "interval_ns": 60_000_000_000,
        "open_time_utc_ns": OPEN_NS,
        "adjustment_mode": "RAW",
    }
    expected = hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True).encode("utf-8")).hexdigest()
    assert bar["bar_id"] == expected
    assert bars.compute_bar_id(identity) == expected
    # identity participation: every identity field moves the id
    moved = bars.build_bar(bar_fields(open_time_utc_ns=OPEN_NS + 1))
    assert moved["bar_id"] != expected
    # a supplied disagreeing id is HASH_DISAGREEMENT (fail closed)
    with pytest.raises(bars.BarError, match="HASH_DISAGREEMENT"):
        bars.build_bar(bar_fields(bar_id="0" * 64))


# --- raw / manifest sha discipline ------------------------------------------------


def test_raw_and_manifest_sha_discipline():
    bar = bars.build_bar(bar_fields())
    assert bar["raw_id"] == bar["raw_sha256"] == RAW_SHA
    with pytest.raises(bars.BarError, match="HASH_DISAGREEMENT"):
        bars.build_bar(bar_fields(raw_id="f" * 64))
    with pytest.raises(bars.BarError, match="raw_sha256"):
        bars.build_bar(bar_fields(raw_sha256="NOT_HEX"))
    with pytest.raises(bars.BarError, match="manifest_sha256"):
        bars.build_bar(bar_fields(manifest_sha256="ab" * 31 + "g"))
    with pytest.raises(bars.BarError, match="manifest_sha256"):
        bars.build_bar(bar_fields(manifest_sha256=None))
    # an explicit raw_id must itself be strict 64-hex
    with pytest.raises(bars.BarError, match="raw_id"):
        bars.build_bar(bar_fields(raw_id="not-hex-at-all"))


# --- frozen reason-code extension set ----------------------------------------------


def test_bar_reason_code_extension_set_frozen():
    assert bars.BAR_REASON_CODES == (
        "BAR_OHLC_ORDER_VIOLATION",
        "BAR_NONPOSITIVE_PRICE",
        "BAR_INTERVAL_OVERLAP",
        "BAR_INTERVAL_DUPLICATE",
        "BAR_VOLUME_NOT_EVALUABLE",
        "BAR_OUTSIDE_CALENDAR",
        "BAR_PRECISION_LOSS",
    )
    # extends, never mutates, reason_codes@1
    assert set(_rc.CODES).isdisjoint(bars.BAR_REASON_CODES)
    for code in bars.BAR_REASON_CODES:
        assert not _rc.is_known(code)  # the @1 registry is untouched
        # BAR_VOLUME_NOT_EVALUABLE on a COMPLETE bar is contradictory
        # coverage (asserted in the NOT_EVALUABLE tests above); the other
        # codes ride legally on a valid bar
        if code == "BAR_VOLUME_NOT_EVALUABLE":
            continue
        bar = bars.build_bar(bar_fields(reason_codes=[code]))
        assert code in bar["reason_codes"]
    with pytest.raises(bars.BarError, match="outside reason_codes@1"):
        bars.build_bar(bar_fields(reason_codes=["BAR_NOT_A_REAL_CODE"]))


def test_quality_status_vocabulary_reuse_and_final_status_rule():
    assert bars.bar_status_from_codes(["BAR_OHLC_ORDER_VIOLATION"]) == "INVALID"
    assert bars.bar_status_from_codes(["BAR_PRECISION_LOSS"]) == "INVALID"
    assert bars.bar_status_from_codes(["BAR_OUTSIDE_CALENDAR"]) == "SUSPECT"
    # completeness classification never degrades quality_status (never zero,
    # not a defect)
    assert bars.bar_status_from_codes(["BAR_VOLUME_NOT_EVALUABLE"]) == "VALID"
    assert bars.bar_status_from_codes([]) == "VALID"
    assert bars.bar_status_from_codes(["SEQUENCE_GAP"]) == "SUSPECT"
    bar = bars.build_bar(bar_fields(quality_status="SUSPECT",
                                    reason_codes=["BAR_OUTSIDE_CALENDAR"]))
    assert bar["quality_status"] == "SUSPECT"
    with pytest.raises(bars.BarError, match="outside frozen enum"):
        bars.build_bar(bar_fields(quality_status="MEH"))


# --- no microstructure --------------------------------------------------------------


def test_bar_dict_fails_event_validation_no_microstructure():
    bar = bars.build_bar(bar_fields())
    with pytest.raises(models.MarketDataPlaneError):
        models.validate_event(bar)
