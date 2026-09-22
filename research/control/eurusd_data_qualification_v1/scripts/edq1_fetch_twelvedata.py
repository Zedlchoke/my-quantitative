#!/usr/bin/env python
"""EDQ1 P1 bounded probe — Twelve Data EUR/USD 1min REST retrieval.

Credential law: TWELVE_DATA_API_KEY is read from root .env into process env
ONLY; never printed, never logged, never persisted. All recorded request URLs
are REDACTED (apikey parameter stripped before writing anything).

Pacing: <=8 requests/min (free tier). Pagination via 'next_url' is rewritten
to strip the apikey before being recorded.
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/eurusd-data-qualification-v1/integration"
CYCLE = os.path.join(WORKTREE, "research/control/eurusd_data_qualification_v1")
RAW_DIR = os.path.join(CYCLE, "data_local/twelvedata")
PROBE_DIR = os.path.join(CYCLE, "probe")
ROOT_ENV = "/Users/hoangminhlong/my-quantitative/.env"

BASE = "https://api.twelvedata.com/time_series"
UA = "edq1-data-qualification-probe/1 (internal research)"
PACE_S = 8.0  # >=8s between requests => <=7.5 req/min
RETRIES = 3
START = "2024-03-04 00:00:00"
END = "2024-03-14 00:00:00"


def redact(url: str) -> str:
    """Strip apikey from a URL for any persistent record."""
    p = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    q = [(k, v) for (k, v) in q if k.lower() != "apikey"]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(q), p.fragment))


def load_key():
    """Safe .env parser: KEY=VALUE lines; value stays in process memory only."""
    key = None
    with open(ROOT_ENV, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "TWELVE_DATA_API_KEY":
                key = v.strip().strip('"').strip("'")
    return key


def fetch(url: str):
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                hdrs = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, body, hdrs, None
        except urllib.error.HTTPError as e:
            return e.code, b"", {}, f"HTTPError {e.code}"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            time.sleep(2 ** attempt)
    return None, b"", {}, f"FAILED_AFTER_{RETRIES}_RETRIES: {last_err}"


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    key = load_key()
    if not key:
        print(json.dumps({"status": "BLOCKED_CREDENTIAL",
                          "note": "TWELVE_DATA_API_KEY absent in root .env"}))
        sys.exit(2)

    url = (f"{BASE}?symbol=EUR%2FUSD&interval=1min"
           f"&start_date={urllib.parse.quote(START)}&end_date={urllib.parse.quote(END)}"
           f"&timezone=UTC&format=JSON&outputsize=5000&apikey={key}")

    request_log = []   # redacted URLs only
    all_values = []
    page = 0
    while True:
        page += 1
        status, body, hdrs, err = fetch(url)
        request_log.append({
            "request_url_redacted": redact(url),
            "retrieval_start_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "http_status": status,
            "error": err,
            "content_type": hdrs.get("content-type"),
            "plan_like_headers": {k: v for k, v in hdrs.items()
                                  if any(s in k for s in ("credit", "plan", "rate", "quota", "limit"))},
        })
        if err or status != 200:
            break
        doc = json.loads(body)
        with open(os.path.join(RAW_DIR, f"page_{page:02d}.json"), "wb") as f:
            f.write(body)  # raw response; contains no credential
        if "status" in doc and doc.get("status") == "error":
            request_log[-1]["api_error"] = doc.get("message", doc.get("err"))
            break
        vals = doc.get("values", [])
        all_values.extend(vals)
        nxt = doc.get("next_url")
        if nxt:
            url = nxt + (f"&apikey={key}" if "apikey=" not in nxt else "")
        elif vals and vals[-1]["datetime"] > START:
            # observed plan behavior: no next_url key; response is newest-first,
            # capped at outputsize. Page manually: move end_date to oldest bar - 1min.
            oldest = dt.datetime.strptime(vals[-1]["datetime"], "%Y-%m-%d %H:%M:%S")
            new_end = (oldest - dt.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
            url = (f"{BASE}?symbol=EUR%2FUSD&interval=1min"
                   f"&start_date={urllib.parse.quote(START)}&end_date={urllib.parse.quote(new_end)}"
                   f"&timezone=UTC&format=JSON&outputsize=5000&apikey={key}")
        else:
            break
        time.sleep(PACE_S)

    with open(os.path.join(PROBE_DIR, "twelvedata_request_log.json"), "w") as f:
        json.dump({
            "schema": "edq1_retrieval_manifest@1",
            "source": "twelvedata",
            "endpoint": "time_series",
            "symbol": "EUR/USD", "interval": "1min",
            "window_utc": [START, END],
            "credential": "TWELVE_DATA_API_KEY from root .env (env-only, redacted everywhere)",
            "pages": page,
            "values_returned": len(all_values),
            "requests": request_log,
        }, f, indent=2)

    # normalized store for the analysis step
    with open(os.path.join(RAW_DIR, "values_1min.json"), "w") as f:
        json.dump(all_values, f)

    if all_values:
        fields = sorted({k for v in all_values for k in v.keys()})
        first, last = all_values[0], all_values[-1]
        print(json.dumps({
            "pages": page, "values": len(all_values),
            "field_inventory": fields,
            "first_bar": first, "last_bar": last,
            "request_errors": [r for r in request_log if r["error"]],
        }, indent=2))
    else:
        print("NO VALUES RETRIEVED", json.dumps(request_log, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
