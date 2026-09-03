"""SFV3-A5-IDIO-SHOCK-REVERSAL: the A8 family module (3 frozen arms).

Implements the frozen executable spec of family ``SFV3-A5-IDIO-SHOCK-REVERSAL``
exactly as pinned in ``research/control/stocks_free_v3_run/selection_freeze.json``
(families[0]) with mechanism source
``research/proposals/stocks_free_v3/a5_family_idio_shock_reversal.md``,
including adjudication ``ADJ-1-EXEC-CLOCK`` (fills at the canonical session
CLOSE, not the proposal's original OPEN):

* :mod:`.features` — PIT rolling beta/sigma/z per completed session from
  issuer-TR daily returns (60-session OLS window inclusive of ``t``,
  population sigma, ddof=0);
* :mod:`.arms` — the three stable frozen arm config heads A1/N1/C1 with
  complete sha256 config digests over the canonical JSON of the frozen
  constants;
* :mod:`.schedule` — the deterministic trigger / selection / rolling-budget /
  concurrency-1 state machine emitting the canonical target-weight SCHEDULE
  (list of ``{entry_type, fill_date, targets (explicit CASH), cash_weight,
  turnover_one_way}`` dicts, the exact shape consumed by
  ``research.assets.stocks.factory.value_book`` and the V2 harness), plus
  schedule-only feasibility (entries/yr, gross exposure, two-way turnover vs
  the 6.0x/yr ceiling) — never any PnL;
* :mod:`.dryrun` — exact-arm dry-run: schedule build + canonical
  ``factory.value_book`` accounting + ``GatedTrialLedger`` publication gate in
  a TEMPORARY ledger with NO-PUBLISH semantics.

Schedule-only discipline: nothing in this package computes or persists any
scored metric on real data (no PnL/expectancy/PF/Sharpe/MDD over S0); the
sealed S1 (2025-08-01..2026-07-31) is never read (all real reads go through
``research.stocks_free_v3.isolation.SealedSnapshotReader``).
"""

from research.stocks_free_v3.family_idio_shock.arms import (
    ARM_A1,
    ARM_C1,
    ARM_N1,
    FROZEN_ARMS,
    FAMILY_ID,
    FrozenArmConfig,
)
from research.stocks_free_v3.family_idio_shock.features import (
    FeatureFrame,
    compute_features,
)
from research.stocks_free_v3.family_idio_shock.schedule import (
    build_arm_schedule,
    build_arm_schedule_from_features,
    schedule_feasibility,
)

__all__ = [
    "ARM_A1",
    "ARM_C1",
    "ARM_N1",
    "FROZEN_ARMS",
    "FAMILY_ID",
    "FeatureFrame",
    "FrozenArmConfig",
    "build_arm_schedule",
    "build_arm_schedule_from_features",
    "compute_features",
    "schedule_feasibility",
]
