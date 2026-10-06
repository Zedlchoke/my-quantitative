"""FX-F1 London-Range Absorption adapter (6E + 6B) — PROPOSED machinery.

Rule text as code: see FROZEN_RULE_DRAFT.md in this directory. Pure
deterministic functions; outcome-blind; synthetic fixtures only
(require_synthetic gates any real-data path on P5-FXEB-OD1).

Per-symbol parameterization lives in fx_common.SYMBOL_LAW: London-local
windowing is shared law (census gate definition), but the F2 day-sets
(6E FOMC∪ECB / 6B MPC∪FOMC), holiday posture (6E fail-closed lists vs 6B
0/42 declared absence), NOT_OBTAINED quarters, tick grid and cost floor
are the symbol's own and are never shared silently.
"""
from __future__ import annotations

from datetime import datetime

import fx_common
from fx_common import (CT, LONDON, PanelError, RefusedPendingOwnerDecision,
                       blocking_flags, is_blocked)

FAMILY = "FX-F1"
RANGE_WINDOW_LON = (8 * 60, 11 * 60)      # [08:00, 11:00) London
TRIGGER_WINDOW_LON = (11 * 60, 15 * 60 + 30)  # [11:00, 15:30) London
COVERAGE_THRESHOLD = 0.80                 # census base filter
EXIT_SESSION_CLOSE = 16 * 60              # 16:00 CT mandatory flat


def _lon_wall(dt: datetime) -> int:
    loc = dt.astimezone(LONDON)
    return loc.hour * 60 + loc.minute


def london_coverage(panel: dict, session_date: str) -> float:
    """Minutes-with-bar share of [08:00, 11:00) London on the session date."""
    bars = fx_common.session_bars(panel, session_date)
    have = {w for b in bars if RANGE_WINDOW_LON[0] <= _lon_wall(b["_dt"]) < RANGE_WINDOW_LON[1]
            for w in [_lon_wall(b["_dt"])]}
    return len(have) / (RANGE_WINDOW_LON[1] - RANGE_WINDOW_LON[0])


def build_observables(panel: dict, calendar: dict, sym: str,
                      session_date: str) -> dict:
    """R_lon, coverage, first-touch trigger — all strict past at the trigger close."""
    fx_common.require_synthetic(panel)
    if sym not in fx_common.SYMBOLS:
        raise ValueError(f"unknown symbol {sym!r}")
    fx_common.validate_panel(panel)
    bars = fx_common.session_bars(panel, session_date)
    range_bars = [b for b in bars
                  if RANGE_WINDOW_LON[0] <= _lon_wall(b["_dt"]) < RANGE_WINDOW_LON[1]]
    if not range_bars:
        return {"session_date": session_date, "symbol": sym, "family": FAMILY,
                "rlon": None, "coverage": 0.0, "trigger": None, "atr20": None,
                "flags": ["RANGE_WINDOW_EMPTY"]}
    rlon_lo = min(float(b["low"]) for b in range_bars)
    rlon_hi = max(float(b["high"]) for b in range_bars)
    cov = london_coverage(panel, session_date)
    trigger = None
    for b in bars:
        w = _lon_wall(b["_dt"])
        if not (TRIGGER_WINDOW_LON[0] <= w < TRIGGER_WINDOW_LON[1]):
            continue
        c = float(b["close"])
        if c > rlon_hi or c < rlon_lo:
            trigger = {"ts": b["ts"], "close": c, "sign": "UP" if c > rlon_hi else "DN",
                       "bar_ct": fx_common.ct_minutes(b["_dt"])}
            break  # cap 1 trigger/session, first-touch
    atr = fx_common.atr20_points(panel, session_date)
    flags = []
    if trigger is None:
        flags.append("NO_TRIGGER")
    if cov < COVERAGE_THRESHOLD:
        flags.append("LONDON_COVERAGE_LT_080")
    if atr is None:
        flags.append("ATR_WARMUP_INSUFFICIENT")
    return {"session_date": session_date, "symbol": sym, "family": FAMILY,
            "rlon": [rlon_lo, rlon_hi], "coverage": round(cov, 6),
            "trigger": trigger, "atr20": atr, "flags": flags,
            "k_views": k_views(session_date, sym)}


