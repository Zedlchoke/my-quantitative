"""adapter — 6A-AF3 BIMODAL US+SYDNEY SESSION STRUCTURE (PROPOSED;
CONTINGENCY-PB3-PARK machinery, never activated).

Law text: ./FROZEN_RULE_DRAFT.md. Family: Sydney-morning 09:30-11:30 range
break; arms AF3-ROT (rotate into the deep US book) / AF3-ABS (absorbed).
Sources: SPEC_6A_CONTINGENCY s.1-3/s.5/s.7; CENSUS AF3 dossier (bimodal
U-curve anatomy; K4 China-window kill; K3 DST-artifact kill);
CALENDAR_PIT_POLICY s.4; COST_CONTRACT s.2-3; frozen 26-ID table sha 1a96b8ea...

Outcome-blind: synthetic fixtures only. Real-data refuses on P5-FXJA-D5.
K4: a trigger inside the 09:30-10:00 Asia/Shanghai data window refuses
(REFUSED_CHINA_CALENDAR_NOT_RUN — China calendars NOT_RUN, P5-HYPO-OD3).
"""
from __future__ import annotations

from datetime import datetime

import fx_common as fc

FAMILY = "AF3"
SYMBOL = "6A"
TZ = fc.SYD
WINDOW_START_MIN = 9 * 60 + 30         # 09:30 Sydney
WINDOW_END_MIN = 11 * 60 + 30          # 11:30 Sydney
NOMINAL_WINDOW_BARS = WINDOW_END_MIN - WINDOW_START_MIN   # 120
COVERAGE_FLOOR = 0.80
TRIGGER_EVAL_LOCAL_MIN = WINDOW_END_MIN
DELAY_MINUTES = {"D1": 0, "D30M": 30}
ATR_PERIOD = 20                        # daily ATR(20), prior held sessions
SL_ATR_MULT = 1.0
TP_SL_MULT = 2.0
TIME_EXIT_UTC_LIMIT = None             # 16:00 CT per date (resolved per session)
CHINA_WINDOW = (9 * 60 + 30, 10 * 60)  # 09:30-10:00 Asia/Shanghai (AF3 K4)
CORE_IDS = fc.contingency_6a_ids("AF3")[:8]
CONTROL_IDS = fc.contingency_6a_ids("AF3")[8:]
DRAFT_IDS = CORE_IDS + CONTROL_IDS     # 8 + 3 = 11 contingency shapes


def af3_freeze_check() -> dict:
    if fc.GUARDS["P5-FXJA-D5"] is None:
        raise fc.RefusedPendingOwnerDecision(
            "P5-FXJA-D5",
            "6A stays PB3 PARK: 0 budget, 0 identities; activation = PB3 lift "
            "-> D8 -> D9 -> D2 -> ABS/China calendar (P5-HYPO-OD3 class)")
    return {"frozen_by": fc.GUARDS["P5-FXJA-D5"]}


