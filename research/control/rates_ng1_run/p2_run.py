"""RATES-NG1 P2 feasibility run: Q-6 census (no-PnL).

Dispatch: rates-ng1-p2-feasibility (cycle RATES-NG1, P2).  This run:

1. consumes the frozen substrate STRICTLY via the plane adapter
   (verify-on-read re-hash against the committed substrate manifest on
   every consumption; NO network access of any kind in P2);
2. builds the A5 common decision-grid census: official curve-CSV dates
   x all-four-leg ETP EOD dates, post-2018-01-01, the DECLARED
   252-trading-day warmup carve-out applied, bookable 16:00-NY decision
   instants per the P1 clock, and the weekday-grid coverage fraction;
3. re-verifies the auction census from the RAW pinned TA_WS windows and
   maps every P0 event through the P1 PIT later-bound law (end of the
   announced NY day; same-day close refused) onto the common grid;
4. documents the projected worst-case round-trip cost ceiling per leg
   from the FROZEN tier-2.0 P1 cost contract (constants cited by the
   contract sha256; declared holding convention; COST PROJECTION ONLY
   -- no PnL, no expectancy, no outcome number);
5. runs the P2 pytest file and records the exact command + exit code;
6. writes p2_gate.json (per-floor frozen-vs-measured, verdicts, and
   the per-lane BLOCKED path; fail-closed) plus two committed census
   sidecar artifacts whose sha256 pins live in the gate.

Frozen floors (declared in the dispatch packet BEFORE measurement):
A5 >= 1500 bookable instants post-2018-01-01 after the 252-session
warmup carve-out AND coverage >= 90% of common NY business days
2018-01-01..2026-09-11; A4 >= 150 grid-eligible auction events.  A lane
under its floor is BLOCKED (dies cheap; no D1 dispatch for that lane).
"""

from __future__ import annotations

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

from research.assets.rates_ng1 import feasibility as fz  # noqa: E402
from research.assets.rates_ng1 import plane_adapter as pa  # noqa: E402
from research.assets.rates_ng1 import substrate as sub  # noqa: E402

SCHEMA = "rates_ng1_run/p2_gate@1"
RUN_DIR = os.path.dirname(os.path.abspath(__file__))
CONTRACT_PATH = os.path.join(RUN_DIR, "p1_cost_contract.json")
GATE_PATH = os.path.join(RUN_DIR, "p2_gate.json")
GRID_SIDECAR_PATH = os.path.join(RUN_DIR, "p2_grid_census.json")
AUCTION_SIDECAR_PATH = os.path.join(RUN_DIR, "p2_auction_eligibility.json")
TEST_FILE = os.path.join(REPO_ROOT, "tests", "test_rates_ng1_p2.py")
P0_AUCTION_CENSUS_PATH = os.path.join(RUN_DIR, "p0_auction_census.json")

#: P0 auction census window (replicated EXACTLY for the re-verification).
AUCTION_ANN_WINDOW = ("2018-01-01", "2026-09-12")

FROZEN_FLOORS = {
    "A5_F1_bookable_decision_instants": {
        "lane": "A5_curve_shape",
        "frozen": fz.MIN_BOOKABLE_INSTANTS,
        "operator": ">=",
        "definition": "bookable daily decision instants post-2018-01-01 "
                      "on the common curve-CSV x ETP-EOD grid AFTER the "
                      "declared 252-trading-day warmup carve-out",
    },
    "A5_F2_common_grid_coverage": {
        "lane": "A5_curve_shape",
        "frozen": fz.MIN_GRID_COVERAGE_FRACTION,
        "operator": ">=",
        "definition": "grid coverage of common NY business days "
                      "(Mon-Fri weekday grid, P0 disclosed convention) "
                      "2018-01-01..2026-09-11",
    },
    "A4_F1_grid_eligible_auction_events": {
        "lane": "A4_auction_clock",
        "frozen": fz.MIN_GRID_ELIGIBLE_AUCTION_EVENTS,
        "operator": ">=",
        "definition": "grid-eligible auction announcement events "
                      "post-2018-01-01 after PIT later-bound mapping "
                      "(end-of-announced-NY-day conservative bound; "
                      "same-day close refused)",
    },
}

