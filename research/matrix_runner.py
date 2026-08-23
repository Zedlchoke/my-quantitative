"""Resumable walk-forward matrix runner for the frozen strategy inventory
(owner: A2).

Generalises ``research.baseline_wf.run_walkforward`` to ANY ``strategy_type``
and executes the declared strategy x symbol matrix cell by cell:

* chronological folds over the declared window (default S0: 2025-08-21 ->
  2026-08-21 per contracts/README.md), warmup strictly OUTSIDE the scored
  window (strategy ``history_days`` when available, else a risk-safe 10 days);
* per-fold post-trade funding audit via ``reports.funding.build_funding_audit``;
* Sprint V2 canonical accounting (PLAN section 8.2): profit factor and gross
  win/loss aggregates are computed at POSITION level from funding-adjusted
  per-position PnL (never from fold net PnL), persisted per cell as
  ``folds[].positions_stats``, a cell-level ``positions_stats``, a
  ``positions_digest`` and a sibling ``<cell>.positions.jsonl`` ledger;
* one JSON artifact per cell containing the frozen ``MatrixCellResult`` fields;
* resumable: an index file (``index.json``) keyed by the cell identity tuple
  ``(strategy_type, symbol, config_sha256, data_snapshot_id, split_policy,
  fee_model, slippage_model, seed)`` lets interrupted matrices reuse completed
  cells instead of rerunning them;
* isolated: a crashing cell becomes a ``PIPELINE_ERROR`` artifact with reason
  ``cell_failed_exception`` and the matrix continues (sequential loop with
  per-cell try/except; workers <= 2 per contract budget - execution stays
  sequential by default because each Nautilus engine is memory-heavy).

Base-config mapping (frozen parameters come from each strategy's own YAML; the
mapping NEVER edits YAML files, it only overrides universe/catalog/funding via
``dataclasses.replace``):

=================  =============================================
strategy_type      base research config
=================  =============================================
ema_atr            config/research.yaml
mean_reversion     config/research_mean_reversion.yaml
regime_switch      config/research_regime_switch.yaml
breakout           config/research_breakout_eth.yaml   (*)
reclaim_mr         config/research_baseline_altcoin.yaml
trend_pullback     config/research_baseline_altcoin.yaml
markdown_breakdown config/research_baseline_altcoin.yaml
=================  =============================================

(*) Adaptation vs. the sprint brief: ``config/research_breakout.yaml`` does not
exist in this repo; the ETH breakout config is the only YAML carrying the
frozen ``breakout`` parameter block, so it is used as the breakout base. The
invariant for every row is: the base YAML must contain that strategy_type's
frozen parameter section and pass ``ResearchSettings.validate()``.

Overrides applied on top of every base config:

* ``market.symbols``       -> the declared universe subset for the run
* ``data.catalog_path``    -> ``./catalog_live_crypto``
* ``report.funding_data_path`` -> ``funding_data/scan_2026``

Statuses written per cell (contracts.protocol.CellStatus):

* ``COMPLETED``          pipeline ran end-to-end; factual G3 observations are
                         attached as reason codes (final candidate verdicts
                         remain the validator agent's job)
* ``DATA_INCOMPLETE``    pre-run data gate failed (missing instrument metadata,
                         coverage below the declared window) with reason codes
* ``PIPELINE_ERROR``     cell raised; recorded with ``cell_failed_exception``
* ``REUSED``             existing artifact matched the cell identity on resume

Usage::

    # Tier 0 compatibility smoke (3-day window, single fold):
    python -m research.matrix_runner --tier 0 --matrix-id tier0_smoke \
        --strategies ema_atr --symbols SOLUSDT

    # Tier 1 full Stage A:
    python -m research.matrix_runner --tier 1 --matrix-id stage_a_full
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from contracts.protocol import (
    STAGE_A_MIN_POSITIVE_FOLD_RATIO,
    STAGE_A_MIN_TRADES_PER_SYMBOL,
    CellStatus,
    MatrixCellResult,
    canonical_json,
    position_pnl_stats,
    require_reason,
    sha256_file,
    sha256_text,
)

# --------------------------------------------------------------------------- #
# Frozen inventory + config mapping
# --------------------------------------------------------------------------- #
INVENTORY: tuple[str, ...] = (
    "ema_atr",
    "mean_reversion",
    "regime_switch",
    "breakout",
    "reclaim_mr",
    "trend_pullback",
    "markdown_breakdown",
)

STRATEGY_CONFIG_MAP: dict[str, str] = {
    "ema_atr": "config/research.yaml",
    "mean_reversion": "config/research_mean_reversion.yaml",
    "regime_switch": "config/research_regime_switch.yaml",
    # research_breakout.yaml does not exist; ETH config holds the frozen
    # breakout block (see module docstring).
    "breakout": "config/research_breakout_eth.yaml",
    "reclaim_mr": "config/research_baseline_altcoin.yaml",
    "trend_pullback": "config/research_baseline_altcoin.yaml",
    "markdown_breakdown": "config/research_baseline_altcoin.yaml",
}

MATRIX_CATALOG_PATH = "./catalog_live_crypto"
MATRIX_FUNDING_PATH = "funding_data/scan_2026"

# Sprint hypothesis extension (iteration-1): A4's pre-registered strategy.
# Its provenance config is the frozen candidate.yaml, not a research YAML.
VOLCOMP_STRATEGY_TYPE = "vol_compression_breakout"
VOLCOMP_HYPOTHESIS_ID = "H-VOLCOMP-BRKOUT-v1"
VOLCOMP_HYPOTHESIS_CONFIG = f"research/hypotheses/{VOLCOMP_HYPOTHESIS_ID}/candidate.yaml"
FUNDCROWD_STRATEGY_TYPE = "funding_crowding"
FUNDCROWD_HYPOTHESIS_ID = "H-FUNDCROWD-MR-v2"
FUNDCROWD_HYPOTHESIS_CONFIG = f"research/hypotheses/{FUNDCROWD_HYPOTHESIS_ID}/candidate.yaml"
ALL_STRATEGIES: tuple[str, ...] = INVENTORY + (VOLCOMP_STRATEGY_TYPE, FUNDCROWD_STRATEGY_TYPE)
HYPOTHESIS_CONFIG_BY_TYPE = {
    VOLCOMP_STRATEGY_TYPE: VOLCOMP_HYPOTHESIS_CONFIG,
    FUNDCROWD_STRATEGY_TYPE: FUNDCROWD_HYPOTHESIS_CONFIG,
}
HYPOTHESIS_TYPES: tuple[str, ...] = (VOLCOMP_STRATEGY_TYPE, FUNDCROWD_STRATEGY_TYPE)

# Declared S0 window (contracts/README.md).
DECLARED_S0_START = pd.Timestamp("2025-08-21T00:00:00Z")
DECLARED_S0_END = pd.Timestamp("2026-08-21T00:00:00Z")

TIER0_FOLDS = 1
TIER0_SMOKE_DAYS = 3
#: Tier 0 is a compatibility smoke only: cap warmup so the tiny window runs fast.
TIER0_WARMUP_DAYS = 10
DEFAULT_WARMUP_DAYS = 10  # risk-safe fallback when history_days unavailable
DEFAULT_FOLDS = 3

BAR_DAY = 96  # 15m bars per day


# --------------------------------------------------------------------------- #
# Settings assembly
# --------------------------------------------------------------------------- #
def build_cell_settings(
    strategy_type: str,
    symbols: tuple[str, ...],
    *,
    catalog_path: str = MATRIX_CATALOG_PATH,
    funding_path: str = MATRIX_FUNDING_PATH,
):
    """Load the strategy's base research config and override universe/data.

    No YAML is modified; all overrides happen through ``dataclasses.replace``.
    """
    if strategy_type not in ALL_STRATEGIES:
        raise ValueError(f"Unknown strategy_type {strategy_type!r}; inventory={ALL_STRATEGIES}")
    from config.settings import load_research_config

    if strategy_type in HYPOTHESIS_TYPES:
        # Hypothesis cell: provenance config = frozen candidate.yaml; base
        # sections (market/risk/strategy/backtest) come from the altcoin
        # baseline YAML. strategy_type stays the file's own so validate()
        # passes; the engine call receives the hypothesis type explicitly.
        settings = load_research_config(STRATEGY_CONFIG_MAP["reclaim_mr"])
        updated = dataclasses.replace(
            settings,
            market=dataclasses.replace(settings.market, symbols=symbols),
            data=dataclasses.replace(settings.data, catalog_path=catalog_path),
            report=dataclasses.replace(settings.report, funding_data_path=funding_path),
        )
        updated.validate()
        return HYPOTHESIS_CONFIG_BY_TYPE[strategy_type], updated

    config_path = STRATEGY_CONFIG_MAP[strategy_type]
    settings = load_research_config(config_path)
    updated = dataclasses.replace(
        settings,
        strategy_type=strategy_type,
        market=dataclasses.replace(settings.market, symbols=symbols),
        data=dataclasses.replace(settings.data, catalog_path=catalog_path),
        report=dataclasses.replace(settings.report, funding_data_path=funding_path),
    )
    updated.validate()
    return config_path, updated


def warmup_days_for(settings, strategy_type: str, *, tier0: bool = False) -> int:
    """Warmup days outside the scored window (history_days or safe default)."""
    if tier0:
        return TIER0_WARMUP_DAYS
    if strategy_type == VOLCOMP_STRATEGY_TYPE:
        from strategy_vol_compression_breakout import VolCompressionBreakoutSettings

        bars = VolCompressionBreakoutSettings().warmup_bars()
        return max(1, -(-bars // BAR_DAY))
    if strategy_type == FUNDCROWD_STRATEGY_TYPE:
        from strategy_funding_crowding_mr import FundingCrowdingMRSettings

        bars = FundingCrowdingMRSettings().warmup_bars()
        return max(1, -(-bars // BAR_DAY))
    baseline = getattr(settings, strategy_type, None)
    days = getattr(baseline, "history_days", None)
    if not days or days <= 0:
        return DEFAULT_WARMUP_DAYS
    return int(days)


def fold_windows(
    start: pd.Timestamp, end: pd.Timestamp, folds: int
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Chronological fold edges over [start, end] (no overlap, no embargo)."""
    if folds < 1 or end <= start:
        raise ValueError("Invalid interval/folds")
    edges = pd.date_range(start=start, end=end, periods=folds + 1)
    return [(edges[i], edges[i + 1]) for i in range(folds)]


