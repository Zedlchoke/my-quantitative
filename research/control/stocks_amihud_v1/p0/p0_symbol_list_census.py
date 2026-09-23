"""STOCKS-AMIHUD-V1 P0 universe seed census (F4 light precursor).

One /exchange-symbol-list pull (delisted included) + Type census to freeze
the common-stock filter BEFORE the heavy crawl. Token never echoed.
"""
from __future__ import annotations

import collections
import hashlib
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV_PATH = Path("/Users/hoangminhlong/my-quantitative/.env")
BASE = "https://eodhd.com/api"


def load_token() -> str:
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith("EODHD_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("EODHD_API_KEY missing from .env")


def get_csv(path: str, params: dict) -> tuple[int, bytes]:
    q = dict(params)
    q["api_token"] = load_token()
    url = f"{BASE}{path}?{urllib.parse.urlencode(q)}"
    req = urllib.request.Request(url, headers={"User-Agent": "stocks-amihud-v1-p0-light/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:512]


def main() -> None:
    out = {"schema": "p0_symbol_list_census/stocks_amihud_v1@1",
           "measured_utc": datetime.now(timezone.utc).isoformat()}
    st, b = get_csv("/exchange-symbol-list", {"exchange": "US", "delisted": "1", "fmt": "csv"})
    out["status"] = st
    out["raw_sha256"] = hashlib.sha256(b).hexdigest()
    out["raw_bytes"] = len(b)
    (HERE / "raw_us_symbol_list_delisted.csv").write_bytes(b)
    text = b.decode("utf-8", errors="replace")
    lines = text.splitlines()
    header = lines[0].split(",")
    out["header"] = header
    type_col = header.index("Type") if "Type" in header else None
    code_col = header.index("Code") if "Code" in header else 0
    census = collections.Counter()
    n = 0
    for ln in lines[1:]:
        parts = ln.split(",")
        if len(parts) <= max(type_col or 0, code_col):
            continue
        n += 1
        if type_col is not None:
            census[parts[type_col].strip()] += 1
    out["rows_total"] = n
    out["type_census"] = dict(census.most_common())
    # proposed frozen filter (to be frozen in F4 census artifact after review)
    out["proposed_filter"] = {"Type == ": "Common Stock"}
    out["common_stock_rows"] = census.get("Common Stock", 0)
    (HERE / "p0_symbol_list_census.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("status", "rows_total", "common_stock_rows",
                                          "type_census")}, indent=1))


if __name__ == "__main__":
    main()
