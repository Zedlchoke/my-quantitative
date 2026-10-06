"""Reproduce F-V2 through the PRODUCTION runner (sandbox, fake GO):
tamper the scored_executor pin INSIDE v2_2_addendum of the sandbox
contract copy => check_drift fails, but the execution gate stays
allowed=true (addendum pins absent from gate facts + TOCTOU base-only)."""
import json, subprocess, sys, tempfile, shutil
from pathlib import Path
RUNNER_DIR = Path.cwd()
SB = RUNNER_DIR / "scratch/synthetic/sandbox"
sys.path.insert(0, str(RUNNER_DIR))
import test_execution_path as T

tmp = Path(tempfile.mkdtemp())
# fresh sandbox copy so we can tamper its contract
sb2 = tmp / "sb"
shutil.copytree(SB, sb2)
ctr_path = sb2 / "launch_contract.json"
ctr = json.load(open(ctr_path))
for np in ctr["v2_2_addendum"]["new_pins"]:
    if np["name"] == "scored_executor":
        np["sha256"] = "f" * 64  # TAMPERED addendum-only pin
json.dump(ctr, open(ctr_path, "w"), indent=1)
# valid fake GO already exists in sandbox (auth/GO_RECORDED.json)
proc = subprocess.run(
    [sys.executable, str(RUNNER_DIR / "scored_runner.py"),
     "--sandbox-root", str(sb2),
     "--contract", str(ctr_path),
     "--registry-path", str(sb2 / "registry" / "CYCLE_REGISTRY.rowcopy.json"),
     "--go-artifact", str(sb2 / "research/control/FUTURES-ES-PB1-V1/authority/GO_RECORDED.json"),
     "--ledger-path", str(sb2 / "ledger" / "fv2_repro.jsonl"),
     "--run-label", "fv2_repro"],
    capture_output=True, text=True, timeout=600)
# pull the refusal-gate verdict from the manifest written under run dir
man = None
for p in (tmp / "run").rglob("manifest.json") if (tmp / "run").exists() else []:
    man = json.load(open(p)); break
if man is None:
    for p in sb2.rglob("run_manifest*.json"):
        man = json.load(open(p)); break
out = {
  "runner_rc": proc.returncode,
  "refusal_gate": (man or {}).get("refusal_gate"),
  "drift_pass": ((man or {}).get("drift_check") or {}).get("pass"),
  "drift_mismatched": ((man or {}).get("drift_check") or {}).get("mismatched_pins"),
  "stderr_tail": proc.stderr[-300:],
}
print(json.dumps(out, indent=1))
