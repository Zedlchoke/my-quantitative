"""FREEZE v1 generator + ledger seed for NFL-WINPROB-SCORED-V1 (schema @1,
parity with NBA freeze v2 fields)."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess

from .protocol import ARMS, LOGIT_L2, RNG_SEED, TEST_SEASONS
from .run_evaluation import REGISTERED_COMPARISONS, CYCLE_ID, GO_PHRASE

DATA_DIR = os.path.expanduser("~/.my-quantitative-data/nfl-nflverse-v1")
POST_FREEZE_ALLOWLIST = ["research/control/NFL-WINPROB-SCORED-V1/**", "results/**"]


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
    games_path = os.path.join(DATA_DIR, "derived/games_nfl.csv")
    features_path = os.path.join(DATA_DIR, "derived/features_nfl.csv")
    manifest = {
        "schema": "nfl_winprob_scored_freeze@1",
        "cycle_id": CYCLE_ID,
        "created_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "code_freeze_sha": _git(["rev-parse", "HEAD"], wt),
        "supersedes": {"code_freeze_sha": "8cd0e1bcf9c9d45f5e10ae1b73b93eee7560a7b7",
                       "reason": "AMENDMENT_1 round 4: ledger-schema + drift-prefix fixes (co-owner audit); 0 outcomes ever computed",
                       "old_manifest": "research/control/NFL-WINPROB-SCORED-V1/FREEZE_MANIFEST.SUPERSEDED_BLOCKED.json"},
        "predecessor_tip": "9639706ffe631b5a2b77df1830ae6c7df13c0ea1",
        "pinned_games": games_path,
        "pinned_features": features_path,
        "ledger_path": os.path.join(ctrl, "TRIAL_LEDGER.jsonl"),
        "results_dir": os.path.join(ctrl, "results"),
        "a7_report_path": os.path.join(ctrl, "audits/AUDIT_PRELAUNCH.md"),
        "protocol_path": "lanes/NFL_C_protocol/PROTOCOL_EVAL_NFL.md",
        "protocol_digest": _sha256_file(os.path.join(wt, "lanes/NFL_C_protocol/PROTOCOL_EVAL_NFL.md")),
        "data": {
            name: {"path": path, "sha256": _sha256_file(path)}
            for name, path in {
                "raw_games": os.path.join(DATA_DIR, "raw/games.csv"),
                "games": games_path,
                "lineages": os.path.join(DATA_DIR, "derived/lineages_nfl.csv"),
                "features": features_path,
            }.items()
        },
        "attribution": {
            "path": os.path.join(DATA_DIR, "raw/ATTRIBUTION.md"),
            "sha256": _sha256_file(os.path.join(DATA_DIR, "raw/ATTRIBUTION.md")),
            "license": "CC BY 4.0 (nflverse/nflverse-data releases)",
            "usage": "internal research only; owner conditional authorization 2026-10-04",
        },
        "arms": [{"arm_id": a.arm_id, "kind": a.kind, "K": a.K, "HCA": a.HCA,
                  "features": list(a.features)} for a in ARMS],
        "test_seasons": list(TEST_SEASONS),
        "train_seasons_range": [2000, 2018],
        "constants": {"logit_l2": LOGIT_L2, "rng_seed": RNG_SEED,
                      "elo_init": 1500.0, "elo_gamma": 2.0 / 3.0,
                      "f1_stream": "B1-a (K=20, HCA=0)"},
        "registered_comparisons": [list(c) for c in REGISTERED_COMPARISONS],
        "go_phrase": GO_PHRASE,
        "go_phrase_state": "REGISTERED_NOT_CONSUMED",
        "post_freeze_allowlist": POST_FREEZE_ALLOWLIST,
        "drift_law": "nfl_winprob/ immutable from code_freeze_sha; allowlisted control/results only; pinned inputs; A7 report + structured owner GO + FREE lock + clean tree at launch",
    }
    with open(os.path.join(ctrl, "FREEZE_MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    ledger = os.path.join(ctrl, "TRIAL_LEDGER.jsonl")
    if not os.path.exists(ledger):
        with open(ledger, "w", encoding="utf-8") as f:
            for a in ARMS:
                f.write(json.dumps({"schema": "nfl_winprob_trial_ledger@1", "cycle_id": CYCLE_ID,
                                    "arm_id": a.arm_id, "status": "PREREGISTERED", "observed": False,
                                    "class": "PRIMARY", "registered_at_utc": manifest["created_utc"],
                                    "spec": {"K": a.K, "HCA": a.HCA, "features": list(a.features)}}) + "\n")
    print(json.dumps({"code_freeze_sha": manifest["code_freeze_sha"],
                      "features_sha": manifest["data"]["features"]["sha256"][:16]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
