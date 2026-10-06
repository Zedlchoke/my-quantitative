"""adapter — 6A-AF1 RBA DECISION-MINUTE REACTION (PROPOSED; CONTINGENCY-PB3-PARK).

Law text: ./FROZEN_RULE_DRAFT.md (PROPOSED — never an approved freeze; the 6A
adapters are CONTINGENCY machinery, NEVER activated while PB3 PARK stands).
Family: RBA ±5' decision reaction; arms AF1-DRIFT / AF1-REV; K0 thin-n kill
PRE-REGISTERED (CENSUS_FINAL s.1 AF1 row).
Sources: SPEC_6A_CONTINGENCY.md s.1-2 (tick-era law + NO-BACK-CAST), s.4
(RBA date-granularity + 14:30-Sydney DECLARED convention), s.7; CENSUS AF1
dossier; CALENDAR_PIT_POLICY s.4; COST_CONTRACT s.2-3; frozen 26-ID table
(identity_tables.json sha 1a96b8ea...).

Outcome-blind: synthetic fixtures only. Real-data paths refuse on the
P5-FXJA-D5 chain (PB3 lift + D8 + D9 + D2 + calendar). Era-1 windows refuse
trade intent (REFUSED_ERA1_DESCRIPTIVE_ONLY — refusal CODE, not a warning).
"""
from __future__ import annotations

from datetime import datetime

import fx_common as fc

FAMILY = "AF1"
SYMBOL = "6A"
TZ = fc.SYD
ANCHOR_LOCAL_MIN = 14 * 60 + 30        # 14:30 Sydney — DECLARED convention
WINDOW_START_MIN = ANCHOR_LOCAL_MIN
WINDOW_END_MIN = ANCHOR_LOCAL_MIN + 5  # ±5' window: bar starts [14:30, 14:35)
DECISION_LOCAL_MIN = WINDOW_END_MIN    # decision time = window close, 14:35 Syd
DELAY_MINUTES = {"D1": 0, "D30M": 30}
ATR_EVENT_PERIOD = 20
SL_ATR_MULT = 1.0
TP_SL_MULT = 2.0
TIME_EXIT_LOCAL_MIN = 17 * 60          # 17:00 Sydney [PROVISIONAL]
WINDOW_KEY = "rba"
CORE_IDS = fc.contingency_6a_ids("AF1")[:8]
CONTROL_IDS = fc.contingency_6a_ids("AF1")[8:]
DRAFT_IDS = CORE_IDS + CONTROL_IDS     # 8 + 3 = 11 contingency shapes (CONV-B)


def af1_freeze_check() -> dict:
    """CONTINGENCY activation gate: the frozen 26-ID table carries total = 0
    today; ANY nonzero count requires the P5-FXJA-D5 chain. Machinery only."""
    if fc.GUARDS["P5-FXJA-D5"] is None:
        raise fc.RefusedPendingOwnerDecision(
            "P5-FXJA-D5",
            "6A stays PB3 PARK: 0 budget, 0 identities (frozen 26-ID table, "
            "total 0 today); activation = PB3 lift -> D8 -> D9 -> D2 -> "
            "calendar (BLOCKED_PB3_PARK / BLOCKED_D8_UNRATIFIED)")
    return {"frozen_by": fc.GUARDS["P5-FXJA-D5"]}