class AF3Adapter:
    family = FAMILY
    symbol = SYMBOL

    def __init__(self, contract: dict | None = None):
        self.contract = contract or fc.load_fx_contract(SYMBOL)

    # ---------------------------------------------------------------- API
    def apply_exclusions(self, calendar: dict, panel: dict) -> dict:
        """EXCLUDE RBA + FOMC days; coverage >=80% of nominal Sydney-morning
        bars else EXCLUDE; the CALENDAR s.5 inventory."""
        out = fc.apply_fx_exclusions(calendar, panel, SYMBOL,
                                     coverage_windows=[(TZ, WINDOW_START_MIN,
                                                        WINDOW_END_MIN)],
                                     exclude_fomc=True)
        for sd in calendar.get("rba_decision_dates", []):
            out.setdefault(sd, []).append("X_RBA_DAY")
        return {k: sorted(set(v)) for k, v in out.items()}

    def build_observables(self, panel: dict, calendar: dict) -> dict:
        fc.require_synthetic(panel, SYMBOL)
        fc.validate_panel(panel, SYMBOL)
        excl = self.apply_exclusions(calendar, panel)
        out = {"window": "09:30-11:30 Sydney", "coverage_floor": COVERAGE_FLOOR,
               "china_window_sha": list(CHINA_WINDOW),
               "quote_direction": "USD per AUD; 6A UP = AUD stronger",
               "sessions": []}
        for s in panel["sessions"]:
            sd = s["session_date"]
            wb = fc.window_bars(panel, sd, TZ, WINDOW_START_MIN, WINDOW_END_MIN)
            if not wb:
                continue
            out["sessions"].append({
                "date": sd, "era": fc.sixa_era_for_date(sd),
                "range_hi": max(float(b["high"]) for b in wb),
                "range_lo": min(float(b["low"]) for b in wb),
                "coverage": round(len(wb) / NOMINAL_WINDOW_BARS, 6),
                "excluded": sd in excl,
            })
        return out

    def sydney_range(self, panel: dict, session_date: str,
                     asof: str | datetime | None = None) -> dict | None:
        wb = fc.window_bars(panel, session_date, TZ,
                            WINDOW_START_MIN, WINDOW_END_MIN, upto=asof)
        if not wb:
            return None
        return {"range_hi": max(float(b["high"]) for b in wb),
                "range_lo": min(float(b["low"]) for b in wb),
                "coverage": len(wb) / NOMINAL_WINDOW_BARS,
                "complete": (fc.local_minutes(wb[-1]["_dt"], TZ)
                             == WINDOW_END_MIN - 1)}

    def in_china_window(self, ts: datetime) -> bool:
        lm = fc.local_minutes(ts, fc.SHA)
        return CHINA_WINDOW[0] <= lm < CHINA_WINDOW[1]

    def signal(self, panel: dict, calendar: dict, session_date: str,
               asof: str | datetime | None = None) -> dict:
        """PIT signal: first 1m close strictly outside the Sydney-morning
        range, evaluated from 11:30 Sydney. K4: a trigger inside the Shanghai
        data window is a contamination boundary -> fail-closed NO-TRADE."""
        fc.require_synthetic(panel, SYMBOL)
        base = {"family": FAMILY, "session_date": session_date,
                "window_law": "09:30-11:30 Sydney range; break from 11:30 Syd",
                "era": fc.sixa_era_for_date(session_date),
                "quote_direction": "USD per AUD; 6A UP = AUD stronger",
                "fold_id": fc.fold_for_date(session_date)}
        eval_dt = (asof if isinstance(asof, datetime) else fc.parse_ts(asof)) \
            if asof is not None else fc.session_last_dt(panel, session_date)
        window_close_dt = fc.at_local(session_date, 11, 30, TZ)
        if eval_dt is not None and eval_dt < window_close_dt:
            return {**base, "knowable": False, "tail": None,
                    "no_trade_reason": "RANGE_NOT_COMPLETE_UPTO_ASOF"}
        rng = self.sydney_range(panel, session_date, asof=asof)
        if rng is None:
            return {**base, "knowable": False, "tail": None,
                    "no_trade_reason": "RANGE_NOT_COMPLETE_UPTO_ASOF"}
        if rng["coverage"] < COVERAGE_FLOOR:
            return {**base, "knowable": False, "tail": None,
                    "no_trade_reason": "WINDOW_COVERAGE_BELOW_FLOOR"}
        post = [b for b in fc.session_bars(panel, session_date, upto=asof)
                if fc.local_minutes(b["_dt"], TZ) >= TRIGGER_EVAL_LOCAL_MIN]
        trig = fc.first_close_outside(post, rng["range_lo"], rng["range_hi"])
        if trig is None:
            return {**base, "knowable": True, "tail": None,
                    "no_trade_reason": "NO_BREAK_UPTO_ASOF"}
        if self.in_china_window(trig["_dt"]):
            return {**base, "knowable": False, "tail": None,
                    "k4_contamination": True,
                    "trigger_sha_local": fc.local_hhmm(trig["_dt"], fc.SHA),
                    "no_trade_reason": "CHINA_WINDOW_CONTAMINATION_K4"}
        tail = "UP" if float(trig["close"]) > rng["range_hi"] else "DN"
        return {**base, "knowable": True, "tail": tail,
                "trigger_ts": trig["_dt"].isoformat(),
                "decision_time": (trig["_dt"] + _ONE_MIN).isoformat(),
                "range_hi": rng["range_hi"], "range_lo": rng["range_lo"],
                "trigger_close": float(trig["close"]),
                "no_trade_reason": None}


