# a7_cap_probes.py — A7_NEGVERIFY cap + boundary probes (own driver, read-only on
# real bytes; doctoring happens ONLY on tmp copies). Proves:
#   1. a doctored season=2022 row inside a loaded schedule file ABORTS the lane's
#      load_schedule (SEASON_CAP_VIOLATION) under the real 2016..2021 range;
#   2. the healthy copy passes and its max observed season is 2021;
#   3. evaluate-oos refuses real data (OOS_REFUSED_NO_GO_TOKEN) and no GO token exists;
#   4. the lane selftest passes (39/39 claim);
#   5. grid/arm/seed constants in the lane code equal the dispatch-packet values.
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

HARNESS = Path("/Users/hoangminhlong/my-quantitative/.worktrees/nba-playerfeat-scored-v1/integration/lanes/T_SELECT/harness.py")
sys.path.insert(0, str(HARNESS.parent))
import harness  # noqa: E402  (import defines constants only; no data access)

SCHED = Path.home() / ".my-quantitative-data" / "nba-hoopr-v1" / "raw"
GO = Path.home() / ".my-quantitative-data" / "nba-playerfeat-scored-v1" / "GO_EVALUATION_TOKEN"
OUT = Path(__file__).resolve().parent / "a7_cap_probe_results.json"

res: dict = {}
res["code_constants"] = {
    "SEASON_MAX_REAL": harness.SEASON_MAX_REAL,
    "SEASON_MIN_REAL": harness.SEASON_MIN_REAL,
    "WARMUP": list(harness.WARMUP_SEASONS),
    "FOLDS": list(harness.FOLD_SEASONS),
    "FEATURE_SHA256_head": harness.FEATURE_SHA256[:16],
    "GO_TOKEN_PATH": str(harness.GO_TOKEN_PATH),
}
import arms  # noqa: E402
res["arm_constants"] = {
    "PHI_GRID": list(arms.PHI_GRID),
    "PF_GROUPS": list(arms.PF_GROUPS),
    "ELO_K": arms.ELO_K, "ELO_HCA": arms.ELO_HCA, "ELO_GAMMA": arms.ELO_GAMMA,
    "ELO_INIT": arms.ELO_INIT, "SEED": arms.SEED, "BOOTSTRAP_N": arms.BOOTSTRAP_N,
    "SLOPE_BAND": list(arms.SLOPE_BAND),
    "GROUP_COLUMNS": {k: list(v) for k, v in arms.GROUP_COLUMNS.items()},
    "n_grid_configs": len(arms.grid_configs()),
}
DISPATCH_CONST = {
    "PHI_GRID": [-50.0, -25.0, 0.0, 25.0, 50.0],
    "PF_GROUPS": ["PF-A", "PF-B", "PF-C"],
    "ELO_K": 32.0, "ELO_HCA": 100.0, "ELO_GAMMA": 0.75, "ELO_INIT": 1500.0,
    "SEED": 20261005, "BOOTSTRAP_N": 10000, "SLOPE_BAND": [0.85, 1.15],
    "GROUP_COLUMNS": {"PF-A": ["a_top5_share_k5", "a_load_top5_k5"],
                      "PF-B": ["b_form_top3"],
                      "PF-C": ["c_abs_out", "c_abs_streak"]},
}
res["constants_match_dispatch"] = all(
    res["arm_constants"][k] == v for k, v in DISPATCH_CONST.items()
) and res["code_constants"]["SEASON_MAX_REAL"] == 2021

# --- probe 1/2: doctored 2022 row aborts; healthy copy passes (full 2016..2021 range)
with tempfile.TemporaryDirectory() as td:
    tdp = Path(td)
    for s in range(2016, 2022):
        shutil.copy2(SCHED / f"nba_schedule_{s}.csv", tdp / f"nba_schedule_{s}.csv")
    healthy = harness.load_schedule(tdp, 2016, 2021)
    res["healthy_max_season"] = int(healthy["season"].max())
    res["healthy_rows"] = int(len(healthy))
    df = pd.read_csv(tdp / "nba_schedule_2021.csv", low_memory=False)
    df.loc[df.index[0], "season"] = 2022
    df.to_csv(tdp / "nba_schedule_2021.csv", index=False)
    try:
        harness.load_schedule(tdp, 2016, 2021)
        res["doctored_2022_aborts"] = False
        res["doctored_2022_msg"] = "NO ABORT — CAP BYPASSED"
    except harness.TechAbort as e:
        res["doctored_2022_aborts"] = True
        res["doctored_2022_msg"] = str(e)[:220]

# --- probe 3: evaluate-oos refuses real data; GO token absent
res["go_token_exists"] = GO.exists()
if res["go_token_exists"]:
    res["evaluate_oos_refusal"] = "FAIL: GO TOKEN EXISTS"
else:
    p = subprocess.run(
        [sys.executable, str(HARNESS), "evaluate-oos", "--real"],
        capture_output=True, text=True, timeout=120,
    )
    combined = (p.stdout + p.stderr)
    res["evaluate_oos_exit_code"] = p.returncode
    res["evaluate_oos_refusal"] = ("OOS_REFUSED_NO_GO_TOKEN" in combined)
    res["evaluate_oos_msg_head"] = combined.strip().splitlines()[0][:200] if combined.strip() else ""

# --- probe 4: lane selftest (their claim: 39/39 PASS exit 0)
p2 = subprocess.run([sys.executable, str(HARNESS), "--selftest"],
                    capture_output=True, text=True, timeout=600)
tail = [l for l in p2.stdout.strip().splitlines() if l.startswith("selftest:")]
res["selftest_exit_code"] = p2.returncode
res["selftest_tail"] = tail[-1] if tail else p2.stdout[-200:]

res["ok"] = bool(res["doctored_2022_aborts"] and res["healthy_max_season"] == 2021
                 and res["constants_match_dispatch"] and (not res["go_token_exists"])
                 and res["evaluate_oos_refusal"] and res["evaluate_oos_exit_code"] != 0
                 and res["selftest_exit_code"] == 0)
OUT.write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=2))
sys.exit(0 if res["ok"] else 1)
