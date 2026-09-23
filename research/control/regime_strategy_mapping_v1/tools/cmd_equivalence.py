#!/usr/bin/env python
"""Engine-equivalence gate (pre-outcome; plan §9).

Runs arms A1 (ALWAYS_ON_MR), A2 (ALWAYS_ON_TREND), B (ORIGINAL_V2_MAPPING
on cached regimes, V2 mechanics) with the SPECIALIST REGISTRY engine (V2
specs registered) and compares every stored V2 tier-1 total to <1e-6.

This reproduces ALREADY-OBSERVED V2 numbers (V2 is TERMINAL; nothing here
is a new outcome) — it exists to prove the registry engine did not drift
the V2 math BEFORE any candidate (arm C/D/E/F) outcome can exist.

Exit 0 only if all 3 cells x 3 arms x 6 totals match.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CYCLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CYCLE_DIR))

from rsmv1.engine import CostModel, constant_targets, targets_from_regime  # noqa: E402
from rsmv1.freezes import Freezes  # noqa: E402
from rsmv1.regime_timeline import rebuild_cell_timeline  # noqa: E402
from rsmv1.specialist_engine import SpecialistEngine, v2_equivalence_specs  # noqa: E402
from rsmv1.strategies import FLAT, MR_LONG, TREND_LONG  # noqa: E402
from rsmv1.attribution import _iso_ns  # noqa: E402
from rsmv1.engine import folds_from_regime_ts, fold_partition_invariants  # noqa: E402

V2_LEDGERS = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/jev-regime-router-v2/"
    "integration/research/control/jev_regime_router_v2/runtime/scored"
)
TOL = 1e-6
EQUIV_SCHEMA = "rsmv1_engine_equivalence@1"


def _context(fz: Freezes, ct):
    exec_bars = ct.exec_bars
    spans = [
        (_iso_ns(sp["start"]), _iso_ns(sp["end"]))
        for sp in fz.fold_contract["cells"][ct.cell]["folds"]
    ]
    folds_exec = folds_from_regime_ts(exec_bars, spans)
    first_decision_ts = int(ct.regime_bars.ts_close[fz.warmup(ct.cell)])
    first_required = next(
        (i for i, t in enumerate(exec_bars.ts_open.tolist()) if t > first_decision_ts),
        len(exec_bars.ts_close),
    )
    fold_partition_invariants(folds_exec, len(exec_bars.ts_close), first_required)
    costs = json.loads((CYCLE_DIR / "freezes" / "mapping_arms_freeze.json").read_text())["costs"]
    if ct.cell.startswith("BTC"):
        c = costs["BTCUSDT"]
        cm = CostModel(c["taker_fee_bps_per_side"], c["slippage_bps_per_side"],
                       c["funding_per_8h_signed"], "BTC")
    else:
        c = costs["SPY"]
        cm = CostModel(c["cost_bps_per_fill"], 0.0, 0.0, "SPY")
    return exec_bars, folds_exec, cm


def run_cell(cell: str) -> dict:
    fz = Freezes(CYCLE_DIR)
    ct = rebuild_cell_timeline(CYCLE_DIR, cell)
    exec_bars, folds_exec, cm = _context(fz, ct)
    specs = v2_equivalence_specs()
    mapping_raw = json.loads(
        (CYCLE_DIR / "freezes" / "mapping_arms_freeze.json").read_text()
    )["mapping"]
    asset = "BTCUSDT" if cell.startswith("BTC") else "SPY"
    mapping = {k: v[asset] for k, v in mapping_raw.items()}

    arms = {
        "ALWAYS_ON_MEAN_REVERSION": constant_targets(len(exec_bars.ts_close), MR_LONG),
        "ALWAYS_ON_TREND": constant_targets(len(exec_bars.ts_close), TREND_LONG),
        "JEV_ONLY_ROUTER": targets_from_regime(
            exec_bars, ct.ts, ct.persisted, ct.period_ns, mapping
        ),
    }
    out = {"cell": cell, "arms": {}, "all_match": True}
    for arm, targets in arms.items():
        eng = SpecialistEngine(exec_bars, targets, folds_exec, cm, specs)
        res = eng.run()
        stored = json.loads(
            (V2_LEDGERS / cell / arm / "tier_1.json").read_text()
        )["totals"]
        cmp = {
            "gross": (res.totals["gross_pnl"], stored["gross_pnl"]),
            "fee": (res.totals["costs_fee"], stored["costs_fee"]),
            "slip": (res.totals["costs_slip"], stored["costs_slip"]),
            "funding": (res.totals["costs_funding"], stored["costs_funding"]),
            "net": (res.totals["net_pnl"], stored["net_pnl"]),
            "trades": (res.totals["trades"], stored["trades"]),
        }
        match = all(
            (a == b) if k == "trades" else abs(a - b) < TOL
            for k, (a, b) in cmp.items()
        )
        out["arms"][arm] = {
            "comparisons": {k: [round(a, 6), round(b, 6)] for k, (a, b) in cmp.items()},
            "match": match,
        }
        out["all_match"] = out["all_match"] and match
    return out


def main() -> int:
    bundle = {"schema": EQUIV_SCHEMA, "cells": {}, "all_match": True,
              "tolerance": TOL,
              "note": "reproduces TERMINAL V2 stored outcomes; not new results"}
    for cell in ("BTC_H1", "BTC_H4", "SPY_D1"):
        blk = run_cell(cell)
        bundle["cells"][cell] = blk
        bundle["all_match"] = bundle["all_match"] and blk["all_match"]
        print(f"{cell}: {'MATCH' if blk['all_match'] else 'MISMATCH'}")
    out = CYCLE_DIR / "evidence" / "engine_equivalence.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=1, sort_keys=True))
    print("all_match:", bundle["all_match"], "->", out)
    return 0 if bundle["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
