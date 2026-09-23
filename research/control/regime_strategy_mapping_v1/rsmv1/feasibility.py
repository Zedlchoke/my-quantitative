"""Phase 2 — regime sample feasibility (NO PnL anywhere in this module).

Preregistered floors (plan §4.0; A7-adjustable BEFORE outcome):
  floor_episodes_total   >= 20 independent episodes / regime / cell
  floor_episodes_fold    >= 3  episodes / regime / outer fold
  floor_decisions_fold   >= 100 eligible decisions / regime / outer fold
Below floor => NOT_RUN_THIN_REGIME for that regime x cell (specialist
defaults FLAT). BTC_H1 / BTC_H4 / SPY_D1 are never pooled.

Definitions (frozen):
- independent episode: maximal contiguous run of one persisted label over
  the cell's regime bars (post-warmup decisions only);
- an episode belongs to the outer fold containing its START bar (fold of a
  regime bar = the fold span containing its close ts; bars outside every
  span belong to no fold, e.g. warmup/gaps);
- eligible episode: length >= ELIGIBLE_MIN_BARS (6 = the persistence
  machine's min_dwell; a shorter episode cannot admit a confirmed entry);
- eligible decisions: regime bars inside eligible episodes, per fold.
"""

from __future__ import annotations

import json
from pathlib import Path

from .freezes import Freezes
from .regime_timeline import CellTimelines, episodes, rebuild_cell_timeline

FLOOR_EPISODES_TOTAL = 20
FLOOR_EPISODES_FOLD = 3
FLOOR_DECISIONS_FOLD = 100
ELIGIBLE_MIN_BARS = 6

PHASE_LABELS = ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND")
FEASIBILITY_SCHEMA = "rsmv1_regime_feasibility@1"


def fold_of_regime_bar(fz: Freezes, cell: str, ts_close: int) -> int:
    """Fold whose frozen span contains this regime-bar close (-1 if none)."""
    spans = fz.fold_contract["cells"][cell]["folds"]
    for fid, sp in enumerate(spans):
        a = _ts_ns(sp["start"])
        b = _ts_ns(sp["end"])
        if a <= ts_close <= b:
            return fid
    return -1


def _ts_ns(iso: str) -> int:
    """ISO (with or without Z / time) to ns UTC."""
    from datetime import datetime, timezone

    s = iso.replace("Z", "+00:00")
    if "T" not in s:
        s += "T00:00:00+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def measure_cell(cycle_dir: str | Path, cell: str) -> dict:
    """Full feasibility block for one cell. No PnL is read or computed."""
    cycle_dir = Path(cycle_dir).resolve()
    ct: CellTimelines = rebuild_cell_timeline(cycle_dir, cell)
    fz = Freezes(cycle_dir)
    ts = ct.ts
    eps_all = episodes(ct.persisted)

    fold_of = [fold_of_regime_bar(fz, cell, t) for t in ts]

    per_regime: dict[str, dict] = {}
    for label in PHASE_LABELS:
        eps = [e for e in eps_all if e["label"] == label]
        elig = [e for e in eps if e["length"] >= ELIGIBLE_MIN_BARS]
        lengths = sorted(e["length"] for e in eps)
        per_fold = {}
        for fid in range(4):
            eps_f = [e for e in eps if fold_of[e["start"]] == fid]
            elig_f = [e for e in elig if fold_of[e["start"]] == fid]
            dec_f = sum(e["length"] for e in elig_f)
            per_fold[fid] = {
                "episodes": len(eps_f),
                "eligible_episodes": len(elig_f),
                "eligible_decisions": dec_f,
                "floor_episodes_ok": len(eps_f) >= FLOOR_EPISODES_FOLD,
                "floor_decisions_ok": dec_f >= FLOOR_DECISIONS_FOLD,
            }
        total_elig_dec = sum(e["length"] for e in elig)
        thin = len(eps) < FLOOR_EPISODES_TOTAL or any(
            (not v["floor_episodes_ok"]) or (not v["floor_decisions_ok"])
            for v in per_fold.values()
        )
        # margin-to-floor: how many times each floor is met (min across all)
        margins = [
            len(eps) / FLOOR_EPISODES_TOTAL if FLOOR_EPISODES_TOTAL else float("inf"),
        ] + [
            v["episodes"] / FLOOR_EPISODES_FOLD if FLOOR_EPISODES_FOLD else float("inf")
            for v in per_fold.values()
        ] + [
            v["eligible_decisions"] / FLOOR_DECISIONS_FOLD
            if FLOOR_DECISIONS_FOLD
            else float("inf")
            for v in per_fold.values()
        ]
        per_regime[label] = {
            "episodes_total": len(eps),
            "eligible_episodes_total": len(elig),
            "eligible_decisions_total": total_elig_dec,
            "episode_lengths": {
                "min": lengths[0] if lengths else 0,
                "p25": lengths[len(lengths) // 4] if lengths else 0,
                "median": lengths[len(lengths) // 2] if lengths else 0,
                "p75": lengths[3 * len(lengths) // 4] if lengths else 0,
                "max": lengths[-1] if lengths else 0,
            },
            "market_time_bars": sum(lengths),
            "per_fold": per_fold,
            "margin_to_floor_min": round(min(margins), 3),
            "verdict": "NOT_RUN_THIN_REGIME" if thin else "SAMPLE_OK",
        }

    transitions = sum(1 for r in ct.timeline.rows if r["switched"])
    return {
        "schema": FEASIBILITY_SCHEMA,
        "cell": cell,
        "n_decisions": ct.stats["n_decisions"],
        "transitions_total": transitions,
        "floors": {
            "episodes_total": FLOOR_EPISODES_TOTAL,
            "episodes_per_fold": FLOOR_EPISODES_FOLD,
            "decisions_per_fold": FLOOR_DECISIONS_FOLD,
            "eligible_min_bars": ELIGIBLE_MIN_BARS,
        },
        "per_regime": per_regime,
        "pooling_law": "BTC_H1/BTC_H4/SPY_D1 never pooled",
    }


def run_all(cycle_dir: str | Path, out_dir: str | Path | None = None) -> dict:
    cycle_dir = Path(cycle_dir).resolve()
    out = {
        "schema": FEASIBILITY_SCHEMA + ".bundle",
        "cycle": "REGIME-STRATEGY-MAPPING-V1",
        "phase": "P2_FEASIBILITY_NO_PNL",
        "cells": {c: measure_cell(cycle_dir, c) for c in ("BTC_H1", "BTC_H4", "SPY_D1")},
    }
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "regime_sample_feasibility.json").write_text(
            json.dumps(out, indent=1, sort_keys=True)
        )
    return out
