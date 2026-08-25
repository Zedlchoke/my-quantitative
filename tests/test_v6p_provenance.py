"""V6P A2 negative fixtures: provenance root + attestation (N01-N03/N15)."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research.provenance_v6p import (  # noqa: E402
    baseline_self_hash_violations,
    create_baseline_root,
    refresh_transition_heads,
    transition_doc,
    validate_launch_provenance,
    write_attestation,
)


@pytest.fixture()
def git_repo(tmp_path):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    def git(*args):
        return subprocess.run(["git", "-C", str(tmp_path), *args],
                              capture_output=True, text=True, check=True,
                              env=env).stdout
    git("init", "-q")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "mod.py").write_text("X = 1\n")
    git("add", "src/mod.py")
    git("commit", "-qm", "init")
    return tmp_path


import os  # noqa: E402


def test_baseline_refuses_dirty_tree(git_repo):
    (git_repo / "src" / "mod.py").write_text("X = 2\n")
    with pytest.raises(RuntimeError, match="dirty"):
        create_baseline_root(git_repo, source_roots=["src"],
                             data_bundle_dir=None,
                             output_path=git_repo / "b.json")


def test_baseline_external_root_has_no_self_hash(git_repo):
    out = git_repo / "research" / "audits" / "v6p" / "baseline_root.json"
    baseline = create_baseline_root(git_repo, source_roots=["src"],
                                    data_bundle_dir=None, output_path=out)
    assert baseline["launch_head"] == subprocess.run(
        ["git", "-C", str(git_repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True).stdout.strip()
    violations = baseline_self_hash_violations(
        baseline, out.read_bytes())
    assert violations == []


def test_attestation_then_validate_pass_and_fail_paths(git_repo):
    out = git_repo / "baseline_root.json"
    create_baseline_root(git_repo, source_roots=["src"],
                         data_bundle_dir=None, output_path=out)
    att = write_attestation(
        git_repo, auditor="A7", baseline_path=out,
        output_path=git_repo / "att.json",
        checks={"clean_tree": True, "hashes_match": True})
    assert att["verdict"] == "PASS"
    head = subprocess.run(["git", "-C", str(git_repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True,
                          check=True).stdout.strip()
    later = (datetime.now(timezone.utc)
             + timedelta(seconds=5)).isoformat()
    reasons = validate_launch_provenance(
        git_repo, baseline_path=out, attestation_path=git_repo / "att.json",
        launch_head=head, dirty=False, first_launch_started_utc=later)
    assert reasons == []

    # dirty launch
    (git_repo / "src" / "mod.py").write_text("X = 3\n")
    reasons = validate_launch_provenance(
        git_repo, baseline_path=out, attestation_path=git_repo / "att.json",
        launch_head=head, dirty=None)
    assert "dirty_worktree_at_launch" in reasons

    # post-launch baseline creation (N01 class)
    reasons = validate_launch_provenance(
        git_repo, baseline_path=out, attestation_path=git_repo / "att.json",
        launch_head=head, dirty=False,
        first_launch_started_utc=(
            datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat())
    assert "post_launch_baseline_creation" in reasons

    # head mismatch
    reasons = validate_launch_provenance(
        git_repo, baseline_path=out, attestation_path=git_repo / "att.json",
        launch_head="0" * 40, dirty=False)
    assert "launch_head_mismatch" in reasons


def test_missing_attestation_fails_closed(git_repo):
    out = git_repo / "baseline_root.json"
    create_baseline_root(git_repo, source_roots=["src"],
                         data_bundle_dir=None, output_path=out)
    reasons = validate_launch_provenance(
        git_repo, baseline_path=out,
        attestation_path=git_repo / "nope.json", dirty=False)
    assert "attestation_missing" in reasons


def test_self_hash_embedding_is_detected():
    # Structural detection: a self-referential HASH KEY is the meaningful
    # violation class (embedding sha256(current bytes) inside those bytes is
    # a fixed-point impossibility).
    assert baseline_self_hash_violations(
        {"self_hash": "x"}, b"{}") == ["self_referential_key:self_hash"]
    assert baseline_self_hash_violations(
        {"baseline_sha256": "x"}, b"{}") == ["self_referential_key:baseline_sha256"]
    assert baseline_self_hash_violations(
        {"source_files_sha256": {"a.py": "b" * 64}}, b"{}") == []


def test_transition_lifecycle_fields_distinct_and_refreshable():
    doc = transition_doc(artifact="t", actor="A1", verdict="PASS")
    assert doc["created_at_utc"]
    assert doc["audited_at_utc"] is None and doc["final_head"] is None
    refreshed = refresh_transition_heads(doc, final_head="f" * 40)
    assert refreshed["final_head"] == "f" * 40
    assert refreshed["integrated_at_utc"] >= doc["created_at_utc"]
