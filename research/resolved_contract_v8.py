"""V8 resolved run contract (PLAN sections 5.2/6/8; owner A6).

Resolves at runtime every field the frozen V8 candidate
(``H-XSECT-REVERSAL-v2``) left open (window/fold layout, cost model, risk
limits, weekly schedule, launch SHA). Fail-closed per the sibling
``research.resolved_contract`` style: there are NO implicit defaults on any
contract field — a caller that omits, nulls or drifts a required argument
gets :class:`ResolvedContractErrorV8` instead of a silently defaulted
contract.

The ``launch_sha`` is the EXPLICIT final integration commit SHA of the V8
launch. Placeholder semantics are FORBIDDEN: ``PENDING_FINAL_CODE_SHA``,
``TO_FREEZE`` and ``PENDING_INTEGRATION_SHA`` raise on sight. It must match
``^[0-9a-f]{40}$`` AND be reachable as a real commit object in the
repository (``git cat-file -e <sha>^{commit}``).

Two-stage freeze (A6 -> A1):
  1. THIS sprint stage commits only the TEMPLATE artifact
     ``research/audits/v8p/resolved_run_contract_v8.template.json``
     carrying ``launch_sha=None`` plus the marker key
     ``launch_sha_frozen: false`` (a literal placeholder string such as
     ``PENDING_FINAL_CODE_SHA`` would violate the no-placeholder rule and
     is never written).
  2. At integration A1 calls :func:`freeze_final(launch_sha, ...)` which
     validates the sha as a REAL commit, re-validates every frozen block
     against this module's constants, fills ``dataset_hashes``, builds the
     canonical contract via :func:`build_resolved_contract_v8`, verifies
     its self-hash and atomically writes
     ``research/audits/v8p/resolved_run_contract_v8.json``. The final path
     is refuse-to-overwrite: once frozen, it never changes silently.

Frozen V8 plan set mirrored here (PLAN sections 5.1/7): exactly four trials
``XSECT-WREV-{3D,7D,14D}`` + ``XSECT-WMOM-7D-CONTROL``, weekly Monday 00:00
UTC schedule with 7-day rebalance / purge / embargo and >=14-day warmup,
gross 0.80 / net 0 / long 0.40 / short 0.40 / max abs symbol weight 0.20,
fee 0.0005 one-tick adverse, three chronological folds with explicit 7-day
purge/embargo fields per fold, one ``CELL_RESULT`` registry root, max two
workers with the six-entry preregistered stress surface.

Regenerate the committed TEMPLATE with::

    PYTHONPATH=<repo> python -m research.resolved_contract_v8

``main()`` writes ONLY the template; the final artifact is produced
exclusively through :func:`freeze_final`.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "v8.resolved_run_contract.v1"
CONTRACT_RELPATH = Path("research") / "audits" / "v8p" / "resolved_run_contract_v8.json"
TEMPLATE_RELPATH = (
    Path("research") / "audits" / "v8p" / "resolved_run_contract_v8.template.json"
)
PRIMARY_REPO_ROOT = Path("/Users/hoangminhlong/my-quantitative")

SIGNAL_FAMILY_FROZEN = "weekly_reversal"
FROZEN_TRIAL_IDS: tuple[str, ...] = (
    "XSECT-WREV-3D",
    "XSECT-WREV-7D",
    "XSECT-WREV-14D",
    "XSECT-WMOM-7D-CONTROL",
)
CONTROL_TRIAL_ID = "XSECT-WMOM-7D-CONTROL"
# PLAN section 5.1 freeze table: id -> formation_lookback_days -> kind.
FROZEN_TRIAL_SPECS: dict[str, dict[str, Any]] = {
    "XSECT-WREV-3D": {"formation_lookback_days": 3, "kind": "reversal"},
    "XSECT-WREV-7D": {"formation_lookback_days": 7, "kind": "reversal"},
    "XSECT-WREV-14D": {"formation_lookback_days": 14, "kind": "reversal"},
    "XSECT-WMOM-7D-CONTROL": {
        "formation_lookback_days": 7,
        "kind": "momentum_control",
    },
}
FROZEN_UNIVERSE: tuple[str, ...] = (
    "ADAUSDT",
    "BNBUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "SOLUSDT",
    "XRPUSDT",
)
BENCHMARK_FROZEN = "BTCUSDT"
COSTS_FROZEN: dict[str, Any] = {"fee_taker": 0.0005, "slippage_ticks": 1}
LIMITS_FROZEN: dict[str, Any] = {
    "gross": 0.80,
    "net": 0.0,
    "long_gross": 0.40,
    "short_gross": 0.40,
    "symbol_weight": 0.20,
}
WEEKLY_SCHEDULE_FROZEN: dict[str, Any] = {
    "weekday": "MON",
    "utc": True,
    "rebalance_days": 7,
    "purge_embargo_days": 7,
    "warmup_days_min": 14,
}
REGISTRY_OUTPUT_CONTRACT_FROZEN: dict[str, str] = {
    "registry_kind": "CELL_RESULT",
    "output_root": "results/portfolio_v8",
    "matrix_id": "v8_xsect_weekly_reversal",
    "shard_pattern": "results/registry/shards/v8_<trial_id>.jsonl",
}
EXECUTION_CONTRACT_FROZEN: dict[str, Any] = {
    "max_concurrent_workers": 2,
    "stress_surface": [
        "fee_x1_5",
        "adverse_two_ticks",
        "delay_one_event",
        "drop_one_symbol_all",
        "drop_one_fold_all",
        "rebalance_day_shift_plus_1d",
    ],
}
# Frozen V8 evidence-chain decision: the resolved contract is only valid
# against THIS baseline + THIS prelaunch attestation, and enforcement is
# MANDATORY. Paths are repo-relative and exact.
PROVENANCE_BASELINE_PATH_FROZEN = "research/audits/v8p/baseline_root_v8.json"
PROVENANCE_ATTESTATION_PATH_FROZEN = (
    "research/audits/v8p/a7_prelaunch_attestation_v8.json"
)
PROVENANCE_CONTRACT_FROZEN: dict[str, Any] = {
    "baseline_path": PROVENANCE_BASELINE_PATH_FROZEN,
    "attestation_path": PROVENANCE_ATTESTATION_PATH_FROZEN,
    "enforcement_required": True,
}
PURGE_EMBARGO_DAYS_FROZEN = 7

_LAUNCH_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN_LAUNCH_SHA_VALUES = frozenset(
    {"PENDING_FINAL_CODE_SHA", "TO_FREEZE", "PENDING_INTEGRATION_SHA"}
)
_TRIAL_KEYS = frozenset({"trial_id", "formation_lookback_days", "kind"})
_LOOKBACKS_ALLOWED = frozenset({3, 7, 14})
_KINDS_ALLOWED = frozenset({"reversal", "momentum_control"})
_FOLD_KEYS = frozenset(
    {"fold_id", "start_utc", "end_utc", "purge_days", "embargo_days"}
)
_COST_KEYS = frozenset(COSTS_FROZEN)
_LIMIT_KEYS = frozenset(LIMITS_FROZEN)
_SCHEDULE_KEYS = frozenset(WEEKLY_SCHEDULE_FROZEN)
_REGISTRY_KEYS = frozenset(REGISTRY_OUTPUT_CONTRACT_FROZEN)
_EXECUTION_KEYS = frozenset(EXECUTION_CONTRACT_FROZEN)
_STRESS_SURFACE_FROZEN = tuple(EXECUTION_CONTRACT_FROZEN["stress_surface"])
_PROVENANCE_KEYS = frozenset(PROVENANCE_CONTRACT_FROZEN)
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


class ResolvedContractErrorV8(ValueError):
    """A required V8 contract field is missing/invalid (fail-closed)."""


# --------------------------------------------------------------------------- #
# Strict primitive validators (no coercion, no defaults)
# --------------------------------------------------------------------------- #
def _require_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ResolvedContractErrorV8(
            f"{name} must be a non-empty string, got {value!r}"
        )
    return value


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ResolvedContractErrorV8(
            f"{name} must be a mapping, got {type(value).__name__}"
        )
    return value


def _require_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ResolvedContractErrorV8(
            f"{name} must be a real number, got {value!r}"
        )
    return float(value)


def _require_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ResolvedContractErrorV8(f"{name} must be an int, got {value!r}")
    return int(value)


def _parse_utc(stamp: str, name: str) -> datetime:
    text = _require_str(stamp, name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ResolvedContractErrorV8(
            f"{name} must be an ISO-8601 UTC timestamp, got {stamp!r}: {exc}"
        ) from exc
    if parsed.tzinfo is None:
        raise ResolvedContractErrorV8(
            f"{name} must be timezone-aware UTC, got {stamp!r}"
        )
    return parsed.astimezone(timezone.utc)


def _require_sha256_hex(value: Any, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in _HEX_DIGITS for ch in value)
    ):
        raise ResolvedContractErrorV8(
            f"{name} must be a 64-char hex sha256 digest, got {value!r}"
        )
    return value.lower()


def _resolve_launch_sha(value: Any, repo_root: Path) -> str:
    """Explicit final launch commit SHA: format-valid AND a real commit."""
    if value is None or isinstance(value, bool) or not isinstance(value, str):
        raise ResolvedContractErrorV8(
            "launch_sha is REQUIRED (explicit final integration SHA), got "
            f"{value!r}; template callers must use launch_sha=None together "
            "with launch_sha_frozen=False via build_template_contract"
        )
    if not value or not value.strip():
        raise ResolvedContractErrorV8("launch_sha must be a non-empty 40-hex sha")
    if value.strip().upper() in {v.upper() for v in _FORBIDDEN_LAUNCH_SHA_VALUES}:
        raise ResolvedContractErrorV8(
            f"launch_sha placeholder {value!r} is FORBIDDEN in the final "
            f"artifact: pass the explicit final integration commit SHA"
        )
    if not _LAUNCH_SHA_RE.match(value):
        raise ResolvedContractErrorV8(
            f"launch_sha must match ^[0-9a-f]{{40}}$, got {value!r}"
        )
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{value}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise ResolvedContractErrorV8(
            f"launch_sha_not_a_commit: {value!r} is not reachable as a commit "
            f"in {repo_root}: {proc.stderr.strip()}"
        )
    return value


def _require_frozen_mapping(value: Any, name: str, frozen: Mapping[str, Any]) -> dict:
    row = _require_mapping(value, name)
    if set(row) != set(frozen):
        raise ResolvedContractErrorV8(
            f"{name} must have exactly keys {sorted(frozen)} "
            f"(no implicit defaults/extras), got {sorted(row)}"
        )
    normalized = {}
    for key, expected in frozen.items():
        got = row[key]
        if isinstance(expected, bool) or not isinstance(expected, (int, float)):
            if got != expected or type(got) is not type(expected):
                raise ResolvedContractErrorV8(
                    f"{name}.{key} is FROZEN and must equal {expected!r}, "
                    f"got {got!r}"
                )
            normalized[key] = got
        elif isinstance(expected, int) and not isinstance(expected, bool):
            if isinstance(got, bool) or not isinstance(got, int) or got != expected:
                raise ResolvedContractErrorV8(
                    f"{name}.{key} is FROZEN and must equal {expected!r}, "
                    f"got {got!r}"
                )
            normalized[key] = got
        else:
            num = _require_number(got, f"{name}.{key}")
            if num != float(expected):
                raise ResolvedContractErrorV8(
                    f"{name}.{key} is FROZEN and must equal {expected!r}, "
                    f"got {got!r}"
                )
            normalized[key] = num
    return normalized


# --------------------------------------------------------------------------- #
# Frozen inventory / universe / folds validation
# --------------------------------------------------------------------------- #
def _validate_trial_inventory(value: Any) -> list[dict]:
    """Exactly the four frozen trials; control sign only on WMOM-7D @ 7."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise ResolvedContractErrorV8(
            "trial_inventory must be a non-empty sequence of trial mappings"
        )
    rows: list[dict] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(value):
        where = f"trial_inventory[{idx}]"
        row = _require_mapping(item, where)
        if set(row) != _TRIAL_KEYS:
            raise ResolvedContractErrorV8(
                f"{where} must have exactly keys {sorted(_TRIAL_KEYS)}, "
                f"got {sorted(row)}"
            )
        trial_id = _require_str(row["trial_id"], f"{where}.trial_id")
        if trial_id not in FROZEN_TRIAL_SPECS:
            raise ResolvedContractErrorV8(
                f"{where}.trial_id {trial_id!r} is not one of the frozen V8 "
                f"trials {sorted(FROZEN_TRIAL_SPECS)}"
            )
        if trial_id in seen_ids:
            raise ResolvedContractErrorV8(f"duplicate trial_id {trial_id!r}")
        seen_ids.add(trial_id)
        lookback = row["formation_lookback_days"]
        if isinstance(lookback, bool) or not isinstance(lookback, int):
            raise ResolvedContractErrorV8(
                f"{where}.formation_lookback_days must be an int in "
                f"{sorted(_LOOKBACKS_ALLOWED)}, got {lookback!r}"
            )
        if lookback not in _LOOKBACKS_ALLOWED:
            raise ResolvedContractErrorV8(
                f"{where}.formation_lookback_days must be one of "
                f"{sorted(_LOOKBACKS_ALLOWED)}, got {lookback!r}"
            )
        kind = row["kind"]
        if kind not in _KINDS_ALLOWED:
            raise ResolvedContractErrorV8(
                f"{where}.kind must be 'reversal' or 'momentum_control', "
                f"got {kind!r}"
            )
        frozen = FROZEN_TRIAL_SPECS[trial_id]
        if lookback != frozen["formation_lookback_days"] or kind != frozen["kind"]:
            raise ResolvedContractErrorV8(
                f"{where} drifts from the frozen spec for {trial_id}: expected "
                f"{frozen}, got formation_lookback_days={lookback}, kind={kind!r}"
            )
        if kind == "momentum_control" and trial_id != CONTROL_TRIAL_ID:
            raise ResolvedContractErrorV8(
                f"momentum_control kind only allowed on {CONTROL_TRIAL_ID}, "
                f"got {trial_id!r}"
            )
        if kind == "momentum_control" and lookback != 7:
            raise ResolvedContractErrorV8(
                f"control trial {trial_id!r} must use "
                f"formation_lookback_days=7, got {lookback}"
            )
        rows.append(
            {
                "trial_id": trial_id,
                "formation_lookback_days": int(lookback),
                "kind": kind,
            }
        )
    if len(rows) != len(FROZEN_TRIAL_IDS):
        raise ResolvedContractErrorV8(
            f"trial_inventory must contain exactly {len(FROZEN_TRIAL_IDS)} "
            f"frozen trials {list(FROZEN_TRIAL_IDS)}, got {len(rows)} entries"
        )
    missing = [tid for tid in FROZEN_TRIAL_IDS if tid not in seen_ids]
    if missing:
        raise ResolvedContractErrorV8(
            f"trial_inventory is missing frozen trials {missing}"
        )
    # Canonical freeze order regardless of caller ordering -> stable hash.
    order = {tid: i for i, tid in enumerate(FROZEN_TRIAL_IDS)}
    return sorted(rows, key=lambda r: order[r["trial_id"]])


