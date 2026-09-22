"""Arms A-F (frozen definitions; controls are diagnostics, not budget).

A BUY_HOLD          enter TREND_LONG at the first exec bar open of each fold,
                    hold to fold force-flat (hold-to-end modulo fold law);
                    entry+exit costs only.
B ALWAYS_ON_TREND   TREND_LONG always on, regime ignored.
C ALWAYS_ON_MR      MR_LONG always on, regime ignored.
D DETERMINISTIC     trend x vol classifier -> SAME persistence -> mapping.
E JEV               decisions -> persistence -> mapping.
F RANDOM_MATCHED    21 seeded segment-permutations of E's persisted path
                    (segment lengths preserved exactly, labels relabeled by a
                    seeded permutation of label identities over the realized
                    marginal), each matched to E on occupancy +-2pp /
                    switches +-10% / mean dwell +-10% / invested fraction
                    +-2pp; <=200 resample attempts per seed, else
                    NOT_RUN_CONTROL_MATCHING with measured deltas (fail-closed).
                    Q-11: lag-1 label autocorrelation and label->forward-return
                    association must MOVE vs E by >0.02 absolute, else the null
                    is flagged invalid (disclosed, not hidden). Headline seed =
                    net PnL nearest the 21-seed median; all seeds reported.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import LABELS
from .data import Bars
from .decisions import Timeline
from .deterministic import deterministic_persisted
from .engine import (
    BUY_HOLD,
    Engine,
    CostModel,
    constant_targets,
    folds_from_regime_ts,
    targets_from_regime,
)
from .metrics import compute_arm_metrics, margin_to_fail, q11_metrics
from .persistence import persisted_labels, run_persistence
from .strategies import FLAT, MR_LONG, TREND_LONG

F_SEEDS = list(range(20260901, 20260901 + 21))
F_MAX_ATTEMPTS = 200
F_TOL = {
    "occupancy_pp": 0.02,
    "switches_rel": 0.10,
    "mean_dwell_rel": 0.10,
    "invested_pp": 0.02,
}
Q11_MIN_DELTA = 0.02


@dataclass
class AssetContext:
    asset: str
    exec_bars: Bars
    regime_period_ns: int
    mapping: dict  # label -> strategy
    folds_exec: list[tuple[int, int, int]]
    costs: CostModel
    periods_per_year: float
    initial_equity: float = 100_000.0

    def invested_labels(self) -> set[str]:
        return {l for l in LABELS if self.mapping.get(l, FLAT) != FLAT}


def _route_and_backtest(ctx: AssetContext, regime_ts: list[int], labels: list[str]):
    targets = targets_from_regime(
        ctx.exec_bars, regime_ts, labels, ctx.regime_period_ns, ctx.mapping
    )
    eng = Engine(ctx.exec_bars, targets, ctx.folds_exec, ctx.costs, ctx.initial_equity)
    res = eng.run()
    return targets, res


def run_arm_A(ctx: AssetContext):
    targets = [None] * len(ctx.exec_bars.ts_close)
    for fid, s, e in ctx.folds_exec:
        for k in range(s, e + 1):
            targets[k] = BUY_HOLD
    eng = Engine(ctx.exec_bars, targets, ctx.folds_exec, ctx.costs, ctx.initial_equity)
    res = eng.run()
    m = compute_arm_metrics(res, ctx.exec_bars, ctx.periods_per_year, ctx.initial_equity)
    return res, m


def run_arm_B(ctx: AssetContext):
    targets = constant_targets(len(ctx.exec_bars.ts_close), TREND_LONG)
    eng = Engine(ctx.exec_bars, targets, ctx.folds_exec, ctx.costs, ctx.initial_equity)
    res = eng.run()
    return res, compute_arm_metrics(res, ctx.exec_bars, ctx.periods_per_year, ctx.initial_equity)


def run_arm_C(ctx: AssetContext):
    targets = constant_targets(len(ctx.exec_bars.ts_close), MR_LONG)
    eng = Engine(ctx.exec_bars, targets, ctx.folds_exec, ctx.costs, ctx.initial_equity)
    res = eng.run()
    return res, compute_arm_metrics(res, ctx.exec_bars, ctx.periods_per_year, ctx.initial_equity)


def run_arm_D(ctx: AssetContext, regime_bars: Bars, persistence_params: dict):
    labels = deterministic_persisted(regime_bars, persistence_params)
    regime_ts = [int(t) for t in regime_bars.ts_close.tolist()]
    targets, res = _route_and_backtest(ctx, regime_ts, labels)
    m = compute_arm_metrics(
        res, ctx.exec_bars, ctx.periods_per_year, ctx.initial_equity, timeline_labels=labels
    )
    return res, m, (regime_ts, labels)


def run_arm_E(ctx: AssetContext, timeline: Timeline):
    regime_ts = timeline.ts
    labels = timeline.persisted
    targets, res = _route_and_backtest(ctx, regime_ts, labels)
    m = compute_arm_metrics(
        res,
        ctx.exec_bars,
        ctx.periods_per_year,
        ctx.initial_equity,
        timeline_labels=labels,
        targets=targets,
        cost_frac_per_side=(ctx.costs.fee_bps + ctx.costs.slip_bps) * 1e-4,
    )
    return res, m, targets


# ---- arm F -----------------------------------------------------------------


def _segments(labels: list[str]) -> list[tuple[str, int]]:
    segs = []
    cur = labels[0]
    n = 1
    for l in labels[1:]:
        if l == cur:
            n += 1
        else:
            segs.append((cur, n))
            cur = l
            n = 1
    segs.append((cur, n))
    return segs


def _match(ok_path: list[str], e_labels: list[str], invested_labels: set[str]) -> tuple[bool, dict]:
    e_occ = {l: e_labels.count(l) / len(e_labels) for l in LABELS}
    f_occ = {l: ok_path.count(l) / len(ok_path) for l in LABELS}
    occ_dev = max(abs(e_occ[l] - f_occ[l]) for l in LABELS)
    e_sw = sum(1 for i in range(1, len(e_labels)) if e_labels[i] != e_labels[i - 1])
    f_sw = sum(1 for i in range(1, len(ok_path)) if ok_path[i] != ok_path[i - 1])
    sw_rel = abs(f_sw - e_sw) / max(e_sw, 1)
    e_dw = len(e_labels) / max(e_sw, 1)
    f_dw = len(ok_path) / max(f_sw, 1)
    dw_rel = abs(f_dw - e_dw) / max(e_dw, 1e-9)
    e_inv = sum(1 for l in e_labels if l in invested_labels) / len(e_labels)
    f_inv = sum(1 for l in ok_path if l in invested_labels) / len(ok_path)
    inv_dev = abs(e_inv - f_inv)
    deltas = {
        "occupancy_max_dev_pp": occ_dev,
        "switches_rel_dev": sw_rel,
        "mean_dwell_rel_dev": dw_rel,
        "invested_frac_dev_pp": inv_dev,
    }
    ok = (
        occ_dev <= F_TOL["occupancy_pp"]
        and sw_rel <= F_TOL["switches_rel"]
        and dw_rel <= F_TOL["mean_dwell_rel"]
        and inv_dev <= F_TOL["invested_pp"]
    )
    return ok, deltas


class ControlMatchingFailed(RuntimeError):
    """NOT_RUN_CONTROL_MATCHING: a seed could not be matched (fail-closed)."""

    def __init__(self, payload: dict) -> None:
        super().__init__("NOT_RUN_CONTROL_MATCHING")
        self.payload = payload


def arm_F_paths(
    e_labels: list[str],
    invested_labels: set[str],
    seeds: list[int] | None = None,
) -> list[dict]:
    """Per-seed matched label paths (rejection-sampled null).

    Per seed, up to F_MAX_ATTEMPTS times:
    (1) shuffle the ORDER of E's maximal constant-label segments with a
        seeded greedy alternation constraint (a segment is only placed next
        to a different-label segment when one is still available; otherwise
        a merge is allowed and the tolerance check will judge it),
    (2) relabel by a seeded random permutation of label identities (the
        realized marginal is E's own occupancy, which a bijective relabeling
        preserves up to the tolerance check).
    Accept the first candidate matching E within the frozen tolerances;
    otherwise fail closed (NOT_RUN_CONTROL_MATCHING).
    """
    seeds = seeds or F_SEEDS
    segs = _segments(e_labels)
    out = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        accepted = None
        last_deltas = None
        for _ in range(F_MAX_ATTEMPTS):
            order = _alternating_segment_order(segs, rng)
            sigma = _marginal_anchored_relabeling(rng)
            path: list[str] = []
            for k in order:
                path.extend([str(sigma[LABELS.index(segs[k][0])])] * segs[k][1])
            ok, deltas = _match(path, e_labels, invested_labels)
            last_deltas = deltas
            if ok:
                accepted = path
                break
        if accepted is None:
            raise ControlMatchingFailed(
                {
                    "seed": seed,
                    "attempts": F_MAX_ATTEMPTS,
                    "measured_deltas": last_deltas,
                    "tolerances": F_TOL,
                }
            )
        out.append({"seed": seed, "labels": accepted, "deltas": last_deltas})
    return out


def _marginal_anchored_relabeling(rng) -> list[str]:
    """Draw a relabeling anchored at the identity: 0..4 seeded transpositions.

    The realized marginal constrains which relabelings are admissible
    (concentrated paths only tolerate near-identity relabelings); rejection
    sampling over these draws plus the order shuffle yields the matched null.
    """
    sigma = list(LABELS)
    for _ in range(int(rng.integers(0, 5))):
        i = int(rng.integers(0, len(sigma)))
        j = int(rng.integers(0, len(sigma)))
        sigma[i], sigma[j] = sigma[j], sigma[i]
    return sigma


def _alternating_segment_order(segs: list[tuple[str, int]], rng) -> list[int]:
    """Seeded shuffle of segment indices avoiding adjacent same-label
    placement whenever a different-label segment remains available."""
    remaining = list(range(len(segs)))
    order: list[int] = []
    last_label: str | None = None
    while remaining:
        cands = [k for k in remaining if segs[k][0] != last_label]
        pool = cands if cands else remaining
        pick = pool[int(rng.integers(0, len(pool)))]
        order.append(pick)
        remaining.remove(pick)
        last_label = segs[pick][0]
    return order


def run_arm_F(ctx: AssetContext, timeline: Timeline, regime_bars_len_hint=None):
    e_labels = timeline.persisted
    e_regime_ts = timeline.ts
    invested = ctx.invested_labels()
    paths = arm_F_paths(e_labels, invested)

    # exec index of each regime decision (for Q-11 forward returns)
    ts_open = ctx.exec_bars.ts_open.tolist()
    import bisect

    exec_idx = [bisect.bisect_right(ts_open, t) for t in e_regime_ts]
    q11_e = q11_metrics(e_labels, dict(zip(LABELS, range(1, 6))), ctx.exec_bars, exec_idx)

    seed_rows = []
    null_invalid = False
    for entry in paths:
        targets, res = _route_and_backtest(ctx, e_regime_ts, entry["labels"])
        m = compute_arm_metrics(
            res, ctx.exec_bars, ctx.periods_per_year, ctx.initial_equity,
            timeline_labels=entry["labels"],
            targets=targets,
            cost_frac_per_side=(ctx.costs.fee_bps + ctx.costs.slip_bps) * 1e-4,
        )
        q11_f = q11_metrics(
            entry["labels"], dict(zip(LABELS, range(1, 6))), ctx.exec_bars, exec_idx
        )
        moved = (
            abs(q11_f["lag1_autocorr"] - q11_e["lag1_autocorr"]) > Q11_MIN_DELTA
            and abs(q11_f["label_forward_assoc"] - q11_e["label_forward_assoc"]) > Q11_MIN_DELTA
        )
        if not moved:
            null_invalid = True
        seed_rows.append(
            {
                "seed": entry["seed"],
                "net_pnl": m["net_pnl"],
                "metrics": m,
                "q11": q11_f,
                "q11_moved": moved,
                "deltas": entry["deltas"],
            }
        )

    nets = [r["net_pnl"] for r in seed_rows]
    med = float(np.median(nets))
    headline = min(seed_rows, key=lambda r: abs(r["net_pnl"] - med))
    return {
        "seeds": seed_rows,
        "headline_seed": headline["seed"],
        "median_net_pnl": med,
        "q11_arm_E": q11_e,
        "null_invalid_flag": null_invalid,
        "tolerances": F_TOL,
    }
