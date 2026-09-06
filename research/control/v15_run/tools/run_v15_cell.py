"""V15 scored-cell driver (one arm per invocation; A1-owner-gated).

The proven ``research/control/v14_run/tools/run_v14_cell.py`` driver pattern,
wired to the TWO frozen V15 families ``research.v15.families.elite_size_asym``
(A5-V15-F1-ELITE-SIZE-ASYM) and ``research.v15.families.taker_sat``
(A6-V15-F1-TAKER-SAT).  No family logic is re-declared here: every
family-specific constant comes from the frozen family packages, publication
goes through the frozen V12 accounting entry point
(``research.v12.accounting.publish_v12_cell``) into a PER-FAMILY shard
ledger, and the generic identity/digest machinery comes from
``research.v11.publication_identity`` (the V14 convention).

The six frozen arms (``research/control/v15_run/selection_freeze_v15.json``):

  elite_size_asym : A5-F1-ANCHOR-ASYM      (anchor)
                    A5-F1-NEIGHBOR         (neighbour)
                    A5-F1-CTL-ELITELEVEL   (causal negative control)
  taker_sat       : A6-F1-ANCHOR-SAT       (anchor)
                    A6-F1-NEIGHBOR         (neighbour)
                    A6-F1-CTL-RAWSAT       (causal negative control)

V15 driver obligations (the V14 set carried forward):

  * ``--data-root`` defaults to the family ``staged_root.json`` value (the
    machine-local staged parquet root the family loaders verify); the driver
    verifies the COMMITTED staging authority
    (``research/control/v15_run/staging/staging_report.json``): its
    ``STAGING_OVERALL`` must read ``PASS`` or ``PASS_UNDER_AMENDMENT_1`` and
    its ``parquet_sha256`` block must match the actual parquet files under
    the data root -- fail-closed per file, BEFORE any family load;
  * preflight BEFORE any metric: six-arm digest pin (every arm-config digest
    recomputed from the frozen identity modules == recorded, pairwise unique
    across all six), the family spec-authority sha256 pins (elite
    ``verify_spec_sha256s`` / taker ``verify_pinned_authorities``), the code
    head pin (``--publish`` requires ``--expect-head == git HEAD``), and the
    mode block (``--dry-run`` refuses ``--publish``/``--ledger`` and
    requires an explicit scratch ``--out-root``; ``--tick-sizes-json`` is a
    synthetic-only wiring and is refused without ``--dry-run``);
  * scored-flag ownership: the family runners are invoked with
    ``scored=True`` ONLY in real mode AFTER every pin above passed.  The
    frozen taker runner REFUSES ``scored=True`` inside the lane
    (``ScoredExecutionForbidden``): a real taker scored invocation therefore
    TECHABORTs (exit 1) until the owner-side family delta lifts that guard
    -- the driver NEVER bypasses a family refusal, and ``--dry-run`` always
    invokes the runners with ``scored=False`` on the synthetic root (their
    own test convention);
  * runner non-vacuity precondition: the cell dict must carry the family
    refusal-registry digest, ``n_decisions > 0`` AND ``n_fills > 0`` -- a
    zero-decision pass is a FAILED run (exit 2, recorded, never published);
    the driver also re-asserts the L-V14-0 ``cost_holding_terms == 0``;
  * scored records carry the frozen stage-A margin-to-fail scaffolding
    (p3_freeze_v15: expectancy 0, PF 1.10, largest fold-positive share
    0.50, largest symbol positive-PnL share 0.70, MDD 0.20) -- the signed
    distance per gate where the input exists; a missing input records the
    field ABSENT, never inferred;
  * publication: ``publish_v12_cell`` exactly-once with the family frozen
    identity ``arm_config_digest``; ``cell_summary.json`` +
    ``publish_record.json`` + ``baseline_metrics.json`` per the V14 layout
    under ``results/v15_phase_e/<family>/<arm>``; denominator before/after
    recorded; an exact replay is the frozen ``IDEMPOTENT_REPLAY_SKIPPED``
    stage with ZERO denominator delta;
  * TECHABORT discipline (V12R/V13R/V14 precedent): any crash BEFORE the
    exactly-once ledger decision writes ``TECHABORT_<arm>.json`` with the
    phase, crash evidence, honest ledger state and ZERO budget effect, then
    exits 1.  The sink is REAL-scoring-time only: real runs default to
    ``<exec-root>/research/control/v15_run`` (override ``--techabort-dir``),
    ``--dry-run`` runs default to ``<out-root>/TECHABORT`` inside the
    mandatory scratch tree and REFUSE any sink under a ``research/control``
    subtree.  Fixes are driver-only; frozen bytes are never edited.

Exit codes: 0 ok/published/idempotent-replay, 1 crash (TECHABORT written),
2 fail-closed preflight or failed non-vacuity postcondition (no metric
published), 4 honest publication refusal recorded (OBSERVATION row; the
trial consumed its budget).
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

#: The committed staging authority (relative to the exec root): the
#: ``STAGING_OVERALL`` verdict plus the per-file ``parquet_sha256`` block
#: the driver verifies against the actual data root before any family load.
STAGING_AUTHORITY_RELPATH = (
    "research",
    "control",
    "v15_run",
    "staging",
    "staging_report.json",
)
#: Accepted committed staging verdicts (fail-closed otherwise).
STAGING_OVERALL_ACCEPTED = ("PASS", "PASS_UNDER_AMENDMENT_1")

#: TECHABORT default sink for REAL scored runs: the designated exec root's
#: V15 control tree.  Synthetic runs sink only inside the scratch out-root
#: and never under a ``research/control`` subtree (forensic files are
#: written at real scoring time only -- the V14 stray-forensics fix).
TECHABORT_REAL_DIR_RELPATH = ("research", "control", "v15_run")

EXIT_OK = 0
EXIT_CRASH = 1
EXIT_FAIL_CLOSED = 2
EXIT_REFUSED = 4

FAMILIES = ("elite_size_asym", "taker_sat")

#: Frozen stage-A gate thresholds (p3_freeze_v15.json
#: ``stage_a_gates_frozen`` V13/V14 set, unchanged; the driver records the
#: margin-to-fail per gate, never a gate verdict -- verdicts are the
#: scoring lane's, computed ex post on scored evidence).
STAGE_A_THRESHOLDS: dict[str, float] = {
    "expectancy_per_day": 0.0,  # gate: after-cost expectancy > 0
    "position_pf": 1.10,  # gate: position PF >= 1.10
    "largest_fold_positive_share": 0.50,  # gate: largest share <= 0.50
    "largest_symbol_positive_pnl_share": 0.70,  # gate: largest share <= 0.70
    "max_drawdown": 0.20,  # gate: MDD <= 0.20
}

#: RECORDED ``arm_config_digest`` per A5-V15-F1 arm, pinned at driver
#: implementation time BEFORE any scored metric exists for any V15 cell
#: (the frozen implementation-lane convention; the taker family carries its
#: own identical record inside ``taker_sat.frozen_identity``).  Recomputed
#: from the frozen elite identity modules and compared fail-closed on every
#: run; pairwise uniqueness across all six arms is asserted at DRIVER level.
ELITE_ARM_CONFIG_DIGESTS_RECORDED: dict[str, str] = {
    "A5-F1-ANCHOR-ASYM": (
        "f859de1e6e106efa1a9abb5f99e16ebf292ceba52cc66308c5f6af8670787068"
    ),
    "A5-F1-NEIGHBOR": (
        "d0106aac2fe58ac866c85a84df5cd8283c043aace84a467591e4fee5e19fa854"
    ),
    "A5-F1-CTL-ELITELEVEL": (
        "7da93a7a358ffb86236d770637c73ff457509fb829117b247ed3e0851a47aa00"
    ),
}


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
    """True iff the sink lies under a ``research/control`` subtree."""
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
    if args.tick_sizes_json and not args.dry_run:
        return (
            "--tick-sizes-json is a synthetic dry-run wiring only (real runs "
            "use the frozen family tick-size loader); refused without --dry-run"
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
# Frozen family registry: construction ONLY from the frozen V15 modules.
# --------------------------------------------------------------------------- #
def elite_identity(arm_id: str) -> Any:
    """Frozen V15 identity of one elite arm, built from the frozen modules.

    The elite family package pins its spec through
    ``elite_size_asym.frozen_identity`` (constants + authority sha256 pins)
    and the per-arm ``ArmSpec`` registry (``elite_size_asym.arms``); this
    builder serializes EXACTLY those frozen bytes into a
    ``StrategyIdentity`` for the generic digest/publication machinery.  No
    value is invented: every field is quoted from a frozen module.
    """
    from importlib import import_module

    from research.adapter_v10.protocol import StrategyIdentity

    elite = import_module(
        "research.v15.families.elite_size_asym.frozen_identity"
    )
    elite_arms = import_module("research.v15.families.elite_size_asym.arms")

    spec = elite_arms.arm_spec(arm_id)  # raises on a non-frozen arm
    return StrategyIdentity(
        strategy_id=elite.STRATEGY_ID,
        family_id=elite.FAMILY_ID,
        arm_config_id=spec.name,
        direction="long_short",
        window_start_iso=elite.WINDOW_START_ISO,
        window_end_iso=elite.WINDOW_END_ISO,
        benchmark_symbols_excluded=(),
        funding_sign_convention="LONG_PAYS_POSITIVE_RATE",
        matrix_cohort_hint="v15",
        arm_id=str(arm_id),
        config={
            "arm_name": spec.name,
            "role": spec.role,
            "feature": spec.feature,
            "window_lookback_days": spec.window_lookback_days,
            "book_side_fraction": spec.book_spec.side_fraction,
            "side_gross": elite.SIDE_GROSS,
            "weight_cap_signed": elite.WEIGHT_CAP_SIGNED,
            "gross_max": elite.GROSS_MAX,
            "min_trade_delta": elite.MIN_TRADE_DELTA,
            "tie_break": elite.TIE_BREAK,
            "direction_statement": spec.direction_statement,
            "universe": list(elite.UNIVERSE),
            "folds": [dict(fold) for fold in elite.FOLDS],
            "purge_days": list(elite.PURGE_DAYS),
            "measured_bound_lag_days": elite.MEASURED_BOUND_LAG_DAYS,
            "window_hole_max_fraction": elite.WINDOW_HOLE_MAX_FRACTION,
            "taker_fee_bps": elite.TAKER_FEE_BPS,
            "slippage_ticks": elite.SLIPPAGE_TICKS,
            "stress_tiers": list(elite.STRESS_TIERS),
            "funding_rate_abs_bound": elite.FUNDING_RATE_ABS_BOUND,
        },
    )


def _staged_root_json_value(family: str, key: str) -> Any:
    path = (
        DRIVER_REPO_ROOT
        / "research"
        / "v15"
        / "families"
        / family
        / "staged_root.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload[key]


def _default_data_root(family: str) -> str:
    return str(_staged_root_json_value(family, "data_root"))


def family_registry() -> dict[str, dict[str, Any]]:
    """The two frozen V15 families (identities from the frozen modules)."""
    # NOTE: import_module (not ``from package import submodule``) -- the
    # taker package __init__ re-exports a FUNCTION named ``frozen_identity``,
    # which would shadow the submodule attribute.
    from importlib import import_module

    elite_frozen = import_module(
        "research.v15.families.elite_size_asym.frozen_identity"
    )
    elite_runner = import_module("research.v15.families.elite_size_asym.runner")
    taker_frozen = import_module(
        "research.v15.families.taker_sat.frozen_identity"
    )
    taker_runner = import_module("research.v15.families.taker_sat.runner")

    def elite_largest_symbol_share(cell: Mapping[str, Any]) -> Optional[float]:
        shares = dict(
            ((cell.get("per_symbol_pnl") or {}).get("positive_shares")) or {}
        )
        return max(shares.values()) if shares else None

    def taker_largest_symbol_share(cell: Mapping[str, Any]) -> Optional[float]:
        shares = dict(
            ((cell.get("per_symbol") or {}).get("positive_pnl_share_by_symbol"))
            or {}
        )
        positives = [float(v) for v in shares.values() if float(v) > 0.0]
        return max(positives) if positives else None

    return {
        "elite_size_asym": {
            "family_id": elite_frozen.FAMILY_ID,
            "strategy_id": elite_frozen.STRATEGY_ID,
            "arms": tuple(sorted(elite_frozen.ARM_ROLES)),
            "roles": dict(elite_frozen.ARM_ROLES),
            "identity": elite_identity,
            "digest": lambda arm_id: _arm_config_digest(elite_identity(arm_id), arm_id),
            "recorded_digests": dict(ELITE_ARM_CONFIG_DIGESTS_RECORDED),
            "run_arm": elite_runner.run_arm,
            "verify_authorities": lambda: elite_frozen.verify_spec_sha256s(
                DRIVER_REPO_ROOT
            ),
            "default_data_root": _default_data_root("elite_size_asym"),
            "refusal_digest": lambda cell: str(
                ((cell.get("refusal_registry") or {}).get("digest")) or ""
            ),
            "largest_symbol_positive_share": elite_largest_symbol_share,
            "baseline_stress_signature": {
                "artifact": "v15_phase_e_baseline_cell",
                "family": "elite_size_asym",
                "stress_tier": "baseline",
            },
            "scored_refusal_note": (
                "the elite runner records the scored flag verbatim; scored "
                "execution itself remains A1-owner-gated through this driver"
            ),
        },
        "taker_sat": {
            "family_id": taker_frozen.FAMILY_ID,
            "strategy_id": taker_frozen.STRATEGY_ID,
            "arms": tuple(sorted(taker_frozen.ARM_ROLES)),
            "roles": dict(taker_frozen.ARM_ROLES),
            "identity": taker_frozen.frozen_identity,
            "digest": lambda arm_id: _arm_config_digest(
                taker_frozen.frozen_identity(arm_id), arm_id
            ),
            "recorded_digests": dict(taker_frozen.TAKER_SAT_ARM_CONFIG_DIGESTS),
            "run_arm": taker_runner.run_arm,
            "verify_authorities": taker_frozen.verify_pinned_authorities,
            "default_data_root": _default_data_root("taker_sat"),
            "refusal_digest": lambda cell: str(
                ((cell.get("refusals") or {}).get("digest")) or ""
            ),
            "largest_symbol_positive_share": taker_largest_symbol_share,
            "baseline_stress_signature": {
                "artifact": "v15_phase_e_baseline_cell",
                "family": "taker_sat",
                "stress_tier": "base",
            },
            "scored_refusal_note": (
                "the frozen taker runner REFUSES run_arm(scored=True) inside "
                "the lane (ScoredExecutionForbidden); a real scored taker "
                "invocation TECHABORTs until the owner-side family delta "
                "lifts the guard -- this driver never bypasses a family "
                "refusal"
            ),
        },
    }


def _arm_config_digest(identity: Any, arm_id: str) -> str:
    from research.v11.publication_identity import arm_config_digest

    return str(arm_config_digest(identity, arm_id=str(arm_id)))


def verify_all_arm_digests(
    registry: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """Six-arm digest pin: recomputed == recorded + pairwise uniqueness.

    Recomputes every frozen arm digest from the frozen identity modules,
    compares against the digests RECORDED before any scored metric existed
    (the taker family's own frozen record; the elite family's record pinned
    in this driver), and asserts at DRIVER level that the six exact digests
    are pairwise unique.  ``ok`` is True only when all six match AND all are
    pairwise distinct.
    """
    report: dict[str, Any] = {"arms": {}, "ok": True}
    all_digests: list[str] = []
    for family, fam in registry.items():
        for arm in fam["arms"]:
            module_digest = str(fam["digest"](arm))
            recorded = str(fam["recorded_digests"].get(arm, ""))
            match = bool(recorded) and module_digest == recorded
            report["arms"][arm] = {
                "family": family,
                "module_digest": module_digest,
                "recorded_digest": recorded,
                "match": match,
            }
            report["ok"] &= match
            all_digests.append(module_digest)
    report["n_arms"] = len(all_digests)
    report["n_match"] = sum(
        1 for entry in report["arms"].values() if entry.get("match") is True
    )
    collisions = sorted({d for d in all_digests if all_digests.count(d) > 1})
    report["pairwise_unique"] = not collisions and len(all_digests) == 6
    report["collisions"] = collisions
    report["ok"] &= report["pairwise_unique"]
    return report


# --------------------------------------------------------------------------- #
# Staged-data authority verification (per-file parquet sha256; fail closed)
# --------------------------------------------------------------------------- #
DATA_SUBTREES = ("metrics", "klines", "funding")


def verify_staging_authority(
    data_root: Path, report_path: Path
) -> dict[str, Any]:
    """Fail-closed verification of the committed staging authority.

    The report's ``STAGING_OVERALL`` must read ``PASS`` or
    ``PASS_UNDER_AMENDMENT_1`` and every ``parquet_sha256`` entry must match
    the actual file under the data root (a mismatch or a missing file fails
    the WHOLE run closed -- per-file, before any family load).
    """
    problems: list[str] = []
    overall: Optional[str] = None
    files_expected = 0
    files_verified = 0
    report_sha: Optional[str] = None
    if not Path(report_path).is_file():
        problems.append(f"staging authority missing: {report_path}")
    else:
        report_sha = sha256_file(Path(report_path))
        try:
            report = json.loads(Path(report_path).read_text(encoding="utf-8"))
        except ValueError as exc:
            problems.append(f"staging authority unreadable: {exc}")
            report = {}
        overall = report.get("STAGING_OVERALL") or (report.get("gates") or {}).get(
            "STAGING_OVERALL"
        )
        if overall not in STAGING_OVERALL_ACCEPTED:
            problems.append(
                f"STAGING_OVERALL {overall!r} not in "
                f"{list(STAGING_OVERALL_ACCEPTED)}"
            )
        files = dict(report.get("parquet_sha256") or {})
        files_expected = len(files)
        if files_expected == 0:
            problems.append("staging authority parquet_sha256 block missing/empty")
        for rel, expected in sorted(files.items()):
            data_path = Path(data_root) / str(rel)
            if not data_path.is_file():
                problems.append(f"staged parquet missing: {rel}")
                continue
            if sha256_file(data_path) != str(expected):
                problems.append(f"staged parquet sha256 mismatch: {rel}")
                continue
            files_verified += 1
    for subtree in DATA_SUBTREES:
        if not (Path(data_root) / subtree).is_dir():
            problems.append(f"data subtree missing: {Path(data_root) / subtree}")
    return {
        "artifact": "v15_phase_e_staging_verification",
        "data_root": str(data_root),
        "staging_report": str(report_path),
        "staging_report_sha256": report_sha,
        "staging_overall": overall,
        "files_expected": files_expected,
        "files_verified": files_verified,
        "problems": problems,
        "ok": not problems,
    }


def verify_synthetic_data_root(data_root: Path) -> dict[str, Any]:
    """Dry-run self-verification of a synthetic tree (subtrees + non-empty)."""
    problems: list[str] = []
    for subtree in DATA_SUBTREES:
        subtree_dir = Path(data_root) / subtree
        if not subtree_dir.is_dir():
            problems.append(f"data subtree missing: {subtree_dir}")
        elif not any(subtree_dir.glob("*.parquet")):
            problems.append(f"data subtree empty: {subtree_dir}")
    return {
        "artifact": "v15_phase_e_staging_verification",
        "mode": "synthetic_self_verified",
        "data_root": str(data_root),
        "staging_report": None,
        "staging_report_sha256": None,
        "staging_overall": None,
        "files_expected": 0,
        "files_verified": 0,
        "problems": problems,
        "ok": not problems,
    }


def verify_family_authorities(family: str) -> dict[str, Any]:
    """The frozen spec-authority sha256 pins of ONE family (fail closed)."""
    fam = family_registry()[family]
    try:
        report = dict(fam["verify_authorities"]())
        ok = True
        error = None
    except Exception as exc:  # noqa: BLE001 - reported fail-closed, not raised
        report = {}
        ok = False
        error = f"{type(exc).__name__}: {exc}"
    return {"family": family, "ok": ok, "error": error, "pins": report}


# --------------------------------------------------------------------------- #
# Scored-record obligations (driver-side, family-independent)
# --------------------------------------------------------------------------- #
def _largest_fold_positive_share(cell: Mapping[str, Any]) -> Optional[float]:
    """Largest positive fold net over the positive-fold pool (or None when
    no fold is positive -- the share is undefined, never inferred)."""
    sums = dict(((cell.get("fold_signs") or {}).get("fold_net_sums")) or {})
    positives = [float(v) for v in sums.values() if float(v) > 0.0]
    if not positives:
        return None
    pool = math.fsum(positives)
    if pool <= 0.0:
        return None
    return max(positives) / pool


def compute_margin_to_fail(
    cell: Mapping[str, Any], fam: Mapping[str, Any]
) -> dict[str, Any]:
    """Frozen stage-A margin-to-fail scaffolding (p3_freeze_v15).

    ``margin = signed distance from the failure threshold``: for lower-bound
    gates (expectancy > 0, PF >= 1.10) ``value - threshold``; for upper-bound
    gates (fold/symbol concentration shares, MDD) ``threshold - value``.
    Positive margin == distance from failing on the passing side.  A gate
    whose input the cell does not carry (or whose share is undefined because
    its positive pool is empty) records the field ABSENT -- never inferred.
    """
    scored = dict(cell.get("scored_metrics") or {})
    margins: dict[str, float] = {}
    absent: list[str] = []

    def lower_bound(name: str, value: Any) -> None:
        if value is None:
            absent.append(name)
        else:
            margins[name] = round(float(value) - STAGE_A_THRESHOLDS[name], 12)

    def upper_bound(name: str, value: Any) -> None:
        if value is None:
            absent.append(name)
        else:
            margins[name] = round(STAGE_A_THRESHOLDS[name] - float(value), 12)

    lower_bound("expectancy_per_day", scored.get("expectancy_per_day"))
    lower_bound("position_pf", scored.get("position_pf"))
    upper_bound(
        "largest_fold_positive_share", _largest_fold_positive_share(cell)
    )
    upper_bound(
        "largest_symbol_positive_pnl_share",
        fam["largest_symbol_positive_share"](cell),
    )
    upper_bound("max_drawdown", scored.get("max_drawdown"))
    return {
        "authority": (
            "p3_freeze_v15.json stage_a_gates_frozen + margin_to_fail_scaffolding"
        ),
        "convention": (
            "margin = signed distance from the failure threshold; positive "
            "= passing side; lower-bound gates use value - threshold, "
            "upper-bound gates threshold - value"
        ),
        "thresholds": dict(sorted(STAGE_A_THRESHOLDS.items())),
        "margins": dict(sorted(margins.items())),
        "absent_inputs": sorted(absent),
    }


def nonvacuity_problems(
    cell: Mapping[str, Any], fam: Mapping[str, Any]
) -> list[str]:
    """Runner non-vacuity + L-V14-0 postconditions (empty list == OK).

    The cell must carry the family refusal-registry digest,
    ``n_decisions > 0``, ``n_fills > 0`` (a zero-decision pass is a FAILED
    run) and ``cost_holding_terms == 0.0`` (the remediated cost-once kernel
    charges on fills only, by construction).
    """
    scored = dict(cell.get("scored_metrics") or {})
    problems: list[str] = []
    if not fam["refusal_digest"](cell):
        problems.append("refusal-registry digest missing from the cell dict")
    for counter in ("n_decisions", "n_fills"):
        value = scored.get(counter)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            problems.append(
                f"non-vacuity failed: scored_metrics.{counter}={value!r} "
                "(a zero-decision pass is a FAILED run)"
            )
    holding = scored.get("cost_holding_terms")
    if holding is None or float(holding) != 0.0:
        problems.append(
            f"L-V14-0 failed: cost_holding_terms={holding!r} must be exactly "
            "0.0 by construction (cost-once kernel)"
        )
    return problems


def publish_scored_cell(
    *,
    family: str,
    arm_id: str,
    cell: Mapping[str, Any],
    ledger_path: Path,
    head: str,
) -> dict[str, Any]:
    """Exactly-once V12 publication of ONE scored V15 cell (importable).

    Calls the frozen ``research.v12.accounting.publish_v12_cell`` with the
    family frozen identity ``arm_config_digest`` and the driver's canonical
    baseline stress signature; records the denominator before/after.  An
    exact replay returns the frozen ``IDEMPOTENT_REPLAY_SKIPPED`` stage with
    ZERO denominator delta.
    """
    from research.v12.accounting import (
        publish_v12_cell,
        v12_denominator_view,
    )

    fam = family_registry()[family]
    identity = fam["identity"](arm_id)
    before = v12_denominator_view(ledger_path)
    publication = publish_v12_cell(
        strategy_id=fam["strategy_id"],
        family=fam["family_id"],
        arm_id=str(arm_id),
        arm_config_digest=fam["digest"](arm_id),
        stress_signature=dict(fam["baseline_stress_signature"]),
        window_start_iso=identity.window_start_iso,
        window_end_iso=identity.window_end_iso,
        scored_metrics=dict(cell["scored_metrics"]),
        result_sha256=str(cell["hashes"]["result_sha256"]),
        ledger_path=ledger_path,
        family_contract_cells=None,
        producer_head_sha=head,
    )
    after = v12_denominator_view(ledger_path)
    return {
        "publication": publication,
        "denominator_before": before,
        "denominator_after": after,
    }


# --------------------------------------------------------------------------- #
# TECHABORT (pre-ledger crash forensics; V12R/V13R/V14 precedent)
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
    was resolved fail-closed by ``main`` (real runs: the V15 control tree;
    synthetic runs: inside the scratch out-root, never under a
    ``research/control`` subtree).  The fix path is DRIVER-ONLY: frozen
    family/accounting bytes are never edited.
    """
    ledger_state: dict[str, Any] = {
        "ledger_path": str(ledger_path) if ledger_path else None,
        "ledger_exists": bool(ledger_path and Path(ledger_path).is_file()),
    }
    if ledger_state["ledger_exists"]:
        try:
            from research.v12.accounting import read_v12_ledger

            ledger_state["ledger_sha256"] = read_v12_ledger(Path(ledger_path))[
                "sha256"
            ]
        except Exception as ledger_exc:  # noqa: BLE001 - forensic must not crash
            ledger_state["ledger_read_error"] = str(ledger_exc)
    payload = {
        "schema": "v15_driver_techabort_forensic_v1",
        "generated_utc": utc_now(),
        "producer_role": "A1",
        "artifact": f"TECHABORT_{arm_id}",
        "cycle": "CRYPTO-V15",
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
            "PLAN_crypto 15)"
            if not scored_metric_computed and not ledger_state["ledger_exists"]
            else "NO LEDGER WRITE COMPLETED (crash before the exactly-once "
            "publication decision); cell artifacts partial; see ledger_state"
        ),
        "out_dir": str(out_dir) if out_dir else None,
        "preflight_artifact": str(preflight_path) if preflight_path else None,
        "fix_path": (
            "driver-only: diagnose and fix research/control/v15_run/tools/"
            "run_v15_cell.py (or its test); frozen family/accounting bytes "
            "are never edited; re-run the same arm invocation after the fix"
        ),
    }
    path = Path(techabort_dir) / f"TECHABORT_{arm_id}.json"
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
        "--data-root",
        default=None,
        help=(
            "staged parquet root (default: the family staged_root.json "
            "data_root, which the family loaders verify)"
        ),
    )
    parser.add_argument(
        "--staging-report",
        default=None,
        help=(
            "staging authority report (default: the committed "
            "research/control/v15_run/staging/staging_report.json; a "
            "synthetic dry-run may point it at a self-consistency copy)"
        ),
    )
    parser.add_argument(
        "--out-root",
        default=None,
        help="default <exec-root>/results/v15_phase_e/<family>/<arm>",
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
        help="frozen pin (required with --publish; must equal git HEAD)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "synthetic full-path exercise (scored=False): no scored ledger "
            "can be written; requires an explicit scratch --out-root"
        ),
    )
    parser.add_argument(
        "--tick-sizes-json",
        default=None,
        help=(
            "synthetic-only per-symbol tick-size map "
            "(refused without --dry-run; real runs use the frozen family "
            "tick-size loader)"
        ),
    )
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument(
        "--techabort-dir",
        default=None,
        help=(
            "forensic dir for TECHABORT_<arm>.json (real runs default to "
            "<exec-root>/research/control/v15_run; --dry-run defaults to "
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
    out_dir = (
        Path(args.out_root).resolve()
        if args.out_root
        else exec_root / "results" / "v15_phase_e" / args.family / args.arm
    )
    # TECHABORT sink discipline: an explicit --techabort-dir wins; otherwise
    # synthetic runs sink into the mandatory scratch out-root and REAL runs
    # sink into the designated exec root's V15 control tree.  A synthetic run
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
    staging_report = (
        Path(args.staging_report).resolve() if args.staging_report else None
    )
    tick_sizes: Optional[dict[str, float]] = None
    if args.tick_sizes_json:
        raw = json.loads(Path(args.tick_sizes_json).read_text(encoding="utf-8"))
        tick_sizes = {str(sym): float(tick) for sym, tick in dict(raw).items()}
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
    data_root = Path(args.data_root).resolve() if args.data_root else Path(
        fam["default_data_root"]
    )

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

        # ---- family spec-authority sha256 pins (fail closed) ---- #
        authorities = verify_family_authorities(args.family)
        if not authorities["ok"]:
            print(
                "FAIL-CLOSED: frozen spec-authority pin failed for "
                f"{args.family}: {authorities['error']}"
            )
            return EXIT_FAIL_CLOSED

        # ---- staged-data authority verification (BEFORE any load) ---- #
        if synthetic and staging_report is None:
            staged = verify_synthetic_data_root(data_root)
        else:
            if staging_report is None:
                staging_report = exec_root.joinpath(*STAGING_AUTHORITY_RELPATH)
            staged = verify_staging_authority(data_root, staging_report)
        if not staged["ok"]:
            print("FAIL-CLOSED: staged-data verification failed:")
            for problem in staged["problems"]:
                print(f"  - {problem}")
            return EXIT_FAIL_CLOSED

        scored_flag_wiring = not synthetic
        preflight = {
            "artifact": "v15_phase_e_cell_preflight",
            "schema": "v15.preflight.v1",
            "cycle": "CRYPTO-V15",
            "family": args.family,
            "family_id": fam["family_id"],
            "arm_id": args.arm,
            "role": fam["roles"][args.arm],
            "at_utc": utc_now(),
            "exec_root": str(exec_root),
            "exec_head": head,
            "expect_head": args.expect_head,
            "producer_role": "A1",
            "mode": "synthetic_dry_run" if synthetic else "real",
            "no_scored_metric_yet": True,
            "scored_flag_wiring": {
                "family_run_arm_scored": scored_flag_wiring,
                "note": fam["scored_refusal_note"],
            },
            "six_arm_digest_pin": digest_report,
            "arm_config_digest": digest,
            "strategy_id": fam["strategy_id"],
            "staged": staged,
            "spec_authority_pins": authorities["pins"],
            "data_root": str(data_root),
            "data_root_default": args.data_root is None,
            "code_sha256": head,
            "remediated_kernel": True,
            "note": "no scored metric existed when this file was written",
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        preflight_path = out_dir / "preflight.json"
        _write_json(preflight_path, preflight)
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

        # ---- run the frozen family arm (scored flags owned HERE) ---- #
        # Real mode passes scored=True ONLY after every pin above passed;
        # the dry-run passes scored=False on the synthetic root (the family
        # runners' own test convention).  A family scored refusal is never
        # bypassed: it surfaces as an honest TECHABORT crash.
        run_kwargs: dict[str, Any] = {}
        if tick_sizes is not None:
            run_kwargs["tick_sizes"] = tick_sizes
        t_compute = time.time()
        cell = fam["run_arm"](
            args.arm, data_root, scored=scored_flag_wiring, **run_kwargs
        )
        compute_seconds = round(time.time() - t_compute, 1)
        scored_metric_computed = True

        # ---- non-vacuity + L-V14-0 postconditions (fail closed) ---- #
        problems = nonvacuity_problems(cell, fam)
        if problems:
            _write_json(
                out_dir / "runner_nonvacuity.json",
                {
                    "artifact": "v15_phase_e_runner_nonvacuity",
                    "family": args.family,
                    "arm_id": args.arm,
                    "at_utc": utc_now(),
                    "mode": preflight["mode"],
                    "problems": problems,
                    "disposition": (
                        "FAILED run (exit 2); nothing published, the cell "
                        "artifact is recorded for forensics only"
                    ),
                },
            )
            print("FAIL-CLOSED: runner non-vacuity postcondition failed:")
            for problem in problems:
                print(f"  - {problem}")
            return EXIT_FAIL_CLOSED

        # ---- scored-record scaffolding ---- #
        margin_block = compute_margin_to_fail(cell, fam)
        cell["scored_metrics"]["margin_to_fail"] = margin_block
        baseline_metrics = {
            "artifact": "v15_phase_e_baseline_metrics",
            "family": args.family,
            "family_id": fam["family_id"],
            "arm_id": args.arm,
            "role": fam["roles"][args.arm],
            "cell_schema": cell.get("schema"),
            "scored": bool(cell.get("scored")),
            "scored_metrics": cell["scored_metrics"],
            "fold_signs": cell.get("fold_signs"),
            "refusal_registry_digest": fam["refusal_digest"](cell),
            "hashes": cell.get("hashes") or {},
        }
        _write_json(out_dir / "baseline_metrics.json", baseline_metrics)
        scored = cell["scored_metrics"]
        print(
            "BASELINE",
            json.dumps(
                {
                    k: scored.get(k)
                    for k in (
                        "score_valid",
                        "net_return_sum",
                        "expectancy_per_day",
                        "max_drawdown",
                        "position_pf",
                        "n_positions",
                        "n_decisions",
                        "n_fills",
                        "cost_fills",
                        "cost_holding_terms",
                    )
                },
                default=str,
            ),
            f"compute_seconds={compute_seconds}",
        )

        if synthetic:
            print(
                "DRY-RUN: full path exercised on the synthetic data root; "
                "no scored ledger written (publication refused by mode)"
            )
            return EXIT_OK

        if not args.publish:
            print("PUBLISH: skipped (no --publish); cell artifacts written only")
            return EXIT_OK

        from research.v12.accounting import (
            STAGE_IDEMPOTENT_REPLAY,
            STAGE_PUBLISHED,
            read_v12_ledger,
        )

        record = publish_scored_cell(
            family=args.family,
            arm_id=args.arm,
            cell=cell,
            ledger_path=ledger_path,
            head=head,
        )
        publication = record["publication"]
        _write_json(out_dir / "publish_record.json", publication)
        ledger_state = read_v12_ledger(ledger_path)
        cell_summary = {
            "artifact": "v15_phase_e_cell_summary",
            "cycle": "CRYPTO-V15",
            "family": args.family,
            "family_id": fam["family_id"],
            "arm_id": args.arm,
            "role": fam["roles"][args.arm],
            "at_utc": utc_now(),
            "producer_head_sha": head,
            "arm_config_digest": digest,
            "remediated_kernel": True,
            "scored_flag": scored_flag_wiring,
            "result_sha256": str(cell["hashes"]["result_sha256"]),
            "staged": staged,
            "scored_metrics": {
                k: scored.get(k)
                for k in (
                    "score_valid",
                    "net_return_sum",
                    "expectancy_per_day",
                    "max_drawdown",
                    "position_pf",
                    "n_positions",
                    "n_decisions",
                    "n_fills",
                    "cost_fills",
                    "cost_holding_terms",
                    "cost_total",
                    "funding_sum",
                    "price_pnl_sum",
                )
            },
            "margin_to_fail": margin_block,
            "refusal_registry_digest": fam["refusal_digest"](cell),
            "publish_stage": publication["stage"],
            "published": bool(publication["published"]),
            "reason_codes": [str(r) for r in publication["reasons"]],
            "observed_delta": int(publication["observed_delta"]),
            "published_delta": int(publication["published_delta"]),
            "denominator_before": record["denominator_before"],
            "denominator_after": record["denominator_after"],
            "ledger_path": str(ledger_path),
            "ledger_sha256_after": ledger_state["sha256"],
            "run_seconds": {"compute": compute_seconds,
                            "total": round(time.time() - t_start, 1)},
        }
        _write_json(out_dir / "cell_summary.json", cell_summary)
        print(
            "PUBLISH",
            json.dumps(
                {
                    "stage": publication["stage"],
                    "published": publication["published"],
                    "reasons": publication["reasons"],
                    "denominator_after": record["denominator_after"],
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


if __name__ == "__main__":
    raise SystemExit(main())
