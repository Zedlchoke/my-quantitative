#!/usr/bin/env python
"""FOREX-NG2 P0 runner: inherited pin re-verification + revision-event census.

Measures, fail-closed, the FOREX-NG2 plan section 5 P0 deliverables:

1. INHERITED PIN RE-VERIFICATION (verify-on-read, machinery inherited
   VERBATIM from research/assets/forex_ng1 -- no edits):
   - S2 CADS address 07d1e0d5... resolves clean (address == re-hash) and
     its 5-file vintaged manifest verifies against live bytes (US leg via
     its CADS object; GB/CA/AU/NZ legs via the V9 staging bytes pinned by
     the manifest digests);
   - S3 pinned ledger entries (all five) resolve through
     consume_via_plane (GRANTED -> CADS resolve verify-on-read ->
     manifest-verified query);
   - spot 4 pairs: verify-on-read against the committed spot_pin_manifest
     sha256s + the 16:00-NY common weekday grid recomputed from the
     pinned bytes (1842-day law);
   - scored-consumption authority gate: require_scored_authority() reads
     the COMMITTED authority proof and returns AUTHORIZED (P-18: the
     gate reader bytes are law; this lane proves the read, it never
     re-promotes);
   - DGS10 ctl pin chain (P-13): V8 run-contract data_pins pin the staged
     vintaged manifest by digest (witnesses re-hashed) -> manifest pins
     DGS10.json by sha256 -> source bytes == ng1 worktree copy == manifest;
   - ng1 announcement census artifact: sha256 must equal the inherited
     pin e8a35d23ce64ce71a8d30792750b877c387de3692af1e4d17391ea4cc35b4abe.

2. REVISION-EVENT CENSUS (the NG2 frontier, new module
   research/assets/forex_ng2/revision_series.py): first-to-second-vintage
   revision events per economy on the vintaged CPI channel (GB/CA MINMEI
   realtime; AU/NZ quarterly vintaged; US fred realtime), with strict
   vintage monotonicity, full availability windows, S0-window usability,
   cross-economy differential months, by-year distribution, Q-6
   recent-window (24 months) count, and descriptive magnitude
   distribution.  NO PnL, NO outcome, NO scoring.

3. CANARIES (P-7): fabricated months must FAIL lookup; measured
   monotonicity violations must be zero on every leg (the planted
   violation is exercised fail-closed in tests/test_forex_ng2_p0.py).

4. FLOORS (frozen): >=30 usable own-economy revision events per
   pair-anchor economy (GB/CA/AU/NZ), >=12 cross-economy differential
   months.  Floor not met -> verdict BLOCKED_DATA (honest terminal per
   plan section 2: "BLOCKED_DATA is live and cheap").

Publishes p0_revision_census.json and p0_gate.json under
research/control/forex_ng2_run/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1 import plane_adapter as pa          # noqa: E402
from research.assets.forex_ng1 import spot_series as ss            # noqa: E402
from research.assets.forex_ng2 import revision_series as rs        # noqa: E402
from research.platform_v3.cads import CADSError                    # noqa: E402

WORKTREE = REPO_ROOT
CADS_ROOT = pa.DEFAULT_CADS_STORE_ROOT                  # READ-ONLY store
V9_ROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
           "forex-free-v9/integration")                  # READ-ONLY evidence
OUT_DIR = os.path.join(WORKTREE, "research/control/forex_ng2_run")
SCRATCH = "/tmp/forex_ng2_p0_scratch"

DISPATCH_BASE_SHA = "c5e52bbfedfcd3b2f9d99f3c1466290283b45902"

#: Inherited pin constants (FOREX-NG1 committed artifacts; this lane
#: re-verifies, never edits).
NG1_CENSUS_PIN_SHA256 = (
    "e8a35d23ce64ce71a8d30792750b877c387de3692af1e4d17391ea4cc35b4abe")
NG1_CENSUS_PATH = os.path.join(
    REPO_ROOT, "research/control/forex_ng1_run/p0_announcement_census.json")
SPOT_PIN_MANIFEST = os.path.join(
    REPO_ROOT, "research/control/forex_ng1_run/p1_spot/spot_pin_manifest.json")
SPOT_AUTHORITY_PROOF = os.path.join(
    REPO_ROOT,
    "research/control/forex_ng1_run/p1_spot/spot_authority_proof.json")
GRID_LAW_DAYS = 1842
GRID_WINDOW = (date(2018, 4, 4), date(2025, 4, 30))

DGS10_PIN = {
    "v8_run_contract_witnesses": [
        "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v9/"
        "integration/research/control/forex_free_v8_run/run_contract.json",
        "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v9/"
        "i-family/research/control/forex_free_v8_run/run_contract.json",
    ],
    "staged_manifest_sha256": (
        "c8ae78777102ab45cec433f5da6c786355b57c884be5f15c39c1fc18ca328e7c"),
    "staged_manifest_witnesses": [
        "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v9/"
        "integration/research/control/forex_free_v8_run/"
        "staged_vintaged_manifest.json",
        "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v9/"
        "i-family/research/control/forex_free_v8_run/"
        "staged_vintaged_manifest.json",
    ],
    "dgs10_sha256": (
        "03dde429ba022e6d011ae3a61323124e38c5a3fac888b492823406a51c4c4aa0"),
    "source_path": (
        "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v8/"
        "integration/research/control/forex_free_v8_run/staged_vintaged/"
        "DGS10.json"),
    "ng1_copy_path": (
        "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng1/"
        "integration/.worktrees/forex-ng1/i-runners/data_raw/"
        "forex_ng1_ctl/DGS10.json"),
}

FRED_LEGS = {
    "GB": ("GBRCPIALLMINMEI", "fred_vintaged/GBRCPIALLMINMEI.json"),
    "CA": ("CANCPIALLMINMEI", "fred_vintaged/CANCPIALLMINMEI.json"),
    "AU": ("AUSCPIALLQINMEI", "fred_vintaged/AUSCPIALLQINMEI.json"),
    "NZ": ("NZLCPIALLQINMEI", "fred_vintaged/NZLCPIALLQINMEI.json"),
}
US_RT_CADS_ENTRY = "US/fred_cpiaucsl_rt.json"
US_RT_CADS_ADDRESS = (
    "7f18ec982374ce4dfb235f53f001327793df8e1c0077d31206de25aa3455ac94")


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


def cads_object_path(address: str) -> str:
    return os.path.join(CADS_ROOT, "objects", address[:2], address)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pytest-exit", type=int, default=None,
                    help="exit code of the mandated pytest command")
    ap.add_argument("--pytest-log", default=None,
                    help="path holding the pytest tail (evidence)")
    args = ap.parse_args()

    blockers: list[str] = []
    commands: list[dict] = []

    gs = git_state()

    # ================= 1. INHERITED PIN RE-VERIFICATION ================ #
    pin_section: dict = {}

    # 1a. authority registry verdicts (GRANTED-gated consumption)
    registry = pa.load_registry()
    ga4 = pa.ga4_granted()
    granted_check = {
        "journal": pa.DEFAULT_AUTHORITY_JOURNAL,
        "ga4_gate": pa.DEFAULT_GA4_GATE,
        "verdicts": {s: registry.verdict(s) for s in (
            "S2:fred-keyed-vintage-classes",
            "S3:forex-print-calendars",
            "S3:forex-announcement-ledger")},
        "ga4_granted_count": len(ga4),
        "verdict": "PASS" if all(
            registry.verdict(s) == "GRANTED" for s in (
                "S2:fred-keyed-vintage-classes",
                "S3:forex-print-calendars",
                "S3:forex-announcement-ledger")) else "FAIL",
    }
    if granted_check["verdict"] != "PASS":
        blockers.append("authority registry/GA4 granted check failed")
    pin_section["granted_check"] = granted_check

    # 1b. S2 re-pin (CADS resolve verify-on-read + 5-file digest verify)
    try:
        s2_manifest = pa.consume_s2_manifest(CADS_ROOT, registry, ga4)
        s2_files = pa.verify_s2_files(s2_manifest, {
            "US/fred_cpiaucsl_rt.json":
                cads_object_path(US_RT_CADS_ADDRESS),
            **{rel: os.path.join(
                V9_ROOT, "data_raw/forex_free_v9_cpi", rel)
               for _, rel in FRED_LEGS.values()},
        })
        pin_section["s2_repin"] = {
            "cads_address": pa.S2_PINNED_ADDRESS,
            "resolve_law": "CADS resolve verify-on-read: address == "
                           "re-hash of the object bytes (fail-closed)",
            "files": s2_files,
            "file_count": len(s2_manifest["series"]),
            "verdict": ("PASS" if len(s2_manifest["series"]) == 5
                        and all(f["match"] for f in s2_files.values())
                        else "FAIL"),
        }
    except (CADSError, pa.ConsumptionRefused, pa.VintageStructureError,
            OSError) as exc:
        pin_section["s2_repin"] = {"cads_address": pa.S2_PINNED_ADDRESS,
                                   "verdict": "FAIL",
                                   "error": repr(exc)[:400]}
    if pin_section["s2_repin"].get("verdict") != "PASS":
        blockers.append("S2 re-pin failed (digest/manifest mismatch)")

    # 1c. S3 re-pin via consume_via_plane (all five pinned entries)
    s3_rows = {}
    for entry in pa.S3_ENTRY_NAMES:
        try:
            consumed = pa.consume_via_plane(
                registry, CADS_ROOT, "S3:forex-announcement-ledger",
                entry, SCRATCH, ga4=ga4)
            s3_rows[entry] = {
                "resolved_address": consumed.resolved_address,
                "bytes": consumed.nbytes,
                "query_verdict": consumed.query_verdict,
                "digest_rehash_clean": True,
                "verdict": "PASS",
            }
        except (pa.ConsumptionRefused, CADSError, OSError) as exc:
            s3_rows[entry] = {"verdict": "FAIL", "error": repr(exc)[:400]}
    pin_section["s3_repin"] = {
        "entries": s3_rows,
        "expected_count": len(pa.S3_ENTRY_NAMES),
        "note": "dispatch said '07d1e0d5 + 3 archive legs'; the pinned S3 "
                "ledger carries FIVE entries and ALL FIVE are re-verified "
                "(superset, nothing skipped)",
        "verdict": ("PASS" if len(s3_rows) == len(pa.S3_ENTRY_NAMES)
                    and all(r["verdict"] == "PASS"
                            for r in s3_rows.values()) else "FAIL"),
    }
    if pin_section["s3_repin"]["verdict"] != "PASS":
        blockers.append("S3 re-pin failed (resolve/verify/refusal)")

    # 1d. spot 4 pairs: verify-on-read + grid 1842 recompute
    spot_section: dict = {"pairs": {}}
    try:
        manifest = ss.load_pin_manifest(SPOT_PIN_MANIFEST)
        # The pinned raw bytes live UNTRACKED in the ng1 pin lane's
        # copy dir (raw_bytes_policy: UNTRACKED_NEVER_COMMITTED; only the
        # manifest commits).  data_dir is derived from the manifest's own
        # copy_path_absolute entries; file NAMES and sha256s always come
        # from the manifest (verify-on-read law).
        copy_dirs = sorted({
            os.path.dirname(e["copy_path_absolute"])
            for e in manifest["files"].values()})
        if len(copy_dirs) != 1:
            raise ss.SpotIntegrityError(
                f"manifest copy_path_absolute entries disagree on the "
                f"pinned data dir: {copy_dirs}")
        pinned_data_dir = copy_dirs[0]
        spot_section["pinned_data_dir"] = pinned_data_dir
        spot_section["pinned_data_dir_law"] = (
            "derived from the committed manifest copy_path_absolute "
            "entries (untracked pinned bytes; sha256 always from the "
            "manifest, verify-on-read)")
        serieses = {}
        for pair in ss.FUNDED_PAIRS:
            sha = ss.verify_spot_file(manifest, pair, data_dir=pinned_data_dir)
            series = ss.resolve_spot_series(pair, SPOT_PIN_MANIFEST,
                                            data_dir=pinned_data_dir)
            serieses[pair] = series
            spot_section["pairs"][pair] = {
                "pinned_sha256": sha,
                "bars": series.bars,
                "first_day": series.first_day.isoformat(),
                "last_day": series.last_day.isoformat(),
                "verdict": "PASS",
            }
        grid = ss.common_weekday_grid(
            serieses, GRID_WINDOW[0], GRID_WINDOW[1])
        binding = min(
            (len(s.window_days(GRID_WINDOW[0], GRID_WINDOW[1]))
             for s in serieses.values()), default=0)
        spot_section["grid_recompute"] = {
            "window": [GRID_WINDOW[0].isoformat(),
                       GRID_WINDOW[1].isoformat()],
            "common_weekday_grid_days": len(grid),
            "binding_pair_days": binding,
            "first_day": grid[0].isoformat() if grid else None,
            "last_day": grid[-1].isoformat() if grid else None,
            "law": "FX 24/5 weekdays in window intersected across the four "
                   "funded-pair calendars (V9 build_grid law, inherited)",
        }
        spot_section["verdict"] = (
            "PASS" if all(p["verdict"] == "PASS"
                          for p in spot_section["pairs"].values())
            and len(grid) == GRID_LAW_DAYS else "FAIL")
    except (ss.SpotDataError, OSError, ValueError) as exc:
        spot_section["verdict"] = "FAIL"
        spot_section["error"] = repr(exc)[:400]
    pin_section["spot_repin"] = spot_section
    if spot_section.get("verdict") != "PASS":
        blockers.append("spot re-pin failed (digest or 1842-day grid law)")

    # 1e. scored-authority gate read (P-18: the committed artifact is law)
    try:
        block = ss.require_scored_authority(SPOT_AUTHORITY_PROOF)
        pin_section["scored_authority_read"] = {
            "proof_path": "research/control/forex_ng1_run/p1_spot/"
                          "spot_authority_proof.json (committed artifact)",
            "status": block.get("status"),
            "scored_consumption": block.get("scored_consumption"),
            "law": "P-18: require_scored_authority() reads the committed "
                   "authority proof and returns AUTHORIZED; this lane "
                   "proves the read (no self-promotion, no edit)",
            "verdict": ("PASS"
                        if block.get("scored_consumption") == "AUTHORIZED"
                        else "FAIL"),
        }
    except (ss.SpotDataError, OSError) as exc:
        pin_section["scored_authority_read"] = {
            "verdict": "FAIL", "error": repr(exc)[:400]}
    if pin_section["scored_authority_read"].get("verdict") != "PASS":
        blockers.append("scored-authority gate did not read AUTHORIZED")

    # 1f. DGS10 ctl pin chain (P-13)
    try:
        chain: dict = {"witnesses": {}}
        contract_pins = set()
        for wit in DGS10_PIN["v8_run_contract_witnesses"]:
            rc = json.load(open(wit, "r", encoding="utf-8"))
            pin = rc["data_pins"]["staged_vintaged_manifest_sha256"]
            contract_pins.add(pin)
            chain["witnesses"][wit] = pin
        chain["run_contract_pin_unique"] = len(contract_pins) == 1
        chain["run_contract_pin"] = (list(contract_pins)[0]
                                     if len(contract_pins) == 1 else None)
        chain["staged_manifest_rehash"] = {}
        for wit in DGS10_PIN["staged_manifest_witnesses"]:
            chain["staged_manifest_rehash"][wit] = sha256_file(wit)
        manifest_entry = None
        for wit in DGS10_PIN["staged_manifest_witnesses"]:
            sm = json.load(open(wit, "r", encoding="utf-8"))
            entry = sm["series"]["DGS10"]
            if manifest_entry is None:
                manifest_entry = entry
            elif manifest_entry["sha256"] != entry["sha256"]:
                manifest_entry = None   # witness disagreement -> fail
                break
        chain["manifest_dgs10_entry"] = manifest_entry
        chain["source_sha256"] = sha256_file(DGS10_PIN["source_path"])
        chain["ng1_copy_sha256"] = sha256_file(DGS10_PIN["ng1_copy_path"])
        ok = (
            chain["run_contract_pin_unique"]
            and chain["run_contract_pin"] == DGS10_PIN["staged_manifest_sha256"]
            and all(v == DGS10_PIN["staged_manifest_sha256"]
                    for v in chain["staged_manifest_rehash"].values())
            and manifest_entry is not None
            and manifest_entry["sha256"] == DGS10_PIN["dgs10_sha256"]
            and chain["source_sha256"] == DGS10_PIN["dgs10_sha256"]
            and chain["ng1_copy_sha256"] == DGS10_PIN["dgs10_sha256"])
        chain["verdict"] = "PASS" if ok else "FAIL"
        chain["pin_law"] = ("P-13 inherited pin: V8 run-contract data_pins "
                            "pin the staged_vintaged MANIFEST by digest; the "
                            "manifest pins DGS10.json by sha256; source "
                            "bytes == ng1 worktree copy == manifest entry")
        pin_section["dgs10_ctl_pin_chain"] = chain
    except (OSError, KeyError, ValueError) as exc:
        pin_section["dgs10_ctl_pin_chain"] = {
            "verdict": "FAIL", "error": repr(exc)[:400]}
    if pin_section["dgs10_ctl_pin_chain"].get("verdict") != "PASS":
        blockers.append("DGS10 ctl pin chain failed")

    # 1g. ng1 announcement census artifact pin (e8a35d23)
    census_digest = sha256_file(NG1_CENSUS_PATH)
    pin_section["ng1_census_pin"] = {
        "path": "research/control/forex_ng1_run/p0_announcement_census.json",
        "pinned_sha256": NG1_CENSUS_PIN_SHA256,
        "measured_sha256": census_digest,
        "verdict": ("PASS" if census_digest == NG1_CENSUS_PIN_SHA256
                    else "FAIL"),
    }
    if pin_section["ng1_census_pin"]["verdict"] != "PASS":
        blockers.append("ng1 census artifact sha pin mismatch (e8a35d23)")

    # ==================== 2. REVISION-EVENT CENSUS ===================== #
    census: dict = {"legs": {}}
    census_error: str | None = None
    built: dict[str, dict] = {}
    dedupe_log: dict[str, int] = {}
    try:
        for eco, (series_id, rel) in FRED_LEGS.items():
            payload = json.load(open(os.path.join(
                V9_ROOT, "data_raw/forex_free_v9_cpi", rel), "rb"))
            rows = pa.parse_fred_vintaged(payload["observations"])
            rows, removed = rs.dedupe_exact_rows(rows)
            dedupe_log[eco] = removed
            built[eco] = rs.build_revision_events(eco, rows)
            built[eco]["series"] = series_id
            built[eco]["rows"] = len(rows)
            built[eco]["distinct_vintages"] = len(
                {r.realtime_start for r in rows})
        us_payload = json.load(open(
            cads_object_path(US_RT_CADS_ADDRESS), "rb"))
        us_rows = pa.parse_fred_vintaged(us_payload)
        us_rows, removed = rs.dedupe_exact_rows(us_rows)
        dedupe_log["US"] = removed
        built["US"] = rs.build_revision_events("US", us_rows)
        built["US"]["series"] = "CPIAUCSL"
        built["US"]["rows"] = len(us_rows)
        built["US"]["distinct_vintages"] = len(
            {r.realtime_start for r in us_rows})
    except (pa.VintageStructureError, rs.RevisionStructureError,
            OSError, ValueError, KeyError) as exc:
        census_error = repr(exc)[:400]
        blockers.append(f"revision census build error: {census_error}")

    events_all_by_eco: dict[str, list] = {}
    usable_by_eco: dict[str, list] = {}
    recent_lo, recent_hi = rs.recent_window_bounds()
    if census_error is None:
        for eco, res in built.items():
            usable = rs.usable_events(res["events_all"], rs.S0_WINDOW)
            events_all_by_eco[eco] = res["events_all"]
            usable_by_eco[eco] = usable
            recent = [e for e in usable
                      if recent_lo <= e.v2_realtime_start <= recent_hi]
            first_print_all = [e for e in res["events_all"]
                               if e.first_print_in_realtime_era]
            first_print_usable = [e for e in usable
                                  if e.first_print_in_realtime_era]
            census["legs"][eco] = {
                "series": res["series"],
                "cadence": ("monthly MINMEI realtime" if eco in
                            rs.ECONOMIES_MONTHLY else
                            "quarterly vintaged (quarter-first-month "
                            "representation)" if eco in
                            rs.ECONOMIES_QUARTERLY else
                            "US fred realtime archive (measured: small "
                            "index-level vintage updates)"),
                "lag_mapping": rs.QUARTERLY_LAG_MAPPING.get(eco),
                "exact_duplicate_rows_removed": dedupe_log.get(eco, 0),
                "rows": res["rows"],
                "distinct_vintages": res["distinct_vintages"],
                "months_carried": res["months_carried"],
                "months_with_second_vintage":
                    res["months_with_second_vintage"],
                "events_all": res["events_all_count"],
                "events_usable_in_window": len(usable),
                "events_first_print_era_all": len(first_print_all),
                "events_first_print_era_usable": len(first_print_usable),
                "events_backfill_history_usable": (
                    len(usable) - len(first_print_usable)),
                "usable_by_year": rs.events_by_year(usable),
                "usable_recent_24m": {
                    "window": [recent_lo, recent_hi],
                    "count": len(recent),
                },
                "magnitude_pct_all": rs.magnitude_distribution(
                    res["events_all"]),
                "magnitude_pct_usable": rs.magnitude_distribution(usable),
                "sample_events": [
                    {"obs_month": e.obs_month,
                     "v1": [e.v1_realtime_start, e.v1_value],
                     "v2": [e.v2_realtime_start, e.v2_value],
                     "ratio_pct": round(100.0 * e.ratio, 6),
                     "first_print_era": e.first_print_in_realtime_era}
                    for e in usable[:5]],
            }
        census["us_structural_note"] = (
            "US CPIAUCSL realtime archive measured: "
            f"{len(usable_by_eco.get('US', []))} usable first-to-second "
            "vintage events (NOT the structural zero a naive 'BLS never "
            "revises CPI' prior predicts); magnitudes are small "
            "(see magnitude_pct_usable) and v2 days cluster on archive "
            "re-pull dates -- index-level updates in the realtime "
            "archive. US is the quote leg of every funded pair and is "
            "not a pair-anchor economy; measured and disclosed, never "
            "floor-anchored.")
        # bulk re-referencing disclosure: usable events sharing an
        # identical (v1 day, v2 day, ratio) signature are ONE structural
        # transition applied to many months, not independent revision
        # news.  Descriptive only; floors stay on the frozen literal
        # definition, the disclosure shows the origin mix.
        bulk: dict[str, dict] = {}
        for eco, evs in usable_by_eco.items():
            groups: dict[tuple, int] = {}
            for e in evs:
                key = (e.v1_realtime_start, e.v2_realtime_start,
                       round(e.ratio, 6))   # ratio to 1e-6: one bulk
                groups[key] = groups.get(key, 0) + 1   # multiplier groups
            big = {f"{k[0]}->{k[1]} ratio {k[2] * 100:.4f}%": v
                   for k, v in sorted(groups.items(),
                                      key=lambda kv: -kv[1]) if v >= 10}
            bulk[eco] = {
                "usable_events": len(evs),
                "events_in_bulk_groups_ge10": sum(
                    v for v in big.values()) if big else 0,
                "bulk_groups": big,
                "law": "identical (v1 day, v2 day, ratio) across >=10 "
                       "months = one bulk re-referencing transition "
                       "(e.g. a re-referencing multiplier applied to the "
                       "whole history at a single vintage)",
            }
        census["bulk_re_referencing_disclosure"] = bulk
        diff = rs.cross_economy_differential_months(usable_by_eco)
        diff_by_year: dict[str, int] = {}
        for m in diff["sorted_month_keys"]:
            y = m[:4]
            diff_by_year[y] = diff_by_year.get(y, 0) + 1
        census["cross_economy_differential"] = {
            **diff,
            "by_year": dict(sorted(diff_by_year.items())),
            "economies_per_month_sample": {
                m: diff["months"][m] for m in
                diff["sorted_month_keys"][:10]},
        }

    # ========================= 3. CANARIES ============================= #
    canary: list[dict] = []
    if census_error is None:
        # positive control: a month that IS a measured CA event must be
        # found (picked from the built events, never hardcoded)
        positive_month = (events_all_by_eco["CA"][0].obs_month
                          if events_all_by_eco.get("CA") else None)
        canary_specs = [
            {"economy": "GB", "obs_month": "2019-06-01",
             "expect_found": False,
             "basis": "fabricated: June-2019 must not be a GB revision-"
                      "event month in the pinned archives (if it "
                      "coincides with a real event the canary reports "
                      "FAIL and the controller is informed, not patched)"},
            {"economy": "AU", "obs_month": "2030-02-01",
             "expect_found": False,
             "basis": "fabricated: far-future month cannot exist in the "
                      "pinned realtime archives (lookup must FAIL)"},
            {"economy": "CA", "obs_month": positive_month,
             "expect_found": True,
             "basis": "positive control: a measured CA event month "
                      "(taken from the built events) must be found"},
        ]
        for spec in canary_specs:
            res = rs.lookup_event(events_all_by_eco, spec["economy"],
                                  spec["obs_month"])
            res["expected_found"] = spec["expect_found"]
            res["verdict"] = ("PASS"
                              if res["found"] is spec["expect_found"]
                              else "FAIL")
            res["basis"] = spec["basis"]
            canary.append(res)
        # measured monotonicity: vintages_by_month RAISES on violation;
        # reaching here with events built means zero violations. Record
        # explicitly for the gate.
        census["monotonicity_check"] = {
            "law": "v2.realtime > v1.realtime STRICT per month; a single "
                   "violation raises VintageMonotonicityError and NO "
                   "events are built (fail-closed)",
            "exact_duplicate_rows_removed": dedupe_log,
            "dedupe_law": "byte-identical duplicate rows only (same "
                          "obs_date + realtime window + value: ingest "
                          "artifact, zero ambiguity); conflicting "
                          "same-realtime_start rows still raise "
                          "fail-closed (a genuine same-day correction "
                          "makes the month unmeasurable, never guessed)",
            "measured_violations_after_dedupe": 0,
            "verdict": "PASS",
            "note": "planted-violation behavior exercised in "
                    "tests/test_forex_ng2_p0.py",
        }
    canary_ok = all(c["verdict"] == "PASS" for c in canary) and (
        census.get("monotonicity_check", {}).get("verdict") == "PASS")
    if not canary_ok:
        blockers.append("canary failed (fabricated month found or "
                        "monotonicity)")

    # ========================== 4. FLOORS ============================== #
    if census_error is None:
        usable_counts = {e: len(v) for e, v in usable_by_eco.items()}
        floors = rs.evaluate_floors(
            usable_counts, census["cross_economy_differential"]["total"])
        floors["usability_definition"] = (
            "usable = v2 availability day (v2.realtime_start; date-only "
            "evidence, conservative) inside the S0 window "
            f"{rs.S0_WINDOW[0]}..{rs.S0_WINDOW[1]} with full realtime "
            "windows on both vintages; events outside the window are "
            "counted in events_all but never toward a floor")
        floors["backfill_disclosure"] = (
            "events with obs month older than the feed's realtime era are "
            "history-backfill transitions (first 'vintage' is the archive "
            "ingest, not a genuine first print); they are counted per the "
            "frozen literal definition and split out in "
            "events_first_print_era_* columns so D1/D2 lanes see the "
            "origin mix")
    else:
        floors = {"verdict": "FAIL", "error": census_error}
    if floors.get("verdict") != "PASS":
        for eco, row in (floors.get("own_economy") or {}).items():
            if row["verdict"] != "PASS":
                blockers.append(
                    f"own-economy floor NOT met for {eco}: "
                    f"{row['usable_events']} < {row['floor']} "
                    f"(margin {row['margin']})")
        cross = floors.get("cross_economy") or {}
        if cross.get("verdict") != "PASS":
            blockers.append(
                "cross-economy differential floor NOT met: "
                f"{cross.get('differential_months')} < "
                f"{cross.get('floor')}")

    # ======================== tests row ================================= #
    test_cmd = (f"cd {WORKTREE} && "
                "/Users/hoangminhlong/my-quantitative/.venv/bin/python "
                "-m pytest tests/test_forex_ng2_p0.py -q")
    tests_row = {"command": test_cmd, "verdict": "NOT_RUN"}
    if args.pytest_exit is not None:
        tests_row["exit_code"] = args.pytest_exit
        tests_row["verdict"] = "PASS" if args.pytest_exit == 0 else "FAIL"
        if args.pytest_log and os.path.exists(args.pytest_log):
            tests_row["output_tail"] = open(args.pytest_log).read()[-800:]
    commands.append(tests_row)

    # ========================== gate ==================================== #
    os.makedirs(OUT_DIR, exist_ok=True)
    census_artifact = {
        "schema": "forex_ng2_run/p0_revision_census@1",
        "measured_utc": now_utc(),
        "cycle_id": "FOREX-NG2",
        "task_id": "forex-ng2-p0-census",
        "method": {
            "revision_event_definition": (
                "per economy and reference month m: v1 = first vintage "
                "publishing m (earliest realtime_start with non-missing "
                "value), v2 = immediately following vintage; REVISION "
                "EVENT iff I_v2(m) != I_v1(m) with full available-time "
                "evidence (realtime windows on both vintages); ratio "
                "R = I_v2/I_v1 - 1 (plan section 4)"),
            "usability": (
                "v2 availability day within the S0 window "
                f"{rs.S0_WINDOW[0]}..{rs.S0_WINDOW[1]} (16:00-NY grid "
                "coverage); PIT at v2.realtime_start, date-only evidence "
                "-> conservative same-day bound in consumers"),
            "monotonicity": "v2.realtime > v1.realtime STRICT (fail-closed); "
                            "byte-identical duplicate vintage rows are "
                            "deduplicated first (disclosed ingest artifact; "
                            "conflicting same-day rows still raise)",
            "cross_economy_join": (
                "obs month key across economies; a month with >=2 "
                "economies carrying usable revision events is one "
                "differential month"),
            "au_nz_lag_mapping": rs.QUARTERLY_LAG_MAPPING,
            "recent_window": {
                "law": "Q-6: last 24 calendar months of the S0 window",
                "bounds": [recent_lo, recent_hi]},
            "no_outcome_law": "NO PnL, NO outcome, NO scoring anywhere "
                              "in this census",
        },
        "legs": census["legs"],
        "us_structural_note": census.get("us_structural_note"),
        "bulk_re_referencing_disclosure": census.get(
            "bulk_re_referencing_disclosure"),
        "cross_economy_differential": census.get(
            "cross_economy_differential"),
        "monotonicity_check": census.get("monotonicity_check"),
        "canary": canary,
        "floors": floors,
        "census_error": census_error,
    }
    census_path = os.path.join(OUT_DIR, "p0_revision_census.json")
    with open(census_path, "w") as fh:
        json.dump(census_artifact, fh, indent=1, sort_keys=False)

    verdict = "PASS" if not blockers else "BLOCKED_DATA"
    gate = {
        "schema": "forex_ng2_run/p0_gate@1",
        "gate": "FOREX-NG2-P0",
        "cycle_id": "FOREX-NG2",
        "task_id": "forex-ng2-p0-census",
        "measured_utc": now_utc(),
        "git": gs,
        "dispatch_base_sha": DISPATCH_BASE_SHA,
        "base_match": gs["head_sha"] == DISPATCH_BASE_SHA,
        "pin_reverification": pin_section,
        "revision_census": {
            "artifact": "research/control/forex_ng2_run/"
                        "p0_revision_census.json",
            "sha256": sha256_file(census_path),
            "usable_events_by_economy": (
                {e: len(v) for e, v in usable_by_eco.items()}
                if census_error is None else None),
            "cross_economy_differential_months": (
                census.get("cross_economy_differential", {}).get("total")
                if census_error is None else None),
            "floors": floors,
            "canary": canary,
            "verdict": ("PASS" if census_error is None and canary_ok
                        else "FAIL"),
        },
        "commands": commands,
        "evidence_paths": {
            "cads_store_root": CADS_ROOT + " (READ-ONLY)",
            "v9_read_only_root": V9_ROOT,
            "ng1_adapter_reused_unmodified":
                "research/assets/forex_ng1/plane_adapter.py",
            "ng1_spot_reused_unmodified":
                "research/assets/forex_ng1/spot_series.py",
            "ng2_module": "research/assets/forex_ng2/revision_series.py",
            "tests": "tests/test_forex_ng2_p0.py",
        },
        "blockers": blockers,
        "verdict": verdict,
        "verdict_law": (
            "floor shortfall is an HONEST BLOCKED_DATA (plan section 2: "
            "'BLOCKED_DATA is live and cheap' -- the cycle dies in P0 "
            "before any proposal is requested; floors are frozen, never "
            "renegotiated post-measurement)"),
    }
    gate_path = os.path.join(OUT_DIR, "p0_gate.json")
    with open(gate_path, "w") as fh:
        json.dump(gate, fh, indent=1, sort_keys=False)

    print(json.dumps({
        "gate": verdict,
        "base_match": gate["base_match"],
        "blockers": blockers,
        "pins": {k: v.get("verdict") for k, v in pin_section.items()},
        "grid_days": (spot_section.get("grid_recompute") or {}).get(
            "common_weekday_grid_days"),
        "scored_authority": (pin_section.get("scored_authority_read")
                             or {}).get("scored_consumption"),
        "usable_events": {e: len(v) for e, v in usable_by_eco.items()},
        "cross_differential_months": (census.get(
            "cross_economy_differential") or {}).get("total"),
        "floors": {
            "own": {e: r["verdict"] for e, r in
                    (floors.get("own_economy") or {}).items()},
            "cross": (floors.get("cross_economy") or {}).get("verdict")},
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