# --------------------------------------------------------------------------- #
# Cell plan / identity / resume index
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellPlan:
    strategy_type: str
    symbol: str
    config_path: str
    config_sha256: str
    tier: int
    folds: int
    warmup_days: int
    window_start: pd.Timestamp
    window_end: pd.Timestamp
    split_policy: str
    catalog_path: str
    funding_path: str
    param_variant: str = "base"

    def identity(self, *, fee_model: str, slippage_model: str, seed, snapshot_id: str) -> dict:
        return {
            "strategy_type": self.strategy_type,
            "symbol": self.symbol,
            "param_variant": self.param_variant,
            "config_sha256": self.config_sha256,
            "data_snapshot_id": snapshot_id,
            "split_policy": self.split_policy,
            "fee_model": fee_model,
            "slippage_model": slippage_model,
            "seed": seed,
        }

    def identity_key(self, identity: dict) -> str:
        return canonical_json(identity)


def _split_policy_id(plan: CellPlan) -> str:
    kind = "tier0_smoke" if plan.tier == 0 else f"chrono_wf{plan.folds}fold"
    return (
        f"{kind}_warmup{plan.warmup_days}d_"
        f"{plan.window_start:%Y%m%d}-{plan.window_end:%Y%m%d}"
    )


def make_plan(
    strategy_type: str,
    symbol: str,
    *,
    tier: int,
    folds: int,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
    catalog_path: str = MATRIX_CATALOG_PATH,
    funding_path: str = MATRIX_FUNDING_PATH,
    param_variant: str = "base",
) -> CellPlan:
    config_path, settings = build_cell_settings(
        strategy_type, (symbol,), catalog_path=catalog_path, funding_path=funding_path
    )
    warmup = warmup_days_for(settings, strategy_type, tier0=(tier == 0))
    plan = CellPlan(
        strategy_type=strategy_type,
        symbol=symbol,
        config_path=config_path,
        config_sha256=sha256_file(config_path),
        tier=tier,
        folds=TIER0_FOLDS if tier == 0 else max(1, folds),
        warmup_days=warmup,
        window_start=window_start,
        window_end=window_end,
        split_policy="pending",
        catalog_path=catalog_path,
        funding_path=funding_path,
        param_variant=param_variant,
    )
    return dataclasses.replace(plan, split_policy=_split_policy_id(plan))


