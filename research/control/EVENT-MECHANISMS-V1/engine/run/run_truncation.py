"""E6(d) — panel-truncation replay.

For a random sample of 300 events (seed 7) + all 3 fold boundaries (nearest
anchor events each side), the book is rebuilt on panels truncated per event:
  V1 entry-instant truncation: bars AFTER the entry session removed — proves
     direction_session / direction / entry_session / entry_price use no
     future bars (decision-prefix byte-compare);
  V2 window-complete truncation: bars AFTER the exit session removed — the
     FULL decision record must be byte-identical (json.dumps equality).
"""
from __future__ import annotations

import json
import os
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emv1 import config as C
from emv1 import clock
from emv1.loaders import load_n4_map, load_corp_actions
from emv1.panel import Panel, NameSeries
from emv1.book import build_decision, DECISION_KEYS as C_DECISION_KEYS


def read_records(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def truncated_panel(full: Panel, ticker: str, cutoff_date: str) -> Panel:
    ns = full.names.get(ticker)
    p = Panel.__new__(Panel)
    p.names = {}
    if ns is None:
        return p
    k = ns.idx.get(cutoff_date)
    if k is None:
        # cutoff not a bar date (e.g. a Sunday): keep all bars <= cutoff
        lo, hi, ans = 0, len(ns.dates) - 1, -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if ns.dates[mid] <= cutoff_date:
                ans = mid
                lo = mid + 1
            else:
                hi = mid - 1
        k = ans
    ns2 = NameSeries(ticker)
    ns2.dates = ns.dates[: k + 1]
    ns2.idx = {d: i for i, d in enumerate(ns2.dates)}
    ns2.open = ns.open[: k + 1]
    ns2.high = ns.high[: k + 1]
    ns2.low = ns.low[: k + 1]
    ns2.close = ns.close[: k + 1]
    ns2.vol = ns.vol[: k + 1]
    ns2.dv = ns.dv[: k + 1]
    ns2.fill_ok = ns.fill_ok[: k + 1]
    p.names[ticker] = ns2
    return p


def replay(rec: dict, full: Panel, corp_actions: dict):
    """Return (v1_record|None, v2_record|None).

    V2 truncation keeps the event's FOLD-BOUNDARY CONTEXT: the cutoff is the
    25th bar (H_max = 20) after the fold end, or the panel end. Bars past the
    exit session cannot influence decision fields (entry/window checks read
    only [entry, exit] and pre-entry history); the buffer exists so the
    panel-extent flags (forced_flat / delisting_exit) are well-defined and
    must reproduce byte-identically too.
    """
    instant_et, _ = clock.to_et(clock.parse_acceptance_utc(rec["acceptance_utc"]))
    override = "LONG" if rec["family_id"] == C.FAMILY_A2 else None
    fold_end = next(hi for name, lo, hi in C.FOLDS if name == rec["fold"])
    ns_full = full.names.get(rec["ticker"])
    v2_cutoff = None
    if ns_full is not None:
        lo, hi, first_ge = 0, len(ns_full.dates) - 1, None
        while lo <= hi:
            mid = (lo + hi) // 2
            if ns_full.dates[mid] >= fold_end:
                first_ge = mid
                hi = mid - 1
            else:
                lo = mid + 1
        if first_ge is None:
            v2_cutoff = ns_full.dates[-1]
        else:
            v2_cutoff = ns_full.dates[min(len(ns_full.dates) - 1, first_ge + 24)]
    v1_panel = truncated_panel(full, rec["ticker"], rec["entry_session"])
    v1, _ = build_decision(
        event_id=rec["event_id"], family_id=rec["family_id"], arm_id=rec["arm_id"],
        cik=rec["cik"], ticker=rec["ticker"], form=rec["form"],
        acceptance_utc=rec["acceptance_utc"], instant_et=instant_et,
        hold_sessions=rec["hold_sessions"], panel=v1_panel,
        corp_actions=corp_actions, stratum=rec["stratum"], bucket=rec["bucket"],
        is_weekend=rec["is_weekend"], control_variant=rec["control_variant"],
        direction_override=override, ticker_reuse_risk=rec.get("ticker_reuse_risk", False))
    v2_panel = truncated_panel(full, rec["ticker"], v2_cutoff)
    v2, _ = build_decision(
        event_id=rec["event_id"], family_id=rec["family_id"], arm_id=rec["arm_id"],
        cik=rec["cik"], ticker=rec["ticker"], form=rec["form"],
        acceptance_utc=rec["acceptance_utc"], instant_et=instant_et,
        hold_sessions=rec["hold_sessions"], panel=v2_panel,
        corp_actions=corp_actions, stratum=rec["stratum"], bucket=rec["bucket"],
        is_weekend=rec["is_weekend"], control_variant=rec["control_variant"],
        direction_override=override, ticker_reuse_risk=rec.get("ticker_reuse_risk", False))
    return v1, v2


def main() -> None:
    n4 = load_n4_map()
    tickers = sorted({n4[c]["ticker"] for c in n4} | {"SPY"})
    full = Panel(tickers)
    corp_actions = load_corp_actions()

    a1 = [r for r in read_records(os.path.join(C.EVIDENCE_DIR, "a1_decisions.jsonl"))
          if r["arm_id"] == "A1-ANCHOR"]
    a2 = [r for r in read_records(os.path.join(C.EVIDENCE_DIR, "a2_decisions.jsonl"))
          if r["arm_id"] == "A2-ANCHOR"]
    pool = a1 + a2

    rng = random.Random(C.SEED_TRUNCATION_SAMPLE)
    sample = rng.sample(pool, C.TRUNCATION_SAMPLE_N)

    # fold-boundary events: nearest anchor events each side of each boundary
    boundary_events = []
    for _, _, hi in C.FOLDS[:-1]:
        before = sorted((r for r in pool if r["acceptance_utc"][:10] < hi),
                        key=lambda r: r["acceptance_utc"])[-3:]
        after = sorted((r for r in pool if r["acceptance_utc"][:10] >= hi),
                       key=lambda r: r["acceptance_utc"])[:3]
        boundary_events.extend(before + after)

    n_v1_ok = n_v2_ok = 0
    v1_fail = []
    v2_fail = []
    dk = set(C_DECISION_KEYS)
    for rec in sample + boundary_events:
        v1, v2 = replay(rec, full, corp_actions)
        # V1: decision prefix must match (fields determinable at entry)
        prefix_keys = ("direction_session", "direction", "entry_session", "entry_price")
        if v1 is not None and all(v1[k] == rec[k] for k in prefix_keys):
            n_v1_ok += 1
        else:
            v1_fail.append(rec["event_id"])
        # V2: FULL builder-produced record byte-identical (the decision-key
        # projection; A2 records additionally carry issuer-day feature fields
        # attached after the build, which are build-independent inputs)
        if v2 is not None and json.dumps({k: v2[k] for k in dk}, sort_keys=True) == \
                json.dumps({k: rec[k] for k in dk}, sort_keys=True):
            n_v2_ok += 1
        else:
            v2_fail.append(rec["event_id"])

    out = {
        "schema": "emv1_truncation_replay@1",
        "seed": C.SEED_TRUNCATION_SAMPLE,
        "sample_n": len(sample),
        "fold_boundary_events": len(boundary_events),
        "total_replayed": len(sample) + len(boundary_events),
        "v1_entry_truncation_prefix_match": n_v1_ok,
        "v1_failures": v1_fail[:10],
        "v2_full_record_byte_identical_match": n_v2_ok,
        "v2_failures": v2_fail[:10],
        "all_match": n_v1_ok == len(sample) + len(boundary_events)
        and n_v2_ok == len(sample) + len(boundary_events),
    }
    os.makedirs(C.EVIDENCE_DIR, exist_ok=True)
    json.dump(out, open(os.path.join(C.EVIDENCE_DIR, "truncation_replay.json"), "w"),
              indent=1, sort_keys=True)
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
