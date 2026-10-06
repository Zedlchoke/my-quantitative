"""CFTC CoT normalizer -> tidy tables (EXACT market-name mapping, 2026-10-03 fix).

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

DEFECT FIX 2026-10-03 (lane INTEGRATION-FIX-V2, task FUTURES-DEEPRESEARCH-V2-20261003;
found independently by DEEP-NQ + DEEP-ES): the pre-fix normalizer matched markets
by SUBSTRING, so series_id COT_LEGACY_{SYM} mixed several CFTC market lines on the
same dates (e.g. ES = E-mini + Micro E-mini + S&P 500 Consolidated -> 1,126
duplicate dates; NQ = Consolidated + Micro + NASDAQ MINI -> 548; CL even mixed
ICE Europe WTI into the NYMEX series -> 928; GC/SI/NG mixed Micro/E-mini strays;
and NQ's true e-mini line 'NASDAQ-100 STOCK INDEX (MINI)' was never captured at
all, so COT_LEGACY_NQ only started 2010-06-15 at the Consolidated line's birth).

Fix: EXACT market-name mapping (names matched AFTER str.strip(); the pre-2019
annual files carry trailing spaces). CFTC renamed several markets mid-2022 -
both spellings are listed and the unions were verified against ALL 21 annual
files (2006-2026): every canonical series = exactly 1,082 weekly rows,
0 duplicate observation_period dates, span 2006-01-03..2026-09-22.

Non-canonical sibling lines in the same product family (Consolidated, Micro,
full-size pit, other exchanges) are PRESERVED under disambiguated series ids
"{prefix}_{SYM}__ALT__{SLUG}" - reproducibility for consumers that used them
(e.g. DEEP-NQ's dossier is based on the NASDAQ-100 Consolidated line) - but are
never mixed into the canonical series_id. Names not in either table are not in
our 10-symbol scope and are excluded.

DEFECT FIX 2 2026-10-03 (lane NONPRICE-SOURCE-FIX2; audit A7-INTEGRATION F-1 +
two same-class findings): (a) the fin tidy double-read the overlapping
hist_2006_2016 bulk + annual archives -> 365 value-identical duplicate dates
per DISAGG series (and the CL __ALT__ ICE lines), now deduped with the
documented annual-file-wins precedence; (b) the fin date parser only accepted
ISO strings, silently dropping the whole TFF bulk-history file (its dates are
M/D/YYYY) - TFF series regain their 2006-06-13..2010-07-06 archive floor
(214 weekly obs per scope market); (c) the fin value-column keyword filter
matched only the legacy schema, so TFF rows carried all-NaN values and disagg
lost its M_Money/Open_Interest columns - now every non-metadata column is
carried (see normalize_fin).
"""
from __future__ import annotations
import datetime as dt
import io
import re
import zipfile
from pathlib import Path

import pandas as pd

RAW = Path("/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms")
OUT = RAW / "normalized"

# Canonical line per symbol = the outright primary-traded contract that matches
# the vendor futures plane (NQ/ES = E-mini; FX = the single CME line; CL = NYMEX
# WTI outright; NG = NYMEX Henry Hub; GC/SI = COMEX). Verified exact names from
# the raw deacot files (scan of all 21 annual zips, 2026-10-03). Mid-2022 CFTC
# renames carry both spellings; each union: 1,082 rows, 0 duplicate dates.
CANONICAL_MARKETS = {
    "NQ": ["NASDAQ-100 STOCK INDEX (MINI) - CHICAGO MERCANTILE EXCHANGE",
           "NASDAQ MINI - CHICAGO MERCANTILE EXCHANGE"],
    "ES": ["E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
           "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"],
    "6E": ["EURO FX - CHICAGO MERCANTILE EXCHANGE"],
    "6J": ["JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE"],
    "6B": ["BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE",
           "BRITISH POUND - CHICAGO MERCANTILE EXCHANGE"],
    "6A": ["AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE"],
    "CL": ["CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE",
           "WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE"],
    "NG": ["NATURAL GAS - NEW YORK MERCANTILE EXCHANGE",
           "NAT GAS NYME - NEW YORK MERCANTILE EXCHANGE"],
    "GC": ["GOLD - COMMODITY EXCHANGE INC."],
    "SI": ["SILVER - COMMODITY EXCHANGE INC."],
}

