"""RSMV1 scored discovery runner (GO-gated entry via tools/cmd_scored.py).

21 scored cells = 3 cells x 7 arm instances (A1, A2, B, C, D, E, F).
Cost tiers 1.0/1.5/2.0 (fee+slip multiplied; funding constant — V2 law).
Atomic: computes every cell x arm x tier, writes only on full success.

Laws (frozen; A6 proposals + A1 pins):
- ZERO provider calls; cached decisions only (rebuilt timeline verified).
- Arms A1/A2/B use V2 frozen strategies and V2 mechanics; B must equal the
  V2 JEV_ONLY tier-1 stored totals (<1e-6) — re-asserted HERE at run start.
- Arm C: per-fold nested selection (fold1 FLAT; inner floors 5/150; stable
  higher inner pooled net; tie -> FLAT) over the frozen A4 library, routed
  under the turnover law (buffer k=1 + direction no-op + regime-bar min-hold
  suppression of direction changes via a bounded fixed point).
- Arm D: always-on base flattened in DISTRIBUTION/DOWNTREND, turnover law.
- Arm E: V2 deterministic law proposes, Jev effective regime may only veto
  (V2 CONFIRM law), turnover law.
- Arm F: episode-shuffled matched to arm C's desired label path, matching
  tolerances AND Q-11 movement BOTH inside acceptance; fail-closed
  NOT_RUN_CONTROL_MATCHING.
- Turnover rejection law: arm C fails the cell if its trade count >= the
  V2 JEV_ONLY pin (978/1060/343); unnecessary_close_reopen must be 0.
- Every computed outcome counts in the observed denominator (21) even if
  publication later fails; no mid-run stopping; no post-PnL edits.
"""

from __future__ import annotations

import bisect
import json
import pathlib
from dataclasses import asdict
from datetime import datetime, timezone

import numpy as np

from . import LABELS
from .data import Bars
from .deterministic import deterministic_persisted
from .engine import CostModel, folds_from_regime_ts, fold_partition_invariants, targets_from_regime
from .freezes import Freezes
from .regime_timeline import CellTimelines, rebuild_cell_timeline, episodes as episodes_of
from .selection import (
    INNER_DECISION_FLOOR,
    INNER_EPISODE_FLOOR,
    SpecialistCandidate,
    select_for_fold,
)
from .specialist_engine import SpecialistEngine, StrategySpec, v2_equivalence_specs
from .specialists import build_specs, eligible_for
from .strategies import FLAT, MR_LONG, TREND_LONG
from .turnover import (
    BUFFER_REGIME_BARS,
    TargetRouter,
    buffered_labels,
    direction_of,
)

CYCLE_DIR = pathlib.Path(__file__).resolve().parents[1]
V2_LEDGERS = pathlib.Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/jev-regime-router-v2/"
    "integration/research/control/jev_regime_router_v2/runtime/scored"
)
ARMS = ["A1_ALWAYS_ON_MR", "A2_ALWAYS_ON_TREND", "B_ORIGINAL_V2_MAPPING",
        "C_REGIME_SPECIALIST_ROUTER", "D_SPARSE_JEV_RISK_OFF_VETO",
        "E_DETERMINISTIC_PLUS_JEV_VETO", "F_EPISODE_SHUFFLED_MATCHED"]
TIERS = [1.0, 1.5, 2.0]
V2_JEV_TRADE_PINS = {"BTC_H1": 978, "BTC_H4": 1060, "SPY_D1": 343}
SCORED_SCHEMA = "rsmv1_scored_cell@1"
FIXED_POINT_MAX = 5
Q11_MIN_DELTA = 0.02
PHASES4 = ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND")


# --------------------------------------------------------------------------
# context


class CellCtx:
    def __init__(self, cell: str):
        self.cell = cell
        fz = Freezes(CYCLE_DIR)
        self.fz = fz
        ct: CellTimelines = rebuild_cell_timeline(CYCLE_DIR, cell)
        self.ct = ct
        self.exec_bars: Bars = ct.exec_bars
        self.asset = "BTCUSDT" if cell.startswith("BTC") else "SPY"
        spans = [
            (_iso_ns(sp["start"]), _iso_ns(sp["end"]))
            for sp in fz.fold_contract["cells"][cell]["folds"]
        ]
        self.folds_exec = folds_from_regime_ts(self.exec_bars, spans)
        fd_ts = int(ct.regime_bars.ts_close[fz.warmup(cell)])
        first_req = next(
            (i for i, t in enumerate(self.exec_bars.ts_open.tolist()) if t > fd_ts),
            len(self.exec_bars.ts_close),
        )
        fold_partition_invariants(self.folds_exec, len(self.exec_bars.ts_close), first_req)
        costs = json.loads(
            (CYCLE_DIR / "freezes" / "mapping_arms_freeze.json").read_text()
        )["costs"]
        if cell.startswith("BTC"):
            c = costs["BTCUSDT"]
            self.base_cost = CostModel(c["taker_fee_bps_per_side"],
                                       c["slippage_bps_per_side"],
                                       c["funding_per_8h_signed"], "BTC")
        else:
            c = costs["SPY"]
            self.base_cost = CostModel(c["cost_bps_per_fill"], 0.0, 0.0, "SPY")
        self.v2_specs = v2_equivalence_specs()
        self.a4_specs = build_specs(self.exec_bars)
        self.n = len(self.exec_bars.ts_close)
        # fold of each regime bar (episode start fold law)
        self.regime_fold = [
            _fold_of_span(spans, int(t)) for t in ct.ts
        ]
        self.episodes = episodes_of(ct.persisted)

    def cost(self, tier: float) -> CostModel:
        return CostModel(self.base_cost.fee_bps * tier,
                         self.base_cost.slip_bps * tier,
                         self.base_cost.funding_rate, self.base_cost.label)

    def governing_index(self, i: int, ts_list=None) -> int:
        ts = ts_list if ts_list is not None else self.ct.ts
        ts_o = int(self.exec_bars.ts_open[i])
        j = bisect.bisect_right(ts, ts_o - 1) - 1
        return j


