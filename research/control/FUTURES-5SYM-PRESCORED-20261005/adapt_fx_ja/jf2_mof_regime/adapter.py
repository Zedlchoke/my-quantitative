"""adapter — 6J-JF2 MOF INTERVENTION-REGIME CONDITIONING (PROPOSED; MACHINERY ONLY).

Law text: ./FROZEN_RULE_DRAFT.md (PROPOSED — never an approved freeze).
Family: MOF disclosure-lagged regime overlay on the JF1/JF3 hosts; 0 own
signal, 0 own identities outside the 7-per-host conditioned block.
Sources: SPEC_6J.md s.6 (MOF ex-post-only, lag law; DC s.1.4); CENSUS_5SYM.md
JF2 dossier; IDENTITY_BUDGET_6J.md s.2 JF2 block; HYPO_GAPS.md P5-HYPO-OD4.

MACHINERY-ONLY law (wave-3 dispatch): this adapter builds the disclosure-lag
label machinery + host conditioning; the zone-threshold constant is an OWNER
slot (P5-HYPO-OD4) and the block cannot freeze while it is unfixed.
Outcome-blind: synthetic fixtures only; real-data paths refuse on P5-FXJA-D1.
"""
from __future__ import annotations

from datetime import datetime

import fx_common as fc

FAMILY = "JF2"
SYMBOL = "6J"
HOST_FAMILY = "JF1"          # single-host draft (option J-A shape)
K_TRAILING = fc.JF2_K_TRAILING_SESSIONS   # 63 [PROVISIONAL]
CORE_IDS = fc.jf2_core_ids()             # FB6J1-JF2-{DRIFT,REV}-{UP,DN}-REG-S2
CONTROL_IDS = fc.jf_control_ids(FAMILY)  # FB6J1-{PLA,ALW,CLK}-JF2
DRAFT_IDS = CORE_IDS + CONTROL_IDS       # 4 + 3 = 7 per host


def jf2_freeze_check() -> dict:
    """The JF2 block CANNOT freeze while the owner zone-threshold constant
    (P5-HYPO-OD4) is unfixed (GAPS s.(b) carried row; census JF2 s.9)."""
    if fc.GUARDS["P5-HYPO-OD4"] is None:
        raise fc.RefusedPendingOwnerDecision(
            "P5-HYPO-OD4",
            "JF2 zone-threshold constant unfixed -> the block cannot freeze; "
            "this adapter stays MACHINERY-ONLY (labels + host conditioning)")
    return {"frozen_by": fc.GUARDS["P5-HYPO-OD4"]}


