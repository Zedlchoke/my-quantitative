"""COMMODITIES-NG1 binding I-phase control battery (S freeze section6).

The I phase MUST implement and run this battery on the IDENTICAL
bookable grid, restricted leg set and window, with the IDENTICAL
frozen cost treatment as the booked arms; omission or weakening of any
element fails the I gate.

Mandatory (designated KILLERS -- the D1 falsification rule kills on
ANY strictly greater after-cost per-decision edge; R2 V8 clause kills
on same-sign >= 0.5x per-trade):

- PRICE_ONLY_SHADOW: the SAME tradeable rule (same clock,
  hold-until-trigger shape, same symbolic parameters) with BOTH the
  state and the trigger replaced by price-only analogues; NO CoT
  input whatsoever (rule.price_only_positions);
- RELEASE_CLOCK_SHADOW: identical holding shape and execution, FIXED
  direction sign, no state and no trigger -- every grid instant pooled
  (rule.release_clock_positions);
- SHIFTED_RELEASE_PLACEBO: the identical state-and-trigger machinery
  fed reports k = 4 release-instants OLDER than the PIT-visible one
  (rule.shifted_release_positions); k FROZEN at 4 by the S freeze.

Diagnostic (do not kill alone):

- DELAY_PAIR: the identical anchor rule at D0 = the P2 later-bound
  decision session and D1 = the next session after D0; both reported
  side by side (execution_lag_sessions 0 vs 1 in execute.decision_trades);
- CLAIRVOYANT: the ceiling arm with full-sample bucket knowledge
  (rule.clairvoyant_positions); smoke-class numbers: kill + disclose,
  NEVER select (P-15).

Q-11 invalid-null law: an arm or control with fewer eligible instants
than the frozen minimum (300 per bookable pair; 3300 pooled across the
11-pair set) is NOT_RUN/INVALID on that scope -- never zero, never a
pass.
"""

from __future__ import annotations

from research.assets.commodities_ng1.runners import rule

SCHEMA = "commodities_ng1/runners/battery@1"

#: Designated KILLER controls (D1 falsification rule, frozen at S).
KILLER_ROLES = ("PRICE_ONLY_SHADOW", "RELEASE_CLOCK_SHADOW",
                "SHIFTED_RELEASE_PLACEBO")

#: Diagnostic controls (inform the I report; never kill alone).
DIAGNOSTIC_ROLES = ("DELAY_PAIR", "CLAIRVOYANT")

#: Stale-release placebo shift, FROZEN at 4 by the S freeze.
SHIFTED_RELEASE_K_FROZEN = 4

#: Q-11 frozen eligibility minima (S freeze section2 per_arm_min_law).
Q11_MIN_ELIGIBLE_PER_PAIR = 300
Q11_MIN_ELIGIBLE_POOLED = 3300

#: Fixed direction sign of the bare release-clock shadow (frozen).
RELEASE_CLOCK_FIXED_SIGN = 1.0


def battery_position_series(chain: dict, params: dict,
                            roles: tuple = KILLER_ROLES + DIAGNOSTIC_ROLES
                            ) -> dict[str, list]:
    """Decision series per battery role for ONE pair chain (the anchor
    series is included; the DELAY_PAIR role reuses it with an
    execution-lag mapping at booking time, not a separate series)."""
    anchor = rule.crowd_carry_positions(chain["rows"], params)
    out: dict[str, list] = {"ANCHOR": anchor}
    n = len(anchor)
    for role in roles:
        if role == "ANCHOR":
            continue
        if role == "PRICE_ONLY_SHADOW":
            out[role] = rule.price_only_positions(chain["rows"], params)
        elif role == "RELEASE_CLOCK_SHADOW":
            out[role] = rule.release_clock_positions(
                n, RELEASE_CLOCK_FIXED_SIGN)
        elif role == "SHIFTED_RELEASE_PLACEBO":
            out[role] = rule.shifted_release_positions(
                anchor, SHIFTED_RELEASE_K_FROZEN)
        elif role == "DELAY_PAIR":
            out[role] = list(anchor)   # D0/D1 = execution placement
        elif role == "CLAIRVOYANT":
            out[role] = rule.clairvoyant_positions(chain["rows"], params)
        else:
            raise ValueError(f"unknown battery role {role!r}")
    return out


