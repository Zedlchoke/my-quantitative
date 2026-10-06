"""A7-R2 independent reproduction/verification of co-owner findings R1-R4.

Fresh-context auditor script (no lane test code imported). Builds its own
fixtures from futbt primitives and prints OBSERVED numbers for:

  R1  commission quantity drop + missing-fee zeroing + slippage blindness
  R2  roll old-leg gross missing from journal (journal vs ledger)
  R3  roll-before-barrier frame mixing (new-contract fill vs old stop)
  R4  gap-stop fill outside bar range

Run from either checkout's code/ dir:
    python audit-relative-path/repro_exec.py
Prints one JSON blob per check with a REPRODUCED / FIXED / status tag.
"""
import datetime as dt
import json
import sys

from futbt.calendarx import WeekdayCalendar
from futbt.costs import CostBook
from futbt.engine import BacktestEngine, Decision, EngineConfig
from futbt.journal import TradeJournal
from futbt.rawdata import Bar, ContractData, ContractIdentity
from futbt.roll import RollEngine

OUT = {"commit_context": sys.argv[1] if len(sys.argv) > 1 else "unspecified"}


def bar(d, o, h, l, c, v=1000):
    b = Bar(t=d, t_raw=d.isoformat(), t_iso=None, o=o, h=h, l=l, c=c,
            v=v, wap=c, n=v)
    return b.validate()


def contract(symbol, local, conid, ltd, bars):
    ident = ContractIdentity(symbol=symbol, local_symbol=local, conid=conid,
                             last_trade_date=ltd)
    return ContractData(identity=ident, daily_trades=bars)


def staircase_es(gap=10.0):
    """Two ES contracts, roll at last session before 2026-03-01
    (=Fri 2026-02-27), staircase +3/day from 5000."""
    cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 6, 30))
    ss = cal.sessions()
    a, b = [], []
    for i, s in enumerate(ss):
        px = 5000.0 + 3.0 * i
        b.append(bar(s, px + gap, px + gap + 5, px + gap - 5, px + gap))
        if s <= dt.date(2026, 3, 18):
            a.append(bar(s, px, px + 5, px - 5, px))
    ca = contract("ES", "ESH6", 101, dt.date(2026, 3, 18), a)
    cb = contract("ES", "ESM6", 102, dt.date(2026, 6, 18), b)
    return cal, [ca, cb]


def engine_for(symbol, cons, cal, book=None, cfg=None):
    re = RollEngine(symbol, cons, cal)
    return BacktestEngine(symbol, re, re.build_roll_table(),
                          book or CostBook.for_symbol(symbol),
                          cfg or EngineConfig())


def once(strategy, t0, **kw):
    def strat(ctx):
        if ctx.asof == t0:
            return Decision(action=kw.get("action", "enter_long"),
                            qty=kw.get("qty", 1),
                            tp_price=kw.get("tp_price", 10**9),
                            sl_price=kw.get("sl_price", -10**9),
                            time_exit_sessions=kw.get("time_exit_sessions", 3),
                            reason=kw.get("reason", "a7r2"),
                            features={})
        return Decision(action="none")
    return strat


