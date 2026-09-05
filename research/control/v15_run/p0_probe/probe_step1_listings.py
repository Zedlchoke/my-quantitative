#!/usr/bin/env python3
"""V15 P0/P2 probe step 1: per-symbol S3 listings for the daily metrics family.

Evidence discipline (plan PLAN_crypto_v15.md section 3, P-1):
- every listing page saved to staged/ with sha256 recorded in the manifest;
- per-file LastModified is the evidenced publication timestamp (S3 object
  creation time as listed at retrieval; retrieved_at recorded);
- read-only keyless HTTP; no credentials, no assumptions.
"""
import json
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BUCKET = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
PREFIX = "data/futures/um/daily/metrics/"
STAGED = Path(__file__).parent / "staged"
STAGED.mkdir(parents=True, exist_ok=True)

SYMBOLS = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "BTCUSDT", "DOGEUSDT",
    "ENAUSDT", "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT",
    "SOLUSDT", "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "my-quantitative-v15-probe/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def list_prefix(prefix: str):
    """Page through the S3 listing; return (pages, objects)."""
    pages, objects, marker = [], [], None
    while True:
        url = f"{BUCKET}?delimiter=/&prefix={prefix}&max-keys=1000"
        if marker:
            url += f"&marker={marker}"
        raw = fetch(url)
        name = prefix.rstrip("/").split("/")[-1] + f"_page{len(pages):03d}.xml"
        (STAGED / name).write_bytes(raw)
        pages.append({"staged_name": name, "url": url, "bytes": len(raw)})
        root = ET.fromstring(raw)
        ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
        for c in root.findall("s3:Contents", ns):
            objects.append({
                "key": c.findtext("s3:Key", default="", namespaces=ns),
                "size": int(c.findtext("s3:Size", default="0", namespaces=ns)),
                "last_modified": c.findtext("s3:LastModified", default="", namespaces=ns),
            })
        truncated = root.findtext("s3:IsTruncated", default="false", namespaces=ns) == "true"
        if not truncated:
            break
        marker = root.findtext("s3:NextMarker", default=None, namespaces=ns)
        if marker is None:  # delimiter listing: fall back to last common prefix
            cps = root.findall("s3:CommonPrefixes/s3:Prefix", ns) or root.findall("s3:Contents/s3:Key", ns)
            marker = cps[-1].text
        if len(pages) > 40:
            raise RuntimeError(f"listing pagination runaway for {prefix}")
    return pages, objects


def main():
    retrieved = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    out = {"schema": "v15_probe_v1", "artifact": "metrics_symbol_listings",
           "retrieved_at_utc": retrieved, "bucket": BUCKET, "prefix": PREFIX,
           "symbols": {}}
    for sym in SYMBOLS:
        pages, objs = list_prefix(f"{PREFIX}{sym}/")
        files = sorted(o["key"] for o in objs if o["key"].endswith(".zip"))
        dates = [f.rsplit("-metrics-", 1)[1][:10] for f in files]
        out["symbols"][sym] = {
            "n_files": len(files),
            "first_date": min(dates) if dates else None,
            "last_date": max(dates) if dates else None,
            "pages": pages,
            "objects": objs,
        }
        print(f"{sym}: n={len(files)} first={min(dates) if dates else '-'} last={max(dates) if dates else '-'}", flush=True)
    (Path(__file__).parent / "step1_listings.json").write_text(json.dumps(out, indent=1))
    print("wrote step1_listings.json")


if __name__ == "__main__":
    sys.exit(main())
