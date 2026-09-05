"""Frozen identity of the A14-V14-A8-OICYC family (per-arm digest contract).

The digest-bearing ``arm_config_id`` identity of each frozen arm, digestible
through the factory-standard
``research.v11.publication_identity.arm_config_digest`` (every
score-affecting arm field -- ``arm_config_id``, ``arm_id``, ``direction``,
funding sign convention, benchmark-exclusion set and the ENTIRE ``config``
mapping -- influences the digest, so anchor, neighbour and causal-control
arms always produce distinct trial keys).

Provenance of the RECORDED digests: the V14 selection freeze
(``research/control/v14_run/selection_freeze_v14.json``) freezes the three
arm ids and their roles but records no per-arm ``arm_config_digest``.  This
implementation lane therefore records the digests computed from the frozen
identities BELOW, at implementation time, BEFORE any scored metric exists
for any V14 cell (the same pre-scored-metric convention the V12 freeze v2
reissue and the V13 implementation lanes used).  The recorded values are
pinned by ``tests/test_v14_family2_oicyc.py``; any drift between the
recomputed and recorded digests is surfaced honestly by
:func:`frozen_arm_digest_report` and must fail the suite -- never silently
repaired.

CONFIRMATORY status (plan Section 1.1): every arm config carries the
preregistered ``scored_status: CONFIRMATORY`` field and the Section 1.1
disclosure, so the status is part of the digest input and is carried into
the verdict record and the observed/published denominator accounting by the
driver (proposal sections 2/12).
"""

from __future__ import annotations

from typing import Any

from research.adapter_v10.protocol import ContractViolation, StrategyIdentity

from research.v14.families.oicyc.strategy import (
    ANCHOR_ARM,
    ARM_CONFIG_IDS,
    ARM_IDS,
    BENCHMARK_SYMBOL,
    CAP_MAX,
    CONFIRMATORY,
    CONTROL_ARM,
    DECISION_CLOCK,
    DIRECTION,
    FAMILY_ID,
    FIRST_STAMP_ISO,
    FOLDS_CONTRACT,
    FUNDING_SIGN_CONVENTION,
    LEG_GROSS,
    MATRIX_COHORT_HINT,
    MIN_ELIGIBLE,
    MIN_SIDE_MEMBERS,
    NEIGHBOUR_ARM,
    SECTION_1_1_DISCLOSURE,
    STRATEGY_ID,
    WARMUP_ROWS_FIRST_STAMP,
    WINDOW_END_ISO,
    WINDOW_ROWS_ANCHOR,
    WINDOW_ROWS_CONTROL,
    WINDOW_ROWS_NEIGHBOUR,
    WINDOW_START_ISO,
)

_BOOK_COMMON: dict[str, Any] = {
    "book": "oicyc_hysteresis_tercile_median_exit",
    "leg_gross": LEG_GROSS,
    "weight_cap_abs": CAP_MAX,
    "gross_max": 1.0,
    "min_side_members": MIN_SIDE_MEMBERS,
    "min_eligible_structural": MIN_ELIGIBLE,
    "cross_section": "complete declared-universe cross-section required per window (fail-closed, no partial aggregate)",
    "exit_rule": "held side exits only when the rank crosses beyond the median (exit = flip); buffer never forces an exit",
    "tie_break": "symbol_id_ascending",
    "decision_clock": DECISION_CLOCK,
    "warmup_rows_first_stamp": WARMUP_ROWS_FIRST_STAMP,
    "first_stamp_iso": FIRST_STAMP_ISO,
    "folds_contract": FOLDS_CONTRACT,
    "window": [WINDOW_START_ISO, WINDOW_END_ISO],
    "universe_size": 19,
    "benchmark": "BTCUSDT context-only (never ranked, never held, never inside the aggregate)",
    "data": (
        "staged OI v11_oi_staging_v1 (oi_data/consolidated, per-file SHA-256 "
        "pinned in research/control/v11_run/oi_staging_manifest.json; "
        "availability = the row's own create_time, read per row); bars for "
        "execution/pricing only; funding COST ONLY, never in any signal"
    ),
    "scored_status": CONFIRMATORY,
    "section_1_1_disclosure": SECTION_1_1_DISCLOSURE,
    "control_never_promotable": True,
}

