"""gen_fixtures — F3 US-8:30 deterministic synthetic panels (6E + 6B).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python gen_fixtures.py

EXPECTED values hand-derived from FROZEN_RULE_DRAFT.md: anchor 07:30 CT
(minute 450); signal = close(07:30) - close(07:29); D0 fill = open(07:31);
D30M fill = open(08:01); exit TP/SL or 16:00 CT flat.
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import fixture_kit as fk  # noqa: E402

HERE = Path(__file__).resolve().parent

S_CPI = "2026-04-21"        # UP release
S_EMP = "2026-05-08"        # DN release (EMPSIT)
S_CANCELED = "2026-04-22"   # canceled-expected negative control
S_OTHER = "2026-04-23"      # unclassified 8:30 stratum
S_DOUBLE = "2026-04-15"     # CPI-known overlapping an F2 day-set
S_QUIET = "2026-04-24"      # postdated-vintage stamp -> PIT refusal class
S_QBAD_6E = "2026-07-06"
S_QBAD_6B = "2023-06-15"

ATR = {"6E": 0.0010, "6B": 0.0020}

for d in (S_CPI, S_EMP, S_CANCELED, S_OTHER, S_DOUBLE, S_QUIET, S_QBAD_6E, S_QBAD_6B):
    assert date.fromisoformat(d).weekday() < 5, d


def release_block(session_date, contract, base, move, spike_volume, post_px,
                  tail_px, volume=1000):
    """07:25..08:35 bars: flat pre, release bar 07:30 closes base+move, then
    flat at the release price; 15:55..16:00 CT tail at tail_px."""
    bars = fk.flat_bars(session_date, (7, 25), (7, 30), base, volume, contract)
    c0 = round(base + move, 10)
    bars.append(fk.bar(session_date, 7, 30, base, c0, base, c0, spike_volume,
                       contract))
    bars += fk.flat_bars(session_date, (7, 31), (8, 36), c0, volume, contract)
    bars += fk.flat_bars(session_date, (15, 55), (16, 1), tail_px, volume,
                         contract)
    return bars


def agg(session_date, o, c, contract, sym):
    r = ATR[sym] / 2.0
    return {"session_date": session_date, "open": o,
            "high": round(max(o, c) + r, 10), "low": round(min(o, c) - r, 10),
            "close": c, "volume": 1000, "contract": contract,
            "last_bar_ct": "16:00"}


def agg_uniform(session_date, base, contract, sym):
    """Range-normalized aggregate (range exactly the ATR constant) so scenario
    sessions never pollute a later day's prior-window ATR(20)."""
    r = ATR[sym] / 2.0
    return {"session_date": session_date, "open": base,
            "high": round(base + r, 10), "low": round(base - r, 10),
            "close": base, "volume": 1000, "contract": contract,
            "last_bar_ct": "16:00"}


def bls_calendar():
    return {
        "bls_vintage": [
            {"date": S_CPI, "series": "CPI", "status": "scheduled",
             "release_et": "08:30", "vintage_asof": "2026-04-10",
             "provenance": "SYNTHETIC (mirrors bls_dates.json 204/204 @08:30 ET)"},
            {"date": S_EMP, "series": "EMPSIT", "status": "scheduled",
             "release_et": "08:30", "vintage_asof": "2026-04-28",
             "provenance": "SYNTHETIC"},
            {"date": S_CANCELED, "series": "CPI", "status": "canceled_expected",
             "release_et": "08:30", "vintage_asof": "2026-04-10",
             "provenance": "SYNTHETIC (the 2025 canceled-expected class)"},
            {"date": S_OTHER, "series": "PPI", "status": "scheduled",
             "release_et": "08:30", "vintage_asof": "2026-04-15",
             "provenance": "SYNTHETIC (unclassified-8:30 stratum)"},
            {"date": S_DOUBLE, "series": "CPI", "status": "scheduled",
             "release_et": "08:30", "vintage_asof": "2026-04-10",
             "provenance": "SYNTHETIC"},
            {"date": S_QUIET, "series": "CPI", "status": "scheduled",
             "release_et": "08:30", "vintage_asof": "2026-05-01",
             "provenance": "SYNTHETIC (postdated vintage -> PIT refusal class)"},
        ],
        "fomc_dates": [{"date": S_DOUBLE, "time_ct": "13:00",
                        "vintage_asof": S_DOUBLE, "provenance": "SYNTHETIC"}],
    }


