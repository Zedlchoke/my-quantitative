"""V13R Phase E scored-cell driver (A1, strong host; one arm per invocation).

Frozen V12R ``run_v12_cell.py`` pattern, wired to the FROZEN V13 families
``research.v13.families.{oitd,liqepis}`` -- no V12 family logic is imported
and no frozen identity, cost, fold, gate or universe constant is re-declared
here.  Everything family-specific comes from the frozen family
strategy/plugin modules; everything adapter-specific comes from the frozen
generic adapter; publication goes through the frozen V12 accounting entry
point (``research.v12.accounting.publish_v12_cell`` with the A1
serialization lock) -- the SAME primitive the V13 family modules already
use -- into a PER-FAMILY SHARD LEDGER.  The canonical registry file
(``results/registry/experiments_v13.jsonl``) stays the empty W1 seed: shard
ledgers are the scored-row authority (V12R convention).

  preflight pins (written BEFORE any scored metric exists)
    -> read-only staged-data loaders from the exec tree's ``staged_data/``
       snapshot: 90/90 per-file sha256 against the committed
       ``research/audits/v12p/a3_staging_manifest.json`` authority AND
       ``staged_manifest_.json`` byte-identity to the frozen equal-twin
       digest (fail-closed before any data is loaded)
    -> 6/6 frozen arm-config digest equality vs
       ``research/control/v13_run/w13_freeze.json`` (W1 c0d0673), recomputed
       from the frozen identity modules (fail-closed before any compute)
    -> producers read ONLY the staged snapshot under the exec tree's
       ``staged_data/`` (bars=binance_bar_15m, perp meta=crypto_perpetual_meta,
       funding=funding_scan_2026 [OITD cost/mark bundle] + funding_20240820_
       20260821 [staged, unused by the frozen producers], OI=oi_consolidated)
       with the fusion availability semantics the frozen families already
       implement.  Every V13 loader that accepts a root is wired by its own
       parameter; the ONE loader without a root parameter (OITD
       ``load_marks_and_settlements``, which resolves its bundle through the
       frozen ``research.v12.data_contract.FUNDING_BUNDLES`` workspace
       constants) is carried by this driver as a byte-semantics mirror with
       an explicit root -- exactly the V12R ``load_settlements_root``
       precedent -- with equivalence pinned by tests/test_v13r_driver.py.
    -> family stress matrix derived from the frozen folds contract
       (L-V11-1 derivation; never the generic superset)
    -> frozen runner-compatibility pin BEFORE any scored metric exists:
       the frozen generic adapter queries ``targets_at`` at EVERY
       non-final schedule instant of EVERY accepted matrix cell (gap
       instants are carried, never opened), so the loaded plugin must
       answer all of those queries; any refusal fails the run closed
       (exit 2) with the exact cell/instant/refusal recorded -- no matrix
       compute is started on an incompatible frozen plugin/fold pair
    -> every accepted matrix cell run; scored metrics from the BASELINE
       cell only, with real decision/fill evidence records
    -> exactly-once publication through
       :func:`research.v12.accounting.publish_v12_cell` (A1 sole publisher,
       per-family shard ledger, ``--publish`` required for any ledger write)
    -> ``--repro`` recompute mode: identical computation in the detached
       reproduction tree, exact-match comparison against the execution
       tree's cell evidence, ZERO ledger writes.

Frozen-producer data conventions mirrored unchanged (never re-declared):
OITD consumes bars + daily OI + the ``scan_2026`` funding bundle (native
settlements COST ONLY + the ``markPrice`` mark root) + perp-meta tick sizes;
LIQEPIS is BARS-ONLY (no OI, mark or funding field enters any signal) and --
L-V14-0 remediation (V14 P1 A2) -- also consumes the real perp-meta tick
sizes through the SAME canonical ``load_tick_sizes`` loader as OITD (the
V13 driver's uniform ``tick_size 0.01`` stub charged the per-fill
adverse-tick slip ~3-4 orders above the frozen per-fill schedule on
sub-cent symbols; verdict-invariant, adjudicated append-only in
``research/control/v14_run/p1_a2/LIQEPIS_cost_adjudication.json``).

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

#: Frozen equal-twin staged-manifest digest (w13_freeze.json "staging";
#: byte-copy of the V12-verified snapshot, identical in both V13 twins).
FROZEN_STAGED_MANIFEST_SHA256 = (
    "f855ad9c778f7a8695d6416b1c912efd7ddc353bf70935669504016cbf3c3c40"
)
#: The archive's staged manifest file name (90 data files + this manifest).
STAGED_MANIFEST_NAME = "staged_manifest_.json"
STAGED_FILES_EXPECTED = 90
#: The committed per-file sha256 authority the 90 staged files verify against.
A3_STAGING_MANIFEST_RELPATH = (
    "research",
    "audits",
    "v12p",
    "a3_staging_manifest.json",
)
#: The W1 freeze authority for the 6/6 arm-config digest equality pin.
W13_FREEZE_RELPATH = ("research", "control", "v13_run", "w13_freeze.json")

#: staged_data label -> the staged snapshot subdirectory (archive layout).
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

EXIT_OK = 0
EXIT_CRASH = 1
EXIT_FAIL_CLOSED = 2
EXIT_REFUSED = 4
EXIT_REPRO_MISMATCH = 6

FAMILIES = ("liqepis", "oitd")


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
            "frozen W13 pin; fail-closed)"
        )
    if args.compare_with and not args.repro:
        return "--compare-with is only valid together with --repro"
    return None


# --------------------------------------------------------------------------- #
# Staged snapshot verification (transport integrity chain; E0 re-verified)
# --------------------------------------------------------------------------- #
def verify_staged_snapshot(
    staged_root: Path,
    expected_sha256: str,
    authority_files: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Fail-closed staged-data identity check BEFORE any data is loaded.

    The staged manifest file must exist, hash exactly to the frozen
    equal-twin digest, declare exactly the frozen 90-file inventory EQUAL
    to the committed a3 staging-manifest authority, and every one of the
    90 files must be present in the staged tree with the authority sha256.
    """
    manifest_path = staged_root / STAGED_MANIFEST_NAME
    problems: list[str] = []
    measured: Optional[str] = None
    files_count: Optional[int] = None
    files_verified: Optional[int] = None
    if not manifest_path.is_file():
        problems.append(f"staged manifest missing: {manifest_path}")
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
                    f"staged manifest files_count {files_count} "
                    f"!= {STAGED_FILES_EXPECTED}"
                )
            staged_files = manifest.get("files", {})
            if dict(staged_files) != dict(authority_files):
                problems.append(
                    "staged manifest inventory != a3 staging-manifest authority"
                )
            for label in STAGED_LABELS:
                if not any(key.startswith(f"{label}/") for key in staged_files):
                    problems.append(f"staged manifest carries no {label}/ entries")
        except ValueError as exc:
            staged_files = {}
            problems.append(f"staged manifest unreadable: {exc}")
        # 90/90 per-file sha256 vs the committed a3 authority.
        verified = 0
        for rel, expected in sorted(dict(authority_files).items()):
            data_path = staged_root / rel
            if not data_path.is_file():
                problems.append(f"staged file missing: {data_path}")
                continue
            actual = sha256_file(data_path)
            if actual != str(expected.get("sha256", "")):
                problems.append(
                    f"staged file sha256 mismatch: {rel}: measured {actual} "
                    f"expected {expected.get('sha256')}"
                )
                continue
            verified += 1
        files_verified = verified
        if verified != STAGED_FILES_EXPECTED and not any(
            "inventory" in p or "files_count" in p or "unreadable" in p
            for p in problems
        ):
            problems.append(
                f"staged files verified {verified} != {STAGED_FILES_EXPECTED}"
            )
    for label in STAGED_LABELS:
        if not (staged_root / label).is_dir():
            problems.append(f"staged subtree missing: {staged_root / label}")
    return {
        "staged_root": str(staged_root),
        "staged_manifest_sha256": measured,
        "expected_staged_manifest_sha256": expected_sha256,
        "files_count": files_count,
        "files_verified": files_verified,
        "authority_files": len(dict(authority_files)),
        "problems": problems,
        "ok": not problems,
    }


