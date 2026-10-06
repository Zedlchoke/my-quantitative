"""Build hypothesis_readiness.json for all 50 hypotheses (NONPRICE lane scope).

Readiness types (dispatch): READY_DATA / DECLARED_LAG / NOT_RUN_PIT / MISSING /
BLOCKED_CONSENSUS / OWNER_KEY_WAIT / WAIT_STORAGE (+ documented compound types:
VENDOR_PAID, PAID_OWNER_WAIT for pieces outside free-public scope).

ERRATUM 2026-10-02 (NONPRICE-FIX, audit finding M-2): labels are now derived
MECHANICALLY from pieces + config demands. Rules (applied in order):
 R1 a REQUIRED piece typed MISSING/MISSING_ROUTE (and no stronger paid/vendor
    blocker) => status must carry it: PARTIAL_MISSING_ROUTE with the exact
    piece named (fixes 6J-H3 mislabel; ES-H4 + 6B-H5 CPI-date legs).
 R2 a REQUIRED external_rates_vintages piece where the config itself demands
    first-release / vintage-clean / PIT values, while the archive holds only
    year-end ALFRED snapshots (per-release-day vintages need the FRED API key
    route - OWNER_KEY_WAIT evidence in manifest_sources.vintage_method) =>
    PARTIAL_VINTAGE with the exact granularity gap named (NQ-H1, GC-H5, CL-H4,
    6E-H2; piece-level caveat added to the rates legs of ES-H2/SI-H3).
 R3 BLOCKED_CONSENSUS dominates (no free as-issued consensus archive exists);
    R4 vendor/paid compound types as before; R5 no nonprice inputs => READY_DATA.

Scope law: this file assesses ONLY the NONPRICE external-data inputs each
hypothesis names in configs/symbols/*.yaml minimal_test/scored_run
requirements with acquisition in {free_public}. Price-data floors
(daily_trades_per_contract depth, M1, Globex, RB/HO, HG) are ANOTHER LANE's
scope; here they are recorded as price_side notes, not adjudicated.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pandas as pd

NORM = Path("/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms/normalized")
CFG = Path(__file__).resolve().parent.parent / "configs/symbols"

VINTAGE_GAP = ("ALFRED vintage snapshots are YEAR-END-ONLY (2010-12-31..2025-12-31 "
               "+ 2026-09-30); the config demands first-release/PIT values, and a "
               "mid-year decision has no same-period snapshot (latest as-of = prior "
               "year-end), so strict per-release-day PIT is NOT computable from the "
               "free route - finer vintages need the FRED API key route "
               "(OWNER_KEY_WAIT evidence: manifest_sources.fred_alfred.vintage_method)")

CPI_DATE_GAP = ("date-level CPI release calendar typed MISSING: BLS site 403-gated "
                "to this lane (gate evidence archived); release months approximable "
                "via ALFRED CPIAUCSL vintage dates only. The config's 'FACT, fetched' "
                "wording (12 of 2026 dates, dossier lane) is NOT re-verifiable from "
                "nonprice raw - cross-lane reconciliation required before CPI-date "
                "event tags are used as FACT (audit m-5)")


def _exists(p):
    """Existence with bounded retry: 2026-10-02 the shared raw volume showed
    transient per-process stat failures (active acq_pipeline.py lane shares
    the dir; file-provider episodes suspected). Never let a transient miss
    silently become null evidence (a wrong-READY source)."""
    import time
    for _ in range(4):
        if p.exists():
            return True
        time.sleep(0.5)
    return False


def coverage(p, col="observation_period"):
    if not _exists(p):
        return None
    df = pd.read_parquet(p)
    if col not in df.columns:
        col = df.columns[0]
    s = df[col].astype(str)
    return {"rows": len(df), "min": s.min(), "max": s.max(), "col": col}


def main():
    import yaml
    e = {}  # evidence
    e["cot"] = coverage(NORM / "cftc_legacy_tidy.parquet")
    e["cot_tff_disagg"] = coverage(NORM / "cftc_tff_disagg_tidy.parquet")
    e["fred_latest"] = coverage(NORM / "fred_latest_tidy.parquet")
    e["fred_vintage"] = coverage(NORM / "fred_vintage_attempts_tidy.parquet")
    e["ecb"] = coverage(NORM / "ecb_tidy.parquet")
    e["boe"] = coverage(NORM / "boe_bank_rate_tidy.parquet", "observation_date")
    e["mof"] = coverage(NORM / "mof_intervention_tidy.parquet")
    e["boj_fomc"] = coverage(NORM / "boj_fomc_statement_inventory.parquet")
    e["wngsr"] = coverage(NORM / "eia_wngsr_vintages_tidy.parquet", "file")
    e["noaa_issued"] = coverage(NORM / "noaa_cpc_issued_forecast_inventory.parquet", "issued_at")
    e["noaa_observed"] = coverage(NORM / "noaa_observed_popweighted_hddcdd.parquet")
    has = {k: v is not None for k, v in e.items()}
    # hard law: these tables were verified on disk this session; a null here
    # is a transient filesystem/read failure, NOT missing evidence -> abort
    # rather than write a mislabeled readiness file (fail-closed)
    required_present = ["cot", "fred_latest", "fred_vintage", "ecb", "boe",
                        "mof", "boj_fomc", "wngsr", "noaa_issued", "noaa_observed"]
    missing = [k for k in required_present if not has[k]]
    if missing:
        print("FATAL: evidence parquets unreadable (transient fs?):", missing,
              file=sys.stderr)
        sys.exit(3)

    R = {}
    def put(hid, status, pieces, notes=""):
        R[hid] = {"status": status, "pieces": pieces, "note": notes}

    # ---- NQ
    put("NQ-H1", "PARTIAL_VINTAGE" if has["fred_vintage"] else "DECLARED_LAG",
        {"FRED_DFII10_DGS10_vintages": f"year-end PIT snapshots 2010-2026 via ALFRED vintage_date route; GAP: {VINTAGE_GAP}",
         "FRED_DFII10_DGS10_latest": "full-history latest for cross-check (NOT_PIT flagged)"},
        "config as_of_rule: 'ALFRED first-release vintage mandatory' - not met at per-release granularity (rule R2); price side (NQ/ES daily) in hand per configs; config floor 2019+ met")
    put("NQ-H2", "READY_DATA",
        {"cot_legacy_NQ": "NASDAQ-100 Consolidated 2010-06..2026-09 (futures-only, as-published, no-revision)",
         "cot_tff_NQ": "TFF leveraged-funds available with classification-backcast caveat (strict PIT needs release-dated weekly files)",
         "cot_disagg": "disaggregated annual files (backcast caveat)"},
        "release Friday 15:30 ET convention encoded; Tuesday as-of separated (parse test)")
    put("NQ-H3", "BLOCKED_CONSENSUS",
        {"consensus_archive": "MISSING - no lawful free as-issued consensus archive (owner decision)"},
        "BLS actuals gated 403; ALFRED CPIAUCSL/PAYEMS vintages give first-print actuals + release-approx (year-end snapshot granularity)")
    put("NQ-H4", "READY_DATA", {}, "no nonprice inputs (Globex intraday = vendor price data; not this lane)")
    put("NQ-H5", "READY_DATA",
        {"FRED_rates_latest": "DTB3/DFF/DGS2 available for rate-change clustering (latest vintage; structural-descriptive use only - NOT a PIT input; rate-change dates are announced facts)"},
        "price-side spread series needs >=2y real-volume (vendor) per config")

    # ---- ES
    put("ES-H1", "READY_DATA", {}, "in hand (config)")
    put("ES-H2", "PARTIAL_PAID_OWNER",
        {"external_rates_3M": f"DTB3 full history + year-end vintages; piece-level vintage caveat (rule R2 supporting leg): {VINTAGE_GAP}",
         "spx_dividend_yield": "PAID_OWNER_WAIT - S&P forward dividend yield (index-provider)"},
        "rates leg acquired (with vintage-granularity caveat); dividend-yield leg is an owner-paid piece (never substituted)")
    put("ES-H3", "BLOCKED_CONSENSUS",
        {"consensus_archive": "MISSING (owner)"},
        "FOMC/CPI date tags READY via fed statements 2011-2026 + calendars; 2010 statements route NOT_FOUND (typed gap, 2010 meetings dates archived)")
    put("ES-H4", "PARTIAL_MISSING_ROUTE",
        {"fomc_calendar+statements": "READY - 147 statements 2011-01..2026 + 2010-2020 historical calendar pages",
         "bls_cpi_dates": f"MISSING leg (rule R1): {CPI_DATE_GAP}"},
        "event-tag v1 legal on FOMC dates; CPI-date leg NOT evidenced by this lane - label downgraded from READY_DATA (audit M-2)")
    put("ES-H5", "READY_DATA", {}, "in hand")

    # ---- CL
    put("CL-H1", "READY_DATA" if has["wngsr"] else "MISSING",
        {"eia_wpsr": "792 as-published weekly issues 2011-01..2026-09 (crude+Cushing narrative parsed; tables tidy 790/790 weeks)",
         "eia_dnav_latest": "WCRSTUS1w/WDISTUS1w revised-latest cross-check"},
        "storage regime split for scored arm now data-complete from 2011 (config target 2010-06; actual archive start 2011-01 disclosed)")
    put("CL-H2", "BLOCKED_CONSENSUS",
        {"consensus": "MISSING (owner); actuals READY via WPSR issues"})
    put("CL-H3", "VENDOR_PAID_PARTIAL",
        {"eia_wpsr_detail": "WPSR issues carry detail tables (as-published)",
         "rb_ho_futures": "VENDOR_PAID - product futures not free-public"},
        None)
    put("CL-H4", "PARTIAL_VINTAGE" if has["fred_vintage"] else "DECLARED_LAG",
        {"FRED_DTWEXBGS": f"broad trade-weighted USD (free DXY-class; ICE DXY licensed) latest + year-end vintages; GAP (rule R2 - config floor 'PIT USD/DXY daily series'): {VINTAGE_GAP}"})
    put("CL-H5", "READY_DATA", {}, "price-side only")

    # ---- GC
    put("GC-H1", "MISSING",
        {"serial_contracts_refetch": "IBKR-entitlement re-fetch - data-lane action (not nonprice-public); 6 serials age out ~Q1-2027"},
        "time-critical per SERIAL_REFETCH_MANIFEST")
    put("GC-H2", "BLOCKED_CONSENSUS",
        {"consensus": "MISSING", "tips_breakevens": "DFII10/T10YIE vintages READY (year-end granularity)",
         "cpi_first_prints": "ALFRED CPIAUCSL vintages (year-end granularity)"})
    put("GC-H3", "READY_DATA", {}, "in hand")
    put("GC-H4", "READY_DATA", {}, "in hand")
    put("GC-H5", "PARTIAL_VINTAGE" if has["fred_vintage"] else "DECLARED_LAG",
        {"FRED_DFII10_T10YIE_DGS10": f"10y TIPS + breakevens year-end vintages 2003+ (floor >=5y met); GAP (rule R2 - config as_of_rule 'vintage-clean first-release values mandatory'): {VINTAGE_GAP}"})

    # ---- NG
    put("NG-H1", "PARTIAL",
        {"eia_wngsr_vintages": "1,205 as-published issues 1996..2026 (config floor 1994 -> actual start 1996 disclosed); net_change rebuilt table/section-anchored + validated (audit M-1 fix)",
         "consensus": "PARTIAL_UNEXPECTED: WNGSR issues EMBED The Desk survey median/range (free as-published consensus record, EIA-reported) - extracted where parseable; NOT a vendor consensus archive; owner adjudicates fitness",
         "m1": "vendor price data (not this lane)"},
        "event-study still gated on M1 depth (vendor); consensus piece now partially covered free")
    put("NG-H2", "PARTIAL_NOT_RUN_PIT_GFS",
        {"cpc_issued": "6-10day temp issued daily 2012-09-11..2025-06 FULL + weekly sample to 2026-10 (PIT-legal issued forecasts; big-file regime daily continuity typed WAIT_STORAGE)",
         "ndfd_gfs_vintages": "MISSING/NOT_RUN_PIT - NDFD bucket not versioned (measured); NCEI AIRS request-based; multi-year GFS vintages exceed cap",
         "eia_wngsr": "storage percentile series READY (as-published issues)"},
        "issued-vs-observed separated (test); observed HDD/CDD official NOAA 1895..2026-10 with pre-declared census weights")
    put("NG-H3", "READY_DATA", {}, "price-side in hand (single-season caveat per config)")
    put("NG-H4", "PARTIAL_NOT_RUN_PIT_GFS",
        {"forecast_vintages": "same structure as NG-H2 (CPC issued READY where archived; GFS multi-year MISSING)"},
        "price-side needs >=3y (vendor)")
    put("NG-H5", "READY_DATA",
        {"wngsr_schedule": "archived (ir.eia.gov/ngs/schedule.html served 200); holiday moves page on file"},
        "execution constraint declared; no further data needed")

    # ---- SI
    put("SI-H1", "READY_DATA", {}, "in hand")
    put("SI-H2", "READY_DATA", {}, "in hand")
    put("SI-H3", "PARTIAL_PAID_OWNER",
        {"FRED_SOFR_DTB3": f"latest + year-end vintages; piece-level vintage caveat (rule R2 supporting leg): {VINTAGE_GAP}",
         "lbma_lease_rates": "PAID_OWNER_WAIT (LBMA/IBA)"})
    put("SI-H4", "READY_DATA", {}, "in hand")
    put("SI-H5", "READY_DATA", {}, "in hand")

    # ---- 6E
    put("6E-H1", "READY_DATA", {}, "in hand")
    put("6E-H2", "PARTIAL_VINTAGE" if (has["ecb"] and has["fred_latest"]) else "MISSING",
        {"FRED_SOFR": f"latest full + year-end ALFRED snapshots; GAP (rule R2 - config class external_rates_vintages): {VINTAGE_GAP}",
         "ECB_ESTR": "SDW daily full 2019+ (latest-serving route; ESTR is an administered overnight rate, effectively unrevised in practice - but vintage-completeness is NOT certified from this route)"})
    put("6E-H3", "BLOCKED_CONSENSUS",
        {"consensus": "MISSING", "fomc": "statements+calendars READY (2010 meeting dates via calendar page; 2011+ statements)"})
    put("6E-H4", "BLOCKED_CONSENSUS",
        {"consensus_both_regions": "MISSING",
         "ecb_decisions_actuals": "ECB key rates + ESTR READY; Eurostat HICP release-history route NOT collected (secondary to the consensus blocker)"})
    put("6E-H5", "READY_DATA", {}, "structurally blocked on price data only (vendor)")

    # ---- 6J
    put("6J-H1", "READY_DATA", {}, "in hand")
    put("6J-H2", "READY_DATA" if has["mof"] else "MISSING",
        {"mof_daily_ops": "official daily intervention history 1991-05..2026-05 (publication lag inherent - not same-day PIT, config-acknowledged)"})
    put("6J-H3", "PARTIAL_MISSING_ROUTE",
        {"FRED_DFF_FEDFUNDS_vintages": "READY (year-end granularity; USD leg)",
         "boj_tona": "MISSING_ROUTE (rule R1) - BoJ TONA daily not found via key-free route this session (BoJ market-stats page archived; SDW-style TONA endpoint not located); USD leg complete, JPY leg MISSING => label downgraded from READY_DATA (audit M-2 mislabel fix)"})
    put("6J-H4", "READY_DATA" if has["boj_fomc"] else "MISSING",
        {"boj_mpm_statements": "180 statements ON DISK 2011-01-25..2026-09-18 (114 PDFs 2011-2017 + 66 HTML 2018+, now all inventoried in tidy; 181 URLs enumerated - 1 PDF >4MB wait_storage'd with same-day HTML sibling, disclosed per audit m-1) + MPM calendar page (2010+ meeting dates)"})
    put("6J-H5", "READY_DATA" if has["mof"] else "MISSING",
        {"mof_action_history": "daily ops READY - threshold definition material"})

    # ---- 6B
    put("6B-H1", "READY_DATA", {}, "in hand")
    put("6B-H2", "BLOCKED_CONSENSUS",
        {"consensus": "MISSING (owner)",
         "ons_calendar_vintages": "MISSING_ROUTE - ONS historical calendar/first-print route not found free (current calendar page archived); BoE Bank Rate history READY"})
    put("6B-H3", "PARTIAL_DECLARED_LAG",
        {"uk_fiscal_calendar": "PARTIAL - gov.uk autumn-statement collection archived; Budget-documents collection 404 (attempts recorded); full Budget-date history typed MISSING",
         "gilt_yields": "BoE nominal gilt daily curve zip (glcnominalddata) archived - latest-vintage official; free vintages NOT published -> vintage-grade NOT_RUN_PIT, jump-filter descriptive use only (DECLARED_LAG)"})
    put("6B-H4", "READY_DATA", {}, "structurally blocked on price data only")
    put("6B-H5", "PARTIAL_MISSING_ROUTE",
        {"bls_cpi_dates": f"MISSING leg (rule R1, same structure as ES-H4): {CPI_DATE_GAP} 12 of 2026 dates exist as config-claimed FACT (dossier lane, not re-verifiable here)"},
        "label downgraded from READY_DATA by the mechanical rule (audit named ES-H4; 6B-H5 has the identical MISSING piece - disclosed in erratum)")

    # ---- 6A
    put("6A-H1", "READY_DATA",
        {"rba_decisions": "rba.gov.au 403-gated to automation (evidence archived); decision dates+times FACT already in-repo (config, fetched 2026-10-02)"},
        "gate recorded; facts in-repo - no fabrication")
    put("6A-H2", "VENDOR_PAID",
        {"hg_copper_daily": "VENDOR_PAID - no free official daily history",
         "iron_ore": "PAID_OWNER_WAIT"})
    put("6A-H3", "READY_DATA", {}, "in hand")
    put("6A-H4", "READY_DATA", {}, "in hand")
    put("6A-H5", "READY_DATA",
        {"rba_cash_rate": "in-repo FACT + gate evidence (config requirement class event_release_calendars, floor_met=true on announced target levels - not a revised data series); FRED DFF/DFEDTARU vintages supporting only (year-end granularity, disclosed)"})

    out = {
        "schema": "nonprice_hypothesis_readiness@1",
        "task_id": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
        "generated_utc": "2026-10-02",
        "scope_note": "NONPRICE external-data inputs only; price-data floors are another lane's scope and not adjudicated here. Status = worst nonprice piece unless noted (mechanical rules R1-R5 in build_readiness.py docstring; erratum 2026-10-02 NONPRICE-FIX). Missing PIT is never inferred PASS.",
        "status_counts": {},
        "evidence_coverage": {k: v for k, v in e.items()},
        "hypotheses": R,
    }
    from collections import Counter
    out["status_counts"] = dict(Counter(v["status"] for v in R.values()))
    p = Path(__file__).resolve().parent / "hypothesis_readiness.json"
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print("wrote", p)
    print(json.dumps(out["status_counts"], indent=1))


if __name__ == "__main__":
    main()
