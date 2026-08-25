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

V6P repairs (PLAN section 6.3, owner A4): all folds run in ONE chronological
engine pass with the three declared fold intervals handed to the engine
(``folds``), capital carrying across boundaries (F2 start == F1 end);
``risk_mode=RISK_MODE_V1`` is passed on every engine call; and the
settlement/accounting artifact set (``funding_cashflows.jsonl``,
``terminal_positions.jsonl``, ``exposure_control.jsonl``,
``accounting_reconciliation.json``, ``commission_slippage.json``) is
persisted per experiment directory. ``--synthetic-panel <spec.json>`` (or
env ``PORTFOLIO_SYNTHETIC_PANEL``) bypasses the real catalog/funding-bundle
data path with a deterministic hand-computable panel engine for golden
validation only.
"""

from __future__ import annotations

import argparse
import bisect
import dataclasses
import importlib
import inspect
import json
import hashlib
import math
import os
import subprocess
import sys
import tempfile
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
    count_execution_evidence,
    evaluate_parameter_spike,
    evaluate_xg5,
    evaluate_xgates,
)
from research.provenance import snapshot_experiment_inputs
from research.protocol.registry import append as registry_append
from research.accounting import IDENTITY_FORMULA as ACCOUNTING_IDENTITY_FORMULA

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
# PLAN section 6.3 item 4: runtime risk adapter, mirrors
# research.portfolio_engine.RISK_MODE_V1["risk_mode"].
RISK_MODE_V1 = "RISK_MODE_V1"
SYNTHETIC_PANEL_ENV = "PORTFOLIO_SYNTHETIC_PANEL"

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
        btc_list = list((btc or {}).get("BTCUSDT") or [])
        panel = {**daily, "BTCUSDT": btc_list}
        from data.catalog import Catalog as _Catalog

        _cat = _Catalog(CATALOG)
        meta_syms = [s for s in traded if _cat.instrument(s) is not None]

        # V6P N08: measured coverage evidence -- never None on the real path.
        from research.panel import coverage_report as _coverage_report

        blocks = _coverage_report(
            panel, ws, we,
            benchmark_symbol="BTCUSDT",
            funding_bundles_dir=FUNDING_DIR,
            metadata_symbols=meta_syms,
        )
        detail: dict[str, dict] = {}
        day_ns = 86_400_000_000_000
        for sym in sorted(traded):
            stamps = sorted(t for t, _ in (daily.get(sym) or []))
            dupes = len(stamps) - len(set(stamps))
            gaps = sum(1 for a, b in zip(stamps, stamps[1:]) if b - a > day_ns)
            detail[sym] = {"days_present": len(stamps),
                           "duplicate_bars": dupes, "gap_bars": gaps}
        eff_starts = [detail[s]["days_present"] and (daily[s][0][0])
                      for s in traded if daily.get(s)]
        eff_ends = [daily[s][-1][0] for s in traded if daily.get(s)]
        files_sha = {}
        for sym in sorted(traded):
            fpath = Path(FUNDING_DIR) / sym / "funding.json"
            files_sha[sym] = (hashlib.sha256(fpath.read_bytes()).hexdigest()
                              if fpath.is_file() else None)
        return {
            "daily_closes": {**daily},
            "benchmark_daily_closes": btc_list,
            "coverage": {
                "days_per_symbol": {s: len(daily.get(s) or []) for s in traded},
                "btc_days": len(btc_list),
                "blocks": blocks,
                "traded_symbols_detail": detail,
                "requested_window": [ws, we],
                "effective_common_window": [
                    datetime.fromtimestamp(min(eff_starts) / 1e9, tz=timezone.utc).isoformat() if eff_starts else None,
                    datetime.fromtimestamp(max(eff_ends) / 1e9, tz=timezone.utc).isoformat() if eff_ends else None,
                ],
                "funding_bundle_identity": {"path": str(FUNDING_DIR),
                                            "files_sha256": files_sha},
            },
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
        folds=None,
        risk_mode=None,
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
                # V6P N04: declared fold intervals -> ONE continuous pass.
                folds=[(int(a), int(b)) for a, b in (
                    folds or [(int(window_start_ns), int(window_end_ns))])],
                risk_mode=risk_mode,
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

    def compute_target_weights_dispatch(**kwargs):
        wrapped = _signal_family_dispatch(compute_target_weights, FUNDING_DIR)
        return wrapped(**kwargs)

    return {
        "build_daily_panel": build_daily_panel,
        "run_shared_capital_backtest": run_shared_capital_backtest,
        "compute_target_weights": compute_target_weights_dispatch,
    }


def _signal_family_dispatch(base_fn, funding_bundles_dir):
    """PORTFOLIO_SIGNAL_FAMILY=funding_carry routes the rank call to the
    frozen H-XSECT-FUNDING-CARRY-v1 signal; default behavior unchanged."""
    family = os.environ.get("PORTFOLIO_SIGNAL_FAMILY", "").strip()
    if family != "funding_carry":
        return base_fn
    from research.funding_carry import compute_target_weights_funding_carry as _fcf

    def _dispatch(**kwargs):
        closes = kwargs.get("daily_closes") or {}
        traded = sorted(s for s in closes if s != "BTCUSDT")
        return _fcf(
            signal_cutoff_ns=int(kwargs["signal_cutoff_ns"]),
            lookback_days=int(kwargs.get("lookback_days") or 0),
            reverse=bool(kwargs.get("reverse")),
            funding_bundles_dir=funding_bundles_dir,
            traded_symbols=traded,
        )

    return _dispatch


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


# --------------------------------------------------------------------------- #
# synthetic panel injection (PLAN section 6.3 item 10 golden fixtures; A4)
# --------------------------------------------------------------------------- #
def load_synthetic_panel_engine(spec_path: str | Path) -> dict[str, Callable]:
    """Deterministic synthetic-panel engine (golden validation ONLY).

    Bypasses the real catalog + funding-bundle data path entirely: 15m bars,
    funding settlements, instrument metadata and target weights all come
    from a hand-written spec JSON so every order/funding/cost/trim/terminal/
    equity number is computable by hand. Never use for scored evidence.

    Spec schema (all prices float; ts accepts epoch ns or ISO-8601 UTC)::

        {
          "traded_symbols": ["SYMAUSDT", "SYMBUSDT"],
          "benchmark_symbol": "BTCUSDT",
          "initial_capital": 100000.0,
          "fee_taker": 0.0005, "slippage_ticks": 1,
          "tick_size": {"*": 0.01}, "step_size": {"*": 0.001},
          "min_notional": 5.0,
          "bars": [{"symbol": "...", "ts": "...", "open": o, "high": h,
                    "low": l, "close": c, "volume": v?}, ...],
          "funding": [{"symbol": "...", "funding_time_ms": 123,
                       "fundingRate": "0.0001"}, ...],   # optional
          "targets": {"longs": [["SYMAUSDT", 0.25]],
                      "shorts": [["SYMBUSDT", -0.25]]}
        }

    """
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    traded = [str(s) for s in (spec.get("traded_symbols") or [])]
    benchmark = str(spec.get("benchmark_symbol") or BENCHMARK_SYMBOL)
    if not traded:
        raise RunnerError("synthetic panel spec needs traded_symbols")
    initial_capital = float(spec.get("initial_capital") or 100000.0)
    fee_taker_base = float(spec.get("fee_taker", 0.0005))
    slippage_ticks_base = int(spec.get("slippage_ticks", 1))
    day_ns = 86_400_000_000_000

    def _per_symbol_table(name: str, default: float) -> dict[str, float]:
        raw = spec.get(name) or {"*": default}
        if not isinstance(raw, Mapping):
            return {s: float(raw) for s in (*traded, benchmark)}
        star = float(raw.get("*", default))
        return {
            s: float(raw.get(s, star)) for s in (*traded, benchmark)
        }

    tick_size = _per_symbol_table("tick_size", 0.01)
    step_size = _per_symbol_table("step_size", 0.001)
    min_notional = float(spec.get("min_notional", 5.0))

    def _coerce_ts(value: Any) -> int:
        if isinstance(value, (int, float)):
            return int(value)
        return ns(parse_utc(str(value)))

    bars_by_symbol: dict[str, list[tuple[int, float, float, float, float, float]]] = {}
    for row in spec.get("bars") or []:
        sym = str(row["symbol"])
        bars_by_symbol.setdefault(sym, []).append((
            _coerce_ts(row["ts"]),
            float(row["open"]), float(row["high"]),
            float(row["low"]), float(row["close"]),
            float(row.get("volume", 1.0)),
        ))
    for sym in bars_by_symbol:
        bars_by_symbol[sym].sort(key=lambda b: b[0])
    if benchmark not in bars_by_symbol:
        raise RunnerError(f"synthetic panel spec missing {benchmark} bars")

    funding_dir: Path | None = None
    funding_spec = spec.get("funding") or []
    if funding_spec:
        # Materialize engine-native bundles under a throwaway dir so the
        # REAL engine settlement loader runs unchanged.
        funding_dir = Path(tempfile.mkdtemp(prefix="synthetic_funding_"))
        all_ms = [int(r["funding_time_ms"]) for r in funding_spec]
        start_ms, end_ms = min(all_ms), max(all_ms)
        by_sym: dict[str, list[dict]] = {}
        for row in funding_spec:
            by_sym.setdefault(str(row["symbol"]), []).append({
                "fundingTime": str(int(row["funding_time_ms"])),
                "fundingRate": str(row["fundingRate"]),
            })
        for sym, rows in by_sym.items():
            target = funding_dir / sym
            target.mkdir(parents=True)
            (target / "funding.json").write_text(json.dumps({
                "requested_start_ms": start_ms,
                "requested_end_ms": end_ms,
                "rows": sorted(rows, key=lambda r: int(r["fundingTime"])),
            }), encoding="utf-8")
    elif spec.get("funding_enabled"):
        raise RunnerError(
            "synthetic panel funding_enabled=true but no funding rows given")

    targets_raw = spec.get("targets") or {}
    longs_base = [[str(s), float(w)] for s, w in (targets_raw.get("longs") or [])]
    shorts_base = [[str(s), float(w)] for s, w in (targets_raw.get("shorts") or [])]

    def build_daily_panel(symbols, window_start_ns, window_end_ns):
        daily: dict[str, list[tuple[int, float]]] = {}
        for sym in symbols:
            per_day: dict[int, float] = {}
            for bar in bars_by_symbol.get(sym, []):
                if window_start_ns <= bar[0] <= window_end_ns:
                    per_day[bar[0] // day_ns] = bar[4]  # last close of UTC day
            daily[sym] = [(d * day_ns, c) for d, c in sorted(per_day.items())]
        coverage = {
            "days_per_symbol": {s: len(v) for s, v in daily.items()},
            "btc_days": len(daily.get(benchmark, [])),
        }
        return {
            "daily_closes": daily,
            "coverage": coverage,
            "benchmark_clean": True,
            "benchmark_daily_closes": daily.get(benchmark, []),
        }

    def compute_target_weights(daily_closes, signal_cutoff_ns,
                               lookback_days, reverse=False):
        sign = -1.0 if reverse else 1.0
        longs = [[s, sign * w] for s, w in longs_base]
        shorts = [[s, sign * w] for s, w in shorts_base]
        known = set(daily_closes) | set(bars_by_symbol)
        missing = [s for s, _ in (*longs, *shorts) if s not in known]
        if missing:
            return {"status": "SKIP_INCOMPLETE",
                    "reason_code": "synthetic_symbol_missing",
                    "longs": [], "shorts": []}
        return {"status": "OK", "longs": longs, "shorts": shorts}

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
        folds=None,
        risk_mode=None,
    ):
        excluded = set(exclude_symbols or ())
        from research.portfolio_engine import (
            run_shared_capital_backtest as _run_engine,
        )

        schedule_by_cutoff = {
            int(entry["rebalance_ts_ns"]): entry
            for entry in (target_schedule or [])
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

        result = dict(_run_engine(
            bars_15m={s: list(b) for s, b in bars_by_symbol.items()
                      if s not in excluded and s in set(daily_closes)},
            daily_closes=daily_closes,
            weight_fn=weight_fn,
            tick_size={s: v for s, v in tick_size.items()
                       if s in set(daily_closes)},
            step_size={s: v for s, v in step_size.items()
                       if s in set(daily_closes)},
            min_notional=min_notional,
            fee_taker=fee_taker_base * float(fee_multiplier),
            slippage_ticks=slippage_ticks_base + int(adverse_ticks),
            funding_bundles_dir=funding_dir,
            initial_capital=initial_capital,
            folds=[(int(a), int(b)) for a, b in (
                folds or [(int(window_start_ns), int(window_end_ns))])],
            reset_folds=False,
            risk_mode=risk_mode,
            extra_delay_events=int(extra_delay_events),
        ).to_dict())
        summary = dict(result.get("summary") or {})
        summary["pf_position_level"] = {
            "trades": summary.get("trades"),
            "gross_profit": summary.get("gross_profit"),
            "gross_loss": summary.get("gross_loss"),
            "profit_factor": summary.get("profit_factor"),
            "pf_reason": summary.get("pf_reason"),
        }
        summary["turnover_total"] = summary.get("turnover_total_notional")
        summary["expectancy_r"] = None
        result["summary"] = summary
        return result

    def compute_target_weights_dispatch(**kwargs):
        wrapped = _signal_family_dispatch(compute_target_weights, funding_dir)
        return wrapped(**kwargs)

    return {
        "build_daily_panel": build_daily_panel,
        "run_shared_capital_backtest": run_shared_capital_backtest,
        "compute_target_weights": compute_target_weights_dispatch,
    }


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
                                    extra_delay_events=0, folds=None,
                                    risk_mode=None) -> dict per the
            frozen A3/A2 agreement (portfolio_ledger/orders/closed_legs/
            equity_curve/summary/skipped_rebalances/invariants).
            V6P: ``folds`` (declared fold intervals) and ``risk_mode``
            (``RISK_MODE_V1``) are forwarded when the engine supports them;
            legacy engines without those kwargs are tolerated.
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


# --------------------------------------------------------------------------- #
# V6P one-pass WFA helpers (PLAN section 6.3 items 1-3; owner A4)
# --------------------------------------------------------------------------- #
def _supported_kwargs(fn: Callable, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    """Drop kwargs the engine callable does not declare (legacy engines)."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return dict(kwargs)
    if any(p.kind is inspect.Parameter.VAR_KEYWORD
           for p in sig.parameters.values()):
        return dict(kwargs)
    return {k: v for k, v in kwargs.items() if k in sig.parameters}


