#!/usr/bin/env python
"""Endpoint-shape probe for the EODHD earnings channel (no key echo)."""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path("/Users/hoangminhlong/my-quantitative")


def load_key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("EODHD_API_KEY="):
            k = line.split("=", 1)[1].strip()
            if k:
                return k
    raise SystemExit("no key")


def probe(label, url):
    key = load_key()
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            body = json.loads(r.read().decode())
        shape = type(body).__name__
        if isinstance(body, dict):
            print(label, "OK", r.status, "dict keys:", str(list(body.keys()))[:160])
        elif isinstance(body, list):
            print(label, "OK", r.status, "list n=", len(body), "sample:", json.dumps(body[0])[:200] if body else "[]")
        else:
            print(label, "OK", r.status, shape, str(body)[:120])
    except urllib.error.HTTPError as e:
        print(label, "HTTP", e.code)
    except Exception as e:
        print(label, "ERR", repr(e)[:120])



def probe_raw(label, url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=30) as r:
            print(label, "status", r.status, "ctype", r.headers.get("Content-Type"))
            print("body[:300]:", r.read().decode(errors="replace")[:300])
    except urllib.error.HTTPError as e:
        print(label, "HTTP", e.code, "ctype", e.headers.get("Content-Type"))
        print("body[:300]:", e.read().decode(errors="replace")[:300])
    except Exception as e:
        print(label, "ERR", repr(e)[:120])


if __name__ == "__main__":
    which = sys.argv[1]
    if which == "raw-earnings-noslash":
        probe_raw("earnings-noslash",
                  f"https://eodhd.com/api/earnings?api_token={load_key()}&symbols=AAPL.US&from=2024-01-01&to=2024-03-01")
    elif which == "raw-eod":
        probe_raw("eod-price-known-good",
                  f"https://eodhd.com/api/eod/AAPL.US?api_token={load_key()}&period=d&order=a&from=2026-08-25&to=2026-08-31")
    elif which == "calendar-earnings":
        probe_raw("calendar-earnings",
                  f"https://eodhd.com/api/calendar/earnings?api_token={load_key()}&from=2024-01-01&to=2024-02-01&tickers=AAPL.US")
    elif which == "fundamentals":
        probe("fundamentals-filter-earnings",
              f"https://eodhd.com/api/fundamentals/AAPL.US?api_token={load_key()}&filter=earnings")
    else:
        print("unknown arg")
