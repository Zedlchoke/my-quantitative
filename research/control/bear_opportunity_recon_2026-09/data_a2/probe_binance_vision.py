#!/usr/bin/env python
"""A2 probe of data.binance.vision — measured coverage, not assumed.

Light-job law: HEAD/Range probes + full GET only for files <= MAX_FULL bytes.
Total download budget < 200 MB (PSV1 section 19 exemption; heavy lock NOT acquired).
Output: data_inventory.json in this directory + funding_events.parquet for the
downtrend funding split (Task 3 input).

Read-only inputs referenced (never written):
  PSV1 manifest: .worktrees/phase-strategy-v1/integration/research/control/
                 phase_strategy_v1/lane_btc_h4/data/manifest.json
"""
from __future__ import annotations

import hashlib
import io
import json
import time
import urllib.error
import urllib.request
import zlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
MANIFEST = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                "integration/research/control/phase_strategy_v1/lane_btc_h4/data/manifest.json")
BASE_UM = "https://data.binance.vision/data/futures/um"
BASE_BM = "https://data.binance.vision/data/futures/bm"
MAX_FULL = 5_000_000        # full GET only below this many bytes
SAMPLE_BYTES = 262_144      # Range window for big files
SOCK_TIMEOUT = 25
POLITE_SLEEP = 0.12
DOWNLOAD_BUDGET = 200_000_000
_manifest = json.loads(MANIFEST.read_text())

STATE = {"bytes_downloaded": 0, "n_requests": 0}
NOW = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _req(url: str, rng: str | None = None, method: str = "GET"):
    STATE["n_requests"] += 1
    headers = {"User-Agent": "a2-recon-probe/1.0 (research; keyless)"}
    if rng:
        headers["Range"] = f"bytes={rng}"
    req = urllib.request.Request(url, headers=headers, method=method)
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=SOCK_TIMEOUT) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), b""
        except Exception as e:  # timeout / conn reset -> retry
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    return None, {"error": repr(last_err)}, b""


def head(url):
    s, h, _ = _req(url, method="HEAD")
    return s, h


def month_add(ym: str, k: int) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    t = (y * 12 + (m - 1)) + k
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


def fam_url(family: str, symbol: str, ym: str, iv: str | None = None) -> str:
    if iv:
        return f"{BASE_UM}/monthly/{family}/{symbol}/{iv}/{symbol}-{iv}-{ym}.zip"
    return f"{BASE_UM}/monthly/{family}/{symbol}/{symbol}-{family}-{ym}.zip"


def zip_rows(data: bytes, max_rows: int = 4) -> tuple[list[str], list[list[str]], int, str]:
    """Decode a Vision zip (CSV inside). Returns (header_or_first_row, rows, n_csv_bytes, zip_name)."""
    zf_bio = io.BytesIO(data)
    import zipfile
    with zipfile.ZipFile(zf_bio) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            raw = f.read()  # full-file decodes only (small files)
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    # Vision 2022+ CSVs carry a header row; pre-2022 are headerless.
    header = None
    body_start = 0
    first = lines[0].split(",") if lines else []
    if first and not _is_numeric_row(first):
        header = first
        body_start = 1
    rows = [ln.split(",") for ln in lines[body_start:body_start + max_rows]]
    return (header if header else first), rows, len(raw), name


def _is_numeric_row(cells: list[str]) -> bool:
    def num(c):
        try:
            float(c)
            return True
        except ValueError:
            return False
    return bool(cells) and num(cells[0])


def inflate_head(rng_bytes: bytes, max_out: int = 65536) -> bytes:
    """Range-sampled zip: parse local header, raw-inflate the head of entry 0."""
    if rng_bytes[:4] != b"PK\x03\x04":
        raise ValueError("not a zip local header")
    name_len = int.from_bytes(rng_bytes[26:28], "little")
    extra_len = int.from_bytes(rng_bytes[28:30], "little")
    method = int.from_bytes(rng_bytes[8:10], "little")
    off = 30 + name_len + extra_len
    payload = rng_bytes[off:]
    if method == 8:
        d = zlib.decompressobj(-15)
        return d.decompress(payload, max_out)
    return payload[:max_out]  # stored


