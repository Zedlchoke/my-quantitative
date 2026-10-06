"""adapter — NQ-F4 ROLLWK Role-B (PROPOSED; MACHINERY-ONLY, synthetic-only).

Law text: ./FROZEN_RULE_DRAFT.md (PROPOSED — never an approved freeze).

Delivers:
  - Role-A roll-construction machinery: k=5 trailing-mean volume-crossover
    switch detection (decided t-1, held from t) + the NEW-4 standing audit
    (spread adjustment present, dte in [0,45], cease-guard violations = 0).
    A Role-A failure kills the RUN, never the hypothesis (0 identities).
  - Roll-week membership + event-stacking observables.
  - A HARD Role-B gate: every order_intent raises
    RoleBInteractionGateNotFormed (ROLE_B_INTERACTION_GATE_NOT_EVIDENCED) —
    the roll-week x session-type interaction is NEEDS_EVIDENCE (the family's
    K6 gate); no Role-B signal exists lawfully.

Pure, deterministic, synthetic-only (P5-NQ1 provenance gate).
"""
from __future__ import annotations

import nq_common as nc

FAMILY = "NQ-F4"
K_WINDOW = 5                     # k=5 crossover window (chain law; NOT tunable here)
DTE_MIN, DTE_MAX = 0, 45
CORE_IDS = nc.core_ids(FAMILY)
CONTROL_IDS = nc.control_ids(FAMILY)
DRAFT_IDS = CORE_IDS + CONTROL_IDS


class RoleBInteractionGateNotFormed(Exception):
    """The Role-B interaction gate is NEEDS_EVIDENCE: no Role-B signal exists."""

    code = "ROLE_B_INTERACTION_GATE_NOT_EVIDENCED"

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__("Role-B interaction gate NEEDS_EVIDENCE — no signal exists"
                         + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "detail": self.detail,
                "family_gate": "NQ-F4 K6 interaction measurement (scored-side NOT_RUN)",
                "note": "machinery-only lane deliverable; owner evidence, not a "
                        "lane parameter, would ever form Role-B"}


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


