#!/usr/bin/env python
"""VOL-NG1 P1 runner (lane p1, task vol-ng1-p1-kernel-costs).

Consumes ONLY the committed P0 frozen substrate through the cycle's
read-only plane adapter (NO price network pulls), plus OFFICIAL fund
fee facts (5 unique URLs -- issuer pages + one SEC-filed 424B2; the
only network reads of this cycle).

Publishes:

- ``p1_fee_facts.json``      official fee-fact evidence (per leg:
                             URL, sha256, percent/annum, bps/day);
- ``p1_cost_contract.json``  the tier-2.0 measured cost contract
                             (Corwin-Schultz p90 stress spreads, Roll
                             cross-checks, expense drag, Q-16 measured
                             roll/decay path ladder component);
- ``p1_gate.json``           per-item measured values + provenance +
                             PASS/FAIL, including the pytest command
                             and exit code.

Sections: kernel_compat (dual-book degenerate case), corp_actions
(P0 inventory -> explicit events -> value invariance + continuity on
the REAL raw bars), cost_constants, clocks (UTC/NY DST + V7 close+1),
tests.

Exit codes: 0 = PASS, 3 = FAIL/BLOCKED, 4 = usage.

NO proposals, NO signals, NO scoring, NO outcome numbers anywhere.
"""

from __future__ import annotations

import argparse
import hashlib
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

from research.assets.vol_ng1 import accounting as ak     # noqa: E402
from research.assets.vol_ng1 import census as vc         # noqa: E402
from research.assets.vol_ng1 import clocks as ck         # noqa: E402
from research.assets.vol_ng1 import corp_actions as ca   # noqa: E402
from research.assets.vol_ng1 import costs as cs          # noqa: E402
from research.assets.vol_ng1 import plane_adapter as pa  # noqa: E402

SCHEMA = "vol_ng1_run/p1_gate@1"
TASK_ID = "vol-ng1-p1-kernel-costs"
CYCLE_ID = "VOL-NG1"

OUT_DIR = os.path.join(REPO_ROOT, "research", "control", "vol_ng1_run")
FEE_EVIDENCE_PATH = os.path.join(OUT_DIR, "p1_fee_facts.json")
CONTRACT_PATH = os.path.join(OUT_DIR, "p1_cost_contract.json")
GATE_PATH = os.path.join(OUT_DIR, "p1_gate.json")
FEE_CACHE_DIR = os.path.join(OUT_DIR, "p1_feefacts_untracked")

CBOE_ENTRIES = {
    "VIX": "VIX_History.csv",
    "VIX9D": "VIX9D_History.csv",
    "VIX3M": "VIX3M_History.csv",
    "VIX6M": "VIX6M_History.csv",
}
ETP_ENTRIES = {
    "VXX": "VXX.US_eod.json",
    "UVXY": "UVXY.US_eod.json",
    "SVXY": "SVXY.US_eod.json",
    "VIXY": "VIXY.US_eod.json",
    "VIXM": "VIXM.US_eod.json",
    "VXZ": "VXZ.US_eod.json",
}

TEST_COMMAND = (os.path.join(os.path.dirname(sys.executable), "python"),
                "-m", "pytest", "tests/test_vol_ng1_p1.py", "-q")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: str, obj: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False, default=str)
        fh.write("\n")


def git_state() -> dict:
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", REPO_ROOT, *args],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    return {"branch": git("branch", "--show-current"),
            "head_sha": git("rev-parse", "HEAD")}


# --------------------------------------------------------------------------- #
# consumed substrate (plane only; no network for prices)
# --------------------------------------------------------------------------- #
def consume_substrate(plane) -> dict:
    etp_bars: dict[str, list[dict]] = {}
    etp_digests = {}
    for leg, entry in ETP_ENTRIES.items():
        res = plane.consume(entry)
        etp_bars[leg] = json.loads(res["data"])
        etp_digests[leg] = res["sha256_measured"]
    index_closes: dict[str, dict[str, float]] = {}
    index_digests = {}
    for name, entry in CBOE_ENTRIES.items():
        res = plane.consume(entry)
        index_closes[name] = vc.parse_cboe_csv(res["data"])
        index_digests[name] = res["sha256_measured"]
    return {"etp_bars": etp_bars, "etp_digests": etp_digests,
            "index_closes": index_closes,
            "index_digests": index_digests}


