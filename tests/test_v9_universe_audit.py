"""Unit tests for the V9 cohort-10 universe + data audit (owner: A2).

Covers the four mandated properties plus supporting pure helpers:
  * deterministic rerun identity (byte-identical artifacts across runs,
    including reproduction of the COMMITTED artifact bytes);
  * BTC exclusion from the traded top-10 (benchmark context only);
  * zero unexplained gaps over both windows (documented ETH
    capture-boundary class is the only permitted explained run);
  * funding held-exposure completeness checker (synthetic bundles).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.v9_universe_audit import (
    DEFAULT_AUDIT_OUT,
    DEFAULT_GATE_OUT,
    DEFAULT_MANIFEST_OUT,
    GATE_ID,
    REPO_ROOT,
    PinVerificationError,
    _pinned_exact_volume,
    close_stamp_iso,
    intersection_range,
    listing_age_check,
    load_pinned_selection,
)
from scripts.v8x_crypto_universe_selection import (
    BAR_INTERVAL_S,
    MAX_FUNDING_INTERVAL_S,
    PRE_END_S,
    PRE_START_S,
    SCORED_END_S,
    SCORED_START_S,
    analyze_funding,
    build_corroboration,
)

ARTIFACTS = (
    DEFAULT_MANIFEST_OUT,
    DEFAULT_AUDIT_OUT,
    DEFAULT_GATE_OUT,
)


# --------------------------------------------------------------------------- #
# Module-scoped fixture: run the full offline audit twice into tmp dirs
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def rerun_pair(tmp_path_factory):
    """Two independent full audit runs; returns (run1_dir, run2_dir)."""
    from scripts.v9_universe_audit import main

    d1 = tmp_path_factory.mktemp("v9_run1")
    d2 = tmp_path_factory.mktemp("v9_run2")
    outs1 = {a.name: d1 / a.name for a in ARTIFACTS}
    outs2 = {a.name: d2 / a.name for a in ARTIFACTS}
    main(manifest_out=outs1[ARTIFACTS[0].name],
         audit_out=outs1[ARTIFACTS[1].name],
         gate_out=outs1[ARTIFACTS[2].name])
    main(manifest_out=outs2[ARTIFACTS[0].name],
         audit_out=outs2[ARTIFACTS[1].name],
         gate_out=outs2[ARTIFACTS[2].name])
    return d1, d2


@pytest.fixture(scope="module")
def docs(rerun_pair):
    """Parsed (manifest, audit, gate) from the FIRST rerun directory."""
    d1, _ = rerun_pair
    read = lambda p: json.loads((d1 / Path(p).name).read_text())  # noqa: E731
    return read(DEFAULT_MANIFEST_OUT), read(DEFAULT_AUDIT_OUT), read(DEFAULT_GATE_OUT)


# --------------------------------------------------------------------------- #
# 1. Deterministic rerun identity
# --------------------------------------------------------------------------- #
def test_deterministic_rerun_byte_identical(rerun_pair):
    d1, d2 = rerun_pair
    for artifact in ARTIFACTS:
        b1 = (d1 / artifact.name).read_bytes()
        b2 = (d2 / artifact.name).read_bytes()
        assert b1 == b2, f"{artifact.name} differs between runs"


def test_rerun_reproduces_committed_artifact_bytes(rerun_pair):
    """The committed deliverables are exactly what an offline rerun produces."""
    d1, _ = rerun_pair
    for artifact in ARTIFACTS:
        assert artifact.exists(), f"committed artifact missing: {artifact}"
        assert (d1 / artifact.name).read_bytes() == artifact.read_bytes(), (
            f"committed {artifact.name} not reproducible"
        )


# --------------------------------------------------------------------------- #
# 2. BTC exclusion (benchmark measurement-only)
# --------------------------------------------------------------------------- #
def test_btc_excluded_from_traded_top10(docs):
    manifest, audit, gate = docs
    assert manifest["btc_excluded"] is True
    selected = [c["symbol"] for c in manifest["selected_symbols"]]
    assert len(selected) == 10
    assert "BTCUSDT" not in selected
    # benchmark context present but flagged measurement-only
    ctx = manifest["btc_benchmark_context_only"]
    assert ctx["symbol"] == "BTCUSDT"
    assert ctx["excluded_from_ranks_weights_pnl"] is True
    assert ctx["context_summary"]["role"] == (
        "benchmark_measurement_only_excluded_from_ranking")
    # normalized block keeps BTC as context role, never 'required'
    assert manifest["normalized"]["symbols"]["BTCUSDT"]["role"] == (
        "benchmark_context_only")
    assert all(
        s["role"] == "required"
        for k, s in manifest["normalized"]["symbols"].items() if k != "BTCUSDT"
    )
    assert audit["btc_exclusion_check"]["in_selected_ten"] is False
    btc_gate_check = next(
        c for c in gate["checks"]
        if c["id"] == "btc_excluded_from_traded_universe")
    assert btc_gate_check["ok"] is True


# --------------------------------------------------------------------------- #
# 3. Zero unexplained gaps over both windows
# --------------------------------------------------------------------------- #
def test_zero_unexplained_gaps_both_windows(docs):
    manifest, audit, gate = docs
    gc = audit["gap_census"]
    assert gc["slots_checked_total"] > 0
    assert gc["gaps_found_total"] == 57  # documented ETH capture-boundary run
    assert gc["unexplained_gaps_total"] == 0
    for run in gc["documented_gap_classes_present"]:
        assert run["explained"] is True
        assert run["cause"] in {
            "local_capture_boundary_between_sessions",
            "local_capture_starts_after_window_start",
            "local_capture_ends_before_window_end",
        }
    assert gc["non_boundary_explained_classes"] == []
    # per-symbol consistency: no census anywhere reports unexplained slots
    for sym, blocks in gc["per_symbol"].items():
        for wname, cen in blocks.items():
            assert cen["expected_15m_slots"] > 0
            assert cen["unexplained_gaps"] == 0, (sym, wname)
    gate_check = next(
        c for c in gate["checks"]
        if c["id"] == "gap_census_unexplained_zero_both_windows")
    assert gate_check["ok"] is True


def test_window_constants_and_measured_scored_window(docs):
    manifest, audit, _ = docs
    pre = audit["windows"]["pre_window"]
    assert (pre["start_utc"], pre["end_utc"]) == (
        "2025-07-22T00:00:00Z", "2025-08-21T00:00:00Z")
    contract = audit["windows"]["scored_window_contract"]
    assert (contract["start_utc"], contract["end_utc"]) == (
        "2025-08-21T00:00:00Z", "2026-08-21T00:00:00Z")
    measured = manifest["scored_window"]
    assert measured["start_utc"] >= contract["start_utc"]
    assert measured["end_utc"] <= contract["end_utc"]
    assert measured["start_utc"] < measured["end_utc"]


# --------------------------------------------------------------------------- #
# 4. Funding held-exposure completeness checker (synthetic bundles)
# --------------------------------------------------------------------------- #
EIGHT_H_MS = MAX_FUNDING_INTERVAL_S * 1000
HOUR_MS = 3_600_000


def _rows(times_ms):
    return [{"fundingTime": int(t), "fundingRate": "0.00010000",
             "markPrice": "1.0"} for t in times_ms]


def _span_series(step_ms=EIGHT_H_MS, drop=None):
    """Settlements covering [SCORED_START - 8h, SCORED_END] inclusive."""
    start = (SCORED_START_S * 1000) - EIGHT_H_MS
    end = SCORED_END_S * 1000
    times = list(range(start, end + step_ms, step_ms))
    if drop is not None:
        del times[drop]
    return times


def test_funding_checker_complete_bundle_passes_all_gates():
    res = analyze_funding(_rows(_span_series()), {})
    assert res["complete"] is True
    assert res["gate_sorted_unique_f1"] is True
    assert res["gate_legal_intervals_f2"] is True
    assert res["gate_boundary_coverage_f3"] is True
    assert res["flagged_interval_steps"] == []
    assert res["settlements_in_exposure_span"] >= 1090


def test_funding_checker_missing_settlement_breaks_legality():
    # dropping one 8h settlement creates a 16h interval -> illegal -> fail
    res = analyze_funding(_rows(_span_series(drop=500)), {})
    assert res["complete"] is False
    assert res["gate_legal_intervals_f2"] is False
    assert 57600 in res["distinct_interval_seconds"]


def test_funding_checker_duplicate_timestamps_fail():
    times = _span_series()
    times.insert(300, times[300])  # exact duplicate stamp
    res = analyze_funding(_rows(sorted(times)), {})
    assert res["duplicate_timestamps"] >= 1
    assert res["gate_sorted_unique_f1"] is False
    assert res["complete"] is False


def test_funding_checker_head_boundary_shortfall_fails():
    # first settlement arrives AFTER exposure_start + 8h -> f3 fails
    times = _span_series()[3:]
    res = analyze_funding(_rows(times), {})
    assert res["gate_boundary_coverage_f3"] is False
    assert res["complete"] is False


def test_funding_checker_tail_boundary_shortfall_fails():
    times = _span_series()[:-3]
    res = analyze_funding(_rows(times), {})
    assert res["gate_boundary_coverage_f3"] is False
    assert res["complete"] is False


def test_funding_checker_empty_bundle_fails_closed():
    res = analyze_funding([], {})
    assert res["complete"] is False
    assert res["first_settlement_utc"] is None


def test_corroborated_exchange_wide_step_is_explained():
    # three symbols run an HOURLY cadence but share ONE identical 8h step;
    # cross-symbol corroboration (>=2 sharers) marks it exchange-wide.
    t0 = SCORED_START_S * 1000
    shared_a, shared_b = t0 + 1000 * HOUR_MS, t0 + 1008 * HOUR_MS

    def hourly_with_shared_step():
        times = list(range(t0 - EIGHT_H_MS, SCORED_END_S * 1000, HOUR_MS))
        times = [t for t in times if not (shared_a < t < shared_b)]
        return times

    funding_by_sym = {
        "AAAUSDT": _rows(hourly_with_shared_step()),
        "BBBUSDT": _rows(hourly_with_shared_step()),
        "CCCUSDT": _rows(hourly_with_shared_step()),
    }
    corroborate = build_corroboration(funding_by_sym)
    res = analyze_funding(funding_by_sym["AAAUSDT"], corroborate)
    assert res["cadence_mode_minutes"] == 60
    steps = res["flagged_interval_steps"]
    assert len(steps) == 1
    assert steps[0]["symbols_sharing_identical_step"] >= 2
    assert steps[0]["cause"] == "exchange_wide_funding_interval_step"
    assert steps[0]["explained"] is True
    assert res["complete"] is True


def test_isolated_interval_step_is_unexplained_and_fails():
    t0 = SCORED_START_S * 1000
    shared_a, shared_b = t0 + 1000 * HOUR_MS, t0 + 1008 * HOUR_MS

    def hourly_with_shared_step():
        times = list(range(t0 - EIGHT_H_MS, SCORED_END_S * 1000, HOUR_MS))
        return [t for t in times if not (shared_a < t < shared_b)]

    def plain_hourly():
        return list(range(t0 - EIGHT_H_MS, SCORED_END_S * 1000, HOUR_MS))

    # NO other symbol carries the identical step -> isolated -> unexplained
    corroborate = build_corroboration({
        "AAAUSDT": _rows(hourly_with_shared_step()),
        "BBBUSDT": _rows(plain_hourly()),
    })
    res = analyze_funding(_rows(hourly_with_shared_step()), corroborate)
    steps = res["flagged_interval_steps"]
    assert len(steps) == 1
    assert steps[0]["cause"] == "unexplained_isolated_interval_step"
    assert res["complete"] is False


# --------------------------------------------------------------------------- #
# Supporting pure helpers
# --------------------------------------------------------------------------- #
def test_intersection_range_takes_max_start_min_end():
    r = {"A": (100, 900), "B": (150, 800), "C": (200, 850)}
    assert intersection_range(r) == (200, 800)
    assert intersection_range({}) == (None, None)


def test_close_stamp_iso_adds_bar_interval():
    assert close_stamp_iso(PRE_START_S - BAR_INTERVAL_S) == "2025-07-22T00:00:00Z"
    assert close_stamp_iso(SCORED_END_S - BAR_INTERVAL_S) == "2026-08-21T00:00:00Z"


def test_listing_age_check_gate_at_365d():
    cutoff_ok_inst = {"onboard_date_utc": "2024-08-01T00:00:00Z",
                      "onboard_ms": (SCORED_START_S - 400 * 86400) * 1000}
    young_inst = {"onboard_date_utc": "2025-09-01T00:00:00Z",
                  "onboard_ms": (SCORED_START_S + 10 * 86400) * 1000}
    none_inst = {"onboard_date_utc": None, "onboard_ms": None}
    assert listing_age_check(cutoff_ok_inst, SCORED_START_S)["ok"] is True
    assert listing_age_check(young_inst, SCORED_START_S)["ok"] is False
    assert listing_age_check(none_inst, SCORED_START_S)["ok"] is False


def test_load_pinned_selection_rejects_wrong_sha(tmp_path):
    bad_root = tmp_path / "repo"
    (bad_root / "data" / "v8x_manifests").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "data" / "v8x_manifests" /
                "crypto_universe_selection.json",
                bad_root / "data" / "v8x_manifests" /
                "crypto_universe_selection.json")
    with pytest.raises(PinVerificationError):
        load_pinned_selection(repo_root=bad_root,
                              pinned_manifest_sha256="0" * 64)


def test_pinned_selection_loader_returns_verified_source():
    pinned, source_block = load_pinned_selection()
    assert pinned["schema_version"] == "2.0.0"
    assert source_block["sha256"] == (
        "e73c703f5fb4dea7ff0c6c2c6c8c756b12218fa1960bf46c0ebb2509abb56376")
    assert len(pinned["chosen_top10"]) == 10
    assert "BTCUSDT" not in [c["symbol"] for c in pinned["chosen_top10"]]


def test_pinned_exact_volume_lookup_matches_chosen_entry():
    pinned, _ = load_pinned_selection()
    entry = pinned["chosen_top10"][0]
    expected = next(
        c["volume"]["median_daily_quote_volume_usdt_exact"]
        for c in pinned["candidates_evaluated"]
        if c["symbol"] == entry["symbol"])
    assert _pinned_exact_volume(pinned, entry["symbol"]) == expected
    with pytest.raises(KeyError):
        _pinned_exact_volume(pinned, "NOTAREALSYMBOL")


# --------------------------------------------------------------------------- #
# Gate document shape
# --------------------------------------------------------------------------- #
def test_gate_document_shape_and_status(docs):
    _, _, gate = docs
    assert gate["artifact"] == "t02_gate_v9"
    assert gate["gate"] == GATE_ID == "P03/P04"
    assert gate["status"] == "PASS", [
        c for c in gate["checks"] if not c["ok"]]
    ids = [c["id"] for c in gate["checks"]]
    assert len(ids) == len(set(ids))
    for key in ("selected_symbols", "btc_excluded", "normalized_manifest_sha256"):
        assert key in gate
