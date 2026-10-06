"""adapter — 6J-JF1 BoJ MPM DECISION-WINDOW (PROPOSED draft machinery; synthetic-only).

Law text: ./FROZEN_RULE_DRAFT.md (PROPOSED — never an approved freeze).
Family: BoJ MPM decision-window resolution; arms JF1-DRIFT / JF1-REV.
Sources: SPEC_6J.md s.2/s.3/s.6/s.7/s.8; CENSUS_5SYM.md JF1 dossier;
IDENTITY_BUDGET_6J.md s.2 (FB6J1-JF1-* enumeration); CALENDAR_PIT_POLICY
s.3 (BoJ dates knowable, intraday stamps NOT_IN_CORPUS -> window-convention
ONLY law); COST_CONTRACT_6J_6A s.1/s.4.

QUOTE-DIRECTION LAW (load-bearing): 6J is quoted USD per JPY; 6J UP = yen
STRONG. The window move and every arm sign are expressed in 6J PRICE terms.

Outcome-blind: SIGNALS + intended ORDER INTENT on synthetic fixtures only;
real-data paths refuse on P5-FXJA-D1 (owner 6J ceiling). No PnL exists here.
"""
from __future__ import annotations

from datetime import datetime

import fx_common as fc

FAMILY = "JF1"
SYMBOL = "6J"
TZ = fc.JST
# Window convention (declared, never a release time — BoJ stamps NOT_IN_CORPUS):
# 12:00-15:30 JST Tokyo-afternoon block; signal evaluated at window close.
WINDOW_START_MIN = 12 * 60            # 12:00 JST
WINDOW_END_MIN = 15 * 60 + 30         # 15:30 JST (exclusive as bar-start bound)
DECISION_LOCAL_MIN = WINDOW_END_MIN   # window close = decision time
# Delay law: D1 = the first 1m bar after the window close (+1-bar mandatory
# delay); D30M = +30 minutes. Entry fill = that bar's OPEN (conservative law).
DELAY_MINUTES = {"D1": 0, "D30M": 30}
ATR_EVENT_PERIOD = 20
SL_ATR_MULT = 1.0
TP_SL_MULT = 2.0
WINDOW_KEY = "mpm"                    # session-aggregate window_ranges key
CORE_IDS = fc.jf1_core_ids()
CONTROL_IDS = fc.jf_control_ids(FAMILY)
DRAFT_IDS = CORE_IDS + CONTROL_IDS    # 8 + 3 = 11 (CONV-B minimal, JF1 block)


def _entry_local_min(delay: str) -> int:
    return DECISION_LOCAL_MIN + DELAY_MINUTES[delay]