#: Frozen per-arm config payloads (digest inputs; canonicalised sorted).
_FROZEN_CONFIGS: dict[str, dict] = {
    ANCHOR_ARM: {
        **_BOOK_COMMON,
        "signal": "leave_one_out_cycle_slope",
        "window_rows": WINDOW_ROWS_ANCHOR,
        "window_changes": WINDOW_ROWS_ANCHOR - 1,
        "aggregate": "leave-one-out mean of the other 18 tradeable symbols' daily log OI changes",
        "sort": "ascending on CYC value (long lowest-CYC tercile, short highest-CYC tercile)",
        "role": "anchor",
        "fill_rule": "slot_open_first_bar_at_or_after_T_plus_15m",
        "drop_one_pin": "held max-|weight| symbol, remaining weights unchanged, no renormalisation",
    },
    NEIGHBOUR_ARM: {
        **_BOOK_COMMON,
        "signal": "leave_one_out_cycle_slope",
        "window_rows": WINDOW_ROWS_NEIGHBOUR,
        "window_changes": WINDOW_ROWS_NEIGHBOUR - 1,
        "aggregate": "leave-one-out mean of the other 18 tradeable symbols' daily log OI changes",
        "sort": "ascending on CYC value (long lowest-CYC tercile, short highest-CYC tercile)",
        "role": "neighbour",
        "neighbour_justification": "halves estimator lag so a leverage-cycle turn two weeks old is reflected now rather than averaged away; 15-row warmup feasible at the first stamp (OICYC.md section 6)",
        "fill_rule": "slot_open_first_bar_at_or_after_T_plus_15m",
        "drop_one_pin": "held max-|weight| symbol, remaining weights unchanged, no renormalisation",
    },
    CONTROL_ARM: {
        **_BOOK_COMMON,
        "signal": "own_share_of_aggregate_oi",
        "window_rows": WINDOW_ROWS_CONTROL,
        "window_changes": None,
        "aggregate": "sum of the 19 tradeable symbols' staged OI levels (denominator only)",
        "quantity": "SH_s = mean own share of the aggregate OI over the 28 most recent daily rows <= T",
        "sort": "ascending on SH value (long lowest-share tercile, short highest-share tercile); frozen 'rank DESCENDING on SH_s' carried as the descending rank presentation in payload diagnostics",
        "deleted_by_construction": "no differencing, no regression, no OI-flow direction anywhere in the control quantity",
        "falsification": (
            "if CTL-OISHARE passes {expectancy>0, PF>=1.10, >=2/3 folds "
            "positive} while the anchor passes, the edge is an OI-dominance/"
            "size artifact and A14-V14-A8-OICYC is FALSIFIED as a "
            "cycle-participation mechanism; the control is never promotable"
        ),
        "role": "causal_negative_control",
        "fill_rule": "slot_open_first_bar_at_or_after_T_plus_15m",
        "drop_one_pin": "held max-|weight| symbol, remaining weights unchanged, no renormalisation",
    },
}

#: The RECORDED ``arm_config_digest`` per arm (binding implementation-lane
#: record made before any scored metric exists; equality with the recomputed
#: digest is test-pinned).
OICYC_ARM_CONFIG_DIGESTS: dict[str, str] = {
    ANCHOR_ARM: "0e7b084c4755f63d25fdc2a175123ca78c48bdffb93da962a5e6d0b0875a61b6",
    NEIGHBOUR_ARM: "7c6baead3053b5a53dcb7731adc66f237a54fef412c3372bec204ca047e2dab1",
    CONTROL_ARM: "11858422224cf502d0eae7abb26eea617afa381b70626e3210b26bb18e00ce08",
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
    from research.v11.publication_identity import arm_config_digest

    report: dict[str, dict[str, Any]] = {}
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        computed = arm_config_digest(identity, arm_id=arm_id)
        recorded = OICYC_ARM_CONFIG_DIGESTS[arm_id]
        report[arm_id] = {
            "computed_from_identity": computed,
            "recorded_in_freeze": recorded,
            "match": bool(computed == recorded),
        }
    return report


__all__ = [
    "OICYC_ARM_CONFIG_DIGESTS",
    "frozen_arm_config",
    "frozen_arm_digest_report",
    "frozen_identity",
]