# --------------------------------------------------------------------------- #
# Funding bundle reader (byte-semantics mirror of the frozen
# research.v13.families.oitd.audits.load_marks_and_settlements row mapping;
# the frozen loader resolves its root through the frozen
# research.v12.data_contract.FUNDING_BUNDLES workspace constants, so the
# driver carries the SAME mapping with an explicit root.  Equivalence is
# pinned by tests/test_v13r_driver.py.  NO family file is edited.)
# --------------------------------------------------------------------------- #
def load_marks_and_settlements_root(
    root: Path, symbols: Sequence[str]
) -> tuple[
    dict[str, tuple[tuple[int, float], ...]],
    dict[str, tuple[dict[str, Any], ...]],
]:
    """Marks + native settlements from one funding bundle root (READ-ONLY).

    Marks: the ``markPrice`` field of EVERY native settlement row (the A9-F
    staged mark root); availability = the settlement stamp.  Settlements:
    ``{"publish_ts_ns", "value"}`` rows (COST ONLY inputs).  Identical row
    mapping to the frozen OITD loader, with the root supplied explicitly.
    """
    wanted = [str(s) for s in symbols]
    marks: dict[str, tuple[tuple[int, float], ...]] = {}
    settlements: dict[str, tuple[dict[str, Any], ...]] = {}
    for sym in wanted:
        path = Path(root) / sym / "funding.json"
        if not path.exists():
            marks[sym] = ()
            settlements[sym] = ()
            continue
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        mark_rows: list[tuple[int, float]] = []
        settle_rows: list[dict[str, Any]] = []
        for row in payload.get("rows") or []:
            ts_ms = row.get("fundingTime")
            rate = row.get("fundingRate")
            mark = row.get("markPrice")
            if ts_ms is None or rate is None:
                raise ValueError(f"{sym}: funding row missing fundingTime/rate")
            stamp_ns = int(ts_ms) * 1_000_000
            settle_rows.append({"publish_ts_ns": stamp_ns, "value": float(rate)})
            if mark is None:
                raise ValueError(f"{sym}: funding row missing markPrice (mark root)")
            mark_rows.append((stamp_ns, float(mark)))
        settle_rows.sort(key=lambda r: r["publish_ts_ns"])
        mark_rows.sort(key=lambda r: r[0])
        if len({t for t, _ in mark_rows}) != len(mark_rows):
            raise ValueError(f"{sym}: duplicate mark/settlement stamps")
        marks[sym] = tuple(mark_rows)
        settlements[sym] = tuple(settle_rows)
    return marks, settlements


