"""A4 safe cache semantics + fail-closed shared-cache merge gate (PLAN H06).

Safe performance flow (H06): prepare immutable raw inputs, build a
deterministic signal schedule, run base, then reuse process-locally for the
frozen stress variants. This module provides the three primitives:

* :func:`make_cache_key` -- deterministic SHA-256 key over the FULL input
  surface (data/catalog hash, symbols, window, bar type, funding model,
  signal inputs). Canonical JSON with sorted keys and explicit separators;
  dict inputs are order-insensitive; symbol collections are normalized
  (sorted) so universe order cannot split the cache; every component is
  key-material, so changing ANY component changes the key.
* :class:`ProcessLocalCache` -- plain-dict-backed get/put store that exists
  only inside its creating process. It can NEVER persist across processes
  (pickling/copying raises), and every reproduction constructs a FRESH
  cache in a fresh process -- scored results/orders/positions/metrics are
  never reused (H08-16).
* :class:`SharedCacheMergeGate` -- fail-closed adoption gate for sharing a
  cache across runs. THREE proofs are required before shared-cache
  adoption: (a) parity -- artifacts produced with cache ON vs OFF are
  byte-identical (SHA-256 manifests of the artifact sets compared);
  (b) an independent rerun reported ``all_match`` (reproduction parity);
  (c) raw-read budget -- an instrumented counter proves the full-stress
  pipeline reads raw bars at most twice. Additionally the wall-time
  reduction vs the uncached baseline must reach the 30% target; under
  ``strict=True`` (default) a miss or unknown wall time REJECTS the merge,
  under ``strict=False`` it degrades to advisory-only. Any missing or
  uncertain proof rejects regardless of ``strict``. Once PnL is visible
  (``pnl_seen``) no cache/concurrency posture change is permitted except
  reductions, so adoption requests are rejected.

All decisions are returned as machine-readable dicts with explicit reasons;
nothing here writes into ``data/`` or ``results/``, touches the network, or
imports engine code.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

__all__ = [
    "CACHE_KEY_SCHEMA",
    "ProcessLocalCache",
    "SharedCacheMergeGate",
    "adopt_shared_cache",
    "make_cache_key",
    "sha256_file_chunked",
]

#: Schema tag embedded in every cache-key payload so a format change
#: invalidates all previously derived keys.
CACHE_KEY_SCHEMA = "orca.cache.v10.key.v1"

_DECISION_SCHEMA_VERSION = 1


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# cache keys
# --------------------------------------------------------------------------- #
def _canonical_json(obj: Any) -> str:
    """Deterministic serialization: sorted keys + explicit separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def make_cache_key(*, data_catalog_hash: Any,
                   symbols: Any,
                   window_start: Any,
                   window_end: Any,
                   bar_type: Any,
                   funding_model: Any,
                   signal_inputs: Mapping[str, Any]) -> str:
    """Deterministic sha256 cache key over the full H06 input surface.

    Every component is mandatory keyword-only key material: changing any of
    them changes the key. Dict inputs (``signal_inputs``, nested maps) are
    order-insensitive via canonical sorted-key JSON; ``symbols`` is sorted
    before hashing so universe ordering never splits equivalent work.
    Non-JSON-serializable components raise ``TypeError`` (fail closed)
    instead of silently hashing unstable reprs.
    """
    if not isinstance(signal_inputs, Mapping):
        raise TypeError("signal_inputs must be a mapping")
    try:
        payload = {
            "schema": CACHE_KEY_SCHEMA,
            "data_catalog_hash": data_catalog_hash,
            "symbols": sorted(str(symbol) for symbol in symbols),
            "window_start": window_start,
            "window_end": window_end,
            "bar_type": bar_type,
            "funding_model": funding_model,
            "signal_inputs": signal_inputs,
        }
        canonical = _canonical_json(payload)
    except (TypeError, ValueError) as exc:
        raise TypeError(
            f"cache-key components must be canonically JSON-serializable: {exc}"
        ) from exc
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# process-local cache
# --------------------------------------------------------------------------- #
class ProcessLocalCache:
    """Dict-backed cache that NEVER survives its creating process.

    Reproduction semantics (H06/H08-16): each reproduction runs in a fresh
    process with a FRESH cache; nothing scored (results, orders, positions,
    metrics) is ever reused across processes. Enforcement beyond memory
    lifetime: pickling or copying an instance raises ``TypeError`` so the
    store cannot smuggle itself into a payload, checkpoint or subprocess
    argument.
    """

    cache_mode = "process_local"
    persists_across_processes = False

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._created_pid = os.getpid()
        self.hits = 0
        self.misses = 0

    def get(self, key: str, default: Any = None) -> Any:
        if os.getpid() != self._created_pid:  # defensive; unreachable in-memory
            raise RuntimeError("ProcessLocalCache used outside its creating process")
        if key in self._store:
            self.hits += 1
            return self._store[key]
        self.misses += 1
        return default

    def put(self, key: str, value: Any) -> Any:
        self._store[key] = value
        return value

    def __contains__(self, key: object) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)

    def stats(self) -> dict[str, int | str]:
        return {
            "cache_mode": self.cache_mode,
            "entries": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
        }

    def __getstate__(self) -> None:
        raise TypeError(
            "ProcessLocalCache must never be persisted/pickled across "
            "processes; reproduction always constructs a FRESH cache")

    def __reduce__(self) -> None:
        raise TypeError(
            "ProcessLocalCache must never be persisted/pickled across "
            "processes; reproduction always constructs a FRESH cache")


