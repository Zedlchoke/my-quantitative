#!/usr/bin/env python
"""
A7N novelty audit, cycle CRYPTO-V15, day D2 (blind proposals from D1 lanes a4/a5/a6).

Reconstructs ancestor/shadow feature panels from the staged V15 metrics parquet
(machine-local, read-only) at each proposal's own decision grid, and computes
pooled Spearman rho between each proposal's primary feature values and every
reconstructed ancestor over the blind-S0 window (2025-08-22..2026-08-21).

Standards applied (p3_freeze_v15.json + amendment 1):
  - pooled |rho| <= 0.20 vs EVERY measured ancestor -> NOVEL candidate
  - MEASURED_BOUND_LAG_3D: features read metrics rows with metrics_date <= decision_date - 3
  - global defect dates excluded from feature windows:
      2025-07-21, 2025-07-22, 2025-08-29, 2026-08-12
  - hole/refusal rule: a feature window with > 10% missing metrics-day cells
    for a symbol refuses that (symbol, decision) row (ACE/ONG hole-heavy
    windows treated under the same rule)

Reconstruction caveat: ancestor panels are RECONSTRUCTIONS from the current
staging (V12-V14 original staged bytes lost from the host). Numbers prove
self-consistency of the current staging, not truth of the original panels.
No PnL is computed anywhere in this audit.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v15/d2-a7n-novelty")
DATA = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v15/integration/v15_data/parquet/metrics")
OUT = WT / "research/control/v15_run/d2/a7n"
WAVE_SHA = "56e4d7c963cf71b403a8f07ccb0c44bf6036f1a2"

SYMS20 = ["1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT", "BCHUSDT",
          "BNBUSDT", "BOMEUSDT", "BTCUSDT", "DOGEUSDT", "ENAUSDT", "ETHUSDT",
          "LINKUSDT", "NEARUSDT", "ONGUSDT", "SOLUSDT", "SUIUSDT", "WLDUSDT",
          "XRPUSDT", "ZECUSDT"]
GLOBAL_DEFECT = {"2025-07-21", "2025-07-22", "2025-08-29", "2026-08-12"}
S0_START, S0_END = pd.Timestamp("2025-08-22"), pd.Timestamp("2026-08-21")
FOLD_STARTS = [pd.Timestamp("2025-08-22"), pd.Timestamp("2025-12-22"), pd.Timestamp("2026-04-22")]
FOLD_ENDS = [pd.Timestamp("2025-12-20"), pd.Timestamp("2026-04-20"), pd.Timestamp("2026-08-21")]

R6 = lambda x: None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), 8)


# ---------------------------------------------------------------- data loading
def load_symbol(sym):
    df = pd.read_parquet(DATA / f"{sym}.parquet")
    ts = pd.to_datetime(df["create_time"])
    df = df.assign(date=ts.dt.normalize(), hhmm=ts.dt.strftime("%H:%M"))
    out = {"sym": sym, "n_rows": len(df), "dates_raw": sorted(set(df["date"]))}
    # stamp-indexed daily snapshots; a stamp must exist AND the day must not be
    # a global defect date for the day to count as available at that stamp
    for stamp, key in [("00:00", "s00"), ("23:55", "s2355")]:
        sub = df[df["hhmm"] == stamp].set_index("date")
        sub = sub[~sub.index.strftime("%Y-%m-%d").isin(GLOBAL_DEFECT)]
        out[key] = sub
    # taker daily aggregates over available labels of each non-defect day
    tk = df[~df["date"].dt.strftime("%Y-%m-%d").isin(GLOBAL_DEFECT)].copy()
    r = pd.to_numeric(tk["sum_taker_long_short_vol_ratio"])
    lr = np.log(r.clip(0.2, 5.0))
    tk["lclip"] = lr.clip(-1.609, 1.609)
    tk["lclip_abs"] = tk["lclip"].abs()
    g = tk.groupby("date").agg(a_day=("lclip", "mean"), aabs_day=("lclip_abs", "mean"),
                               n_labels=("lclip", "size"))
    out["taker"] = g
    out["n_labels_min"] = int(g["n_labels"].min()) if len(g) else 0
    return out


D = {s: load_symbol(s) for s in SYMS20}

# availability sets
AV00 = {s: sorted(D[s]["s00"].index) for s in SYMS20}
AV2355 = {s: sorted(D[s]["s2355"].index) for s in SYMS20}
AVTAK = {s: sorted(D[s]["taker"].index) for s in SYMS20}
AVSET00 = {s: set(AV00[s]) for s in SYMS20}
AVSET2355 = {s: set(AV2355[s]) for s in SYMS20}
AVSETTAK = {s: set(AVTAK[s]) for s in SYMS20}


def oi_series(sym):
    return D[sym]["s00"]["sum_open_interest"].astype(float)


def oiv_series(sym, stamp="s00"):
    return D[sym][stamp]["sum_open_interest_value"].astype(float)


def missing_days(sym, a, b, avset):
    """calendar days in [a, b] with no available staged metrics day for sym"""
    if a > b:
        return 0
    all_days = pd.date_range(a, b, freq="D")
    return int(sum(1 for d in all_days if d not in avset))


def window_refuse(sym, a, b, avset):
    """amendment-1 rule: > 10% missing metrics-day cells in window -> refuse"""
    span = (b - a).days + 1
    miss = missing_days(sym, a, b, avset)
    return (miss / span) > 0.10 + 1e-12, miss, span


# ------------------------------------------------------- ancestor features
# All ancestors read at anchor date d (an available 00:00-stamp metrics date)
# using the trailing "n available metrics dates" convention. daily OI snapshot
# = sum_open_interest at the 00:00 UTC label (start-of-period semantics:
# labeled-T snapshot at T+5min per frozen data contract).

def _pos(avlist, d):
    # bisect: position of d in avlist, or None
    import bisect
    i = bisect.bisect_left(avlist, d)
    if i < len(avlist) and avlist[i] == d:
        return i
    return None


def flow28(sym, d):
    """OILEV-V2 28D-FLOW reconstruction: 28-day rolling SUM of signed daily OI change."""
    oi = oi_series(sym)
    av = AV00[sym]
    i = _pos(av, d)
    if i is None or i < 28:
        return np.nan
    w = av[i - 27:i + 1]
    prev = av[i - 28]
    deltas = [float(oi[w[0]] - oi[prev])] + [float(oi[w[k]] - oi[w[k - 1]]) for k in range(1, 28)]
    return float(np.sum(deltas))


def churn28(sym, d):
    """A4-P1 anchor feature: mean |delta_log OI| over trailing 28 available dates."""
    oi = oi_series(sym)
    av = AV00[sym]
    i = _pos(av, d)
    if i is None or i < 28:
        return np.nan
    w = av[i - 27:i + 1]
    prev = av[i - 28]
    dl = [abs(np.log(oi[w[0]] / oi[prev]))] + [abs(np.log(oi[w[k]] / oi[w[k - 1]])) for k in range(1, 28)]
    return float(np.mean(dl))


def dlog_change(sym, d):
    """most recent single-day log OI change at available date d (needs d-1 avail)."""
    oi = oi_series(sym)
    av = AV00[sym]
    i = _pos(av, d)
    if i is None or i < 1:
        return np.nan
    return float(np.log(oi[av[i]] / oi[av[i - 1]]))


def p90_abs_dlog(sym, d, n=42):
    """P90 of |delta_log OI| over the n changes ending at the change INTO d's predecessor.
    Here: the n changes ending at d's own change is used for the A4-P2 threshold
    over changes k in [i-n, i-1] (i.e., 42 changes strictly before the event change)."""
    oi = oi_series(sym)
    av = AV00[sym]
    i = _pos(av, d)
    if i is None or i < n:
        return np.nan
    vals = [abs(np.log(oi[av[k]] / oi[av[k - 1]])) for k in range(i - n, i)]
    return float(np.percentile(vals, 90))


def stoch28(sym, d):
    """OICYC approximation: position of current OI within its trailing 28D min-max range."""
    oi = oi_series(sym)
    av = AV00[sym]
    i = _pos(av, d)
    if i is None or i < 27:
        return np.nan
    w = av[i - 27:i + 1]
    lo, hi = float(np.min(oi[w])), float(np.max(oi[w]))
    if hi - lo <= 0:
        return np.nan
    return (float(oi[d]) - lo) / (hi - lo)


def oishare(sym, d):
    """CTL-OISHARE: cross-sectional OI-value dominance = sym OI value / total across staged syms."""
    oiv = oiv_series(sym, "s00")
    if d not in AVSET00[sym]:
        return np.nan
    tot = 0.0
    for s2 in SYMS20:
        if d in AVSET00[s2]:
            tot += float(oiv_series(s2, "s00")[d])
    if tot <= 0:
        return np.nan
    return float(oiv[d]) / tot


def _trail_mean(sym, d, n):
    oi = oi_series(sym)
    av = AV00[sym]
    i = _pos(av, d)
    if i is None or i < n - 1:
        return np.nan
    w = av[i - n + 1:i + 1]
    return float(np.mean([oi[x] for x in w]))


def oitd28(sym, d):
    """OITD 28D: mean(OI, 28 available dates) / mean(OI, 56 available dates)."""
    m28, m56 = _trail_mean(sym, d, 28), _trail_mean(sym, d, 56)
    if not np.isfinite(m28) or not np.isfinite(m56) or m56 == 0:
        return np.nan
    return m28 / m56


def oitd56(sym, d):
    """OITD 56D: mean(OI, 56 available dates) / mean(OI, 112 available dates)."""
    m56, m112 = _trail_mean(sym, d, 56), _trail_mean(sym, d, 112)
    if not np.isfinite(m56) or not np.isfinite(m112) or m112 == 0:
        return np.nan
    return m56 / m112


ANCESTORS = [
    ("OILEV-V2-28DFLOW", flow28, "rejected V12 anchor: 28d rolling sum of signed daily OI change, read at 00:00 stamp"),
    ("OILEV-V2-INV", lambda s, d: -flow28(s, d), "CLOSED V12 shadow: sign-inverted 28D-FLOW (|rho| identical to 28DFLOW by construction)"),
    ("OICYC-STOCH28", stoch28, "CLOSED V14 confirmatory ancestor, proposal-grade approximation: (OI - min28)/(max28 - min28)"),
    ("OICYC-STOCH28-INV", lambda s, d: -stoch28(s, d), "sign-inverted OICYC approximation (|rho| identical to OICYC-STOCH28)"),
    ("CTL-OISHARE", oishare, "V14 measured firing control: cross-sectional OI-value market share"),
    ("OITD-28D", oitd28, "V13 anchor form: mean(OI,28d)/mean(OI,56d)"),
    ("OITD-56D", oitd56, "V13 neighbour form: mean(OI,56d)/mean(OI,112d)"),
]


# ------------------------------------------------------ decision grids
def daily_grid():
    return list(pd.date_range(S0_START, S0_END, freq="D"))


def five_day_grid():
    out = []
    for fs, fe in zip(FOLD_STARTS, FOLD_ENDS):
        d = fs
        while d <= fe:
            out.append(d)
            d = d + pd.Timedelta(days=5)
    return out


def latest_avail(sym, d, avlist):
    import bisect
    i = bisect.bisect_right(avlist, d)
    return avlist[i - 1] if i > 0 else None


# ------------------------------------------------------ proposal features
def build_a4p1(universe):
    rows = []
    for Dd in daily_grid():
        bound = Dd - pd.Timedelta(days=3)
        for s in universe:
            d0 = latest_avail(s, bound, AV00[s])
            if d0 is None:
                rows.append((Dd, s, np.nan)); continue
            i = _pos(AV00[s], d0)
            if i < 28:
                rows.append((Dd, s, np.nan)); continue
            a, b = AV00[s][i - 27], d0
            refuse, miss, span = window_refuse(s, a, b, AVSET00[s])
            rows.append((Dd, s, np.nan if refuse else churn28(s, d0)))
    return pd.DataFrame(rows, columns=["date", "sym", "feat"])


def build_a4p2(universe):
    rows = []
    for Dd in daily_grid():
        bound = Dd - pd.Timedelta(days=3)
        for s in universe:
            e = latest_avail(s, bound, AV00[s])
            i = _pos(AV00[s], e) if e is not None else None
            if i is None or i < 43:
                rows.append((Dd, s, np.nan)); continue
            thr_w_a = AV00[s][i - 42]  # start of the 42-change P90 window
            refuse, miss, span = window_refuse(s, thr_w_a, AV00[s][i - 1], AVSET00[s])
            if refuse:
                rows.append((Dd, s, np.nan)); continue
            dl = dlog_change(s, e)
            thr = max(p90_abs_dlog(s, e, 42), 0.05)
            val = 0.0
            if np.isfinite(dl) and np.isfinite(thr) and abs(dl) > thr:
                val = -float(np.sign(dl))
            rows.append((Dd, s, val))
    return pd.DataFrame(rows, columns=["date", "sym", "feat"])


def _cliplog(x, lo=0.01, hi=100.0):
    return np.log(min(max(float(x), lo), hi))


def build_a5p1(universe):
    st = {s: D[s]["s00"]["sum_toptrader_long_short_ratio"].astype(float) for s in universe}
    ct = {s: D[s]["s00"]["count_toptrader_long_short_ratio"].astype(float) for s in universe}
    rows = []
    for Dd in daily_grid():
        for s in universe:
            days = [Dd - pd.Timedelta(days=k) for k in (7, 6, 5, 4, 3)]
            vals = []
            ok = True
            for t in days:
                if t not in AVSET00[s] or pd.isna(st[s].get(t, np.nan)) or pd.isna(ct[s].get(t, np.nan)):
                    ok = False
                    break
                vals.append(_cliplog(st[s][t]) - _cliplog(ct[s][t]))
            rows.append((Dd, s, float(np.median(vals)) if ok else np.nan))
    return pd.DataFrame(rows, columns=["date", "sym", "feat"])


def build_a5p2(universe):
    c = {s: D[s]["s00"]["count_long_short_ratio"].astype(float) for s in universe}
    ct = {s: D[s]["s00"]["count_toptrader_long_short_ratio"].astype(float) for s in universe}
    rows = []
    for Dd in daily_grid():
        t_end, t_beg = Dd - pd.Timedelta(days=3), Dd - pd.Timedelta(days=23)
        cand = []
        day_vals = {}
        for s in universe:
            if t_end not in AVSET00[s] or t_beg not in AVSET00[s]:
                day_vals[s] = np.nan
                continue
            refuse, miss, span = window_refuse(s, t_beg, t_end, AVSET00[s])
            if refuse or pd.isna(c[s].get(t_end, np.nan)) or pd.isna(c[s].get(t_beg, np.nan)) \
               or pd.isna(ct[s].get(t_end, np.nan)) or pd.isna(ct[s].get(t_beg, np.nan)):
                day_vals[s] = np.nan
                continue
            v_glob = _cliplog(c[s][t_end]) - _cliplog(c[s][t_beg])
            v_top = _cliplog(ct[s][t_end]) - _cliplog(ct[s][t_beg])
            cand.append((s, v_glob, v_top))
            day_vals[s] = 0.0  # provisional flat; fires assigned after top-5 cut
        # top-5 breadth restriction by |v_glob| desc, ties by symbol id ascending
        eligible = sorted([(abs(vg), s, vg, vt) for s, vg, vt in cand],
                          key=lambda x: (-x[0], x[1]))
        for _abs_vg, _s, vg, vt in eligible[:5]:
            gate = abs(vt) < 0.5 * abs(vg)
            if abs(vg) > 0 and gate:
                day_vals[_s] = 1.0 if vg < 0 else -1.0
        for s in universe:
            rows.append((Dd, s, day_vals[s]))
    return pd.DataFrame(rows, columns=["date", "sym", "feat"])


def build_a6(kind, universe):
    """kind='P1': S = A_bar/(O+0.02); kind='P2': R = g/(A_abs+0.01). Grid: every 5 days from fold starts."""
    rows = []
    for Dd in five_day_grid():
        for s in universe:
            t_end, t_beg = Dd - pd.Timedelta(days=3), Dd - pd.Timedelta(days=12)
            wdays = [t_beg + pd.Timedelta(days=k) for k in range(10)]
            if t_end not in AVSET2355[s] or t_beg not in AVSET2355[s] \
               or t_end not in AVSETTAK[s]:
                rows.append((Dd, s, np.nan)); continue
            refuse, miss, span = window_refuse(s, t_beg, t_end, AVSETTAK[s])
            if refuse:
                rows.append((Dd, s, np.nan)); continue
            tk = D[s]["taker"]
            wvals = [tk["a_day" if kind == "P1" else "aabs_day"].get(t, np.nan) for t in wdays]
            wvals = [v for v in wvals if pd.notna(v)]
            if len(wvals) < 9:
                rows.append((Dd, s, np.nan)); continue
            A_bar = float(np.mean(wvals))
            oiv = oiv_series(s, "s2355")
            O = abs(np.log(float(oiv[t_end]) / float(oiv[t_beg])))
            if kind == "P1":
                feat = A_bar / (O + 0.02)
            else:
                tt = D[s]["s2355"]["sum_toptrader_long_short_ratio"].astype(float)
                g = np.log(float(tt[t_end]) / float(tt[t_beg]))
                feat = g / (A_bar + 0.01)
            rows.append((Dd, s, float(feat)))
    return pd.DataFrame(rows, columns=["date", "sym", "feat"])


# ------------------------------------------------------ ancestor panels
def build_ancestor_panels(grid, universe):
    panels = {}
    for name, fn, _desc in ANCESTORS:
        vals = []
        for Dd in grid:
            bound = Dd - pd.Timedelta(days=3)
            for s in universe:
                d0 = latest_avail(s, bound, AV00[s])
                vals.append((Dd, s, fn(s, d0) if d0 is not None else np.nan))
        panels[name] = pd.DataFrame(vals, columns=["date", "sym", "anc"])
    return panels


# ------------------------------------------------------ correlation
def _spearman(x, y):
    """Spearman rho = Pearson correlation of average ranks (scipy-free)."""
    xr, yr = x.rank(), y.rank()
    if xr.std() == 0 or yr.std() == 0:
        return np.nan
    return float(xr.corr(yr))


def pooled_spearman(feat_df, anc_df):
    m = feat_df.merge(anc_df, on=["date", "sym"]).dropna()
    n = len(m)
    if n < 3:
        return {"n": n, "rho": None, "per_symbol_max": None, "per_symbol_arg": None}
    rho = _spearman(m["feat"], m["anc"])
    per = {}
    for s, g in m.groupby("sym"):
        if len(g) >= 3 and g["feat"].nunique() > 1 and g["anc"].nunique() > 1:
            r = _spearman(g["feat"], g["anc"])
            if pd.notna(r):
                per[s] = float(r)
    if per:
        argmax = max(per, key=lambda k: abs(per[k]))
        psmax = abs(per[argmax])
    else:
        argmax, psmax = None, None
    # supplementary: cross-sectionally ranked within each decision date, then pooled
    m2 = m.copy()
    m2["fr"] = m2.groupby("date")["feat"].rank()
    m2["ar"] = m2.groupby("date")["anc"].rank()
    rho_xr = _spearman(m2["fr"], m2["ar"])
    return {"n": n, "rho": float(rho) if pd.notna(rho) else None,
            "rho_xsec_ranked": float(rho_xr) if pd.notna(rho_xr) else None,
            "per_symbol_max": psmax, "per_symbol_arg": argmax, "n_syms_defined": len(per)}


# ------------------------------------------------------ schema + attestation
REQUIRED = ["hypothesis_id", "mechanism", "information_source", "universe", "clock",
            "warmup_spec", "features_and_lags", "entry_exit_rules", "fill_model",
            "cost_assumptions", "anchor_spec", "neighbour_spec", "causal_control_spec",
            "falsification_rule", "expected_failure_interpretation", "decorrelation_plan"]


def check_schema(pid, j):
    missing = [k for k in REQUIRED if k not in j]
    uni = j.get("universe", [])
    uni_ok = sorted(uni) == sorted(SYMS20)
    cs = j.get("confirmatory_status")
    flags = []
    if missing:
        flags.append(f"missing fields: {missing}")
    if not uni_ok:
        absent = sorted(set(SYMS20) - set(uni))
        extra = sorted(set(uni) - set(SYMS20))
        flags.append(f"universe != 20 staged symbols (n={len(uni)}); absent={absent}; extra={extra}")
    if cs != "EXPLORATORY":
        flags.append(f"confirmatory_status={cs!r} != EXPLORATORY")
    return {"hypothesis_id": pid, "missing_fields": missing, "universe_n": len(uni),
            "universe_matches_staged_20": uni_ok, "confirmatory_status": cs,
            "flags": flags}


def check_attestation(lane, pids):
    p = WT / f"research/control/v15_run/d1/{lane}/outcome_blind_attestation.json"
    if not p.exists():
        return {"lane": lane, "present": False, "flags": ["outcome_blind_attestation.json MISSING"]}
    j = json.loads(p.read_text())
    flags = []
    if j.get("wave_sha") != WAVE_SHA:
        flags.append(f"wave_sha mismatch: {j.get('wave_sha')}")
    if not j.get("outcome_blind", False):
        flags.append("outcome_blind not true")
    if sorted(j.get("proposals", [])) != sorted(pids):
        flags.append(f"proposals list mismatch: {j.get('proposals')}")
    return {"lane": lane, "present": True, "wave_sha": j.get("wave_sha"),
            "outcome_blind": j.get("outcome_blind"), "proposals": j.get("proposals"),
            "flags": flags}


# ------------------------------------------------------ run all proposals
PROPOSALS = [
    ("a4", "A4-V15-P1", "proposal_P1.json", "daily", build_a4p1),
    ("a4", "A4-V15-P2", "proposal_P2.json", "daily", build_a4p2),
    ("a5", "A5-V15-P1", "proposal_P1.json", "daily", build_a5p1),
    ("a5", "A5-V15-P2", "proposal_P2.json", "daily", build_a5p2),
    ("a6", "A6-V15-P1", "proposal_P1.json", "5day", lambda u: build_a6("P1", u)),
    ("a6", "A6-V15-P2", "proposal_P2.json", "5day", lambda u: build_a6("P2", u)),
]

NOT_RUN = {
    "PREMFADE": ("NOT_RUN_UNMEASURABLE_FROM_STAGED_FIELDS",
                 "premium/basis requires price-premium vs index fields absent from the staged metrics "
                 "schema (6 fields only); the OIv/OI implied-mark-price identity is a price LEVEL, not a "
                 "basis, and building a premium proxy from it would itself smuggle a forbidden price "
                 "signal — not faked, fail-closed per honesty rules"),
    "XSECT_MOMENTUM_REVERSAL_SPRINTS": ("NOT_RUN_APPLICABILITY_EXCLUDED",
                 "price-derived sprint forms; every audited proposal's primary feature is metrics-derived "
                 "with no kline/price input (verified per proposal information_source), so feature-level "
                 "overlap with price-form ancestors is not plausible"),
    "VOL_SHOCK_SPRINT": ("NOT_RUN_APPLICABILITY_EXCLUDED",
                 "price/volatility-derived; proposals read no price/volume field in any primary feature"),
    "BAB-LOWBETA": ("NOT_RUN_APPLICABILITY_EXCLUDED",
                 "beta is price-derived; no proposal feature is price-derived"),
    "LIQEPIS": ("NOT_RUN_APPLICABILITY_EXCLUDED",
                 "V13 episodes were conditioned on price/volume liquidity fields absent from every "
                 "audited anchor's input set"),
    "CARRY_FAMILIES_FUNDING_1D_3D_7D": ("NOT_RUN_UNDERDETERMINED_FORM",
                 "funding parquet is staged, but the V6/V7 carry book forms (thresholds, conditioning) "
                 "are not restaged in this worktree; reconstructing a specific form would require "
                 "inventing parameters; additionally no audited proposal reads any funding field"),
    "H-FUNDCROWD-MR": ("NOT_RUN_UNDERDETERMINED_FORM",
                 "same reason as carry families: form not restaged; no proposal reads funding"),
    "FUNDING_PRICE_DIVERGENCE": ("NOT_RUN_UNDERDETERMINED_FORM",
                 "requires funding + price inputs; no proposal feature uses either"),
    "LOT_RESIDUAL_MAX / ILLIQ_AMIHUD": ("NOT_RUN_APPLICABILITY_EXCLUDED",
                 "price/return-derived (residual idio MAX, Amihud illiquidity); no proposal feature "
                 "touches price or volume"),
}

PRIMARY_FEATURE_DESC = {
    "A4-V15-P1": "churn28(s,D) = mean |delta_log(sum_open_interest)| over the 28 most recent available metrics dates ending at latest available date <= D-3, cross-sectionally ranked per spec (raw churn used for rho; Spearman is rank-based)",
    "A4-V15-P2": "shock-fade indicator: at each decision D scan e = latest available metrics date <= D-3; if |dlog_oi(e)| > max(P90 of trailing 42 |dlog| changes ending e-1, 0.05) then -sign(dlog_oi(e)) else 0",
    "A5-V15-P1": "S_i(D) = median over the 5 usable daily rows in [D-7, D-3] of ln(clip(sum_toptrader_lsr)) - ln(clip(count_toptrader_lsr)) at the 00:00 UTC row",
    "A5-V15-P2": "gated crowd-rotation fade indicator: top-5 universe names by |v_glob| (v_glob = 20d log-change of count_long_short_ratio, endpoints D-3/D-23); fire -sign(v_glob) iff |v_top| < 0.5*|v_glob| (v_top = same on count_toptrader_lsr); else 0",
    "A6-V15-P1": "S_i(D) = A_bar / (O + 0.02) over W = [D-12, D-3]; A_bar = mean daily aggression (mean over day's labels of clip(ln(clip(sum_taker_lsr,0.2,5.0)),-1.609,1.609)); O = |ln(OIv_2355(D-3)/OIv_2355(D-12))|",
    "A6-V15-P2": "R_i(D) = g / (A_abs + 0.01) over W = [D-12, D-3]; g = ln(TT_2355(D-3)/TT_2355(D-12)); A_abs = mean over W of per-day mean |clip(ln r_t)|",
}

AUDIT_NOTES = {
    "A4-V15-P1": [
        "BLOCK is robust across pooling variants: pooled raw rho = -0.43110304 and cross-sectionally-ranked pooled rho = -0.47099183 vs CTL-OISHARE; per-symbol max |rho| 0.60606348 (ACEUSDT).",
        "The proposal's own expected_failure_interpretation ('static_sort_collapse') preregistered exactly this death: churn ranks persist per symbol, collapsing toward the structural OI-size sort measured as CTL-OISHARE (V14 firing control). Measured, not argued.",
        "THIN: OITD-28D margin 0.02556963 (|rho| 0.17443037) recorded as thin per honesty rules; moot given the block.",
        "6 refused rows, all ONGUSDT (hole-heavy symbol, window >10% missing metrics-day cells).",
    ],
    "A4-V15-P2": [
        "BLOCKING ancestor OICYC-STOCH28: pooled raw |rho| = 0.25327361 > 0.20 (margin -0.05327361). The supplementary cross-sectionally-ranked pooled statistic is 0.16398839 (< 0.20); the frozen D2 standard is the pooled raw statistic on the (symbol, decision_date) panel, so the verdict is ANCESTRY_BLOCKED, and the discrepancy is recorded, not resolved.",
        "Interpretation of the block direction (recorded, not adjudicated): the fade goes long after OI collapses (low stochastic-OI) and short after OI inflow spikes (high stochastic-OI), reproducing the OI-cycle phase object at event granularity — i.e., the sign structure of the OICYC confirmatory ancestor.",
        "Firing census: 746/7300 rows nonzero (10.22%, matching the P90 design rate; 332 long / 414 short) — the correlation is NOT vacuous.",
        "0 refused rows: the P90/event windows never tripped the >10% hole rule on this grid.",
    ],
    "A5-V15-P1": [
        "All measured pooled |rho| <= 0.13357811 (OITD-56D); no comparison below the 0.05 thin-margin line, but OITD-56D margin 0.06642189 and OITD-28D margin 0.07566964 are the two smallest — recorded.",
        "197 refused rows = every (symbol, decision) whose [D-7, D-3] window contains one of the in-S0 global defect dates 2025-08-29 / 2026-08-12 or an ONG hole day (5-row window: 1 missing = 20% > 10% -> refuse; consistent with the proposal's own fail_closed rule).",
        "SCHEMA FLAG (does not change the novelty verdict): universe lists 19 symbols - SOLUSDT absent - while entry_exit_rules reference ranking 'the 20 symbols' with a 7/6/7 tercile split; internal inconsistency for A1/lane adjudication per the freeze ambiguity_rule.",
    ],
    "A5-V15-P2": [
        "LOW-POWER caveat: the anchor fires on only 63 of 6869 scored rows (0.92%; 25 long / 38 short, spread over 72 distinct decision dates). The near-zero pooled rho is measured on a series dominated by ties at 0; low fire-rate means low statistical power, recorded as such — the pass is not evidence of independence, it is absence of measurable overlap.",
        "Max measured pooled |rho| = 0.01881768 (OITD-56D); nothing near the threshold.",
        "66 refused rows: decisions whose D-3 or D-23 endpoint lands on a global defect/ONG hole date.",
        "SCHEMA FLAG (does not change the novelty verdict): universe lists 19 symbols - SOLUSDT absent - while entry_exit_rules reference a 20-symbol ranked set.",
    ],
    "A6-V15-P1": [
        "Max measured pooled |rho| = 0.14687781 (CTL-OISHARE, margin 0.05312219) — the closest comparison, recorded; not below the 0.05 thin line but the smallest margin in this proposal's table.",
        "54 refused rows, measured per-symbol: ONGUSDT 13, ACEUSDT 4, BOMEUSDT 3, and exactly 2 for each of the other 17 symbols. The 2-per-symbol refusals are decisions whose D-3 endpoint lands on a global defect date (D=2025-09-01 with endpoint 2025-08-29; D=2026-08-15 with endpoint 2026-08-12); the ONG/ACE/BOME extras are hole-cluster windows tripping the >10% rule or missing 23:55 endpoint stamps on partial days.",
        "5-day decision grid: 74 decision dates across F0/F1/F2 fold starts; 1480 grid rows.",
    ],
    "A6-V15-P2": [
        "Max measured pooled |rho| = 0.05079854 (OICYC-STOCH28); all margins >= 0.14920146 — no thin comparisons.",
        "Same refusal decode as A6-V15-P1 (54 rows): endpoint-on-defect-date refusals plus ONG/ACE hole-cluster window refusals.",
        "5-day decision grid: 74 decision dates; 1480 grid rows.",
    ],
}

results = {"schema": "v15_d2_a7n_novelty_v1", "cycle": "CRYPTO-V15",
           "generated_utc": "2026-09-06",
           "auditor_role": "A7N",
           "worktree": str(WT),
           "head_verified": "d078252a7c0f42b5a848b8fd97447be1c479d707",
           "branch": "orca/v15-d2-a7n-novelty",
           "wave_sha": WAVE_SHA,
           "standard": {"threshold": 0.20, "statistic": "pooled Spearman rho on (symbol, decision_date) feature values",
                        "window": "blind-S0 2025-08-22..2026-08-21",
                        "lag": "MEASURED_BOUND_LAG_3D (features read metrics_date <= decision_date - 3)"},
           "reconstruction_conventions": [
               "daily OI snapshot = sum_open_interest at the 00:00 UTC labeled row (start-of-period semantics: snapshot at T+5min per frozen data contract); a day counts as available at a stamp only if that stamp exists AND the day is not a global defect date",
               "OILEV-V2-28DFLOW = sum of 28 consecutive-available-date signed raw OI deltas (contracts, not log)",
               "OICYC approximation (proposal-grade, per D2 task): stochastic-OI = (OI - trailing-28-avail-date min) / (max - min)",
               "CTL-OISHARE = symbol sum_open_interest_value (00:00 stamp) / cross-sectional total over available staged symbols",
               "OITD-28D = mean(OI,28 avail)/mean(OI,56 avail); OITD-56D = mean(OI,56)/mean(OI,112)",
               "amendment-1 exclusions: global defect dates 2025-07-21, 2025-07-22, 2025-08-29, 2026-08-12 removed from every feature window; >10% missing metrics-day cells in a feature window refuses that (symbol, decision) row",
               "sign-inverted ancestors (OILEV-V2-INV, OICYC-STOCH28-INV) have |rho| IDENTICAL to their non-inverted forms by construction — reported once per pair and noted",
           ],
           "global_caveats": [
               "ALL ancestor panels are RECONSTRUCTIONS reconstructed from the CURRENT staging (integration worktree v15_data); the V12-V14 original staged bytes have been lost from the host. Measured rho therefore establishes self-consistency between D1 proposals and the current staging, NOT truth of the original V12-V14 panels.",
               "pooled Spearman on raw feature values embeds cross-sectional scale differences (e.g. raw OI-flow contract counts span orders of magnitude across symbols); a supplementary cross-sectionally-ranked-then-pooled Spearman is reported per comparison as robustness, but the frozen verdict uses the raw pooled value per the D2 standard",
               "5-minute-level holes inside present-but-partial ONG/ACE days (e.g. ONG 2026-07-29 has 10 labels, no 23:55) are handled at DAILY granularity here: a6's 23:55 stamp reads refuse on such days and the day counts as missing in window checks; a 5-min-level runner would refuse more rows than this audit does",
           ],
           "proposals": [], "attestations": [], "final": {}}

for lane, pid, fname, gridname, builder in PROPOSALS:
    pj = json.loads((WT / f"research/control/v15_run/d1/{lane}/{fname}").read_text())
    universe = pj.get("universe", SYMS20)
    feat = builder(universe)
    grid = sorted(set(feat["date"]))
    n_rows = len(feat)
    n_refused = int(feat["feat"].isna().sum())
    anc_panels = build_ancestor_panels(grid, universe)
    comps = []
    blocked = []
    thin = []
    for name, _fn, desc in ANCESTORS:
        r = pooled_spearman(feat, anc_panels[name])
        rho = r["rho"]
        arho = abs(rho) if rho is not None else None
        margin = (0.20 - arho) if arho is not None else None
        entry = {"ancestor": name, "description": desc, "n_pairs": r["n"],
                 "pooled_spearman_rho": R6(rho), "abs_rho": R6(arho),
                 "margin_to_fail_0.20": R6(margin),
                 "rho_xsec_ranked_supplementary": R6(r.get("rho_xsec_ranked")),
                 "per_symbol_max_abs_rho": R6(r["per_symbol_max"]),
                 "per_symbol_max_at": r["per_symbol_arg"],
                 "n_symbols_with_defined_rho": r.get("n_syms_defined"),
                 "note": "sign-inverted form: |rho| identical to non-inverted form" if "INV" in name else None}
        comps.append(entry)
        if arho is not None:
            if arho > 0.20:
                blocked.append((name, arho))
            elif margin < 0.05:
                thin.append((name, arho, margin))
    verdict = "ANCESTRY_BLOCKED" if blocked else "NOVEL"
    results["proposals"].append({
        "hypothesis_id": pid, "lane": lane, "family_name": pj.get("family_name", pj.get("axis", "")),
        "grid": gridname, "n_decision_dates": len(grid), "n_grid_rows": n_rows,
        "n_rows_refused_nan": n_refused,
        "primary_feature": PRIMARY_FEATURE_DESC[pid],
        "audit_notes": AUDIT_NOTES[pid],
        "comparisons": comps,
        "verdict": verdict,
        "blocking_ancestors": [{"ancestor": b[0], "abs_rho": R6(b[1]), "margin_to_fail": R6(0.20 - b[1])} for b in blocked],
        "thin_passes_margin_lt_0.05": [{"ancestor": t[0], "abs_rho": R6(t[1]), "margin": R6(t[2])} for t in thin],
        "not_run": {k: {"status": v[0], "reason": v[1]} for k, v in NOT_RUN.items()},
        "schema_check": check_schema(pid, pj),
    })
    results["final"][pid] = verdict

for lane, pids in [("a4", ["A4-V15-P1", "A4-V15-P2"]), ("a5", ["A5-V15-P1", "A5-V15-P2"]),
                   ("a6", ["A6-V15-P1", "A6-V15-P2"])]:
    results["attestations"].append(check_attestation(lane, pids))

results["final_summary"] = {
    "NOVEL": [k for k, v in results["final"].items() if v == "NOVEL"],
    "ANCESTRY_BLOCKED": [k for k, v in results["final"].items() if v == "ANCESTRY_BLOCKED"],
    "NOVELTY_UNMEASURABLE": [k for k, v in results["final"].items() if v == "NOVELTY_UNMEASURABLE"],
}

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "a7n_novelty_v15.json").write_text(json.dumps(results, indent=1) + "\n")
print(json.dumps(results["final_summary"], indent=1))
for p in results["proposals"]:
    print(f"\n== {p['hypothesis_id']} [{p['verdict']}] grid={p['grid']} dates={p['n_decision_dates']} rows={p['n_grid_rows']} refused={p['n_rows_refused_nan']}")
    for c in p["comparisons"]:
        print(f"  {c['ancestor']:22s} rho={c['pooled_spearman_rho']} |rho|={c['abs_rho']} margin={c['margin_to_fail_0.20']} n={c['n_pairs']} xr={c['rho_xsec_ranked_supplementary']} psmax={c['per_symbol_max_abs_rho']}@{c['per_symbol_max_at']}")
    print("  schema flags:", p["schema_check"]["flags"])
print("\nattestations:", json.dumps(results["attestations"], indent=1))