# ------------------------------------------------------------------ R1
def r1():
    res = {}
    # R1a: ES qty3 commission scaling
    cal, cons = staircase_es()
    eng = engine_for("ES", cons, cal)
    j = eng.run(once(None, dt.date(2026, 1, 5), qty=3,
                     time_exit_sessions=3, reason="r1-qty3"),
                TradeJournal(0.0))
    rec = [r for r in j.records if r.entry_fill][0]
    res["r1a_es_qty3"] = {
        "qty": rec.qty,
        "entry_signed_qty": rec.entry_fill.signed_qty,
        "entry_cost_usd": rec.entry_fill.cost_total_usd,
        "exit_cost_usd": rec.exit_fill.cost_total_usd,
        "record_cost_total_usd": rec.cost_components_total_usd,
        "expected_per_side_qty3": 6.72,
        "expected_roundtrip_qty3": 13.44,
        "qty_scaled_correct": abs(rec.entry_fill.cost_total_usd - 6.72) < 1e-9,
        "qty_dropped_bug": abs(rec.entry_fill.cost_total_usd - 2.24) < 1e-9,
    }
    # R1b: CL known broker fee zeroed when exchange fee missing
    cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 4, 30))
    ss = cal.sessions()
    bars_a = [bar(s, 60.0, 60.5, 59.5, 60.0, v=500)
              for s in ss if s <= dt.date(2026, 3, 18)]
    bars_b = [bar(s, 61.0, 61.5, 60.5, 61.0, v=500)
              for s in ss if s >= dt.date(2026, 1, 5)]
    cons = [contract("CL", "CLH6", 11, dt.date(2026, 3, 18), bars_a),
            contract("CL", "CLJ6", 12, dt.date(2026, 4, 18), bars_b)]
    eng = engine_for("CL", cons, cal)
    j = eng.run(once(None, dt.date(2026, 1, 5), time_exit_sessions=2,
                     reason="r1-cl"), TradeJournal(0.0))
    rec = [r for r in j.records if r.entry_fill][0]
    res["r1b_cl_missing_fee"] = {
        "entry_cost_usd": rec.entry_fill.cost_total_usd,
        "expected_known_broker_fee": 0.85,
        "zeroed_bug": rec.entry_fill.cost_total_usd == 0.0,
        "known_fee_charged": abs(rec.entry_fill.cost_total_usd - 0.85) < 1e-9,
        "cost_incomplete_flag": rec.cost_incomplete,
    }
    # R1c: cost_incomplete blind to missing slippage (ES complete
    # commissions, slippage NOT_RUN in the default book)
    book = CostBook.for_symbol("ES")
    slip = book.components.get("slippage") if hasattr(book, "components") else None
    slip_known = slip is not None and getattr(slip, "usd_per_contract_side", None) is not None
    cal, cons = staircase_es()
    eng = engine_for("ES", cons, cal)
    j = eng.run(once(None, dt.date(2026, 1, 5), time_exit_sessions=2,
                     reason="r1-slip"), TradeJournal(0.0))
    rec = [r for r in j.records if r.entry_fill][0]
    missing = getattr(rec, "cost_missing_components", None)
    res["r1c_slippage_blindness"] = {
        "es_slippage_component_known_in_book": slip_known,
        "record_cost_incomplete": rec.cost_incomplete,
        "cost_missing_components_field": missing,
        "blind_bug": (not rec.cost_incomplete) and (not slip_known),
        "covers_slippage": (rec.cost_incomplete and missing is not None
                            and "slippage" in missing),
    }
    # R1d: allow_incomplete_costs=False refusal (fix-only behavior)
    try:
        engine_for("CL", cons, cal, cfg=EngineConfig(
            allow_incomplete_costs=False))
        res["r1d_refusal"] = {"refused": False}
    except Exception as e:
        res["r1d_refusal"] = {"refused": True, "error": type(e).__name__,
                              "msg": str(e)[:160]}
    return res


# ------------------------------------------------------------------ R2
def r2():
    cal, cons = staircase_es()
    eng = engine_for("ES", cons, cal)
    j = eng.run(once(None, dt.date(2026, 2, 24), time_exit_sessions=6,
                     reason="r2-roll"), TradeJournal(0.0))
    rec = [r for r in j.records if r.entry_fill][0]
    st = eng.last_run_stats
    segs = getattr(rec, "gross_segments", None)
    ledger_gross = st["realized_gross_usd"]
    journal_gross = rec.gross_pnl_usd
    ir = st.get("independent_reconciliation")
    out = {
        "rolls": len(rec.rolls),
        "ledger_realized_gross_usd": ledger_gross,
        "journal_gross_pnl_usd": journal_gross,
        "journal_net_pnl_usd": rec.net_pnl_usd,
        "ledger_final_usd": st["ledger"]["final"],
        "gross_missing_bug": (journal_gross is not None
                              and abs(journal_gross - 425.0) < 1e-6
                              and abs(ledger_gross - 700.0) < 1e-6),
        "reconciled": (journal_gross is not None
                       and abs(journal_gross - ledger_gross) < 1e-6),
    }
    if segs is not None:
        out["gross_segments"] = [
            {"kind": s.get("kind"), "conid": s.get("conid"),
             "session": s.get("session"), "gross_usd": s.get("gross_usd")}
            for s in segs]
    if ir is not None:
        out["independent_reconciliation"] = {
            k: ir.get(k) for k in ("reconciled", "journal_gross_usd",
                                   "journal_costs_usd", "cash_final_usd",
                                   "ledger_realize_usd", "per_bar_checks",
                                   "ledger_cost_outflow_usd")
            if k in ir}
    return {"r2_roll_lifecycle": out}


