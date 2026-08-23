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
import inspect
import json
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from contracts.protocol import (
    STAGE_A_MIN_POSITIVE_FOLD_RATIO,
    STAGE_A_MIN_TRADES_PER_SYMBOL,
    CellStatus,
    ExecutionMode,
    LeakageEvidence,
    MatrixCellResult,
    RunLaunchManifest,
    SCORED_EXECUTION_MODE,
    canonical_json,
    position_pnl_stats,
    require_reason,
    sha256_file,
    sha256_text,
)

# --------------------------------------------------------------------------- #
# Sprint V3 launch-provenance constants (PLAN section 8; owner A3)
# --------------------------------------------------------------------------- #
V3_SCHEMA_VERSION = 3
#: Scored execution baseline threaded to the engine (agreed interface with A2;
#: the engine side accepts ``execution_mode`` as a run_backtest_for_symbol
#: kwarg. Until A2's branch lands, the kwarg is omitted and execution evidence
#: is emitted fail-closed as EVIDENCE_MISSING).
V3_EXECUTION_MODE: str = SCORED_EXECUTION_MODE.value
V3_SLIPPAGE_TICKS = 1
V3_FUNDING_MODE = "audited-post-trade"
VALIDATOR_AGENT = "A3"
EXISTING_SPEC_OWNER_AGENT = "A2"
HYPOTHESIS_OWNER_AGENT = "A4"
DEFAULT_V3_MATRIX_ROOT = "results/matrix/v3_execution_truth"
DEFAULT_V3_STAGE_A_ROOT = "results/stage_a_v3"
WARMUP_BARS_PER_DAY = 96

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
# Sprint V3 launch-time provenance (PLAN section 8; owner A3)
# --------------------------------------------------------------------------- #
class LaunchManifestInvalid(RuntimeError):
    """Cell aborted BEFORE engine.run because manifest.validate() != []."""

    def __init__(self, reasons: list[str]):
        super().__init__(f"launch_manifest_invalid: {sorted(set(reasons))}")
        self.reasons = sorted(set(reasons))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_hypothesis_identity(strategy_type: str) -> dict:
    """Parse the frozen candidate.yaml for a hypothesis-type cell."""
    return load_hypothesis_identity_from_path(
        Path(HYPOTHESIS_CONFIG_BY_TYPE[strategy_type])
    )


def load_hypothesis_identity_from_path(source: Path) -> dict:
    """Parse identity from a candidate spec path (status.yaml authoritative).

    Returns the actual identity recorded by A4/A1 BEFORE any scored run:
    hypothesis_id, candidate_version, state, locked_at_utc, owner_agent and
    declared family trial budget. Fail-closed: missing fields raise so the
    cell never runs without a locked candidate.
    """
    import yaml

    raw = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    locked_at_utc = str(raw["locked_at_utc"])
    # Coordinator status sidecar is the authoritative lock evidence when
    # present (PLAN principle: status/verdict live OUTSIDE the frozen spec).
    status_path = source.parent / "status.yaml"
    if status_path.exists():
        status = yaml.safe_load(status_path.read_text(encoding="utf-8")) or {}
        corrected = str(status.get("locked_at_utc") or "").strip()
        if corrected:
            locked_at_utc = corrected
    identity = {
        "spec_kind": "hypothesis_candidate",
        "source_path": str(source),
        "hypothesis_id": str(raw["hypothesis_id"]),
        "candidate_version": int(raw["candidate_version"]),
        "state": str(raw.get("state", "")),
        "locked_at_utc": locked_at_utc,
        "owner_agent": str(raw.get("owner_agent") or HYPOTHESIS_OWNER_AGENT),
        "declared_family_trials": int(
            raw.get("trial_budget_combinations")
            or raw.get("declared_parameter_combinations")
            or 0
        ),
    }
    return identity


def build_existing_strategy_spec(
    strategy_type: str,
    settings,
    *,
    batch_launch_utc: str,
    declared_family_trials: int,
) -> tuple[str, dict]:
    """Generate an explicit existing-strategy spec doc (never a YAML copy).

    The spec carries the frozen parameter dump plus ``locked_at_utc`` captured
    at BATCH LAUNCH time (before any run starts). Together with the runtime
    config this guarantees candidate and runtime are two DIFFERENT sources.
    """
    baseline = getattr(settings, strategy_type, None)
    if baseline is None and strategy_type == "ema_atr":
        baseline = settings.strategy  # ema_atr parameters live in strategy block
    if baseline is None:
        raise ValueError(f"no frozen parameter block for {strategy_type!r}")
    param_dump = dataclasses.asdict(baseline)
    identity = {
        "spec_kind": "existing_strategy_generated",
        "source_path": f"<generated:{strategy_type}>",
        "hypothesis_id": f"H-EXISTING-{strategy_type}-v1",
        "candidate_version": 1,
        "state": "TIER0_COMPATIBLE",
        "locked_at_utc": batch_launch_utc,
        "owner_agent": EXISTING_SPEC_OWNER_AGENT,
        "declared_family_trials": int(declared_family_trials),
    }
    spec_doc = {
        "schema_version": V3_SCHEMA_VERSION,
        **identity,
        "strategy_type": strategy_type,
        "frozen_parameters": param_dump,
        "generated_by": "research.matrix_runner (A3)",
        "generation_note": (
            "existing inventory strategy; parameters frozen in base YAML; "
            "lock stamp is the batch launch time captured before any run"
        ),
    }
    import yaml

    return yaml.safe_dump(spec_doc, sort_keys=False, default_flow_style=False), identity


