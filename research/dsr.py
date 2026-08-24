"""Deflated Sharpe Ratio and Probability of Backtest Overfitting (A3, D4).

Sprint V5 multiple-testing corrections (PLAN section 31.4 items 3-4).

* :func:`dsr_probability` -- Bailey & Lopez de Prado "The Deflated Sharpe
  Ratio" (2014).  The benchmark Sharpe ``SR0`` is derived from the variance
  ACROSS all trial Sharpes and the GLOBAL scored-trial count ``n_trials``
  (not the surviving candidates), then the Probabilistic Sharpe Ratio is
  evaluated against it using sample length, skewness and kurtosis:

      SR0 = sqrt(V[SR_trials]) * ((1-g)*Z(1-1/N) + g*Z(1-1/(N*e)))
      DSR = Phi( (SR* - SR0) * sqrt(T-1)
                 / sqrt(1 - g3*SR* + (kappa-1)/4 * SR*^2) )

  with g = Euler-Mascheroni constant, e = Euler number, g3 = skewness,
  kappa = PEARSON kurtosis (3 = normal), T = sample length.
  Estimator id frozen: ``DSR_BAILEY_LOPEZDEPRADO_V1``.

* :func:`pbo_cscv` -- Combinatorially Symmetric Cross-Validation PBO
  (Bailey, Borwein, Lopez de Prado, Zhu "The Probability of Backtest
  Overfitting", 2015).  Verdicts are only issued when the PRE-REGISTERED
  minimum configuration count and partition count are met; otherwise the
  result is ``NOT_ENOUGH_CONFIGURATIONS``.  A fake PASS is impossible.

Both functions are pure: no I/O, no engine imports, deterministic.
"""

from __future__ import annotations

import itertools
import math
import statistics
from typing import Any, Mapping, Sequence

DSR_ESTIMATOR_ID = "DSR_BAILEY_LOPEZDEPRADO_V1"
PBO_ESTIMATOR_ID = "PBO_CSCV_BAILEY_ETAL_V1"

#: Pre-registered minima (V5): a CSCV verdict needs >= 8 configurations and
#: >= 8 partitions. Below that we refuse to issue PASS/FAIL at all.
PBO_MIN_CONFIGURATIONS = 8
PBO_MIN_PARTITIONS = 8

#: Pre-registered overfitting threshold: PBO above this fails the family.
PBO_MAX_ACCEPTABLE = 0.5

_EULER_GAMMA = 0.5772156649015329
_EULER_NUMBER = math.e


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    from statistics import NormalDist

    return NormalDist().inv_cdf(p)


def dsr_probability(
    sharpe_star_candidate: float,
    sharpe_trials: Sequence[float] | None,
    n_trials: int,
    sample_len: int,
    skew: float,
    kurtosis: float,
) -> dict[str, Any]:
    """Deflated Sharpe probability for one candidate among scored trials.

    Parameters
    ----------
    sharpe_star_candidate :
        SR of the candidate being judged (per-period, same scale as trials).
    sharpe_trials :
        Sharpes of ALL scored trials in the family; variance ACROSS these
        calibrates the expected-maximum-under-null benchmark SR0.
    n_trials :
        Global scored-trial count N (>= len(trials)); never just survivors.
    sample_len :
        Number of return observations T behind the candidate Sharpe.
    skew, kurtosis :
        Candidate return skewness and PEARSON kurtosis (normal == 3).

    Returns a dict with ``dsr`` in [0, 1], ``sr0``, ``estimator_id`` and a
    ``reason`` when the measurement is impossible (fail-closed ``None``):

    * ``insufficient_trials``   fewer than 2 trial Sharpes -> no variance;
    * ``insufficient_sample``   sample_len < 2;
    * ``invalid_kurtosis``      Pearson kurtosis <= 1 makes the PSR
                                denominator imaginary (documented edge).
    """
    trials = [float(v) for v in (sharpe_trials or [])]
    n_trials_int = int(n_trials)
    sr_star = float(sharpe_star_candidate)

    if len(trials) < 2:
        return {
            "dsr": None,
            "sr0": None,
            "estimator_id": DSR_ESTIMATOR_ID,
            "reason": "insufficient_trials",
        }
    if sample_len < 2:
        return {
            "dsr": None,
            "sr0": None,
            "estimator_id": DSR_ESTIMATOR_ID,
            "reason": "insufficient_sample",
        }
    if float(kurtosis) <= 1.0:
        return {
            "dsr": None,
            "sr0": None,
            "estimator_id": DSR_ESTIMATOR_ID,
            "reason": "invalid_kurtosis",
        }

    trial_variance = statistics.variance(trials)  # ddof=1 ACROSS trials
    effective_n = max(n_trials_int, len(trials))
    if effective_n < 2:
        return {
            "dsr": None,
            "sr0": None,
            "estimator_id": DSR_ESTIMATOR_ID,
            "reason": "insufficient_trials",
        }
    z1 = _norm_ppf(1.0 - 1.0 / effective_n)
    z2 = _norm_ppf(1.0 - 1.0 / (effective_n * _EULER_NUMBER))
    sr0 = math.sqrt(trial_variance) * (
        (1.0 - _EULER_GAMMA) * z1 + _EULER_GAMMA * z2
    )

    skew_v = float(skew)
    kurt_v = float(kurtosis)
    denominator_sq = 1.0 - skew_v * sr_star + ((kurt_v - 1.0) / 4.0) * sr_star**2
    # Guard tiny negative rounding noise around flat strategies.
    denominator = math.sqrt(max(denominator_sq, 1e-12))
    z_stat = (sr_star - sr0) * math.sqrt(sample_len - 1) / denominator
    return {
        "dsr": _norm_cdf(z_stat),
        "sr0": sr0,
        "z_statistic": z_stat,
        "trial_variance": trial_variance,
        "effective_n_trials": effective_n,
        "sample_len": sample_len,
        "skew": skew_v,
        "kurtosis": kurt_v,
        "estimator_id": DSR_ESTIMATOR_ID,
        "reason": None,
    }


