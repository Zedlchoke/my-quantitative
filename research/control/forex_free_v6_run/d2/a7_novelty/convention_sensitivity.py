#!/usr/bin/env python3
"""A7 novelty audit SUPPLEMENT: exposure-cell convention sensitivity.

The main audit freezes the convention "a position opened at close(f) occupies
exposure cells f..x-1 (entry instant counted as held)".  A defensible
alternative reading counts the first FULL held session instead: cells
f+1..x.  This script rebuilds the four proposal anchor schedules under the
+1-session shift and recomputes the POOLED gate statistic vs the two V5
books and the V4 commodity-bloc exposure book -- the comparisons that carry
the main verdicts -- plus the A4P1-vs-A6P1 intra duplication statistic.
No PnL; schedule construction and rank correlations only.
"""
import importlib.util
import json
import math
from collections import defaultdict

import numpy as np

SPEC = importlib.util.spec_from_file_location(
    "m", "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v6/"
         "d2-a7-novelty/research/control/forex_free_v6_run/d2/a7_novelty/"
         "compute_ancestry_rhos.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

OUT = m.OUT


def shift_cells_plus1(sched):
    """Shift every exposure cell one decision day LATER within its pair's
    series (the alternative 'first-full-session' convention)."""
    out = {}
    per_pair = defaultdict(list)
    for (d, p) in sched.cells:
        per_pair[p].append(d)
    for p, ds in per_pair.items():
        ser = m.SERIES[p]
        for d in ds:
            j = ser.index(d)
            if j + 1 < len(ser):
                out[(ser[j + 1], p)] = sched.cells[(d, p)]
    return out


def pooled_rho(cells_a, cells_b, pairs, zero_fill="full"):
    if zero_fill == "full":
        xs, ys = [], []
        for p in pairs:
            for d in m.SERIES[p]:
                if not (m.S0_START <= d <= m.S0_END):
                    continue
                xs.append(float(cells_a.get((d, p), 0)))
                ys.append(float(cells_b.get((d, p), 0)))
    elif zero_fill == "union":
        keys = sorted(set(k for k in cells_a if k[1] in pairs) |
                      set(k for k in cells_b if k[1] in pairs))
        xs = [float(cells_a.get(k, 0)) for k in keys]
        ys = [float(cells_b.get(k, 0)) for k in keys]
    else:  # netsigned
        ma, mb = defaultdict(dict), defaultdict(dict)
        for (d, p), v in cells_a.items():
            if p in pairs:
                ma[d][p] = v
        for (d, p), v in cells_b.items():
            if p in pairs:
                mb[d][p] = v
        dates = sorted(set(ma) | set(mb))
        xs = [float(sum(ma.get(d, {}).values())) for d in dates]
        ys = [float(sum(mb.get(d, {}).values())) for d in dates]
    return m.spearman(xs, ys), len(xs)


def main():
    anchors = {
        "A4P1": m.sched_a4p1(False, 5),
        "A4P2": m.sched_a4p2(False, 5),
        "A6P1": m.sched_a6p1("compression", False),
        "A6P2": m.sched_a6p2(0),
    }
    v5a = m.sched_v5_family(m.CLK_V5, False)
    v5s = m.sched_v5_family(m.CLK_V5, True)
    differential = m.load_ledger_reader(
        f"{m.ROOT}/research/control/forex_free_v5_run/announcement_ledger_v5_extension.jsonl")
    carry = m.sched_carry(differential, False)
    _, v4exp = m.sched_commodity_bloc()

    ancestors = {"V5_anchor": v5a, "V5_sham": v5s,
                 "carry_unconditional": carry, "V4_commodity_bloc_exposure": v4exp}

    res = {"schema": "forex_free_v6_d2_a7n_convention_sensitivity_v1",
           "alternative_convention": "position occupies f+1..x (first FULL held session counted; entry-close instant not counted)",
           "frozen_convention": "position occupies f..x-1 (entry-close instant counted)",
           "note": "ancestor books are unchanged (their cell convention is the V5 runner's own); only the proposal schedules are re-expressed",
           "comparisons": {}}

    for pn, s in anchors.items():
        shifted = shift_cells_plus1(s)
        for an, sa in ancestors.items():
            pairs = sorted(set(p for _, p in s.cells) & set(p for _, p in sa.cells))
            if not pairs:
                continue
            r_frozen_c = pooled_rho(s.cells, sa.cells, pairs, "full")[0]
            r_alt_c = pooled_rho(shifted, sa.cells, pairs, "full")[0]
            r_frozen_u = pooled_rho(s.cells, sa.cells, pairs, "union")[0]
            r_alt_u = pooled_rho(shifted, sa.cells, pairs, "union")[0]
            r_frozen_n = pooled_rho(s.cells, sa.cells, pairs, "nets")[0]
            r_alt_n = pooled_rho(shifted, sa.cells, pairs, "nets")[0]
            key = f"{pn}_anchor__vs__{an}"
            res["comparisons"][key] = {
                "pooled_rho_frozen_convention": {
                    "cellwise_full": None if r_frozen_c is None else round(r_frozen_c, 4),
                    "cellwise_union": None if r_frozen_u is None else round(r_frozen_u, 4),
                    "netsigned": None if r_frozen_n is None else round(r_frozen_n, 4)},
                "pooled_rho_shifted_convention": {
                    "cellwise_full": None if r_alt_c is None else round(r_alt_c, 4),
                    "cellwise_union": None if r_alt_u is None else round(r_alt_u, 4),
                    "netsigned": None if r_alt_n is None else round(r_alt_n, 4)},
            }
    # intra A4P1 vs A6P1 under the shifted convention
    s1, s2 = anchors["A4P1"], anchors["A6P1"]
    sh1, sh2 = shift_cells_plus1(s1), shift_cells_plus1(s2)
    pairs = sorted(set(p for _, p in s1.cells) & set(p for _, p in s2.cells))
    res["intra_A4P1_vs_A6P1_shifted"] = {
        "cellwise_full": None if pooled_rho(sh1, sh2, pairs, "full")[0] is None
        else round(pooled_rho(sh1, sh2, pairs, "full")[0], 4),
        "netsigned": None if pooled_rho(sh1, sh2, pairs, "nets")[0] is None
        else round(pooled_rho(sh1, sh2, pairs, "nets")[0], 4)}

    json.dump(res, open(f"{OUT}/convention_sensitivity.json", "w"), indent=1)
    for k, v in res["comparisons"].items():
        print(k, json.dumps(v))
    print("intra:", json.dumps(res["intra_A4P1_vs_A6P1_shifted"]))


if __name__ == "__main__":
    main()