#: Execution lag (sessions after D0) per battery role.
EXECUTION_LAG = {"ANCHOR": 0, "PRICE_ONLY_SHADOW": 0,
                 "RELEASE_CLOCK_SHADOW": 0, "SHIFTED_RELEASE_PLACEBO": 0,
                 "DELAY_PAIR": 1, "CLAIRVOYANT": 0}


def falsification_eval(anchor_metrics: dict,
                       killer_metrics: dict) -> dict:
    """The D1 falsification rule over the designated-killer battery:
    KILL if ANY designated KILLER earns a strictly greater after-cost
    per-decision edge than the ANCHOR arm; each killer's R2 envelope
    (V8 clause + falsification clause) is reported side by side."""
    per_killer = {role: r2_single(anchor_metrics,
                                  killer_metrics[role])
                  for role in killer_metrics}
    missing = [r for r in KILLER_ROLES if r not in killer_metrics]
    fired = [r for r, v in per_killer.items()
             if v["falsification_clause"]["fires"]]
    return {
        "schema": SCHEMA,
        "rule": "D1 falsification (frozen at S): KILL if ANY designated "
                "KILLER earns a strictly greater after-cost "
                "per-decision edge than the ANCHOR",
        "killer_controls": list(KILLER_ROLES),
        "per_killer": per_killer,
        "falsification_fired_by": fired,
        "kill": bool(fired),
        "coverage_complete": not missing,
        "missing_killers": missing,
    }


def r2_single(anchor_metrics: dict, killer_metrics: dict) -> dict:
    """One killer's R2 verdict (V8 clause OR falsification clause)."""
    from research.assets.commodities_ng1.runners.stage_a import (
        r2_control_kill,
    )
    return r2_control_kill(anchor_metrics, killer_metrics)


def control_verdict_rows(books: dict) -> dict:
    """Per-role control verdict rows for one cell's booked populations
    (``role -> execute.book_ledger`` result).  Z-R1 remediation wiring:
    a DECLARED ``NOT_EXECUTABLE`` book (empty booked population, e.g.
    every trade excluded by the split-boundary law) propagates its
    declared verdict row -- never a crash, never a silent pass; an
    executed book verdicts PASS iff its reconciliation identity holds
    (fail-closed FAIL otherwise)."""
    from research.assets.commodities_ng1.runners.execute import (
        control_verdict_row,
    )
    return {role: control_verdict_row(book)
            for role, book in books.items()}


def q11_eligibility(eligible_per_pair: dict[str, int],
                    pooled: int | None = None) -> dict:
    """Q-11 invalid-null law: fewer eligible instants than the frozen
    minimum (300 per bookable pair; 3300 pooled) is NOT_RUN/INVALID on
    that scope -- never zero, never a pass."""
    if pooled is None:
        pooled = sum(eligible_per_pair.values())
    per_pair = {pid: {
        "eligible_instants": n,
        "minimum": Q11_MIN_ELIGIBLE_PER_PAIR,
        "verdict": "ELIGIBLE" if n >= Q11_MIN_ELIGIBLE_PER_PAIR
        else "NOT_RUN_INVALID",
    } for pid, n in sorted(eligible_per_pair.items())}
    pooled_ok = pooled >= Q11_MIN_ELIGIBLE_POOLED
    return {
        "schema": SCHEMA,
        "per_pair": per_pair,
        "pooled": {
            "eligible_instants": pooled,
            "minimum": Q11_MIN_ELIGIBLE_POOLED,
            "verdict": "ELIGIBLE" if pooled_ok else "NOT_RUN_INVALID",
        },
        "eligible_overall": pooled_ok and all(
            v["verdict"] == "ELIGIBLE" for v in per_pair.values()),
    }
