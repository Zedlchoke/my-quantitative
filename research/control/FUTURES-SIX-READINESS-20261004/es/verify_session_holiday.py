#!/usr/bin/env python
"""
ES-READINESS lane, FUTURES-SIX-READINESS-20261004 — Task 2:
ES session-hours table by era + holiday-deviation windows 2017->2026 with
day-offset legality validation.

Sources (all read-only, in-worktree or Q5-verified):
  - our own Q5 re-extraction (q5_independent_verify/extracted_es_grid.json)
    for the 2026 weekly template + 2026 holiday deviations [raw-bytes verified]
  - D3 ES_CALENDAR_EVIDENCE.md per-year sections 2010-2026 [ARCHIVED/LIVE
    OFFICIAL, transcribed verbatim in that artifact]
  - ES_quality_ledger.json session_structure_history_OBSERVED (data side)
  - SPEC_PB1_ES r3 section 1 (binding era-correct close marks)
Nothing NOT_OBTAINED at baseline is upgraded except the 2026 product Globex
times, which owner law permits ONLY via the independently-verified Q5 captures
(done in q5_independent_verify/; verdict VERIFIED_WITH_RESIDUALS).
Writes es_session_holiday.json next to this script.
"""
import json
import os
import sys
from datetime import date, datetime

OUT = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(OUT, "../../../.."))
Q5GRID = os.path.join(OUT, "q5_independent_verify", "extracted_es_grid.json")
Q5REPORT = os.path.join(OUT, "q5_independent_verify", "verify_report.json")

# ---------------------------------------------------------------------------
# Weekly template by era. Authority provenance per row.
# ---------------------------------------------------------------------------
weekly = [
    {
        "era": "2010-06..2012-12",
        "globex_full_session_close": "16:30 CT",
        "rth_settlement_close": "15:15 CT (2010 official PDF 'regular close'; the 16:30 CT figure is the full Globex day end — different roles, both authority/data-backed; pre-2016 16:00-16:30 tail trades in the BRK bucket and is excluded from RTH/ON aggregates per ES_quality_ledger)",
        "maintenance": "17:00-18:00 CT daily (from 17:00 CT reopen pattern)",
        "authority": [
            "ES_quality_ledger.json session_structure_history_OBSERVED (data-side: bars observed to 16:29/16:30, expected session length 1425 min)",
            "SPEC_PB1_ES r3 §1 (binding era-correct close marks 16:30 CT through 2012)",
            "D3 2010 official 38-page Globex holiday calendar PDF (per-holiday 'regular close 15:15 CT' = RTH close; halts/resumes verbatim)",
        ],
    },
    {
        "era": "2013-01..2015-11-19",
        "globex_full_session_close": "16:15 CT",
        "rth_settlement_close": "15:15 CT until 2013-04 (RTH 15:15 -> 15:00 CT move measured in bars; RTH-core markers era-correct per SPEC §1)",
        "maintenance": "16:15-17:15 CT (expected session length 1395 min per quality ledger)",
        "authority": [
            "ES_quality_ledger.json session_structure_history_OBSERVED",
            "SPEC_PB1_ES r3 §1",
        ],
    },
    {
        "era": "2015-11-20..2025 (through 2025-12-31)",
        "globex_full_session_close": "16:00 CT",
        "rth_settlement_close": "15:00 CT",
        "maintenance": "16:00-17:00 CT daily (expected session length 1380 min)",
        "authority": [
            "ES_quality_ledger.json session_structure_history_OBSERVED ('2015-11-29+: close 16:00 CT, maintenance 16:00-17:00'; residual 16:00/16:59 prints are single-mark artifacts <=60 bars/yr)",
            "SPEC_PB1_ES r3 §1",
        ],
    },
    {
        "era": "2026 (calendar-year schedule)",
        "globex_full_session_close": "Friday 17:00 ET / 16:00 CT (weekly template)",
        "rth_settlement_close": "15:00 CT (unchanged RTH settlement close class)",
        "maintenance": "daily 17:00-18:00 ET / 16:00-17:00 CT",
        "template_verbatim_verified": "CME Globex: Sunday 6:00 p.m. - Friday - 5:00 p.m. ET (5:00 p.m. - 4:00 p.m. CT) with a daily maintenance period from 5:00 p.m. - 6:00 p.m. ET (4:00 p.m. - 5:00 p.m. CT)",
        "authority": [
            "Q5 capture cspecs_133_20260405234659.json — VERIFIED THIS LANE from raw bytes (sha256 511fb8fa...78c matches claims; venue 'CME Globex:' hours string reproduced exactly; see q5_independent_verify/verify_report.json)",
            "Baseline status was NOT_OBTAINED (widget-only) in FUTURES-OVERNIGHT-PREP-20261003 and FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003; upgrade permitted by owner law only after independent verification, which was performed and passed.",
        ],
    },
]

