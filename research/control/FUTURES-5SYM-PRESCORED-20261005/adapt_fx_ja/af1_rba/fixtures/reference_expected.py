"""reference_expected — INDEPENDENT expected-signal computation for AF1."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
SYD = ZoneInfo("Australia/Sydney")
E2_TICK = 5e-05


def load():
    with open(HERE / "af1_panel_rba.json", "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    with open(HERE / "af1_calendar.json", "r", encoding="utf-8") as fh:
        calendar = json.load(fh)
    return panel, calendar


def lmin(ts: str) -> int:
    dt = datetime.fromisoformat(ts).astimezone(SYD)
    return dt.hour * 60 + dt.minute


def compute() -> dict:
    panel, calendar = load()
    events = calendar["rba_decision_dates"]
    bars_by_day: dict[str, list[dict]] = {}
    for b in panel["bars"]:
        bars_by_day.setdefault(b["session_date"], []).append(b)
    sm = {s["session_date"]: s for s in panel["sessions"]}

    def win(sd: str):
        wb = [b for b in bars_by_day[sd] if 870 <= lmin(b["ts"]) < 875]
        return float(wb[-1]["close"]) - float(wb[0]["open"])

    def watr(sd: str) -> float:
        prior = sorted(d for d in events if d < sd)[-20:]
        return sum(float(sm[d]["window_ranges"]["rba"]) for d in prior) / 20.0

    def intent(sd: str, arm: str, tail: str, delay: str) -> dict:
        atr = watr(sd)
        entry_local = 875 + (0 if delay == "D1" else 30)
        eb = next(b for b in bars_by_day[sd] if lmin(b["ts"]) == entry_local)
        entry = float(eb["open"])
        tdir = 1 if tail == "UP" else -1
        direction = tdir if arm == "DRIFT" else -tdir
        sl, tp = (entry - atr, entry + 2 * atr) if direction == 1 \
            else (entry + atr, entry - 2 * atr)
        sl, tp = round(sl, 10), round(tp, 10)
        ex = None
        for b in bars_by_day[sd]:
            lm = lmin(b["ts"])
            if lm < entry_local or lm > 1020:
                continue
            lo, hi = float(b["low"]), float(b["high"])
            if lo <= sl <= hi:
                ex = {"exit_ref_price": sl, "exit_reason": "SL", "exit_ts": b["ts"]}
                break
            if lo <= tp <= hi:
                ex = {"exit_ref_price": tp, "exit_reason": "TP", "exit_ts": b["ts"]}
                break
        if ex is None:
            cand = [b for b in bars_by_day[sd]
                    if entry_local <= lmin(b["ts"]) <= 1020]
            ex = {"exit_ref_price": float(cand[-1]["close"]),
                  "exit_reason": "SESSION_CLOSE", "exit_ts": cand[-1]["ts"]}
        return {"identity_probe": f"C6A0-CONT-AF1-{arm}-{tail}-{delay}-S2",
                "session_date": sd, "era": "era2", "tail": tail,
                "direction": direction, "side": "BUY" if direction == 1 else "SELL",
                "entry_ref_price": entry, "atr20_window": round(atr, 12),
                "sl_price": sl, "tp_price": tp, **ex}

    up_day, dn_day = calendar_probe()["up_day"], calendar_probe()["dn_day"]
    return {
        "n_events": len(events),
        "up_day": up_day, "dn_day": dn_day,
        "up_move": round(win(up_day), 12), "dn_move": round(win(dn_day), 12),
        "cont_up_d1": intent(up_day, "DRIFT", "UP", "D1"),
        "cont_dn_d1": intent(dn_day, "DRIFT", "DN", "D1"),
        "k0_change_days": {"n": 23, "folds": 8, "per_fold": round(23 / 8, 2),
                           "passes": False,
                           "law": "K0 thin-n kill PRE-REGISTERED: change-vs-hold "
                                  "strata fragment the folds below the >=5 floor"},
        "expected_exclusions": {
            calendar_probe()["fomc_day"]: ["X_FOMC_DAY"],
            calendar_probe()["fomc_spill_day"]: ["X_FOMC_SPILLOVER_NEXT_DAY"],
        },
    }


def calendar_probe() -> dict:
    with open(HERE / "probe_dates.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


if __name__ == "__main__":
    print(json.dumps(compute(), indent=1, sort_keys=True)[:1200])
