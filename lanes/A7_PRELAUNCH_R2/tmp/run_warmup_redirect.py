import json, sys
from pathlib import Path
REC = Path("/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration/research/control/NFL-WINPROB-NG-SCORED-V1/recorder")
TMP = Path("/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration/lanes/A7_PRELAUNCH_R2/tmp/warmup_rerun")
sys.path.insert(0, str(REC))
import record_batch as rb
TMP.mkdir(parents=True, exist_ok=True)
rb.LANE_DIR = TMP
ev = rb.mode_warmup_check()
(TMP / "warmup_rerun_evidence.json").write_text(json.dumps(ev, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
print("WARMUP_REDIRECT_OK")
