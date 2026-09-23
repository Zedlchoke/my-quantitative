#!/usr/bin/env python
"""A2 probe #2 — authoritative S3 listing of data.binance.vision (keyless
ListObjectsV2 on s3-ap-northeast-1.amazonaws.com/data.binance.vision).

Corrects the URL-pattern assumptions of probe #1 with the bucket's own key
listing: true first/last keys per family/symbol, paginated. No file bodies
except a few small sample decodes. Output: s3_structure.json next to this file.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
REST_FAPI = "https://fapi.binance.com"
NOW = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def s3list(prefix: str, delim: str = "/", marker: str | None = None, maxkeys: int = 1000):
    params = {"delimiter": delim, "prefix": prefix, "max-keys": str(maxkeys)}
    if marker:
        params["marker"] = marker
    url = f"{S3}?{urllib.parse.urlencode(params)}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read().decode()
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"s3list failed {prefix}")


def list_all_keys(prefix: str, keep_pattern: str = r"\.zip$") -> dict:
    """Paginate ListObjectsV2 (delimiter='/') collecting .zip keys (+counts)."""
    keys, marker, truncated, pages = [], None, True, 0
    while truncated and pages < 100:
        xml = s3list(prefix, "/", marker)
        keys += re.findall(r"<Key>([^<]*)</Key>", xml)
        truncated = "<IsTruncated>true</IsTruncated>" in xml
        if truncated:
            marker = keys[-1]
        pages += 1
        time.sleep(0.1)
    zips = [k for k in keys if re.search(keep_pattern, k)]
    return {"n_keys_total": len(keys), "n_zip": len(zips), "pages": pages,
            "first_key": zips[0] if zips else None,
            "last_key": zips[-1] if zips else None,
            "zip_keys": zips}


def head(url):
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "a2-recon-probe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers)
    except Exception as e:
        return None, {"error": repr(e)}


def range_get(url, n=262144):
    req = urllib.request.Request(url, headers={"Range": f"bytes=0-{n-1}",
                                               "User-Agent": "a2-recon-probe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), b""


def month_of(key):
    m = re.search(r"(\d{4}-\d{2})\.zip$", key)
    return m.group(1) if m else None


def day_of(key):
    m = re.search(r"(\d{4}-\d{2}-\d{2})\.zip$", key)
    return m.group(1) if m else None


def inflate_head(rng_bytes: bytes, max_out: int = 65536) -> bytes:
    if rng_bytes[:4] != b"PK\x03\x04":
        raise ValueError("not a zip local header")
    name_len = int.from_bytes(rng_bytes[26:28], "little")
    extra_len = int.from_bytes(rng_bytes[28:30], "little")
    method = int.from_bytes(rng_bytes[8:10], "little")
    payload = rng_bytes[30 + name_len + extra_len:]
    if method == 8:
        d = zlib.decompressobj(-15)
        return d.decompress(payload, max_out)
    return payload[:max_out]


def head_lines(csv_bytes, max_rows=3):
    lines = csv_bytes.decode("utf-8", errors="replace").splitlines()
    def numeric(cells):
        try:
            float(cells[0]); return True
        except Exception:
            return False
    hdr, start = None, 0
    if lines and not numeric(lines[0].split(",")):
        hdr = lines[0].split(","); start = 1
    rows = [ln.split(",") for ln in lines[start:start + max_rows]]
    return hdr if hdr else (lines[0].split(",") if lines else []), rows


def main():
    out = {"schema": "a2_s3_structure@1", "probed_utc": NOW(),
           "bucket": "data.binance.vision (public keyless ListObjectsV2)"}

    # roots (authoritative family inventory)
    def prefixes_at(prefix):
        xml = s3list(prefix, "/")
        ps = re.findall(r"<Prefix>([^<]*)</Prefix>", xml)
        return [p for p in ps if p != prefix]
    out["root_futures"] = prefixes_at("data/futures/")
    out["um_families_monthly"] = [p.split("/")[-2] for p in prefixes_at("data/futures/um/monthly/")]
    out["um_families_daily"] = [p.split("/")[-2] for p in prefixes_at("data/futures/um/daily/")]
    out["cm_families_monthly"] = [p.split("/")[-2] for p in prefixes_at("data/futures/cm/monthly/")]
    out["cm_families_daily"] = [p.split("/")[-2] for p in prefixes_at("data/futures/cm/daily/")]
    out["note_bm"] = "prefix 'bm' does NOT exist in the bucket root; COIN-M is 'cm'"

    targets = {
        # monthly families (BTCUSDT)
        "fundingRate_monthly": "data/futures/um/monthly/fundingRate/BTCUSDT/",
        "klines_4h_monthly": "data/futures/um/monthly/klines/BTCUSDT/4h/",
        "klines_1h_monthly": "data/futures/um/monthly/klines/BTCUSDT/1h/",
        "klines_1m_monthly": "data/futures/um/monthly/klines/BTCUSDT/1m/",
        "markPriceKlines_1m_monthly": "data/futures/um/monthly/markPriceKlines/BTCUSDT/1m/",
        "markPriceKlines_1h_monthly": "data/futures/um/monthly/markPriceKlines/BTCUSDT/1h/",
        "indexPriceKlines_1h_monthly": "data/futures/um/monthly/indexPriceKlines/BTCUSDT/1h/",
        "premiumIndexKlines_1h_monthly": "data/futures/um/monthly/premiumIndexKlines/BTCUSDT/1h/",
        "bookTicker_monthly": "data/futures/um/monthly/bookTicker/BTCUSDT/",
        # daily families (BTCUSDT)
        "klines_4h_daily": "data/futures/um/daily/klines/BTCUSDT/4h/",
        "bookTicker_daily": "data/futures/um/daily/bookTicker/BTCUSDT/",
        "bookDepth_daily": "data/futures/um/daily/bookDepth/BTCUSDT/",
        "metrics_daily": "data/futures/um/daily/metrics/BTCUSDT/",
    }
    out["families"] = {}
    for name, prefix in targets.items():
        r = list_all_keys(prefix)
        r["first_month_or_day"] = month_of(r["first_key"]) or day_of(r["first_key"])
        r["last_month_or_day"] = month_of(r["last_key"]) or day_of(r["last_key"])
        r["prefix"] = prefix
        out["families"][name] = r
        print(f"[list] {name}: n={r['n_zip']} {r['first_month_or_day']} .. {r['last_month_or_day']}", flush=True)

    # liquidationSnapshot: direct legacy-path HEADs (prefix absent from listing)
    liq = {"listing_verdict": "no liquidationSnapshot prefix under um/ or cm/ (monthly or daily)"}
    for base in ["data/futures/um/monthly/liquidationSnapshot/BTCUSDT/",
                 "data/futures/cm/monthly/liquidationSnapshot/BTCUSD_PERP/"]:
        for ym in ["2020-01", "2020-04", "2020-06", "2021-01", "2021-02", "2021-03", "2021-06"]:
            sym = "BTCUSDT" if "um" in base else "BTCUSD_PERP"
            url = f"https://data.binance.vision/{base}{sym}-liquidationSnapshot-{ym}.zip"
            s, h = head(url)
            liq[f"HEAD {base}{sym} {ym}"] = {"status": s, "bytes": int(h.get("Content-Length") or 0) if s == 200 else None}
            time.sleep(0.1)
    out["liquidationSnapshot"] = liq

    # sample decodes (small full GETs or Range heads)
    samples = {}

    def add_sample(name, url, mode):
        if mode == "full":
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "a2-recon-probe/1.0"}), timeout=60) as r:
                data = r.read()
            hdr, rows = None, None
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                raw = z.read(z.namelist()[0]).decode("utf-8", errors="replace")
            lines = raw.splitlines()
            def numeric(cells):
                try:
                    float(cells[0]); return True
                except Exception:
                    return False
            start = 0
            if lines and not numeric(lines[0].split(",")):
                hdr = lines[0].split(","); start = 1
            rows = [ln.split(",") for ln in lines[start:start + 3]]
            samples[name] = {"url": url, "mode": "full", "bytes": len(data),
                             "sha256_full": hashlib.sha256(data).hexdigest(),
                             "fields": hdr if hdr else lines[0].split(","),
                             "csv_header_row_present": hdr is not None,
                             "sample_rows": rows,
                             "retrieved_time_utc": NOW(),
                             "last_modified": None}
        else:
            s, h, data = range_get(url)
            try:
                csv_head = inflate_head(data)
                hdr, rows = head_lines(csv_head)
            except Exception as e:
                hdr, rows = None, [[repr(e)]]
            samples[name] = {"url": url, "mode": "range_head", "http_status": s,
                             "bytes_total": int(h.get("Content-Length") or 0) if s in (200, 206) else None,
                             "sha256_range": hashlib.sha256(data).hexdigest(),
                             "sha256_scope": f"first {len(data)} bytes (partial)",
                             "fields": hdr,
                             "csv_header_row_present": hdr is not None,
                             "sample_rows": rows[:2],
                             "last_modified": h.get("Last-Modified"), "etag": h.get("ETag"),
                             "retrieved_time_utc": NOW()}
        time.sleep(0.2)

    # metrics daily: decode a recent small file fully
    m_last = out["families"]["metrics_daily"]["last_key"]
    add_sample("metrics_daily", f"https://data.binance.vision/{m_last}", "full")
    # an older metrics day for field drift check
    mkeys = out["families"]["metrics_daily"]["zip_keys"]
    if len(mkeys) > 400:
        add_sample("metrics_daily_older", f"https://data.binance.vision/{mkeys[400]}", "full")
    # bookTicker monthly sample (large file -> range head)
    bt_first = out["families"]["bookTicker_monthly"]["first_key"]
    add_sample("bookTicker_monthly", f"https://data.binance.vision/{bt_first}", "range")
    # bookTicker daily sample (large -> range head)
    btd_last = out["families"]["bookTicker_daily"]["last_key"]
    add_sample("bookTicker_daily", f"https://data.binance.vision/{btd_last}", "range")
    # bookDepth daily sample
    bd_last = out["families"]["bookDepth_daily"]["last_key"]
    add_sample("bookDepth_daily", f"https://data.binance.vision/{bd_last}", "range")
    # fundingRate monthly sample (small, full)
    fr_last = out["families"]["fundingRate_monthly"]["last_key"]
    add_sample("fundingRate_monthly", f"https://data.binance.vision/{fr_last}", "full")
    # premiumIndexKlines 1h sample (full)
    pk = out["families"]["premiumIndexKlines_1h_monthly"]["last_key"]
    add_sample("premiumIndexKlines_1h_monthly", f"https://data.binance.vision/{pk}", "full")
    out["samples"] = samples

    # REST fapi cross-checks (measured, not trusted from docs)
    rest = {}
    def jget(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "a2-recon-probe/1.0"}), timeout=30) as r:
            return json.loads(r.read().decode())
    try:
        t = jget(f"{REST_FAPI}/fapi/v1/time")
        rest["server_time_ms"] = t.get("serverTime")
    except Exception as e:
        rest["server_time_error"] = repr(e)
    time.sleep(0.5)
    try:
        oi = jget(f"{REST_FAPI}/futures/data/openInterestHist?symbol=BTCUSDT&period=5m&limit=500")
        rest["openInterestHist_5m_limit500_no_startTime"] = {
            "n": len(oi), "first": oi[0], "last": oi[-1]}
    except Exception as e:
        rest["openInterestHist_5m_limit500_no_startTime"] = {"error": repr(e)}
    time.sleep(0.5)
    try:
        oi2 = jget(f"{REST_FAPI}/futures/data/openInterestHist?symbol=BTCUSDT&period=5m&limit=500&startTime=1577836800000")
        rest["openInterestHist_5m_startTime_2020_01_01"] = {
            "n": len(oi2), "first_ts": oi2[0]["timestamp"] if oi2 else None,
            "last_ts": oi2[-1]["timestamp"] if oi2 else None}
    except Exception as e:
        rest["openInterestHist_5m_startTime_2020_01_01"] = {"error": repr(e)}
    time.sleep(0.5)
    try:
        oi3 = jget(f"{REST_FAPI}/futures/data/openInterestHist?symbol=BTCUSDT&period=1h&limit=500&startTime=1577836800000")
        rest["openInterestHist_1h_startTime_2020_01_01"] = {
            "n": len(oi3), "first_ts": oi3[0]["timestamp"] if oi3 else None}
    except Exception as e:
        rest["openInterestHist_1h_startTime_2020_01_01"] = {"error": repr(e)}
    time.sleep(0.5)
    try:
        fr = jget(f"{REST_FAPI}/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=0&limit=5")
        rest["fundingRate_startTime0_limit5"] = {"n": len(fr), "first": fr[0] if fr else None}
    except Exception as e:
        rest["fundingRate_startTime0_limit5"] = {"error": repr(e)}
    time.sleep(0.5)
    try:
        fr2 = jget(f"{REST_FAPI}/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1577836800000&limit=1000")
        rest["fundingRate_startTime_2020_01_01_limit1000"] = {
            "n": len(fr2),
            "first_time": fr2[0]["fundingTime"] if fr2 else None,
            "last_time": fr2[-1]["fundingTime"] if fr2 else None}
    except Exception as e:
        rest["fundingRate_startTime_2020_01_01_limit1000"] = {"error": repr(e)}
    out["rest_fapi"] = rest

    p = HERE / "s3_structure.json"
    p.write_text(json.dumps(out, indent=2))
    print("WROTE", p)


if __name__ == "__main__":
    main()
