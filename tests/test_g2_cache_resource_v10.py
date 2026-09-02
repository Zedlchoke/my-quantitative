"""V10P-R G2 blockers F2/G-H06 + G17: cache-decision threshold logic + cap math.

Boundary discipline (explicitly requested by the sprint):

* These are UNIT tests over the DECISION LAYER ONLY. Measurements are mocked;
  none of them can produce, fake or substitute the F2 raw-read proof. The
  real raw-read evidence lives exclusively in
  ``research/cache_resource_measure_v10.py`` executed with ``--probe-cache``
  against the real catalog.
* One labelled WIRING test runs the instrumented pipeline against a tiny
  SYNTHETIC catalog to prove the counter/cache plumbing works. It is NOT F2
  evidence and asserts plumbing only.
"""

from __future__ import annotations

import json

import pytest

import research.cache_resource_measure_v10 as crm
from research.cache_v10 import SharedCacheMergeGate
from research.resource_governor_v10 import MIN_RESERVED_RAM_GB


GOOD_UNCACHED = {
    "mode": "off",
    "raw_reads_total": 6,
    "wall_time_s": 2.0,
    "peak_rss_gb": 0.18,
    "result_sha256": "a" * 64,
    "all_pass_digests_equal": True,
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "catalog_bytes": 10_000_000,
    "per_pass": [
        {"pass": i, "raw_reads_this_pass": 2, "ranks_sha256": "a" * 64}
        for i in (1, 2, 3)
    ],
}
GOOD_CACHED = dict(
    GOOD_UNCACHED,
    mode="on",
    raw_reads_total=2,
    wall_time_s=0.8,
    peak_rss_gb=0.16,
    per_pass=[
        {"pass": 1, "raw_reads_this_pass": 2, "ranks_sha256": "a" * 64, "cache_hit": False},
        {"pass": 2, "raw_reads_this_pass": 0, "ranks_sha256": "a" * 64, "cache_hit": True},
        {"pass": 3, "raw_reads_this_pass": 0, "ranks_sha256": "a" * 64, "cache_hit": True},
    ],
)


# --------------------------------------------------------------------------- #
# preregistration sanity (thresholds frozen BEFORE any measurement)
# --------------------------------------------------------------------------- #
def test_preregistered_thresholds_match_audited_gate_constants():
    assert crm.PREREGISTERED_THRESHOLDS["max_raw_reads_cached"] == (
        SharedCacheMergeGate.MAX_RAW_READS_FULL_STRESS
    )
    assert crm.PREREGISTERED_THRESHOLDS["min_wall_time_reduction"] == (
        SharedCacheMergeGate.MIN_WALL_TIME_REDUCTION
    )
    assert crm.PREREGISTERED_THRESHOLDS["require_strict_raw_read_improvement"] is True
    assert crm.RESERVED_RAM_GB >= MIN_RESERVED_RAM_GB


def test_bootstrap_and_producer_identity_are_pinned():
    assert crm.BOOTSTRAP_SHA == "5bb1a90551c8f7823773af713316a45e0ca070cd"
    assert crm.PRODUCER_ROLE == "G2"
    assert set(crm.VALID_VERDICTS) == {
        "PASS",
        "DISABLED_FAIL_CLOSED",
        "FAIL",
        "UNAVAILABLE_FAIL_CLOSED",
    }


# --------------------------------------------------------------------------- #
# decision layer -- mocked measurements only
# --------------------------------------------------------------------------- #
def _evaluate(**overrides):
    available = overrides.pop("available_ram_gb_before", 2.4)
    return crm.evaluate_cache_decision(
        crm.PREREGISTERED_THRESHOLDS,
        uncached=overrides.pop("uncached", GOOD_UNCACHED),
        cached=overrides.pop("cached", GOOD_CACHED),
        available_ram_gb_before=available,
    )


def test_decision_passes_only_when_every_preregistered_gate_holds():
    d = _evaluate()
    assert d["verdict"] == "PASS" and d["enable"] is True
    assert d["reasons"] == [] and d["parity_proof"] is True
    assert d["metrics"]["raw_reads_cached"] == 2
    assert d["metrics"]["raw_reads_uncached"] == 6
    assert d["metrics"]["wall_time_reduction"] == pytest.approx((2.0 - 0.8) / 2.0)


