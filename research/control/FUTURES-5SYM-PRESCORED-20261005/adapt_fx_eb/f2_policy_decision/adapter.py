"""FX-F2 Policy-Decision Resolution adapter (6E FOMC leg / 6B MPC leg).

PROPOSED machinery — see FROZEN_RULE_DRAFT.md. Pure deterministic functions;
outcome-blind; synthetic fixtures only. The two legs are ONE family with
mutually exclusive day-sets: the 6E anchor is 13:00 CT (minute 780, FOMC); the
6B anchor is 12:00 Europe/London (minute 720, MPC) resolved via zoneinfo per
session date — never a hardcoded CT clock (DST-mismatch CT shift is the
K4-analog clock law; a CT-anchored MPC implementation is a bug class, tested).
"""
from __future__ import annotations

from datetime import datetime

import fx_common
from fx_common import LONDON, PanelError, blocking_flags

FAMILY = "FX-F2"
FOMC_ANCHOR_CT_MIN = 13 * 60          # 13:00 CT = minute 780 (SPEC_6E s.5)
MPC_ANCHOR_LON_MIN = 12 * 60          # 12:00 London = minute 720 (SPEC_6B s.5)
WINDOW_MIN = 5                        # first-5m window after the anchor
FILL_OFFSET = 6                       # T+60s law: D0 = open of anchor+6 bar


def _lon_wall(dt: datetime) -> int:
    loc = dt.astimezone(LONDON)
    return loc.hour * 60 + loc.minute


def mpc_stamp_for(calendar: dict, session_date: str) -> dict | None:
    for row in (calendar or {}).get("mpc_dates", []):
        if (row["date"] if isinstance(row, dict) else row) == session_date:
            return row if isinstance(row, dict) else {"date": row}
    return None


def fomc_stamp_for(calendar: dict, session_date: str) -> dict | None:
    for row in (calendar or {}).get("fomc_statements", calendar.get("fomc_dates", [])):
        if (row["date"] if isinstance(row, dict) else row) == session_date:
            return row if isinstance(row, dict) else {"date": row}
    return None


def ecb_stamp_for(calendar: dict, session_date: str) -> dict | None:
    for row in (calendar or {}).get("ecb_dates", []):
        if (row["date"] if isinstance(row, dict) else row) == session_date:
            return row if isinstance(row, dict) else {"date": row}
    return None


def anchor_ct_minute(panel: dict, sym: str, session_date: str) -> int | None:
    """Resolve the anchor bar in CT minutes. 6E: fixed 13:00 CT. 6B: the bar
    whose LONDON wall time is 12:00 (zoneinfo; CT time varies by DST)."""
    bars = fx_common.session_bars(panel, session_date)
    if sym == "6E":
        return FOMC_ANCHOR_CT_MIN if any(
            fx_common.ct_minutes(b["_dt"]) == FOMC_ANCHOR_CT_MIN for b in bars) else None
    for b in bars:
        if _lon_wall(b["_dt"]) == MPC_ANCHOR_LON_MIN:
            return fx_common.ct_minutes(b["_dt"])
    return None


