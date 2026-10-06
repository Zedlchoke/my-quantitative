#!/usr/bin/env python3
"""acq_probe.py — ACQ-OPT lane, FUTURES-BEHAVIOR-10SYMS-PREP-20261002.

METADATA-ONLY acquisition-optimization probe against official Databento
endpoints (hist.databento.com). Transport + param shapes copied verbatim
from the verified METADATA-PROBE lane script
(../databento_metadata_probe/probe_metadata.py, 78x HTTP 200 on 2026-10-02):
  - metadata.get_record_count / get_billable_size / get_cost : POST form
  - metadata.list_unit_prices : GET
  - symbology.resolve : POST (free endpoint), start_date/end_date params
  - parent symbology is {ROOT}.FUT (verified)
  - HTTP Basic auth, username=<key>, password="" — key read in-process from
    the owner 0600 file; NEVER in params/URLs/logs/artifacts.

Authority: metadata only. ZERO data downloads (no timeseries/batch/live),
ZERO purchases/subscriptions/account changes. get_cost is a quote, not a
charge. 100/600 USD are SCENARIOS, not granted budget.

Request budget: HARD CAP 260 logical requests, sequential, <=3 attempts each,
0.4 s sleep between requests, every call timestamped (UTC), errors redacted.

Phases
  P0  list_unit_prices refresh                        (1 req)
  P1  earliest-band grid 10 roots x 4 schemas         (~80 req: W-ladder
      [2010-06-06..2011-06-06],[2011..2013],[2013..2016],[2016..2019],
      [2019..2022] from oldest; first window with records>0 sets the band,
      then ONE half-year refinement of that window)
  P2  latest month per root x ohlcv-1m                (10 req)
  P3  package quotes: per line get_record_count +
      get_billable_size + get_cost                    (~100 req)
      pkgA ~ $100 scenario / pkgB ~ $600 scenario / pkgC longest, no cap
  P4  symbology.resolve fix validation                (1 req:
      continuous -> instrument_id on NQ/CL c/n parents)

Outputs (this directory):
  coverage_results.json        raw evidence + derived coverage + package totals
  package_manifests/pkgA.json  machine request lines, quoted
  package_manifests/pkgB.json
  package_manifests/pkgC.json
"""

import base64
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ----------------------------------------------------------------- config ---
KEY_PATH = Path(
    "/Users/hoangminhlong/.config/my-quantitative-secrets/databento-api-key"
)
SCRIPT_DIR = Path(__file__).resolve().parent
OUT_PATH = SCRIPT_DIR / "coverage_results.json"
PKG_DIR = SCRIPT_DIR / "package_manifests"
DATA_DEST = Path.home() / ".my-quantitative-data"

PRIMARY_HOST = "https://hist.databento.com"
FALLBACK_HOST = "https://databento.com"
DATASET = "GLBX.MDP3"
GB = 1_000_000_000.0

MAX_REQUESTS = 260          # hard cap, logical requests
MAX_ATTEMPTS = 3
BACKOFF_S = (2.0, 5.0)
SLEEP_BETWEEN_S = 0.4
ATTEMPT_TIMEOUT_S = 60

ALL_ROOTS = ["NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"]
PARENT = {r: f"{r}.FUT" for r in ALL_ROOTS}
COVERAGE_SCHEMAS = ["ohlcv-1m", "bbo-1m", "statistics", "definition"]
RECORD_SIZE = {"ohlcv-1m": 56, "bbo-1m": 80, "statistics": 80,
               "definition": 520}  # FACT: code/futbt/dbn/spec.py (frozen)

# Unit prices $/GB (historical mode) — refreshed at P0 from list_unit_prices;
# these are only a fallback default sourced from the METADATA-PROBE run
# (metadata_results.json R004, 2026-10-02).
UNIT_PRICE_DEFAULT = {"ohlcv-1m": 70.0, "bbo-1m": 18.0, "statistics": 1.0,
                      "definition": 1.7}