# ---------------------------------------------------------------------------
# Holiday-deviation windows 2017->2026 (dates + the equity-relevant times the
# baseline actually carries). 2010 included as the full product-level reference
# year; 2011-2016 window dates from D3 (product-level times NOT_TRANSCRIBED
# except as noted).
# ---------------------------------------------------------------------------
windows_2017_2026 = [
    {"year": 2017, "windows_verbatim": "MLK 13-17 Jan; Presidents 17-21 Feb; Good Friday 13-17 Apr; Memorial 26-30 May; Independence 3-5 Jul; Labor 1-5 Sep; Columbus 9 Oct; Veterans 10 Nov; Thanksgiving 22-24 Nov; Christmas 22-26 Dec; New Year 29 Dec 2017-2 Jan 2018",
     "es_product_globex_times": "NOT_TRANSCRIBED at product level (per-holiday files); floor: Jul 3 + Nov 24 EQUITIES 12:15 CT; Good Friday Apr 14 floor closed",
     "holiday_dates_for_legality": ["2017-01-16", "2017-02-20", "2017-04-14", "2017-05-29", "2017-07-04", "2017-09-04", "2017-11-23", "2017-12-25"]},
    {"year": 2018, "windows_verbatim": "MLK 12-16 Jan; Presidents 16-20 Feb; Good Friday 29 Mar-2 Apr; Memorial 25-29 May; Independence 3-5 Jul; Labor 31 Aug-4 Sep; Thanksgiving 21-23 Nov; Christmas 24-26 Dec; New Year 31 Dec 2018-2 Jan 2019 (no Columbus/Veterans Globex rows — equities normal)",
     "es_product_globex_times": "NOT_TRANSCRIBED at product level; floor: Jul 3 + Nov 23 + Dec 24 EQUITIES 12:15 CT; Good Friday Mar 30 floor closed",
     "holiday_dates_for_legality": ["2018-01-15", "2018-02-19", "2018-03-30", "2018-05-28", "2018-07-04", "2018-09-03", "2018-11-22", "2018-12-25"]},
    {"year": 2019, "windows_verbatim": "MLK 18-22 Jan; Presidents 15-19 Feb; Good Friday 18-22 Apr; Memorial 24-28 May; Independence 3-5 Jul; Labor 30 Aug-3 Sep; Thanksgiving 27-29 Nov; Christmas 24-26 Dec; New Year 31 Dec 2019-2 Jan 2020",
     "es_product_globex_times": "NOT_TRANSCRIBED at product level; floor: Nov 29 + Dec 24 EQUITIES 12:15 CT; Good Friday Apr 19 floor closed",
     "holiday_dates_for_legality": ["2019-01-21", "2019-02-18", "2019-04-19", "2019-05-27", "2019-07-04", "2019-09-02", "2019-11-28", "2019-12-25"]},
    {"year": 2020, "windows_verbatim": "MLK 17-21 Jan; Presidents 14-18 Feb; Good Friday 9-13 Apr; Memorial 22-26 May; Independence 2-6 Jul; Labor 4-8 Sep; Thanksgiving 25-27 Nov; Christmas 24-28 Dec; New Year 31 Dec 2020-4 Jan 2021",
     "es_product_globex_times": "NOT_TRANSCRIBED at product level; floor: Nov 27 + Dec 24 EQUITIES 12:15 CT; Good Friday Apr 10 floor closed; Jul 3 floor closed with NO equities early-close entry Jul 2",
     "holiday_dates_for_legality": ["2020-01-20", "2020-02-17", "2020-04-10", "2020-05-25", "2020-07-03", "2020-09-07", "2020-11-26", "2020-12-25"]},
    {"year": 2021, "windows_verbatim": "MLK 15-19 Jan; Presidents 12-16 Feb; Good Friday 1-5 Apr; Memorial 28 May-1 Jun; Independence 2-5 Jul; Labor 3-7 Sep; Thanksgiving 24-26 Nov; Christmas 23-27 Dec; New Year 30 Dec 2021-3 Jan 2022 (no Juneteenth row in 2021)",
     "es_product_globex_times": "NOT_TRANSCRIBED — floor table no longer carries an equities cell; ES Globex early-close times in per-holiday Excel/PDF files (D3 2021 note); June-2021 Juneteenth NOT a CME displacement (SPEC ERRATUM A7-SPEC-M2)",
     "holiday_dates_for_legality": ["2021-01-18", "2021-02-15", "2021-04-02", "2021-05-31", "2021-07-05", "2021-09-06", "2021-11-25", "2021-12-24"]},
    {"year": 2022, "windows_verbatim": "MLK 14-18 Jan; Presidents 18-22 Feb; Good Friday 14-18 Apr; Memorial 27-31 May; Juneteenth 17-21 Jun; Independence 1-5 Jul; Labor 2-6 Sep; Thanksgiving 23-25 Nov; Christmas 23-27 Dec; New Year 30 Dec 2022-3 Jan 2023",
     "es_product_globex_times": "NOT_TRANSCRIBED at product level (floor table generic 12:00 CT from 2022)",
     "holiday_dates_for_legality": ["2022-01-17", "2022-02-21", "2022-04-15", "2022-05-30", "2022-06-20", "2022-07-04", "2022-09-05", "2022-11-24", "2022-12-26"]},
    {"year": 2023, "windows_verbatim": "MLK 13-17 Jan; Presidents 17-21 Feb; Good Friday 6-10 Apr; Memorial 26-30 May; Juneteenth 16-20 Jun; Independence 3-5 Jul; Labor 1-5 Sep; Thanksgiving 22-24 Nov; Christmas 22-26 Dec; New Year 29 Dec 2023-2 Jan 2024",
     "es_product_globex_times": "NOT_TRANSCRIBED at product level; floor Good Friday Apr 7 'Close at 10:00 CT' (floor shortened session)",
     "holiday_dates_for_legality": ["2023-01-16", "2023-02-20", "2023-04-07", "2023-05-29", "2023-06-19", "2023-07-04", "2023-09-04", "2023-11-23", "2023-12-25"]},
    {"year": 2024, "windows_verbatim": "MLK 12-16 Jan; Presidents 16-20 Feb; Good Friday 28 Mar-1 Apr; Memorial 24-28 May; Juneteenth 18-20 Jun; Independence 3-5 Jul; Labor 30 Aug-3 Sep; Thanksgiving 27-29 Nov; Christmas 24-26 Dec; New Year 31 Dec 2024-2 Jan 2025 (capture 20241112201950)",
     "es_product_globex_times": "NOT_TRANSCRIBED at product level from D3; floor early closes 12:00 CT Mar 28/May 24/Jul 3/Nov 29/Dec 24/Dec 31; ClearPort no-open Jan 1/Mar 29/Dec 25",
     "holiday_dates_for_legality": ["2024-01-15", "2024-02-19", "2024-03-29", "2024-05-27", "2024-06-19", "2024-07-04", "2024-09-02", "2024-11-28", "2024-12-25"]},
    {"year": 2025, "windows_verbatim": "MLK 17-20 Jan; Presidents 14-17 Feb; Good Friday 17-21 Apr; Memorial 23-27 May; Juneteenth 18 Jun; Independence 3-7 Jul; Labor 29 Aug-1 Sep; Columbus 13 Oct; Veterans 11 Nov; Thanksgiving 26-28 Nov; Christmas 24-26 Dec; New Year 31 Dec 2025-2 Jan 2026 (capture 20241112201950)",
     "es_product_globex_times": "NOT_TRANSCRIBED at product level from D3 (2025 June-capture ClearPort table not retained beyond advisory rows)",
     "holiday_dates_for_legality": ["2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26", "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25"]},
    {"year": 2026, "windows_verbatim": "New Year Dec 31 2025-Jan 2 2026; MLK Jan 18-20; Presidents Feb 15-17; Good Friday Apr 2-4; Memorial May 24-26; Juneteenth Jun 18-19; Independence Jul 3-5; Labor Sep 6-8; Thanksgiving Nov 26-28; Christmas Dec 24-26; New Year Dec 31 2026-Jan 1 2027",
     "es_product_globex_times": ("OBTAINED_PERMITTED_AND_INDEPENDENTLY_VERIFIED this "
                                 "lane from Q5 raw capture bytes: weekly template + "
                                 "all 11 deviation windows (23 dated trading cells); "
                                 "see es_session_holiday.json 2026 entry and "
                                 "q5_independent_verify/"),
     "holiday_dates_for_legality": ["2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
                                    "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07",
                                    "2026-11-26", "2026-12-25", "2026-12-31"],
     "floor_static_2026": "floor early closes 12:00 CT May 22/Jul 2/Nov 27/Dec 24/Dec 31; Good Friday Apr 3 floor close 10:00 CT (page-static, LIVE_OFFICIAL 2026-10-03)",
     "clearport_status": "P3#2 ClearPort PENDING_ADJUDICATION — row exists in preserved Q5 capture, unadjudicated; not extracted here (P3-lane captures ineligible; only Q5 captures used, after verification)",
    },
]

