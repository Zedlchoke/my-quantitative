"""V7P resolved run contract (PLAN sections 6.1/7 gate C06, owner A6).

Resolves at runtime every field the frozen V7 candidate left open
(``effective_window``, ``data_hashes``, fold layout, cost model, risk
limits, launch SHA). Fail-closed per PLAN C06: there are NO implicit
defaults on any contract field — a caller that omits, nulls or empties a
required argument gets :class:`ResolvedContractError` instead of a
silently defaulted contract.

Provenance fields (``schema_version``, ``generated_at_utc``,
``source_commit``/``source_sha256``) are derived from the repository
itself: the bootstrap commit is discovered by walking ``git log`` from
HEAD for the first ``BOOTSTRAP:`` subject (falling back to the root
commit), and ``source_sha256 = sha256(git cat-file commit <hex>)``.

Regenerate the committed evidence artifact with::

    PYTHONPATH=<repo> python -m research.resolved_contract

Every value below is passed explicitly (V7 inherits the V6 data/window/
cost/limit contract set per PLAN section 16.2; dataset hashes are the
verified ``inputs_used`` of the frozen V6 data manifest).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "v7p.resolved_run_contract.v1"
LAUNCH_SHA_PLACEHOLDER = "PENDING_INTEGRATION_SHA"
CONTRACT_RELPATH = Path("research") / "audits" / "v7p" / "resolved_run_contract.json"

_COST_KEYS = frozenset({"fee_taker", "slippage_ticks"})
_LIMIT_KEYS = frozenset({"gross", "net", "symbol_weight"})
_FOLD_KEYS = frozenset({"fold_id", "start_utc", "end_utc"})
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
    launch_sha_placeholder: str,
    repo_root: str | Path | None = None,
    generated_at_utc: str | None = None,
) -> dict:
    """Build the ordered resolved-run-contract dict; fail closed on any gap.

    Every contract field MUST be passed explicitly and valid — see module
    docstring. ``repo_root``/``generated_at_utc`` are provenance anchors
    (repository/clock), not contract fields, and may be overridden in tests.
    """
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

    placeholder = _require_str(launch_sha_placeholder, "launch_sha_placeholder")

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
        "launch_sha": placeholder,
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


def main() -> int:
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
        launch_sha_placeholder=LAUNCH_SHA_PLACEHOLDER,
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