# Earliest-band ladder (oldest first). End dates EXCLUSIVE per API semantics.
BANDS = [
    ("W1", "2010-06-06", "2011-06-06"),
    ("W2", "2011-06-06", "2013-06-06"),
    ("W3", "2013-06-06", "2016-06-06"),
    ("W4", "2016-06-06", "2019-06-06"),
    ("W5", "2019-06-06", "2022-06-06"),
]
LATEST_PROBE_START = "2026-09-01"
LATEST_PROBE_END = "2026-10-02"   # exclusive -> covers through 2026-10-01

FULL_START = "2010-06-06"         # dataset-level history start (verified)
FULL_END = "2026-10-02"           # exclusive

TOKEN_RE = re.compile(r"db-[A-Za-z0-9_\-]{12,}")

# Package window design (analytic pre-tune from METADATA-PROBE EXP-04/05
# measured per-root list-cost rates; exact numbers re-measured in P3):
PKG_A_OHLCV = {  # $-100 scenario: 24-month floor for the 8 cheaper roots,
    # 12 months for the two dominant-cost roots (CL, NG) — floors for CL/NG
    # depth remain unmet in A (documented UNSUPPORTED list).
    **{r: ("2023-10-01", "2026-10-01") for r in
       ["NQ", "ES", "GC", "SI", "6E", "6J", "6B", "6A"]},
    "CL": ("2025-10-01", "2026-10-01"),
    "NG": ("2025-10-01", "2026-10-01"),
}
PKG_A_JOINED = {"definition": ("2023-10-01", "2026-10-01"),
                "statistics": ("2023-10-01", "2026-10-01")}
PKG_B_OHLCV = {  # $-600 scenario: NQ/ES full history, CL 2019+, NG 2021+,
    # remaining six 2019+ (all measured-start windows; FIX/FAST caveat pre-2017).
    "NQ": (FULL_START, FULL_END), "ES": (FULL_START, FULL_END),
    "CL": ("2019-01-01", FULL_END), "NG": ("2021-01-01", FULL_END),
    **{r: ("2019-01-01", FULL_END) for r in
       ["GC", "SI", "6E", "6J", "6B", "6A"]},
}
PKG_B_JOINED = {"definition": ("2019-01-01", FULL_END),
                "statistics": ("2019-01-01", FULL_END)}
PKG_B_BBO = {"NQ": ("2024-10-01", "2026-10-01"),   # NQ-H5/CL-H5 floor: >=2y
             "CL": ("2024-10-01", "2026-10-01")}    # synchronous BBO
PKG_C_JOINED = {"ohlcv-1m": (FULL_START, FULL_END),
                "definition": (FULL_START, FULL_END),
                "statistics": (FULL_START, FULL_END)}
PKG_C_BBO = {"NQ": (FULL_START, FULL_END), "CL": (FULL_START, FULL_END)}

RESULTS: dict = {
    "schema": "futures_behavior_10syms_acq_probe@1",
    "task_id": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
    "lane": "ACQ-OPT",
    "generated_utc_start": None,
    "generated_utc_end": None,
    "config": {
        "primary_host": PRIMARY_HOST,
        "dataset": DATASET,
        "max_requests": MAX_REQUESTS,
        "max_attempts_per_request": MAX_ATTEMPTS,
        "sequential": True,
        "data_downloaded_bytes": 0,
        "forbidden_endpoints_not_called": [
            "timeseries.get_range", "batch.submit_job", "live.*",
            "metadata.* purchase/subscription surfaces (none exist)",
        ],
    },
    "requests": {},
    "order": [],
    "unit_prices_usd_per_gb": None,
    "disk_snapshot": None,
    "coverage": None,
    "latest": None,
    "packages": None,
    "symbology_fix": None,
    "request_count": 0,
    "cap_exhausted": False,
}

_KEY_CACHE: str | None = None


def load_key() -> str:
    global _KEY_CACHE
    if _KEY_CACHE is None:
        try:
            _KEY_CACHE = KEY_PATH.read_text().strip()
        except OSError as exc:
            print(f"FATAL: cannot read key file ({type(exc).__name__}). "
                  "No probe performed.", file=sys.stderr)
            sys.exit(2)
        if not _KEY_CACHE:
            print("FATAL: key file empty.", file=sys.stderr)
            sys.exit(2)
    return _KEY_CACHE