def data_snapshot_id(catalog_path: str, symbol: str, plan_window_start: pd.Timestamp,
                     plan_window_end: pd.Timestamp) -> str:
    """Stable data descriptor for the resume identity.

    Deliberately derived from catalog + symbol + declared window (NOT volatile
    file mtimes) so identical declarations reuse artifacts; data freshness
    itself is proven separately by research.data_audit / G0.
    """
    return (
        f"{Path(catalog_path).name}|{symbol}|"
        f"{plan_window_start:%Y%m%d}|{plan_window_end:%Y%m%d}"
    )


def load_index(index_path: Path) -> dict:
    if index_path.exists():
        return json.loads(index_path.read_text(encoding="utf-8"))
    return {"schema_version": 1, "cells": {}}


def save_index(index_path: Path, index: dict) -> None:
    index["updated_at"] = datetime.now(timezone.utc).isoformat()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Walk-forward execution for one cell
# --------------------------------------------------------------------------- #
def _strategy_kwargs(settings) -> dict[str, object]:
    return {
        "mean_reversion": settings.mean_reversion,
        "regime_switch": settings.regime_switch,
        "breakout": settings.breakout,
        "reclaim_mr": settings.reclaim_mr,
        "trend_pullback": settings.trend_pullback,
        "markdown_breakdown": settings.markdown_breakdown,
    }


def _bars_in_range(all_bars: list, start_ns: int, end_ns: int) -> list:
    return [bar for bar in all_bars if start_ns <= bar.ts_event <= end_ns]


