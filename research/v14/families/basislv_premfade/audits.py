"""Audit-only evidence builders for the frozen BASISLV-PREMFADE family.

SCOPE BOUNDARY: this module computes NO PnL, no returns and no scored
metric on real data.  Every real-data output is a field verification, a
count, a timestamp comparison, a schedule verdict, a turnover/holding
estimate or an sha256 equality.  Nothing here publishes.

Data authorities (READ-ONLY, never copied or committed):

* A9-F staged basis observables -- the 19 ranked names x 4 routes of
  ``research/control/v14_run/d2_a9f/staged_basis_manifest.json``
  (machine-local, gitignored bulk under the d2-a9f worktree / a mirrored
  root; resolved via the manifest's own ``file`` paths, the
  ``V14_D2A9F_STAGED_ROOT`` environment override, or an explicit
  ``staged_root`` argument).  EVERY file's SHA-256 is verified against the
  manifest at load; any mismatch FAILS CLOSED (never a warning).
* authorized staged 15m bars -- ``research.v12.data_contract.BARS_ROOT``
  (Nautilus layout; ``ts_event`` is the raw bar-close stamp in ns,
  forward-snapped to the 15m boundary it terminates; prices decode as raw
  i128 / 1e16, A9-F F7).
* perp instrument metadata tick sizes -- the P1 load path
  (``research.v12.families.oilev_v2.audits.load_tick_sizes`` semantics;
  real ticks, no uniform stubs -- L-V14-0).
* funding settlements -- ``research.v12.data_contract.FUNDING_BUNDLES``
  (settlement stamp availability; hour-snapped stamps).

The SIGNAL consumes the basis route ONLY; the premium/mark/index kline
routes are verification-only cross-check inputs (the proposal declares them
out of scope for the signal, proposal section 10) and are loaded here with
the A9-F malformed-row rules (premium-close 0.0 sentinel, nonpositive
price-level fields) purely to prove staging health and availability
discipline.

Evidence builders (each returns a JSON-safe payload):

* :func:`evidence_identity` -- frozen identity payloads + the recomputed
  vs recorded per-arm ``arm_config_digest`` report;
* :func:`evidence_staged_inputs` -- staged-basis verification: manifest
  SHA equality, per-file SHA-256 verification, zero-gap grid checks, the
  frozen basis-route identity check (p_b vs basisRate within the declared
  absolute tolerance, fail-closed per symbol) and verification-route health;
* :func:`build_schedule_records` / :func:`evidence_schedule_feasibility` --
  schedule-only feasibility on the REAL snapshot: decisions per fold,
  purged stamps, per-stamp eligibility/side-size/refusals, cap/gross
  invariants, one-way turnover estimates (NO PnL, no cost numbers);
* :func:`evidence_double_generation` -- the full effective-schedule target
  generation for all three arms computed twice; byte-identical canonical
  JSON (sha256 equality);
* :func:`evidence_drop_one` -- the pinned drop-one diagnostic on the real
  anchor schedule (held max-|weight| leg with the largest |b_i|, proven
  held; 2k-1-leg renormalization to gross 1.0).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import numpy as np
import pyarrow.parquet as pq

from research.adapter_v10.protocol import ContractViolation
from research.v12.data_contract import (
    BARS_ROOT,
    FUNDING_BUNDLES,
    REQUIRED_SYMBOLS,
    snap_funding_times_to_hour,
)
from research.v14.families.basislv_premfade.frozen_identity import (
    BASISLV_ARM_CONFIG_DIGESTS,
    frozen_arm_config,
    frozen_arm_digest_report,
    frozen_identity,
)
from research.v14.families.basislv_premfade.plugin import (
    BasislvPremfadePlugin,
    family_stress_cell,
)
from research.v14.families.basislv_premfade.strategy import (
    ANCHOR_ARM,
    ARM_IDS,
    BASIS_IDENTITY_TOL_ABS,
    BENCHMARK_SYMBOL,
    BUCKET_NS,
    CAP_MAX,
    DAY_NS,
    FIRST_STAMP_ISO,
    FOLD_WINDOWS,
    FOLDS_CONTRACT,
    GROSS_TARGET,
    HOLDING_DAYS,
    MIN_ELIGIBLE,
    PURGE_DAYS,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    BarSeries,
    BasisRouteSeries,
    bars_from_rows,
    basis_series_from_rows,
    build_drop_one_book,
    compute_targets_at,
    effective_schedule,
    fold_assignments,
    fold_end_ns,
    iso_utc,
    parse_iso_utc,
    schedule_drop_one,
    select_drop_one_symbol_at,
    signal_scores_at,
    stamp_calendar,
)

AUDITS_SCHEMA = "v14i.basislv_premfade.audits.v1"
PRODUCER_ROLE = "I-F1"

#: The A9-F staged manifest authority (recorded in the A9-F lane handoff and
#: its gate G2 artifact hash; verified at load, fail-closed on mismatch).
MANIFEST_RECORDED_SHA256 = (
    "3867bdca3162f219d9a62b30b6768997f89a751b7bb86231b1c1175a6e25ee88"
)
MANIFEST_RELATIVE_PATH = (
    "research/control/v14_run/d2_a9f/staged_basis_manifest.json"
)
STAGED_ROOT_ENV = "V14_D2A9F_STAGED_ROOT"

#: The 19 ranked names: staged REQUIRED_SYMBOLS minus the benchmark leg.
TRADEABLE_UNIVERSE: tuple[str, ...] = tuple(
    sorted(set(REQUIRED_SYMBOLS) - {BENCHMARK_SYMBOL})
)

#: Route file naming inside the staged root.
ROUTE_SUFFIX = {
    "basis": "_basis_15m.parquet",
    "premium_klines": "_premium_klines_15m.parquet",
    "mark_klines": "_mark_klines_15m.parquet",
    "index_klines": "_index_klines_15m.parquet",
}
#: Value column per route (A9-F staged schema).
ROUTE_VALUE_COLUMN = {
    "basis": ("futures_price", "index_price", "basis_rate"),
    "premium_klines": ("premium_close",),
    "mark_klines": ("mark_close",),
    "index_klines": ("index_close",),
}
#: A9-F malformed-value classes (DISC-1 / staging evidence):
#: 'zero'        -- premiumIndexKlines close emits exact 0.0 when the
#:                  premium index did not update at the bucket boundary
#:                  (a sentinel, never a real premium rate);
#: 'nonpositive' -- price-level fields must be > 0.
MALFORMED_RULE = {
    "premium_close": "zero",
    "mark_close": "nonpositive",
    "index_close": "nonpositive",
    "futures_price": "nonpositive",
    "index_price": "nonpositive",
}


# --------------------------------------------------------------------------- #
# Manifest resolution + SHA verification (fail closed)
# --------------------------------------------------------------------------- #
def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_manifest_path(repo_root: Optional[str | Path] = None) -> Path:
    """Locate ``staged_basis_manifest.json`` (worktree-relative first)."""
    candidates: list[Path] = []
    if repo_root is not None:
        candidates.append(Path(repo_root) / MANIFEST_RELATIVE_PATH)
    here = Path(__file__).resolve()
    for base in here.parents:
        candidates.append(base / MANIFEST_RELATIVE_PATH)
    candidates.append(
        Path("/Users/hoangminhlong/my-quantitative") / MANIFEST_RELATIVE_PATH
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"staged basis manifest not found; looked in {[str(c) for c in candidates]}"
    )


def staged_root_candidates(manifest: Mapping[str, Any]) -> list[Path]:
    """Candidate roots for the staged bulk (manifest paths first)."""
    roots: list[Path] = []
    env = os.environ.get(STAGED_ROOT_ENV)
    if env:
        roots.append(Path(env))
    entries = manifest.get("entries", {})
    for entry in entries.values():
        file_path = entry.get("file")
        if file_path:
            roots.append(Path(str(file_path)).parent)
            break
    here = Path(__file__).resolve()
    for base in here.parents:
        candidate = base / "research/control/v14_run/d2_a9f/staged"
        roots.append(candidate)
    roots.append(
        Path(
            "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v14/"
            "d2-a9f-feasibility/research/control/v14_run/d2_a9f/staged"
        )
    )
    seen: set[str] = set()
    unique: list[Path] = []
    for root in roots:
        text = str(root)
        if text not in seen:
            seen.add(text)
            unique.append(root)
    return unique


def resolve_staged_path(
    manifest: Mapping[str, Any], key: str, staged_root: Optional[str | Path] = None
) -> Path:
    """Resolve one staged file path (explicit root > env > manifest path)."""
    entry = manifest["entries"][key]
    name = Path(str(entry["file"])).name
    if staged_root is not None:
        return Path(staged_root) / name
    for root in staged_root_candidates(manifest):
        candidate = root / name
        if candidate.is_file():
            return candidate
    return Path(str(entry["file"]))


def load_staged_manifest(
    *,
    manifest_path: Optional[str | Path] = None,
    verify_manifest_sha: bool = True,
) -> dict[str, Any]:
    """Load the A9-F staged manifest; verify its own recorded SHA (fail-closed)."""
    path = Path(manifest_path) if manifest_path else resolve_manifest_path()
    with open(path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if verify_manifest_sha:
        observed = sha256_file(path)
        if observed != MANIFEST_RECORDED_SHA256:
            raise ContractViolation(
                "staged_basis_manifest.json SHA mismatch: observed "
                f"{observed} != recorded {MANIFEST_RECORDED_SHA256} "
                "(fail-closed; the staged authority is not the audited one)"
            )
    return manifest


def verify_staged_file(
    manifest: Mapping[str, Any],
    key: str,
    *,
    staged_root: Optional[str | Path] = None,
) -> dict[str, Any]:
    """Verify ONE staged file's SHA-256 against the manifest (fail-closed)."""
    entry = manifest["entries"][key]
    path = resolve_staged_path(manifest, key, staged_root=staged_root)
    if not path.is_file():
        raise FileNotFoundError(f"staged file missing for {key}: {path}")
    observed = sha256_file(path)
    if observed != str(entry["sha256"]):
        raise ContractViolation(
            f"staged file SHA mismatch for {key}: observed {observed} != "
            f"manifest {entry['sha256']} (fail-closed)"
        )
    return {
        "key": str(key),
        "path": str(path),
        "sha256": observed,
        "bytes": int(entry["bytes"]),
        "rows": int(entry["rows"]),
        "expected_buckets": int(entry["expected_buckets"]),
        "missing_buckets": int(entry.get("missing_buckets", -1)),
    }


