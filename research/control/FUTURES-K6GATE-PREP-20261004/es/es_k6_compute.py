#!/usr/bin/env python
"""
ES-K6 lane, FUTURES-K6GATE-PREP-20261004 — 0-cost anatomy gates (K6-class) on
committed data. UNCONDITIONAL descriptive statistics only: no PnL, no
expectancy, no conditional-on-signal measurement, no sign/return-direction
statistic of any kind. Every statistic computed here is pre-declared in
ES_K6_GATES.md §0 (written before this script was first run) as amended in
§0.8 (implementation-discovery amendment written after the first compute
pass and BEFORE any result was adjudicated; see that section for the two
defects found and fixed: RTH-core expected minutes 390 not 420; |1m ret|
computed on the held chain, volume on the complex sum).

Inputs (read-only, committed):
  research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/
    es_1m_outright.parquet           (7,825,657-row multi-contract 1m panel)
    ../ES_fomc_stats.json            (132-statement artifact; 131 in-data)
  research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/
    events_bbo_coverage/bls_dates.json          (CPI 204 + EMPSIT 204)
  research/control/FUTURES-SIX-READINESS-20261004/es/
    es_expiry_recheck.json           (68/68 expiry calendar)

Zero network. Single-shot parquet read, aggregate, release.
Outputs (write-boundary: this es/ directory only):
  session_dispersion_es.json, es_k6_gates_results.json (raw gate numbers)
"""
import json
from datetime import date

import numpy as np
import pyarrow.parquet as pq

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep"
CACHE = WT + "/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache"
SIX = WT + "/research/control/FUTURES-SIX-READINESS-20261004/es"
DEEP = WT + "/research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003"
OUT = WT + "/research/control/FUTURES-K6GATE-PREP-20261004/es"

EPOCH_ORD = date(1970, 1, 1).toordinal()  # 719163
RTH_LO, RTH_HI = 510, 900  # minute-starts 08:30..14:59 CT -> 390 expected bars
RTH_EXPECTED = RTH_HI - RTH_LO  # 390 (§0.8 amendment 1)
CLOSE_FULL = {0: 990, 1: 975, 2: 960}  # CA 16:30, CB 16:15, CC 16:00 (minute of close)


def day_idx_to_datestr(di):
    return date.fromordinal(int(di) + EPOCH_ORD).isoformat()


def datestr_to_day_idx(s):
    y, m, d = (int(x) for x in s.split("-"))
    return date(y, m, d).toordinal() - EPOCH_ORD


def weekday_of_day_idx(di):  # 0=Mon..6=Sun
    return (int(di) + 3) % 7


def month_position(day_idx):
    d = date.fromordinal(int(day_idx) + EPOCH_ORD)
    return (d.day - 1) // 7 + 1


def build_ct_offsets(day_lo, day_hi):
    """Day-level CT offset seconds (local = utc - offset). CDT(5h) 2nd Sun
    Mar .. 1st Sun Nov; CST(6h) otherwise. Day granularity is exact for all
    ES traded minutes (transitions land on closed Sunday 01:00-02:00 CT)."""
    offs = np.empty(day_hi - day_lo + 1, dtype=np.int64)
    for i, di in enumerate(range(day_lo, day_hi + 1)):
        y = date.fromordinal(di + EPOCH_ORD).year
        mar1_wd = weekday_of_day_idx(datestr_to_day_idx(f"{y}-03-01"))
        second_sun_mar = 1 + (6 - mar1_wd) % 7 + 7
        nov1_wd = weekday_of_day_idx(datestr_to_day_idx(f"{y}-11-01"))
        first_sun_nov = 1 + (6 - nov1_wd) % 7
        start = datestr_to_day_idx(f"{y}-03-{second_sun_mar:02d}")
        end = datestr_to_day_idx(f"{y}-11-{first_sun_nov:02d}")
        offs[i] = 5 * 3600 if start <= di < end else 6 * 3600
    return day_lo, offs


# ---------------------------------------------------------------- load panel
print("reading panel (single shot) ...", flush=True)
t = pq.read_table(CACHE + "/es_1m_outright.parquet")
n_rows = t.num_rows
ts = (t.column("ts_event").to_numpy().astype(np.int64)) // 10**9  # bar START, sec
op = t.column("open").to_numpy().astype(np.float64) * 1e-9
hi_ = t.column("high").to_numpy().astype(np.float64) * 1e-9
lo_ = t.column("low").to_numpy().astype(np.float64) * 1e-9
cl = t.column("close").to_numpy().astype(np.float64) * 1e-9
vol = t.column("volume").to_numpy().astype(np.float64)
sym = t.column("raw_symbol").to_pandas().values
del t

assert np.all(np.diff(ts) >= 0), "panel not time-sorted"
print(f"rows={n_rows} span={day_idx_to_datestr(ts[0]//86400)}..{day_idx_to_datestr(ts[-1]//86400)}", flush=True)