# ------------------------------------------------------------------ R3
def r3():
    cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 6, 30))
    ss = cal.sessions()
    a, b = [], []
    for i, s in enumerate(ss):
        px = 5000.0 + 3.0 * i
        if s == dt.date(2026, 2, 26):
            a.append(bar(s, 100.0, 101.0, 99.0, 100.0))
        elif s == dt.date(2026, 2, 27):
            a.append(bar(s, 110.0, 115.0, 90.0, 112.0))
            b.append(bar(s, 200.0, 205.0, 198.0, 202.0))
        elif s <= dt.date(2026, 3, 18):
            a.append(bar(s, px, px + 5, px - 5, px))
        if s != dt.date(2026, 2, 27) and s >= dt.date(2026, 1, 2):
            b.append(bar(s, px + 10, px + 15, px + 5, px + 10))
    cons = [contract("ES", "ESH6", 101, dt.date(2026, 3, 18), a),
            contract("ES", "ESM6", 102, dt.date(2026, 6, 18), b)]
    eng = engine_for("ES", cons, cal)
    j = eng.run(once(None, dt.date(2026, 2, 25), tp_price=150.0,
                     sl_price=95.0, time_exit_sessions=10,
                     reason="r3-order"), TradeJournal(0.0))
    rec = [r for r in j.records if r.entry_fill][0]
    px = rec.exit_fill.price
    lo_new, hi_new = 198.0, 205.0
    lo_old, hi_old = 90.0, 115.0
    segs = getattr(rec, "mae_mfe_segments", None)
    seg_out = None
    if segs:
        seg_out = [{"conid": s.get("conid"), "mae_usd": s.get("mae_usd"),
                    "mfe_usd": s.get("mfe_usd")} for s in segs]
    return {"r3_barrier_vs_roll": {
        "exit_type": rec.exit_type,
        "exit_session": rec.exit_session.isoformat()
        if rec.exit_session else None,
        "exit_conid": rec.exit_fill.conid,
        "exit_symbol": rec.exit_fill.local_symbol,
        "exit_price": px,
        "n_rolls": len(rec.rolls),
        "inside_old_bar_range": lo_old <= px <= hi_old,
        "outside_new_bar_range_bug": not (lo_new <= px <= hi_new) and rec.exit_fill.conid == 102,
        "frame_mix_184_75_bug": abs(px - 184.75) < 1e-9,
        "old_contract_stop_94_75_fixed": (abs(px - 94.75) < 1e-9
                                          and rec.exit_fill.conid == 101),
        "mae_mfe_segments": seg_out,
    }}


# ------------------------------------------------------------------ R4
def r4():
    bars = [bar(dt.date(2026, 1, 5), 100.5, 101, 99.5, 100.0),
            bar(dt.date(2026, 1, 6), 100.0, 101.0, 99.0, 100.5),
            bar(dt.date(2026, 1, 7), 80.0, 90.0, 70.0, 85.0),
            bar(dt.date(2026, 1, 8), 100.0, 101.0, 99.0, 100.5)]
    cal = WeekdayCalendar(dt.date(2026, 1, 5), dt.date(2026, 1, 8))
    cons = [contract("ES", "ESH6", 101, dt.date(2026, 1, 8), bars)]
    eng = engine_for("ES", cons, cal)
    j = eng.run(once(None, dt.date(2026, 1, 5), sl_price=95.0,
                     reason="r4-gap"), TradeJournal(0.0))
    rec = [r for r in j.records if r.entry_fill][0]
    px = rec.exit_fill.price
    return {"r4_gap_stop": {
        "exit_type": rec.exit_type,
        "exit_session": rec.exit_session.isoformat()
        if rec.exit_session else None,
        "exit_price": px,
        "bar_range": [70.0, 90.0],
        "open": 80.0,
        "outside_bar_range_bug": not (70.0 <= px <= 90.0),
        "fill_94_75_bug": abs(px - 94.75) < 1e-9,
        "open_adverse_79_75_fixed": abs(px - 79.75) < 1e-9,
        "gross_pnl_usd": rec.gross_pnl_usd,
    }}


# ------------------------------------------------------- R4b: same-bar ambiguous
def r4b():
    bars = [bar(dt.date(2026, 1, 5), 100.5, 101, 99.5, 100.0),
            bar(dt.date(2026, 1, 6), 100.0, 101.0, 99.0, 100.5),
            bar(dt.date(2026, 1, 7), 100.0, 108.0, 92.0, 100.0),
            bar(dt.date(2026, 1, 8), 100.0, 101.0, 99.0, 100.5)]
    cal = WeekdayCalendar(dt.date(2026, 1, 5), dt.date(2026, 1, 8))
    cons = [contract("ES", "ESH6", 101, dt.date(2026, 1, 8), bars)]
    eng = engine_for("ES", cons, cal)
    j = eng.run(once(None, dt.date(2026, 1, 5), tp_price=105.0,
                     sl_price=95.0, reason="r4-amb"), TradeJournal(0.0))
    rec = [r for r in j.records if r.entry_fill][0]
    return {"r4b_same_bar_ambiguous": {
        "ambiguity": rec.ambiguity,
        "net_pnl_is_none": rec.net_pnl_usd is None,
        "scenario_bounds": rec.scenario_bounds,
    }}


if __name__ == "__main__":
    for name, fn in (("R1", r1), ("R2", r2), ("R3", r3), ("R4", r4),
                     ("R4b", r4b)):
        try:
            OUT[name] = fn()
        except Exception as e:
            OUT[name] = {"ERROR": f"{type(e).__name__}: {e}"}
    print(json.dumps(OUT, indent=1, default=str))
