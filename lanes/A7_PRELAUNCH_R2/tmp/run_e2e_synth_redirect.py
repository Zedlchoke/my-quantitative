"""A7_R2 independent re-run of record_batch --mode e2e-synth.
Audited code untouched; ALL module writes redirected into lanes/A7_PRELAUNCH_R2/tmp/.
"""
import json, sys
from pathlib import Path

REC = Path("/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration/research/control/NFL-WINPROB-NG-SCORED-V1/recorder")
TMP = Path("/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration/lanes/A7_PRELAUNCH_R2/tmp/e2e_rerun")
sys.path.insert(0, str(REC))
import record_batch as rb

TMP.mkdir(parents=True, exist_ok=True)
rb.LANE_DIR = TMP / "lane_out"
rb.RECORDER_SANDBOX = TMP / "sandbox"
rb.E2E_DIR = TMP / "sandbox" / "e2e"

ev = rb.mode_e2e_synth()
out = TMP / "e2e_rerun_evidence.json"
out.write_text(json.dumps(ev, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
print("REDIRECTED-RE_RUN_OK", out)
