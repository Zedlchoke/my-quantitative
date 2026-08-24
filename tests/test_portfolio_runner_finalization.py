"""Artifact finalization contract tests for research.portfolio_runner (A4, D1).

Synthetic tmp_path experiment directories only (never real results/). These
fixtures detect the historical DIAG-V5 defect class: a run.log append AFTER
artifact_hashes.json was computed, which left every manifest stale.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.portfolio_runner import (
    HashesFinalViolation,
    append_run_log,
    verify_artifact_hashes,
    write_artifact_hashes,
)


def _make_exp_dir(root: Path) -> Path:
    exp = root / "EXP-TEST"
    (exp / "frozen").mkdir(parents=True)
    (exp / "run.log").write_text("[t0] launch\n[t1] verdict=INCONCLUSIVE\n",
                                 encoding="utf-8")
    (exp / "canonical_metrics.json").write_text('{"total_pnl": 1.0}\n',
                                                encoding="utf-8")
    (exp / "frozen" / "candidate.yaml").write_text("lookback_days: 3\n",
                                                   encoding="utf-8")
    return exp


def test_verify_clean_after_finalize(tmp_path):
    exp = _make_exp_dir(tmp_path)
    out = write_artifact_hashes(exp)
    assert out == exp / "artifact_hashes.json"
    hashes = json.loads(out.read_text(encoding="utf-8"))["hashes"]
    assert set(hashes) == {"run.log", "canonical_metrics.json",
                           "frozen/candidate.yaml"}
    assert "artifact_hashes.json" not in hashes  # manifest self-excludes
    assert verify_artifact_hashes(exp) == []


def test_verify_flags_post_hash_runlog_append(tmp_path):
    exp = _make_exp_dir(tmp_path)
    write_artifact_hashes(exp)
    with (exp / "run.log").open("a", encoding="utf-8") as handle:
        handle.write("[t2] late verdict line\n")  # historical defect class
    assert verify_artifact_hashes(exp) == ["run.log:hash_mismatch"]


def test_verify_reports_missing_and_unlisted_files(tmp_path):
    exp = _make_exp_dir(tmp_path)
    write_artifact_hashes(exp)
    (exp / "canonical_metrics.json").unlink()
    (exp / "extra.txt").write_text("unlisted\n", encoding="utf-8")
    assert verify_artifact_hashes(exp) == [
        "canonical_metrics.json:missing",
        "extra.txt:unlisted",
    ]


def test_double_finalize_identical_content_is_idempotent(tmp_path):
    exp = _make_exp_dir(tmp_path)
    first = write_artifact_hashes(exp)
    before = first.read_bytes()
    again = write_artifact_hashes(exp)
    assert again == first
    assert first.read_bytes() == before
    assert verify_artifact_hashes(exp) == []


def test_double_finalize_after_mutation_fails_closed(tmp_path):
    exp = _make_exp_dir(tmp_path)
    out = write_artifact_hashes(exp)
    frozen_manifest = json.loads(out.read_text(encoding="utf-8"))
    (exp / "canonical_metrics.json").write_text('{"total_pnl": 2.0}\n',
                                                encoding="utf-8")
    with pytest.raises(HashesFinalViolation):
        write_artifact_hashes(exp)
    assert json.loads(out.read_text(encoding="utf-8")) == frozen_manifest


def test_post_hash_run_log_append_raises(tmp_path):
    exp = _make_exp_dir(tmp_path)
    log_path = exp / "run.log"
    before = log_path.read_bytes()
    write_artifact_hashes(exp)
    with pytest.raises(RuntimeError):
        append_run_log(log_path, "[t2] after finalize")
    assert log_path.read_bytes() == before
