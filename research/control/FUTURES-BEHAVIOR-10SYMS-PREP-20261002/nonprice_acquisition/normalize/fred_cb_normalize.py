"""FRED/ALFRED + central banks + Fed/BoJ/MOF normalizer -> tidy tables.

- FRED latest CSVs -> latest (revised) vintage table with vintage_flag.
- ALFRED vintage_attempt files (if any succeeded) -> PIT snapshot rows.
- ECB SDW CSVs (ESTR daily, key rates) -> tidy.
- BoE Bank-Rate.asp -> decision table.
- BoJ: statement file inventory (dates from k{YYMMDD} names) + MPM calendar page.
- MOF intervention CSV (Shift-JIS) -> tidy operations history.
- FOMC: statement file inventory (dates from monetary{YYYYMMDD} names).
"""
from __future__ import annotations
import hashlib
import io
import re
from pathlib import Path

import pandas as pd

RAW = Path("/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms")
OUT = RAW / "normalized"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def normalize_fred_latest() -> None:
    rows = []
    for p in sorted((RAW / "fred_alfred/latest").glob("*_latest.csv")):
        sid = p.name.split("_")[0]
        df = pd.read_csv(p)
        valcol = df.columns[1] if len(df.columns) > 1 else None
        if valcol is None:
            continue
        for _, r in df.iterrows():
            v = r[valcol]
            if pd.isna(v) or v == ".":
                continue
            rows.append({
                "series_id": f"FRED_{sid}",
                "observation_period": str(r[df.columns[0]]),
                "value": float(v),
                "released_at": None,  # latest-revised file: no per-obs release stamp
                "first_available_at": None,
                "vintage_flag": "latest_revised_NOT_PIT",
                "provenance_sha256": _sha(p),
            })
    if rows:
        pd.DataFrame(rows).to_parquet(OUT / "fred_latest_tidy.parquet")
        print("fred latest rows:", len(rows))


def normalize_fred_vintage_attempts() -> None:
    rows = []
    d = RAW / "fred_alfred/vintage_attempts"
    if not d.exists():
        return
    for p in sorted(d.glob("*.csv")):
        m = re.match(r"(\w+)_(\d{4}-\d{2}-\d{2})\.csv", p.name)
        if not m:
            continue
        sid, vdate = m.groups()
        df = pd.read_csv(p)
        valcol = df.columns[1] if len(df.columns) > 1 else None
        if valcol is None:
            continue
        for _, r in df.iterrows():
            v = r[valcol]
            if pd.isna(v) or v == ".":
                continue
            rows.append({
                "series_id": f"FRED_{sid}",
                "observation_period": str(r[df.columns[0]]),
                "value": float(v),
                "released_at": vdate,      # as-of snapshot date
                "first_available_at": None,
                "vintage_flag": f"pit_snapshot_asof_{vdate}",
                "provenance_sha256": _sha(p),
            })
    if rows:
        pd.DataFrame(rows).to_parquet(OUT / "fred_vintage_attempts_tidy.parquet")
        print("fred vintage rows:", len(rows))


def normalize_ecb() -> None:
    rows = []
    for p, sid, datecol in [
        (RAW / "ecb/estr_daily_full.csv", "ECB_ESTR", "TIME_PERIOD"),
        (RAW / "ecb/key_ecb_interest_rates_mro.csv", "ECB_MRO", "TIME_PERIOD"),
    ]:
        if not p.exists():
            continue
        df = pd.read_csv(p)
        valcol = "OBS_VALUE"
        if valcol not in df.columns or datecol not in df.columns:
            continue
        for _, r in df.iterrows():
            rows.append({
                "series_id": sid,
                "observation_period": str(r[datecol]),
                "value": float(r[valcol]),
                "released_at": None,  # ECB SDW serves latest; release timing per ECB calendar
                "first_available_at": None,
                "vintage_flag": "latest_official_ecb_sdw",
                "provenance_sha256": _sha(p),
            })
    if rows:
        pd.DataFrame(rows).to_parquet(OUT / "ecb_tidy.parquet")
        print("ecb rows:", len(rows))