def _row_ts(row: Mapping[str, Any]) -> int | None:
    for key in ("ts", "rebalance_ts_ns", "execution_bar_ts", "terminal_ts"):
        value = row.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return None


def _fold_tag_for_ts(ts_ns: int | None,
                     fold_edges_ns: Sequence[tuple[int, int]]) -> str | None:
    if ts_ns is None:
        return None
    for index, (start_ns, end_ns) in enumerate(fold_edges_ns, start=1):
        if start_ns <= ts_ns <= end_ns:
            return f"F{index}"
    return None


def _segment_equities(
    curve: Sequence[tuple[int, float]],
    fold_edges_ns: Sequence[tuple[int, int]],
    initial_equity: float | None = None,
) -> list[dict[str, float]]:
    """Per-fold start/end equity read off ONE continuous curve (N04).

    Fold 1 starts from the engine-declared ``initial_equity`` (nothing trades
    before the scored window); every later fold STARTS from the previous
    fold's ENDING equity by construction, so the carry identity
    ``F2_start == F1_end`` holds exactly on a single engine pass — stitched
    100k-reset curves would show full-reset gaps here.
    """
    samples = sorted((int(t), float(e)) for t, e in curve)
    times = [t for t, _ in samples]
    segments: list[dict[str, float]] = []
    prev_end: float | None = None
    for index, (start_ns, end_ns) in enumerate(fold_edges_ns):
        i = bisect.bisect_right(times, end_ns) - 1
        end_eq = samples[i][1] if i >= 0 else prev_end
        j = bisect.bisect_right(times, start_ns) - 1
        if index == 0:
            if initial_equity is not None:
                start_eq: float | None = float(initial_equity)
            elif j >= 0:
                start_eq = samples[j][1]
            else:
                start_eq = samples[0][1] if samples else (end_eq or 0.0)
        else:
            if prev_end is not None:
                start_eq = prev_end
            elif j >= 0:
                start_eq = samples[j][1]
            else:
                start_eq = samples[0][1] if samples else (end_eq or 0.0)
        segments.append({"start_equity": start_eq, "end_equity": end_eq})
        if end_eq is not None:
            prev_end = end_eq
    return segments


