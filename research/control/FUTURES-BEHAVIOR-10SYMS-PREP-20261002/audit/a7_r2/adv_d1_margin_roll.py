"""A7-R2 adversarial regression D1: margin-cap veto + same-session roll.

3-symbol portfolio (CL with a roll scheduled Fri 2026-02-27, 6J no roll,
ES). ES's entry fill is attempted at the 2026-02-27 open — the SAME
session CL executes its calendar roll — with equity deliberately too low
for the aggregated post-fill book. Verifies:
  * ES blocked with BLOCKED_MARGIN_INITIAL, requested qty preserved
    (never clipped), no ES entry fill;
  * the CL roll still executes on time (another symbol's margin block
    must not disturb it), journal gross reconciles with the ledger;
  * veto math exact: per-symbol requirement == MARGINS initial x qty,
    shortfall == required - equity, breach iff required > equity.

Run from code/ of the HEAD worktree:
  PYTHONPATH=<code> python audit/.../adv_d1_margin_roll.py
"""
import datetime as dt
import json
import sys

from futbt.accounting import MarginModel, MARGINS
from futbt.calendarx import WeekdayCalendar
from futbt.composition import PortfolioRiskGate
from futbt.costs import CostBook
from futbt.engine import (BacktestEngine, Decision, EngineConfig,
                          PortfolioEngine)
from futbt.instruments import get_instrument
from futbt.journal import TradeJournal
from futbt.rawdata import Bar, ContractData, ContractIdentity
from futbt.roll import RollEngine

OUT = {}


def bar(d, o, h, low, c, v=1000):
    return Bar(t=d, t_raw=d.isoformat(), t_iso=None, o=o, h=h, l=low, c=c,
               v=v, wap=c, n=v).validate()


def contract(sym, local, conid, ltd, bars):
    return ContractData(
        identity=ContractIdentity(symbol=sym, local_symbol=local,
                                  conid=conid, last_trade_date=ltd),
        daily_trades=bars)


def staircase(sessions, start, drift, until=None, gap=0.0):
    bars = []
    prev = None
    for i, s in enumerate(sessions):
        if until and s > until:
            break
        c = start + gap + drift * i
        o = prev if prev is not None else c
        bars.append(bar(s, o, max(o, c) + 1.0, min(o, c) - 1.0, c))
        prev = c
    return bars


def build():
    cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 6, 30))
    ss = cal.sessions()
    cl = [contract("CL", "CLH6", 11, dt.date(2026, 3, 20),
                   staircase(ss, 70.0, -0.10, until=dt.date(2026, 3, 20))),
          contract("CL", "CLJ6", 12, dt.date(2026, 4, 20),
                   staircase(ss, 70.0, -0.10, gap=-0.40))]
    j6 = [contract("6J", "6JM6", 21, dt.date(2026, 6, 18),
                   staircase(ss, 0.006330, -0.000001))]
    es = [contract("ES", "ESH6", 31, dt.date(2026, 3, 18),
                   staircase(ss, 5000.0, -3.0, until=dt.date(2026, 3, 18))),
          contract("ES", "ESM6", 32, dt.date(2026, 6, 18),
                   staircase(ss, 5000.0, -3.0, gap=10.0))]
    cash = {"CL": 10_000.0, "6J": 10_000.0, "ES": 5_000.0}
    engines = {}
    for sym, cons in (("CL", cl), ("6J", j6), ("ES", es)):
        re = RollEngine(sym, cons, cal)
        engines[sym] = BacktestEngine(
            sym, re, re.build_roll_table(), CostBook.for_symbol(sym),
            EngineConfig(initial_cash_usd=cash[sym]))
    return cal, engines


def enter_at(t0, direction="long", qty=1, time_exit=200):
    def strat(ctx):
        if ctx.asof == t0 and ctx.position is None:
            return Decision(action=f"enter_{direction}", qty=qty,
                            tp_price=1e12 if direction == "long" else -1e12,
                            sl_price=-1e12 if direction == "long" else 1e12,
                            time_exit_sessions=time_exit, reason="d1",
                            features={})
        return Decision(action="none")
    return strat


