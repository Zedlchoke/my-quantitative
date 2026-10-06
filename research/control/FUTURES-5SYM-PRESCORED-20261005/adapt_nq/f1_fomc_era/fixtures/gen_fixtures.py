"""gen_fixtures — builds the committed F1 synthetic panels (deterministic).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python gen_fixtures.py
(then reference_expected.py regenerates EXPECTED_MANIFEST.json).
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
    """Prior sessions engineered to range exactly 60.00 (ATR(20) = 60.00)."""
    return [session_agg(s, open_=base, high=base + 30, low=base - 30, close=base,
                        volume=250_000, rth_core_coverage=1.0, last_bar_ct="15:59",
                        contract=contract)
            for s in weekdays(start, n)]


def fomc_afternoon(session_date: str, contract: str, *, anchor_o: float, anchor_c: float,
                   flat1: float, flat2: float, last_bar: str, final_o: float,
                   final_c: float, end_min: int) -> list[dict]:
    """Anchor bar (13:00) + engineered flat path to the close jump bar."""
    bars = [bar(session_date, 13, 0, anchor_o, max(anchor_o, anchor_c),
                min(anchor_o, anchor_c), anchor_c, 90_000, contract)]
    # bars from 13:01 to (13:00+DELAYS[30]=13:31 exclusive) at flat1
    m = 13 * 60 + 1
    while m < 13 * 60 + 31:
        hh, mm = divmod(m, 60)
        bars.append(bar(session_date, hh, mm, flat1, flat1, flat1, flat1, 8_000, contract))
        m += 1
    # from 13:31 to (last bar) at flat2
    m = 13 * 60 + 31
    while m < end_min - 1:
        hh, mm = divmod(m, 60)
        bars.append(bar(session_date, hh, mm, flat2, flat2, flat2, flat2, 8_000, contract))
        m += 1
    hh, mm = divmod(end_min - 1, 60)
    bars.append(bar(session_date, hh, mm, final_o, max(final_o, final_c),
                    min(final_o, final_c), final_c, 30_000, contract))
    return bars


def main() -> None:
    # ---------------- core panel: June 2023 (UP FOMC day + SHDW Wednesday + H1 day)
    contract = "NQM3_2023"
    sessions = atr_sessions("2023-05-15", 22, 14900.0, contract)  # 05-15..06-13
    sessions += [
        session_agg("2023-06-14", open_=15000.0, high=15050.0, low=15000.0,
                    close=15050.0, volume=1_200_000, rth_core_coverage=1.0,
                    last_bar_ct="15:59", contract=contract),  # FOMC day (bars below)
        session_agg("2023-06-15", open_=14900.0, high=14930.0, low=14870.0,
                    close=14900.0, volume=250_000, rth_core_coverage=1.0,
                    last_bar_ct="15:59", contract=contract),
        session_agg("2023-06-19", open_=14900.0, high=14930.0, low=14870.0,
                    close=14900.0, volume=250_000, rth_core_coverage=1.0,
                    last_bar_ct="15:59", contract=contract),
        session_agg("2023-06-20", open_=14900.0, high=14930.0, low=14870.0,
                    close=14900.0, volume=250_000, rth_core_coverage=1.0,
                    last_bar_ct="15:59", contract=contract),
    ]
    bars = fomc_afternoon(
        "2023-06-14", contract, anchor_o=15000.00, anchor_c=15006.00,
        flat1=15006.25, flat2=15010.00, last_bar="15:59",
        final_o=15010.00, final_c=15050.00, end_min=16 * 60)
    # 2023-06-16 low-coverage session (H1): bars 08:30-10:00 only (91 bars)
    bars += [bar("2023-06-16", hh, mm, 14900.0, 14900.0, 14900.0, 14900.0, 500, contract)
             for hh, mm in [(8, m) for m in range(30, 60)] + [(9, m) for m in range(60)]
             + [(10, 0)]]
    sessions.append(session_agg(
        "2023-06-16", open_=14900.0, high=14900.0, low=14900.0, close=14900.0,
        volume=45_500, rth_core_coverage=91 / 450, last_bar_ct="10:00", contract=contract))
    # 2023-06-21 SHDW Wednesday (bars 13:00-15:59)
    bars += fomc_afternoon(
        "2023-06-21", contract, anchor_o=14900.00, anchor_c=14900.00,
        flat1=14900.25, flat2=14900.25, last_bar="15:59",
        final_o=14900.25, final_c=14930.00, end_min=16 * 60)
    sessions.append(session_agg(
        "2023-06-21", open_=14900.0, high=14930.0, low=14900.0, close=14930.0,
        volume=250_000, rth_core_coverage=1.0, last_bar_ct="15:59", contract=contract))
    core = {"schema": "adapt_nq/synthetic_panel@1", "provenance": "SYNTHETIC",
            "symbol": "NQ", "contract": contract, "family": "NQ-F1",
            "note": "synthetic fixture; engineered prices; not market data",
            "sessions": sessions, "bars": bars,
            "calendar": {"fomc_statements": [
                {"date": "2023-06-14", "time_et": "14:00",
                 "statement_file": "monetary20230614a.html"},
                {"date": "2023-07-26", "time_et": "14:00",
                 "statement_file": "monetary20230726a.html"}],
                "bls_vintage": [], "early_close_not_transcribed": [],
                "quarters_unproven": []}}
    (HERE / "f1_panel_core.json").write_text(json.dumps(core, indent=1), encoding="utf-8")

    # ---------------- July 2023 panel (DN FOMC day)
    contract = "NQU3_2023"
    sessions = atr_sessions("2023-06-26", 21, 15050.0, contract)  # 06-26..07-25
    sessions.append(session_agg(
        "2023-07-26", open_=15100.0, high=15100.0, low=15040.0, close=15040.0,
        volume=1_200_000, rth_core_coverage=1.0, last_bar_ct="15:59", contract=contract))
    bars = fomc_afternoon(
        "2023-07-26", contract, anchor_o=15100.00, anchor_c=15092.00,
        flat1=15091.75, flat2=15088.00, last_bar="15:59",
        final_o=15088.00, final_c=15040.00, end_min=16 * 60)
    dn = {"schema": "adapt_nq/synthetic_panel@1", "provenance": "SYNTHETIC",
          "symbol": "NQ", "contract": contract, "family": "NQ-F1",
          "note": "synthetic fixture; engineered prices; not market data",
          "sessions": sessions, "bars": bars,
          "calendar": {"fomc_statements": [
              {"date": "2023-07-26", "time_et": "14:00",
               "statement_file": "monetary20230726a.html"}],
              "bls_vintage": [], "early_close_not_transcribed": [],
              "quarters_unproven": []}}
    (HERE / "f1_panel_july_dn.json").write_text(json.dumps(dn, indent=1), encoding="utf-8")

    # ---------------- era-boundary panel (2015-09-17 era-A event day)
    contract = "NQU5_2015"
    sessions = atr_sessions("2015-08-19", 21, 14600.0, contract)  # ..2015-09-16
    sessions += [
        session_agg("2015-09-17", open_=14570.0, high=14580.0, low=14570.0,
                    close=14580.0, volume=1_100_000, rth_core_coverage=1.0,
                    last_bar_ct="16:14", contract=contract),  # era-A FOMC day (bars below)
        session_agg("2015-09-18", open_=14600.0, high=14630.0, low=14570.0,
                    close=14600.0, volume=200_000, rth_core_coverage=1.0,
                    last_bar_ct="15:14", contract=contract),  # era-A Friday 15:15 class
        session_agg("2015-09-21", open_=14600.0, high=14630.0, low=14570.0,
                    close=14600.0, volume=250_000, rth_core_coverage=1.0,
                    last_bar_ct="15:59", contract=contract),  # era-B first session
    ]
    bars = fomc_afternoon(
        "2015-09-17", contract, anchor_o=14570.00, anchor_c=14576.00,
        flat1=14576.25, flat2=14576.25, last_bar="16:14",
        final_o=14576.25, final_c=14580.00, end_min=16 * 60 + 15)  # era-A 16:15 close
    era = {"schema": "adapt_nq/synthetic_panel@1", "provenance": "SYNTHETIC",
           "symbol": "NQ", "contract": contract, "family": "NQ-F1",
           "note": "synthetic fixture; era-A (16:15 close) event day + era boundary",
           "sessions": sessions, "bars": bars,
           "calendar": {"fomc_statements": [
               {"date": "2015-09-17", "time_et": "14:00",
                "statement_file": "monetary20150917a.html"}],
               "bls_vintage": [], "early_close_not_transcribed": [],
               "quarters_unproven": []}}
    (HERE / "f1_panel_era_boundary.json").write_text(json.dumps(era, indent=1),
                                                     encoding="utf-8")

    # ---------------- 2026/H4 exclusions panel (aggregate-only)
    sessions = [
        session_agg("2026-01-16", open_=25000.0, high=25030.0, low=24970.0,
                    close=25000.0, volume=300_000, rth_core_coverage=1.0,
                    last_bar_ct="15:59", contract="NQH6_2026"),
        session_agg("2026-01-19", open_=25000.0, high=25010.0, low=24990.0,
                    close=25000.0, volume=80_000, rth_core_coverage=0.35,
                    last_bar_ct="11:00", contract="NQH6_2026"),
        session_agg("2026-01-20", open_=25000.0, high=25030.0, low=24970.0,
                    close=25000.0, volume=300_000, rth_core_coverage=1.0,
                    last_bar_ct="15:59", contract="NQH6_2026"),
        session_agg("2023-11-24", open_=15500.0, high=15510.0, low=15490.0,
                    close=15500.0, volume=60_000, rth_core_coverage=0.2,
                    last_bar_ct="12:00", contract="NQZ3_2023"),
    ]
    excl = {"schema": "adapt_nq/synthetic_panel@1", "provenance": "SYNTHETIC",
            "symbol": "NQ", "contract": "SYNTH-MIX", "family": "NQ-F1",
            "note": "synthetic fixture; 2026 dubious days + H4 NOT_TRANSCRIBED day",
            "sessions": sessions, "bars": [],
            "calendar": {"fomc_statements": [], "bls_vintage": [],
                         "early_close_not_transcribed": ["2023-11-24"],
                         "quarters_unproven": []}}
    (HERE / "f1_panel_exclusions_2026.json").write_text(json.dumps(excl, indent=1),
                                                        encoding="utf-8")
    print("F1 fixtures written to", HERE)


if __name__ == "__main__":
    main()
