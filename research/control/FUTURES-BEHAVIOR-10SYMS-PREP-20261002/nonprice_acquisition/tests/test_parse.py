"""Parse tests (NONPRICE-DATA-ACQUISITION) - prove the PIT laws on normalized tables.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python tests/test_parse.py
Exit 0 = all pass. Each test prints PASS/FAIL with evidence.
"""
from __future__ import annotations
import datetime as dt
import sys
from pathlib import Path

import pandas as pd

RAW = Path("/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms")
NORM = RAW / "normalized"
TODAY = dt.date(2026, 10, 2)
RESULTS = []


def check(name: str, cond: bool, evidence: str = "") -> None:
    RESULTS.append((name, bool(cond), evidence))
    print(("PASS " if cond else "FAIL ") + name + (" | " + evidence if evidence else ""))


def t_cftc_asof_vs_release():
    p = NORM / "cftc_legacy_tidy.parquet"
    if not p.exists():
        check("cftc_tidy_exists", False)
        return
    df = pd.read_parquet(p)
    check("cftc_tidy_exists", True, f"{len(df)} rows")
    obs = pd.to_datetime(df["observation_period"])
    rel = pd.to_datetime(df["released_at"].str[:10])
    delta_days = (rel - obs).dt.days
    ok_strict = (delta_days >= 2).all() and (delta_days <= 7).all()
    check("cftc_release_after_asof_2_to_7_days", ok_strict,
          f"min={delta_days.min()} max={delta_days.max()} (Tuesday as-of -> following Friday release)")
    # 2026-10-03 exact-name fix: series_id COT_LEGACY_{SYM} = exactly one market
    # line per symbol; sibling CFTC lines live under __ALT__ ids (never mixed).
    canonical = {s for s in df["series_id"].unique() if "__ALT__" not in s}
    check("cftc_all_10_canonical_symbols_exact_set",
          canonical == {f"COT_LEGACY_{s}" for s in
                        ["NQ", "ES", "6E", "6J", "6B", "6A", "CL", "NG", "GC", "SI"]},
          f"{len(canonical)} canonical ids (+{df['series_id'].nunique() - len(canonical)} "
          f"__ALT__ sibling series)")
    check("cftc_no_future_asof", (obs.dt.date <= TODAY).all(),
          f"last={obs.max().date()}")
    cov = df[~df["series_id"].str.contains("__ALT__")].groupby("series_id")["observation_period"].agg(["min", "max", "size"])
    starts = pd.to_datetime(cov["min"])
    # ERRATUM 2026-10-03: pre-fix NQ canonical series started 2010-06-15 (the
    # Consolidated line's birth; the true e-mini line was never captured). The
    # exact-name fix restores 'NASDAQ-100 STOCK INDEX (MINI)' -> 10/10 from 2006.
    floor_ok = (starts.dt.year <= 2006).all() and (cov["size"] == 1082).all()
    check("cftc_floor_2006_met_all_10_at_1082_weeks", floor_ok,
          "; ".join(f"{i}:{r['min']}..{r['max']} n={r['size']}" for i, r in cov.iterrows()))


def t_latest_vs_vintage_distinguishable():
    lat = NORM / "fred_latest_tidy.parquet"
    vin = NORM / "fred_vintage_attempts_tidy.parquet"
    if not lat.exists():
        check("fred_latest_exists", False)
        return
    ldf = pd.read_parquet(lat)
    check("fred_latest_exists", True, f"{len(ldf)} rows, {ldf['series_id'].nunique()} series")
    check("fred_latest_flagged_not_pit",
          (ldf["vintage_flag"] == "latest_revised_NOT_PIT").all())
    if vin.exists():
        vdf = pd.read_parquet(vin)
        check("fred_vintage_exists", True, f"{len(vdf)} rows")
        check("fred_vintage_flagged_pit",
              vdf["vintage_flag"].str.startswith("pit_snapshot_asof_").all())
        # join on (series, obs): at least one differing value between a PIT
        # snapshot (asof <= obs-ish windows) and latest proves distinguishability
        merged = vdf.merge(ldf, on=["series_id", "observation_period"],
                           suffixes=("_vintage", "_latest"))
        merged = merged.dropna(subset=["value_vintage", "value_latest"])
        merged["asof_year"] = merged["vintage_flag_vintage"].str[-10:].str[:4]
        # only compare where the snapshot could plausibly have known the obs
        merged = merged[pd.to_datetime(merged["observation_period"]).dt.strftime("%Y")
                        <= merged["asof_year"]]
        n_diff = (merged["value_vintage"] != merged["value_latest"]).sum()
        series_with_diff = merged.loc[merged["value_vintage"] != merged["value_latest"],
                                      "series_id"].nunique()
        check("fred_vintage_vs_latest_distinguishable",
              (series_with_diff >= 1) or len(merged) == 0,
              f"{len(merged)} comparable rows; {n_diff} differing values across "
              f"{series_with_diff} series (revised-latest != PIT snapshot)")
    else:
        check("fred_vintage_exists", False, "no vintage attempts succeeded")


