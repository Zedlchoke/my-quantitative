"""gen_fixtures — F2 Policy-Decision deterministic synthetic panels (6E + 6B).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python gen_fixtures.py

EXPECTED values hand-derived from FROZEN_RULE_DRAFT.md: 6E anchor 13:00 CT
(minute 780); 6B anchor 12:00 London — minute 720 — which on 2026-04-16
(BST/CDT, +6h) is 06:00 CT and on the DST-mismatch date 2026-03-12 (US DST
active, UK still GMT, +5h) is 07:00 CT. The CT shift with a stable London
anchor IS the DST-proof the fixtures encode.
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import fixture_kit as fk  # noqa: E402

HERE = Path(__file__).resolve().parent

S_FOMC = "2026-04-15"
S_EMERG = "2026-04-21"
S_ECB = "2026-04-16"          # 6E ECB stratum; 6B MPC anchor day
S_MPC_HOLD = "2026-03-12"     # 6B DST-mismatch week (US DST, UK GMT)
S_DOUBLE = "2026-04-22"       # 6B MPC n FOMC
S_QUIET = "2026-04-23"
S_QBAD_6E = "2026-07-06"
S_QBAD_6B = "2023-06-15"

for d in (S_FOMC, S_EMERG, S_ECB, S_MPC_HOLD, S_DOUBLE, S_QUIET, S_QBAD_6E, S_QBAD_6B):
    assert date.fromisoformat(d).weekday() < 5, d


def spike_block(session_date, contract, anchor_min, pre_close, anchor_close,
                window_closes, spike_volume, volume=1000):
    """pre(anchor-10..anchor-1) + anchor bar + 5 window bars + flat post
    (anchor+6..anchor+45 at window_closes[-1]) + 15:55-16:00 CT tail."""
    bars = fk.flat_bars(session_date, divmod(anchor_min - 10, 60),
                        divmod(anchor_min, 60), pre_close, volume, contract)
    bars.append(fk.bar(session_date, anchor_min // 60, anchor_min % 60,
                       pre_close, max(pre_close, anchor_close),
                       min(pre_close, anchor_close), anchor_close,
                       spike_volume, contract))
    px = anchor_close
    for i, c in enumerate(window_closes, 1):
        bars.append(fk.bar(session_date, (anchor_min + i) // 60,
                           (anchor_min + i) % 60, px, max(px, c), min(px, c),
                           c, volume, contract))
        px = c
    bars += fk.flat_bars(session_date, divmod(anchor_min + 6, 60),
                         divmod(anchor_min + 46, 60), window_closes[-1],
                         volume, contract)
    bars += fk.flat_bars(session_date, (15, 55), (16, 1), window_closes[-1],
                         volume, contract)
    return bars


ATR = {"6E": 0.0010, "6B": 0.0020}


def agg(session_date, o, c, contract, sym):
    """Held-session aggregate whose range is exactly the symbol's ATR constant
    (spanning the day move), so sparse scenario sessions never pollute a
    prior-window ATR(20)."""
    r = ATR[sym] / 2.0
    return {"session_date": session_date, "open": o,
            "high": round(max(o, c) + r, 10), "low": round(min(o, c) - r, 10),
            "close": c, "volume": 1000, "contract": contract,
            "last_bar_ct": "16:00"}


WINDOW_6E = [1.10050, 1.10080, 1.10100, 1.10120, 1.10150]
WINDOW_6B = [1.30050, 1.30080, 1.30100, 1.30120, 1.30150]


def build_6e():
    sym, contract = "6E", "6EZ6-SYN"
    base = 1.10010
    sessions, atr20 = fk.warmup_sessions(sym, contract)
    bars = spike_block(S_FOMC, contract, 780, base, 1.10030, WINDOW_6E, 17240)
    sessions.append(agg(S_FOMC, base, 1.10150, contract, "6E"))
    bars += fk.flat_bars(S_EMERG, (12, 25), (12, 36), base, 1000, contract)
    sessions.append(agg(S_EMERG, base, base, contract, "6E"))
    bars += fk.flat_bars(S_ECB, (14, 10), (14, 13), base, 1500, contract)
    sessions.append(agg(S_ECB, base, base, contract, "6E"))
    bars += fk.flat_bars(S_QUIET, (12, 55), (13, 6), base, 1000, contract)
    sessions.append(agg(S_QUIET, base, base, contract, "6E"))
    bars += fk.flat_bars(S_QBAD_6E, (12, 55), (13, 6), base, 1000, contract)
    sessions.append(agg(S_QBAD_6E, base, base, contract, "6E"))
    calendar = {
        "fomc_statements": [
            {"date": S_FOMC, "time_ct": "13:00", "kind": "decision",
             "vintage_asof": S_FOMC, "provenance": "SYNTHETIC"},
            {"date": S_EMERG, "time_ct": "12:30", "kind": "emergency",
             "vintage_asof": S_EMERG, "provenance": "SYNTHETIC"},
        ],
        "ecb_dates": [{"date": S_ECB, "decision": "14:15 CET",
                       "vintage_asof": S_ECB, "provenance": "SYNTHETIC"}],
    }
    return fk.panel(sym, contract, sessions, bars, calendar), base, atr20


def build_6b():
    sym, contract = "6B", "6BZ6-SYN"
    base = 1.30010
    # warmup ends 2026-03-11 so the DST-mismatch day 2026-03-12 sits just after
    # it; uniform filler aggregates bridge 03-13..04-15 so the ATR(20) window
    # of the 2026-04-16 MPC day is clean (constant range = 0.0020 exactly).
    sessions, atr20 = fk.warmup_sessions(sym, contract,
                                         end=date(2026, 3, 11))
    rng = 0.0020
    # March DST-mismatch week: US DST on, UK GMT -> 12:00 London = 07:00 CT (420)
    bars = spike_block(S_MPC_HOLD, contract, 420, base, 1.30030, WINDOW_6B, 18700)
    sessions.append(agg(S_MPC_HOLD, base, 1.30150, contract, "6B"))
    existing = {s["session_date"] for s in sessions}
    for d in fk.weekday_dates(date(2026, 4, 15), 40):
        if d not in existing:
            sessions.append({"session_date": d, "open": base,
                             "high": round(base + rng / 2, 10),
                             "low": round(base - rng / 2, 10), "close": base,
                             "volume": 1000, "contract": contract,
                             "last_bar_ct": "16:00"})
    # April: London BST / Chicago CDT -> 12:00 London = 06:00 CT (minute 360)
    bars += spike_block(S_ECB, contract, 360, base, 1.30030, WINDOW_6B, 18700)
    sessions.append(agg(S_ECB, base, 1.30150, contract, "6B"))
    bars += fk.flat_bars(S_FOMC, (12, 55), (13, 6), base, 1500, contract)
    sessions.append(agg(S_FOMC, base, base, contract, "6B"))
    bars += fk.flat_bars(S_DOUBLE, (6, 55), (7, 6), base, 1500, contract)
    sessions.append(agg(S_DOUBLE, base, base, contract, "6B"))
    bars += fk.flat_bars(S_QUIET, (6, 55), (7, 6), base, 1000, contract)
    sessions.append(agg(S_QUIET, base, base, contract, "6E"))
    bars += fk.flat_bars(S_QBAD_6B, (6, 55), (7, 6), base, 1000, contract)
    sessions.append(agg(S_QBAD_6B, base, base, contract, "6B"))
    calendar = {
        "mpc_dates": [
            {"date": S_ECB, "kind": "change", "vintage_asof": S_ECB,
             "provenance": "SYNTHETIC (official-class capture cal_cost/captures/"
                           "boe_mpc_live.html for 2026 forward dates)"},
            {"date": S_MPC_HOLD, "kind": "hold", "vintage_asof": S_MPC_HOLD,
             "provenance": "SYNTHETIC"},
            {"date": S_DOUBLE, "kind": "change", "vintage_asof": S_DOUBLE,
             "provenance": "SYNTHETIC"},
        ],
        "fomc_statements": [
            {"date": S_FOMC, "time_ct": "13:00", "kind": "decision",
             "vintage_asof": S_FOMC, "provenance": "SYNTHETIC"},
            {"date": S_DOUBLE, "time_ct": "13:00", "kind": "decision",
             "vintage_asof": S_DOUBLE, "provenance": "SYNTHETIC"},
        ],
    }
    return fk.panel(sym, contract, sessions, bars, calendar), base, atr20


def expected_6e():
    return {
        "S_fomc": {"anchor_ct_minute": 780, "window_sign": "UP",
                   "window_move": 0.0012, "spike_ratio": 17.24, "atr20": 0.001,
                   "strata": ["FOMC_DECISION_1300CT"],
                   "orders": {
                       "FXF2-6E-RC-UP-D0-S2": {"side": "BUY", "entry": 1.10150,
                                               "sl": 1.10050, "tp": 1.10350,
                                               "exit": 1.10150,
                                               "rule": "TIME_EXIT_1600CT"},
                       "FXF2-6E-RD-UP-D0-S2": {"side": "SELL", "entry": 1.10150,
                                               "sl": 1.10250, "tp": 1.09950,
                                               "exit": 1.10150,
                                               "rule": "TIME_EXIT_1600CT"}}},
        "S_emerg": {"status": "NO_TRADE",
                    "blocking": ["EMERGENCY_TIMING"]},
        "S_ecb": {"status": "NO_TRADE",
                  "blocking": ["ECB_STRATUM_NO_BASE_TRADE"]},
        "S_quiet": {"status": "NO_TRADE", "blocking": ["NOT_AN_EVENT_DAY"]},
        "S_qbad": {"status": "NO_TRADE",
                   "blocking": ["NOT_AN_EVENT_DAY",
                                "QUARTER_NOT_OBTAINED_ROLL_ANCHOR"]},
    }


def expected_6b():
    return {
        "S_mpc_change": {"anchor_ct_minute": 360, "window_sign": "UP",
                         "window_move": 0.0012, "spike_ratio": 18.7,
                         "atr20": 0.002, "strata": ["MPC_CHANGE"],
                         "orders": {
                             "FXF2-6B-RC-UP-D0-S2": {"side": "BUY",
                                                     "entry": 1.30150,
                                                     "sl": 1.29950,
                                                     "tp": 1.30550,
                                                     "exit": 1.30150,
                                                     "rule": "TIME_EXIT_1600CT"},
                             "FXF2-6B-RD-UP-D0-S2": {"side": "SELL",
                                                     "entry": 1.30150,
                                                     "sl": 1.30350,
                                                     "tp": 1.29750,
                                                     "exit": 1.30150,
                                                     "rule": "TIME_EXIT_1600CT"}}},
        "S_mpc_hold_mismatch": {"anchor_ct_minute": 420, "window_sign": "UP",
                                "strata": ["MPC_HOLD"]},
        "S_fomc_6B": {"status": "NO_TRADE",
                      "blocking": ["FOMC_STRATUM_NO_BASE_TRADE"]},
        "S_double": {"status": "NO_TRADE", "blocking": ["DOUBLE_EVENT_EXCLUDED"]},
        "S_quiet": {"status": "NO_TRADE", "blocking": ["NOT_AN_EVENT_DAY"]},
        "S_qbad": {"status": "NO_TRADE",
                   "blocking": ["NOT_AN_EVENT_DAY",
                                "QUARTER_NOT_OBTAINED_ROLL_ANCHOR"]},
    }


def main():
    p6e, base6e, atr6e = build_6e()
    p6b, base6b, atr6b = build_6b()
    for sym, p in (("6E", p6e), ("6B", p6b)):
        with open(HERE / f"panel_{sym}.json", "w", encoding="utf-8") as fh:
            json.dump(p, fh, indent=1)
        print(f"{sym}: sessions={len(p['sessions'])} bars={len(p['bars'])}")
    manifest = {"family": "FX-F2",
                "proposed": "PROPOSED fixtures; outcome-blind; synthetic only",
                "panels": {"6E": "panel_6E.json", "6B": "panel_6B.json"},
                "expected": {"6E": expected_6e(), "6B": expected_6b()}}
    with open(HERE / "EXPECTED_MANIFEST.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print("EXPECTED_MANIFEST.json written; bases", base6e, base6b, atr6e, atr6b)


if __name__ == "__main__":
    main()
