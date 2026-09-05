"""Frozen identity of the A14-V14-A5-BASISLV-PREMFADE family (per-arm digest).

The digest-bearing ``arm_config_id`` identity of each frozen arm, digestible
through the factory-standard
``research.v11.publication_identity.arm_config_digest`` (every
score-affecting arm field -- ``arm_config_id``, ``arm_id``, ``direction``,
funding sign convention, benchmark-exclusion set and the ENTIRE ``config``
mapping -- influences the digest, so anchor, neighbour and causal-control
arms always produce distinct trial keys).

Provenance of the RECORDED digests: the V14 selection freeze
(``research/control/v14_run/selection_freeze_v14.json``, frozen at HEAD
``d16341f``) freezes the three arm ids and their roles but records no
per-arm ``arm_config_digest``.  This implementation lane therefore records
the digests computed from the frozen identities BELOW, at implementation
time, BEFORE any scored metric exists for any V14 cell (the V12/V13
pre-scored-metric convention).  The recorded values are pinned by
``tests/test_v14_family1_basislv.py``; any drift between the recomputed and
recorded digests is surfaced honestly by :func:`frozen_arm_digest_report`
and must fail the suite -- never silently repaired.
"""

from __future__ import annotations

from typing import Any

from research.adapter_v10.protocol import ContractViolation, StrategyIdentity  # noqa: F401 (cycle-break import kept first)
from research.v11.publication_identity import arm_config_digest

from research.v14.families.basislv_premfade.strategy import (
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
    FORMATION_BUCKETS_ANCHOR,
    FORMATION_BUCKETS_NEIGHBOUR,
    GROSS_TARGET,
    LAG_CONVENTION,
    MATRIX_COHORT_HINT,
    MIN_ELIGIBLE,
    NEIGHBOUR_ARM,
    PRICE_ONLY_CLAUSE_TEXT,
    SIGNAL_EVALUATION,
    SIGNAL_NAME,
    SIGNAL_ROUTE,
    STRATEGY_ID,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    FUNDING_SIGN_CONVENTION,
)

#: Shared digest-input text pinned once and referenced by every arm.
_DATA_AUTHORITY = (
    "A9-F staged basis observables, staged_basis_manifest.json "
    "(manifest sha256 3867bdca3162f219d9a62b30b6768997f89a751b7bb86231b1c1175a6e25ee88); "
    "per-file SHA-256 verified at load, fail-closed on mismatch"
)
_SIDE_RULE = (
    "long = floor(n_eligible/3) lowest premium (low/discount tier), short = "
    "floor(n_eligible/3) highest premium (high/premium tier), equal weight "
    "1/(2*floor(n_eligible/3)), gross 1.0, middle flat, ranks ascend by "
    "(b_i, symbol id), min 12 eligible names, max |w| = 0.125 <= 0.30"
)
_OUT_OF_SCOPE = (
    "premiumIndexKlines / markPriceKlines / indexPriceKlines / open interest "
    "/ funding rate are declared out of scope for the signal (proposal "
    "section 10); funding enters ONLY as an identical native settlement "
    "cost, never a signal input"
)

_COMMON: dict[str, Any] = {
    "signal": SIGNAL_NAME,
    "signal_evaluation": SIGNAL_EVALUATION,
    "signal_route": SIGNAL_ROUTE,
    "lag_convention": LAG_CONVENTION,
    "side_rule": _SIDE_RULE,
    "min_eligible": int(MIN_ELIGIBLE),
    "weight_cap_abs": float(CAP_MAX),
    "gross": float(GROSS_TARGET),
    "tie_break": "symbol_id_ascending_on_equal_b_i",
    "decision_clock": DECISION_CLOCK,
    "fill_rule": FILL_RULE,
    "holding_days": 7,
    "folds_contract": FOLDS_CONTRACT,
    "drop_one_pin": DROP_ONE_PIN,
    "window": [WINDOW_START_ISO, WINDOW_END_ISO],
    "data_authority": _DATA_AUTHORITY,
    "signal_inputs_out_of_scope": _OUT_OF_SCOPE,
    "price_only_failure_clause": PRICE_ONLY_CLAUSE_TEXT,
}

#: Frozen per-arm config payloads (digest inputs; canonicalised sorted).
_FROZEN_CONFIGS: dict[str, dict] = {
    ANCHOR_ARM: {
        **_COMMON,
        "formation_buckets": int(FORMATION_BUCKETS_ANCHOR),
        "formation_days": 28,
        "arm_config_id": ARM_CONFIG_IDS[ANCHOR_ARM],
    },
    NEIGHBOUR_ARM: {
        **_COMMON,
        "formation_buckets": int(FORMATION_BUCKETS_NEIGHBOUR),
        "formation_days": 56,
        "arm_config_id": ARM_CONFIG_IDS[NEIGHBOUR_ARM],
    },
    CONTROL_ARM: {
        **_COMMON,
        "formation_buckets": int(FORMATION_BUCKETS_ANCHOR),
        "formation_days": 28,
        "arm_config_id": ARM_CONFIG_IDS[CONTROL_ARM],
        "sign": "inverted",
        "book": "exact sign-inverted anchor book (weights element-wise negated)",
        "falsification": (
            "if BASISLV-PREMFADE-28D-INV passes the incremental gate while the "
            "anchor passes, the premium ordering carries no directional "
            "crowding information, the anchor FAILS and the family is "
            "rejected; the control is never promotable regardless of its own "
            "result (L-V11-3 / L-V12-1)"
        ),
    },
}

#: The RECORDED ``arm_config_digest`` per arm (binding implementation-lane
#: record made before any scored metric exists; equality with the recomputed
#: digest is test-pinned).
BASISLV_ARM_CONFIG_DIGESTS: dict[str, str] = {
    ANCHOR_ARM: "8d7704663b923815e0bb2b201c339c9a2c209875c3348752c721d17265247d52",
    NEIGHBOUR_ARM: "832ccde72cde6bf1a1982fbaad728dbdbd7e21f26a768c389c22de1d1768d4ef",
    CONTROL_ARM: "76f0b0ccba127cef85aa91ebaf4faa4d13fffd5130d2cf6f7e305f53aac46893",
}


def frozen_arm_config(arm_id: str) -> dict:
    """The exact frozen ``config`` payload of one arm (digest input)."""
    arm_id = str(arm_id)
    if arm_id not in _FROZEN_CONFIGS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return dict(_FROZEN_CONFIGS[arm_id])


def frozen_identity(arm_id: str) -> StrategyIdentity:
    """The frozen V14 identity of one arm (digest equality is test-pinned)."""
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
        recorded = BASISLV_ARM_CONFIG_DIGESTS[arm_id]
        report[arm_id] = {
            "computed_from_identity": computed,
            "recorded_in_freeze": recorded,
            "match": bool(computed == recorded),
        }
    return report


__all__ = [
    "BASISLV_ARM_CONFIG_DIGESTS",
    "frozen_arm_config",
    "frozen_arm_digest_report",
    "frozen_identity",
]
