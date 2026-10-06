"""adapter — NQ-F3 RUN-REV-NQ (PROPOSED draft machinery; synthetic-only).

Law text: ./FROZEN_RULE_DRAFT.md (PROPOSED — never an approved freeze).
Family: horizon-dependent daily-close reversion; k=5 same-sign run trigger on
the held daily series; arms REV (fade) vs CONT (trend competitor); single D0
delay; fixed 5-held-session horizon exit; roll-cross refusal per the
spread-adjustment chain law.

Full-era rebuild precondition harness (referenced, NOT duplicated):
  research/control/FUTURES-K6GATE-PREP-20261004/nq/k6_compute_m34.py
  research/control/FUTURES-K6GATE-PREP-20261004/nq/nq_f3_rebuild_a1a2.json
  (rebuilt ret series == nq_held_daily_v3, max diff 0.0, n=4,218).

Pure, deterministic, synthetic-only (P5-NQ1 provenance gate).
"""
from __future__ import annotations

from datetime import datetime, timedelta

import nq_common as nc

FAMILY = "NQ-F3"
K_RUN = 5                      # [DRAFT-CODE/PROVISIONAL] census F3 s.5
EXIT_HORIZON_SESSIONS = 5      # [DRAFT-CODE] fixed k-day horizon (T4 class)
CORE_IDS = nc.core_ids(FAMILY)
CONTROL_IDS = nc.control_ids(FAMILY)
DRAFT_IDS = CORE_IDS + CONTROL_IDS


def shadow_direction(session_date: str, seed: int = 20261002) -> int:
    d = nc._as_date(session_date)
    return 1 if (seed + d.toordinal()) % 2 == 0 else -1


def held_series(panel: dict, asof: str | datetime | None = None) -> list[dict]:
    """Held daily series (date, open, close), strictly ordered, optionally
    truncated to sessions whose date <= asof.date()."""
    cut = None
    if asof is not None:
        d = asof if isinstance(asof, datetime) else nc.parse_ts(asof)
        cut = d.date()
    out = []
    for s in sorted(panel["sessions"], key=lambda x: x["session_date"]):
        if cut is not None and nc._as_date(s["session_date"]) > cut:
            continue
        out.append({"session_date": s["session_date"], "open": float(s["open"]),
                    "close": float(s["close"])})
    return out


def run_lengths(panel: dict, asof: str | datetime | None = None) -> dict:
    """run_len(t) = consecutive same-sign close-to-close returns ending at t."""
    series = held_series(panel, asof)
    out: dict[str, int] = {}
    prev_sign = 0
    run = 0
    last_close = None
    for row in series:
        if last_close is None:
            out[row["session_date"]] = 0
            last_close = row["close"]
            continue
        ret = row["close"] - last_close
        sign = 1 if ret > 0 else (-1 if ret < 0 else 0)
        run = run + 1 if sign != 0 and sign == prev_sign else (1 if sign != 0 else 0)
        prev_sign = sign if sign != 0 else prev_sign
        out[row["session_date"]] = run
        last_close = row["close"]
    return out


def trigger_at(panel: dict, session_date: str,
               asof: str | datetime | None = None) -> dict:
    """First-crossing trigger: run_len(t) >= K and run_len(t-1) < K."""
    rl = run_lengths(panel, asof)
    dates = sorted(rl)
    if session_date not in rl:
        return {"trigger": False, "reason": "SESSION_NOT_IN_PANEL"}
    i = dates.index(session_date)
    cur, prev = rl[session_date], (rl[dates[i - 1]] if i > 0 else 0)
    if cur >= K_RUN and prev < K_RUN:
        return {"trigger": True, "run_len": cur,
                "tail": "UP" if prev_sign_of(panel, session_date) > 0 else "DN"}
    return {"trigger": False, "reason": "NO_TRIGGER",
            "run_len": cur, "prev_run_len": prev}