# --------------------------------------------------------------------------- #
# Position-level canonical accounting (Sprint V2 section 8.2, owner A3)
# --------------------------------------------------------------------------- #
def _position_stats_from_pnls(pnls: list[float]) -> dict:
    """Canonical position-level stats dict (pure; engine-free).

    Wraps ``contracts.protocol.position_pnl_stats`` so tests and callers get a
    JSON-ready mapping: trades / gross_profit / gross_loss / net_pnl /
    profit_factor / pf_reason.  PF is ``None`` + reason for no-trade and
    no-losing-position sets (never infinity, never auto-PASS).
    """
    stats = position_pnl_stats([float(pnl) for pnl in pnls])
    return {
        "trades": stats.trades,
        "gross_profit": round(stats.gross_profit, 10),
        "gross_loss": round(stats.gross_loss, 10),
        "net_pnl": round(stats.net_pnl, 10),
        "profit_factor": (
            None if stats.profit_factor is None else round(stats.profit_factor, 10)
        ),
        "pf_reason": stats.pf_reason,
    }


_UNAVAILABLE_STATS = {
    "trades": None,
    "gross_profit": None,
    "gross_loss": None,
    "net_pnl": None,
    "profit_factor": None,
}


def _unavailable_stats(reason: str) -> dict:
    return {**_UNAVAILABLE_STATS, "pf_reason": require_reason(reason)}


def _quantity_float(value: object) -> float:
    """Parse engine quantity/price strings like ``'12.5 USDT'`` -> float."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("position accounting requires non-null numeric fields")
    text = str(value).strip()
    if not text:
        raise ValueError("position accounting requires non-empty numeric fields")
    try:
        return float(text.split()[0])
    except ValueError as exc:
        raise ValueError(f"unparsable numeric field {value!r}") from exc


def _optional_float(value: object) -> float | None:
    """Tolerant parse for informational columns (e.g. commissions)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text == "0":
        return None
    try:
        return float(text.split()[0])
    except ValueError:
        return None


def _positions_rows_in_window(adjusted: "pd.DataFrame", w_start, w_end) -> list[dict]:
    """Closed-position rows with funding-adjusted canonical PnL in window.

    One row per closed position whose ``ts_closed`` falls inside the scored
    fold window ``[w_start, w_end]`` (inclusive), sorted by close time.
    """
    has_commission = "commissions" in adjusted.columns
    rows: list[dict] = []
    for _, row in adjusted.iterrows():
        closed = pd.Timestamp(row["ts_closed"])
        if closed.tzinfo is None:
            closed = closed.tz_localize("UTC")
        if not (w_start <= closed <= w_end):
            continue
        opened = pd.Timestamp(row["ts_opened"])
        if opened.tzinfo is None:
            opened = opened.tz_localize("UTC")
        after_funding = float(row["realized_pnl_after_funding"])
        funding_net = float(row.get("funding_net", 0.0) or 0.0)
        rows.append(
            {
                "instrument_id": str(row.get("instrument_id", "")),
                "side": "LONG" if str(row["entry"]).upper() == "BUY" else "SHORT",
                "qty": _quantity_float(row["peak_qty"]),
                "entry_ts": opened.isoformat(),
                "exit_ts": closed.isoformat(),
                "realized_pnl_gross": round(after_funding - funding_net, 10),
                "commission": (
                    _optional_float(row["commissions"]) if has_commission else None
                ),
                "funding_net": round(funding_net, 10),
                "pnl_after_funding": round(after_funding, 10),
            }
        )
    rows.sort(key=lambda item: item["exit_ts"])
    return rows


def _funding_fold_positions(engine, funding_path: str | None, w_start, w_end) -> dict:
    """Funding-audited position accounting restricted to the fold window.

    Returns the legacy fold-metric block (kept for continuity) plus
    ``positions_stats`` computed at POSITION level per Sprint V2 section 8.2
    and the raw closed-position rows for persistence.

    Distinction kept honest: a fold whose engine produced NO closed positions
    gets ``no_trades`` stats (zeros, PF undefined); only a failing/partial
    funding bundle marks ``funding_coverage_insufficient``.
    """
    unavailable = {
        "funding_available": False,
        "reason_codes": ["funding_coverage_insufficient"],
        "trades_after_funding": 0,
        "pnl_after_funding": 0.0,
        "expectancy_after_funding": None,
        "profit_factor_after_funding": None,
        "positions_stats": _unavailable_stats("funding_coverage_insufficient"),
        "positions_rows": [],
    }
    if not funding_path:
        return unavailable
    try:
        from reports.funding import build_funding_audit

        audit = build_funding_audit(engine.trader.generate_positions_report(), funding_path)
    except Exception:  # noqa: BLE001 - missing/partial bundle must not kill the cell
        return unavailable
    adjusted = audit.adjusted_positions
    rows = (
        _positions_rows_in_window(adjusted, w_start, w_end)
        if not adjusted.empty
        else []
    )
    stats = _position_stats_from_pnls([row["pnl_after_funding"] for row in rows])
    total = sum((row["pnl_after_funding"] for row in rows), 0.0)
    return {
        "funding_available": True,
        "reason_codes": [],
        "trades_after_funding": len(rows),
        "pnl_after_funding": round(total, 6),
        "expectancy_after_funding": (
            round(total / len(rows), 6) if rows else None
        ),
        # Continuity note: this is now the POSITION-level PF of the fold
        # (V2 section 8.2); V1 emitted a fold-net-PF here instead.
        "profit_factor_after_funding": stats["profit_factor"],
        "positions_stats": stats,
        "positions_rows": rows,
    }


