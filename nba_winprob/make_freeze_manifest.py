"""Generate FREEZE_MANIFEST v2 + seed TRIAL_LEDGER for NBA-WINPROB-SCORED-V1.

v2 per AMENDMENT_1: schema nba_winprob_scored_freeze@2 adds pinned_games /
pinned_features / ledger_path / results_dir / a7_report_path / supersedes;
the runner's launch gates enforce all of them.
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
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          check=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--control-dir", required=True)
    args = ap.parse_args()
    wt, ctrl = args.worktree, args.control_dir
    os.makedirs(ctrl, exist_ok=True)
    games_path = os.path.join(DATA_DIR, "derived/games.csv")
    features_path = os.path.join(DATA_DIR, "derived/features.csv")

    manifest = {
        "schema": "nba_winprob_scored_freeze@2",
        "cycle_id": CYCLE_ID,
        "created_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "code_freeze_sha": _git(["rev-parse", "HEAD"], wt),
        "supersedes": {"code_freeze_sha": "2c64b6f34b0b2cf46db7243418f5b929a6a5b4c8",
                       "reason": "freeze v3: v2 pinned a sha that predated its own generator commit (A7r2 CRITICAL C1) + M1/M2 verdict-verbatim fixes + L1-L3 gate hardening (A7r2); 0 outcomes ever computed",
                       "older_freeze": "39b11156 (SUPERSEDED_BLOCKED, AMENDMENT_1)",
                       "old_manifest": "research/control/NBA-WINPROB-SCORED-V1/FREEZE_MANIFEST.SUPERSEDED_BLOCKED.json"},
        "pinned_games": games_path,
        "pinned_features": features_path,
        "ledger_path": os.path.join(ctrl, "TRIAL_LEDGER.jsonl"),
        "results_dir": os.path.join(ctrl, "results"),
        "a7_report_path": os.path.join(ctrl, "audits/AUDIT_PRELAUNCH_ROUND2.md"),
        "protocol_path": "lanes/C_protocol/PROTOCOL_EVAL.md",
        "protocol_digest": _sha256_file(os.path.join(wt, "lanes/C_protocol/PROTOCOL_EVAL.md")),
        "amendment_path": "research/control/NBA-WINPROB-SCORED-V1/AMENDMENT_1.md",
        "amendment_digest": _sha256_file(os.path.join(ctrl, "AMENDMENT_1.md")),
        "predecessor_tip": "b5b5084753d213dfd793488d3c009cf4380e0323",
        "data": {
            name: {"path": path, "sha256": _sha256_file(path)}
            for name, path in {
                "raw_nbaallelo": os.path.join(DATA_DIR, "raw/nbaallelo.csv"),
                "games": games_path,
                "lineages": os.path.join(DATA_DIR, "derived/lineages.csv"),
                "participants": os.path.join(DATA_DIR, "derived/participants.csv"),
                "features": features_path,
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
                      "elo_init": 1500.0, "elo_gamma": 0.75,
                      "f1_stream": "B1-a (K=16, HCA=0) — AMENDMENT_1 A1"},
        "registered_comparisons": [list(c) for c in REGISTERED_COMPARISONS],
        "go_phrase": GO_PHRASE,
        "go_phrase_state": "REGISTERED_NOT_CONSUMED",
        "post_freeze_allowlist": POST_FREEZE_ALLOWLIST,
        "drift_law": "nba_winprob/ immutable from code_freeze_sha; only allowlisted control/results paths may change; inputs must equal pinned paths; A7 report + structured owner GO record + FREE lock + clean tree required at launch",
    }
    with open(os.path.join(ctrl, "FREEZE_MANIFEST.json"), "w", encoding="utf-8") as f:
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
    print(json.dumps({"code_freeze_sha": manifest["code_freeze_sha"],
                      "features_sha": manifest["data"]["features"]["sha256"][:16],
                      "comparisons": len(manifest["registered_comparisons"])}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