class RollWkAdapter:
    family = FAMILY

    def __init__(self, contract: dict | None = None):
        self.contract = contract or nc.load_nq_contract()
        self.tick = self.contract["tick_size"]
        self.mult = self.contract["multiplier"]

    # ---------------------------------------------------------------- API
    def apply_exclusions(self, calendar: dict, panel: dict) -> dict:
        return nc.apply_exclusions_with_panel(calendar, panel, include_fomc=True)

    def build_observables(self, panel: dict, calendar: dict) -> dict:
        nc.require_synthetic(panel)
        nc.validate_panel(panel)
        rolls = self.roll_calendar(panel)
        membership = self.roll_week_membership(panel)
        excl = self.apply_exclusions(calendar, panel)
        stacking = {}
        # EVENT_STACKING law (census F4 s.6): roll-WEEK sessions overlapping
        # scheduled events are flagged; any future Role-B conditioning excludes them
        for sd in sorted(membership):
            flags = list(excl.get(sd, []))
            if flags:
                stacking[sd] = flags
        return {
            "rolls": rolls,
            "roll_week_membership": sorted(membership),
            "event_stacking_flags": stacking,
            "role_b_gate": "NEEDS_EVIDENCE (roll-week x session-type interaction "
                           "never measured — it IS the family K6 gate)",
            "new4_audit_note": "Role-A audit binds EVERY NQ run (see role_a_audit)",
        }

    # ------------------------------------------------------- Role-A machinery
    def roll_calendar(self, panel: dict) -> list[dict]:
        """k=5 trailing-MEAN volume crossover; decided from sessions [t-k, t-1],
        held from t (PIT: never reads session t's own volume for the decision)."""
        sessions = sorted(panel["sessions"], key=lambda s: s["session_date"])
        cands = self._candidate_contracts(panel)
        if len(cands) != 2:
            return []
        old, new = sorted(cands)
        held = panel.get("held_contract", old)
        rolls: list[dict] = []
        for i, s in enumerate(sessions):
            if i >= K_WINDOW:
                w = sessions[i - K_WINDOW:i]          # [t-k, t-1] inclusive
                m_old = _mean([float(x["cand_volumes"][old]) for x in w])
                m_new = _mean([float(x["cand_volumes"][new]) for x in w])
                cand = new if m_new > m_old else old   # tie -> hold incumbent
            else:
                cand = held
            if cand != held:
                rolls.append({
                    "switch_date": s["session_date"], "from_contract": held,
                    "to_contract": cand, "k": K_WINDOW,
                    "decided_from_data_through": sessions[i - 1]["session_date"],
                    "dte": self._dte(panel, s["session_date"]),
                    "spread_adjustment_factor":
                        nc.session_map(panel).get(s["session_date"], {})
                        .get("spread_adjustment_factor"),
                })
                held = cand
        return rolls

    def role_a_audit(self, panel: dict) -> dict:
        """NEW-4 standing law: construction audit binding on EVERY NQ run.
        pass=False is a RUN-killer (never a hypothesis-killer)."""
        rolls = self.roll_calendar(panel)
        failures: list[dict] = []
        sm = nc.session_map(panel)
        for r in rolls:
            sw = r["switch_date"]
            factor = (sm.get(sw, {}) or {}).get("spread_adjustment_factor")
            if factor is None:
                failures.append({"switch_date": sw,
                                 "code": "MISSING_SPREAD_ADJUSTMENT",
                                 "law": "corr-0.999 phantom-drift law requires "
                                        "spread-adjusted switch-day returns"})
            dte = r.get("dte")
            if dte is None or not (DTE_MIN <= dte <= DTE_MAX):
                failures.append({"switch_date": sw, "code": "DTE_OUT_OF_RANGE",
                                 "dte": dte})
        cg = panel.get("cease_guard_violations")
        if cg is not None and cg > 0:
            failures.append({"code": "CEASE_GUARD_VIOLATION", "count": cg})
        return {
            "pass": not failures, "failures": failures,
            "n_rolls": len(rolls),
            "binding": "NEW-4 standing law: a Role-A construction failure kills "
                       "the RUN, never the hypothesis (SPEC_NQ.md s.7)",
        }

    def roll_week_membership(self, panel: dict) -> set[str]:
        """The k=5 crossover window: the K_WINDOW held sessions ending at each
        switch date (machinery for any future Role-B conditioning)."""
        dates = sorted(s["session_date"] for s in panel["sessions"])
        out: set[str] = set()
        for r in self.roll_calendar(panel):
            sw = dates.index(r["switch_date"])
            out.update(dates[max(0, sw - K_WINDOW + 1): sw + 1])
        return out

    # ------------------------------------------------------------ hard gate
    def signal(self, panel: dict, calendar: dict, session_date: str,
               asof=None) -> dict:
        """Roll-state observables only — never a Role-B signal."""
        nc.require_synthetic(panel)
        rolls = self.roll_calendar(panel)
        in_week = session_date in self.roll_week_membership(panel)
        return {"family": FAMILY, "session_date": session_date,
                "in_roll_week": in_week,
                "switch_dates": [r["switch_date"] for r in rolls],
                "role_b_signal": None,
                "gate": "ROLE_B_INTERACTION_GATE_NOT_EVIDENCED"}

    def order_intent(self, panel: dict, calendar: dict, identity_id: str,
                     session_date: str, asof=None, **_kw) -> dict:
        """HARD GATE: every Role-B intent request refuses — machinery-only."""
        nc.require_synthetic(panel)
        _parse_identity(identity_id)  # grammar check only
        raise RoleBInteractionGateNotFormed(
            f"identity {identity_id!r}: the roll-week x session-type interaction "
            f"has never been measured (family K6 gate NEEDS_EVIDENCE)")

    # ------------------------------------------------------------ internals
    def _candidate_contracts(self, panel: dict) -> set[str]:
        cands: set[str] = set()
        for s in panel["sessions"]:
            cands.update((s.get("cand_volumes") or {}).keys())
        return cands

    def _dte(self, panel: dict, switch_date: str) -> int | None:
        exp = panel.get("expiry_date")
        if not exp:
            return None
        return (nc._as_date(exp) - nc._as_date(switch_date)).days


def _parse_identity(identity_id: str) -> dict:
    parts = identity_id.split("-")
    if len(parts) not in (3, 5, 6) or parts[0] != nc.DRAFT_TOKEN or parts[1] != "F4":
        raise ValueError(f"identity {identity_id!r} does not match the F4 draft grammar")
    if len(parts) == 6:
        arm, tail = parts[2], parts[3]
        if arm not in ("CONT", "REV") or tail not in ("UP", "DN"):
            raise ValueError("core grammar requires CONT/REV x UP/DN")
    elif len(parts) == 5:
        if parts[2] not in ("SHDW", "ALW"):
            raise ValueError("control grammar requires SHDW/ALW")
    else:
        if parts[2] != "FLAT":
            raise ValueError("3-part grammar is FLAT-only")
    return {"identity_id": identity_id}