def normalize_boe() -> None:
    p = RAW / "boe/bank_rate_history.html"
    if not p.exists():
        return
    text = p.read_text(errors="replace")
    rows = []
    # table rows: |18 Dec 25| 3.75|
    months = ("Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec")
    for m in re.finditer(r"(\d{1,2})\s+(" + months + r")\s+(\d{2})\s*</td>.{0,120}?([\d\.]+)\s*<", text, re.S):
        d, mon, yy, rate = m.groups()
        rows.append({"series_id": "BOE_BANK_RATE",
                     "observation_period": f"20{yy}-{mon}",
                     "observation_date": f"20{yy}-{mon}-{int(d):02d}",
                     "value": float(rate),
                     "vintage_flag": "official_history_latest",
                     "provenance_sha256": _sha(p)})
    df = pd.DataFrame(rows).drop_duplicates(subset=["observation_date", "value"])
    # drop template/example rows with impossible years (e.g. 2099)
    df = df[df["observation_date"].str[:4] <= "2026"]
    df.to_parquet(OUT / "boe_bank_rate_tidy.parquet")
    print("boe bank-rate rows:", len(df),
          df["observation_date"].min() if len(df) else "",
          df["observation_date"].max() if len(df) else "")


def normalize_boj_fomc_inventory() -> None:
    """BoJ MPM statement inventory from RAW files (no downloads).

    ERRATUM 2026-10-02 (NONPRICE-FIX, audit m-1): the pre-fix inventory
    carried only the 66 HTML statements (2018+); the 114 PDF statements
    (2010-2017) were archived raw but never inventoried. Both formats are
    now included (180 files on disk; 181 URLs were enumerated - one PDF
    >4MB went wait_storage with a same-day HTML sibling, disclosed)."""
    rows = []
    stmt_dir = RAW / "boj/statements"
    if stmt_dir.exists():
        for p in sorted(set(stmt_dir.rglob("k*.htm*")) | set(stmt_dir.rglob("k*.pdf"))):
            m = re.search(r"k(\d{2})(\d{2})(\d{2})", p.name)
            if not m:
                continue
            y, mo, d = 2000 + int(m.group(1)), int(m.group(2)), int(m.group(3))
            rows.append({"series_id": "BOJ_MPM_STATEMENT",
                         "observation_period": f"{y:04d}-{mo:02d}-{d:02d}",
                         "value": 1.0,
                         "vintage_flag": "as_published_statement",
                         "format": ("pdf" if p.suffix.lower() == ".pdf" else "html"),
                         "file": p.name,
                         "provenance_sha256": _sha(p)})
    fed_dir = RAW / "fed/statements"
    if fed_dir.exists():
        for p in fed_dir.glob("monetary*.html"):
            m = re.search(r"monetary(\d{4})(\d{2})(\d{2})", p.name)
            if m:
                rows.append({"series_id": "FOMC_STATEMENT",
                             "observation_period": "-".join(m.groups()),
                             "value": 1.0,
                             "vintage_flag": "as_published_statement_14:00_ET_convention",
                             "format": "html",
                             "file": p.name,
                             "provenance_sha256": _sha(p)})
    if rows:
        pd.DataFrame(rows).sort_values(["series_id", "observation_period"]).to_parquet(
            OUT / "boj_fomc_statement_inventory.parquet")
        boj = [r for r in rows if r["series_id"] == "BOJ_MPM_STATEMENT"]
        print(f"boj+fomc statement rows: {len(rows)} "
              f"(boj={len(boj)}: pdf={sum(1 for r in boj if r['format']=='pdf')}, "
              f"html={sum(1 for r in boj if r['format']=='html')})")


