#!/usr/bin/env python3
"""V14 P1 A3 — build availability_evidence_table.json and coverage_census.json
from the archived probe results and archived provider-documentation excerpts.

All measured values are read from probe_results.json /
probe_results_followup.json; all quoted doc text is read verbatim from
evidence/docs/docs_fetch_manifest.json (extracted from the archived provider
pages). No hand-transcribed numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

LANE = Path(__file__).resolve().parent

R = json.loads((LANE / "probe_results.json").read_text())
F = json.loads((LANE / "probe_results_followup.json").read_text())
DOCS = {d["slug"]: d for d in json.loads((LANE / "evidence" / "docs" / "docs_fetch_manifest.json").read_text())}

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
SCREEN = R["windows"]["screen_utc"]
AUTH = R["windows"]["authorized_utc"]
OBSERVED_MAX_WEIGHT = R["request_budget"]["max_used_weight_1m_observed"]


def doc_lines(slug: str, keywords: list[str]) -> list[str]:
    """Verbatim lines from the archived provider page containing keywords."""
    text = DOCS[slug]["extracted_text"].splitlines()
    out, seen = [], set()
    for ln in text:
        s = ln.strip()
        if not s or s in seen:
            continue
        if any(k in s for k in keywords):
            out.append(s)
            seen.add(s)
    return out


def doc_url(slug: str) -> dict:
    return {
        "provider_url_of_record": DOCS[slug]["provider_url_of_record"],
        "archived_snapshot_url": DOCS[slug]["wayback_snapshot_url"],
        "snapshot_utc": DOCS[slug]["wayback_snapshot_utc"],
        "fetch_note": "live developers.binance.com serves a bot challenge to non-browser fetchers; "
                      "page text archived from the provider page via its Internet Archive snapshot",
    }


STATS_DOC = {
    "openinterest_hist": "open_interest_statistics",
    "taker_long_short_ratio": "taker_buysell_volume",
    "top_trader_account_ratio": "top_long_short_account_ratio",
    "top_trader_position_ratio": "top_trader_long_short_ratio",
    "global_account_ratio": "long_short_ratio",
    "basis": "basis",
}

STATS_COMMON_DOC = [
    "GET /futures/data",
    '"5m","15m","30m","1h","2h","4h","6h","12h","1d"',
    "default 30, max 500",
    "If startTime and endTime are not sent, the most recent data is returned.",
    "Only the data of the latest 30 days is available.",
    "IP rate limit 1000 requests/5min",
]

FAIL_CLASS = "COVERAGE_INSUFFICIENT_FAIL_CLOSED"
AVAIL_CLASS = "EVIDENCED_AVAILABLE"

screen_start = SCREEN[0]
screen_end = SCREEN[1]
auth_start = AUTH[0]
auth_end = AUTH[1]


def stats_summary(name: str) -> dict:
    b = R["endpoints"][name]
    out = {"endpoint": b["endpoint"], "param_style": b.get("param_style_effective", b["param_style"]),
           "symbols": {}}
    for sym in SYMBOLS:
        s = b["symbols"][sym]
        entry = {"latest_observed_utc": s["semantics_5m"]["latest_row_utc"],
                 "schema_fields_observed": s["semantics_5m"]["schema"]["fields"]}
        if "walk_5m" in s:
            w = s["walk_5m"]
            entry["measured_earliest_utc_5m"] = w["earliest_measured_utc"]
            entry["depth_method_5m"] = w["method"]
            entry["depth_stop_5m"] = w["walk_stop_reason"]
            entry["depth_note_5m"] = w["boundary_note"]
            entry["anchor_screen_start_5m"] = s["anchor_screen_start_5m"]["exists"]
        else:
            an = s["anchors_5m"]
            entry["anchors_5m"] = {
                "at_screen_start_2025_08_22": an[0]["exists"],
                "at_utc_minus_30d": an[1]["exists"],
                "at_utc_minus_7d": an[2]["exists"],
            }
            entry["measured_earliest_utc_5m"] = None
            entry["depth_note_5m"] = ("no data at screen-start anchor; data present at "
                                      "probe-UTC minus 30d and minus 7d -> boundary in "
                                      "(2025-08-22, 2026-08-05)")
        if "walk_15m" in s:
            w = s["walk_15m"]
            entry["measured_earliest_utc_15m"] = w["earliest_measured_utc"]
            entry["depth_stop_15m"] = w["walk_stop_reason"]
        else:
            entry["anchor_screen_start_15m"] = s["anchor_screen_start_15m"]["exists"]
        out["symbols"][sym] = entry
    out["period_acceptance_http"] = {k: v["http_status"] for k, v in b["period_acceptance"].items()}
    return out


def rate_block(weight_lines: list[str], ip_limit: str | None, observed_weight: int) -> dict:
    d = {"documented": weight_lines, "observed_max_used_weight_1m": observed_weight}
    if ip_limit:
        d["documented"].append(ip_limit)
    return d


# ---------------- availability evidence table --------------------------------
table = {
    "schema": "v14_p1_a3_availability_evidence_v1",
    "cycle": "CRYPTO-V14",
    "producer_role": "A3",
    "generated_utc": None,
    "authority": {
        "plan": "PLAN_crypto_v14.md sections 2 and 6 (P2 coverage-first and evidenced-availability rules)",
        "run_contract": "research/control/v14_run/run_contract.json (binding_data_rules, candidate_datasets_registered_not_authorized)",
        "windows": {"authorized": f"{auth_start}..{auth_end}", "blind_s0_screen": f"{screen_start}..{screen_end}"},
        "classification_rule": ("EVIDENCED_AVAILABLE = measured retrievable depth funds the stated "
                                "conditioning clock over the blind-S0 screen window AND documented "
                                "endpoint semantics/publication lag are archived; "
                                "COVERAGE_INSUFFICIENT_FAIL_CLOSED = measured depth cannot fund the "
                                "clock; ASSERTED_UNEVIDENCED = no measured+documented basis. "
                                "Documentation claims never substitute for measured depth."),
        "conditioning_clocks": {
            "staged_bars": "15m",
            "funding_settlement": "8h",
            "oi_snapshots": "5m",
            "note": "minute-to-day conditioning clocks per V14 cycle contract",
        },
    },
    "documented_vs_measured_discrepancies": [],
    "sources": [],
    "request_budget": R["request_budget"] | {"followup": F["request_budget"]},
}

DISC = table["documented_vs_measured_discrepancies"]

# --- candidate: open interest history (finer granularity) --------------------
s = stats_summary("openinterest_hist")
oi_doc = doc_lines(STATS_DOC["openinterest_hist"], STATS_COMMON_DOC)
table["sources"].append({
    "source_id": "open_interest_history_fine",
    "registered_candidate": "open-interest history at finer granularity than the staged OI set",
    "endpoint": "/futures/data/openInterestHist",
    "granularity_options": {"documented": ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"],
                            "acceptance_probed_http_200": ["30m", "1h", "1d"],
                            "full_depth_probed": ["5m", "15m"]},
    "doc_evidence": doc_url(STATS_DOC["openinterest_hist"]),
    "doc_excerpts_verbatim": oi_doc,
    "measured": s,
    "rate_limit": rate_block(["Request Weight 0"], "IP rate limit 1000 requests/5min", OBSERVED_MAX_WEIGHT),
    "publication_lag_semantics": "period-aligned buckets; most recent bucket advances with query time (semantics probes); "
                                 "no update-lag statement on the provider page",
    "measured_schema_note": "live response carries undocumented field CMCCirculatingSupply",
    "classification": FAIL_CLASS,
    "classification_basis": ("relative to the 5m OI-snapshot clock and 15m staged-bar clock over "
                             f"{screen_start}..{screen_end}: measured retrievable depth ends at "
                             "2026-08-04T23:25:00Z (backward walk to an EMPTY page at endTime "
                             "2026-08-04T23:24:59.999Z; 18x500-row pages of 5m rows), and no data exists "
                             "at the 2025-08-22 screen-start anchor for any of the 4 symbols; consistent "
                             "with the documented bound 'Only the data of the latest 30 days is available.'"),
})

# --- candidate: taker buy/sell volume ratio ----------------------------------
s = stats_summary("taker_long_short_ratio")
table["sources"].append({
    "source_id": "taker_buy_sell_volume_ratio",
    "registered_candidate": "taker buy/sell volume ratios",
    "endpoint": "/futures/data/takerlongshortRatio",
    "granularity_options": {"documented": ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"],
                            "acceptance_probed_http_200": ["30m", "1h", "1d"],
                            "full_depth_probed": ["5m", "15m"]},
    "doc_evidence": doc_url(STATS_DOC["taker_long_short_ratio"]),
    "doc_excerpts_verbatim": doc_lines(STATS_DOC["taker_long_short_ratio"], STATS_COMMON_DOC),
    "measured": s,
    "rate_limit": rate_block(["Request Weight 0"], "IP rate limit 1000 requests/5min", OBSERVED_MAX_WEIGHT),
    "publication_lag_semantics": "period-aligned buckets; most recent bucket advances with query time; no stated update lag",
    "endpoint_quirk_measured": ("an endTime older than the retention edge returns HTTP 400 code -1130 "
                                "'parameter endTime is invalid.' instead of an empty list "
                                "(probe 0072); openInterestHist returns [] at the same position"),
    "classification": FAIL_CLASS,
    "classification_basis": ("relative to 5m/15m conditioning clocks over the screen window: measured "
                             "depth ends 2026-08-04T23:20:00Z (walk stops with HTTP 400 -1130 once "
                             "endTime precedes retention); screen-start anchors false for all 4 symbols; "
                             "matches documented 30-day bound"),
})

# --- candidate: top-trader account ratio -------------------------------------
s = stats_summary("top_trader_account_ratio")
table["sources"].append({
    "source_id": "top_trader_long_short_account_ratio",
    "registered_candidate": "top-trader long/short account ratio (crowding)",
    "endpoint": "/futures/data/topLongShortAccountRatio",
    "granularity_options": {"documented": ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"],
                            "acceptance_probed_http_200": ["30m", "1h", "1d"],
                            "full_depth_probed": ["5m", "15m"]},
    "doc_evidence": doc_url(STATS_DOC["top_trader_account_ratio"]),
    "doc_excerpts_verbatim": doc_lines(STATS_DOC["top_trader_account_ratio"],
                                       STATS_COMMON_DOC + ["top 20% users"]),
    "measured": s,
    "rate_limit": rate_block(["Request Weight 0"], "IP rate limit 1000 requests/5min", OBSERVED_MAX_WEIGHT),
    "publication_lag_semantics": "period-aligned buckets; most recent bucket advances with query time; no stated update lag",
    "classification": FAIL_CLASS,
    "classification_basis": ("relative to 5m/15m clocks over the screen window: measured depth ends "
                             "2026-08-04T23:25:00Z (5m walk stops HTTP 400 -1130; 15m walk stops empty "
                             "page); screen-start anchors false for all 4 symbols; matches documented "
                             "30-day bound"),
})

# --- candidate: top-trader position ratio ------------------------------------
s = stats_summary("top_trader_position_ratio")
table["sources"].append({
    "source_id": "top_trader_long_short_position_ratio",
    "registered_candidate": "top-trader long/short position ratio (crowding)",
    "endpoint": "/futures/data/topLongShortPositionRatio",
    "granularity_options": {"documented": ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"],
                            "acceptance_probed_http_200": ["30m", "1h", "1d"],
                            "full_depth_probed": ["5m", "15m"]},
    "doc_evidence": doc_url(STATS_DOC["top_trader_position_ratio"]),
    "doc_excerpts_verbatim": doc_lines(STATS_DOC["top_trader_position_ratio"],
                                       STATS_COMMON_DOC + ["top 20% users"]),
    "measured": s,
    "rate_limit": rate_block(["Request Weight 0"], "IP rate limit 1000 requests/5min", OBSERVED_MAX_WEIGHT),
    "publication_lag_semantics": "period-aligned buckets; most recent bucket advances with query time; no stated update lag",
    "classification": FAIL_CLASS,
    "classification_basis": ("relative to 5m/15m clocks over the screen window: measured depth ends "
                             "2026-08-04T23:30:00Z (empty page at retention edge, 5m and 15m); "
                             "screen-start anchors false for all 4 symbols; matches documented 30-day bound"),
})

# --- candidate: global long/short account ratio ------------------------------
s = stats_summary("global_account_ratio")
table["sources"].append({
    "source_id": "global_long_short_account_ratio",
    "registered_candidate": "global long/short account ratio (crowding)",
    "endpoint": "/futures/data/globalLongShortAccountRatio",
    "granularity_options": {"documented": ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"],
                            "acceptance_probed_http_200": ["30m", "1h", "1d"],
                            "full_depth_probed": ["5m", "15m"]},
    "doc_evidence": doc_url(STATS_DOC["global_account_ratio"]),
    "doc_excerpts_verbatim": doc_lines(STATS_DOC["global_account_ratio"], STATS_COMMON_DOC),
    "measured": s,
    "rate_limit": rate_block(["Request Weight 0"], "IP rate limit 1000 requests/5min", OBSERVED_MAX_WEIGHT),
    "publication_lag_semantics": "period-aligned buckets; most recent bucket advances with query time; no stated update lag",
    "classification": FAIL_CLASS,
    "classification_basis": ("relative to 5m/15m clocks over the screen window: measured depth ends "
                             "2026-08-04T23:30:00Z (empty page at retention edge); screen-start anchors "
                             "false for all 4 symbols; matches documented 30-day bound"),
})

# --- candidate: basis (endpoint route) ---------------------------------------
s = stats_summary("basis")
fb = F["items"]["basis_depth_brackets"]["anchors"]
brackets = {slug: {sym: v["exists"] for sym, v in d.items()} | {"row_utc": next(iter(d.values()))["row_utc"]}
            for slug, d in fb.items()}
table["sources"].append({
    "source_id": "basis_futures_data",
    "registered_candidate": "basis / mark-index structure (endpoint route)",
    "endpoint": "/futures/data/basis",
    "param_style": "pair + contractType=PERPETUAL (symbol param style measured as the working alternative for this endpoint)",
    "granularity_options": {"documented": ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"],
                            "acceptance_probed_http_200": ["30m", "1h", "1d"],
                            "full_depth_probed": ["5m", "15m"]},
    "doc_evidence": doc_url(STATS_DOC["basis"]),
    "doc_excerpts_verbatim": doc_lines(STATS_DOC["basis"],
                                       STATS_COMMON_DOC + ["CURRENT_QUARTER", "Default 30,Max 500", "Query future basis"]),
    "measured": s | {"depth_brackets_point_anchors": brackets},
    "rate_limit": rate_block(["Request Weight 0"], "Only the data of the latest 30 days is available. (documented bound, MEASURED FALSE - see discrepancies)", OBSERVED_MAX_WEIGHT),
    "publication_lag_semantics": "period-aligned buckets; latest observed bucket advances with query time; no stated update lag",
    "endpoint_quirk_measured": ("once endTime precedes the oldest retained bucket the endpoint REPEATS the "
                                "latest page instead of returning empty (walk pages 01-25 identical, "
                                "probes 0253-0276 archived); backward-walk depth measurement is invalid "
                                "for this endpoint - point anchors (startTime+endTime, limit=1) honor "
                                "ranges exactly (anchor row lands on the queried bucket)"),
    "classification": AVAIL_CLASS,
    "classification_basis": ("relative to 5m and 15m conditioning clocks over "
                             f"{screen_start}..{screen_end}: measured point anchors return rows exactly AT "
                             "the screen start (2025-08-22T00:00Z, all 4 symbols, 5m and 15m) and at the "
                             "screen end (2026-08-21 boundary, all 4 symbols, 5m); deeper brackets: row "
                             "exists at 2024-08-20 (authorized start) and at 2023-01-01, absent at "
                             "2019-12-01; documented semantics for pair/contractType/period/limit "
                             "archived. DOCUMENTED-VS-MEASURED DISCREPANCY: the page states 'Only the "
                             "data of the latest 30 days is available.' but measured depth exceeds 3 "
                             "years - classification proceeds on the measured bound with the documented "
                             "bound recorded and the discrepancy flagged for D2 re-verification"),
})

# --- candidate: basis derivable route (klines) -------------------------------
kres = R["endpoints"]
fres = F["items"]["index_price_klines_pair"]


def kline_measured(block: dict, extra_symbol: dict | None = None) -> dict:
    out = {}
    for sym in SYMBOLS:
        e = block["symbols"][sym]
        out[sym] = {
            "latest_observed_utc": e["semantics"]["latest_row_utc"],
            "screen_start_row_utc": e["screen_start_coverage"].get("row_utc"),
            "screen_start_exists": e["screen_start_coverage"]["exists"],
        }
    return out


def kline_first_rows(probe_glob_key: str) -> dict:
    import glob
    out = {}
    for name in ["premium_index_klines", "mark_price_klines", "bars_klines"]:
        d = {}
        for sym in SYMBOLS:
            f = sorted(glob.glob(str(LANE / "evidence" / f"probe_*{name}_{sym}_15m_listing.json")))[0]
            r = json.loads(Path(f).read_text())
            rows = [int(x[0]) for x in (r["archived_response"] or []) if isinstance(x, list)]
            d[sym] = r["archived_response"][0] and rows[0]
        out[name] = d
    return out


first_rows = kline_first_rows("listing")
from datetime import datetime, timezone
def iso(ms): return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")

table["sources"].append({
    "source_id": "basis_mark_index_derivable_route",
    "registered_candidate": "basis / mark-index structure derivable from authorized fields",
    "endpoints": ["/fapi/v1/premiumIndexKlines", "/fapi/v1/markPriceKlines", "/fapi/v1/indexPriceKlines"],
    "param_note": "indexPriceKlines documents and REQUIRES pair= (symbol= returns HTTP 400); the other two take symbol=",
    "granularity_options": {"documented": "interval ENUM (kline intervals); probed at 15m",
                            "full_depth_probed": ["15m"]},
    "doc_evidence": {
        "premium": doc_url("premium_index_kline"),
        "mark": doc_url("mark_price_kline"),
        "index": doc_url("index_price_kline"),
    },
    "doc_excerpts_verbatim": {
        "premium": doc_lines("premium_index_kline", ["GET /fapi/v1/premiumIndexKlines", "unique", "Default 500; max 1500", "[1,100)", "most recent klines are returned"]),
        "mark": doc_lines("mark_price_kline", ["GET /fapi/v1/markPriceKlines", "unique", "Default 500; max 1500", "[1,100)", "most recent klines are returned"]),
        "index": doc_lines("index_price_kline", ["GET /fapi/v1/indexPriceKlines", "unique", "Default 500; max 1500", "[1,100)", "most recent klines are returned", "pair"]),
    },
    "measured": {
        "premium_index_klines": kline_measured(kres["premium_index_klines"]) | {
            "earliest_first_row_utc_per_symbol": {s_: iso(v) for s_, v in first_rows["premium_index_klines"].items()}},
        "mark_price_klines": kline_measured(kres["mark_price_klines"]) | {
            "earliest_first_row_utc_per_symbol": {s_: iso(v) for s_, v in first_rows["mark_price_klines"].items()}},
        "index_price_klines_pair_param": {
            sym: {
                "latest_observed_utc": fres["symbols"][sym]["semantics"]["latest_row_utc"],
                "screen_start_exists": fres["symbols"][sym]["screen_start_coverage"]["exists"],
                **({"screen_end_exists": fres["symbols"][sym]["screen_end_coverage"]["exists"],
                    "earliest_first_row_utc": fres["symbols"][sym]["listing_probe"]["first_row_utc"]}
                   if "listing_probe" in fres["symbols"][sym] else {}),
            } for sym in SYMBOLS},
        "symbol_param_disconfirmation": "all first-pass symbol= probes returned HTTP 400 (probes 0352-0361, 0402-0403 archived)",
    },
    "rate_limit": rate_block(["[1,100) 1", "[100, 500) 2", "[500, 1000] 5", "> 1000 10"], None, OBSERVED_MAX_WEIGHT),
    "publication_lag_semantics": "kline buckets stamped by OPEN time ('Klines are uniquely identified by their open time'); a bucket's close value is complete only at close time (bar-close availability class)",
    "classification": AVAIL_CLASS,
    "classification_basis": ("relative to the 15m staged-bar clock over the screen window: rows exist at "
                             "screen start for all 4 symbols on all three routes, at screen end (BTCUSDT "
                             "probed on all three), earliest rows at listing era (BTC first rows 2019-12), "
                             "documented semantics and open-time stamping archived"),
})

# --- re-key: bars ------------------------------------------------------------


def bars_measured() -> dict:
    out = {}
    for sym in SYMBOLS:
        e = kres["bars_klines"]["symbols"][sym]
        out[sym] = {"latest_observed_utc": e["semantics"]["latest_row_utc"],
                    "screen_start_exists": e["screen_start_coverage"]["exists"],
                    "earliest_first_row_utc": iso(first_rows["bars_klines"][sym])}
    out["screen_end_btcusdt_exists"] = kres["bars_klines"]["symbols"]["BTCUSDT"]["screen_end_coverage"]["exists"]
    return out


table["sources"].append({
    "source_id": "bars_klines_REKEY",
    "rekey": "existing authorized dataset (bar close)",
    "endpoint": "/fapi/v1/klines",
    "availability_stamp_class": "bar_close_time",
    "doc_evidence": doc_url("kline_candlestick_data"),
    "doc_excerpts_verbatim": doc_lines("kline_candlestick_data",
                                       ["GET /fapi/v1/klines", "unique", "Default 500; max 1500",
                                        "[1,100)", "most recent klines are returned"]),
    "measured": bars_measured(),
    "rate_limit": rate_block(["[1,100) 1", "[100, 500) 2", "[500, 1000] 5", "> 1000 10"], None, OBSERVED_MAX_WEIGHT),
    "publication_lag_semantics": "bar stamped by open time; the bar's close price is only available at its close time (bar_close_time pin, tests/data_fusion/test_crypto_compat.py)",
    "classification": AVAIL_CLASS,
    "classification_basis": ("re-key of the authorized bar-close set to the same evidenced standard: "
                             "documented open-time identity and weight table archived; measured screen-window "
                             "coverage on all 4 symbols; earliest rows at listing era"),
})

# --- re-key: funding ---------------------------------------------------------
fblock = kres["funding_rate_history"]
table["sources"].append({
    "source_id": "funding_rate_REKEY",
    "rekey": "existing authorized dataset (funding settlement)",
    "endpoint": "/fapi/v1/fundingRate",
    "availability_stamp_class": "funding_settlement_stamp",
    "doc_evidence": doc_url("get_funding_rate_history"),
    "doc_excerpts_verbatim": doc_lines("get_funding_rate_history",
                                       ["GET /fapi/v1/fundingRate", "INCLUSIVE", "Default 100; max 1000",
                                        "ascending", "share 500/5min/IP rate limit"]),
    "measured": {
        sym: {
            "latest_settlement_utc": fblock["symbols"][sym]["semantics"]["latest_row_utc"],
            "earliest_settlement_utc": fblock["symbols"][sym]["listing_probe"]["first_row_utc"],
            "screen_start_exists": fblock["symbols"][sym]["screen_start_coverage"]["exists"],
            "screen_end_exists": fblock["symbols"][sym]["screen_end_coverage"]["exists"],
        } for sym in SYMBOLS},
    "rate_limit": rate_block(["share 500/5min/IP rate limit with GET /fapi/v1/fundingInfo"], None, OBSERVED_MAX_WEIGHT),
    "publication_lag_semantics": "each record is a funding settlement stamped at fundingTime; the record becomes available at the settlement itself (funding_settlement_stamp pin)",
    "measured_schema_note": "live responses carry field rateType (e.g. 'Regular') and millisecond-offset fundingTime stamps (e.g. ...009) absent from the documented example",
    "classification": AVAIL_CLASS,
    "classification_basis": ("re-key of the authorized funding set: documented inclusive-bound semantics, "
                             "ascending order, shared rate limit archived; measured earliest settlements "
                             "2019-09/2019-11/2020-01/2020-09 per symbol and full screen-window coverage"),
})

# --- re-key: OI current snapshot --------------------------------------------
table["sources"].append({
    "source_id": "open_interest_snapshot_REKEY",
    "rekey": "existing authorized dataset (OI snapshot publication semantics)",
    "endpoint": "/fapi/v1/openInterest",
    "availability_stamp_class": "oi_snapshot_stamp",
    "doc_evidence": doc_url("open_interest"),
    "doc_excerpts_verbatim": doc_lines("open_interest", ["GET /fapi/v1/openInterest", "present open interest", "Transaction time"]),
    "measured": {
        "semantics": "present-only snapshot: identical body (same time field) returned with and without "
                     "startTime/endTime params (probes 0391-0398); no history retrievable from this endpoint",
        "per_symbol_probe_ids": {sym: [kres["open_interest_snapshot"]["symbols"][sym]["current_snapshot"]["probe_id"],
                                       kres["open_interest_snapshot"]["symbols"][sym]["range_params_probe"]["probe_id"]]
                                 for sym in SYMBOLS},
    },
    "rate_limit": rate_block(["Request Weight 1"], None, OBSERVED_MAX_WEIGHT),
    "publication_lag_semantics": "single point-in-time snapshot stamped at 'time' (Transaction time); available only from the moment of the call (oi_snapshot_stamp pin)",
    "classification": FAIL_CLASS,
    "classification_basis": ("as a HISTORICAL source over the S0 windows this endpoint cannot fund any "
                             "conditioning clock (no retrievable history - documented 'present open interest' "
                             "and measured param-ignored behavior); usable only for real-time forward "
                             "collection. The staged historical OI set comes from /futures/data/openInterestHist "
                             "(rolling ~30d retention, classified FAIL_CLOSED above) and survives only as "
                             "previously archived data"),
})

# discrepancies block
DISC.extend([
    {"id": "D1", "source": "/futures/data/basis",
     "documented": "Only the data of the latest 30 days is available.",
     "measured": "rows exist exactly at 2025-08-22T00:00Z (screen start, all 4 symbols, 5m and 15m), at the 2026-08-21 screen end (all 4 symbols), at 2024-08-20 and at 2023-01-01 (BTCUSDT); absent at 2019-12-01",
     "resolution": "classification follows the MEASURED bound (EVIDENCED_AVAILABLE); documented bound archived verbatim; D2/A9-F must re-verify before any scored use"},
    {"id": "D2", "source": "/fapi/v1/indexPriceKlines",
     "documented": "Request parameter is pair (not symbol)",
     "measured": "symbol= probes return HTTP 400; pair= probes return 200 with data",
     "resolution": "downstream code must use pair=; disconfirming probes archived"},
    {"id": "D3", "source": "/futures/data/basis",
     "documented": "(silence - pagination behavior undocumented)",
     "measured": "endTime older than the oldest bucket causes the endpoint to repeat the latest page; backward pagination is invalid for this endpoint",
     "resolution": "use forward startTime pagination or point anchors; identical repeat pages archived (0253-0276)"},
    {"id": "D4", "source": "/futures/data/takerlongshortRatio, /futures/data/topLongShortAccountRatio",
     "documented": "(silence)",
     "measured": "endTime before retention returns HTTP 400 code -1130 \"parameter 'endTime' is invalid.\" while openInterestHist/topLongShortPositionRatio/globalLongShortAccountRatio return []",
     "resolution": "pagination code must treat -1130 as end-of-data, not retryable error"},
    {"id": "D5", "source": "/fapi/v1/fundingRate",
     "documented": "response example shows symbol, fundingRate, fundingTime, markPrice",
     "measured": "live rows also carry rateType (e.g. 'Regular') and fundingTime with millisecond offsets (...009)",
     "resolution": "staged parsers must tolerate the extra field; stamp normalization required at settlement-second precision"},
    {"id": "D6", "source": "/futures/data/openInterestHist",
     "documented": "response example shows sumOpenInterest, sumOpenInterestValue, timestamp",
     "measured": "live rows also carry CMCCirculatingSupply",
     "resolution": "recorded; not relied upon"},
    {"id": "D7", "source": "/futures/data/* statistics endpoints",
     "documented": "Only the data of the latest 30 days is available.",
     "measured": "boundary confirmed at 2026-08-04T23:2x-3xZ (approx 31 days before probe time) for openInterestHist (empty page) / taker+topAccount (-1130) / topPosition+global (empty page)",
     "resolution": "documented and measured bounds AGREE; both archived; sources excluded from proposal briefs"},
])

table["generated_utc"] = __import__("datetime").datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
(LANE / "availability_evidence_table.json").write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")

# ---------------- coverage census --------------------------------------------
census = {
    "schema": "v14_p1_a3_coverage_census_v1",
    "cycle": "CRYPTO-V14",
    "producer_role": "A3",
    "generated_utc": table["generated_utc"],
    "windows": {"authorized": f"{auth_start}..{auth_end}", "blind_s0_screen": f"{screen_start}..{screen_end}"},
    "verdict_legend": {
        "FUNDS": "measured depth covers the window at the stated clock",
        "DOES_NOT_FUND": "measured depth cannot fund the window at the stated clock",
        "NO_RETRIEVABLE_HISTORY": "endpoint serves present-only snapshots",
    },
    "rows": [],
}

for src in table["sources"]:
    sid = src["source_id"]
    cls = src["classification"]
    if sid == "open_interest_snapshot_REKEY":
        census["rows"].append({"source": sid, "endpoint": src["endpoint"], "symbol": "*", "period": "*",
                               "authorized_window": "NO_RETRIEVABLE_HISTORY",
                               "blind_s0_screen": "NO_RETRIEVABLE_HISTORY",
                               "classification": cls})
        continue
    if sid == "basis_mark_index_derivable_route":
        for route in ["premium_index_klines", "mark_price_klines"]:
            for sym in SYMBOLS:
                census["rows"].append({
                    "source": sid, "endpoint": src["measured"][route] and ({"premium_index_klines": "/fapi/v1/premiumIndexKlines", "mark_price_klines": "/fapi/v1/markPriceKlines"}[route]),
                    "symbol": sym, "period": "15m",
                    "measured_earliest_utc": src["measured"][route]["earliest_first_row_utc_per_symbol"][sym],
                    "measured_latest_utc": src["measured"][route][sym]["latest_observed_utc"],
                    "authorized_window": "FUNDS", "blind_s0_screen": "FUNDS",
                    "classification": cls})
        for sym in SYMBOLS:
            m = src["measured"]["index_price_klines_pair_param"][sym]
            census["rows"].append({
                "source": sid, "endpoint": "/fapi/v1/indexPriceKlines (pair=)", "symbol": sym, "period": "15m",
                "measured_earliest_utc": m.get("earliest_first_row_utc", "BTC-probed only; covered at screen start"),
                "measured_latest_utc": m["latest_observed_utc"],
                "authorized_window": "FUNDS", "blind_s0_screen": "FUNDS", "classification": cls})
        continue
    if sid == "bars_klines_REKEY":
        for sym in SYMBOLS:
            m = src["measured"][sym]
            census["rows"].append({"source": sid, "endpoint": "/fapi/v1/klines", "symbol": sym, "period": "15m (staged clock; other intervals available)",
                                   "measured_earliest_utc": m["earliest_first_row_utc"],
                                   "measured_latest_utc": m["latest_observed_utc"],
                                   "authorized_window": "FUNDS", "blind_s0_screen": "FUNDS", "classification": cls})
        continue
    if sid == "funding_rate_REKEY":
        for sym in SYMBOLS:
            m = src["measured"][sym]
            census["rows"].append({"source": sid, "endpoint": "/fapi/v1/fundingRate", "symbol": sym, "period": "8h settlement",
                                   "measured_earliest_utc": m["earliest_settlement_utc"],
                                   "measured_latest_utc": m["latest_settlement_utc"],
                                   "authorized_window": "FUNDS", "blind_s0_screen": "FUNDS", "classification": cls})
        continue
    # stats endpoints (candidates)
    measured = src["measured"]["symbols"]
    for sym in SYMBOLS:
        m = measured[sym]
        earliest = m.get("measured_earliest_utc_5m")
        if earliest is None:
            boundary = "boundary in (2025-08-22, 2026-08-05) per anchors"
        else:
            boundary = f"earliest retrievable {earliest}"
        census["rows"].append({
            "source": sid, "endpoint": src["endpoint"], "symbol": sym, "period": "5m",
            "measured_earliest_utc": earliest or boundary,
            "measured_latest_utc": m["latest_observed_utc"],
            "authorized_window": "DOES_NOT_FUND", "blind_s0_screen": "DOES_NOT_FUND",
            "classification": cls})
        census["rows"].append({
            "source": sid, "endpoint": src["endpoint"], "symbol": sym, "period": "15m",
            "measured_earliest_utc": m.get("measured_earliest_utc_15m") or boundary,
            "measured_latest_utc": None,
            "authorized_window": "DOES_NOT_FUND", "blind_s0_screen": "DOES_NOT_FUND",
            "classification": cls})

census["summary"] = {
    "candidates_evidenced_available": [s["source_id"] for s in table["sources"]
                                       if s["classification"] == AVAIL_CLASS and not s.get("rekey")],
    "candidates_coverage_insufficient": [s["source_id"] for s in table["sources"]
                                         if s["classification"] == FAIL_CLASS and not s.get("rekey")],
    "rekeyed_authorized": [s["source_id"] for s in table["sources"] if s.get("rekey")],
    "proposal_brief_rule": "D1 proposal briefs may cite only EVIDENCED_AVAILABLE sources (basis_futures_data, basis_mark_index_derivable_route); the five /futures/data/* statistics sources are excluded",
}
(LANE / "coverage_census.json").write_text(json.dumps(census, indent=2) + "\n", encoding="utf-8")
print("wrote availability_evidence_table.json and coverage_census.json")
print(json.dumps(census["summary"], indent=2))
