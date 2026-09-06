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


__all__ = [
    "ANCHOR_ARM",
    "ARM_IDS",
    "ARM_ROLES",
    "CONTROL_ARM",
    "CYCLE",
    "FAMILY_ID",
    "NEIGHBOR_ARM",
    "PRODUCER_ROLE",
    "RECORDED_SPEC_SHA256",
    "SPEC_AUTHORITY_RELPATHS",
    "STRATEGY_ID",
    "UNIVERSE",
    "verify_spec_sha256s",
]
