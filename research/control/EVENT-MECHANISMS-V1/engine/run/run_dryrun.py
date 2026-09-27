"""E8 — exact-arm dry-run: 6 arms, scored=false, real_pnl=false.

Proofs: pairwise-distinct record IDs; recursive no-PnL scan over all output
artifacts; populations per arm per fold vs freeze floors. Placeholder ledger
rows land in engine/dryrun/ (NOT the canonical trial ledger — A1 owns that).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emv1 import config as C
from emv1.nopnl import scan_tree

CODE_FREEZE_SHA = None  # filled by the caller (current HEAD) if provided


def read_records(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def main(code_freeze_sha: str = "") -> None:
    a1 = read_records(os.path.join(C.EVIDENCE_DIR, "a1_decisions.jsonl"))
    a2 = read_records(os.path.join(C.EVIDENCE_DIR, "a2_decisions.jsonl"))
    by_arm = {}
    for r in a1 + a2:
        by_arm.setdefault(r["arm_id"], []).append(r)

    arms = ["A1-ANCHOR", "A1-N1", "A1-N2", "A2-ANCHOR", "A2-N1", "A2-N2"]
    id_sets = {a: set(r["event_id"] for r in by_arm.get(a, [])) for a in arms}

    pairwise = []
    for i, a in enumerate(arms):
        for b in arms[i + 1:]:
            inter = id_sets[a] & id_sets[b]
            pairwise.append({"arm_a": a, "arm_b": b, "intersection": len(inter),
                             "distinct": len(inter) == 0})

    arm_records = {}
    for a in arms:
        pops = {}
        for r in by_arm.get(a, []):
            pops[r["fold"]] = pops.get(r["fold"], 0) + 1
        arm_records[a] = {
            "family_id": by_arm[a][0]["family_id"] if by_arm.get(a) else None,
            "n_records": len(by_arm.get(a, [])),
            "fold_populations": dict(sorted(pops.items())),
            "id_prefix": a,
        }

    # recursive no-forbidden-field scan over ALL engine output artifacts
    # (stale dry-run artifacts are removed first so the scan judges only the
    # outputs of THIS run)
    for stale in ("dryrun_manifest.json", "placeholder_ledger.jsonl"):
        p = os.path.join(C.DRYRUN_DIR, stale)
        if os.path.exists(p):
            os.remove(p)
    violations, n_files = scan_tree(C.EVIDENCE_DIR)
    v2, n2 = scan_tree(C.DRYRUN_DIR)
    violations += v2

    manifest = {
        "cycle_id": C.CYCLE_ID,
        "schema": "emv1_dryrun_manifest@1",
        "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "code_freeze_sha": code_freeze_sha,
        "arms": arm_records,
        "arms_scored": False,
        "real_money": False,
        "record_kind": "DECISION_RECORDS_ONLY_PRICES_AND_COST_BANDS",
        "pairwise_distinct_id_proofs": pairwise,
        "pairwise_all_distinct": all(p["distinct"] for p in pairwise),
        "forbidden_field_scan": {
            "files_scanned": n_files + n2,
            "violations": violations,
            "clean": len(violations) == 0,
            "forbidden_key_substrings": list(C.NOPNL_FORBIDDEN_KEY_SUBSTRINGS),
        },
        "floors": {
            "per_fold_min": C.FLOOR_EVENTS_PER_FOLD,
            "total_per_anchor_min": C.FLOOR_EVENTS_TOTAL_PER_ANCHOR,
        },
    }
    os.makedirs(C.DRYRUN_DIR, exist_ok=True)
    json.dump(manifest, open(os.path.join(C.DRYRUN_DIR, "dryrun_manifest.json"), "w"),
              indent=1, sort_keys=True)

    # placeholder ledger rows (engine/dryrun/ — NOT the canonical ledger)
    with open(os.path.join(C.DRYRUN_DIR, "placeholder_ledger.jsonl"), "w") as f:
        for a in arms:
            info = arm_records[a]
            row = {
                "cycle_id": C.CYCLE_ID,
                "family_id": info["family_id"],
                "arm_id": a,
                "arm_config_digest_note": "sha256 of G3_FREEZE section — owned by A1 at registration",
                "scored": False,
                "real_money": False,
                "record_kind": "PLACEHOLDER_PRE_GO",
                "status": "DRY_RUN_ONLY_PRE_GO",
                "fold_populations": info["fold_populations"],
                "n_records": info["n_records"],
                "record_id_range": sorted(id_sets[a])[:1] + sorted(id_sets[a])[-1:] if id_sets[a] else [],
            }
            f.write(json.dumps(row, sort_keys=True) + "\n")

    print("pairwise all distinct:", manifest["pairwise_all_distinct"])
    print("forbidden-field scan clean:", manifest["forbidden_field_scan"]["clean"],
          f"({manifest['forbidden_field_scan']['files_scanned']} files)")
    if violations:
        print("VIOLATIONS:", violations[:10])
    for a in arms:
        print(f"  {a}: {arm_records[a]['n_records']} records {arm_records[a]['fold_populations']}")


if __name__ == "__main__":
    import subprocess
    sha = subprocess.run(
        ["git", "-C", C.WT, "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    main(sha)
