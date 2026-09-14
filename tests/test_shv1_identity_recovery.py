"""PROSPECTIVE-SHADOW-V1 P1 identity recovery: byte-level verification.

Recomputes every hash in research/control/prospective_shadow_v1/identity/
identity_recovery.json from actual bytes (`git show <commit>:<path>` for
commit-sourced files, direct reads for WORKING_TREE_TRACKED files), asserts
git blob ids via `git ls-tree` / `git hash-object`, asserts the three
historical verdict labels are present verbatim, and fails loudly if any
listed file is missing or any verbatim parameter quote drifts.

Evidence-only: this test performs no scoring and no network access.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    WORKTREE / "research/control/prospective_shadow_v1/identity/identity_recovery.json"
)
README_PATH = (
    WORKTREE / "research/control/prospective_shadow_v1/identity/README.md"
)

EXPECTED_VERDICTS = {
    "ILLIQ-AMIHUD-28D-W": "V11_FAMILY_REJECT",
    "BASISLV-PREMFADE-28D": "V14_FAMILY_REJECT",
    "XSECT-FUND-CARRY-7D": "CANDIDATE_FAIL",
}


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(WORKTREE), *args], capture_output=True, check=check
    )


@pytest.fixture(scope="module")
def manifest() -> dict:
    assert MANIFEST_PATH.is_file(), f"missing manifest: {MANIFEST_PATH}"
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _raw_bytes(commit: str, path: str) -> bytes:
    """Exact bytes of a manifest-listed file, from git or the working tree."""
    if commit == "WORKING_TREE_TRACKED":
        p = WORKTREE / path
        assert p.is_file(), f"MISSING working-tree file: {p}"
        return p.read_bytes()
    proc = _git("show", f"{commit}:{path}", check=False)
    assert proc.returncode == 0, (
        f"MISSING git object {commit}:{path}: "
        f"{proc.stderr.decode(errors='replace')}"
    )
    return proc.stdout


def _expected_blob_sha(commit: str, path: str) -> str:
    if commit == "WORKING_TREE_TRACKED":
        return _git("hash-object", path).stdout.decode().strip()
    out = _git("ls-tree", commit, "--", path).stdout.decode().strip()
    assert out, f"git ls-tree returned nothing for {commit}:{path}"
    parts = out.split()
    assert parts[1] == "blob", out
    return parts[2]


# --------------------------------------------------------------------------- #
# Manifest structure
# --------------------------------------------------------------------------- #


def test_manifest_schema_and_three_families(manifest: dict) -> None:
    assert manifest["schema"] == "shv1_identity_recovery_v1"
    assert manifest["cycle_id"] == "PROSPECTIVE-SHADOW-V1"
    families = manifest["families"]
    assert len(families) == 3
    assert [f["family_id"] for f in families] == list(EXPECTED_VERDICTS)


def test_replay_label_is_declared(manifest: dict) -> None:
    assert "REPLAY_NOT_PROSPECTIVE" in manifest["replay_label_rule"]
    readme = README_PATH.read_text(encoding="utf-8")
    assert "REPLAY_NOT_PROSPECTIVE" in readme


def test_verdict_labels_arent_rewritable_statement(manifest: dict) -> None:
    policy = manifest["verdict_labels_policy"]
    for label in EXPECTED_VERDICTS.values():
        assert label in policy


# --------------------------------------------------------------------------- #
# Byte-level verification of every listed file
# --------------------------------------------------------------------------- #


def _iter_all_file_entries(manifest: dict):
    for fam in manifest["families"]:
        for e in fam["files"]:
            yield fam["family_id"], e
        ve = fam.get("verdict_evidence") or {}
        for e in ve.get("files", []):
            yield fam["family_id"], e


def test_every_listed_file_exists_and_hashes_match(manifest: dict) -> None:
    entries = list(_iter_all_file_entries(manifest))
    assert len(entries) >= 24  # 8+2 (f1) + 11+1 (f2) + 7 (f3), some overlap
    for owner, e in entries:
        commit, path = e["commit"], e["path"]
        raw = _raw_bytes(commit, path)  # asserts existence loudly
        assert hashlib.sha256(raw).hexdigest() == e["sha256_of_content"], (
            f"sha256 drift for {owner} file {commit}:{path}"
        )
        assert len(raw) == e["byte_len"], (
            f"byte_len drift for {owner} file {commit}:{path}"
        )
        assert _expected_blob_sha(commit, path) == e["git_blob_sha"], (
            f"git blob sha drift for {owner} file {commit}:{path}"
        )


def test_family3_is_working_tree_tracked_at_recovery_head(manifest: dict) -> None:
    fam = next(
        f for f in manifest["families"] if f["family_id"] == "XSECT-FUND-CARRY-7D"
    )
    assert fam["source_commit_sha"] == "WORKING_TREE_TRACKED"
    head = _git("rev-parse", "HEAD").stdout.decode().strip()
    assert fam["worktree_head_at_recovery"] == "bd5e3437dd90384f7754cc8e33acb96337500f2d"
    assert len(head) == 40  # current HEAD moves with this lane's commit; base is pinned
    # family 3 files must be tracked (not untracked junk) at the current HEAD
    for e in fam["files"]:
        ls = _git("ls-files", "--error-unmatch", e["path"], check=False)
        assert ls.returncode == 0, f"family 3 file not tracked: {e['path']}"


def test_identity_commits_exist(manifest: dict) -> None:
    for fam in manifest["families"]:
        commit = fam["source_commit_sha"]
        if commit == "WORKING_TREE_TRACKED":
            continue
        assert _git("cat-file", "-t", commit).stdout.decode().strip() == "commit"
    ve = next(
        f for f in manifest["families"] if f["family_id"] == "ILLIQ-AMIHUD-28D-W"
    )["verdict_evidence"]["source_commit_sha"]
    assert _git("cat-file", "-t", ve).stdout.decode().strip() == "commit"


# --------------------------------------------------------------------------- #
# Verdict labels and verbatim parameter bytes
# --------------------------------------------------------------------------- #


def test_historical_verdict_labels_verbatim(manifest: dict) -> None:
    for fam in manifest["families"]:
        expected = EXPECTED_VERDICTS[fam["family_id"]]
        assert fam["historical_verdict_label"] == expected
        found = False
        for e in fam["files"] + (fam.get("verdict_evidence") or {}).get("files", []):
            raw = _raw_bytes(e["commit"], e["path"])
            if expected.encode() in raw:
                found = True
                break
        assert found, (
            f"verdict label {expected} not found in any listed byte source "
            f"for {fam['family_id']}"
        )


def test_failure_metrics_quoted_from_bytes(manifest: dict) -> None:
    for fam in manifest["families"]:
        quotes = fam["historical_failure_metric_verbatim"]
        assert quotes, f"no verbatim failure metrics for {fam['family_id']}"
        by_source: dict[tuple[str, str], list[str]] = {}
        for q in quotes:
            src = q["source"]  # "<path>@<commit>"
            path, commit = src.rsplit("@", 1)
            raw = _raw_bytes(commit, path)
            assert q["quote"].encode() in raw, (
                f"verbatim quote not in bytes ({src}): {q['quote']!r}"
            )
            by_source.setdefault((commit, path), []).append(q["quote"])
        assert by_source


def test_verbatim_source_checks_pass(manifest: dict) -> None:
    checks = manifest["verbatim_source_checks"]
    assert set(checks) == set(EXPECTED_VERDICTS)
    for family, fam_checks in checks.items():
        assert fam_checks, f"no verbatim checks for {family}"
        for c in fam_checks:
            raw = _raw_bytes(c["commit"], c["file"])
            text = raw.decode("utf-8", errors="replace")
            for s in c["substrings"]:
                assert s in text, (
                    f"verbatim substring missing from {c['commit']}:{c['file']} "
                    f"({family}): {s!r}"
                )


def test_score_affecting_parameters_present(manifest: dict) -> None:
    required_keys = {
        "ILLIQ-AMIHUD-28D-W": [
            "feature", "book", "formation_days", "holding_days",
            "decision_clock", "universe", "costs_and_funding",
            "window.start", "window.end", "fold_policy",
        ],
        "BASISLV-PREMFADE-28D": [
            "direction", "funding_sign_convention", "decision_clock",
            "fill_rule", "side_rule", "min_eligible", "gross", "holding_days",
            "folds_contract", "window_start_iso", "window_end_iso",
            "recorded_anchor_arm_config_digest",
        ],
        "XSECT-FUND-CARRY-7D": [
            "traded_universe", "signal_clock", "feature", "lookback_days",
            "long_rule", "short_rule", "rebalance", "folds", "purge_embargo",
            "target_gross", "hard_gross_cap", "hard_abs_net_cap",
            "max_abs_weight_per_symbol",
        ],
    }
    for fam in manifest["families"]:
        params = fam["score_affecting_parameters"]
        for key in required_keys[fam["family_id"]]:
            assert key in params, (
                f"missing score-affecting parameter {key!r} for {fam['family_id']}"
            )


def test_identity_ambiguity_disclosed(manifest: dict) -> None:
    by_id = {f["family_id"]: f for f in manifest["families"]}
    assert by_id["ILLIQ-AMIHUD-28D-W"]["identity_ambiguity"] is None
    assert by_id["BASISLV-PREMFADE-28D"]["identity_ambiguity"] is None
    ambiguity = by_id["XSECT-FUND-CARRY-7D"]["identity_ambiguity"]
    assert isinstance(ambiguity, str) and ambiguity.strip()
    assert "TO_FREEZE_AT_AUTHORIZATION" in ambiguity
