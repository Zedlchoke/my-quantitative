"""A5 full-family reproduction harness (PLAN.md section 6.6, V7 contract).

Freezes the comparison tolerances BEFORE any rerun is consulted, then compares
a scored experiment directory against its independent rerun directory across
the FULL surface required by PLAN section 6.6:

* code hash -- source ``launch_manifest.yaml`` ``git_commit_at_launch`` MUST
  be an ANCESTOR of the primary repository's current HEAD
  (``git merge-base --is-ancestor <launch> <HEAD>``), so a rerun executed at
  a descendant integration commit still verifies while unrelated divergence
  fails closed;
* config/data hashes -- SOURCE self-consistency: recomputed SHA-256 of the
  source experiment's own ``frozen/*`` files vs the digests recorded in its
  launch manifest (the rerun-side manifest carries no provenance fields and
  none are expected from it);
* order/position/ledger/funding/terminal artifact SHA-256 digests plus strict
  row-count equality;
* funding cashflow digest AND absolute cashflow-sum tolerance;
* canonical metrics numeric tolerances (total PnL via a relative-to-equity
  scaling rule, PF/MDD/beta/turnover relative);
* exact fold-PnL map equality;
* equity curve (reconstructed from the portfolio ledger) length + last-value
  tolerance and STRICT whole-curve digest equality;
* SOURCE ``artifact_hashes.json`` replay: every ``rel -> sha256`` entry of
  the source manifest EXCLUDING ``SKIP_RERUN`` rels must equal the recomputed
  SHA-256 of ``<rerun_artifacts>/<rel>``; a rerun-side file missing from that
  replay fails closed naming the rel, while extra rerun files the manifest
  does not list (e.g. ``core_result.json``) are ignored -- the
  ``--reproduce`` worker by design emits no ``artifact_hashes.json`` of its
  own and excludes ``launch_manifest.yaml``/``run.log`` from
  ``rerun_artifacts`` (A3 emission contract).  The pure existence half of the
  replay is re-stated as an explicit boolean surface,
  ``rerun_emission_completeness``, for audit readability.

``all_match`` is true only when every surface matches; every failing surface
carries a machine-readable reason.  The harness never rewrites evidence and
never mutates either experiment directory; its only output is the returned
report dict (and, for :func:`run_reproduction`, ``reproduction_report.json``
written into the verify directory).

Pre-run hygiene (:func:`run_reproduction`): when the verify directory already
exists (e.g. from a broken earlier attempt that would make the inner runner
abort with ``--verify-id`` already exists), the stale directory is inspected:
an ``all_match: true`` report short-circuits as already-verified, otherwise
the whole directory is RENAMED (bytes preserved, never deleted) to
``<verify_id>.FAILED-<UTCcompact>-n`` and a fresh run proceeds; the new
report records ``renamed_from``/``archived_to``.

    python -m research.reproduction_harness plan [--family {v6,v8}]
    python -m research.reproduction_harness freeze [--path OUT.json]
    python -m research.reproduction_harness compare --source DIR --rerun DIR \
        [--primary-repo REPO]
    python -m research.reproduction_harness run-one \
        --primary-repo REPO --source-rel results/portfolio_v6/XSECT-FUND-CARRY-1D \
        --verify-id VERIFY-V6FULL-1D [--reproduction-root results/reproduction_v7]
    python -m research.reproduction_harness emit-commands [--family {v6,v8}] \
        [--primary-repo REPO] [--reproduction-root ROOT]

The ``v8`` family (PLAN sections 7/13) lists XSECT-WREV-3D/7D/14D +
XSECT-WMOM-7D-CONTROL under ``results/portfolio_v8`` with
``VERIFY-V8-*`` verify ids and defaults to ``results/reproduction_v8``;
the WMOM control trial's frozen argv carries ``--control-momentum``,
which :func:`run_reproduction` forwards to the worker as
``PORTFOLIO_CONTROL_MOMENTUM``.

Exit codes: ``0`` match/ok, ``6`` reproduction mismatch, ``2`` abort/usage.
No network access; no engine imports; pure file/subprocess orchestration.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from contracts.protocol import sha256_file

__all__ = [
    "CONTROL_MOMENTUM_ENV",
    "FORWARDED_ENV_KEYS",
    "FROZEN_TOLERANCES",
    "REPRODUCTION_SCHEMA_VERSION",
    "EXIT_REPRO_MISMATCH",
    "SKIP_RERUN",
    "V6_FAMILY_DIR",
    "V8_FAMILY_DIR",
    "V8_REPRODUCTION_ROOT",
    "compare_trials",
    "expected_control_momentum_from_source",
    "expected_signal_family_from_source",
    "freeze_tolerances",
    "run_reproduction",
    "v6_family_plan",
    "v8_family_plan",
    "v8_verify_id_for_trial",
    "verify_id_for_trial",
    "main",
]

REPRODUCTION_SCHEMA_VERSION = 1
#: Mirrors research.portfolio_runner.EXIT_REPRO_MISMATCH semantics without
#: importing the runner (the harness must stay import-light).
EXIT_REPRO_MISMATCH = 6

#: --------------------------------------------------------------------------
#: FROZEN before any rerun is launched (PLAN 6.6: "tolerance được freeze trước").
#: Values here are contractual; changing them requires a new schema_version.
#: --------------------------------------------------------------------------
FROZEN_TOLERANCES: dict[str, Any] = {
    # total PnL: |src - rer| <= pnl_abs_scale_tol * scale where
    # scale = max(1.0, |starting_equity_src|, |ending_equity_src|,
    #                |starting_equity_rer|, |ending_equity_rer|)
    # (falls back to max(1.0, |pnl_src|, |pnl_rer|) when equity is absent).
    # Rationale: absolute noise scales with account size; anchoring the scale
    # to the EQUITY magnitude keeps the bound meaningful for both small and
    # large accounts instead of a raw absolute epsilon.
    "pnl_abs_scale_tol": 1e-9,
    # fee / slippage totals: absolute tolerance.
    "fee_abs_tol": 1e-6,
    "slippage_abs_tol": 1e-6,
    # profit factor / max drawdown / beta / turnover: relative tolerance,
    # |a - b| <= tol * max(1.0, |a|, |b|).
    "pf_rel_tol": 1e-6,
    "mdd_rel_tol": 1e-6,
    "beta_rel_tol": 1e-6,
    "turnover_rel_tol": 1e-6,
    # funding: cashflow-sum absolute tolerance (per-experiment total).
    "funding_abs_tol": 1e-6,
    # strict-equality surfaces (no numeric slack at all).
    "row_count_strict": True,
    "ledger_equity_digest_strict": True,
    "fold_pnls_exact": True,
    "artifact_manifest_strict": True,
}

#: Captured ONCE at import so repeated freeze_tolerances() calls are
#: byte-identical (determinism of the frozen document).
_FROZEN_GENERATED_AT_UTC: str = datetime.now(timezone.utc).isoformat()

_TOLERANCE_RULES: dict[str, str] = {
    "pnl_abs_scale": (
        "|src-rerun| <= pnl_abs_scale_tol * max(1.0, |starting_equity_src|, "
        "|ending_equity_src|, |starting_equity_rerun|, |ending_equity_rerun|); "
        "relative-to-equity scaling so the bound tracks account size"
    ),
    "fee_slippage": "absolute tolerance on summed fee/slippage totals",
    "pf_mdd_beta_turnover": (
        "|a-b| <= tol * max(1.0, |a|, |b|) per metric"
    ),
    "funding_cashflow_sum": (
        "digest strict equality PLUS |sum(src)-sum(rerun)| <= funding_abs_tol"
    ),
    "row_counts": "strict integer equality per jsonl artifact",
    "ledger_equity_digests": (
        "canonical_metrics orders/positions digests and the ledger-derived "
        "equity curve digest: strict SHA-256 equality"
    ),
    "fold_pnls": "exact map equality (no tolerance)",
    "artifact_manifest": (
        "each SOURCE artifact_hashes.json 'hashes' entry EXCLUDING "
        "SKIP_RERUN rels is recomputed against the rerun artifacts; "
        "extra rerun-side files are ignored; missing/unreadable source "
        "manifest or rerun artifact fails closed"
    ),
    "rerun_emission_completeness": (
        "every rel in the SOURCE artifact_hashes.json MINUS SKIP_RERUN "
        "(launch_manifest.yaml, run.log: excluded from rerun_artifacts by "
        "design) must exist on the rerun side; explicit existence-only "
        "re-statement of the replay's missing-file half for audit readability"
    ),
}


def freeze_tolerances(path: str | Path | None = None) -> dict[str, Any]:
    """Serialize the frozen tolerance contract as an immutable doc.

    Returns ``{"schema_version", "artifact", "generated_at_utc",
    "tolerances", "rules"}``.  Deterministic: ``generated_at_utc`` is frozen
    at module import, so every call returns identical content.  When ``path``
    is given the same document is also written as JSON (parent dirs created;
    existing files are never silently rewritten with different content).
    """
    doc = {
        "schema_version": REPRODUCTION_SCHEMA_VERSION,
        "artifact": "reproduction_tolerances",
        "generated_at_utc": _FROZEN_GENERATED_AT_UTC,
        "tolerances": copy.deepcopy(FROZEN_TOLERANCES),
        "rules": copy.deepcopy(_TOLERANCE_RULES),
    }
    if path is not None:
        target = Path(path)
        serialized = json.dumps(doc, indent=2, sort_keys=True) + "\n"
        if target.is_file():
            if target.read_text(encoding="utf-8") != serialized:
                raise RuntimeError(
                    f"frozen tolerances already exist with different content: {target}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(serialized, encoding="utf-8")
    return doc


# --------------------------------------------------------------------------- #
# low-level readers
# --------------------------------------------------------------------------- #
def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _read_jsonl_rows(path: Path) -> list[dict[str, Any]] | None:
    """Rows of a JSONL artifact, or ``None`` when missing/unreadable."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            return None
    return rows


