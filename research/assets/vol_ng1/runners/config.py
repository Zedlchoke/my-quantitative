"""VOL-NG1 I-phase frozen run configuration (task vol-ng1-i-implementation).

Authority chain (read at load time, never re-typed):

- ``selection_freeze``  : research/control/vol_ng1_run/s/selection_freeze.json
  (BINDING: the two frozen families, the six arm configs with their
  recorded arm_config_digests, the R1-R6 rule order, the cost binding
  c8529b88 tier-2.0 + Q-16 path ladder, the frozen folds, the I-phase
  control battery and the representation freeze);
- ``p1_cost_contract``  : research/control/vol_ng1_run/p1_cost_contract.json
  (the frozen measured cost contract cited by the freeze);
- the P1 kernel/assets    : research/assets/vol_ng1/{accounting,costs,
  clocks,corp_actions,feasibility,plane_adapter}.py (FROZEN -- consumed,
  never modified by this lane);
- the D2 committed state builders : research/control/vol_ng1_run/d2/
  d2_novelty.py (the freeze's parameter_freeze_rationale binds the I
  phase to "re-use the D2 committed state builders unchanged").

Canonical arm configs are DERIVED from the freeze bytes;
``arm_config_digest`` is sha256 of the canonical JSON of the arm's
'config' object ONLY (json.dumps(sort_keys=True, separators=(',',':'),
ensure_ascii=True)) -- the freeze's own digest_law.  Recomputation must
reproduce the freeze's recorded digests exactly and pairwise distinct.

PBO LAW (packet + plans/PLAN_forex_ng1.md section 5 precedent): PBO/CSCV
is fail-closed NOT_RUN when cells < 8 (V17 contract).  This cycle books
6 cells, so PBO is NOT_RUN here; the frozen alternative robustness rule
recorded in the FOREX-NG1 precedent is R6 NON_CONCENTRATION
(drop-one-fold survival + no single round trip > 50% of the cell's
gross), inherited verbatim -- provenance commits read read-only via
``git show`` from orca/forex-ng1-integration:
d0992d17df8e2dfde57c9a0806a5798f14021a4f
(research/control/forex_ng1_run/selection_freeze.json,
stage_a_rule_order_frozen[5]) and
f6c17886c32025242fdf21ffb8565666d64cbaec
(research/assets/forex_ng1/run/evaluator.py) -- the exact shas the
freeze's rule_set_r1_r6 provenance section cites.

NO scored execution, NO outcome numbers on real data, NO PnL anywhere
in the I lane: the runners emit decision series + kernel events only;
scored expectancy/PF metrics are supplied EXTERNALLY at E under scored
authority.  ``research.assets.vol_ng1.accounting.compute_outcomes``
keeps refusing (tested).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

SELECTION_FREEZE_PATH = os.path.join(
    REPO_ROOT, "research", "control", "vol_ng1_run", "s",
    "selection_freeze.json")
COST_CONTRACT_PATH = os.path.join(
    REPO_ROOT, "research", "control", "vol_ng1_run", "p1_cost_contract.json")

SCHEMA = "vol_ng1_runners/i_config@1"
TASK_ID = "vol-ng1-i-implementation"
CYCLE_ID = "VOL-NG1"
INVOCATION = "lead-bg-vol-i"

#: Frozen cost binding (selection_freeze.cost_contract_binding).
COST_TIER_LADDER = (1.0, 1.5, 2.0)
PRIMARY_TIER = 2.0
FROZEN_COST_CONTRACT_SHA256 = (
    "c8529b888c5c92e04802ddda8006a74b3f94d099cb14c4dd6d64a1df1ce2d1a4")

#: Frozen battery constants (selection_freeze.i_phase_control_battery).
CALENDAR_SHIFT_K_SESSIONS = 5
PLACEBO_SEED = 20260912
PLACEBO_RNG_KIND = "numpy.random.default_rng"

#: Structural notional unit for kernel plumbing (I is UNSCORED: this
#: constant fixes the plumbing's fill/cost arithmetic only; no outcome
#: number on real data is ever produced in I).
NOTIONAL_USD_UNIT = 10_000.0

#: Frozen R1-R6 rule bars (selection_freeze.rule_set_r1_r6, inherited
#: verbatim from the FOREX-NG1 stage-A order).
PF_BAR = 1.10
CONTROL_KILL_RATIO = 0.5
MIN_POSITIVE_FOLDS = 2
FOLDS_TOTAL = 3
MAX_ROUND_TRIP_GROSS_SHARE = 0.50

#: PBO law (see module docstring for the provenance citations).
PBO_MIN_CELLS = 8
PBO_PRECEDENT_COMMITS = (
    "d0992d17df8e2dfde57c9a0806a5798f14021a4f",
    "f6c17886c32025242fdf21ffb8565666d64cbaec",
)
PBO_ALTERNATIVE_RULE = (
    "R6 NON_CONCENTRATION: drop-one-fold survival + no single round "
    "trip > 50% of the cell's gross (frozen alternative robustness "
    "rule; FOREX-NG1 precedent stage_a_rule_order_frozen[5], commits "
    + ", ".join(PBO_PRECEDENT_COMMITS) + ")")

FAMILY_A4_P2 = "VOLNG1-A4-P2"
FAMILY_A5_P2 = "VOLNG1-A5-P2"

#: The frozen A4-P2 latch axis and A5-P2 asym axis, as frozen in the
#: six arm configs (verified against the freeze bytes at load).
A4_LATCH_M_AXIS = (2, 3, 4)
A5_ARM_AXES = {           # arm_id -> (asym_threshold, latch_sessions)
    "VOLNG1-A5-P2-ANCHOR": (0.5, 2),
    "VOLNG1-A5-P2-NEIGH-STRICT": (0.75, 3),
    "VOLNG1-A5-P2-NEIGH-FAST": (0.25, 1),
}

#: Frozen proxy constants (P2 C7, re-cited by every A5-P2 arm config):
#: consumed from research.assets.vol_ng1.feasibility at use time.

#: Index-only A5 shadow mid-side lookback: the committed MID-bucket
#: day gap (frozen cost contract path day_gap == 90, the only committed
#: longer lookback for the mid bucket; disclosure recorded in the
#: battery module and the I gate).
A5_SHADOW_SHORT_LOOKBACK = 21
A5_SHADOW_MID_LOOKBACK = 90

#: Index-only A4 shadow BOOK convention (audit
#: a7_prelaunch_vol_ng1.json finding H1, remediated pre-scored by the
#: addendum selection_freeze_addendum_a7r1.json): the A4-P2 index-only
#: shadow scores HYPOTHETICAL positions on the index series itself --
#: `state` units of the VIX close marked in INDEX POINTS, V7 close+1
#: re-clock, NO ETP leg and NO ETP costs (an index is not a tradable
#: instrument; PLAN_vol_ng1.md section 1a: "the same rule driven by the
#: vol index series alone with no ETP leg -- is the ETP decision
#: beating its own index re-clock?").  The shadow book is therefore a
#: genuinely different book from the arm's ETP book for every cell.
SHADOW_MARK_SERIES = "VIX"


class ConfigError(Exception):
    """Fail-closed frozen-config error: nothing inferred, nothing
    repaired."""


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj) -> str:
    """The freeze's digest_law canonical form."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def arm_config_digest(config: dict) -> str:
    """sha256 of the canonical JSON of the arm's 'config' object ONLY."""
    return hashlib.sha256(
        canonical_json(config).encode("utf-8")).hexdigest()