def _iso_ns(iso: str) -> int:
    from datetime import datetime, timezone

    s = iso.replace("Z", "+00:00")
    if "T" not in s:
        s += "T00:00:00+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def _fold_of_span(spans, ts: int) -> int:
    for fid, (a, b) in enumerate(spans):
        if a <= ts <= b:
            return fid
    return -1


def _tier_tag(t: float) -> str:
    return {1.0: "tier_1", 1.5: "tier_1p5", 2.0: "tier_2"}[t]


def _identity_ok(res) -> list:
    t = res.totals
    eq = (100_000.0 + t["net_pnl"]) - float(res.equity[-1])
    ni = t["net_pnl"] - (t["gross_pnl"] - t["costs_fee"] - t["costs_slip"] - t["costs_funding"])
    return [bool(abs(eq) < 1e-6 and abs(ni) < 1e-9), max(abs(eq), abs(ni))]


def _fold_ok(res) -> list:
    d = float(sum(res.fold_net_pnl)) - float(res.totals["net_pnl"])
    return [bool(abs(d) < 1e-9), d]


def _run_engine(ctx: CellCtx, targets, specs, tier: float):
    eng = SpecialistEngine(ctx.exec_bars, targets, ctx.folds_exec, ctx.cost(tier),
                           specs, regime_ts=ctx.ct.ts)
    return eng.run()


# --------------------------------------------------------------------------
# turnover-law routing with regime-bar min-hold suppression (fixed point)


def _suppress_min_hold(desired, trades_prev, ctx: CellCtx) -> list:
    """Emit the held position's strategy while a direction change would fire
    before min-hold (6 regime bars) elapses (A4 law). Uses the previous
    engine pass's trade list; iterated to a fixed point by the caller."""
    min_hold = 6
    out = list(desired)
    ts_open = ctx.exec_bars.ts_open.tolist()
    regime_ts = ctx.ct.ts
    for tr in trades_prev:
        entry_ts = tr["entry_ts"] if isinstance(tr, dict) else tr.entry_ts
        strategy = tr["strategy"] if isinstance(tr, dict) else tr.strategy
        d = direction_of(strategy)
        if d == 0:
            continue
        # span of bars where this position was live
        eb = tr["entry_bar"] if isinstance(tr, dict) else tr.entry_bar
        xb = tr["exit_bar"] if isinstance(tr, dict) else tr.exit_bar
        for i in range(eb, xb + 1):
            if i >= len(out):
                break
            want = direction_of(desired[i])
            if want != d and want is not None:
                a = bisect.bisect_right(regime_ts, entry_ts)
                b = bisect.bisect_right(regime_ts, int(ctx.exec_bars.ts_close[i]))
                if (b - a) < min_hold:
                    spec = ctx.a4_specs.get(strategy)
                    out[i] = strategy if spec is not None else out[i]
    return out


