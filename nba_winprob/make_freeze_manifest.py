"""Generate FREEZE_MANIFEST.json + seed TRIAL_LEDGER.jsonl for
NBA-WINPROB-SCORED-V1. Run once, after the code commit, before A7.

The manifest pins: code freeze sha (worktree HEAD at generation), the frozen
protocol file digest, plan digest (root control-plane commit), data file
hashes (outside git), the 9-arm table, the split, the seed, and the
post-freeze allowlist (control/results paths only — nba_winprob/ is hard-
immutable per check_launch_gates).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess

from .protocol import ARMS, LOGIT_L2, RNG_SEED, TEST_SEASONS
from .run_evaluation import REGISTERED_COMPARISONS, CYCLE_ID, GO_PHRASE

DATA_DIR = os.path.expanduser("~/.my-quantitative-data/nba-538-v1")
POST_FREEZE_ALLOWLIST = [
    "research/control/NBA-WINPROB-SCORED-V1/**",
    "results/**",
]


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--control-dir", required=True)
    args = ap.parse_args()

    wt = args.worktree
    ctrl = args.control_dir
    os.makedirs(ctrl, exist_ok=True)

    manifest = {
        "schema": "nba_winprob_scored_freeze@1",
        "cycle_id": CYCLE_ID,
        "created_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "code_freeze_sha": _git(["rev-parse", "HEAD"], wt),
        "protocol_path": "lanes/C_protocol/PROTOCOL_EVAL.md",
        "protocol_digest": _sha256_file(os.path.join(wt, "lanes/C_protocol/PROTOCOL_EVAL.md")),
        "predecessor_tip": "b5b5084753d213dfd793488d3c009cf4380e0323",
        "data": {
            name: {"path": path, "sha256": _sha256_file(path)}
            for name, path in {
                "raw_nbaallelo": os.path.join(DATA_DIR, "raw/nbaallelo.csv"),
                "games": os.path.join(DATA_DIR, "derived/games.csv"),
                "lineages": os.path.join(DATA_DIR, "derived/lineages.csv"),
                "participants": os.path.join(DATA_DIR, "derived/participants.csv"),
                "features": os.path.join(DATA_DIR, "derived/features.csv"),
            }.items()
        },
        "attribution": {
            "path": os.path.join(DATA_DIR, "raw/ATTRIBUTION.md"),
            "sha256": _sha256_file(os.path.join(DATA_DIR, "raw/ATTRIBUTION.md")),
            "license": "CC BY 4.0 (FiveThirtyEight data repo)",
            "usage": "internal research only; BRef provenance disclosed; owner conditional acceptance 2026-10-04",
        },
        "arms": [{"arm_id": a.arm_id, "kind": a.kind, "K": a.K, "HCA": a.HCA,
                  "features": list(a.features)} for a in ARMS],
        "test_seasons": list(TEST_SEASONS),
        "train_seasons_range": [1947, 2008],
        "constants": {"logit_l2": LOGIT_L2, "rng_seed": RNG_SEED,
                      "elo_init": 1500.0, "elo_gamma": 0.75},
        "registered_comparisons": [list(c) for c in REGISTERED_COMPARISONS],
        "go_phrase": GO_PHRASE,
        "go_phrase_state": "REGISTERED_NOT_CONSUMED",
        "post_freeze_allowlist": POST_FREEZE_ALLOWLIST,
        "drift_law": "nba_winprob/ is immutable from code_freeze_sha; only allowlisted control/results paths may change after freeze",
    }
    mpath = os.path.join(ctrl, "FREEZE_MANIFEST.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)

    ledger = os.path.join(ctrl, "TRIAL_LEDGER.jsonl")
    if not os.path.exists(ledger):
        with open(ledger, "w", encoding="utf-8") as f:
            for a in ARMS:
                f.write(json.dumps({
                    "schema": "nba_winprob_trial_ledger@1", "cycle_id": CYCLE_ID,
                    "arm_id": a.arm_id, "status": "PREREGISTERED", "observed": False,
                    "class": "PRIMARY", "registered_at_utc": manifest["created_utc"],
                    "spec": {"K": a.K, "HCA": a.HCA, "features": list(a.features)},
                }) + "\n")

    print(json.dumps({"manifest": mpath, "code_freeze_sha": manifest["code_freeze_sha"],
                      "ledger_seeded": os.path.exists(ledger), "arms": len(manifest["arms"])}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
