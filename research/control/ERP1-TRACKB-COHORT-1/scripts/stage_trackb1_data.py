"""ERP1-TRACKB-COHORT-1 GO-1 data staging (bounded heavy job).

Stages, under the machine-wide heavy lock:
  1. BTCUSDT funding settlements: fapi /fapi/v1/fundingRate pagination
     (program precedent V8/V11/V14/CHR3F) 2020-06-01..2026-08-21, PLUS
     data.binance.vision monthly fundingRate zips as CROSS-CHECK only
     (exclusion-not-merge; pre-fapi-floor prefix excluded from scoring —
     PITDATA §1 law).
  2. Perp 1h klines: vision futures/um monthly klines 2020-01..2026-08.
  3. Spot 1h klines: vision spot monthly klines 2017-08..2026-08.
  4. Availability PROBES (fail-closed, no assumptions): bookTicker history
     for spot and um futures (COSTEXEC census input class — absent history
     => spread stays DECLARED+stress, never fabricated).
Outputs: raw bytes under data_local/ (untracked), sha256 manifests + gap
censuses committed. No PnL, no signal computation (ordering law: this is
data gate only).
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

VISION = "https://data.binance.vision"
FAPI = "https://fapi.binance.com"
SYMBOL = "BTCUSDT"
START_MS = int(datetime(2020, 6, 1, tzinfo=timezone.utc).timestamp() * 1000)
END_MS = int(datetime(2026, 8, 21, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)
PERP_KLINE_START = (2020, 1)
SPOT_KLINE_START = (2017, 8)
KLINE_END = (2026, 8)
SLEEP_S = 0.4
ROOT = Path(__file__).resolve().parents[4]  # .../integration
CYC = ROOT / "research/control/ERP1-TRACKB-COHORT-1"
DATA = CYC / "data_local"


def _get(url: str, timeout: float = 60.0) -> bytes:
    req = Request(url, headers={"User-Agent": "my-quantitative-trackb1-staging/1.0"})
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 fixed https hosts
        return resp.read()


def months(start: tuple[int, int], end: tuple[int, int]):
    y, m = start
    while (y, m) <= end:
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch_funding_fapi() -> list[dict]:
    rows, cursor = [], START_MS
    while cursor <= END_MS:
        url = f"{FAPI}/fapi/v1/fundingRate?symbol={SYMBOL}&startTime={cursor}&endTime={END_MS}&limit=1000"
        page = json.loads(_get(url))
        if not page:
            break
        rows.extend(page)
        nxt = int(page[-1]["fundingTime"]) + 1
        if nxt <= cursor:
            raise RuntimeError("funding pagination did not advance")
        cursor = nxt
        time.sleep(SLEEP_S)
    return rows


def download_zip(url: str) -> tuple[bytes, int] | None:
    try:
        raw = _get(url, timeout=120.0)
        return raw, len(raw)
    except Exception as exc:  # 404 etc — recorded, never guessed
        return None, str(exc)  # type: ignore[return-value]


def stage_channel(kind: str, months_iter, url_fn, out_dir: Path, manifest: dict):
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for tag in months_iter:
        url = url_fn(tag)
        raw, size = download_zip(url)
        if raw is None:
            files.append({"month": tag, "status": "ABSENT", "error": size})
            continue
        name = f"{kind}-{tag}.zip"
        (out_dir / name).write_bytes(raw)
        files.append({"month": tag, "status": "OK", "bytes": size,
                      "sha256": sha256(raw), "file": name})
        time.sleep(SLEEP_S)
    manifest[kind] = {"files": files,
                      "ok": sum(1 for f in files if f["status"] == "OK"),
                      "absent": sum(1 for f in files if f["status"] == "ABSENT")}


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from research.governance import heavy_lock

    expected = [str(CYC / "data_local/staging_manifest_v1.json")]
    cmd = [".venv/bin/python", str(Path(__file__))]
    with heavy_lock.acquire(cycle_id="ERP1-TRACKB-COHORT-1", role="go1-data-staging",
                            worktree=str(ROOT), command=cmd,
                            expected_artifacts=expected) as handle:
        manifest: dict = {"schema": "erp1_trackb1_staging_manifest@1",
                          "staged_utc": datetime.now(timezone.utc).isoformat(),
                          "symbol": SYMBOL, "sources": {}}

        # 1. funding fapi (authoritative settled series)
        funding = fetch_funding_fapi()
        fb = json.dumps({"requested_start_ms": START_MS, "requested_end_ms": END_MS,
                         "rows": funding}, sort_keys=True).encode()
        (DATA / "funding/BTCUSDT").mkdir(parents=True, exist_ok=True)
        (DATA / "funding/BTCUSDT/funding.json").write_bytes(fb)
        stamps = [int(r["fundingTime"]) for r in funding]
        manifest["sources"]["funding_fapi"] = {
            "rows": len(funding), "first": datetime.fromtimestamp(min(stamps)/1000, tz=timezone.utc).isoformat(),
            "last": datetime.fromtimestamp(max(stamps)/1000, tz=timezone.utc).isoformat(),
            "sha256": sha256(fb),
            "bundle_convention": "reports.funding._load_bundle compatible (requested_start_ms/end_ms/rows)",
        }
        handle.heartbeat(extra={"stage": "funding_fapi_done", "rows": len(funding)})

        # 2. vision funding zips (cross-check channel)
        stage_channel("funding_vision", months((2019, 9), (2026, 8)),
                      lambda t: f"{VISION}/data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{t}.zip",
                      DATA / "funding_vision", manifest["sources"])
        # 3. perp 1h klines
        stage_channel("perp_1h", months(PERP_KLINE_START, KLINE_END),
                      lambda t: f"{VISION}/data/futures/um/monthly/klines/{SYMBOL}/1h/{SYMBOL}-1h-{t}.zip",
                      DATA / "perp_1h", manifest["sources"])
        # 4. spot 1h klines
        stage_channel("spot_1h", months(SPOT_KLINE_START, KLINE_END),
                      lambda t: f"{VISION}/data/spot/monthly/klines/{SYMBOL}/1h/{SYMBOL}-1h-{t}.zip",
                      DATA / "spot_1h", manifest["sources"])

        # 5. availability probes (bookTicker history) — measured, fail-closed
        probes = {}
        for label, url in {
            "spot_bookTicker_recent": f"{VISION}/data/spot/monthly/bookTicker/{SYMBOL}/{SYMBOL}-bookTicker-2026-07.zip",
            "um_bookTicker_recent": f"{VISION}/data/futures/um/monthly/bookTicker/{SYMBOL}/{SYMBOL}-bookTicker-2026-07.zip",
            "spot_bookTicker_old": f"{VISION}/data/spot/monthly/bookTicker/{SYMBOL}/{SYMBOL}-bookTicker-2021-01.zip",
            "um_bookTicker_old": f"{VISION}/data/futures/um/monthly/bookTicker/{SYMBOL}/{SYMBOL}-bookTicker-2021-01.zip",
        }.items():
            raw, size = download_zip(url)
            probes[label] = ("PRESENT" if raw is not None else "ABSENT",
                             size if raw is not None else str(size))
        manifest["sources"]["bookTicker_probes"] = probes

        mb = json.dumps(manifest, sort_keys=True, indent=1).encode()
        (CYC / "data_local/staging_manifest_v1.json").write_bytes(mb)
        handle.heartbeat(extra={"stage": "manifest_written", "sha256": sha256(mb)})
        print(json.dumps({"manifest_sha256": sha256(mb),
                          "funding_rows": manifest["sources"]["funding_fapi"]["rows"],
                          "vision_funding_ok": manifest["sources"]["funding_vision"]["ok"],
                          "perp_1h_ok": manifest["sources"]["perp_1h"]["ok"],
                          "spot_1h_ok": manifest["sources"]["spot_1h"]["ok"],
                          "bookTicker_probes": probes}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
