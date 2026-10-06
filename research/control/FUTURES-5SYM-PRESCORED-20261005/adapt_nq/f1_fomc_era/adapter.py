"""adapter — NQ-F1 FOMC-ERA (PROPOSED draft machinery; synthetic-only).

Law text: ./FROZEN_RULE_DRAFT.md (PROPOSED — never an approved freeze).
Family: FOMC statement-day reaction, era-conditioned; mechanisms M-NQ-CONT /
M-NQ-UNW. Pure functions over injected panels; no randomness, no wall-clock,
no real-data paths (provenance gate P5-NQ1). Outcome-blind: SIGNALS + intended
ORDER INTENT on synthetic fixtures only — never real-data PnL.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import nq_common as nc

FAMILY = "NQ-F1"
TRIGGER_WINDOW_BARS = 1          # [DRAFT-CODE] the release-minute bar (census F1 s.5)
ANCHOR_CT = "13:00"              # 14:00 ET statements == 13:00 CT
DELAYS = {"D0": 1, "D30": 31}    # minutes after the anchor bar start
ATR_PERIOD = 20
SL_ATR_MULT = 1.0
TP_SL_MULT = 2.0
CORE_IDS = nc.core_ids(FAMILY)
CONTROL_IDS = nc.control_ids(FAMILY)
DRAFT_IDS = CORE_IDS + CONTROL_IDS


def shadow_direction(session_date: str, seed: int = 20261002) -> int:
    """C1-class clock-only shadow: single-seed/single-delay law, seed 20261002,
    reading (a). Deterministic direction from (seed, session ordinal) — a
    [DRAFT-CODE] convention; the registered freeze would pin the C1 recipe."""
    d = nc._as_date(session_date)
    return 1 if (seed + d.toordinal()) % 2 == 0 else -1


def _ct(session_date: str, hhmm: str) -> datetime:
    return nc.parse_ts(f"{session_date}T{hhmm}:00{nc.ct_offset_str(session_date)}")


class FomcEraAdapter:
    family = FAMILY

    def __init__(self, contract: dict | None = None):
        self.contract = contract or nc.load_nq_contract()
        self.tick = self.contract["tick_size"]
        self.mult = self.contract["multiplier"]

    # ---------------------------------------------------------------- API
    def apply_exclusions(self, calendar: dict, panel: dict) -> dict:
        """F1-aware exclusion pass: H1..H5 fail-closed (NO FOMC day-level
        standing-outside flag — the timed statement days ARE this family's
        universe; the standing-outside law binds other families' base arms and
        is consumed by nq_common with include_fomc=True). F1 layers its own
        stratum flags: untimed statements (day-level law only, minute anatomy
        NOT_RUN) and non-14:00-ET timed stamps (EMERGENCY_TIMING)."""
        excl = nc.apply_exclusions_with_panel(calendar, panel, include_fomc=False)
        sessions = {s["session_date"] for s in panel["sessions"]}
        for r in calendar.get("fomc_statements", []):
            t = r.get("time_et")
            if r["date"] not in sessions:
                continue
            if t is None:
                excl.setdefault(r["date"], []).append("UNTIMED_DAY_LEVEL_ONLY")
            elif t != "14:00":
                excl.setdefault(r["date"], []).append("EMERGENCY_TIMING")
        return {k: sorted(set(v)) for k, v in excl.items()}

    def build_observables(self, panel: dict, calendar: dict) -> dict:
        nc.require_synthetic(panel)
        nc.validate_panel(panel)
        sessions = nc.session_map(panel)
        out = {"timed_events": [], "emergency_timing": [], "untimed": []}
        for r in calendar.get("fomc_statements", []):
            t = r.get("time_et")
            if t is None:
                out["untimed"].append({**r, "stratum": "UNTIMED_DAY_LEVEL_ONLY"})
            elif t != "14:00":
                out["emergency_timing"].append({**r, "stratum": "EMERGENCY_TIMING"})
        for r in calendar.get("fomc_statements", []):
            if r.get("time_et") != "14:00" or r["date"] not in sessions:
                continue
            sd = r["date"]
            out["timed_events"].append({
                "date": sd, "anchor_ct": ANCHOR_CT, "stratum": "TIMED_1400ET",
                "era_view": nc.k_views(sd),
                "atr20_points": nc.atr20_points(panel, sd, ATR_PERIOD),
                "fold_id": nc.fold_for_date(sd),
            })
        return out

    def signal(self, panel: dict, calendar: dict, session_date: str,
               asof: str | datetime | None = None) -> dict:
        """PIT signal state for a session at decision time `asof`."""
        nc.require_synthetic(panel)
        events = {r["date"] for r in calendar.get("fomc_statements", [])
                  if r.get("time_et") == "14:00"}
        base = {"family": FAMILY, "session_date": session_date,
                "era_view": nc.k_views(session_date),
                "fold_id": nc.fold_for_date(session_date)}
        if session_date not in events:
            return {**base, "event": False, "knowable": False, "tail": None,
                    "no_trade_reason": "NOT_EVENT_MEMBER"}
        anchor = _ct(session_date, ANCHOR_CT)
        decision_time = anchor + timedelta(minutes=TRIGGER_WINDOW_BARS)
        if asof is not None:
            a = asof if isinstance(asof, datetime) else nc.parse_ts(asof)
            if a < decision_time:
                return {**base, "event": True, "knowable": False, "tail": None,
                        "decision_time": decision_time.isoformat()}
        bars = nc.session_bars(panel, session_date, upto=asof)
        anchor_bar = next((b for b in bars
                           if nc.ct_minutes(b["_dt"]) == nc.ct_minutes(anchor)), None)
        if anchor_bar is None:
            return {**base, "event": True, "knowable": False, "tail": None,
                    "no_trade_reason": "ANCHOR_BAR_ABSENT_UPTO_ASOF"}
        move = float(anchor_bar["close"]) - float(anchor_bar["open"])
        tail = "UP" if move > 0 else ("DN" if move < 0 else None)
        return {**base, "event": True, "knowable": True,
                "decision_time": decision_time.isoformat(),
                "trigger_move_points": move, "tail": tail,
                "no_trade_reason": None if tail else "TRIGGER_FLAT"}

    def order_intent(self, panel: dict, calendar: dict, identity_id: str,
                     session_date: str, asof: str | datetime | None = None,
                     cost_tier: str = "S2", stress: float = 1.0) -> dict:
        """Intended ORDER INTENT (never an execution). asof=None resolves the
        full session from panel data (post-session resolution); any explicit
        asof restricts every read (PIT). Evaluation order: exclusions ->
        warmup -> arm routing -> fill/exit resolution."""
        nc.require_synthetic(panel)
        parsed = _parse_identity(identity_id)
        excl = self.apply_exclusions(calendar, panel)
        flags = excl.get(session_date, [])
        head = {
            "identity_id": identity_id, "family": FAMILY, "status": "INTENT",
            "session_date": session_date, "era_view": nc.k_views(session_date),
            "fold_id": nc.fold_for_date(session_date),
            "warmup_ok": nc.atr20_points(panel, session_date, ATR_PERIOD) is not None,
            "exclusion_flags": list(flags),
            "decision_slot_dependencies": nc.decision_slot_dependencies(),
            "contract": nc.session_map(panel).get(session_date, {}).get(
                "contract", panel.get("contract")),
            "tick_size": self.tick, "multiplier": self.mult,
        }
        if flags:
            return {**head, "no_trade": True,
                    "no_trade_reason": "EXCLUDED: " + ",".join(flags)}
        if not head["warmup_ok"]:
            return {**head, "no_trade": True, "no_trade_reason": "ATR_WARMUP_INSUFFICIENT"}
        if parsed["arm"] == "FLAT":
            return {**head, "no_trade": True, "no_trade_reason": "FLAT_ANCHOR_ZERO_TRADES"}

        if parsed["arm"] in ("CONT", "REV"):
            sig = self.signal(panel, calendar, session_date, asof)
            if not sig.get("event"):
                return {**head, "no_trade": True, "no_trade_reason": sig["no_trade_reason"]}
            if not sig.get("knowable"):
                return {**head, "no_trade": True,
                        "no_trade_reason": "SIGNAL_NOT_KNOWABLE_AT_ASOF"}
            if sig.get("tail") is None:
                return {**head, "no_trade": True, "no_trade_reason": "TRIGGER_FLAT"}
            if sig["tail"] != parsed["tail"]:
                return {**head, "no_trade": True, "no_trade_reason": "TAIL_MISMATCH"}
            trigger_dir = 1 if sig["tail"] == "UP" else -1
            direction = trigger_dir if parsed["arm"] == "CONT" else -trigger_dir
            event_context = {"event_type": "FOMC_STATEMENT", "event_time_et": "14:00",
                             "anchor_ct": ANCHOR_CT,
                             "trigger_move_points": sig["trigger_move_points"],
                             "trigger_window_bars": TRIGGER_WINDOW_BARS}
        elif parsed["arm"] == "ALW":
            # C2 always-on: in-event-window, signal ignored (direction +1 long-if
            # convention [DRAFT-CODE]); trades only on timed event days.
            sig = self.signal(panel, calendar, session_date, asof)
            if not sig.get("event"):
                return {**head, "no_trade": True, "no_trade_reason": "NOT_EVENT_MEMBER"}
            direction = 1
            event_context = {"event_type": "FOMC_STATEMENT", "event_time_et": "14:00",
                             "anchor_ct": ANCHOR_CT, "signal_ignored": True}
        else:  # SHDW
            # C1 clock-only shadow: matched non-FOMC 13:00-CT Wednesdays,
            # single-seed/single-delay (seed 20261002, reading (a)).
            if nc._as_date(session_date).weekday() != 2:
                return {**head, "no_trade": True, "no_trade_reason": "SHDW_NOT_WEDNESDAY"}
            if session_date in nc.fomc_day_set(calendar):
                return {**head, "no_trade": True, "no_trade_reason": "SHDW_FOMC_DAY_MATCH"}
            direction = shadow_direction(session_date)
            event_context = {"event_type": "CLOCK_ONLY_SHADOW", "anchor_ct": ANCHOR_CT,
                             "seed": 20261002, "shadow_direction": direction}

        if parsed["delay"] not in DELAYS:
            return {**head, "no_trade": True, "no_trade_reason": "UNSUPPORTED_DELAY"}
        atr = nc.atr20_points(panel, session_date, ATR_PERIOD)
        return self._resolve_intent(head, panel, session_date, asof, parsed,
                                    direction, atr, event_context, cost_tier, stress)

    # ------------------------------------------------------------ internals
    def _resolve_intent(self, head, panel, session_date, asof, parsed, direction,
                        atr, event_context, cost_tier, stress) -> dict:
        bars = nc.session_bars(panel, session_date, upto=asof)
        if not bars:
            return {**head, "no_trade": True, "no_trade_reason": "NO_BARS_UPTO_ASOF"}
        agg = nc.session_map(panel).get(session_date)
        last_start = (agg or {}).get("last_bar_ct")
        if last_start is None:
            return {**head, "no_trade": True, "no_trade_reason": "SESSION_MASK_UNKNOWN"}
        last_dt = _ct(session_date, last_start)
        partial = bars[-1]["_dt"] < last_dt
        if not partial and bars[-1]["_dt"] != last_dt:
            raise nc.RefusedSessionMaskMismatch(
                f"{session_date}: last bar {bars[-1]['_dt'].isoformat()} != measured "
                f"last_bar_ct {last_start}")

        entry_min = nc.ct_minutes(_ct(session_date, ANCHOR_CT)) + DELAYS[parsed["delay"]]
        entry_bar = next((b for b in bars if nc.ct_minutes(b["_dt"]) == entry_min), None)
        if entry_bar is None:
            return {**head, "no_trade": True, "no_trade_reason": "ENTRY_BAR_ABSENT_UPTO_ASOF"}
        entry_px = nc.round_to_tick(float(entry_bar["open"]), self.tick)
        sl_dist = SL_ATR_MULT * float(atr)
        if direction == 1:
            sl_px = nc.round_to_tick(entry_px - sl_dist, self.tick)
            tp_px = nc.round_to_tick(entry_px + TP_SL_MULT * sl_dist, self.tick)
        else:
            sl_px = nc.round_to_tick(entry_px + sl_dist, self.tick)
            tp_px = nc.round_to_tick(entry_px - TP_SL_MULT * sl_dist, self.tick)

        exit_px = exit_ts = exit_reason = None
        if not partial:
            for b in bars:
                if nc.ct_minutes(b["_dt"]) < entry_min:
                    continue
                lo, hi = float(b["low"]), float(b["high"])
                hit_sl = lo <= sl_px <= hi
                hit_tp = lo <= tp_px <= hi
                if hit_sl:  # same-bar TP/SL -> SL priority (conservative fill law)
                    exit_px, exit_reason, exit_ts = sl_px, "SL", b["_dt"]
                    break
                if hit_tp:
                    exit_px, exit_reason, exit_ts = tp_px, "TP", b["_dt"]
                    break
            if exit_px is None:
                last_bar = bars[-1]
                exit_px = nc.round_to_tick(float(last_bar["close"]), self.tick)
                exit_reason, exit_ts = "SESSION_CLOSE", last_bar["_dt"]

        cost = nc.cost_per_side_usd(cost_tier, stress)
        return {
            **head,
            "no_trade": False, "no_trade_reason": None,
            "arm": parsed["arm"], "tail": parsed["tail"], "delay": parsed["delay"],
            "side": "BUY" if direction == 1 else "SELL", "direction": direction,
            "quantity": 1,
            "order_type": "MARKET_NEXT_BAR_OPEN",
            "ts_entry": entry_bar["_dt"].isoformat(),
            "entry_ref_price": entry_px,
            "sl_price": sl_px, "tp_price": tp_px,
            "atr20_points": float(atr),
            "ts_exit": exit_ts.isoformat() if exit_ts is not None else None,
            "exit_ref_price": exit_px, "exit_reason": exit_reason,
            "exit_resolution": "RESOLVED" if exit_px is not None else "PENDING_UPTO_ASOF",
            "session_context": {
                "era": nc.era_for_date(session_date),
                "era_close_ct": nc.era_close_min(session_date),
                "last_bar_ct": last_start,
                "rth_core_coverage": nc.rth_core_coverage(panel, session_date),
            },
            "event_context": event_context,
            "k3_stratum": nc.k_views(session_date)["K-V4_covid_window"],
            "cost_preview": cost,
            "labels": ["SYNTHETIC FIXTURE", "PROPOSED DRAFT", "NO EXECUTION"],
        }


def _parse_identity(identity_id: str) -> dict:
    parts = identity_id.split("-")
    if len(parts) not in (3, 5, 6) or parts[0] != nc.DRAFT_TOKEN or parts[1] != "F1":
        raise ValueError(f"identity {identity_id!r} does not match the F1 draft grammar")
    if len(parts) == 6:                       # core: ARM-TAIL-DELAY-TIER
        arm, tail, delay, tier = parts[2], parts[3], parts[4], parts[5]
        if arm not in ("CONT", "REV"):
            raise ValueError(f"core grammar requires CONT/REV, got {arm!r}")
        if tail not in ("UP", "DN"):
            raise ValueError(f"arm {arm} requires tail UP/DN")
    elif len(parts) == 5:                     # control: ARM-DELAY-TIER (no tail)
        arm, tail, delay, tier = parts[2], None, parts[3], parts[4]
        if arm not in ("SHDW", "ALW"):
            raise ValueError(f"control grammar requires SHDW/ALW, got {arm!r}")
        if delay != "D0":
            raise ValueError("reading (a) controls are single-delay D0")
    else:                                     # FLAT anchor: no tail/delay/tier
        arm, tail, delay, tier = parts[2], None, None, None
        if arm != "FLAT":
            raise ValueError(f"3-part grammar is FLAT-only, got {arm!r}")
    if tier is not None and tier != "S2":
        raise ValueError("CONV-B core tier is S2")
    return {"arm": arm, "tail": tail, "delay": delay, "tier": tier}
