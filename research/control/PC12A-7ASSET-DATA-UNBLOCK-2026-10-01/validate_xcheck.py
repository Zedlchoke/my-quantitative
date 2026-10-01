#!/usr/bin/env python
"""Cross-source validation for PC12A-7ASSET-DATA-UNBLOCK-2026-10-01.

Builds IBKR D1 mid panels (BID/ASK year chunks) and CONTFUT TRADES panels from
the PC12A probe raw dir, parses every landed independent archive, and measures
per-asset overlap bases. All numbers derive from the landed raw bytes; nothing
is hand-typed. Emits XCHECK_REPORT.json.

Honesty rules encoded:
- ETF (SLV/GLD) archives are PROXIES: daily-return agreement only, never a
  spot-level PIT basis.
- Energy joins are EIA official SPOT vs IBKR CONTFUT front-continuous: the
  basis is structural (term structure), NOT a PIT gate; flat-OHLC synthetic
  share is disclosed on the aligned set.
- BoE files are HTML error pages -> excluded, listed as failed.
"""
from __future__ import annotations
import json
import math
import statistics as st
from datetime import date, datetime, timezone
from pathlib import Path

RAW = Path.home() / ".my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw"
IBKR = Path.home() / ".my-quantitative-data/portfolio-composite-12assets-100k-v1/ibkr_acq_20260930"
CTL = Path("/Users/hoangminhlong/my-quantitative/.worktrees/pc12a-7asset-unblock-20261001/research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01")
TD_XAU = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng6/integration/research/control/forex_ng6_run/p0/staging/XAUUSD_1day_full.json")
YEARS = ["20210930", "20220930", "20230930", "20240930", "20250930", "20260930"]
WINDOW = ("2020-10-01", "2026-09-30")