_ONE_MIN = __import__("datetime").timedelta(minutes=1)


class AF3AdapterFull(AF3Adapter):
    """order_intent half (CONTINGENCY machinery)."""

    def order_intent(self, panel: dict, calendar: dict, identity_id: str,
                     session_date: str, asof: str | datetime | None = None,
                     cost_tier: str = "T1", cost_slip: str = "S1",
                     stress: float = 1.0) -> dict:
        fc.require_synthetic(panel, SYMBOL)
        if fc.sixa_era_for_date(session_date) == "era1":
            raise fc.RefusedEra1NoTradeIntent(
                f"{session_date} is an era-1 window: descriptive-only "
                f"(no-back-cast law, SPEC_6A s.2)")
        parsed = _parse_identity(identity_id)
        excl = self.apply_exclusions(calendar, panel)
        flags = excl.get(session_date, [])
        tick = fc.sixa_tick(session_date)
        atr = fc.atr20_points(panel, session_date, ATR_PERIOD)
        head = fc.intent_head(FAMILY, identity_id, session_date, panel, {
            "warmup_ok": atr is not None,
            "exclusion_flags": list(flags),
            "era": "era2",
            "tick_size": tick, "tick_value_usd": fc.sixa_tick_value_usd(session_date),
            "multiplier": fc.SIXA_MULTIPLIER,
            "contract": fc.session_map(panel).get(session_date, {}).get("contract"),
            "contingency": "CONTINGENCY-PB3-PARK — machinery, never activated",
        })
        if flags:
            return fc.no_trade(head, "EXCLUDED: " + ",".join(flags))
        if not head["warmup_ok"]:
            return fc.no_trade(head, "ATR_WARMUP_INSUFFICIENT")

        arm, tail_id = parsed["arm"], parsed["tail"]
        if arm in ("ROT", "ABS"):
            sig = self.signal(panel, calendar, session_date, asof)
            if sig.get("no_trade_reason") == "CHINA_WINDOW_CONTAMINATION_K4":
                raise fc.RefusedChinaCalendarNotRun(
                    f"trigger on {session_date} lands inside the 09:30-10:00 "
                    f"Shanghai data window; China splits NOT_RUN (AF3 K4 kills "
                    f"the base spec; P5-HYPO-OD3 acquisition class)")
            if not sig.get("knowable"):
                return fc.no_trade(head, sig.get("no_trade_reason")
                                   or "SIGNAL_NOT_KNOWABLE_AT_ASOF")
            if sig.get("tail") is None:
                return fc.no_trade(head, sig.get("no_trade_reason") or "NO_BREAK")
            if sig["tail"] != tail_id:
                return fc.no_trade(head, "TAIL_MISMATCH")
            trigger_dir = 1 if sig["tail"] == "UP" else -1
            direction = trigger_dir if arm == "ROT" else -trigger_dir
            event_context = {"event_type": "SYDNEY_MORNING_RANGE_BREAK",
                             "trigger_ts": sig["trigger_ts"],
                             "decision_time": sig["decision_time"],
                             "range_hi": sig["range_hi"], "range_lo": sig["range_lo"],
                             "sign_law": "6A UP = AUD stronger"}
        elif arm == "ALW":
            direction = 1
            event_context = {"event_type": "C2_ALWAYS_IN", "signal_ignored": True}
        elif arm == "PLA":
            direction = fc.shadow_direction(session_date)
            event_context = {"event_type": "C1_CLOCK_ONLY_SHADOW",
                             "seed": fc.C1_SEED, "shadow_direction": direction}
        else:   # CLK — C3 weekday-matched non-event clock (RBA/FOMC removed)
            if session_date in set(calendar.get("rba_decision_dates", [])) | \
                    set(calendar.get("fomc_statement_days", [])):
                return fc.no_trade(head, "CLK_EVENT_DAY_MATCH")
            sig = self.signal(panel, calendar, session_date, asof)
            if sig.get("no_trade_reason") == "CHINA_WINDOW_CONTAMINATION_K4":
                raise fc.RefusedChinaCalendarNotRun("CLK share the K4 boundary")
            if sig.get("tail") is None:
                return fc.no_trade(head, sig.get("no_trade_reason") or "CLK_NO_BREAK")
            direction = 1 if sig["tail"] == "UP" else -1
            event_context = {"event_type": "C3_WEEKDAY_MATCHED_CLOCK"}

        return self._resolve_intent(head, panel, session_date, asof, parsed,
                                    direction, atr, event_context,
                                    cost_tier, cost_slip, stress, tick)

    def _resolve_intent(self, head, panel, session_date, asof, parsed, direction,
                        atr, event_context, cost_tier, cost_slip, stress,
                        tick) -> dict:
        bars = fc.session_bars(panel, session_date, upto=asof)
        last_dt = fc.session_last_dt(panel, session_date)
        session_complete = bool(bars) and bars[-1]["_dt"] >= last_dt
        trig_min = fc.local_minutes(fc.parse_ts(event_context["trigger_ts"]), TZ)
        entry_min = (trig_min + 1) + DELAY_MINUTES[parsed["delay"]]
        entry_bar = next((b for b in bars
                          if fc.local_minutes(b["_dt"], TZ) == entry_min), None)
        if entry_bar is None:
            return fc.no_trade(head, "ENTRY_BAR_ABSENT_UPTO_ASOF")
        entry_px = fc.round_to_tick(float(entry_bar["open"]), tick)
        sl_dist = SL_ATR_MULT * float(atr)
        if direction == 1:
            sl_px = fc.round_to_tick(entry_px - sl_dist, tick)
            tp_px = fc.round_to_tick(entry_px + TP_SL_MULT * sl_dist, tick)
        else:
            sl_px = fc.round_to_tick(entry_px + sl_dist, tick)
            tp_px = fc.round_to_tick(entry_px - TP_SL_MULT * sl_dist, tick)
        # time exit 16:00 CT: the scan stops at the CT afternoon close
        ct_close = fc.at_local(session_date, 16, 0, fc.CT)
        after = [b for b in bars
                 if fc.local_minutes(b["_dt"], TZ) >= entry_min
                 and b["_dt"] <= ct_close]
        exitres = fc.resolve_exit(after, entry_px, sl_px, tp_px, tick,
                                  session_complete)
        cost = fc.cost_per_side_usd(SYMBOL, session_date, cost_tier, cost_slip,
                                    stress, session_floor=True)
        return {
            **head, "no_trade": False, "no_trade_reason": None,
            "arm": parsed["arm"], "tail": parsed["tail"], "delay": parsed["delay"],
            "side": "BUY" if direction == 1 else "SELL", "direction": direction,
            "quantity": 1, "order_type": "MARKET_NEXT_BAR_OPEN",
            "decision_time": event_context.get("decision_time"),
            "ts_entry": entry_bar["_dt"].isoformat(),
            "entry_ref_price": entry_px, "sl_price": sl_px, "tp_price": tp_px,
            "atr20_points": float(atr), **exitres,
            "event_context": event_context,
            "cost_preview": cost,
        }