def pbo_cscv(
    performance_by_config: Mapping[str, Sequence[float]] | None,
    *,
    min_configs: int = PBO_MIN_CONFIGURATIONS,
    partitions: int = PBO_MIN_PARTITIONS,
    pbo_max: float = PBO_MAX_ACCEPTABLE,
) -> dict[str, Any]:
    """Combinatorially-Symmetric-CV Probability of Backtest Overfitting.

    ``performance_by_config`` maps config_id -> per-block performance series
    (equal block counts across configs).  All C(S, S/2) symmetric train/test
    splits of the S blocks are enumerated; for each split the best IN-SAMPLE
    config is ranked OUT-of-sample and its logit lambda computed.  PBO =
    fraction of splits where the IS-best config lands below the OOS median.

    Governance (never fake-PASS): with fewer than ``min_configs``
    configurations or fewer than ``partitions`` blocks the verdict is
    ``NOT_ENOUGH_CONFIGURATIONS`` regardless of any measured numbers.
    """
    payload: dict[str, Any] = {
        "pbo": None,
        "verdict": "NOT_ENOUGH_CONFIGURATIONS",
        "estimator_id": PBO_ESTIMATOR_ID,
        "min_configs_required": min_configs,
        "min_partitions_required": partitions,
        "n_configs": 0,
        "n_blocks": 0,
        "n_combinations": 0,
        "reason": "insufficient_configurations_or_partitions",
    }
    if not isinstance(performance_by_config, Mapping) or not performance_by_config:
        return payload

    configs = {str(k): [float(x) for x in value]
               for k, value in performance_by_config.items()}
    n_configs = len(configs)
    block_lengths = {len(series) for series in configs.values()}
    if len(block_lengths) != 1:
        payload["reason"] = "ragged_block_matrix"
        return payload
    n_blocks = block_lengths.pop()
    s_partitions = int(partitions)
    if s_partitions % 2 != 0:
        s_partitions -= 1  # symmetric halves require an even partition count
    payload["n_configs"] = n_configs
    payload["n_blocks"] = n_blocks

    if n_configs < min_configs or n_blocks < max(s_partitions, partitions):
        return payload
    if s_partitions < 2 or s_partitions > n_blocks:
        payload["reason"] = "partitions_exceed_blocks"
        return payload

    config_ids = sorted(configs)
    matrix = {cid: configs[cid] for cid in config_ids}
    half = s_partitions // 2

    def _partition_slice(series: Sequence[float]) -> list[float]:
        """Fold the block series into ``s_partitions`` contiguous chunks."""
        edges = [
            round(i * n_blocks / s_partitions)
            for i in range(s_partitions + 1)
        ]
        return [
            math.fsum(series[edges[i]:edges[i + 1]])
            for i in range(s_partitions)
        ]

    partition_scores = {cid: _partition_slice(series) for cid, series in matrix.items()}

    logits: list[float] = []
    combinations = list(itertools.combinations(range(s_partitions), half))
    for is_parts in combinations:
        oos_parts = tuple(p for p in range(s_partitions) if p not in is_parts)
        is_totals = {
            cid: math.fsum(partition_scores[cid][p] for p in is_parts)
            for cid in config_ids
        }
        oos_totals = {
            cid: math.fsum(partition_scores[cid][p] for p in oos_parts)
            for cid in config_ids
        }
        best_is = max(sorted(is_totals), key=lambda cid: is_totals[cid])
        oos_sorted = sorted(config_ids, key=lambda cid: oos_totals[cid])
        rank = oos_sorted.index(best_is) + 1  # 1..N
        relative_rank = rank / (n_configs + 1)
        logit = math.log(relative_rank / (1.0 - relative_rank))
        logits.append(logit)

    pbo = sum(1 for lam in logits if lam < 0.0) / len(logits)
    payload.update({
        "pbo": pbo,
        "n_combinations": len(combinations),
        "logit_mean": math.fsum(logits) / len(logits),
        "pbo_max_acceptable": pbo_max,
        "reason": None,
    })
    payload["verdict"] = "PASS" if pbo <= pbo_max else "FAIL"
    return payload
