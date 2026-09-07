"""V6-P0b (A3): light-phase assembly entry point.

Runs the probe runner over the archived window documents, merges the
channel-integrity findings, and writes the five committed control
artifacts. Evidence-first: every number in the outputs traces to archived
bytes under .staging_prices_v6/ (gitignored, sha256-manifested).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from datetime import date

from research.assets.stocks.p0b_control_writer import (
    RAW_DIR,
    TERMS_DIR,
    build_license_evidence,
    build_price_authority,
    build_bulk_download_plan,
    now_utc,
    sha256_file,
    write_all,
)
from research.assets.stocks.p0b_fetch import write_dir_manifest
from research.assets.stocks.p0b_l7_crosscheck import (
    DividendFact,
    SplitFact,
)
from research.assets.stocks.p0b_probe import run_probes

SPLIT_FACTS = {
    # pinned PIT store facts (sha256 f53eb371...df955):
    # us-gaap:StockholdersEquityNoteStockSplitConversionRatio1
    "CMG": [
        SplitFact(
            window_start=date(2024, 6, 16),
            window_end=date(2024, 7, 6),
            ratio=50.0,
            source_field="us-gaap:StockholdersEquityNoteStockSplitConversionRatio1",
            fact_available_time="2024-07-25 (first of 5 vintages, all ratio=50, event 2024-06-26)",
        )
    ],
    "TJX": [
        SplitFact(
            window_start=date(2018, 10, 22),
            window_end=date(2018, 11, 6),
            ratio=2.0,
            source_field="us-gaap:StockholdersEquityNoteStockSplitConversionRatio1 (+ StockIssuedDuringPeriodSharesStockSplits=617000000)",
            fact_available_time="2018-12-04 (7 vintages, all ratio=2)",
        )
    ],
}

DIVIDEND_FACTS = {
    "AIG": [
        # us-gaap:CommonStockDividendsPerShareCashPaid, USD/shares
        DividendFact(date(2022, 3, 31), 0.32, "us-gaap:CommonStockDividendsPerShareCashPaid", "2022-05-05"),
        DividendFact(date(2022, 6, 30), 0.32, "us-gaap:CommonStockDividendsPerShareCashPaid", "2022-08-09"),
        DividendFact(date(2022, 9, 30), 0.32, "us-gaap:CommonStockDividendsPerShareCashPaid", "2022-11-02"),
    ],
    "TJX": [],
    "CMG": [],
}

WINDOWS = [
    {
        "symbol": "CMG",
        "window_id": "split_window",
        "d1": date(2024, 6, 1),
        "d2": date(2024, 7, 15),
        "file": "cmg_20240601_20240715.csv",
        "retrieval": {
            "channel": "browser-equivalent rendering (web reader), summarizer-mediated",
            "fidelity": "UNVERIFIABLE — numbers transcribed from the rendered document; content NOT hash-pinnable to server bytes",
            "requested_url": "https://stooq.com/q/d/l/?s=cmg.us&i=d&d1=20240601&d2=20240715",
        },
    },
    {
        "symbol": "TJX",
        "window_id": "pre_split_scan",
        "d1": date(2018, 9, 4),
        "d2": date(2018, 10, 12),
        "file": "tjx_20180904_20181012.csv",
        "retrieval": {
            "channel": "browser-equivalent rendering (web reader), summarizer-mediated",
            "fidelity": "UNVERIFIABLE — see channel_integrity",
            "requested_url": "https://stooq.com/q/d/l/?s=tjx.us&i=d&d1=20180904&d2=20181012",
        },
    },
    {
        "symbol": "TJX",
        "window_id": "split_window_scan",
        "d1": date(2018, 10, 15),
        "d2": date(2018, 11, 15),
        "file": "tjx_20181015_20181115.csv",
        "retrieval": {
            "channel": "browser-equivalent rendering (web reader), summarizer-mediated",
            "fidelity": "UNVERIFIABLE — see channel_integrity",
            "requested_url": "https://stooq.com/q/d/l/?s=tjx.us&i=d&d1=20181015&d2=20181115",
        },
    },
    {
        "symbol": "TJX",
        "window_id": "post_split_scan",
        "d1": date(2018, 11, 16),
        "d2": date(2018, 12, 28),
        "file": "tjx_20181116_20181228.csv",
        "retrieval": {
            "channel": "browser-equivalent rendering (web reader), summarizer-mediated",
            "fidelity": "UNVERIFIABLE — see channel_integrity",
            "requested_url": "https://stooq.com/q/d/l/?s=tjx.us&i=d&d1=20181116&d2=20181228",
        },
    },
]

CHANNEL_INTEGRITY = {
    "verdict": "CHANNEL_UNFAITHFUL_FAIL_CLOSED",
    "plain_http_channel": (
        "stooq.com and stooq.pl serve a JavaScript proof-of-work "
        "browser-verification challenge to plain-HTTP clients on all endpoints "
        "including the /q/d/l/ CSV endpoint; challenge bytes archived and "
        "sha256-pinned in p0b_license_evidence.json; challenge NOT solved, no "
        "gate bypassed"
    ),
    "rendering_channel": (
        "the only channel that passes the gate delivers page content to the "
        "agent through a summarization layer; retrieved numbers cannot be "
        "pinned as server bytes"
    ),
    "tjx_falsification_detail": (
        "TJX renders (Sep-Dec 2018) show no split signature anywhere (SEC fact: "
        "2:1 in the 2018-10-22..2018-11-06 quarter), no October 2018 market "
        "selloff, a December 2018 price level ~2x the documented post-split "
        "level, and mechanically regular volumes (all round hundreds, narrow "
        "band); in addition ALL THREE TJX renders fail the OHLC interval "
        "consistency check (close > high by ~0.10 on multiple rows) while the "
        "CMG render passes every bar-consistency check — either the rendering "
        "paraphrases/fabricates or the source series is corrupt; neither is "
        "admissible as hash-pinned research data"
    ),
    "cmg_corroboration_detail": (
        "the CMG render is the single internally consistent window: the -97.95% "
        "close-to-close impact lands exactly on the SEC-evidenced 2024-06-26 "
        "50:1 split date (expected -98.0%, residual 2.6% = split-day market "
        "move), and volume steps 451,554 -> 17,536,154 (~39x, consistent with a "
        "50x share-multiplication) — corroborated, but fidelity remains "
        "unverifiable through the summarizing channel"
    ),
}

L7_OVERRIDES = {
    "CMG": {
        "l7_verdict": "SEC_CORROBORATED_FIDELITY_UNVERIFIABLE",
        "measured_close_to_close_impact": -0.97946403721522,
        "sec_expected_impact": -0.98,
        "implied_ratio_close_to_close": 48.695062923523714,
        "sec_ratio": 50.0,
        "tolerance_statement": "|implied/sec - 1| <= 5% (split-day market move allowance) -> PASS",
        "volume_step_evidence": {"pre_split_close_volume": 451554, "split_day_volume": 17536154, "step": 38.85},
    },
    "TJX": {
        "l7_verdict": "CHANNEL_UNFAITHFUL_FAIL_CLOSED",
        "mechanical_continuity_verdict": "NOT_RUN — all three TJX renders fail the parse contract's OHLC interval consistency check (close > high), which is itself evidence of render unfaithfulness",
        "override_reason": (
            "the rendered series is additionally irreconcilable with documented "
            "market history (no October 2018 selloff, December 2018 level wrong "
            "by ~2x, no split signature, no volume step), so no adjustment "
            "convention may be inferred from it and the windows are recorded "
            "as failures"
        ),
    },
    "AIG": {"l7_verdict": "NOT_RUN", "reason": "dividend windows not fetched after the TJX fidelity failure (resource + evidence discipline)"},
    "AAL": {"l7_verdict": "NOT_RUN", "reason": "not fetched; fidelity failure terminated the probe sequence"},
    "AGNCZ": {"l7_verdict": "NOT_RUN", "reason": "not fetched; fidelity failure terminated the probe sequence"},
    "RTX": {"l7_verdict_note": "identity probe not fetched", "l7_verdict": "NOT_RUN", "reason": "not fetched; fidelity failure terminated the probe sequence; RTX also has no split/dividend fields in the pinned store"},
}

AVAILABILITY = {
    "schema": "stocks_free_v6_run/p0b_availability_evidence@1",
    "generated_at_utc": now_utc(),
    "discipline": (
        "handbook section 11: retrieved_time never substitutes for historical "
        "availability; asserted bounds are never authorized (forex-V3 "
        "downgrade); for market data the availability question is whether the "
        "historical series is served today consistently and whether revision/"
        "backfill behavior exists"
    ),
    "stooq_table_status": "FAIL_CLOSED_SCRIPTED_ACCESS_UNAVAILABLE (evidence-conflicted channel; see claims)",
    "stooq_claims": [
        {
            "claim": "documented CSV endpoint /q/d/l/?s=<symbol>.us&i=d serves daily OHLCV CSV with d1/d2=YYYYMMDD window parameters",
            "status": "EVIDENCED",
            "evidence": "4 windowed retrievals conformed to the parse contract (header, ISO dates, ascending, d1/d2 honored); rendered documents archived under .staging_prices_v6/raw/",
            "caveat": "channel fidelity unverifiable (summarizer-mediated)",
        },
        {
            "claim": "endpoint is keyless (no account, no API key) for browser access",
            "status": "EVIDENCED",
            "evidence": "CSV content was retrievable through the browser-equivalent channel with zero credentials; plain-HTTP requests hit the anti-bot challenge BEFORE any authentication wall (no signup was ever required or performed)",
            "caveat": "scripted access remains blocked by the challenge — separate claim below",
        },
        {
            "claim": "endpoint usable for scripted, hash-pinnable retrieval in this environment",
            "status": "REFUTED_IN_THIS_ENVIRONMENT",
            "evidence": "plain HTTP: JS proof-of-work challenge on all endpoints, both domains (archived bytes); renderer channel: summarizer-mediated, fidelity failure demonstrated on TJX",
        },
        {
            "claim": "served series adjustment convention (split-adjusted vs raw; dividend-adjusted)",
            "status": "UNEVIDENCED_CONFLICTED",
            "evidence": "CMG render behaves split-RAW with the SEC-corroborated 50:1 signature; TJX renders behave neither coherently adjusted nor raw (irreconcilable with SEC fact and market history); dividend adjustment is not determinable from any single series without a raw/adjusted pair",
            "consequence": "any future authorization MUST pin the adjustment convention from certified bytes BEFORE any return is computed; the corporate_actions engine path assumes RAW + issuer facts until then",
        },
        {
            "claim": "US single-name history depth across the S0 window (2018-04-04..2025-07-24)",
            "status": "UNEVIDENCED",
            "evidence": "no certifiable full-window retrieval exists; the 1990-depth window probe was abandoned after the fidelity failure",
        },
        {
            "claim": "delisted-name history coverage",
            "status": "UNEVIDENCED",
            "evidence": "the 410-filer panel contains no currently-dead CIK (all 410 map in today's SEC ticker file — archived mapping), so no in-panel delisted probe was possible; no out-of-panel delisted probe was run",
        },
        {
            "claim": "revision/vintage behavior of the served series",
            "status": "UNEVIDENCED",
            "evidence": "no repeat-download byte-diff was performed (deferred to the census plan)",
        },
        {
            "claim": "terms: acceptance-by-use (browse-wrap); commercial use requires author consent",
            "status": "ASSERTED",
            "evidence": "rendered quotes from https://stooq.com/regulamin/ (~4000/5726 chars) recorded in p0b_license_evidence.json",
            "caveat": "character-exact fidelity not guaranteed; full text review required before any bulk authorization",
        },
    ],
    "massive_table_status": "CANDIDATE_NOT_AUTHORIZED (no data scope reachable)",
    "massive_claims": [
        {
            "claim": "Basic tier: $0/month, 2-year historical depth, 5 API calls/min, EOD data",
            "status": "ASSERTED",
            "evidence": "massive.com/pricing static HTML (raw bytes sha256-pinned in p0b_license_evidence.json)",
            "caveat": "never executed — every data path requires signup",
        },
        {
            "claim": "API access requires account signup + API key + terms acceptance",
            "status": "EVIDENCED",
            "evidence": "verbatim Individuals Terms quotes (account registration mandatory; acceptance at sign-up) from pinned raw bytes",
        },
        {
            "claim": "Basic/Individual tier license is personal, non-business, non-commercial use only",
            "status": "EVIDENCED",
            "evidence": "verbatim Individuals Terms preamble quote; business/commercial use requires the Business terms (paid)",
        },
        {
            "claim": "data availability for this research",
            "status": "NOT_RUN",
            "evidence": "no authorized scope: agents may not sign up or accept terms (PLAN_stocks_v6 section 15; handbook section 11.4)",
        },
    ],
}


def main() -> None:
    probe_report = run_probes(WINDOWS, RAW_DIR, SPLIT_FACTS, DIVIDEND_FACTS)
    probe_report["channel_integrity"] = CHANNEL_INTEGRITY
    probe_report["l7_overrides"] = L7_OVERRIDES
    probe_report["symbols_budget_note"] = (
        "light-phase symbol budget: 2 symbols of data windows retrieved (CMG, "
        "TJX) within the max-6 budget; 4 additional window requests were spent "
        "on TJX to chase the split signature before the fidelity failure was "
        "declared; AIG/AAL/AGNCZ/RTX windows NOT fetched"
    )

    write_all(AVAILABILITY, probes_ok=False, probe_report=probe_report)
    # pin the staged raw bytes (raw windows + terms documents) via manifests
    for d in (RAW_DIR, TERMS_DIR, Path(".staging_prices_v6/summaries")):
        m = write_dir_manifest(d)
        print("manifest:", m)
    # license evidence + bulk plan are produced inside write_all; availability
    # table gets its own file here
    control = Path("research/control/stocks_free_v6_run")
    (control / "p0b_availability_evidence.json").write_text(
        json.dumps(AVAILABILITY, indent=1), encoding="utf-8"
    )
    print("wrote:")
    for p in sorted(control.glob("p0b_*.json")):
        print("  ", p)
    print("windows OK:", len(probe_report["windows"]), "failures:", len(probe_report["failures"]))
    for w in probe_report["windows"]:
        print("   ", w["symbol"], w["window_id"], w["rows"], "rows", w["status"])


if __name__ == "__main__":
    main()
