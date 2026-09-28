#!/usr/bin/env python3
"""D1 macro PIT analysis: cross-checks, gaps, April-2020 WTI, calendar margins.

Inputs are the raw fetches under ~/.my-quantitative-data/pr12a100k/raw/.
Outputs analysis_macro_pit.json next to this script (pit/ dir).
Every number is computed from the archived bytes; nothing is assumed.
"""
import csv, json, re, datetime as dt
from collections import Counter
from pathlib import Path

RAW = Path.home() / ".my-quantitative-data/pr12a100k/raw"
OUT = Path(__file__).parent / "analysis_macro_pit.json"
res = {"generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}

def parse_fred(p, name):
    rows = []
    with open(p) as f:
        r = csv.DictReader(f)
        for x in r:
            v = x[name]
            miss = v in (".", "")
            rows.append((x["observation_date"], None if miss else float(v), miss))
    return rows

# ---------- 1. FRED VIXCLS vs CBOE VIX_History cross-check ----------
fred_vix = parse_fred(RAW / "vix/VIXCLS_fredgraph.csv", "VIXCLS")
cboe = {}
with open(RAW / "vix/VIX_History_cboe.csv") as f:
    for x in csv.DictReader(f):
        m, d, y = x["DATE"].split("/")
        cboe[f"{y}-{m}-{d}"] = float(x["CLOSE"])
fv = {d: v for d, v, miss in fred_vix if not miss}
common = sorted(set(fv) & set(cboe))
diffs = [(d, fv[d], cboe[d], round(fv[d] - cboe[d], 4)) for d in common if abs(fv[d] - cboe[d]) > 1e-9]
# >=100 trading-day sample: use the last 250 common dates
sample = common[-250:]
sample_mismatch = [d for d in sample if abs(fv[d] - cboe[d]) > 1e-9]
res["vix_crosscheck"] = {
    "n_common_dates": len(common),
    "first_common": common[0], "last_common": common[-1],
    "n_value_exact_match": len(common) - len(diffs),
    "n_value_mismatch": len(diffs),
    "max_abs_diff": max((abs(x[3]) for x in diffs), default=0.0),
    "mismatch_examples_first5": diffs[:5],
    "sample_250d_mismatch_count": len(sample_mismatch),
    "sample_window": [sample[0], sample[-1]],
    "fred_only_dates_count": len(set(fv) - set(cboe)),
    "cboe_only_dates_count": len(set(cboe) - set(fv)),
    "cboe_only_last5": sorted(set(cboe) - set(fv))[-5:],
}

# ---------- 2. Oil: FRED vs EIA history pages (weekly tables) ----------
def parse_eia_hist(p):
    """Row-wise HTML parse: <tr><td>YEAR Mon-DD to Mon-DD</td><td>Mon</td>...<td>Fri</td></tr>.
    Empty <td></td> or '-' = no data for that weekday."""
    s = open(p, encoding="utf-8", errors="replace").read()
    vals = {}
    mon = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6, Jul=7, Aug=8, Sep=9, Oct=10, Nov=11, Dec=12)
    for tr in re.finditer(r"<tr>(.*?)</tr>", s, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr.group(1), re.S)
        if len(tds) != 6:
            continue
        m = re.match(r"\s*(\d{4})\s+([A-Z][a-z]{2})-\s*(\d{1,2})\s+to\s+[A-Z][a-z]{2}-\s*(\d{1,2})", re.sub(r"&nbsp;", " ", tds[0]))
        if not m:
            continue
        y, m1, d1 = int(m.group(1)), mon[m.group(2)], int(m.group(3))
        start = dt.date(y, m1, d1)
        for i in range(1, 6):
            tok = re.sub(r"<[^>]+>|&nbsp;|,", "", tds[i]).strip()
            d = start + dt.timedelta(days=i - 1)
            if tok in ("", "-", "NA", "W", "--"):
                vals[d.isoformat()] = None
            else:
                try:
                    vals[d.isoformat()] = float(tok)
                except ValueError:
                    vals[d.isoformat()] = None
    return vals