# --------------------------------------------------------------------------- #
# Route loaders (availability-carrying; A9-F malformed-row rules)
# --------------------------------------------------------------------------- #
def _route_arrays(
    manifest: Mapping[str, Any],
    route: str,
    symbol: str,
    *,
    staged_root: Optional[str | Path] = None,
    verify_sha: bool = True,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """``(open_time_ms, {value_col: array})`` of one staged route file."""
    key = f"{route}|{symbol}"
    path = resolve_staged_path(manifest, key, staged_root=staged_root)
    if verify_sha:
        verify_staged_file(manifest, key, staged_root=staged_root)
    table = pq.read_table(path)
    opens = np.asarray(
        table.column("open_time_ms").to_pylist(), dtype=np.int64
    )
    values = {
        col: np.asarray(table.column(col).to_pylist(), dtype=np.float64)
        for col in ROUTE_VALUE_COLUMN[route]
    }
    return opens, values


def _malformed_mask(vals: np.ndarray, value_col: str) -> np.ndarray:
    rule = MALFORMED_RULE.get(value_col)
    if rule == "zero":
        return vals == 0.0
    if rule == "nonpositive":
        return vals <= 0.0
    return np.zeros(vals.shape, dtype=bool)


def load_premium_series(
    symbol: str,
    *,
    manifest: Optional[Mapping[str, Any]] = None,
    staged_root: Optional[str | Path] = None,
    verify_sha: bool = True,
) -> BasisRouteSeries:
    """The frozen basis-route premium series for one symbol (fail-closed).

    Rows are indexed by bucket close (``open_time_ms + 15m``); the per-bucket
    premium ``p_b = (futuresPrice - indexPrice)/indexPrice`` is computed from
    the archived fields; the staging identity check requires ``|p_b -
    basisRate| <= BASIS_IDENTITY_TOL_ABS`` at every admissible bucket
    (ABSOLUTE band per A9F-OBS-3; the endpoint rounds basisRate to 4 decimal
    places) -- ANY violation fails the symbol closed.  A malformed row
    (nonpositive index price, non-finite fields) marks the bucket NaN (a
    gap, never back-filled -- L-V12-5).
    """
    resolved = manifest if manifest is not None else load_staged_manifest()
    opens, values = _route_arrays(
        resolved, "basis", symbol, staged_root=staged_root, verify_sha=verify_sha
    )
    fut = values["futures_price"]
    idx = values["index_price"]
    basis_rate = values["basis_rate"]
    if not (fut.shape[0] == idx.shape[0] == basis_rate.shape[0] == opens.shape[0]):
        raise ContractViolation(f"{symbol}: basis route columns must share one length")
    with np.errstate(divide="ignore", invalid="ignore"):
        computed = (fut - idx) / idx
    admissible = (
        np.isfinite(computed)
        & np.isfinite(idx)
        & (idx > 0.0)
        & ~_malformed_mask(fut, "futures_price")
    )
    deviation = np.abs(computed[admissible] - basis_rate[admissible])
    max_deviation = float(deviation.max()) if deviation.size else 0.0
    if max_deviation > BASIS_IDENTITY_TOL_ABS:
        raise ContractViolation(
            f"{symbol}: basis-route identity check violated: max |p_b - "
            f"basisRate| = {max_deviation} > {BASIS_IDENTITY_TOL_ABS} "
            "(fail-closed staging flag)"
        )
    premium = np.where(admissible, computed, np.nan)
    # open_time_ms is epoch MILLISECONDS; the family grid is epoch NS and
    # slots are indexed by bucket CLOSE (availability = bucket close).
    opens_ns = (opens.astype(np.int64) * 1_000_000).astype(np.int64)
    closes_ns = opens_ns + BUCKET_NS
    rows = [
        (int(closes_ns[i]), int(closes_ns[i]), float(premium[i]))
        for i in range(opens_ns.shape[0])
    ]
    # Duplicate closes or off-grid opens must fail closed.
    if opens_ns.size and int(opens_ns[0]) % BUCKET_NS != 0:
        raise ContractViolation(f"{symbol}: basis bucket open off the 15m grid")
    series = basis_series_from_rows(rows)
    expected = (
        (int(opens_ns[-1]) - int(opens_ns[0])) // BUCKET_NS + 1 if opens_ns.size else 0
    )
    if series.premium.shape[0] != expected:
        raise ContractViolation(
            f"{symbol}: basis route grid gap at load ({series.premium.shape[0]} "
            f"slots vs {expected} expected; fail-closed)"
        )
    return series


def load_verification_route(
    symbol: str,
    route: str,
    *,
    manifest: Optional[Mapping[str, Any]] = None,
    staged_root: Optional[str | Path] = None,
    verify_sha: bool = True,
) -> dict[str, Any]:
    """Verification-only kline-route health for one symbol (no signal use).

    The premium/mark/index kline routes are DECLARED OUT OF SCOPE for the
    signal (proposal section 10); this loader proves staging health and
    availability discipline only: per-file SHA equality, the 15m grid with
    zero gaps, the A9-F malformed-row rules (premium-close 0.0 sentinel,
    nonpositive price levels) and availability = bucket close (a row is
    never treated as readable before its own close).  Returns counts only.
    """
    if route not in ("premium_klines", "mark_klines", "index_klines"):
        raise ContractViolation(f"route {route!r} is not a verification route")
    resolved = manifest if manifest is not None else load_staged_manifest()
    opens, values = _route_arrays(
        resolved, route, symbol, staged_root=staged_root, verify_sha=verify_sha
    )
    (col,) = list(values)
    arr = values[col]
    bad = _malformed_mask(arr, col) | ~np.isfinite(arr)
    closes_ns = (opens.astype(np.int64) * 1_000_000).astype(np.int64) + BUCKET_NS
    grid = int(opens[-1]) - int(opens[0])
    expected = grid // 900_000 + 1 if opens.size else 0
    return {
        "symbol": str(symbol),
        "route": str(route),
        "rows": int(opens.shape[0]),
        "expected_grid_slots": int(expected),
        "zero_grid_gap": bool(opens.shape[0] == expected),
        "malformed_or_nonfinite": int(bad.sum()),
        "malformed_share": float(bad.sum() / max(1, opens.shape[0])),
        "first_close_utc": iso_utc(int(closes_ns[0])) if opens.size else None,
        "availability_semantics": "bucket_close_time",
        "signal_use": "NONE (declared out of scope; verification-only)",
    }


# --------------------------------------------------------------------------- #
# Authorized bars / tick sizes / funding (read-only workspace snapshots)
# --------------------------------------------------------------------------- #
PRICE_DECODE_DIVISOR = 1e16


def decode_i128(raw: bytes) -> tuple[float, int]:
    """Decode one Nautilus i128 price/quantity column value: ``raw / 1e16``."""
    raw_int = int.from_bytes(bytes(raw), "little", signed=True)
    decoded = raw_int / PRICE_DECODE_DIVISOR
    if not math.isfinite(decoded) or decoded <= 0.0:
        raise ValueError(f"i128 decode produced a non-positive value: {decoded}")
    return decoded, raw_int


def _snap_close_to_boundary_vectorized(ts: "np.ndarray") -> "np.ndarray":
    """Forward-snap raw bar-close stamps to the 15m boundary they terminate."""
    remainder = ts % BUCKET_NS
    forward = (BUCKET_NS - remainder) % BUCKET_NS
    return np.where(forward < BUCKET_NS // 2, ts + forward, ts)


def load_execution_bars(
    symbols: Optional[Sequence[str]] = None,
    *,
    bars_root: str = BARS_ROOT,
    start_ns: Optional[int] = None,
    end_ns: Optional[int] = None,
) -> dict[str, BarSeries]:
    """Boundary-indexed execution bar series per symbol (read-only snapshot)."""
    wanted = [str(s) for s in (symbols or (TRADEABLE_UNIVERSE + (BENCHMARK_SYMBOL,)))]
    out: dict[str, BarSeries] = {}
    for sym in wanted:
        sym_dir = Path(bars_root) / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
        paths = sorted(sym_dir.glob("*.parquet"))
        if not paths:
            raise FileNotFoundError(f"no bar parquets for {sym} under {bars_root}")
        rows: list[tuple[int, int, float]] = []
        seen: set[int] = set()
        for path in paths:
            table = pq.read_table(path, columns=["ts_event", "close"])
            ts = np.asarray(table.column("ts_event").to_pylist(), dtype=np.int64)
            boundary = _snap_close_to_boundary_vectorized(ts)
            mask = np.ones(boundary.shape[0], dtype=bool)
            if start_ns is not None:
                mask &= boundary >= int(start_ns)
            if end_ns is not None:
                mask &= boundary <= int(end_ns)
            close_col = table.column("close").to_pylist()
            for idx in np.nonzero(mask)[0]:
                b = int(boundary[idx])
                if b in seen:
                    raise ContractViolation(
                        f"{sym}: two bar closes snap to boundary {b}"
                    )
                seen.add(b)
                close, _ci = decode_i128(close_col[idx])
                rows.append((b, b, close))
        rows.sort(key=lambda r: r[0])
        out[sym] = bars_from_rows(rows)
    return out


def load_tick_sizes(
    symbols: Optional[Sequence[str]] = None,
) -> dict[str, float]:
    """Real perp-metadata tick sizes (the P1 load path; no uniform stubs)."""
    from research.v12.families.oilev_v2.audits import load_tick_sizes as _load

    return _load(symbols or list(REQUIRED_SYMBOLS))


def load_settlements(
    symbol: str,
    *,
    bundles: Optional[Sequence[tuple[str, str]]] = None,
) -> tuple[dict[str, Any], ...]:
    """Native funding settlement rows for one symbol (first holding bundle).

    Availability = the settlement stamp (``fundingTime``, hour-snapped per
    the v12 contract); ``value`` = ``fundingRate``.  Funding is a
    cost/credit ONLY -- never a signal input (proposal section 4).
    """
    ordered = tuple(bundles) if bundles else FUNDING_BUNDLES
    for _label, root in ordered:
        path = Path(root) / str(symbol) / "funding.json"
        if not path.is_file():
            continue
        with open(path, "r", encoding="utf-8") as handle:
            body = json.load(handle)
        rows = body.get("rows", [])
        times = [int(row["fundingTime"]) * 1_000_000 for row in rows]
        snapped, _snap = snap_funding_times_to_hour(times)
        out = []
        for row, stamp in zip(rows, snapped):
            out.append(
                {
                    "publish_ts_ns": int(stamp),
                    "value": float(row["fundingRate"]),
                }
            )
        return tuple(out)
    raise FileNotFoundError(f"no funding bundle holds {symbol}")


# --------------------------------------------------------------------------- #
# Plugin assembly
# --------------------------------------------------------------------------- #
def load_basis_world(
    symbols: Optional[Sequence[str]] = None,
    *,
    manifest: Optional[Mapping[str, Any]] = None,
    staged_root: Optional[str | Path] = None,
    verify_sha: bool = True,
) -> dict[str, BasisRouteSeries]:
    """SHA-verified basis-route premium world for the ranked names."""
    wanted = [str(s) for s in (symbols or TRADEABLE_UNIVERSE)]
    resolved = manifest if manifest is not None else load_staged_manifest()
    return {
        sym: load_premium_series(
            sym, manifest=resolved, staged_root=staged_root, verify_sha=verify_sha
        )
        for sym in wanted
    }


def build_plugins(
    *,
    symbols: Optional[Sequence[str]] = None,
    basis_by_symbol: Optional[Mapping[str, BasisRouteSeries]] = None,
    bars_by_symbol: Optional[Mapping[str, BarSeries]] = None,
    settlements_by_symbol: Optional[Mapping[str, Sequence[Any]]] = None,
    tick_sizes: Optional[Mapping[str, float]] = None,
    manifest: Optional[Mapping[str, Any]] = None,
    staged_root: Optional[str | Path] = None,
) -> dict[str, BasislvPremfadePlugin]:
    """Build the three frozen arm plugins on the read-only snapshot."""
    universe = tuple(symbols) if symbols else TRADEABLE_UNIVERSE
    needed = sorted(set(universe) | {BENCHMARK_SYMBOL})
    if basis_by_symbol is None:
        basis_by_symbol = load_basis_world(
            universe, manifest=manifest, staged_root=staged_root
        )
    if bars_by_symbol is None:
        first_stamp = parse_iso_utc(FIRST_STAMP_ISO)
        bars_by_symbol = load_execution_bars(
            needed,
            start_ns=first_stamp - int(HOLDING_DAYS) * DAY_NS,
            end_ns=parse_iso_utc(WINDOW_END_ISO),
        )
    if tick_sizes is None:
        tick_sizes = load_tick_sizes(needed)
    plugins: dict[str, BasislvPremfadePlugin] = {}
    for arm_id in ARM_IDS:
        plugins[arm_id] = BasislvPremfadePlugin(
            arm_id=arm_id,
            basis_by_symbol={
                sym: s for sym, s in basis_by_symbol.items() if sym in set(universe)
            },
            bars_by_symbol=bars_by_symbol,
            settlements_by_symbol=settlements_by_symbol or {},
            tick_sizes=tick_sizes,
        )
    return plugins


# --------------------------------------------------------------------------- #
# Evidence builders
# --------------------------------------------------------------------------- #
def evidence_identity() -> dict[str, Any]:
    """Frozen identity payloads + honest recomputed-vs-recorded digest report."""
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        arms[arm_id] = {
            "public_payload": identity.public_payload(),
            "matrix_cohort_hint": identity.matrix_cohort_hint,
            "arm_id_declared": identity.arm_id,
            "recorded_config": frozen_arm_config(arm_id),
        }
    report = frozen_arm_digest_report()
    all_match = all(entry["match"] for entry in report.values())
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "identity",
        "producer_role": PRODUCER_ROLE,
        "digest_function": (
            "research.v11.publication_identity.arm_config_digest("
            "StrategyIdentity(...), arm_id=...)"
        ),
        "digest_provenance": (
            "the V14 selection freeze records no per-arm digests; this lane "
            "recorded the digests computed from the frozen identities at "
            "implementation time, BEFORE any scored metric exists for any "
            "V14 cell (V12/V13 pre-scored-metric convention)"
        ),
        "arms": arms,
        "digest_report": report,
        "recorded_digests": dict(BASISLV_ARM_CONFIG_DIGESTS),
        "all_match": bool(all_match),
    }


def evidence_staged_inputs(
    *,
    manifest: Optional[Mapping[str, Any]] = None,
    staged_root: Optional[str | Path] = None,
    verify_sha: bool = True,
) -> dict[str, Any]:
    """Staged-basis verification (SHA, grid, identity check; fail-closed)."""
    resolved = manifest if manifest is not None else load_staged_manifest()
    basis_files: dict[str, Any] = {}
    for sym in TRADEABLE_UNIVERSE:
        basis_files[sym] = verify_staged_file(
            resolved, f"basis|{sym}", staged_root=staged_root
        )
    # Grid + identity checks via the loader (raises on any violation).
    series = load_basis_world(
        manifest=resolved, staged_root=staged_root, verify_sha=False
    )
    identity_notes = {
        sym: {
            "slots": int(s.premium.shape[0]),
            "finite_slots": int(np.isfinite(s.premium).sum()),
            "origin_iso": iso_utc(int(s.origin_ns)),
        }
        for sym, s in sorted(series.items())
    }
    verification_routes = {
        sym: {
            route: load_verification_route(
                sym,
                route,
                manifest=resolved,
                staged_root=staged_root,
                verify_sha=verify_sha,
            )
            for route in ("premium_klines", "mark_klines", "index_klines")
        }
        for sym in TRADEABLE_UNIVERSE
    }
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "staged_inputs_verification",
        "producer_role": PRODUCER_ROLE,
        "manifest_recorded_sha256": MANIFEST_RECORDED_SHA256,
        "manifest_sha_verified": bool(verify_sha),
        "universe": list(TRADEABLE_UNIVERSE),
        "basis_files_verified": basis_files,
        "basis_grid_summary": identity_notes,
        "verification_routes": verification_routes,
        "verification_route_note": (
            "premium/mark/index klines are verification-only staging inputs; "
            "the signal consumes the basis route ONLY (proposal section 10)"
        ),
        "pnl_computed": False,
    }


