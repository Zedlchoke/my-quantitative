"""E4 — controls machinery (re-evaluations, no PnL): date-only variants,
permuted-acceptance placebo (seed 20260927, 3 draws), clock-only shadow,
value/date-matched no-event placebo (A2).
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emv1 import config as C
from emv1.loaders import load_a1_events, load_n4_map, load_corp_actions
from emv1.panel import Panel
from emv1.arms import (build_a1_arms, build_a2_arms, build_a1_dateonly,
                       build_a2_dateonly, permute_a1_acceptances,
                       clock_only_shadow_a1, value_date_matched_placebo_a2)
from emv1.book import summarize_populations, summarize_exclusions
from emv1.a2_inputs import stream_p_rows, load_accession_form_map, load_xml_by_accession, build_a2_issuer_days


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w"), indent=1, sort_keys=True)


def dump_records(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")


def main() -> None:
    t0 = time.time()
    ev: dict = {}
    n4 = load_n4_map()
    cohort_ciks = set(n4)
    ticker_by_cik = {c: n4[c]["ticker"] for c in n4}
    tickers = sorted({n4[c]["ticker"] for c in n4} | {"SPY"})
    panel = Panel(tickers)
    corp_actions = load_corp_actions()
    a1_events, _ = load_a1_events()

    # A2 issuer-days (same pipeline as build_books)
    p_rows = stream_p_rows()
    p_ciks = sorted({r["cik"] for r in p_rows} & cohort_ciks)
    acc_form = load_accession_form_map(p_ciks)
    accs = sorted({r["accession"] for r in p_rows if r["cik"] in cohort_ciks})
    acc_cik = {}
    for r in p_rows:
        if r["cik"] in cohort_ciks:
            acc_cik.setdefault(r["accession"], r["cik"])
    xml = load_xml_by_accession(accs, acc_cik)
    a2_days, a2_stats = build_a2_issuer_days(p_rows, acc_form, xml, cohort_ciks)
    print(f"[a2] {a2_stats['issuer_day_events']} issuer-days {time.time()-t0:.0f}s")

    # (a) date-only variants
    a1_do, a1_do_x = build_a1_dateonly(a1_events, panel, corp_actions)
    a2_do, a2_do_x = build_a2_dateonly(a2_days, ticker_by_cik, panel, corp_actions)
    dump_records(os.path.join(C.EVIDENCE_DIR, "control_a1_dateonly.jsonl"), a1_do)
    dump_records(os.path.join(C.EVIDENCE_DIR, "control_a2_dateonly.jsonl"), a2_do)
    ev["date_only_populations"] = summarize_populations(a1_do + a2_do)
    ev["date_only_note"] = ("filing-date clock (filing_date 00:00 ET), strata removed; "
                            "arms = A1-DATEONLY-ANCHOR (H=5), A1-DATEONLY-N1 (H=10), "
                            "A2-DATEONLY-ANCHOR (H=10)")
    print(f"[E4a] date-only: A1 {len(a1_do)} A2 {len(a2_do)} records")

    # (b) permuted-acceptance placebo: within issuer x form x year, 3 draws
    draws = permute_a1_acceptances(a1_events, C.SEED_PERMUTE, C.PERMUTE_DRAWS)
    perm_records, perm_x = [], []
    for draw, pev in sorted(draws.items()):
        pr, px = build_a1_arms(pev, panel, corp_actions, control_variant="PERMUTED")
        # only the anchor-equivalent arm (unmonitored buckets, H=5) from each draw
        anchor_eq = [r for r in pr if r["arm_id"] == "A1-ANCHOR"]
        for r in anchor_eq:
            r["control_variant"] = "PERMUTED_ACCEPTANCE"
            r["draw"] = draw
        perm_records.extend(anchor_eq)
    dump_records(os.path.join(C.EVIDENCE_DIR, "control_a1_permuted.jsonl"), perm_records)
    ev["permuted_populations"] = summarize_populations(perm_records)
    ev["permuted_note"] = (f"acceptance stamps shuffled within issuer x form x year, "
                           f"seed {C.SEED_PERMUTE}, draws {C.PERMUTE_DRAWS}; anchor rule applied")
    print(f"[E4b] permuted: {len(perm_records)} records {time.time()-t0:.0f}s")

    # (c) clock-only shadow (strata clocks, payload removed)
    sh_records, sh_x = clock_only_shadow_a1(a1_events, panel, corp_actions, C.SEED_CLOCK_SHADOW)
    dump_records(os.path.join(C.EVIDENCE_DIR, "control_a1_clock_shadow.jsonl"), sh_records)
    ev["clock_shadow_populations"] = summarize_populations(sh_records)
    print(f"[E4c] clock shadow: {len(sh_records)} records {time.time()-t0:.0f}s")

    # (d) value/date-matched no-event placebo (A2)
    pl_records, pl_x = value_date_matched_placebo_a2(
        a2_days, ticker_by_cik, panel, corp_actions, C.SEED_VALUE_DATE_PLACEBO)
    dump_records(os.path.join(C.EVIDENCE_DIR, "control_a2_placebo.jsonl"), pl_records)
    ev["a2_placebo_populations"] = summarize_populations(pl_records)
    print(f"[E4d] A2 placebo: {len(pl_records)} records {time.time()-t0:.0f}s")

    dump(os.path.join(C.EVIDENCE_DIR, "controls_evidence.json"), ev)
    print(f"[done] {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
