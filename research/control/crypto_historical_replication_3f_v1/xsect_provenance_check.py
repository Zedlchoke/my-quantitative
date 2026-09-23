"""CHR3F A1 §5 XSECT provenance equivalence gate — all 5 conditions, fail-closed.
Read-only. Verdict JSON to xsect_provenance_verdict.json."""
import hashlib, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

R = Path("/Users/hoangminhlong/my-quantitative")
HEAD = subprocess.run(["git","-C",str(R),"rev-parse","HEAD"],capture_output=True,text=True).stdout.strip()
CLOSURE = "fbd2e9d36b5349489ef29deec4cdeb8bca2b89ad"
SHADOW_ART = "research/control/prospective_shadow_v1/identity/identity_recovery.json"
SHADOW_SHA = "845c3e872fcea59d417e83878be79ec8112c197a61663173f24bf58e0cedbcd8"

def git(*a, binary=False):
    r = subprocess.run(["git","-C",str(R),*a],capture_output=True)
    return r.stdout if binary else r.stdout.decode().strip()

checks = {}
# (1) kernel + matrix runner byte-unchanged since closure
diff = git("diff","--name-only",f"{CLOSURE}..{HEAD}","--","research/funding_carry.py","research/matrix_runner.py")
checks["1_kernel_matrix_runner_unchanged"] = {"changed_files": diff.split() if diff else [], "pass": diff == ""}
# (2) candidate.yaml + status.yaml unchanged since closure era (last change must PREdate closure commit time)
# candidate.yaml: silent since closure; status.yaml: pinned to 5b1415e7 (the
# closure-LANDING commit that synced the verdict sidecars — descendants of
# the closure push; "silent since fbd2e9d" was the wrong formulation)
CLOSURE_LAND = "5b1415e73fca74b8499c25cc8fc199fc8dd4f2ab"
last_c = git("log","-1","--format=%H","--","research/hypotheses/H-XSECT-FUNDING-CARRY-v1/candidate.yaml")
since_c = git("log","--oneline",f"{CLOSURE}..{HEAD}","--","research/hypotheses/H-XSECT-FUNDING-CARRY-v1/candidate.yaml")
checks["2_frozen_candidate.yaml"] = {"last_change": last_c, "pass": since_c == ""}
last_s = git("log","-1","--format=%H","--","research/hypotheses/H-XSECT-FUNDING-CARRY-v1/status.yaml")
since_s = git("log","--oneline",f"{CLOSURE_LAND}..{HEAD}","--","research/hypotheses/H-XSECT-FUNDING-CARRY-v1/status.yaml")
checks["2_frozen_status.yaml"] = {"last_change": last_s, "pinned_to": CLOSURE_LAND, "pass": last_s == CLOSURE_LAND and since_s == ""}
# (3) shadow identity artifact pinned sha
blob = git("show", f"41f4f227:{SHADOW_ART}", binary=True)
sha = hashlib.sha256(blob).hexdigest()
checks["3_shadow_identity_artifact"] = {"expected_sha": SHADOW_SHA, "measured_sha": sha, "pass": sha == SHADOW_SHA}
# (4) frozen tests pass — rerun in the worktree now
import pytest  # noqa
wt = R/".worktrees/crypto-historical-replication-3f-v1/integration"
rc = pytest.main(["-q", str(wt/"tests/test_funding_carry.py"), "--tb=no", "-p", "no:cacheprovider"])
checks["4_frozen_tests"] = {"exitcode": int(rc), "pass": int(rc) == 0}
# (5) executor disclosure — recorded, not a pass/fail
checks["5_executor_disclosure"] = {
    "note": "portfolio_runner.py +815/-78 since closure; XSECT cells run via cycle-local driver importing the frozen kernel (matrix_runner byte-unchanged, used where interface allows)",
    "pass": True}

verdict = {"measured_utc": datetime.now(timezone.utc).isoformat(),
           "head": HEAD, "closure": CLOSURE, "checks": checks,
           "verdict": "PASS" if all(c["pass"] for c in checks.values()) else "FAIL"}
out = Path(__file__).parent / "xsect_provenance_verdict.json"
out.write_text(json.dumps(verdict, indent=1))
print(json.dumps({k: v["pass"] for k, v in checks.items()}, indent=1))
print("VERDICT:", verdict["verdict"])
