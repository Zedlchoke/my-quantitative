"""V14 Phase E scored-cell driver (A1, one arm per invocation; owner-gated).

Frozen ``run_v13_cell.py`` pattern, wired to the TWO frozen V14 families
``research.v14.families.{basislv_premfade,oicyc}`` -- no V13 family logic is
imported and no frozen identity, cost, fold, gate or universe constant is
re-declared here.  Everything family-specific comes from the frozen family
packages (whose interfaces are the binding statements in
``research/control/v14_run/i_family_1/lane_handoff.json`` and
``research/control/v14_run/i_family_2/lane_handoff.json``); everything
adapter-specific comes from the frozen generic adapter; publication goes
through the frozen V12 accounting entry point
(``research.v12.accounting.publish_v12_cell`` with the A1 serialization
lock) into a PER-FAMILY shard ledger, exactly as in V13.

The six frozen arms (``research/control/v14_run/selection_freeze_v14.json``):

  basislv_premfade : BASISLV-PREMFADE-28D (anchor)
                     BASISLV-PREMFADE-56D (neighbour)
                     BASISLV-PREMFADE-28D-INV (causal control)
  oicyc            : CYC-28D (anchor) -- CONFIRMATORY per plan Section 1.1
                     CYC-14D (neighbour) -- CONFIRMATORY
                     CTL-OISHARE (causal control) -- CONFIRMATORY, never
                     promotable

V14 driver obligations carried ON TOP of the proven V13 pattern:

  * data roots are SPLIT: the staged bars/funding/mark/ticks root
    (``--staged-root``; 90-file staged-equivalent tree verified per-file
    against the committed ``research/audits/v12p/a3_staging_manifest.json``
    authority -- the P1 ``recompute_*.py`` assembly precedent) PLUS the
    A9-F staged basis root (``--basis-staged-root``; default the
    integration-worktree staged dir; manifest
    ``research/control/v14_run/d2_a9f/staged_basis_manifest.json`` SHA
    fail-closed at load and per-file SHA fail-closed at read) PLUS the
    archived staged OI root (``--oi-root``; default the frozen
    ``OI_CONSOLIDATED_ROOT``; manifest
    ``research/control/v11_run/oi_staging_manifest.json``; OI enters ONLY
    through ``oicyc.audits.load_oi_by_symbol_verified`` -- SHA fail-closed);
  * preflight computes ALL SIX arm-config digests from the frozen identity
    modules, asserts RECOMPUTED == RECORDED for every arm AND driver-level
    PAIRWISE UNIQUENESS across all six arms -- fail-closed before any data
    is loaded;
  * the frozen runner-compatibility pin (V13) runs before any scored
    metric: every accepted matrix cell's ``targets_at`` is probed at every
    non-final schedule instant; any refusal fails the run closed;
  * scored records carry the remediated cost kernel marker
    (``remediated_kernel`` = true, L-V14-0) and the cost broken out by
    FILLS vs HOLDING terms: the adapter charges per fill (weight-delta
    transitions only), so ``cost_holding_terms`` must be EXACTLY 0 by
    construction and the driver asserts it;
  * basislv scored cells carry the price-only vs total expectancy split,
    and at gate time the driver computes and passes
    ``price_only_expectancy`` AND ``total_expectancy`` into
    ``gate_runner.evaluate_family_gate`` -- the price-only failure clause
    is a REQUIRED gate input (missing inputs => BLOCKED, never an inferred
    PASS).  The gate runs on the ANCHOR invocation once both sibling arms'
    cell evidence exists in the family out tree; missing sibling evidence
    => BLOCKED (recorded, never inferred);
  * oicyc scored cells carry the CONFIRMATORY status metadata block
    (``plugin.status_metadata()``) and the denominator note -- the block is
    embedded in the scored metrics (hence inside the ledger row) and in the
    cell summary;
  * ``--dry-run``: the FULL path (staged verification, plugin construction,
    preflight, digests, traversal pin, adapter run) on a SYNTHETIC staged
    root -- per-file SHA self-consistency still fail-closed -- but
    publication is REFUSED and a scored ledger can never be written
    (``--publish``/``--ledger`` fail closed with ``--dry-run``, and an
    explicit ``--out-root`` is REQUIRED so no repo results tree is touched);
  * TECHABORT discipline (V12R/V13R precedent): any crash BEFORE the
    exactly-once ledger decision writes the forensic file
    ``TECHABORT_<arm>.json`` recording the phase, the crash evidence, honest
    ledger state and the ZERO budget effect, then exits 1.  The sink is
    REAL-scoring-time only: real runs default to the designated exec root's
    control tree (``<exec-root>/research/control/v14_run``; override with
    ``--techabort-dir``), while ``--dry-run`` runs default to
    ``<out-root>/TECHABORT`` inside the mandatory scratch tree and REFUSE
    any sink under a ``research/control`` subtree -- a test or dry-run can
    never again drop forensics into the control tree (the cancelled lane's
    six stray ``TECHABORT_*.json`` files were exactly that bug; fixed here
    and asserted by tests/test_v14_driver.py).
    Fixes are driver-only; frozen bytes are never edited.

No network access, no tuning, no grids, no threshold changes; artifacts are
written only under the ``--out-root`` namespace (default
``<exec-root>/results/v14_phase_e/<family>/<arm>``).  Exit codes: 0
ok/published/idempotent-replay, 1 crash (TECHABORT written), 2 fail-closed
preflight (no metric computed), 4 honest refusal recorded (observation row;
the cell consumed its budget).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

DRIVER_REPO_ROOT = Path(__file__).resolve().parents[4]

#: The committed per-file sha256 authority for the staged-equivalent
#: bars/funding/mark/ticks tree (the P1 ``recompute_*.py`` assembly).
A3_STAGING_MANIFEST_RELPATH = (
    "research",
    "audits",
    "v12p",
    "a3_staging_manifest.json",
)
STAGED_FILES_EXPECTED = 90
#: The staged-tree manifest file name (V13 layout; synthetic roots carry a
#: self-describing manifest under the same name).
STAGED_MANIFEST_NAME = "staged_manifest_.json"

#: The A9-F staged basis manifest authority (relative to the exec root) and
#: its recorded SHA (verified fail-closed at load by the frozen family
#: loader; re-verified here before any plugin construction).
BASIS_MANIFEST_RELPATH = (
    "research",
    "control",
    "v14_run",
    "d2_a9f",
    "staged_basis_manifest.json",
)
BASIS_MANIFEST_RECORDED_SHA256 = (
    "3867bdca3162f219d9a62b30b6768997f89a751b7bb86231b1c1175a6e25ee88"
)
#: Default staged basis bulk root candidates (machine-local, first existing
#: wins): the integration worktree's staged dir, then the originating d2-a9f
#: lane bulk.  If neither exists the frozen loader falls back to the manifest
#: entry paths (same bulk; explicit ``--basis-staged-root`` is the supported
#: wiring and the handoff invocation lines pass it explicitly).
_BASIS_STAGED_ROOT_CANDIDATES = (
    Path(
        "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v14/"
        "integration/research/control/v14_run/d2_a9f/staged"
    ),
    Path(
        "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v14/"
        "d2-a9f-feasibility/research/control/v14_run/d2_a9f/staged"
    ),
)


def _default_basis_staged_root() -> Optional[Path]:
    for candidate in _BASIS_STAGED_ROOT_CANDIDATES:
        if candidate.is_dir():
            return candidate
    return None

#: staged_data label -> subtree of the staged-equivalent root.
STAGED_BARS = "binance_bar_15m"
STAGED_PERP_META = "crypto_perpetual_meta"
STAGED_FUNDING_SCAN = "funding_scan_2026"
STAGED_FUNDING_LONG = "funding_20240820_20260821"
STAGED_OI = "oi_consolidated"
STAGED_LABELS = (
    STAGED_BARS,
    STAGED_PERP_META,
    STAGED_FUNDING_SCAN,
    STAGED_FUNDING_LONG,
    STAGED_OI,
)

#: OI staging authority (frozen; the archived machine-local v11 staging).
OI_MANIFEST_RELPATH = ("research", "control", "v11_run", "oi_staging_manifest.json")

#: TECHABORT default sink for REAL scored runs: the designated exec root's
#: control tree (the V13R ``TECHABORT_liqepis_chain_attempt1`` precedent --
#: an A1-produced forensic artifact under ``research/control``).  In
#: ``--dry-run``/synthetic mode the sink defaults to ``<out-root>/TECHABORT``
#: inside the mandatory scratch tree, and the driver REFUSES any synthetic
#: TECHABORT write whose sink lies under a ``research/control`` subtree:
#: forensic files are written at REAL scoring time only, never as a test
#: side effect (the cancelled lane's six stray ``TECHABORT_*.json`` files in
#: the control tree were exactly that bug).
TECHABORT_REAL_DIR_RELPATH = ("research", "control", "v14_run")

EXIT_OK = 0
EXIT_CRASH = 1
EXIT_FAIL_CLOSED = 2
EXIT_REFUSED = 4

FAMILIES = ("basislv_premfade", "oicyc")


# --------------------------------------------------------------------------- #
# Small shared helpers (I/O plumbing only; no family semantics)
# --------------------------------------------------------------------------- #
def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _finite(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), indent=1, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def git_head(repo_root: Path) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def techabort_sink_under_control_tree(techabort_dir: Path) -> bool:
    """True iff the sink lies under a ``research/control`` subtree.

    Synthetic runs must NEVER sink TECHABORT forensics into a control tree
    (real scoring time only); used as a fail-closed startup guard.
    """
    parts = [p.lower() for p in Path(techabort_dir).parts]
    return any(
        parts[i] == "research" and parts[i + 1] == "control"
        for i in range(len(parts) - 1)
    )


def validate_args(args: argparse.Namespace) -> Optional[str]:
    """Pure flag-combination validation (reason string, or None when OK)."""
    if args.family not in FAMILIES:
        return f"unknown family {args.family!r}; frozen families are {FAMILIES}"
    if args.dry_run and args.publish:
        return "--dry-run must never publish; --publish is forbidden with --dry-run"
    if args.dry_run and args.ledger:
        return "--dry-run must never touch a scored ledger; --ledger is forbidden"
    if args.dry_run and not args.out_root:
        return (
            "--dry-run requires an explicit --out-root (a scratch tree; the "
            "driver refuses to write anywhere under the repo results namespace)"
        )
    if args.publish and not args.ledger:
        return "--publish requires --ledger (per-family shard ledger)"
    if args.publish and not args.expect_head:
        return (
            "--publish requires --expect-head (the operator must state the "
            "frozen pin; fail-closed)"
        )
    return None


# --------------------------------------------------------------------------- #
# Staged-root verification (bars/funding/mark/ticks transport integrity)
# --------------------------------------------------------------------------- #
def verify_staged_root(
    staged_root: Path,
    *,
    synthetic: bool,
    authority_files: Optional[Mapping[str, Mapping[str, Any]]],
    authority_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Fail-closed staged-tree identity check BEFORE any data is loaded.

    Real mode: every one of the 90 authority files must be present with the
    committed a3 staging-manifest sha256, and the tree must carry every
    staged label subtree (the P1 ``verify_inputs`` pattern).
    Synthetic mode (``--dry-run``): the tree carries its own
    ``staged_manifest_.json``; every listed file must be present with the
    manifest sha256 (self-consistency, still fail-closed) and every staged
    label subtree must exist.
    """
    problems: list[str] = []
    files_verified = 0
    files_expected = 0
    manifest_sha: Optional[str] = None
    authority_sha: Optional[str] = None
    if synthetic:
        manifest_path = staged_root / STAGED_MANIFEST_NAME
        if not manifest_path.is_file():
            problems.append(f"synthetic staged manifest missing: {manifest_path}")
        else:
            manifest_sha = sha256_file(manifest_path)
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                files = dict(manifest.get("files", {}))
                files_expected = len(files)
                for rel, meta in sorted(files.items()):
                    data_path = staged_root / str(rel)
                    if not data_path.is_file():
                        problems.append(f"staged file missing: {rel}")
                        continue
                    actual = sha256_file(data_path)
                    if actual != str(meta.get("sha256", "")):
                        problems.append(f"staged file sha256 mismatch: {rel}")
                        continue
                    files_verified += 1
            except ValueError as exc:
                problems.append(f"synthetic staged manifest unreadable: {exc}")
    else:
        if authority_files is None:
            problems.append("a3 staging authority unavailable")
        else:
            if authority_path is not None and Path(authority_path).is_file():
                authority_sha = sha256_file(Path(authority_path))
            files_expected = len(dict(authority_files))
            if files_expected != STAGED_FILES_EXPECTED:
                problems.append(
                    f"a3 authority files {files_expected} != {STAGED_FILES_EXPECTED}"
                )
            for rel, expected in sorted(dict(authority_files).items()):
                data_path = staged_root / rel
                if not data_path.is_file():
                    problems.append(f"staged file missing: {rel}")
                    continue
                actual = sha256_file(data_path)
                if actual != str(expected.get("sha256", "")):
                    problems.append(f"staged file sha256 mismatch: {rel}")
                    continue
                files_verified += 1
            if files_verified != files_expected and not any(
                p.startswith("a3 authority") for p in problems
            ):
                problems.append(
                    f"staged files verified {files_verified} != {files_expected}"
                )
    for label in STAGED_LABELS:
        if not (staged_root / label).is_dir():
            problems.append(f"staged subtree missing: {staged_root / label}")
    return {
        "staged_root": str(staged_root),
        "mode": "synthetic" if synthetic else "real",
        "files_expected": files_expected,
        "files_verified": files_verified,
        "staged_manifest_sha256": manifest_sha,
        "authority_sha256": authority_sha,
        "problems": problems,
        "ok": not problems,
    }


