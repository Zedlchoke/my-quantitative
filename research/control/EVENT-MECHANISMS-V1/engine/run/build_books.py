"""Lane I main build — E1/E2/E3 + populations (R2-6 boundary respected).

Run:  .venv/bin/python research/control/EVENT-MECHANISMS-V1/engine/run/build_books.py
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emv1 import config as C
from emv1.loaders import (verify_all_digests, load_a1_events, load_n4_map,
                          load_corp_actions)
from emv1.panel import Panel
from emv1.arms import (build_a1_arms, build_a2_arms, ARM_DEFS)
from emv1.book import summarize_populations, summarize_exclusions
from emv1.a2_inputs import (stream_p_rows, load_accession_form_map,
                            load_xml_by_accession, build_a2_issuer_days)


def dump(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)


def dump_records(path: str, records) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")


def main() -> None:
    t0 = time.time()
    ev: dict = {}

    # ---------------- E1: fail-closed digests ----------------
    ev["digest_verification"] = verify_all_digests()
    print("[E1] digests verified:", ev["digest_verification"]["ok"])

    n4 = load_n4_map()
    cohort_ciks = set(n4)
    ticker_by_cik = {c: n4[c]["ticker"] for c in n4}

    # ---------------- panel (raw OHLCV only) ----------------
    counters: dict = {}
    tickers = sorted({n4[c]["ticker"] for c in n4} | {"SPY"})
    panel = Panel(tickers, counters)
    ev["panel_guard_counters"] = counters
    ev["panel_names_loaded"] = len(panel.names)
    print(f"[panel] {len(panel.names)} names, counters={counters}", f"{time.time()-t0:.0f}s")

    ca_census: dict = {}
    corp_actions = load_corp_actions(ca_census)
    ev["corp_action_loader_census"] = ca_census

    # ---------------- E2: A1 book ----------------
    a1_events, a1_stats = load_a1_events()
    ev["a1_event_set"] = a1_stats
    print(f"[E2] A1 events {a1_stats['events']} (dedup {a1_stats['dropped_duplicate_identity']})")

    records, exclusions = build_a1_arms(a1_events, panel, corp_actions, n4=n4)
    dump_records(os.path.join(C.EVIDENCE_DIR, "a1_decisions.jsonl"), records)
    dump_records(os.path.join(C.EVIDENCE_DIR, "a1_exclusions.jsonl"), exclusions)
    ev["a1_populations"] = summarize_populations(records)
    ev["a1_exclusions"] = summarize_exclusions(exclusions)
    ev["a1_unique_event_exclusions"] = unique_event_exclusion_census(
        records, exclusions, lambda e: e.split(":", 1)[1])
    print(f"[E2] A1 records {len(records)}, exclusions {len(exclusions)}", f"{time.time()-t0:.0f}s")

    # ---------------- E3: A2 book ----------------
    p_rows = stream_p_rows()
    p_ciks = sorted({r["cik"] for r in p_rows} & cohort_ciks)
    acc_form = load_accession_form_map(p_ciks)
    accs = sorted({r["accession"] for r in p_rows if r["cik"] in cohort_ciks})
    acc_cik = {}
    for r in p_rows:
        if r["cik"] in cohort_ciks and r["accession"] not in acc_cik:
            acc_cik[r["accession"]] = r["cik"]
    xml = load_xml_by_accession(accs, acc_cik)
    a2_days, a2_stats = build_a2_issuer_days(p_rows, acc_form, xml, cohort_ciks)
    ev["a2_inputs"] = a2_stats
    ev["a2_inputs"]["p_rows_total"] = len(p_rows)
    ev["a2_inputs"]["unique_accessions_parsed"] = len(accs)
    ev["a2_inputs"]["xml_missing"] = sum(1 for v in xml.values() if v is None)
    print(f"[E3] A2 issuer-day events {a2_stats['issuer_day_events']} drops={a2_stats['drops']}")

    a2_records, a2_exclusions = build_a2_arms(a2_days, ticker_by_cik, panel, corp_actions, n4=n4)
    dump_records(os.path.join(C.EVIDENCE_DIR, "a2_decisions.jsonl"), a2_records)
    dump_records(os.path.join(C.EVIDENCE_DIR, "a2_exclusions.jsonl"), a2_exclusions)
    # issuer-day feature table for E5 cadence (values only, no returns)
    dump(os.path.join(C.EVIDENCE_DIR, "a2_issuer_days.json"), a2_days)
    ev["a2_populations"] = summarize_populations(a2_records)
    ev["a2_exclusions"] = summarize_exclusions(a2_exclusions)
    ev["a2_unique_event_exclusions"] = unique_event_exclusion_census(
        a2_records, a2_exclusions, lambda e: e.split(":", 1)[1])
    print(f"[E3] A2 records {len(a2_records)}, exclusions {len(a2_exclusions)}", f"{time.time()-t0:.0f}s")

    # arm/fold floor check (feasibility only; ALL folds checked incl. empty)
    all_records = records + a2_records
    floors = {}
    for arm in sorted(set(r["arm_id"] for r in all_records)):
        if not arm.endswith("-ANCHOR"):
            continue
        pops = summarize_populations([r for r in all_records if r["arm_id"] == arm])[arm]
        per_fold = {name: pops.get(name, 0) for name, _, _ in C.FOLDS}
        floors[arm] = {
            "per_fold": per_fold,
            "total": pops.get("TOTAL", 0),
            "meets_100_per_fold": all(v >= C.FLOOR_EVENTS_PER_FOLD for v in per_fold.values()),
            "meets_400_total": pops.get("TOTAL", 0) >= C.FLOOR_EVENTS_TOTAL_PER_ANCHOR,
            "empty_folds": [name for name, _, _ in C.FOLDS if per_fold[name] == 0],
        }
    ev["floor_check"] = floors
    ev["floor_check_note"] = (
        "form4_stream substrate coverage measured 2018-01..2025 (no 2015-2017 rows); "
        "A2 F1 = 0 is a data-coverage fact, flagged NOT_RUN_THIN-risk for A2 per the freeze floor law"
    )

    # R2-2 contamination check on UNIQUE events (corp-action exclusions / all candidates per fold)
    for fam, cens in (("A1", ev["a1_unique_event_exclusions"]),
                      ("A2", ev["a2_unique_event_exclusions"])):
        per_fold = {}
        for reason, folds in cens["by_reason"].items():
            if reason != "CORP_ACTION_IN_WINDOW":
                continue
            for f, v in folds.items():
                if f != "TOTAL":
                    per_fold[f] = per_fold.get(f, 0) + v
        frac = {f: round(per_fold.get(f, 0) / max(1, cens["candidates_per_fold"].get(f, 0)), 4)
                for f, _, _ in C.FOLDS}
        ev[f"{fam}_corp_action_fraction_per_fold"] = {
            "fractions": frac,
            "contamination_high": any(v > C.CONTAMINATION_EXCLUSION_FRACTION for v in frac.values()),
        }

    dump(os.path.join(C.EVIDENCE_DIR, "build_evidence.json"), ev)
    print(f"[done] {time.time()-t0:.0f}s -> {C.EVIDENCE_DIR}")


_PIPELINE_ORDER = (
    "NO_PANEL_FOR_TICKER", "NO_SESSION_AFTER_ACCEPTANCE", "NO_ENTRY_SESSION",
    "ZERO_DIRECTION_SESSION_MOVE", "FOLD_BOUNDARY_NO_WINDOW",
    "CORP_ACTION_IN_WINDOW", "ENTRY_BAR_UNFILLABLE_B1B2",
    "BELOW_DV_FLOOR_AT_DECISION",
)
# r3 note: EXIT_BAR_UNFILLABLE_B1B2 left the pipeline — r3 AMB-7 rolls the
# exit forward (exhaustion books at the last permissible bar flagged
# delisting_exit), so it is no longer an exclusion reason.


def unique_event_exclusion_census(records, exclusions, base_key) -> dict:
    """Unique-event exclusion census at pipeline order (R2-2 feasibility
    numbers, deduped across arms)."""
    bookable = set()
    for r in records:
        bookable.add(base_key(r["event_id"]))
    first: dict = {}
    rank = {reason: i for i, reason in enumerate(_PIPELINE_ORDER)}
    for e in exclusions:
        k = base_key(e["event_id"])
        reason = e["reason"]
        if reason not in rank:
            continue
        if k not in first or rank[reason] < rank[first[k]]:
            first[k] = reason
    by_reason: dict = {}
    candidates_per_fold: dict = {}
    fold_by_key = {}
    for r in records:
        fold_by_key[base_key(r["event_id"])] = r["fold"]
    for e in exclusions:
        fold_by_key.setdefault(base_key(e["event_id"]), e.get("fold", "?"))
    for k, reason in first.items():
        f = fold_by_key.get(k, "?")
        by_reason.setdefault(reason, {}).setdefault(f, 0)
        by_reason[reason][f] += 1
    all_keys = bookable | set(first)
    for k in all_keys:
        f = fold_by_key.get(k, "?")
        candidates_per_fold[f] = candidates_per_fold.get(f, 0) + 1
    out = {"candidates_unique": len(all_keys),
           "bookable_unique": len(bookable),
           "excluded_unique": len(first),
           "candidates_per_fold": candidates_per_fold,
           "by_reason": {}}
    for reason, folds in sorted(by_reason.items()):
        out["by_reason"][reason] = dict(sorted(folds.items()))
        out["by_reason"][reason]["TOTAL"] = sum(folds.values())
    return out


if __name__ == "__main__":
    main()