def sample_head_lines(data_head: bytes, max_rows: int = 3):
    text = data_head.decode("utf-8", errors="replace")
    lines = text.splitlines()
    header = None
    body_start = 0
    first = lines[0].split(",") if lines else []
    if first and not _is_numeric_row(first):
        header = first
        body_start = 1
    rows = [ln.split(",") for ln in lines[body_start:body_start + max_rows]]
    return (header if header else first), rows


def probe_first_last(family: str, symbol: str = "BTCUSDT", iv: str | None = None,
                     hard_floor: str = "2017-01"):
    """TRUE first month (walk back from first candidate hit) and last (walk fwd)."""
    candidates = ["2019-09", "2019-12", "2020-01", "2020-06", "2021-01",
                  "2021-06", "2021-12", "2022-01", "2026-06", "2026-07", "2026-08", "2026-09"]
    observed = {}
    for ym in candidates:
        url = fam_url(family, symbol, ym, iv)
        s, h = head(url)
        n = int(h.get("Content-Length") or 0) if s == 200 else None
        observed[ym] = {"status": s, "bytes": n}
        time.sleep(POLITE_SLEEP)
    hits = [ym for ym in candidates if observed[ym]["status"] == 200 and (observed[ym]["bytes"] or 0) > 0]
    empty = [ym for ym in candidates if observed[ym]["status"] == 200 and (observed[ym]["bytes"] or 0) == 0]
    out = {"candidate_probes": observed, "empty_200": empty}
    if not hits:
        out.update({"first_month": None, "last_month": None, "method": "no candidate hit"})
        return out
    # walk back from earliest hit
    first_hit = min(hits)
    ym = first_hit
    last_miss = None
    while ym > hard_floor:
        prev = month_add(ym, -1)
        s, h = head(fam_url(family, symbol, prev, iv))
        ok = s == 200 and int(h.get("Content-Length") or 0) > 0
        observed[prev] = {"status": s, "bytes": int(h.get("Content-Length") or 0) if s == 200 else None}
        if not ok:
            last_miss = prev
            break
        ym = prev
        time.sleep(POLITE_SLEEP)
    out["first_month"] = month_add(last_miss, 1) if last_miss else (hard_floor if ym == hard_floor else ym)
    # walk forward from latest hit
    last_hit = max(hits)
    ym = last_hit
    last_ok = last_hit
    for _ in range(12):
        nxt = month_add(ym, 1)
        if nxt > "2026-09":
            break
        s, h = head(fam_url(family, symbol, nxt, iv))
        observed[nxt] = {"status": s, "bytes": int(h.get("Content-Length") or 0) if s == 200 else None}
        if s == 200 and int(h.get("Content-Length") or 0) > 0:
            last_ok = nxt
            ym = nxt
        else:
            break
        time.sleep(POLITE_SLEEP)
    out["last_month"] = last_ok
    out["method"] = "candidate probe + monthly walk to first miss (both ends)"
    return out


def fetch_sample(family: str, symbol: str, ym: str, iv: str | None = None):
    """Full GET if small, else Range-sample the head. Returns dict."""
    url = fam_url(family, symbol, ym, iv)
    s, h = head(url)
    total = int(h.get("Content-Length") or 0)
    rec = {"url": url, "http_status_head": s, "bytes_total": total,
           "last_modified": h.get("Last-Modified"), "etag": h.get("ETag"),
           "retrieved_time_utc": NOW(), "mode": None, "sha256": None,
           "sha256_scope": None}
    if s != 200 or total <= 0:
        rec["mode"] = "unavailable"
        return rec
    if STATE["bytes_downloaded"] + total <= DOWNLOAD_BUDGET and total <= MAX_FULL:
        s2, h2, data = _req(url)
        STATE["bytes_downloaded"] += len(data)
        rec.update({"mode": "full", "http_status_get": s2,
                    "sha256": hashlib.sha256(data).hexdigest(), "sha256_scope": "full file"})
        rec["_data"] = data
    else:
        s2, h2, data = _req(url, rng=f"0-{SAMPLE_BYTES - 1}")
        STATE["bytes_downloaded"] += len(data)
        rec.update({"mode": "range_head", "http_status_get": s2,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "sha256_scope": f"first {len(data)} bytes (partial, not file digest)"})
        rec["_data"] = data
    return rec


