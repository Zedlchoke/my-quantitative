"""V11 P1 lane A4 -- no-real-PnL exact-arm dry-run and platform-safe preflight.

Frozen PLAN.md section 7 (lane A4) deliverables implemented here:

1. A dry-run that traverses  load -> signal shape -> schedule -> fills ->
   costs/funding shape -> dummy finite metrics -> temporary-ledger
   publication  using SYNTHETIC data through the REAL adapter path
   (``research.adapter_v10.runner.run_strategy`` and the BG/G facade
   primitives).  No scored metric of a real strategy is computed, exposed
   or persisted anywhere: every metric produced here is a constant, finite,
   explicitly ``DUMMY`` payload, and every write goes to a caller-provided
   temporary ledger that is fail-closed namespaced (``dryrun_*.jsonl``
   under the system temp tree; the real registry path is refused).

2. Identity distinctness: the dry-run takes an injectable
   ``identity_provider`` mapping an arm payload to its trial key.  The
   DEFAULT provider is exactly the adapter's current trial-key function at
   bootstrap (``research.adapter_v10.publish.trial_key`` over
   ``canonical_scored_payload``) -- NO new identity scheme is implemented
   here (lane A2 owns that; A1 wires it at integration).  Before any
   freeze the three arms (anchor, neighbour, causal control) must produce
   pairwise-distinct keys, each stable across replay, otherwise the dry-run
   fails closed.

3. Explicit fail-closed detection of: missing tick sizes, missing benchmark
   declaration, missing terminal valuation bar, missing funding bundle,
   stale manifest and non-finite payload.  Any blocking finding refuses
   publication of the affected arm.

4. Temporary-ledger semantics: first publication of each arm succeeds
   (denominator +1), one replay per arm yields a zero denominator delta,
   and a colliding publication (same trial key, different content) fails
   closed with the ledger bytes unchanged.

Nothing here reads catalog data, touches the network, places orders or
opens a scored window (PLAN.md section 3).
"""

from __future__ import annotations

import math
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from research.adapter_v10.dummy_strategy import DummyDeterministicStrategy
from research.adapter_v10.facade import (
    FORCE_FLAT_REASON,
    FORCE_FLAT_STATUS,
    GenericRunnerV10,
    checked_funding_accrual,
)
from research.adapter_v10.hashes import payload_sha256
from research.adapter_v10.publish import (
    IDEMPOTENT_REPLAY,
    PUBLISHED,
    PRESCORE_BLOCKED,
    canonical_scored_payload,
    publish_trial as adapter_publish_trial,
    trial_denominator,
    trial_key,
)
from research.adapter_v10.protocol import (
    ContractViolation,
    PositionSpan,
    StrategyIdentity,
)
from research.adapter_v10.runner import run_strategy
from research.global_ledger import (
    DEFAULT_REGISTRY_PATH,
    digest as ledger_digest,
    snapshot,
    verify_append_only,
)

#: Package schema version of this dry-run artifact.
DRYRUN_SCHEMA_VERSION = "v11p.a4.exact_arm_dryrun.v1"

#: Producer role recorded on every artifact this module emits.
PRODUCER_ROLE = "A4"

#: Matrix-id namespace of every dry-run publication (never a scored matrix).
DRYRUN_MATRIX_ID = "v11p-a4-dryrun"

#: Marker carried by every dummy metrics payload published by the dry-run.
DRYRUN_DUMMY_METRICS_KIND = "DUMMY_DRYRUN_METRICS"

#: The three exact arms a frozen cell will compare (PLAN section 10/11).
ANCHOR = "anchor"
NEIGHBOUR = "neighbour"
CAUSAL_CONTROL = "causal_control"
ARM_NAMES = (ANCHOR, NEIGHBOUR, CAUSAL_CONTROL)

#: Blocking detection codes (missing evidence is a finding, never a PASS).
FINDING_MISSING_TICK_SIZE = "MISSING_TICK_SIZE"
FINDING_MISSING_BENCHMARK_DECLARATION = "MISSING_BENCHMARK_DECLARATION"
FINDING_MISSING_TERMINAL_VALUATION_BAR = "MISSING_TERMINAL_VALUATION_BAR"
FINDING_MISSING_FUNDING_BUNDLE = "MISSING_FUNDING_BUNDLE"
FINDING_STALE_MANIFEST = "STALE_MANIFEST"
FINDING_NON_FINITE_PAYLOAD = "NON_FINITE_PAYLOAD"
FINDING_STAGE_FAILED = "STAGE_FAILED"
BLOCKING_FINDING_CODES = frozenset(
    {
        FINDING_MISSING_TICK_SIZE,
        FINDING_MISSING_BENCHMARK_DECLARATION,
        FINDING_MISSING_TERMINAL_VALUATION_BAR,
        FINDING_MISSING_FUNDING_BUNDLE,
        FINDING_STALE_MANIFEST,
        FINDING_NON_FINITE_PAYLOAD,
        FINDING_STAGE_FAILED,
    }
)

#: Ordered dry-run stage checklist (PLAN section 7, deliverable 1).
STAGE_NAMES = (
    "load",
    "identity_distinctness",
    "signal_shape",
    "schedule",
    "fills",
    "costs_funding_shape",
    "dummy_metrics",
    "temporary_ledger",
)

IdentityProvider = Callable[[Mapping[str, Any]], str]