# --------------------------------------------------------------------------- #
# artifact manifests / byte parity
# --------------------------------------------------------------------------- #
def sha256_file_chunked(path: str | Path, chunk_size: int = 1 << 20) -> str:
    """Streaming SHA-256 of file bytes (constant memory)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SharedCacheMergeGate:
    """Fail-closed adoption gate for shared-cache merges (H06).

    Required proofs:
      * ``parity_proof``: cache-ON vs cache-OFF artifact sets are
        byte-identical (sha256 manifest equality over every file).
      * ``repro_all_match``: an INDEPENDENT rerun reproduced all surfaces.
      * ``raw_reads``: instrumented full-stress pipeline read raw bars at
        most ``max_raw_reads`` times (default 2).

    Performance target: wall-time reduction vs uncached baseline must reach
    ``min_wall_time_reduction`` (default 0.30). Under ``strict=True``
    (default) a miss OR UNKNOWN reduction rejects; under ``strict=False``
    the performance criterion is advisory-only. Proof failures are hard in
    every mode. With ``pnl_seen=True`` any adoption is rejected: once PnL
    is visible, concurrency/cache posture may only be REDUCED, never
    changed toward caching.
    """

    SCHEMA_VERSION = 1
    MIN_WALL_TIME_REDUCTION = 0.30
    MAX_RAW_READS_FULL_STRESS = 2

    def __init__(self,
                 *,
                 min_wall_time_reduction: float = MIN_WALL_TIME_REDUCTION,
                 max_raw_reads: int = MAX_RAW_READS_FULL_STRESS) -> None:
        self.min_wall_time_reduction = float(min_wall_time_reduction)
        self.max_raw_reads = int(max_raw_reads)

    # -- manifests ----------------------------------------------------------
    @staticmethod
    def sha256_manifest(artifact_dir: str | Path) -> dict[str, str]:
        """Deterministic ``{relpath_posix: sha256}`` over ALL files below
        ``artifact_dir`` (nested included, sorted); raises OSError when the
        root is not a readable directory."""
        root = Path(artifact_dir)
        if not root.is_dir():
            raise NotADirectoryError(f"artifact dir missing: {root}")
        manifest: dict[str, str] = {}
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            rel = path.relative_to(root).as_posix()
            manifest[rel] = sha256_file_chunked(path)
        return manifest

    @classmethod
    def parity_from_dirs(cls,
                         cached_on_dir: str | Path,
                         cached_off_dir: str | Path,
                         ) -> tuple[bool | None, str | None]:
        """Byte-parity proof from two artifact directories.

        Returns ``(True, None)`` when manifests match exactly, ``(False,
        reason)`` naming up to 8 differing relpaths, or ``(None, reason)``
        when either side is unreadable (uncertainty fails closed).
        """
        try:
            on_manifest = cls.sha256_manifest(cached_on_dir)
            off_manifest = cls.sha256_manifest(cached_off_dir)
        except OSError as exc:
            return None, f"parity_manifest_unreadable:{exc}"
        if on_manifest == off_manifest:
            return True, None
        differing = sorted(
            rel for rel in set(on_manifest) | set(off_manifest)
            if on_manifest.get(rel) != off_manifest.get(rel))
        shown = ";".join(f"artifact_differs:{rel}" for rel in differing[:8])
        more = f";+{len(differing) - 8}_more" if len(differing) > 8 else ""
        return False, f"artifact_manifest_mismatch:{shown}{more}"

    # -- decision -----------------------------------------------------------
    def evaluate(self,
                 *,
                 parity_proof: bool | None = None,
                 parity_dirs: tuple[str | Path, str | Path] | None = None,
                 repro_all_match: bool | None = None,
                 raw_reads: int | float | None = None,
                 wall_time_cached_s: float | None = None,
                 wall_time_uncached_s: float | None = None,
                 strict: bool = True,
                 pnl_seen: bool = False) -> dict[str, Any]:
        """Return the adoption decision object (never raises for evidence
        problems; uncertainty becomes rejection reasons)."""
        reasons: list[str] = []
        advisory_notes: list[str] = []
        proofs: dict[str, Any] = {}

        # (a) parity proof -----------------------------------------------------
        parity_value: bool | None = parity_proof
        if parity_dirs is not None:
            parity_value, why = self.parity_from_dirs(*parity_dirs)
            if parity_value is not True and why is not None:
                reasons.append(why)
        proofs["parity_proof"] = parity_value
        if parity_value is True:
            pass
        elif parity_value is False:
            if parity_dirs is None:
                reasons.append("parity_proof_false")
        else:
            reasons.append("parity_proof_missing_or_uncertain")

        # (b) independent rerun all-match --------------------------------------
        proofs["repro_all_match"] = (
            bool(repro_all_match) if repro_all_match is not None else None)
        if repro_all_match is True:
            pass
        elif repro_all_match is False:
            reasons.append("independent_reproduction_not_all_match")
        else:
            reasons.append("repro_all_match_proof_missing_or_uncertain")

        # (c) raw-read budget ---------------------------------------------------
        reads_valid = False
        if raw_reads is None:
            proofs["raw_reads"] = None
            reasons.append("raw_reads_counter_missing_or_uncertain")
        elif isinstance(raw_reads, bool) or not isinstance(raw_reads, (int, float)) \
                or not math.isfinite(float(raw_reads)):
            proofs["raw_reads"] = None
            reasons.append("raw_reads_counter_not_numeric")
        elif raw_reads < 0:
            proofs["raw_reads"] = raw_reads
            reasons.append("raw_reads_counter_negative")
        else:
            proofs["raw_reads"] = raw_reads
            reads_valid = True
            if int(raw_reads) > self.max_raw_reads:
                reasons.append(
                    f"raw_reads_budget_exceeded:{int(raw_reads)}>"
                    f"{self.max_raw_reads}")
        if reads_valid:
            proofs["raw_reads_budget_max"] = self.max_raw_reads

        # wall-time reduction metric -------------------------------------------
        reduction: float | None = None
        try:
            base = float(wall_time_uncached_s)
            cached = float(wall_time_cached_s)
            if math.isfinite(base) and math.isfinite(cached) and base > 0 \
                    and cached >= 0:
                reduction = (base - cached) / base
        except (TypeError, ValueError):
            reduction = None
        perf_ok = reduction is not None and reduction >= self.min_wall_time_reduction
        if perf_ok:
            pass
        else:
            detail = (
                f"wall_time_reduction_below_target:"
                f"{reduction:.6f}<{self.min_wall_time_reduction}"
                if reduction is not None
                else "wall_time_reduction_unknown")
            if strict:
                reasons.append(detail)
            else:
                advisory_notes.append(
                    detail + ":advisory_only_strict_false")

        # PnL visibility freeze --------------------------------------------------
        if pnl_seen:
            reasons.append(
                "pnl_visible_posture_change_forbidden:"
                "cache/concurrency posture may only be reduced after PnL seen")

        adopted = not reasons
        return {
            "schema_version": _DECISION_SCHEMA_VERSION,
            "artifact": "shared_cache_merge_gate_decision",
            "adopted": adopted,
            "advisory_only": bool(adopted and advisory_notes),
            "strict": bool(strict),
            "pnl_seen": bool(pnl_seen),
            "reasons": reasons,
            "advisory_notes": advisory_notes,
            "proofs": proofs,
            "metrics": {
                "wall_time_reduction": reduction,
                "wall_time_reduction_target": self.min_wall_time_reduction,
                "max_raw_reads_full_stress": self.max_raw_reads,
            },
            "generated_at_utc": _utcnow_iso(),
        }


def adopt_shared_cache(**kwargs: Any) -> dict[str, Any]:
    """Module-level convenience wrapper: evaluate via a default-gate
    instance with contractual thresholds; returns the decision object."""
    gate = SharedCacheMergeGate()
    return gate.evaluate(**kwargs)
