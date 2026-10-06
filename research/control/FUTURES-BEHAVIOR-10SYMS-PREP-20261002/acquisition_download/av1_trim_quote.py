#!/usr/bin/env python3
"""av1_trim_quote.py — STEP 1 of ACQ-DOWNLOAD: A-v1-trim candidate quotes.

Owner authority (verbatim): 'Chốt ceiling $125 từ credit, duyệt gói A-v1-trim,
tải theo chunk. Đồng thời đẩy lên icloud luôn để tôi lưu trữ.'

Base package: acquisition_optimization/package_manifests/pkgA_variant_24m_floor.json
(A-v1 = $129.57 get_cost, 12 lines). Ceiling $125, lane hard stop $118, trim
manifest target <= $115.

METADATA-ONLY (get_cost / get_billable_size / get_record_count are free
quotes; zero data bytes, zero billing). Key law: the owner 0600 key file is
read in-process and passed ONLY to the official client constructor (Basic
Authorization header); never in env/args/logs/artifacts. All error text is
redacted with the db- token regex before any artifact write.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

import databento as db

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_QUOTES = SCRIPT_DIR / "trim_quotes.json"
OUT_MANIFEST = SCRIPT_DIR / "AV1_TRIM_MANIFEST.json"

DATASET = "GLBX.MDP3"
END = "2026-10-01"  # exclusive, same as A-v1 lines
KEY_PATH = Path(
    "/Users/hoangminhlong/.config/my-quantitative-secrets/databento-api-key")
TOKEN_RE = re.compile(r"db-[A-Za-z0-9_\-]{12,}")

BUDGET_CEILING_OWNER = 125.00     # owner ceiling (credit; treat as real money)
BUDGET_HARD_STOP_LANE = 118.00    # running committed spend must stay <= this
TRIM_TARGET = 115.00              # manifest target for the chosen trim

ROOTS_ALL = ["NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"]
PARENT = {r: f"{r}.FUT" for r in ROOTS_ALL}

# A-v1 unchanged lines (windows frozen per owner approval: 24m floor for
# NQ/ES/GC/SI, CL/NG 9m as-is, definitions+statistics 24m).
OHLCV_24M_ROOTS = ["NQ", "ES", "GC", "SI"]          # 2023-10-01..2026-10-01
OHLCV_9M_ROOTS = ["CL", "NG"]                        # 2025-10-01..2026-10-01
DEF_STAT_START = "2023-10-01"

# Trim candidates: FX (6E/6J/6B/6A) ohlcv-1m start dates (end fixed 2026-10-01).
# Every FX vendor-gated hypothesis floor is >=24m (or >=2019), so NO sub-24m
# trim keeps those literal floors; allocation therefore maximizes recent
# reference/validation depth within the budget.
CANDIDATES = {
    "C1_FX_6m": {"6E": "2026-04-01", "6J": "2026-04-01",
                 "6B": "2026-04-01", "6A": "2026-04-01"},
    "C2_FX_7m": {"6E": "2026-03-01", "6J": "2026-03-01",
                 "6B": "2026-03-01", "6A": "2026-03-01"},
    "C3_staggered_9m_6m": {"6E": "2026-01-01", "6J": "2026-01-01",
                           "6B": "2026-04-01", "6A": "2026-04-01"},
    "C4_FX_12m_REJECTED_ALT": {"6E": "2025-10-01", "6J": "2025-10-01",
                               "6B": "2025-10-01", "6A": "2025-10-01"},
}

SLEEP_BETWEEN_S = 0.35
MAX_ATTEMPTS = 3


def load_client() -> db.Historical:
    key = KEY_PATH.read_text().strip()
    if not key:
        print("FATAL: key file empty", file=sys.stderr)
        sys.exit(2)
    return db.Historical(key=key)


def redact(text: str) -> str:
    return TOKEN_RE.sub("db-REDACTED", text)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def quote_line(client: db.Historical, rid: str, *, symbols: str, schema: str,
               start: str, end: str, log: list) -> dict:
    """get_cost + get_billable_size + get_record_count for one request shape."""
    rec: dict = {"rid": rid, "dataset": DATASET, "symbols": symbols,
                 "schema": schema, "stype_in": "parent",
                 "start": start, "end": end, "end_exclusive": True,
                 "ts_utc": now_utc()}
    for name in ("get_cost", "get_billable_size", "get_record_count"):
        fn = getattr(client.metadata, name)
        params = dict(dataset=DATASET, symbols=symbols, schema=schema,
                      stype_in="parent", start=start, end=end)
        last_err = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                value = fn(**params)
                rec[name] = float(value)
                rec[f"{name}_attempts"] = attempt
                last_err = None
                break
            except Exception as exc:  # noqa: BLE001
                last_err = redact(f"{type(exc).__name__}: {exc}")[:400]
                rec[f"{name}_attempts"] = attempt
                if attempt < MAX_ATTEMPTS:
                    time.sleep(2.0 * attempt)
        if last_err is not None:
            rec[f"{name}_error_redacted"] = last_err
        time.sleep(SLEEP_BETWEEN_S)
    ok = all(k in rec for k in ("get_cost", "get_billable_size",
                                "get_record_count"))
    rec["ok"] = ok
    log.append(rec)
    print(f"  {rid}: cost={rec.get('get_cost')} bytes={rec.get('get_billable_size')} "
          f"records={rec.get('get_record_count')} ok={ok}")
    return rec


def build_lines(fx_starts: dict[str, str]) -> list[dict]:
    lines = []
    for r in ROOTS_ALL:
        if r in OHLCV_24M_ROOTS:
            start = "2023-10-01"
        elif r in OHLCV_9M_ROOTS:
            start = "2025-10-01"
        else:
            start = fx_starts[r]
        lines.append({
            "line_id": f"AV1T-O1M-{r}",
            "dataset": DATASET,
            "schema": "ohlcv-1m",
            "symbols": [PARENT[r]],
            "stype_in": "parent",
            "start": start,
            "end": END,
            "end_exclusive": True,
        })
    lines.append({
        "line_id": "AV1T-definition-ALL10",
        "dataset": DATASET,
        "schema": "definition",
        "symbols": [PARENT[r] for r in ROOTS_ALL],
        "stype_in": "parent",
        "start": DEF_STAT_START, "end": END, "end_exclusive": True,
    })
    lines.append({
        "line_id": "AV1T-statistics-ALL10",
        "dataset": DATASET,
        "schema": "statistics",
        "symbols": [PARENT[r] for r in ROOTS_ALL],
        "stype_in": "parent",
        "start": DEF_STAT_START, "end": END, "end_exclusive": True,
    })
    return lines


def main() -> int:
    client = load_client()
    log: list[dict] = []

    # 1. Quote every distinct request shape once (dedupe by params key).
    shapes: dict[str, dict] = {}

    def quote_for(line: dict, tag: str) -> dict:
        key = (line["schema"], ",".join(line["symbols"]),
               line["start"], line["end"])
        if key not in shapes:
            rid = f"{tag}:{line['line_id']}"
            shapes[key] = quote_line(client, rid, symbols=",".join(
                line["symbols"]), schema=line["schema"],
                start=line["start"], end=line["end"], log=log)
        return shapes[key]

    candidate_results: dict[str, dict] = {}
    for cand_name, fx_starts in CANDIDATES.items():
        lines = build_lines(fx_starts)
        total_cost = 0.0
        total_bytes = 0
        total_records = 0
        per_line = []
        all_ok = True
        for line in lines:
            q = quote_for(line, cand_name)
            all_ok = all_ok and q["ok"]
            total_cost += q.get("get_cost", 0.0) or 0.0
            total_bytes += int(q.get("get_billable_size", 0) or 0)
            total_records += int(q.get("get_record_count", 0) or 0)
            per_line.append({**{k: line[k] for k in
                                ("line_id", "schema", "symbols", "stype_in",
                                 "start", "end")},
                             "get_cost": q.get("get_cost"),
                             "billable_size": q.get("get_billable_size"),
                             "records": q.get("get_record_count")})
        fx_months = sum(
            (dt.date.fromisoformat(END).year - dt.date.fromisoformat(s).year)
            * 12 + dt.date.fromisoformat(END).month
            - dt.date.fromisoformat(s).month
            for s in fx_starts.values())
        candidate_results[cand_name] = {
            "fx_ohlcv_starts": fx_starts,
            "fx_ohlcv_total_months": fx_months,
            "total_get_cost": round(total_cost, 6),
            "total_billable_size": total_bytes,
            "total_records": total_records,
            "all_lines_ok": all_ok,
            "within_trim_target": all_ok and total_cost <= TRIM_TARGET,
            "within_lane_hard_stop": all_ok and total_cost <= BUDGET_HARD_STOP_LANE,
            "lines": per_line,
        }
        print(f"[{cand_name}] total=${total_cost:.4f} records={total_records:,} "
              f"bytes={total_bytes:,} within_target={total_cost <= TRIM_TARGET}")

    # 2. Choose: max FX ohlcv months among candidates within TRIM_TARGET;
    #    tie-break lower cost. Rejected candidates recorded with quotes.
    eligible = [(c, r) for c, r in candidate_results.items()
                if r["within_trim_target"]]
    eligible.sort(key=lambda cr: (-cr[1]["fx_ohlcv_total_months"],
                                  cr[1]["total_get_cost"]))
    chosen_name, chosen = (eligible[0] if eligible else (None, None))
    if chosen is None:
        print("FATAL: no candidate within trim target", file=sys.stderr)
        OUT_QUOTES.write_text(json.dumps({
            "generated_utc": now_utc(),
            "candidates": candidate_results,
            "quote_log": log,
            "chosen": None,
        }, indent=1))
        return 3

    # 3. Write artifacts.
    OUT_QUOTES.write_text(json.dumps({
        "generated_utc": now_utc(),
        "budget_law": {
            "owner_ceiling_usd": BUDGET_CEILING_OWNER,
            "lane_hard_stop_usd": BUDGET_HARD_STOP_LANE,
            "trim_target_usd": TRIM_TARGET,
            "note": "get_cost quotes the API's own charge for the exact "
                    "request incl. batched files; see client docstring "
                    "'Request the cost in US dollars for historical "
                    "streaming or batched files from Databento.'",
        },
        "candidates": candidate_results,
        "chosen": chosen_name,
        "quote_log": log,
    }, indent=1))

    manifest = {
        "schema": "futures_behavior_av1_trim_manifest@1",
        "task_id": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
        "lane": "ACQ-DOWNLOAD",
        "generated_utc": now_utc(),
        "authority": "Owner approval 2026-10-02 (ceiling $125, package "
                     "A-v1-trim, chunked download, iCloud mirror). Base: "
                     "acquisition_optimization/package_manifests/"
                     "pkgA_variant_24m_floor.json ($129.57).",
        "package": "A-v1-trim",
        "chosen_candidate": chosen_name,
        "selection_rule": "max FX ohlcv-1m months with total get_cost <= "
                          "$115.00; all FX vendor-gated floors are >=24m so "
                          "no sub-24m trim retains them (allocation "
                          "maximizes recent reference/overlap-validation "
                          "depth); NQ/ES/GC/SI 24m floor, CL/NG 9m and "
                          "definition/statistics 24m preserved as-is per "
                          "owner instruction.",
        "budget": {
            "total_get_cost_usd": chosen["total_get_cost"],
            "owner_ceiling_usd": BUDGET_CEILING_OWNER,
            "lane_hard_stop_usd": BUDGET_HARD_STOP_LANE,
            "headroom_to_hard_stop_usd": round(
                BUDGET_HARD_STOP_LANE - chosen["total_get_cost"], 6),
        },
        "totals": {
            "lines": len(chosen["lines"]),
            "records": chosen["total_records"],
            "billable_size_bytes": chosen["total_billable_size"],
            "get_cost_usd": chosen["total_get_cost"],
        },
        "request_lines": chosen["lines"],
        "alternatives_considered": {
            c: {"total_get_cost_usd": r["total_get_cost"],
                "fx_ohlcv_total_months": r["fx_ohlcv_total_months"],
                "within_trim_target": r["within_trim_target"],
                "within_lane_hard_stop": r["within_lane_hard_stop"],
                "reason": ("CHOSEN" if c == chosen_name else
                           ("over $115 trim target" if not r["within_trim_target"]
                            else "fewer FX months than chosen"))}
            for c, r in candidate_results.items() if c != chosen_name
        },
        "conventions": {
            "stype": "parent ({ROOT}.FUT) for every line; per-contract raw "
                     "series via parent resolution (all listed expiries; "
                     "identity via definition records + symbol mappings)",
            "continuous_series": "NONE purchased (no CONTFUT/adjusted "
                                 "execution series; vendor c/n/v tables via "
                                 "free symbology.resolve only, NOT_RUN here)",
            "end_dates_exclusive": True,
            "delivery": "official batch API (batch.submit_job, dbn+zstd, "
                        "download delivery); per-chunk re-quote before every "
                        "submit (budget law)",
            "chunking": "3-6 month windows per (root, schema) line; order: "
                        "definition/statistics, NQ/ES, GC/SI, FX, CL/NG",
            "pilot_relationship": "PILOT-01/02 def+stat NQ/CL windows are "
                                  "strictly inside AV1T-definition/statistics "
                                  "lines (one-owner rule: this delivery owns "
                                  "them; nothing else was ever submitted — "
                                  "no completion ledger existed).",
        },
        "quote_evidence": "trim_quotes.json (every call timestamped)",
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=1))
    print(f"\nCHOSEN: {chosen_name} total=${chosen['total_get_cost']:.4f} "
          f"(target <= {TRIM_TARGET}, hard stop {BUDGET_HARD_STOP_LANE})")
    print(f"wrote {OUT_QUOTES.name} and {OUT_MANIFEST.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