def redact(text: str) -> str:
    try:
        key = load_key()
        if key and key in text:
            text = text.replace(key, "db-REDACTED")
    except SystemExit:
        raise
    except Exception:
        pass
    return TOKEN_RE.sub("db-REDACTED", text)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def flush_out() -> None:
    RESULTS["generated_utc_end"] = now_utc()
    tmp = OUT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(RESULTS, indent=1))
    tmp.replace(OUT_PATH)


# ------------------------------------------------------------- transport ---

def rpc(rid: str, endpoint: str, params: dict, post: bool, phase: str,
        line_id: str, note: str = "") -> dict:
    """One logical request (<= MAX_ATTEMPTS attempts). Counted against cap."""
    if RESULTS["request_count"] >= MAX_REQUESTS:
        RESULTS["cap_exhausted"] = True
        print(f"[CAP] skipping {rid} — hard cap {MAX_REQUESTS} reached")
        return {"rid": rid, "http_status": None, "result_summary": "SKIPPED_CAP",
                "payload": None, "error_redacted": "SKIPPED_CAP",
                "params": params, "note": note, "phase": phase,
                "line_id": line_id, "ts_start_utc": now_utc(),
                "ts_end_utc": now_utc(), "attempts": 0, "elapsed_ms": None,
                "http_method": "POST" if post else "GET"}
    RESULTS["request_count"] += 1
    started = now_utc()
    rec: dict = {
        "rid": rid, "phase": phase, "line_id": line_id, "endpoint": endpoint,
        "http_method": "POST" if post else "GET",
        "params": dict(params),  # never contains credentials
        "note": note, "ts_start_utc": started, "attempts": 0,
        "http_status": None, "result_summary": None, "error_redacted": None,
        "payload": None, "ts_end_utc": None, "elapsed_ms": None,
    }
    key = load_key()
    basic = base64.b64encode(f"{key}:".encode()).decode()
    hosts = [PRIMARY_HOST, FALLBACK_HOST]
    last_err = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        rec["attempts"] = attempt
        host = hosts[0] if attempt <= 2 else hosts[-1]
        url = f"{host}/v0/{endpoint}"
        try:
            if post:
                body = urllib.parse.urlencode(params).encode()
                req = urllib.request.Request(url, data=body, method="POST")
                req.add_header("Content-Type",
                               "application/x-www-form-urlencoded")
            else:
                qs = urllib.parse.urlencode(params)
                req = urllib.request.Request(f"{url}?{qs}", method="GET")
            req.add_header("Authorization", f"Basic {basic}")
            t0 = time.monotonic()
            with urllib.request.urlopen(req, timeout=ATTEMPT_TIMEOUT_S) as resp:
                status = resp.status
                raw = resp.read()  # metadata JSON only
            rec["elapsed_ms"] = int((time.monotonic() - t0) * 1000)
            rec["http_status"] = status
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:  # noqa: BLE001
                payload = {"_non_json_len_bytes": len(raw)}
            rec["payload"] = payload
            if endpoint == "metadata.get_record_count":
                rec["result_summary"] = f"record_count={payload}"
            elif endpoint == "metadata.get_billable_size":
                rec["result_summary"] = f"billable_size_bytes={payload}"
            elif endpoint == "metadata.get_cost":
                rec["result_summary"] = f"cost_usd={payload}"
            elif endpoint == "symbology.resolve":
                res = payload.get("result", {}) if isinstance(payload, dict) else {}
                rec["result_summary"] = (
                    f"resolved={len(res)}; intervals="
                    f"{ {str(k): len(v) for k, v in res.items()} }")
            else:
                rec["result_summary"] = f"rows={len(payload) if isinstance(payload, (list, dict)) else '?'}"
            rec["ts_end_utc"] = now_utc()
            break
        except urllib.error.HTTPError as exc:
            snippet = ""
            try:
                snippet = exc.read().decode("utf-8", "replace")[:400]
            except Exception:  # noqa: BLE001
                snippet = "<unreadable>"
            last_err = f"HTTP {exc.code}: {snippet}"
            rec["http_status"] = exc.code
            if exc.code < 500 and exc.code != 429:   # 4xx terminal
                rec["error_redacted"] = redact(last_err)
                rec["ts_end_utc"] = now_utc()
                break
        except Exception as exc:  # noqa: BLE001
            last_err = f"{type(exc).__name__}: {exc}"
        if attempt < MAX_ATTEMPTS:
            time.sleep(BACKOFF_S[min(attempt - 1, len(BACKOFF_S) - 1)])
    else:
        rec["error_redacted"] = redact(last_err or "unknown error")
        rec["ts_end_utc"] = now_utc()

    RESULTS["requests"][rid] = rec
    RESULTS["order"].append(rid)
    ok = rec["http_status"] == 200
    print(f"[{rid}] {rec['http_status'] or 'ERR'} {endpoint} "
          f"{rec['params'].get('schema', '')} "
          f"{rec['params'].get('symbols', '')[:48]} "
          f"{rec['params'].get('start', rec['params'].get('start_date', ''))} "
          f"{'OK' if ok else 'FAIL ' + (rec['error_redacted'] or '')[:100]}")
    flush_out()
    time.sleep(SLEEP_BETWEEN_S)
    return rec


