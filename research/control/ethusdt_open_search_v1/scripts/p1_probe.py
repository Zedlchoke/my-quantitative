"""EOS1 P1 probe — measure Binance Vision monthly-zip availability floors.

Keyless public CDN availability probe only (HEAD requests, no auth, no
account). Paced >= 0.35 s apart per plan §2 egress etiquette (2026-09-21
418 precedent). Writes probe_result.json next to this script.

Series probed (plan §2):
  futures/um  klines        ETHUSDT 1h      (execution series)
  futures/um  fundingRate   ETHUSDT         (measured funding cost authority)
  spot        klines        ETHBTC  1h      (lane E2 signal input)
  futures/um  klines        BTCUSDT 1h      (lane E1 signal input)
"""
from __future__ import annotations

import json
import pathlib
import time
import urllib.request

PAUSE_S = 0.35
BASE = "https://data.binance.vision/data"

PROBES = [
    ("futures/um/klines/ETHUSDT/1h/ETHUSDT-1h-{ym}.zip", "klines:ETHUSDT:1h",
     ["2019-10", "2019-11", "2019-12", "2020-01", "2026-08", "2026-09"]),
    ("futures/um/fundingRate/ETHUSDT/ETHUSDT-fundingRate-{ym}.zip",
     "fundingRate:ETHUSDT", ["2019-11", "2019-12", "2020-01", "2020-02", "2020-07", "2026-08"]),
    ("spot/klines/ETHBTC/1h/ETHBTC-1h-{ym}.zip", "klines:ETHBTC:1h",
     ["2020-01", "2026-08"]),
    ("futures/um/klines/BTCUSDT/1h/BTCUSDT-1h-{ym}.zip", "klines:BTCUSDT:1h",
     ["2020-01", "2026-08"]),
]


def probe(url: str, attempts: int = 3, backoff_s: float = 1.0) -> dict:
    """GET + 1-byte Range with retry: the Vision CDN answers transient 404s
    to existing keys AND 404 to every HEAD (both measured 2026-09-24).
    A month is declared MISSING only after all attempts 404 — stagers must
    carry the same retry law, never trust a single 404."""
    seen = []
    for i in range(attempts):
        req = urllib.request.Request(
            url, headers={"User-Agent": "eos1-p1-probe/1.0",
                          "Range": "bytes=0-15"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                blob = r.read(16)
                return {"http_status": r.status, "bytes_read": len(blob),
                        "magic": blob[:4] == b"PK\x03\x04" and "ZIP_MAGIC" or None,
                        "attempts": seen + [r.status]}
        except urllib.error.HTTPError as e:
            seen.append(e.code)
            if e.code != 404:
                return {"http_status": e.code, "bytes_read": None,
                        "magic": None, "attempts": seen}
        except Exception:
            seen.append(-1)
        time.sleep(backoff_s)
    return {"http_status": seen[-1] if seen else -1, "bytes_read": None,
            "magic": None, "attempts": seen}


def main() -> None:
    out = {"schema": "eos1.p1_probe@1",
           "probe_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "method": "HEAD, keyless, paced >=0.35s", "series": {}}
    for template, series, months in PROBES:
        rows = {}
        for ym in months:
            url = f"{BASE}/{template.format(ym=ym)}"
            rows[ym] = {**probe(url), "url": url}
            time.sleep(PAUSE_S)
        out["series"][series] = rows
    dest = pathlib.Path(__file__).with_name("probe_result.json")
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({s: {m: (r["http_status"], r.get("magic"),
                              len(r.get("attempts", [])))
                          for m, r in v.items()}
                      for s, v in out["series"].items()}, indent=1))


if __name__ == "__main__":
    main()