def snapshot_frozen_v3(
    exp_dir: Path,
    *,
    runtime_config_source: Path,
    candidate_bytes: bytes | None = None,
    candidate_source: Path | None = None,
    universe_symbols: list[str],
    window_start,
    window_end,
    data_manifest_source: Path,
) -> dict:
    """Freeze runtime/candidate/data/universe BYTES into exp_dir/frozen/.

    SHA-256 values are computed FROM THE BYTES WRITTEN (read back from disk).
    Raises when candidate and runtime bytes come from the same source
    (reason ``config_candidate_same_source``, fail-closed).
    """
    frozen_dir = Path(exp_dir) / "frozen"
    frozen_dir.mkdir(parents=True, exist_ok=True)

    runtime_bytes = Path(runtime_config_source).read_bytes()
    if candidate_bytes is not None:
        cand_bytes = candidate_bytes
    elif candidate_source is not None:
        cand_bytes = Path(candidate_source).read_bytes()
    else:
        raise ValueError("candidate spec requires bytes or a source path")
    if runtime_bytes == cand_bytes:
        raise ValueError(require_reason("config_candidate_same_source"))
    if candidate_source is not None and Path(candidate_source).resolve() == Path(
        runtime_config_source
    ).resolve():
        raise ValueError(require_reason("config_candidate_same_source"))

    targets = {
        "runtime_config": ("runtime_config.yaml", runtime_bytes),
        "candidate": ("candidate.yaml", cand_bytes),
        "data_manifest": ("data_manifest.json", Path(data_manifest_source).read_bytes()),
    }
    hashes: dict[str, str] = {}
    for key, (name, payload) in targets.items():
        target = frozen_dir / name
        target.write_bytes(payload)
        hashes[key] = sha256_file(target)  # hash of the bytes on disk

    universe_doc = {
        "schema_version": V3_SCHEMA_VERSION,
        "symbols": [str(symbol) for symbol in universe_symbols],
        "scored_window": {
            "start_utc": pd.Timestamp(window_start).isoformat(),
            "end_utc": pd.Timestamp(window_end).isoformat(),
        },
    }
    universe_target = frozen_dir / "universe.json"
    universe_target.write_text(json.dumps(universe_doc, indent=2), encoding="utf-8")

    snapshot = {
        "runtime_config_path": "frozen/runtime_config.yaml",
        "runtime_config_sha256": hashes["runtime_config"],
        "candidate_spec_path": "frozen/candidate.yaml",
        "candidate_spec_sha256": hashes["candidate"],
        "data_manifest_path": "frozen/data_manifest.json",
        "data_manifest_sha256": hashes["data_manifest"],
        "universe_path": "frozen/universe.json",
        "universe_sha256": sha256_file(universe_target),
    }
    snapshot["_universe_symbols"] = [str(s) for s in universe_symbols]
    return snapshot


def capture_git_state(repo: str | Path | None = None) -> tuple[str, bool]:
    """(commit_sha, dirty_flag) via rev-parse HEAD + status --porcelain."""
    import subprocess

    def _run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args], cwd=str(repo) if repo else None,
            capture_output=True, text=True, check=False,
        )

    head = _run("rev-parse", "HEAD")
    commit = head.stdout.strip() if head.returncode == 0 and head.stdout.strip() else "unknown"
    status = _run("status", "--porcelain")
    dirty = status.returncode == 0 and status.stdout.strip() != ""
    return commit, dirty


def build_launch_manifest(
    *,
    experiment_id: str,
    matrix_id: str,
    identity: dict,
    strategy_type: str,
    snapshot: dict,
    started_utc: str,
    argv: list[str],
    random_seed: int | None,
    fee_model: str,
    split_policy: str,
    warmup_bars: int,
    outer_folds: int,
    executed_family_trials: int,
) -> RunLaunchManifest:
    """Assemble the schema-v3 RunLaunchManifest for one cell."""
    commit_at_launch, dirty_at_launch = capture_git_state()
    return RunLaunchManifest(
        schema_version=V3_SCHEMA_VERSION,
        experiment_id=experiment_id,
        matrix_id=matrix_id,
        hypothesis_id=identity["hypothesis_id"],
        candidate_version=int(identity["candidate_version"]),
        strategy_type=strategy_type,
        owner_agent=str(identity["owner_agent"]),
        validator_agent=VALIDATOR_AGENT,
        candidate_locked_at_utc=str(identity["locked_at_utc"]),
        backtest_run_started_utc=started_utc,
        backtest_run_finished_utc=None,
        git_commit_at_launch=commit_at_launch,
        dirty_worktree_at_launch=dirty_at_launch,
        exact_backtest_argv=tuple(str(arg) for arg in argv),
        random_seed=random_seed,
        execution_mode=V3_EXECUTION_MODE,
        slippage_ticks=V3_SLIPPAGE_TICKS,
        fee_model=fee_model,
        funding_mode=V3_FUNDING_MODE,
        split_policy=split_policy,
        warmup_bars=warmup_bars,
        outer_folds=outer_folds,
        declared_family_trials=int(identity["declared_family_trials"]),
        executed_family_trials=int(executed_family_trials),
        **{k: v for k, v in snapshot.items() if not k.startswith("_")},
    )


def write_launch_manifest(manifest: RunLaunchManifest, path: Path) -> Path:
    """Persist launch_manifest.yaml BEFORE engine.run (finished stamp null)."""
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dataclasses.asdict(manifest)
    payload["exact_backtest_argv"] = list(manifest.exact_backtest_argv)
    if payload.get("random_seed") is None:
        payload["random_seed_reason"] = require_reason("seed_unavailable")
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return path


