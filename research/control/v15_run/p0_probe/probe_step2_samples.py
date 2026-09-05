#!/usr/bin/env python3
"""V15 P0/P2 probe step 2: schema-drift samples + license evidence.

Bounded downloads (gitignored staged/, sha256 recorded): one file per
regime boundary for the schema-diff, plus the repository license/terms
page. No unbounded downloads; aggTrades-class stays out of scope.
"""
import csv
import hashlib
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path

STAGED = Path(__file__).parent / "staged"
STAGED.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "my-quantitative-v15-probe/1.0"}

# regime-boundary samples: (symbol, date, regime_label)
SAMPLES = [
    ("BTCUSDT", "2023-08-01", "continuous_2023"),
    ("BTCUSDT", "2024-02-01", "continuous_pre_gap"),
    ("BTCUSDT", "2024-03-01", "backfilled_span_start"),
    ("BTCUSDT", "2025-08-21", "backfilled_span_S0_start_minus_1"),
    ("BTCUSDT", "2025-09-01", "backfilled_span_S0"),
    ("BTCUSDT", "2026-07-11", "backfilled_span_end"),
    ("BTCUSDT", "2026-07-12", "continuous_post_backfill"),
    ("BTCUSDT", "2026-08-20", "continuous_post_backfill"),
    ("ETHUSDT", "2025-09-01", "backfilled_span_S0"),
    ("SUIUSDT", "2025-09-01", "backfilled_span_S0"),
    ("1000PEPEUSDT", "2026-08-20", "continuous_post_backfill_altcoin"),
]


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    manifest, schemas = [], {}
    for sym, date, label in SAMPLES:
        name = f"{sym}-metrics-{date}.zip"
        url = f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{name}"
        raw = fetch(url)
        (STAGED / name).write_bytes(raw)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            inner = z.namelist()[0]
            with z.open(inner) as f:
                text = io.TextIOWrapper(f, encoding="utf-8")
                rows = list(csv.reader(text))
        manifest.append({
            "staged_name": name, "url": url, "bytes": len(raw),
            "sha256": sha256(raw), "regime_label": label,
        })
        schemas[name] = {
            "regime_label": label, "symbol": sym, "date": date,
            "n_data_rows": len(rows) - 1,
            "header": rows[0],
            "first_data_row": rows[1] if len(rows) > 1 else None,
            "last_data_row": rows[-1] if len(rows) > 1 else None,
        }
        print(f"{name:38} bytes={len(raw):>7} rows={len(rows)-1:>5} cols={len(rows[0])} [{label}]")

    lic = fetch("https://data.binance.vision/")
    (STAGED / "data.binance.vision_landing.html").write_bytes(lic)
    manifest.append({
        "staged_name": "data.binance.vision_landing.html",
        "url": "https://data.binance.vision/", "bytes": len(lic),
        "sha256": sha256(lic), "regime_label": "license_terms",
    })
    print(f"landing page bytes={len(lic)}")

    out = {
        "schema": "v15_probe_v1", "artifact": "metrics_schema_license_samples",
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "manifest": manifest, "schemas": schemas,
    }
    (Path(__file__).parent / "step2_samples.json").write_text(json.dumps(out, indent=1))
    print("wrote step2_samples.json")


if __name__ == "__main__":
    main()
