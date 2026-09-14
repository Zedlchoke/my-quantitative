"""COMMODITIES-NG1 I-phase ``--dry-run-plumbing`` self-check.

STRUCTURAL PLUMBING ONLY -- the I-phase law: real-substrate access is
limited to digests, counts and config assembly.  This module NEVER
computes a PnL, return, expectancy or edge; its output schema is
scanned for outcome vocabulary and refuses to emit any such key
(fail-closed).

What it verifies (all structural):

1. config assembly: the 3 booked arms are consumed VERBATIM from the
   binding S freeze; every ``arm_config_digest`` is recomputed
   (sha256 of the UTF-8 canonical JSON, sort_keys=True,
   separators=(',',':')) and must equal the recorded digest; digests
   pairwise distinct; 3 of 6 budget cells booked, 3 unbooked (never
   padded);
2. substrate digests: CoT archives consumed through the P0 plane
   adapter (authority verdict GRANTED + sha256 digest verification);
   only the measured digest identities are reported;
3. chain plumbing: per bookable pair, the weekly chain builds and the
   counted-window STRUCTURE is asserted against the committed P2
   per-pair floor evaluation (counted releases, grid-eligible
   instants, first/last counted release, unmapped releases);
4. decision-series structural counts: per arm, chain rows, counted
   instants, and held/flat decision counts -- COUNTS ONLY.

Run modes:

- ``python -m
  research.assets.commodities_ng1.runners.dry_run --dry-run-plumbing``:
  the REAL substrate (structural plumbing only: plane digests, config
  digests, chain/census structure);
- the I tests run the same self-check function on SYNTHETIC loaders.
"""

from __future__ import annotations

import hashlib
import json
import sys

SCHEMA = "commodities_ng1/runners/dry_run@1"

#: Outcome vocabulary forbidden in ANY structural artifact key.
_OUTCOME_VOCABULARY = ("pnl", "expectancy", "edge", "profit_factor",
                       "sharpe", "drawdown", "win_rate", "payoff",
                       "gross", "net_", "_net", "return_", "_return")


def assert_structural(obj, path: str = "$") -> None:
    """Fail-closed scan: no outcome-vocabulary key may appear in a
    structural artifact (I-phase no-PnL law)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            for bad in _OUTCOME_VOCABULARY:
                if bad in kl:
                    raise ValueError(
                        f"structural artifact carries outcome-vocabulary "
                        f"key {path}.{k} (I-phase no-PnL law)")
            assert_structural(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            assert_structural(v, f"{path}[{i}]")


def canonical_json(obj) -> str:
    """The freeze's canonical JSON law (sort_keys=True,
    separators=(',',':'))."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def arm_config_digest(arm_config: dict) -> str:
    """arm_config_digest = sha256 of the UTF-8 canonical JSON of the
    arm_config (recomputable by any party; freeze digest law)."""
    return hashlib.sha256(
        canonical_json(arm_config).encode("utf-8")).hexdigest()


def assemble_booked_arms(freeze: dict) -> dict:
    """Consume the 3 booked arms VERBATIM from the binding S freeze
    and verify every recorded digest + the trial-accounting structure."""
    arms = freeze["section2_arm_plan"]["arms"]
    booked = [a for a in arms if a.get("selection_status") == "BOOKED"]
    results = []
    digests = []
    for a in booked:
        recomputed = arm_config_digest(a["arm_config"])
        recorded = a["arm_config_digest"]
        digests.append(recomputed)
        results.append({
            "arm_id": a["arm_id"],
            "role": a["role"],
            "recorded_digest": recorded,
            "recomputed_digest": recomputed,
            "digest_match": bool(recomputed == recorded),
            "parameters": a["arm_config"]["parameters"],
            "bookable_pairs": a["arm_config"]["bookable_pairs"],
            "primary_tier": a["arm_config"]["cost_treatment"]
            ["primary_tier"],
        })
    acct = freeze["trial_accounting"]
    structural = {
        "schema": SCHEMA,
        "item": "config_assembly",
        "single_family": freeze["section2_arm_plan"]["single_family"],
        "booked_cells": len(booked),
        "trial_budget_cells": acct["trial_budget_cells"],
        "unbooked_cells": acct["unbooked_cells"],
        "booked_arm_ids": acct["booked_arm_ids"],
        "digests_pairwise_distinct": len(set(digests)) == len(digests),
        "all_digests_match": all(r["digest_match"] for r in results),
        "arms": results,
    }
    if not structural["all_digests_match"]:
        raise ValueError(
            "arm_config_digest mismatch against the binding freeze; "
            "fail closed")
    if not structural["digests_pairwise_distinct"]:
        raise ValueError("arm digests not pairwise distinct; fail closed")
    if structural["booked_cells"] + structural["unbooked_cells"] \
            != structural["trial_budget_cells"]:
        raise ValueError("trial budget accounting broken; fail closed")
    assert_structural(structural)
    return structural


