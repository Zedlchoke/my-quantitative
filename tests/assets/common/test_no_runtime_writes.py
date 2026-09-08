"""The suite writes only to tmp_path: imports must leave the tree untouched.

Companion check for the M0 acceptance rule "running the suite leaves
``git status --porcelain=v1`` unchanged": importing every module of the
asset-neutral core in a fresh interpreter must not create or modify any
tracked/untracked file in the worktree (bytecode caches are gitignored).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

_MODULES = (
    "research.assets.common",
    "research.assets.common.calendar",
    "research.assets.common.carrying_cost",
    "research.assets.common.contracts",
    "research.assets.common.crypto_compat",
    "research.assets.common.execution_cost",
    "research.assets.common.instrument",
    "research.assets.common.ledger_policy",
    "research.assets.common.trial_identity",
)


def _git_status() -> str:
    out = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout


def test_importing_common_core_writes_nothing_to_the_worktree():
    before = _git_status()
    probe = "import importlib\n"
    probe += "".join(f"importlib.import_module({name!r})\n" for name in _MODULES)
    probe += "print('imported-ok')\n"
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "imported-ok" in completed.stdout
    assert _git_status() == before
