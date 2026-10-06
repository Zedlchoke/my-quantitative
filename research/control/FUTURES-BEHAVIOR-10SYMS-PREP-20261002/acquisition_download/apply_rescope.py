#!/usr/bin/env python3
"""apply_rescope.py — write RESCOPE_MANIFEST.json + update the ledger for
the owner rescope (6 symbols; GC/SI/CL/NG ohlcv dropped; NQ/ES full-era
deltas + FX 2022 backfills added). One-shot; every number sourced from
rescope_quotes.json + AV1_TRIM_MANIFEST.json + COMPLETION_LEDGER.json."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ACQ = Path(__file__).resolve().parent
LEDGER = ACQ / "COMPLETION_LEDGER.json"
TRIM = ACQ / "AV1_TRIM_MANIFEST.json"
RQ = ACQ / "rescope_quotes.json"
OUT = ACQ / "RESCOPE_MANIFEST.json"

DROPPED_ROOTS = ["GC", "SI", "CL", "NG"]


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def main() -> None:
    rq = json.loads(RQ.read_text())
    trim = json.loads(TRIM.read_text())
    led = json.loads(LEDGER.read_text())

    chosen = rq["fx_chosen_starts"]
    fx_lines = rq["fx_chosen_lines"]

    # ---- 1. ledger: mark dropped ohlcv chunks ----
    marked = []
    for key, c in led["chunks"].items():
        if c.get("state") != "PLANNED":
            continue
        root = c["line_id"].replace("AV1T-O1M-", "")
        if root in DROPPED_ROOTS:
            c["state"] = "DROPPED_BY_OWNER_RESCOPE"
            c["dropped_utc"] = now_utc()
            c["drop_reason"] = ("owner rescope 2026-10-02: 'tôi muốn NQ ES "
                                "6E 6J 6B 6A thôi. Tải trong 125 đô đó. "
                                "Còn lại mắc quá tính sau.' No spend occurred "
                                "on this chunk (never submitted).")
            marked.append(key)
    led["rescope_applied_utc"] = now_utc()

    # ---- 2. rescope manifest ----
    new_lines = [
        {"line_id": "AV1R-O1M-NQ-DELTA", "dataset": "GLBX.MDP3",
         "schema": "ohlcv-1m", "symbols": ["NQ.FUT"], "stype_in": "parent",
         "start": "2010-06-06", "end": "2023-10-01",
         "chunk_months": 24, "order": 60,
         "get_cost": rq["deltas"]["NQ"]["get_cost"],
         "billable_size": rq["deltas"]["NQ"]["billable_size"],
         "records": rq["deltas"]["NQ"]["records"],
         "no_overlap_note": "ends exactly at the start of committed "
                            "AV1T-O1M-NQ window 2023-10-01"},
        {"line_id": "AV1R-O1M-ES-DELTA", "dataset": "GLBX.MDP3",
         "schema": "ohlcv-1m", "symbols": ["ES.FUT"], "stype_in": "parent",
         "start": "2010-06-06", "end": "2023-10-01",
         "chunk_months": 24, "order": 62,
         "get_cost": rq["deltas"]["ES"]["get_cost"],
         "billable_size": rq["deltas"]["ES"]["billable_size"],
         "records": rq["deltas"]["ES"]["records"],
         "no_overlap_note": "ends exactly at the start of committed "
                            "AV1T-O1M-ES window 2023-10-01"},
    ]
    order = 70
    for root in ("6E", "6J", "6B", "6A"):
        q = fx_lines[root]
        new_lines.append({
            "line_id": f"AV1R-O1M-{root}-BACKFILL", "dataset": "GLBX.MDP3",
            "schema": "ohlcv-1m", "symbols": [f"{root}.FUT"],
            "stype_in": "parent",
            "start": chosen[root], "end": q["end"],
            "chunk_months": 24, "order": order,
            "get_cost": q["get_cost"], "billable_size": q["billable_size"],
            "records": q["records"],
            "no_overlap_note": (f"ends exactly at the start of the kept "
                                f"AV1T-O1M-{root} short window "
                                f"{q['end']}"),
        })
        order += 2

    dropped_avoided = sum(
        l["get_cost"] for l in trim["request_lines"]
        if l["line_id"].replace("AV1T-O1M-", "") in DROPPED_ROOTS)

    manifest = {
        "schema": "futures_behavior_rescope_manifest@1",
        "task_id": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
        "lane": "ACQ-DOWNLOAD",
        "generated_utc": now_utc(),
        "owner_rescope_verbatim": rq["owner_rescope_verbatim"],
        "supersedes": "AV1_TRIM_MANIFEST.json (ohlcv scope only; kept lines "
                      "continue under their existing chunk keys)",
        "dropped_lines": {
            "lines": [f"AV1T-O1M-{r}" for r in DROPPED_ROOTS],
            "reason": "owner rescope: 'Còn lại mắc quá tính sau' (too "
                      "expensive, defer)",
            "avoided_spend_usd": round(dropped_avoided, 6),
            "actual_spend_on_dropped": 0.0,
            "note": "no ohlcv chunk of these roots was ever submitted "
                    "(ledger-verified); their definition/statistics share "
                    "inside the ALL10 joined lines is KEPT (cheap, serves "
                    "the 6 kept symbols).",
        },
        "kept_lines": {
            "AV1T-definition-ALL10": rq["fixed_core"][
                "AV1T-definition-ALL10"],
            "AV1T-statistics-ALL10": rq["fixed_core"][
                "AV1T-statistics-ALL10"],
            "AV1T-O1M-NQ (2023-10..2026-10)": rq["fixed_core"][
                "AV1T-O1M-NQ (2023-10..2026-10)"],
            "AV1T-O1M-ES (2023-10..2026-10)": rq["fixed_core"][
                "AV1T-O1M-ES (2023-10..2026-10)"],
            "FX short windows (6E/6J 2026-01, 6B/6A 2026-04)": sum(
                rq["fixed_core"][k] for k in rq["fixed_core"]
                if "6E (2026" in k or "6J (2026" in k
                or "6B (2026" in k or "6A (2026" in k),
        },
        "new_lines": new_lines,
        "fx_selection_rule": "equal-dollar allocation "
                             f"(${rq['fx_equal_allocation']:.4f}/root from "
                             "the $115 target after fixed core + NQ/ES "
                             "deltas); deepest candidate start that fits; "
                             "all four roots fit at 2022-01-01 (2020-01-01 "
                             "starts exceeded the allocation for every "
                             "root; choosing a lone deeper root would break "
                             "the owner's equal rule and consume the drift "
                             "buffer, so the remaining $9.19 of target "
                             "headroom is preserved)",
        "budget": {
            "owner_ceiling_usd": 125.00, "lane_hard_stop_usd": 118.00,
            "target_usd": 115.00,
            "new_package_total_get_cost":
                rq["new_package_total_get_cost"],
            "committed_at_rescope_usd":
                led["running_totals"]["committed_usd"],
            "headroom_to_hard_stop_usd": round(
                118.0 - rq["new_package_total_get_cost"], 6),
        },
        "chunking": "new backfill/delta lines chunked at 24 months "
                    "(documented deviation from the 3-6m suggestion for "
                    "wall-time feasibility: <=1.1M records/chunk, below the "
                    "definition-chunk workload; per-chunk budget re-quote + "
                    "QA + SHA + iCloud mirror unchanged)",
        "quote_evidence": "rescope_quotes.json",
    }
    OUT.write_text(json.dumps(manifest, indent=1))

    # ---- 3. ledger: append new chunks (plan) ----
    def add_months(d: dt.date, n: int) -> dt.date:
        y = d.year + (d.month - 1 + n) // 12
        m = (d.month - 1 + n) % 12 + 1
        return d.replace(year=y, month=m, day=1)

    def month_floor(d: dt.date) -> dt.date:
        return d.replace(day=1)

    def split_months(start: str, end: str, months: int):
        s = month_floor(dt.date.fromisoformat(start))
        e = dt.date.fromisoformat(end)
        out = []
        while s < e:
            nxt = min(add_months(s, months), e)
            out.append((s.isoformat(), nxt.isoformat()))
            s = nxt
        return out

    added = 0
    for line in new_lines:
        for (s, e) in split_months(line["start"], line["end"],
                                   line["chunk_months"]):
            key = f"{line['line_id']}__{s}_{e}"
            if key in led["chunks"]:
                continue
            led["chunks"][key] = {
                "chunk_key": key, "line_id": line["line_id"],
                "dataset": line["dataset"], "schema": line["schema"],
                "symbols": line["symbols"], "stype_in": line["stype_in"],
                "start": s, "end": e, "order": line["order"],
                "state": "PLANNED",
                "rescope_added": True,
            }
            added += 1

    tmp = LEDGER.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(led, indent=1, default=str))
    tmp.replace(LEDGER)

    print(f"marked {len(marked)} chunks DROPPED_BY_OWNER_RESCOPE")
    print(f"added {added} new chunks to the ledger plan")
    print(f"new package total ${rq['new_package_total_get_cost']:.4f}; "
          f"dropped-line avoided spend ${dropped_avoided:.4f}; "
          f"committed at rescope "
          f"${led['running_totals']['committed_usd']:.4f}")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
