"""Schedule comparison: Spearman rho over the three V8/V9-house
variants, pooled max |rho|, and P-2 margins.

Variants (identical semantics to the V8/V9 D2 novelty machinery):

- ``cellwise_signed_full_grid``: every (grid day, shared pair) cell of
  the combined active date span, zeros where a book is flat;
- ``cellwise_union_active``: only cells where at least one book is
  active;
- ``netsigned_union_dates_shared_pairs``: per grid day the summed
  signed exposure over shared pairs, sampled on days where either book
  carries any exposure.

Spearman uses average-tie ranks; a constant vector yields rho=None
(recorded, never silently zero).  All comparisons are restricted to the
shared pairs and to the NG1 frozen grid (committed ancestor cells dated
outside S0 drop out before comparison).
"""

from __future__ import annotations

import math


def _avg_tie_ranks(v: list[float]) -> list[float]:
    order = sorted(range(len(v)), key=lambda i: v[i])
    ranks = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float | None:
    """Spearman rank correlation with average-tie ranks; None when
    either vector is constant or the sample is smaller than 3."""
    n = len(x)
    if n != len(y) or n < 3:
        return None
    rx, ry = _avg_tie_ranks(x), _avg_tie_ranks(y)
    mx = math.fsum(rx) / n
    my = math.fsum(ry) / n
    cov = math.fsum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = math.fsum((a - mx) ** 2 for a in rx)
    vy = math.fsum((b - my) ** 2 for b in ry)
    if vx <= 0.0 or vy <= 0.0:
        return None
    return cov / math.sqrt(vx * vy)


def _parse_cells(cells: dict) -> tuple[dict[str, float], set[str],
                                       set[str]]:
    vals: dict[str, float] = {}
    dates: set[str] = set()
    pairs: set[str] = set()
    for key, v in cells.items():
        d, p = key.split("|")
        vals[key] = float(v)
        dates.add(d)
        pairs.add(p)
    return vals, dates, pairs


def compare_schedules(a_cells: dict, b_cells: dict,
                      grid_days_iso: list[str],
                      shared_pairs: list[str]) -> dict:
    """All-variant comparison of two signed schedules on the frozen
    grid restricted to ``shared_pairs``.  Returns per-variant rho and
    sample sizes."""
    av, ad, ap = _parse_cells(a_cells)
    bv, bd, bp = _parse_cells(b_cells)
    pairs = [p for p in shared_pairs if p in ap and p in bp]
    if not pairs:
        return {"shared_pairs": [], "verdict": "NO_SHARED_PAIRS",
                "variants": {}}
    grid_set = set(grid_days_iso)
    ad = {d for d in ad if d in grid_set}
    bd = {d for d in bd if d in grid_set}
    if not ad or not bd:
        return {"shared_pairs": pairs, "verdict": "NO_ACTIVE_DATES_IN_GRID",
                "variants": {}}
    active_dates = sorted(ad | bd)
    span = [d for d in grid_days_iso if active_dates[0] <= d <= active_dates[-1]]

    out = {"shared_pairs": pairs,
           "span_first": span[0] if span else None,
           "span_last": span[-1] if span else None,
           "active_dates_a": len(ad), "active_dates_b": len(bd),
           "variants": {}}

    # 1. cellwise signed full grid
    x, y = [], []
    for d in span:
        for p in pairs:
            x.append(av.get(f"{d}|{p}", 0.0))
            y.append(bv.get(f"{d}|{p}", 0.0))
    out["variants"]["cellwise_signed_full_grid"] = {
        "n": len(x), "rho": spearman(x, y)}

    # 2. cellwise union active
    x, y = [], []
    joint = 0
    for d in active_dates:
        if d not in grid_set:
            continue
        for p in pairs:
            ka, kb = f"{d}|{p}", f"{d}|{p}"
            va, vb = av.get(ka, 0.0), bv.get(kb, 0.0)
            if va != 0.0 or vb != 0.0:
                x.append(va)
                y.append(vb)
                if va != 0.0 and vb != 0.0:
                    joint += 1
    out["variants"]["cellwise_union_active"] = {
        "n": len(x), "rho": spearman(x, y), "joint_active_cells": joint}

    # 3. netsigned union dates, shared pairs
    x, y = [], []
    joint_dates = 0
    for d in active_dates:
        if d not in grid_set:
            continue
        sa = math.fsum(av.get(f"{d}|{p}", 0.0) for p in pairs)
        sb = math.fsum(bv.get(f"{d}|{p}", 0.0) for p in pairs)
        if sa != 0.0 or sb != 0.0:
            x.append(sa)
            y.append(sb)
            if sa != 0.0 and sb != 0.0:
                joint_dates += 1
    out["variants"]["netsigned_union_dates_shared_pairs"] = {
        "n": len(x), "rho": spearman(x, y), "joint_active_dates": joint_dates}

    rhos = [v["rho"] for v in out["variants"].values()
            if v["rho"] is not None]
    out["max_abs_rho"] = max((abs(r) for r in rhos), default=None)
    out["verdict"] = "MEASURED" if rhos else "UNMEASURABLE_CONSTANT"
    return out


def pooled_max_abs_rho(comparisons: dict[str, dict]) -> dict:
    """Aggregate a {veto_name: compare_schedules(...)} map into the
    pooled worst shape (P-2 margin basis)."""
    rows = []
    for name, cmp in comparisons.items():
        worst_variant = None
        worst_abs = None
        for vname, v in cmp.get("variants", {}).items():
            r = v.get("rho")
            if r is None:
                continue
            if worst_abs is None or abs(r) > worst_abs:
                worst_abs, worst_variant = abs(r), vname
        rows.append({"veto": name,
                     "max_abs_rho": worst_abs,
                     "worst_variant": worst_variant,
                     "verdict": cmp.get("verdict")})
    measured = [r for r in rows if r["max_abs_rho"] is not None]
    if not measured:
        return {"rows": rows, "max_pooled_abs_rho": None,
                "worst": None, "worst_variant": None}
    worst = max(measured, key=lambda r: r["max_abs_rho"])
    return {"rows": rows,
            "max_pooled_abs_rho": worst["max_abs_rho"],
            "worst": worst["veto"],
            "worst_variant": worst["worst_variant"]}
