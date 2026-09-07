"""Frozen identity of the A5-V15-F1-ELITE-SIZE-ASYM family (A8-I lane).

Every constant below is transcribed from the frozen authorities (priority
order, see package docstring); nothing here is tuned, chosen or improved.
The four spec sha256 pins are RECORDED at implementation time (before any
scored metric exists for any V15 cell, the V12/V13/V14 implementation-lane
convention) and re-verified against the on-disk authority bytes by
:func:`verify_spec_sha256s` (fail-closed; test-pinned).

Arm ids are the three frozen in
``research/control/v15_run/selection_freeze_v15.json``::

    A5-F1-ANCHOR-ASYM      anchor      (proposal anchor_spec)
    A5-F1-NEIGHBOR         neighbour   (proposal neighbour_spec ELITE-SIZE-ASYM-NB10Q)
    A5-F1-CTL-ELITELEVEL   causal negative control (proposal causal_control_spec)

Universe adjudication (selection_freeze ``ambiguity_adjudication``): the
proposal's ``universe`` field listed 19 names (SOLUSDT absent) while its own
rules cite the 20 symbols and a 7/6/7 split; A1 adjudicated the BINDING
universe to be the frozen 20 symbols (SOLUSDT included), per
p3_freeze_amendment_1 "universe stays the frozen 20 symbols".  The frozen 20
below are the ``p0_probe/probe_verdict_v15.json`` ``windows.universe`` list,
verbatim and in order.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Tuple

from research.adapter_v10.protocol import StrategyIdentity

FAMILY_ID = "A5-V15-F1-ELITE-SIZE-ASYM"
STRATEGY_ID = "elite_size_asym_v15"
CYCLE = "CRYPTO-V15"
PRODUCER_ROLE = "A8-I"

ANCHOR_ARM = "A5-F1-ANCHOR-ASYM"
NEIGHBOR_ARM = "A5-F1-NEIGHBOR"
CONTROL_ARM = "A5-F1-CTL-ELITELEVEL"
ARM_IDS: Tuple[str, ...] = (ANCHOR_ARM, NEIGHBOR_ARM, CONTROL_ARM)
ARM_ROLES: Dict[str, str] = {
    ANCHOR_ARM: "anchor",
    NEIGHBOR_ARM: "neighbour",
    CONTROL_ARM: "causal_negative_control",
}

#: The binding frozen 20-symbol universe (selection_freeze adjudication;
#: probe_verdict windows.universe, verbatim order; SOLUSDT included).
UNIVERSE: Tuple[str, ...] = (
    "1000PEPEUSDT",
    "AAVEUSDT",
    "ACEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "BCHUSDT",
    "BNBUSDT",
    "BOMEUSDT",
    "BTCUSDT",
    "DOGEUSDT",
    "ENAUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "NEARUSDT",
    "ONGUSDT",
    "SOLUSDT",
    "SUIUSDT",
    "WLDUSDT",
    "XRPUSDT",
    "ZECUSDT",
)

#: Frozen spec authority files (relative to the repo root) and their
#: RECORDED sha256 pins.  The proposal pin is stated verbatim in the lane
#: task and in selection_freeze_v15.json; the other three are computed from
#: the on-disk authority bytes at implementation time and pinned here.
SPEC_AUTHORITY_RELPATHS: Dict[str, str] = {
    "proposal_P1": "research/control/v15_run/d1/a5/proposal_P1.json",
    "selection_freeze_v15": "research/control/v15_run/selection_freeze_v15.json",
    "p3_freeze_v15": "research/control/v15_run/p3_freeze_v15.json",
    "p3_freeze_amendment_1": "research/control/v15_run/p3_freeze_amendment_1.json",
}

RECORDED_SPEC_SHA256: Dict[str, str] = {
    "proposal_P1": (
        "6d2bc25fc3d3e5ebd96ca60c8e428efed9823b94589073f41ddcbdf47392cb16"
    ),
    "selection_freeze_v15": (
        "0e02c2dfa09561ba17fb9c2a8afd876d24105a7c0929f9a30488605d46676cf0"
    ),
    "p3_freeze_v15": (
        "1df3f29a3138d26a3def086f3d82e5476ebb0602b37cdaca8f97c07feabeffb7"
    ),
    "p3_freeze_amendment_1": (
        "552bb550d5582c1fb930c1a9fc21f10441ee82db174a2f6889f181297606f434"
    ),
}

# --------------------------------------------------------------------------- #
# Clock / folds (proposal clock + p3_freeze binding constraints; verbatim)
# --------------------------------------------------------------------------- #
WINDOW_START_ISO = "2025-08-22"
WINDOW_END_ISO = "2026-08-21"

FOLDS: Tuple[Dict[str, str], ...] = (
    {"fold_id": "F0", "start": "2025-08-22", "end": "2025-12-20"},
    {"fold_id": "F1", "start": "2025-12-22", "end": "2026-04-20"},
    {"fold_id": "F2", "start": "2026-04-22", "end": "2026-08-21"},
)
#: 1-day purge between folds: book flat, unscored (p3 binding constraint).
PURGE_DAYS: Tuple[str, ...] = ("2025-12-21", "2026-04-21")

#: MEASURED_BOUND_LAG_3D (p3 freeze availability_semantics_binding; hard):
#: every metrics row read satisfies metrics_date <= decision_date - 3.
MEASURED_BOUND_LAG_DAYS = 3

#: amendment_1 global defect dates -- dropped by the loader entirely.
GLOBAL_DEFECT_DATES: Tuple[str, ...] = (
    "2025-07-21",
    "2025-07-22",
    "2025-08-29",
    "2026-08-12",
)

#: amendment_1 hole rule: a feature window with MORE than 10% missing
#: metrics-day cells for a symbol refuses every decision for that
#: symbol-date (refusal registry; no position; never a fill).
WINDOW_HOLE_MAX_FRACTION = 0.10

# --------------------------------------------------------------------------- #
# Features (proposal features_and_lags; verbatim)
# --------------------------------------------------------------------------- #
CLIP_LOW = 0.01
CLIP_HIGH = 100.0
#: anchor / causal control: median over t in [D-7, D-3] (5 usable daily rows).
ANCHOR_WINDOW_LOOKBACK_DAYS = 7
#: neighbour: median over t in [D-12, D-3] (10 usable daily rows).
NEIGHBOR_WINDOW_LOOKBACK_DAYS = 12

# --------------------------------------------------------------------------- #
# Book (proposal entry_exit_rules; verbatim)
# --------------------------------------------------------------------------- #
SIDE_GROSS = 0.5
WEIGHT_CAP_SIGNED = 0.30
GROSS_MAX = 1.0
MIN_TRADE_DELTA = 0.05
#: Full-cross-section side counts: anchor/control 7/6/7 on 20 (terciles),
#: neighbour 5/10/5 on 20 (frozen counts; per-name weight 0.10).
ANCHOR_SIDE_FRACTION = 1.0 / 3.0
NEIGHBOR_SIDE_FRACTION = 0.25
TIE_BREAK = "symbol_id_ascending"

# --------------------------------------------------------------------------- #
# Fill model + costs (proposal fill_model / cost_assumptions; verbatim)
# --------------------------------------------------------------------------- #
#: fill price = 00:00 UTC bar OPEN of the fill date (decision date D for the
#: base/stress-fee/stress-ticks tiers; D+1 for the +1-day delay tier).
DECISION_TIME_UTC = "00:00:00"
TAKER_FEE_BPS = 5.0
SLIPPAGE_TICKS = 2
#: Stress tiers on booked PnL (p3 inherited convention; proposal cost
#: stress): fee x1.5 (7.5 bps), slippage +2 ticks (4 total), +1 day delay.
STRESS_FEE_MULTIPLIER = 1.5
STRESS_EXTRA_TICKS = 2
STRESS_DELAY_DAYS = 1
STRESS_TIERS: Tuple[str, ...] = (
    "baseline",
    "fee_x1_5",
    "plus2ticks",
    "delay_plus1d",
)

#: amendment_1 funding sanity bound; measured -0.02 floor events are
#: legitimate data and enter costs normally.
FUNDING_RATE_ABS_BOUND = 0.0375

# --------------------------------------------------------------------------- #
# Spec-pin verification (fail-closed, recomputed from disk)
# --------------------------------------------------------------------------- #


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_spec_sha256s(repo_root: Path | str) -> Dict[str, Dict[str, Any]]:
    """Recompute every frozen-spec sha256 from disk vs the recorded pin.

    Returns a per-species report; raises :class:`RuntimeError` on any
    mismatch or missing authority file (fail closed, before any data load).
    """
    root = Path(repo_root)
    report: Dict[str, Dict[str, Any]] = {}
    for name, relpath in SPEC_AUTHORITY_RELPATHS.items():
        path = root / relpath
        recorded = RECORDED_SPEC_SHA256[name]
        if not path.is_file():
            raise RuntimeError(f"frozen spec authority missing: {path}")
        observed = sha256_file(path)
        report[name] = {
            "relpath": relpath,
            "recorded_sha256": recorded,
            "observed_sha256": observed,
            "match": observed == recorded,
        }
        if observed != recorded:
            raise RuntimeError(
                f"frozen spec sha256 mismatch for {name} ({relpath}): "
                f"observed {observed} != recorded {recorded}"
            )
    return report


# --------------------------------------------------------------------------- #
# Frozen arm-config identity + digests (oicyc V14 pattern; remediated)
# --------------------------------------------------------------------------- #
REMEDIATION_NOTE = (
    "gross-cap remediation A1-ordered pre-score (residual-budget "
    "renormalization on refusal-while-held); budget still 0/6"
)

_SIZING_PROCEDURE = (
    "side_gross 0.5 per populated side; per-name weight min(0.5/n_side, "
    "0.30); gross <= 1.0; REFUSAL-WHILE-HELD DATES (A1-ordered PRE-SCORE "
    "remediation): carried refused weights keep their budget and the fresh "
    "book renormalizes into the residual budget GROSS_MAX - sum|carried "
    "refused weights| (fresh side budgets scale proportionally to the "
    "residual; the 0.30 signed cap still binds each name; a downward scale "
    "only shrinks weights; residual <= 0 forces the fresh side flat and "
    "records the event)"
)

_BOOK_COMMON: Dict[str, Any] = {
    "book": "elite_size_asym_cross_sectional_rank",
    "leg_gross": SIDE_GROSS,
    "weight_cap_abs": WEIGHT_CAP_SIGNED,
    "gross_max": GROSS_MAX,
    "min_trade_delta": MIN_TRADE_DELTA,
    "tie_break": "symbol_id_ascending",
    "decision_clock": "daily 00:00:00 UTC on every scored day",
    "lag_rule": "MEASURED_BOUND_LAG_3D (metrics_date <= D - 3, hard)",
    "hole_rule": (
        ">10% missing metrics-day cells in the feature window refuse the "
        "symbol-date (per-arm refusal registry; never a fill, never "
        "synthesized)"
    ),
    "sizing_procedure": _SIZING_PROCEDURE,
    "exit_rule": (
        "rank-bucket change only; force-flat at the last scored day of "
        "every fold and on purge days; re-entry at the next fold's first "
        "scored day"
    ),
    "folds_contract": [
        {"fold_id": fold["fold_id"], "start": fold["start"], "end": fold["end"]}
        for fold in FOLDS
    ],
    "purge_days": list(PURGE_DAYS),
    "window": [WINDOW_START_ISO, WINDOW_END_ISO],
    "universe_size": len(UNIVERSE),
    "cross_section": "frozen 20-symbol universe; refusals shrink the eligible set",
    "fill_rule": "00:00 UTC bar OPEN of the fill date; min-trade |dw| >= 0.05",
    "cost": {
        "taker_fee_bps": TAKER_FEE_BPS,
        "slippage_ticks": SLIPPAGE_TICKS,
        "cost_once_per_fill": True,
        "funding": "native settlements once per holding interval, cost only",
        "stress_tiers": "fee x1.5 / +2 ticks / +1 day delay",
    },
    "data": (
        "staged v15 parquet (metrics/klines/funding) read through this "
        "package's staged_root.json; machine-local, read-only"
    ),
    "scored_status": "EXPLORATORY",
    "remediation_note": REMEDIATION_NOTE,
}

_FROZEN_CONFIGS: Dict[str, Dict[str, Any]] = {
    ANCHOR_ARM: {
        **_BOOK_COMMON,
        "signal": "ln(clip(sum_toptrader)) - ln(clip(count_toptrader)), median over [D-7, D-3]",
        "window_lookback_days": ANCHOR_WINDOW_LOOKBACK_DAYS,
        "side_fraction": ANCHOR_SIDE_FRACTION,
        "side_shape_on_20": "7/6/7 terciles",
        "sort": "ascending on S_i(D): long bottom-7, short top-7, middle flat",
        "role": "anchor",
        "direction": "fade the size-heavy side (preregistered, no post-hoc flip)",
    },
    NEIGHBOR_ARM: {
        **_BOOK_COMMON,
        "signal": "ln(clip(sum_toptrader)) - ln(clip(count_toptrader)), median over [D-12, D-3]",
        "window_lookback_days": NEIGHBOR_WINDOW_LOOKBACK_DAYS,
        "side_fraction": NEIGHBOR_SIDE_FRACTION,
        "side_shape_on_20": "5/10/5 (per-name weight 0.10)",
        "sort": "ascending on S_i(D): long bottom-5, short top-5, middle flat",
        "role": "neighbour",
        "direction": "same mechanism and direction as the anchor",
    },
    CONTROL_ARM: {
        **_BOOK_COMMON,
        "signal": "ln(clip(count_toptrader)) alone, median over [D-7, D-3] (never reads the sum ratio)",
        "window_lookback_days": ANCHOR_WINDOW_LOOKBACK_DAYS,
        "side_fraction": ANCHOR_SIDE_FRACTION,
        "side_shape_on_20": "7/6/7 terciles (identical machinery)",
        "sort": "ascending on C_i(D): long bottom-7, short top-7 (identical machinery)",
        "role": "causal_negative_control",
        "direction": "long most-elite-short tercile, short most-elite-long tercile",
        "control_never_promotable": True,
        "falsification": (
            "if CTL-ELITELEVEL reproduces per its preregistered rule, "
            "A5-V15-P1 fails stage-A gate 11 regardless of the anchor"
        ),
    },
}

#: Per-arm stable config id (digest input via the canonical v11 payload).
ARM_CONFIG_IDS: Dict[str, str] = {
    ANCHOR_ARM: "elite-size-asym-anchor-asym-v15",
    NEIGHBOR_ARM: "elite-size-asym-nb10q-v15",
    CONTROL_ARM: "elite-size-asym-ctl-elitelevel-v15",
}

DIRECTION = "BOTH_WITH_SIGN_SEMANTICS"
FUNDING_SIGN_CONVENTION = "LONG_PAYS_POSITIVE_RATE"
BENCHMARK_SYMBOLS_EXCLUDED: Tuple[str, ...] = ()  # BTCUSDT is ranked here

#: The RECORDED ``arm_config_digest`` per arm (binding implementation-lane
#: record made with zero scored V15 cells; equality with the recomputed
#: digest is test-pinned).  The recorded values carry the A1-ordered
#: PRE-SCORE gross-cap remediation in ``sizing_procedure`` (the sizing
#: procedure is a digest input), so the digests changed with the remediation
#: and are re-pinned here.
ARM_CONFIG_DIGESTS: Dict[str, str] = {
    ANCHOR_ARM: "a1efb186862819882abcf1602fbb8c786b5d487a075f10712469c509e808cae1",
    NEIGHBOR_ARM: "ba4f27b1de8683ab812e788e5d5f18a1c122cef977bdcb446130fceaf696bde4",
    CONTROL_ARM: "7a4bd244089f2a923edb024e8ec0e66eb5f2938c21eaa60463bc104a1e9c0d36",
}


def frozen_arm_config(arm_id: str) -> Dict[str, Any]:
    """The exact frozen ``config`` payload of one arm (digest input)."""
    arm_id = str(arm_id)
    if arm_id not in _FROZEN_CONFIGS:
        raise KeyError(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return dict(_FROZEN_CONFIGS[arm_id])


def frozen_identity(arm_id: str) -> StrategyIdentity:
    """The frozen V15 identity of one arm (digest equality is test-pinned)."""
    arm_id = str(arm_id)
    if arm_id not in ARM_CONFIG_IDS:
        raise KeyError(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return StrategyIdentity(
        strategy_id=STRATEGY_ID,
        family_id=FAMILY_ID,
        arm_config_id=ARM_CONFIG_IDS[arm_id],
        direction=DIRECTION,
        window_start_iso=WINDOW_START_ISO,
        window_end_iso=WINDOW_END_ISO,
        benchmark_symbols_excluded=BENCHMARK_SYMBOLS_EXCLUDED,
        funding_sign_convention=FUNDING_SIGN_CONVENTION,
        matrix_cohort_hint=FAMILY_ID,
        arm_id=arm_id,
        config=frozen_arm_config(arm_id),
    )


def frozen_arm_digest_report() -> Dict[str, Dict[str, Any]]:
    """Recomputed vs recorded ``arm_config_digest`` per arm (honest report)."""
    from research.v11.publication_identity import arm_config_digest

    report: Dict[str, Dict[str, Any]] = {}
    for arm_id in ARM_IDS:
        computed = arm_config_digest(frozen_identity(arm_id), arm_id=arm_id)
        recorded = ARM_CONFIG_DIGESTS[arm_id]
        report[arm_id] = {
            "computed_from_identity": computed,
            "recorded_in_freeze": recorded,
            "match": bool(computed == recorded),
        }
    return report


def verify_arm_digests() -> Dict[str, Any]:
    """Fail-closed digest pin: recomputed == recorded for every arm AND
    pairwise uniqueness across the three arms."""
    report = frozen_arm_digest_report()
    all_match = all(entry["match"] for entry in report.values())
    digests = [entry["computed_from_identity"] for entry in report.values()]
    pairwise_unique = len(set(digests)) == len(ARM_IDS) and len(digests) == len(ARM_IDS)
    return {
        "arms": report,
        "all_match": all_match,
        "pairwise_unique": pairwise_unique,
        "ok": all_match and pairwise_unique,
    }


__all__ = [
    "ANCHOR_ARM",
    "ARM_CONFIG_DIGESTS",
    "ARM_CONFIG_IDS",
    "ARM_IDS",
    "ARM_ROLES",
    "CONTROL_ARM",
    "CYCLE",
    "DIRECTION",
    "FAMILY_ID",
    "NEIGHBOR_ARM",
    "PRODUCER_ROLE",
    "RECORDED_SPEC_SHA256",
    "REMEDIATION_NOTE",
    "SPEC_AUTHORITY_RELPATHS",
    "STRATEGY_ID",
    "UNIVERSE",
    "frozen_arm_config",
    "frozen_arm_digest_report",
    "frozen_identity",
    "verify_arm_digests",
    "verify_spec_sha256s",
]
