"""A7-R2 adversarial regression D2: zero-range bar (H==L) with TP and SL
both outside the bar; and D3: 2-symbol portfolio with a cost book missing
the exchange fee on one symbol.

D2: a long faces a bar with O==H==L==C==100 (real volume, NOT close-only)
with TP=150 / SL=50 — both unreachable. No crash, no invented fill: the
position must survive that bar and exit later by TIME at a real price.
Also the mirrored short case (TP=50 / SL=150).

D3: CL (exchange+regulatory fee NOT_RUN in CostBook.for_symbol) + ES in
one PortfolioEngine; both trade. CL records must disclose the missing
exchange fee as NULL with provenance (never a fabricated 0 and never
silently omitted); known CL broker commission 0.85/side still charged;
ES (complete commissions, slippage declared for this test) stamps
cost_incomplete=False. Portfolio cash identity must hold.
"""
import datetime as dt
import json
import sys

from futbt.calendarx import WeekdayCalendar
from futbt.costs import CostBook
from futbt.engine import (BacktestEngine, Decision, EngineConfig,
                          PortfolioEngine)
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


def engine_for(sym, bars, cfg=None, book=None):
    cal = WeekdayCalendar(bars[0].t, bars[-1].t)
    cons = [contract(sym, f"{sym}H6", 101, bars[-1].t, bars)]
    re = RollEngine(sym, cons, cal)
    return BacktestEngine(sym, re, re.build_roll_table(),
                          book or CostBook.for_symbol(sym),
                          cfg or EngineConfig())


def once(t0, action="enter_long", qty=1, tp=None, sl=None, time_exit=3):
    def strat(ctx):
        if ctx.asof == t0:
            return Decision(action=action, qty=qty, tp_price=tp,
                            sl_price=sl, time_exit_sessions=time_exit,
                            reason="adv", features={})
        return Decision(action="none")
    return strat


def d2():
    res = {}
    # long, TP/SL both ABOVE and BELOW the zero-range bar at 100
    bars = [bar(dt.date(2026, 1, 5), 100.5, 101, 99.5, 100.0),
            bar(dt.date(2026, 1, 6), 100.0, 101.0, 99.0, 100.5),
            bar(dt.date(2026, 1, 7), 100.0, 100.0, 100.0, 100.0),  # H==L
            bar(dt.date(2026, 1, 8), 100.0, 101.0, 99.0, 100.5),
            bar(dt.date(2026, 1, 9), 101.0, 102.0, 100.0, 101.5)]
    eng = engine_for("ES", bars)
    j = eng.run(once(dt.date(2026, 1, 5), tp=150.0, sl=50.0,
                     time_exit=3), TradeJournal(0.0))
    rec = [r for r in j.records if r.entry_fill][0]
    res["long_zero_range"] = {
        "exit_type": rec.exit_type,
        "exit_session": rec.exit_session.isoformat(),
        "exit_price": rec.exit_fill.price,
        "exited_on_zero_range_bar": rec.exit_session == dt.date(2026, 1, 7),
        "no_barrier_invented": rec.exit_type in ("TIME", "END_OF_DATA",
                                                 "MANUAL"),
    }
    # short mirror
    bars_s = [bar(dt.date(2026, 1, 5), 100.5, 101, 99.5, 100.0),
              bar(dt.date(2026, 1, 6), 100.0, 101.0, 99.0, 100.5),
              bar(dt.date(2026, 1, 7), 100.0, 100.0, 100.0, 100.0),
              bar(dt.date(2026, 1, 8), 100.0, 101.0, 99.0, 100.5),
              bar(dt.date(2026, 1, 9), 99.0, 100.0, 98.0, 99.5)]
    eng = engine_for("ES", bars_s)
    j = eng.run(once(dt.date(2026, 1, 5), action="enter_short", tp=50.0,
                     sl=150.0, time_exit=3), TradeJournal(0.0))
    rec = [r for r in j.records if r.entry_fill][0]
    res["short_zero_range"] = {
        "exit_type": rec.exit_type,
        "exit_session": rec.exit_session.isoformat(),
        "exited_on_zero_range_bar": rec.exit_session == dt.date(2026, 1, 7),
        "no_barrier_invented": rec.exit_type in ("TIME", "END_OF_DATA",
                                                 "MANUAL"),
    }
    # degenerate universe: EVERY bar zero-range -> TIME exit must still
    # resolve somewhere legal or censor honestly; never a barrier fill
    bars_z = [bar(dt.date(2026, 1, 5), 100.0, 100.0, 100.0, 100.0),
              bar(dt.date(2026, 1, 6), 100.0, 100.0, 100.0, 100.0),
              bar(dt.date(2026, 1, 7), 100.0, 100.0, 100.0, 100.0)]
    eng = engine_for("ES", bars_z)
    j = eng.run(once(dt.date(2026, 1, 5), tp=150.0, sl=50.0,
                     time_exit=2), TradeJournal(0.0))
    recs = [r for r in j.records if r.entry_fill]
    res["all_zero_range"] = {
        "n_records": len(recs),
        "exit_type": recs[0].exit_type if recs else None,
        "not_barrier": (recs[0].exit_type not in ("TP", "SL")) if recs else None,
    }
    res["PASS"] = (
        res["long_zero_range"]["no_barrier_invented"]
        and not res["long_zero_range"]["exited_on_zero_range_bar"]
        and res["short_zero_range"]["no_barrier_invented"]
        and not res["short_zero_range"]["exited_on_zero_range_bar"]
        and res["all_zero_range"]["not_barrier"])
    return res


