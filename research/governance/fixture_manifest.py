"""Governance fixture manifest: repo-wide accountability for tests/fixtures/.

Shared repo convention (MDP-V2R1 D1). Every file under tests/fixtures/ must be
accounted for by a manifest entry declaring WHAT the bytes are and WHO may
consume them:

- the canonical manifest is tests/fixtures/governance_fixture_manifest.json;
- any ``fixture_entries.json`` fragment anywhere under tests/fixtures/ is
  INFRASTRUCTURE, not a violation: later lanes deliver their fixture
  accounting as fragments and this loader merges those entries into the
  validation set (the fragment file itself never needs an entry);
- validation is fail-closed: a wrong digest, an unknown fixture class, a path
  escaping tests/fixtures/, duplicate fixture_id/path, secret-like content,
  missing required fields, or ANY unaccounted fixture file is a problem.

API: :func:`validate_fixture_manifest` returns the list of problems (empty ==
valid). CLI: ``python -m governance.fixture_manifest`` exits 0 when the
manifest is valid and 1 when any problem is found (never silent, never
auto-repairs). The module never writes anything under tests/fixtures/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

SCHEMA_ID = "governance_fixture_manifest@1"
MANIFEST_REL = "tests/fixtures/governance_fixture_manifest.json"
FIXTURES_DIR_REL = "tests/fixtures"
FRAGMENT_NAME = "fixture_entries.json"

ALLOWED_CLASSES = (
    "SYNTHETIC_HAND_COMPUTED",
    "SCHEMA_MINIMAL",
    "REDISTRIBUTABLE_PINNED",
    "DERIVED_NON_REVERSIBLE",
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")

# secret-like content patterns: a fixture carrying any of these is a problem
SECRET_PATTERNS = (
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key id"),
    (re.compile(r"(?i)api[_-]?key\s*="), "api key assignment"),
    (re.compile(r"\"password\"\s*:"), "password field"),
)

_REQUIRED_STR_FIELDS = ("fixture_id", "path", "class", "purpose",
                        "license_authority")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _default_repo_root() -> Path:
    """Repo root via the enclosing git worktree of cwd; cwd as fallback."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return Path(out)
    except (OSError, subprocess.CalledProcessError):
        pass
    return Path.cwd()


def _load_json(path: Path) -> Tuple[Optional[dict], Optional[str]]:
    try:
        obj = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"{path}: unparseable manifest json: {exc}"
    if not isinstance(obj, dict):
        return None, f"{path}: manifest must be a json object"
    return obj, None


def _iter_entries(repo_root: Path) -> Tuple[List[Tuple[dict, str]], List[str]]:
    """Collect canonical + fragment entries as (entry, origin_label) pairs."""
    problems: List[str] = []
    entries: List[Tuple[dict, str]] = []
    manifest_path = repo_root / MANIFEST_REL
    manifest, err = _load_json(manifest_path)
    if err:
        problems.append(err)
        return entries, problems
    if manifest.get("schema") != SCHEMA_ID:
        problems.append(
            f"{MANIFEST_REL}: schema must be {SCHEMA_ID!r}, got {manifest.get('schema')!r}"
        )
    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list):
        problems.append(f"{MANIFEST_REL}: 'fixtures' must be a list")
        return entries, problems
    for i, entry in enumerate(fixtures):
        entries.append((entry, f"{MANIFEST_REL}#fixtures[{i}]"))
    fixtures_root = (repo_root / FIXTURES_DIR_REL).resolve()
    if fixtures_root.is_dir():
        for fragment in sorted(fixtures_root.rglob(FRAGMENT_NAME)):
            frag_obj, err = _load_json(fragment)
            if err:
                problems.append(err)
                continue
            frag_fixtures = frag_obj.get("fixtures")
            if not isinstance(frag_fixtures, list):
                problems.append(
                    f"{fragment.relative_to(repo_root)}: 'fixtures' must be a list"
                )
                continue
            rel = fragment.relative_to(repo_root)
            for i, entry in enumerate(frag_fixtures):
                entries.append((entry, f"{rel}#fixtures[{i}]"))
    return entries, problems


