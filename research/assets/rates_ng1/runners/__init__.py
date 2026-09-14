"""RATES-NG1 I-phase runner machinery for the frozen selection.

Cycle RATES-NG1, task rates-ng1-i-implementation (dispatch packet
invocation lead-bg-rates-i).  The S-phase selection freeze
(research/control/rates_ng1_run/s/selection_freeze.json, BINDING) named
ONE family -- RATESNG1-A5-P1 curvature-gated slope on the
level-orthogonalized par-curve shape -- with 3 gate-variant arms
(NEUTRAL / CONSERVATIVE / AGGRESSIVE), the tenor-bracket leg law
2 Yr -> SHY / 30 Yr -> TLT, the frozen tier-2.0 cost treatment (CS p90
per leg, charged once per fill on BOTH legs, ACT/365F expense drag), the
equal-thirds folds, the control battery (level-vs-shape decomposition
control = declared executioner, clock-only shadow, k=5 misaligned
placebo) and the R1-R6 rule order adapted from the FOREX-NG1 precedent.

This package implements the runner machinery ONLY:

- ``runner``   : the frozen decision rule (state machinery + position
  law + dual-book kernel booking) and cell-config assembly.
- ``battery``  : the control battery (declared executioner + secondary
  executioners) with Q-11 invalid-vs-null discipline.
- ``rules``    : R1-R6 scaffolding (frozen bounds, folds) + the PBO law
  (fail-closed NOT_RUN below 8 cells, per the ng1 plan law).
- ``fixtures`` : SYNTHETIC fixture builders shared by the unit tests and
  the --dry-run-plumbing self-check.

SCOPE LAW (I phase): unit tests and the dry-run self-check run on
SYNTHETIC fixtures only.  NO scored execution on real data, NO outcome
numbers on real data anywhere in I.  Real-substrate access is limited
to structural plumbing (digests, series lengths, config assembly).
Emitted decision series are structural records: state, position, fold
and cost-EVENT structure -- never after-cost outcomes.  S1 stays
SEALED_UNTOUCHED.
"""

from research.assets.rates_ng1.runners.battery import (  # noqa: F401
    align_defined_pairs,
    battery_verdict,
    out_earning_kill,
    placebo_state,
)
from research.assets.rates_ng1.runners.runner import (  # noqa: F401
    PairedLegBooks,
    arm_state_series,
    assemble_cell_configs,
    book_round_trips,
    canonical_digest,
    clock_only_state,
    curve_coordinates,
    gate_state_series,
    level_control_state,
    load_representation,
    misaligned_state,
    ols_residual_on_level,
    positions_from_states,
    quantile_cut,
    round_trip_leg_signed_pnl,
    run_arm,
)
from research.assets.rates_ng1.runners.rules import (  # noqa: F401
    evaluate_r1_r6,
    fold_bounds,
    fold_of_session,
    pbo_record,
    scan_emission_for_outcome_tokens,
)
from research.assets.rates_ng1.runners.dryrun import (  # noqa: F401
    build_i_gate_payload,
    dry_run_plumbing,
)

SCHEMA = "rates_ng1/runners@1"
