#!/usr/bin/env python
"""FOREX-NG4 P0c runner: A7-F1 remediation -- ONE wide-window ALFRED
pull of CP0000EZ19M086NEST -> true-vintage EZ census + gate additive
p0c section, under the A7 audit prescription
(research/control/forex_ng4_run/audits/a7_terminal_ng4.json,
required_owner_action) and plans/PLAN_forex_ng4.md sec 2-3.

Measures, fail-closed:

1. PULL (research/assets/forex_ng4/wide_pull.py): ONE wide-window query
   shape realtime_start=2015-01-01 (<= the committed V8 earliest-vintage
   bound 2015-02-27) .. realtime_end=9999-12-31, + limit/offset paging
   of the SAME shape only while a full page returns; under the owner's
   EXISTING FRED entitlement (FRED_API_KEY from the gitignored root
   .env, loaded programmatically, NEVER echoed -- key_present only).
   Etiquette: <= 1 request / 1.2 s + backoff 2/4/8 s, max 3 retries per
   page; key/quota/deterministic refusals STOP fail-closed.  Raw page
   bytes + the merged document pinned UNTRACKED under
   data_raw/forex_ng4_ez/; the COMMITTED manifest carries every sha256
   (verify-on-read; the merged document must BE the merge of the pages).

2. CENSUS (ng2/ng3 machinery VIA IMPORT, unmodified): the pure input
   adapter (wide_pull.validate_wide_response) turns the merged document
   into ng1 VintageRows with TRUE realtime windows; those rows feed
   ng3.build_restricted_stream("EZ", ...) UNMODIFIED -- dedupe, STRICT
   realtime-monotonicity fail-closed, v1->v2 first-to-second-version
   events, S0-window usable filter, first-print-era restriction and
   bulk re-referencing exclusion are all the frozen machinery's own law.
   Floors (frozen, unchanged): A4 EZ print events >= 30; A5 EZ-vs-US
   differential months >= 12 (US leg rebuilt from the pinned CADS
   CPIAUCSL realtime archive with the same machinery); Q-6 recent
   measured (no floor frozen for EZ).  Canaries: fabricated obs months
   found=False; wide-response shape (true windows, count, monthly grid);
   realtime monotonicity; manifest verify-on-read; merged==merge(pages).

3. ERA COMPARISON (artifact-vs-artifact): the committed p0b as-of
   census (p0b_ez_hicp_census.json) vs THIS wide census -- the A7-F1
   reconciliation table (era start, panel, events, floors, the
   2015-03..2017-11 cohort), recorded in the census artifact and the
   gate.

4. GATE (research/control/forex_ng4_run/p0_gate.json): ADDITIVE p0c
   section; the p0b ez_hicp_census section is retained VERBATIM as the
   superseded as-of-snapshot measurement; the top-level verdict is
   re-decided by the frozen floors on the plan-conformant wide-window
   basis (PASS -> the cycle proceeds to D1 per plan; floor shortfall or
   any canary failure => BLOCKED_DATA honest -- never an inferred PASS).

NO PnL, NO outcome, NO scoring anywhere in this runner (P0 census law).

Usage:
  p0c_wide_window_run.py --mode live     # the etiquette-paced pull
  p0c_wide_window_run.py --mode pinned [--pytest-exit 0 --pytest-log F]
                                        # verify-on-read, no network
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1 import plane_adapter as pa          # noqa: E402
from research.assets.forex_ng3 import revision_series as rs        # noqa: E402
from research.assets.forex_ng4 import ez_vintaged as ezv           # noqa: E402
from research.assets.forex_ng4 import td_probe as tp               # noqa: E402
from research.assets.forex_ng4 import wide_pull as wp              # noqa: E402

WORKTREE = REPO_ROOT
CADS_ROOT = pa.DEFAULT_CADS_STORE_ROOT                  # READ-ONLY store
OUT_DIR = os.path.join(WORKTREE, "research/control/forex_ng4_run")
MANIFEST_OUT = os.path.join(OUT_DIR, "p0c_wide_window_manifest.json")
CENSUS_OUT = os.path.join(OUT_DIR, "p0c_wide_window_census.json")
GATE_PATH = os.path.join(OUT_DIR, "p0_gate.json")
EURUSD_MANIFEST_OUT = os.path.join(OUT_DIR, "p0_spot_pin_manifest.json")
P0B_CENSUS_PATH = os.path.join(OUT_DIR, "p0b_ez_hicp_census.json")

#: This lane's dispatch base (the p0b handoff commit).
DISPATCH_BASE_SHA = "eafc2fec10077dbd78ca0ac59072b885a0254f06"
P0B_TASK_ID = "forex-ng4-p0b-ez-ingest"

US_RT_CADS_ADDRESS = (
    "7f18ec982374ce4dfb235f53f001327793df8e1c0077d31206de25aa3455ac94")

#: Frozen floors (plan sec 3 / p0a gate, unchanged by any lane).
EZ_PRINT_EVENT_FLOOR = 30          # A4
EZ_US_DIFFERENTIAL_FLOOR = 12      # A5

#: Fabricated obs months for the lookup canaries (must be found=False).
FABRICATED_OBS_MONTHS = ("2013-07-01", "2026-05-01")

#: The A7-F1 counterfactual cohort (obs months whose first prints the
#: as-of shape era-excluded and the wide shape re-admits).
COHORT_FIRST = "2015-03-01"
COHORT_LAST = "2017-11-01"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_state() -> dict:
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", WORKTREE, *args],
            capture_output=True, text=True, check=True).stdout.strip()
    return {
        "branch": git("branch", "--show-current"),
        "head_sha": git("rev-parse", "HEAD"),
        "clean_except_owned_new_files": git("status", "--porcelain=v1"),
    }


def write_json(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False)
        fh.write("\n")


def cads_object_path(address: str) -> str:
    return os.path.join(CADS_ROOT, "objects", address[:2], address)


def load_us_restricted() -> dict:
    """Rebuild the US restricted stream from the pinned CADS realtime
    archive (the ng3 restricted standard, machinery imported unmodified;
    CADS verify-on-read: address == sha256 of the bytes)."""
    path = cads_object_path(US_RT_CADS_ADDRESS)
    with open(path, "rb") as fh:
        raw = fh.read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != US_RT_CADS_ADDRESS:
        raise pa.VintageStructureError(
            f"CADS verify-on-read failed for the US rt archive: "
            f"{digest} != {US_RT_CADS_ADDRESS} (fail-closed)")
    payload = json.loads(raw.decode("utf-8"))
    us_rows = pa.parse_fred_vintaged(payload)
    return rs.build_restricted_stream("US", us_rows)


def _in_cohort(month: str) -> bool:
    return COHORT_FIRST <= month <= COHORT_LAST


def era_comparison(wide_block: dict, wide_floors: dict) -> dict:
    """Artifact-vs-artifact reconciliation: the committed p0b as-of
    census vs THIS wide census (the A7-F1 table)."""
    with open(P0B_CENSUS_PATH, "r", encoding="utf-8") as fh:
        p0b = json.load(fh)
    as_of = {
        "artifact": "research/control/forex_ng4_run/"
                    "p0b_ez_hicp_census.json",
        "basis": ("monthly ALFRED as-of snapshots 2017-12-01..2025-12-01; "
                  "every row's realtime window CLAMPED to the query day "
                  "(reconstructed panel)"),
        "realtime_era_start": p0b["panel"]["realtime_era_start"],
        "panel_rows": p0b["panel"]["rows"],
        "events_all": p0b["streams"]["events_all_count"],
        "usable": p0b["streams"]["restricted_report"]["usable_events"],
        "first_print_era": p0b["streams"]["restricted_report"][
            "first_print_era_events"],
        "backfill_history": p0b["streams"]["restricted_report"][
            "backfill_history_events"],
        "bulk_group_events": p0b["streams"]["restricted_report"][
            "bulk_group_events_total"],
        "restricted": p0b["streams"]["restricted_events"],
        "a4": p0b["floors"]["a4_ez_print_events"]["measured"],
        "a4_verdict": p0b["floors"]["a4_ez_print_events"]["verdict"],
        "a5": p0b["floors"]["a5_ez_us_differential_months"]["measured"],
        "q6": p0b["floors"]["q6_ez_recent_measured"]["measured"],
        "cohort_2015_03_2017_11": sum(
            1 for m in p0b["differential"]["ez_restricted_months"]
            if _in_cohort(m + "-01")),   # month_key "YYYY-MM" -> date
    }
    wide = {
        "artifact": "research/control/forex_ng4_run/"
                    "p0c_wide_window_census.json",
        "basis": ("ONE wide-window ALFRED pull realtime 2015-01-01.."
                  "9999-12-31; TRUE vintage windows (one row per value "
                  "version, the V8 archive shape)"),
        "realtime_era_start": wide_block["realtime_era_start"],
        "panel_rows": wide_block["rows"],
        "events_all": wide_block["events_all_count"],
        "usable": wide_block["usable_events"],
        "first_print_era": wide_block["first_print_era_events"],
        "backfill_history": wide_block["backfill_history_events"],
        "bulk_group_events": wide_block["bulk_group_events_total"],
        "restricted": wide_block["restricted_events"],
        "a4": wide_floors["a4_ez_print_events"]["measured"],
        "a4_verdict": wide_floors["a4_ez_print_events"]["verdict"],
        "a5": wide_floors["a5_ez_us_differential_months"]["measured"],
        "q6": wide_floors["q6_ez_recent_measured"]["measured"],
        "cohort_2015_03_2017_11": wide_block["cohort_2015_03_2017_11"],
    }
    return {
        "law": ("A7-F1 reconciliation, artifact-vs-artifact: the SAME "
                "frozen ng2/ng3 machinery on the SAME feed under two "
                "query shapes; era_start (min realtime_start over rows) "
                "is a function of the shape, not the feed"),
        "as_of_snapshot_basis_p0b": as_of,
        "wide_window_basis_p0c": wide,
    }


def build_census(mode: str, pull_ev: dict, payload: dict | None,
                 rows: list | None, manifest: dict | None) -> dict:
    """The EZ HICP census on the wide-window true-vintage bytes."""
    series_ident = {
        "ez_series_id": ezv.SERIES_ID,
        "ez_series_kind": "ez_hicp monthly (Euro area 19 HICP all-items "
                          "index, FRED/OECD MEI-derived)",
        "audit_finding": "NG4-A7-F1 (HIGH): the p0b A4 FAIL was an "
                         "artifact of the as-of snapshot ingest shape, "
                         "not a feed property",
        "prescription": (
            "a7_terminal_ng4.json required_owner_action: one wide-window "
            "ALFRED pull (realtime_start <= 2015-02-27 .. 9999-12-31), "
            "parse to VintageRows (true windows), feed UNMODIFIED to "
            "rs.build_restricted_stream, let the frozen floors decide"),
    }

    pull_block = {
        "mode": mode,
        "manifest_artifact": "research/control/forex_ng4_run/"
                             "p0c_wide_window_manifest.json",
        "manifest_sha256": (sha256_file(MANIFEST_OUT)
                            if os.path.exists(MANIFEST_OUT) else None),
        "status": pull_ev.get("status"),
        "query_shape": pull_ev.get("query_shape") or (
            manifest or {}).get("query_shape"),
        "pages": [{"offset": p.get("offset"), "status": p.get("status"),
                   "observations": p.get("observations")}
                  for p in pull_ev.get("pages", [])] or (
            {"count": len((manifest or {}).get("pages", [])),
             "source": "committed manifest (pinned mode)"} if manifest
        else []),
        "rows_total": pull_ev.get("rows_total"),
        "count_declared": pull_ev.get("count_declared"),
        "key_check": {
            "key_name": ezv.KEY_NAME,
            "key_source": ("gitignored root .env, loaded programmatically; "
                           "the value is never echoed into any output, "
                           "log, artifact or commit"),
            "key_present": pull_ev.get("key_present"),
        },
        "raw_bytes_policy": ("UNTRACKED_NEVER_COMMITTED "
                             "(data_raw/forex_ng4_ez/wide_window.json + "
                             "wide_window_pages/); the committed manifest "
                             "pins every file by sha256, verify-on-read"),
    }

    # ---- fail-closed short-circuit on pull failure ------------- #
    if pull_ev.get("status") != "COMPLETE":
        floors = {
            "a4_ez_print_events": {
                "measured": None, "floor": EZ_PRINT_EVENT_FLOOR,
                "verdict": "NOT_RUN",
                "law": "EZ print events with full realtime availability "
                       "windows inside S0 (ng2/ng3 restricted first-print "
                       "standard); requires a COMPLETE wide-window pull"},
            "a5_ez_us_differential_months": {
                "measured": None, "floor": EZ_US_DIFFERENTIAL_FLOOR,
                "verdict": "NOT_RUN",
                "law": "obs months carrying BOTH an EZ restricted event "
                       "and a US restricted event; requires a COMPLETE "
                       "wide-window pull"},
        }
        return {
            "schema": "forex_ng4_run/p0c_wide_window_census@1",
            "cycle_id": "FOREX-NG4",
            "task_id": "forex-ng4-p0c-wide-window",
            "measured_utc": now_utc(),
            "series_identification": series_ident,
            "pull": pull_block,
            "status": "PULL_FAILED",
            "floors": floors,
            "blockers": [
                "EZ wide-window pull FAILED (fail-closed): "
                + json.dumps({"status": pull_ev.get("status"),
                              "reason": pull_ev.get("reason")})[:300]],
            "verdict": "BLOCKED_DATA",
            "no_outcome_law": "NO PnL, NO outcome, NO scoring in this "
                              "census",
        }

    # ---- restricted stream (ng2/ng3 via import, UNMODIFIED) ----- #
    ez_stream = rs.build_restricted_stream("EZ", rows)
    era_start = min(r.realtime_start for r in rows)
    us_stream = load_us_restricted()
    diff = ezv.ez_us_differential_months(ez_stream["restricted"],
                                         us_stream["restricted"])
    q6 = rs.restricted_recent_events(ez_stream["restricted"])

    obs_dates = sorted({r.obs_date for r in rows})
    realtime_starts = sorted({r.realtime_start for r in rows})
    restricted_months = sorted({e.obs_month for e in ez_stream["restricted"]})
    cohort_months = [m for m in restricted_months if _in_cohort(m)]
    wide_block = {
        "rows": ez_stream["rows"],
        "rows_input": ez_stream["rows_input"],
        "obs_months": len(obs_dates),
        "obs_first": obs_dates[0] if obs_dates else None,
        "obs_last": obs_dates[-1] if obs_dates else None,
        "distinct_true_vintages": len(realtime_starts),
        "first_true_vintage": realtime_starts[0] if realtime_starts else None,
        "last_true_vintage": realtime_starts[-1] if realtime_starts else None,
        "realtime_era_start": era_start,
        "realtime_era_law": (
            "ng2 frozen law, UNMODIFIED, on true-window rows: era start = "
            "min realtime_start over the archive rows; obs months >= era "
            "start are first-print era, earlier months are backfill "
            "history (the archive's own clock zero, not a snapshot-day "
            "artifact)"),
        "open_version_stat": wp.open_version_stat(rows),
        "events_all_count": ez_stream["events_all_count"],
        "usable_events": ez_stream["report"]["usable_events"],
        "first_print_era_events": ez_stream["report"]["first_print_era_events"],
        "backfill_history_events": ez_stream["report"][
            "backfill_history_events"],
        "bulk_group_events_total": ez_stream["report"][
            "bulk_group_events_total"],
        "bulk_groups_ge_min": ez_stream["report"]["bulk_groups_ge_min"],
        "restricted_events": len(ez_stream["restricted"]),
        "restricted_months": restricted_months,
        "cohort_2015_03_2017_11": len(cohort_months),
        "cohort_2015_03_2017_11_months": cohort_months,
        "restricted_definition": rs.RESTRICTED_DEFINITION,
    }

    a4_measured = len(ez_stream["restricted"])
    a5_measured = diff["total"]
    floors = {
        "a4_ez_print_events": {
            "measured": a4_measured,
            "floor": EZ_PRINT_EVENT_FLOOR,
            "margin": a4_measured - EZ_PRINT_EVENT_FLOOR,
            "verdict": ("PASS" if a4_measured >= EZ_PRINT_EVENT_FLOOR
                        else "FAIL"),
            "law": "EZ print events (ng2/ng3 restricted first-print "
                   "standard: v1->v2 version gap, full availability "
                   "windows, S0-usable, first-print era, non-bulk) on the "
                   "wide-window TRUE-vintage archive rows",
        },
        "a5_ez_us_differential_months": {
            "measured": a5_measured,
            "floor": EZ_US_DIFFERENTIAL_FLOOR,
            "margin": a5_measured - EZ_US_DIFFERENTIAL_FLOOR,
            "verdict": ("PASS" if a5_measured >= EZ_US_DIFFERENTIAL_FLOOR
                        else "FAIL"),
            "law": "obs months carrying BOTH an EZ restricted event and "
                   "a US restricted event (US leg: pinned CADS "
                   "CPIAUCSL realtime archive, ng3 restricted standard)",
        },
        "q6_ez_recent_measured": {
            "measured": q6["count"],
            "window": q6["window"],
            "floor": None,
            "verdict": "MEASURED_NO_FLOOR_FROZEN",
            "law": "Q-6 law on the EZ restricted stream (last 24 "
                   "calendar months of S0, matched on v2 availability "
                   "days); measured and disclosed -- NO floor was ever "
                   "frozen for the EZ recent window (the ng3 >= 15 "
                   "floor was CA-specific), so no verdict is inferred",
        },
    }

    canaries = []
    for m in FABRICATED_OBS_MONTHS:
        look = rs.lookup_restricted({"EZ": ez_stream["restricted"]},
                                    "EZ", m)
        canaries.append({
            "kind": "fabricated_obs_month_lookup",
            "obs_month": m,
            "found": look["found"],
            "verdict": "PASS" if look["found"] is False else "FAIL",
        })
    # wide-response shape canary: true windows (NOT one clamped day),
    # count == rows, monthly obs grid, valid windows -- all executed by
    # the pure adapter on the merged document
    canaries.append({
        "kind": "wide_response_shape",
        "checks": ["count == observations (no truncation)",
                   "every row parses under the ng1 realtime parser",
                   "NOT a single-day-clamped as-of shape",
                   "obs dates all first-of-month",
                   "realtime windows well-formed"],
        "verdict": "PASS",
        "law": "wide_pull.validate_wide_response executed on the merged "
               "document (fail-closed: any violation raises and NOTHING "
               "is measured)",
    })
    canaries.append({
        "kind": "realtime_monotonicity",
        "verdict": "PASS",
        "law": "ng2 vintages_by_month STRICT realtime-monotonicity law "
               "executed on the true-window rows inside "
               "build_restricted_stream (a violation raises "
               "VintageMonotonicityError and NOTHING is built)",
    })
    canaries.append({
        "kind": "manifest_verify_on_read",
        "verdict": "PASS",
        "law": "load_pinned_wide re-hashed every pinned page AND the "
               "merged document against the committed manifest sha256s, "
               "re-merged the pages and required byte-equality with the "
               "pinned merged document, then re-ran the full "
               "wide-response canaries before any row entered the "
               "machinery",
    })
    canary_fail = [c for c in canaries if c.get("verdict") == "FAIL"]

    us_context = {
        "series": "CPIAUCSL (US/fred_cpiaucsl_rt.json, pinned via "
                  "CADS 7f18ec98..., verify-on-read address == "
                  "sha256 of bytes)",
        "restricted_events": len(us_stream["restricted"]),
        "restricted_months": sorted(
            {e.obs_month for e in us_stream["restricted"]}),
        "recent_24m_count": rs.restricted_recent_events(
            us_stream["restricted"])["count"],
        "law": ("ng2/ng3 restricted first-print standard on pinned "
                "bytes; measured as the US leg of the A5 EZ-vs-US "
                "differential"),
        "verdict": "MEASURED_CONTEXT_ONLY",
    }

    comparison = era_comparison(wide_block, floors)

    floors_ok = all(floors[k]["verdict"] == "PASS" for k in (
        "a4_ez_print_events", "a5_ez_us_differential_months"))
    blockers = []
    if not floors_ok:
        blockers.append(
            "EZ floors not reached on the wide-window archive: "
            + json.dumps({k: floors[k] for k in (
                "a4_ez_print_events", "a5_ez_us_differential_months")})
            [:300])
    if canary_fail:
        blockers.append("EZ wide census canary FAIL: "
                        + json.dumps(canary_fail)[:300])

    return {
        "schema": "forex_ng4_run/p0c_wide_window_census@1",
        "cycle_id": "FOREX-NG4",
        "task_id": "forex-ng4-p0c-wide-window",
        "measured_utc": now_utc(),
        "series_identification": series_ident,
        "pull": pull_block,
        "status": "MEASURED_ON_WIDE_WINDOW_TRUE_VINTAGES",
        "s0_window": {"start": rs.S0_WINDOW[0], "end": rs.S0_WINDOW[1]},
        "streams": wide_block,
        "differential": diff,
        "floors": floors,
        "canaries": canaries,
        "us_side_context": us_context,
        "era_comparison_p0b_vs_p0c": comparison,
        "blockers": blockers,
        "verdict": "PASS" if not blockers else "BLOCKED_DATA",
        "no_outcome_law": "NO PnL, NO outcome, NO scoring in this census",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("live", "pinned"), default="live",
                    help="live: the etiquette-paced wide-window pull; "
                         "pinned: verify-on-read the committed manifest, "
                         "no network")
    ap.add_argument("--pytest-exit", type=int, default=None)
    ap.add_argument("--pytest-log", default=None)
    args = ap.parse_args()

    gs = git_state()
    if gs["head_sha"] != DISPATCH_BASE_SHA:
        print(json.dumps({
            "error": "BASE_MISMATCH", "expected": DISPATCH_BASE_SHA,
            "measured": gs["head_sha"]}))
        return 2

    # ------------------- 1. pull / verify-on-read ------------------- #
    if args.mode == "live":
        key = ezv.load_fred_key()
        pull_ev = wp.fetch_wide_window(key)
        if pull_ev["status"] == "COMPLETE":
            manifest = wp.pin_wide_window(
                pull_ev["page_payloads"], MANIFEST_OUT,
                fetch_evidence=pull_ev)
            payload, rows = wp.load_pinned_wide(MANIFEST_OUT)
        else:
            manifest = None
            payload, rows = None, None
    else:
        with open(MANIFEST_OUT, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        payload, rows = wp.load_pinned_wide(MANIFEST_OUT)
        pull_ev = {
            "status": manifest.get("status"),
            "query_shape": manifest.get("query_shape"),
            "key_present": manifest.get("key_present"),
            "rows_total": manifest.get("merged", {}).get("observations"),
            "count_declared": manifest.get("merged", {}).get(
                "count_declared"),
            "pages": [], "page_payloads": [],
        }

    # ------------------- 2. census --------------------------------- #
    census = build_census(args.mode, pull_ev, payload, rows, manifest)
    write_json(CENSUS_OUT, census)

    # ------------------- 3. substrate re-verification --------------- #
    substrate = {"verdict": "NOT_RUN"}
    try:
        with open(EURUSD_MANIFEST_OUT, "r", encoding="utf-8") as fh:
            committed = json.load(fh)
        pinned_sha = committed["files"]["EURUSD"]["copy_sha256"]
        ev = tp.verify_pinned_bytes(tp.PIN_DIR_DEFAULT, pinned_sha)
        substrate = {
            "check": "EURUSD pinned bytes vs the committed p0 spot pin "
                     "manifest (verify-on-read, no network)",
            "copy_sha256": ev["copy_sha256"],
            "verdict": "PASS" if ev["copy_sha256"] == pinned_sha
                       else "FAIL",
        }
    except (tp.ProbeError, OSError, KeyError, ValueError) as exc:
        substrate = {"verdict": "FAIL", "error": repr(exc)[:300]}

    # ------------------- 4. gate upgrade (additive p0c) ------------- #
    with open(GATE_PATH, "r", encoding="utf-8") as fh:
        gate = json.load(fh)
    blockers: list[str] = []
    if census["verdict"] != "PASS":
        for b in census.get("blockers", []):
            blockers.append("EZ wide-window census (p0c): " + b[:300])
    if substrate["verdict"] != "PASS":
        blockers.append("substrate re-verification failed (EURUSD pinned "
                        "bytes vs committed manifest): "
                        + str(substrate.get("error", ""))[:200])

    test_cmd = (f"cd {WORKTREE} && "
                "/Users/hoangminhlong/my-quantitative/.venv/bin/python "
                "-m pytest tests/test_forex_ng4_p0.py -q")
    tests_row = {"task": "forex-ng4-p0c-wide-window",
                 "command": test_cmd, "verdict": "NOT_RUN"}
    if args.pytest_exit is not None:
        tests_row["exit_code"] = args.pytest_exit
        tests_row["verdict"] = "PASS" if args.pytest_exit == 0 else "FAIL"
        if args.pytest_log and os.path.exists(args.pytest_log):
            tests_row["output_tail"] = open(args.pytest_log).read()[-800:]
        if tests_row["verdict"] != "PASS":
            blockers.append("tests/test_forex_ng4_p0.py did not PASS")

    gate["task_id"] = "forex-ng4-p0c-wide-window"
    gate["prior_task_id"] = P0B_TASK_ID
    gate["measured_utc"] = now_utc()
    gate["git"] = gs
    gate["p0c_dispatch_base_sha"] = DISPATCH_BASE_SHA
    gate["p0c_base_match"] = gs["head_sha"] == DISPATCH_BASE_SHA
    gate["section_provenance"]["p0c_wide_window_census"] = (
        "measured by task forex-ng4-p0c-wide-window (A7-F1 remediation, "
        "audit prescription): ONE wide-window ALFRED pull of "
        "CP0000EZ19M086NEST (realtime 2015-01-01..9999-12-31, true "
        "vintage windows) fed UNMODIFIED through the ng2/ng3 restricted "
        "machinery; SUPERSEDES the p0b ez_hicp_census A4 verdict (the "
        "as-of snapshot shape's clamped clock collapsed the frozen era "
        "law to the first snapshot day -- an ingest-shape artifact per "
        "NG4-A7-F1); the p0b section below is retained VERBATIM as "
        "superseded evidence")
    gate["substrate_reverification"] = substrate
    gate["p0c_wide_window_census"] = {
        "artifact": "research/control/forex_ng4_run/"
                    "p0c_wide_window_census.json",
        "sha256": sha256_file(CENSUS_OUT),
        "series_identification": census["series_identification"],
        "bytes_source": (
            "P0C_WIDE_WINDOW_ALFRED_PULL: ONE wide-window query "
            "realtime 2015-01-01..9999-12-31 (+ limit/offset paging of "
            "the same shape), true vintage windows (untracked raw bytes "
            "under data_raw/forex_ng4_ez/wide_window.json + "
            "wide_window_pages/ + committed sha manifest "
            "p0c_wide_window_manifest.json, verify-on-read, merged == "
            "merge(pages))"),
        "pull_status": census["pull"]["status"],
        "manifest_sha256": census["pull"]["manifest_sha256"],
        "panel": {k: (census.get("streams", {}) or {}).get(k) for k in (
            "rows", "obs_months", "distinct_true_vintages",
            "first_true_vintage", "last_true_vintage",
            "realtime_era_start", "restricted_events")},
        "streams": {k: (census.get("streams", {}) or {}).get(k) for k in (
            "events_all_count", "restricted_events")},
        "floors": census["floors"],
        "canaries": census.get("canaries"),
        "us_side_context": census.get("us_side_context"),
        "era_comparison_p0b_vs_p0c": census.get("era_comparison_p0b_vs_p0c"),
        "blockers": census.get("blockers"),
        "verdict": census["verdict"],
    }
    # additive across tasks, latest-wins within this task: rows carry a
    # task tag; a re-run replaces only THIS task's earlier row (e.g. the
    # live run's NOT_RUN placeholder) and never touches prior tasks'
    # untagged rows
    gate["commands"] = (
        [row for row in gate.get("commands", [])
         if row.get("task") != "forex-ng4-p0c-wide-window"]
        + [tests_row])
    gate["evidence_paths"]["ng4_modules"] = list(
        gate["evidence_paths"].get("ng4_modules", [])) + [
        "research/assets/forex_ng4/wide_pull.py"]
    gate["evidence_paths"]["ez_wide_window_bytes"] = (
        "data_raw/forex_ng4_ez/wide_window.json + wide_window_pages/ "
        "(UNTRACKED; committed manifest p0c_wide_window_manifest.json "
        "carries the sha256 per file)")
    gate["evidence_paths"]["a7_audit"] = (
        "research/control/forex_ng4_run/audits/a7_terminal_ng4.json "
        "(finding NG4-A7-F1 + required_owner_action -- this lane's "
        "prescription)")
    gate["blockers"] = blockers
    gate["verdict"] = "PASS" if not blockers else "BLOCKED_DATA"
    gate["verdict_law"] = (
        "plan sec 2-3 (upgraded by task forex-ng4-p0c-wide-window, the "
        "A7-F1 remediation): the gate is PASS iff the inherited-pin "
        "substrate and the EURUSD probe (p0a, carried forward with the "
        "pinned bytes re-verified) hold AND the EZ HICP floors are "
        "reached on the plan-conformant wide-window TRUE-vintage basis "
        "(A4 >= 30 EZ print events; A5 >= 12 EZ-vs-US differential "
        "months; the same frozen ng2/ng3 machinery, fed UNMODIFIED, "
        "floors unchanged); pull failure, floor shortfall or any canary "
        "failure => BLOCKED_DATA honest -- never an inferred PASS.  The "
        "p0b as-of-snapshot A4 measurement is retained as superseded "
        "evidence (ingest-shape artifact per NG4-A7-F1).  On PASS the "
        "cycle proceeds to D1 per plan.")
    write_json(GATE_PATH, gate)

    print(json.dumps({
        "mode": args.mode,
        "pull_status": census["pull"]["status"],
        "pages": len(census["pull"].get("pages", []))
        if isinstance(census["pull"].get("pages"), list) else
        census["pull"].get("pages"),
        "rows_total": census["pull"].get("rows_total"),
        "era_start": (census.get("streams", {}) or {}).get(
            "realtime_era_start"),
        "ez_events_all": (census.get("streams", {}) or {}).get(
            "events_all_count"),
        "ez_restricted": (census.get("streams", {}) or {}).get(
            "restricted_events"),
        "cohort_2015_03_2017_11": (census.get("streams", {}) or {}).get(
            "cohort_2015_03_2017_11"),
        "floors": {k: {"measured": v.get("measured"),
                       "verdict": v.get("verdict")}
                   for k, v in census["floors"].items()},
        "substrate": substrate["verdict"],
        "census": census["verdict"],
        "gate": gate["verdict"],
        "blockers": blockers,
    }, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