def build_schedule_records(
    arm_id: str,
    *,
    basis_by_symbol: Mapping[str, BasisRouteSeries],
    universe: Sequence[str],
    instants: Sequence[int],
) -> list[dict[str, Any]]:
    """The effective (purged) target-book schedule of one arm (schedule-only)."""
    records: list[dict[str, Any]] = []
    for stamp in instants:
        scores, _refused = signal_scores_at(
            arm_id,
            basis_by_symbol=basis_by_symbol,
            stamp_ns=int(stamp),
            universe=universe,
        )
        book = compute_targets_at(
            arm_id,
            basis_by_symbol=basis_by_symbol,
            stamp_ns=int(stamp),
            universe=universe,
        )
        records.append(
            {
                "decision_ns": int(stamp),
                "arm_id": str(arm_id),
                "status": str(book["status"]),
                "weights": [[sym, float(w)] for sym, w in book["weights"]],
                "scores": {str(s): float(v) for s, v in sorted(scores.items())},
                "diagnostics": book["diagnostics"],
            }
        )
    return records


def evidence_schedule_feasibility(
    *,
    manifest: Optional[Mapping[str, Any]] = None,
    staged_root: Optional[str | Path] = None,
) -> dict[str, Any]:
    """Schedule-only feasibility on the REAL snapshot (no PnL, no costs)."""
    universe = TRADEABLE_UNIVERSE
    calendar = stamp_calendar()
    effective, purged_by_fold = effective_schedule(calendar)
    series = load_basis_world(
        manifest=manifest, staged_root=staged_root, verify_sha=True
    )
    assignments = fold_assignments(calendar)
    fold_counts = {label: len(members) for _i, label, members, _p in assignments}
    stamp_fold_label = {
        int(stamp): label
        for _i, label, members, _p in assignments
        for stamp in members
    }
    arms: dict[str, Any] = {}
    problems: list[str] = []
    for arm_id in ARM_IDS:
        records = build_schedule_records(
            arm_id, basis_by_symbol=series, universe=universe, instants=effective
        )
        eligible = [rec["diagnostics"]["n_eligible"] for rec in records]
        side_sizes = [rec["diagnostics"]["side_size"] for rec in records]
        refused_total = sum(int(rec["diagnostics"]["n_refused"]) for rec in records)
        max_abs = max(rec["diagnostics"]["max_abs_weight"] for rec in records)
        gross_max = max(rec["diagnostics"]["gross_after_scale"] for rec in records)
        # one-way turnover estimate (weights change per stamp; no PnL)
        turnover = 0.0
        previous: dict[str, float] = {}
        for rec in records:
            current = {str(s): float(w) for s, w in rec["weights"]}
            turnover += math.fsum(
                abs(current.get(s, 0.0) - previous.get(s, 0.0))
                for s in set(current) | set(previous)
            )
            previous = current
        per_fold: dict[str, int] = {label: 0 for label, _s, _e in FOLD_WINDOWS}
        for record in records:
            per_fold[stamp_fold_label[int(record["decision_ns"])]] += 1
        for label, count in per_fold.items():
            if count < 15:
                problems.append(
                    f"{arm_id}: fold {label} has {count} live stamps < 15"
                )
        if min(eligible) < MIN_ELIGIBLE:
            problems.append(
                f"{arm_id}: min eligible {min(eligible)} < {MIN_ELIGIBLE}"
            )
        if max_abs > CAP_MAX + 1e-12:
            problems.append(f"{arm_id}: max |w| {max_abs} > {CAP_MAX}")
        if abs(gross_max - GROSS_TARGET) > 1e-9:
            problems.append(f"{arm_id}: gross {gross_max} != {GROSS_TARGET}")
        arms[arm_id] = {
            "decisions_total": len(records),
            "decisions_per_fold": per_fold,
            "n_eligible_min": int(min(eligible)),
            "n_eligible_max": int(max(eligible)),
            "side_size_min": int(min(side_sizes)),
            "side_size_max": int(max(side_sizes)),
            "refused_symbol_stamps_total": int(refused_total),
            "max_abs_weight_observed": float(max_abs),
            "max_gross_observed": float(gross_max),
            "cap_max": float(CAP_MAX),
            "one_way_turnover_total": round(turnover, 12),
            "one_way_turnover_mean_per_step": round(
                turnover / max(1, len(records)), 12
            ),
        }
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "schedule_feasibility_real_snapshot",
        "producer_role": PRODUCER_ROLE,
        "authority_note": (
            "schedule-only: counts, weights invariants and turnover estimates "
            "only -- NO PnL, no returns, no cost numbers"
        ),
        "window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "folds_contract": FOLDS_CONTRACT,
        "n_schedule_stamps": len(calendar),
        "purged_stamps_by_fold": {
            label: [iso_utc(t) for t in stamps]
            for label, stamps in sorted(purged_by_fold.items())
        },
        "n_effective_stamps": len(effective),
        "fold_member_counts": fold_counts,
        "universe_size": len(universe),
        "min_eligible": int(MIN_ELIGIBLE),
        "purge_days": int(PURGE_DAYS),
        "arms": arms,
        "problems": problems,
        "all_arms_pass": bool(not problems),
        "schedule_only": True,
        "pnl_computed": False,
    }