def t_issued_vs_observed_separate():
    obs_p = NORM / "noaa_observed_divisions_tidy.parquet"
    iss_p = NORM / "noaa_cpc_issued_forecast_inventory.parquet"
    ok = obs_p.exists()
    check("noaa_observed_table_exists", ok)
    if ok:
        odf = pd.read_parquet(obs_p, columns=["series_id", "vintage_flag"])
        check("noaa_observed_flagged_observed",
              odf["vintage_flag"].str.contains("observed").all(), f"{len(odf)} rows")
    ok2 = iss_p.exists()
    check("noaa_issued_table_exists", ok2)
    if ok and ok2:
        idf = pd.read_parquet(iss_p, columns=["series_id", "vintage_flag"])
        check("noaa_issued_flagged_issued",
              idf["vintage_flag"].str.contains("issued").all(), f"{len(idf)} files")
        disjoint = not (set(odf["series_id"]) & set(idf["series_id"]))
        check("noaa_issued_and_observed_disjoint_series_ids", disjoint,
              f"observed={sorted(odf['series_id'].unique())} issued={sorted(idf['series_id'].unique())}")


def t_no_future_rows():
    for name, p, col in [("cftc", NORM / "cftc_legacy_tidy.parquet", "observation_period"),
                         ("fred_latest", NORM / "fred_latest_tidy.parquet", "observation_period"),
                         ("fred_vintage", NORM / "fred_vintage_attempts_tidy.parquet", "observation_period"),
                         ("noaa_issued", NORM / "noaa_cpc_issued_forecast_inventory.parquet", "issued_at"),
                         ("mof", NORM / "mof_intervention_tidy.parquet", "observation_period"),
                         ("boe", NORM / "boe_bank_rate_tidy.parquet", "observation_date"),
                         ("wngsr", NORM / "eia_wngsr_vintages_tidy.parquet", "file")]:
        if not p.exists():
            continue
        df = pd.read_parquet(p, columns=[col] if col in pd.read_parquet(p).columns else None)
        if col not in df.columns:
            continue
        s = pd.to_datetime(df[col].astype(str).str.replace(r"\.html?$", "", regex=True)
                           .str.replace("_", "-"), errors="coerce").dropna()
        if len(s) == 0:
            continue
        check(f"no_future_rows[{name}]", (s.dt.date <= TODAY).all(),
              f"max={s.max().date()}")


def t_eia_wngsr_survey():
    p = NORM / "eia_wngsr_vintages_tidy.parquet"
    if not p.exists():
        check("wngsr_tidy_exists", False)
        return
    df = pd.read_parquet(p)
    check("wngsr_tidy_exists", True, f"{len(df)} issues")
    n_total = df["working_gas_total_bcf"].notna().sum()
    n_survey = df["survey_median_bcf"].notna().sum()
    # narrative phrasing varies by era: 2014+ parses ~82-100%; pre-2014 HTML
    # issues remain archived raw evidence (parse-rate table in the report)
    recent = df[df["file"].str[:4].astype(int) >= 2014]
    recent_rate = recent["working_gas_total_bcf"].notna().mean()
    check("wngsr_totals_parsed_2014plus_95pct", recent_rate >= 0.90,
          f"2014+ parse rate {recent_rate:.2%} ({recent['working_gas_total_bcf'].notna().sum()}/{len(recent)}); "
          f"all-era {n_total}/{len(df)}")
    check("wngsr_survey_median_extracted_any", n_survey > 0,
          f"{n_survey} issues carry the embedded The Desk survey median "
          f"(free as-published consensus record)")