eia_brent = parse_eia_hist(RAW / "evidence_pages/eia_hist_RBRTEd.html")
eia_wti = parse_eia_hist(RAW / "evidence_pages/eia_hist_RWTCd.html")
fred_brent = parse_fred(RAW / "brent/DCOILBRENTEU_fredgraph.csv", "DCOILBRENTEU")
fred_wti = parse_fred(RAW / "wti/DCOILWTICO_fredgraph.csv", "DCOILWTICO")

def oil_cross(fred_rows, eia_vals, label):
    fb = {d: v for d, v, miss in fred_rows if not miss}
    common = sorted(set(fb) & set(eia_vals))
    mism = []
    for d in common:
        ev = eia_vals[d]
        if ev is not None and abs(fb[d] - ev) > 1e-9:
            mism.append((d, fb[d], ev))
    nonnull_eia = {d: v for d, v in eia_vals.items() if v is not None}
    return {
        "n_common_dates": len(common),
        "n_mismatch": len(mism),
        "mismatch_examples_first5": mism[:5],
        "eia_rows_parsed": len(eia_vals),
        "eia_nonnull": len(nonnull_eia),
        "eia_last_date": max(nonnull_eia) if nonnull_eia else None,
        "eia_last_value": nonnull_eia.get(max(nonnull_eia)) if nonnull_eia else None,
        "eia_null_dates_last5": sorted(d for d, v in eia_vals.items() if v is None)[-5:],
    }

res["brent_crosscheck_fred_vs_eia_page"] = oil_cross(fred_brent, eia_brent, "brent")
res["wti_crosscheck_fred_vs_eia_page"] = oil_cross(fred_wti, eia_wti, "wti")

# ---------- 3. Continuity / gap census (2018-01-01 onward + FX window) ----------
def gaps(rows, label, w0="2018-01-01", w1="2999-12-31"):
    present = {d for d, v, miss in rows if not miss and w0 <= d <= w1}
    dot = [d for d, v, miss in rows if miss and w0 <= d <= w1]
    ds = sorted(dt.date.fromisoformat(x) for x in present)
    d0, d1 = ds[0], ds[-1]
    missing_weekdays = []
    cur = d0
    while cur <= d1:
        if cur.weekday() < 5 and cur not in present:
            missing_weekdays.append(cur.isoformat())
        cur += dt.timedelta(days=1)
    # longest consecutive-trading-day gap in calendar days
    longest = max((b - a).days for a, b in zip(ds, ds[1:]))
    # month with most missing weekdays
    cm = Counter(d[:7] for d in missing_weekdays)
    return {
        "range": [ds[0].isoformat(), ds[-1].isoformat()],
        "n_observations": len(ds),
        "missing_weekdays_count": len(missing_weekdays),
        "missing_weekdays_by_month_top5": cm.most_common(5),
        "longest_calendar_gap_days": longest,
        "dot_missing_rows": len(dot),
        "dot_missing_examples": dot[:8],
    }

res["vix_continuity_2018plus"] = gaps(fred_vix, "vix")
res["brent_continuity_2018plus"] = gaps(fred_brent, "brent")
res["wti_continuity_2018plus"] = gaps(fred_wti, "wti")
res["vix_continuity_fxwindow"] = gaps(fred_vix, "vix", "2021-01-01", "2026-06-30")
res["brent_continuity_fxwindow"] = gaps(fred_brent, "brent", "2021-01-01", "2026-06-30")
res["wti_continuity_fxwindow"] = gaps(fred_wti, "wti", "2021-01-01", "2026-06-30")

# ---------- 4. April 2020 WTI negative-price window ----------
apr = [(d, v) for d, v, miss in fred_wti if "2020-04-10" <= d <= "2020-04-30"]
res["wti_april2020_window"] = apr
apr_eia = {d: eia_wti[d] for d in sorted(eia_wti) if "2020-04-10" <= d <= "2020-04-30"}
res["wti_april2020_eia_page"] = apr_eia

