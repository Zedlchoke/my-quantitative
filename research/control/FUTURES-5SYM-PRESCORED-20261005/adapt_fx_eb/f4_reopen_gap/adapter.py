"""FX-F4 Globex Reopen Gap adapter (6E + 6B) — PROPOSED machinery, M2c dual-window.

Rule text as code: FROZEN_RULE_DRAFT.md in this directory. The M2c erratum is
implemented structurally: WINDOW_A (17:00-CT reopen) is PRIMARY and the only
signal source; WINDOW_B (08:30-CT RTH open) is the ERRATUM BASELINE, computed
for audit and never traded. The minimum-gap threshold is a registered-cycle
decision (NOT_RUN) — the adapter refuses to fire without an explicit one.
Pure deterministic functions; outcome-blind; synthetic fixtures only.
"""
from __future__ import annotations

import fx_common
from fx_common import PanelError, blocking_flags

FAMILY = "FX-F4"
REOPEN_CT_MIN = 17 * 60              # 17:00 CT session open (auction minute)
RTH_OPEN_CT_MIN = 8 * 60 + 30        # 08:30 CT (WINDOW_B erratum-baseline print)
FILL_CT_MIN = 17 * 60 + 5            # T+5m law; the 17:00 auction minute excluded
EXIT_0900_CT_MIN = 9 * 60            # time exit [PROVISIONAL]


def _prior_session_close(panel: dict, session_date: str) -> float | None:
    dates = sorted(s["session_date"] for s in panel["sessions"])
    prior = [d for d in dates if d < session_date]
    if not prior:
        return None
    sm = fx_common.session_map(panel)
    return float(sm[prior[-1]]["close"])


def _bar_at(panel: dict, session_date: str, ct_min: int) -> dict | None:
    for b in fx_common.session_bars(panel, session_date):
        if fx_common.ct_minutes(b["_dt"]) == ct_min:
            return b
    return None


def opens_on_sunday(panel: dict, session_date: str) -> bool:
    """The session-opening bar's CT weekday: 6 = Sunday (Globex Sunday-evening
    open; the session_date itself is the following Monday)."""
    bars = fx_common.session_bars(panel, session_date)
    if not bars:
        return False
    return bars[0]["_dt"].weekday() == 6


def build_observables(panel: dict, calendar: dict, sym: str,
                      session_date: str) -> dict:
    fx_common.require_synthetic(panel)
    if sym not in fx_common.SYMBOLS:
        raise ValueError(f"unknown symbol {sym!r}")
    fx_common.validate_panel(panel)
    out = {"session_date": session_date, "symbol": sym, "family": FAMILY,
           "window_a_reopen_1700": None, "window_b_rth_open_0830": None,
           "gap_a": None, "gap_b": None, "gap_ratio_b_over_a": None,
           "atr20": None, "flags": [],
           "m2c_labels": {
               "WINDOW_A_REOPEN_1700_PRIMARY":
                   "primary signal source (true reopen window)",
               "WINDOW_B_RTH_OPEN_0830_ERRATUM_BASELINE":
                   "erratum baseline (family-doc 0.3778% was THIS window); "
                   "measurement only — never a signal source"}}
    prior_close = _prior_session_close(panel, session_date)
    if prior_close is None:
        out["flags"].append("PRIOR_SESSION_CLOSE_ABSENT")
    reopen = _bar_at(panel, session_date, REOPEN_CT_MIN)
    rth = _bar_at(panel, session_date, RTH_OPEN_CT_MIN)
    if reopen is None:
        out["flags"].append("ANCHOR_BAR_ABSENT")
    if prior_close is not None and reopen is not None:
        out["window_a_reopen_1700"] = float(reopen["open"])
        out["gap_a"] = round(float(reopen["open"]) - prior_close, 10)
    if prior_close is not None and rth is not None:
        out["window_b_rth_open_0830"] = float(rth["open"])
        out["gap_b"] = round(float(rth["open"]) - prior_close, 10)
    if out["gap_a"] not in (None, 0.0) and out["gap_b"] is not None:
        out["gap_ratio_b_over_a"] = round(abs(out["gap_b"]) / abs(out["gap_a"]), 4)
    atr = fx_common.atr20_points(panel, session_date)
    out["atr20"] = atr
    if atr is None:
        out["flags"].append("ATR_WARMUP_INSUFFICIENT")
    if opens_on_sunday(panel, session_date):
        out["flags"].append("SUNDAY_REOPEN_STRATUM")   # separate stratum, not base
    return out