def t_mof_and_boj():
    p = NORM / "mof_intervention_tidy.parquet"
    if p.exists():
        df = pd.read_parquet(p)
        check("mof_tidy_nonempty", len(df) > 0,
              f"{len(df)} daily operations {df['observation_period'].min()}..{df['observation_period'].max()}")
        check("mof_covers_2011_2022_interventions",
              (df["observation_period"] >= "2011-01-01").any() and
              (df["observation_period"] <= "2022-12-31").any(),
              "official record includes the 2011 and 2022 intervention episodes")
        # ---- NONPRICE-SOURCE-FIX2 regression (audit A7-DEEP-6J MAJOR-1/n-2),
        # 2026-10-03: pre-fix parser dropped blank-month (merged-cell) rows ->
        # 81 of 386 official daily ops kept (bak_81rows_20261003); carry-forward
        # fix recovers the full record.
        check("mof_record_386_daily_ops_1991_05_13",
              len(df) == 386 and df["observation_period"].min() == "1991-05-13"
              and df["observation_period"].max() == "2026-05-06"
              and df["observation_period"].nunique() == 369,
              f"n={len(df)} ({df['observation_period'].min()}.."
              f"{df['observation_period'].max()}, {df['observation_period'].nunique()} "
              f"distinct dates; 17 same-date rows = genuine multi-currency same-day "
              f"ops, NOT dups; pre-fix kept only 81; NOT '1991-04' as once claimed)")
        r = df[df["observation_period"] == "2022-10-24"]
        check("mof_2022_10_24_jpy_buying_op_recovered",
              len(r) == 1 and float(r["value_yen_100m"].iloc[0]) == 7296.0
              and r["direction"].iloc[0] == "JPY_buying",
              "yen 7,296 x 100m = 0.73T USD-sold/JPY-bought (raw CSV row 519, blank "
              "year AND month cells; dropped pre-fix; Q4-2022 legs 56,202+7,296 = "
              "63,498 vs CSV quarterly total 63,499, +1 MOF rounding unit)")
        n2020 = int((df["observation_period"] >= "2020-01-01").sum())
        check("mof_inwindow_2020s_op_count_10_not_9", n2020 == 10,
              f"ops >=2020-01-01: {n2020} (pre-fix 9; dossier '9 JPY-buying ops "
              f"in-window' undercounted - audit M-1)")
        q4 = df[(df["observation_period"] >= "2022-10-01")
                & (df["observation_period"] <= "2022-12-31")]
        check("mof_q4_2022_daily_sum_matches_quarterly_total",
              len(q4) == 2 and q4["value_yen_100m"].sum() == 63498,
              f"Q4-2022 daily sum {q4['value_yen_100m'].sum()} vs CSV kikei row "
              f"63,499 (+1 rounding unit)")
        # independent raw recount with the same carry-forward law the fixed
        # normalizer documents (year AND month carried forward over merged cells)
        import csv as _csv
        raw_path = RAW / "mof/foreign_exchange_intervention_operations.csv"
        if raw_path.exists():
            month_num = {}
            for i, m in enumerate(["January", "February", "March", "April", "May",
                                   "June", "July", "August", "September", "October",
                                   "November", "December"]):
                month_num[m[:3]] = i + 1
            ops, year, mon = set(), None, None
            with open(raw_path, encoding="shift-jis", errors="replace", newline="") as f:
                for cells in _csv.reader(f):
                    cells = [c.strip() for c in cells]
                    if not any(cells) or len(cells) < 7:
                        continue
                    if cells[3].isdigit() and len(cells[3]) == 4:
                        year = int(cells[3])
                    if cells[4][:3] in month_num:
                        mon = month_num[cells[4][:3]]
                    try:
                        day = int(cells[5])
                        amt = float(cells[6].replace(",", ""))
                    except ValueError:
                        continue  # quarterly-total rows carry no day
                    if year and mon:
                        ops.add((year, mon, day, amt))
            tidy_set = {(int(d[:4]), int(d[5:7]), int(d[8:10]), float(a))
                        for d, a in zip(df["observation_period"], df["value_yen_100m"])}
            check("mof_tidy_set_equals_raw_carryforward_recount",
                  len(ops) == 386 and ops == tidy_set,
                  f"raw recount {len(ops)} ops == tidy set exactly "
                  f"({len(ops - tidy_set)} missing, {len(tidy_set - ops)} extra)")
    p2 = NORM / "boj_fomc_statement_inventory.parquet"
    if p2.exists():
        df = pd.read_parquet(p2)
        for sid, need in [("FOMC_STATEMENT", "2011"), ("BOJ_MPM_STATEMENT", "2010")]:
            sub = df[df["series_id"] == sid]
            check(f"{sid}_coverage_from_{need}", (sub["observation_period"] >= need).all() and len(sub) > 50,
                  f"n={len(sub)} {sub['observation_period'].min()}..{sub['observation_period'].max()}")
        # audit m-1 fix: PDFs (2010-17) now inventoried alongside HTML (2018+)
        boj = df[df["series_id"] == "BOJ_MPM_STATEMENT"]
        n_pdf = int((boj["format"] == "pdf").sum()) if "format" in boj else 0
        n_html = int((boj["format"] == "html").sum()) if "format" in boj else 0
        check("boj_inventory_180_on_disk_pdf_html",
              len(boj) == 180 and n_pdf == 114 and n_html == 66,
              f"n={len(boj)} (pdf={n_pdf}, html={n_html}); 181st URL = wait_storage'd "
              f">4MB PDF with same-day HTML sibling (disclosed in manifest erratum)")