# --------------------------------------------------------------------------- #
# Funding row mirror (byte-semantics of the frozen
# research.v13.families.oitd.audits.load_marks_and_settlements row mapping,
# carried with an explicit root -- the V13 ``load_marks_and_settlements_root``
# precedent).  Used ONLY where the frozen loader cannot be root-wired
# (oicyc synthetic dry-run); the real oicyc path goes through
# ``oicyc.audits.load_snapshot_data`` (the frozen wiring) unchanged.
# --------------------------------------------------------------------------- #
def load_settlements_root(
    root: Path, symbols: Sequence[str]
) -> dict[str, tuple[dict[str, Any], ...]]:
    """Native funding settlement rows (COST ONLY) from one bundle root."""
    wanted = [str(s) for s in symbols]
    settlements: dict[str, tuple[dict[str, Any], ...]] = {}
    for sym in wanted:
        path = Path(root) / sym / "funding.json"
        if not path.exists():
            settlements[sym] = ()
            continue
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        settle_rows: list[dict[str, Any]] = []
        for row in payload.get("rows") or []:
            ts_ms = row.get("fundingTime")
            rate = row.get("fundingRate")
            if ts_ms is None or rate is None:
                raise ValueError(f"{sym}: funding row missing fundingTime/rate")
            settle_rows.append(
                {"publish_ts_ns": int(ts_ms) * 1_000_000, "value": float(rate)}
            )
        settle_rows.sort(key=lambda r: r["publish_ts_ns"])
        if len({r["publish_ts_ns"] for r in settle_rows}) != len(settle_rows):
            raise ValueError(f"{sym}: duplicate settlement stamps")
        settlements[sym] = tuple(settle_rows)
    return settlements


# --------------------------------------------------------------------------- #
# Series digests (preflight pin inputs)
# --------------------------------------------------------------------------- #
def _rows_digest(rows_by_symbol: Mapping[str, Sequence[Any]]) -> str:
    """Digest of Mapping-row series (settlements)."""
    digest = hashlib.sha256()
    for sym in sorted(rows_by_symbol):
        for row in rows_by_symbol[sym]:
            fields = [str(k) for k in sorted(row)]
            digest.update(
                (f"{sym}|" + "|".join(f"{k}={row[k]!r}" for k in fields)).encode()
            )
    return digest.hexdigest()


def _pairs_digest(series_by_symbol: Mapping[str, Sequence[tuple[int, Any]]]) -> str:
    """Digest of ``(stamp_ns, value)`` pair series (OI)."""
    digest = hashlib.sha256()
    for sym in sorted(series_by_symbol):
        for stamp, value in series_by_symbol[sym]:
            digest.update(f"{sym}|{int(stamp)}|{float(value)!r}".encode())
    return digest.hexdigest()


def _bars_series_digest(series_by_symbol: Mapping[str, Any]) -> str:
    """Digest of boundary-indexed bar series (``origin_ns/close/available_ns``)."""
    digest = hashlib.sha256()
    for sym in sorted(series_by_symbol):
        series = series_by_symbol[sym]
        digest.update(
            f"{sym}|origin={int(series.origin_ns)}|".encode()
            + series.close.tobytes()
            + series.available_ns.tobytes()
        )
    return digest.hexdigest()


