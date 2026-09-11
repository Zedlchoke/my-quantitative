#!/usr/bin/env python
"""FOREX-NG4 P0b runner: EZ HICP vintaged re-ingest + realtime census +
gate EZ-section upgrade, under the owner directive of 2026-09-12 and
plans/PLAN_forex_ng4.md sec 2-3.

Measures, fail-closed:

1. INGEST (research/assets/forex_ng4/ez_vintaged.py): 97 monthly ALFRED
   as-of snapshots of CP0000EZ19M086NEST (2017-12-01 warmup ..
   2025-12-01) under the owner's EXISTING FRED entitlement
   (FRED_API_KEY from the gitignored root .env, loaded
   programmatically, NEVER echoed -- only key_present is recorded).
   Etiquette: <= 1 request / 1.2 s + exponential backoff (2/4/8 s) on
   retryable errors, max 3 retries; key/quota/deterministic refusals
   STOP fail-closed.  Raw bytes pinned UNTRACKED under
   data_raw/forex_ng4_ez/vintages/; the COMMITTED manifest carries the
   per-file sha256 (verify-on-read).

2. CENSUS (ng2/ng3 machinery VIA IMPORT, unmodified): the snapshots
   are collapsed to archive-shaped vintaged rows (the panel law in
   ez_vintaged.build_realtime_panel) and fed to
   ng3.build_restricted_stream("EZ", ...) -- dedupe, STRICT
   realtime-monotonicity fail-closed, v1->v2 first-to-second-version
   events, S0-window usable filter, first-print-era restriction and
   bulk re-referencing exclusion.  Floors: A4 EZ print events >= 30;
   A5 EZ-vs-US differential months >= 12 (US leg rebuilt from the
   pinned CADS CPIAUCSL realtime archive with the same machinery);
   Q-6 recent measured (no floor frozen for EZ).  Canaries: fabricated
   obs months must look up found=False; response integrity (clamped
   windows, count truncation, monthly grid) re-verified verify-on-read.

3. GATE UPGRADE (research/control/forex_ng4_run/p0_gate.json): the EZ
   section is replaced by this measurement (PASS if the floors are
   reached, BLOCKED_DATA otherwise / on ingest failure -- plan sec 2);
   the p0a-measured sections (inherited pin re-verification, EURUSD TD
   probe) are carried forward verbatim with their provenance recorded,
   and the EURUSD pinned-bytes substrate is re-verified here
   (verify-on-read against the committed manifest, no network).

NO PnL, NO outcome, NO scoring anywhere in this runner (P0 census law).

Usage:
  p0b_ez_ingest_run.py --mode live     # the etiquette-paced ingest
  p0b_ez_ingest_run.py --mode pinned [--pytest-exit 0 --pytest-log FILE]
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
from research.assets.forex_ng4 import ez_census as ezp0a           # noqa: E402
from research.assets.forex_ng4 import ez_vintaged as ezv           # noqa: E402
from research.assets.forex_ng4 import td_probe as tp               # noqa: E402

WORKTREE = REPO_ROOT
CADS_ROOT = pa.DEFAULT_CADS_STORE_ROOT                  # READ-ONLY store
OUT_DIR = os.path.join(WORKTREE, "research/control/forex_ng4_run")
MANIFEST_OUT = os.path.join(OUT_DIR, "p0b_ez_vintages_manifest.json")
CENSUS_OUT = os.path.join(OUT_DIR, "p0b_ez_hicp_census.json")
GATE_PATH = os.path.join(OUT_DIR, "p0_gate.json")
EURUSD_MANIFEST_OUT = os.path.join(OUT_DIR, "p0_spot_pin_manifest.json")

#: This lane's dispatch base (the p0a substance commit).
DISPATCH_BASE_SHA = "730aaafdfaf74c9e0734d8526dcc842200565c80"
P0A_TASK_ID = "forex-ng4-p0-census"
P0A_BASE_SHA = "330a6cd0c829082d03f2658e2cebe63ef1205b2d"

US_RT_CADS_ADDRESS = (
    "7f18ec982374ce4dfb235f53f001327793df8e1c0077d31206de25aa3455ac94")

#: Frozen floors (plan sec 3 / p0a gate, unchanged by this lane).
EZ_PRINT_EVENT_FLOOR = 30          # A4
EZ_US_DIFFERENTIAL_FLOOR = 12      # A5

#: Fabricated obs months for the lookup canaries (must be found=False).
FABRICATED_OBS_MONTHS = ("2013-07-01", "2026-05-01")


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
    archive (the ng3 restricted standard, machinery imported
    unmodified; CADS verify-on-read: address == sha256 of the bytes)."""
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