BLOCKED_PATH_BY_LANE = {
    "A5_curve_shape": "lane A5 dies cheap: no D1 blind-proposal dispatch "
                      "for this lane; the cycle proceeds per plan section "
                      "4 (P2 'lane dies cheap if under floor')",
    "A4_auction_clock": "lane A4 dies cheap: no D1 blind-proposal "
                        "dispatch for this lane; the cycle proceeds per "
                        "plan section 4 (P2 'lane dies cheap if under "
                        "floor')",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", REPO_ROOT, *args],
                          capture_output=True, text=True,
                          check=True).stdout.strip()


def build_grid_census(plane: pa.RatesNG1Plane) -> tuple[dict, list[str]]:
    """Work item 1: the decision-grid census on the plane-frozen
    substrate (verify-on-read; no network)."""
    curve_dates: set[str] = set()
    curve_digests: dict[str, str] = {}
    for year in range(2018, 2027):
        entry = f"treasury_curve/par_yields_{year}.csv"
        res = plane.consume_via_plane(entry)
        curve_digests[entry] = res["sha256_measured"]
        curve_dates |= {r["date"] for r in res["rows"] or []}
    etp_dates: dict[str, set[str]] = {}
    etp_digests: dict[str, str] = {}
    etp_windows: dict[str, list[str]] = {}
    for ticker in pa.ETP_TICKERS:
        rows = plane.etp_rows(ticker)
        entry = f"etp_eod/{ticker}.US.json"
        etp_digests[entry] = plane.consume_via_plane(entry)["sha256_measured"]
        etp_dates[ticker] = {str(r["date"]) for r in rows}
        etp_windows[ticker] = [min(etp_dates[ticker]),
                               max(etp_dates[ticker])]
    grid = fz.build_common_grid(curve_dates, etp_dates)
    census = fz.grid_census(grid, warmup_sessions=fz.WARMUP_SESSIONS,
                            window=fz.FEASIBILITY_WINDOW)
    provenance = {
        "adapter": "research/assets/rates_ng1/plane_adapter.py "
                   "(consume_via_plane, verify-on-read re-hash)",
        "network_access": "NONE (frozen substrate only)",
        "curve_entries_consumed": sorted(curve_digests),
        "curve_digests": curve_digests,
        "etp_digests": etp_digests,
        "etp_windows_full_series": etp_windows,
        "common_grid_definition": "dates with an official curve-CSV row "
                                  "AND an EOD bar for ALL FOUR frozen "
                                  "legs (TLT/IEF/IEI/SHY), restricted to "
                                  "the window",
    }
    return census, provenance


def rebuild_auction_census(plane: pa.RatesNG1Plane) -> tuple[dict, dict]:
    """Work item 2: re-verify the auction census from the RAW pinned
    TA_WS windows (digest-verified on read) and cross-check against the
    committed P0 census artifact."""
    window_rows: list[list[dict]] = []
    digests: dict[str, str] = {}
    for year in pa.AUCTION_WINDOW_YEARS:
        entry = f"auctions/ta_ws_search_{year}.json"
        res = plane.consume_via_plane(entry)
        digests[entry] = res["sha256_measured"]
        payload = json.loads(
            plane._raw_bytes(plane.raw_path(entry)).decode("utf-8"))
        window_rows.append(payload)
    census = sub.auction_census(window_rows, AUCTION_ANN_WINDOW[0],
                                AUCTION_ANN_WINDOW[1])
    with open(P0_AUCTION_CENSUS_PATH, "r", encoding="utf-8") as fh:
        committed = json.load(fh)
    cross_check = {
        "reverified_event_count": census["event_count"],
        "committed_p0_event_count":
            committed["census"]["event_count"],
        "counts_match": (census["event_count"]
                         == committed["census"]["event_count"]),
        "committed_p0_artifact": os.path.relpath(
            P0_AUCTION_CENSUS_PATH, REPO_ROOT),
        "window_replicated": list(AUCTION_ANN_WINDOW),
    }
    if not cross_check["counts_match"]:
        raise RuntimeError(
            "auction census re-verification disagrees with the committed "
            f"P0 artifact ({census['event_count']} vs "
            f"{committed['census']['event_count']}): fail-closed")
    return census, {"auction_digests": digests,
                    "cross_check": cross_check}


