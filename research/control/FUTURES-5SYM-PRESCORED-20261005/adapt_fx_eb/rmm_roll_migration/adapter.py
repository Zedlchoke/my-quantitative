"""RMM roll-migration adapter — Role-A MACHINERY-ONLY; Role-B owner-gated.

PROPOSED; PB2 HOLD stands. Role-A (construction ledger, 0 identities) is CLOSED
in k6gate (mode ledger 6E 22/5, 6B 23/4 abrupt/gradual — DERIVED from the
committed switch tables). This package implements the ledger helpers and the
switch-session exclusion law; Role-B identity mints REFUSE on P5-FXEB-OD5
(owner DC s.1.3 boundary ruling) with the interaction NOT_RUN recorded. The
mode x post-switch-drift interaction has never been measured — that measurement
IS the family; no Role-B signal exists here.
"""
from __future__ import annotations

import fx_common
from fx_common import PanelError, RefusedPendingOwnerDecision, \
    blocking_flags

FAMILY = "RMM"
# k6gate D-1 mode ledger (CLOSED; fx_ja/rmm_mode_ledger.json, DERIVED — cited):
MODE_LEDGER = {"6E": {"abrupt": 22, "gradual": 5},
               "6B": {"abrupt": 23, "gradual": 4}}
MEASURED_SWITCHES = {"6E": 27, "6B": 27}
ROLE_B_IDS = ("RB1", "RB2", "RB3", "RB4")   # +4/leg, DC s.1.3-gated (FX-C only)


def request_rmm_role_b_identity(sym: str, rb: str) -> None:
    """Any Role-B identity mint refuses while the owner DC s.1.3 ruling is
    unsigned; the interaction measurement is NOT_RUN and PB2 HOLD stands."""
    if sym not in fx_common.SYMBOLS:
        raise ValueError(f"unknown symbol {sym!r}")
    if rb not in ROLE_B_IDS:
        raise ValueError(f"unknown Role-B slot {rb!r} (known: {ROLE_B_IDS})")
    raise RefusedPendingOwnerDecision(
        "P5-FXEB-OD5",
        f"FXRMM-{sym}-{rb}: Role-B legality requires the owner DC s.1.3 "
        f"boundary ruling (HYPOTHESES_R2 s.2/s.9.7 — carried, never "
        f"self-ratified); the mode x post-switch-drift interaction is NOT_RUN "
        f"(that measurement IS the family); PB2 HOLD stands")


def mode_split_count(labels: list[str]) -> dict:
    """Deterministic Role-A ledger count over injected mode labels."""
    return {"abrupt": sum(1 for x in labels if x == "ABRUPT"),
            "gradual": sum(1 for x in labels if x == "GRADUAL"),
            "unknown": sum(1 for x in labels if x not in ("ABRUPT", "GRADUAL"))}


def switch_session_flags(sym: str, calendar: dict, session_date: str) -> list[str]:
    """Switch-session exclusion law: event-stacking + 6B holiday-adjacency +
    D12 quarter posture."""
    cal = calendar or {}
    flags: list[str] = []
    if session_date in set(cal.get("roll_switch_dates", [])):
        f2_days = fx_common.f2_event_day_set(sym, cal)
        if session_date in f2_days:
            flags.append("EVENT_STACKING_EXCLUDED")
        if sym == "6B" and session_date in set(cal.get("holiday_adjacent_6b", [])):
            flags.append("HOLIDAY_ADJACENT_SWITCH_EXCLUDED_6B")
    flags += fx_common.roll_anchor_exclusions(sym, session_date)
    return flags


def build_observables(panel: dict, calendar: dict, sym: str,
                      mode_labels: list[dict]) -> dict:
    fx_common.require_synthetic(panel)
    if sym not in fx_common.SYMBOLS:
        raise ValueError(f"unknown symbol {sym!r}")
    labels = [r["mode"] for r in mode_labels]
    out = {"family": FAMILY, "symbol": sym, "kind": "ROLE_A_CONSTRUCTION_LEDGER",
           "standalone_identities": 0,
           "cited_mode_ledger": MODE_LEDGER[sym],
           "measured_switches": MEASURED_SWITCHES[sym],
           "fixture_mode_split": mode_split_count(labels),
           "switch_flags": {r["date"]: switch_session_flags(sym, calendar,
                                                            r["date"])
                            for r in mode_labels},
           "timing_law": "mode label = strict-past classification decided at "
                         "close t, effective t+1 (DC s.1.3)",
           "role_b_status": "NEEDS_EVIDENCE (interaction NOT_RUN) + P5-FXEB-OD5",
           "provenance": panel["provenance"]}
    return out


def apply_exclusions(panel: dict, calendar: dict, sym: str) -> dict:
    fx_common.require_synthetic(panel)
    out: dict[str, list[str]] = {}
    for s in panel["sessions"]:
        sd = s["session_date"]
        flags = switch_session_flags(sym, calendar, sd)
        if flags:
            out[sd] = flags
    return out


def signal(observables: dict, session_date: str, exclusions: dict, sym: str,
           calendar: dict, panel: dict, **_k) -> dict:
    fx_common.require_synthetic(panel)
    return {"session_date": session_date, "family": FAMILY, "symbol": sym,
            "status": "NO_TRADE",
            "flags": ["ROLE_A_CONSTRUCTION_ONLY"],
            "blocking": ["ROLE_A_CONSTRUCTION_ONLY"],
            "role_b_blockers": ["P5-FXEB-OD5 (DC s.1.3 owner ruling)",
                                "mode x post-switch-drift interaction NOT_RUN",
                                "PB2 HOLD (P5-FXEB-OD1)"],
            "identity_draft_ids": [f"FXRMM-{sym}-RB{k}" for k in (1, 2, 3, 4)],
            "identity_mint": "refuses (request_rmm_role_b_identity raises)",
            "proposed": "PROPOSED — machinery only; not a scored signal",
            "decision_slot_dependencies": fx_common.decision_slot_dependencies()}
