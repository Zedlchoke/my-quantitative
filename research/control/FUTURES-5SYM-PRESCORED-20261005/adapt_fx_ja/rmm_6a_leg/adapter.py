"""adapter — 6A RMM Role-B leg, M-COMPRESS (PROPOSED; CONTINGENCY-PB3-PARK
machinery; never activated).

Law text: ./FROZEN_RULE_DRAFT.md. Sources: SPEC_6A_CONTINGENCY s.3 (measured
chain 27 rolls; baseline k=5 with 2 cease-guard violations => explicit
cease-guard variant MANDATORY, law-pending ADOPT-D9; K6(c) roll-rule timing
materiality); CENSUS RMM dossier + RMM-6A leg bindings (mode split MEASURED
21/6; era tick caveat pre-2020-11-23 descriptive only); frozen 26-ID table
(RMM_6A_contingency = 4).

Outcome-blind: synthetic fixtures only. ANY Role-B intent refuses on the
P5-FXJA-D5 chain FIRST (PB3 PARK), then P5-FXJA-D2 (DC s.1.3, never
self-ratified). Era-1 switch sessions are descriptive-only (era tick caveat).
"""
from __future__ import annotations

import fx_common as fc

FAMILY = "RMM6A"
SYMBOL = "6A"
CORE_IDS = fc.contingency_6a_ids("RMM6A")
CONTROL_IDS: list[str] = []
DRAFT_IDS = CORE_IDS              # 4 contingency shapes; C1 layer sits OUTSIDE
MEASURED = {"rolls": 27, "abrupt_explicit": 21, "gradual_explicit": 6,
            "baseline_violations": 2}
EXTREMAL_ABRUPT_DATES = ["2022-09-20", "2024-12-17", "2026-06-16"]


def rmm6a_freeze_check() -> dict:
    if fc.GUARDS["P5-FXJA-D5"] is None:
        raise fc.RefusedPendingOwnerDecision(
            "P5-FXJA-D5",
            "RMM-6A is a contingency-only census line (4 IDs, all zero until "
            "PB3 lift + D8 + D9 + DC s.1.3); the leg can never activate while "
            "6A is PB3 PARK")
    return {"frozen_by": fc.GUARDS["P5-FXJA-D5"]}


class RMM6AAdapter:
    family = FAMILY
    symbol = SYMBOL

    def __init__(self, contract: dict | None = None):
        self.contract = contract or fc.load_fx_contract(SYMBOL)

    def build_observables(self, roll_rows: list[dict]) -> dict:
        """Role-A machinery: both chain variants + the MANDATORY explicit-guard
        disclosure (2 measured baseline violations) + era tick caveat."""
        chain = fc.build_roll_chain(roll_rows)
        disclosure = fc.measure_and_disclose_guard_violations(chain)
        for r in chain["baseline_k5"] + chain["explicit_cease_guard"]:
            r["era"] = fc.sixa_era_for_date(r["switch_date"])
            r["era_law"] = ("descriptive-only (era-1 tick caveat, $10.00/tick; "
                            "no-back-cast)" if r["era"] == "era1" else "era2")
        return {
            "measured_chain_of_record": MEASURED,
            "fixture_chain": chain,
            "guard_disclosure": disclosure,
            "extremal_abrupt_stratum": {
                "dates": EXTREMAL_ABRUPT_DATES,
                "fold_floor": fc.fold_floor_check(3, 4),
                "law": "extremal abrupt stratum descriptive-only, n=3 fails any "
                       "fold floor (pre-declared)"},
            "roll_rule_timing_materiality": (
                "K6(c): declared calendar-rule rolls land ~9-15d (median 11) "
                "before the k=5 crossover dates — roll-rule choice is material "
                "to timing, disclosed, never silently normalized"),
            "timing_law": "decided at close t, effective t+1",
        }

    def order_intent(self, panel: dict | None, calendar: dict | None,
                     identity_id: str, *args, **kwargs) -> dict:
        """Refusal chain: P5-FXJA-D5 (PB3 PARK) FIRST, then P5-FXJA-D2 (DC
        s.1.3) — including on synthetic fixtures. Era-1 sessions additionally
        raise the era refusal."""
        if identity_id not in DRAFT_IDS:
            raise ValueError(f"identity {identity_id!r} is not an RMM-6A "
                             f"contingency draft ID")
        if fc.sixa_era_for_date(str(kwargs.get("session_date", "2024-06-17"))) == "era1":
            raise fc.RefusedEra1NoTradeIntent(
                "era-1 switch sessions are descriptive-only (era tick caveat)")
        if fc.GUARDS["P5-FXJA-D5"] is None:
            raise fc.RefusedPendingOwnerDecision(
                "P5-FXJA-D5",
                "PB3 PARK: RMM-6A is contingency-only (4 IDs, all zero); "
                "activation = PB3 lift -> D8 -> D9 -> D2 -> calendar "
                "(BLOCKED_PB3_PARK / BLOCKED_D8_UNRATIFIED)")
        raise fc.RefusedPendingOwnerDecision(
            "P5-FXJA-D2",
            "RMM Role-B legality requires the owner DC s.1.3 boundary ruling; "
            "never self-ratified")
