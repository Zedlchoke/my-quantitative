#!/usr/bin/env python
"""FOREX-FREE-V1 F8 executor: runs the six frozen scored cells
(family1 anchor/neighbour/control, family2 anchor/neighbour/control)
from the W1 code tree against the staged canonical H1 data.
Serial: anchor -> neighbour -> control per family. Observed counter
increments per computed cell; publication is gated by the W1 verdict.
Also runs the cost-stress tiers and drop-one-pair analyses per cell
(recorded in the cell's stress block)."""
import hashlib, importlib, json, os, sys

W1_TREE = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v1/exec-2"
INTEG = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v1/integration"
VERDICT = os.path.join(INTEG, "research/control/forex_free_v1_run/w1_launch_verdict.json")
W1_SHA = "f33a32a2f245d08447a67bb6a0b1f7276c7c5a85"
DATA_ROOT = os.path.join(W1_TREE, "data_raw")          # staged read-only copy
LEDGER = os.path.join(DATA_ROOT, "forex_free_v1", "scored_ledger.jsonl")
PAIRS = ["EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/JPY", "USD/CHF", "USD/CAD"]

sys.path.insert(0, W1_TREE)
from research.assets.forex_free_v1 import td_loader, scored_runner as R  # noqa: E402
import importlib  # noqa: E402
family1 = importlib.import_module("research.assets.forex_free_v1.family1")  # noqa: E402
family2 = importlib.import_module("research.assets.forex_free_v1.family2")  # noqa: E402

manifest = json.load(open(os.path.join(W1_TREE, "research/control/forex_free_v1_run/data_probe/request_manifest.json")))
pair_bars, quarantine = {}, {}
for p in PAIRS:
    rows, q = td_loader.load_pair_h1(p, DATA_ROOT, manifest)
    pair_bars[p] = rows
    quarantine[p] = len(q)
print("data loaded:", {p: len(b) for p, b in pair_bars.items()}, "quarantine:", quarantine, flush=True)

MODULES = {"family1": family1, "family2": family2}
cells = []
for family in ("family1", "family2"):
    mod = MODULES[family]
    for arm in R.ARM_ORDER:  # anchor -> neighbour -> control, serial
        base_run = R.run_family_cell(mod, family, pair_bars, arm, 1.0)
        rec = R.assemble_cell_record(base_run, family, arm, 1.0)
        rec["module_scoring_authorized_field"] = base_run.get("module_scoring_authorized_fields")
        # cost stresses (same frozen arm, higher tiers)
        stress = {}
        for tier in (1.5, 2.0):
            srun = R.run_family_cell(mod, family, pair_bars, arm, tier)
            srec = R.assemble_cell_record(srun, family, arm, tier)
            stress[f"tier{tier}"] = {"expectancy": srec["book"]["expectancy"],
                                     "profit_factor": srec["profit_factor"] if "profit_factor" in srec else srec["book"]["profit_factor"],
                                     "positive": srec["book"]["positive"]}
        # drop-one-pair analysis on base trades
        drops = {}
        for dp in PAIRS:
            kept = [t for t in base_run["trades"] if t["pair"] != dp]
            m = R.book_metrics([t["pnl"] for t in kept]) if kept else {"expectancy": None}
            drops[dp] = {"expectancy": m["expectancy"], "positive": (m["expectancy"] or 0) > 0}
        gates = R.stage_a_gates(rec)
        observed_delta, published = R.publish_cell(LEDGER, rec, VERDICT, W1_SHA)
        cell = {"label": rec["label"], "digest": rec["digest"], "gates": gates,
                "book": rec["book"], "mdd_usd": rec["mdd_usd"], "folds": rec["folds"],
                "pair_concentration": rec["pair_concentration"],
                "fold_concentration": rec["fold_concentration"],
                "stress": stress, "drop_one_pair_positive": drops,
                "observed_delta": observed_delta, "published": published,
                "quarantine": quarantine}
        cells.append(cell)
        print(json.dumps({"cell": rec["label"], "gates": gates,
                          "trades": rec["book"]["trades"],
                          "expectancy": rec["book"]["expectancy"],
                          "pf": rec["book"]["profit_factor"],
                          "total_pnl": rec["book"]["total_pnl"]}), flush=True)

out = {"cells": cells,
       "observed_total": sum(c["observed_delta"] for c in cells),
       "published_total": sum(1 for c in cells if c["published"]),
       "ledger_sha256": hashlib.sha256(open(LEDGER, "rb").read()).hexdigest()}
with open(os.path.join(W1_TREE, "data_raw/forex_free_v1/execution_summary.json"), "w") as f:
    json.dump(out, f, indent=1, default=str)
print("EXECUTION DONE observed=%d published=%d" % (out["observed_total"], out["published_total"]), flush=True)
