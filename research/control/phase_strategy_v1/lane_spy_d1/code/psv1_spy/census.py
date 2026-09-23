"""Label reliability census (counts/occupancy/dwell/transitions ONLY; no PnL)
and the immutable floor-margin calculator (plan section 4.3).
"""

from typing import Dict, List, Sequence, Tuple

from .phase_rule import (
    ACCUMULATION,
    DISTRIBUTION,
    DOWNTREND,
    PHASES,
    UNKNOWN,
    UPTREND,
)

NAMED_PHASES = (ACCUMULATION, UPTREND, DISTRIBUTION, DOWNTREND)
FLOOR_EPISODES_CELL = 20
FLOOR_EPISODES_FOLD = 3
FLOOR_DECISIONS_FOLD = 100


def episodes(lengths: Sequence[int]) -> List[int]:
    """Maximal contiguous runs of one label inside a fold (fold-local)."""
    out: List[int] = []
    run = 0
    for v in lengths:
        if v:
            run += 1
        elif run:
            out.append(run)
            run = 0
    if run:
        out.append(run)
    return out


def dwell_stats(runs: Sequence[int]) -> Dict[str, float]:
    if not runs:
        return {
            "count": 0,
            "min": 0,
            "p25": 0.0,
            "median": 0.0,
            "p75": 0.0,
            "max": 0,
        }
    xs = sorted(runs)

    def q(p: float) -> float:
        if len(xs) == 1:
            return float(xs[0])
        idx = p * (len(xs) - 1)
        lo = int(idx)
        hi = min(lo + 1, len(xs) - 1)
        frac = idx - lo
        return round(xs[lo] * (1 - frac) + xs[hi] * frac, 3)

    return {
        "count": len(xs),
        "min": xs[0],
        "p25": q(0.25),
        "median": q(0.5),
        "p75": q(0.75),
        "max": xs[-1],
    }


def longest_run(lengths: Sequence[int]) -> int:
    best = run = 0
    for v in lengths:
        run = run + 1 if v else 0
        best = max(best, run)
    return best


def transition_matrix(labels: Sequence[str]) -> Dict[str, Dict[str, int]]:
    m = {a: {b: 0 for b in PHASES} for a in PHASES}
    for a, b in zip(labels, labels[1:]):
        m[a][b] += 1
    return m


def fold_census(
    labels: Sequence[str],
    folds: Sequence[Tuple[str, str, int, int]],
) -> Dict[str, object]:
    """labels: full post-warmup label stream, indexed by snapshot index;
    folds: list of (fold_id, era_id, start_idx, end_idx) inclusive.
    All counts are fold-local (fold ends force-flat by construction)."""
    per_fold = []
    for fold_id, era_id, a, b in folds:
        seg = labels[a : b + 1]
        entry = {
            "fold_id": fold_id,
            "era_id": era_id,
            "sessions": len(seg),
            "first_session_index": a,
            "last_session_index": b,
            "phases": {},
            "transition_matrix": transition_matrix(seg),
            "transitions_total": sum(1 for x, y in zip(seg, seg[1:]) if x != y),
            "unknown": {
                "share": round(sum(1 for x in seg if x == UNKNOWN) / len(seg), 6),
                "longest_run": longest_run(1 if x == UNKNOWN else 0 for x in seg),
            },
        }
        for p in PHASES:
            mask = [1 if x == p else 0 for x in seg]
            runs = episodes(mask)
            entry["phases"][p] = {
                "occupancy_sessions": int(sum(mask)),
                "occupancy_share": round(sum(mask) / len(seg), 6),
                "episode_count_fold_local": len(runs),
                "dwell": dwell_stats(runs),
            }
        per_fold.append(entry)

    # cell-level (post-warmup, fold-local episodes summed; global runs too)
    overall = {}
    for p in PHASES:
        mask = [1 if x == p else 0 for x in labels]
        runs_global = episodes(mask)
        overall[p] = {
            "occupancy_sessions": int(sum(mask)),
            "occupancy_share": round(sum(mask) / len(labels), 6),
            "episode_count_global_runs": len(runs_global),
            "episode_count_sum_of_folds": sum(
                e["phases"][p]["episode_count_fold_local"] for e in per_fold
            ),
            "dwell_global": dwell_stats(runs_global),
        }
    overall_unknown = {
        "share": round(sum(1 for x in labels if x == UNKNOWN) / len(labels), 6),
        "longest_run": longest_run(1 if x == UNKNOWN else 0 for x in labels),
    }
    return {
        "post_warmup_sessions": len(labels),
        "per_fold": per_fold,
        "cell": overall,
        "cell_unknown": overall_unknown,
        "transition_matrix_post_warmup": transition_matrix(labels),
    }


def margin(value: int, floor: int) -> Dict[str, object]:
    return {
        "value": value,
        "floor": floor,
        "margin": value - floor,
        "pass": value >= floor,
    }


def floor_margins(census: Dict[str, object]) -> Dict[str, object]:
    """Immutable floors; every phase reports margin-to-floor, not just pass."""
    out: Dict[str, object] = {"phases": {}}
    for p in NAMED_PHASES:
        cell_eps = census["cell"][p]["episode_count_sum_of_folds"]
        per_fold_eps = {
            e["fold_id"]: e["phases"][p]["episode_count_fold_local"]
            for e in census["per_fold"]
        }
        per_fold_dec = {
            e["fold_id"]: e["phases"][p]["occupancy_sessions"]
            for e in census["per_fold"]
        }
        fold_ok_eps = {k: margin(v, FLOOR_EPISODES_FOLD) for k, v in per_fold_eps.items()}
        fold_ok_dec = {k: margin(v, FLOOR_DECISIONS_FOLD) for k, v in per_fold_dec.items()}
        cell_ok = margin(cell_eps, FLOOR_EPISODES_CELL)
        meets = cell_ok["pass"] and all(v["pass"] for v in fold_ok_eps.values()) and all(
            v["pass"] for v in fold_ok_dec.values()
        )
        out["phases"][p] = {
            "episodes_cell_total": cell_ok,
            "episodes_per_fold": fold_ok_eps,
            "eligible_decisions_per_fold": fold_ok_dec,
            "floors_met": meets,
            "verdict_if_floors_failed": "NOT_RUN_THIN_PHASE" if not meets else None,
        }
    return out
