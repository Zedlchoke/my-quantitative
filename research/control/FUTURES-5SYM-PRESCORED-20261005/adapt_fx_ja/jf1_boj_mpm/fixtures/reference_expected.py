"""reference_expected — INDEPENDENT expected-signal computation for JF1.

Recomputes the expected manifest from the committed panel JSON with its OWN
arithmetic (stdlib only; imports neither the adapter nor fx_common) so the
adapter is checked against a second implementation, not itself.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
JST = ZoneInfo("Asia/Tokyo")
TICK = 5e-07


def load():
    with open(HERE / "jf1_panel_mpm.json", "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    with open(HERE / "jf1_calendar.json", "r", encoding="utf-8") as fh:
        calendar = json.load(fh)
    return panel, calendar


def local_min(ts: str) -> int:
    dt = datetime.fromisoformat(ts).astimezone(JST)
    return dt.hour * 60 + dt.minute


def window_window(panel: dict, sd: str):
    return [b for b in panel["bars"] if b["session_date"] == sd
            and 720 <= local_min(b["ts"]) < 930]


def bars_from(panel: dict, sd: str, min_local: int):
    return [b for b in panel["bars"] if b["session_date"] == sd
            and local_min(b["ts"]) >= min_local]


def compute() -> dict:
    panel, calendar = load()
    mpm = set(calendar["boj_mpm_dates"])
    sessions = {s["session_date"]: s for s in panel["sessions"]}

    # ---- tails per event date (window move in 6J price terms)
    tails: dict[str, str | None] = {}
    window_moves: dict[str, float] = {}
    for sd in sorted(mpm):
        wb = window_window(panel, sd)
        move = float(wb[-1]["close"]) - float(wb[0]["open"])
        window_moves[sd] = round(move, 12)
        tails[sd] = "UP" if move > 0 else ("DN" if move < 0 else None)

    # ---- window ATR(20) = mean of prior-20 EVENT window ranges, strict past
    def w_atr(sd: str) -> float:
        prior = sorted(d for d in mpm if d < sd)[-20:]
        assert len(prior) == 20
        return sum(float(sessions[d]["window_ranges"]["mpm"]) for d in prior) / 20.0

    def exit_scan(sd: str, entry_local: int, entry: float, sl: float, tp: float):
        for b in bars_from(panel, sd, entry_local):
            lo, hi = float(b["low"]), float(b["high"])
            if lo <= sl <= hi:
                return {"exit_ref_price": sl, "exit_reason": "SL",
                        "exit_ts": b["ts"], "exit_resolution": "RESOLVED"}
            if lo <= tp <= hi:
                return {"exit_ref_price": tp, "exit_reason": "TP",
                        "exit_ts": b["ts"], "exit_resolution": "RESOLVED"}
        last = bars_from(panel, sd, entry_local)[-1]
        return {"exit_ref_price": float(last["close"]), "exit_reason": "SESSION_CLOSE",
                "exit_ts": last["ts"], "exit_resolution": "RESOLVED"}

    def intent(sd: str, arm: str, tail: str, delay: str) -> dict:
        atr = w_atr(sd)
        entry_local = 930 + (0 if delay == "D1" else 30)
        eb = next(b for b in bars_from(panel, sd, entry_local)
                  if local_min(b["ts"]) == entry_local)
        entry = float(eb["open"])
        tdir = 1 if tail == "UP" else -1
        direction = tdir if arm == "DRIFT" else -tdir
        if direction == 1:
            sl, tp = entry - atr, entry + 2 * atr
        else:
            sl, tp = entry + atr, entry - 2 * atr
        sl, tp = round(sl, 10), round(tp, 10)
        ex = exit_scan(sd, entry_local, entry, sl, tp)
        return {"identity_probe": f"FB6J1-JF1-{arm}-{tail}-{delay}-S2",
                "session_date": sd, "tail": tail, "direction": direction,
                "side": "BUY" if direction == 1 else "SELL",
                "entry_ref_price": entry, "atr20_window": round(atr, 12),
                "sl_price": sl, "tp_price": tp, **ex}

    tp_day = calendar_probe_dates()["tp_hit"]
    sl_day = calendar_probe_dates()["sl_hit"]
    manifest = {
        "n_events": len(mpm),
        "n_control_days": len([d for d in sessions if d not in mpm]),
        "tails": tails,
        "window_moves": window_moves,
        "flat_day": calendar_probe_dates()["flat"],
        "tp_hit_intent_drift_up_d1": intent(tp_day, "DRIFT", "UP", "D1"),
        "sl_hit_intent_drift_dn_d1": intent(sl_day, "DRIFT", "DN", "D1"),
        "expected_exclusions": expected_exclusions(calendar, sessions),
    }
    return manifest


def calendar_probe_dates() -> dict:
    _, calendar = load()
    mpm = calendar["boj_mpm_dates"]
    return {"tp_hit": "2026-02-15", "sl_hit": "2026-03-15", "flat": "2026-01-15"}


def expected_exclusions(calendar: dict, sessions: dict) -> dict:
    """Independent recomputation of the fail-closed exclusion sets."""
    exp: dict[str, list[str]] = {}
    op = set(calendar["mof_op_days"])
    for sd in sessions:
        flags = []
        if sd in op:
            flags.append("X_MOF_OP_DAY")
        if sd == "2022-09-20":
            flags.append("X_ROLL_CEASE_GUARD")
        if sd == "2024-06-17":
            flags.append("H_HOLIDAY_TIMES_NOT_OBTAINED")
        if sd == "2026-07-30":
            flags.append("X_UNVERIFIED_OP_WINDOW_PRICE_ONLY")
        if flags:
            exp[sd] = sorted(flags)
    return exp


if __name__ == "__main__":
    print(json.dumps(compute(), indent=1, sort_keys=True)[:2000])
