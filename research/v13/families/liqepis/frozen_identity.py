"""Frozen identity of the A13-V13-A5-LIQEPIS family (per-arm digest contract).

The digest-bearing ``arm_config_id`` identity of each frozen arm, digestible
through the factory-standard
``research.v11.publication_identity.arm_config_digest`` (every
score-affecting arm field -- ``arm_config_id``, ``arm_id``, ``direction``,
funding sign convention, benchmark-exclusion set and the ENTIRE ``config``
mapping -- influences the digest, so anchor, neighbour and causal-control
arms always produce distinct trial keys).

Provenance of the RECORDED digests: the V13 selection freeze
(``research/control/v13_run/selection_freeze_v13.json``) freezes the three
arm ids and their roles but records no per-arm ``arm_config_digest``.  This
implementation lane therefore records the digests computed from the frozen
identities BELOW, at implementation time, BEFORE any scored metric exists
for any V13 cell (the same pre-scored-metric convention the V12 freeze v2
reissue used).  The recorded values are pinned by
``tests/test_v13i_liqepis_goldens.py``; any drift between the recomputed
and recorded digests is surfaced honestly by :func:`frozen_arm_digest_report`
and must fail the suite -- never silently repaired.
"""

from __future__ import annotations

from typing import Any

from research.adapter_v10.protocol import ContractViolation, StrategyIdentity
from research.v11.publication_identity import arm_config_digest

from research.v13.families.liqepis.strategy import (
    ANCHOR_ARM,
    ARM_CONFIG_IDS,
    ARM_IDS,
    BENCHMARK_SYMBOL,
    CAP_MAX,
    CONTROL_ARM,
    DECISION_CLOCK,
    DIRECTION,
    DROP_ONE_PIN,
    FAMILY_ID,
    FILL_RULE,
    FOLDS_CONTRACT,
    FORMATION_BARS_ANCHOR,
    FORMATION_BARS_NEIGHBOUR,
    GROSS_TARGET,
    LEGS_PER_SIDE,
    MATRIX_COHORT_HINT,
    MIN_ELIGIBLE,
    NEIGHBOUR_ARM,
    PER_NAME_WEIGHT,
    SIGNAL_NAME,
    STRATEGY_ID,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    FUNDING_SIGN_CONVENTION,
)

#: Frozen per-arm config payloads (digest inputs; canonicalised sorted).
_FROZEN_CONFIGS: dict[str, dict] = {
    ANCHOR_ARM: {
        "signal": SIGNAL_NAME,
        "signal_evaluation": "H = (sum_b q_b**2) / (sum_b q_b)**2; q_b = close x volume",
        "formation_bars": FORMATION_BARS_ANCHOR,
        "legs_per_side": LEGS_PER_SIDE,
        "per_name_weight": PER_NAME_WEIGHT,
        "gross": GROSS_TARGET,
        "weight_cap_abs": CAP_MAX,
        "min_eligible": MIN_ELIGIBLE,
        "book": "long_bottom_tercile_smooth_short_top_tercile_bursty",
        "tie_break": "symbol_id_ascending",
        "decision_clock": DECISION_CLOCK,
        "fill_rule": FILL_RULE,
        "holding_days": 7,
        "folds_contract": FOLDS_CONTRACT,
        "drop_one_pin": DROP_ONE_PIN,
        "window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "data": "bars-only (no OI, mark-price or funding-rate field in any signal)",
    },
    NEIGHBOUR_ARM: {
        "signal": SIGNAL_NAME,
        "signal_evaluation": "H = (sum_b q_b**2) / (sum_b q_b)**2; q_b = close x volume",
        "formation_bars": FORMATION_BARS_NEIGHBOUR,
        "legs_per_side": LEGS_PER_SIDE,
        "per_name_weight": PER_NAME_WEIGHT,
        "gross": GROSS_TARGET,
        "weight_cap_abs": CAP_MAX,
        "min_eligible": MIN_ELIGIBLE,
        "book": "long_bottom_tercile_smooth_short_top_tercile_bursty",
        "tie_break": "symbol_id_ascending",
        "decision_clock": DECISION_CLOCK,
        "fill_rule": FILL_RULE,
        "holding_days": 7,
        "folds_contract": FOLDS_CONTRACT,
        "drop_one_pin": DROP_ONE_PIN,
        "window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "data": "bars-only (no OI, mark-price or funding-rate field in any signal)",
    },
    CONTROL_ARM: {
        "signal": SIGNAL_NAME,
        "signal_evaluation": "H = (sum_b q_b**2) / (sum_b q_b)**2; q_b = close x volume",
        "formation_bars": FORMATION_BARS_ANCHOR,
        "legs_per_side": LEGS_PER_SIDE,
        "per_name_weight": PER_NAME_WEIGHT,
        "gross": GROSS_TARGET,
        "weight_cap_abs": CAP_MAX,
        "min_eligible": MIN_ELIGIBLE,
        "book": "long_bottom_tercile_smooth_short_top_tercile_bursty",
        "tie_break": "symbol_id_ascending",
        "decision_clock": DECISION_CLOCK,
        "fill_rule": FILL_RULE,
        "holding_days": 7,
        "folds_contract": FOLDS_CONTRACT,
        "drop_one_pin": DROP_ONE_PIN,
        "window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "data": "bars-only (no OI, mark-price or funding-rate field in any signal)",
        "sign": "inverted",
        "falsification": (
            "if LIQEPIS-SIGN-INV passes the incremental gate while the anchor "
            "passes, the anchor is a tilt artifact and the family is falsified; "
            "the control is never promotable regardless of its own result"
        ),
    },
}