def apply_exclusions(panel: dict, calendar: dict, sym: str) -> dict:
    """Roll/after-roll + holiday/quarter posture (SUNDAY_REOPEN_STRATUM is a
    stratum flag computed in build_observables, not a calendar exclusion)."""
    fx_common.require_synthetic(panel)
    return fx_common.apply_exclusions(sym, calendar, panel, family=FAMILY)


def signal(observables: dict, session_date: str, exclusions: dict, sym: str,
           calendar: dict, panel: dict, min_gap_threshold: float | None,
           delay_slots: tuple[str, ...] = fx_common.DELAY_SLOTS_DRAFT) -> dict:
    fx_common.require_synthetic(panel)
    ident = {"identity_draft_ids": fx_common.core_ids(FAMILY, sym, delay_slots)
             + fx_common.control_ids(FAMILY, sym),
             "decision_slot_dependencies":
                 fx_common.decision_slot_dependencies()}
    if min_gap_threshold is None:
        return {"session_date": session_date, "family": FAMILY, "symbol": sym,
                "status": "NO_TRADE",
                "blocking": ["THRESHOLD_NOT_REGISTERED"],
                "flags": ["THRESHOLD_NOT_REGISTERED"],
                "not_run_grounds": "minimum-gap threshold = registered-cycle "
                                   "decision, never tuned in PREP (SPEC NOT_RUN "
                                   "item 9)",
                "proposed": "PROPOSED — conditional on PB2 lift; not a scored "
                            "signal", **ident}
    flags = sorted(set(list(exclusions.get(session_date, [])) +
                       fx_common.holiday_exclusion_flags(sym, calendar,
                                                         session_date) +
                       fx_common.roll_anchor_exclusions(sym, session_date) +
                       observables.get("flags", [])))
    blocking = sorted(set(blocking_flags(flags) +
                          [f for f in ("PRIOR_SESSION_CLOSE_ABSENT",
                                       "ANCHOR_BAR_ABSENT",
                                       "ATR_WARMUP_INSUFFICIENT",
                                       "SUNDAY_REOPEN_STRATUM")
                           if f in flags]))
    base = {"session_date": session_date, "family": FAMILY, "symbol": sym,
            "threshold": min_gap_threshold,
            "threshold_label": "SYNTHETIC-PARAMETER-NOT-REGISTERED",
            "gap_a": observables["gap_a"], "gap_b": observables["gap_b"],
            "strata": ["SUNDAY_REOPEN"] if "SUNDAY_REOPEN_STRATUM" in flags
                      else ["WEEKDAY_REOPEN"],
            "proposed": "PROPOSED — conditional on PB2 lift; not a scored "
                        "signal", **ident}
    if blocking:
        base.update({"status": "NO_TRADE", "flags": flags, "blocking": blocking})
        return base
    gap = observables["gap_a"]
    if gap is None or abs(gap) <= min_gap_threshold:
        base.update({"status": "NO_TRADE", "flags": flags,
                     "blocking": ["GAP_BELOW_THRESHOLD"],
                     "placebo_class": "zero/minimum-gap-day placebo"})
        return base
    return {**base, "status": "TRIGGERED", "tail": "UP" if gap > 0 else "DN",
            "arms": ["GC", "GD"], "delay_slots": list(delay_slots),
            "atr20": observables["atr20"], "flags": flags}


