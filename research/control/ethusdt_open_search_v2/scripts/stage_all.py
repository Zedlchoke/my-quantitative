"""EOSV2 P1 stager — Binance Vision monthly zips for 4 series, deterministic.

Laws carried from probe_findings.md (measured 2026-09-24):
  - GET only (HEAD is 404-always);
  - pacing >= 2.0 s between requests;
  - on 404: backoff 1/2/4 s, then 60 s cooldown attempts, max 5;
  - a month is MISSING only after the 5th attempt, and every MISSING
    verdict is re-verified once after a 120 s quiet window at the end;
  - every downloaded byte sha256-pinned into the staged manifest.

Series (plan §2):
  um/klines     ETHUSDT 1h   2019-10..2026-08  (floor probe; 2019-11/12 warmup-only)
  um/fundingRate ETHUSDT     2019-11..2026-08  (measured funding cost authority)
  spot/klines   ETHBTC  1h   2019-05..2026-08  (lane E2 warmup needs 200d pre-2020)
  um/klines     BTCUSDT 1h   2019-09..2026-08  (lane E1 signal)

Idempotent: an existing valid zip (opens as zip, expected magic) is
reused (cached) and re-hashed, never re-downloaded.
"""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import sys
import time
import urllib.request
import zipfile

BASE = "https://data.binance.vision/data"
ROOT = pathlib.Path(__file__).resolve().parents[1]  # research/control/ethusdt_open_search_v1
DATA = ROOT / "data_local" / "vision"
PAUSE_S = 2.0
UA = "eosv2-stager/1.0"

SERIES = [
    ("klines_um_ETHUSDT_1h", "futures/um/monthly/klines/ETHUSDT/1h/ETHUSDT-1h-{ym}.zip", "2020-01", "2026-08"),
    ("fundingRate_um_ETHUSDT", "futures/um/monthly/fundingRate/ETHUSDT/ETHUSDT-fundingRate-{ym}.zip", "2020-01", "2026-08"),
    ("klines_um_BTCUSDT_1h", "futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{ym}.zip", "2020-01", "2026-08"),
    ("klines_um_SOLUSDT_1h", "futures/um/monthly/klines/SOLUSDT/1h/SOLUSDT-1h-{ym}.zip", "2019-10", "2026-08"),
    ("klines_um_BNBUSDT_1h", "futures/um/monthly/klines/BNBUSDT/1h/BNBUSDT-1h-{ym}.zip", "2019-10", "2026-08"),
    ("klines_um_XRPUSDT_1h", "futures/um/monthly/klines/XRPUSDT/1h/XRPUSDT-1h-{ym}.zip", "2019-10", "2026-08"),
    ("klines_um_ADAUSDT_1h", "futures/um/monthly/klines/ADAUSDT/1h/ADAUSDT-1h-{ym}.zip", "2019-10", "2026-08"),
]


def months(start: str, end: str) -> list[str]:
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def fetch(url: str) -> tuple[bytes | None, list[int]]:
    """GET with the preregistered retry law. Returns (body|None, statuses)."""
    delays = [0.0, 1.0, 2.0, 4.0, 60.0]  # 5 attempts, escalating, last after cooldown
    seen: list[int] = []
    for i, d in enumerate(delays):
        if d:
            time.sleep(d)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read(), seen + [r.status]
        except urllib.error.HTTPError as e:
            seen.append(e.code)
            if e.code != 404:
                return None, seen
        except Exception:
            seen.append(-1)
    return None, seen


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def valid_zip(b: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            return z.namelist() != [] and b[:4] == b"PK\x03\x04"
    except Exception:
        return False


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    manifest: dict = {
        "schema": "eos1.staged_manifest@1",
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stager": "scripts/stage_all.py",
        "retry_law": "GET; pacing>=2.0s; 404 backoff 1/2/4s + 60s cooldown, max 5 attempts; MISSING re-verified after 120s quiet",
        "series": {},
    }
    missing: list[tuple[str, str, str]] = []  # series, ym, url — for quiet re-verify
    for name, template, start, end in SERIES:
        rows: dict[str, dict] = {}
        for ym in months(start, end):
            url = f"{BASE}/{template.format(ym=ym)}"
            dest = DATA / name / f"{ym}.zip"
            entry: dict = {"url": url}
            if dest.exists():
                b = dest.read_bytes()
                if valid_zip(b):
                    entry.update(status="cached", sha256=sha256(b), bytes=len(b))
                    rows[ym] = entry
                    print(f"{name} {ym} cached ({len(b)}B)", flush=True)
                    continue
                dest.unlink()  # corrupt cache -> refetch
            body, statuses = fetch(url)
            time.sleep(PAUSE_S)
            if body is not None and valid_zip(body):
                dest.parent.mkdir(parents=True, exist_ok=True)
                tmp = dest.with_suffix(".tmp")
                tmp.write_bytes(body)
                tmp.rename(dest)
                entry.update(status="fetched", sha256=sha256(body), bytes=len(body), attempts=statuses)
                rows[ym] = entry
                print(f"{name} {ym} fetched ({len(body)}B, {statuses})", flush=True)
            else:
                entry.update(status="MISSING", attempts=statuses)
                rows[ym] = entry
                missing.append((name, ym, url))
                print(f"{name} {ym} MISSING ({statuses})", flush=True)
        manifest["series"][name] = rows

    if missing:
        print(f"quiet-window re-verify of {len(missing)} MISSING months after 120s...", flush=True)
        time.sleep(120.0)
        for name, ym, url in missing:
            body, statuses = fetch(url)
            time.sleep(PAUSE_S)
            if body is not None and valid_zip(body):
                dest = DATA / name / f"{ym}.zip"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(body)
                manifest["series"][name][ym].update(
                    status="fetched_on_reverify", sha256=sha256(body), bytes=len(body),
                    reverify_attempts=statuses)
                print(f"{name} {ym} fetched on re-verify ({statuses})", flush=True)
            else:
                manifest["series"][name][ym]["reverify_attempts"] = statuses
                print(f"{name} {ym} MISSING confirmed ({statuses})", flush=True)

    out = ROOT / "freezes" / "staged_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(f"manifest -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