days = ts // 86400
sod = ts - days * 86400
day_lo, offs_table = build_ct_offsets(int(days.min()), int(days.max()))
offs = offs_table[days - day_lo]
local_sod = sod - offs
local_day = days - (local_sod < 0).astype(np.int64)
local_sod = np.where(local_sod < 0, local_sod + 86400, local_sod)
tod = local_sod // 60

sess_day = local_day + (tod >= 1020).astype(np.int64)  # >=17:00 -> next trade date
sat = ((sess_day + 3) % 7) == 5
print("bars mapping to Saturday session:", int(sat.sum()), flush=True)

new_sess = np.empty(n_rows, dtype=bool)
new_sess[0] = True
np.not_equal(sess_day[1:], sess_day[:-1], out=new_sess[1:])
sess_starts = np.flatnonzero(new_sess)
sess_ids = sess_day[sess_starts]
n_sess = len(sess_starts)
sess_end = np.append(sess_starts[1:], n_rows)
print("n sessions:", n_sess, flush=True)

ohlc_bad = (hi_ < np.maximum(op, cl)) | (lo_ > np.minimum(op, cl)) | (hi_ < lo_)

# ---------------------------------------------------------------- session pass
# held contract = max-session-volume outright symbol (§0.8 amendment 2);
# |1m ret| on the held contract's consecutive in-session bars only.
sessions = []
absret_held = np.full(n_rows, np.nan)
for k in range(n_sess):
    s, e = sess_starts[k], sess_end[k]
    di = int(sess_ids[k])
    dstr = day_idx_to_datestr(di)
    tod_s = tod[s:e]
    vol_s = vol[s:e]
    sym_s = sym[s:e]
    ce = 0 if dstr <= "2012-12-31" else (1 if dstr <= "2015-11-19" else 2)
    # dominant symbol by session volume
    uniq, inv = np.unique(sym_s, return_inverse=True)
    sums = np.bincount(inv, weights=vol_s)
    dom = uniq[int(np.argmax(sums))]
    held_mask = sym_s == dom
    # held-chain |1m ret|: consecutive held bars, attributed to later bar
    idx_held = np.flatnonzero(held_mask)
    if len(idx_held) > 1:
        c_h = cl[s:e][idx_held]
        ar = np.abs(np.diff(np.log(c_h)))
        absret_held[s + idx_held[1:]] = ar
    rth_mask_h = held_mask & (tod_s >= RTH_LO) & (tod_s < RTH_HI)
    rth_minutes_h = np.unique(tod_s[rth_mask_h])
    cov = len(rth_minutes_h) / RTH_EXPECTED
    ar_rth = absret_held[s:e][(tod_s >= RTH_LO) & (tod_s < RTH_HI) & ~np.isnan(absret_held[s:e])]
    rth_minutes_cplx = np.unique(tod_s[(tod_s >= RTH_LO) & (tod_s < RTH_HI)])
    sessions.append(dict(
        di=di, dstr=dstr, wd=weekday_of_day_idx(di), ce=ce,
        qera=("E1" if dstr <= "2012-12-31" else "E2" if dstr <= "2015-11-19" else
              "E3" if dstr <= "2017-05-20" else "E4" if dstr <= "2020-02-19" else
              "E5" if dstr <= "2021-12-31" else "E6" if dstr <= "2023-09-30" else "E7"),
        tri=("T1" if dstr <= "2016-12-31" else "T2" if dstr <= "2021-12-31" else "T3"),
        sl=s, se=e, held=str(dom),
        bars_total=int(e - s),
        bars_rth_held=len(rth_minutes_h),
        bars_rth_cplx_unique=len(rth_minutes_cplx),
        cov=cov,
        median_ar=float(np.median(ar_rth)) if len(ar_rth) else None,
        p75_ar=float(np.percentile(ar_rth, 75)) if len(ar_rth) else None,
        p90_ar=float(np.percentile(ar_rth, 90)) if len(ar_rth) else None,
        sd_ar=float(np.std(ar_rth)) if len(ar_rth) > 1 else None,
        vol_total=float(vol_s.sum()),
        ohlc_bad=int(ohlc_bad[s:e].sum()),
        n_rth_missing=int(RTH_EXPECTED - len(rth_minutes_h)),
    ))
print("per-session pass done", flush=True)
sess_by_di = {s["di"]: s for s in sessions}

# ---------------------------------------------------------------- event sets
with open(SIX + "/es_expiry_recheck.json") as f:
    exp_json = json.load(f)
expiry_dates = sorted(r["expiry"] for r in exp_json["date_machine_checks"]["per_quarter"])
expiry_di = set(datestr_to_day_idx(d) for d in expiry_dates)