def d3():
    cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 3, 31))
    ss = cal.sessions()

    def quiet(start, gap=0.0):
        return [bar(s, start + gap + 0.1 * i, start + gap + 0.1 * i + 1,
                    start + gap + 0.1 * i - 1, start + gap + 0.1 * i)
                for i, s in enumerate(ss)]

    cl_cons = [contract("CL", "CLH6", 11, dt.date(2026, 3, 20),
                        quiet(70.0, 0.0)),
               contract("CL", "CLJ6", 12, dt.date(2026, 4, 20),
                        quiet(70.0, -0.40))]
    es_cons = [contract("ES", "ESH6", 31, dt.date(2026, 3, 18),
                        quiet(5000.0, 0.0)),
               contract("ES", "ESM6", 32, dt.date(2026, 6, 18),
                        quiet(5000.0, 10.0))]
    es_book = CostBook.for_symbol("ES").declare_slippage(
        10.0, "adv-d3", "declared for the complete-book contrast")
    engines = {}
    for sym, cons in (("CL", cl_cons), ("ES", es_cons)):
        re = RollEngine(sym, cons, cal)
        book = es_book if sym == "ES" else CostBook.for_symbol("CL")
        engines[sym] = BacktestEngine(sym, re, re.build_roll_table(),
                                      book, EngineConfig())
    strats = {
        "CL": once(dt.date(2026, 1, 5), time_exit=5),
        "ES": once(dt.date(2026, 1, 5), time_exit=5),
    }
    pe = PortfolioEngine(engines)
    res = pe.run(strats)
    out = {}
    cl_rec = [r for r in res.journals["CL"].records if r.entry_fill][0]
    es_rec = [r for r in res.journals["ES"].records if r.entry_fill][0]
    bd = cl_rec.entry_fill.cost_breakdown
    status = bd.get("missing_component_status", {}).get(
        "exchange_plus_regulatory", {})
    out["cl_missing_fee_disclosure"] = {
        "cost_incomplete": cl_rec.cost_incomplete,
        "missing_components": getattr(cl_rec, "cost_missing_components", None),
        "known_broker_fee_charged": abs(
            cl_rec.entry_fill.cost_total_usd - 0.85) < 1e-9,
        "fee_value_is_null_not_zero": status.get(
            "value_usd_per_contract_side") is None,
        "provenance": status.get("provenance"),
        "expected_source_class": status.get(
            "expected_source_class_when_provided"),
    }
    out["es_complete_book"] = {
        "cost_incomplete": es_rec.cost_incomplete,
        "missing_components": getattr(es_rec, "cost_missing_components", None),
    }
    # portfolio cash identity: final cash = initial + gross - costs, both symbols
    ident = {}
    for sym in ("CL", "ES"):
        st = engines[sym].last_run_stats
        ident[sym] = abs(st["ledger"]["final"] - (
            st["ledger"]["initial"] + st["realized_gross_usd"]
            - st["total_costs_usd"])) < 1e-6
    out["cash_identity"] = ident
    out["PASS"] = (
        out["cl_missing_fee_disclosure"]["cost_incomplete"]
        and "exchange_plus_regulatory" in out["cl_missing_fee_disclosure"]["missing_components"]
        and out["cl_missing_fee_disclosure"]["known_broker_fee_charged"]
        and out["cl_missing_fee_disclosure"]["fee_value_is_null_not_zero"]
        and out["cl_missing_fee_disclosure"]["provenance"] == "NOT_RUN"
        and not out["es_complete_book"]["cost_incomplete"]
        and all(ident.values()))
    return out


if __name__ == "__main__":
    OUT["D2_zero_range_bar"] = d2()
    OUT["D3_missing_exchange_fee_portfolio"] = d3()
    ok = OUT["D2_zero_range_bar"]["PASS"] and OUT["D3_missing_exchange_fee_portfolio"]["PASS"]
    OUT["PASS"] = ok
    print(json.dumps(OUT, indent=1, default=str))
    sys.exit(0 if ok else 1)
