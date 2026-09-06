"""Frozen identity of the A6-V15-F1-TAKER-SAT family (implementation lane).

This module pins, verbatim, the frozen spec of the selected family
``A6-V15-F1-TAKER-SAT`` ("aggression saturation", AXIS-3):

1. ``research/control/v15_run/d1/a6/proposal_P1.json``
   (sha256 ``2b7a3ed3caf636af3646cddeeee081e49ae3549ef3cffa0875962c7928a5c034``)
   -- mechanism, features, window/lag, entry/exit, fill model, costs, the
   three arms and the falsification rule;
2. ``research/control/v15_run/selection_freeze_v15.json`` -- the SELECTED
   arm ids (``A6-F1-ANCHOR-SAT``, ``A6-F1-NEIGHBOR``,
   ``A6-F1-CTL-RAWSAT``) and the binding universe (the frozen 20 symbols);
3. ``research/control/v15_run/p3_freeze_v15.json`` +
   ``research/control/v15_run/p3_freeze_amendment_1.json`` -- weights cap
   0.30 signed / gross <= 1.0, force-flat folds F0/F1/F2 with 1-day purge,
   ``MEASURED_BOUND_LAG_3D``, the >10%-window-hole refusals, cost-once and
   the stress tiers (x1.5 fee / +2 ticks / +1 delay);
4. ``research/control/v15_run/p0_probe/probe_verdict_v15.json`` -- the
   frozen label semantics (taker ratio is a FLOW over ``[T, T+5min)`` at
   label T; OI stock snapshot at ``T+5min``; row identity = start-of-period
   label; the daily aggregation never double-counts boundary stamps).

Every sha256 below was recorded at implementation time, BEFORE any cell ran
anywhere in the cycle (budget 0/6, ``no_pnl_computed: true`` in every
authority).  ``verify_pinned_authorities`` recomputes each digest fail-closed
-- a drifted authority is a STOP, never a silent proceed.  The per-arm
``arm_config_digest`` values in ``TAKER_SAT_ARM_CONFIG_DIGESTS`` are recorded
from the frozen identity payloads below at implementation time and are
test-pinned; any drift surfaces honestly and fails the suite.

The implementer never improves a frozen spec: every constant here is quoted
from the authorities, not chosen.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from research.adapter_v10.protocol import ContractViolation, StrategyIdentity

REPO_ROOT = Path(__file__).resolve().parents[4]

# --------------------------------------------------------------------------- #
# Frozen identity (selection_freeze_v15.json family record)
# --------------------------------------------------------------------------- #
FAMILY_ID = "A6-V15-F1-TAKER-SAT"
STRATEGY_ID = "hyp_a6_v15_f1_taker_sat"
AXIS = "AXIS-3 taker flow ratio-of-ratio"
#: Long/short cross-sectional fade book; BTCUSDT is a RANKED tradeable name
#: here (the frozen universe is the proposal's 20 authorized symbols) and the
#: BTC context gates are a Stage-A scoring concern, never a leg exclusion.
DIRECTION = "long_short"
MATRIX_COHORT_HINT = "v15"
FUNDING_SIGN_CONVENTION = "LONG_PAYS_POSITIVE_RATE"

ANCHOR_ARM = "A6-F1-ANCHOR-SAT"
NEIGHBOUR_ARM = "A6-F1-NEIGHBOR"
CONTROL_ARM = "A6-F1-CTL-RAWSAT"

#: arm id -> frozen role (selection_freeze_v15.json ``arms`` semantics).
ARM_ROLES: dict[str, str] = {
    ANCHOR_ARM: "anchor",
    NEIGHBOUR_ARM: "neighbour",
    CONTROL_ARM: "causal_negative_control",
}
ARM_IDS: tuple[str, ...] = tuple(sorted(ARM_ROLES))

#: Digest-bearing ``arm_config_id`` per arm.
ARM_CONFIG_IDS: dict[str, str] = {
    ANCHOR_ARM: "SAT-W10",
    NEIGHBOUR_ARM: "SAT-W20",
    CONTROL_ARM: "RAWSAT-W10",
}

#: The proposal-internal arm ids (provenance; the selection-freeze ids above
#: are the binding names).
PROPOSAL_ARM_IDS: dict[str, str] = {
    ANCHOR_ARM: "A6-V15-P1-ANCHOR",
    NEIGHBOUR_ARM: "A6-V15-P1-NEIGH",
    CONTROL_ARM: "A6-V15-P1-CTL",
}

#: The frozen 20-symbol binding universe (proposal ``universe`` field;
#: selection_freeze binding constraint "universe = frozen 20 symbols").
UNIVERSE: tuple[str, ...] = (
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "BTCUSDT", "DOGEUSDT",
    "ENAUSDT", "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT",
    "SOLUSDT", "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
)
UNIVERSE_SIZE = 20
BENCHMARK_CONTEXT_SYMBOL = "BTCUSDT"  # context gates only, never excluded

# --------------------------------------------------------------------------- #
# Pinned authority sha256s (recorded at implementation time; fail-closed)
# --------------------------------------------------------------------------- #
PINNED_AUTHORITY_SHA256: dict[str, Mapping[str, str]] = {
    "proposal_P1": {
        "relpath": "research/control/v15_run/d1/a6/proposal_P1.json",
        "sha256": "2b7a3ed3caf636af3646cddeeee081e49ae3549ef3cffa0875962c7928a5c034",
    },
    "selection_freeze": {
        "relpath": "research/control/v15_run/selection_freeze_v15.json",
        "sha256": "0e02c2dfa09561ba17fb9c2a8afd876d24105a7c0929f9a30488605d46676cf0",
    },
    "p3_freeze": {
        "relpath": "research/control/v15_run/p3_freeze_v15.json",
        "sha256": "1df3f29a3138d26a3def086f3d82e5476ebb0602b37cdaca8f97c07feabeffb7",
    },
    "p3_freeze_amendment_1": {
        "relpath": "research/control/v15_run/p3_freeze_amendment_1.json",
        "sha256": "552bb550d5582c1fb930c1a9fc21f10441ee82db174a2f6889f181297606f434",
    },
    "probe_verdict": {
        "relpath": "research/control/v15_run/p0_probe/probe_verdict_v15.json",
        "sha256": "f9873dfc8e178feeb943f99d0e1c2ca0363ebafd40c8e1f795cb755fe99fa179",
    },
}


def verify_pinned_authorities(repo_root: Path | None = None) -> dict[str, Any]:
    """Recompute every pinned authority sha256; fail closed on any drift.

    A missing or mutated frozen authority is a STOP (the spec this lane
    implements is no longer the spec on disk), never a silent proceed.
    """
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    report: dict[str, Any] = {}
    for name, pin in PINNED_AUTHORITY_SHA256.items():
        path = root / pin["relpath"]
        if not path.is_file():
            raise ContractViolation(
                f"pinned authority missing: {pin['relpath']} (fail-closed STOP)"
            )
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        report[name] = {
            "relpath": pin["relpath"],
            "recorded_sha256": pin["sha256"],
            "observed_sha256": observed,
            "match": observed == pin["sha256"],
        }
        if observed != pin["sha256"]:
            raise ContractViolation(
                f"pinned authority sha256 drift for {pin['relpath']}: observed "
                f"{observed} != recorded {pin['sha256']} (fail-closed STOP)"
            )
    return report


# --------------------------------------------------------------------------- #
# Frozen feature constants (proposal features_and_lags, verbatim numbers)
# --------------------------------------------------------------------------- #
#: five_minute_hygiene: r_t clipped to [0.2, 5.0] before log.
RATIO_CLIP_LO = 0.2
RATIO_CLIP_HI = 5.0
#: ... then clip(ln r_t, -1.609, +1.609).
LOG_CLIP_ABS = 1.609
#: anchor regularization floor c = 0.02.
CHURN_FLOOR_C = 0.02
#: HARD LAG (MEASURED_BOUND_LAG_3D): max metrics_date read at decision D is
#: D - 3 calendar days.
LAG_DAYS = 3
#: Anchor/control window W = metrics dates [D-12, D-3] = 10 daily aggregates.
WINDOW_DAYS_ANCHOR = 10
#: Neighbour window W = metrics dates [D-23, D-3] = 21 daily aggregates
#: (single-knob horizon variant; churn endpoints move with the window).
#: ADJUDICATED_BY_A1 (pre-score): the explicit dated range binds over the
#: draft prose count "20" -- see the neighbour config's adjudication note.
WINDOW_DAYS_NEIGHBOUR = 21
#: amendment-1 hole rule: a lookback window with MORE than 10% missing
#: metrics-day cells refuses the symbol's decision (integer test
#: ``10 * missing > n``; exactly 10% still computes over available days).
HOLE_REFUSE_FRACTION_NUM = 10
HOLE_REFUSE_FRACTION_DEN = 100

# --------------------------------------------------------------------------- #
# Frozen book constants (proposal entry_exit_rules, verbatim numbers)
# --------------------------------------------------------------------------- #
#: SHORT the top 5, LONG the bottom 5 of the descending-S rank.
N_SIDE = 5
#: signed weight +0.10 per long name, -0.10 per short name.
WEIGHT_PER_NAME = 0.10
#: per-symbol signed weight cap (p3 freeze binding constraint).
CAP_MAX = 0.30
#: gross <= 1.0 (10 names x 0.10).
GROSS_MAX = 1.0
#: "if fewer than 10 symbols ... are available, stay flat for that cycle".
MIN_AVAILABLE = 10
#: decisions every 5 calendar days from each fold start.
REBALANCE_DAYS = 5
#: ties broken by symbol name ascending (deterministic).
TIE_BREAK = "symbol_name_ascending"

# --------------------------------------------------------------------------- #
# Frozen cost model (proposal cost_assumptions; V12 selection-freeze tiers)
# --------------------------------------------------------------------------- #
TAKER_FEE_BPS = 5.0
BASE_SLIP_TICKS = 1
STRESS_FEE_MULTIPLIER = 1.5
STRESS_EXTRA_TICKS = 2
STRESS_SLIP_TICKS = BASE_SLIP_TICKS + STRESS_EXTRA_TICKS  # 3
STRESS_DELAY_DAYS = 1
#: amendment-1 funding sanity bound (documented extreme cap).
FUNDING_RATE_ABS_CAP = 0.0375
COST_ONCE_PRINCIPLE = (
    "costs and funding charged exactly once on booked PnL, per the pinned "
    "cost-once kernel (tests/test_v14_p1_cost_once.py authority)"
)

# --------------------------------------------------------------------------- #
# Frozen folds + clock (p3 freeze binding constraints; proposal clock)
# --------------------------------------------------------------------------- #
PURGE_DAYS = 1
#: (label, start_date_inclusive, end_date_EXCLUSIVE).  The p3 freeze writes
#: each fold by its last COVERED date (F0 2025-08-22..2025-12-20 etc.); the
#: 1-day purge zone is [end - 1d, end) = the fold's last covered date, so
#: force-flat covers that whole day and the next fold starts the day after.
FOLDS: tuple[tuple[str, str, str], ...] = (
    ("F0", "2025-08-22", "2025-12-21"),
    ("F1", "2025-12-21", "2026-04-21"),
    ("F2", "2026-04-21", "2026-08-22"),
)
WINDOW_START_ISO = "2025-08-22T00:00:00Z"
WINDOW_END_ISO = "2026-08-22T00:00:00Z"  # exclusive; last covered 2026-08-21
FOLDS_CONTRACT = (
    "folds F0 2025-08-22..2025-12-20, F1 2025-12-21..2026-04-20, "
    "F2 2026-04-21..2026-08-21 (p3 freeze; dates covered), 1-day purge zone "
    "[end - 1d, end) force-flat, decisions every 5 calendar days from each "
    "fold start, blind-S0 2025-08-22..2026-08-21"
)
DECISION_CLOCK = (
    "DAILY grid; decisions every 5 calendar days from each fold start at "
    "00:00 UTC; force-flat at fold boundaries through the 1-day purge; "
    "MEASURED_BOUND_LAG_3D on every feature read"
)

# --------------------------------------------------------------------------- #
# Frozen data contract (p3 freeze v15_data_contract_freeze + probe verdict)
# --------------------------------------------------------------------------- #
GLOBAL_DEFECT_DATES: frozenset[str] = frozenset(
    {"2025-07-21", "2025-07-22", "2025-08-29", "2026-08-12"}
)
LABEL_SEMANTICS = (
    "start-of-period archive-wide on current published bytes: labeled T "
    "carries the stock snapshot at T+5min and the taker flow window "
    "[T, T+5min); the taker ratio is a FLOW field -- the daily aggregate "
    "consumes each 5-minute label of its own metrics_date exactly once and "
    "never double-counts boundary stamps"
)
METRICS_GRID = (
    "per (symbol, metrics_date) cell: exactly 288 rows, 288 unique "
    "create_time labels, full 00:00..23:55 grid, sorted by create_time; "
    "violations refuse the cell (fail closed, never synthesized)"
)
#: Scored-guard remediation A1-ordered pre-score (driver-owned guard;
#: V14-aligned); budget still 0/6.
SCORED_GUARD_REMEDIATION_NOTE = (
    "scored-guard remediation A1-ordered pre-score (driver-owned guard; "
    "V14-aligned); budget still 0/6"
)

# --------------------------------------------------------------------------- #
# Frozen per-arm config payloads (digest inputs; canonicalised sorted)
# --------------------------------------------------------------------------- #
_BOOK_COMMON: dict[str, Any] = {
    "book": "cross_sectional_extreme_fade_5v5",
    "rank": "descending on the arm feature; ties broken by symbol name ascending",
    "short_side": "top 5 (extreme buy-side aggression saturation)",
    "long_side": "bottom 5 (extreme sell-side aggression saturation)",
    "weight_per_name": WEIGHT_PER_NAME,
    "cap_max_signed": CAP_MAX,
    "gross_max": GROSS_MAX,
    "min_available_names": MIN_AVAILABLE,
    "below_min_available": "stay flat for that cycle (preregistered)",
    "rebalance_days": REBALANCE_DAYS,
    "tie_break": TIE_BREAK,
    "universe_size": UNIVERSE_SIZE,
    "hold": "until the next decision date; exit fills at that date's 00:00 UTC open",
    "force_flat": "on the last day of each fold and through the 1-day purge",
    "decision_clock": DECISION_CLOCK,
    "folds_contract": FOLDS_CONTRACT,
    "window": [WINDOW_START_ISO, WINDOW_END_ISO],
    "lag_discipline": (
        "MEASURED_BOUND_LAG_3D: max metrics_date read at decision D is D-3"
    ),
    "label_semantics": LABEL_SEMANTICS,
    "metrics_grid": METRICS_GRID,
    "fill_model": (
        "taker fills at the 00:00 UTC bar open of the decision date from "
        "staged klines (start-of-period label semantics; the open is known "
        "at bar start); next-allowed-fill when the 00:00 bar is absent; "
        "each fill charged exactly once; no intrabar path dependence"
    ),
    "cost_model": {
        "base": "taker fee 5.0 bps per fill + 1 native tick slippage per fill",
        "stress": "fee x1.5 (7.5 bps) + 2 extra ticks (3 total) per fill + "
        "1-day execution delay on decision-date fills",
        "principle": COST_ONCE_PRINCIPLE,
    },
    "funding": "applied once per settlement stamp; LONG_PAYS_POSITIVE_RATE",
    "funding_rate_abs_cap": FUNDING_RATE_ABS_CAP,
    "scored_flag_semantics": (
        "run_arm(scored=...) records the flag verbatim in the cell payload; "
        "unauthorized scored execution is refused at the DRIVER layer "
        "(--publish/--expect-head + exactly-once ledger chain), never "
        "inside the family package (V14-aligned, elite_size_asym pattern)"
    ),
    "scored_guard_remediation": SCORED_GUARD_REMEDIATION_NOTE,
    "hole_rule": (
        "feature windows compute over available staged rows only; more than "
        "10% missing metrics-day cells in the lookback window refuses the "
        "symbol's decision (refusal registry); a refused decision never "
        "becomes a fill and never synthesizes data"
    ),
    "data": (
        "staged V15 parquet metrics (5-minute taker ratio + OI value), "
        "klines 15m for fills only, funding for costs only; klines enter "
        "FILL PRICES ONLY and never enter any feature"
    ),
}

_FROZEN_CONFIGS: dict[str, dict[str, Any]] = {
    ANCHOR_ARM: {
        **_BOOK_COMMON,
        "signal": "saturation_ratio_of_ratio",
        "feature": (
            "S = A_bar / (O + 0.02); A_bar = mean of the daily clipped-log "
            "taker-ratio aggregate a_i_d over W = metrics dates [D-12, D-3] "
            "(10 daily aggregates, all <= D-3); O = "
            "|ln(OIv_2355(D-3) / OIv_2355(D-12))|"
        ),
        "window_days": WINDOW_DAYS_ANCHOR,
        "window_expr": "[D-12, D-3]",
        "churn_endpoints": "[D-12, D-3]",
        "role": "anchor",
        "claim": (
            "aggression saturation relative to positioning churn predicts "
            "multi-day reversal of the aggressive side"
        ),
    },
    NEIGHBOUR_ARM: {
        **_BOOK_COMMON,
        "signal": "saturation_ratio_of_ratio",
        "feature": (
            "identical pipeline and constants except the window horizon: "
            "A_bar = mean of a_i_d over W = the 21 metrics dates [D-23, "
            "D-3] inclusive, with churn endpoints moved to the same window "
            "endpoints [D-23, D-3]; single-knob horizon variant of the "
            "anchor"
        ),
        "window_days": WINDOW_DAYS_NEIGHBOUR,
        "window_expr": "[D-23, D-3] inclusive (21 daily aggregates)",
        "churn_endpoints": "[D-23, D-3]",
        "role": "neighbour",
        "support_rule": (
            "neighbour supports if it passes the stage-A gate (10); "
            "horizon-robustness of the saturation mechanism is the support "
            "claim"
        ),
        "spec_ambiguity_adjudication": (
            "ADJUDICATED_BY_A1 (V15 selection-phase ambiguity rule, family "
            "A6-V15-F1-TAKER-SAT, neighbour window off-by-one). Ruling: "
            "bind the EXPLICIT RANGE [D-23, D-3] inclusive = 21 daily "
            "aggregates (WINDOW_DAYS_NEIGHBOUR = 21). Reasons recorded: "
            "(1) a dated range is the more precise instrument -- prose "
            "counts are derived text and '20' appears to be a draft "
            "remnant; (2) the family's own internal convention is "
            "inclusive-endpoint ranges (anchor [D-12, D-3] = 10 "
            "aggregates, consistent); (3) materiality is confined to the "
            "NEIGHBOUR arm's support gate, and the adjudication is frozen "
            "BEFORE any scored outcome exists (none exists; budget still "
            "0/6). Applied by the I-F2 lane as a one-frozen-constant "
            "revert; digest re-pinned pre-score."
        ),
    },
    CONTROL_ARM: {
        **_BOOK_COMMON,
        "signal": "raw_aggression_intensity",
        "feature": (
            "identical pipeline, window, ranking, weights, rules and costs, "
            "but the feature is raw A_bar_i (daily aggression intensity) "
            "with NO positioning-churn denominator"
        ),
        "window_days": WINDOW_DAYS_ANCHOR,
        "window_expr": "[D-12, D-3]",
        "churn_endpoints": None,
        "role": "causal_negative_control",
        "what_it_kills": (
            "the convenient explanation that the anchor is plain "
            "flow-reversal / flow-momentum relabeling the XSECT sprint "
            "ancestry"
        ),
        "preregistered_non_reproduction_rule": (
            "CTL must NOT simultaneously pass stage-A gates (1) after-cost "
            "expectancy > 0 and (2) position PF >= 1.10; if CTL passes both, "
            "the anchor's saturation normalization is doing no causal work, "
            "the mechanism is falsified, and the family is ineligible "
            "regardless of the anchor's own gates"
        ),
        "control_never_promotable": True,
    },
}


def frozen_arm_config(arm_id: str) -> dict[str, Any]:
    """The exact frozen ``config`` payload of one arm (digest input)."""
    arm_id = str(arm_id)
    if arm_id not in _FROZEN_CONFIGS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return dict(_FROZEN_CONFIGS[arm_id])


def frozen_identity(arm_id: str) -> StrategyIdentity:
    """The frozen V15 identity of one arm (digest equality is test-pinned)."""
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
        benchmark_symbols_excluded=(),  # BTCUSDT is a ranked tradeable name
        funding_sign_convention=FUNDING_SIGN_CONVENTION,
        matrix_cohort_hint=MATRIX_COHORT_HINT,
        arm_id=arm_id,
        config=frozen_arm_config(arm_id),
    )


#: The RECORDED ``arm_config_digest`` per arm (binding implementation-lane
#: record made before any scored metric exists; equality with the recomputed
#: digest is test-pinned).
TAKER_SAT_ARM_CONFIG_DIGESTS: dict[str, str] = {
    ANCHOR_ARM: "908c8033af9321156404ffa4f8307a6f3a88d4d3ca31ab3756eb469271524caa",
    NEIGHBOUR_ARM: "fb74cf5747f6e59249312717151f033a7dc8f8ba649cdae4497cb1a14888fdd1",
    CONTROL_ARM: "9081d4426d05a4619e9f2444fad0ab33f7066ffb3625b581b50c548e2bf6770a",
}


def frozen_arm_digest_report() -> dict[str, dict[str, Any]]:
    """Recomputed vs recorded ``arm_config_digest`` per arm (honest report)."""
    from research.v11.publication_identity import arm_config_digest

    report: dict[str, dict[str, Any]] = {}
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        computed = arm_config_digest(identity, arm_id=arm_id)
        recorded = TAKER_SAT_ARM_CONFIG_DIGESTS[arm_id]
        report[arm_id] = {
            "computed_from_identity": computed,
            "recorded_in_freeze": recorded,
            "match": bool(computed == recorded),
        }
    return report


__all__ = [
    "ANCHOR_ARM",
    "ARM_CONFIG_IDS",
    "ARM_IDS",
    "ARM_ROLES",
    "AXIS",
    "BASE_SLIP_TICKS",
    "BENCHMARK_CONTEXT_SYMBOL",
    "CAP_MAX",
    "CHURN_FLOOR_C",
    "CONTROL_ARM",
    "COST_ONCE_PRINCIPLE",
    "DECISION_CLOCK",
    "DIRECTION",
    "FOLDS",
    "FOLDS_CONTRACT",
    "FUNDING_RATE_ABS_CAP",
    "FUNDING_SIGN_CONVENTION",
    "GLOBAL_DEFECT_DATES",
    "GROSS_MAX",
    "LAG_DAYS",
    "LABEL_SEMANTICS",
    "LOG_CLIP_ABS",
    "MATRIX_COHORT_HINT",
    "MIN_AVAILABLE",
    "NEIGHBOUR_ARM",
    "N_SIDE",
    "PINNED_AUTHORITY_SHA256",
    "PROPOSAL_ARM_IDS",
    "PURGE_DAYS",
    "RATIO_CLIP_HI",
    "RATIO_CLIP_LO",
    "REBALANCE_DAYS",
    "SCORED_GUARD_REMEDIATION_NOTE",
    "STRATEGY_ID",
    "STRESS_DELAY_DAYS",
    "STRESS_EXTRA_TICKS",
    "STRESS_FEE_MULTIPLIER",
    "STRESS_SLIP_TICKS",
    "TAKER_FEE_BPS",
    "TAKER_SAT_ARM_CONFIG_DIGESTS",
    "TIE_BREAK",
    "UNIVERSE",
    "UNIVERSE_SIZE",
    "WEIGHT_PER_NAME",
    "WINDOW_DAYS_ANCHOR",
    "WINDOW_DAYS_NEIGHBOUR",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "frozen_arm_config",
    "frozen_arm_digest_report",
    "frozen_identity",
    "verify_pinned_authorities",
]