def _basis_series_digest(series_by_symbol: Mapping[str, Any]) -> str:
    """Digest of basis-route premium series (``origin_ns/premium/available_ns``)."""
    digest = hashlib.sha256()
    for sym in sorted(series_by_symbol):
        series = series_by_symbol[sym]
        digest.update(
            f"{sym}|origin={int(series.origin_ns)}|".encode()
            + series.premium.tobytes()
            + series.available_ns.tobytes()
        )
    return digest.hexdigest()


def _bars_tuple_digest(bars_by_symbol: Mapping[str, Sequence[Any]]) -> str:
    """Digest of Bar-tuple bundles (oitd loader output)."""
    digest = hashlib.sha256()
    for sym in sorted(bars_by_symbol):
        for bar in bars_by_symbol[sym]:
            digest.update(
                f"{sym}|{getattr(bar, 'ts_event_ns', None)!r}|"
                f"{getattr(bar, 'open', None)!r}|{getattr(bar, 'high', None)!r}|"
                f"{getattr(bar, 'low', None)!r}|{getattr(bar, 'close', None)!r}".encode()
            )
    return digest.hexdigest()


# --------------------------------------------------------------------------- #
# Frozen family registry: construction ONLY from the frozen V14 modules.
# --------------------------------------------------------------------------- #
def _data_roots(staged_root: Path) -> dict[str, Path]:
    return {
        "bars": staged_root / STAGED_BARS,
        "perp_meta": staged_root / STAGED_PERP_META,
        "funding_scan_2026": staged_root / STAGED_FUNDING_SCAN,
        "funding_20240820_20260821": staged_root / STAGED_FUNDING_LONG,
        "oi": staged_root / STAGED_OI,
    }


def build_basislv(
    staged_root: Path,
    arm_id: str,
    exec_root: Optional[Path] = None,
    *,
    synthetic: bool = False,
    basis_staged_root: Optional[Path] = None,
    basis_manifest_path: Optional[Path] = None,
) -> tuple[Any, dict[str, Any]]:
    """Frozen BASISLV-PREMFADE arm plugin (i-family-1 handoff interface).

    ``BasislvPremfadePlugin(arm_id, basis_by_symbol=..., bars_by_symbol=...,
    settlements_by_symbol=..., tick_sizes=...)`` with every bundle loaded
    through the frozen family loaders: the basis world through
    ``audits.load_basis_world`` (per-file SHA fail-closed against the A9-F
    manifest), execution bars through ``audits.load_execution_bars``,
    settlements through ``audits.load_settlements`` (the scan_2026 bundle of
    the staged tree), ticks through the canonical V12
    ``load_tick_sizes`` loader root-wired to the staged perp metadata
    (L-V14-0: real per-instrument tick sizes, no uniform stubs).
    """
    from research.v12.families.oilev_v2.audits import load_tick_sizes as _v12_ticks
    from research.v14.families.basislv_premfade.audits import (
        TRADEABLE_UNIVERSE,
        load_basis_world,
        load_execution_bars,
        load_settlements,
        load_staged_manifest,
    )
    from research.v14.families.basislv_premfade.plugin import BasislvPremfadePlugin
    from research.v14.families.basislv_premfade.strategy import (
        ARM_IDS as BASISLV_ARMS,
        BENCHMARK_SYMBOL,
        DAY_NS,
        FIRST_STAMP_ISO,
        HOLDING_DAYS,
        WINDOW_END_ISO,
        parse_iso_utc,
    )

    if arm_id not in BASISLV_ARMS:
        raise ValueError(f"arm {arm_id!r} is not a frozen basislv_premfade arm")
    roots = _data_roots(staged_root)
    universe = tuple(TRADEABLE_UNIVERSE)
    feed_symbols = tuple(sorted(set(universe) | {BENCHMARK_SYMBOL}))

    manifest = load_staged_manifest(
        manifest_path=basis_manifest_path, verify_manifest_sha=not synthetic
    )
    if not synthetic:
        import hashlib as _hashlib

        manifest_bytes = Path(basis_manifest_path).read_bytes()
        observed = _hashlib.sha256(manifest_bytes).hexdigest()
        if observed != BASIS_MANIFEST_RECORDED_SHA256:
            raise RuntimeError(
                "staged basis manifest SHA mismatch: observed "
                f"{observed} != recorded {BASIS_MANIFEST_RECORDED_SHA256}"
            )
    basis = load_basis_world(
        universe,
        manifest=manifest,
        staged_root=basis_staged_root,
        verify_sha=True,
    )
    first_stamp = parse_iso_utc(FIRST_STAMP_ISO)
    bars = load_execution_bars(
        feed_symbols,
        bars_root=str(roots["bars"]),
        start_ns=first_stamp - int(HOLDING_DAYS) * DAY_NS,
        end_ns=parse_iso_utc(WINDOW_END_ISO),
    )
    tick_sizes = _v12_ticks(feed_symbols, perp_root=str(roots["perp_meta"]))
    settlements = {
        sym: load_settlements(
            sym, bundles=((STAGED_FUNDING_SCAN, str(roots["funding_scan_2026"])),)
        )
        for sym in sorted(universe)
    }

    plugin = BasislvPremfadePlugin(
        arm_id=arm_id,
        basis_by_symbol=basis,
        bars_by_symbol=bars,
        settlements_by_symbol=settlements,
        tick_sizes=tick_sizes,
    )
    inputs = {
        "universe": list(universe),
        "benchmark_symbol": BENCHMARK_SYMBOL,
        "basis_digest": _basis_series_digest(basis),
        "bars_digest": _bars_series_digest(bars),
        "settlements_digest": _rows_digest(settlements),
        "tick_sizes": dict(sorted(tick_sizes.items())),
        "basis_buckets_per_symbol": {
            sym: int(series.premium.shape[0]) for sym, series in sorted(basis.items())
        },
        "bars_slots_per_symbol": {
            sym: int(s.close.shape[0]) for sym, s in sorted(bars.items())
        },
        "settlements_per_symbol": {
            s: len(v) for s, v in sorted(settlements.items())
        },
        "schedule_instants": len(plugin.schedule().instants),
        "basis_staged_root": str(basis_staged_root),
        "basis_manifest": str(basis_manifest_path),
        "basis_manifest_sha256": (
            sha256_file(Path(basis_manifest_path))
            if basis_manifest_path and Path(basis_manifest_path).is_file()
            else "unrecorded"
        ),
        "bundles_read": [
            "A9-F staged basis route (SHA-verified)",
            "binance_bar_15m (execution bars)",
            "crypto_perpetual_meta (real tick sizes; L-V14-0)",
            "funding_scan_2026 (settlements, COST ONLY)",
        ],
    }
    return plugin, inputs