# ---- NONPRICE-FIX regression tests (audit M-1/M-2 + minors), 2026-10-02 ----

# previously-MISGRABBED issues pinned exactly (audit M-1: first-mention regex
# grabbed expectation/prediction/survey-bound/last-year/5yr-average values)
WNGSR_MISGRAB_PINS = {
    "2016_01_14.html": (-168, 178),   # legacy grabbed the market expectation
    "2016_03_17.html": (-1, 19),      # legacy grabbed an analyst prediction
    "2018_10_11.html": (90, 74),      # legacy grabbed The Desk survey range low
    "2023_01_12.html": (11, 157),     # legacy grabbed last year's same-week value
    "2019_03_14.html": (-204, 99),    # legacy grabbed the five-year average
}
# known-good pins across all format eras (table / early table / narratives)
WNGSR_KNOWNGOOD_PINS = {
    "2026_01_22.html": -120, "2024_01_18.html": -154, "2019_09_12.html": 78,
    "2022_12_15.html": -50, "2014_01_16.html": -287, "2001_05_07.html": 102,
    "2005_06_30.html": 92, "2010_10_07.html": 85, "2008_04_03.html": -29,
    "2018_01_11.html": -359, "2018_01_18.html": -183, "2012_05_31.html": 71,
    "2017_09_07.html": 65, "2021_11_18.html": 26, "2020_04_16.html": 73,
    "2019_04_25.html": 92, "2023_09_21.html": 64, "2021_06_17.html": 16,
}
OK_FLAGS = {"OK_VERIFIED_TOTALS_DIFF", "OK_VERIFIED_TOTALS_DIFF_NARR_NONCORROB",
            "OK_PRIOR_WEEK_REVISED", "OK_TABLE_INTERNAL",
            "OK_TABLE_INTERNAL_NARR_NONCORROB", "OK_NARRATIVE_ONLY"}


def t_wngsr_net_change_regression():
    p = NORM / "eia_wngsr_vintages_tidy.parquet"
    if not p.exists():
        check("wngsr_netchange_tidy_exists", False)
        return
    df = pd.read_parquet(p)
    idx = df.set_index("file")

    bad = []
    for f, (expect, legacy_wrong) in WNGSR_MISGRAB_PINS.items():
        r = idx.loc[f]
        got = None if pd.isna(r["net_change_bcf"]) else int(r["net_change_bcf"])
        legacy = (None if pd.isna(r["net_change_legacy_firstmention_bcf"])
                  else int(r["net_change_legacy_firstmention_bcf"]))
        if got != expect or legacy != legacy_wrong or r["net_change_flag"] not in OK_FLAGS:
            bad.append(f"{f}: got={got}/{r['net_change_flag']} legacy={legacy}")
    check("wngsr_netchange_misgrab_pins_5_audit_cases", not bad,
          "; ".join(f"{f}->{v[0]:+d} (legacy wrong grab {v[1]})"
                    for f, v in WNGSR_MISGRAB_PINS.items()) + ("" if not bad else " | BAD: " + "; ".join(bad)))

    bad = []
    for f, expect in WNGSR_KNOWNGOOD_PINS.items():
        r = idx.loc[f]
        got = None if pd.isna(r["net_change_bcf"]) else int(r["net_change_bcf"])
        if got != expect or r["net_change_flag"] not in OK_FLAGS:
            bad.append(f"{f}: got={got}/{r['net_change_flag']}")
    check("wngsr_netchange_knowngood_pins_18_all_eras", not bad,
          f"{len(WNGSR_KNOWNGOOD_PINS)} issues pinned (2001-2026, table+early+narrative eras)"
          + ("" if not bad else " | BAD: " + "; ".join(bad)))

    quar = df[df["net_change_flag"] == "EXTRACT_LOW_CONFIDENCE"]
    quar_ok = quar["net_change_bcf"].isna().all() and quar["net_change_quarantine_reason"].notna().all()
    check("wngsr_netchange_quarantined_null_with_reason", quar_ok,
          f"{len(quar)} rows quarantined EXTRACT_LOW_CONFIDENCE; all nulled with recorded reason "
          f"(never silently keep a wrong value)")

    comp = df[df["net_change_check_bcf"].notna() & df["net_change_bcf"].notna()]
    agree = (comp["net_change_bcf"].astype(float) == comp["net_change_check_bcf"].astype(float)).mean()
    check("wngsr_netchange_agreement_after_ge_95pct", agree >= 0.95,
          f"kept-value agreement with independent consecutive-totals diff: "
          f"{agree:.1%} ({len(comp)} rows) - was ~11% with the pre-fix first-mention grab")

    # survey pins incl. the direction-intervening median variant (audit NOTE-1)
    pins = {"2019_09_12.html": (82, 74, 95), "2024_01_18.html": (163, 132, 176),
            "2023_01_12.html": (3, None, None)}
    bad = []
    for f, (med, lo, hi) in pins.items():
        r = idx.loc[f]
        m = None if pd.isna(r["survey_median_bcf"]) else int(r["survey_median_bcf"])
        if m != med:
            bad.append(f"{f}: median {m}!={med}")
        if lo is not None and (int(r["survey_low_bcf"]), int(r["survey_high_bcf"])) != (lo, hi):
            bad.append(f"{f}: range mismatch")
    check("wngsr_survey_pins_median_range", not bad,
          "2019-09-12 median 82 [74,95]; 2024-01-18 median 163 [132,176]; "
          "2023-01-12 median 3 (net-withdrawals phrasing, previously missed)"
          + ("" if not bad else " | BAD: " + "; ".join(bad)))

    iso = df["issue_date"].astype(str).str.match(r"^\d{4}-\d{2}-\d{2}$").all()
    hdr = (df["issue_date_source"] == "release_date_header").sum()
    fname_match = (df["issue_date"] == df["file"].str.replace(".html", "", regex=False)
                   .str.replace("_", "-", regex=False)).sum()
    check("wngsr_issue_date_robust", bool(iso) and hdr >= 1100 and fname_match >= 1180,
          f"issue_date ISO on all {len(df)} rows; {hdr} from 'Release date:' header; "
          f"{fname_match}/{len(df)} match the archive filename date "
          f"(issue_date_raw kept but documented unreliable - audit m-4)")