class JF1Adapter:
    family = FAMILY
    symbol = SYMBOL

    def __init__(self, contract: dict | None = None):
        self.contract = contract or fc.load_fx_contract(SYMBOL)
        self.tick = self.contract["tick_size"]
        self.mult = self.contract["multiplier"]

    # ---------------------------------------------------------------- API
    def apply_exclusions(self, calendar: dict, panel: dict) -> dict:
        """Fail-closed exclusion pass (CALENDAR_PIT_POLICY s.5 + JF1 universe
        law). MOF op days arrive as calendar['mof_op_days'] (a committed ex-post
        universe CUT, never a decision-time input); the 2026-07-30 unverified
        op-window arrives as calendar['unverified_op_windows'] and is excluded
        price-only-label law (never merged into any op set)."""
        out = fc.apply_fx_exclusions(calendar, panel, SYMBOL)
        for sd in calendar.get("unverified_op_windows", []):
            out.setdefault(sd, []).append("X_UNVERIFIED_OP_WINDOW_PRICE_ONLY")
        return {k: sorted(set(v)) for k, v in out.items()}

    def build_observables(self, panel: dict, calendar: dict) -> dict:
        """Window observables per MPM date (strict past at decision time):
        window open/close (6J price terms), move, tail, coverage, stratum."""
        fc.require_synthetic(panel, SYMBOL)
        fc.validate_panel(panel, SYMBOL)
        events = [d for d in calendar.get("boj_mpm_dates", [])
                  if d in fc.session_map(panel)]
        out = {"window_convention": ("12:00-15:30 JST declared window; BoJ "
                                     "intraday stamps NOT_IN_CORPUS (owner slot "
                                     "P5-HYPO-OD2); K3 ANCHOR_INSENSITIVE_AT_45MIN "
                                     "delivered (jf1_k3_anchor.json sha 235e0472...)"),
               "quote_direction": fc.QUOTE_DIRECTION_6J,
               "events": []}
        for sd in events:
            wb = fc.window_bars(panel, sd, TZ, WINDOW_START_MIN, WINDOW_END_MIN)
            if not wb:
                continue
            w_open, w_close = float(wb[0]["open"]), float(wb[-1]["close"])
            move = w_close - w_open
            tail = "UP" if move > 0 else ("DN" if move < 0 else None)
            regime = sd in set(calendar.get("boj_mpm_regime_change_dates", []))
            out["events"].append({
                "date": sd, "window_open": w_open, "window_close": w_close,
                "window_move": move, "tail": tail,
                "n_window_bars": len(wb),
                "stratum": "REGIME_CHANGE_DESCRIPTIVE_ONLY" if regime else "ORDINARY_MPM",
                "fold_id": fc.fold_for_date(sd),
            })
        return out

    def signal(self, panel: dict, calendar: dict, session_date: str,
               asof: str | datetime | None = None) -> dict:
        """PIT signal state for a session at decision time `asof`.

        The decision time is the WINDOW CLOSE (15:30 JST) — never a BoJ minute
        stamp (consuming one refuses at fc.consume_boj_intraday_stamp)."""
        fc.require_synthetic(panel, SYMBOL)
        events = set(calendar.get("boj_mpm_dates", []))
        base = {"family": FAMILY, "session_date": session_date,
                "window_law": "12:00-15:30 JST convention (stamps NOT_IN_CORPUS)",
                "quote_direction": fc.QUOTE_DIRECTION_6J,
                "fold_id": fc.fold_for_date(session_date)}
        if session_date not in events:
            return {**base, "event": False, "knowable": False, "tail": None,
                    "no_trade_reason": "NOT_MPM_EVENT_MEMBER"}
        decision_dt = fc.at_local(session_date, 15, 30, TZ)
        if asof is not None:
            a = asof if isinstance(asof, datetime) else fc.parse_ts(asof)
            if a < decision_dt:
                return {**base, "event": True, "knowable": False, "tail": None,
                        "decision_time": decision_dt.isoformat(),
                        "no_trade_reason": "SIGNAL_NOT_KNOWABLE_AT_ASOF"}
        wb = fc.window_bars(panel, session_date, TZ,
                            WINDOW_START_MIN, WINDOW_END_MIN, upto=asof)
        if not wb:
            return {**base, "event": True, "knowable": False, "tail": None,
                    "decision_time": decision_dt.isoformat(),
                    "no_trade_reason": "WINDOW_BARS_ABSENT_UPTO_ASOF"}
        w_open, w_close = float(wb[0]["open"]), float(wb[-1]["close"])
        move = w_close - w_open
        tail = "UP" if move > 0 else ("DN" if move < 0 else None)
        return {**base, "event": True, "knowable": True,
                "decision_time": decision_dt.isoformat(),
                "window_open": w_open, "window_close": w_close,
                "window_move": move, "tail": tail,
                "no_trade_reason": None if tail else "TRIGGER_FLAT"}

    def order_intent(self, panel: dict, calendar: dict, identity_id: str,
                     session_date: str, asof: str | datetime | None = None,
                     cost_tier: str = "T1", cost_slip: str = "S1",
                     stress: float = 1.0) -> dict:
        """Intended ORDER INTENT (never an execution). Identity grammar:
        cores FB6J1-JF1-{DRIFT,REV}-{UP,DN}-{D1,D30M}-S2; controls
        FB6J1-{PLA,ALW,CLK}-JF1. Evaluation order: exclusions -> warmup ->
        arm routing (6J price-term signs) -> conservative fill/exit."""
        fc.require_synthetic(panel, SYMBOL)
        parsed = _parse_identity(identity_id)
        excl = self.apply_exclusions(calendar, panel)
        flags = excl.get(session_date, [])
        event_dates = [d for d in calendar.get("boj_mpm_dates", [])
                       if d in fc.session_map(panel)]
        atr = fc.window_atr20(panel, event_dates, session_date, WINDOW_KEY)
        head = fc.intent_head(FAMILY, identity_id, session_date, panel, {
            "warmup_ok": atr is not None,
            "exclusion_flags": list(flags),
            "tick_size": self.tick, "multiplier": self.mult,
            "contract": fc.session_map(panel).get(session_date, {}).get("contract"),
            "quote_direction": fc.QUOTE_DIRECTION_6J,
            "delay_supported": parsed.get("delay") in DELAY_MINUTES,
        })
        if flags:
            return fc.no_trade(head, "EXCLUDED: " + ",".join(flags))
        if not head["warmup_ok"]:
            return fc.no_trade(head, "ATR_WARMUP_INSUFFICIENT")
        if parsed["delay"] is not None and parsed["delay"] not in DELAY_MINUTES:
            return fc.no_trade(head, "UNSUPPORTED_DELAY")

        arm, tail_id = parsed["arm"], parsed["tail"]
        if arm in ("DRIFT", "REV"):
            sig = self.signal(panel, calendar, session_date, asof)
            if not sig.get("event"):
                return fc.no_trade(head, sig.get("no_trade_reason")
                                   or "NOT_MPM_EVENT_MEMBER")
            if not sig.get("knowable"):
                return fc.no_trade(head, "SIGNAL_NOT_KNOWABLE_AT_ASOF")
            if sig.get("tail") is None:
                return fc.no_trade(head, "TRIGGER_FLAT")
            if sig["tail"] != tail_id:
                return fc.no_trade(head, "TAIL_MISMATCH")
            trigger_dir = 1 if sig["tail"] == "UP" else -1   # 6J price terms
            direction = trigger_dir if arm == "DRIFT" else -trigger_dir
            event_context = {
                "event_type": "BOJ_MPM_WINDOW_CONVENTION",
                "window_jst": "12:00-15:30",
                "decision_time": sig["decision_time"],
                "window_move": sig["window_move"],
                "sign_law": "6J UP = yen STRONG (SPEC_6J s.2 orientation proof)",
            }
        elif arm == "ALW":
            # C2 always-in-window on ALL non-event days: direction +1 [DRAFT-CODE
            # long-if convention]; trades only on non-excluded non-event days.
            if session_date in set(calendar.get("boj_mpm_dates", [])):
                return fc.no_trade(head, "ALW_NOT_NON_EVENT_DAY")
            direction = 1
            event_context = {"event_type": "C2_ALWAYS_IN_WINDOW", "signal_ignored": True}
        elif arm == "PLA":
            # C1 clock-only shadow at identical window times on matched
            # non-event days (single-seed/single-delay, seed 20261002).
            if session_date in set(calendar.get("boj_mpm_dates", [])):
                return fc.no_trade(head, "SHDW_EVENT_DAY_MATCH")
            direction = fc.shadow_direction(session_date)
            event_context = {"event_type": "C1_CLOCK_ONLY_SHADOW",
                             "seed": fc.C1_SEED, "shadow_direction": direction}
        else:  # CLK — C3 weekday-matched non-event clock (family negative):
            # trades the SAME clock on weekday-matched non-event days with the
            # day's own window-move sign (a clock-conditioned negative).
            if session_date in set(calendar.get("boj_mpm_dates", [])):
                return fc.no_trade(head, "CLK_EVENT_DAY_MATCH")
            sig = self.signal(panel, calendar, session_date, asof)
            if sig.get("tail") is None:
                return fc.no_trade(head, "CLK_WINDOW_FLAT")
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

        entry_min = _entry_local_min(parsed["delay"])
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

        after = [b for b in bars
                 if fc.local_minutes(b["_dt"], TZ) >= entry_min]
        exitres = fc.resolve_exit(after, entry_px, sl_px, tp_px,
                                  self.tick, session_complete)
        # Tokyo-window entry fills carry the +1-tick entry-side session floor
        # (PROVISIONAL, JF1-7) — declared cost surface, never a fill claim.
        cost = fc.cost_per_side_usd(SYMBOL, session_date, cost_tier, cost_slip,
                                    stress, session_floor=True)
        return {
            **head,
            "no_trade": False, "no_trade_reason": None,
            "arm": parsed["arm"], "tail": parsed["tail"], "delay": parsed["delay"],
            "side": "BUY" if direction == 1 else "SELL", "direction": direction,
            "quantity": 1, "order_type": "MARKET_NEXT_BAR_OPEN",
            "decision_time": event_context.get("decision_time"),
            "ts_entry": entry_bar["_dt"].isoformat(),
            "entry_ref_price": entry_px,
            "sl_price": sl_px, "tp_price": tp_px,
            "atr20_window": float(atr),
            **exitres,
            "event_context": event_context,
            "cost_preview": cost,
            "quote_direction_law": fc.QUOTE_DIRECTION_6J,
        }


def _parse_identity(identity_id: str) -> dict:
    parts = identity_id.split("-")
    if len(parts) == 6 and parts[0] == fc.DRAFT_TOKEN_6J and parts[1] == "JF1":
        arm, tail, delay, tier = parts[2], parts[3], parts[4], parts[5]
        if arm not in ("DRIFT", "REV"):
            raise ValueError(f"unknown JF1 arm {arm!r}")
        if tail not in ("UP", "DN"):
            raise ValueError(f"arm {arm} requires tail UP/DN")
        if tier != "S2":
            raise ValueError("CONV-B core tier is S2")
        return {"arm": arm, "tail": tail, "delay": delay, "tier": tier}
    if len(parts) == 3 and parts[0] == fc.DRAFT_TOKEN_6J and parts[2] == "JF1":
        if parts[1] not in ("PLA", "ALW", "CLK"):
            raise ValueError(f"unknown JF1 control {parts[1]!r}")
        return {"arm": parts[1], "tail": None, "delay": "D1", "tier": None}
    raise ValueError(f"identity {identity_id!r} does not match the JF1 draft grammar")
