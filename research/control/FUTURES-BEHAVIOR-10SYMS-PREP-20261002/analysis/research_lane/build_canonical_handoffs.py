#!/usr/bin/env python3
"""Build canonical-form replacement handoffs for FUTURES-BEHAVIOR-10SYMS-PREP-20261002.

Round co-owner-review-fix-1, lane HANDOFF-RESEARCH (2026-10-02).

What this does (and does NOT do):
- Reads the 14 attempt-1 handoff originals, preserved VERBATIM in
  dispatch/archive_attempt1/ (ORIGINAL_SHA256SUMS.txt records their digests).
- Writes a replacement at each original dispatch/handoff_*.json path that
  carries (a) the canonical zcode_orch_v3_handoff@1 required keys per
  plugins/quant-research-orchestrator/skills/structured-handoff/SKILL.md with
  honest, re-measured values, and (b) the lane-prose fields
  (status/summary/findings/defects/open_questions) copied verbatim from the
  archived original, plus a provenance block.
- outputs[] hashes are computed from the COMMITTED file content at
  commit eae8c3d2 (git show), not from the working tree, because later lanes
  inside the same attempt-1 commit (FIX-A7-FINDINGS) modified some files and
  the committed state is the authoritative attempt-1 output state.
- It does NOT claim canonical validation: the orchestrator MCP validator is
  NOT_RUN in this session; dispatch/validate_handoffs.py is script-only
  evidence.

Honest sha policy:
- dispatch_sha = actual_start_sha = 1f61b489d6ca777243f9c347c2875c21b4e63236
  (worktree base at attempt-1 dispatch; verified: parent of eae8c3d2).
- commit_sha = eae8c3d2d8282f89fb3547ed5572ffe1f88fabc7 (the Lead commit that
  contains every attempt-1 lane output; every outputs[] path verified present
  in that commit).
- cycle_id = 'UNREGISTERED_PREP' — this task is PREP, never a registered cycle.
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.abspath(os.path.join(HERE, "..", ".."))  # task namespace root
DISPATCH = os.path.join(NS, "dispatch")
ARCHIVE = os.path.join(DISPATCH, "archive_attempt1")
REPO = "/Users/hoangminhlong/my-quantitative"

TASK_ID = "FUTURES-BEHAVIOR-10SYMS-PREP-20261002"
COMMIT = "eae8c3d2d8282f89fb3547ed5572ffe1f88fabc7"
BASE = "1f61b489d6ca777243f9c347c2875c21b4e63236"
NS_REL = "research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002"
PY = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"

ENGINE_CMD = (
    f"cd {NS_REL}/code && {PY} -m unittest discover -s tests -t ."
)
ENGINE_LOG_DIGEST = "72c644082293b0c6b577b4a8ab06147038cfb2d216a0e4ece0b9a1262f9facde"
ENGINE_RUN_NOTE = (
    "Re-run at commit eae8c3d2 on a clean checkout (2026-10-02, lane "
    "HANDOFF-RESEARCH): 'Ran 147 tests in 1.783s — OK', exit 0. 147 = 140 "
    "original engine-lane tests + 7 close-only-fill-law regressions added "
    "later inside the same commit by lane FIX-A7-FINDINGS. The engine lane's "
    "own session record was 'Ran 140 tests — OK' (see archived original, "
    "dispatch/archive_attempt1/handoff_ENGINE.json). log_digest is sha256 of "
    "the full stdout+stderr of the re-run."
)

COMMON_LIMITS = [
    "Replacement written by lane HANDOFF-RESEARCH (round co-owner-review-fix-1, "
    "2026-10-02): canonical zcode_orch_v3_handoff@1 keys added with honest "
    "re-measured values; lane-prose fields (status/summary/findings/defects/"
    "open_questions) preserved VERBATIM from the archived original in "
    "dispatch/archive_attempt1/.",
    "Canonical validator MCP NOT_RUN in this session — schema checked by "
    "script dispatch/validate_handoffs.py only.",
    "outputs[] digests are of the file content COMMITTED at eae8c3d2 "
    "(git show), the authoritative attempt-1 output state; where lane "
    "FIX-A7-FINDINGS later edited the same files inside that commit, the "
    "committed (post-fix) state is what is hashed.",
    "The archived original listed this handoff file itself among its outputs; "
    "a JSON file cannot contain its own sha256, so the replacement's outputs[] "
    "excludes the handoff path — the archived original's digest is recorded "
    "in the provenance block instead.",
    "cycle_id 'UNREGISTERED_PREP' is an honest marker: this task is PREP "
    "ONLY, not a registered cycle; no budget/freeze/GO exists.",
]

TREE_STATUS = (
    "clean at eae8c3d2 (all attempt-1 lane outputs were committed by the Lead "
    "in eae8c3d2; the lane left nothing dirty). Re-measured 2026-10-02 by "
    "HANDOFF-RESEARCH: git status --porcelain at the worktree shows only this "
    "round's untracked dispatch/COOWNER_REVIEW_DISPATCH.json."
)


def git_show_bytes(repo_rel_path: str) -> bytes:
    out = subprocess.run(
        ["git", "-C", REPO, "show", f"{COMMIT}:{repo_rel_path}"],
        capture_output=True, check=True,
    )
    return out.stdout


def sha256_commit(repo_rel_path: str) -> str:
    return hashlib.sha256(git_show_bytes(repo_rel_path)).hexdigest()


def archived_digest(name: str) -> str:
    with open(os.path.join(ARCHIVE, name), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


SYMBOL_LANES = {
    "NQ": "SYMBOL-DOSSIER-NQ",
    "ES": "SYMBOL-DOSSIER-ES",
    "CL": "SYMBOL-DOSSIER-CL",
    "NG": "SYMBOL-DOSSIER-NG",
    "GC": "SYMBOL-DOSSIER-GC",
    "SI": "SYMBOL-DOSSIER-SI",
    "6E": "SYMBOL-DOSSIER-6E",
    "6J": "SYMBOL-DOSSIER-6J",
    "6B": "SYMBOL-DOSSIER-6B",
    "6A": "SYMBOL-DOSSIER-6A",
}

SYMBOL_SCRIPTS = {
    "NQ": "NQ_descriptives.py", "ES": "ES_analysis.py",
    "CL": "CL_behavior_stats.py", "NG": "NG_descriptives.py",
    "GC": "GC_descriptives.py", "SI": "SI_behavior_stats.py",
    "6E": "6E_descriptives.py", "6J": "6J_descriptives.py",
    "6B": "6B_descriptives.py", "6A": "6A_descriptives.py",
}

SYMBOL_TESTS_NOTE = (
    "Descriptive-statistics script only — there is no test harness for "
    "descriptive analysis and none is claimed. NOT re-executed by the "
    "replacing lane; the archived JSON next to the script is the lane "
    "session's output (OBSERVED evidence: script + window recorded in the "
    "dossier)."
)

SYMBOL_LIMITS_EXTRA = [
    "analysis/{SYM} script path sits outside the manifest's literal "
    "allowed_paths glob ('analysis/{SYM}_*.json'); the dispatch packet text "
    "and sibling-lane convention authorized the .py-in-analysis/ layout — "
    "flagged in the archived originals (NQ/NG) and disclosed here for all.",
]

NEXT_ACTIONS = {
    "NQ": "Owner decisions via DATA lane spec: useRTH=false re-pull (free, unlocks overnight description), vendor depth vs 16-month acceptance, consensus archive for H3; re-fetch decision is NOT needed for NQ (no missing serials claimed).",
    "ES": "Engine A/B decision: T-5 expiry-week calendar roll vs declared rule (dossier finding); consensus archive choice for H3/H4.",
    "CL": "Owner vendor-depth decision (pre-2025 true volume) + consensus source for EIA surprise (PARAM-GAP) per dossier §6.",
    "NG": "Verify WNGSR intraday cutoff + weekly-estimate revision policy before strict PIT event design; weather-vintage sourcing (NOMADS) for H2.",
    "GC": "TIME-CRITICAL $0: re-fetch the 6 missing serials (GCX5 at the resolve-wall edge now — see SERIAL_REFETCH_MANIFEST.md); consensus PARAM-GAP for H2.",
    "SI": "Adopt liquid-era spread (~$100/contract) over the S6 serial-book row; COMEX price-limit schedule fetch after the measured -31% day.",
    "6E": "Free FRED(SOFR)/ECB-SDW(€STR) pull for the CIP check (H2); engine default = quarterly-only HMUZ roll targets.",
    "6J": "Adopt HMUZ-restricted roll rule for 6J; the 8 missing serials are IBKR-resolve-gated (2 likely already past the wall — see SERIAL_REFETCH_MANIFEST.md) else vendor.",
    "6B": "Re-fetch ONS calendar + BoE announcement time from primary pages (both failed this session); CME tick adjudication 0.0001-vs-0.0002.",
    "6A": "TIME-CRITICAL $0: re-fetch the 6 missing serials before the expired-resolve wall ages them out (6AF6/6AG6 ~Jan-Mar 2027) — see SERIAL_REFETCH_MANIFEST.md.",
    "ENGINE": "Open items blocking launch (BACKTEST_LAUNCH_DRAFT §9): owner data-depth decision, registered-cycle trial budget freeze, owner-declared slippage + per-symbol exchange fees, real holiday calendar, rule set R freeze.",
    "DATA": "Phase-0 FREE probes (per-symbol x schema start dates via metadata.get_record_count, list_unit_prices, get_billable_size) MUST run before any spend; no account may be created before owner GO.",
    "A7": "Fresh-context delta audit of THIS round's fixes (co-owner-review-fix-1) should reproduce the 6 review findings at eae8c3d2 and verify the fix lanes' outputs.",
    "FIX": "Superseded in part by round co-owner-review-fix-1 (R1-R5 findings handled by EXEC-FIX/WF-PIT-FIX lanes); suite re-verified 147 OK at eae8c3d2 by HANDOFF-RESEARCH.",
}

DATA_INCIDENT = (
    "Web-source verification friction during the lane session: bls.gov "
    "schedule fetch returned HTTP 403 (bot filtering; URL search-verified "
    "instead — DATA_ACQUISITION_SPEC.md §8) and the Databento catalog page is "
    "JS-rendered (m4 re-verification note). Lead-described rate-limit retries "
    "are consistent with these outcomes; the archived handoff records the "
    "403/JS-render results, not the retry sequence itself."
)


def build_symbol(sym: str) -> dict:
    name = f"handoff_{sym}.json"
    with open(os.path.join(ARCHIVE, name), encoding="utf-8") as fh:
        orig = json.load(fh)
    outputs = []
    for p in orig["outputs"]:
        if p.endswith(f"/dispatch/{name}"):
            continue  # self-hash impossible; see provenance
        outputs.append({"path": p, "sha256": sha256_commit(p)})
    limits = COMMON_LIMITS + [
        s.replace("{SYM}", sym) for s in SYMBOL_LIMITS_EXTRA
    ] + [
        "tests[] verdict NOT_RUN is honest: descriptive scripts produce "
        "statistics, not pass/fail artifacts; no test harness exists or is "
        "claimed for them."
    ]
    return {
        "schema": "zcode_orch_v3_handoff@1",
        "task_id": TASK_ID,
        "cycle_id": "UNREGISTERED_PREP",
        "role": "lane",
        "lane": SYMBOL_LANES[sym],
        "status": orig.get("status", "COMPLETE"),
        "dispatch_sha": BASE,
        "actual_start_sha": BASE,
        "commit_sha": COMMIT,
        "changed_paths": list(orig["outputs"]),
        "tests": [{
            "command": f"cd {NS_REL}/analysis && {PY} {SYMBOL_SCRIPTS[sym]}",
            "exit_code": None,
            "verdict": "NOT_RUN",
            "log_digest": None,
            "note": SYMBOL_TESTS_NOTE,
        }],
        "authority_claims": [],
        "known_limitations": limits,
        "incidents": [],
        "tree_status": TREE_STATUS,
        "workers": 0,
        "outputs": outputs,
        "recommended_next_action": NEXT_ACTIONS[sym],
        "summary": orig["summary"],
        "findings": orig["findings"],
        "defects": orig.get("defects", []),
        "open_questions": orig.get("open_questions", []),
        "provenance": {
            "replaces": f"dispatch/archive_attempt1/{name}",
            "original_sha256": archived_digest(name),
            "reason": "attempt-1 original missing the 13 canonical keys "
                      "(cycle_id, role, lane, dispatch_sha, actual_start_sha, "
                      "commit_sha, changed_paths, tests, authority_claims, "
                      "known_limitations, incidents, tree_status, workers); "
                      "canonical form restored without altering lane prose",
            "written_by": "lane HANDOFF-RESEARCH, round co-owner-review-fix-1, "
                          "2026-10-02",
            "generator": f"{NS_REL}/analysis/research_lane/build_canonical_handoffs.py",
            "sha_policy": "dispatch_sha=actual_start_sha=worktree base at "
                          "attempt-1 dispatch (1f61b489, parent of eae8c3d2); "
                          "commit_sha=Lead commit containing the outputs; "
                          "outputs hashed at that commit via git show",
        },
    }


def build_engine_like(name: str, lane_id: str) -> dict:
    with open(os.path.join(ARCHIVE, name), encoding="utf-8") as fh:
        orig = json.load(fh)
    outputs = [
        {"path": p, "sha256": sha256_commit(p)}
        for p in orig["outputs"] if not p.endswith(f"/dispatch/{name}")
    ]
    limits = list(COMMON_LIMITS)
    incidents = []
    tests = None
    if name == "handoff_ENGINE.json":
        tests = [{
            "command": ENGINE_CMD,
            "exit_code": 0,
            "verdict": "PASS",
            "log_digest": ENGINE_LOG_DIGEST,
            "note": ENGINE_RUN_NOTE,
        }]
    elif name == "handoff_FIX_A7_FINDINGS.json":
        tests = [{
            "command": ENGINE_CMD,
            "exit_code": 0,
            "verdict": "PASS",
            "log_digest": ENGINE_LOG_DIGEST,
            "note": "Same suite re-run at eae8c3d2 (digest above): 147 OK, "
                    "including the 7 TestCloseOnlyNeverFills regressions this "
                    "lane added; the lane's own session record was 'Ran 147 "
                    "tests in ~1.7s — OK' (archived original).",
        }]
        limits.append(
            "changed_paths spans other lanes' files (dossier/code/data edits "
            "mandated by the audit remediation) — recorded as the archived "
            "original listed them; ownership of those files remained with "
            "their lanes."
        )
    elif name == "handoff_A7.json":
        tests = [{
            "command": f"cd {NS_REL}/audit && {PY} recompute_headline.py",
            "exit_code": None,
            "verdict": "NOT_RUN",
            "log_digest": None,
            "note": "Auditor's independent recomputation helper; NOT re-run "
                    "by the replacing lane. Its archived output JSON "
                    "(recompute_headline.json) is the recorded evidence. "
                    "Code-suite evidence for the commit it audited is carried "
                    "on the ENGINE/FIX handoffs (147 OK at eae8c3d2).",
        }]
        limits.append(
            "This archived artifact records a DELTA audit of the FIX lane's "
            "work (its 'lane_id' field says FIX-A7-FINDINGS in the original "
            "prose); the canonical lane field uses the dispatch manifest's "
            "A7-AUDIT lane id. Both readings preserved."
        )
    elif name == "handoff_DATA.json":
        tests = [{
            "command": f"cd {NS_REL}/data/scripts && {PY} measure_coverage.py && {PY} build_coverage_manifest.py",
            "exit_code": None,
            "verdict": "NOT_RUN",
            "log_digest": None,
            "note": "Coverage-measurement scripts (descriptive corpus "
                    "census); the archived original records that "
                    "measure_coverage.py was re-executed once by the lane "
                    "with identical results after an earlier interrupted "
                    "run. NOT re-run by the replacing lane.",
        }]
        incidents.append(DATA_INCIDENT)
    return {
        "schema": "zcode_orch_v3_handoff@1",
        "task_id": TASK_ID,
        "cycle_id": "UNREGISTERED_PREP",
        "role": "lane",
        "lane": lane_id,
        "status": orig.get("status", "COMPLETE"),
        "dispatch_sha": BASE,
        "actual_start_sha": BASE,
        "commit_sha": COMMIT,
        "changed_paths": list(orig["outputs"]),
        "tests": tests,
        "authority_claims": [],
        "known_limitations": limits,
        "incidents": incidents,
        "tree_status": TREE_STATUS,
        "workers": 0,
        "outputs": outputs,
        "recommended_next_action": NEXT_ACTIONS[
            {"handoff_ENGINE.json": "ENGINE",
             "handoff_DATA.json": "DATA",
             "handoff_A7.json": "A7",
             "handoff_FIX_A7_FINDINGS.json": "FIX"}[name]
        ],
        "summary": orig["summary"],
        "findings": orig["findings"],
        "defects": orig.get("defects", []),
        "open_questions": orig.get("open_questions", []),
        "provenance": {
            "replaces": f"dispatch/archive_attempt1/{name}",
            "original_sha256": archived_digest(name),
            "reason": "canonical-key completion (see SKILL.md required keys)",
            "written_by": "lane HANDOFF-RESEARCH, round co-owner-review-fix-1, 2026-10-02",
            "generator": f"{NS_REL}/analysis/research_lane/build_canonical_handoffs.py",
            "sha_policy": "dispatch_sha=actual_start_sha=1f61b489; commit_sha=eae8c3d2; outputs hashed at that commit",
        },
    }


def main() -> int:
    made = []
    for sym in SYMBOL_LANES:
        doc = build_symbol(sym)
        path = os.path.join(DISPATCH, f"handoff_{sym}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        made.append(os.path.basename(path))
    for name, lane_id in [
        ("handoff_ENGINE.json", "BACKTEST-ENGINE-PREP"),
        ("handoff_DATA.json", "DATA-PIT-ACQUISITION-PREP"),
        ("handoff_A7.json", "A7-AUDIT"),
        ("handoff_FIX_A7_FINDINGS.json", "FIX-A7-FINDINGS"),
    ]:
        doc = build_engine_like(name, lane_id)
        with open(os.path.join(DISPATCH, name), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        made.append(name)
    print(f"wrote {len(made)} canonical replacement handoffs:")
    for m in sorted(made):
        print("  -", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
