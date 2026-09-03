"""Cohort verification logic on synthetic payloads (schema, splits, TR, calendar).

The real-snapshot integration cases live in ``test_real_snapshot.py``.  Here
every payload is synthetic; the OHLC sanity check is proven S0-bounded (an
out-of-range S1 row that would fail the sanity check is deliberately NOT
value-checked, only structurally).
"""

from __future__ import annotations

import json
from datetime import date

import pytest

from research.assets.stocks.calendar import USEquityRegularCalendar
from research.stocks_free_v3.authority import (
    CALENDAR_DIGEST,
    S0_END,
    S1_START,
    PINNED_CLOSE_RATIOS,
    SPLIT_SYMBOLS,
)
from research.stocks_free_v3.cohort import (
    VERDICT_FAIL,
    VERDICT_NOT_RUN,
    VERDICT_PASS,
    CohortVerificationReport,
    verify_calendar,
    verify_distribution_inputs,
    verify_split_events,
    verify_symbol_payload,
    verify_tr_inputs,
)


def _payload(
    symbol: str,
    rows: list[dict[str, object]],
    *,
    status: str = "ok",
    meta: dict | None = None,
) -> dict:
    base_meta = {
        "symbol": symbol,
        "interval": "1day",
        "currency": "USD",
        "exchange": "NYSE",
        "mic_code": "ARCX",
    }
    if meta:
        base_meta.update(meta)
    return {"meta": base_meta, "status": status, "values": rows}


def _row(day: str, close: str = "10", high: str | None = None, low: str | None = None,
         open_: str = "10", volume: str = "1000") -> dict[str, str]:
    # Sane defaults: high = max(open, close), low = min(open, close); rows
    # with unparsable numbers skip the derivation (they fail numeric_parse).
    try:
        top, bottom = max(open_, close, key=float), min(open_, close, key=float)
    except ValueError:
        top = bottom = open_
    return {
        "datetime": day,
        "open": open_,
        "high": high or top,
        "low": low or bottom,
        "close": close,
        "volume": volume,
    }


def _s0_rows() -> list[dict[str, object]]:
    return [
        _row("2025-07-31", close="11"),
        _row("2025-07-30", close="10"),
        _row("2018-04-04", close="5"),
    ]


# --- per-symbol schema checks ---------------------------------------------------- #


def test_valid_payload_passes_all_checks() -> None:
    checks = verify_symbol_payload(_payload("SPY", _s0_rows()), "SPY")
    by_name = {c.name: c for c in checks}
    assert all(c.verdict == VERDICT_PASS for c in checks)
    assert set(by_name) == {
        "status_and_meta",
        "symbol_identity",
        "row_schema",
        "numeric_parse",
        "s0_bar_sanity",
        "coverage_span",
    }


def test_bad_status_and_meta_fail() -> None:
    checks = verify_symbol_payload(_payload("SPY", _s0_rows(), status="error"), "SPY")
    by_name = {c.name: c for c in checks}
    assert by_name["status_and_meta"].verdict == VERDICT_FAIL
    wrong = verify_symbol_payload(_payload("SPY", _s0_rows(), meta={"symbol": "XLC"}), "SPY")
    assert {c.name: c for c in wrong}["symbol_identity"].verdict == VERDICT_FAIL
    wrong_interval = verify_symbol_payload(
        _payload("SPY", _s0_rows(), meta={"interval": "1min"}), "SPY"
    )
    assert {c.name: c for c in wrong_interval}["symbol_identity"].verdict == VERDICT_FAIL


def test_row_schema_requires_exactly_the_ohlcv_keys() -> None:
    rows = _s0_rows()
    rows[0] = dict(rows[0], extra="adjusted_close")  # type: ignore[dict-item]
    checks = verify_symbol_payload(_payload("SPY", rows), "SPY")
    assert {c.name: c for c in checks}["row_schema"].verdict == VERDICT_FAIL


def test_row_schema_requires_strictly_descending_unique_datetimes() -> None:
    rows = [
        _row("2025-07-30"),
        _row("2025-07-30"),  # duplicate
        _row("2018-04-04"),
    ]
    checks = verify_symbol_payload(_payload("SPY", rows), "SPY")
    assert {c.name: c for c in checks}["row_schema"].verdict == VERDICT_FAIL


def test_nonfinite_and_unparsable_numbers_fail() -> None:
    rows = [_row("2025-07-31", close="NaN"), _row("2025-07-30", close="not-a-number")]
    checks = verify_symbol_payload(_payload("SPY", rows), "SPY")
    assert {c.name: c for c in checks}["numeric_parse"].verdict == VERDICT_FAIL


def test_s0_bar_sanity_detects_broken_ohlc_relationship() -> None:
    rows = [_row("2025-07-31", close="10", high="9")]  # high < close
    checks = verify_symbol_payload(_payload("SPY", rows), "SPY")
    assert {c.name: c for c in checks}["s0_bar_sanity"].verdict == VERDICT_FAIL