def _series_digest(rows_by_symbol: Mapping[str, Sequence[Any]]) -> str:
    """Deterministic digest of loaded bar/OI/settlement series (pin input)."""
    digest = hashlib.sha256()
    for sym in sorted(rows_by_symbol):
        for row in rows_by_symbol[sym]:
            if isinstance(row, Mapping):
                fields = [str(k) for k in sorted(row)]
                digest.update(
                    (f"{sym}|" + "|".join(f"{k}={row[k]!r}" for k in fields)).encode()
                )
            else:  # Bar-like objects: positional frozen fields
                digest.update(
                    f"{sym}|{getattr(row, 'ts_event_ns', None)!r}|"
                    f"{getattr(row, 'open', None)!r}|{getattr(row, 'high', None)!r}|"
                    f"{getattr(row, 'low', None)!r}|{getattr(row, 'close', None)!r}".encode()
                )
    return digest.hexdigest()


def fusion_series_digest(series_by_symbol: Mapping[str, Any]) -> str:
    """Deterministic digest of loaded fusion bar series (pin input)."""
    digest = hashlib.sha256()
    for sym in sorted(series_by_symbol):
        series = series_by_symbol[sym]
        digest.update(
            f"{sym}|origin={int(series.origin_ns)}|".encode()
            + series.close.tobytes()
            + series.volume.tobytes()
            + series.available_ns.tobytes()
        )
    return digest.hexdigest()


