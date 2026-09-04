"""A7 TERMINAL spot-recompute (C2): rerun compute_cell for ONE cell
(family2:anchor, the decisive survivor cell) in the A7 worktree against
e-exec-1's frozen data, with the W3C freeze token set, and compare the
fresh record_id + every booked field against the canonical ledger row.

Expected benign diffs (driver/publisher-added, not compute_cell output):
  published  (False -> True pre-digest)
  gates / gate_reasons  (stage_a_gates injected by publish_cell)
  observed_delta  (publisher once-only event)
Run from the r-a7-terminal worktree with .venv/bin/python.
"""
import json
import os
import sys

REPO = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3/r-a7-terminal"
E = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3/e-exec-1"
LEDGER = os.path.join(REPO, "research/control/forex_free_v3_run/scored_ledger_published.jsonl")
CELL = "family2:anchor:tier1.0"

sys.path.insert(0, REPO)
from research.assets.forex_free_v3 import scored_runner as R  # noqa: E402
from research.assets.forex_free_v3 import family2 as fam2  # noqa: E402

R.register_family("family2", fam2)

macro_dir = os.path.join(E, "data_raw/forex_free_v3_macro")
price_dir = os.path.join(E, "data_raw/forex_free_v1")
data_paths = {
    "price_h1_dir": price_dir,
    "h1_dir": price_dir,
    "macro_vintages": {a: os.path.join(macro_dir, a + ".json")
                       for a in ("US", "EMU", "GB", "AU", "NZ", "JP", "CH", "CA")},
}

stored = None
with open(LEDGER, "r", encoding="utf-8") as fh:
    for line in fh:
        rec = json.loads(line)
        if rec.get("record_id") == CELL:
            stored = rec
            break
assert stored is not None, f"{CELL} not found in canonical ledger"

fresh = R.compute_cell("family2", "anchor", data_paths,
                       freeze_token=R.FREEZE_TOKEN)

fresh_gates, fresh_reasons = R.stage_a_gates(fresh)

booked_diffs = []
keys = sorted(set(fresh) | set(stored))
BENIGN = {"published", "gates", "gate_reasons", "observed_delta"}
for k in keys:
    if k in BENIGN:
        continue
    if json.dumps(fresh.get(k), sort_keys=True) != json.dumps(stored.get(k), sort_keys=True):
        booked_diffs.append({
            "field": k,
            "fresh": fresh.get(k),
            "stored": stored.get(k),
        })

result = {
    "schema": "forex_free_v3_a7_spot_recompute_v1",
    "cell_id": CELL,
    "fresh_record_id": fresh["record_id"],
    "stored_record_id": stored["record_id"],
    "record_id_match": fresh["record_id"] == stored["record_id"],
    "fresh_scored": fresh["scored"],
    "fresh_real_pnl": fresh["real_pnl"],
    "fresh_gate_verdict": fresh_gates,
    "fresh_gate_reasons": fresh_reasons,
    "stored_gate_verdict": stored["gates"],
    "stored_gate_reasons": stored["gate_reasons"],
    "gate_verdict_match": fresh_gates == stored["gates"],
    "gate_reasons_match": sorted(fresh_reasons) == sorted(stored["gate_reasons"]),
    "booked_field_diffs": booked_diffs,
    "booked_fields_compared": len(keys) - len(BENIGN),
    "booked_fields_identical": len(booked_diffs) == 0,
    "freeze_token": R.FREEZE_TOKEN,
    "code_tree": REPO,
    "data_source": E,
}
print(json.dumps(result, indent=1))
