"""Scored discovery runner (invoked ONLY by tools/cmd_scored.py after the
owner GO token passes the quarantine).

Constructed by A1 at integration; the shape is fixed by the plan + A6
freeze proposals:
- denominator: 21 scored cells = 3 cells x 7 arm instances
  (A1 ALWAYS_ON_MR, A2 ALWAYS_ON_TREND, B ORIGINAL_V2_MAPPING_REFERENCE,
   C REGIME_SPECIALIST_ROUTER, D SPARSE_JEV_RISK_OFF_VETO,
   E DETERMINISTIC_PROPOSAL_PLUS_JEV_VETO, F EPISODE_SHUFFLED_MATCHED);
- cost tiers 1.0/1.5/2.0 inside each cell run; fold force-flat;
- references (FLAT, buy-and-hold) computed, never scored;
- every outcome counted in the observed denominator even on publication
  failure; reproduction is a byte-compare of tier files;
- heavy lock held for the whole run (one machine-wide heavy job);
- NO mid-run stopping on ugly numbers; NO post-PnL edits.
"""

from __future__ import annotations


def run_all() -> int:
    raise NotImplementedError(
        "scored.run_all is completed at integration (specialist library + "
        "arms freezes must land first); the GO quarantine in tools/"
        "cmd_scored.py is the authority that gates entry to this function"
    )
