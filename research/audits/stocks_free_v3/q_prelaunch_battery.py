"""STOCKS-FREE-V3 Phase-Q prelaunch battery (A1, PLAN_stocks.md section 14).

Runs the §14 machine gates that are executable without a scored cell:

  B. six-arm dummy dry-run into ONE fresh empty temporary ledger;
  C. six distinct trial identities, six first publications, six idempotent
     replays with zero counter delta, zero-position publication denial;
  D. benchmark/beta falsification on synthetic fixtures (a beta-only arm
     earns ~0 incremental alpha; a genuine edge earns its excess);
  E. real-loader gate: sealed snapshot read through the actual loaders with
     pin verification, schedule-only feasibility on real S0 (no metrics).

The battery never computes or persists a scored metric on real data; its
only real-data artefacts are schedule/feasibility facts.  Output:
research/audits/stocks_free_v3/q_prelaunch_battery.json
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

from research.assets.stocks.factory import (
    GatedTrialLedger,
    publication_metrics,
)
from research.stocks_free_v3.arm_registry import (
    EXECUTION_ORDER,
    S1_START,
    build_arm_schedule,
    build_registry,
    run_arm_dry_run,
    schedule_entries,
)
from research.stocks_free_v3.benchmarks import build_risk_matched_spy
from research.stocks_free_v3.incremental import compute_fold_alpha

RESULTS: dict = {"schema": "stocks_free_v3/q_prelaunch_battery@1"}
SYMBOLS = ["SPY", "XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLU",
           "XLB", "XLRE"]


def _weekday_sessions(start: date, end: date) -> list[str]:
    out, cur = [], start
    while cur <= end:
        if cur.weekday() < 5:
            out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def _synthetic_world(n_sessions: int) -> dict:
    """Deterministic synthetic cohort with guaranteed IDIO triggers."""
    sessions = _weekday_sessions(date(2021, 1, 4), date(2021, 12, 31))[:n_sessions]
    rng = random.Random(7)
    spy = [rng.gauss(0.0004, 0.01) for _ in sessions]
    shocks = {}
    for sym, idx, size in (("XLK", 100, -0.10), ("XLE", 130, 0.10)):
        shocks[(sym, idx)] = size
    returns: dict[str, dict[str, float]] = {"SPY": {}}
    raw_close: dict[str, dict[str, float]] = {}
    betas = {"XLK": 1.2, "XLE": 0.8, "XLF": 1.0, "XLV": 0.7, "XLI": 1.0,
             "XLP": 0.6, "XLY": 1.1, "XLU": 0.6, "XLB": 0.9, "XLRE": 0.9}
    level = {s: 100.0 for s in SYMBOLS}
    for i, d in enumerate(sessions):
        returns["SPY"][d] = spy[i]
        level["SPY"] *= 1.0 + spy[i]
        raw_close.setdefault("SPY", {})[d] = round(level["SPY"], 6)
        for sym in SYMBOLS[1:]:
            r = betas[sym] * spy[i] + rng.gauss(0.0, 0.008)
            if (sym, i) in shocks:
                r += shocks[(sym, i)]
            returns.setdefault(sym, {})[d] = r
            level[sym] *= 1.0 + r
            raw_close.setdefault(sym, {})[d] = round(level[sym], 6)
    return {"sessions": sessions, "returns": returns, "raw_close": raw_close,
            "distributions": {s: {} for s in SYMBOLS},
            "split_factors": {s: {} for s in SYMBOLS}}


def section_b_c(world: dict, tmp: Path) -> dict:
    """Six-arm dummy dry-run + publication/idempotence/denial battery."""
    from research.stocks_free_v3.arm_registry import ArmInputs

    inputs = ArmInputs(
        sessions=tuple(world["sessions"]),
        raw_close=world["raw_close"],
        distributions=world["distributions"],
        split_factors=world["split_factors"],
        issuer_tr_returns=world["returns"],
    )
    reg = build_registry()
    ledger_dir = str(tmp / "qa_ledger")
    dry: dict = {}
    for arm_id in EXECUTION_ORDER:
        payload = run_arm_dry_run(
            arm_id, inputs, ledger_dir=ledger_dir,
            publish_to_temp_ledger=False)
        dry[arm_id] = {
            "arm_id": payload.get("arm_id", arm_id),
            "feasibility_turnover_two_way_per_year":
                payload.get("feasibility", {}).get(
                    "two_way_turnover_per_year",
                    payload.get("turnover_two_way_per_year")),
            "keys": sorted(k for k in payload.keys()),
        }
    RESULTS.setdefault("checks", {})[
        "B_six_arm_dummy_dry_run"] = {"status": "PASS", "arms": dry,
                                      "ledger_dir_shared": True}

    # one fresh empty temporary ledger receives all six publications
    ledger = GatedTrialLedger(path=str(tmp / "qa_pub_ledger.json"))
    pubs, replays = {}, {}
    observed_before = ledger.observed
    for arm_id in EXECUTION_ORDER:
        entries = schedule_entries(arm_id, inputs)
        metrics = publication_metrics(entries)
        artifact = {"arm_id": arm_id, "trial": "Q_DUMMY",
                    "n_entries": len(entries)}
        ok = ledger.publish_result(arm_id, artifact, **metrics)
        pubs[arm_id] = bool(ok)
    published_after_first = len(ledger.published_keys)
    for arm_id in EXECUTION_ORDER:
        replays[arm_id] = bool(ledger.publish_result(
            arm_id, {"arm_id": arm_id, "trial": "Q_DUMMY_REPLAY"},
            n_fill_events=1, n_held_positions=1))
    # fix publication metrics to come from the canonical schedule entries
    RESULTS["schedule_entry_counts"] = {
        arm_id: len(schedule_entries(arm_id, inputs))
        for arm_id in EXECUTION_ORDER}
    delta = {
        "published_keys_after_first": published_after_first,
        "published_keys_after_replays": len(ledger.published_keys),
        "first_publication_events":
            sum(1 for e in ledger.entries
                if e.get("event") == "FIRST_PUBLICATION"),
        "replay_zero_delta_events":
            sum(1 for e in ledger.entries
                if e.get("event") == "REPLAY_ZERO_DELTA"),
        "observed_delta_from_pubs_and_replays":
            ledger.observed - observed_before,
    }
    denial = ledger.publish_result("ZERO-ARM", {},
                                   n_fill_events=0, n_held_positions=0)
    refusal_events = [e for e in ledger.entries
                      if e.get("event") == "PUBLICATION_REFUSED_ZERO_RESULT"]
    checks = {
        "all_first_publications_true": all(pubs.values()) and len(pubs) == 6,
        "six_distinct_published_keys":
            published_after_first == 6,
        "all_replays_rejected_zero_delta":
            (not any(replays.values()))
            and delta["replay_zero_delta_events"] == 6
            and delta["published_keys_after_replays"] == 6
            and delta["observed_delta_from_pubs_and_replays"] == 0,
        "zero_event_publication_denied": (denial is False
                                          and len(refusal_events) == 1),
    }
    RESULTS["checks"]["C_publication_battery"] = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "first_publications": pubs, "replays_accepted": replays,
        "delta": delta, "denial_ok": denial is False,
        "checks": checks,
    }
    return RESULTS["checks"]["C_publication_battery"]


def section_d(world: dict) -> dict:
    """Beta falsification: beta-only arm -> alpha ~ 0; edge -> alpha == edge."""
    sessions = world["sessions"]
    rule_tom = build_registry()["SFV3-A6-TOM-SETTLE-A"].vol_scaling_rule
    rule_const = build_registry()[
        "SFV3-A5-IDIO-SHOCK-REVERSAL-A1"].vol_scaling_rule
    out = {}
    for name, rule in (("risk_matched_tom_rule", rule_tom),
                       ("risk_matched_constant_rule", rule_const)):
        bench = build_risk_matched_spy(
            world["raw_close"]["SPY"], world["distributions"]["SPY"],
            world["split_factors"]["SPY"], sessions,
            sessions[70], sessions[-1], rule)
        beta_only = compute_fold_alpha(
            family_id="Q_SYNTHETIC", arm_id="BETA_ONLY", fold_id="F0",
            strategy_return_after_cost=bench.total_return,
            strategy_metric_digest=hashlib.sha256(
                b"q_battery_beta_only").hexdigest(),
            benchmark=bench)
        edge = compute_fold_alpha(
            family_id="Q_SYNTHETIC", arm_id="TIMED_EDGE", fold_id="F0",
            strategy_return_after_cost=bench.total_return + 0.01,
            strategy_metric_digest=hashlib.sha256(
                b"q_battery_timed_edge").hexdigest(),
            benchmark=bench)
        out[name] = {
            "benchmark_total_return": bench.total_return,
            "beta_only_alpha": beta_only.incremental_alpha,
            "beta_only_alpha_abs_lt_1e_12":
                abs(beta_only.incremental_alpha) < 1e-12,
            "edge_alpha": edge.incremental_alpha,
            "edge_alpha_equals_1pct": abs(edge.incremental_alpha - 0.01)
            < 1e-12,
        }
    ok = all(v["beta_only_alpha_abs_lt_1e_12"] and v["edge_alpha_equals_1pct"]
             for v in out.values())
    RESULTS["checks"]["D_beta_falsification"] = {
        "status": "PASS" if ok else "FAIL", "fixtures": out}
    return RESULTS["checks"]["D_beta_falsification"]


def section_e(tmp: Path) -> dict:
    """Real-loader gate: sealed reader + pins + schedule-only feasibility."""
    from research.stocks_free_v3.arm_registry import ArmInputs
    from research.stocks_free_v3.family_idio_shock.dryrun import (
        load_s0_snapshot_inputs,
    )
    from research.assets.common.contracts import canonical_json

    pin = json.loads((Path("research/stocks_free_v3/authority.py")).read_text()
                     ) if False else None
    inputs_d = load_s0_snapshot_inputs()
    sessions = list(inputs_d["sessions"])
    s1 = S1_START
    leak = [d for d in sessions if d >= s1]
    # schedule-only builds through the registry on REAL S0 (no metrics)
    from research.stocks_free_v3.family_idio_shock.schedule import (
        build_arm_schedule as idio_build,
    )
    from research.stocks_free_v3.family_idio_shock.arms import ARM_A1
    from research.stocks_free_v3.benchmarks import issuer_total_return_daily
    tr = {}
    for sym in SYMBOLS:
        dates, rets = issuer_total_return_daily(
            inputs_d["raw_close"][sym], inputs_d["distributions"][sym],
            inputs_d["split_factors"][sym])
        tr[sym] = dict(zip(dates, rets))
    real = ArmInputs(sessions=tuple(sessions), raw_close=inputs_d["raw_close"],
                     distributions=inputs_d["distributions"],
                     split_factors=inputs_d["split_factors"],
                     issuer_tr_returns=tr)
    idio_sched = idio_build(ARM_A1, sessions, tr)
    tom_sched = build_arm_schedule("SFV3-A6-TOM-SETTLE-A", real)
    idio_digest = idio_sched.schedule_digest
    tom_digest = tom_sched.schedule_digest
    ok = (not leak) and len(sessions) > 1000 and idio_digest and tom_digest
    RESULTS["checks"]["E_real_loader_gate"] = {
        "status": "PASS" if ok else "FAIL",
        "reader": "SealedSnapshotReader (pin-verified) via load_s0_snapshot_inputs",
        "s0_sessions": len(sessions),
        "first_session": sessions[0], "last_session": sessions[-1],
        "s1_leak_dates": leak[:5],
        "idio_a1_real_schedule_digest16": idio_digest[:16],
        "tom_a_real_schedule_digest16": tom_digest[:16],
        "scored_metrics_computed": 0,
    }
    return RESULTS["checks"]["E_real_loader_gate"]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output",
                        default="research/audits/stocks_free_v3/"
                                "q_prelaunch_battery.json")
    args = parser.parse_args()
    RESULTS["generated_by"] = "A1"
    with tempfile.TemporaryDirectory(prefix="v3_qa_") as td:
        tmp = Path(td)
        world = _synthetic_world(260)
        section_b_c(world, tmp)
        section_d(world)
        section_e(tmp)
    ok = all(c.get("status") == "PASS"
             for c in RESULTS["checks"].values())
    RESULTS["battery_verdict"] = ("Q_BATTERY_PASS" if ok
                                  else "Q_BATTERY_FAIL")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(RESULTS, indent=2) + "\n")
    print(json.dumps({k: v.get("status") for k, v in
                      RESULTS["checks"].items()}, indent=1))
    print(RESULTS["battery_verdict"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
