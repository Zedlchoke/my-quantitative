"""ILLIQ-REG-V1 sanitized dry-run (A7 prelaunch step; NO PnL surfaces).

Traverses the GATED strategy over the S0R fold without emitting any PnL:
for each frozen Monday 00:00:00Z stamp the gate state is read from
gate_series.json (produced by full_build under the heavy lock) and, when
GATED, the plugin's universe/targets_at is evaluated STATUS ONLY. Gated-OFF
stamps return the same skip semantics as frozen MIN_ELIGIBLE skips — status
skip with reason_code GATE_OFF. NO orders, fills, equity, positions, costs,
funding cashflows or returns are computed or serialized anywhere (the v10
runner is never called).

The gated variant introduces NO new fill logic: it only suppresses book
formation at GATE_OFF stamps, exactly like the engine's own skip statuses.

Non-vacuous gate: the report asserts >= 1 stamp GATED ON with a
constructible book AND >= 1 stamp GATED OFF; counts are reported either way.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # never drop __pycache__ into READ-ONLY trees
sys.path.insert(0, str(HERE))

import wiring  # noqa: E402

V11_ROOT = wiring.CHR3F_CTRL / "recovered" / "v11_root"
sys.path.insert(0, str(V11_ROOT))
sys.path.insert(0, str(wiring.CHR3F_CTRL))

from research.hyp_a8_m01 import read_bars_15m  # noqa: E402
from research.adapter_v10.protocol import SettlementPoint, StressSpec  # noqa: E402
from chr3f_illiq_plugin import Chr3fIlliqPlugin  # noqa: E402
from research.v11.families.illiq_amihud.strategy import (  # noqa: E402
    STATUS_OK, STATUS_SKIP,
)

FOLD = "S0R"
DEFAULT_ARM = "ILLIQ-AMIHUD-28D-W"   # PREREG arms.anchor_gated
GATE_OFF_REASON = "GATE_OFF"

# Substrings that must NEVER appear as a key in the sanitized report.
PNL_KEY_SUBSTRINGS = ("pnl", "net_return", "gross_return", "equity",
                      "position", "fill", "cost", "fee", "slippage",
                      "drawdown", "cashflow", "order")
SENTINEL_KEY = "no_pnl_fields"


def _iso(date: dt.date) -> str:
    return date.isoformat()


def _gate_states(gate_series_path: Path) -> dict[str, dict]:
    doc = json.loads(gate_series_path.read_text())
    if doc.get("schema") != "illiq_reg_v1.gate_series@1":
        raise wiring.WiringError(
            f"{gate_series_path}: unexpected schema {doc.get('schema')!r}")
    fold = doc["folds"][FOLD]
    stamps = {}
    for row in fold["per_day"]:
        if not row["is_stamp"]:
            continue
        if not row["data_complete"]:
            raise wiring.WiringError(
                f"{FOLD} stamp {row['date']} data_incomplete in gate series "
                "— wired fold must be complete (fail-closed)")
        stamps[row["date"]] = {
            "gated": bool(row["gated"]),
            "v1_state": bool(row["v1_state"]),
            "v2_state": bool(row["v2_state"]),
        }
    return stamps


def _load_settlements(scan_root: Path) -> dict[str, tuple]:
    out = {}
    for sym in wiring.SYMS:
        doc = json.loads((scan_root / sym / "funding.json").read_text())
        pts = [SettlementPoint(publish_ts_ns=int(r["fundingTime"]) * 1_000_000,
                               value=float(r["fundingRate"]), kind="info")
               for r in doc["rows"]]
        pts.sort(key=lambda p: p.publish_ts_ns)
        out[sym] = tuple(pts)
    return out


def _assert_no_pnl_fields(report: dict) -> bool:
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                key = str(k).lower()
                if key == SENTINEL_KEY:
                    continue
                if any(s in key for s in PNL_KEY_SUBSTRINGS):
                    raise wiring.WiringError(
                        f"sanitized report leaked PnL-adjacent key {k!r}")
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(report)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default=DEFAULT_ARM)
    ap.add_argument("--gate-series", default=str(HERE / "gate_series.json"))
    ap.add_argument("--out", default=str(HERE / "dryrun_report.json"))
    args = ap.parse_args()

    gate_series_path = Path(args.gate_series)
    if not gate_series_path.exists():
        raise wiring.WiringError(
            f"gate series missing: {gate_series_path} — run the full build "
            "under the heavy lock first (full_build_locked.py)")
    import gate_module as gm
    gates = _gate_states(gate_series_path)

    # --- wire the frozen engine exactly like the CHR3F cell runner ----------
    w0, w1 = wiring.FOLD_WINDOWS[FOLD]
    pre_iso, ext_iso = wiring.bars_load_bounds(w0, w1)
    catalog = wiring.FOLD_WIRING[FOLD]["catalog"]
    scan = wiring.FOLD_WIRING[FOLD]["funding_scan"]
    bars = {s: read_bars_15m(catalog, s, pre_iso, ext_iso)
            for s in wiring.SYMS}
    settles = _load_settlements(scan)
    plugin = Chr3fIlliqPlugin(
        bars_by_symbol=bars, arm_id=args.arm,
        tick_sizes={s: 1e-07 for s in wiring.SYMS},
        settle_points_by_symbol=settles,
        window_start_iso=w0, window_end_iso=w1)
    plugin.bind_window((w0, w1))
    stress = StressSpec(name="baseline")

    # frozen schedule must equal the gate-series stamp set (fail-closed)
    schedule_dates = [_iso(dt.datetime.fromtimestamp(ns / 1e9,
                                                    dt.timezone.utc).date())
                      for ns in plugin.schedule().instants]
    if sorted(schedule_dates) != sorted(gates):
        raise wiring.WiringError(
            "frozen schedule stamps differ from gate-series stamps: "
            f"{len(schedule_dates)} vs {len(gates)}")
    universe = plugin.universe(stress)

    # --- sanitized traversal: STATUS ONLY, never run_strategy ---------------
    per_stamp = []
    gated_on = gated_off = skip_other = gated_on_with_book = 0
    for ns in plugin.schedule().instants:
        iso = _iso(dt.datetime.fromtimestamp(ns / 1e9,
                                             dt.timezone.utc).date())
        if not gates[iso]["gated"]:
            status, reason, book = STATUS_SKIP, GATE_OFF_REASON, False
            gated_off += 1
        else:
            gated_on += 1
            res = plugin.targets_at(int(ns), universe=universe, stress=stress)
            status = str(res["status"])
            reason = res.get("reason_code")
            book = bool(status == STATUS_OK and res.get("weights"))
            if status == STATUS_SKIP:
                skip_other += 1
            elif book:
                gated_on_with_book += 1
        per_stamp.append({"stamp": iso, "gated": gates[iso]["gated"],
                          "status": status, "reason_code": reason,
                          "book_constructed": book})

    non_vacuous = gated_on_with_book >= 1 and gated_off >= 1
    labels = wiring.labels_for_row(FOLD, wiring.scan_id_for_fold(FOLD))
    wiring.validate_labels(labels)
    report = {
        "schema": "illiq_reg_v1.dryrun_report@1",
        "cycle_id": gm.CYCLE_ID,
        "fold": FOLD,
        "window": [w0, w1],
        "arm": args.arm,
        "gate_series": str(gate_series_path.name),
        "gate_series_sha256": __import__("hashlib").sha256(
            gate_series_path.read_bytes()).hexdigest(),
        "gate_module_sha256": __import__("hashlib").sha256(
            (HERE / "gate_module.py").read_bytes()).hexdigest(),
        "labels": labels,
        "stamps_total": len(per_stamp),
        "gated_on": gated_on,
        "gated_off": gated_off,
        "skip_other": skip_other,
        "gated_on_with_book": gated_on_with_book,
        "non_vacuous": non_vacuous,
        "no_pnl_fields": True,
        "per_stamp": per_stamp,
    }
    report["no_pnl_fields"] = _assert_no_pnl_fields(report)
    Path(args.out).write_text(json.dumps(report, indent=1, sort_keys=True))
    print(json.dumps({k: report[k] for k in (
        "stamps_total", "gated_on", "gated_off", "skip_other",
        "gated_on_with_book", "non_vacuous", "no_pnl_fields")}))
    return 0 if non_vacuous else 1


if __name__ == "__main__":
    raise SystemExit(main())