def rc_ok(rec: dict) -> bool:
    return rec.get("http_status") == 200 and isinstance(
        rec.get("payload"), int)


def count_value(rec: dict):
    return rec["payload"] if rc_ok(rec) else None


def rc_params(symbols, schema, start, end, stype_in="parent"):
    return {"dataset": DATASET, "symbols": symbols, "schema": schema,
            "start": start, "end": end, "stype_in": stype_in}


def bs_params(symbols, schema, start, end, stype_in="parent"):
    return {**rc_params(symbols, schema, start, end, stype_in),
            "stype_out": "instrument_id"}


# ------------------------------------------------------------ disk gate ---

def disk_snapshot() -> dict:
    snap = {"path": str(DATA_DEST), "captured_utc": now_utc()}
    try:
        st = os.statvfs(DATA_DEST)
        snap["statvfs"] = {
            "f_bsize": st.f_bsize, "f_frsize": st.f_frsize,
            "f_blocks": st.f_blocks, "f_bfree": st.f_bfree,
            "f_bavail": st.f_bavail,
            "total_bytes": st.f_blocks * st.f_frsize,
            "free_bytes": st.f_bfree * st.f_frsize,
            "available_bytes": st.f_bavail * st.f_frsize,
            "available_gib": round(st.f_bavail * st.f_frsize / 2**30, 2),
            "available_gb_decimal": round(
                st.f_bavail * st.f_frsize / 1e9, 2),
        }
    except OSError as exc:
        snap["statvfs_error_redacted"] = redact(f"{type(exc).__name__}: {exc}")
    try:
        out = subprocess.run(["df", "-h", str(DATA_DEST)], capture_output=True,
                             text=True, timeout=15)
        snap["df_h"] = out.stdout.strip()
    except Exception as exc:  # noqa: BLE001
        snap["df_h_error_redacted"] = redact(f"{type(exc).__name__}: {exc}")
    try:
        du = subprocess.run(["du", "-sh", str(DATA_DEST)], capture_output=True,
                            text=True, timeout=120)
        snap["du_sh_current_usage"] = du.stdout.strip()
    except Exception as exc:  # noqa: BLE001
        snap["du_error_redacted"] = redact(f"{type(exc).__name__}: {exc}")
    return snap


# ---------------------------------------------------------------- phases ---

