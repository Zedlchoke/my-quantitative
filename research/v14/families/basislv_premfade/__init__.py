"""A14-V14-A5-BASISLV-PREMFADE -- cross-sectional perp-premium level fade.

Frozen mechanism (selection_freeze_v14.json +
research/proposals/v14/a5/BASISLV-PREMFADE.md, implemented faithfully --
no redesign; selection-freeze HEAD d16341f):

* signal = trailing mean premium level ``b_i(T) = mean(p_b)`` over the
  2688 completed 15m basis-route buckets (28d anchor) / 5376 buckets (56d
  neighbour), with ``p_b = (futuresPrice - indexPrice)/indexPrice``; the
  frozen lag convention makes a bucket available at its close boundary and
  the last admissible bucket for a Monday 00:00Z stamp is
  ``[Sun 23:45, Mon 00:00)``; every slot of the formation window must
  exist AND be available (fail-closed; one missing slot refuses the symbol
  at that stamp -- L-V12-5);
* book = long the ``floor(n_eligible/3)`` lowest-premium names (low /
  discount tier) / short the ``floor(n_eligible/3)`` highest-premium names
  (high / premium tier), equal weight ``1/(2*floor(n_eligible/3))`` per
  leg, gross 1.0, middle flat, ranks ascending by ``(b_i, symbol id)``
  (ties by symbol id ascending, declared a priori); minimum 12 eligible
  names per stamp (below that the stamp refuses, fail-closed);
  ``max |weight| = 1/8 = 0.125 <= 0.30`` by construction; BTCUSDT is
  benchmark/beta context only and never ranked;
* arms: ``BASISLV-PREMFADE-28D`` (anchor) / ``BASISLV-PREMFADE-56D``
  (neighbour) / ``BASISLV-PREMFADE-28D-INV`` (causal negative control: the
  EXACT sign-inverted anchor book); preregistered falsification: if the
  inversion passes the incremental gate while the anchor passes, the
  premium ordering carries no directional crowding information and the
  family is falsified (see :mod:`research.v14.families.basislv_premfade.gate_runner`);
* the PRICE-ONLY FAILURE CLAUSE is a binding gate input: the scored layer
  computes the price-only vs total expectancy split and the gate runner
  applies it (price-only <= 0 with positive-total-only-via-funding =>
  carry-harvest artifact => family rejected, declared ex ante);
* clock = weekly Monday 00:00:00Z decisions; ONE declared execution lag:
  fills at the close of the first completed 15m bar strictly after the
  decision stamp (Monday 00:15Z close; the +1-delay stress fills at the
  00:30Z close); holding 7 days, force-flat at fold boundaries;
* folds = frozen chronological F0/F1/F2 over the blind-S0 screen window
  2025-08-22..2026-08-21 with the 1-day trailing purge (the frozen
  V11-lineage ``purge_fold_members`` convention: exactly one stamp,
  2026-04-20, falls inside the F1 purge zone, leaving 51 effective Mondays
  at 17/17/17 -- A9-F measured; A9F-OBS-4 recorded);
* costs = the L-V14-0 remediated kernel: charged on FILLS ONLY, real
  perp-metadata tick sizes, native funding settlements once, identical
  across arms; funding is never a signal input;
* data = the A9-F staged basis observables (staged_basis_manifest.json;
  per-file SHA-256 verified at load, fail-closed on mismatch) plus the
  authorized staged bars/funding/perp-metadata snapshots.

SCOPE BOUNDARY: nothing in this package computes PnL, returns or any
scored metric; real data are READ-ONLY workspace files.
"""

from research.v14.families.basislv_premfade.frozen_identity import (
    BASISLV_ARM_CONFIG_DIGESTS,
    frozen_arm_config,
    frozen_arm_digest_report,
    frozen_identity,
)
from research.v14.families.basislv_premfade.gate_runner import (
    CONTROL_NEVER_PROMOTABLE,
    evaluate_family_gate,
    incremental_gate,
    price_only_clause,
)
from research.v14.families.basislv_premfade.plugin import (
    BasislvPremfadePlugin,
    family_stress_cell,
    fold_terminal_force_flat_stamps,
)
from research.v14.families.basislv_premfade.strategy import (
    ANCHOR_ARM,
    ARM_IDS,
    ARM_ROLES,
    CONTROL_ARM,
    EligibilityShortfall,
    FAMILY_ID,
    NEIGHBOUR_ARM,
    compute_targets_at,
    premium_level_at,
    stamp_calendar,
)

__all__ = [
    "ANCHOR_ARM",
    "ARM_IDS",
    "ARM_ROLES",
    "BASISLV_ARM_CONFIG_DIGESTS",
    "CONTROL_ARM",
    "CONTROL_NEVER_PROMOTABLE",
    "EligibilityShortfall",
    "FAMILY_ID",
    "BasislvPremfadePlugin",
    "NEIGHBOUR_ARM",
    "compute_targets_at",
    "evaluate_family_gate",
    "family_stress_cell",
    "fold_terminal_force_flat_stamps",
    "frozen_arm_config",
    "frozen_arm_digest_report",
    "frozen_identity",
    "incremental_gate",
    "premium_level_at",
    "price_only_clause",
    "stamp_calendar",
]