def prev_sign_of(panel: dict, session_date: str) -> int:
    """Sign of the returns making up the run ending at session_date."""
    series = held_series(panel)
    dates = [r["session_date"] for r in series]
    i = dates.index(session_date)
    if i < 1:
        return 0
    ret = series[i]["close"] - series[i - 1]["close"]
    return 1 if ret > 0 else (-1 if ret < 0 else 0)


def _parse_identity(identity_id: str) -> dict:
    parts = identity_id.split("-")
    if len(parts) not in (3, 5, 6) or parts[0] != nc.DRAFT_TOKEN or parts[1] != "F3":
        raise ValueError(f"identity {identity_id!r} does not match the F3 draft grammar")
    if len(parts) == 6:
        arm, tail, delay, tier = parts[2], parts[3], parts[4], parts[5]
        if arm not in ("CONT", "REV"):
            raise ValueError(f"core grammar requires CONT/REV, got {arm!r}")
        if tail not in ("UP", "DN"):
            raise ValueError(f"arm {arm} requires tail UP/DN")
        if delay != "D0":
            raise ValueError("F3 minimal core is single-delay D0")
    elif len(parts) == 5:
        arm, tail, delay, tier = parts[2], None, parts[3], parts[4]
        if arm not in ("SHDW", "ALW"):
            raise ValueError(f"control grammar requires SHDW/ALW, got {arm!r}")
    else:
        arm, tail, delay, tier = parts[2], None, None, None
        if arm != "FLAT":
            raise ValueError(f"3-part grammar is FLAT-only, got {arm!r}")
    if tier is not None and tier != "S2":
        raise ValueError("CONV-B core tier is S2")
    return {"arm": arm, "tail": tail, "delay": delay, "tier": tier}


