#!/usr/bin/env python3
"""Script-only validator for FUTURES-BEHAVIOR-10SYMS-PREP-20261002 handoffs.

Round co-owner-review-fix-1, lane HANDOFF-RESEARCH (2026-10-02).

Implements the checks of
plugins/quant-research-orchestrator/skills/structured-handoff/SKILL.md that
can be executed WITHOUT the orchestrator MCP:

1. Required keys present (SKILL.md canonical list):
   task_id, cycle_id, role, lane, dispatch_sha, actual_start_sha, commit_sha,
   changed_paths, tests, authority_claims, known_limitations, incidents,
   tree_status, workers, outputs, recommended_next_action.
2. dispatch_sha == actual_start_sha (SKILL.md: unequal => INVALID, full stop).
3. dispatch_sha / actual_start_sha / commit_sha are 40-hex; commit_sha may be
   null ONLY with an explicit disclosure in known_limitations.
4. authority_claims empty for role 'lane' (lanes have none; non-empty =>
   REFUSED per SKILL.md).
5. tests[] entries have {command, exit_code, verdict}; verdict in
   {PASS, FAIL, NOT_RUN}; PASS requires exit_code == 0 and a log_digest.
6. outputs[] digests re-verified against the file content at commit_sha
   (git show) when commit_sha is set, else against the working tree.
7. status in {COMPLETE, PARTIAL, BLOCKED}; workers is an integer >= 0.

EVIDENCE CLASS DISCLAIMER (do not over-claim): this script is a structural +
digest check only. The canonical orchestrator MCP validator
(orchestrator_validate_handoff) is NOT_RUN in this session and nothing here
may be described as 'canonical-validated' or 'MCP-validated'.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)                     # task namespace root
REPO = "/Users/hoangminhlong/my-quantitative"
# The worktree root that physically contains this dispatch dir (uncommitted
# outputs of null-commit_sha handoffs live here, not in the root checkout):
# NS = <worktree>/research/control/<TASK>; three levels up = worktree root.
WORKTREE = os.path.abspath(os.path.join(NS, "..", "..", ".."))

REQUIRED = [
    "task_id", "cycle_id", "role", "lane", "dispatch_sha", "actual_start_sha",
    "commit_sha", "changed_paths", "tests", "authority_claims",
    "known_limitations", "incidents", "tree_status", "workers", "outputs",
    "recommended_next_action",
]
HEX40 = re.compile(r"^[0-9a-f]{40}$")
VERDICTS = {"PASS", "FAIL", "NOT_RUN"}
STATUSES = {"COMPLETE", "PARTIAL", "BLOCKED"}


def blob_digest(commit: str, repo_rel: str) -> str:
    out = subprocess.run(["git", "-C", REPO, "show", f"{commit}:{repo_rel}"],
                         capture_output=True)
    if out.returncode != 0:
        raise FileNotFoundError(out.stderr.decode()[:200])
    return hashlib.sha256(out.stdout).hexdigest()


def wt_digest(repo_rel: str) -> str:
    with open(os.path.join(WORKTREE, repo_rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def validate(path: str) -> tuple[bool, list[str]]:
    errs, name = [], os.path.basename(path)
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        return False, [f"{name}: unparseable JSON ({exc})"]

    for key in REQUIRED:
        if key not in doc:
            errs.append(f"{name}: missing required key '{key}'")
    if errs:
        return False, errs

    if doc["dispatch_sha"] != doc["actual_start_sha"]:
        errs.append(f"{name}: dispatch_sha != actual_start_sha -> INVALID (SKILL.md refusal rule)")
    for key in ("dispatch_sha", "actual_start_sha"):
        if not HEX40.match(str(doc[key])):
            errs.append(f"{name}: {key} not 40-hex: {doc[key]!r}")
    cs = doc["commit_sha"]
    if cs is None:
        joined = " ".join(doc["known_limitations"])
        if "commit" not in joined.lower() or "null" not in joined.lower():
            errs.append(f"{name}: commit_sha null WITHOUT disclosure in known_limitations")
    elif not HEX40.match(str(cs)):
        errs.append(f"{name}: commit_sha not 40-hex and not null: {cs!r}")

    if doc["role"] == "lane" and doc["authority_claims"]:
        errs.append(f"{name}: lane authority_claims non-empty -> REFUSED per SKILL.md")

    if doc.get("status") not in STATUSES:
        errs.append(f"{name}: status {doc.get('status')!r} not in {sorted(STATUSES)}")
    if not isinstance(doc["workers"], int) or doc["workers"] < 0:
        errs.append(f"{name}: workers must be an integer >= 0")

    for i, t in enumerate(doc["tests"]):
        for tk in ("command", "exit_code", "verdict"):
            if tk not in t:
                errs.append(f"{name}: tests[{i}] missing '{tk}'")
        if t.get("verdict") not in VERDICTS:
            errs.append(f"{name}: tests[{i}] verdict {t.get('verdict')!r} not in {sorted(VERDICTS)}")
        if t.get("verdict") == "PASS":
            if t.get("exit_code") != 0:
                errs.append(f"{name}: tests[{i}] PASS with exit_code != 0")
            if not t.get("log_digest"):
                errs.append(f"{name}: tests[{i}] PASS without log_digest")

    commit = doc["commit_sha"]
    for i, o in enumerate(doc["outputs"]):
        p = o.get("path")
        if not p or "sha256" not in o:
            errs.append(f"{name}: outputs[{i}] missing path/sha256")
            continue
        try:
            digest = (blob_digest(commit, p) if commit
                      else wt_digest(p))
        except (FileNotFoundError, OSError) as exc:
            errs.append(f"{name}: outputs[{i}] {p}: unreadable ({str(exc)[:80]})")
            continue
        if digest != o["sha256"]:
            errs.append(f"{name}: outputs[{i}] {p}: sha256 MISMATCH "
                        f"(recorded {o['sha256'][:12]}…, "
                        f"{'commit' if commit else 'worktree'} {digest[:12]}…)")
    return (not errs), errs


def main() -> int:
    targets = sorted(
        os.path.join(HERE, f) for f in os.listdir(HERE)
        if f.startswith("handoff_") and f.endswith(".json")
    )
    print(f"validate_handoffs.py — script-only evidence (orchestrator MCP "
          f"validator NOT_RUN in this session)")
    print(f"targets: {len(targets)} handoff files in dispatch/\n")
    bad = 0
    for path in targets:
        ok, errs = validate(path)
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        line = (f"{'PASS' if ok else 'FAIL'}  {os.path.basename(path):32s} "
                f"lane={doc.get('lane','-'):30s} dispatch==start="
                f"{doc['dispatch_sha'] == doc['actual_start_sha']} "
                f"commit={(doc['commit_sha'] or 'null')[:12]} "
                f"outputs={len(doc['outputs'])} "
                f"tests={','.join(t['verdict'] for t in doc['tests'])}")
        print(line)
        for e in errs:
            print("      -", e)
        bad += 0 if ok else 1
    print(f"\nSUMMARY: {len(targets) - bad}/{len(targets)} structurally valid; "
          f"{bad} with findings")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