# --------------------------------------------------------------------------- #
# Synthetic exact-arm plugins (deterministic, static, never random)
# --------------------------------------------------------------------------- #
DAY_NS = 86_400_000_000_000
DRYRUN_SYMBOLS = tuple(f"DRYSYM{i:02d}" for i in range(10))
DRYRUN_BENCHMARK = "DRYBENCH00"
#: distinct drifts so dollar-neutral books do not cancel price moves
DRYRUN_DRIFTS = {
    sym: 0.001 * ((index % 5) - 2) for index, sym in enumerate(DRYRUN_SYMBOLS)
}
DRYRUN_RATES = (0.0, 0.0001, -0.0002, 0.00005)
DRYRUN_INSTANTS_NS = tuple(DAY_NS * index for index in range(2, 8))
DRYRUN_WINDOW_START_ISO = "2025-01-01T00:00:00Z"
DRYRUN_WINDOW_END_ISO = "2025-01-08T00:00:00Z"

_ARM_CONFIG: dict[str, dict[str, Any]] = {
    ANCHOR: {"arm_config_id": "v11-dryrun-arm-anchor", "strategy_id": "v11_dryrun_anchor", "n_select": 4},
    NEIGHBOUR: {"arm_config_id": "v11-dryrun-arm-neighbour", "strategy_id": "v11_dryrun_neighbour", "n_select": 5},
    CAUSAL_CONTROL: {
        "arm_config_id": "v11-dryrun-arm-causal-control",
        "strategy_id": "v11_dryrun_causal_control",
        "n_select": 4,
    },
}


def build_dry_run_arms(
    *, exclude_benchmark: bool = True
) -> dict[str, DummyDeterministicStrategy]:
    """Build the three synthetic arm plugins on identical synthetic frames.

    The arms differ ONLY in their declared identity fields (plus the
    neighbour's score-affecting ``n_select``), which is exactly the property
    the identity distinctness proof must exercise: identical windows,
    universe, costs and settlements, distinct keys.
    """
    arms: dict[str, DummyDeterministicStrategy] = {}
    for name in ARM_NAMES:
        spec = _ARM_CONFIG[name]
        arms[name] = DummyDeterministicStrategy(
            symbols=DRYRUN_SYMBOLS,
            instants_ns=DRYRUN_INSTANTS_NS,
            n_select=int(spec["n_select"]),
            daily_drift_by_symbol=DRYRUN_DRIFTS,
            settle_rate_by_day_index=DRYRUN_RATES,
            excluded_benchmark_symbol=DRYRUN_BENCHMARK if exclude_benchmark else "",
            window_start_iso=DRYRUN_WINDOW_START_ISO,
            window_end_iso=DRYRUN_WINDOW_END_ISO,
            strategy_id=str(spec["strategy_id"]),
            family_id="V11_DRYRUN_EXACT_ARMS",
            arm_config_id=str(spec["arm_config_id"]),
            fold_count=2,
            purge_days=1,
        )
    return arms


# --------------------------------------------------------------------------- #
# Identity provider (injectable; default = adapter's current trial key)
# --------------------------------------------------------------------------- #
def arm_identity_payload(strategy: Any, *, stress_signature: Mapping[str, Any]) -> dict[str, Any]:
    """Canonical payload handed to an ``identity_provider`` for one arm."""
    identity = strategy.identity()
    return {
        "arm": getattr(strategy, "strategy_id", ""),
        "identity": identity.public_payload(),
        "stress_signature": dict(stress_signature),
    }


def default_identity_provider(arm_payload: Mapping[str, Any]) -> str:
    """The adapter's CURRENT trial-key function at bootstrap (no new scheme).

    Exactly ``research.adapter_v10.publish.trial_key`` over
    ``canonical_scored_payload(identity, stress_signature)``.  Lane A2's
    arm-aware scheme is injected here at integration; this lane only proves
    distinctness through the provider seam.
    """
    if not isinstance(arm_payload, Mapping):
        raise ContractViolation("identity_provider payload must be a mapping")
    for field in ("identity", "stress_signature"):
        if field not in arm_payload:
            raise ContractViolation(f"identity_provider payload missing {field!r}")
    pub = dict(arm_payload["identity"])
    identity = StrategyIdentity(
        strategy_id=str(pub["strategy_id"]),
        family_id=str(pub["family_id"]),
        arm_config_id=str(pub["arm_config_id"]),
        direction=str(pub["direction"]),
        window_start_iso=str(pub["window_start_iso"]),
        window_end_iso=str(pub["window_end_iso"]),
        benchmark_symbols_excluded=tuple(pub.get("benchmark_symbols_excluded") or ()),
        funding_sign_convention=str(
            pub.get("funding_sign_convention") or "LONG_PAYS_POSITIVE_RATE"
        ),
        config=dict(pub.get("config") or {}),
    )
    return trial_key(
        canonical_scored_payload(
            identity=identity, stress_signature=dict(arm_payload["stress_signature"])
        )
    )