def decode_sample(family: str, ym: str, iv: str, rec: dict):
    """Fields + granularity from a fetched sample."""
    data = rec.get("_data")
    if not data:
        return {}
    out = {}
    try:
        if rec["mode"] == "full":
            header, rows, nbytes, zname = zip_rows(data)
        else:
            head_csv = inflate_head(data)
            header, rows = sample_head_lines(head_csv)
            nbytes = None
        out["fields"] = header
        out["sample_rows"] = rows[:3]
        out["csv_header_row_present"] = (header is not None and not _is_numeric_row(header))
        # granularity: first-col timestamps of the first two rows
        if len(rows) >= 2:
            try:
                t0, t1 = float(rows[0][0]), float(rows[1][0])
                out["granularity_seconds_observed"] = t1 - t0
                out["first_event_time_utc"] = datetime.fromtimestamp(
                    t0 / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                out["granularity_seconds_observed"] = None
    except Exception as e:
        out["decode_error"] = repr(e)
    return out


def main():
    inventory: dict = {"schema": "a2_data_inventory@1",
                       "probe_started_utc": NOW(),
                       "base": {"um_monthly": BASE_UM + "/monthly", "um_daily": BASE_UM + "/daily",
                                "bm_monthly": BASE_BM + "/monthly"},
                       "manifest_cross_ref": {
                           "path": str(MANIFEST),
                           "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
                           "psv1_first_month": _manifest["first_month"],
                           "psv1_last_complete_month": _manifest["last_complete_month"],
                           "psv1_retrieved_at": _manifest["retrieved_at"],
                           "psv1_pit_disclosure": _manifest["pit_disclosure"]},
                       "sources": {}}

    # ---- 1. interval discovery for Klines families -------------------------
    intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"]
    interval_scan = {}
    for fam in ["klines", "markPriceKlines", "indexPriceKlines", "premiumIndexKlines"]:
        found = []
        for iv in intervals:
            s, h = head(f"{BASE_UM}/monthly/{fam}/BTCUSDT/{iv}/BTCUSDT-{iv}-2024-06.zip")
            if s == 200:
                found.append({"interval": iv, "bytes": int(h.get("Content-Length") or 0),
                              "last_modified": h.get("Last-Modified")})
            time.sleep(POLITE_SLEEP)
        interval_scan[fam] = found
    inventory["interval_scan_2024_06"] = interval_scan

    # ---- 2. coverage measurement ------------------------------------------
    coverage_targets = [
        ("klines", "1h"), ("klines", "4h"),
        ("markPriceKlines", "1h"), ("markPriceKlines", "1m"),
        ("indexPriceKlines", "1h"), ("premiumIndexKlines", "1h"),
        ("fundingRate", None), ("metrics", None),
        ("bookTicker", None), ("bookDepth", None), ("liquidationSnapshot", None),
    ]
    for fam, iv in coverage_targets:
        key = f"{fam}:{iv}" if iv else fam
        print(f"[coverage] {key} ...", flush=True)
        cov = probe_first_last(fam, iv=iv)
        inventory["sources"].setdefault(key, {})["coverage"] = cov

    # ---- 3. sample decode ---------------------------------------------------
    samples = [
        ("klines:1h", "klines", "1h", "2020-01"),   # manifest cross-check file
        ("klines:4h", "klines", "4h", "2024-06"),
        ("klines:4h", "klines", "4h", "2020-01"),
        ("markPriceKlines:1h", "markPriceKlines", "1h", "2024-06"),
        ("markPriceKlines:1m", "markPriceKlines", "1m", "2024-06"),
        ("indexPriceKlines:1h", "indexPriceKlines", "1h", "2024-06"),
        ("premiumIndexKlines:1h", "premiumIndexKlines", "1h", "2024-06"),
        ("fundingRate", "fundingRate", None, "2024-06"),
        ("fundingRate", "fundingRate", None, "2020-01"),
        ("metrics", "metrics", None, "2024-06"),
        ("bookTicker", "bookTicker", None, "2024-06"),
        ("bookDepth", "bookDepth", None, "2024-06"),
    ]
    for key, fam, iv, ym in samples:
        print(f"[sample] {key} {ym} ...", flush=True)
        rec = fetch_sample(fam, "BTCUSDT", ym, iv)
        dec = decode_sample(fam, ym, iv, rec)
        rec.pop("_data", None)
        tgt = inventory["sources"].setdefault(key, {})
        tgt.setdefault("samples", []).append({"ym": ym, **rec, **dec})

    # ---- 4. determinism: re-download one sample twice ----------------------
    print("[determinism] ...", flush=True)
    det = {}
    for fam, iv, ym in [("fundingRate", None, "2024-06"), ("klines", "1h", "2020-01")]:
        url = fam_url(fam, "BTCUSDT", ym, iv)
        s1, h1, d1 = _req(url)
        STATE["bytes_downloaded"] += len(d1)
        s2, h2, d2 = _req(url)
        STATE["bytes_downloaded"] += len(d2)
        key = f"{fam}:{iv}" if iv else fam
        det[key] = {
            "url": url, "download1_sha256": hashlib.sha256(d1).hexdigest(),
            "download2_sha256": hashlib.sha256(d2).hexdigest(),
            "byte_identical": d1 == d2, "bytes": len(d1),
            "etag1": h1.get("ETag"), "etag2": h2.get("ETag"),
            "retrieved_time_utc": NOW()}
    # cross-check vs frozen manifest sha for 1h 2020-01
    mf = next(f for f in _manifest["files"]
              if f["kind"] == "1h_monthly" and f["period"] == "2020-01")
    det["klines:1h"]["manifest_sha256_2020_01"] = mf["sha256"]
    det["klines:1h"]["matches_frozen_manifest"] = (
        det["klines:1h"]["download1_sha256"] == mf["sha256"])
    inventory["deterministic_reretrieval"] = det

    # ---- 5. daily tails ----------------------------------------------------
    daily = {}
    for url in [
        f"{BASE_UM}/daily/klines/BTCUSDT/4h/BTCUSDT-4h-2026-09-22.zip",
        f"{BASE_UM}/daily/klines/BTCUSDT/4h/BTCUSDT-4h-2026-09-23.zip",
        f"{BASE_UM}/daily/klines/BTCUSDT/1h/BTCUSDT-1h-2026-09-22.zip",
        f"{BASE_UM}/daily/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2026-09-22.zip",
        f"{BASE_UM}/daily/metrics/BTCUSDT/BTCUSDT-metrics-2026-09-22.zip",
        f"{BASE_UM}/daily/bookTicker/BTCUSDT/BTCUSDT-bookTicker-2026-09-22.zip",
        f"{BASE_UM}/daily/liquidationSnapshot/BTCUSDT/BTCUSDT-liquidationSnapshot-2026-09-22.zip",
    ]:
        s, h = head(url)
        daily[url] = {"status": s, "bytes": int(h.get("Content-Length") or 0) if s == 200 else None,
                      "last_modified": h.get("Last-Modified")}
        time.sleep(POLITE_SLEEP)
    inventory["daily_tail_2026_09"] = daily

    # ---- 6. liquidationSnapshot completeness -------------------------------
    print("[liquidationSnapshot walk] ...", flush=True)
    liq = inventory["sources"]["liquidationSnapshot"]["coverage"]
    months = []
    if liq.get("first_month") and liq.get("last_month"):
        ym = liq["first_month"]
        while ym <= liq["last_month"]:
            s, h = head(fam_url("liquidationSnapshot", "BTCUSDT", ym))
            months.append({"ym": ym, "status": s,
                           "bytes": int(h.get("Content-Length") or 0) if s == 200 else None,
                           "last_modified": h.get("Last-Modified")})
            ym = month_add(ym, 1)
            time.sleep(POLITE_SLEEP)
    # decode every liq month (small files) for row counts + time span
    for m in months:
        if m["status"] == 200 and m["bytes"] and m["bytes"] <= MAX_FULL:
            s, h, data = _req(fam_url("liquidationSnapshot", "BTCUSDT", m["ym"]))
            STATE["bytes_downloaded"] += len(data)
            m["sha256"] = hashlib.sha256(data).hexdigest()
            try:
                import zipfile
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    with z.open(z.namelist()[0]) as f:
                        raw = f.read().decode("utf-8", errors="replace")
                ln = raw.splitlines()
                hdr_present = not _is_numeric_row(ln[0].split(","))
                body = ln[1:] if hdr_present else ln
                m["fields"] = ln[0].split(",") if hdr_present else "headerless"
                m["rows"] = len(body)
                ts = [float(r.split(",")[-1]) for r in body if r.strip()]
                if ts:
                    m["first_event_utc"] = datetime.fromtimestamp(min(ts) / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    m["last_event_utc"] = datetime.fromtimestamp(max(ts) / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                m["decode_error"] = repr(e)
        time.sleep(POLITE_SLEEP)
    inventory["sources"]["liquidationSnapshot"]["monthly_detail"] = months
    # bm liquidationSnapshot quick probe
    bmlq = {}
    for ym in ["2020-01", "2021-06", "2022-01", "2024-06"]:
        s, h = head(f"{BASE_BM}/monthly/liquidationSnapshot/BTCUSDT/BTCUSDT-liquidationSnapshot-{ym}.zip")
        bmlq[ym] = {"status": s, "bytes": int(h.get("Content-Length") or 0) if s == 200 else None}
        time.sleep(POLITE_SLEEP)
    inventory["bm_liquidationSnapshot_probe"] = bmlq
    # bm klines existence (record only)
    s, h = head(f"{BASE_BM}/monthly/klines/BTCUSDT/4h/BTCUSDT-4h-2020-01.zip")
    inventory["bm_klines_4h_2020_01_probe"] = {"status": s,
                                               "bytes": int(h.get("Content-Length") or 0) if s == 200 else None}

    # ---- 7. REST fapi cross-checks -----------------------------------------
    print("[REST fapi] ...", flush=True)
    rest = {}
    FAPI = "https://fapi.binance.com"
    try:
        s, h, data = _req(f"{FAPI}/fapi/v1/time")
        rest["server_time"] = {"status": s, "body": data.decode()[:200]}
    except Exception as e:
        rest["server_time"] = {"error": repr(e)}
    time.sleep(1)

    def jget(url):
        s, h, data = _req(url)
        try:
            return s, json.loads(data.decode())
        except Exception:
            return s, data.decode()[:300]

    s, body = jget(f"{FAPI}/futures/data/openInterestHist?symbol=BTCUSDT&period=5m&limit=500")
    if isinstance(body, list) and body:
        rest["openInterestHist_5m_limit500_nostart"] = {
            "status": s, "n": len(body),
            "first_time": body[0].get("timestamp"), "last_time": body[-1].get("timestamp"),
            "fields": list(body[0].keys())}
    time.sleep(1)
    s, body = jget(f"{FAPI}/futures/data/openInterestHist?symbol=BTCUSDT&period=5m&limit=500&startTime=1577836800000")
    rest["openInterestHist_5m_startTime_2020_01_01"] = {
        "status": s,
        "n": len(body) if isinstance(body, list) else body,
        "first_time": body[0].get("timestamp") if isinstance(body, list) and body else None,
        "last_time": body[-1].get("timestamp") if isinstance(body, list) and body else None}
    time.sleep(1)
    s, body = jget(f"{FAPI}/futures/data/openInterestHist?symbol=BTCUSDT&period=1h&limit=500&startTime=1577836800000")
    rest["openInterestHist_1h_startTime_2020_01_01"] = {
        "status": s,
        "n": len(body) if isinstance(body, list) else body,
        "first_time": body[0].get("timestamp") if isinstance(body, list) and body else None}
    time.sleep(1)
    s, body = jget(f"{FAPI}/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=0&limit=5")
    rest["fundingRate_rest_startTime0_limit5"] = {
        "status": s,
        "n": len(body) if isinstance(body, list) else body,
        "first_time": body[0].get("fundingTime") if isinstance(body, list) and body else None,
        "fields": list(body[0].keys()) if isinstance(body, list) and body else None}
    inventory["rest_fapi"] = rest

    inventory["probe_finished_utc"] = NOW()
    inventory["bytes_downloaded_total"] = STATE["bytes_downloaded"]
    inventory["n_http_requests"] = STATE["n_requests"]

    out = HERE / "data_inventory.json"
    out.write_text(json.dumps(inventory, indent=2, default=str))
    print(f"WROTE {out}  bytes={STATE['bytes_downloaded']} reqs={STATE['n_requests']}")


if __name__ == "__main__":
    main()
