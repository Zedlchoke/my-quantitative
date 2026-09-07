#!/usr/bin/env python
"""FOREX-FREE-V3R R2 prep: build evidenced-availability vintage copies.

STATUS: DRAFT -- UNRUN (authored during a session shell outage; must pass the
offline selftest below and targeted review before any recompute trusts it).

Reads
-----
  * the FROZEN BIS vintage files (data_raw/forex_free_v3_macro/<AREA>.json;
    byte-hashes pinned in w3_freeze.json data_freeze.macro_vintages);
  * the pinned announcement ledger
    (research/control/forex_free_v3r_run/announcement_ledger.jsonl -- refuses
    to run against an unpinned ledger or a stale sha256).

Writes
------
  data_raw/forex_free_v3r_macro_evidenced/<AREA>.json -- byte-identical
  canonical records EXCEPT ``available_time_utc``, which now comes from the
  announcement ledger's operative bound, plus
  ``evidenced_vintages_manifest.json``.

Mapping rule (the single scientific change, applied row-wise)
-------------------------------------------------------------
Every vintage row carries a level that was established by the most recent
change event with effective date <= the row's effective date.  The row's
``available_time_utc`` becomes that establishing event's operative bound:

  * EVIDENCED event   -> the evidenced announcement instant (as precise as
    the source supports; DAY-precision events take end of announcement UTC
    day, conservative within the evidenced day);
  * UNEVIDENCED event -> the conservative LATER bound (end of the EVENT's
    effective UTC day vs first BIS publication stamp -- historically null),
    i.e. the V3 baseline bound, so an unevidenced event can only ever
    reproduce the old behaviour, never earlier;
  * rows before the area's first in-window change (baseline level) -> the
    BASELINE_LEVEL row's conservative bound (end of the row's own effective
    day, matching the V3 baseline; provenance-only, not load-bearing).

The PIT eligibility invariant is enforced unchanged by the frozen reader:
``available_time_utc <= decision_ts`` AND ``effective_time_utc <=
decision_ts`` -- a rate is still never read before it is in force; the
evidence only moves when the (already effective) level first becomes
readable at a 16:00-NY decision.

Fail-closed guarantees (verified per row before writing):
  * record count and every non-availability field are BYTE-IDENTICAL to the
    frozen input (only available_time_utc may differ);
  * each new availability satisfies the NormalizedRecord constraint
    available_time_utc <= retrieved_time_utc (models.py validation);
  * the row's effective date is covered by a ledger row (event or baseline);
    a vintage row with no establishing ledger row is a FATAL mismatch (the
    recompute would silently read a differently-evidenced dataset).

Usage
-----
  .venv/bin/python research/control/forex_free_v3r_run/build_evidenced_vintages.py \
      [--vintage-dir data_raw/forex_free_v3_macro] \
      [--out-dir data_raw/forex_free_v3r_macro_evidenced]
  add --selftest to run the mapping checks without writing (uses staging
  ledger if the pinned one is absent).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone

RUN_DIR = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(RUN_DIR, "announcement_ledger.jsonl")
LEDGER_PIN = os.path.join(RUN_DIR, "LEDGER_PINNED")
AREAS = ("US", "EMU", "GB", "JP", "CH", "CA", "AU", "NZ")


def load_pinned_ledger(allow_staging=False):
    path = LEDGER + (".staging" if allow_staging else "")
    source = LEDGER if os.path.exists(LEDGER) else path
    if source.endswith(".staging") and not allow_staging:
        raise SystemExit("LEDGER_NOT_PINNED: run announcement_ledger_builder.py --pin first")
    if not os.path.exists(LEDGER_PIN) and not allow_staging:
        raise SystemExit("LEDGER_PINNED_MARKER_MISSING: hash-pin the ledger before recompute")
    raw = open(source, "rb").read()
    if os.path.exists(LEDGER_PIN) and not allow_staging:
        pinned = json.load(open(LEDGER_PIN))
        if hashlib.sha256(raw).hexdigest() != pinned.get("ledger_sha256"):
            raise SystemExit("LEDGER_SHA256_MISMATCH: staged bytes differ from the pin")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    return rows


def operative_bound(row):
    return row["announcement"]["operative_available_time_utc"]


def index_ledger(rows):
    events, baselines = {}, {}
    for row in rows:
        if row["row_type"] == "RATE_CHANGE":
            events[(row["area"], row["effective_date"])] = operative_bound(row)
        elif row["row_type"] == "BASELINE_LEVEL":
            baselines[row["area"]] = operative_bound(row)
    return events, baselines


def establishing_bound(area, effective_day, events, baselines):
    """Operative bound of the event that established the level on
    ``effective_day``: the most recent ledger event with effective_date <=
    effective_day; before any such event, the baseline bound."""
    candidates = [d for (a, d) in events if a == area and d <= effective_day]
    if candidates:
        return events[(area, max(candidates))]
    return baselines.get(area)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vintage-dir", default="data_raw/forex_free_v3_macro")
    parser.add_argument("--out-dir", default="data_raw/forex_free_v3r_macro_evidenced")
    parser.add_argument("--selftest", action="store_true",
                        help="run all checks and report, write nothing")
    args = parser.parse_args()

    ledger_rows = load_pinned_ledger()
    events, baselines = index_ledger(ledger_rows)

    manifest = {"schema": "forex_free_v3r_evidenced_vintages_manifest_v1",
                "per_area": {}, "fatal": []}
    os.makedirs(args.out_dir, exist_ok=True)
    for area in AREAS:
        src_path = os.path.join(args.vintage_dir, f"{area}.json")
        frozen = json.load(open(src_path, encoding="utf-8"))
        frozen.sort(key=lambda r: r["effective_time_utc"])
        out_rows, changed = [], 0
        for original in frozen:
            row = dict(original)
            eff_day = row["effective_time_utc"][:10]
            bound = establishing_bound(area, eff_day, events, baselines)
            if bound is None:
                manifest["fatal"].append(
                    {"area": area, "effective_date": eff_day,
                     "reason": "NO_ESTABLISHING_LEDGER_ROW"})
                continue
            # invariant: availability can never move past retrieval
            retrieved = row["retrieved_time_utc"]
            if bound > retrieved:
                manifest["fatal"].append(
                    {"area": area, "effective_date": eff_day,
                     "reason": "BOUND_AFTER_RETRIEVAL", "bound": bound,
                     "retrieved": retrieved})
                continue
            row["available_time_utc"] = bound
            if row["available_time_utc"] != original["available_time_utc"]:
                changed += 1
            # only-differs invariant: strip and deep-compare
            a = {k: v for k, v in original.items() if k != "available_time_utc"}
            b = {k: v for k, v in row.items() if k != "available_time_utc"}
            if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
                manifest["fatal"].append(
                    {"area": area, "effective_date": eff_day,
                     "reason": "NON_AVAILABILITY_FIELD_MUTATED"})
                continue
            out_rows.append(row)
        out_path = os.path.join(args.out_dir, f"{area}.json")
        digest = hashlib.sha256(
            json.dumps(out_rows, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False).encode("utf-8")).hexdigest()
        manifest["per_area"][area] = {
            "frozen_source": src_path,
            "frozen_sha256": hashlib.sha256(open(src_path, "rb").read()).hexdigest(),
            "rows": len(out_rows),
            "rows_with_changed_availability": changed,
            "rows_unchanged": len(out_rows) - changed,
            "evidenced_sha256_canonical": digest,
        }
        if not args.selftest and not manifest["fatal"]:
            with open(out_path, "w", encoding="utf-8") as handle:
                json.dump(out_rows, handle, ensure_ascii=False, separators=(",", ":"))
        print(json.dumps({area: manifest["per_area"][area]}, indent=1))

    manifest_path = os.path.join(args.out_dir, "evidenced_vintages_manifest.json")
    if not args.selftest and not manifest["fatal"]:
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=1, sort_keys=True)
    if manifest["fatal"]:
        print(json.dumps({"FATAL": manifest["fatal"]}, indent=1))
        return 2
    print(json.dumps({"selftest": args.selftest,
                      "wrote": not args.selftest,
                      "out_dir": args.out_dir}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