def _synthesize_commission_slippage(orders: Sequence[Mapping[str, Any]]) -> dict:
    """Cost totals recomputed from order rows when the engine payload is absent.

    Key names mirror ``research.accounting.build_commission_slippage``.
    """
    executed = [o for o in orders if o.get("rejected_reason") is None]
    rejected = [dict(o) for o in orders if o.get("rejected_reason") is not None]
    return {
        "source": "runner_synthesized_from_orders",
        "executed_orders": len(executed),
        "rejected_orders": rejected,
        "total_commission": math_fsum(float(o.get("fee") or 0.0) for o in executed),
        "total_slippage": math_fsum(
            float(o.get("slippage_cost") or 0.0) for o in executed),
    }


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
    """Run ALL folds in ONE chronological engine pass (V6P N04/N05/N06).

    One target schedule spans every fold interval; the engine receives the
    declared ``folds`` intervals and ``risk_mode=RISK_MODE_V1`` so capital
    carries across boundaries, MDD derives from the continuous equity path,
    and per-bar exposure enforcement stays active. Engines predating the
    ``folds``/``risk_mode`` kwargs are tolerated: unsupported kwargs are
    dropped and the degradation is reported in ``metrics["one_pass"]``.
    """
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

    windows = fold_windows(window_start, window_end, folds)
    fold_edges_ns = [(ns(a), ns(b)) for a, b in windows]
    window_start_ns = ns(window_start)

    all_ranks: list[dict] = []
    skipped_rows: list[dict] = []
    schedule: list[dict] = []
    max_abs_target_weight = 0.0

    # ONE rank loop over ALL folds -> ONE chronological target schedule.
    for index, (fold_start, fold_end) in enumerate(windows, start=1):
        fold_id = f"F{index}"
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

    base_kwargs: dict[str, Any] = {
        "daily_closes": daily_closes,
        "target_schedule": schedule,
        "window_start_ns": window_start_ns,
        "window_end_ns": ns(window_end),
        "fee_multiplier": 1.0,
        "adverse_ticks": 0,
        "extra_delay_events": 0,
        # V6P N04/N05: one pass with declared intervals + runtime risk mode.
        "folds": fold_edges_ns,
        "risk_mode": RISK_MODE_V1,
    }
    import os as _os
    if _os.environ.get("V6P_DEBUG_SCHEDULE"):
        print(f"DEBUG schedule_len={len(schedule)} "
              f"ranks={len(all_ranks)} skipped={len(skipped_rows)} "
              f"daily_keys={sorted(daily_closes)}", file=sys.stderr)
    run_kwargs = _supported_kwargs(call.run_shared_capital_backtest, base_kwargs)
    result = call.run_shared_capital_backtest(**run_kwargs) or {}

    def _tag(rows) -> list[dict]:
        return [
            {**row, "experiment_fold": _fold_tag_for_ts(_row_ts(row), fold_edges_ns)}
            for row in rows
        ]

    all_ledger = _tag(result.get("portfolio_ledger") or [])
    all_orders = _tag(result.get("orders") or [])
    all_legs = _tag(result.get("closed_legs") or [])
    skipped_rows.extend(result.get("skipped_rebalances") or [])
    invariant_rows: list[dict] = list(
        result.get("invariant_checks") or result.get("invariants") or [])

    meta = dict(result.get("meta") or {})
    summary = dict(result.get("summary") or {})

    # Continuous equity path: single pass; anchor the engine-declared
    # initial capital at window start so pre-first-sample PnL and the true
    # MDD peak are never lost.
    curve = sorted((int(t), float(e)) for t, e in (result.get("equity_curve") or []))
    initial_capital = float(
        meta.get("initial_capital") or (curve[0][1] if curve else 0.0))
    declared_initial = meta.get("initial_capital")
    if declared_initial is not None:
        anchor = (window_start_ns, float(declared_initial))
        if (not curve or curve[0][0] > window_start_ns
                or (curve[0][0] == window_start_ns
                    and curve[0][1] != anchor[1])):
            curve.append(anchor)
            curve.sort()
    segments = _segment_equities(
        curve, fold_edges_ns,
        initial_equity=(float(declared_initial)
                        if declared_initial is not None else None))
    starting_equity = segments[0]["start_equity"] if segments else initial_capital
    ending_equity = curve[-1][1] if curve else initial_capital

    fold_pnls: dict[str, float] = {}
    fold_returns: dict[str, float | None] = {}
    fold_exp_rs: dict[str, float | None] = {}
    fold_segments: list[dict] = []
    carry_gaps: list[float] = []
    for index, seg in enumerate(segments):
        fid = f"F{index + 1}"
        pnl = seg["end_equity"] - seg["start_equity"]
        ret = (seg["end_equity"] / seg["start_equity"] - 1.0
               if seg["start_equity"] else None)
        fold_pnls[fid] = pnl
        fold_returns[fid] = ret
        fold_exp_rs[fid] = summary.get("expectancy_r")
        fold_segments.append({"fold_id": fid, **seg, "pnl": pnl, "return": ret})
        if index:
            carry_gaps.append(abs(seg["start_equity"]
                                  - segments[index - 1]["end_equity"]))
    carry_scale = max(1.0, abs(starting_equity), abs(ending_equity))
    carry_max_gap = max(carry_gaps) if carry_gaps else 0.0

    total_pnl = ending_equity - starting_equity
    legs_pnls = [float(leg.get("canonical_pnl", leg.get("pnl", 0.0)) or 0.0) for leg in all_legs]
    merged_pf = _merge_pf([summary.get("pf_position_level") or {}])
    turnover_total = float(summary.get("turnover_total")
                           or summary.get("turnover_total_notional") or 0.0)
    rebalances_scored = int(summary.get("rebalances_scored") or 0)

    from research import portfolio_metrics as pm

    equity_curve = curve
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
    # N04: MDD comes from the CONTINUOUS curve across all folds.
    mdd_fraction, mdd_duration_days = pm.max_drawdown_from_equity(equity_curve)

    gross_max = max(
        [float(summary.get("gross_max") or 0.0),
         float(summary.get("gross_exposure_max") or 0.0)]
        + [abs(float(r.get("gross_exposure", r.get("weight", 0.0)) or 0.0))
           for r in all_ledger if r.get("gross_exposure") is not None]
    ) if all_ledger or summary else 0.0
    net_abs_max = max(
        [abs(float(summary.get("net_abs_max") or 0.0))]
        + [abs(float(r.get("net_exposure", 0.0) or 0.0)) for r in all_ledger
           if r.get("net_exposure") is not None]
    ) if all_ledger or summary else 0.0
    margin_signal_invariants = sum(
        1 for row in invariant_rows
        if str(row.get("check", row.get("type", ""))).lower().find("margin") >= 0
        and row.get("ok") is False
    )
    margin_signal_rows = sum(
        1 for row in invariant_rows if row.get("margin_ok") is False
    )
    aborted_folds = meta.get("aborted_folds") or []
    margin_breach_rows = max(
        margin_signal_invariants, margin_signal_rows, len(aborted_folds))

    exposure_control = list(result.get("exposure_control") or [])
    commission_slippage = dict(result.get("commission_slippage") or {}) or \
        _synthesize_commission_slippage(all_orders)

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
        "fold_edges_utc": [
            {"fold_id": f"F{i}", "start_utc": iso(a), "end_utc": iso(b)}
            for i, (a, b) in enumerate(windows, start=1)
        ],
        "fold_segments": fold_segments,
        "funding_cashflows": list(result.get("funding_cashflows") or []),
        "terminal_positions": list(result.get("terminal_positions") or []),
        "exposure_control": exposure_control,
        "accounting": dict(result.get("accounting") or {}),
        "commission_slippage": commission_slippage,
        "engine_meta": meta,
        "metrics": {
            "total_pnl": total_pnl,
            "starting_equity": starting_equity,
            "ending_equity": ending_equity,
            "fold_pnls": fold_pnls,
            "fold_returns": fold_returns,
            "fold_return_definition": (
                "fold_end_equity / fold_start_equity - 1 "
                "(continuous capital, no reset)"
            ),
            "fold_exp_rs": fold_exp_rs,
            "fold_carry_max_gap": carry_max_gap,
            "fold_carry_ok": bool(carry_max_gap <= 1e-6 * carry_scale),
            "one_pass": {
                "single_engine_call": True,
                "folds_declared": len(fold_edges_ns),
                "folds_kwarg_supported": "folds" in run_kwargs,
                "risk_mode_kwarg_supported": "risk_mode" in run_kwargs,
            },
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
            "risk_mode_requested": RISK_MODE_V1,
            "risk_mode_active": bool(meta.get("risk_mode") == RISK_MODE_V1),
            "exposure_control_rows": len(exposure_control),
            "daily_return_count": len(port_returns),
        },
    }


def math_fsum(values) -> float:
    import math

    return math.fsum(float(v) for v in values)


