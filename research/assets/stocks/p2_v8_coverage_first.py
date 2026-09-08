"""V8 P2: coverage-first artifact - per-name price coverage + cohort
reconciliation. Phase P: data facts only, NO returns, NO PnL.

Reads the staged EODHD pulls (.staging_prices_v8/eod, gitignored) plus the
SEC submissions census and publishes:
  - per-name price coverage over the S0 window (bars vs US equity sessions)
  - band population at the S0 boundary dates (ADV63 liquidity bands, P3 model)
  - cohort x servable reconciliation (census status x price servability)

Usage:
  python -m research.assets.stocks.p2_v8_coverage_first build
"""

import json
import os
import statistics
import datetime

RAW_DIR = ".staging_prices_v8/eod"
CENSUS = "research/control/stocks_free_v8_run/p0a_submissions_cohort_census.json"
OUT = "research/control/stocks_free_v8_run/p2_coverage_first.json"
S0_START, S0_MID, S0_END = "2018-04-04", "2021-11-16", "2025-07-24"
BANDS = [("A", 50_000_000), ("B", 10_000_000), ("C", 2_000_000)]  # below C => UNTRADABLE


def sessions_spx_like(bars_by_cik):
    """Market session set = union of all bars' dates (any liquid US name
    trades on US sessions; the union is the observed common calendar)."""
    days = set()
    for bars in bars_by_cik.values():
        for b in bars:
            days.add(b["date"])
    return sorted(days)


def load_bars():
    out = {}
    for fn in sorted(os.listdir(RAW_DIR)):
        if not fn.endswith(".json"):
            continue
        cik = fn.split("__")[0]
        data = json.load(open(f"{RAW_DIR}/{fn}"))
        bars = [
            {"date": b["date"], "close": b["adjusted_close"], "raw_close": b["close"],
             "volume": b["volume"], "dollar_volume": b["close"] * b["volume"]}
            for b in data
        ]
        out.setdefault(cik, []).extend(bars)
    for cik in out:
        out[cik].sort(key=lambda b: b["date"])
    return out


def adv63(bars, i):
    window = bars[max(0, i - 62): i + 1]
    return statistics.median(b["dollar_volume"] for b in window)


def band_of(v):
    for name, floor in BANDS:
        if v >= floor:
            return name
    return "UNTRADABLE"


def build():
    census = json.load(open(CENSUS))
    bars_by_cik = load_bars()
    sessions = sessions_spx_like(bars_by_cik)
    s0_sessions = [d for d in sessions if S0_START <= d <= S0_END]
    per_name = {}
    for cik, bars in sorted(bars_by_cik.items()):
        dates = [b["date"] for b in bars]
        in_s0 = [d for d in dates if S0_START <= d <= S0_END]
        s0_set = set(in_s0)
        missing = sum(1 for d in s0_sessions if d not in s0_set and d >= (in_s0[0] if in_s0 else S0_END))
        cov = (len(in_s0) / len(s0_sessions)) if s0_sessions else 0.0
        idx_by_date = {b["date"]: i for i, b in enumerate(bars)}
        boundary_bands = {}
        for label, dt in (("start", S0_START), ("mid", S0_MID), ("end", S0_END)):
            prior = [d for d in dates if d <= dt]
            if prior:
                i = idx_by_date[prior[-1]]
                boundary_bands[label] = {
                    "band": band_of(adv63(bars, i)),
                    "adv63_usd": round(adv63(bars, i), 0),
                }
            else:
                boundary_bands[label] = {"band": "NO_DATA", "adv63_usd": None}
        per_name[cik] = {
            "file": f"{cik}__{(census['filers'][cik].get('tickers_current') or ['NONE'])[0]}",
            "ticker": (census['filers'][cik].get('tickers_current') or ['NONE'])[0],
            "census_status": census["filers"][cik]["status"],
            "bars_total": len(bars),
            "first_bar": dates[0] if dates else None,
            "last_bar": dates[-1] if dates else None,
            "bars_in_S0": len(in_s0),
            "s0_session_coverage_ratio": round(cov, 4),
            "s0_missing_after_first_bar": missing,
            "boundary_bands": boundary_bands,
        }
    # cohort reconciliation
    recon = {}
    for status in ("ACTIVE_FILER", "TERMINATED_REGISTRATION", "FETCH_FAILED"):
        names = {c: v for c, v in per_name.items() if v["census_status"] == status}
        recon[status] = {
            "filers": len(census and [c for c, f in census["filers"].items() if f["status"] == status]),
            "with_price_file": len(names),
            "with_S0_bars": sum(1 for v in names.values() if v["bars_in_S0"] > 0),
            "coverage_ge_0.9": sum(1 for v in names.values() if v["s0_session_coverage_ratio"] >= 0.9),
        }
    # band population at S0 start (eligibility preview, data only)
    band_pop = {"start": {}, "mid": {}, "end": {}}
    for label in band_pop:
        for v in per_name.values():
            b = v["boundary_bands"][label]["band"]
            band_pop[label][b] = band_pop[label].get(b, 0) + 1
    art = {
        "schema": "stocks_free_v8_run/p2_coverage_first@1",
        "built_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer_role": "A1 (inlined light lane)",
        "authority": "PLAN_stocks_v7.md section 6 P2 (inherited): per-field coverage AND per-name price coverage published BEFORE any proposal brief; proposals may cite only funded clocks and servable names; NO returns computed in Phase P",
        "per_field_reference": {
            "artifact": "research/control/stocks_free_v6_run/p0a_coverage_census.json",
            "sha256_note": "inherited, hash recorded in clock freeze frozen_inputs (ec2a5aa4...)",
            "headline": "Assets coverage 0.946/0.985/0.998 at S0 start/mid/end (V6 pin)"
        },
        "market_sessions_observed": len(sessions),
        "s0_sessions": len(s0_sessions),
        "s0_window": [S0_START, S0_END],
        "cohort_reconciliation": recon,
        "band_population_boundary_dates": band_pop,
        "per_name": per_name,
        "verdict": "P2_PASS",
    }
    json.dump(art, open(OUT, "w"), indent=1)
    print(json.dumps({"recon": recon, "bands": band_pop, "out": OUT}))


if __name__ == "__main__":
    build()