def main():
    cal, engines = build()
    gate = PortfolioRiskGate(margin_model=MarginModel(),
                             margin_level="initial")
    strats = {
        "CL": enter_at(dt.date(2026, 1, 5)),                       # holds through the Feb-27 roll
        "6J": enter_at(dt.date(2026, 1, 5)),                       # no roll
        "ES": enter_at(dt.date(2026, 2, 26), qty=2),               # fill at Feb-27 open = roll session
    }
    pe = PortfolioEngine(engines)
    res = pe.run(strats, gate=gate)

    # --- ES margin block ------------------------------------------------
    es_blocked = [r for r in res.journals["ES"].records
                  if r.entry_fill is None and r.veto_reason]
    es_fills = [r for r in res.journals["ES"].records if r.entry_fill]
    blk_audit = [d for d in gate.decisions
                 if d["symbol"] == "ES" and d["kind"] == "fill_block"]
    OUT["es_blocked_records"] = len(es_blocked)
    OUT["es_entry_fills"] = len(es_fills)
    OUT["es_blocked_qty_preserved"] = sorted(
        r.qty for r in es_blocked)
    OUT["es_veto_reasons"] = sorted({r.veto_reason for r in es_blocked})
    OUT["es_block_code"] = blk_audit[0]["code"] if blk_audit else None

    # --- veto math: exact recompute from MARGINS + audit detail ---------
    detail = blk_audit[0]["detail"] if blk_audit else {}
    held_qty = {"CL": 1, "6J": 1, "ES": 2}
    per_sym_expect = {s: MARGINS[s].initial_usd * q
                      for s, q in held_qty.items()}
    OUT["veto_math"] = {
        "per_symbol_usd_detail": detail.get("per_symbol_usd"),
        "per_symbol_usd_expected": per_sym_expect,
        "per_symbol_exact": all(
            abs(detail.get("per_symbol_usd", {}).get(s) - v) < 1e-6
            for s, v in per_sym_expect.items()),
        "required_usd": detail.get("required_usd"),
        "required_expected": sum(per_sym_expect.values()),
        "required_exact": abs(detail.get("required_usd", 0)
                              - sum(per_sym_expect.values())) < 1e-6,
        "shortfall": detail.get("shortfall_usd"),
        "shortfall_identity": abs(
            detail.get("shortfall_usd", -1)
            - max(0.0, detail.get("required_usd", 0)
                  - detail.get("equity_usd", 0))) < 1e-6,
        "breach_iff_required_gt_equity": (
            (detail.get("required_usd", 0) > detail.get("equity_usd", 0))
            == bool(blk_audit)),
    }

    # --- CL roll same session, undisturbed ------------------------------
    cl_recs = [r for r in res.journals["CL"].records if r.entry_fill]
    rolls = cl_recs[0].rolls if cl_recs else []
    OUT["cl_roll"] = {
        "n_rolls": len(rolls),
        "roll_session": rolls[0].session.isoformat() if rolls else None,
        "expected_roll_session": "2026-02-27",
        "roll_on_time": bool(rolls) and rolls[0].session == dt.date(2026, 2, 27),
    }
    ir = engines["CL"].last_run_stats.get("independent_reconciliation")
    OUT["cl_reconciliation"] = {
        "reconciled": ir.get("reconciled") if ir else None,
        "journal_gross": ir.get("journal_gross_usd") if ir else None,
        "ledger_realize": ir.get("ledger_realize_usd") if ir else None,
    }
    # 6J unaffected, no clipping anywhere
    OUT["no_clipping"] = {
        sym: [r.qty for r in res.journals[sym].records]
        for sym in ("CL", "6J", "ES")}
    OUT["verdict"] = {
        "es_blocked_no_fill": len(es_blocked) >= 1 and not es_fills,
        "qty_preserved": all(r.qty == 2 for r in es_blocked),
        "veto_math_exact": OUT["veto_math"]["per_symbol_exact"]
        and OUT["veto_math"]["required_exact"]
        and OUT["veto_math"]["shortfall_identity"]
        and OUT["veto_math"]["breach_iff_required_gt_equity"],
        "roll_undisturbed": OUT["cl_roll"]["roll_on_time"],
        "cl_reconciled": bool(ir and ir.get("reconciled")),
    }
    ok = all(OUT["verdict"].values())
    OUT["PASS"] = ok
    print(json.dumps(OUT, indent=1, default=str))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
