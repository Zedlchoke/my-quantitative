"""RGC100 — REGIME-GATED-COMBO-V1: conditional allocation over 6 DT100 legs.

Frozen laws (plan §2-3, G3 freeze):
- Gate state for week W uses ONLY data strictly before W's Monday 00:00 UTC.
- Tercile cuts computed on WARMUP distributions only (2020-09-01..2021-03-31
  crypto / 2021-01-01..2021-03-31 FX), frozen in GATE_TABLE.json.
- Allocation table is MECHANISM-FIRST: each leg's weight is tilted by the one
  external state variable its dead mechanism claims to need. G3 trend and G4
  corr are computed and logged but deliberately UNUSED (no leg mechanism maps
  to them cleanly; adding knobs would be fitting).
- Weekly reallocation only; switching cost = sum |delta_w| * RT_leg, charged
  exactly once per boundary.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from dt100 import config, signals
from dt100.data import load_binance_zipdir, load_fx_pair
from dt100.engine import run_arm

LEGS = [
    # family, kind, source, params(anchor), symbol, asset, extras
    ("FUNDCONTRA", "fund_contra", "btc1m", {"band": 2.0, "zwin": 90}, "BTCUSDT", "crypto", {}),
    ("WEEKEND", "weekend", "btc1m", {"band": 1.0}, "BTCUSDT", "crypto", {}),
    ("CORRBREAK", "corr_break", "eth1h", {"corr_win": 168, "corr_pct": 30, "band": 1.5, "hold": 12}, "ETHUSDT", "crypto", {"other": "btc1h"}),
    ("ASIANRANGE", "asian_range", "eur", {"edge_frac": 0.10}, "EURUSD", "fx", {}),
    ("LONDONMOM", "london_mom", "eur", {"edge_frac": 0.0}, "EURUSD", "fx", {}),
    ("PDHLSWEEPFX", "pdhl_sweep", "eur", {"reclaim_frac": 0.0004}, "EURUSD", "fx", {}),
]
FOLDS = config.CRYPTO_FOLDS
WEEK_START = pd.Timestamp("2021-04-05", tz="UTC")     # first Monday in folds
WEEK_END = pd.Timestamp("2026-08-31", tz="UTC")
CRYPTO_WARM = (pd.Timestamp("2020-09-01", tz="UTC"), pd.Timestamp("2021-03-31", tz="UTC"))
FX_WARM = (pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp("2021-03-31", tz="UTC"))
RT_CRYPTO_BPS = 2 * (5.0 + 1.0)      # frozen: taker+half-spread, both sides
RT_FX_BPS = None                     # frozen at gate-table build: 2 x warmup median spread


def _fund_contra_pos(df, funding, p):
    z = (funding["rate"] - funding["rate"].rolling(p["zwin"], min_periods=30).mean()) \
        / funding["rate"].rolling(p["zwin"], min_periods=30).std()
    posf = pd.Series(0.0, index=funding.index)
    posf[z.shift(1) > p["band"]] = -1.0
    posf[z.shift(1) < -p["band"]] = 1.0
    held = posf.replace(0.0, np.nan).ffill(limit=1).fillna(0.0)
    mapped = pd.merge_asof(df[["ts"]], pd.DataFrame({"ts": funding["ts"], "pos": held}),
                           on="ts", direction="forward")["pos"].fillna(0.0)
    return pd.Series(mapped.to_numpy(), index=df.index)


def build_leg_pos(leg, df, src):
    fam, kind, _, p, sym, asset, extra = leg
    if kind == "fund_contra":
        return _fund_contra_pos(df, src("funding_btc"), p)
    if kind == "corr_break":
        cb = signals.corr_break(df, src(extra["other"]), p)
        return cb["pos"], cb[["ts", "o", "h", "l", "c"]]
    fn = getattr(signals, kind)
    return fn(df, p)


def leg_weekly_pnl(tr: pd.DataFrame) -> pd.Series:
    """Trade PnL aggregated to ISO-Monday weeks (bps of leg notional)."""
    wk = tr["ts_entry"].dt.floor("W")
    return tr.assign(wk=wk).groupby("wk")["net_bps"].sum()


# ------------------------------------------------------------ gate variables

def funding_z_series(funding: pd.DataFrame) -> pd.Series:
    z = (funding["rate"] - funding["rate"].rolling(90, min_periods=30).mean()) \
        / funding["rate"].rolling(90, min_periods=30).std()
    return pd.Series(z.to_numpy(), index=funding["ts"].to_numpy())


def daily_rv(df_1m: pd.DataFrame) -> pd.Series:
    r = df_1m.set_index("ts")["c"].pct_change()
    rv = r.resample("1D").std() * np.sqrt(1440)
    return rv.dropna()


def _tercile_cuts(s: pd.Series, warm) -> tuple[float, float]:
    m = s[(s.index >= warm[0]) & (s.index <= warm[1])].dropna()
    return float(m.quantile(1 / 3)), float(m.quantile(2 / 3))


def _tercile(v, cuts) -> int:
    return 3 if v > cuts[1] else (1 if v < cuts[0] else 2)


def week_mondays() -> pd.DatetimeIndex:
    return pd.date_range(WEEK_START, WEEK_END, freq="W-MON")


def last_before(s: pd.Series, t) -> float:
    s2 = s[s.index < t]
    return float(s2.iloc[-1]) if len(s2) else float("nan")


def build_gate_table(src, fx_spread_bps) -> dict:
    """Frozen at G3: tercile cuts from warmup + the mechanism-first allocation."""
    fz = funding_z_series(src("funding_btc"))
    btc_rv = daily_rv(src("btc1m"))
    eur_rv = daily_rv(src("eur"))
    table = {
        "frozen_utc": "2026-09-28",
        "cuts": {
            "G1_funding_z": _tercile_cuts(fz, CRYPTO_WARM),
            "G2c_btc_rv": _tercile_cuts(btc_rv, CRYPTO_WARM),
            "G2f_eur_rv": _tercile_cuts(eur_rv, FX_WARM),
        },
        "rt_bps": {"crypto": RT_CRYPTO_BPS, "fx": fx_spread_bps},
        "multipliers": {
            "FUNDCONTRA": "G1: {3:3, 2:2, 1:1}      # harvest needs rich funding",
            "CORRBREAK": "G2c: {3:3, 2:2, 1:1}      # dislocation needs high vol",
            "PDHLSWEEPFX": "G2f: {3:3, 2:2, 1:1}    # sweeps need FX vol",
            "ASIANRANGE": "G2f: {3:1, 2:2, 1:3}     # session books need calm",
            "LONDONMOM": "G2f: {3:1, 2:2, 1:3}",
            "WEEKEND": "constant 2 (no mechanism claims a state)",
        },
        "unused_logged": ["G3_trend", "G4_corr"],
        "cap_single_leg": 0.5,
        "law": "state for week W uses data strictly before W Monday 00:00 UTC",
    }
    return table


def weights_for_week(monday, table, series) -> dict:
    mult = {}
    g1 = _tercile(last_before(series["G1"], monday), table["cuts"]["G1_funding_z"])
    g2c = _tercile(last_before(series["G2c"], monday), table["cuts"]["G2c_btc_rv"])
    g2f = _tercile(last_before(series["G2f"], monday), table["cuts"]["G2f_eur_rv"])
    mult["FUNDCONTRA"] = g1
    mult["CORRBREAK"] = g2c
    mult["PDHLSWEEPFX"] = g2f
    mult["ASIANRANGE"] = 4 - g2f
    mult["LONDONMOM"] = 4 - g2f
    mult["WEEKEND"] = 2
    total = sum(mult.values())
    w = {k: min(v / total, table["cap_single_leg"]) for k, v in mult.items()}
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}


def run_combo(mode: str = "scored", out_dir: str | None = None, seed: int = 20260928):
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from run_dt100 import src  # reuse loaders/cache

    ctrl = Path(config.WT).parent.parent / "research/control/REGIME-GATED-COMBO-V1"
    ctrl = Path(str(ctrl).replace("/integration/research", ""))
    ctrl = Path("/Users/hoangminhlong/my-quantitative/.worktrees/regime-gated-combo-v1/integration/research/control/REGIME-GATED-COMBO-V1")
    ctrl.mkdir(parents=True, exist_ok=True)

    fx = src("eur")
    rt_fx = 2 * float(np.median(fx["spread_bps"][
        (fx["ts"] >= FX_WARM[0]) & (fx["ts"] <= FX_WARM[1])].dropna()))
    table = build_gate_table(src, rt_fx)
    (ctrl / "GATE_TABLE.json").write_text(json.dumps(table, indent=1))

    series = {
        "G1": funding_z_series(src("funding_btc")),
        "G2c": daily_rv(src("btc1m")),
        "G2f": daily_rv(fx),
    }
    legs_wk: dict[str, pd.Series] = {}
    for leg in LEGS:
        fam, kind, srck, p, sym, asset, extra = leg
        df = src(srck)
        built = build_leg_pos(leg, df, src)
        if isinstance(built, tuple):
            pos, mark = built
        else:
            pos, mark = built, df
        funding = src("funding_btc") if fam == "FUNDCONTRA" else None
        stats, tr = run_arm(mark, pos, FOLDS, asset, sym, warmup_end=config.CRYPTO_WARMUP[1],
                            funding=funding, return_trades=True)
        legs_wk[fam] = leg_weekly_pnl(tr)

    mondays = week_mondays()
    wts = {m: weights_for_week(m, table, series) for m in mondays}

    rng = np.random.default_rng(seed)
    combos = {"GATED": [], "ALWAYS_ON": [], "RANDOM": [], "BEST_LEG": [], "CLOCK": []}
    prev_w = {k: 1 / 6 for k in [l[0] for l in LEGS]}
    prev_wr = dict(prev_w)
    prev_wc = dict(prev_w)
    for m in mondays:
        legs_this = {f: legs_wk[f].get(m, 0.0) for f in legs_wk}
        # GATED
        w = wts[m]
        switch = sum(abs(w[f] - prev_w[f]) * (table["rt_bps"]["crypto"] if f in
                     ("FUNDCONTRA", "WEEKEND", "CORRBREAK") else rt_fx) for f in w)
        combos["GATED"].append(sum(w[f] * legs_this[f] for f in w) - switch)
        prev_w = w
        # ALWAYS_ON
        combos["ALWAYS_ON"].append(sum((1 / 6) * legs_this[f] for f in legs_this))
        # RANDOM (same switch cost discipline)
        wr = {}
        for f in legs_this:
            wr[f] = float(rng.integers(1, 4))
        s = sum(wr.values())
        wr = {k: min(v / s, table["cap_single_leg"]) for k, v in wr.items()}
        sw = sum(abs(wr[f] - prev_wr[f]) * (table["rt_bps"]["crypto"] if f in
               ("FUNDCONTRA", "WEEKEND", "CORRBREAK") else rt_fx) for f in wr)
        combos["RANDOM"].append(sum(wr[f] * legs_this[f] for f in wr) - sw)
        prev_wr = wr
        # BEST_LEG (CORRBREAK w=1)
        combos["BEST_LEG"].append(legs_this.get("CORRBREAK", 0.0))
    combos["CLOCK"] = clock_shadow_series(legs_wk, wts, table, rt_fx, mondays, seed)

    folds_idx = {name: (pd.Timestamp(a, tz="UTC"), pd.Timestamp(b, tz="UTC") + pd.Timedelta(days=1))
                 for name, a, b in FOLDS}
    result = {}
    for name, vals in combos.items():
        s = pd.Series(vals, index=monds)
        per = {fn: float(s[(s.index >= a) & (s.index < b)].sum())
               for fn, (a, b) in folds_idx.items()}
        result[name] = {"total_bps": float(s.sum()), "per_fold": per,
                        "weeks": int(len(s))}
    verdict = {
        "beats_always_on": result["GATED"]["total_bps"] > result["ALWAYS_ON"]["total_bps"],
        "beats_random": result["GATED"]["total_bps"] > result["RANDOM"]["total_bps"],
        "beats_best_leg": result["GATED"]["total_bps"] > result["BEST_LEG"]["total_bps"],
        "beats_clock": result["GATED"]["total_bps"] > result["CLOCK"]["total_bps"],
        "folds_beating_always_on": sum(1 for fn in folds_idx
                                       if result["GATED"]["per_fold"][fn] > result["ALWAYS_ON"]["per_fold"][fn]),
    }
    verdict["PASS_ALL_BASELINES"] = all([verdict["beats_always_on"], verdict["beats_random"],
                                         verdict["beats_best_leg"], verdict["beats_clock"]])
    payload = {"mode": mode, "gate_table_ref": "GATE_TABLE.json",
               "disclosure": "legs individually dead (DT100 REJECT_ALL); conditional-allocation identity",
               "combos": result, "verdict": verdict, "weights_first3": {str(m): wts[m] for m in mondays[:3]}}
    out = Path(out_dir or (ctrl / ("dry_run" if mode == "dry" else "scored")))
    out.mkdir(parents=True, exist_ok=True)
    (out / f"rgc100_{mode}.json").write_text(json.dumps(payload, indent=1, default=str))
    if mode == "dry":
        dry = {"weeks": len(mondays), "legs": sorted(legs_wk),
               "weeks_with_trades": {f: int((legs_wk[f] != 0).sum()) for f in legs_wk},
               "gate_cuts": table["cuts"], "rt_fx": rt_fx,
               "note": "NO PnL in dry mode"}
        (out / "rgc100_dry_summary.json").write_text(json.dumps(dry, indent=1))
        print(json.dumps(dry, indent=1))
    else:
        print(json.dumps({"verdict": verdict, "totals": {k: v["total_bps"] for k, v in result.items()}}, indent=1))
    return payload


def clock_shadow_series(legs_wk, wts, table, rt_fx, mondays, seed):
    """Same allocation-change schedule; the STATE driving each week's weights is
    block-shuffled (13-week blocks) — Q-7: how much is pure schedule/clock."""
    rng = np.random.default_rng(seed + 1)
    wks = list(mondays)
    blocks = [wks[i:i + 13] for i in range(0, len(wks), 13)]
    shuffled = []
    for b in blocks:
        shuffled += list(rng.permutation(b))
    remap = dict(zip(wks, shuffled))
    out, prev = [], {k: 1 / 6 for k in legs_wk}
    for m in wks:
        w = wts[remap[m]]
        switch = sum(abs(w[f] - prev[f]) * (table["rt_bps"]["crypto"] if f in
                     ("FUNDCONTRA", "WEEKEND", "CORRBREAK") else rt_fx) for f in w)
        out.append(sum(w[f] * legs_wk[f].get(m, 0.0) for f in w) - switch)
        prev = w
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dry", "scored"], default="dry")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    run_combo(a.mode, a.out)