def phase0_prices() -> dict:
    print("== P0: unit prices refresh ==")
    rec = rpc("P0-PRICES", "metadata.list_unit_prices",
              {"dataset": DATASET}, False, "P0", "P0",
              "USD/GB per schema per mode; only legitimate price source")
    prices = dict(UNIT_PRICE_DEFAULT)
    src = "default fallback (METADATA-PROBE R004, 2026-10-02)"
    if rec.get("http_status") == 200 and isinstance(rec.get("payload"), list):
        for row in rec["payload"]:
            if isinstance(row, dict) and row.get("mode") == "historical":
                up = row.get("unit_prices", {})
                for s in UNIT_PRICE_DEFAULT:
                    if s in up:
                        prices[s] = float(up[s])
                src = "live list_unit_prices (this run)"
                break
    RESULTS["unit_prices_usd_per_gb"] = {"source": src, "mode": "historical",
                                         "prices": prices}
    return prices


def refine_start(band_start: str) -> str:
    y, m, d = (int(x) for x in band_start.split("-"))
    t = dt.date(y, m, d) + dt.timedelta(days=183)
    return t.isoformat()


def phase1_coverage() -> dict:
    """Per root x schema: first band with records>0 (oldest-first ladder),
    then ONE half-year refinement of that band's start."""
    print("== P1: earliest-band grid (10 roots x 4 schemas) ==")
    coverage: dict = {r: {} for r in ALL_ROOTS}
    for schema in COVERAGE_SCHEMAS:
        for root in ALL_ROOTS:
            cell = {"band_probes": [], "earliest_band": None,
                    "earliest_valid_from": None, "earliest_valid_to": None,
                    "notes": []}
            coverage[root][schema] = cell
            sym = PARENT[root]
            hit = None
            for band_id, s, e in BANDS:
                rid = f"P1-{schema}-{root}-{band_id}"
                rec = rpc(rid, "metadata.get_record_count",
                          rc_params(sym, schema, s, e), True, "P1",
                          f"coverage {root} {schema}",
                          f"band {band_id} {s}..{e}")
                cnt = count_value(rec)
                cell["band_probes"].append(
                    {"band": band_id, "start": s, "end": e,
                     "record_count": cnt,
                     "http_status": rec.get("http_status")})
                if cnt is not None and cnt > 0:
                    hit = (band_id, s, e)
                    break
                if cnt is None:
                    cell["notes"].append(
                        f"probe {band_id} failed (typed in requests log); "
                        "band unresolved below this point")
                    break   # do not burn requests past an error
            if hit:
                band_id, s, e = hit
                r_start = refine_start(s)
                rid = f"P1-{schema}-{root}-{band_id}R"
                rec = rpc(rid, "metadata.get_record_count",
                          rc_params(sym, schema, s, r_start), True, "P1",
                          f"coverage {root} {schema}",
                          f"half-year refinement {s}..{r_start}")
                cnt = count_value(rec)
                cell["band_probes"].append(
                    {"band": f"{band_id}R", "start": s, "end": r_start,
                     "record_count": cnt,
                     "http_status": rec.get("http_status")})
                if cnt is not None and cnt > 0:
                    cell["earliest_band"] = f"{s}..{r_start}"
                    cell["earliest_valid_from"] = s
                    cell["earliest_valid_to"] = r_start
                else:
                    cell["earliest_band"] = f"{r_start}..{e}"
                    cell["earliest_valid_from"] = r_start
                    cell["earliest_valid_to"] = e
            else:
                cell["earliest_band"] = "NO_RECORDS_IN_2010_2022_LADDER"
                cell["notes"].append(
                    "all five ladder windows returned 0 records (or probe "
                    "failure) — per-cell status NOT_RUN beyond ladder; "
                    "does NOT contradict dataset-level 2010-06-06 range")
    RESULTS["coverage"] = coverage
    return coverage


def phase2_latest() -> dict:
    print("== P2: latest month per root (ohlcv-1m) ==")
    latest: dict = {}
    for root in ALL_ROOTS:
        rid = f"P2-{root}"
        rec = rpc(rid, "metadata.get_record_count",
                  rc_params(PARENT[root], "ohlcv-1m", LATEST_PROBE_START,
                            LATEST_PROBE_END), True, "P2",
                  f"latest {root}",
                  f"{LATEST_PROBE_START}..{LATEST_PROBE_END} (end exclusive)")
        latest[root] = {"window": f"{LATEST_PROBE_START}..{LATEST_PROBE_END}",
                        "record_count": count_value(rec),
                        "http_status": rec.get("http_status")}
    RESULTS["latest"] = latest
    return latest


