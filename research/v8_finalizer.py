"""V8 machine finalizer & statistics (A4) -- thin adapter over V7 finalizer.

Sprint V8 -- PLAN sections 7.2/7.3.  The generic six-artifact pipeline in
:mod:`research.v7_finalizer` is REUSED unchanged; this module only adds the
V8-specific layer:

* :func:`finalize_trial_v8` -- delegates to
  ``research.v7_finalizer.finalize_trial`` with the V8 resolved contract,
  then augments ``final_gate_result.json`` with gate **FG8**: the
  weekly-specific minimum-rebalances check (PLAN 7.2 "minimum weekly
  rebalances/legs frozen before score").  Threshold comes from the
  contract field ``min_weekly_rebalances`` (top level or under
  ``thresholds``).  If the field is ABSENT the criterion is emitted as an
  honest ``SKIPPED`` row that does NOT fail the trial (skip-not-fail);
  if present-but-unmeasurable it degrades to fail-closed ``NOT_TESTED``
  like every other hard input.
* :func:`build_family_summary` -- family-level §7.2 conjunction verdict:
  adjacent-pair logic over the lookback chain ``[3D, 7D, 14D]`` plus the
  control-not-beats-best rule, producing a ``V8_*`` terminal label per
  PLAN section 7.3.

Fail-closed rules carried over from V7: no silent defaults, PASS is
impossible without measurement, missing A7 evidence keeps FG7 failed, and
``effective_n_trials=None`` keeps DSR at its literal
``DSR_UNAVAILABLE_FAIL_CLOSED`` sentinel.  PBO intentionally stays at its
fail-closed sentinel here: the comparable-cohort returns matrix is a
family-level input assembled from :mod:`research.global_ledger`, not a
per-trial one.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from research.v7_finalizer import (
    ARTIFACT_FAMILY as V7_ARTIFACT_FAMILY,
    finalize_trial as v7_finalize_trial,
)

V8_FINALIZER_SCHEMA_VERSION = 2
V8_ARTIFACT_FAMILY = "V8_FINALIZER_A4"

WEEKLY_REBALANCE_GATE_ID = "FG8"
WEEKLY_REBALANCE_CONTRACT_KEY = "min_weekly_rebalances"

#: Frozen V8 formation-lookback chain (PLAN section 7.2 / candidate.yaml).
ADJACENT_CHAIN_DAYS_DEFAULT: tuple[int, ...] = (3, 7, 14)

ADJACENT_PAIR_RULE_ID = "ADJACENT_OVER_ASCENDING_DISTINCT_PASSING_LOOKBACKS_V1"
CONTROL_RULE_ID = "CONTROL_NOT_BEAT_BEST_REVERSAL_NET_PNL_V1"

#: Family terminal labels (PLAN section 7.3).
FAMILY_LOCK = "V8_LOCK_FOR_FUTURE_S1"
FAMILY_EXPLORATORY = "V8_STAGE_A_PASS_EXPLORATORY"
FAMILY_REJECT_ALL = "V8_REJECT_ALL"
FAMILY_INVALIDATED = "V8_INVALIDATED"

_LOCKBACK_RE = re.compile(r"(\d+)D")

SIX_FINAL_ARTIFACTS = (
    "final_gate_result.json",
    "final_scorecard.json",
    "concentration_report.json",
    "stress_manifest.json",
    "statistical_haircut.json",
    "reproduction_report.json",
)


# --------------------------------------------------------------------------- #
# small local IO helpers (kept dependency-free from v7 privates)
# --------------------------------------------------------------------------- #
def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _read_json(path: Path) -> Any | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".v8tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def parse_lookback_days(experiment_id: str | None) -> int | None:
    """``XSECT-WREV-14D`` -> 14; ``XSECT-WMOM-7D-CONTROL`` -> 7."""
    if not experiment_id:
        return None
    match = _LOCKBACK_RE.search(str(experiment_id).upper())
    return int(match.group(1)) if match else None


# --------------------------------------------------------------------------- #
# A7 verdict normalisation (fail closed on anything unrecognised)
# --------------------------------------------------------------------------- #
def normalize_a7_verdict(a7_verdict: Any) -> dict[str, Any] | None:
    """Map a V8 A7 terminal verdict onto the v7 ``a7_audit`` payload schema.

    * ``None``                -> ``None`` (FG7 audit criterion NOT_TESTED).
    * mapping                 -> passed through unchanged (must already carry
      ``unresolved_high``/``unresolved_critical`` or a ``findings`` list).
    * string ending in ``PASS`` -> normalised to zero unresolved findings
      WITH an explicit provenance note (never silently).
    * any other string/type   -> wrapped as unknown schema so FG7 fails
      closed instead of guessing.
    """
    if a7_verdict is None:
        return None
    if isinstance(a7_verdict, Mapping):
        return dict(a7_verdict)
    token = str(a7_verdict).strip().upper()
    if isinstance(a7_verdict, str) and token.endswith("PASS"):
        return {
            "unresolved_high": 0,
            "unresolved_critical": 0,
            "a7_verdict_source": f"STRING_VERDICT_NORMALIZED:{a7_verdict}",
        }
    return {"a7_verdict_schema_unknown": str(a7_verdict)}


# --------------------------------------------------------------------------- #
# FG8 -- weekly-specific minimum rebalances (PLAN 7.2)
# --------------------------------------------------------------------------- #
def _weekly_threshold(resolved_contract: Mapping[str, Any]) -> tuple[float | None, bool]:
    """Contract lookup for ``min_weekly_rebalances`` (top-level or thresholds).

    Returns ``(threshold_or_None, present_in_contract)``.  A malformed
    value counts as present-but-unmeasurable -> fail closed downstream.
    """
    thresholds = resolved_contract.get("thresholds")
    if WEEKLY_REBALANCE_CONTRACT_KEY in resolved_contract:
        return _finite(resolved_contract[WEEKLY_REBALANCE_CONTRACT_KEY]), True
    if isinstance(thresholds, Mapping) and \
            WEEKLY_REBALANCE_CONTRACT_KEY in thresholds:
        return _finite(thresholds[WEEKLY_REBALANCE_CONTRACT_KEY]), True
    return None, False


def measured_weekly_rebalances(canonical_metrics: Mapping[str, Any] | None) -> float | None:
    """Engine-scored rebalance count (``canonical_metrics.rebalances_scored``)."""
    if not isinstance(canonical_metrics, Mapping):
        return None
    return _finite(canonical_metrics.get("rebalances_scored"))


def build_weekly_rebalance_gate(
    canonical_metrics: Mapping[str, Any] | None,
    resolved_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Gate row ``FG8``: measured weekly rebalances >= frozen contract floor.

    * contract field absent      -> honest ``SKIPPED`` (never FAIL, never a
      silent PASS): excluded from the hard-gate conjunction.
    * present but threshold/measured unmeasurable -> fail-closed
      ``NOT_TESTED`` criterion (gate FAILs).
    """
    title = ("Weekly cadence (minimum rebalances frozen before score, "
             f"{WEEKLY_REBALANCE_CONTRACT_KEY})")
    threshold, present = _weekly_threshold(resolved_contract)
    if not present:
        reason = f"{WEEKLY_REBALANCE_CONTRACT_KEY}_not_in_contract_skip_not_fail"
        return {
            "gate": WEEKLY_REBALANCE_GATE_ID,
            "title": title,
            "status": "SKIPPED",
            "pass": None,
            "skipped": True,
            "criteria": [{
                "check": "weekly_rebalances_at_least_minimum",
                "measured_value": None,
                "threshold": None,
                "operator": ">=",
                "pass": None,
                "status": "SKIPPED",
                "reason": reason,
            }],
            "reasons": [reason],
        }
    measured = measured_weekly_rebalances(canonical_metrics)
    evaluated = None if (measured is None or threshold is None) \
        else measured >= threshold - 1e-12
    if evaluated is None:
        reason = (f"{WEEKLY_REBALANCE_CONTRACT_KEY}_unmeasurable:"
                  "rebalances_scored_missing" if measured is None
                  else f"{WEEKLY_REBALANCE_CONTRACT_KEY}_malformed")
        criterion = {
            "check": "weekly_rebalances_at_least_minimum",
            "measured_value": measured,
            "threshold": threshold,
            "operator": ">=",
            "pass": False,
            "status": "NOT_TESTED",
            "reason": reason,
        }
        status, passed, reasons = "FAIL", False, [reason]
    else:
        criterion = {
            "check": "weekly_rebalances_at_least_minimum",
            "measured_value": measured,
            "threshold": threshold,
            "operator": ">=",
            "pass": bool(evaluated),
            "status": "PASS" if evaluated else "FAIL",
            "reason": None if evaluated
            else "criterion_failed:weekly_rebalances_at_least_minimum",
        }
        status = "PASS" if evaluated else "FAIL"
        passed = bool(evaluated)
        reasons = [] if evaluated else ["weekly_rebalances_below_minimum"]
    return {
        "gate": WEEKLY_REBALANCE_GATE_ID,
        "title": title,
        "status": status,
        "pass": passed,
        "skipped": False,
        "criteria": [criterion],
        "reasons": reasons,
    }