class AF1Adapter:
    family = FAMILY
    symbol = SYMBOL

    def __init__(self, contract: dict | None = None):
        self.contract = contract or fc.load_fx_contract(SYMBOL)

    @property
    def tick(self) -> float:
        return self.contract["tick_size"]   # era-2 convenience; era read per session

    # ---------------------------------------------------------------- API
    def apply_exclusions(self, calendar: dict, panel: dict) -> dict:
        """AF1 base excludes: FOMC statement days + next-day spillover + the
        CALENDAR s.5 inventory (the measured US common factor on 6A is LARGER
        than RBA's: ±5' 8.2x vs 9.0x RBA)."""
        return fc.apply_fx_exclusions(calendar, panel, SYMBOL, exclude_fomc=True)

    def build_observables(self, panel: dict, calendar: dict) -> dict:
        fc.require_synthetic(panel, SYMBOL)
        fc.validate_panel(panel, SYMBOL)
        excl = self.apply_exclusions(calendar, panel)
        events = [d for d in calendar.get("rba_decision_dates", [])
                  if d in fc.session_map(panel)]
        out = {"anchor_law": ("14:30 Sydney DECLARED convention; the RBA table "
                              "carries DATES only — decision TIME is not carried "
                              "(CALENDAR_PIT_POLICY s.4)"),
               "era_law": fc.sixa_era_for_date.__doc__.split("\n")[0].strip(),
               "quote_direction": "USD per AUD; 6A UP = AUD stronger",
               "events": []}
        for sd in events:
            wb = fc.window_bars(panel, sd, TZ, WINDOW_START_MIN, WINDOW_END_MIN)
            if not wb:
                continue
            move = float(wb[-1]["close"]) - float(wb[0]["open"])
            out["events"].append({
                "date": sd, "era": fc.sixa_era_for_date(sd),
                "window_move": move,
                "tail": "UP" if move > 0 else ("DN" if move < 0 else None),
                "stratum": ("ERA1_DESCRIPTIVE_ONLY" if fc.sixa_era_for_date(sd) == "era1"
                            else "ERA2"),
                "excluded": sd in excl,
            })
        return out

    def signal(self, panel: dict, calendar: dict, session_date: str,
               asof: str | datetime | None = None) -> dict:
        """PIT signal: the ±5' signed move around the 14:30-Sydney anchor."""
        fc.require_synthetic(panel, SYMBOL)
        events = set(calendar.get("rba_decision_dates", []))
        base = {"family": FAMILY, "session_date": session_date,
                "anchor_law": "14:30 Syd declared convention (time NOT carried)",
                "era": fc.sixa_era_for_date(session_date),
                "fold_id": fc.fold_for_date(session_date)}
        if session_date not in events:
            return {**base, "event": False, "knowable": False, "tail": None,
                    "no_trade_reason": "NOT_RBA_EVENT_MEMBER"}
        decision_dt = fc.at_local(session_date, 14, 35, TZ)
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
                    "no_trade_reason": "WINDOW_BARS_ABSENT_UPTO_ASOF"}
        move = float(wb[-1]["close"]) - float(wb[0]["open"])
        tail = "UP" if move > 0 else ("DN" if move < 0 else None)
        return {**base, "event": True, "knowable": True,
                "decision_time": decision_dt.isoformat(),
                "window_move": move, "tail": tail,
                "no_trade_reason": None if tail else "TRIGGER_FLAT"}

    def order_intent(self, panel: dict, calendar: dict, identity_id: str,
                     session_date: str, asof: str | datetime | None = None,
                     cost_tier: str = "T1", cost_slip: str = "S1",
                     stress: float = 1.0) -> dict:
        """CONTINGENCY machinery. Era-1 windows REFUSE trade intent
        (REFUSED_ERA1_DESCRIPTIVE_ONLY — the no-back-cast law)."""
        fc.require_synthetic(panel, SYMBOL)
        if fc.sixa_era_for_date(session_date) == "era1":
            raise fc.RefusedEra1NoTradeIntent(
                f"{session_date} is an era-1 window (2020-01-02..2020-11-20, "
                f"$10.00/tick): descriptive-only stratum forever (AF4 K3); "
                f"era-2-calibrated cost models may NOT back-cast (SPEC_6A s.2); "
                f"era-aware scoring additionally sits behind P5-FXJA-D5")
        parsed = _parse_identity(identity_id)
        excl = self.apply_exclusions(calendar, panel)
        flags = excl.get(session_date, [])
        events = [d for d in calendar.get("rba_decision_dates", [])
                  if d in fc.session_map(panel) and fc.sixa_era_for_date(d) == "era2"]
        tick = fc.sixa_tick(session_date)
        atr = fc.window_atr20(panel, events, session_date, WINDOW_KEY)
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
        if arm in ("DRIFT", "REV"):
            sig = self.signal(panel, calendar, session_date, asof)
            if not sig.get("event"):
                return fc.no_trade(head, sig.get("no_trade_reason")
                                   or "NOT_RBA_EVENT_MEMBER")
            if not sig.get("knowable"):
                return fc.no_trade(head, "SIGNAL_NOT_KNOWABLE_AT_ASOF")
            if sig.get("tail") is None:
                return fc.no_trade(head, "TRIGGER_FLAT")
            if sig["tail"] != tail_id:
                return fc.no_trade(head, "TAIL_MISMATCH")
            trigger_dir = 1 if sig["tail"] == "UP" else -1   # 6A UP = AUD stronger
            direction = trigger_dir if arm == "DRIFT" else -trigger_dir
            event_context = {"event_type": "RBA_DECISION_1430_SYD_CONVENTION",
                             "decision_time": sig["decision_time"],
                             "window_move": sig["window_move"],
                             "surprise_classification": "NOT_RUN (weak "
                                                        "change-vs-hold proxy)"}
        elif arm == "ALW":
            if session_date not in set(calendar.get("rba_decision_dates", [])):
                return fc.no_trade(head, "ALW_NOT_EVENT_DAY")
            direction = 1
            event_context = {"event_type": "C2_ALWAYS_IN", "signal_ignored": True}
        elif arm == "PLA":
            if session_date in set(calendar.get("rba_decision_dates", [])):
                return fc.no_trade(head, "SHDW_EVENT_DAY_MATCH")
            direction = fc.shadow_direction(session_date)
            event_context = {"event_type": "C1_CLOCK_ONLY_SHADOW",
                             "seed": fc.C1_SEED, "shadow_direction": direction}
        else:   # CLK — C3 Tuesday-matched non-event clock (RBA days are Tuesdays)
            if session_date in set(calendar.get("rba_decision_dates", [])):
                return fc.no_trade(head, "CLK_EVENT_DAY_MATCH")
            sig = self.signal(panel, calendar, session_date, asof)
            direction = 1   # clock-only: no market read by law [DRAFT-CODE]
            event_context = {"event_type": "C3_TUESDAY_MATCHED_CLOCK",
                             "market_read": False}

        return self._resolve_intent(head, panel, session_date, asof, parsed,
                                    direction, atr, event_context,
                                    cost_tier, cost_slip, stress, tick)

    # ------------------------------------------------------------ internals
    def _resolve_intent(self, head, panel, session_date, asof, parsed, direction,
                        atr, event_context, cost_tier, cost_slip, stress,
                        tick) -> dict:
        bars = fc.session_bars(panel, session_date, upto=asof)
        if not bars:
            return fc.no_trade(head, "NO_BARS_UPTO_ASOF")
        last_dt = fc.session_last_dt(panel, session_date)
        session_complete = bool(bars) and bars[-1]["_dt"] >= last_dt
        entry_min = DECISION_LOCAL_MIN + DELAY_MINUTES[parsed["delay"]]
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
        after = [b for b in bars
                 if fc.local_minutes(b["_dt"], TZ) >= entry_min
                 and fc.local_minutes(b["_dt"], TZ) <= TIME_EXIT_LOCAL_MIN]
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
            "atr20_window": float(atr), **exitres,
            "event_context": event_context,
            "cost_preview": cost,
            "k0_structure": fc.fold_floor_check(23, 8),
        }


