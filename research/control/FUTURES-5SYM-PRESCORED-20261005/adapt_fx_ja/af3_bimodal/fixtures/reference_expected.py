"""reference_expected — INDEPENDENT expected-signal computation for AF3."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
SYD = ZoneInfo("Australia/Sydney")
SHA = ZoneInfo("Asia/Shanghai")


def load():
    with open(HERE / "af3_panel_sydney.json", "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    with open(HERE / "af3_calendar.json", "r", encoding="utf-8") as fh:
        calendar = json.load(fh)
    with open(HERE / "probe_dates.json", "r", encoding="utf-8") as fh:
        probe = json.load(fh)
    return panel, calendar, probe


def lmin(ts: str, tz=SYD) -> int:
    dt = datetime.fromisoformat(ts).astimezone(tz)
    return dt.hour * 60 + dt.minute


def compute() -> dict:
    panel, calendar, probe = load()
    bars_by_day: dict[str, list[dict]] = {}
    for b in panel["bars"]:
        bars_by_day.setdefault(b["session_date"], []).append(b)

    def rng(sd: str):
        wb = [b for b in bars_by_day[sd] if 570 <= lmin(b["ts"]) < 690]
        return (max(float(b["high"]) for b in wb), min(float(b["low"]) for b in wb))

    def trigger(sd: str):
        hi, lo = rng(sd)
        for b in bars_by_day[sd]:
            if lmin(b["ts"]) < 690:
                continue
            c = float(b["close"])
            if c > hi or c < lo:
                in_sha = 570 <= lmin(b["ts"], SHA) < 600
                return {"ts": b["ts"], "tail": "UP" if c > hi else "DN",
                        "close": c, "range_hi": hi, "range_lo": lo,
                        "in_china_window": in_sha,
                        "sha_local": lmin(b["ts"], SHA)}
        return None

    def atr20(sd: str) -> float:
        sm = {s["session_date"]: s for s in panel["sessions"]}
        prior = sorted(d for d in sm if d < sd)[-20:]
        return sum(float(sm[d]["high"]) - float(sm[d]["low"]) for d in prior) / 20.0

    def intent(sd: str, arm: str, tail: str, delay: str) -> dict:
        t = trigger(sd)
        atr = atr20(sd)
        tmin = lmin(t["ts"])
        entry_min = (tmin + 1) + (0 if delay == "D1" else 30)
        eb = next(b for b in bars_by_day[sd] if lmin(b["ts"]) == entry_min)
        entry = float(eb["open"])
        tdir = 1 if tail == "UP" else -1
        direction = tdir if arm == "ROT" else -tdir
        sl, tp = (entry - atr, entry + 2 * atr) if direction == 1 \
            else (entry + atr, entry - 2 * atr)
        sl, tp = round(sl, 10), round(tp, 10)
        ex = None
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
        if ex is None:
            cand = [b for b in bars_by_day[sd] if lmin(b["ts"]) >= entry_min]
            ex = {"exit_ref_price": float(cand[-1]["close"]),
                  "exit_reason": "SESSION_CLOSE", "exit_ts": cand[-1]["ts"]}
        return {"identity_probe": f"C6A0-CONT-AF3-{arm}-{tail}-{delay}-S2",
                "session_date": sd, "tail": tail, "direction": direction,
                "side": "BUY" if direction == 1 else "SELL",
                "trigger_ts": t["ts"], "entry_ref_price": entry,
                "atr20_points": round(atr, 12), "sl_price": sl, "tp_price": tp, **ex}

    rot, absd, k4 = probe["rot_day"], probe["abs_day"], probe["k4_day"]
    return {
        "rot_day": rot, "abs_day": absd, "k4_day": k4,
        "rot_trigger": trigger(rot), "abs_trigger": trigger(absd),
        "k4_trigger": trigger(k4),
        "k4_in_china_window": trigger(k4)["in_china_window"],
        "rot_up_d1": intent(rot, "ROT", "UP", "D1"),
        "abs_dn_d30m": intent(absd, "ABS", "DN", "D30M"),
        "coverage": {"cov_day": probe["cov_day"],
                     "value": round(90 / 120, 6)},
        "expected_exclusions": {
            probe["rba_day"]: ["X_RBA_DAY"],
            probe["fomc_day"]: ["X_FOMC_DAY"],
            probe["cov_day"]: ["H_WINDOW_COVERAGE_LT_080"],
        },
    }


if __name__ == "__main__":
    print(json.dumps(compute(), indent=1, sort_keys=True)[:1200])
