"""Runtime path resolution for the Quant Shadow Dashboard app.

The app must find the PROSPECTIVE-SHADOW-V1 runtime data on its own
(registry/worktree driven — never a hard-coded wrong checkout).

Resolution order (first valid wins):

1. ``QUANT_SHADOW_RUNTIME_ROOT`` env var pointing directly at the
   runtime root (the dir holding ``ledgers/`` + ``valuation_marks/``).
2. ``QUANT_SHADOW_REPO`` env var pointing at a repo checkout whose
   ``plans/CYCLE_REGISTRY.json`` names the integration worktree.
3. The marker file ``~/Library/Application Support/QuantShadowDashboard/
   runtime_root.txt`` written by the app on a previous successful run.
4. ``/Users/*/my-quantitative`` globs (the standard clone location on
   this machine) resolved through the cycle registry.

A candidate is valid only when its ``ledgers/`` dir exists with at
least one ``*.jsonl`` family ledger AND the runtime dir exists. The
result is cross-checked against the ``runtime_root`` field inside the
valuation heartbeat when that file is readable.
"""

from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

CYCLE_ID = "PROSPECTIVE-SHADOW-V1"
RUNTIME_SUBPATH = os.path.join("results", "prospective_shadow_v1")
REGISTRY_RELPATH = os.path.join("plans", "CYCLE_REGISTRY.json")
IDENTITY_RELPATH = os.path.join(
    "research", "control", "prospective_shadow_v1", "identity",
    "identity_recovery.json",
)
APP_SUPPORT_DIR = os.path.expanduser(
    "~/Library/Application Support/QuantShadowDashboard"
)
MARKER_PATH = os.path.join(APP_SUPPORT_DIR, "runtime_root.txt")


@dataclass(frozen=True)
class RuntimePaths:
    repo_root: Optional[str]
    worktree: Optional[str]
    runtime_root: str
    source: str
    identity_manifest: Optional[str] = None

    @property
    def ledgers_dir(self) -> str:
        return os.path.join(self.runtime_root, "ledgers")

    @property
    def valuation_dir(self) -> str:
        return os.path.join(self.runtime_root, "valuation_marks")

    @property
    def runtime_dir(self) -> str:
        return os.path.join(self.runtime_root, "runtime")

    @property
    def heartbeat_path(self) -> str:
        return os.path.join(self.runtime_dir, "heartbeat.json")

    @property
    def valuation_heartbeat_path(self) -> str:
        return os.path.join(self.runtime_dir, "valuation_heartbeat.json")

    def fingerprint_files(self) -> List[str]:
        """Every file whose bytes influence the snapshot (for stat-keyed
        incremental refresh). Missing files are fingerprinted as absent."""
        files: List[str] = []
        for base in (self.ledgers_dir, self.valuation_dir):
            if os.path.isdir(base):
                files.extend(
                    os.path.join(base, name)
                    for name in sorted(os.listdir(base))
                    if name.endswith(".jsonl")
                )
        files.append(self.heartbeat_path)
        files.append(self.valuation_heartbeat_path)
        if self.identity_manifest:
            files.append(self.identity_manifest)
        return files

    def describe(self) -> Dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "worktree": self.worktree,
            "runtime_root": self.runtime_root,
            "ledgers_dir": self.ledgers_dir,
            "valuation_marks_dir": self.valuation_dir,
            "heartbeat": self.heartbeat_path,
            "valuation_heartbeat": self.valuation_heartbeat_path,
            "identity_manifest": self.identity_manifest,
            "resolved_via": self.source,
        }


def load_registry_row(repo_root: str) -> Optional[Dict[str, Any]]:
    """Return the PROSPECTIVE-SHADOW-V1 row from a checkout's registry."""
    path = os.path.join(repo_root, REGISTRY_RELPATH)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None

    def _walk(node: Any) -> Optional[Dict[str, Any]]:
        if isinstance(node, dict):
            if node.get("cycle_id") == CYCLE_ID:
                return node
            for value in node.values():
                found = _walk(value)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for value in node:
                found = _walk(value)
                if found is not None:
                    return found
        return None

    return _walk(data)


def _is_valid_runtime(root: str) -> bool:
    ledgers = os.path.join(root, "ledgers")
    if not os.path.isdir(ledgers):
        return False
    if not any(name.endswith(".jsonl") for name in os.listdir(ledgers)):
        return False
    return os.path.isdir(os.path.join(root, "runtime")) or os.path.isdir(
        os.path.join(root, "valuation_marks")
    )