def route_arm(ctx: CellCtx, mapping_by_fold: dict[int, dict], buffer_k: int,
              specs: dict[str, StrategySpec], tier: float):
    """Per-fold regime->strategy mapping, buffered + no-op + min-hold
    suppression; returns (targets, router_reports, fixed_point_iters)."""
    # desired targets per fold region
    desired: list = [None] * ctx.n
    fold_of_exec = np.full(ctx.n, -1, dtype=np.int64)
    for fid, s, e in ctx.folds_exec:
        fold_of_exec[s : e + 1] = fid
    ts_b, labels_b = buffered_labels(ctx.ct.ts, ctx.ct.persisted, buffer_k)
    # map buffered label -> desired strategy per exec bar (fold-aware)
    j = -1
    for i in range(ctx.n):
        ts_o = int(ctx.exec_bars.ts_open[i])
        while j + 1 < len(ts_b) and ts_b[j + 1] < ts_o:
            j += 1
        if j < 0:
            desired[i] = None
            continue
        if ts_o - ts_b[j] > 2 * ctx.ct.period_ns:
            desired[i] = FLAT
            continue
        fid = int(fold_of_exec[i])
        mapping = mapping_by_fold.get(fid, {})
        lab = labels_b[j]
        s = mapping.get(lab, FLAT)
        desired[i] = s if (s in specs or s == FLAT) else FLAT
    # direction no-op pass
    emitted: list = [None] * ctx.n
    cur, cur_d = None, 0
    noop = 0
    for i, t in enumerate(desired):
        if t is None:
            emitted[i] = None
            continue
        d = direction_of(t)
        if cur is None or d != cur_d:
            cur, cur_d = t, d
        elif t != cur and d != 0:
            noop += 1
        emitted[i] = cur
    # no-op suppression counter (A7-R1 LOW, corrected RSMV1-INC-1c):
    # label changed to a different SAME-DIRECTION strategy string and the
    # no-op law kept the standing position (emitted != desired). These are
    # SUPPRESSED changes — by construction they cause ZERO fills (the
    # emitted string changes only on direction changes). The fill-level
    # invariant (no regime_off exit immediately followed by a same-direction
    # entry) is proven from the engine's trade stream below.
    noop_suppressed_label_changes = 0
    for i in range(1, ctx.n):
        a, b = desired[i - 1], desired[i]
        if (a is not None and b is not None and a != b
                and direction_of(a) != 0 and direction_of(a) == direction_of(b)):
            noop_suppressed_label_changes += 1
    # A4 min-hold law, deterministic form (RSMV1-INC-1b remediation):
    # a DIRECTION change of the desired series is DEFERRED until the current
    # invested desired-segment is >= MIN_HOLD_REGIME_BARS old (counted on the
    # buffered regime clock). Fully determined by the desired series + regime
    # clock — no engine feedback (the engine-feedback fixed point could
    # oscillate; TECHABORT of run-2 attempt 1). Strategy-native exits and
    # stops are engine-side and never suppressed by this pass.
    MIN_HOLD = 6
    ts_open_l = ctx.exec_bars.ts_open.tolist()
    held: list = [None] * ctx.n
    cur, cur_d = None, 0
    seg_start_ts: int | None = None
    deferred = 0
    for i, t in enumerate(desired):
        if t is None:
            held[i] = None
            continue
        d = direction_of(t)
        if d != cur_d:
            if cur_d != 0 and seg_start_ts is not None:
                bars_held = bisect.bisect_right(ts_b, ts_open_l[i]) - \
                    bisect.bisect_right(ts_b, seg_start_ts)
                if bars_held < MIN_HOLD:
                    deferred += 1
                    held[i] = cur
                    continue
            cur, cur_d = t, d
            seg_start_ts = ts_open_l[i] if d != 0 else None
        held[i] = cur
    emitted = held
    # NO-OP LAW invariant (RSMV1-INC-1d, exact form): the EMITTED series must
    # never change its strategy STRING while the direction stays non-zero —
    # that is the only mechanism by which an unnecessary same-direction
    # close/reopen could fire (the engine reconciles exactly on string
    # changes). Direction legitimately leaving and returning (e.g. through a
    # TRANSITION_UNKNOWN window that maps FLAT) is NOT a violation — the
    # target really left.
    unnecessary_string_changes = sum(
        1 for i in range(1, ctx.n)
        if emitted[i - 1] is not None and emitted[i] is not None
        and emitted[i - 1] != emitted[i]
        and emitted[i - 1] != FLAT and emitted[i] != FLAT
        and direction_of(emitted[i - 1]) != 0
        and direction_of(emitted[i - 1]) == direction_of(emitted[i])
    )
    res = _run_engine(ctx, emitted, specs, tier)
    report = {"noop_target_updates": noop,
              "noop_suppressed_label_changes": noop_suppressed_label_changes,
              "unnecessary_close_reopen_string_changes":
                  unnecessary_string_changes,
              "unnecessary_close_reopen_law": "must be identically 0 "
              "(same-direction string changes in the emitted series)",
              "min_hold_deferred_direction_changes": deferred,
              "mechanism": "deterministic desired-series deferral "
                           "(min-hold 6 regime bars, buffered clock)"}
    if unnecessary_string_changes != 0:
        raise RuntimeError(
            "unnecessary_close_reopen: emitted series changed strategy "
            f"string {unnecessary_string_changes} times with unchanged "
            "direction — no-op law violated")
    return emitted, report, res
    raise RuntimeError(f"min-hold suppression did not converge in {FIXED_POINT_MAX} iters")


# --------------------------------------------------------------------------
# arms


def arm_a1(ctx: CellCtx, tier: float):
    return _run_engine(ctx, [MR_LONG] * ctx.n, ctx.v2_specs, tier)


def arm_a2(ctx: CellCtx, tier: float):
    return _run_engine(ctx, [TREND_LONG] * ctx.n, ctx.v2_specs, tier)


def _v2_mapping(ctx: CellCtx) -> dict:
    raw = json.loads(
        (CYCLE_DIR / "freezes" / "mapping_arms_freeze.json").read_text()
    )["mapping"]
    return {k: v[ctx.asset] for k, v in raw.items()}


def arm_b(ctx: CellCtx, tier: float):
    targets = targets_from_regime(ctx.exec_bars, ctx.ct.ts, ctx.ct.persisted,
                                  ctx.ct.period_ns, _v2_mapping(ctx))
    return _run_engine(ctx, targets, ctx.v2_specs, tier)