def _canonical_sha256(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def evidence_double_generation(
    *,
    manifest: Optional[Mapping[str, Any]] = None,
    staged_root: Optional[str | Path] = None,
) -> dict[str, Any]:
    """Generate the full effective-schedule targets twice; byte-identical JSON."""
    universe = TRADEABLE_UNIVERSE
    calendar = stamp_calendar()
    effective, _purged = effective_schedule(calendar)
    series = load_basis_world(
        manifest=manifest, staged_root=staged_root, verify_sha=True
    )
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        first = build_schedule_records(
            arm_id, basis_by_symbol=series, universe=universe, instants=effective
        )
        second = build_schedule_records(
            arm_id, basis_by_symbol=series, universe=universe, instants=effective
        )
        sha_first = _canonical_sha256(first)
        sha_second = _canonical_sha256(second)
        arms[arm_id] = {
            "generation_1_sha256": sha_first,
            "generation_2_sha256": sha_second,
            "byte_identical": bool(sha_first == sha_second),
            "records": len(first),
        }
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "double_generation_determinism",
        "producer_role": PRODUCER_ROLE,
        "volatile_metadata_excluded_note": (
            "records carry no volatile metadata at all (no wall-clock or "
            "environment fields), so the whole canonical payload must match"
        ),
        "arms": arms,
        "all_byte_identical": all(a["byte_identical"] for a in arms.values()),
    }