with open(CACHE + "/../ES_fomc_stats.json") as f:
    fomc = json.load(f)
fomc_all = [r["date"] for r in fomc["per_event_day_level"]]
fomc_di = set(datestr_to_day_idx(d) for d in fomc_all)
timed_rows = [r for r in fomc["per_event_day_level"] if r.get("timed")]
IRREG_CT = {"2019-10-11": 600, "2020-03-03": 540, "2020-03-23": 420,
            "2020-03-31": 450, "2020-08-27": 490, "2025-08-22": 540}
EXCLUDE_EVENTS = {"2020-03-15"}  # Sunday release; family field-4 EXCLUDE

with open(DEEP + "/events_bbo_coverage/bls_dates.json") as f:
    bls = json.load(f)


def bls_dates(series_name):
    out = []
    for y, yd in bls["series"][series_name]["years"].items():
        for d in yd["dates"]:
            out.append(d if d.startswith(y) else f"{y}-{d[5:]}")
    return out


cpi_dates = set(bls_dates("CPI"))
empsit_dates = set(bls_dates("EMPSIT"))
cpi_2025_out = {"2025-10-15", "2025-11-13"}
cpi_2025_in = {"2025-10-24", "2025-12-18"}
empsit_2025_out = {"2025-10-03", "2025-11-07"}
empsit_2025_in = {"2025-11-20", "2025-12-16"}
cpi_main = (cpi_dates - cpi_2025_out) | cpi_2025_in
empsit_main = (empsit_dates - empsit_2025_out) | empsit_2025_in
bls_canceled_falsifiers = {"2025-11-13", "2025-11-07"}
bls_union = cpi_main | empsit_main
bls_di = set(datestr_to_day_idx(d) for d in bls_union)
bls_fals_di = set(datestr_to_day_idx(d) for d in bls_canceled_falsifiers)

# =====================================================================
# M4 — session dispersion table (unconditional, full panel)
# =====================================================================
disp_rows = []
for s in sessions:
    disp_rows.append(dict(
        session_date=s["dstr"], held_symbol=s["held"],
        close_era=["CA_1630", "CB_1615", "CC_1600"][s["ce"]],
        quality_era=s["qera"], tri_era=s["tri"],
        bars_total_complex=s["bars_total"],
        bars_rth_core_held=s["bars_rth_held"],
        bars_rth_core_complex_unique=s["bars_rth_cplx_unique"],
        rth_core_expected_minutes=RTH_EXPECTED,
        rth_core_coverage=round(s["cov"], 4),
        rth_core_missing_minutes=s["n_rth_missing"],
        median_abs1mret_bp_rth_held=round(s["median_ar"] * 1e4, 2) if s["median_ar"] is not None else None,
        p75_abs1mret_bp_rth_held=round(s["p75_ar"] * 1e4, 2) if s["p75_ar"] is not None else None,
        p90_abs1mret_bp_rth_held=round(s["p90_ar"] * 1e4, 2) if s["p90_ar"] is not None else None,
        sd_1mret_bp_rth_held=round(s["sd_ar"] * 1e4, 2) if s["sd_ar"] is not None else None,
        volume_total_complex=s["vol_total"],
        ohlc_violations=s["ohlc_bad"],
        excluded=s["cov"] < 0.60,
        exclusion_reason=("rth_core_coverage_below_0.60" if s["cov"] < 0.60 else None),
    ))
by_year = {}
for r in disp_rows:
    by_year.setdefault(r["session_date"][:4], []).append(r)
year_summary = {}
for y, rows in sorted(by_year.items()):
    ok = [r for r in rows if not r["excluded"]]
    med = [r["median_abs1mret_bp_rth_held"] for r in ok if r["median_abs1mret_bp_rth_held"] is not None]
    year_summary[y] = dict(
        sessions=len(rows), excluded=int(len(rows) - len(ok)),
        median_of_session_median_abs1mret_bp=round(float(np.median(med)), 2) if med else None,
        mean_bars_rth_core_held=round(float(np.mean([r["bars_rth_core_held"] for r in ok])), 1) if ok else None,
    )
era_summary = {}
for cel in ["CA_1630", "CB_1615", "CC_1600"]:
    rows = [r for r in disp_rows if r["close_era"] == cel]
    ok = [r for r in rows if not r["excluded"]]
    med = [r["median_abs1mret_bp_rth_held"] for r in ok if r["median_abs1mret_bp_rth_held"] is not None]
    era_summary[cel] = dict(
        sessions=len(rows), excluded=int(len(rows) - len(ok)),
        median_of_session_median_abs1mret_bp=round(float(np.median(med)), 2) if med else None)