def _cross_check_heartbeat(root: str) -> Optional[str]:
    """The valuation heartbeat publishes its own runtime_root; when
    readable and mismatched, the directory is rejected (defence against
    a stale copy of the tree)."""
    path = os.path.join(root, "runtime", "valuation_heartbeat.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        declared = data.get("runtime_root")
    except (OSError, ValueError):
        return None
    if isinstance(declared, str) and declared.strip():
        if os.path.abspath(declared) != os.path.abspath(root):
            return None  # unreadable verdict -> do not cross-reject
        return declared
    return None


def _from_repo(repo_root: str, source: str) -> Optional[RuntimePaths]:
    repo_root = os.path.abspath(repo_root)
    row = load_registry_row(repo_root)
    worktree = row.get("integration_worktree") if row else None
    candidates: List[Tuple[Optional[str], str]] = []
    if isinstance(worktree, str) and worktree:
        candidates.append((worktree, f"{source}:registry.integration_worktree"))
        candidates.append((repo_root, f"{source}:registry.row_on_repo_root"))
    candidates.append((repo_root, f"{source}:repo_root_fallback"))
    for wt, via in candidates:
        runtime_root = os.path.join(wt, RUNTIME_SUBPATH)
        if _is_valid_runtime(runtime_root):
            identity = os.path.join(wt, IDENTITY_RELPATH)
            return RuntimePaths(
                repo_root=repo_root,
                worktree=wt if wt != repo_root else None,
                runtime_root=runtime_root,
                source=via,
                identity_manifest=identity if os.path.isfile(identity) else None,
            )
    return None


def _candidate_roots(env: Any) -> List[str]:
    roots: List[str] = []
    for env_name in ("QUANT_SHADOW_REPO",):
        value = env.get(env_name)
        if value:
            roots.append(("env:" + env_name, value))
    marker: List[Tuple[str, str]] = []
    if os.path.isfile(MARKER_PATH):
        try:
            with open(MARKER_PATH, "r", encoding="utf-8") as fh:
                noted = fh.read().strip()
            if noted:
                marker.append(("marker_file", noted))
        except OSError:
            pass
    globs: List[Tuple[str, str]] = []
    home = os.path.expanduser("~")
    for pattern in (
        os.path.join(home, "my-quantitative"),
        os.path.join(os.path.dirname(home), "*", "my-quantitative"),
    ):
        for hit in sorted(glob.glob(pattern)):
            globs.append(("glob:" + pattern, hit))
    ordered: List[str] = []
    seen = set()
    for source, root in roots + marker + globs:
        root = os.path.abspath(root)
        if root not in seen:
            seen.add(root)
            ordered.append(root)
    return ordered


def find_runtime(env: Optional[Any] = None) -> RuntimePaths:
    """Resolve the live PROSPECTIVE-SHADOW-V1 runtime. Raises RuntimeError
    listing every attempt when nothing valid is found."""
    if env is None:
        env = os.environ
    attempts: List[str] = []

    direct = env.get("QUANT_SHADOW_RUNTIME_ROOT")
    if direct:
        root = os.path.abspath(direct)
        if _is_valid_runtime(root):
            return RuntimePaths(
                repo_root=None, worktree=None, runtime_root=root,
                source="env:QUANT_SHADOW_RUNTIME_ROOT",
            )
        attempts.append(f"env QUANT_SHADOW_RUNTIME_ROOT={root}: invalid")

    for root in _candidate_roots(env):
        resolved = _from_repo(root, "candidate")
        if resolved is not None:
            return resolved
        attempts.append(f"repo {root}: no valid {RUNTIME_SUBPATH} runtime")

    raise RuntimeError(
        "cannot find PROSPECTIVE-SHADOW-V1 runtime data; attempted:\n  "
        + "\n  ".join(attempts)
    )


def remember_runtime(paths: RuntimePaths) -> None:
    """Persist the resolved runtime root for the next launch (best effort)."""
    try:
        os.makedirs(APP_SUPPORT_DIR, exist_ok=True)
        with open(MARKER_PATH, "w", encoding="utf-8") as fh:
            fh.write(paths.runtime_root + "\n")
    except OSError:
        pass