def run_p2_tests() -> dict:
    cmd = [sys.executable, "-m", "pytest", "-q", TEST_FILE]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True,
                          text=True, timeout=1800)
    tail = (proc.stdout.strip().splitlines() or [""])[-1]
    return {
        "command": f"cd {REPO_ROOT} && {sys.executable} -m pytest "
                   "tests/test_rates_ng1_p2.py -q",
        "exit_code": proc.returncode,
        "summary_tail": tail,
        "verdict": "PASS" if proc.returncode == 0 else "FAIL",
    }


def main() -> int:
    measured_utc = _now_utc()
    head = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    print(f"[p2] worktree={REPO_ROOT}")
    print(f"[p2] branch={branch} head={head}")
    print(f"[p2] measured_utc={measured_utc}")

    plane = pa.RatesNG1Plane()

    # -- work item 1: decision-grid census ----------------------------- #
    grid_census, grid_provenance = build_grid_census(plane)
    grid_sidecar = {
        "schema": "rates_ng1_run/p2_grid_census@1",
        "cycle_id": "RATES-NG1",
        "task_id": "rates-ng1-p2-feasibility",
        "measured_utc": measured_utc,
        "frozen_floors": {
            "min_bookable_instants": fz.MIN_BOOKABLE_INSTANTS,
            "min_grid_coverage_fraction": fz.MIN_GRID_COVERAGE_FRACTION,
            "warmup_sessions": fz.WARMUP_SESSIONS,
            "window": list(fz.FEASIBILITY_WINDOW),
        },
        "provenance": grid_provenance,
        "census": grid_census,
    }
    with open(GRID_SIDECAR_PATH, "w", encoding="utf-8") as fh:
        json.dump(grid_sidecar, fh, indent=1, sort_keys=True)
    grid_sha = _sha256_file(GRID_SIDECAR_PATH)
    print(f"[p2] grid: sessions={grid_census['grid_session_count']} "
          f"bookable={grid_census['bookable_count']} "
          f"coverage={grid_census['coverage_fraction']}")

    # -- work item 2: auction grid-eligibility re-verification --------- #
    auction_census, auction_provenance = rebuild_auction_census(plane)
    eligibility = fz.auction_grid_eligibility(
        auction_census["events"], grid_census["grid_dates"])
    auction_sidecar = {
        "schema": "rates_ng1_run/p2_auction_eligibility@1",
        "cycle_id": "RATES-NG1",
        "task_id": "rates-ng1-p2-feasibility",
        "measured_utc": measured_utc,
        "frozen_floor": {
            "min_grid_eligible_events":
                fz.MIN_GRID_ELIGIBLE_AUCTION_EVENTS,
            "pit_law": "end-of-announced-NY-day conservative LATER "
                       "bound; the same-day close is refused (P1 clock "
                       "semantics)",
        },
        "provenance": auction_provenance,
        "census_headline": {
            k: auction_census[k] for k in
            ("announcement_window", "event_count",
             "events_by_security_type", "first_announcement",
             "last_announcement")},
        "eligibility_headline": {
            k: eligibility[k] for k in
            ("events_total", "eligible_count", "ineligible_count",
             "eligible_by_security_type", "first_eligible_decision_session",
             "last_eligible_decision_session",
             "clock_authority_cross_check")},
        "mappings": eligibility["mappings"],
    }
    with open(AUCTION_SIDECAR_PATH, "w", encoding="utf-8") as fh:
        json.dump(auction_sidecar, fh, indent=1, sort_keys=True)
    auction_sha = _sha256_file(AUCTION_SIDECAR_PATH)
    print(f"[p2] auction: total={eligibility['events_total']} "
          f"eligible={eligibility['eligible_count']} "
          f"ineligible={eligibility['ineligible_count']}")

    # -- work item 3: cost ceilings from the FROZEN contract ----------- #
    contract_sha = _sha256_file(CONTRACT_PATH)
    with open(CONTRACT_PATH, "r", encoding="utf-8") as fh:
        contract = json.load(fh)
    ceilings = fz.round_trip_cost_ceilings(contract)
    ceilings["contract"] = {
        "path": os.path.relpath(CONTRACT_PATH, REPO_ROOT),
        "sha256": contract_sha,
        "cost_ladder_tier": contract["cost_ladder_tier"],
        "cost_frequency": contract["cost_frequency"],
        "stress_tier_quantile": contract["stress_tier"]["quantile"],
        "constants_cited_by_sha256": True,
    }
    for t, v in ceilings["per_leg"].items():
        ceiling = v["worst_case_round_trip_ceiling_bps"]
        spread = v["round_trip_spread_bps"]
        drag = v["er_drag_round_trip_bps"]
        print(f"[p2] ceiling {t}: {ceiling:.4f} bps "
              f"(spread {spread:.4f} + ER drag {drag:.4f})")

    # -- floors (frozen-vs-measured, fail-closed per lane) -------------- #
    measured = {
        "A5_F1_bookable_decision_instants": {
            "measured": grid_census["bookable_count"],
            "pass": grid_census["bookable_count"]
                    >= fz.MIN_BOOKABLE_INSTANTS,
            "detail": {
                "grid_session_count": grid_census["grid_session_count"],
                "warmup_sessions": fz.WARMUP_SESSIONS,
                "first_decision_session":
                    grid_census["first_decision_session"],
                "last_decision_session":
                    grid_census["grid_dates"][-1],
            },
        },
        "A5_F2_common_grid_coverage": {
            "measured": grid_census["coverage_fraction"],
            "pass": grid_census["coverage_fraction"]
                    >= fz.MIN_GRID_COVERAGE_FRACTION,
            "detail": {
                "covered_weekdays": grid_census["covered_weekdays"],
                "expected_weekdays_window":
                    grid_census["expected_weekdays_window"],
                "convention": "Mon-Fri weekday grid (P0 disclosed "
                              "convention; holidays not enumerated)",
            },
        },
        "A4_F1_grid_eligible_auction_events": {
            "measured": eligibility["eligible_count"],
            "pass": eligibility["eligible_count"]
                    >= fz.MIN_GRID_ELIGIBLE_AUCTION_EVENTS,
            "detail": {
                "events_total": eligibility["events_total"],
                "ineligible_count": eligibility["ineligible_count"],
                "p0_raw_census_reverified":
                    auction_provenance["cross_check"][
                        "reverified_event_count"],
            },
        },
    }
    floors: dict[str, dict] = {}
    for name, frozen in FROZEN_FLOORS.items():
        m = measured[name]
        floors[name] = {
            "name": name,
            "lane": frozen["lane"],
            "frozen": frozen["frozen"],
            "operator": frozen["operator"],
            "definition": frozen["definition"],
            "measured": m["measured"],
            "detail": m["detail"],
            "verdict": "PASS" if m["pass"] else "BLOCKED_LANE",
        }
    lanes = {}
    for lane in ("A5_curve_shape", "A4_auction_clock"):
        lane_floors = [f for f in floors.values() if f["lane"] == lane]
        feasible = all(f["verdict"] == "PASS" for f in lane_floors)
        lanes[lane] = {
            "floors": [f["name"] for f in lane_floors],
            "feasibility": "FEASIBLE" if feasible else "BLOCKED",
            "blocked_path": None if feasible
            else BLOCKED_PATH_BY_LANE[lane],
        }

    lane_a5 = lanes["A5_curve_shape"]["feasibility"]
    lane_a4 = lanes["A4_auction_clock"]["feasibility"]
    if lane_a5 == "FEASIBLE" and lane_a4 == "FEASIBLE":
        verdict = "PASS"
    elif lane_a5 == "BLOCKED" and lane_a4 == "BLOCKED":
        verdict = "BLOCKED_BOTH_LANES"
    elif lane_a5 == "BLOCKED":
        verdict = "BLOCKED_LANE_A5"
    else:
        verdict = "BLOCKED_LANE_A4"
    blockers = [k for k, v in floors.items() if v["verdict"] != "PASS"]

    # The gate is written BEFORE the test run so the pytest file can
    # check the committed artifacts (gate + sidecars) in-run; the test
    # row is then updated in place with the exact command + exit code.
    tests: dict = {"status": "PENDING_RUN_ARTIFACTS_PRESENT"}

    gate = {
        "schema": SCHEMA,
        "gate": "RATES-NG1-P2",
        "cycle_id": "RATES-NG1",
        "task_id": "rates-ng1-p2-feasibility",
        "phase_objective": "Q-6 feasibility, NO PnL: census floors only; "
                           "no proposals, no signal design, no scoring, "
                           "no outcome numbers anywhere in this gate",
        "measured_utc": measured_utc,
        "worktree": REPO_ROOT,
        "git": {"branch": branch, "head_sha": head},
        "floors": floors,
        "frozen_floor_provenance": {
            "declared": "dispatch packet rates-ng1-p2-feasibility, "
                        "BEFORE measurement",
            "floor_values": {k: v["frozen"]
                             for k, v in FROZEN_FLOORS.items()},
            "warmup_carveout_sessions": fz.WARMUP_SESSIONS,
        },
        "lanes": lanes,
        "cost_ceilings": ceilings,
        "census_artifacts": {
            "grid_census": {
                "path": os.path.relpath(GRID_SIDECAR_PATH, REPO_ROOT),
                "sha256": grid_sha,
                "bookable_count": grid_census["bookable_count"],
                "grid_session_count": grid_census["grid_session_count"],
                "coverage_fraction": grid_census["coverage_fraction"],
            },
            "auction_eligibility": {
                "path": os.path.relpath(AUCTION_SIDECAR_PATH, REPO_ROOT),
                "sha256": auction_sha,
                "events_total": eligibility["events_total"],
                "eligible_count": eligibility["eligible_count"],
            },
        },
        "tests": tests,
        "evidence_paths": {
            "gate": os.path.relpath(GATE_PATH, REPO_ROOT),
            "grid_census": os.path.relpath(GRID_SIDECAR_PATH, REPO_ROOT),
            "auction_eligibility": os.path.relpath(AUCTION_SIDECAR_PATH,
                                                   REPO_ROOT),
            "p1_cost_contract": os.path.relpath(CONTRACT_PATH, REPO_ROOT),
            "p0_auction_census": os.path.relpath(P0_AUCTION_CENSUS_PATH,
                                                 REPO_ROOT),
            "tests": "tests/test_rates_ng1_p2.py",
        },
        "blockers": blockers,
        "verdict": verdict,
    }
    with open(GATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, indent=1, sort_keys=True)
    print(f"[p2] gate written (pre-test): {GATE_PATH}")

    # -- P2 pytest run (gate + sidecars are on disk for the artifact
    #    checks); the gate's test row is then updated in place.
    tests = run_p2_tests()
    print(f"[p2] tests: {tests['exit_code']} ({tests['summary_tail']})")
    if tests["verdict"] != "PASS":
        blockers.append("P2_tests")
    gate["tests"] = tests
    gate["blockers"] = blockers
    if "P2_tests" in blockers and verdict == "PASS":
        gate["verdict"] = "FAIL_TESTS"
    with open(GATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, indent=1, sort_keys=True)
    print(f"[p2] gate finalized: {GATE_PATH}")
    for k, v in floors.items():
        print(f"[p2] {k}: frozen {v['frozen']} {v['operator']} measured "
              f"{v['measured']} -> {v['verdict']}")
    print(f"[p2] lanes: A5={lane_a5} A4={lane_a4}")
    print(f"[p2] VERDICT: {gate['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