def bookable_pairs_of(freeze: dict) -> list[str]:
    """The frozen bookable set (11 pairs; section2 bookable_set)."""
    return list(freeze["section2_arm_plan"]["bookable_set"]["pairs"])


def plumbing_self_check(freeze: dict, cot_loader, etp_loader,
                        pairs: list[str] | None = None,
                        p2_per_pair_census: dict | None = None) -> dict:
    """The structural self-check over injectable loaders.

    ``cot_loader()`` -> {contract_market_code: [report dict rows]} (the
    caller obtains them via the P0 plane on the real substrate, or
    synthetically in tests).  ``etp_loader(symbol)`` ->
    (session_dates, session_closes, split_boundary_dates).

    Emits STRUCTURAL COUNTS ONLY and enforces the no-PnL key law.
    """
    from research.assets.commodities_ng1.runners.battery import (
        battery_position_series,
    )
    from research.assets.commodities_ng1.runners.chain import (
        build_pair_chain, verify_pair_census,
    )

    config = assemble_booked_arms(freeze)
    cot = cot_loader()
    bookable = sorted(set(pairs if pairs is not None
                          else bookable_pairs_of(freeze)))
    per_pair = {}
    for pid in bookable:
        code, symbol = pid.split("/")
        reports = cot.get(code)
        if not reports:
            raise ValueError(f"pair {pid}: no CoT reports; fail closed")
        session_dates, session_closes, boundaries = etp_loader(symbol)
        chain = build_pair_chain(reports, session_dates, session_closes)
        census_ref = None
        if p2_per_pair_census is not None:
            census_ref = p2_per_pair_census.get(pid, {}).get(
                "floor_evaluation")
        census_ok = None
        if census_ref is not None:
            census_ok = bool(verify_pair_census(pid, chain, census_ref))
        arm_counts = []
        for a in config["arms"]:
            anchor = battery_position_series(
                chain, a["parameters"], roles=("ANCHOR",))["ANCHOR"]
            n_held = sum(1 for p in anchor if p != 0.0)
            arm_counts.append({
                "arm_id": a["arm_id"],
                "chain_rows": len(anchor),
                "counted_instants": sum(chain["counted"]),
                "held_decision_count": n_held,
                "flat_decision_count": sum(chain["counted"]) - n_held,
            })
        per_pair[pid] = {
            "cot_market_code": code,
            "etp_leg": symbol,
            "cot_reports": len(reports),
            "etp_sessions": len(set(session_dates)),
            "split_boundary_dates": sorted(
                b.isoformat() if hasattr(b, "isoformat") else str(b)
                for b in boundaries),
            "chain_rows": len(chain["rows"]),
            "counted_instants": sum(chain["counted"]),
            "census_identity_verified": census_ok,
            "arm_decision_counts": arm_counts,
        }
    pooled_counted = sum(v["counted_instants"] for v in per_pair.values())
    out = {
        "schema": SCHEMA,
        "item": "dry_run_plumbing",
        "law": "I-phase structural plumbing only: digests, counts, "
               "config assembly; NO PnL, no outcome numbers",
        "single_family": config["single_family"],
        "booked_cells": config["booked_cells"],
        "unbooked_cells": config["unbooked_cells"],
        "arm_config_digests": {
            a["arm_id"]: a["recorded_digest"] for a in config["arms"]},
        "all_digests_match": config["all_digests_match"],
        "digests_pairwise_distinct": config["digests_pairwise_distinct"],
        "bookable_pairs": bookable,
        "bookable_pair_count": len(bookable),
        "per_pair": per_pair,
        "pooled_counted_instants": pooled_counted,
        "q11_minimums": {"per_pair": 300, "pooled": 3300},
        "pooled_meets_q11_minimum": pooled_counted >= 3300,
    }
    assert_structural(out)
    return out