# --------------------------------------------------------------------------- #
# V6P accounting artifact (PLAN section 6.3 items 7-9; owner A4)
# --------------------------------------------------------------------------- #
def build_v6p_accounting_payload(
    execution: Mapping[str, Any],
    *,
    experiment_id: str,
    matrix_id: str,
) -> dict[str, Any]:
    """Fold+experiment reconciliation payload for ``accounting_reconciliation.json``.

    Layers: (a) engine-native accounting verbatim when present, (b) the
    canonical identity recomputed runner-side from emitted rows
    (``ending - starting == closed_price_pnl + terminal_pnl + funding
    - commissions - slippage - rejection_costs``), (c) funding leg-vs-
    settlement reconciliation, (d) terminal rows vs closed legs + flat final
    book, (e) the continuous fold-carry proof.
    """
    metrics = execution["metrics"]
    legs = execution["closed_legs"]
    orders = execution["orders"]
    ledger = execution["portfolio_ledger"]
    funding_rows = execution["funding_cashflows"]

    def _fsum(rows, key: str) -> float:
        return math_fsum(float(r.get(key) or 0.0) for r in rows)

    executed = [o for o in orders if o.get("rejected_reason") is None]
    regular_legs = [l for l in legs if not l.get("is_terminal")]
    terminal_legs = [l for l in legs if l.get("is_terminal")]
    engine_native_rows = bool(executed and "fee" in executed[0])

    commissions = _fsum(executed, "fee")
    slippage = _fsum(executed, "slippage_cost")
    closed_price_pnl = _fsum(regular_legs, "gross_pnl")
    terminal_pnl = _fsum(terminal_legs, "gross_pnl")
    funding_total = _fsum(funding_rows, "cashflow")
    starting_equity = float(metrics["starting_equity"])
    ending_equity = float(metrics["ending_equity"])
    equity_delta = ending_equity - starting_equity
    residual = equity_delta - (
        closed_price_pnl + terminal_pnl + funding_total
        - commissions - slippage - 0.0
    )
    tol = max(1e-6, 1e-9 * max(1.0, abs(starting_equity), abs(ending_equity)))

    # Funding: settlement-level cashflows must equal leg-level allocations
    # once every leg has closed (flat final book).
    symbols = sorted(
        ({str(r.get("symbol")) for r in funding_rows}
         | {str(l.get("symbol")) for l in legs})
        - {"", "None"}
    ) if (funding_rows or legs) else []
    funding_per_symbol: dict[str, dict] = {}
    for sym in symbols:
        s_total = _fsum([r for r in funding_rows if r.get("symbol") == sym],
                        "cashflow")
        l_total = _fsum([l for l in legs if l.get("symbol") == sym],
                        "funding_allocated")
        funding_per_symbol[sym] = {
            "settlements_total": s_total,
            "legs_allocated_total": l_total,
            "residual": s_total - l_total,
            "ok": bool(abs(s_total - l_total) <= tol),
        }
    funding_legs_total = _fsum(terminal_legs + regular_legs, "funding_allocated")

    terminal_rows = execution["terminal_positions"]
    terminal_counts_ok = len(terminal_rows) == len(terminal_legs)
    terminal_rows_sum = _fsum(terminal_rows, "canonical_pnl")
    terminal_legs_sum = _fsum(terminal_legs, "canonical_pnl")
    last_positions = ledger[-1].get("positions") if ledger else None
    flat_final_book = (last_positions == {}) if last_positions is not None else None

    fold_carry_folds = []
    edges = {e["fold_id"]: e for e in execution.get("fold_edges_utc") or []}
    for seg in execution.get("fold_segments") or []:
        fold_carry_folds.append({
            "fold_id": seg["fold_id"],
            **(edges.get(seg["fold_id"]) or {}),
            "start_equity": seg["start_equity"],
            "end_equity": seg["end_equity"],
            "pnl": seg["pnl"],
            "return": seg["return"],
        })

    return {
        "schema_version": 1,
        "artifact": "accounting_reconciliation",
        "experiment_id": experiment_id,
        "matrix_id": matrix_id,
        "identity_formula": ACCOUNTING_IDENTITY_FORMULA,
        "risk_mode": {
            "requested": metrics.get("risk_mode_requested"),
            "active": metrics.get("risk_mode_active"),
            "exposure_control_rows": metrics.get("exposure_control_rows"),
        },
        "folds_declared": execution.get("fold_edges_utc") or [],
        "equity": {
            "starting_equity": starting_equity,
            "ending_equity": ending_equity,
            "delta": equity_delta,
        },
        "components": {
            "closed_price_pnl": closed_price_pnl,
            "terminal_pnl": terminal_pnl,
            "funding_cashflows": funding_total,
            "commissions": commissions,
            "slippage": slippage,
            "rejection_costs": 0.0,
        },
        "experiment_identity": {
            "source": "runner_recomputed_from_rows",
            "engine_native_rows": engine_native_rows,
            "residual": residual,
            "tolerance": tol,
            "identity_ok": (bool(abs(residual) <= tol)
                            if engine_native_rows else None),
        },
        "engine_accounting": dict(execution.get("accounting") or {}) or None,
        "funding_reconciliation": {
            "settlements_total": funding_total,
            "legs_allocated_total": funding_legs_total,
            "residual": funding_total - funding_legs_total,
            "per_symbol": funding_per_symbol,
            "all_ok": bool(all(v["ok"] for v in funding_per_symbol.values()))
            if funding_per_symbol else None,
        },
        "terminal_reconciliation": {
            "terminal_rows": len(terminal_rows),
            "terminal_closed_legs": len(terminal_legs),
            "counts_ok": bool(terminal_counts_ok),
            "rows_canonical_sum": terminal_rows_sum,
            "legs_canonical_sum": terminal_legs_sum,
            "sums_ok": bool(abs(terminal_rows_sum - terminal_legs_sum) <= tol),
            "flat_final_book": flat_final_book,
        },
        "fold_carry": {
            "definition": (
                "F(i+1).start_equity == F(i).end_equity on ONE continuous "
                "pass; stitched 100k resets would violate this"
            ),
            "max_gap": metrics.get("fold_carry_max_gap"),
            "carry_ok": metrics.get("fold_carry_ok"),
            "folds": fold_carry_folds,
        },
    }


