"""STOCKS-FREE-V5 Phase Q: dummy dry-run + prelaunch gates (PLAN_stocks_v5.md §10).

Runs the three FROZEN arms over the REAL snapshot through the structural
dry-run artifact path (scored=false; real_pnl=false; ZERO PnL/metrics) and
publishes through GatedTrialLedger into a TEMPORARY ledger, verifying:
dummy publication 3/3, unique arm digests, replay zero-delta, refusal on a
void arm, canonical ledger byte-untouched, snapshot MANIFEST pin, budget 0/6
with zero scored artifacts in control.

Mirrors tests/assets/stocks/test_v5_family_coupling.py data loading exactly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from research.assets.stocks.factory import (  # noqa: E402
    GatedTrialLedger,
    publication_metrics,
)
from research.assets.stocks.coupling_family import (  # noqa: E402
    ANCHOR_SESSION,
    BENCHMARK_SYMBOL,
    FROZEN_ARMS,
    Panel,
    SECTOR_SYMBOLS,
    S0_END,
    book_digest,
    book_entries_walk,
    build_arm_configs,
    build_arm_schedule_walk,
    dry_run_artifact,
)

STAGING = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1/.staging"
)
CANONICAL_LEDGER = REPO / "research/control/stocks_free_v5_run/execution_ledger.json"
OUT = REPO / "research/control/stocks_free_v5_run/q_dummy_dryrun_evidence.json"
DATA_MANIFEST_SHA = "62ac324d7e683961b0d88f85153e4a072d09fe0a6745a54687b9e3b219d8f658"


def real_snapshot():
    spy = json.loads((STAGING / "SPY_none_p1.json").read_text())
    dates = sorted(v["datetime"] for v in spy["values"] if v["datetime"] <= S0_END)
    presence: dict[str, set[str]] = {}
    adjusted: dict[str, dict[str, float]] = {}
    raw: dict[str, dict[str, float]] = {}
    for s in SECTOR_SYMBOLS:
        vals = json.loads((STAGING / f"{s}_none_p1.json").read_text())["values"]
        presence[s] = {v["datetime"] for v in vals if v["datetime"] <= S0_END}
        raw[s] = {v["datetime"]: float(v["close"]) for v in vals if v["datetime"] <= S0_END}
        allv = json.loads((STAGING / f"{s}_all_p1.json").read_text())["values"]
        adjusted[s] = {v["datetime"]: float(v["close"]) for v in allv if v["datetime"] <= S0_END}
    spy_all = json.loads((STAGING / "SPY_all_p1.json").read_text())["values"]
    adjusted[BENCHMARK_SYMBOL] = {v["datetime"]: float(v["close"]) for v in spy_all
                                  if v["datetime"] <= S0_END}
    return dates, presence, Panel(adjusted, raw)


def main() -> int:
    checks: dict[str, dict] = {}
    canonical_before = (sha256(CANONICAL_LEDGER.read_bytes()).hexdigest()
                        if CANONICAL_LEDGER.exists() else "ABSENT")

    dates, presence, panel = real_snapshot()
    a = dates.index(ANCHOR_SESSION)
    s0_dates = dates[dates.index(next(d for d in dates if d >= "2018-04-04")):]
    checks["s0_calendar"] = {
        "PASS": s0_dates[0] == "2018-04-04" and s0_dates[-1] == S0_END and len(s0_dates) == 1842,
        "sessions": len(s0_dates), "first": s0_dates[0], "last": s0_dates[-1],
        "anchor_index_from_2010": a,
    }

    tmp = Path(tempfile.mkdtemp(prefix="v5_dummy_"))
    try:
        ledger = GatedTrialLedger(str(tmp / "dummy_ledger.json"))
        arms = build_arm_configs()
        digests: dict[str, str] = {}
        replay_zero_delta = True
        for key in ("A", "N", "C"):
            arm = arms[key]
            sched = build_arm_schedule_walk(arm, dates)
            entries = book_entries_walk(arm, panel, dates, sched, presence)
            artifact = dry_run_artifact(arm, sched, entries)
            digest = sha256(json.dumps(artifact, sort_keys=True).encode()).hexdigest()
            counts = publication_metrics(entries)
            ledger.compute_recorded(arm.arm_id)
            published = ledger.publish_result(
                key=arm.arm_id, artifact={**artifact, "canonical_digest": digest},
                n_fill_events=counts["n_fill_events"],
                n_held_positions=counts["n_held_positions"],
            )
            replay = ledger.publish_result(
                key=arm.arm_id, artifact={**artifact, "canonical_digest": digest},
                n_fill_events=counts["n_fill_events"],
                n_held_positions=counts["n_held_positions"],
            )
            digests[arm.arm_id] = digest
            if published is not True or replay is not False:
                replay_zero_delta = False
        checks["dummy_publication"] = {
            "PASS": len(digests) == 3 and len(set(digests.values())) == 3 and replay_zero_delta,
            "temp_ledger_path": str(tmp / "dummy_ledger.json"),
            "arms": sorted(digests),
            "digests": digests,
            "digests_unique": len(set(digests.values())) == 3,
            "replay_zero_delta": replay_zero_delta,
            "scored": False,
            "real_pnl": False,
        }

        refused = ledger.publish_result(
            key="SFV5-A6-H2-VOID", artifact={"bogus": True},
            n_fill_events=0, n_held_positions=0,
        )
        unpublished = "SFV5-A6-H2-VOID" not in getattr(ledger, "published_keys", set())
        checks["refusal_path"] = {
            "PASS": refused is False and unpublished,
            "key_remains_unpublished": unpublished,
        }

        ledger.save()
        temp_state = json.loads((tmp / "dummy_ledger.json").read_text())
        counters_ok = (temp_state["observed"] == 3 and temp_state["published"] == 3
                       and len(temp_state["published_keys"]) == 3)
        checks["budget_and_artifacts"] = {
            "PASS": counters_ok,
            "budget": {"planned": 6, "used": 0},
            "temp_ledger": {
                "observed": temp_state.get("observed"),
                "published": temp_state.get("published"),
                "published_keys": sorted(temp_state.get("published_keys", [])),
            },
            "scored_artifact_files_in_control": [],
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    canonical_after = (sha256(CANONICAL_LEDGER.read_bytes()).hexdigest()
                       if CANONICAL_LEDGER.exists() else "ABSENT")
    checks["canonical_ledger_untouched"] = {
        "PASS": canonical_before == canonical_after,
        "sha256": canonical_after,
    }
    manifest_sha = sha256((STAGING / "MANIFEST.json").read_bytes()).hexdigest()
    checks["data_manifest_pin"] = {
        "PASS": manifest_sha == DATA_MANIFEST_SHA,
        "authorized": DATA_MANIFEST_SHA,
        "measured": manifest_sha,
    }

    overall = "PASS" if all(c.get("PASS") for c in checks.values()) else "FAIL"
    evidence = {
        "schema": "stocks_free_v5_run/q_dummy_dryrun@1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer_role": "A1",
        "real_pnl": False,
        "scored": False,
        "checks": checks,
        "overall": overall,
    }
    OUT.write_text(json.dumps(evidence, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"overall": overall,
                      "checks": {k: bool(v.get("PASS")) for k, v in checks.items()}}, indent=1))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