# --------------------------------------------------------------------------- #
# section 1: kernel compatibility (degenerate dual-book case)
# --------------------------------------------------------------------------- #
def measure_kernel_compat() -> dict:
    # hand-computed degenerate case: 1 round trip (2 fills)
    rt = ak.book_round_trip(
        direction=1, notional_usd=10_000.0, entry_price=40.0,
        exit_price=44.0, stress_spread_frac=0.02)
    observed = {
        "gross_pnl_usd": rt["gross_pnl_usd"],
        "cost_per_fill_by_tier": {
            t: rt["fills"][t]["cost_per_fill_usd"]
            for t in rt["fills"]},
        "net_pnl_usd_by_tier": rt["net_pnl_usd_by_tier"],
        "expected": {
            "gross_pnl_usd": 1000.0,
            "cost_per_fill_by_tier": {"1.0": 100.0, "1.5": 150.0,
                                      "2.0": 200.0},
            "net_pnl_usd_by_tier": {"1.0": 800.0, "1.5": 700.0,
                                    "2.0": 600.0},
        },
    }
    exact = (
        abs(observed["gross_pnl_usd"] - 1000.0) < 1e-9
        and all(abs(observed["cost_per_fill_by_tier"][t]
                    - observed["expected"]["cost_per_fill_by_tier"][t])
                < 1e-9 for t in observed["cost_per_fill_by_tier"])
        and all(abs(observed["net_pnl_usd_by_tier"][t]
                    - observed["expected"]["net_pnl_usd_by_tier"][t])
                < 1e-9 for t in observed["net_pnl_usd_by_tier"]))
    ledger = ak.dual_book_ledger([rt], starting_equity=100_000.0)
    refusal_ok = False
    try:
        ak.compute_outcomes([rt])
    except ak.AccountingRefused:
        refusal_ok = True
    return {
        "command": "degenerate case: 1 round trip, 2 fills, "
                   "notional 10k, 40->44 long, stress spread 2%",
        "observed": observed,
        "values_exact": bool(exact),
        "dual_book_ledger": ledger,
        "shared_module": "research.accounting imported (identity "
                         "reconciliation + canonical row adapter), "
                         "not forked",
        "scored_refusal_ok": refusal_ok,
        "verdict": "PASS" if (exact and ledger["dual_book_equality_ok"]
                              and refusal_ok) else "FAIL",
    }


# --------------------------------------------------------------------------- #
# section 2: corp actions (P0 inventory -> explicit events)
# --------------------------------------------------------------------------- #
def measure_corp_actions(sub: dict) -> dict:
    inventory = ca.load_inventory()
    table = ca.build_event_table(inventory)
    mismatches = ca.inventory_mismatches(inventory, table)

    named_keys = sorted(f"{s}@{d}" for (s, d) in ca.NAMED_EVENTS)
    named_measured = []
    for sym, date_s in sorted(ca.NAMED_EVENTS):
        ev = next(e for e in table[sym] if e["date"] == date_s)
        named_measured.append({
            "key": f"{sym}@{date_s}",
            "kind": ev["kind"],
            "measured_factor": round(ev["factor"], 6),
            "nominal_factor": ev["nominal_factor"],
            "note": ev["named_note"],
        })

    per_leg = {}
    max_residual = 0.0
    total_uncovered = 0
    for leg, bars in sorted(sub["etp_bars"].items()):
        events = table[leg]
        ca.require_coverage(leg, events)
        res = ca.continuity_residuals(bars, events)
        uncovered = ca.scan_uncovered_steps(bars, events)
        max_residual = max(max_residual,
                           res["max_abs_mechanical_residual"])
        total_uncovered += len(uncovered)
        per_leg[leg] = {
            "steps_inventoried": len(events),
            "kinds": sorted({e["kind"] for e in events}),
            "max_abs_mechanical_residual":
                res["max_abs_mechanical_residual"],
            "uncovered_steps": uncovered,
        }

    # position-layer value law re-measured on REAL bars at the named
    # events: after restatement, a position revalued at the raw event
    # close captures ONLY the adjusted (market) ratio across the step
    invariance = []
    for sym, date_s in sorted(ca.NAMED_EVENTS):
        if ca.NAMED_EVENTS[(sym, date_s)]["kind"] == "PRICE_EVENT":
            continue  # value changes with the market by design
        ev = next(e for e in table[sym] if e["date"] == date_s)
        bars = sorted(sub["etp_bars"][sym], key=lambda b: b["date"])
        idx = next(i for i, b in enumerate(bars)
                   if b["date"] == date_s)
        raw_prev = float(bars[idx - 1]["close"])
        raw_cur = float(bars[idx]["close"])
        shares_before = 100.0
        shares_after, _price_after = ca.apply_event(
            shares_before, raw_prev, ev)
        value_unhandled = shares_before * raw_cur
        value_handled = shares_after * raw_cur
        adj = ca.event_adjusted_closes(bars, [ev])
        adjusted_ratio = adj[date_s] / adj[max(d for d in adj
                                               if d < date_s)]
        expected = shares_before * raw_prev * adjusted_ratio
        invariance.append({
            "key": f"{sym}@{date_s}",
            "shares_restated": round(shares_after, 9),
            "value_unhandled_at_raw_step": round(value_unhandled, 9),
            "value_handled": round(value_handled, 9),
            "value_expected_market_only": round(expected, 9),
            "captures_market_ratio_only":
                abs(value_handled - expected) < 1e-6,
        })

    return {
        "inventory_source": os.path.relpath(inventory["gate_path"],
                                            REPO_ROOT),
        "total_steps_inventoried": inventory["total_steps"],
        "named_events_packet": named_keys,
        "named_events_measured": named_measured,
        "inventory_table_mismatches": mismatches,
        "per_leg": per_leg,
        "max_abs_mechanical_residual": max_residual,
        "total_uncovered_steps": total_uncovered,
        "position_invariance_named": invariance,
        "raw_primary_note": "RAW series primary (V8); every "
                            "inventoried step carries an explicit "
                            "SPLIT/REORG/PRICE_EVENT decision",
        "verdict": "PASS" if (not mismatches and total_uncovered == 0
                              and max_residual < 1e-4
                              and all(i["captures_market_ratio_only"]
                                      for i in invariance)
                              ) else "FAIL",
    }