#: The RECORDED ``arm_config_digest`` per arm (binding implementation-lane
#: record made before any scored metric exists; equality with the recomputed
#: digest is test-pinned).
LIQEPIS_ARM_CONFIG_DIGESTS: dict[str, str] = {
    ANCHOR_ARM: "d7af1b24b2e50555fd5994db79cd0975f5c72eef6c6091e0197654730e40faa6",
    NEIGHBOUR_ARM: "6028040889c20fcd72a6a53d3582269d322a8f43e524f3c1fcb0fae0342f9999",
    CONTROL_ARM: "49ca153a3d320584620e5d1525716b484b359b8c6290d3c0612888675a8ab140",
}


def frozen_arm_config(arm_id: str) -> dict:
    """The exact frozen ``config`` payload of one arm (digest input)."""
    arm_id = str(arm_id)
    if arm_id not in _FROZEN_CONFIGS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return dict(_FROZEN_CONFIGS[arm_id])


def frozen_identity(arm_id: str) -> StrategyIdentity:
    """The frozen V13 identity of one arm (digest equality is test-pinned)."""
    arm_id = str(arm_id)
    if arm_id not in ARM_CONFIG_IDS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return StrategyIdentity(
        strategy_id=STRATEGY_ID,
        family_id=FAMILY_ID,
        arm_config_id=ARM_CONFIG_IDS[arm_id],
        direction=DIRECTION,
        window_start_iso=WINDOW_START_ISO,
        window_end_iso=WINDOW_END_ISO,
        benchmark_symbols_excluded=(BENCHMARK_SYMBOL,),
        funding_sign_convention=FUNDING_SIGN_CONVENTION,
        matrix_cohort_hint=MATRIX_COHORT_HINT,
        arm_id=arm_id,
        config=frozen_arm_config(arm_id),
    )


def frozen_arm_digest_report() -> dict[str, dict[str, Any]]:
    """Recomputed vs recorded ``arm_config_digest`` per arm (honest report)."""
    report: dict[str, dict[str, Any]] = {}
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        computed = arm_config_digest(identity, arm_id=arm_id)
        recorded = LIQEPIS_ARM_CONFIG_DIGESTS[arm_id]
        report[arm_id] = {
            "computed_from_identity": computed,
            "recorded_in_freeze": recorded,
            "match": bool(computed == recorded),
        }
    return report


__all__ = [
    "LIQEPIS_ARM_CONFIG_DIGESTS",
    "frozen_arm_config",
    "frozen_arm_digest_report",
    "frozen_identity",
]