# --------------------------------------------------------------------------- #
# gates / scorecard assembly
# --------------------------------------------------------------------------- #
def assemble_xg1_measured_rows(
    execution: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Build REAL signal->fill pairs from emitted rows (V6P N07; owner A5).

    One row per engine order (executed OR rejected): ``fill_ts`` is the
    order's own execution-bar timestamp and ``signal_ts`` is the LATEST
    runner rank cutoff at or before that bar -- both MEASURED from artifact
    rows, never hand-built booleans. A row with either timestamp missing is
    KEPT (it counts toward the fail-closed ``missing_ts`` counter) instead
    of being dropped or padded.
    """
    stamps = sorted({
        int(row["signal_cutoff_ns"])
        for row in (execution.get("signal_ranks") or [])
        if row.get("signal_cutoff_ns") is not None
    })
    rows: list[dict[str, Any]] = []
    for order in execution.get("orders") or []:
        fill_ts = _row_ts(order)
        signal_ts: int | None = None
        if fill_ts is not None and stamps:
            index = bisect.bisect_right(stamps, int(fill_ts)) - 1
            if index >= 0:
                signal_ts = stamps[index]
        rows.append({
            "symbol": order.get("symbol"),
            "kind": order.get("kind"),
            "side": order.get("side"),
            "signal_ts": signal_ts,
            "fill_ts": None if fill_ts is None else int(fill_ts),
        })
    return rows


def build_gate_inputs(
    execution: dict[str, Any],
    *,
    declared_symbols: Sequence[str],
    required_days: int,
    warmup_boundaries: Mapping[str, str | None],
    stress_report: Mapping[str, Any] | None = None,
    independent_reproduction: IndependentReproductionResult | None = None,
    artifact_integrity: ArtifactIntegrityResult | None = None,
    legacy_boolean_compat: bool = False,
) -> dict[str, Any]:
    """Assemble XG gate inputs from MEASURED runner evidence.

    V6P N07: the scored path supplies REAL execution-ledger rows assembled
    from ``execution['orders']`` + rank timestamps; XG1 is then evaluated by
    counting violations (:func:`research.protocol.gates.evaluate_xg1_measured`).
    The legacy hand-built boolean struct is NOT emitted anymore unless
    ``legacy_boolean_compat=True`` -- and even then it is flagged
    ``not_scored_usable`` so it can never back a scored promotion.
    """
    metrics = execution["metrics"]
    folds_block = [
        {"fold_id": fid, "pnl": pnl,
         "exp_r": metrics["fold_exp_rs"].get(fid)}
        for fid, pnl in metrics["fold_pnls"].items()
    ]

    # Family-aware drop-one evidence from the unconditional stress report
    # (V6P N10); R-normalized stress fields stay None -- this portfolio
    # family has NO R normalization (MISSING_R_NORMALIZATION, V5 F07).
    dropone_symbol_clean: bool | None = None
    dropone_fold_clean: bool | None = None
    if isinstance(stress_report, Mapping):
        flags = derive_dropone_clean_flags(stress_report)
        dropone_symbol_clean = flags["dropone_symbol_clean"]
        dropone_fold_clean = flags["dropone_fold_clean"]

    robustness = {
        # expectancy-R stress metrics are retired for this family (N10);
        # family-aware per-variant metrics live in stress_report.json.
        "fee50_exp_r": None,
        "twotick_exp_r": None,
        "extradelay_exp_r": None,
        "dropone_symbol_clean": dropone_symbol_clean,
        "dropone_fold_clean": dropone_fold_clean,
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

    gate_inputs: dict[str, Any] = {
        "coverage": _coverage_payload_from_execution(
            execution, declared_symbols=declared_symbols,
            required_days=required_days,
        ),
        "declared_symbols": list(declared_symbols),
        # V6P N07: MEASURED XG1 evidence -- evaluate_xgates routes these
        # through evaluate_xg1_measured (violation counting), never the
        # boolean struct. Stateless rank pipeline => empty transform
        # registry records not_applicable_with_reason honestly.
        "execution_ledger_rows": assemble_xg1_measured_rows(execution),
        "transform_registry": {},
        "warmup_boundaries": dict(warmup_boundaries),
        "artifact_integrity": artifact_integrity,
        "independent_reproduction": independent_reproduction,
        "stage_a": stage_a,
        "robustness": robustness,
        "risk": risk,
    }
    if legacy_boolean_compat:
        # NON-SCORED legacy compatibility ONLY: hand-built booleans kept for
        # old consumers, explicitly flagged not usable for scored promotion.
        gate_inputs["pit_evidence"] = {
            "not_scored_usable": True,
            "features_completed_before_signal": True,
            "signal_before_every_fill": True,
            "membership_tie_deterministic": True,
            "execution_bar_excluded": True,
            "warmup_boundaries": dict(warmup_boundaries),
        }
    return gate_inputs


def _coverage_payload_from_execution(
    execution: Mapping[str, Any],
    *,
    declared_symbols: Sequence[str],
    required_days: int,
) -> dict[str, Any]:
    raw = execution.get("panel_coverage") or {}
    detail = raw.get("traded_symbols_detail") or {}
    blocks = raw.get("blocks") or {}
    fund_blocks = blocks.get("funding_coverage") or {}
    meta_blocks = blocks.get("metadata_coverage") or {}
    req_win = raw.get("requested_window") or [None, None]
    req_start_day = str(req_win[0])[:10] if req_win[0] else None
    req_end_day = str(req_win[1])[:10] if req_win[1] else None
    legacy_days = dict(raw.get("days_per_symbol") or {})

    bench_days = int(
        (blocks.get("benchmark_coverage") or {}).get(BENCHMARK_SYMBOL)
        or raw.get("btc_days") or 0)
    bench_floor = max(1, math.ceil(0.98 * required_days))
    bench_clean = bool(execution.get("benchmark_btc_clean")) and (
        bench_days >= bench_floor)

    traded: dict[str, Any] = {}
    for sym in declared_symbols:
        d = detail.get(sym) or {}
        f = fund_blocks.get(sym) or {}
        settlements = int(f.get("settlements") or 0)
        first, last = f.get("first"), f.get("last")
        covers = bool(
            settlements > 0 and first and last and req_start_day and req_end_day
            and str(first) <= req_start_day and str(last) >= req_end_day)
        entry: dict[str, Any] = {
            "days_present": int(d.get("days_present",
                                      legacy_days.get(sym, 0)) or 0),
            "funding": {
                "bundle_present": settlements > 0,
                "covers_declared_window": covers,
                "settlements": settlements,
                "first": first, "last": last,
            },
            "instrument_metadata_present": bool(meta_blocks.get(sym)),
        }
        if "duplicate_bars" in d:
            entry["duplicate_bars"] = int(d["duplicate_bars"] or 0)
        if "gap_bars" in d:
            entry["gap_bars"] = int(d["gap_bars"] or 0)
        traded[sym] = entry

    return {
        "required_days": required_days,
        "traded_symbols": traded,
        "benchmark": {
            "symbol": BENCHMARK_SYMBOL,
            "days_present": bench_days,
            "clean": bench_clean,
        },
        "requested_window": list(req_win),
        "effective_common_window": raw.get("effective_common_window"),
        "funding_bundle_identity": raw.get("funding_bundle_identity"),
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
_FINALIZED_EXP_DIRS: set[Path] = set()


class HashesFinalViolation(RuntimeError):
    """Raised when a finalized experiment directory is written again."""


def _iter_artifact_files(exp_dir: Path, skip: Sequence[str]) -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    for path in sorted(exp_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(exp_dir).as_posix()
        if rel in skip:
            continue
        files.append((rel, path))
    return files


def _serialize_hash_manifest(hashes: Mapping[str, str]) -> str:
    return json.dumps({"schema_version": 4, "hashes": hashes},
                      indent=2, sort_keys=True, default=str)


def append_run_log(log_path: Path, message: str) -> None:
    """Append one UTC-stamped line; refuse once the directory is finalized."""
    if log_path.resolve().parent in _FINALIZED_EXP_DIRS:
        raise HashesFinalViolation(
            f"run.log append refused, experiment already finalized: {log_path}")
    stamp = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def write_artifact_hashes(exp_dir: Path, skip: Sequence[str] = ("artifact_hashes.json",)) -> Path:
    """Hash every regular file under ``exp_dir`` and write the manifest LAST.

    D1 fail-closed contract: all data files and ``run.log`` must be closed
    before this call; afterwards :func:`append_run_log` refuses appends. If
    ``artifact_hashes.json`` already exists, this is an idempotent no-op
    returning the existing path only when the recomputed manifest is
    byte-identical -- otherwise it raises instead of rewriting.
    """
    exp_dir = Path(exp_dir)
    if not exp_dir.is_dir():
        raise RunnerError(f"artifact dir missing: {exp_dir}")
    serialized = _serialize_hash_manifest(
        {rel: sha256_file(path) for rel, path in _iter_artifact_files(exp_dir, skip)})
    out = exp_dir / "artifact_hashes.json"
    if out.is_file() and out.read_text(encoding="utf-8") != serialized:
        raise HashesFinalViolation(
            f"artifact_hashes.json already finalized with different content: {out}")
    if not out.is_file():
        out.write_text(serialized, encoding="utf-8")
    _FINALIZED_EXP_DIRS.add(out.parent.resolve())
    return out


def verify_artifact_hashes(
    exp_dir: Path,
    skip: Sequence[str] = ("artifact_hashes.json",),
    extra_skip: Sequence[str] = ("ABORTED.json", "REGISTRATION_REPAIRED.json"),
) -> list[str]:
    """Separate-reader check (pure read): recompute hashes from disk and
    return one reason string per mismatched, missing, or unlisted regular
    file (same skip rules as the writer); empty list means verified."""
    exp_dir = Path(exp_dir)
    out = exp_dir / "artifact_hashes.json"
    if not out.is_file():
        return [f"{out.name}:missing_manifest"]
    try:
        recorded = json.loads(out.read_text(encoding="utf-8"))["hashes"]
    except (OSError, ValueError, KeyError, TypeError):
        return [f"{out.name}:unreadable_manifest"]
    reasons: list[str] = []
    seen: set[str] = set()
    skip_all = tuple(skip) + tuple(extra_skip)
    for rel, path in _iter_artifact_files(exp_dir, skip_all):
        seen.add(rel)
        if rel not in recorded:
            reasons.append(f"{rel}:unlisted")
        elif sha256_file(path) != recorded[rel]:
            reasons.append(f"{rel}:hash_mismatch")
    reasons.extend(f"{rel}:missing" for rel in sorted(set(recorded) - seen))
    return sorted(reasons)


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
    if getattr(args, "synthetic_panel", None):
        extra_manifest_fields["synthetic_panel_path"] = str(
            Path(args.synthetic_panel).resolve())

    log_path = exp_dir / "run.log"

    def _log(message: str) -> None:
        append_run_log(log_path, message)

    # V6P N01/N02/N03: committed-baseline provenance block + fail-closed
    # preflight when enforcement is enabled (real launches set the env).
    provenance_block: dict[str, Any] = {
        "baseline_file": None,
        "baseline_sha256": None,
        "attestation_file": None,
        "attestation_sha256": None,
        "preflight": "NOT_ENFORCED",
    }
    if os.environ.get("V6P_ENFORCE_PROVENANCE") == "1":
        from research.provenance_v6p import (
            ATTESTATION_FILENAME,
            BASELINE_FILENAME,
            validate_launch_provenance,
        )
        base_p = Path("research/audits/v6p") / BASELINE_FILENAME
        att_p = Path("research/audits/v6p") / ATTESTATION_FILENAME
        reasons = validate_launch_provenance(
            Path.cwd(),
            baseline_path=base_p,
            attestation_path=att_p,
            launch_head=snapshot["git_commit_at_launch"],
            dirty=None,  # validator applies the declared-exemption scan
            first_launch_started_utc=snapshot["run_started_utc"],
        )
        if reasons:
            _log(f"ABORT provenance_preflight_failed: {reasons}")
            print(f"ABORT provenance preflight failed: {reasons}",
                  file=sys.stderr)
            return EXIT_DEPENDENCY_MISSING
        provenance_block = {
            "baseline_file": str(base_p),
            "baseline_sha256": sha256_file(base_p),
            "attestation_file": str(att_p),
            "attestation_sha256": sha256_file(att_p),
            "preflight": "PASS",
        }
    extra_manifest_fields["provenance"] = provenance_block
    _log(f"launch experiment={args.experiment_id} matrix={args.matrix_id}")
    _log(f"lock evidence source={identity['lock_source']} "
         f"locked_at={identity['locked_at_utc']}")
    dump_launch_manifest(manifest, extra_manifest_fields, exp_dir / "launch_manifest.yaml")
    _log("launch_manifest.yaml written BEFORE engine execution (finish=null)")

    # ---- 3. engine -------------------------------------------------------- #
    synthetic_panel = (
        getattr(args, "synthetic_panel", None)
        or os.environ.get(SYNTHETIC_PANEL_ENV, "").strip()
        or None
    )
    try:
        if synthetic_panel:
            engine = load_synthetic_panel_engine(synthetic_panel)
            _log(f"SYNTHETIC PANEL engine active (golden validation only): "
                 f"{synthetic_panel}")
        else:
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
    # ---- 4. UNCONDITIONAL family-aware stress suite (V6P N10/C13) --------- #
    # Runs for EVERY experiment -- regardless of the base XG3 verdict or
    # reverse-control status. The base verdict is recorded for the report
    # but NEVER gates execution; a negative base edge stays REJECTED.
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
    base_xg3_verdict = next(
        (row.verdict.value for row in base_rows
         if row.gate == XGateId.XG3_STAGE_A_PORTFOLIO),
        None,
    )
    _log(f"base XG3 verdict={base_xg3_verdict} "
         f"(stress execution is unconditional and diagnostic-only)")
    stress_report = execute_stress_suite(
        engine, execution=execution,
        traded_symbols=identity["traded_symbols"],
        benchmark_symbol=identity["benchmark_symbol"],
        window_start=window_start, window_end=window_end,
        lookback_days=args.lookback_days, reverse=bool(args.reverse),
        folds=args.folds, base_edge_verdict=base_xg3_verdict, log=_log,
    )

    # ---- 5. gates + scorecard --------------------------------------------- #
    gate_inputs = build_gate_inputs(
        execution, declared_symbols=identity["traded_symbols"],
        required_days=scored_days,
        warmup_boundaries=warmup_boundaries,
        stress_report=stress_report,
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
    # V6P N06 (PLAN 6.3 item 6): engine-native settlement/accounting set.
    write_jsonl(exp_dir / "funding_cashflows.jsonl", execution["funding_cashflows"])
    write_jsonl(exp_dir / "terminal_positions.jsonl", execution["terminal_positions"])
    write_jsonl(exp_dir / "exposure_control.jsonl", execution["exposure_control"])
    write_json(exp_dir / "accounting_reconciliation.json",
               build_v6p_accounting_payload(
                   execution, experiment_id=args.experiment_id,
                   matrix_id=args.matrix_id))
    write_json(exp_dir / "commission_slippage.json",
               execution["commission_slippage"])
    # V6P N10: family-aware stress evidence persisted even when the base
    # edge fails (diagnostic-only; never rescue logic).
    write_json(exp_dir / "stress_report.json", stress_report)

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
        # V6P N07: measured XG1 counters recomputed from the assembled
        # execution-ledger rows (external-reader recheck support).
        "xg1_measured_counters": count_execution_evidence(
            gate_inputs["execution_ledger_rows"]).to_dict(),
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

    verify_reasons = verify_frozen_snapshots_local(snapshot, exp_dir)
    if verify_reasons:
        _log(f"WARN frozen snapshot verification issues: {verify_reasons}")
    # D1 contract: run.log is complete BEFORE any hash computation; a later
    # _log() here would raise HashesFinalViolation (fail closed).
    _log(f"verdict={verdict} scorecard_total={scorecard['total']} "
         f"mode={scorecard['score_mode']} hashes=artifact_hashes.json")
    artifact_hash_path = write_artifact_hashes(exp_dir)
    integrity_reasons = verify_artifact_hashes(exp_dir)
    leg_pnl_sum = math.fsum(
        float(leg.get("pnl", 0.0)) for leg in execution["closed_legs"])
    total_pnl = float(execution["metrics"]["total_pnl"])
    legs_count_match = (
        len(execution["closed_legs"]) == int(execution["metrics"]["legs_closed"]))
    identity_ok = abs(leg_pnl_sum - total_pnl) <= 1e-6 and legs_count_match
    canonical_written = json.loads(
        (exp_dir / "canonical_metrics.json").read_text(encoding="utf-8"))
    report_index_ok = (
        canonical_written.get("positions_digest")
        == rows_digest(execution["closed_legs"]))

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
        "inprocess_integrity": {
            "manifest_verify_reasons": integrity_reasons,
            "leg_pnl_identity_ok": identity_ok,
            "report_index_reconcile_ok": report_index_ok,
            "authoritative_verdict_source": "external_reader",
        },
    }, path=args.registry_path)

    update_matrix_index(args.matrix_id, args.experiment_id, verdict, exp_dir,
                        is_control=is_control)
    print(json.dumps({"experiment_id": args.experiment_id, "verdict": verdict,
                      "scorecard_total": scorecard["total"],
                      "score_mode": scorecard["score_mode"],
                      "artifact_dir": str(exp_dir)}, indent=2))
    return 0


# --------------------------------------------------------------------------- #
# V6P N10 unconditional family-aware stress suite (PLAN section 6.4; owner A5)
# --------------------------------------------------------------------------- #
#: Family-aware stress metric set -- NO expectancy-R anywhere (this
#: shared-capital portfolio family has no R normalization).
STRESS_METRIC_KEYS = (
    "canonical_pnl",
    "profit_factor",
    "funding_pnl",
    "fold_returns",
    "mdd_continuous",
    "max_gross_exposure",
)


def _pf_from_legs(legs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    pnl_values = [
        float(leg.get("canonical_pnl", leg.get("pnl", 0.0)) or 0.0)
        for leg in legs
    ]
    gross_profit = math_fsum(v for v in pnl_values if v > 0)
    gross_loss = abs(math_fsum(v for v in pnl_values if v < 0))
    if not pnl_values:
        return {"profit_factor": None, "pf_reason": "no_trades"}
    if gross_loss > 0:
        return {"profit_factor": gross_profit / gross_loss, "pf_reason": None}
    return {"profit_factor": None, "pf_reason": "no_losing_positions"}


def family_metrics(execution: Mapping[str, Any]) -> dict[str, Any]:
    """Canonical family metrics for one (base or stressed) execution."""
    metrics = execution["metrics"]
    pf_block = metrics.get("pf_position_level") or {}
    return {
        "canonical_pnl": float(metrics["total_pnl"]),
        "profit_factor": pf_block.get("profit_factor"),
        "pf_reason": pf_block.get("pf_reason"),
        "funding_pnl": math_fsum(
            float(row.get("cashflow") or 0.0)
            for row in (execution.get("funding_cashflows") or [])
        ),
        "fold_returns": dict(metrics.get("fold_returns") or {}),
        "mdd_continuous": metrics.get("max_drawdown_fraction"),
        "max_gross_exposure": metrics.get("gross_max"),
    }


def _drop_one_fold_metrics(
    execution: Mapping[str, Any], fold_id: str
) -> dict[str, Any]:
    """Family metrics recomputed from base rows EXCLUDING one fold's rows.

    Fold membership uses the runner-tagged ``experiment_fold`` on closed
    legs / funding rows. Path-dependent quantities (continuous MDD, peak
    gross exposure) are NOT recomputable from a filtered row population and
    stay honestly null instead of being faked.
    """
    legs = [
        leg for leg in (execution.get("closed_legs") or [])
        if leg.get("experiment_fold") != fold_id
    ]
    funding_rows = [
        row for row in (execution.get("funding_cashflows") or [])
        if row.get("experiment_fold", row.get("fold_id")) != fold_id
    ]
    fold_returns = {
        fid: ret for fid, ret in
        ((execution.get("metrics") or {}).get("fold_returns") or {}).items()
        if fid != fold_id
    }
    removed = [
        float(leg.get("canonical_pnl", leg.get("pnl", 0.0)) or 0.0)
        for leg in (execution.get("closed_legs") or [])
        if leg.get("experiment_fold") == fold_id
    ]
    result = dict(_pf_from_legs(legs))
    result.update({
        "canonical_pnl": math_fsum(
            float(leg.get("canonical_pnl", leg.get("pnl", 0.0)) or 0.0)
            for leg in legs
        ),
        "removed_fold_canonical_pnl": math_fsum(removed),
        "funding_pnl": math_fsum(
            float(row.get("cashflow") or 0.0) for row in funding_rows
        ),
        "fold_returns": fold_returns,
        "mdd_continuous": None,
        "mdd_reason": "path_dependent_not_recomputable_after_fold_removal",
        "max_gross_exposure": None,
        "exposure_reason": "path_dependent_not_recomputable_after_fold_removal",
    })
    return result


def derive_dropone_clean_flags(stress_report: Mapping[str, Any]) -> dict[str, bool | None]:
    """Drop-one cleanliness from CANONICAL PnL sign flips (never expectancy_r).

    ``None`` means the variants never executed (absence of evidence is not a
    negative result); otherwise clean iff no dropped variant flips the sign
    of canonical PnL relative to the baseline.
    """
    baseline = stress_report.get("baseline") or {}
    base_pnl = baseline.get("canonical_pnl")
    variants = stress_report.get("variants") or {}

    def _clean(prefix: str) -> bool | None:
        names = [name for name in variants if name.startswith(prefix)]
        if not names or base_pnl is None:
            return None
        flips = [
            name for name in names
            if isinstance(variants[name], Mapping)
            and variants[name].get("canonical_pnl") is not None
            and (float(variants[name]["canonical_pnl"]) > 0)
            != (float(base_pnl) > 0)
        ]
        incomplete = any(
            not isinstance(variants[name], Mapping)
            or variants[name].get("canonical_pnl") is None
            for name in names
        )
        return None if incomplete else not flips

    return {
        "dropone_symbol_clean": _clean("drop_one_symbol:"),
        "dropone_fold_clean": _clean("drop_one_fold:"),
    }


def run_stressed_execution(
    engine: dict[str, Callable],
    *,
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
) -> dict[str, Any]:
    """Re-run the SAME schedule under a stressed cost/universe model."""
    return execute_experiment(
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


def execute_stress_suite(
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
    base_edge_verdict: str | None = None,
    log: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Execute EVERY variant family UNCONDITIONALLY (V6P N10; C13/C14).

    Fee x1.5, adverse-two-ticks, extra-one-event-delay, drop-one-symbol
    (each traded symbol) and drop-one-fold all run regardless of the base
    XG3 verdict or reverse-control status; each stressed rerun is measured
    with the family-aware metric set (canonical_pnl, profit_factor,
    funding_pnl, fold_returns, mdd_continuous, max_gross_exposure) -- never
    expectancy_r. The report is DIAGNOSTIC evidence: a negative base edge
    stays REJECTED and stress results can never rescue it.
    """

    def _log(message: str) -> None:
        if log is not None:
            log(message)

    report: dict[str, Any] = {
        "schema_version": 1,
        "artifact": "stress_report",
        "executed_unconditionally": True,
        "base_edge_verdict": base_edge_verdict,
        "diagnostic_only": (
            "stress evidence is diagnostic; a negative base edge remains "
            "REJECTED regardless of variant outcomes"
        ),
        "metric_set": list(STRESS_METRIC_KEYS),
        "expectancy_r_note": (
            "MISSING_R_NORMALIZATION: expectancy_r deliberately absent from "
            "the stress metric set for this portfolio family"
        ),
        "baseline": family_metrics(execution),
        "variants": {},
    }

    variants: tuple[tuple[str, dict[str, Any]], ...] = (
        ("fee_x1_5", {"fee_multiplier": 1.5}),
        ("adverse_two_ticks", {"adverse_ticks": 2}),
        ("extra_one_event_delay", {"extra_delay_events": 1}),
    ) + tuple(
        (f"drop_one_symbol:{sym}", {"exclude_symbols": [sym]})
        for sym in traded_symbols
    )
    for name, kwargs in variants:
        try:
            stressed = run_stressed_execution(
                engine,
                traded_symbols=traded_symbols,
                benchmark_symbol=benchmark_symbol,
                window_start=window_start, window_end=window_end,
                lookback_days=lookback_days, reverse=reverse, folds=folds,
                **kwargs,
            )
        except (TypeError, ValueError) as exc:
            # Per-variant degradation: an unsupported stress kwarg records
            # the failure but never silently cancels the remaining variants.
            report["variants"][name] = {"executed": False, "error": str(exc)}
            _log(f"stress {name} FAILED: {exc}")
            continue
        entry = {"executed": True, **kwargs}
        entry.update(family_metrics(stressed))
        report["variants"][name] = entry
        _log(f"stress {name}: canonical_pnl={entry['canonical_pnl']}")

    for fold_id in (execution["metrics"].get("fold_pnls") or {}):
        entry = {"executed": True, "dropped_fold": fold_id}
        entry.update(_drop_one_fold_metrics(execution, fold_id))
        report["variants"][f"drop_one_fold:{fold_id}"] = entry
        _log(f"stress drop_one_fold:{fold_id}: "
             f"canonical_pnl={entry['canonical_pnl']}")
    return report


def _wrap_stress(fn: Callable, *, fee_multiplier: float, adverse_ticks: int,
                 extra_delay_events: int,
                 exclude_symbols: Sequence[str] | None = None) -> Callable:
    def wrapped(**kwargs):
        # Stress values OVERRIDE base kwargs unconditionally: execute_experiment
        # always emits its own fee=1.0/ticks=0/delay=0, so a setdefault here
        # would silently no-op every cost stress.
        kwargs["fee_multiplier"] = fee_multiplier
        kwargs["adverse_ticks"] = adverse_ticks
        kwargs["extra_delay_events"] = extra_delay_events
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
    if not env.get(SYNTHETIC_PANEL_ENV) and source_raw.get("synthetic_panel_path"):
        env[SYNTHETIC_PANEL_ENV] = str(source_raw["synthetic_panel_path"])
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

    # ---- V6P N11 FULL-SURFACE comparison ---------------------------------- #
    #: (component name, artifact filename) digest pairs -- every scored
    #: surface must match for ``all_match`` (exact digests; deterministic).
    COMPONENT_ARTIFACTS: tuple[tuple[str, str], ...] = (
        ("signals", "signal_ranks.jsonl"),
        ("orders", "orders.jsonl"),
        ("positions", "positions.jsonl"),
        ("ledger", "portfolio_ledger.jsonl"),
        ("funding_cashflows", "funding_cashflows.jsonl"),
        ("terminal_positions", "terminal_positions.jsonl"),
        ("exposure_control", "exposure_control.jsonl"),
        ("accounting_reconciliation", "accounting_reconciliation.json"),
        ("commission_slippage", "commission_slippage.json"),
        ("stress_report", "stress_report.json"),
        ("canonical_metrics", "canonical_metrics.json"),
    )
    rerun_art_dir = rerun_dir / "rerun_artifacts"
    components: dict[str, dict[str, Any]] = {}
    checks: dict[str, bool] = {
        "orders_digest_match": orders_match,
        "positions_digest_match": positions_match,
        "pnl_match": pnl_match,
        "beta_match": metric_close("beta"),
        "turnover_match": metric_close("turnover_total"),
        "mdd_match": metric_close("max_drawdown_fraction"),
    }

    def _sha(path: Path) -> str | None:
        return sha256_file(path) if path.is_file() else None

    for component, filename in COMPONENT_ARTIFACTS:
        src_path = source_dir / filename
        dst_path = rerun_art_dir / filename
        src_digest, dst_digest = _sha(src_path), _sha(dst_path)
        if src_digest is None or dst_digest is None:
            match = False
            reason = ("missing_source_artifact" if src_digest is None
                      else "missing_rerun_artifact")
        else:
            match = src_digest == dst_digest
            reason = None if match else "digest_mismatch"
        checks[f"{component}_match"] = match
        components[component] = {
            "filename": filename,
            "match": match,
            **({"reason": reason} if reason else {}),
            "source_sha256": src_digest,
            "rerun_sha256": dst_digest,
        }

    # Canonical metric detail: fold returns compared fold-by-fold within the
    # frozen tolerance (the byte-level digest above must ALSO hold).
    source_fold_returns = source_core.get("fold_returns") or {}
    rerun_fold_returns = rerun_core.get("fold_returns") or {}

    def _fold_returns_close() -> bool:
        if set(map(str, source_fold_returns)) != set(map(str, rerun_fold_returns)):
            return False
        return all(metric_close_pair(source_fold_returns[k],
                                     rerun_fold_returns[str(k)])
                   for k in source_fold_returns)

    def metric_close_pair(a: Any, b: Any) -> bool:
        if a is None or b is None:
            return a == b
        return abs(float(a) - float(b)) <= METRIC_MATCH_TOLERANCE * max(
            1.0, abs(float(a)), abs(float(b)))

    checks["fold_returns_match"] = _fold_returns_close()
    components["fold_returns"] = {"match": checks["fold_returns_match"],
                                  "source": source_fold_returns,
                                  "rerun": rerun_fold_returns}

    # Gate verdicts MAP (gate id -> verdict string), not free-text reasons.
    try:
        source_gate_doc = json.loads(
            (source_dir / "gate_result.json").read_text(encoding="utf-8"))
        source_gate_map = {
            str(row.get("gate")): str(row.get("verdict"))
            for row in (source_gate_doc.get("gates") or [])
        }
        gate_reason = None
    except (OSError, ValueError):
        source_gate_map = {}
        gate_reason = "missing_or_unreadable_source_gate_result"
    rerun_gate_map = {
        str(k): str(v) for k, v in (rerun_core.get("gate_verdicts") or {}).items()
    }
    checks["gate_result_verdicts_match"] = (
        source_gate_map == rerun_gate_map and bool(source_gate_map))
    components["gate_result_verdicts"] = {
        "match": checks["gate_result_verdicts_match"],
        **({"reason": gate_reason} if gate_reason else {}),
        "source": source_gate_map,
        "rerun": rerun_gate_map,
    }

    try:
        source_scorecard_doc = json.loads(
            (source_dir / "scorecard.json").read_text(encoding="utf-8"))
        scorecard_total_source = source_scorecard_doc.get("total")
        scorecard_reason = None
    except (OSError, ValueError):
        scorecard_total_source = None
        scorecard_reason = "missing_or_unreadable_source_scorecard"
    scorecard_total_rerun = rerun_core.get("scorecard_total")
    checks["scorecard_totals_match"] = (
        scorecard_reason is None
        and scorecard_total_source == scorecard_total_rerun)
    components["scorecard_totals"] = {
        "match": checks["scorecard_totals_match"],
        **({"reason": scorecard_reason} if scorecard_reason else {}),
        "source": scorecard_total_source,
        "rerun": scorecard_total_rerun,
    }

    # Final hash manifests: the SOURCE manifest must verify clean under an
    # external reader AND its recorded values must equal the recomputed
    # digests of every rerun component artifact.
    source_hash_reasons = verify_artifact_hashes(source_dir)
    try:
        source_manifest = json.loads(
            (source_dir / "artifact_hashes.json").read_text(encoding="utf-8")
        ).get("hashes") or {}
    except (OSError, ValueError):
        source_manifest = {}
    common_ok = all(
        source_manifest.get(filename) == _sha(rerun_art_dir / filename)
        for _component, filename in COMPONENT_ARTIFACTS
        if (rerun_art_dir / filename).is_file()
    )
    checks["artifact_hashes_match"] = (
        not source_hash_reasons and bool(source_manifest) and common_ok)
    components["artifact_hashes"] = {
        "match": checks["artifact_hashes_match"],
        "source_verify_reasons": source_hash_reasons,
        "manifest_common_values_match": common_ok,
    }

    all_match = all(checks.values())
    comparison = {
        "schema_version": 5,
        "verify_id": verify_id,
        "source_experiment_id": rerun_manifest["source_experiment_id"],
        "matrix_id": source_raw.get("matrix_id"),
        "comparison_surface": "full_v6p_n11",
        "checks": checks,
        "components": components,
        "values": {
            "source": {k: source_core.get(k) for k in
                       ("total_pnl", "beta", "turnover_total",
                        "max_drawdown_fraction")},
            "rerun": {k: rerun_core.get(k) for k in
                      ("total_pnl", "beta", "turnover_total",
                       "max_drawdown_fraction")},
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
        synthetic_panel = (
            os.environ.get(SYNTHETIC_PANEL_ENV, "").strip()
            or (str(raw.get("synthetic_panel_path")) if raw.get("synthetic_panel_path") else None)
        )
        if synthetic_panel:
            engine = load_synthetic_panel_engine(synthetic_panel)
        else:
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

    # V6P N11: the rerun mirrors the FULL scored surface -- same unconditional
    # stress suite, same gate/scorecard assembly -- so every component is
    # digest-comparable against the source artifacts.
    warmup_days = int(raw.get("lookback_days") or 3) + WARMUP_PADDING_DAYS
    warmup_boundaries = {
        "warmup_start": iso(window_start - timedelta(days=warmup_days)),
        "scored_start": iso(window_start),
        "scored_end": iso(window_end),
    }
    scored_days = max(1, int((window_end - window_start).total_seconds() // 86400))
    declared_traded = [str(s) for s in (traded or UNIVERSE_SYMBOLS_DEFAULT)]
    base_rows = evaluate_xgates(build_gate_inputs(
        execution, declared_symbols=declared_traded,
        required_days=scored_days, warmup_boundaries=warmup_boundaries,
    ))
    base_xg3_verdict = next(
        (row.verdict.value for row in base_rows
         if row.gate == XGateId.XG3_STAGE_A_PORTFOLIO),
        None,
    )
    stress_report = execute_stress_suite(
        engine, execution=execution,
        traded_symbols=declared_traded,
        benchmark_symbol=benchmark,
        window_start=window_start, window_end=window_end,
        lookback_days=int(raw.get("lookback_days") or 3),
        reverse=bool(raw.get("reverse")),
        folds=int(manifest.outer_folds or 3),
        base_edge_verdict=base_xg3_verdict,
    )
    gate_rows = evaluate_xgates(build_gate_inputs(
        execution, declared_symbols=declared_traded,
        required_days=scored_days, warmup_boundaries=warmup_boundaries,
        stress_report=stress_report,
    ))
    scorecard = compute_portfolio_scorecard(gate_rows)

    out_dir = Path(args.rerun_out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    experiment_id = str(raw.get("experiment_id") or out_dir.parent.name)
    matrix_id = str(raw.get("matrix_id") or "")
    write_jsonl(out_dir / "signal_ranks.jsonl", execution["signal_ranks"])
    write_jsonl(out_dir / "orders.jsonl", execution["orders"])
    write_jsonl(out_dir / "positions.jsonl", execution["closed_legs"])
    write_jsonl(out_dir / "portfolio_ledger.jsonl", execution["portfolio_ledger"])
    # V6P N06: same settlement/accounting set as the scored path so A5 can
    # compare them across reproduction.
    write_jsonl(out_dir / "funding_cashflows.jsonl", execution["funding_cashflows"])
    write_jsonl(out_dir / "terminal_positions.jsonl", execution["terminal_positions"])
    write_jsonl(out_dir / "exposure_control.jsonl", execution["exposure_control"])
    write_json(out_dir / "accounting_reconciliation.json",
               build_v6p_accounting_payload(
                   execution, experiment_id=experiment_id,
                   matrix_id=matrix_id))
    write_json(out_dir / "commission_slippage.json",
               execution["commission_slippage"])
    write_json(out_dir / "stress_report.json", stress_report)
    write_json(out_dir / "canonical_metrics.json", {
        "schema_version": 4,
        "experiment_id": experiment_id,
        "matrix_id": matrix_id,
        **metrics,
        "orders_digest": rows_digest(execution["orders"]),
        "positions_digest": rows_digest(execution["closed_legs"]),
    })
    write_json(out_dir / "core_result.json", {
        "orders_digest": rows_digest(execution["orders"]),
        "positions_digest": rows_digest(execution["closed_legs"]),
        "total_pnl": metrics["total_pnl"],
        "beta": metrics["beta"],
        "turnover_total": metrics["turnover_total"],
        "max_drawdown_fraction": metrics["max_drawdown_fraction"],
        "fold_returns": metrics["fold_returns"],
        "fold_pnls": metrics["fold_pnls"],
        "legs_closed": metrics["legs_closed"],
        "rebalances_scored": metrics["rebalances_scored"],
        # V6P N11 full-surface components:
        "gate_verdicts": xgate_verdict_map(gate_rows),
        "scorecard_total": scorecard["total"],
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
    parser.add_argument("--synthetic-panel", default=None, metavar="SPEC_JSON",
                        help="deterministic synthetic panel spec (golden "
                             "validation only; bypasses catalog + funding "
                             f"bundles; env {SYNTHETIC_PANEL_ENV} also honored)")
    parser.add_argument("--reproduce", metavar="SOURCE_EXP_DIR", default=None)
    parser.add_argument("--verify-id", default=None)
    parser.add_argument("--rerun-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--source-exp-dir", default=None)
    parser.add_argument("--rerun-out-dir", default=None)
    parser.add_argument("--finalize-matrix", action="store_true")
    parser.add_argument("--matrix-dir", default=str(MATRIX_ROOT))
    parser.add_argument("--reproduction-root", default=str(REPRODUCTION_ROOT))
    parser.add_argument("--signal-family", choices=["none", "funding_carry"],
                        default="none")
    return parser


def main(argv: list[str] | None = None) -> int:
    global REPRODUCTION_ROOT
    args = build_parser().parse_args(argv)
    if getattr(args, "signal_family", "none") == "funding_carry":
        os.environ["PORTFOLIO_SIGNAL_FAMILY"] = "funding_carry"
    elif "PORTFOLIO_SIGNAL_FAMILY" in os.environ and             getattr(args, "signal_family", "none") == "none":
        del os.environ["PORTFOLIO_SIGNAL_FAMILY"]
    REPRODUCTION_ROOT = Path(args.reproduction_root)
    if args.reproduce:
        return run_reproduce(args)
    if args.rerun_worker:
        assert args.source_exp_dir and args.rerun_out_dir
        return run_rerun_worker(args)
    if args.finalize_matrix:
        from research.protocol.reconciliation import finalize_matrix

        reconciliation = finalize_matrix(args.matrix_dir, args.registry_path)
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
