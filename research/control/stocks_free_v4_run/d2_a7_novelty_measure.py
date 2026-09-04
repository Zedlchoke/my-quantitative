#!/usr/bin/env python
"""A7-N V4-D2 feature-space measurement (read-only, no PnL, no backtest).

Computes, at sample decision dates across S0, each blind proposal's intended
long-direction ranking score and its Spearman rank correlation against two
forbidden reference rankings:
  REF-MOM : plain 12-1 cross-sectional momentum (adj close t-252 -> t-21)
  REF-VOL : plain close-to-close realized volatility (RMS daily return, 252 sessions)
plus targeted redundancy/descent diagnostics.
Snapshot: stocks-free-v2 z8-exec-1 .staging (authorized S0 snapshot).
"""
import json
import math
import numpy as np
import pandas as pd

STAGING = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1/.staging"
SECTORS = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
S0_START, S0_END = "2018-04-04", "2025-07-31"


def load(sym, kind):
    """Return DataFrame indexed by ascending date with float columns."""
    d = json.load(open(f"{STAGING}/{sym}_{kind}_p1.json"))
    rows = d["values"][::-1]  # ascending
    df = pd.DataFrame(rows)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime")
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


spy_all = load("SPY", "all")
calendar = spy_all.index  # ascending, full history 2010-01-04 .. 2026-08-27
ALL = {s: load(s, "all") for s in SECTORS}
NONE = {s: load(s, "none") for s in SECTORS}

# --- per-symbol aligned frames on the SPY calendar (symbol's own observed dates) ---
def sym_series(sym, col, kind="all"):
    df = ALL[sym] if kind == "all" else NONE[sym]
    return df[col]

# Sample decision dates: every 126th SPY session within S0 starting at S0 start.
s0_mask = (calendar >= S0_START) & (calendar <= S0_END)
s0_idx = np.where(s0_mask)[0]
sample_pos = list(range(0, len(s0_idx), 126))
sample_dates = [calendar[s0_idx[p]] for p in sample_pos]

WARM = 252  # strictest common requirement (mom121, vov, rv252, shock)

def r_cc(adj_close):  # close-to-close simple returns
    return adj_close.pct_change()

def last_n(series, d, n):
    s = series.loc[:d]
    return s.iloc[-n:]

def compute_row(sym, d):
    a = ALL[sym]; n = NONE[sym]
    a_to = a.loc[:d]; n_to = n.loc[:d]
    if len(a_to) < WARM + 1 or len(n_to) < WARM + 1:
        return None
    ac = a_to["close"]
    r = r_cc(ac)
    r252 = r.iloc[-252:]
    # REF-MOM: 12-1 momentum
    mom121 = ac.iloc[-21] / ac.iloc[-252] - 1.0
    # REF-VOL: realized vol level, RMS daily return over 252
    rv252 = math.sqrt(float(np.mean(r252.values ** 2)))
    mom21 = ac.iloc[-1] / ac.iloc[-21] - 1.0
    # A4-H1: semivariance share over 126
    r126 = r.iloc[-126:].values
    ss = float(np.sum(r126 ** 2)); ds = float(np.sum(r126[r126 < 0] ** 2))
    S126 = ds / ss if ss > 0 else np.nan
    # A4-H2: vol-of-vol = std of 12 non-overlapping 21-session block RMS vols over 252
    blocks = [r252.values[i * 21:(i + 1) * 21] for i in range(12)]
    vols = [math.sqrt(float(np.mean(b ** 2))) for b in blocks]
    vov = float(np.std(vols, ddof=1))
    # A5-H1: dollar-volume participation shock 21/231 on raw path
    dv = (n_to["close"] * n_to["volume"])
    num = float(dv.iloc[-21:].mean()); den = float(dv.iloc[-251:-21].mean())
    shock = num / den if den > 0 else np.nan
    # A5-H1 stale control: same feature one holding period (63 sessions) back
    if len(dv) >= 251 + 63:
        dv_lag = dv.iloc[:-63]
        num_l = float(dv_lag.iloc[-21:].mean()); den_l = float(dv_lag.iloc[-251:-21].mean())
        shock_stale = num_l / den_l if den_l > 0 else np.nan
    else:
        shock_stale = np.nan
    # A5-H2: follow-through and effective score
    follow21 = abs(ac.iloc[-1] / ac.iloc[-21] - 1.0)
    # A6-H1: Garman-Klass variance over 63 valid sessions (raw OHLC)
    gk_terms = []
    idx = n_to.index
    o, h, l, c = n_to["open"].values, n_to["high"].values, n_to["low"].values, n_to["close"].values
    for j in range(len(idx) - 1, -1, -1):
        if len(gk_terms) >= 63:
            break
        if min(o[j], h[j], l[j], c[j]) > 0 and h[j] > 0 and l[j] > 0 and o[j] > 0 and c[j] > 0:
            gk_terms.append(0.5 * math.log(h[j] / l[j]) ** 2 - (2 * math.log(2) - 1) * math.log(c[j] / o[j]) ** 2)
    gk63 = float(np.mean(gk_terms)) if len(gk_terms) >= 63 else np.nan
    # A6-H1 redundancy target: close-to-close variance over same 63 sessions (adjusted)
    cc63 = float(np.sum(r.iloc[-63:].values ** 2))
    # A6-H2: overnight variance share over 63 sessions (adjusted open/close)
    ao = a_to["open"]
    r_on_vals, r_in_vals = [], []
    ac_vals = ac.values; ao_vals = ao.values
    for j in range(len(ac_vals) - 63, len(ac_vals)):
        prev_c = ac_vals[j - 1]
        if prev_c > 0 and ao_vals[j] > 0:
            r_on_vals.append(ao_vals[j] / prev_c - 1.0)
            r_in_vals.append(ac_vals[j] / ao_vals[j] - 1.0)
    von = float(np.sum(np.array(r_on_vals) ** 2)); vin = float(np.sum(np.array(r_in_vals) ** 2))
    onshare63 = von / (von + vin) if (von + vin) > 1e-12 else np.nan
    return dict(sym=sym, date=str(d.date()), mom121=mom121, mom21=mom21, rv252=rv252,
                S126=S126, vov=vov, shock=shock, shock_stale=shock_stale,
                follow21=follow21, gk63=gk63, cc63=cc63, onshare63=onshare63)


