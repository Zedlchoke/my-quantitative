"""V12R Phase E scored-cell driver (A1, strong host; one arm per invocation).

Frozen V10R ``run_m01_cell.py`` pattern, wired to the FROZEN V12 families
``research.v12.families.{oilev_v2,bab_lowbeta}`` -- no V11 family logic is
imported and no frozen identity, cost, fold, gate or universe constant is
re-declared here.  Everything family-specific comes from the frozen family
strategy/plugin modules; everything adapter-specific comes from the frozen
generic adapter; publication goes through the frozen V12 accounting entry
point only.

  preflight pins (written BEFORE any scored metric exists)
    -> read-only staged-data loaders from the exec tree's ``staged_data/``
       snapshot (the frozen V12 loader modules with explicit roots; the
       BAB catalog shim is a read-through NTFS junction / symlink, never a
       data copy)
    -> 6/6 frozen arm-config digest equality vs ``selection_freeze.json``
       (fail-closed before any compute)
    -> family stress matrix derived from the frozen folds contract
       (L-V11-1 derivation; never the generic superset)
    -> every accepted matrix cell run; scored metrics from the BASELINE
       cell only, with real decision/fill evidence records
    -> exactly-once publication through
       :func:`research.v12.accounting.publish_v12_cell` (A1 sole publisher,
       per-family shard ledger, ``--publish`` required for any ledger write)
    -> ``--repro`` recompute mode: identical computation in the detached
       reproduction tree, exact-match comparison against the execution
       tree's cell evidence, ZERO ledger writes.

No network access, no S1 access, no tuning, no grids, no threshold changes;
artifacts are written only under the exec tree's gitignored ``results/``
namespace.  Exit codes: 0 ok/published/idempotent-replay, 1 crash,
2 fail-closed preflight (no metric computed), 4 honest refusal recorded
(observation row; the cell consumed its budget), 6 reproduction mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

DRIVER_REPO_ROOT = Path(__file__).resolve().parents[4]

#: Frozen equal-twin staged-manifest digest (strong-host runbook section 4;
#: also recorded in research/control/v12_run/equal_twin_staging.json).
FROZEN_STAGED_MANIFEST_SHA256 = (
    "f855ad9c778f7a8695d6416b1c912efd7ddc353bf70935669504016cbf3c3c40"
)
#: The archive's staged manifest file name (90 data files + this manifest).
STAGED_MANIFEST_NAME = "staged_manifest_.json"
STAGED_FILES_EXPECTED = 90

#: staged_data label -> the staged snapshot subdirectory (archive layout).
STAGED_BARS = "binance_bar_15m"
STAGED_PERP_META = "crypto_perpetual_meta"
STAGED_FUNDING = "funding_scan_2026"
STAGED_OI = "oi_consolidated"

EXIT_OK = 0
EXIT_CRASH = 1
EXIT_FAIL_CLOSED = 2
EXIT_REFUSED = 4
EXIT_REPRO_MISMATCH = 6

FAMILIES = ("oilev_v2", "bab_lowbeta")


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


def validate_args(args: argparse.Namespace) -> Optional[str]:
    """Pure flag-combination validation (reason string, or None when OK)."""
    if args.family not in FAMILIES:
        return f"unknown family {args.family!r}; frozen families are {FAMILIES}"
    if args.publish and args.repro:
        return "--repro must never write; --publish is forbidden with --repro"
    if args.publish and not args.ledger:
        return "--publish requires --ledger (per-family shard ledger)"
    if args.publish and not args.expect_head:
        return (
            "--publish requires --expect-head (the operator must state the "
            "frozen W12R pin; fail-closed)"
        )
    if args.compare_with and not args.repro:
        return "--compare-with is only valid together with --repro"
    return None


# --------------------------------------------------------------------------- #
# Staged snapshot verification (transport integrity chain; E0 re-verified)
# --------------------------------------------------------------------------- #
def verify_staged_snapshot(staged_root: Path, expected_sha256: str) -> dict[str, Any]:
    """Fail-closed staged-data identity check BEFORE any data is loaded.

    The staged manifest file must exist, hash exactly to the expected
    equal-twin digest, and declare exactly the frozen 90-file inventory.
    Per-file hash verification itself is the E0 staging gate; this pin binds
    the run to that verified snapshot.
    """
    manifest_path = staged_root / STAGED_MANIFEST_NAME
    problems: list[str] = []
    if not manifest_path.is_file():
        problems.append(f"staged manifest missing: {manifest_path}")
        measured: Optional[str] = None
        files_count: Optional[int] = None
    else:
        measured = sha256_file(manifest_path)
        if measured != expected_sha256:
            problems.append(
                f"staged manifest sha256 mismatch: measured {measured} "
                f"expected {expected_sha256}"
            )
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            files_count = int(manifest.get("files_count", -1))
            if files_count != STAGED_FILES_EXPECTED:
                problems.append(
                    f"staged manifest files_count {files_count} != {STAGED_FILES_EXPECTED}"
                )
            for label in (STAGED_BARS, STAGED_PERP_META, STAGED_FUNDING, STAGED_OI):
                if not any(key.startswith(f"{label}/") for key in manifest.get("files", {})):
                    problems.append(f"staged manifest carries no {label}/ entries")
            if problems:
                pass
        except ValueError as exc:
            files_count = None
            problems.append(f"staged manifest unreadable: {exc}")
    for label in (STAGED_BARS, STAGED_PERP_META, STAGED_FUNDING, STAGED_OI):
        if not (staged_root / label).is_dir():
            problems.append(f"staged subtree missing: {staged_root / label}")
    return {
        "staged_root": str(staged_root),
        "staged_manifest_sha256": measured,
        "expected_staged_manifest_sha256": expected_sha256,
        "files_count": files_count,
        "problems": problems,
        "ok": not problems,
    }


# --------------------------------------------------------------------------- #
# Settlements reader (byte-semantics mirror of the frozen
# research.v12.families.oilev_v2.audits.load_settlements row mapping; the
# frozen loader resolves its root through Mac-workspace constants, so the
# driver carries the SAME mapping with an explicit root.  Equivalence is
# pinned by tests/test_v12r_driver.py).
# --------------------------------------------------------------------------- #
def load_settlements_root(
    root: Path, symbols: Sequence[str]
) -> dict[str, tuple[dict[str, Any], ...]]:
    out: dict[str, tuple[dict[str, Any], ...]] = {}
    for sym in symbols:
        path = Path(root) / str(sym) / "funding.json"
        if not path.exists():
            out[str(sym)] = ()
            continue
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows = []
        for row in payload.get("rows") or []:
            ts_ms = row.get("fundingTime")
            rate = row.get("fundingRate")
            if ts_ms is None or rate is None:
                raise ValueError(f"{sym}: funding row missing fundingTime/rate")
            rows.append(
                {
                    "publish_ts_ns": int(ts_ms) * 1_000_000,
                    "value": float(rate),
                }
            )
        rows.sort(key=lambda r: r["publish_ts_ns"])
        stamps = [r["publish_ts_ns"] for r in rows]
        if len(set(stamps)) != len(stamps):
            raise ValueError(f"{sym}: duplicate settlement timestamps")
        out[str(sym)] = tuple(rows)
    return out


def _series_digest(rows_by_symbol: Mapping[str, Sequence[Any]]) -> str:
    """Deterministic digest of loaded bar/OI/settlement series (pin input)."""
    digest = hashlib.sha256()
    for sym in sorted(rows_by_symbol):
        for row in rows_by_symbol[sym]:
            if isinstance(row, Mapping):
                fields = [str(k) for k in sorted(row)]
                digest.update(f"{sym}|" + "|".join(f"{k}={row[k]!r}" for k in fields).encode())
            else:  # Bar-like objects: positional frozen fields
                digest.update(
                    f"{sym}|{getattr(row, 'ts_event_ns', None)!r}|"
                    f"{getattr(row, 'open', None)!r}|{getattr(row, 'high', None)!r}|"
                    f"{getattr(row, 'low', None)!r}|{getattr(row, 'close', None)!r}".encode()
                )
    return digest.hexdigest()


# --------------------------------------------------------------------------- #
# BAB catalog shim: read-through junction/symlink from the Nautilus catalog
# layout the frozen loaders expect onto the staged snapshot labels.  No data
# is ever copied; the shim lives under the gitignored results/ namespace.
# --------------------------------------------------------------------------- #
def ensure_catalog_shim(exec_root: Path, staged_root: Path) -> Path:
    shim_data = exec_root / "results" / "_staged_catalog" / "data"
    pairs = {
        "binance_bar": staged_root / STAGED_BARS,
        "crypto_perpetual": staged_root / STAGED_PERP_META,
    }
    for name, target in pairs.items():
        link = shim_data / name
        if link.exists():
            if Path(str(link)).resolve() != Path(str(target)).resolve():
                raise RuntimeError(
                    f"catalog shim {link} does not resolve to {target}; refusing"
                )
            continue
        shim_data.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0 or not link.exists():
                raise RuntimeError(f"mklink /J failed for {link}: {result.stderr}")
        else:
            os.symlink(Path(target), link)
    return shim_data.parent


# --------------------------------------------------------------------------- #
# Frozen family registry: construction ONLY from the frozen V12 modules.
# --------------------------------------------------------------------------- #
def _data_roots(staged_root: Path) -> dict[str, Path]:
    return {
        "bars": staged_root / STAGED_BARS,
        "perp_meta": staged_root / STAGED_PERP_META,
        "funding": staged_root / STAGED_FUNDING,
        "oi": staged_root / STAGED_OI,
    }


def build_oilev(staged_root: Path, arm_id: str) -> tuple[Any, dict[str, Any]]:
    """Frozen OILEV-V2 arm plugin on the staged snapshot (explicit roots)."""
    from research.v12.data_contract import REQUIRED_SYMBOLS
    from research.v12.families.oilev_v2.audits import (
        load_bars_for_plugin,
        load_oi_by_symbol,
        load_tick_sizes,
    )
    from research.v12.families.oilev_v2.plugin import OilevV2Plugin
    from research.v12.families.oilev_v2.strategy import (
        ARM_IDS as OILEV_ARMS,
        BENCHMARK_SYMBOL,
        stamp_calendar,
    )

    if arm_id not in OILEV_ARMS:
        raise ValueError(f"arm {arm_id!r} is not a frozen OILEV-V2 arm")
    roots = _data_roots(staged_root)
    universe = tuple(sorted(set(REQUIRED_SYMBOLS) - {BENCHMARK_SYMBOL}))
    feed_symbols = tuple(sorted(set(universe) | {BENCHMARK_SYMBOL}))
    instants = stamp_calendar()

    oi_all = load_oi_by_symbol(feed_symbols, root=str(roots["oi"]))
    oi = {sym: oi_all[sym] for sym in universe}
    bars = load_bars_for_plugin(feed_symbols, instants, bars_root=str(roots["bars"]))
    settlements = load_settlements_root(roots["funding"], universe)
    tick_sizes = load_tick_sizes(feed_symbols, perp_root=str(roots["perp_meta"]))

    plugin = OilevV2Plugin(
        arm_id=arm_id,
        oi_by_symbol=oi,
        bars_by_symbol=bars,
        settlements_by_symbol=dict(settlements),
        tick_sizes=dict(tick_sizes),
    )
    inputs = {
        "universe": universe,
        "oi_digest": _series_digest(oi),
        "bars_digest": _series_digest(bars),
        "settlements_digest": _series_digest(settlements),
        "tick_sizes": dict(sorted(tick_sizes.items())),
        "bars_per_symbol": {s: len(b) for s, b in sorted(bars.items())},
        "oi_rows_per_symbol": {s: len(v) for s, v in sorted(oi.items())},
        "settlements_per_symbol": {s: len(v) for s, v in sorted(settlements.items())},
        "schedule_instants": len(instants),
    }
    return plugin, inputs


def build_bab(staged_root: Path, arm_id: str, exec_root: Path) -> tuple[Any, dict[str, Any]]:
    """Frozen BAB-LOWBETA arm plugin on the staged snapshot (catalog shim)."""
    from research.v12.families.bab_lowbeta.audits import (
        PREWINDOW_START_ISO,
        STAGED_SYMBOLS,
        load_funding_settlements,
        load_staged_bars,
        load_tick_sizes,
    )
    from research.v12.families.bab_lowbeta.plugin import BabLowBetaPlugin
    from research.v12.families.bab_lowbeta.strategy import (
        ARM_IDS as BAB_ARMS,
        WINDOW_END_ISO,
    )

    if arm_id not in BAB_ARMS:
        raise ValueError(f"arm {arm_id!r} is not a frozen BAB-LOWBETA arm")
    roots = _data_roots(staged_root)
    catalog = ensure_catalog_shim(exec_root, staged_root)

    bars = load_staged_bars(
        catalog_path=str(catalog),
        symbols=STAGED_SYMBOLS,
        start_iso=PREWINDOW_START_ISO,
        end_iso=WINDOW_END_ISO,
    )
    tick_sizes = load_tick_sizes(catalog_path=str(catalog), symbols=STAGED_SYMBOLS)
    settlements = load_funding_settlements(
        funding_root=str(roots["funding"]), symbols=STAGED_SYMBOLS
    )
    plugin = BabLowBetaPlugin(
        arm_id=arm_id,
        bars_by_symbol=bars,
        tick_sizes=tick_sizes,
        settle_points_by_symbol=settlements,
    )
    inputs = {
        "universe": tuple(sorted(set(STAGED_SYMBOLS) - {"BTCUSDT"})),
        "bars_digest": _series_digest(bars),
        "settlements_digest": _series_digest(settlements),
        "tick_sizes": dict(sorted(tick_sizes.items())),
        "bars_per_symbol": {s: len(b) for s, b in sorted(bars.items())},
        "settlements_per_symbol": {s: len(v) for s, v in sorted(settlements.items())},
        "schedule_instants": len(plugin.schedule().instants),
    }
    return plugin, inputs


def family_registry() -> dict[str, dict[str, Any]]:
    """The two frozen V12 families (identities from the frozen modules)."""
    from research.v12.families.bab_lowbeta.plugin import ROLE_BY_ARM as BAB_ROLES
    from research.v12.families.bab_lowbeta.strategy import (
        FAMILY_ID as BAB_FAMILY,
        build_frozen_identity as bab_frozen_identity,
        frozen_arm_config_digest,
        frozen_arm_ids,
    )
    from research.v12.families.oilev_v2.strategy import (
        ARM_ROLES as OILEV_ROLES,
        FAMILY_ID as OILEV_FAMILY,
        frozen_identity as oilev_frozen_identity,
    )
    from research.v11.publication_identity import arm_config_digest

    return {
        "oilev_v2": {
            "family_id": OILEV_FAMILY,
            "arms": tuple(sorted(OILEV_ROLES)),
            "roles": dict(OILEV_ROLES),
            "identity": oilev_frozen_identity,
            "digest": lambda arm_id: arm_config_digest(
                oilev_frozen_identity(arm_id), arm_id=arm_id
            ),
            "build": lambda staged_root, arm_id, exec_root: build_oilev(
                staged_root, arm_id
            ),
        },
        "bab_lowbeta": {
            "family_id": BAB_FAMILY,
            "arms": tuple(sorted(frozen_arm_ids())),
            "roles": dict(BAB_ROLES),
            "identity": bab_frozen_identity,
            "digest": frozen_arm_config_digest,
            "build": lambda staged_root, arm_id, exec_root: build_bab(
                staged_root, arm_id, exec_root
            ),
        },
    }


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


def scored_metrics_from_baseline(baseline_run: Mapping[str, Any]) -> dict[str, Any]:
    """Scored metrics + REAL decision/fill evidence from the baseline cell."""
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
    return {
        "score_valid": all(_finite(metrics.get(k)) for k in REQUIRED_SCORED_FIELDS),
        "net_return_sum": metrics.get("net_return_sum"),
        "expectancy_per_day": metrics.get("expectancy_per_day"),
        "max_drawdown": metrics.get("max_drawdown"),
        "n_positions": len(positions),
        "n_decisions": len(decisions),
        "n_fills": len(fills),
        "decisions": decisions,
        "fills": fills,
    }


def compute_cell(
    *,
    family: str,
    arm_id: str,
    plugin: Any,
    out_dir: Path,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    """Run the frozen family matrix for ONE arm; score the baseline only."""
    from research.adapter_v10.hashes import atomic_write_json, payload_sha256
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
# Reproduction comparison (exact match; volatile metadata excluded)
# --------------------------------------------------------------------------- #
REPRO_COMPARE_FIELDS = (
    "arm_config_digest",
    "staged_manifest_sha256",
    "matrix_digest",
    "matrix_cells",
    "baseline_result_sha256",
    "baseline_hash_portfolio_payload_sha256",
    "baseline_hash_positions_sha256",
    "universe",
    "scored_net_return_sum",
    "scored_expectancy_per_day",
    "scored_max_drawdown",
    "scored_n_positions",
    "scored_n_decisions",
    "scored_n_fills",
    "producer_head_sha",
)


def repro_view(result: Mapping[str, Any], *, staged_sha: str, head: str) -> dict[str, Any]:
    baseline = result["baseline_run"]
    scored = result["scored_metrics"]
    return {
        "arm_config_digest": result["arm_config_digest"],
        "staged_manifest_sha256": staged_sha,
        "matrix_digest": result["matrix_digest"],
        "matrix_cells": list(result["matrix_cells"]),
        "baseline_result_sha256": str(baseline["hashes"]["result_sha256"]),
        "baseline_hash_portfolio_payload_sha256": str(
            baseline["hashes"]["portfolio_payload_sha256"]
        ),
        "baseline_hash_positions_sha256": str(baseline["hashes"]["positions_sha256"]),
        "universe": list(result["universe"]),
        "scored_net_return_sum": scored["net_return_sum"],
        "scored_expectancy_per_day": scored["expectancy_per_day"],
        "scored_max_drawdown": scored["max_drawdown"],
        "scored_n_positions": int(scored["n_positions"]),
        "scored_n_decisions": int(scored["n_decisions"]),
        "scored_n_fills": int(scored["n_fills"]),
        "producer_head_sha": head,
    }


def compare_repro(exec_view: Mapping[str, Any], repro_view_payload: Mapping[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    all_match = True
    for name in REPRO_COMPARE_FIELDS:
        left = exec_view.get(name)
        right = repro_view_payload.get(name)
        match = left == right
        all_match &= match
        fields[name] = {"execution": left, "reproduction": right, "match": bool(match)}
    return {
        "artifact": "v12r_repro_cell_comparison",
        "all_match": bool(all_match),
        "fields": fields,
        "verdict": "ALL_MATCH" if all_match else "MISMATCH",
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--family", required=True, choices=FAMILIES)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--exec-root", default=str(DRIVER_REPO_ROOT))
    parser.add_argument("--staged-root", default=None,
                        help="staged_data snapshot root (default <exec-root>/staged_data)")
    parser.add_argument("--out-root", default=None,
                        help="default <exec-root>/results/v12r_phase_e/<family>/<arm>")
    parser.add_argument("--ledger", default=None,
                        help="per-family shard ledger (required with --publish)")
    parser.add_argument("--publish", action="store_true",
                        help="A1-only: write the exactly-once ledger row")
    parser.add_argument("--repro", action="store_true",
                        help="reproduction recompute; no ledger writes allowed")
    parser.add_argument("--compare-with", default=None,
                        help="execution-tree cell evidence dir to compare against (--repro)")
    parser.add_argument("--expect-head", default=None,
                        help="frozen W12R pin (required with --publish)")
    parser.add_argument("--expect-staged-manifest", default=FROZEN_STAGED_MANIFEST_SHA256)
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:  # noqa: PLR0912
    t_start = time.time()
    args = parse_args(argv)
    reason = validate_args(args)
    if reason:
        print(f"FAIL-CLOSED: {reason}")
        return EXIT_FAIL_CLOSED

    exec_root = Path(args.exec_root).resolve()
    staged_root = (
        Path(args.staged_root).resolve()
        if args.staged_root
        else exec_root / "staged_data"
    )
    out_dir = (
        Path(args.out_root).resolve()
        if args.out_root
        else exec_root / "results" / "v12r_phase_e" / args.family / args.arm
    )
    sys.path.insert(0, str(exec_root))

    # Import-order contract (A7 wave-1 pin convention): the generic adapter
    # is imported before anything that pulls research.v11.publication_identity.
    import research.adapter_v10  # noqa: F401

    registry = family_registry()
    fam = registry[args.family]
    if args.arm not in fam["arms"]:
        print(f"FAIL-CLOSED: arm {args.arm!r} not frozen for {args.family} {fam['arms']}")
        return EXIT_FAIL_CLOSED

    head = git_head(exec_root)
    if args.publish and args.expect_head != head:
        print(
            f"FAIL-CLOSED: exec head {head} != expected pin {args.expect_head}; "
            "no data loaded, no metric computed"
        )
        return EXIT_FAIL_CLOSED

    staged = verify_staged_snapshot(staged_root, args.expect_staged_manifest)
    if not staged["ok"]:
        print("FAIL-CLOSED: staged snapshot verification failed:")
        for problem in staged["problems"]:
            print(f"  - {problem}")
        return EXIT_FAIL_CLOSED

    # Frozen digest equality BEFORE any scored metric can exist.
    digest = fam["digest"](args.arm)
    freeze_path = exec_root / "research" / "control" / "v12_run" / "selection_freeze.json"
    frozen_cells = {
        c["arm_id"]: c
        for c in json.loads(freeze_path.read_text(encoding="utf-8"))["frozen_cells"]
    }
    frozen_digest = frozen_cells[args.arm]["arm_config_digest"]
    if digest != frozen_digest:
        print(
            f"FAIL-CLOSED: arm_config_digest mismatch for {args.arm}: "
            f"module {digest} != freeze {frozen_digest}"
        )
        return EXIT_FAIL_CLOSED

    # Load the staged snapshot through the frozen loaders.
    t_load = time.time()
    plugin, inputs = fam["build"](staged_root, args.arm, exec_root)
    load_seconds = round(time.time() - t_load, 1)
    identity = plugin.identity()
    cost_model = plugin.cost_model()

    preflight = {
        "artifact": "v12r_phase_e_cell_preflight",
        "schema": "v12r.preflight.v1",
        "family": args.family,
        "family_id": fam["family_id"],
        "arm_id": args.arm,
        "role": fam["roles"][args.arm],
        "at_utc": utc_now(),
        "exec_root": str(exec_root),
        "exec_head": head,
        "expect_head": args.expect_head,
        "producer_role": "A1",
        "no_scored_metric_yet": True,
        "staged": staged,
        "arm_config_digest": digest,
        "frozen_arm_config_digest": frozen_digest,
        "digest_matches_freeze": digest == frozen_digest,
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
        "inputs": inputs,
        "input_snapshot_sha256": staged["staged_manifest_sha256"],
        "code_sha256": head,
        "loader_seconds": load_seconds,
        "note": "no scored metric existed when this file was written",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "preflight.json", preflight)
    print(
        "PREFLIGHT",
        json.dumps(
            {
                "family": args.family,
                "arm_id": args.arm,
                "role": preflight["role"],
                "exec_head": head,
                "digest_matches_freeze": preflight["digest_matches_freeze"],
                "staged_manifest_sha256": staged["staged_manifest_sha256"],
            }
        ),
    )
    if args.preflight_only:
        return EXIT_OK

    # Compute the frozen matrix; score the baseline cell only.
    t_compute = time.time()
    result = compute_cell(
        family=args.family,
        arm_id=args.arm,
        plugin=plugin,
        out_dir=out_dir,
    )
    compute_seconds = round(time.time() - t_compute, 1)
    baseline = result["baseline_run"]
    baseline_metrics = {
        "baseline_cell": result["baseline_cell"],
        "metrics": baseline.get("portfolio_metrics") or {},
        "scored_metrics": result["scored_metrics"],
        "hashes": baseline.get("hashes") or {},
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
            {k: result["scored_metrics"][k]
             for k in ("score_valid", "net_return_sum", "expectancy_per_day", "max_drawdown", "n_positions")}
        ),
        f"compute_seconds={compute_seconds}",
    )

    if args.repro:
        exec_dir = Path(args.compare_with).resolve() if args.compare_with else None
        if exec_dir is None or not exec_dir.is_dir():
            print("FAIL-CLOSED: --repro requires --compare-with <execution cell dir>")
            return EXIT_FAIL_CLOSED
        exec_metrics = json.loads((exec_dir / "baseline_metrics.json").read_text(encoding="utf-8"))
        exec_summary = json.loads((exec_dir / "cell_summary.json").read_text(encoding="utf-8"))
        exec_view = repro_view(
            {
                "arm_config_digest": exec_summary["arm_config_digest"],
                "staged_manifest_sha256": exec_summary["staged_manifest_sha256"],
                "matrix_digest": exec_summary["matrix_digest"],
                "matrix_cells": exec_summary["matrix_cells"],
                "baseline_run": {"hashes": exec_metrics["hashes"]},
                "scored_metrics": exec_metrics["scored_metrics"],
                "universe": exec_summary["universe"],
            },
            staged_sha=exec_summary["staged_manifest_sha256"],
            head=exec_summary["producer_head_sha"],
        )
        my_view = repro_view(
            {**result, "arm_config_digest": digest},
            staged_sha=staged["staged_manifest_sha256"],
            head=head,
        )
        report = compare_repro(exec_view, my_view)
        report.update(
            {
                "family": args.family,
                "arm_id": args.arm,
                "execution_dir": str(exec_dir),
                "repro_dir": str(out_dir),
                "at_utc": utc_now(),
            }
        )
        _write_json(out_dir / "repro_report.json", report)
        print("REPRO", report["verdict"])
        return EXIT_OK if report["all_match"] else EXIT_REPRO_MISMATCH

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

    ledger_path = Path(args.ledger).resolve()
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
        "artifact": "v12r_phase_e_cell_summary",
        "family": args.family,
        "family_id": fam["family_id"],
        "arm_id": args.arm,
        "role": fam["roles"][args.arm],
        "at_utc": utc_now(),
        "producer_head_sha": head,
        "arm_config_digest": digest,
        "staged_manifest_sha256": staged["staged_manifest_sha256"],
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
            )
        },
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
        "run_seconds": {"load": load_seconds, "compute": compute_seconds, "total": total_seconds},
    }
    _write_json(out_dir / "cell_summary.json", cell_summary)
    print(
        "PUBLISH",
        json.dumps(
            {
                "stage": publication["stage"],
                "published": publication["published"],
                "reasons": publication["reasons"],
                "observed_delta": publication["observed_delta"],
                "published_delta": publication["published_delta"],
                "denominator_after": after,
            },
            default=str,
        ),
    )
    if publication["stage"] in (STAGE_PUBLISHED, STAGE_IDEMPOTENT_REPLAY):
        return EXIT_OK
    return EXIT_REFUSED


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - the driver reports its own crash
        print(f"CRASH: {type(exc).__name__}: {exc}")
        raise SystemExit(EXIT_CRASH) from exc
