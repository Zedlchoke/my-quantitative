"""F-3 clock-placebo REBUILD runner — skeptic ADJUDICATION #2 (one shot).

Reads the battery's measured occupancies from falsifier_results.json,
recomputes r per pair from the UNROUNDED values, rebuilds the control per
the amended spec (seed 20260925; entries/day scaled one-shot by r;
uniform-random in-session entry hours — deliberately NOT the anchor's
hour distribution; seed-pinned day-parity; durations unchanged; honest
own-event-time costing in the scored phase, no cost-parity demand),
verifies the amended predicates (a)-(d) FAIL-CLOSED, patches the freeze
artifact (new arm_config_digest replacing the old, seed, per-pair r,
before/after occupancy, amended predicate text verbatim, signed zero-PnL
statement) and APPENDS the rebuild rows to the committed ledger.

Sanction: ADJUDICATION #2 A2.2 — exactly ONE rebuild occurrence; a
predicate miss closes F-3's control as UNBUILDABLE_SHAPE /
BLOCKED_F3_CONTROL with no second attempt.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LANE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LANE / "scripts"))

import tracka_lib as T  # noqa: E402
from falsifier_run import (DERIVED, OUT_FREEZE, OUT_LEDGER, OUT_RESULTS,  # noqa: E402
                           PAIRS, SEAM_LIMB3_MIN_N, WARMUP_TRADED_DAYS,
                           HOLDOUT_START, arm_digest)

OUT_REBUILD = LANE / "falsifier_rebuild_results.json"
REBUILD_SEED = 20260925
BAND_PP = 0.10

AMENDED_PREDICATE_TEXT = (
    "(a) |occ_ctrl - occ_anchor| <= 10 pp on the pinned in-session "
    "denominator (07:00-18:00 UTC bars, identical definition for anchor "
    "and control), achieved via the one-shot r = (occupancy_anchor + "
    "10 pp) / occupancy_natural calibration, else UNBUILDABLE_SHAPE / "
    "BLOCKED_F3_CONTROL; (b) >= 90% of control round trips distinct from "
    "the anchor's (entry_ts, dir); (c) both directions present; (d) "
    "signal series non-constant; (e) kill band unchanged: control net "
    ">= 0.5 x anchor net @ x1.0 => KILL_CONTROL_REPRODUCED, plus the "
    "fold-residue clause (control net-positive on >= 4/6 dev folds while "
    "anchor net < 2 x control net); (f) uniform-random hours + "
    "seed-pinned parity + honest own-event cost, no anchor-hour import, "
    "no cost parity.")

ZERO_PNL_STATEMENT = (
    "ZERO-PNL-AT-REBUILD ATTESTATION (signed): at rebuild time no "
    "net-return / expectancy / PF / win-rate of any arm has been computed "
    "anywhere in cycle ERP1-TRACKA-COHORT-1; the holdout window "
    "2026-01-01..2026-06-30 has never been read; every rebuild input is a "
    "dev-window signal-level shape statistic (occupancy, entries/day, "
    "holding duration) that the battery itself was required to measure. "
    "This rebuild is the ONE occurrence sanctioned by skeptic ADJUDICATION "
    "#2 (A2.2, 'SANCTIONED - one occurrence, no look consumed'); any "
    "second rebuild is unavailable — failure is BLOCKED_F3_CONTROL.")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_plane(pair: str):
    from pair_config import load_pair_config
    cfg = load_pair_config(pair)
    df = pd.read_parquet(DERIVED / f"bars1h_ANC_{pair}.parquet")
    df = df[df["ts"] < pd.Timestamp(f"{HOLDOUT_START}T00:00:00Z")]
    return T.SignalPlane(df, pip_mult=1.0 / cfg.pip)


def main() -> int:
    results = json.loads(OUT_RESULTS.read_text())
    freeze = json.loads(OUT_FREEZE.read_text())

    out = {
        "schema": "tracka_placebo_rebuild@1",
        "sanction": "skeptic ADJUDICATION #2 (A2.1 AMEND approve-with-"
                    "amendment; A2.2 SANCTIONED - one occurrence, no look "
                    "consumed); adjudication text: "
                    "research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/"
                    "tracka_cohort1/SKEPTIC_cohort1_REPORT.md#adjudication-2",
        "seed": REBUILD_SEED,
        "band_pp": BAND_PP,
        "amended_predicate_text_verbatim": AMENDED_PREDICATE_TEXT,
        "pairs": {},
        "verdict": None,
    }

    per_pair = {}
    for pair in PAIRS:
        p = load_plane(pair)
        days = p.traded_days()
        warmup_end_idx = int(
            np.nonzero(p.day == days[WARMUP_TRADED_DAYS - 1])[0][-1])
        idx = np.arange(len(p.ts))
        in_session = (~p.skip) & (p.hour >= 7) & (p.hour <= 18) \
            & (idx > warmup_end_idx)

        # measured battery numbers (unrounded) + consistency gate
        bat = results["pairs"][pair]
        occ_anchor = bat["F3_placebo_probe"]["anchor_tgt_in_session_occupancy"]
        occ_natural = bat["F3_placebo_probe"]["occupancy_in_session"]
        tgt_anchor = T.f_rangeexp_anchor_shift(p)
        occ_anchor_live = float((tgt_anchor[in_session] != 0).mean())
        if abs(occ_anchor_live - occ_anchor) > 1e-9:
            print(json.dumps({"verdict": "NOT_RUN_CONSISTENCY_DRIFT",
                              "pair": pair, "live": occ_anchor_live,
                              "recorded": occ_anchor}))
            return 5
        sched_anchor = T.schedule_only(p, tgt_anchor, warmup_end_idx)

        rb = T.placebo_rebuild(
            p, occ_anchor, occ_natural, sched_anchor, in_session,
            seed=REBUILD_SEED, warmup_end_idx=warmup_end_idx)
        rb["verdict"] = ("CONSTRUCTIBLE" if rb["all_predicates_hold"]
                         else "UNBUILDABLE_SHAPE")
        rb["pair"] = pair
        rb["in_session_bars"] = int(in_session.sum())
        rb["anchor_trips_dev"] = len(sched_anchor)
        rb["arm_config_digest_new"] = arm_digest(
            "M1", "CAUSAL-PLACEBO", pair,
            {"recipe": "rebuild_adjudication_2", "r": rb["r"],
             "seed": REBUILD_SEED, "parity": "even->+1",
             "hours": "uniform 7..17", "hold": rb["hold_bars"]})
        rb["arm_config_digest_old"] = next(
            e["arm_config_digest"] for e in freeze["arm_registry"]
            if e["mechanism"] == "M1" and e["arm"] == "CAUSAL-PLACEBO"
            and e["pair"] == pair)
        per_pair[pair] = rb
        out["pairs"][pair] = rb

    out["verdict"] = ("CONSTRUCTIBLE"
                      if all(v["all_predicates_hold"] for v in
                             per_pair.values())
                      else "UNBUILDABLE_SHAPE")
    OUT_REBUILD.write_text(json.dumps(out, indent=1, default=str))

    # ---------------- freeze artifact patch (additive, pins kept) -------
    new_digests = {pair: per_pair[pair]["arm_config_digest_new"]
                   for pair in PAIRS}
    # (1) holdout membership: replace the CAUSAL-PLACEBO digest per pair
    for pair in PAIRS:
        for comp in freeze["pins"]["(ii)_holdout_pass_membership"] \
                ["per_pair"][pair]["companions_single_pass"]:
            if comp["arm"] == "CAUSAL-PLACEBO":
                comp["arm_config_digest"] = new_digests[pair]
                comp["recipe"] = "rebuild_adjudication_2"
    membership_blob = json.dumps(
        freeze["pins"]["(ii)_holdout_pass_membership"]["per_pair"],
        sort_keys=True, default=str)
    freeze["pins"]["(ii)_holdout_pass_membership"]["sha256"] = \
        hashlib.sha256(membership_blob.encode()).hexdigest()
    freeze["pins"]["(ii)_holdout_pass_membership"]["sha256_note"] = (
        "recomputed after the ADJUDICATION #2 CAUSAL-PLACEBO digest "
        "replacement (sanctioned rebuild, recorded per A2.2 obligations)")
    # (2) arm registry: replace the CAUSAL-PLACEBO entries
    for entry in freeze["arm_registry"]:
        if entry["mechanism"] == "M1" and entry["arm"] == "CAUSAL-PLACEBO":
            entry["arm_config_digest"] = new_digests[entry["pair"]]
            entry["status"] = ("FROZEN_PRE_PNL (rebuilt per skeptic "
                               "ADJUDICATION #2 - ONE occurrence; "
                               "supersedes the natural-recipe digest "
                               "recorded in commit 3931aed8)")
    # (3) rebuild section
    statement_blob = ZERO_PNL_STATEMENT
    freeze["clock_placebo_rebuild"] = {
        "sanction": out["sanction"],
        "occurrence": "ONE (consumed by this rebuild; any second rebuild "
                      "unavailable - failure is BLOCKED_F3_CONTROL)",
        "seed": REBUILD_SEED,
        "band_pp": BAND_PP,
        "amended_predicate_text_verbatim": AMENDED_PREDICATE_TEXT,
        "supersedes": "placebo_recipe_pin (kept below for the record)",
        "per_pair": {pair: {
            "r": per_pair[pair]["r"],
            "occ_natural_before": per_pair[pair]["occ_natural_before"],
            "occ_anchor": per_pair[pair]["occ_anchor"],
            "occ_ctrl_after": per_pair[pair]["occ_ctrl"],
            "margin_a_pp": per_pair[pair]["margin_a_pp"],
            "predicates": per_pair[pair]["predicates"],
            "all_predicates_hold": per_pair[pair]["all_predicates_hold"],
            "distinct_trip_share": per_pair[pair]["distinct_trip_share"],
            "directions": per_pair[pair]["directions"],
            "parity_rule": per_pair[pair]["parity_rule"],
            "draw_order": per_pair[pair]["draw_order"],
            "hold_bars": per_pair[pair]["hold_bars"],
            "entries_placed": per_pair[pair]["entries_placed"],
            "trips_dev": per_pair[pair]["trips_dev"],
            "arm_config_digest_old": per_pair[pair]["arm_config_digest_old"],
            "arm_config_digest_new": per_pair[pair]["arm_config_digest_new"],
            "costing": "honest own-event-time costing at the placebo's "
                       "fill bars from the same per-session spread curve "
                       "in the scored phase; NO cost-parity demand",
            "rider": "control-net-per-occupied-hour vs anchor-net-per-"
                     "occupied-hour is a SCORED-PHASE diagnostic obligation "
                     "(signal-level lane cannot compute net)",
        } for pair in PAIRS},
        "zero_pnl_statement": statement_blob,
        "zero_pnl_statement_sha256": hashlib.sha256(
            statement_blob.encode()).hexdigest(),
        "signed_by": "tracka1-falsifier lane, "
                     + dt.datetime.now(dt.timezone.utc).isoformat(
                         timespec="seconds"),
        "rebuild_results_sha256": sha256_file(OUT_REBUILD),
    }
    freeze["placebo_recipe_pin"]["superseded_by"] = "clock_placebo_rebuild"
    OUT_FREEZE.write_text(json.dumps(freeze, indent=1, default=str))

    # ---------------- ledger APPEND (committed file: append-only) -------
    chain = {"code_freeze": freeze["sha_chain"]["code_freeze"],
             "data_manifest": freeze["cost_book"]["census_sha256"],
             "selection_digest": sha256_file(OUT_REBUILD)}
    with open(OUT_LEDGER, "a") as f:
        for pair in PAIRS:
            rb = per_pair[pair]
            row = {
                "cycle_id": "ERP1-TRACKA-COHORT-1",
                "mechanism_id": "M1", "arm_id": "CAUSAL-PLACEBO",
                "arm_config_digest": rb["arm_config_digest_new"],
                "pair": pair,
                "fold_or_holdout_tag": "PRE_PNL_REBUILD_ADJUDICATION_2",
                "cost_tier": "PAPER_TIER_PER_SESSION_X_K",
                "net_pnl": None, "gross_pnl": None,
                "gates_with_margins_to_fail": {
                    "r": rb["r"],
                    "occ_natural_before": rb["occ_natural_before"],
                    "occ_anchor": rb["occ_anchor"],
                    "occ_ctrl_after": rb["occ_ctrl"],
                    "predicate_a_margin_pp": rb["margin_a_pp"],
                    "distinct_trip_share": rb["distinct_trip_share"],
                    "directions": rb["directions"],
                    "non_constant": rb["predicates"]["d_non_constant"],
                    "hold_bars": rb["hold_bars"],
                    "trips_dev": rb["trips_dev"],
                    "seed": REBUILD_SEED,
                },
                "verdict": rb["verdict"],
                "exclusion_zones": None,
                "labels": ["SINGLE_SOURCE_PANEL",
                           "FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK",
                           "PAPER_TIER"],
                "falsifier_id": "F-3-control-rebuild",
                "sha_chain": chain,
                "note": "one-shot rebuild per skeptic ADJUDICATION #2 "
                        "(A2.1 amendment, A2.2 sanction: one occurrence, "
                        "no look consumed); supersedes the natural-recipe "
                        "digest; scored-phase rider: net-per-occupied-hour "
                        "disclosure",
            }
            f.write(json.dumps(row, default=str) + "\n")

    print(json.dumps({pair: {
        "r": round(per_pair[pair]["r"], 6),
        "occ_before": round(per_pair[pair]["occ_natural_before"], 6),
        "occ_after": round(per_pair[pair]["occ_ctrl"], 6),
        "occ_anchor": round(per_pair[pair]["occ_anchor"], 6),
        "margin_a_pp": round(per_pair[pair]["margin_a_pp"], 3),
        "predicates": per_pair[pair]["predicates"],
        "trips_dev": per_pair[pair]["trips_dev"],
        "distinct_share": round(per_pair[pair]["distinct_trip_share"], 4),
        "verdict": per_pair[pair]["verdict"],
    } for pair in PAIRS} | {"overall": out["verdict"]}, indent=1))
    return 0 if out["verdict"] == "CONSTRUCTIBLE" else 6


if __name__ == "__main__":
    sys.exit(main())