def main(argv: list[str] | None = None) -> int:
    """REAL-substrate structural plumbing self-check (no PnL)."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--dry-run-plumbing" not in argv:
        print("usage: dry_run.py --dry-run-plumbing", file=sys.stderr)
        return 2
    import os
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    sys.path.insert(0, repo_root)
    run_dir = os.path.join(repo_root, "research", "control",
                           "commodities_ng1_run")
    with open(os.path.join(run_dir, "s", "selection_freeze.json"),
              encoding="utf-8") as fh:
        freeze = json.load(fh)
    with open(os.path.join(run_dir, "p2_gate.json"),
              encoding="utf-8") as fh:
        p2 = json.load(fh)
    with open(os.path.join(run_dir, "p1_cost_contract.json"),
              encoding="utf-8") as fh:
        contract = json.load(fh)

    bookable = bookable_pairs_of(freeze)
    codes = {p.split("/")[0] for p in bookable}
    legs = {p.split("/")[1] for p in bookable}

    # Committed measured share-base boundary events per bookable leg
    # (p1_cost_contract per_leg spread.share_base_events; never
    # re-derived).
    leg_boundaries: dict[str, set] = {}
    for leg in legs:
        events = (contract.get("per_leg", {}).get(leg, {})
                  .get("spread", {}).get("share_base_events", []))
        leg_boundaries[leg] = {e["boundary_date"] for e in events}

    from research.assets.commodities_ng1.plane_adapter import (
        CommoditiesNG1Plane,
    )
    plane = CommoditiesNG1Plane()
    digest_rows = []
    cot_by_code: dict[str, list[dict]] = {}
    for year in range(2016, 2027):
        entry = f"cftc/deacot{year}"
        res = plane.consume(entry)
        digest_rows.append({
            "entry": entry,
            "sha256_pinned": res["sha256_pinned"],
            "sha256_measured": res["sha256_measured"],
            "digest_ok": bool(res["sha256_pinned"]
                              == res["sha256_measured"]),
            "bytes": res["bytes"],
        })
        _, records = plane.consume_records(entry)
        for rec in records:
            if rec.contract_market_code in codes:
                cot_by_code.setdefault(
                    rec.contract_market_code, []).append({
                        "report_date": rec.report_date,
                        "open_interest": rec.open_interest,
                        "noncomm_long": rec.noncomm_long,
                        "noncomm_short": rec.noncomm_short,
                        "noncomm_spreading": rec.noncomm_spreading,
                        "comm_long": rec.comm_long,
                        "comm_short": rec.comm_short,
                    })
    from research.assets.commodities_ng1.etp_census import csv_to_rows

    def etp_loader(symbol: str):
        path = os.path.join(run_dir, "etp_eod", f"{symbol}.csv")
        with open(path, encoding="utf-8") as fh:
            rows = csv_to_rows(fh.read(), symbol=symbol)
        dates = [r["date"] for r in rows]
        closes = {r["date"]: r["close"] for r in rows}
        return dates, closes, set(leg_boundaries.get(symbol, ()))

    out = plumbing_self_check(freeze,
                              cot_loader=lambda: cot_by_code,
                              etp_loader=etp_loader,
                              pairs=None,
                              p2_per_pair_census=p2["per_pair_census"])
    out["plane_digests"] = digest_rows
    out["plane_digests_all_ok"] = all(d["digest_ok"]
                                      for d in digest_rows)
    assert_structural(out)
    print(json.dumps(out, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
