"""A7 L1a — independent 20-file sha sample of the EURUSD M1 corpus.

Reads the READ-ONLY diag lane corpus bytes and verifies the sampled files
against the manifest COMMITTED IN THE A7 WORKTREE (the authority chain's
pinned manifest). Sample law: seed 20260926, 20 files, random.Random.
Light job (20 small files) — no heavy lock needed.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

A7_WORK = Path(__file__).resolve().parent.parent
COHORT = A7_WORK.parent
CORPUS = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
              "erp1-tracka-cohort-1/diag-daemon/research/control/"
              "ERP1-TRACKA-COHORT-1/diag/data_local/EURUSD")
MANIFEST = COHORT / "diag" / "data_local" / "EURUSD" / "m1_manifest.json"
OUT = A7_WORK / "layer_results" / "a7_m1_sample_sha.json"


def main() -> int:
    man = json.loads(MANIFEST.read_text())
    on_disk = sorted(
        f"{side}/{f.name}"
        for side in ("BID", "ASK")
        for f in (CORPUS / side).glob("*.bi5"))
    rng = random.Random(20260926)
    sample = sorted(rng.sample(on_disk, 20))
    rows = []
    mism = []
    for rel in sample:
        raw = (CORPUS / rel).read_bytes()
        got = hashlib.sha256(raw).hexdigest()
        exp = man["files"].get(f"M1/{rel}", {}).get("sha256")
        ok = exp == got
        rows.append({"file": rel, "bytes": len(raw), "sha256_ok": ok})
        if not ok:
            mism.append(rel)
    res = {
        "schema": "a7_m1_sample_sha@1",
        "labels": ["A7_INDEPENDENT_REPRODUCTION",
                   "FAILURE_ROOT_CAUSE_RESEARCH",
                   "DIAGNOSTIC_OUTCOME_EXPOSED"],
        "manifest": str(MANIFEST),
        "corpus_readonly": str(CORPUS),
        "files_on_disk": len(on_disk),
        "manifest_entries": len(man["files"]),
        "sample": {"n": 20, "seed": 20260926},
        "ok": sum(1 for r in rows if r["sha256_ok"]),
        "mismatches": mism,
        "files": rows,
        "verdict": "PASS" if not mism else "FAIL",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in
                      ("files_on_disk", "manifest_entries", "ok",
                       "mismatches", "verdict")}))
    return 0 if not mism else 1


if __name__ == "__main__":
    sys.exit(main())