def pctl(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    f, c = math.floor(k), math.ceil(k)
    return xs[f] if f == c else xs[f] + (xs[c] - xs[f]) * (k - f)


def gap_holes(dates):
    ds = sorted(dates)
    if not ds:
        return None, 0
    mx = max((date.fromisoformat(b) - date.fromisoformat(a)).days
             for a, b in zip(ds, ds[1:]))
    holes = sum(1 for a, b in zip(ds, ds[1:])
                if (date.fromisoformat(b) - date.fromisoformat(a)).days > 5)
    return mx, holes


def span(dates, name):
    ds = sorted(d for d in dates if WINDOW[0] <= d <= WINDOW[1])
    if not ds:
        return {"source": name, "n_window": 0, "verdict": "NO_OVERLAP_WITH_WINDOW"}
    mx, holes = gap_holes(ds)
    return {"source": name, "n_window": len(ds), "first": ds[0], "last": ds[-1],
            "max_calendar_gap": mx, "holes_gt5d": holes,
            "coverage_note": "business-day calendars differ (ECB/Fed/EIA/venue holidays)"}


# ------------------------------------------------------------ IBKR panels ---
def ibkr_mid(asset):
    out = {}
    for y in YEARS:
        b = json.loads((IBKR / f"{asset}_1d_BID_{y}.json").read_text())
        a = json.loads((IBKR / f"{asset}_1d_ASK_{y}.json").read_text())
        bid = {r["date"]: r["close"] for r in b if r.get("close")}
        ask = {r["date"]: r["close"] for r in a if r.get("close")}
        for d in bid.keys() & ask.keys():
            if bid[d] > 0 and ask[d] >= bid[d] > 0:
                out[d] = (bid[d] + ask[d]) / 2
    return out


def ibkr_contfut(asset):
    rows = json.loads((IBKR / f"{asset}_CONTFUT_TRADES_1d_6Y.json").read_text())
    out = {}
    flat = 0
    for r in rows:
        d = r["date"][:10]
        o, h, l, c = r["open"], r["high"], r["low"], r["close"]
        is_flat = (o == h == l == c)
        flat += is_flat
        out[d] = {"close": c, "flat": is_flat, "volume": r.get("volume")}
    return out, flat, len(rows)


# ---------------------------------------------------------- source parsers ---
def parse_ecb():
    """ECB hist CSV -> {date: {ccy: rate}} (rates are CCY per 1 EUR)."""
    txt = (RAW / "ecb_eurofxref_hist.csv").read_text().splitlines()
    hdr = txt[0].split(",")
    idx = {c: i for i, c in enumerate(hdr)}
    out = {}
    for line in txt[1:]:
        p = line.split(",")
        if len(p) < 3:
            continue
        d = p[0]
        try:
            out[d] = {"USD": float(p[idx["USD"]]), "NZD": float(p[idx["NZD"]]),
                      "CHF": float(p[idx["CHF"]])}
        except (KeyError, ValueError):
            continue
    return out


def parse_fred(fname, invert=False):
    out = {}
    for line in (RAW / fname).read_text().splitlines()[1:]:
        d, v = line.split(",")
        if v in (".", ""):
            continue
        x = float(v)
        out[d] = (1.0 / x) if invert else x
    return out


def parse_eia_v2(fname):
    j = json.loads((RAW / fname).read_text())
    return {r["period"]: float(r["value"]) for r in j["rows"]
            if r.get("value") not in (None, "w") }


def parse_eodhd(fname):
    rows = json.loads((RAW / fname).read_text())
    return {r["date"]: float(r["adjusted_close"]) for r in rows}


def parse_td_xau():
    j = json.loads(TD_XAU.read_text())
    return {v["datetime"]: float(v["close"]) for v in j["values"]}


# -------------------------------------------------------------- join stats ---
def basis_stats(ibkr: dict, src: dict, srcname, unit_note=""):
    common = sorted(d for d in (ibkr.keys() & src.keys()) if WINDOW[0] <= d <= WINDOW[1])
    if not common:
        return {"source": srcname, "n_aligned": 0, "verdict": "NO_COMMON_DATES"}
    bps = [(ibkr[d] - src[d]) / src[d] * 1e4 for d in common]
    signed_native = [ibkr[d] - src[d] for d in common]
    absbps = [abs(x) for x in bps]
    top = sorted(zip(absbps, common), reverse=True)[:5]
    return {
        "source": srcname, "n_aligned": len(common),
        "first": common[0], "last": common[-1],
        "signed_mean_native": st.mean(signed_native),
        "signed_mean_bps": st.mean(bps),
        "signed_median_bps": st.median(bps),
        "abs_p50_bps": pctl(absbps, .50), "abs_p95_bps": pctl(absbps, .95),
        "abs_max_bps": max(absbps),
        "worst5_dates": [{"date": d, "abs_bps": round(a, 4)} for a, d in top],
        "unit_note": unit_note,
        "definition": "basis_bps = (IBKR_daily_mid - archive_value)/archive_value*1e4; "
                      "IBKR mid = (BIDclose+ASKclose)/2; fixing-time mismatch "
                      "(H.10 noon / ECB 16:00 CET vs IBKR ET session close) is "
                      "included in the basis and is why p95 tail exists",
    }


def proxy_stats(ibkr: dict, proxy: dict, srcname):
    """ETF proxy: daily-return agreement, never level basis."""
    common = sorted(d for d in (ibkr.keys() & proxy.keys()) if WINDOW[0] <= d <= WINDOW[1])
    if len(common) < 100:
        return {"source": srcname, "n_aligned": len(common), "verdict": "TOO_FEW_FOR_PROXY_METRIC"}
    def ret(series, dlist):
        return [(series[b] / series[a] - 1) for a, b in zip(dlist, dlist[1:])
                if a in series and b in series]
    # align consecutive-pair returns on common dates only
    pairs = [(a, b) for a, b in zip(common, common[1:])]
    ri = [ibkr[b] / ibkr[a] - 1 for a, b in pairs]
    rp = [proxy[b] / proxy[a] - 1 for a, b in pairs]
    n = len(ri)
    mi, mp = st.mean(ri), st.mean(rp)
    cov = sum((x - mi) * (y - mp) for x, y in zip(ri, rp)) / n
    corr = cov / (st.pstdev(ri) * st.pstdev(rp))
    diffs = [abs(x - y) * 1e4 for x, y in zip(ri, rp)]
    return {
        "source": srcname, "metric": "ETF-PROXY daily-return agreement (NOT a level PIT basis)",
        "n_aligned_dates": len(common), "n_return_pairs": n,
        "pearson_r": round(corr, 6),
        "mean_abs_return_diff_bps": round(st.mean(diffs), 4),
        "p95_abs_return_diff_bps": round(pctl(diffs, .95), 4),
        "first": common[0], "last": common[-1],
    }


def energy_join(name, spot: dict, contfut: dict, flat_total, rows_total):
    common = sorted(d for d in (spot.keys() & contfut.keys()) if WINDOW[0] <= d <= WINDOW[1])
    if not common:
        return {"asset": name, "n_aligned": 0}
    basis = [contfut[d]["close"] - spot[d] for d in common]  # futures minus spot
    flat_aligned = sum(1 for d in common if contfut[d]["flat"])
    pairs = list(zip(common, common[1:]))
    agree = sum(1 for a, b in pairs
                if (contfut[b]["close"] - contfut[a]["close"]) * (spot[b] - spot[a]) > 0)
    nz_pairs = [(a, b) for a, b in pairs
                if (contfut[b]["close"] - contfut[a]["close"]) != 0 and (spot[b] - spot[a]) != 0]
    agree_nz = sum(1 for a, b in nz_pairs
                   if (contfut[b]["close"] - contfut[a]["close"]) * (spot[b] - spot[a]) > 0)
    return {
        "asset": name,
        "n_aligned": len(common), "first": common[0], "last": common[-1],
        "basis_def": "IBKR CONTFUT close minus EIA official spot (same date)",
        "signed_mean_usd": round(st.mean(basis), 4),
        "signed_median_usd": round(st.median(basis), 4),
        "abs_p50_usd": round(pctl([abs(x) for x in basis], .5), 4),
        "abs_p95_usd": round(pctl([abs(x) for x in basis], .95), 4),
        "daily_change_sign_agreement": round(agree / len(pairs), 4),
        "daily_change_sign_agreement_nonzero_only": round(agree_nz / len(nz_pairs), 4) if nz_pairs else None,
        "nonzero_pairs": len(nz_pairs), "total_pairs": len(pairs),
        "flat_ohlc_bars_aligned": flat_aligned,
        "flat_share_aligned_pct": round(100 * flat_aligned / len(common), 2),
        "contfut_flat_share_total_pct": round(100 * flat_total / rows_total, 2),
        "caveat": "front-continuous vs spot basis is STRUCTURAL (term structure + roll), "
                  "not a PIT gate; synthetic flat bars per GATE_TABLE finding F-1",
    }


report = {
    "schema": "pc12a_7asset_xcheck_report@1",
    "session": "PC12A-7ASSET-DATA-UNBLOCK-2026-10-01",
    "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "window": WINDOW,
    "ibkr_provenance": "131 raw files, ~/.my-quantitative-data/portfolio-composite-12assets-100k-v1/ibkr_acq_20260930 (DV-verified sha256 2026-09-30)",
    "spans": {}, "overlaps": {}, "triangulation": {}, "energy": {}, "proxies": {},
    "excluded": {
        "boe_XUDLNZ/XUDLSF": "HTTP 200 served an HTML error page - UNAVAILABLE_FAIL_CLOSED",
        "twelvedata_XAG/USD": "plan-blocked (Grow/Venture only); no purchase permitted - UNAVAILABLE_FAIL_CLOSED",
        "stooq_xauusd/xagusd": "JavaScript proof-of-work anti-bot challenge - BLOCKED_TRANSPORT, zero circumvention",
        "lbma_gold/silver_pm.json, rbnz, perthmint, bundesbank-api": "HTTP 403 / empty reply - BLOCKED_NETWORK",
        "yahoo_GC=F/SI=F": "reachable but ToS prohibits automated access - REJECTED_LICENSE, not fetched",
    },
}

ecb = parse_ecb()
# ECB crosses (rates are CCY per EUR)
ecb_nzdusd = {d: v["USD"] / v["NZD"] for d, v in ecb.items()}
ecb_usdchf = {d: v["CHF"] / v["USD"] for d, v in ecb.items()}
fred_nzdusd = parse_fred("fred_DEXUSNZ.csv")            # USD per NZD == NZDUSD
fred_usdchf = parse_fred("fred_DEXSZUS.csv")  # already USDCHF convention (CHF per USD): 2026-09-24 DEXSZUS 0.8286 vs IBKR mid 0.8278 - inversion ERRATUM, corrected this session
eia_brent = parse_eia_v2("eia_v2_RBRTE_daily.json")
eia_wti = parse_eia_v2("eia_v2_RWTC_daily.json")
eia_hh = parse_eia_v2("eia_v2_RNGWHHD_daily.json")
fred_brent = parse_fred("fred_DCOILBRENTEU.csv")
fred_wti = parse_fred("fred_DCOILWTICO.csv")
fred_hh = parse_fred("fred_DHHNGSP.csv")
slv = parse_eodhd("eodhd_SLV_US_eod.json")
gld = parse_eodhd("eodhd_GLD_US_eod.json")
td_xau = parse_td_xau()

for nm, series in [("ECB_cross_NZDUSD", ecb_nzdusd), ("FRED_H10_NZDUSD", fred_nzdusd),
                   ("ECB_cross_USDCHF", ecb_usdchf), ("FRED_H10_USDCHF", fred_usdchf),
                   ("EIA_RBRTE", eia_brent), ("EIA_RWTC", eia_wti), ("EIA_RNGWHHD", eia_hh),
                   ("FRED_DCOILBRENTEU", fred_brent), ("FRED_DCOILWTICO", fred_wti),
                   ("FRED_DHHNGSP", fred_hh), ("EODHD_SLV", slv), ("EODHD_GLD", gld),
                   ("TD_XAUUSD", td_xau)]:
    report["spans"][nm] = span(series.keys(), nm)

# sanity: ECB vs FRED mutual agreement (source triangulation, no IBKR)
def mutual(a, b, an, bn):
    common = sorted(d for d in (a.keys() & b.keys()) if WINDOW[0] <= d <= WINDOW[1])
    if not common:
        return {"pair": f"{an}_vs_{bn}", "n": 0}
    bps = [(a[d] - b[d]) / b[d] * 1e4 for d in common]
    ab = [abs(x) for x in bps]
    return {"pair": f"{an}_vs_{bn}", "n": len(common),
            "abs_p50_bps": round(pctl(ab, .5), 4), "abs_p95_bps": round(pctl(ab, .95), 4),
            "signed_mean_bps": round(st.mean(bps), 4)}

report["triangulation"]["NZDUSD"] = mutual(ecb_nzdusd, fred_nzdusd, "ECB", "FRED")
report["triangulation"]["USDCHF"] = mutual(ecb_usdchf, fred_usdchf, "ECB", "FRED")
report["triangulation"]["BRENT"] = mutual(eia_brent, fred_brent, "EIA", "FRED")
report["triangulation"]["WTI"] = mutual(eia_wti, fred_wti, "EIA", "FRED")
report["triangulation"]["HENRYHUB"] = mutual(eia_hh, fred_hh, "EIA", "FRED")

for asset in ["NZDUSD", "USDCHF", "XAUUSD", "XAGUSD"]:
    mid = ibkr_mid(asset)
    report["spans"][f"IBKR_{asset}_mid"] = span(mid.keys(), f"IBKR_{asset}")
    if asset == "NZDUSD":
        report["overlaps"][asset] = [
            basis_stats(mid, ecb_nzdusd, "ECB_eurofxref_cross"),
            basis_stats(mid, fred_nzdusd, "FRED_H10_DEXUSNZ")]
    elif asset == "USDCHF":
        report["overlaps"][asset] = [
            basis_stats(mid, ecb_usdchf, "ECB_eurofxref_cross"),
            basis_stats(mid, fred_usdchf, "FRED_H10_DEXSZUS")]
    elif asset == "XAUUSD":
        report["overlaps"][asset] = [
            basis_stats(mid, td_xau, "TD_archive_XAUUSD_1day_full")]
    elif asset == "XAGUSD":
        report["overlaps"][asset] = []  # spot-level archives: none reachable

report["proxies"]["XAGUSD_SLV"] = proxy_stats(ibkr_mid("XAGUSD"), slv, "EODHD_SLV_US")
report["proxies"]["XAUUSD_GLD"] = proxy_stats(ibkr_mid("XAUUSD"), gld, "EODHD_GLD_US")

for asset, spot in [("BRENT", eia_brent), ("WTI", eia_wti), ("NATGAS", eia_hh)]:
    cf, flat, total = ibkr_contfut(asset)
    report["spans"][f"IBKR_{asset}_contfut"] = span(cf.keys(), f"IBKR_{asset}_contfut")
    report["energy"][asset] = energy_join(asset, spot, cf, flat, total)

out = CTL / "XCHECK_REPORT.json"
out.write_text(json.dumps(report, indent=1))
print("written", out)
for k in ["overlaps", "triangulation", "energy", "proxies"]:
    print("\n==", k)
    print(json.dumps(report[k], indent=1)[:3000])