def consume_rba_decision_stamp(*_args, **_kwargs) -> None:
    """The RBA table carries DATES, not decision TIME (CALENDAR_PIT_POLICY
    s.4). Any verified-release-minute claim refuses; the 14:30-Sydney anchor
    stays a DECLARED convention (6A_DEEP s.4.1)."""
    raise fc.RefusedRbaTimeNotCarried(
        "the 14:30-Sydney anchor is a declared convention; the source file "
        "carries date granularity only")


def _parse_identity(identity_id: str) -> dict:
    parts = identity_id.split("-")
    if len(parts) == 7 and parts[0] == fc.CONTINGENCY_TOKEN_6A and parts[1] == "CONT":
        family, arm, tail, delay, tier = parts[2], parts[3], parts[4], parts[5], parts[6]
        if family != "AF1":
            raise ValueError(f"not an AF1 id: {identity_id!r}")
        if arm not in ("DRIFT", "REV"):
            raise ValueError(f"unknown AF1 arm {arm!r}")
        if tail not in ("UP", "DN"):
            raise ValueError(f"arm {arm} requires tail UP/DN")
        if tier != "S2":
            raise ValueError("CONV-B core tier is S2")
        return {"arm": arm, "tail": tail, "delay": delay, "tier": tier}
    if len(parts) == 4 and parts[0] == fc.CONTINGENCY_TOKEN_6A and parts[2] == "AF1":
        if parts[1] not in ("PLA", "ALW", "CLK"):
            raise ValueError(f"unknown AF1 control {parts[1]!r}")
        return {"arm": parts[1], "tail": None, "delay": "D1", "tier": None}
    raise ValueError(f"identity {identity_id!r} does not match the AF1 "
                     f"CONTINGENCY-PB3-PARK grammar")
