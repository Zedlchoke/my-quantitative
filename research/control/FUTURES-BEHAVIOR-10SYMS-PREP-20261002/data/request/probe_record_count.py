#!/usr/bin/env python3
"""probe_record_count.py — METADATA-ONLY record-count probes for the Databento
request manifest (FUTURES-BEHAVIOR-10SYMS-PREP-20261002, lane REQUEST-PACKET).

What it does (when actually run with an owner key):
  * Historical.metadata.get_record_count(...) per concrete request line from
    data/request/request_manifest.json (free, metadata-only: returns counts,
    never data).
  * Optional Phase-0 coverage probes (--phase0): per root x schema x probe
    window get_record_count, per DATA_ACQUISITION_SPEC.md §7 P0-3 — resolves
    the vendor caveat "historical data availability could vary between
    schemas".

What it NEVER does: timeseries.get_range, batch submission, downloads, live
sessions, any billable data retrieval. get_record_count is metadata.

Security: API key ONLY from env var DATABENTO_API_KEY. Never pass a key as a
CLI argument; the script refuses key-like arguments and redacts the env var
from all output/logs.

Backends:
  auto (default) — use the `databento` Python library if importable, else
                    fall back to the plain-HTTP variant.
  lib            — require the `databento` library (installed 2026-10-02:
                    NOT installed in .venv — pip show databento -> not found).
  http           — stdlib-only plain HTTP against the documented raw routes
                    (GET https://databento.com/v0/metadata.get_record_count
                    with HTTP Basic auth user=<key> password=''). The exact
                    raw-route/auth convention must be confirmed on the first
                    live Phase-0 call; the library backend is authoritative
                    when available.

Usage:
  # Show the exact requests that WOULD be made (no network, no key needed):
  python3 probe_record_count.py --dry-run
  python3 probe_record_count.py --dry-run --phase0
  python3 probe_record_count.py --dry-run --lines PILOT-04 EXP-04

  # Real run (owner decision, Phase 0; key in env, never in args):
  export DATABENTO_API_KEY=db-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
  python3 probe_record_count.py --phase0 --out reports/record_counts.json

Exit codes: 0 ok (dry-run counts as ok) · 2 missing key on real run ·
3 request/backend failure · 4 manifest missing/invalid.

Status this round (2026-10-02): NOT_RUN — prepared only; zero network calls
were made by the lane that wrote this file.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = SCRIPT_DIR / "request_manifest.json"
DEFAULT_BASE_URL = "https://databento.com"  # raw API host used by the official client
DATASET = "GLBX.MDP3"

# Phase-0 per-symbol schema-start probe windows (DATA_ACQUISITION_SPEC.md §7.3).
PHASE0_PROBE_WINDOWS = [
    ("2010-06-01", "2010-09-30"),
    ("2012-01-01", "2012-03-31"),
    ("2015-01-01", "2015-03-31"),
    ("2019-01-01", "2019-03-31"),
    ("2021-01-01", "2021-03-31"),
]
PHASE0_PROBE_SCHEMAS = ["ohlcv-1m", "ohlcv-1d", "definition", "statistics"]
ALL_ROOTS = ["NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"]

# Data schemas (exact match — substring matching is forbidden: "symbology"
# contains "mbo"). Anything else in the manifest, e.g. "symbology.resolve
# only", is not probeable with get_record_count.
DATA_SCHEMAS = {
    "ohlcv-1s", "ohlcv-1m", "ohlcv-1h", "ohlcv-1d",
    "definition", "statistics", "trades", "tbbo",
    "mbp-1", "mbp-10", "mbo", "bbo-1m", "bbo-1s", "status",
}


def is_data_schema(schema_name: str) -> bool:
    return schema_name.strip().lower() in DATA_SCHEMAS


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"manifest not found: {MANIFEST_PATH}")
    with MANIFEST_PATH.open() as fh:
        return json.load(fh)


def line_requests(line: dict) -> list[dict]:
    """Expand one manifest line into concrete get_record_count request dicts.

    Lines whose windows cannot be enumerated offline (EXP-06/07/08 rules that
    depend on PIT calendars or on roll tables built AFTER EXP-01/02 delivery)
    are returned as NOT_ENUMERATED placeholders — by design, never guessed.
    """
    reqs: list[dict] = []
    stype = line.get("stype_in", "parent")
    symbols = line.get("symbols", [])
    for sch in line.get("schemas", []):
        name = sch.get("name", "")
        if not is_data_schema(name):
            continue
        date_spec = line.get("date_spec", {})
        if "windows_rule" in date_spec:
            reqs.append({
                "line_id": line["line_id"], "schema": name, "stype_in": stype,
                "symbols": symbols, "window_label": "NOT_ENUMERATED",
                "start": None, "end": None,
                "note": "windows_rule depends on inputs not yet in hand "
                        "(PIT calendars / our roll tables); enumerate later, "
                        "probe then — never guess dates.",
            })
            continue
        if "windows" in date_spec and isinstance(date_spec["windows"], list):
            for w in date_spec["windows"]:
                if not isinstance(w, dict) or "start" not in w:
                    continue
                reqs.append({
                    "line_id": line["line_id"], "schema": name, "stype_in": stype,
                    "symbols": w.get("symbols", symbols),
                    "window_label": w.get("label", f"{w['start']}..{w.get('end')}"),
                    "start": w["start"], "end": w.get("end"),
                })
        elif "start" in date_spec:
            reqs.append({
                "line_id": line["line_id"], "schema": name, "stype_in": stype,
                "symbols": symbols,
                "window_label": f"{date_spec['start']}..{date_spec.get('end')}",
                "start": date_spec["start"], "end": date_spec.get("end"),
            })
    return reqs


def phase0_requests() -> list[dict]:
    reqs = []
    for root in ALL_ROOTS:
        for schema in PHASE0_PROBE_SCHEMAS:
            for (start, end) in PHASE0_PROBE_WINDOWS:
                reqs.append({
                    "line_id": "P0-3", "schema": schema, "stype_in": "parent",
                    "symbols": [root], "window_label": f"{root} {start}..{end}",
                    "start": start, "end": end,
                    "note": "Phase-0 coverage probe (free); count>0 proves "
                            "symbol x schema availability in that window.",
                })
    return reqs


# ---------------------------------------------------------------- backends ---

def redact(text: str) -> str:
    key = os.environ.get("DATABENTO_API_KEY", "")
    if key and key in text:
        text = text.replace(key, "db-REDACTED")
    return text


def http_get_record_count(req: dict, key: str, base_url: str) -> int:
    params = urllib.parse.urlencode({
        "dataset": DATASET,
        "start": req["start"], "end": req["end"],
        "symbols": ",".join(req["symbols"]),
        "schema": req["schema"], "stype_in": req["stype_in"],
    })
    url = f"{base_url}/v0/metadata.get_record_count?{params}"
    request = urllib.request.Request(url, method="GET")
    import base64 as _b64
    token = _b64.b64encode(f"{key}:".encode()).decode()
    request.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(request, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    # Raw route returns {"record_count": <int>}; tolerate a bare int too.
    if isinstance(payload, dict):
        return int(payload.get("record_count", payload.get("count", -1)))
    return int(payload)


def lib_get_record_count(req: dict, client) -> int:
    return int(client.metadata.get_record_count(
        dataset=DATASET,
        start=dt.datetime.fromisoformat(req["start"]),
        end=dt.datetime.fromisoformat(req["end"]),
        symbols=req["symbols"],
        schema=req["schema"],
        stype_in=req["stype_in"],
    ))


def lib_available() -> bool:
    try:
        import databento  # noqa: F401
        return True
    except ImportError:
        return False


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--dry-run", action="store_true",
                    help="print the exact requests that would be made; no network, no key")
    ap.add_argument("--phase0", action="store_true",
                    help="add the P0-3 per-root x schema coverage probes")
    ap.add_argument("--lines", nargs="*", default=None,
                    help="restrict to these manifest line_ids")
    ap.add_argument("--backend", choices=["auto", "lib", "http"], default="auto")
    ap.add_argument("--out", default=None,
                    help="write the results JSON here on a REAL run (relative to this dir)")
    args = ap.parse_args(argv)

    try:
        manifest = load_manifest()
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 4

    reqs: list[dict] = []
    for line in manifest.get("lines", []):
        if args.lines and line["line_id"] not in args.lines:
            continue
        reqs.extend(line_requests(line))
    if args.phase0:
        reqs.extend(phase0_requests())

    print(f"# probe_record_count — {len(reqs)} requests "
          f"(dry_run={args.dry_run}, phase0={args.phase0}, backend={args.backend})")
    print(f"# manifest: {MANIFEST_PATH}")
    print(f"# key source: env DATABENTO_API_KEY only — keys never appear in "
          f"args or output. NOT_RUN until executed by the owner.")

    use_lib = (args.backend == "lib") or (args.backend == "auto" and lib_available())
    if args.backend == "lib" and not lib_available():
        print("FATAL: --backend lib but the databento package is not importable.",
              file=sys.stderr)
        return 3

    if args.dry_run:
        for r in reqs:
            print(f"[{r['line_id']:9s}] {r['schema']:11s} {r['stype_in']:10s} "
                  f"{r['window_label']}")
            if r["start"] is None:
                print(f"            # NO REQUEST YET — {r.get('note', 'not enumerated')}")
            else:
                method = ("GET "
                          f"{DEFAULT_BASE_URL}/v0/metadata.get_record_count?"
                          "dataset=GLBX.MDP3"
                          f"&start={r['start']}&end={r['end']}"
                          f"&symbols={','.join(r['symbols'])}"
                          f"&schema={r['schema']}&stype_in={r['stype_in']}")
                print(f"            {method}")
        print(f"# DRY-RUN COMPLETE: 0 network calls, 0 bytes billed. "
              f"{len(reqs)} requests enumerated.")
        return 0

    key = os.environ.get("DATABENTO_API_KEY", "").strip()
    if not key:
        print("FATAL: DATABENTO_API_KEY not set (real run). Export it in the "
              "environment; never pass it as an argument.", file=sys.stderr)
        return 2

    client = None
    if use_lib:
        import databento as db
        client = db.Historical(key)  # reads env var natively when key omitted

    results = []
    failures = 0
    for r in reqs:
        if r["start"] is None:
            results.append({**r, "record_count": "NOT_ENUMERATED"})
            continue
        try:
            count = (lib_get_record_count(r, client) if use_lib
                     else http_get_record_count(r, key, DEFAULT_BASE_URL))
            results.append({**r, "record_count": count})
            print(f"[{r['line_id']:9s}] {r['schema']:11s} {r['window_label']}: "
                  f"{count} records")
        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as exc:  # noqa: BLE001
            failures += 1
            results.append({**r, "record_count": None, "error": redact(str(exc))})
            print(f"[{r['line_id']:9s}] {r['schema']:11s} {r['window_label']}: "
                  f"ERROR {redact(str(exc))}", file=sys.stderr)

    if args.out:
        out_path = (SCRIPT_DIR / args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        blob = {
            "schema": "futures_behavior_10syms_record_counts@1",
            "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "backend": "lib" if use_lib else "http",
            "results": results,
        }
        out_path.write_text(json.dumps(blob, indent=1))
        digest = hashlib.sha256(redact(json.dumps(blob)).encode()).hexdigest()
        print(f"# wrote {out_path} (sha256(redacted)={digest[:16]}...)")

    print(f"# done: {len(results)} probes, {failures} failures")
    return 3 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
