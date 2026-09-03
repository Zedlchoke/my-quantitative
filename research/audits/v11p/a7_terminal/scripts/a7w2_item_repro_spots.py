"""A7-TERMINAL wave 2: reproduction payload-hash spot checks.

A7's own payload sha256 (artifact minus hashes/artifacts keys, frozen
<TREE_ROOT> normalisation, canonical JSON) computed from BOTH trees for:
  - LOT-RESSKEW-30D-W: baseline, drop_one_symbol  (2 cells)
  - ILLIQ-AMIHUD-56D-W: baseline, plus_2_ticks, drop_one_fold  (3 cells)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXEC = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\exec-v11-1")
REPRO = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\repro-v11-1")
TARGETS = [
    ("LOT", "LOT-RESSKEW-30D-W", "baseline"),
    ("LOT", "LOT-RESSKEW-30D-W", "drop_one_symbol"),
    ("ILLIQ", "ILLIQ-AMIHUD-56D-W", "baseline"),
    ("ILLIQ", "ILLIQ-AMIHUD-56D-W", "plus_2_ticks"),
    ("ILLIQ", "ILLIQ-AMIHUD-56D-W", "drop_one_fold"),
]


def norm(value, root):
    if isinstance(value, str):
        return (value.replace(str(root), "<TREE_ROOT>")
                     .replace(str(root).replace("\\", "/"), "<TREE_ROOT>"))
    if isinstance(value, list):
        return [norm(v, root) for v in value]
    if isinstance(value, dict):
        return {k: norm(v, root) for k, v in value.items()}
    return value


def payload_sha(art, root):
    payload = {k: v for k, v in art.items() if k not in ("hashes", "artifacts")}
    return hashlib.sha256(
        json.dumps(norm(payload, root), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def main():
    out = {"schema": "a7_terminal_wave2_repro_spots_v1", "cells": {}}
    all_ok = True
    for fam, arm, cell in TARGETS:
        rel = f"results/v11_phase_e/{fam}/{arm}/matrix/{cell}/results/artifact.json"
        a = json.loads((EXEC / rel).read_text(encoding="utf-8"))
        r = json.loads((REPRO / rel).read_text(encoding="utf-8"))
        ha, hr = payload_sha(a, EXEC), payload_sha(r, REPRO)
        ca, cr = a["hashes"]["result_sha256"], r["hashes"]["result_sha256"]
        rec = {
            "family": fam, "arm": arm, "cell": cell,
            "a7_payload_sha_exec": ha, "a7_payload_sha_repro": hr,
            "a7_payload_equal": ha == hr,
            "claimed_result_sha256_exec": ca, "claimed_result_sha256_repro": cr,
            "claimed_equal": ca == cr,
        }
        out["cells"][f"{fam}/{arm}/{cell}"] = rec
        all_ok = all_ok and rec["a7_payload_equal"] and rec["claimed_equal"]
    out["all_match"] = all_ok
    out["n_cells"] = len(TARGETS)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
