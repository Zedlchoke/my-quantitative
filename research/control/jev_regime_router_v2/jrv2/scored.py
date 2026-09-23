"""JRV2 scored driver — the 18 frozen scored cells (3 cells x 6 arms).

Runs ONLY under the scored-phase GO authority (owner phrase-gated at STOP-2;
see run.cmd_backtest). Uses CACHED Jev decisions exclusively — zero provider
calls. Cost tiers 1.0x/1.5x/2.0x per the frozen cost contract (fee+slip
multiplied; funding rate constant). Atomic: one process computes every
cell x arm x tier and writes outputs only on full success; any failure
raises and leaves no partial summary (trial accounting stays honest).

Trial accounting: each (cell, arm) at BASE tier = one scored cell (18/18).
Stress tiers are diagnostics of the same scored cell. Nothing is tuned:
folds/costs/mapping/thresholds are frozen and digest-asserted at start.
"""
from __future__ import annotations

import json
from dataclasses import asdict
import pathlib
from datetime import datetime, timezone

import numpy as np

from .arms import (
    AssetContext,
    run_always_on_mr,
    run_always_on_trend,
    run_buy_hold,
    run_confirmation_arm,
    run_deterministic_router,
    run_jev_only_router,
    run_random_matched,
)
from .questionio import CacheProvider, DecisionStore, Timeline, sequential_timeline
from .run import build_context  # noqa: F401  (reuse: mapping/folds/costs/PPP law)

ARMS = [
    "ALWAYS_ON_TREND",
    "ALWAYS_ON_MEAN_REVERSION",
    "DETERMINISTIC_REGIME_ROUTER",
    "JEV_ONLY_ROUTER",
    "DETERMINISTIC_PLUS_JEV_CONFIRMATION",
    "RANDOM_MATCHED_ROUTER",
]
TIERS = [1.0, 1.5, 2.0]


def _engine_identity_ok(res, initial_equity: float) -> tuple[bool, float]:
    """equity_end == initial + gross - fee - slip - funding (net over trades)
    AND totals arithmetic identity net == gross - costs."""
    t = res.totals
    eq_delta = (initial_equity + t["net_pnl"]) - float(res.equity[-1])
    net_identity = t["net_pnl"] - (t["gross_pnl"] - t["costs_fee"] - t["costs_slip"] - t["costs_funding"])
    ok = abs(eq_delta) < 1e-6 and abs(net_identity) < 1e-9
    return ok, max(abs(eq_delta), abs(net_identity))


def _fold_reconciliation_ok(res) -> tuple[bool, float]:
    d = float(sum(res.fold_net_pnl)) - float(res.totals["net_pnl"])
    return abs(d) < 1e-9, d


def _persist_result(out_dir: pathlib.Path, arm: str, tier: float, res, m: dict, extra: dict | None = None) -> dict:
    tier_tag = {1.0: "tier_1", 1.5: "tier_1p5", 2.0: "tier_2"}[tier]
    rec = {
        "schema": "jrv2_scored_cell@1",
        "arm": arm,
        "cost_tier": tier,
        "metrics": m,
        "totals": dict(res.totals),
        "fold_net_pnl": list(res.fold_net_pnl),
        "fold_return_series": res.fold_return_series,
        "engine_identity": _engine_identity_ok(res, 100_000.0),
        "fold_reconciliation": _fold_reconciliation_ok(res),
        "trades": [asdict(tr) for tr in res.trades],
        "equity": [float(x) for x in res.equity],
        "extra": extra or {},
    }
    d = out_dir / arm
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{tier_tag}.json").write_text(json.dumps(rec, indent=1, sort_keys=True, default=str) + "\n")
    return rec


