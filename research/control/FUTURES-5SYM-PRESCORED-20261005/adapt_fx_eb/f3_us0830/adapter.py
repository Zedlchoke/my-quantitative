"""FX-F3 US-8:30 Spillover adapter (6E + 6B) — PROPOSED machinery.

Rule text as code: FROZEN_RULE_DRAFT.md in this directory. Anchor 07:30 CT
(08:30 ET) on vintage-correct CPI/EMPSIT-known days; arms SC (continuation) /
SD (fade); conservative next-bar-open fills; BBO NOT_RUN. Pure deterministic
functions; outcome-blind; synthetic fixtures only (require_synthetic gates any
real-data path on P5-FXEB-OD1).
"""
from __future__ import annotations

import fx_common
from fx_common import PanelError, blocking_flags

FAMILY = "FX-F3"
ANCHOR_CT_MIN = 7 * 60 + 30          # 07:30 CT = minute 450 (08:30 ET)
KNOWN_SERIES = ("CPI", "EMPSIT")     # the pooled "US-hard-data 8:30 class" base


def bls_stamp_for(calendar: dict, session_date: str) -> dict | None:
    for row in (calendar or {}).get("bls_vintage", []):
        if row.get("date") == session_date:
            return row
    return None


def build_observables(panel: dict, calendar: dict, sym: str,
                      session_date: str) -> dict:
    fx_common.require_synthetic(panel)
    if sym not in fx_common.SYMBOLS:
        raise ValueError(f"unknown symbol {sym!r}")
    fx_common.validate_panel(panel)
    out = {"session_date": session_date, "symbol": sym, "family": FAMILY,
           "anchor_ct_minute": None, "release_sign": None, "release_move": None,
           "spike_ratio": None, "atr20": None, "flags": []}
    bars = {fx_common.ct_minutes(b["_dt"]): b
            for b in fx_common.session_bars(panel, session_date)}
    if ANCHOR_CT_MIN not in bars or (ANCHOR_CT_MIN - 1) not in bars:
        out["flags"].append("ANCHOR_BAR_ABSENT")
        return out
    out["anchor_ct_minute"] = ANCHOR_CT_MIN
    prev_close = float(bars[ANCHOR_CT_MIN - 1]["close"])
    a_close = float(bars[ANCHOR_CT_MIN]["close"])
    move = round(a_close - prev_close, 10)
    out["release_move"] = move
    out["release_sign"] = "UP" if move > 0 else ("DN" if move < 0 else "FLAT")
    if out["release_sign"] == "FLAT":
        out["flags"].append("TRIGGER_FLAT")
    prior = [float(bars[m]["volume"]) for m in range(ANCHOR_CT_MIN - 6,
                                                     ANCHOR_CT_MIN) if m in bars]
    if prior:
        med = sorted(prior)[len(prior) // 2]
        out["spike_ratio"] = round(float(bars[ANCHOR_CT_MIN]["volume"]) / med, 4) \
            if med else None
    atr = fx_common.atr20_points(panel, session_date)
    out["atr20"] = atr
    if atr is None:
        out["flags"].append("ATR_WARMUP_INSUFFICIENT")
    return out


def event_class(sym: str, calendar: dict, session_date: str) -> dict:
    """Stamp classification: base (CPI/EMPSIT scheduled, vintage-correct) vs the
    negative-control strata vs exclusions. Vintage law enforced: a stamp whose
    vintage_asof postdates the decision date refuses (PIT)."""
    cls: dict = {"strata": [], "blocking": []}
    stamp = bls_stamp_for(calendar, session_date)
    if stamp is None:
        cls["blocking"].append("NO_EVENT_STAMP")
        return cls
    if str(stamp.get("vintage_asof", session_date)) > session_date:
        cls["blocking"].append("PIT_VINTAGE_POSTDATED")
        cls["strata"].append("VINTAGE_POSTDATED")
        return cls
    series = str(stamp.get("series", "")).upper()
    status = str(stamp.get("status", "scheduled"))
    if status == "canceled_expected":
        cls["strata"].append("CANCELED_EXPECTED")
        cls["blocking"].append("CANCELED_NEGATIVE_CONTROL")
        return cls
    if series not in KNOWN_SERIES:
        cls["strata"].append("UNCLASSIFIED_830")
        cls["blocking"].append("UNCLASSIFIED_830_STRATUM")
        return cls
    cls["strata"].append(f"KNOWN_{series}")
    f2_days = fx_common.f2_event_day_set(sym, calendar)
    if session_date in f2_days:
        cls["strata"].append("DOUBLE_EVENT")
        cls["blocking"].append("DOUBLE_EVENT_RECLASS_F2")
    return cls


def apply_exclusions(panel: dict, calendar: dict, sym: str) -> dict:
    """Fail-closed exclusion pass (stamp classes + F2 overlap + holiday/quarter)."""
    fx_common.require_synthetic(panel)
    out: dict[str, list[str]] = {}
    for s in panel["sessions"]:
        sd = s["session_date"]
        cls = event_class(sym, calendar, sd)
        flags = sorted(set(cls["blocking"] +
                           fx_common.holiday_exclusion_flags(sym, calendar, sd) +
                           fx_common.roll_anchor_exclusions(sym, sd)))
        if flags:
            out[sd] = flags
    return out


def signal(observables: dict, session_date: str, exclusions: dict, sym: str,
           calendar: dict, panel: dict,
           delay_slots: tuple[str, ...] = fx_common.DELAY_SLOTS_DRAFT) -> dict:
    fx_common.require_synthetic(panel)
    cls = event_class(sym, calendar, session_date)
    flags = sorted(set(list(exclusions.get(session_date, [])) +
                       fx_common.holiday_exclusion_flags(sym, calendar,
                                                         session_date) +
                       fx_common.roll_anchor_exclusions(sym, session_date) +
                       observables.get("flags", [])))
    blocking = sorted(set(blocking_flags(flags) + cls["blocking"] +
                          [f for f in ("ANCHOR_BAR_ABSENT", "TRIGGER_FLAT",
                                       "ATR_WARMUP_INSUFFICIENT") if f in flags]))
    base = {"session_date": session_date, "family": FAMILY, "symbol": sym,
            "strata": cls["strata"],
            "identity_draft_ids": fx_common.core_ids(FAMILY, sym, delay_slots)
                                  + fx_common.control_ids(FAMILY, sym),
            "decision_slot_dependencies": fx_common.decision_slot_dependencies(),
            "proposed": "PROPOSED — conditional on PB2 lift; not a scored signal"}
    if blocking:
        base.update({"status": "NO_TRADE", "flags": flags, "blocking": blocking})
        return base
    return {**base, "status": "TRIGGERED", "tail": observables["release_sign"],
            "arms": ["SC", "SD"], "delay_slots": list(delay_slots),
            "anchor_ct_minute": observables["anchor_ct_minute"],
            "release_move": observables["release_move"],
            "spike_ratio": observables["spike_ratio"],
            "atr20": observables["atr20"], "flags": flags}


def order_intent(panel: dict, observables: dict, sig: dict, identity_id: str,
                 sym: str, delay_slot: str = "D0",
                 resolve_exit: bool = True) -> dict:
    """D0 = open of the 07:31 CT bar; D1B = 07:32; D30M = 08:01. Exit per
    family law (fx_common.exit_walk). Journal-payload row."""
    fx_common.require_synthetic(panel)
    session_date = sig["session_date"]
    if sig["status"] != "TRIGGERED":
        return {"identity_id": identity_id, "status": "NO_TRADE",
                "flags": sig["flags"], "session_date": session_date}
    if identity_id not in sig["identity_draft_ids"]:
        raise PanelError(f"identity {identity_id!r} not in the DRAFT enumeration")
    fill_min = ANCHOR_CT_MIN + 1 + {"D0": 0, "D1B": 1, "D30M": 30}[delay_slot]
    bars = {fx_common.ct_minutes(b["_dt"]): b
            for b in fx_common.session_bars(panel, session_date)}
    if fill_min not in bars:
        return {"identity_id": identity_id, "status": "NO_TRADE",
                "flags": ["FILL_BAR_ABSENT"], "session_date": session_date}
    fill = bars[fill_min]
    entry = float(fill["open"])
    arm = identity_id.split("-")[2]
    direction = 1 if (arm == "SC") == (sig["tail"] == "UP") else -1
    atr = float(sig["atr20"])
    sl = fx_common.round_to_tick(entry - direction * atr, sym)
    tp = fx_common.round_to_tick(entry + direction * 2.0 * atr, sym)
    if resolve_exit:
        exit_px, exit_rule = fx_common.exit_walk(panel, session_date,
                                                 fill["ts"], sl, tp, direction)
    else:
        exit_px, exit_rule = None, "NOT_RESOLVED_AT_DECISION_INSTANT"
    return {
        "identity_id": identity_id, "session_date": session_date,
        "family": FAMILY, "symbol": sym, "arm": arm, "tail": sig["tail"],
        "delay_slot": delay_slot, "tier": "S2", "strata": sig["strata"],
        "status": "ORDER_INTENT", "side": "BUY" if direction == 1 else "SELL",
        "entry_ts_intent": fill["ts"], "entry_px_intent": entry,
        "fill_law": "CONSERVATIVE_NEXT_BAR_OPEN; BBO NOT_RUN (D5; P5-FXEB-OD8); "
                    "publish-latency NOT_RUN declared",
        "sl_level": sl, "tp_level": tp, "same_bar_priority": "SL",
        "exit_px_model": exit_px, "exit_rule": exit_rule,
        "horizon": "intraday_same_session; mandatory flat 16:00 CT",
        "cost_model": fx_common.cost_ladder_usd(sym, "S2", 1.0),
        "cost_gate_consumable": False,
        "k_views": {"K5_era": "2020-22" if int(session_date[:4]) <= 2022
                    else "2023-26",
                    "K_BLS_vintage_regime_2025": session_date[:4] == "2025"},
        "provenance": panel["provenance"], "pit_asof": fill["ts"],
        "proposed": "PROPOSED — conditional on PB2 lift; no order transmission",
        "decision_slot_dependencies": fx_common.decision_slot_dependencies(),
    }