def _fg8_effective(fg8: Mapping[str, Any]) -> bool:
    """Conjunction contribution of FG8: skipped gates do not block."""
    if fg8.get("skipped") is True:
        return True
    return fg8.get("pass") is True


# --------------------------------------------------------------------------- #
# finalize_trial_v8 -- thin delegation + FG8 augmentation
# --------------------------------------------------------------------------- #
def finalize_trial_v8(
    exp_dir: str | Path,
    *,
    resolved_contract: Mapping[str, Any],
    sibling_trials: Sequence[Mapping[str, Any]] | None = None,
    repro_comparison_path: str | Path | None = None,
    a7_verdict: Any = None,
    effective_n_trials: int | None = None,
) -> dict[str, Any]:
    """Finalize ONE finished V8 trial directory into the six artifacts.

    Delegates the whole FG0..FG7/scorecard/statistics pipeline to
    ``research.v7_finalizer.finalize_trial`` and then:

    #. appends the V8-specific **FG8** weekly-minimum-rebalances gate row;
    #. recomputes ``all_hard_gates_pass`` / ``verdict`` including FG8
       (skipped FG8 neither blocks nor helps);
    #. downgrades the scorecard's ``score_meaningful``/``band`` when FG8
       actively FAILED (score can never rescue a failed gate);
    #. embeds ``v8_meta`` (experiment identity derived from
       ``canonical_metrics.json`` + the resolved contract).

    ``repro_comparison_path`` is the single independent-rerun
    ``comparison.json`` for this trial; ``None`` fails FG6 closed
    (``no_comparisons_provided``), a missing/unreadable path fails it as
    ``MISSING_OR_UNREADABLE_FAIL_CLOSED``.
    """
    exp_dir = Path(exp_dir)
    if not isinstance(resolved_contract, Mapping):
        raise ValueError("resolved_contract_required_mapping_fail_closed")
    a7_audit = normalize_a7_verdict(a7_verdict)
    comparison_paths = [str(repro_comparison_path)] \
        if repro_comparison_path is not None else []

    summary = v7_finalize_trial(
        exp_dir,
        resolved_contract=dict(resolved_contract),
        sibling_trials=list(sibling_trials or []),
        effective_n_trials=effective_n_trials,
        comparison_paths=comparison_paths,
        a7_audit=a7_audit,
    )

    canonical_metrics = _read_json(exp_dir / "canonical_metrics.json")
    fg8 = build_weekly_rebalance_gate(canonical_metrics, resolved_contract)

    experiment_id = canonical_metrics.get("experiment_id") \
        if isinstance(canonical_metrics, Mapping) else None
    experiment_id = str(experiment_id) if experiment_id else Path(exp_dir).name
    is_control = bool(resolved_contract.get("is_control")) \
        or "CONTROL" in experiment_id.upper()
    v8_meta = {
        "experiment_id": experiment_id,
        "matrix_id": (canonical_metrics.get("matrix_id")
                      if isinstance(canonical_metrics, Mapping) else None),
        "direction": resolved_contract.get("direction"),
        "price_lookback_days": resolved_contract.get("price_lookback_days"),
        "is_control": is_control,
    }

    gate_path = exp_dir / "final_gate_result.json"
    gate_doc = _read_json(gate_path)
    all_pass = False
    if isinstance(gate_doc, Mapping):
        gates = [g for g in gate_doc.get("gates", []) if isinstance(g, Mapping)]
        gates.append(dict(fg8))
        gate_doc["gates"] = gates
        all_pass = all(g.get("pass") is True for g in gates[:-1]) \
            and _fg8_effective(fg8)
        gate_doc["all_hard_gates_pass"] = all_pass
        gate_doc["verdict"] = "LOCK_ELIGIBLE" if all_pass else "NOT_ELIGIBLE"
        gate_doc["v8_meta"] = v8_meta
        gate_doc["v8_finalizer"] = {
            "schema_version": V8_FINALIZER_SCHEMA_VERSION,
            "artifact_family": V8_ARTIFACT_FAMILY,
            "delegated_family": V7_ARTIFACT_FAMILY,
            "fg8_contract_key": WEEKLY_REBALANCE_CONTRACT_KEY,
            "skip_rule": ("min_weekly_rebalances absent from the resolved "
                          "contract => FG8 SKIPPED honestly (not FAIL, not "
                          "silent PASS); present => hard criterion"),
            "adjacent_chain_days": list(ADJACENT_CHAIN_DAYS_DEFAULT),
        }
        _write_json_atomic(gate_path, gate_doc)

    scorecard_path = exp_dir / "final_scorecard.json"
    scorecard = _read_json(scorecard_path)
    if isinstance(scorecard, Mapping) and scorecard.get("score_meaningful") is True \
            and not _fg8_effective(fg8):
        scorecard["score_meaningful"] = False
        scorecard["band"] = None
        scorecard["v8_note"] = ("FG8 weekly-rebalance gate failed after V7 "
                                "scoring; score is not meaningful (a score "
                                "can never rescue a failed gate)")
        _write_json_atomic(scorecard_path, scorecard)

    return {
        **summary,
        "all_hard_gates_pass": all_pass,
        "verdict": "LOCK_ELIGIBLE" if all_pass else "NOT_ELIGIBLE",
        "fg8": {
            "status": fg8["status"],
            "pass": fg8["pass"],
            "skipped": fg8["skipped"],
            "measured_value": (fg8["criteria"][0]["measured_value"]),
            "threshold": fg8["criteria"][0]["threshold"],
        },
        "v8_meta": v8_meta,
        "artifact_family": V8_ARTIFACT_FAMILY,
    }


