#!/usr/bin/env python3
"""rescope_quote.py — OWNER RESCOPE quote round (metadata-only, zero cost).

Owner verbatim: 'tôi muốn NQ ES 6E 6J 6B 6A thôi. Tải trong 125 đô đó.
Còn lại [GC/SI/CL/NG] mắc quá tính sau.'

Fixed kept core (from AV1_TRIM_MANIFEST + ledger, no double-billing):
  definition ALL10 36m + statistics ALL10 36m + NQ/ES ohlcv 36m (already
  planned 2023-10-01..2026-10-01) + existing FX short windows
  (6E/6J 2026-01-01, 6B/6A 2026-04-01).

New lines to quote:
  NQ.FUT delta 2010-06-06..2023-10-01 (no overlap with committed window)
  ES.FUT delta 2010-06-06..2023-10-01
  6E/6J backfill 2010-06-06..2026-01-01 (candidate starts)
  6B/6A backfill 2010-06-06..2026-04-01 (candidate starts)

Selection: remaining budget at $115 target / $118 hard stop after fixed
core + NQ/ES deltas -> equal-dollar allocation across the 4 FX roots;
deepest start per root within allocation; shrink symmetrically if needed.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

import databento as db

ACQ = Path(__file__).resolve().parent
KEY_PATH = Path(
    "/Users/hoangminhlong/.config/my-quantitative-secrets/databento-api-key")
TOKEN_RE = re.compile(r"db-[A-Za-z0-9_\-]{12,}")
DATASET = "GLBX.MDP3"
TARGET_TOTAL = 115.00
HARD_STOP = 118.00

FIXED_CORE = {
    "AV1T-definition-ALL10": 10.008760023862,
    "AV1T-statistics-ALL10": 5.145746171474,
    "AV1T-O1M-NQ (2023-10..2026-10)": 5.730271339416,
    "AV1T-O1M-ES (2023-10..2026-10)": 6.197820007801,
    "AV1T-O1M-6E (2026-01..2026-10)": 1.472978368402,
    "AV1T-O1M-6J (2026-01..2026-10)": 1.35814294219,
    "AV1T-O1M-6B (2026-04..2026-10)": 0.713177099824,
    "AV1T-O1M-6A (2026-04..2026-10)": 0.764364749193,
}

FX_CANDIDATE_STARTS = ["2010-06-06", "2012-01-01", "2014-01-01",
                       "2016-01-01", "2018-01-01", "2020-01-01",
                       "2022-01-01"]
FX_END = {"6E": "2026-01-01", "6J": "2026-01-01",
          "6B": "2026-04-01", "6A": "2026-04-01"}
DELTA = {"NQ": ("2010-06-06", "2023-10-01"), "ES": ("2010-06-06",
                                                     "2023-10-01")}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def redact(t: str) -> str:
    return TOKEN_RE.sub("db-REDACTED", t)


def main() -> int:
    key = KEY_PATH.read_text().strip()
    client = db.Historical(key=key)
    quotes: dict[str, dict] = {}

    def quote(tag: str, symbols: str, schema: str, start: str, end: str):
        k = f"{tag}|{start}|{end}"
        if k in quotes:
            return quotes[k]
        for attempt in range(1, 4):
            try:
                cost = float(client.metadata.get_cost(
                    dataset=DATASET, symbols=symbols, schema=schema,
                    stype_in="parent", start=start, end=end))
                size = int(client.metadata.get_billable_size(
                    dataset=DATASET, symbols=symbols, schema=schema,
                    stype_in="parent", start=start, end=end))
                count = int(client.metadata.get_record_count(
                    dataset=DATASET, symbols=symbols, schema=schema,
                    stype_in="parent", start=start, end=end))
                quotes[k] = {"symbols": symbols, "schema": schema,
                             "start": start, "end": end,
                             "get_cost": cost, "billable_size": size,
                             "records": count, "ts_utc": now_utc()}
                print(f"  {k}: ${cost:.4f} {count:,} rec")
                time.sleep(0.35)
                return quotes[k]
            except Exception as exc:  # noqa: BLE001
                if attempt == 3:
                    raise
                time.sleep(2 * attempt)

    fixed_total = sum(FIXED_CORE.values())
    print(f"fixed core (kept lines): ${fixed_total:.4f}")

    # --- NQ/ES full-era deltas ---
    deltas = {}
    for root, (s, e) in DELTA.items():
        deltas[root] = quote(f"delta-{root}", f"{root}.FUT", "ohlcv-1m", s, e)
    delta_total = sum(v["get_cost"] for v in deltas.values())
    print(f"NQ+ES deltas: ${delta_total:.4f}")

    pool_target = TARGET_TOTAL - fixed_total - delta_total
    pool_stop = HARD_STOP - fixed_total - delta_total
    alloc = pool_target / 4
    print(f"FX backfill pool: target ${pool_target:.4f} "
          f"(hard-stop pool ${pool_stop:.4f}); equal alloc "
          f"${alloc:.4f}/root")

    # --- FX candidate ladders ---
    ladder = {}
    for root in ("6E", "6J", "6B", "6A"):
        ladder[root] = {}
        for s in FX_CANDIDATE_STARTS:
            ladder[root][s] = quote(f"fx-{root}", f"{root}.FUT", "ohlcv-1m",
                                    s, FX_END[root])

    # --- selection: deepest start within equal-dollar allocation; if the
    # deepest (2010-06-06) fits for ALL roots, take it; else shrink each
    # root to the deepest start fitting its allocation; if even the
    # shallowest candidate exceeds allocation for some root, fall back to
    # a computed later start via the per-year rate (recorded). ---
    chosen = {}
    for root in ("6E", "6J", "6B", "6A"):
        pick = None
        for s in FX_CANDIDATE_STARTS:          # deepest first
            if ladder[root][s]["get_cost"] <= alloc + 1e-9:
                pick = s
                break
        chosen[root] = pick
        print(f"{root}: chosen start {pick} "
              f"(${ladder[root][pick]['get_cost']:.4f})" if pick else
              f"{root}: NO candidate fits allocation ${alloc:.4f}")

    # symmetric shrink if some root missed: lower the allocation by using
    # the max cost among chosen-fit roots is NOT equal — owner rule says
    # shrink all four symmetrically: find largest equal budget b such that
    # every root has a candidate <= b.
    if any(v is None for v in chosen.values()):
        b = 0.0
        for bs in sorted({ladder[r][s]["get_cost"]
                          for r in ladder for s in FX_CANDIDATE_STARTS}):
            if all(any(ladder[r][s]["get_cost"] <= bs
                       for s in FX_CANDIDATE_STARTS) for r in ladder):
                b = bs
                break
        print(f"symmetric shrink: equal per-root budget ${b:.4f}")
        for root in ("6E", "6J", "6B", "6A"):
            for s in FX_CANDIDATE_STARTS:
                if ladder[root][s]["get_cost"] <= b + 1e-9:
                    chosen[root] = s
                    break

    new_total = (fixed_total + delta_total
                 + sum(ladder[r][chosen[r]]["get_cost"] for r in chosen))
    out = {
        "generated_utc": now_utc(),
        "owner_rescope_verbatim": "tôi muốn NQ ES 6E 6J 6B 6A thôi. Tải "
                                  "trong 125 đô đó. Còn lại mắc quá tính "
                                  "sau.",
        "fixed_core": FIXED_CORE,
        "fixed_core_total": fixed_total,
        "deltas": {r: quotes[f"delta-{r}|{DELTA[r][0]}|{DELTA[r][1]}"]
                   for r in DELTA},
        "deltas_total": delta_total,
        "fx_ladder": ladder,
        "fx_equal_allocation": alloc,
        "fx_chosen_starts": chosen,
        "fx_chosen_lines": {r: ladder[r][chosen[r]] for r in chosen},
        "new_package_total_get_cost": new_total,
        "within_target_115": new_total <= TARGET_TOTAL,
        "within_hard_stop_118": new_total <= HARD_STOP,
    }
    (ACQ / "rescope_quotes.json").write_text(json.dumps(out, indent=1))
    print(f"\nNEW PACKAGE TOTAL: ${new_total:.4f} "
          f"(target<=115: {new_total <= TARGET_TOTAL}, "
          f"hard-stop<=118: {new_total <= HARD_STOP})")
    print("wrote rescope_quotes.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
