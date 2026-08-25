"""V7P resolved run contract (PLAN sections 6.1/7 gate C06, owner A6).

Resolves at runtime every field the frozen V7 candidate left open
(``effective_window``, ``data_hashes``, fold layout, cost model, risk
limits, launch SHA). Fail-closed per PLAN C06: there are NO implicit
defaults on any contract field — a caller that omits, nulls or empties a
required argument gets :class:`ResolvedContractError` instead of a
silently defaulted contract.

The ``launch_sha`` is the EXPLICIT final integration commit SHA of the
launch: placeholder semantics (``PENDING_INTEGRATION_SHA``) are removed
and forbidden. It must match ``^[0-9a-f]{40}$`` AND be reachable as a
real commit object in the repository (``git cat-file -e <sha>^{commit}``).
Legacy callers still passing ``launch_sha_placeholder=...`` fail closed.

The trial inventory / signal family / registry-output / execution
contracts below are the FROZEN V7 plan set (PLAN section 8.1/8.2): the
exactly-four trials ``XSECT-FUND-PRICE-DIV-{1D,3D,7D,REV-3D}``, two
execution waves, one ``CELL_RESULT`` registry root. They must be passed
explicitly and equal to the freeze — no partial or drifted inventories.

Provenance fields (``schema_version``, ``generated_at_utc``,
``source_commit``/``source_sha256``) are derived from the repository
itself: the bootstrap commit is discovered by walking ``git log`` from
HEAD for the first ``BOOTSTRAP:`` subject (falling back to the root
commit), and ``source_sha256 = sha256(git cat-file commit <hex>)``.

Regenerate the committed evidence artifact with::

    PYTHONPATH=<repo> python -m research.resolved_contract

``main()`` resolves ``launch_sha`` as the current HEAD of the primary
repository (:data:`PRIMARY_REPO_ROOT`) via ``git rev-parse``; pass an
explicit sha with ``python -m research.resolved_contract --launch-sha <sha>``
to pin it instead.

Dataset hashes are the verified ``inputs_used`` of the frozen V6 data
manifest (funding bundle identity per sibling usage in
``research.portfolio_runner``); V7 inherits the V6 window/cost/limit
contract set per PLAN section 16.2.

The ``provenance_contract`` block (B2 item 6) pins the V7P evidence
chain to its two FROZEN artifact paths plus mandatory enforcement:
``baseline_path`` = ``research/audits/v7p/baseline_root.json``,
``attestation_path`` =
``research/audits/v7p/a7_prelaunch_attestation.json``,
``enforcement_required`` = ``True``. It is a REQUIRED keyword argument
(fail-closed like ``limits``): omitting, nulling or drifting any value
raises :class:`ResolvedContractError`. The block is part of the
canonical body covered by ``contract_sha256``.
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

SCHEMA_VERSION = "v7p.resolved_run_contract.v1"
LAUNCH_SHA_PLACEHOLDER = "PENDING_INTEGRATION_SHA"
CONTRACT_RELPATH = Path("research") / "audits" / "v7p" / "resolved_run_contract.json"
PRIMARY_REPO_ROOT = Path("/Users/hoangminhlong/my-quantitative")

SIGNAL_FAMILY_FROZEN = "funding_price_divergence"
FUNDING_LOOKBACK_DAYS_FROZEN = 3
FROZEN_TRIAL_IDS: tuple[str, ...] = (
    "XSECT-FUND-PRICE-DIV-1D",
    "XSECT-FUND-PRICE-DIV-3D",
    "XSECT-FUND-PRICE-DIV-7D",
    "XSECT-FUND-PRICE-DIV-REV-3D",
)
REV_TRIAL_ID = "XSECT-FUND-PRICE-DIV-REV-3D"
# PLAN section 8.1 freeze table: id -> price_lookback_days -> direction.
FROZEN_TRIAL_SPECS: dict[str, dict[str, Any]] = {
    "XSECT-FUND-PRICE-DIV-1D": {"price_lookback_days": 1, "direction": "normal"},
    "XSECT-FUND-PRICE-DIV-3D": {"price_lookback_days": 3, "direction": "normal"},
    "XSECT-FUND-PRICE-DIV-7D": {"price_lookback_days": 7, "direction": "normal"},
    "XSECT-FUND-PRICE-DIV-REV-3D": {"price_lookback_days": 3, "direction": "reverse"},
}
REGISTRY_OUTPUT_CONTRACT_FROZEN: dict[str, str] = {
    "registry_kind": "CELL_RESULT",
    "output_root": "results/portfolio_v7",
    "matrix_id": "v7_xsect_funding_price_divergence",
    "shard_pattern": "results/registry/shards/v7_<trial_id>.jsonl",
}
EXECUTION_CONTRACT_FROZEN: dict[str, Any] = {
    "max_concurrent_workers": 2,
    "waves": [
        ["XSECT-FUND-PRICE-DIV-1D", "XSECT-FUND-PRICE-DIV-3D"],
        ["XSECT-FUND-PRICE-DIV-7D", "XSECT-FUND-PRICE-DIV-REV-3D"],
    ],
}
# Frozen V7P evidence-chain decision (B2 item 6): the resolved contract is
# only valid against THIS baseline + THIS prelaunch attestation, and the
# attestation's gate enforcement is MANDATORY. Paths are repo-relative and
# exact — no normalization, no alternates.
PROVENANCE_BASELINE_PATH_FROZEN = "research/audits/v7p/baseline_root.json"
PROVENANCE_ATTESTATION_PATH_FROZEN = "research/audits/v7p/a7_prelaunch_attestation.json"
PROVENANCE_CONTRACT_FROZEN: dict[str, Any] = {
    "baseline_path": PROVENANCE_BASELINE_PATH_FROZEN,
    "attestation_path": PROVENANCE_ATTESTATION_PATH_FROZEN,
    "enforcement_required": True,
}

_LAUNCH_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN_LAUNCH_SHA_VALUES = frozenset({LAUNCH_SHA_PLACEHOLDER, "TO_FREEZE"})
_TRIAL_KEYS = frozenset({"trial_id", "price_lookback_days", "direction"})
_PRICE_LOOKBACK_DAYS_ALLOWED = frozenset({1, 3, 7})
_DIRECTIONS_ALLOWED = frozenset({"normal", "reverse"})

_UNSET = object()

_COST_KEYS = frozenset({"fee_taker", "slippage_ticks"})
_LIMIT_KEYS = frozenset({"gross", "net", "symbol_weight"})
_FOLD_KEYS = frozenset({"fold_id", "start_utc", "end_utc"})
_PROVENANCE_KEYS = frozenset(PROVENANCE_CONTRACT_FROZEN)
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


class ResolvedContractError(ValueError):
    """A required contract field is missing/invalid (fail-closed, PLAN C06)."""


# --------------------------------------------------------------------------- #
# Strict primitive validators (no coercion, no defaults)
# --------------------------------------------------------------------------- #
def _require_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ResolvedContractError(f"{name} must be a non-empty string, got {value!r}")
    return value


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ResolvedContractError(f"{name} must be a mapping, got {type(value).__name__}")
    return value


def _require_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ResolvedContractError(f"{name} must be a real number, got {value!r}")
    return float(value)


def _require_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ResolvedContractError(f"{name} must be an int, got {value!r}")
    return int(value)


def _parse_utc(stamp: str, name: str) -> datetime:
    text = _require_str(stamp, name)
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ResolvedContractError(f"{name} must be timezone-aware UTC, got {stamp!r}")
    return parsed.astimezone(timezone.utc)


def _require_sha256_hex(value: Any, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in _HEX_DIGITS for ch in value)
    ):
        raise ResolvedContractError(
            f"{name} must be a 64-char hex sha256 digest, got {value!r}"
        )
    return value.lower()


def _resolve_launch_sha(value: Any, repo_root: Path) -> str:
    """Explicit final launch commit SHA: format-valid AND a real commit."""
    if value is None or isinstance(value, bool) or not isinstance(value, str):
        raise ResolvedContractError(
            f"launch_sha is REQUIRED (explicit final integration SHA), got {value!r}"
        )
    if not value or not value.strip():
        raise ResolvedContractError("launch_sha must be a non-empty 40-hex sha")
    if value.strip().upper() in {v.upper() for v in _FORBIDDEN_LAUNCH_SHA_VALUES}:
        raise ResolvedContractError(
            f"launch_sha placeholder {value!r} is FORBIDDEN in the final artifact "
            f"(PLAN C06): pass the explicit final integration commit SHA"
        )
    if not _LAUNCH_SHA_RE.match(value):
        raise ResolvedContractError(
            f"launch_sha must match ^[0-9a-f]{{40}}$, got {value!r}"
        )
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{value}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise ResolvedContractError(
            f"launch_sha_not_a_commit: {value!r} is not reachable as a commit "
            f"in {repo_root}: {proc.stderr.strip()}"
        )
    return value


def _validate_trial_inventory(value: Any) -> list[dict]:
    """Exactly the four frozen trials; reverse only on REV-3D lookback 3."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise ResolvedContractError(
            "trial_inventory must be a non-empty sequence of trial mappings"
        )
    rows: list[dict] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(value):
        where = f"trial_inventory[{idx}]"
        row = _require_mapping(item, where)
        if set(row) != _TRIAL_KEYS:
            raise ResolvedContractError(
                f"{where} must have exactly keys {sorted(_TRIAL_KEYS)}, "
                f"got {sorted(row)}"
            )
        trial_id = _require_str(row["trial_id"], f"{where}.trial_id")
        if trial_id not in FROZEN_TRIAL_SPECS:
            raise ResolvedContractError(
                f"{where}.trial_id {trial_id!r} is not one of the frozen V7 "
                f"trials {sorted(FROZEN_TRIAL_SPECS)}"
            )
        if trial_id in seen_ids:
            raise ResolvedContractError(f"duplicate trial_id {trial_id!r}")
        seen_ids.add(trial_id)
        lookback = row["price_lookback_days"]
        if isinstance(lookback, bool) or not isinstance(lookback, int):
            raise ResolvedContractError(
                f"{where}.price_lookback_days must be an int in "
                f"{sorted(_PRICE_LOOKBACK_DAYS_ALLOWED)}, got {lookback!r}"
            )
        if lookback not in _PRICE_LOOKBACK_DAYS_ALLOWED:
            raise ResolvedContractError(
                f"{where}.price_lookback_days must be one of "
                f"{sorted(_PRICE_LOOKBACK_DAYS_ALLOWED)}, got {lookback!r}"
            )
        direction = row["direction"]
        if direction not in _DIRECTIONS_ALLOWED:
            raise ResolvedContractError(
                f"{where}.direction must be 'normal' or 'reverse', got {direction!r}"
            )
        frozen = FROZEN_TRIAL_SPECS[trial_id]
        if lookback != frozen["price_lookback_days"] or direction != frozen["direction"]:
            raise ResolvedContractError(
                f"{where} drifts from the frozen spec for {trial_id}: expected "
                f"{frozen}, got price_lookback_days={lookback}, direction={direction!r}"
            )
        if direction == "reverse" and trial_id != REV_TRIAL_ID:
            raise ResolvedContractError(
                f"reverse direction only allowed on {REV_TRIAL_ID}, got {trial_id!r}"
            )
        if direction == "reverse" and lookback != FUNDING_LOOKBACK_DAYS_FROZEN:
            raise ResolvedContractError(
                f"reverse trial {trial_id!r} must use price_lookback_days="
                f"{FUNDING_LOOKBACK_DAYS_FROZEN}, got {lookback}"
            )
        rows.append({"trial_id": trial_id, "price_lookback_days": int(lookback),
                     "direction": direction})
    if len(rows) != len(FROZEN_TRIAL_IDS):
        raise ResolvedContractError(
            f"trial_inventory must contain exactly {len(FROZEN_TRIAL_IDS)} frozen "
            f"trials {list(FROZEN_TRIAL_IDS)}, got {len(rows)} entries"
        )
    missing = [tid for tid in FROZEN_TRIAL_IDS if tid not in seen_ids]
    if missing:
        raise ResolvedContractError(f"trial_inventory is missing frozen trials {missing}")
    # Canonical freeze order regardless of caller ordering -> stable hash.
    order = {tid: i for i, tid in enumerate(FROZEN_TRIAL_IDS)}
    return sorted(rows, key=lambda r: order[r["trial_id"]])


