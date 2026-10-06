#!/usr/bin/env python3
"""probe_cost.py — METADATA-ONLY cost probe for the Databento request manifest
(FUTURES-BEHAVIOR-10SYMS-PREP-20261002, lane REQUEST-PACKET).

What it does (when actually run with an owner key), per DATA_ACQUISITION_SPEC
§6 and the metered-pricing docs (access 2026-10-02):
  1. Historical.metadata.list_unit_prices(dataset="GLBX.MDP3")   — free
     ("US dollars per gigabyte" per schema per mode). The ONLY legitimate
     price source; nothing in this repo invents prices.
  2. Historical.metadata.get_billable_size(...) per concrete request line —
     free; returns billable UNCOMPRESSED bytes for the exact request, no
     data. Vendor caveat: estimates may be inaccurate for ranges that are
     not discrete multiples of 10 minutes (definition: multiples of 24h).
  3. cost estimate per line = billable_GB x unit_price[mode=historical]
     [schema] — computed ONLY from values actually returned by those calls.

Optionally also P0-1 re-confirmation: metadata.list_datasets /
list_schemas / get_dataset_range (all free) via --phase0.

What it NEVER does: get_range, batch jobs, downloads, live sessions.

Security: API key ONLY from env DATABENTO_API_KEY; never a CLI argument;
output is redacted against the env key.

Backends: auto (lib if importable else http) / lib / http.
  Installed status 2026-10-02: `databento` NOT installed in .venv
  (pip show databento -> not found). The http backend uses stdlib only
  against the documented raw routes (GET .../v0/metadata.list_unit_prices,
  .../v0/metadata.get_billable_size) with HTTP Basic auth user=<key>
  password=''. Raw-route conventions must be confirmed on the first live
  Phase-0 call; the library backend is authoritative when available.

Usage:
  python3 probe_cost.py --dry-run                 # exact requests, no network
  python3 probe_cost.py --dry-run --phase0        # + P0-1 dataset probes
  python3 probe_cost.py --dry-run --lines PILOT-04 EXP-04

  export DATABENTO_API_KEY=db-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
  python3 probe_cost.py --phase0 --out reports/cost_table.json

Exit codes: 0 ok (dry-run ok) · 2 missing key on real run · 3 backend/HTTP
failure · 4 manifest missing/invalid.

Status this round (2026-10-02): NOT_RUN — every price/quote anywhere in this
repo is NOT_RUN_NO_CALL; this script made zero network calls.
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
DEFAULT_BASE_URL = "https://databento.com"
DATASET = "GLBX.MDP3"
GB = 1_000_000_000.0  # decimal GB, the unit the vendor prices in (docs: $/GB)

# Data schemas (exact match — substring matching is forbidden: "symbology"
# contains "mbo"). Symbology-only lines are FREE (no billable size).
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
    """Concrete get_billable_size requests per manifest line (same expansion
    rule as probe_record_count.py)."""
    reqs: list[dict] = []
    stype = line.get("stype_in", "parent")
    symbols = line.get("symbols", [])
    for sch in line.get("schemas", []):
        name = sch.get("name", "")
        if not is_data_schema(name):
            continue  # symbology.resolve-only lines are FREE and cost nothing
        date_spec = line.get("date_spec", {})
        if "windows_rule" in date_spec:
            reqs.append({
                "line_id": line["line_id"], "schema": name, "stype_in": stype,
                "symbols": symbols, "window_label": "NOT_ENUMERATED",
                "start": None, "end": None,
                "note": "enumerate windows after PILOT acceptance / roll tables; "
                        "probe billable size then",
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


def redact(text: str) -> str:
    key = os.environ.get("DATABENTO_API_KEY", "")
    if key and key in text:
        text = text.replace(key, "db-REDACTED")
    return text


# ------------------------------------------------------------------ http ----

def _http_get(path: str, params: dict, key: str) -> dict:
    qs = urllib.parse.urlencode(params)
    url = f"{DEFAULT_BASE_URL}{path}?{qs}"
    request = urllib.request.Request(url, method="GET")
    import base64 as _b64
    token = _b64.b64encode(f"{key}:".encode()).decode()
    request.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(request, timeout=60) as resp:
        return json.loads(resp.read().decode())


def http_get_billable_size(req: dict, key: str) -> int:
    payload = _http_get("/v0/metadata.get_billable_size", {
        "dataset": DATASET,
        "start": req["start"], "end": req["end"],
        "symbols": ",".join(req["symbols"]),
        "schema": req["schema"], "stype_in": req["stype_in"],
    }, key)
    if isinstance(payload, dict):
        return int(payload.get("billable_size", payload.get("size", -1)))
    return int(payload)


def http_list_unit_prices(key: str) -> dict:
    return _http_get("/v0/metadata.list_unit_prices", {"dataset": DATASET}, key)


# ------------------------------------------------------------------- lib ----

def lib_available() -> bool:
    try:
        import databento  # noqa: F401
        return True
    except ImportError:
        return False


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--dry-run", action="store_true",
                    help="print the exact requests that would be made; no network")
    ap.add_argument("--phase0", action="store_true",
                    help="also P0-1: list_datasets / list_schemas / get_dataset_range")
    ap.add_argument("--lines", nargs="*", default=None)
    ap.add_argument("--backend", choices=["auto", "lib", "http"], default="auto")
    ap.add_argument("--out", default=None,
                    help="write results JSON here on a REAL run (relative to this dir)")
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

    use_lib = (args.backend == "lib") or (args.backend == "auto" and lib_available())
    if args.backend == "lib" and not lib_available():
        print("FATAL: --backend lib but databento is not importable.", file=sys.stderr)
        return 3

    print(f"# probe_cost — {len(reqs)} billable-size requests + 1 list_unit_prices "
          f"(dry_run={args.dry_run}, phase0={args.phase0}, backend={args.backend})")
    print(f"# manifest: {MANIFEST_PATH}")
    print(f"# cost = billable_GB x unit_price(USD/GB, historical mode); every price "
          f"NOT_RUN_NO_CALL until list_unit_prices actually returns it.")
    print(f"# key via env DATABENTO_API_KEY only; output redacted.")

    if args.dry_run:
        print("[unit-prices] GET "
              f"{DEFAULT_BASE_URL}/v0/metadata.list_unit_prices?dataset=GLBX.MDP3")
        if args.phase0:
            print("[P0-1a] GET /v0/metadata.list_datasets")
            print("[P0-1b] GET /v0/metadata.list_schemas?dataset=GLBX.MDP3")
            print("[P0-1c] GET /v0/metadata.get_dataset_range?dataset=GLBX.MDP3")
        for r in reqs:
            print(f"[{r['line_id']:9s}] {r['schema']:11s} {r['stype_in']:10s} "
                  f"{r['window_label']}")
            if r["start"] is None:
                print(f"            # NO REQUEST YET — {r['note']}")
            else:
                print("            GET "
                      f"{DEFAULT_BASE_URL}/v0/metadata.get_billable_size?"
                      f"dataset=GLBX.MDP3&start={r['start']}&end={r['end']}"
                      f"&symbols={','.join(r['symbols'])}"
                      f"&schema={r['schema']}&stype_in={r['stype_in']}")
        print(f"# DRY-RUN COMPLETE: 0 network calls. "
              f"{len(reqs)} billable-size requests + 1 unit-price request enumerated.")
        return 0

    key = os.environ.get("DATABENTO_API_KEY", "").strip()
    if not key:
        print("FATAL: DATABENTO_API_KEY not set (real run). Export it in the "
              "environment; never pass it as an argument.", file=sys.stderr)
        return 2

    client = None
    if use_lib:
        import databento as db
        client = db.Historical(key)

    blob: dict = {
        "schema": "futures_behavior_10syms_cost_table@1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "backend": "lib" if use_lib else "http",
        "dataset": DATASET,
        "unit_prices": None,
        "results": [],
    }

    # 1) unit prices (the only price authority)
    try:
        if use_lib:
            prices = client.metadata.list_unit_prices(dataset=DATASET)
        else:
            prices = http_list_unit_prices(key)
        blob["unit_prices"] = prices
        print(f"[unit-prices] OK ({len(prices) if isinstance(prices, list) else 'dict'}) "
              f"— captured at run time; treat as of this date.")
    except Exception as exc:  # noqa: BLE001
        print(f"[unit-prices] ERROR {redact(str(exc))} — no cost computed.",
              file=sys.stderr)
        blob["unit_prices_error"] = redact(str(exc))

    def usd_per_gb(schema: str, prices) -> float | None:
        """Extract historical-mode unit price for a schema from list_unit_prices
        output. Tolerates list-of-dicts and dict-of-dicts shapes; returns None
        when absent (then NO cost is computed for that line — never guessed)."""
        if prices is None:
            return None
        rows = prices if isinstance(prices, list) else prices.get("prices", prices)
        best = None
        if isinstance(rows, list):
            for row in rows:
                if str(row.get("schema", row.get("name", ""))) == schema:
                    if str(row.get("mode", "")) == "historical" or "mode" not in row:
                        best = row
                        if str(row.get("mode", "")) == "historical":
                            break
        elif isinstance(rows, dict):
            node = rows.get(schema)
            if isinstance(node, dict):
                best = node.get("historical", node)
        if not best:
            return None
        for k in ("price", "unit_price", "usd_per_gb", "cost_per_gb"):
            if k in best:
                return float(best[k])
        return None

    failures = 0
    for r in reqs:
        if r["start"] is None:
            blob["results"].append({**r, "billable_size_bytes": "NOT_ENUMERATED",
                                    "est_cost_usd": "NOT_ENUMERATED"})
            continue
        try:
            if use_lib:
                size = int(client.metadata.get_billable_size(
                    dataset=DATASET,
                    start=dt.datetime.fromisoformat(r["start"]),
                    end=dt.datetime.fromisoformat(r["end"]),
                    symbols=r["symbols"], schema=r["schema"],
                    stype_in=r["stype_in"]))
            else:
                size = http_get_billable_size(r, key)
            price = usd_per_gb(r["schema"], blob.get("unit_prices"))
            cost = round(size / GB * price, 2) if price is not None else "PRICE_NOT_RETURNED"
            blob["results"].append({**r, "billable_size_bytes": size,
                                    "est_cost_usd": cost})
            print(f"[{r['line_id']:9s}] {r['schema']:11s} {r['window_label']}: "
                  f"{size:,} B ≈ {size / GB:.3f} GB → {cost} USD")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            blob["results"].append({**r, "billable_size_bytes": None,
                                    "error": redact(str(exc))})
            print(f"[{r['line_id']:9s}] {r['schema']:11s} {r['window_label']}: "
                  f"ERROR {redact(str(exc))}", file=sys.stderr)

    if args.out:
        out_path = (SCRIPT_DIR / args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(blob, indent=1))
        digest = hashlib.sha256(redact(json.dumps(blob)).encode()).hexdigest()
        print(f"# wrote {out_path} (sha256(redacted)={digest[:16]}...)")

    print(f"# done: {len(blob['results'])} lines, {failures} failures. "
          f"Every number above came from a live metadata call at run time.")
    return 3 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