excluded_dates = [r["session_date"] for r in disp_rows if r["excluded"]]
with open(OUT + "/session_dispersion_es.json", "w") as f:
    json.dump(dict(
        schema="session_dispersion_es@1", lane="ES-K6",
        round="FUTURES-K6GATE-PREP-20261004",
        panel="research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_1m_outright.parquet",
        convention=("held-chain dispersion: |1m ret| on the max-session-volume (held) outright "
                    "contract's consecutive bars per session; volume_total_complex = sum over all "
                    "co-trading contracts (ES_K6_GATES.md §0.8)"),
        n_rows_panel=int(n_rows), n_sessions=len(disp_rows),
        rth_core_window_ct="08:30-15:00 (bar starts 08:30..14:59)", rth_core_expected_minutes=RTH_EXPECTED,
        exclusion_law="SPEC_PB1_ES §2 [ERRATUM A7-SPEC-M4]: RTH-core coverage <60% => EXCLUDE; never imputed (flagged, kept)",
        year_summary=year_summary, close_era_summary=era_summary,
        n_excluded=len(excluded_dates), excluded_dates=excluded_dates,
        sessions=disp_rows,
    ), f)
print("M4 written: session_dispersion_es.json", flush=True)


# ---------------------------------------------------------------- helpers
def win_mask(tod_s, lo, hi):
    return (tod_s >= lo) & (tod_s < hi)


def per_minute_mean_vol(s, lo, hi):
    m = win_mask(tod[s["sl"]:s["se"]], lo, hi)
    return float(vol[s["sl"]:s["se"]][m].sum()) / (hi - lo)


def held_median_absret_win(s, lo, hi):
    tod_s = tod[s["sl"]:s["se"]]
    ar = absret_held[s["sl"]:s["se"]]
    m = win_mask(tod_s, lo, hi) & ~np.isnan(ar)
    return float(np.median(ar[m])) if m.any() else None


def settle_close_of(dstr, ce):
    if ce == 0 or (ce == 1 and dstr < "2013-04-01"):
        return 915
    return 900


def w60_full(s):
    c = CLOSE_FULL[s["ce"]]
    return c - 60, c


def w60_rth(s):
    c = settle_close_of(s["dstr"], s["ce"])
    return c - 60, c


BLOCKS = [
    ("evening_1700_2359", 1020, 1440),
    ("overnight_0000_0829", 0, 510),
    ("rth_open_0830_1029", 510, 630),
    ("rth_mid_1030_1229", 630, 750),
    ("rth_aft_1230_1429", 750, 870),
    ("rth_1430_1459", 870, 900),
]
CE_NAME = {0: "CA_1630", 1: "CB_1615", 2: "CC_1600"}

# =====================================================================
# M1 — F5-K6 EXPWITCH ES leg
# =====================================================================
panel_fridays = [s for s in sessions if s["wd"] == 4]
# W = committed 68/68 calendar dates ∩ panel sessions (§0.2); the calendar
# contains 67 Fridays + 2026-06-18 (Thursday, Juneteenth-shifted ESM6) — the
# calendar date is the authority, the weekday is disclosed.
W_all = [s for s in sessions if s["di"] in expiry_di]
W_weekday_split = {"fri": sum(1 for s in W_all if s["wd"] == 4),
                   "not_fri": [s["dstr"] for s in W_all if s["wd"] != 4]}
O_all = [s for s in panel_fridays
         if month_position(s["di"]) in (2, 4, 5) and s["di"] not in expiry_di]

W_covfail = [s["dstr"] for s in W_all if s["cov"] < 0.60]
O_covfail = [s["dstr"] for s in O_all if s["cov"] < 0.60]
W_bls = [s["dstr"] for s in W_all if s["di"] in bls_di and s["cov"] >= 0.60]
W_fomc = [s["dstr"] for s in W_all if s["di"] in fomc_di and s["cov"] >= 0.60 and s["di"] not in bls_di]
W_main = [s for s in W_all
          if s["cov"] >= 0.60 and s["di"] not in bls_di and s["di"] not in fomc_di]
W_sens = [s for s in W_all if s["cov"] >= 0.60]
O_main = [s for s in O_all if s["cov"] >= 0.60]


