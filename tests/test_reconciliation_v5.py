"""Measured XG2a fixtures (PLAN 31.2 item 8-9 / F15+F16, owner A3).

Every test builds a REAL experiment directory in tmp, finalizes hashes LAST,
then perturbs exactly one thing:

* tamper a file post-hash            -> FAIL (hash mismatch)
* append to a file AFTER hashing     -> FAIL (stale hashes mtime)
* clean directory                    -> PASS
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from contracts.protocol import GateVerdict, sha256_text
from research.reconciliation import (
    HASHES_FILENAME,
    finalize_directory_hashes,
    verify_experiment_dir,
)


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, (dict, list)):
        text = json.dumps(payload, indent=2)
    else:
        text = str(payload)
    path.write_text(text + "\n", encoding="utf-8")


def _build_clean_dir(exp_dir: Path) -> None:
    positions = [
        {"symbol": "BTCUSDT", "canonical_pnl": 120.0},
        {"symbol": "ETHUSDT", "canonical_pnl": -30.5},
    ]
    funding = [{"funding_net": -1.5}, {"funding_net": 0.25}]
    costs = [
        {"commission": 2.0, "modeled_slippage": 1.0},
        {"commission": 1.5, "modeled_slippage": 0.75},
    ]
    accounting = {
        "positions_total_pnl": 89.5,
        "funding_total": -1.25,
        "commission_total": 3.5,
        "slippage_total": 1.75,
    }
    _write(exp_dir / "positions.jsonl", "\n".join(json.dumps(r) for r in positions))
    _write(exp_dir / "funding_cashflows.jsonl", "\n".join(json.dumps(r) for r in funding))
    _write(exp_dir / "costs.jsonl", "\n".join(json.dumps(r) for r in costs))
    _write(exp_dir / "accounting_reconciliation.json", accounting)
    _write(
        exp_dir / "canonical_metrics.json",
        {
            "net_canonical_pnl": {"value": 88.25, "reason": None},
            "trades": {"value": 2, "reason": None},
            "position_pf": {"value": 1.42, "reason": None},
        },
    )
    _write(exp_dir / "cell.json", {"source_trial_experiment_id": "V4-SRC-001"})
    _write(exp_dir / "scorecard.json", {"total": 0})
    _write(exp_dir / "gate_result.json", {"rows": []})
    _write(exp_dir / "run.log", "2026-08-24 | DIAG-V5 | done\n")
    # Hashes MUST come last (PLAN 31.2 item 9).
    finalize_directory_hashes(exp_dir)


def test_hashes_final_flag_written_and_listed_files_complete(tmp_path):
    exp_dir = tmp_path / "EXP1-DIAG-V5"
    _build_clean_dir(exp_dir)
    assert (exp_dir / ".hashes_final").is_file()
    listing = json.loads((exp_dir / HASHES_FILENAME).read_text())["files"]
    on_disk = {
        str(p.relative_to(exp_dir))
        for p in exp_dir.rglob("*")
        if p.is_file() and p.name not in (HASHES_FILENAME, ".hashes_final")
    }
    assert set(listing) == on_disk


def test_clean_dir_passes_with_measured_result(tmp_path):
    exp_dir = tmp_path / "CLEAN-DIAG-V5"
    _build_clean_dir(exp_dir)
    result = verify_experiment_dir(exp_dir)
    assert isinstance(result.reasons, tuple)  # never constructed bare-True only
    assert result.verdict() is GateVerdict.PASS, result.reasons


def test_tamper_file_after_hashing_fails(tmp_path):
    exp_dir = tmp_path / "TAMPER-DIAG-V5"
    _build_clean_dir(exp_dir)
    time.sleep(0.01)
    metrics = json.loads((exp_dir / "canonical_metrics.json").read_text())
    metrics["net_canonical_pnl"]["value"] = 999_999.0
    _write(exp_dir / "canonical_metrics.json", metrics)
    result = verify_experiment_dir(exp_dir)
    assert result.verdict() is GateVerdict.FAIL
    assert result.hashes_match is False
    assert any(
        r.startswith("artifact_hash_mismatch:canonical_metrics.json")
        for r in result.reasons
    )


def test_append_log_after_hashes_fails_stale_mtime(tmp_path):
    """F15 regression: hash-before-log-append must be caught."""
    exp_dir = tmp_path / "APPEND-DIAG-V5"
    _build_clean_dir(exp_dir)
    time.sleep(0.01)
    with open(exp_dir / "run.log", "a", encoding="utf-8") as handle:
        handle.write("post-hash sneaky append\n")
    result = verify_experiment_dir(exp_dir)
    assert result.verdict() is GateVerdict.FAIL
    assert result.report_index_reconcile is False
    assert any(r.startswith("artifact_hashes_stale:run.log") for r in result.reasons)


def test_unlisted_extra_file_fails(tmp_path):
    exp_dir = tmp_path / "EXTRA-DIAG-V5"
    _build_clean_dir(exp_dir)
    time.sleep(0.01)
    _write(exp_dir / "sneaky_side_channel.json", {"leak": True})
    result = verify_experiment_dir(exp_dir)
    assert result.verdict() is GateVerdict.FAIL
    assert any(r.startswith("unlisted_artifact_file:") for r in result.reasons)


def test_accounting_mismatch_fails_within_1e9(tmp_path):
    exp_dir = tmp_path / "ACCT-DIAG-V5"
    _build_clean_dir(exp_dir)
    accounting = json.loads((exp_dir / "accounting_reconciliation.json").read_text())
    accounting["positions_total_pnl"] += 0.01  # >> 1e-9 scaled tolerance
    time.sleep(0.01)
    _write(exp_dir / "accounting_reconciliation.json", accounting)
    finalize_directory_hashes(exp_dir)  # re-hash so ONLY accounting is wrong
    result = verify_experiment_dir(exp_dir)
    assert result.verdict() is GateVerdict.FAIL
    assert any(r.startswith("accounting_reconcile_fail") for r in result.reasons)


def test_missing_required_artifact_is_schema_fail(tmp_path):
    exp_dir = tmp_path / "SCHEMA-DIAG-V5"
    _build_clean_dir(exp_dir)
    (exp_dir / "gate_result.json").unlink()
    time.sleep(0.01)
    finalize_directory_hashes(exp_dir)
    result = verify_experiment_dir(exp_dir)
    assert result.schema_valid is False
    assert any(r == "missing_artifact:gate_result.json" for r in result.reasons)
    # missing artifact is also absent from the fresh listing -> hash side clean
    assert result.verdict() is GateVerdict.FAIL


def test_missing_directory_fails_closed(tmp_path):
    result = verify_experiment_dir(tmp_path / "does-not-exist-DIAG-V5")
    assert result.verdict() is GateVerdict.FAIL
    assert "experiment_dir_missing" in result.reasons


def test_ledger_field_missing_fails_closed(tmp_path):
    exp_dir = tmp_path / "FIELD-DIAG-V5"
    _build_clean_dir(exp_dir)
    rows = [
        {"symbol": "BTCUSDT", "canonical_pnl": 120.0},
        {"symbol": "ETHUSDT"},  # canonical_pnl vanished
    ]
    _write(exp_dir / "positions.jsonl", "\n".join(json.dumps(r) for r in rows))
    time.sleep(0.01)
    finalize_directory_hashes(exp_dir)
    result = verify_experiment_dir(exp_dir)
    assert result.positions_reconcile is False
    assert any(
        r.startswith("ledger_field_missing:positions.jsonl") for r in result.reasons
    )


def test_hash_listing_self_consistency_content_digest_recorded(tmp_path):
    """The hashes doc records the digest of its own pre-write content spec."""
    exp_dir = tmp_path / "SELFHASH-DIAG-V5"
    _build_clean_dir(exp_dir)
    doc = json.loads((exp_dir / HASHES_FILENAME).read_text())
    assert doc["algorithm"] == "sha256"
    assert doc["files_spec_sha256"] == sha256_text(json.dumps(doc["files"], sort_keys=True))
