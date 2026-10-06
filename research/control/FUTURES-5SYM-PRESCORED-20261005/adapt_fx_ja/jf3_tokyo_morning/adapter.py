"""adapter — 6J-JF3 TOKYO-MORNING SESSION STRUCTURE (PROPOSED draft machinery).

Law text: ./FROZEN_RULE_DRAFT.md (PROPOSED — never an approved freeze).
Family: Tokyo-morning 09:00-11:30 JST range break; arms JF3-CONT / JF3-FADE.
Sources: SPEC_6J.md s.3/s.4/s.7/s.8; CENSUS_5SYM.md JF3 dossier (incl. the
row-34 dead-adjacency disclosure); IDENTITY_BUDGET_6J.md s.2 (FB6J1-JF3-*).

QUOTE-DIRECTION LAW: 6J UP = yen STRONG; the break tail and every arm sign
are in 6J PRICE terms (SPEC_6J s.2 orientation proof).

Outcome-blind: SIGNALS + intended ORDER INTENT on synthetic fixtures only;
real-data paths refuse on P5-FXJA-D1. Dead-adjacency warning carried: the
nearest ancestry row (FOREX-FREE-V2-A4-P1, row 34, EXPECTANCY_NONPOSITIVE on
SPOT) binds the full clock/sham placebo set to this family's scored future.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import fx_common as fc

FAMILY = "JF3"
SYMBOL = "6J"
TZ = fc.JST
WINDOW_START_MIN = 9 * 60            # 09:00 JST
WINDOW_END_MIN = 11 * 60 + 30        # 11:30 JST (exclusive bar-start bound)
NOMINAL_WINDOW_BARS = WINDOW_END_MIN - WINDOW_START_MIN   # 150
COVERAGE_FLOOR = 0.80                # Tokyo-window >=80% of nominal bars else EXCLUDE
TRIGGER_EVAL_LOCAL_MIN = WINDOW_END_MIN
# Delay law: D1 = the first 1m bar after the trigger bar; D30M = +30 minutes
# after the trigger bar's close-minute.
DELAY_MINUTES = {"D1": 0, "D30M": 30}
ATR_PERIOD = 20                      # daily ATR(20), prior held sessions, strict past
SL_ATR_MULT = 1.0
TP_SL_MULT = 2.0
ONE_MIN = timedelta(minutes=1)
CORE_IDS = fc.jf3_core_ids()
CONTROL_IDS = fc.jf_control_ids(FAMILY)
DRAFT_IDS = CORE_IDS + CONTROL_IDS   # 8 + 3 = 11 (CONV-B minimal, JF3 block)


class JF3Adapter:
    family = FAMILY
    symbol = SYMBOL

    def __init__(self, contract: dict | None = None):
        self.contract = contract or fc.load_fx_contract(SYMBOL)
        self.tick = self.contract["tick_size"]
        self.mult = self.contract["multiplier"]

    # ---------------------------------------------------------------- API
    def apply_exclusions(self, calendar: dict, panel: dict) -> dict:
        """Fail-closed pass: base EXCLUDES BoJ MPM dates + MOF disclosure dates;
        Tokyo-window >=80% coverage rule; the CALENDAR s.5 inventory."""
        return fc.apply_fx_exclusions(calendar, panel, SYMBOL,
                                      coverage_windows=[(TZ, WINDOW_START_MIN,
                                                         WINDOW_END_MIN)],
                                      exclude_boj_mpm=True,
                                      exclude_mof_disclosure=True)

    def build_observables(self, panel: dict, calendar: dict) -> dict:
        """Tokyo-morning range + coverage per session (strict past at 11:30)."""
        fc.require_synthetic(panel, SYMBOL)
        fc.validate_panel(panel, SYMBOL)
        out = {"window": "09:00-11:30 JST", "coverage_floor": COVERAGE_FLOOR,
               "quote_direction": fc.QUOTE_DIRECTION_6J,
               "sessions": []}
        excl = self.apply_exclusions(calendar, panel)
        for s in panel["sessions"]:
            sd = s["session_date"]
            wb = fc.window_bars(panel, sd, TZ, WINDOW_START_MIN, WINDOW_END_MIN)
            if not wb:
                continue
            out["sessions"].append({
                "date": sd,
                "range_hi": max(float(b["high"]) for b in wb),
                "range_lo": min(float(b["low"]) for b in wb),
                "coverage": round(len(wb) / NOMINAL_WINDOW_BARS, 6),
                "excluded": sd in excl,
            })
        return out

    def tokyo_range(self, panel: dict, session_date: str,
                    asof: str | datetime | None = None) -> dict | None:
        """The 09:00-11:30 JST window range as of `asof` (strict past; the
        range is fully formed only at the window close, 11:30 JST)."""
        wb = fc.window_bars(panel, session_date, TZ,
                            WINDOW_START_MIN, WINDOW_END_MIN, upto=asof)
        if not wb:
            return None
        return {"range_hi": max(float(b["high"]) for b in wb),
                "range_lo": min(float(b["low"]) for b in wb),
                "n_bars": len(wb),
                "coverage": len(wb) / NOMINAL_WINDOW_BARS,
                "complete": (fc.local_minutes(wb[-1]["_dt"], TZ)
                             == WINDOW_END_MIN - 1)}

    def signal(self, panel: dict, calendar: dict, session_date: str,
               asof: str | datetime | None = None) -> dict:
        """PIT signal: first 1m close strictly outside the 09:00-11:30 JST
        range, evaluated from 11:30 JST onward. Decision time = the trigger
        bar's close (start + 1 min)."""
        fc.require_synthetic(panel, SYMBOL)
        base = {"family": FAMILY, "session_date": session_date,
                "window_law": "09:00-11:30 JST range; break evaluated from 11:30 JST",
                "quote_direction": fc.QUOTE_DIRECTION_6J,
                "fold_id": fc.fold_for_date(session_date)}
        # evaluation instant: explicit asof, else the session's measured end
        eval_dt = (asof if isinstance(asof, datetime) else fc.parse_ts(asof)) \
            if asof is not None else fc.session_last_dt(panel, session_date)
        window_close_dt = fc.at_local(session_date, 11, 30, TZ)
        rng = self.tokyo_range(panel, session_date, asof=asof)
        if eval_dt is not None and eval_dt < window_close_dt:
            return {**base, "knowable": False, "tail": None, "trigger": None,
                    "no_trade_reason": "RANGE_NOT_COMPLETE_UPTO_ASOF"}
        if rng is None:
            return {**base, "knowable": False, "tail": None, "trigger": None,
                    "no_trade_reason": "RANGE_NOT_COMPLETE_UPTO_ASOF"}
        if rng["coverage"] < COVERAGE_FLOOR:
            return {**base, "knowable": False, "tail": None, "trigger": None,
                    "no_trade_reason": "WINDOW_COVERAGE_BELOW_FLOOR"}
        post = [b for b in fc.session_bars(panel, session_date, upto=asof)
                if fc.local_minutes(b["_dt"], TZ) >= TRIGGER_EVAL_LOCAL_MIN]
        trig = fc.first_close_outside(post, rng["range_lo"], rng["range_hi"])
        if trig is None:
            return {**base, "knowable": True, "tail": None, "trigger_ts": None,
                    "decision_time": None,
                    "no_trade_reason": "NO_BREAK_UPTO_ASOF"}
        tail = "UP" if float(trig["close"]) > rng["range_hi"] else "DN"
        decision_dt = trig["_dt"] + ONE_MIN
        return {**base, "knowable": True, "tail": tail,
                "trigger_ts": trig["_dt"].isoformat(),
                "decision_time": decision_dt.isoformat(),
                "range_hi": rng["range_hi"], "range_lo": rng["range_lo"],
                "trigger_close": float(trig["close"]),
                "no_trade_reason": None}

    def order_intent(self, panel: dict, calendar: dict, identity_id: str,
                     session_date: str, asof: str | datetime | None = None,
                     cost_tier: str = "T1", cost_slip: str = "S1",
                     stress: float = 1.0) -> dict:
        """Intended ORDER INTENT (never an execution). Identity grammar:
        cores FB6J1-JF3-{CONT,FADE}-{UP,DN}-{D1,D30M}-S2; controls
        FB6J1-{PLA,ALW,CLK}-JF3. Evaluation order: exclusions -> warmup ->
        arm routing (6J price-term signs) -> conservative fill/exit."""
        fc.require_synthetic(panel, SYMBOL)
        parsed = _parse_identity(identity_id)
        excl = self.apply_exclusions(calendar, panel)
        flags = excl.get(session_date, [])
        atr = fc.atr20_points(panel, session_date, ATR_PERIOD)
        head = fc.intent_head(FAMILY, identity_id, session_date, panel, {
            "warmup_ok": atr is not None,
            "exclusion_flags": list(flags),
            "tick_size": self.tick, "multiplier": self.mult,
            "contract": fc.session_map(panel).get(session_date, {}).get("contract"),
            "quote_direction": fc.QUOTE_DIRECTION_6J,
        })
        if flags:
            return fc.no_trade(head, "EXCLUDED: " + ",".join(flags))
        if not head["warmup_ok"]:
            return fc.no_trade(head, "ATR_WARMUP_INSUFFICIENT")
        if parsed["delay"] not in DELAY_MINUTES:
            return fc.no_trade(head, "UNSUPPORTED_DELAY")

        arm, tail_id = parsed["arm"], parsed["tail"]
        if arm in ("CONT", "FADE"):
            sig = self.signal(panel, calendar, session_date, asof)
            if not sig.get("knowable"):
                return fc.no_trade(head, sig.get("no_trade_reason")
                                   or "SIGNAL_NOT_KNOWABLE_AT_ASOF")
            if sig.get("tail") is None:
                return fc.no_trade(head, sig.get("no_trade_reason") or "NO_BREAK")
            if sig["tail"] != tail_id:
                return fc.no_trade(head, "TAIL_MISMATCH")
            trigger_dir = 1 if sig["tail"] == "UP" else -1   # 6J price terms
            direction = trigger_dir if arm == "CONT" else -trigger_dir
            event_context = {
                "event_type": "TOKYO_MORNING_RANGE_BREAK",
                "trigger_ts": sig["trigger_ts"],
                "decision_time": sig["decision_time"],
                "range_hi": sig["range_hi"], "range_lo": sig["range_lo"],
                "trigger_close": sig["trigger_close"],
                "sign_law": "6J UP = yen STRONG (SPEC_6J s.2 orientation proof)",
            }
        elif arm == "ALW":
            direction = 1   # C2 always-in [DRAFT-CODE long-if convention]
            event_context = {"event_type": "C2_ALWAYS_IN", "signal_ignored": True}
        elif arm == "PLA":
            direction = fc.shadow_direction(session_date)
            event_context = {"event_type": "C1_CLOCK_ONLY_SHADOW",
                             "seed": fc.C1_SEED, "shadow_direction": direction}
        else:   # CLK — C3 weekday-matched non-event clock (MPM/MOF removed)
            if session_date in set(calendar.get("boj_mpm_dates", [])) | \
                    set(calendar.get("mof_disclosure_dates", [])):
                return fc.no_trade(head, "CLK_EVENT_DAY_MATCH")
            sig = self.signal(panel, calendar, session_date, asof)
            if sig.get("tail") is None:
                return fc.no_trade(head, sig.get("no_trade_reason") or "CLK_NO_BREAK")
            direction = 1 if sig["tail"] == "UP" else -1
            event_context = {"event_type": "C3_WEEKDAY_MATCHED_CLOCK"}

        return self._resolve_intent(head, panel, session_date, asof, parsed,
                                    direction, atr, event_context,
                                    cost_tier, cost_slip, stress)

    # ------------------------------------------------------------ internals
    def _resolve_intent(self, head, panel, session_date, asof, parsed, direction,
                        atr, event_context, cost_tier, cost_slip, stress) -> dict:
        bars = fc.session_bars(panel, session_date, upto=asof)
        if not bars:
            return fc.no_trade(head, "NO_BARS_UPTO_ASOF")
        last_dt = fc.session_last_dt(panel, session_date)
        if last_dt is None:
            return fc.no_trade(head, "SESSION_MASK_UNKNOWN")
        session_complete = bars[-1]["_dt"] >= last_dt

        trig_min = fc.local_minutes(fc.parse_ts(event_context["trigger_ts"]), TZ)
        entry_min = (trig_min + 1) + DELAY_MINUTES[parsed["delay"]]
        entry_bar = next((b for b in bars
                          if fc.local_minutes(b["_dt"], TZ) == entry_min), None)
        if entry_bar is None:
            return fc.no_trade(head, "ENTRY_BAR_ABSENT_UPTO_ASOF")
        entry_px = fc.round_to_tick(float(entry_bar["open"]), self.tick)
        sl_dist = SL_ATR_MULT * float(atr)
        if direction == 1:
            sl_px = fc.round_to_tick(entry_px - sl_dist, self.tick)
            tp_px = fc.round_to_tick(entry_px + TP_SL_MULT * sl_dist, self.tick)
        else:
            sl_px = fc.round_to_tick(entry_px + sl_dist, self.tick)
            tp_px = fc.round_to_tick(entry_px - TP_SL_MULT * sl_dist, self.tick)
        after = [b for b in bars if fc.local_minutes(b["_dt"], TZ) >= entry_min]
        exitres = fc.resolve_exit(after, entry_px, sl_px, tp_px,
                                  self.tick, session_complete)
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
            "quote_direction_law": fc.QUOTE_DIRECTION_6J,
        }


def _parse_identity(identity_id: str) -> dict:
    parts = identity_id.split("-")
    if len(parts) == 6 and parts[0] == fc.DRAFT_TOKEN_6J and parts[1] == "JF3":
        arm, tail, delay, tier = parts[2], parts[3], parts[4], parts[5]
        if arm not in ("CONT", "FADE"):
            raise ValueError(f"unknown JF3 arm {arm!r}")
        if tail not in ("UP", "DN"):
            raise ValueError(f"arm {arm} requires tail UP/DN")
        if tier != "S2":
            raise ValueError("CONV-B core tier is S2")
        return {"arm": arm, "tail": tail, "delay": delay, "tier": tier}
    if len(parts) == 3 and parts[0] == fc.DRAFT_TOKEN_6J and parts[2] == "JF3":
        if parts[1] not in ("PLA", "ALW", "CLK"):
            raise ValueError(f"unknown JF3 control {parts[1]!r}")
        return {"arm": parts[1], "tail": None, "delay": "D1", "tier": None}
    raise ValueError(f"identity {identity_id!r} does not match the JF3 draft grammar")