def class_anatomy(ss):
    per_ce = {}
    for ce in (0, 1, 2):
        sub = [s for s in ss if s["ce"] == ce]
        if not sub:
            continue
        blocks = {}
        for name, lo, hi in BLOCKS:
            v = [per_minute_mean_vol(s, lo, hi) for s in sub]
            blocks[name] = dict(per_minute_mean_vol=float(np.mean(v)))
        tot = [s["vol_total"] / max(1, s["bars_total"]) for s in sub]
        blocks["FULL_SESSION_per_minute_mean_vol"] = dict(value=float(np.mean(tot)))
        wf = [per_minute_mean_vol(s, *w60_full(s)) for s in sub]
        wr = [per_minute_mean_vol(s, *w60_rth(s)) for s in sub]
        ar_wf = [held_median_absret_win(s, *w60_full(s)) for s in sub]
        ar_wr = [held_median_absret_win(s, *w60_rth(s)) for s in sub]
        ar_wf = [a for a in ar_wf if a is not None]
        ar_wr = [a for a in ar_wr if a is not None]
        blocks["W60_full_close_window"] = dict(
            per_minute_mean_vol=float(np.mean(wf)),
            per_minute_median_absret_bp_held=float(np.median(ar_wf)) if ar_wf else None)
        blocks["W60_rth_close_window"] = dict(
            per_minute_mean_vol=float(np.mean(wr)),
            per_minute_median_absret_bp_held=float(np.median(ar_wr)) if ar_wr else None)
        per_ce[CE_NAME[ce]] = dict(
            n=len(sub),
            median_bars_total=float(np.median([s["bars_total"] for s in sub])),
            median_bars_rth_core_held=float(np.median([s["bars_rth_held"] for s in sub])),
            blocks=blocks)
    return per_ce


def ratio_view(W, O, name):
    out = {}
    for key, sel in (("close_era", lambda s: CE_NAME[s["ce"]]),
                     ("tri_era", lambda s: s["tri"])):
        groups = {}
        for s in W:
            groups.setdefault((key, sel(s)), [[], []])[0].append(s)
        for s in O:
            groups.setdefault((key, sel(s)), [[], []])[1].append(s)
        for (k2, g), (w_, o_) in sorted(groups.items()):
            if not w_ or not o_:
                continue
            vw = float(np.mean([per_minute_mean_vol(s, *w60_full(s)) for s in w_]))
            vo = float(np.mean([per_minute_mean_vol(s, *w60_full(s)) for s in o_]))
            aw = [held_median_absret_win(s, *w60_full(s)) for s in w_]
            ao = [held_median_absret_win(s, *w60_full(s)) for s in o_]
            aw = [a for a in aw if a is not None]
            ao = [a for a in ao if a is not None]
            out.setdefault(name, {})[g] = dict(
                n_W=len(w_), n_O=len(o_),
                vol_ratio_W_over_O=vw / vo,
                absret_median_ratio_W_over_O_held=(float(np.median(aw) / np.median(ao))
                                                   if aw and ao else None))
    return out


m1 = dict(
    predeclare_ref="ES_K6_GATES.md §0.2 (+§0.8 amendment); HYPOTHESES_ESNQ_R3.md §2 field 7 (F5-K6)",
    expiry_artifact="FUTURES-SIX-READINESS-20261004/es/es_expiry_recheck.json (68/68; in-panel 66)",
    n_expiry_calendar=68, n_expiry_in_panel=len(W_all),
    W_weekday_split=W_weekday_split,
    W_covfail=W_covfail, O_covfail_n=len(O_covfail), O_covfail_dates=O_covfail,
    W_bls_stacked_excluded=W_bls, W_fomc_stacked_excluded=W_fomc,
    n_W_main=len(W_main), n_O_main=len(O_main),
    W_anatomy_main=class_anatomy(W_main),
    O_anatomy=class_anatomy(O_main),
    W_anatomy_sensitivity_with_stacked=class_anatomy(W_sens),
)
m1.update(ratio_view(W_main, O_main, "W60full_ratios"))
m1["sensitivity_ratios"] = ratio_view(W_sens, O_main, "W60full_ratios_with_stacked")


def integrity(ss):
    return dict(
        n=len(ss),
        sessions_with_missing_rth_minutes=[s["dstr"] for s in ss if s["n_rth_missing"] > 0],
        sessions_with_ohlc_violations=[s["dstr"] for s in ss if s["ohlc_bad"] > 0],
        total_missing_rth_minutes_held=int(sum(s["n_rth_missing"] for s in ss)),
        total_ohlc_violations=int(sum(s["ohlc_bad"] for s in ss)),
    )


m1["integrity_W"] = integrity(W_main)
m1["integrity_O"] = integrity(O_main)


def minute0830_held(ss):
    vols, ars = [], []
    for s in ss:
        tod_s = tod[s["sl"]:s["se"]]
        sym_s = sym[s["sl"]:s["se"]]
        ar_s = absret_held[s["sl"]:s["se"]]
        m = (tod_s == 510) & (sym_s == s["held"])
        if m.any():
            vols.append(float(vol[s["sl"]:s["se"]][m][0]))
            a = ar_s[m][0]
            if not np.isnan(a):
                ars.append(float(a))
    return dict(n=len(vols), median_vol=float(np.median(vols)) if vols else None,
                median_absret_bp_held=float(np.median(ars) * 1e4) if ars else None)


m1["minute_0830_held_W"] = minute0830_held(W_main)
m1["minute_0830_held_O"] = minute0830_held(O_main)

