"""ILLIQ-REG-V1 phase-1 scored sweep (plan SS8/§10.7; post-GO only).

4 cells on the S0R falsification surface, all `scored=False` diagnostics in
namespace REPLICATION_NOT_PROSPECTIVE, each counting one budget unit
(registry cap 4):

  P1-C1  ANCHOR (ILLIQ-AMIHUD-28D-W)      baseline     <- falsification cell
  P1-C2  ANCHOR                            fee x1.5     (frozen named cell)
  P1-C3  ANCHOR                            fee x2.0     (prereg spec, SS7)
  P1-C4  INV    (ILLIQ-AMIHUD-28D-W-INV)   baseline     (causal control)

Refuses to run unless ALL hold (fail-closed):
  - A7 prelaunch verdict == AUTHORIZED (first key);
  - AUTH/GO_RECORDED.json exists with the registered phrase (second key);
  - registry lifecycle == ACTIVE_HEAVY (consumption recorded);
  - gate_series.json digest == the audited digest;
  - S0R funding coverage re-verified (scan_2026_a, 20/20);
  - budget used 0/4.
The machine-wide heavy lock is held for the whole sweep; bars and funding
are loaded ONCE and shared; the frozen engine is never modified; per-fold
funding law (S0R -> scan_2026_a) and bars load-end +3d are enforced by
wiring.py exactly as audited (A7 SS5).
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))

import gated_plugin  # noqa: E402
import wiring  # noqa: E402
from gate_module import falsification_verdict  # noqa: E402

R = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(R))
from research.governance import heavy_lock  # noqa: E402

V11_ROOT = wiring.CHR3F_CTRL / "recovered" / "v11_root"
for p in (str(V11_ROOT), str(wiring.CHR3F_CTRL), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from research.hyp_a8_m01 import read_bars_15m  # noqa: E402
from research.adapter_v10.protocol import SettlementPoint, StressSpec  # noqa: E402
from research.adapter_v10.runner import run_strategy  # noqa: E402
from research.adapter_v10.stress import build_stress_spec  # noqa: E402
from gated_plugin import IlliqRegGatedPlugin  # noqa: E402

CYCLE = "ILLIQ-REG-V1"
FOLD = "S0R"
FALSIFICATION_CELL = "P1-C1"
AUDITED_GATE_SERIES_SHA256 = ("e09187f925e761cfabe94e0766ca2104b3b45f5def76f"
                              "adc061cdbc09c51702d")
REGISTERED_PHRASE = "GO ILLIQ REG V1 SCORED EXECUTION"

ARMS = {"ANCHOR": "ILLIQ-AMIHUD-28D-W", "INV": "ILLIQ-AMIHUD-28D-W-INV"}
CELLS = [("P1-C1", "ANCHOR", "baseline"),
         ("P1-C2", "ANCHOR", "fee_x1_5"),
         ("P1-C3", "ANCHOR", "fee_x2_0"),
         ("P1-C4", "INV", "baseline")]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def preconditions() -> dict:
    a7_path = HERE / "a7_prelaunch" / "a7_prelaunch_illiq_reg_v1.json"
    a7 = json.loads(a7_path.read_text())
    if a7.get("verdict") != "AUTHORIZED":
        raise wiring.WiringError(f"REFUSED: A7 verdict {a7.get('verdict')!r}")
    go = json.loads((HERE / "AUTH" / "GO_RECORDED.json").read_text())
    if go.get("go_phrase") != REGISTERED_PHRASE:
        raise wiring.WiringError("REFUSED: GO record phrase mismatch")
    if not go.get("received_after_a7_prelaunch") or not go.get(
            "registered_phrase_matches"):
        raise wiring.WiringError("REFUSED: GO record incomplete")
    gs_bytes = (HERE / "gate_series.json").read_bytes()
    if sha256_bytes(gs_bytes) != AUDITED_GATE_SERIES_SHA256:
        raise wiring.WiringError("REFUSED: gate_series digest != audited digest")
    reg = json.loads((R / "plans" / "CYCLE_REGISTRY.json").read_text())
    row = next(c for c in reg["cycles"] if c["cycle_id"] == CYCLE)
    if row.get("lifecycle") != "ACTIVE_HEAVY":
        raise wiring.WiringError(
            f"REFUSED: registry lifecycle {row.get('lifecycle')!r} != "
            "ACTIVE_HEAVY (GO consumption not recorded)")
    w0, w1 = wiring.FOLD_WINDOWS[FOLD]
    wiring.verify_funding_scan_coverage(
        wiring.FOLD_WIRING[FOLD]["funding_scan"], wiring.SYMS, w0, w1)
    budget = row.get("budget") or {}
    budget_used = int(budget.get("used", 0))
    budget_max = int(budget.get("max", 4))
    if budget_used != 0 or budget_max < 4:
        raise wiring.WiringError(
            f"REFUSED: budget {budget_used}/{budget_max} != 0/4")
    return {"a7": a7, "go": True, "gate_series_sha256":
            sha256_bytes(gs_bytes), "registry_lifecycle": row["lifecycle"],
            "budget": f"{budget_used}/{budget_max}"}


def gate_stamp_map(gate_series_path: Path) -> dict[int, bool]:
    doc = json.loads(gate_series_path.read_text())
    if doc.get("schema") != "illiq_reg_v1.gate_series@1":
        raise wiring.WiringError("gate_series schema mismatch")
    fold = doc["folds"][FOLD]
    by_date = {}
    for row in fold["per_day"]:
        if not row["is_stamp"]:
            continue
        if not row["data_complete"]:
            raise wiring.WiringError(f"incomplete stamp {row['date']}")
        by_date[row["date"]] = bool(row["gated"])
    return by_date


def stress_spec_for(kind: str, plugin: IlliqRegGatedPlugin) -> StressSpec:
    base = plugin.baseline_stress()
    if kind == "baseline":
        return base
    if kind == "fee_x1_5":
        return build_stress_spec("fee_slippage_x1_5", strategy_baseline=base)
    if kind == "fee_x2_0":
        # plan SS7 s2: taker fee x2.0, slip floor +1 tick kept, no delay —
        # a pure parameter change over the plugin's own baseline floors,
        # preregistered in the PREREG draft (stress.s2) and plan SS7.
        return dataclasses.replace(base, name="fee_x2_0_prereg",
                                   fee_multiplier=2.0)
    raise wiring.WiringError(f"unknown stress {kind!r}")


def main() -> int:
    pre = preconditions()
    print(json.dumps({"preconditions": "OK", **pre}), flush=True)

    gate_by_date = gate_stamp_map(HERE / "gate_series.json")
    w0, w1 = wiring.FOLD_WINDOWS[FOLD]
    pre_iso, ext_iso = wiring.bars_load_bounds(w0, w1)
    catalog = wiring.FOLD_WIRING[FOLD]["catalog"]
    scan = wiring.FOLD_WIRING[FOLD]["funding_scan"]

    bars = {s: read_bars_15m(catalog, s, pre_iso, ext_iso) for s in wiring.SYMS}
    settles = {}
    for sym in wiring.SYMS:
        doc = json.loads((scan / sym / "funding.json").read_text())
        pts = [SettlementPoint(publish_ts_ns=int(r["fundingTime"]) * 1_000_000,
                               value=float(r["fundingRate"]), kind="info")
               for r in doc["rows"]]
        pts.sort(key=lambda p: p.publish_ts_ns)
        settles[sym] = tuple(pts)
    print(json.dumps({"wiring": "OK", "bars_symbols": len(bars),
                      "scan": scan.name}), flush=True)

    handle = heavy_lock.acquire(
        cycle_id=CYCLE, role="scored-cells", worktree=str(HERE.parents[2]),
        command=[sys.executable, str(Path(__file__))],
        expected_artifacts=[str(HERE / "phase1_status.json")])
    cells = []
    try:
        for cell_id, arm_key, stress_kind in CELLS:
            started = dt.datetime.now(dt.timezone.utc).isoformat()
            plugin = IlliqRegGatedPlugin(
                bars_by_symbol=bars, arm_id=ARMS[arm_key],
                tick_sizes={s: 1e-07 for s in wiring.SYMS},
                settle_points_by_symbol=settles,
                window_start_iso=w0, window_end_iso=w1)
            plugin.bind_window((w0, w1))
            stamp_ns = {int(ns): gate_by_date[
                            dt.datetime.fromtimestamp(int(ns) / 1e9,
                                                      dt.timezone.utc).date()]
                        for ns in plugin.schedule().instants}
            plugin.bind_gate(stamp_ns)
            spec = stress_spec_for(stress_kind, plugin)
            out_dir = HERE / "phase1" / cell_id
            payload = run_strategy(plugin, out_dir=str(out_dir),
                                   stress=spec, write_artifact_file=True)
            m = payload.get("portfolio_metrics") or {}
            gc = plugin.gate_counts()
            labels = wiring.labels_for_row(FOLD, wiring.scan_id_for_fold(FOLD))
            wiring.validate_labels(labels)
            cell = {
                "cell_id": cell_id, "arm": arm_key, "arm_id": ARMS[arm_key],
                "stress": spec.name,
                "stress_signature": spec.signature(),
                "fold": FOLD, "window": [w0, w1],
                "labels": labels,
                "gate_counts": gc,
                "net_return_sum": m.get("net_return_sum"),
                "max_drawdown": m.get("max_drawdown"),
                "position_pf": m.get("position_pf"),
                "n_positions": m.get("n_positions"),
                "funding_sum": m.get("funding_sum"),
                "artifact_dir": str(out_dir),
                "started_utc": started,
                "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            }
            cells.append(cell)
            print(json.dumps({"cell": cell_id, "stress": spec.name,
                              "net_return_sum": m.get("net_return_sum"),
                              "max_drawdown": m.get("max_drawdown"),
                              "position_pf": m.get("position_pf"),
                              "n_positions": m.get("n_positions"),
                              **gc}), flush=True)
            status_path = HERE / "phase1_status.json"
            status_path.write_text(json.dumps(
                {"cycle_id": CYCLE, "fold": FOLD, "cells": cells}, indent=1))
    finally:
        heavy_lock.release(handle)

    base_cell = next(c for c in cells if c["cell_id"] == FALSIFICATION_CELL)
    verdict = falsification_verdict(base_cell["net_return_sum"],
                                    base_cell["max_drawdown"])
    inv_cell = next(c for c in cells if c["arm"] == "INV"
                    and c["stress"] == "baseline")
    doc = {
        "schema": "illiq_reg_v1.phase1_verdict@1",
        "cycle_id": CYCLE,
        "fold": FOLD,
        "falsification_cell": FALSIFICATION_CELL,
        "labels_base_cell": base_cell["labels"],
        "verdict": verdict,
        "inv_coherence": {
            "inv_gated_net_sum": inv_cell["net_return_sum"],
            "note": "plan SS7: on a losing anchor window INV-gated is "
                    "expected positive; sign reported, not a rescue path",
        },
        "cells": cells,
        "budget_used": f"{len(cells)}/4",
        "phase_2": "NOT AUTHORIZED — owner amendment required (plan SS8)",
        "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    (HERE / "phase1_verdict.json").write_text(json.dumps(doc, indent=1))
    print(json.dumps({"verdict": verdict["verdict"],
                      "net_margin": verdict["net_margin"],
                      "mdd_margin": verdict["mdd_margin"],
                      "inv_gated_net_sum": inv_cell["net_return_sum"]}),
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
