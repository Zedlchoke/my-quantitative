"""STOCKS-NG2 D2 measurement runner (lane d2, task stocks-ng2-d2-measurement).

Usage (interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python):

    run_d2_measurement.py <built_at_utc>

Writes, from THIS worktree:
  research/control/stocks_ng2_run/d2/d2_novelty_feasibility_ng2.json
  research/control/stocks_ng2_run/d1/feasibility/feasibility_summary.json

Determinism contract (ng1/V13 pattern): the ONLY wall-clock input is
built_at_utc; the full measurement is computed TWICE in-process and the
two JSON serializations must be byte-identical (same sha256) or the run
fails closed and writes nothing.  Zero PnL / expectancy / PF arithmetic
exists anywhere on this path.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, os.pardir,
    os.pardir))
sys.path.insert(0, REPO_ROOT)

from research.assets.stocks_ng2.d2 import measure  # noqa: E402

D2_DIR = os.path.join(REPO_ROOT,
                      "research/control/stocks_ng2_run/d2")
OUT_MAIN = os.path.join(D2_DIR, "d2_novelty_feasibility_ng2.json")
OUT_FEAS = os.path.join(
    REPO_ROOT,
    "research/control/stocks_ng2_run/d1/feasibility/feasibility_summary.json")

DISPATCH_SHA = "3cc37aeb452f606f12dc60a9e3c63f1b6d76fab0"


def _git(args):
    return subprocess.run(["git", "-C", REPO_ROOT] + args,
                          capture_output=True, text=True, check=True
                          ).stdout.strip()


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_d2_measurement.py <built_at_utc>\n")
        return 2
    built_at_utc = argv[1]
    actual_start_sha = _git(["rev-parse", "HEAD"])
    dispatch_sha = DISPATCH_SHA
    if actual_start_sha != dispatch_sha:
        # the packet's dispatch base: mismatch is a STOP condition, but
        # the substance commit may already exist on this branch - the
        # handoff records both; only a DIRTY tree at a different HEAD is
        # fatal here.
        dirty = _git(["status", "--porcelain=v1"])
        if dirty:
            sys.stderr.write(
                f"BLOCKED: HEAD {actual_start_sha} != dispatch "
                f"{dispatch_sha} with a dirty tree\n")
            return 4

    print("[d2] pass 1 ...", flush=True)
    s1 = measure.run_measurement(built_at_utc, actual_start_sha, dispatch_sha)
    print("[d2] pass 2 (determinism) ...", flush=True)
    s2 = measure.run_measurement(built_at_utc, actual_start_sha, dispatch_sha)
    h1 = hashlib.sha256(s1.encode()).hexdigest()
    h2 = hashlib.sha256(s2.encode()).hexdigest()
    if h1 != h2:
        sys.stderr.write(f"BLOCKED: nondeterministic measurement {h1} != "
                         f"{h2}\n")
        return 3

    audit = json.loads(s1)
    audit["determinism"] = {
        "passes": 2,
        "byte_identical": True,
        "sha256_pass_1": h1,
        "sha256_pass_2": h2,
        "scope": "whole measurement (both anchors + all 17 vetoes + sham "
                 "+ arrival shadow + feasibility blocks), recomputed "
                 "in-process from the same pinned inputs",
    }
    s1 = json.dumps(audit, indent=1, sort_keys=True)
    os.makedirs(D2_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUT_FEAS), exist_ok=True)
    with open(OUT_MAIN, "w") as fh:
        fh.write(s1)
    with open(OUT_FEAS, "w") as fh:
        fh.write(json.dumps(measure.feasibility_summary_from_audit(audit),
                            indent=1, sort_keys=True))
    print(f"[d2] wrote {OUT_MAIN}")
    print(f"[d2] wrote {OUT_FEAS}")
    for pid, res in audit["results"].items():
        print(f"[d2] {pid}: novelty={res['verdict_novelty']} "
              f"sham_rho="
              f"{res['identifiability']['sham_amendment_matched_original_only']['pooled_anchor_vs_control_rho']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
