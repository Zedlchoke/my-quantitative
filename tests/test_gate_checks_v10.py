"""A10 tests for the machine-readable V9H gate evaluator (research.gate_checks_v10).

Covers every gate's PASS / FAIL / UNAVAILABLE_FAIL_CLOSED triangle, the
atomic rows write (crash between tmp and replace keeps the previous file),
and the CLI contract ``python -m research.gate_checks_v10 --gates ... --out
...`` executed from the worktree root exactly as A1/A7 will run it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

from research import gate_checks_v10 as gc
from research.resource_governor_v10 import freeze

REPO_ROOT = Path(gc.__file__).resolve().parents[1]
PY = sys.executable


# ------------------------------------------------------------------- G-H03
def test_gh03_passes_on_integrated_sources() -> None:
    row = gc.evaluate_gate("G-H03", {})
    assert row["verdict"] == "PASS"
    assert row["measured"]["files_scanned"] == len(gc.DEFAULT_SOURCES_GH03)
    assert row["measured"]["violations"] == []
    assert all(str(p).endswith(".py") for p in row["evidence_refs"])


def test_gh03_fails_on_injected_bad_source(tmp_path: Path) -> None:
    bad = tmp_path / "runtime_controller_v10.py"
    bad.write_text(
        "import subprocess\n"
        "subprocess.run(['ls'])\n"
        "subprocess.check_call(['x'], timeout=None)\n"
        "DEFAULT_TERM_GRACE_S = 0\n",
        encoding="utf-8",
    )
    row = gc.evaluate_gate("G-H03", {"sources": [str(bad)]})
    assert row["verdict"] == "FAIL"
    joined = "\n".join(row["measured"]["violations"])
    assert "without timeout" in joined
    assert "timeout=None" in joined
    assert "frozen constant DEFAULT_TERM_GRACE_S=0.0 not positive" in joined
    assert "frozen constant DEFAULT_HEARTBEAT_INTERVAL_S missing" in joined

    unallowlisted = tmp_path / "some_other_layer.py"
    unallowlisted.write_text("import subprocess\nsubprocess.run(['ls'])\n", encoding="utf-8")
    row2 = gc.evaluate_gate("G-H03", {"sources": [str(unallowlisted)]})
    assert row2["verdict"] == "FAIL"
    assert any("without timeout" in v for v in row2["measured"]["violations"])


def test_gh03_unavailable_when_source_missing(tmp_path: Path) -> None:
    row = gc.evaluate_gate("G-H03", {"sources": [str(tmp_path / "nope.py")]})
    assert row["verdict"] == "UNAVAILABLE_FAIL_CLOSED"


# ------------------------------------------------------------------- G-H05
def _consistent_governor_state(tmp_path: Path) -> Path:
    state_path = tmp_path / "freeze.json"
    gov = freeze(
        cap_contract=2,
        reserved_ram_gb=2.5,
        measured_peak_worker_ram_gb=1.0,
        available_ram_gb=16.0,
        state_path=str(state_path),
    )
    for idx in range(3):
        gov.record_two_worker_probe(safe=True, detail=f"probe {idx}")
    gov.save_state()
    return state_path


def test_gh05_passes_on_consistent_freeze_record(tmp_path: Path) -> None:
    state_path = _consistent_governor_state(tmp_path)
    row = gc.evaluate_gate("G-H05", {"governor_state_path": str(state_path)})
    assert row["verdict"] == "PASS"
    recomputed = row["measured"]["recomputed"]
    assert recomputed["ram_cap_workers"] == 13
    assert recomputed["effective_heavy_workers_recomputed"] == 2


def test_gh05_fails_on_tampered_or_underreserved_record(tmp_path: Path) -> None:
    state_path = _consistent_governor_state(tmp_path)
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["effective_heavy_workers"] = 4
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")
    row = gc.evaluate_gate("G-H05", {"governor_state_path": str(tampered)})
    assert row["verdict"] == "FAIL"
    assert any(r.startswith("effective_cap_mismatch") for r in row["measured"]["reasons"])

    payload2 = json.loads(state_path.read_text(encoding="utf-8"))
    payload2["reserved_ram_gb"] = 1.0
    under = tmp_path / "under.json"
    under.write_text(json.dumps(payload2), encoding="utf-8")
    row2 = gc.evaluate_gate("G-H05", {"governor_state": payload2})
    assert row2["verdict"] == "FAIL"
    assert "reserved_ram_gb_below_2gb_reserve" in row2["measured"]["reasons"]


def test_gh05_unavailable_without_record() -> None:
    row = gc.evaluate_gate("G-H05", {})
    assert row["verdict"] == "UNAVAILABLE_FAIL_CLOSED"
    row_missing = gc.evaluate_gate(
        "G-H05", {"governor_state_path": "/nonexistent/freeze.json"}
    )
    assert row_missing["verdict"] == "UNAVAILABLE_FAIL_CLOSED"


# ------------------------------------------------------------------- G-H06
@pytest.fixture()
def parity_dirs(tmp_path: Path) -> Dict[str, Path]:
    off, on = tmp_path / "off", tmp_path / "on"
    for d in (off, on):
        d.mkdir()
        (d / "metrics.json").write_text('{"aggregate": 7}\n', encoding="utf-8")
        (d / "sched.csv").write_text("sym\nBTCUSDT\n", encoding="utf-8")
    return {"on": on, "off": off}


def test_gh06_passes_with_full_proof_object(parity_dirs: Dict[str, Path]) -> None:
    row = gc.evaluate_gate(
        "G-H06",
        {
            "proof": {
                "parity_proof": True,
                "repro_all_match": True,
                "raw_reads": 2,
                "wall_time_cached_s": 2.0,
                "wall_time_uncached_s": 4.0,
            }
        },
    )
    assert row["verdict"] == "PASS"
    assert row["measured"]["metrics"]["wall_time_reduction"] == pytest.approx(0.5)


def test_gh06_fail_vs_unavailable_triangle(parity_dirs: Dict[str, Path]) -> None:
    (parity_dirs["on"] / "metrics.json").write_text('{"aggregate": 666}\n', encoding="utf-8")
    explicit_false = gc.evaluate_gate(
        "G-H06",
        {"proof": {"parity_proof": False, "repro_all_match": True, "raw_reads": 1,
                   "wall_time_cached_s": 1.0, "wall_time_uncached_s": 4.0}},
    )
    assert explicit_false["verdict"] == "FAIL"

    dirs_row = gc.evaluate_gate("G-H06", {"parity_dirs": [parity_dirs["on"], parity_dirs["off"]]})
    assert dirs_row["verdict"] == "FAIL"
    assert any("artifact_manifest_mismatch" in r for r in dirs_row["measured"]["reasons"])

    missing = gc.evaluate_gate("G-H06", {})
    assert missing["verdict"] == "UNAVAILABLE_FAIL_CLOSED"

    partial = gc.evaluate_gate(
        "G-H06",
        {"proof": {"parity_proof": True, "repro_all_match": True}},
    )
    assert partial["verdict"] == "UNAVAILABLE_FAIL_CLOSED"

    below_target = gc.evaluate_gate(
        "G-H06",
        {"proof": {"parity_proof": True, "repro_all_match": True, "raw_reads": 1,
                   "wall_time_cached_s": 3.9, "wall_time_uncached_s": 4.0}},
    )
    assert below_target["verdict"] == "FAIL"
    assert any(
        r.startswith("wall_time_reduction_below_target") for r in below_target["measured"]["reasons"]
    )

    over_budget = gc.evaluate_gate(
        "G-H06",
        {"proof": {"parity_proof": True, "repro_all_match": True, "raw_reads": 3,
                   "wall_time_cached_s": 1.0, "wall_time_uncached_s": 4.0}},
    )
    assert over_budget["verdict"] == "FAIL"
    assert any("raw_reads_budget_exceeded" in r for r in over_budget["measured"]["reasons"])


# ------------------------------------------------------------------- G-H08
def _all_items(status: str) -> Dict[int, str]:
    return {i: status for i in range(1, gc.H08_ITEM_COUNT + 1)}


def test_gh08_all_twenty_pass() -> None:
    row = gc.evaluate_gate("G-H08", {"items": _all_items("PASS")})
    assert row["verdict"] == "PASS"
    assert len(row["measured"]["passing_items"]) == gc.H08_ITEM_COUNT


def test_gh08_explicit_failure_is_fail_not_unavailable() -> None:
    items = _all_items("PASS")
    items[5] = "FAIL"
    row = gc.evaluate_gate("G-H08", {"items": items})
    assert row["verdict"] == "FAIL"
    assert row["measured"]["failed_items"] == [5]


def test_gh08_gap_is_unavailable_fail_closed() -> None:
    items = {i: "PASS" for i in range(1, 14)}
    row = gc.evaluate_gate("G-H08", {"items": items})
    assert row["verdict"] == "UNAVAILABLE_FAIL_CLOSED"
    assert 14 in row["measured"]["missing_items"]

    weird = _all_items("PASS")
    weird[20] = "SKIP"
    row2 = gc.evaluate_gate("G-H08", {"items": weird})
    assert row2["verdict"] == "UNAVAILABLE_FAIL_CLOSED"

    empty = gc.evaluate_gate("G-H08", {})
    assert empty["verdict"] == "UNAVAILABLE_FAIL_CLOSED"


# ------------------------------------------------------------------- G-H12
def test_gh12_pair_equal_mismatch_malformed_triangle() -> None:
    sha_a = "a" * 64
    row = gc.evaluate_gate(
        "G-H12",
        {
            "pairs": [
                {"label": "ts_trend_targets", "sha_root_a": sha_a, "sha_root_b": sha_a},
                {"label": "vol_shock_targets", "sha_root_a": "b" * 64, "sha_root_b": "B" * 64},
            ]
        },
    )
    assert row["verdict"] == "PASS"

    mismatch = gc.evaluate_gate(
        "G-H12",
        {"pairs": [{"label": "golden", "sha_root_a": sha_a, "sha_root_b": "c" * 64}]},
    )
    assert mismatch["verdict"] == "FAIL"
    assert mismatch["measured"]["mismatched_labels"] == ["golden"]

    malformed = gc.evaluate_gate(
        "G-H12",
        {"pairs": [{"label": "golden", "sha_root_a": "nothex", "sha_root_b": sha_a}]},
    )
    assert malformed["verdict"] == "UNAVAILABLE_FAIL_CLOSED"

    flat = gc.evaluate_gate("G-H12", {"sha_root_a": sha_a, "sha_root_b": sha_a})
    assert flat["verdict"] == "PASS"

    nothing = gc.evaluate_gate("G-H12", {})
    assert nothing["verdict"] == "UNAVAILABLE_FAIL_CLOSED"


# ------------------------------------------------------------ registry/CLI
def test_evaluate_gate_unknown_id_raises() -> None:
    with pytest.raises(ValueError, match="unknown gate id"):
        gc.evaluate_gate("G-NOPE", {})


def test_write_rows_atomically_survives_replace_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "rows.json"
    gc.write_rows_atomically(out, [gc.evaluate_gate("G-H03", {})])
    first = out.read_bytes()

    real_replace = os.replace
    calls = {"n": 0}

    def flaky(src: Any, dst: Any) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("injected crash")
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky)
    with pytest.raises(OSError):
        gc.write_rows_atomically(out, [])
    monkeypatch.undo()

    assert calls["n"] == 1
    assert json.loads(out.read_text(encoding="utf-8"))[0]["gate"] == "G-H03"
    assert out.read_bytes() == first
    gc.write_rows_atomically(out, [gc.evaluate_gate("G-H03", {})])
    rows = json.loads(out.read_text(encoding="utf-8"))
    assert len(rows) == 1 and out.read_text(encoding="utf-8").endswith("\n")


@pytest.mark.parametrize("gate,expected_verdict", [
    ("G-H03", "PASS"),
])
def test_cli_single_gate_from_worktree_root(tmp_path: Path, gate: str, expected_verdict: str) -> None:
    out = tmp_path / "cli_rows.json"
    proc = subprocess.run(
        [PY, "-m", "research.gate_checks_v10", "--gates", gate, "--out", str(out)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    rows = json.loads(out.read_text(encoding="utf-8"))
    assert len(rows) == 1 and rows[0]["gate"] == gate
    assert rows[0]["verdict"] == expected_verdict


def test_cli_all_gates_writes_atomic_rows_and_fails_closed(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    state_payload = json.loads(
        Path(_consistent_governor_state(evidence_dir)).read_text(encoding="utf-8")
    )
    (evidence_dir / "G-H05.json").write_text(
        json.dumps({"governor_state": state_payload}), encoding="utf-8"
    )
    golden_sha = "d" * 64
    (evidence_dir / "G-H12.json").write_text(
        json.dumps({"pairs": [{"label": "ts_trend", "sha_root_a": golden_sha, "sha_root_b": golden_sha}]}),
        encoding="utf-8",
    )

    out = tmp_path / "all_rows.json"
    proc = subprocess.run(
        [PY, "-m", "research.gate_checks_v10", "--gates", "all",
         "--evidence-dir", str(evidence_dir), "--out", str(out)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode != 0, "unavailable gates must fail the CLI closed"
    rows = {row["gate"]: row for row in json.loads(out.read_text(encoding="utf-8"))}
    assert set(rows) == set(gc.EVALUATORS)
    assert rows["G-H03"]["verdict"] == "PASS"
    assert rows["G-H05"]["verdict"] == "PASS"
    assert rows["G-H12"]["verdict"] == "PASS"
    assert rows["G-H06"]["verdict"] == "UNAVAILABLE_FAIL_CLOSED"
    assert rows["G-H08"]["verdict"] == "UNAVAILABLE_FAIL_CLOSED"
    assert out.read_text(encoding="utf-8").endswith("\n")


def test_cli_rejects_unknown_gate(tmp_path: Path) -> None:
    proc = subprocess.run(
        [PY, "-m", "research.gate_checks_v10", "--gates", "G-NOT-REAL",
         "--out", str(tmp_path / "x.json")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode != 0
    assert "unknown gate id" in (proc.stderr + proc.stdout)