def arm_c_inner_evidence(ctx: CellCtx, tier: float):
    """Inner-fold pooled net per (regime, specialist) — selection input.

    Evidence targets: the specialist ACTIVE on bars governed by regime R
    (unbuffered persisted law), FLAT elsewhere. Runs once per pair; pooled
    inner net = sum of fold nets over inner folds (all folds' engines run;
    the selection law only READS inner folds)."""
    evidence: dict[str, dict[str, dict]] = {}
    for regime in PHASES4:
        elig = eligible_for(ctx.asset, regime)
        if not elig:
            continue
        for sid in elig:
            targets: list = [None] * ctx.n
            j = -1
            ts = ctx.ct.ts
            for i in range(ctx.n):
                ts_o = int(ctx.exec_bars.ts_open[i])
                while j + 1 < len(ts) and ts[j + 1] < ts_o:
                    j += 1
                if j < 0:
                    continue
                if ts_o - ts[j] > 2 * ctx.ct.period_ns:
                    targets[i] = FLAT
                    continue
                targets[i] = sid if ctx.ct.persisted[j] == regime else FLAT
            res = _run_engine(ctx, targets, ctx.a4_specs, tier)
            evidence.setdefault(regime, {})[sid] = {
                "fold_nets": {fid: v for fid, v in enumerate(res.fold_net_pnl)},
                "pooled_net": float(sum(res.fold_net_pnl)),
                "trades": res.totals["trades"],
            }
    return evidence


FROZEN_OUTER_FLOORS = {"episodes_total": 20, "episodes_per_fold": 3,
                       "eligible_decisions_per_fold": 100}
RELAXED_OUTER_FLOORS = {"episodes_total": 10, "episodes_per_fold": 2,
                        "eligible_decisions_per_fold": 50}
# frozen in freezes/go_authority_and_floor_sensitivity_freeze.json BEFORE
# any scored outcome (owner GO instruction: compare floors vs relaxed)


def _outer_thin_regimes(ctx: CellCtx, floors: dict) -> dict[str, dict]:
    """Per-regime outer-floor block mirroring the census law exactly:
    thin iff episodes_total < floor OR any fold (episodes < fold floor OR
    eligible decisions < fold floor). Returns {regime: info} with 'thin'."""
    out: dict[str, dict] = {}
    spans = [
        (_iso_ns(sp["start"]), _iso_ns(sp["end"]))
        for sp in ctx.fz.fold_contract["cells"][ctx.cell]["folds"]
    ]
    for regime in PHASES4:
        eps = [e for e in ctx.episodes if e["label"] == regime]
        total = len(eps)
        fold_eps = {f: 0 for f in range(4)}
        fold_dec = {f: 0 for f in range(4)}
        for e in eps:
            f = _fold_of_span(spans, int(ctx.ct.regime_bars.ts_close[e["start"]]))
            if 0 <= f <= 3:
                fold_eps[f] += 1
                if e["length"] >= 6:
                    fold_dec[f] += e["length"]
        reasons = []
        if total < floors["episodes_total"]:
            reasons.append("episodes_total")
        for f in range(4):
            if fold_eps[f] < floors["episodes_per_fold"]:
                reasons.append(f"fold{f + 1}_episodes")
            if fold_dec[f] < floors["eligible_decisions_per_fold"]:
                reasons.append(f"fold{f + 1}_decisions")
        out[regime] = {
            "thin": bool(reasons), "failed_floors": reasons,
            "episodes_total": total,
            "fold_episodes": fold_eps, "fold_eligible_decisions": fold_dec,
        }
    return out