def _parse_identity(identity_id: str) -> dict:
    parts = identity_id.split("-")
    if len(parts) == 7 and parts[0] == fc.CONTINGENCY_TOKEN_6A and parts[1] == "CONT":
        family, arm, tail, delay, tier = parts[2], parts[3], parts[4], parts[5], parts[6]
        if family != "AF3":
            raise ValueError(f"not an AF3 id: {identity_id!r}")
        if arm not in ("ROT", "ABS"):
            raise ValueError(f"unknown AF3 arm {arm!r}")
        if tail not in ("UP", "DN"):
            raise ValueError(f"arm {arm} requires tail UP/DN")
        if tier != "S2":
            raise ValueError("CONV-B core tier is S2")
        return {"arm": arm, "tail": tail, "delay": delay, "tier": tier}
    if len(parts) == 4 and parts[0] == fc.CONTINGENCY_TOKEN_6A and parts[2] == "AF3":
        if parts[1] not in ("PLA", "ALW", "CLK"):
            raise ValueError(f"unknown AF3 control {parts[1]!r}")
        return {"arm": parts[1], "tail": None, "delay": "D1", "tier": None}
    raise ValueError(f"identity {identity_id!r} does not match the AF3 "
                     f"CONTINGENCY-PB3-PARK grammar")


# The shipped adapter class carries both halves:
AF3Adapter = AF3AdapterFull   # noqa: F811 — single exported class