def build_oicyc(
    staged_root: Path,
    arm_id: str,
    exec_root: Optional[Path] = None,
    *,
    synthetic: bool = False,
    oi_root: Optional[str] = None,
    oi_manifest_path: Optional[Path] = None,
) -> tuple[Any, dict[str, Any]]:
    """Frozen OICYC arm plugin (i-family-2 handoff interface).

    ``OicycPlugin(arm_id, oi_by_symbol=..., bars_by_symbol=...,
    settlements_by_symbol=..., tick_sizes=...)``.  OI enters ONLY through
    ``oicyc.audits.load_oi_by_symbol_verified`` (SHA-256 fail-closed against
    the v11 staging manifest).  Real mode wires the whole snapshot through
    the frozen ``oicyc.audits.load_snapshot_data`` (bars/marks/settlements/
    ticks via the frozen V13/V12 loaders, exactly the i-family-2
    ``driver_wiring`` statement).  Synthetic mode uses the SAME frozen
    loaders with explicit roots, except settlements, which come through the
    explicit-root funding row mirror above (the V13 byte-semantics
    precedent; no real workspace data is ever read in synthetic mode).
    """
    from research.v12.families.oilev_v2.audits import load_tick_sizes as _v12_ticks
    from research.v14.families.oicyc.audits import (
        load_oi_by_symbol_verified,
        load_snapshot_data,
        tradeable_universe_symbols,
    )
    from research.v14.families.oicyc.plugin import OicycPlugin
    from research.v14.families.oicyc.strategy import (
        ARM_IDS as OICYC_ARMS,
        BENCHMARK_SYMBOL,
        fold_end_instants,
        stamp_calendar,
    )

    if arm_id not in OICYC_ARMS:
        raise ValueError(f"arm {arm_id!r} is not a frozen oicyc arm")
    roots = _data_roots(staged_root)
    universe = tradeable_universe_symbols()
    feed_symbols = tuple(sorted(set(universe) | {BENCHMARK_SYMBOL}))

    if synthetic:
        instants = list(stamp_calendar())
        fold_ends = fold_end_instants()
        from research.v13.families.oitd.audits import load_bars_for_plugin

        oi = load_oi_by_symbol_verified(
            universe, root=str(oi_root), manifest_path=str(oi_manifest_path)
        )
        bars = load_bars_for_plugin(
            feed_symbols, instants + list(fold_ends), bars_root=str(roots["bars"])
        )
        settlements = load_settlements_root(roots["funding_scan_2026"], universe)
        ticks = _v12_ticks(feed_symbols, perp_root=str(roots["perp_meta"]))
        marks: dict[str, tuple[tuple[int, float], ...]] = {}
    else:
        data = load_snapshot_data(
            oi_root=str(oi_root),
            bars_root=str(roots["bars"]),
            oi_manifest_path=str(oi_manifest_path),
        )
        oi = data["oi"]
        bars = data["bars"]
        marks = data["marks"]
        settlements = data["settlements"]
        ticks = data["tick_sizes"]

    plugin = OicycPlugin(
        arm_id=arm_id,
        oi_by_symbol=oi,
        bars_by_symbol=bars,
        settlements_by_symbol=settlements,
        tick_sizes=ticks,
    )
    inputs = {
        "universe": list(universe),
        "benchmark_symbol": BENCHMARK_SYMBOL,
        "oi_digest": _pairs_digest(oi),
        "bars_digest": _bars_tuple_digest(bars),
        "settlements_digest": _rows_digest(settlements),
        "tick_sizes": {str(k): float(v) for k, v in sorted(dict(ticks).items())},
        "oi_rows_per_symbol": {s: len(v) for s, v in sorted(oi.items())},
        "bars_per_symbol": {s: len(b) for s, b in sorted(bars.items())},
        "settlements_per_symbol": {
            s: len(v) for s, v in sorted(settlements.items())
        },
        "schedule_instants": len(plugin.schedule().instants),
        "oi_root": str(oi_root),
        "oi_manifest": str(oi_manifest_path),
        "oi_load_path": (
            "oicyc.audits.load_oi_by_symbol_verified (SHA fail-closed)"
        ),
        "synthetic_settlements_mirror": bool(synthetic),
        "bundles_read": [
            "archived staged OI v11_oi_staging_v1 (SHA-verified)",
            "binance_bar_15m (execution/valuation bars)",
            "crypto_perpetual_meta (real tick sizes; L-V14-0)",
            "funding settlements (COST ONLY)",
        ],
    }
    if not synthetic:
        inputs["marks_digest"] = _pairs_digest(marks)
    return plugin, inputs


def family_registry() -> dict[str, dict[str, Any]]:
    """The two frozen V14 families (identities from the frozen modules)."""
    from research.v11.publication_identity import arm_config_digest
    from research.v14.families.basislv_premfade.frozen_identity import (
        BASISLV_ARM_CONFIG_DIGESTS,
        frozen_identity as basislv_frozen_identity,
    )
    from research.v14.families.basislv_premfade.strategy import (
        ARM_ROLES as BASISLV_ROLES,
        FAMILY_ID as BASISLV_FAMILY,
    )
    from research.v14.families.oicyc.frozen_identity import (
        OICYC_ARM_CONFIG_DIGESTS,
        frozen_identity as oicyc_frozen_identity,
    )
    from research.v14.families.oicyc.strategy import (
        ARM_ROLES as OICYC_ROLES,
        FAMILY_ID as OICYC_FAMILY,
    )

    return {
        "basislv_premfade": {
            "family_id": BASISLV_FAMILY,
            "lane_handoff": "research/control/v14_run/i_family_1/lane_handoff.json",
            "arms": tuple(sorted(BASISLV_ROLES)),
            "roles": dict(BASISLV_ROLES),
            "identity": basislv_frozen_identity,
            "recorded_digests": dict(BASISLV_ARM_CONFIG_DIGESTS),
            "digest": lambda arm_id: arm_config_digest(
                basislv_frozen_identity(arm_id), arm_id=arm_id
            ),
            "build": build_basislv,
        },
        "oicyc": {
            "family_id": OICYC_FAMILY,
            "lane_handoff": "research/control/v14_run/i_family_2/lane_handoff.json",
            "arms": tuple(sorted(OICYC_ROLES)),
            "roles": dict(OICYC_ROLES),
            "identity": oicyc_frozen_identity,
            "recorded_digests": dict(OICYC_ARM_CONFIG_DIGESTS),
            "digest": lambda arm_id: arm_config_digest(
                oicyc_frozen_identity(arm_id), arm_id=arm_id
            ),
            "build": build_oicyc,
        },
    }


