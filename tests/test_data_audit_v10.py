"""A6 data/PIT gate tests (PLAN.md section 6 H07-data).

Synthetic fixtures only — tiny fake catalog trees built inside tmp dirs;
the real ``catalog_live_crypto`` tree is never touched here. Coverage:

* :func:`research.data_audit_v10.catalog_hash` — run-to-run stability,
  root-independence (identical content under two roots -> same merkle),
  tamper sensitivity, count/byte accounting, empty-tree determinism;
* :func:`research.data_audit_v10.audit_s0_window` — full-coverage PASS,
  seeded gap -> GAP_FAIL, required symbol missing entirely ->
  MISSING_REQUIRED with overall FAIL_MISSING_REQUIRED (fail-closed),
  benchmark-context symbols cannot flip the gate, ISO window parsing;
* :func:`research.data_audit_v10.clock_audit` — clean fixture PASS; each
  seeded defect (off-grid bar stamp, non-monotonic stamps, duplicates,
  funding off its 8h boundary) flips exactly the expected row to FAIL;
* :func:`research.data_audit_v10.warmup_purge_audit` — contract-compliant
  inputs PASS; short purge+embargo vs holding horizon, warmup inside OOS
  and warmup extending before data start each FAIL with named checks;
* :func:`research.data_audit_v10.write_audit_report` — atomic JSON writer:
  payload round-trips, no tmp leftovers, safe overwrite.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from research.data_audit_v10 import (
    AuditInputError,
    INTERVAL_NS,
    audit_s0_window,
    catalog_hash,
    clock_audit,
    ns_to_iso,
    parse_window_ns,
    warmup_purge_audit,
    write_audit_report,
)

BASE_NS = int(
    datetime(2025, 8, 21, tzinfo=timezone.utc).timestamp()
) * 1_000_000_000


def grid_stamps(count: int, start_ns: int = BASE_NS,
                step_ns: int = INTERVAL_NS) -> list[int]:
    return [start_ns + i * step_ns for i in range(count)]


def make_tree(root: Path, files: dict[str, bytes]) -> Path:
    for rel, payload in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return root


# --------------------------------------------------------------------------- #
# catalog_hash
# --------------------------------------------------------------------------- #
def test_catalog_hash_stable_across_two_runs(tmp_path):
    make_tree(tmp_path, {
        "data/a.csv": b"ts,px\n1,2\n",
        "data/sub/b.bin": bytes(range(256)),
        "top.txt": b"hello",
    })
    first = catalog_hash(tmp_path)
    second = catalog_hash(tmp_path)
    assert first == second
    assert first["file_count"] == 3
    assert first["total_bytes"] == len(b"ts,px\n1,2\n") + 256 + 5
    assert len(first["merkle_root_hex"]) == 64


def test_catalog_hash_identical_content_different_roots(tmp_path):
    tree = {"x/f.parquet": b"\x01\x02\x03", "y/g.csv": b"a,b\n1,2\n"}
    root_a = make_tree(tmp_path / "root_a", tree)
    root_b = make_tree(tmp_path / "totally-different-name", tree)
    ha, hb = catalog_hash(root_a), catalog_hash(root_b)
    assert ha["merkle_root_hex"] == hb["merkle_root_hex"]
    assert ha["root"] != hb["root"]


def test_catalog_hash_tamper_changes_merkle(tmp_path):
    root_a = make_tree(tmp_path / "a", {"f.bin": b"original-bytes"})
    root_b = make_tree(tmp_path / "b", {"f.bin": b"tampered-bytes!"})
    assert (
        catalog_hash(root_a)["merkle_root_hex"]
        != catalog_hash(root_b)["merkle_root_hex"]
    )


def test_catalog_hash_empty_tree_and_missing_root(tmp_path):
    (tmp_path / "empty").mkdir()
    empty = catalog_hash(tmp_path / "empty")
    assert empty["file_count"] == 0 and empty["total_bytes"] == 0
    again = catalog_hash(tmp_path / "empty")
    assert empty["merkle_root_hex"] == again["merkle_root_hex"]
    with pytest.raises(AuditInputError):
        catalog_hash(tmp_path / "does-not-exist")


# --------------------------------------------------------------------------- #
# audit_s0_window
# --------------------------------------------------------------------------- #
GOOD_MANIFEST = {
    "selected_symbols": [{"symbol": "ALPHA"}, {"symbol": "BETA"}],
    "btc_benchmark_context_only": {"symbol": "BTCCTX"},
}


def _report(**by_symbol: list[int]) -> dict:
    return {"symbols": {sym: {"ts_event_ns": stamps} for sym, stamps in by_symbol.items()}}


def test_s0_window_pass_on_full_coverage():
    stamps = grid_stamps(96)  # one full day of 15m slots
    report = audit_s0_window(
        _report(ALPHA=stamps, BETA=list(stamps), BTCCTX=list(stamps)),
        GOOD_MANIFEST,
        BASE_NS,
        BASE_NS + 96 * INTERVAL_NS - 1,
    )
    assert report["status"] == "PASS"
    assert report["per_symbol"]["ALPHA"]["verdict"] == "PASS"
    assert report["per_symbol"]["ALPHA"]["coverage_fraction"] == 1.0
    assert report["per_symbol"]["BTCCTX"]["role"] == "benchmark_context_only"


def test_s0_window_gap_seeded_fails_required_symbol():
    stamps = grid_stamps(96)
    gapped = stamps[:40] + stamps[48:]           # 8 missing slots mid-window
    report = audit_s0_window(
        _report(ALPHA=gapped, BETA=list(stamps)),
        GOOD_MANIFEST,
        BASE_NS,
        BASE_NS + 96 * INTERVAL_NS - 1,
    )
    row = report["per_symbol"]["ALPHA"]
    assert row["verdict"] == "GAP_FAIL"
    assert row["gap_event_count"] == 1
    assert row["gap_census"][0]["missing_grid_slots"] == 8
    assert abs(row["coverage_fraction"] - 88 / 96) < 1e-6
    assert report["status"] == "FAIL"
    assert "ALPHA" in report["failed_required_symbols"]


def test_s0_window_missing_required_symbol_fail_closed():
    stamps = grid_stamps(96)
    report = audit_s0_window(
        _report(ALPHA=list(stamps)),            # BETA entirely absent
        GOOD_MANIFEST,
        BASE_NS,
        BASE_NS + 96 * INTERVAL_NS - 1,
    )
    beta = report["per_symbol"]["BETA"]
    assert beta["verdict"] == "MISSING_REQUIRED"
    assert beta["bar_count"] == 0
    assert report["status"] == "FAIL_MISSING_REQUIRED"
    assert report["missing_required_symbols"] == ["BETA"]


def test_s0_window_benchmark_cannot_flip_gate_but_required_shortfall_does():
    stamps = grid_stamps(96)
    # benchmark has zero bars; required BETA late by half a slot-grid shortfall
    report = audit_s0_window(
        _report(ALPHA=list(stamps), BETA=stamps[:90]),
        GOOD_MANIFEST,
        BASE_NS,
        BASE_NS + 96 * INTERVAL_NS - 1,
    )
    assert report["per_symbol"]["BTCCTX"]["verdict"] == "GAP_FAIL"
    assert "BTCCTX" not in report["failed_required_symbols"]
    assert report["status"] == "FAIL"
    assert report["per_symbol"]["BETA"]["reasons"] == ["coverage_below_full"]


def test_s0_window_accepts_iso_window_edges():
    stamps = grid_stamps(4)                     # :00 :15 :30 :45
    report = audit_s0_window(
        _report(ALPHA=stamps), GOOD_MANIFEST,
        "2025-08-21T00:00:00Z", "2025-08-21T00:45:00Z",
    )
    assert report["window_start_ns"] == BASE_NS
    assert report["per_symbol"]["ALPHA"]["coverage_fraction"] == 1.0


def test_parse_window_ns_rejects_bad_order():
    with pytest.raises(AuditInputError):
        parse_window_ns(BASE_NS + 100, BASE_NS)


# --------------------------------------------------------------------------- #
# clock_audit
# --------------------------------------------------------------------------- #
def good_clock_inputs():
    bars = grid_stamps(96)
    funding = [BASE_NS + h * 8 * 3_600 * 1_000_000_000 for h in range(3)]
    oi = grid_stamps(24)
    mark = grid_stamps(24)
    return bars, funding, oi, mark


def test_clock_audit_passes_clean_fixture():
    report = clock_audit(*good_clock_inputs())
    assert report["verdict"] == "PASS"
    assert report["failed_checks"] == []
    assert all(row["status"] == "PASS" for row in report["checks"])
    assert report["rows_total"] == {"bars": 96, "funding": 3,
                                    "open_interest": 24, "mark": 24}


def test_clock_audit_off_grid_bar_stamp_fails_only_that_row():
    bars, funding, oi, mark = good_clock_inputs()
    bars[7] += 60 * 1_000_000_000                  # +1min off the 15m grid
    report = clock_audit(bars, funding, oi, mark)
    bad = [r for r in report["checks"] if r["status"] != "PASS"]
    assert [(r["stream"], r["check"]) for r in bad] == [
        ("bars", "bar_close_grid_alignment")
    ]
    assert report["verdict"] == "FAIL"


def test_clock_audit_duplicate_and_non_monotonic_fail():
    bars, funding, oi, mark = good_clock_inputs()
    dup = bars + [bars[10]]
    shuffled = bars[:10] + [bars[12]] + [bars[11]] + bars[13:]
    report_dup = clock_audit(dup, funding, oi, mark)
    report_mono = clock_audit(shuffled, funding, oi, mark)
    assert ("bars", "no_duplicate_timestamps") in [
        (r["stream"], r["check"]) for r in report_dup["checks"] if r["status"] != "PASS"
    ]
    assert ("bars", "monotonic_strict") in [
        (r["stream"], r["check"]) for r in report_mono["checks"] if r["status"] != "PASS"
    ]


def test_clock_audit_funding_off_boundary_fails_and_config_respected():
    bars, funding, oi, mark = good_clock_inputs()
    skewed = list(funding)
    skewed[1] += 10 * 60 * 1_000_000_000           # +10min past the 8h slot
    report = clock_audit(bars, skewed, oi, mark)
    failed = {(r["stream"], r["check"]) for r in report["checks"] if r["status"] != "PASS"}
    assert ("funding", "funding_boundary_alignment") in failed
    assert report["config"]["funding_interval_hours"] == 8

    custom = clock_audit(bars, funding, oi, mark, funding_interval_ns=4 * 3_600 * 1_000_000_000)
    assert custom["verdict"] == "PASS"
    assert custom["config"]["funding_interval_hours"] == 4


# --------------------------------------------------------------------------- #
# warmup_purge_audit
# --------------------------------------------------------------------------- #
def test_warmup_purge_pass_with_boundaries():
    report = warmup_purge_audit(
        window_start=1000, window_end=2000,
        warmup_bars=500, purge_bars=20, embargo_bars=30,
        holding_horizon_bars=50,
    )
    assert report["verdict"] == "PASS"
    b = report["boundary_indices"]
    assert b["warmup_start"] == 500 and b["warmup_end"] == 1000
    assert b["train_effective_end"] == 980
    assert b["embargo_zone"] == [2000, 2030]
    assert b["next_evaluable_index"] == 2030


def test_warmup_purge_short_purge_embargo_fails():
    report = warmup_purge_audit(1000, 2000, 500, 10, 30, 50)
    assert report["verdict"] == "FAIL"
    assert "purge_embargo_ge_holding" in report["failed_checks"]


def test_warmup_inside_oos_fails():
    report = warmup_purge_audit(1000, 2000, -5, 20, 30, 50)
    assert report["verdict"] == "FAIL"
    assert "warmup_outside_oos" in report["failed_checks"]


def test_warmup_extending_before_data_start_fails():
    report = warmup_purge_audit(10, 2000, 50, 20, 30, 50)
    assert report["verdict"] == "FAIL"
    assert "warmup_within_data" in report["failed_checks"]


def test_empty_window_fails():
    report = warmup_purge_audit(1000, 1000, 100, 20, 30, 50)
    assert "window_valid" in report["failed_checks"]


# --------------------------------------------------------------------------- #
# write_audit_report
# --------------------------------------------------------------------------- #
def test_write_audit_report_atomic_roundtrip_and_overwrite(tmp_path):
    target = tmp_path / "nested" / "report.json"
    payload = {"b": 2, "a": [1, {"k": "v"}], "label": "S0_ALREADY_INSPECTED"}
    out = write_audit_report(payload, target)
    assert out == target
    loaded = json.loads(target.read_text())
    assert loaded == payload
    leftovers = [p for p in target.parent.iterdir() if p.name != target.name]
    assert leftovers == []

    write_audit_report({"replaced": True}, target)
    assert json.loads(target.read_text()) == {"replaced": True}