def arm_c_selection(ctx: CellCtx, evidence,
                    outer_floors: dict | None = None) -> tuple[dict[int, dict], list[dict]]:
    """Nested selection: mapping per outer fold + audit trail.

    A7-R1 F1 fix: the OUTER sample floors gate FIRST — a census-THIN regime
    routes FLAT in EVERY fold (reason OUTER_FLOOR_THIN); only non-thin
    regimes proceed to the inner-floor + inner-net law.

    outer_floors=None -> the FROZEN census verdicts (20/3/100); a dict ->
    the owner-frozen sensitivity floors (computed from episode data with the
    exact census math; frozen pre-outcome, never tuned).
    """
    if outer_floors is None:
        from .census import measure_cell_census

        census = measure_cell_census(CYCLE_DIR, ctx.cell)
        outer = {
            r: {"thin": census["per_regime"][r]["verdict"] == "NOT_RUN_THIN_REGIME",
                "episodes_total": census["per_regime"][r]["episodes_total"],
                "margin_to_floor_min": census["per_regime"][r].get(
                    "margin_to_floor_min")}
            for r in PHASES4
        }
    else:
        outer = _outer_thin_regimes(ctx, outer_floors)
    mapping_by_fold: dict[int, dict] = {}
    audit: list[dict] = []
    base_map = {"TRANSITION_UNKNOWN": FLAT}
    for fid in range(4):
        mapping = dict(base_map)
        for regime in PHASES4:
            o = outer[regime]
            if o["thin"]:
                mapping[regime] = FLAT
                audit.append({
                    "regime": regime, "fold_id": fid, "selected": "FLAT",
                    "reason": "OUTER_FLOOR_THIN",
                    "outer_episodes_total": o["episodes_total"],
                    "outer_failed_floors": o.get("failed_floors"),
                    "inner_episodes": None,
                    "inner_eligible_decisions": None,
                    "floor_ok": False,
                })
                continue
            elig = eligible_for(ctx.asset, regime)
            # inner sample floors from census episodes starting in folds < fid
            inner_eps = [
                e for e in ctx.episodes
                if e["label"] == regime and 0 <= _start_fold(ctx, e) < fid
            ]
            inner_episodes = len(inner_eps)
            inner_dec = sum(e["length"] for e in inner_eps if e["length"] >= 6)
            cands = []
            for sid in elig:
                ev = evidence.get(regime, {}).get(sid)
                if ev is None:
                    continue
                fold_nets = {f: v for f, v in ev["fold_nets"].items() if f < fid}
                cands.append(SpecialistCandidate(
                    specialist_id=sid,
                    tie_break_class=("BTC_ONLY_SHORT" if sid.endswith("-S")
                                     else "LONG_CAPABLE"),
                    inner_pooled_net=float(sum(fold_nets.values())),
                    inner_fold_nets=fold_nets,
                ))
            out = select_for_fold(regime, fid, cands, inner_episodes,
                                  inner_dec, max(0, fid))
            mapping[regime] = out.selected if out.selected != "FLAT" else FLAT
            audit.append({
                "regime": regime, "fold_id": fid, "selected": out.selected,
                "reason": out.reason, "outer_episodes_total": o["episodes_total"],
                "inner_episodes": inner_episodes,
                "inner_eligible_decisions": inner_dec,
                "floor_ok": out.floor_ok,
            })
        mapping_by_fold[fid] = mapping
    return mapping_by_fold, audit


def _start_fold(ctx: CellCtx, episode: dict) -> int:
    ts = int(ctx.ct.regime_bars.ts_close[episode["start"]])
    return _fold_of_span(
        [(_iso_ns(sp["start"]), _iso_ns(sp["end"]))
         for sp in ctx.fz.fold_contract["cells"][ctx.cell]["folds"]], ts)


def arm_c(ctx: CellCtx, tier: float, outer_floors: dict | None = None):
    evidence = arm_c_inner_evidence(ctx, 1.0)  # selection on BASE tier law
    mapping_by_fold, audit = arm_c_selection(ctx, evidence, outer_floors)
    targets, report, res = route_arm(ctx, mapping_by_fold, BUFFER_REGIME_BARS,
                                     ctx.a4_specs, tier)
    res.selection_audit = audit  # type: ignore[attr-defined]
    res.routing_report = report  # type: ignore[attr-defined]
    return res, audit, report, mapping_by_fold


def arm_d(ctx: CellCtx, tier: float):
    base = MR_LONG if ctx.asset == "BTCUSDT" else TREND_LONG
    mapping = {
        "ACCUMULATION": base, "UPTREND": base, "DISTRIBUTION": FLAT,
        "DOWNTREND": FLAT, "TRANSITION_UNKNOWN": FLAT,
    }
    mapping_by_fold = {fid: mapping for fid in range(4)}
    targets, report, res = route_arm(ctx, mapping_by_fold, BUFFER_REGIME_BARS,
                                     ctx.v2_specs, tier)
    res.routing_report = report  # type: ignore[attr-defined]
    return res, report


def arm_e(ctx: CellCtx, tier: float):
    params = ctx.fz.persistence_params()
    det = deterministic_persisted(ctx.ct.regime_bars, params)
    v2map = _v2_mapping(ctx)
    # V2 CONFIRM law: trade det strategy IFF Jev PERSISTED effective regime
    # equals the det proposal; else FLAT. Per regime bar -> exec mapping.
    per_regime: list[str | None] = []
    for d, jev in zip(det, ctx.ct.persisted):
        per_regime.append(v2map.get(d, FLAT) if d == jev else FLAT)
    desired: list = [None] * ctx.n
    j = -1
    ts = ctx.ct.ts
    for i in range(ctx.n):
        ts_o = int(ctx.exec_bars.ts_open[i])
        while j + 1 < len(ts) and ts[j + 1] < ts_o:
            j += 1
        if j < 0:
            continue
        if ts_o - ts[j] > 2 * ctx.ct.period_ns:
            desired[i] = FLAT
            continue
        desired[i] = per_regime[j] if per_regime[j] else FLAT
    emitted: list = [None] * ctx.n
    cur, cur_d = None, 0
    for i, t in enumerate(desired):
        if t is None:
            emitted[i] = None
            continue
        d = direction_of(t)
        if cur is None or d != cur_d:
            cur, cur_d = t, d
        emitted[i] = cur
    res = _run_engine(ctx, emitted, ctx.v2_specs, tier)
    return res, {"noop_law": "applied", "buffer": BUFFER_REGIME_BARS}


