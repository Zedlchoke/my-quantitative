"""RATES-NG1 P0 substrate pullers + census builders.

Deterministic, bounded pulls of the frozen consumption set (plan
section 3), each sha256-pinned into the substrate manifest:

- S5 Treasury.gov daily par-yield curve: per-year CSVs 1990..2026
  (keyless; per-year URL given by the dispatch packet, Lead-verified
  live 2026-09-12);
- S2 FRED granted-set re-pin: DGS10, DGS2, DFII10, DFII5, T10YIE,
  T5YIE, CPIAUCSL (keyed; programmatic key load, never echoed);
- EODHD family-1 ETP census: eod/TLT.US, eod/IEF.US, eod/IEI.US,
  eod/SHY.US RAW primary + adjusted cross-check, plus the US delisted
  channel probe (census item, not a floor);
- TreasuryDirect TA_WS per-year auction ``search`` windows (keyless;
  the ``announced`` endpoint is hard-capped at the latest 250 records
  and cannot carry a 2018..2026 census -- measured 2026-09-12).

Every fetch is bounded (3 attempts, small sleeps), every failure is
recorded with the key REDACTED, and nothing is ever fabricated when a
source fails: the caller records fail-closed BLOCKED evidence.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.rates_ng1 import plane_adapter as pa  # noqa: E402

USER_AGENT = "my-quantitative-research/1.0"
REDACT_RE = re.compile(r"(api_key|api_token)=[^&\s\"']+")


def redact(text: str) -> str:
    return REDACT_RE.sub(r"\1=REDACTED", text)


def load_key(name: str, env_path: str | None = None) -> str:
    """Load an API key from the environment or the gitignored .env.

    The key value is NEVER printed, logged, or written anywhere by this
    module (V13 law).  .env is parsed line-wise for exactly one
    ``NAME=`` prefix; its contents are never surfaced.
    """
    key = os.environ.get(name)
    if key:
        return key
    # the gitignored .env lives in the ROOT checkout (owner space); the
    # value is parsed line-wise and NEVER surfaced (V13 law)
    path = env_path or "/Users/hoangminhlong/my-quantitative/.env"
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped.startswith(name + "="):
                key = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not key:
        raise RuntimeError(
            f"{name} not found in environment or .env: fail closed")
    os.environ[name] = key          # environment only
    return key


def fetch_url(url: str, attempts: int = 3, timeout: int = 120,
              sleep_s: float = 1.0) -> bytes:
    """Bounded fetch: small retry loop, redacted failures.  Raises on
    the final attempt (caller records fail-closed BLOCKED evidence)."""
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - recorded redacted only
            last_exc = RuntimeError(redact(repr(exc)))
            if attempt < attempts:
                time.sleep(sleep_s * attempt)
    raise last_exc if last_exc else RuntimeError("fetch failed")


def treasury_curve_url(year: int) -> str:
    return (
        "https://home.treasury.gov/resource-center/data-chart-center/"
        "interest-rates/daily-treasury-rates.csv/"
        f"{year}/all?type=daily_treasury_yield_curve"
        f"&field_tdr_date_value={year}&page&_format=csv")


def fred_observations_url(series_id: str, realtime_start: str | None,
                          realtime_end: str = "9999-12-31") -> str:
    key = load_key("FRED_API_KEY")
    url = (f"https://api.stlouisfed.org/fred/series/observations"
           f"?series_id={series_id}&file_type=json&api_key={key}")
    if realtime_start:
        url += f"&realtime_start={realtime_start}&realtime_end={realtime_end}"
    return url


def eodhd_eod_url(symbol: str, adjusted: bool) -> str:
    key = load_key("EODHD_API_KEY")
    return (f"https://eodhd.com/api/eod/{symbol}?api_token={key}"
            f"&fmt=json&order=a&period=d" + ("&adjusted=true" if adjusted
                                             else ""))


def eodhd_delisted_url() -> str:
    key = load_key("EODHD_API_KEY")
    return (f"https://eodhd.com/api/exchange-symbol-list/US"
            f"?api_token={key}&fmt=json&delisted=1")


def eodhd_never_existed_url(symbol: str) -> str:
    key = load_key("EODHD_API_KEY")
    return (f"https://eodhd.com/api/eod/{symbol}?api_token={key}"
            f"&fmt=json&order=a&period=d")


def ta_ws_search_url(year: int) -> str:
    return ("https://www.treasurydirect.gov/TA_WS/securities/search"
            f"?format=json&startDate=01/01/{year}&endDate=12/31/{year}")


# ---------------------------------------------------------------------- #
# S5 Treasury par-yield curve
# ---------------------------------------------------------------------- #

def expected_business_days(start_iso: str, end_iso: str) -> int:
    """Count Mon-Fri days in [start, end] (weekday grid; the disclosed
    expectation convention for the coverage floor)."""
    d0 = dt.date.fromisoformat(start_iso)
    d1 = dt.date.fromisoformat(end_iso)
    n = 0
    d = d0
    while d <= d1:
        if d.weekday() < 5:
            n += 1
        d += dt.timedelta(days=1)
    return n


def treasury_curve_census(year_rows: Mapping[int, list[dict[str, str]]],
                          coverage_start: str, coverage_end: str) -> dict:
    """Depth/coverage census: rows per year, business-day coverage
    fraction on the 2005..2026 window, tenor columns per year."""
    by_year: dict[str, dict] = {}
    covered_2005_2026 = 0
    for year in sorted(year_rows):
        rows = year_rows[year]
        dates = {r["date"] for r in rows}
        rec: dict[str, Any] = {
            "rows": len(rows),
            "first_date": min(dates),
            "last_date": max(dates),
            "tenor_columns": [c for c in rows[0] if c != "date"],
        }
        if 2005 <= year <= 2026:
            bds = expected_business_days(
                max(dt.date(year, 1, 1).isoformat(), coverage_start),
                min(dt.date(year, 12, 31).isoformat(), coverage_end))
            got = sum(
                1 for d in dates
                if coverage_start <= d <= coverage_end)
            rec["expected_business_days"] = bds
            rec["curve_days_in_window"] = got
            covered_2005_2026 += got
        by_year[str(year)] = rec
    expected_total = expected_business_days(coverage_start, coverage_end)
    coverage_frac = (round(covered_2005_2026 / expected_total, 6)
                     if expected_total else 0.0)
    # tenor availability census across years
    tenor_by_year = {y: r["tenor_columns"] for y, r in by_year.items()}
    return {
        "years": by_year,
        "year_count": len(by_year),
        "tenor_columns_by_year": tenor_by_year,
        "coverage_window": [coverage_start, coverage_end],
        "expected_business_days_window": expected_total,
        "curve_days_in_window": covered_2005_2026,
        "coverage_fraction": coverage_frac,
    }


# ---------------------------------------------------------------------- #
# S2 FRED re-pin
# ---------------------------------------------------------------------- #

def parse_fred_payload(data: bytes) -> list[dict[str, str]]:
    payload = json.loads(data.decode("utf-8"))
    obs = payload["observations"] if isinstance(payload, dict) else payload
    for o in obs:
        if not {"date", "value"} <= set(o):
            raise ValueError("FRED observation lacks date/value")
    return obs


def fred_overlap_verify(pinned_obs: list[dict[str, str]],
                        fresh_obs: list[dict[str, str]]) -> dict:
    """0-drift verify on the overlap between the inherited pin and the
    fresh vintaged pull.

    Matching law: the inherited pin was pulled with a bounded realtime
    window, so its FIRST vintage rows carry a clipped realtime_start
    (the requested window start, e.g. 2017-01-01) instead of the true
    vintage date.  Rows at that clip edge are compared against the
    fresh row for the same obs_date whose realtime_start is the LATEST
    at-or-before the clip edge (the vintage actually live at the pin's
    window start).  All other rows match on the exact
    (date, realtime_start) key.  Every matched pair must carry the
    IDENTICAL value.  realtime_end may legitimately advance when a
    vintage is superseded (recorded, never counted as drift).
    """
    by_date: dict[str, list[dict[str, str]]] = {}
    for o in fresh_obs:
        by_date.setdefault(o["date"], []).append(o)
    for rows in by_date.values():
        rows.sort(key=lambda o: o["realtime_start"])
    clip_edge = min(o["realtime_start"] for o in pinned_obs) \
        if pinned_obs else None

    compared = 0
    equal = 0
    exact_key_rows = 0
    clip_edge_rows = 0
    realtime_end_advanced = 0
    mismatches: list[dict[str, str]] = []
    missing = 0
    for o in pinned_obs:
        date = o["date"]
        fresh = None
        mode = None
        exact = by_date.get(date, [])
        for cand in exact:
            if cand["realtime_start"] == o["realtime_start"]:
                fresh, mode = cand, "exact_key"
                break
        if fresh is None and o["realtime_start"] == clip_edge:
            earlier = [c for c in exact
                       if c["realtime_start"] <= clip_edge]
            if earlier:
                fresh, mode = earlier[-1], "clip_edge_vintage"
        if fresh is None:
            missing += 1
            mismatches.append({"date": date,
                               "realtime_start": o["realtime_start"],
                               "reason": "MISSING_IN_FRESH"})
            continue
        compared += 1
        if mode == "exact_key":
            exact_key_rows += 1
        else:
            clip_edge_rows += 1
        if o["value"] == fresh["value"]:
            equal += 1
        else:
            mismatches.append({"date": date,
                               "realtime_start": o["realtime_start"],
                               "pinned": o["value"], "fresh": fresh["value"],
                               "match_mode": mode or "?"})
        if fresh.get("realtime_end", o.get("realtime_end")) != \
                o.get("realtime_end"):
            realtime_end_advanced += 1
    zero_drift = compared > 0 and (compared - equal) == 0 and missing == 0
    return {
        "pinned_rows": len(pinned_obs),
        "fresh_rows": len(fresh_obs),
        "clip_edge_realtime_start": clip_edge,
        "overlap_rows_compared": compared,
        "exact_key_rows": exact_key_rows,
        "clip_edge_vintage_rows": clip_edge_rows,
        "overlap_value_equal": equal,
        "drift_count": compared - equal + missing,
        "realtime_end_advanced_rows": realtime_end_advanced,
        "mismatches_sample": mismatches[:10],
        "zero_drift_on_overlap": zero_drift,
    }


# ---------------------------------------------------------------------- #
# EODHD ETP census
# ---------------------------------------------------------------------- #

def split_steps(raw_rows: list[dict[str, Any]],
                adj_rows: list[dict[str, Any]],
                rel_threshold: float = 0.10) -> dict:
    """Corp-actions cross-check (V8 G4 method): a split shows as the RAW
    close ratio deviating from the ADJUSTED close ratio by a large
    factor on one day."""
    adj_by_date = {r["date"]: float(r["close"]) for r in adj_rows}
    steps: list[dict[str, Any]] = []
    prev_raw: float | None = None
    prev_adj: float | None = None
    max_delta = 0.0
    for r in raw_rows:
        date = r["date"]
        if date not in adj_by_date:
            continue
        raw_c = float(r["close"])
        adj_c = adj_by_date[date]
        if prev_raw and prev_raw > 0 and prev_adj and prev_adj > 0:
            raw_ratio = raw_c / prev_raw
            adj_ratio = adj_c / prev_adj
            if adj_ratio > 0:
                rel = abs(raw_ratio / adj_ratio - 1.0)
                max_delta = max(max_delta, rel)
                if rel > rel_threshold:
                    steps.append({"date": date,
                                  "raw_ratio": round(raw_ratio, 6),
                                  "adj_ratio": round(adj_ratio, 6)})
        prev_raw, prev_adj = raw_c, adj_c
    return {"split_steps": steps, "split_step_count": len(steps),
            "max_rel_ratio_deviation": round(max_delta, 8)}


def delisted_census(entries: list[dict[str, Any]]) -> dict:
    """Delisted-channel probe (census item, NOT a floor): counts and
    name-pattern findings only."""
    with_name = sum(1 for x in entries if x.get("Name"))
    treasury_named = [
        {"code": x.get("Code"), "name": x.get("Name")}
        for x in entries
        if "TREASUR" in str(x.get("Name", "")).upper()]
    fund_type = sum(1 for x in entries if str(x.get("Type", "")).upper()
                    == "FUND")
    return {
        "total_delisted_symbols": len(entries),
        "entries_with_name": with_name,
        "fund_type_count": fund_type,
        "treasury_named_count": len(treasury_named),
        "treasury_named_sample": treasury_named[:10],
        "note": ("census item only (dispatch packet: 'record counts and "
                 "names, not a floor')"),
    }


# ---------------------------------------------------------------------- #
# TA_WS auction calendar census
# ---------------------------------------------------------------------- #

def auction_census(window_rows: list[list[dict[str, Any]]],
                   ann_start: str, ann_end: str) -> dict:
    """PIT census of official announcement events: dedupe by
    (cusip, announcementDate, auctionDate) -- a reopening re-announces
    the SAME cusip, so cusip alone is not an event key -- keep events
    with announcementDate in [ann_start, ann_end], record per-event
    official evidence filenames."""
    seen: dict[tuple[str, str, str], dict[str, Any]] = {}
    for rows in window_rows:
        for r in rows:
            cusip = str(r.get("cusip", "")).strip()
            ann = str(r.get("announcementDate", ""))[:10]
            aud = str(r.get("auctionDate", ""))[:10]
            if not cusip or not ann:
                continue
            seen[(cusip, ann, aud)] = r
    events = []
    for (cusip, ann, _aud), r in sorted(
            seen.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        ann = str(r.get("announcementDate", ""))[:10]
        if not (ann_start <= ann <= ann_end):
            continue
        events.append({
            "cusip": cusip,
            "securityType": r.get("securityType"),
            "securityTerm": r.get("securityTerm"),
            "announcementDate": ann,
            "auctionDate": str(r.get("auctionDate", ""))[:10],
            "issueDate": str(r.get("issueDate", ""))[:10],
            "maturityDate": str(r.get("maturityDate", ""))[:10],
            "series": r.get("series"),
            "evidence": {
                "endpoint": ta_ws_search_url(2018).split("?")[0] +
                " (per-year search windows)",
                "pdf_announcement": r.get("pdfFilenameAnnouncement") or None,
                "xml_announcement": r.get("xmlFilenameAnnouncement") or None,
            },
        })
    by_type: dict[str, int] = {}
    for e in events:
        t = e["securityType"] or "UNKNOWN"
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "announcement_window": [ann_start, ann_end],
        "event_count": len(events),
        "events_by_security_type": by_type,
        "first_announcement": min((e["announcementDate"] for e in events),
                                  default=None),
        "last_announcement": max((e["announcementDate"] for e in events),
                                 default=None),
        "events": events,
    }


# ---------------------------------------------------------------------- #
# P-7 canaries (each fabricated access must FAIL / be refused)
# ---------------------------------------------------------------------- #

def canary_fabricated_curve_date(plane: pa.RatesNG1Plane) -> dict:
    """A date that never existed (2025-11-31: November has 30 days)
    must be refused by the exact-date curve lookup."""
    fabricated = "2025-11-31"
    try:
        plane.curve_row(fabricated)
    except pa.UnknownCurveDate as exc:
        return {"canary": "fabricated_curve_date",
                "probe": fabricated,
                "expected": "REFUSED",
                "observed": f"UnknownCurveDate: {exc}",
                "verdict": "REFUSED_AS_EXPECTED"}
    return {"canary": "fabricated_curve_date", "probe": fabricated,
            "expected": "REFUSED", "observed": "LOOKUP SUCCEEDED",
            "verdict": "FAIL_CANARY_BREACH"}


def canary_fabricated_tenor(plane: pa.RatesNG1Plane) -> dict:
    """A tenor column no official curve file ever carried ('13 Mo')
    must be refused by the tenor lookup."""
    fabricated = "13 Mo"
    try:
        plane.curve_tenor("2025-06-02", fabricated)
    except pa.UnknownTenor as exc:
        return {"canary": "fabricated_tenor_column",
                "probe": fabricated,
                "expected": "REFUSED",
                "observed": f"UnknownTenor: {exc}",
                "verdict": "REFUSED_AS_EXPECTED"}
    except pa.UnknownCurveDate as exc:
        return {"canary": "fabricated_tenor_column",
                "probe": fabricated,
                "expected": "REFUSED",
                "observed": f"UnknownCurveDate: {exc}",
                "verdict": "REFUSED_AS_EXPECTED"}
    return {"canary": "fabricated_tenor_column", "probe": fabricated,
            "expected": "REFUSED", "observed": "LOOKUP SUCCEEDED",
            "verdict": "FAIL_CANARY_BREACH"}


def canary_never_existed_ticker() -> dict:
    """A ticker that never existed on EODHD must NOT return a valid
    price series (V8 never-existed-controls law)."""
    symbol = "ZZTREASURYNOPE9.US"
    try:
        data = fetch_url(eodhd_never_existed_url(symbol), attempts=2,
                         timeout=60)
    except Exception as exc:  # noqa: BLE001 - refusal is the expectation
        return {"canary": "never_existed_ticker",
                "probe": symbol,
                "expected": "REFUSED (no valid series)",
                "observed": f"fetch refused: {redact(str(exc))[:200]}",
                "verdict": "REFUSED_AS_EXPECTED"}
    text = data.decode("utf-8", "replace").strip()
    invalid = (text.startswith("{") and "errorMessage" in text[:200]) \
        or text in ("", "[]", "null")
    if invalid:
        return {"canary": "never_existed_ticker",
                "probe": symbol,
                "expected": "REFUSED (no valid series)",
                "observed": f"vendor returned no series "
                            f"({redact(text[:120])})",
                "verdict": "REFUSED_AS_EXPECTED"}
    return {"canary": "never_existed_ticker", "probe": symbol,
            "expected": "REFUSED (no valid series)",
            "observed": "VALID SERIES RETURNED (fabrication risk)",
            "verdict": "FAIL_CANARY_BREACH"}


# ---------------------------------------------------------------------- #
# substrate manifest
# ---------------------------------------------------------------------- #

def build_manifest_entry(rel_name: str, data: bytes, source_url: str) -> dict:
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "source_url": redact(source_url),
        "rel_path": os.path.join("raw_substrate", rel_name),
    }
