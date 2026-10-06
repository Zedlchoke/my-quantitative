"""gen_fixtures — builds the committed F2 synthetic panels (deterministic).

Run (from adapt_nq/): PYTHONPATH=. ../../.venv/bin/python f2_macro_0730/fixtures/gen_fixtures.py
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from fixture_kit import bar, session_agg

HERE = Path(__file__).resolve().parent


def weekdays(start: str, n: int) -> list[str]:
    out, d = [], date.fromisoformat(start)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def atr_sessions(start: str, n: int, base: float, contract: str) -> list[dict]:
    return [session_agg(s, open_=base, high=base + 30, low=base - 30, close=base,
                        volume=250_000, rth_core_coverage=1.0, last_bar_ct="15:59",
                        contract=contract)
            for s in weekdays(start, n)]


def cpi_day(session_date: str, contract: str, *, anchor_o: float, anchor_c: float,
            flat1: float, tp_bar: dict | None, flat2: float, final_o: float,
            final_c: float) -> list[dict]:
    """Bars 07:30..15:59: anchor 07:30, flat to 07:36 (flat1), optional engineered
    TP-touch bar at 07:37, flat (flat2) 07:38..15:58, close-jump bar 15:59."""
    bars = [bar(session_date, 7, 30, anchor_o, max(anchor_o, anchor_c),
                min(anchor_o, anchor_c), anchor_c, 90_000, contract)]
    for m in range(7 * 60 + 31, 7 * 60 + 37):
        hh, mm = divmod(m, 60)
        bars.append(bar(session_date, hh, mm, flat1, flat1, flat1, flat1, 8_000, contract))
    if tp_bar is not None:
        bars.append(bar(session_date, 7, 37, tp_bar["o"], tp_bar["h"], tp_bar["l"],
                        tp_bar["c"], 120_000, contract))
        start2 = 7 * 60 + 38
    else:
        start2 = 7 * 60 + 37
    for m in range(start2, 16 * 60 - 1):
        hh, mm = divmod(m, 60)
        bars.append(bar(session_date, hh, mm, flat2, flat2, flat2, flat2, 8_000, contract))
    bars.append(bar(session_date, 15, 59, final_o, max(final_o, final_c),
                    min(final_o, final_c), final_c, 30_000, contract))
    return bars


def main() -> None:
    contract = "NQM3_2023"
    sessions = atr_sessions("2023-05-15", 20, 14900.0, contract)  # 05-15..06-12
    sessions += [
        session_agg("2023-06-13", open_=15000.0, high=15150.0, low=15000.0,
                    close=15150.0, volume=1_400_000, rth_core_coverage=1.0,
                    last_bar_ct="15:59", contract=contract),  # CPI UP (bars below)
        session_agg("2023-06-14", open_=14900.0, high=14930.0, low=14870.0,
                    close=14900.0, volume=250_000, rth_core_coverage=1.0,
                    last_bar_ct="15:59", contract=contract),  # FOMC day (no CPI row)
        session_agg("2023-06-15", open_=15000.0, high=15030.0, low=15000.0,
                    close=15030.0, volume=250_000, rth_core_coverage=1.0,
                    last_bar_ct="15:59", contract=contract),  # SHDW clock day (bars below)
    ]
    # 06-16..07-11 weekdays, skipping the 2023-07-04 holiday (17 aggregates,
    # range 60 each) — gives exactly 20 priors for the 2023-07-12 CPI day
    fixed = ["2023-06-16", "2023-06-19", "2023-06-20", "2023-06-21",
             "2023-06-22", "2023-06-23", "2023-06-26", "2023-06-27",
             "2023-06-28", "2023-06-29", "2023-06-30", "2023-07-03",
             "2023-07-05", "2023-07-06", "2023-07-07", "2023-07-10",
             "2023-07-11"]
    sessions += [session_agg(
        s, open_=14900.0, high=14930.0, low=14870.0, close=14900.0, volume=250_000,
        rth_core_coverage=1.0, last_bar_ct="15:59", contract=contract) for s in fixed]
    sessions.append(session_agg(
        "2023-07-12", open_=15100.0, high=15100.0, low=15040.0, close=15040.0,
        volume=1_400_000, rth_core_coverage=1.0, last_bar_ct="15:59",
        contract=contract))  # CPI DN (bars below)
    sessions.append(session_agg(
        "2023-09-13", open_=14900.0, high=14930.0, low=14870.0, close=14900.0,
        volume=250_000, rth_core_coverage=1.0, last_bar_ct="15:59",
        contract=contract))  # CPI-on-FOMC day (aggregate only)

    bars = cpi_day("2023-06-13", contract, anchor_o=15000.00, anchor_c=15006.00,
                   flat1=15006.25,
                   tp_bar={"o": 15006.25, "h": 15126.50, "l": 15006.25, "c": 15126.50},
                   flat2=15130.00, final_o=15130.00, final_c=15150.00)
    bars += cpi_day("2023-06-15", contract, anchor_o=15000.00, anchor_c=15000.00,
                    flat1=15000.25, tp_bar=None, flat2=15000.25,
                    final_o=15000.25, final_c=15030.00)
    bars += cpi_day("2023-07-12", contract, anchor_o=15100.00, anchor_c=15092.00,
                    flat1=15091.75, tp_bar=None, flat2=15091.75,
                    final_o=15091.75, final_c=15040.00)

    core = {"schema": "adapt_nq/synthetic_panel@1", "provenance": "SYNTHETIC",
            "symbol": "NQ", "contract": contract, "family": "NQ-F2",
            "note": "synthetic fixture; engineered prices; not market data",
            "sessions": sessions, "bars": bars,
            "calendar": {
                "fomc_statements": [
                    {"date": "2023-06-14", "time_et": "14:00",
                     "statement_file": "monetary20230614a.html"},
                    {"date": "2023-09-13", "time_et": "14:00",
                     "statement_file": "monetary20230913a.html"}],
                "bls_vintage": [
                    {"series": "CPI", "scheduled_date": "2023-06-13",
                     "known_by": "2023-05-10", "status": "scheduled"},
                    {"series": "CPI", "scheduled_date": "2023-07-12",
                     "known_by": "2023-06-09", "status": "scheduled"},
                    {"series": "CPI", "scheduled_date": "2023-09-13",
                     "known_by": "2023-08-11", "status": "scheduled"},
                    {"series": "EMPSIT", "scheduled_date": "2023-06-02",
                     "known_by": "2023-05-05", "status": "scheduled"}],
                "early_close_not_transcribed": [], "quarters_unproven": []}}
    (HERE / "f2_panel_core.json").write_text(json.dumps(core, indent=1), encoding="utf-8")

    # ---- era-gated 2019 CPI day (aggregate only; outside 2023-26 scoring era)
    sessions = atr_sessions("2019-05-13", 20, 7400.0, "NQH9_2019")
    sessions.append(session_agg(
        "2019-06-12", open_=7400.0, high=7430.0, low=7370.0, close=7400.0,
        volume=250_000, rth_core_coverage=1.0, last_bar_ct="15:59", contract="NQH9_2019"))
    era = {"schema": "adapt_nq/synthetic_panel@1", "provenance": "SYNTHETIC",
           "symbol": "NQ", "contract": "NQH9_2019", "family": "NQ-F2",
           "note": "synthetic fixture; pre-scoring-era CPI day (era gate)",
           "sessions": sessions, "bars": [],
           "calendar": {"fomc_statements": [], "bls_vintage": [
               {"series": "CPI", "scheduled_date": "2019-06-12",
                "known_by": "2019-05-10", "status": "scheduled"}],
               "early_close_not_transcribed": [], "quarters_unproven": []}}
    (HERE / "f2_panel_era_gated_2019.json").write_text(json.dumps(era, indent=1),
                                                       encoding="utf-8")

    # ---- canceled-expected 2025 CPI day (lapse-anomaly stratum)
    sessions = atr_sessions("2025-09-15", 20, 24500.0, "NQZ5_2025")
    sessions.append(session_agg(
        "2025-10-15", open_=24500.0, high=24530.0, low=24470.0, close=24500.0,
        volume=120_000, rth_core_coverage=1.0, last_bar_ct="15:59", contract="NQZ5_2025"))
    canceled = {"schema": "adapt_nq/synthetic_panel@1", "provenance": "SYNTHETIC",
                "symbol": "NQ", "contract": "NQZ5_2025", "family": "NQ-F2",
                "note": "synthetic fixture; canceled-but-expected CPI day (NC-6b stratum)",
                "sessions": sessions, "bars": [],
                "calendar": {"fomc_statements": [], "bls_vintage": [
                    {"series": "CPI", "scheduled_date": "2025-10-15",
                     "known_by": "2025-09-30", "status": "canceled"}],
                    "early_close_not_transcribed": [], "quarters_unproven": []}}
    (HERE / "f2_panel_canceled_2025.json").write_text(json.dumps(canceled, indent=1),
                                                      encoding="utf-8")

    # ---- 2026 panel carrying the D5 pin (CPI 2026-02-13)
    sessions = atr_sessions("2026-01-12", 20, 25000.0, "NQH6_2026")
    sessions.append(session_agg(
        "2026-02-13", open_=25000.0, high=25030.0, low=24970.0, close=25000.0,
        volume=1_400_000, rth_core_coverage=1.0, last_bar_ct="15:59",
        contract="NQH6_2026"))
    p2026 = {"schema": "adapt_nq/synthetic_panel@1", "provenance": "SYNTHETIC",
             "symbol": "NQ", "contract": "NQH6_2026", "family": "NQ-F2",
             "note": "synthetic fixture; D5-pin day 2026-02-13 (aggregate only)",
             "sessions": sessions, "bars": [],
             "calendar": {"fomc_statements": [], "bls_vintage": [
                 {"series": "CPI", "scheduled_date": "2026-02-13",
                  "known_by": "2026-01-14", "status": "scheduled"}],
                 "early_close_not_transcribed": [], "quarters_unproven": []}}
    (HERE / "f2_panel_2026_d5.json").write_text(json.dumps(p2026, indent=1),
                                                encoding="utf-8")
    print("F2 fixtures written to", HERE)


if __name__ == "__main__":
    main()