def _file_sha_pair(source_dir: Path, rerun_dir: Path, rel: str) -> tuple[bool, str | None]:
    src, rer = source_dir / rel, rerun_dir / rel
    if not src.is_file():
        return False, f"missing_source_artifact:{rel}"
    if not rer.is_file():
        return False, f"missing_rerun_artifact:{rel}"
    if sha256_file(src) != sha256_file(rer):
        return False, f"digest_mismatch:{rel}"
    return True, None


def _close(a: float, b: float, tol: float) -> bool:
    return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(a)), abs(float(b)))


def _metric_number(metrics: Mapping[str, Any], key: str) -> float | None:
    """Numeric view of a canonical metric; unwraps nested PF payloads.

    ``canonical_metrics.json`` stores profit factor either as a scalar or as
    the merged position-level payload ``{"profit_factor": ..., ...}``; both
    shapes must be comparable.
    """
    value = metrics.get(key)
    if isinstance(value, Mapping):
        value = value.get("profit_factor")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_repo_head(primary_repo: str | Path) -> tuple[str | None, str | None]:
    """Current HEAD of ``primary_repo`` via ``git rev-parse HEAD``.

    Returns ``(head_sha, None)`` on success or ``(None, reason)`` fail-closed.
    """
    try:
        completed = subprocess.run(
            ["git", "-C", str(primary_repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"git_rev_parse:error:{type(exc).__name__}"
    if completed.returncode != 0:
        return None, "git_rev_parse:failed"
    head = completed.stdout.strip()
    if not head:
        return None, "git_rev_parse:empty_output"
    return head, None


def _commit_is_ancestor(primary_repo: str | Path, commit: str,
                        head: str) -> tuple[bool | None, str | None]:
    """Ancestry probe: ``git merge-base --is-ancestor <commit> <head>``.

    Returns ``(True, None)`` when ``commit`` is an ancestor of (or equal to)
    ``head``, ``(False, None)`` when git answers NO (exit code 1), and
    ``(None, reason)`` when the probe itself fails (fail-closed).
    """
    try:
        completed = subprocess.run(
            ["git", "-C", str(primary_repo), "merge-base", "--is-ancestor",
             str(commit), str(head)],
            capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"git_merge_base:error:{type(exc).__name__}"
    if completed.returncode == 0:
        return True, None
    if completed.returncode == 1:
        return False, None
    return None, f"git_merge_base:failed:{completed.returncode}"


# --------------------------------------------------------------------------- #
# surface comparisons
# --------------------------------------------------------------------------- #
#: rels the ``--reproduce`` worker EXCLUDES from ``rerun_artifacts/`` BY
#: DESIGN (A3 emission contract): ``launch_manifest.yaml`` is verify-dir
#: provenance and ``run.log`` is the worker's own console log -- neither is
#: replayed from the SOURCE artifact_hashes.json against the rerun side.
SKIP_RERUN: tuple[str, ...] = ("launch_manifest.yaml", "run.log")

_LAUNCH_MANIFEST_NAMES = ("launch_manifest.yaml", "rerun_manifest.yaml")
#: research.portfolio_runner writes ``rerun_manifest.yaml`` at the VERIFY-DIR
#: level (the parent of ``rerun_artifacts/``), never inside the artifacts dir,
#: so the rerun-side loader probes the parent directory for that alias only.
_RERUN_MANIFEST_ALIAS = "rerun_manifest.yaml"


def _load_launch_manifest(exp_dir: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Parsed launch manifest mapping, or ``(None, reason)`` fail-closed."""
    for name in _LAUNCH_MANIFEST_NAMES:
        if name == _RERUN_MANIFEST_ALIAS:
            candidates = (exp_dir / name, exp_dir.parent / name)
        else:
            candidates = (exp_dir / name,)
        path = next((candidate for candidate in candidates if candidate.is_file()), None)
        if path is None:
            continue
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, ValueError) as exc:
            return None, f"{name}:unreadable:{type(exc).__name__}"
        if not isinstance(raw, Mapping):
            return None, f"{name}:not_a_mapping"
        return dict(raw), None
    return None, f"{_LAUNCH_MANIFEST_NAMES[0]}:missing"


#: argv flags inside ``exact_backtest_argv`` whose value pins the signal
#: family a faithful rerun MUST execute.
_SIGNAL_FAMILY_ARGV_FLAGS = ("--signal-family", "--strategy-kind")


def expected_signal_family_from_source(source_exp_dir: str | Path) -> str | None:
    """Signal family the rerun must execute, from the frozen source argv.

    Reads ``exact_backtest_argv`` from the source launch manifest; the token
    following ``--signal-family``/``--strategy-kind`` pins the family (e.g.
    ``funding_carry`` for the V6 family trials).  Returns ``None`` when the
    manifest is missing/unreadable or carries no such flag (default dispatch).
    """
    manifest, _reason = _load_launch_manifest(Path(source_exp_dir))
    argv = (manifest or {}).get("exact_backtest_argv")
    if not isinstance(argv, (list, tuple)):
        return None
    tokens = [str(token) for token in argv]
    for index, token in enumerate(tokens[:-1]):
        if token in _SIGNAL_FAMILY_ARGV_FLAGS:
            value = tokens[index + 1].strip()
            if value:
                return value
    return None


#: argv flag inside ``exact_backtest_argv`` that marks the source run as a
#: MOMENTUM-CONTROL trial (V8 ``XSECT-WMOM-7D-CONTROL``): a faithful rerun
#: worker must inherit the same control dispatch, which the runner reads from
#: :data:`CONTROL_MOMENTUM_ENV` in its environment.
_CONTROL_MOMENTUM_ARGV_FLAG = "--control-momentum"

#: Worker-environment key carrying the momentum-control dispatch.
CONTROL_MOMENTUM_ENV = "PORTFOLIO_CONTROL_MOMENTUM"

#: Environment keys this harness GUARANTEES reach the spawned reproduce
#: worker.  The worker inherits the FULL parent environment by design (the
#: V6 audit traced a silent dispatch divergence to an env-deletion side
#: effect -- commit fe31440 -- so whitelisting/downsizing the child env is
#: forbidden); these keys are additionally re-copied explicitly and their
#: resolved values recorded in every report so the guarantee is auditable.
FORWARDED_ENV_KEYS: tuple[str, ...] = (
    "PORTFOLIO_SIGNAL_FAMILY",
    CONTROL_MOMENTUM_ENV,
)


def expected_control_momentum_from_source(
        source_exp_dir: str | Path) -> str | None:
    """Momentum-control dispatch the rerun must execute, from frozen argv.

    Reads ``exact_backtest_argv`` from the source launch manifest; a
    ``--control-momentum`` token pins the WMOM control trial.  A bare flag
    maps to ``"1"``; ``--control-momentum <value>`` forwards the value
    verbatim.  Returns ``None`` when the manifest is missing/unreadable or
    carries no such flag (plain directional trial).
    """
    manifest, _reason = _load_launch_manifest(Path(source_exp_dir))
    argv = (manifest or {}).get("exact_backtest_argv")
    if not isinstance(argv, (list, tuple)):
        return None
    tokens = [str(token) for token in argv]
    for index, token in enumerate(tokens):
        if token != _CONTROL_MOMENTUM_ARGV_FLAG:
            continue
        nxt = tokens[index + 1] if index + 1 < len(tokens) else ""
        if nxt and not nxt.startswith("-"):
            return nxt.strip()
        return "1"
    return None


_FROZEN_INPUT_HASH_FIELDS: tuple[tuple[str, str], ...] = (
    ("runtime_config_sha256", "frozen/config.yaml"),
    ("candidate_spec_sha256", "frozen/candidate.yaml"),
    ("data_manifest_sha256", "frozen/data_manifest.json"),
    ("universe_sha256", "frozen/universe.json"),
)

_ROW_COUNT_ARTIFACTS: tuple[str, ...] = (
    "orders.jsonl",
    "positions.jsonl",
    "portfolio_ledger.jsonl",
    "funding_cashflows.jsonl",
    "terminal_positions.jsonl",
)

_CANONICAL_METRIC_SURFACES: tuple[tuple[str, str, str], ...] = (
    # (check name, canonical key, tolerance key)
    ("pnl_match", "total_pnl", "pnl_abs_scale_tol"),
    ("pf_match", "pf_position_level", "pf_rel_tol"),
    ("mdd_match", "max_drawdown_fraction", "mdd_rel_tol"),
    ("beta_match", "beta", "beta_rel_tol"),
    ("turnover_match", "turnover_total", "turnover_rel_tol"),
)

_LEDGER_EQUITY_CURVE_NAME = "equity_curve_from_ledger"


def _equity_curve_from_ledger(rows: Sequence[Mapping[str, Any]] | None) -> list[list[float]] | None:
    """Sorted ``[[ts, equity], ...]`` reconstruction; ``None`` if unusable."""
    if rows is None:
        return None
    points: list[list[float]] = []
    for row in rows:
        try:
            points.append([int(row["ts"]), float(row["equity"])])
        except (KeyError, TypeError, ValueError):
            return None
    points.sort(key=lambda pair: pair[0])
    return points


def _curve_digest(curve: Sequence[Sequence[float]]) -> str:
    payload = json.dumps([list(pair) for pair in curve], sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _pnl_scale(source_metrics: Mapping[str, Any],
               rerun_metrics: Mapping[str, Any]) -> float:
    """Relative-to-equity scale (see FROZEN_TOLERANCES['pnl_abs_scale_tol'])."""

    def _num(doc: Mapping[str, Any], key: str) -> float | None:
        value = doc.get(key)
        try:
            return abs(float(value)) if value is not None else None
        except (TypeError, ValueError):
            return None

    candidates = [1.0]
    for doc in (source_metrics, rerun_metrics):
        for key in ("starting_equity", "ending_equity"):
            value = _num(doc, key)
            if value is not None:
                candidates.append(value)
    for doc in (source_metrics, rerun_metrics):
        value = _num(doc, "total_pnl")
        if value is not None:
            candidates.append(value)
    return max(candidates)


def compare_trials(source_exp_dir: str | Path,
                   rerun_exp_dir: str | Path,
                   tolerances: Mapping[str, Any] | None = None,
                   primary_repo: str | Path | None = None,
                   git_head: str | None = None) -> dict[str, Any]:
    """Compare a scored experiment dir against its independent rerun dir.

    Returns a report dict whose ``checks`` maps each surface name to a boolean
    and ``surfaces`` carries details/reasons; ``all_match`` is true only when
    EVERY surface matched.  Fail-closed: missing artifacts, unreadable
    manifests and absent metric fields are mismatches with explicit reasons,
    never silent passes.

    Provenance is anchored to AUTHORITATIVE sources only (never to the
    rerun-side manifest): ``code_hash_match`` requires the source launch
    manifest's ``git_commit_at_launch`` to be an ancestor of the primary
    repository's current HEAD (``git merge-base --is-ancestor``; a rerun at a
    descendant integration commit verifies, unrelated divergence fails
    closed), ``config_hashes_match``/``data_hashes_match`` require the source
    experiment's own frozen files to hash to the digests its launch manifest
    recorded, and ``artifact_manifest_match`` replays every entry of the
    SOURCE ``artifact_hashes.json`` against the rerun artifacts after dropping
    the ``SKIP_RERUN`` rels the worker excludes by design (missing non-skipped
    rerun files fail closed naming the rel; extra rerun files are ignored);
    ``rerun_emission_completeness`` re-states that existence half as an
    explicit boolean.
    ``primary_repo`` (default: cwd) supplies the repository for the HEAD and
    ancestry lookups; ``git_head`` overrides HEAD resolution entirely and
    emulates the ancestry rule by direct equality (hermetic test seam --
    production callers must not pass it).
    """
    tol = dict(FROZEN_TOLERANCES if tolerances is None else tolerances)
    source_dir = Path(source_exp_dir)
    rerun_dir = Path(rerun_exp_dir)

    checks: dict[str, bool] = {}
    surfaces: dict[str, dict[str, Any]] = {}

    def record(name: str, matched: bool, *, reason: str | None = None,
               **details: Any) -> None:
        checks[name] = bool(matched)
        entry: dict[str, Any] = {"match": bool(matched)}
        if reason is not None:
            entry["reason"] = reason
        if details:
            entry.update(details)
        surfaces[name] = entry

    # -- 0. directories exist ------------------------------------------------
    if not source_dir.is_dir() or not rerun_dir.is_dir():
        missing = ("source" if not source_dir.is_dir() else "rerun") + "_experiment_dir_missing"
        for name in _ALL_SURFACE_NAMES:
            record(name, False, reason=missing)
        return {
            "schema_version": REPRODUCTION_SCHEMA_VERSION,
            "comparison_surface": "v7_reproduction_full",
            "source_experiment_dir": str(source_dir),
            "rerun_experiment_dir": str(rerun_dir),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "tolerances": tol,
            "tolerance_rules": dict(_TOLERANCE_RULES),
            "checks": checks,
            "surfaces": surfaces,
            "all_match": False,
            "error": missing,
        }

    # -- 1. code hash: source launch commit ancestor of primary repo HEAD ----
    # Authoritative anchor: the SOURCE launch manifest's git_commit_at_launch
    # must be an ANCESTOR of the primary repository's current HEAD
    # (merge-base --is-ancestor).  A rerun worker executed at a descendant
    # integration commit therefore verifies, while unrelated divergence still
    # fails closed.  The rerun-side manifest carries no provenance fields and
    # none are expected from it.
    source_manifest, _source_manifest_reason = _load_launch_manifest(source_dir)
    source_commit = (source_manifest or {}).get("git_commit_at_launch")
    head_reason: str | None = None
    if git_head:
        resolved_head, head_reason = str(git_head), None
    else:
        resolved_head, head_reason = _resolve_repo_head(
            Path(primary_repo) if primary_repo is not None else Path.cwd())
    code_matched = False
    if source_manifest is None or source_commit in (None, ""):
        code_reason = ("launch_manifest.yaml:missing" if source_manifest is None
                       else "git_commit_at_launch:missing_field")
    elif resolved_head is None:
        code_reason = f"git_head_unresolved:{head_reason}"
    elif git_head:
        # Hermetic test seam: no trustworthy repo is available for a real
        # merge-base probe, so the caller-vouched head emulates the rule by
        # direct equality (the degenerate ancestor case).  Production callers
        # must not pass git_head.
        code_matched = str(source_commit) == resolved_head
        code_reason = None if code_matched else "git_commit_at_launch:not_ancestor_of_head"
    else:
        ancestry, probe_reason = _commit_is_ancestor(
            Path(primary_repo) if primary_repo is not None else Path.cwd(),
            str(source_commit), resolved_head)
        if ancestry is True:
            code_matched, code_reason = True, None
        else:
            code_reason = probe_reason or "git_commit_at_launch:not_ancestor_of_head"
    record("code_hash_match", code_matched, reason=code_reason,
           source=str(source_commit) if source_commit else None,
           head=str(resolved_head) if resolved_head else None)

    # -- 2. config/data hashes: SOURCE self-consistency -----------------------
    # The digests recorded in the source launch manifest must equal the
    # recomputed SHA-256 of the source experiment's own frozen/* files.
    config_reasons: list[str] = []
    data_reasons: list[str] = []
    for field, rel in _FROZEN_INPUT_HASH_FIELDS:
        reason: str | None = None
        expected = (source_manifest or {}).get(field)
        target = source_dir / rel
        if expected is None:
            reason = f"{field}:missing_in_source_manifest"
        elif not target.is_file():
            reason = f"source:{rel}:missing"
        elif sha256_file(target) != str(expected):
            reason = f"{field}:self_hash_mismatch"
        bucket = (config_reasons if rel.endswith(("config.yaml", "candidate.yaml"))
                  else data_reasons)
        if reason is not None:
            bucket.append(reason)
    record("config_hashes_match", not config_reasons,
           reason=None if not config_reasons else ";".join(config_reasons))
    record("data_hashes_match", not data_reasons,
           reason=None if not data_reasons else ";".join(data_reasons))

    # -- 3. artifact file digests --------------------------------------------
    for name, rel in (
        ("orders_file_digest_match", "orders.jsonl"),
        ("positions_file_digest_match", "positions.jsonl"),
        ("ledger_file_digest_match", "portfolio_ledger.jsonl"),
        ("funding_digest_match", "funding_cashflows.jsonl"),
        ("terminal_positions_digest_match", "terminal_positions.jsonl"),
    ):
        matched, reason = _file_sha_pair(source_dir, rerun_dir, rel)
        record(name, matched, reason=reason)

    # -- 4. strict row counts --------------------------------------------------
    counts_src: dict[str, int] = {}
    counts_rer: dict[str, int] = {}
    row_reasons: list[str] = []
    for rel in _ROW_COUNT_ARTIFACTS:
        rows_src = _read_jsonl_rows(source_dir / rel)
        rows_rer = _read_jsonl_rows(rerun_dir / rel)
        if rows_src is None or rows_rer is None:
            row_reasons.append(f"unreadable_or_missing:{rel}")
            continue
        counts_src[rel] = len(rows_src)
        counts_rer[rel] = len(rows_rer)
        if len(rows_src) != len(rows_rer):
            row_reasons.append(f"row_count_mismatch:{rel}:{len(rows_src)}vs{len(rows_rer)}")
    record("row_counts_match", not row_reasons,
           reason=None if not row_reasons else ";".join(row_reasons),
           source=counts_src, rerun=counts_rer)

    # -- 5. canonical metrics --------------------------------------------------
    source_metrics = _read_json(source_dir / "canonical_metrics.json") or {}
    rerun_metrics = _read_json(rerun_dir / "canonical_metrics.json") or {}
    if not source_metrics:
        record("canonical_metrics_readable", False,
               reason="source_canonical_metrics_missing_or_unreadable")
    elif not rerun_metrics:
        record("canonical_metrics_readable", False,
               reason="rerun_canonical_metrics_missing_or_unreadable")
    else:
        record("canonical_metrics_readable", True)

    for name, key, tol_key in _CANONICAL_METRIC_SURFACES:
        if not source_metrics or not rerun_metrics:
            record(name, False, reason="canonical_metrics_unavailable")
            continue
        src_num = _metric_number(source_metrics, key)
        rer_num = _metric_number(rerun_metrics, key)
        if src_num is None or rer_num is None:
            record(name, False, reason=f"{key}:missing_field_or_non_numeric")
            continue
        matched = _close(src_num, rer_num, float(tol[tol_key]))
        scale = (_pnl_scale(source_metrics, rerun_metrics)
                 if tol_key == "pnl_abs_scale_tol" else None)
        record(name, matched,
               reason=None if matched else f"{key}:beyond_tolerance",
               **({"scale": scale} if scale is not None else {}),
               source=src_num, rerun=rer_num)

    # exact fold PnL map (no tolerance)
    fold_src = source_metrics.get("fold_pnls")
    fold_rer = rerun_metrics.get("fold_pnls")
    folds_matched = (
        isinstance(fold_src, Mapping) and isinstance(fold_rer, Mapping)
        and {str(k): v for k, v in fold_src.items()}
        == {str(k): v for k, v in fold_rer.items()}
    ) if tol.get("fold_pnls_exact", True) else True
    record("fold_pnls_exact_match", bool(folds_matched),
           reason=None if folds_matched else "fold_pnls:map_mismatch",
           source=dict(fold_src) if isinstance(fold_src, Mapping) else fold_src,
           rerun=dict(fold_rer) if isinstance(fold_rer, Mapping) else fold_rer)

    # -- 6. canonical row digests (strict) ------------------------------------
    digest_pairs = (("orders_digest", "orders"), ("positions_digest", "positions"))
    digest_reasons: list[str] = []
    for key, label in digest_pairs:
        src_dig, rer_dig = source_metrics.get(key), rerun_metrics.get(key)
        if src_dig is None or rer_dig is None:
            digest_reasons.append(f"{key}:missing_field")
        elif src_dig != rer_dig:
            digest_reasons.append(f"{key}:mismatch")
    record("canonical_row_digests_match", not digest_reasons,
           reason=None if not digest_reasons else ";".join(digest_reasons))

    # -- 7. funding cashflow sum (abs tol) ------------------------------------
    funding_src = _read_jsonl_rows(source_dir / "funding_cashflows.jsonl")
    funding_rer = _read_jsonl_rows(rerun_dir / "funding_cashflows.jsonl")

    def _cashflow_sum(rows: list[dict[str, Any]] | None) -> float | None:
        if rows is None:
            return None
        total = 0.0
        for row in rows:
            value = row.get("cashflow")
            if value is None:
                return None
            try:
                total += float(value)
            except (TypeError, ValueError):
                return None
        return total

    sum_src, sum_rer = _cashflow_sum(funding_src), _cashflow_sum(funding_rer)
    if sum_src is None or sum_rer is None:
        record("funding_sum_match", False,
               reason="funding_cashflows:unreadable_or_missing_field")
    else:
        delta = abs(sum_src - sum_rer)
        matched = delta <= float(tol["funding_abs_tol"])
        record("funding_sum_match", matched,
               reason=None if matched else "funding_cashflow_sum:beyond_tolerance",
               source=sum_src, rerun=sum_rer, delta=delta)

    # -- 8. equity curve (length + last value tol, strict digest) -------------
    curve_src = _equity_curve_from_ledger(_read_jsonl_rows(
        source_dir / "portfolio_ledger.jsonl"))
    curve_rer = _equity_curve_from_ledger(_read_jsonl_rows(
        rerun_dir / "portfolio_ledger.jsonl"))
    if curve_src is None or curve_rer is None:
        record("equity_curve_shape_match", False,
               reason="equity_curve:unusable_ledger_rows")
        record("equity_curve_digest_match", False,
               reason="equity_curve:unusable_ledger_rows")
    else:
        shape_ok = len(curve_src) == len(curve_rer)
        shape_reason = None if shape_ok else (
            f"equity_curve:length_mismatch:{len(curve_src)}vs{len(curve_rer)}")
        if shape_ok and curve_src and curve_rer:
            last_src, last_rer = curve_src[-1][1], curve_rer[-1][1]
            scale = _pnl_scale(source_metrics, rerun_metrics)
            last_ok = abs(last_src - last_rer) <= float(
                tol["pnl_abs_scale_tol"]) * scale
            shape_reason = None if last_ok else "equity_curve:last_value_beyond_tolerance"
            shape_ok = last_ok
        record("equity_curve_shape_match", shape_ok, reason=shape_reason,
               length_source=len(curve_src), length_rerun=len(curve_rer),
               last_value_source=curve_src[-1][1] if curve_src else None,
               last_value_rerun=curve_rer[-1][1] if curve_rer else None)
        dig_ok = _curve_digest(curve_src) == _curve_digest(curve_rer)
        record("equity_curve_digest_match", bool(dig_ok),
               reason=None if dig_ok else "equity_curve_digest:mismatch")

    # -- 9. SOURCE artifact manifest replayed against the rerun artifacts -----
    # The --reproduce worker emits the FULL deterministic artifact set EXCEPT
    # the SKIP_RERUN rels (launch_manifest.yaml / run.log are excluded BY
    # DESIGN) and emits no artifact_hashes.json of its own, so the SOURCE
    # manifest is authoritative: every NON-skipped listed rel must recompute
    # to the recorded digest inside the rerun dir; a missing/unreadable
    # non-skipped rerun file fails closed naming that rel; extra unlisted
    # rerun files (e.g. core_result.json) are ignored.
    # rerun_emission_completeness re-states the pure existence half (every
    # SOURCE key minus SKIP_RERUN present on the rerun side) as an explicit
    # boolean for audit readability.
    manifest_src = _read_json(source_dir / "artifact_hashes.json")
    hashes_src = (manifest_src.get("hashes")
                  if isinstance(manifest_src, Mapping) else None)
    if not isinstance(hashes_src, Mapping) or not hashes_src:
        reason = "source_artifact_hashes:missing_or_unreadable"
        record("rerun_emission_completeness", False, reason=reason,
               expected=0, missing=[], skipped=[])
        record("artifact_manifest_match", False, reason=reason, entries=0)
    else:
        rels_all = sorted(map(str, hashes_src))
        skipped = [rel for rel in rels_all if rel in SKIP_RERUN]
        expected = [rel for rel in rels_all if rel not in SKIP_RERUN]
        missing: list[str] = []
        unreadable: list[str] = []
        mismatched: list[str] = []
        for rel in expected:
            target = rerun_dir / rel
            if not target.is_file():
                missing.append(rel)
                continue
            try:
                actual = sha256_file(target)
            except OSError:
                unreadable.append(rel)
                continue
            if actual != str(hashes_src[rel]):
                mismatched.append(rel)
        record("rerun_emission_completeness", not missing,
               reason=None if not missing else ";".join(
                   f"missing_rerun_artifact:{rel}" for rel in missing[:8]),
               expected=len(expected), missing=missing[:8],
               missing_total=len(missing), skipped=skipped)
        reasons = ([f"missing_rerun_artifact:{rel}" for rel in missing]
                   + [f"unreadable_rerun_artifact:{rel}" for rel in unreadable]
                   + [f"artifact_hash_mismatch:{rel}" for rel in mismatched])
        matched = not reasons
        shown, reason = reasons[:8], None
        if reasons:
            reason = ";".join(shown) + (f";+{len(reasons) - 8}_more"
                                        if len(reasons) > 8 else "")
        record("artifact_manifest_match", matched, reason=reason,
               entries=len(expected), skipped=skipped,
               missing=missing[:8], unreadable=unreadable[:8],
               differing=mismatched[:8],
               missing_total=len(missing), unreadable_total=len(unreadable),
               differing_total=len(mismatched))

    all_match = all(checks.values())
    return {
        "schema_version": REPRODUCTION_SCHEMA_VERSION,
        "comparison_surface": "v7_reproduction_full",
        "source_experiment_dir": str(source_dir),
        "rerun_experiment_dir": str(rerun_dir),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tolerances": tol,
        "tolerance_rules": dict(_TOLERANCE_RULES),
        "checks": checks,
        "surfaces": surfaces,
        "all_match": all_match,
    }


#: Canonical surface names, derived once so the early-return path above stays
#: exhaustive even when a directory itself is missing.
_ALL_SURFACE_NAMES: tuple[str, ...] = (
    "code_hash_match",
    "config_hashes_match",
    "data_hashes_match",
    "orders_file_digest_match",
    "positions_file_digest_match",
    "ledger_file_digest_match",
    "funding_digest_match",
    "terminal_positions_digest_match",
    "row_counts_match",
    "canonical_metrics_readable",
    *(name for name, _key, _tol in _CANONICAL_METRIC_SURFACES),
    "fold_pnls_exact_match",
    "canonical_row_digests_match",
    "funding_sum_match",
    "equity_curve_shape_match",
    "equity_curve_digest_match",
    "rerun_emission_completeness",
    "artifact_manifest_match",
)


# --------------------------------------------------------------------------- #
# V6 family plan
# --------------------------------------------------------------------------- #
V6_FAMILY_DIR = "results/portfolio_v6"

_V6_FAMILY_TRIALS: tuple[tuple[str, str], ...] = (
    ("XSECT-FUND-CARRY-1D", f"{V6_FAMILY_DIR}/XSECT-FUND-CARRY-1D"),
    ("XSECT-FUND-CARRY-3D", f"{V6_FAMILY_DIR}/XSECT-FUND-CARRY-3D"),
    ("XSECT-FUND-CARRY-7D", f"{V6_FAMILY_DIR}/XSECT-FUND-CARRY-7D"),
    ("XSECT-FUND-REVERSE-3D-CONTROL", f"{V6_FAMILY_DIR}/XSECT-FUND-REVERSE-3D-CONTROL"),
)

_V6_VERIFY_SHORT: dict[str, str] = {
    "XSECT-FUND-CARRY-1D": "1D",
    "XSECT-FUND-CARRY-3D": "3D",
    "XSECT-FUND-CARRY-7D": "7D",
    "XSECT-FUND-REVERSE-3D-CONTROL": "REV3D",
}


def v6_family_plan() -> list[tuple[str, str]]:
    """The four V6 family trials: ``(trial_id, source_rel)`` pairs."""
    return [(trial_id, source_rel) for trial_id, source_rel in _V6_FAMILY_TRIALS]


def verify_id_for_trial(trial_id: str) -> str:
    """Deterministic verify id ``VERIFY-V6FULL-<short>`` for a family trial."""
    short = _V6_VERIFY_SHORT.get(trial_id)
    if short is None:
        short = "".join(ch if ch.isalnum() else "-" for ch in trial_id)[:32].strip("-")
    return f"VERIFY-V6FULL-{short}"


# --------------------------------------------------------------------------- #
# V8 family plan (PLAN.md section 7 / 13: results/portfolio_v8 + reproduction_v8)
# --------------------------------------------------------------------------- #
V8_FAMILY_DIR = "results/portfolio_v8"
#: Default verify root for the V8 four-trial loop (PLAN.md artifact contract).
V8_REPRODUCTION_ROOT = "results/reproduction_v8"

_V8_FAMILY_TRIALS: tuple[tuple[str, str], ...] = (
    ("XSECT-WREV-3D", f"{V8_FAMILY_DIR}/XSECT-WREV-3D"),
    ("XSECT-WREV-7D", f"{V8_FAMILY_DIR}/XSECT-WREV-7D"),
    ("XSECT-WREV-14D", f"{V8_FAMILY_DIR}/XSECT-WREV-14D"),
    ("XSECT-WMOM-7D-CONTROL", f"{V8_FAMILY_DIR}/XSECT-WMOM-7D-CONTROL"),
)

_V8_VERIFY_SHORT: dict[str, str] = {
    "XSECT-WREV-3D": "WREV-3D",
    "XSECT-WREV-7D": "WREV-7D",
    "XSECT-WREV-14D": "WREV-14D",
    "XSECT-WMOM-7D-CONTROL": "WMOM-7D-CONTROL",
}


def v8_family_plan() -> list[tuple[str, str]]:
    """The four V8 family trials: ``(trial_id, source_rel)`` pairs.

    Waves per PLAN section 7 -- Wave 1: XSECT-WREV-3D + XSECT-WREV-7D;
    Wave 2: XSECT-WREV-14D + XSECT-WMOM-7D-CONTROL (the control trial's
    source argv carries ``--control-momentum``, forwarded to the rerun
    worker via :data:`CONTROL_MOMENTUM_ENV`).
    """
    return [(trial_id, source_rel) for trial_id, source_rel in _V8_FAMILY_TRIALS]


def v8_verify_id_for_trial(trial_id: str) -> str:
    """Deterministic verify id ``VERIFY-V8-<short>`` for a V8 family trial."""
    short = _V8_VERIFY_SHORT.get(trial_id)
    if short is None:
        short = "".join(
            ch if ch.isalnum() else "-" for ch in trial_id.removeprefix("XSECT-")
        )[:32].strip("-")
    return f"VERIFY-V8-{short}"


# --------------------------------------------------------------------------- #
# subprocess driver
# --------------------------------------------------------------------------- #
_DEFAULT_REPRODUCTION_ROOT = "results/reproduction_v7"


def _resolve_python() -> str:
    override = os.environ.get("ORCA_REPRO_PYTHON", "").strip()
    return override or sys.executable


def build_reproduce_command(primary_repo: str | Path,
                            source_rel: str,
                            verify_id: str,
                            reproduction_root: str = _DEFAULT_REPRODUCTION_ROOT) -> list[str]:
    """Exact argv handed to subprocess for one reproduction run."""
    repo = Path(primary_repo).resolve()
    source_abs = (repo / source_rel).resolve()
    repro_root_abs = (repo / reproduction_root).resolve()
    return [
        _resolve_python(), "-m", "research.portfolio_runner",
        "--reproduce", str(source_abs),
        "--verify-id", verify_id,
        "--reproduction-root", str(repro_root_abs),
    ]


def _locate_rerun_artifacts(verify_dir: Path) -> Path | None:
    for candidate in (verify_dir / "rerun_artifacts", verify_dir):
        if candidate.is_dir() and (candidate / "canonical_metrics.json").is_file():
            return candidate
    return None


def _archive_failed_verify_dir(verify_dir: Path) -> tuple[str, str]:
    """Preserve a stale/broken verify dir by RENAMING it aside (never delete).

    Target name: ``<verify_id>.FAILED-<UTCcompact>-n`` with ``n >= 1``
    disambiguating same-second collisions.  Returns ``(renamed_from,
    archived_to)`` paths.  Raises :class:`RuntimeError` when the rename fails
    so a fresh run can never clobber unarchived evidence.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    n = 1
    while True:
        candidate = verify_dir.parent / f"{verify_dir.name}.FAILED-{stamp}-{n}"
        if not candidate.exists():
            break
        n += 1
    try:
        verify_dir.rename(candidate)
    except OSError as exc:
        raise RuntimeError(
            f"cannot archive stale verify dir {verify_dir}: {exc}") from exc
    return str(verify_dir), str(candidate)


def _already_verified_report(verify_dir: Path) -> dict[str, Any] | None:
    """Persisted report proving this verify id already fully matched."""
    prior = _read_json(verify_dir / "reproduction_report.json")
    if isinstance(prior, Mapping) and prior.get("all_match") is True:
        return dict(prior)
    return None


def run_reproduction(primary_repo: str | Path,
                     source_rel: str,
                     verify_id: str,
                     reproduction_root: str = _DEFAULT_REPRODUCTION_ROOT,
                     expected_signal_family: str | None = None,
                     extra_env: Mapping[str, str] | None = None,
                     timeout_s: float | None = None) -> dict[str, Any]:
    """Re-run one experiment via ``research.portfolio_runner --reproduce`` and
    compare it against the source artifacts.

    Launches ``[python, -m, research.portfolio_runner, --reproduce,
    <abs source>, --verify-id, ..., --reproduction-root, ...]`` with
    ``cwd=primary_repo``.  The spawned runner inherits
    ``os.environ | {"PORTFOLIO_SIGNAL_FAMILY": family} | extra_env`` where
    ``family`` is derived from the SOURCE experiment's frozen
    ``exact_backtest_argv`` (``--signal-family``/``--strategy-kind``), unless
    explicitly pinned via ``expected_signal_family``; the resolved value is
    recorded as ``resolved_env_family`` (``None`` = default dispatch).  This
    keeps flagless reproduce workers on the source signal family instead of
    silently rerunning momentum (V6 4/4 loop defect).

    Momentum-control trials (V8 ``XSECT-WMOM-7D-CONTROL``): a
    ``--control-momentum`` token in the same frozen argv pins
    :data:`CONTROL_MOMENTUM_ENV` in the worker environment the same way --
    the derived value overrides any ambient one and is recorded as
    ``resolved_env_control_momentum``; when the argv carries no such flag,
    an ambient parent-process value is inherited untouched.  The full parent
    environment always reaches the child (see :data:`FORWARDED_ENV_KEYS`);
    ``extra_env`` still merges LAST so caller overrides win.

    The rerun artifacts under ``<primary_repo>/<reproduction_root>/<verify_id>/``
    are then located, :func:`compare_trials` runs and
    ``reproduction_report.json`` is written into the verify directory.

    Pre-run hygiene: if the verify directory already exists (leftover from an
    earlier BROKEN attempt -- otherwise the inner runner aborts because the
    ``--verify-id`` dir already exists), its persisted report decides the
    outcome: ``all_match: true`` short-circuits as ALREADY VERIFIED (the
    persisted report is returned untouched, no subprocess is spawned);
    anything else (false/mismatched/unreadable/absent report) is archived via
    :func:`_archive_failed_verify_dir` and a fresh run proceeds.  The new
    report then records ``renamed_from`` (original dir) and ``archived_to``
    (preserved copy location).

    ``worker_returncode`` is the raw exit status of the process THIS module
    spawned, taken directly from its own subprocess result -- it is never
    re-derived from any runner-written comparison artifact.  Returns the
    merged report (never raises for a mismatch; mismatch is reported via
    ``all_match: false``).
    """
    repo = Path(primary_repo)
    verify_dir = (repo / reproduction_root).resolve() / verify_id

    renamed_from: str | None = None
    archived_to: str | None = None
    if verify_dir.exists():
        prior = _already_verified_report(verify_dir)
        if prior is not None:
            prior.setdefault("report_path", str(verify_dir / "reproduction_report.json"))
            return prior
        renamed_from, archived_to = _archive_failed_verify_dir(verify_dir)

    command = build_reproduce_command(repo, source_rel, verify_id, reproduction_root)
    source_probe = Path(source_rel) if Path(source_rel).is_absolute() else (
        repo / source_rel)
    if expected_signal_family is None and source_probe.is_dir():
        expected_signal_family = expected_signal_family_from_source(source_probe)
    derived_control = (expected_control_momentum_from_source(source_probe)
                       if source_probe.is_dir() else None)
    # frozen source argv wins over an ambient orchestrator-provided value;
    # extra_env still merges LAST so a caller override wins in the child env
    resolved_control_momentum = (derived_control
                                 or os.environ.get(CONTROL_MOMENTUM_ENV, "").strip()
                                 or None)
    env = dict(os.environ)
    if expected_signal_family:
        env["PORTFOLIO_SIGNAL_FAMILY"] = str(expected_signal_family)
    if resolved_control_momentum:
        env[CONTROL_MOMENTUM_ENV] = str(resolved_control_momentum)
    if extra_env:
        env.update({str(k): str(v) for k, v in extra_env.items()})
    started_utc = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(command, cwd=str(repo), env=env,
                               capture_output=True, text=True,
                               timeout=timeout_s, check=False)
    finished_utc = datetime.now(timezone.utc).isoformat()

    def _spawn_fields() -> dict[str, Any]:
        return {
            "command": command,
            "returncode": completed.returncode,
            "worker_returncode": completed.returncode,
            "resolved_env_family": expected_signal_family,
            "resolved_env_control_momentum": resolved_control_momentum,
            "started_at_utc": started_utc,
            "finished_at_utc": finished_utc,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
        }

    rerun_dir = _locate_rerun_artifacts(verify_dir)
    source_abs = Path(source_rel) if Path(source_rel).is_absolute() else (
        repo / source_rel).resolve()
    if rerun_dir is None or not source_abs.is_dir():
        report: dict[str, Any] = {
            "schema_version": REPRODUCTION_SCHEMA_VERSION,
            "comparison_surface": "v7_reproduction_full",
            "verify_id": verify_id,
            "trial_source_rel": str(source_rel),
            "primary_repo": str(repo.resolve()),
            **_spawn_fields(),
            "error": ("rerun_artifacts_not_found" if rerun_dir is None
                      else "source_experiment_dir_missing"),
        }
        report["checks"] = {name: False for name in _ALL_SURFACE_NAMES}
        report["surfaces"] = {}
        report["all_match"] = False
    else:
        report = compare_trials(source_abs, rerun_dir, primary_repo=repo)
        report.update({
            "verify_id": verify_id,
            "trial_source_rel": str(source_rel),
            "primary_repo": str(repo.resolve()),
            "rerun_experiment_dir": str(rerun_dir),
            **_spawn_fields(),
        })
        report.pop("error", None)

    if renamed_from is not None:
        report["renamed_from"] = renamed_from
        report["archived_to"] = archived_to
    verify_dir.mkdir(parents=True, exist_ok=True)
    out_path = verify_dir / "reproduction_report.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
                        encoding="utf-8")
    report["report_path"] = str(out_path)
    return report


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
_FAMILY_PLANS: dict[str, Any] = {
    "v6": (v6_family_plan, verify_id_for_trial, _DEFAULT_REPRODUCTION_ROOT),
    "v8": (v8_family_plan, v8_verify_id_for_trial, V8_REPRODUCTION_ROOT),
}


def _emit_commands(primary_repo: str, reproduction_root: str,
                   family: str = "v6") -> int:
    plan_fn, verify_fn = _FAMILY_PLANS[family][:2]
    python = _resolve_python()
    this_pkg = "research.reproduction_harness"
    for trial_id, source_rel in plan_fn():
        verify_id = verify_fn(trial_id)
        print(
            f"# {trial_id}\n"
            f'{python} -m {this_pkg} run-one --primary-repo {primary_repo} '
            f'--source-rel {source_rel} --verify-id {verify_id} '
            f'--reproduction-root {reproduction_root}'
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research.reproduction_harness",
        description="A5 full-family reproduction harness (PLAN 6.6)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", help="print the family trial plan")
    p_plan.add_argument("--family", choices=tuple(_FAMILY_PLANS), default="v6")
    p_freeze = sub.add_parser("freeze", help="emit/write the frozen tolerance doc")
    p_freeze.add_argument("--path", default=None)
    p_compare = sub.add_parser("compare", help="compare two experiment dirs")
    p_compare.add_argument("--source", required=True)
    p_compare.add_argument("--rerun", required=True)
    p_compare.add_argument("--primary-repo", default=".",
                           help="repo whose git history anchors code_hash_match")
    p_run = sub.add_parser("run-one", help="reproduce one trial then compare")
    p_run.add_argument("--primary-repo", default=".")
    p_run.add_argument("--source-rel", required=True)
    p_run.add_argument("--verify-id", required=True)
    p_run.add_argument("--reproduction-root", default=_DEFAULT_REPRODUCTION_ROOT)
    p_emit = sub.add_parser("emit-commands",
                            help="print A1's per-family run-one command loop")
    p_emit.add_argument("--family", choices=tuple(_FAMILY_PLANS), default="v6")
    p_emit.add_argument("--primary-repo", default=".")
    p_emit.add_argument("--reproduction-root", default=None,
                        help="default: results/reproduction_v7 (v6) / "
                             "results/reproduction_v8 (v8)")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "plan":
        plan_fn, verify_fn, _root = _FAMILY_PLANS[args.family]
        for trial_id, source_rel in plan_fn():
            print(f"{trial_id}\t{source_rel}\t{verify_fn(trial_id)}")
        return 0
    if args.cmd == "freeze":
        print(json.dumps(freeze_tolerances(args.path), indent=2, sort_keys=True))
        return 0
    if args.cmd == "compare":
        report = compare_trials(args.source, args.rerun,
                                primary_repo=args.primary_repo)
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
        return 0 if report["all_match"] else EXIT_REPRO_MISMATCH
    if args.cmd == "run-one":
        report = run_reproduction(args.primary_repo, args.source_rel,
                                  args.verify_id, args.reproduction_root)
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
        return 0 if report["all_match"] else EXIT_REPRO_MISMATCH
    if args.cmd == "emit-commands":
        reproduction_root = (args.reproduction_root
                             or _FAMILY_PLANS[args.family][2])
        return _emit_commands(args.primary_repo, reproduction_root,
                              family=args.family)
    parser.error(f"unknown command: {args.cmd}")  # pragma: no cover
    return 2  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
