"""repro_fv2_after_fix.py — the controller's FAIL_FV2 reproduction re-run
AFTER the PIN-ENFORCE fix. Same tamper as repro_fv2.py (LIVE scored_executor
pin -> f*64) against a fresh sandbox copy; asserts the FLIP: exit 2
REFUSED_DRIFT naming scored_executor, ledger REFUSED row, ZERO execution
artifacts. (Script corrected 2026-10-05: evidence = ledger REFUSED row —
refusal_record.json only exists for SANDBOX-ISOLATION refusals; core body
replaced with the controller's proven debug body after a lane-authored
logic defect made the original report false-negatives.)
Run: .venv/bin/python fix3/repro_fv2_after_fix.py"""
import json, subprocess, sys, tempfile, shutil, hashlib
from pathlib import Path
RUNNER_DIR = Path(__file__).resolve().parents[1]
SB = RUNNER_DIR / "scratch/synthetic/sandbox"
CY = "research/control/FUTURES-ES-PB1-V1"
RUNNER = str(RUNNER_DIR / "scored_runner.py")

tmp = Path(tempfile.mkdtemp(prefix="fv2_after_fix_"))
sb2 = tmp / "sb"
shutil.copytree(SB, sb2)
ctr_path = sb2 / "launch_contract.json"
ctr = json.loads(ctr_path.read_text("utf-8"))
live_sha = hashlib.sha256(
    (RUNNER_DIR / "scored_executor.py").read_bytes()).hexdigest()
tampered_in = None
for key in sorted(k for k in ctr
                  if k.startswith("v2_") and k.endswith("_addendum")):
    for np in ctr[key].get("new_pins", []):
        if np["name"] == "scored_executor" and np["sha256"] == live_sha:
            np["sha256"] = "f" * 64
            tampered_in = key
assert tampered_in, "live scored_executor pin not found in the contract"
json.dump(ctr, open(ctr_path, "w", encoding="utf-8"), indent=1)

ledger = str(sb2 / "ledger" / "fv2_repro_after_fix.jsonl")
proc = subprocess.run(
    [sys.executable, RUNNER,
     "--sandbox-root", str(sb2),
     "--contract", str(ctr_path),
     "--registry-path", str(sb2 / "registry/CYCLE_REGISTRY.rowcopy.json"),
     "--go-artifact", str(sb2 / CY / "authority/GO_RECORDED.json"),
     "--ledger-path", ledger, "--run-label", "fv2_repro_after_fix"],
    capture_output=True, text=True, timeout=600)

rows = [json.loads(line) for line in
        Path(ledger).read_text("utf-8").splitlines() if line.strip()] \
    if Path(ledger).exists() else []
refused = [r for r in rows if r.get("status") == "REFUSED"]
rr = refused[-1] if refused else {}

checks = {
    "tampered_live_pin_in": tampered_in,
    "exit_2": proc.returncode == 2,
    "reason_REFUSED_DRIFT": rr.get("reason") == "REFUSED_DRIFT",
    "names_scored_executor":
        "scored_executor" in json.dumps(rr),
    "ledger_REFUSED_row": any(r.get("reason") == "REFUSED_DRIFT"
                              for r in refused),
    "no_runs_dir": not (sb2 / "runs").exists(),
    "no_execution_artifacts": not [p for p in sb2.rglob("*")
                                   if p.is_file()
                                   and ("pass_a" in p.parent.name
                                        or p.name.startswith(
                                            "terminal_handoff"))],
    "no_EXECUTION_COMPLETE_in_stdout":
        "EXECUTION_COMPLETE" not in proc.stdout,
}
out = {
    "runner_rc": proc.returncode,
    "refusal_reason": rr.get("reason"),
    "mismatched_pins": (rr.get("detail") or {}).get("mismatched_pins"),
    "ledger_refused_rows": len(refused),
    "checks": checks,
    "flip_vs_FAIL_FV2": all(checks.values()),
}
print(json.dumps(out, indent=1))
( Path(__file__).resolve().parent / "repro_fv2_after_fix_output.json"
  ).write_text(json.dumps(out, indent=1, sort_keys=True,
                          ensure_ascii=False) + "\n", encoding="utf-8")
( Path(__file__).resolve().parent / "repro_fv2_after_fix_stderr.txt"
  ).write_text(f"exit_code={proc.returncode}\n{proc.stderr}",
               encoding="utf-8")
sys.exit(0 if out["flip_vs_FAIL_FV2"] else 1)
