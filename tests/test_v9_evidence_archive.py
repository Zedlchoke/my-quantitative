"""Unit tests for scripts/v9_evidence_archive.py (A2, sprint V9H->V10 Phase 0).

All fixtures are synthetic tmp trees mirroring the real V9 layout; no real
evidence source is touched. One optional slow smoke test against the real
trees is marked skip by default.

The real-world attestation pin cannot exist in synthetic fixtures (sha256
preimage), so the harness monkeypatches KNOWN_PINS to the fixture's own
attestation digest; every other pin keeps its production value.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.v9_evidence_archive as mod  # noqa: E402

LAUNCH = mod.KNOWN_PINS["launch_sha"]
REAL_ATTEST_PIN = mod.KNOWN_PINS["attestation_sha256"]
TRIALS = {
    "exec-v9-r1": ["XSECT-TSTREND-L14", "XSECT-TSTREND-CTRL", "XSECT-VOLSHK-CTRL"],
    "exec-v9-r2": ["XSECT-TSTREND-L28", "XSECT-VOLSHK-S15"],
}
TECHABORTS = {
    "exec-v9-r1": "XSECT-VOLSHK-CTRL.TECHABORT-V9-B",
    "exec-v9-r2": "XSECT-VOLSHK-S15.TECHABORT-V9-OOM-A",
}
REPROS = {
    "exec-v9-r1": ["VERIFY-V9-TSTREND-L14", "VERIFY-V9-TSTREND-CTRL", "VERIFY-V9-VOLSHK-CTRL"],
    "exec-v9-r2": ["VERIFY-V9-TSTREND-L28", "VERIFY-V9-VOLSHK-S15"],
}


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def build_fixture(root: Path) -> tuple[dict[str, Path], str]:
    """Synthetic V9 evidence tree with the real directory/role structure."""
    attest_hash_by_tree: dict[str, str] = {}
    for tree in ("exec-v9-r1", "exec-v9-r2"):
        base = root / tree
        baseline_text = json.dumps(
            {"artifact": "baseline_root", "launch_head": LAUNCH, "tree": tree}
        )
        _write(base / "research/audits/v9p/baseline_root.json", baseline_text)
        baseline_sha = hashlib.sha256(baseline_text.encode()).hexdigest()
        attest_text = json.dumps({"artifact": "a7_prelaunch_attestation", "checks": {}})
        _write(base / "research/audits/v9p/a7_prelaunch_attestation.json", attest_text)
        attest_hash_by_tree[tree] = hashlib.sha256(attest_text.encode()).hexdigest()
        _write(base / "data/v9_manifests/universe_selection_v9.json", "{}")

        results = base / "results"
        for name in ("account.csv", "summary.json"):
            _write(results / name, f"{tree},{name}\n")
        for trial in TRIALS[tree]:
            d = results / "portfolio_v9" / trial
            _write(d / "final_gate_result.json", '{"verdict": "REJECTED"}')
            _write(d / "canonical_metrics.json", '{"sharpe": -0.1}')
            for frozen in ("candidate.yaml", "config.yaml", "data_manifest.json", "universe.json"):
                _write(d / "frozen" / frozen, f"# {trial} {frozen}\n")
            launch = (
                "schema_version: 3\n"
                f"experiment_id: {trial}\n"
                f"git_commit_at_launch: {LAUNCH}\n"
                "provenance:\n"
                f"  baseline_sha256: {baseline_sha}\n"
                f"  attestation_sha256: {attest_hash_by_tree[tree]}\n"
            )
            _write(d / "launch_manifest.yaml", launch)
            shard = results / "registry" / "shards" / f"v9_{trial}.jsonl"
            _write(shard, json.dumps({"experiment_id": trial, "CELL_RESULT": True}) + "\n")
        ta = results / "portfolio_v9" / TECHABORTS[tree]
        _write(ta / "run.log", "OOM kill before scoring\n")
        for frozen in ("candidate.yaml", "config.yaml", "data_manifest.json", "universe.json"):
            _write(ta / "frozen" / frozen, "# aborted\n")
        _write(ta / "launch_manifest.yaml", "schema_version: 3\nexperiment_id: aborted\n")
        _write(results / "registry/experiments.jsonl", '{"kind": "index"}\n')
        matrix = results / "matrix/v9_multifamily"
        _write(matrix / "index.json", "{}")
        _write(matrix / "report.json", "{}")
        for rep in REPROS[tree]:
            rd = results / "reproduction_v9" / rep
            _write(
                rd / "comparison.json",
                '{"all_match": true, "failed_checks": [], "checks": {"pnl_match": true}}',
            )
            _write(rd / "reproduction_report.json", '{"status": "ok"}')
            _write(rd / "rerun_artifacts/core_result.json", '{"core": true}')

    main_repo = root / "main-repo"
    _write(main_repo / "research/audits/v9/a7_terminal_audit_v9.json",
           '{"verdict": "V9_REJECT_ALL_MULTI_FAMILY"}')
    _write(main_repo / "research/audits/v9p/resolved_contract_v9.json", '{"contract": "v9"}')
    _write(main_repo / "research/audits/v9p/v9_budget_freeze.json", '{"budget": 5}')
    _write(main_repo / "research/control/v9_multifamily_run/event_log.jsonl",
           '{"event": "launch"}\n{"event": "close"}\n')

    sources = {
        "exec-v9-r1": root / "exec-v9-r1",
        "exec-v9-r2": root / "exec-v9-r2",
        "main-repo": main_repo,
    }
    return sources, attest_hash_by_tree


@pytest.fixture()
def harness(tmp_path, monkeypatch):
    sources, attest_hash = build_fixture(tmp_path / "evidence")
    monkeypatch.setattr(
        mod,
        "KNOWN_PINS",
        {
            "launch_sha": LAUNCH,
            "attestation_sha256": attest_hash["exec-v9-r1"],
            "terminal_verdict": mod.KNOWN_PINS["terminal_verdict"],
        },
    )
    return {
        "tmp_path": tmp_path,
        "sources": sources,
        "attest_hash": attest_hash,
    }


def archive_bundle(tmp_path: Path, name: str, sources) -> tuple[Path, dict]:
    dest = tmp_path / name
    summary = mod.cmd_archive(argparse.Namespace(dest=str(dest)), sources=sources)
    return dest, summary


def run_verify(dest: Path, restore: Path):
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            mod.cmd_verify(argparse.Namespace(bundle=str(dest), restore_to=str(restore)))
        code = 0
    except SystemExit as exc:
        code = exc.code
    report = json.loads(out.getvalue())
    return code, report


def load_bundle(dest: Path) -> dict:
    return {
        "manifest": json.loads((dest / "manifest.json").read_text(encoding="utf-8")),
        "index": json.loads((dest / "index.json").read_text(encoding="utf-8")),
    }


def prepare_restore(harness: dict) -> Path:
    dest, _ = archive_bundle(harness["tmp_path"], "b1", harness["sources"])
    restore = harness["tmp_path"] / "restore"
    code, report = run_verify(dest, restore)
    assert code == 0, json.dumps(report.get("semantic_checks", {}), indent=1)[:2000]
    return restore


# --------------------------------------------------------------------------- #
# roles + manifest determinism
# --------------------------------------------------------------------------- #

def test_role_assignment_table():
    cases = {
        "results/portfolio_v9/XSECT-TSTREND-L14/canonical_metrics.json": "scored_trial",
        "results/portfolio_v9/XSECT-TSTREND-L14/frozen/config.yaml": "scored_trial",
        "results/portfolio_v9/XSECT-VOLSHK-CTRL.TECHABORT-V9-B/run.log": "techabort_zero_score_archive",
        "results/reproduction_v9/VERIFY-V9-TSTREND-L28/comparison.json": "reproduction",
        "results/registry/shards/v9_XSECT-TSTREND-L14.jsonl": "registry_shard",
        "results/registry/experiments.jsonl": "registry_index",
        "results/matrix/v9_multifamily/index.json": "matrix_summary",
        "results/account.csv": "results_root_misc",
        "research/audits/v9p/baseline_root.json": "prelaunch_baseline",
        "research/audits/v9p/a7_prelaunch_attestation.json": "prelaunch_attestation",
        "data/v9_manifests/universe_selection_v9.json": "data_universe_manifest",
        "research/audits/v9/a7_terminal_audit_v9.json": "audit_terminal",
        "research/control/v9_multifamily_run/event_log.jsonl": "control_lineage",
    }
    for rel, want in cases.items():
        assert mod.role_for(rel) == want, rel


def test_archive_is_idempotent_and_matches_formula(tmp_path):
    sources, _ = build_fixture(tmp_path / "evidence")
    d1, s1 = archive_bundle(tmp_path, "b1", sources)
    m1 = load_bundle(d1)["manifest"]
    lines = sorted(f"{r['sha256']}  {r['relpath']}" for r in m1["files"])
    expect = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    assert s1["bundle_hash"] == m1["bundle_hash"] == expect
    assert m1["total_files"] == len(m1["files"])
    assert sum(r["size_bytes"] for r in m1["files"]) == m1["total_bytes"]

    time.sleep(1.1)
    d2, s2 = archive_bundle(tmp_path, "b2", sources)
    m2 = load_bundle(d2)["manifest"]
    assert s1["bundle_hash"] == s2["bundle_hash"]
    assert m1["files"] == m2["files"]
    assert m1["created_at_utc"] != m2["created_at_utc"]


def test_content_addressed_blobs_dedup_and_roundtrip(tmp_path):
    sources, _ = build_fixture(tmp_path / "evidence")
    dest, _ = archive_bundle(tmp_path, "b1", sources)
    data = load_bundle(dest)
    by_blob: dict[str, int] = {}
    for r in data["manifest"]["files"]:
        blob = dest / r["bundle_path"]
        assert blob.is_file(), r["bundle_path"]
        assert mod.sha256_file(blob) == r["sha256"]
        assert blob.stat().st_size == r["size_bytes"]
        assert r["bundle_path"] == f"blobs/{r['sha256'][:2]}/{r['sha256']}"
        by_blob[r["bundle_path"]] = by_blob.get(r["bundle_path"], 0) + 1
    rows = {r["relpath"]: r for r in data["manifest"]["files"]}
    shared = rows["exec-v9-r1/data/v9_manifests/universe_selection_v9.json"]["bundle_path"]
    assert shared == rows["exec-v9-r2/data/v9_manifests/universe_selection_v9.json"]["bundle_path"]
    assert by_blob[shared] >= 2
    assert len(by_blob) < len(data["manifest"]["files"])


# --------------------------------------------------------------------------- #
# verify: happy path + tamper detection
# --------------------------------------------------------------------------- #

def test_verify_pass_with_restore_byte_equality(harness):
    dest, _ = archive_bundle(harness["tmp_path"], "b1", harness["sources"])
    restore = harness["tmp_path"] / "restore"
    code, report = run_verify(dest, restore)
    assert code == 0
    assert report["verdict"] == "PASS"
    assert report["semantic_all_pass"] is True
    assert report["files_matched"] == report["total_files"]
    pairs = [
        (
            harness["sources"]["exec-v9-r1"] / "results/portfolio_v9/XSECT-TSTREND-L14/canonical_metrics.json",
            restore / "exec-v9-r1/results/portfolio_v9/XSECT-TSTREND-L14/canonical_metrics.json",
        ),
        (
            harness["sources"]["main-repo"] / "research/control/v9_multifamily_run/event_log.jsonl",
            restore / "main-repo/research/control/v9_multifamily_run/event_log.jsonl",
        ),
    ]
    for src, dst in pairs:
        assert src.read_bytes() == dst.read_bytes()


def test_verify_detects_single_flipped_byte(tmp_path):
    sources, _ = build_fixture(tmp_path / "evidence")
    dest, _ = archive_bundle(tmp_path, "b1", sources)
    victim = next(p for p in (dest / "blobs").rglob("*") if p.is_file())
    raw = bytearray(victim.read_bytes())
    raw[0] ^= 0xFF
    victim.write_bytes(bytes(raw))
    code, report = run_verify(dest, tmp_path / "restore")
    assert code == 1
    assert report["verdict"] == "FAIL"
    joined = json.dumps(report)
    assert "blob_sha256_mismatch" in joined or "restored_byte_comparison_failed" in joined


def test_verify_detects_missing_and_extra_blobs(tmp_path):
    sources, _ = build_fixture(tmp_path / "evidence")
    dest, _ = archive_bundle(tmp_path, "b1", sources)
    victim = next(p for p in (dest / "blobs").rglob("*") if p.is_file())
    saved = victim.read_bytes()
    victim.unlink()
    code, report = run_verify(dest, tmp_path / "r_missing")
    assert code == 1 and report["verdict"] == "FAIL"
    assert any("missing_blob" in p for p in report["structural_problems"])

    stray_prefix = "00" * 31 + "ff"
    stray = dest / "blobs" / "00" / stray_prefix
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_bytes(saved[:8])
    code2, report2 = run_verify(dest, tmp_path / "r_extra")
    assert code2 == 1 and report2["verdict"] == "FAIL"
    assert any("extra_blob" in p for p in report2["structural_problems"])


def test_verify_detects_index_manifest_inconsistency(tmp_path):
    sources, _ = build_fixture(tmp_path / "evidence")
    dest, _ = archive_bundle(tmp_path, "b1", sources)
    data = load_bundle(dest)
    some_key = sorted(data["index"].keys())[0]
    data["index"][some_key]["role"] = "tampered_role"
    (dest / "index.json").write_text(json.dumps(data["index"], indent=2), encoding="utf-8")
    code, report = run_verify(dest, tmp_path / "restore")
    assert code == 1
    assert any("index_manifest_row_mismatch" in p for p in report["structural_problems"])


def test_verify_detects_bundle_hash_tamper(tmp_path):
    sources, _ = build_fixture(tmp_path / "evidence")
    dest, _ = archive_bundle(tmp_path, "b1", sources)
    data = load_bundle(dest)
    data["manifest"]["bundle_hash"] = "0" * 64
    (dest / "manifest.json").write_text(json.dumps(data["manifest"], indent=2), encoding="utf-8")
    code, report = run_verify(dest, tmp_path / "restore")
    assert code == 1
    assert any("bundle_hash_mismatch" in p for p in report["structural_problems"])


# --------------------------------------------------------------------------- #
# semantic checks
# --------------------------------------------------------------------------- #

def test_semantic_techabort_zero_score_variants(harness):
    restore = prepare_restore(harness)
    clean = mod.semantic_checks(restore)["techabort_archives_zero_score"]
    assert clean["pass"] is True

    planted_metric = (
        restore
        / f"exec-v9-r1/results/portfolio_v9/{TECHABORTS['exec-v9-r1']}/canonical_metrics.json"
    )
    planted_metric.write_text('{"sharpe": 0.0}', encoding="utf-8")
    dirty = mod.semantic_checks(restore)["techabort_archives_zero_score"]
    assert dirty["pass"] is False
    planted_metric.unlink()

    ledger = (
        restore
        / f"exec-v9-r2/results/portfolio_v9/{TECHABORTS['exec-v9-r2']}/portfolio_ledger.jsonl"
    )
    ledger.write_text('{"sharpe_ratio": 0.42}\n', encoding="utf-8")
    dirty_ledger = mod.semantic_checks(restore)["techabort_archives_zero_score"]
    assert dirty_ledger["pass"] is False


def test_semantic_comparison_all_match_variants(harness):
    restore = prepare_restore(harness)
    comp = restore / "exec-v9-r2/results/reproduction_v9/VERIFY-V9-TSTREND-L28/comparison.json"

    comp.write_text('{"all_match": false, "failed_checks": []}', encoding="utf-8")
    assert mod.semantic_checks(restore)["five_reproductions_all_match"]["pass"] is False

    comp.write_text('{"all_match": true, "failed_checks": ["pnl_match"]}', encoding="utf-8")
    assert mod.semantic_checks(restore)["five_reproductions_all_match"]["pass"] is False

    comp.write_text(
        '{"all_match": true, "failed_checks": [], "checks": {"orders_match": false}}',
        encoding="utf-8",
    )
    assert mod.semantic_checks(restore)["five_reproductions_all_match"]["pass"] is False

    comp.write_text(
        '{"all_match": true, "failed_checks": [], "checks": {"pnl_match": true}}',
        encoding="utf-8",
    )
    assert mod.semantic_checks(restore)["five_reproductions_all_match"]["pass"] is True


def test_semantic_pin_checks(harness):
    restore = prepare_restore(harness)

    launch = (
        restore / "exec-v9-r1/results/portfolio_v9/XSECT-TSTREND-L14/launch_manifest.yaml"
    )
    original = launch.read_text(encoding="utf-8")

    launch.write_text(original.replace(LAUNCH, "deadbeef" * 6 + "aaaa"), encoding="utf-8")
    bad_launch = mod.semantic_checks(restore)["five_scored_trials_readable_with_pins"]
    assert bad_launch["pass"] is False
    launch.write_text(original, encoding="utf-8")

    bogus_baseline = original.replace("baseline_sha256: ", "baseline_sha256: 1111", 1)
    launch.write_text(bogus_baseline, encoding="utf-8")
    bad_baseline = mod.semantic_checks(restore)["five_scored_trials_readable_with_pins"]
    assert bad_baseline["pass"] is False
    launch.write_text(original, encoding="utf-8")

    attestation = restore / "exec-v9-r2/research/audits/v9p/a7_prelaunch_attestation.json"
    attestation.write_text('{"tampered": true}', encoding="utf-8")
    bad_attest = mod.semantic_checks(restore)["baseline_and_attestation_hashes_present"]
    assert bad_attest["pass"] is False

    checks = mod.semantic_checks(restore)
    assert checks["terminal_verdict_evidence"]["pass"] is True
    assert checks["contract_budget_universe_data_manifests"]["pass"] is True
    assert checks["registry_shards_for_all_five_trials"]["pass"] is True
    assert checks["control_event_log_present"]["pass"] is True
    assert checks["five_reproductions_all_match"]["pass"] is True


def test_semantic_full_pass_on_clean_fixture(harness):
    restore = prepare_restore(harness)
    result = mod.semantic_checks(restore)
    assert result["all_pass"] is True
    assert result["five_scored_trials_readable_with_pins"]["pass"] is True
    assert len(result["five_scored_trials_readable_with_pins"]["trials"]) == 5


# --------------------------------------------------------------------------- #
# inventory on a real temp git repo
# --------------------------------------------------------------------------- #

def test_tree_inventory_on_tmp_git_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "results").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    (repo / "tracked.txt").write_text("hi\n", encoding="utf-8")
    (repo / "results" / "a.bin").write_bytes(b"\x00\x01" * 4)
    (repo / "results" / "b.bin").write_bytes(b"x" * 10)
    subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    inv = mod.tree_inventory(repo)
    assert inv["head_sha"] == head
    assert inv["dirty_files"] == 1
    assert inv["results_file_count"] == 2
    assert inv["results_bytes"] == 18


@pytest.mark.skip(reason="slow end-to-end smoke over the real ~220MB V9 trees; run manually")
def test_real_trees_archive_and_verify_smoke(tmp_path):
    sources = mod.default_sources()
    dest, summary = archive_bundle(tmp_path, "real_bundle", sources)
    code, report = run_verify(dest, tmp_path / "restore")
    assert code == 0
    assert report["verdict"] == "PASS"
    assert summary["total_files"] == report["total_files"]