# --------------------------------------------------------------------------- #
# section 3: measured cost constants + tier-2.0 contract
# --------------------------------------------------------------------------- #
def measure_costs(sub: dict, fetch_live: bool) -> tuple[dict, dict]:
    # fee facts: live official reads (bounded) or committed evidence
    if fetch_live:
        legs = cs.fetch_fee_facts(cache_dir=FEE_CACHE_DIR)
    else:
        legs = cs.load_fee_facts(FEE_EVIDENCE_PATH)
    evidence = {
        "schema": "vol_ng1_run/p1_fee_facts@1",
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "measured_utc": now_utc(),
        "note": "official issuer pages + SEC-filed prospectus only; "
                "raw bytes cached untracked under "
                "p1_feefacts_untracked/ (never committed)",
        "legs": legs,
    }
    write_json(FEE_EVIDENCE_PATH, evidence)

    per_leg = {}
    problems = []
    for leg in cs.LIVING_LEGS:
        bars = sub["etp_bars"][leg]
        cs_monthly = cs.corwin_schultz_monthly(bars)
        stress = cs.cs_stress_tier(cs_monthly)
        closes = [float(b["close"]) for b in
                  sorted(bars, key=lambda b: b["date"])]
        roll = cs.roll_spread(closes)
        fee = legs.get(leg) or {}
        bucket = cs.LEG_BUCKETS[leg]
        path = cs.path_cost_series(sub["index_closes"], bucket)
        if fee.get("verdict") != "MEASURED":
            problems.append(f"{leg}: expense fact {fee.get('verdict')}")
            continue
        per_leg[leg] = cs.build_leg_cost(leg, stress, roll, fee, path)

    contract = None
    if not problems:
        contract = cs.build_cost_contract(per_leg)
        write_json(CONTRACT_PATH, contract)
    return evidence, {
        "fee_evidence_path": os.path.relpath(FEE_EVIDENCE_PATH,
                                             REPO_ROOT),
        "fee_legs_measured": sorted(
            l for l, v in legs.items()
            if v.get("verdict") == "MEASURED"),
        "contract_path": os.path.relpath(CONTRACT_PATH, REPO_ROOT)
        if contract else None,
        "contract_sha256": sha256_file(CONTRACT_PATH)
        if contract else None,
        "problems": problems,
        "per_leg_summary": {
            leg: {
                "cs_p50_spread_frac": per_leg[leg]["spread"][
                    "p50_spread_frac"],
                "cs_p90_spread_frac": per_leg[leg]["spread"][
                    "p90_spread_frac"],
                "cs_measurable_months": per_leg[leg]["spread"][
                    "n_measurable_months"],
                "cs_floored_months": per_leg[leg]["spread"][
                    "floored_months"],
                "roll_spread_frac": round(
                    per_leg[leg]["roll_crosscheck"]["spread_frac"], 8),
                "expense_pct_per_annum": per_leg[leg]["expense"][
                    "percent_per_annum"],
                "expense_bps_per_day": per_leg[leg]["expense"][
                    "bps_per_day"],
                "path_mean_daily_bps": per_leg[leg]["path_cost"][
                    "mean_daily_bps"],
                "path_formula": per_leg[leg]["path_cost"]["formula"],
                "execution_bps_per_fill_tier2":
                    per_leg[leg]["tiers"]["2.0"][
                        "execution_spread_bps_per_fill"],
            }
            for leg in per_leg
        },
        "verdict": "PASS" if (contract is not None and not problems)
        else "FAIL",
    }


