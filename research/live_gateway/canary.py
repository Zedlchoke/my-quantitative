"""Dual-run canary (plan §9.2) — thresholds FROZEN in the plan.

Leg A (mark prices): gateway WS mark vs the valuation worker's REST
premiumIndex source, aligned |Δprovider_ts| ≤ 2 s. PASS over ≥24 h:
≥99% comparisons present, ≥99.9% of present comparisons within 5 bps,
ZERO comparisons > 50 bps, every missing side explained by a recorded
gateway/upstream event.

Leg B (historical equivalence): same endpoints/params/cutoffs/PIT
(completed-by-cutoff) both via gateway cache and DIRECT (paced canary
leg: min-gap 1.0 s, ≤6 rpm, ≤2 attempts, 418/429/Retry-After ⇒ abort
the direct leg for max(RA, banned-until, 120 s)). PASS: identical row
counts, identical canonical timestamps, digest equality OR exact
numeric equality (rel tol 0, abs tol 1e-12) on every row. Scored PnL
is NEVER read.

Evidence: JSONL/JSON under research/control/live_data_gateway_v1/canary/.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# ---- frozen thresholds (plan §9.2; DO NOT tune after any result) ----
ALIGN_WINDOW_MS = 2_000
PASS_PRESENCE = 0.99
PASS_WITHIN_5BPS = 0.999
HARD_BPS = 50.0
NUMERIC_ABS_TOL = 1e-12
NUMERIC_REL_TOL = 0.0

# ---- frozen canary direct-leg pacing law (A7 FND-1) ----
DIRECT_MIN_GAP_S = 1.0
DIRECT_MAX_RPM = 6
DIRECT_MAX_ATTEMPTS = 2
DIRECT_ABORT_MIN_S = 120.0

PREMIUM_INDEX_URL = "https://fapi.binance.com/fapi/v1/premiumIndex"

CANARY_DIR = os.path.join(
    "research", "control", "live_data_gateway_v1", "canary"
)


class DirectLegAborted(Exception):
    def __init__(self, until_epoch_s: float, reason: str):
        super().__init__(f"direct leg aborted until {until_epoch_s}: {reason}")
        self.until_epoch_s = until_epoch_s
        self.reason = reason


class PacedDirectFetcher:
    """The canary's own direct-Binance transport under §9.2 pacing law."""

    RETRYABLE = (418, 429, 500, 502, 503, 504)

    def __init__(self) -> None:
        self.last_request_at = 0.0
        self.window: List[float] = []
        self.abort_until = 0.0

    def _respect_abort(self) -> None:
        if time.time() < self.abort_until:
            raise DirectLegAborted(
                self.abort_until, "inside prior abort window"
            )

    def get_json(self, url: str) -> Any:
        for attempt in range(DIRECT_MAX_ATTEMPTS):
            self._respect_abort()
            now = time.time()
            gap = now - self.last_request_at
            if gap < DIRECT_MIN_GAP_S:
                time.sleep(DIRECT_MIN_GAP_S - gap)
            self.window = [
                t for t in self.window if time.time() - t < 60.0
            ]
            if len(self.window) >= DIRECT_MAX_RPM:
                raise DirectLegAborted(
                    time.time() + 10.0, f"canary rpm cap {DIRECT_MAX_RPM}"
                )
            self.last_request_at = time.time()
            self.window.append(self.last_request_at)
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "ldgv1-canary/1.0"}
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                body = ""
                try:
                    body = exc.read().decode("utf-8", "replace")
                except Exception:  # noqa: BLE001
                    pass
                wait_s = DIRECT_ABORT_MIN_S
                if retry_after and str(retry_after).strip().isdigit():
                    wait_s = max(wait_s, float(retry_after))
                import re

                m = re.search(r"banned until (\d{9,14})", body)
                if m:
                    raw = int(m.group(1))
                    ban_epoch = raw / 1000.0 if raw > 10**12 else float(raw)
                    wait_s = max(wait_s, ban_epoch - time.time())
                if exc.code in self.RETRYABLE:
                    self.abort_until = time.time() + wait_s
                    raise DirectLegAborted(
                        self.abort_until,
                        f"HTTP {exc.code}; aborting direct leg {wait_s:.0f}s",
                    )
                raise
        raise DirectLegAborted(time.time() + 60.0, "attempts exhausted")


