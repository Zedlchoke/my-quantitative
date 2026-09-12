#!/usr/bin/env python
"""VOL-NG1 P2 runner (task vol-ng1-p2-feasibility, Q-6 no-PnL).

Consumes ONLY the committed P0 frozen substrate through the cycle's
read-only plane adapter (NO network at all), builds the event-adjusted
ETP closes through ``research.assets.vol_ng1.corp_actions`` (the only
lawful ETP consumption layer), and measures the FROZEN P2 floors:

- A4 term-structure slope lane census (bookable instants + coverage);
- A5 risk-premium lane realized-proxy determination (FEASIBLE or
  BLOCKED -- BLOCKED is a valid outcome; cycle proceeds A4-only);
- worst-case round-trip cost ceilings per leg from the FROZEN
  ``p1_cost_contract.json`` (cost bounds only -- NO PnL numbers).

Publishes ``p2_gate.json`` (per-lane frozen-vs-measured + verdicts +
BLOCKED paths + artifact sha256 citations + pytest record) and exits
0 = measured-clean (A4 PASS), 3 = FAIL/BLOCKED, 4 = usage.

NO proposals, NO signal design, NO scoring, NO PnL/outcome numbers
anywhere.
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

from research.assets.vol_ng1 import census as vc           # noqa: E402
from research.assets.vol_ng1 import corp_actions as ca     # noqa: E402
from research.assets.vol_ng1 import feasibility as fb      # noqa: E402
from research.assets.vol_ng1 import plane_adapter as pa    # noqa: E402

SCHEMA = "vol_ng1_run/p2_gate@1"
TASK_ID = "vol-ng1-p2-feasibility"
CYCLE_ID = "VOL-NG1"

OUT_DIR = os.path.join(REPO_ROOT, "research", "control", "vol_ng1_run")
GATE_PATH = os.path.join(OUT_DIR, "p2_gate.json")
P0_GATE_PATH = os.path.join(OUT_DIR, "p0_gate.json")
P1_GATE_PATH = os.path.join(OUT_DIR, "p1_gate.json")
CONTRACT_PATH = os.path.join(OUT_DIR, "p1_cost_contract.json")

CBOE_ENTRIES = {
    "VIX": "VIX_History.csv",
    "VIX9D": "VIX9D_History.csv",
    "VIX3M": "VIX3M_History.csv",
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
                "-m", "pytest", "tests/test_vol_ng1_p2.py", "-q")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def consume_substrate(plane) -> dict:
    """Read-only plane consumption of the frozen census inputs."""
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


def event_adjusted_legs(sub: dict) -> tuple[dict[str, dict[str, float]], dict]:
    """Build every ETP leg's event-adjusted close series through the
    ONLY lawful layer (corp_actions) and re-measure the continuity law.
    Any uncovered step / inventory mismatch / large mechanical residual
    fails closed BEFORE the census runs."""
    inventory = ca.load_inventory()
    table = ca.build_event_table(inventory)
    mismatches = ca.inventory_mismatches(inventory, table)
    if mismatches:
        raise ca.CorpActionError(f"event table mismatches: {mismatches}")
    adj: dict[str, dict[str, float]] = {}
    per_leg = {}
    max_residual = 0.0
    for leg in fb.GRID_ETP_LEGS:
        bars = sub["etp_bars"][leg]
        events = table[leg]
        ca.require_coverage(leg, events)
        uncovered = ca.scan_uncovered_steps(bars, events)
        if uncovered:
            raise ca.CorpActionError(
                f"{leg}: uncovered raw steps {uncovered} (fail-closed)")
        res = ca.continuity_residuals(bars, events)
        max_residual = max(max_residual,
                           res["max_abs_mechanical_residual"])
        adj[leg] = ca.event_adjusted_closes(bars, events)
        per_leg[leg] = {
            "events_applied": sorted(
                (e["date"], e["kind"]) for e in events),
            "max_abs_mechanical_residual":
                res["max_abs_mechanical_residual"],
        }
    if max_residual >= 1e-4:
        raise ca.CorpActionError(
            f"max mechanical continuity residual {max_residual} >= 1e-4")
    return adj, {"per_leg": per_leg,
                 "max_abs_mechanical_residual": max_residual,
                 "inventory_total_steps": inventory["total_steps"],
                 "consumption_law": "ETP legs consumed ONLY through "
                                    "corp_actions.event_adjusted_closes "
                                    "(never raw, never vendor-adjusted)"}


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


def run() -> int:
    started = now_utc()
    plane = pa.VolNg1Plane()
    sub = consume_substrate(plane)
    adj, evlaw = event_adjusted_legs(sub)

    grid = fb.common_grid(sub["index_closes"], adj)
    a4 = fb.a4_lane(grid)
    granted = {s: plane.verdict(s) for s in sorted(pa.FROZEN_TARGET_SET)}
    a5 = fb.a5_lane(grid, adj[fb.PROXY_LEG], granted)
    if not os.path.isfile(CONTRACT_PATH):
        raise FileNotFoundError(f"frozen cost contract missing: "
                                f"{CONTRACT_PATH}")
    with open(CONTRACT_PATH, "r", encoding="utf-8") as fh:
        contract = json.load(fh)
    contract_sha = sha256_file(CONTRACT_PATH)
    ceilings = fb.cost_ceilings(contract)

    tests = run_tests()

    costs_ok = (len(ceilings["legs"]) == len(fb.GRID_ETP_LEGS)
                and all(v["round_trip_cost_ceiling_bps"] > 0
                        for v in ceilings["legs"].values()))
    sections = {
        "a4_term_structure_slope": a4,
        "a5_risk_premium": a5,
        "cost_ceilings": {
            "schema": ceilings["schema"],
            "source": ceilings["source"],
            "contract_sha256_cited": contract_sha,
            "q8_law": ceilings["q8_law"],
            "q16_law": ceilings["q16_law"],
            "execution_note": ceilings["execution_note"],
            "holding_conventions_declared": {
                "SHORT": fb.HOLD_SESSIONS_BY_BUCKET["SHORT"],
                "MID": fb.HOLD_SESSIONS_BY_BUCKET["MID"],
                "note": "each leg's own measured path day_gap "
                        "(declared before measurement, C9); verified "
                        "equal to the contract at measure time",
            },
            "legs": ceilings["legs"],
            "no_pnl_note": "cost ceilings are bounds, not expectations "
                           "and not PnL numbers (Q-6 no-PnL law)",
            "verdict": "PASS" if costs_ok else "FAIL",
        },
        "event_adjusted_layer": {**evlaw, "verdict": "PASS"},
        "tests": tests,
    }
    gate = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "cycle_id": CYCLE_ID,
        "lane": "p2",
        "question": "Q-6 feasibility (no-PnL): can each lane's frozen "
                    "floors be met on the plane-consumed, "
                    "event-adjusted substrate?",
        "measured_utc": started,
        "published_utc": now_utc(),
        "worktree": REPO_ROOT,
        "git": git_state(),
        "consumed_via_plane": {
            "etp_digests": sub["etp_digests"],
            "index_digests": sub["index_digests"],
            "network_reads": 0,
            "store_write_ops": 0,
        },
        "artifact_hashes_cited": {
            "p0_gate_json_sha256": sha256_file(P0_GATE_PATH),
            "p1_gate_json_sha256": sha256_file(P1_GATE_PATH),
            "p1_cost_contract_json_sha256": contract_sha,
        },
        "sections": sections,
        "lane_outcomes": {
            "A4": a4["verdict"],
            "A5": a5["verdict"],
            "A5_note": a5["blocked_note"],
        },
        "verdict": "PASS" if (
            a4["verdict"] == "PASS"
            and sections["cost_ceilings"]["verdict"] == "PASS"
            and sections["event_adjusted_layer"]["verdict"] == "PASS"
            and tests["verdict"] == "PASS"
            and a5["verdict"] in ("FEASIBLE", "BLOCKED")) else "FAIL",
        "verdict_note": "a5 BLOCKED is a VALID outcome (cycle proceeds "
                        "A4-only) and does not fail the gate; a4/costs/"
                        "tests must PASS for a measured-clean gate",
    }
    write_json(GATE_PATH, gate)
    print(f"p2_gate verdict={gate['verdict']} path={GATE_PATH}")
    print(f"  A4: {a4['verdict']} "
          f"(bookable={a4['bookable_instants']}, "
          f"coverage={a4['coverage_primary']})")
    print(f"  A5: {a5['verdict']} "
          f"(computable={a5['bookable_instants_state_computable']})")
    print(f"  costs: {sections['cost_ceilings']['verdict']}  "
          f"tests: {tests['verdict']}")
    return 0 if gate["verdict"] == "PASS" else 3


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    try:
        return run()
    except Exception as exc:  # noqa: BLE001 -- fail-closed gate
        print(f"P2 FAIL/BLOCKED: {exc!r}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