def verify_all_arm_digests(
    registry: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """Six-arm digest pin: recomputed == recorded + pairwise uniqueness.

    Recomputes every frozen arm digest from the frozen identity modules,
    compares against the digests RECORDED by the family lanes at
    implementation time (before any scored metric existed), and asserts at
    DRIVER level that the six exact digests are pairwise unique.  Fail-closed
    input: ``ok`` is True only when all six match AND all are pairwise
    distinct.
    """
    owners = {
        arm: family for family, fam in registry.items() for arm in fam["arms"]
    }
    report: dict[str, Any] = {"arms": {}, "ok": True}
    computed: dict[str, list[str]] = {}
    for family, fam in registry.items():
        for arm in fam["arms"]:
            module_digest = fam["digest"](arm)
            recorded = str(fam["recorded_digests"].get(arm, ""))
            match = bool(recorded) and module_digest == recorded
            report["arms"][arm] = {
                "family": family,
                "module_digest": module_digest,
                "recorded_digest": recorded,
                "match": match,
            }
            report["ok"] &= match
            computed.setdefault(family, []).append(module_digest)
    all_digests = [d for fam_digests in computed.values() for d in fam_digests]
    report["n_arms"] = len(all_digests)
    report["n_match"] = sum(
        1 for v in report["arms"].values() if v.get("match") is True
    )
    collisions = sorted({d for d in all_digests if all_digests.count(d) > 1})
    report["pairwise_unique"] = not collisions and len(all_digests) == 6
    report["collisions"] = collisions
    report["ok"] &= report["pairwise_unique"]
    return report


# --------------------------------------------------------------------------- #
# Compute core: matrix -> baseline scored metrics (importable for tests)
# --------------------------------------------------------------------------- #
def derive_contract(plugin: Any) -> tuple[Any, dict[str, Any]]:
    """L-V11-1 family cell derivation from the frozen folds contract."""
    from research.adapter_v10.stress import derive_family_stress_matrix
    from research.v12.accounting import freeze_family_cell_contract

    derivation = derive_family_stress_matrix(
        strategy_baseline=plugin.baseline_stress(),
        droppable_symbols=tuple(plugin.tradeable_universe()),
        folds=plugin.folds,
        instants=list(plugin.schedule().instants),
    )
    contract = freeze_family_cell_contract(
        str(plugin.identity().family_id), [cell.spec for cell in derivation.cells]
    )
    return derivation, contract


def verify_runner_traversal(plugin: Any) -> dict[str, Any]:
    """Frozen runner-compatibility pin (BEFORE any scored metric exists).

    The frozen generic adapter queries ``targets_at`` at EVERY non-final
    schedule instant of EVERY accepted matrix cell (gap instants are
    carried, never opened); a frozen plugin that refuses any mandatory
    query fails the run closed here -- no matrix compute is started.  This
    probe also exercises the plugin's zero-position/eligibility refusals on
    the loaded data (an under-breadth stamp surfaces here, pre-metric).
    ``AdapterError`` is the common base of the adapter's
    ``ContractViolation`` AND the families' ``EligibilityShortfall``
    refusals -- both mean the scored traversal is impossible.
    """
    from research.adapter_v10.protocol import AdapterError

    derivation, _contract = derive_contract(plugin)
    open_instants = list(plugin.schedule().instants)[:-1]
    problems: list[dict[str, Any]] = []
    probes = 0
    for cell in derivation.cells:
        universe = plugin.universe(cell.spec)
        for instant in open_instants:
            probes += 1
            try:
                plugin.targets_at(int(instant), universe=universe, stress=cell.spec)
            except AdapterError as exc:
                problems.append(
                    {
                        "cell": str(cell.name),
                        "instant_ns": int(instant),
                        "instant_iso": iso_utc_ns(int(instant)),
                        "error": str(exc),
                    }
                )
                break  # per-cell short-circuit: one refusal pins the cell
    return {
        "artifact": "v14_phase_e_runner_traversal_pin",
        "schema": "v14.traversal_pin.v1",
        "note": (
            "the frozen generic runner queries targets_at at every non-final "
            "schedule instant of every accepted cell; refusals here make the "
            "scored traversal impossible without a frozen-module change"
        ),
        "probes": probes,
        "cells_probed": [str(cell.name) for cell in derivation.cells],
        "schedule_instants": len(plugin.schedule().instants),
        "problems": problems,
        "ok": not problems,
    }


def iso_utc_ns(stamp_ns: int) -> str:
    """ISO-UTC rendering of an epoch-ns stamp (I/O plumbing only)."""
    from research.v12.data_contract import ns_to_iso_utc

    return str(ns_to_iso_utc(int(stamp_ns)))


def cost_breakout(baseline_run: Mapping[str, Any]) -> dict[str, Any]:
    """Cost split into FILLS vs HOLDING terms (L-V14-0 remediated kernel).

    The frozen adapter charges cost ONLY at book transitions
    (``rebalance_cost_between`` at weight deltas; a carried book has an
    identical prior/target and charges exactly 0.0).  ``cost_fills`` sums
    the charged rows (entries / force-flats / re-entries);
    ``cost_holding_terms`` sums every carried boundary's charge and MUST be
    exactly 0.0 by construction -- the driver asserts it and refuses the
    scored record otherwise.
    """
    daily_rows = list(baseline_run.get("daily_returns") or [])
    books = list(baseline_run.get("books") or [])
    carried = {
        int(book["decision_ns"]) for book in books if bool(book.get("carried_forward"))
    }
    fills = 0.0
    holding = 0.0
    row_instants = {int(row["decision_ns"]) for row in daily_rows}
    for row in daily_rows:
        cost = float(row.get("cost_charged_per_unit", 0.0))
        if int(row["decision_ns"]) in carried:
            holding += cost
        else:
            fills += cost
    fills = round(fills, 12)
    holding = round(holding, 12)
    return {
        "cost_fills": fills,
        "cost_holding_terms": holding,
        "cost_total": round(fills + holding, 12),
        "holding_terms_zero_by_construction": holding == 0.0,
        "carried_boundaries": len(carried & row_instants),
        "transition_boundaries": len(row_instants - carried),
    }


def fold_signs(baseline_run: Mapping[str, Any]) -> dict[str, Any]:
    """Per-fold net-return sign vector (the incremental-gate input)."""
    per_fold: dict[int, float] = {}
    for row in baseline_run.get("daily_returns") or []:
        idx = int(row["fold_index"])
        per_fold[idx] = per_fold.get(idx, 0.0) + float(row["net_return_per_unit"])
    ordered = [per_fold[k] for k in sorted(per_fold)]
    return {
        "fold_net_sums": {str(k): round(v, 12) for k, v in sorted(per_fold.items())},
        "fold_positive": [v > 0.0 for v in ordered],
    }


def expectancy_split(baseline_run: Mapping[str, Any]) -> dict[str, Any]:
    """Price-only vs total after-cost expectancy (the REQUIRED gate input).

    ``price_only_expectancy``: mean per-decision after-cost price PnL with
    native funding EXCLUDED.  ``total_expectancy``: mean per-decision total
    after-cost PnL with native funding INCLUDED.  Funding credits are
    reported alongside so the price-only failure clause is auditable.
    """
    metrics = dict(baseline_run.get("portfolio_metrics") or {})
    n_days = int(metrics.get("n_days_with_records", 0) or 0)
    if n_days <= 0:
        raise RuntimeError("no realized days; expectancy split undefined")
    price = float(metrics.get("price_pnl_sum", 0.0))
    funding = float(metrics.get("funding_sum", 0.0))
    cost = float(metrics.get("cost_charged_sum", 0.0))
    return {
        "price_only_expectancy": round((price - cost) / n_days, 12),
        "total_expectancy": round((price + funding - cost) / n_days, 12),
        "funding_credit_sum": round(funding, 12),
        "n_days_with_records": n_days,
    }


def scored_metrics_from_baseline(baseline_run: Mapping[str, Any]) -> dict[str, Any]:
    """Scored metrics + REAL decision/fill evidence (remediated kernel)."""
    from research.v12.accounting import REQUIRED_SCORED_FIELDS

    metrics = dict(baseline_run.get("portfolio_metrics") or {})
    positions = list(baseline_run.get("positions") or [])
    books = list(baseline_run.get("books") or [])
    decisions = [
        {"symbol": str(sym), "decision_ts": int(book["decision_ns"])}
        for book in books
        for sym, weight in (book.get("weights") or [])
        if float(weight) != 0.0
    ]
    fills = [
        {"symbol": str(pos["symbol"]), "ts_ns": int(pos["entry_ns"])}
        for pos in positions
    ]
    breakout = cost_breakout(baseline_run)
    if not breakout["holding_terms_zero_by_construction"]:
        raise RuntimeError(
            "cost_holding_terms must be exactly 0 by construction "
            f"(remediated L-V14-0 kernel); measured {breakout['cost_holding_terms']!r}"
        )
    scored = {
        "score_valid": all(_finite(metrics.get(k)) for k in REQUIRED_SCORED_FIELDS),
        "net_return_sum": metrics.get("net_return_sum"),
        "expectancy_per_day": metrics.get("expectancy_per_day"),
        "max_drawdown": metrics.get("max_drawdown"),
        "position_pf": metrics.get("position_pf"),
        "n_positions": len(positions),
        "n_decisions": len(decisions),
        "n_fills": len(fills),
        "decisions": decisions,
        "fills": fills,
        "cost_fills": breakout["cost_fills"],
        "cost_holding_terms": breakout["cost_holding_terms"],
        "cost_total": breakout["cost_total"],
        "funding_sum": metrics.get("funding_sum"),
        "price_pnl_sum": metrics.get("price_pnl_sum"),
        "remediated_kernel": True,
    }
    return scored


def apply_family_scored_record_extensions(
    *,
    family: str,
    plugin: Any,
    result: dict[str, Any],
    baseline: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], Optional[dict[str, Any]]]:
    """Family scored-record obligations on the baseline cell (importable).

    oicyc: the CONFIRMATORY status metadata (plan Section 1.1) flows from
    ``plugin.status_metadata()`` into the scored record
    (``confirmatory_status`` + ``denominator_note``, hence inside the ledger
    row) and the block is returned for the cell summary / verdict record.
    basislv: the price-only vs total expectancy split is embedded in the
    scored record.  Returns ``(fold_signs_block, expectancy_split,
    confirmatory_block)``.
    """
    fold_signs_block = fold_signs(baseline)
    split = expectancy_split(baseline)
    confirmatory: Optional[dict[str, Any]] = None
    if family == "oicyc":
        confirmatory = dict(plugin.status_metadata())
        result["scored_metrics"]["confirmatory_status"] = confirmatory[
            "scored_status"
        ]
        result["scored_metrics"]["denominator_note"] = confirmatory[
            "denominator_note"
        ]
    if family == "basislv_premfade":
        result["scored_metrics"]["price_only_expectancy"] = split[
            "price_only_expectancy"
        ]
        result["scored_metrics"]["total_expectancy"] = split["total_expectancy"]
        result["scored_metrics"]["funding_credit_sum"] = split["funding_credit_sum"]
    return fold_signs_block, split, confirmatory


