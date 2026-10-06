#!/usr/bin/env python3
"""A7-INTEGRATION audit script 1: re-derive the CoT exact-name mapping from raw
deacot zips INDEPENDENTLY of the INTEGRATION-FIX-V2 lookup tables.

Method: keyword-family scan of every stripped market name in all 21 annual
deacot zips (2006-2026). For each family keyword set (chosen by this auditor
from symbol semantics, NOT from the fix's tables), list every matching name
with row counts and date spans. Then compare against the delivered
cftc_legacy_tidy.parquet (canonical + __ALT__) and the fix's lookup to find:
  (a) in-scope family lines silently DROPPED (in raw, in neither canonical nor ALT);
  (b) lines mapped canonical that carry duplicate dates (mixing);
  (c) weekly-grid completeness of each canonical union (1,082 weeks claim).
READ-ONLY on raw; writes only under audit/a7_integration/.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

RAW = Path("/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms")
HERE = Path(__file__).resolve().parent

# Independent family keywords (auditor's own; deliberately broad).
FAMILIES = {
    "NQ": ["NASDAQ"],
    "ES": ["S&P 500", "S&P500"],
    "CL": ["CRUDE OIL", "WTI"],
    "NG": ["NATURAL GAS", "NAT GAS"],
    "GC": ["GOLD"],
    "SI": ["SILVER"],
    "6E": ["EURO FX"],
    "6J": ["JAPANESE YEN"],
    "6B": ["BRITISH POUND"],
    "6A": ["AUSTRALIAN DOLLAR"],
}


def read_zip(path: Path) -> pd.DataFrame | None:
    try:
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".txt"))
            with z.open(name) as f:
                data = f.read()
        return pd.read_csv(io.BytesIO(data), low_memory=False)
    except Exception as e:  # noqa: BLE001
        print(f"  !! {path.name}: {type(e).__name__}")
        return None


def main() -> None:
    # ---- 1. raw scan: every name matching a family keyword ----
    names: dict[str, dict[str, dict]] = defaultdict(dict)  # fam -> name -> stats
    for z in sorted((RAW / "cftc/legacy_futures_only").glob("deacot*.zip")):
        df = read_zip(z)
        if df is None or df.empty:
            continue
        date_col = [c for c in df.columns if c.startswith("As of Date in Form YYYY")][0]
        stripped = df["Market and Exchange Names"].astype(str).str.strip()
        for fam, kws in FAMILIES.items():
            mask = stripped.apply(lambda m: any(k in m.upper() for k in kws))
            for name, g in df[mask].groupby(stripped[mask]):
                dates = []
                for v in g[date_col]:
                    try:
                        dates.append(dt.date.fromisoformat(str(v)).isoformat())
                    except Exception:
                        pass
                st = names[fam].setdefault(name, {"rows": 0, "first": "9999", "last": "0000"})
                st["rows"] += len(dates)
                if dates:
                    st["first"] = min(st["first"], min(dates))
                    st["last"] = max(st["last"], max(dates))

    print("=== RAW deacot family-name census (independent keywords) ===")
    for fam in FAMILIES:
        print(f"\n[{fam}]")
        for name, st in sorted(names[fam].items(), key=lambda kv: -kv[1]["rows"]):
            print(f"  {st['rows']:5d}  {st['first']}..{st['last']}  {name!r}")

    # ---- 2. delivered tidy: per series_id stats ----
    tidy = pd.read_parquet(RAW / "normalized/cftc_legacy_tidy.parquet")
    print("\n=== DELIVERED cftc_legacy_tidy.parquet (sha f7a2719e) ===")
    print("total rows:", len(tidy))
    rep = {}
    for sid, g in tidy.groupby("series_id"):
        rep[sid] = {
            "rows": int(len(g)),
            "dup_dates": int(g.duplicated("observation_period").sum()),
            "first": g.observation_period.min(),
            "last": g.observation_period.max(),
            "market_names": sorted(g.market_name.unique().tolist()),
        }
        print(f"  {sid}: rows={rep[sid]['rows']} dup={rep[sid]['dup_dates']} "
              f"{rep[sid]['first']}..{rep[sid]['last']} names={rep[sid]['market_names']}")

    # ---- 3. cross-check: raw census names vs tidy coverage ----
    tidy_names = set(tidy.market_name.unique())
    print("\n=== CROSS-CHECK: raw family names NOT present in delivered tidy ===")
    dropped = {}
    for fam, nm in names.items():
        for name, st in nm.items():
            if name not in tidy_names:
                dropped.setdefault(fam, []).append((name, st))
                print(f"  DROPPED [{fam}] {st['rows']:5d} {st['first']}..{st['last']} {name!r}")
    if not dropped:
        print("  (none — every family-matching raw name appears in the tidy)")

    # ---- 4. weekly grid completeness for canonical series ----
    print("\n=== canonical weekly grid check (expected 1082 contiguous weeks) ===")
    grid = {}
    for sym in ["NQ", "ES", "6E", "6J", "6B", "6A", "CL", "NG", "GC", "SI"]:
        g = tidy[tidy.series_id == f"COT_LEGACY_{sym}"]
        d = sorted(pd.to_datetime(g.observation_period).dt.date)
        grid[sym] = {"n": len(d), "first": str(d[0]), "last": str(d[-1])}
        # weekly Tuesday grid check
        ds = pd.Series(d)
        gaps = ds.diff().dt.days.dropna()
        odd = gaps[(gaps < 5) | (gaps > 9)]
        grid[sym]["irregular_gaps"] = int(len(odd))
        grid[sym]["n_distinct"] = int(g.observation_period.nunique())
        print(f"  COT_LEGACY_{sym}: n={len(d)} distinct={g.observation_period.nunique()} "
              f"{d[0]}..{d[-1]} irregular_gaps={len(odd)}")

    out = {"raw_census": {f: {n: s for n, s in v.items()} for f, v in names.items()},
           "tidy_series": rep, "dropped_family_names": {f: v for f, v in dropped.items()},
           "canonical_grid": grid}
    (HERE / "a7_cot_rederive.json").write_text(json.dumps(out, indent=1, default=str))
    print("\nwrote", HERE / "a7_cot_rederive.json")


if __name__ == "__main__":
    main()