# =====================================================================
# M2 — F1-K6 FOMC-RES
# =====================================================================
events = []
for r in timed_rows:
    d = r["date"]
    if d in EXCLUDE_EVENTS or datestr_to_day_idx(d) not in sess_by_di:
        continue
    s = sess_by_di[datestr_to_day_idx(d)]
    if s["cov"] < 0.60:
        continue
    events.append(dict(dstr=d, rel=IRREG_CT.get(d, 780), di=s["di"]))
events_covfail = [r["date"] for r in timed_rows
                  if r["date"] not in EXCLUDE_EVENTS
                  and datestr_to_day_idx(r["date"]) in sess_by_di
                  and sess_by_di[datestr_to_day_idx(r["date"])]["cov"] < 0.60]
baseline_weds = [s for s in sessions
                 if s["wd"] == 2 and s["di"] not in fomc_di and s["cov"] >= 0.60]
OFFSETS = list(range(-120, 166, 15))


def event_bucket_stats(evs):
    res = {}
    for b in OFFSETS:
        vs, as_, vsh = [], [], []
        for e in evs:
            s = sess_by_di[e["di"]]
            lo = e["rel"] + b
            m = win_mask(tod[s["sl"]:s["se"]], lo, lo + 15)
            vs.append(float(vol[s["sl"]:s["se"]][m].sum()))
            vsh.append(float(vol[s["sl"]:s["se"]][m & (sym[s["sl"]:s["se"]] == s["held"])].sum()))
            ar = absret_held[s["sl"]:s["se"]]
            a = ar[m & ~np.isnan(ar)]
            if len(a):
                as_.append(float(np.median(a)))
        res[b] = dict(vol_median_complex=float(np.median(vs)),
                      vol_median_held=float(np.median(vsh)), n=len(vs),
                      absret_median_held=float(np.median(as_)) if as_ else None)
    return res


def clock_bucket_stats(ss):
    res = {}
    for b in OFFSETS:
        vs, as_, vsh = [], [], []
        for s in ss:
            lo = 780 + b
            m = win_mask(tod[s["sl"]:s["se"]], lo, lo + 15)
            vs.append(float(vol[s["sl"]:s["se"]][m].sum()))
            vsh.append(float(vol[s["sl"]:s["se"]][m & (sym[s["sl"]:s["se"]] == s["held"])].sum()))
            ar = absret_held[s["sl"]:s["se"]]
            a = ar[m & ~np.isnan(ar)]
            if len(a):
                as_.append(float(np.median(a)))
        res[b] = dict(vol_median_complex=float(np.median(vs)),
                      vol_median_held=float(np.median(vsh)), n=len(vs),
                      absret_median_held=float(np.median(as_)) if as_ else None)
    return res


ev_buckets = event_bucket_stats(events)
bl_buckets = clock_bucket_stats(baseline_weds)
ratio_vol = {b: (ev_buckets[b]["vol_median_complex"] / bl_buckets[b]["vol_median_complex"]
                 if bl_buckets[b]["vol_median_complex"] else None) for b in OFFSETS}
ratio_vol_held = {b: (ev_buckets[b]["vol_median_held"] / bl_buckets[b]["vol_median_held"]
                      if bl_buckets[b]["vol_median_held"] else None) for b in OFFSETS}
ratio_ar = {b: (ev_buckets[b]["absret_median_held"] / bl_buckets[b]["absret_median_held"]
                if ev_buckets[b]["absret_median_held"] and bl_buckets[b]["absret_median_held"] else None)
            for b in OFFSETS}
pre = [-120, -105, -90, -75, -60, -45, -30, -15]
m2 = dict(
    predeclare_ref="ES_K6_GATES.md §0.3; ESNQ_HYPOTHESES.md ES-F1 field 7 (F1-K6)",
    fomc_artifact="FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_fomc_stats.json (n_statements_total=132, 131 in-data)",
    n_timed_in_panel=len(events),
    excluded_events_sunday=list(EXCLUDE_EVENTS),
    excluded_events_covfail=events_covfail,
    n_baseline_wednesdays=len(baseline_weds),
    event_buckets=ev_buckets, baseline_wed13_buckets=bl_buckets,
    vol_ratio_event_over_wed13_complex=ratio_vol,
    vol_ratio_event_over_wed13_held_alignment=ratio_vol_held,
    absret_ratio_event_over_wed13_held=ratio_ar,
    gate_bucket0_vol_ratio=ratio_vol[0],
    gate_pre_release_max_vol_ratio=max(ratio_vol[b] for b in pre),
    note=("gate statistic is complex-summed volume per §0.3; held-only ratios are the §0.8 "
          "alignment view; absret ratios use held-chain medians (§0.8)"),
)

FOMC_ERAS = [("2016-19", "2016-01-01", "2019-12-31"),
             ("2020-22", "2020-01-01", "2022-12-31"),
             ("2023-26", "2023-01-01", "2026-12-31")]
