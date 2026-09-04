"""A7T terminal-audit book-level recompute for STOCKS-FREE-V5 (read-only).

Re-derives each scored arm's frozen schedule/book through the FROZEN W1 code
in the detached r-reproduce twin (never this worktree's code) and re-values
the book at base/stress/drop-one costs, then verifies the money arithmetic
that the canonical artifact only summarizes:

  * every per-fill cost == equity * etf_leg_turnover * cost_bps / 1e4
    (10 bps base; 20 bps stress);
  * total_cost == fsum(per-fill costs) (charged exactly once);
  * assert_reconciles (attribution identity + cost accumulator);
  * schedule_turnover_two_way_per_year == 2 * sum(one_way) / (n_sessions/252);
  * drop-one symbol selection == the recorded dropped symbol;
  * base/stress/drop-one totals equal the committed cell payload values.

The sealed S0 snapshot is read from the pinned read-only staging root.
NO file under either worktree is written; stdout is a JSON report.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CELLS = REPO / "research" / "control" / "stocks_free_v5_run" / "cells"
ARMS = ["A", "N", "C"]
STRESS_COST_BPS = 20.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--twin", required=True,
                    help="r-reproduce worktree root (frozen W1 code)")
    ap.add_argument("--staging", required=True,
                    help="sealed read-only S0 snapshot root (MANIFEST 62ac324d...)")
    args = ap.parse_args()

    twin = Path(args.twin).resolve()
    sys.path.insert(0, str(twin))
    from research.assets.stocks.factory import (
        value_book, normalize_entry_targets, select_drop_one_symbol)
    from research.assets.stocks.coupling_family import (
        Panel, SECTOR_SYMBOLS, build_arm_configs, book_entries_walk,
        build_arm_schedule_walk)

    staging = Path(args.staging)
    S1_START = "2025-08-01"
    adjusted, raw = {}, {}
    for sym in ["SPY"] + list(SECTOR_SYMBOLS):
        ac, rc = {}, {}
        for row in json.loads((staging / f"{sym}_all_p1.json").read_text())["values"]:
            d = row["datetime"]
            if d < S1_START:
                ac[d] = float(row["close"])
        adjusted[sym] = ac
        if sym != "SPY":
            for row in json.loads((staging / f"{sym}_none_p1.json").read_text())["values"]:
                d = row["datetime"]
                if d < S1_START:
                    rc[d] = float(row["close"])
            raw[sym] = rc
    sessions = sorted(adjusted["SPY"])
    assert sessions[-1] < S1_START, "S1 leak in staging load"

    per_arm = {}
    for arm_key in ARMS:
        arm_id = f"SFV5-A6-H2-{arm_key}"
        cell = json.loads((CELLS / f"{arm_id}.json").read_text())
        arm = build_arm_configs()[arm_key]
        panel = Panel({s: adjusted[s] for s in adjusted},
                      {s: raw.get(s, {}) for s in SECTOR_SYMBOLS})
        presence = {s: {d for d in raw.get(s, {})} for s in SECTOR_SYMBOLS}
        sched = build_arm_schedule_walk(arm, sessions)
        entries = book_entries_walk(arm, panel, sessions, sched, presence)
        entries.sort(key=lambda x: x["fill_date"])

        base = value_book(entries, adjusted, {}, {}, sessions, cost_bps=10.0)
        stress = value_book(entries, adjusted, {}, {}, sessions, cost_bps=STRESS_COST_BPS)
        held_weights = {}
        for e in entries:
            if e.get("entry_type") == "FORCE_FLAT":
                continue
            targets, _ = normalize_entry_targets(e)
            for s, w in targets.items():
                if s != "CASH":
                    held_weights[s] = max(held_weights.get(s, 0.0), abs(w))
        dropped = select_drop_one_symbol(dict(base.symbol_contribution), held_weights)
        drop = value_book(entries, adjusted, {}, {}, sessions, cost_bps=10.0,
                          excluded_symbol=dropped)

        n_years = len(sessions) / 252.0
        one_way = sum(t for _, t, _ in base.fill_costs)
        turnover = one_way * 2.0 / n_years

        # Per-fill cost verification.  value_book charges cost = equity_at_fill
        # * turnover * bps / 1e4 and curve[d] records equity AFTER the charge,
        # so equity_at_fill = curve[d] + cost; verify the documented identity
        # c == (curve[d] + c) * t * bps / 1e4 per fill.
        curve = base.equity_curve
        per_fill_checks = [
            abs(c - (curve[d] + c) * t * cell["cost_bps_base"] / 1e4)
            <= 1e-12 * max(1.0, abs(c))
            for d, t, c in base.fill_costs]
        stress_per_fill_checks = [
            abs(c - (stress.equity_curve[d] + c) * t * STRESS_COST_BPS / 1e4)
            <= 1e-12 * max(1.0, abs(c))
            for d, t, c in stress.fill_costs]

        per_arm[arm_id] = {
            "n_fills": len(base.fill_costs),
            "total_cost_equals_fsum_fill_costs": abs(
                base.total_cost - math.fsum(c for _, _, c in base.fill_costs)) <= 1e-12,
            "per_fill_cost_formula_10bps_all_ok": all(per_fill_checks),
            "stress_total_cost_equals_fsum_fill_costs": abs(
                stress.total_cost - math.fsum(c for _, _, c in stress.fill_costs)) <= 1e-12,
            "per_fill_cost_formula_20bps_stress_all_ok": all(stress_per_fill_checks),
            "stress_costs_double_bps_ratio": stress.total_cost / base.total_cost,
            "reconciles_base_raises_none": _safe_reconciles(base),
            "reconciles_stress_raises_none": _safe_reconciles(stress),
            "reconciles_drop_raises_none": _safe_reconciles(drop),
            "turnover_formula_matches_recorded": abs(
                turnover - cell["schedule_turnover_two_way_per_year"]) <= 1e-12,
            "base_total_pnl_matches_cell": base.total_pnl == cell["base"]["total_pnl"],
            "stress_total_pnl_matches_cell": stress.total_pnl == cell["stress"]["total_pnl"],
            "drop_total_pnl_matches_cell": drop.total_pnl == cell["drop_one_etf"]["total_pnl"],
            "dropped_symbol_matches_cell": dropped == cell["drop_one_etf"]["dropped_symbol"],
            "equity_curve_matches_cell": base.equity_curve == cell["base"]["equity_curve"],
        }

    report = {"twin": str(twin), "staging": str(args.staging),
              "per_arm": per_arm,
              "ok": all(all(v for k, v in a.items() if k != "stress_costs_double_bps_ratio")
                        for a in per_arm.values())}
    print(json.dumps(report, indent=1))
    return 0


def _safe_reconciles(result) -> bool:
    from research.assets.stocks.factory import assert_reconciles
    try:
        assert_reconciles(result)
        return True
    except Exception as exc:  # noqa: BLE001 - audit records any failure
        return f"RAISED: {exc}"


if __name__ == "__main__":
    sys.exit(main())