def normalize_mof() -> None:
    """MOF official daily intervention history (Shift-JIS CSV) -> tidy.

    ERRATUM 2026-10-03 (lane NONPRICE-SOURCE-FIX2, task
    FUTURES-DEEPRESEARCH-V2-20261003; audit A7-DEEP-6J MAJOR-1): the pre-fix
    parser required every row to carry its own explicit Year AND MonthEN
    column. The official CSV uses merged-cell layout: the year and month are
    written only on the first row of each (year, month) block and left blank
    on subsequent daily-op rows, so 305 of the 386 official daily ops were
    silently dropped (81 kept; audit prose said "300" - a blank-month census
    gives exactly 386-81 = 305, re-verified on resume), including the
    in-window 2022-10-24
    JPY-buying op (yen 7,296 x 100m = 0.73T; Q4-2022 legs 56,202 + 7,296 =
    63,498 vs the CSV's own quarterly total row 63,499, +1 rounding unit).
    Fix: carry the month forward when blank, exactly as the year already
    was. Quarterly-total rows (期計, blank day) are still skipped. The 17
    same-date row pairs in the record are genuine multi-currency same-day
    operations (e.g. USD + EUR legs on 1999-06-21), NOT duplicates; rows
    stay keyed on (observation_period, value). Full record: 386 daily ops
    1991-05-13..2026-05-06 (369 distinct dates; NOT "1991-04" as the report
    header previously claimed - audit n-2)."""
    p = RAW / "mof/foreign_exchange_intervention_operations.csv"
    if not p.exists():
        return
    rows = []
    prov = _sha(p)
    month_en = {m: i + 1 for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}
    import csv as _csv
    with open(p, encoding="shift-jis", errors="replace", newline="") as f:
        year = None
        mon = None
        for cells in _csv.reader(f):
            cells = [c.strip() for c in cells]
            if not any(cells):
                continue
            # layout: [era_y, jp_m, jp_d, Year, MonthEN, Day, amount(1e8 JPY), pairJP, pairEN]
            if len(cells) < 7:
                continue
            # skip quarterly total rows (期計) and headers
            joined = "".join(cells)
            if "期計" in cells[0] or "Quarterly total" in joined or cells[0] in ("実施年月日", "年", ""):
                if cells[0].startswith("平成") or cells[0].startswith("令和") or cells[0].startswith("年"):
                    pass
                if "期計" in cells[0]:
                    continue
            if cells[3].isdigit():
                year = int(cells[3])
            # FIX 2026-10-03: blank MonthEN = same month as the previous row
            # (merged-cell layout); carry it forward like the year. A blank
            # month on a daily row is legitimate CSV structure, not a skip row.
            mon_new = month_en.get(cells[4][:3]) if cells[4] else None
            if mon_new:
                mon = mon_new
            try:
                day = int(cells[5])
            except ValueError:
                day = None
            if not (year and mon and day):
                continue
            try:
                amount = float(cells[6].replace(",", ""))
            except ValueError:
                continue
            pair = cells[8] if len(cells) > 8 else cells[7]
            date = f"{year:04d}-{mon:02d}-{day:02d}"
            sign = ""
            if "yen (bought)" in pair or "日本円買い" in cells[7] if len(cells) > 7 else False:
                sign = "JPY_buying"
            elif "yen (sold)" in pair:
                sign = "JPY_selling"
            rows.append({
                "series_id": "MOF_FX_INTERVENTION_DAILY",
                "observation_period": date,
                "value_yen_100m": amount,
                "direction": sign,
                "pair_desc": pair,
                "vintage_flag": "official_history_published_with_lag",
                "provenance_sha256": prov,
            })
    out = pd.DataFrame(rows).drop_duplicates(subset=["observation_period", "value_yen_100m"])
    out.to_parquet(OUT / "mof_intervention_tidy.parquet")
    print("mof intervention rows:", len(out),
          out["observation_period"].min() if len(out) else "",
          out["observation_period"].max() if len(out) else "")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    normalize_fred_latest()
    normalize_fred_vintage_attempts()
    normalize_ecb()
    normalize_boe()
    normalize_boj_fomc_inventory()
    normalize_mof()


if __name__ == "__main__":
    main()