def load_selection_freeze(path: str | None = None) -> dict:
    """Fail-closed load of the BINDING selection freeze."""
    p = path or SELECTION_FREEZE_PATH
    if not os.path.isfile(p):
        raise ConfigError(f"selection freeze missing: {p}")
    with open(p, "r", encoding="utf-8") as fh:
        fz = json.load(fh)
    if fz.get("schema") != "vol_ng1_selection_freeze@1":
        raise ConfigError(
            f"selection freeze schema mismatch at {p}: "
            f"{fz.get('schema')!r}")
    if fz.get("s1_status") != "SEALED_UNTOUCHED":
        raise ConfigError("freeze s1_status is not SEALED_UNTOUCHED")
    return fz


def load_cost_contract(path: str | None = None) -> dict:
    """Fail-closed load of the frozen P1 cost contract + binding sha
    check against the freeze's citation."""
    p = path or COST_CONTRACT_PATH
    if not os.path.isfile(p):
        raise ConfigError(f"cost contract missing: {p}")
    measured = sha256_file(p)
    if measured != FROZEN_COST_CONTRACT_SHA256:
        raise ConfigError(
            f"cost contract sha256 drift: measured {measured} != frozen "
            f"{FROZEN_COST_CONTRACT_SHA256}")
    with open(p, "r", encoding="utf-8") as fh:
        cc = json.load(fh)
    if cc.get("schema") != "vol_ng1_run/p1_cost_contract@1":
        raise ConfigError(f"cost contract schema mismatch: {cc.get('schema')!r}")
    if tuple(cc.get("tier_ladder", [])) != COST_TIER_LADDER \
            or cc.get("primary_tier") != PRIMARY_TIER:
        raise ConfigError("cost contract tier ladder drift vs the freeze")
    return cc