class JF2Adapter:
    family = FAMILY
    symbol = SYMBOL

    def __init__(self, host_adapter=None, contract: dict | None = None):
        self.contract = contract or fc.load_fx_contract(SYMBOL)
        if host_adapter is None:
            from jf1_boj_mpm.adapter import JF1Adapter
            host_adapter = JF1Adapter()
        self.host = host_adapter

    # ---------------------------------------------------------------- API
    def apply_exclusions(self, calendar: dict, panel: dict) -> dict:
        return self.host.apply_exclusions(calendar, panel)

    def build_observables(self, panel: dict, calendar: dict) -> dict:
        """Disclosure-lagged regime series over the host sessions (strict PIT:
        only ops with disclosure_date <= asof are ever visible)."""
        fc.require_synthetic(panel, SYMBOL)
        ops = calendar.get("mof_ops", [])
        held = [s["session_date"] for s in panel["sessions"]]
        out = {"lag_law": ("op amounts publish ~1 month (monthly) / quarterly "
                           "(daily detail) after the fact; labels on the "
                           "DISCLOSURE date only; same-day signals FORBIDDEN"),
               "k_trailing_sessions": K_TRAILING, "k_status": "PROVISIONAL",
               "null_era_check": fc.jf2_null_era_check(ops),
               "series": []}
        for s in panel["sessions"]:
            sd = s["session_date"]
            label = fc.mof_regime_label(ops, sd, asof=f"{sd}T23:59:59+00:00",
                                        held_sessions=held, k=K_TRAILING)
            out["series"].append(label)
        return out

    def regime_at(self, calendar: dict, panel: dict, session_date: str,
                  asof: str | datetime) -> dict:
        """PIT regime state at `asof` (disclosure-dated visibility only)."""
        fc.require_synthetic(panel, SYMBOL)
        held = [s["session_date"] for s in panel["sessions"]]
        return fc.mof_regime_label(calendar.get("mof_ops", []), session_date,
                                   asof=asof, held_sessions=held, k=K_TRAILING)

    def signal(self, panel: dict, calendar: dict, session_date: str,
               asof: str | datetime | None = None) -> dict:
        """JF2 has NO signal of its own (census JF2 s.5): the observable is the
        disclosure-lagged regime state; the market read is the host's."""
        fc.require_synthetic(panel, SYMBOL)
        a = asof if asof is not None else fc.session_last_dt(panel, session_date)
        reg = self.regime_at(calendar, panel, session_date, a)
        host_sig = self.host.signal(panel, calendar, session_date, asof)
        return {"family": FAMILY, "session_date": session_date,
                "regime": reg, "host_signal": host_sig,
                "own_signal_law": "NONE (overlay; 0 own identities)",
                "quote_direction": fc.QUOTE_DIRECTION_6J,
                "fold_id": fc.fold_for_date(session_date)}

    def order_intent(self, panel: dict, calendar: dict, identity_id: str,
                     session_date: str, asof: str | datetime | None = None,
                     cost_tier: str = "T1", cost_slip: str = "S1",
                     stress: float = 1.0) -> dict:
        """Regime-conditioned HOST intent. Identity grammar: cores
        FB6J1-JF2-{DRIFT,REV}-{UP,DN}-REG-S2 (the host's 2 arms x 2 tails
        evaluated only in the disclosed-regime state); controls
        FB6J1-{PLA,ALW,CLK}-JF2."""
        fc.require_synthetic(panel, SYMBOL)
        parsed = _parse_identity(identity_id)
        excl = self.apply_exclusions(calendar, panel)
        flags = excl.get(session_date, [])
        head = fc.intent_head(FAMILY, identity_id, session_date, panel, {
            "exclusion_flags": list(flags),
            "tick_size": self.contract["tick_size"],
            "multiplier": self.contract["multiplier"],
            "host_family": HOST_FAMILY,
            "quote_direction": fc.QUOTE_DIRECTION_6J,
        })
        if flags:
            return fc.no_trade(head, "EXCLUDED: " + ",".join(flags))
        a = asof if asof is not None else fc.session_last_dt(panel, session_date)
        reg = self.regime_at(calendar, panel, session_date, a)

        arm = parsed["arm"]
        if arm in ("DRIFT", "REV"):
            # REG core: trade the host arm ONLY in the disclosed-regime state
            if reg["regime_label"] != "REGIME":
                return fc.no_trade(head, "REGIME_CONDITION_NOT_MET")
            host_id = (f"{fc.DRAFT_TOKEN_6J}-{HOST_FAMILY}-{arm}-{parsed['tail']}"
                       f"-{parsed['delay']}-S2")
            out = self.host.order_intent(panel, calendar, host_id, session_date,
                                         asof=asof, cost_tier=cost_tier,
                                         cost_slip=cost_slip, stress=stress)
            out["identity_id"] = identity_id
            out["family"] = FAMILY
            out["regime_context"] = reg
            return out
        if arm == "PLA":
            # C3' disclosure-date label shuffle, single-seed single-shuffle
            shuffled = shuffle_disclosure_labels(calendar.get("mof_ops", []),
                                                 seed=fc.C1_SEED)
            reg_sh = fc.mof_regime_label(shuffled, session_date, asof=a,
                                         held_sessions=_held(panel),
                                         k=K_TRAILING)
            if reg_sh["regime_label"] != "REGIME":
                return fc.no_trade(head, "SHUFFLED_REGIME_CONDITION_NOT_MET")
            host_id = (f"{fc.DRAFT_TOKEN_6J}-{HOST_FAMILY}-DRIFT-UP-D1-S2")
            out = self.host.order_intent(panel, calendar, host_id, session_date,
                                         asof=asof, cost_tier=cost_tier,
                                         cost_slip=cost_slip, stress=stress)
            out["identity_id"] = identity_id
            out["family"] = FAMILY
            out["regime_context"] = {**reg_sh, "shuffled": True, "seed": fc.C1_SEED}
            return out
        if arm == "ALW":
            # C2 host always-on INSIDE the disclosed-regime state
            if reg["regime_label"] != "REGIME":
                return fc.no_trade(head, "REGIME_CONDITION_NOT_MET")
            host_id = f"{fc.DRAFT_TOKEN_6J}-{HOST_FAMILY}-DRIFT-UP-D1-S2"
            out = self.host.order_intent(panel, calendar, host_id, session_date,
                                         asof=asof, cost_tier=cost_tier,
                                         cost_slip=cost_slip, stress=stress)
            out["identity_id"] = identity_id
            out["family"] = FAMILY
            out["regime_context"] = reg
            return out
        # CLK — C3'' pre-2022 null-era clock: the label must read NON_REGIME
        # throughout 2020-01..2022-08; trading there is a construction bug.
        if not fc.jf2_null_era_check(calendar.get("mof_ops", []))["clean"]:
            return fc.no_trade(head, "NULL_ERA_CONTAMINATED")
        if reg["regime_label"] == "REGIME":
            return fc.no_trade(head, "CLK_NULL_ERA_EXPECTS_NON_REGIME")
        return {**head, "no_trade": True,
                "no_trade_reason": "CLK_NEGATIVE_CONTROL_NO_TRADE",
                "regime_context": reg}


