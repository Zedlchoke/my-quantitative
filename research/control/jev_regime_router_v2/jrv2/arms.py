"""Arms — six frozen arms + buy-hold REFERENCE metric (mapping_arms_freeze).

A ALWAYS_ON_TREND               TREND_LONG always active, regime ignored.
B ALWAYS_ON_MEAN_REVERSION      MR_LONG always active, regime ignored.
C DETERMINISTIC_REGIME_ROUTER   V1 arm-D classifier (EMA12/48 structure,
                                ADX>=22, +-10% trailing-168) + same
                                persistence + mapping. UNCHANGED.
D JEV_ONLY_ROUTER               effective Jev regime -> persistence ->
                                mapping.
E DETERMINISTIC_PLUS_JEV_CONFIRMATION
                                architecturally preferred confirm-law:
                                deterministic law proposes the regime;
                                trade its strategy IFF Jev's persisted
                                effective regime equals the proposal; ANY
                                disagreement -> flat. Jev never selects
                                alone; disagreement never invents a strategy.
F RANDOM_MATCHED_ROUTER         21 seeded segment-permutation null matched
                                to the JEV_ONLY path (occupancy +-2pp /
                                switches +-10% / mean dwell +-10% /
                                invested +-2pp; <=200 resample attempts per
                                seed, else NOT_RUN_CONTROL_MATCHING
                                fail-closed). Q-11 movement checks
                                (>0.02 absolute on lag-1 autocorr AND
                                label->forward-return association).
BUY_HOLD                        reference metric per cell, NOT a scored arm.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import LABELS
from .data import Bars
from .deterministic import deterministic_persisted
from .engine import (
    BUY_HOLD,
    Engine,
    CostModel,
    constant_targets,
    folds_from_regime_ts,
    targets_from_regime,
)
from .metrics import compute_arm_metrics, q11_metrics
from .questionio import Timeline
from .safety import UNKNOWN
from .strategies import FLAT, MR_LONG, TREND_LONG

ARM_NAMES = (
    "ALWAYS_ON_TREND",
    "ALWAYS_ON_MEAN_REVERSION",
    "DETERMINISTIC_REGIME_ROUTER",
    "JEV_ONLY_ROUTER",
    "DETERMINISTIC_PLUS_JEV_CONFIRMATION",
    "RANDOM_MATCHED_ROUTER",
)

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
    cell: str
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


def _buy_hold_reference(ctx: AssetContext) -> dict:
    """Buy-hold REFERENCE metric per cell (fold force-flat law); not scored."""
    res, m = run_buy_hold(ctx)
    return {
        "net_pnl": m["net_pnl"],
        "total_return": m["total_return"],
        "cagr": m["cagr"],
        "sharpe": m["sharpe"],
        "max_drawdown": m["max_drawdown"],
        "note": "reference metric only, never a scored arm",
    }


def run_buy_hold(ctx: AssetContext):
    targets = [None] * len(ctx.exec_bars.ts_close)
    for fid, s, e in ctx.folds_exec:
        for k in range(s, e + 1):
            targets[k] = BUY_HOLD
    eng = Engine(ctx.exec_bars, targets, ctx.folds_exec, ctx.costs, ctx.initial_equity)
    res = eng.run()
    m = compute_arm_metrics(res, ctx.exec_bars, ctx.periods_per_year, ctx.initial_equity)
    return res, m


def run_always_on_trend(ctx: AssetContext):
    targets = constant_targets(len(ctx.exec_bars.ts_close), TREND_LONG)
    eng = Engine(ctx.exec_bars, targets, ctx.folds_exec, ctx.costs, ctx.initial_equity)
    res = eng.run()
    return res, compute_arm_metrics(res, ctx.exec_bars, ctx.periods_per_year, ctx.initial_equity)


def run_always_on_mr(ctx: AssetContext):
    targets = constant_targets(len(ctx.exec_bars.ts_close), MR_LONG)
    eng = Engine(ctx.exec_bars, targets, ctx.folds_exec, ctx.costs, ctx.initial_equity)
    res = eng.run()
    return res, compute_arm_metrics(res, ctx.exec_bars, ctx.periods_per_year, ctx.initial_equity)


def run_deterministic_router(ctx: AssetContext, regime_bars: Bars, persistence_params: dict):
    labels = deterministic_persisted(regime_bars, persistence_params)
    regime_ts = [int(t) for t in regime_bars.ts_close.tolist()]
    targets, res = _route_and_backtest(ctx, regime_ts, labels)
    m = compute_arm_metrics(
        res, ctx.exec_bars, ctx.periods_per_year, ctx.initial_equity, timeline_labels=labels
    )
    return res, m, (regime_ts, labels)


def run_jev_only_router(ctx: AssetContext, timeline: Timeline):
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


def confirmation_labels(
    det_labels: list[str], jev_labels: list[str], mapping: dict
) -> list[str | None]:
    """DETERMINISTIC_PLUS_JEV_CONFIRMATION targets per regime bar.

    deterministic proposes; trade its strategy IFF Jev's persisted effective
    regime equals the proposal; ANY disagreement -> FLAT. Equal UNKNOWN ->
    FLAT (mapping[TRANSITION_UNKNOWN] is FLAT). Returns per-bar target
    strategies over the regime grid (routed through targets_from_regime by
    the caller via a mapping-like dict).
    """
    targets: list[str | None] = []
    for det, jev in zip(det_labels, jev_labels):
        if det == jev:
            targets.append(mapping.get(det, FLAT))
        else:
            targets.append(FLAT)
    return targets


def run_confirmation_arm(
    ctx: AssetContext, regime_bars: Bars, timeline: Timeline, persistence_params: dict
):
    det = deterministic_persisted(regime_bars, persistence_params)
    jev = timeline.persisted
    n = min(len(det), len(jev))
    det, jev = det[len(det) - n :], jev[len(jev) - n :]
    regime_ts = [int(t) for t in regime_bars.ts_close.tolist()][len(regime_bars.ts_close) - n :]
    targets = confirmation_labels(det, jev, ctx.mapping)
    # route: reuse targets_from_regime-free direct target grid over regime ts
    # -> map onto exec bars with the same governing law as targets_from_regime
    exec_targets = _targets_from_regime_target_grid(
        ctx.exec_bars, regime_ts, targets, ctx.regime_period_ns
    )
    eng = Engine(ctx.exec_bars, exec_targets, ctx.folds_exec, ctx.costs, ctx.initial_equity)
    res = eng.run()
    m = compute_arm_metrics(
        res,
        ctx.exec_bars,
        ctx.periods_per_year,
        ctx.initial_equity,
        timeline_labels=jev,
        targets=exec_targets,
        cost_frac_per_side=(ctx.costs.fee_bps + ctx.costs.slip_bps) * 1e-4,
    )
    return res, m, exec_targets, (det, jev)


def _targets_from_regime_target_grid(
    exec_bars: Bars,
    regime_ts: list[int],
    regime_targets: list[str | None],
    regime_period_ns: int,
) -> list[str | None]:
    """Governing law of targets_from_regime applied to a PRE-COMPUTED per-bar
    target grid (same staleness/None semantics)."""
    targets: list[str | None] = [None] * len(exec_bars.ts_close)
    j = -1
    for i, ts_o in enumerate(exec_bars.ts_open.tolist()):
        while j + 1 < len(regime_ts) and regime_ts[j + 1] < ts_o:
            j += 1
        if j < 0:
            continue
        if ts_o - regime_ts[j] > 2 * regime_period_ns:
            targets[i] = FLAT
            continue
        targets[i] = regime_targets[j]
    return targets


# ---- arm F: RANDOM_MATCHED (V1 machinery, adapted keys) --------------------


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


def _marginal_anchored_relabeling(rng) -> list[str]:
    sigma = list(LABELS)
    for _ in range(int(rng.integers(0, 5))):
        i = int(rng.integers(0, len(sigma)))
        j = int(rng.integers(0, len(sigma)))
        sigma[i], sigma[j] = sigma[j], sigma[i]
    return sigma


def _alternating_segment_order(segs: list[tuple[str, int]], rng) -> list[int]:
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


def random_matched_paths(
    e_labels: list[str],
    invested_labels: set[str],
    seeds: list[int] | None = None,
) -> list[dict]:
    """Per-seed matched label paths (rejection-sampled null; V1 machinery).

    Per seed, up to F_MAX_ATTEMPTS: (1) seeded alternating shuffle of E's
    maximal constant-label segments, (2) seeded marginal-anchored relabeling.
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


def run_random_matched(ctx: AssetContext, timeline: Timeline):
    e_labels = timeline.persisted
    e_regime_ts = timeline.ts
    invested = ctx.invested_labels()
    paths = random_matched_paths(e_labels, invested)

    import bisect

    ts_open = ctx.exec_bars.ts_open.tolist()
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
        "q11_jev_only": q11_e,
        "null_invalid_flag": null_invalid,
        "tolerances": F_TOL,
    }