rows = []
for d in sample_dates:
    for s in SECTORS:
        row = compute_row(s, d)
        if row:
            rows.append(row)
T = pd.DataFrame(rows)

# long-direction scores (higher = more long)
T["sc_a4h1"] = T["S126"]                     # long high semivariance share
T["sc_a4h2"] = -T["vov"]                     # long low vol-of-vol
T["sc_a5h1"] = T["shock"]                    # long high participation shock
# A5-H2 effective score: +shock if quiet (follow <= per-date median) else -shock
T["median_follow"] = T.groupby("date")["follow21"].transform(lambda x: x.median())
T["sc_a5h2"] = np.where(T["follow21"] <= T["median_follow"], T["shock"], -T["shock"])
T["sc_a5h2ctrl"] = -T["follow21"]            # long quiet / short movers (price-only)
T["sc_a6h1"] = -T["gk63"]                    # long low range-vol
T["sc_a6h2"] = -T["onshare63"]               # long low overnight share
T["sc_a6h2ctrl"] = -T["cc63"]                # long low cc variance (H2 control = H1 anchor class)

def spearman(x, y):
    return float(pd.Series(x).rank().corr(pd.Series(y).rank()))

def per_date_stats(col, ref):
    out = []
    for d, g in T.groupby("date"):
        g = g.dropna(subset=[col, ref])
        if len(g) >= 8:
            out.append((d, len(g), spearman(g[col].values, g[ref].values)))
    return out

def summarize(col):
    res = {}
    for ref, refname in [("mom121", "REF-MOM(12-1)"), ("rv252", "REF-VOL(252)")]:
        stats = per_date_stats(col, ref)
        rhos = [r for _, _, r in stats]
        res[refname] = {
            "n_dates": len(rhos),
            "mean_rho": round(float(np.mean(rhos)), 3),
            "min_rho": round(float(np.min(rhos)), 3),
            "max_rho": round(float(np.max(rhos)), 3),
            "n_dates_abs_ge_0.9": int(sum(abs(r) >= 0.9 for r in rhos)),
            "n_dates_abs_ge_0.8": int(sum(abs(r) >= 0.8 for r in rhos)),
            "per_date": {d: round(r, 3) for d, n, r in stats},
        }
    # pooled feature-space correlation across all date x sector observations
    g = T.dropna(subset=[col, "mom121"])
    res["pooled_rho_vs_mom121"] = round(spearman(g[col].values, g["mom121"].values), 3)
    g2 = T.dropna(subset=[col, "rv252"])
    res["pooled_rho_vs_rv252"] = round(spearman(g2[col].values, g["rv252"].values), 3)
    return res