def _reconcile_positions(folds_payload: list[dict], all_position_rows: list[dict]) -> None:
    """Stop-condition guard: position accounting must reconcile with folds.

    ``sum(position pnls) == sum(fold nets)`` within relative tolerance 1e-9;
    a mismatch raises so the caller records PIPELINE_ERROR (PLAN section 14).
    """
    position_total = sum((row["pnl_after_funding"] for row in all_position_rows), 0.0)
    fold_total = sum(
        (
            fold["positions_stats"]["net_pnl"]
            for fold in folds_payload
            if isinstance(fold["positions_stats"].get("net_pnl"), float)
        ),
        0.0,
    )
    if abs(position_total - fold_total) > 1e-9 * max(1.0, abs(position_total)):
        raise RuntimeError(
            f"positions_reconciliation_failed: positions={position_total!r} "
            f"folds={fold_total!r}"
        )


def execute_cell(plan: CellPlan) -> dict:
    """Run the full walk-forward for one cell and build its artifact payload.

    Raises on any pipeline failure (the caller converts to PIPELINE_ERROR).
    """
    from backtest.engine import run_backtest_for_symbol
    from data.catalog import Catalog
    from research.breakout_wf import _metrics_in_window

    _, settings = build_cell_settings(
        plan.strategy_type,
        (plan.symbol,),
        catalog_path=plan.catalog_path,
        funding_path=plan.funding_path,
    )
    extra_kwargs: dict[str, object] = {}
    if plan.strategy_type == VOLCOMP_STRATEGY_TYPE:
        from strategy_vol_compression_breakout import VolCompressionBreakoutSettings

        grid = VolCompressionBreakoutSettings.parameter_grid()
        if plan.param_variant != "base":
            extra_kwargs["vol_compression"] = grid[int(plan.param_variant[1:])]
        else:
            extra_kwargs["vol_compression"] = grid[0]
    elif plan.strategy_type == FUNDCROWD_STRATEGY_TYPE:
        from strategy_funding_crowding_mr import FundingCrowdingMRSettings

        grid = FundingCrowdingMRSettings.parameter_grid()
        if plan.param_variant != "base":
            extra_kwargs["funding_crowding"] = grid[int(plan.param_variant[1:])]
        else:
            extra_kwargs["funding_crowding"] = grid[0]
    catalog = Catalog(settings.data.catalog_path)
    instrument = catalog.instrument(settings.market.instrument_id(plan.symbol))
    if instrument is None:
        raise FileNotFoundError(
            f"Instrument {settings.market.instrument_id(plan.symbol)} missing "
            f"from {settings.data.catalog_path}"
        )
    all_bars = catalog.bars(settings.market.bar_type(plan.symbol))
    if not all_bars:
        raise FileNotFoundError(f"No bars for {plan.symbol} in {settings.data.catalog_path}")

    data_first = pd.Timestamp(min(bar.ts_event for bar in all_bars), unit="ns", tz="UTC")
    data_last = pd.Timestamp(max(bar.ts_event for bar in all_bars), unit="ns", tz="UTC")
    snapshot_id = data_snapshot_id(
        settings.data.catalog_path, plan.symbol, plan.window_start, plan.window_end
    )

    actual_start = max(plan.window_start, data_first)
    actual_end = min(plan.window_end, data_last)
    windows = fold_windows(actual_start, actual_end, plan.folds)

    folds_payload: list[dict] = []
    reasons: set[str] = set()
    all_position_rows: list[dict] = []
    for index, (w_start, w_end) in enumerate(windows):
        warm_start = w_start - pd.Timedelta(days=plan.warmup_days)
        bars = _bars_in_range(all_bars, int(warm_start.value), int(w_end.value))
        bt_settings = dataclasses.replace(settings.backtest, start=None, end=None)
        run = run_backtest_for_symbol(
            settings.market,
            settings.risk,
            settings.strategy,
            bt_settings,
            catalog,
            symbol=plan.symbol,
            strategy_type=plan.strategy_type,
            **_strategy_kwargs(settings),
            **extra_kwargs,
            trader_id=f"MATRIX-{plan.strategy_type}",
            log_level="OFF",
            instrument=instrument,
            bars=bars,
        )
        try:
            pnl, exp, pf, wr, trades = _metrics_in_window(
                run.engine, w_start.isoformat(), w_end.isoformat()
            )
            funding = _funding_fold_positions(run.engine, plan.funding_path, w_start, w_end)
        finally:
            run.engine.dispose()

        def _clean(value: float) -> float | None:
            if value != value:  # NaN sentinel from _metrics_in_window
                return None
            return round(float(value), 6)

        position_rows = funding.pop("positions_rows")
        all_position_rows.extend(position_rows)
        folds_payload.append(
            {
                "fold": index,
                "start_utc": w_start.isoformat(),
                "end_utc": w_end.isoformat(),
                "warmup_days": plan.warmup_days,
                "bars_incl_warmup": len(bars),
                "scored_bars": max(0, len(_bars_in_range(all_bars, int(w_start.value), int(w_end.value)))),
                "trades": trades,
                "pnl": _clean(pnl),
                "expectancy": _clean(exp),
                "profit_factor": _clean(pf),
                "win_rate": _clean(wr),
                "positions_stats": funding["positions_stats"],
                **funding,
            }
        )
        reasons.update(funding.get("reason_codes") or [])

    _reconcile_positions(folds_payload, all_position_rows)

    cell_stats = _position_stats_from_pnls(
        [row["pnl_after_funding"] for row in all_position_rows]
    ) if all_position_rows else _position_stats_from_pnls([])
    positions_digest = sha256_text(canonical_json(all_position_rows))
    total_trades = sum(int(fold["trades"]) for fold in folds_payload)
    positive_folds = sum(1 for fold in folds_payload if (fold["expectancy"] or 0) > 0)
    total_pnl = sum(fold["pnl"] or 0.0 for fold in folds_payload)
    funded = [
        fold
        for fold in folds_payload
        if fold.get("trades_after_funding")
    ]
    exp_after_total = sum(fold["pnl_after_funding"] for fold in funded)
    trades_after_total = sum(fold["trades_after_funding"] for fold in funded)
    exp_after = exp_after_total / trades_after_total if trades_after_total else None

    # Factual observations only (final verdicts belong to the validator agent).
    # Tier 0 is a compatibility smoke: never scored, no edge observations.
    observations: set[str] = set(reasons)
    if plan.tier == 0:
        observations = set()
        return {
            "window_actual": {"start_utc": actual_start.isoformat(), "end_utc": actual_end.isoformat()},
            "data_bounds": {"first_bar_utc": data_first.isoformat(), "last_bar_utc": data_last.isoformat()},
            "snapshot_id": snapshot_id,
            "total_trades": total_trades,
            "positive_folds": positive_folds,
            "total_pnl": round(total_pnl, 6),
            "pnl_after_funding": round(exp_after_total, 6),
            "expectancy_after_funding": round(exp_after, 6) if exp_after is not None else None,
            "positions_stats": cell_stats,
            "positions_digest": positions_digest,
            "positions_rows": all_position_rows,
            "observations": [],
            "folds": folds_payload,
        }
    if not all_position_rows:
        observations.add(require_reason("no_trades"))
    if total_trades < STAGE_A_MIN_TRADES_PER_SYMBOL:
        observations.add("trades_below_min")
    if trades_after_total and exp_after is not None and exp_after <= 0:
        observations.add("exp_nonpositive")
    if total_trades and positive_folds / max(1, plan.folds) < STAGE_A_MIN_POSITIVE_FOLD_RATIO:
        observations.add("positive_folds_ratio_low")

    return {
        "window_actual": {"start_utc": actual_start.isoformat(), "end_utc": actual_end.isoformat()},
        "data_bounds": {"first_bar_utc": data_first.isoformat(), "last_bar_utc": data_last.isoformat()},
        "snapshot_id": snapshot_id,
        "total_trades": total_trades,
        "positive_folds": positive_folds,
        "total_pnl": round(total_pnl, 6),
        "pnl_after_funding": round(exp_after_total, 6),
        "expectancy_after_funding": round(exp_after, 6) if exp_after is not None else None,
        "positions_stats": cell_stats,
        "positions_digest": positions_digest,
        "positions_rows": all_position_rows,
        "observations": sorted(observations),
        "folds": folds_payload,
    }


