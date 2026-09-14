"""COMMODITIES-NG1 I-phase family runner machinery.

Implements the FROZEN selection (research/control/commodities_ng1_run/
s/selection_freeze.json, binding): the single eligible family
COMMNG1-A4-P2 (crowd-carry persistence, continuation-until-positioning-
trigger on the ETP leg) x exactly 3 booked arms = 3 cells, plus the
binding I-phase control battery and the R1-R6 stage-A scaffolding.

Modules
-------
rule      the frozen decision-rule machinery (pure functions on weekly
          chains; semantics pinned verbatim to the D2 committed
          measurement code ``measure_novelty.py::state_a4p2`` and
          ``percentile_tail`` -- decision-STATE machinery only, no
          outcomes).
chain     weekly decision-grid chain assembly: CoT facts via the P0
          plane + kernel-side PIT guard, ETP legs RAW-primary, V7
          close+1 readability (D1 stricter convention), counted-window
          logic and the fail-closed P2 census identity.
execute   decision series -> kernel trade events (fills at the decision
          session EOD close, cost exactly ONCE per fill, split-boundary
          law, terminal policy) through the P1 dual-book kernel.
battery   the binding I-phase control battery: price-only shadow,
          release-clock shadow, shifted-release placebo (k=4), delay
          pair, clairvoyant ceiling; the D1 falsification rule; Q-11
          invalid-null eligibility law.
stage_a   R1-R6 stage-A rule scaffolding over the frozen folds; PBO
          fail-closed law (cells < 8) with the FOREX-NG1 precedent
          alternative cited.
dry_run   the ``--dry-run-plumbing`` self-check: structural plumbing
          only (digests, counts, config assembly) -- NO PnL, no
          outcome numbers, on synthetic data in tests.

I-PHASE LAW: nothing here may be SCORED on real data in I; real
substrate access is limited to structural plumbing (digests, counts,
config assembly).  Every outcome-producing function is exercised in the
I tests on SYNTHETIC fixtures only.
"""

from research.assets.commodities_ng1.runners.battery import (  # noqa: F401
    KILLER_ROLES,
    SHIFTED_RELEASE_K_FROZEN,
    battery_position_series,
    falsification_eval,
    q11_eligibility,
)
from research.assets.commodities_ng1.runners.chain import (  # noqa: F401
    build_pair_chain,
    verify_pair_census,
)
from research.assets.commodities_ng1.runners.execute import (  # noqa: F401
    decision_trades,
    arm_metrics,
    book_ledger,
    trades_to_folds,
)
from research.assets.commodities_ng1.runners.rule import (  # noqa: F401
    clairvoyant_positions,
    crowd_carry_positions,
    percentile_tail,
    price_only_positions,
    release_clock_positions,
    shifted_release_positions,
    sign,
)
from research.assets.commodities_ng1.runners.stage_a import (  # noqa: F401
    FOLDS_FROZEN,
    evaluate_stage_a,
    fold_of,
    pbo_verdict,
)

__all__ = [
    "KILLER_ROLES",
    "SHIFTED_RELEASE_K_FROZEN",
    "FOLDS_FROZEN",
    "arm_metrics",
    "clairvoyant_positions",
    "battery_position_series",
    "book_ledger",
    "build_pair_chain",
    "crowd_carry_positions",
    "decision_trades",
    "evaluate_stage_a",
    "falsification_eval",
    "fold_of",
    "pbo_verdict",
    "percentile_tail",
    "price_only_positions",
    "q11_eligibility",
    "release_clock_positions",
    "shifted_release_positions",
    "sign",
    "trades_to_folds",
    "verify_pair_census",
]
