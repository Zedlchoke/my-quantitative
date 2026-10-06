"""gen_fixtures — F4 Globex reopen-gap deterministic synthetic panels (6E + 6B).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python gen_fixtures.py

M2c dual-window fixtures: each reopen session carries BOTH the 17:00-CT reopen
print (WINDOW_A, PRIMARY) and an 08:30-CT RTH-open print (WINDOW_B, ERRATUM
BASELINE) engineered so gap_B > gap_A — echoing the erratum's direction (true
reopen gaps 2.3-5x SMALLER than the mislabeled baseline) on synthetic numbers.
The Sunday fixture carries the ratio-4.0 pairing. All thresholds are
SYNTHETIC-PARAMETER-NOT-REGISTERED values that exercise machinery only.
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import fixture_kit as fk  # noqa: E402

HERE = Path(__file__).resolve().parent

S_REOPEN = "2026-04-17"    # Friday session, opens Thu 2026-04-16 17:00 CT
S_SUNDAY = "2026-04-20"    # Monday session_date, opens Sun 2026-04-19 17:00 CT
S_ROLL = "2026-04-22"      # injected roll switch
S_AFTER = "2026-04-23"     # session after the roll
S_BELOW = "2026-04-24"     # below-threshold gap (placebo class)

ATR = {"6E": 0.0010, "6B": 0.0020}
GAP = {  # (gap_a_reopen, gap_b_rth, sunday_gap_a, sunday_gap_b, below_gap)
    "6E": (0.00080, 0.00150, 0.00030, 0.00120, 0.00010),
    "6B": (0.00070, 0.00140, 0.00030, 0.00110, 0.00010),
}
THRESHOLD = {"6E": 0.00050, "6B": 0.00050}


def agg_uniform(session_date, close, contract, sym):
    r = ATR[sym] / 2.0
    return {"session_date": session_date, "open": close,
            "high": round(close + r, 10), "low": round(close - r, 10),
            "close": close, "volume": 1000, "contract": contract,
            "last_bar_ct": "16:00"}


def reopen_bars(family_date, prev_day, contract, open_px, post_px,
                rth_open_px, tail_px, volume=1000):
    """17:00 (prev_day wall clock) auction bar + flat + 08:30 RTH print +
    08:55-09:00 tail — ALL bars tagged with the family session_date (the Globex
    session that opens prev_day 17:00 CT belongs to family_date)."""
    bars = [fk.bar(prev_day, 17, 0, open_px, max(open_px, open_px + 0.0001),
                   min(open_px, open_px - 0.0001), open_px, 5000, contract)]
    bars += fk.flat_bars(prev_day, (17, 1), (17, 40), open_px, volume, contract)
    bars += fk.flat_bars(family_date, (8, 25), (8, 30), open_px, volume, contract)
    bars.append(fk.bar(family_date, 8, 30, rth_open_px, rth_open_px,
                       rth_open_px, rth_open_px, 2000, contract))
    bars += fk.flat_bars(family_date, (8, 31), (8, 36), rth_open_px, volume,
                         contract)
    bars += fk.flat_bars(family_date, (8, 55), (9, 1), tail_px, volume, contract)
    for b in bars:
        b["session_date"] = family_date          # carried session_date law
    return bars


def build(sym: str):
    contract = f"{sym}Z6-SYN"
    base = 1.10010 if sym == "6E" else 1.30010
    gap_a, gap_b, sun_a, sun_b, below = GAP[sym]
    sessions, atr20 = fk.warmup_sessions(sym, contract, end=date(2026, 4, 15))
    # uniform bridge sessions (04-16 prior-close carrier, 04-21, 04-23=S_AFTER)
    for d, close in ((date(2026, 4, 16), base), (date(2026, 4, 21), base),
                     (date(2026, 4, 23), base)):
        sessions.append(agg_uniform(d.isoformat(), close, contract, sym))
    bars = []
    # S_REOPEN 2026-04-17: reopen open = base + gap_a ; RTH open = base + gap_b
    reopen_px = round(base + gap_a, 10)
    rth_px = round(base + gap_b, 10)
    bars += reopen_bars(S_REOPEN, "2026-04-16", contract, reopen_px, reopen_px,
                        rth_px, reopen_px)
    sessions.append({"session_date": S_REOPEN, "open": reopen_px,
                     "high": max(reopen_px, rth_px),
                     "low": min(reopen_px, round(reopen_px - 0.0001, 10)),
                     "close": reopen_px, "volume": 7000,
                     "contract": contract, "last_bar_ct": "09:00"})
    # S_SUNDAY 2026-04-20 (opens Sunday 2026-04-19 17:00 CT)
    sun_px = round(base + gap_a + sun_a, 10)      # prior close = S_REOPEN close
    sun_rth = round(base + gap_a + sun_b, 10)
    bars += reopen_bars(S_SUNDAY, "2026-04-19", contract, sun_px, sun_px,
                        sun_rth, sun_px)
    sessions.append({"session_date": S_SUNDAY, "open": sun_px,
                     "high": max(sun_px, sun_rth), "low": sun_px,
                     "close": sun_px, "volume": 3000,
                     "contract": contract, "last_bar_ct": "09:00"})
    # S_ROLL / S_AFTER sparse
    for sd in (S_ROLL, S_AFTER):
        bars += fk.flat_bars(sd, (17, 0), (17, 2), base, 500, contract)
        sessions.append(agg_uniform(sd, base, contract, sym))
    # S_BELOW 2026-04-24 (prior close = base via S_AFTER agg)
    below_px = round(base + below, 10)
    bars += reopen_bars(S_BELOW, "2026-04-23", contract, below_px, below_px,
                        below_px, below_px)
    sessions.append({"session_date": S_BELOW, "open": below_px,
                     "high": below_px, "low": below_px, "close": below_px,
                     "volume": 1000, "contract": contract,
                     "last_bar_ct": "09:00"})
    calendar = {"roll_switch_dates": [S_ROLL]}
    if sym == "6E":
        calendar["holiday_neighborhood_6e"] = []
    return fk.panel(sym, contract, sessions, bars, calendar), base, atr20


def expected(sym: str, base: float, atr: float) -> dict:
    gap_a, gap_b, sun_a, sun_b, below = GAP[sym]
    thr = THRESHOLD[sym]
    fill = round(base + gap_a, 10)
    return {
        "atr": atr, "threshold": thr,
        "S_reopen": {"gap_a": gap_a, "gap_b": gap_b,
                     "ratio": round(gap_b / gap_a, 4),
                     "window_a_open": round(base + gap_a, 10),
                     "window_b_open": round(base + gap_b, 10),
                     "strata": ["WEEKDAY_REOPEN"], "tail": "UP",
                     "entry": fill, "exit": fill,
                     "exit_rule": "TIME_EXIT_0900CT_PROVISIONAL",
                     "sides": {"GC": "BUY", "GD": "SELL"},
                     "sl": {"GC": round(fill - atr, 10),
                            "GD": round(fill + atr, 10)},
                     "tp": {"GC": round(fill + 2 * atr, 10),
                            "GD": round(fill - 2 * atr, 10)}},
        "S_sunday": {"gap_a": sun_a,
                     "gap_b": sun_b,
                     "ratio": round(sun_b / sun_a, 4),
                     "status": "NO_TRADE",
                     "blocking": ["SUNDAY_REOPEN_STRATUM"]},
        "S_below": {"status": "NO_TRADE", "blocking": ["GAP_BELOW_THRESHOLD"],
                    "gap_a": below},
        "S_roll": {"status": "NO_TRADE", "blocking": ["ROLL_SESSION"]},
        "S_after": {"status": "NO_TRADE", "blocking": ["SESSION_AFTER_ROLL"]},
    }


def main():
    manifest = {"family": "FX-F4",
                "proposed": "PROPOSED fixtures; outcome-blind; synthetic only; "
                            "thresholds SYNTHETIC-PARAMETER-NOT-REGISTERED",
                "panels": {"6E": "panel_6E.json", "6B": "panel_6B.json"},
                "expected": {}}
    for sym in ("6E", "6B"):
        panel, base, atr = build(sym)
        with open(HERE / f"panel_{sym}.json", "w", encoding="utf-8") as fh:
            json.dump(panel, fh, indent=1)
        manifest["expected"][sym] = expected(sym, base, atr)
        print(f"{sym}: sessions={len(panel['sessions'])} bars={len(panel['bars'])}")
    with open(HERE / "EXPECTED_MANIFEST.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print("EXPECTED_MANIFEST.json written")


if __name__ == "__main__":
    main()
