"""adapter — NQ-F2 MACRO-0730 (PROPOSED draft machinery; synthetic-only).

Law text: ./FROZEN_RULE_DRAFT.md (PROPOSED — never an approved freeze).
Family: 08:30-ET US print (BLS CPI core) discharge into the pre-RTH thin book;
mechanism M-NQ-MS, arms CONT vs REV on the 07:30-CT release-minute realized
sign. BLS first-published-vintage law (current-calendar inference forbidden);
D5 pin refusal; scoring-era confinement 2023-01-01..2026-09-30 (committed K6
anatomy law). Pure, deterministic, synthetic-only (P5-NQ1 provenance gate).
"""
from __future__ import annotations

from datetime import datetime, timedelta

import nq_common as nc

FAMILY = "NQ-F2"
ANCHOR_CT = "07:30"              # 08:30 ET embargo == 07:30 CT
TRIGGER_WINDOW_BARS = 1          # [DRAFT-CODE] the release-minute bar
DELAYS = {"D0": 1, "D30": 31}    # minutes after the anchor bar start
ATR_PERIOD = 20
SL_ATR_MULT = 1.0
TP_SL_MULT = 2.0
SCORE_ERA = ("2023-01-01", "2026-09-30")   # committed K6 scoring-era confinement
CORE_SERIES = "CPI"              # CONV-B minimal core is CPI-only (budget s.1)
D5_PIN_DATE = "2026-02-13"       # RC-3.4 measured law
CORE_IDS = nc.core_ids(FAMILY)
CONTROL_IDS = nc.control_ids(FAMILY)
DRAFT_IDS = CORE_IDS + CONTROL_IDS


def shadow_direction(session_date: str, seed: int = 20261002) -> int:
    """C1-class single-seed law (reading (a)) — same convention as F1."""
    d = nc._as_date(session_date)
    return 1 if (seed + d.toordinal()) % 2 == 0 else -1


def _ct(session_date: str, hhmm: str) -> datetime:
    return nc.parse_ts(f"{session_date}T{hhmm}:00{nc.ct_offset_str(session_date)}")


def vintage_row_for(calendar: dict, series: str, session_date: str) -> dict | None:
    """BLS vintage law: the row KNOWN at the decision date. A row with
    known_by > session_date does not exist at decision time (current-calendar
    inference forbidden) and never qualifies."""
    for r in nc.bls_rows_for(calendar, series):
        if (r.get("scheduled_date") == session_date
                and str(r.get("known_by", "9999-12-31")) <= session_date):
            return r
    return None


