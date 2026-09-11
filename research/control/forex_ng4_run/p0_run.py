#!/usr/bin/env python
"""FOREX-NG4 P0 runner: inherited pin re-verification + EURUSD TD probe
+ EZ HICP vintaged census, under plans/PLAN_forex_ng4.md sec 3.

Measures, fail-closed, the FOREX-NG4 P0 deliverables:

1. INHERITED PIN RE-VERIFICATION (7/7 like ng3; machinery inherited
   VERBATIM from research/assets/forex_ng1|ng2|ng3 via import -- no
   edits): authority registry GRANTED + GA4 gate; S2 CADS resolve +
   5-file vintaged digest verify; S3 five pinned ledger entries;
   spot 4 pairs verify-on-read + 1842-day grid recompute; scored
   authority read (P-18, the committed ng1 proof); DGS10 ctl pin chain
   (P-13); ng1 announcement census sha pin (e8a35d23).

2. EURUSD TD PROBE (the owner's EXISTING entitlement; key loaded from
   the gitignored root .env programmatically, NEVER echoed -- only
   key_present booleans are recorded).  Exactly ONE time_series call
   (1day, 5000 bars) + at most ONE retry, and only on transport
   timeout.  Key absent / endpoint error / 403 / quota -> EURUSD
   UNAVAILABLE -> honest BLOCKED_DATA with the owner action named (the
   cycle dies in P0; no borrowed bars, ever).  On OK: raw bytes pinned
   UNTRACKED under data_raw/forex_ng4_spot/ with a committed sha256
   manifest (ng1 spot pin law), integrity census (strict ng1 parser:
   duplicates/monotonicity/finite-positive closes; DST-sanity of the
   16:00-NY mapping; OHLC cross record; coverage vs S0
   2018-04-04..2025-04-30 with closure classification) and the
   16:00-NY grid EXTENDED with EURUSD (5-pair intersection recompute,
   plan sec 3).  Authority note: same Twelve Data channel that carries
   the ng1 AUTHORIZED_INTERNAL_RESEARCH ruling (cross-ref the committed
   ng1 authority proof enforcement event; terms-gap disclosure retained
   verbatim; this lane records the ruling, never self-promotes).

3. EZ HICP VINTAGED CENSUS (research/assets/forex_ng4/ez_census.py):
   which series (CP0000EZ19M086NEST; the dispatch-suggested
   EZCPIALLMINMEI appears in NO manifest -- correction recorded);
   whether the vintaged bytes are in the pinned set (exhaustive
   search); if absent, the committed V8 DERIVED stats are recorded as
   EVIDENCE ABOUT the lost archive (never a floor PASS) and every
   EZ-floor measurement (A4 >= 30 print events, A5 >= 12 EZ-vs-US
   differential months) is NOT_RUN with the honest blocker: EZ vintaged
   ingest needs an owner / A3-lane decision.  The US leg of A5 is
   measured on pinned bytes for context (ng2/ng3 restricted standard).

NO PnL, NO outcome, NO scoring anywhere in this runner (P0 census law).

Publishes under research/control/forex_ng4_run/:
  p0_spot_pin_manifest.json, p0_eurusd_integrity_census.json,
  p0_ez_hicp_census.json, p0_gate.json.

Usage:
  p0_run.py --probe live    # first run: performs the single network call
  p0_run.py --probe pinned [--pytest-exit 0 --pytest-log FILE]
                           # re-run from pinned bytes, no network
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1 import plane_adapter as pa          # noqa: E402
from research.assets.forex_ng1 import spot_series as ss            # noqa: E402
from research.assets.forex_ng3 import revision_series as rs        # noqa: E402
from research.assets.forex_ng4 import ez_census as ez              # noqa: E402
from research.assets.forex_ng4 import td_probe as tp               # noqa: E402
from research.platform_v3.cads import CADSError                    # noqa: E402

WORKTREE = REPO_ROOT
CADS_ROOT = pa.DEFAULT_CADS_STORE_ROOT                  # READ-ONLY store
V9_ROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
           "forex-free-v9/integration")                  # READ-ONLY evidence
OUT_DIR = os.path.join(WORKTREE, "research/control/forex_ng4_run")
SCRATCH = "/tmp/forex_ng4_p0_scratch"

DISPATCH_BASE_SHA = "330a6cd0c829082d03f2658e2cebe63ef1205b2d"

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
US_RT_CADS_ADDRESS = (
    "7f18ec982374ce4dfb235f53f001327793df8e1c0077d31206de25aa3455ac94")

#: ng4 EURUSD pin artifacts (this lane's OWN committed pin; the raw
#: bytes stay untracked under data_raw/forex_ng4_spot/).
EURUSD_PIN_DIR = tp.PIN_DIR_DEFAULT
EURUSD_MANIFEST_OUT = os.path.join(OUT_DIR, "p0_spot_pin_manifest.json")
EURUSD_CENSUS_OUT = os.path.join(OUT_DIR, "p0_eurusd_integrity_census.json")
EZ_CENSUS_OUT = os.path.join(OUT_DIR, "p0_ez_hicp_census.json")

#: Known FX calendar closures for missing-weekday classification of the
#: EURUSD coverage census (only dates that actually appear missing are
#: looked up; ng1 closure law extended with the EZ-area dates inside the
#: S0 window: Easter Mondays + Dec 26).
KNOWN_CLOSURES = {
    "2019-01-01": "New Year's Day (FX global closure)",
    "2019-04-19": "Good Friday (FX global closure)",
    "2019-04-22": "Easter Monday (EZ-area closure)",
    "2019-12-25": "Christmas Day (FX global closure)",
    "2019-12-26": "Dec 26 (EZ-area closure)",
    "2020-01-01": "New Year's Day (FX global closure)",
    "2020-04-10": "Good Friday (FX global closure)",
    "2020-04-13": "Easter Monday (EZ-area closure)",
    "2020-12-25": "Christmas Day (FX global closure)",
    "2021-01-01": "New Year's Day (FX global closure)",
    "2021-04-02": "Good Friday (FX global closure)",
    "2021-04-05": "Easter Monday (EZ-area closure)",
    "2021-12-24": "Christmas Eve (EZ-area early close / provider gap)",
    "2021-12-31": "New Year's Eve (EZ-area early close / provider gap)",
    "2022-04-15": "Good Friday (FX global closure)",
    "2022-04-18": "Easter Monday (EZ-area closure)",
    "2022-12-26": "Dec 26 (EZ-area closure; Dec 25 is a Sunday)",
    "2023-01-02": "New Year's Day observed (FX global closure)",
    "2023-04-07": "Good Friday (FX global closure)",
    "2023-04-10": "Easter Monday (EZ-area closure)",
    "2023-12-25": "Christmas Day (FX global closure)",
    "2023-12-26": "Dec 26 (EZ-area closure)",
    "2024-01-01": "New Year's Day (FX global closure)",
    "2024-03-29": "Good Friday (FX global closure)",
    "2024-04-01": "Easter Monday (EZ-area closure)",
    "2024-12-25": "Christmas Day (FX global closure)",
    "2024-12-26": "Dec 26 (EZ-area closure)",
    "2025-01-01": "New Year's Day (FX global closure)",
    "2025-04-18": "Good Friday (FX global closure)",
    "2025-04-21": "Easter Monday (EZ-area closure; GBPUSD closure too)",
    "2019-05-22": ("UNEXPLAINED_DATA_HOLE (no G7 FX calendar closure; "
                   "the same provider hole the ng1 GBPUSD census "
                   "recorded -- recorded, not repaired)"),
}


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


def write_json(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False)
        fh.write("\n")


# --------------------------------------------------------------------------- #
# 2. EURUSD probe + pin + integrity census (ng1 p1_spot law re-run on the
#    ng4 lane's own bytes; helpers re-implemented from the ng1
#    build_artifacts law -- DST sanity / coverage / OHLC record)
# --------------------------------------------------------------------------- #

def _dst_sanity(days: list[date]) -> dict:
    """ng1 law verbatim: every consecutive 16:00-NY instant gap must
    equal calendar-days*24h adjusted ONLY by US DST transitions falling
    between the two instants."""
    gaps, anomalies = [], []
    for prev, cur in zip(days, days[1:]):
        inst_prev = ss.ny_decision_instant_utc(prev)
        inst_cur = ss.ny_decision_instant_utc(cur)
        gap_h = (inst_cur - inst_prev).total_seconds() / 3600.0
        cal_h = (cur - prev).days * 24.0
        off_p = datetime(prev.year, prev.month, prev.day, 16,
                         tzinfo=ss.NY_TZ).utcoffset()
        off_c = datetime(cur.year, cur.month, cur.day, 16,
                         tzinfo=ss.NY_TZ).utcoffset()
        dst_h = (off_p - off_c).total_seconds() / 3600.0
        gaps.append(gap_h)
        if abs(gap_h - (cal_h + dst_h)) > 1e-9:
            anomalies.append({
                "from": prev.isoformat(), "to": cur.isoformat(),
                "instant_gap_hours": gap_h, "calendar_hours": cal_h,
                "dst_offset_delta_hours": dst_h,
                "expected_hours": cal_h + dst_h})
    return {
        "bars_mapped": len(days),
        "instant_gap_distribution_hours": {
            str(k): v for k, v in sorted(Counter(gaps).items())},
        "gaps_not_explained_by_calendar_plus_dst": anomalies,
        "all_gaps_explained": not anomalies,
        "note": ("a 3-day Fri->Mon gap is 72h normally, 71h across a "
                 "spring-forward weekend, 73h across a fall-back "
                 "weekend; 1-day gaps are exactly 24h (transitions occur "
                 "on Sundays, which carry no weekday grid instant)"),
        "law_source": ("ng1 build_artifacts._dst_sanity law, "
                       "re-implemented verbatim on this lane"),
    }


def _coverage(days: list[date]) -> dict:
    weekdays = {GRID_WINDOW[0] + timedelta(days=i)
                for i in range((GRID_WINDOW[1] - GRID_WINDOW[0]).days + 1)}
    weekdays = {d for d in weekdays if d.weekday() < 5}
    present = {d for d in days
               if GRID_WINDOW[0] <= d <= GRID_WINDOW[1]}
    missing = sorted(weekdays - present)
    weekend_in_window = [d for d in days
                         if GRID_WINDOW[0] <= d <= GRID_WINDOW[1]
                         and d.weekday() >= 5]
    missing_rows = [{
        "date": d.isoformat(), "weekday": d.strftime("%A"),
        "classification": KNOWN_CLOSURES.get(
            d.isoformat(), "UNCLASSIFIED"),
    } for d in missing]
    return {
        "bars_in_window_weekday": len(present & weekdays),
        "weekend_bars_in_window_excluded_from_grid": len(weekend_in_window),
        "total_weekdays_in_window": len(weekdays),
        "missing_weekdays": missing_rows,
        "unclassified_missing_count": sum(
            1 for r in missing_rows if r["classification"] == "UNCLASSIFIED"),
    }


def _ohlc_cross(raw_values: list[dict]) -> dict:
    violations = []
    for v in raw_values:
        try:
            o, h, l, c = (float(v[k]) for k in ("open", "high",
                                                "low", "close"))
        except (KeyError, TypeError, ValueError):
            violations.append({"date": v.get("datetime"),
                               "kind": "UNPARSEABLE_OHLC"})
            continue
        if not (h >= l and h >= o and h >= c and l <= o and l <= c):
            viol = []
            if o > h: viol.append(("open", "high", o - h))
            if o < l: viol.append(("open", "low", l - o))
            if c > h: viol.append(("close", "high", c - h))
            if c < l: viol.append(("close", "low", l - c))
            violations.append({
                "date": v["datetime"], "kind": "OHLC_CROSS",
                "violations": [{"field_a": a, "field_b": b,
                                "abs_excess": round(x, 10)}
                               for a, b, x in viol],
                "max_abs_excess_bps_of_close": round(
                    max(x for _a, _b, x in viol) / c * 1e4, 4)})
    return {
        "count": len(violations), "rows": violations,
        "policy": ("RECORDED, not serve-blocking: all closes are "
                   "finite-positive and the decision grid consumes close "
                   "only; violations are provider open/close-vs-range "
                   "rounding artifacts (ng1 law)"),
    }


def eurusd_census(bars: list[dict], payload: dict, sha: str) -> dict:
    """Full integrity census on the pinned EURUSD bars (strict ng1
    parser already applied upstream -- duplicates would have refused)."""
    days = [b["date"] for b in bars]
    storage = [str(v["datetime"]) for v in payload["values"]]
    return {
        "schema": "forex_ng4_p0_eurusd_integrity_census@1",
        "cycle_id": "FOREX-NG4",
        "task_id": "forex-ng4-p0-census",
        "measured_utc": now_utc(),
        "pair": "EURUSD",
        "sha256": sha,
        "s0_window": {"start": GRID_WINDOW[0].isoformat(),
                      "end": GRID_WINDOW[1].isoformat(),
                      "basis": ("ng1-ng3 plane S0 window inherited "
                                "(ng3 grid recompute law)")},
        "parser": "research.assets.forex_ng1.spot_series.parse_spot_payload"
                  " (strict, reused unmodified: status/meta/symbol/1day, "
                  "duplicate dates, non-ISO datetimes, non-finite or "
                  "non-positive closes, non-monotonic storage ALL refuse)",
        "parser_fail_closed_checks": [
            "status != ok -> refuse", "meta.interval != 1day -> refuse",
            "meta.symbol != EUR/USD -> refuse",
            "duplicate bar datetime -> refuse",
            "non-ISO datetime -> refuse",
            "non-finite / non-positive close -> refuse",
            "non-monotonic storage order -> refuse",
            "sha256 verify-on-read mismatch -> refuse",
        ],
        "schema_meta": {
            "status": payload.get("status"),
            "meta": payload.get("meta"),
            "bar_fields": sorted({k for v in payload["values"] for k in v}),
            "values_storage": ("newest-first" if storage[0] > storage[-1]
                               else "oldest-first"),
        },
        "bars": len(bars),
        "first_bar": days[0].isoformat(),
        "last_bar": days[-1].isoformat(),
        "duplicate_dates": 0,
        "non_finite_or_non_positive_close": 0,
        "strictly_increasing_served_days": all(
            days[i] < days[i + 1] for i in range(len(days) - 1)),
        "weekend_bars_total": sum(1 for d in days if d.weekday() >= 5),
        "saturday_bars": sum(1 for d in days if d.weekday() == 5),
        "sunday_bars": sum(1 for d in days if d.weekday() == 6),
        "ohlc_cross_violations": _ohlc_cross(payload["values"]),
        "dst_sanity_16ny": _dst_sanity(days),
        "coverage_s0_window": _coverage(days),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", choices=("live", "pinned"), default="live",
                    help="live: the single permitted network call; "
                         "pinned: verify-on-read the already-pinned bytes "
                         "(manifest sha law), no network")
    ap.add_argument("--pytest-exit", type=int, default=None,
                    help="exit code of the mandated pytest command")
    ap.add_argument("--pytest-log", default=None,
                    help="path holding the pytest tail (evidence)")
    args = ap.parse_args()

    blockers: list[str] = []
    commands: list[dict] = []
    gs = git_state()
    os.makedirs(OUT_DIR, exist_ok=True)

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
        "note": "the pinned S3 ledger carries FIVE entries and ALL FIVE "
                "are re-verified (superset, nothing skipped)",
        "verdict": ("PASS" if len(s3_rows) == len(pa.S3_ENTRY_NAMES)
                    and all(r["verdict"] == "PASS"
                            for r in s3_rows.values()) else "FAIL"),
    }
    if pin_section["s3_repin"]["verdict"] != "PASS":
        blockers.append("S3 re-pin failed (resolve/verify/refusal)")

    # 1d. spot 4 pairs: verify-on-read + grid 1842 recompute
    spot_section: dict = {"pairs": {}}
    ng1_serieses: dict = {}
    try:
        manifest = ss.load_pin_manifest(SPOT_PIN_MANIFEST)
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
        for pair in ss.FUNDED_PAIRS:
            sha = ss.verify_spot_file(manifest, pair, data_dir=pinned_data_dir)
            series = ss.resolve_spot_series(pair, SPOT_PIN_MANIFEST,
                                            data_dir=pinned_data_dir)
            ng1_serieses[pair] = series
            spot_section["pairs"][pair] = {
                "pinned_sha256": sha,
                "bars": series.bars,
                "first_day": series.first_day.isoformat(),
                "last_day": series.last_day.isoformat(),
                "verdict": "PASS",
            }
        grid4 = ss.common_weekday_grid(
            ng1_serieses, GRID_WINDOW[0], GRID_WINDOW[1])
        binding = min(
            (len(s.window_days(GRID_WINDOW[0], GRID_WINDOW[1]))
             for s in ng1_serieses.values()), default=0)
        spot_section["grid_recompute"] = {
            "window": [GRID_WINDOW[0].isoformat(),
                       GRID_WINDOW[1].isoformat()],
            "common_weekday_grid_days": len(grid4),
            "binding_pair_days": binding,
            "first_day": grid4[0].isoformat() if grid4 else None,
            "last_day": grid4[-1].isoformat() if grid4 else None,
            "law": "FX 24/5 weekdays in window intersected across the four "
                   "funded-pair calendars (V9 build_grid law, inherited)",
        }
        spot_section["verdict"] = (
            "PASS" if all(p["verdict"] == "PASS"
                          for p in spot_section["pairs"].values())
            and len(grid4) == GRID_LAW_DAYS else "FAIL")
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
    pin_section["verdict"] = (
        "PASS" if all(v.get("verdict") == "PASS"
                      for k, v in pin_section.items() if k != "verdict")
        else "FAIL")

    # ==================== 2. EURUSD TD PROBE =========================== #
    eurusd: dict = {"probe": {"mode": args.probe}}
    eurusd_probe_available = False
    eurusd_sha: str | None = None
    eurusd_payload: dict | None = None
    eurusd_bars: list[dict] | None = None
    key_present_row: dict = {
        "key_name": tp.KEY_NAME,
        "key_source": ("gitignored root .env, loaded programmatically; "
                       "the value is never echoed into any output, log, "
                       "artifact or commit"),
        "key_present": tp.load_api_key() is not None,
    }
    eurusd["key_check"] = key_present_row

    if args.probe == "live":
        rec = tp.probe_eurusd(tp.load_api_key())
        # scrub the payload bytes from the recorded evidence (bytes are
        # pinned to disk, never embedded in the gate json)
        eurusd["probe"] = {
            k: v for k, v in rec.items()
            if k not in ("payload_bytes", "payload")}
        if rec["status"] == "OK":
            pre = tp.strict_payload_check(rec["payload"])
            if not pre["ok"]:
                rec["status"] = "UNAVAILABLE"
                eurusd["probe"]["status"] = "UNAVAILABLE"
                eurusd["probe"]["precheck_problems"] = pre["problems"]
                eurusd["probe"]["reason"] = (
                    "provider contract pre-check failed: EURUSD "
                    "UNAVAILABLE (fail-closed)")
            else:
                pin_ev = tp.pin_probe_bytes(rec["payload_bytes"],
                                            EURUSD_PIN_DIR)
                eurusd["pin"] = pin_ev
                eurusd_sha = pin_ev["copy_sha256"]
                eurusd_payload = rec["payload"]
                eurusd_probe_available = True
        else:
            blockers.append(
                "EURUSD UNAVAILABLE under the current entitlement (probe "
                "measured: " + str(eurusd["probe"].get("reason",
                              "no reason recorded"))[:200] + ") -- owner "
                "action: confirm/extend the Twelve Data entitlement or "
                "name the lane that may re-acquire EURUSD")
    else:   # pinned: verify-on-read against the committed manifest
        try:
            committed = json.load(open(EURUSD_MANIFEST_OUT, "r",
                                       encoding="utf-8"))
            pinned_sha = committed["files"]["EURUSD"]["copy_sha256"]
            ev = tp.verify_pinned_bytes(EURUSD_PIN_DIR, pinned_sha)
            eurusd["probe"] = {
                "mode": "pinned",
                "status": "OK",
                "law": ("verify-on-read: pinned bytes re-hashed equal to "
                        "the committed manifest sha256 (no network)"),
            }
            eurusd["pin"] = {
                "file": tp.PIN_FILE,
                "copy_path_absolute": ev["copy_path_absolute"],
                "copy_sha256": ev["copy_sha256"],
                "bytes": ev["bytes"],
                "raw_bytes_policy": "UNTRACKED_NEVER_COMMITTED",
            }
            with open(os.path.join(EURUSD_PIN_DIR, tp.PIN_FILE), "r",
                      encoding="utf-8") as fh:
                eurusd_payload = json.load(fh)
            eurusd_sha = ev["copy_sha256"]
            eurusd_probe_available = True
        except (tp.ProbeError, OSError, KeyError, ValueError) as exc:
            eurusd["probe"] = {"mode": "pinned", "status": "UNAVAILABLE",
                               "error": repr(exc)[:400]}
            blockers.append(
                "EURUSD pinned-bytes verification failed (fail-closed): "
                + repr(exc)[:200])

    if eurusd_probe_available:
        try:
            eurusd_bars = ss.parse_spot_payload(eurusd_payload, "EURUSD")
            census = eurusd_census(eurusd_bars, eurusd_payload,
                                   str(eurusd_sha))
            write_json(EURUSD_CENSUS_OUT, census)
            eurusd["integrity_census"] = {
                "artifact": "research/control/forex_ng4_run/"
                            "p0_eurusd_integrity_census.json",
                "sha256": sha256_file(EURUSD_CENSUS_OUT),
                "bars": census["bars"],
                "first_bar": census["first_bar"],
                "last_bar": census["last_bar"],
                "duplicate_dates": census["duplicate_dates"],
                "dst_all_gaps_explained":
                    census["dst_sanity_16ny"]["all_gaps_explained"],
                "coverage_s0": census["coverage_s0_window"],
                "ohlc_cross_count":
                    census["ohlc_cross_violations"]["count"],
            }
            if census["dst_sanity_16ny"]["all_gaps_explained"] is False:
                blockers.append("EURUSD DST sanity failed (16:00-NY map)")
            # the pin manifest (committed authority for the untracked
            # bytes) is written ONLY from verified-probe bytes
            pin_manifest = {
                "schema": "forex_ng4_p0_spot_pin_manifest@1",
                "cycle_id": "FOREX-NG4",
                "task_id": "forex-ng4-p0-census",
                "pinned_utc": now_utc(),
                "pin_basis": (
                    "raw bytes of the FOREX-NG4 P0 EURUSD probe (Twelve "
                    "Data time_series under the OWNER existing "
                    "entitlement; exactly one call + at most one "
                    "timeout-only retry; key loaded programmatically from "
                    "the gitignored root .env and never echoed). Raw "
                    "bytes are UNTRACKED under data_raw/forex_ng4_spot/ "
                    "(data_raw/ is not gitignored in this worktree -> "
                    "never committed); this manifest is the committed "
                    "authority. Same channel/product class as the ng1 "
                    "spot pin (four funded pairs); the ng1 authority "
                    "ruling AUTHORIZED_INTERNAL_RESEARCH is cross-"
                    "referenced, not re-ruled here."),
                "raw_bytes_policy": "UNTRACKED_NEVER_COMMITTED",
                "files": {
                    "EURUSD": {
                        "file": tp.PIN_FILE,
                        "copy_path_absolute": os.path.join(
                            EURUSD_PIN_DIR, tp.PIN_FILE),
                        "copy_sha256": eurusd_sha,
                        "bytes": (eurusd["pin"] or {}).get("bytes"),
                        "bars": census["bars"],
                        "first_bar_date": census["first_bar"],
                        "last_bar_date": census["last_bar"],
                        "provider_meta": eurusd_payload.get("meta", {}),
                        "status": eurusd_payload.get("status"),
                    },
                },
            }
            write_json(EURUSD_MANIFEST_OUT, pin_manifest)
            eurusd["pin_manifest"] = {
                "artifact": "research/control/forex_ng4_run/"
                            "p0_spot_pin_manifest.json",
                "sha256": sha256_file(EURUSD_MANIFEST_OUT),
                "copy_sha256": eurusd_sha,
            }
        except (ss.SpotDataError, OSError, ValueError, KeyError) as exc:
            eurusd_probe_available = False
            eurusd["parse_error"] = repr(exc)[:400]
            blockers.append("EURUSD strict parse failed (fail-closed): "
                            + repr(exc)[:200])

    # authority note: same channel as the ng1 ruling; cross-ref, no
    # self-promotion (the lane records, the committed ng1 proof rules)
    authority_note: dict = {
        "channel": {
            "provider": "Twelve Data",
            "endpoint": tp.ENDPOINT,
            "product": ("FX spot daily bars (interval=1day, outputsize="
                        "5000, provider format {meta, values, status}; "
                        "date-only bar datetimes; no volume field) -- the "
                        "same channel/product class as the four ng1 "
                        "funded-pair pins"),
            "keyed": True,
            "key_handling": ("TWELVE_DATA_API_KEY via the gitignored root "
                             ".env, loaded programmatically, never "
                             "echoed (ng1 key law, inherited)"),
            "entitlement_basis": (
                "OWNER existing entitlement (the same entitlement the ng1 "
                "proof ruled on; no new purchase/signup/account)"),
        },
        "cross_ref_ng1_ruling": {
            "proof_path": ("research/control/forex_ng1_run/p1_spot/"
                           "spot_authority_proof.json (committed; this "
                           "lane reads, never edits)"),
            "verdict": "AUTHORIZED_INTERNAL_RESEARCH",
            "scored_consumption": "AUTHORIZED",
            "ruling_event": ("authority_enforcement.ruling_utc "
                             "2026-09-11T15:30:00Z, ruled by A1_LEAD "
                             "under owner standing delegation (ng1); the "
                             "require_scored_authority read in this "
                             "gate's pin_reverification proves the "
                             "committed block still yields AUTHORIZED"),
            "scope_note": (
                "the ng1 ruling authorizes the Twelve Data CHANNEL under "
                "the owner entitlement; ng1 pinned 4 pairs and its "
                "serving layer refused EURUSD as unpinned (structural "
                "canary evidence); THIS lane pins EURUSD under the SAME "
                "channel/ruling via its own committed manifest -- no new "
                "authority decision is claimed or needed for "
                "staging/census consumption"),
        },
        "terms_disclosure_retained_verbatim": (
            "NO WRITTEN TERMS EXIST ANYWHERE IN EVIDENCE (terms_url=None) "
            "-- DISCLOSED; A7 prelaunch independent assessment rates the "
            "terms gap MEDIUM (not blocking) with the TD-outside-S2/S3-"
            "plane tension to be reported at terminal"),
        "this_lane_law": (
            "recording lane only: P0 census/staging consumption through "
            "pinned bytes; no scored consumption happens in P0 (NO PnL, "
            "NO outcome, NO scoring)"),
    }
    eurusd["authority"] = authority_note

    # 16:00-NY grid EXTENDED with EURUSD (plan sec 3): recompute the
    # intersection grid across the FOUR funded pairs + EURUSD.
    if eurusd_probe_available and eurusd_bars is not None:
        eurusd_series = ss.SpotSeries(
            pair="EURUSD", bars=len(eurusd_bars),
            first_day=eurusd_bars[0]["date"],
            last_day=eurusd_bars[-1]["date"],
            days=tuple(b["date"] for b in eurusd_bars),
            closes={b["date"]: b["close"] for b in eurusd_bars},
            sha256=str(eurusd_sha))
        five = dict(ng1_serieses)
        five["EURUSD"] = eurusd_series
        grid5 = ss.common_weekday_grid(five, GRID_WINDOW[0], GRID_WINDOW[1])
        grid4 = spot_section.get("grid_recompute", {})
        days4 = None
        if spot_section.get("verdict") == "PASS":
            days4 = ss.common_weekday_grid(
                ng1_serieses, GRID_WINDOW[0], GRID_WINDOW[1])
        removed = (sorted(set(days4) - set(grid5))
                   if days4 is not None else None)
        removed_rows = [{
            "date": d.isoformat(), "weekday": d.strftime("%A"),
            "classification": KNOWN_CLOSURES.get(
                d.isoformat(), "UNCLASSIFIED"),
        } for d in (removed or [])]
        eurusd["grid_extension_5pair"] = {
            "window": [GRID_WINDOW[0].isoformat(),
                       GRID_WINDOW[1].isoformat()],
            "grid_days_4pair_inherited":
                grid4.get("common_weekday_grid_days"),
            "grid_days_5pair_with_eurusd": len(grid5),
            "days_removed_by_eurusd": removed_rows,
            "first_day": grid5[0].isoformat() if grid5 else None,
            "last_day": grid5[-1].isoformat() if grid5 else None,
            "law": ("plan sec 3: the 16:00-NY frozen grid is EXTENDED with "
                    "EURUSD by recomputing the weekday intersection "
                    "across the four funded-pair calendars + the pinned "
                    "EURUSD calendar (V9 build_grid law; EZ lanes will "
                    "consume THIS grid)"),
        }
        if len(grid5) == 0:
            blockers.append("5-pair grid extension empty (EURUSD calendar "
                            "does not intersect the funded grid)")

    eurusd["verdict"] = ("PASS" if eurusd_probe_available
                         and eurusd.get("integrity_census", {}).get(
                             "duplicate_dates") == 0
                         else ("BLOCKED_DATA" if not eurusd_probe_available
                               else "FAIL"))

    # ==================== 3. EZ HICP VINTAGED CENSUS =================== #
    ez_block: dict = {}
    ez_error: str | None = None
    us_context: dict | None = None
    try:
        byte_search = ez.find_ez_bytes()
        v8_derived = ez.extract_v8_derived_evidence()
        cv_search = ez.find_current_vintage_doi()
        # US leg of the A5 differential, measured on pinned bytes (the
        # ng2/ng3 restricted first-print standard, machinery imported
        # unmodified) -- context only: the differential join needs EZ.
        us_payload = json.load(open(
            cads_object_path(US_RT_CADS_ADDRESS), "rb"))
        us_rows = pa.parse_fred_vintaged(us_payload)
        us_stream = rs.build_restricted_stream("US", us_rows)
        us_recent = rs.restricted_recent_events(us_stream["restricted"])
        us_context = {
            "series": "CPIAUCSL (US/fred_cpiaucsl_rt.json, pinned via "
                      "CADS 7f18ec98...)",
            "restricted_events": len(us_stream["restricted"]),
            "restricted_months": sorted(
                {e.obs_month for e in us_stream["restricted"]}),
            "recent_24m_count": us_recent["count"],
            "law": ("ng2/ng3 restricted first-print standard on pinned "
                    "bytes; measured as the US leg of the A5 "
                    "EZ-vs-US differential -- the join itself is NOT_RUN "
                    "without EZ vintaged bytes"),
            "verdict": "MEASURED_CONTEXT_ONLY",
        }
        ez_block = ez.ez_census_decision(
            byte_search, v8_derived, cv_search, us_context)
    except (ez.EZCensusError, OSError, ValueError, KeyError,
            pa.VintageStructureError) as exc:
        ez_error = repr(exc)[:400]
        ez_block = {"verdict": "FAIL", "error": ez_error}
    ez_block["schema"] = "forex_ng4_p0_ez_hicp_census@1"
    ez_block["cycle_id"] = "FOREX-NG4"
    ez_block["task_id"] = "forex-ng4-p0-census"
    ez_block["measured_utc"] = now_utc()
    ez_block["s0_window"] = {"start": ez.S0_WINDOW[0],
                             "end": ez.S0_WINDOW[1]}
    ez_block["no_outcome_law"] = ("NO PnL, NO outcome, NO scoring in this "
                                  "census")
    write_json(EZ_CENSUS_OUT, ez_block)
    if ez_block.get("verdict") == "BLOCKED_DATA":
        for problem in ez_block.get("blockers", []):
            blockers.append("EZ HICP vintaged census BLOCKED_DATA: "
                            + problem[:300])
        blockers.append(
            "EZ vintaged ingest needs an owner / A3-lane decision (next "
            "action: re-ingest CP0000EZ19M086NEST vintaged bytes under "
            "the V8 retrieval window and re-run this gate) -- floors A4 "
            "(>= 30 EZ print events) and A5 (>= 12 EZ-vs-US differential "
            "months) are NOT_RUN until then")
    elif ez_block.get("verdict") != "MEASURABLE":
        blockers.append(f"EZ census build error: {ez_error}")

    # ======================== tests row ================================= #
    test_cmd = (f"cd {WORKTREE} && "
                "/Users/hoangminhlong/my-quantitative/.venv/bin/python "
                "-m pytest tests/test_forex_ng4_p0.py -q")
    tests_row = {"command": test_cmd, "verdict": "NOT_RUN"}
    if args.pytest_exit is not None:
        tests_row["exit_code"] = args.pytest_exit
        tests_row["verdict"] = "PASS" if args.pytest_exit == 0 else "FAIL"
        if args.pytest_log and os.path.exists(args.pytest_log):
            tests_row["output_tail"] = open(args.pytest_log).read()[-800:]
    commands.append(tests_row)

    # ========================== gate ==================================== #
    verdict = "PASS" if not blockers else "BLOCKED_DATA"
    gate = {
        "schema": "forex_ng4_run/p0_gate@1",
        "gate": "FOREX-NG4-P0",
        "cycle_id": "FOREX-NG4",
        "task_id": "forex-ng4-p0-census",
        "measured_utc": now_utc(),
        "git": gs,
        "dispatch_base_sha": DISPATCH_BASE_SHA,
        "base_match": gs["head_sha"] == DISPATCH_BASE_SHA,
        "pin_reverification": pin_section,
        "eurusd_td_probe": {
            "key_check": key_present_row,
            "probe": eurusd.get("probe"),
            "pin": eurusd.get("pin"),
            "pin_manifest": eurusd.get("pin_manifest"),
            "integrity_census": {
                k: v for k, v in
                (eurusd.get("integrity_census") or {}).items()
                if k != "coverage_s0"},
            "coverage_s0_window": (eurusd.get("integrity_census")
                                   or {}).get("coverage_s0"),
            "grid_extension_5pair": eurusd.get("grid_extension_5pair"),
            "authority": authority_note,
            "verdict": eurusd.get("verdict"),
        },
        "ez_hicp_census": {
            "artifact": "research/control/forex_ng4_run/p0_ez_hicp_census.json",
            "sha256": sha256_file(EZ_CENSUS_OUT),
            "series_identification": ez_block.get("series_identification"),
            "status": ez_block.get("status"),
            "bytes_search_resolvable":
                (ez_block.get("bytes_search") or {}).get(
                    "bytes_resolvable"),
            "floors": ez_block.get("floors"),
            "us_side_context": ez_block.get("us_side_context"),
            "blockers": ez_block.get("blockers"),
            "verdict": ez_block.get("verdict"),
        },
        "commands": commands,
        "evidence_paths": {
            "cads_store_root": CADS_ROOT + " (READ-ONLY)",
            "v9_read_only_root": V9_ROOT,
            "ng1_adapter_reused_unmodified":
                "research/assets/forex_ng1/plane_adapter.py",
            "ng1_spot_reused_unmodified":
                "research/assets/forex_ng1/spot_series.py",
            "ng3_module_reused_unmodified":
                "research/assets/forex_ng3/revision_series.py",
            "ng4_modules": ["research/assets/forex_ng4/td_probe.py",
                            "research/assets/forex_ng4/ez_census.py"],
            "eurusd_pinned_bytes": ("data_raw/forex_ng4_spot/EURUSD.json "
                                    "(UNTRACKED; committed manifest "
                                    "carries the sha256)"),
            "tests": "tests/test_forex_ng4_p0.py",
        },
        "blockers": blockers,
        "verdict": verdict,
        "verdict_law": (
            "plan sec 2-3: EURUSD not servable by the entitlement => "
            "BLOCKED_DATA honest with the owner action named; EZ HICP "
            "vintaged bytes absent from the pinned set => the EZ floors "
            "(A4 >= 30 print events; A5 >= 12 EZ-vs-US differential "
            "months) are NOT_RUN and the gate is BLOCKED_DATA with the "
            "EZ ingest decision escalated to the owner / A3 lane; the "
            "inherited-pin section and any measurable census rows remain "
            "PASS/NOT_RUN exactly as measured -- never inferred"),
    }
    gate_path = os.path.join(OUT_DIR, "p0_gate.json")
    write_json(gate_path, gate)

    print(json.dumps({
        "gate": verdict,
        "base_match": gate["base_match"],
        "pins_7": pin_section.get("verdict"),
        "pins": {k: v.get("verdict") for k, v in pin_section.items()
                 if k != "verdict"},
        "eurusd_status": (eurusd.get("probe") or {}).get("status"),
        "eurusd_verdict": eurusd.get("verdict"),
        "eurusd_bars": (eurusd.get("integrity_census") or {}).get("bars"),
        "eurusd_grid5": (eurusd.get("grid_extension_5pair") or {}).get(
            "grid_days_5pair_with_eurusd"),
        "ez_status": ez_block.get("status"),
        "ez_verdict": ez_block.get("verdict"),
        "ez_floors": {k: v.get("verdict")
                      for k, v in (ez_block.get("floors") or {}).items()},
        "blockers": blockers,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
