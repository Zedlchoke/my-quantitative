"""A9-F T1: per-symbol availability re-verification probes (V14 D2).

Discharges discrepancy D1 (per-symbol depth re-verification for all 19 ranked
names; P2 probed only BTC/ETH/SOL/XRP) and re-keys D2 (indexPriceKlines
requires pair=) and D3 (basis route point anchors only, no backward walk).

Keyless public GETs against https://fapi.binance.com only; >= 0.5s sleep
between calls; every response archived as one compact JSON under evidence/
(url, params, utc, http status, first/last row stamps).  Total request count
is printed at the end; the design is ~19 symbols x (3 kline routes x 4
anchors + 4 basis spot checks) ~= 304 requests.

No PnL, no positions, no selection or novelty opinions.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://fapi.binance.com"
HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)

SLEEP_SECONDS = 0.55

# 19 ranked names = staged REQUIRED_SYMBOLS minus BTCUSDT (frozen benchmark).
UNIVERSE = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "DOGEUSDT", "ENAUSDT",
    "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT", "SOLUSDT",
    "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
]

MS = 1000
# Frozen instants (UTC).
T_LISTING_PROBE = "2019-01-01T00:00:00Z"   # earliest-retrievable probe floor
T_AUTHORIZED_START = "2024-08-20T00:00:00Z"  # authorized window start
T_STAGING_EARLIEST = "2025-06-30T00:00:00Z"  # 56d before first stamp
T_SCREEN_END_LAST_BUCKET = "2026-08-21T23:45:00Z"  # last 15m bucket of screen
T_SCREEN_START = "2025-08-22T00:00:00Z"    # basis-route spot check


def iso_to_ms(iso: str) -> int:
    dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp()) * MS


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


ANCHORS = {
    "earliest_retrievable": (T_LISTING_PROBE, None),
    "authorized_start_2024_08_20": (T_AUTHORIZED_START, T_AUTHORIZED_START),
    "staging_earliest_2025_06_30": (T_STAGING_EARLIEST, T_STAGING_EARLIEST),
    "screen_end_last_bucket_2026_08_21": (T_SCREEN_END_LAST_BUCKET, T_SCREEN_END_LAST_BUCKET),
}

BASIS_ANCHORS = {
    "authorized_start_2024_08_20": T_AUTHORIZED_START,
    "screen_start_2025_08_22": T_SCREEN_START,
    "staging_earliest_2025_06_30": T_STAGING_EARLIEST,
    "screen_end_2026_08_21": T_SCREEN_END_LAST_BUCKET,
}

KLINE_ROUTES = [
    ("premiumIndexKlines", "/fapi/v1/premiumIndexKlines", "symbol"),
    ("markPriceKlines", "/fapi/v1/markPriceKlines", "symbol"),
    ("indexPriceKlines_pair", "/fapi/v1/indexPriceKlines", "pair"),  # D2: pair=
]

_counter = {"n": 0}


def probe_get(path: str, params: dict, label: str) -> dict:
    """One keyless GET; archive a compact evidence JSON; return the record."""
    _counter["n"] += 1
    probe_id = f"d2probe_{_counter['n']:04d}"
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    rec: dict = {
        "probe_id": probe_id,
        "label": label,
        "url": url,
        "params": params,
        "utc": utc_now_iso(),
    }
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research-probe)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:  # noqa: PERF203
        status = exc.code
        body = exc.read().decode("utf-8", errors="replace")
    except Exception as exc:  # transport-level failure
        rec.update({"http_status": None, "error": f"{type(exc).__name__}: {exc}"})
        _write(rec)
        time.sleep(SLEEP_SECONDS)
        return rec
    rec["http_status"] = status
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = None
        rec["body_head"] = body[:200]
    rows = payload if isinstance(payload, list) else None
    rec["row_count"] = len(rows) if rows is not None else None
    if rows:
        first, last = rows[0], rows[-1]
        open_idx = 0
        rec["first_row"] = first
        rec["last_row"] = last
        for key, getter in (
            ("first_row_open_utc", lambda r: r[open_idx]),
            ("last_row_open_utc", lambda r: r[open_idx]),
        ):
            try:
                val = int(getter(first if key.startswith("first") else last))
                rec[key] = datetime.fromtimestamp(val / MS, tz=timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            except Exception:
                rec[key] = None
        if isinstance(first, dict) and "timestamp" in first:
            try:
                ts = int(first["timestamp"])
                rec["first_row_open_utc"] = datetime.fromtimestamp(
                    ts / MS, tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass
            if isinstance(last, dict) and "timestamp" in last:
                try:
                    ts = int(last["timestamp"])
                    rec["last_row_open_utc"] = datetime.fromtimestamp(
                        ts / MS, tz=timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")
                except Exception:
                    pass
    _write(rec)
    time.sleep(SLEEP_SECONDS)
    return rec


def _write(rec: dict) -> None:
    target = EVIDENCE / f"{rec['probe_id']}.json"
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(rec, handle, indent=1, sort_keys=True)
        handle.write("\n")


def main() -> None:
    summary: list[dict] = []
    for sym in UNIVERSE:
        for route_name, path, param_key in KLINE_ROUTES:
            for anchor_name, (start_iso, end_iso) in ANCHORS.items():
                params = {
                    param_key: sym,
                    "interval": "15m",
                    "limit": 1,
                    "startTime": iso_to_ms(start_iso),
                }
                if end_iso is not None:
                    params["endTime"] = iso_to_ms(end_iso) + 899_999  # inclusive open bucket
                rec = probe_get(path, params, f"{route_name}|{sym}|{anchor_name}")
                summary.append(
                    {
                        "probe_id": rec["probe_id"],
                        "route": route_name,
                        "symbol": sym,
                        "anchor": anchor_name,
                        "http_status": rec.get("http_status"),
                        "row_count": rec.get("row_count"),
                        "first_row_open_utc": rec.get("first_row_open_utc"),
                        "last_row_open_utc": rec.get("last_row_open_utc"),
                    }
                )
        # /futures/data/basis spot checks (D3: point anchors only).
        for anchor_name, iso in BASIS_ANCHORS.items():
            params = {
                "pair": sym,
                "contractType": "PERPETUAL",
                "period": "15m",
                "limit": 1,
                "startTime": iso_to_ms(iso),
                "endTime": iso_to_ms(iso) + 899_999,
            }
            rec = probe_get("/futures/data/basis", params, f"basis_futures_data|{sym}|{anchor_name}")
            summary.append(
                {
                    "probe_id": rec["probe_id"],
                    "route": "basis_futures_data",
                    "symbol": sym,
                    "anchor": anchor_name,
                    "http_status": rec.get("http_status"),
                    "row_count": rec.get("row_count"),
                    "first_row_open_utc": rec.get("first_row_open_utc"),
                    "last_row_open_utc": rec.get("last_row_open_utc"),
                    "basis_row": rec.get("first_row") if isinstance(rec.get("first_row"), dict) else None,
                }
            )
        print(f"[{utc_now_iso()}] {sym}: probes complete (cumulative={_counter['n']})", flush=True)

    out = {
        "schema": "v14_d2_a9f_probe_summary_v1",
        "cycle": "CRYPTO-V14",
        "producer_role": "A9-F",
        "generated_utc": utc_now_iso(),
        "base_url": BASE,
        "keyless": True,
        "sleep_seconds": SLEEP_SECONDS,
        "universe": UNIVERSE,
        "discrepancies_honored": {
            "D1": "per-symbol depth re-verification on all 19 ranked names",
            "D2": "indexPriceKlines probes use pair= (symbol= disconfirmed by P2)",
            "D3": "basis route probed by point anchors only (no backward walk)",
        },
        "total_requests": _counter["n"],
        "probes": summary,
    }
    with open(HERE / "probe_summary.json", "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(f"TOTAL REQUESTS: {_counter['n']}")


if __name__ == "__main__":
    main()
