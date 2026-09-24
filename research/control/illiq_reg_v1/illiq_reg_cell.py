"""One gated ILLIQ-REG-V1 cell in its own process (package isolation).

Mirrors illiq_cell_runner.py wiring exactly (catalog bars -125d/+3d, per-fold
funding scan, tick sizes 1e-07, Chr3fIlliqPlugin fold law) and adds ONLY the
plan-frozen gate suppression (IlliqRegGatedPlugin) and the plan SS7 stress
spec. run_strategy does everything else with the frozen engine.

Runs INSIDE the heavy lock acquired by phase1_sweep.py; refuses without it.
stdout: one summary JSON line. Artifact: <out>/results/artifact.json.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))

import wiring  # noqa: E402

V11_ROOT = wiring.CHR3F_CTRL / "recovered" / "v11_root"
for p in (str(V11_ROOT), str(wiring.CHR3F_CTRL)):
    if p not in sys.path:
        sys.path.insert(0, p)

from research.hyp_a8_m01 import read_bars_15m  # noqa: E402
from research.adapter_v10.protocol import SettlementPoint, StressSpec  # noqa: E402
from research.adapter_v10.runner import run_strategy  # noqa: E402
from research.adapter_v10.stress import build_stress_spec  # noqa: E402
from gated_plugin import IlliqRegGatedPlugin  # noqa: E402

ARMS = {"ANCHOR": "ILLIQ-AMIHUD-28D-W", "INV": "ILLIQ-AMIHUD-28D-W-INV"}
FOLD = "S0R"


def stress_spec_for(kind: str, plugin: IlliqRegGatedPlugin) -> StressSpec:
    base = plugin.baseline_stress()
    if kind == "baseline":
        return base
    if kind == "fee_x1_5":
        return build_stress_spec("fee_slippage_x1_5", strategy_baseline=base)
    if kind == "fee_x2_0":
        # plan SS7 s2: taker fee x2.0, slip floor +1 tick kept, no delay —
        # pure parameter change over the plugin's own baseline floors,
        # preregistered (PREREG stress.s2, plan SS7).
        return dataclasses.replace(base, name="fee_x2_0_prereg",
                                   fee_multiplier=2.0)
    raise wiring.WiringError(f"unknown stress {kind!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell-id", required=True)
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--stress", required=True,
                    choices=["baseline", "fee_x1_5", "fee_x2_0"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--gate-series", default=str(HERE / "gate_series.json"))
    args = ap.parse_args()

    lock_path = Path("/Users/hoangminhlong/.my-quantitative-governance/"
                     "heavy_runtime/heavy_worker.lock")
    if not lock_path.exists():
        raise wiring.WiringError(
            "REFUSED: heavy lock not held — cells run only under the sweep")

    doc = json.loads(Path(args.gate_series).read_text())
    if doc.get("schema") != "illiq_reg_v1.gate_series@1":
        raise wiring.WiringError("gate_series schema mismatch")
    by_date = {}
    for row in doc["folds"][FOLD]["per_day"]:
        if not row["is_stamp"]:
            continue
        if not row["data_complete"]:
            raise wiring.WiringError(f"incomplete stamp {row['date']}")
        by_date[row["date"]] = bool(row["gated"])

    w0, w1 = wiring.FOLD_WINDOWS[FOLD]
    pre_iso, ext_iso = wiring.bars_load_bounds(w0, w1)
    catalog = wiring.FOLD_WIRING[FOLD]["catalog"]
    scan = wiring.FOLD_WIRING[FOLD]["funding_scan"]
    wiring.verify_funding_scan_coverage(scan, wiring.SYMS, w0, w1)

    bars = {s: read_bars_15m(catalog, s, pre_iso, ext_iso) for s in wiring.SYMS}
    settles = {}
    for sym in wiring.SYMS:
        d = json.loads((scan / sym / "funding.json").read_text())
        pts = [SettlementPoint(publish_ts_ns=int(r["fundingTime"]) * 1_000_000,
                               value=float(r["fundingRate"]), kind="info")
               for r in d["rows"]]
        pts.sort(key=lambda p: p.publish_ts_ns)
        settles[sym] = tuple(pts)

    plugin = IlliqRegGatedPlugin(
        bars_by_symbol=bars, arm_id=ARMS[args.arm],
        tick_sizes={s: 1e-07 for s in wiring.SYMS},
        settle_points_by_symbol=settles,
        window_start_iso=w0, window_end_iso=w1)
    plugin.bind_window((w0, w1))
    gate_ns = {int(ns): by_date[dt.datetime.fromtimestamp(
                   int(ns) / 1e9, dt.timezone.utc).date().isoformat()]
               for ns in plugin.schedule().instants}
    plugin.bind_gate(gate_ns)
    spec = stress_spec_for(args.stress, plugin)

    payload = run_strategy(plugin, out_dir=args.out, stress=spec,
                           write_artifact_file=True)
    m = payload.get("portfolio_metrics") or {}
    labels = wiring.labels_for_row(FOLD, wiring.scan_id_for_fold(FOLD))
    wiring.validate_labels(labels)
    summary = {
        "cell_id": args.cell_id, "arm": args.arm, "arm_id": ARMS[args.arm],
        "stress": spec.name, "stress_signature": spec.signature(),
        "fold": FOLD, "window": [w0, w1], "labels": labels,
        "gate_counts": plugin.gate_counts(),
        "net_return_sum": m.get("net_return_sum"),
        "max_drawdown": m.get("max_drawdown"),
        "position_pf": m.get("position_pf"),
        "n_positions": m.get("n_positions"),
        "funding_sum": m.get("funding_sum"),
        "artifact_dir": args.out,
        "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