m2["era_views"] = {}
for name, lo_d, hi_d in FOMC_ERAS:
    evs = [e for e in events if lo_d <= e["dstr"] <= hi_d]
    bl = [s for s in baseline_weds if lo_d <= s["dstr"] <= hi_d]
    if not evs or not bl:
        continue
    evb = event_bucket_stats(evs)
    blb = clock_bucket_stats(bl)
    zero_cells = [b for b in OFFSETS if not blb[b]["vol_median_complex"] or not evb[b]["vol_median_complex"]]
    m2["era_views"][name] = dict(
        n_events=len(evs), n_baseline=len(bl), zero_vol_median_buckets=zero_cells,
        vol_ratio_complex={b: (evb[b]["vol_median_complex"] / blb[b]["vol_median_complex"]
                               if blb[b]["vol_median_complex"] else None) for b in OFFSETS},
        absret_ratio_held={b: (evb[b]["absret_median_held"] / blb[b]["absret_median_held"]
                               if evb[b]["absret_median_held"] and blb[b]["absret_median_held"] else None)
                           for b in OFFSETS})

# =====================================================================
# M3a — F2-K6 MACRO-0730
# =====================================================================
SPIKE_LO, SPIKE_HI = 445, 455
NB_LO1, NB_HI1, NB_LO2, NB_HI2 = 405, 444, 456, 495


def day_win(s, lo, hi):
    m = win_mask(tod[s["sl"]:s["se"]], lo, hi)
    return float(vol[s["sl"]:s["se"]][m].sum())


bls_events = []
for dstr in sorted(bls_union):
    di = datestr_to_day_idx(dstr)
    if di not in sess_by_di:
        continue
    bls_events.append(dict(dstr=dstr, di=di, s=sess_by_di[di]))
bls_fomc_stacked = [e["dstr"] for e in bls_events if e["di"] in fomc_di]
bls_covfail = [e["dstr"] for e in bls_events if e["s"]["cov"] < 0.60]
bls_main = [e for e in bls_events if e["di"] not in fomc_di and e["s"]["cov"] >= 0.60]
matched_nr = []
for e in bls_main:
    wd = e["s"]["wd"]
    cands = [s for s in sessions
             if s["wd"] == wd and abs(s["di"] - e["di"]) <= 30
             and s["di"] not in bls_di and s["di"] not in fomc_di
             and s["cov"] >= 0.60]
    if cands:
        cands.sort(key=lambda s: abs(s["di"] - e["di"]))
        matched_nr.append(cands[0])

m3 = dict(
    predeclare_ref="ES_K6_GATES.md §0.4; ESNQ_HYPOTHESES.md ES-F2 field 7 (F2-K6)",
    bls_artifact="FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/events_bbo_coverage/bls_dates.json (204+204) + vintage law BLS_VINTAGE_INVESTIGATION.md",
    n_bls_union_dates=len(bls_union), n_bls_in_panel=len(bls_events),
    bls_fomc_stacked_excluded=bls_fomc_stacked,
    bls_covfail_excluded=bls_covfail,
    n_bls_main=len(bls_main), n_matched_nonrelease=len(matched_nr),
)


def era_view_bls(evs, nrs):
    sp_e = np.mean([day_win(e["s"], SPIKE_LO, SPIKE_HI) / 10.0 for e in evs])
    nb_e = np.mean([(day_win(e["s"], NB_LO1, NB_HI1) + day_win(e["s"], NB_LO2, NB_HI2)) / 80.0 for e in evs])
    sp_n = np.mean([day_win(s, SPIKE_LO, SPIKE_HI) / 10.0 for s in nrs])
    nb_n = np.mean([(day_win(s, NB_LO1, NB_HI1) + day_win(s, NB_LO2, NB_HI2)) / 80.0 for s in nrs])
    ar_e = [a for a in (held_median_absret_win(e["s"], SPIKE_LO, SPIKE_HI) for e in evs) if a is not None]
    ar_n = [a for a in (held_median_absret_win(s, SPIKE_LO, SPIKE_HI) for s in nrs) if a is not None]
    h7_e = np.mean([day_win(e["s"], 420, 480) / e["s"]["vol_total"] for e in evs])
    h7_n = np.mean([day_win(s, 420, 480) / s["vol_total"] for s in nrs])
    return dict(
        n_release=len(evs), n_matched=len(nrs),
        spike_per_min_vol_release=float(sp_e), neighbor_per_min_vol_release=float(nb_e),
        gate_stat_spike_over_neighbor_release=float(sp_e / nb_e),
        spike_per_min_vol_matched=float(sp_n), neighbor_per_min_vol_matched=float(nb_n),
        release_over_matched_spike_ratio=float(sp_e / sp_n) if sp_n else None,
        median_absret_bp_held_release_spike=float(np.median(ar_e) * 1e4) if ar_e else None,
        median_absret_bp_held_matched_spike=float(np.median(ar_n) * 1e4) if ar_n else None,
        hour07_vol_share_release=float(h7_e), hour07_vol_share_matched=float(h7_n))