results = {}
for col, name in [("sc_a4h1", "A4-H1_semivar_share"), ("sc_a4h2", "A4-H2_neg_vov"),
                  ("sc_a5h1", "A5-H1_participation_shock"), ("sc_a5h2", "A5-H2_shock_x_quiet_eff"),
                  ("sc_a5h2ctrl", "A5-H2_ctrl_neg_follow"), ("sc_a6h1", "A6-H1_neg_gk63"),
                  ("sc_a6h2", "A6-H2_neg_onshare63"), ("sc_a6h2ctrl", "A6-H2_ctrl_neg_cc63"),
                  ("shock_stale", "A5-H1_ctrl_stale_shock")]:
    results[name] = summarize(col)

# targeted diagnostics
diag = {}
# reference entanglement: REF-VOL vs REF-MOM
res = per_date_stats("rv252", "mom121")
diag["REFVOL_vs_REFMOM_per_date"] = {d: round(r, 3) for d, n, r in res}
diag["REFVOL_vs_REFMOM_mean"] = round(float(np.mean([r for _, _, r in res])), 3)
# A6-H1 anchor vs A6-H2 control (estimator redundancy, same 63 window)
res = per_date_stats("sc_a6h1", "sc_a6h2ctrl")
diag["A6H1_anchor_vs_A6H2_ctrl_mean_rho"] = round(float(np.mean([r for _, _, r in res])), 3)
diag["A6H1_anchor_vs_A6H2_ctrl_min"] = round(float(np.min([r for _, _, r in res])), 3)
# A6-H2 anchor vs its own control
res = per_date_stats("sc_a6h2", "sc_a6h2ctrl")
diag["A6H2_anchor_vs_own_ctrl_mean_rho"] = round(float(np.mean([r for _, _, r in res])), 3)
# A5-H1 anchor vs its stale control (control adequacy / persistence)
res = per_date_stats("sc_a5h1", "shock_stale")
diag["A5H1_anchor_vs_stale_ctrl_mean_rho"] = round(float(np.mean([r for _, _, r in res])), 3)
# A5-H2 anchor vs its quietness control
res = per_date_stats("sc_a5h2", "sc_a5h2ctrl")
diag["A5H2_anchor_vs_quiet_ctrl_mean_rho"] = round(float(np.mean([r for _, _, r in res])), 3)
# A5-H2 quietness axis vs signed short-horizon momentum (mom21)
res = per_date_stats("sc_a5h2ctrl", "mom21")
diag["A5H2_ctrl_negfollow_vs_mom21_mean_rho"] = round(float(np.mean([r for _, _, r in res])), 3)
# A5-H2 descent overlap: share of dates where the anchor's short basket (top-3 shock among confirmed)
# contains >=2 of top-3 mom21 sectors
overlaps = []
for d, g in T.groupby("date"):
    g = g.dropna(subset=["shock", "follow21", "mom21"])
    if len(g) < 8:
        continue
    med = g["follow21"].median()
    confirmed = g[g["follow21"] > med]
    short_basket = set(confirmed.nlargest(3, "shock")["sym"])
    top_mom = set(g.nlargest(3, "mom21")["sym"])
    overlaps.append(len(short_basket & top_mom))
diag["A5H2_shortbasket_vs_top3mom21_overlap_counts"] = overlaps
diag["A5H2_shortbasket_mean_overlap_of_3"] = round(float(np.mean(overlaps)), 3)
# A4-H1 long basket vs bottom-momentum: is long-high-S long-recent-losers?
res = per_date_stats("sc_a4h1", "mom121")
diag["A4H1_score_vs_mom121_per_date"] = {d: round(r, 3) for d, n, r in res}

# sample-date metadata
results["_meta"] = {
    "sample_dates": [str(d.date()) for d in sample_dates],
    "names_per_date": {str(d.date()): int((T["date"] == str(d.date())).sum()) for d in sample_dates},
    "note": "Spearman on 10-11 sector cross-section per date; XLC excluded before 252-session eligibility",
}

out = {"schema": "stocks_free_v4_run/d2_a7_novelty_measure@1", "results": results, "diagnostics": diag}
print(json.dumps(out, indent=1))
with open("/tmp/a7n_measure.json", "w") as f:
    json.dump(out, f, indent=1)