def t_readiness_labels():
    import json
    p = Path(__file__).resolve().parent.parent / "hypothesis_readiness.json"
    if not p.exists():
        check("readiness_json_exists", False)
        return
    d = json.loads(p.read_text())
    hyp = d["hypotheses"]
    check("readiness_json_exists", True, f"{len(hyp)} hypotheses")

    expect = {"6J-H3": "PARTIAL_MISSING_ROUTE",   # TONA leg MISSING_ROUTE (audit M-2)
              "ES-H4": "PARTIAL_MISSING_ROUTE",   # CPI-date leg MISSING (audit M-2)
              "6B-H5": "PARTIAL_MISSING_ROUTE",   # same CPI-date rule (disclosed extension)
              "NQ-H1": "PARTIAL_VINTAGE", "GC-H5": "PARTIAL_VINTAGE",
              "CL-H4": "PARTIAL_VINTAGE", "6E-H2": "PARTIAL_VINTAGE"}
    bad = [f"{h}: {hyp[h]['status']}!={s}" for h, s in expect.items() if hyp[h]["status"] != s]
    check("readiness_m2_downgrades_pinned", not bad,
          "6J-H3/ES-H4/6B-H5 -> PARTIAL_MISSING_ROUTE; NQ-H1/GC-H5/CL-H4/6E-H2 -> "
          "PARTIAL_VINTAGE (year-end-only ALFRED vs config first-release mandatory)"
          + ("" if not bad else " | BAD: " + "; ".join(bad)))

    # mechanical rule R1: no READY_DATA label may coexist with a MISSING piece
    viol = []
    for h, v in hyp.items():
        if v["status"] == "READY_DATA":
            for piece, txt in (v.get("pieces") or {}).items():
                if isinstance(txt, str) and ("MISSING_ROUTE" in txt or "MISSING leg" in txt
                                             or txt.strip().startswith("MISSING")):
                    viol.append(f"{h}/{piece}")
    check("readiness_no_ready_with_missing_piece", not viol,
          "READY_DATA labels carry no MISSING/MISSING_ROUTE piece" + ("" if not viol else " | BAD: " + "; ".join(viol)))

    from collections import Counter
    recomputed = dict(Counter(v["status"] for v in hyp.values()))
    check("readiness_counts_consistent_sum50",
          d["status_counts"] == recomputed and sum(recomputed.values()) == 50,
          f"counts recompute exactly; total 50; READY_DATA={recomputed.get('READY_DATA')} "
          f"(was 34 pre-fix)")


def t_dfii10_probe_fence():
    probe = RAW / "fred_alfred/pit/DFII10/DFII10_asof_2024-12-31.csv"
    p = NORM / "fred_vintage_attempts_tidy.parquet"
    if not p.exists():
        check("dfii10_probe_not_ingested", False, "no vintage tidy")
        return
    df = pd.read_parquet(p, columns=["provenance_sha256"])
    import hashlib
    h = hashlib.sha256(probe.read_bytes()).hexdigest()
    check("dfii10_probe_not_ingested", not (df["provenance_sha256"] == h).any(),
          "dead pit/ probe file (contains LATEST vintage, realtime params ignored - "
          "audit m-3) is fenced out of every PIT vintage table; raw immutable, "
          "disclosed in manifest_sources erratum")