# ------------------------------------------------------- package quoting ---

def quote_line(pkg: str, line_id: str, schema: str, symbols: list,
               start: str, end: str, prices: dict, note: str = "") -> dict:
    """rc + bs + get_cost for one package line; exact, no double counting
    (each (symbols, schema, window) quoted once)."""
    sym = ",".join(symbols)
    rc_rec = rpc(f"{pkg}-{line_id}-RC", "metadata.get_record_count",
                 rc_params(sym, schema, start, end), True, "P3",
                 f"{pkg}:{line_id}", note)
    bs_rec = rpc(f"{pkg}-{line_id}-BS", "metadata.get_billable_size",
                 bs_params(sym, schema, start, end), True, "P3",
                 f"{pkg}:{line_id}", note)
    cost_rec = rpc(f"{pkg}-{line_id}-COST", "metadata.get_cost",
                   bs_params(sym, schema, start, end), True, "P3",
                   f"{pkg}:{line_id}", note)
    rc = count_value(rc_rec)
    bs = count_value(bs_rec)
    cost = count_value(cost_rec)
    line = {
        "line_id": line_id, "package": pkg, "schema": schema,
        "symbols": symbols, "stype_in": "parent",
        "start": start, "end": end,
        "end_exclusive": True,
        "record_count": rc,
        "billable_size_bytes": bs,
        "billable_gb_decimal": round(bs / GB, 6) if isinstance(bs, int) else None,
        "cost_usd_get_cost": cost,
        "cost_usd_list": round(bs / GB * prices[schema], 6)
                         if isinstance(bs, int) else None,
        "cost_ratio_get_cost_over_list": (
            round(cost / (bs / GB * prices[schema]), 4)
            if isinstance(bs, int) and isinstance(cost, (int, float))
            and bs > 0 else None),
        "consistency_bytes_eq_rc_x_recsize": (
            bs == rc * RECORD_SIZE[schema]
            if isinstance(bs, int) and isinstance(rc, int) else None),
        "http_statuses": {"rc": rc_rec.get("http_status"),
                          "bs": bs_rec.get("http_status"),
                          "cost": cost_rec.get("http_status")},
        "note": note,
    }
    return line


def package_totals(lines: list) -> dict:
    tot = {"lines": len(lines), "record_count": 0, "billable_size_bytes": 0,
           "cost_usd_list": 0.0, "cost_usd_get_cost": 0.0,
           "lines_with_get_cost": 0, "lines_failed": 0}
    for ln in lines:
        if ln["record_count"] is None or ln["billable_size_bytes"] is None:
            tot["lines_failed"] += 1
        if isinstance(ln["record_count"], int):
            tot["record_count"] += ln["record_count"]
        if isinstance(ln["billable_size_bytes"], int):
            tot["billable_size_bytes"] += ln["billable_size_bytes"]
        if isinstance(ln["cost_usd_list"], float):
            tot["cost_usd_list"] += ln["cost_usd_list"]
        if isinstance(ln["cost_usd_get_cost"], (int, float)):
            tot["cost_usd_get_cost"] += ln["cost_usd_get_cost"]
            tot["lines_with_get_cost"] += 1
    tot["billable_gb_decimal"] = round(
        tot["billable_size_bytes"] / GB, 4)
    tot["cost_usd_list"] = round(tot["cost_usd_list"], 2)
    tot["cost_usd_get_cost"] = round(tot["cost_usd_get_cost"], 2)
    return tot


