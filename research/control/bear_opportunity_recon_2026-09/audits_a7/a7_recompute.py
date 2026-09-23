"""A7 fresh-context recomputation of A4's decisive numbers (FINAL, corrected).

Light jobs only: reads staged parquets (~25 MB) + keyless HTTP HEAD probes.
NOTE: the panel's index PRICE column must be read as m5["index"]; m5.index is
the pandas row index (v1 of this script had that bug; v2+ corrected).
Writes a7_recompute_out.json. No PnL, no fees, no scoring.
"""
import pandas as pd, numpy as np, json, datetime as dt

BASE = "/Users/hoangminhlong/my-quantitative/research/control/bear_opportunity_recon_2026-09"
K4 = f"{BASE}/killer_a4"
out = {}
tr = pd.read_parquet(f"{K4}/a4_B_trades.parquet"); m5 = pd.read_parquet(f"{K4}/m5_panel.parquet")
h4 = pd.read_parquet(f"{K4}/h4_rebuilt.parquet"); ep = pd.read_parquet(f"{K4}/a4_A_episodes.parquet")
S = m5.S.values; last = m5.last.values; mark = m5.mark.values
ix = m5["index"].values; ot = m5.open_time.values
base = int(ot[0]); step = 4 * 3600 * 1000; phase = h4.phase.values
gidx = ((ot - base) // step).astype(int) - 1                      # last CLOSED H4
g = np.zeros(len(m5), bool); ok = (gidx >= 0) & (gidx < len(phase))
g[ok] = phase[gidx[ok]] == "DOWNTREND"
sig = tr.sig_i.values
entry = np.zeros(len(m5)); entry[sig] = 1.0
win = np.zeros(len(m5), bool)
for i in sig: win[max(0, i - 36): i + 37] = True
def P(a, b, mask):
    x, y = a[mask], b[mask]; m = np.isfinite(x) & np.isfinite(y)
    return round(float(np.corrcoef(x[m], y[m])[0, 1]), 4) if m.sum() > 10 else None

# B: events / clusters / window
out["theta_raw_recomputed"] = int(((S[1:] >= 0.0012) & (S[:-1] >= 0.0012)).sum())
out["theta_in_gate_recomputed"] = int(g[sig].all()) and len(sig)
_rawset = set((np.where((S[1:] >= 0.0012) & (S[:-1] >= 0.0012))[0] + 1).tolist())
out["theta_signal_set_matches_file"] = bool(set(sig.tolist()) <= _rawset)
out["theta_raw_recomputed_n"] = len(_rawset)
out["theta_in_gate_recomputed_n"] = int(len([i for i in _rawset if g[i]]))
cl = tr.groupby("cluster").size().sort_values(ascending=False)
out["n_trades"] = int(len(tr)); out["n_clusters"] = int(tr.cluster.nunique())
out["top1_share"] = round(float(cl.iloc[0] / len(tr)), 4); out["top3_share"] = round(float(cl.iloc[:3].sum() / len(tr)), 4)
tt = ot[tr.loc[tr.cluster == cl.index[0], "sig_i"].values]
f = lambda ms: dt.datetime.fromtimestamp(int(ms) / 1000, dt.UTC).strftime("%Y-%m-%d %H:%M")
out["top1_cluster_window_utc"] = [f(tt.min()), f(tt.max())]
# B: matched pairs (control: in-gate, r5<=-0.3%, S<theta; nearest |r5| within +/-7d; same hold)
r5 = np.full(len(m5), np.nan); r5[1:] = last[1:] / last[:-1] - 1.0
ctl = np.where(g & (r5 <= -0.003) & (S < 0.0012) & np.isfinite(r5))[0]
fills = tr.fill_i.values; exits = tr.exit_i.values; r5e = tr.r5m_entry.values
diffs = []; worse = 0
for k in range(len(tr)):
    cand = ctl[(ctl >= sig[k] - 2016) & (ctl <= sig[k] + 2016)]
    if not len(cand): continue
    j = cand[np.argmin(np.abs(r5[cand] - r5e[k]))]
    hold = exits[k] - fills[k]; cf = min(j + 1, len(last) - 1)
    d = -(last[min(fills[k] + hold, len(last) - 1)] / last[fills[k]] - 1) + (last[min(cf + hold, len(last) - 1)] / last[cf] - 1)
    diffs.append(d); worse += d < 0
diffs = np.array(diffs)
out["pairs"] = int(len(diffs)); out["pair_diff_mean_pp"] = round(float(diffs.mean() * 100), 3)
out["pair_diff_median_pp"] = round(float(np.median(diffs) * 100), 3); out["traded_worse_share"] = round(worse / len(diffs), 4)
out["control_n"] = int(len(ctl))
out["short_fwd_mean_pct"] = round(float(tr.short_fwd.mean() * 100), 3)
out["short_fwd_median_pct"] = round(float(tr.short_fwd.median() * 100), 3)
ex = tr[tr.cluster != cl.index[0]]
out["excl_top_cluster_short_fwd"] = [round(float(ex.short_fwd.mean() * 100), 2), round(float(ex.short_fwd.median() * 100), 2)]
# B: class-7 rho (premium := (last-index)/index)
with np.errstate(all="ignore"):
    prem = pd.Series((last - ix) / ix)
    out["rho_class7"] = {
        "LEVEL_full_gated": P(entry, prem.values, g),
        "LEVEL_event_cond": P(entry, prem.values, win),
        "S_vs_LEVEL_full": P(S, prem.values, np.isfinite(S) & np.isfinite(prem.values)),
        "IDENTITY_S_vs_fastdev_ema288": P(S, (prem - prem.ewm(span=288, adjust=False).mean()).values,
                                          np.isfinite(S) & np.isfinite((prem - prem.ewm(span=288, adjust=False).mean()).values)),
        "IDENTITY_S_vs_fastdev_ema144_12h_label": P(S, (prem - prem.ewm(span=144, adjust=False).mean()).values,
                                          np.isfinite(S) & np.isfinite((prem - prem.ewm(span=144, adjust=False).mean()).values)),
        "FADE_z576_lt-2_evcond": P(entry, np.where(np.isfinite(((prem - prem.rolling(576, min_periods=288).mean()) / prem.rolling(576, min_periods=288).std()).values) &
                                     (((prem - prem.rolling(576, min_periods=288).mean()) / prem.rolling(576, min_periods=288).std()).values < -2), 1.0, 0.0), win),
    }
# A: state machine / census / rho
lens = h4.lens_down.values.astype(bool); conj = lens & (phase != "DOWNTREND")
entries = []; armed = True
for i in range(len(h4)):
    if conj[i]:
        if armed: entries.append(i); armed = False
    else: armed = True
out["A_entries"] = len(entries)
ent = np.zeros(len(h4)); ent[entries] = 1.0
oks = np.isfinite(h4.sma200.values)
out["A_rho_vs_lens_full"] = P(ent, lens.astype(float), oks)
conf = ep[ep.outcome.isin(["confirmed_hold_done", "tu_exit"])]
out["A_confirming_fakeouts"] = [int(len(conf)), int(len(ep) - len(conf))]
out["A_median_conf_lag"] = float(conf.conf_lag.median())
sl = slice(153, None)
dtt = (phase[sl] == "DOWNTREND"); lnt = lens[sl]; N = int(dtt.sum()) and len(dtt)
out["census_trim153"] = {"N": N, "DT": int(dtt.sum()), "LENS": int(lnt.sum()),
    "agreement": round(((int((dtt & lnt).sum()) + int(((~dtt) & (~lnt)).sum())) / N), 4),
    "P_DT_and_not_lens": round(int((dtt & ~lnt).sum()) / N, 6),
    "P_lens_and_not_DT": round(int((lnt & ~dtt).sum()) / N, 6),
    "TU": int((phase[sl] == "TRANSITION_UNKNOWN").sum())}
a = json.load(open(f"{K4}/a4_rho_tables_a.json"))
out["A_full_grid_max_abs_pearson"] = round(max(abs(v["pearson"]) for v in a["A_full_grid"].values() if v["pearson"] is not None), 4)
json.dump(out, open(f"{BASE}/audits_a7/a7_recompute_out.json", "w"), indent=1)
print(json.dumps(out, indent=1))
