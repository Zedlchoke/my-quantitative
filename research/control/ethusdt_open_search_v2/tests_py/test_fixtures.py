"""EOSV2 fixtures — hand-computed golden tests for the engine kernel
(plan §P3; CLAUDE §16.2: hand-computed, no production outcomes inside).

Run: .venv/bin/python research/control/ethusdt_open_search_v1/tests_py/test_fixtures.py
All arithmetic below was computed by hand from the frozen cost law:
  fee/side = 5bps * tier on raw price; adverse tick 0.01 * tier in price;
  funding cashflow = -sign * qty * px_settle * rate; qty = 100000 / raw.
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

import random as _r

import eosv2_engine as E  # noqa: E402

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def approx(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


# ---------------------------------------------------------------- synthetic kit

# anchor synthetic bars INSIDE fold F1 (engine trades only inside folds)
_F1_MS = E._FOLD_START_MS["2020-01-01"]


def h4(i: int, o: float, h: float, l: float, c: float) -> dict:
    return {"ts": _F1_MS + i * E.H4_MS, "open": o, "high": h, "low": l, "close": c}


class SettleStub:
    """Deterministic settlement pricer for synthetic tests."""
    def __init__(self, px: float):
        self.px, self.fallbacks = px, 0
    def price(self, ts: int) -> float:
        return self.px


def fund_at_hour(h: int, rate: float) -> dict:
    return {"ts": _F1_MS + h * 3600_000, "rate": rate}


# ---------------------------------------------------------------- 1. resample golden

def test_resample():
    print("1. H4 resample golden (drop incomplete groups)")
    bars = []
    # day 0 hours 0..7 complete -> two H4 bars; hour 8 missing -> group dropped
    for h in range(8):
        bars.append({"ts": h * 3600_000, "open": 10 + h, "high": 11 + h,
                     "low": 9 + h, "close": 10.5 + h})
    bars.append({"ts": 9 * 3600_000, "open": 19.0, "high": 20.0, "low": 18.0, "close": 19.5})
    h4, dropped = E.to_h4(bars)
    check("h4 count 2", len(h4) == 2, f"got {len(h4)}")
    check("incomplete group dropped", dropped == 1, f"got {dropped}")
    b0 = h4[0]
    check("b0 open=first open", b0["open"] == 10.0)
    check("b0 close=hour3 close", b0["close"] == 13.5)
    check("b0 high=max", b0["high"] == 14.0 and b0["low"] == 9.0)


# ---------------------------------------------------------------- 2. indicators golden

def test_indicators():
    print("2. SMA / sign / pct-rank goldens")
    closes = [10.0, 11.0, 12.0, 11.5, 11.0, 12.5]
    st = E.sma_states(closes, 3)
    # SMA3 at idx2 = 11.0 -> close 12 > 11 -> 1 ; idx3 = (11+12+11.5)/3=11.5 -> 11.5>11.5 False -> 0
    check("sma warmup None", st[0] is None and st[1] is None)
    check("sma idx2 = 1", st[2] == 1)
    check("sma idx3 = 0 (close==sma)", st[3] == 0)
    sg = E.sign_states(closes, 2)
    # idx2: 12>10 ->1 ; idx4: 11<12 ->0
    check("sign idx2 = 1", sg[2] == 1)
    check("sign idx4 = 0", sg[4] == 0)
    pr = E.pct_rank_states(closes, 4)
    # idx3 window [10,11,12,11.5], v=11.5: rank=2/3=0.667 -> 1
    # idx4 window [11,12,11.5,11], v=11:  rank=0/3=0 -> 0
    # idx5 window [12,11.5,11,12.5], v=12.5: rank=3/3=1 -> 1
    check("pctrank idx3 = 1", pr[3] == 1)
    check("pctrank idx4 = 0", pr[4] == 0)
    check("pctrank idx5 = 1", pr[5] == 1)


# ---------------------------------------------------------------- 3. one-bar lag + costs-once

def test_lag_and_costs():
    print("3. One-bar lag + costs exactly once (hand arithmetic)")
    # 6 H4 bars all inside one synthetic fold window: use real F1 dates
    bars = [h4(i, 2000.0 + 10 * i, 2010.0 + 10 * i, 1990.0 + 10 * i, 2005.0 + 10 * i)
            for i in range(6)]
    # target decides at bar i-1 close, fills at bar i open:
    # target = [0,1,1,0,0,0] -> enter long at bar1 open 2010, exit at bar3 open 2030
    target = [0, 1, 1, 0, 0, 0]
    res = E.run_book(target, bars, [], 1.0, SettleStub(0))
    f = res["folds"]["F1"]
    qty = 100_000.0 / 2010.0
    entry_eff = 2010.0 + 0.01
    exit_eff = 2030.0 - 0.01
    gross = qty * (exit_eff - entry_eff)
    fee = 5e-4  # 5 bps
    fees = qty * 2010.0 * fee + qty * 2030.0 * fee
    check("one trade", f["trades"] == 1)
    check("two fills", f["fills"] == 2 and res["fills_total"] == 2)
    check("gross exact", approx(f["gross"], gross), f"{f['gross']} vs {gross}")
    check("fees exact", approx(f["fees"], fees), f"{f['fees']} vs {fees}")
    check("net exact", approx(f["net"], gross - fees))
    check("no funding rows -> zero funding", f["funding"] == 0.0)


# ---------------------------------------------------------------- 4. funding sign/cadence

def test_funding():
    print("4. Funding sign + pre-entry exclusion")
    bars = [h4(i, 100.0, 101.0, 99.0, 100.0) for i in range(4)]
    # enter long at bar1 open, hold to fold end (bar3 close)
    target = [0, 1, 1, 1]
    # settlements: hour 0 (pre-entry, before bar1 open=4h), hour 4 (== entry ts),
    # hour 8, hour 12 (inside), hour 16 (>= last settle window end 12+4=16? settle(12+4h=16h) excludes 16h)
    funding = [fund_at_hour(0, 0.001), fund_at_hour(4, 0.001),
               fund_at_hour(8, 0.001), fund_at_hour(12, 0.001),
               fund_at_hour(16, 0.001)]
    res = E.run_book(target, bars, funding, 1.0, SettleStub(100.0))
    f = res["folds"]["F1"]
    qty = 100_000.0 / 100.0
    # charged: ts=4h (== entry_ts, included), 8h, 12h -> 3 events; 0h pre-entry excluded
    check("funding events 3", f["funding_events"] == 3, f"got {f['funding_events']}")
    # long pays positive: cf = -1 * qty * 100 * 0.001 each = -100.0
    check("funding cashflow negative", approx(f["funding"], -3 * qty * 100.0 * 0.001))
    # short receives: invert target
    res2 = E.run_book([0, -1, -1, -1], bars, funding, 1.0, SettleStub(100.0))
    f2 = res2["folds"]["F1"]
    check("short funding positive", approx(f2["funding"], 3 * qty * 100.0 * 0.001))


# ---------------------------------------------------------------- 5. fold force-flat + attribution

def test_fold_boundary():
    print("5. Fold force-flat at boundary close + attribution")
    # bars spanning F1 end: F1 last bar opens 2021-04-30 20:00 (idx 11887ish) — synthetic:
    import datetime as dt
    def ts_of(s):
        return int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    t_f1_last = ts_of("2021-04-30 20:00")
    t_f2_first = ts_of("2021-05-01 00:00")
    bars = [{"ts": t_f1_last - 2 * E.H4_MS, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"ts": t_f1_last, "open": 110.0, "high": 111.0, "low": 109.0, "close": 120.0},
            {"ts": t_f2_first, "open": 130.0, "high": 131.0, "low": 129.0, "close": 131.0},
            {"ts": t_f2_first + E.H4_MS, "open": 140.0, "high": 141.0, "low": 139.0, "close": 141.0}]
    # long from first bar of F1-part; force-flat at F1 last bar CLOSE (120), not F2 open
    target = [1, 1, 0, 0]
    res = E.run_book(target, bars, [], 1.0, SettleStub(0))
    f1, f2 = res["folds"]["F1"], res["folds"]["F2"]
    qty = 100_000.0 / 100.0
    gross = qty * ((120.0 - 0.01) - (100.0 + 0.01))
    fees = qty * 100.0 * 5e-4 + qty * 120.0 * 5e-4
    check("F1 trade closed at close px", f1["trades"] == 1 and approx(f1["net"], gross - fees))
    check("F2 no trades", f2["trades"] == 0)


# ---------------------------------------------------------------- 6. truncation invariance

def test_truncation_invariance():
    print("6. Truncation invariance at the FAMILY-FUNCTION layer (Q-14 law)")
    # Indicators on a suffix must equal the full-series indicators on that
    # suffix once warmup depth is available inside the suffix itself — the
    # book layer is intentionally NOT stateless (positions carry), so the
    # invariance law lives at the signal layer.
    rng = _r.Random(7)
    closes = [100.0 + rng.uniform(-5, 5) for _ in range(300)]
    k = 120
    # after the suffix's OWN warmup (n-1 elements) the windows are identical
    # to the full series' — values must match exactly on that region
    for n in (3, 50):
        full = E.sma_states(closes, n)
        suff = E.sma_states(closes[k:], n)
        check(f"sma_states({n}) suffix-invariant after own warmup",
              suff[n - 1:] == full[k + n - 1:])
    w = 40
    check("pct_rank suffix-invariant after own warmup",
          E.pct_rank_states(closes[k:], w)[w - 1:] == E.pct_rank_states(closes, w)[k + w - 1:])
    lag = 25
    check("sign_states suffix-invariant after own warmup",
          E.sign_states(closes[k:], lag)[lag:] == E.sign_states(closes, lag)[k + lag:])


# ---------------------------------------------------------------- 7. controls determinism

def test_controls():
    print("7. Block-shuffle determinism + effect")
    rng = _r.Random(11)
    st = [rng.choice([0, 1]) for _ in range(120)]  # non-degenerate: blocks differ
    a = E.shuffle_blocks(st, 30, "seed-x")
    b = E.shuffle_blocks(st, 30, "seed-x")
    c = E.shuffle_blocks(st, 30, "seed-y")
    check("same seed identical", a == b)
    check("different seed differs", a != c)
    check("multiset preserved", sorted(a) == sorted(st))
    check("blocks preserved (first 30 of a == some 30-block of st)",
          any(a[:30] == st[i:i + 30] for i in range(0, 120, 30)))


# ---------------------------------------------------------------- 8. no-lookahead mutation

def test_no_lookahead():
    print("8. No-lookahead: +1 bar shift of info series moves fills")
    bars = [h4(i, 100.0 + 5 * i, 101.0 + 5 * i, 99.0 + 5 * i, 100.0 + 5 * i)
            for i in range(12)]
    raw = [0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]  # info states decided at close
    t = [0] + raw[:-1]                            # engine shift
    r1 = E.run_book(t, bars, [], 1.0, SettleStub(0))
    # mutate: info arrives one bar LATER -> fills must move
    raw2 = [0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    t2 = [0] + raw2[:-1]
    r2 = E.run_book(t2, bars, [], 1.0, SettleStub(0))
    f1, f2 = r1["folds"]["F1"], r2["folds"]["F1"]
    # r1 enters at bar2 open (105); r2 enters at bar3 open (110): gross differs
    check("fills moved (gross changed)", not approx(f1["gross"], f2["gross"]),
          f"{f1['gross']} vs {f2['gross']}")
    # and determinism of repeat
    again = E.run_book(t, bars, [], 1.0, SettleStub(0))
    check("repeat run identical", again["folds"]["F1"] == f1)


# ---------------------------------------------------------------- 9. tier scaling law

def test_tiers():
    print("9. Tier scaling: 1.5x scales fee+tick exactly (funding unscaled)")
    bars = [h4(i, 100.0, 101.0, 99.0, 100.0) for i in range(4)]
    target = [0, 1, 1, 1]
    funding = [fund_at_hour(4, 0.001), fund_at_hour(12, 0.001)]
    r10 = E.run_book(target, bars, funding, 1.0, SettleStub(100.0))
    r15 = E.run_book(target, bars, funding, 1.5, SettleStub(100.0))
    check("funding identical across tiers",
          approx(r10["folds"]["F1"]["funding"], r15["folds"]["F1"]["funding"]))
    check("fees scale 1.5x", approx(r15["folds"]["F1"]["fees"],
                                    1.5 * r10["folds"]["F1"]["fees"]))
    qty = 1000.0
    g10 = r10["folds"]["F1"]["gross"]
    g15 = r15["folds"]["F1"]["gross"]
    # exit at fold end close 100, enter at bar1 open 100: gross = qty*((100-0.01*k)-(100+0.01*k))
    check("gross = -qty*2*tick*k", approx(g10, -qty * 0.02) and approx(g15, -qty * 0.03))


def test_settlement_pricing_pit():
    print("10. Settlement pricing PIT law (A7 E-1 remediation fixture)")
    h0 = _F1_MS                      # an exact hour boundary
    bars = [{"ts": h0 - 3600_000, "open": 100.0, "high": 105.0, "low": 99.0, "close": 110.0},
            {"ts": h0, "open": 130.0, "high": 135.0, "low": 129.0, "close": 150.0},
            {"ts": h0 + 3600_000, "open": 151.0, "high": 155.0, "low": 150.0, "close": 152.0}]
    ps = E.PriceAtSettlement(bars)
    # exact stamp -> floor-hour open
    check("exact stamp uses floor-hour open", ps.price(h0) == 130.0)
    # odd-millisecond stamp (00:00:00.002) MUST be the floor-hour OPEN,
    # never that bar's CLOSE (finalizes 1h later — future price)
    check("odd-ms stamp uses floor-hour open, not close",
          ps.price(h0 + 2) == 130.0, f"got {ps.price(h0 + 2)}")
    # missing floor-hour bar -> close of the last bar ENDING at floor
    bars2 = bars[:1] + bars[2:]
    ps2 = E.PriceAtSettlement(bars2)
    check("missing floor bar -> previous bar close (price AT floor instant)",
          ps2.price(h0 + 2) == 110.0, f"got {ps2.price(h0 + 2)}")


def test_gates_synthetic():
    print("11. gates() synthetic exercise (scored-path plumbing, post-TECHABORT hardening)")
    import run_scored as R
    fold_names = [f[0] for f in E.FOLDS]

    def mk_book(net_folds, fills=10, avg_px=2000.0):
        folds = {fn: {"net": v, "gross": v, "fees": 0.0, "funding": 0.0,
                      "trades": 1, "fills": 2, "funding_events": 1}
                 for fn, v in zip(fold_names, net_folds)}
        return {"res": {"folds": folds, "fills_total": fills,
                        "settlement_price_fallbacks": 0,
                        "net_total": sum(net_folds),
                        "avg_raw_fill_px": avg_px}}

    tier_table = {
        "CELL": {1.0: mk_book([140.0, 60.0, 70.0, 50.0]),   # 320 > all refs
                 1.5: mk_book([80.0, 40.0, 50.0, 30.0]),
                 2.0: mk_book([60.0, 30.0, 40.0, 20.0])},
        "CELL|G6-SHUF": {1.0: mk_book([10.0, 5.0, 6.0, 4.0])},
        "CELL|G6-INV": {1.0: mk_book([-50.0, -5.0, -6.0, -4.0])},
        "BASE_CASH": {1.0: mk_book([0.0, 0.0, 0.0, 0.0])},
        "BASE_ALWAYS_ON_LONG": {1.0: mk_book([200.0, -80.0, 150.0, 30.0])},
        "BASE_TREND_LF": {1.0: mk_book([150.0, 20.0, 120.0, 20.0])},
        "REF_SHORT_ALWAYS": {1.0: mk_book([-100.0, 50.0, -80.0, -20.0])},
    }
    refs = {r: tier_table[r] for r in ("BASE_CASH", "BASE_ALWAYS_ON_LONG",
                                       "BASE_TREND_LF", "REF_SHORT_ALWAYS")}
    feas = {"g11_spearman_vs_trend_lf": {"CELL": 0.3}}
    g = R.gates("CELL", tier_table, refs, feas)
    check("gates returns all G keys",
          all(k in g for k in ("G1", "G2", "G3", "G4", "G5", "G6", "G7",
                               "G10", "G11_disclosure", "all_pass")))
    check("strong synthetic cell ALL-PASS", g["all_pass"] is True,
          f"failed: {[k for k, v in g.items() if k.startswith('G') and isinstance(v, dict) and not v.get('pass', True)]}")
    check("G4 4/4 folds positive", g["G4"] is True)
    check("G5 conc = 0.4375", abs(g["fold_concentration"] - 140.0 / 320.0) < 1e-9)
    # negative case: cell below the wall must fail G3 and all_pass
    tier_table["CELL"][1.0] = mk_book([90.0, 40.0, 50.0, 30.0])
    tier_table["CELL"][1.5] = mk_book([70.0, 30.0, 40.0, 20.0])
    g2 = R.gates("CELL", tier_table, refs, feas)
    check("weak synthetic cell fails G3", g2["G3"]["pass"] is False)
    check("weak synthetic cell not all_pass", g2["all_pass"] is False)


def test_v2_constructors():
    print("12. V2 constructor goldens: rvol_states + breadth_states")
    # rvol: constant prices -> rvol == 0 everywhere; the trailing-1y
    # quantile is also 0, and the law is STRICTLY below -> state 0
    # (degenerate series carry no vol distinction — honest 0, not 1)
    flat = [100.0] * 2600
    st = E.rvol_states(flat, 180, 2190, 0.5)
    check("rvol flat prices -> all 0 after warmup (strict-below law)",
          all(v == 0 for v in st[2370:]), f"tail sample {st[2370:2375]}")
    # positive case: vol that HALVES in the final stretch -> recent rvol
    # below its own trailing distribution -> 1
    import random as _rr
    rngg = _rr.Random(3)
    prices, px = [100.0], 100.0
    for i in range(2599):
        shock = rngg.uniform(-1, 1) * (0.02 if i < 2300 else 0.005)
        px *= (1 + shock)
        prices.append(px)
    stp = E.rvol_states(prices, 180, 2190, 0.5)
    check("rvol vol-halving tail -> 1", all(v == 1 for v in stp[2400:]),
          f"tail sample {stp[2400:2405]}")
    # alternating tiny returns -> rvol constant == threshold (strictly-below fails)
    zig = [100.0 + (0.01 if i % 2 else -0.01) * i for i in range(2600)]
    st2 = E.rvol_states(zig, 180, 2190, 0.5)
    # deterministic + defined after warmup is the golden; exact values:
    check("rvol zigzag states defined after warmup",
          all(v in (0, 1) for v in st2[2370:]))
    # warmup boundary exact: None until vol_win + qual_win
    check("rvol warmup None until 2369", st[2369] is None and st[2370] is not None)
    # breadth: 3 eligible symbols, threshold 2
    ts = [E._FOLD_START_MS["2020-01-01"] + i * E.H4_MS for i in range(6)]
    per = {"SOL": {ts[0]: 1, ts[1]: 1, ts[2]: 0, ts[3]: 0, ts[4]: 1, ts[5]: 1},
           "BNB": {ts[0]: 1, ts[1]: 0, ts[2]: 0, ts[3]: 1, ts[4]: 0, ts[5]: 1},
           "XRP": {ts[0]: 0, ts[1]: 1, ts[2]: 0, ts[3]: 1, ts[4]: 0, ts[5]: 1}}
    b = E.breadth_states(per, ts, 2)
    check("breadth counts >=2", b == [1, 1, 0, 1, 0, 1], f"got {b}")
    b3 = E.breadth_states(per, ts, 3)
    check("breadth ==3 only when all three on", b3 == [0, 0, 0, 0, 0, 1], f"got {b3}")
    b_min = E.breadth_states({"SOL": {ts[0]: 1}}, ts, 1, min_eligible=3)
    check("min_eligible floor enforced (1 symbol: ts0 -> 0, after -> None)",
          b_min == [0, None, None, None, None, None], f"got {b_min}")


def main() -> int:
    test_resample()
    test_indicators()
    test_lag_and_costs()
    test_funding()
    test_fold_boundary()
    test_truncation_invariance()
    test_controls()
    test_no_lookahead()
    test_tiers()
    test_settlement_pricing_pit()
    test_gates_synthetic()
    test_v2_constructors()
    print()
    if FAILURES:
        print(f"FIXTURES FAILED: {len(FAILURES)} -> {FAILURES}")
        return 1
    print("ALL FIXTURES PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