def evidence_drop_one(
    *,
    manifest: Optional[Mapping[str, Any]] = None,
    staged_root: Optional[str | Path] = None,
) -> dict[str, Any]:
    """The pinned drop-one diagnostic on the real anchor schedule.

    Selection per :data:`DROP_ONE_PIN` (earliest largest-held-|weight|
    stamp; the held leg with the largest |b_i| at that stamp, ties by
    symbol id ascending, proven held); the surviving ``2k-1`` legs are
    renormalized to gross 1.0 at ``1/(2k-1)`` each.
    """
    universe = TRADEABLE_UNIVERSE
    calendar = stamp_calendar()
    effective, _purged = effective_schedule(calendar)
    series = load_basis_world(
        manifest=manifest, staged_root=staged_root, verify_sha=True
    )
    records = build_schedule_records(
        ANCHOR_ARM, basis_by_symbol=series, universe=universe, instants=effective
    )
    selection = schedule_drop_one(records)
    at_stamp = next(
        r for r in records if int(r["decision_ns"]) == int(selection["stamp_ns"])
    )
    weights = {str(sym): float(w) for sym, w in at_stamp["weights"]}
    scores = {str(sym): float(v) for sym, v in at_stamp["scores"].items()}
    dropped_symbol = select_drop_one_symbol_at(weights, scores)
    dropped_book = build_drop_one_book(weights, dropped_symbol=dropped_symbol)
    side_weights = [abs(w) for _s, w in dropped_book["weights"]]
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "drop_one_diagnostic",
        "producer_role": PRODUCER_ROLE,
        "rule": selection["pin"],
        "selection": selection,
        "dropped_symbol": dropped_symbol,
        "dropped_symbol_abs_b_i": abs(scores[dropped_symbol]),
        "renormalized_book": {
            "dropped_side": dropped_book["dropped_side"],
            "longs": dropped_book["longs"],
            "shorts": dropped_book["shorts"],
            "n_surviving_legs": dropped_book["n_surviving_legs"],
            "per_leg_weight": dropped_book["per_leg_weight"],
            "gross": dropped_book["gross"],
        },
        "renormalization_ok": bool(
            abs(dropped_book["gross"] - 1.0) <= 1e-9
            and max(side_weights) <= CAP_MAX + 1e-12
        ),
        "non_vacuous": bool(
            selection["proven_held"] and abs(weights[dropped_symbol]) > 1e-9
        ),
    }