def build_census(mode: str, ingest_ev: dict, vintages: list) -> dict:
    """The EZ HICP census on the re-ingested vintaged bytes."""
    series_ident = {
        "ez_series_id": ezv.SERIES_ID,
        "ez_series_kind": ezp0a.EZ_SERIES_KIND,
        "dispatch_suggested_series_id": ezp0a.DISPATCH_SUGGESTED_SERIES_ID,
        "dispatch_id_correction": (
            f"{ezp0a.DISPATCH_SUGGESTED_SERIES_ID} appears in NO manifest "
            "or census artifact anywhere in the repo (p0a measured); the "
            "EZ HICP series the V8 evidence pinned and this lane "
            f"re-ingests is {ezv.SERIES_ID}"),
        "p0a_history": (
            "the p0a census measured the V8 manifest pin 886f0afe... "
            "against NO resolvable bytes (BLOCKED_DATA); the owner "
            "directive 2026-09-12 authorized this re-ingest under the "
            "existing FRED entitlement"),
    }

    ingest_block = {
        "mode": mode,
        "manifest_artifact": "research/control/forex_ng4_run/"
                             "p0b_ez_vintages_manifest.json",
        "manifest_sha256": sha256_file(MANIFEST_OUT),
        "status": ingest_ev.get("status"),
        "vintages_planned": ingest_ev.get("vintage_count_planned"),
        "vintages_fetched": ingest_ev.get("vintage_count_fetched"),
        "failures": ingest_ev.get("failures", []),
        "key_check": {
            "key_name": ezv.KEY_NAME,
            "key_source": ("gitignored root .env, loaded programmatically; "
                           "the value is never echoed into any output, "
                           "log, artifact or commit"),
            "key_present": ingest_ev.get("key_present"),
        },
        "raw_bytes_policy": ("UNTRACKED_NEVER_COMMITTED "
                             "(data_raw/forex_ng4_ez/vintages/); the "
                             "committed manifest pins every file by "
                             "sha256, verify-on-read"),
    }

    # ---- fail-closed short-circuit on ingest failure ------------- #
    if ingest_ev.get("status") != "COMPLETE":
        floors = {
            "a4_ez_print_events": {
                "measured": None, "floor": EZ_PRINT_EVENT_FLOOR,
                "verdict": "NOT_RUN",
                "law": "EZ print events with full realtime availability "
                       "windows inside S0 (ng2/ng3 restricted first-print "
                       "standard); requires COMPLETE vintaged ingest"},
            "a5_ez_us_differential_months": {
                "measured": None, "floor": EZ_US_DIFFERENTIAL_FLOOR,
                "verdict": "NOT_RUN",
                "law": "obs months carrying BOTH an EZ restricted event "
                       "and a US restricted event; requires COMPLETE "
                       "vintaged ingest"},
        }
        return {
            "schema": "forex_ng4_run/p0b_ez_hicp_census@2",
            "cycle_id": "FOREX-NG4",
            "task_id": "forex-ng4-p0b-ez-ingest",
            "measured_utc": now_utc(),
            "series_identification": series_ident,
            "ingest": ingest_block,
            "status": "INGEST_FAILED",
            "floors": floors,
            "blockers": [
                "EZ vintaged ingest FAILED (fail-closed): "
                + json.dumps(ingest_ev.get("failures", [])[:1])[:300]],
            "verdict": "BLOCKED_DATA",
            "no_outcome_law": "NO PnL, NO outcome, NO scoring in this "
                              "census",
        }

    # ---- panel + restricted stream (ng2/ng3 via import) ---------- #
    panel = ezv.build_realtime_panel(vintages)
    ez_stream = rs.build_restricted_stream("EZ", panel["rows"])
    era_start = min(r.realtime_start for r in panel["rows"])
    us_stream = load_us_restricted()
    diff = ezv.ez_us_differential_months(ez_stream["restricted"],
                                         us_stream["restricted"])
    q6 = rs.restricted_recent_events(ez_stream["restricted"])

    obs_dates = sorted({r.obs_date for r in panel["rows"]})
    panel_block = {
        "rows": panel["rows_count"],
        "snapshots": panel["snapshots"],
        "first_snapshot": panel["first_snapshot"],
        "last_snapshot": panel["last_snapshot"],
        "obs_months": panel["obs_months"],
        "obs_first": obs_dates[0] if obs_dates else None,
        "obs_last": obs_dates[-1] if obs_dates else None,
        "versions": panel["versions"],
        "value_changes": panel["value_changes"],
        "realtime_era_start": era_start,
        "realtime_era_law": (
            "ng2 frozen law: era start = min realtime_start over the "
            "panel rows = the first snapshot day (2017-12-01); obs months "
            ">= era start are first-print era, earlier months are "
            "backfill history.  Disclosed loss: the 2017-11 obs month "
            "(true first print ~2017-12-15, inside coverage) is "
            "era-excluded by this frozen law -- one month, caused by the "
            "mandated warmup snapshot choice"),
        "reconstruction_law": panel["reconstruction_law"],
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
                   "windows, S0-usable, first-print era, non-bulk) on "
                   "the re-ingested monthly ALFRED panel",
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
    planned = ezv.vintage_dates()
    grid_ok = (ingest_ev.get("vintage_count_planned") == len(planned)
               and ingest_ev.get("vintage_count_fetched") == len(planned)
               and planned[0] == ezv.VINTAGE_START
               and planned[-1] == ezv.VINTAGE_END)
    canaries.append({
        "kind": "vintage_grid_exactness",
        "expected": {"first": ezv.VINTAGE_START, "last": ezv.VINTAGE_END,
                     "count": len(planned)},
        "verdict": "PASS" if grid_ok else "FAIL",
    })
    canaries.append({
        "kind": "realtime_monotonicity",
        "verdict": "PASS",
        "law": "ng2 vintages_by_month STRICT realtime-monotonicity law "
               "executed on the panel inside build_restricted_stream "
               "(a violation raises VintageMonotonicityError and "
               "NOTHING is built); the panel self-check additionally "
               "asserts strictly-increasing version starts and valid "
               "windows per obs month",
    })
    canaries.append({
        "kind": "manifest_verify_on_read",
        "verdict": "PASS",
        "law": "load_pinned_vintages re-hashed every vintage file "
               "against the committed manifest sha256 and re-ran the "
               "response-integrity canaries (clamped as-of windows, "
               "count truncation, monthly obs grid) before the panel "
               "was built",
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

    floors_ok = all(floors[k]["verdict"] == "PASS" for k in (
        "a4_ez_print_events", "a5_ez_us_differential_months"))
    blockers = []
    if not floors_ok:
        blockers.append(
            "EZ floors not reached on the re-ingested panel: "
            + json.dumps({k: floors[k] for k in (
                "a4_ez_print_events", "a5_ez_us_differential_months")})
            [:300])
    if canary_fail:
        blockers.append("EZ census canary FAIL: "
                        + json.dumps(canary_fail)[:300])

    return {
        "schema": "forex_ng4_run/p0b_ez_hicp_census@2",
        "cycle_id": "FOREX-NG4",
        "task_id": "forex-ng4-p0b-ez-ingest",
        "measured_utc": now_utc(),
        "series_identification": series_ident,
        "ingest": ingest_block,
        "status": "MEASURED_ON_REINGESTED_VINTAGES",
        "s0_window": {"start": rs.S0_WINDOW[0], "end": rs.S0_WINDOW[1]},
        "panel": panel_block,
        "streams": {
            "economy": "EZ",
            "rows_input": ez_stream["rows_input"],
            "rows": ez_stream["rows"],
            "exact_duplicate_rows_removed":
                ez_stream["exact_duplicate_rows_removed"],
            "distinct_vintages": ez_stream["distinct_vintages"],
            "months_carried": ez_stream["months_carried"],
            "months_with_second_vintage":
                ez_stream["months_with_second_vintage"],
            "events_all_count": ez_stream["events_all_count"],
            "restricted_report": ez_stream["report"],
            "restricted_events": len(ez_stream["restricted"]),
            "restricted_definition": rs.RESTRICTED_DEFINITION,
        },
        "differential": diff,
        "floors": floors,
        "canaries": canaries,
        "us_side_context": us_context,
        "blockers": blockers,
        "verdict": "PASS" if not blockers else "BLOCKED_DATA",
        "no_outcome_law": "NO PnL, NO outcome, NO scoring in this census",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("live", "pinned"), default="live",
                    help="live: the etiquette-paced ingest; pinned: "
                         "verify-on-read the committed manifest, no "
                         "network")
    ap.add_argument("--pytest-exit", type=int, default=None)
    ap.add_argument("--pytest-log", default=None)
    args = ap.parse_args()

    gs = git_state()
    if gs["head_sha"] != DISPATCH_BASE_SHA:
        print(json.dumps({
            "error": "BASE_MISMATCH", "expected": DISPATCH_BASE_SHA,
            "measured": gs["head_sha"]}))
        return 2

    # ------------------- 1. ingest / verify-on-read ----------------- #
    if args.mode == "live":
        key = ezv.load_fred_key()
        ingest_ev = ezv.ingest_all(key, MANIFEST_OUT)
        vintages = ezv.load_pinned_vintages(MANIFEST_OUT) \
            if ingest_ev.get("status") == "COMPLETE" else []
    else:
        with open(MANIFEST_OUT, "r", encoding="utf-8") as fh:
            ingest_ev = json.load(fh)
        vintages = ezv.load_pinned_vintages(MANIFEST_OUT)

    # ------------------- 2. census --------------------------------- #
    census = build_census(args.mode, ingest_ev, vintages)
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

    # ------------------- 4. gate upgrade ---------------------------- #
    with open(GATE_PATH, "r", encoding="utf-8") as fh:
        gate = json.load(fh)
    blockers: list[str] = []
    if census["verdict"] != "PASS":
        for b in census.get("blockers", []):
            blockers.append("EZ HICP vintaged census: " + b[:300])
    if substrate["verdict"] != "PASS":
        blockers.append("substrate re-verification failed (EURUSD pinned "
                        "bytes vs committed manifest): "
                        + str(substrate.get("error", ""))[:200])

    test_cmd = (f"cd {WORKTREE} && "
                "/Users/hoangminhlong/my-quantitative/.venv/bin/python "
                "-m pytest tests/test_forex_ng4_p0.py -q")
    tests_row = {"command": test_cmd, "verdict": "NOT_RUN"}
    if args.pytest_exit is not None:
        tests_row["exit_code"] = args.pytest_exit
        tests_row["verdict"] = "PASS" if args.pytest_exit == 0 else "FAIL"
        if args.pytest_log and os.path.exists(args.pytest_log):
            tests_row["output_tail"] = open(args.pytest_log).read()[-800:]
        if tests_row["verdict"] != "PASS":
            blockers.append("tests/test_forex_ng4_p0.py did not PASS")

    gate["task_id"] = "forex-ng4-p0b-ez-ingest"
    gate["prior_task_id"] = P0A_TASK_ID
    gate["measured_utc"] = now_utc()
    gate["git"] = gs
    gate["dispatch_base_sha"] = DISPATCH_BASE_SHA
    gate["p0a_base_sha"] = P0A_BASE_SHA
    gate["base_match"] = gs["head_sha"] == DISPATCH_BASE_SHA
    gate["section_provenance"] = {
        "pin_reverification": (
            f"measured by task {P0A_TASK_ID} at {P0A_BASE_SHA} "
            "(carried forward VERBATIM; read-only evidence roots "
            "unchanged on disk)"),
        "eurusd_td_probe": (
            f"measured by task {P0A_TASK_ID} at {P0A_BASE_SHA} "
            "(carried forward VERBATIM; the pinned-bytes substrate is "
            "re-verified by THIS task -- see substrate_reverification)"),
        "ez_hicp_census": (
            "REPLACED by task forex-ng4-p0b-ez-ingest: measured on the "
            "re-ingested monthly ALFRED vintages (owner directive "
            "2026-09-12); the p0a artifact p0_ez_hicp_census.json "
            "remains on disk untouched as the BLOCKED_DATA evidence "
            "of the lost V8 bytes"),
    }
    gate["substrate_reverification"] = substrate
    gate["ez_hicp_census"] = {
        "artifact": "research/control/forex_ng4_run/"
                    "p0b_ez_hicp_census.json",
        "sha256": sha256_file(CENSUS_OUT),
        "series_identification": census["series_identification"],
        "bytes_source": (
            "P0B_REINGEST_ALFRED_MONTHLY_VINTAGES: 97 as-of snapshots "
            "2017-12-01..2025-12-01 (untracked raw bytes under "
            "data_raw/forex_ng4_ez/vintages/ + committed sha manifest "
            "p0b_ez_vintages_manifest.json, verify-on-read)"),
        "ingest_status": census["ingest"]["status"],
        "manifest_sha256": census["ingest"]["manifest_sha256"],
        "panel": {k: census.get("panel", {}).get(k) for k in (
            "rows", "snapshots", "obs_months", "versions",
            "value_changes", "realtime_era_start")},
        "streams": {k: (census.get("streams", {}).get(k)) for k in (
            "events_all_count", "restricted_events")},
        "floors": census["floors"],
        "canaries": census.get("canaries"),
        "us_side_context": census.get("us_side_context"),
        "blockers": census.get("blockers"),
        "verdict": census["verdict"],
    }
    gate["commands"] = [tests_row]
    gate["evidence_paths"] = {
        "cads_store_root": CADS_ROOT + " (READ-ONLY)",
        "ng1_adapter_reused_unmodified":
            "research/assets/forex_ng1/plane_adapter.py",
        "ng3_module_reused_unmodified":
            "research/assets/forex_ng3/revision_series.py (imports the "
            "ng2 machinery unmodified)",
        "ng4_modules": ["research/assets/forex_ng4/td_probe.py",
                        "research/assets/forex_ng4/ez_census.py",
                        "research/assets/forex_ng4/ez_vintaged.py"],
        "eurusd_pinned_bytes": ("data_raw/forex_ng4_spot/EURUSD.json "
                                "(UNTRACKED; committed manifest carries "
                                "the sha256)"),
        "ez_vintaged_bytes": ("data_raw/forex_ng4_ez/vintages/ "
                              "(UNTRACKED; committed manifest "
                              "p0b_ez_vintages_manifest.json carries "
                              "the sha256 per file)"),
        "p0a_ez_census_artifact_retained":
            "research/control/forex_ng4_run/p0_ez_hicp_census.json",
        "tests": "tests/test_forex_ng4_p0.py",
    }
    gate["blockers"] = blockers
    gate["verdict"] = "PASS" if not blockers else "BLOCKED_DATA"
    gate["verdict_law"] = (
        "plan sec 2-3 (upgraded by task forex-ng4-p0b-ez-ingest): the "
        "gate is PASS iff the inherited-pin substrate and the EURUSD "
        "probe (p0a, carried forward with the pinned bytes re-verified) "
        "hold AND the EZ HICP floors are reached on the re-ingested "
        "vintaged bytes (A4 >= 30 EZ print events; A5 >= 12 EZ-vs-US "
        "differential months); ingest failure, floor shortfall or any "
        "canary failure => BLOCKED_DATA honest -- never an inferred "
        "PASS")
    write_json(GATE_PATH, gate)

    print(json.dumps({
        "mode": args.mode,
        "ingest_status": census["ingest"]["status"],
        "vintages_fetched": census["ingest"]["vintages_fetched"],
        "panel_rows": (census.get("panel", {}) or {}).get("rows"),
        "ez_events_all": (census.get("streams", {}) or {}).get(
            "events_all_count"),
        "ez_restricted": (census.get("streams", {}) or {}).get(
            "restricted_events"),
        "floors": {k: {"measured": v.get("measured"),
                       "verdict": v.get("verdict")}
                   for k, v in census["floors"].items()},
        "substrate": substrate["verdict"],
        "census": census["verdict"],
        "gate": gate["verdict"],
        "blockers": blockers,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