@pytest.mark.parametrize(
    "reads_cached,expected_reason_part",
    [
        (3, "raw_reads_budget_exceeded:3>2"),
        (6, "no_strict_raw_read_improvement:6>=6"),
        (9, "no_strict_raw_read_improvement:9>=6"),
    ],
)
def test_decision_never_enables_when_read_budget_or_improvement_fails(
    reads_cached, expected_reason_part
):
    d = _evaluate(cached=dict(GOOD_CACHED, raw_reads_total=reads_cached))
    assert d["verdict"] == "DISABLED_FAIL_CLOSED" and d["enable"] is False
    assert expected_reason_part in ";".join(d["reasons"])


def test_decision_flags_incorrectness_as_fail_when_byte_parity_breaks():
    drifted = dict(GOOD_CACHED, result_sha256="b" * 64)
    d = _evaluate(cached=drifted)
    assert d["verdict"] == "FAIL" and d["enable"] is False
    assert any(r.startswith("byte_parity_broken") for r in d["reasons"])


def test_decision_rejects_input_surface_mismatch_and_unstable_cache():
    d = _evaluate(
        cached=dict(GOOD_CACHED, symbols=["ETHUSDT"], all_pass_digests_equal=True)
    )
    assert d["verdict"] == "FAIL"
    assert "byte_parity_broken:input_surface_mismatch" in d["reasons"]

    unstable = {**GOOD_CACHED, "all_pass_digests_equal": False}
    d = _evaluate(cached=unstable)
    assert d["verdict"] == "FAIL"
    assert "byte_parity_broken:cached_run_not_deterministic_across_passes" in d["reasons"]


def test_decision_disables_below_wall_target_or_over_host_memory_guard():
    slow = dict(GOOD_CACHED, wall_time_s=1.85)  # reduction 0.075 < 0.30
    d = _evaluate(cached=slow)
    assert d["verdict"] == "DISABLED_FAIL_CLOSED"
    assert any(r.startswith("wall_time_reduction_below_target") for r in d["reasons"])

    fat = dict(GOOD_CACHED, peak_rss_gb=1.5)  # 1.5 GiB > 0.5 * 2.4 GiB guard
    d = _evaluate(cached=fat)
    assert d["verdict"] == "DISABLED_FAIL_CLOSED"
    assert any(r.startswith("cached_rss_exceeds_host_guard") for r in d["reasons"])
    assert d["enable"] is False


def test_decision_missing_measurements_can_never_be_pass():
    for kwargs in (
        {"uncached": None, "cached": None},
        {"cached": None},
        {"uncached": None},
    ):
        d = crm.evaluate_cache_decision(
            crm.PREREGISTERED_THRESHOLDS,
            **kwargs,
            available_ram_gb_before=None,
        )
        assert d["verdict"] == "DISABLED_FAIL_CLOSED" and d["enable"] is False
        assert d["parity_proof"] is None
    # Non-numeric / unfurnished counters fail closed too.
    d = _evaluate(cached=dict(GOOD_CACHED, raw_reads_total="many"))
    assert d["verdict"] == "DISABLED_FAIL_CLOSED"
    assert "raw_read_measurement_missing_or_non_numeric" in d["reasons"]


def test_decision_mixed_failure_still_blocks_and_reports_all_reasons():
    d = _evaluate(
        cached=dict(
            GOOD_CACHED, raw_reads_total=4, wall_time_s=1.9, peak_rss_gb=2.0
        )
    )
    assert d["verdict"] == "DISABLED_FAIL_CLOSED"
    joined = ";".join(d["reasons"])
    assert "raw_reads_budget_exceeded" in joined
    assert "wall_time_reduction_below_target" in joined
    assert "cached_rss_exceeds_host_guard" in joined


# --------------------------------------------------------------------------- #
# G17 cap arithmetic: min(owner_ceiling, measured_safe_cap[, prior])
# --------------------------------------------------------------------------- #
def test_final_cap_is_min_of_owner_ceiling_and_measured_safe_cap():
    # avail 2.42GB, reserve 2GB -> headroom 0.42GB; peak 0.25GB -> floor(1.68)=1
    r = crm.resolve_final_cap(
        owner_ceiling=1,
        available_ram_gb=2.42,
        measured_peak_worker_ram_gb=0.25,
    )
    assert r["measured_safe_cap"] == 1 and r["final_cap"] == 1
    assert r["local_scored_launch_allowed"] is True
    # smaller peak pushes the formula above the owner ceiling -> clamped at 1
    r = crm.resolve_final_cap(
        owner_ceiling=1, available_ram_gb=8.0, measured_peak_worker_ram_gb=0.25
    )
    assert r["measured_safe_cap"] == 24 and r["final_cap"] == 1


