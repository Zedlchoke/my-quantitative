"""rerun_suites.py — EXEC lane: re-run ALL existing suites at the EXEC tree.

  1. ledger synthetic suite       -> 42/42 expected (pytest, read-only)
  2. successor synthetic suite    -> 16/16 expected (pytest, read-only)
  3. PIPE recorder --selftest     -> 10 checks expected (in-process; writes nothing)
  4. PIPE recorder --e2e-synth    -> 3 scenarios expected (in-process; the
     evidence write is REDIRECTED to lanes/EXEC/pipe_rerun_evidence/ so the
     frozen lanes/PIPE files are untouched — same precedent as
     lanes/A7_PRELAUNCH_R2/tmp/run_e2e_synth_redirect.py)

Evidence: lanes/EXEC/suites_rerun_evidence.json. No lane file outside lanes/EXEC
(and the shared sandboxes under ~/.my-quantitative-data) is written.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
RECORDER_DIR = WORKTREE / "research" / "control" / "NFL-WINPROB-NG-SCORED-V1" / "recorder"
EXEC_DIR = WORKTREE / "lanes" / "EXEC"
INTERPRETER = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"
EVIDENCE_REDIRECT = EXEC_DIR / "pipe_rerun_evidence"

sys.path.insert(0, str(RECORDER_DIR))


def run_pytest(target: str) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    out = subprocess.run(
        [INTERPRETER, "-m", "pytest", target, "-q", "--no-header"],
        cwd=str(WORKTREE), capture_output=True, text=True, env=env, timeout=1800,
    )
    tail = [l for l in out.stdout.splitlines() if l.strip()][-3:]
    passed = "passed" in out.stdout and out.returncode == 0
    return {"target": target, "returncode": out.returncode, "tail": tail,
            "ok": passed, "stdout_tail": out.stdout[-400:]}


def run_recorder_mode(mode: str, redirect_evidence: bool) -> dict:
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    import record_batch

    redirected = None
    if redirect_evidence:
        redirected = str(record_batch.LANE_DIR)
        EVIDENCE_REDIRECT.mkdir(parents=True, exist_ok=True)
        record_batch.LANE_DIR = EVIDENCE_REDIRECT
    buf_out, buf_err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            if mode == "selftest":
                results = record_batch.mode_selftest()
                summary = {"checks": len(results), "results": results}
            else:
                evidence = record_batch.mode_e2e_synth()
                summary = {
                    "scenarios": {
                        k: evidence[k] for k in evidence
                        if k.startswith("scenario") or k in
                        ("chain_and_scoring_rehearsal", "fixtures")
                    },
                    "determinism": evidence.get("scenario1_nominal", {}).get(
                        "determinism_double_run"),
                    "real_ledger_paths_existing": evidence.get("real_ledger_paths_existing"),
                }
        return {"mode": mode, "ok": True, "summary": summary}
    except Exception as e:  # noqa: BLE001 — suite failure IS the result
        return {"mode": mode, "ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        if redirect_evidence and redirected is not None:
            record_batch.LANE_DIR = Path(redirected)


def main() -> int:
    results = {}
    results["ledger_42"] = run_pytest(
        "research/control/NFL-WINPROB-NG-SCORED-V1/ledger/test_ledger_synthetic.py")
    results["successor_16"] = run_pytest("lanes/S_SYNTH/test_successor_synthetic.py")
    results["pipe_selftest"] = run_recorder_mode("selftest", redirect_evidence=False)
    results["pipe_e2e_synth"] = run_recorder_mode("e2e_synth", redirect_evidence=True)
    ok = (results["ledger_42"]["ok"] and results["successor_16"]["ok"]
          and results["pipe_selftest"]["ok"] and results["pipe_e2e_synth"]["ok"])
    doc = {"rerun_at_tree": str(WORKTREE), "lane": "EXEC", "all_green": ok,
           "evidence_redirect": str(EVIDENCE_REDIRECT), "results": results}
    EXEC_DIR.mkdir(parents=True, exist_ok=True)
    (EXEC_DIR / "suites_rerun_evidence.json").write_text(
        json.dumps(doc, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: (v["ok"] if isinstance(v, dict) and "ok" in v else v)
                      for k, v in results.items()}, indent=1))
    print("ALL GREEN" if ok else "REGRESSION PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