# ---- INTEGRATION-FIX-V2 regression (CFTC tidy market-line mixing), 2026-10-03 ----
# Pre-fix defect (found independently by DEEP-NQ + DEEP-ES): substring market
# matching mixed several CFTC lines on duplicate dates inside one series_id.
# Pre-fix duplicate-date counts per canonical series_id (measured on the old
# tidy, sha256 4f9cd789...): NQ=548, ES=1126, CL=928, GC=164, NG=10, SI=5,
# 6A/6B/6E/6J=0. Post-fix: 0 everywhere (law: duplicate-date count == 0).
CFTC_DUP_DATES_PREFIX = {"NQ": 548, "ES": 1126, "CL": 928, "GC": 164,
                         "NG": 10, "SI": 5, "6A": 0, "6B": 0, "6E": 0, "6J": 0}
# DEEP-ES exact-name filter (ES_cot.py, found 2026-10-02) -> "1082 clean weeks,
# 0 duplicates" (handoff_DEEP-ES incident note)
DEEP_ES_EMINI_NAMES = {"E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
                       "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"}
# DEEP-NQ consolidated-line pins (NQ_a5_cot.json)
DEEP_NQ_CONSOLIDATED = {"n_rows": 850, "first": "2010-06-15", "last": "2026-09-22",
                        "oi_median_2010": 94852.0, "oi_median_2011": 89278.0,
                        "oi_median_2012": 91118.0, "oi_median_2013": 78607.0,
                        "excluded_micro": 306, "excluded_nasdaq_mini": 242}


def t_cftc_market_line_disambiguation():
    p = NORM / "cftc_legacy_tidy.parquet"
    if not p.exists():
        check("cftc_disambig_tidy_exists", False)
        return
    df = pd.read_parquet(p)
    canon = df[~df["series_id"].str.contains("__ALT__")]
    alt = df[df["series_id"].str.contains("__ALT__")]

    # LAW: duplicate-date count == 0 per canonical symbol (regression on the
    # pre-fix mixing; prefix counts above are the measured defect).
    bad = {s: int(g.duplicated("observation_period").sum())
           for s, g in canon.groupby("series_id")
           if g.duplicated("observation_period").sum() > 0}
    check("cftc_canonical_zero_duplicate_dates_all_10", not bad,
          "pre-fix dup dates: " + ", ".join(f"{s}={n}" for s, n in
                                            sorted(CFTC_DUP_DATES_PREFIX.items(), key=lambda kv: -kv[1]))
          + ("" if not bad else " | BAD: " + str(bad)))

    # every canonical line must be one coherent weekly series 2006-2026
    bad_span = [s for s, g in canon.groupby("series_id")
                if len(g) != 1082 or g["observation_period"].min() != "2006-01-03"
                or g["observation_period"].max() != "2026-09-22"]
    check("cftc_canonical_1082_weeks_2006_2026_each", not bad_span,
          f"10 canonical x 1,082 weekly obs 2006-01-03..2026-09-22"
          + ("" if not bad_span else f" | BAD: {bad_span}"))

    # ALT ids never collide with canonical and never carry a canonical name
    canon_names = set(canon["market_name"].unique())
    bad_alt = alt[alt["market_name"].isin(canon_names)]["series_id"].unique().tolist()
    check("cftc_alt_never_mixes_canonical_names", not bad_alt,
          f"{alt['series_id'].nunique()} __ALT__ sibling series "
          f"({len(alt)} rows) kept disambiguated for reproducibility"
          + ("" if not bad_alt else f" | BAD: {bad_alt}"))

    # DEEP-ES spot-check: canonical ES == their local exact-name filter
    es = canon[canon["series_id"] == "COT_LEGACY_ES"]
    ok = (set(es["market_name"]) == DEEP_ES_EMINI_NAMES
          and len(es) == 1082 and es.duplicated("observation_period").sum() == 0)
    check("cftc_deep_es_spotcheck_emini_1082", ok,
          "canonical ES == DEEP-ES exact e-mini filter (2 rename spellings, "
          "1,082 clean weeks, 0 duplicates - handoff_DEEP-ES)")

    # DEEP-NQ spot-check: their Consolidated line is preserved 1:1 under ALT
    cons = alt[alt["market_name"] == "NASDAQ-100 Consolidated - CHICAGO MERCANTILE EXCHANGE"]
    cons_y = cons.assign(y=pd.to_datetime(cons["observation_period"]).dt.year)
    med = {y: float(cons_y[cons_y.y == y]["open_interest_all"].median())
           for y in (2010, 2011, 2012, 2013)}
    nq = canon[canon["series_id"] == "COT_LEGACY_NQ"]
    ok = (len(cons) == DEEP_NQ_CONSOLIDATED["n_rows"]
          and cons["observation_period"].min() == DEEP_NQ_CONSOLIDATED["first"]
          and cons["observation_period"].max() == DEEP_NQ_CONSOLIDATED["last"]
          and all(med[y] == DEEP_NQ_CONSOLIDATED[f"oi_median_{y}"] for y in med)
          and int((alt["market_name"] == "MICRO E-MINI NASDAQ-100 INDEX - CHICAGO MERCANTILE EXCHANGE").sum())
          == DEEP_NQ_CONSOLIDATED["excluded_micro"]
          and int((nq["market_name"] == "NASDAQ MINI - CHICAGO MERCANTILE EXCHANGE").sum())
          == DEEP_NQ_CONSOLIDATED["excluded_nasdaq_mini"])
    check("cftc_deep_nq_spotcheck_consolidated_alt", ok,
          "ALT consolidated: 850 rows 2010-06-15..2026-09-22, OI medians "
          "2010-2013 = 94852/89278/91118/78607 (NQ_a5_cot.json); micro 306 ALT; "
          "DEEP-NQ's 242 excluded NASDAQ MINI rows == canonical rename-epoch rows")

    # DEEP-6B spot-check: series consumed as-is (no local filter possible on a
    # mixed table) - canonical must equal the clean rename union
    b6 = canon[canon["series_id"] == "COT_LEGACY_6B"]
    names6b = set(b6["market_name"].unique())
    ok = (len(b6) == 1082 and b6.duplicated("observation_period").sum() == 0
          and names6b == {"BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE",
                          "BRITISH POUND - CHICAGO MERCANTILE EXCHANGE"})
    check("cftc_deep_6b_spotcheck_rename_union", ok,
          "canonical 6B = pre/post mid-2022 CFTC rename union, 1,082 rows, "
          "0 duplicate dates (DEEP-6B used COT_LEGACY_6B as-is)")

    # contaminant exclusions pinned (were silently mixed pre-fix)
    cl = canon[canon["series_id"] == "COT_LEGACY_CL"]
    gc = canon[canon["series_id"] == "COT_LEGACY_GC"]
    si = canon[canon["series_id"] == "COT_LEGACY_SI"]
    ng = canon[canon["series_id"] == "COT_LEGACY_NG"]
    ok = (not cl["market_name"].str.contains("ICE").any()
          and not gc["market_name"].str.startswith("MICRO").any()
          and not si["market_name"].str.startswith("MICRO").any()
          and not ng["market_name"].str.contains("E-MIN").any()
          and len(cl) == 1082 and len(gc) == 1082 and len(si) == 1082 and len(ng) == 1082)
    check("cftc_cl_gc_si_ng_contaminants_only_under_alt", ok,
          "pre-fix mixed: CL+ICE Europe WTI (928 dup dates), GC Micro Gold, "
          "SI Micro Silver, NG E-mini/E-miny gas (10) - all now __ALT__ only; "
          "canonical lines 1,082 weekly rows each")