class Macro0730Adapter:
    family = FAMILY

    def __init__(self, contract: dict | None = None):
        self.contract = contract or nc.load_nq_contract()
        self.tick = self.contract["tick_size"]
        self.mult = self.contract["multiplier"]

    # ---------------------------------------------------------------- API
    def apply_exclusions(self, calendar: dict, panel: dict) -> dict:
        """Base-arm pass: H1..H5 + FOMC standing-outside (F2's release days are
        NOT the FOMC universe — a CPI day that is also a statement day is
        excluded)."""
        return nc.apply_exclusions_with_panel(calendar, panel, include_fomc=True)

    def build_observables(self, panel: dict, calendar: dict) -> dict:
        nc.require_synthetic(panel)
        nc.validate_panel(panel)
        if self._panel_touches_2026(panel):
            nc.require_d5_pin(calendar)
        scheduled, canceled, late_vintage = [], [], []
        sessions = {s["session_date"] for s in panel["sessions"]}
        for r in calendar.get("bls_vintage", []):
            sd = r.get("scheduled_date")
            if sd not in sessions:
                continue
            if str(r.get("known_by", "9999-12-31")) > sd:
                late_vintage.append({**r, "stratum": "VINTAGE_UNKNOWN_AT_D"})
            elif r.get("status") == "canceled":
                canceled.append({**r, "stratum": "CANCELED_CONTROL"})
            elif r.get("series") == CORE_SERIES:
                scheduled.append({**r, "stratum": "SCHEDULED_RELEASE",
                                  "anchor_ct": ANCHOR_CT,
                                  "era_view": nc.k_views(sd),
                                  "in_score_era": self._in_score_era(sd),
                                  "atr20_points": nc.atr20_points(panel, sd, ATR_PERIOD),
                                  "fold_id": nc.fold_for_date(sd)})
        return {"scheduled_releases": scheduled, "canceled_control": canceled,
                "vintage_unknown_at_decision_date": late_vintage,
                "score_era": list(SCORE_ERA), "core_series": CORE_SERIES}

    def signal(self, panel: dict, calendar: dict, session_date: str,
               asof: str | datetime | None = None) -> dict:
        """PIT signal state: vintage-correct release membership + anchor-bar
        realized sign, knowable only from 07:31 CT."""
        nc.require_synthetic(panel)
        base = {"family": FAMILY, "session_date": session_date,
                "era_view": nc.k_views(session_date),
                "fold_id": nc.fold_for_date(session_date),
                "in_score_era": self._in_score_era(session_date)}
        row = vintage_row_for(calendar, CORE_SERIES, session_date)
        if row is None:
            return {**base, "event": False, "knowable": False, "tail": None,
                    "no_trade_reason": "NOT_EVENT_MEMBER"}
        if row.get("status") == "canceled":
            return {**base, "event": True, "knowable": True, "tail": None,
                    "stratum": "CANCELED_CONTROL",
                    "no_trade_reason": "CANCELED_CONTROL_STRATUM"}
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
        """Intended ORDER INTENT. Evaluation order: provenance -> D5 pin ->
        exclusions (H1..H5 + FOMC) -> release-membership routing (vintage law;
        canceled stratum) -> era gate -> warmup -> arm routing -> fills."""
        nc.require_synthetic(panel)
        if self._panel_touches_2026(panel):
            nc.require_d5_pin(calendar)
        parsed = _parse_identity(identity_id)
        excl = self.apply_exclusions(calendar, panel)
        flags = list(excl.get(session_date, []))
        head = {
            "identity_id": identity_id, "family": FAMILY, "status": "INTENT",
            "session_date": session_date, "era_view": nc.k_views(session_date),
            "fold_id": nc.fold_for_date(session_date),
            "warmup_ok": nc.atr20_points(panel, session_date, ATR_PERIOD) is not None,
            "in_score_era": self._in_score_era(session_date),
            "exclusion_flags": flags,
            "decision_slot_dependencies": nc.decision_slot_dependencies(),
            "contract": nc.session_map(panel).get(session_date, {}).get(
                "contract", panel.get("contract")),
            "tick_size": self.tick, "multiplier": self.mult,
        }
        if flags:
            return {**head, "no_trade": True,
                    "no_trade_reason": "EXCLUDED: " + ",".join(flags)}
        row = vintage_row_for(calendar, CORE_SERIES, session_date)
        canceled = row is not None and row.get("status") == "canceled"
        if canceled:
            return {**head, "no_trade": True,
                    "no_trade_reason": "CANCELED_CONTROL_STRATUM"}
        if not head["in_score_era"]:
            return {**head, "no_trade": True, "no_trade_reason": "ERA_GATED"}
        if not head["warmup_ok"]:
            return {**head, "no_trade": True, "no_trade_reason": "ATR_WARMUP_INSUFFICIENT"}
        if parsed["arm"] == "FLAT":
            return {**head, "no_trade": True, "no_trade_reason": "FLAT_ANCHOR_ZERO_TRADES"}

        if parsed["arm"] in ("CONT", "REV"):
            sig = self.signal(panel, calendar, session_date, asof)
            if not sig.get("event") or sig.get("stratum") == "CANCELED_CONTROL":
                return {**head, "no_trade": True, "no_trade_reason": "NOT_EVENT_MEMBER"}
            if not sig.get("knowable"):
                return {**head, "no_trade": True,
                        "no_trade_reason": "SIGNAL_NOT_KNOWABLE_AT_ASOF"}
            if sig.get("tail") is None:
                return {**head, "no_trade": True, "no_trade_reason": "TRIGGER_FLAT"}
            if sig["tail"] != parsed["tail"]:
                return {**head, "no_trade": True, "no_trade_reason": "TAIL_MISMATCH"}
            trigger_dir = 1 if sig["tail"] == "UP" else -1
            direction = trigger_dir if parsed["arm"] == "CONT" else -trigger_dir
            event_context = {"event_type": "BLS_RELEASE", "series": CORE_SERIES,
                             "anchor_ct": ANCHOR_CT,
                             "trigger_move_points": sig["trigger_move_points"],
                             "vintage_known_by": row.get("known_by"),
                             "trigger_window_bars": TRIGGER_WINDOW_BARS}
        elif parsed["arm"] == "ALW":
            if row is None:
                return {**head, "no_trade": True, "no_trade_reason": "NOT_EVENT_MEMBER"}
            direction = 1
            event_context = {"event_type": "BLS_RELEASE", "series": CORE_SERIES,
                             "anchor_ct": ANCHOR_CT, "signal_ignored": True}
        else:  # SHDW — NC-6 non-release 07:30 clock
            if row is not None:
                return {**head, "no_trade": True, "no_trade_reason": "SHDW_ON_RELEASE_DAY"}
            direction = shadow_direction(session_date)
            event_context = {"event_type": "CLOCK_ONLY_SHADOW", "anchor_ct": ANCHOR_CT,
                             "seed": 20261002, "shadow_direction": direction}

        if parsed["delay"] not in DELAYS:
            return {**head, "no_trade": True, "no_trade_reason": "UNSUPPORTED_DELAY"}
        atr = nc.atr20_points(panel, session_date, ATR_PERIOD)
        return self._resolve_intent(head, panel, session_date, asof, parsed,
                                    direction, atr, event_context, cost_tier, stress)

    # ------------------------------------------------------------ internals
    def _in_score_era(self, session_date: str) -> bool:
        a, b = SCORE_ERA
        return a <= session_date <= b

    def _panel_touches_2026(self, panel: dict) -> bool:
        return any(s["session_date"] >= "2026-01-01" for s in panel["sessions"])

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
                if lo <= sl_px <= hi:   # same-bar TP/SL -> SL priority
                    exit_px, exit_reason, exit_ts = sl_px, "SL", b["_dt"]
                    break
                if lo <= tp_px <= hi:
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
    if len(parts) not in (3, 5, 6) or parts[0] != nc.DRAFT_TOKEN or parts[1] != "F2":
        raise ValueError(f"identity {identity_id!r} does not match the F2 draft grammar")
    if len(parts) == 6:
        arm, tail, delay, tier = parts[2], parts[3], parts[4], parts[5]
        if arm not in ("CONT", "REV"):
            raise ValueError(f"core grammar requires CONT/REV, got {arm!r}")
        if tail not in ("UP", "DN"):
            raise ValueError(f"arm {arm} requires tail UP/DN")
    elif len(parts) == 5:
        arm, tail, delay, tier = parts[2], None, parts[3], parts[4]
        if arm not in ("SHDW", "ALW"):
            raise ValueError(f"control grammar requires SHDW/ALW, got {arm!r}")
        if delay != "D0":
            raise ValueError("reading (a) controls are single-delay D0")
    else:
        arm, tail, delay, tier = parts[2], None, None, None
        if arm != "FLAT":
            raise ValueError(f"3-part grammar is FLAT-only, got {arm!r}")
    if tier is not None and tier != "S2":
        raise ValueError("CONV-B core tier is S2")
    return {"arm": arm, "tail": tail, "delay": delay, "tier": tier}
