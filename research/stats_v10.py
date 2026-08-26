"""V10 fail-closed statistics: deterministic return matrices, Sharpe inputs,
deflated Sharpe ratio, CSCV PBO and the honest statistical haircut (A5,
PLAN section 6 H07 / section 12).

Closes the V9 A7 audit gaps:

* return matrices are built deterministically (sorted variant keys, pure
  python, canonical-JSON byte-stable serialization) so "missing matrix" can
  no longer silently disable DSR/PBO;
* DSR reuses the frozen Bailey/Lopez de Prado estimator from
  ``research/dsr.py`` (imported, never edited);
* PBO delegates to the pre-registered CSCV implementation with V10
  guardrails; tiny matrices yield explicit failure verdicts;
* :func:`statistical_haircut_v10` refuses to certify a haircut from a stale
  effective trial count below the current denominator (V9 regression: N=112
  while the honest ledger held 117).

EVERY public function is fail-closed: insufficient inputs produce
``{"verdict": "UNAVAILABLE_FAIL_CLOSED", "reason": ...}`` objects — never a
number, never an exception, never inferred credit.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from research.dsr import (
    DSR_ESTIMATOR_ID,
    PBO_ESTIMATOR_ID,
    PBO_MAX_ACCEPTABLE,
    PBO_MIN_CONFIGURATIONS,
    PBO_MIN_PARTITIONS,
    dsr_probability as _dsr_probability,
    pbo_cscv as _pbo_cscv,
)
from research.contract_v10 import BASE_DENOMINATOR_V10

VERDICT_UNAVAILABLE = "UNAVAILABLE_FAIL_CLOSED"
VERDICT_OK = "OK"

MATRIX_SCHEMA_VERSION = "v10.returns_matrix.v1"
HAIRCUT_ESTIMATOR_ID = "HAIRCUT_SQRT_DENOMINATOR_GROWTH_V1"


def _unavailable(reason: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "verdict": VERDICT_UNAVAILABLE,
        "reason": reason,
        "estimator_ids": {"matrix": MATRIX_SCHEMA_VERSION},
    }
    payload.update(extra)
    return payload


# --------------------------------------------------------------------------- #
# Deterministic returns matrix (pure python, pandas-free)
# --------------------------------------------------------------------------- #
def build_returns_matrix(
    period_returns_by_variant: Mapping[str, Sequence[float]] | None,
) -> dict[str, Any]:
    """Deterministic variant x period returns matrix from a mapping.

    Variants are ordered by SORTED key so two constructions from the same
    data (insertion order irrelevant) produce byte-identical canonical
    payloads. Rows = variants (sorted), columns = periods.
    """
    if not isinstance(period_returns_by_variant, Mapping) or not period_returns_by_variant:
        return _unavailable("empty_or_invalid_input")
    variants = sorted(str(key) for key in period_returns_by_variant)
    if any(not str(k).strip() for k in period_returns_by_variant):
        return _unavailable("blank_variant_key")
    if len(set(variants)) != len(variants):
        return _unavailable("duplicate_variant_keys")

    matrix: list[list[float]] = []
    width: int | None = None
    for variant in variants:
        series = period_returns_by_variant[variant]
        if not isinstance(series, Sequence) or isinstance(series, (str, bytes)):
            return _unavailable(f"variant_not_a_sequence:{variant}")
        row: list[float] = []
        for idx, value in enumerate(series):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return _unavailable(f"non_numeric_return_value:{variant}:{idx}")
            value_f = float(value)
            if not math.isfinite(value_f):
                return _unavailable(f"non_finite_return_value:{variant}:{idx}")
            row.append(value_f)
        if not row:
            return _unavailable(f"empty_variant_series:{variant}")
        if width is None:
            width = len(row)
        elif len(row) != width:
            return _unavailable("ragged_matrix")
        matrix.append(row)

    payload = {
        "verdict": VERDICT_OK,
        "schema_version": MATRIX_SCHEMA_VERSION,
        "variants": variants,
        "matrix": matrix,
        "n_variants": len(variants),
        "n_periods": width,
    }
    digest = hashlib.sha256(
        json.dumps(
            {k: v for k, v in payload.items() if k != "canonical_sha256"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        **payload,
        "canonical_sha256": digest,
    }


def serialize_matrix_payload(payload: Mapping[str, Any]) -> str:
    """Canonical byte-stable JSON text for a matrix payload."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_matrix_payload(text: str | bytes) -> dict[str, Any]:
    """Inverse of :func:`serialize_matrix_payload`; round-trip verified.

    Raises ``ValueError`` if the parsed payload does not re-serialize to the
    exact same bytes (tamper evidence), or if the verdict is unavailable.
    """
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    payload = json.loads(text)
    if not isinstance(payload, Mapping):
        raise ValueError("matrix_payload_not_a_mapping")
    if serialize_matrix_payload(payload) != text:
        raise ValueError("matrix_round_trip_not_byte_stable")
    if payload.get("verdict") != VERDICT_OK:
        raise ValueError("matrix_payload_unavailable_fail_closed")
    expected = hashlib.sha256(
        json.dumps(
            {k: v for k, v in payload.items() if k != "canonical_sha256"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if payload.get("canonical_sha256") != expected:
        raise ValueError("matrix_canonical_sha256_mismatch")
    return payload


# --------------------------------------------------------------------------- #
# Sharpe inputs per variant
# --------------------------------------------------------------------------- #
def _moments(series: Sequence[float]) -> tuple[float, float, float, float]:
    n = len(series)
    mean = math.fsum(series) / n
    centered = [x - mean for x in series]
    m2 = math.fsum(c * c for c in centered) / n
    m3 = math.fsum(c * c * c for c in centered) / n
    m4 = math.fsum(c * c * c * c for c in centered) / n
    skew = m3 / m2**1.5 if m2 > 0 else 0.0
    kurtosis = m4 / (m2 * m2) if m2 > 0 else 3.0
    return mean, math.sqrt(m2), skew, kurtosis


def sharpe_inputs(matrix_payload: Any) -> dict[str, Any]:
    """Per-variant mean / sample-std / count / per-period Sharpe summary.

    Fail-closed when the payload is not an OK matrix, any variant has < 2
    observations, or any variant has zero variance (a zero-variance variant
    would fabricate infinite Sharpe).
    """
    if (
        not isinstance(matrix_payload, Mapping)
        or matrix_payload.get("verdict") != VERDICT_OK
        or not isinstance(matrix_payload.get("matrix"), list)
        or not isinstance(matrix_payload.get("variants"), list)
    ):
        return _unavailable("invalid_matrix_payload")
    variants = matrix_payload["variants"]
    matrix = matrix_payload["matrix"]
    if len(variants) != len(matrix) or len(variants) == 0:
        return _unavailable("invalid_matrix_payload_shape")

    inputs: list[dict[str, Any]] = []
    for variant, row in zip(variants, matrix):
        count = len(row)
        if count < 2:
            return _unavailable(f"insufficient_observations:{variant}:{count}<2")
        mean, pop_std, skew, kurtosis = _moments(row)
        sample_var = math.fsum((x - mean) ** 2 for x in row) / (count - 1)
        sample_std = math.sqrt(sample_var)
        constant_series = min(row) == max(row)
        if sample_std == 0.0 or constant_series:
            return _unavailable(f"zero_variance_variant:{variant}")
        inputs.append(
            {
                "variant": variant,
                "count": count,
                "mean_per_period": mean,
                "std_sample": sample_std,
                "sharpe_per_period": mean / sample_std,
                "skew_population_g1": skew,
                "kurtosis_pearson": kurtosis,
            }
        )
    return {
        "verdict": VERDICT_OK,
        "estimator_id": "SHARPE_INPUTS_V10_V1",
        "n_variants": len(variants),
        "n_periods": len(matrix[0]),
        "inputs": inputs,
    }


# --------------------------------------------------------------------------- #
# Deflated Sharpe Ratio (Bailey / Lopez de Prado via research.dsr)
# --------------------------------------------------------------------------- #
def deflated_sharpe_ratio(
    sharpe_star_candidate: float,
    sharpe_trials: Sequence[float] | None,
    n_trials: int,
    sample_len: int,
    skew: float,
    kurtosis: float,
) -> dict[str, Any]:
    """Fail-closed wrapper over the frozen ``DSR_BAILEY_LOPEZDEPRADO_V1``.

    Same formulas and id as ``research/dsr.py::dsr_probability`` (imported,
    never edited). Any degeneracy the estimator reports becomes an explicit
    ``UNAVAILABLE_FAIL_CLOSED`` object here — no number is awarded.
    """
    if not isinstance(sharpe_star_candidate, (int, float)) or isinstance(
        sharpe_star_candidate, bool
    ):
        return _unavailable("candidate_sharpe_not_numeric", estimator_id=DSR_ESTIMATOR_ID)
    result = _dsr_probability(
        float(sharpe_star_candidate),
        sharpe_trials,
        n_trials,
        sample_len,
        skew,
        kurtosis,
    )
    reason = result.get("reason")
    if reason is not None or result.get("dsr") is None:
        return _unavailable(
            str(reason or "dsr_unavailable"), estimator_id=DSR_ESTIMATOR_ID
        )
    return {
        "verdict": VERDICT_OK,
        "dsr": result["dsr"],
        "sr0": result["sr0"],
        "z_statistic": result["z_statistic"],
        "trial_variance": result["trial_variance"],
        "effective_n_trials": result["effective_n_trials"],
        "sample_len": result["sample_len"],
        "skew": result["skew"],
        "kurtosis": result["kurtosis"],
        "estimator_id": DSR_ESTIMATOR_ID,
    }


# --------------------------------------------------------------------------- #
# CSCV Probability of Backtest Overfitting on the returns matrix
# --------------------------------------------------------------------------- #
def pbo_cscv(matrix_payload: Any, n_partitions: int = 16) -> dict[str, Any]:
    """PBO via combinatorially symmetric cross-validation on the matrix.

    Delegates block aggregation + logit ranking to the pre-registered
    ``research/dsr.py`` implementation. Guardrails: needs >= 8 variants,
    >= 8 partitions (even), and >= n_partitions periods; anything smaller
    yields ``UNAVAILABLE_FAIL_CLOSED`` instead of a fabricated probability.
    """
    if (
        not isinstance(matrix_payload, Mapping)
        or matrix_payload.get("verdict") != VERDICT_OK
    ):
        return _unavailable("invalid_matrix_payload", estimator_id=PBO_ESTIMATOR_ID)
    variants = matrix_payload.get("variants")
    matrix = matrix_payload.get("matrix")
    if (
        not isinstance(variants, list)
        or not isinstance(matrix, list)
        or len(variants) != len(matrix)
        or not variants
    ):
        return _unavailable("invalid_matrix_payload_shape", estimator_id=PBO_ESTIMATOR_ID)
    if isinstance(n_partitions, bool) or not isinstance(n_partitions, int):
        return _unavailable("partitions_must_be_int", estimator_id=PBO_ESTIMATOR_ID)
    n_variants = len(variants)
    n_periods = len(matrix[0]) if matrix else 0
    if n_variants < PBO_MIN_CONFIGURATIONS:
        return _unavailable(
            f"insufficient_configurations:{n_variants}<{PBO_MIN_CONFIGURATIONS}",
            estimator_id=PBO_ESTIMATOR_ID,
            n_variants=n_variants,
        )
    if n_partitions < PBO_MIN_PARTITIONS:
        return _unavailable(
            f"insufficient_partitions:{n_partitions}<{PBO_MIN_PARTITIONS}",
            estimator_id=PBO_ESTIMATOR_ID,
        )
    if n_partitions % 2 != 0:
        return _unavailable("partitions_must_be_even", estimator_id=PBO_ESTIMATOR_ID)
    if any(len(row) != n_periods for row in matrix):
        return _unavailable("ragged_matrix", estimator_id=PBO_ESTIMATOR_ID)
    if n_periods < n_partitions:
        return _unavailable(
            f"insufficient_blocks:{n_periods}<{n_partitions}",
            estimator_id=PBO_ESTIMATOR_ID,
        )

    performance_by_variant = {
        variant: list(row) for variant, row in zip(variants, matrix)
    }
    raw = _pbo_cscv(performance_by_variant, partitions=n_partitions)
    if raw.get("verdict") == "NOT_ENOUGH_CONFIGURATIONS":
        return _unavailable(
            str(raw.get("reason") or "insufficient_configurations_or_partitions"),
            estimator_id=PBO_ESTIMATOR_ID,
            n_configs=raw.get("n_configs"),
            n_blocks=raw.get("n_blocks"),
        )
    pbo_value = raw.get("pbo")
    if pbo_value is None:
        return _unavailable("pbo_uncomputed", estimator_id=PBO_ESTIMATOR_ID)
    return {
        "verdict": VERDICT_OK,
        "pbo": pbo_value,
        "classification": "PASS" if pbo_value <= PBO_MAX_ACCEPTABLE else "FAIL",
        "pbo_max_acceptable": PBO_MAX_ACCEPTABLE,
        "logit_mean": raw.get("logit_mean"),
        "n_combinations": raw.get("n_combinations"),
        "n_configs": raw.get("n_configs"),
        "n_blocks": raw.get("n_blocks"),
        "estimator_id": PBO_ESTIMATOR_ID,
    }


# --------------------------------------------------------------------------- #
# Honest statistical haircut (V9 stale-N regression closed)
# --------------------------------------------------------------------------- #
def statistical_haircut_v10(effective_n: Any, base_n: int = BASE_DENOMINATOR_V10) -> dict[str, Any]:
    """Haircut record for multiple-testing evidence at the CURRENT denominator.

    The honest denominator only grows (117 after V9). A caller passing an
    ``effective_n`` BELOW ``base_n`` is using a stale/shrunk count — the V9
    documentation gap computed haircuts from N=112 while the ledger held
    117 — and this function REFUSES to certify anything (fail-closed,
    zero credit). At ``effective_n == base_n`` the haircut is exactly zero;
    above it the haircut fraction is ``1 - sqrt(base_n / effective_n)``,
    applied multiplicatively to Sharpe-type evidence, and the record notes
    that it must be recomputed whenever the ledger grows.
    """
    if isinstance(effective_n, bool) or not isinstance(effective_n, int) or effective_n < 1:
        return _unavailable(
            "effective_n_must_be_positive_int", estimator_id=HAIRCUT_ESTIMATOR_ID
        )
    if isinstance(base_n, bool) or not isinstance(base_n, int) or base_n < 1:
        return _unavailable(
            "base_n_must_be_positive_int", estimator_id=HAIRCUT_ESTIMATOR_ID
        )
    if effective_n < base_n:
        return _unavailable(
            "stale_or_regressed_denominator",
            estimator_id=HAIRCUT_ESTIMATOR_ID,
            effective_n=effective_n,
            current_denominator=base_n,
            documentation_gap=(
                "V9 gap: haircut was computed from stale effective_n=112 "
                "while the honest historical denominator was 117; "
                "statistics certified against a smaller-than-current "
                "denominator earn zero credit"
            ),
        )
    haircut_fraction = 1.0 - math.sqrt(base_n / effective_n)
    if effective_n == base_n:
        note = (
            f"effective_n matches the current denominator ({base_n}); "
            "no growth haircut applies yet"
        )
    else:
        note = (
            f"denominator grew from {base_n} to {effective_n} scored trials; "
            "haircut must be recomputed whenever MultipleTestingDenominator.N "
            "advances — never cached at a stale N"
        )
    return {
        "verdict": VERDICT_OK,
        "estimator_id": HAIRCUT_ESTIMATOR_ID,
        "effective_n": effective_n,
        "base_denominator": base_n,
        "matches_current_denominator": effective_n == base_n,
        "haircut_fraction": haircut_fraction,
        "applies_to": "multiplicative on Sharpe-type statistical evidence",
        "note": note,
    }
