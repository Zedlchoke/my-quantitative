#!/usr/bin/env python
"""FOREX-NG1 P0 runner: data authority + platform v3 adoption gate.

Measures, fail-closed, the plan section 3 P0 deliverables:

1. S2 re-pin: CADS address 07d1e0d5... resolves, re-hashes clean, and its
   5-file FRED vintaged manifest verifies against live bytes (US leg via
   its CADS object; GB/CA/AU/NZ legs via the V9 staging bytes named by
   the V9 P0 census staging policy).
2. S3 re-pin: the five S3 entries resolve through consume_via_plane
   (GRANTED -> CADS resolve verify-on-read -> manifest-verified query)
   and re-hash clean.
3. Vintaged GB/CA channel proof (V9 HIGH finding binding): structural
   proof that the GB/CA PIT channels are vintaged archives (per-value
   realtime windows) and NOT current-vintage revised-in-place tables
   (the ONS/StatCan official tables are read structurally and recorded
   as CURRENT_VINTAGE_SNAPSHOT continuation-only).
4. Bounded shadow parity pilot: plane-read bytes vs V9 staging bytes,
   digest equality (+ window-overlap content parity for tabular legs).
5. Tail-trim measurement + the S0 window actually used.
6. Announcement-instant PIT census from the pinned print calendars
   (GB/AU/NZ v5 pins, CA v3 pin) + US realtime first-appearances, with
   publication-timestamp evidence per instant and two fabricated
   canary instants that must FAIL lookup.

Publishes p0_announcement_census.json and p0_gate.json. Verdict is
PASS only when every section passes; any digest mismatch or missing
vintage proof is BLOCKED_DATA (honest, never invented).
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

from research.assets.forex_ng1 import plane_adapter as pa  # noqa: E402
from research.platform_v3.cads import CADSError  # noqa: E402

WORKTREE = REPO_ROOT
V9_ROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
           "forex-free-v9/integration")           # READ-ONLY evidence
CADS_ROOT = pa.DEFAULT_CADS_STORE_ROOT              # READ-ONLY store
OUT_DIR = os.path.join(WORKTREE, "research/control/forex_ng1_run")
SCRATCH = "/tmp/forex_ng1_p0_scratch"

V9_S0_WINDOW = ("2018-04-04", "2025-07-24")         # V9 census, inherited
NG1_S0_START = "2018-04-04"                          # inherited start

FRED_LEGS = {
    "GB": ("GBRCPIALLMINMEI", "fred_vintaged/GBRCPIALLMINMEI.json"),
    "CA": ("CANCPIALLMINMEI", "fred_vintaged/CANCPIALLMINMEI.json"),
    "AU": ("AUSCPIALLQINMEI", "fred_vintaged/AUSCPIALLQINMEI.json"),
    "NZ": ("NZLCPIALLQINMEI", "fred_vintaged/NZLCPIALLQINMEI.json"),
}

US_RT_CADS_ENTRY = "US/fred_cpiaucsl_rt.json"


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
        "clean": not git("status", "--porcelain=v1"),
    }


def cads_object_path(address: str) -> str:
    return os.path.join(CADS_ROOT, "objects", address[:2], address)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pytest-exit", type=int, default=None,
                    help="exit code of the mandated pytest command")
    ap.add_argument("--pytest-log", default=None,
                    help="path holding the pytest tail (evidence)")
    args = ap.parse_args()

    commands: list[dict] = []
    blockers: list[str] = []

    gs = git_state()
    registry = pa.load_registry()
    ga4 = pa.ga4_granted()
    granted_check = {
        "journal": pa.DEFAULT_AUTHORITY_JOURNAL,
        "ga4_gate": pa.DEFAULT_GA4_GATE,
        "S2:fred-keyed-vintage-classes": registry.verdict(
            "S2:fred-keyed-vintage-classes"),
        "S3:forex-print-calendars": registry.verdict(
            "S3:forex-print-calendars"),
        "S3:forex-announcement-ledger": registry.verdict(
            "S3:forex-announcement-ledger"),
        "ga4_granted_count": len(ga4),
        "verdict": "PASS" if all(
            registry.verdict(s) == "GRANTED" for s in (
                "S2:fred-keyed-vintage-classes",
                "S3:forex-print-calendars",
                "S3:forex-announcement-ledger")) else "FAIL",
    }
    if granted_check["verdict"] != "PASS":
        blockers.append("authority registry/GA4 granted check failed")

    # ---------------- 1. S2 re-pin ------------------------------------ #
    try:
        s2_manifest = pa.consume_s2_manifest(CADS_ROOT, registry, ga4)
        s2_files = pa.verify_s2_files(s2_manifest, {
            "US/fred_cpiaucsl_rt.json": cads_object_path(
                "7f18ec982374ce4dfb235f53f001327793df8e1c0077d31206de25aa3455ac94"),
            **{rel: os.path.join(V9_ROOT, "data_raw/forex_free_v9_cpi", rel)
               for _, rel in FRED_LEGS.values()},
        })
        s2 = {
            "cads_address": pa.S2_PINNED_ADDRESS,
            "digest": pa.S2_PINNED_ADDRESS,   # resolve() re-hashed clean
            "files": s2_files,
            "file_count": len(s2_manifest["series"]),
            "verdict": ("PASS" if len(s2_manifest["series"]) == 5
                        and all(f["match"] for f in s2_files.values())
                        else "FAIL"),
        }
    except (CADSError, pa.ConsumptionRefused, pa.VintageStructureError,
            OSError) as exc:
        s2 = {"cads_address": pa.S2_PINNED_ADDRESS, "verdict": "FAIL",
              "error": repr(exc)[:400]}
    if s2["verdict"] != "PASS":
        blockers.append("S2 re-pin failed (digest/manifest mismatch)")

    # ---------------- 2. S3 re-pin via consume_via_plane --------------- #
    s3_rows = {}
    for entry in pa.S3_ENTRY_NAMES:
        try:
            consumed = pa.consume_via_plane(
                registry, CADS_ROOT, "S3:forex-announcement-ledger",
                entry, SCRATCH, ga4=ga4)
            row = {
                "resolved_address": consumed.resolved_address,
                "bytes": consumed.nbytes,
                "query_verdict": consumed.query_verdict,
                "digest_rehash_clean": True,
                "verdict": "PASS",
            }
        except (pa.ConsumptionRefused, CADSError, OSError) as exc:
            row = {"verdict": "FAIL", "error": repr(exc)[:400]}
        s3_rows[entry] = row
    s3 = {"entries": s3_rows,
          "expected_count": len(pa.S3_ENTRY_NAMES),
          "verdict": ("PASS" if len(s3_rows) == len(pa.S3_ENTRY_NAMES)
                      and all(r["verdict"] == "PASS" for r in s3_rows.values())
                      else "FAIL")}
    if s3["verdict"] != "PASS":
        blockers.append("S3 re-pin failed (resolve/verify/refusal)")
    s2_files_ok = (s2.get("files") or {})

    # ---------------- 3. vintaged GB/CA channel proof ------------------ #
    vintaged: dict[str, dict] = {}
    coverage: dict[str, dict] = {}
    tails: dict[str, dict] = {}
    official_tables: dict = {}
    vintage_verdict = "FAIL"
    us_rows: list = []

    def leg_rows(rel_file: str) -> list:
        with open(os.path.join(
                V9_ROOT, "data_raw/forex_free_v9_cpi", rel_file),
                "rb") as fh:
            payload = json.load(fh)
        return pa.parse_fred_vintaged(payload["observations"])

    try:
        for eco, (series, rel) in FRED_LEGS.items():
            rows = leg_rows(rel)
            proof = pa.vintage_structure_proof(rows)
            coverage[eco] = pa.first_appearance(rows)
            latest = pa.latest_vintage_by_month(rows)
            last_month = max(latest)
            tails[eco] = {
                "series": series,
                "last_obs_month": last_month,
                "last_month_first_realtime": coverage[eco][last_month][0],
                "feed_freeze_realtime_end": max(
                    r.realtime_end for r in rows),
            }
            vintaged[eco] = {
                "pit_channel": f"fred_vintaged {series} "
                               f"(S2 manifest file {rel}, sha256 "
                               f"{s2_files_ok.get(series, {}).get('pinned_sha256')})",
                "structure": proof,
                "verdict": ("VINTAGED_PROVEN"
                            if proof["every_value_vintaged"]
                            and proof["distinct_vintages"] >= 2
                            else "NOT_VINTAGED"),
            }
        # US realtime pattern (structure + tail)
        with open(cads_object_path(
                s3_rows[US_RT_CADS_ENTRY]["resolved_address"]),
                "rb") as fh:
            us_payload = json.loads(fh.read().decode("utf-8"))
        us_rows = pa.parse_fred_vintaged(us_payload)
        us_proof = pa.vintage_structure_proof(us_rows)
        coverage["US"] = pa.first_appearance(us_rows)
        us_latest = pa.latest_vintage_by_month(us_rows)
        us_last = max(us_latest)
        tails["US"] = {
            "series": "CPIAUCSL",
            "last_obs_month": us_last,
            "last_month_first_realtime": coverage["US"][us_last][0],
            "feed_freeze_realtime_end": max(
                r.realtime_end for r in us_rows),
        }
        vintaged["US"] = {
            "pit_channel": "CADS US/fred_cpiaucsl_rt.json realtime "
                           "archive (address "
                           + s3_rows[US_RT_CADS_ENTRY]["resolved_address"] + ")",
            "structure": us_proof,
            "verdict": ("VINTAGED_PROVEN" if us_proof["every_value_vintaged"]
                        and us_proof["distinct_vintages"] >= 2
                        else "NOT_VINTAGED"),
        }
        # official continuation tables read structurally (NOT the PIT channel)
        with open(cads_object_path(
                s3_rows["GB/ons_d7bt_cpi_allitems.csv"]["resolved_address"]),
                "rb") as fh:
            ons = pa.parse_ons_d7bt(fh.read().decode("utf-8"))
        with open(cads_object_path(
                s3_rows["CA/statcan_18100004.zip"]["resolved_address"]),
                "rb") as fh:
            statcan = pa.parse_statcan_zip(fh.read())
        official_tables = {
            "GB_ons_d7bt": ons,
            "CA_statcan_18100004": statcan,
            "law": "V9 HIGH finding binding: current-vintage tables are "
                   "continuation/tail coverage only; GB/CA PIT legs come "
                   "from the vintaged archives above; no current-vintage "
                   "backfill anywhere in this cycle",
        }
        vintage_verdict = ("PASS"
                           if vintaged["GB"]["verdict"] == "VINTAGED_PROVEN"
                           and vintaged["CA"]["verdict"] == "VINTAGED_PROVEN"
                           else "FAIL")
        if vintaged["GB"]["verdict"] != "VINTAGED_PROVEN":
            blockers.append("GB leg vintage-ness NOT proven -> GB BLOCKED "
                            "this cycle (no current-vintage backfill)")
        if vintaged["CA"]["verdict"] != "VINTAGED_PROVEN":
            blockers.append("CA leg vintage-ness NOT proven -> CA BLOCKED "
                            "this cycle (no current-vintage backfill)")
        if (vintaged["GB"]["verdict"] != "VINTAGED_PROVEN"
                and vintaged["CA"]["verdict"] != "VINTAGED_PROVEN"):
            blockers.append("STOP CONDITION: vintage-ness unproven for BOTH "
                            "GB and CA (dispatch stop rule)")
    except (pa.VintageStructureError, OSError, ValueError, KeyError) as exc:
        official_tables = official_tables or {}
        vintage_verdict = "FAIL"
        blockers.append(f"vintaged channel proof error: {exc!r}"[:300])
    vintage_section = {
        "method": "structural read (per-value realtime windows) + "
                  "available-time evidence (each value carries its "
                  "[realtime_start, realtime_end] vintage interval) + "
                  "official-table contrast read (single release header / "
                  "Archive Status CURRENT)",
        "legs": vintaged,
        "official_continuation_tables": official_tables,
        "verdict": vintage_verdict,
    }

    # ---------------- 4. shadow parity pilot --------------------------- #
    parity_rows = {}
    v9_staging = {
        "GB/ons_d7bt_cpi_allitems.csv":
            f"{V9_ROOT}/data_raw/forex_free_v9_cpi/GB/ons_d7bt_cpi_allitems.csv",
        "CA/canada_allitems_nsa_2002_100_monthly.csv":
            f"{V9_ROOT}/data_raw/forex_free_v9_cpi/CA/canada_allitems_nsa_2002_100_monthly.csv",
        "CA/statcan_18100004.zip":
            f"{V9_ROOT}/data_raw/forex_free_v9_cpi/CA/statcan_18100004.zip",
        "AU/abs_640101_jul2026.xlsx":
            f"{V9_ROOT}/data_raw/forex_free_v9_cpi/AU/abs_640101_jul2026.xlsx",
        "US/fred_cpiaucsl_rt.json":
            f"{V9_ROOT}/data_raw/forex_free_v9_cpi/US/fred_cpiaucsl_rt.json",
    }
    for entry, staging_path in v9_staging.items():
        row = dict(s3_rows.get(entry, {}))
        if row.get("verdict") == "PASS":
            plane_digest = row["resolved_address"]   # address == digest
            try:
                staging_digest = sha256_file(staging_path)
                row["v9_staging_sha256"] = staging_digest
                row["digest_equal"] = plane_digest == staging_digest
                row["method"] = "full-file sha256 equality (no sampling " \
                                "fallback needed; largest file 15.3MB)"
                if entry == "CA/canada_allitems_nsa_2002_100_monthly.csv":
                    with open(os.path.join(
                            SCRATCH,
                            "CA_canada_allitems_nsa_2002_100_monthly.csv"),
                            "r") as fh:
                        plane_rows = pa.parse_ca_tidy(fh.read())
                    with open(staging_path, "r") as fh:
                        staging_rows = pa.parse_ca_tidy(fh.read())
                    w0, w1 = V9_S0_WINDOW
                    win = lambda m: f"{w0[:7]}-01" <= f"{m}-28" <= f"{w1[:7]}-28"
                    pw = [r for r in plane_rows if win(r[0])]
                    sw = [r for r in staging_rows if win(r[0])]
                    row["window_overlap_parity"] = {
                        "window": f"{w0[:7]}..{w1[:7]}",
                        "plane_rows_in_window": len(pw),
                        "staging_rows_in_window": len(sw),
                        "rows_equal": pw == sw,
                    }
                    row["digest_equal"] = row["digest_equal"] and pw == sw
            except OSError as exc:
                row["digest_equal"] = False
                row["error"] = repr(exc)[:200]
        else:
            row["digest_equal"] = False
        parity_rows[entry] = row
    parity = {
        "plane_source": "consume_via_plane CADS resolve verify-on-read",
        "staging_source": "V9 worktree data_raw/forex_free_v9_cpi "
                          "(paths per p0_census_v9.json staging policy)",
        "s2_manifest_pin_parity": {
            eco: s2_files_ok.get(series, {}).get("match")
            for eco, (series, _) in FRED_LEGS.items()},
        "entries": parity_rows,
        "verdict": ("PASS" if all(
            r.get("digest_equal") for r in parity_rows.values())
            and all(s2_files_ok.get(series, {}).get("match") is True
                    for series, _ in FRED_LEGS.values()) else "FAIL"),
    }
    if parity["verdict"] != "PASS":
        blockers.append("shadow parity digest mismatch (plane vs V9 staging)")

    # ---------------- 5. tail trim + S0 window ------------------------- #
    census_error: str | None = None
    cal_digests: dict[str, str] = {}
    instants: list[dict] = []
    try:
        for eco in ("GB", "CA", "AU", "NZ"):
            cal, digest = pa.load_calendar(eco, V9_ROOT)
            cal_digests[eco] = digest
            builder = {"GB": pa.gb_instants, "CA": pa.ca_instants,
                       "AU": pa.au_instants, "NZ": pa.nz_instants}[eco]
            instants.extend(builder(cal))
        instants.extend(pa.us_instants(us_rows))
    except (pa.ConsumptionRefused, OSError, ValueError) as exc:
        census_error = repr(exc)[:400]
        blockers.append(f"calendar load/parse error: {census_error}")

    # S0_END = last calendar-evidenced FIRST-release publication whose
    # reference period is vintaged-covered, across the non-US economies
    # (binding tail; correction releases of the same month do not move
    # the window boundary).
    pub_by_period: dict[tuple[str, str], str] = {}
    for inst in instants:
        eco, ref = inst["economy"], inst["reference_period"]
        if eco == "US":
            continue
        if coverage.get(eco, {}).get(f"{ref}-01") is None:
            continue
        key = (eco, ref)
        cur = pub_by_period.get(key)
        if cur is None or inst["publication_date"] < cur:
            pub_by_period[key] = inst["publication_date"]
    non_us_last: dict[str, str] = {}
    for (eco, _ref), pub in pub_by_period.items():
        cur = non_us_last.get(eco)
        if cur is None or pub > cur:
            non_us_last[eco] = pub
    s0_end = max(non_us_last.values()) if non_us_last else V9_S0_WINDOW[1]

    def _effective_end_month(eco: str, last_obs_month: str) -> str:
        """Quarterly feeds (AU/NZ) are represented at the quarter FIRST
        month (V9 law); their reference period ends two months later.
        The tail-trim law speaks of real coverage end, so quarterly
        legs are measured at quarter end."""
        y, m = int(last_obs_month[:4]), int(last_obs_month[5:7])
        if eco in ("AU", "NZ"):
            m += 2
            if m > 12:
                m -= 12
                y += 1
        return f"{y:04d}-{m:02d}"

    tail_effective = {
        e: _effective_end_month(e, t["last_obs_month"])
        for e, t in tails.items()}
    tail_trim = {
        "vintaged_feed_tails": tails,
        "effective_coverage_end_month": tail_effective,
        "expectation": "vintaged feeds end ~2025-03..2025-06 (V8 tail-trim "
                       "law, measured as the effective coverage end "
                       "month: quarterly AU/NZ legs at quarter end); no "
                       "current-vintage backfill, ever",
        "non_us_last_covered_publication": non_us_last,
        "s0_window_used": {"start": NG1_S0_START, "end": s0_end,
                           "start_basis": "V9 S0 window start inherited",
                           "end_basis": "last calendar-evidenced print "
                                        "publication with a vintaged "
                                        "realized value on the non-US legs"},
        "verdict": ("PASS" if tails and all(
            "2025-03" <= em <= "2025-06"
            for em in tail_effective.values()) else "FAIL"),
    }
    if tail_trim["verdict"] != "PASS":
        blockers.append("vintaged tail outside the 2025-03..2025-06 law")

    # ---------------- 6. announcement census + canary ------------------ #
    census = pa.build_census(instants, coverage, NG1_S0_START, s0_end)
    canary_specs = [
        {"economy": "GB", "publication_date": "2019-03-09",
         "basis": "fabricated: no ONS bulletin released that day"},
        {"economy": "AU", "publication_date": "2021-02-14",
         "basis": "fabricated: ABS CPI is quarterly; no such release"},
    ]
    canary = []
    for spec in canary_specs:
        res = pa.census_lookup_instant(census, spec["economy"],
                                       spec["publication_date"])
        res["expected"] = "FAIL"
        res["verdict"] = "PASS" if not res["found"] else "FAIL"
        res["basis"] = spec["basis"]
        canary.append(res)
    emu_path = os.path.join(V9_ROOT, pa.EMU_LEDGER_PIN["path"])
    emu = {
        "path": pa.EMU_LEDGER_PIN["path"],
        "sha256": sha256_file(emu_path),
        "rows": sum(1 for _ in open(emu_path, "rb")),
        "note": pa.EMU_LEDGER_PIN["pin_basis"] + "; read-only evidence "
                "lineage for the S3 announcement-ledger series (EMU "
                "rate-decision rows are not CPI print instants and are "
                "not in the GB/CA/AU/NZ/US census scope)",
    }
    census_artifact = {
        "schema": "forex_ng1_run/p0_announcement_census@1",
        "measured_utc": now_utc(),
        "cycle_id": "FOREX-NG1",
        "method": {
            "instant_sources": {
                "GB": "pinned ONS bulletin calendar (v5 pin aad19697); "
                      "date-only evidence -> conservative end-of-day UTC",
                "CA": "pinned StatCan WDS calendar v3 (pin 0f1a9328); "
                      "true-UTC timestamps evidenced per row "
                      "(tz_conversion archived); ref month = release "
                      "month - 1 (StatCan monthly convention, validated "
                      "by non-negative realtime lags below)",
                "AU": "pinned ABS release calendar (v5 pin 42a4e4a3); "
                      "date-only -> conservative end-of-day UTC; "
                      "quarter-first-month representation (V9 law)",
                "NZ": "pinned Stats NZ calendar (v5 pin 62f82c23); 10:45 "
                      "Pacific/Auckland local -> DST-correct UTC",
                "US": "pinned FRED realtime archive first-appearances "
                      "(CADS US/fred_cpiaucsl_rt.json); date-only -> "
                      "conservative end-of-day UTC",
            },
            "inclusion_rule": "publication date within the measured S0 "
                              "window AND the reference period carries a "
                              "vintaged realized value (first-appearance "
                              "realtime exists); per instant the census "
                              "records publication evidence, archive "
                              "first-realtime, the conservative "
                              "operative availability max(publication, "
                              "first_realtime), and release ordinals "
                              "(CA WDS correction releases of the same "
                              "month are listed but flagged)",
            "dst_rule": "zoneinfo local->UTC conversion; date-only "
                        "evidence gets a conservative 23:59:59Z bound "
                        "(a 16:00-NY same-day decision cannot see it)",
        },
        "calendar_sha256": cal_digests,
        "calendar_pin_basis": {e: pa.CALENDAR_PINS[e]["pin_basis"]
                               for e in pa.CALENDAR_PINS},
        "announcement_ledger_emu_v2": emu,
        "s0_window": tail_trim["s0_window_used"],
        "coverage_tails": tails,
        "coverage_tails_effective_end_month": tail_effective,
        "counts_by_economy": census["counts_by_economy"],
        "first_release_counts_by_economy": census[
            "first_release_counts_by_economy"],
        "total_instants": census["total_instants"],
        "instants": census["instants"],
        "excluded_count": len(census["excluded"]),
        "exclusion_reasons_summary": _exclusion_summary(census["excluded"]),
        "pit_anomaly_count": sum(
            1 for i in census["instants"] if i.get("pit_notes")),
        "canary": canary,
        "census_error": census_error,
        "known_gaps": [
            "AU calendar evidence starts 2019-10-30 (V9: ABS past-release "
            "pulls network-failed); pre-2019-10 AU prints have no "
            "publication-timestamp evidence and are NOT counted",
            "US instants carry date-only evidence (FRED realtime bytes "
            "have no time-of-day): conservative end-of-day bound",
            "CA WDS calendars list correction releases of the same "
            "reference month; all are listed with "
            "release_ordinal_in_reference_period and "
            "is_first_release_of_period flags -- the PRINT instant is "
            "ordinal 1",
        ],
    }
    census_verdict = ("PASS" if census_error is None
                      and census["total_instants"] > 0
                      and all(c["verdict"] == "PASS" for c in canary)
                      and all(census["counts_by_economy"].get(e, 0) > 0
                              for e in ("GB", "CA", "AU", "NZ", "US"))
                      else "FAIL")
    if census_verdict != "PASS":
        blockers.append("announcement census failed (coverage or canary)")

    # ---------------- tests row ---------------------------------------- #
    test_cmd = (f"cd {WORKTREE} && "
                "/Users/hoangminhlong/my-quantitative/.venv/bin/python "
                "-m pytest tests/test_forex_ng1_p0.py -q")
    tests_row = {"command": test_cmd, "verdict": "NOT_RUN"}
    if args.pytest_exit is not None:
        tests_row["exit_code"] = args.pytest_exit
        tests_row["verdict"] = "PASS" if args.pytest_exit == 0 else "FAIL"
        if args.pytest_log and os.path.exists(args.pytest_log):
            tests_row["output_tail"] = open(args.pytest_log).read()[-800:]
    commands.append(tests_row)

    # ---------------- gate --------------------------------------------- #
    os.makedirs(OUT_DIR, exist_ok=True)
    census_path = os.path.join(OUT_DIR, "p0_announcement_census.json")
    with open(census_path, "w") as fh:
        json.dump(census_artifact, fh, indent=1, sort_keys=False)

    verdict = "PASS" if not blockers else "BLOCKED_DATA"
    gate = {
        "schema": "forex_ng1_run/p0_gate@1",
        "gate": "FOREX-NG1-P0",
        "cycle_id": "FOREX-NG1",
        "task_id": "forex-ng1-p0-adoption",
        "measured_utc": now_utc(),
        "git": gs,
        "dispatch_base_sha": "f165cac5622c424ae3150e1373eeb7942b29979d",
        "base_match": gs["head_sha"] == "f165cac5622c424ae3150e1373eeb7942b29979d",
        "series_granted_check": granted_check,
        "s2_repin": s2,
        "s3_repin": s3,
        "vintaged_channel_proof": vintage_section,
        "shadow_parity": parity,
        "tail_trim": tail_trim,
        "announcement_census": {
            "artifact": "research/control/forex_ng1_run/"
                        "p0_announcement_census.json",
            "sha256": sha256_file(census_path),
            "counts_by_economy": census["counts_by_economy"],
            "first_release_counts_by_economy": census[
                "first_release_counts_by_economy"],
            "total_instants": census["total_instants"],
            "canary": canary,
            "verdict": census_verdict,
        },
        "commands": commands,
        "evidence_paths": {
            "cads_store_root": CADS_ROOT,
            "v9_read_only_root": V9_ROOT,
            "adapter": "research/assets/forex_ng1/plane_adapter.py",
            "tests": "tests/test_forex_ng1_p0.py",
        },
        "blockers": blockers,
        "verdict": verdict,
    }
    gate_path = os.path.join(OUT_DIR, "p0_gate.json")
    with open(gate_path, "w") as fh:
        json.dump(gate, fh, indent=1, sort_keys=False)

    print(json.dumps({
        "gate": gate["verdict"],
        "blockers": blockers,
        "s2": s2["verdict"], "s3": s3["verdict"],
        "vintaged": vintage_section["verdict"],
        "parity": parity["verdict"], "tail": tail_trim["verdict"],
        "census": census_verdict,
        "counts": census["counts_by_economy"],
        "s0_window": tail_trim["s0_window_used"],
    }, indent=1))
    return 0


def _exclusion_summary(excluded: list[dict]) -> dict:
    summary: dict[str, int] = {}
    for rec in excluded:
        for reason in rec.get("exclusion_reasons", []):
            summary[reason] = summary.get(reason, 0) + 1
    return summary


if __name__ == "__main__":
    raise SystemExit(main())
