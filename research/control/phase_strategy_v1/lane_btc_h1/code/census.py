"""Census for BTC_H1 — occupancy / episode / dwell / transition statistics.

Outcome-blindness law (plan sec 7.3): counts, occupancy, dwell and transition
statistics ONLY. No returns, no PnL, no equity.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from phase_rule import PHASES


def episodes(mask: np.ndarray) -> list[tuple[int, int]]:
    """Maximal contiguous runs of mask; returns [start_idx, end_idx] inclusive."""
    runs: list[tuple[int, int]] = []
    start = None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        elif not m and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(mask) - 1))
    return runs


def dwell_stats(lengths: list[int]) -> dict:
    if not lengths:
        return {"count": 0, "min_bars": None, "p25_bars": None,
                "median_bars": None, "p75_bars": None, "max_bars": None}
    a = np.array(lengths, dtype=float)
    return {
        "count": int(len(a)),
        "min_bars": float(a.min()),
        "p25_bars": float(np.percentile(a, 25)),
        "median_bars": float(np.median(a)),
        "p75_bars": float(np.percentile(a, 75)),
        "max_bars": float(a.max()),
    }


def margin_to_floor(value: float | int, floor: int) -> dict:
    v = float(value)
    return {
        "value": v, "floor": float(floor), "margin": v - floor,
        "pass": bool(v >= floor),
    }


def slot_for_phase(phase: str, thin_phases: list[str]) -> str | None:
    """Proposal-slot law: a phase below ANY floor is NOT_RUN_THIN_PHASE and
    its strategy slot is FLAT (valid result, reported, never scored)."""
    if phase in thin_phases:
        return "FLAT (NOT_RUN_THIN_PHASE)"
    return None


def census_cell(labels: list[str], opens: pd.DatetimeIndex,
                fold_bounds: list[tuple[pd.Timestamp, pd.Timestamp]],
                floors: dict) -> dict:
    """Full census. labels/opens are the POST-warmup series; fold_bounds are
    [start_open, end_open_exclusive] per fold in the same index space."""
    lab = np.array(labels)
    out: dict = {"per_fold": {}, "per_phase_cell_totals": {}, "transitions": {}}

    seg: dict[str, dict] = {}
    for phase in PHASES:
        seg[phase] = {"episodes": [], "decisions": 0, "truncated_episodes": 0}
    transition_pairs: dict[str, int] = {}
    unknown_runs: list[int] = []
    run_start = 0

    for f_idx, (f_start, f_end) in enumerate(fold_bounds):
        sel = (opens >= f_start) & (opens < f_end)
        idx = np.where(sel)[0]
        sub = lab[idx]
        fkey = f"F{f_idx + 1}"
        fdat: dict = {"fold": fkey, "bars": int(len(sub))}
        for phase in PHASES:
            mask = sub == phase
            runs = episodes(mask)
            # truncated at fold edge?
            trunc = 0
            if runs:
                s0, e0 = runs[0]
                if s0 == 0 and idx[s0] == idx[0]:
                    trunc += 1
                if runs[-1][1] == len(sub) - 1 and idx[runs[-1][1]] == idx[-1]:
                    trunc += 1
            lens = [e - s + 1 for s, e in runs]
            seg[phase]["episodes"].append((f_idx, lens, trunc))
            seg[phase]["decisions"] += int(mask.sum())
            fdat[phase] = {
                "bars": int(mask.sum()),
                "occupancy_share": float(mask.mean()) if len(sub) else 0.0,
                "episodes": len(lens),
                "truncated_episodes": trunc,
                "dwell": dwell_stats(lens),
            }
        # transitions inside fold
        for a, b in zip(sub[:-1], sub[1:]):
            if a != b:
                transition_pairs[f"{a}->{b}"] = transition_pairs.get(f"{a}->{b}", 0) + 1
        # longest UNKNOWN run inside fold
        ur = [e - s + 1 for s, e in episodes(sub == "TRANSITION_UNKNOWN")]
        unknown_runs.extend(ur)
        fdat["unknown_share"] = float((sub == "TRANSITION_UNKNOWN").mean())
        fdat["longest_unknown_run_bars"] = int(max(ur)) if ur else 0
        out["per_fold"][fkey] = fdat

    for phase in PHASES:
        all_lens = [n for _, lens, _ in seg[phase]["episodes"] for n in lens]
        trunc_total = sum(t for _, _, t in seg[phase]["episodes"])
        total = {
            "decisions_total": seg[phase]["decisions"],
            "episodes_total": len(all_lens),
            "truncated_at_fold_edges": trunc_total,
            "dwell": dwell_stats(all_lens),
            "floors": {
                "episodes_per_cell": margin_to_floor(
                    len(all_lens), floors["episodes_per_phase_per_cell_total"]),
                "episodes_per_fold": {
                    f"F{fi + 1}": margin_to_floor(
                        len(lens), floors["episodes_per_phase_per_fold"])
                    for fi, lens, _ in seg[phase]["episodes"]
                },
                "decisions_per_fold": {},
            },
        }
        # decisions per fold cleanly
        for i, (f_start, f_end) in enumerate(fold_bounds):
            sel = (opens >= f_start) & (opens < f_end)
            n = int(((lab[sel] == phase)).sum())
            total["floors"]["decisions_per_fold"][f"F{i + 1}"] = margin_to_floor(
                n, floors["eligible_decisions_per_phase_per_fold"])
        out["per_phase_cell_totals"][phase] = total

    out["transitions"]["counts"] = transition_pairs
    out["unknown"] = {
        "share_cell": float((lab == "TRANSITION_UNKNOWN").mean()),
        "longest_run_bars": int(max(unknown_runs)) if unknown_runs else 0,
    }
    thin = [
        p for p in PHASES
        if not out["per_phase_cell_totals"][p]["floors"]["episodes_per_cell"]["pass"]
        or any(not v["pass"] for v in
               out["per_phase_cell_totals"][p]["floors"]["episodes_per_fold"].values())
        or any(not v["pass"] for v in
               out["per_phase_cell_totals"][p]["floors"]["decisions_per_fold"].values())
    ]
    out["thin_phases"] = thin
    return out
