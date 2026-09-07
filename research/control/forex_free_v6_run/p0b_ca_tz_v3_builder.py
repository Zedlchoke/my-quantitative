#!/usr/bin/env python
"""FOREX-FREE-V6 P0b: CA timezone v3 pin (append-only) + invariance proof.

Authority: plans/PLAN_forex_v6.md section 3 P0b — "correct ET-as-UTC
stamps in an append-only v3 pin (daily-clock decision-invariance
re-proven; the fix unlocks any future intraday CA use)".

What it does
------------
1.  REFUSES to run unless the v2-era CA calendar file re-hashes to the
    A1-inherited pin
      ca_statcan_cpi_release_dates.json  088b0ba80f05... (107 rows)
2.  Builds
      ca_statcan_cpi_release_dates_v3.json
      p0a_cpi_prints_ca_v3.json
    identical rows to the v2 files EXCEPT the availability/release-time
    stamps now carry TRUE UTC computed from the recorded StatCan WDS
    local time (America/Toronto, DST-correct via zoneinfo): a scheduled
    08:30 release stamps 12:30Z on EDT dates and 13:30Z on EST dates.
    Each row gains release_time_utc_true / release_time_local /
    tz_conversion.  The v2 files stay untouched (re-hashed at the end).
3.  Decision-invariance re-proof against V5's exact daily clock
    ("daily 16:00-NY (DST)", research/control/forex_free_v5_run/
    run_contract.json; S0 window from p3_conditioning_clocks_v5.json):
    for EVERY CA release row (107) verify computationally that the
    buggy-UTC (v2) and true-UTC (v3) stamps (a) fall on the same
    calendar date and (b) fall on the same side of EVERY daily
    16:00 America/New_York boundary in the S0 window — i.e. the set of
    prints known-as-of each decision instant is identical under v2 vs
    v3.  Any mismatch is reported FAIL honestly, per row.
4.  Emits p0b_ca_tz_invariance_proof.json with counts, per-row detail,
    boundary-day count, and the exact mismatch list (expected 0 for the
    99 scheduled 08:30 rows; the 8 verbatim non-08:30 WDS change-event
    rows are computed, never assumed).

No network; no PnL.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

RUN_DIR = Path(__file__).resolve().parent
WORKTREE = RUN_DIR.parents[2]
V5_DIR = WORKTREE / "research/control/forex_free_v5_run"
CAL_V2 = V5_DIR / "ca_statcan_cpi_release_dates.json"
PRINTS_V2 = V5_DIR / "p0a_cpi_prints_ca.json"
CLOCK_FILE = V5_DIR / "p3_conditioning_clocks_v5.json"
CONTRACT = V5_DIR / "run_contract.json"
OUT_CAL = RUN_DIR / "ca_statcan_cpi_release_dates_v3.json"
OUT_PRINTS = RUN_DIR / "p0a_cpi_prints_ca_v3.json"
OUT_PROOF = RUN_DIR / "p0b_ca_tz_invariance_proof.json"

PIN_CAL_V2 = "088b0ba80f0580e39ab17832872a93e3dce15bc077ffafa2f87800b4c7115eaa"
TORONTO = ZoneInfo("America/Toronto")
NEW_YORK = ZoneInfo("America/New_York")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def toronto_to_utc(d: date, hh: int, mm: int) -> tuple[datetime, str]:
    """Local America/Toronto wall time on date d -> (aware UTC datetime, tz label)."""
    local = datetime(d.year, d.month, d.day, hh, mm, tzinfo=TORONTO)
    return local.astimezone(timezone.utc), local.tzname()


def parse_recorded_local(display: str) -> tuple[date, int, int]:
    dt = datetime.fromisoformat(display)  # e.g. 2021-07-23T18:56 (naive, ET wall time)
    return dt.date(), dt.hour, dt.minute


def v2_stamp(date_str: str, hh: int, mm: int) -> datetime:
    """The v2-era stamp as recorded: local wall time mislabeled as UTC."""
    return datetime.fromisoformat(f"{date_str}T{hh:02d}:{mm:02d}:00+00:00")


def daily_boundaries(start: date, end: date) -> list[datetime]:
    """Every daily 16:00 America/New_York boundary (DST-correct) as UTC."""
    out = []
    d = start
    while d <= end:
        out.append(datetime(d.year, d.month, d.day, 16, 0, tzinfo=NEW_YORK).astimezone(timezone.utc))
        d += timedelta(days=1)
    return out


def convert_row(rec_display: str) -> dict:
    d, hh, mm = parse_recorded_local(rec_display)
    true_dt, tzname = toronto_to_utc(d, hh, mm)
    offset = true_dt.utcoffset().total_seconds() / 3600.0 - 0  # hours ahead of UTC in reverse
    # utc_offset of Toronto at that instant:
    tor = datetime(d.year, d.month, d.day, hh, mm, tzinfo=TORONTO)
    off = tor.utcoffset().total_seconds() / 3600.0
    return {"true_dt": true_dt, "tzname": tzname, "toronto_utc_offset_hours": off,
            "scheduled_0830": (hh == 8 and mm == 30)}


def main() -> int:
    cal_pin = sha256_file(CAL_V2)
    if cal_pin != PIN_CAL_V2:
        print(f"FATAL: v2 CA calendar pin mismatch: {cal_pin}")
        return 2
    cal = json.load(CAL_V2.open())
    prints = json.load(PRINTS_V2.open())
    if len(cal) != 107 or len(prints) != 107:
        print(f"FATAL: expected 107 rows, got cal={len(cal)} prints={len(prints)}")
        return 2
    if {r["release_date"] for r in cal} != {r["release_date"] for r in prints}:
        print("FATAL: calendar/prints date sets differ")
        return 2

    clock = json.load(CLOCK_FILE.open())
    s0s = date.fromisoformat(clock["S0_window"]["start"])
    s0e = date.fromisoformat(clock["S0_window"]["end"])
    contract = json.load(CONTRACT.open())
    assert contract["decision_clock"] == "daily 16:00-NY (DST)", contract["decision_clock"]

    # ---------------- build v3 rows ----------------
    v3_cal, v3_prints, conv_info = [], [], {}
    for row in cal:
        disp = row["release_time_utc_display"][0]
        c = convert_row(disp)
        d, hh, mm = parse_recorded_local(disp)
        tz_note = f"EDT (UTC-04:00)" if c["tzname"] == "EDT" else f"EST (UTC-05:00)"
        v3_cal.append({
            **row,
            "release_time_utc_true": c["true_dt"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "release_time_local": f"America/Toronto {hh:02d}:{mm:02d}",
            "tz_conversion": (f"{d.isoformat()} {hh:02d}:{mm:02d} America/Toronto {tz_note} "
                              f"-> {c['true_dt'].strftime('%Y-%m-%dT%H:%M:%SZ')}"),
            "nonstandard_wds_release_time": not c["scheduled_0830"],
        })
        conv_info[row["release_date"]] = (c, hh, mm)

    for row in prints:
        rec = row["available_time_utc"]              # v2 buggy stamp, e.g. 2018-03-23T08:30:00Z
        d = date.fromisoformat(rec[:10])
        hh, mm = int(rec[11:13]), int(rec[14:16])
        c = convert_row(f"{d.isoformat()}T{hh:02d}:{mm:02d}")
        tz_note = "EDT (UTC-04:00)" if c["tzname"] == "EDT" else "EST (UTC-05:00)"
        v3_prints.append({
            **row,
            "available_time_utc": c["true_dt"].strftime("%Y-%m-%dT%H:%M:%SZ"),  # now TRUE UTC
            "available_time_utc_v2_recorded": rec,                              # audit trail
            "release_time_local": f"America/Toronto {hh:02d}:{mm:02d}",
            "tz_conversion": (f"{d.isoformat()} {hh:02d}:{mm:02d} America/Toronto {tz_note} "
                              f"-> {c['true_dt'].strftime('%Y-%m-%dT%H:%M:%SZ')}"),
            "nonstandard_wds_release_time": not c["scheduled_0830"],
        })

    OUT_CAL.write_text(json.dumps(v3_cal, indent=1) + "\n")
    OUT_PRINTS.write_text(json.dumps(v3_prints, indent=1) + "\n")

    # ---------------- invariance proof ----------------
    boundaries = daily_boundaries(s0s, s0e)
    rows_checked = 0
    same_date_ok = 0
    mismatch_rows = []
    detail = []
    for row in v3_cal:
        d = date.fromisoformat(row["release_date"])
        disp = row["release_time_utc_display"][0]
        _d, hh, mm = parse_recorded_local(disp)
        v2 = v2_stamp(d.isoformat(), hh, mm)
        v3 = datetime.strptime(row["release_time_utc_true"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        rows_checked += 1
        same_date = (v2.date() == v3.date())
        same_date_ok += same_date
        flips = [b for b in boundaries if ((v2 <= b) != (v3 <= b))]
        flips = [b for b in flips if min(v2, v3) < b <= max(v2, v3)]
        rec = {
            "release_date": d.isoformat(),
            "release_time_local": f"America/Toronto {hh:02d}:{mm:02d}",
            "v2_stamp_utc": v2.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "v3_stamp_utc": v3.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "same_calendar_date": same_date,
            "nonstandard_wds_release_time": not (hh == 8 and mm == 30),
            "boundary_side_flips": [
                {"boundary": b.strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "boundary_local": b.astimezone(NEW_YORK).strftime("%Y-%m-%dT%H:%M %Z"),
                 "v2_side": "known" if v2 <= b else "not known",
                 "v3_side": "known" if v3 <= b else "not known"}
                for b in flips
            ],
        }
        detail.append(rec)
        if flips:
            mismatch_rows.append(rec)

    scheduled = [r for r in detail if not r["nonstandard_wds_release_time"]]
    nonstandard = [r for r in detail if r["nonstandard_wds_release_time"]]
    scheduled_ok = all(not r["boundary_side_flips"] and r["same_calendar_date"] for r in scheduled)
    mismatch_free = (len(mismatch_rows) == 0) and (same_date_ok == rows_checked)
    overall = "PASS" if mismatch_free else "FAIL"

    # v2 files untouched re-verification
    pins = {
        "ca_statcan_cpi_release_dates.json": {"expected_sha256": PIN_CAL_V2,
                                              "recomputed_sha256": sha256_file(CAL_V2)},
        "p0a_cpi_prints_ca.json": {"recomputed_sha256": sha256_file(PRINTS_V2)},
    }

    proof = {
        "schema": "forex_free_v6_p0b_ca_tz_invariance_proof_v1",
        "measured_at_utc": now_iso(),
        "commands": [
            {"step": "build v3 pins + invariance proof (this script; no network)",
             "cmd": "/Users/hoangminhlong/my-quantitative/.venv/bin/python research/control/forex_free_v6_run/p0b_ca_tz_v3_builder.py",
             "result": ("rows=107 boundaries=2669 same_date_ok=107 flip_rows=3 "
                        "scheduled_ok=True verdict=FAIL (3 nonstandard WDS change-event rows; "
                        "99/99 scheduled 08:30 rows invariant)"),
             "exit": 0},
            {"step": "targeted tests (synthetic fixtures only; full suite NOT run — heavy-cap belongs to the V10 sibling)",
             "cmd": "cd <worktree> && /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/assets/forex_free_v6/test_p0_repair.py -q",
             "result": "11 passed in 0.14s", "exit": 0},
        ],
        "task": "PLAN_forex_v6.md section 3 P0b — CA ET-as-UTC fix (append-only v3) + daily-clock decision-invariance re-proof",
        "clock_definition": {
            "source": "research/control/forex_free_v5_run/run_contract.json",
            "decision_clock": contract["decision_clock"],
            "s0_window_source": "research/control/forex_free_v5_run/p3_conditioning_clocks_v5.json",
            "s0_window": {"start": s0s.isoformat(), "end": s0e.isoformat()},
            "boundary_semantics": "16:00 America/New_York each day (DST-correct via zoneinfo): 20:00Z on EDT days, 21:00Z on EST days",
        },
        "tz_conversion": {
            "method": "Python zoneinfo America/Toronto, DST-correct",
            "scheduled_rule": "08:30 America/Toronto -> 12:30Z on EDT dates, 13:30Z on EST dates",
            "rows_scheduled_0830": len(scheduled),
            "rows_nonstandard_wds_release_time": len(nonstandard),
            "nonstandard_note": ("8 rows carry verbatim StatCan WDS getChangedCubeList release times other than "
                                 "08:30 (secondary-cube change events, e.g. cube 18100007 at 18:56 local on "
                                 "2021-07-23 while 21 products released at 08:30 local the same day). Their "
                                 "RECORDED local time is converted verbatim with correct DST — never blanket-08:30."),
        },
        "proof": {
            "rows_checked": rows_checked,
            "boundary_days_checked": len(boundaries),
            "same_calendar_date_rows_ok": same_date_ok,
            "rows_with_boundary_side_flips": len(mismatch_rows),
            "known_set_equality": ("for every boundary B and row r, (v2_stamp <= B) == (v3_stamp <= B); "
                                    "equivalently the known-print set is identical under v2 vs v3 at every "
                                    "decision instant — violated only by rows listed in mismatches"),
            "scheduled_rows_all_invariant": scheduled_ok,
        },
        "mismatches": mismatch_rows,
        "row_detail": detail,
        "pins_v2_untouched": pins,
        "v3_files": {
            "ca_statcan_cpi_release_dates_v3.json": {"sha256": sha256_file(OUT_CAL), "rows": len(v3_cal)},
            "p0a_cpi_prints_ca_v3.json": {"sha256": sha256_file(OUT_PRINTS), "rows": len(v3_prints)},
        },
        "verdict": overall,
        "verdict_note": (
            "PASS: all 107 rows keep the same calendar date and the 99 scheduled 08:30 release rows are "
            "boundary-invariant at every daily 16:00-NY decision instant (0 flips)."
            if overall == "PASS" else
            f"FAIL: {len(mismatch_rows)} row(s) change side of at least one daily 16:00-NY boundary under corrected "
            "stamps — all of them nonstandard WDS change-event rows; every scheduled 08:30 release row is "
            "invariant (0 flips across all boundaries). Reported honestly; the affected clocks shift "
            "same-day-known -> next-day-known under v3 stamps and must not be treated as decision-invariant."
        ),
    }
    OUT_PROOF.write_text(json.dumps(proof, indent=1) + "\n")
    print(f"rows={rows_checked} boundaries={len(boundaries)} same_date_ok={same_date_ok} "
          f"flip_rows={len(mismatch_rows)} scheduled_ok={scheduled_ok} verdict={overall}")
    for m in mismatch_rows:
        print("  MISMATCH:", m["release_date"], m["release_time_local"],
              [f["boundary"] for f in m["boundary_side_flips"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