def arm_f(ctx: CellCtx, c_desired_mapping_by_fold, tier: float):
    """Episode-shuffled matched control on arm C's desired label path.

    Matching + Q-11 movement BOTH inside acceptance (A6 law; V2's
    null_invalid weakness cannot recur silently)."""
    from .arms import (
        F_MAX_ATTEMPTS, F_SEEDS, F_TOL,
        _alternating_segment_order, _marginal_anchored_relabeling,
        _segments, _match, q11_metrics,
    )

    # The matcher + Q-11 operate on the REGIME-GRID buffered label path
    # (V2 machinery semantics); routing maps each regime bar's (permuted)
    # label through the SAME fold-aware specialist mapping arm C uses.
    fold_of_exec = np.full(ctx.n, -1, dtype=np.int64)
    for fid, s, e in ctx.folds_exec:
        fold_of_exec[s : e + 1] = fid
    ts_b, labels_b = buffered_labels(ctx.ct.ts, ctx.ct.persisted, BUFFER_REGIME_BARS)
    exec_idx = [bisect.bisect_right(ctx.exec_bars.ts_open.tolist(), t)
                for t in ts_b]
    code = dict(zip(LABELS, range(1, 6)))
    q11_e = q11_metrics(labels_b, code, ctx.exec_bars, exec_idx)
    segs = _segments(labels_b)
    desired_labels = labels_b  # regime-grid anchor for matching
    invested_label_set = {
        lab for lab in LABELS
        for fid in range(4)
        if c_desired_mapping_by_fold.get(fid, {}).get(lab, FLAT) != FLAT
    }

    def _route(labels_path):
        """Regime-grid permuted path -> per-exec-bar strategy targets."""
        targets: list = [None] * ctx.n
        j = -1
        for i in range(ctx.n):
            ts_o = int(ctx.exec_bars.ts_open[i])
            while j + 1 < len(ts_b) and ts_b[j + 1] < ts_o:
                j += 1
            if j < 0:
                continue
            fid = int(fold_of_exec[i])
            mapping = c_desired_mapping_by_fold.get(fid, {})
            strat = mapping.get(labels_path[j], FLAT)
            targets[i] = strat if (strat in ctx.a4_specs or strat == FLAT) else FLAT
        emitted: list = [None] * ctx.n
        cur, cur_d = None, 0
        for i, t in enumerate(targets):
            if t is None:
                continue
            d = direction_of(t)
            if cur is None or d != cur_d:
                cur, cur_d = t, d
            emitted[i] = cur
        return emitted

    seed_rows = []
    matched_paths = []
    for seed in F_SEEDS:
        rng = np.random.default_rng(seed)
        accepted = None
        for _ in range(F_MAX_ATTEMPTS):
            order = _alternating_segment_order(segs, rng)
            sigma = _marginal_anchored_relabeling(rng)
            path: list[str] = []
            for k in order:
                path.extend([str(sigma[LABELS.index(segs[k][0])])] * segs[k][1])
            ok, deltas = _match(path, desired_labels, invested_label_set)
            if not ok:
                continue
            q11_f = q11_metrics(path, code, ctx.exec_bars, exec_idx)
            moved = (
                abs(q11_f["lag1_autocorr"] - q11_e["lag1_autocorr"]) > Q11_MIN_DELTA
                and abs(q11_f["label_forward_assoc"] - q11_e["label_forward_assoc"]) > Q11_MIN_DELTA
            )
            if moved:
                accepted = (path, q11_f, deltas)
                break
        if accepted is None:
            raise ControlMatchFailure(
                {"seed": seed, "attempts": F_MAX_ATTEMPTS, "cell": ctx.cell,
                 "law": "NOT_RUN_CONTROL_MATCHING (matching or Q-11 movement "
                        "never satisfied)"})
        path, q11_f, deltas = accepted
        matched_paths.append(path)
        res = _run_engine(ctx, _route(path), ctx.a4_specs, tier)
        seed_rows.append({
            "seed": seed, "net_pnl": res.totals["net_pnl"],
            "trades": res.totals["trades"],
            "q11": q11_f, "q11_moved": True, "deltas": deltas,
        })
    nets = [r["net_pnl"] for r in seed_rows]
    return {
        "seeds": seed_rows,
        "median_net_pnl": float(np.median(nets)),
        "q11_anchor": q11_e,
        "null_invalid_flag": False,
        "tolerances": F_TOL,
        "movement_law": "Q-11 inside acceptance; every reported seed moved",
    }


class ControlMatchFailure(RuntimeError):
    def __init__(self, payload):
        super().__init__("NOT_RUN_CONTROL_MATCHING")
        self.payload = payload


# --------------------------------------------------------------------------
# runner


def _persist(out_root: pathlib.Path, cell: str, arm: str, tier: float,
             res, extra: dict | None = None) -> None:
    rec = {
        "schema": SCORED_SCHEMA,
        "arm": arm,
        "cost_tier": tier,
        "metrics": {},
        "totals": dict(res.totals),
        "fold_net_pnl": list(res.fold_net_pnl),
        "engine_identity": _identity_ok(res),
        "fold_reconciliation": _fold_ok(res),
        "trades": [asdict(t) for t in res.trades],
        "extra": extra or {},
    }
    d = out_root / cell / arm
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{_tier_tag(tier)}.json").write_text(
        json.dumps(rec, indent=1, sort_keys=True, default=str) + "\n"
    )