def phase3_packages(prices: dict) -> dict:
    pkgs: dict = {}

    # ---------------- Package A: essential-10, ~$100 scenario -------------
    print("== P3: package A ($100 scenario) ==")
    lines_a = []
    for root in ALL_ROOTS:
        s, e = PKG_A_OHLCV[root]
        lines_a.append(quote_line(
            "PKGA", f"A-O1M-{root}", "ohlcv-1m", [PARENT[root]], s, e,
            prices, f"pkgA ohlcv-1m {root}"))
    for schema, (s, e) in PKG_A_JOINED.items():
        lines_a.append(quote_line(
            "PKGA", f"A-{schema}-ALL10", schema,
            [PARENT[r] for r in ALL_ROOTS], s, e, prices,
            f"pkgA joined {schema} all 10 roots"))
    pkgs["A"] = {"scenario": "essential 10 symbols, longest within ~$100",
                 "lines": lines_a, "totals": package_totals(lines_a)}

    # ---------------- Package B: ~$600 scenario ---------------------------
    print("== P3: package B ($600 scenario) ==")
    lines_b = []
    for root in ALL_ROOTS:
        s, e = PKG_B_OHLCV[root]
        lines_b.append(quote_line(
            "PKGB", f"B-O1M-{root}", "ohlcv-1m", [PARENT[root]], s, e,
            prices, f"pkgB ohlcv-1m {root}"))
    for schema, (s, e) in PKG_B_JOINED.items():
        lines_b.append(quote_line(
            "PKGB", f"B-{schema}-ALL10", schema,
            [PARENT[r] for r in ALL_ROOTS], s, e, prices,
            f"pkgB joined {schema} all 10 roots"))
    for root, (s, e) in PKG_B_BBO.items():
        lines_b.append(quote_line(
            "PKGB", f"B-BBO1M-{root}", "bbo-1m", [PARENT[root]], s, e,
            prices, f"pkgB bbo-1m {root} (roll-cost hypotheses)"))
    pkgs["B"] = {"scenario": "10 symbols, deeper history within ~$600",
                 "lines": lines_b, "totals": package_totals(lines_b)}

    # ---------------- Package C: longest feasible, no cap ------------------
    print("== P3: package C (longest feasible, no cap) ==")
    lines_c = []
    per_root_rc = {}
    for schema, (s, e) in PKG_C_JOINED.items():
        lines_c.append(quote_line(
            "PKGC", f"C-{schema}-ALL10", schema,
            [PARENT[r] for r in ALL_ROOTS], s, e, prices,
            f"pkgC joined {schema} all 10 roots, full dataset history"))
    for root, (s, e) in PKG_C_BBO.items():
        lines_c.append(quote_line(
            "PKGC", f"C-BBO1M-{root}", "bbo-1m", [PARENT[root]], s, e,
            prices, f"pkgC bbo-1m {root} full history"))
    for root in ALL_ROOTS:   # per-root ohlcv-1m record counts (rc only)
        s, e = PKG_C_JOINED["ohlcv-1m"]
        rid = f"PKGC-C-O1M-{root}-RC"
        rec = rpc(rid, "metadata.get_record_count",
                  rc_params(PARENT[root], "ohlcv-1m", s, e), True, "P3",
                  "PKGC:C-O1M", f"pkgC per-root ohlcv-1m count {root}")
        per_root_rc[root] = {"window": f"{s}..{e}",
                             "record_count": count_value(rec),
                             "http_status": rec.get("http_status")}
    pkgs["C"] = {"scenario": "longest feasible history, no cost cap",
                 "lines": lines_c, "totals": package_totals(lines_c),
                 "ohlcv1m_per_root_counts": per_root_rc}

    RESULTS["packages"] = pkgs
    return pkgs


def phase4_symbology_fix() -> dict:
    print("== P4: symbology.resolve fix validation (free endpoint) ==")
    params = {
        "dataset": DATASET,
        "symbols": "NQ.c.0,CL.c.0,NQ.n.0,CL.n.0",
        "stype_in": "continuous", "stype_out": "instrument_id",
        "start_date": "2010-01-01", "end_date": "2026-10-01",
    }
    rec = rpc("P4-SYMRES", "symbology.resolve", params, True, "P4",
              "P4", "continuous->instrument_id fix validation (422 fix)")
    out = {"params": {k: v for k, v in params.items()},
           "http_status": rec.get("http_status"),
           "summary": rec.get("result_summary"),
           "ok": rec.get("http_status") == 200}
    RESULTS["symbology_fix"] = out
    return out


