#!/usr/bin/env python
"""Coverage / interior-gap scan + measurable-cost addendum for session 2 of
PC12A-7ASSET-DATA-UNBLOCK-2026-10-01. Everything from landed raw bytes.

Outputs COVERAGE_REPORT.json:
  per asset: window weekday histogram, gap histogram (2..5 cal days),
  per-archive coverage fraction, isolation days (IBKR-only, no archive),
  longest streak covered by >=1 archive;
  energy: same for CONTFUT + per-year flat-bar share;
  measurable-cost addendum: energy front D3 BID/ASK spreads p50/p90/max bps
  (29-30d sample, labeled as such - NOT a 6y panel);
  FRED serving-lag second observation recorded.
"""
import json
import statistics as st
from collections import Counter
from datetime import date
from pathlib import Path

RAW = Path.home() / ".my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw"
IBKR = Path.home() / ".my-quantitative-data/portfolio-composite-12assets-100k-v1/ibkr_acq_20260930"
CTL = Path("/Users/hoangminhlong/my-quantitative/.worktrees/pc12a-7asset-unblock-2026-10-01/research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01")
W = ("2020-10-01", "2026-09-30")
YEARS = ["20210930", "20220930", "20230930", "20240930", "20250930", "20260930"]


def pctl(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    import math
    f, c = math.floor(k), math.ceil(k)
    return xs[f] if f == c else xs[f] + (xs[c] - xs[f]) * (k - f)


def gap_hist(dates):
    ds = sorted(dates)
    gaps = Counter()
    for a, b in zip(ds, ds[1:]):
        gaps[(date.fromisoformat(b) - date.fromisoformat(a)).days] += 1
    return {str(k): v for k, v in sorted(gaps.items()) if 2 <= k <= 6}


def wd_hist(dates):
    c = Counter(date.fromisoformat(d).weekday() for d in dates)
    return {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][k]: v for k, v in sorted(c.items())}


def ibkr_mid(asset):
    out = {}
    for y in YEARS:
        b = {r["date"]: r["close"] for r in json.loads((IBKR / f"{asset}_1d_BID_{y}.json").read_text())}
        a = {r["date"]: r["close"] for r in json.loads((IBKR / f"{asset}_1d_ASK_{y}.json").read_text())}
        for d in b.keys() & a.keys():
            if b[d] > 0 and a[d] >= b[d]:
                out[d] = (b[d] + a[d]) / 2
    return out


def ibkr_contfut(asset):
    rows = json.loads((IBKR / f"{asset}_CONTFUT_TRADES_1d_6Y.json").read_text())
    return {r["date"][:10]: {"close": r["close"],
                             "flat": r["open"] == r["high"] == r["low"] == r["close"]}
            for r in rows}


def parse_fred(f):
    o = {}
    for l in (RAW / f).read_text().splitlines()[1:]:
        d, v = l.split(",")
        if v not in (".", ""):
            o[d] = float(v)
    return o


ecb_hdr = (RAW / "ecb_eurofxref_hist.csv").read_text().splitlines()[0].split(",")
ix = {c: i for i, c in enumerate(ecb_hdr)}
ecb = {}
for line in (RAW / "ecb_eurofxref_hist.csv").read_text().splitlines()[1:]:
    p = line.split(",")
    try:
        ecb[p[0]] = (float(p[ix["USD"]]), float(p[ix["NZD"]]), float(p[ix["CHF"]]))
    except Exception:
        pass
ecb_nzd = {d: v[0] / v[1] for d, v in ecb.items()}
ecb_chf = {d: v[2] / v[0] for d, v in ecb.items()}
fr_nzd = parse_fred("fred_DEXUSNZ.csv")
fr_chf = parse_fred("fred_DEXSZUS.csv")
eia = {k: {r["period"]: float(r["value"]) for r in json.loads((RAW / f).read_text())["rows"]
           if r.get("value") is not None}
       for k, f in [("BRENT", "eia_v2_RBRTE_daily.json"), ("WTI", "eia_v2_RWTC_daily.json"),
                    ("NATGAS", "eia_v2_RNGWHHD_daily.json")]}