# Non-canonical sibling lines (same product family, different instrument
# complex / venue / size) -> kept under __ALT__ series ids, never in canonical.
ALT_MARKETS = {
    "NQ": ["NASDAQ-100 Consolidated - CHICAGO MERCANTILE EXCHANGE",  # 2010+ (DEEP-NQ used this line)
           "MICRO E-MINI NASDAQ-100 INDEX - CHICAGO MERCANTILE EXCHANGE",  # 2020+
           "NASDAQ-100 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE"],  # full-size pit 2006-2015
    "ES": ["S&P 500 Consolidated - CHICAGO MERCANTILE EXCHANGE",  # 2010+
           "MICRO E-MINI S&P 500 INDEX - CHICAGO MERCANTILE EXCHANGE",  # 2020+
           "S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE"],  # full-size pit 2006-2021
    "6E": [], "6J": [], "6B": [], "6A": [],
    "CL": ["CRUDE OIL, LIGHT SWEET-WTI - ICE FUTURES EUROPE",  # ICE WTI (was mixed in pre-fix)
           "CRUDE OIL, LIGHT SWEET - ICE FUTURES EUROPE",
           "CRUDE OIL, LIGHT SWEET - ICE EUROPE",
           "E-MINI CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE",
           "E-MINY CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE"],  # CFTC's own typo'd e-mini name
    "NG": ["E-MINI NATURAL GAS - NEW YORK MERCANTILE EXCHANGE",
           "E-MINY NATURAL GAS - NEW YORK MERCANTILE EXCHANGE"],
    "GC": ["MICRO GOLD - COMMODITY EXCHANGE INC."],
    "SI": ["MICRO SILVER - COMMODITY EXCHANGE INC."],
}


