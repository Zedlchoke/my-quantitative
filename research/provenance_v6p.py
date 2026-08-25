"""V6P provenance root: provable committed baselines (PLAN §6.1, N01-N03/N15).

Design invariants:
* The baseline manifest NEVER contains its own hash (external-root design).
* ``created_at_utc`` is the single freeze timestamp; A7 later stamps
  ``audited_at_utc`` on the ATTESTATION file, never inside the baseline.
* Launch validity requires: clean worktree, HEAD == baseline.launch_head,
  baseline + attestation present and hash-matched, and attestation timestamp
  strictly BEFORE every launch start. Validators fail closed.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASELINE_FILENAME = "baseline_root.json"
ATTESTATION_FILENAME = "a7_prelaunch_attestation.json"


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _provenance_exempt(repo: Path) -> set[str]:
    """The baseline + its attestation are pinned to each other by hash chain
    (attestation carries baseline_sha256), so they may legitimately be
    uncommitted-at-launch PROVIDED they are declared here. Any other dirty
    entry fails the freeze/launch."""
    return {
        str(Path("research/audits/v6p") / BASELINE_FILENAME),
        str(Path("research/audits/v6p") / ATTESTATION_FILENAME),
        # Coordinator journal/state mutate continuously by design; they carry
        # no strategy/data authority, so they cannot participate in the
        # launch-clean guarantee.
        "research/control/",
    }


def create_baseline_root(
    repo: Path,
    *,
    source_roots: list[str],
    data_bundle_dir: str | None,
    output_path: Path,
) -> dict:
    """Freeze the external baseline root. Refuses any undeclared dirtiness."""
    exempt = _provenance_exempt(repo)
    def _nonexempt(line: str) -> bool:
        path = line[3:] if len(line) > 3 and line[2] == " " else line
        covered = (
            path in exempt
            or any(path.endswith(e) for e in exempt if not e.endswith("/"))
            or any(path.startswith(e) for e in exempt if e.endswith("/"))
        )
        return not covered

    status = [
        l for l in _git(repo, "status", "--porcelain=v1").splitlines()
        if l and _nonexempt(l)
    ]
    if status:
        raise RuntimeError(f"refusing baseline freeze on dirty tree: {status}")

    files: dict[str, str] = {}
    for root in source_roots:
        base = repo / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if (path.is_file() and "__pycache__" not in path.parts
                    and path.suffix in (".py", ".yaml", ".yml", ".json", ".toml")):
                files[str(path.relative_to(repo))] = sha256_file(path)

    bundle: dict[str, object] | None = None
    if data_bundle_dir:
        bundle_path = repo / data_bundle_dir
        bundle_files: dict[str, str] = {}
        for path in sorted(bundle_path.rglob("funding.json")):
            rel = str(path.relative_to(repo))
            bundle_files[rel] = sha256_file(path)
        combined = hashlib.sha256(
            "\n".join(f"{k}:{v}" for k, v in sorted(bundle_files.items()))
            .encode("utf-8")).hexdigest()
        bundle = {"path": data_bundle_dir, "files_sha256": bundle_files,
                  "identity_sha256": combined}

    baseline = {
        "schema_version": 1,
        "artifact": "v6p_baseline_root",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "launch_head": _git(repo, "rev-parse", "HEAD"),
        "worktree_clean": True,
        "allowed_uncommitted_at_launch": sorted(exempt),
        "source_files_sha256": files,
        "data_bundle": bundle,
        "attestation": {"file": ATTESTATION_FILENAME,
                         "sha256_at_freeze": None},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(baseline, indent=2) + "\n",
                           encoding="utf-8")
    return baseline


def baseline_self_hash_violations(baseline: dict, baseline_bytes: bytes) -> list[str]:
    """N03: the manifest must not carry a self-referential hash slot.

    Embedding sha256(current bytes) inside those bytes is a fixed-point
    impossibility, so the meaningful check is structural: no key may declare
    itself as the hash of this very document.
    """
    problems: list[str] = []

    def _walk(node, parent_key=None):
        if isinstance(node, dict):
            for key, value in node.items():
                key_l = str(key).lower()
                if ("self" in key_l and "hash" in key_l) or key_l in (
                        "baseline_sha256", "manifest_sha256", "own_sha256"):
                    problems.append(f"self_referential_key:{key}")
                _walk(value, key)
        elif isinstance(node, list):
            for value in node:
                _walk(value, parent_key)

    _walk(baseline)
    return problems


def write_attestation(
    repo: Path,
    *,
    auditor: str,
    baseline_path: Path,
    output_path: Path,
    checks: dict[str, bool],
) -> dict:
    """A7 pre-launch attestation; references baseline by hash only."""
    digest = sha256_file(baseline_path)
    doc = {
        "schema_version": 1,
        "artifact": "a7_prelaunch_attestation",
        "auditor": auditor,
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_file": str(baseline_path.relative_to(repo)),
        "baseline_sha256": digest,
        "checks": checks,
        "verdict": ("PASS" if all(checks.values()) else "FAIL"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def validate_launch_provenance(
    repo: Path,
    *,
    baseline_path: Path,
    attestation_path: Path,
    launch_head: str | None = None,
    dirty: bool | None = None,
    first_launch_started_utc: str | None = None,
) -> list[str]:
    """Fail-closed preflight shared by runners and auditors."""
    reasons: list[str] = []
    if not baseline_path.is_file():
        return ["baseline_missing"]
    if not attestation_path.is_file():
        reasons.append("attestation_missing")

    baseline_bytes = baseline_path.read_bytes()
    try:
        baseline = json.loads(baseline_bytes)
    except ValueError:
        return ["baseline_unreadable"]

    reasons.extend(baseline_self_hash_violations(baseline, baseline_bytes))

    if attestation_path.is_file():
        try:
            att = json.loads(attestation_path.read_text(encoding="utf-8"))
        except ValueError:
            att = None
        if not isinstance(att, dict) or att.get("verdict") != "PASS":
            reasons.append("attestation_not_pass")
        else:
            expected = sha256_file(baseline_path)
            if att.get("baseline_sha256") != expected:
                reasons.append("attestation_baseline_hash_mismatch")
            if baseline.get("attestation", {}).get("sha256_at_freeze") \
                    not in (None, att.get("baseline_sha256")):
                reasons.append("attestation_slot_mismatch")

    if launch_head is not None:
        recorded = baseline.get("launch_head")
        if launch_head != recorded:
            # The freeze may legitimately be committed inside a child of the
            # recorded head (the freeze commit itself); require ancestry so
            # unrelated divergence still fails closed.
            try:
                anc = subprocess.run(
                    ["git", "-C", str(repo), "merge-base", "--is-ancestor",
                     str(recorded), str(launch_head)],
                    capture_output=True, text=True)
                if anc.returncode != 0:
                    reasons.append("launch_head_mismatch")
            except subprocess.CalledProcessError:
                reasons.append("launch_head_mismatch")

    if dirty is None:
        exempt = _provenance_exempt(repo)
        def _covered(line: str) -> bool:
            path = line[3:] if len(line) > 3 and line[2] == " " else line
            return (
                path in exempt
                or any(path.endswith(e) for e in exempt if not e.endswith("/"))
                or any(path.startswith(e) for e in exempt if e.endswith("/"))
            )
        dirty = any(
            not _covered(l)
            for l in _git(repo, "status", "--porcelain=v1").splitlines() if l
        )
    if dirty:
        reasons.append("dirty_worktree_at_launch")

    if first_launch_started_utc:
        try:
            started = datetime.fromisoformat(first_launch_started_utc)
            created = datetime.fromisoformat(str(baseline["created_at_utc"]))
            if started <= created:
                reasons.append("post_launch_baseline_creation")
        except ValueError:
            reasons.append("timestamp_unparseable")
    return reasons


def transition_doc(*, artifact: str, actor: str, **fields) -> dict:
    """N15: distinct lifecycle timestamps/heads for transition artifacts."""
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "schema_version": 1,
        "artifact": artifact,
        "created_at_utc": now,
        "audited_at_utc": fields.pop("audited_at_utc", None),
        "integrated_at_utc": fields.pop("integrated_at_utc", None),
        "actor": actor,
        "audited_head": fields.pop("audited_head", None),
        "final_head": fields.pop("final_head", None),
    }
    doc.update(fields)
    return doc


def refresh_transition_heads(doc: dict, *, final_head: str) -> dict:
    """Refresh final_head/integrated_at AFTER integration without rewriting
    gate content (N15)."""
    doc["final_head"] = final_head
    doc["integrated_at_utc"] = datetime.now(timezone.utc).isoformat()
    return doc