def test_zero_headroom_yields_cap_zero_fail_closed_without_override():
    r = crm.resolve_final_cap(
        owner_ceiling=1,
        available_ram_gb=1.5665,          # BELOW the 2GB reserve (v10H case)
        measured_peak_worker_ram_gb=1.25,
    )
    assert r["headroom_gb"] < 0
    assert r["measured_safe_cap"] == 0
    assert r["final_cap"] == 0                     # min(1, 0) == 0
    assert r["local_scored_launch_allowed"] is False
    # Exactly-at-zero headroom is also zero-cap.
    r = crm.resolve_final_cap(
        owner_ceiling=1, available_ram_gb=2.0, measured_peak_worker_ram_gb=0.25
    )
    assert r["final_cap"] == 0


def test_cap_arithmetic_is_monotone_decreasing_in_pressure():
    previous = None
    peak = 0.25
    for avail_gb in [8.0, 4.0, 3.0, 2.5, 2.05, 2.0, 1.99, 1.56, 0.0]:
        r = crm.resolve_final_cap(
            owner_ceiling=1, available_ram_gb=avail_gb, measured_peak_worker_ram_gb=peak
        )
        if previous is not None:
            assert r["final_cap"] <= previous, avail_gb
            assert r["measured_safe_cap"] >= 0
        assert r["final_cap"] <= 1                      # never exceeds ceiling
        previous = r["final_cap"]
    assert previous == 0                                # tightest pressure -> 0


def test_prior_frozen_cap_is_lower_only_monotone_clamp():
    base = dict(
        owner_ceiling=1, available_ram_gb=2.42, measured_peak_worker_ram_gb=0.25
    )
    assert crm.resolve_final_cap(prior_frozen_cap=None, **base)["final_cap"] == 1
    # prior frozen 0 forbids silent promotion back to 1 ...
    raised = crm.resolve_final_cap(prior_frozen_cap=0, **base)
    assert raised["final_cap"] == 0 and raised["monotone_clamp_applied"] is True
    # ... and a prior higher value cannot exceed today's safe cap either.
    lowered = crm.resolve_final_cap(
        prior_frozen_cap=1,
        owner_ceiling=1,
        available_ram_gb=1.0,
        measured_peak_worker_ram_gb=0.25,
    )
    assert lowered["final_cap"] == 0


def test_resolve_final_cap_rejects_invalid_peak_measurement():
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            crm.resolve_final_cap(
                owner_ceiling=1,
                available_ram_gb=3.0,
                measured_peak_worker_ram_gb=bad,
            )


