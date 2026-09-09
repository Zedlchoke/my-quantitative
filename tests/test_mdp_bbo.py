"""MDP-V1 A4 tests: venue-local and consolidated BBO (research/market_data_plane/bbo.py).

Every fixture expectation is hand-computed and shown as a literal with the
arithmetic in a comment.  Property tests use LOCAL hypothesis strategies with
an inline derandomized profile (the shared profiles are owned by A2).
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import bbo as bbo_mod  # noqa: E402
from market_data_plane.bbo import VenueBook, is_quote_stale, venue_asof_quote  # noqa: E402

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

INST = "BTC-USD"


def quote_event(
    venue,
    instrument_id=INST,
    bid="100.00",
    ask="100.02",
    et=1_000,
    rt=1_001,
    event_id="evt-x",
    currency="USD",
    bid_size="1",
    ask_size="1",
    quality_status="VALID",
):
    """Full 27-field mdp.market_event@1 QUOTE envelope as a plain dict."""
    return {
        "schema_version": "mdp.market_event@1",
        "event_id": event_id,
        "raw_id": "raw-" + event_id,
        "source_id": "src-1",
        "venue": venue,
        "instrument_id": instrument_id,
        "asset_class": "crypto",
        "event_type": "QUOTE",
        "exchange_time_utc_ns": et,
        "receive_time_utc_ns": rt,
        "available_time_utc_ns": rt,
        "sequence_number": 0,
        "price": None,
        "quantity": None,
        "side": None,
        "bid_price": bid,
        "ask_price": ask,
        "bid_size": bid_size,
        "ask_size": ask_size,
        "currency": currency,
        "price_precision": 2,
        "size_precision": 2,
        "quality_status": quality_status,
        "reason_codes": [],
        "raw_sha256": "0" * 64,
        "manifest_sha256": None,
        "normalizer_version": "test-1",
    }


# --------------------------------------------------------------------------
# venue-local: last non-stale quote wins, deterministic tie-break
# --------------------------------------------------------------------------


def test_venue_local_last_quote_wins():
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=1_000, rt=1_001, event_id="evt-1"))
    book.apply_quote(quote_event("VA", bid="100.01", ask="100.03", et=2_000, rt=2_001, event_id="evt-2"))
    local = book.venue_local("VA", INST)
    # later (et, rt) quote replaces the earlier one
    assert local["bid"] == Decimal("100.01")
    assert local["ask"] == Decimal("100.03")
    assert local["event_id"] == "evt-2"
    assert local["bid_size"] == Decimal("1")


def test_venue_local_out_of_order_apply_is_ignored():
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.01", ask="100.03", et=2_000, rt=2_001, event_id="evt-new"))
    # older quote arrives late: it must NOT replace the winner (order independence)
    replaced = book.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=1_000, rt=1_001, event_id="evt-old"))
    assert replaced is False
    assert book.venue_local("VA", INST)["event_id"] == "evt-new"


def test_venue_local_tie_break_event_id_then_receive_time():
    # Case 1: equal (et, rt) -> greater event_id wins ("evt-zzz" > "evt-yyy").
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.02", ask="100.04", et=2_000, rt=2_000, event_id="evt-zzz"))
    book.apply_quote(quote_event("VA", bid="100.01", ask="100.03", et=2_000, rt=2_000, event_id="evt-yyy"))
    assert book.venue_local("VA", INST)["event_id"] == "evt-zzz"
    # Case 2: receive_time beats event_id ("evt-aaa" has larger rt and smaller id).
    book2 = VenueBook()
    book2.apply_quote(quote_event("VA", bid="100.01", ask="100.03", et=2_000, rt=2_000, event_id="evt-zzz"))
    book2.apply_quote(quote_event("VA", bid="100.02", ask="100.04", et=2_000, rt=2_500, event_id="evt-aaa"))
    assert book2.venue_local("VA", INST)["event_id"] == "evt-aaa"


def test_venue_local_staleness_boundary_exact():
    now = 10_000_000_000
    threshold = 4_000_000_000
    # stale iff et < now - threshold = 10e9 - 4e9 = 6_000_000_000
    assert is_quote_stale(5_999_999_999, now, threshold) is True
    assert is_quote_stale(6_000_000_000, now, threshold) is False  # boundary equality is fresh

    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=6_000_000_000, rt=6_000_000_001, event_id="evt-edge"))
    fresh = book.evaluate_venue_local("VA", INST, now, threshold)
    assert fresh is not None and fresh["bid"] == Decimal("100.00")

    book2 = VenueBook()
    book2.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=5_999_999_999, rt=5_999_999_999, event_id="evt-old"))
    assert book2.evaluate_venue_local("VA", INST, now, threshold) is None
    # ...but the same quote is fresh under a wider threshold: threshold is an input, not a constant
    assert book2.evaluate_venue_local("VA", INST, now, 4_000_000_001) is not None


def test_staleness_threshold_is_required_no_default():
    book = VenueBook()
    book.apply_quote(quote_event("VA", event_id="evt-1"))
    with pytest.raises(TypeError):
        book.evaluate_venue_local("VA", INST, 10_000)  # missing staleness_threshold_ns
    with pytest.raises(TypeError):
        book.consolidated_bbo(["VA"], INST, {"VA"}, 10_000)  # missing staleness_threshold_ns
    with pytest.raises(TypeError):
        venue_asof_quote([], "VA", INST, 10_000)  # missing staleness_threshold_ns


def test_invalid_and_quarantined_events_are_ignored():
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.01", ask="100.03", et=1_000, rt=1_001, event_id="evt-good"))
    assert (
        book.apply_quote(
            quote_event("VA", bid="200.00", ask="200.02", et=2_000, rt=2_001, event_id="evt-bad", quality_status="INVALID")
        )
        is False
    )
    assert (
        book.apply_quote(
            quote_event("VA", bid="300.00", ask="300.02", et=3_000, rt=3_001, event_id="evt-q", quality_status="QUARANTINED")
        )
        is False
    )
    local = book.venue_local("VA", INST)
    assert local["event_id"] == "evt-good"  # INVALID evidence never becomes view state
    # SUSPECT remains usable evidence (flag, not rejection)
    assert (
        book.apply_quote(
            quote_event("VA", bid="100.02", ask="100.04", et=4_000, rt=4_001, event_id="evt-sus", quality_status="SUSPECT")
        )
        is True
    )
    assert book.venue_local("VA", INST)["event_id"] == "evt-sus"


def test_malformed_or_non_quote_events_raise():
    book = VenueBook()
    trade = quote_event("VA", bid="1", ask="2")
    trade["event_type"] = "TRADE"
    with pytest.raises(ValueError):
        book.apply_quote(trade)
    with pytest.raises(ValueError):
        book.apply_quote(quote_event("VA", bid=None, ask="2"))
    with pytest.raises(ValueError):
        book.apply_quote(quote_event("VA", bid="10.x", ask="2"))
    with pytest.raises(ValueError):
        book.apply_quote(quote_event("VA", bid="1e5", ask="2"))  # exponent form is not canonical
    with pytest.raises(ValueError):
        book.apply_quote(quote_event("VA", et=1_000.5))  # float clock evidence rejected


# --------------------------------------------------------------------------
# consolidated BBO
# --------------------------------------------------------------------------


def test_consolidated_best_bid_max_and_best_ask_min_with_contributors():
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=6_000, rt=6_001, event_id="evt-a"))
    book.apply_quote(quote_event("VB", bid="100.01", ask="100.03", et=7_000, rt=7_001, event_id="evt-b"))
    result = book.consolidated_bbo(["VA", "VB"], INST, {"VA", "VB"}, 10_000, 5_000)
    # best_bid = max(100.00, 100.01) = 100.01 from VB; best_ask = min(100.02, 100.03) = 100.02 from VA
    assert result["bid"] == Decimal("100.01")
    assert result["ask"] == Decimal("100.02")
    assert result["bid_contributors"] == ["evt-b"]
    assert result["ask_contributors"] == ["evt-a"]
    assert result["venues_used"] == ["VA", "VB"]
    assert result["skipped_stale_count"] == 0
    assert result["crossed"] is False


def test_consolidated_tied_sides_record_all_contributors():
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.01", ask="100.05", et=6_000, rt=6_001, event_id="evt-a"))
    book.apply_quote(quote_event("VB", bid="100.01", ask="100.02", et=7_000, rt=7_001, event_id="evt-b"))
    result = book.consolidated_bbo(["VA", "VB"], INST, {"VA", "VB"}, 10_000, 5_000)
    # both venues bid 100.01 -> both event ids are bid contributors (sorted)
    assert result["bid"] == Decimal("100.01")
    assert result["bid_contributors"] == ["evt-a", "evt-b"]
    # best ask = min(100.05, 100.02) = 100.02 only from VB
    assert result["ask"] == Decimal("100.02")
    assert result["ask_contributors"] == ["evt-b"]


def test_consolidated_crossed_across_venues_reported_not_raised():
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.05", ask="100.06", et=6_000, rt=6_001, event_id="evt-a"))
    book.apply_quote(quote_event("VB", bid="100.00", ask="100.01", et=7_000, rt=7_001, event_id="evt-b"))
    # best_bid (100.05, VA) > best_ask (100.01, VB): cross-venue disagreement is
    # information, never a CROSSED_QUOTE error
    result = book.consolidated_bbo(["VA", "VB"], INST, {"VA", "VB"}, 10_000, 5_000)
    assert result["bid"] == Decimal("100.05")
    assert result["ask"] == Decimal("100.01")
    assert result["crossed"] is True
    assert result["bid_contributors"] == ["evt-a"]
    assert result["ask_contributors"] == ["evt-b"]


def test_consolidated_locked_reported_crossed_per_frozen_convention():
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.03", ask="100.05", et=6_000, rt=6_001, event_id="evt-a"))
    book.apply_quote(quote_event("VB", bid="100.01", ask="100.03", et=7_000, rt=7_001, event_id="evt-b"))
    # best_bid = max(100.03, 100.01) = 100.03; best_ask = min(100.05, 100.03) = 100.03
    # bid == ask (locked) -> crossed True under the frozen bid >= ask convention
    result = book.consolidated_bbo(["VA", "VB"], INST, {"VA", "VB"}, 10_000, 5_000)
    assert result["bid"] == Decimal("100.03")
    assert result["ask"] == Decimal("100.03")
    assert result["crossed"] is True


def test_identity_incompatible_currency_excluded_from_consolidation():
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=6_000, rt=6_001, event_id="evt-a", currency="USD"))
    # same instrument_id, different currency: NOT identity-compatible
    book.apply_quote(quote_event("VB", bid="100.99", ask="101.01", et=7_000, rt=7_001, event_id="evt-b", currency="EUR"))
    result = book.consolidated_bbo(["VA", "VB"], INST, {"VA", "VB"}, 10_000, 5_000)
    # EUR quote would have the best bid but must be excluded: no conversion assumed
    assert result["bid"] == Decimal("100.00")
    assert result["bid_contributors"] == ["evt-a"]
    assert result["ask"] == Decimal("100.02")
    assert result["venues_used"] == ["VA"]
    assert result["skipped_stale_count"] == 0


def test_unknown_currency_is_only_compatible_with_unknown():
    book = VenueBook()
    # lexicographically smallest venue (VA) has no currency evidence -> anchor None
    book.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=6_000, rt=6_001, event_id="evt-a", currency=None))
    book.apply_quote(quote_event("VB", bid="100.50", ask="100.60", et=7_000, rt=7_001, event_id="evt-b", currency="USD"))
    result = book.consolidated_bbo(["VA", "VB"], INST, {"VA", "VB"}, 10_000, 5_000)
    # None currency cannot be proven equal to USD: fail closed, VB excluded
    assert result["venues_used"] == ["VA"]
    assert result["bid"] == Decimal("100.00")


def test_consolidated_skips_stale_venues_and_counts_them():
    now = 10_000_000_000
    threshold = 5_000_000_000  # cutoff = 5_000_000_000
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=1_000_000_000, rt=1_000_000_001, event_id="evt-stale"))
    book.apply_quote(quote_event("VB", bid="100.01", ask="100.03", et=9_000_000_000, rt=9_000_000_001, event_id="evt-fresh"))
    result = book.consolidated_bbo(["VA", "VB"], INST, {"VA", "VB"}, now, threshold)
    # stale VA quote (et 1e9 < 5e9 cutoff) is skipped and counted; VB wins both sides
    assert result["skipped_stale_count"] == 1
    assert result["venues_used"] == ["VB"]
    assert result["bid"] == Decimal("100.01")
    assert result["ask"] == Decimal("100.03")
    assert result["crossed"] is False


def test_consolidated_staleness_boundary_count_exact():
    now = 10_000_000_000
    threshold = 5_000_000_000
    book = VenueBook()
    # et == now - threshold exactly -> fresh (not "older than")
    book.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=5_000_000_000, rt=5_000_000_001, event_id="evt-edge"))
    result = book.consolidated_bbo(["VA"], INST, {"VA"}, now, threshold)
    assert result["skipped_stale_count"] == 0
    assert result["venues_used"] == ["VA"]
    # one nanosecond older -> stale, counted, nothing used
    book2 = VenueBook()
    book2.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=4_999_999_999, rt=4_999_999_999, event_id="evt-edge"))
    result2 = book2.consolidated_bbo(["VA"], INST, {"VA"}, now, threshold)
    assert result2["skipped_stale_count"] == 1
    assert result2["bid"] is None and result2["ask"] is None
    assert result2["crossed"] is False and result2["venues_used"] == []


def test_consolidated_respects_permitted_venues():
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=6_000, rt=6_001, event_id="evt-a"))
    book.apply_quote(quote_event("VB", bid="100.01", ask="100.03", et=7_000, rt=7_001, event_id="evt-b"))
    result = book.consolidated_bbo(["VA", "VB"], INST, {"VA"}, 10_000, 5_000)
    # VB holds the best bid but is not permitted: only VA participates
    assert result["bid"] == Decimal("100.00")
    assert result["bid_contributors"] == ["evt-a"]
    assert result["venues_used"] == ["VA"]
    assert result["skipped_stale_count"] == 0  # unpermitted is not "stale"


def test_consolidated_empty_candidates_and_unknown_instrument():
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.00", ask="100.02", et=6_000, rt=6_001, event_id="evt-a"))
    empty = book.consolidated_bbo([], INST, set(), 10_000, 5_000)
    assert empty == {
        "bid": None,
        "ask": None,
        "bid_contributors": [],
        "ask_contributors": [],
        "venues_used": [],
        "skipped_stale_count": 0,
        "crossed": False,
        "reference_currency": None,  # A1 ruling A4_Q2: currency is recorded
    }
    # venue permitted but no quote for THIS instrument: absent, not stale
    assert book.consolidated_bbo(["VA"], "ETH-USD", {"VA"}, 10_000, 5_000)["skipped_stale_count"] == 0


def test_venue_local_crossed_quote_is_diagnostic_not_error():
    book = VenueBook()
    book.apply_quote(quote_event("VA", bid="100.05", ask="100.04", et=6_000, rt=6_001, event_id="evt-a"))
    local = book.venue_local("VA", INST)
    assert local["crossed"] is True  # within-one-venue crossing is surfaced diagnostically
    result = book.consolidated_bbo(["VA"], INST, {"VA"}, 10_000, 5_000)
    assert result["crossed"] is True  # reported as-is, never raised


def test_venue_asof_quote_window_and_determinism():
    quotes = [
        quote_event("VA", bid="100.00", ask="100.02", et=900_000_000, rt=900_000_001, event_id="evt-qa"),
        quote_event("VA", bid="100.01", ask="100.03", et=1_400_000_000, rt=1_400_000_001, event_id="evt-qb"),
        quote_event("VA", bid="100.02", ask="100.04", et=1_000_000_000, rt=1_000_000_001, event_id="evt-qc"),
    ]
    threshold = 1_000_000_000
    # as-of 1_000_000_000: candidates et in [0, 1_000_000_000] -> evt-qa (0.9e9)
    # and evt-qc (1.0e9, exactly at the upper boundary -> included);
    # winner = max by (et, rt, id) = evt-qc
    assert venue_asof_quote(quotes, "VA", INST, 1_000_000_000, threshold)["event_id"] == "evt-qc"
    # as-of 1_900_000_000: window [0.9e9, 1.9e9] includes evt-qa exactly at the
    # lower boundary (et == at - threshold -> fresh) and evt-qb (1.4e9): winner evt-qb
    assert venue_asof_quote(quotes, "VA", INST, 1_900_000_000, threshold)["event_id"] == "evt-qb"
    # window [1_900_000_001, 2_900_000_001]: qb (1.4e9) now below the lower
    # boundary, nothing newer -> None
    assert venue_asof_quote(quotes, "VA", INST, 2_900_000_001, threshold) is None
    # future quote never leaks backwards (no lookahead)
    assert venue_asof_quote(quotes, "VA", INST, 1_399_999_999, threshold)["event_id"] == "evt-qc"
    # other venue / instrument never matches
    assert venue_asof_quote(quotes, "VB", INST, 1_000_000_000, threshold) is None
    assert venue_asof_quote(quotes, "VA", "ETH-USD", 1_000_000_000, threshold) is None
    # INVALID quality never becomes evidence
    quotes_bad = [quote_event("VA", bid="9.99", ask="10.01", et=1_000_000_000, rt=1_000_000_001,
                              event_id="evt-bad", quality_status="INVALID")]
    assert venue_asof_quote(quotes_bad, "VA", INST, 1_000_000_000, threshold) is None


# --------------------------------------------------------------------------
# property: stale/crossed/locked quotes -> deterministic, monotone consolidation
# --------------------------------------------------------------------------


def _cents(c: int) -> str:
    return f"{c // 100}.{c % 100:02d}"


VENUES = ("VA", "VB", "VC")


@settings(derandomize=True, max_examples=30, deadline=None)
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=2),   # venue index
            st.integers(min_value=0, max_value=20),  # time slot (x 1000 ns)
            st.integers(min_value=5, max_value=500),  # bid cents
            st.integers(min_value=-2, max_value=5),   # ask delta cents (<0 crossed, 0 locked)
        ),
        min_size=1,
        max_size=12,
    ),
    st.integers(min_value=15_000, max_value=25_000),  # now_ns
)
def test_property_consolidated_deterministic_and_monotone(specs, now_ns):
    threshold = 5_000
    events = []
    for i, (vi, slot, bid_cents, ask_delta) in enumerate(specs):
        et = slot * 1_000
        events.append(
            quote_event(
                VENUES[vi],
                bid=_cents(bid_cents),
                ask=_cents(bid_cents + ask_delta),  # ask_delta may cross/lock within the venue
                et=et,
                rt=et + 1,
                event_id=f"e{i:04d}",  # unique id -> total order independent of arrival
            )
        )
    book_a = VenueBook()
    for ev in events:
        book_a.apply_quote(ev)
    book_b = VenueBook()
    for ev in reversed(events):
        book_b.apply_quote(ev)

    result = book_a.consolidated_bbo(VENUES, INST, set(VENUES), now_ns, threshold)
    permuted = book_b.consolidated_bbo(VENUES, INST, set(VENUES), now_ns, threshold)
    # determinism under input permutation (unique event ids give a total order)
    assert result == permuted

    fresh = {}
    for venue in VENUES:
        q = book_a.evaluate_venue_local(venue, INST, now_ns, threshold)
        if q is not None:
            fresh[venue] = q
    stale_count = 0
    for venue in VENUES:
        stored = book_a.venue_local(venue, INST)
        if stored is not None and stored["exchange_time_utc_ns"] < now_ns - threshold:
            stale_count += 1
    assert result["skipped_stale_count"] == stale_count

    if not fresh:
        assert result["bid"] is None and result["ask"] is None
        assert result["crossed"] is False
        return
    # monotone re-derivation: best bid is the max, best ask the min of fresh locals
    best_bid = max(q["bid"] for q in fresh.values())
    best_ask = min(q["ask"] for q in fresh.values())
    assert result["bid"] == best_bid
    assert result["ask"] == best_ask
    assert result["crossed"] == (best_bid >= best_ask)
    assert sorted(result["bid_contributors"]) == sorted(
        q["event_id"] for q in fresh.values() if q["bid"] == best_bid
    )
    assert sorted(result["ask_contributors"]) == sorted(
        q["event_id"] for q in fresh.values() if q["ask"] == best_ask
    )
    assert result["venues_used"] == sorted(fresh)


def test_consolidated_result_records_reference_currency_a1_ruling():
    # A1 ruling A4_Q2 (MDP-V1): currency exclusion must be observable.
    book = bbo_mod.VenueBook()
    et = 1_700_000_000_000_000_000
    for venue, ccy, bid, ask in (("AAA", "USD", "100.0", "100.2"),
                                 ("BBB", "USD", "100.1", "100.3"),
                                 ("CCC", "EUR", "99.9", "100.1")):
        book.apply_quote(quote_event(venue, bid=bid, ask=ask, et=et, rt=et + 1,
                                     currency=ccy, event_id=f"e-{venue}"))
    res = book.consolidated_bbo(["AAA", "BBB", "CCC"], INST, {"AAA", "BBB", "CCC"},
                                et + 1, 10**9)
    assert res["reference_currency"] == "USD"   # AAA is the lexicographic anchor
    assert res["venues_used"] == ["AAA", "BBB"]
    empty = book.consolidated_bbo([], INST, set(), et + 1, 10**9)
    assert empty["reference_currency"] is None