def _validate_entry(entry, origin: str, repo_root: Path,
                    seen_ids: dict, seen_paths: dict,
                    fixtures_root: Path) -> List[str]:
    problems: List[str] = []
    if not isinstance(entry, dict):
        return [f"{origin}: entry must be a json object"]
    fid = entry.get("fixture_id")
    if not isinstance(fid, str) or not fid.strip():
        problems.append(f"{origin}: fixture_id must be a non-empty string")
        fid = None
    elif fid in seen_ids:
        problems.append(
            f"{origin}: duplicate fixture_id {fid!r} (already declared in {seen_ids[fid]})"
        )
    else:
        seen_ids[fid] = origin
    for field in _REQUIRED_STR_FIELDS:
        val = entry.get(field)
        if not isinstance(val, str) or not val.strip():
            problems.append(f"{origin}: {field} must be a non-empty string")
    klass = entry.get("class")
    if klass not in ALLOWED_CLASSES:
        problems.append(
            f"{origin}: unknown fixture class {klass!r} (allowed: {', '.join(ALLOWED_CLASSES)})"
        )
    for field in ("contains_real_provider_payload", "contains_secret"):
        if entry.get(field) is not False:
            problems.append(f"{origin}: {field} must be exactly false")
    for field in ("expected_consumers", "expected_semantics"):
        val = entry.get(field)
        if not (isinstance(val, list) and val
                and all(isinstance(x, str) and x.strip() for x in val)):
            problems.append(
                f"{origin}: {field} must be a non-empty list of non-empty strings"
            )
    digest = entry.get("sha256")
    if not (isinstance(digest, str) and _HEX64.match(digest)):
        problems.append(
            f"{origin}: sha256 must be 64 lowercase hex chars, got {digest!r}"
        )
    path_val = entry.get("path")
    rel_norm = None
    if not isinstance(path_val, str) or not path_val.strip():
        problems.append(f"{origin}: path must be a non-empty string")
    else:
        candidate = Path(path_val)
        if candidate.is_absolute():
            problems.append(
                f"{origin}: path must be repo-relative, got absolute {path_val!r}"
            )
        else:
            resolved = (repo_root / candidate).resolve()
            if resolved != fixtures_root and fixtures_root not in resolved.parents:
                problems.append(
                    f"{origin}: path escape: {path_val!r} resolves to {resolved}, "
                    f"outside {FIXTURES_DIR_REL}/"
                )
            else:
                rel_norm = Path(path_val)
                if rel_norm in seen_paths:
                    problems.append(
                        f"{origin}: duplicate path {path_val!r} "
                        f"(already declared in {seen_paths[rel_norm]})"
                    )
                else:
                    seen_paths[rel_norm] = origin
                if not resolved.is_file():
                    problems.append(f"{origin}: fixture file missing: {path_val!r}")
                else:
                    if isinstance(digest, str) and _HEX64.match(digest):
                        actual = _sha256_file(resolved)
                        if actual != digest:
                            problems.append(
                                f"{origin}: sha256 mismatch for {path_val!r}: "
                                f"manifest says {digest}, file bytes hash to {actual}"
                            )
                    try:
                        text = resolved.read_bytes().decode("utf-8", errors="replace")
                    except OSError as exc:
                        problems.append(f"{origin}: fixture file unreadable: {exc}")
                    else:
                        for pattern, label in SECRET_PATTERNS:
                            if pattern.search(text):
                                problems.append(
                                    f"{origin}: secret-like content in {path_val!r} "
                                    f"({label}); fixtures must never carry secrets"
                                )
    return problems


def _unaccounted_files(repo_root: Path, seen_paths: dict) -> List[str]:
    fixtures_root = (repo_root / FIXTURES_DIR_REL).resolve()
    if not fixtures_root.is_dir():
        return [f"{FIXTURES_DIR_REL}/ is missing entirely"]
    manifest_path = (repo_root / MANIFEST_REL).resolve()
    problems: List[str] = []
    for path in sorted(fixtures_root.rglob("*")):
        if not path.is_file():
            continue
        if path.resolve() == manifest_path:
            continue  # the manifest itself is infrastructure
        if path.name == FRAGMENT_NAME:
            continue  # fragments are infrastructure, never violations
        if any(part == "__pycache__" for part in path.parts):
            continue
        if path.name == ".DS_Store":
            continue
        rel = Path(path).relative_to(repo_root)
        if rel not in seen_paths:
            problems.append(
                f"unaccounted fixture file: {rel.as_posix()} — every file under "
                f"{FIXTURES_DIR_REL}/ needs a manifest entry (here or in a "
                f"{FRAGMENT_NAME} fragment)"
            )
    return problems


def validate_fixture_manifest(repo_root) -> List[str]:
    """Validate the fixture manifest for the repo at ``repo_root``.

    Returns the list of problems; an empty list means the manifest is valid.
    Checks: manifest presence/schema, per-entry required fields, allowed
    fixture classes, path confinement inside tests/fixtures/, digest match
    against the actual file bytes, secret-like content scan, duplicate
    fixture_id/path (canonical + fragments), and full coverage of every file
    under tests/fixtures/ (manifest, fixture_entries.json fragments and
    __pycache__ are infrastructure and never need an entry).
    """
    repo_root = Path(repo_root).resolve()
    fixtures_root = (repo_root / FIXTURES_DIR_REL).resolve()
    entries, problems = _iter_entries(repo_root)
    seen_ids: dict = {}
    seen_paths: dict = {}
    for entry, origin in entries:
        problems.extend(
            _validate_entry(entry, origin, repo_root, seen_ids, seen_paths,
                            fixtures_root)
        )
    problems.extend(_unaccounted_files(repo_root, seen_paths))
    return problems


def main(argv=None) -> int:
    """Fail-closed CLI: exit 0 when the manifest is valid, 1 on any problem."""
    parser = argparse.ArgumentParser(
        description="Validate the governance fixture manifest (fail-closed)."
    )
    parser.add_argument(
        "--repo-root", default=None,
        help="Repo root to validate (default: enclosing git worktree of cwd).",
    )
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else _default_repo_root()
    try:
        problems = validate_fixture_manifest(repo_root)
    except Exception as exc:  # fail closed: any internal failure is a problem
        print(f"FIXTURE-MANIFEST PROBLEM: validation crashed: {exc!r}")
        return 1
    if problems:
        for problem in problems:
            print(f"FIXTURE-MANIFEST PROBLEM: {problem}")
        print(f"fixture manifest INVALID: {len(problems)} problem(s) under {repo_root}")
        return 1
    print(f"fixture manifest valid (repo root: {repo_root})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