# --------------------------------------------------------------------------- #
# build_family_summary -- PLAN 7.2 conjunction + 7.3 terminal labels
# --------------------------------------------------------------------------- #
def _trial_record(trial_dir: Path, cfg_specs: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    gate_doc = _read_json(trial_dir / "final_gate_result.json")
    canonical = _read_json(trial_dir / "canonical_metrics.json")
    runner_gate = _read_json(trial_dir / "gate_result.json")
    readable = isinstance(gate_doc, Mapping) and isinstance(canonical, Mapping)
    raw_experiment_id = canonical.get("experiment_id") \
        if isinstance(canonical, Mapping) else None
    experiment_id = str(raw_experiment_id) if raw_experiment_id else trial_dir.name
    spec = cfg_specs.get(experiment_id) or {}
    spec = spec if isinstance(spec, Mapping) else {}
    lookback = spec.get("price_lookback_days")
    if lookback is None:
        meta = gate_doc.get("v8_meta") if isinstance(gate_doc, Mapping) else None
        lookback = (meta or {}).get("price_lookback_days") \
            if isinstance(meta, Mapping) else None
    if lookback is None:
        lookback = parse_lookback_days(experiment_id)
    is_control = spec.get("is_control")
    if is_control is None:
        runner_flag = runner_gate.get("is_negative_control") \
            if isinstance(runner_gate, Mapping) else None
        meta = gate_doc.get("v8_meta") if isinstance(gate_doc, Mapping) else None
        meta_flag = (meta or {}).get("is_control") \
            if isinstance(meta, Mapping) else None
        is_control = bool(meta_flag) if meta_flag is not None else (
            bool(runner_flag) if runner_flag is not None
            else "CONTROL" in experiment_id.upper())
    net_pnl = _finite(canonical.get("total_pnl")) \
        if isinstance(canonical, Mapping) else None
    return {
        "experiment_dir": str(trial_dir),
        "experiment_id": experiment_id,
        "price_lookback_days": int(lookback) if lookback is not None else None,
        "is_control": bool(is_control),
        "net_pnl": net_pnl,
        "readable": readable,
        "all_hard_gates_pass": (gate_doc.get("all_hard_gates_pass") is True)
        if isinstance(gate_doc, Mapping) else False,
    }


def build_family_summary(
    trial_dirs: Sequence[str | Path],
    cfg: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Family-level §7.2 conjunction over finalized trial dirs.

    ``cfg`` keys (all optional, fail-closed defaults):

    * ``trial_specs``: ``{experiment_id: {"price_lookback_days": int,
      "is_control": bool}}`` explicit overrides (otherwise parsed from the
      experiment id / finalizer metadata);
    * ``adjacent_chain_days``: default frozen ``(3, 7, 14)``;
    * ``a7_terminal_pass`` / ``pbo_comparable_cohort_valid``: booleans that
      must BOTH be true (plus every trial passing its own gates) before the
      family may reach ``V8_LOCK_FOR_FUTURE_S1``; absent/false keeps the
      family at ``V8_STAGE_A_PASS_EXPLORATORY`` (forward/statistical
      evidence insufficient).

    Adjacent-pair rule ``ADJACENT_OVER_ASCENDING_DISTINCT_PASSING_LOOKBACKS_V1``:
    pairs are consecutive elements of the ASCENDING DISTINCT passing
    reversal-lookback list; a failing lookback drops out of the chain so
    its neighbours become adjacent -- e.g. 3D PASS + 7D FAIL + 14D PASS
    yields exactly one pair ``(3, 14)``, while a single passing lookback
    yields none.

    Control rule ``CONTROL_NOT_BEAT_BEST_REVERSAL_NET_PNL_V1``: the control
    trial's ``net_pnl`` must be <= the best reversal candidate's
    ``net_pnl``; unmeasurable pnl fails closed (never assumed fine).

    Verdict precedence (PLAN 7.3): any unreadable trial dir =>
    ``V8_INVALIDATED``; otherwise no adjacent passing pair OR control beats
    best OR control comparison unmeasurable => ``V8_REJECT_ALL``; otherwise
    lock vs exploratory per the statistical/A7 cfg flags above.
    """
    cfg = cfg or {}
    chain = tuple(int(d) for d in
                  (cfg.get("adjacent_chain_days") or ADJACENT_CHAIN_DAYS_DEFAULT))
    specs = cfg.get("trial_specs") or {}
    records = [_trial_record(Path(d), specs) for d in (trial_dirs or [])]

    unreadable = [r["experiment_dir"] for r in records if not r["readable"]]
    if not records or unreadable:
        return {
            "schema_version": V8_FINALIZER_SCHEMA_VERSION,
            "artifact_family": V8_ARTIFACT_FAMILY,
            "n_trials": len(records),
            "trials": records,
            "unreadable_trial_dirs": unreadable or
            ["no_trial_dirs_provided"],
            "passing_lookbacks": [],
            "adjacent_pairs": [],
            "pair_exists": False,
            "control_check": "NOT_TESTED",
            "core_hard_gate_conjunction_pass": False,
            "family_verdict": FAMILY_INVALIDATED,
            "reasons": ["final_gate_result_or_canonical_unreadable_fail_closed"]
            if unreadable else ["no_trial_dirs_provided"],
            "rules": {
                "adjacent_pair_rule": ADJACENT_PAIR_RULE_ID,
                "control_rule": CONTROL_RULE_ID,
                "chain_days": list(chain),
            },
        }

    reversals = [r for r in records if not r["is_control"]]
    controls = [r for r in records if r["is_control"]]
    reasons: list[str] = []

    passing_lookbacks = sorted({r["price_lookback_days"] for r in reversals
                                if r["all_hard_gates_pass"]
                                and r["price_lookback_days"] is not None})
    adjacent_pairs = [[a, b] for a, b in zip(passing_lookbacks, passing_lookbacks[1:])]
    pair_exists = len(adjacent_pairs) > 0
    if not pair_exists:
        reasons.append(
            "no_adjacent_passing_pair_over_chain_"
            + "_".join(str(d) for d in chain))

    reversal_pnls = [r["net_pnl"] for r in reversals if r["net_pnl"] is not None]
    control_pnls = [r["net_pnl"] for r in controls if r["net_pnl"] is not None]
    best_reversal_pnl = max(reversal_pnls) if reversal_pnls else None
    worst_case_control_pnl = max(control_pnls) if control_pnls else None

    if best_reversal_pnl is None or worst_case_control_pnl is None:
        control_check = "NOT_TESTED"
        control_ok = False
        reasons.append("control_not_beats_best_unmeasurable_fail_closed")
    else:
        control_ok = worst_case_control_pnl <= best_reversal_pnl
        control_check = "PASS" if control_ok else "FAIL_CONTROL_BEATS_BEST"
        if not control_ok:
            reasons.append(
                f"control_beats_best:{worst_case_control_pnl}>"
                f"{best_reversal_pnl}")

    core_pass = pair_exists and control_ok
    if core_pass:
        lock_ready = (cfg.get("a7_terminal_pass") is True
                      and cfg.get("pbo_comparable_cohort_valid") is True
                      and all(r["all_hard_gates_pass"] for r in records))
        verdict = FAMILY_LOCK if lock_ready else FAMILY_EXPLORATORY
        if not lock_ready:
            reasons.append(
                "lock_withheld_insufficient_statistical_or_a7_evidence")
    else:
        verdict = FAMILY_REJECT_ALL

    return {
        "schema_version": V8_FINALIZER_SCHEMA_VERSION,
        "artifact_family": V8_ARTIFACT_FAMILY,
        "n_trials": len(records),
        "trials": records,
        "unreadable_trial_dirs": [],
        "passing_lookbacks": passing_lookbacks,
        "adjacent_pairs": adjacent_pairs,
        "pair_exists": pair_exists,
        "best_reversal_net_pnl": best_reversal_pnl,
        "control_net_pnl_worst_case": worst_case_control_pnl,
        "control_check": control_check,
        "core_hard_gate_conjunction_pass": core_pass,
        "family_verdict": verdict,
        "reasons": reasons,
        "rules": {
            "adjacent_pair_rule": ADJACENT_PAIR_RULE_ID,
            "adjacent_pair_rule_detail": (
                "pairs are consecutive elements of the ascending DISTINCT "
                "passing reversal-lookback list; failing lookbacks drop out "
                "so their neighbours become adjacent (3D PASS + 7D FAIL + "
                "14D PASS => one pair (3,14))"),
            "control_rule": CONTROL_RULE_ID,
            "chain_days": list(chain),
        },
    }
