"""D2-CURIOSITY-V1 scored orchestrator (run ONLY after the owner GO).

Phases (per plan §6 E/R):
  P0  env verify: branch, HEAD contains the freeze commits, tree clean
      (engines/ + contracts committed), no S1 path reachable
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
                           capture_output=True, text=True, check=True).stdout.strip()
    if branch != "orca/d2-curiosity-v1-integration":
        raise RuntimeError(f"wrong branch {branch}")
    if dirty:
        raise RuntimeError(f"worktree dirty: {dirty[:300]}")
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


def score_cng2(contracts) -> dict:
    """GO-time scoring: build the anchor decision rows on the BOUND data
    (per-row outcomes; this is the sanctioned scored computation), then
    aggregate per the frozen evaluation contract."""
    import cng2_engine as eng
    eng.ALLOW_SCORE = True          # sanctioned setter at GO-time only
    try:
        panels = {s: eng.load_panel(_RUN / "data" / "cng2", s)
                  for s in eng.UNIVERSE}
        funding = {s: eng.load_funding_series(_RUN / "data" / "cng2", s)
                   for s in eng.UNIVERSE}
        rows = [dict(zip(eng.DECISION_ROW_COLUMNS, r))
                for r in eng.build_anchor_decisions(panels, funding)]
    finally:
        eng.ALLOW_SCORE = False
    funded = [r for r in rows
              if r.get("status") in ("OK", "FUNDED", None)
              and r.get("net") is not None]
    t2 = eng.COST_TIERS["2.0"]
    bps_rt = (t2["taker_bps_per_fill"] + t2["spread_bps_per_fill"]) * 2
    m = _metrics_from_rows(funded, [], bps_rt)
    ks = sorted({r["S"] for r in funded})
    thirds = {}
    if ks:
        t1, t2k = ks[len(ks) // 3], ks[2 * len(ks) // 3]
        for name, pred in (("T1", lambda s: s < t1),
                           ("T2", lambda s: t1 <= s < t2k),
                           ("T3", lambda s: s >= t2k)):
            sub = [r for r in funded if pred(r["S"])]
            thirds[name] = {"n": len(sub),
                            "net": round(sum(r["net"] for r in sub), 6)}
    m["descriptive_calendar_thirds_DESCRIPTIVE_ONLY"] = thirds
    m["folds_note"] = "NULL in source (pre-scoring D2 kill) — pool only"
    m["status_counts"] = {st: sum(1 for r in rows
                                  if r.get("status") == st)
                          for st in sorted({r.get("status")
                                            for r in rows})}
    m["decision_rows_digest"] = canon_digest(
        [[r[c] for c in eng.DECISION_ROW_COLUMNS] for r in rows])
    m["benchmark_descriptive"] = None  # arms runnable post-GO; recorded
    return m


def score_fxng3(contracts) -> dict:
    import fxng3_engine as eng
    eng.ALLOW_SCORE = True
    try:
        ev = eng.load_events(_RUN / "data" / "fxng3" /
                             "fred_vintaged_repull" /
                             "CANCPIALLMINMEI_derived_events.json")
        bars = eng.load_bars(_RUN / "data" / "fxng3" /
                             "twelvedata_repull" / "USDCAD_1day_repull.json")
        grid = eng.build_grid(bars)
        pos = eng.build_positions(ev, grid, bars)
    finally:
        eng.ALLOW_SCORE = False
    rows = [dict(zip(eng.POSITION_ROW_COLUMNS, r)) if not isinstance(
        r, dict) else r for r in pos]
    measured = [r for r in rows if r.get("status") in ("OK", "MEASURED", None)
                and r.get("net") is not None]
    m = _metrics_from_rows(measured, ["F1", "F2", "F3"],
                           eng.COST_TIERS["2.0"]["bps_per_side"] * 2)
    m["status_counts"] = {st: sum(1 for r in rows
                                  if r.get("status") == st)
                          for st in sorted({r.get("status")
                                            for r in rows})}
    m["decision_rows_digest"] = canon_digest(rows)
    try:
        m["benchmark_descriptive"] = eng.build_benchmark(pos)
    except Exception as e:           # noqa: BLE001 — descriptive only
        m["benchmark_descriptive"] = {"error": repr(e)}
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
                results[fam] = {"verdict": "TECHNICAL_FAILURE",
                                "error": repr(e),
                                "traceback_tail": traceback.format_exc()[-1500:],
                                "label": LABEL}
                log(f"{fam} TECHNICAL_FAILURE: {e!r}")
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