# --------------------------------------------------------------------------- #
# Frozen family registry: construction ONLY from the frozen V13 modules.
# --------------------------------------------------------------------------- #
def _data_roots(staged_root: Path) -> dict[str, Path]:
    return {
        "bars": staged_root / STAGED_BARS,
        "perp_meta": staged_root / STAGED_PERP_META,
        "funding_scan_2026": staged_root / STAGED_FUNDING_SCAN,
        "funding_20240820_20260821": staged_root / STAGED_FUNDING_LONG,
        "oi": staged_root / STAGED_OI,
    }


def build_oitd(
    staged_root: Path, arm_id: str, exec_root: Optional[Path] = None
) -> tuple[Any, dict[str, Any]]:
    """Frozen OITD arm plugin on the staged snapshot (explicit roots).

    Root-wired mirror of the frozen ``research.v13.families.oitd.audits``
    ``load_snapshot_data`` + ``build_plugins`` -- every loader that accepts
    a root parameter is wired by that parameter; the funding bundle comes
    through :func:`load_marks_and_settlements_root` (the byte-semantics
    mirror above).  No family file is edited and no constant is re-declared.
    """
    from research.v12.families.oilev_v2.audits import load_tick_sizes
    from research.v13.families.oitd.audits import (
        DAY_NS,
        fold_end_instants,
        load_bars_for_plugin,
        load_day_turnover_by_symbol,
        load_oi_by_symbol,
        tradeable_universe_symbols,
    )
    from research.v13.families.oitd.plugin import OitdPlugin
    from research.v13.families.oitd.strategy import (
        ARM_IDS as OITD_ARMS,
        BENCHMARK_SYMBOL,
        CONTROL_ARM,
        stamp_calendar,
    )

    if arm_id not in OITD_ARMS:
        raise ValueError(f"arm {arm_id!r} is not a frozen OITD arm")
    roots = _data_roots(staged_root)
    universe = tradeable_universe_symbols()
    feed_symbols = tuple(sorted(set(universe) | {BENCHMARK_SYMBOL}))
    instants = stamp_calendar()
    fold_ends = fold_end_instants()
    # Turnover span exactly as the frozen load_snapshot_data declares it.
    first_day = int(instants[0]) // DAY_NS
    last_day = int(instants[-1]) // DAY_NS
    margin_days = 1
    day_turnover = load_day_turnover_by_symbol(
        universe,
        bars_root=str(roots["bars"]),
        span_start_day_ns=first_day - 56 - margin_days,
        span_end_day_ns=last_day + margin_days,
    )
    bars = load_bars_for_plugin(
        feed_symbols,
        list(instants) + list(fold_ends),
        bars_root=str(roots["bars"]),
    )
    oi = load_oi_by_symbol(universe, root=str(roots["oi"]))
    marks, settlements = load_marks_and_settlements_root(
        roots["funding_scan_2026"], universe
    )
    tick_sizes = load_tick_sizes(feed_symbols, perp_root=str(roots["perp_meta"]))

    is_control = arm_id == CONTROL_ARM
    plugin = OitdPlugin(
        arm_id=arm_id,
        day_turnover_by_symbol=day_turnover,
        bars_by_symbol=bars,
        oi_by_symbol=None if is_control else oi,
        mark_by_symbol=None if is_control else marks,
        settlements_by_symbol=settlements,
        tick_sizes=tick_sizes,
    )
    inputs = {
        "universe": universe,
        "day_turnover_digest": _series_digest(day_turnover),
        "bars_digest": _series_digest(bars),
        "oi_digest": _series_digest(oi),
        "marks_digest": _series_digest(marks),
        "settlements_digest": _series_digest(settlements),
        "tick_sizes": dict(sorted(tick_sizes.items())),
        "bars_per_symbol": {s: len(b) for s, b in sorted(bars.items())},
        "oi_rows_per_symbol": {s: len(v) for s, v in sorted(oi.items())},
        "marks_per_symbol": {s: len(v) for s, v in sorted(marks.items())},
        "settlements_per_symbol": {
            s: len(v) for s, v in sorted(settlements.items())
        },
        "schedule_instants": len(instants),
        "oi_mark_bundles": None if is_control else "staged (numerator retained)",
    }
    return plugin, inputs


