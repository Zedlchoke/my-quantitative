"""CFTC CoT normalizer -> tidy tables.

Inputs (raw): cftc/legacy_futures_only/deacot{YYYY}.zip (annual.txt CSV inside),
cftc/tff/*.zip, cftc/disaggregated/*.zip.
Output columns: series_id, observation_period (Tuesday as-of), value,
released_at (Friday 15:30 ET convention - computed, disclosed as convention
not per-file timestamp), first_available_at (= released_at for as-published
legacy; NULL + flag for TFF/disagg backcast histories), vintage_flag,
provenance (source file sha256).

CFTC PIT law encoded:
- positions as-of Tuesday ("As of Date"), report released the following
  Friday 15:30 ET (RESEARCH_MATRIX CoT note, FACT) -> released_at >= as_of+2d.
- legacy futures-only as-published files are NOT revised (CFTC FAQ) ->
  vintage = as-published.
- TFF/disagg ANNUAL compressed histories are classification-backcasts (Form 40
  refresh every ~2 years) -> vintage_flag='classification_backcast_NOT_vintage';
  strict PIT use requires release-dated weekly files (not collected; caveat).
"""
from __future__ import annotations
import datetime as dt
import io
import json
import zipfile
from pathlib import Path

import pandas as pd

RAW = Path("/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms")
OUT = Path(__file__).resolve().parent / "oldtidy_sandbox"

MARKETS = {
    "NQ": ["NASDAQ-100 Consolidated", "NASDAQ MINI", "E-MINI NASDAQ-100"],
    "ES": ["S&P 500 Consolidated", "E-MINI S&P 500"],
    "CL": ["WTI-PHYSICAL", "CRUDE OIL, LIGHT SWEET"],
    "NG": ["NAT GAS NYME", "NATURAL GAS - NEW YORK MERCANTILE"],
    "GC": ["GOLD - COMMODITY EXCHANGE"],
    "SI": ["SILVER - COMMODITY EXCHANGE"],
    "6E": ["EURO FX - CHICAGO MERCANTILE EXCHANGE"],
    "6J": ["JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE"],
    "6B": ["BRITISH POUND - CHICAGO MERCANTILE EXCHANGE",
           "BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE"],
    "6A": ["AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE"],
}


def _read_zip_csv(path: Path) -> pd.DataFrame | None:
    try:
        with zipfile.ZipFile(path) as zf:
            inner = [n for n in zf.namelist() if n.lower().endswith(".txt")][0]
            with zf.open(inner) as f:
                return pd.read_csv(io.TextIOWrapper(f, encoding="latin-1"), low_memory=False)
    except Exception:
        return None


def _sha(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def next_friday_1530_et(as_of: dt.date) -> str:
    """CFTC release convention: following Friday 15:30 ET (FACT schedule).
    Computed, disclosed as convention-based released_at."""
    d = as_of
    days = (4 - d.weekday()) % 7  # Friday = 4
    if days == 0:
        days = 7  # always the FOLLOWING Friday
    fri = d + dt.timedelta(days=days)
    return f"{fri.isoformat()}T15:30:00-05:00/America_New_York_convention"


def market_symbol(name: str) -> str | None:
    for sym, pats in MARKETS.items():
        if any(p.lower() in name.lower() for p in pats):
            return sym
    return None


def normalize_legacy() -> pd.DataFrame:
    rows = []
    for z in sorted((RAW / "cftc/legacy_futures_only").glob("deacot*.zip")):
        df = _read_zip_csv(z)
        if df is None or df.empty:
            continue
        prov = _sha(z)
        date_col = [c for c in df.columns if c.startswith("As of Date in Form YYYY")][0]
        for sym, pats in MARKETS.items():
            mask = df["Market and Exchange Names"].apply(lambda m: any(p.lower() in str(m).lower() for p in pats))
            sub = df[mask]
            if sub.empty:
                continue
            for _, r in sub.iterrows():
                try:
                    as_of = dt.date.fromisoformat(str(r[date_col]))
                except Exception:
                    continue
                row = {
                    "series_id": f"COT_LEGACY_{sym}",
                    "observation_period": as_of.isoformat(),
                    "released_at": next_friday_1530_et(as_of),
                    "first_available_at": next_friday_1530_et(as_of),
                    "vintage_flag": "as_published_no_revision",
                    "market_name": r["Market and Exchange Names"],
                    "open_interest_all": r.get("Open Interest (All)"),
                    "noncomm_long": r.get("Noncommercial Positions-Long (All)"),
                    "noncomm_short": r.get("Noncommercial Positions-Short (All)"),
                    "noncomm_spreading": r.get("Noncommercial Positions-Spreading (All)"),
                    "comm_long": r.get("Commercial Positions-Long (All)"),
                    "comm_short": r.get("Commercial Positions-Short (All)"),
                    "provenance_sha256": prov,
                }
                rows.append(row)
    return pd.DataFrame(rows)


def normalize_fin(products: list[tuple[str, str]]) -> pd.DataFrame:
    """TFF/disagg annual zips -> tidy with backcast caveat flag."""
    rows = []
    for rel_dir, series_prefix in products:
        for z in sorted((RAW / rel_dir).glob("*.zip")):
            df = _read_zip_csv(z)
            if df is None or df.empty:
                continue
            prov = _sha(z)
            name_col = df.columns[0]
            date_col = [c for c in df.columns
                        if "As of Date" in c or "Report_Date_as" in c or "Report_Date_as_YYYY" in c][0]
            for sym, pats in MARKETS.items():
                mask = df[name_col].apply(lambda m: any(p.lower() in str(m).lower() for p in pats))
                sub = df[mask]
                for _, r in sub.iterrows():
                    try:
                        as_of = dt.date.fromisoformat(str(r[date_col]).split(" ")[0])
                    except Exception:
                        continue
                    vals = {c: r.get(c) for c in df.columns
                            if any(k in c for k in ("Asset Manager", "Leveraged Funds",
                                                    "Producer/Merchant", "Swap", "Managed Money",
                                                    "Other Reportables", "Open Interest"))}
                    rows.append({
                        "series_id": f"{series_prefix}_{sym}",
                        "observation_period": as_of.isoformat(),
                        "released_at": next_friday_1530_et(as_of),
                        "first_available_at": None,
                        "vintage_flag": "classification_backcast_NOT_vintage",
                        "market_name": r[name_col],
                        **vals,
                        "provenance_sha256": prov,
                    })
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    legacy = normalize_legacy()
    if not legacy.empty:
        legacy.to_parquet(OUT / "cftc_legacy_tidy.parquet")
        print("legacy rows:", len(legacy))
        print(legacy.groupby("series_id").agg(
            n=("observation_period", "size"),
            first=("observation_period", "min"), last=("observation_period", "max")))
    fin = normalize_fin([("cftc/tff", "COT_TFF"), ("cftc/disaggregated", "COT_DISAGG")])
    if not fin.empty:
        fin.to_parquet(OUT / "cftc_tff_disagg_tidy.parquet")
        print("tff/disagg rows:", len(fin))


if __name__ == "__main__":
    main()