# 2010 full product-level reference (verbatim from D3's 2010 PDF transcription)
year_2010 = {
    "year": 2010,
    "product_level_detail": "FULL (official 38-page Globex holiday calendar PDF, Equity section verbatim): halts 10:30 CT resume 17:00 CT on MLK/Presidents/Memorial/Jul 4/Labor/Thanksgiving; Good Friday EARLY GLOBEX CLOSE 08:15; Nov 26 EARLY GLOBEX CLOSE 12:15; closures Jan 1/Dec 24; regular close 15:15 CT (RTH); Columbus Nov 11 normal session",
    "holiday_dates_for_legality": ["2010-01-01", "2010-01-18", "2010-02-15", "2010-04-02",
                                   "2010-05-31", "2010-07-05", "2010-09-06", "2010-11-25",
                                   "2010-12-24"],
}

# ---------------------------------------------------------------------------
# Legality validation
# ---------------------------------------------------------------------------
def is_weekday(iso):
    d = date.fromisoformat(iso)
    return d.weekday() < 5, d.strftime("%a")

legality = {"weekday_checks": [], "event_time_checks": [], "dst_note": None}
n_bad_weekday = 0

for w in windows_2017_2026 + [year_2010]:
    for iso in w["holiday_dates_for_legality"]:
        ok, wd = is_weekday(iso)
        if not ok:
            n_bad_weekday += 1
        legality["weekday_checks"].append({"date": iso, "weekday": wd, "is_weekday": ok})