def build_liqepis(
    staged_root: Path, arm_id: str, exec_root: Optional[Path] = None
) -> tuple[Any, dict[str, Any]]:
    """Frozen LIQEPIS arm plugin on the staged snapshot (explicit roots).

    Root-wired mirror of the frozen ``research.v13.families.liqepis.audits``
    ``build_plugins``: the family's loader ``load_fusion_series`` accepts a
    ``bars_root`` parameter wired to the staged bars.  BARS-ONLY family --
    no OI/mark/funding bundle is read by the frozen producer.  L-V14-0
    remediation (V14 P1 A2): tick sizes are the REAL perp-metadata tick
    sizes via the same canonical ``load_tick_sizes`` loader the OITD path
    uses -- the V13 driver's uniform ``tick_size 0.01`` stub inflated the
    per-fill adverse-tick slip ~3-4 orders on sub-cent symbols.  The
    stub remains ONLY in the audit-only ``audits.build_plugins`` (which
    computes no PnL and is never scored).
    """
    from research.v12.families.oilev_v2.audits import load_tick_sizes
    from research.v13.families.liqepis.audits import (
        load_fusion_series,
        tradeable_universe_symbols,
    )
    from research.v13.families.liqepis.plugin import LiqepisPlugin
    from research.v13.families.liqepis.strategy import (
        ARM_IDS as LIQEPIS_ARMS,
        BENCHMARK_SYMBOL,
        DAY_NS,
        FIRST_STAMP_ISO,
        WINDOW_END_ISO,
        parse_iso_utc,
    )

    if arm_id not in LIQEPIS_ARMS:
        raise ValueError(f"arm {arm_id!r} is not a frozen LIQEPIS arm")
    roots = _data_roots(staged_root)
    universe = tradeable_universe_symbols()
    needed = sorted(set(universe) | {BENCHMARK_SYMBOL})
    first_stamp = parse_iso_utc(FIRST_STAMP_ISO)
    series = load_fusion_series(
        needed,
        bars_root=str(roots["bars"]),
        start_ns=first_stamp - 56 * DAY_NS,
        end_ns=parse_iso_utc(WINDOW_END_ISO),
    )
    # L-V14-0 remediation: real per-instrument tick sizes (cost exactly
    # once per fill at the frozen per-fill schedule), never a uniform stub.
    tick_sizes = load_tick_sizes(needed, perp_root=str(roots["perp_meta"]))
    plugin = LiqepisPlugin(
        arm_id=arm_id,
        bars_by_symbol={
            sym: s for sym, s in series.items() if sym in set(needed)
        },
        tick_sizes=tick_sizes,
    )
    inputs = {
        "universe": universe,
        "fusion_bars_digest": fusion_series_digest(series),
        "tick_sizes": dict(sorted(tick_sizes.items())),
        "slots_per_symbol": {
            sym: int(s.close.shape[0]) for sym, s in sorted(series.items())
        },
        "series_origin_ns": {
            sym: int(s.origin_ns) for sym, s in sorted(series.items())
        },
        "schedule_instants": len(plugin.schedule().instants),
        "bundles_read": ["binance_bar_15m (bars-only frozen producer)"],
    }
    return plugin, inputs