def run_scored(fz, cells: list[str], out_root: pathlib.Path) -> dict:
    from .run import _load_cell_full, CYCLE_ID  # noqa: F401
    from .freezes import Freezes  # noqa: F401
    from .features import RegimeFeatures
    from .run import build_context as _bc

    fz.assert_mapping_digest()
    pinned = fz.model_pin.get("pinned_model")
    if not pinned:
        raise SystemExit("BLOCKED_MODEL_PIN: scored run requires the G0-frozen pin")

    out_root.mkdir(parents=True, exist_ok=True)
    summary: dict = {
        "schema": "jrv2_scored_summary@1",
        "cycle": "JEV-REGIME-ROUTER-V2",
        "started_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cells": {},
        "trial_accounting": {"planned_cells": len(cells) * len(ARMS), "observed_cells": 0},
    }

    for cell in cells:
        exec_bars, regime_bars, period, _ = _load_cell_full(fz, cell)
        feats = RegimeFeatures(regime_bars)
        dec_path = out_root.parent / "replay" / cell / f"decisions_{cell}.jsonl"
        store = DecisionStore.load(dec_path)
        timeline = sequential_timeline(
            cell, fz, regime_bars, feats, CacheProvider(store),
            pinned_model=pinned, requested_model=pinned, strict=True,
        )
        cell_dir = out_root / cell
        cell_summary: dict = {"timeline_stats": timeline.stats(), "arms": {}, "buy_hold_reference": None}
        params = fz.persistence_params()

        # buy-hold reference (metric only) at base tier
        ctx_ref = _bc(fz, cell, 1.0)
        _, m_ref = run_buy_hold(ctx_ref)
        cell_summary["buy_hold_reference"] = {
            k: m_ref[k] for k in ("net_pnl", "total_return", "cagr", "sharpe", "max_drawdown")
        }

        for tier in TIERS:
            ctx = _bc(fz, cell, tier)
            cell_summary.setdefault("tiers", {})[str(tier)] = {}
            for arm, runner in (
                ("ALWAYS_ON_TREND", lambda c: run_always_on_trend(c)),
                ("ALWAYS_ON_MEAN_REVERSION", lambda c: run_always_on_mr(c)),
            ):
                res, m = runner(ctx)
                _persist_result(cell_dir, arm, tier, res, m)
                cell_summary["tiers"][str(tier)][arm] = {"net_pnl": m["net_pnl"]}
            res, m, _ = run_deterministic_router(ctx, regime_bars, params)
            _persist_result(cell_dir, "DETERMINISTIC_REGIME_ROUTER", tier, res, m)
            cell_summary["tiers"][str(tier)]["DETERMINISTIC_REGIME_ROUTER"] = {"net_pnl": m["net_pnl"]}
            res, m, _t = run_jev_only_router(ctx, timeline)
            rec = _persist_result(cell_dir, "JEV_ONLY_ROUTER", tier, res, m)
            cell_summary["tiers"][str(tier)]["JEV_ONLY_ROUTER"] = {"net_pnl": m["net_pnl"]}
            res, m, _tg, (det, jev) = run_confirmation_arm(ctx, regime_bars, timeline, params)
            agree = sum(1 for a, b in zip(det, jev) if a == b)
            extra = {"det_jev_agreement_share": round(agree / max(len(det), 1), 4)}
            _persist_result(cell_dir, "DETERMINISTIC_PLUS_JEV_CONFIRMATION", tier, res, m, extra)
            cell_summary["tiers"][str(tier)]["DETERMINISTIC_PLUS_JEV_CONFIRMATION"] = {"net_pnl": m["net_pnl"]}
            rnd = run_random_matched(ctx, timeline)
            head = next(r for r in rnd["seeds"] if r["seed"] == rnd["headline_seed"])
            res_r, m_r = _route_for_random(ctx, timeline, rnd["headline_seed"])
            extra_r = {
                "headline_seed": rnd["headline_seed"],
                "median_net_pnl": rnd["median_net_pnl"],
                "null_invalid_flag": rnd["null_invalid_flag"],
                "q11_jev_only": rnd["q11_jev_only"],
                "seed_nets": [r["net_pnl"] for r in rnd["seeds"]],
            }
            _persist_result(cell_dir, "RANDOM_MATCHED_ROUTER", tier, res_r, m_r, extra_r)
            cell_summary["tiers"][str(tier)]["RANDOM_MATCHED_ROUTER"] = {
                "net_pnl": m_r["net_pnl"], "median": rnd["median_net_pnl"],
                "null_invalid": rnd["null_invalid_flag"],
            }

        # base-tier full metrics for the summary
        base = {}
        for arm in ARMS:
            rec = json.loads((cell_dir / arm / "tier_1.json").read_text())
            m = rec["metrics"]
            base[arm] = {k: m.get(k) for k in (
                "net_pnl", "gross_pnl", "costs_fee", "costs_slip", "costs_funding",
                "total_return", "cagr", "sharpe", "sortino", "max_drawdown",
                "profit_factor", "expectancy_per_trade", "trades", "win_rate",
                "turnover", "time_in_market", "regime_switches",
                "unknown_share_effective", "concentration_top_fold_profit_share",
                "skipped_trade_pnl_fraction", "fold_by_fold_net_pnl")}
            base[arm]["engine_identity_ok"] = rec["engine_identity"][0]
            base[arm]["fold_reconciliation_ok"] = rec["fold_reconciliation"][0]
        cell_summary["arms"] = base
        summary["cells"][cell] = cell_summary
        summary["trial_accounting"]["observed_cells"] += len(ARMS)

    # margin-to-fail at base tier, per cell: |delta net| vs arms B/C/D/F
    for cell, cs in summary["cells"].items():
        arms = cs["arms"]
        jev = arms["JEV_ONLY_ROUTER"]["net_pnl"]
        conf = arms["DETERMINISTIC_PLUS_JEV_CONFIRMATION"]["net_pnl"]
        cs["margins"] = {
            "JEV_vs_ALWAYS_TREND": jev - arms["ALWAYS_ON_TREND"]["net_pnl"],
            "JEV_vs_ALWAYS_MR": jev - arms["ALWAYS_ON_MEAN_REVERSION"]["net_pnl"],
            "JEV_vs_DETERMINISTIC": jev - arms["DETERMINISTIC_REGIME_ROUTER"]["net_pnl"],
            "JEV_vs_RANDOM_MEDIAN": jev - arms["RANDOM_MATCHED_ROUTER"]["net_pnl"],
            "CONFIRM_vs_DETERMINISTIC": conf - arms["DETERMINISTIC_REGIME_ROUTER"]["net_pnl"],
        }

    summary["finished_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (out_root / "scored_summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "SCORED_RUN_COMPLETE",
        "observed_cells": summary["trial_accounting"]["observed_cells"],
        "summary_path": str(out_root / "scored_summary.json"),
    }))
    return summary


def _route_for_random(ctx: AssetContext, timeline: Timeline, seed: int):
    from .arms import random_matched_paths, _route_and_backtest

    invested = ctx.invested_labels()
    paths = random_matched_paths(timeline.persisted, invested)
    entry = next(p for p in paths if p["seed"] == seed)
    return _route_and_backtest(ctx, timeline.ts, entry["labels"])