def _validate_signal_family(value: Any) -> str:
    family = _require_str(value, "signal_family")
    if family != SIGNAL_FAMILY_FROZEN:
        raise ResolvedContractError(
            f"signal_family must equal {SIGNAL_FAMILY_FROZEN!r}, got {family!r}"
        )
    return family


def _validate_funding_lookback_days(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ResolvedContractError(
            f"funding_lookback_days must be the int {FUNDING_LOOKBACK_DAYS_FROZEN}, "
            f"got {value!r}"
        )
    if value != FUNDING_LOOKBACK_DAYS_FROZEN:
        raise ResolvedContractError(
            f"funding_lookback_days must equal {FUNDING_LOOKBACK_DAYS_FROZEN}, "
            f"got {value}"
        )
    return value


def _require_frozen_mapping(value: Any, name: str, frozen: Mapping[str, Any]) -> dict:
    row = _require_mapping(value, name)
    if dict(row) != dict(frozen):
        raise ResolvedContractError(
            f"{name} must exactly equal the frozen contract {dict(frozen)!r}, "
            f"got {dict(row)!r}"
        )
    return dict(frozen)


def _validate_provenance_contract(value: Any) -> dict:
    """Frozen V7P evidence chain (B2 item 6): exact paths + mandatory enforcement."""
    row = _require_mapping(value, "provenance_contract")
    if set(row) != _PROVENANCE_KEYS:
        raise ResolvedContractError(
            f"provenance_contract must have exactly keys {sorted(_PROVENANCE_KEYS)} "
            f"(no implicit defaults/extras), got {sorted(row)}"
        )
    baseline = _require_str(row["baseline_path"], "provenance_contract.baseline_path")
    if baseline != PROVENANCE_BASELINE_PATH_FROZEN:
        raise ResolvedContractError(
            f"provenance_contract.baseline_path is a FROZEN V7P decision and must "
            f"equal {PROVENANCE_BASELINE_PATH_FROZEN!r}, got {baseline!r}"
        )
    attestation = _require_str(
        row["attestation_path"], "provenance_contract.attestation_path"
    )
    if attestation != PROVENANCE_ATTESTATION_PATH_FROZEN:
        raise ResolvedContractError(
            f"provenance_contract.attestation_path is a FROZEN V7P decision and "
            f"must equal {PROVENANCE_ATTESTATION_PATH_FROZEN!r}, got {attestation!r}"
        )
    enforcement = row["enforcement_required"]
    if enforcement is not True:
        raise ResolvedContractError(
            f"provenance_contract.enforcement_required must be exactly True "
            f"(V7P prelaunch gate enforcement is mandatory), got {enforcement!r}"
        )
    return dict(PROVENANCE_CONTRACT_FROZEN)


# --------------------------------------------------------------------------- #
# Bootstrap provenance
# --------------------------------------------------------------------------- #
def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(repo_root), capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise ResolvedContractError(
            f"git {' '.join(args)} failed in {repo_root}: {proc.stderr.strip()}"
        )
    return proc.stdout


def discover_bootstrap_commit(repo_root: Path) -> tuple[str, str]:
    """(hex, subject) of the first ``BOOTSTRAP:`` commit reachable from HEAD."""
    lines = _git(repo_root, "log", "--reverse", "--format=%H%x1f%s").splitlines()
    candidates = [line.split("\x1f", 1) for line in lines if "\x1f" in line]
    if not candidates:
        raise ResolvedContractError(f"no commits reachable from HEAD in {repo_root}")
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
def build_resolved_contract(
    *,
    window_start: str,
    window_end: str,
    folds: Sequence[Mapping[str, Any]],
    traded_universe: Sequence[str],
    benchmark: str,
    costs: Mapping[str, Any],
    limits: Mapping[str, Any],
    dataset_hashes: Mapping[str, str],
    provenance_contract: Mapping[str, Any],
    launch_sha: Any = _UNSET,
    trial_inventory: Sequence[Mapping[str, Any]],
    signal_family: str,
    funding_lookback_days: int,
    registry_output_contract: Mapping[str, Any],
    execution_contract: Mapping[str, Any],
    repo_root: str | Path | None = None,
    generated_at_utc: str | None = None,
    launch_sha_placeholder: Any = _UNSET,
    **_unexpected: Any,
) -> dict:
    """Build the ordered resolved-run-contract dict; fail closed on any gap.

    Every contract field MUST be passed explicitly and valid — see module
    docstring. ``launch_sha`` is the EXPLICIT final integration commit SHA:
    placeholders (``PENDING_INTEGRATION_SHA``/``TO_FREEZE``) are rejected,
    and the sha must be reachable as a real commit in the repository.
    ``provenance_contract`` is REQUIRED (fail-closed like ``limits``) and
    must equal the frozen V7P evidence-chain block exactly.
    Legacy callers passing ``launch_sha_placeholder=...`` now raise
    :class:`ResolvedContractError` (placeholder semantics removed).
    ``repo_root``/``generated_at_utc`` are provenance anchors
    (repository/clock), not contract fields, and may be overridden in tests.
    """
    if launch_sha_placeholder is not _UNSET:
        raise ResolvedContractError(
            "launch_sha_placeholder was REMOVED (PLAN C06 forbids placeholders "
            "in the final artifact): pass the explicit final launch_sha instead "
            f"(got {launch_sha_placeholder!r})"
        )
    if _unexpected:
        raise ResolvedContractError(
            f"unexpected contract arguments {sorted(_unexpected)} (fail-closed: "
            "no implicit acceptance of unknown fields)"
        )
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]

    start_dt = _parse_utc(window_start, "window_start")
    end_dt = _parse_utc(window_end, "window_end")
    if end_dt <= start_dt:
        raise ResolvedContractError(
            f"window_end {window_end!r} must be after window_start {window_start!r}"
        )

    bench = _require_str(benchmark, "benchmark")
    if not isinstance(traded_universe, Sequence) or isinstance(traded_universe, (str, bytes)):
        raise ResolvedContractError("traded_universe must be a sequence of symbols")
    symbols = [str(s) for s in traded_universe]
    if not symbols:
        raise ResolvedContractError("traded_universe must be non-empty")
    if any(not s.strip() for s in symbols):
        raise ResolvedContractError(f"traded_universe contains blank symbols: {symbols!r}")
    if len(set(symbols)) != len(symbols):
        raise ResolvedContractError(f"traded_universe has duplicates: {symbols!r}")
    if bench in symbols:
        raise ResolvedContractError(
            f"benchmark {bench!r} must not appear in traded_universe (context-only)"
        )

    if not isinstance(folds, Sequence) or isinstance(folds, (str, bytes)) or not folds:
        raise ResolvedContractError("folds must be a non-empty sequence of fold mappings")
    seen_ids: set[str] = set()
    parsed_folds: list[dict] = []
    for idx, item in enumerate(folds):
        where = f"folds[{idx}]"
        row = _require_mapping(item, where)
        if set(row) != _FOLD_KEYS:
            raise ResolvedContractError(
                f"{where} must have exactly keys {sorted(_FOLD_KEYS)}, got {sorted(row)}"
            )
        fold_id = _require_str(row["fold_id"], f"{where}.fold_id")
        if fold_id in seen_ids:
            raise ResolvedContractError(f"duplicate fold_id {fold_id!r}")
        seen_ids.add(fold_id)
        f_start = _parse_utc(row["start_utc"], f"{where}.start_utc")
        f_end = _parse_utc(row["end_utc"], f"{where}.end_utc")
        if f_end <= f_start:
            raise ResolvedContractError(f"{where} window must satisfy start < end")
        if f_start < start_dt or f_end > end_dt:
            raise ResolvedContractError(f"{where} escapes the declared window")
        if parsed_folds and f_start < parsed_folds[-1]["_end"]:
            raise ResolvedContractError(
                f"{where} overlaps previous fold (chronological, non-overlapping required)"
            )
        parsed_folds.append(
            {"fold_id": fold_id, "start_utc": f_start, "end_utc": f_end, "_end": f_end}
        )

    cost_map = _require_mapping(costs, "costs")
    if set(cost_map) != _COST_KEYS:
        raise ResolvedContractError(
            f"costs must have exactly keys {sorted(_COST_KEYS)} "
            f"(no implicit defaults/extras), got {sorted(cost_map)}"
        )
    fee_taker = _require_number(cost_map["fee_taker"], "costs.fee_taker")
    if not 0.0 < fee_taker < 1.0:
        raise ResolvedContractError(f"costs.fee_taker must be in (0, 1), got {fee_taker!r}")
    slippage_ticks = _require_int(cost_map["slippage_ticks"], "costs.slippage_ticks")
    if slippage_ticks < 0:
        raise ResolvedContractError(
            f"costs.slippage_ticks must be >= 0, got {slippage_ticks!r}"
        )

    limit_map = _require_mapping(limits, "limits")
    if set(limit_map) != _LIMIT_KEYS:
        raise ResolvedContractError(
            f"limits must have exactly keys {sorted(_LIMIT_KEYS)} "
            f"(no implicit defaults/extras), got {sorted(limit_map)}"
        )
    gross = _require_number(limit_map["gross"], "limits.gross")
    net = _require_number(limit_map["net"], "limits.net")
    symbol_weight = _require_number(limit_map["symbol_weight"], "limits.symbol_weight")
    if not 0.0 < net <= gross <= 1.0:
        raise ResolvedContractError(
            f"limits must satisfy 0 < net <= gross <= 1, got "
            f"net={net!r} gross={gross!r}"
        )
    if not 0.0 < symbol_weight <= 1.0:
        raise ResolvedContractError(
            f"limits.symbol_weight must be in (0, 1], got {symbol_weight!r}"
        )

    hash_map = _require_mapping(dataset_hashes, "dataset_hashes")
    if not hash_map:
        raise ResolvedContractError("dataset_hashes must be non-empty")
    normalized_hashes = {
        _require_str(key, "dataset_hashes key"): _require_sha256_hex(value, f"dataset_hashes[{key!r}]")
        for key, value in hash_map.items()
    }

    if launch_sha is _UNSET:
        raise ResolvedContractError(
            "launch_sha is REQUIRED (explicit final integration commit SHA): "
            "no value was passed"
        )
    resolved_launch_sha = _resolve_launch_sha(launch_sha, root)
    inventory = _validate_trial_inventory(trial_inventory)
    family = _validate_signal_family(signal_family)
    fund_lb = _validate_funding_lookback_days(funding_lookback_days)
    registry = _require_frozen_mapping(
        registry_output_contract, "registry_output_contract", REGISTRY_OUTPUT_CONTRACT_FROZEN
    )
    execution = _require_frozen_mapping(
        execution_contract, "execution_contract", EXECUTION_CONTRACT_FROZEN
    )
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
        "trial_inventory": inventory,
        "signal_family": family,
        "funding_lookback_days": fund_lb,
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
                "start_utc": f["start_utc"].isoformat(),
                "end_utc": f["end_utc"].isoformat(),
            }
            for f in parsed_folds
        ],
        "universe": {
            "traded_symbols": sorted(symbols),
            "n_traded": len(symbols),
            "benchmark": bench,
        },
        "costs": {"fee_taker": fee_taker, "slippage_ticks": slippage_ticks},
        "limits": {"gross": gross, "net": net, "symbol_weight": symbol_weight},
        "dataset_hashes": dict(sorted(normalized_hashes.items())),
        "provenance_contract": provenance,
    }
    canonical = json.dumps(contract, sort_keys=True, separators=(",", ":"))
    contract["contract_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return contract


def contract_canonical_sha256(contract_without_hash: Mapping[str, Any]) -> str:
    """Recompute the self-hash of a contract payload (verification helper)."""
    canonical = json.dumps(contract_without_hash, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_resolved_contract(contract: Mapping[str, Any]) -> None:
    """Raise :class:`ResolvedContractError` if a persisted contract is tampered."""
    payload = {k: v for k, v in contract.items() if k != "contract_sha256"}
    expected = contract_canonical_sha256(payload)
    if contract.get("contract_sha256") != expected:
        raise ResolvedContractError(
            f"contract_sha256 mismatch: expected {expected}, "
            f"got {contract.get('contract_sha256')!r}"
        )


def write_resolved_contract(contract: Mapping[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(contract, indent=2, ensure_ascii=False) + "\n"
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(target)
    return target


# --------------------------------------------------------------------------- #
# Explicit evidence generator (committed artifact; no implicit values)
# --------------------------------------------------------------------------- #
def _equal_chronological_folds(start: datetime, end: datetime, n: int) -> list[dict]:
    span = (end - start) / n
    return [
        {
            "fold_id": f"F{i + 1}",
            "start_utc": (start + i * span).isoformat(),
            "end_utc": (start + (i + 1) * span if i + 1 < n else end).isoformat(),
        }
        for i in range(n)
    ]


def resolve_primary_head(primary_root: Path = PRIMARY_REPO_ROOT) -> str:
    """Full HEAD sha of the primary repository (the integration launch ref)."""
    proc = subprocess.run(
        ["git", "-C", str(primary_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise ResolvedContractError(
            f"git rev-parse HEAD failed in {primary_root}: {proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    launch_sha: str | None = None
    if "--launch-sha" in args:
        idx = args.index("--launch-sha")
        if idx + 1 >= len(args):
            raise ResolvedContractError("--launch-sha requires a value")
        launch_sha = args[idx + 1]
    if launch_sha is None:
        # The explicit final integration SHA: current primary repository HEAD.
        launch_sha = resolve_primary_head()

    repo_root = Path(__file__).resolve().parents[1]
    window_start = "2025-08-21T14:30:00+00:00"
    window_end = "2026-08-21T00:00:00+00:00"
    folds = _equal_chronological_folds(
        _parse_utc(window_start, "window_start"),
        _parse_utc(window_end, "window_end"),
        3,
    )
    contract = build_resolved_contract(
        window_start=window_start,
        window_end=window_end,
        folds=folds,
        traded_universe=[
            "ETHUSDT", "SOLUSDT", "BNBUSDT",
            "XRPUSDT", "DOGEUSDT", "LINKUSDT", "ADAUSDT",
        ],
        benchmark="BTCUSDT",
        costs={"fee_taker": 0.0005, "slippage_ticks": 1},
        limits={"gross": 0.80, "net": 0.10, "symbol_weight": 0.20},
        dataset_hashes={
            "funding_bundle:ETHUSDT": "8f39023ae3046fcdd2e7c6cce54102c7d8ace85c355826bb4c3afdf19b996b04",
            "funding_bundle:SOLUSDT": "0bc86d3b74f5877751b70971f29711eae0d94a4894a53ce4ed23e2ecff0fc543",
            "funding_bundle:BNBUSDT": "194d0729c564fc9bacb92233e1c3977b1370f59a194249439f8baf442eadf4be",
            "funding_bundle:XRPUSDT": "337ac2bf8a2d66067cff4c6d731fbdb529719f5fff3b08677ae58e2606d9d169",
            "funding_bundle:DOGEUSDT": "fa4833419cf369ed88a3ac70cad8ecc4b8525e32dc9ed094174e25bf864f5232",
            "funding_bundle:LINKUSDT": "60060f680fe48a60e3286081d4c55b6f21973e9c0baaa887a0c2f0f50c16c82e",
            "funding_bundle:ADAUSDT": "492ad0aebee58cf1f567901e11d7223f6d8a168e28f58b6bad9a4936d47aa908",
            "v6p_coverage_audit": "d291564d91f0433318fcbbba5accaa438de2897ede6cd92df0ef48334ac7d84d",
        },
        provenance_contract=dict(PROVENANCE_CONTRACT_FROZEN),
        launch_sha=launch_sha,
        trial_inventory=[
            {"trial_id": "XSECT-FUND-PRICE-DIV-1D",
             "price_lookback_days": 1, "direction": "normal"},
            {"trial_id": "XSECT-FUND-PRICE-DIV-3D",
             "price_lookback_days": 3, "direction": "normal"},
            {"trial_id": "XSECT-FUND-PRICE-DIV-7D",
             "price_lookback_days": 7, "direction": "normal"},
            {"trial_id": "XSECT-FUND-PRICE-DIV-REV-3D",
             "price_lookback_days": 3, "direction": "reverse"},
        ],
        signal_family=SIGNAL_FAMILY_FROZEN,
        funding_lookback_days=FUNDING_LOOKBACK_DAYS_FROZEN,
        registry_output_contract=dict(REGISTRY_OUTPUT_CONTRACT_FROZEN),
        execution_contract={
            "max_concurrent_workers": EXECUTION_CONTRACT_FROZEN["max_concurrent_workers"],
            "waves": [list(w) for w in EXECUTION_CONTRACT_FROZEN["waves"]],
        },
        repo_root=repo_root,
    )
    target = write_resolved_contract(contract, repo_root / CONTRACT_RELPATH)
    print(f"written={target}")
    print(f"contract_sha256={contract['contract_sha256']}")
    print(f"source_commit={contract['source_commit']}")
    print(f"source_sha256={contract['source_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