# --------------------------------------------------------------------------- #
# section 4: clocks (DST + V7 close+1 on the real grid)
# --------------------------------------------------------------------------- #
def measure_clocks(sub: dict) -> dict:
    dst = ck.dst_boundary_report()
    grid = ck.decision_grid(
        b["date"] for b in sub["etp_bars"]["VXX"])
    pairs = []
    probes = ["2018-01-24", "2021-04-22", "2024-07-23",
              "2026-09-10"]
    for p in probes:
        try:
            nxt = ck.next_session(grid, p)
            pairs.append({"decision_close": p, "executable_session":
                          nxt, "close_utc": ck.close_instant(p),
                          "verdict": "MEASURED"})
        except ck.ClockError as exc:
            pairs.append({"decision_close": p, "verdict": "NOT_RUN",
                          "error": str(exc)})
    last_grid_tail = None
    try:
        ck.next_session(grid, grid[-1])
        tail_ok = False
    except ck.ClockError as exc:
        tail_ok = True
        last_grid_tail = str(exc)
    return {
        "dst_report": dst,
        "vxx_grid_sessions": len(grid),
        "vxx_grid_first": grid[0],
        "vxx_grid_last": grid[-1],
        "close_plus_1_pairs": pairs,
        "last_session_refusal": last_grid_tail,
        "last_session_refusal_ok": tail_ok,
        "verdict": "PASS" if (dst["all_match"] and tail_ok and all(
            p["verdict"] == "MEASURED" for p in pairs)) else "FAIL",
    }


# --------------------------------------------------------------------------- #
# gate assembly
# --------------------------------------------------------------------------- #
def run_tests() -> dict:
    cmd = list(TEST_COMMAND)
    started = time.time()
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True,
                          text=True)
    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "seconds": round(time.time() - started, 2),
        "tail": proc.stdout.strip().splitlines()[-4:] if
        proc.stdout.strip() else [],
        "verdict": "PASS" if proc.returncode == 0 else "FAIL",
    }


def run(fetch_live: bool) -> int:
    started = now_utc()
    plane = pa.VolNg1Plane()
    sub = consume_substrate(plane)
    sections = {}
    sections["kernel_compat"] = measure_kernel_compat()
    sections["corp_actions"] = measure_corp_actions(sub)
    evidence, cost_sec = measure_costs(sub, fetch_live)
    sections["cost_constants"] = cost_sec
    sections["clocks"] = measure_clocks(sub)
    sections["tests"] = run_tests()

    verdict = "PASS" if all(
        s.get("verdict") == "PASS" for s in sections.values()) \
        else "FAIL"
    gate = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "cycle_id": CYCLE_ID,
        "lane": "p1",
        "measured_utc": started,
        "published_utc": now_utc(),
        "worktree": REPO_ROOT,
        "git": git_state(),
        "consumed_via_plane": {
            "etp_digests": sub["etp_digests"],
            "index_digests": sub["index_digests"],
            "price_network_pulls": 0,
            "fee_fact_network_reads": sorted(
                {v["url"] for v in evidence["legs"].values()}),
        },
        "sections": sections,
        "verdict": verdict,
    }
    write_json(GATE_PATH, gate)
    print(f"p1_gate verdict={verdict} path={GATE_PATH}")
    for name, s in sections.items():
        print(f"  {name}: {s.get('verdict')}")
    return 0 if verdict == "PASS" else 3


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-fetch", action="store_true",
                    help="reuse the committed fee-fact evidence "
                         "instead of the bounded official reads")
    args = ap.parse_args()
    try:
        return run(fetch_live=not args.no_fetch)
    except Exception as exc:  # noqa: BLE001 -- fail-closed gate
        print(f"P1 FAIL/BLOCKED: {exc!r}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
