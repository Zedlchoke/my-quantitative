"""ELITE-SIZE-ASYM (A5-V15-F1) implementation package -- A8-I lane, cycle
CRYPTO-V15.

Implements the FROZEN spec, in authority priority order:

1. ``research/control/v15_run/d1/a5/proposal_P1.json``
   (sha256 6d2bc25fc3d3e5ebd96ca60c8e428efed9823b94589073f41ddcbdf47392cb16)
   -- mechanism, anchor/neighbour/control definitions, entry/exit, fill
   model, costs;
2. ``research/control/v15_run/selection_freeze_v15.json`` -- selected arms
   and the ADJUDICATION: binding universe = the FROZEN 20 symbols (SOLUSDT
   included), tercile split 7/6/7 by asymmetry rank;
3. ``research/control/v15_run/p3_freeze_v15.json`` +
   ``p3_freeze_amendment_1.json`` -- weights cap 0.30 signed / gross <= 1.0,
   force-flat fold boundaries, folds F0/F1/F2 with 1-day purge,
   MEASURED_BOUND_LAG_3D, the >10% window-hole refusal rule, the cost-once
   schedule and the stress tiers (x1.5 fee / +2 ticks / +1 delay);
4. ``research/control/v15_run/p0_probe/probe_verdict_v15.json`` -- label
   semantics (labeled-T metrics row carries the stock snapshot at T+5min).

The implementer never improves a frozen spec (p3_freeze ambiguity_rule).
"""

from research.v15.families.elite_size_asym.frozen_identity import (
    ANCHOR_ARM,
    ARM_CONFIG_DIGESTS,
    ARM_IDS,
    ARM_ROLES,
    CONTROL_ARM,
    FAMILY_ID,
    NEIGHBOR_ARM,
    RECORDED_SPEC_SHA256,
    REMEDIATION_NOTE,
    SPEC_AUTHORITY_RELPATHS,
    UNIVERSE,
    verify_arm_digests,
    verify_spec_sha256s,
)

__all__ = [
    "ANCHOR_ARM",
    "ARM_CONFIG_DIGESTS",
    "ARM_IDS",
    "ARM_ROLES",
    "CONTROL_ARM",
    "FAMILY_ID",
    "NEIGHBOR_ARM",
    "RECORDED_SPEC_SHA256",
    "REMEDIATION_NOTE",
    "SPEC_AUTHORITY_RELPATHS",
    "UNIVERSE",
    "verify_arm_digests",
    "verify_spec_sha256s",
]
