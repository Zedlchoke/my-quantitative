"""Fixture manifest validation: happy path at the repo root plus mutation
cases. Mutations run against TMP COPIES of the manifest layout — the
committed manifest is never corrupted in place. Exercises the shared
convention that later lanes extend via fixture_entries.json fragments
(infrastructure, never violations).
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from governance import fixture_manifest  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_REL = Path("tests/fixtures/governance_fixture_manifest.json")


def _make_tmp_repo(tmp_path: Path) -> Path:
    """Copy the committed tests/fixtures/ layout into a tmp repo root."""
    shutil_root = tmp_path / "repo"
    (shutil_root / "tests").mkdir(parents=True)
    copy_tree(REPO_ROOT / "tests" / "fixtures", shutil_root / "tests" / "fixtures")
    return shutil_root


def copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        if item.is_dir():
            (dst / rel).mkdir(parents=True, exist_ok=True)
        else:
            (dst / rel).write_bytes(item.read_bytes())


def _load_manifest(repo_root: Path) -> dict:
    return json.loads((repo_root / MANIFEST_REL).read_text(encoding="utf-8"))


def _write_manifest(repo_root: Path, manifest: dict) -> None:
    (repo_root / MANIFEST_REL).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def test_manifest_valid_at_repo_root():
    """Happy path: the committed manifest accounts for every fixture file."""
    problems = fixture_manifest.validate_fixture_manifest(REPO_ROOT)
    assert problems == [], f"committed manifest must be valid, got: {problems}"


def test_tampered_digest_is_a_problem(tmp_path):
    root = _make_tmp_repo(tmp_path)
    manifest = _load_manifest(root)
    manifest["fixtures"][0]["sha256"] = "0" * 64  # valid hex, wrong bytes
    _write_manifest(root, manifest)
    problems = fixture_manifest.validate_fixture_manifest(root)
    assert any("sha256 mismatch" in p for p in problems)
    assert fixture_manifest.main(["--repo-root", str(root)]) == 1


def test_unknown_class_is_a_problem(tmp_path):
    root = _make_tmp_repo(tmp_path)
    manifest = _load_manifest(root)
    manifest["fixtures"][0]["class"] = "NOT_A_REAL_CLASS"
    _write_manifest(root, manifest)
    problems = fixture_manifest.validate_fixture_manifest(root)
    assert any("unknown fixture class" in p for p in problems)


def test_path_escape_entry_is_a_problem(tmp_path):
    root = _make_tmp_repo(tmp_path)
    manifest = _load_manifest(root)
    manifest["fixtures"][0]["path"] = "../outside/research_secrets.json"
    _write_manifest(root, manifest)
    problems = fixture_manifest.validate_fixture_manifest(root)
    assert any("path escape" in p for p in problems)


def test_duplicate_fixture_id_is_a_problem(tmp_path):
    root = _make_tmp_repo(tmp_path)
    manifest = _load_manifest(root)
    manifest["fixtures"].append(copy.deepcopy(manifest["fixtures"][0]))
    _write_manifest(root, manifest)
    problems = fixture_manifest.validate_fixture_manifest(root)
    assert any("duplicate fixture_id" in p for p in problems)


def test_unaccounted_fixture_file_is_a_problem(tmp_path):
    root = _make_tmp_repo(tmp_path)
    stray = root / "tests" / "fixtures" / "legacy_adapters" / "stray.json"
    stray.write_text('{"schema": "stray"}\n', encoding="utf-8")
    problems = fixture_manifest.validate_fixture_manifest(root)
    assert any("unaccounted fixture file" in p and "stray.json" in p
               for p in problems)


def test_fixture_entries_fragment_is_infrastructure_not_violation(tmp_path):
    """The v9-lane pattern: a new fixtures subdirectory accounted for by its
    own fixture_entries.json fragment validates clean — the fragment file
    itself never needs an entry, and the scan finds the fragment's files."""
    root = _make_tmp_repo(tmp_path)
    frag_dir = root / "tests" / "fixtures" / "v9_universe_audit"
    frag_dir.mkdir(parents=True)
    sample = frag_dir / "sample.json"
    sample.write_text('{"schema": "x"}\n', encoding="utf-8")
    fragment = {
        "schema": "governance_fixture_manifest@1",
        "fixtures": [{
            "fixture_id": "fx-v9-audit-sample",
            "path": "tests/fixtures/v9_universe_audit/sample.json",
            "class": "SYNTHETIC_HAND_COMPUTED",
            "purpose": "tmp-repo fragment entry proving the fragment pattern",
            "sha256": hashlib.sha256(sample.read_bytes()).hexdigest(),
            "license_authority": "repo-owner-authored synthetic fixture",
            "contains_real_provider_payload": False,
            "contains_secret": False,
            "expected_consumers": ["tests/test_fixture_manifest.py::"
                                   "test_fixture_entries_fragment_is_infrastructure_not_violation"],
            "expected_semantics": ["fragment entries validate like canonical entries"],
        }],
    }
    (frag_dir / "fixture_entries.json").write_text(
        json.dumps(fragment, indent=2) + "\n", encoding="utf-8")
    assert fixture_manifest.validate_fixture_manifest(root) == []


def test_cli_exit_codes(tmp_path, capsys):
    # fail-closed contract: valid committed manifest -> exit 0
    assert fixture_manifest.main(["--repo-root", str(REPO_ROOT)]) == 0
    broken = _make_tmp_repo(tmp_path)
    manifest = _load_manifest(broken)
    manifest["fixtures"][1]["class"] = "BOGUS"
    _write_manifest(broken, manifest)
    assert fixture_manifest.main(["--repo-root", str(broken)]) == 1
    out = capsys.readouterr().out
    assert "FIXTURE-MANIFEST PROBLEM" in out