def _validate_universe(value: Any, benchmark: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ResolvedContractErrorV8("traded_universe must be a sequence of symbols")
    symbols = [str(s) for s in value]
    if not symbols:
        raise ResolvedContractErrorV8("traded_universe must be non-empty")
    if any(not s.strip() for s in symbols):
        raise ResolvedContractErrorV8(
            f"traded_universe contains blank symbols: {symbols!r}"
        )
    if len(set(symbols)) != len(symbols):
        raise ResolvedContractErrorV8(f"traded_universe has duplicates: {symbols!r}")
    if set(symbols) != set(FROZEN_UNIVERSE) or len(symbols) != len(FROZEN_UNIVERSE):
        raise ResolvedContractErrorV8(
            f"traded_universe must be EXACTLY the frozen six-alt V8 universe "
            f"{list(FROZEN_UNIVERSE)}, got {symbols!r}"
        )
    if benchmark in symbols:
        raise ResolvedContractErrorV8(
            f"benchmark {benchmark!r} must not appear in traded_universe "
            f"(context-only)"
        )
    return symbols


def _validate_folds(
    folds: Any, start_dt: datetime, end_dt: datetime
) -> list[dict]:
    """Chronological non-overlapping folds with explicit 7-day purge/embargo."""
    if not isinstance(folds, Sequence) or isinstance(folds, (str, bytes)) or not folds:
        raise ResolvedContractErrorV8(
            "folds must be a non-empty sequence of fold mappings"
        )
    seen_ids: set[str] = set()
    parsed: list[dict] = []
    for idx, item in enumerate(folds):
        where = f"folds[{idx}]"
        row = _require_mapping(item, where)
        if set(row) != _FOLD_KEYS:
            raise ResolvedContractErrorV8(
                f"{where} must have exactly keys {sorted(_FOLD_KEYS)}, "
                f"got {sorted(row)}"
            )
        fold_id = _require_str(row["fold_id"], f"{where}.fold_id")
        if fold_id in seen_ids:
            raise ResolvedContractErrorV8(f"duplicate fold_id {fold_id!r}")
        seen_ids.add(fold_id)
        purge = _require_int(row["purge_days"], f"{where}.purge_days")
        embargo = _require_int(row["embargo_days"], f"{where}.embargo_days")
        if purge != PURGE_EMBARGO_DAYS_FROZEN:
            raise ResolvedContractErrorV8(
                f"{where}.purge_days must equal "
                f"{PURGE_EMBARGO_DAYS_FROZEN} (PLAN section 5.1), got {purge!r}"
            )
        if embargo != PURGE_EMBARGO_DAYS_FROZEN:
            raise ResolvedContractErrorV8(
                f"{where}.embargo_days must equal "
                f"{PURGE_EMBARGO_DAYS_FROZEN} (PLAN section 5.1), got {embargo!r}"
            )
        f_start = _parse_utc(row["start_utc"], f"{where}.start_utc")
        f_end = _parse_utc(row["end_utc"], f"{where}.end_utc")
        if f_end <= f_start:
            raise ResolvedContractErrorV8(f"{where} window must satisfy start < end")
        if f_start < start_dt or f_end > end_dt:
            raise ResolvedContractErrorV8(f"{where} escapes the declared window")
        if parsed and f_start < parsed[-1]["_end"]:
            raise ResolvedContractErrorV8(
                f"{where} overlaps previous fold "
                "(chronological, non-overlapping required)"
            )
        parsed.append(
            {
                "fold_id": fold_id,
                "start_utc": f_start.isoformat(),
                "end_utc": f_end.isoformat(),
                "purge_days": purge,
                "embargo_days": embargo,
                "_end": f_end,
            }
        )
    return parsed


# --------------------------------------------------------------------------- #
# Bootstrap provenance
# --------------------------------------------------------------------------- #
def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(repo_root), capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise ResolvedContractErrorV8(
            f"git {' '.join(args)} failed in {repo_root}: {proc.stderr.strip()}"
        )
    return proc.stdout


def discover_bootstrap_commit(repo_root: Path) -> tuple[str, str]:
    """(hex, subject) of the first ``BOOTSTRAP:`` commit reachable from HEAD."""
    lines = _git(repo_root, "log", "--reverse", "--format=%H%x1f%s").splitlines()
    candidates = [line.split("\x1f", 1) for line in lines if "\x1f" in line]
    if not candidates:
        raise ResolvedContractErrorV8(
            f"no commits reachable from HEAD in {repo_root}"
        )
    for hex_sha, subject in candidates:
        if subject.startswith("BOOTSTRAP:"):
            return hex_sha, subject
    return candidates[0]


def _source_sha256(repo_root: Path, commit_hex: str) -> str:
    raw = _git(repo_root, "cat-file", "commit", commit_hex).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# --------------------------------------------------------------------------- #
# Contract assembly
# --------------------------------------------------------------------------- #
def build_resolved_contract_v8(
    *,
    window_start: str,
    window_end: str,
    folds: Sequence[Mapping[str, Any]],
    traded_universe: Sequence[str],
    benchmark: str,
    costs: Mapping[str, Any],
    limits: Mapping[str, Any],
    weekly_schedule: Mapping[str, Any],
    dataset_hashes: Mapping[str, str],
    launch_sha: Any,
    trial_inventory: Sequence[Mapping[str, Any]],
    signal_family: str,
    registry_output_contract: Mapping[str, Any],
    execution_contract: Mapping[str, Any],
    provenance_contract: Mapping[str, Any],
    repo_root: str | Path | None = None,
    generated_at_utc: str | None = None,
    **_unexpected: Any,
) -> dict:
    """Build the ordered V8 resolved-run-contract dict; fail closed on gaps.

    Every contract field MUST be passed explicitly and valid — see module
    docstring. ``launch_sha`` is REQUIRED and must be the explicit final
    integration commit SHA (placeholders rejected; must be a reachable git
    commit object). The template stage uses :func:`build_template_contract`
    instead — passing ``launch_sha=None`` here raises by design.
    """
    if _unexpected:
        raise ResolvedContractErrorV8(
            f"unexpected contract arguments {sorted(_unexpected)} (fail-closed: "
            "no implicit acceptance of unknown fields)"
        )
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]

    start_dt = _parse_utc(window_start, "window_start")
    end_dt = _parse_utc(window_end, "window_end")
    if end_dt <= start_dt:
        raise ResolvedContractErrorV8(
            f"window_end {window_end!r} must be after window_start {window_start!r}"
        )

    bench = _require_str(benchmark, "benchmark")
    if bench != BENCHMARK_FROZEN:
        raise ResolvedContractErrorV8(
            f"benchmark must equal {BENCHMARK_FROZEN!r}, got {bench!r}"
        )
    symbols = _validate_universe(traded_universe, bench)
    parsed_folds = _validate_folds(folds, start_dt, end_dt)

    cost_map = _require_mapping(costs, "costs")
    costs_norm = _require_frozen_mapping(cost_map, "costs", COSTS_FROZEN)

    limit_map = _require_mapping(limits, "limits")
    limits_norm = _require_frozen_mapping(limit_map, "limits", LIMITS_FROZEN)

    schedule_map = _require_mapping(weekly_schedule, "weekly_schedule")
    schedule_norm = _require_frozen_mapping(
        schedule_map, "weekly_schedule", WEEKLY_SCHEDULE_FROZEN
    )

    hash_map = _require_mapping(dataset_hashes, "dataset_hashes")
    if not hash_map:
        raise ResolvedContractErrorV8(
            "dataset_hashes must be non-empty in the FINAL contract; the "
            "pre-freeze template may carry {} but freeze_final() must inject "
            "the audited hashes"
        )
    normalized_hashes = {
        _require_str(key, "dataset_hashes key"): _require_sha256_hex(
            value, f"dataset_hashes[{key!r}]"
        )
        for key, value in hash_map.items()
    }

    resolved_launch_sha = _resolve_launch_sha(launch_sha, root)
    inventory = _validate_trial_inventory(trial_inventory)
    family = _require_str(signal_family, "signal_family")
    if family != SIGNAL_FAMILY_FROZEN:
        raise ResolvedContractErrorV8(
            f"signal_family must equal {SIGNAL_FAMILY_FROZEN!r}, got {family!r}"
        )
    registry = _require_frozen_mapping(
        registry_output_contract,
        "registry_output_contract",
        REGISTRY_OUTPUT_CONTRACT_FROZEN,
    )
    execution = _require_execution_contract(execution_contract)
    provenance = _validate_provenance_contract(provenance_contract)

    commit_hex, commit_subject = discover_bootstrap_commit(root)
    src_sha = _source_sha256(root, commit_hex)
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

    contract: dict = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "source_commit": commit_hex,
        "source_commit_subject": commit_subject,
        "source_sha256": src_sha,
        "source_sha256_formula": "sha256(git cat-file commit <source_commit>)",
        "launch_sha": resolved_launch_sha,
        "launch_sha_frozen": True,
        "trial_inventory": inventory,
        "signal_family": family,
        "weekly_schedule": schedule_norm,
        "registry_output_contract": registry,
        "execution_contract": execution,
        "window": {
            "start_utc": start_dt.isoformat(),
            "end_utc": end_dt.isoformat(),
            "days": round((end_dt - start_dt).total_seconds() / 86_400.0, 6),
        },
        "folds": [
            {
                "fold_id": f["fold_id"],
                "start_utc": f["start_utc"],
                "end_utc": f["end_utc"],
                "purge_days": f["purge_days"],
                "embargo_days": f["embargo_days"],
            }
            for f in parsed_folds
        ],
        "universe": {
            "traded_symbols": sorted(symbols),
            "n_traded": len(symbols),
            "benchmark": bench,
        },
        "costs": costs_norm,
        "limits": limits_norm,
        "dataset_hashes": dict(sorted(normalized_hashes.items())),
        "provenance_contract": provenance,
    }
    canonical = json.dumps(contract, sort_keys=True, separators=(",", ":"))
    contract["contract_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return contract


def _require_execution_contract(value: Any) -> dict:
    row = _require_mapping(value, "execution_contract")
    if set(row) != _EXECUTION_KEYS:
        raise ResolvedContractErrorV8(
            f"execution_contract must have exactly keys {sorted(_EXECUTION_KEYS)} "
            f"(no implicit defaults/extras), got {sorted(row)}"
        )
    workers = row["max_concurrent_workers"]
    if isinstance(workers, bool) or not isinstance(workers, int):
        raise ResolvedContractErrorV8(
            f"execution_contract.max_concurrent_workers must be an int, got "
            f"{workers!r}"
        )
    if workers != EXECUTION_CONTRACT_FROZEN["max_concurrent_workers"]:
        raise ResolvedContractErrorV8(
            f"execution_contract.max_concurrent_workers is FROZEN and must "
            f"equal {EXECUTION_CONTRACT_FROZEN['max_concurrent_workers']}, got "
            f"{workers!r}"
        )
    surface = row["stress_surface"]
    if not isinstance(surface, Sequence) or isinstance(surface, (str, bytes)):
        raise ResolvedContractErrorV8(
            "execution_contract.stress_surface must be a sequence of names"
        )
    surface = [str(s) for s in surface]
    if tuple(surface) != _STRESS_SURFACE_FROZEN:
        raise ResolvedContractErrorV8(
            "execution_contract.stress_surface must EXACTLY equal the frozen "
            f"preregistered surface {list(_STRESS_SURFACE_FROZEN)} "
            f"(same members, same order), got {surface!r}"
        )
    return {
        "max_concurrent_workers": workers,
        "stress_surface": list(surface),
    }


def _validate_provenance_contract(value: Any) -> dict:
    """Frozen V8 evidence chain: exact paths + mandatory enforcement."""
    row = _require_mapping(value, "provenance_contract")
    if set(row) != _PROVENANCE_KEYS:
        raise ResolvedContractErrorV8(
            f"provenance_contract must have exactly keys {sorted(_PROVENANCE_KEYS)} "
            f"(no implicit defaults/extras), got {sorted(row)}"
        )
    baseline = _require_str(row["baseline_path"], "provenance_contract.baseline_path")
    if baseline != PROVENANCE_BASELINE_PATH_FROZEN:
        raise ResolvedContractErrorV8(
            f"provenance_contract.baseline_path is a FROZEN V8 decision and must "
            f"equal {PROVENANCE_BASELINE_PATH_FROZEN!r}, got {baseline!r}"
        )
    attestation = _require_str(
        row["attestation_path"], "provenance_contract.attestation_path"
    )
    if attestation != PROVENANCE_ATTESTATION_PATH_FROZEN:
        raise ResolvedContractErrorV8(
            f"provenance_contract.attestation_path is a FROZEN V8 decision and "
            f"must equal {PROVENANCE_ATTESTATION_PATH_FROZEN!r}, got {attestation!r}"
        )
    enforcement = row["enforcement_required"]
    if enforcement is not True:
        raise ResolvedContractErrorV8(
            f"provenance_contract.enforcement_required must be exactly True "
            f"(V8 prelaunch gate enforcement is mandatory), got {enforcement!r}"
        )
    return dict(PROVENANCE_CONTRACT_FROZEN)


def contract_canonical_sha256(contract_without_hash: Mapping[str, Any]) -> str:
    """Recompute the self-hash of a contract payload (verification helper)."""
    canonical = json.dumps(
        contract_without_hash, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_resolved_contract_v8(contract: Mapping[str, Any]) -> None:
    """Raise if a persisted contract/template payload was tampered with."""
    payload = {k: v for k, v in contract.items() if k != "contract_sha256"}
    expected = contract_canonical_sha256(payload)
    if contract.get("contract_sha256") != expected:
        raise ResolvedContractErrorV8(
            f"contract_sha256 mismatch: expected {expected}, "
            f"got {contract.get('contract_sha256')!r}"
        )


def write_contract_json(payload: Mapping[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(target)
    return target


# --------------------------------------------------------------------------- #
# Two-stage freeze: TEMPLATE now (committed), FINAL via freeze_final()
# --------------------------------------------------------------------------- #
def build_template_contract(
    *,
    window_start: str,
    window_end: str,
    folds: Sequence[Mapping[str, Any]],
    dataset_hashes: Mapping[str, str] | None = None,
    repo_root: str | Path | None = None,
    generated_at_utc: str | None = None,
) -> dict:
    """Pre-freeze TEMPLATE body: launch_sha=None + launch_sha_frozen=False.

    Everything except ``launch_sha``/``dataset_hashes`` comes from this
    module's FROZEN constants, so the template can never drift from the
    freeze. ``dataset_hashes`` defaults to ``{}``: audited hashes are
    injected at :func:`freeze_final` time. The payload carries the same
    self-hash mechanism as the final contract (tamper-evidence).
    """
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    start_dt = _parse_utc(window_start, "window_start")
    end_dt = _parse_utc(window_end, "window_end")
    if end_dt <= start_dt:
        raise ResolvedContractErrorV8(
            f"window_end {window_end!r} must be after window_start {window_start!r}"
        )
    parsed_folds = _validate_folds(folds, start_dt, end_dt)
    hashes = dict(dataset_hashes or {})
    for key, value in hashes.items():
        _require_str(key, "dataset_hashes key")
        _require_sha256_hex(value, f"dataset_hashes[{key!r}]")

    commit_hex, commit_subject = discover_bootstrap_commit(root)
    src_sha = _source_sha256(root, commit_hex)
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

    template: dict = {
        "schema_version": SCHEMA_VERSION,
        "artifact_state": "TEMPLATE_PENDING_A1_FREEZE",
        "generated_at_utc": generated,
        "source_commit": commit_hex,
        "source_commit_subject": commit_subject,
        "source_sha256": src_sha,
        "source_sha256_formula": "sha256(git cat-file commit <source_commit>)",
        "launch_sha": None,
        "launch_sha_frozen": False,
        "trial_inventory": [
            {
                "trial_id": tid,
                "formation_lookback_days": FROZEN_TRIAL_SPECS[tid][
                    "formation_lookback_days"
                ],
                "kind": FROZEN_TRIAL_SPECS[tid]["kind"],
            }
            for tid in FROZEN_TRIAL_IDS
        ],
        "signal_family": SIGNAL_FAMILY_FROZEN,
        "weekly_schedule": dict(WEEKLY_SCHEDULE_FROZEN),
        "registry_output_contract": dict(REGISTRY_OUTPUT_CONTRACT_FROZEN),
        "execution_contract": {
            "max_concurrent_workers": EXECUTION_CONTRACT_FROZEN[
                "max_concurrent_workers"
            ],
            "stress_surface": list(_STRESS_SURFACE_FROZEN),
        },
        "window": {
            "start_utc": start_dt.isoformat(),
            "end_utc": end_dt.isoformat(),
            "days": round((end_dt - start_dt).total_seconds() / 86_400.0, 6),
        },
        "folds": [
            {
                "fold_id": f["fold_id"],
                "start_utc": f["start_utc"],
                "end_utc": f["end_utc"],
                "purge_days": f["purge_days"],
                "embargo_days": f["embargo_days"],
            }
            for f in parsed_folds
        ],
        "universe": {
            "traded_symbols": sorted(FROZEN_UNIVERSE),
            "n_traded": len(FROZEN_UNIVERSE),
            "benchmark": BENCHMARK_FROZEN,
        },
        "costs": dict(COSTS_FROZEN),
        "limits": dict(LIMITS_FROZEN),
        "dataset_hashes": dict(sorted(hashes.items())),
        "provenance_contract": dict(PROVENANCE_CONTRACT_FROZEN),
    }
    canonical = json.dumps(template, sort_keys=True, separators=(",", ":"))
    template["contract_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return template


def load_template(
    template_path: str | Path | None = None, repo_root: str | Path | None = None
) -> dict:
    """Load + self-verify the committed template; assert unfrozen state."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    path = Path(template_path) if template_path is not None else root / TEMPLATE_RELPATH
    if not path.is_file():
        raise ResolvedContractErrorV8(f"template artifact missing: {path}")
    template = json.loads(path.read_text(encoding="utf-8"))
    verify_resolved_contract_v8(template)
    if template.get("launch_sha") is not None or template.get("launch_sha_frozen") is not False:
        raise ResolvedContractErrorV8(
            f"template {path} must carry launch_sha=None + launch_sha_frozen="
            f"False; got launch_sha={template.get('launch_sha')!r}, "
            f"launch_sha_frozen={template.get('launch_sha_frozen')!r}"
        )
    return template


def _assert_template_matches_constants(template: Mapping[str, Any]) -> None:
    """Fail closed if the committed template drifted from module constants."""
    checks = {
        "trial_inventory": [
            {
                "trial_id": tid,
                "formation_lookback_days": FROZEN_TRIAL_SPECS[tid][
                    "formation_lookback_days"
                ],
                "kind": FROZEN_TRIAL_SPECS[tid]["kind"],
            }
            for tid in FROZEN_TRIAL_IDS
        ],
        "signal_family": SIGNAL_FAMILY_FROZEN,
        "weekly_schedule": WEEKLY_SCHEDULE_FROZEN,
        "registry_output_contract": REGISTRY_OUTPUT_CONTRACT_FROZEN,
        "execution_contract": EXECUTION_CONTRACT_FROZEN,
        "universe": {
            "traded_symbols": sorted(FROZEN_UNIVERSE),
            "n_traded": len(FROZEN_UNIVERSE),
            "benchmark": BENCHMARK_FROZEN,
        },
        "costs": COSTS_FROZEN,
        "limits": LIMITS_FROZEN,
        "provenance_contract": PROVENANCE_CONTRACT_FROZEN,
    }
    for field, expected in checks.items():
        if template.get(field) != expected:
            raise ResolvedContractErrorV8(
                f"template field {field!r} drifted from the frozen constants: "
                f"expected {expected!r}, got {template.get(field)!r}"
            )


def freeze_final(
    launch_sha: Any,
    *,
    dataset_hashes: Mapping[str, str] | None = None,
    template_path: str | Path | None = None,
    final_path: str | Path | None = None,
    repo_root: str | Path | None = None,
    generated_at_utc: str | None = None,
) -> Path:
    """A1 integration entry point: turn the committed template into the FINAL
    resolved-run-contract artifact.

    Validates ``launch_sha`` as a real commit, refuses to overwrite an
    existing final artifact, re-validates the template against this
    module's frozen constants, requires non-empty audited
    ``dataset_hashes`` (arg wins over the template's placeholder ``{}``),
    rebuilds the canonical contract and writes it atomically to
    ``research/audits/v8p/resolved_run_contract_v8.json``.
    """
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    resolved_launch_sha = _resolve_launch_sha(launch_sha, root)
    tpath = Path(template_path) if template_path is not None else root / TEMPLATE_RELPATH
    fpath = Path(final_path) if final_path is not None else root / CONTRACT_RELPATH
    if fpath.is_file():
        raise ResolvedContractErrorV8(
            f"final artifact already frozen at {fpath}: refuse to overwrite "
            "(single-freeze discipline)"
        )
    template = load_template(tpath, repo_root=root)
    _assert_template_matches_constants(template)
    hashes = dict(template.get("dataset_hashes") or {})
    if dataset_hashes is not None:
        hashes = dict(dataset_hashes)
    if not hashes:
        raise ResolvedContractErrorV8(
            "freeze_final requires non-empty audited dataset_hashes: pass "
            "dataset_hashes=<T12 data-manifest inputs_used> explicitly"
        )
    contract = build_resolved_contract_v8(
        window_start=template["window"]["start_utc"],
        window_end=template["window"]["end_utc"],
        folds=template["folds"],
        traded_universe=template["universe"]["traded_symbols"],
        benchmark=template["universe"]["benchmark"],
        costs=template["costs"],
        limits=template["limits"],
        weekly_schedule=template["weekly_schedule"],
        dataset_hashes=hashes,
        launch_sha=resolved_launch_sha,
        trial_inventory=template["trial_inventory"],
        signal_family=template["signal_family"],
        registry_output_contract=template["registry_output_contract"],
        execution_contract=template["execution_contract"],
        provenance_contract=template["provenance_contract"],
        repo_root=root,
        generated_at_utc=generated_at_utc,
    )
    verify_resolved_contract_v8(contract)
    if contract["launch_sha"] != resolved_launch_sha:
        raise ResolvedContractErrorV8("internal: launch_sha round-trip mismatch")
    return write_contract_json(contract, fpath)


# --------------------------------------------------------------------------- #
# Explicit template generator (committed artifact; no implicit values)
# --------------------------------------------------------------------------- #
def _equal_chronological_folds(start: datetime, end: datetime, n: int) -> list[dict]:
    span = (end - start) / n
    return [
        {
            "fold_id": f"F{i + 1}",
            "start_utc": (start + i * span).isoformat(),
            "end_utc": (start + (i + 1) * span if i + 1 < n else end).isoformat(),
            "purge_days": PURGE_EMBARGO_DAYS_FROZEN,
            "embargo_days": PURGE_EMBARGO_DAYS_FROZEN,
        }
        for i in range(n)
    ]


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--final" in args:
        raise ResolvedContractErrorV8(
            "this generator writes ONLY the template; the final artifact is "
            "produced exclusively by freeze_final(launch_sha) at integration"
        )
    repo_root = Path(__file__).resolve().parents[1]
    # Target window from H-XSECT-REVERSAL-v2 candidate.yaml (data_window);
    # exact completed-bar endpoints remain subject to gate T12 audit.
    window_start = "2024-08-21T14:30:00+00:00"
    window_end = "2026-08-21T00:00:00+00:00"
    folds = _equal_chronological_folds(
        _parse_utc(window_start, "window_start"),
        _parse_utc(window_end, "window_end"),
        3,
    )
    template = build_template_contract(
        window_start=window_start,
        window_end=window_end,
        folds=folds,
        dataset_hashes={},  # audited hashes injected by freeze_final at T14
        repo_root=repo_root,
    )
    verify_resolved_contract_v8(template)
    target = write_contract_json(template, repo_root / TEMPLATE_RELPATH)
    print(f"written={target}")
    print(f"artifact_state={template['artifact_state']}")
    print(f"contract_sha256={template['contract_sha256']}")
    print(f"source_commit={template['source_commit']}")
    print("next_step=A1 calls research.resolved_contract_v8.freeze_final(launch_sha)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
