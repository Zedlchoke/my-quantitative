"""V7 machine finalizer & statistics (A4).

Sprint V7 -- PLAN sections 6.3-6.5, 9, 10.  Turns one finished trial
directory (as written by ``research.portfolio_runner``) into the six
machine-readable FINAL artifacts:

* ``final_gate_result.json``   hard gates FG0..FG7      (PLAN section 9)
* ``final_scorecard.json``     100-point table          (PLAN section 10)
* ``concentration_report.json`` positive-PnL concentration (fold/symbol)
* ``stress_manifest.json``     required stress families + executed flags
* ``statistical_haircut.json`` DSR + PBO                (PLAN 6.4/6.5)
* ``reproduction_report.json`` comparison.json aggregation

Design rules (frozen):

* **No silent defaults.**  Every threshold comes from the caller-supplied
  ``resolved_contract``; a missing threshold makes the affected criterion
  FAIL/NOT_TESTED -- never PASS against an implicit number.
* **Fail closed.**  Missing/unreadable input => gate row ``NOT_TESTED`` or
  ``FAIL`` with a reason string; PASS is impossible without measurement.
* **Honest statistics.**  DSR needs real daily returns (built from the
  portfolio-ledger equity curve inside the trial dir), observed Sharpe,
  moments, sample length, the global effective trial count AND comparable-
  trial Sharpe dispersion; anything short yields the literal sentinel
  ``{"dsr": "DSR_UNAVAILABLE_FAIL_CLOSED", ...}``.  PBO needs an ALIGNED
  returns matrix of >= 8 configurations (PLAN 6.5); anything short yields
  ``{"pbo": "PBO_UNAVAILABLE_FAIL_CLOSED", ...}``.  CSCV reuses the
  pre-registered implementation in :mod:`research.dsr`.
* **Provenance.**  Every writer embeds ``schema_version``,
  ``generated_at_utc`` and sha256 source-hashes of every input file read.
* Score is ONLY meaningful when every hard gate passes; the scorecard
  records ``score_meaningful`` accordingly and never rescues a failed gate.

Sibling-trial descriptor (for FG1 control comparison + FG3 adjacency):
``{"experiment_id": str, "is_control": bool, "price_lookback_days": int|None,
"net_pnl": float, "profit_factor": float|None, "fold_pnls": {...}|None,
"mechanism_pass": bool}``.  Siblings missing any performance field are
recorded under ``notes`` but never counted (fail closed).

A7 audit descriptor: mapping with either integer ``unresolved_high`` +
``unresolved_critical`` fields, or a ``findings`` list of
``{"severity", "resolved"}`` entries; anything else is NOT_TESTED.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from research.dsr import (
    DSR_ESTIMATOR_ID,
    PBO_ESTIMATOR_ID,
    PBO_MIN_CONFIGURATIONS,
    dsr_probability,
    pbo_cscv,
)
from research.portfolio_metrics import daily_returns_from_equity_curve, daily_sharpe

FINALIZER_SCHEMA_VERSION = 1
ARTIFACT_FAMILY = "V7_FINALIZER_A4"

DSR_UNAVAILABLE = "DSR_UNAVAILABLE_FAIL_CLOSED"
PBO_UNAVAILABLE = "PBO_UNAVAILABLE_FAIL_CLOSED"

SKEW_KURT_ESTIMATOR_ID = "PEARSON_MOMENT_SKEW_KURT_BIASED_V1"
DAILY_RETURNS_SOURCE_ID = "PORTFOLIO_LEDGER_EQUITY_LAST_PER_UTC_DAY_V1"

#: Core artifacts a completed runner trial directory must contain.
REQUIRED_TRIAL_ARTIFACTS = (
    "canonical_metrics.json",
    "portfolio_ledger.jsonl",
    "positions.jsonl",
    "funding_cashflows.jsonl",
    "accounting_reconciliation.json",
    "commission_slippage.json",
    "stress_report.json",
)

#: Fixed stress families required by FG5 (PLAN sections 8.4 and 9).
REQUIRED_STRESS_FAMILIES = ("fee_x1_5", "adverse_two_ticks", "extra_one_event_delay")

_FLOAT_TOL = 1e-12


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _read_json(path: Path) -> Any | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def _read_jsonl(path: Path) -> list[dict] | None:
    """Read a JSONL artifact; ``None`` marks unreadable/missing (fail closed)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    except (OSError, ValueError):
        return None


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _source_hashes(paths: Iterable[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in paths:
        digest = _sha256_file(path)
        if digest is not None:
            hashes[path.name] = digest
    return hashes


def _envelope(source_files: Sequence[Path]) -> dict[str, Any]:
    return {
        "schema_version": FINALIZER_SCHEMA_VERSION,
        "artifact_family": ARTIFACT_FAMILY,
        "generated_at_utc": _utc_now_iso(),
        "source_hashes": _source_hashes(source_files),
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")


def _threshold(contract: Mapping[str, Any], key: str) -> tuple[float | None, bool]:
    thresholds = contract.get("thresholds")
    if not isinstance(thresholds, Mapping) or key not in thresholds:
        return None, False
    return _finite(thresholds.get(key)), True


def _compare(measured: float | None, operator: str, threshold: float | None) -> bool | None:
    """Evaluate ``measured <op> threshold``; ``None`` => cannot evaluate."""
    if measured is None or threshold is None:
        return None
    if operator == ">":
        return measured > threshold
    if operator == ">=":
        return measured >= threshold - _FLOAT_TOL
    if operator == "<":
        return measured < threshold
    if operator == "<=":
        return measured <= threshold + _FLOAT_TOL
    if operator == "==":
        return abs(measured - threshold) <= _FLOAT_TOL
    if operator == "!=":
        return abs(measured - threshold) > _FLOAT_TOL
    raise ValueError(f"unknown_operator:{operator}")


def _untested(check: str, *, threshold: Any, operator: str, reason: str) -> dict[str, Any]:
    """Fail-closed criterion row for an unmeasurable input (never PASS)."""
    return {
        "check": check,
        "measured_value": None,
        "threshold": threshold,
        "operator": operator,
        "pass": False,
        "status": "NOT_TESTED",
        "reason": reason,
    }


def _criterion(
    check: str,
    *,
    measured_value: Any,
    threshold: Any,
    operator: str,
    reason_missing: str,
) -> dict[str, Any]:
    """One measurable criterion row; unmeasurable => fail-closed NOT_TESTED."""
    if isinstance(measured_value, bool) and isinstance(threshold, bool):
        evaluated: bool | None = measured_value == threshold
        measured_out: Any = measured_value
        threshold_out: Any = threshold
    elif isinstance(measured_value, bool) and _finite(threshold) is not None:
        evaluated = _compare(1.0 if measured_value else 0.0, operator, _finite(threshold))
        measured_out = 1.0 if measured_value else 0.0
        threshold_out = _finite(threshold)
    else:
        evaluated = _compare(_finite(measured_value), operator, _finite(threshold))
        measured_out = _finite(measured_value)
        threshold_out = _finite(threshold)
    if evaluated is None:
        return _untested(check, threshold=threshold_out, operator=operator,
                         reason=reason_missing)
    return {
        "check": check,
        "measured_value": measured_out,
        "threshold": threshold_out,
        "operator": operator,
        "pass": bool(evaluated),
        "status": "PASS" if evaluated else "FAIL",
        "reason": None if evaluated else f"criterion_failed:{check}",
    }


def _gate(gate_id: str, title: str, criteria: Sequence[Mapping[str, Any]],
          reasons: Sequence[str], *, tested: bool) -> dict[str, Any]:
    criteria_pass = bool(criteria) and all(row["pass"] for row in criteria)
    if not tested or not criteria:
        status, verdict = "FAIL", False
    else:
        status, verdict = ("PASS" if criteria_pass else "FAIL"), criteria_pass
    return {
        "gate": gate_id,
        "title": title,
        "status": status,
        "pass": verdict,
        "criteria": [dict(row) for row in criteria],
        "reasons": list(reasons),
    }


def _net_funding_pnl(cashflows: list[dict] | None) -> float | None:
    if cashflows is None:
        return None
    values = [_finite(row.get("cashflow")) for row in cashflows]
    if not values or any(v is None for v in values):
        return None
    return math.fsum(float(v) for v in values)


def _positive_aggregate_shares(
    closed_legs: Sequence[Mapping[str, Any]], key_field: str
) -> tuple[dict[str, float], str | None, float | None]:
    """Positive-aggregate PnL shares grouped by ``key_field`` (FG3).

    Denominator: SUM over legs with pnl > 0
    (POSITIVE_AGGREGATE_PNL_ONLY_V1).  Returns ``(shares, top_key,
    top_share)``; no positive PnL => ``({}, None, None)``.
    """
    aggregates: dict[str, float] = {}
    for leg in closed_legs:
        value = _finite(leg.get("canonical_pnl", leg.get("pnl")))
        if value is None or value <= 0.0:
            continue
        key = str(leg.get(key_field))
        aggregates[key] = aggregates.get(key, 0.0) + value
    total = math.fsum(aggregates.values())
    if total <= 0.0:
        return {}, None, None
    shares = {key: value / total for key, value in sorted(aggregates.items())}
    top_key = max(sorted(shares), key=lambda k: shares[k])
    return shares, top_key, shares[top_key]


def _canonical_of(exp_dir: Path) -> Mapping[str, Any] | None:
    doc = _read_json(exp_dir / "canonical_metrics.json")
    return doc if isinstance(doc, Mapping) else None


def _closed_legs_of(exp_dir: Path) -> list[dict] | None:
    return _read_jsonl(exp_dir / "positions.jsonl")


# --------------------------------------------------------------------------- #
# 1. concentration report
# --------------------------------------------------------------------------- #
def build_concentration_report(
    closed_legs: Sequence[Mapping[str, Any]] | None,
    *,
    source_path: Path | None = None,
) -> dict[str, Any]:
    """Positive-PnL concentration grouped by ``experiment_fold`` and ``symbol``."""
    sources = [source_path] if source_path is not None else []
    payload = _envelope(sources)
    legs_unreadable = closed_legs is None
    legs = list(closed_legs or [])
    fold_shares, top_fold, top_fold_share = _positive_aggregate_shares(
        legs, "experiment_fold")
    symbol_shares, top_symbol, top_symbol_share = _positive_aggregate_shares(
        legs, "symbol")
    payload.update({
        "definition": ("POSITIVE_AGGREGATE_PNL_ONLY_V1 "
                       "(share = group positive pnl / total positive pnl)"),
        "computed_from": source_path.name if source_path is not None else "closed_legs",
        "legs_used": len(legs),
        "input_status": "UNREADABLE_FAIL_CLOSED" if legs_unreadable else "OK",
        "by_experiment_fold": {
            "shares": fold_shares,
            "top": top_fold,
            "top_share": top_fold_share,
        },
        "by_symbol": {
            "shares": symbol_shares,
            "top": top_symbol,
            "top_share": top_symbol_share,
        },
    })
    return payload


# --------------------------------------------------------------------------- #
# 2. stress manifest
# --------------------------------------------------------------------------- #
def build_stress_manifest(
    exp_dir: Path,
    *,
    expected_symbols: Sequence[str] | None = None,
    expected_folds: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Required stress families (PLAN 8.4 / FG5) vs what actually ran.

    Reads the existing diagnostic ``stress_report.json``; required fixed
    families are ``fee_x1_5``, ``adverse_two_ticks``, ``extra_one_event_delay``
    plus every ``drop_one_symbol_*`` / ``drop_one_fold_*`` variant.  Required
    diagnostics that never ran are emitted as explicit ``executed=false`` rows.
    """
    report_path = exp_dir / "stress_report.json"
    payload = _envelope([report_path])
    report = _read_json(report_path)
    variants: Mapping[str, Any] = {}
    if isinstance(report, Mapping):
        raw = report.get("variants")
        if isinstance(raw, Mapping):
            variants = raw

    def _variant_entry(family: str, report_key: str) -> dict[str, Any]:
        variant = variants.get(report_key)
        executed = bool(isinstance(variant, Mapping) and variant.get("executed") is True)
        return {
            "family": family,
            "report_key": report_key,
            "present": isinstance(variant, Mapping),
            "executed": executed,
            "canonical_pnl": _finite(variant.get("canonical_pnl"))
            if isinstance(variant, Mapping) else None,
        }

    rows: list[dict[str, Any]] = [
        _variant_entry(family, family) for family in REQUIRED_STRESS_FAMILIES
    ]
    seen_symbols: set[str] = set()
    seen_folds: set[str] = set()
    for key in sorted(map(str, variants)):
        if key.startswith("drop_one_symbol"):
            symbol = key.split(":", 1)[-1]
            rows.append(_variant_entry(f"drop_one_symbol_{symbol}", key))
            seen_symbols.add(symbol)
        elif key.startswith("drop_one_fold"):
            fold = key.split(":", 1)[-1]
            rows.append(_variant_entry(f"drop_one_fold_{fold}", key))
            seen_folds.add(fold)
    for symbol in sorted(set(expected_symbols or []) - seen_symbols):
        rows.append({
            "family": f"drop_one_symbol_{symbol}",
            "report_key": f"drop_one_symbol:{symbol}",
            "present": False,
            "executed": False,
            "canonical_pnl": None,
        })
    for fold in sorted(set(expected_folds or []) - seen_folds):
        rows.append({
            "family": f"drop_one_fold_{fold}",
            "report_key": f"drop_one_fold:{fold}",
            "present": False,
            "executed": False,
            "canonical_pnl": None,
        })
    rows.sort(key=lambda row: row["family"])
    missing_executed = [row["family"] for row in rows if not row["executed"]]
    payload.update({
        "required_families_fixed": list(REQUIRED_STRESS_FAMILIES),
        "required_families_drop_one_pattern": ["drop_one_symbol_*", "drop_one_fold_*"],
        "expected_symbols": sorted(set(expected_symbols or [])),
        "expected_folds": sorted(set(expected_folds or [])),
        "variants": rows,
        "all_required_executed": not missing_executed,
        "missing_or_not_executed": missing_executed,
        "input_status": ("OK" if isinstance(report, Mapping)
                         else "STRESS_REPORT_MISSING_OR_UNREADABLE"),
    })
    return payload


# --------------------------------------------------------------------------- #
# 3. statistical haircut (PLAN 6.4 DSR + 6.5 PBO)
# --------------------------------------------------------------------------- #
def _skew_kurtosis(returns: Sequence[float]) -> tuple[float, float] | None:
    """Biased central-moment skew and PEARSON kurtosis (normal == 3)."""
    n = len(returns)
    if n < 3:
        return None
    mean = math.fsum(returns) / n
    m2 = math.fsum((r - mean) ** 2 for r in returns) / n
    m3 = math.fsum((r - mean) ** 3 for r in returns) / n
    m4 = math.fsum((r - mean) ** 4 for r in returns) / n
    if m2 <= 0.0:
        return None
    return m3 / m2 ** 1.5, m4 / (m2 * m2)


def build_statistical_haircut(
    exp_dir: Path,
    *,
    effective_n_trials: int | None = None,
    trial_sharpes: Sequence[float] | None = None,
    pbo_returns_matrix: Mapping[str, Sequence[float]] | None = None,
    ledger_path: Path | None = None,
) -> dict[str, Any]:
    """DSR from daily equity returns in-dir + CSCV PBO on an aligned matrix.

    Fail-closed sentinels per PLAN 6.4/6.5: insufficient DSR inputs =>
    ``{"dsr": "DSR_UNAVAILABLE_FAIL_CLOSED", ...}``; a missing, sub-8-config
    or misaligned matrix => ``{"pbo": "PBO_UNAVAILABLE_FAIL_CLOSED", ...}``.
    """
    ledger_path = ledger_path or (exp_dir / "portfolio_ledger.jsonl")
    payload = _envelope([ledger_path])
    ledger_rows = _read_jsonl(ledger_path)

    daily_returns: dict[str, float] = {}
    returns_reason: str | None = None
    if ledger_rows is None:
        returns_reason = "portfolio_ledger_missing_or_unreadable"
    else:
        curve: list[tuple[int, float]] = []
        for row in ledger_rows:
            ts = _finite(row.get("ts"))
            equity = _finite(row.get("equity"))
            if ts is None or equity is None:
                returns_reason = "ledger_rows_missing_ts_or_equity"
                break
            curve.append((int(ts), equity))
        if returns_reason is None:
            if not curve:
                returns_reason = "empty_ledger"
            else:
                daily_returns = daily_returns_from_equity_curve(curve)
                if len(daily_returns) < 2:
                    returns_reason = "insufficient_daily_returns"

    ordered_returns = [daily_returns[key] for key in sorted(daily_returns)]

    observed_sharpe: float | None = None
    sharpe_reason: str | None = None
    skew_value: float | None = None
    kurtosis_value: float | None = None
    moments_reason: str | None = None
    if ordered_returns:
        observed_sharpe, sharpe_reason = daily_sharpe(ordered_returns)
        moments = _skew_kurtosis(ordered_returns)
        if moments is None:
            moments_reason = "insufficient_observations_or_zero_variance"
        else:
            skew_value, kurtosis_value = moments
    else:
        sharpe_reason = returns_reason
        moments_reason = returns_reason

    n_samples = len(ordered_returns)
    sharpe_unusable = observed_sharpe is None or sharpe_reason is not None
    if sharpe_unusable or skew_value is None or kurtosis_value is None \
            or n_samples < 3 or effective_n_trials is None \
            or not trial_sharpes:
        dsr_block: dict[str, Any] = {
            "dsr": DSR_UNAVAILABLE,
            "estimator_id": DSR_ESTIMATOR_ID,
            "reason": (
                returns_reason or "insufficient_inputs"
                if sharpe_unusable or skew_value is None or kurtosis_value is None
                else "effective_n_trials_missing" if effective_n_trials is None
                else "trial_sharpe_dispersion_missing"
            ),
        }
    else:
        result = dsr_probability(
            sharpe_star_candidate=observed_sharpe,
            sharpe_trials=list(trial_sharpes),
            n_trials=int(effective_n_trials),
            sample_len=n_samples,
            skew=skew_value,
            kurtosis=kurtosis_value,
        )
        if result.get("reason") is not None:
            dsr_block = {
                "dsr": DSR_UNAVAILABLE,
                "estimator_id": DSR_ESTIMATOR_ID,
                "reason": f"dsr_estimator_fail_closed:{result['reason']}",
            }
        else:
            dsr_block = {**result,
                         "input_scale": "DAILY_NON_ANNUALIZED_SHARPE_V1"}

    pbo_block: dict[str, Any]
    if not isinstance(pbo_returns_matrix, Mapping) or not pbo_returns_matrix:
        pbo_block = {
            "pbo": PBO_UNAVAILABLE,
            "estimator_id": PBO_ESTIMATOR_ID,
            "min_configurations_required": PBO_MIN_CONFIGURATIONS,
            "reason": "returns_matrix_missing",
        }
    else:
        configs: dict[str, list[float | None]] = {}
        malformed = False
        for config_id, series in pbo_returns_matrix.items():
            if not isinstance(series, (list, tuple)):
                malformed = True
                break
            configs[str(config_id)] = [_finite(v) for v in series]
        lengths = {len(vals) for vals in configs.values()}
        ragged_or_bad = (
            malformed
            or any(None in vals or not vals for vals in configs.values())
            or len(lengths) != 1
        )
        if ragged_or_bad:
            pbo_block = {
                "pbo": PBO_UNAVAILABLE,
                "estimator_id": PBO_ESTIMATOR_ID,
                "min_configurations_required": PBO_MIN_CONFIGURATIONS,
                "reason": "misaligned_matrix",
            }
        elif len(configs) < PBO_MIN_CONFIGURATIONS:
            pbo_block = {
                "pbo": PBO_UNAVAILABLE,
                "estimator_id": PBO_ESTIMATOR_ID,
                "n_configs": len(configs),
                "min_configurations_required": PBO_MIN_CONFIGURATIONS,
                "reason": "insufficient_configurations",
            }
        else:
            cscv = pbo_cscv({k: [float(x) for x in v]
                             for k, v in configs.items()})
            if cscv.get("verdict") == "NOT_ENOUGH_CONFIGURATIONS" \
                    or cscv.get("pbo") is None:
                pbo_block = {
                    "pbo": PBO_UNAVAILABLE,
                    "estimator_id": PBO_ESTIMATOR_ID,
                    "n_configs": cscv.get("n_configs"),
                    "n_blocks": cscv.get("n_blocks"),
                    "min_configurations_required": PBO_MIN_CONFIGURATIONS,
                    "min_partitions_required": cscv.get("min_partitions_required"),
                    "reason": f"cscv_fail_closed:{cscv.get('reason')}",
                }
            else:
                pbo_block = {
                    **cscv,
                    "rank_rule": "OOS_RANK_OF_IS_BEST_CONFIG_V1",
                    "tie_rule": "CONFIG_ID_LEXICOGRAPHIC_ASC_V1",
                    "seed": None,
                    "alignment_note": "equal-length aligned daily returns per config",
                }

    payload.update({
        "daily_returns_source": DAILY_RETURNS_SOURCE_ID,
        "daily_return_count": n_samples,
        "inputs_status": {
            "daily_returns": returns_reason or "OK",
            "observed_sharpe": sharpe_reason or "OK",
            "moments": moments_reason or "OK",
        },
        "observed_daily_sharpe": observed_sharpe,
        "sharpe_estimator_id": "DAILY_SHARPE_RF0_V1",
        "skew": skew_value,
        "kurtosis": kurtosis_value,
        "skew_kurtosis_estimator_id": SKEW_KURT_ESTIMATOR_ID,
        "sample_len": n_samples,
        "effective_n_trials": (int(effective_n_trials)
                               if effective_n_trials is not None else None),
        "trial_sharpe_count": len(trial_sharpes or []),
        "dsr": dsr_block,
        "pbo": pbo_block,
    })
    return payload


# --------------------------------------------------------------------------- #
# 4. reproduction report
# --------------------------------------------------------------------------- #
def build_reproduction_report(comparison_paths: Sequence[str | Path] | None) -> dict[str, Any]:
    """PASS iff EVERY provided ``comparison.json`` carries ``all_match: true``.

    Empty input or an unreadable comparison fails closed.
    """
    paths = [Path(p) for p in (comparison_paths or [])]
    payload = _envelope(paths)
    entries: list[dict[str, Any]] = []
    for path in paths:
        doc = _read_json(path)
        digest = _sha256_file(path)
        if not isinstance(doc, Mapping):
            entries.append({
                "path": str(path),
                "sha256": digest,
                "exists": path.is_file(),
                "all_match": False,
                "failed_checks": [],
                "status": "MISSING_OR_UNREADABLE_FAIL_CLOSED",
            })
            continue
        checks = doc.get("checks")
        failed_checks = sorted(k for k, v in checks.items() if v is not True) \
            if isinstance(checks, Mapping) else []
        all_match = doc.get("all_match") is True
        entries.append({
            "path": str(path),
            "sha256": digest,
            "exists": True,
            "source_experiment_id": doc.get("source_experiment_id"),
            "verify_id": doc.get("verify_id"),
            "all_match": all_match,
            "failed_checks": [] if all_match else failed_checks,
            "status": "MATCH" if all_match else "MISMATCH",
        })
    overall = bool(entries) and all(entry["all_match"] for entry in entries)
    payload.update({
        "entries": entries,
        "n_comparisons": len(entries),
        "pass": overall,
        "rule": ("pass iff all_match true for EVERY entry; "
                 "empty/missing input fails closed"),
        "reason": None if overall else (
            "no_comparisons_provided" if not entries
            else "one_or_more_comparisons_not_all_match"),
    })
    return payload


# --------------------------------------------------------------------------- #
# 5. final gate rows FG0..FG7 (PLAN section 9)
# --------------------------------------------------------------------------- #
def _fg0_integrity(exp_dir: Path, reasons: list[str]) -> dict[str, Any]:
    missing = [name for name in REQUIRED_TRIAL_ARTIFACTS
               if not (exp_dir / name).is_file()]
    criteria: list[dict[str, Any]] = []

    criteria.append(_criterion(
        "required_artifacts_complete",
        measured_value=float(len(missing)), threshold=0.0, operator="==",
        reason_missing="artifact_presence_unverifiable"))
    if missing:
        reasons.append(f"missing_artifacts:{','.join(missing)}")

    hashes_doc = _read_json(exp_dir / "artifact_hashes.json")
    recorded = (hashes_doc.get("hashes")
                if isinstance(hashes_doc, Mapping) else None)
    if not isinstance(recorded, Mapping):
        reason = "artifact_hashes_missing_or_malformed"
        reasons.append(reason)
        criteria.append(_untested("artifact_hashes_cover_inputs",
                                  threshold=0.0, operator="==", reason=reason))
        criteria.append(_untested("artifact_hashes_recompute_match",
                                  threshold=0.0, operator="==", reason=reason))
    else:
        absent = sorted(name for name in REQUIRED_TRIAL_ARTIFACTS
                        if name not in recorded)
        criteria.append(_criterion(
            "artifact_hashes_cover_inputs", measured_value=float(len(absent)),
            threshold=0.0, operator="==",
            reason_missing="artifact_hashes_coverage_unverifiable"))
        mismatches, unverifiable = [], []
        for name in sorted(recorded):
            actual = _sha256_file(exp_dir / str(name))
            if actual is None:
                unverifiable.append(str(name))
            elif actual != recorded[name]:
                mismatches.append(str(name))
        criteria.append(_criterion(
            "artifact_hashes_recompute_match", measured_value=float(len(mismatches)),
            threshold=0.0, operator="==",
            reason_missing="artifact_hash_recompute_unverifiable"))
        if mismatches:
            reasons.append(f"hash_mismatch:{','.join(mismatches)}")
        if unverifiable:
            reasons.append(f"hash_target_absent:{','.join(unverifiable)}")

    ledger_rows = _read_jsonl(exp_dir / "portfolio_ledger.jsonl")
    criteria.append(_criterion(
        "ledger_nonempty",
        measured_value=(float(len(ledger_rows)) if ledger_rows is not None else None),
        threshold=0.0, operator=">",
        reason_missing="portfolio_ledger_missing_or_unreadable"))
    return _gate("FG0", "Integrity (artifacts complete, hashes verified)",
                 criteria, reasons, tested=True)


def _fg1_mechanism(
    exp_dir: Path,
    contract: Mapping[str, Any],
    sibling_trials: Sequence[Mapping[str, Any]] | None,
    own_net_pnl: float | None,
    reasons: list[str],
) -> dict[str, Any]:
    criteria: list[dict[str, Any]] = []
    direction = contract.get("direction")
    if direction not in ("normal", "reverse"):
        reason = "direction_missing_in_resolved_contract"
        reasons.append(reason)
        criteria.append(_untested("funding_sign_matches_hypothesis",
                                  threshold=True, operator="==", reason=reason))
    else:
        cashflows = _read_jsonl(exp_dir / "funding_cashflows.jsonl")
        net_funding = _net_funding_pnl(cashflows)
        expected_positive = direction == "normal"
        operator = ">" if expected_positive else "<"
        if net_funding is None:
            reason = "funding_cashflows_missing_or_unreadable"
            reasons.append(reason)
            criteria.append(_untested("funding_sign_matches_hypothesis",
                                      threshold="positive" if expected_positive
                                      else "negative",
                                      operator=operator, reason=reason))
        else:
            sign_ok = (net_funding > 0.0) if expected_positive else (net_funding < 0.0)
            criteria.append({
                "check": "funding_sign_matches_hypothesis",
                "measured_value": net_funding,
                "threshold": "positive" if expected_positive else "negative",
                "operator": operator,
                "pass": sign_ok,
                "status": "PASS" if sign_ok else "FAIL",
                "reason": None if sign_ok else "funding_sign_violates_hypothesis",
            })

    siblings = [s for s in (sibling_trials or []) if isinstance(s, Mapping)]
    normals = [s for s in siblings if s.get("is_control") is not True]
    controls = [s for s in siblings if s.get("is_control") is True]
    own_is_control = contract.get("direction") == "reverse"
    reference_pool = normals if own_is_control else controls
    label = ("control_underperforms_normal" if own_is_control
             else "reverse_control_not_better")
    if not reference_pool:
        reason = ("no_normal_sibling_for_comparison" if own_is_control
                  else "reverse_control_evidence_missing")
        reasons.append(reason)
        criteria.append(_untested(label, threshold=own_net_pnl,
                                  operator="<=", reason=reason))
    else:
        ref_pnl = _finite(reference_pool[0].get("net_pnl"))
        if ref_pnl is None or own_net_pnl is None:
            reason = "control_comparison_pnl_unavailable"
            reasons.append(reason)
            criteria.append(_untested(label, threshold=own_net_pnl,
                                      operator="<=", reason=reason))
        else:
            criteria.append(_criterion(
                label, measured_value=ref_pnl, threshold=own_net_pnl,
                operator="<=", reason_missing="control_comparison_pnl_unavailable"))
    return _gate("FG1", "Mechanism (hypothesis sign; control does not beat treatment)",
                 criteria, reasons, tested=True)


def _fg2_performance(
    canonical_metrics: Mapping[str, Any] | None,
    contract: Mapping[str, Any],
    reasons: list[str],
) -> tuple[dict[str, Any], float | None, float | None]:
    """Returns ``(gate_row, total_pnl, profit_factor)``."""
    criteria: list[dict[str, Any]] = []
    if not isinstance(canonical_metrics, Mapping):
        reasons.append("canonical_metrics_missing_or_unreadable")
        return (_gate("FG2", "Performance (net PnL, PF, folds)",
                      [], reasons, tested=False), None, None)

    total_pnl = _finite(canonical_metrics.get("total_pnl"))
    pf_doc = canonical_metrics.get("pf_position_level")
    pf = _finite(pf_doc.get("profit_factor")) if isinstance(pf_doc, Mapping) else None
    min_pf, have_min_pf = _threshold(contract, "min_profit_factor")

    criteria.append(_criterion(
        "net_pnl_positive", measured_value=total_pnl, threshold=0.0,
        operator=">", reason_missing="total_pnl_missing"))
    if total_pnl is None:
        reasons.append("total_pnl_missing")

    if not have_min_pf:
        reasons.append("min_profit_factor_threshold_missing")
    criteria.append(_criterion(
        "profit_factor_at_least_minimum", measured_value=pf, threshold=min_pf,
        operator=">=", reason_missing=(
            "profit_factor_missing" if have_min_pf
            else "min_profit_factor_threshold_missing")))

    fold_pnls = canonical_metrics.get("fold_pnls")
    if isinstance(fold_pnls, Mapping) and fold_pnls:
        negative_folds = [
            fold_id for fold_id in sorted(fold_pnls)
            if (_finite(fold_pnls[fold_id]) is None) or _finite(fold_pnls[fold_id]) <= 0.0
        ]
        criteria.append(_criterion(
            "no_negative_fold", measured_value=float(len(negative_folds)),
            threshold=0.0, operator="==", reason_missing="fold_pnls_missing"))
        if negative_folds:
            reasons.append(f"negative_folds:{','.join(negative_folds)}")
    else:
        reasons.append("fold_pnls_missing_or_empty")
        criteria.append(_untested("no_negative_fold", threshold=0.0, operator="==",
                                  reason="fold_pnls_missing_or_empty"))
    return (_gate("FG2", "Performance (net PnL, PF, folds)", criteria, reasons,
                  tested=True), total_pnl, pf)


def _adjacent_lookback_count(
    sibling_trials: Sequence[Mapping[str, Any]] | None,
    contract: Mapping[str, Any],
    min_pf: float | None,
    reasons: list[str],
) -> float | None:
    """Distinct adjacent positive lookbacks among same-family normal siblings.

    A sibling counts only when it is a non-control with a DIFFERENT
    lookback than this trial and demonstrates mechanism+performance
    (net_pnl>0, PF>=min_pf, no negative fold, mechanism_pass true).
    Anything short is recorded under ``reasons`` and never counted.
    """
    if sibling_trials is None:
        reasons.append("sibling_trials_not_provided")
        return None
    own_lookback = contract.get("price_lookback_days")
    counted_lookbacks: set[Any] = set()
    rejected: list[str] = []
    for index, sibling in enumerate(s for s in sibling_trials if isinstance(s, Mapping)):
        tag = str(sibling.get("experiment_id") or f"sibling[{index}]")
        if sibling.get("is_control") is True:
            rejected.append(f"{tag}:is_control")
            continue
        lookback = sibling.get("price_lookback_days")
        if own_lookback is not None and lookback == own_lookback:
            rejected.append(f"{tag}:same_lookback_as_self")
            continue
        net_pnl = _finite(sibling.get("net_pnl"))
        pf = _finite(sibling.get("profit_factor"))
        if net_pnl is None or net_pnl <= 0.0:
            rejected.append(f"{tag}:non_positive_or_unknown_net_pnl")
            continue
        if min_pf is None or pf is None or pf < min_pf:
            rejected.append(f"{tag}:pf_below_min_or_unknown")
            continue
        if sibling.get("mechanism_pass") is not True:
            rejected.append(f"{tag}:mechanism_not_passed")
            continue
        fold_pnls = sibling.get("fold_pnls")
        if isinstance(fold_pnls, Mapping) and fold_pnls:
            if any((_finite(v) is None) or _finite(v) <= 0.0 for v in fold_pnls.values()):
                rejected.append(f"{tag}:negative_fold")
                continue
        counted_lookbacks.add(lookback)
    if rejected:
        reasons.append("siblings_not_counted:" + ";".join(rejected))
    return float(len(counted_lookbacks))


def _fg3_funding_concentration(
    exp_dir: Path,
    contract: Mapping[str, Any],
    concentration: Mapping[str, Any],
    sibling_trials: Sequence[Mapping[str, Any]] | None,
    min_pf: float | None,
    reasons: list[str],
) -> dict[str, Any]:
    criteria: list[dict[str, Any]] = []

    cashflows = _read_jsonl(exp_dir / "funding_cashflows.jsonl")
    net_funding = _net_funding_pnl(cashflows)
    criteria.append(_criterion(
        "net_funding_positive", measured_value=net_funding, threshold=0.0,
        operator=">", reason_missing="funding_cashflows_missing_or_unreadable"))

    max_fold_share, have_fold_thr = _threshold(contract, "max_top_fold_share")
    max_symbol_share, have_symbol_thr = _threshold(contract, "max_top_symbol_share")
    min_adjacent, have_adjacent_thr = _threshold(
        contract, "min_adjacent_positive_lookbacks")

    by_fold = concentration.get("by_experiment_fold") or {}
    by_symbol = concentration.get("by_symbol") or {}
    top_fold_share = by_fold.get("top_share") if isinstance(by_fold, Mapping) else None
    top_symbol_share = by_symbol.get("top_share") if isinstance(by_symbol, Mapping) else None

    if not have_fold_thr:
        reasons.append("max_top_fold_share_threshold_missing")
    criteria.append(_criterion(
        "top_positive_fold_share_within_limit", measured_value=top_fold_share,
        threshold=max_fold_share, operator="<=", reason_missing=(
            "max_top_fold_share_threshold_missing" if not have_fold_thr
            else "top_fold_share_unmeasurable")))
    if not have_symbol_thr:
        reasons.append("max_top_symbol_share_threshold_missing")
    criteria.append(_criterion(
        "top_positive_symbol_share_within_limit", measured_value=top_symbol_share,
        threshold=max_symbol_share, operator="<=", reason_missing=(
            "max_top_symbol_share_threshold_missing" if not have_symbol_thr
            else "top_symbol_share_unmeasurable")))

    if not have_adjacent_thr:
        reasons.append("min_adjacent_positive_lookbacks_threshold_missing")
        criteria.append(_untested(
            "adjacent_positive_lookbacks", threshold=min_adjacent, operator=">=",
            reason="min_adjacent_positive_lookbacks_threshold_missing"))
    else:
        adjacent_count = _adjacent_lookback_count(
            sibling_trials, contract, min_pf, reasons)
        criteria.append(_criterion(
            "adjacent_positive_lookbacks", measured_value=adjacent_count,
            threshold=min_adjacent, operator=">=", reason_missing=(
                "adjacency_unmeasurable_no_qualifying_siblings"
                if adjacent_count is None else "adjacency_unmeasurable")))
    return _gate("FG3", "Funding + concentration (net funding, adjacency, shares)",
                 criteria, reasons, tested=True)


def _fg4_risk(canonical_metrics: Mapping[str, Any] | None,
              contract: Mapping[str, Any], reasons: list[str]) -> dict[str, Any]:
    criteria: list[dict[str, Any]] = []
    if not isinstance(canonical_metrics, Mapping):
        reasons.append("canonical_metrics_missing_or_unreadable")
        return _gate("FG4", "Risk (MDD, exposure caps)", [], reasons, tested=False)

    mdd = _finite(canonical_metrics.get("max_drawdown_fraction"))
    max_mdd, have_mdd = _threshold(contract, "max_drawdown")
    if not have_mdd:
        reasons.append("max_drawdown_threshold_missing")
    criteria.append(_criterion(
        "max_drawdown_within_limit", measured_value=mdd, threshold=max_mdd,
        operator="<=", reason_missing=("max_drawdown_threshold_missing"
                                       if not have_mdd else "max_drawdown_missing")))

    breaches = _finite(canonical_metrics.get("margin_breach_rows"))
    criteria.append(_criterion(
        "margin_breach_rows_zero", measured_value=breaches, threshold=0.0,
        operator="==", reason_missing="margin_breach_rows_missing"))

    gross_max = _finite(canonical_metrics.get("gross_max"))
    gross_cap, have_gross = _threshold(contract, "max_gross_exposure")
    if not have_gross:
        reasons.append("max_gross_exposure_threshold_missing")
    criteria.append(_criterion(
        "gross_exposure_within_cap", measured_value=gross_max, threshold=gross_cap,
        operator="<=", reason_missing=("max_gross_exposure_threshold_missing"
                                       if not have_gross else "gross_max_missing")))

    net_abs = _finite(canonical_metrics.get("net_abs_max"))
    net_cap, have_net = _threshold(contract, "max_net_abs_exposure")
    if not have_net:
        reasons.append("max_net_abs_exposure_threshold_missing")
    criteria.append(_criterion(
        "net_abs_exposure_within_cap", measured_value=net_abs, threshold=net_cap,
        operator="<=", reason_missing=("max_net_abs_exposure_threshold_missing"
                                       if not have_net else "net_abs_max_missing")))
    return _gate("FG4", "Risk (MDD, exposure caps)", criteria, reasons, tested=True)


def _fg5_stress(manifest: Mapping[str, Any] | None, reasons: list[str]) -> dict[str, Any]:
    criteria: list[dict[str, Any]] = []
    if not isinstance(manifest, Mapping):
        reasons.append("stress_manifest_missing")
        return _gate("FG5", "Stress", [], reasons, tested=False)
    if manifest.get("input_status") != "OK":
        reasons.append(str(manifest.get("input_status")))
    rows = [row for row in manifest.get("variants") or [] if isinstance(row, Mapping)]
    by_family = {row.get("family"): row for row in rows}

    def _stressed_positive(family: str) -> dict[str, Any]:
        row = by_family.get(family)
        if row is None or row.get("executed") is not True:
            reason = f"stress_variant_not_executed:{family}"
            reasons.append(reason)
            return _untested(f"stress_positive_after_{family}",
                             threshold=0.0, operator=">", reason=reason)
        return _criterion(
            f"stress_positive_after_{family}",
            measured_value=_finite(row.get("canonical_pnl")), threshold=0.0,
            operator=">", reason_missing=f"stress_pnl_unmeasurable:{family}")

    for family in REQUIRED_STRESS_FAMILIES:
        criteria.append(_stressed_positive(family))

    drop_rows = [row for row in rows
                 if str(row.get("family")).startswith(("drop_one_symbol_",
                                                       "drop_one_fold_"))]
    if not drop_rows:
        reason = "drop_one_diagnostics_missing"
        reasons.append(reason)
        criteria.append(_untested("drop_one_dependency_free",
                                  threshold=0.0, operator="==", reason=reason))
    else:
        flips: list[str] = []
        unexecuted: list[str] = []
        for row in drop_rows:
            family = str(row.get("family"))
            if row.get("executed") is not True:
                unexecuted.append(family)
                continue
            pnl = _finite(row.get("canonical_pnl"))
            if pnl is None or pnl <= 0.0:
                flips.append(family)
        criteria.append(_criterion(
            "drop_one_dependency_free", measured_value=float(len(flips)),
            threshold=0.0, operator="==",
            reason_missing="drop_one_pnl_unmeasurable"))
        if unexecuted:
            reasons.append(f"drop_one_not_executed:{','.join(unexecuted)}")
        if flips:
            reasons.append(f"single_point_dependency:{','.join(flips)}")
    return _gate("FG5", "Stress (cost/delay survival; no single-point dependency)",
                 criteria, reasons, tested=True)


def _fg6_reproduction(reproduction: Mapping[str, Any] | None,
                      reasons: list[str]) -> dict[str, Any]:
    criteria: list[dict[str, Any]] = []
    if not isinstance(reproduction, Mapping):
        reasons.append("reproduction_report_missing")
        return _gate("FG6", "Reproduction (independent reruns all-match)",
                     [], reasons, tested=False)
    n_total_raw = reproduction.get("n_comparisons")
    n_total = _finite(n_total_raw)
    entries = reproduction.get("entries") or []
    n_matching = sum(1 for entry in entries
                     if isinstance(entry, Mapping) and entry.get("all_match") is True)
    criteria.append(_criterion(
        "comparisons_all_match", measured_value=float(n_matching),
        threshold=n_total, operator="==",
        reason_missing="comparison_entries_unavailable"))
    if n_total is not None and n_total > 0:
        criteria.append({
            "check": "at_least_one_comparison",
            "measured_value": n_total, "threshold": 0.0, "operator": ">",
            "pass": True, "status": "PASS", "reason": None,
        })
    else:
        reasons.append("no_comparisons_provided")
        criteria.append(_untested("at_least_one_comparison", threshold=0.0,
                                  operator=">", reason="no_comparisons_provided"))
    if not reproduction.get("pass"):
        reasons.append(str(reproduction.get("reason")))
    return _gate("FG6", "Reproduction (independent reruns all-match)",
                 criteria, reasons, tested=True)


def _a7_unresolved_high_critical(audit: Mapping[str, Any] | None) -> tuple[float | None, str | None]:
    if not isinstance(audit, Mapping):
        return None, "audit_payload_missing_or_unreadable"
    high = _finite(audit.get("unresolved_high"))
    critical = _finite(audit.get("unresolved_critical"))
    if high is not None and critical is not None:
        return high + critical, None
    findings = audit.get("findings")
    if isinstance(findings, list):
        total = 0
        for finding in findings:
            if not isinstance(finding, Mapping):
                return None, "malformed_audit_finding"
            severity = str(finding.get("severity", "")).upper()
            if severity in ("HIGH", "CRITICAL") and finding.get("resolved") is not True:
                total += 1
        return float(total), None
    return None, "audit_schema_unknown"


def _fg7_statistical_audit(
    haircut: Mapping[str, Any] | None,
    audit_payload: Mapping[str, Any] | None,
    reasons: list[str],
) -> dict[str, Any]:
    criteria: list[dict[str, Any]] = []
    if not isinstance(haircut, Mapping):
        reasons.append("statistical_haircut_missing")
        contract_ok: bool | None = None
    else:
        dsr_block = haircut.get("dsr")
        pbo_block = haircut.get("pbo")
        dsr_honest = isinstance(dsr_block, Mapping) and (
            dsr_block.get("dsr") == DSR_UNAVAILABLE
            or _finite(dsr_block.get("dsr")) is not None)
        pbo_honest = isinstance(pbo_block, Mapping) and (
            pbo_block.get("pbo") == PBO_UNAVAILABLE
            or _finite(pbo_block.get("pbo")) is not None)
        contract_ok = bool(dsr_honest and pbo_honest)
        if not contract_ok:
            reasons.append("statistical_haircut_contract_violation")
    if contract_ok is None:
        criteria.append(_untested("dsr_pbo_contract_honored", threshold=1.0,
                                  operator="==",
                                  reason="statistical_haircut_missing"))
    else:
        criteria.append({
            "check": "dsr_pbo_contract_honored",
            "measured_value": 1.0 if contract_ok else 0.0,
            "threshold": 1.0, "operator": "==",
            "pass": contract_ok,
            "status": "PASS" if contract_ok else "FAIL",
            "reason": None if contract_ok else "statistical_haircut_contract_violation",
        })

    unresolved, audit_reason = _a7_unresolved_high_critical(audit_payload)
    if audit_reason is not None:
        reasons.append(f"a7_audit:{audit_reason}")
    criteria.append(_criterion(
        "a7_no_unresolved_high_critical", measured_value=unresolved,
        threshold=0.0, operator="==", reason_missing=f"a7_audit:{audit_reason}"
        if audit_reason else "a7_audit_unmeasurable"))
    return _gate("FG7", "Statistical contract + independent audit",
                 criteria, reasons, tested=True)


def build_final_gate_result(
    exp_dir: Path,
    *,
    resolved_contract: Mapping[str, Any],
    sibling_trials: Sequence[Mapping[str, Any]] | None = None,
    concentration: Mapping[str, Any] | None = None,
    stress_manifest: Mapping[str, Any] | None = None,
    haircut: Mapping[str, Any] | None = None,
    reproduction: Mapping[str, Any] | None = None,
    a7_audit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the FG0..FG7 document from already-built sub-artifacts."""
    exp_dir = Path(exp_dir)
    input_paths = [exp_dir / name for name in
                   (*REQUIRED_TRIAL_ARTIFACTS, "artifact_hashes.json")]
    payload = _envelope(input_paths)
    contract_valid = isinstance(resolved_contract, Mapping)
    contract = dict(resolved_contract) if contract_valid else {}
    if not contract_valid:
        payload["input_status"] = "RESOLVED_CONTRACT_MISSING_FAIL_CLOSED"

    canonical_metrics = _canonical_of(exp_dir)
    concentration = concentration if concentration is not None else \
        build_concentration_report(_closed_legs_of(exp_dir),
                                   source_path=exp_dir / "positions.jsonl")
    stress_manifest = stress_manifest if stress_manifest is not None else \
        build_stress_manifest(exp_dir)

    own_net_pnl = (_finite(canonical_metrics.get("total_pnl"))
                   if isinstance(canonical_metrics, Mapping) else None)
    min_pf, _have_min_pf = _threshold(contract, "min_profit_factor")

    fg0_reasons: list[str] = []
    fg0 = _fg0_integrity(exp_dir, fg0_reasons)
    fg1_reasons: list[str] = []
    fg1 = _fg1_mechanism(exp_dir, contract, sibling_trials, own_net_pnl, fg1_reasons)
    fg2_reasons: list[str] = []
    fg2, _total_pnl, _pf = _fg2_performance(canonical_metrics, contract, fg2_reasons)
    fg3_reasons: list[str] = []
    fg3 = _fg3_funding_concentration(exp_dir, contract, concentration,
                                     sibling_trials, min_pf, fg3_reasons)
    fg4_reasons: list[str] = []
    fg4 = _fg4_risk(canonical_metrics, contract, fg4_reasons)
    fg5_reasons: list[str] = []
    fg5 = _fg5_stress(stress_manifest, fg5_reasons)
    fg6_reasons: list[str] = []
    fg6 = _fg6_reproduction(reproduction, fg6_reasons)
    fg7_reasons: list[str] = []
    fg7 = _fg7_statistical_audit(haircut, a7_audit, fg7_reasons)

    gates = [fg0, fg1, fg2, fg3, fg4, fg5, fg6, fg7]
    all_pass = all(gate["pass"] for gate in gates)
    payload.update({
        "experiment_dir": str(exp_dir),
        "gates": gates,
        "all_hard_gates_pass": all_pass,
        "verdict": "LOCK_ELIGIBLE" if all_pass else "NOT_ELIGIBLE",
        "lock_eligibility_rule": ("LOCK_ELIGIBLE only when FG0..FG7 all PASS "
                                  "(PLAN sections 6.3/9/11)"),
        "notes": fg0_reasons + fg1_reasons + fg2_reasons + fg3_reasons
        + fg4_reasons + fg5_reasons + fg6_reasons + fg7_reasons,
    })
    return payload


# --------------------------------------------------------------------------- #
# 6. final scorecard (PLAN section 10)
# --------------------------------------------------------------------------- #
def _score_item(
    item: str,
    points_max: float,
    *,
    raw_value: Any,
    threshold: Any,
    operator: str,
    force_fail_reason: str | None = None,
) -> dict[str, Any]:
    """Binary-award scorecard line with serialized raw value + operator."""
    if force_fail_reason is not None:
        awarded = 0.0
        earned = False
        reason: str | None = force_fail_reason
        measured_num = None
    else:
        if isinstance(raw_value, bool):
            measured_num = 1.0 if raw_value else 0.0
        else:
            measured_num = _finite(raw_value)
        evaluated = _compare(measured_num, operator,
                             None if isinstance(threshold, str) else _finite(threshold))
        earned = bool(evaluated)
        awarded = points_max if earned else 0.0
        reason = None if evaluated is not None else "raw_value_unmeasurable"
    return {
        "item": item,
        "points_max": points_max,
        "awarded": awarded,
        "raw_value": (1.0 if raw_value else 0.0) if isinstance(raw_value, bool)
        else measured_num,
        "threshold": threshold,
        "operator": operator,
        "earned": earned,
        "reason": reason,
    }


def _stress_family_row(manifest: Mapping[str, Any] | None,
                       family: str) -> tuple[float | None, bool]:
    if not isinstance(manifest, Mapping):
        return None, False
    for row in manifest.get("variants") or []:
        if isinstance(row, Mapping) and row.get("family") == family:
            return _finite(row.get("canonical_pnl")), row.get("executed") is True
    return None, False


def build_final_scorecard(
    *,
    gate_result: Mapping[str, Any],
    canonical_metrics: Mapping[str, Any] | None,
    concentration: Mapping[str, Any],
    stress_manifest: Mapping[str, Any] | None,
    haircut: Mapping[str, Any] | None,
    resolved_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """100-point ranking table; meaningful ONLY when every hard gate passes."""
    contract = resolved_contract if isinstance(resolved_contract, Mapping) else {}

    def thr(key: str) -> tuple[float | None, bool]:
        return _threshold(contract, key)

    gates = {gate.get("gate"): gate for gate in gate_result.get("gates", [])
             if isinstance(gate, Mapping)}

    def gate_criterion(gate_id: str, check: str) -> Mapping[str, Any] | None:
        for row in (gates.get(gate_id) or {}).get("criteria", []):
            if isinstance(row, Mapping) and row.get("check") == check:
                return row
        return None

    canonical = canonical_metrics if isinstance(canonical_metrics, Mapping) else {}
    by_fold = concentration.get("by_experiment_fold") or {}
    by_symbol = concentration.get("by_symbol") or {}

    fold_return_values: list[float] = []
    fr = canonical.get("fold_returns")
    if isinstance(fr, Mapping):
        for fold_id in sorted(fr):
            value = _finite(fr[fold_id])
            if value is not None:
                fold_return_values.append(value)
    dispersion = (statistics.stdev(fold_return_values)
                  if len(fold_return_values) >= 2 else None)
    median_fold = (statistics.median(fold_return_values)
                   if fold_return_values else None)
    disp_thr, have_disp = thr("max_fold_return_dispersion")

    observed_sharpe = (haircut.get("observed_daily_sharpe")
                       if isinstance(haircut, Mapping) else None)
    dsr_block = haircut.get("dsr") if isinstance(haircut, Mapping) else None
    pbo_block = haircut.get("pbo") if isinstance(haircut, Mapping) else None
    dsr_value = None
    dsr_force_fail = "statistical_haircut_missing"
    if isinstance(dsr_block, Mapping):
        if dsr_block.get("dsr") == DSR_UNAVAILABLE:
            dsr_force_fail = "DSR_UNAVAILABLE_NO_INTERPOLATION"
        else:
            dsr_value = _finite(dsr_block.get("dsr"))
            dsr_force_fail = None if dsr_value is not None \
                else "raw_value_unmeasurable"
    pbo_value = None
    pbo_force_fail = "statistical_haircut_missing"
    if isinstance(pbo_block, Mapping):
        if pbo_block.get("pbo") == PBO_UNAVAILABLE:
            pbo_force_fail = "PBO_UNAVAILABLE_NO_INTERPOLATION"
        else:
            pbo_value = _finite(pbo_block.get("pbo"))
            pbo_force_fail = None if pbo_value is not None \
                else "raw_value_unmeasurable"

    completeness = gate_criterion("FG0", "required_artifacts_complete")
    hashes_cover = gate_criterion("FG0", "artifact_hashes_cover_inputs")
    hash_match = gate_criterion("FG0", "artifact_hashes_recompute_match")
    folds_neg = gate_criterion("FG2", "no_negative_fold")
    pf_row = gate_criterion("FG2", "profit_factor_at_least_minimum")
    mdd_row = gate_criterion("FG4", "max_drawdown_within_limit")
    adjacent_row = gate_criterion("FG3", "adjacent_positive_lookbacks")

    min_pf_thr, have_min_pf = thr("min_profit_factor")
    max_mdd_thr, have_max_mdd = thr("max_drawdown")
    adjacent_thr, have_adjacent_thr = thr("min_adjacent_positive_lookbacks")
    symbol_thr, have_symbol_thr = thr("max_top_symbol_share")
    fold_thr, have_fold_thr = thr("max_top_fold_share")

    fee_pnl, fee_exec = _stress_family_row(stress_manifest, "fee_x1_5")
    adverse_pnl, adverse_exec = _stress_family_row(stress_manifest, "adverse_two_ticks")
    delay_pnl, delay_exec = _stress_family_row(stress_manifest, "extra_one_event_delay")

    groups: dict[str, Any] = {
        "integrity": {
            "points_max": 20,
            "items": [
                _score_item("pit_and_data_artifacts_complete", 5,
                            raw_value=completeness.get("measured_value")
                            if completeness else None,
                            threshold=0.0, operator="=="),
                _score_item("hashes_provenance_coverage", 5,
                            raw_value=hashes_cover.get("measured_value")
                            if hashes_cover else None,
                            threshold=0.0, operator="=="),
                _score_item("independent_reproduction_all_match", 5,
                            raw_value=gates.get("FG6", {}).get("pass") is True,
                            threshold=1.0, operator="=="),
                _score_item("deterministic_artifacts_hash_recompute", 5,
                            raw_value=hash_match.get("measured_value")
                            if hash_match else None,
                            threshold=0.0, operator="=="),
            ],
        },
        "robustness": {
            "points_max": 20,
            "items": [
                _score_item("all_folds_positive", 8,
                            raw_value=folds_neg.get("measured_value")
                            if folds_neg else None,
                            threshold=0.0, operator="=="),
                _score_item("low_fold_return_dispersion", 6,
                            raw_value=dispersion, threshold=disp_thr, operator="<=",
                            force_fail_reason=(
                                None if (have_disp and dispersion is not None)
                                else "dispersion_threshold_missing"
                                if not have_disp
                                else "dispersion_unmeasurable")),
                _score_item("walk_forward_consistency_median_fold_return", 6,
                            raw_value=median_fold, threshold=0.0, operator=">",
                            force_fail_reason=None if median_fold is not None
                            else "median_fold_return_unmeasurable"),
            ],
        },
        "risk_adjusted": {
            "points_max": 20,
            "items": [
                _score_item("profit_factor", 8,
                            raw_value=pf_row.get("measured_value") if pf_row else None,
                            threshold=min_pf_thr, operator=">=",
                            force_fail_reason=None if have_min_pf
                            else "min_profit_factor_threshold_missing"),
                _score_item("max_drawdown", 6,
                            raw_value=mdd_row.get("measured_value") if mdd_row else None,
                            threshold=max_mdd_thr, operator="<=",
                            force_fail_reason=None if have_max_mdd
                            else "max_drawdown_threshold_missing"),
                _score_item("return_risk_efficiency_daily_sharpe", 6,
                            raw_value=observed_sharpe, threshold=0.0, operator=">",
                            force_fail_reason=None if observed_sharpe is not None
                            else "daily_sharpe_unmeasurable"),
            ],
        },
        "costs": {
            "points_max": 15,
            "items": [
                _score_item("fee_x1_5_survival", 5, raw_value=fee_pnl,
                            threshold=0.0, operator=">",
                            force_fail_reason=None if fee_exec
                            else "stress_variant_not_executed"),
                _score_item("adverse_two_ticks_survival", 5, raw_value=adverse_pnl,
                            threshold=0.0, operator=">",
                            force_fail_reason=None if adverse_exec
                            else "stress_variant_not_executed"),
                _score_item("extra_one_event_delay_survival", 5, raw_value=delay_pnl,
                            threshold=0.0, operator=">",
                            force_fail_reason=None if delay_exec
                            else "stress_variant_not_executed"),
            ],
        },
        "breadth": {
            "points_max": 15,
            "items": [
                _score_item("adjacent_positive_lookbacks", 5,
                            raw_value=adjacent_row.get("measured_value")
                            if adjacent_row else None,
                            threshold=adjacent_thr, operator=">=",
                            force_fail_reason=None if have_adjacent_thr
                            else "min_adjacent_positive_lookbacks_threshold_missing"),
                _score_item("top_symbol_share", 5,
                            raw_value=by_symbol.get("top_share"),
                            threshold=symbol_thr, operator="<=",
                            force_fail_reason=None if have_symbol_thr
                            else "max_top_symbol_share_threshold_missing"),
                _score_item("top_fold_share", 5,
                            raw_value=by_fold.get("top_share"),
                            threshold=fold_thr, operator="<=",
                            force_fail_reason=None if have_fold_thr
                            else "max_top_fold_share_threshold_missing"),
            ],
        },
        "statistical": {
            "points_max": 10,
            "items": [
                _score_item("deflated_sharpe_ratio", 5, raw_value=dsr_value,
                            threshold=thr("dsr_min")[0], operator=">=",
                            force_fail_reason=dsr_force_fail
                            or (None if thr("dsr_min")[1]
                                else "dsr_min_threshold_missing")),
                _score_item("probability_of_backtest_overfitting", 5,
                            raw_value=pbo_value, threshold=thr("pbo_max")[0],
                            operator="<=", force_fail_reason=pbo_force_fail
                            or (None if thr("pbo_max")[1]
                                else "pbo_max_threshold_missing")),
            ],
        },
    }

    for group in groups.values():
        group["points_awarded"] = math.fsum(
            float(item["awarded"]) for item in group["items"])
    total = math.fsum(float(group["points_awarded"]) for group in groups.values())
    all_gates_pass = gate_result.get("all_hard_gates_pass") is True
    band = None
    if all_gates_pass:
        if total < 70:
            band = "REJECT"
        elif total < 80:
            band = "RESEARCH_ONLY_NOT_LOCKABLE"
        elif total < 90:
            band = "LOCK_ELIGIBLE_ALL_GATES_PASS"
        else:
            band = "STRONG_LOCK_ELIGIBLE_STILL_NEEDS_A7_SIGNATURE"

    payload = _envelope([])
    payload.update({
        "groups": groups,
        "total": total,
        "total_possible": 100.0,
        "all_hard_gates_pass": all_gates_pass,
        "score_meaningful": all_gates_pass,
        "band": band,
        "band_rule": ("<70 reject; 70-79 research-only; 80-89 lock-eligible if "
                      "FG0..FG7 PASS; >=90 strong lock-eligible still needs A7"),
        "note": ("Score ranks candidates ONLY after all hard gates PASS; it can "
                 "never rescue a failed gate (PLAN section 10). Unavailable "
                 "statistics score 0 with no interpolation."),
    })
    return payload


# --------------------------------------------------------------------------- #
# 7. orchestrator -- writes ALL SIX final artifacts into exp_dir
# --------------------------------------------------------------------------- #
def finalize_trial(
    exp_dir: str | Path,
    *,
    resolved_contract: Mapping[str, Any],
    sibling_trials: Sequence[Mapping[str, Any]] | None = None,
    effective_n_trials: int | None = None,
    trial_sharpes: Sequence[float] | None = None,
    pbo_returns_matrix: Mapping[str, Sequence[float]] | None = None,
    comparison_paths: Sequence[str | Path] | None = None,
    a7_audit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Finalize one trial directory and write the six PLAN 6.3 artifacts.

    All inputs are explicit so tests can point at synthetic directories.
    Fail-closed: a missing input degrades the affected gate to FAIL/NOT_TESTED
    and the verdict to ``NOT_ELIGIBLE`` -- never to PASS.
    """
    exp_dir = Path(exp_dir)

    canonical_metrics = _canonical_of(exp_dir)
    closed_legs = _closed_legs_of(exp_dir)

    symbols = sorted({str(leg.get("symbol")) for leg in (closed_legs or [])
                      if leg.get("symbol")})
    folds = sorted({str(leg.get("experiment_fold")) for leg in (closed_legs or [])
                    if leg.get("experiment_fold")}
                   | ({str(k) for k in canonical_metrics.get("fold_pnls", {})}
                      if isinstance(canonical_metrics, Mapping)
                      and isinstance(canonical_metrics.get("fold_pnls"), Mapping)
                      else set()))

    concentration = build_concentration_report(
        closed_legs, source_path=exp_dir / "positions.jsonl")
    stress_manifest = build_stress_manifest(
        exp_dir, expected_symbols=symbols, expected_folds=folds)
    haircut = build_statistical_haircut(
        exp_dir,
        effective_n_trials=effective_n_trials,
        trial_sharpes=trial_sharpes,
        pbo_returns_matrix=pbo_returns_matrix,
    )
    reproduction = build_reproduction_report(comparison_paths)
    gate_result = build_final_gate_result(
        exp_dir,
        resolved_contract=resolved_contract,
        sibling_trials=sibling_trials,
        concentration=concentration,
        stress_manifest=stress_manifest,
        haircut=haircut,
        reproduction=reproduction,
        a7_audit=a7_audit,
    )
    scorecard = build_final_scorecard(
        gate_result=gate_result,
        canonical_metrics=canonical_metrics,
        concentration=concentration,
        stress_manifest=stress_manifest,
        haircut=haircut,
        resolved_contract=resolved_contract,
    )
    envelope = _envelope([exp_dir / name for name in
                          (*REQUIRED_TRIAL_ARTIFACTS, "artifact_hashes.json")])
    gate_result.update({
        "generated_at_utc": envelope["generated_at_utc"],
        "source_hashes": envelope["source_hashes"],
    })

    outputs = {
        "final_gate_result.json": gate_result,
        "final_scorecard.json": scorecard,
        "concentration_report.json": concentration,
        "statistical_haircut.json": haircut,
        "reproduction_report.json": reproduction,
        "stress_manifest.json": stress_manifest,
    }
    for filename, document in outputs.items():
        _write_json(exp_dir / filename, document)

    return {
        "experiment_dir": str(exp_dir),
        "artifacts_written": sorted(outputs),
        "all_hard_gates_pass": gate_result["all_hard_gates_pass"],
        "verdict": gate_result["verdict"],
        "gate_statuses": {gate["gate"]: gate["status"]
                          for gate in gate_result["gates"]},
        "score_total": scorecard["total"],
        "score_meaningful": scorecard["score_meaningful"],
        "score_band": scorecard["band"],
    }