class RunRevAdapter:
    family = FAMILY

    def __init__(self, contract: dict | None = None):
        self.contract = contract or nc.load_nq_contract()
        self.tick = self.contract["tick_size"]
        self.mult = self.contract["multiplier"]

    # ---------------------------------------------------------------- API
    def apply_exclusions(self, calendar: dict, panel: dict) -> dict:
        return nc.apply_exclusions_with_panel(calendar, panel, include_fomc=True)

    def build_observables(self, panel: dict, calendar: dict) -> dict:
        nc.require_synthetic(panel)
        nc.validate_panel(panel)
        rl = run_lengths(panel)
        triggers = [d for d in sorted(rl)
                    if trigger_at(panel, d)["trigger"]]
        return {
            "held_sessions": len(panel["sessions"]),
            "roll_switch_dates": [r["switch_date"] for r in panel.get("rolls", [])],
            "run_len_last": rl[sorted(rl)[-1]] if rl else 0,
            "triggers": [{"session_date": d, "tail": trigger_at(panel, d)["tail"],
                          "k3_stratum": nc.k_views(d)["K-V4_covid_window"],
                          "fold_id": nc.fold_for_date(d)} for d in triggers],
            "rebuild_precondition_reference":
                "FUTURES-K6GATE-PREP-20261004/nq/nq_f3_rebuild_a1a2.json "
                "(ret == nq_held_daily_v3, max diff 0.0, n=4218) — referenced, "
                "not duplicated",
        }

    def signal(self, panel: dict, calendar: dict, session_date: str,
               asof: str | datetime | None = None) -> dict:
        """PIT trigger state at session_date (knowable at that session's close)."""
        nc.require_synthetic(panel)
        base = {"family": FAMILY, "session_date": session_date,
                "era_view": nc.k_views(session_date),
                "fold_id": nc.fold_for_date(session_date)}
        sm = nc.session_map(panel)
        agg = sm.get(session_date)
        if agg is None:
            return {**base, "trigger": False, "knowable": False,
                    "no_trade_reason": "SESSION_NOT_IN_PANEL"}
        close_time = nc.parse_ts(f"{session_date}T{agg['last_bar_ct']}:00"
                                 + nc.ct_offset_str(session_date)) + timedelta(minutes=1)
        if asof is not None:
            a = asof if isinstance(asof, datetime) else nc.parse_ts(asof)
            if a < close_time:
                return {**base, "trigger": False, "knowable": False,
                        "session_close_time": close_time.isoformat()}
        trig = trigger_at(panel, session_date, asof=asof)
        return {**base, "knowable": True, "session_close_time": close_time.isoformat(),
                "k3_stratum": nc.k_views(session_date)["K-V4_covid_window"], **trig}

    def order_intent(self, panel: dict, calendar: dict, identity_id: str,
                     session_date: str, asof: str | datetime | None = None,
                     cost_tier: str = "S2", stress: float = 1.0) -> dict:
        """Intended ORDER INTENT off the trigger session `session_date`.
        Evaluation order: provenance -> trigger -> entry-session exclusions ->
        roll law -> horizon -> arm routing -> fills."""
        nc.require_synthetic(panel)
        parsed = _parse_identity(identity_id)
        head = {
            "identity_id": identity_id, "family": FAMILY, "status": "INTENT",
            "trigger_session": session_date,
            "era_view": nc.k_views(session_date),
            "fold_id": nc.fold_for_date(session_date),
            "k3_stratum": nc.k_views(session_date)["K-V4_covid_window"],
            "decision_slot_dependencies": nc.decision_slot_dependencies(),
            "tick_size": self.tick, "multiplier": self.mult,
            "contract": nc.session_map(panel).get(session_date, {}).get(
                "contract", panel.get("contract")),
        }
        if parsed["arm"] == "FLAT":
            return {**head, "no_trade": True, "no_trade_reason": "FLAT_ANCHOR_ZERO_TRADES"}

        sig = self.signal(panel, calendar, session_date, asof)
        if sig.get("SESSION_NOT_IN_PANEL") or sig.get("no_trade_reason"):
            return {**head, "no_trade": True,
                    "no_trade_reason": sig.get("no_trade_reason", "SESSION_NOT_IN_PANEL")}
        if not sig.get("knowable"):
            return {**head, "no_trade": True, "no_trade_reason": "SIGNAL_NOT_KNOWABLE_AT_ASOF"}
        tail = sig.get("tail")

        # arm routing BEFORE any price resolution
        if parsed["arm"] == "SHDW":
            # clock-only shadow: identical entry/exit/holding machinery driven
            # purely by the clock on matched NO-SIGNAL sessions (C1 class,
            # single-seed/single-delay, seed 20261002, reading (a))
            if sig.get("trigger"):
                return {**head, "no_trade": True, "no_trade_reason": "SHDW_ON_SIGNAL_SESSION"}
            direction = shadow_direction(session_date)
            event_context = {"event_type": "CLOCK_ONLY_SHADOW", "seed": 20261002,
                             "shadow_direction": direction}
        elif parsed["arm"] == "ALW":
            # C2 always-in-window: trades the trigger session, signal ignored
            if not sig.get("trigger"):
                return {**head, "no_trade": True, "no_trade_reason": "NO_TRIGGER"}
            direction = 1
            event_context = {"event_type": "ALWAYS_IN", "signal_ignored": True,
                             "tail": tail}
        else:  # CONT / REV
            if not sig.get("trigger"):
                return {**head, "no_trade": True, "no_trade_reason": "NO_TRIGGER"}
            if parsed["tail"] != tail:
                return {**head, "no_trade": True, "no_trade_reason": "TAIL_MISMATCH"}
            run_dir = 1 if tail == "UP" else -1
            direction = run_dir if parsed["arm"] == "CONT" else -run_dir
            event_context = {"event_type": "K_RUN", "k": K_RUN,
                             "run_len": sig["run_len"], "tail": tail}

        # PIT resolution law: a session's open/close prints are treated as
        # knowable only from the FOLLOWING day (strictly conservative). While
        # the entry session is not yet knowable, the intent is refused
        # IDENTICALLY whether or not the future session exists in the injected
        # panel (calendar knowledge is never used to differentiate).
        asof_date = None
        if asof is not None:
            asof_date = (asof if isinstance(asof, datetime)
                         else nc.parse_ts(asof)).date()
        entry_session = nc.next_session(panel, session_date, 1)
        if entry_session is None or (asof is not None
                                     and asof_date <= nc._as_date(entry_session)):
            return {**head, "no_trade": True,
                    "no_trade_reason": "ENTRY_SESSION_NOT_KNOWABLE_AT_ASOF"}

        # entry-session exclusions BEFORE horizon/roll resolution (law order)
        excl = self.apply_exclusions(calendar, panel)
        eflags = excl.get(entry_session, [])
        if eflags:
            return {**head, "entry_session": entry_session, "no_trade": True,
                    "no_trade_reason": "EXCLUDED: " + ",".join(eflags),
                    "exclusion_flags": eflags}

        # exit = the EXIT_HORIZON_SESSIONS-th held session counting the entry
        # session as day 1 (fixed k-day horizon, T4 class)
        exit_session = nc.next_session(panel, session_date, EXIT_HORIZON_SESSIONS)
        # exit is knowable only when its session is in-world AND its date has
        # passed; an exit session absent from the (possibly truncated) world is
        # PENDING, never "beyond panel" — the two worlds must not diverge
        exit_known = asof is None or (exit_session is not None
                                      and asof_date > nc._as_date(exit_session))
        sm = nc.session_map(panel)
        if exit_known:
            if exit_session is None:
                return {**head, "entry_session": entry_session, "no_trade": True,
                        "no_trade_reason": "HORIZON_BEYOND_PANEL"}
            switch_dates = {r["switch_date"] for r in panel.get("rolls", [])}
            window = _sessions_between(panel, entry_session, exit_session)
            if entry_session in switch_dates or exit_session in switch_dates \
                    or any(d in switch_dates for d in window):
                return {**head, "entry_session": entry_session,
                        "exit_session": exit_session, "no_trade": True,
                        "no_trade_reason": "ROLL_CROSS_UNADJUSTED",
                        "law": "spread-adjusted switch-day returns are chain data; "
                               "the adapter refuses rather than fabricating an "
                               "adjustment"}
            sm = nc.session_map(panel)
            entry_px = nc.round_to_tick(float(sm[entry_session]["open"]), self.tick)
            exit_px = nc.round_to_tick(float(sm[exit_session]["close"]), self.tick)
            exit_reason = "HORIZON_CLOSE"
            exit_last_bar = sm[exit_session]["last_bar_ct"]
        else:
            # PENDING: no exit details (session date, price, roll adjudication)
            # are reported or consumed in this state — uniform across worlds
            entry_px = None
            exit_px = exit_reason = None
            exit_session = None

        cost = nc.cost_per_side_usd(cost_tier, stress)
        return {
            **head,
            "no_trade": False, "no_trade_reason": None,
            "tail": tail, "delay": "D0",
            "entry_session": entry_session, "exit_session": exit_session,
            "holding_held_sessions": EXIT_HORIZON_SESSIONS,
            "arm": parsed["arm"],
            "side": "BUY" if direction == 1 else "SELL", "direction": direction,
            "quantity": 1,
            "order_type": "MARKET_NEXT_SESSION_OPEN",
            "ts_entry": f"{entry_session} (session open)",
            "entry_ref_price": entry_px,
            "ts_exit": f"{exit_session} (session close)",
            "exit_ref_price": exit_px, "exit_reason": exit_reason,
            "exit_resolution": ("RESOLVED" if exit_px is not None
                                else "PENDING_UPTO_ASOF"),
            "session_context": {
                "era": nc.era_for_date(entry_session),
                "entry_last_bar_ct": sm[entry_session]["last_bar_ct"],
                "exit_last_bar_ct": (sm[exit_session]["last_bar_ct"]
                                     if exit_known and exit_session else None),
            },
            "event_context": event_context,
            "exclusion_flags": [],
            "cost_preview": cost,
            "labels": ["SYNTHETIC FIXTURE", "PROPOSED DRAFT", "NO EXECUTION"],
        }


def _sessions_between(panel: dict, a: str, b: str) -> list[str]:
    dates = sorted(s["session_date"] for s in panel["sessions"])
    return [d for d in dates if a <= d <= b]