def prove_arm_identity_distinctness(
    arms: Mapping[str, Any],
    *,
    stress_signatures: Mapping[str, Mapping[str, Any]],
    identity_provider: Optional[IdentityProvider] = None,
) -> dict[str, Any]:
    """Prove anchor / neighbour / causal-control keys are pairwise distinct.

    Fail closed (:class:`ContractViolation`) before any freeze if any two
    arms collide, if a replay of the same arm changes its key, or if the
    arms are not exactly the three declared ones.
    """
    provider = identity_provider if identity_provider is not None else default_identity_provider
    if not callable(provider):
        raise ContractViolation("identity_provider must be callable")
    names = sorted(str(name) for name in arms)
    if names != sorted(ARM_NAMES):
        raise ContractViolation(f"expected exactly arms {sorted(ARM_NAMES)}, got {names}")

    payloads = {
        str(name): arm_identity_payload(
            arms[name], stress_signature=stress_signatures[name]
        )
        for name in arms
    }
    keys = {str(name): str(provider(payloads[name])) for name in payloads}
    replay_keys = {str(name): str(provider(payloads[name])) for name in payloads}

    collisions: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for name in sorted(keys):
        key = keys[name]
        if key in seen:
            collisions.append({"arms": f"{seen[key]}|{name}", "key": key})
        seen[key] = name
    unstable = sorted(name for name in keys if keys[name] != replay_keys[name])
    if collisions:
        raise ContractViolation(
            f"arm identity collision before freeze: {collisions}; "
            "refusing to freeze non-distinct arms"
        )
    if unstable:
        raise ContractViolation(f"arm identity replay drift for arms: {unstable}")

    anchor_payload, control_payload = payloads[ANCHOR], payloads[CAUSAL_CONTROL]
    differing = sorted(
        key
        for key in set(anchor_payload["identity"]) | set(control_payload["identity"])
        if anchor_payload["identity"].get(key) != control_payload["identity"].get(key)
    )
    return {
        "distinct": True,
        "keys_sha256": keys,
        "replay_stable": {name: replay_keys[name] == keys[name] for name in keys},
        "pairwise_collisions": collisions,
        "control_vs_anchor_differing_identity_fields": differing,
        "provider": getattr(provider, "__name__", str(provider)),
    }


# --------------------------------------------------------------------------- #
# Fail-closed detection
# --------------------------------------------------------------------------- #
def scan_non_finite(payload: Any, _path: str = "$") -> list[str]:
    """JSON paths of every non-finite float inside ``payload`` (recursive)."""
    found: list[str] = []
    if isinstance(payload, Mapping):
        for key in sorted(payload, key=str):
            found.extend(scan_non_finite(payload[key], f"{_path}.{key}"))
    elif isinstance(payload, (list, tuple)):
        for index, value in enumerate(payload):
            found.extend(scan_non_finite(value, f"{_path}[{index}]"))
    elif isinstance(payload, float) and not math.isfinite(payload):
        found.append(_path)
    return found


