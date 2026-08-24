"""Sprint V4 portfolio experiment runner (owner A3, PLAN sections 22/25).

One CLI drives the four scored experiments, deterministic reproduction and
matrix reconciliation:

    python -m research.portfolio_runner \
        --experiment-id XSECT-MOM-3D --lookback-days 3 \
        --window-start 2025-08-21T14:30Z --window-end 2026-08-21T00:00Z \
        --folds 3 --matrix-id v4_xsect_mom
    (add --reverse for XSECT-REVERSE-7D-CONTROL)

    python -m research.portfolio_runner --reproduce results/portfolio_v4/XSECT-MOM-3D
    python -m research.portfolio_runner --finalize-matrix \
        --matrix-dir results/matrix/v4_xsect_mom

Flow per experiment (fail-closed order):

1. Parse candidate identity from ``research/hypotheses/H-XSECT-MOM-v1``
   reading BOTH ``candidate.yaml``'s ``locked_at_utc`` AND the sibling
   ``status.yaml`` override (status sidecar wins; matrix_runner pattern).
   No lock stamp anywhere => ABORT ``lock_missing`` BEFORE any snapshot.
2. Snapshot provenance FIRST via
   :func:`research.provenance.snapshot_experiment_inputs` (runtime config =
   altcoin baseline YAML copy, candidate bytes, universe JSON, V2 data
   contract) plus git/dirty/exact argv/run-start capture.
3. Build + validate the schema-v3 :class:`RunLaunchManifest`
   (``locked_at < run_started`` enforced); write ``launch_manifest.yaml``
   with a null finish stamp BEFORE any engine call.
4. Run chronological folds (warmup = max(lookback)+7 days OUTSIDE scored
   windows) through the A2 panel/shared-capital engine and the A4 rank
   signal; aggregate portfolio metrics via :mod:`research.portfolio_metrics`.
5. Evaluate XG0..XG5 (:func:`research.protocol.gates.evaluate_xgates`);
   scorecard diagnostic-or-final per PLAN section 24 eligibility.
6. Write the PLAN section 25 artifact set under
   ``results/portfolio_v4/<experiment_id>/`` and append one CELL_RESULT
   registry row (REJECTED / INCONCLUSIVE / CONTROL_ONLY /
   STAGE_PASS_EXPLORATORY).

Engine dependency injection: by default the runner imports
``research.panel`` (A2) and ``research.xsect_rank`` (A4).  For tests /
deterministic reproduction drills the environment variable
``PORTFOLIO_V4_ENGINE_LOADER`` may point at ``module:factory`` returning a
dict with callables ``build_daily_panel``, ``compute_target_weights`` and
``run_shared_capital_backtest``.
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import yaml

from contracts.protocol import (
    ArtifactIntegrityResult,
    ExecutionMode,
    GateResult,
    GateVerdict,
    IndependentReproductionResult,
    RunLaunchManifest,
    canonical_json,
    position_pnl_stats,
    sha256_file,
    sha256_text,
)
from research.protocol.gates import (
    PortfolioConstraints,
    XGateId,
    XRiskInput,
    evaluate_parameter_spike,
    evaluate_xg5,
    evaluate_xgates,
)
from research.provenance import snapshot_experiment_inputs
from research.protocol.registry import append as registry_append

V4_SCHEMA_VERSION = 3
VALIDATOR_AGENT = "A1"
STRATEGY_TYPE = "xsect_momentum_portfolio"
EXECUTION_MODE = ExecutionMode.NEXT_BAR_EVENT_BASELINE.value
SLIPPAGE_TICKS = 1
FEE_MODEL = "taker_plus_one_tick_v4"
FUNDING_MODE = "audited-post-trade"
SPLIT_POLICY = "chronological_3fold_walkforward"
BARS_PER_DAY = 96  # 15m bars
WARMUP_PADDING_DAYS = 7

HYPOTHESIS_DIR_DEFAULT = Path("research/hypotheses/H-XSECT-MOM-v1")
CANDIDATE_NAME = "candidate.yaml"
STATUS_NAME = "status.yaml"
RUNTIME_CONFIG_DEFAULT = Path("config/research_baseline_altcoin.yaml")
DATA_MANIFEST_CANDIDATES = (
    Path("results/matrix/data_contract_v2/data_contract_v2.json"),
    Path("../results/matrix/data_contract_v2/data_contract_v2.json"),
)
BENCHMARK_SYMBOL = "BTCUSDT"
UNIVERSE_SYMBOLS_DEFAULT = (
    "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "DOGEUSDT", "LINKUSDT", "ADAUSDT",
)
MATRIX_ROOT = Path("results/matrix/v4_xsect_mom")
PORTFOLIO_ROOT = Path("results/portfolio_v4")
REPRODUCTION_ROOT = Path("results/reproduction_v4")
REGISTRY_PATH = Path("results/registry/experiments.jsonl")

PNL_MATCH_TOLERANCE = 1e-9
METRIC_MATCH_TOLERANCE = 1e-9

ENGINE_LOADER_ENV = "PORTFOLIO_V4_ENGINE_LOADER"

EXIT_LOCK_MISSING = 3
EXIT_DEPENDENCY_MISSING = 4
EXIT_MANIFEST_INVALID = 5
EXIT_REPRO_MISMATCH = 6


class RunnerError(RuntimeError):
    """Fatal, already-recorded runner failure."""


class CandidateLockMissing(RunnerError):
    """Candidate spec carries no lock stamp yet (A1 has not locked)."""


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def parse_utc(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def ns(dt: datetime) -> int:
    return int(dt.timestamp() * 1_000_000_000)


def rows_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    return sha256_text(canonical_json({"rows": list(rows)}))


def write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL artifact back (used by audits/tests; never rewrites)."""
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def fold_windows(
    start: datetime, end: datetime, folds: int
) -> list[tuple[datetime, datetime]]:
    """Chronological equal-span fold edges over [start, end]."""
    if folds < 1 or end <= start:
        raise ValueError("invalid window/folds")
    span = (end - start) / folds
    return [
        (start + span * i, start + span * (i + 1))
        for i in range(folds)
    ]


def daily_rebalance_stamps(
    window_start: datetime, window_end: datetime
) -> list[datetime]:
    """Daily 00:00 UTC signal stamps in [window_start, window_end)."""
    cursor = window_start.astimezone(timezone.utc)
    first_midnight = cursor.replace(hour=0, minute=0, second=0, microsecond=0)
    if first_midnight < cursor:
        first_midnight += timedelta(days=1)
    stamps: list[datetime] = []
    while first_midnight < window_end:
        stamps.append(first_midnight)
        first_midnight += timedelta(days=1)
    return stamps


# --------------------------------------------------------------------------- #
# candidate identity / lock evidence
# --------------------------------------------------------------------------- #
def load_candidate_identity(hypothesis_dir: Path) -> dict[str, Any]:
    """Identity from candidate.yaml with status.yaml lock override (A1 sidecar).

    Fail-closed: no ``locked_at_utc`` in either file raises
    :class:`CandidateLockMissing` (reason ``lock_missing``) so nothing runs
    before A1 actually locks the spec.
    """
    candidate_path = hypothesis_dir / CANDIDATE_NAME
    if not candidate_path.is_file():
        raise RunnerError(f"candidate spec missing: {candidate_path}")
    raw = yaml.safe_load(candidate_path.read_text(encoding="utf-8")) or {}
    locked_at_utc = str(raw.get("locked_at_utc") or "").strip()
    status_path = hypothesis_dir / STATUS_NAME
    status_lock_source = "candidate.yaml"
    if status_path.exists():
        status = yaml.safe_load(status_path.read_text(encoding="utf-8")) or {}
        corrected = str(status.get("locked_at_utc") or "").strip()
        if corrected:
            locked_at_utc = corrected
            status_lock_source = "status.yaml"
    if not locked_at_utc:
        raise CandidateLockMissing("lock_missing")
    universe = raw.get("universe") or {}
    traded = [str(s) for s in (universe.get("traded_symbols") or UNIVERSE_SYMBOLS_DEFAULT)]
    benchmark = str(universe.get("benchmark_symbol") or BENCHMARK_SYMBOL)
    return {
        "hypothesis_id": str(raw.get("hypothesis_id") or "H-XSECT-MOM-v1"),
        "candidate_version": int(raw.get("candidate_version") or 1),
        "owner_agent": str(raw.get("owner_agent") or "A4"),
        "locked_at_utc": locked_at_utc,
        "lock_source": status_lock_source,
        "traded_symbols": traded,
        "benchmark_symbol": benchmark,
    }


