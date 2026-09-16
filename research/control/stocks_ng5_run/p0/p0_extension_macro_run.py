"""P0-extension: macro shadow authority re-pin (A2R-F1/A4) — STOCKS-NG5.

Re-pins the FRED granted-set series DGS10 and DFII10 into this cycle's
staging so the D2 shadow inventory v2 macro shadows are measurable without
any ungated pull.  Two bounded HTTP requests; no PnL anywhere.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path("/Users/hoangminhlong/my-quantitative")
WT = ROOT / ".worktrees/stocks-ng5/integration"
CTL = WT / "research/control/stocks_ng5_run"


def load_key() -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("FRED_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("FRED entitlement key not found in root env file")


def main() -> int:
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    key = load_key()
    pins = {}
    for series in ("DGS10", "DFII10"):
        url = ("https://api.stlouisfed.org/fred/series/observations?"
               + urllib.parse.urlencode({
                   "series_id": series, "api_key": key, "file_type": "json",
                   "sort_order": "asc", "observation_start": "2005-06-01"}))
        req = urllib.request.Request(url, headers={"User-Agent": "my-quantitative-research/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
        p = CTL / f"p0/staging/FRED_{series}.json"
        p.write_bytes(body)
        pins[series] = {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
                        "path": str(p), "status": "HTTP 200"}
        print(f"re-pin {series}: {len(body)} bytes sha {hashlib.sha256(body).hexdigest()[:12]}")
    ext = {
        "schema": "stocks_ng5_p0_extension_macro_shadows@1",
        "cycle_id": "STOCKS-NG5",
        "frozen_at_utc": ts,
        "purpose": "P0-extension ordered by A2R-F1/A4: D2 shadow inventory v2 includes macro shadows (DGS10 nominal-LEVEL state per D1 R0-S4; DFII10 shock). Their data authority is the FRED granted set (RATES-NG1 §3 lineage); re-pinned INTO this cycle's staging so D2 measures them without any ungated pull.",
        "authority": "owner FRED entitlement; granted-set lineage plans/PLAN_rates_ng1.md §3; effective != available handled by AX2-as-of convention frozen for D2 (conservative +1 day availability)",
        "pins": pins,
        "http_requests": 2,
        "no_pnl_computed": True,
    }
    (CTL / "p0/p0_extension_macro_shadows.json").write_text(
        json.dumps(ext, indent=1, sort_keys=True) + "\n")
    print("extension artifact written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
