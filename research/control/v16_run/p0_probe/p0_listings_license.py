"""CRYPTO-V16 P0 completion: listing evidence + license re-verify + design freeze inputs.

Evidence discipline (plan PLAN_crypto_v16.md section 4 P0, P-1, FAMILY_PIPELINE 2.7):
- S3 listing pages saved raw (gitignored /v16_data/p0_evidence/) with sha256 in the
  committed manifest; per-file LastModified is the evidenced publication timestamp
  as listed at retrieval; retrieved_at recorded;
- license terms re-fetched fresh and hash-compared against the V15 pin (94d6f61a...);
- read-only keyless HTTP; no credentials, no assumptions.

Usage: python p0_listings_license.py
"""
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

WORKTREE = Path(__file__).resolve().parents[4]
EVID = WORKTREE / "v16_data" / "p0_evidence"
ART = WORKTREE / "research" / "control" / "v16_run" / "p0_probe"

BUCKET = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
TERMS_PDF_URL = "https://data.binance.vision/Binance_Vision-Terms_of_Use.pdf"
TERMS_HTML_URL = "https://data.binance.vision/terms-of-use.html"
V15_TERMS_PDF_SHA256 = "94d6f61a39b5f821ef1d38f968aea1f2aa136e374f2061a2131db9a6af96bc3b"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
S0_MONTHS = [f"{y}-{m:02d}" for y, m in
             [(2025, 8), (2025, 9), (2025, 10), (2025, 11), (2025, 12),
              (2026, 1), (2026, 2), (2026, 3), (2026, 4), (2026, 5),
              (2026, 6), (2026, 7), (2026, 8)]]

NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(url: str) -> bytes:
    with urlopen(url, timeout=60) as resp:
        return resp.read()


def pin(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def month_end_utc(month: str) -> datetime:
    y, m = int(month[:4]), int(month[5:7])
    if m == 12:
        nxt = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
    else:
        nxt = datetime(y, m + 1, 1, tzinfo=timezone.utc)
    from datetime import timedelta
    return nxt - timedelta(seconds=1)


def parse_listing(xml_bytes: bytes, symbol: str) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    out = []
    for c in root.iter(f"{NS}Contents"):
        key = c.findtext(f"{NS}Key") or ""
        if not (key.endswith(".zip") and "-aggTrades-" in key):
            continue
        lm = c.findtext(f"{NS}LastModified") or ""
        size = c.findtext(f"{NS}Size") or ""
        out.append({"key": key, "last_modified": lm, "size_bytes": int(size)})
    return out


def main() -> None:
    EVID.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    retrieved_at = utcnow()
    manifest_files = []

    # --- license re-verify (fresh fetch, hash vs V15 pin) ---
    pdf = fetch(TERMS_PDF_URL)
    (EVID / "Binance_Vision-Terms_of_Use.pdf").write_bytes(pdf)
    pdf_sha = pin(pdf)
    html = fetch(TERMS_HTML_URL)
    (EVID / "data.binance.vision_terms-of-use.html").write_bytes(html)
    license_block = {
        "terms_pdf_url": TERMS_PDF_URL,
        "terms_pdf_sha256_fresh": pdf_sha,
        "v15_pin_sha256": V15_TERMS_PDF_SHA256,
        "byte_identical_to_v15_pin": pdf_sha == V15_TERMS_PDF_SHA256,
        "terms_html_sha256_fresh": pin(html),
        "retrieved_at": retrieved_at,
        "verdict": "AUTHORIZED_INTERNAL_RESEARCH (V15 scope reading carried: section 4.1 "
                   "permits algorithmic historical backtesting for purely personal "
                   "non-production research; no live proprietary trading)",
        "v15_evidence": "v15 p0_probe probe_verdict_v15.json .license (Terms v1.0, last updated 2026-08-26)",
    }

    # --- listings per candidate symbol ---
    per_symbol = {}
    for sym in SYMBOLS:
        prefix = f"data/futures/um/monthly/aggTrades/{sym}/"
        listing_url = f"{BUCKET}?delimiter=/&prefix={prefix}"
        xml_bytes = fetch(listing_url)
        raw_name = f"{sym}_monthly_aggtrades_listing.xml"
        (EVID / raw_name).write_bytes(xml_bytes)
        manifest_files.append({"staged_name": raw_name, "bytes": len(xml_bytes),
                               "sha256": pin(xml_bytes), "source_url": listing_url})
        rows = parse_listing(xml_bytes, sym)
        lags = []
        for r in rows:
            stem = r["key"].rsplit("/", 1)[-1][:-4]  # e.g. BTCUSDT-aggTrades-2025-08
            parts = stem.rsplit("-", 2)
            month = f"{parts[1]}-{parts[2]}"
            if month not in S0_MONTHS:
                continue
            lm_dt = datetime.fromisoformat(r["last_modified"].replace("Z", "+00:00"))
            lag_h = (lm_dt - month_end_utc(month)).total_seconds() / 3600
            r.update({"month": month, "publication_lag_hours_rounded": round(lag_h, 1)})
            lags.append(lag_h)
        lags.sort()
        n = len(lags)
        per_symbol[sym] = {
            "listing_url": listing_url,
            "objects_in_prefix_total": len(rows),
            "s0_months_found": [r["month"] for r in rows if "month" in r],
            "s0_months_missing": sorted(set(S0_MONTHS) - {r["month"] for r in rows if "month" in r}),
            "publication_lag_hours": {
                "n": n,
                "min": round(lags[0], 1) if lags else None,
                "p50": round(lags[n // 2], 1) if n else None,
                "max": round(lags[-1], 1) if n else None,
            },
            "rows": rows,
        }
        manifest_files.append({"staged_name": raw_name + ".sha256.txt",
                               "sha256": pin(xml_bytes), "note": "duplicate pin in manifest"})

    result = {
        "schema": "v16_run_artifact_v1",
        "artifact": "p0_listings_license",
        "generated_utc": utcnow(),
        "producer_role": "A1 (P0 completion, A3-class evidence work)",
        "retrieved_at": retrieved_at,
        "license": license_block,
        "listing_evidence": {
            "semantics": "S3 LastModified = object creation time as listed at retrieval "
                         "(V15-identical evidence class); dated monthly objects; "
                         "publication lag measured against month end UTC",
            "first_class_caveat": "original listing dates inside a potentially rewritten "
                                  "span remain UNEVIDENCED per-file (V15 identical caveat, "
                                  "carried to D2/A7/owner, not silently resolved); V16 "
                                  "conditioning uses exchange event-time (transact_time), "
                                  "not archive vintage, so the caveat does not touch the "
                                  "decision clock",
            "per_symbol": {k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                           for k, v in per_symbol.items()},
        },
        "rows_full": {k: v["rows"] for k, v in per_symbol.items()},
        "evidence_dir_gitignored": str(EVID),
        "manifest_files": manifest_files,
    }
    out = ART / "p0_listings_license.json"
    out.write_text(json.dumps(result, indent=1) + "\n")
    slim = {k: v for k, v in result.items() if k != "rows_full"}
    print(json.dumps(slim, indent=1)[:3500])


if __name__ == "__main__":
    main()