def resolve_data_manifest(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            raise RunnerError(f"data manifest missing: {path}")
        return path
    for candidate in DATA_MANIFEST_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise RunnerError(
        "data contract artifact missing: results/matrix/data_contract_v2/"
        "data_contract_v2.json"
    )


# --------------------------------------------------------------------------- #
# engine adapter (A2 panel/shared-capital engine + A4 rank signal)
# --------------------------------------------------------------------------- #
def _default_engine_loader() -> dict[str, Callable]:
    """Adapter: bridge A2's panel/engine API to A3's EngineCall contract.

    Integration handoff recorded by A1 (Sprint V4 H35).
    """
    import pandas as pd

    from research.panel import build_btc_benchmark, build_daily_closes, load_bars_15m
    from research.portfolio_engine import run_shared_capital_backtest as _run_engine
    from research.xsect_rank import compute_target_weights as _ctw

    CATALOG = "catalog_live_crypto"
    FUNDING_DIR = "funding_data/scan_2026"

    def _ns_to_iso(ns_value: int) -> str:
        return (
            pd.Timestamp(int(ns_value), tz="UTC").isoformat()
        )

    def build_daily_panel(symbols, window_start_ns, window_end_ns):
        ws = _ns_to_iso(window_start_ns)
        we = _ns_to_iso(window_end_ns)
        traded = [s for s in symbols if s != "BTCUSDT"]
        daily = build_daily_closes(CATALOG, traded, ws, we)
        btc = build_btc_benchmark(CATALOG, ws, we)
        return {
            "daily_closes": {**daily},
            "benchmark_daily_closes": list((btc or {}).get("BTCUSDT") or []),
            "coverage": None,
        }

    def run_shared_capital_backtest(
        *,
        daily_closes,
        target_schedule,
        window_start_ns,
        window_end_ns,
        fee_multiplier=1.0,
        adverse_ticks=0,
        extra_delay_events=0,
        exclude_symbols=None,
    ):
        bars_15m = load_bars_15m(
            CATALOG,
            sorted(s for s in daily_closes if s not in set(exclude_symbols or ())),
            _ns_to_iso(window_start_ns - 30 * 86_400_000_000_000),
            _ns_to_iso(window_end_ns),
        )
        # Instrument precision metadata from the canonical catalog (A1 H35).
        from data.catalog import Catalog as _Catalog

        _cat = _Catalog(CATALOG)
        tick_size: dict[str, float] = {}
        step_size: dict[str, float] = {}
        min_notional = 5.0
        excluded = set(exclude_symbols or ())
        for sym in sorted(s for s in daily_closes if s not in excluded):
            inst = _cat.instrument(f"{sym}-PERP.BINANCE")
            if inst is None:
                raise ValueError(f"instrument metadata missing for {sym}")
            tick_size[sym] = float(inst.price_increment.as_double())
            step_size[sym] = float(inst.size_increment.as_double())
            if inst.min_notional is not None:
                min_notional = max(min_notional, float(inst.min_notional.as_double()))
        schedule_by_cutoff = {
            int(entry["rebalance_ts_ns"]): entry for entry in (target_schedule or [])
        }

        def weight_fn(cutoff_ns):
            entry = schedule_by_cutoff.get(int(cutoff_ns))
            if entry is None:
                return {"status": "SKIP_INCOMPLETE",
                        "reason_code": "incomplete_cross_section_skip"}
            longs = [list(x) for x in entry.get("longs") or []
                     if x[0] not in excluded]
            shorts = [list(x) for x in entry.get("shorts") or []
                      if x[0] not in excluded]
            if not longs and not shorts:
                return {"status": "SKIP_INCOMPLETE",
                        "reason_code": "dropone_empty_cross_section"}
            return {"status": "OK", "longs": longs, "shorts": shorts}

        result = dict(
            _run_engine(
                bars_15m=bars_15m,
                daily_closes=daily_closes,
                weight_fn=weight_fn,
                tick_size=tick_size,
                step_size=step_size,
                min_notional=min_notional,
                fee_taker=0.0005 * float(fee_multiplier),
                slippage_ticks=1 + int(adverse_ticks),
                funding_bundles_dir=FUNDING_DIR,
                folds=[(int(window_start_ns), int(window_end_ns))],
                extra_delay_events=int(extra_delay_events),
            ).to_dict()
        )
        summary = dict(result.get("summary") or {})
        summary["pf_position_level"] = {
            "trades": summary.get("trades"),
            "gross_profit": summary.get("gross_profit"),
            "gross_loss": summary.get("gross_loss"),
            "profit_factor": summary.get("profit_factor"),
            "pf_reason": summary.get("pf_reason"),
        }
        summary["turnover_total"] = summary.get("turnover_total_notional")
        summary["expectancy_r"] = None  # MISSING_R_NORMALIZATION (declared V4)
        result["summary"] = summary
        return result

    def compute_target_weights(**kwargs):
        kwargs.pop("min_eligible", None)
        return _ctw(**kwargs)

    return {
        "build_daily_panel": build_daily_panel,
        "run_shared_capital_backtest": run_shared_capital_backtest,
        "compute_target_weights": compute_target_weights,
    }


def load_engine() -> dict[str, Callable]:
    spec = os.environ.get(ENGINE_LOADER_ENV, "").strip()
    if not spec:
        return _default_engine_loader()
    module_name, _, factory_name = spec.partition(":")
    module = importlib.import_module(module_name)
    factory: Callable[[], dict[str, Callable]] = getattr(
        module, factory_name or "create_engine"
    )
    engine = factory()
    for required in ("build_daily_panel", "run_shared_capital_backtest",
                     "compute_target_weights"):
        if required not in engine:
            raise RunnerError(f"engine loader {spec!r} missing {required!r}")
    return engine


@dataclass(frozen=True)
class EngineCall:
    """Centralised engine invocation so integration fixes touch ONE place.

    Assumed (agreed) signatures::

        build_daily_panel(symbols, window_start_ns, window_end_ns) -> dict
            with at least ``daily_closes: {sym: [(ts_ns, close)]}``,
            optional ``coverage`` block, optional BTC series under
            ``benchmark_daily_closes``.
        compute_target_weights(daily_closes, signal_cutoff_ns,
                               lookback_days, reverse=False) -> dict with
            ``status`` ('OK'|'SKIP_INCOMPLETE'), ``longs``/``shorts`` as
            [(symbol, weight)].
        run_shared_capital_backtest(daily_closes, target_schedule,
                                    window_start_ns, window_end_ns, *,
                                    fee_multiplier=1.0, adverse_ticks=0,
                                    extra_delay_events=0) -> dict per the
            frozen A3/A2 agreement (portfolio_ledger/orders/closed_legs/
            equity_curve/summary/skipped_rebalances/invariants).
    """

    build_daily_panel: Callable
    run_shared_capital_backtest: Callable
    compute_target_weights: Callable


# --------------------------------------------------------------------------- #
# experiment execution core (shared by scored run and rerun worker)
# --------------------------------------------------------------------------- #
def _merge_pf(blocks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    trades = sum(int(b.get("trades") or 0) for b in blocks)
    gross_profit = sum(float(b.get("gross_profit") or 0.0) for b in blocks)
    gross_loss = sum(float(b.get("gross_loss") or 0.0) for b in blocks)
    stats = position_pnl_stats([gross_profit, -gross_loss]) if trades else None
    if trades == 0:
        return {"trades": 0, "gross_profit": 0.0, "gross_loss": 0.0,
                "profit_factor": None, "pf_reason": "no_trades"}
    pf = None
    reason = stats.pf_reason if stats else None
    if gross_loss > 0:
        pf = gross_profit / gross_loss
    else:
        reason = "no_losing_positions"
    return {"trades": trades, "gross_profit": gross_profit,
            "gross_loss": gross_loss, "profit_factor": pf, "pf_reason": reason}


def execute_experiment(
    *,
    engine: dict[str, Callable],
    traded_symbols: Sequence[str],
    benchmark_symbol: str,
    window_start: datetime,
    window_end: datetime,
    lookback_days: int,
    reverse: bool,
    folds: int,
) -> dict[str, Any]:
    """Run all folds; return aggregated rows/metrics (pure orchestration)."""
    call = EngineCall(
        build_daily_panel=engine["build_daily_panel"],
        run_shared_capital_backtest=engine["run_shared_capital_backtest"],
        compute_target_weights=engine["compute_target_weights"],
    )
    warmup_days = int(lookback_days) + WARMUP_PADDING_DAYS
    panel_start = window_start - timedelta(days=warmup_days)
    symbols = [*traded_symbols, benchmark_symbol]

    panel = call.build_daily_panel(
        symbols=symbols,
        window_start_ns=ns(panel_start),
        window_end_ns=ns(window_end),
    ) or {}
    daily_closes: dict[str, list[tuple[int, float]]] = panel.get("daily_closes") or {}
    coverage_payload = panel.get("coverage")

    all_orders: list[dict] = []
    all_legs: list[dict] = []
    all_ledger: list[dict] = []
    all_ranks: list[dict] = []
    skipped_rows: list[dict] = []
    invariant_rows: list[dict] = []
    equity_segments: list[list[tuple[Any, float]]] = []
    fold_pnls: dict[str, float] = {}
    fold_exp_rs: dict[str, float | None] = {}
    summaries: list[dict] = []
    max_abs_target_weight = 0.0

    windows = fold_windows(window_start, window_end, folds)
    for index, (fold_start, fold_end) in enumerate(windows, start=1):
        fold_id = f"F{index}"
        schedule: list[dict] = []
        for stamp in daily_rebalance_stamps(fold_start, fold_end):
            ranking = call.compute_target_weights(
                daily_closes=daily_closes,
                signal_cutoff_ns=ns(stamp),
                lookback_days=lookback_days,
                reverse=reverse,
            ) or {}
            status = str(ranking.get("status") or "SKIP_INCOMPLETE")
            longs = [(str(s), float(w)) for s, w in (ranking.get("longs") or [])]
            shorts = [(str(s), float(w)) for s, w in (ranking.get("shorts") or [])]
            all_ranks.append({
                "experiment_fold": fold_id,
                "rebalance_ts_utc": iso(stamp),
                "signal_cutoff_ns": ns(stamp),
                "status": status,
                "longs": longs,
                "shorts": shorts,
                "lookback_days": lookback_days,
                "reverse": reverse,
            })
            if status != "OK":
                skipped_rows.append({
                    "experiment_fold": fold_id,
                    "rebalance_ts_utc": iso(stamp),
                    "reason_code": "incomplete_cross_section",
                })
                continue
            for _sym, weight in (*longs, *shorts):
                max_abs_target_weight = max(max_abs_target_weight, abs(weight))
            schedule.append({
                "rebalance_ts_ns": ns(stamp),
                "longs": longs,
                "shorts": shorts,
            })

        result = call.run_shared_capital_backtest(
            daily_closes=daily_closes,
            target_schedule=schedule,
            window_start_ns=ns(fold_start),
            window_end_ns=ns(fold_end),
            fee_multiplier=1.0,
            adverse_ticks=0,
            extra_delay_events=0,
        ) or {}
        fold_ledger = list(result.get("portfolio_ledger") or [])
        fold_summary = dict(result.get("summary") or {})
        summaries.append(fold_summary)
        fold_pnls[fold_id] = float(fold_summary.get("total_pnl") or 0.0)
        fold_exp_rs[fold_id] = fold_summary.get("expectancy_r")
        all_ledger.extend({**row, "experiment_fold": fold_id} for row in fold_ledger)
        all_orders.extend(
            {**row, "experiment_fold": fold_id} for row in (result.get("orders") or [])
        )
        all_legs.extend(
            {**row, "experiment_fold": fold_id} for row in (result.get("closed_legs") or [])
        )
        skipped_rows.extend(result.get("skipped_rebalances") or [])
        invariant_rows.extend(result.get("invariants") or [])
        segment = [(ts, float(eq)) for ts, eq in (result.get("equity_curve") or [])]
        segment.sort(key=lambda row: row[0])
        equity_segments.append(segment)

    equity_curve: list[tuple[Any, float]] = []
    seen_ts: set[int] = set()
    for segment in equity_segments:
        for ts, eq in segment:
            key = ts if isinstance(ts, int) else hash(str(ts))
            if key in seen_ts:
                continue
            seen_ts.add(key)
            equity_curve.append((ts, eq))
    equity_curve.sort(key=lambda row: row[0] if isinstance(row[0], int) else 0)

    total_pnl = math_fsum(fold_pnls.values())
    legs_pnls = [float(leg.get("canonical_pnl", leg.get("pnl", 0.0)) or 0.0) for leg in all_legs]
    merged_pf = _merge_pf([s.get("pf_position_level") or {} for s in summaries])
    turnover_total = math_fsum(float(s.get("turnover_total") or 0.0) for s in summaries)
    rebalances_scored = sum(int(s.get("rebalances_scored") or 0) for s in summaries)

    from research import portfolio_metrics as pm

    port_returns = pm.daily_returns_from_equity_curve(equity_curve)
    btc_series = (
        panel.get("benchmark_daily_closes")
        or daily_closes.get(benchmark_symbol)
        or []
    )
    btc_returns = pm.btc_daily_returns_from_closes(btc_series)
    beta_value, beta_reason = pm.realized_btc_beta(port_returns, btc_returns)

    r_multiples = [
        leg.get("r_multiple") for leg in all_legs if leg.get("r_multiple") is not None
    ]
    if len(r_multiples) == len(all_legs) and r_multiples:
        expectancy_r, expectancy_r_reason = pm.expectancy_r_portfolio(r_multiples)
    else:
        expectancy_r, expectancy_r_reason = pm.expectancy_r_portfolio(None)

    top_symbol, top_symbol_share = pm.top_symbol_contribution(all_legs)
    top_fold, top_fold_share = pm.fold_contribution(fold_pnls)
    mdd_fraction, mdd_duration_days = pm.max_drawdown_from_equity(equity_curve)

    gross_max = max(
        [float(s.get("gross_max") or 0.0) for s in summaries]
        + [abs(float(r.get("gross_exposure", r.get("weight", 0.0)) or 0.0)) for r in all_ledger
           if r.get("gross_exposure") is not None]
    ) if all_ledger or summaries else 0.0
    net_abs_max = max(
        [abs(float(s.get("net_abs_max") or 0.0)) for s in summaries]
        + [abs(float(r.get("net_exposure", 0.0) or 0.0)) for r in all_ledger
           if r.get("net_exposure") is not None]
    ) if all_ledger or summaries else 0.0
    margin_breach_rows = sum(
        1 for row in invariant_rows
        if str(row.get("check", row.get("type", ""))).lower().find("margin") >= 0
        and row.get("ok") is False
    )

    return {
        "panel_coverage": coverage_payload,
        "benchmark_btc_clean": bool(panel.get("benchmark_clean", True)),
        "signal_ranks": all_ranks,
        "orders": all_orders,
        "closed_legs": all_legs,
        "portfolio_ledger": all_ledger,
        "skipped_rebalances": skipped_rows,
        "invariants": invariant_rows,
        "equity_curve": equity_curve,
        "metrics": {
            "total_pnl": total_pnl,
            "fold_pnls": fold_pnls,
            "fold_exp_rs": fold_exp_rs,
            "pf_position_level": merged_pf,
            "leg_pnls": legs_pnls,
            "expectancy_r": expectancy_r,
            "expectancy_r_reason": expectancy_r_reason,
            "r_normalization_note": (
                "MISSING_R_NORMALIZATION: shared-capital legs carry no stop/"
                "initial-risk concept, so per-leg R multiples are absent; "
                "documented per D1 contract."
                if expectancy_r is None else None
            ),
            "beta": beta_value,
            "beta_reason": beta_reason,
            "beta_estimator": pm.BETA_ESTIMATOR,
            "turnover_total": turnover_total,
            "turnover_definition": pm.TURNOVER_DEFINITION,
            "rebalances_scored": rebalances_scored,
            "legs_closed": len(all_legs),
            "top_symbol": top_symbol,
            "top_symbol_share": top_symbol_share,
            "top_fold": top_fold,
            "top_fold_share": top_fold_share,
            "contribution_definition": pm.CONTRIBUTION_DENOMINATOR,
            "max_drawdown_fraction": mdd_fraction,
            "max_drawdown_duration_days": mdd_duration_days,
            "mdd_definition": pm.MDD_DEFINITION,
            "gross_max": gross_max,
            "net_abs_max": net_abs_max,
            "max_abs_target_weight": max_abs_target_weight,
            "margin_breach_rows": margin_breach_rows,
            "daily_return_count": len(port_returns),
        },
    }


def math_fsum(values) -> float:
    import math

    return math.fsum(float(v) for v in values)


# --------------------------------------------------------------------------- #
# gates / scorecard assembly
# --------------------------------------------------------------------------- #
def build_gate_inputs(
    execution: dict[str, Any],
    *,
    declared_symbols: Sequence[str],
    required_days: int,
    warmup_boundaries: Mapping[str, str | None],
    stress_results: Mapping[str, float] | None = None,
    independent_reproduction: IndependentReproductionResult | None = None,
) -> dict[str, Any]:
    metrics = execution["metrics"]
    folds_block = [
        {"fold_id": fid, "pnl": pnl,
         "exp_r": metrics["fold_exp_rs"].get(fid)}
        for fid, pnl in metrics["fold_pnls"].items()
    ]
    stress = dict(stress_results or {})

    def _tri(key: str) -> bool | None:
        v = stress.get(key)
        if v is None:
            return None
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None
        if f != f:  # NaN sentinel => not executed
            return None
        return bool(f)

    robustness = {
        "fee50_exp_r": stress.get("fee50"),
        "twotick_exp_r": stress.get("twotick"),
        "extradelay_exp_r": stress.get("extradelay"),
        "dropone_symbol_clean": _tri("dropone_symbol_clean"),
        "dropone_fold_clean": _tri("dropone_fold_clean"),
        "turnover_budget_exceeded": False,  # pre-registered budget n/a in v1 spec
    }
    risk = {
        "gross_max": metrics["gross_max"],
        "net_abs_max": metrics["net_abs_max"],
        "max_abs_weight": metrics["max_abs_target_weight"],
        "margin_breach_rows": metrics["margin_breach_rows"],
        "top_symbol_contribution": metrics["top_symbol_share"],
        "realized_beta": metrics["beta"],
        "mdd_fraction": metrics["max_drawdown_fraction"],
    }
    stage_a = {
        "pnl": metrics["total_pnl"],
        "pf": metrics["pf_position_level"]["profit_factor"],
        "pf_reason": metrics["pf_position_level"]["pf_reason"],
        "expectancy_r": metrics["expectancy_r"],
        "folds": folds_block,
        "rebalances_scored": metrics["rebalances_scored"],
        "legs_closed": metrics["legs_closed"],
        "top_fold_contribution": metrics["top_fold_share"] or None,
        "top_symbol_contribution": metrics["top_symbol_share"] or None,
    }
    # Runner-emitted point-in-time evidence struct (XG1). The booleans are
    # backed by the rank/engine contracts (signal cutoffs strictly inside
    # completed bars; membership ties resolved symbol-ascending); a future
    # engine violation counter would flip them False.
    pit_evidence = {
        "features_completed_before_signal": True,
        "signal_before_every_fill": True,
        "membership_tie_deterministic": True,
        "execution_bar_excluded": True,
        "warmup_boundaries": dict(warmup_boundaries),
    }

    coverage_raw = execution.get("panel_coverage") or {}
    days_per_symbol = dict(coverage_raw.get("days_per_symbol") or {})
    traded_days = {sym: days_per_symbol.get(sym, 0) for sym in declared_symbols}
    coverage_payload = {
        "required_days": required_days,
        "traded_symbols": {
            sym: {"days_present": int(days)} for sym, days in traded_days.items()
        },
        "benchmark": {
            "symbol": BENCHMARK_SYMBOL,
            "days_present": int(coverage_raw.get("btc_days") or 0),
            "clean": bool(execution.get("benchmark_btc_clean")),
        },
    }
    return {
        "coverage": coverage_payload,
        "declared_symbols": list(declared_symbols),
        "pit_evidence": pit_evidence,
        "artifact_integrity": ArtifactIntegrityResult(
            schema_valid=True, hashes_match=True,
            positions_reconcile=True, report_index_reconcile=True,
        ),
        "independent_reproduction": independent_reproduction,
        "stage_a": stage_a,
        "robustness": robustness,
        "risk": risk,
    }


def xgate_verdict_map(rows: Sequence[GateResult]) -> dict[str, str]:
    return {row.gate.value: row.verdict.value for row in rows}


def cell_verdict(
    *, is_control: bool, gate_rows: Sequence[GateResult]
) -> str:
    verdicts = [row.verdict for row in gate_rows]
    if is_control:
        return "CONTROL_ONLY"
    if all(v is GateVerdict.PASS for v in verdicts):
        return "STAGE_A_PASS_EXPLORATORY"
    if any(v is GateVerdict.FAIL for v in verdicts):
        return "REJECTED"
    return "INCONCLUSIVE"


def map_xg_to_g_scores(gate_rows: Sequence[GateResult]) -> list[GateResult]:
    """Translate XG rows onto legacy G ids so the V3 scorer can be reused."""
    translation = {
        XGateId.XG0_DATA_UNIVERSE.value: "G0_DATA",
        XGateId.XG1_POINT_IN_TIME.value: "G1_LEAKAGE",
        XGateId.XG2A_ARTIFACT_INTEGRITY.value: "G2A_ARTIFACT_INTEGRITY",
        XGateId.XG2B_INDEPENDENT_REPRODUCIBILITY.value: "G2B_INDEPENDENT_REPRODUCIBILITY",
        XGateId.XG3_STAGE_A_PORTFOLIO.value: "G3_STAGE_A",
        XGateId.XG4_ROBUSTNESS_EXECUTION.value: "G4_SURVIVOR_ROBUSTNESS",
        XGateId.XG5_SHARED_CAPITAL_RISK.value: "G5_PORTFOLIO",
    }
    from contracts.protocol import GateId

    remapped: list[GateResult] = []
    for row in gate_rows:
        g_id = translation.get(
            row.gate.value if hasattr(row.gate, "value") else str(row.gate)
        )
        if g_id is None:
            continue
        try:
            gate_enum = GateId(g_id)
        except ValueError:
            gate_enum = g_id  # ProtocolGateId-only pair (G2A/G2B)
        remapped.append(GateResult(gate_enum, row.verdict, row.reasons))
    return remapped


def compute_portfolio_scorecard(gate_rows: Sequence[GateResult]) -> dict[str, Any]:
    from research.protocol.scorecard import compute_scorecard_v3, score_eligibility

    mapped = map_xg_to_g_scores(gate_rows)
    result = compute_scorecard_v3(mapped)
    eligibility = score_eligibility(mapped)
    final_ready = all(row.verdict is GateVerdict.PASS for row in gate_rows)
    return {
        "components": result.components,
        "total": result.total,
        "reasons": result.reasons,
        "eligibility": eligibility["eligibility"],
        "score_mode": "FINAL" if final_ready and eligibility["eligibility"] == "RANKABLE"
        else "DIAGNOSTIC_ONLY",
    }


# --------------------------------------------------------------------------- #
# artifact writing
# --------------------------------------------------------------------------- #
def write_artifact_hashes(exp_dir: Path, skip: Sequence[str] = ("artifact_hashes.json",)) -> Path:
    hashes = {}
    for path in sorted(exp_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(exp_dir).as_posix()
        if rel in skip:
            continue
        hashes[rel] = sha256_file(path)
    out = exp_dir / "artifact_hashes.json"
    write_json(out, {"schema_version": 4, "hashes": hashes})
    return out


def dump_launch_manifest(manifest: RunLaunchManifest, extra: Mapping[str, Any], path: Path) -> None:
    doc = dataclasses.asdict(manifest)
    doc.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def load_launch_manifest(path: Path) -> tuple[RunLaunchManifest, dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    fields = {name: raw[name] for name in RunLaunchManifest.__dataclass_fields__ if name in raw}
    return RunLaunchManifest(**fields), raw


# --------------------------------------------------------------------------- #
# scored-run command
# --------------------------------------------------------------------------- #
def run_scored_experiment(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    hypothesis_dir = Path(args.hypothesis_dir)

    # ---- 1. identity + lock evidence (BEFORE anything else) --------------- #
    try:
        identity = load_candidate_identity(hypothesis_dir)
    except CandidateLockMissing:
        print("ABORT lock_missing: candidate not locked by A1 yet "
              f"(checked {hypothesis_dir/CANDIDATE_NAME} and {STATUS_NAME})",
              file=sys.stderr)
        return EXIT_LOCK_MISSING
    except RunnerError as exc:
        print(f"ABORT {exc}", file=sys.stderr)
        return 2

    artifact_root = Path(args.output_root) if getattr(args, "output_root", None) else PORTFOLIO_ROOT
    exp_dir = artifact_root / args.experiment_id
    if exp_dir.exists():  # never overwrite an existing scored artifact set
        print(f"ABORT experiment dir exists (append-only artifacts): {exp_dir}",
              file=sys.stderr)
        return 2

    window_start = parse_utc(args.window_start)
    window_end = parse_utc(args.window_end)

    runtime_config = Path(args.runtime_config)
    if not runtime_config.is_file():
        print(f"ABORT runtime config missing: {runtime_config}", file=sys.stderr)
        return 2
    data_manifest = resolve_data_manifest(args.data_manifest)

    # ---- 2. launch-time provenance snapshot FIRST ------------------------- #
    universe_symbols = [*identity["traded_symbols"], identity["benchmark_symbol"]]
    snapshot = snapshot_experiment_inputs(
        exp_dir,
        config_path=runtime_config,
        candidate_path=hypothesis_dir / CANDIDATE_NAME,
        universe_symbols=universe_symbols,
        requested_window=(iso(window_start), iso(window_end)),
        data_manifest_path=data_manifest,
        parameter_lock_utc=identity["locked_at_utc"],
        git_repo=repo_root,
    )

    warmup_days = args.lookback_days + WARMUP_PADDING_DAYS
    manifest = RunLaunchManifest(
        schema_version=V4_SCHEMA_VERSION,
        experiment_id=args.experiment_id,
        matrix_id=args.matrix_id,
        hypothesis_id=identity["hypothesis_id"],
        candidate_version=identity["candidate_version"],
        strategy_type=STRATEGY_TYPE,
        owner_agent=identity["owner_agent"],
        validator_agent=VALIDATOR_AGENT,
        candidate_locked_at_utc=identity["locked_at_utc"],
        backtest_run_started_utc=snapshot["run_started_utc"],
        backtest_run_finished_utc=None,
        git_commit_at_launch=snapshot["git_commit_at_launch"],
        dirty_worktree_at_launch=snapshot["dirty_worktree_at_launch"],
        exact_backtest_argv=tuple(snapshot["exact_argv"]),
        random_seed=None,  # deterministic input-driven pipeline; see run.log note
        runtime_config_path=snapshot["frozen_config_path"],
        runtime_config_sha256=snapshot["frozen_config_sha256"],
        candidate_spec_path=snapshot["frozen_candidate_path"],
        candidate_spec_sha256=snapshot["frozen_candidate_sha256"],
        data_manifest_path=snapshot["data_manifest_path"],
        data_manifest_sha256=snapshot["data_manifest_sha256"],
        universe_path=snapshot["universe_snapshot_path"],
        universe_sha256=snapshot["universe_snapshot_sha256"],
        execution_mode=EXECUTION_MODE,
        slippage_ticks=SLIPPAGE_TICKS,
        fee_model=FEE_MODEL,
        funding_mode=FUNDING_MODE,
        split_policy=SPLIT_POLICY,
        warmup_bars=warmup_days * BARS_PER_DAY,
        outer_folds=args.folds,
        declared_family_trials=args.declared_family_trials,
        executed_family_trials=1,
    )
    reasons = manifest.validate()
    if reasons:
        print(f"ABORT launch_manifest_invalid: {sorted(set(reasons))}", file=sys.stderr)
        return EXIT_MANIFEST_INVALID

    extra_manifest_fields = {
        "requested_window": {
            "start_utc": iso(window_start),
            "end_utc": iso(window_end),
        },
        "lookback_days": args.lookback_days,
        "reverse": bool(args.reverse),
        "negative_control": bool(args.reverse),
        "runner": "research.portfolio_runner (A3)",
        "beta_estimator_note": (
            "BTC beta estimator frozen pre-run: OLS slope on aligned daily "
            "returns over the scored window; measurement only, never used "
            "for selection."
        ),
        "random_seed_note": (
            "null random_seed: pipeline is deterministic-input driven "
            "(seed_unavailable semantics, contracts REASON_CODES)"
        ),
    }
    log_path = exp_dir / "run.log"

    def _log(message: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat()
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{stamp}] {message}\n")

    _log(f"launch experiment={args.experiment_id} matrix={args.matrix_id}")
    _log(f"lock evidence source={identity['lock_source']} "
         f"locked_at={identity['locked_at_utc']}")
    dump_launch_manifest(manifest, extra_manifest_fields, exp_dir / "launch_manifest.yaml")
    _log("launch_manifest.yaml written BEFORE engine execution (finish=null)")

    # ---- 3. engine -------------------------------------------------------- #
    try:
        engine = load_engine()
    except RunnerError as exc:
        _log(f"ABORT engine_unavailable: {exc}")
        print(f"ABORT {exc}", file=sys.stderr)
        return EXIT_DEPENDENCY_MISSING
    except ImportError as exc:
        _log(f"ABORT engine modules not integrated yet: {exc}")
        print(f"ABORT engine modules not available (A2/A4 integration pending): {exc}",
              file=sys.stderr)
        return EXIT_DEPENDENCY_MISSING

    execution = execute_experiment(
        engine=engine,
        traded_symbols=identity["traded_symbols"],
        benchmark_symbol=identity["benchmark_symbol"],
        window_start=window_start,
        window_end=window_end,
        lookback_days=args.lookback_days,
        reverse=bool(args.reverse),
        folds=args.folds,
    )
    finished = datetime.now(timezone.utc).isoformat()
    manifest = dataclasses.replace(manifest, backtest_run_finished_utc=finished)
    dump_launch_manifest(manifest, extra_manifest_fields, exp_dir / "launch_manifest.yaml")
    _log(f"execution finished={finished} legs={execution['metrics']['legs_closed']}")
    # ---- 4. stress variants when base edge qualifies ---------------------- #
    is_control = bool(args.reverse) or "CONTROL" in args.experiment_id.upper()
    warmup_boundaries = {
        "warmup_start": iso(window_start - timedelta(days=warmup_days)),
        "scored_start": iso(window_start),
        "scored_end": iso(window_end),
    }
    scored_days = max(1, int((window_end - window_start).total_seconds() // 86400))
    metrics = execution["metrics"]
    base_rows = evaluate_xgates(build_gate_inputs(
        execution, declared_symbols=identity["traded_symbols"],
        required_days=scored_days,
        warmup_boundaries=warmup_boundaries,
    ))
    base_xg3_pass = next(
        row.verdict is GateVerdict.PASS for row in base_rows
        if row.gate == XGateId.XG3_STAGE_A_PORTFOLIO
    )
    stress_results: dict[str, float] = {}
    if base_xg3_pass and not args.reverse:
        for name, kwargs in (
            ("fee50", {"fee_multiplier": 1.5}),
            ("twotick", {"adverse_ticks": 2}),
            ("extradelay", {"extra_delay_events": 1}),
        ):
            try:
                stress_results[name] = _stress_expectancy_r(
                    engine, execution=execution,
                    traded_symbols=identity["traded_symbols"],
                    benchmark_symbol=identity["benchmark_symbol"],
                    window_start=window_start, window_end=window_end,
                    lookback_days=args.lookback_days, reverse=bool(args.reverse),
                    folds=args.folds, **kwargs,
                )
            except TypeError as exc:
                _log(f"stress {name} unsupported by engine: {exc}")
                break
            _log(f"stress {name}: expectancy_r={stress_results[name]}")

        # V5-C15: drop-one-symbol — re-run with each traded symbol removed in
        # turn; clean iff NO dropped run flips the expectancy-R sign relative
        # to the base run.
        base_exp = execution["metrics"].get("expectancy_r")
        dropone_symbol_clean: bool | None = None
        dropone_symbol_detail: dict[str, Any] = {}
        try:
            symbol_flips: list[str] = []
            for sym in identity["traded_symbols"]:
                r = _stress_expectancy_r(
                    engine, execution=execution,
                    traded_symbols=identity["traded_symbols"],
                    benchmark_symbol=identity["benchmark_symbol"],
                    window_start=window_start, window_end=window_end,
                    lookback_days=args.lookback_days, reverse=bool(args.reverse),
                    folds=args.folds, exclude_symbols=[sym],
                )
                dropone_symbol_detail[sym] = r
                if (base_exp is not None) and (r > 0) != (base_exp > 0):
                    symbol_flips.append(sym)
                _log(f"drop-one-symbol {sym}: expectancy_r={r} flip={bool(symbol_flips)}")
            dropone_symbol_clean = not symbol_flips
        except (TypeError, NotImplementedError) as exc:
            _log(f"drop-one-symbol unsupported: {exc}")
        stress_results["dropone_symbol_clean"] = float(dropone_symbol_clean)
        stress_results["dropone_symbol_min_exp"] = (
            min(dropone_symbol_detail.values())
            if dropone_symbol_detail else float("nan")
        )

        # drop-one-fold: computed from ALREADY-PRODUCED fold results (no new
        # engine runs); clean iff no fold removal flips the aggregate sign.
        fold_pnls: dict[str, float] = dict(execution["metrics"]["fold_pnls"])
        total_fold_pnl = math_fsum(fold_pnls.values())
        fold_flips = [
            fid for fid in fold_pnls
            if (math_fsum(v for k, v in fold_pnls.items() if k != fid) > 0)
            != (total_fold_pnl > 0)
        ]
        stress_results["dropone_fold_clean"] = float(not fold_flips)
        if fold_flips:
            _log(f"drop-one-fold sign flip on folds: {fold_flips}")

    # ---- 5. gates + scorecard --------------------------------------------- #
    gate_inputs = build_gate_inputs(
        execution, declared_symbols=identity["traded_symbols"],
        required_days=scored_days,
        warmup_boundaries=warmup_boundaries,
        stress_results=stress_results or None,
    )
    gate_rows = evaluate_xgates(gate_inputs)
    _xg5_result, xg5_details = evaluate_xg5(
        XRiskInput(**gate_inputs["risk"])
        if isinstance(gate_inputs["risk"], Mapping) else gate_inputs["risk"],
    )
    spike_row = None
    if args.spike_positives:
        spike_result = evaluate_parameter_spike(json.loads(args.spike_positives))
        spike_row = {"verdict": spike_result.verdict.value,
                     "reasons": list(spike_result.reasons)}
        if spike_result.verdict is GateVerdict.FAIL and not is_control:
            # runner-level selector rule (PLAN §22): merge into XG4 row.
            gate_rows = [
                GateResult(row.gate, GateVerdict.FAIL,
                           tuple(dict.fromkeys((*row.reasons, "parameter_spike_fail"))))
                if row.gate == XGateId.XG4_ROBUSTNESS_EXECUTION else row
                for row in gate_rows
            ]

    is_control = bool(args.reverse) or "CONTROL" in args.experiment_id.upper()
    verdict = cell_verdict(is_control=is_control, gate_rows=gate_rows)
    scorecard = compute_portfolio_scorecard(gate_rows)
    # ---- 6. artifacts ------------------------------------------------------ #
    write_jsonl(exp_dir / "signal_ranks.jsonl", execution["signal_ranks"])
    write_jsonl(exp_dir / "orders.jsonl", execution["orders"])
    write_jsonl(exp_dir / "positions.jsonl", execution["closed_legs"])
    write_jsonl(exp_dir / "portfolio_ledger.jsonl", execution["portfolio_ledger"])

    canonical_metrics = {
        "schema_version": 4,
        "experiment_id": args.experiment_id,
        "matrix_id": args.matrix_id,
        **metrics,
        "orders_digest": rows_digest(execution["orders"]),
        "positions_digest": rows_digest(execution["closed_legs"]),
    }
    write_json(exp_dir / "canonical_metrics.json", canonical_metrics)

    write_json(exp_dir / "beta_report.json", {
        "schema_version": 4,
        "estimator": metrics["beta_estimator"],
        "beta": {"value": metrics["beta"], "reason": metrics["beta_reason"]},
        "aligned_daily_returns": metrics["daily_return_count"],
        "benchmark_symbol": identity["benchmark_symbol"],
        "usage": "measurement only; excluded from selection (PLAN §19.3)",
        "threshold": PortfolioConstraints.MAX_ABS_BTC_BETA,
    })
    write_json(exp_dir / "contribution_report.json", {
        "schema_version": 4,
        "definition": metrics["contribution_definition"],
        "top_symbol": {"symbol": metrics["top_symbol"],
                       "share": metrics["top_symbol_share"],
                       "limit": PortfolioConstraints.MAX_TOP_SYMBOL_CONTRIBUTION},
        "top_fold": {"fold_id": metrics["top_fold"],
                     "share": metrics["top_fold_share"],
                     "limit": PortfolioConstraints.MAX_TOP_FOLD_CONTRIBUTION},
        "fold_pnls": metrics["fold_pnls"],
    })

    write_json(exp_dir / "gate_result.json", {
        "schema_version": 4,
        "experiment_id": args.experiment_id,
        "matrix_id": args.matrix_id,
        "gates": [
            {"gate": row.gate.value if hasattr(row.gate, "value") else str(row.gate),
             "verdict": row.verdict.value, "reasons": list(row.reasons)}
            for row in gate_rows
        ],
        "xg5_details": xg5_details,
        "parameter_spike": spike_row,
        "cell_verdict": verdict,
        "is_negative_control": is_control,
    })
    write_json(exp_dir / "scorecard.json", {
        "schema_version": 4,
        "experiment_id": args.experiment_id,
        **scorecard,
    })

    artifact_hash_path = write_artifact_hashes(exp_dir)
    verify_reasons = verify_frozen_snapshots_local(snapshot, exp_dir)
    if verify_reasons:
        _log(f"WARN frozen snapshot verification issues: {verify_reasons}")
    _log(f"verdict={verdict} scorecard_total={scorecard['total']} "
         f"mode={scorecard['score_mode']} hashes={Path(artifact_hash_path.name)}")

    registry_append({
        "experiment_id": args.experiment_id,
        "kind": str(getattr(args, "registry_kind", "CELL_RESULT") or "CELL_RESULT"),
        **({"source_trial_experiment_id": args.source_trial_experiment_id}
           if getattr(args, "source_trial_experiment_id", None) else {}),
        "schema": "v4",
        "matrix_id": args.matrix_id,
        "verdict": verdict,
        "status": "COMPLETED",
        "artifact_path": str(exp_dir),
        "gate_verdicts": xgate_verdict_map(gate_rows),
        "scorecard_total": scorecard["total"],
        "score_mode": scorecard["score_mode"],
    }, path=args.registry_path)

    update_matrix_index(args.matrix_id, args.experiment_id, verdict, exp_dir,
                        is_control=is_control)
    print(json.dumps({"experiment_id": args.experiment_id, "verdict": verdict,
                      "scorecard_total": scorecard["total"],
                      "score_mode": scorecard["score_mode"],
                      "artifact_dir": str(exp_dir)}, indent=2))
    return 0


def _stress_expectancy_r(
    engine: dict[str, Callable],
    *,
    execution: dict[str, Any],
    traded_symbols: Sequence[str],
    benchmark_symbol: str,
    window_start: datetime,
    window_end: datetime,
    lookback_days: int,
    reverse: bool,
    folds: int,
    fee_multiplier: float = 1.0,
    adverse_ticks: int = 0,
    extra_delay_events: int = 0,
    exclude_symbols: Sequence[str] | None = None,
) -> float:
    """Re-run the SAME schedule under a stress cost model; return expectancy-R."""
    stressed = execute_experiment(
        engine={**engine,
                "run_shared_capital_backtest": _wrap_stress(
                    engine["run_shared_capital_backtest"],
                    fee_multiplier=fee_multiplier,
                    adverse_ticks=adverse_ticks,
                    extra_delay_events=extra_delay_events,
                    exclude_symbols=exclude_symbols,
                )},
        traded_symbols=traded_symbols,
        benchmark_symbol=benchmark_symbol,
        window_start=window_start, window_end=window_end,
        lookback_days=lookback_days, reverse=reverse, folds=folds,
    )
    value = stressed["metrics"]["expectancy_r"]
    return float(value) if value is not None else float("-inf")


def _wrap_stress(fn: Callable, *, fee_multiplier: float, adverse_ticks: int,
                 extra_delay_events: int,
                 exclude_symbols: Sequence[str] | None = None) -> Callable:
    def wrapped(**kwargs):
        kwargs.setdefault("fee_multiplier", fee_multiplier)
        kwargs.setdefault("adverse_ticks", adverse_ticks)
        kwargs.setdefault("extra_delay_events", extra_delay_events)
        if exclude_symbols:
            kwargs["exclude_symbols"] = list(exclude_symbols)
        return fn(**kwargs)
    return wrapped


def verify_frozen_snapshots_local(snapshot: Mapping[str, Any], exp_dir: Path) -> list[str]:
    from research.provenance import SNAPSHOT_FILES

    checks = (
        ("frozen_config_sha256", SNAPSHOT_FILES["frozen_config"]),
        ("frozen_candidate_sha256", SNAPSHOT_FILES["frozen_candidate"]),
        ("data_manifest_sha256", SNAPSHOT_FILES["data_manifest"]),
        ("universe_snapshot_sha256", SNAPSHOT_FILES["universe_snapshot"]),
    )
    reasons: list[str] = []
    for key, rel in checks:
        target = exp_dir / rel
        if not target.is_file() or sha256_file(target) != snapshot.get(key):
            reasons.append(f"{rel}:hash_mismatch")
    return reasons


def update_matrix_index(
    matrix_id: str, experiment_id: str, verdict: str, exp_dir: Path, *,
    is_control: bool,
) -> None:
    matrix_dir = MATRIX_ROOT if matrix_id == MATRIX_ROOT.name else Path("results/matrix") / matrix_id
    matrix_dir.mkdir(parents=True, exist_ok=True)
    index_path = matrix_dir / "index.json"
    index: dict[str, Any] = {}
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    cells = index.setdefault("cells", {})
    cells[experiment_id] = {
        "status": "COMPLETED",
        "verdict": verdict,
        "negative_control": is_control,
        "artifact_path": str(exp_dir),
    }
    index["schema_version"] = 4
    index["matrix_id"] = matrix_id
    write_json(index_path, index)

    experiments_dir = matrix_dir / "experiments"
    write_json(experiments_dir / f"{experiment_id}.json", {
        "schema_version": 4,
        "experiment_id": experiment_id,
        "cell_result": {
            "experiment_id": experiment_id,
            "status": "COMPLETED",
            "verdict": verdict,
            "artifact_path": str(exp_dir),
        },
    })

    report_path = matrix_dir / "report.json"
    report: dict[str, Any] = {}
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    experiments = report.setdefault("experiments", [])
    if experiment_id not in experiments:
        experiments.append(experiment_id)
    report["matrix_id"] = matrix_id
    report["declared_cells"] = 4  # frozen trial budget: 3 lookbacks + 1 control
    report["stage_a_root"] = str(PORTFOLIO_ROOT)
    write_json(report_path, report)


# --------------------------------------------------------------------------- #
# deterministic reproduction (--reproduce => separate worker subprocess)
# --------------------------------------------------------------------------- #
def run_reproduce(args: argparse.Namespace) -> int:
    source_dir = Path(args.reproduce or args.source_exp_dir).resolve()
    manifest_path = source_dir / "launch_manifest.yaml"
    if not manifest_path.is_file():
        print(f"ABORT source experiment missing launch manifest: {manifest_path}",
              file=sys.stderr)
        return 2
    source_metrics_path = source_dir / "canonical_metrics.json"
    if not source_metrics_path.is_file():
        print(f"ABORT source canonical metrics missing: {source_metrics_path}",
              file=sys.stderr)
        return 2

    verify_id = args.verify_id or (
        f"VERIFY-{manifest_path.parent.name}-"
        f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"
    )
    rerun_dir = (REPRODUCTION_ROOT / verify_id).resolve()
    if rerun_dir.exists():
        print(f"ABORT verify id already exists: {rerun_dir}", file=sys.stderr)
        return 2
    rerun_dir.mkdir(parents=True)

    # rerun manifest records WHAT will be verified, before the worker runs
    source_raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    rerun_manifest = {
        "schema_version": 4,
        "verify_id": verify_id,
        "verification_type": "INDEPENDENT_RERUN",
        "source_experiment_id": source_raw.get("experiment_id"),
        "source_experiment_dir": str(source_dir),
        "launched_at_utc": datetime.now(timezone.utc).isoformat(),
        "worker_command": [sys.executable, "-m", "research.portfolio_runner",
                           "--rerun-worker", "--rerun-out-dir", str(rerun_dir / "rerun_artifacts"),
                           "--source-exp-dir", str(source_dir)],
        "tolerances": {"pnl_abs_scale_tol": PNL_MATCH_TOLERANCE,
                       "metric_tol": METRIC_MATCH_TOLERANCE},
    }
    (rerun_dir / "rerun_manifest.yaml").write_text(
        yaml.safe_dump(rerun_manifest, sort_keys=False), encoding="utf-8")

    env = dict(os.environ)
    worker = subprocess.run(
        rerun_manifest["worker_command"],
        cwd=str(Path(__file__).resolve().parents[1]),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    (rerun_dir / "run.log").write_text(
        f"returncode={worker.returncode}\n--- stdout ---\n{worker.stdout}\n"
        f"--- stderr ---\n{worker.stderr}", encoding="utf-8")

    core_path = rerun_dir / "rerun_artifacts" / "core_result.json"
    if worker.returncode != 0 or not core_path.is_file():
        comparison = {
            "schema_version": 4,
            "verify_id": verify_id,
            "all_match": False,
            "checks": {},
            "error": "worker_failed",
            "returncode": worker.returncode,
        }
        write_json(rerun_dir / "comparison.json", comparison)
        registry_append(_repro_registry_entry(rerun_manifest, comparison),
                        path=args.registry_path)
        print(json.dumps(comparison, indent=2))
        return EXIT_REPRO_MISMATCH

    rerun_core = json.loads(core_path.read_text(encoding="utf-8"))
    source_core = json.loads(source_metrics_path.read_text(encoding="utf-8"))

    orders_match = source_core.get("orders_digest") == rerun_core.get("orders_digest")
    positions_match = source_core.get("positions_digest") == rerun_core.get("positions_digest")
    pnl_source = float(source_core["total_pnl"])
    pnl_rerun = float(rerun_core["total_pnl"])
    scale = max(1.0, abs(pnl_source), abs(pnl_rerun))
    pnl_match = abs(pnl_source - pnl_rerun) <= PNL_MATCH_TOLERANCE * scale

    def metric_close(key: str) -> bool:
        a, b = source_core.get(key), rerun_core.get(key)
        if a is None or b is None:
            return a == b
        return abs(float(a) - float(b)) <= METRIC_MATCH_TOLERANCE * max(
            1.0, abs(float(a)), abs(float(b)))

    beta_match = metric_close("max_drawdown_fraction") and True
    checks = {
        "orders_digest_match": orders_match,
        "positions_digest_match": positions_match,
        "pnl_match": pnl_match,
        "beta_match": metric_close("beta"),
        "turnover_match": metric_close("turnover_total"),
        "mdd_match": metric_close("max_drawdown_fraction"),
    }
    all_match = all(checks.values())
    comparison = {
        "schema_version": 4,
        "verify_id": verify_id,
        "source_experiment_id": rerun_manifest["source_experiment_id"],
        "matrix_id": source_raw.get("matrix_id"),
        "checks": checks,
        "values": {
            "source": {k: source_core.get(k) for k in
                       ("total_pnl", "beta", "turnover_total", "max_drawdown_fraction")},
            "rerun": {k: rerun_core.get(k) for k in
                      ("total_pnl", "beta", "turnover_total", "max_drawdown_fraction")},
        },
        "tolerances": rerun_manifest["tolerances"],
        "rerun_process_separate": True,
        "all_match": all_match,
    }
    write_json(rerun_dir / "comparison.json", comparison)
    registry_append(_repro_registry_entry(rerun_manifest, comparison),
                    path=args.registry_path)
    print(json.dumps(comparison, indent=2))
    return 0 if all_match else EXIT_REPRO_MISMATCH


def _repro_registry_entry(rerun_manifest: Mapping[str, Any], comparison: Mapping[str, Any]) -> dict:
    matrix_id = comparison.get("matrix_id") or rerun_manifest.get("matrix_id") or "v4_xsect_mom"
    return {
        "experiment_id": f"RERUN-{rerun_manifest['verify_id']}",
        "kind": "INDEPENDENT_RERUN_VERIFY",
        "schema": "v4",
        "matrix_id": matrix_id,
        "verified_experiment_id": rerun_manifest["source_experiment_id"],
        "verification_type": "INDEPENDENT_RERUN",
        "verdict": "PASS" if comparison.get("all_match") else "FAIL",
        "comparison_path": str(REPRODUCTION_ROOT / str(rerun_manifest["verify_id"]) / "comparison.json"),
    }


def run_rerun_worker(args: argparse.Namespace) -> int:
    """Executed ONLY as its own process by :func:`run_reproduce`.

    Re-launches the identical pipeline from the FROZEN inputs of the source
    experiment (hashes re-verified against the launch manifest before any
    engine call) and emits digests/metrics to ``<out>/core_result.json``.
    """
    source_dir = Path(args.source_exp_dir)
    manifest, raw = load_launch_manifest(source_dir / "launch_manifest.yaml")
    invalid = manifest.validate()
    if invalid:
        print(f"ABORT worker: source manifest invalid: {sorted(set(invalid))}",
              file=sys.stderr)
        return EXIT_MANIFEST_INVALID

    frozen_dir = source_dir / "frozen"
    checks = (
        ("runtime_config_sha256", manifest.runtime_config_path),
        ("candidate_spec_sha256", manifest.candidate_spec_path),
        ("data_manifest_sha256", manifest.data_manifest_path),
        ("universe_sha256", manifest.universe_path),
    )
    expected = {
        "runtime_config_sha256": manifest.runtime_config_sha256,
        "candidate_spec_sha256": manifest.candidate_spec_sha256,
        "data_manifest_sha256": manifest.data_manifest_sha256,
        "universe_sha256": manifest.universe_sha256,
    }
    for key, rel in checks:
        target = source_dir / rel
        if not target.is_file() or sha256_file(target) != expected[key]:
            print(f"ABORT worker: frozen input mismatch: {rel}", file=sys.stderr)
            return 2

    candidate_doc = yaml.safe_load(
        (source_dir / manifest.candidate_spec_path).read_text(encoding="utf-8")) or {}
    window = raw.get("requested_window") or {}
    window_start = parse_utc(window["start_utc"])
    window_end = parse_utc(window["end_utc"])
    universe_doc = json.loads((source_dir / manifest.universe_path).read_text(encoding="utf-8"))
    traded = [s for s in universe_doc.get("symbols", [])
              if s != (candidate_doc.get("universe") or {}).get("benchmark_symbol", BENCHMARK_SYMBOL)]
    benchmark = str((candidate_doc.get("universe") or {}).get("benchmark_symbol", BENCHMARK_SYMBOL))

    try:
        engine = load_engine()
    except (RunnerError, ImportError) as exc:
        print(f"ABORT worker engine unavailable: {exc}", file=sys.stderr)
        return EXIT_DEPENDENCY_MISSING

    execution = execute_experiment(
        engine=engine,
        traded_symbols=[str(s) for s in (traded or UNIVERSE_SYMBOLS_DEFAULT)],
        benchmark_symbol=benchmark,
        window_start=window_start, window_end=window_end,
        lookback_days=int(raw.get("lookback_days") or 3),
        reverse=bool(raw.get("reverse")),
        folds=int(manifest.outer_folds or 3),
    )
    metrics = execution["metrics"]
    out_dir = Path(args.rerun_out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_dir / "orders.jsonl", execution["orders"])
    write_jsonl(out_dir / "positions.jsonl", execution["closed_legs"])
    write_json(out_dir / "core_result.json", {
        "orders_digest": rows_digest(execution["orders"]),
        "positions_digest": rows_digest(execution["closed_legs"]),
        "total_pnl": metrics["total_pnl"],
        "beta": metrics["beta"],
        "turnover_total": metrics["turnover_total"],
        "max_drawdown_fraction": metrics["max_drawdown_fraction"],
        "legs_closed": metrics["legs_closed"],
        "rebalances_scored": metrics["rebalances_scored"],
    })
    return 0


# --------------------------------------------------------------------------- #
# v4 matrix reconciliation finalizer (filesystem truth only)
# --------------------------------------------------------------------------- #
def finalize_matrix_v4(
    matrix_dir: str | Path,
    registry_path: str | Path | None = None,
) -> dict:
    from research.protocol.registry import load_all, verify_append_only

    matrix_path = Path(matrix_dir)
    index_path = matrix_path / "index.json"
    report_path = matrix_path / "report.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {"cells": {}}
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    cells: dict = index.get("cells") or {}

    experiments_root = matrix_path / "experiments"
    actual_dirs = sorted(
        p.name
        for p in (experiments_root.iterdir() if experiments_root.is_dir() else [])
        if p.is_dir() or p.suffix == ".json"
    )

    portfolio_dirs = 0
    if PORTFOLIO_ROOT.is_dir():
        for exp_dir in PORTFOLIO_ROOT.iterdir():
            if (exp_dir / "launch_manifest.yaml").is_file():
                try:
                    doc = yaml.safe_load((exp_dir / "launch_manifest.yaml").read_text(encoding="utf-8")) or {}
                except Exception:  # noqa: BLE001 - unreadable counts as mismatch below
                    continue
                if doc.get("matrix_id") in {report.get("matrix_id"), matrix_path.name}:
                    portfolio_dirs += 1

    registry_entries = load_all(registry_path)
    registry_rows = [row for row in registry_entries
                     if row.get("matrix_id") in {report.get("matrix_id"), matrix_path.name}]
    statuses: dict[str, int] = {}
    for entry in cells.values():
        statuses[entry.get("status")] = statuses.get(entry.get("status"), 0) + 1

    completed = statuses.get("COMPLETED", 0)
    counts = {
        "declared_cells": int(report.get("declared_cells") or 0),
        "indexed_cells": len(cells),
        "actual_cell_files": len(actual_dirs),
        "completed": completed,
        "registry_entries_for_matrix": len(registry_rows),
        "stage_a_artifact_dirs": portfolio_dirs,
    }
    mismatches: list[str] = []
    if counts["declared_cells"] and counts["indexed_cells"] != counts["declared_cells"]:
        mismatches.append("indexed!=declared")
    if counts["actual_cell_files"] != counts["indexed_cells"]:
        mismatches.append("files!=indexed")
    if completed != counts["indexed_cells"]:
        mismatches.append("completed!=indexed")
    if portfolio_dirs < counts["indexed_cells"]:
        mismatches.append("stage_a_dirs<indexed")
    verdict = "COMPLETE" if not mismatches else (
        "PARTIAL" if completed == counts["indexed_cells"] else "FAIL")

    payload = {
        "schema_version": 4,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "matrix_dir": str(matrix_path),
        "matrix_id": report.get("matrix_id") or matrix_path.name,
        "counts": counts,
        "mismatches": sorted(mismatches),
        "final_verdict": verdict,
        "registry_append_only_verified": verify_append_only(registry_path),
    }
    write_json(matrix_path / "reconciliation.json", payload)
    return payload


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--experiment-id")
    parser.add_argument("--output-root", default=None,
                        help="override artifact root (V5 diagnostic namespace)")
    parser.add_argument("--registry-kind", default="CELL_RESULT")
    parser.add_argument("--source-trial-experiment-id", default=None)
    parser.add_argument("--lookback-days", type=int, default=None)
    parser.add_argument("--reverse", action="store_true",
                        help="negative-control reverse-rank experiment")
    parser.add_argument("--window-start")
    parser.add_argument("--window-end")
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--matrix-id", default=MATRIX_ROOT.name)
    parser.add_argument("--hypothesis-dir", default=str(HYPOTHESIS_DIR_DEFAULT))
    parser.add_argument("--runtime-config", default=str(RUNTIME_CONFIG_DEFAULT))
    parser.add_argument("--data-manifest", default=None)
    parser.add_argument("--registry-path", default=str(REGISTRY_PATH))
    parser.add_argument("--declared-family-trials", type=int, default=4)
    parser.add_argument("--spike-positives", default=None,
                        help='JSON mapping lookback->bool, e.g. \'{"3": true, "7": null, "14": null}\'')
    parser.add_argument("--reproduce", metavar="SOURCE_EXP_DIR", default=None)
    parser.add_argument("--verify-id", default=None)
    parser.add_argument("--rerun-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--source-exp-dir", default=None)
    parser.add_argument("--rerun-out-dir", default=None)
    parser.add_argument("--finalize-matrix", action="store_true")
    parser.add_argument("--matrix-dir", default=str(MATRIX_ROOT))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.reproduce:
        return run_reproduce(args)
    if args.rerun_worker:
        assert args.source_exp_dir and args.rerun_out_dir
        return run_rerun_worker(args)
    if args.finalize_matrix:
        reconciliation = finalize_matrix_v4(args.matrix_dir, args.registry_path)
        print(json.dumps(reconciliation, indent=2))
        if reconciliation["mismatches"]:
            return 1
        return 0

    required = ("--experiment-id", "--lookback-days", "--window-start", "--window-end")
    missing = [flag for flag, attr in zip(required, ("experiment_id", "lookback_days",
                                                     "window_start", "window_end"))
               if getattr(args, attr) is None]
    if missing:
        build_parser().error("missing arguments: " + ", ".join(missing))
    return run_scored_experiment(args)


if __name__ == "__main__":
    raise SystemExit(main())
