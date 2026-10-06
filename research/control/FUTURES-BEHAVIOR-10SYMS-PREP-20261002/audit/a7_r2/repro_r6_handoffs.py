"""A7-R2 independent check of co-owner finding R6 (handoff canonicity).

Checks BOTH the archived originals (dispatch/archive_attempt1/, which the
lane claims are byte-identical to eae8c3d2's committed handoff_*.json)
and the current replacements against the zcode_orch_v3_handoff@1 schema
as required by plugins/quant-research-orchestrator/skills/structured-
handoff/SKILL.md:

  required: task_id, cycle_id, role, lane, dispatch_sha, actual_start_sha
  (both 40-hex and EQUAL), commit_sha, changed_paths[], tests[] each with
  {command, exit_code, verdict PASS|FAIL|NOT_RUN, log_digest},
  authority_claims[], known_limitations[], incidents[], tree_status,
  workers, outputs[] each {path, sha256}, recommended_next_action.

Usage:
  python repro_r6_handoffs.py <worktree-root> base     # originals @eae8c3d2
  python repro_r6_handoffs.py <worktree-root> current  # replacements
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

WT = Path(sys.argv[1])
MODE = sys.argv[2] if len(sys.argv) > 2 else "base"
TASK = "research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002"

REQUIRED_TOP = [
    "schema", "task_id", "cycle_id", "role", "lane",
    "dispatch_sha", "actual_start_sha", "commit_sha", "changed_paths",
    "tests", "authority_claims", "known_limitations", "incidents",
    "tree_status", "workers", "outputs", "recommended_next_action",
]
TEST_KEYS = {"command", "exit_code", "verdict", "log_digest"}
VERDICTS = {"PASS", "FAIL", "NOT_RUN"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def load_originals():
    """Read handoff_*.json content straight from commit eae8c3d2."""
    names = subprocess.run(
        ["git", "-C", str(WT), "ls-tree", "--name-only",
         "eae8c3d2:" + TASK + "/dispatch"],
        capture_output=True, text=True, check=True).stdout.split()
    out = {}
    for n in names:
        if n.startswith("handoff_") and n.endswith(".json"):
            blob = subprocess.run(
                ["git", "-C", str(WT), "show",
                 f"eae8c3d2:{TASK}/dispatch/{n}"],
                capture_output=True, text=True, check=True).stdout
            out[n] = blob
    return out


def load_current():
    d = WT / TASK / "dispatch"
    return {p.name: p.read_text()
            for p in sorted(d.glob("handoff_*.json"))}


def check(name, text):
    problems = []
    try:
        d = json.loads(text)
    except Exception as e:
        return {"file": name, "json_error": str(e), "problems": ["bad json"]}
    missing = [k for k in REQUIRED_TOP if k not in d]
    if missing:
        problems.append(f"missing keys: {missing}")
    if d.get("schema") != "zcode_orch_v3_handoff@1":
        problems.append(f"schema != zcode_orch_v3_handoff@1 ({d.get('schema')!r})")
    ds, ax = d.get("dispatch_sha"), d.get("actual_start_sha")
    for k, v in (("dispatch_sha", ds), ("actual_start_sha", ax)):
        if not (isinstance(v, str) and HEX40.match(v)):
            problems.append(f"{k} not 40-hex: {v!r}")
    if isinstance(ds, str) and isinstance(ax, str) and ds != ax:
        problems.append("dispatch_sha != actual_start_sha (REFUSED per skill)")
    if d.get("commit_sha") is None:
        problems.append("commit_sha null")
    elif not (isinstance(d.get("commit_sha"), str)
              and HEX40.match(d["commit_sha"])):
        problems.append(f"commit_sha not 40-hex: {d.get('commit_sha')!r}")
    t = d.get("tests")
    if not isinstance(t, list) or not t:
        problems.append("tests missing/empty")
    else:
        for i, e in enumerate(t):
            miss = TEST_KEYS - set(e)
            if miss:
                problems.append(f"tests[{i}] missing {sorted(miss)}")
            if e.get("verdict") not in VERDICTS:
                problems.append(
                    f"tests[{i}] verdict not PASS/FAIL/NOT_RUN: "
                    f"{e.get('verdict')!r}")
            if not e.get("log_digest"):
                problems.append(f"tests[{i}] log_digest empty")
    if d.get("authority_claims") is None:
        problems.append("authority_claims missing")
    elif d.get("authority_claims"):
        problems.append(f"authority_claims non-empty: {d['authority_claims']}")
    for k in ("known_limitations", "incidents", "changed_paths",
              "outputs", "tree_status", "workers", "recommended_next_action"):
        if k not in d:
            problems.append(f"{k} missing")
    o = d.get("outputs")
    if isinstance(o, list):
        for i, e in enumerate(o):
            if not (isinstance(e, dict) and e.get("path")
                    and e.get("sha256")):
                problems.append(f"outputs[{i}] lacks path/sha256")
    return {"file": name, "problems": problems,
            "n_problems": len(problems),
            "sha256": hashlib.sha256(text.encode()).hexdigest()}


if MODE == "base":
    src = load_originals()
else:
    src = load_current()
report = {name: check(name, text) for name, text in sorted(src.items())}
summary = {
    "mode": MODE,
    "n_files": len(report),
    "n_canonical": sum(1 for r in report.values() if r["n_problems"] == 0),
    "n_noncanonical": sum(1 for r in report.values() if r["n_problems"] > 0),
}
print(json.dumps({"summary": summary, "files": report}, indent=1))
