"""MDP-V1 A4 tests: depth view gating, market-by-level construction, L1 attachment.

Key invariants under test:
- NOT_EVALUABLE unless the caller explicitly supplies snapshot_proven=True AND
  sequence_contiguous=True (bars and any other shape can never synthesize depth);
- actual sequence contiguity of deltas is verified behind the flag;
- L1 always comes from the BBO view and is never gated by depth inputs;
- proven levels are exact Decimals, ordered best-bid-first / best-ask-first.

The source-inspection test at the bottom proves the module has no bar code
path at all: the identifiers of aggregate-candle fields never occur in
depth.py's source (there is nothing to grep FOR -- the module cannot even name
those fields).
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import depth as depth_mod  # noqa: E402
from market_data_plane.bbo import VenueBook  # noqa: E402
from market_data_plane.depth import (  # noqa: E402
    DepthView,
    NotEvaluable,
    evaluate_depth,
    evaluate_l1,
)

INST = "BTC-USD"


def assert_not_evaluable(value, reason):
    assert isinstance(value, NotEvaluable)
    assert not value  # sentinel is falsy
    assert value != 0  # never a zero substitution
    assert value.reason == reason


def proven_inputs(snapshot=None, deltas=None):
    return {
        "snapshot_proven": True,
        "sequence_contiguous": True,
        "snapshot": snapshot
        if snapshot is not None
        else {
            "venue": "VA",
            "instrument_id": INST,
            "currency": "USD",
            "sequence_number": 100,
            "exchange_time_utc_ns": 1_000,
            "receive_time_utc_ns": 1_001,
            "bids": [["100.00", "5"], ["99.99", "3"]],
            "asks": [["100.02", "4"], ["100.03", "2"]],
        },
        "deltas": deltas if deltas is not None else [],
    }


# --------------------------------------------------------------------------
# proven-semantics gate
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_input",
    [
        None,
        [],
        "snapshot",
        {},
        {"snapshot_proven": True},  # sequence_contiguous missing
        {"sequence_contiguous": True},  # snapshot_proven missing
        {"snapshot_proven": False, "sequence_contiguous": True},
        {"snapshot_proven": True, "sequence_contiguous": False},
        {"snapshot_proven": 1, "sequence_contiguous": 1},  # must be explicitly True
        {"bars": [{"o": 1}]},  # wrong-shaped payload without proven flags
    ],
)
def test_unproven_inputs_return_not_evaluable(bad_input):
    assert_not_evaluable(
        evaluate_depth(bad_input, staleness_threshold_ns=1_000), "DEPTH_SEMANTICS_UNPROVEN"
    )


def test_malformed_proven_payloads_return_not_evaluable():
    # flags claimed but snapshot missing entirely
    assert_not_evaluable(
        evaluate_depth({"snapshot_proven": True, "sequence_contiguous": True},
                       staleness_threshold_ns=1),
        "MALFORMED_DEPTH_RECORD",
    )
    # snapshot not a mapping (e.g. a candle-shaped record with OHLCV keys and no
    # bids/asks): the proven gate passes but the record is not depth-shaped
    assert_not_evaluable(
        evaluate_depth(
            {
                "snapshot_proven": True,
                "sequence_contiguous": True,
                "snapshot": {"open": "1", "high": "2", "low": "0.5", "close": "1.5", "volume": "9"},
                "deltas": [],
            },
            staleness_threshold_ns=1,
        ),
        "MALFORMED_DEPTH_RECORD",
    )
    # deltas not a list
    assert_not_evaluable(
        evaluate_depth(
            proven_inputs(deltas={"side": "bid"}), staleness_threshold_ns=1
        ),
        "MALFORMED_DEPTH_RECORD",
    )
    # bad decimal string in a level
    bad = proven_inputs()
    bad["snapshot"]["bids"] = [["10.x", "5"]]
    assert_not_evaluable(evaluate_depth(bad, staleness_threshold_ns=1), "MALFORMED_DEPTH_RECORD")
    # negative size
    bad2 = proven_inputs()
    bad2["snapshot"]["asks"] = [["100.02", "-4"]]
    assert_not_evaluable(evaluate_depth(bad2, staleness_threshold_ns=1), "MALFORMED_DEPTH_RECORD")
    # malformed delta
    assert_not_evaluable(
        evaluate_depth(
            proven_inputs(deltas=[{"side": "bid", "action": "set", "price": "1.00",
                                   "size": "oops", "sequence_number": 101}]),
            staleness_threshold_ns=1,
        ),
        "MALFORMED_DEPTH_RECORD",
    )


def test_staleness_threshold_is_required_on_every_evaluation_call():
    with pytest.raises(TypeError):
        evaluate_depth(None)  # missing staleness_threshold_ns -> no hidden default
    with pytest.raises(TypeError):
        evaluate_depth(proven_inputs())  # even the proven path demands it


# --------------------------------------------------------------------------
# market-by-level construction (proven case)
# --------------------------------------------------------------------------


def test_proven_snapshot_builds_exact_decimal_levels():
    view = evaluate_depth(proven_inputs(), staleness_threshold_ns=1_000)
    assert isinstance(view, DepthView)
    l2 = view.l2
    assert not isinstance(l2, NotEvaluable)
    # snapshot levels, best bid first (descending), best ask first (ascending)
    assert l2["bids"] == [[Decimal("100.00"), Decimal("5")], [Decimal("99.99"), Decimal("3")]]
    assert l2["asks"] == [[Decimal("100.02"), Decimal("4")], [Decimal("100.03"), Decimal("2")]]
    assert l2["sequence_number"] == 100
    assert l2["level_counts"] == {"bids": 2, "asks": 2}
    # exact arithmetic: every level value is a Decimal, never a float
    for price, size in l2["bids"] + l2["asks"]:
        assert isinstance(price, Decimal) and not isinstance(price, float)
        assert isinstance(size, Decimal) and not isinstance(size, float)


def test_proven_deltas_apply_in_sequence_order():
    deltas = [
        {"side": "ask", "action": "remove", "price": "100.02", "sequence_number": 102},
        {"side": "bid", "action": "set", "price": "100.01", "size": "7", "sequence_number": 101},
    ]
    view = evaluate_depth(proven_inputs(deltas=deltas), staleness_threshold_ns=1_000)
    l2 = view.l2
    # deltas applied by sequence order regardless of list order:
    # bids: set 100.01@7 over 100.00@5 -> [[100.01,7],[100.00,5],[99.99,3]]
    # asks: remove 100.02 -> [[100.03,2]]
    assert l2["bids"] == [
        [Decimal("100.01"), Decimal("7")],
        [Decimal("100.00"), Decimal("5")],
        [Decimal("99.99"), Decimal("3")],
    ]
    assert l2["asks"] == [[Decimal("100.03"), Decimal("2")]]
    assert l2["sequence_number"] == 102
    assert l2["snapshot_sequence_number"] == 100
    assert l2["delta_count"] == 2


def test_remove_of_absent_level_is_deterministic_noop():
    view = evaluate_depth(
        proven_inputs(
            deltas=[{"side": "ask", "action": "remove", "price": "123.45", "sequence_number": 101}]
        ),
        staleness_threshold_ns=1,
    )
    assert view.l2["asks"] == [[Decimal("100.02"), Decimal("4")], [Decimal("100.03"), Decimal("2")]]


def test_sequence_gap_detected_behind_the_flag():
    # flag claims contiguous but actual sequence jumps 101 -> 103 (102 missing)
    deltas = [
        {"side": "bid", "action": "set", "price": "100.01", "size": "7", "sequence_number": 101},
        {"side": "bid", "action": "set", "price": "100.02", "size": "8", "sequence_number": 103},
    ]
    assert_not_evaluable(
        evaluate_depth(proven_inputs(deltas=deltas), staleness_threshold_ns=1),
        "SEQUENCE_GAP_DETECTED",
    )


def test_duplicate_sequence_number_surfaces_as_gap():
    # a duplicated sequence number breaks contiguity (the second 101 is not the
    # expected 102), so the contiguity check refuses with a detected gap
    deltas = [
        {"side": "bid", "action": "set", "price": "100.01", "size": "7", "sequence_number": 101},
        {"side": "bid", "action": "set", "price": "100.02", "size": "8", "sequence_number": 101},
    ]
    assert_not_evaluable(
        evaluate_depth(proven_inputs(deltas=deltas), staleness_threshold_ns=1),
        "SEQUENCE_GAP_DETECTED",
    )


# --------------------------------------------------------------------------
# bars can never synthesize depth (behavioral proof)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bar_shaped",
    [
        [{"open": "1", "high": "2", "low": "0.5", "close": "1.5", "volume": "10"}],
        [{"timestamp": 1, "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5}],
        {"interval": "1m", "records": [{"open": "1", "close": "2"}]},
        [{"o": "1", "h": "2", "l": "0.5", "c": "1.5", "v": "10"}],
    ],
)
def test_ohlcv_shaped_inputs_can_never_become_depth(bar_shaped):
    # whatever the container shape, an OHLCV payload fails the gate:
    # NOT_EVALUABLE, never a synthesized book
    assert_not_evaluable(
        evaluate_depth(bar_shaped, staleness_threshold_ns=1), "DEPTH_SEMANTICS_UNPROVEN"
    )


def test_ohlcv_with_forged_proven_flags_still_not_evaluable():
    # even a caller lying about provenance cannot smuggle candle fields through:
    # the payload is not depth-shaped, so the gate still refuses
    forged = {
        "snapshot_proven": True,
        "sequence_contiguous": True,
        "snapshot": {"open": "1", "high": "2", "low": "0.5", "close": "1.5", "volume": "9"},
        "deltas": [{"open": "1", "sequence_number": 101}],
    }
    assert_not_evaluable(evaluate_depth(forged, staleness_threshold_ns=1), "MALFORMED_DEPTH_RECORD")


def test_module_has_no_bar_code_path_at_all():
    # source inspection: depth.py cannot even NAME aggregate-candle fields --
    # there is no synthesis code to reach, so bars cannot become depth by any path
    source = Path(depth_mod.__file__).read_text(encoding="utf-8").lower()
    for token in ("ohlcv", "ohlc", "open", "high", "low", "close", "volume"):
        assert token not in source, f"depth.py must not contain {token!r}"


# --------------------------------------------------------------------------
# L1 always available from BBO; L2 optional
# --------------------------------------------------------------------------


def _fresh_book():
    book = VenueBook()
    book.apply_quote(
        {
            "schema_version": "mdp.market_event@1",
            "event_id": "evt-l1",
            "raw_id": "raw-l1",
            "source_id": "src-1",
            "venue": "VA",
            "instrument_id": INST,
            "asset_class": "crypto",
            "event_type": "QUOTE",
            "exchange_time_utc_ns": 8_000,
            "receive_time_utc_ns": 8_001,
            "available_time_utc_ns": 8_001,
            "sequence_number": 0,
            "price": None,
            "quantity": None,
            "side": None,
            "bid_price": "100.00",
            "ask_price": "100.02",
            "bid_size": "1",
            "ask_size": "1",
            "currency": "USD",
            "price_precision": 2,
            "size_precision": 2,
            "quality_status": "VALID",
            "reason_codes": [],
            "raw_sha256": "0" * 64,
            "manifest_sha256": None,
            "normalizer_version": "test-1",
        }
    )
    return book


def test_l1_attached_from_bbo_view_and_never_gated_by_depth_inputs():
    book = _fresh_book()
    # depth inputs are UNPROVEN, yet L1 remains available from the BBO view:
    assert_not_evaluable(evaluate_depth(None, staleness_threshold_ns=1_000), "DEPTH_SEMANTICS_UNPROVEN")
    l1 = evaluate_l1(book, ["VA"], INST, {"VA"}, 10_000, 1_000)
    # fresh window [9_000, 10_000] vs quote et 8_000 -> stale -> empty consolidated
    assert l1["bid"] is None and l1["skipped_stale_count"] == 1
    l1_fresh = evaluate_l1(book, ["VA"], INST, {"VA"}, 10_000, 3_000)
    # window [7_000, 10_000] includes et 8_000
    assert l1_fresh["bid"] == Decimal("100.00")
    assert l1_fresh["ask"] == Decimal("100.02")
    assert evaluate_l1(book, ["VA"], INST, {"VA"}, 10_000, 3_000) == book.consolidated_bbo(
        ["VA"], INST, {"VA"}, 10_000, 3_000
    )


def test_depth_view_attaches_l1_and_keeps_l2_optional():
    book = _fresh_book()
    view = evaluate_depth(
        proven_inputs(),
        staleness_threshold_ns=3_000,
        l1_book=book,
        l1_venues=["VA"],
        l1_now_ns=10_000,
    )
    assert isinstance(view, DepthView)
    assert view.l1["bid"] == Decimal("100.00")  # BBO evidence, not depth-derived
    assert view.l1["ask"] == Decimal("100.02")
    assert view.l2["bids"][0][0] == Decimal("100.00")

    # L2 optional: without a BBO book the L2 view still stands, L1 reports why
    view_no_book = evaluate_depth(proven_inputs(), staleness_threshold_ns=1_000)
    assert not isinstance(view_no_book.l2, NotEvaluable)
    assert_not_evaluable(view_no_book.l1, "MISSING_BBO_EVIDENCE")

    # book given but no evaluation clock: L1 reports the missing clock evidence
    view_no_clock = evaluate_depth(
        proven_inputs(), staleness_threshold_ns=1_000, l1_book=book, l1_venues=["VA"]
    )
    assert_not_evaluable(view_no_clock.l1, "MISSING_CLOCK_EVIDENCE")
    assert not isinstance(view_no_clock.l2, NotEvaluable)
