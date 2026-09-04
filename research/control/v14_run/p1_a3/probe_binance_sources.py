#!/usr/bin/env python3
"""V14 P1 A3 candidate-source availability probes — live Binance USD-M futures REST.

Lane: orca/v14-p1-a3-data (CRYPTO-V14, P2 coverage-first rule, PLAN_crypto_v14.md
sections 2 and 6). This script MEASURES retrievable history depth; it does not
mass-download histories. It is a light, bounded probe:

- small symbol set: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT;
- small page limits (archive probes use limit 1..5; backward-walk pages use the
  documented per-endpoint maximum so the walk reaches the boundary in few calls);
- sleep >= 0.55 s between requests, adaptive back-off on observed
  X-MBX-USED-WEIGHT-1M;
- hard request-budget cap (HARD_CAP requests; target < 400).

Every HTTP request is archived as one JSON evidence file under
``evidence/`` with: full request URL/params, HTTP status, retrieval UTC
timestamp, response headers of record, full raw body (small probes) or a
declared first-N-row truncation plus the SHA-256 of the full raw body
(walk pages), row count and first/last row timestamps.

Depth-measurement method (recorded per result):
- ``backward_walk``: paginate backwards with endTime/limit (limit = documented
  max) until the API returns an empty page, or until the walk reaches the
  authorized-window floor, or the page cap is hit;
- ``anchor``/``binary_search``: point-existence probes
  ``startTime=t, endTime=t+span, limit=1`` used to bracket/pin the earliest
  retrievable timestamp when a full walk would be disproportionate;
- every earliest-boundary claim is confirmed by an empty probe just before it.

stdlib only; no third-party dependencies; no credentials.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FAPI_BASE = "https://fapi.binance.com"
LANE_DIR = Path(__file__).resolve().parent
EVIDENCE_DIR = LANE_DIR / "evidence"

# --- S0 windows (from research/control/v14_run/first_report_v14.json) -------
AUTH_START_MS = int(datetime(2024, 8, 20, tzinfo=timezone.utc).timestamp() * 1000)
AUTH_END_MS = int(datetime(2026, 8, 22, tzinfo=timezone.utc).timestamp() * 1000) - 1
SCREEN_START_MS = int(datetime(2025, 8, 22, tzinfo=timezone.utc).timestamp() * 1000)
SCREEN_END_MS = int(datetime(2026, 8, 21, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
PERIOD_MS = {
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 60 * 60_000,
    "2h": 2 * 60 * 60_000,
    "4h": 4 * 60 * 60_000,
    "6h": 6 * 60 * 60_000,
    "12h": 12 * 60 * 60_000,
    "1d": 24 * 60 * 60_000,
}

# Candidate sources (registered, not yet authorized) — /futures/data/* family.
STATS_ENDPOINTS = [
    ("openinterest_hist", "/futures/data/openInterestHist", "symbol"),
    ("taker_long_short_ratio", "/futures/data/takerlongshortRatio", "symbol"),
    ("top_trader_account_ratio", "/futures/data/topLongShortAccountRatio", "symbol"),
    ("top_trader_position_ratio", "/futures/data/topLongShortPositionRatio", "symbol"),
    ("global_account_ratio", "/futures/data/globalLongShortAccountRatio", "symbol"),
    ("basis", "/futures/data/basis", "pair"),  # pair + contractType param style
]

# Derivable authorized-field route for basis/mark-index structure.
KLINE_ROUTES = [
    ("premium_index_klines", "/fapi/v1/premiumIndexKlines"),
    ("mark_price_klines", "/fapi/v1/markPriceKlines"),
    ("index_price_klines", "/fapi/v1/indexPriceKlines"),
    ("bars_klines", "/fapi/v1/klines"),  # re-key of existing authorized dataset
]

# Existing authorized datasets re-keyed to the same evidenced standard.
FUNDING_ENDPOINT = ("funding_rate_history", "/fapi/v1/fundingRate")
OI_SNAPSHOT_ENDPOINT = ("open_interest_snapshot", "/fapi/v1/openInterest")

HARD_CAP = 420
SLEEP_S = 0.55
WALK_PAGE_LIMIT_STATS = 500   # documented max for /futures/data/*
WALK_PAGE_LIMIT_KLINES = 1500  # documented max for /fapi/v1/* klines
WALK_PAGE_CAP = 25
LISTING_PROBE_MS = int(datetime(2019, 9, 1, tzinfo=timezone.utc).timestamp() * 1000)


def utc_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ProbeRunner:
    def __init__(self) -> None:
        self.count = 0
        self.used_weight_observed = 0
        self.records: list[dict] = []
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    def _archive(
        self,
        slug: str,
        endpoint: str,
        params: dict,
        url: str,
        status: int,
        headers: dict,
        raw: bytes,
        parsed,
        error: str | None,
        row_count: int | None,
        first_ts_key: str | None,
        last_ts_key: str | None,
        archive_rows: int | None,
    ) -> dict:
        self.count += 1
        first_ts = last_ts = None
        if row_count:
            first_ts = _row_ts(parsed[0], first_ts_key)
            last_ts = _row_ts(parsed[-1], last_ts_key)
        archived = parsed
        truncation = None
        if archive_rows is not None and isinstance(parsed, list) and len(parsed) > archive_rows:
            archived = parsed[:archive_rows]
            truncation = {
                "kept": archive_rows,
                "total": len(parsed),
                "note": "archived_response truncated; sha256_raw_body covers the FULL raw body",
            }
        rec = {
            "probe_id": f"{self.count:04d}",
            "retrieval_utc": now_utc_iso(),
            "endpoint": endpoint,
            "request_url": url,
            "request_params": {k: str(v) for k, v in params.items()},
            "http_status": status,
            "response_headers_of_record": headers,
            "row_count": row_count,
            "first_row_ms": first_ts,
            "first_row_utc": utc_iso(first_ts) if first_ts else None,
            "last_row_ms": last_ts,
            "last_row_utc": utc_iso(last_ts) if last_ts else None,
            "raw_body_bytes": len(raw),
            "raw_body_sha256": hashlib.sha256(raw).hexdigest(),
            "error": error,
            "archived_response": archived,
            "row_truncation": truncation,
        }
        path = EVIDENCE_DIR / f"probe_{rec['probe_id']}_{slug}.json"
        path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        self.records.append({"probe_id": rec["probe_id"], "file": path.name, "endpoint": endpoint,
                             "status": status, "rows": row_count})
        return rec

    def get(self, slug: str, endpoint: str, params: dict, *, archive_rows: int | None = None,
            first_ts_key: str | None = "timestamp", last_ts_key: str | None = "timestamp") -> dict:
        assert self.count < HARD_CAP, f"hard request budget cap {HARD_CAP} reached"
        url = f"{FAPI_BASE}{endpoint}?{urllib.parse.urlencode(params)}"
        last_err = None
        for attempt in range(3):
            if self.count and self.used_weight_observed > 1800:
                time.sleep(25.0)
            elif self.count and self.used_weight_observed > 1200:
                time.sleep(10.0)
            if self.count:
                time.sleep(SLEEP_S)
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "v14-p1-a3-availability-probe/1.0"})
                with urllib.request.urlopen(req, timeout=30.0) as resp:
                    status = resp.status
                    raw = resp.read()
                    headers = {
                        k.lower(): v
                        for k, v in resp.headers.items()
                        if k.lower() in {
                            "x-mbx-used-weight-1m", "x-mbx-order-count-1m",
                            "content-type", "date",
                        }
                    }
                    w = headers.get("x-mbx-used-weight-1m")
                    if w:
                        self.used_weight_observed = max(self.used_weight_observed, int(w))
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read()
                headers = {"x-mbx-used-weight-1m": exc.headers.get("x-mbx-used-weight-1m", "")}
                w = headers.get("x-mbx-used-weight-1m")
                if w:
                    self.used_weight_observed = max(self.used_weight_observed, int(w))
                if status in (429, 418) and attempt < 2:
                    time.sleep(30.0)
                    last_err = f"HTTP {status}; retrying"
                    continue
                parsed = _try_json(raw)
                return self._archive(slug, endpoint, params, url, status, headers, raw,
                                     parsed, f"HTTP {status}: {parsed}", None,
                                     first_ts_key, last_ts_key, archive_rows)
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                status = 0
                raw = b""
                headers = {}
                last_err = f"network error: {exc}"
                if attempt < 2:
                    time.sleep(5.0)
                    continue
                return self._archive(slug, endpoint, params, url, 0, headers, raw, None,
                                     last_err, None, first_ts_key, last_ts_key, archive_rows)
            break
        parsed = _try_json(raw)
        if not isinstance(parsed, list):
            err = parsed if isinstance(parsed, dict) else None
            return self._archive(slug, endpoint, params, url, status, headers, raw, parsed,
                                 json.dumps(err) if err else None,
                                 len(parsed) if isinstance(parsed, list) else None,
                                 first_ts_key, last_ts_key, archive_rows)
        return self._archive(slug, endpoint, params, url, status, headers, raw, parsed, None,
                             len(parsed), first_ts_key, last_ts_key, archive_rows)


def _try_json(raw: bytes):
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def _row_ts(row, key: str | None):
    if key is None:
        return None
    if isinstance(row, dict):
        return int(row[key])
    if isinstance(row, list):
        return int(row[0])  # kline arrays: element 0 is the open time
    return None


def schema_of(rec: dict) -> dict:
    body = rec.get("archived_response")
    if isinstance(body, list) and body:
        row = body[0]
        if isinstance(row, dict):
            return {"row_type": "object", "fields": sorted(row.keys())}
        if isinstance(row, list):
            return {"row_type": "array", "fields": [f"[{i}]" for i in range(len(row))]}
    return {"row_type": "none", "fields": []}


# --- depth measurement primitives -------------------------------------------


def backward_walk(runner: ProbeRunner, name: str, endpoint: str, params_style: str,
                  symbol: str, period: str, *, floor_ms: int, page_cap: int,
                  limit: int, ts_key: str | None = "timestamp") -> dict:
    """Paginate backwards with endTime/limit until empty, floor, or page cap."""
    period_ms = PERIOD_MS[period]
    pages: list[dict] = []
    cursor_end = int(time.time() * 1000) + period_ms
    boundary = None
    stop_reason = None
    empty_probe = None
    for page_no in range(page_cap):
        params = _base_params(params_style, symbol, period)
        params["endTime"] = cursor_end
        params["limit"] = limit
        rec = runner.get(
            f"{name}_{symbol}_{period}_walk_p{page_no:02d}", endpoint, params,
            archive_rows=3, first_ts_key=ts_key, last_ts_key=ts_key)
        rows = rec.get("row_count") or 0
        if rec.get("http_status") != 200:
            stop_reason = f"http_{rec.get('http_status')}"
            break
        if rows == 0:
            stop_reason = "empty_page"
            empty_probe = rec["probe_id"]
            boundary = cursor_end
            break
        pages.append({"page": page_no, "probe_id": rec["probe_id"], "rows": rows,
                      "first_ms": rec["first_row_ms"], "last_ms": rec["last_row_ms"]})
        lowest = rec["first_row_ms"]
        if lowest <= floor_ms:
            stop_reason = "authorized_window_floor_reached"
            boundary = lowest
            break
        cursor_end = lowest - 1
    else:
        stop_reason = "page_cap_hit"
        boundary = pages[-1]["first_ms"] if pages else None
    if stop_reason == "page_cap_hit" and pages:
        # one extra request: does anything exist before the lowest walked row?
        params = _base_params(params_style, symbol, period)
        params["endTime"] = pages[-1]["first_ms"] - 1
        params["limit"] = 1
        rec = runner.get(f"{name}_{symbol}_{period}_walk_belowcap", endpoint, params,
                         archive_rows=2, first_ts_key=ts_key, last_ts_key=ts_key)
        boundary = pages[-1]["first_ms"]
        stop_reason = ("page_cap_hit_data_continues" if rec.get("row_count")
                       else "page_cap_hit_boundary_confirmed_empty_below")
    earliest = pages[-1]["first_ms"] if pages else None
    latest = pages[0]["last_ms"] if pages else None
    return {
        "symbol": symbol, "period": period, "method": "backward_walk",
        "pages": pages, "page_count": len(pages),
        "earliest_measured_ms": earliest,
        "earliest_measured_utc": utc_iso(earliest) if earliest else None,
        "latest_walk_ms": latest,
        "latest_walk_utc": utc_iso(latest) if latest else None,
        "walk_stop_reason": stop_reason,
        "boundary_note": (
            f"empty page at endTime={boundary} ({utc_iso(boundary)})" if boundary and stop_reason == "empty_page"
            else stop_reason),
        "floor_ms": floor_ms,
        "page_cap": page_cap,
    }


def anchor_exists(runner: ProbeRunner, name: str, endpoint: str, params_style: str,
                  symbol: str, period: str, at_ms: int, *,
                  ts_key: str | None = "timestamp", span_ms: int | None = None) -> dict:
    period_ms = PERIOD_MS[period]
    span = span_ms if span_ms is not None else max(2 * period_ms, 10 * 60_000)
    params = _base_params(params_style, symbol, period)
    params["startTime"] = at_ms
    params["endTime"] = at_ms + span
    params["limit"] = 1
    rec = runner.get(f"{name}_{symbol}_{period}_anchor_{at_ms}", endpoint, params,
                     archive_rows=2, first_ts_key=ts_key, last_ts_key=ts_key)
    return {
        "anchor_ms": at_ms, "anchor_utc": utc_iso(at_ms),
        "exists": bool(rec.get("row_count")),
        "row_ms": rec.get("first_row_ms"),
        "row_utc": utc_iso(rec["first_row_ms"]) if rec.get("first_row_ms") else None,
        "probe_id": rec["probe_id"],
    }


def binary_search_boundary(runner: ProbeRunner, name: str, endpoint: str, params_style: str,
                           symbol: str, period: str, *, true_ms: int, false_ms: int,
                           ts_key: str | None = "timestamp") -> dict:
    """Pin earliest retrievable timestamp within ~1 period between a known-true
    and a known-false anchor (data exists at/after true_ms, not at false_ms)."""
    period_ms = PERIOD_MS[period]
    lo, hi = true_ms, false_ms
    steps = 0
    while hi + period_ms < lo and steps < 14:
        mid = (lo + hi) // 2
        res = anchor_exists(runner, name, endpoint, params_style, symbol, period, mid,
                            ts_key=ts_key)
        steps += 1
        if res["exists"]:
            lo = min(lo, res["row_ms"] or mid)
        else:
            hi = mid
    confirm = anchor_exists(runner, name, endpoint, params_style, symbol, period, lo,
                            ts_key=ts_key)
    below = anchor_exists(runner, name, endpoint, params_style, symbol, period,
                          max(hi - 3 * period_ms, hi - 1), span_ms=3 * period_ms,
                          ts_key=ts_key)
    return {
        "symbol": symbol, "period": period,
        "method": "binary_search",
        "steps": steps,
        "earliest_measured_ms": confirm.get("row_ms"),
        "earliest_measured_utc": utc_iso(confirm["row_ms"]) if confirm.get("row_ms") else None,
        "bracket_false_before_ms": hi,
        "bracket_false_before_utc": utc_iso(hi),
        "confirm_probe": confirm["probe_id"],
        "below_boundary_exists": below["exists"],
        "below_probe": below["probe_id"],
    }


def _base_params(params_style: str, symbol: str, period: str) -> dict:
    if params_style == "pair":
        return {"pair": symbol, "contractType": "PERPETUAL", "period": period}
    return {"symbol": symbol, "period": period}


def main() -> int:
    runner = ProbeRunner()
    started = now_utc_iso()
    results: dict = {"schema": "v14_p1_a3_probe_results_v1", "started_utc": started,
                     "finished_utc": None, "fapi_base": FAPI_BASE,
                     "windows": {
                         "authorized_ms": [AUTH_START_MS, AUTH_END_MS],
                         "authorized_utc": [utc_iso(AUTH_START_MS), utc_iso(AUTH_END_MS)],
                         "screen_ms": [SCREEN_START_MS, SCREEN_END_MS],
                         "screen_utc": [utc_iso(SCREEN_START_MS), utc_iso(SCREEN_END_MS)],
                     },
                     "endpoints": {}}

    # ---------------- Phase A: /futures/data/* candidate sources -------------
    for name, endpoint, style in STATS_ENDPOINTS:
        block: dict = {"endpoint": endpoint, "param_style": style, "symbols": {}}

        # basis param-style verification first (pair+contractType vs symbol)
        if style == "pair":
            p_pair = {"pair": "BTCUSDT", "contractType": "PERPETUAL", "period": "5m", "limit": 2}
            rec_pair = runner.get(f"{name}_BTCUSDT_5m_semantics_pair", endpoint, p_pair,
                                  archive_rows=2)
            p_sym = {"symbol": "BTCUSDT", "period": "5m", "limit": 2}
            rec_sym = runner.get(f"{name}_BTCUSDT_5m_semantics_symbolparam", endpoint, p_sym,
                                 archive_rows=2)
            style_eff = ("pair" if rec_pair.get("http_status") == 200
                         else ("symbol" if rec_sym.get("http_status") == 200 else "pair"))
            block["param_style_effective"] = style_eff
            block["param_style_probes"] = [rec_pair["probe_id"], rec_sym["probe_id"]]
            style = style_eff
        block["param_style"] = style

        # semantics probes (latest page) for every symbol at 5m
        for symbol in SYMBOLS:
            params = _base_params(style, symbol, "5m")
            params["limit"] = 5
            rec = runner.get(f"{name}_{symbol}_5m_semantics", endpoint, params, archive_rows=5)
            if symbol not in block["symbols"]:
                block["symbols"][symbol] = {}
            block["symbols"][symbol]["semantics_5m"] = {
                "probe_id": rec["probe_id"], "http_status": rec["http_status"],
                "schema": schema_of(rec),
                "latest_row_ms": rec["last_row_ms"],
                "latest_row_utc": rec["last_row_utc"],
            }

        # BTC 5m full backward walk (primary measured boundary)
        block["symbols"]["BTCUSDT"]["walk_5m"] = backward_walk(
            runner, name, endpoint, style, "BTCUSDT", "5m",
            floor_ms=AUTH_START_MS, page_cap=WALK_PAGE_CAP, limit=WALK_PAGE_LIMIT_STATS)

        # other symbols: screen-window anchor + coarse depth anchors at 5m
        for symbol in ["ETHUSDT", "SOLUSDT", "XRPUSDT"]:
            anchors = [
                anchor_exists(runner, name, endpoint, style, symbol, "5m", SCREEN_START_MS),
                anchor_exists(runner, name, endpoint, style, symbol, "5m",
                              int(time.time() * 1000) - 30 * 24 * 3600_000),
                anchor_exists(runner, name, endpoint, style, symbol, "5m",
                              int(time.time() * 1000) - 7 * 24 * 3600_000),
            ]
            block["symbols"][symbol]["anchors_5m"] = anchors

        # BTC screen-start anchor (classification evidence even if walk capped)
        block["symbols"]["BTCUSDT"]["anchor_screen_start_5m"] = anchor_exists(
            runner, name, endpoint, style, "BTCUSDT", "5m", SCREEN_START_MS)

        # BTC 15m backward walk (staged-bar clock); others: semantics + anchor
        block["symbols"]["BTCUSDT"]["walk_15m"] = backward_walk(
            runner, name, endpoint, style, "BTCUSDT", "15m",
            floor_ms=AUTH_START_MS, page_cap=WALK_PAGE_CAP, limit=WALK_PAGE_LIMIT_STATS)
        for symbol in ["ETHUSDT", "SOLUSDT", "XRPUSDT"]:
            params = _base_params(style, symbol, "15m")
            params["limit"] = 5
            rec = runner.get(f"{name}_{symbol}_15m_semantics", endpoint, params, archive_rows=5)
            anc = anchor_exists(runner, name, endpoint, style, symbol, "15m", SCREEN_START_MS)
            block["symbols"][symbol]["semantics_15m"] = {
                "probe_id": rec["probe_id"], "http_status": rec["http_status"],
                "latest_row_ms": rec["last_row_ms"], "latest_row_utc": rec["last_row_utc"]}
            block["symbols"][symbol]["anchor_screen_start_15m"] = anc

        # period acceptance probes on BTC (documented enum partially evidenced)
        block["period_acceptance"] = {}
        for period in ["30m", "1h", "1d"]:
            params = _base_params(style, "BTCUSDT", period)
            params["limit"] = 2
            rec = runner.get(f"{name}_BTCUSDT_{period}_acceptance", endpoint, params,
                             archive_rows=2)
            block["period_acceptance"][period] = {
                "probe_id": rec["probe_id"], "http_status": rec["http_status"],
                "schema": schema_of(rec) if rec["http_status"] == 200 else rec.get("error")}

        results["endpoints"][name] = block

    # ---------------- Phase B: kline routes (basis derivation + re-key) ------
    for name, endpoint in KLINE_ROUTES:
        block: dict = {"endpoint": endpoint, "interval": "15m", "symbols": {}}
        for symbol in SYMBOLS:
            rec = runner.get(f"{name}_{symbol}_15m_semantics", endpoint,
                             {"symbol": symbol, "interval": "15m", "limit": 3},
                             archive_rows=3, first_ts_key=None, last_ts_key=None)
            listing = runner.get(f"{name}_{symbol}_15m_listing", endpoint,
                                 {"symbol": symbol, "interval": "15m",
                                  "startTime": LISTING_PROBE_MS, "limit": 2},
                                 archive_rows=2, first_ts_key=None, last_ts_key=None)
            wstart = runner.get(f"{name}_{symbol}_15m_windowstart", endpoint,
                                {"symbol": symbol, "interval": "15m",
                                 "startTime": SCREEN_START_MS,
                                 "endTime": SCREEN_START_MS + PERIOD_MS["15m"], "limit": 2},
                                archive_rows=2, first_ts_key=None, last_ts_key=None)
            block["symbols"][symbol] = {
                "semantics": {"probe_id": rec["probe_id"], "http_status": rec["http_status"],
                              "schema": schema_of(rec),
                              "latest_row_ms": rec["last_row_ms"],
                              "latest_row_utc": rec["last_row_utc"]},
                "listing_probe": {"probe_id": listing["probe_id"],
                                  "http_status": listing["http_status"],
                                  "first_row_ms": listing["first_row_ms"],
                                  "first_row_utc": listing["first_row_utc"],
                                  "rows": listing.get("row_count")},
                "screen_start_coverage": {"probe_id": wstart["probe_id"],
                                          "exists": bool(wstart.get("row_count")),
                                          "row_ms": wstart.get("first_row_ms"),
                                          "row_utc": wstart.get("first_row_utc")},
            }
        # window-end spot check on BTCUSDT
        wend = runner.get(f"{name}_BTCUSDT_15m_windowend", endpoint,
                          {"symbol": "BTCUSDT", "interval": "15m",
                           "startTime": SCREEN_END_MS - PERIOD_MS["15m"],
                           "endTime": SCREEN_END_MS, "limit": 2},
                          archive_rows=2, first_ts_key=None, last_ts_key=None)
        block["symbols"]["BTCUSDT"]["screen_end_coverage"] = {
            "probe_id": wend["probe_id"], "exists": bool(wend.get("row_count")),
            "row_ms": wend.get("first_row_ms"), "row_utc": wend.get("first_row_utc")}
        results["endpoints"][name] = block

    # ---------------- Phase C: funding settlement (re-key) --------------------
    name, endpoint = FUNDING_ENDPOINT
    block: dict = {"endpoint": endpoint, "symbols": {}}
    for symbol in SYMBOLS:
        rec = runner.get(f"{name}_{symbol}_semantics", endpoint,
                         {"symbol": symbol, "limit": 3}, archive_rows=3,
                         first_ts_key="fundingTime", last_ts_key="fundingTime")
        listing = runner.get(f"{name}_{symbol}_listing", endpoint,
                             {"symbol": symbol, "startTime": LISTING_PROBE_MS, "limit": 2},
                             archive_rows=2, first_ts_key="fundingTime", last_ts_key="fundingTime")
        wstart = runner.get(f"{name}_{symbol}_windowstart", endpoint,
                            {"symbol": symbol, "startTime": SCREEN_START_MS,
                             "endTime": SCREEN_START_MS + 3 * 8 * 3600_000, "limit": 5},
                            archive_rows=5, first_ts_key="fundingTime", last_ts_key="fundingTime")
        wend = runner.get(f"{name}_{symbol}_windowend", endpoint,
                          {"symbol": symbol, "startTime": SCREEN_END_MS - 3 * 8 * 3600_000,
                           "endTime": SCREEN_END_MS, "limit": 5},
                          archive_rows=5, first_ts_key="fundingTime", last_ts_key="fundingTime")
        block["symbols"][symbol] = {
            "semantics": {"probe_id": rec["probe_id"], "http_status": rec["http_status"],
                          "schema": schema_of(rec),
                          "latest_row_ms": rec["last_row_ms"], "latest_row_utc": rec["last_row_utc"]},
            "listing_probe": {"probe_id": listing["probe_id"],
                              "first_row_ms": listing["first_row_ms"],
                              "first_row_utc": listing["first_row_utc"],
                              "rows": listing.get("row_count")},
            "screen_start_coverage": {"probe_id": wstart["probe_id"],
                                      "exists": bool(wstart.get("row_count")),
                                      "row_ms": wstart.get("first_row_ms")},
            "screen_end_coverage": {"probe_id": wend["probe_id"],
                                    "exists": bool(wend.get("row_count")),
                                    "row_ms": wend.get("first_row_ms")},
        }
    results["endpoints"][name] = block

    # ---------------- Phase D: OI current snapshot (re-key) -------------------
    name, endpoint = OI_SNAPSHOT_ENDPOINT
    block: dict = {"endpoint": endpoint, "symbols": {}}
    for symbol in SYMBOLS:
        rec = runner.get(f"{name}_{symbol}_current", endpoint, {"symbol": symbol},
                         archive_rows=2, first_ts_key="time", last_ts_key="time")
        rec2 = runner.get(f"{name}_{symbol}_withrange", endpoint,
                          {"symbol": symbol, "startTime": SCREEN_START_MS,
                           "endTime": SCREEN_START_MS + 3600_000},
                          archive_rows=2, first_ts_key="time", last_ts_key="time")
        block["symbols"][symbol] = {
            "current_snapshot": {"probe_id": rec["probe_id"], "http_status": rec["http_status"],
                                 "schema": schema_of(rec),
                                 "time_ms": rec["last_row_ms"], "time_utc": rec["last_row_utc"]},
            "range_params_probe": {"probe_id": rec2["probe_id"],
                                   "http_status": rec2["http_status"],
                                   "time_ms": rec2.get("last_row_ms"),
                                   "time_utc": rec2.get("last_row_utc"),
                                   "note": "startTime/endTime given; endpoint semantics check"}
        }
    results["endpoints"][name] = block

    results["finished_utc"] = now_utc_iso()
    results["request_budget"] = {
        "used": runner.count, "hard_cap": HARD_CAP, "target": "< 400",
        "max_used_weight_1m_observed": runner.used_weight_observed,
        "sleep_between_requests_s": SLEEP_S,
    }
    results["probe_index"] = runner.records
    out = LANE_DIR / "probe_results.json"
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"request_budget": results["request_budget"],
                      "endpoints": sorted(results["endpoints"]),
                      "output": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