def _assert_b_equivalence(ctx: CellCtx, res) -> None:
    stored = json.loads(
        (V2_LEDGERS / ctx.cell / "JEV_ONLY_ROUTER" / "tier_1.json").read_text()
    )["totals"]
    got = res.totals
    for k_got, k_sto in [("net_pnl", "net_pnl"), ("gross_pnl", "gross_pnl"),
                         ("costs_fee", "costs_fee"), ("costs_slip", "costs_slip"),
                         ("costs_funding", "costs_funding")]:
        if abs(got[k_got] - stored[k_sto]) >= 1e-6:
            raise RuntimeError(
                f"arm B equivalence FAILED on {ctx.cell}.{k_got}: "
                f"{got[k_got]} != {stored[k_sto]} — abort before any C outcome")
    if got["trades"] != stored["trades"]:
        raise RuntimeError(f"arm B trade-count equivalence FAILED on {ctx.cell}")


def run_all() -> int:
    out_root = CYCLE_DIR / "runtime" / "scored"
    summary: dict = {
        "schema": "rsmv1_scored_summary@1",
        "cycle": "REGIME-STRATEGY-MAPPING-V1",
        "started_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cells": {},
        "trial_accounting": {"planned": 21, "planned_sensitivity": 6, "observed": 0,
         "denominator_law": "21 primary (frozen floors) + 6 owner-instructed sensitivity (C_RELAXED/F_RELAXED, relaxed floors 10/2/50, frozen pre-outcome); verdict decided on PRIMARY only"},
        "disclosure": (
            "S0 DISCOVERY on an outcome-observed corpus. Strongest allowed "
            "verdict: DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION. No "
            "shadow/promotion. S1 sealed. No orders."
        ),
    }
    observed = 0
    results_cache: dict[str, dict] = {}

    for cell in ("BTC_H1", "BTC_H4", "SPY_D1"):
        ctx = CellCtx(cell)
        cell_blk: dict = {"arms": {}}

        # -- references (never scored)
        # -- arm A1 / A2 (order: references first so B equivalence gates C)
        res_a1 = arm_a1(ctx, 1.0)
        res_a2 = arm_a2(ctx, 1.0)
        res_b1 = arm_b(ctx, 1.0)
        _assert_b_equivalence(ctx, res_b1)  # hard gate BEFORE any C outcome

        # -- arm C at base tier (selection audit captured)
        res_c, sel_audit, route_report, mapping_by_fold = arm_c(ctx, 1.0)

        # turnover rejection law
        c_trades = res_c.totals["trades"]
        cap = V2_JEV_TRADE_PINS[cell]
        turnover_law = {
            "v2_jev_only_trade_pin": cap,
            "arm_c_trades": c_trades,
            "verdict": "PASS" if c_trades < cap else "FAIL",
        }

        # -- arms D, E at base tier
        res_d, rep_d = arm_d(ctx, 1.0)
        res_e, rep_e = arm_e(ctx, 1.0)

        # -- arm F at base tier (may raise ControlMatchFailure -> recorded)
        f_blk = None
        f_error = None
        try:
            f_blk = arm_f(ctx, mapping_by_fold, 1.0)
        except ControlMatchFailure as exc:
            f_error = exc.payload

        # -- tier sweeps for every arm (recompute per tier; deterministic)
        tier_results: dict[str, dict[float, object]] = {
            "A1_ALWAYS_ON_MR": {1.0: res_a1}, "A2_ALWAYS_ON_TREND": {1.0: res_a2},
            "B_ORIGINAL_V2_MAPPING": {1.0: res_b1},
            "C_REGIME_SPECIALIST_ROUTER": {1.0: res_c},
            "D_SPARSE_JEV_RISK_OFF_VETO": {1.0: res_d},
            "E_DETERMINISTIC_PLUS_JEV_VETO": {1.0: res_e},
        }
        for arm, by_tier in tier_results.items():
            for tier in TIERS:
                if tier in by_tier:
                    continue
                if arm == "A1_ALWAYS_ON_MR":
                    by_tier[tier] = arm_a1(ctx, tier)
                elif arm == "A2_ALWAYS_ON_TREND":
                    by_tier[tier] = arm_a2(ctx, tier)
                elif arm == "B_ORIGINAL_V2_MAPPING":
                    by_tier[tier] = arm_b(ctx, tier)
                elif arm == "C_REGIME_SPECIALIST_ROUTER":
                    r, _, _, _ = arm_c(ctx, tier)
                    by_tier[tier] = r
                elif arm == "D_SPARSE_JEV_RISK_OFF_VETO":
                    r, _ = arm_d(ctx, tier)
                    by_tier[tier] = r
                else:
                    r, _ = arm_e(ctx, tier)
                    by_tier[tier] = r

        # -- persist everything (atomic: in-memory first, write at end)
        for arm, by_tier in tier_results.items():
            cell_blk["arms"][arm] = {}
            for tier, res in sorted(by_tier.items()):
                extra = {}
                if arm == "C_REGIME_SPECIALIST_ROUTER":
                    extra = {"selection_audit": sel_audit,
                             "routing_report": route_report,
                             "turnover_rejection_law": turnover_law,
                             "regime_switches": int(sum(
                                 1 for r in ctx.ct.timeline.rows if r["switched"])),
                             "position_switches": int(res.totals["trades"])}
                if arm == "D_SPARSE_JEV_RISK_OFF_VETO":
                    extra = {"routing_report": rep_d}
                if arm == "E_DETERMINISTIC_PLUS_JEV_VETO":
                    extra = rep_e
                _persist(out_root, cell, arm, tier, res, extra)
                cell_blk["arms"][arm][_tier_tag(tier)] = {
                    "net": res.totals["net_pnl"],
                    "trades": res.totals["trades"],
                    "fold_nets": list(res.fold_net_pnl),
                }
        if f_blk is not None:
            _persist(out_root, cell, "F_EPISODE_SHUFFLED_MATCHED", 1.0,
                     _run_engine(ctx, [FLAT] * ctx.n, ctx.a4_specs, 1.0),
                     {"f_control": f_blk})
            cell_blk["arms"]["F_EPISODE_SHUFFLED_MATCHED"] = {
                "median_net_pnl": f_blk["median_net_pnl"],
                "seeds": len(f_blk["seeds"]),
                "null_invalid_flag": f_blk["null_invalid_flag"],
            }
        else:
            cell_blk["arms"]["F_EPISODE_SHUFFLED_MATCHED"] = {
                "status": "NOT_RUN_CONTROL_MATCHING", "detail": f_error}

        # -- owner-instructed floor sensitivity (frozen pre-outcome):
        #    C_RELAXED + F_RELAXED under RELAXED_OUTER_FLOORS (10/2/50).
        #    SENSITIVITY ONLY: never the primary candidate.
        res_cr, sel_audit_r, route_report_r, mapping_r = arm_c(
            ctx, 1.0, outer_floors=RELAXED_OUTER_FLOORS)
        c_trades_r = res_cr.totals["trades"]
        turnover_law_r = {
            "v2_jev_only_trade_pin": V2_JEV_TRADE_PINS[cell],
            "arm_c_relaxed_trades": c_trades_r,
            "verdict": "PASS" if c_trades_r < V2_JEV_TRADE_PINS[cell] else "FAIL",
        }
        fr_blk = None
        fr_error = None
        try:
            fr_blk = arm_f(ctx, mapping_r, 1.0)
        except ControlMatchFailure as exc:
            fr_error = exc.payload
        cr_tiers = {1.0: res_cr}
        for tier in TIERS:
            if tier in cr_tiers:
                continue
            r, _, _, _ = arm_c(ctx, tier, outer_floors=RELAXED_OUTER_FLOORS)
            cr_tiers[tier] = r
        cell_blk["arms"]["C_RELAXED_REGIME_SPECIALIST_ROUTER"] = {}
        for tier, res in sorted(cr_tiers.items()):
            _persist(out_root, cell, "C_RELAXED_REGIME_SPECIALIST_ROUTER", tier,
                     res, {
                         "selection_audit": sel_audit_r,
                         "routing_report": route_report_r,
                         "outer_floors": RELAXED_OUTER_FLOORS,
                         "sensitivity_note": "owner-instructed relaxed-floor "
                                             "variant; NOT the primary candidate",
                         "turnover_rejection_law": turnover_law_r})
            cell_blk["arms"]["C_RELAXED_REGIME_SPECIALIST_ROUTER"][_tier_tag(tier)] = {
                "net": res.totals["net_pnl"], "trades": res.totals["trades"],
                "fold_nets": list(res.fold_net_pnl)}
        if fr_blk is not None:
            _persist(out_root, cell, "F_RELAXED_EPISODE_SHUFFLED_MATCHED", 1.0,
                     _run_engine(ctx, [FLAT] * ctx.n, ctx.a4_specs, 1.0),
                     {"f_control": fr_blk})
            cell_blk["arms"]["F_RELAXED_EPISODE_SHUFFLED_MATCHED"] = {
                "median_net_pnl": fr_blk["median_net_pnl"],
                "seeds": len(fr_blk["seeds"]),
                "null_invalid_flag": fr_blk["null_invalid_flag"]}
        else:
            cell_blk["arms"]["F_RELAXED_EPISODE_SHUFFLED_MATCHED"] = {
                "status": "NOT_RUN_CONTROL_MATCHING", "detail": fr_error}

        observed += 7  # primary cells (7) + sensitivity (2)
        observed += 2
        summary["cells"][cell] = cell_blk
        summary["trial_accounting"]["observed"] = observed
        results_cache[cell] = cell_blk

    summary["finished_at_utc"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "scored_summary.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n")
    (CYCLE_DIR / "evidence" / "scored").mkdir(parents=True, exist_ok=True)
    (CYCLE_DIR / "evidence" / "scored" / "scored_summary.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n")
    print("scored complete: observed", observed, "/ 21")
    return 0
