#!/usr/bin/env python3
"""probe_metadata.py — SERIALIZED, METADATA-ONLY Databento probe for
FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (lane METADATA-PROBE).

Authority: owner dispatch (this lane's packet). Scope: READ-ONLY metadata —
authentication check, dataset/schema/coverage/entitlement verification,
record counts, billable sizes, cost quotes — per the prepared request
manifest at ../data/request/request_manifest.json (READ-ONLY input; this
script never writes there).

Endpoints used (verified 2026-10-02 against the official docs URLs and the
official Python client source, github.com/databento/databento-python @ main;
RPC form https://hist.databento.com/v0/METHOD_FAMILY.METHOD per docs page
/api-reference-historical):

  GET  /v0/metadata.list_datasets       (list of dataset codes)
  GET  /v0/metadata.list_schemas        (schemas for a dataset)
  GET  /v0/metadata.get_dataset_range   (available range GIVEN ENTITLEMENTS)
  GET  /v0/metadata.list_unit_prices    (USD per GB per schema per mode)
  POST /v0/metadata.get_record_count    (int count; NO stype_out sent)
  POST /v0/metadata.get_billable_size   (int billable UNCOMPRESSED bytes)
  POST /v0/metadata.get_cost            (float USD quote)
  POST /v0/symbology.resolve            (FREE per docs symbology page)

Billing safety (docs, access 2026-10-02): usage-based pricing page states
billing is "per byte consumed" of delivered historical DATA (uncompressed
DBN binary). Every endpoint above returns metadata (codes/lists/counts/
sizes/prices/mappings), not data. symbology.resolve is explicitly free
("Databento offers symbology resolution for free in our symbology.resolve
endpoint"). No timeseries.get_range, no batch submit, no live, no purchase,
no account change is performed by this script. Zero data bytes downloaded.

NOT called (typed NOT_RUN_DOC_UNCLEAR): any whoami/account endpoint — none
exists in the official client's API surface or the docs nav; auth is
verified by the authenticated metadata calls themselves.

Key handling (owner rules): the key is read INSIDE this process from
/Users/hoangminhlong/.config/my-quantitative-secrets/databento-api-key
(0600) and used ONLY as HTTP Basic credentials to official Databento
endpoints. It is never printed, passed as an argument, placed in the
environment, or written to any output. All error text is scrubbed against
the key value and any db-XXXX token-like substring before storage.

Request budget: HARD CAP 80 logical requests (plan uses exactly 80),
sequential (1 in flight), <=3 attempts per request (backoff 2 s / 5 s) on
network errors / 5xx / 429 only; 4xx is terminal (typed, not retried).

IMPORTANT CORRECTION vs the prepared probe scripts (data/request/, not
modified): with stype_in=parent the correct GLBX.MDP3 symbols are
"{ROOT}.FUT" (docs standards-and-conventions/symbology + examples pages,
access 2026-10-02), not the bare root. This script sends {ROOT}.FUT.

Exit codes: 0 = all planned requests completed (results may still contain
per-request errors); 2 = key file missing/unreadable; 3 = fatal early
failure (Phase A auth dead); 5 = EXPANSION skipped by gate (typed blocker).
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import re
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
MANIFEST_PATH = (
    SCRIPT_DIR.parent / "data" / "request" / "request_manifest.json"
)  # READ-ONLY input
OUT_PATH = SCRIPT_DIR / "metadata_results.json"

PRIMARY_HOST = "https://hist.databento.com"   # current official client default
FALLBACK_HOST = "https://databento.com"       # legacy gateway (prepared probes)
DATASET = "GLBX.MDP3"
GB = 1_000_000_000.0  # decimal GB — the unit the vendor prices in

MAX_REQUESTS = 80
MAX_ATTEMPTS = 3
BACKOFF_S = (2.0, 5.0)
SLEEP_BETWEEN_S = 0.4
ATTEMPT_TIMEOUT_S = 60

ALL_ROOTS = ["NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"]
PARENT = {r: f"{r}.FUT" for r in ALL_ROOTS}  # correct parent symbology

TOKEN_RE = re.compile(r"db-[A-Za-z0-9_\-]{12,}")

RESULTS: dict = {
    "schema": "futures_behavior_10syms_metadata_probe@1",
    "generated_utc_start": None,
    "generated_utc_end": None,
    "config": {
        "primary_host": PRIMARY_HOST,
        "fallback_host": FALLBACK_HOST,
        "dataset": DATASET,
        "max_requests": MAX_REQUESTS,
        "max_attempts_per_request": MAX_ATTEMPTS,
        "planned_request_count": None,
        "sequential": True,
        "data_downloaded_bytes": 0,
        "forbidden_endpoints_not_called": [
            "timeseries.get_range", "batch.submit_job", "live.*",
        ],
        "not_run_doc_unclear": [
            "whoami/account endpoint — not present in official client API "
            "surface or docs nav; authentication verified via authenticated "
            "metadata calls (HTTP 200 vs 401)",
        ],
    },
    "requests": {},      # rid -> record
    "order": [],         # execution order of rids
    "gate": None,
    "aggregates": None,
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
    """Scrub the key value and any token-like substring; never raises."""
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

def _open(request: urllib.request.Request):
    return urllib.request.urlopen(request, timeout=ATTEMPT_TIMEOUT_S)


def rpc(rid: str, endpoint: str, params: dict, post: bool, phase: str,
        line_id: str, note: str = "") -> dict:
    """One logical request (<= MAX_ATTEMPTS attempts). Returns the record.

    Auth: HTTP Basic, username=<key>, password="" — exactly like the
    official client (databento/common/http.py, basic_auth=True). The key
    never appears in params, URLs, logs, or the results file.
    """
    started = now_utc()
    rec: dict = {
        "rid": rid, "phase": phase, "line_id": line_id, "endpoint": endpoint,
        "http_method": "POST" if post else "GET",
        "params": {k: v for k, v in params.items()},  # no credentials inside
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
        host = hosts[0] if attempt <= 2 else hosts[-1]  # last retry on legacy
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
            with _open(req) as resp:
                status = resp.status
                raw = resp.read()  # metadata JSON only (counts/sizes/prices)
            rec["elapsed_ms"] = int((time.monotonic() - t0) * 1000)
            rec["http_status"] = status
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:  # noqa: BLE001 — non-JSON body summary only
                payload = {"_non_json_len_bytes": len(raw)}
            rec["payload"] = payload
            rec["result_summary"] = summarize(endpoint, payload)
            rec["ts_end_utc"] = now_utc()
            break
        except urllib.error.HTTPError as exc:
            # 4xx terminal (typed); 429/5xx retried. Body snippet scrubbed.
            snippet = ""
            try:
                snippet = exc.read().decode("utf-8", "replace")[:400]
            except Exception:  # noqa: BLE001
                snippet = "<unreadable>"
            last_err = f"HTTP {exc.code}: {snippet}"
            rec["http_status"] = exc.code
            if exc.code < 500 and exc.code != 429:
                rec["error_redacted"] = redact(last_err)
                rec["ts_end_utc"] = now_utc()
                break
        except Exception as exc:  # noqa: BLE001 — network-level
            last_err = f"{type(exc).__name__}: {exc}"
        if attempt < MAX_ATTEMPTS:
            time.sleep(BACKOFF_S[min(attempt - 1, len(BACKOFF_S) - 1)])
    else:
        rec["error_redacted"] = redact(last_err or "unknown error")
        rec["ts_end_utc"] = now_utc()

    RESULTS["requests"][rid] = rec
    RESULTS["order"].append(rid)
    status_str = (f"{rec['http_status']} " if rec["http_status"] else "")
    ok = rec["http_status"] == 200
    print(f"[{rid}] {status_str}{endpoint} {rec['params'].get('schema', '')} "
          f"{rec['params'].get('symbols', '')[:60]} "
          f"{'OK' if ok else 'ERR ' + (rec['error_redacted'] or '')[:120]}")
    flush_out()
    time.sleep(SLEEP_BETWEEN_S)
    return rec


# -------------------------------------------------------------- summaries ---

def summarize(endpoint: str, payload) -> str:
    """Human-readable, credential-free summary of a metadata payload."""
    try:
        if endpoint == "metadata.list_datasets":
            lst = payload if isinstance(payload, list) else []
            return (f"{len(lst)} datasets; GLBX.MDP3 present: "
                    f"{'GLBX.MDP3' in lst}")
        if endpoint == "metadata.list_schemas":
            lst = payload if isinstance(payload, list) else []
            has_eod = "ohlcv-eod" in [str(s) for s in lst]
            return f"schemas={lst}; ohlcv-eod present: {has_eod}"
        if endpoint == "metadata.get_dataset_range":
            return f"dataset_range={json.dumps(payload)[:200]}"
        if endpoint == "metadata.list_unit_prices":
            return (f"unit_prices rows={len(payload)} "
                    f"(raw stored; parse at aggregation)")
        if endpoint == "metadata.get_record_count":
            return f"record_count={payload}"
        if endpoint == "metadata.get_billable_size":
            return f"billable_size_bytes={payload}"
        if endpoint == "metadata.get_cost":
            return f"cost_usd={payload}"
        if endpoint == "symbology.resolve":
            res = payload.get("result", {}) if isinstance(payload, dict) else {}
            counts = {str(k): len(v) for k, v in res.items()}
            nf = payload.get("not_found", []) if isinstance(payload, dict) else []
            return (f"resolved_symbols={len(res)}; "
                    f"intervals_per_symbol={counts}; "
                    f"not_found={list(nf)[:10]}")
        return f"type={type(payload).__name__}"
    except Exception as exc:  # noqa: BLE001
        return f"summary_error:{type(exc).__name__}"


# ----------------------------------------------------------- request plan ---

def parent_list(roots: list[str]) -> str:
    return ",".join(PARENT[r] for r in roots)


def rc_params(symbols: str, schema: str, start: str, end: str,
              stype_in: str = "parent") -> dict:
    # Mirrors official client get_record_count body (no stype_out).
    return {"dataset": DATASET, "symbols": symbols, "schema": schema,
            "start": start, "end": end, "stype_in": stype_in}


def bs_params(symbols: str, schema: str, start: str, end: str,
              stype_in: str = "parent") -> dict:
    # Mirrors official client get_billable_size body (stype_out=instrument_id).
    return {**rc_params(symbols, schema, start, end, stype_in),
            "stype_out": "instrument_id"}


def build_plan(manifest: dict) -> list[dict]:
    """The exact 80-request plan (deterministic order). CC2 (second get_cost
    cross-check) is filled at runtime from the largest PILOT-04 window."""
    lines = {ln["line_id"]: ln for ln in manifest["lines"]}
    plan: list[dict] = []

    def add(endpoint, params, post, phase, line_id, note=""):
        plan.append({"endpoint": endpoint, "params": params, "post": post,
                     "phase": phase, "line_id": line_id, "note": note})

    # -- Phase A: account/dataset/price metadata (4) -------------------------
    add("metadata.list_datasets", {}, False, "A", "P0-1",
        "auth check + dataset list")
    add("metadata.list_schemas", {"dataset": DATASET}, False, "A", "P0-1",
        "schema set; ohlcv-eod presence check")
    add("metadata.get_dataset_range", {"dataset": DATASET}, False, "A", "P0-1",
        "coverage range GIVEN entitlements")
    add("metadata.list_unit_prices", {"dataset": DATASET}, False, "A", "P0-2",
        "USD/GB per schema per mode; the only price authority")

    # -- PILOT block (61) -----------------------------------------------------
    p06 = lines["PILOT-06"]
    add("symbology.resolve", {
        "dataset": DATASET,
        "symbols": ",".join(f"{r}.{s}.0" for r in ("NQ", "CL")
                            for s in ("c", "n", "v")),
        "stype_in": "continuous", "stype_out": "raw_symbol",
        "start_date": p06["date_spec"]["start"],
        "end_date": p06["date_spec"]["end"],
    }, True, "PILOT", "PILOT-06", "vendor roll tables (FREE endpoint)")

    for lid in ("PILOT-01", "PILOT-02"):
        ln = lines[lid]
        sch = ln["schemas"][0]["name"]
        ds = ln["date_spec"]
        sym = parent_list(ln["symbols"])
        add("metadata.get_record_count",
            rc_params(sym, sch, ds["start"], ds["end"]), True, "PILOT", lid)
        add("metadata.get_billable_size",
            bs_params(sym, sch, ds["start"], ds["end"]), True, "PILOT", lid)

    ln = lines["PILOT-02"]  # cost cross-check #1 on a full PILOT line shape
    ds = ln["date_spec"]
    add("metadata.get_cost",
        bs_params(parent_list(ln["symbols"]), ln["schemas"][0]["name"],
                  ds["start"], ds["end"]),
        True, "PILOT", "PILOT-02", "get_cost cross-check vs bs*unit_price")

    ln = lines["PILOT-03"]  # ohlcv-1d windows: billable size per window
    sym = parent_list(ln["symbols"])
    sch = ln["schemas"][0]["name"]
    for w in ln["date_spec"]["windows"]:
        add("metadata.get_billable_size",
            bs_params(sym, sch, w["start"], w["end"]), True, "PILOT",
            "PILOT-03", f"window {w['label']}")

    ln = lines["PILOT-04"]  # ohlcv-1m windows: rc + bs per window
    sch = ln["schemas"][0]["name"]
    for w in ln["date_spec"]["windows"]:
        sym = ",".join(w["symbols"])
        add("metadata.get_record_count",
            rc_params(sym, sch, w["start"], w["end"], "raw_symbol"),
            True, "PILOT", "PILOT-04", f"window {w['label']}")
        add("metadata.get_billable_size",
            bs_params(sym, sch, w["start"], w["end"], "raw_symbol"),
            True, "PILOT", "PILOT-04", f"window {w['label']}")

    ln = lines["PILOT-05"]  # bbo-1m windows: billable size per window
    sch = ln["schemas"][0]["name"]
    for w in ln["date_spec"]["windows"]:
        sym = ",".join(w["symbols"])
        add("metadata.get_billable_size",
            bs_params(sym, sch, w["start"], w["end"], "raw_symbol"),
            True, "PILOT", "PILOT-05", f"window {w['label']}")

    # (get_cost cross-check #2 inserted at runtime after the PILOT-04 loop)

    # -- EXPANSION block (19) -------------------------------------------------
    for lid in ("EXP-01", "EXP-02", "EXP-03"):
        ln = lines[lid]
        ds = ln["date_spec"]
        sch = ln["schemas"][0]["name"]
        sym = parent_list(ln["symbols"])
        add("metadata.get_record_count",
            rc_params(sym, sch, ds["start"], ds["end"]), True,
            "EXPANSION", lid, "joined 10 roots")
        add("metadata.get_billable_size",
            bs_params(sym, sch, ds["start"], ds["end"]), True,
            "EXPANSION", lid, "joined 10 roots")

    ln = lines["EXP-04"]  # ohlcv-1m tier-A: per-root rc + joined bs
    ds = ln["date_spec"]
    sch = ln["schemas"][0]["name"]
    for r in ln["symbols"]:
        add("metadata.get_record_count",
            rc_params(PARENT[r], sch, ds["start"], ds["end"]), True,
            "EXPANSION", "EXP-04", f"per-root {r} full line window")
    add("metadata.get_billable_size",
        bs_params(parent_list(ln["symbols"]), sch, ds["start"], ds["end"]),
        True, "EXPANSION", "EXP-04", "joined NQ,ES,CL,NG")

    ln = lines["EXP-05"]  # ohlcv-1m tier-B: per-root rc + joined bs
    ds = ln["date_spec"]
    sch = ln["schemas"][0]["name"]
    for r in ln["symbols"]:
        add("metadata.get_record_count",
            rc_params(PARENT[r], sch, ds["start"], ds["end"]), True,
            "EXPANSION", "EXP-05", f"per-root {r} full line window")
    add("metadata.get_billable_size",
        bs_params(parent_list(ln["symbols"]), sch, ds["start"], ds["end"]),
        True, "EXPANSION", "EXP-05", "joined GC,SI,6E,6J,6B,6A")

    e09 = lines["EXP-09"]
    add("symbology.resolve", {
        "dataset": DATASET,
        "symbols": ",".join(f"{r}.{s}.0" for r in ALL_ROOTS
                            if r not in ("NQ", "CL")
                            for s in ("c", "n", "v")),
        "stype_in": "continuous", "stype_out": "raw_symbol",
        "start_date": e09["date_spec"]["start"],
        "end_date": e09["date_spec"]["end"],
    }, True, "EXPANSION", "EXP-09", "vendor roll tables (FREE endpoint)")

    # P0-3-style earliest-window coverage probes (joined roots x schema at the
    # 2010-06-01..2010-09-30 window): NOT_RUN this round — the 80-request cap
    # is fully consumed by the manifest lines + 2 get_cost cross-checks.
    # Partial compensation recorded in aggregates.notes: get_dataset_range
    # (entitlement-aware dataset range) + full-line-window record counts.
    # EXP-06/07/08: windows_rule / placeholder — NOT_ENUMERATED, no request.
    return plan


# ------------------------------------------------------------ aggregation ---

def unit_price_lookup(prices_payload) -> dict:
    """schema -> usd_per_gb for historical mode. Defensive; {} if absent.

    Observed payload shape (2026-10-02 run): a list of rows like
    {"mode": "historical", "unit_prices": {"ohlcv-1m": 70.0, ...}}.
    """
    out: dict = {}
    if not isinstance(prices_payload, list):
        return out
    for row in prices_payload:
        if not isinstance(row, dict):
            continue
        mode = str(row.get("mode", row.get("feed_mode", "")))
        if mode and mode != "historical":
            continue
        inner = row.get("unit_prices")
        if inner is None:
            inner = row.get("prices")
        if isinstance(inner, dict):
            for sch, val in inner.items():
                try:
                    out[str(sch)] = float(val)
                except (TypeError, ValueError):
                    pass
        else:
            sch = row.get("schema")
            for k in ("unit_price", "price", "usd_per_gb"):
                if isinstance(row.get(k), (int, float)):
                    if sch:
                        out[str(sch)] = float(row[k])
                    break
    return out


def aggregate(results: dict) -> dict:
    reqs = results["requests"]
    prices = {}
    for rid in results["order"]:
        r = reqs[rid]
        if r["endpoint"] == "metadata.list_unit_prices" and r["http_status"] == 200:
            prices = unit_price_lookup(r.get("payload"))
            break

    def line_rows(line_id: str) -> list[dict]:
        return [reqs[rid] for rid in results["order"]
                if reqs[rid]["line_id"] == line_id]

    def num(r: dict, key: str):
        p = r.get("payload")
        return p if isinstance(p, (int, float)) else None

    agg: dict = {"unit_prices_usd_per_gb_historical": prices,
                 "lines": {}, "notes": []}
    for line_id in ("PILOT-01", "PILOT-02", "PILOT-03", "PILOT-04",
                    "PILOT-05", "PILOT-06", "EXP-01", "EXP-02", "EXP-03",
                    "EXP-04", "EXP-05", "EXP-06", "EXP-07", "EXP-08",
                    "EXP-09"):
        rows = line_rows(line_id)
        if not rows:
            agg["lines"][line_id] = {"status": "NOT_RUN"}
            continue
        recs = sum(n for r in rows
                   if r["endpoint"] == "metadata.get_record_count"
                   and isinstance(n := num(r, "record_count"), (int, float)))
        # NOTE: for EXP-04/05 per-root rc rows are separate logical requests;
        # summing full-span per-root counts equals the joined count.
        bytes_total = sum(n for r in rows
                          if r["endpoint"] == "metadata.get_billable_size"
                          and isinstance(n := num(r, "billable_size"),
                                         (int, float)))
        cost_api = [n for r in rows if r["endpoint"] == "metadata.get_cost"
                    and isinstance(n := num(r, "cost"), (int, float))]
        schemas = sorted({str(r["params"].get("schema"))
                          for r in rows if r["params"].get("schema")})
        by_schema: dict = {}
        for r in rows:
            if r["endpoint"] != "metadata.get_billable_size":
                continue
            sch = str(r["params"].get("schema"))
            n = num(r, "billable_size")
            if isinstance(n, (int, float)):
                by_schema.setdefault(sch, 0)
                by_schema[sch] += n
        cost_computed = None
        if prices:
            cost_computed = round(
                sum(by_schema.get(s, 0) / GB * prices.get(s, 0.0)
                    for s in by_schema), 4)
        n_ok = sum(1 for r in rows if r["http_status"] == 200)
        derived_recs = None
        if bytes_total and not recs:
            # DERIVED (not measured): billable bytes / fixed DBN record size
            # (OhlcvMsg 56 B, BboMsg 80 B per the DBN-ADAPTER lane's spec).
            rec_size = 80 if "bbo-1m" in schemas else 56
            derived_recs = bytes_total // rec_size
        agg["lines"][line_id] = {
            "requests": len(rows), "ok": n_ok,
            "schemas": schemas,
            "record_count_sum": recs if recs else None,
            "record_count_derived_from_bytes_NOT_MEASURED": derived_recs,
            "billable_bytes_sum": bytes_total if bytes_total else None,
            "billable_gb_sum": round(bytes_total / GB, 4) if bytes_total else None,
            "cost_usd_computed_from_api_bs_x_unitprice": cost_computed,
            "cost_usd_get_cost_api": cost_api if cost_api else None,
            "errors": [r["rid"] for r in rows if r["http_status"] != 200],
        }

    def pkg(ids: list[str]) -> dict:
        recs = sum((agg["lines"][i]["record_count_sum"] or 0)
                   for i in ids if agg["lines"].get(i))
        drecs = sum((agg["lines"][i].get(
            "record_count_derived_from_bytes_NOT_MEASURED") or 0)
            for i in ids if agg["lines"].get(i))
        b = sum((agg["lines"][i]["billable_bytes_sum"] or 0)
                for i in ids if agg["lines"].get(i))
        c = sum(filter(None, (agg["lines"][i].get(
            "cost_usd_computed_from_api_bs_x_unitprice")
            for i in ids if agg["lines"].get(i))))
        return {"lines": ids, "record_count_total": recs,
                "record_count_derived_total_NOT_MEASURED": drecs,
                "billable_bytes_total": b,
                "billable_gb_total": round(b / GB, 4),
                "cost_usd_total_computed": round(c, 4)}

    agg["PILOT_package"] = pkg(["PILOT-01", "PILOT-02", "PILOT-03",
                                "PILOT-04", "PILOT-05"])
    agg["EXPANSION_package"] = pkg(["EXP-01", "EXP-02", "EXP-03", "EXP-04",
                                    "EXP-05"])

    # get_cost vs computed-cost ratio on the two cross-checked shapes
    ratios = []
    for rid in results["order"]:
        r = reqs[rid]
        if r["endpoint"] != "metadata.get_cost" or r["http_status"] != 200:
            continue
        sch = str(r["params"].get("schema"))
        price = prices.get(sch)
        api_cost = r.get("payload")
        # find the matching billable_size request (same params minus kind)
        for rid2 in results["order"]:
            r2 = reqs[rid2]
            if (r2["endpoint"] == "metadata.get_billable_size"
                    and r2["http_status"] == 200
                    and r2["params"] == r["params"]
                    and isinstance(r2.get("payload"), (int, float))
                    and isinstance(api_cost, (int, float)) and price):
                ratios.append({
                    "rid": rid, "schema": sch,
                    "get_cost_usd": api_cost,
                    "computed_bs_x_price_usd":
                        round(r2["payload"] / GB * price, 6),
                    "ratio_get_cost_over_computed":
                        round(api_cost / (r2["payload"] / GB * price), 4),
                })
                break
    agg["get_cost_cross_checks"] = ratios
    agg["notes"] = [
        "cost_usd_computed = sum(get_billable_size)/1e9 x unit_price"
        "(schema, historical mode) — the request manifest's own method; "
        "cross-checked against metadata.get_cost where called.",
        "get_cost != purchase; quotes reflect current prices and any "
        "account discounts at probe time; credits are not free spend.",
        "end dates are EXCLUSIVE per API semantics — manifest windows are "
        "passed verbatim, so the final strip windows cover through "
        "2026-09-30 only; delivery-time chunk re-probe discipline applies.",
        "EXP-06/07/08 NOT_ENUMERATED by manifest (windows depend on inputs "
        "not yet in hand); EXP-08 placeholder not requested this round.",
        "Record counts for PILOT-05 (bbo-1m) NOT_RUN (request-cap bound); "
        "billable size and cost were measured.",
        "P0-3 earliest-window coverage probes (per root x schema at fixed "
        "2010/2012/2015/2019/2021 windows) NOT_RUN this round — request cap "
        "consumed by manifest lines; per-root coverage partially evidenced by "
        "EXP-04/05 per-root full-window record counts and get_dataset_range.",
        "Parent stype symbols sent as {ROOT}.FUT (docs symbology page) — a "
        "correction to the prepared probe scripts, which pass bare roots.",
    ]
    return agg


# ------------------------------------------------------------------- main ---

def gate_ok() -> tuple[bool, str | None]:
    """EXPANSION proceeds only if PILOT metadata came back clean of
    auth/entitlement failures (no 401/403 anywhere so far)."""
    for rid in RESULTS["order"]:
        r = RESULTS["requests"][rid]
        if r["http_status"] in (401, 403):
            if r["http_status"] == 401:
                return False, "BLOCKED_AUTH"
            return False, "BLOCKED_NO_ENTITLEMENT"
    return True, None


def main() -> int:
    RESULTS["generated_utc_start"] = now_utc()
    manifest = json.loads(MANIFEST_PATH.read_text())
    plan = build_plan(manifest)
    RESULTS["config"]["planned_request_count"] = len(plan) + 1  # +1 CC2
    print(f"# probe_metadata — {len(plan) + 1} planned logical requests "
          f"(hard cap {MAX_REQUESTS}), sequential, metadata-only")
    print(f"# manifest (READ-ONLY): {MANIFEST_PATH}")
    print(f"# output: {OUT_PATH}")

    n = 0
    cc2_done = False
    for spec in plan:
        if n >= MAX_REQUESTS:
            break
        # Insert get_cost cross-check #2 after the PILOT-05 block.
        if (not cc2_done and spec["phase"] == "EXPANSION"
                and n + 1 < MAX_REQUESTS):
            best = None
            for rid in RESULTS["order"]:
                r = RESULTS["requests"][rid]
                if (r["line_id"] == "PILOT-04"
                        and r["endpoint"] == "metadata.get_billable_size"
                        and isinstance(r.get("payload"), (int, float))
                        and (best is None or r["payload"] > best[1])):
                    best = (r, r["payload"])
            if best:
                src = best[0]
                rpc(f"R{n + 1:03d}", "metadata.get_cost",
                    dict(src["params"]), True, "PILOT", "PILOT-04",
                    "get_cost cross-check on largest PILOT-04 window")
                n += 1
            cc2_done = True
        rpc(f"R{n + 1:03d}", spec["endpoint"], spec["params"],
            spec["post"], spec["phase"], spec["line_id"], spec["note"])
        n += 1
        if spec["line_id"] == "PILOT-05" and spec is plan[
                [i for i, s in enumerate(plan)
                 if s["line_id"] == "PILOT-05"][-1]]:
            ok, blocker = gate_ok()
            RESULTS["gate"] = {
                "after": "PILOT block", "clean": ok,
                "blocker": blocker,
                "expansion_executed": ok,
            }
            if not ok:
                RESULTS["aggregates"] = aggregate(RESULTS)
                flush_out()
                print(f"# GATE: PILOT not clean ({blocker}) — EXPANSION "
                      f"skipped. Typed blocker recorded.")
                return 5

    RESULTS["gate"] = {"after": "PILOT block", "clean": True,
                       "blocker": None, "expansion_executed": True}
    RESULTS["aggregates"] = aggregate(RESULTS)
    flush_out()
    n_err = sum(1 for rid in RESULTS["order"]
                if RESULTS["requests"][rid]["http_status"] != 200)
    print(f"# done: {len(RESULTS['order'])} logical requests, "
          f"{n_err} non-200. Zero data bytes downloaded "
          f"(metadata-only endpoints).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
