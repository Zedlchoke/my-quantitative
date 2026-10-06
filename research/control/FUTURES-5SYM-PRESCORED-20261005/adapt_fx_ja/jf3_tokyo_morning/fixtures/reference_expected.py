"""reference_expected — INDEPENDENT expected-signal computation for JF3.

Recomputes the expected manifest from the committed panel JSON with its OWN
arithmetic (stdlib only; imports neither the adapter nor fx_common).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
JST = ZoneInfo("Asia/Tokyo")
CT_SUMMER = ZoneInfo("America/Chicago")   # for the C3'' clock-law probe
TICK = 5e-07
BASE = 0.0065


def load():
    with open(HERE / "jf3_panel_tokyo.json", "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    with open(HERE / "jf3_calendar.json", "r", encoding="utf-8") as fh:
        calendar = json.load(fh)
    return panel, calendar


def lmin(ts: str, tz=JST) -> int:
    dt = datetime.fromisoformat(ts).astimezone(tz)
    return dt.hour * 60 + dt.minute


def compute() -> dict:
    panel, calendar = load()
    bars_by_day: dict[str, list[dict]] = {}
    for b in panel["bars"]:
        bars_by_day.setdefault(b["session_date"], []).append(b)
    dates = sorted(bars_by_day)

    def rng(sd: str, tz=JST) -> tuple[float, float] | None:
        wb = [b for b in bars_by_day[sd] if 540 <= lmin(b["ts"], tz) < 690]
        if not wb:
            return None
        return (max(float(b["high"]) for b in wb), min(float(b["low"]) for b in wb))

    def atr20(sd: str) -> float:
        sm = {s["session_date"]: s for s in panel["sessions"]}
        prior = sorted(d for d in sm if d < sd)[-20:]
        assert len(prior) == 20
        return sum(float(sm[d]["high"]) - float(sm[d]["low"]) for d in prior) / 20.0

    def trigger(sd: str, tz=JST) -> dict | None:
        r = rng(sd, tz)
        if r is None:
            return None
        hi, lo = r
        for b in bars_by_day[sd]:
            if lmin(b["ts"], tz) < 690:
                continue
            c = float(b["close"])
            if c > hi or c < lo:
                return {"ts": b["ts"], "tail": "UP" if c > hi else "DN",
                        "close": c, "range_hi": hi, "range_lo": lo,
                        "decision_time": (datetime.fromisoformat(b["ts"])
                                          + timedelta(minutes=1)).isoformat()}
        return None

    def intent(sd: str, arm: str, tail: str, delay: str) -> dict | None:
        t = trigger(sd)
        assert t and t["tail"] == tail
        atr = atr20(sd)
        tmin = lmin(t["ts"])
        entry_min = (tmin + 1) + (0 if delay == "D1" else 30)
        eb = next(b for b in bars_by_day[sd] if lmin(b["ts"]) == entry_min)
        entry = float(eb["open"])
        tdir = 1 if tail == "UP" else -1
        direction = tdir if arm == "CONT" else -tdir
        sl, tp = (entry - atr, entry + 2 * atr) if direction == 1 \
            else (entry + atr, entry - 2 * atr)
        sl, tp = round(sl, 10), round(tp, 10)
        for b in bars_by_day[sd]:
            if lmin(b["ts"]) < entry_min:
                continue
            lo, hi = float(b["low"]), float(b["high"])
            if lo <= sl <= hi:
                ex = {"exit_ref_price": sl, "exit_reason": "SL", "exit_ts": b["ts"]}
                break
            if lo <= tp <= hi:
                ex = {"exit_ref_price": tp, "exit_reason": "TP", "exit_ts": b["ts"]}
                break
        else:
            last = [b for b in bars_by_day[sd] if lmin(b["ts"]) >= entry_min][-1]
            ex = {"exit_ref_price": float(last["close"]),
                  "exit_reason": "SESSION_CLOSE", "exit_ts": last["ts"]}
        return {"identity_probe": f"FB6J1-JF3-{arm}-{tail}-{delay}-S2",
                "session_date": sd, "tail": tail, "direction": direction,
                "side": "BUY" if direction == 1 else "SELL",
                "trigger_ts": t["ts"], "decision_time": t["decision_time"],
                "range_hi": t["range_hi"], "range_lo": t["range_lo"],
                "entry_ref_price": entry, "atr20_points": round(atr, 12),
                "sl_price": sl, "tp_price": tp, **ex}

    up_day, dn_day = calendar_probe()["up_day"], calendar_probe()["dn_day"]
    cov = 100 / 150
    return {
        "n_sessions": len(dates),
        "up_day": up_day, "dn_day": dn_day,
        "up_trigger": trigger(up_day), "dn_trigger": trigger(dn_day),
        "cont_up_d1": intent(up_day, "CONT", "UP", "D1"),
        "fade_dn_d30m": intent(dn_day, "FADE", "DN", "D30M"),
        "cont_dn_d1_on_up_day": {"no_trade_reason": "TAIL_MISMATCH"},
        "coverage_fail_day": calendar_probe()["cov_day"],
        "coverage_fail_value": round(cov, 6),
        "boj_day": calendar_probe()["boj_day"],
        "mof_day": calendar_probe()["mof_day"],
        "expected_exclusions": {
            calendar_probe()["boj_day"]: ["X_BOJ_MPM_DAY"],
            calendar_probe()["mof_day"]: ["X_MOF_DISCLOSURE_DAY"],
            calendar_probe()["cov_day"]: ["H_WINDOW_COVERAGE_LT_080"],
        },
        # C3'' clock-law probe: bucketing the SAME bars in CT instead of JST
        # moves the window by 14-15h -> a different (or no) trigger. The
        # Tokyo-anchor is load-bearing; a +/-1h-class shift is a clock bug kill.
        "dst_mismatch_probe": {
            "up_day_trigger_jst": (trigger(up_day) or {}).get("ts"),
            "up_day_trigger_ct_bucketed": (trigger(up_day, CT_SUMMER) or {}).get("ts"),
            "different": (trigger(up_day) or {}).get("ts")
                         != (trigger(up_day, CT_SUMMER) or {}).get("ts"),
        },
    }


def calendar_probe() -> dict:
    _, calendar = load()
    with open(HERE / "probe_dates.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


if __name__ == "__main__":
    print(json.dumps(compute(), indent=1, sort_keys=True)[:1500])