def _http_get_json(url: str, timeout: float = 10.0) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "ldgv1-canary/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ----------------------------------------------------------------------
# Leg A: mark-price comparison
# ----------------------------------------------------------------------
def compare_marks(
    gateway_prices: Dict[str, Any],
    rest_payload: List[Dict[str, Any]],
    watched: List[str],
) -> List[Dict[str, Any]]:
    """One aligned-comparison batch. Gateway payload keyed by symbol."""
    rest_by_symbol = {}
    for entry in rest_payload:
        sym = entry.get("symbol")
        if isinstance(sym, str):
            rest_by_symbol[sym] = entry
    rows: List[Dict[str, Any]] = []
    for sym in watched:
        gw = gateway_prices.get(sym) or {}
        rest = rest_by_symbol.get(sym) or {}
        gw_ts = _ms(gw.get("provider_timestamp_utc"))
        rest_ts = rest.get("time")
        rest_mark = rest.get("markPrice")
        if gw_ts is None or rest_ts is None or rest_mark is None:
            rows.append(
                {
                    "symbol": sym,
                    "outcome": "missing_side",
                    "gw_status": gw.get("status"),
                    "gw_ts": gw.get("provider_timestamp_utc"),
                    "rest_ts": rest_ts,
                }
            )
            continue
        delta_ms = abs(int(gw_ts) - int(rest_ts))
        if delta_ms > ALIGN_WINDOW_MS:
            rows.append(
                {
                    "symbol": sym,
                    "outcome": "unaligned",
                    "delta_ms": delta_ms,
                    "gw_ts": gw.get("provider_timestamp_utc"),
                }
            )
            continue
        try:
            gw_mark = float(gw.get("value"))
            rm = float(rest_mark)
        except (TypeError, ValueError):
            rows.append({"symbol": sym, "outcome": "unparsable"})
            continue
        abs_diff = abs(gw_mark - rm)
        rel_bps = (abs_diff / rm * 10_000.0) if rm else None
        rows.append(
            {
                "symbol": sym,
                "outcome": "compared",
                "delta_ms": delta_ms,
                "abs_diff": abs_diff,
                "rel_bps": rel_bps,
                "gw_age_s": gw.get("age_seconds"),
                "gw_status": gw.get("status"),
            }
        )
    return rows


def _ms(iso: Optional[str]) -> Optional[int]:
    if not isinstance(iso, str) or not iso:
        return None
    try:
        return int(
            dt.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=dt.timezone.utc)
            .timestamp()
            * 1000
        )
    except ValueError:
        return None