# --------------------------------------------------------------- outputs ---

def write_package_manifests(pkgs: dict) -> None:
    PKG_DIR.mkdir(parents=True, exist_ok=True)
    for pkg, key in (("A", "pkgA"), ("B", "pkgB"), ("C", "pkgC")):
        data = pkgs[pkg]
        manifest = {
            "schema": "futures_behavior_10syms_package_manifest@1",
            "task_id": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
            "lane": "ACQ-OPT",
            "generated_utc": now_utc(),
            "package": pkg,
            "scenario": data["scenario"],
            "dataset": DATASET,
            "status": "QUOTED_ONLY — NOT authorization to spend; quotes from "
                      "live metadata calls recorded in ../coverage_results.json",
            "delivery_notes": {
                "stype_in": "parent ({ROOT}.FUT) — all listed expiries; "
                            "front/active contracts used downstream, dead "
                            "serials ride along but emit no trades bars",
                "continuous_series": "NEVER purchased (no CONTFUT/adjusted "
                                     "fills); vendor c/n/v tables via FREE "
                                     "symbology.resolve only",
                "daily_hourly": "aggregated LOCALLY from ohlcv-1m — no "
                                "ohlcv-1d/1h lines, no duplicate billing",
                "end_dates_exclusive": True,
                "chunks": "per (root, schema, calendar quarter); completion "
                          "ledger + SHA256 manifests; idempotent re-request "
                          "dedupe by exact params (one-owner rule)",
                "pilot_relationship": "pilot NQ/CL lines (data/request/"
                                      "request_manifest.json PILOT-01..06) "
                                      "remain SEPARATE; overlapping NQ/CL "
                                      "def/stat pilot windows must be carved "
                                      "out at chunk time by the one-owner rule",
            },
            "totals": data["totals"],
            "request_lines": [
                {"line_id": ln["line_id"], "dataset": DATASET,
                 "schema": ln["schema"], "symbols": ln["symbols"],
                 "stype_in": "parent", "start": ln["start"],
                 "end": ln["end"], "end_exclusive": True,
                 "quoted_record_count": ln["record_count"],
                 "quoted_billable_size_bytes": ln["billable_size_bytes"],
                 "quoted_cost_usd_get_cost": ln["cost_usd_get_cost"],
                 "quoted_cost_usd_list": ln["cost_usd_list"]}
                for ln in data["lines"]],
        }
        if "ohlcv1m_per_root_counts" in data:
            manifest["ohlcv1m_per_root_counts"] = data[
                "ohlcv1m_per_root_counts"]
        path = PKG_DIR / f"{key}.json"
        path.write_text(json.dumps(manifest, indent=1))
        print(f"wrote {path}")


def main() -> int:
    RESULTS["generated_utc_start"] = now_utc()
    print("acq_probe.py — METADATA-ONLY (zero data downloads, zero spend)")
    print(f"cap={MAX_REQUESTS} sequential requests; dataset={DATASET}")

    RESULTS["disk_snapshot"] = disk_snapshot()
    flush_out()

    prices = phase0_prices()
    flush_out()
    phase1_coverage()
    flush_out()
    phase2_latest()
    flush_out()
    pkgs = phase3_packages(prices)
    flush_out()
    phase4_symbology_fix()
    write_package_manifests(pkgs)

    RESULTS["generated_utc_end"] = now_utc()
    ok = sum(1 for r in RESULTS["requests"].values()
             if r.get("http_status") == 200)
    fail = len(RESULTS["requests"]) - ok
    print(f"DONE: {len(RESULTS['requests'])} logical requests "
          f"({ok} ok, {fail} non-200), cap {MAX_REQUESTS} "
          f"({'EXHAUSTED' if RESULTS['cap_exhausted'] else 'honored'})")
    print(f"evidence: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
