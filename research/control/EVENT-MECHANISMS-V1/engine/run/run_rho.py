"""E5 — ancestry rho battery runner (pre-PnL bar 0.20; RECORD ONLY)."""
from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from datetime import date, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emv1 import config as C
from emv1.loaders import load_n4_map
from emv1.panel import Panel
from emv1 import rho as R


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w"), indent=1, sort_keys=True)


def read_records(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def main() -> None:
    t0 = time.time()
    n4 = load_n4_map()
    tickers = sorted({n4[c]["ticker"] for c in n4} | {"SPY"})
    panel = Panel(tickers)
    print(f"[panel] {time.time()-t0:.0f}s")

    a1_recs = read_records(os.path.join(C.EVIDENCE_DIR, "a1_decisions.jsonl"))
    a2_recs = read_records(os.path.join(C.EVIDENCE_DIR, "a2_decisions.jsonl"))
    a1_anchor = [r for r in a1_recs if r["arm_id"] == "A1-ANCHOR"]
    a2_anchor = [r for r in a2_recs if r["arm_id"] == "A2-ANCHOR"]

    ind_a1 = R.identity_indicator(a1_anchor, panel.names)
    ind_a2 = R.identity_indicator(a2_anchor, panel.names)

    # ---- proxy dead-observables from staged bytes ----
    rev5 = {t: R.proxy_reversal(ns, 5) for t, ns in panel.names.items()}
    rev20 = {t: R.proxy_reversal(ns, 20) for t, ns in panel.names.items()}
    mom60 = {t: R.proxy_momentum(ns, 60) for t, ns in panel.names.items()}
    am28_lvl = {t: R.proxy_amihud(ns, 28) for t, ns in panel.names.items()}
    am63_lvl = {t: R.proxy_amihud(ns, 63) for t, ns in panel.names.items()}
    am28 = R.cross_sectional_rank_scale(am28_lvl, panel.names)
    am63 = R.cross_sectional_rank_scale(am63_lvl, panel.names)

    # declared-plan cadence (A2): trailing-180d count of aff10b5One='1'
    # purchase accessions per issuer, from the parsed A2 accession universe.
    a2_days = json.load(open(os.path.join(C.EVIDENCE_DIR, "a2_issuer_days.json")))
    by_cik = defaultdict(list)
    for d in a2_days:
        by_cik[d["cik"]].append((d["day"], d["plan_flagged_accessions"]))
    ticker_by_cik = {c: n4[c]["ticker"] for c in n4}
    plan_by_ticker = defaultdict(list)
    for cik, rows in by_cik.items():
        t = ticker_by_cik.get(cik)
        if t:
            plan_by_ticker[t] = sorted(rows)
    cadence = {}
    for t, rows in plan_by_ticker.items():
        ns = panel.names.get(t)
        if ns is None:
            continue
        arr = np.zeros(len(ns.dates), dtype=np.float64)
        days = [date.fromisoformat(d) for d, _ in rows]
        vals = [v for _, v in rows]
        for i, ds in enumerate(ns.dates):
            cutoff = date.fromisoformat(ds) - timedelta(days=180)
            arr[i] = sum(v for d, v in zip(days, vals) if cutoff < d <= date.fromisoformat(ds))
        cadence[t] = arr

    proxies = {
        "reversal_5d": rev5,
        "reversal_20d": rev20,
        "momentum_60d": mom60,
        "amihud_28d": am28,
        "amihud_63d": am63,
        "declared_plan_cadence_180d": cadence,
    }
    ev = {"construction_notes": {
        "reversal_kd": "-sign(raw k-session return) on bars t-1, t-1-k (closed before session t)",
        "momentum_60d": "+sign(raw 60-session return), same closed-bar basis",
        "amihud_kd": "mean(|ret_1d|/dollar-volume) trailing k closed sessions, cross-sectional percentile rank scaled [-1,1]",
        "declared_plan_cadence_180d": ("per issuer, count of aff10b5One='1' P-accessions in trailing 180 calendar days; "
                                        "universe = A2 parsed accession set (stream carries no plan flag — measured); "
                                        "aff10b5One exists only on post-2023 forms — pre-2023 cadence is 0 by construction"),
        "identity_indicator": "signed direction (+1 LONG / -1 SHORT / 0 none) at each (name, entry_session)",
    }}
    ev["rho_a1"] = R.rho_table(ind_a1, proxies, panel.names)
    ev["rho_a2"] = R.rho_table(ind_a2, proxies, panel.names)
    ev["stream_rho_a1_vs_a2"] = R.stream_rho_between(ind_a1, ind_a2, panel.names)
    ev["bar"] = C.RHO_BAR

    over = [r for r in ev["rho_a1"] + ev["rho_a2"] if r["over_bar"]]
    ev["any_over_bar"] = bool(over)
    ev["over_bar_rows"] = over
    dump(os.path.join(C.EVIDENCE_DIR, "rho_evidence.json"), ev)

    print("A1 rhos (pooled):")
    for r in ev["rho_a1"]:
        if r["scope"] == "POOLED":
            print(f"  {r['proxy']:28s} spearman={r['spearman']} n={r['n_points']} over={r['over_bar']}")
    print("A2 rhos (pooled):")
    for r in ev["rho_a2"]:
        if r["scope"] == "POOLED":
            print(f"  {r['proxy']:28s} spearman={r['spearman']} n={r['n_points']} over={r['over_bar']}")
    print("A1 vs A2 stream rho:")
    for r in ev["stream_rho_a1_vs_a2"]:
        print(f"  {r['scope']}: spearman={r['spearman']} overlap={r['overlap_points']}")
    print(f"ANY OVER BAR 0.20: {ev['any_over_bar']} ({len(over)} rows)")
    print(f"[done] {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