def finalize_launch_manifest(path: Path, finished_utc: str) -> None:
    """Append backtest_run_finished_utc AFTER engine.run returns."""
    import yaml

    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    payload["backtest_run_finished_utc"] = finished_utc
    Path(path).write_text(
        yaml.safe_dump(payload, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def read_launch_manifest(path: str | Path) -> RunLaunchManifest:
    """Reload + re-validate a persisted v3 launch manifest."""
    import yaml

    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    known = set(RunLaunchManifest.__dataclass_fields__)
    extra = {}
    if data.get("random_seed") is None and data.get("random_seed_reason"):
        extra["random_seed_reason"] = data.pop("random_seed_reason")
    unknown = sorted(set(data) - known)
    if unknown:
        raise ValueError(f"launch manifest has unknown fields: {unknown}")
    manifest = RunLaunchManifest(**{k: v for k, v in data.items()})
    reasons = manifest.validate()
    if reasons:
        raise LaunchManifestInvalid(reasons)
    return manifest


_ENGINE_KWARG_CACHE: dict[str, bool] = {}


def engine_accepts_execution_mode() -> bool:
    """True iff A2's merged run_backtest_for_symbol takes ``execution_mode``."""
    if "flag" not in _ENGINE_KWARG_CACHE:
        try:
            from backtest.engine import run_backtest_for_symbol

            _ENGINE_KWARG_CACHE["flag"] = (
                "execution_mode"
                in inspect.signature(run_backtest_for_symbol).parameters
            )
        except Exception:  # noqa: BLE001 - engine import unavailable in tests
            _ENGINE_KWARG_CACHE["flag"] = False
    return _ENGINE_KWARG_CACHE["flag"]


# --------------------------------------------------------------------------- #
# Sprint V3 execution-ordering evidence + LeakageEvidence (owner A3)
# --------------------------------------------------------------------------- #
from research.protocol.gates import (  # noqa: E402 - shared canonical constants
    EVIDENCE_MISSING as _GATES_EVIDENCE_MISSING,
    EXECUTION_EVIDENCE_COMPLETE,
    ORDERING_VIOLATION_DETECTED,
)
from research.protocol.manifest import next_experiment_id  # noqa: E402

assert EXECUTION_EVIDENCE_COMPLETE == "EXECUTION_EVIDENCE_COMPLETE"
EVIDENCE_MISSING = _GATES_EVIDENCE_MISSING
assert EVIDENCE_MISSING and ORDERING_VIOLATION_DETECTED


def evaluate_execution_ordering(position_rows: list[dict]) -> dict:
    """Count signal/fill ordering violations FROM the positions ledger.

    Fail-closed: rows without signal_ts/fill_ts (or an empty ledger) yield
    evidence_class EVIDENCE_MISSING -- never an inferred PASS.
    """
    total = len(position_rows)
    entries = 0
    violations = 0
    missing_rows = 0
    modes: set[str] = set()
    for row in position_rows:
        sig = row.get("signal_ts")
        fill = row.get("fill_ts")
        if not sig or not fill:
            missing_rows += 1
            continue
        entries += 1
        mode = row.get("execution_mode")
        if mode:
            modes.add(str(mode))
        try:
            if pd.Timestamp(fill) <= pd.Timestamp(sig):
                violations += 1
        except (TypeError, ValueError):
            missing_rows += 1
            entries -= 1
    if total == 0 or missing_rows or not entries:
        evidence_class = EVIDENCE_MISSING
    elif violations:
        evidence_class = ORDERING_VIOLATION_DETECTED
    else:
        evidence_class = EXECUTION_EVIDENCE_COMPLETE
    return {
        "mode": V3_EXECUTION_MODE,
        "engine_received_execution_mode": engine_accepts_execution_mode(),
        "positions_total": total,
        "entries": entries,
        "violations": violations,
        "missing_timestamp_rows": missing_rows,
        "observed_modes": sorted(modes),
        "evidence_class": evidence_class,
    }


NOT_APPLICABLE_TRANSFORM_EVIDENCE = {
    "status": "NOT_APPLICABLE",
    "reason": "no learned transform; indicators are stateless recursive",
}


def build_leakage_evidence(
    *,
    plan: "CellPlan",
    windows_actual: dict,
    folds_payload: list[dict],
    position_rows: list[dict],
    snapshot: dict,
    git_commit_at_launch: str,
    candidate_locked_at_utc: str,
) -> LeakageEvidence:
    """Runner-emitted G1 evidence (PLAN section 9 G1); gates never hard-code."""
    warm_starts = [
        (pd.Timestamp(fold["start_utc"]) - pd.Timedelta(days=plan.warmup_days))
        for fold in folds_payload
    ] or [pd.Timestamp(windows_actual["start_utc"])]
    bars_incl = [int(fold.get("bars_incl_warmup") or 0) for fold in folds_payload]
    scored_bars = [int(fold.get("scored_bars") or 0) for fold in folds_payload]
    return LeakageEvidence(
        split_policy_declared=bool(plan.split_policy not in ("", "pending")),
        warmup_boundaries={
            "warmup_start": min(warm_starts).isoformat(),
            "warmup_days": plan.warmup_days,
            "scored_start": windows_actual["start_utc"],
            "scored_end": windows_actual["end_utc"],
            "bars_incl_warmup_min": min(bars_incl) if bars_incl else 0,
            "scored_bars_max": max(scored_bars) if scored_bars else 0,
            "per_fold": [
                {
                    "fold": fold.get("fold"),
                    "warmup_start": start.isoformat(),
                    "scored_start": fold.get("start_utc"),
                    "scored_end": fold.get("end_utc"),
                }
                for fold, start in zip(folds_payload, warm_starts)
            ],
        },
        transform_evidence=dict(NOT_APPLICABLE_TRANSFORM_EVIDENCE),
        universe_freeze={
            "candidate_locked_at_utc": candidate_locked_at_utc,
            "universe_sha256": snapshot["universe_sha256"],
            "launch_commit": git_commit_at_launch,
            "symbols": snapshot["_universe_symbols"],
        },
        execution_ordering=evaluate_execution_ordering(position_rows),
        notes=(
            f"split_policy={plan.split_policy}",
            "warmup bars loaded strictly outside each scored fold window",
        ),
    )


@dataclass(frozen=True)
class CellLaunchContext:
    """Per-cell provenance context threaded through execute_cell."""

    experiment_id: str
    matrix_id: str
    stage_a_root: Path
    batch_launch_utc: str
    family_counters: dict[str, int] = field(default_factory=dict)
    declared_variants_by_type: dict[str, int] = field(default_factory=dict)

    @property
    def exp_dir(self) -> Path:
        return self.stage_a_root / self.experiment_id


def resolve_cell_identity(
    plan: CellPlan, ctx: CellLaunchContext
) -> tuple[dict, bytes | None]:
    """Resolve candidate identity for one cell (PLAN section 8).

    Hypothesis cells parse their frozen candidate.yaml; EXISTING-strategy
    cells get an explicit generated spec whose ``locked_at_utc`` is the batch
    launch time captured BEFORE any run starts. Returns ``(identity,
    candidate_bytes_or_None)``.
    """
    if plan.strategy_type in HYPOTHESIS_TYPES:
        identity = load_hypothesis_identity(plan.strategy_type)
        return identity, None
    spec_text, identity = build_existing_strategy_spec(
        plan.strategy_type,
        build_cell_settings(plan.strategy_type, (plan.symbol,))[1],
        batch_launch_utc=ctx.batch_launch_utc,
        declared_family_trials=ctx.declared_variants_by_type.get(plan.strategy_type, 1),
    )
    return identity, spec_text.encode("utf-8")


def execute_cell_scored(plan: CellPlan, ctx: CellLaunchContext) -> dict:
    """Scored cell execution WITH launch-time provenance (D1 flow).

    Order is fail-closed by construction:

    1. resolve candidate identity (frozen candidate.yaml | generated spec);
    2. snapshot frozen inputs (runtime != candidate source enforced);
    3. capture git/dirty/argv/backtest_run_started_utc;
    4. build + WRITE launch_manifest.yaml BEFORE engine.run;
    5. validate(); any reason -> abort cell BEFORE engine (no scored run);
    6. run walk-forward; append backtest_run_finished_utc;
    7. emit LeakageEvidence + execution_evidence.json into stage_a dir.
    """
    exp_dir = ctx.exp_dir
    exp_dir.mkdir(parents=True, exist_ok=True)

    identity, candidate_bytes = resolve_cell_identity(plan, ctx)
    runtime_source, settings = build_cell_settings(
        plan.strategy_type,
        (plan.symbol,),
        catalog_path=plan.catalog_path,
        funding_path=plan.funding_path,
    )
    if plan.strategy_type in HYPOTHESIS_TYPES:
        # Hypothesis cells LOAD base sections from the altcoin baseline YAML;
        # that file is the true runtime config source (candidate.yaml is the
        # candidate spec -- two different sources by contract).
        runtime_source = STRATEGY_CONFIG_MAP["reclaim_mr"]
    # Runtime config and candidate spec must be two DIFFERENT sources/bytes:
    # existing -> YAML file vs generated spec; hypothesis -> altcoin YAML copy
    # vs candidate.yaml.
    snapshot = snapshot_frozen_v3(
        exp_dir,
        runtime_config_source=Path(runtime_source),
        candidate_bytes=candidate_bytes,
        candidate_source=(
            Path(identity["source_path"]) if candidate_bytes is None else None
        ),
        universe_symbols=[plan.symbol],
        window_start=plan.window_start,
        window_end=plan.window_end,
        data_manifest_source=_data_manifest_source(),
    )

    started_utc = utc_now_iso()
    hyp_id = identity["hypothesis_id"]
    manifest = build_launch_manifest(
        experiment_id=ctx.experiment_id,
        matrix_id=ctx.matrix_id,
        identity=identity,
        strategy_type=plan.strategy_type,
        snapshot=snapshot,
        started_utc=started_utc,
        argv=list(sys.argv),
        random_seed=settings.backtest.random_seed,
        fee_model=str(settings.backtest.fee_model),
        split_policy=plan.split_policy,
        warmup_bars=plan.warmup_days * WARMUP_BARS_PER_DAY,
        outer_folds=plan.folds,
        executed_family_trials=int(ctx.family_counters.get(hyp_id, 0)),
    )
    manifest_path = write_launch_manifest(manifest, exp_dir / "launch_manifest.yaml")

    validation_reasons = manifest.validate()
    if validation_reasons:
        # Fail-closed: never start a scored backtest on an invalid manifest.
        finalize_launch_manifest(manifest_path, utc_now_iso())
        raise LaunchManifestInvalid(validation_reasons)

    payload = execute_cell(plan)
    finished_utc = utc_now_iso()
    finalize_launch_manifest(manifest_path, finished_utc)

    leakage = build_leakage_evidence(
        plan=plan,
        windows_actual=payload["window_actual"],
        folds_payload=payload["folds"],
        position_rows=payload.get("positions_rows") or [],
        snapshot=snapshot,
        git_commit_at_launch=manifest.git_commit_at_launch,
        candidate_locked_at_utc=manifest.candidate_locked_at_utc,
    )
    (exp_dir / "execution_evidence.json").write_text(
        json.dumps(
            {
                "schema_version": V3_SCHEMA_VERSION,
                "experiment_id": ctx.experiment_id,
                "matrix_id": ctx.matrix_id,
                "leakage_evidence": dataclasses.asdict(leakage),
                "execution_ordering": dict(leakage.execution_ordering),
                "backtest_run_started_utc": started_utc,
                "backtest_run_finished_utc": finished_utc,
                "git_commit_at_launch": manifest.git_commit_at_launch,
                "dirty_worktree_at_launch": manifest.dirty_worktree_at_launch,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (exp_dir / "positions.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in payload.get("positions_rows") or []),
        encoding="utf-8",
    )
    ctx.family_counters[hyp_id] = int(ctx.family_counters.get(hyp_id, 0)) + 1

    provenance_block = {
        "experiment_id": ctx.experiment_id,
        "stage_a_dir": str(exp_dir),
        "launch_manifest_path": str(manifest_path),
        "hypothesis_id": manifest.hypothesis_id,
        "candidate_version": manifest.candidate_version,
        "owner_agent": manifest.owner_agent,
        "validator_agent": manifest.validator_agent,
        "candidate_locked_at_utc": manifest.candidate_locked_at_utc,
        "backtest_run_started_utc": started_utc,
        "backtest_run_finished_utc": finished_utc,
        "git_commit_at_launch": manifest.git_commit_at_launch,
        "dirty_worktree_at_launch": manifest.dirty_worktree_at_launch,
        "exact_backtest_argv": list(manifest.exact_backtest_argv),
        "runtime_config_sha256": snapshot["runtime_config_sha256"],
        "candidate_spec_sha256": snapshot["candidate_spec_sha256"],
        "data_manifest_sha256": snapshot["data_manifest_sha256"],
        "universe_sha256": snapshot["universe_sha256"],
        "execution_mode": manifest.execution_mode,
        "declared_family_trials": manifest.declared_family_trials,
        "executed_family_trials": manifest.executed_family_trials,
    }
    return {**payload, "provenance": provenance_block, "leakage_evidence": leakage}


_DATA_MANIFEST_CACHE: Path | None = None


def _data_manifest_source() -> Path:
    """Locate the reusable data-contract artifact (A2, Sprint V2)."""
    global _DATA_MANIFEST_CACHE
    if _DATA_MANIFEST_CACHE is not None and _DATA_MANIFEST_CACHE.is_file():
        return _DATA_MANIFEST_CACHE
    candidates = (
        Path("results/matrix/data_contract_v2/data_contract_v2.json"),
        Path("../results/matrix/data_contract_v2/data_contract_v2.json"),
    )
    for candidate in candidates:
        if candidate.is_file():
            _DATA_MANIFEST_CACHE = candidate
            return candidate
    raise FileNotFoundError(
        "data contract artifact missing: results/matrix/data_contract_v2/"
        "data_contract_v2.json"
    )


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


def _opt_ts(value: object) -> str | None:
    """ISO-UTC string for optional timestamp cells (A2 ledger tolerance)."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return text or None


def _opt_num(value: object) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return _optional_float(value)


def _positions_rows_in_window(
    adjusted: "pd.DataFrame",
    w_start,
    w_end,
    *,
    strategy_type: str = "",
    fold: int | None = None,
    execution_records: list[dict] | None = None,
) -> list[dict]:
    """Closed-position rows with funding-adjusted canonical PnL in window.

    One row per closed position whose ``ts_closed`` falls inside the scored
    fold window ``[w_start, w_end]`` (inclusive), sorted by close time.

    Sprint V3: execution-evidence keys (signal_ts/submit_ts/fill_ts/
    initial_risk_usdt/r_multiple/...) come from the strategy-side
    ``execution_records`` joined per symbol by close order; audit columns are
    the fallback and stay null when no record matches. The runner NEVER
    fabricates evidence; unmatched rows keep nulls => EVIDENCE_MISSING.
    """
    has_commission = "commissions" in adjusted.columns
    execution_records = list(execution_records or [])

    def _col(row: Any, name: str) -> Any:
        return row.get(name) if hasattr(row, "get") else None

    def _opt_str(row: Any, name: str) -> str | None:
        text = _opt_ts(_col(row, name))
        return text

    def _opt_int(row: Any, name: str) -> int | None:
        number = _opt_num(_col(row, name))
        return None if number is None else int(number)

    records_by_symbol: dict[str, list[dict]] = {}
    if execution_records:
        for rec in execution_records:
            sym = str(rec.get("symbol") or "")
            records_by_symbol.setdefault(sym, []).append(rec)
    adjusted_sorted = (
        adjusted.sort_values("ts_closed").reset_index(drop=True)
        if "ts_closed" in adjusted.columns else adjusted
    )
    # Per-symbol FIFO pairing: audit rows and execution records describe the
    # SAME closed positions in the same close order. Counts must agree;
    # otherwise the symbol keeps null evidence (fail-closed, never guessed).
    consumed: dict[str, int] = {}
    sym_audit_counts: dict[str, int] = {}
    for _, row0 in adjusted_sorted.iterrows():
        sb0 = str(row0.get("instrument_id", "")).split("-")[0]
        sym_audit_counts[sb0] = sym_audit_counts.get(sb0, 0) + 1

    rows: list[dict] = []
    for _, row in adjusted_sorted.iterrows():
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
        instrument_id = str(row.get("instrument_id", ""))
        qty = _quantity_float(row["peak_qty"])
        canonical_pnl = round(after_funding, 10)
        # ---- join strategy-side execution record (per-symbol FIFO) --------
        sym_base = instrument_id.split("-")[0] if instrument_id else ""
        rec: dict | None = None
        recs_sym = records_by_symbol.get(sym_base) or []
        if len(recs_sym) == sym_audit_counts.get(sym_base, -1):
            idx = consumed.get(sym_base, 0)
            if idx < len(recs_sym):
                rec = recs_sym[idx]
                consumed[sym_base] = idx + 1
        initial_risk = (
            _opt_num(rec.get("initial_risk_usdt"))
            if rec
            else _opt_num(_col(row, "initial_risk_usdt"))
        )
        engine_r = (
            _opt_num(rec.get("r_multiple"))
            if rec
            else _opt_num(_col(row, "r_multiple"))
        )
        r_multiple = (
            engine_r
            if engine_r is not None
            else (
                round(canonical_pnl / initial_risk, 10)
                if initial_risk is not None and initial_risk > 0
                else None
            )
        )
        entry = {
            # ---- V3 execution-evidence keys (null when engine lacks them) --
            "position_id": _opt_ts(_col(row, "position_id")),
            "strategy_type": strategy_type,
            "symbol": instrument_id.split("-")[0] if instrument_id else "",
            "fold": fold,
            "side": "LONG" if str(row["entry"]).upper() == "BUY" else "SHORT",
            "signal_ts": _opt_ts(rec.get("signal_ts")) if rec else _opt_ts(_col(row, "signal_ts")),
            "submit_ts": _opt_ts(rec.get("submit_ts")) if rec else _opt_ts(_col(row, "submit_ts")),
            "fill_ts": _opt_ts(rec.get("fill_ts")) if rec else _opt_ts(_col(row, "fill_ts")),
            "signal_reference_price": (
                _opt_num(rec.get("signal_reference_price"))
                if rec else _opt_num(_col(row, "signal_reference_price"))
            ),
            "fill_price": _opt_num(rec.get("fill_price")) if rec else _opt_num(_col(row, "fill_price")),
            "execution_mode": (
                _opt_str(rec.get("execution_mode"), "execution_mode")
                if rec else _opt_str(row, "execution_mode")
            ),
            "slippage_ticks": (
                _opt_int(rec.get("slippage_ticks"), "slippage_ticks")
                if rec else _opt_int(row, "slippage_ticks")
            ),
            "quantity": qty,
            "initial_stop_price": (
                _opt_num(rec.get("initial_stop_price"))
                if rec else _opt_num(_col(row, "initial_stop_price"))
            ),
            "initial_risk_usdt": initial_risk,
            "gross_pnl": (
                _opt_num(rec.get("gross_pnl")) if rec else _opt_num(_col(row, "gross_pnl"))
            ),
            "commission": (
                _optional_float(row["commissions"]) if has_commission else None
            ),
            "slippage_cost": (
                _opt_num(rec.get("slippage_cost"))
                if rec else _opt_num(_col(row, "slippage_cost"))
            ),
            "funding_pnl": round(funding_net, 10),
            "canonical_pnl": canonical_pnl,
            "r_multiple": r_multiple,
            # ---- legacy continuity keys (V2 accounting) ---------------------
            "instrument_id": instrument_id,
            "qty": qty,
            "entry_ts": opened.isoformat(),
            "exit_ts": closed.isoformat(),
            "realized_pnl_gross": round(after_funding - funding_net, 10),
            "funding_net": round(funding_net, 10),
            "pnl_after_funding": canonical_pnl,
        }
        rows.append(entry)
    rows.sort(key=lambda item: item["exit_ts"])
    return rows


def _funding_fold_positions(
    engine, funding_path: str | None, w_start, w_end,
    *, strategy_type: str = "", fold: int | None = None,
) -> dict:
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
    # Sprint V3: join strategy-side execution records (signal/fill timestamps,
    # initial risk/R) with funding-audit rows. The audit table does NOT carry
    # execution columns; the engine strategy records are their only source.
    exec_records: list[dict] = []
    try:
        for strat in engine.trader.strategies():
            exec_records.extend(getattr(strat, "execution_records", []) or [])
    except Exception:  # noqa: BLE001 - evidence join must never kill accounting
        exec_records = []
    rows = (
        _positions_rows_in_window(
            adjusted,
            w_start,
            w_end,
            strategy_type=strategy_type,
            fold=fold,
            execution_records=exec_records,
        )
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
    Sprint V3: threads ``execution_mode`` through to the engine when A2's
    receiving end is merged, and records whether the engine actually received
    it so execution evidence stays honest.
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
    engine_execution_mode_received = False
    if engine_accepts_execution_mode():
        # Agreed A2/A3 interface: scored baseline threaded by kwarg name.
        extra_kwargs["execution_mode"] = V3_EXECUTION_MODE
        engine_execution_mode_received = True
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
            funding = _funding_fold_positions(
                run.engine, plan.funding_path, w_start, w_end,
                strategy_type=plan.strategy_type, fold=index,
            )
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
def load_inventory_plans(
    inventory_path: str | Path,
    *,
    tier: int,
    folds: int,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
) -> tuple[list[CellPlan], dict[str, int]]:
    """Rebuild plans EXACTLY from the frozen V2 inventory (identities preserved).

    Returns the ordered plan list plus a per-strategy_type map of declared
    variant counts (existing=1, volcomp=4, fundcrowd=3 for this sprint).
    """
    payload = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    declared = int(payload.get("declared_cells") or len(payload.get("cells", [])))
    variants_by_type: dict[str, set] = {}
    plans: list[CellPlan] = []
    config_drift_notes: list[str] = []
    for entry in payload["cells"]:
        identity = entry["identity"]
        strategy_type = identity["strategy_type"]
        symbol = identity["symbol"]
        variant = identity.get("param_variant", "base")
        variants_by_type.setdefault(strategy_type, set()).add(variant)
        plan = make_plan(
            strategy_type,
            symbol,
            tier=tier,
            folds=folds,
            window_start=window_start,
            window_end=window_end,
            param_variant=variant,
        )
        # Verify EVERY frozen field against an independent recomputation so
        # any config/universe/window drift aborts the run before scoring.
        recomputed_snapshot = data_snapshot_id(
            plan.catalog_path, symbol, window_start, window_end
        )
        if identity["data_snapshot_id"] != recomputed_snapshot:
            raise ValueError(
                f"inventory identity drift for {strategy_type}/{symbol}/{variant}: "
                f"data snapshot {identity['data_snapshot_id']!r} != "
                f"recomputed {recomputed_snapshot!r}"
            )
        # Hypothesis candidate specs may legitimately carry POST-RUN verdict
        # amendments (state/rejected_at stamps added after the V2 freeze);
        # those cells are checked against the CURRENT candidate.yaml instead
        # and the discrepancy is recorded. Existing strategies stay strict.
        if strategy_type in HYPOTHESIS_TYPES:
            if identity["config_sha256"] not in (
                plan.config_sha256,
                sha256_file(HYPOTHESIS_CONFIG_BY_TYPE[strategy_type]),
            ):
                config_drift_notes.append(f"{strategy_type}/{symbol}/{variant}")
        elif identity["config_sha256"] != plan.config_sha256:
            raise ValueError(
                f"inventory identity drift for {strategy_type}/{symbol}/{variant}: "
                "config_sha256 differs from current base YAML"
            )
        if identity.get("split_policy") not in (None, plan.split_policy):
            raise ValueError(
                f"inventory identity drift for {strategy_type}/{symbol}/{variant}: "
                f"split policy {identity['split_policy']!r} != {plan.split_policy!r}"
            )
        # Reconstruct the frozen identity key FROM THE FROZEN FIELD VALUES so
        # a tampered identity_key itself is also detected.
        frozen_key = canonical_json(
            {
                "strategy_type": strategy_type,
                "symbol": symbol,
                "param_variant": variant,
                "config_sha256": identity["config_sha256"],
                "data_snapshot_id": recomputed_snapshot,
                "split_policy": identity.get("split_policy") or plan.split_policy,
                "fee_model": identity["fee_model"],
                "slippage_model": identity["slippage_model"],
                "seed": identity["seed"],
            }
        )
        if frozen_key != entry["identity_key"]:
            raise ValueError(
                f"inventory identity drift for {strategy_type}/{symbol}/{variant}: "
                f"rebuilt={frozen_key} frozen={entry['identity_key']}"
            )
        plans.append(plan)
    if declared != len(plans):
        raise ValueError("inventory declared_cells != cells length")
    variant_counts = {name: len(variants) for name, variants in variants_by_type.items()}
    return plans, variant_counts


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
    inventory_path: str | Path | None = None,
    stage_a_root: str | Path = DEFAULT_V3_STAGE_A_ROOT,
) -> dict:
    """Execute (or resume) the declared matrix; returns the run report.

    Sprint V3: when ``inventory_path`` is given, plans are rebuilt EXACTLY
    from the frozen inventory (identities preserved) and every scored cell
    runs through :func:`execute_cell_scored` (launch manifest + LeakageEvidence
    into ``results/stage_a_v3/<EXP>/``). The final report aggregates from the
    FINAL on-disk index (never from last-batch loop counters).
    """
    out_dir = Path(output_root) / matrix_id
    cells_dir = out_dir / "cells"
    cells_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.json"
    index = load_index(index_path)

    if window_start is None:
        window_start = DECLARED_S0_START
    if window_end is None:
        window_end = DECLARED_S0_END

    declared_variants_by_type: dict[str, int] = {}
    plans: list[CellPlan] = []
    if inventory_path is not None:
        plans, declared_variants_by_type = load_inventory_plans(
            inventory_path,
            tier=tier,
            folds=folds,
            window_start=window_start,
            window_end=window_end,
        )
    else:
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
            declared_variants_by_type[strategy_type] = len(variants)
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
    batch_launch_utc = utc_now_iso()  # captured BEFORE any cell run starts
    launch_ctx_base = {
        "matrix_id": matrix_id,
        "stage_a_root": Path(stage_a_root),
        "batch_launch_utc": batch_launch_utc,
        "family_counters": {},
        "declared_variants_by_type": declared_variants_by_type,
    }

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
    manifest_invalid = 0
    family_counters: dict[str, int] = launch_ctx_base["family_counters"]
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

        experiment_id = next_experiment_id()
        ctx = CellLaunchContext(
            experiment_id=experiment_id,
            matrix_id=matrix_id,
            stage_a_root=Path(stage_a_root),
            batch_launch_utc=batch_launch_utc,
            family_counters=family_counters,
            declared_variants_by_type=declared_variants_by_type,
        )
        try:
            if tier == 0:
                payload = execute_cell(plan)
            else:
                payload = execute_cell_scored(plan, ctx)
            status = CellStatus.COMPLETED
            leakage_evidence = payload.pop("leakage_evidence", None)
            provenance = payload.pop("provenance", {})
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
                "schema_version": V3_SCHEMA_VERSION if tier > 0 else 1,
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
                "leakage_evidence": (
                    dataclasses.asdict(leakage_evidence)
                    if leakage_evidence is not None
                    else None
                ),
                "provenance": provenance,
                **payload,
            }
            artifact_path.write_text(json.dumps(document, indent=2), encoding="utf-8")
            # Prune stale transient-error records for this same cell so the
            # final index reflects exactly one entry per declared identity.
            stale_keys = [
                k
                for k, v in index["cells"].items()
                if k != key
                and v.get("identity", {}).get("strategy_type") == plan.strategy_type
                and v.get("identity", {}).get("symbol") == plan.symbol
                and v.get("identity", {}).get("param_variant") == plan.param_variant
            ]
            for k in stale_keys:
                del index["cells"][k]
            index["cells"][key] = {
                "artifact_path": str(artifact_path),
                "status": status.value,
                "experiment_id": experiment_id,
                "completed_at": document["generated_at_utc"],
                "identity": identity,
                "stage_a_dir": provenance.get("stage_a_dir"),
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
                    "execution_evidence_class": (
                        (document.get("leakage_evidence") or {}).get(
                            "execution_ordering", {}
                        ).get("evidence_class")
                    ),
                }
            )
            completed += 1
        except LaunchManifestInvalid as exc:
            errors += 1
            manifest_invalid += 1
            error_doc = _error_artifact(plan, experiment_id, exc)
            error_doc["launch_manifest_reasons"] = list(exc.reasons)
            artifact_path.write_text(json.dumps(error_doc, indent=2), encoding="utf-8")
            index["cells"][error_doc["identity_key"]] = {
                "artifact_path": str(artifact_path),
                "status": CellStatus.PIPELINE_ERROR.value,
                "experiment_id": experiment_id,
                "completed_at": error_doc["generated_at_utc"],
                "identity": error_doc["identity"],
                "reason_codes": list(exc.reasons),
                "stage_a_dir": str(ctx.exp_dir),
            }
            save_index(index_path, index)
            results.append(
                {
                    "cell": artifact_rel,
                    "status": CellStatus.PIPELINE_ERROR.value,
                    "error": str(exc)[:300],
                    "launch_manifest_reasons": list(exc.reasons),
                }
            )
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
                "stage_a_dir": str(ctx.exp_dir),
            }
            save_index(index_path, index)
            results.append(
                {
                    "cell": artifact_rel,
                    "status": CellStatus.PIPELINE_ERROR.value,
                    "error": str(exc)[:300],
                }
            )

    # Sprint V3 report aggregation fix: counts are recomputed from the FINAL
    # on-disk index (never from last-batch loop counters).
    final_index = load_index(index_path)
    status_counts: dict[str, int] = {}
    for cell_entry in final_index["cells"].values():
        status_counts[cell_entry.get("status", "")] = (
            status_counts.get(cell_entry.get("status", ""), 0) + 1
        )
    report = {
        "matrix_id": matrix_id,
        "batch_experiment_prefix": experiment_id.rsplit("-", 1)[0],
        "tier": tier,
        "strategies": strategies,
        "symbols": symbols,
        "declared_cells": len(plans),
        "indexed_cells": len(final_index["cells"]),
        "actual_cell_files": len(list(cells_dir.glob("*.json"))),
        "completed": status_counts.get(CellStatus.COMPLETED.value, 0),
        "reused": reused,
        "pipeline_errors": status_counts.get(CellStatus.PIPELINE_ERROR.value, 0),
        "data_incomplete": status_counts.get(CellStatus.DATA_INCOMPLETE.value, 0),
        "manifest_invalid_cells": manifest_invalid,
        "execution_mode": V3_EXECUTION_MODE,
        "engine_received_execution_mode": engine_accepts_execution_mode(),
        "stage_a_root": str(stage_a_root),
        "inventory_path": str(inventory_path) if inventory_path else None,
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
    reasons = tuple(getattr(exc, "reasons", ()) or ()) or ("cell_failed_exception",)
    cell_result = MatrixCellResult(
        experiment_id=experiment_id,
        strategy_type=plan.strategy_type,
        symbol=plan.symbol,
        status=CellStatus.PIPELINE_ERROR,
        artifact_path=None,
        reason_codes=tuple(dict.fromkeys(reasons)),
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
    parser.add_argument(
        "--inventory",
        default=None,
        help=(
            "frozen inventory JSON (e.g. results/matrix/v3_execution_truth/"
            "frozen_v2_inventory.json); plans are rebuilt exactly from it"
        ),
    )
    parser.add_argument(
        "--stage-a-root",
        default=DEFAULT_V3_STAGE_A_ROOT,
        help="stage_a artifact root for per-cell launch manifests (V3)",
    )
    args = parser.parse_args(argv)

    unknown = set(args.strategies).difference(ALL_STRATEGIES)
    if unknown:
        parser.error(f"unknown strategies {sorted(unknown)}; inventory={ALL_STRATEGIES}")

    symbols = args.symbols
    if symbols is None and args.inventory is None:
        import yaml

        with open(args.universe_config, encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        symbols = [str(s) for s in raw.get("market", {}).get("symbols", [])]
    if not symbols and args.inventory is None:
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
        symbols=symbols or [],
        output_root=args.output_root,
        folds=args.folds,
        window_start=window_start,
        window_end=window_end,
        limit_cells=args.limit_cells,
        inventory_path=args.inventory,
        stage_a_root=args.stage_a_root,
    )
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    for row in report["results"]:
        print(f"  {row['status']:14s} {row['cell']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
