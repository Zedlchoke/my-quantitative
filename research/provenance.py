"""Immutable input snapshots for scored experiments (Sprint V2, owner A3).

Implements PLAN.md H4-A3 provenance requirements: every scored run snapshots
the exact bytes of its config, candidate spec, universe and data-manifest into
``<exp_dir>/frozen/`` BEFORE results are consulted, computes actual SHA-256 of
each snapshot copy, and records git commit/dirty state, exact ``argv``, run
start time and the caller-supplied ``parameter_lock_utc``.

The returned dict carries ``ManifestV2Spec``-compatible field names so
``research.sprint_eval`` (V2 mode) can build the contract manifest directly.
``parameter_lock_utc`` MUST be strictly earlier than ``run_started_utc``;
violations surface through ``ManifestV2Spec.validate()`` as reason code
``lock_not_before_run``.

Tamper detection: :func:`verify_frozen_snapshots` recomputes hashes from the
frozen bytes on disk; any later modification of a snapshot yields reason
``hash_mismatch`` (fail-closed).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from contracts.protocol import sha256_file

FROZEN_DIRNAME = "frozen"
CONFIG_COPY_NAME = "config.yaml"
CANDIDATE_COPY_NAME = "candidate.yaml"
UNIVERSE_COPY_NAME = "universe.json"
DATA_MANIFEST_COPY_NAME = "data_manifest.json"

#: Frozen artifact-relative paths recorded in the manifest.
SNAPSHOT_FILES: dict[str, str] = {
    "frozen_config": f"{FROZEN_DIRNAME}/{CONFIG_COPY_NAME}",
    "frozen_candidate": f"{FROZEN_DIRNAME}/{CANDIDATE_COPY_NAME}",
    "universe_snapshot": f"{FROZEN_DIRNAME}/{UNIVERSE_COPY_NAME}",
    "data_manifest": f"{FROZEN_DIRNAME}/{DATA_MANIFEST_COPY_NAME}",
}


def _git_state(repo: str | Path | None) -> tuple[str, bool]:
    """Return ``(commit_sha, dirty_flag)`` for the working tree at ``repo``."""

    def _run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=str(repo) if repo else None,
            capture_output=True,
            text=True,
            check=False,
        )

    head = _run("rev-parse", "HEAD")
    commit = head.stdout.strip() if head.returncode == 0 and head.stdout.strip() else "unknown"
    status = _run("status", "--porcelain")
    dirty = status.returncode == 0 and status.stdout.strip() != ""
    return commit, dirty


def _copy_bytes(source: Path, destination: Path) -> None:
    """Byte-exact copy; refuses missing sources (fail-closed)."""
    if not source.is_file():
        raise FileNotFoundError(f"snapshot source missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())


def snapshot_experiment_inputs(
    exp_dir: str | Path,
    *,
    config_path: str | Path,
    candidate_path: str | Path,
    universe_symbols: Sequence[str],
    requested_window: tuple[Any, Any],
    data_manifest_path: str | Path,
    parameter_lock_utc: str,
    git_repo: str | Path | None = None,
) -> dict[str, Any]:
    """Freeze experiment inputs into ``exp_dir/frozen/`` and record provenance.

    Copies config/candidate/universe/data-manifest BYTES, computes actual
    SHA-256 of each frozen copy, captures ``git rev-parse HEAD`` + dirty flag,
    exact ``sys.argv`` and ``run_started_utc`` at call time.  Returns a dict
    whose keys align with ``contracts.protocol.ManifestV2Spec`` fields plus an
    audit ``sources`` block with the original absolute paths.

    ``parameter_lock_utc`` is caller-supplied and stored verbatim; it must be
    strictly earlier than ``run_started_utc`` (enforced by manifest validate).
    """
    exp_path = Path(exp_dir)
    frozen_dir = exp_path / FROZEN_DIRNAME

    universe_doc = {
        "schema_version": 2,
        "symbols": [str(symbol) for symbol in universe_symbols],
        "requested_window": {
            "start_utc": pd_or_iso(requested_window[0]),
            "end_utc": pd_or_iso(requested_window[1]),
        },
    }

    copies = [
        (Path(config_path), frozen_dir / CONFIG_COPY_NAME),
        (Path(candidate_path), frozen_dir / CANDIDATE_COPY_NAME),
        (Path(data_manifest_path), frozen_dir / DATA_MANIFEST_COPY_NAME),
    ]
    for source, destination in copies:
        _copy_bytes(source, destination)
    universe_target = frozen_dir / UNIVERSE_COPY_NAME
    universe_target.parent.mkdir(parents=True, exist_ok=True)
    universe_target.write_text(
        json.dumps(universe_doc, indent=2, sort_keys=True), encoding="utf-8"
    )

    # run_started captured AFTER the freeze so lock < start always holds when
    # the caller takes its lock timestamp before calling this function.
    run_started = datetime.now(timezone.utc).isoformat()
    commit, dirty = _git_state(git_repo)

    return {
        "parameter_lock_utc": parameter_lock_utc,
        "run_started_utc": run_started,
        "git_commit_at_launch": commit,
        "dirty_worktree_at_launch": dirty,
        "exact_argv": tuple(str(arg) for arg in sys.argv),
        "frozen_config_path": SNAPSHOT_FILES["frozen_config"],
        "frozen_config_sha256": sha256_file(frozen_dir / CONFIG_COPY_NAME),
        "frozen_candidate_path": SNAPSHOT_FILES["frozen_candidate"],
        "frozen_candidate_sha256": sha256_file(frozen_dir / CANDIDATE_COPY_NAME),
        "data_manifest_path": SNAPSHOT_FILES["data_manifest"],
        "data_manifest_sha256": sha256_file(frozen_dir / DATA_MANIFEST_COPY_NAME),
        "universe_snapshot_path": SNAPSHOT_FILES["universe_snapshot"],
        "universe_snapshot_sha256": sha256_file(universe_target),
        "requested_start_utc": universe_doc["requested_window"]["start_utc"],
        "requested_end_utc": universe_doc["requested_window"]["end_utc"],
        "sources": {
            "config_path": str(config_path),
            "candidate_path": str(candidate_path),
            "data_manifest_path": str(data_manifest_path),
        },
    }


def pd_or_iso(value: Any) -> str:
    """ISO-8601 UTC string from a timestamp-like value (no pandas import)."""
    iso = getattr(value, "isoformat", None)
    if callable(iso):
        text = str(iso())
    else:
        text = str(value)
    if "T" not in text:
        text = text.replace(" ", "T", 1)
    return text


def verify_frozen_snapshots(snapshot: dict, exp_dir: str | Path) -> list[str]:
    """Recompute frozen-copy hashes; return reason codes for any mismatch.

    ``exp_dir`` is the experiment directory holding the artifact-local frozen
    paths recorded in the snapshot.  A missing file or a byte change yields
    fail-closed reason codes (``manifest_missing_field`` / ``hash_mismatch``).
    """
    base = Path(exp_dir)
    checks = (
        ("frozen_config_sha256", SNAPSHOT_FILES["frozen_config"]),
        ("frozen_candidate_sha256", SNAPSHOT_FILES["frozen_candidate"]),
        ("data_manifest_sha256", SNAPSHOT_FILES["data_manifest"]),
        ("universe_snapshot_sha256", SNAPSHOT_FILES["universe_snapshot"]),
    )
    reasons: list[str] = []
    for key, relative in checks:
        target = base / relative
        if not target.is_file():
            reasons.append("manifest_missing_field")
            continue
        if sha256_file(target) != snapshot.get(key):
            reasons.append("hash_mismatch")
    return sorted(set(reasons))


def build_manifest_v2(snapshot: dict, **spec_fields: Any):
    """Assemble a ``ManifestV2Spec`` from a snapshot + caller-provided fields.

    Snapshot keys win only where the caller does not supply an explicit
    override.  Raises ``TypeError`` when required fields are still missing;
    call ``.validate()`` on the result for reason-code level validation.
    """
    from contracts.protocol import ManifestV2Spec

    merged: dict[str, Any] = {k: v for k, v in snapshot.items() if k != "sources"}
    merged.update(spec_fields)
    merged.setdefault("schema_version", 2)
    known = {name for name in ManifestV2Spec.__dataclass_fields__}
    unknown = sorted(set(merged) - known)
    if unknown:
        raise TypeError(f"unknown ManifestV2Spec fields: {unknown}")
    return ManifestV2Spec(**{name: merged[name] for name in known})
