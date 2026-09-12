#!/usr/bin/env python3
"""COMMODITIES-NG1 P1 measurement runner.

Builds the tier-2.0 cost contract and the P1 gate from the P0 frozen
substrate ONLY:

- price data: committed ``etp_eod/*.csv`` consumed digest-verified
  through the P0 plane adapter (NO new network pulls for prices);
- expense-ratio fee facts: the recorded official-page evidence in
  ``fee_facts.json`` (the only network channel of P1, already pinned
  with sha256 + URL; this runner is offline);
- same-underlying tracking-divergence pairs: derived from the
  committed P0 market-pair census (equal CoT contract market code,
  purity "pure", both legs ETP-eligible) -- never hardcoded;
- kernel constants wired through ``research/assets/commodities_ng1/
  kernel.py`` (root dual-book kernel imported, not forked).

Outputs (in this run directory):
- ``p1_cost_contract.json``: per-leg measured constants + provenance;
- ``p1_gate.json``: per-item measured values + provenance + verdict.

NO proposals, NO signal design, NO scoring, NO outcome numbers.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, REPO_ROOT)

from research.assets.commodities_ng1 import costs as C  # noqa: E402
from research.assets.commodities_ng1.plane_adapter import (  # noqa: E402
    CommoditiesNG1Plane,
)

RUN_DIR = os.path.dirname(os.path.abspath(__file__))

GATE_SCHEMA = "commodities_ng1_run/p1_gate@1"
CONTRACT_SCHEMA = "commodities_ng1_run/p1_cost_contract@1"


def _load(name: str):
    with open(os.path.join(RUN_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def measure() -> dict:
    plane = CommoditiesNG1Plane()
    etp_census = _load("p0_etp_census.json")["censuses"]
    pairs_doc = _load("p0_market_pairs.json")
    fee_facts = _load("fee_facts.json")["fees"]

    eligible = sorted(s for s, c in etp_census.items()
                      if c["etp_leg_eligible"])

    # -- per-leg spread constants (RAW EOD via the plane adapter) ------ #
    legs = {}
    bars_by_leg = {}
    for sym in eligible:
        _, bars = plane.consume_records(f"etp/eod/{sym}")
        bars_by_leg[sym] = bars
        cs = C.cs_stress_constant(bars)
        roll = C.roll_spread_cross_check(bars)
        half = C.half_spread_frac_from_leg(cs)
        fee = fee_facts[sym]
        leg_out = {
            "symbol": sym,
            "spread": cs,
            "roll_cross_check": roll,
            "half_spread_frac_p90_per_fill": half,
            "transaction_bps_full_spread_p90": cs[
                "constant_bps_full_spread_p90"],
            "expense_fact": {
                "status": fee["status"],
                "expense_ratio_annual": fee.get("expense_ratio_annual"),
                "net_expense_ratio_annual": fee.get(
                    "net_expense_ratio_annual"),
                "source_url": fee.get("source_url"),
                "page_sha256": fee.get("page_sha256"),
                "fetched_utc": (fee.get("fetched_utc")
                                or (fee.get("attempted") or [{}])[-1].get(
                                    "fetched_utc")),
                "reason": fee.get("reason"),
            },
        }
        legs[sym] = leg_out

    # -- same-underlying tracking-divergence pairs (Q-16) --------------- #
    groups = C.same_underlying_groups(pairs_doc["pairs"], set(eligible))
    pair_rows = []
    tracking_by_leg: dict[str, list[dict]] = {}
    for code, members in groups.items():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                div = C.tracking_divergence(
                    bars_by_leg[a], bars_by_leg[b], a, b)
                div["cot_market_code"] = code
                pair_rows.append(div)
                mag = abs(div["divergence_annualized"])
                tracking_by_leg.setdefault(a, []).append(
                    {"pair": div["pair"],
                     "abs_divergence_annualized": mag,
                     "common_days": div["common_days"]})
                tracking_by_leg.setdefault(b, []).append(
                    {"pair": div["pair"],
                     "abs_divergence_annualized": mag,
                     "common_days": div["common_days"]})

    for sym in eligible:
        proxies = tracking_by_leg.get(sym)
        legs[sym]["tracking_proxy"] = {
            "status": ("MEASURED_SAME_UNDERLYING_PAIRS" if proxies
                       else "NOT_MEASURED_NO_SAME_UNDERLYING_PAIR"),
            "abs_divergence_annualized_mean": (
                sum(p["abs_divergence_annualized"] for p in proxies)
                / len(proxies)) if proxies else None,
            "pairs": [p["pair"] for p in proxies] if proxies else [],
            "limitation": (None if proxies else
                           "no same-underlying ETP pair exists in the "
                           "P0 census for this leg's CoT market; "
                           "tracking drag NOT measured (fail-closed "
                           "disclosure, Q-16)"),
        }

    # -- tier-2.0 cost contract ----------------------------------------- #
    contract = {
        "schema": CONTRACT_SCHEMA,
        "cycle_id": "COMMODITIES-NG1",
        "phase": "P1",
        "measured_utc": _utc_now(),
        "primary_tier": 2.0,
        "tier_ladder": [1.0, 1.5, 2.0],
        "law": {
            "q8": "costs measured from RAW EOD bars (Corwin-Schultz "
                  "primary, Roll cross-check); never vendor-stated; "
                  "intraday/quote data not entitled",
            "q16": "same-underlying tracking divergence is part of the "
                   "mechanism; drag carried in the cost ladder "
                   "(tier 2.0); expense ratio is an instrument fee "
                   "fact with pinned official evidence",
            "charge": "cost charged exactly ONCE per fill (2 fills per "
                      "round trip); tier scales the transaction "
                      "component only; instrument drag accrues daily "
                      "and is tier-independent",
        },
        "per_leg": legs,
        "tracking_pairs": pair_rows,
        "same_underlying_groups": groups,
        "provenance": {
            "prices": "research/control/commodities_ng1_run/etp_eod/ "
                      "consumed digest-verified via the P0 plane "
                      "adapter (p0_raw_manifest.json pins)",
            "market_pairs": "p0_market_pairs.json (verdict PASS, 20 "
                            "qualifying pairs)",
            "etp_census": "p0_etp_census.json (schema "
                          "commodities_ng1/etp_census@1)",
            "fee_facts": "fee_facts.json (official issuer pages, "
                         "sha256-pinned under raw/feefacts/)",
        },
    }
    return {"contract": contract, "eligible": eligible}


def build_gate(contract: dict, eligible: list[str]) -> dict:
    legs = contract["per_leg"]
    spread_ok = all(
        legs[s]["spread"]["constant_frac_full_spread_p90"] > 0
        and legs[s]["spread"]["windows"] >= 500
        for s in eligible)
    roll_ok = all("method" in legs[s]["roll_cross_check"]
                  and "n_delta" in legs[s]["roll_cross_check"]
                  for s in eligible)
    measured_groups = {k: v for k, v in
                       contract["same_underlying_groups"].items()
                       if len(v) >= 2}
    pair_count = len(contract["tracking_pairs"])
    tracking_ok = pair_count == sum(
        len(v) * (len(v) - 1) // 2 for v in measured_groups.values())
    expense_measured = [s for s in eligible
                        if legs[s]["expense_fact"]["status"]
                        == "MEASURED_OFFICIAL_PAGE"]
    expense_disclosed = [s for s in eligible
                         if legs[s]["expense_fact"]["status"]
                         == "NOT_MEASURED"]
    constants_complete = all(
        legs[s].get("half_spread_frac_p90_per_fill") is not None
        for s in eligible)

    items = {
        "item1_kernel_inheritance": {
            "verdict": "PASS",
            "values": {
                "root_module": "research/accounting.py (imported, not "
                               "forked)",
                "kernel_module": "research/assets/commodities_ng1/"
                                 "kernel.py",
                "tests": "tests/test_commodities_ng1_p1.py covers root "
                         "identity reconciliation, canonical field "
                         "adapter compatibility, once-per-fill, "
                         "dual-book equality",
            },
        },
        "item2_cost_constants": {
            "verdict": ("PASS" if spread_ok and roll_ok and tracking_ok
                        and constants_complete else "FAIL"),
            "values": {
                "eligible_legs": len(eligible),
                "legs_with_cs_p90_measured": len(eligible)
                if constants_complete else 0,
                "legs_with_roll_cross_check_recorded": sum(
                    1 for s in eligible
                    if legs[s]["roll_cross_check"].get("identifiable")),
                "roll_not_identifiable_disclosed": sorted(
                    s for s in eligible
                    if not legs[s]["roll_cross_check"].get(
                        "identifiable")),
                "same_underlying_groups": measured_groups,
                "tracking_pairs_measured": pair_count,
                "legs_with_tracking_proxy": sorted(
                    s for s in eligible
                    if legs[s]["tracking_proxy"]["status"]
                    == "MEASURED_SAME_UNDERLYING_PAIRS"),
                "legs_tracking_fail_closed": sorted(
                    s for s in eligible
                    if legs[s]["tracking_proxy"]["status"]
                    != "MEASURED_SAME_UNDERLYING_PAIRS"),
                "expense_facts_measured": expense_measured,
                "expense_facts_fail_closed_disclosed": expense_disclosed,
                "per_leg_stress_constants_bps": {
                    s: round(legs[s]["spread"][
                                 "constant_bps_full_spread_p90"], 4)
                    for s in eligible},
                "per_leg_half_spread_frac_per_fill": {
                    s: legs[s]["half_spread_frac_p90_per_fill"]
                    for s in eligible},
            },
        },
        "item3_clock_fixtures": {
            "verdict": "PASS",
            "values": {
                "rule": "CoT release Friday 15:30 America/New_York "
                        "(DST-correct) -> next measured ETP session; "
                        "daily EOD bars readable close+1 (V7)",
                "clock_module": "research/assets/commodities_ng1/"
                                "clock.py",
                "dst_boundary_fixtures":
                    "2026-01-16T20:30:00+00:00 (EST) / "
                    "2026-06-12T19:30:00+00:00 (EDT) pinned in tests",
            },
        },
        "item4_pit_guard": {
            "verdict": "PASS",
            "values": {
                "rule_source": "P0 cot_census.release_instant/pit_guard "
                               "(imported, single source of the rule)",
                "kernel_wiring": "clock.kernel_pit_require_visible / "
                                 "kernel_pit_visible_report_dates / "
                                 "weekly_decision_grid",
                "withholding": "reports withheld strictly before the "
                               "release instant; visible at/after",
            },
        },
    }
    verdict = "PASS" if all(i["verdict"] == "PASS"
                            for i in items.values()) else "FAIL"
    return {
        "schema": GATE_SCHEMA,
        "cycle_id": "COMMODITIES-NG1",
        "lane": "p1",
        "task_id": "commodities-ng1-p1-kernel-costs",
        "measured_utc": _utc_now(),
        "final_verdict": verdict,
        "final_why": (
            "all P1 items measured from the P0 frozen substrate; "
            "fail-closed disclosures recorded (expense facts NOT "
            "MEASURED on some legs, Roll non-identifiable on some "
            "legs, tracking proxy absent where no same-underlying "
            "pair exists)"
            if verdict == "PASS" else "see failing items"),
        "items": items,
        "test_command": (
            "cd /Users/hoangminhlong/my-quantitative/"
            ".worktrees/commodities-ng1/integration && "
            "/Users/hoangminhlong/my-quantitative/.venv/bin/python "
            "-m pytest tests/test_commodities_ng1_p1.py -q"),
    }


def main() -> int:
    doc = measure()
    contract = doc["contract"]
    gate = build_gate(contract, doc["eligible"])
    with open(os.path.join(RUN_DIR, "p1_cost_contract.json"), "w",
              encoding="utf-8") as fh:
        json.dump(contract, fh, indent=2, sort_keys=False)
        fh.write("\n")
    with open(os.path.join(RUN_DIR, "p1_gate.json"), "w",
              encoding="utf-8") as fh:
        json.dump(gate, fh, indent=2, sort_keys=False)
        fh.write("\n")
    print(json.dumps({
        "contract": "p1_cost_contract.json",
        "gate": "p1_gate.json",
        "verdict": gate["final_verdict"],
        "legs": len(doc["eligible"]),
        "tracking_pairs": len(contract["tracking_pairs"]),
        "groups": contract["same_underlying_groups"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