def compute_cell(
    *,
    family: str,
    arm_id: str,
    plugin: Any,
    out_dir: Path,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    """Run the frozen family matrix for ONE arm; score the baseline only."""
    from research.adapter_v10.hashes import payload_sha256
    from research.adapter_v10.runner import run_strategy

    derivation, contract = derive_contract(plugin)
    cells = list(derivation.cells)
    if not cells or cells[0].name != "baseline":
        raise RuntimeError(
            f"family derivation must carry the baseline first, got {[c.name for c in cells]}"
        )
    runs: dict[str, Any] = {}
    for cell in cells:
        cell_dir = out_dir / "matrix" / cell.spec.key
        runs[cell.name] = run_strategy(
            plugin,
            stress=cell.spec,
            out_dir=cell_dir,
            write_artifact_file=write_artifacts,
        )
    baseline = runs["baseline"]
    matrix_digest = payload_sha256({name: runs[name]["hashes"] for name in runs})
    scored = scored_metrics_from_baseline(baseline)
    return {
        "family": family,
        "arm_id": arm_id,
        "derivation_record": derivation.record,
        "matrix_cells": [cell.name for cell in cells],
        "matrix_digest": matrix_digest,
        "runs": runs,
        "baseline_cell": "baseline",
        "baseline_run": baseline,
        "scored_metrics": scored,
        "contract": contract,
        "universe": list(baseline["universe"]),
    }


# --------------------------------------------------------------------------- #
# Family gates (scored layer obligations)
# --------------------------------------------------------------------------- #
def load_sibling_fold_signs(
    family_out_dir: Path, arm_id: str
) -> Optional[dict[str, Any]]:
    """Sibling arm fold signs from its baseline_metrics.json (or None)."""
    path = family_out_dir / arm_id / "baseline_metrics.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    signs = payload.get("fold_signs")
    return dict(signs) if isinstance(signs, dict) else None


def evaluate_basislv_family_gate(
    *,
    anchor_arm: str,
    control_arm: str,
    neighbour_arm: str,
    family_out_dir: Path,
    anchor_run: Mapping[str, Any],
) -> dict[str, Any]:
    """The preregistered family gate with the REQUIRED clause inputs.

    Computes the price-only vs total expectancy split from the anchor's
    baseline cell, loads the control/neighbour fold-sign vectors from their
    driver-written ``baseline_metrics.json`` artifacts (earlier invocations
    of this same driver), and calls the frozen
    ``gate_runner.evaluate_family_gate``.  Missing sibling evidence or
    missing clause inputs yields the frozen BLOCKED verdict -- never an
    inferred PASS.
    """
    from research.v14.families.basislv_premfade.gate_runner import (
        evaluate_family_gate,
    )

    split = expectancy_split(anchor_run)
    anchor_signs = fold_signs(anchor_run)["fold_positive"]
    control_signs = load_sibling_fold_signs(family_out_dir, control_arm)
    neighbour_signs = load_sibling_fold_signs(family_out_dir, neighbour_arm)
    missing = [
        label
        for label, signs in (
            (control_arm, control_signs),
            (neighbour_arm, neighbour_signs),
        )
        if signs is None or not signs.get("fold_positive")
    ]
    record: dict[str, Any] = {
        "artifact": "v14_phase_e_basislv_family_gate",
        "schema": "v14.basislv_gate.v1",
        "at_utc": utc_now(),
        "anchor_arm": anchor_arm,
        "control_arm": control_arm,
        "neighbour_arm": neighbour_arm,
        "expectancy_split": split,
        "anchor_fold_positive": anchor_signs,
        "missing_inputs": [],
        "price_only_clause_inputs_supplied": True,
    }
    if missing:
        record["missing_inputs"] = missing
        record["price_only_clause_inputs_supplied"] = False
        record["verdict"] = "BLOCKED_SIBLING_EVIDENCE_MISSING"
        record["reason"] = (
            "the family gate requires the control/neighbour fold-sign "
            "vectors from their scored cells; run this driver for "
            f"{', '.join(missing)} before the anchor invocation "
            "(fail closed, never an inferred PASS)"
        )
        return record
    verdict = evaluate_family_gate(
        anchor_fold_positive=anchor_signs,
        control_fold_positive=list(control_signs["fold_positive"]),
        neighbour_fold_positive=list(neighbour_signs["fold_positive"]),
        price_only_expectancy=split["price_only_expectancy"],
        total_expectancy=split["total_expectancy"],
    )
    record["verdict"] = verdict.get("verdict")
    record["gate_verdict"] = verdict
    return record


# --------------------------------------------------------------------------- #
# TECHABORT (pre-ledger crash forensics; V12R/V13R precedent)
# --------------------------------------------------------------------------- #
def write_techabort(
    *,
    techabort_dir: Path,
    arm_id: str,
    family: str,
    exc: BaseException,
    phase: str,
    head: str,
    scored_metric_computed: bool,
    ledger_path: Optional[Path],
    out_dir: Optional[Path],
    preflight_path: Optional[Path],
) -> Path:
    """Write ``TECHABORT_<arm>.json`` with the crash evidence, then exit 1.

    Budget effect is ZERO unless the exactly-once ledger row was already
    written; the file records the honest ledger state either way.  The sink
    was resolved fail-closed by ``main``: real runs sink into the designated
    exec root's control tree (``--techabort-dir`` overrides); synthetic
    runs sink only inside the scratch out-root and never under a
    ``research/control`` subtree.  The fix path is DRIVER-ONLY: frozen
    family/adapter bytes are never edited.
    """
    ledger_state: dict[str, Any] = {
        "ledger_path": str(ledger_path) if ledger_path else None,
        "ledger_exists": bool(ledger_path and Path(ledger_path).is_file()),
    }
    if ledger_state["ledger_exists"]:
        try:
            from research.v12.accounting import read_v12_ledger

            ledger_state["ledger_sha256"] = read_v12_ledger(Path(ledger_path))["sha256"]
        except Exception as ledger_exc:  # noqa: BLE001 - forensic must not crash
            ledger_state["ledger_read_error"] = str(ledger_exc)
    payload = {
        "schema": "v14_techabort_forensic_v1",
        "generated_utc": utc_now(),
        "producer_role": "A1",
        "artifact": f"TECHABORT_{arm_id}",
        "family": family,
        "arm_id": arm_id,
        "phase": phase,
        "crash": {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback_tail": "\n".join(traceback.format_exc().splitlines()[-12:]),
        },
        "exec_head": head,
        "scored_metric_computed": bool(scored_metric_computed),
        "ledger_state": ledger_state,
        "budget_effect": (
            "ZERO budget consumed (no scored metric computed; TECHABORT per "
            "PLAN_crypto 14)"
            if not scored_metric_computed and not ledger_state["ledger_exists"]
            else "NO LEDGER WRITE COMPLETED (crash before the exactly-once "
            "publication decision); cell artifacts partial; see ledger_state"
        ),
        "out_dir": str(out_dir) if out_dir else None,
        "preflight_artifact": str(preflight_path) if preflight_path else None,
        "fix_path": (
            "driver-only: diagnose and fix research/control/v14_run/tools/"
            "run_v14_cell.py (or its test); frozen family/adapter/accounting "
            "bytes are never edited; re-run the same arm invocation after the fix"
        ),
    }
    path = techabort_dir / f"TECHABORT_{arm_id}.json"
    _write_json(path, payload)
    return path


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--family", required=True, choices=FAMILIES)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--exec-root", default=str(DRIVER_REPO_ROOT))
    parser.add_argument(
        "--staged-root",
        required=True,
        help=(
            "staged-equivalent bars/funding/mark/ticks root (a3 staging "
            "authority layout; the P1 recompute_*.py assembly)"
        ),
    )
    parser.add_argument(
        "--basis-staged-root",
        default=None,
        help="A9-F staged basis bulk root (default the integration staged dir)",
    )
    parser.add_argument(
        "--basis-manifest",
        default=None,
        help="A9-F staged basis manifest (default <exec-root> authority path)",
    )
    parser.add_argument("--oi-root", default=None, help="staged OI root")
    parser.add_argument(
        "--oi-manifest",
        default=None,
        help="OI staging manifest (default <exec-root> v11 authority path)",
    )
    parser.add_argument(
        "--out-root",
        default=None,
        help="default <exec-root>/results/v14_phase_e/<family>/<arm>",
    )
    parser.add_argument(
        "--ledger",
        default=None,
        help="per-family shard ledger (required with --publish)",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="A1-only: write the exactly-once ledger row",
    )
    parser.add_argument(
        "--expect-head",
        default=None,
        help="frozen pin (required with --publish)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "synthetic full-path exercise: no scored ledger can be written; "
            "requires an explicit scratch --out-root"
        ),
    )
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument(
        "--techabort-dir",
        default=None,
        help=(
            "forensic dir for TECHABORT_<arm>.json (real runs default to "
            "<exec-root>/research/control/v14_run; --dry-run defaults to "
            "<out-root>/TECHABORT and refuses any research/control sink)"
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:  # noqa: PLR0912
    t_start = time.time()
    args = parse_args(argv)
    reason = validate_args(args)
    if reason:
        print(f"FAIL-CLOSED: {reason}")
        return EXIT_FAIL_CLOSED

    synthetic = bool(args.dry_run)
    exec_root = Path(args.exec_root).resolve()
    staged_root = Path(args.staged_root).resolve()
    out_dir = (
        Path(args.out_root).resolve()
        if args.out_root
        else exec_root / "results" / "v14_phase_e" / args.family / args.arm
    )
    # TECHABORT sink discipline: an explicit --techabort-dir wins; otherwise
    # synthetic runs sink into the mandatory scratch out-root and REAL runs
    # sink into the designated exec root's control tree.  A synthetic run
    # whose sink resolves under any research/control subtree is refused
    # BEFORE any work (forensic files are real-scoring-time only).
    if args.techabort_dir:
        techabort_dir = Path(args.techabort_dir).resolve()
    elif synthetic:
        techabort_dir = out_dir / "TECHABORT"
    else:
        techabort_dir = exec_root.joinpath(*TECHABORT_REAL_DIR_RELPATH)
    if synthetic and techabort_sink_under_control_tree(techabort_dir):
        print(
            "FAIL-CLOSED: --dry-run refuses a TECHABORT sink under a "
            f"research/control subtree: {techabort_dir}; forensic files are "
            "written at real scoring time only -- pass --techabort-dir "
            "inside the scratch tree"
        )
        return EXIT_FAIL_CLOSED
    basis_staged_root = (
        Path(args.basis_staged_root).resolve()
        if args.basis_staged_root
        else _default_basis_staged_root()
    )
    basis_manifest_path = (
        Path(args.basis_manifest).resolve()
        if args.basis_manifest
        else exec_root.joinpath(*BASIS_MANIFEST_RELPATH)
    )
    oi_root = (
        args.oi_root
        if args.oi_root
        else str(_default_oi_root())
    )
    oi_manifest_path = (
        Path(args.oi_manifest).resolve()
        if args.oi_manifest
        else exec_root.joinpath(*OI_MANIFEST_RELPATH)
    )
    sys.path.insert(0, str(exec_root))

    # Import-order contract (A7 wave-1 pin convention): the generic adapter
    # is imported before anything that pulls research.v11.publication_identity.
    import research.adapter_v10  # noqa: F401

    registry = family_registry()
    fam = registry[args.family]
    if args.arm not in fam["arms"]:
        print(
            f"FAIL-CLOSED: arm {args.arm!r} not frozen for {args.family} "
            f"{fam['arms']}"
        )
        return EXIT_FAIL_CLOSED

    head = git_head(exec_root)
    if args.publish and args.expect_head != head:
        print(
            f"FAIL-CLOSED: exec head {head} != expected pin {args.expect_head}; "
            "no data loaded, no metric computed"
        )
        return EXIT_FAIL_CLOSED

    # ---- crash guard: everything below writes TECHABORT on any crash ---- #
    scored_metric_computed = False
    ledger_path: Optional[Path] = Path(args.ledger).resolve() if args.ledger else None
    preflight_path: Optional[Path] = None
    try:
        # ---- six-arm digest pin (data-independent; BEFORE any load) ---- #
        digest_report = verify_all_arm_digests(registry)
        if not digest_report["ok"]:
            offenders = {
                arm: entry
                for arm, entry in digest_report["arms"].items()
                if not entry["match"]
            }
            print(
                "FAIL-CLOSED: six-arm arm-config digest pin failed "
                f"({digest_report['n_match']}/{digest_report['n_arms']} match; "
                f"pairwise_unique={digest_report['pairwise_unique']}; "
                f"offenders={_canonical(offenders)})"
            )
            return EXIT_FAIL_CLOSED
        digest = fam["digest"](args.arm)

        # ---- staged-root verification (transport integrity) ---- #
        authority_files: Optional[dict[str, Any]] = None
        authority_path: Optional[Path] = None
        if not synthetic:
            authority_path = exec_root.joinpath(*A3_STAGING_MANIFEST_RELPATH)
            if not authority_path.is_file():
                print(f"FAIL-CLOSED: staging authority missing: {authority_path}")
                return EXIT_FAIL_CLOSED
            authority_files = dict(
                json.loads(authority_path.read_text(encoding="utf-8"))["files"]
            )
        staged = verify_staged_root(
            staged_root,
            synthetic=synthetic,
            authority_files=authority_files,
            authority_path=authority_path,
        )
        if not staged["ok"]:
            print("FAIL-CLOSED: staged root verification failed:")
            for problem in staged["problems"]:
                print(f"  - {problem}")
            return EXIT_FAIL_CLOSED
        if not synthetic and basis_manifest_path.is_file():
            measured = sha256_file(basis_manifest_path)
            if measured != BASIS_MANIFEST_RECORDED_SHA256:
                print(
                    "FAIL-CLOSED: staged basis manifest SHA mismatch: measured "
                    f"{measured} != recorded {BASIS_MANIFEST_RECORDED_SHA256}"
                )
                return EXIT_FAIL_CLOSED

        # ---- load the staged bundles through the frozen loaders ---- #
        # Per-family build kwargs: each frozen build_* accepts exactly its own
        # family's roots (a driver-side TypeError here is what the cancelled
        # lane's TECHABORT strays recorded -- never pass one family's kwargs
        # into the other family's constructor again).
        t_load = time.time()
        if args.family == "basislv_premfade":
            build_kwargs: dict[str, Any] = {
                "synthetic": synthetic,
                "basis_staged_root": basis_staged_root,
                "basis_manifest_path": basis_manifest_path,
            }
        else:
            build_kwargs = {
                "synthetic": synthetic,
                "oi_root": oi_root,
                "oi_manifest_path": oi_manifest_path,
            }
        plugin, inputs = fam["build"](
            staged_root,
            args.arm,
            exec_root,
            **build_kwargs,
        )
        load_seconds = round(time.time() - t_load, 1)
        identity = plugin.identity()
        cost_model = plugin.cost_model()

        # ---- frozen runner-compatibility pin (pre-metric) ---- #
        t_pin = time.time()
        traversal = verify_runner_traversal(plugin)
        pin_seconds = round(time.time() - t_pin, 1)

        preflight = {
            "artifact": "v14_phase_e_cell_preflight",
            "schema": "v14.preflight.v1",
            "family": args.family,
            "family_id": fam["family_id"],
            "lane_handoff": fam["lane_handoff"],
            "arm_id": args.arm,
            "role": fam["roles"][args.arm],
            "at_utc": utc_now(),
            "exec_root": str(exec_root),
            "exec_head": head,
            "expect_head": args.expect_head,
            "producer_role": "A1",
            "mode": "synthetic_dry_run" if synthetic else "real",
            "no_scored_metric_yet": True,
            "staged": staged,
            "six_arm_digest_pin": digest_report,
            "arm_config_digest": digest,
            "strategy_id": identity.strategy_id,
            "arm_config_id": identity.arm_config_id,
            "window_pins": [identity.window_start_iso, identity.window_end_iso],
            "cost_model": {
                "taker_fee_bps": float(cost_model.taker_fee_bps),
                "adverse_tick_slip_floor": int(cost_model.adverse_tick_slip_floor),
                "default_tick_sizes": {
                    str(k): float(v)
                    for k, v in sorted(cost_model.default_tick_sizes.items())
                },
            },
            "remediated_kernel": True,
            "zero_position_refusal": (
                "plugin EligibilityShortfall (breadth floor, probed by the "
                "traversal pin) + accounting-layer REFUSED_ZERO_POSITIONS "
                "(publication gate)"
            ),
            "fold_force_flat": (
                "both families implement fold-terminal force-flat; the frozen "
                "runner carries gap instants and never opens across folds"
            ),
            "inputs": inputs,
            "runner_traversal_pin": traversal,
            "input_snapshot_sha256": (
                staged["staged_manifest_sha256"]
                or staged["authority_sha256"]
                or staged["staged_root"]
            ),
            "code_sha256": head,
            "loader_seconds": load_seconds,
            "pin_seconds": pin_seconds,
            "note": "no scored metric existed when this file was written",
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        preflight_path = out_dir / "preflight.json"
        _write_json(preflight_path, preflight)
        if not traversal["ok"]:
            first = traversal["problems"][0]
            print(
                "FAIL-CLOSED: frozen runner-compatibility pin failed for "
                f"{args.family}/{args.arm}: cell {first['cell']} instant "
                f"{first['instant_iso']}: {first['error']}"
            )
            print(
                "BLOCKED-FROZEN-CONFLICT: the frozen plugin refuses a mandatory "
                "frozen-runner query; no matrix compute started, no scored "
                "metric exists. Resolving this requires an owner decision and "
                "a new freeze delta audit (never a driver-side workaround)."
            )
            return EXIT_FAIL_CLOSED
        print(
            "PREFLIGHT",
            json.dumps(
                {
                    "family": args.family,
                    "arm_id": args.arm,
                    "role": preflight["role"],
                    "mode": preflight["mode"],
                    "exec_head": head,
                    "six_arm_digests_pairwise_unique": digest_report[
                        "pairwise_unique"
                    ],
                    "staged_files_verified": staged["files_verified"],
                }
            ),
        )
        if args.preflight_only:
            return EXIT_OK

        # ---- compute the frozen matrix; score the baseline cell only ---- #
        t_compute = time.time()
        result = compute_cell(
            family=args.family,
            arm_id=args.arm,
            plugin=plugin,
            out_dir=out_dir,
            write_artifacts=not synthetic,
        )
        compute_seconds = round(time.time() - t_compute, 1)
        scored_metric_computed = True
        baseline = result["baseline_run"]

        # ---- scored-record extensions ---- #
        (
            fold_signs_block,
            split,
            confirmatory,
        ) = apply_family_scored_record_extensions(
            family=args.family,
            plugin=plugin,
            result=result,
            baseline=baseline,
        )

        baseline_metrics = {
            "baseline_cell": result["baseline_cell"],
            "metrics": baseline.get("portfolio_metrics") or {},
            "scored_metrics": result["scored_metrics"],
            "hashes": baseline.get("hashes") or {},
            "fold_signs": fold_signs_block,
            "expectancy_split": split,
        }
        _write_json(out_dir / "baseline_metrics.json", baseline_metrics)
        _write_json(
            out_dir / "matrix_summary.json",
            {
                "matrix_cells": result["matrix_cells"],
                "derivation_record": result["derivation_record"],
                "matrix_digest": result["matrix_digest"],
                "universe": result["universe"],
            },
        )
        print(
            "BASELINE",
            json.dumps(
                {
                    k: result["scored_metrics"][k]
                    for k in (
                        "score_valid",
                        "net_return_sum",
                        "expectancy_per_day",
                        "max_drawdown",
                        "n_positions",
                        "cost_fills",
                        "cost_holding_terms",
                    )
                }
            ),
            f"compute_seconds={compute_seconds}",
        )

        # ---- family gate (basislv anchor: REQUIRED clause inputs) ---- #
        gate_record: Optional[dict[str, Any]] = None
        if args.family == "basislv_premfade" and args.arm == _anchor_arm(
            registry, args.family
        ):
            gate_record = evaluate_basislv_family_gate(
                anchor_arm=args.arm,
                control_arm=_control_arm(registry, args.family),
                neighbour_arm=_neighbour_arm(registry, args.family),
                family_out_dir=out_dir.parent,
                anchor_run=baseline,
            )
            _write_json(out_dir / "gate_record.json", gate_record)
            print("GATE", json.dumps({"verdict": gate_record["verdict"]}))

        if synthetic:
            print(
                "DRY-RUN: full path exercised on the synthetic staged root; "
                "no scored ledger written (publication refused by mode)"
            )
            return EXIT_OK

        if not args.publish:
            print("PUBLISH: skipped (no --publish); cell artifacts written only")
            return EXIT_OK

        from research.v12.accounting import (
            STAGE_IDEMPOTENT_REPLAY,
            STAGE_PUBLISHED,
            publish_v12_cell,
            read_v12_ledger,
            v12_denominator_view,
        )

        before = v12_denominator_view(ledger_path)
        publication = publish_v12_cell(
            strategy_id=identity.strategy_id,
            family=fam["family_id"],
            arm_id=args.arm,
            arm_config_digest=digest,
            stress_signature=plugin.baseline_stress().signature(),
            window_start_iso=identity.window_start_iso,
            window_end_iso=identity.window_end_iso,
            scored_metrics=result["scored_metrics"],
            result_sha256=str(baseline["hashes"]["result_sha256"]),
            ledger_path=ledger_path,
            family_contract_cells=result["contract"],
            producer_head_sha=head,
        )
        _write_json(out_dir / "publish_record.json", publication)
        after = v12_denominator_view(ledger_path)
        ledger_state = read_v12_ledger(ledger_path)
        total_seconds = round(time.time() - t_start, 1)
        cell_summary = {
            "artifact": "v14_phase_e_cell_summary",
            "family": args.family,
            "family_id": fam["family_id"],
            "arm_id": args.arm,
            "role": fam["roles"][args.arm],
            "at_utc": utc_now(),
            "producer_head_sha": head,
            "arm_config_digest": digest,
            "remediated_kernel": True,
            "cost_breakout": {
                "cost_fills": result["scored_metrics"]["cost_fills"],
                "cost_holding_terms": result["scored_metrics"]["cost_holding_terms"],
            },
            "staged_manifest_sha256": (
                staged["staged_manifest_sha256"]
                or staged["authority_sha256"]
                or staged["staged_root"]
            ),
            "matrix_digest": result["matrix_digest"],
            "matrix_cells": result["matrix_cells"],
            "universe": result["universe"],
            "baseline_result_sha256": str(baseline["hashes"]["result_sha256"]),
            "scored_metrics": {
                k: result["scored_metrics"][k]
                for k in (
                    "score_valid",
                    "net_return_sum",
                    "expectancy_per_day",
                    "max_drawdown",
                    "n_positions",
                    "n_decisions",
                    "n_fills",
                    "cost_fills",
                    "cost_holding_terms",
                )
            },
            "confirmatory": confirmatory,
            "gate_verdict": (gate_record or {}).get("verdict"),
            "publish_stage": publication["stage"],
            "published": bool(publication["published"]),
            "reason_codes": [str(r) for r in publication["reasons"]],
            "observed_delta": int(publication["observed_delta"]),
            "published_delta": int(publication["published_delta"]),
            "denominator_before": before,
            "denominator_after": after,
            "ledger_path": str(ledger_path),
            "ledger_sha256_after": ledger_state["sha256"],
            "input_snapshot_sha256": staged["staged_manifest_sha256"],
            "run_seconds": {
                "load": load_seconds,
                "compute": compute_seconds,
                "total": total_seconds,
            },
        }
        _write_json(out_dir / "cell_summary.json", cell_summary)
        print(
            "PUBLISH",
            json.dumps(
                {
                    "stage": publication["stage"],
                    "published": publication["published"],
                    "reasons": publication["reasons"],
                    "denominator_after": after,
                },
                default=str,
            ),
        )
        if publication["stage"] in (STAGE_PUBLISHED, STAGE_IDEMPOTENT_REPLAY):
            return EXIT_OK
        return EXIT_REFUSED
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 - the driver reports its crash
        techabort = write_techabort(
            techabort_dir=techabort_dir,
            arm_id=args.arm,
            family=args.family,
            exc=exc,
            phase=(
                "pre-metric (before the exactly-once ledger decision)"
                if not scored_metric_computed
                else "post-metric pre-publication"
            ),
            head=head,
            scored_metric_computed=scored_metric_computed,
            ledger_path=ledger_path,
            out_dir=out_dir,
            preflight_path=preflight_path,
        )
        print(f"CRASH: {type(exc).__name__}: {exc}")
        print(f"TECHABORT: forensic file written: {techabort}")
        if isinstance(exc, KeyboardInterrupt):
            return EXIT_CRASH
        raise SystemExit(EXIT_CRASH) from exc


def _anchor_arm(registry: Mapping[str, Mapping[str, Any]], family: str) -> str:
    from research.v14.families.basislv_premfade.strategy import ANCHOR_ARM

    return str(ANCHOR_ARM)


def _control_arm(registry: Mapping[str, Mapping[str, Any]], family: str) -> str:
    from research.v14.families.basislv_premfade.strategy import CONTROL_ARM

    return str(CONTROL_ARM)


def _neighbour_arm(registry: Mapping[str, Mapping[str, Any]], family: str) -> str:
    from research.v14.families.basislv_premfade.strategy import NEIGHBOUR_ARM

    return str(NEIGHBOUR_ARM)


def _default_oi_root() -> str:
    from research.v12.data_contract import OI_CONSOLIDATED_ROOT

    return str(OI_CONSOLIDATED_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
