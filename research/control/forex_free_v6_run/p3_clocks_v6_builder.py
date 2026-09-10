#!/usr/bin/env python3
"""FOREX-FREE-V6 P2/P3 builder: conditioning clocks v6 + data authority census v6.

Authority: plans/PLAN_forex_v6.md section 3 P2 (coverage-first data authority)
and P3 (conditioning clocks publication; invariants-freeze inputs).

Semantics:
- S0 window 2018-04-04..2025-07-24 FROZEN (no extension authorized).
- GB/AU/NZ clocks carried from the V5 publication (p3_conditioning_clocks_v5.json),
  re-verified row-by-row against the underlying v5-era calendar files
  (gb_ons_cpi_release_dates.json, au_abs_cpi_release_dates.json,
  nz_statsnz_cpi_release_dates.json) - those calendars are unchanged this cycle.
- CA clocks rebuilt from the v3 TRUE-UTC pins (ca_statcan_cpi_release_dates_v3.json,
  P0b): available_time_utc is the TRUE UTC of the recorded local StatCan WDS
  release time (zoneinfo America/Toronto, DST-correct). ET-as-UTC (v2) stamps are
  never used.
- Daily decision clock: 16:00 America/New_York (run_contract.json
  "decision_clock": "daily 16:00-NY (DST)"). A CA print is available for the
  release-date decision instant iff available_time_utc <= that instant's UTC time
  (20:00Z on EDT days, 21:00Z on EST days). 08:30-local scheduled releases are
  before 16:00 NY in both EST/EDT -> same-day. The 3 nonstandard WDS rows
  (17:03/18:04/18:56 local) land after the boundary -> boundary_shift: the print
  becomes conditionable only at the NEXT decision instant
  (available_for_daily_decision_date = next trading day, FX 24/5 weekday
  convention; no holiday calendar is in evidence, so holiday refinement is NOT
  attempted and the computed next weekday is recorded as-is).
- P-1: every clock carries its availability evidence (archive_path +
  archive_sha256) copied verbatim from the underlying calendar files.

Determinism: the document is a pure function of the input files + the
--measured-at argument. No wall-clock reads, no network. dump is byte-stable
(indent=1, ensure_ascii=True, insertion-ordered keys, no trailing newline -
V5 publication convention). Re-running with the same --measured-at reproduces
byte-identical files; an existing file that differs from the rebuild is a hard
error (fail-closed idempotence guard).

No PnL, no scored computation, no network fetches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")

REPO_ROOT = Path(__file__).resolve().parents[3]  # research/control/forex_free_v6_run/ -> worktree root
V5_DIR = REPO_ROOT / "research" / "control" / "forex_free_v5_run"
V6_DIR = REPO_ROOT / "research" / "control" / "forex_free_v6_run"

V5_CLOCKS = V5_DIR / "p3_conditioning_clocks_v5.json"
V5_P2 = V5_DIR / "p2_data_authority_v5.json"
GB_CAL = V5_DIR / "gb_ons_cpi_release_dates.json"
AU_CAL = V5_DIR / "au_abs_cpi_release_dates.json"
NZ_CAL = V5_DIR / "nz_statsnz_cpi_release_dates.json"
CA_V3 = V6_DIR / "ca_statcan_cpi_release_dates_v3.json"
CA_PRINTS_V3 = V6_DIR / "p0a_cpi_prints_ca_v3.json"
TZ_PROOF = V6_DIR / "p0b_ca_tz_invariance_proof.json"
P0C_VERDICT = V6_DIR / "p0c_unlock_verdict.json"
EMU_REPAIR_LEDGER = V6_DIR / "announcement_ledger_v6_emu_repair.jsonl"
EMU_REPAIR_VERDICT = V6_DIR / "p0a_emu_repair_verdict.json"
V1_MANIFEST = REPO_ROOT / "research" / "control" / "forex_free_v1_run" / "staged_data_manifest.json"

SCHEMA_CLOCKS = "forex_free_v6_conditioning_clocks_v1"
SCHEMA_P2 = "forex_free_v6_gate_evidence_v1"
GATE_P2 = "V6_P2_DATA_AUTHORITY"
PRODUCER = "A3_DATA_AUTHORITY_LANE_FOREX_V6"
AUTHORITY = (
    "PLAN_forex_v6.md section 3 P3; CA v3 semantics from P0b; "
    "availability evidence absolute per P-1"
)

S0_START = "2018-04-04"
S0_END = "2025-07-24"
V5_TOTAL = 246
V5_COUNTS = {"GB": 88, "CA": 105, "AU": 23, "NZ": 30}
ECONOMY_ORDER = ["GB", "CA", "AU", "NZ"]

# Verbatim V5 rule string - carries the D1 conditioning restriction AND the
# fail-closed gap statement exactly as V5 recorded it.
V5_RULE_VERBATIM = (
    "a D1 proposal may condition ONLY on clocks listed here; every clock "
    "carries its availability evidence sha256; gaps are recorded (AU "
    "pre-Sep-2019 quarterlies and mid-2022) and must fail closed in any "
    "implementation"
)

CA_PRECISION = (
    "INSTANT (StatCan WDS recorded release time, America/Toronto; "
    "TRUE UTC via zoneinfo, DST-correct)"
)
KNOWN_FLIP_DATES = {"2018-05-28", "2018-05-29", "2021-07-23"}

# Pins asserted from authorities (fail-closed cross-checks).
EXPECTED_CA_V2_SHA = "088b0ba80f0580e39ab17832872a93e3dce15bc077ffafa2f87800b4c7115eaa"
EXPECTED_CA_V3_SHA = "0f1a93282348cef94aecf2b9a8da275945e809643e3646f551b2df916e2af7b3"
EXPECTED_CA_PRINTS_V3_SHA = "d6f7ec94a8aa8e167e2e46046dffe58354d67eddf9d90ae668ede6487fee3cd0"

MONTHS = {
    m.lower(): i + 1
    for i, m in enumerate(
        ["January", "February", "March", "April", "May", "June", "July",
         "August", "September", "October", "November", "December"]
    )
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def dump_json_bytes(obj) -> bytes:
    """Byte-stable publication dump (V5 convention: indent=1, no trailing newline)."""
    return json.dumps(obj, indent=1, ensure_ascii=True).encode("utf-8")


def parse_iso_z(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def parse_gb_display(s: str) -> date:
    """'13 February 2018' -> date(2018, 2, 13)."""
    day, mon, year = s.split()
    return date(int(year), MONTHS[mon.lower()], int(day))


def in_s0(d: date) -> bool:
    return date.fromisoformat(S0_START) <= d <= date.fromisoformat(S0_END)


def ny_decision_boundary_utc(d: date) -> datetime:
    """The daily 16:00 America/New_York decision instant of date d, as aware UTC."""
    return datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY).astimezone(timezone.utc)


def next_weekday(d: date) -> date:
    """Next trading day, FX 24/5 weekday convention (skip Sat/Sun only).

    No holiday calendar is in evidence anywhere in the tree; holiday refinement
    is therefore NOT attempted (P-1: asserted holiday bounds are unauthorized).
    """
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5:  # 5=Sat, 6=Sun
        nxt += timedelta(days=1)
    return nxt


# ---------------------------------------------------------------- inputs


def _read_json(p: Path):
    return json.loads(p.read_bytes().decode("utf-8"))


def load_inputs():
    inputs = {
        "v5_clocks": _read_json(V5_CLOCKS),
        "gb": _read_json(GB_CAL),
        "au": _read_json(AU_CAL),
        "nz": _read_json(NZ_CAL),
        "ca_v3": _read_json(CA_V3),
        "tz_proof": _read_json(TZ_PROOF),
        "hashes": {
            "gb_cal": sha256_file(GB_CAL),
            "au_cal": sha256_file(AU_CAL),
            "nz_cal": sha256_file(NZ_CAL),
            "ca_v3": sha256_file(CA_V3),
            "ca_prints_v3": sha256_file(CA_PRINTS_V3),
            "ca_v2": sha256_file(V5_DIR / "ca_statcan_cpi_release_dates.json"),
            "tz_proof": sha256_file(TZ_PROOF),
            "p0c_verdict": sha256_file(P0C_VERDICT),
            "emu_ledger": sha256_file(EMU_REPAIR_LEDGER),
            "v1_manifest": sha256_file(V1_MANIFEST),
            "v5_p2": sha256_file(V5_P2),
        },
    }
    inputs["emu_ledger_rows"] = len(
        [l for l in EMU_REPAIR_LEDGER.read_bytes().decode("utf-8").splitlines() if l.strip()]
    )
    inputs["emu_verdict"] = _read_json(EMU_REPAIR_VERDICT)
    inputs["v1_manifest_doc"] = _read_json(V1_MANIFEST)
    # Fail-closed pin cross-checks.
    assert inputs["hashes"]["ca_v2"] == EXPECTED_CA_V2_SHA, "CA v2 pin drifted"
    assert inputs["hashes"]["ca_v3"] == EXPECTED_CA_V3_SHA, "CA v3 pin drifted"
    assert inputs["hashes"]["ca_prints_v3"] == EXPECTED_CA_PRINTS_V3_SHA, "CA prints v3 pin drifted"
    proof = inputs["tz_proof"]
    assert proof["v3_files"]["ca_statcan_cpi_release_dates_v3.json"]["sha256"] == EXPECTED_CA_V3_SHA
    assert proof["v3_files"]["p0a_cpi_prints_ca_v3.json"]["sha256"] == EXPECTED_CA_PRINTS_V3_SHA
    return inputs


# ------------------------------------------------- GB / AU / NZ (carried)


def rebuild_gbanz_from_calendar(econ: str, cal_rows: list, v5_rows: list):
    """Rebuild GB/AU/NZ clock rows from the v5-era calendar file and prove they
    equal the V5-published rows (decision_date + archive_sha256 sets)."""
    cal = {}
    unevidenced_no_date = 0
    for r in cal_rows:
        if econ == "GB":
            rd = parse_gb_display(r["release_date_display"])
        else:
            if not r.get("release_date"):
                # Fail-closed gap row (e.g. AU UNEVIDENCED nov-2025: no evidenced
                # Released date) - can never become a clock.
                assert r.get("class") != "EVIDENCED", f"{econ}: EVIDENCED row without date"
                unevidenced_no_date += 1
                continue
            rd = date.fromisoformat(r["release_date"])
        cal[rd] = r
    rebuilt = {d for d in cal if in_s0(d)}
    carried = {date.fromisoformat(r["decision_date"]) for r in v5_rows}
    assert rebuilt == carried, f"{econ}: rebuilt in-S0 set != V5 carried set"
    for r in v5_rows:
        d = date.fromisoformat(r["decision_date"])
        c = cal[d]
        assert c["archive_sha256"] == r["archive_sha256"], f"{econ} {d}: evidence sha drift"
        assert c.get("slug", c.get("reference_period")) == r["reference_period"], \
            f"{econ} {d}: reference_period drift"
        if econ == "NZ":
            # V5 stamp convention "YYYY-MM-DDTHH:MM:45+12:00" (flat +12:00; the
            # offset-qualified instant is conservative-LATER on NZDT dates).
            hhmm = r["available_time_utc"][11:16]
            assert hhmm == c["release_time_local"], f"NZ {d}: local time prefix drift"
        assert r["economy"] == econ
    dropped_out_of_window = 0
    for r in cal_rows:  # count ROWS (not distinct dates): duplicate-date rows exist (AU)
        if econ == "GB":
            rd2 = parse_gb_display(r["release_date_display"])
        elif not r.get("release_date"):
            continue
        else:
            rd2 = date.fromisoformat(r["release_date"])
        if not in_s0(rd2):
            dropped_out_of_window += 1
    return len(v5_rows), dropped_out_of_window, cal, unevidenced_no_date


def carried_gbanz_rows(econ: str, v5_clocks: dict, cal_map: dict) -> list:
    rows = []
    for r in v5_clocks["clocks"]:
        if r["economy"] != econ:
            continue
        d = date.fromisoformat(r["decision_date"])
        rows.append(
            {
                "decision_date": r["decision_date"],
                "available_time_utc": r["available_time_utc"],
                "precision": r["precision"],
                "reference_period": r["reference_period"],
                "archive_path": cal_map[d]["archive_path"],
                "archive_sha256": r["archive_sha256"],
                "economy": econ,
            }
        )
    rows.sort(key=lambda x: x["decision_date"])
    return rows


# ------------------------------------------------------- CA (v3 TRUE-UTC)


def ca_rows_core(ca_v3_rows: list, continuity_sha_by_date: dict | None = None,
                 s0_start: str = S0_START, s0_end: str = S0_END):
    """Pure core: CA clock rows under v3 TRUE-UTC semantics + boundary_shift ledger.

    Synthetic-testable: no authority-file assertions here; the real-input
    fail-closed checks (evidence continuity vs V5, flip-set equality with the
    P0b proof) live in build_ca_rows().

    Returns (rows, shift_ledger, stats, flips).
    """
    start, end = date.fromisoformat(s0_start), date.fromisoformat(s0_end)

    def _in_s0(d: date) -> bool:
        return start <= d <= end

    rows, shift_ledger, flips = [], [], set()
    dropped = 0
    for r in ca_v3_rows:
        d = date.fromisoformat(r["release_date"])
        stamp = r["release_time_utc_true"]
        assert stamp.endswith("Z"), f"CA {d}: v3 stamp not UTC-qualified"
        if not _in_s0(d):
            dropped += 1
            continue
        if continuity_sha_by_date is not None and r["release_date"] in continuity_sha_by_date:
            assert continuity_sha_by_date[r["release_date"]] == r["archive_sha256"], \
                f"CA {d}: archive evidence differs from V5 publication"
        boundary = ny_decision_boundary_utc(d)
        available_same_day = parse_iso_z(stamp) <= boundary
        if not available_same_day:
            flips.add(r["release_date"])
            nxt = next_weekday(d)
            assert _in_s0(nxt), f"CA {d}: next trading day outside frozen S0 window"
            next_date = nxt.isoformat()
        else:
            next_date = r["release_date"]
        row = {
            "decision_date": r["release_date"],
            "available_time_utc": stamp,
            "precision": CA_PRECISION,
            "reference_period": r["release_date"],
            "archive_path": r["archive_path"],
            "archive_sha256": r["archive_sha256"],
            "economy": "CA",
            "available_for_daily_decision_date": next_date,
        }
        if not available_same_day:
            shift_ledger.append(
                {
                    "economy": "CA",
                    "decision_date": r["release_date"],
                    "release_time_local": r["release_time_local"],
                    "before_v2": {
                        "stamp_utc": r["release_time_utc_display"][0] + ":00Z",
                        "semantics": "ET-as-UTC (F-TERM-2): local wall time misread as UTC; "
                                     "at the release-date 16:00-NY decision instant the print "
                                     "wrongly appeared KNOWN",
                    },
                    "after_v3": {
                        "stamp_utc": stamp,
                        "semantics": "TRUE UTC of the recorded local time (zoneinfo, DST-correct); "
                                     "at the release-date 16:00-NY decision instant the print is "
                                     "NOT yet available",
                    },
                    "affected_decision_dates": {
                        "release_date_decision_instant": (
                            f"{r['release_date']} 16:00-NY - print NOT conditionable"
                        ),
                        "available_for_daily_decision_date": next_date,
                    },
                    "consequence": "for daily-clock mechanisms the print becomes conditionable "
                                   "only at the NEXT decision instant (next trading day, FX 24/5 "
                                   "weekday convention; no holiday calendar is in evidence)",
                    "nonstandard_wds_release_time": True,
                    "archive_path": r["archive_path"],
                    "archive_sha256": r["archive_sha256"],
                }
            )
        rows.append(row)
    rows.sort(key=lambda x: x["decision_date"])
    shift_ledger.sort(key=lambda x: x["decision_date"])
    stats = {
        "in_s0": len(rows),
        "same_day_available": len(rows) - len(shift_ledger),
        "boundary_shifted": len(shift_ledger),
        "dropped_out_of_window": dropped,
    }
    return rows, shift_ledger, stats, flips


def build_ca_rows(ca_v3_rows: list, v5_ca_rows: list, tz_proof: dict):
    """Real-input wrapper: adds the P0b fail-closed checks to the pure core."""
    continuity = {r["decision_date"]: r["archive_sha256"] for r in v5_ca_rows}
    rows, ledger, stats, flips = ca_rows_core(ca_v3_rows, continuity)
    # Evidence continuity: every published CA clock must trace to the V5 publication.
    assert {r["decision_date"] for r in rows} <= set(continuity), \
        "CA clock published without V5-published archive evidence"
    proof_flips = {m["release_date"] for m in tz_proof["mismatches"]}
    assert flips == proof_flips == KNOWN_FLIP_DATES, \
        f"flip sets disagree: computed={flips} proof={proof_flips}"
    assert len(ledger) == 3
    return rows, ledger, stats


# ------------------------------------------------------------- documents


def build_clocks_doc(inputs: dict, measured_at: str) -> dict:
    v5 = inputs["v5_clocks"]
    assert v5["total_clocks_published"] == V5_TOTAL
    assert v5["per_economy_in_S0"] == V5_COUNTS
    assert v5["S0_window"] == {"start": S0_START, "end": S0_END}

    v5_by_econ = {e: [r for r in v5["clocks"] if r["economy"] == e] for e in ECONOMY_ORDER}

    counts, dropped_by_econ, cal_maps = {}, {}, {}
    gb_count, gb_dropped, gb_map, _ = rebuild_gbanz_from_calendar("GB", inputs["gb"], v5_by_econ["GB"])
    au_count, au_dropped, au_map, au_unevid = rebuild_gbanz_from_calendar("AU", inputs["au"], v5_by_econ["AU"])
    nz_count, nz_dropped, nz_map, _ = rebuild_gbanz_from_calendar("NZ", inputs["nz"], v5_by_econ["NZ"])
    counts.update(GB=gb_count, AU=au_count, NZ=nz_count)
    dropped_by_econ.update(GB=gb_dropped, AU=au_dropped, NZ=nz_dropped)
    cal_maps.update(GB=gb_map, AU=au_map, NZ=nz_map)

    ca_rows, shift_ledger, ca_stats = build_ca_rows(
        inputs["ca_v3"], v5_by_econ["CA"], inputs["tz_proof"]
    )
    counts["CA"] = ca_stats["in_s0"]
    dropped_by_econ["CA"] = ca_stats["dropped_out_of_window"]

    assert counts == V5_COUNTS, f"per-economy in-S0 counts changed: {counts}"
    total = sum(counts.values())
    assert total == V5_TOTAL, f"total {total} != V5 246"

    clocks = []
    for e in ECONOMY_ORDER:
        if e == "CA":
            clocks.extend(ca_rows)
        else:
            clocks.extend(carried_gbanz_rows(e, v5, cal_maps[e]))
    assert len(clocks) == V5_TOTAL

    dated_dropped = sum(dropped_by_econ.values())

    return {
        "schema": SCHEMA_CLOCKS,
        "measured_at_utc": measured_at,
        "producer": PRODUCER,
        "authority": AUTHORITY,
        "rule": V5_RULE_VERBATIM,
        "S0_window": {
            "start": S0_START,
            "end": S0_END,
            "frozen": True,
            "extension": "NONE - no extension authorized by PLAN_forex_v6.md; "
                         "window carried unchanged from V5",
        },
        "clock_semantics": {
            "decision_clock": "daily 16:00 America/New_York (DST-correct via zoneinfo); "
                              "20:00Z on EDT days, 21:00Z on EST days",
            "true_utc": "all available_time_utc values are TRUE-UTC-qualified instants; "
                        "CA rows use the P0b v3 TRUE-UTC pins (ET-as-UTC v2 stamps retired); "
                        "GB/AU/NZ carried unchanged from V5 (their v5-era calendar files are "
                        "unchanged this cycle and were re-verified row-by-row at build time)",
            "GB_AU_NZ_day_precision": "DAY-precision clocks carry a 23:59:59Z end-of-day bound "
                                      "(GB ONS Release date field, AU ABS Released field) or an "
                                      "offset-qualified instant (NZ Stats NZ PublicationDate); "
                                      "each is available for the daily decision on its "
                                      "decision_date by construction",
            "NZ_offset_convention": "V5-published flat +12:00 offset carried verbatim; on NZDT "
                                    "dates the expressed instant is one hour later than the true "
                                    "local wall-clock conversion - conservative LATER bound (P-1)",
            "ca_boundary_rule": "CA print available at the release-date decision instant iff "
                                "available_time_utc <= 16:00-NY instant of the release date; "
                                "08:30-local scheduled releases are before 16:00 NY in both "
                                "EST/EDT (same-day); the 3 nonstandard WDS change-event rows land "
                                "after the boundary (boundary_shift)",
            "next_trading_day_rule": "next weekday (FX 24/5 convention); no holiday calendar is "
                                     "in evidence, so holiday refinement is NOT attempted",
            "gaps_fail_closed": {
                "AU_pre_Sep_2019_quarterlies": "recorded exactly as V5 recorded them; ABS pages "
                                               "for pre-Sep-2019 quarterlies carry no evidenced "
                                               "Released date; must fail closed in any implementation",
                "AU_mid_2022": "recorded exactly as V5 recorded them; must fail closed in any "
                               "implementation",
            },
        },
        "per_economy_in_S0": {"GB": counts["GB"], "CA": counts["CA"], "AU": counts["AU"],
                              "NZ": counts["NZ"]},
        "total_clocks_published": total,
        "delta_vs_v5": {
            "total": 0,
            "per_economy": {"GB": 0, "CA": 0, "AU": 0, "NZ": 0},
            "explanation": "identical 246-clock class; V6 changes CA STAMPS (v2 ET-as-UTC -> v3 "
                           "TRUE UTC) and flags 3 CA rows boundary_shift (same-day-known -> "
                           "next-day-known); no clock enters or leaves the S0 window",
        },
        "boundary_shift_rows": shift_ledger,
        "clocks": clocks,
        "note_out_of_window_rows_dropped_dated": dated_dropped,
        "note_out_of_window_rows_dropped_by_economy": dropped_by_econ,
        "note_unevidenced_calendar_rows_without_release_date": {
            "AU": au_unevid,
            "treatment": "fail-closed gap rows; never published as clocks",
        },
    }


def build_p2_doc(inputs: dict, measured_at: str, head: str | None) -> dict:
    h = inputs["hashes"]
    manifest = inputs["v1_manifest_doc"]
    emu = inputs["emu_verdict"]
    doc = {
        "schema": SCHEMA_P2,
        "gate": GATE_P2,
        "measured_at_utc": measured_at,
        "producer": PRODUCER,
        "authority": "PLAN_forex_v6.md section 3 P2 (coverage-first) - census only; "
                     "no scored computation; no network fetches; no re-download",
        "phase": "V6-P (no PnL)",
        "price_series": {
            "status": "INHERITED",
            "worktree_observation": "data_raw/ staging NOT materialized in this lane worktree "
                                    "(gitignored raw data is not checked out into fresh "
                                    "worktrees); nothing re-downloaded per task scope",
            "manifest_path": "research/control/forex_free_v1_run/staged_data_manifest.json",
            "manifest_present_tracked": True,
            "manifest_sha256": h["v1_manifest"],
            "manifest_file_count_per_tree_recomputed": manifest["file_count_per_tree"],
            "inherited_evidence": {
                "v5_p2_verdict_path": "research/control/forex_free_v5_run/p2_data_authority_v5.json",
                "v5_p2_sha256": h["v5_p2"],
                "v5_statement": "price snapshots INHERITED_BYTE_VERIFIED: V4 P2 measured 152/152 "
                                "byte-identical vs V3R + 156/156 manifest digests; manifest "
                                "byte_identical_exec_repro=true",
            },
            "no_redownload": True,
        },
        "calendars": {
            "GB": {
                "status": "EVIDENCED_CITABLE",
                "file": "research/control/forex_free_v5_run/gb_ons_cpi_release_dates.json",
                "sha256_recomputed": h["gb_cal"],
                "rows_total": len(inputs["gb"]),
                "rows_in_S0": V5_COUNTS["GB"],
                "note": "v5-era calendar unchanged this cycle; re-verified row-by-row by the "
                        "P3 clocks builder",
            },
            "CA": {
                "status": "EVIDENCED_CITABLE_V3",
                "v3_file": "research/control/forex_free_v6_run/ca_statcan_cpi_release_dates_v3.json",
                "v3_sha256": h["ca_v3"],
                "v3_rows_total": len(inputs["ca_v3"]),
                "v3_rows_in_S0": V5_COUNTS["CA"],
                "v3_prints_table": "research/control/forex_free_v6_run/p0a_cpi_prints_ca_v3.json",
                "v3_prints_sha256": h["ca_prints_v3"],
                "v2_pins_untouched": {
                    "file": "research/control/forex_free_v5_run/ca_statcan_cpi_release_dates.json",
                    "sha256": h["ca_v2"],
                },
                "tz_invariance_proof": {
                    "path": "research/control/forex_free_v6_run/p0b_ca_tz_invariance_proof.json",
                    "sha256": h["tz_proof"],
                    "flip_rows": 3,
                    "honest_verdict": "FAIL (3 nonstandard WDS change-event rows; 99/99 scheduled "
                                      "08:30 rows invariant) - the v3 semantics flow into the "
                                      "P3 clocks as boundary_shift flags",
                },
                "note": "CA superseded by v3 TRUE-UTC pins this cycle (P0b); v2 ET-as-UTC stamps "
                        "retired from clock publication; archive evidence bytes unchanged",
            },
            "AU": {
                "status": "EVIDENCED_CITABLE",
                "file": "research/control/forex_free_v5_run/au_abs_cpi_release_dates.json",
                "sha256_recomputed": h["au_cal"],
                "rows_total": len(inputs["au"]),
                "rows_in_S0": V5_COUNTS["AU"],
                "note": "v5-era calendar unchanged this cycle; UNEVIDENCED nov-2025 row stays "
                        "out (fail-closed)",
            },
            "NZ": {
                "status": "EVIDENCED_CITABLE",
                "file": "research/control/forex_free_v5_run/nz_statsnz_cpi_release_dates.json",
                "sha256_recomputed": h["nz_cal"],
                "rows_total": len(inputs["nz"]),
                "rows_in_S0": V5_COUNTS["NZ"],
                "note": "v5-era calendar unchanged this cycle",
            },
            "US": {
                "status": "OUT",
                "verdict_path": "research/control/forex_free_v6_run/p0c_unlock_verdict.json",
                "outcome_one_line": "P0c axis 3: zero owner-provided BLS schedule pages staged "
                                    "anywhere in scope (find control demonstrably non-vacuous) - "
                                    "US stays OUT",
            },
            "EMU": {
                "status": "LEDGER_REPAIRED_NOT_A_FUNDED_CALENDAR",
                "repair_ledger": "research/control/forex_free_v6_run/announcement_ledger_v6_emu_repair.jsonl",
                "repair_ledger_sha256": h["emu_ledger"],
                "repair_ledger_rows": inputs["emu_ledger_rows"],
                "diagnosis": emu["run_diagnosis"]["finding"],
                "diagnosis_counts": emu["run_diagnosis"]["diagnoses"],
                "calendar_funding": "NONE - EMU is NOT a funded per-print calendar in V6; the "
                                    "repair resolves the 9 value-integrity rows (append-only v2) "
                                    "and records the series-heterogeneity diagnosis only",
            },
        },
        "lane_2_market_based_real_rate": {
            "status": "DATA_BLOCKED_VALID",
            "verdict_path": "research/control/forex_free_v6_run/p0c_unlock_verdict.json",
            "outcome_one_line": "FRED_API_KEY absent (axis 1) + keyless API 400 (axis 2b) + "
                                "license page unreachable on 3 archived attempts (axis 2c) - no "
                                "working path under the pre-registered fail-closed rule; lane "
                                "carried again",
        },
        "boundary_shift_ledger": build_ca_rows(
            inputs["ca_v3"],
            [r for r in inputs["v5_clocks"]["clocks"] if r["economy"] == "CA"],
            inputs["tz_proof"],
        )[1],
        "coverage_totals": {
            "conditioning_clocks_published": V5_TOTAL,
            "per_economy_in_S0": {"GB": V5_COUNTS["GB"], "CA": V5_COUNTS["CA"],
                                  "AU": V5_COUNTS["AU"], "NZ": V5_COUNTS["NZ"]},
            "delta_vs_v5": 0,
        },
        "s1": {"listed": False, "opened": False, "hashed": False, "copied": False},
        "verdict": "PASS",
        "verdict_note": "coverage-first census complete: per-print calendars EVIDENCED_CITABLE "
                        "for GB/AU/NZ (v5-era, re-hashed) and EVIDENCED_CITABLE_V3 for CA (P0b "
                        "TRUE-UTC pins); US OUT and lane 2 DATA_BLOCKED_VALID are documented "
                        "fail-closed outcomes, not census failures; margin note (P-2): counts "
                        "reconcile exactly to the V5 246-clock class with zero delta - the only "
                        "semantic change is the CA v3 stamp correction with 3 flagged "
                        "boundary_shift rows",
    }
    assert emu["run_diagnosis"]["diagnoses"] == {"DFR_SUSPECTED_CONFIRMED": 7, "MRO_CONFIRMED": 2}
    if head:
        doc["head"] = head
    return doc


# ------------------------------------------------------------------ main


def write_deterministic(path: Path, payload_bytes: bytes) -> None:
    if path.exists():
        existing = path.read_bytes()
        if existing != payload_bytes:
            raise SystemExit(
                f"DETERMINISM GUARD: {path} exists with different bytes; the publication is "
                f"append-only - reuse the original --measured-at or remove the file consciously."
            )
    path.write_bytes(payload_bytes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--measured-at", required=True,
                    help="UTC timestamp for the head metadata (e.g. output of `date -u`); "
                         "the builder never reads the wall clock itself")
    ap.add_argument("--head", default=None, help="short HEAD sha to record in the P2 census")
    ap.add_argument("--out-dir", default=None,
                    help="output directory (default: research/control/forex_free_v6_run)")
    args = ap.parse_args(argv)
    datetime.strptime(args.measured_at, "%Y-%m-%dT%H:%M:%SZ")  # validate form

    inputs = load_inputs()

    clocks_doc = build_clocks_doc(inputs, args.measured_at)
    clocks_doc_b = dump_json_bytes(clocks_doc)
    assert dump_json_bytes(build_clocks_doc(inputs, args.measured_at)) == clocks_doc_b, \
        "in-process determinism check failed (clocks)"

    p2_doc = build_p2_doc(inputs, args.measured_at, args.head)
    p2_doc_b = dump_json_bytes(p2_doc)
    assert dump_json_bytes(build_p2_doc(inputs, args.measured_at, args.head)) == p2_doc_b, \
        "in-process determinism check failed (p2)"

    out_dir = Path(args.out_dir) if args.out_dir else V6_DIR
    clocks_path = out_dir / "p3_conditioning_clocks_v6.json"
    p2_path = out_dir / "p2_data_authority_v6.json"
    write_deterministic(clocks_path, clocks_doc_b)
    write_deterministic(p2_path, p2_doc_b)

    print("clocks:", clocks_path)
    print("  sha256:", sha256_bytes(clocks_doc_b), "bytes:", len(clocks_doc_b))
    print("  per_economy_in_S0:", clocks_doc["per_economy_in_S0"],
          "total:", clocks_doc["total_clocks_published"])
    print("  boundary_shift rows:",
          [r["decision_date"] for r in clocks_doc["boundary_shift_rows"]])
    print("  out-of-window dated rows dropped:",
          clocks_doc["note_out_of_window_rows_dropped_dated"])
    print("p2 census:", p2_path)
    print("  sha256:", sha256_bytes(p2_doc_b), "bytes:", len(p2_doc_b))
    print("  gate:", p2_doc["gate"], "verdict:", p2_doc["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