def build_observables(panel: dict, calendar: dict, sym: str,
                      session_date: str) -> dict:
    fx_common.require_synthetic(panel)
    if sym not in fx_common.SYMBOLS:
        raise ValueError(f"unknown symbol {sym!r}")
    fx_common.validate_panel(panel)
    anchor_min = anchor_ct_minute(panel, sym, session_date)
    out = {"session_date": session_date, "symbol": sym, "family": FAMILY,
           "anchor_ct_minute": anchor_min, "window_sign": None,
           "window_move": None, "spike_ratio": None, "atr20": None,
           "flags": []}
    if anchor_min is None:
        out["flags"].append("ANCHOR_BAR_ABSENT")
        return out
    bars = {fx_common.ct_minutes(b["_dt"]): b
            for b in fx_common.session_bars(panel, session_date)}
    anchor = bars[anchor_min]
    window = [bars.get(anchor_min + i) for i in range(1, WINDOW_MIN + 1)]
    if any(w is None for w in window):
        out["flags"].append("WINDOW_INCOMPLETE")
        return out
    a_close = float(anchor["close"])
    w_close = float(window[-1]["close"])
    move = round(w_close - a_close, 10)
    out["window_move"] = move
    out["window_sign"] = "UP" if move > 0 else ("DN" if move < 0 else "FLAT")
    if out["window_sign"] == "FLAT":
        out["flags"].append("TRIGGER_FLAT")
    prior = [float(bars[m]["volume"]) for m in range(anchor_min - 6, anchor_min)
             if m in bars]
    if prior:
        med = sorted(prior)[len(prior) // 2]
        out["spike_ratio"] = round(float(anchor["volume"]) / med, 4) if med else None
    out["anchor_close"] = a_close
    out["window_close"] = w_close
    out["anchor_volume"] = float(anchor["volume"])
    atr = fx_common.atr20_points(panel, session_date)
    out["atr20"] = atr
    if atr is None:
        out["flags"].append("ATR_WARMUP_INSUFFICIENT")
    return out


def event_class(sym: str, calendar: dict, session_date: str) -> dict:
    """Stamp classification for the session (base / stratum / exclusion)."""
    fomc = fomc_stamp_for(calendar, session_date)
    mpc = mpc_stamp_for(calendar, session_date)
    ecb = ecb_stamp_for(calendar, session_date)
    cls: dict = {"strata": [], "blocking": []}
    if sym == "6E":
        if fomc is None:
            cls["blocking"].append("NOT_AN_EVENT_DAY")
        elif str(fomc.get("time_ct", "13:00")) != "13:00":
            cls["strata"].append("EMERGENCY_TIMING")
            cls["blocking"].append("EMERGENCY_TIMING")
        else:
            cls["strata"].append("FOMC_DECISION_1300CT")
        if ecb is not None:
            cls["strata"].append("ECB_STRATUM")
            cls["blocking"].append("ECB_STRATUM_NO_BASE_TRADE")
    else:  # 6B
        if mpc is not None:
            kind = str(mpc.get("kind", "hold"))
            cls["strata"].append("MPC_CHANGE" if kind == "change" else "MPC_HOLD")
        if fomc is not None and mpc is not None:
            cls["strata"].append("DOUBLE_EVENT")
            cls["blocking"].append("DOUBLE_EVENT_EXCLUDED")
        elif fomc is not None:
            cls["strata"].append("FOMC_STRATUM")
            cls["blocking"].append("FOMC_STRATUM_NO_BASE_TRADE")
        elif mpc is None:
            cls["blocking"].append("NOT_AN_EVENT_DAY")
    return cls


def apply_exclusions(panel: dict, calendar: dict, sym: str) -> dict:
    """Fail-closed exclusion pass (event classes + holiday/quarter posture)."""
    fx_common.require_synthetic(panel)
    out = fx_common.apply_exclusions(sym, calendar, panel, family="__none__")
    for s in panel["sessions"]:
        cls = event_class(sym, calendar, s["session_date"])
        flags = cls["blocking"] + fx_common.holiday_exclusion_flags(
            sym, calendar, s["session_date"]) + \
            fx_common.roll_anchor_exclusions(sym, s["session_date"])
        if flags:
            out.setdefault(s["session_date"], [])
            out[s["session_date"]] = sorted(set(out[s["session_date"]] + flags))
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
                          [f for f in ("ANCHOR_BAR_ABSENT", "WINDOW_INCOMPLETE",
                                       "TRIGGER_FLAT", "ATR_WARMUP_INSUFFICIENT")
                           if f in flags]))
    base = {"session_date": session_date, "family": FAMILY, "symbol": sym,
            "strata": cls["strata"],
            "identity_draft_ids": fx_common.core_ids(FAMILY, sym, delay_slots)
                                  + fx_common.control_ids(FAMILY, sym),
            "decision_slot_dependencies": fx_common.decision_slot_dependencies(),
            "proposed": "PROPOSED — conditional on PB2 lift; not a scored signal"}
    if blocking:
        base.update({"status": "NO_TRADE", "flags": flags, "blocking": blocking})
        return base
    return {**base, "status": "TRIGGERED", "tail": observables["window_sign"],
            "arms": ["RC", "RD"], "delay_slots": list(delay_slots),
            "anchor_ct_minute": observables["anchor_ct_minute"],
            "window_move": observables["window_move"],
            "spike_ratio": observables["spike_ratio"],
            "atr20": observables["atr20"], "flags": flags}


def order_intent(panel: dict, observables: dict, sig: dict, identity_id: str,
                 sym: str, delay_slot: str = "D0",
                 resolve_exit: bool = True) -> dict:
    """D0 = open of anchor+6 (T+60s law); D1B = anchor+7; D30M = anchor+36.
    Exit per family law (fx_common.exit_walk). Journal-payload row."""
    fx_common.require_synthetic(panel)
    session_date = sig["session_date"]
    if sig["status"] != "TRIGGERED":
        return {"identity_id": identity_id, "status": "NO_TRADE",
                "flags": sig["flags"], "session_date": session_date}
    if identity_id not in sig["identity_draft_ids"]:
        raise PanelError(f"identity {identity_id!r} not in the DRAFT enumeration")
    anchor_min = observables["anchor_ct_minute"]
    fill_min = anchor_min + FILL_OFFSET + \
        {"D0": 0, "D1B": 1, "D30M": 30}[delay_slot]
    bars = {fx_common.ct_minutes(b["_dt"]): b
            for b in fx_common.session_bars(panel, session_date)}
    if fill_min not in bars:
        return {"identity_id": identity_id, "status": "NO_TRADE",
                "flags": ["FILL_BAR_ABSENT"], "session_date": session_date}
    fill = bars[fill_min]
    entry = float(fill["open"])
    arm = identity_id.split("-")[2]
    direction = 1 if (arm == "RC") == (sig["tail"] == "UP") else -1
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
        "fill_law": "CONSERVATIVE_NEXT_BAR_OPEN; >=1min post-release (T+60s); "
                    "BBO NOT_RUN (D5; P5-FXEB-OD8)",
        "sl_level": sl, "tp_level": tp, "same_bar_priority": "SL",
        "exit_px_model": exit_px, "exit_rule": exit_rule,
        "horizon": "intraday_same_session; mandatory flat 16:00 CT",
        "cost_model": fx_common.cost_ladder_usd(sym, "S2", 1.0),
        "cost_gate_consumable": False,
        "k_views": {"K5_era": "2020-22" if int(session_date[:4]) <= 2022
                    else "2023-26",
                    "K_DST_mismatch_6B_minute720": sym == "6B"},
        "provenance": panel["provenance"], "pit_asof": fill["ts"],
        "proposed": "PROPOSED — conditional on PB2 lift; no order transmission",
        "decision_slot_dependencies": fx_common.decision_slot_dependencies(),
    }