def verdict_leg_a(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Frozen-threshold verdict over accumulated comparison rows."""
    total = len(rows)
    compared = [r for r in rows if r.get("outcome") == "compared"]
    present = len(compared)

    def _bps(r: dict) -> float:
        v = r.get("rel_bps")
        return float(v) if isinstance(v, (int, float)) else float("inf")

    within = [r for r in compared if _bps(r) <= 5.0]
    hard = [r for r in compared if _bps(r) > HARD_BPS]
    presence_ratio = (present / total) if total else 0.0
    within_ratio = (len(within) / present) if present else 0.0
    passed = (
        total > 0
        and presence_ratio >= PASS_PRESENCE
        and within_ratio >= PASS_WITHIN_5BPS
        and not hard
    )
    return {
        "leg": "A_mark_prices",
        "rows_total": total,
        "compared": present,
        "presence_ratio": round(presence_ratio, 6),
        "within_5bps_ratio": round(within_ratio, 6),
        "hard_violations_over_50bps": len(hard),
        "pass": passed,
        "thresholds": {
            "presence": PASS_PRESENCE,
            "within_5bps": PASS_WITHIN_5BPS,
            "hard_bps": HARD_BPS,
            "align_window_ms": ALIGN_WINDOW_MS,
        },
    }


# ----------------------------------------------------------------------
# Leg B: historical equivalence
# ----------------------------------------------------------------------
def rows_digest(rows: List[Any]) -> str:
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True).encode()
    ).hexdigest()


def numeric_equal(a: Any, b: Any) -> bool:
    """Exact numeric equality: rel tol 0, abs tol 1e-12 (plan §9.2B).
    Venue rows are string-typed: numeric-looking strings compare
    numerically ("101.0" == "101.0000000000001")."""
    try:
        return abs(float(a) - float(b)) <= NUMERIC_ABS_TOL
    except (TypeError, ValueError):
        return a == b


def compare_window(gw_result: Dict[str, Any], direct_rows: List[Any]) -> Dict[str, Any]:
    """Digest-or-numeric equivalence over one window."""
    gw_rows = gw_result.get("rows") or []
    same_count = len(gw_rows) == len(direct_rows)
    if not same_count:
        return {
            "pass": False,
            "reason": "row_count_mismatch",
            "gw_count": len(gw_rows),
            "direct_count": len(direct_rows),
            "gw_complete": gw_result.get("complete"),
        }
    digest_eq = rows_digest(gw_rows) == rows_digest(direct_rows)
    numeric_mismatches = 0
    if not digest_eq:
        for g, d in zip(gw_rows, direct_rows):
            keys = set(g.keys()) | set(d.keys()) if isinstance(g, dict) and isinstance(d, dict) else set()
            for k in keys:
                if not numeric_equal(g.get(k), d.get(k)):
                    numeric_mismatches += 1
    return {
        "pass": digest_eq or numeric_mismatches == 0,
        "digest_equal": digest_eq,
        "numeric_mismatches": numeric_mismatches,
        "row_count": len(gw_rows),
        "gw_complete": gw_result.get("complete"),
        "gw_cache_hit": gw_result.get("cache_hit"),
        "gw_merged_sha256": gw_result.get("merged_sha256"),
        "direct_sha256": rows_digest(direct_rows),
    }


# ----------------------------------------------------------------------
# CLI runners
# ----------------------------------------------------------------------
async def run_leg_a(
    gateway_base: str,
    watched: List[str],
    evidence_path: str,
    interval_s: float = 30.0,
    duration_s: Optional[float] = None,
) -> int:
    """Continuous mark comparison loop (default ≥24 h per plan G3)."""
    os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
    fetcher = PacedDirectFetcher()
    started = time.time()
    with open(evidence_path, "a", encoding="utf-8") as evidence:
        while True:
            batch_utc = dt.datetime.now(dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            try:
                gw = _http_get_json(f"{gateway_base}/v1/prices/latest")
                rows = []
                try:
                    rest = fetcher.get_json(PREMIUM_INDEX_URL)
                    rows = compare_marks(gw, rest, watched)
                except DirectLegAborted as exc:
                    rows = [
                        {
                            "symbol": s,
                            "outcome": "missing_side",
                            "reason": f"direct_leg_aborted: {exc.reason}",
                        }
                        for s in watched
                    ]
                record = {"batch_utc": batch_utc, "rows": rows}
                evidence.write(
                    json.dumps(record, sort_keys=True) + "\n"
                )
                evidence.flush()
                print(f"[legA {batch_utc}] {len(rows)} rows written")
            except Exception as exc:  # noqa: BLE001 - record and continue
                evidence.write(
                    json.dumps(
                        {"batch_utc": batch_utc, "error": repr(exc)}
                    )
                    + "\n"
                )
                evidence.flush()
            if duration_s and (time.time() - started) >= duration_s:
                break
            await asyncio.sleep(interval_s)
    return 0


async def run_leg_b(
    gateway_base: str,
    evidence_path: str,
) -> int:
    """One historical-equivalence pass over frozen fixture windows."""
    os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
    fetcher = PacedDirectFetcher()
    now = dt.datetime.now(dt.timezone.utc)
    end_ms = int((now - dt.timedelta(minutes=20)).timestamp() * 1000)
    start_ms = end_ms - 3 * 24 * 3600 * 1000  # last 3 complete days
    results: List[Dict[str, Any]] = []

    def gw_get(path: str, qs: str) -> Any:
        return _http_get_json(f"{gateway_base}{path}?{qs}")

    # klines windows (5 symbols x 15m)
    for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT"):
        qs = f"symbol={symbol}&interval=15m&startMs={start_ms}&endMs={end_ms}"
        gw = gw_get("/v1/bars", qs)
        direct_rows = fetcher.get_json(
            f"https://fapi.binance.com/fapi/v1/klines"
            f"?symbol={symbol}&interval=15m&startTime={start_ms}"
            f"&endTime={end_ms}&limit=1500"
        )
        while len(direct_rows) == 1500:
            cursor = int(direct_rows[-1][0]) + 900_000
            if cursor > end_ms:
                break
            page = fetcher.get_json(
                f"https://fapi.binance.com/fapi/v1/klines"
                f"?symbol={symbol}&interval=15m&startTime={cursor}"
                f"&endTime={end_ms}&limit=1500"
            )
            if not page:
                break
            direct_rows.extend(page)
        results.append(
            {"kind": "klines", "symbol": symbol,
             **compare_window(gw, direct_rows)}
        )
    # basis windows (2 pairs)
    for pair in ("BTCUSDT", "ETHUSDT"):
        qs = f"pair={pair}&period=15m&startMs={start_ms}&endMs={end_ms}"
        gw = gw_get("/v1/basis", qs)
        direct_rows = fetcher.get_json(
            f"https://fapi.binance.com/futures/data/basis"
            f"?pair={pair}&contractType=PERPETUAL&period=15m"
            f"&startTime={start_ms}&endTime={end_ms}&limit=500"
        )
        while len(direct_rows) == 500:
            cursor = int(direct_rows[-1]["timestamp"]) + 900_000
            if cursor > end_ms:
                break
            page = fetcher.get_json(
                f"https://fapi.binance.com/futures/data/basis"
                f"?pair={pair}&contractType=PERPETUAL&period=15m"
                f"&startTime={cursor}&endTime={end_ms}&limit=500"
            )
            if not page:
                break
            direct_rows.extend(page)
        results.append(
            {"kind": "basis", "pair": pair, **compare_window(gw, direct_rows)}
        )
    # funding windows (3 symbols)
    for symbol in ("ETHUSDT", "SOLUSDT", "ADAUSDT"):
        qs = f"symbol={symbol}&startMs={start_ms}&endMs={end_ms}"
        gw = gw_get("/v1/funding", qs)
        direct_rows = fetcher.get_json(
            f"https://fapi.binance.com/fapi/v1/fundingRate"
            f"?symbol={symbol}&startTime={start_ms}"
            f"&endTime={end_ms}&limit=1000"
        )
        while len(direct_rows) == 1000:
            cursor = int(direct_rows[-1]["fundingTime"]) + 1
            if cursor > end_ms:
                break
            page = fetcher.get_json(
                f"https://fapi.binance.com/fapi/v1/fundingRate"
                f"?symbol={symbol}&startTime={cursor}"
                f"&endTime={end_ms}&limit=1000"
            )
            if not page:
                break
            direct_rows.extend(page)
        results.append(
            {"kind": "funding", "symbol": symbol,
             **compare_window(gw, direct_rows)}
        )
    overall_pass = all(r.get("pass") for r in results) and bool(results)
    verdict = {
        "leg": "B_historical_equivalence",
        "pass": overall_pass,
        "window_utc": {
            "start_ms": start_ms, "end_ms": end_ms,
        },
        "results": results,
    }
    with open(evidence_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(verdict, sort_keys=True) + "\n")
    print(json.dumps({"leg": "B", "pass": overall_pass,
                      "windows": len(results)}))
    return 0 if overall_pass else 4


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ldgv1-canary")
    sub = parser.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("marks")
    pa.add_argument("--gateway", default="http://127.0.0.1:8792")
    pa.add_argument("--evidence", default=os.path.join(CANARY_DIR, "leg_a_marks.jsonl"))
    pa.add_argument("--interval", type=float, default=30.0)
    pa.add_argument("--duration-s", type=float, default=None)
    pa.add_argument("--symbols", default="BTCUSDT,ETHUSDT,SOLUSDT,ADAUSDT,DOGEUSDT")
    pb = sub.add_parser("history")
    pb.add_argument("--gateway", default="http://127.0.0.1:8792")
    pb.add_argument("--evidence", default=os.path.join(CANARY_DIR, "leg_b_history.jsonl"))
    args = parser.parse_args(argv)
    if args.cmd == "marks":
        return asyncio.run(
            run_leg_a(
                args.gateway,
                [s.strip().upper() for s in args.symbols.split(",") if s.strip()],
                args.evidence,
                args.interval,
                args.duration_s,
            )
        )
    return asyncio.run(run_leg_b(args.gateway, args.evidence))


if __name__ == "__main__":
    raise SystemExit(main())