def build(sym: str):
    contract = f"{sym}Z6-SYN"
    base = 1.10010 if sym == "6E" else 1.30010
    sessions, atr20 = fk.warmup_sessions(sym, contract, end=date(2026, 4, 14))
    bars = []
    # S_DOUBLE (inside the warmup span) and the 04-15..04-20 bridge carry
    # uniform-range aggregates so no prior-window ATR(20) is polluted
    existing = {s["session_date"] for s in sessions}
    for d in fk.weekday_dates(date(2026, 4, 20), 30):
        if d not in existing:
            sessions.append(agg(d, base, base, contract, sym))
    bars += release_block(S_CPI, contract, base, 0.00050, 1950,
                          round(base + 0.00050, 10), round(base + 0.00110, 10))
    sessions.append(agg_uniform(S_CPI, base, contract, sym))
    bars += release_block(S_EMP, contract, base, -0.00040, 1900,
                          round(base - 0.00040, 10), round(base - 0.00070, 10))
    sessions.append(agg_uniform(S_EMP, base, contract, sym))
    for sd in (S_CANCELED, S_OTHER, S_QUIET):
        bars += fk.flat_bars(sd, (7, 28), (7, 33), base, 800, contract)
        sessions.append(agg_uniform(sd, base, contract, sym))
    qbad = S_QBAD_6E if sym == "6E" else S_QBAD_6B
    bars += fk.flat_bars(qbad, (7, 28), (7, 33), base, 800, contract)
    sessions.append(agg_uniform(qbad, base, contract, sym))
    return fk.panel(sym, contract, sessions, bars, bls_calendar()), base, atr20


def expected(sym: str, base: float, atr: float) -> dict:
    up_fill = round(base + 0.00050, 10)
    dn_fill = round(base - 0.00040, 10)
    return {
        "atr": atr,
        "S_cpi": {"anchor_ct_minute": 450, "release_sign": "UP",
                  "release_move": 0.00050, "spike_ratio": 1.95,
                  "strata": ["KNOWN_CPI"], "entry": up_fill,
                  "exit": round(base + 0.00110, 10),
                  "exit_rule": "TIME_EXIT_1600CT",
                  "sides": {"SC": "BUY", "SD": "SELL"}},
        "S_emp": {"release_sign": "DN", "release_move": -0.00040,
                  "strata": ["KNOWN_EMPSIT"], "entry": dn_fill,
                  "exit": round(base - 0.00070, 10),
                  "exit_rule": "TIME_EXIT_1600CT",
                  "sides": {"SC": "SELL", "SD": "BUY"}},
        "S_canceled": {"status": "NO_TRADE",
                       "blocking": ["CANCELED_NEGATIVE_CONTROL"]},
        "S_other": {"status": "NO_TRADE",
                    "blocking": ["UNCLASSIFIED_830_STRATUM"]},
        "S_double": {"status": "NO_TRADE",
                     "blocking": ["DOUBLE_EVENT_RECLASS_F2"]},
        "S_quiet": {"status": "NO_TRADE",
                    "blocking": ["PIT_VINTAGE_POSTDATED"]},
        "S_qbad": {"status": "NO_TRADE",
                   "blocking": ["NO_EVENT_STAMP",
                                "QUARTER_NOT_OBTAINED_ROLL_ANCHOR"]},
    }


def main():
    manifest = {"family": "FX-F3",
                "proposed": "PROPOSED fixtures; outcome-blind; synthetic only",
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
