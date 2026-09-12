#!/usr/bin/env python
"""RATES-NG1 P0 runner: data authority + platform v3 adoption gate.

Measures, fail-closed, the dispatch-packet P0 deliverables:

1. S5 Treasury.gov daily par-yield curve: per-year CSVs 1990..2026,
   deterministic keyless pull, sha256-pinned substrate manifest,
   depth/coverage census (rows/year, business-day coverage fraction on
   2005..2026, tenor columns per year).  FLOOR: coverage >= 90% of
   expected business days.
2. S2 FRED granted-set re-pin: DGS10, DGS2, DFII10, DFII5, T10YIE,
   T5YIE, CPIAUCSL; CPIAUCSL gets a 0-drift overlap verify against the
   inherited platform-v3 CADS pin (read-only); DGS10 gets the committed
   V8 pin-chain citation (staged bytes archived 2026-09-12: byte
   re-verify impossible, recorded honestly, never pretended).
3. EODHD family-1 ETP census: TLT/IEF/IEI/SHY RAW primary + adjusted
   corp-actions cross-check (V8 G4 method) + US delisted-channel probe
   (census item, not a floor).  FLOOR: all four with EOD through
   2026-09.
4. Treasury auction calendar PIT census 2018-01-01..pull-date from the
   official TreasuryDirect TA_WS per-year search windows (the
   ``announced`` endpoint is hard-capped at the latest 250 records --
   measured 2026-09-12 -- so it cannot carry this census).
   FLOOR: events >= 150.
5. Adoption law: every consumption goes through the rates_ng1
   ``consume_via_plane`` adapter; bounded shadow-parity pilot must show
   plane-read == raw-file-bytes digest equality.
6. P-7 canaries (fabricated curve date, fabricated tenor column,
   never-existed ticker): each fabricated access must FAIL (be
   refused); a canary breach is a gate failure.

Artifacts land in research/control/rates_ng1_run/.  Verdict is PASS
only when every floor passes, every canary is refused as expected and
parity is digest-equal; any failure yields the honest BLOCKED verdict
path (cycle dies before proposals -- plan section 2).  No signals, no
scoring, no outcome numbers anywhere.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.rates_ng1 import plane_adapter as pa  # noqa: E402
from research.assets.rates_ng1 import substrate as sub  # noqa: E402

WORKTREE = REPO_ROOT
OUT_DIR = os.path.join(WORKTREE, "research", "control", "rates_ng1_run")
RAW_ROOT = pa.RAW_SUBSTRATE_ROOT
MANIFEST_PATH = pa.SUBSTRATE_MANIFEST
SCRATCH = "/tmp/rates_ng1_p0_scratch"

AUCTION_ANN_START = "2018-01-01"
ETP_FLOOR_LAST_DATE = "2026-09-01"
COVERAGE_FLOOR_FRACTION = 0.90
AUCTION_FLOOR_EVENTS = 150

# The bounded shadow-parity pilot entries (adoption law: bounded pilot).
PARITY_PILOT = (
    "treasury_curve/par_yields_1990.csv",
    "treasury_curve/par_yields_2005.csv",
    "treasury_curve/par_yields_2016.csv",
    "treasury_curve/par_yields_2025.csv",
    "treasury_curve/par_yields_2026.csv",
    "fred/DGS10.json",
    "fred/CPIAUCSL.json",
    "etp_eod/TLT.US.json",
    "auctions/ta_ws_search_2025.json",
)


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


def write_json(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=False)
        fh.write("\n")


def save_raw(files: dict[str, bytes], manifest_files: dict[str, dict],
             rel_name: str, data: bytes, source_url: str) -> None:
    path = os.path.join(RAW_ROOT, rel_name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)
    manifest_files[rel_name] = sub.build_manifest_entry(
        rel_name, data, source_url)
    files[rel_name] = data


def fetch_recorded(rel_name: str, url: str, manifest_files: dict,
                   files: dict, pull_log: dict) -> bool:
    """Bounded pull + raw save + manifest pin; failures recorded
    fail-closed (redacted) and never fabricated."""
    try:
        data = sub.fetch_url(url)
    except Exception as exc:  # noqa: BLE001 - recorded redacted only
        pull_log[rel_name] = {
            "status": "PULL_FAILED", "url": sub.redact(url),
            "error": sub.redact(repr(exc))[:300]}
        return False
    save_raw(files, manifest_files, rel_name, data, url)
    pull_log[rel_name] = {"status": "PULLED",
                          "url": sub.redact(url), "bytes": len(data)}
    time.sleep(0.15)
    return True


# --------------------------------------------------------------------- #
# section 1: Treasury curve
# --------------------------------------------------------------------- #

def run_treasury(manifest_files: dict, files: dict, pull_log: dict) -> dict:
    year_rows: dict[int, list[dict[str, str]]] = {}
    failed_years: list[dict] = []
    for year in pa.CURVE_YEARS:
        rel = f"treasury_curve/par_yields_{year}.csv"
        url = sub.treasury_curve_url(year)
        ok = fetch_recorded(rel, url, manifest_files, files, pull_log)
        if not ok:
            failed_years.append({"year": year, "status": "PULL_FAILED"})
            continue
        try:
            year_rows[year] = pa.parse_treasury_curve_csv(files[rel])
        except pa.PlaneDataBlocked as exc:
            failed_years.append({"year": year, "status": "PARSE_BLOCKED",
                                 "error": str(exc)[:200]})
    max_date = max((r["date"] for rows in year_rows.values() for r in rows),
                   default=None)
    census = sub.treasury_curve_census(
        year_rows, "2005-01-01", max_date or "2026-09-11")
    all_pulled = len(year_rows) == len(pa.CURVE_YEARS)
    floor_pass = (all_pulled
                  and census["coverage_fraction"]
                  >= COVERAGE_FLOOR_FRACTION)
    return {
        "section": "s5_treasury_par_yield_curve",
        "source": sub.redact(sub.treasury_curve_url(2005)).split(
            "/2005/")[0] + "/{YYYY}/ (per-year CSVs, keyless)",
        "years_pulled": len(year_rows),
        "years_expected": len(pa.CURVE_YEARS),
        "failed_years": failed_years,
        "census": census,
        "floor": {
            "name": "treasury_curve_coverage",
            "definition": (f"coverage_fraction >= "
                           f"{COVERAGE_FLOOR_FRACTION} of expected "
                           "business days (Mon-Fri grid) on "
                           "[2005-01-01, measured last curve date]; all "
                           "37 per-year files pulled"),
            "measured": census["coverage_fraction"],
            "measured_curve_days": census["curve_days_in_window"],
            "measured_expected_days":
                census["expected_business_days_window"],
            "verdict": "PASS" if floor_pass else "FAIL",
        },
        "verdict": "PASS" if (all_pulled and not failed_years) else "FAIL",
    }


# --------------------------------------------------------------------- #
# section 2: FRED re-pin
# --------------------------------------------------------------------- #

FRED_PULL_SPEC = {
    "DGS10": None, "DGS2": None, "DFII10": None, "DFII5": None,
    "T10YIE": None, "T5YIE": None,
    # vintaged archive pull (bounded by the FRED 2000-vintage file-type
    # limit; 1776-07-04 is the API minimum realtime_start)
    "CPIAUCSL": "1776-07-04",
}


def run_fred(manifest_files: dict, files: dict, pull_log: dict) -> dict:
    series_census: dict[str, dict] = {}
    for sid, rt_start in FRED_PULL_SPEC.items():
        rel = f"fred/{sid}.json"
        url = sub.fred_observations_url(sid, rt_start)
        ok = fetch_recorded(rel, url, manifest_files, files, pull_log)
        if not ok:
            series_census[sid] = {"status": "PULL_FAILED"}
            continue
        try:
            obs = sub.parse_fred_payload(files[rel])
            series_census[sid] = {
                "status": "PINNED",
                "rows": len(obs),
                "first_date": obs[0]["date"],
                "last_date": obs[-1]["date"],
                "vintaged_pull": rt_start is not None,
                "sha256": manifest_files[rel]["sha256"],
            }
        except Exception as exc:  # noqa: BLE001 - recorded redacted only
            series_census[sid] = {"status": "PARSE_BLOCKED",
                                  "error": sub.redact(repr(exc))[:200]}

    # CPIAUCSL 0-drift overlap verify vs the inherited CADS pin
    overlap: dict = {"verdict": "NOT_RUN"}
    try:
        pinned = pa.resolve_inherited_cpiaucsl_pin()
        fresh = sub.parse_fred_payload(files["fred/CPIAUCSL.json"])
        overlap = sub.fred_overlap_verify(pinned["observations"], fresh)
        overlap.update({
            "pinned_cads_address": pinned["cads_address"],
            "pinned_sha256": pinned["sha256_measured"],
            "verdict": ("PASS" if overlap["zero_drift_on_overlap"]
                        else "FAIL"),
        })
    except Exception as exc:  # noqa: BLE001 - recorded redacted only
        overlap = {"verdict": "BLOCKED",
                   "error": sub.redact(repr(exc))[:300]}

    dgs10_chain = {
        "verdict": "CITED",
        "prior_pin_digest": pa.V8_DGS10_SHA256_PIN,
        "prior_manifest_digest": pa.V8_STAGED_VINTAGED_MANIFEST_SHA256,
        "witnesses": [
            "research/control/forex_free_v8_run/run_contract.json "
            "(commit 720decb3: data_pins.staged_vintaged_manifest_sha256)",
            "research/assets/forex_ng1/run/ctlpin.py (committed constant "
            "DGS10_SHA256_PIN; FOREX-NG1 lineage)",
        ],
        "honest_note": (
            "the V8 staged_vintaged DGS10.json bytes were archived out of "
            "the tree by the owner-ordered worktree cleanup "
            "(research/control/WORKTREE_CLEANUP_2026-09-12.json, P-13 "
            "archive-then-delete); a byte-level re-verify of the FRESH "
            "pull against those staged bytes is impossible, so this "
            "re-pin records the committed digest chain as citation and "
            "pins today's fresh bytes under a NEW substrate digest. No "
            "continuity claim is inferred."),
    }

    all_pinned = all(
        s.get("status") == "PINNED" for s in series_census.values())
    floor_pass = (all_pinned
                  and overlap.get("verdict") == "PASS"
                  and len(series_census) == len(pa.FRED_SERIES))
    return {
        "section": "s2_fred_granted_repin",
        "series": series_census,
        "expected_series_count": len(pa.FRED_SERIES),
        "cpiaucsl_overlap_verify": overlap,
        "dgs10_prior_pin_chain": dgs10_chain,
        "floor": {
            "name": "fred_granted_repin",
            "definition": ("all 7 granted series pulled + pinned; "
                           "CPIAUCSL overlap verify vs inherited CADS "
                           "pin shows 0 drift"),
            "verdict": "PASS" if floor_pass else "FAIL",
        },
        "verdict": "PASS" if floor_pass else "FAIL",
    }


# --------------------------------------------------------------------- #
# section 3: EODHD ETP census
# --------------------------------------------------------------------- #

def run_etp(manifest_files: dict, files: dict, pull_log: dict) -> dict:
    tickers: dict[str, dict] = {}
    for t in pa.ETP_TICKERS:
        rel = f"etp_eod/{t}.US.json"
        adj_rel = f"etp_eod/{t}.US_adj.json"
        ok = fetch_recorded(rel, sub.eodhd_eod_url(f"{t}.US", False),
                            manifest_files, files, pull_log)
        ok_adj = fetch_recorded(adj_rel,
                                sub.eodhd_eod_url(f"{t}.US", True),
                                manifest_files, files, pull_log)
        if not (ok and ok_adj):
            tickers[t] = {"status": "PULL_FAILED"}
            continue
        try:
            raw_rows = pa.parse_eodhd_eod_json(files[rel])
            adj_rows = pa.parse_eodhd_eod_json(files[adj_rel])
            xcheck = sub.split_steps(raw_rows, adj_rows)
            tickers[t] = {
                "status": "CENSORED",
                "rows": len(raw_rows),
                "first_date": raw_rows[0]["date"],
                "last_date": raw_rows[-1]["date"],
                "adj_rows": len(adj_rows),
                "corp_actions_cross_check": xcheck,
                "sha256": manifest_files[rel]["sha256"],
                "adj_sha256": manifest_files[adj_rel]["sha256"],
            }
        except Exception as exc:  # noqa: BLE001 - recorded redacted only
            tickers[t] = {"status": "PARSE_BLOCKED",
                          "error": sub.redact(repr(exc))[:200]}

    delisted_status = "NOT_RUN"
    delisted: dict = {}
    if fetch_recorded("etp_eod/us_delisted_symbols.json",
                      sub.eodhd_delisted_url(),
                      manifest_files, files, pull_log):
        try:
            entries = json.loads(
                files["etp_eod/us_delisted_symbols.json"].decode("utf-8"))
            delisted = sub.delisted_census(entries)
            delisted_status = "CENSORED"
        except Exception as exc:  # noqa: BLE001
            delisted = {"error": sub.redact(repr(exc))[:200]}
            delisted_status = "PARSE_BLOCKED"

    floor_pass = all(
        s.get("status") == "CENSORED"
        and s.get("last_date", "") >= ETP_FLOOR_LAST_DATE
        for s in tickers.values()) and len(tickers) == len(pa.ETP_TICKERS)
    return {
        "section": "eodhd_family1_etp_census",
        "tickers": tickers,
        "delisted_channel_probe": {
            "status": delisted_status,
            "census": delisted,
            "note": "census item per dispatch packet, NOT a floor",
        },
        "floor": {
            "name": "treasury_etp_eod_census",
            "definition": (f"all 4 of TLT/IEF/IEI/SHY carry EOD rows with "
                           f"last_date >= {ETP_FLOOR_LAST_DATE} (full EOD "
                           "through 2026-09); RAW primary + adjusted "
                           "corp-actions cross-check recorded"),
            "verdict": "PASS" if floor_pass else "FAIL",
        },
        "verdict": "PASS" if floor_pass else "FAIL",
    }


# --------------------------------------------------------------------- #
# section 4: auction calendar
# --------------------------------------------------------------------- #

def run_auctions(manifest_files: dict, files: dict, pull_log: dict,
                 measured_today: str) -> dict:
    window_rows: list[list[dict]] = []
    failed_windows: list[int] = []
    for year in pa.AUCTION_WINDOW_YEARS:
        rel = f"auctions/ta_ws_search_{year}.json"
        ok = fetch_recorded(rel, sub.ta_ws_search_url(year),
                            manifest_files, files, pull_log)
        if not ok:
            failed_windows.append(year)
            continue
        try:
            rows = json.loads(files[rel].decode("utf-8"))
            if not isinstance(rows, list):
                raise ValueError("TA_WS payload not a list")
            window_rows.append(rows)
        except Exception as exc:  # noqa: BLE001 - recorded redacted only
            failed_windows.append(year)
            pull_log[rel]["status"] = "PARSE_BLOCKED"
            pull_log[rel]["error"] = sub.redact(repr(exc))[:200]
    census = sub.auction_census(window_rows, AUCTION_ANN_START,
                                measured_today)
    all_windows = not failed_windows
    floor_pass = (all_windows
                  and census["event_count"] >= AUCTION_FLOOR_EVENTS)
    return {
        "section": "treasury_auction_calendar",
        "source_endpoint": sub.ta_ws_search_url(2018).split("?")[0] +
                           " (per-year search windows, keyless)",
        "windows_pulled": [y for y in pa.AUCTION_WINDOW_YEARS
                           if y not in failed_windows],
        "failed_windows": failed_windows,
        "census_head": {k: v for k, v in census.items() if k != "events"},
        "floor": {
            "name": "auction_calendar_events",
            "definition": (f"official announcement events with "
                           f"announcementDate in [{AUCTION_ANN_START}, "
                           f"{measured_today}] >= {AUCTION_FLOOR_EVENTS}"),
            "measured": census["event_count"],
            "verdict": "PASS" if floor_pass else "FAIL",
        },
        # full per-event evidence kept in the standalone artifact only
        # (keeps p0_gate.json compact); the gate cites the path
        "events_evidence_path": ("research/control/rates_ng1_run/"
                                 "p0_auction_census.json"),
        "census": census,
        "verdict": "PASS" if floor_pass else "FAIL",
    }


# --------------------------------------------------------------------- #
# section 5: canaries + parity + adoption
# --------------------------------------------------------------------- #

def run_canaries(plane: pa.RatesNG1Plane) -> dict:
    canaries = [
        sub.canary_fabricated_curve_date(plane),
        sub.canary_fabricated_tenor(plane),
        sub.canary_never_existed_ticker(),
    ]
    ok = all(c["verdict"] == "REFUSED_AS_EXPECTED" for c in canaries)
    return {"section": "p7_canaries", "canaries": canaries,
            "verdict": "PASS" if ok else "FAIL"}


def run_parity(plane: pa.RatesNG1Plane) -> dict:
    records = plane.shadow_parity(PARITY_PILOT, SCRATCH)
    ok = all(r["digest_identical"] for r in records)
    return {
        "section": "shadow_parity",
        "pilot_entries": list(PARITY_PILOT),
        "records": records,
        "digest_equality_all": ok,
        "verdict": "PASS" if ok else "FAIL",
    }


def run_adoption(plane: pa.RatesNG1Plane) -> dict:
    """consume_via_plane over EVERY frozen entry (adoption law: all
    consumption via the plane; any refusal/drift breaks the gate)."""
    per_entry: dict[str, dict] = {}
    for entry in sorted(pa.FROZEN_CONSUMPTION_SET):
        kind = pa.FROZEN_CONSUMPTION_SET[entry]["kind"]
        try:
            res = plane.consume_via_plane(
                entry, SCRATCH if kind == "curve" else None)
            per_entry[entry] = {
                "verdict": "PASS",
                "sha256": res["sha256_measured"],
                "query_verdict": res["query_verdict"],
            }
        except Exception as exc:  # noqa: BLE001 - recorded redacted only
            per_entry[entry] = {"verdict": "FAIL",
                                "error": sub.redact(repr(exc))[:200]}
    ok = all(r["verdict"] == "PASS" for r in per_entry.values())
    return {
        "section": "platform_adoption_consume_via_plane",
        "frozen_entry_count": len(pa.FROZEN_CONSUMPTION_SET),
        "entries": per_entry,
        "verdict": "PASS" if ok else "FAIL",
    }


# --------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------- #

def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(RAW_ROOT, exist_ok=True)
    pull_log: dict[str, dict] = {}
    manifest_files: dict[str, dict] = {}
    files: dict[str, bytes] = {}

    print("[1/6] Treasury par-yield curve pulls ...", flush=True)
    treasury = run_treasury(manifest_files, files, pull_log)
    print(f"      years={treasury['years_pulled']}/"
          f"{treasury['years_expected']} "
          f"coverage={treasury['census']['coverage_fraction']}", flush=True)

    print("[2/6] FRED granted-set re-pin ...", flush=True)
    fred = run_fred(manifest_files, files, pull_log)
    print(f"      overlap verdict={fred['cpiaucsl_overlap_verify'].get('verdict')}",
          flush=True)

    print("[3/6] EODHD ETP census ...", flush=True)
    etp = run_etp(manifest_files, files, pull_log)
    print("      tickers censored="
          f"{sum(1 for t in etp['tickers'].values() if t.get('status') == 'CENSORED')}",
          flush=True)

    measured_today = now_utc()[:10]
    print("[4/6] Auction calendar census ...", flush=True)
    auctions = run_auctions(manifest_files, files, pull_log, measured_today)
    print(f"      events={auctions['census_head']['event_count']}",
          flush=True)

    # substrate manifest committed AFTER all pulls
    manifest = {
        "schema": "rates_ng1_run/substrate_manifest@1",
        "measured_utc": now_utc(),
        "law": ("raw bytes are machine-local under "
                "research/assets/rates_ng1/raw_substrate/ (untracked); "
                "this committed manifest sha256-pins every file; keys "
                "are redacted from every recorded URL"),
        "files": manifest_files,
        "file_count": len(manifest_files),
    }
    write_json(MANIFEST_PATH, manifest)

    plane = pa.RatesNG1Plane(MANIFEST_PATH, RAW_ROOT)

    print("[5/6] Canaries + adoption + parity ...", flush=True)
    canaries = run_canaries(plane)
    adoption = run_adoption(plane)
    parity = run_parity(plane)
    print(f"      canaries={canaries['verdict']} "
          f"adoption={adoption['verdict']} parity={parity['verdict']}",
          flush=True)

    floors = {
        "F1_treasury_curve_coverage": treasury["floor"],
        "F2_fred_granted_repin": fred["floor"],
        "F3_treasury_etp_census": etp["floor"],
        "F4_auction_calendar_events": auctions["floor"],
    }
    flo_pass = all(f["verdict"] == "PASS" for f in floors.values())
    adoption_pass = (adoption["verdict"] == "PASS"
                     and parity["verdict"] == "PASS"
                     and canaries["verdict"] == "PASS")
    pull_ok = all(v.get("status") == "PULLED" for v in pull_log.values())
    blockers: list[str] = []

    if flo_pass and adoption_pass and pull_ok:
        verdict = "PASS"
    else:
        verdict = "BLOCKED_DATA"
        if not pull_ok:
            blockers.append("one or more bounded pulls FAILED after "
                            "retries (fail-closed, never fabricated)")
        if not flo_pass:
            blockers.append("one or more frozen floors FAILED")
        if not adoption_pass:
            blockers.append("adoption/parity/canaries FAILED")

    gate = {
        "schema": "rates_ng1_run/p0_gate@1",
        "gate": "RATES-NG1-P0",
        "cycle_id": "RATES-NG1",
        "task_id": "rates-ng1-p0-adoption",
        "measured_utc": now_utc(),
        "worktree": WORKTREE,
        "git": git_state(),
        "pull_log": pull_log,
        "floors": floors,
        "sections": {
            "s5_treasury_curve": treasury,
            "s2_fred_repin": fred,
            "etp_census": etp,
            # compact: the full per-event auction census is stored only
            # in p0_auction_census.json (events_evidence_path)
            "auction_census_compact": {
                k: v for k, v in auctions.items() if k != "census"},
            "canaries": canaries,
            "adoption": adoption,
            "shadow_parity": parity,
        },
        "adoption_law": {
            "consume_via_plane": "research/assets/rates_ng1/"
                                 "plane_adapter.py (frozen set -> "
                                 "authority -> digest verify-on-read -> "
                                 "manifest-verified query)",
            "cads_store_mode": "READ-ONLY (inherited CPIAUCSL pin "
                               "resolve only; no new pins written into "
                               "the shared store from this lane)",
        },
        "evidence_paths": {
            "substrate_manifest": "research/control/rates_ng1_run/"
                                  "substrate_manifest.json",
            "gate": "research/control/rates_ng1_run/p0_gate.json",
            "raw_substrate_root": "research/assets/rates_ng1/"
                                  "raw_substrate/ (untracked)",
        },
        "blockers": blockers,
        "verdict": verdict,
    }
    gate_path = os.path.join(OUT_DIR, "p0_gate.json")
    write_json(gate_path, gate)

    # per-section census artifacts (compact evidence; the auction events
    # list is stored once, inside the section artifact)
    write_json(os.path.join(OUT_DIR, "p0_treasury_census.json"), treasury)
    write_json(os.path.join(OUT_DIR, "p0_fred_repin.json"), fred)
    write_json(os.path.join(OUT_DIR, "p0_etp_census.json"), etp)
    write_json(os.path.join(OUT_DIR, "p0_auction_census.json"), auctions)
    write_json(os.path.join(OUT_DIR, "p0_canaries.json"), canaries)
    write_json(os.path.join(OUT_DIR, "p0_shadow_parity.json"), parity)

    print(f"[6/6] p0_gate verdict={verdict} blockers={blockers}",
          flush=True)
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