def test_value_checks_are_s0_bounded_and_findings_never_record_levels() -> None:
    """A post-S0 (sealed S1) row with a broken OHLC relationship is NOT
    value-checked; findings name dates and relationships, never price
    levels."""
    rows = [
        _row("2025-08-01", close="999999", high="1", low="888888"),  # broken, sealed
        _row("2025-07-31", close="11"),
    ]
    checks = verify_symbol_payload(_payload("SPY", rows), "SPY")
    by_name = {c.name: c for c in checks}
    assert by_name["s0_bar_sanity"].verdict == VERDICT_PASS
    for check in checks:
        assert "999999" not in check.detail and "888888" not in check.detail


# --- split events ------------------------------------------------------------------ #


def test_split_events_pass_on_pinned_ratios() -> None:
    raw_closes = {
        symbol: {"2025-12-04": 100.0, "2025-12-05": 100.0 * ratio}
        for symbol, ratio in PINNED_CLOSE_RATIOS.items()
    }
    check = verify_split_events(raw_closes)
    assert check.verdict == VERDICT_PASS
    assert set(SPLIT_SYMBOLS) == set(PINNED_CLOSE_RATIOS)


def test_split_events_fail_on_drift() -> None:
    raw_closes = {
        symbol: {"2025-12-04": 100.0, "2025-12-05": 100.0 * ratio}
        for symbol, ratio in PINNED_CLOSE_RATIOS.items()
    }
    raw_closes["XLK"]["2025-12-05"] = 100.0  # no split anymore
    check = verify_split_events(raw_closes)
    assert check.verdict == VERDICT_FAIL
    assert "XLK" in check.detail


def test_split_events_fail_on_missing_provenance_closes() -> None:
    check = verify_split_events({"XLK": {"2025-12-04": 100.0}})
    assert check.verdict == VERDICT_FAIL
    assert "unavailable" in check.detail


# --- distribution inputs ------------------------------------------------------------ #


def test_distribution_inputs_pass_and_fail() -> None:
    symbols = ("SPY", "XLK")
    ok = verify_distribution_inputs(
        {"SPY": {"2025-03-21": 1.5}, "XLK": {"2025-03-24": 0.4}}, symbols
    )
    assert ok.verdict == VERDICT_PASS
    missing = verify_distribution_inputs({"SPY": {"2025-03-21": 1.5}}, symbols)
    assert missing.verdict == VERDICT_FAIL
    unparsable = verify_distribution_inputs(
        {"SPY": {"2025-03-21": 1.5}, "XLK": {"bad-date": 0.4}}, symbols
    )
    assert unparsable.verdict == VERDICT_FAIL


# --- TR inputs ------------------------------------------------------------------------ #


def test_tr_inputs_pass_on_clean_synthetic_series() -> None:
    closes = {f"2025-07-{day:02d}": 100.0 + day for day in range(1, 6)}
    dists = {"2025-07-03": 0.5}
    check = verify_tr_inputs({"SPY": closes}, {"SPY": dists}, {"SPY": {}}, ("SPY",))
    assert check.verdict == VERDICT_PASS
    assert "S1 never reconstructed" in check.detail


def test_tr_inputs_fail_on_broken_series() -> None:
    check = verify_tr_inputs({"SPY": {"2025-07-01": 100.0}}, {"SPY": {}}, {}, ("SPY",))
    assert check.verdict == VERDICT_FAIL


# --- calendar --------------------------------------------------------------------------- #


def test_calendar_check_passes_with_injected_official_calendar() -> None:
    check = verify_calendar(USEquityRegularCalendar())
    assert check.verdict == VERDICT_PASS
    assert CALENDAR_DIGEST[:8] in check.detail or "frozen pin" in check.detail


def test_calendar_check_not_run_without_calendar() -> None:
    check = verify_calendar(None)
    assert check.verdict == VERDICT_NOT_RUN
    assert "UNAVAILABLE" not in check.detail and "cannot be assumed" in check.detail


def test_calendar_check_fails_on_digest_drift() -> None:
    class DriftedCalendar:
        @property
        def calendar_manifest_digest(self) -> str:  # property form
            return "f" * 64

        def is_session_day(self, day: date) -> bool:
            return day.weekday() < 5

    check = verify_calendar(DriftedCalendar())
    assert check.verdict == VERDICT_FAIL
    assert "digest" in check.detail


def test_calendar_check_accepts_method_form() -> None:
    """The shared USEquityRegularCalendar exposes the digest as a method or
    property; both forms must be accepted."""
    check = verify_calendar(USEquityRegularCalendar())
    assert check.verdict == VERDICT_PASS


# --- full report shape -------------------------------------------------------------------- #


def test_report_verdict_aggregates_and_serializes() -> None:
    ok = verify_symbol_payload(_payload("SPY", _s0_rows()), "SPY")
    bad_rows = [_row("2025-07-31", close="10", high="1")]
    bad = verify_symbol_payload(_payload("XLK", bad_rows), "XLK")
    report = CohortVerificationReport(
        symbol_reports={"SPY": ok, "XLK": bad},
        cross_checks=(
            verify_split_events(
                {s: {"2025-12-04": 1.0, "2025-12-05": r} for s, r in PINNED_CLOSE_RATIOS.items()}
            ),
        ),
    )
    assert report.verdict == VERDICT_FAIL
    payload = json.loads(report.canonical_json())
    assert payload["verdict"] == VERDICT_FAIL
    assert set(payload["symbols"]) == {"SPY", "XLK"}