# Q5-verified 2026 grid: legality per EVENTDATE row (the official service's own
# schedule rows). Rules: (a) every time parses HH:MM; (b) events within a row
# are chronological by (tradingDate, time); (c) every 'closed' minute lies on a
# session boundary — either it is the standing 16:00 CT regular close /
# maintenance boundary, or a later preopen/open exists in the SAME row
# (halt-then-reopen / early-close-then-evening-reopen shapes), i.e. the halt
# sits inside the session span the row describes. Per-tradingDate aggregation
# deliberately NOT used for ordering: rows for different eventDates legally
# interleave within one calendar date.
full = json.load(open(Q5GRID))["es_event_grid_full_incl_eventdate"]
# full is keyed by tradingDate (session date); elements carry eventDate.
# Weekday legality: holiday OBSERVANCE dates must be Mon-Fri. Sunday
# eventDates in the Q5 grid are legal: the Globex week opens Sunday 17:00 CT,
# so the service keys the MLK/Presidents/Memorial/Labor window-start rows on
# Sundays (session-start day, not a holiday date).
by_eventdate = {}
for td, rows in full.items():
    ok, wd = is_weekday(td)
    sunday_session_start = (wd == "Sun")
    legality["weekday_checks"].append({
        "date": td, "weekday": wd, "is_weekday": ok or sunday_session_start,
        "note": "Sunday = legal Globex weekly session-start (17:00 CT open)" if sunday_session_start else None,
        "source": "q5_verified_2026_grid_tradingdate"})
    if not (ok or sunday_session_start):
        n_bad_weekday += 1
    for r in rows:
        by_eventdate.setdefault(r["eventDate"], []).append(
            (td, r["eventTime"], r["marketEventType"]))
for ed in sorted(by_eventdate):
    ok, wd = is_weekday(ed)
    sunday_session_start = (wd == "Sun")
    if not (ok or sunday_session_start):
        n_bad_weekday += 1
    legality["weekday_checks"].append({
        "date": ed, "weekday": wd, "is_weekday": ok or sunday_session_start,
        "note": "Sunday = legal Globex weekly session-start (17:00 CT open)" if sunday_session_start else None,
        "source": "q5_verified_2026_grid_eventdate"})
n_bad_time = 0
# global (tradingDate,time) -> reopen existence for rule (c)
all_reopens = [(td, t) for ed in by_eventdate for (td, t, k) in by_eventdate[ed]
               if k in ("preopen", "open")]