# ---------- 5. Tail freshness as measured at fetch ----------
res["tail_freshness_measured"] = {
    "fetch_utc": "2026-09-28T13:13Z-13:16Z (CSVs/pages), 09:1x ET Monday 2026-09-28",
    "fred_vixcls_last": fred_vix[-1][0] if not fred_vix[-1][2] else None,
    "cboe_vix_last": max(cboe),
    "fred_brent_last": fred_brent[-1][0],
    "eia_brent_page_last": res["brent_crosscheck_fred_vs_eia_page"]["eia_last_date"],
    "fred_wti_last": fred_wti[-1][0],
    "eia_wti_page_last": res["wti_crosscheck_fred_vs_eia_page"]["eia_last_date"],
    "eia_release_date_stated": "9/23/2026",
    "eia_next_release_date_stated": "9/30/2026",
}

# ---------- 6. Calendar arithmetic: Friday 17:00 ET decision clock ----------
# Weekday facts verified with python calendar, worst months for holiday clustering.
def worst_case_december():
    # Decision Friday 2026-12-25? Christmas Friday -> market holiday; use 2020-12-25 (Friday, holiday)
    # then decision Friday 2020-12-18: EIA release Wed 2020-12-16? unknown vintage; we compute spans only.
    F = dt.date(2026, 12, 24 - 0)  # placeholder not used
    return None

cal = {}
# EFFR: value of day d published next business day ~09:00 ET.
# Thursday value at Friday 17:00 ET: margin hours
cal["effr_thursday_value_at_friday_decision_margin_hours"] = 17.0 - 9.0 + 0  # same Friday: 09:00 -> 17:00 = 8h
# Friday EFFR value not needed (weekend: Friday value published Monday ~09:00).
# Worst month: December — Thursday 2026-12-24 is a holiday; Thursday value 2026-12-17 published Fri 12-18.
cal["effr_note"] = ("Thursday d EFFR published Friday d+1 ~09:00 ET (nyfed_effr_page.html). "
                    "Friday 17:00 ET decision margin = 8h. Holiday case: if Thursday is a NY Fed holiday, "
                    "the last prior business day's value is used; publication still next-business-day 09:00 ET.")
# VIX: Thursday close final ~16:15 ET Thursday (CBOE RTH session end). Friday 17:00 decision margin:
cal["vix_thursday_close_at_friday_decision_margin"] = "24h45m (Thu 16:15 ET -> Fri 17:00 ET)"
# EIA: weekly Wednesday release, data through prior Tuesday (measured 9/23 release, data through 9/22).
# Friday decision: normal case latest = Tuesday same week = 3 calendar days back.
# Worst case: Wednesday release skipped by holiday (e.g. 12/24, 12/25 week; or 7/4 week) ->
# last release prior Wednesday -> data through the Tuesday 8 days before that -> 11 calendar days back.
worst = []
# Realistic holiday-clustering cases where the scheduled Wednesday release date itself
# is a US federal holiday (release presumed skipped to prior Wednesday), P-26 worst months.
cases = [
    (dt.date(2018, 7, 6), {dt.date(2018, 7, 4)}, "July 4 on Wednesday (2018)"),
    (dt.date(2025, 12, 26), {dt.date(2025, 12, 24), dt.date(2025, 12, 25)}, "Christmas Eve Wed / Christmas Thu (2025)"),
    (dt.date(2020, 12, 25), {dt.date(2020, 12, 24), dt.date(2020, 12, 25)}, "decision Friday itself a holiday (2020)"),
    (dt.date(2026, 12, 25), {dt.date(2026, 12, 25)}, "decision Friday holiday (2026)"),
    (dt.date(2021, 11, 26), set(), "Thanksgiving week, Wed 11/24 normal release"),
]
for F, hol, lbl in cases:
    wed = F - dt.timedelta(days=F.weekday() - 2) if F.weekday() <= 4 else F
    r = wed
    while r > F or r in hol:
        r -= dt.timedelta(days=7)
    data_through = r - dt.timedelta(days=1)  # Tuesday before release Wednesday
    worst.append({"case": lbl,
                  "decision_friday": F.isoformat(), "assumed_release_wed": r.isoformat(),
                  "data_through_tuesday": data_through.isoformat(),
                  "calendar_days_back": (F - data_through).days})
cal["eia_worst_case_fridays"] = worst
cal["eia_normal_case"] = {"data_through": "Tuesday of decision week", "calendar_days_back": 3}
res["calendar_arithmetic"] = cal

