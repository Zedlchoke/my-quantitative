#!/usr/bin/env python3
"""COMMODITIES-NG1 P2 Q-6 feasibility measurement runner (NO PnL).

Builds the P2 gate from the P0/P1 frozen substrate ONLY (offline, NO
network):

- CoT weekly report dates: the sha256-pinned P0 canonical surface
  (``cftc/cot_weekly_targets_csv``), consumed digest-verified through
  the P0 plane adapter;
- ETP session calendars: the sha256-pinned ``etp/eod/<SYM>`` surfaces,
  consumed digest-verified through the P0 plane adapter;
- qualifying market-pairs: ``p0_market_pairs.json`` (P0 verdict PASS,
  20 qualifying pairs; the dispatch-declared DBA basket triple earns
  pair credit per the P0 floor rule);
- cost ceilings: the frozen P1 tier-2.0 contract
  ``p1_cost_contract.json`` (constants cited by sha256).

Floors (frozen in the dispatch packet BEFORE measurement; measured
against exactly, fail-closed per lane A4/A5):

- >= 300 grid-eligible weekly decision instants post-2018-01-01 per
  qualifying market-pair after the declared 52-week warmup carve-out;
- >= 90% of expected weekly CoT releases on the window map to a
  measured ETP session on the decision grid.

A pair under any floor is excluded from the bookable set and reported.
NO proposals, NO signal design, NO scoring, NO PnL/outcome numbers.

Output: ``p2_gate.json`` (this run directory).
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, REPO_ROOT)

from research.assets.commodities_ng1 import feasibility as F  # noqa: E402
from research.assets.commodities_ng1.cot_census import (  # noqa: E402
    csv_to_records,
)
from research.assets.commodities_ng1.plane_adapter import (  # noqa: E402
    CommoditiesNG1Plane,
)

RUN_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_SCHEMA = "commodities_ng1_run/p2_gate@1"
TASK_ID = "commodities-ng1-p2-feasibility"

FROZEN_FLOOR_TEXT = (
    "Both lanes (A4/A5): >= 300 grid-eligible weekly decision instants "
    "post-2018-01-01 PER QUALIFYING MARKET-PAIR after a declared "
    "52-week warmup carve-out; AND >= 90% of expected weekly CoT "
    "releases on the window map to a measured ETP session on the "
    "decision grid. A pair under floor is excluded from the bookable "
    "set, reported -- not silently dropped.")

FROZEN_COST_TEXT = (
    "Document worst-case round-trip cost ceiling per pair-leg from "
    "p1_cost_contract.json (CS p90 x 2 fills + expense where MEASURED; "
    "NOT_MEASURED legs explicitly listed; constants cited by sha256; "
    "NO PnL).")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(name: str):
    with open(os.path.join(RUN_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


def measure() -> dict:
    plane = CommoditiesNG1Plane()

    # -- qualifying pairs (P0 authority, frozen) ------------------------ #
    pairs_doc = _load("p0_market_pairs.json")
    if pairs_doc.get("verdict") != "PASS":
        raise F.FeasibilityRefused("p0_market_pairs verdict not PASS")
    qualifying = [p for p in pairs_doc["pairs"] if p["qualifying"]]
    if not qualifying:
        raise F.FeasibilityRefused("zero qualifying market-pairs")

    # -- CoT weekly report dates (plane-consumed, digest-verified) ------ #
    res = plane.resolve_entry("cftc/cot_weekly_targets_csv")
    with open(res["path"], encoding="utf-8") as fh:
        cot_records = csv_to_records(fh.read())
    reports_by_code: dict[str, list[date]] = {}
    for r in cot_records:
        reports_by_code.setdefault(r.contract_market_code,
                                   []).append(r.report_date)

    # -- ETP session calendars (plane-consumed, digest-verified) -------- #
    sessions_by_sym: dict[str, list[date]] = {}
    etp_pins: dict[str, str] = {}
    for sym in sorted({p["etp"] for p in qualifying}):
        eres = plane.resolve_entry(f"etp/eod/{sym}")
        with open(eres["path"], encoding="utf-8") as fh:
            sessions_by_sym[sym] = sorted(
                date.fromisoformat(row["date"])
                for row in csv.DictReader(fh))
        etp_pins[sym] = eres["sha256_pinned"]

    # -- per-pair census + frozen floors -------------------------------- #
    per_pair = {}
    for p in sorted(qualifying, key=lambda q: (q["cot_market_code"],
                                               q["etp"])):
        code, sym = p["cot_market_code"], p["etp"]
        if code not in reports_by_code:
            raise F.FeasibilityRefused(
                f"pair {code}/{sym}: CoT market absent from the pinned "
                "weekly targets surface")
        grid = F.census_pair_grid(reports_by_code[code],
                                  sessions_by_sym[sym])
        floors = F.evaluate_floors(grid)
        per_pair[f"{code}/{sym}"] = {
            "cot_market_code": code,
            "etp": sym,
            "purity": p["purity"],
            "declared_basis": p.get("declared_basis"),
            "etp_session_calendar": {
                "first": sessions_by_sym[sym][0].isoformat(),
                "last": sessions_by_sym[sym][-1].isoformat(),
                "sessions": len(sessions_by_sym[sym]),
                "sha256_pinned": etp_pins[sym],
            },
            "cot_weeks_measured": len(reports_by_code[code]),
            "instants_window": grid["instants_window"],
            "instants_grid_eligible_window": grid["instants_grid_eligible"],
            "unmapped_release_dates_window": grid["unmapped_release_dates"],
            "floor_evaluation": floors,
        }

    bookable = sorted(k for k, v in per_pair.items()
                      if v["floor_evaluation"]["pair_meets_floors"])
    excluded = {
        k: {
            "floor_a_instants": v["floor_evaluation"]["floor_a_instants"],
            "floor_b_coverage": v["floor_evaluation"]["floor_b_coverage"],
        }
        for k, v in per_pair.items()
        if not v["floor_evaluation"]["pair_meets_floors"]}

    # -- cost ceilings from the FROZEN P1 contract ----------------------- #
    contract_path = os.path.join(RUN_DIR, "p1_cost_contract.json")
    contract = _load("p1_cost_contract.json")
    contract_sha = _sha256_file(contract_path)
    fee_sha = _sha256_file(os.path.join(RUN_DIR, "fee_facts.json"))
    legs = contract["per_leg"]
    ceilings = {}
    expense_fail_closed_legs = []
    for key, pp in per_pair.items():
        sym = pp["etp"]
        leg = legs.get(sym)
        if leg is None:
            raise F.FeasibilityRefused(
                f"pair {key}: ETP leg {sym} absent from the frozen P1 "
                "cost contract")
        ceil = F.round_trip_cost_ceiling(leg)
        ceil["cot_market_code"] = pp["cot_market_code"]
        ceil["pair"] = key
        ceil["transaction_bps_full_spread_p90"] = leg[
            "transaction_bps_full_spread_p90"]
        ceil["expense_page_sha256"] = leg["expense_fact"].get("page_sha256")
        ceil["expense_source_url"] = leg["expense_fact"].get("source_url")
        ceilings[key] = ceil
        if ceil["expense_fail_closed"] and sym not in \
                expense_fail_closed_legs:
            expense_fail_closed_legs.append(sym)

    # -- per-lane floor verdicts (identical measured grid; A4/A5) -------- #
    lanes = {}
    for lane in F.LANES:
        lanes[lane] = {
            "bookable_pairs": bookable,
            "bookable_pair_count": len(bookable),
            "excluded_pairs": excluded,
            "floors_met_all_qualifying_pairs": not excluded,
        }

    blocked_paths = []
    for lane, lv in lanes.items():
        if lv["bookable_pair_count"] == 0:
            blocked_paths.append(
                f"lane {lane}: empty bookable set (no qualifying "
                "market-pair meets the frozen floors)")

    census_complete = all(
        v["floor_evaluation"]["counted_expected_releases"] > 0
        for v in per_pair.values())
    verdict = "PASS" if (census_complete and not blocked_paths) else "FAIL"

    items = {
        "item1_decision_grid_census": {
            "verdict": "PASS" if census_complete else "FAIL",
            "values": {
                "qualifying_pairs_measured": len(per_pair),
                "substrate": "plane-consumed digest-verified (NO network)",
                "per_pair_instants_window": {
                    k: v["instants_window"] for k, v in per_pair.items()},
                "per_pair_instants_grid_eligible": {
                    k: v["instants_grid_eligible_window"]
                    for k, v in per_pair.items()},
                "declared_window": {
                    "window_start": F.WINDOW_START.isoformat(),
                    "warmup_carve_out_weeks": F.WARMUP_WEEKS,
                    "warmup_rule": "first 52 window decision instants "
                                   "(ordered by release) are warmup; "
                                   "both floors evaluated on the "
                                   "remaining counted window",
                },
                "release_rule": {
                    "p0_rule_imported": "cot_census.release_instant "
                                        "(single source; used verbatim "
                                        "for Tuesday as-of dates)",
                    "holiday_shift_rule": "measured Monday as-of dates "
                                          "(CFTC holiday-shifted report "
                                          "weeks) take the same "
                                          "week-anchor: Friday 15:30 "
                                          "America/New_York of the "
                                          "Mon-Sun week containing the "
                                          "as-of date; identity with the "
                                          "P0 rule asserted per Tuesday "
                                          "report at census time",
                },
            },
        },
        "item2_release_to_session_coverage": {
            "verdict": "PASS" if census_complete else "FAIL",
            "values": {
                "coverage_floor_frozen": F.COVERAGE_FLOOR,
                "per_pair_coverage": {
                    k: v["floor_evaluation"][
                        "release_to_session_coverage"]
                    for k, v in per_pair.items()},
                "per_pair_unmapped_counted": {
                    k: v["floor_evaluation"][
                        "unmapped_release_dates_counted"]
                    for k, v in per_pair.items()},
                "expected_releases_definition": "every measured weekly "
                    "CoT report of the pair's market whose release "
                    "falls in the counted window (holiday-shifted "
                    "weeks included; never silently dropped)",
            },
        },
        "item3_cost_ceilings": {
            "verdict": "PASS",
            "values": {
                "source": "p1_cost_contract.json (frozen P1 tier-2.0)",
                "source_sha256": contract_sha,
                "fee_facts_sha256": fee_sha,
                "per_pair_leg_ceilings": ceilings,
                "expense_not_measured_legs_fail_closed":
                    sorted(expense_fail_closed_legs),
                "declared_conventions": {
                    "transaction": "2 fills x half_spread_frac_p90 "
                                   "(cost charged exactly once per fill)",
                    "expense": "MEASURED_OFFICIAL_PAGE expense_ratio_annual "
                               "accrued linearly over the declared "
                               f"{F.CEILING_HORIZON_TRADING_DAYS}-trading-"
                               "day worst-case horizon; annual rate "
                               "reported alongside (horizon-linear)",
                    "not_measured": "transaction-only ceiling + explicit "
                                    "fail-closed listing; downstream "
                                    "lanes treat conservatively or "
                                    "exclude",
                },
                "no_pnl": "cost documentation only; no PnL/outcome "
                          "numbers anywhere in this gate",
            },
        },
        "item4_frozen_floor_reconciliation": {
            "verdict": verdict,
            "values": {
                "frozen_floors_text": FROZEN_FLOOR_TEXT,
                "declared_before_measurement": True,
                "per_lane": lanes,
                "qualifying_pairs_under_floor_excluded": sorted(excluded),
                "blocked_paths": blocked_paths,
            },
        },
    }

    gate = {
        "schema": GATE_SCHEMA,
        "cycle_id": "COMMODITIES-NG1",
        "lane": "p2-feasibility (lanes A4/A5 Q-6 floors)",
        "task_id": TASK_ID,
        "measured_utc": _utc_now(),
        "final_verdict": verdict,
        "final_why": (
            "Q-6 feasibility measured fail-closed on the frozen "
            "substrate for all 20 qualifying market-pairs; bookable "
            f"set = {len(bookable)} pairs; frozen floors met on the "
            "declared window" if verdict == "PASS"
            else "see item4 blocked_paths / failing items"),
        "frozen_floors": {
            "instants": {"floor": F.INSTANT_FLOOR, "window_start":
                         F.WINDOW_START.isoformat(),
                         "warmup_carve_out_weeks": F.WARMUP_WEEKS},
            "coverage": {"floor": F.COVERAGE_FLOOR},
            "text": FROZEN_FLOOR_TEXT,
            "cost_ceiling_text": FROZEN_COST_TEXT,
            "declared_before_measurement": True,
            "source": "dispatch packet commodities-ng1-p2-feasibility "
                      "(frozen in the task objective)",
        },
        "items": items,
        "per_pair_census": per_pair,
        "substrate_pins": {
            "cot_weekly_targets_csv_sha256": res["sha256_pinned"],
            "etp_eod_sha256": etp_pins,
            "p1_cost_contract_sha256": contract_sha,
            "fee_facts_sha256": fee_sha,
        },
        "test_command": (
            "cd /Users/hoangminhlong/my-quantitative/"
            ".worktrees/commodities-ng1/integration && "
            "/Users/hoangminhlong/my-quantitative/.venv/bin/python "
            "-m pytest tests/test_commodities_ng1_p2.py -q"),
    }
    return gate


def main() -> int:
    gate = measure()
    out = os.path.join(RUN_DIR, "p2_gate.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, indent=2, sort_keys=False)
        fh.write("\n")
    lanes = gate["items"]["item4_frozen_floor_reconciliation"]["values"][
        "per_lane"]
    print(json.dumps({
        "gate": "p2_gate.json",
        "final_verdict": gate["final_verdict"],
        "qualifying_pairs_measured":
            gate["items"]["item1_decision_grid_census"]["values"][
                "qualifying_pairs_measured"],
        "bookable_pair_count_A4": lanes["A4"]["bookable_pair_count"],
        "bookable_pair_count_A5": lanes["A5"]["bookable_pair_count"],
        "expense_not_measured_legs":
            gate["items"]["item3_cost_ceilings"]["values"][
                "expense_not_measured_legs_fail_closed"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