def family_registry() -> dict[str, dict[str, Any]]:
    """The two frozen V13 families (identities from the frozen modules)."""
    from research.v11.publication_identity import arm_config_digest
    from research.v13.families.liqepis.frozen_identity import (
        LIQEPIS_ARM_CONFIG_DIGESTS,
        frozen_identity as liqepis_frozen_identity,
    )
    from research.v13.families.liqepis.strategy import (
        ARM_ROLES as LIQEPIS_ROLES,
        FAMILY_ID as LIQEPIS_FAMILY,
    )
    from research.v13.families.oitd.strategy import (
        ARM_ROLES as OITD_ROLES,
        FAMILY_ID as OITD_FAMILY,
        FROZEN_ARM_CONFIG_DIGESTS,
        frozen_identity as oitd_frozen_identity,
    )
    return {
        "oitd": {
            "family_id": OITD_FAMILY,
            "arms": tuple(sorted(OITD_ROLES)),
            "roles": dict(OITD_ROLES),
            "identity": oitd_frozen_identity,
            "recorded_digests": dict(FROZEN_ARM_CONFIG_DIGESTS),
            "digest": lambda arm_id: arm_config_digest(
                oitd_frozen_identity(arm_id), arm_id=arm_id
            ),
            "build": lambda staged_root, arm_id, exec_root=None: build_oitd(
                staged_root, arm_id
            ),
        },
        "liqepis": {
            "family_id": LIQEPIS_FAMILY,
            "arms": tuple(sorted(LIQEPIS_ROLES)),
            "roles": dict(LIQEPIS_ROLES),
            "identity": liqepis_frozen_identity,
            "recorded_digests": dict(LIQEPIS_ARM_CONFIG_DIGESTS),
            "digest": lambda arm_id: arm_config_digest(
                liqepis_frozen_identity(arm_id), arm_id=arm_id
            ),
            "build": lambda staged_root, arm_id, exec_root=None: build_liqepis(
                staged_root, arm_id
            ),
        },
    }


