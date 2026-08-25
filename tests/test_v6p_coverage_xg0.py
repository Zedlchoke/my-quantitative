"""V6P A3 negative fixtures: measured XG0 coverage wiring (N08/N09).

Covers the real-path adapter contract without touching real data catalogs:
coverage blocks are fabricated, then mapped through
``_coverage_payload_from_execution`` and judged by ``_evaluate_xg0``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research.protocol.gates import XGateInputs, _evaluate_xg0  # noqa: E402
from research.portfolio_runner import _coverage_payload_from_execution  # noqa: E402


def _execution(**overrides):
    base = {
        "benchmark_btc_clean": True,
        "panel_coverage": {
            "days_per_symbol": {"ETHUSDT": 365, "SOLUSDT": 365},
            "btc_days": 365,
            "blocks": {
                "bar_coverage": {"ETHUSDT": 365, "SOLUSDT": 365, "BTCUSDT": 365},
                "benchmark_coverage": {"BTCUSDT": 365},
                "funding_coverage": {
                    "ETHUSDT": {"settlements": 1095, "first": "2025-08-21",
                                "last": "2026-08-21"},
                    "SOLUSDT": {"settlements": 1095, "first": "2025-08-21",
                                "last": "2026-08-21"},
                },
                "metadata_coverage": {"ETHUSDT": True, "SOLUSDT": True},
            },
            "traded_symbols_detail": {
                "ETHUSDT": {"days_present": 365, "duplicate_bars": 0,
                            "gap_bars": 0},
                "SOLUSDT": {"days_present": 365, "duplicate_bars": 0,
                            "gap_bars": 0},
            },
            "requested_window": ["2025-08-21T14:30Z", "2026-08-21T00:00Z"],
            "effective_common_window": ["2025-08-21T14:30Z", "2026-08-20T23:45Z"],
            "funding_bundle_identity": {"path": "funding_data/scan_2026",
                                        "files_sha256": {"ETHUSDT": "a" * 64,
                                                         "SOLUSDT": "b" * 64}},
        },
    }
    base.update(overrides)
    return base


def _payload(execution, required_days=365):
    return _coverage_payload_from_execution(
        execution, declared_symbols=["ETHUSDT", "SOLUSDT"],
        required_days=required_days)


def _xg0(payload):
    return _evaluate_xg0(XGateInputs(coverage=payload))


def test_full_coverage_passes_with_measured_blocks():
    res = _xg0(_payload(_execution()))
    assert res.verdict.value == "PASS", res.reasons


def test_missing_btc_emits_only_benchmark_reason():
    ex = _execution()
    ex["panel_coverage"]["btc_days"] = 0
    ex["panel_coverage"]["blocks"]["benchmark_coverage"] = {"BTCUSDT": 0}
    ex["benchmark_btc_clean"] = False
    res = _xg0(_payload(ex))
    assert res.verdict.value == "FAIL"
    assert "benchmark_coverage_incomplete" in res.reasons
    assert "funding_coverage_insufficient" not in res.reasons


def test_short_traded_bars_emit_coverage_below_declared():
    ex = _execution()
    ex["panel_coverage"]["traded_symbols_detail"]["ETHUSDT"]["days_present"] = 300
    res = _xg0(_payload(ex))
    assert "coverage_below_declared" in res.reasons


def test_gap_counter_surfaces_unexplained_gap_reason():
    ex = _execution()
    ex["panel_coverage"]["traded_symbols_detail"]["SOLUSDT"]["gap_bars"] = 3
    res = _xg0(_payload(ex))
    assert "unexplained_gap" in res.reasons


def test_funding_block_flags_fail_closed_without_settlements():
    payload = _payload(_execution())
    entry = payload["traded_symbols"]["ETHUSDT"]
    assert entry["funding"]["bundle_present"] is True
    assert entry["funding"]["covers_declared_window"] is True

    ex = _execution()
    ex["panel_coverage"]["blocks"]["funding_coverage"]["ETHUSDT"] = {
        "settlements": 0, "first": None, "last": None}
    payload2 = _payload(ex)
    entry2 = payload2["traded_symbols"]["ETHUSDT"]
    assert entry2["funding"]["bundle_present"] is False
    assert entry2["funding"]["covers_declared_window"] is False


def test_metadata_absent_is_flagged_not_assumed():
    ex = _execution()
    ex["panel_coverage"]["blocks"]["metadata_coverage"]["SOLUSDT"] = False
    payload = _payload(ex)
    assert payload["traded_symbols"]["SOLUSDT"]["instrument_metadata_present"] is False


def test_bundle_identity_hashes_are_carried_through():
    payload = _payload(_execution())
    ident = payload["funding_bundle_identity"]
    assert ident["files_sha256"]["ETHUSDT"] == "a" * 64
