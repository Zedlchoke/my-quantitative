"""PSV1 lane_btc_h4 — label reliability census (plan §5.4, §4.3).

Census = counts / occupancy / dwell / transitions ONLY (outcome-blind law,
plan §7.3). No strategy returns of any kind are computed here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .phase_rule import UNKNOWN

ERAS_OF_FOLD = {f"F{i+1}": e["era"] for i, e in enumerate(config.ERAS)}


def era_fold_assignment(bucket_ms: pd.Series, data_end_ms: int,
                        warmup: int) -> pd.DataFrame:
    """Assign era + fold by bucket open time; post-warmup mask included.

    Fold law: 4 eras => F_i = ERA-Bi boundaries (post-warmup). Buckets before
    the post-warmup start carry fold=None (excluded from floors/census).
    """
    ts = pd.to_datetime(bucket_ms, unit="ms", utc=True)
    df = pd.DataFrame({"bucket_ms": bucket_ms.to_numpy(), "ts": ts})
    df["era"] = None
    df["fold"] = None
    for i, e in enumerate(config.ERAS):
        start = pd.Timestamp(e["start"], tz="UTC")
        end = (pd.Timestamp(data_end_ms, unit="ms", tz="UTC")
               if e["end"] is None else pd.Timestamp(e["end"], tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1))
        m = (df["ts"] >= start) & (df["ts"] <= end)
        df.loc[m, "era"] = e["era"]
        df.loc[m, "fold"] = f"F{i+1}"
    df["post_warmup"] = np.arange(len(df)) >= warmup
    df.loc[~df["post_warmup"], ["era", "fold"]] = None
    return df.drop(columns=["ts"])


def episodes(mask: np.ndarray) -> list[tuple[int, int]]:
    """Maximal contiguous runs of True. Returns list of (start_idx, end_idx) inclusive."""
    out = []
    n = len(mask)
    t = 0
    while t < n:
        if mask[t]:
            s = t
            while t + 1 < n and mask[t + 1]:
                t += 1
            out.append((s, t))
        t += 1
    return out


def dwell_stats(lengths: list[int]) -> dict:
    if not lengths:
        return {"n": 0, "min": None, "p25": None, "median": None, "p75": None, "max": None}
    a = np.array(lengths, dtype="int64")
    return {
        "n": int(a.size),
        "min": int(a.min()),
        "p25": float(np.percentile(a, 25)),
        "median": float(np.median(a)),
        "p75": float(np.percentile(a, 75)),
        "max": int(a.max()),
    }


def census_for_labels(labels: pd.Series, assign: pd.DataFrame) -> dict:
    """Full per phase x era x fold census + margins (no PnL anywhere)."""
    lab = labels.to_numpy()
    folds = assign["fold"].to_numpy()
    post = assign["post_warmup"].to_numpy()
    usable = post & pd.notna(folds)
    fold_names = sorted({f for f in folds[usable]})

    per: dict = {}
    cell_episode_counts: dict[str, int] = {ph: 0 for ph in config.PHASES}
    cell_decision_counts: dict[str, int] = {ph: 0 for ph in config.PHASES}

    # cell-level episodes (across the full post-warmup window, folds ignored
    # for the 20/cell floor; run boundaries = maximal contiguous runs)
    for ph in config.PHASES:
        mask = lab == ph
        eps = episodes(mask)
        cell_episode_counts[ph] = len(eps)
        cell_decision_counts[ph] = int(mask.sum())

    for fold in fold_names:
        fm = usable & (folds == fold)
        idx = np.where(fm)[0]
        trans: dict[str, int] = {ph: 0 for ph in config.TRADED_PHASES}
        for ph in config.PHASES:
            mask = np.zeros(len(lab), dtype=bool)
            mask[idx] = lab[idx] == ph
            eps_in_fold = episodes(mask)
            lengths = [e - s + 1 for s, e in eps_in_fold]
            # transitions into ph within fold: True-run starts
            n_trans = len(eps_in_fold)
            trans[ph] = n_trans
            n_dec = int(mask.sum())
            per[f"{ph}|{fold}"] = {
                "phase": ph, "fold": fold, "era": ERAS_OF_FOLD.get(fold),
                "occupancy_bars": n_dec,
                "occupancy_share_of_fold": float(n_dec / max(1, len(idx))),
                "episodes": len(eps_in_fold),
                "dwell_bars": dwell_stats(lengths),
                "transitions_into": n_trans,
                "unknown_share_of_fold": None,  # filled below
                "margin_episodes_fold": len(eps_in_fold) - config.FLOOR_EPISODES_FOLD,
                "margin_decisions_fold": n_dec - config.FLOOR_DECISIONS_FOLD,
                "floor_met_fold": bool(
                    len(eps_in_fold) >= config.FLOOR_EPISODES_FOLD
                    and n_dec >= config.FLOOR_DECISIONS_FOLD),
            }
        # UNKNOWN share + longest UNKNOWN run per fold
        umask = np.zeros(len(lab), dtype=bool)
        umask[idx] = lab[idx] == UNKNOWN
        ueps = episodes(umask)
        longest_unknown = max([e - s + 1 for s, e in ueps], default=0)
        for ph in config.PHASES:
            per[f"{ph}|{fold}"]["unknown_share_of_fold"] = float(umask.sum() / max(1, len(idx)))
            per[f"{ph}|{fold}"]["longest_unknown_run_in_fold"] = int(longest_unknown)

    # margins vs cell floor + phase-level thin verdict
    summary: dict[str, dict] = {}
    for ph in config.PHASES:
        fold_flags = [per[f"{ph}|{f}"]["floor_met_fold"] for f in fold_names
                      if f"{ph}|{f}" in per]
        meets = (cell_episode_counts[ph] >= config.FLOOR_EPISODES_CELL
                 and all(fold_flags) and bool(fold_flags))
        summary[ph] = {
            "episodes_cell_total": cell_episode_counts[ph],
            "margin_episodes_cell": cell_episode_counts[ph] - config.FLOOR_EPISODES_CELL,
            "decisions_cell_total": cell_decision_counts[ph],
            "all_folds_meet_floor": bool(fold_flags) and all(fold_flags),
            "floor_met": bool(meets),
            "verdict": "DATA_SUFFICIENT" if meets else "NOT_RUN_THIN_PHASE",
        }

    return {
        "schema": "psv1_lane_btc_h4_census@1",
        "floors": {
            "episodes_per_phase_cell": config.FLOOR_EPISODES_CELL,
            "episodes_per_phase_fold": config.FLOOR_EPISODES_FOLD,
            "eligible_decisions_per_phase_fold": config.FLOOR_DECISIONS_FOLD,
            "note": "floors immutable (plan §4.3); below floor => NOT_RUN_THIN_PHASE, slot FLAT",
        },
        "fold_names": fold_names,
        "per_phase_era_fold": per,
        "per_phase_summary": summary,
        "outcome_blindness": "occupancy/episodes/dwell/transitions only; no strategy results computed or stored",
    }
