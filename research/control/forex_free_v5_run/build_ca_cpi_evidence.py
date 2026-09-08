#!/usr/bin/env python3
"""V5-P0a CA/StatCan per-print CPI release evidence builder.

Scans the official keyless WDS REST endpoint getChangedCubeList over weekdays
2018-03-01..2025-08-31, keeps any response containing a CPI-family product
(table group 18-10 = Price indexes: CPI cubes 18100xxx), archives the raw
bytes + sha256, and records the official releaseTime stamps.

Keyless official channel only. Paced 0.35s (WDS is a documented automation API).
"""
import hashlib
import json
import subprocess
import time
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
ARC = BASE / "cpi_calendar_archives" / "CA" / "wds"
ARC.mkdir(parents=True, exist_ok=True)
UA = "my-quantitative-research/1.0 (keyless official evidence probe)"
EP = "https://www150.statcan.gc.ca/t1/wds/rest/getChangedCubeList"
START = date(2018, 3, 1)
END = date(2025, 8, 31)
# CPI cube family: productIds observed in probes (table group 18-10-00xx).
# A response counts as a CPI release when ANY productId is in the CPI cube set.
CPI_PRODUCTS = {
    "18100001", "18100002", "18100004", "18100005", "18100006", "18100007",
    "18100008", "18100256",
}


def main():
    day = START
    rows = []
    hits = 0
    checked = 0
    while day <= END:
        if day.weekday() < 5:  # weekdays only (StatCan releases 08:30 ET weekdays)
            fname = ARC / f"wds_changed_{day.isoformat()}.json"
            if not fname.exists():
                r = subprocess.run(
                    ["curl", "-sS", "--max-time", "45", "-A", UA, "-o", str(fname),
                     "-w", "%{http_code}", f"{EP}/{day.isoformat()}"],
                    capture_output=True, text=True, timeout=60)
                code = r.stdout.strip()
            else:
                code = "200(cache)"
            checked += 1
            if code == "200":
                try:
                    d = json.loads(fname.read_text())
                    objs = d.get("object") or []
                    cpi = sorted({str(o["productId"]) for o in objs
                                  if str(o.get("productId")) in CPI_PRODUCTS
                                  and o.get("responseStatusCode") == 0})
                    if cpi:
                        times = sorted({o["releaseTime"] for o in objs
                                        if str(o.get("productId")) in CPI_PRODUCTS
                                        and o.get("responseStatusCode") == 0})
                        sha = hashlib.sha256(fname.read_bytes()).hexdigest()
                        rows.append({
                            "release_date": day.isoformat(),
                            "release_time_utc_display": times,
                            "cpi_products": cpi,
                            "archive_path": str(fname.relative_to(BASE)),
                            "archive_sha256": sha,
                            "class": "EVIDENCED",
                        })
                        hits += 1
                        print(f"{day}: CPI {cpi[:3]} {times}", flush=True)
                except Exception as e:
                    print(f"{day}: PARSE ERROR {e}", flush=True)
            else:
                print(f"{day}: HTTP {code}", flush=True)
                time.sleep(2)
            time.sleep(0.35)
        day += timedelta(days=1)
    (BASE / "ca_statcan_cpi_release_dates.json").write_text(json.dumps(rows, indent=1))
    print(f"DONE: scanned {checked} weekdays, {hits} CPI-release dates EVIDENCED", flush=True)


if __name__ == "__main__":
    main()