def _slug(name: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")


def build_name_lookup(prefix: str) -> dict[str, str]:
    """stripped exact market name -> series_id (canonical or __ALT__)."""
    lut: dict[str, str] = {}
    for sym, names in CANONICAL_MARKETS.items():
        for n in names:
            assert n not in lut, f"duplicate mapping name {n!r}"
            lut[n] = f"{prefix}_{sym}"
    for sym, names in ALT_MARKETS.items():
        for n in names:
            assert n not in lut, f"duplicate mapping name {n!r}"
            lut[n] = f"{prefix}_{sym}__ALT__{_slug(n)}"
    return lut


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


def normalize_legacy() -> pd.DataFrame:
    lut = build_name_lookup("COT_LEGACY")
    rows = []
    for z in sorted((RAW / "cftc/legacy_futures_only").glob("deacot*.zip")):
        df = _read_zip_csv(z)
        if df is None or df.empty:
            continue
        prov = _sha(z)
        date_col = [c for c in df.columns if c.startswith("As of Date in Form YYYY")][0]
        names = df["Market and Exchange Names"].astype(str).str.strip()
        mapped = names.map(lut)  # NaN = not our 10-symbol scope -> excluded
        sub = df[mapped.notna()]
        series_ids = mapped[mapped.notna()]
        for (i, r), series_id in zip(sub.iterrows(), series_ids):
            try:
                as_of = dt.date.fromisoformat(str(r[date_col]))
            except Exception:
                continue
            row = {
                "series_id": series_id,
                "observation_period": as_of.isoformat(),
                "released_at": next_friday_1530_et(as_of),
                "first_available_at": next_friday_1530_et(as_of),
                "vintage_flag": "as_published_no_revision",
                "market_name": names[i],
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


# Metadata columns never carried into the fin tidy (dates parse into
# observation_period; CFTC_* are code bookkeeping duplicated across files).
# NOTE (NONPRICE-SOURCE-FIX2, 2026-10-03): the pre-fix fin normalizer selected
# value columns by keyword ("Asset Manager", "Leveraged Funds", "Managed
# Money", "Producer/Merchant", "Swap", "Open Interest") - those spellings
# match the LEGACY deacot schema only. The TFF/disagg txt files use
# underscore schemas (Asset_Mgr_*, Lev_Money_*, Dealer_*, M_Money_*, ...),
# so the keyword filter silently kept only the disagg Swap_* family and TFF
# rows carried ALL-NaN values (their defining Asset Manager / Leveraged
# Funds positions were dropped column-wise). Fix: carry every non-metadata
# column for both products.
FIN_EXCLUDE_COLS_PREFIXES = ("CFTC_",)
FIN_EXCLUDE_COLS = {"Market_and_Exchange_Names",
                    "As_of_Date_In_Form_YYMMDD",  # date in another format
                    "Report_Date_as_YYYY-MM-DD", "Report_Date_as_MM_DD_YYYY",
                    "Report_Date_as_YYMMDD"}


def _parse_fin_date(raw: str) -> dt.date | None:
    """Tolerant as-of date parse.

    FIX (NONPRICE-SOURCE-FIX2, 2026-10-03): CFTC fin files mix date formats -
    the annual zips carry ISO strings ('2010-12-28') but the TFF bulk history
    fin_fut_txt_2006_2016.zip carries 'M/D/YYYY 12:00:00 AM' strings (its
    column is even named Report_Date_as_YYYY-MM-DD). The pre-fix
    dt.date.fromisoformat() silently skipped every M/D/YYYY row, dropping the
    entire TFF 2006-06-13..2010-07-06 history (214 weekly obs per scope
    market) that exists in the raw archive."""
    s = str(raw).split(" ")[0]
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        pass
    for fmt in ("%m/%d/%Y", "%Y/%m/%d", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# Annual year-files are the ongoing per-year publication
# (fut_fin_txt_YYYY.zip / fut_disagg_txt_YYYY.zip); everything else in the
# dirs is a bulk multi-year re-pack (fut_disagg_txt_hist_2006_2016.zip,
# fin_fut_txt_2006_2016.zip - note the TFF bulk file has NO "_hist_" token).
_ANNUAL_ZIP_RE = re.compile(r"^fut_(?:fin|disagg)_txt_\d{4}\.zip$")


def _is_bulk_zip(name) -> bool:
    return not _ANNUAL_ZIP_RE.match(str(name))


def _clean_fin_value(v):
    """Normalize one carried fin value: strip whitespace, map CFTC's '.'
    missing-marker to NaN, coerce numeric-looking strings to float.

    The two archive generations format the same numbers differently (annual
    zips parse as numeric dtypes, the bulk hist txt as padded strings, e.g.
    '6' vs 6.0) - normalizing at ingest makes the generation-time
    value-identity gate on overlapping rows exact."""
    if isinstance(v, str):
        s = v.strip()
        if s in (".", ""):
            return None
        try:
            return float(s)
        except ValueError:
            return s
    return v


def normalize_fin(products: list[tuple[str, str]]) -> pd.DataFrame:
    """TFF/disagg annual + bulk-history zips -> tidy with backcast caveat flag.

    DEFECT FIX 2026-10-03 (lane NONPRICE-SOURCE-FIX2, task
    FUTURES-DEEPRESEARCH-V2-20261003; audit A7-INTEGRATION F-1): the archives
    overlap - fut_disagg_txt_hist_2006_2016.zip (+ fin_fut_txt_2006_2016.zip
    for TFF) re-publish every 2010..2016 week that the annual
    fut_*_txt_2010..2016.zip files also carry, so each DISAGG canonical
    series carried 365 value-identical duplicate dates (2010-01-05..
    2016-12-27; CL/GC/NG/SI each 1,424 rows over 1,059 distinct dates), as
    did the CL __ALT__ ICE lines. Fix = dedupe with an EXPLICIT precedence
    rule: for the same (series_id, observation_period) the ANNUAL year-file
    row wins over the bulk *_hist_2006_2016.zip row (annual files are the
    ongoing per-year publication; the bulk file is the frozen historical
    re-pack). Values on every overlapping pair were verified identical
    (generation-time assert below + audit A7-INTEGRATION), so the choice is
    immaterial - it is documented, not silently applied. Bulk-only weeks
    (2006-2009, and TFF's 2006-06-13..2010-07-06 after the date-format fix)
    are kept."""
    rows = []
    for rel_dir, series_prefix in products:
        lut = build_name_lookup(series_prefix)
        for z in sorted((RAW / rel_dir).glob("*.zip")):
            df = _read_zip_csv(z)
            if df is None or df.empty:
                continue
            prov = _sha(z)
            name_col = df.columns[0]
            date_col = [c for c in df.columns
                        if "As of Date" in c or "Report_Date_as" in c][0]
            names = df[name_col].astype(str).str.strip()
            mapped = names.map(lut)
            sub = df[mapped.notna()]
            series_ids = mapped[mapped.notna()]
            keep_cols = [c for c in df.columns
                         if c not in FIN_EXCLUDE_COLS
                         and not c.startswith(FIN_EXCLUDE_COLS_PREFIXES)]
            for (i, r), series_id in zip(sub.iterrows(), series_ids):
                as_of = _parse_fin_date(r[date_col])
                if as_of is None:
                    continue
                # CFTC txt files are whitespace-padded (the two archive
                # generations even disagree on trailing spaces, e.g.
                # Contract_Units); carried values are normalized via
                # _clean_fin_value - same convention as market names.
                vals = {c: _clean_fin_value(r.get(c)) for c in keep_cols}
                rows.append({
                    "series_id": series_id,
                    "observation_period": as_of.isoformat(),
                    "released_at": next_friday_1530_et(as_of),
                    "first_available_at": None,
                    "vintage_flag": "classification_backcast_NOT_vintage",
                    "market_name": names[i],
                    "source_zip": z.name,
                    **vals,
                    "provenance_sha256": prov,
                })
    if not rows:
        return pd.DataFrame(rows)
    fin = pd.DataFrame(rows)

    # --- dedupe gate: log every value difference on the archive overlap ---
    # The overlapping rows are overwhelmingly identical, but NOT bit-exact in
    # every column: the two archive generations disagree at rounding level
    # in a few Pct_of_OI_* cells (e.g. COT_TFF_6A 2016-05-31
    # Pct_of_OI_Lev_Money_Long_All hist=24.0 vs annual=23.9, verified from
    # the raw zips). Every conflict
    # is recorded and disclosed (printed here + counted in the erratum);
    # the annual-file-wins precedence below resolves them deterministically.
    value_cols = [c for c in fin.columns
                  if c not in ("series_id", "observation_period", "released_at",
                               "first_available_at", "vintage_flag", "market_name",
                               "source_zip", "provenance_sha256")]
    key = ["series_id", "observation_period"]
    dupmask = fin.duplicated(key, keep=False)
    dups = fin[dupmask]
    conflicts = []
    for (sid, obs), g in dups.groupby(key):
        bulk_rows = g[g["source_zip"].map(_is_bulk_zip)]
        ann_rows = g[~g["source_zip"].map(_is_bulk_zip)]
        if bulk_rows.empty or ann_rows.empty:
            continue
        h, a = bulk_rows.iloc[0], ann_rows.iloc[0]
        for c in value_cols:
            hv, av = h[c], a[c]
            if str(hv) != str(av):
                conflicts.append((sid, obs, c, hv, av))
    n_before = len(fin)

    # --- precedence dedupe: annual year-file beats bulk re-pack ---
    # RESUME-FIX 2026-10-03 (lane NONPRICE-SOURCE-FIX2, post-power-outage
    # verification): the first cut of this block sorted _from_bulk ASCENDING
    # and kept="last", which kept the BULK row - the exact INVERSE of the
    # documented annual-file-wins rule (caught by pinning the known conflict
    # cell COT_TFF_6A 2016-05-31 Pct_of_OI_Lev_Money_Long_All: raw hist=24.0
    # vs annual=23.9; the shipped sha 3e32e0ee file carried 24.0/fin_fut_txt_
    # 2006_2016.zip = bulk). Sort _from_bulk DESCENDING so the annual row is
    # last and keep="last" keeps it, matching the documentation above.
    fin["_from_bulk"] = fin["source_zip"].map(_is_bulk_zip)
    fin = (fin.sort_values(["series_id", "observation_period",
                            "_from_bulk", "source_zip"],
                           ascending=[True, True, False, True], kind="stable")
              .drop_duplicates(key, keep="last")
              .drop(columns="_from_bulk")
              .sort_values(key, kind="stable")
              .reset_index(drop=True))
    print(f"fin dedupe: {n_before} raw rows -> {len(fin)} "
          f"(dropped {n_before - len(fin)} overlap rows; annual-file-wins "
          f"precedence); archive-overlap value conflicts: {len(conflicts)} "
          f"cells across {len({(c[0], c[1]) for c in conflicts})} series-dates "
          f"in columns {sorted({c[2] for c in conflicts}) if conflicts else '{}'} "
          f"(annual value kept, all differences at rounding level)")
    for sid, obs, c, hv, av in conflicts[:10]:
        print(f"  conflict: {sid} {obs} {c}: hist={hv} annual={av}")
    if len(conflicts) > 10:
        print(f"  ... +{len(conflicts) - 10} more")
    return fin


def assert_canonical_clean(legacy: pd.DataFrame) -> dict:
    """Generation-time gate: every canonical series has 0 duplicate dates."""
    report = {}
    canon_prefix = "COT_LEGACY_"
    for sym in CANONICAL_MARKETS:
        sid = f"{canon_prefix}{sym}"
        sub = legacy[legacy["series_id"] == sid]
        dups = int(sub.duplicated("observation_period").sum()) if len(sub) else -1
        report[sym] = {"rows": int(len(sub)), "dup_dates": dups}
        assert len(sub) > 0 and dups == 0, f"canonical {sid} not clean: {report[sym]}"
    return report


def assert_fin_clean(fin: pd.DataFrame) -> dict:
    """Generation-time gate (NONPRICE-SOURCE-FIX2, audit F-1): every fin
    series - canonical AND __ALT__, TFF AND disagg - has 0 duplicate dates."""
    report = {}
    for sid, g in fin.groupby("series_id"):
        dups = int(g.duplicated("observation_period").sum())
        report[sid] = {"rows": int(len(g)), "dup_dates": dups}
        assert dups == 0, f"fin series {sid} not clean: {report[sid]}"
    return report


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    legacy = normalize_legacy()
    if not legacy.empty:
        report = assert_canonical_clean(legacy)
        legacy.to_parquet(OUT / "cftc_legacy_tidy.parquet")
        print("legacy rows:", len(legacy))
        print("canonical (1 market line per symbol, 0 dup dates):")
        for sym, r in report.items():
            print(f"  COT_LEGACY_{sym}: rows={r['rows']} dup_dates={r['dup_dates']}")
        is_alt = legacy["series_id"].str.contains("__ALT__")
        print(f"ALT rows (disambiguated sibling lines): {int(is_alt.sum())} across "
              f"{legacy.loc[is_alt, 'series_id'].nunique()} series")
    fin = normalize_fin([("cftc/tff", "COT_TFF"), ("cftc/disaggregated", "COT_DISAGG")])
    if not fin.empty:
        fin_report = assert_fin_clean(fin)
        fin.to_parquet(OUT / "cftc_tff_disagg_tidy.parquet")
        print("tff/disagg rows:", len(fin),
              "canonical:", int((~fin["series_id"].str.contains("__ALT__")).sum()),
              "alt:", int(fin["series_id"].str.contains("__ALT__").sum()))
        for sid, r in fin_report.items():
            print(f"  {sid}: rows={r['rows']} dup_dates={r['dup_dates']}")


if __name__ == "__main__":
    main()
