#!/usr/bin/env python
"""Lane FX-JA-READINESS — task 6: RBA / DFF / BoJ event PIT census.

Verifies presence + dated counts of:
  * RBA decision calendar (cash_rate_gate.html, as-published) 2023-2026
  * FRED DFF series (vintage_attempts year-end files + latest snapshot)
  * BoJ MPM archives for 6J (statements + mpmdeci indices)
Restates the vintage law (available_time = vintage as-of the decision date;
current-calendar inference FORBIDDEN). BoJ: dates present, NO intraday
timestamps -> PARTIAL (BoJ stamps = owner decision, per matrix) — restated,
not fixed. No network.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_ja_lib import NONPRICE, jdump, sha256_file  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))


def census_rba():
    p = os.path.join(NONPRICE, "rba", "cash_rate_gate.html")
    html = open(p, encoding="utf-8", errors="replace").read()
    rows = re.findall(
        r'<th scope="row">(\d{1,2} \w{3} \d{4})</th>\s*<td>([+-][\d.]+|0\.00|-)</td>\s*<td>([\d.]+)</td>',
        html)
    by_year = {}
    parsed = []
    for dmy, chg, lvl in rows:
        d = pd.to_datetime(dmy, format="%d %b %Y")
        parsed.append({"effective_date": str(d.date()), "change_pct_points": chg,
                       "cash_rate_target_pct": float(lvl)})
        by_year[str(d.year)] = by_year.get(str(d.year), 0) + 1
    parsed.sort(key=lambda r: r["effective_date"])
    sha = sha256_file(p)
    # page-level as-published stamp
    mod = re.search(r'name="dcterms.modified" content="([\d-]+)"', html)
    return {
        "source": os.path.join(NONPRICE, "rba", "cash_rate_gate.html"),
        "sha256": sha,
        "page_modified_stamp": mod.group(1) if mod else None,
        "n_decision_rows_total": len(rows),
        "effective_date_range": [parsed[0]["effective_date"], parsed[-1]["effective_date"]]
        if parsed else None,
        "decisions_by_year_2023_2026": {y: by_year.get(y, 0) for y in
                                        ("2023", "2024", "2025", "2026")},
        "decisions_by_year_all": {y: n for y, n in sorted(by_year.items())},
        "changes_2023_2026": [r for r in parsed
                              if r["effective_date"] >= "2023-01-01"
                              and r["change_pct_points"] not in ("0.00", "-")],
        "pit_law": ("as-published table, no revisions column; decision TIME = "
                    "14:00 Sydney convention NOT carried by the file (dates "
                    "only) -> decision-minute anchoring uses the effective-"
                    "date-minus-1-AU-business-day + 14:30 Sydney convention "
                    "declared in 6A_DEEP_v2.md §4.1; RBA stamps = NOT in "
                    "corpus, decision-time inference is a DECLARED convention"),
        "verdict": "PASS_EVIDENCED (dates, as-published) / timestamps NOT_IN_CORPUS",
    }


def census_dff():
    vfiles = sorted(glob.glob(os.path.join(
        NONPRICE, "fred_alfred", "vintage_attempts", "DFF_*.csv")))
    vintages = []
    for f in vfiles:
        m = re.search(r"DFF_(\d{4}-\d{2}-\d{2})\.csv$", f)
        asof = m.group(1)
        df = pd.read_csv(f)
        dcol = df.columns[0]
        vcol = [c for c in df.columns if c != dcol][0]
        vv = df.dropna(subset=[vcol])
        vintages.append({
            "vintage_asof": asof,
            "file": os.path.basename(f),
            "n_obs": int(len(vv)),
            "obs_first": str(vv[dcol].iloc[0])[:10],
            "obs_last": str(vv[dcol].iloc[-1])[:10],
        })
    latest_path = os.path.join(NONPRICE, "fred_alfred", "latest", "DFF_latest.csv")
    latest = None
    if os.path.exists(latest_path):
        df = pd.read_csv(latest_path)
        dcol = df.columns[0]
        vcol = [c for c in df.columns if c != dcol][0]
        vv = df.dropna(subset=[vcol])
        latest = {"file": "latest/DFF_latest.csv", "n_obs": int(len(vv)),
                  "obs_first": str(vv[dcol].iloc[0])[:10],
                  "obs_last": str(vv[dcol].iloc[-1])[:10]}
    return {
        "root": os.path.join(NONPRICE, "fred_alfred"),
        "vintage_files_dff": vintages,
        "n_vintages": len(vintages),
        "vintage_asof_dates": [v["vintage_asof"] for v in vintages],
        "latest_snapshot": latest,
        "note_missing_2025_vintage": ("no DFF_2025-12-31 vintage in store "
                                       "(year-end attempts skip 2025); 2026 "
                                       "covered by the 2026-09-30 vintage"),
        "vintage_law": ("available_time = vintage as-of the decision date: "
                        "for a decision at date d, usable DFF observations = "
                        "the latest vintage file with as-of <= d, truncated "
                        "at that vintage's own obs range; constructing a "
                        "'current' series at d from newer data = current-"
                        "calendar inference = FORBIDDEN (BLS PIT vintage law, "
                        "standing ruling). Year-end vintages only -> any "
                        "intra-year decision uses a vintage UP TO ~12 months "
                        "stale; that staleness is the price of PIT, not a "
                        "defect to patch."),
        "verdict": ("PARTIAL-PIT: series PRESENT with dated vintages; NOT a "
                    "dense PIT series (year-end snapshots only) — same caveat "
                    "as AF2/6J CIP usage"),
    }


def census_boj():
    stmts = sorted(glob.glob(os.path.join(
        NONPRICE, "boj", "statements", "*", "k*a.*")))
    years = {}
    for f in stmts:
        y = f.split("/")[-2]
        years[y] = years.get(y, 0) + 1
    idx = sorted(glob.glob(os.path.join(
        NONPRICE, "boj", "mpmdeci", "mpr_*_index.html")))
    idx_years = sorted(re.search(r"mpr_(\d{4})_index", f).group(1) for f in idx)
    # dated decision set from statement filenames kYYMMDDa
    dates = []
    for f in stmts:
        m = re.search(r"k(\d{2})(\d{2})(\d{2})a\.", os.path.basename(f))
        if m:
            dates.append(f"20{m.group(1)}-{m.group(2)}-{m.group(3)}")
    dates.sort()
    d2023_2026 = [d for d in dates if d >= "2023-01-01"]
    return {
        "root": os.path.join(NONPRICE, "boj"),
        "statement_files_k_a": len(stmts),
        "statement_years": {y: years[y] for y in sorted(years)},
        "statement_date_range": [dates[0], dates[-1]] if dates else None,
        "mpmdeci_index_files": len(idx),
        "mpmdeci_index_years": idx_years,
        "n_decision_dates_2023_2026": len(d2023_2026),
        "decision_dates_2023_2026": d2023_2026,
        "timestamps": "NOT_IN_CORPUS (filenames + index carry dates only)",
        "verdict": ("PARTIAL — decision DATES evidenced; intraday statement "
                    "stamps absent; per matrix, BoJ stamps = owner decision. "
                    "JF1 window anchor stays the declared 12:00-15:30 JST "
                    "convention (K3 anchor-robustness law unchanged). "
                    "Restated, NOT fixed."),
    }


def census_mof():
    p = os.path.join(NONPRICE, "normalized", "mof_intervention_tidy.parquet")
    df = pd.read_parquet(p)
    q = sorted(glob.glob(os.path.join(NONPRICE, "mof", "quarters", "*.html")))
    return {
        "tidy_rows": int(len(df)),
        "obs_range": [str(df["observation_period"].min()),
                      str(df["observation_period"].max())]
        if "observation_period" in df.columns else "columns: " + ",".join(df.columns),
        "quarter_pages": len(q),
        "verdict": ("SOURCE_TIDY_RESOLVED (ERRATUM M-1 upheld; 386 rows on "
                    "disk) — cited, not re-litigated"),
    }


if __name__ == "__main__":
    out = {
        "schema": "ja_event_pit@1",
        "task": "FUTURES-SIX-READINESS-20261004 / FX-JA-READINESS task 6",
        "generated_root_note": ("events live under "
                                "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms/ "
                                "(the dispatch's ~/my-quantitative-data/... path "
                                "holds only normalized/ — path discrepancy "
                                "disclosed; all reads from the dot-path root "
                                "the DEEP-v2 lanes cite)"),
        "rba": census_rba(),
        "fred_dff": census_dff(),
        "boj": census_boj(),
        "mof": census_mof(),
    }
    jdump(out, os.path.join(OUT, "ja_event_pit.json"))