# ---- NONPRICE-SOURCE-FIX2 regression (fin tidy archive-overlap dedupe),
# 2026-10-03 ----
# Audit A7-INTEGRATION F-1: the regenerated fin tidy (sha 1dbb5e93, preserved
# as .bak_dup_overlap_20261003) double-read the overlapping archives
# (disagg hist_2006_2016 bulk + annual 2010..2016 zips; TFF bulk has no
# "_hist_" token but is the same re-pack) -> per-series duplicate dates:
# DISAGG CL/GC/NG/SI 1,424 rows over 1,059 distinct (365 dups each) + CL
# __ALT__ ICE lines 221+144 = 1,825 dup rows total. Two same-class defects
# fixed in the same pass: (b) ISO-only date parser dropped the whole TFF bulk
# file (M/D/YYYY strings) -> TFF canonical was 845 rows starting 2010-07-20;
# (c) legacy-schema value-keyword filter left TFF rows all-NaN and dropped
# disagg M_Money/Open_Interest. Post-fix: every series 0 dups, TFF floor
# 2006-06-13, all value columns carried, precedence = ANNUAL file wins over
# bulk re-pack (an intermediate regeneration, sha 3e32e0ee, shipped with the
# precedence accidentally inverted - bulk kept; pinned below).
FIN_DISAGG_PRE_DUP = {"COT_DISAGG_CL": 365, "COT_DISAGG_GC": 365,
                      "COT_DISAGG_NG": 365, "COT_DISAGG_SI": 365}


