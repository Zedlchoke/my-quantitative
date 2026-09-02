"""V10 canonical scientific-contract authority + honest multiple-testing
denominator (A5, PLAN section 6 H07 / section 11 / section 12).

This module is the SINGLE machine-readable authority for the V10 scientific
execution contract. It closes the three contract gaps found by the V9 A7
terminal audit:

(a) the resolved contract had no REQUIRED ``direction`` field, so the
    funding-sign gate was NOT_TESTED fail-closed on all 5 scored V9 trials.
    V10 makes ``direction`` a REQUIRED enum on every trial spec and rejects
    any spec without it (regression-tested);
(b) the statistical haircut was computed from a STALE effective trial count
    (112) while the honest ledger denominator had moved to 117. V10 ships
    :class:`MultipleTestingDenominator` (base=117, append-only JSONL,
    idempotent adds, decrement refused) and
    :func:`research.stats_v10.statistical_haircut_v10` refuses to certify a
    haircut from an effective_n below the current denominator;
(c) missing return matrices silently disabled DSR/PBO. V10 statistics are
    fail-closed by construction (see sibling module ``research/stats_v10``):
    insufficient inputs produce explicit ``UNAVAILABLE_FAIL_CLOSED`` verdicts
    and never interpolated credit.

Runner-facing rule (H07): a family that is not registered AND frozen in the
:class:`FamilyAllowlist` is rejected even if code supports it — archived or
unfrozen families can never enter a scored run.

Design rules inherited from ``research/resolved_contract_v8.py``: no implicit
defaults, no placeholder values, canonical-JSON self-hashing, fail-closed
:class:`ContractViolation` on every gap. Registry persistence paths are ALWAYS
passed explicitly by the caller (tests use tmp dirs; nothing under results/
is written here).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "v10.canonical_contract.v1"
FAMILY_ALLOWLIST_SCHEMA_VERSION = "v10.family_allowlist.v1"
DENOMINATOR_SCHEMA_VERSION = "v10.denominator.v1"

#: Honest historical denominator after V9 (ledger N_headline 112 through V8R
#: + 5 V9 cells). Every V10 statistic starts from this number.
BASE_DENOMINATOR_V10 = 117

# --------------------------------------------------------------------------- #
# Frozen clock / warmup / purge-embargo vocabulary
# --------------------------------------------------------------------------- #
BAR_CLOCK_V10 = "completed_15m_bars_only"
FILL_CLOCK_V10 = "next_allowed_event_after_signal_bar_close"
WARMUP_RULE_V10 = (
    "warmup_bars_completed_15m_strictly_outside_scored_oos"
)
DIRECTION_VALUES_V10 = ("LONG", "SHORT", "BOTH_WITH_SIGN_SEMANTICS")
DIRECTION_REQUIRED_REASON_V10 = (
    "V9 gap closure: without an explicit direction the funding-sign gate "
    "was NOT_TESTED fail-closed; direction is now REQUIRED per trial spec"
)
FUNDING_SETTLEMENT_V10 = "native_intrarun_settlement"

#: Baseline cost floor (PLAN section 11): stricter frozen values allowed,
#: looser values rejected unless a documented pre-score freeze block exists.
TAKER_FEE_FLOOR_BPS_V10 = 5.0
ADVERSE_TICKS_SLIPPAGE_FLOOR_V10 = 1

#: Purge/embargo must cover at least the holding horizon (spec-time check).
MIN_FOLDS_V10 = 3

CAPS_V10: Mapping[str, float] = {
    "max_symbol_positive_pnl_share": 0.40,
    "max_fold_positive_contribution": 0.50,
}

#: Preregistered stress surface — exactly these five, same order everywhere.
STRESS_MATRIX_V10: tuple[str, ...] = (
    "fee_slippage_x1_5",
    "plus_2_ticks",
    "plus_1_event_delay",
    "drop_one_symbol",
    "drop_one_fold",
)

PF_DEFINITION_V10 = (
    "position_level_profit_factor_as_used_by_V9_scorecards: "
    "sum(position_pnl > 0) / abs(sum(position_pnl <= 0)) computed over "
    "closed positions; trade-level or bar-level PF substitutes forbidden"
)

BENCHMARKS_V10: Mapping[str, Mapping[str, Any]] = {
    "flat_hard": {
        "mandatory": True,
        "definition": "zero-position flat hard benchmark evaluated after cost",
        "role": "hard_gate",
    },
    "buy_and_hold": {"mandatory": False, "role": "context_only"},
    "btc_beta_neutral": {"mandatory": False, "role": "context_only"},
}

FOLD_CONTRACT_V10: Mapping[str, Any] = {
    "min_folds": MIN_FOLDS_V10,
    "ordering": "chronological_non_overlapping",
    "warmup": WARMUP_RULE_V10,
}


class ContractViolation(ValueError):
    """A required V10 contract field/family/registry state is invalid."""


# --------------------------------------------------------------------------- #
# Frozen canonical contract (dataclass; S0 bounds parameterized at resolve)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CanonicalContractV10:
    schema_version: str = SCHEMA_VERSION
    s0_window_start_utc: str | None = None
    s0_window_end_utc: str | None = None
    s0_window_rule: str = (
        "bounds_parameterized_by_caller_iso_dates_resolved_via_"
        "resolve_s0_window_no_default_dates"
    )
    warmup_bars_rule: str = WARMUP_RULE_V10
    bar_clock: str = BAR_CLOCK_V10
    fill_clock: str = FILL_CLOCK_V10
    direction_required: tuple[str, ...] = DIRECTION_VALUES_V10
    direction_required_reason: str = DIRECTION_REQUIRED_REASON_V10
    baseline_costs: Mapping[str, Any] = field(
        default_factory=lambda: {
            "taker_fee_bps": TAKER_FEE_FLOOR_BPS_V10,
            "adverse_ticks_slippage": ADVERSE_TICKS_SLIPPAGE_FLOOR_V10,
            "funding": FUNDING_SETTLEMENT_V10,
        }
    )
    cost_floor_policy: str = (
        "taker_fee_bps >= 5.0 and adverse_ticks_slippage >= 1 are floors; "
        "stricter frozen values allowed; looser values rejected unless a "
        "documented pre-score stricter_frozen block is attached"
    )
    folds: Mapping[str, Any] = field(default_factory=lambda: dict(FOLD_CONTRACT_V10))
    caps: Mapping[str, float] = field(default_factory=lambda: dict(CAPS_V10))
    stress_matrix: tuple[str, ...] = STRESS_MATRIX_V10
    pf_definition: str = PF_DEFINITION_V10
    benchmarks: Mapping[str, Mapping[str, Any]] = field(
        default_factory=lambda: {k: dict(v) for k, v in BENCHMARKS_V10.items()}
    )
    base_denominator: int = BASE_DENOMINATOR_V10


CANONICAL_CONTRACT_V10 = CanonicalContractV10()

_REQUIRED_SPEC_KEYS = frozenset(
    {
        "trial_id",
        "family_id",
        "direction",
        "window_start",
        "window_end",
        "bar_clock",
        "fill_clock",
        "warmup_bars",
        "holding_horizon_bars",
        "purge_periods",
        "embargo_periods",
        "costs",
        "folds",
    }
)
_COST_KEYS = frozenset({"taker_fee_bps", "adverse_ticks_slippage", "funding"})
_COST_OPTIONAL_KEYS = frozenset({"stricter_frozen"})
_FOLD_KEYS = frozenset({"fold_id", "start_utc", "end_utc"})


def _require_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractViolation(f"{name} must be an int, got {value!r}")
    return int(value)


def _parse_iso_utc(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{name} must be a non-empty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractViolation(
            f"{name} must be ISO-8601 UTC, got {value!r}: {exc}"
        ) from exc
    if parsed.tzinfo is None:
        raise ContractViolation(f"{name} must be timezone-aware UTC, got {value!r}")
    return parsed.astimezone(timezone.utc)


def resolve_s0_window(start_iso: Any, end_iso: Any) -> dict[str, Any]:
    """Resolve + validate the parameterized S0 window bounds.

    There is NO default window: both ISO dates are REQUIRED, end must be
    strictly after start, and the resolved payload embeds the duration so
    callers can hash the exact scored span.
    """
    start = _parse_iso_utc(start_iso, "s0_window_start")
    end = _parse_iso_utc(end_iso, "s0_window_end")
    if end <= start:
        raise ContractViolation(
            f"s0_window_end {end_iso!r} must be after s0_window_start "
            f"{start_iso!r}"
        )
    days = round((end - start).total_seconds() / 86_400.0, 6)
    return {
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "days": days,
    }


def contract_dict(contract: CanonicalContractV10 = CANONICAL_CONTRACT_V10) -> dict:
    """Machine-readable dict view of the frozen authority with self-hash."""
    payload: dict[str, Any] = {
        "schema_version": contract.schema_version,
        "s0_window": {
            "start_utc": contract.s0_window_start_utc,
            "end_utc": contract.s0_window_end_utc,
            "rule": contract.s0_window_rule,
        },
        "warmup_bars_rule": contract.warmup_bars_rule,
        "bar_clock": contract.bar_clock,
        "fill_clock": contract.fill_clock,
        "direction_required": list(contract.direction_required),
        "direction_required_reason": contract.direction_required_reason,
        "baseline_costs": dict(contract.baseline_costs),
        "cost_floor_policy": contract.cost_floor_policy,
        "folds": dict(contract.folds),
        "caps": dict(contract.caps),
        "stress_matrix": list(contract.stress_matrix),
        "pf_definition": contract.pf_definition,
        "benchmarks": {k: dict(v) for k, v in contract.benchmarks.items()},
        "base_denominator": contract.base_denominator,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["contract_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


# --------------------------------------------------------------------------- #
# Family allowlist (starts EMPTY for V10; archived/unfrozen never runnable)
# --------------------------------------------------------------------------- #
class FamilyAllowlist:
    """Registry of preregistered signal families for V10.

    Starts EMPTY. :meth:`validate_family` raises :class:`ContractViolation`
    unless ``family_id`` is registered AND ``status == "frozen"`` — an
    archived family is rejected even though the codebase may still support
    it (H07 runner requirement). Persistence JSON path is passed explicitly.
    """

    ROLES = ("candidate", "negative_control")
    STATUSES = ("frozen", "archived")

    def __init__(self) -> None:
        self._families: dict[str, dict[str, str]] = {}

    def register_family(
        self,
        family_id: str,
        spec_hash: str,
        role: str,
        status: str = "frozen",
    ) -> dict[str, str]:
        if not isinstance(family_id, str) or not family_id.strip():
            raise ContractViolation(f"family_id must be non-empty str, got {family_id!r}")
        if not isinstance(spec_hash, str) or len(spec_hash) != 64 or any(
            ch not in "0123456789abcdefABCDEF" for ch in spec_hash
        ):
            raise ContractViolation(
                f"spec_hash must be a 64-char hex sha256, got {spec_hash!r}"
            )
        if role not in self.ROLES:
            raise ContractViolation(
                f"role must be one of {list(self.ROLES)}, got {role!r}"
            )
        if status not in self.STATUSES:
            raise ContractViolation(
                f"status must be one of {list(self.STATUSES)}, got {status!r}"
            )
        row = {
            "family_id": family_id,
            "spec_hash": spec_hash.lower(),
            "role": role,
            "status": status,
        }
        existing = self._families.get(family_id)
        if existing is not None:
            if existing != row:
                raise ContractViolation(
                    f"family {family_id!r} already registered with different "
                    f"payload {existing}; registration is immutable"
                )
            return dict(existing)
        self._families[family_id] = row
        return dict(row)

    def archive_family(self, family_id: str) -> dict[str, str]:
        row = self._families.get(family_id)
        if row is None:
            raise ContractViolation(
                f"unknown_family:{family_id!r} cannot be archived (not registered)"
            )
        row["status"] = "archived"
        return dict(row)

    def validate_family(self, family_id: str) -> dict[str, str]:
        row = self._families.get(family_id)
        if row is None:
            raise ContractViolation(f"unknown_family:{family_id!r}")
        if row["status"] != "frozen":
            raise ContractViolation(
                f"family_not_runnable:{family_id!r} status={row['status']!r} "
                "(archived/unfrozen families are rejected even if code "
                "supports them)"
            )
        return dict(row)

    def get(self, family_id: str) -> dict[str, str] | None:
        row = self._families.get(family_id)
        return dict(row) if row is not None else None

    def families(self) -> tuple[dict[str, str], ...]:
        return tuple(
            dict(self._families[fid]) for fid in sorted(self._families)
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": FAMILY_ALLOWLIST_SCHEMA_VERSION,
            "families": [dict(self._families[fid]) for fid in sorted(self._families)],
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "FamilyAllowlist":
        if not isinstance(payload, Mapping):
            raise ContractViolation("allowlist payload must be a mapping")
        if payload.get("schema_version") != FAMILY_ALLOWLIST_SCHEMA_VERSION:
            raise ContractViolation(
                f"allowlist schema_version mismatch, expected "
                f"{FAMILY_ALLOWLIST_SCHEMA_VERSION}, got "
                f"{payload.get('schema_version')!r}"
            )
        registry = cls()
        rows = payload.get("families")
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise ContractViolation("allowlist payload families must be a sequence")
        for row in rows:
            if not isinstance(row, Mapping):
                raise ContractViolation("allowlist family row must be a mapping")
            registry.register_family(
                row["family_id"], row["spec_hash"], row["role"], row["status"]
            )
        return registry

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(self.to_payload(), sort_keys=True, separators=(",", ":"))
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(target)
        return target

    @classmethod
    def load(cls, path: str | Path) -> "FamilyAllowlist":
        target = Path(path)
        if not target.is_file():
            raise ContractViolation(f"allowlist file missing: {target}")
        payload = json.loads(target.read_text(encoding="utf-8"))
        return cls.from_payload(payload)


#: Module-level V10 allowlist: intentionally EMPTY until A-sprint freezes
#: register their families explicitly.
FAMILY_ALLOWLIST = FamilyAllowlist()


# --------------------------------------------------------------------------- #
# Trial spec validation (fail-closed violation list, never silent defaults)
# --------------------------------------------------------------------------- #
def _check_cost_model(costs: Any, violations: list[str]) -> None:
    where = "costs"
    if not isinstance(costs, Mapping):
        violations.append(f"{where}_not_a_mapping")
        return
    unknown = set(costs) - _COST_KEYS - _COST_OPTIONAL_KEYS
    for key in sorted(unknown):
        violations.append(f"{where}.unexpected_field:{key}")
    fee = costs.get("taker_fee_bps")
    if isinstance(fee, bool) or not isinstance(fee, (int, float)):
        violations.append(f"{where}.taker_fee_bps_must_be_real_number")
    else:
        if fee <= 0:
            violations.append(f"{where}.taker_fee_bps_must_be_positive")
        elif fee < TAKER_FEE_FLOOR_BPS_V10:
            documented = costs.get("stricter_frozen")
            if not isinstance(documented, Mapping):
                violations.append(
                    f"{where}.taker_fee_bps_below_baseline_floor:"
                    f"{fee}<>{TAKER_FEE_FLOOR_BPS_V10}"
                )
            else:
                frozen_before = documented.get("frozen_before_score") is True
                rationale = documented.get("rationale")
                if not frozen_before or not isinstance(rationale, str) or not rationale.strip():
                    violations.append(
                        f"{where}.cost_floor_exception_not_documented:"
                        "stricter_frozen requires frozen_before_score=true and "
                        "a non-empty rationale"
                    )
    ticks = costs.get("adverse_ticks_slippage")
    if isinstance(ticks, bool) or not isinstance(ticks, int):
        violations.append(f"{where}.adverse_ticks_slippage_must_be_int")
    elif ticks < ADVERSE_TICKS_SLIPPAGE_FLOOR_V10:
        violations.append(
            f"{where}.adverse_ticks_slippage_below_baseline_floor:"
            f"{ticks}<>{ADVERSE_TICKS_SLIPPAGE_FLOOR_V10}"
        )
    funding = costs.get("funding")
    if funding != FUNDING_SETTLEMENT_V10:
        violations.append(
            f"{where}.funding_must_equal:{FUNDING_SETTLEMENT_V10}"
        )


def _check_folds(
    folds: Any,
    window_start: datetime,
    window_end: datetime,
    warmup_bars: int,
    violations: list[str],
) -> None:
    where = "folds"
    if not isinstance(folds, Sequence) or isinstance(folds, (str, bytes)):
        violations.append(f"{where}_must_be_sequence")
        return
    if len(folds) < MIN_FOLDS_V10:
        violations.append(
            f"{where}.insufficient_folds:{len(folds)}<{MIN_FOLDS_V10}"
        )
    seen_ids: set[str] = set()
    previous_end: datetime | None = None
    warmup_span = timedelta(minutes=15 * warmup_bars)
    earliest_allowed = window_start + warmup_span
    for idx, fold in enumerate(folds):
        fwhere = f"{where}[{idx}]"
        if not isinstance(fold, Mapping):
            violations.append(f"{fwhere}_not_a_mapping")
            continue
        unknown = set(fold) - _FOLD_KEYS
        for key in sorted(unknown):
            violations.append(f"{fwhere}.unexpected_field:{key}")
        for key in sorted(_FOLD_KEYS - set(fold)):
            violations.append(f"{fwhere}.missing_required_field:{key}")
        if not all(k in fold for k in _FOLD_KEYS):
            continue
        fold_id = fold["fold_id"]
        if not isinstance(fold_id, str) or not fold_id.strip():
            violations.append(f"{fwhere}.fold_id_must_be_non_empty_str")
        elif fold_id in seen_ids:
            violations.append(f"{fwhere}.duplicate_fold_id:{fold_id}")
        else:
            seen_ids.add(fold_id)
        try:
            f_start = _parse_iso_utc(fold["start_utc"], f"{fwhere}.start_utc")
            f_end = _parse_iso_utc(fold["end_utc"], f"{fwhere}.end_utc")
        except ContractViolation as exc:
            violations.append(f"{fwhere}.{exc}")
            continue
        if f_end <= f_start:
            violations.append(f"{fwhere}.window_must_satisfy_start_lt_end")
            continue
        if f_start < window_start or f_end > window_end:
            violations.append(f"{fwhere}.escapes_declared_s0_window")
        if idx == 0 and f_start < earliest_allowed:
            violations.append(
                f"{where}.warmup_inside_scored_oos:first fold starts before "
                f"window_start+warmup_bars*15m ({earliest_allowed.isoformat()})"
            )
        if previous_end is not None and f_start < previous_end:
            violations.append(
                f"{fwhere}.overlaps_previous_fold:chronological required"
            )
        previous_end = f_end


def validate_trial_spec(
    spec: Any,
    *,
    allowlist: FamilyAllowlist | None = None,
    trial_registry: "TrialRegistry | None" = None,
) -> list[str]:
    """Return the list of contract violations for one candidate trial spec.

    Empty list == spec satisfies the canonical V10 contract. Fail-closed:
    a spec WITHOUT ``direction``, with purge/embargo below the holding
    horizon, referencing an unknown/unfrozen/archived family, drifting from
    the frozen clocks, carrying below-floor costs without documentation, or
    duplicating a registered ``trial_id`` is REJECTED — never defaulted.
    """
    violations: list[str] = []
    if not isinstance(spec, Mapping):
        return ["spec_not_a_mapping"]

    for key in sorted(_REQUIRED_SPEC_KEYS - set(spec)):
        violations.append(f"missing_required_field:{key}")
    for key in sorted(set(spec) - _REQUIRED_SPEC_KEYS):
        violations.append(f"unexpected_field:{key}")

    trial_id = spec.get("trial_id")
    if not isinstance(trial_id, str) or not trial_id.strip():
        violations.append("trial_id_must_be_non_empty_str")

    direction = spec.get("direction")
    if direction is None:
        violations.append(
            "missing_required_field:direction (REQUIRED enum "
            f"{list(DIRECTION_VALUES_V10)}; {DIRECTION_REQUIRED_REASON_V10})"
        )
    elif direction not in DIRECTION_VALUES_V10:
        violations.append(
            f"direction_must_be_one_of:{list(DIRECTION_VALUES_V10)},got:{direction!r}"
        )

    if spec.get("bar_clock") != BAR_CLOCK_V10:
        violations.append(f"bar_clock_must_equal:{BAR_CLOCK_V10}")
    if spec.get("fill_clock") != FILL_CLOCK_V10:
        violations.append(f"fill_clock_must_equal:{FILL_CLOCK_V10}")

    warmup_bars = spec.get("warmup_bars")
    if isinstance(warmup_bars, bool) or not isinstance(warmup_bars, int) or warmup_bars <= 0:
        violations.append("warmup_bars_must_be_positive_int")

    holding = spec.get("holding_horizon_bars")
    if isinstance(holding, bool) or not isinstance(holding, int) or holding <= 0:
        violations.append("holding_horizon_bars_must_be_positive_int")
    else:
        purge = spec.get("purge_periods")
        embargo = spec.get("embargo_periods")
        for label, value in (("purge_periods", purge), ("embargo_periods", embargo)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                violations.append(f"{label}_must_be_positive_int")
            elif value < holding:
                violations.append(
                    f"{label}_below_holding_horizon:{value}<{holding}"
                    " (invariant purge/embargo >= holding_horizon_bars)"
                )

    window_start_raw = spec.get("window_start")
    window_end_raw = spec.get("window_end")
    window_start_dt: datetime | None = None
    window_end_dt: datetime | None = None
    try:
        window_start_dt = _parse_iso_utc(window_start_raw, "window_start")
    except ContractViolation as exc:
        violations.append(str(exc))
    try:
        window_end_dt = _parse_iso_utc(window_end_raw, "window_end")
    except ContractViolation as exc:
        violations.append(str(exc))
    if window_start_dt is not None and window_end_dt is not None:
        if window_end_dt <= window_start_dt:
            violations.append("window_end_must_be_after_window_start")
        if (
            isinstance(warmup_bars, int)
            and not isinstance(warmup_bars, bool)
            and warmup_bars > 0
        ):
            _check_folds(
                spec.get("folds"),
                window_start_dt,
                window_end_dt,
                warmup_bars,
                violations,
            )

    _check_cost_model(spec.get("costs"), violations)

    family_id = spec.get("family_id")
    if not isinstance(family_id, str) or not family_id.strip():
        violations.append("family_id_must_be_non_empty_str")
    else:
        registry = allowlist if allowlist is not None else FAMILY_ALLOWLIST
        try:
            registry.validate_family(family_id)
        except ContractViolation as exc:
            violations.append(f"unknown_or_unfrozen_family:{exc}")

    if trial_registry is not None and isinstance(trial_id, str) and trial_id.strip():
        if trial_registry.has(trial_id):
            violations.append(f"duplicate_trial_id:{trial_id}")

    return violations


class TrialRegistry:
    """Uniqueness index for scored ``trial_id`` values within V10."""

    def __init__(self) -> None:
        self._ids: dict[str, dict[str, Any]] = {}

    def has(self, trial_id: str) -> bool:
        return trial_id in self._ids

    def register(self, trial_id: str, payload: Mapping[str, Any] | None = None) -> None:
        if not isinstance(trial_id, str) or not trial_id.strip():
            raise ContractViolation(f"trial_id must be non-empty str, got {trial_id!r}")
        if trial_id in self._ids:
            raise ContractViolation(f"duplicate_trial_id:{trial_id}")
        self._ids[trial_id] = dict(payload or {})

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._ids))


# --------------------------------------------------------------------------- #
# Honest multiple-testing denominator (auto-updating from 117)
# --------------------------------------------------------------------------- #
class MultipleTestingDenominator:
    """Auto-updating scored-trial denominator starting from the honest V9
    base of 117 unique scored trials.

    * :meth:`add_scored_cell` is IDEMPOTENT per ``trial_id``;
    * ``N`` is always ``base + len(unique added cells)``;
    * every add persists ONE canonical JSONL line when ``ledger_path`` is
      given (append-only; no rewrite/delete ever);
    * loading an existing ledger replays rows deterministically in file
      order (duplicate rows collapse idempotently);
    * decrements are REFUSED — the denominator only grows.
    """

    ACTIONS = ("add_scored_cell",)

    def __init__(self, base: int = BASE_DENOMINATOR_V10, ledger_path: str | Path | None = None) -> None:
        if isinstance(base, bool) or not isinstance(base, int) or base < 1:
            raise ContractViolation(f"base must be a positive int, got {base!r}")
        self._base = int(base)
        self._cells: list[str] = []
        self._seen: set[str] = set()
        self._ledger_path = Path(ledger_path) if ledger_path is not None else None
        if self._ledger_path is not None and self._ledger_path.is_file():
            self._replay(self._ledger_path)

    def _replay(self, path: Path) -> None:
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise ContractViolation(
                    f"denominator_ledger_corrupt_line:{lineno}:{exc}"
                ) from exc
            if not isinstance(row, Mapping):
                raise ContractViolation(f"denominator_ledger_line_not_object:{lineno}")
            action = row.get("action")
            if action not in self.ACTIONS:
                raise ContractViolation(
                    f"denominator_ledger_unknown_action:{action!r}:{lineno}"
                )
            trial_id = row.get("trial_id")
            if not isinstance(trial_id, str) or not trial_id.strip():
                raise ContractViolation(
                    f"denominator_ledger_missing_trial_id:{lineno}"
                )
            if trial_id not in self._seen:
                self._seen.add(trial_id)
                self._cells.append(trial_id)

    @property
    def N(self) -> int:
        """Current honest denominator (never below the V9 base of 117)."""
        return self._base + len(self._cells)

    @property
    def base(self) -> int:
        return self._base

    def cells(self) -> tuple[str, ...]:
        return tuple(self._cells)

    def has(self, trial_id: str) -> bool:
        return trial_id in self._seen

    def add_scored_cell(self, trial_id: str) -> bool:
        """Register one newly scored cell; returns True iff newly added."""
        if not isinstance(trial_id, str) or not trial_id.strip():
            raise ContractViolation(
                f"add_scored_cell requires non-empty str trial_id, got {trial_id!r}"
            )
        if trial_id in self._seen:
            return False
        self._seen.add(trial_id)
        self._cells.append(trial_id)
        if self._ledger_path is not None:
            row = {
                "schema_version": DENOMINATOR_SCHEMA_VERSION,
                "action": "add_scored_cell",
                "trial_id": trial_id,
            }
            line = json.dumps(row, sort_keys=True, separators=(",", ":"))
            self._ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._ledger_path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
                handle.flush()
        return True

    def remove_scored_cell(self, trial_id: str = "") -> None:
        raise ContractViolation(
            "denominator_decrement_refused: the multiple-testing denominator "
            "is monotonic; scored trials can never be removed"
        )

    def decrement(self) -> None:
        self.remove_scored_cell()
