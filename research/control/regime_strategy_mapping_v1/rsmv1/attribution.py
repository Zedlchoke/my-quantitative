"""Phase 1 — V2 mechanism attribution audit (outcome-observed diagnostic).

DIAGNOSTIC ONLY (plan §3): nothing measured here may be selected as a
validated configuration. Inputs: V2 frozen trade ledgers (tier 1), read-only;
the rebuilt regime timelines (verified vs V2 recorded metrics); the V2 frozen
mapping/fold contracts. Zero provider calls; no V2 artifact is written.

DISCLOSURE (must appear verbatim in any report built on this module):
"Outcome-observed diagnostics on the terminal V2 corpus. Nothing here is a
validated configuration; counterfactuals locate the failure mechanism only.
No strategy design, no parameter selection, and no counterfactual may be
read as a proposal (plan section 3)."

Reconciliation law: every per-arm gross/fee/slip/funding/net and trade count
recomputed from the V2 ledger trades must equal the V2 stored totals to
<1e-6 (each check PASS/FAIL; a mismatch is never silently adjusted). The
forked engine rerun on the REBUILT JEV target series must additionally
reproduce the V2 stored JEV_ONLY totals and fold nets to <1e-6 (baseline
reproduction), and the engine identity (100000 + net == equity[-1];
|sum(fold_net) - net| < 1e-9) must hold on every rerun.

Per-trade cause classification (FROZEN rule, applied to every arm):
  exit_reason fold_flat            -> fold_force_flat
  exit_reason stop | strategy_exit -> strategy_native
  exit_reason regime_off:
      the NEXT entry of the arm (immediate successor in the ledger) lies in
      the SAME fold, has the SAME direction, and the governing target over
      the intervening bars [exit_bar .. next_entry_bar] never maps to the
      OPPOSITE direction   -> unnecessary_close_reopen
      otherwise            -> regime_switch
  Entry fills and funding inherit their trade's cause class.

Counterfactual families (diagnostic target transforms, engine mechanics
unchanged):
  cf_a no-op: hold the same direction — a target change that does not change
      the direction is suppressed (no close/reopen of the same-direction
      position); direction changes (to flat or opposite) are honored.
  cf_b transition buffer k regime bars (k=1,2,3): the persisted label is
      honored k regime bars LATE (delayed label timeline, timestamps
      unchanged — no look-ahead, staleness law untouched).
  cf_c minimum hold h regime bars (h=2,4,8): once an invested direction is
      entered, any target change that would leave that direction is ignored
      for h regime bars (anchor = the direction-entry bar); opposite-
      direction changes are honored immediately; after the window the
      target is followed again.
  cf_d JEV risk-off veto only: a constant always-on base strategy, flattened
      in DISTRIBUTION/DOWNTREND per the frozen label set (both MR_LONG and
      TREND_LONG bases + their always-on references are measured; no base is
      selected or promoted).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from . import LABELS
from .data import Bars  # noqa: F401  (typing only)
from .engine import (
    Engine,
    CostModel,
    folds_from_regime_ts,
    fold_partition_invariants,
    targets_from_regime,
)
from .freezes import Freezes
from .regime_timeline import CellTimelines, rebuild_cell_timeline
from .strategies import FLAT, MR_LONG, TREND_LONG, TREND_SHORT

V2_CYCLE_DIR = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/jev-regime-router-v2/"
    "integration/research/control/jev_regime_router_v2"
)
V2_LEDGERS = V2_CYCLE_DIR / "runtime" / "scored"

ARMS = (
    "ALWAYS_ON_MEAN_REVERSION",
    "ALWAYS_ON_TREND",
    "DETERMINISTIC_REGIME_ROUTER",
    "JEV_ONLY_ROUTER",
    "DETERMINISTIC_PLUS_JEV_CONFIRMATION",
    "RANDOM_MATCHED_ROUTER",
)
JEV_ARM = "JEV_ONLY_ROUTER"
CELLS = ("BTC_H1", "BTC_H4", "SPY_D1")

ATTR_SCHEMA = "rsmv1_mechanism_attribution@1"
RECON_TOL = 1e-6
FOLD_RECON_TOL = 1e-9
ENGINE_IDENTITY_INITIAL = 100_000.0

# A7 terminal audit (audits/a7_terminal_audit.md §2) JEV_ONLY base-tier fold
# nets, rounded to whole dollars by the auditor — independent cross-check.
A7_JEV_FOLD_NETS = {
    "BTC_H1": [-40997.0, -37419.0, -4923.0, -4802.0],
    "BTC_H4": [-44582.0, -27241.0, -6522.0, -6930.0],
    "SPY_D1": [-25488.0, 4985.0, -14810.0, -16310.0],
}

CAUSE_FOLD = "fold_force_flat"
CAUSE_STRATEGY = "strategy_native"
CAUSE_REGIME = "regime_switch"
CAUSE_NOOP = "unnecessary_close_reopen"

DISCLOSURE = (
    "Outcome-observed diagnostics on the terminal V2 corpus. "
    "Nothing here is a validated configuration; counterfactuals "
    "locate the failure mechanism only. No strategy design, no parameter "
    "selection, and no counterfactual may be read as a proposal "
    "(plan section 3)."
)


def direction_of(strategy: str | None) -> int:
    if strategy in (TREND_LONG, MR_LONG):
        return 1
    if strategy == TREND_SHORT:
        return -1
    return 0  # FLAT / None


def targets_directions(targets: list[str | None]) -> list[int]:
    return [direction_of(t) for t in targets]


# ---------------------------------------------------------------------------
# pure helpers (unit-tested; no I/O)
# ---------------------------------------------------------------------------


def _r2(x: float) -> float:
    return round(float(x), 2)


def recompute_totals(trades: list[dict]) -> dict:
    """Sum the ledger trade components with exact fsum summation."""
    return {
        "trades": len(trades),
        "gross": math.fsum(t["gross_pnl"] for t in trades),
        "fee": math.fsum(t["fees"] for t in trades),
        "slip": math.fsum(t["slip"] for t in trades),
        "funding": math.fsum(t["funding"] for t in trades),
        "net": math.fsum(t["net_pnl"] for t in trades),
    }


def reconcile_ledger(ledger: dict) -> tuple[bool, dict, dict]:
    """Recompute one tier-1 ledger's totals from its trades vs stored totals.

    Returns (ok, recomputed, stored). ok is True iff counts match and every
    component agrees to <1e-6 (RECON_TOL).
    """
    rec = recompute_totals(ledger["trades"])
    sto = ledger["totals"]
    stored = {
        "trades": sto["trades"],
        "gross": sto["gross_pnl"],
        "fee": sto["costs_fee"],
        "slip": sto["costs_slip"],
        "funding": sto["costs_funding"],
        "net": sto["net_pnl"],
    }
    ok = (
        rec["trades"] == stored["trades"]
        and abs(rec["gross"] - stored["gross"]) < RECON_TOL
        and abs(rec["fee"] - stored["fee"]) < RECON_TOL
        and abs(rec["slip"] - stored["slip"]) < RECON_TOL
        and abs(rec["funding"] - stored["funding"]) < RECON_TOL
        and abs(rec["net"] - stored["net"]) < RECON_TOL
    )
    return ok, rec, stored


def stored_engine_identity_ok(ledger: dict) -> tuple[bool, dict]:
    """V2 engine identity on the STORED ledger: 100000 + net == equity[-1]
    (<1e-6) and |sum(stored fold nets) - net| < 1e-9."""
    net = ledger["totals"]["net_pnl"]
    eq_last = float(ledger["equity"][-1])
    fold_sum = math.fsum(ledger["fold_net_pnl"])
    ok_id = abs((ENGINE_IDENTITY_INITIAL + net) - eq_last) < RECON_TOL
    ok_fold = abs(fold_sum - net) < FOLD_RECON_TOL
    return (
        ok_id and ok_fold,
        {
            "identity_gap": (ENGINE_IDENTITY_INITIAL + net) - eq_last,
            "fold_sum_gap": fold_sum - net,
        },
    )


def classify_exit_reason(reason: str) -> str:
    """Frozen rule, exit-reason branch: fold_flat -> fold_force_flat;
    stop | strategy_exit -> strategy_native; regime_off handled separately."""
    if reason == "fold_flat":
        return CAUSE_FOLD
    if reason in ("stop", "strategy_exit"):
        return CAUSE_STRATEGY
    if reason == "regime_off":
        return "regime_off"  # caller must refine via classify_regime_off
    return "unknown_reason"


def classify_regime_off(
    trade: dict, next_entry: dict | None, target_dirs: list[int]
) -> str:
    """Frozen rule for a regime_off exit (target_dirs = per-exec-bar target
    direction of the arm's governing target series).

    unnecessary_close_reopen iff the NEXT ledger entry exists, lies in the
    SAME fold, has the SAME direction, and the governing target over
    [exit_bar .. next_entry_bar] never maps to the OPPOSITE direction;
    otherwise regime_switch.
    """
    d = trade["direction"]
    if next_entry is None or next_entry["fold_id"] != trade["fold_id"]:
        return CAUSE_REGIME
    if next_entry["direction"] != d:
        return CAUSE_REGIME
    lo = int(trade["exit_bar"])
    hi = min(int(next_entry["entry_bar"]), len(target_dirs) - 1)
    for i in range(lo, hi + 1):
        if target_dirs[i] == -d:
            return CAUSE_REGIME
    return CAUSE_NOOP


def classify_trade(
    t: dict, j: int, tr: list[dict], target_dirs: list[int]
) -> str:
    """Frozen per-trade cause classification (see module docstring)."""
    cause = classify_exit_reason(t["exit_reason"])
    if cause == "regime_off":
        nxt = tr[j + 1] if j + 1 < len(tr) else None
        return classify_regime_off(t, nxt, target_dirs)
    return cause


def noop_hold_same_direction(targets: list[str | None]) -> list[str | None]:
    """cf_a transform: suppress every target change that does not change the
    direction (hold the current strategy string until the direction changes).
    Pre-first-decision Nones pass through unchanged."""
    fixed: list[str | None] = [None] * len(targets)
    cur: str | None = None
    cur_d = 0
    for i, tgt in enumerate(targets):
        if tgt is None:
            continue
        d = direction_of(tgt)
        if cur is None or d != cur_d:
            cur, cur_d = tgt, d
        fixed[i] = cur
    return fixed


def delay_labels(persisted: list[str], k: int) -> list[str]:
    """cf_b transform: honor the persisted label k regime bars late.

    delayed[j] = persisted[j - k] for j >= k; persisted[0] for j < k.
    Timestamps are unchanged (no look-ahead; staleness law untouched).
    """
    n = len(persisted)
    if k <= 0:
        return list(persisted)
    if k >= n:
        return [persisted[0]] * n
    return [persisted[0]] * k + list(persisted[: n - k])


def min_hold_targets(
    targets: list[str | None], ts_open, hold_ns: int
) -> list[str | None]:
    """cf_c transform: once an invested direction is entered, ignore every
    target change that would leave that direction for hold_ns (measured from
    the direction-entry bar open). Opposite-direction changes are honored
    immediately (they re-anchor). After the window the target is followed
    again. Pre-first-decision Nones pass through."""
    out: list[str | None] = [None] * len(targets)
    cur: str | None = None
    held_d = 0
    anchor_ts: int | None = None
    for i, tgt in enumerate(targets):
        if tgt is None:
            continue
        ts_o = int(ts_open[i])
        d = direction_of(tgt)
        if d != 0:
            if d != held_d:
                cur, held_d, anchor_ts = tgt, d, ts_o
            elif anchor_ts is not None and ts_o - anchor_ts < hold_ns:
                pass  # inside minimum hold: keep the position untouched
            else:
                cur = tgt  # same direction after the window: follow target
        else:  # target maps flat
            if held_d != 0 and anchor_ts is not None and ts_o - anchor_ts < hold_ns:
                pass  # veto the flat: stay invested
            else:
                cur, held_d, anchor_ts = tgt, 0, None
        out[i] = cur
    return out


# ---------------------------------------------------------------------------
# per-cell attribution
# ---------------------------------------------------------------------------


class Attribution:
    """One cell's V2 attribution bundle (diagnostic only)."""

    def __init__(self, cycle_dir: str | Path, cell: str) -> None:
        self.cycle_dir = Path(cycle_dir).resolve()
        self.cell = cell
        self.fz = Freezes(self.cycle_dir)
        self.ct: CellTimelines = rebuild_cell_timeline(self.cycle_dir, cell)
        self._build_context()
        self.ledgers = {arm: self._load_ledger(arm) for arm in ARMS}
        self.targets = self._jev_targets()
        self.target_dirs = targets_directions(self.targets)
        self._gov: list[str] | None = None
        self._ind = None
        self.checks: list[dict] = []

    # -- context ----------------------------------------------------------

    def _build_context(self) -> None:
        cell = self.cell
        fz = self.fz
        self.exec_bars: Bars = self.ct.exec_bars
        spans = [
            (_iso_ns(sp["start"]), _iso_ns(sp["end"]))
            for sp in fz.fold_contract["cells"][cell]["folds"]
        ]
        self.folds_exec = folds_from_regime_ts(self.exec_bars, spans)
        first_decision_ts = int(self.ct.regime_bars.ts_close[fz.warmup(cell)])
        first_required = next(
            (
                i
                for i, t in enumerate(self.exec_bars.ts_open.tolist())
                if t > first_decision_ts
            ),
            len(self.exec_bars.ts_close),
        )
        fold_partition_invariants(
            self.folds_exec, len(self.exec_bars.ts_close), first_required
        )
        costs = fz.mapping["costs"]
        if cell.startswith("BTC"):
            c = costs["BTCUSDT"]
            self.cost_model = CostModel(
                fee_bps=c["taker_fee_bps_per_side"],
                slip_bps=c["slippage_bps_per_side"],
                funding_rate=c["funding_per_8h_signed"],
                label="BTC 5+1 bps/side + funding",
            )
        else:
            c = costs["SPY"]
            self.cost_model = CostModel(
                fee_bps=c["cost_bps_per_fill"], slip_bps=0.0, label="SPY 10bps/fill"
            )
        self.asset = "BTCUSDT" if cell.startswith("BTC") else "SPY"

    def _mapping(self) -> dict:
        raw = self.fz.mapping["mapping"]
        return {k: v[self.asset] for k, v in raw.items()}

    def _jev_targets(self) -> list[str | None]:
        return targets_from_regime(
            self.exec_bars,
            self.ct.ts,
            self.ct.persisted,
            self.ct.period_ns,
            self._mapping(),
        )

    def _exec_indicators(self):
        if self._ind is None:
            from .strategies import exec_indicators

            self._ind = exec_indicators(self.exec_bars)
        return self._ind

    def _governing_labels(self) -> list[str]:
        """Persisted label governing each exec bar (same law as targets)."""
        if self._gov is not None:
            return self._gov
        import bisect

        ts = self.ct.ts
        period = self.ct.period_ns
        out: list[str] = []
        for ts_o in self.exec_bars.ts_open.tolist():
            j = bisect.bisect_right(ts, int(ts_o) - 1) - 1
            if j < 0:
                out.append("PRE_FIRST_DECISION")
            elif int(ts_o) - ts[j] > 2 * period:
                out.append("STALE")
            else:
                out.append(self.ct.persisted[j])
        self._gov = out
        return out

    # -- ledger reconciliation -------------------------------------------

    def _load_ledger(self, arm: str) -> dict:
        return json.loads((V2_LEDGERS / self.cell / arm / "tier_1.json").read_text())

    def reconcile(self) -> dict:
        out = {}
        for arm in ARMS:
            ok, rec, stored = reconcile_ledger(self.ledgers[arm])
            self.checks.append(
                {
                    "check": f"ledger_reconciliation[{arm}]",
                    "cell": self.cell,
                    "verdict": "PASS" if ok else "FAIL",
                    "recomputed": {k: _r2(v) for k, v in rec.items()},
                    "stored": {k: _r2(v) for k, v in stored.items()},
                }
            )
            ok_id, gaps = stored_engine_identity_ok(self.ledgers[arm])
            self.checks.append(
                {
                    "check": f"stored_engine_identity[{arm}]",
                    "cell": self.cell,
                    "verdict": "PASS" if ok_id else "FAIL",
                    **{k: _r2(v) for k, v in gaps.items()},
                }
            )
            out[arm] = {
                "stored_net": stored["net"],
                "stored_gross": stored["gross"],
                "stored_fee": stored["fee"],
                "stored_slip": stored["slip"],
                "stored_funding": stored["funding"],
                "trades": stored["trades"],
            }
        return out

    # -- decomposition ------------------------------------------------------

    @staticmethod
    def _equity_deltas(ledger: dict) -> np.ndarray:
        eq = np.asarray(ledger["equity"], dtype=float)
        return np.diff(np.concatenate([[ENGINE_IDENTITY_INITIAL], eq]))

    def pnl_by_regime(self) -> dict:
        """Bar-level equity-delta attribution by the governing persisted label
        (every arm; the labels are arm-independent), plus trade-level PnL by
        entry regime for JEV_ONLY."""
        gov = self._governing_labels()
        extra = ("PRE_FIRST_DECISION", "STALE")
        all_labels = list(LABELS) + list(extra)
        bar_level = {}
        for arm in ARMS:
            deltas = self._equity_deltas(self.ledgers[arm])
            buckets: dict[str, list[float]] = {l: [] for l in all_labels}
            for i, lab in enumerate(gov):
                buckets[lab].append(float(deltas[i]))
            sums = {l: math.fsum(v) for l, v in buckets.items() if v}
            total = math.fsum(sums.values())
            ledger_net = float(self.ledgers[arm]["equity"][-1]) - ENGINE_IDENTITY_INITIAL
            ok = abs(total - ledger_net) < RECON_TOL
            if arm == JEV_ARM:
                self.checks.append(
                    {
                        "check": "bar_attribution_identity",
                        "cell": self.cell,
                        "verdict": "PASS" if ok else "FAIL",
                        "sum_by_label": _r2(total),
                        "ledger_net": _r2(ledger_net),
                    }
                )
            bar_level[arm] = {k: _r2(v) for k, v in sums.items()}
        trade_level = {}
        for t in self.ledgers[JEV_ARM]["trades"]:
            lab = gov[t["entry_bar"]]
            b = trade_level.setdefault(
                lab, {"trades": 0, "net": 0.0, "gross": 0.0, "costs": 0.0}
            )
            b["trades"] += 1
            b["net"] += t["net_pnl"]
            b["gross"] += t["gross_pnl"]
            b["costs"] += t["fees"] + t["slip"] + t["funding"]
        return {
            "bar_level_equity_delta_by_governing_label": bar_level,
            "jev_only_trade_level_by_entry_regime": {
                k: {kk: _r2(vv) for kk, vv in v.items()} for k, v in trade_level.items()
            },
        }

    def stable_vs_transition(self) -> dict:
        """Equity deltas inside windows of +-k regime bars around each
        persisted switch vs outside them (k = 1/2/3), for every arm."""
        switch_ts = [
            int(r["regime_bar_close_ns"])
            for r in self.ct.timeline.rows
            if r["switched"]
        ]
        ts_open = self.exec_bars.ts_open.tolist()
        n = len(ts_open)
        out: dict = {"n_switches": len(switch_ts)}
        for k in (1, 2, 3):
            win = k * self.ct.period_ns
            inside_mask = np.zeros(n, dtype=bool)
            for s in switch_ts:
                lo = np.searchsorted(ts_open, s - win, side="left")
                hi = np.searchsorted(ts_open, s + win, side="right")
                inside_mask[lo:hi] = True
            block = {}
            for arm in ARMS:
                deltas = self._equity_deltas(self.ledgers[arm])
                d = np.asarray(deltas, dtype=float)
                inside = math.fsum(d[inside_mask].tolist())
                outside = math.fsum(d[~inside_mask].tolist())
                block[arm] = {
                    "pnl_inside": _r2(inside),
                    "pnl_outside": _r2(outside),
                }
            block["n_bars_inside"] = int(inside_mask.sum())
            block["n_bars_outside"] = n - int(inside_mask.sum())
            out[f"window_pm{k}"] = block
        return out

    def counts_and_holding(self) -> dict:
        per_arm = {}
        for arm in ARMS:
            tr = self.ledgers[arm]["trades"]
            exits_by_reason: dict[str, int] = {}
            reversals = 0
            same_dir_reentries = 0
            holds: list[float] = []
            for j, t in enumerate(tr):
                exits_by_reason[t["exit_reason"]] = (
                    exits_by_reason.get(t["exit_reason"], 0) + 1
                )
                holds.append(float(t["exit_bar"] - t["entry_bar"]))
                if j > 0:
                    if t["direction"] != tr[j - 1]["direction"]:
                        reversals += 1
                    elif t["direction"] != 0:
                        same_dir_reentries += 1
            per_arm[arm] = {
                "entries": len(tr),
                "exits_by_reason": exits_by_reason,
                "reversals": reversals,
                "same_direction_reentries": same_dir_reentries,
                "median_hold_exec_bars": float(np.median(holds)) if holds else 0.0,
                "mean_hold_exec_bars": _r2(float(np.mean(holds))) if holds else 0.0,
                "turnover_stored": self.ledgers[arm]["metrics"]["turnover"],
            }
        # no-op target updates (arm-independent: the JEV governing target
        # series): label changes that did NOT change the target direction
        changes = 0
        noop = 0
        prev: str | None = None
        prev_d = 0
        for tgt in self.targets:
            if tgt != prev:
                if prev is not None:
                    changes += 1
                    if direction_of(tgt) == prev_d:
                        noop += 1
                prev = tgt
                prev_d = direction_of(tgt)
        per_arm["target_series_changes"] = changes
        per_arm["no_op_target_updates_direction_unchanged"] = noop
        return per_arm

    def cost_attribution(self) -> dict:
        """Per-trade frozen cause classification -> PnL/cost totals per arm."""
        per_arm = {}
        for arm in ARMS:
            tr = self.ledgers[arm]["trades"]
            classes: dict[str, dict] = {}
            net_lists: dict[str, list[float]] = {}
            for j, t in enumerate(tr):
                cause = classify_trade(t, j, tr, self.target_dirs)
                b = classes.setdefault(
                    cause,
                    {"trades": 0, "gross": 0.0, "fee": 0.0, "slip": 0.0,
                     "funding": 0.0},
                )
                b["trades"] += 1
                b["gross"] += t["gross_pnl"]
                b["fee"] += t["fees"]
                b["slip"] += t["slip"]
                b["funding"] += t["funding"]
                net_lists.setdefault(cause, []).append(t["net_pnl"])
            for cause, lst in net_lists.items():
                classes[cause]["net"] = math.fsum(lst)
            tot = math.fsum(x for lst in net_lists.values() for x in lst)
            sto = self.ledgers[arm]["totals"]["net_pnl"]
            ok = abs(tot - sto) < RECON_TOL
            if arm == JEV_ARM:
                self.checks.append(
                    {
                        "check": "cost_attribution_reconciliation",
                        "cell": self.cell,
                        "verdict": "PASS" if ok else "FAIL",
                        "class_sum_net": _r2(tot),
                        "ledger_net": _r2(sto),
                    }
                )
            per_arm[arm] = {
                c: {
                    "trades": v["trades"],
                    "net": _r2(v["net"]),
                    "gross": _r2(v["gross"]),
                    "costs": _r2(v["fee"] + v["slip"] + v["funding"]),
                }
                for c, v in classes.items()
            }
        return per_arm

    # -- counterfactuals (diagnostic) --------------------------------------

    def _rerun(self, targets: list[str | None]) -> dict:
        eng = Engine(
            self.exec_bars,
            targets,
            self.folds_exec,
            self.cost_model,
            ENGINE_IDENTITY_INITIAL,
            ind=self._exec_indicators(),
        )
        res = eng.run()
        net = res.totals["net_pnl"]
        ok_id = (
            abs((ENGINE_IDENTITY_INITIAL + net) - float(res.equity[-1])) < RECON_TOL
            and abs(math.fsum(res.fold_net_pnl) - net) < FOLD_RECON_TOL
        )
        if not ok_id:
            raise AssertionError("rerun engine identity violated")
        return {
            "net": _r2(net),
            "gross": _r2(res.totals["gross_pnl"]),
            "costs": _r2(
                res.totals["costs_fee"]
                + res.totals["costs_slip"]
                + res.totals["costs_funding"]
            ),
            "trades": res.totals["trades"],
            "_net_raw": net,
            "_fold_net_raw": list(res.fold_net_pnl),
        }

    def baseline_reproduction(self) -> None:
        """The forked engine on the REBUILT target series must reproduce the
        V2 stored JEV_ONLY ledger (totals <1e-6, fold nets <1e-6) and the A7
        audit's fold nets (rounded to whole dollars)."""
        raw = self._rerun(self.targets)
        sto = self.ledgers[JEV_ARM]["totals"]
        components = {
            "net": raw["_net_raw"],
            "trades": raw["trades"],
        }
        ok_tot = components["trades"] == sto["trades"] and abs(
            components["net"] - sto["net_pnl"]
        ) < RECON_TOL
        self.checks.append(
            {
                "check": "baseline_rerun_totals_reconcile[JEV_ONLY_ROUTER]",
                "cell": self.cell,
                "verdict": "PASS" if ok_tot else "FAIL",
                "rerun_net": _r2(raw["_net_raw"]),
                "stored_net": _r2(sto["net_pnl"]),
                "rerun_trades": raw["trades"],
                "stored_trades": sto["trades"],
            }
        )
        folds = raw["_fold_net_raw"]
        stored_folds = self.ledgers[JEV_ARM]["fold_net_pnl"]
        ok_folds = len(folds) == len(stored_folds) and all(
            abs(a - b) < RECON_TOL for a, b in zip(folds, stored_folds)
        )
        self.checks.append(
            {
                "check": "baseline_rerun_fold_nets_reconcile[JEV_ONLY_ROUTER]",
                "cell": self.cell,
                "verdict": "PASS" if ok_folds else "FAIL",
                "rerun_fold_nets": [_r2(x) for x in folds],
                "stored_fold_nets": [_r2(x) for x in stored_folds],
            }
        )
        a7 = A7_JEV_FOLD_NETS[self.cell]
        ok_a7 = len(folds) == len(a7) and all(
            abs(a - b) <= 0.5 + 1e-9 for a, b in zip(folds, a7)
        )
        self.checks.append(
            {
                "check": "a7_audit_fold_nets_crosscheck[JEV_ONLY_ROUTER]",
                "cell": self.cell,
                "verdict": "PASS" if ok_a7 else "FAIL",
                "rerun_fold_nets": [_r2(x) for x in folds],
                "a7_audit_fold_nets": a7,
            }
        )

    def counterfactuals(self) -> dict:
        base = self.targets
        base_res = self._rerun(base)
        base_net = base_res["_net_raw"]
        mapping = self._mapping()

        def entry(res: dict, name: str) -> tuple[str, dict]:
            delta = res["_net_raw"] - base_net
            return name, {
                "net": res["net"],
                "gross": res["gross"],
                "costs": res["costs"],
                "trades": res["trades"],
                "delta_net_vs_baseline": _r2(delta),
            }

        out: dict = {
            "baseline_reproduction_jev_targets": {
                k: v for k, v in base_res.items() if not k.startswith("_")
            }
        }

        # (a) no-op: hold same direction (suppress direction-preserving churn)
        out.update(
            dict(
                [entry(self._rerun(noop_hold_same_direction(base)),
                       "cf_a_noop_hold_same_direction")]
            )
        )

        # (b) transition buffer: honor the persisted label k regime bars late
        for k in (1, 2, 3):
            delayed = targets_from_regime(
                self.exec_bars,
                self.ct.ts,
                delay_labels(self.ct.persisted, k),
                self.ct.period_ns,
                mapping,
            )
            out.update(
                dict([entry(self._rerun(delayed), f"cf_b_buffer_{k}regimebars")])
            )

        # (c) minimum hold of the invested state: 2/4/8 regime bars
        for h in (2, 4, 8):
            held = min_hold_targets(base, self.exec_bars.ts_open, h * self.ct.period_ns)
            out.update(
                dict([entry(self._rerun(held), f"cf_c_minhold_{h}regimebars")])
            )

        # (d) JEV risk-off veto only: constant always-on base, flat in
        # DISTRIBUTION/DOWNTREND. Both frozen always-on bases are measured;
        # neither is selected (diagnostic only).
        for name, strat in (("mr_long", MR_LONG), ("trend_long", TREND_LONG)):
            veto_map = {
                l: (FLAT if l in ("DISTRIBUTION", "DOWNTREND") else strat)
                for l in LABELS
            }
            out.update(
                dict(
                    [
                        entry(
                            self._rerun(
                                targets_from_regime(
                                    self.exec_bars,
                                    self.ct.ts,
                                    self.ct.persisted,
                                    self.ct.period_ns,
                                    veto_map,
                                )
                            ),
                            f"cf_d_riskoff_veto_only_base_{name}",
                        ),
                        entry(
                            self._rerun([strat] * len(base)),
                            f"cf_d_always_on_base_reference_{name}",
                        ),
                    ]
                )
            )
        return out

    # -- bundle --------------------------------------------------------------

    def run(self) -> dict:
        arms_summary = self.reconcile()
        self.baseline_reproduction()
        pnl = self.pnl_by_regime()
        svt = self.stable_vs_transition()
        counts = self.counts_and_holding()
        causes = self.cost_attribution()
        cfs = self.counterfactuals()
        return {
            "schema": ATTR_SCHEMA,
            "cell": self.cell,
            "phase": "P1_MECHANISM_ATTRIBUTION_DIAGNOSTIC",
            "v2_ledgers_readonly": str(V2_LEDGERS / self.cell),
            "arms_summary": arms_summary,
            "pnl_decomposition": pnl,
            "stable_vs_transition": svt,
            "counts_and_holding": counts,
            "cost_attribution_by_cause": causes,
            "counterfactuals_diagnostic_only": cfs,
            "checks": self.checks,
            "disclosure": DISCLOSURE,
        }


def _iso_ns(iso: str) -> int:
    from datetime import datetime, timezone

    s = iso.replace("Z", "+00:00")
    if "T" not in s:
        s += "T00:00:00+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def _headline(cell_bundle: dict) -> dict:
    """Compact cross-cell summary (derived; the per-cell blocks are authority)."""
    arm = cell_bundle["arms_summary"][JEV_ARM]
    causes = cell_bundle["cost_attribution_by_cause"][JEV_ARM]
    cfs = cell_bundle["counterfactuals_diagnostic_only"]
    deltas = {
        k: v["delta_net_vs_baseline"]
        for k, v in cfs.items()
        if isinstance(v, dict) and "delta_net_vs_baseline" in v
    }
    return {
        "jev_only_net": _r2(arm["stored_net"]),
        "jev_only_gross": _r2(arm["stored_gross"]),
        "jev_only_costs": _r2(
            arm["stored_fee"] + arm["stored_slip"] + arm["stored_funding"]
        ),
        "jev_only_trades": arm["trades"],
        "cost_by_cause": {
            c: {"trades": v["trades"], "net": v["net"], "costs": v["costs"]}
            for c, v in causes.items()
        },
        "counterfactual_delta_net": deltas,
    }


def run_all(cycle_dir: str | Path, out_dir: str | Path | None = None) -> dict:
    bundle = {
        "schema": ATTR_SCHEMA + ".bundle",
        "cycle": "REGIME-STRATEGY-MAPPING-V1",
        "phase": "P1_MECHANISM_ATTRIBUTION_DIAGNOSTIC",
        "cells": {},
        "checks": [],
        "disclosure": DISCLOSURE,
    }
    for cell in CELLS:
        attr = Attribution(cycle_dir, cell)
        cb = attr.run()
        bundle["cells"][cell] = cb
        bundle["checks"].extend(cb["checks"])
        cb["headline"] = _headline(cb)
    bundle["all_checks_pass"] = all(
        c["verdict"] == "PASS" for c in bundle["checks"]
    )
    bundle["n_checks"] = len(bundle["checks"])
    bundle["n_checks_pass"] = sum(
        1 for c in bundle["checks"] if c["verdict"] == "PASS"
    )
    bundle["cells_headline"] = {c: b["headline"] for c, b in bundle["cells"].items()}
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "mechanism_attribution.json").write_text(
            json.dumps(bundle, indent=1, sort_keys=True)
        )
    return bundle
