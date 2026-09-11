"""Frozen run configuration for the FOREX-NG1 I-phase cell runners.

Authority chain (read at load time, never re-typed):

- ``selection_freeze_path``  : research/control/forex_ng1_run/
  selection_freeze.json (families, trial budget, Stage-A rule order,
  cost contract, folds);
- ``proposal paths``         : the two selected families' frozen proposals
  (arm batteries with every parameter).

Canonical arm configs are DERIVED from those bytes; ``arm_config_digest``
is sha256 of the canonical JSON (sort_keys, tight separators) -- the P-12
representation identity the run contract pins.  Re-computing the digests
from the committed spec must reproduce the contract's digests exactly.

Budget-cell mapping (6 = 2 families x 3 arms, plan section 6 rubric #5;
basis recorded because each proposal carries a wider falsification
battery than the budget): the family control cell is the V8-law
nominal-exposure control CTL-DGS10LEVEL on both families, per

- selection_freeze.stage_a_rule_order_frozen R2: "control out-earns
  anchor same-sign >= 0.5x per-trade (V8 law; for A5 ADDITIONALLY the
  V7-recap kill R2' if CTL-V7RECAP reproduces anchor)" -- the standard
  R2 control is the V8-law nominal-exposure kill and CTL-V7RECAP is an
  additional check, not the budget cell;
- plans/PLAN_forex_ng1.md section 1: "a nominal-exposure control is
  MANDATORY on every yield/inflation lane" (both selected families are
  CPI/inflation lanes);
- V8 run-contract precedent: arms = anchor/neighbour/control with
  control = control_dgs10_level_z252_21bd.

The remaining battery books (A5 CTL-V7RECAP, both SHADOW-CLOCK shadows,
both seeded placebos) are fully implemented here for the E-phase
falsification ladder but are NOT budget cells; the dry-run covers exactly
the six budget cells.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

DEFAULT_CONTROL_DIR = os.path.join(
    REPO_ROOT, "research/control/forex_ng1_run")
DEFAULT_SELECTION_FREEZE = os.path.join(
    DEFAULT_CONTROL_DIR, "selection_freeze.json")
DEFAULT_PROPOSAL_A5_P1 = os.path.join(
    DEFAULT_CONTROL_DIR, "d1/proposals/proposal_A5_P1.json")
DEFAULT_PROPOSAL_A4_P2 = os.path.join(
    DEFAULT_CONTROL_DIR, "d1/proposals/proposal_A4_P2.json")

#: The S0 window (V9-inherited start; tail trimmed per plan section 3).
S0_WINDOW = {"start": "2018-04-04", "end": "2025-04-30"}

#: Frozen temporal folds (selection_freeze R3): month spans -> date bounds.
FOLD_BOUNDS = (
    (date(2018, 4, 1), date(2020, 6, 30)),
    (date(2020, 7, 1), date(2022, 10, 31)),
    (date(2022, 11, 1), date(2025, 4, 30)),
)
FOLD_LABELS = ("2018-04..2020-06", "2020-07..2022-10", "2022-11..2025-04")

#: Frozen cost contract (selection_freeze.cost_contract_frozen):
#: 1.5 bps per side x stress tier {1.0, 1.5, 2.0}; tier 2.0 PRIMARY;
#: charged exactly once per fill (entry and exit are separate fills).
COST_BPS_PER_SIDE = 1.5
COST_TIER_LADDER = (1.0, 1.5, 2.0)
PRIMARY_TIER = 2.0
#: USD-unit notional per fired 1-unit pair-decision (V2..V8 inherited
#: frozen PnL identity design: results already USD at this notional).
NOTIONAL_USD_UNIT = 10000.0

#: Placebo RNG (frozen by proposal A5-P1, P-12/P-15): numpy default_rng,
#: one draw, seed committed before any outcome.
PLACEBO_RNG_SEED = 20260911
PLACEBO_RNG_KIND = "numpy.random.default_rng"

#: Holding horizon H (grid days) -- identical (H=5) in both proposals'
#: frozen_parameters.
HOLD_GRID_DAYS = 5

FAMILY_A5_P1 = "FXNG1-A5-P1"
FAMILY_A4_P2 = "FXNG1-A4-P2"

#: The six budget cells (2 families x anchor/neighbour/control).
BUDGET_ARMS = (
    (FAMILY_A5_P1, "FXNG1-A5-P1-ANCHOR"),
    (FAMILY_A5_P1, "FXNG1-A5-P1-NEIGH-COOPEN"),
    (FAMILY_A5_P1, "FXNG1-A5-P1-CTL-DGS10LEVEL"),
    (FAMILY_A4_P2, "FXNG1-A4-P2-ANCHOR"),
    (FAMILY_A4_P2, "FXNG1-A4-P2-NEIGH-SMOOTH2"),
    (FAMILY_A4_P2, "FXNG1-A4-P2-CTL-DGS10LEVEL"),
)

#: Non-budget battery books implemented for the E-phase falsification
#: ladder (proposal arm_battery entries not occupying budget cells).
BATTERY_ONLY_ARMS = (
    (FAMILY_A5_P1, "FXNG1-A5-P1-CTL-V7RECAP"),
    (FAMILY_A5_P1, "FXNG1-A5-P1-SHADOW-CLOCK"),
    (FAMILY_A5_P1, "FXNG1-A5-P1-PLACEBO-ORDSHUF"),
    (FAMILY_A4_P2, "FXNG1-A4-P2-SHADOW-CLOCK"),
    (FAMILY_A4_P2, "FXNG1-A4-P2-PLACEBO-SHAM7D"),
)

ALL_ARMS = tuple(BUDGET_ARMS) + tuple(BATTERY_ONLY_ARMS)

ARM_ROLE = {
    "FXNG1-A5-P1-ANCHOR": "anchor",
    "FXNG1-A5-P1-NEIGH-COOPEN": "neighbour",
    "FXNG1-A5-P1-CTL-DGS10LEVEL": "control",
    "FXNG1-A5-P1-CTL-V7RECAP": "v7_ancestry_control",
    "FXNG1-A5-P1-SHADOW-CLOCK": "clock_only_shadow",
    "FXNG1-A5-P1-PLACEBO-ORDSHUF": "placebo_order_shuffle",
    "FXNG1-A4-P2-ANCHOR": "anchor",
    "FXNG1-A4-P2-NEIGH-SMOOTH2": "neighbour",
    "FXNG1-A4-P2-CTL-DGS10LEVEL": "control",
    "FXNG1-A4-P2-SHADOW-CLOCK": "clock_only_shadow",
    "FXNG1-A4-P2-PLACEBO-SHAM7D": "placebo_non_print_days",
}

FAMILY_OF_ARM = {arm: fam for fam, arm in ALL_ARMS}

DEFAULT_PROPOSAL_PATHS = {
    FAMILY_A5_P1: DEFAULT_PROPOSAL_A5_P1,
    FAMILY_A4_P2: DEFAULT_PROPOSAL_A4_P2,
}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
# frozen spec loading + digest verification (fail-closed)
# --------------------------------------------------------------------------- #

def load_selection_freeze(path: str = DEFAULT_SELECTION_FREEZE) -> dict:
    freeze = _load_json(path)
    if freeze.get("schema") != "forex_ng1_selection_freeze@1":
        raise ValueError(
            f"selection freeze schema {freeze.get('schema')!r} != "
            "'forex_ng1_selection_freeze@1' (fail-closed)")
    if freeze.get("trial_budget") != 6 or freeze.get("arm_count") != 6:
        raise ValueError(
            "selection freeze budget/arm_count drift: "
            f"{freeze.get('trial_budget')}/{freeze.get('arm_count')} != 6/6")
    return freeze


def verify_proposal_pins(paths: dict | None = None,
                         freeze: dict | None = None) -> dict:
    """Verify each proposal file's sha256 against the selection freeze's
    pinned proposal_sha256 (fail-closed on any drift)."""
    paths = paths or DEFAULT_PROPOSAL_PATHS
    freeze = freeze or load_selection_freeze()
    pinned = {f["family_id"]: f["proposal_sha256"]
              for f in freeze["selected_families"]}
    out = {}
    for fam, path in paths.items():
        digest = sha256_file(path)
        if digest != pinned.get(fam):
            raise ValueError(
                f"{fam} proposal sha256 drift: {digest} != pinned "
                f"{pinned.get(fam)} (fail-closed)")
        out[fam] = digest
    return out


# --------------------------------------------------------------------------- #
# canonical arm configs (P-12 representation identity)
# --------------------------------------------------------------------------- #

def _cost_contract() -> dict:
    return {
        "model": "bps_per_side_x_tier_charged_once_per_fill",
        "bps_per_side": COST_BPS_PER_SIDE,
        "tier_ladder": list(COST_TIER_LADDER),
        "primary_tier": PRIMARY_TIER,
        "fills_per_round_trip": 2,
        "notional_usd_per_unit": NOTIONAL_USD_UNIT,
        "basis": "selection_freeze.cost_contract_frozen (referenced "
                 "V2/V8 proxy ladder; Q-8 measured constants supersede "
                 "when published -- cost verdict NOT_RUN without them "
                 "at scored time, never an assumed spread)",
    }


def _common_identity(representation_id: str, proposal_sha256: str) -> dict:
    return {
        "grid": "daily 16:00 America/New_York FX-trading-day grid "
                "(zoneinfo DST; V9 frozen representation)",
        "window": dict(S0_WINDOW),
        "folds": list(FOLD_LABELS),
        "fold_force_flat": "positions never span a fold boundary; forced "
                           "exit at the fold's last grid day",
        "exit_rule": f"H={HOLD_GRID_DAYS} grid days; forced exit at the "
                     f"{S0_WINDOW['end']} grid instant; post-window "
                     "entries dropped",
        "costs": _cost_contract(),
        "representation_id": representation_id,
        "proposal_sha256": proposal_sha256,
    }


def arm_frozen_config(arm_id: str,
                      proposal_paths: dict | None = None) -> dict:
    """The canonical frozen config of one arm, derived from the committed
    proposal bytes.  sha256(canonical JSON) is the arm_config_digest."""
    proposal_paths = proposal_paths or DEFAULT_PROPOSAL_PATHS
    fam = FAMILY_OF_ARM[arm_id]
    proposal = _load_json(proposal_paths[fam])
    rid = proposal["representation_identity"]["representation_id"]
    psha = sha256_file(proposal_paths[fam])
    cfg = _common_identity(rid, psha)
    cfg["family_id"] = fam
    cfg["arm_id"] = arm_id
    cfg["arm_role"] = ARM_ROLE[arm_id]
    fp = proposal["information_source_and_surprise_construction"][
        "frozen_parameters"]

    if fam == FAMILY_A5_P1:
        cfg["surprise"] = "s1 = 100*(I_print / (I(m-1)*I(m-12)/I(m-13)) - 1)"
        cfg["threshold_pp"] = fp["anchor_threshold_pp"]
        cfg["holding_grid_days"] = fp["anchor_holding_grid_days"]
        cfg["event_instrument_law"] = ("each fired event trades the "
                                       "opener economy's OWN pair, 1 unit")
        cfg["direction_law"] = ("s1 >= +thr -> long funded currency vs "
                                "USD (CA inverts the pair); s1 <= -thr "
                                "mirror; |s1| < thr no position")
        cfg["entry_clock"] = ("D(e) = first 16:00-NY grid instant "
                              "strictly after max(EOD(operative_vintaged_"
                              "available_from), EOD(P_us_same_month))")
        if arm_id == "FXNG1-A5-P1-ANCHOR":
            cfg["event_set"] = ("the 50 unique opening-follower events "
                                "(US-anchored months with a provably "
                                "unique OF; interval-strict-before "
                                "order, fail-closed)")
        elif arm_id == "FXNG1-A5-P1-NEIGH-COOPEN":
            cfg["event_set"] = ("anchor events PLUS all provable "
                                "co-earliest prints of the no-unique-OF "
                                "months (104-event pool)")
        elif arm_id == "FXNG1-A5-P1-CTL-V7RECAP":
            cfg["event_set"] = ("ALL non-US first releases of the 77 "
                                "US-anchored months (openers, ties, "
                                "later followers alike; no order state)")
        elif arm_id == "FXNG1-A5-P1-CTL-DGS10LEVEL":
            cfg["book"] = ("identical fired ANCHOR book (same event days, "
                           "pairs, horizons, 1-unit magnitudes)")
            cfg["direction_rule"] = {
                "form": "nominal-yield-level exposure, print "
                        "conditioning removed",
                "state": "sign=+1 (long funded currency vs USD) iff the "
                         "DGS10 level as-of D(e) is below its trailing "
                         "252-grid-day median, else -1 (ties -> -1)",
                "dgs10_asof_law": "value in effect at day g = row with "
                                  "max realtime_start <= g (V8 staged "
                                  "vintaged manifest semantics); each "
                                  "window value bound at its own grid "
                                  "day, never re-pulled (AX2-C1)",
                "window": "252 grid days ending at and including D(e), "
                          "computed on the weekday-intersection grid "
                          "extended backward before S0 (DGS10 numeric "
                          "coverage starts 1962; no anchor event dropped "
                          "for warmup)",
                "series_pin": "DGS10 vintaged S2 bytes pinned from V8 "
                              "committed evidence (ctl_dgs10_pin.json)",
            }
        elif arm_id == "FXNG1-A5-P1-SHADOW-CLOCK":
            cfg["book"] = "identical fired ANCHOR book"
            cfg["direction_rule"] = ("constant +1 (always long the "
                                     "funded currency vs USD); zero "
                                     "information")
        elif arm_id == "FXNG1-A5-P1-PLACEBO-ORDSHUF":
            cfg["pool"] = ("threshold-passing (|s1| >= thr) non-US "
                           "first-release events of the 77 US-anchored "
                           "months, pool sorted by (publication_date, "
                           "economy, reference_period)")
            cfg["n_star"] = "the anchor's fired count"
            cfg["draw"] = "uniform without replacement, single draw"
            cfg["rng"] = {"kind": PLACEBO_RNG_KIND,
                          "seed": PLACEBO_RNG_SEED}
            cfg["fire_rule"] = ("each drawn event fires on its own pair "
                                "with its own sign(s1) at its own clock, "
                                "same H and units")
    elif fam == FAMILY_A4_P2:
        cfg["entry_clock"] = ("D(e) = first 16:00-NY grid instant "
                              "strictly after EOD(operative_vintaged_"
                              "available_from)")
        cfg["event_instrument_law"] = ("non-US events trade the "
                                       "economy's OWN pair (1 unit); US "
                                       "events fire 4 pair-decisions x "
                                       "1 unit")
        cfg["direction_law"] = ("surprise >= +thr -> long funded "
                                "currency vs USD (CA inverts; US: long "
                                "USD in all four pairs); <= -thr mirror; "
                                "|.| < thr no position")
        if arm_id == "FXNG1-A4-P2-ANCHOR":
            cfg["surprise"] = ("s2 = 100*(I_print / (I(m-12)*(1+pi_bar)) "
                               "- 1), pi_bar = I(m-1)/I(m-13) - 1")
            cfg["threshold_pp"] = fp["anchor_threshold_pp"]
            cfg["holding_grid_days"] = fp["anchor_holding_grid_days"]
            cfg["event_set"] = ("census first releases "
                                "(is_first_release_of_period) minus "
                                "pit_notes rows (306)")
        elif arm_id == "FXNG1-A4-P2-NEIGH-SMOOTH2":
            cfg["surprise"] = ("s2' = 100*(I_print / (I(m-12)*(1+pi_bar2))"
                               " - 1), pi_bar2 = mean(I(m-1)/I(m-13)-1, "
                               "I(m-2)/I(m-14)-1)  (quarterly feeds: the "
                               "corresponding observation-step lags)")
            cfg["threshold_pp"] = fp["anchor_threshold_pp"]
            cfg["holding_grid_days"] = fp["anchor_holding_grid_days"]
            cfg["event_set"] = "same census event set as the anchor"
        elif arm_id == "FXNG1-A4-P2-CTL-DGS10LEVEL":
            cfg["book"] = ("identical fired ANCHOR book (same event days, "
                           "pairs, horizons, 1-unit magnitudes)")
            cfg["direction_rule"] = {
                "form": "nominal-yield-level exposure, print "
                        "conditioning removed",
                "state": "sign=+1 (long funded currency vs USD; for US "
                         "events long USD in all four pairs) iff the "
                         "DGS10 level as-of D(e) is below its trailing "
                         "252-grid-day median, else -1 (ties -> -1)",
                "dgs10_asof_law": "value in effect at day g = row with "
                                  "max realtime_start <= g (V8 staged "
                                  "vintaged manifest semantics); each "
                                  "window value bound at its own grid "
                                  "day, never re-pulled (AX2-C1)",
                "window": "252 grid days ending at and including D(e), "
                          "computed on the weekday-intersection grid "
                          "extended backward before S0 (DGS10 numeric "
                          "coverage starts 1962; no anchor event dropped "
                          "for warmup)",
                "series_pin": "DGS10 vintaged S2 bytes pinned from V8 "
                              "committed evidence (ctl_dgs10_pin.json)",
            }
        elif arm_id == "FXNG1-A4-P2-SHADOW-CLOCK":
            cfg["book"] = "identical fired ANCHOR book"
            cfg["direction_rule"] = ("constant +1 (always long the "
                                     "funded currency vs USD; US events "
                                     "always long USD in all four pairs)")
        elif arm_id == "FXNG1-A4-P2-PLACEBO-SHAM7D":
            cfg["sham_rule"] = ("every fired anchor event day shifted +7 "
                                "calendar days; collision with a real "
                                "fired event day of the same pair shifts "
                                "again +7 (max 4 attempts, else drop); "
                                "off-grid landings snap forward to the "
                                "next grid day")
            cfg["direction_rule"] = ("the SAME surprise sign as the "
                                     "source event (stale information)")
            cfg["same"] = ("horizon, units, fills and costs identical "
                           "to the anchor")
    else:                                           # pragma: no cover
        raise ValueError(f"unknown arm {arm_id!r}")
    return cfg


def canonical_config_bytes(cfg: dict) -> bytes:
    return json.dumps(cfg, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def arm_config_digest(arm_id: str,
                      proposal_paths: dict | None = None) -> str:
    blob = canonical_config_bytes(
        arm_frozen_config(arm_id, proposal_paths))
    return hashlib.sha256(blob).hexdigest()


def budget_arm_digests(proposal_paths: dict | None = None) -> dict:
    """arm_id -> arm_config_digest for the six budget cells (pairwise
    distinct enforced by the run contract; asserted here too)."""
    digests = {arm: arm_config_digest(arm, proposal_paths)
               for _, arm in BUDGET_ARMS}
    values = list(digests.values())
    if len(set(values)) != len(values):
        raise ValueError("arm_config_digest collision among budget arms")
    return digests


def fold_of_day(day: date) -> int:
    """1-based fold index of a grid day (every S0 grid day is covered by
    exactly one frozen fold span)."""
    for i, (lo, hi) in enumerate(FOLD_BOUNDS, start=1):
        if lo <= day <= hi:
            return i
    raise ValueError(f"day {day} outside the frozen folds (fail-closed)")