def assemble_arm_configs(fz: dict | None = None) -> dict:
    """The six frozen cells, digests recomputed and checked.

    Returns arm_id -> {family_key, family_form, role, budget_cell,
    config, arm_config_digest (recomputed), recorded_arm_config_digest,
    digest_match, battery_binding}.  Any digest drift/collision or
    budget violation raises (fail-closed).
    """
    fz = fz or load_selection_freeze()
    plan = fz["arm_configuration_plan"]
    runner_map = {r["arm_id"]: r for r in
                  fz["i_phase_control_battery"]["runner_map"]}
    arms = {}
    for arm in plan["arms"]:
        aid = arm["arm_id"]
        cfg = arm["config"]
        recomputed = arm_config_digest(cfg)
        if recomputed != arm["arm_config_digest"]:
            raise ConfigError(
                f"{aid}: arm_config_digest drift: recomputed {recomputed} "
                f"!= recorded {arm['arm_config_digest']}")
        binding = runner_map.get(aid, {}).get("battery_binding")
        arms[aid] = {
            "arm_id": aid,
            "family_key": arm["family_key"],
            "family_form": cfg["family_form"],
            "role": arm["role"],
            "budget_cell": arm["budget_cell"],
            "config": cfg,
            "arm_config_digest": recomputed,
            "recorded_arm_config_digest": arm["arm_config_digest"],
            "digest_match": True,
            "battery_binding": binding,
        }
    if len(arms) != plan["arm_count"]:
        raise ConfigError(
            f"arm count {len(arms)} != frozen {plan['arm_count']}")
    cells = sorted(a["budget_cell"] for a in arms.values())
    if cells != list(range(1, plan["cells_total_max"] + 1)):
        raise ConfigError(f"budget cells not exactly 1..6: {cells}")
    digests = [a["arm_config_digest"] for a in arms.values()]
    if len(set(digests)) != len(digests):
        raise ConfigError("arm_config_digest collision (fail-closed)")
    return arms


def frozen_folds(fz: dict | None = None) -> tuple:
    """The three frozen fold windows as (fold, (start_date, end_date)),
    parsed from the freeze bytes (never re-typed)."""
    fz = fz or load_selection_freeze()
    rows = []
    for row in fz["rule_set_r1_r6"]["frozen_folds"]:
        w = row["window"]
        rows.append((row["fold"],
                     (date.fromisoformat(w[0]),
                      date.fromisoformat(w[1]))))
    if len(rows) != FOLDS_TOTAL:
        raise ConfigError(f"expected {FOLDS_TOTAL} frozen folds")
    return tuple(rows)


def fold_of(session: str, folds: tuple | None = None) -> int:
    """Fold index (1-based) of a session inside the frozen fold windows;
    fail-closed outside (never inferred)."""
    folds = folds or frozen_folds()
    d = date.fromisoformat(str(session))
    for i, (_name, (lo, hi)) in enumerate(folds, start=1):
        if lo <= d <= hi:
            return i
    raise ConfigError(
        f"session {session!r} outside the frozen fold windows "
        "(fail-closed; no fold inference)")


def cost_source_from_contract(contract: dict) -> dict:
    """Per-leg cost source wired to the FROZEN measured contract:
    leg -> {stress_spread_frac (Q-8 p90, full spread per round trip),
    bucket, expense_bps_per_day, path_formula, path_day_gap,
    path_adverse_tail_daily_bps} (the adverse tail per the P2 C9
    convention: max(|p10|, |p90|) of the measured path series)."""
    out = {}
    for leg, block in sorted(contract["legs"].items()):
        path = block["path_cost"]
        out[leg] = {
            "stress_spread_frac": float(block["spread"]["p90_spread_frac"]),
            "bucket": block["bucket"],
            "expense_bps_per_day": float(
                block["tiers"][str(PRIMARY_TIER)]["expense_bps_per_day"]),
            "path_formula": path["formula"],
            "path_day_gap": float(path["day_gap"]),
            "path_adverse_tail_daily_bps": max(
                abs(float(path["p10_daily_bps"])),
                abs(float(path["p90_daily_bps"]))),
        }
    if len(out) != 6:
        raise ConfigError(
            f"cost source needs exactly the 6 living legs, got {len(out)}")
    return out


def battery_constants(fz: dict | None = None) -> dict:
    """The battery constants as frozen in the freeze bytes (the module
    constants must equal them; equality is tested)."""
    fz = fz or load_selection_freeze()
    ctl = fz["i_phase_control_battery"]["controls"]
    return {
        "calendar_shift_k_sessions":
            ctl["calendar_clock_shadow"]["calendar_shift_k_sessions"],
        "placebo_seed": ctl["placebo"]["placebo_seed"],
    }
