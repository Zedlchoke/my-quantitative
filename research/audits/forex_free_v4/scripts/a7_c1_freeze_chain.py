#!/usr/bin/env python3
"""A7 C1: recompute every code hash in w4_freeze.json from bytes in this tree;
compare V3 kernel hashes against w3_freeze.json; verify freeze commit and post-freeze drift."""
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v4/q-a7-prelaunch")
W4 = ROOT / "research/control/forex_free_v4_run/w4_freeze.json"
W3 = ROOT / "research/control/forex_free_v3_run/w3_freeze.json"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout.strip()

w4 = json.loads(W4.read_text())
w3 = json.loads(W3.read_text())

report = {"check": "C1_freeze_chain", "results": {}}

# 1. recompute all hashes listed in w4 code_hashes
hash_results = {}
mismatch = []
missing = []
for rel, expected in sorted(w4["code_hashes"].items()):
    p = ROOT / rel
    if not p.is_file():
        missing.append(rel)
        hash_results[rel] = {"expected": expected, "actual": None, "match": False, "exists": False}
        continue
    actual = sha256_file(p)
    ok = actual == expected
    if not ok:
        mismatch.append(rel)
    hash_results[rel] = {"expected": expected, "actual": actual, "match": ok, "exists": True}
report["results"]["code_hash_recompute"] = {
    "n_files": len(w4["code_hashes"]),
    "n_match": sum(1 for v in hash_results.values() if v["match"]),
    "mismatch": mismatch,
    "missing": missing,
    "detail": hash_results,
}

# 2. V3 kernel 7 files: w4 hash equality vs w3 hash equality
v3_invariance = {}
v3_w3_hashes = w3.get("code_hashes", {})
for rel, w4flag in w4.get("v3_kernel_invariance", {}).items():
    w4_actual = hash_results.get(rel, {}).get("actual")
    w3_expected = v3_w3_hashes.get(rel)
    entry = {
        "w4_claims_invariant": bool(w4flag),
        "w4_hash_matches_tree": hash_results.get(rel, {}).get("match", False),
        "w3_has_hash": rel in v3_w3_hashes,
        "w3_hash": w3_expected,
        "tree_hash": w4_actual,
        "w3_eq_w4": (w3_expected == w4_actual) if (w3_expected and w4_actual) else None,
    }
    v3_invariance[rel] = entry
report["results"]["v3_kernel_invariance_vs_w3"] = {
    "n": len(v3_invariance),
    "n_eq": sum(1 for v in v3_invariance.values() if v["w3_eq_w4"] is True),
    "detail": v3_invariance,
}

# 3. w4_freeze.json committed exactly at 80d3509 and content unchanged since
head = git("rev-parse", "HEAD")
freeze_commit_contains_w4 = git("log", "--format=%H", "-1", "80d3509", "--", "research/control/forex_free_v4_run/w4_freeze.json")
# hash of w4_freeze.json at 80d3509 vs at HEAD
w4_at_freeze = git("show", "80d3509:research/control/forex_free_v4_run/w4_freeze.json")
w4_now = W4.read_text()
report["results"]["freeze_file_stability"] = {
    "head": head,
    "freeze_commit": "80d3509",
    "freeze_commit_is_ancestor": subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", "80d3509", "HEAD"], capture_output=True).returncode == 0,
    "w4_bytes_same_at_80d3509_and_HEAD": (w4_at_freeze == w4_now),
    "w4_sha256_now": sha256_file(W4),
}

# 4. post-freeze drift: files changed 80d3509..HEAD restricted to code paths
CODE_PREFIXES = ("research/assets/", "tests/", "scripts/", "backtest/", "config/", "contracts/", "risk/", "data/")
drift = [ln for ln in git("diff", "--name-only", "80d3509", "HEAD").splitlines() if ln]
non_control = [f for f in drift if not f.startswith("research/control/forex_free_v4_run/")]
report["results"]["post_freeze_drift"] = {
    "changed_files": drift,
    "changed_outside_v4_control": non_control,
    "clean": len(non_control) == 0,
}

# 5. code-path drift over the whole cycle: 754b851..80d3509 should only touch v4 assets/tests + control
cycle_code = [f for f in git("diff", "--name-only", "754b851", "80d3509").splitlines() if f]
code_only_cycle = [f for f in cycle_code if f.startswith(("research/assets/forex_free_v4/", "tests/assets/forex_free_v4/"))]
cycle_other = [f for f in cycle_code if not f.startswith(("research/assets/forex_free_v4/", "tests/assets/forex_free_v4/", "research/control/"))]
report["results"]["cycle_code_scope_754b851_to_80d3509"] = {
    "n_code_files": len(code_only_cycle),
    "other_touched": cycle_other[:30],
}

# 6. verify the freeze hash of the driver itself is the one the driver would self-check (read driver gate code presence)
driver_rel = "research/assets/forex_free_v4/exec_driver_v4.py"
report["results"]["driver_self_hash_entry"] = {
    "in_freeze": driver_rel in w4["code_hashes"],
    "match": hash_results.get(driver_rel, {}).get("match", False),
}

ok = (
    report["results"]["code_hash_recompute"]["n_match"] == report["results"]["code_hash_recompute"]["n_files"]
    and not missing
    and report["results"]["v3_kernel_invariance_vs_w3"]["n_eq"] == 7
    and report["results"]["freeze_file_stability"]["w4_bytes_same_at_80d3509_and_HEAD"]
    and report["results"]["post_freeze_drift"]["clean"]
)
report["verdict"] = "PASS" if ok else "FAIL"
print(json.dumps(report, indent=1))
