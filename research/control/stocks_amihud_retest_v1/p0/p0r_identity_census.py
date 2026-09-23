"""RETEST-V1 P0-I/B: identity + bar-validity census -> quarantine manifest.

Frozen laws (plan §2 I3, §3 B1; A7 r1 F-2/F-3 carries applied):
  Q1 GHOST      edgar_absent AND no_isin AND (shared-death batch >=20 OR
                has C8 extreme print)
  Q2 VENDOR-TEST code starts NTEST or contains TEST
  Q3 DUPLICATE  same-ISIN group: keep lexicographically-first code; any
                other member with return-corr >= 0.999 vs the KEPT member
                on >= 200 common bars -> quarantined (others: flag only)
  Q4 NO-SERIES  staged file missing/empty
  B1 C8 flag    |log(adj_d / adj_{d-1})| >= log(10)  (BOTH directions)
Census only; no PnL of any kind. EDGAR current tickers fetched with a
declared UA (SEC 403 otherwise); if EDGAR unreachable -> channel
UNAVAILABLE recorded and edgar_absent treated True (fail-closed tightens
Q1 — disclosed in the manifest header).
"""
from __future__ import annotations

import csv
import io
import json
import math
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGING = HERE / "staging_eod_csv"
OUT_MANIFEST = HERE / "quarantine_manifest.jsonl"
OUT_UNIVERSE = HERE / "universe_retest_frozen.json"
OUT_CENSUS = HERE / "identity_census.json"
LOG10 = math.log(10.0)
UA = "my-quantitative-research/1.0 (research contact: owner@local)"


def load_series(code: str):
    p = STAGING / f"{code}.csv"
    if not p.exists():
        return None
    rows = []
    with p.open(newline="") as f:
        for r in csv.DictReader(f):
            try:
                rows.append((r["Date"], float(r["Adjusted_close"]),
                             float(r["Close"]), float(r["Volume"])))
            except (ValueError, KeyError, TypeError):
                continue
    return rows or None


def fetch_edgar_current() -> tuple[set[str] | None, str]:
    url = "https://www.sec.gov/files/company_tickers.json"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
        return {v["ticker"].upper() for v in data.values()}, "OK"
    except Exception as e:
        return None, f"UNAVAILABLE: {e!r}"


