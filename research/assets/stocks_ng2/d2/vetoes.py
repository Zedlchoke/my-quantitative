"""STOCKS-NG2 D2 veto registry: the SEVENTEEN-entry veto set.

  * entries 1-15: the V13 D2 audit veto set VERBATIM (names + generic
    family constructions + pooled midrank Spearman-on-common-pairs
    fail-closed semantics), reused UNCHANGED from the ng1 D2 machinery
    (research/assets/stocks_ng1/d2/vetoes.py - the constructions were
    already rebuilt as generic family forms on these same consumption
    surfaces: EODHD prices + the pinned stream).
  * entries 16-17: the ng1 10b5-1 kills (SFNG1-A4-P1 fdens / SFNG1-A4-P2
    planshare, both killed at D2 by goodwill_bloat -0.3547/-0.384),
    constructed by the ng1 D2 exposure machinery on THIS cycle's panel
    and grid - plan sec1: "10b5-1 forms remain dead; any proposal
    reducing to them dies at D2".

Every construction is a deterministic (entity, decision-close) ->
float-or-None function; None = UNMEASURED and fails the novelty gate
closed (never a pass by absence).
"""

from __future__ import annotations

from research.assets.stocks_ng1.d2 import exposures as ng1_exposures
from research.assets.stocks_ng1.d2 import vetoes as ng1_vetoes
from .core import VETO_NAMES, VETO_NAMES_15, VETO_NAMES_NG1

assert list(ng1_vetoes.VETO_BUILDERS) == VETO_NAMES_15, (
    "ng1 veto register drifted: the 15 V13 names must match verbatim")

VETO_BUILDERS = dict(ng1_vetoes.VETO_BUILDERS)
VETO_BUILDERS["ng1_10b5_1_fdens"] = ng1_exposures.fdens
VETO_BUILDERS["ng1_10b5_1_planshare"] = ng1_exposures.planshare
assert sorted(VETO_BUILDERS) == sorted(VETO_NAMES), "veto registry mismatch"

VETO_CONSTRUCTION_REGISTER = (
    "entries 1-15 = the ng1 D2 veto set verbatim (V13 D2 audit names "
    "$L1194-1213; generic family constructions on EODHD prices + the "
    "pinned stream; see research/assets/stocks_ng1/d2/vetoes.py module "
    "docstring, reused unchanged); entry 16 ng1_10b5_1_fdens = the ng1 "
    "SFNG1-A4-P1 anchor (distinct flagged 10b5-1-declared acceptance "
    "sessions in the trailing 63 sessions, defined iff >= 1); entry 17 "
    "ng1_10b5_1_planshare = the ng1 SFNG1-A4-P2 anchor (flagged dispose "
    "value share of all dispose value over nonDerivative D rows in the "
    "trailing 63 sessions; floors V_all >= 2,000 USD and >= 2 D rows) - "
    "both ng1 10b5-1 forms died at their own D2 (goodwill_bloat "
    "-0.3547/-0.384) and are carried as vetoes per plan sec1")