TD = {}
_tdj = json.loads(Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng6/integration/research/control/forex_ng6_run/p0/staging/XAUUSD_1day_full.json").read_text())
for _v in _tdj["values"]:
    TD[_v["datetime"]] = float(_v["close"])
ARCH = {
    "NZDUSD": {"FRED_H10": fr_nzd, "ECB_cross": ecb_nzd},
    "USDCHF": {"FRED_H10": fr_chf, "ECB_cross": ecb_chf},
    "XAUUSD": {"TD_archive": TD},
    "XAGUSD": {},
    "BRENT": {"EIA_spot": eia["BRENT"]},
    "WTI": {"EIA_spot": eia["WTI"]},
    "NATGAS": {"EIA_spot": eia["NATGAS"]},
}
report = {"schema": "pc12a_7asset_coverage@1", "window": W, "assets": {}}

for asset in ["NZDUSD", "USDCHF", "XAUUSD", "XAGUSD"]:
    mid = {d: v for d, v in ibkr_mid(asset).items() if W[0] <= d <= W[1]}
    row = {"ibkr_days": len(mid),
           "ibkr_weekday_hist": wd_hist(mid.keys()),
           "ibkr_gap_hist_cal_days": gap_hist(mid.keys()),
           "archives": {}}
    arch_dates = None
    for name, series in ARCH[asset].items():
        sd = {d for d in series if W[0] <= d <= W[1]}
        common = mid.keys() & sd
        row["archives"][name] = {"archive_days": len(sd), "common_with_ibkr": len(common),
                                 "coverage_of_ibkr_pct": round(100 * len(common) / len(mid), 2)}
        arch_dates = (arch_dates or set()) | sd
    if arch_dates is not None:
        iso = sorted(set(mid.keys()) - arch_dates)
        row["isolation_days_ibkr_only_no_archive"] = {"count": len(iso), "dates": iso[:40]}
        both = sorted(set(mid.keys()) & arch_dates)
        longest = cur = 0
        prev = None
        for d in both:
            if prev is not None and (date.fromisoformat(d) - date.fromisoformat(prev)).days <= 5:
                cur += 1
            else:
                cur = 1
            longest = max(longest, cur)
            prev = d
        row["longest_streak_covered_by_ge1_archive_days"] = longest
    else:
        row["archives"]["(none reachable)"] = True
        row["isolation_days_ibkr_only_no_archive"] = "n/a - no archive exists"
    report["assets"][asset] = row

for asset in ["BRENT", "WTI", "NATGAS"]:
    cf = {d: v for d, v in ibkr_contfut(asset).items() if W[0] <= d <= W[1]}
    flat_by_year = {}
    for y in ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]:
        xs = [v["flat"] for d, v in cf.items() if d[:4] == y]
        if xs:
            flat_by_year[y] = round(100 * sum(xs) / len(xs), 1)
    row = {"contfut_days": len(cf),
           "contfut_weekday_hist": wd_hist(cf.keys()),
           "contfut_gap_hist_cal_days": gap_hist(cf.keys()),
           "flat_ohlc_share_pct_by_year": flat_by_year,
           "archives": {}}
    for name, series in ARCH[asset].items():
        sd = {d for d in series if W[0] <= d <= W[1]}
        common = cf.keys() & sd
        row["archives"][name] = {"archive_days": len(sd), "common_with_contfut": len(common),
                                 "coverage_of_contfut_pct": round(100 * len(common) / len(cf), 2)}
    report["assets"][asset] = row

# ---- measurable-cost addendum: D3 energy front spreads (30d sample) ----
d3 = json.loads((RAW / "ibkr_ro_20261001" / "d3_energy_front_bidask_30d.json").read_text())
cost = {"definition": ("front-contract D1 BID/ASK close spreads from the "
                       "2026-10-01 read-only probe; 29-30d SAMPLE, not a 6y "
                       "panel; spread=(ask-bid)/((ask+bid)/2)*1e4"),
        "sample_window": "last 30 D1 bars to 2026-09-30", "fronts": {}}
for name, row in d3.items():
    if not isinstance(row, dict) or "BID" not in row:
        continue
    bid = {r["date"]: r["close"] for r in row["BID"]}
    ask = {r["date"]: r["close"] for r in row["ASK"]}
    xs = [(ask[d] - bid[d]) / ((ask[d] + bid[d]) / 2) * 1e4
          for d in bid.keys() & ask.keys() if bid[d] > 0 and ask[d] >= bid[d]]
    if xs:
        cost["fronts"][name] = {"n": len(xs),
                                "p50_bps": round(pctl(xs, .5), 3),
                                "p90_bps": round(pctl(xs, .9), 3),
                                "max_bps": round(max(xs), 3)}
report["measurable_cost_addendum"] = cost

# reads LANDED point-2 files (skeptic finding 1: never hard-code observations)
def _last(fname):
    ls = (RAW / fname).read_text().strip().splitlines()
    return ls[-1].split(",")[0] if len(ls) > 1 else None
report["fred_serving_lag_observations"] = {
    "point_1": {"at_utc": "2026-10-01T01:25-01:26Z (MANIFEST_RAW rows)",
                "fx_last": "2026-09-25", "energy_last": "2026-09-29"},
    "point_2": {"source": "FRED_STALENESS_POINT2.json + fred_*_staleness_p2.csv",
                "fx_last": _last("fred_DEXUSNZ_staleness_p2.csv"),
                "energy_last": _last("fred_DCOILBRENTEU_staleness_p2.csv")}}

# harness quirk 2026-10-01: some python processes cannot stat the worktree
# dir (sandbox); the raw data dir is always writable -> write there, shell
# copies into CTL afterwards
out = RAW.parent / "COVERAGE_REPORT.json"
out.write_text(json.dumps(report, indent=1))
print("written", out)
print("written", out)
for a, r in report["assets"].items():
    print(a, "ibkr/contfut days:", r.get("ibkr_days") or r.get("contfut_days"),
          "| archives:", {k: (v.get("coverage_of_ibkr_pct") or v.get("coverage_of_contfut_pct"))
                          for k, v in r["archives"].items() if isinstance(v, dict)})
print("front spreads:", json.dumps(cost["fronts"], indent=1))