def build_all_evidence(out_dir: str | Path) -> dict[str, str]:
    """Run every real-data evidence builder and write JSON artifacts."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    builders = {
        "identity_digest_report.json": evidence_identity,
        "staged_inputs_verification.json": evidence_staged_inputs,
        "schedule_feasibility.json": evidence_schedule_feasibility,
        "double_generation_determinism.json": evidence_double_generation,
        "drop_one_diagnostic.json": evidence_drop_one,
    }
    written: dict[str, str] = {}
    for name, builder in builders.items():
        payload = builder()
        target = out / name
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1, sort_keys=True, default=str)
            handle.write("\n")
        written[name] = str(target)
    return written


__all__ = [
    "AUDITS_SCHEMA",
    "BASIS_IDENTITY_TOL_ABS",
    "MANIFEST_RECORDED_SHA256",
    "PRICE_DECODE_DIVISOR",
    "PRODUCER_ROLE",
    "STAGED_ROOT_ENV",
    "TRADEABLE_UNIVERSE",
    "BarSeries",
    "BasisRouteSeries",
    "build_all_evidence",
    "build_plugins",
    "build_schedule_records",
    "decode_i128",
    "evidence_double_generation",
    "evidence_drop_one",
    "evidence_identity",
    "evidence_schedule_feasibility",
    "evidence_staged_inputs",
    "load_basis_world",
    "load_execution_bars",
    "load_premium_series",
    "load_settlements",
    "load_staged_manifest",
    "load_tick_sizes",
    "load_verification_route",
    "resolve_manifest_path",
    "resolve_staged_path",
    "sha256_file",
    "verify_staged_file",
]
