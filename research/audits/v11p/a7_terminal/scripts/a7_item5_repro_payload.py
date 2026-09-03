"""A7-TERMINAL item 5: independent reproduction payload-hash verification.

My own payload hash: sha256 over canonical JSON (sorted keys, compact
separators) of the scored artifact with the 'hashes' and 'artifacts' keys
removed and each tree's own absolute root path normalised to <TREE_ROOT>
(frozen rule per PLAN 15 / compare_repro.py).  Computed independently for
every LOT LOT-RESMAX-7D-W cell (exceeds the 2-cell minimum) from BOTH trees.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXEC = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\exec-v11-1")
REPRO = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\repro-v11-1")
BASE = "results/v11_phase_e/LOT/LOT-RESMAX-7D-W/matrix"
CELLS = ["baseline", "fee_slippage_x1_5", "plus_2_ticks", "plus_1_event_delay", "drop_one_symbol"]


def norm(value, root: Path):
    if isinstance(value, str):
        return (value.replace(str(root), "<TREE_ROOT>")
                     .replace(str(root).replace("\\", "/"), "<TREE_ROOT>"))
    if isinstance(value, list):
        return [norm(v, root) for v in value]
    if isinstance(value, dict):
        return {k: norm(v, root) for k, v in value.items()}
    return value


def my_payload_sha(art: dict, root: Path) -> str:
    payload = {k: v for k, v in art.items() if k not in ("hashes", "artifacts")}
    text = json.dumps(norm(payload, root), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    out = {"schema": "a7_terminal_item5_repro_payload_v1", "arm": "LOT-RESMAX-7D-W", "cells": {}}
    all_ok = True
    for cell in CELLS:
        a = json.loads((EXEC / BASE / cell / "results" / "artifact.json").read_text(encoding="utf-8"))
        r = json.loads((REPRO / BASE / cell / "results" / "artifact.json").read_text(encoding="utf-8"))
        ha = my_payload_sha(a, EXEC)
        hr = my_payload_sha(r, REPRO)
        claimed_a = a["hashes"]["result_sha256"]
        claimed_r = r["hashes"]["result_sha256"]
        rec = {
            "a7_payload_sha_exec": ha,
            "a7_payload_sha_repro": hr,
            "a7_payload_equal": ha == hr,
            "claimed_result_sha256_exec": claimed_a,
            "claimed_result_sha256_repro": claimed_r,
            "claimed_equal": claimed_a == claimed_r,
            "claimed_matches_report": claimed_a == claimed_r,
        }
        out["cells"][cell] = rec
        all_ok = all_ok and rec["a7_payload_equal"] and rec["claimed_equal"]
    out["all_match"] = all_ok
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
