#!/usr/bin/env python
"""PA4: per-channel canary re-probes (plan section 8 PA4, P-7 etiquette).

One polite request per channel (bounded, resumable, no retries storm):
- alive probe: the channel's real endpoint answers with expected content;
- dead probe: a bogus identifier/path is DISTINGUISHABLE (404/empty) --
  proving the channel can tell existence from absence.

Keyed channels (eodhd, fred-api) require a pre-existing env key
(<NAME>_API_KEY).  No key in env => NOT_RUN_NO_KEY (fail-closed downstream:
a series whose channel cannot be probed cannot GRANT).

Results are appended (resumable) to a JSONL and summarized to a gate
artifact.  Network access only; no purchases, no signups, no credential
logging.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

SCHEMA = "research_platform_v3_run/pa4_canary@1"
UA = ("my-quantitative-research/1.0 (evidence-first research; "
      "contact: local-operator@localhost)")
TIMEOUT = 30


def fetch(url: str, method: str = "GET") -> dict:
    req = urllib.request.Request(url, method=method,
                                 headers={"User-Agent": UA})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read(65536)
            return {"http_status": resp.status,
                    "bytes_head": len(body),
                    "body_sha256_64k": hashlib.sha256(body).hexdigest(),
                    "content_sample": body[:200].decode("utf-8", "replace"),
                    "seconds": round(time.time() - started, 2)}
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "seconds": round(time.time() - started, 2)}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}",
                "seconds": round(time.time() - started, 2)}


def probe_edgar() -> dict:
    # data.sec.gov is the SEC-declared machine-access endpoint and
    # requires a UA with contact info (SEC fair-access etiquette)
    alive = fetch("https://data.sec.gov/submissions/CIK0000320193.json")
    dead = fetch("https://data.sec.gov/submissions/CIK0000000000.json")
    alive_ok = alive.get("http_status") == 200
    dead_distinct = dead.get("http_status") in (404, 400)
    return {"channel": "edgar", "alive": alive, "dead": dead,
            "verdict": "PASS" if alive_ok and dead_distinct else "FAIL"}


def probe_binance_vision() -> dict:
    alive = fetch("https://data.binance.vision/?prefix=data/futures/um/"
                  "monthly/klines/BTCUSDT/")
    dead = fetch("https://data.binance.vision/?prefix=data/futures/um/"
                 "monthly/klines/BOGUSNOPE/")
    alive_ok = alive.get("http_status") == 200 and (
        "Binance" in alive.get("content_sample", ""))
    dead_distinct = dead.get("http_status") in (403, 404)
    return {"channel": "binance-vision", "alive": alive, "dead": dead,
            "verdict": "PASS" if alive_ok and dead_distinct else "FAIL"}


def probe_official(name: str, alive_url: str, dead_url: str,
                   alive_marker: str = "") -> dict:
    alive = fetch(alive_url)
    dead = fetch(dead_url)
    alive_ok = alive.get("http_status") == 200 and (
        alive_marker.lower() in alive.get("content_sample", "").lower()
        if alive_marker else True)
    dead_distinct = dead.get("http_status") in (403, 404, 410, 400)
    return {"channel": name, "alive": alive, "dead": dead,
            "verdict": "PASS" if alive_ok and dead_distinct else "FAIL"}


def probe_keyed(name: str, env_suffix: str, alive_url: str,
                dead_url: str) -> dict:
    key = os.environ.get(env_suffix, "")
    if not key:
        return {"channel": name, "verdict": "NOT_RUN_NO_KEY",
                "note": f"{env_suffix} absent from environment; "
                        "fail-closed downstream; no signup performed"}
    alive = fetch(alive_url.replace("<KEY>", key))
    dead = fetch(dead_url.replace("<KEY>", key))
    alive_ok = alive.get("http_status") == 200
    dead_distinct = (dead.get("http_status") != 200) or (
        '"code"' in dead.get("content_sample", "") or
        dead.get("content_sample", "").strip() in ("", "[]", "{}"))
    return {"channel": name, "alive": {"http_status": alive.get("http_status")},
            "dead": {"http_status": dead.get("http_status")},
            "verdict": "PASS" if alive_ok and dead_distinct else "FAIL"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--journal", required=True)
    args = ap.parse_args()

    probes = [
        probe_edgar(),
        probe_binance_vision(),
        probe_official(
            "ons", "https://www.ons.gov.uk/economy/inflationandpriceindices",
            "https://www.ons.gov.uk/no-such-page-xyz-404-check"),
        probe_official(
            "statcan",
            "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=18100004"
            "01",
            "https://www150.statcan.gc.ca/no-such-tbl-xyz"),
        probe_official(
            "abs", "https://www.abs.gov.au/statistics/economy/price-indexes"
                   "-and-inflation/consumer-price-index-australia/latest"
                   "-release",
            "https://www.abs.gov.au/no-such-release-xyz"),
        probe_official(
            "bis", "https://www.bis.org/statistics/",
            "https://www.bis.org/statistics/no-such-page-xyz"),
        probe_official(
            "ecb", "https://data.ecb.europa.eu/",
            "https://data.ecb.europa.eu/no-such-dataset-xyz"),
        probe_keyed(
            "eodhd", "EODHD_API_KEY",
            "https://eodhd.com/api/eod/AAPL.US?fmt=json&api_token=<KEY>",
            "https://eodhd.com/api/eod/ZZZZZZ.NOPE?fmt=json&api_token=<KEY>"),
        probe_keyed(
            "fred-api", "FRED_API_KEY",
            "https://api.stlouisfed.org/fred/series?series_id=CPIAUCSL"
            "&api_key=<KEY>&file_type=json",
            "https://api.stlouisfed.org/fred/series?series_id=NOPE1234"
            "&api_key=<KEY>&file_type=json"),
    ]

    with open(args.journal, "a", encoding="utf-8") as fh:
        for p in probes:
            fh.write(json.dumps(
                {"utc": datetime.now(timezone.utc).isoformat(), **p},
                sort_keys=True, default=str) + "\n")
        fh.flush()

    runnable = [p for p in probes
                if p["verdict"].startswith(("PASS", "FAIL"))]
    passed = sum(1 for p in runnable if p["verdict"] == "PASS")
    not_run = [p["channel"] for p in probes if p["verdict"] == "NOT_RUN_NO_KEY"]
    failed = [p["channel"] for p in runnable if p["verdict"] == "FAIL"]

    # network unavailability must be distinguished from channel failure:
    # every runnable probe erroring with a transport error (no HTTP status)
    # means the HOST could not reach the network at all
    transport_only = runnable and all(
        "error" in p.get("alive", {}) and "http_status" not in p.get("alive", {})
        for p in runnable)
    if transport_only:
        verdict = "NOT_RUN_NETWORK_UNAVAILABLE"
    elif failed:
        verdict = "FAIL"
    elif runnable:
        verdict = "PASS"
    else:
        verdict = "NOT_RUN"

    artifact = {
        "schema": SCHEMA,
        "gate": "V3-GA3",
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "channels_probed": [p["channel"] for p in probes],
        "passed": passed,
        "failed_channels": failed,
        "not_run_no_key": not_run,
        "probes": probes,
        "verdict": verdict,
    }
    with open(args.out, "w") as fh:
        json.dump(artifact, fh, indent=1)
    print(json.dumps({k: v for k, v in artifact.items() if k != "probes"},
                     indent=1))
    return 0 if artifact["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
