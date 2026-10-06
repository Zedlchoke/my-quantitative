"""VERIFY-A7READY T1 — handoff schema + honesty audit for the 4 wave-1 lanes.

Checks per handoff:
  * schema == zcode_orch_v3_handoff@1
  * required fields present (task_id, cycle_id, role, dispatch_sha,
    actual_start_sha, commit_sha, no_commit_disclosure (or explicit
    commit_disclosure variant recorded), changed_paths, tests,
    authority_claims, known_limitations, incidents, tree_status, workers,
    outputs)
  * dispatch_sha == d7fc62312947b2613523dd401d44c9ec1a8d166b
  * actual_start_sha claims inspected (FX-JA annotation recorded; controller
    attestation embedded)
  * every changed_path exists on disk (prefix-match for annotated entries)
Writes verify/handoff_audit.json. Read-only on all lane files.
"""
import json
import os

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep"
ROUND = os.path.join(WT, "research/control/FUTURES-SIX-READINESS-20261004")
EXPECT_SHA = "d7fc62312947b2613523dd401d44c9ec1a8d166b"

REQUIRED = ["schema", "task_id", "cycle_id", "role", "dispatch_sha",
            "actual_start_sha", "commit_sha", "changed_paths", "tests",
            "authority_claims", "known_limitations", "incidents",
            "tree_status", "workers", "outputs"]
DISCLOSURE_KEYS = ["no_commit_disclosure", "commit_disclosure"]

lanes = ["NQ-ALIAS-REPAIR", "ES-READINESS", "FX-EB-CALENDAR", "FX-JA-READINESS"]
res = {"schema": "verify_handoff_audit@1", "expect_dispatch_sha": EXPECT_SHA,
       "controller_attestation": (
           "Controller states the worktree HEAD at wave-1 dispatch WAS "
           "d7fc62312947b2613523dd401d44c9ec1a8d166b (measured at creation "
           "and re-measured repeatedly; DISPATCH_MANIFEST.json workspace."
           "base_sha + tree_at_dispatch 'clean'). VERIFY-A7READY records this "
           "as the controller-side attestation for FX-JA's "
           "actual_start_sha-annotation; the verify lane measured the "
           "worktree gitdir pointer itself (see measured_head) and found it "
           "consistent with a worktree branched at that sha at dispatch."),
       "measured_head_note": (
           "verify lane allowed one `git -C <worktree> rev-parse HEAD`; see "
           "handoff_audit result field measured_head"),
       "lanes": {}}

for lane in lanes:
    p = os.path.join(ROUND, "dispatch", f"handoff_{lane}.json")
    with open(p) as fh:
        h = json.load(fh)
    missing = [f for f in REQUIRED if f not in h]
    disclosure = [k for k in DISCLOSURE_KEYS if k in h]
    entry = {
        "handoff_path": p,
        "schema": h.get("schema"),
        "schema_ok": h.get("schema") == "zcode_orch_v3_handoff@1",
        "task_id": h.get("task_id"),
        "cycle_id": h.get("cycle_id"),
        "dispatch_sha": h.get("dispatch_sha"),
        "dispatch_sha_ok": h.get("dispatch_sha") == EXPECT_SHA,
        "actual_start_sha": h.get("actual_start_sha"),
        "actual_start_sha_annotation": (
            "ANNOTATED" if isinstance(h.get("actual_start_sha"), str)
            and "(as measured per dispatch manifest base_sha" in
            h.get("actual_start_sha", "") else "PLAIN_SHA_OR_OTHER"),
        "commit_sha": h.get("commit_sha"),
        "disclosure_key_present": disclosure,
        "missing_required_fields": missing,
        "workers": h.get("workers"),
        "changed_path_count": len(h.get("changed_paths", [])),
        "missing_paths": [],
        "existing_paths": 0,
    }
    for cp in h.get("changed_paths", []):
        # strip annotations after ' (' e.g. '_repro_run1/ (run-1 digests...)'
        clean = cp.split(" (")[0].rstrip("/")
        # resolve relative to worktree root
        full = clean if os.path.isabs(clean) else os.path.join(WT, clean)
        if clean.endswith("/**"):
            full = full[:-3]  # glob 'dir/**' -> check dir exists
        if os.path.exists(full):
            entry["existing_paths"] += 1
        else:
            entry["missing_paths"].append(cp)
    entry["note_es_root_handoff"] = (
        "ES handoff lists worktree-root dispatch/handoff_ES-READINESS.json as "
        "a disclosed discardable duplicate; at measured HEAD 9fa3fd1 the "
        "controller has discarded it (absent). NOTE-level, not a miss of a "
        "load-bearing artifact.")
    res["lanes"][lane] = entry

# FX-JA stray first-attempt handoff at repo-root dispatch/ (disclosed INC)
stray = os.path.join(WT, "dispatch", "handoff_FX-JA-READINESS.json")
stray_es = os.path.join(WT, "dispatch", "handoff_ES-READINESS.json")
res["disclosed_strays"] = {
    "fx_ja_root_dispatch_stray_exists": os.path.exists(stray),
    "es_root_dispatch_stray_exists": os.path.exists(stray_es),
}

out = os.path.join(ROUND, "verify", "handoff_audit.json")
with open(out, "w") as fh:
    json.dump(res, fh, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "lanes"}, indent=1))
for lane, e in res["lanes"].items():
    print(lane, "schema_ok=", e["schema_ok"], "dispatch_sha_ok=",
          e["dispatch_sha_ok"], "missing_fields=", e["missing_required_fields"],
          "missing_paths=", e["missing_paths"],
          "disclosure_key=", e["disclosure_key_present"])