def main() -> None:
    uni = json.loads((HERE / "universe_frozen.json").read_text())
    codes_all = sorted(uni["codes"].keys())
    meta = {}
    with (HERE / "raw_us_symbol_list_delisted.csv").open() as f:
        for r in csv.DictReader(f):
            meta[r["Code"]] = r
    edgar, edgar_status = fetch_edgar_current()

    series: dict[str, list] = {}
    isin_map: dict[str, str] = {}
    spans: dict[str, tuple[str, str, int]] = {}
    extreme: dict[str, list[str]] = defaultdict(list)
    batch_counter: dict[tuple[str, int], list[str]] = defaultdict(list)

    for code in codes_all:
        rows = load_series(code)
        if rows is None:
            series[code] = None
            continue
        series[code] = rows
        spans[code] = (rows[0][0], rows[-1][0], len(rows))
        batch_counter[(rows[-1][0], len(rows))].append(code)
        m = meta.get(code, {})
        isin = (m.get("Isin") or "").strip()
        if isin:
            isin_map[code] = isin
        for i in range(1, len(rows)):
            a0, a1 = rows[i - 1][1], rows[i][1]
            if a0 > 0 and a1 > 0 and abs(math.log(a1 / a0)) >= LOG10:
                extreme[code].append(rows[i][0])
                break  # flag only; count of codes matters for Q1

    # death batch = common (last, bars) group of >=20 whose last date is
    # BEFORE the window end (names ending 2022-12-30 are window survivors,
    # not a death batch) — interpretation pinned pre-PnL, plan §2 I3 wording
    batches = {k for k, v in batch_counter.items()
               if len(v) >= 20 and k[0] < "2022-12-30"}
    quarantine = {}
    notes_global = (["EDGAR_UNAVAILABLE_TREATING_ABSENT"] if edgar is None
                    else [])
    for code in codes_all:
        m = meta.get(code, {})
        reasons = []
        if series[code] is None:
            reasons.append("Q4_NO_SERIES")
        else:
            isin = (m.get("Isin") or "").strip()
            edgar_absent = (edgar is None) or (code not in edgar)
            if code.upper().startswith("NTEST") or "TEST" in code.upper():
                reasons.append("Q2_VENDOR_TEST")
            if (not isin) and edgar_absent and \
               (((spans[code][1], spans[code][2]) in batches)
               or code in extreme):
                reasons.append("Q1_GHOST")
        if reasons:
            quarantine[code] = reasons

    # Q3 duplicates: same-ISIN groups, corr vs KEPT member
    by_isin = defaultdict(list)
    for code, isin in isin_map.items():
        by_isin[isin].append(code)
    def returns(rows):
        return {(rows[i][0]): rows[i][1] / rows[i - 1][1]
                for i in range(1, len(rows))
                if rows[i - 1][1] > 0 and rows[i][1] > 0}
    dup_removed = []
    for isin, group in sorted(by_isin.items()):
        live = sorted(c for c in group if series.get(c) and c not in quarantine)
        if len(live) < 2:
            continue
        kept = live[0]
        rk = returns(series[kept])
        for other in live[1:]:
            ro = returns(series[other])
            common = sorted(set(rk) & set(ro))
            if len(common) < 200:
                continue
            num = sum(rk[d] * ro[d] for d in common)
            den = math.sqrt(sum(rk[d] ** 2 for d in common) *
                            sum(ro[d] ** 2 for d in common))
            corr = num / den if den > 0 else 0.0
            if corr >= 0.999:
                quarantine.setdefault(other, []).append("Q3_DUPLICATE_OF_" + kept)
                dup_removed.append(other)

    kept_codes = [c for c in codes_all if c not in quarantine]
    # keep SPY/AAPL/TSLA extras available to the engine
    extras = [c for c in ("SPY", "AAPL", "TSLA") if c not in kept_codes]
    with OUT_MANIFEST.open("w") as f:
        for code in sorted(quarantine):
            ev = {"code": code, "reasons": quarantine[code]}
            if series.get(code) is not None:
                ev["span"] = spans[code]
                ev["series_sha_note"] = "raw file sha in predecessor crawl manifest"
            if code in extreme:
                ev["c8_first_date"] = extreme[code][0]
            f.write(json.dumps(ev) + "\n")
    universe = {
        "schema": "universe_retest_frozen/stocks_amihud_retest_v1@1",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "class": "OUTCOME_OBSERVED_RETROSPECTIVE_RETEST",
        "laws": "plan §2 I3 Q1-Q4 (Q1 both-direction C8 via log-ratio per A7 F-2; Q3 corr-vs-kept per A7 F-3)",
        "edgar_status": edgar_status,
        "edgar_fail_closed_note": notes_global,
        "death_batch_interpretation": "common (last,bars) group >=20 with last < 2022-12-30 (window-end survivors are not a death batch) — pinned pre-PnV",
        "counts": {
            "predecessor_universe": len(codes_all),
            "staged_with_series": sum(1 for v in series.values() if v),
            "quarantined_total": len(quarantine),
            "q1_ghost": sum(1 for r in quarantine.values() if any(x.startswith("Q1") for x in r)),
            "q2_vendor": sum(1 for r in quarantine.values() if any(x.startswith("Q2") for x in r)),
            "q3_duplicate": sum(1 for r in quarantine.values() if any(x.startswith("Q3") for x in r)),
            "q4_no_series": sum(1 for r in quarantine.values() if any(x.startswith("Q4") for x in r)),
            "kept": len(kept_codes),
            "extreme_print_names": len(extreme),
            "shared_death_batches_ge20": {f"{k[0]}|{k[1]}": len(v) for k, v in batch_counter.items() if len(v) >= 20},
        },
        "codes": {c: uni["codes"][c] for c in kept_codes},
        "extras": extras,
    }
    OUT_UNIVERSE.write_text(json.dumps(universe, indent=1))
    census = dict(universe["counts"])
    census["edgar_status"] = edgar_status
    census["sample_q1"] = [c for c in sorted(quarantine)
                           if any(x.startswith("Q1") for x in quarantine[c])][:15]
    census["sample_q3"] = dup_removed[:15]
    census["htv_nlgb_byon_ostk"] = {c: (quarantine.get(c) or "KEPT")
                                    for c in ("HTV", "NLG", "BYON", "OSTK")}
    OUT_CENSUS.write_text(json.dumps(census, indent=1))
    print(json.dumps(census, indent=1))


if __name__ == "__main__":
    main()