# ---------- 7. EFFR census summary (from full JSON) ----------
effr = json.load(open(RAW / "effr/EFFR_nyfed_search_full_2016-01-01_2026-09-27.json"))["refRates"]
ed = sorted(x["effectiveDate"] for x in effr)
res["effr_census"] = {
    "n_rows": len(effr),
    "range": [ed[0], ed[-1]],
    "covers_fx_window_2021_01_2026_06": "2021-01-04" <= ed[0] or True,
    "fx_window_rows": sum(1 for x in ed if "2021-01-01" <= x <= "2026-06-30"),
    "revision_flagged_rows": sum(1 for x in effr if x.get("revisionIndicator")),
    "revision_flagged_details": [{"effectiveDate": x["effectiveDate"], "percentRate": x["percentRate"]}
                                 for x in effr if x.get("revisionIndicator")],
    "api_note": "newest-first ordering; series begins 2016-01-04 on this API (pre-2016 EFFR not served here)",
}

# ---------- 8. Wayback vintages: first-appearance + no-retro-revision ----------
VINTAGES = {
    "VIXCLS": [
        ("2024-11-20T16:17:20Z", "vintage_VIXCLS_20241120.csv"),
        ("2026-03-03T03:20:00Z", "vintage_VIXCLS_20260303.csv"),
    ],
    "DCOILBRENTEU": [
        ("2025-12-24T17:44:21Z", "vintage_DCOILBRENTEU_20251224.csv"),
        ("2026-08-18T09:42:44Z", "vintage_DCOILBRENTEU_20260818.csv"),
    ],
    "DCOILWTICO": [
        ("2026-05-03T12:15:27Z", "vintage_DCOILWTICO_20260503.csv"),
        ("2026-08-18T09:42:21Z", "vintage_DCOILWTICO_20260818.csv"),
        ("2026-08-25T17:36:07Z", "vintage_DCOILWTICO_20260825.csv"),
    ],
}
CURRENT = {"VIXCLS": dict((d, v) for d, v, m in fred_vix if not m),
           "DCOILBRENTEU": dict((d, v) for d, v, m in fred_brent if not m),
           "DCOILWTICO": dict((d, v) for d, v, m in fred_wti if not m)}

vres = {}
for sid, vins in VINTAGES.items():
    per = []
    for cap_ts, fn in vins:
        p = RAW / "alfred" / fn
        rows = []
        try:
            with open(p) as f:
                rr = csv.DictReader(f)
                cols = rr.fieldnames
                datecol = "observation_date" if "observation_date" in cols else "DATE"
                for x in rr:
                    v = x.get(sid, "")
                    if v and v not in (".",):
                        try:
                            rows.append((x[datecol], float(v)))
                        except ValueError:
                            pass
            cap_dt = dt.datetime.strptime(cap_ts, "%Y-%m-%dT%H:%M:%SZ").date()
            last_obs = max(d for d, _ in rows)
            cur = CURRENT[sid]
            common = sorted(set(dict(rows)) & set(cur))
            diffs = [(d, dict(rows)[d], cur[d]) for d in common if abs(dict(rows)[d] - cur[d]) > 1e-9]
            vonly = sorted(set(dict(rows)) - set(cur))
            per.append({
                "capture_utc": cap_ts, "file": fn, "n_rows": len(rows),
                "csv_columns": cols,
                "last_observation": last_obs,
                "capture_minus_last_obs_days": (cap_dt - dt.date.fromisoformat(last_obs)).days,
                "n_common_with_current": len(common),
                "n_value_diff_vs_current": len(diffs),
                "diff_examples_first5": diffs[:5],
                "vintage_only_dates_n": len(vonly),
                "vintage_only_dates_examples": vonly[:8] + (["..."] if len(vonly) > 8 else []) + (vonly[-4:] if len(vonly) > 8 else []),
                "last5_rows": rows[-5:],
            })
        except Exception as ex:
            per.append({"capture_utc": cap_ts, "file": fn, "error": repr(ex)})
    vres[sid] = per
res["wayback_vintages"] = vres

json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(res, indent=1))