def verify_all_arm_digests(
    registry: Mapping[str, Mapping[str, Any]], freeze_path: Path
) -> dict[str, Any]:
    """6/6 frozen arm-config digest equality vs the W13 freeze (fail-closed).

    Recomputes every arm digest from the frozen identity modules and
    compares against ``w13_freeze.json`` ``arm_config_digests``.  Returns
    the honest report; ``ok`` is False unless ALL SIX frozen arms match.
    Non-arm annotation keys in the freeze mapping (e.g. the recorded
    ``pairwise_unique`` verdict) are reported as extras, never treated as
    arms.
    """
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    frozen_digests = dict(freeze["arm_config_digests"])
    owners = {
        arm: family
        for family, fam in registry.items()
        for arm in fam["arms"]
    }
    report: dict[str, Any] = {"arms": {}, "ok": True}
    for arm in sorted(owners):
        if arm not in frozen_digests:
            report["arms"][arm] = {
                "family": owners[arm],
                "error": "arm not recorded in the W13 freeze",
            }
            report["ok"] = False
            continue
        module_digest = registry[owners[arm]]["digest"](arm)
        freeze_digest = str(frozen_digests[arm])
        match = module_digest == freeze_digest
        report["arms"][arm] = {
            "family": owners[arm],
            "module_digest": module_digest,
            "freeze_digest": freeze_digest,
            "match": bool(match),
        }
        report["ok"] &= bool(match)
    report["n_arms"] = len(report["arms"])
    report["n_match"] = sum(
        1 for v in report["arms"].values() if v.get("match") is True
    )
    report["freeze_extra_keys"] = sorted(set(frozen_digests) - set(owners))
    report["freeze_path"] = str(freeze_path)
    report["w1_sha"] = str(freeze.get("w1_sha", ""))
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

    The frozen generic adapter (``research.adapter_v10.runner``) queries
    ``targets_at`` at EVERY non-final schedule instant of EVERY accepted
    matrix cell and only ever OPENS books at fold-claimed instants (gap
    instants are carried, never opened).  A frozen family plugin that
    refuses any of those mandatory queries cannot traverse the scored
    path at all; this pin proves the compatibility before the matrix
    compute starts and records the exact refusal otherwise.  Schedule
    only: ``targets_at`` computes target books, never PnL -- a run that
    fails this pin has produced NO scored metric.
    """
    from research.adapter_v10.protocol import ContractViolation

    derivation, _contract = derive_contract(plugin)
    open_instants = list(plugin.schedule().instants)[:-1]
    problems: list[dict[str, Any]] = []
    probes = 0
    for cell in derivation.cells:
        universe = plugin.universe(cell.spec)
        for instant in open_instants:
            probes += 1
            try:
                plugin.targets_at(
                    int(instant), universe=universe, stress=cell.spec
                )
            except ContractViolation as exc:
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
        "artifact": "v13r_runner_traversal_pin",
        "schema": "v13r.traversal_pin.v1",
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
        "artifact": "v13r_repro_cell_comparison",
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
                        help="default <exec-root>/results/v13_phase_e/<family>/<arm>")
    parser.add_argument("--ledger", default=None,
                        help="per-family shard ledger (required with --publish)")
    parser.add_argument("--publish", action="store_true",
                        help="A1-only: write the exactly-once ledger row")
    parser.add_argument("--repro", action="store_true",
                        help="reproduction recompute; no ledger writes allowed")
    parser.add_argument("--compare-with", default=None,
                        help="execution-tree cell evidence dir to compare against (--repro)")
    parser.add_argument("--expect-head", default=None,
                        help="frozen W13 pin (required with --publish)")
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
        else exec_root / "results" / "v13_phase_e" / args.family / args.arm
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

    authority_path = exec_root.joinpath(*A3_STAGING_MANIFEST_RELPATH)
    if not authority_path.is_file():
        print(f"FAIL-CLOSED: staging authority missing: {authority_path}")
        return EXIT_FAIL_CLOSED
    authority_files = dict(
        json.loads(authority_path.read_text(encoding="utf-8"))["files"]
    )
    staged = verify_staged_snapshot(staged_root, args.expect_staged_manifest, authority_files)
    if not staged["ok"]:
        print("FAIL-CLOSED: staged snapshot verification failed:")
        for problem in staged["problems"]:
            print(f"  - {problem}")
        return EXIT_FAIL_CLOSED

    # Frozen digest equality (ALL SIX arms) BEFORE any scored metric can exist.
    freeze_path = exec_root.joinpath(*W13_FREEZE_RELPATH)
    if not freeze_path.is_file():
        print(f"FAIL-CLOSED: W13 freeze missing: {freeze_path}")
        return EXIT_FAIL_CLOSED
    digest_report = verify_all_arm_digests(registry, freeze_path)
    digest = fam["digest"](args.arm)
    frozen_digest = str(dict(digest_report["arms"])[args.arm]["freeze_digest"])
    if not digest_report["ok"] or digest != frozen_digest:
        print(
            f"FAIL-CLOSED: arm_config_digest equality vs W13 freeze failed "
            f"({digest_report['n_match']}/{digest_report['n_arms']} match; "
            f"invoked arm {args.arm}: module {digest} != freeze {frozen_digest})"
        )
        return EXIT_FAIL_CLOSED

    # Load the staged snapshot through the frozen loaders (root-wired).
    t_load = time.time()
    plugin, inputs = fam["build"](staged_root, args.arm, exec_root)
    load_seconds = round(time.time() - t_load, 1)
    identity = plugin.identity()
    cost_model = plugin.cost_model()

    # Frozen runner-compatibility pin: BEFORE any scored metric exists, the
    # loaded plugin must answer every query the frozen generic adapter will
    # make.  A refusal here means the scored traversal is impossible for
    # this frozen plugin/fold pair; the run fails closed with the exact
    # cell/instant/refusal recorded (no matrix compute, no metric).
    t_pin = time.time()
    traversal = verify_runner_traversal(plugin)
    pin_seconds = round(time.time() - t_pin, 1)

    preflight = {
        "artifact": "v13r_phase_e_cell_preflight",
        "schema": "v13r.preflight.v1",
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
        "all_arm_digests_match_freeze": digest_report,
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
        "runner_traversal_pin": traversal,
        "input_snapshot_sha256": staged["staged_manifest_sha256"],
        "code_sha256": head,
        "loader_seconds": load_seconds,
        "pin_seconds": pin_seconds,
        "note": "no scored metric existed when this file was written",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "preflight.json", preflight)
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
                "exec_head": head,
                "digest_matches_freeze": preflight["digest_matches_freeze"],
                "staged_manifest_sha256": staged["staged_manifest_sha256"],
                "staged_files_verified": staged["files_verified"],
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
        "artifact": "v13r_phase_e_cell_summary",
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
