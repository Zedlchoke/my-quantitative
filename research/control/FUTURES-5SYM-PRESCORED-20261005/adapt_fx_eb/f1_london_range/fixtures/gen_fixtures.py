"""gen_fixtures — F1 London-Range deterministic synthetic panels (6E + 6B).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python gen_fixtures.py
(writes panel_6E.json / panel_6B.json / EXPECTED_MANIFEST.json alongside).

EXPECTED values are hand-derived from FROZEN_RULE_DRAFT.md (independent of the
adapter code path): London windows [08:00,11:00)/[11:00,15:30) = CT 02:00-05:00/
05:00-09:30 on April 2026 dates (BST-CDT = +6h, zoneinfo-resolved).
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import fixture_kit as fk  # noqa: E402

HERE = Path(__file__).resolve().parent

S_TRIG = "2026-04-15"
S_NOTRIG = "2026-04-16"
S_COVLOW = "2026-04-17"
S_HOLIDAY = "2026-04-24"
S_ONFOMC = "2026-04-22"
S_OVERLAY = "2026-04-23"      # ECB day on 6E / MPC day on 6B
S_QBAD_6E = "2026-07-06"      # 2026-Q3 (ECU26 NOT_OBTAINED)
S_QBAD_6B = "2023-06-15"      # 2023-Q2 (BPM24 NOT_OBTAINED)

for d in (S_TRIG, S_NOTRIG, S_COVLOW, S_HOLIDAY, S_ONFOMC, S_OVERLAY,
          S_QBAD_6E, S_QBAD_6B):
    assert date.fromisoformat(d).weekday() < 5, d


def sawtooth_range_bars(session_date, contract, base, tick, volume=1000):
    """[08:00,11:00) London = 02:00-05:00 CT, 180 bars, 8-tick sawtooth:
    R_lon = [base, base + 8*tick]."""
    bars = []
    px = base
    for i in range(180):
        step = tick if (i % 16) < 8 else -tick
        c = round(px + step, 10)
        bars.append(fk.bar(session_date, (2 * 60 + i) // 60, (2 * 60 + i) % 60,
                           px, max(px, c), min(px, c), c, volume, contract))
        px = c
    return bars


def trigger_window_bars(session_date, contract, base, trig_close, volume=1000):
    """05:00-09:29 CT: flat at base, trigger bar 05:45 closes at trig_close,
    then flat at trig_close through 09:29."""
    bars = fk.flat_bars(session_date, (5, 0), (5, 45), base, volume, contract)
    bars.append(fk.bar(session_date, 5, 45, base, trig_close, base, trig_close,
                       5000, contract))
    bars += fk.flat_bars(session_date, (5, 46), (9, 30), trig_close, volume, contract)
    return bars


def tail_bars(session_date, contract, px):
    return fk.flat_bars(session_date, (15, 55), (16, 1), px, 1000, contract)


def agg(session_date, o, h, lo, c, contract, volume=1000):
    return {"session_date": session_date, "open": o, "high": h, "low": lo,
            "close": c, "volume": volume, "contract": contract,
            "last_bar_ct": "16:00"}


def build(sym: str):
    tick = 0.00005 if sym == "6E" else 0.0001
    base = round(1.10010 if sym == "6E" else 1.30010, 10)
    trig_close = round(base + 18 * tick, 10)          # 1.10100 / 1.30130
    contract = f"{sym}Z6-SYN"
    sessions, atr20 = fk.warmup_sessions(sym, contract)
    bars: list[dict] = []

    # S_TRIG — full range + trigger + tail
    bars += sawtooth_range_bars(S_TRIG, contract, base, tick)
    bars += trigger_window_bars(S_TRIG, contract, base, trig_close)
    bars += tail_bars(S_TRIG, contract, trig_close)
    sessions.append(agg(S_TRIG, base, trig_close, base, trig_close, contract))

    # S_NOTRIG — dense windows, no out-of-range close
    bars += sawtooth_range_bars(S_NOTRIG, contract, base, tick)
    bars += trigger_window_bars(S_NOTRIG, contract, base, base)
    bars += tail_bars(S_NOTRIG, contract, base)
    sessions.append(agg(S_NOTRIG, base, round(base + 8 * tick, 10), base, base, contract))

    # S_COVLOW — 60/180 range minutes (coverage 1/3) + would-be trigger
    rng = sawtooth_range_bars(S_COVLOW, contract, base, tick)[:60]
    bars += rng
    bars += trigger_window_bars(S_COVLOW, contract, base, trig_close)
    bars += tail_bars(S_COVLOW, contract, trig_close)
    sessions.append(agg(S_COVLOW, base, trig_close, base, trig_close, contract))

    # S_HOLIDAY / S_QBAD — sparse
    for sd in ([S_HOLIDAY, S_QBAD_6E] if sym == "6E" else [S_QBAD_6B]):
        bars += fk.flat_bars(sd, (5, 40), (5, 42), base, 500, contract)
        sessions.append(agg(sd, base, base, base, base, contract))

    # S_ONFOMC — engineered trigger inside an F2 event day
    bars += sawtooth_range_bars(S_ONFOMC, contract, base, tick)
    bars += trigger_window_bars(S_ONFOMC, contract, base, trig_close)
    bars += tail_bars(S_ONFOMC, contract, trig_close)
    sessions.append(agg(S_ONFOMC, base, trig_close, base, trig_close, contract))

    # S_OVERLAY — the 6E ECB / 6B MPC day (engineered trigger, must stand outside)
    bars += sawtooth_range_bars(S_OVERLAY, contract, base, tick)
    bars += trigger_window_bars(S_OVERLAY, contract, base, trig_close)
    bars += tail_bars(S_OVERLAY, contract, trig_close)
    sessions.append(agg(S_OVERLAY, base, trig_close, base, trig_close, contract))

    if sym == "6E":
        calendar = {
            "fomc_dates": [{"date": S_ONFOMC, "time_ct": "13:00",
                            "vintage_asof": S_ONFOMC, "provenance": "SYNTHETIC"}],
            "ecb_dates": [{"date": S_OVERLAY, "decision": "14:15 CET",
                           "vintage_asof": S_OVERLAY, "provenance": "SYNTHETIC"}],
            "holiday_neighborhood_6e": [S_HOLIDAY],   # fixture-scoped injection
        }
    else:
        calendar = {
            "mpc_dates": [{"date": S_OVERLAY, "kind": "change",
                           "vintage_asof": S_OVERLAY, "provenance": "SYNTHETIC"}],
            "fomc_dates": [{"date": S_ONFOMC, "time_ct": "13:00",
                            "vintage_asof": S_ONFOMC, "provenance": "SYNTHETIC"}],
        }
    return fk.panel(sym, contract, sessions, bars, calendar), base, tick, trig_close, atr20


def expected(sym: str, base: float, tick: float, trig_close: float, atr: float) -> dict:
    rlon_hi = round(base + 8 * tick, 10)
    sl = round(trig_close - atr, 10)
    tp = round(trig_close + 2 * atr, 10)
    fam = "FXF1"
    exp = {
        "atr20": atr,
        "S_trig": {
            "rlon": [base, rlon_hi], "coverage": 1.0,
            "trigger": {"sign": "UP", "close": trig_close, "bar_ct": 5 * 60 + 45},
            "signal_status": "TRIGGERED",
            "orders": {
                f"{fam}-{sym}-HC-UP-D0-S2": {
                    "side": "BUY", "entry": trig_close, "sl": sl, "tp": tp,
                    "exit": trig_close, "rule": "TIME_EXIT_1600CT"},
                f"{fam}-{sym}-HD-UP-D0-S2": {
                    "side": "SELL", "entry": trig_close,
                    "sl": round(trig_close + atr, 10),
                    "tp": round(trig_close - 2 * atr, 10),
                    "exit": trig_close, "rule": "TIME_EXIT_1600CT"},
            },
        },
        "S_notrig": {"status": "NO_TRADE", "blocking": ["NO_TRIGGER"]},
        "S_covlow": {"status": "NO_TRADE",
                     "blocking": ["LONDON_COVERAGE_LT_080"]},
        "S_onfomc": {"status": "NO_TRADE",
                     "blocking": ["FXF2_EVENT_DAY_STANDING_OUTSIDE"]},
        "S_overlay": {"status": "NO_TRADE",
                      "blocking": ["FXF2_EVENT_DAY_STANDING_OUTSIDE"]},
    }
    if sym == "6E":
        exp["S_holiday"] = {"status": "NO_TRADE",
                            "blocking": ["H6E_NEIGHBORHOOD_FAIL_CLOSED"]}
        exp["S_qbad"] = {"status": "NO_TRADE",
                         "blocking": ["QUARTER_NOT_OBTAINED_ROLL_ANCHOR"]}
    else:
        exp["declaration_flag_every_session"] = "HOL_GRID_ABSENT_0OF42_DECLARED"
        exp["S_qbad"] = {"status": "NO_TRADE",
                         "blocking": ["QUARTER_NOT_OBTAINED_ROLL_ANCHOR"]}
    return exp


def main():
    manifest = {"family": "FX-F1",
                "proposed": "PROPOSED fixtures; outcome-blind; synthetic only",
                "panels": {"6E": "panel_6E.json", "6B": "panel_6B.json"},
                "expected": {}}
    for sym in ("6E", "6B"):
        panel, base, tick, trig_close, atr = build(sym)
        with open(HERE / f"panel_{sym}.json", "w", encoding="utf-8") as fh:
            json.dump(panel, fh, indent=1)
        manifest["expected"][sym] = expected(sym, base, tick, trig_close, atr)
        print(f"{sym}: sessions={len(panel['sessions'])} bars={len(panel['bars'])} "
              f"base={base} trig={trig_close} atr20={atr}")
    with open(HERE / "EXPECTED_MANIFEST.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print("EXPECTED_MANIFEST.json written")


if __name__ == "__main__":
    main()