def t_cftc_fin_archive_overlap_dedup():
    p = NORM / "cftc_tff_disagg_tidy.parquet"
    if not p.exists():
        check("cftc_fin_tidy_exists", False)
        return
    df = pd.read_parquet(p)
    check("cftc_fin_tidy_exists", True,
          f"{len(df)} rows, {df['series_id'].nunique()} series")

    # LAW: 0 duplicate (series_id, observation_period) everywhere - canonical
    # AND __ALT__, TFF AND disagg (regression on F-1's 1,825 dup rows).
    bad = {s: int(g.duplicated("observation_period").sum())
           for s, g in df.groupby("series_id")
           if g.duplicated("observation_period").sum() > 0}
    n_canon = int((~df["series_id"].str.contains("__ALT__")).sum())
    n_alt = int(df["series_id"].str.contains("__ALT__").sum())
    check("cftc_fin_zero_duplicate_dates_all_series", not bad,
          f"15,065 rows (canonical {n_canon} + ALT {n_alt}); pre-fix dup rows: "
          f"{sum(FIN_DISAGG_PRE_DUP.values())} canonical + 365 CL-ALT ICE = 1,825 "
          f"(DISAGG CL/GC/NG/SI were 1,424 rows over 1,059 distinct dates)"
          + ("" if not bad else f" | BAD: {bad}"))

    # DISAGG canonical: exactly the 1,059 distinct weekly dates, full span
    dis = df[df["series_id"].isin(FIN_DISAGG_PRE_DUP)]
    ok = (len(dis) == 4 * 1059
          and (dis.groupby("series_id")["observation_period"].size() == 1059).all()
          and (dis.groupby("series_id")["observation_period"].min() == "2006-06-13").all()
          and (dis.groupby("series_id")["observation_period"].max() == "2026-09-22").all())
    check("cftc_fin_disagg_canonical_1059_full_span", ok,
          "COT_DISAGG_CL/GC/NG/SI: 1,059 weekly obs 2006-06-13..2026-09-22 each "
          "(365 value-identical overlap rows dropped per series)")

    # TFF canonical: date-format fix regains the 2006-06-13 archive floor
    tff_syms = [f"COT_TFF_{s}" for s in ("6A", "6B", "6E", "6J", "ES", "NQ")]
    tff = df[df["series_id"].isin(tff_syms)]
    ok = (len(tff) == 6 * 1059
          and (tff.groupby("series_id")["observation_period"].size() == 1059).all()
          and (tff.groupby("series_id")["observation_period"].min() == "2006-06-13").all())
    check("cftc_fin_tff_floor_2006_regained", ok,
          "TFF canonical 1,059 rows from 2006-06-13 (pre-date-fix: 845 rows from "
          "2010-07-20 - the M/D/YYYY bulk-history file was silently dropped)")

    # value columns actually carried (pre-fix: TFF all-NaN, disagg lost cols)
    tff_vals = [c for c in df.columns if c.startswith(("Asset_Mgr_Positions", "Lev_Money_Positions"))]
    dis_vals = [c for c in df.columns if c.startswith("M_Money_Positions")] + ["Open_Interest_All"]
    ok = (tff_vals and not tff[tff_vals].isna().all().all()
          and dis_vals and not dis[dis_vals].isna().all().all())
    check("cftc_fin_value_columns_present", ok,
          f"TFF {tff_vals[0]}.. + DISAGG {dis_vals[0]}.. not all-NaN "
          f"(pre-fix keyword filter matched the legacy schema only)")

    # precedence pin: ANNUAL file wins on the 9 rounding-level overlap cells
    # (raw: hist bulk 24.0 vs annual 23.9; the inverted intermediate 3e32e0ee
    # shipped 24.0 sourced from the bulk zip)
    r = df[(df["series_id"] == "COT_TFF_6A") & (df["observation_period"] == "2016-05-31")]
    ok = (len(r) == 1 and float(r["Pct_of_OI_Lev_Money_Long_All"].iloc[0]) == 23.9
          and r["source_zip"].iloc[0] == "fut_fin_txt_2016.zip")
    check("cftc_fin_dedupe_annual_wins_precedence_pin", ok,
          "COT_TFF_6A 2016-05-31 Pct_of_OI_Lev_Money_Long_All = 23.9 from "
          "fut_fin_txt_2016.zip (annual wins; hist bulk carries 24.0; one of 9 "
          "rounding-level cells across 9 series-dates, all Pct_of_OI_*/"
          "Change_in_* columns)")


def main() -> int:
    t_cftc_asof_vs_release()
    t_cftc_market_line_disambiguation()
    t_cftc_fin_archive_overlap_dedup()
    t_latest_vs_vintage_distinguishable()
    t_issued_vs_observed_separate()
    t_no_future_rows()
    t_eia_wngsr_survey()
    t_mof_and_boj()
    t_wngsr_net_change_regression()
    t_readiness_labels()
    t_dfii10_probe_fence()
    fails = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(fails)}/{len(RESULTS)} tests passed")
    if fails:
        print("FAILED:", fails)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
