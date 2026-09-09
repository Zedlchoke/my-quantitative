"""MDP-V1 A4 tests: research TCA (research/market_data_plane/tca.py).

All expectations are HAND-COMPUTED literals; the arithmetic is shown in
comments next to each assertion.  All ratio math is Decimal inside the module;
the literals here are the float values at the metric boundary.

Shared evidence timeline (staleness_threshold_ns = 1_000_000_000 everywhere):
  qA et=0.9e9  bid 100.005 ask 100.015  (mid 100.010)
  qB et=1.4e9  bid 100.010 ask 100.030  (mid 100.020)
  qC et=2.5e9  bid 100.020 ask 100.040  (mid 100.030)
  qD et=3.0e9  bid 100.000 ask 100.060  (mid 100.030)
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane.depth import NotEvaluable  # noqa: E402
from market_data_plane.tca import (  # noqa: E402
    REALIZED_SPREAD_HORIZONS_NS,
    evaluate_tca,
    total_cost_view,
)

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

THRESHOLD = 1_000_000_000
H1, H5, H30, H300 = REALIZED_SPREAD_HORIZONS_NS


def assert_not_evaluable(value, reason):
    assert isinstance(value, NotEvaluable)
    assert not value
    assert value != 0  # NOT_EVALUABLE is never a zero substitution
    assert value.reason == reason


def quote(event_id, bid, ask, et):
    return {
        "schema_version": "mdp.market_event@1",
        "event_id": event_id,
        "raw_id": "raw-" + event_id,
        "source_id": "src-1",
        "venue": "VENE",
        "instrument_id": "BTC-USD",
        "asset_class": "crypto",
        "event_type": "QUOTE",
        "exchange_time_utc_ns": et,
        "receive_time_utc_ns": et + 1,
        "available_time_utc_ns": et + 1,
        "sequence_number": 0,
        "price": None,
        "quantity": None,
        "side": None,
        "bid_price": bid,
        "ask_price": ask,
        "bid_size": "1",
        "ask_size": "1",
        "currency": "USD",
        "price_precision": 3,
        "size_precision": 2,
        "quality_status": "VALID",
        "reason_codes": [],
        "raw_sha256": "0" * 64,
        "manifest_sha256": None,
        "normalizer_version": "test-1",
    }


QUOTES = [
    quote("evt-qa", "100.005", "100.015", 900_000_000),
    quote("evt-qb", "100.010", "100.030", 1_400_000_000),
    quote("evt-qc", "100.020", "100.040", 2_500_000_000),
    quote("evt-qd", "100.000", "100.060", 3_000_000_000),
]


def fill(fill_id, side, price, quantity, decision_ns, fill_ns, **extra):
    base = {
        "fill_id": fill_id,
        "venue": "VENE",
        "instrument_id": "BTC-USD",
        "currency": "USD",
        "side": side,
        "price": price,
        "quantity": quantity,
        "decision_time_utc_ns": decision_ns,
        "fill_time_utc_ns": fill_ns,
    }
    base.update(extra)
    return base


def fill_1():
    # buy 10 @ 100.02, decided at 1.0e9, filled at 1.5e9, fee 0.20, funding -0.05
    return fill(
        "fill-1", "buy", "100.02", "10",
        1_000_000_000, 1_500_000_000,
        fee="0.20", fee_currency="USD",
        funding_or_swap="-0.05", funding_currency="USD",
    )


def fill_2():
    # sell 5 @ 99.98, decided at 1.2e9, filled at 2.6e9, no fee/funding evidence
    return fill("fill-2", "sell", "99.98", "5", 1_200_000_000, 2_600_000_000)


# --------------------------------------------------------------------------
# hand-computed happy path
# --------------------------------------------------------------------------


def test_frozen_horizons_are_exact():
    assert REALIZED_SPREAD_HORIZONS_NS == (
        1_000_000_000,
        5_000_000_000,
        30_000_000_000,
        300_000_000_000,
    )


def test_arrival_mid_and_slippage_hand_computed():
    result = evaluate_tca([fill_1()], QUOTES, staleness_threshold_ns=THRESHOLD)
    row = result["fills"][0]
    # arrival: as-of decision 1.0e9 with window [0, 1.0e9] -> qA (et 0.9e9)
    # arrival_mid = (100.005 + 100.015) / 2 = 100.010 exactly
    assert row["arrival_mid"] == Decimal("100.010")
    assert row["arrival_mid_source"] == "venue_quote"
    # slippage = +1 * (100.02 - 100.01) / 100.01 * 1e4 = 100 / 100.01 = 0.9999000099990001
    assert row["decision_to_fill_slippage_bps"] == pytest.approx(0.9999000099990001, abs=0, rel=1e-15)


def test_effective_spread_hand_computed():
    result = evaluate_tca([fill_1()], QUOTES, staleness_threshold_ns=THRESHOLD)
    row = result["fills"][0]
    # mid at fill 1.5e9, window [0.5e9, 1.5e9] -> qB; mid = (100.010+100.030)/2 = 100.020
    assert row["mid_at_fill"] == Decimal("100.020")
    # effective = 2 * +1 * (100.02 - 100.02) / 100.02 * 1e4 = 0.0
    assert row["effective_spread_bps"] == 0.0

    result2 = evaluate_tca([fill_2()], QUOTES, staleness_threshold_ns=THRESHOLD)
    row2 = result2["fills"][0]
    # mid at fill 2.6e9, window [1.6e9, 2.6e9] -> qC (qD et 3.0e9 is future, no lookahead)
    # mid = (100.020+100.040)/2 = 100.030
    assert row2["mid_at_fill"] == Decimal("100.030")
    # effective = 2 * -1 * (99.98 - 100.03) / 99.98 * 1e4 = 1000 / 99.98 = 10.002000400080016
    assert row2["effective_spread_bps"] == pytest.approx(10.002000400080016, abs=0, rel=1e-15)


def test_realized_spread_and_impact_at_horizon_boundary_exact():
    result = evaluate_tca([fill_1()], QUOTES, staleness_threshold_ns=THRESHOLD)
    row = result["fills"][0]
    # H = 1e9: lookup t = 1.5e9 + 1e9 = 2.5e9, window [1.5e9, 2.5e9];
    # qC et == 2.5e9 exactly == t: horizon upper boundary is INCLUSIVE
    # mid = (100.020+100.040)/2 = 100.030
    # realized = 2 * +1 * (100.02 - 100.03) / 100.02 * 1e4 = -200/100.02 = -1.9996000799840032
    assert row["realized_spread_bps"][H1] == pytest.approx(-1.9996000799840032, abs=0, rel=1e-15)
    # impact = +1 * (100.03 - 100.02) / 100.02 * 1e4 = 100/100.02 = 0.9998000399920016
    assert row["impact_proxy_bps"][H1] == pytest.approx(0.9998000399920016, abs=0, rel=1e-15)
    # H = 5e9: t = 6.5e9, window [5.5e9, 6.5e9]; qC (2.5e9) and qD (3.0e9) are
    # older than 5.5e9 -> stale -> NOT_EVALUABLE for that horizon only
    assert_not_evaluable(row["realized_spread_bps"][H5], "MISSING_QUOTE_EVIDENCE")
    assert_not_evaluable(row["impact_proxy_bps"][H5], "MISSING_QUOTE_EVIDENCE")
    assert_not_evaluable(row["realized_spread_bps"][H30], "MISSING_QUOTE_EVIDENCE")
    assert_not_evaluable(row["realized_spread_bps"][H300], "MISSING_QUOTE_EVIDENCE")


def test_realized_spread_lower_staleness_boundary_exact():
    # quote exactly at t - threshold is fresh; one ns older is stale
    edge = [quote("evt-lo", "99.990", "100.010", 1_500_000_000)]  # mid (99.990+100.010)/2 = 100.000
    f = fill("f", "buy", "100.02", "1", 1_000_000_000, 1_500_000_000)
    row = evaluate_tca([f], edge, staleness_threshold_ns=THRESHOLD)["fills"][0]
    # t = 1.5e9 + 1e9 = 2.5e9; window [1.5e9, 2.5e9]; quote et == 1.5e9 == t - threshold: INCLUDED
    # realized = 2 * (100.02 - 100.000) / 100.02 * 1e4 = 400/100.02 = 3.9992001599680064
    assert row["realized_spread_bps"][H1] == pytest.approx(3.9992001599680064, abs=0, rel=1e-15)

    edge_old = [quote("evt-lo", "99.990", "100.010", 1_499_999_999)]  # one ns too old
    row_old = evaluate_tca([f], edge_old, staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert_not_evaluable(row_old["realized_spread_bps"][H1], "MISSING_QUOTE_EVIDENCE")


def test_realized_and_impact_second_fill_hand_computed():
    result = evaluate_tca([fill_2()], QUOTES, staleness_threshold_ns=THRESHOLD)
    row = result["fills"][0]
    # arrival as-of 1.2e9, window [0.2e9, 1.2e9] -> qA; mid 100.010
    assert row["arrival_mid"] == Decimal("100.010")
    # slippage = -1 * (99.98 - 100.01) / 100.01 * 1e4 = 300/100.01 = 2.9997000299970003
    assert row["decision_to_fill_slippage_bps"] == pytest.approx(2.9997000299970003, abs=0, rel=1e-15)
    # H = 1e9: t = 3.6e9, window [2.6e9, 3.6e9] -> qD (et 3.0e9); mid = (100.000+100.060)/2 = 100.030
    # realized = 2 * -1 * (99.98 - 100.03) / 99.98 * 1e4 = 1000/99.98 = 10.002000400080016
    assert row["realized_spread_bps"][H1] == pytest.approx(10.002000400080016, abs=0, rel=1e-15)
    # impact = -1 * (100.030 - 100.030) / 100.030 * 1e4 = 0.0 (sign-normalised, not -0.0)
    assert row["impact_proxy_bps"][H1] == 0.0


def test_fees_funding_columns_and_fill_ratio():
    result = evaluate_tca(
        [fill_1(), fill_2()], QUOTES, staleness_threshold_ns=THRESHOLD, submitted_quantity="20"
    )
    rows = {r["fill_id"]: r for r in result["fills"]}
    # fees stay a separate column: amount 0.20 exactly, never merged into slippage
    assert rows["fill-1"]["fees"] == Decimal("0.20")
    # fees_bps = 0.20 / (100.02 * 10) * 1e4 = 2000 / 1000.2 = 1.9996000799840032
    assert rows["fill-1"]["fees_bps"] == pytest.approx(1.9996000799840032, abs=0, rel=1e-15)
    assert rows["fill-1"]["funding_or_swap"] == Decimal("-0.05")
    # funding_bps = -0.05 / 1000.2 * 1e4 = -500/1000.2 = -0.4999000199960008
    assert rows["fill-1"]["funding_bps"] == pytest.approx(-0.4999000199960008, abs=0, rel=1e-15)
    # fill_ratio = (10 + 5) / 20 = 0.75
    assert result["fill_ratio"] == 0.75
    # fill-2 has no fee/funding evidence: NOT_EVALUABLE, never zero
    assert_not_evaluable(rows["fill-2"]["fees"], "MISSING_FEE_EVIDENCE")
    assert_not_evaluable(rows["fill-2"]["funding_or_swap"], "MISSING_FEE_EVIDENCE")


def test_staleness_threshold_required():
    with pytest.raises(TypeError):
        evaluate_tca([fill_1()], QUOTES)  # missing staleness_threshold_ns


# --------------------------------------------------------------------------
# recorded-consolidated fallback (venue BBO first, consolidated only when recorded)
# --------------------------------------------------------------------------


def test_consolidated_fallback_used_only_when_recorded_and_venue_quote_absent():
    # decision 0.1e9 predates every venue quote -> no venue-local evidence
    f = fill(
        "f", "buy", "100.02", "1", 100_000_000, 1_500_000_000,
        consolidated_arrival_bbo={"bid": "100.000", "ask": "100.020"},
    )
    row = evaluate_tca([f], QUOTES, staleness_threshold_ns=THRESHOLD)["fills"][0]
    # fallback mid = (100.000 + 100.020)/2 = 100.010, flagged as recorded-consolidated
    assert row["arrival_mid_source"] == "consolidated_recorded"
    assert row["arrival_mid"] == Decimal("100.010")
    # slippage = (100.02 - 100.01)/100.01*1e4 = 0.9999000099990001
    assert row["decision_to_fill_slippage_bps"] == pytest.approx(0.9999000099990001, abs=0, rel=1e-15)

    # venue quote exists -> it wins, the recorded consolidated evidence is ignored
    f2 = fill(
        "f2", "buy", "100.02", "1", 1_000_000_000, 1_500_000_000,
        consolidated_arrival_bbo={"bid": "1.00", "ask": "1.02"},
    )
    row2 = evaluate_tca([f2], QUOTES, staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert row2["arrival_mid_source"] == "venue_quote"
    assert row2["arrival_mid"] == Decimal("100.010")

    # neither venue quote nor recorded consolidation -> NOT_EVALUABLE
    f3 = fill("f3", "buy", "100.02", "1", 100_000_000, 1_500_000_000)
    row3 = evaluate_tca([f3], QUOTES, staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert_not_evaluable(row3["arrival_mid"], "MISSING_QUOTE_EVIDENCE")
    assert_not_evaluable(row3["decision_to_fill_slippage_bps"], "MISSING_QUOTE_EVIDENCE")


# --------------------------------------------------------------------------
# NOT_EVALUABLE per affected metric on each missing-evidence path
# --------------------------------------------------------------------------


def test_missing_side():
    f = fill("f", None, "100.02", "1", 1_000_000_000, 1_500_000_000, fee="0.20")
    row = evaluate_tca([f], QUOTES, staleness_threshold_ns=THRESHOLD)["fills"][0]
    # arrival_mid needs no side: still exact
    assert row["arrival_mid"] == Decimal("100.010")
    assert_not_evaluable(row["decision_to_fill_slippage_bps"], "MISSING_SIDE")
    assert_not_evaluable(row["effective_spread_bps"], "MISSING_SIDE")
    assert_not_evaluable(row["realized_spread_bps"][H1], "MISSING_SIDE")
    assert_not_evaluable(row["impact_proxy_bps"][H1], "MISSING_SIDE")
    # fee amount evidence is independent of side
    assert row["fees"] == Decimal("0.20")


def test_missing_decision_clock_evidence_only_affects_decision_metrics():
    f = fill("f", "buy", "100.02", "1", None, 1_500_000_000)
    row = evaluate_tca([f], QUOTES, staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert_not_evaluable(row["arrival_mid"], "MISSING_CLOCK_EVIDENCE")
    assert_not_evaluable(row["decision_to_fill_slippage_bps"], "MISSING_CLOCK_EVIDENCE")
    # fill-time metrics remain evaluable from fill_time evidence
    assert row["mid_at_fill"] == Decimal("100.020")
    assert row["effective_spread_bps"] == 0.0


def test_missing_fill_clock_evidence():
    f = fill("f", "buy", "100.02", "1", 1_000_000_000, None)
    row = evaluate_tca([f], QUOTES, staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert row["arrival_mid"] == Decimal("100.010")
    assert row["decision_to_fill_slippage_bps"] == pytest.approx(0.9999000099990001, abs=0, rel=1e-15)
    assert_not_evaluable(row["mid_at_fill"], "MISSING_CLOCK_EVIDENCE")
    assert_not_evaluable(row["effective_spread_bps"], "MISSING_CLOCK_EVIDENCE")
    assert_not_evaluable(row["realized_spread_bps"][H1], "MISSING_CLOCK_EVIDENCE")
    assert_not_evaluable(row["impact_proxy_bps"][H1], "MISSING_CLOCK_EVIDENCE")


def test_missing_quote_evidence_never_zeroes_metrics():
    f = fill("f", "buy", "100.02", "1", 1_000_000_000, 1_500_000_000, fee="0.25")
    row = evaluate_tca([f], [], staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert_not_evaluable(row["arrival_mid"], "MISSING_QUOTE_EVIDENCE")
    assert_not_evaluable(row["decision_to_fill_slippage_bps"], "MISSING_QUOTE_EVIDENCE")
    assert_not_evaluable(row["mid_at_fill"], "MISSING_QUOTE_EVIDENCE")
    assert_not_evaluable(row["effective_spread_bps"], "MISSING_QUOTE_EVIDENCE")
    assert_not_evaluable(row["realized_spread_bps"][H1], "MISSING_QUOTE_EVIDENCE")
    assert_not_evaluable(row["impact_proxy_bps"][H1], "MISSING_QUOTE_EVIDENCE")
    # fee evidence is independent of quotes: still exact
    assert row["fees"] == Decimal("0.25")


def test_currency_mismatch_without_conversion_evidence():
    eur_quotes = [quote("evt-eur", "90.000", "90.020", 900_000_000)]
    eur_quotes[0]["currency"] = "EUR"
    f = fill("f", "buy", "100.02", "1", 1_000_000_000, 1_500_000_000)  # USD fill
    row = evaluate_tca([f], eur_quotes, staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert_not_evaluable(row["arrival_mid"], "CURRENCY_MISMATCH_NO_CONVERSION")
    assert_not_evaluable(row["decision_to_fill_slippage_bps"], "CURRENCY_MISMATCH_NO_CONVERSION")
    assert_not_evaluable(row["effective_spread_bps"], "CURRENCY_MISMATCH_NO_CONVERSION")


def test_unknown_quote_currency_is_unproven_not_mismatch():
    # None currency cannot be PROVEN different: allowed, not a proven mismatch
    null_ccy = [quote("evt-n", "100.000", "100.020", 900_000_000)]
    null_ccy[0]["currency"] = None
    f = fill("f", "buy", "100.02", "1", 1_000_000_000, 1_500_000_000)
    row = evaluate_tca([f], null_ccy, staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert row["arrival_mid"] == Decimal("100.010")


def test_malformed_quote_evidence():
    bad = [quote("evt-bad", "not-a-price", "100.020", 900_000_000)]
    f = fill("f", "buy", "100.02", "1", 1_000_000_000, 1_500_000_000)
    row = evaluate_tca([f], bad, staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert_not_evaluable(row["arrival_mid"], "MALFORMED_QUOTE_EVIDENCE")


def test_missing_fill_and_submitted_evidence():
    f = fill("f", "buy", None, "1", 1_000_000_000, 1_500_000_000)
    row = evaluate_tca([f], QUOTES, staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert_not_evaluable(row["decision_to_fill_slippage_bps"], "MISSING_FILL_EVIDENCE")
    assert_not_evaluable(row["effective_spread_bps"], "MISSING_FILL_EVIDENCE")
    assert_not_evaluable(row["realized_spread_bps"][H1], "MISSING_FILL_EVIDENCE")
    # fee amount still recorded; fee bps need the notional -> NOT_EVALUABLE
    f_fee = fill("g", "buy", None, "1", 1_000_000_000, 1_500_000_000, fee="0.20")
    row_fee = evaluate_tca([f_fee], QUOTES, staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert row_fee["fees"] == Decimal("0.20")
    assert_not_evaluable(row_fee["fees_bps"], "MISSING_FILL_EVIDENCE")

    result = evaluate_tca([fill_1()], QUOTES, staleness_threshold_ns=THRESHOLD)
    assert_not_evaluable(result["fill_ratio"], "MISSING_SUBMITTED_QUANTITY_EVIDENCE")


def test_fee_currency_mismatch():
    f = fill("f", "buy", "100.02", "1", 1_000_000_000, 1_500_000_000,
             fee="0.20", fee_currency="EUR")
    row = evaluate_tca([f], QUOTES, staleness_threshold_ns=THRESHOLD)["fills"][0]
    assert row["fees"] == Decimal("0.20")
    assert_not_evaluable(row["fees_bps"], "CURRENCY_MISMATCH_NO_CONVERSION")


# --------------------------------------------------------------------------
# total cost view: only evaluable columns are summed, exclusions reported
# --------------------------------------------------------------------------


def test_total_cost_view_sums_evaluable_columns_and_reports_exclusions():
    result = evaluate_tca(
        [fill_1(), fill_2()], QUOTES, staleness_threshold_ns=THRESHOLD, submitted_quantity="20"
    )
    view = total_cost_view(result, fees_included=True, funding_included=True)
    by_id = {p["fill_id"]: p for p in view["per_fill"]}
    # fill-1 total = 0.9999000099990001 + 1.9996000799840032 + (-0.4999000199960008)
    #             = 2.4996000699870025
    assert by_id["fill-1"]["total_bps"] == pytest.approx(2.4996000699870025, abs=0, rel=1e-15)
    assert by_id["fill-1"]["excluded"] == []
    # fill-2: fees/funding missing -> excluded with reasons; total = slippage only
    assert by_id["fill-2"]["total_bps"] == pytest.approx(2.9997000299970003, abs=0, rel=1e-15)
    assert {"column": "fees_bps", "reason": "MISSING_FEE_EVIDENCE"} in by_id["fill-2"]["excluded"]
    assert {"column": "funding_bps", "reason": "MISSING_FEE_EVIDENCE"} in by_id["fill-2"]["excluded"]
    assert {"column": "fees_bps", "fill_id": "fill-2", "reason": "MISSING_FEE_EVIDENCE"} in view["excluded"]
    assert {"column": "funding_bps", "fill_id": "fill-2", "reason": "MISSING_FEE_EVIDENCE"} in view["excluded"]
    # weighted aggregate = (10*2.4996000699870025 + 5*2.9997000299970003) / 15
    #                    = 2.666300056657002
    assert view["weighted_total_bps"] == pytest.approx(2.666300056657002, abs=0, rel=1e-15)


def test_total_cost_view_excludes_by_request():
    result = evaluate_tca(
        [fill_1()], QUOTES, staleness_threshold_ns=THRESHOLD, submitted_quantity="10"
    )
    view = total_cost_view(result, fees_included=False, funding_included=True)
    assert view["included_columns"] == ["decision_to_fill_slippage_bps", "funding_bps"]
    assert {"column": "fees_bps", "reason": "EXCLUDED_BY_REQUEST"} in view["excluded"]
    # fill-1 total without fees = 0.9999000099990001 + (-0.4999000199960008)
    #                           = 0.4999999900029993
    assert view["per_fill"][0]["total_bps"] == pytest.approx(0.4999999900029993, abs=0, rel=1e-15)
    assert result["fill_ratio"] == 1.0  # 10/10


def test_total_cost_view_unevaluable_core_slippage():
    f = fill("f", "buy", "100.02", "1", 1_000_000_000, 1_500_000_000, fee="0.20")
    result = evaluate_tca([f], [], staleness_threshold_ns=THRESHOLD)
    view = total_cost_view(result, fees_included=True, funding_included=True)
    # core slippage missing -> no total at all (never zero), fees not double-reported
    entry = view["per_fill"][0]
    assert_not_evaluable(entry["total_bps"], "MISSING_QUOTE_EVIDENCE")
    assert view["weighted_total_bps"].reason == "NO_EVALUABLE_FILLS"


# --------------------------------------------------------------------------
# property: per-fill metrics are invariant under input permutation
# --------------------------------------------------------------------------


@settings(derandomize=True, max_examples=30, deadline=None)
@given(
    st.lists(
        st.tuples(
            st.sampled_from([1, -1]),                 # side sign
            st.integers(min_value=99_000, max_value=101_000),  # fill price cents
            st.integers(min_value=1, max_value=50),   # quantity
            st.integers(min_value=0, max_value=4),    # decision slot
        ),
        min_size=1,
        max_size=5,
    ),
    st.integers(min_value=1, max_value=500),          # submitted quantity
)
def test_property_tca_invariant_under_input_permutation(specs, submitted):
    fills = []
    for i, (sign, price_cents, quantity, slot) in enumerate(specs):
        decision = 1_000_000_000 + slot * 400_000_000
        fills.append(
            fill(
                f"fill-{i:02d}",
                "buy" if sign == 1 else "sell",
                f"{price_cents // 100}.{price_cents % 100:02d}",
                str(quantity),
                decision,
                decision + 300_000_000,
            )
        )
    base = evaluate_tca(fills, QUOTES, staleness_threshold_ns=THRESHOLD,
                        submitted_quantity=submitted)
    permuted = evaluate_tca(list(reversed(fills)), QUOTES, staleness_threshold_ns=THRESHOLD,
                            submitted_quantity=submitted)
    again = evaluate_tca(fills, QUOTES, staleness_threshold_ns=THRESHOLD,
                         submitted_quantity=submitted)
    # rows are keyed and sorted by fill_id: the whole result is permutation-invariant
    assert base == permuted
    assert base == again