# --------------------------------------------------------------------------- #
# unmeasured artifacts are UNAVAILABLE_FAIL_CLOSED, never PASS
# --------------------------------------------------------------------------- #
def test_write_unavailable_artifacts_records_no_pass(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = crm.write_unavailable_artifacts(
        ["python", "cache_resource_measure_v10.py"],
        repo_root=tmp_path,
        out_dir=tmp_path / "research",
        reasons=["unit_test_unmeasured_path"],
    )
    assert rc == 2
    cache_doc = json.loads((tmp_path / "research" / "cache_decision_v10.json").read_text())
    cap_doc = json.loads((tmp_path / "research" / "resource_cap_report_v10.json").read_text())
    for doc in (cache_doc, cap_doc):
        assert doc["schema_version"] == crm.MODULE_TAG
        assert doc["producer_role"] == "G2"
        assert doc["bootstrap_sha"] == crm.BOOTSTRAP_SHA
        assert doc["exit_code"] == 2
        assert doc["verdict"] == "UNAVAILABLE_FAIL_CLOSED"
        assert doc["measured"] is False
    assert cache_doc["enable"] is False
    assert cap_doc["final_cap"] is None
    assert cap_doc["local_scored_launch_allowed"] is False
    assert "head_sha" in cache_doc and "input_hashes" in cache_doc
    assert "command" in cap_doc and "generated_at" in cap_doc


def test_unmeasured_run_never_downgrades_measured_artifacts(tmp_path, monkeypatch):
    """A no-flag invocation must not silently replace measured evidence."""
    out = tmp_path / "research"
    out.mkdir(parents=True)
    (out / "cache_decision_v10.json").write_text(
        json.dumps({"verdict": "PASS", "measured": True})
    )
    rc = crm.write_unavailable_artifacts(
        ["python", "cache_resource_measure_v10.py"],
        repo_root=tmp_path,
        out_dir=out,
        reasons=["unit_test_guard"],
    )
    assert rc == 3  # refused
    still = json.loads((out / "cache_decision_v10.json").read_text())
    assert still["verdict"] == "PASS" and still["measured"] is True
    # Explicit force downgrades only when the caller asks for it.
    rc_forced = crm.write_unavailable_artifacts(
        ["python", "cache_resource_measure_v10.py"],
        repo_root=tmp_path,
        out_dir=out,
        reasons=["unit_test_guard_forced"],
        overwrite_existing=True,
    )
    assert rc_forced == 2
    downgraded = json.loads((out / "cache_decision_v10.json").read_text())
    assert downgraded["verdict"] == "UNAVAILABLE_FAIL_CLOSED"


# --------------------------------------------------------------------------- #
# WIRING test (synthetic catalog) -- plumbing only, NOT F2 evidence
# --------------------------------------------------------------------------- #
_PRICE_SCALE = 10 ** 16


def _write_synthetic_catalog(root, symbols, days=4, bars_per_day=96):
    """Tiny nautilus-shaped bar catalog so research.panel._read_bars can read it."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    day_ns = 86_400_000_000_000
    start_ns = 1_755_658_800_000_000_000  # an arbitrary UTC instant
    schema = pa.schema(
        [
            ("ts_event", pa.int64()),
            ("open", pa.binary(16)),
            ("high", pa.binary(16)),
            ("low", pa.binary(16)),
            ("close", pa.binary(16)),
            ("volume", pa.binary(16)),
        ]
    )

    def enc(x: float) -> bytes:
        return int(round(x * _PRICE_SCALE)).to_bytes(16, "little", signed=True)

    part_ns = day_ns // bars_per_day
    for sym in symbols:
        directory = root / "data" / "binance_bar" / f"{sym}-PERP.BINANCE-{crm.BAR_TYPE_LABEL}"
        directory.mkdir(parents=True, exist_ok=True)
        rows = []
        px = 100.0
        for d in range(days):
            for k in range(bars_per_day):
                px += 0.01
                rows.append(
                    {
                        "ts_event": start_ns + d * day_ns + k * part_ns,
                        "open": enc(px),
                        "high": enc(px),
                        "low": enc(px),
                        "close": enc(px),
                        "volume": enc(1.0),
                    }
                )
        pq.write_table(pa.Table.from_pylist(rows, schema=schema), directory / "part.parquet")


def test_instrumentation_counts_reads_and_cache_prevents_reload(tmp_path):
    """WIRING ONLY: the shim counts real read_table calls and the process-local
    cache suppresses re-reads across passes on repeat identical workloads."""
    symbols = ["AAUSDT", "BBUSDT"]
    _write_synthetic_catalog(tmp_path, symbols)
    off = crm.run_representative_pipeline(
        catalog_path=tmp_path / "data" / "..",
        window_start_iso="2025-07-22",
        window_end_iso="2025-08-21",
        cache_mode="off",
        passes=3,
    )
    assert off["raw_reads_total"] == 3 * len(symbols)      # every pass re-reads
    assert all(not p["cache_hit"] for p in off["per_pass"])
    assert off["rows_last_pass"] > 0

    on = crm.run_representative_pipeline(
        catalog_path=tmp_path / "data" / "..",
        window_start_iso="2025-07-22",
        window_end_iso="2025-08-21",
        cache_mode="on",
        passes=3,
    )
    assert on["per_pass"][0]["raw_reads_this_pass"] == len(symbols)   # cold load
    assert sum(p["raw_reads_this_pass"] for p in on["per_pass"][1:]) == 0
    assert on["raw_reads_total"] < off["raw_reads_total"]
    assert on["result_sha256"] == off["result_sha256"]     # identical output


def test_decide_from_wiring_measurements_end_to_end(tmp_path):
    """Same synthetic pipeline feeding the pure decision layer directly."""
    symbols = ["CCUSDT"]
    _write_synthetic_catalog(tmp_path, symbols)
    common = dict(
        catalog_path=tmp_path / "data" / "..",
        window_start_iso="2025-07-22",
        window_end_iso="2025-08-21",
    )
    uncached = crm.run_representative_pipeline(cache_mode="off", passes=3, **common)
    cached = crm.run_representative_pipeline(cache_mode="on", passes=3, **common)
    d = crm.evaluate_cache_decision(
        crm.PREREGISTERED_THRESHOLDS,
        uncached=uncached,
        cached=cached,
        available_ram_gb_before=2.4,
    )
    # On the synthetic workload every structural gate holds except possibly the
    # strict 30% wall target, which stays enforced even here (fail closed).
    assert d["verdict"] in {"PASS", "DISABLED_FAIL_CLOSED"}
    if d["verdict"] == "DISABLED_FAIL_CLOSED":
        assert all(
            r.startswith("wall_time_reduction") for r in d["reasons"]
        ), d["reasons"]
