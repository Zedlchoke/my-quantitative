"""Central A1 wiring: the six frozen STOCKS-FREE-V3 arms in one registry.

Single place that binds each frozen arm id to its family module and to its
executable risk-matched ``VolScalingRule`` for the scoring lane.  No strategy
logic lives here and nothing scored is computed.

ADJ-4-CONSTANT-SCALE-RULE (selection_freeze.json adjudications): the A5-IDIO
freeze records ``target_daily_vol: null`` because the constant scale is fully
determined by ``min_gross == max_gross`` (the clip always returns that
constant).  The executable ``VolScalingRule`` requires a positive finite
target vol, pinned here to 0.01 (the P1 baseline); any positive value yields
the identical constant scale, so schedules, valuations and costs are
unaffected.  TOM-SETTLE's rule is wired verbatim from its frozen config
(0.005 target vol, gross clip [0.30, 0.50]).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping

from research.assets.common.contracts import canonical_json
from research.stocks_free_v3.benchmarks import VolScalingRule

#: Wire-in UTC (A1 central wiring commit; pre-scoring).
WIRED_AT_UTC = "2026-09-03T13:40:00Z"

SELECTION_SHA = "e2d7241151966b863233cc3bab4ad8593f457a87"

BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0
TURNOVER_CEILING_TWO_WAY_PER_YEAR = 6.0
HISTORICAL_STOCKS_DENOMINATOR = 6

COHORT_DIGEST = "c9d4e88a33c53448120e79138057bcb0d100abecc1d33fbec92bd3d9c541bc96"
PARTITION_DIGEST = "9b4ad7993f943edb1f4a995184eb85083879168f9f86eb1720b2a66623ef17c7"
CALENDAR_DIGEST = "028a7b21c9e306c7399467309d18e3ed696181682ca01f1e3170c21bdceb69ab"

S0_FOLDS = (
    ("S0_FOLD_1", "2018-04-04", "2020-09-01"),
    ("S0_FOLD_2", "2020-09-10", "2023-02-09"),
    ("S0_FOLD_3", "2023-02-17", "2025-07-24"),
)
S1_START = "2025-08-01"
S1_END = "2026-07-31"

#: Execution order after the owner GO (PLAN section 15: families
#: lexicographic; within a family anchor -> neighbour -> control).
EXECUTION_ORDER = (
    "SFV3-A5-IDIO-SHOCK-REVERSAL-A1",
    "SFV3-A5-IDIO-SHOCK-REVERSAL-N1",
    "SFV3-A5-IDIO-SHOCK-REVERSAL-C1",
    "SFV3-A6-TOM-SETTLE-A",
    "SFV3-A6-TOM-SETTLE-N",
    "SFV3-A6-TOM-SETTLE-C",
)


def _constant_scale_rule(constant_gross: float) -> VolScalingRule:
    return VolScalingRule(
        lookback_sessions=63,
        target_daily_vol=0.01,
        min_gross=constant_gross,
        max_gross=constant_gross,
    )


@dataclass(frozen=True)
class ArmInputs:
    """Resolved, S0-only data bundle a family schedule/dry-run consumes.

    ``issuer_tr_returns`` is required by the IDIO family only; TOM derives
    its schedule from the calendar and needs only the price surfaces.
    """

    sessions: tuple[str, ...]
    raw_close: Mapping[str, Mapping[str, float]]
    distributions: Mapping[str, Mapping[str, float]]
    split_factors: Mapping[str, Mapping[str, float]]
    issuer_tr_returns: Mapping[str, Mapping[str, float]] | None = None


@dataclass(frozen=True)
class ArmBinding:
    """One frozen arm: family wiring plus its resolved benchmark rule."""

    arm_id: str
    family_id: str
    role: str
    module: str
    config: Any
    vol_scaling_rule: VolScalingRule

    @property
    def config_digest(self) -> str:
        """Family-module digest: TOM ArmConfig exposes ``.digest``, IDIO
        FrozenArmConfig exposes ``.config_digest``."""
        digest = getattr(self.config, "digest", None)
        if digest is None:
            digest = self.config.config_digest
        return digest

    @property
    def trial_identity_digest(self) -> str:
        """sha256 over the complete scoring-identity payload."""
        payload: dict[str, Any] = {
            "asset_class": "US_ETF_CASH",
            "cycle": "STOCKS_FREE_V3",
            "family_id": self.family_id,
            "arm_id": self.arm_id,
            "role": self.role,
            "arm_config_digest": self.config_digest,
            "vol_scaling_rule": self.vol_scaling_rule.to_payload(),
            "costs": {"base_bps_per_side": BASE_COST_BPS,
                      "stress_bps_per_side": STRESS_COST_BPS},
            "turnover_ceiling_two_way_per_year":
                TURNOVER_CEILING_TWO_WAY_PER_YEAR,
            "cohort_digest": COHORT_DIGEST,
            "partition_digest": PARTITION_DIGEST,
            "calendar_digest": CALENDAR_DIGEST,
            "s0_folds": [list(f) for f in S0_FOLDS],
            "selection_sha": SELECTION_SHA,
            "wired_at_utc": WIRED_AT_UTC,
            "adjudications": ["ADJ-1-EXEC-CLOCK",
                              "ADJ-4-CONSTANT-SCALE-RULE"],
        }
        return hashlib.sha256(
            canonical_json(payload).encode("utf-8")).hexdigest()


def build_registry() -> dict[str, ArmBinding]:
    """Bind all six frozen arms; fail closed unless identities are complete
    and distinct."""
    from research.stocks_free_v3.family_idio_shock.arms import (
        ARM_A1,
        ARM_C1,
        ARM_N1,
    )
    from research.stocks_free_v3.family_tom_settle.config import (
        ARM_KEY_ANCHOR,
        ARM_KEY_CONTROL,
        ARM_KEY_NEIGHBOUR,
        build_arm_configs,
    )

    tom = build_arm_configs()

    specs = (
        ArmBinding(
            arm_id="SFV3-A5-IDIO-SHOCK-REVERSAL-A1",
            family_id="SFV3-A5-IDIO-SHOCK-REVERSAL",
            role="anchor",
            module="research.stocks_free_v3.family_idio_shock",
            config=ARM_A1,
            vol_scaling_rule=_constant_scale_rule(0.025),
        ),
        ArmBinding(
            arm_id="SFV3-A5-IDIO-SHOCK-REVERSAL-N1",
            family_id="SFV3-A5-IDIO-SHOCK-REVERSAL",
            role="neighbour",
            module="research.stocks_free_v3.family_idio_shock",
            config=ARM_N1,
            vol_scaling_rule=_constant_scale_rule(0.05),
        ),
        ArmBinding(
            arm_id="SFV3-A5-IDIO-SHOCK-REVERSAL-C1",
            family_id="SFV3-A5-IDIO-SHOCK-REVERSAL",
            role="causal_negative_control",
            module="research.stocks_free_v3.family_idio_shock",
            config=ARM_C1,
            vol_scaling_rule=_constant_scale_rule(0.025),
        ),
        ArmBinding(
            arm_id="SFV3-A6-TOM-SETTLE-A",
            family_id="SFV3-A6-TOM-SETTLE",
            role="anchor",
            module="research.stocks_free_v3.family_tom_settle",
            config=tom[ARM_KEY_ANCHOR],
            vol_scaling_rule=tom[ARM_KEY_ANCHOR].vol_scaling_rule,
        ),
        ArmBinding(
            arm_id="SFV3-A6-TOM-SETTLE-N",
            family_id="SFV3-A6-TOM-SETTLE",
            role="neighbour",
            module="research.stocks_free_v3.family_tom_settle",
            config=tom[ARM_KEY_NEIGHBOUR],
            vol_scaling_rule=tom[ARM_KEY_NEIGHBOUR].vol_scaling_rule,
        ),
        ArmBinding(
            arm_id="SFV3-A6-TOM-SETTLE-C",
            family_id="SFV3-A6-TOM-SETTLE",
            role="causal_negative_control",
            module="research.stocks_free_v3.family_tom_settle",
            config=tom[ARM_KEY_CONTROL],
            vol_scaling_rule=tom[ARM_KEY_CONTROL].vol_scaling_rule,
        ),
    )

    bindings = {b.arm_id: b for b in specs}
    assert set(bindings) == set(EXECUTION_ORDER), sorted(bindings)
    digests = {b.trial_identity_digest for b in bindings.values()}
    assert len(digests) == 6, "six arms must have six distinct identities"
    assert all(b.arm_id == b.config.arm_id for b in bindings.values()), (
        "registry arm ids must equal the family modules' frozen ids")
    return bindings


def build_arm_schedule(arm_id: str, inputs: ArmInputs):
    """Dispatch schedule construction to the owning family module."""
    binding = build_registry()[arm_id]
    if binding.family_id == "SFV3-A5-IDIO-SHOCK-REVERSAL":
        from research.stocks_free_v3.family_idio_shock.schedule import (
            build_arm_schedule as _build,
        )
        assert inputs.issuer_tr_returns is not None, (
            "IDIO arms require issuer-TR returns")
        return _build(binding.config, list(inputs.sessions),
                      inputs.issuer_tr_returns)
    from research.stocks_free_v3.family_tom_settle.schedule import (
        build_schedule as _build,
    )
    return _build(binding.config, list(inputs.sessions))


def schedule_entries(arm_id: str, inputs: ArmInputs) -> list[dict]:
    """Factory-shaped schedule entries for the publication gate (no PnL)."""
    binding = build_registry()[arm_id]
    if binding.family_id == "SFV3-A5-IDIO-SHOCK-REVERSAL":
        sched = build_arm_schedule(arm_id, inputs)
        records = sched.records if hasattr(sched, "records") else sched.entries
        return [dict(r) for r in records]
    from research.stocks_free_v3.family_tom_settle.dryrun import (
        schedule_book_entries,
    )
    from research.stocks_free_v3.family_tom_settle.schedule import (
        build_schedule as _build,
    )
    return [dict(e) for e in schedule_book_entries(
        _build(binding.config, list(inputs.sessions)))]


def run_arm_dry_run(arm_id: str, inputs: ArmInputs, *,
                    ledger_dir: str | None = None,
                    publish_to_temp_ledger: bool = False,
                    cost_bps: float = BASE_COST_BPS) -> dict:
    """Dispatch the exact-arm dry-run; returns report facts only (no scored
    metrics are extracted, returned or persisted)."""
    binding = build_registry()[arm_id]
    if binding.family_id == "SFV3-A5-IDIO-SHOCK-REVERSAL":
        from research.stocks_free_v3.family_idio_shock.dryrun import dry_run_arm
        assert inputs.issuer_tr_returns is not None
        report = dry_run_arm(
            binding.config, list(inputs.sessions), inputs.issuer_tr_returns,
            inputs.raw_close, inputs.distributions, inputs.split_factors,
            ledger_dir=ledger_dir,
            publish_to_temp_ledger=publish_to_temp_ledger,
            cost_bps=cost_bps,
        )
    else:
        from research.assets.stocks.factory import GatedTrialLedger
        from research.stocks_free_v3.family_tom_settle.dryrun import (
            run_exact_arm_dry_run,
        )
        # in-memory fresh temporary ledger; the Phase-Q publication battery
        # separately proves on-disk first-publication/replay idempotence.
        ledger = GatedTrialLedger(path=None)
        report = run_exact_arm_dry_run(
            binding.config, list(inputs.sessions), inputs.raw_close,
            inputs.distributions, inputs.split_factors,
            cost_bps=cost_bps, ledger=ledger, trial_key=arm_id,
        )
    return (
        report.to_payload() if hasattr(report, "to_payload") else dict(
            report.__dict__))


__all__ = [
    "ArmBinding",
    "ArmInputs",
    "EXECUTION_ORDER",
    "S0_FOLDS",
    "S1_END",
    "S1_START",
    "SELECTION_SHA",
    "WIRED_AT_UTC",
    "build_arm_schedule",
    "build_registry",
    "run_arm_dry_run",
]
