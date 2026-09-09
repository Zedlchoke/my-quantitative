"""Property-based tests (Hypothesis) for MDP-V1 models + quality.

Profile selection: ``mdp_ci`` by default via HYPOTHESIS_PROFILE (frozen
profiles registered in tests/mdp_hypothesis/profiles.py, which this module
imports before any test runs).  The deep gate runs once with:

    HYPOTHESIS_PROFILE=mdp_deep \
      /Users/hoangminhlong/my-quantitative/.venv/bin/python \
      -m pytest tests/test_mdp_hyp_models_quality.py -q

No explicit ``@settings(max_examples=...)`` is used anywhere: example counts,
derandomization, deadline and health checks come exclusively from the frozen
profile, so mdp_ci and mdp_deep exercise the identical properties.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("HYPOTHESIS_PROFILE", "mdp_ci")  # BEFORE hypothesis import

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

import pytest  # noqa: E402  (after env selection, before hypothesis use)
from hypothesis import given, strategies as st  # noqa: E402

from market_data_plane import models, quality, reason_codes  # noqa: E402
from tests.mdp_hypothesis import profiles  # noqa: E402,F401  (registers+loads)
from tests.mdp_hypothesis import strategies as mst  # noqa: E402


def mdp_quality_params():
    return quality.QualityParams(evaluation_time_ns=2**62,
                                 staleness_threshold_ns=10**12)


# --- property 1: from_dict(to_dict(e)) == e for valid events ----------------


@given(mst.valid_event_dicts())
def test_round_trip_identity_for_valid_events(fields):
    event = models.build_event(fields)
    assert models.from_dict(models.to_dict(event)) == event
    # JSON round trip of the canonical dict is lossless (all values are
    # strings/ints/lists — never floats, never datetimes)
    revived = models.from_dict(json.loads(models.canonical_json(event)))
    assert revived == event


# --- property 2: every invalid shape rejected with the frozen code ----------


@given(mst.invalid_event_dicts())
def test_invalid_shapes_rejected_with_frozen_code(pair):
    event, expected_code = pair
    with pytest.raises(models.MarketDataPlaneError) as exc:
        models.validate_event(event)
    assert exc.value.reason_code == expected_code
    # the same code surfaces through quality.evaluate's structural gate
    status, codes = quality.evaluate(event, {}, mdp_quality_params())
    assert status == "INVALID"
    assert codes == [expected_code]


# --- property 3: byte-stable canonical json + digest ------------------------


@given(mst.valid_event_dicts(), st.integers(1, 6))
def test_canonical_json_and_stream_digest_byte_stability(fields, n):
    events = []
    for i in range(n):
        fields_i = dict(fields)
        fields_i["raw_id"] = f"{fields['raw_id']}-{i}"
        fields_i["sequence_number"] = i
        fields_i["exchange_time_utc_ns"] += i
        fields_i["receive_time_utc_ns"] = max(fields_i["receive_time_utc_ns"],
                                              fields_i["exchange_time_utc_ns"])
        fields_i["available_time_utc_ns"] = max(
            fields_i["available_time_utc_ns"], fields_i["receive_time_utc_ns"])
        events.append(models.build_event(fields_i))
    line0 = models.canonical_json(events[0])
    assert line0 == models.canonical_json(models.from_dict(json.loads(line0)))
    digest_a = models.stream_digest(events)
    assert digest_a == models.stream_digest(events)  # deterministic, repeatable
    assert models.stream_digest(list(reversed(events))) == \
        models.stream_digest(events[::-1])
    replay = models.sort_events_for_replay(events)
    assert models.stream_digest(replay) == models.stream_digest(replay)
    # total order key: order independent of input permutation
    shuffled = events[::-1]
    assert models.stream_digest(models.sort_events_for_replay(shuffled)) == \
        models.stream_digest(replay)


# --- property 4: evaluate is a pure function of (event, context, params) ----


@given(mst.valid_event_dicts(), mst.manifest_contexts(), mst.quality_params())
def test_evaluate_pure_function_of_inputs(event_fields, context, params):
    event = models.build_event(event_fields)
    event_before = copy.deepcopy(event)
    context_before = copy.deepcopy(context)
    result_a = quality.evaluate(event, context, params)
    result_b = quality.evaluate(event, context, params)
    result_c = quality.evaluate(copy.deepcopy(event), copy.deepcopy(context),
                                params)
    assert result_a == result_b == result_c
    assert event == event_before
    assert context == context_before
    status, codes = result_a
    assert status in models.QUALITY_STATUSES
    assert codes == sorted(set(codes))
    for code in codes:
        assert reason_codes.is_known(code)
    assert status == reason_codes.final_status_for(codes)


# --- quality semantics over generated scenarios -----------------------------


@given(mst.crossed_or_locked_quote_dicts())
def test_generated_crossed_or_locked_quotes_rejected(event):
    status, codes = quality.evaluate(event, {}, mdp_quality_params())
    assert "CROSSED_QUOTE" in codes
    assert status == "INVALID"


@given(mst.stale_quote_scenario())
def test_generated_stale_quotes_suspect(scenario):
    event, params = scenario
    status, codes = quality.evaluate(event, {}, params)
    assert "STALE_QUOTE" in codes
    assert status == "SUSPECT"


@given(mst.valid_event_dicts())
def test_sequence_codes_exact_deterministic_scenarios(fields):
    event = models.build_event(fields)
    if event["sequence_number"] != 5:
        raw = models.to_dict(event)
        raw["sequence_number"] = 5
        raw["event_id"] = None
        event = models.validate_event(raw)
    assert event["sequence_number"] == 5
    # staleness ruled out: evaluation time equals the event's exchange time
    p = quality.QualityParams(
        evaluation_time_ns=event["exchange_time_utc_ns"],
        staleness_threshold_ns=10**18)
    status, codes = quality.evaluate(
        event, {"sequence_semantics": "CONTIGUOUS", "last_sequence_number": 1},
        p)
    assert "SEQUENCE_GAP" in codes and status == "SUSPECT"
    status, codes = quality.evaluate(
        event, {"sequence_semantics": "CONTIGUOUS", "last_sequence_number": 9,
                "sequence_reset_evidenced": True}, p)
    assert codes == ["SEQUENCE_RESET"] and status == "SUSPECT"
    status, codes = quality.evaluate(
        event, {"sequence_semantics": "CONTIGUOUS", "last_sequence_number": 9},
        p)
    assert codes == ["SOURCE_RESET_UNEVIDENCED"] and status == "INVALID"
    status, codes = quality.evaluate(
        event, {"sequence_semantics": "NONE", "last_sequence_number": 1}, p)
    assert codes == [] and status == "VALID"


@given(mst.valid_event_dicts())
def test_out_of_order_gated_on_ordered_delivery(fields):
    event = models.build_event(fields)
    p = mdp_quality_params()
    ctx = {"ordered_delivery": True,
           "last_receive_time_ns": event["receive_time_utc_ns"] + 1}
    status, codes = quality.evaluate(event, ctx, p)
    assert "OUT_OF_ORDER_DELIVERY" in codes and status == "SUSPECT"
    status, codes = quality.evaluate(
        event, {"last_receive_time_ns": event["receive_time_utc_ns"] + 1}, p)
    assert "OUT_OF_ORDER_DELIVERY" not in codes


# --- structural invariants over generated valid events ----------------------


@given(mst.valid_event_dicts())
def test_precision_and_identity_invariants(fields):
    event = models.build_event(fields)
    # decimals persist as canonical fixed-point strings at declared precision
    for name, precision in (("price", "price_precision"),
                            ("quantity", "size_precision"),
                            ("bid_price", "price_precision"),
                            ("ask_price", "price_precision"),
                            ("bid_size", "size_precision"),
                            ("ask_size", "size_precision")):
        value = event[name]
        if value is None:
            continue
        d = Decimal(value)
        assert max(0, -d.as_tuple().exponent) <= event[precision]
        assert "e" not in value.lower()
        assert value == format(d, "f")
    # timestamps are ints, never bool/float
    for name in ("exchange_time_utc_ns", "receive_time_utc_ns",
                 "available_time_utc_ns"):
        assert isinstance(event[name], int)
        assert not isinstance(event[name], bool)
    # event_id is lowercase hex sha256 and deterministic from identity fields
    assert len(event["event_id"]) == 64
    assert event["event_id"] == event["event_id"].lower()
    assert event["event_id"] == models.compute_event_id(event)


@given(mst.valid_event_dicts())
def test_extreme_decimal_magnitudes_survive_as_exact_strings(fields):
    event = models.build_event(fields)
    for name in ("price", "quantity"):
        value = event[name]
        if value is None:  # matrix-forbidden on QUOTE
            continue
        value = Decimal(value)
        if value == 0:
            continue
        assert Decimal("1e-8") <= value <= Decimal("1e9")
    assert models.from_dict(models.to_dict(event)) == event


@given(mst.valid_event_dicts())
def test_reason_codes_canonicalised_sorted_unique(fields):
    event = models.build_event(fields)
    shuffled = models.set_quality(event, "SUSPECT",
                                  ["STALE_QUOTE", "DUPLICATE_EVENT",
                                   "STALE_QUOTE"])
    assert shuffled["reason_codes"] == ["DUPLICATE_EVENT", "STALE_QUOTE"]
    assert models.from_dict(models.to_dict(shuffled)) == shuffled