def _held(panel: dict) -> list[str]:
    return [s["session_date"] for s in panel["sessions"]]


def shuffle_disclosure_labels(ops: list[dict], seed: int) -> list[dict]:
    """C3' placebo construction (evaluation view): deterministically rotate the
    disclosure dates across ops (single-seed single-shuffle law; >=100-seed
    expansions are separate owner rulings — the placebo slot is EMPTY)."""
    if not ops:
        return []
    n = len(ops)
    dates = [o["disclosure_date"] for o in ops]
    rotated = dates[seed % n:] + dates[:seed % n]
    return [{**o, "disclosure_date": rotated[i]} for i, o in enumerate(ops)]


def _parse_identity(identity_id: str) -> dict:
    parts = identity_id.split("-")
    if len(parts) == 6 and parts[0] == fc.DRAFT_TOKEN_6J and parts[1] == "JF2":
        arm, tail, reg, tier = parts[2], parts[3], parts[4], parts[5]
        if arm not in ("DRIFT", "REV"):
            raise ValueError(f"unknown JF2 arm {arm!r}")
        if tail not in ("UP", "DN"):
            raise ValueError(f"arm {arm} requires tail UP/DN")
        if reg != "REG" or tier != "S2":
            raise ValueError("JF2 cores are REG-conditioned @ S2")
        return {"arm": arm, "tail": tail, "delay": "D1", "tier": tier}
    if len(parts) == 3 and parts[0] == fc.DRAFT_TOKEN_6J and parts[2] == "JF2":
        if parts[1] not in ("PLA", "ALW", "CLK"):
            raise ValueError(f"unknown JF2 control {parts[1]!r}")
        return {"arm": parts[1], "tail": "UP", "delay": "D1", "tier": None}
    raise ValueError(f"identity {identity_id!r} does not match the JF2 draft grammar")