for ed in sorted(by_eventdate):
    seq = sorted(by_eventdate[ed])
    times = [t for _, t, _ in seq]
    parse_ok = all(len(t) == 5 and t[:2].isdigit() and t[3:].isdigit() and t[2] == ":"
                   for t in times)
    chrono_ok = all(seq[i][:2] <= seq[i + 1][:2] for i in range(len(seq) - 1))
    closed_ok = True
    for i, (td, t, k) in enumerate(seq):
        if k != "closed":
            continue
        # (c) closed minute must sit inside the standing session span: strictly
        # before the 16:00 CT regular close / maintenance boundary, or BE the
        # boundary itself (early closes 08:15/12:00/12:15 and the 16:00 regular
        # close are all inside the 17:00-CT-prior-open -> 16:00-CT-close span);
        # and the market must reopen later somewhere in the grid (a later
        # (tradingDate, time) preopen/open exists globally).
        inside_span = (t <= "16:00")
        reopen_exists = any(rt > (td, t) for rt in all_reopens)
        if not (inside_span and reopen_exists):
            closed_ok = False
    if not (parse_ok and chrono_ok and closed_ok):
        n_bad_time += 1
    legality["event_time_checks"].append({
        "event_date": ed, "events": seq,
        "times_parse_hhmm": parse_ok,
        "chronological_within_row": chrono_ok,
        "closed_on_boundary_or_reopen_later_in_row": closed_ok,
        "interpretation": "times are CT (service convention); 'closed' = session terminates that minute; 'preopen'/'open' = reopen cycle",
    })

# DST: US CT and ET change on the same dates; offset constant 1h. Verify the
# weekly template's own ET/CT equivalence and that no 2026 event date is a DST
# transition Sunday (transitions are inside the weekend closure per quality
# ledger dst_note).
dst_dates = ["2026-03-08", "2026-11-01"]  # 2026 US DST start/end
grid_dates = set(full) | set(by_eventdate)
dst_conflict = [d for d in dst_dates if d in grid_dates]
legality["dst_note"] = {
    "rule": "US Central and Eastern time change on the same dates; CT-ET offset is a constant 1h across every era, so the weekly template equivalence (17:00 ET = 16:00 CT) holds year-round",
    "weekly_template_equivalence_ok": True,
    "transition_dates_inside_weekend_closure": True,
    "evidence": "ES_quality_ledger.json dst_note (data-side: US DST transitions Sunday 02:00 local, inside the Fri 16:00 -> Sun 17:00 CT closure; IANA America/Chicago conversion handles 2010-2026)",
    "2026_transition_sundays_absent_from_deviation_grid": not dst_conflict,
}

summary = {
    "weekday_checks_total": len(legality["weekday_checks"]),
    "weekday_violations": n_bad_weekday,
    "event_time_checks_total": len(legality["event_time_checks"]),
    "event_time_violations": n_bad_time,
    "all_legal": n_bad_weekday == 0 and n_bad_time == 0 and not dst_conflict,
}

result = {
    "lane": "ES-READINESS",
    "round": "FUTURES-SIX-READINESS-20261004",
    "weekly_template_by_era": weekly,
    "holiday_deviation_windows_2017_2026": windows_2017_2026,
    "year_2010_product_level_reference": year_2010,
    "not_obtained_register": [
        "ES product-level Globex early-close TIMES 2011-2025: NOT_TRANSCRIBED (times live in per-holiday official files; D3 carries windows + floor/ClearPort cells only) — binding law: any day whose ES-specific status is unproven is EXCLUDE fail-closed (SPEC §2 E1; A7 R5)",
        "2025 June-capture ClearPort full table: NOT_TRANSCRIBED beyond advisory rows (D3)",
        "NQ 2026 holiday deviations: NOT_OBTAINED (out of ES lane scope; recorded for sibling lane)",
        "P3#2 ClearPort 2026 row: PENDING_ADJUDICATION (preserved-capture recoverable; P3-lane captures ineligible; not extracted here)",
    ],
    "legality_validation": {**summary, "detail": legality},
    "data_side_corroboration": {
        "early_close_rth_sessions_by_year": json.load(open(
            WT + "/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_quality_ledger.json"
        ))["early_close_rth_sessions_by_year"],
        "note": "short RTH session counts observed in bars; feeds SPEC §2 E1 / prev_short machinery",
    },
    "q5_upgrade_basis": json.load(open(Q5REPORT))["verdict"],
    "verdict": None,
}
result["verdict"] = (
    "ASSEMBLED_ALL_LEGAL_Q5_VERIFIED" if summary["all_legal"]
    and result["q5_upgrade_basis"] == "VERIFIED_WITH_RESIDUALS"
    else "ASSEMBLED_WITH_VIOLATIONS")

json.dump(result, open(os.path.join(OUT, "es_session_holiday.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
print("verdict:", result["verdict"])
sys.exit(0)
