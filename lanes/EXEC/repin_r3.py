"""repin_r3.py — keep the ERRATUM_R3 executor pin in sync with the executor bytes.

Lane-internal helper (EXEC). After any edit of
research/control/NFL-WINPROB-NG-SCORED-V1/recorder/execute_post_go.py:
  1. sha256(executor) -> patch freeze_digests_r3.json executor_freeze.modules
  2. patch the ERRATUM_R3.md §2 table row with the same sha
  3. sha256(ERRATUM_R3.md) -> patch freeze_digests_r3.json erratum.sha256
Run again after any further edit. G2 (executor pin) refuses on any drift.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
EXECUTOR = WORKTREE / "research/control/NFL-WINPROB-NG-SCORED-V1/recorder/execute_post_go.py"
ERRATUM = WORKTREE / "lanes/FREEZE_ERRATUM_R3/ERRATUM_R3.md"
DIGESTS = WORKTREE / "lanes/FREEZE_ERRATUM_R3/freeze_digests_r3.json"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    exec_sha = sha256_file(EXECUTOR)
    doc = json.loads(DIGESTS.read_text(encoding="utf-8"))
    old_exec = doc["executor_freeze"]["modules"]["execute_post_go.py"]
    if old_exec != exec_sha:
        doc["executor_freeze"]["modules"]["execute_post_go.py"] = exec_sha
        print(f"executor pin: {old_exec[:12]}… -> {exec_sha[:12]}…")
    err_text = ERRATUM.read_text(encoding="utf-8")
    err_text2 = err_text.replace(old_exec, exec_sha)
    if err_text2 != err_text:
        print("ERRATUM_R3.md §2 table updated")
    ERRATUM.write_text(err_text2, encoding="utf-8")
    doc["erratum"]["sha256"] = sha256_file(ERRATUM)
    old_err = doc["erratum"]["sha256"]
    DIGESTS.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"erratum pin set: {old_err[:12]}…")
    if "--check" in sys.argv:
        assert json.loads(DIGESTS.read_text())["executor_freeze"]["modules"][
            "execute_post_go.py"] == sha256_file(EXECUTOR)
        print("pins consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
