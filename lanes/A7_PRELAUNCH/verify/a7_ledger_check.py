# a7_ledger_check.py — A7_NEGVERIFY ledger completeness + cross-check of every
# ledger pooled-LL against A7's own recompute grid.
from __future__ import annotations

import json
import sys
from pathlib import Path

LEDGER = Path("/Users/hoangminhlong/my-quantitative/.worktrees/nba-playerfeat-scored-v1/integration/lanes/T_SELECT/SELECTION_LEDGER.jsonl")
OWN = Path(__file__).resolve().parent / "a7_recompute_results.json"
OUT = Path(__file__).resolve().parent / "a7_ledger_check_results.json"

rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
res: dict = {"n_rows": len(rows)}
res["config_ids"] = [r["config_id"] for r in rows]

expected_grid = {f"{a}|phi={p:g}" for a in ("PF-A", "PF-B", "PF-C") for p in (-50.0, -25.0, 0.0, 25.0, 50.0)}
expected_refs = {"B0", "B1*", "B1-HCA0"}
got = set(res["config_ids"])
res["grid_rows_present"] = expected_grid <= got
res["ref_rows_present"] = expected_refs <= got
res["unexpected_rows"] = sorted(got - expected_grid - expected_refs)
res["completeness_18"] = len(rows) == 18 and res["grid_rows_present"] and res["ref_rows_present"] and not res["unexpected_rows"]

own = json.load(open(OWN))
errs = {}
for r in rows:
    cid = r["config_id"]
    if cid in expected_grid:
        arm, phi = cid.split("|phi=")
        errs[cid] = abs(float(r["pooled_ll"]) - own["grid_pooled_ll_own"][arm][phi])
    elif cid == "B1*":
        errs[cid] = abs(float(r["pooled_ll"]) - own["b1_pooled_ll"])
    elif cid == "B0":
        errs[cid] = abs(float(r["pooled_ll"]) - own["b0_pooled_ll"])
    elif cid == "B1-HCA0":
        errs[cid] = abs(float(r["pooled_ll"]) - own["hca0_pooled_ll"])
res["max_abs_err_pooled_ll_vs_own"] = max(errs.values())
res["argmax_cfg"] = max(errs, key=errs.get)

# grid-min-at-phi0 from the LEDGER itself
mins = {}
for a in ("PF-A", "PF-B", "PF-C"):
    lls = {float(r["phi"]): float(r["pooled_ll"]) for r in rows if r["config_id"].startswith(a + "|")}
    mins[a] = min(lls, key=lls.get)
res["ledger_grid_min_phi"] = mins
res["ledger_grid_min_all_zero"] = all(v == 0.0 for v in mins.values())

# verdict coherence: every non-zero phi INCREASES pooled LL vs B1* (negative direction)
b1 = [r for r in rows if r["config_id"] == "B1*"][0]["pooled_ll"]
res["all_nonzero_phis_increase_ll"] = all(
    float(r["pooled_ll"]) > float(b1) for r in rows
    if r["config_id"] in expected_grid and float(r["phi"]) != 0.0
)
res["admitted_arms"] = sorted({r["arm"] for r in rows if r.get("arm_verdict") == "ADMITTED"})
res["selected_for_arm_all_phi0"] = all(
    float(r["phi"]) == 0.0 for r in rows if r.get("selected_for_arm")
)
res["ok"] = bool(res["completeness_18"] and res["max_abs_err_pooled_ll_vs_own"] < 1e-9
                 and res["ledger_grid_min_all_zero"] and res["all_nonzero_phis_increase_ll"]
                 and res["selected_for_arm_all_phi0"] and not res["admitted_arms"])
OUT.write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=2))
sys.exit(0 if res["ok"] else 1)