def k_views(session_date: str, sym: str) -> dict:
    """Declared evaluation views (labels only): era split, DST-mismatch-week
    split, 6B London-share-drift split, census band."""
    y = int(session_date[:4])
    dst_mismatch = session_date[:10] in {
        # UK/US DST out-of-sync weeks (UTC offsets differ): the K4 clock-bug
        # detector windows (representative, zoneinfo is authoritative in code).
        "2020-03-09", "2020-03-10", "2020-03-11", "2020-03-12", "2020-03-13",
        "2021-03-08", "2021-03-09", "2021-03-10", "2021-03-11", "2021-03-12",
        "2021-11-01", "2021-11-02", "2021-11-03", "2021-11-04", "2021-11-05",
        "2022-03-07", "2022-03-08", "2022-03-09", "2022-03-10", "2022-03-11",
        "2022-10-31", "2022-11-01", "2022-11-02", "2022-11-03", "2022-11-04",
        "2023-03-06", "2023-03-07", "2023-03-08", "2023-03-09", "2023-03-10",
        "2023-10-30", "2023-10-31", "2023-11-01", "2023-11-02", "2023-11-03",
        "2024-03-04", "2024-03-05", "2024-03-06", "2024-03-07", "2024-03-08",
        "2024-10-28", "2024-10-29", "2024-10-30", "2024-11-01",
        "2025-03-03", "2025-03-04", "2025-03-05", "2025-03-06", "2025-03-07",
        "2025-10-27", "2025-10-28", "2025-10-29", "2025-10-30", "2025-10-31",
        "2026-03-02", "2026-03-03", "2026-03-04", "2026-03-05", "2026-03-06",
        "2026-03-09", "2026-03-10", "2026-03-11", "2026-03-12", "2026-03-13",
        "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30",
    }
    return {
        "K5_era": "2020-22" if y <= 2022 else "2023-26",
        "K_DST_mismatch_week": dst_mismatch,
        "K_london_share_drift" + ("_6B_falsifier" if sym == "6B" else ""):
            "2020-22" if y <= 2022 else "2023-26",
        "census_triggers": fx_common.SYMBOL_LAW[sym]["census_triggers"],
    }


def apply_exclusions(panel: dict, calendar: dict, sym: str) -> dict:
    """Family-scoped fail-closed exclusion pass (FROZEN_RULE_DRAFT §4)."""
    fx_common.require_synthetic(panel)
    cov = {s["session_date"]: london_coverage(panel, s["session_date"])
           for s in panel["sessions"]}
    return fx_common.apply_exclusions(sym, calendar, panel, family=FAMILY,
                                      coverage_threshold=COVERAGE_THRESHOLD,
                                      london_coverage=cov)


def signal(observables: dict, session_date: str, exclusions: dict,
           sym: str, calendar: dict, panel: dict,
           delay_slots: tuple[str, ...] = fx_common.DELAY_SLOTS_DRAFT) -> dict:
    """Trigger signal for the session under the draft delay-slot law.

    Excluded sessions return NO-TRADE with their flags (declaration-only flags
    on 6B never block). ATR warmup insufficiency blocks. No trigger blocks.
    """
    fx_common.require_synthetic(panel)
    if delay_slots not in (fx_common.DELAY_SLOTS_DRAFT, fx_common.DELAY_SLOTS_ALT):
        raise ValueError("delay slots must be draft default or declared alternative "
                         "(binding requires P5-FXEB-OD3)")
    flags = list(exclusions.get(session_date, []))
    flags += fx_common.holiday_exclusion_flags(sym, calendar, session_date)
    flags += fx_common.roll_anchor_exclusions(sym, session_date)
    obs_flags = list(observables.get("flags", []))
    if obs_flags:
        flags += [f for f in obs_flags if f not in flags]
    blocking = blocking_flags(flags) + [f for f in ("ATR_WARMUP_INSUFFICIENT",
                                                    "NO_TRIGGER")
                                        if f in flags]
    if blocking:
        return {"session_date": session_date, "family": FAMILY, "symbol": sym,
                "status": "NO_TRADE", "flags": sorted(set(flags)),
                "blocking": sorted(set(blocking)),
                "identity_draft_ids": fx_common.core_ids(FAMILY, sym, delay_slots)
                                      + fx_common.control_ids(FAMILY, sym),
                "decision_slot_dependencies": fx_common.decision_slot_dependencies()}
    trig = observables["trigger"]
    return {"session_date": session_date, "family": FAMILY, "symbol": sym,
            "status": "TRIGGERED", "tail": trig["sign"], "arms": ["HC", "HD"],
            "delay_slots": list(delay_slots), "trigger_ts": trig["ts"],
            "trigger_close": trig["close"], "rlon": observables["rlon"],
            "atr20": observables["atr20"],
            "flags": sorted(set(flags)),
            "identity_draft_ids": fx_common.core_ids(FAMILY, sym, delay_slots)
                                  + fx_common.control_ids(FAMILY, sym),
            "decision_slot_dependencies": fx_common.decision_slot_dependencies(),
            "proposed": "PROPOSED — conditional on PB2 lift; not a scored signal"}