def detect_fail_closed_findings(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Explicit fail-closed preflight detection over one arm bundle.

    Every rule below emits a BLOCKING finding -- missing evidence is never
    inferred PASS (PLAN section 3).  Expected bundle keys:

    * ``universe`` / ``tick_sizes``            -> per-symbol tick coverage;
    * ``benchmark_declaration``                -> declared context-only legs;
    * ``terminal_valuation``                   -> final-boundary finite marks;
    * ``funding_bundle``                       -> per-symbol settlement series;
    * ``manifest`` + ``payload``               -> freshness digest + finiteness.
    """
    findings: list[dict[str, Any]] = []

    def add(code: str, detail: str, **extra: Any) -> None:
        findings.append({"code": code, "blocking": True, "detail": detail, **extra})

    universe = [str(sym) for sym in (bundle.get("universe") or [])]

    # 1) missing tick sizes -------------------------------------------------
    tick_sizes = bundle.get("tick_sizes")
    if not isinstance(tick_sizes, Mapping) or not tick_sizes:
        add(FINDING_MISSING_TICK_SIZE, "tick_sizes bundle absent or empty")
    else:
        for symbol in universe:
            size = tick_sizes.get(symbol)
            if size is None or not isinstance(size, (int, float)) or not math.isfinite(float(size)) or float(size) <= 0.0:
                add(FINDING_MISSING_TICK_SIZE, f"symbol {symbol} has no positive tick_size")

    # 2) missing benchmark declaration --------------------------------------
    declaration = bundle.get("benchmark_declaration")
    declared = []
    if isinstance(declaration, Mapping):
        declared = [str(sym) for sym in (declaration.get("symbols") or [])]
    if not declared:
        add(
            FINDING_MISSING_BENCHMARK_DECLARATION,
            "no benchmark declaration: context-only benchmark legs are undeclared",
        )

    # 3) missing terminal valuation bar -------------------------------------
    terminal = bundle.get("terminal_valuation")
    marks: Mapping[str, Any] = {}
    if isinstance(terminal, Mapping):
        marks = terminal.get("marks") if isinstance(terminal.get("marks"), Mapping) else {}
        if terminal.get("decision_ns") is None:
            add(FINDING_MISSING_TERMINAL_VALUATION_BAR, "terminal valuation bar has no decision instant")
        for symbol in universe:
            value = marks.get(symbol)
            if value is None or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0.0:
                add(
                    FINDING_MISSING_TERMINAL_VALUATION_BAR,
                    f"terminal bar {terminal.get('decision_ns')} lacks a finite positive mark for {symbol}",
                )
    else:
        add(FINDING_MISSING_TERMINAL_VALUATION_BAR, "terminal valuation bar absent")

    # 4) missing funding bundle --------------------------------------------
    funding = bundle.get("funding_bundle")
    series: Mapping[str, Any] = {}
    if isinstance(funding, Mapping):
        series = funding.get("settlements") if isinstance(funding.get("settlements"), Mapping) else {}
        for symbol in universe:
            points = series.get(symbol)
            if not points:
                add(FINDING_MISSING_FUNDING_BUNDLE, f"no native settlement series for {symbol}")
    else:
        add(FINDING_MISSING_FUNDING_BUNDLE, "funding bundle absent")

    # 5) non-finite payload -------------------------------------------------
    payload = bundle.get("payload")
    non_finite = scan_non_finite(payload) if payload is not None else []
    for path in non_finite:
        add(FINDING_NON_FINITE_PAYLOAD, f"non-finite float at {path}")

    # 6) stale manifest -----------------------------------------------------
    manifest = bundle.get("manifest")
    if not isinstance(manifest, Mapping):
        add(FINDING_STALE_MANIFEST, "manifest absent: artifact freshness cannot be verified")
    else:
        for field in ("payload_sha256", "window_start_iso", "window_end_iso"):
            if not str(manifest.get(field) or "").strip():
                add(FINDING_STALE_MANIFEST, f"manifest field {field!r} missing")
        declared_digest = str(manifest.get("payload_sha256") or "")
        if payload is not None and declared_digest and not non_finite:
            # a non-finite payload cannot be canonically hashed at all; the
            # NON_FINITE_PAYLOAD finding above already blocks it fail closed.
            actual = payload_sha256(payload)
            if declared_digest != actual:
                add(
                    FINDING_STALE_MANIFEST,
                    f"manifest digest {declared_digest[:16]} != payload digest {actual[:16]}",
                )

    for finding in findings:
        if finding["code"] not in BLOCKING_FINDING_CODES:
            raise ContractViolation(f"unknown finding code: {finding['code']}")
    return findings


def build_preflight_bundle(strategy: Any, *, runner_result: Mapping[str, Any]) -> dict[str, Any]:
    """Assemble the detection bundle for one arm from the real adapter path."""
    universe = [str(sym) for sym in runner_result["universe"]]
    identity = strategy.identity()
    last_instant = int(runner_result["schedule"]["last_decision_ns"])
    terminal_marks = strategy.marks_at(universe, last_instant)
    payload = _json_safe_shallow(runner_result)
    return {
        "universe": universe,
        "tick_sizes": dict(runner_result["cost_model"]["default_tick_sizes"]),
        "benchmark_declaration": {
            "symbols": list(runner_result["benchmark_symbols_excluded"]),
            "role": "context_only",
        },
        "terminal_valuation": {"decision_ns": last_instant, "marks": dict(terminal_marks)},
        "funding_bundle": {
            "settlements": {
                sym: [int(p.publish_ts_ns) for p in strategy.settlements(sym)]
                for sym in universe
            }
        },
        "payload": payload,
        "manifest": {
            "payload_sha256": payload_sha256(payload),
            "window_start_iso": str(identity.window_start_iso),
            "window_end_iso": str(identity.window_end_iso),
            "schema_version": str(runner_result.get("schema_version", "")),
        },
    }


def _json_safe_shallow(value: Any) -> Any:
    """JSON-safe deep copy refusing non-finite floats (adapter vocabulary)."""
    if isinstance(value, Mapping):
        return {str(k): _json_safe_shallow(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe_shallow(v) for v in value]
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractViolation("non-finite float cannot enter a dry-run payload")
        return value
    return str(value)


# --------------------------------------------------------------------------- #
# Temporary-ledger guard (fail closed against the real registry)
# --------------------------------------------------------------------------- #
def require_temporary_ledger(ledger_path: Any) -> Path:
    """Validate that ``ledger_path`` is a namespaced DRY-RUN scratch ledger.

    Refuses (fail closed): ``None``, the real global registry path, anything
    under a ``results/registry`` tree, and any filename not shaped
    ``dryrun_*.jsonl``.  The dry-run can therefore never touch a real ledger.
    """
    if ledger_path is None:
        raise ContractViolation("dry-run requires an explicit temporary ledger path")
    resolved = Path(ledger_path).expanduser().resolve()
    real_default = Path(DEFAULT_REGISTRY_PATH).expanduser().resolve()
    if resolved == real_default:
        raise ContractViolation(
            f"refusing to dry-run publish into the real registry: {resolved}"
        )
    parts = resolved.parts
    for index in range(len(parts) - 1):
        if parts[index] == "results" and parts[index + 1] == "registry":
            raise ContractViolation(
                f"refusing to dry-run publish under a results/registry tree: {resolved}"
            )
    if resolved.suffix != ".jsonl" or not resolved.name.startswith("dryrun_"):
        raise ContractViolation(
            "dry-run ledgers must be namespaced 'dryrun_*.jsonl' scratch files; "
            f"got {resolved.name!r}"
        )
    temp_root = Path(tempfile.gettempdir()).resolve()
    if temp_root != resolved and temp_root not in resolved.parents:
        raise ContractViolation(
            f"dry-run ledger must live under the system temp tree ({temp_root}); got {resolved}"
        )
    return resolved


# --------------------------------------------------------------------------- #
# Dummy finite metrics (never a scored metric)
# --------------------------------------------------------------------------- #
DUMMY_METRIC_SERIES: dict[str, dict[str, tuple[float, ...]]] = {
    ANCHOR: {"F1": (0.001, -0.0004, 0.0002), "F2": (0.0001, 0.0003, -0.0002)},
    NEIGHBOUR: {"F1": (0.0008, -0.0002), "F2": (0.0002, 0.0001, -0.0003, 0.0001)},
    CAUSAL_CONTROL: {"F1": (-0.0001, 0.0002, 0.0001), "F2": (0.0003, -0.0002)},
}


def build_dummy_metrics(arm: str) -> dict[str, Any]:
    """Constant, finite, explicitly DUMMY fold metrics for one arm.

    These are NOT strategy PnL: the series are fixed synthetic constants
    hashed into the dry-run artifacts, used only to exercise the metric
    plumbing and the publication gate end-to-end on a scratch ledger.
    """
    if arm not in DUMMY_METRIC_SERIES:
        raise ContractViolation(f"no dummy metric series declared for arm {arm!r}")
    series = {fold: list(values) for fold, values in DUMMY_METRIC_SERIES[arm].items()}
    metrics = _compute_dummy(series)
    aggregate = metrics["aggregate"]
    dummy = {
        "kind": DRYRUN_DUMMY_METRICS_KIND,
        "dry_run": True,
        "scored": False,
        "producer_role": PRODUCER_ROLE,
        "arm": str(arm),
        "score_valid": True,  # publication-gate flag only; values are DUMMY
        "net_return_sum": round(float(aggregate["net_return_sum"]), 12),
        "expectancy_per_day": round(float(aggregate["expectancy"]), 12),
        "max_drawdown": round(float(aggregate["max_drawdown"]), 12),
        "fold_metrics_payload_sha256": str(metrics["payload_sha256"]),
        "source": "fixed synthetic constant series; not strategy PnL",
    }
    non_finite = scan_non_finite(dummy)
    if non_finite:
        raise ContractViolation(f"dummy metrics produced non-finite values: {non_finite}")
    return dummy


def _compute_dummy(series: Mapping[str, Sequence[float]]) -> dict[str, Any]:
    """Adapter-path fold metrics over the dummy series (BG1 primitive)."""
    return _FACADE_RUNNER.compute_fold_metrics(dict(series))


class _FacadeRunnerShim:
    """Thin handle so dummy metrics run through GenericRunnerV10 (BG1 path)."""

    def __init__(self) -> None:
        self._runner: Optional[GenericRunnerV10] = None

    def compute_fold_metrics(self, series: Mapping[str, Sequence[float]]) -> dict[str, Any]:
        if self._runner is None:
            self._runner = GenericRunnerV10(
                strategy=_NullStrategy(), config={"cap": 0.30}
            )
        return self._runner.compute_fold_metrics(series)


class _NullStrategy:
    """Identity-only stand-in satisfying the GenericRunnerV10 constructor."""

    strategy_id = "v11_dryrun_metric_primitive"
    schedule_provider = None

    @property
    def config(self) -> dict[str, Any]:
        return {"cap": 0.30}


class _RunnerView:
    """Presents a ``GenericStrategyBase`` plugin through the runner surface.

    The BG2 schedule primitives key off ``strategy_id`` / ``config`` /
    ``schedule_provider``; a bare plugin carries them inside its identity,
    so the dry-run projects them without mutating the plugin.
    """

    def __init__(self, strategy: Any) -> None:
        identity = strategy.identity()
        cost = strategy.cost_model()
        self._strategy = strategy
        self.strategy_id = str(identity.strategy_id)
        self.config = {
            "cap": 0.30,
            "taker_fee_bps": float(cost.taker_fee_bps),
            "adverse_tick_slip": int(cost.adverse_tick_slip_floor),
        }
        self.schedule_provider = strategy.schedule()


_FACADE_RUNNER = _FacadeRunnerShim()


# --------------------------------------------------------------------------- #
# Temporary-ledger publication semantics
# --------------------------------------------------------------------------- #
def publish_arm_to_temporary_ledger(
    *,
    arm: str,
    strategy: Any,
    stress_signature: Mapping[str, Any],
    ledger_path: Any,
    dummy_metrics: Mapping[str, Any],
) -> dict[str, Any]:
    """Exactly-once dry-run publication of ONE arm into a scratch ledger."""
    path = require_temporary_ledger(ledger_path)
    if str(dummy_metrics.get("kind")) != DRYRUN_DUMMY_METRICS_KIND:
        raise ContractViolation("dry-run publication refuses non-dummy metrics payloads")
    before = trial_denominator(path)
    record = adapter_publish_trial(
        identity=strategy.identity(),
        stress_signature=dict(stress_signature),
        scored_metrics=dict(dummy_metrics),
        payload_digests={
            "dry_run_metrics_sha256": payload_sha256(dict(dummy_metrics)),
            "ledger_namespace": DRYRUN_MATRIX_ID,
        },
        experiment_digest=payload_sha256(
            {"arm": arm, "metrics": dict(dummy_metrics), "namespace": DRYRUN_MATRIX_ID}
        ),
        matrix_id=DRYRUN_MATRIX_ID,
        ledger_path=path,
    )
    after = trial_denominator(path)
    return {
        "arm": str(arm),
        "stage": str(record.get("stage", "")),
        "published": bool(record.get("published", False)),
        "denominator_before": int(before),
        "denominator_after": int(after),
        "denominator_delta": int(after - before),
        "trial_key_sha256": str(record.get("trial_key_sha256", "")),
        "reasons": [str(reason) for reason in record.get("reasons", [])],
    }


def exercise_temporary_ledger_semantics(
    arms: Mapping[str, Any],
    *,
    stress_signatures: Mapping[str, Mapping[str, Any]],
    ledger_path: Any,
) -> dict[str, Any]:
    """First publish -> replay (delta 0) -> collision fails closed, per arm."""
    path = require_temporary_ledger(ledger_path)
    state0 = snapshot(path)
    per_arm: dict[str, Any] = {}
    for name in sorted(arms):
        dummy = build_dummy_metrics(name)
        first = publish_arm_to_temporary_ledger(
            arm=name,
            strategy=arms[name],
            stress_signature=stress_signatures[name],
            ledger_path=path,
            dummy_metrics=dummy,
        )
        if first["stage"] != PUBLISHED or first["denominator_delta"] != 1:
            raise ContractViolation(
                f"arm {name}: first dry-run publication did not append exactly one "
                f"row (stage={first['stage']}, delta={first['denominator_delta']})"
            )
        # one replay per arm: the denominator must not move
        replay = publish_arm_to_temporary_ledger(
            arm=name,
            strategy=arms[name],
            stress_signature=stress_signatures[name],
            ledger_path=path,
            dummy_metrics=dummy,
        )
        if replay["stage"] != IDEMPOTENT_REPLAY or replay["denominator_delta"] != 0:
            raise ContractViolation(
                f"arm {name}: replay was not an exactly-once idempotent skip "
                f"(stage={replay['stage']}, delta={replay['denominator_delta']})"
            )
        # collision: same trial key, DIFFERENT content must fail closed
        mutated = dict(dummy)
        mutated["net_return_sum"] = round(dummy["net_return_sum"] + 0.5, 12)
        collision = publish_arm_to_temporary_ledger(
            arm=name,
            strategy=arms[name],
            stress_signature=stress_signatures[name],
            ledger_path=path,
            dummy_metrics=mutated,
        )
        if collision["published"] or collision["denominator_delta"] != 0:
            raise ContractViolation(
                f"arm {name}: colliding publication was not refused fail-closed"
            )
        per_arm[name] = {
            "first_stage": first["stage"],
            "first_delta": first["denominator_delta"],
            "replay_stage": replay["stage"],
            "replay_delta": replay["denominator_delta"],
            "collision_published": collision["published"],
            "collision_stage": collision["stage"],
            "collision_delta": collision["denominator_delta"],
        }
    state1 = snapshot(path)
    n_publishes = sum(1 for row in state1["rows"] if row.get("kind") == "CELL_RESULT")
    if n_publishes != len(arms):
        raise ContractViolation(
            f"temporary ledger holds {n_publishes} rows, expected exactly {len(arms)}"
        )
    return {
        "ledger_path": str(path),
        "ledger_sha256_after": state1["sha256"],
        "ledger_digest_after": ledger_digest(state1),
        "rows_total": int(state1["count"]),
        "denominator_final": trial_denominator(path),
        "per_arm": per_arm,
        "semantics": "first_publish=+1; replay=+0; collision=refused_fail_closed",
    }


# --------------------------------------------------------------------------- #
# The dry-run itself
# --------------------------------------------------------------------------- #
def _run_stage(name: str, function: Callable[[], Any]) -> dict[str, Any]:
    try:
        detail = function()
        return {"name": name, "ok": True, "detail": detail, "error": None}
    except (ContractViolation, ValueError) as exc:
        return {"name": name, "ok": False, "detail": None, "error": f"{type(exc).__name__}: {exc}"}


def run_exact_arm_dryrun(
    *,
    ledger_path: Any,
    arms: Optional[Mapping[str, Any]] = None,
    identity_provider: Optional[IdentityProvider] = None,
) -> dict[str, Any]:
    """No-real-PnL exact-arm dry-run over the full adapter traversal.

    Returns a JSON-safe record with the stage checklist, the fail-closed
    findings, the identity distinctness proof and the temporary-ledger
    semantics.  ``ok`` is True only when every stage passed, no blocking
    finding exists and each arm published exactly once with a zero-delta
    idempotent replay.  Any stage failure or blocking finding refuses
    publication (fail closed) for the affected arm.
    """
    path = require_temporary_ledger(ledger_path)
    stages: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    per_arm: dict[str, Any] = {}

    def record(stage: dict[str, Any]) -> bool:
        stages.append(stage)
        if not stage["ok"]:
            findings.append(
                {
                    "code": FINDING_STAGE_FAILED,
                    "blocking": True,
                    "stage": stage["name"],
                    "detail": str(stage["error"]),
                }
            )
            return False
        return True

    resolved_arms = dict(arms) if arms is not None else build_dry_run_arms()

    # -- 1. load ------------------------------------------------------------
    def _load() -> dict[str, Any]:
        detail: dict[str, Any] = {}
        for name in sorted(resolved_arms):
            strategy = resolved_arms[name]
            identity = strategy.identity()
            schedule = strategy.schedule()
            universe = strategy.universe(strategy.baseline_stress())
            cost = strategy.cost_model()
            detail[name] = {
                "strategy_id": identity.strategy_id,
                "arm_config_id": identity.arm_config_id,
                "window": [identity.window_start_iso, identity.window_end_iso],
                "n_instants": len(schedule.instants),
                "universe_size": len(universe),
                "taker_fee_bps": float(cost.taker_fee_bps),
                "benchmark_excluded": list(identity.benchmark_symbols_excluded),
            }
        return detail

    if not record(_run_stage("load", _load)):
        return _terminal_result(path, stages, findings, per_arm, aborted=True)

    # -- 2. identity distinctness (BEFORE any freeze) ------------------------
    stress_signatures = {
        name: resolved_arms[name].baseline_stress().signature()
        for name in resolved_arms
    }

    def _identity() -> dict[str, Any]:
        return prove_arm_identity_distinctness(
            resolved_arms,
            stress_signatures=stress_signatures,
            identity_provider=identity_provider,
        )

    identity_proof: dict[str, Any] = {}
    if record(_run_stage("identity_distinctness", _identity)):
        identity_proof = stages[-1]["detail"]
    else:
        return _terminal_result(path, stages, findings, per_arm, aborted=True)

    # -- 3..6 per-arm traversal through the REAL adapter path ----------------
    for name in sorted(resolved_arms):
        strategy = resolved_arms[name]
        baseline = strategy.baseline_stress()
        arm_findings_before = len(findings)

        def _signal_shape() -> dict[str, Any]:
            universe = strategy.universe(baseline)
            cap = 0.30
            checked = 0
            for instant in strategy.schedule().instants:
                book = strategy.targets_at(int(instant), universe=universe, stress=baseline)
                if str(book.get("status")) not in ("OK", "SKIP_NO_SELECTION"):
                    raise ContractViolation(f"unexpected target status {book.get('status')!r}")
                weights = dict(book.get("weights") or [])
                gross = math.fsum(abs(float(w)) for w in weights.values())
                if gross > 0.0:
                    if any(abs(float(w)) > cap + 1e-9 for w in weights.values()):
                        raise ContractViolation("target book breaches the weight cap")
                    if abs(gross - 1.0) > 1e-6:
                        raise ContractViolation(f"target book gross {gross} != 1.0")
                checked += 1
            return {"instants_checked": checked, "cap_max": cap}

        def _schedule() -> dict[str, Any]:
            scenario_rows = [
                {
                    "action": "OPEN_REBALANCE",
                    "decision_ns": int(instant),
                    "status": "OK",
                    "weights": [
                        [sym, weight]
                        for sym, weight in sorted(
                            dict(
                                strategy.targets_at(
                                    int(instant),
                                    universe=strategy.universe(baseline),
                                    stress=baseline,
                                ).get("weights")
                                or {}
                            ).items()
                        )
                    ],
                }
                for instant in strategy.schedule().instants
            ]
            boundary = int(strategy.schedule().instants[-1])
            runner = GenericRunnerV10(strategy=_RunnerView(strategy))
            payload = runner.schedule(
                {"rows": scenario_rows, "final_boundary_ns": boundary}
            )
            last = payload["rows"][-1]
            if str(last.get("action")) != FORCE_FLAT_STATUS:
                raise ContractViolation("schedule lacks the terminal force-flat row")
            if str(last.get("reason_code")) != FORCE_FLAT_REASON:
                raise ContractViolation("terminal row carries the wrong force-flat reason")
            if int(payload["final_boundary_ns"]) != boundary:
                raise ContractViolation("final boundary drifted from the schedule")
            finalised = runner.finalise_schedule_payload(payload)
            if payload_sha256(payload) != payload_sha256(finalised):
                raise ContractViolation("finalised schedule payload is not hash-stable")
            return {
                "n_rows": int(payload["n_rows"]),
                "final_boundary_ns": boundary,
                "terminal_force_flat": True,
            }

        def _fills() -> dict[str, Any]:
            result = run_strategy(strategy, write_artifact_file=False)
            if bool(result.get("scored", True)) is not False:
                raise ContractViolation("adapter run must stay unscored in a dry-run")
            fills = 0
            for book in result["books"]:
                for _sym, _weight in book["weights"]:
                    fills += 1
            return {
                "run_result_sha256": str(result["hashes"]["result_sha256"]),
                "n_books": len(result["books"]),
                "n_legs": fills,
                "n_closed_positions": len(result["positions"]),
                "write_artifact_file": False,
            }

        def _costs_funding_shape() -> dict[str, Any]:
            result = run_strategy(strategy, write_artifact_file=False)
            spans = [
                PositionSpan(
                    symbol=str(row["symbol"]),
                    signed_weight=float(row["signed_weight"]),
                    start_ns=int(row["entry_ns"]),
                    end_ns=int(row["exit_ns"]),
                )
                for row in result["positions"]
            ]
            settlements_map = {
                sym: [
                    {
                        "publish_ts_ns": int(point.publish_ts_ns),
                        "value": float(point.value),
                        "kind": str(point.kind),
                    }
                    for point in strategy.settlements(sym)
                ]
                for sym in result["universe"]
            }
            accrual = checked_funding_accrual(spans, settlements_map)
            if accrual["status"] != "OK":
                raise ContractViolation(
                    f"funding coverage unavailable: {accrual['coverage']['unavailable_spans'][:3]}"
                )
            if str(accrual["sign_convention"]) != "LONG_PAYS_POSITIVE_RATE":
                raise ContractViolation("unexpected funding sign convention")
            for flow in accrual["cashflows"]:
                if not math.isfinite(float(flow["cashflow_per_unit_capital"])):
                    raise ContractViolation("non-finite funding cashflow")
                expected = -float(flow["signed_weight"]) * float(flow["rate"])
                if abs(float(flow["cashflow_per_unit_capital"]) - expected) > 1e-12:
                    raise ContractViolation("funding cashflow violates LONG_PAYS_POSITIVE_RATE")
            return {
                "n_flows": int(accrual["n_flows"]),
                "cashflow_total": round(float(accrual["cashflow_total"]), 12),
                "coverage_complete": bool(accrual["coverage"]["is_complete"]),
                "sign_convention": str(accrual["sign_convention"]),
            }

        arm_ok = True
        arm_ok &= record(_run_stage("signal_shape", _signal_shape))
        arm_ok &= record(_run_stage("schedule", _schedule))
        arm_ok &= record(_run_stage("fills", _fills))
        arm_ok &= record(_run_stage("costs_funding_shape", _costs_funding_shape))

        # detection over the assembled bundle (needs the adapter result)
        bundle: dict[str, Any] = {}
        if arm_ok:
            try:
                result = run_strategy(strategy, write_artifact_file=False)
                bundle = build_preflight_bundle(strategy, runner_result=result)
                for finding in detect_fail_closed_findings(bundle):
                    findings.append({"arm": name, **finding})
                stages.append(
                    {
                        "name": f"detection:{name}",
                        "ok": not any(f.get("arm") == name for f in findings),
                        "detail": {"findings": len(findings) - arm_findings_before},
                        "error": None,
                    }
                )
            except (ContractViolation, ValueError) as exc:
                arm_ok = False
                findings.append(
                    {
                        "arm": name,
                        "code": FINDING_STAGE_FAILED,
                        "blocking": True,
                        "stage": f"detection:{name}",
                        "detail": f"{type(exc).__name__}: {exc}",
                    }
                )
                stages.append(
                    {
                        "name": f"detection:{name}",
                        "ok": False,
                        "detail": None,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
        else:
            stages.append(
                {"name": f"detection:{name}", "ok": False, "detail": None,
                 "error": "skipped: earlier arm stage failed"}
            )

        arm_blocking = any(f.get("arm") == name for f in findings)

        # -- dummy finite metrics + temporary-ledger publication --------------
        def _dummy_and_publish() -> dict[str, Any]:
            dummy = build_dummy_metrics(name)
            publish = publish_arm_to_temporary_ledger(
                arm=name,
                strategy=strategy,
                stress_signature=stress_signatures[name],
                ledger_path=path,
                dummy_metrics=dummy,
            )
            replay = publish_arm_to_temporary_ledger(
                arm=name,
                strategy=strategy,
                stress_signature=stress_signatures[name],
                ledger_path=path,
                dummy_metrics=dummy,
            )
            if replay["stage"] != IDEMPOTENT_REPLAY or replay["denominator_delta"] != 0:
                raise ContractViolation(
                    f"arm {name}: dry-run replay moved the denominator (fail closed)"
                )
            return {
                "published": True,
                "dummy_metrics_sha256": payload_sha256(dict(dummy)),
                "publish_stage": publish["stage"],
                "publish_delta": publish["denominator_delta"],
                "replay_stage": replay["stage"],
                "replay_delta": replay["denominator_delta"],
            }

        if arm_ok and not arm_blocking:
            stage = _run_stage(f"dummy_metrics:{name}", lambda: _dummy_and_publish())
            if record(stage):
                per_arm[name] = dict(stage["detail"])
            else:
                per_arm[name] = {"published": False, "reason": stages[-1]["error"]}
        else:
            reason = (
                "blocked by blocking detection findings"
                if arm_blocking
                else "blocked by earlier stage failure"
            )
            stages.append(
                {
                    "name": f"dummy_metrics:{name}",
                    "ok": False,
                    "detail": None,
                    "error": f"publication refused fail-closed: {reason}",
                }
            )
            per_arm[name] = {"published": False, "reason": reason}

    # -- 7. temporary-ledger final integrity ---------------------------------
    def _temporary_ledger() -> dict[str, Any]:
        state = snapshot(path)
        if int(state["count"]) != len(resolved_arms):
            raise ContractViolation(
                f"temporary ledger holds {state['count']} rows, "
                f"expected exactly {len(resolved_arms)}"
            )
        for row in state["rows"]:
            if str(row.get("kind")) != "CELL_RESULT":
                raise ContractViolation("dry-run ledger holds a non-CELL_RESULT row")
            if str(row.get("matrix_id")) != DRYRUN_MATRIX_ID:
                raise ContractViolation(
                    f"dry-run ledger row outside the {DRYRUN_MATRIX_ID} namespace"
                )
        denominator = trial_denominator(path)
        if denominator != len(resolved_arms):
            raise ContractViolation("temporary-ledger denominator drifted")
        if not verify_append_only(path):
            raise ContractViolation("temporary ledger failed the append-only check")
        return {
            "rows": int(state["count"]),
            "denominator": int(denominator),
            "ledger_sha256": state["sha256"],
            "append_only_verified": True,
            "namespace_matrix_id": DRYRUN_MATRIX_ID,
        }

    record(_run_stage("temporary_ledger", _temporary_ledger))

    return _terminal_result(path, stages, findings, per_arm, aborted=False, identity_proof=identity_proof)


def _terminal_result(
    ledger_path: Path,
    stages: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    per_arm: Mapping[str, Any],
    *,
    aborted: bool,
    identity_proof: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    def _stage_ok(name: str) -> bool:
        matching = [
            stage
            for stage in stages
            if stage["name"] == name or stage["name"].startswith(f"{name}:")
        ]
        return bool(matching) and all(stage["ok"] for stage in matching)

    ok = (
        not aborted
        and not findings
        and all(stage["ok"] for stage in stages)
        and all(info.get("published") for info in per_arm.values())
        and all(_stage_ok(name) for name in STAGE_NAMES)
    )
    return {
        "schema_version": DRYRUN_SCHEMA_VERSION,
        "producer_role": PRODUCER_ROLE,
        "scored": False,
        "real_pnl": False,
        "network": False,
        "ok": bool(ok),
        "aborted": bool(aborted),
        "stages": stages,
        "findings": findings,
        "arms": {name: dict(info) for name, info in sorted(per_arm.items())},
        "identity_distinctness": dict(identity_proof or {}),
        "ledger": {
            "path": str(ledger_path),
            "namespace_matrix_id": DRYRUN_MATRIX_ID,
            "temporary": True,
        },
        "dummy_metrics_kind": DRYRUN_DUMMY_METRICS_KIND,
        "stage_checklist": {name: _stage_ok(name) for name in STAGE_NAMES},
    }


__all__ = [
    "ANCHOR",
    "ARM_NAMES",
    "BLOCKING_FINDING_CODES",
    "CAUSAL_CONTROL",
    "DRYRUN_DUMMY_METRICS_KIND",
    "DRYRUN_MATRIX_ID",
    "DRYRUN_SCHEMA_VERSION",
    "FINDING_MISSING_BENCHMARK_DECLARATION",
    "FINDING_MISSING_FUNDING_BUNDLE",
    "FINDING_MISSING_TERMINAL_VALUATION_BAR",
    "FINDING_MISSING_TICK_SIZE",
    "FINDING_NON_FINITE_PAYLOAD",
    "FINDING_STAGE_FAILED",
    "FINDING_STALE_MANIFEST",
    "NEIGHBOUR",
    "PRODUCER_ROLE",
    "STAGE_NAMES",
    "build_dummy_metrics",
    "build_dry_run_arms",
    "build_preflight_bundle",
    "default_identity_provider",
    "detect_fail_closed_findings",
    "exercise_temporary_ledger_semantics",
    "publish_arm_to_temporary_ledger",
    "prove_arm_identity_distinctness",
    "require_temporary_ledger",
    "run_exact_arm_dryrun",
    "scan_non_finite",
]