for tn in ("T1", "T2", "T3"):
    evs = [e for e in bls_main if e["s"]["tri"] == tn]
    nrs = [s for s in matched_nr if s["tri"] == tn]
    if evs and nrs:
        m3[tn] = era_view_bls(evs, nrs)
for cen, ce in (("CA_1630", 0), ("CB_1615", 1), ("CC_1600", 2)):
    evs = [e for e in bls_main if e["s"]["ce"] == ce]
    nrs = [s for s in matched_nr if s["ce"] == ce]
    if evs and nrs:
        v = era_view_bls(evs, nrs)
        m3["close_era_" + cen] = dict(n_release=v["n_release"], n_matched=v["n_matched"],
                                      gate_stat_spike_over_neighbor_release=v["gate_stat_spike_over_neighbor_release"],
                                      release_over_matched_spike_ratio=v["release_over_matched_spike_ratio"])
m3["nc2b_canceled_falsifier_subview"] = {}
for dstr in sorted(bls_canceled_falsifiers):
    di = datestr_to_day_idx(dstr)
    if di not in sess_by_di:
        m3["nc2b_canceled_falsifier_subview"][dstr] = "not_in_panel"
        continue
    s = sess_by_di[di]
    sp = day_win(s, SPIKE_LO, SPIKE_HI) / 10.0
    nb = (day_win(s, NB_LO1, NB_HI1) + day_win(s, NB_LO2, NB_HI2)) / 80.0
    m3["nc2b_canceled_falsifier_subview"][dstr] = dict(
        spike_per_min_vol=float(sp), neighbor_per_min_vol=float(nb),
        spike_over_neighbor=float(sp / nb) if nb else None, cov=s["cov"])

# =====================================================================
# write results
# =====================================================================
results = dict(
    schema="es_k6_gates_results@1", lane="ES-K6", round="FUTURES-K6GATE-PREP-20261004",
    zero_pnl_statement="Unconditional descriptive anatomy only; no PnL, no expectancy, no conditional-on-signal measurement, no sign/return-direction statistic; 0 network fetches; cap 24 FROZEN untouched.",
    panel_rows=int(n_rows), n_sessions=int(n_sess),
    amendment_note="computed per ES_K6_GATES.md §0 as amended by §0.8 (held-chain |1m ret|; RTH-core expected 390 min)",
    M1_F5K6=m1, M2_F1K6=m2, M3a_F2K6=m3,
    M3b_F4K6=dict(status="NOT_RUN",
                  reason="F4-K6 measures placement of run-reversal CONDITIONED on a price-derived signal (k consecutive same-sign sessions); dispatch law this round forbids conditional-on-signal measurement; not unconditional anatomy. Unconditional inputs delivered by M4."),
)
with open(OUT + "/es_k6_gates_results.json", "w") as f:
    json.dump(results, f, indent=1)
print("results written", flush=True)

digest = dict(
    m1_W60full_ratios=m1["W60full_ratios"],
    m1_sens=m1["sensitivity_ratios"],
    m1_integrity_W={k: (v if not isinstance(v, list) else (len(v), v[:6])) for k, v in m1["integrity_W"].items()},
    m1_minute0830=dict(W=m1["minute_0830_held_W"], O=m1["minute_0830_held_O"]),
    m1_nW=m1["n_W_main"], m1_nO=m1["n_O_main"], m1_W_bls=m1["W_bls_stacked_excluded"], m1_W_fomc=m1["W_fomc_stacked_excluded"], m1_W_covfail=m1["W_covfail"],
    m2_bucket0=m2["gate_bucket0_vol_ratio"], m2_pre_max=m2["gate_pre_release_max_vol_ratio"],
    m2_n=len(events), m2_bl=len(baseline_weds),
    m2_pre_vol={b: ratio_vol[b] for b in pre},
    m2_era0={k: (v['vol_ratio_complex'][0], max(v['vol_ratio_complex'][b] for b in pre)) for k, v in m2['era_views'].items()},
    m3_T1=m3.get("T1"), m3_T2=m3.get("T2"), m3_T3=m3.get("T3"),
    m3_close_eras={k: m3[k] for k in m3 if k.startswith("close_era_")},
    m3_nBLS=m3["n_bls_main"], m3_fomc_stack=m3["bls_fomc_stacked_excluded"], m3_covfail=m3["bls_covfail_excluded"],
    m4_n_excluded=len(excluded_dates), m4_excluded_sample=excluded_dates[:10],
)
print(json.dumps(digest, indent=1, default=str))