def _fill_bars(panel: dict, session_date: str, after_ct_min: int, count: int = 1) -> list[dict]:
    bars = [b for b in fx_common.session_bars(panel, session_date)
            if fx_common.ct_minutes(b["_dt"]) >= after_ct_min]
    return bars[:count]


def order_intent(panel: dict, observables: dict, sig: dict, identity_id: str,
                 sym: str, delay_slot: str = "D0",
                 resolve_exit: bool = True) -> dict:
    """Intended order for one DRAFT identity on one session (journal-payload
    shape, TRADE_JOURNAL_SCHEMA_6E_6B.md). Conservative fill: D0 = open of the
    first bar after the trigger; D1B = one bar later; D30M = D0 bar + 30 min.
    Exit = TP 2xSL_distance / SL 1.0xATR(20), same-bar SL-priority, else 16:00
    CT close. No transmission, no BBO claim (BBO NOT_RUN, D5/P5-FXEB-OD8).
    resolve_exit=False is the PIT-truncated read: entry fields are produced at
    the decision instant; the exit (a future event by construction) is emitted
    as NOT_RESOLVED_AT_DECISION_INSTANT instead of consuming future bars."""
    fx_common.require_synthetic(panel)
    session_date = sig["session_date"]
    if sig["status"] != "TRIGGERED":
        return {"identity_id": identity_id, "status": "NO_TRADE",
                "flags": sig["flags"], "session_date": session_date}
    if identity_id not in sig["identity_draft_ids"]:
        raise PanelError(f"identity {identity_id!r} not in the DRAFT enumeration "
                         f"for {FAMILY}/{sym}")
    trig = sig["trigger_close"]
    trig_min = fx_common.ct_minutes(fx_common.parse_ts(sig["trigger_ts"]))
    base_fill_min = trig_min + 1
    if delay_slot == "D0":
        fill_min = base_fill_min
    elif delay_slot == "D1B":
        fill_min = base_fill_min + 1
    elif delay_slot == "D30M":
        fill_min = base_fill_min + 30
    else:
        raise ValueError(f"unknown delay slot {delay_slot!r}")
    fills = _fill_bars(panel, session_date, fill_min, 1)
    if not fills:
        return {"identity_id": identity_id, "status": "NO_TRADE",
                "flags": ["FILL_BAR_ABSENT"], "session_date": session_date}
    entry = float(fills[0]["open"])
    arm = identity_id.split("-")[2]
    direction = 1 if (arm == "HC") == (sig["tail"] == "UP") else -1
    atr = float(sig["atr20"])
    sl_dist = 1.0 * atr
    sl = fx_common.round_to_tick(entry - direction * sl_dist, sym)
    tp = fx_common.round_to_tick(entry + direction * 2.0 * sl_dist, sym)
    if resolve_exit:
        exit_px, exit_rule = fx_common.exit_walk(panel, session_date,
                                                 fills[0]["ts"], sl, tp, direction)
    else:
        exit_px, exit_rule = None, "NOT_RESOLVED_AT_DECISION_INSTANT"
    cost = fx_common.cost_ladder_usd(sym, "S2", 1.0)
    return {
        "identity_id": identity_id, "session_date": session_date,
        "family": FAMILY, "symbol": sym, "arm": arm, "tail": sig["tail"],
        "delay_slot": delay_slot, "tier": "S2",
        "status": "ORDER_INTENT", "side": "BUY" if direction == 1 else "SELL",
        "entry_ts_intent": fills[0]["ts"], "entry_px_intent": entry,
        "fill_law": "CONSERVATIVE_NEXT_BAR_OPEN; BBO NOT_RUN (D5; P5-FXEB-OD8)",
        "sl_level": sl, "tp_level": tp, "same_bar_priority": "SL",
        "exit_px_model": exit_px, "exit_rule": exit_rule,
        "horizon": "intraday_same_session; mandatory flat 16:00 CT",
        "cost_model": cost, "cost_gate_consumable": False,
        "k_views": observables.get("k_views"), "provenance": panel["provenance"],
        "pit_asof": exit_px and fills[0]["ts"],
        "proposed": "PROPOSED — conditional on PB2 lift; no order transmission; "
                    "no scored consumption",
        "decision_slot_dependencies": fx_common.decision_slot_dependencies(),
    }
