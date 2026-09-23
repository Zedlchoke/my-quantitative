#!/usr/bin/env python
"""JRV2-DECISION-AUDIT-V1 — LOCKED blind-review sampler (seed 20260923).

Run AFTER rubric.md is committed, BEFORE any case sheet is read. Strata use
JEV effective labels (selection only — sheets carry no JEV information).
Design is fully deterministic from (census_rows.csv.gz, seed).
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

AUDIT = Path(__file__).resolve().parent.parent
CENSUS = AUDIT / "census/census_rows.csv.gz"
BLIND = AUDIT / "blind"

SEED = 20260923
PER_CELL_BUDGET = {"BTC_H1": 72, "BTC_H4": 72, "SPY_D1": 72}
LABELS = ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND",
          "TRANSITION_UNKNOWN")
MIN_PER_STRATUM = 8
CAP_PER_STRATUM = 26

STRENGTH_HIGH_CONF_MIN = 0.70


def strength_class(row):
    if row["effective"] != "TRANSITION_UNKNOWN":
        conf = float(row["phase_conf"]) if row["phase_conf"] else 0.0
        return "high_conf" if conf >= STRENGTH_HIGH_CONF_MIN else "low_conf"
    reason = row["effective_reason"]
    if reason.startswith("status_"):
        return "unk_provider_error"
    if reason.startswith("contradiction") or reason.startswith("phase_disagrees"):
        return "unk_contradiction"
    if reason == "low_margin":
        return "unk_low_margin"
    if reason == "low_confidence":
        return "unk_low_conf"
    return "unk_other"


def allocate(sizes, budget):
    """Largest-remainder allocation with MIN (take-all below MIN) and CAP."""
    quota = {}
    for lab, n in sizes.items():
        if n <= MIN_PER_STRATUM:
            quota[lab] = n
        else:
            q = max(MIN_PER_STRATUM, min(CAP_PER_STRATUM,
                                         budget * n / sum(sizes.values())))
            quota[lab] = q
    # floor + largest remainder to hit budget exactly (respecting take-alls)
    fixed = {lab: q for lab, q in quota.items() if sizes[lab] <= MIN_PER_STRATUM}
    flexible = {lab: q for lab, q in quota.items() if lab not in fixed}
    flex_budget = budget - sum(fixed.values())
    floored = {lab: int(q) for lab, q in flexible.items()}
    rem = flex_budget - sum(floored.values())
    order = sorted(flexible, key=lambda lab: (-(flexible[lab] - floored[lab]),
                                              -sizes[lab], lab))
    for lab in order[:max(0, rem)]:
        floored[lab] += 1
    out = {**fixed, **floored}
    # if mins pushed us over budget, trim from the largest quotas
    while sum(out.values()) > budget:
        lab = max(out, key=lambda l: (out[l], sizes[l], l))
        if out[lab] > MIN_PER_STRATUM and sizes[lab] > MIN_PER_STRATUM:
            out[lab] -= 1
        else:
            break
    return out


def main():
    rows = []
    with gzip.open(CENSUS, "rt") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    rng = np.random.default_rng(SEED)

    sample = []
    strata_report = {}
    for cell in ("BTC_H1", "BTC_H4", "SPY_D1"):
        cell_rows = [r for r in rows if r["cell"] == cell]
        sizes = Counter(r["effective"] for r in cell_rows)
        budget = PER_CELL_BUDGET[cell]
        alloc = allocate({lab: sizes.get(lab, 0) for lab in LABELS}, budget)
        strata_report[cell] = {"stratum_sizes": dict(sizes), "allocation": alloc}

        for lab, k in alloc.items():
            pool = [r for r in cell_rows if r["effective"] == lab]
            # bucket by (transition zone x strength), then round-robin folds
            buckets = defaultdict(lambda: defaultdict(list))
            for r in pool:
                zone = "zone" if r["in_transition_zone"] == "True" else "off"
                buckets[(zone, strength_class(r))][int(r["fold"])].append(r)
            for key in buckets:
                for fold in buckets[key]:
                    idx = rng.permutation(len(buckets[key][fold]))
                    buckets[key][fold] = [buckets[key][fold][i] for i in idx]
            picks = []
            keys = sorted(buckets)
            progress = True
            while len(picks) < k and progress:
                progress = False
                for key in keys:
                    folds = sorted(buckets[key])
                    for fold in folds:
                        if buckets[key][fold] and len(picks) < k:
                            picks.append(buckets[key][fold].pop())
                            progress = True
            assert len(picks) == k, (cell, lab, len(picks), k)
            for r in picks:
                sample.append({
                    "case_id": None, "cell": cell, "state_id": r["state_id"],
                    "bar_index": int(r["bar_index"]), "fold": int(r["fold"]),
                    "stratum": lab, "zone": "zone" if r["in_transition_zone"] == "True" else "off",
                    "strength": strength_class(r),
                    "effective_label_sealed": r["effective"],
                    "effective_reason_sealed": r["effective_reason"],
                    "phase_conf_sealed": r["phase_conf"],
                    "persisted_after_sealed": r["persisted_after"],
                    "switched_sealed": r["switched"],
                })

    # deterministic shuffled case order + ids
    order = rng.permutation(len(sample))
    sample = [sample[i] for i in order]
    for i, s in enumerate(sample):
        s["case_id"] = f"C{i + 1:03d}"

    # ---- case sheets: the ONLY reviewer-facing payload --------------------
    # sheets need the state payload -> rebuild from the census-independent
    # state reconstruction is unnecessary: the sheet is exactly
    # {bins, numerics, prior_*} which the census already verified equals the
    # request digest. Rebuild states via the frozen path for the sampled
    # state_ids only.
    sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/.worktrees/"
                       "jev-regime-router-v2/integration/research/control/"
                       "jev_regime_router_v2")
    from jrv2 import CELLS  # noqa: E402
    from jrv2.data import load_cell  # noqa: E402
    from jrv2.features import RegimeFeatures  # noqa: E402
    from jrv2.freezes import Freezes  # noqa: E402

    fz = Freezes(Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                      "jev-regime-router-v2/integration/research/control/"
                      "jev_regime_router_v2"))
    cell_cache = {}
    cases = []
    for s in sample:
        cell = s["cell"]
        if cell not in cell_cache:
            _, regime_bars, _ = load_cell(fz, cell)
            feats = RegimeFeatures(regime_bars)
            cell_cache[cell] = (regime_bars, feats)
        regime_bars, feats = cell_cache[cell]
        t = s["bar_index"]
        st = feats.numerics_at(t)
        assert st is not None, (cell, t)
        from jrv2.features import compute_bins, PRIOR_DIRECTION_MAP, PRIOR_STRUCTURE_MAP
        # prior from the census (persisted at t-1) — recompute locally
        # (persisted_after_sealed is persisted AFTER t; prior is what the
        # state carried, which the census row stores in *_recomputed cols)
        # we re-read the census row for exact prior fields:
        prior_pd, prior_ps = PRIOR_INDEX[(cell, s["state_id"])]
        sheet = {
            "cell": cell,
            "regime_clock": CELLS[cell]["regime_clock"],
            "bins": compute_bins(st),
            "numerics": {k: round(v, 6) for k, v in st.items()},
            "prior_structure": prior_ps,
            "prior_direction": prior_pd,
        }
        cases.append({"case_id": s["case_id"], "state_id": s["state_id"],
                      "sheet": sheet})

    BLIND.mkdir(parents=True, exist_ok=True)
    (BLIND / "sampling.json").write_text(json.dumps({
        "schema": "jrv2_decision_audit_blind_sampling@1",
        "seed": SEED, "rule": {
            "per_cell_budget": PER_CELL_BUDGET,
            "strata": "cell x effective label",
            "min_per_stratum": MIN_PER_STRATUM,
            "cap_per_stratum": CAP_PER_STRATUM,
            "within_stratum": "round-robin over (transition-zone x strength) "
                              "buckets, then folds; seeded shuffle inside buckets",
            "strength_classes": "labeled: high_conf>=0.70 vs low_conf; "
                                "unknown: low_conf/low_margin/contradiction/provider_error",
            "zone": "within +/-3 bars of a persisted switch",
        },
        "strata_report": strata_report,
        "n_cases": len(sample),
        "sample_sealed": sample,
    }, indent=1))
    with open(BLIND / "cases.jsonl", "w") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")

    # reviewer-facing rendered sheets (no JEV info, no bar index, no dates)
    lines = ["# BLIND CASE SHEETS — rubric: blind/rubric.md (LOCKED)",
             "", f"{len(cases)} cases, shuffled (seed {SEED}).",
                 "Fields: 9 bins, 14 numerics, prior lineage, cell + clock.", ""]
    for c in cases:
        sh = c["sheet"]
        lines.append(f"## {c['case_id']}  [{sh['cell']} / {sh['regime_clock']}]")
        lines.append(f"prior_structure={sh['prior_structure']}  prior_direction={sh['prior_direction']}")
        lines.append("bins: " + "  ".join(f"{k}={v}" for k, v in sorted(sh["bins"].items())))
        nums = "  ".join(f"{k}={v}" for k, v in sorted(sh["numerics"].items()))
        lines.append("numerics: " + nums)
        lines.append("")
    (BLIND / "case_sheets.md").write_text("\n".join(lines))
    print(f"sampler: {len(cases)} cases -> blind/cases.jsonl, case_sheets.md; "
          f"design -> blind/sampling.json")
    for cell, rep in strata_report.items():
        print(cell, rep["allocation"])


# prior fields per sampled state, read from census rows (persisted(t-1) map)
PRIOR_INDEX = {}


def load_prior_index():
    with gzip.open(CENSUS, "rt") as f:
        for r in csv.DictReader(f):
            PRIOR_INDEX[(r["cell"], r["state_id"])] = (
                r["prior_direction_recomputed"], r["prior_structure_recomputed"])


if __name__ == "__main__":
    load_prior_index()
    main()