# --------------------------------------------------------------------------- #
# Matrix driver
# --------------------------------------------------------------------------- #
def run_matrix(
    *,
    matrix_id: str,
    tier: int,
    strategies: list[str],
    symbols: list[str],
    output_root: str | Path = "results/matrix",
    folds: int = DEFAULT_FOLDS,
    window_start: pd.Timestamp | None = None,
    window_end: pd.Timestamp | None = None,
    limit_cells: int | None = None,
) -> dict:
    """Execute (or resume) the declared matrix; returns the run report."""
    out_dir = Path(output_root) / matrix_id
    cells_dir = out_dir / "cells"
    cells_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.json"
    index = load_index(index_path)

    if window_start is None:
        window_start = DECLARED_S0_START
    if window_end is None:
        window_end = DECLARED_S0_END

    plans: list[CellPlan] = []
    for strategy_type in strategies:
        if strategy_type in HYPOTHESIS_TYPES:
            module = {
                VOLCOMP_STRATEGY_TYPE: "strategy_vol_compression_breakout",
                FUNDCROWD_STRATEGY_TYPE: "strategy_funding_crowding_mr",
            }[strategy_type]
            settings_cls = {
                VOLCOMP_STRATEGY_TYPE: "VolCompressionBreakoutSettings",
                FUNDCROWD_STRATEGY_TYPE: "FundingCrowdingMRSettings",
            }[strategy_type]
            import importlib

            grid_len = len(
                getattr(importlib.import_module(module), settings_cls).parameter_grid()
            )
            variants = tuple(f"v{i}" for i in range(grid_len))
        else:
            variants = ("base",)
        for symbol in symbols:
            for variant in variants:
                if tier == 0:
                    # Smoke: last few days inside the declared window.
                    start = window_end - pd.Timedelta(days=TIER0_SMOKE_DAYS)
                    plan = make_plan(
                        strategy_type,
                        symbol,
                        tier=0,
                        folds=TIER0_FOLDS,
                        window_start=start,
                        window_end=window_end,
                        param_variant=variant,
                    )
                else:
                    plan = make_plan(
                        strategy_type,
                        symbol,
                        tier=1,
                        folds=folds,
                        window_start=window_start,
                        window_end=window_end,
                        param_variant=variant,
                    )
                plans.append(plan)
    if limit_cells:
        plans = plans[:limit_cells]

    experiment_id = f"EXP-{datetime.now(timezone.utc):%Y%m%d}-{datetime.now(timezone.utc):%H%M}"

    def identity_for(plan: CellPlan) -> tuple[dict, object]:
        _, settings = build_cell_settings(
            plan.strategy_type,
            (plan.symbol,),
            catalog_path=plan.catalog_path,
            funding_path=plan.funding_path,
        )
        bt = settings.backtest
        identity = plan.identity(
            fee_model=str(bt.fee_model),
            slippage_model=str(bt.fill_model),
            seed=bt.random_seed,
            snapshot_id=data_snapshot_id(
                plan.catalog_path, plan.symbol, plan.window_start, plan.window_end
            ),
        )
        return identity, bt

    results: list[dict] = []
    reused = 0
    completed = 0
    errors = 0
    for plan in plans:
        artifact_rel = f"cells/{plan.strategy_type}__{plan.symbol}__{plan.param_variant}.json"
        artifact_path = out_dir / artifact_rel

        # Resume check: same identity + existing artifact => REUSED (skip rerun).
        identity, bt = identity_for(plan)
        key = plan.identity_key(identity)
        entry = index["cells"].get(key)
        if entry and entry.get("status") == CellStatus.COMPLETED.value and Path(
            entry.get("artifact_path", "")
        ).exists():
            results.append({"cell": artifact_rel, "status": CellStatus.REUSED.value})
            reused += 1
            continue

        try:
            payload = execute_cell(plan)
            status = CellStatus.COMPLETED
            cell_result = MatrixCellResult(
                experiment_id=experiment_id,
                strategy_type=plan.strategy_type,
                symbol=plan.symbol,
                status=status,
                artifact_path=str(artifact_path),
                reason_codes=tuple(payload["observations"]),
                config_sha256=plan.config_sha256,
                data_snapshot_id=identity["data_snapshot_id"],
                split_policy=plan.split_policy,
                folds_completed=len(payload["folds"]),
            )
            # Per-cell closed-position ledger (Sprint V2 section 13): one JSON
            # object per position, funding-adjusted canonical PnL included.
            position_rows = payload.pop("positions_rows")
            positions_path = artifact_path.with_name(artifact_path.stem + ".positions.jsonl")
            positions_path.write_text(
                "".join(json.dumps(row) + "\n" for row in position_rows),
                encoding="utf-8",
            )
            document = {
                "schema_version": 1,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "tier": plan.tier,
                "identity": identity,
                "cell_result": cell_result.to_dict(),
                "plan": {
                    "config_path": plan.config_path,
                    "config_sha256": plan.config_sha256,
                    "catalog_path": plan.catalog_path,
                    "funding_path": plan.funding_path,
                    "folds": plan.folds,
                    "warmup_days": plan.warmup_days,
                    "window_declared": {
                        "start_utc": plan.window_start.isoformat(),
                        "end_utc": plan.window_end.isoformat(),
                    },
                    "split_policy": plan.split_policy,
                },
                **payload,
            }
            artifact_path.write_text(json.dumps(document, indent=2), encoding="utf-8")
            index["cells"][key] = {
                "artifact_path": str(artifact_path),
                "status": status.value,
                "experiment_id": experiment_id,
                "completed_at": document["generated_at_utc"],
                "identity": identity,
            }
            save_index(index_path, index)
            results.append(
                {
                    "cell": artifact_rel,
                    "status": status.value,
                    "trades": payload["total_trades"],
                    "pnl_after_funding": payload["pnl_after_funding"],
                    "positions_digest": payload["positions_digest"][:16],
                    "observations": payload["observations"],
                }
            )
            completed += 1
        except Exception as exc:  # noqa: BLE001 - isolation boundary
            errors += 1
            error_doc = _error_artifact(plan, experiment_id, exc)
            artifact_path.write_text(json.dumps(error_doc, indent=2), encoding="utf-8")
            index["cells"][error_doc["identity_key"]] = {
                "artifact_path": str(artifact_path),
                "status": CellStatus.PIPELINE_ERROR.value,
                "experiment_id": experiment_id,
                "completed_at": error_doc["generated_at_utc"],
                "identity": error_doc["identity"],
            }
            save_index(index_path, index)
            results.append(
                {
                    "cell": artifact_rel,
                    "status": CellStatus.PIPELINE_ERROR.value,
                    "error": str(exc)[:300],
                }
            )

    report = {
        "matrix_id": matrix_id,
        "experiment_id": experiment_id,
        "tier": tier,
        "strategies": strategies,
        "symbols": symbols,
        "declared_cells": len(plans),
        "completed": completed,
        "reused": reused,
        "pipeline_errors": errors,
        "results": results,
        "index_path": str(index_path),
        "coverage_ref": "coverage.json (research.data_audit)",
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _error_artifact(plan: CellPlan, experiment_id: str, exc: Exception) -> dict:
    identity = plan.identity(
        fee_model="unknown",
        slippage_model="unknown",
        seed=None,
        snapshot_id=data_snapshot_id(
            plan.catalog_path, plan.symbol, plan.window_start, plan.window_end
        )
        + "|ERROR",
    )
    cell_result = MatrixCellResult(
        experiment_id=experiment_id,
        strategy_type=plan.strategy_type,
        symbol=plan.symbol,
        status=CellStatus.PIPELINE_ERROR,
        artifact_path=None,
        reason_codes=("cell_failed_exception",),
        config_sha256=plan.config_sha256,
        data_snapshot_id=None,
        split_policy=plan.split_policy,
        folds_completed=0,
    )
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tier": plan.tier,
        "identity": identity,
        "identity_key": plan.identity_key(identity),
        "cell_result": cell_result.to_dict(),
        "error": str(exc),
        "traceback": traceback.format_exc(limit=12),
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--matrix-id", required=True)
    parser.add_argument("--tier", type=int, choices=(0, 1), required=True)
    parser.add_argument("--strategies", nargs="+", default=list(INVENTORY))
    parser.add_argument("--symbols", nargs="+", default=None)
    parser.add_argument("--universe-config", default="config/research_scan_top20.yaml")
    parser.add_argument("--folds", type=int, default=DEFAULT_FOLDS)
    parser.add_argument("--window-start", default=None)
    parser.add_argument("--window-end", default=None)
    parser.add_argument("--output-root", default="results/matrix")
    parser.add_argument("--limit-cells", type=int, default=None)
    args = parser.parse_args(argv)

    unknown = set(args.strategies).difference(ALL_STRATEGIES)
    if unknown:
        parser.error(f"unknown strategies {sorted(unknown)}; inventory={ALL_STRATEGIES}")

    symbols = args.symbols
    if symbols is None:
        import yaml

        with open(args.universe_config, encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        symbols = [str(s) for s in raw.get("market", {}).get("symbols", [])]
    if not symbols:
        parser.error("no symbols resolved")

    window_start = pd.Timestamp(args.window_start) if args.window_start else DECLARED_S0_START
    window_end = pd.Timestamp(args.window_end) if args.window_end else DECLARED_S0_END
    if window_start.tzinfo is None:
        window_start = window_start.tz_localize("UTC")
    if window_end.tzinfo is None:
        window_end = window_end.tz_localize("UTC")

    report = run_matrix(
        matrix_id=args.matrix_id,
        tier=args.tier,
        strategies=args.strategies,
        symbols=symbols,
        output_root=args.output_root,
        folds=args.folds,
        window_start=window_start,
        window_end=window_end,
        limit_cells=args.limit_cells,
    )
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    for row in report["results"]:
        print(f"  {row['status']:14s} {row['cell']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
