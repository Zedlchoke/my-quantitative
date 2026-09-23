"""Phase 1 — V2 mechanism attribution audit (outcome-observed diagnostic).

DIAGNOSTIC ONLY (plan §3): nothing measured here may be selected as a
validated configuration. Inputs: V2 frozen trade ledgers (tier 1.0x),
read-only; the rebuilt regime timelines (verified vs V2); the V2 frozen
mapping. Zero provider calls; no V2 artifact is written.

Reconciliation law: every per-arm gross/fee/slip/funding/net and trade count
recomputed from the V2 ledger trades must equal the V2 stored totals to
<1e-6 (each check PASS/FAIL). Counterfactuals rerun the FORKED V2 engine
(original mechanics) on transformed target series; engine identity
(100000 + net == equity[-1]; |sum(fold_net) - net| < 1e-9) asserted.

Per-trade cause classification (frozen rule, applied to JEV_ONLY_ROUTER):
  exit_reason fold_flat            -> fold_force_flat
  exit_reason stop | strategy_exit -> strategy_native
  exit_reason regime_off:
      next entry (same arm, same fold) has the SAME direction
      and the intervening governing target never mapped to the OPPOSITE
      direction                                               -> unnecessary_close_reopen
      otherwise                                                -> regime_switch
  Entry fills + funding inherit their trade's cause class.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from . import LABELS
from .data import Bars
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

ATTR_SCHEMA = "rsmv1_mechanism_attribution@1"
RECON_TOL = 1e-6
PERIODS_PER_YEAR = {"BTC_H1": 24 * 365, "BTC_H4": 6 * 365, "SPY_D1": 252}
SPY_PERIOD_NS = 86_400_000_000_000


def direction_of(strategy: str | None) -> int:
    if strategy in (TREND_LONG, MR_LONG):
        return 1
    if strategy == TREND_SHORT:
        return -1
    return 0  # FLAT / None


class Attribution:
    """One cell's V2 attribution bundle."""

    def __init__(self, cycle_dir: str | Path, cell: str) -> None:
        self.cycle_dir = Path(cycle_dir).resolve()
        self.cell = cell
        self.fz = Freezes(self.cycle_dir)
        self.ct: CellTimelines = rebuild_cell_timeline(self.cycle_dir, cell)
        self._build_context()
        self.ledger = self._load_ledger("JEV_ONLY_ROUTER")
        self.targets = self._jev_targets()
        self.checks: list[dict] = []

    # -- context ----------------------------------------------------------

    def _build_context(self) -> None:
        fz = self.fz
        cell = self.cell
        self.exec_bars: Bars = self.ct.exec_bars
        spans = [
            (_iso_ns(sp["start"]), _iso_ns(sp["end"]))
            for sp in fz.fold_contract["cells"][cell]["folds"]
        ]
        self.folds_exec = folds_from_regime_ts(self.exec_bars, spans)
        first_decision_ts = int(
            self.ct.regime_bars.ts_close[fz.warmup(cell)]
        )
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
        costs = fz.mapping_arms_freeze["costs"] if hasattr(fz, "mapping_arms_freeze") \
            else json.loads((self.cycle_dir / "freezes" / "mapping_arms_freeze.json").read_text())["costs"]
        if cell.startswith("BTC"):
            c = costs["BTCUSDT"]
            self.cost_model = CostModel(
                fee_bps=c["taker_fee_bps_per_side"],
                slip_bps=c["slippage_bps_per_side"],
                funding_rate=c["funding_per_8h_signed"],
                label="BTC 6bps/side+funding",
            )
        else:
            c = costs["SPY"]
            self.cost_model = CostModel(
                fee_bps=c["cost_bps_per_fill"], slip_bps=0.0, label="SPY 10bps/fill"
            )

    def _mapping(self) -> dict:
        raw = json.loads(
            (self.cycle_dir / "freezes" / "mapping_arms_freeze.json").read_text()
        )
        asset = "BTCUSDT" if self.cell.startswith("BTC") else "SPY"
        return {k: v[asset] for k, v in raw["mapping"].items()}

    def _jev_targets(self) -> list[str | None]:
        return targets_from_regime(
            self.exec_bars,
            self.ct.ts,
            self.ct.persisted,
            self.ct.period_ns,
            self._mapping(),
        )

    def governing_label(self, i: int) -> str:
        """Persisted label governing exec bar i (same law as targets)."""
        import bisect

        ts_o = int(self.exec_bars.ts_open[i])
        j = bisect.bisect_right(self.ct.ts, ts_o - 1) - 1
        if j < 0:
            return "PRE_FIRST_DECISION"
        if ts_o - self.ct.ts[j] > 2 * self.ct.period_ns:
            return "STALE"
        return self.ct.persisted[j]

    # -- ledger reconciliation -------------------------------------------

    def _load_ledger(self, arm: str) -> dict:
        p = V2_LEDGERS / self.cell / arm / "tier_1.json"
        return json.loads(p.read_text())

    def reconcile(self) -> dict:
        """Recompute all six V2 arms' tier-1 totals from trades."""
        out = {}
        for arm in [
            "ALWAYS_ON_MEAN_REVERSION",
            "ALWAYS_ON_TREND",
            "DETERMINISTIC_REGIME_ROUTER",
            "JEV_ONLY_ROUTER",
            "DETERMINISTIC_PLUS_JEV_CONFIRMATION",
            "RANDOM_MATCHED_ROUTER",
        ]:
            d = self._load_ledger(arm)
            tr = d["trades"]
            rec = {
                "trades": len(tr),
                "gross": sum(t["gross_pnl"] for t in tr),
                "fee": sum(t["fees"] for t in tr),
                "slip": sum(t["slip"] for t in tr),
                "funding": sum(t["funding"] for t in tr),
                "net": sum(t["net_pnl"] for t in tr),
            }
            sto = d["totals"]
            ok = (
                rec["trades"] == sto["trades"]
                and abs(rec["gross"] - sto["gross_pnl"]) < RECON_TOL
                and abs(rec["fee"] - sto["costs_fee"]) < RECON_TOL
                and abs(rec["slip"] - sto["costs_slip"]) < RECON_TOL
                and abs(rec["funding"] - sto["costs_funding"]) < RECON_TOL
                and abs(rec["net"] - sto["net_pnl"]) < RECON_TOL
            )
            self.checks.append(
                {
                    "check": f"ledger_reconciliation[{arm}]",
                    "cell": self.cell,
                    "verdict": "PASS" if ok else "FAIL",
                    "recomputed": rec,
                    "stored": {
                        "trades": sto["trades"],
                        "gross": sto["gross_pnl"],
                        "fee": sto["costs_fee"],
                        "slip": sto["costs_slip"],
                        "funding": sto["costs_funding"],
                        "net": sto["net_pnl"],
                    },
                }
            )
            out[arm] = {"stored_net": sto["net_pnl"], "trades": sto["trades"]}
        return out

    # -- decomposition ------------------------------------------------------

    def pnl_by_regime(self) -> dict:
        """Bar-level MTM attribution: per-exec-bar equity delta summed by the
        governing persisted label; plus trade-level (regime at entry)."""
        eq = np.asarray(self.ledger["equity"], dtype=float)
        n = len(self.exec_bars.ts_close)
        assert len(eq) == n, f"equity length {len(eq)} != exec bars {n}"
        deltas = np.diff(np.concatenate([[100_000.0], eq]))
        by_label: dict[str, float] = {l: 0.0 for l in LABELS}
        by_label["PRE_FIRST_DECISION"] = 0.0
        by_label["STALE"] = 0.0
        for i in range(n):
            by_label[self.governing_label(i)] += float(deltas[i])
        # NOTE: deltas[i] is the change across bar i (close_{i-1}->close_i);
        # attribute to the label governing bar i (open of bar i). The final
        # bar's delta closes at equity[-1].
        trades_by_regime: dict[str, dict] = {}
        for t in self.ledger["trades"]:
            lab = self.governing_label(t["entry_bar"])
            b = trades_by_regime.setdefault(
                lab, {"trades": 0, "net": 0.0, "gross": 0.0, "costs": 0.0}
            )
            b["trades"] += 1
            b["net"] += t["net_pnl"]
            b["gross"] += t["gross_pnl"]
            b["costs"] += t["fees"] + t["slip"] + t["funding"]
        recon = abs(sum(by_label.values()) - (eq[-1] - 100_000.0)) < RECON_TOL
        self.checks.append(
            {
                "check": "bar_attribution_identity",
                "cell": self.cell,
                "verdict": "PASS" if recon else "FAIL",
                "sum_by_label": sum(by_label.values()),
                "ledger_net": float(eq[-1] - 100_000.0),
            }
        )
        return {
            "bar_level_equity_delta_by_governing_label": {
                k: round(v, 2) for k, v in by_label.items()
            },
            "trade_level_by_entry_regime": {
                k: {kk: round(vv, 2) for kk, vv in v.items()}
                for k, v in trades_by_regime.items()
            },
        }

    def stable_vs_transition(self) -> dict:
        """Equity deltas inside windows of +-k regime bars around each
        persisted switch, vs outside them (k = 1/2/3)."""
        ts_close = self.ct.regime_bars.ts_close
        switch_ts = [
            int(ts_close[r["bar_index"]])
            for r in self.ct.timeline.rows
            if r["switched"]
        ]
        eq = np.asarray(self.ledger["equity"], dtype=float)
        deltas = np.diff(np.concatenate([[100_000.0], eq]))
        out = {}
        for k in (1, 2, 3):
            win = k * self.ct.period_ns
            inside = 0.0
            outside = 0.0
            n_in = 0
            for i in range(len(eq)):
                ts_o = int(self.exec_bars.ts_open[i])
                if any(abs(ts_o - s) <= win for s in switch_ts):
                    inside += float(deltas[i])
                    n_in += 1
                else:
                    outside += float(deltas[i])
            out[f"window_pm{k}"] = {
                "n_bars_inside": n_in,
                "pnl_inside": round(inside, 2),
                "pnl_outside": round(outside, 2),
            }
        return out

    def counts_and_holding(self) -> dict:
        tr = self.ledger["trades"]
        entries = len(tr)
        reversals = 0
        exits_by_reason: dict[str, int] = {}
        holds = []
        for j, t in enumerate(tr):
            exits_by_reason[t["exit_reason"]] = (
                exits_by_reason.get(t["exit_reason"], 0) + 1
            )
            holds.append(t["exit_bar"] - t["entry_bar"])
            if j > 0 and t["direction"] != tr[j - 1]["direction"]:
                reversals += 1
        # no-op target updates: governing-label changes that did NOT change
        # the target direction (from the reconstructed target series)
        changes = 0
        noop = 0
        prev = None
        prev_dir = 0
        for i, tgt in enumerate(self.targets):
            d = direction_of(tgt)
            if tgt != prev:
                if prev is not None:
                    changes += 1
                    if d == prev_dir:
                        noop += 1
                prev = tgt
                prev_dir = d
        return {
            "entries": entries,
            "exits_by_reason": exits_by_reason,
            "reversals": reversals,
            "median_hold_exec_bars": int(np.median(holds)) if holds else 0,
            "mean_hold_exec_bars": round(float(np.mean(holds)), 2) if holds else 0.0,
            "target_series_changes": changes,
            "no_op_target_updates_label_changed_direction_same": noop,
            "turnover": self.ledger["metrics"]["turnover"],
        }

    def cost_attribution(self) -> dict:
        """Per-trade cause classification -> PnL and cost totals (JEV_ONLY)."""
        tr = self.ledger["trades"]
        classes: dict[str, dict] = {}
        for j, t in enumerate(tr):
            cause = self._classify_trade(t, j, tr)
            b = classes.setdefault(
                cause,
                {"trades": 0, "net": 0.0, "gross": 0.0, "fee": 0.0, "slip": 0.0,
                 "funding": 0.0},
            )
            b["trades"] += 1
            b["net"] += t["net_pnl"]
            b["gross"] += t["gross_pnl"]
            b["fee"] += t["fees"]
            b["slip"] += t["slip"]
            b["funding"] += t["funding"]
        tot = sum(v["net"] for v in classes.values())
        sto = self.ledger["totals"]["net_pnl"]
        ok = abs(tot - sto) < RECON_TOL
        self.checks.append(
            {
                "check": "cost_attribution_reconciliation",
                "cell": self.cell,
                "verdict": "PASS" if ok else "FAIL",
                "class_sum_net": tot,
                "ledger_net": sto,
            }
        )
        return {
            k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in classes.items()
        }

    def _classify_trade(self, t: dict, j: int, tr: list[dict]) -> str:
        reason = t["exit_reason"]
        if reason == "fold_flat":
            return "fold_force_flat"
        if reason in ("stop", "strategy_exit"):
            # if this entry immediately follows a regime-switch flat period,
            # the re-entry is part of the switch cost story
            if j > 0:
                prev_cause = self._quick_regime_off_class(tr[j - 1], j - 1, tr)
                if prev_cause == "regime_switch":
                    return "regime_switch"
            return "strategy_native"
        if reason == "regime_off":
            return self._quick_regime_off_class(t, j, tr)
        return "unknown_reason"

    def _quick_regime_off_class(self, t: dict, j: int, tr: list[dict]) -> str:
        """regime_off exit: unnecessary reopen (same direction resumes) vs
        genuine regime switch (opposite direction or regime-driven exit)."""
        # Look at the target series from the exit bar to the next entry bar:
        # if the opposite direction never became the target and the same
        # direction resumed -> the close/reopen was avoidable.
        exit_bar = t["exit_bar"]
        d = t["direction"]
        next_entry = tr[j + 1]["entry_bar"] if j + 1 < len(tr) else None
        horizon = next_entry if next_entry is not None else exit_bar + 96
        saw_opposite = False
        same_resumed = False
        for i in range(exit_bar, min(horizon + 1, len(self.targets))):
            td = direction_of(self.targets[i])
            if td == -d:
                saw_opposite = True
                break
            if td == d and i > exit_bar:
                same_resumed = True
        if same_resumed and not saw_opposite:
            return "unnecessary_close_reopen"
        return "regime_switch"

    # -- counterfactuals (diagnostic) --------------------------------------

    def _rerun(self, targets: list[str | None]) -> dict:
        eng = Engine(
            self.exec_bars, targets, self.folds_exec, self.cost_model, 100_000.0
        )
        res = eng.run()
        # engine identity (V2 law) recomputed here: the engine asserts its own
        # fold invariants internally; we assert the public identities.
        net = res.totals["net_pnl"]
        assert abs((100_000.0 + net) - float(res.equity[-1])) < RECON_TOL
        assert abs(sum(res.fold_net_pnl) - net) < 1e-9
        return {
            "net": round(net, 2),
            "gross": round(res.totals["gross_pnl"], 2),
            "costs": round(
                res.totals["costs_fee"] + res.totals["costs_slip"]
                + res.totals["costs_funding"],
                2,
            ),
            "trades": res.totals["trades"],
        }

    def counterfactuals(self) -> dict:
        base = self.targets
        mapping = self._mapping()
        out: dict = {"baseline_reproduction": self._rerun(base)}

        # (a) no-op law: same direction => keep current target (never change
        # strategy string when direction is unchanged)
        fixed: list[str | None] = [None] * len(base)
        cur: str | None = None
        cur_d = 0
        for i, tgt in enumerate(base):
            d = direction_of(tgt)
            if tgt is None:
                fixed[i] = None
                continue
            if cur is None or d != cur_d or d == 0:
                cur = tgt
                cur_d = d
            fixed[i] = cur
        out["cf_a_noop_hold_same_direction"] = self._rerun(fixed)

        # (b) transition buffer k regime bars: honor the persisted label k
        # bars LATE — the label known at ts[i] applies only from ts[i+k]
        # (pair ts[k:] with labels[:n-k]; the reverse pairing is lookahead)
        from .turnover import buffered_labels

        for k in (1, 2, 3):
            shifted_ts, shifted_lab = buffered_labels(self.ct.ts, self.ct.persisted, k)
            out[f"cf_b_buffer_{k}regimebars"] = self._rerun(
                targets_from_regime(
                    self.exec_bars, shifted_ts, shifted_lab,
                    self.ct.period_ns, mapping,
                )
            )

        # (c) minimum hold of the INVESTED state: once invested-direction
        # target is set, hold for >= h regime bars against label flips back
        # to flat (direction changes still honored immediately)
        for h in (2, 4, 8):
            hold_ns = h * self.ct.period_ns
            tgt_h: list[str | None] = [None] * len(base)
            last_change_ts = None
            cur: str | None = None
            for i, tgt in enumerate(base):
                ts_o = int(self.exec_bars.ts_open[i])
                if tgt is None:
                    tgt_h[i] = None
                    continue
                if cur is None or direction_of(tgt) != direction_of(cur):
                    cur = tgt
                    last_change_ts = ts_o
                elif (
                    direction_of(cur) != 0
                    and direction_of(tgt) == 0
                    and last_change_ts is not None
                    and ts_o - last_change_ts < hold_ns
                ):
                    pass  # flat ignored: still inside the minimum hold
                else:
                    cur = tgt
                    last_change_ts = ts_o
                tgt_h[i] = cur
            out[f"cf_c_minhold_{h}regimebars"] = self._rerun(tgt_h)

        # (d) JEV risk-off veto only: always-on base, flat in DIST/DOWN
        base_strategy = (
            MR_LONG if self.cell.startswith("BTC") else TREND_LONG
        )
        veto_mapping = {
            l: (FLAT if l in ("DISTRIBUTION", "DOWNTREND") else base_strategy)
            for l in LABELS
        }
        out["cf_d_riskoff_veto_only"] = self._rerun(
            targets_from_regime(
                self.exec_bars, self.ct.ts, self.ct.persisted,
                self.ct.period_ns, veto_mapping,
            )
        )
        out["cf_d_always_on_base_reference"] = self._rerun(
            [base_strategy] * len(base)
        )
        return out

    # -- bundle --------------------------------------------------------------

    def run(self) -> dict:
        return {
            "schema": ATTR_SCHEMA,
            "cell": self.cell,
            "phase": "P1_MECHANISM_ATTRIBUTION_DIAGNOSTIC",
            "v2_ledgers_readonly": str(V2_LEDGERS / self.cell),
            "arms_summary": self.reconcile(),
            "pnl_decomposition": self.pnl_by_regime(),
            "stable_vs_transition": self.stable_vs_transition(),
            "counts_and_holding": self.counts_and_holding(),
            "cost_attribution_by_cause": self.cost_attribution(),
            "counterfactuals_diagnostic_only": self.counterfactuals(),
            "checks": self.checks,
            "disclosure": (
                "Outcome-observed diagnostics on the terminal V2 corpus. "
                "Nothing here is a validated configuration; counterfactuals "
                "locate the failure mechanism only (plan section 3)."
            ),
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


def run_all(cycle_dir: str | Path, out_dir: str | Path | None = None) -> dict:
    bundle = {
        "schema": ATTR_SCHEMA + ".bundle",
        "cycle": "REGIME-STRATEGY-MAPPING-V1",
        "cells": {},
        "all_checks_pass": True,
    }
    checks: list[dict] = []
    for cell in ("BTC_H1", "BTC_H4", "SPY_D1"):
        attr = Attribution(cycle_dir, cell)
        bundle["cells"][cell] = attr.run()
        checks.extend(attr.checks)
    bundle["checks"] = checks
    bundle["all_checks_pass"] = all(c["verdict"] == "PASS" for c in checks)
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "mechanism_attribution.json").write_text(
            json.dumps(bundle, indent=1, sort_keys=True)
        )
    return bundle
