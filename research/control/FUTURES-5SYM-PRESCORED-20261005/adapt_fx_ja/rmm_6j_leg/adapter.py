"""adapter — 6J RMM Role-B leg, M-COMPRESS (PROPOSED; MACHINERY ONLY — never
self-activated).

Law text: ./FROZEN_RULE_DRAFT.md (PROPOSED — never an approved freeze).
Family: roll-migration-mode conditioning on the 27 measured 6J rolls; +4 IDs
inside option J-C ONLY. Sources: SPEC_6J.md s.5 (chain + cease-guard + 2022-
09-20 law case); CENSUS_5SYM.md RMM dossier (Role-A ledger CLOSED 19/8;
Role-B NEEDS_EVIDENCE); IDENTITY_BUDGET_6J.md s.2 RMM block; GAPS
P5-FXJA-D1/D2 (J-C legality = ceiling + DC s.1.3, never self-ratified).

MACHINERY-ONLY law: this adapter exposes the descriptive machinery (mode
ledger, guard-violation disclosure, event clock, extremal stratum). ANY
Role-B trade intent refuses on P5-FXJA-D2 while the DC s.1.3 boundary ruling
is unsigned — on synthetic fixtures too. Outcome-blind; real data refuses on
P5-FXJA-D1.
"""
from __future__ import annotations

from datetime import datetime

import fx_common as fc

FAMILY = "RMM6J"
SYMBOL = "6J"
K_EXIT_SESSIONS = 5            # time exit = switch+K sessions [PROVISIONAL]
CORE_IDS = fc.rmm6j_ids()      # FB6J1-RMM-MCOMPRESS-{REV,CONT}-{D1,D30M}
CONTROL_IDS: list[str] = []    # C1 block-shuffle layer sits OUTSIDE the +4
DRAFT_IDS = CORE_IDS


class RMM6JAdapter:
    family = FAMILY
    symbol = SYMBOL

    def __init__(self, contract: dict | None = None):
        self.contract = contract or fc.load_fx_contract(SYMBOL)
        self.tick = self.contract["tick_size"]
        self.mult = self.contract["multiplier"]

    # ---------------------------------------------------------------- API
    def apply_exclusions(self, calendar: dict, panel: dict) -> dict:
        """Event-stacking + flagged-stratum law: switch sessions overlapping a
        BoJ/FOMC/ECB/MPC decision window are EXCLUDED; the 2022-09-20 law-case
        day is the flagged extremal stratum, never a base stratum."""
        out = fc.apply_fx_exclusions(calendar, panel, SYMBOL)
        boj = set(calendar.get("boj_mpm_dates", []))
        fomc = set(calendar.get("fomc_statement_days", []))
        for sd in calendar.get("roll_switch_days", []):
            if sd in boj or sd in fomc:
                out.setdefault(sd, []).append("X_EVENT_STACKING_CENTRAL_BANK")
        return {k: sorted(set(v)) for k, v in out.items()}

    def build_observables(self, panel: dict, calendar: dict,
                          roll_rows: list[dict]) -> dict:
        """Role-A construction ledger view (0 IDs): mode classification from
        the injected switch tables, both chain variants, guard-violation
        disclosure, extremal-stratum flagging."""
        fc.require_synthetic(panel, SYMBOL)
        chain = fc.build_roll_chain(roll_rows)
        disclosure = fc.measure_and_disclose_guard_violations(chain)
        cal2 = {**calendar,
                "roll_switch_days": [r["switch_date"] for r in roll_rows]}
        excl = self.apply_exclusions(cal2, panel)
        return {
            "mode_ledger_measured": {"abrupt": 19, "gradual": 8, "total": 27},
            "fixture_chain": chain,
            "guard_disclosure": disclosure,
            "event_clock_law": "switch session t; decided at close t, effective t+1",
            "extremal_stratum_law": fc.fold_floor_check(3),
            "extremal_dates": [SWITCH_LAW_DATE_6J],
            "exclusions": excl,
            "quote_direction": fc.QUOTE_DIRECTION_6J,
        }

    def signal(self, panel: dict, calendar: dict, session_date: str,
               receiving_contract: str,
               asof: str | datetime | None = None) -> dict:
        """Descriptive machinery only: the switch-session signed move on the
        RECEIVING contract (the Role-B event-clock read). This is NOT a trade
        signal — intent refuses on P5-FXJA-D2."""
        fc.require_synthetic(panel, SYMBOL)
        bars = [b for b in fc.session_bars(panel, session_date, upto=asof)
                if b.get("contract") == receiving_contract]
        base = {"family": FAMILY, "session_date": session_date,
                "receiving_contract": receiving_contract,
                "event_clock_law": "decided at close t, effective t+1",
                "quote_direction": fc.QUOTE_DIRECTION_6J,
                "fold_id": fc.fold_for_date(session_date)}
        if not bars:
            return {**base, "knowable": False, "tail": None,
                    "no_trade_reason": "NO_RECEIVING_CONTRACT_BARS_UPTO_ASOF"}
        move = float(bars[-1]["close"]) - float(bars[0]["open"])
        tail = "UP" if move > 0 else ("DN" if move < 0 else None)
        return {**base, "knowable": True, "switch_move": move, "tail": tail,
                "machinery_note": ("descriptive only; Role-B intent requires "
                                   "P5-FXJA-D1 + P5-FXJA-D2"),
                "no_trade_reason": None if tail else "SWITCH_SESSION_FLAT"}

    def order_intent(self, panel: dict, calendar: dict, identity_id: str,
                     session_date: str, *args, **kwargs) -> dict:
        """Role-B legality gate: J-C requires BOTH the owner 6J ceiling
        (P5-FXJA-D1) AND the DC s.1.3 boundary ruling (P5-FXJA-D2). Neither is
        signable by this lane; the builder refuses (`BLOCKED_NO_CEILING` /
        never-self-ratified) — on synthetic fixtures too. MACHINERY-ONLY."""
        fc.require_synthetic(panel, SYMBOL)
        if identity_id not in DRAFT_IDS:
            raise ValueError(f"identity {identity_id!r} is not an RMM-6J draft ID")
        if fc.GUARDS["P5-FXJA-D1"] is None:
            raise fc.RefusedPendingOwnerDecision(
                "P5-FXJA-D1", "J-C (which contains the RMM 6J leg) requires the "
                "owner ceiling signature first (BLOCKED_NO_CEILING)")
        raise fc.RefusedPendingOwnerDecision(
            "P5-FXJA-D2",
            "RMM Role-B 6J leg legality requires the owner DC s.1.3 boundary "
            "ruling (migration-mode microstructure vs roll-timing-as-"
            "construction); never self-ratified — intent machinery is REFUSED "
            "even on synthetic fixtures")


SWITCH_LAW_DATE_6J = "2022-09-20"
