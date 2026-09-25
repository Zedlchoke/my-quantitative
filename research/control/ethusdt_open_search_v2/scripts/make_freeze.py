"""EOSV2 P3 freeze builder — identity freeze BEFORE any PnL.

Hashes: engine, runner, stager, fixtures; staged manifest, census,
feasibility, dry-run; records the frozen arm ladder, gates verbatim,
controls law, seeds law, verdict enum and the measured tree HEAD.
Output: freezes/eosv2_freeze.json (committed; this IS the freeze).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FREEZES = ROOT / "freezes"

GATES_VERBATIM = {
    "G1": "net > 0 @1.0x",
    "G2": "net > 0 @1.5x",
    "G3": "net @1.0x beats BASE_ALWAYS_ON_LONG, BASE_TREND_LF, REF_SHORT_ALWAYS (strictly each)",
    "G4": ">=3/4 folds net>0 OR best-fold-removed net>0",
    "G5": "max positive-fold share <= 0.50",
    "G6": "block-shuffled info control AND sign-inverted control must NOT out-earn the cell @1.0x",
    "G7": "fills @1.5x <= 10000 AND measured cost/round-trip <= 10 bps",
    "G8": "reproduction byte-match (detached twin at code-freeze SHA)",
    "G9": "A7 terminal clean (0 unresolved HIGH/CRITICAL)",
    "G10": "vs BASE_TREND_LF: combined net increases AND no fold flips positive->negative",
    "G11": "ancestry disclosure (spearman vs TREND_LF weights, disclosure-only)",
}


def sha_file(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def arm_digest(spec: dict) -> str:
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def main() -> int:
    import eosv2_engine as E
    worktree = ROOT.parents[2]
    head = subprocess.run(["git", "-C", str(worktree), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(worktree), "status", "--porcelain=v1"],
                           capture_output=True, text=True, check=True).stdout.strip()
    arms = {}
    for arm, (lane, desc) in E.ARMS.items():
        spec = {"cycle": "ETHUSDT-OPEN-SEARCH-V2", "family": arm, "lane": lane,
                "description": desc,
                "grid": "H4 UTC", "states": "{0,1} long/flat",
                "cost_law": {"fee_bps_side": 5.0, "adverse_tick": 0.01,
                             "funding": "measured per settlement",
                             "tiers": [1.0, 1.5, 2.0], "tier_scales": ["fee", "tick"]},
                "notional": 100000.0,
                "folds": [list(f) for f in E.FOLDS],
                "control_law": {"block_shuffle_bars": E.BLOCK_SHUFFLE_BARS,
                                "seed": f"eosv2|{arm}|shuffle",
                                "sign_inversion": True}}
        arms[arm] = {"spec": spec, "arm_config_digest": arm_digest(spec)}

    out = {
        "schema": "eosv2.freeze@1",
        "frozen_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cycle_id": "ETHUSDT-OPEN-SEARCH-V2",
        "code_freeze": {
            "eosv2_engine.py": sha_file(SCRIPTS / "eosv2_engine.py"),
            "run_scored.py": sha_file(SCRIPTS / "run_scored.py"),
            "stage_all.py": sha_file(SCRIPTS / "stage_all.py"),
            "test_fixtures.py": sha_file(ROOT / "tests_py" / "test_fixtures.py"),
        },
        "evidence_freeze": {
            "staged_manifest.json": sha_file(FREEZES / "staged_manifest.json"),
            "census.json": sha_file(FREEZES / "census.json"),
            "feasibility.json": sha_file(FREEZES / "feasibility.json"),
            "dry_run.json": sha_file(FREEZES / "dry_run.json"),
        },
        "arms": arms,
        "references": ["BASE_CASH", "BASE_ALWAYS_ON_LONG", "BASE_TREND_LF", "REF_SHORT_ALWAYS"],
        "gates_verbatim": GATES_VERBATIM,
        "budget": {"cells_max": 8, "tiers": [1.0, 1.5, 2.0], "funding_law": "MEASURED"},
        "verdict_enum": [
            "ETHUSDT_OPEN_SEARCH_V2_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION",
            "ETHUSDT_OPEN_SEARCH_V2_NO_INCREMENTAL_VALUE",
            "ETHUSDT_OPEN_SEARCH_V2_NO_ELIGIBLE_PROPOSAL",
            "ETHUSDT_OPEN_SEARCH_V2_BLOCKED_DATA_OR_SELECTION",
            "TECHABORT"],
        "go_phrase": "GO ETHUSDT OPEN SEARCH V2 SCORED EXECUTION",
        "tree": {"head": head, "dirty_paths": [l[3:] for l in dirty.splitlines()] or "clean-at-commit"},
        "posthoc_disclosure": ("all windows outcome-observed (cross-sectional ETH exposure + "
                               "price-history knowledge); survivor ceiling = prospective validation"),
    }
    dest = FREEZES / "eosv2_freeze.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"freeze -> {dest}")
    print(json.dumps({"code_freeze": out["code_freeze"],
                      "arms": {a: v["arm_config_digest"][:16] for a, v in arms.items()}},
                     indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
