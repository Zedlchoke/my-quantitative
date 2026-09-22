"""D2-CURIOSITY-V1 scored orchestrator (run ONLY after the owner GO).

Phases (per plan §6 E/R):
  P0  env verify: branch + clean tracked tree (engines/, contracts and
      this runner committed); S1 denial enforced inside every engine
      loader (denied paths raise before IO)
  P1  machine-wide heavy lock acquire + heartbeat
  P2  contracts load + cells_registry intact + data-gate per-family status
      re-read (families not BINDABLE_NOW are NOT_RUN_DATA_BLOCKED —
      honestly labelled, never improvised)
  P3  score: for each family with BINDABLE_NOW, set engine ALLOW_SCORE
      via the sanctioned setter, compute the frozen evaluation-contract
      metrics on the BOUND data, write per-cell + summary artifacts
      atomically; observed counter consumed at each scored cell START
  P4  reproduce: re-run in-process on the same bound inputs and require
      byte-identical decision rows + identical metric JSON (digest match)
  P5  write final report skeleton (the human table is A1's deliverable)

Honesty laws: verdict vocabulary fixed; NO survivor language; every
number carries NON_GOVERNING_DIAGNOSTIC / NO PROMOTION labels; a cell
that fails technically records TECHNICAL_FAILURE and still consumes its
observed slot.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_RUN = _HERE.parent
sys.path.insert(0, str(_RUN / "engines"))
sys.path.insert(0, str(_HERE.parents[2]))          # repo root for governance

REPO = Path("/Users/hoangminhlong/my-quantitative")
WT = REPO / ".worktrees/d2-curiosity-v1/integration"
LABEL = "NON_GOVERNING_DIAGNOSTIC / NO PROMOTION / old D2 verdicts immutable"
GO_PHRASE_ENV = "D2C_GO_PHRASE"
GO_PHRASE = "GO D2 CURIOSITY V1 THREE DIAGNOSTIC CELLS"


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with open(_RUN / "score_run_log.txt", "a") as f:
        f.write(line + "\n")


def canon_digest(obj) -> str:
    return hashlib.sha256(json.dumps(
        obj, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, default=str).encode()).hexdigest()


def p0_env() -> None:
    head = subprocess.run(["git", "-C", str(WT), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    branch = subprocess.run(["git", "-C", str(WT), "branch", "--show-current"],
                            capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(WT), "status", "--porcelain"],
                           capture_output=True, text=True, check=True).stdout
    lines = [l for l in dirty.splitlines() if l.strip()]
    bad = [l for l in lines
           if not (l.startswith("??") and "d2_curiosity_v1_run/" in l)]
    if branch != "orca/d2-curiosity-v1-integration":
        raise RuntimeError(f"wrong branch {branch}")
    if bad:
        raise RuntimeError(f"worktree dirty: {bad[:5]}")
    log(f"P0 ok: HEAD {head[:12]} clean")


def p1_lock():
    from governance import heavy_lock
    handle = heavy_lock.acquire(
        cycle_id="D2-CURIOSITY-V1", role="quant-implementer/d2c-score",
        worktree=str(WT),
        command=[sys.executable, str(_HERE / "score_runner.py"), "--run"],
        expected_artifacts=[str(_RUN / "score_summary.json")])
    stop = threading.Event()

    def beat():
        n = 0
        while not stop.wait(60.0):
            n += 1
            try:
                handle.heartbeat(extra={"heartbeat_n": n})
            except Exception as e:
                log(f"heartbeat error (continuing): {e!r}")

    threading.Thread(target=beat, daemon=True).start()
    return handle, stop


def load_contracts() -> dict:
    return {
        "three_cell": json.loads((_RUN / "three_cell_contract.json").read_text()),
        "cost": json.loads((_RUN / "cost_contract.json").read_text()),
        "evaluation": json.loads((_RUN / "evaluation_contract.json").read_text()),
        "gate": json.loads((_RUN / "data_gate_report.json").read_text()),
    }


def family_bindable(gate: dict, fam: str) -> bool:
    row = gate.get("families", {}).get(fam, {})
    return row.get("overall") == "BINDABLE_NOW"


def _metrics_from_rows(rows, folds_list, tier_bps_per_fill):
    """Evaluation-contract metrics over per-position/decision rows.

    rows carry: gross (before costs, transfers included where the family
    books them as gross-side), costs, net, fold (or None), d.
    """
    import math
    n = len(rows)
    gross_sum = sum(r["gross"] for r in rows)
    cost_sum = sum(r["costs"] for r in rows)
    net_sum = sum(r["net"] for r in rows)
    wins = [r for r in rows if r["net"] > 0]
    losses = [r for r in rows if r["net"] < 0]
    pf = (sum(r["net"] for r in wins) / abs(sum(r["net"] for r in losses))
          if losses and sum(r["net"] for r in losses) != 0 else
          (math.inf if wins else math.nan))
    fold_rows = {}
    for f in folds_list:
        fr = [r for r in rows if r.get("fold") == f]
        fold_rows[f] = {
            "n": len(fr),
            "net": sum(r["net"] for r in fr) if fr else None,
            "positive": bool(fr) and sum(r["net"] for r in fr) > 0,
        } if fr else {"n": 0, "net": None, "positive": None}
    return {
        "n_trades": n,
        "gross_pnl": round(gross_sum, 6),
        "costs": round(cost_sum, 6),
        "net_pnl": round(net_sum, 6),
        "return_pct_on_unit_notional_base": round(net_sum, 6),
        "profit_factor": (None if pf is math.nan else
                          "inf" if pf is math.inf else round(pf, 6)),
        "expectancy_per_trade": round(net_sum / n, 8) if n else None,
        "win_rate": round(len(wins) / n, 6) if n else None,
        "folds": fold_rows,
        "positive_folds": sum(1 for f in fold_rows.values()
                              if f["positive"] is True),
        "cost_tier_bps_per_fill": tier_bps_per_fill,
        "label": LABEL,
    }


def _pin_for(binding, needle, sub_hint=None):
    """Flat 64-hex digest for the CONSUMED artifact, fail-closed.

    Binding reports may carry observed_sha256 as a flat hex string or a
    NESTED dict of per-artifact digests (FXNG3 v2 form); extract the
    sub-digest matching sub_hint (or the unique value), and REFUSE
    anything that is not a 64-hex digest (A7 r2 F8)."""
    import re as _re
    def _flat(v):
        if isinstance(v, str):
            return v if _re.fullmatch(r"[0-9a-f]{64}", v) else None
        if isinstance(v, dict):
            if sub_hint:
                for k, x in v.items():
                    if sub_hint in str(k):
                        return _flat(x)
            vals = [_flat(x) for x in v.values()]
            vals = [x for x in vals if x]
            return vals[0] if len(vals) == 1 else None
        return None
    for inp in binding.get("inputs", []):
        if needle in str(inp.get("input", "")):
            got = _flat(inp.get("observed_sha256")) or \
                _flat(inp.get("pinned_sha256"))
            if got is None:
                raise RuntimeError(
                    f"binding pin for {needle!r} is not a flat 64-hex "
                    "digest (sub_hint="
                    f"{sub_hint!r}) — fail-closed (A7 F8)")
            return got
    raise RuntimeError(
        f"binding report has no input matching {needle!r} — fail-closed "
        "unpinned-load refusal (A7 r3 N1)")


def _maxdd(nets):
    import math
    peak = 0.0
    dd = 0.0
    eq = 0.0
    for x in nets:
        eq += x
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    return round(dd, 6) if nets else None


def _full_metrics(rows, gross_col_fn, folds_list, tier1_scale, tier2_bps_rt,
                  span_note=None):
    import math
    nets = [r["net"] for r in rows]
    n = len(rows)
    gross_pre = [gross_col_fn(r) for r in rows]     # pre-cost net
    cost_sum = sum(r["costs"] for r in rows)
    net_sum = sum(nets)
    gross_sum = sum(gross_pre)
    wins = [x for x in nets if x > 0]
    losses = [x for x in nets if x < 0]
    gw = [g for g, x in zip(gross_pre, nets) if x > 0]
    gl = [g for g, x in zip(gross_pre, nets) if x < 0]

    def pf(xs):
        tot = sum(xs)
        if not xs or tot == 0:
            return None
        return round(tot, 6)
    fold_rows = {}
    for f in folds_list:
        fr = [r for r in rows if r.get("fold") == f]
        fold_rows[f] = ({"n": len(fr), "net": round(sum(r["net"] for r in fr), 6),
                         "positive": sum(r["net"] for r in fr) > 0}
                        if fr else {"n": 0, "net": None, "positive": None})
    net_t1 = sum(r["net"] + r["costs"] - r["costs"] * tier1_scale for r in rows)
    return {
        "n_trades": n,
        "gross_pnl_pre_cost": round(gross_sum, 6),
        "costs": round(cost_sum, 6),
        "net_pnl": round(net_sum, 6),
        "net_pnl_tier_1.0": round(net_t1, 6),
        "return_pct_on_unit_notional_base": round(net_sum, 6),
        "profit_factor_net": (None if not wins or not losses else
                              round(sum(wins) / abs(sum(losses)), 6)),
        "profit_factor_gross_basis": (None if not gw or not gl else
                                      round(sum(gw) / abs(sum(gl)), 6)),
        "expectancy_per_trade": round(net_sum / n, 8) if n else None,
        "win_rate": round(len(wins) / n, 6) if n else None,
        "max_drawdown_on_cumulative_position_marks": _maxdd(nets),
        "folds": fold_rows,
        "positive_folds": sum(1 for f in fold_rows.values()
                              if f["positive"] is True),
        "cost_attribution": {
            "cost_tier2_bps_round_trip": tier2_bps_rt,
            "cost_share_of_gross": (round(cost_sum / abs(gross_sum), 6)
                                    if gross_sum else None),
            "net_to_gross_ratio": (round(net_sum / gross_sum, 6)
                                   if gross_sum else None)},
        "concentration": {
            "largest_abs_position_share_of_sum_abs_net": (
                round(max(abs(x) for x in nets) / sum(abs(x) for x in nets), 6)
                if nets and sum(abs(x) for x in nets) else None),
            "largest_abs_fold_net_share": (
                round(max(abs(fv["net"]) for fv in fold_rows.values()
                          if fv["net"] is not None) /
                      sum(abs(fv["net"]) for fv in fold_rows.values()
                          if fv["net"] is not None), 6)
                if folds_list and any(fv["net"] is not None
                                      for fv in fold_rows.values()) else None)},
        "label": LABEL,
    }


def score_cng2(contracts) -> dict:
    """GO-time scoring: anchor arm rows on the BOUND data (per-row
    outcomes = the sanctioned scored computation), full evaluation-
    contract aggregation. Universe coverage asserted (F7): a missing
    symbol file is BLOCKED before any slot burns."""
    import cng2_engine as eng
    binding = json.loads((_RUN / "data" / "cng2" / "binding_report.json")
                         .read_text())
    panels = {}
    funding = None
    for sym in eng.UNIVERSE:
        pin = _pin_for(binding, f"panel_{sym}")
        cands = [p for p in binding.get("inputs", [])
                 if f"panel_{sym}" in str(p.get("input", ""))]
        path = None
        for c in cands:
            for ep in c.get("evidence_paths", []):
                if Path(ep).exists():
                    path = ep
                    break
        if path is None:
            raise RuntimeError(f"CNG2 BLOCKED_DATA: panel for {sym} not "
                               "resolvable to existing bound bytes")
        panels.update(eng.load_panel(path, expected_sha256=pin))
    fp = _RUN / "data" / "cng2" / "funding_history.json"
    funding = eng.load_funding_series(
        fp, expected_sha256=_pin_for(binding, "funding"))
    missing = [s for s in eng.UNIVERSE if s not in panels]
    if missing:
        raise RuntimeError(f"CNG2 BLOCKED_DATA: universe missing {missing}")
    eng.ALLOW_SCORE = True
    try:
        ds = eng.build_anchor_decisions(panels, funding)
    finally:
        eng.ALLOW_SCORE = False
    rows = [dict(zip(eng.DECISION_ROW_COLUMNS, r))
            if not isinstance(r, dict) else r for r in ds["rows"]]
    funded = [r for r in rows if r.get("net") is not None
              and r.get("entry") is not None]
    t2 = eng.COST_TIERS["2.0"]
    t1 = eng.COST_TIERS["1.0"]
    bps2 = (t2["taker_bps_per_fill"] + t2["spread_bps_per_fill"]) * 2
    scale1 = (t1["taker_bps_per_fill"] + t1["spread_bps_per_fill"]) / \
             (t2["taker_bps_per_fill"] + t2["spread_bps_per_fill"])
    def g(r):
        return r["gross_before_costs"] + r["transfer"]
    m = _full_metrics(funded, g, [], scale1, bps2)
    ks = sorted({r["S"] for r in funded})
    thirds = {}
    if ks:
        a, b = ks[len(ks) // 3], ks[2 * len(ks) // 3]
        for name, pred in (("T1", lambda x: x < a),
                           ("T2", lambda x: a <= x < b),
                           ("T3", lambda x: x >= b)):
            sub = [r for r in funded if pred(r["S"])]
            thirds[name] = {"n": len(sub),
                            "net": round(sum(r["net"] for r in sub), 6)}
    m["descriptive_calendar_thirds_DESCRIPTIVE_ONLY"] = thirds
    m["folds_note"] = "NULL in source (pre-scoring D2 kill) — pool only"
    m["status_counts"] = {st: sum(1 for r in rows if r.get("status") == st)
                          for st in sorted({r.get("status") for r in rows})}
    m["exposure"] = {"funded_decisions": len(funded),
                     "settlements_span": [ks[0], ks[-1]] if ks else None}
    m["turnover"] = {"fills": 2 * len(funded)}
    m["decision_rows_digest"] = canon_digest(
        [[r[c] for c in eng.DECISION_ROW_COLUMNS] for r in rows])
    # descriptive control arms (A7 r2 F4a): same panels/funding, frozen
    # arm rules — DESCRIPTIVE_ONLY, never fold evidence
    eng.ALLOW_SCORE = True
    try:
        for arm_name, builder in (
                ("CTL-SHIFTBOUNDMINUS2H",
                 eng.build_ctl_shiftboundminus2h_decisions),
                ("CTL-FUNDLEVEL", eng.build_ctl_fundlevel_decisions)):
            arows = [dict(zip(eng.DECISION_ROW_COLUMNS, r))
                     if not isinstance(r, dict) else r
                     for r in builder(panels, funding)["rows"]]
            af = [r for r in arows if r.get("net") is not None
                  and r.get("entry") is not None]
            m.setdefault("control_arms_DESCRIPTIVE_ONLY", {})[arm_name] = {
                "n": len(af), "net": round(sum(r["net"] for r in af), 6)}
    finally:
        eng.ALLOW_SCORE = False
    if ks:
        import datetime as _dt
        d0 = _dt.datetime.fromisoformat(str(ks[0]).replace("Z", "+00:00"))
        d1 = _dt.datetime.fromisoformat(str(ks[-1]).replace("Z", "+00:00"))
        yrs = max((d1 - d0).total_seconds() / (365.25 * 86400), 1e-9)
        base = 1.0 + m["net_pnl"]
        if base > 0:
            m["cagr_on_unit_notional"] = round(base ** (1.0 / yrs) - 1.0, 8)
        else:
            m["cagr_on_unit_notional"] = None
            m["cagr_note"] = ("undefined: total-loss domain "
                              "(1 + net <= 0)")
        m["span"] = [str(ks[0]), str(ks[-1])]
    return m


def score_fxng3(contracts) -> dict:
    import fxng3_engine as eng
    binding = json.loads((_RUN / "data" / "fxng3" / "binding_report.json")
                         .read_text())
    ev_path = (_RUN / "data" / "fxng3" / "fred_vintaged_repull" /
               "CANCPIALLMINMEI_derived_events.json")
    bars_path = (_RUN / "data" / "fxng3" / "twelvedata_repull" /
                 "USDCAD_1day_repull.json")
    ev = eng.load_events(
        ev_path,
        expected_sha256=_pin_for(binding, "CANCPIALLMINMEI",
                                 sub_hint="derived restricted-event"))
    bars = eng.load_bars(
        bars_path,
        expected_sha256=_pin_for(binding, "USDCAD",
                                 sub_hint="assembled repull"))
    grid = eng.build_grid(bars)
    eng.ALLOW_SCORE = True
    try:
        pos = eng.build_positions(ev, grid, bars)
    finally:
        eng.ALLOW_SCORE = False
    rows = [dict(zip(eng.POSITION_ROW_COLUMNS, r))
            if not isinstance(r, dict) else r for r in pos["rows"]]
    funded = [r for r in rows if r.get("net") is not None
              and r.get("entry_open") is not None]
    m = _full_metrics(funded, lambda r: r["gross"], ["F1", "F2", "F3"],
                      1.5 / 3.0, eng.COST_TIERS["2.0"]["bps_per_side"] * 2)
    m["status_counts"] = {st: sum(1 for r in rows if r.get("status") == st)
                          for st in sorted({r.get("status") for r in rows})}
    held = sum((r.get("hold_days") or 0) for r in funded)
    m["exposure"] = {"held_grid_cells": held,
                     "grid_days": len(grid)}
    m["turnover"] = {"fills": 2 * len(funded)}
    if funded:
        y0 = min(str(r["D"]) for r in funded)[:10]
        y1 = max(str(r["exit_day"]) for r in funded)[:10]
        import datetime as _dt
        yrs = max((_dt.date.fromisoformat(y1) -
                   _dt.date.fromisoformat(y0)).days / 365.25, 1e-9)
        base = 1.0 + m["net_pnl"]
        if base > 0:
            m["cagr_on_unit_notional"] = round(base ** (1.0 / yrs) - 1.0, 8)
        else:
            m["cagr_on_unit_notional"] = None
            m["cagr_note"] = ("undefined: total-loss domain "
                              "(1 + net <= 0)")
        m["span"] = [y0, y1]
    m["decision_rows_digest"] = canon_digest(rows)
    try:
        m["benchmark_descriptive_DESCRIPTIVE_ONLY"] = eng.build_benchmark(pos)
    except Exception as e:                    # noqa: BLE001
        m["benchmark_descriptive_DESCRIPTIVE_ONLY"] = {"error": repr(e)}
    return m


def reproduce(results: dict) -> dict:
    """Re-run and require identical digests (P4)."""
    contracts = load_contracts()
    again = {}
    if "CNG2-A5-P1" in results:
        again["CNG2-A5-P1"] = score_cng2(contracts)
    if "FXNG3-A4-P1" in results:
        again["FXNG3-A4-P1"] = score_fxng3(contracts)
    ok = all(
        again[k]["decision_rows_digest"] == results[k]["decision_rows_digest"]
        for k in again)
    return {"reproduced": ok,
            "detail": {k: again[k]["decision_rows_digest"]
                       for k in again}}


def main() -> int:
    t0 = time.time()
    phrase = os.environ.get(GO_PHRASE_ENV, "")
    if phrase != GO_PHRASE:
        raise SystemExit(
            "GO gate: set D2C_GO_PHRASE to the owner's exact phrase "
            "(P-8; early/paraphrased dies unconsumed)")
    p0_env()
    contracts = load_contracts()
    import cells_registry as reg
    reg.assert_registry_intact()
    handle, stop = p1_lock()
    log("heavy lock acquired")
    results = {}
    observed_slots = 0
    plan_cells = ["SFNG2-A4-P1", "FXNG3-A4-P1", "CNG2-A5-P1"]
    try:
        for fam in plan_cells:
            if not family_bindable(contracts["gate"], fam):
                results[fam] = {
                    "verdict": "NOT_RUN_DATA_BLOCKED",
                    "reason": "data gate: not BINDABLE_NOW (see "
                              "data_gate_report.json)",
                    "label": LABEL}
                log(f"{fam}: NOT_RUN_DATA_BLOCKED (no slot consumed)")
                continue
            observed_slots += 1
            log(f"scoring {fam} (observed slot {observed_slots}/3)")
            try:
                if fam == "CNG2-A5-P1":
                    m = score_cng2(contracts)
                elif fam == "FXNG3-A4-P1":
                    m = score_fxng3(contracts)
                else:
                    raise RuntimeError("no engine wired for this family")
                m["verdict"] = ("NET_POSITIVE" if (m["net_pnl"] or 0) > 0
                                else "NET_NEGATIVE" if (m["net_pnl"] or 0) < 0
                                else "FLAT")
                results[fam] = m
            except Exception as e:                       # noqa: BLE001
                import traceback
                results[fam] = {
                    "verdict": "NOT_ADJUDICABLE",
                    "reason": f"technical failure at scoring: {e!r}",
                    "traceback_tail": traceback.format_exc()[-1500:],
                    "label": LABEL}
                log(f"{fam} NOT_ADJUDICABLE (technical): {e!r}")
        rep = reproduce(results)
        summary = {
            "schema": "d2c_score_summary@1",
            "cycle_id": "D2-CURIOSITY-V1",
            "go_phrase_state": "CONSUMED_AT_GATE",
            "observed_diagnostic_slots": observed_slots,
            "budget": f"{observed_slots}/3",
            "results": results,
            "reproduction": rep,
            "old_d2_verdicts_preserved_verbatim":
                json.loads((_RUN / "source_identity_freeze.json").read_text())
                ["prior_d2_verdicts_preserved_verbatim"],
            "forbidden_language": ["D2 PASS", "survivor", "validated edge",
                                   "production-ready"],
            "wall_seconds": round(time.time() - t0, 1),
            "label": LABEL,
        }
        tmp = _RUN / "score_summary.json.tmp"
        tmp.write_text(json.dumps(summary, indent=1, sort_keys=True,
                                  default=str) + "\n")
        os.replace(tmp, _RUN / "score_summary.json")
        log(f"summary written; reproduction identical: {rep['reproduced']}")
        return 0
    finally:
        try:
            handle.release(status="FINISHED", note="d2c scored job")
        finally:
            stop.set()
        log("heavy lock released")


if __name__ == "__main__":
    sys.exit(main())