def _f4_exit(panel: dict, session_date: str, fill_ts: str, sl: float, tp: float,
             direction: int) -> tuple[float, str]:
    """SL-priority / TP walk with the 09:00-CT provisional time exit."""
    close_bar = None
    for b in fx_common.session_bars(panel, session_date):
        if b["ts"] < fill_ts:
            continue
        m = fx_common.ct_minutes(b["_dt"])
        lo, hi = float(b["low"]), float(b["high"])
        hit_sl = (direction == 1 and lo <= sl) or (direction == -1 and hi >= sl)
        hit_tp = (direction == 1 and hi >= tp) or (direction == -1 and lo <= tp)
        if hit_sl:
            return sl, "SL_TOUCH"
        if hit_tp:
            return tp, "TP_TOUCH"
        if m == EXIT_0900_CT_MIN:
            close_bar = b
    if close_bar is not None:
        return float(close_bar["close"]), "TIME_EXIT_0900CT_PROVISIONAL"
    raise PanelError(f"no 09:00 CT bar for the provisional time exit: "
                     f"{session_date}")


def order_intent(panel: dict, observables: dict, sig: dict, identity_id: str,
                 sym: str, delay_slot: str = "D0",
                 resolve_exit: bool = True) -> dict:
    """D0 = open of the 17:05-CT bar (auction minute excluded); D1B = 17:06;
    D30M = 17:35. Exit TP/SL else 09:00-CT provisional flat."""
    fx_common.require_synthetic(panel)
    session_date = sig["session_date"]
    if sig["status"] != "TRIGGERED":
        return {"identity_id": identity_id, "status": "NO_TRADE",
                "flags": sig["flags"], "session_date": session_date}
    if identity_id not in sig["identity_draft_ids"]:
        raise PanelError(f"identity {identity_id!r} not in the DRAFT enumeration")
    fill_min = FILL_CT_MIN + {"D0": 0, "D1B": 1, "D30M": 30}[delay_slot]
    fill = _bar_at(panel, session_date, fill_min)
    if fill is None:
        return {"identity_id": identity_id, "status": "NO_TRADE",
                "flags": ["FILL_BAR_ABSENT"], "session_date": session_date}
    entry = float(fill["open"])
    arm = identity_id.split("-")[2]
    direction = 1 if (arm == "GC") == (sig["tail"] == "UP") else -1
    atr = float(sig["atr20"])
    sl = fx_common.round_to_tick(entry - direction * atr, sym)
    tp = fx_common.round_to_tick(entry + direction * 2.0 * atr, sym)
    if resolve_exit:
        exit_px, exit_rule = _f4_exit(panel, session_date, fill["ts"], sl, tp,
                                      direction)
    else:
        exit_px, exit_rule = None, "NOT_RESOLVED_AT_DECISION_INSTANT"
    return {
        "identity_id": identity_id, "session_date": session_date,
        "family": FAMILY, "symbol": sym, "arm": arm, "tail": sig["tail"],
        "delay_slot": delay_slot, "tier": "S2", "strata": sig["strata"],
        "window": "WINDOW_A_REOPEN_1700_PRIMARY",
        "status": "ORDER_INTENT", "side": "BUY" if direction == 1 else "SELL",
        "entry_ts_intent": fill["ts"], "entry_px_intent": entry,
        "fill_law": "CONSERVATIVE_NEXT_BAR_OPEN; T+5m auction-minute exclusion; "
                    "BBO NOT_RUN (D5; P5-FXEB-OD8); close-proxy spread likely "
                    "MOST biased-low at the 17:00 CT thin window (disclosed)",
        "sl_level": sl, "tp_level": tp, "same_bar_priority": "SL",
        "exit_px_model": exit_px, "exit_rule": exit_rule,
        "horizon": "intraday_same_session; provisional flat 09:00 CT",
        "cost_model": fx_common.cost_ladder_usd(sym, "S2", 1.0),
        "cost_gate_consumable": False,
        "k_views": {"K5_era": "2020-22" if int(session_date[:4]) <= 2022
                    else "2023-26"},
        "provenance": panel["provenance"], "pit_asof": fill["ts"],
        "proposed": "PROPOSED — conditional on PB2 lift; no order transmission",
        "decision_slot_dependencies": fx_common.decision_slot_dependencies(),
    }
