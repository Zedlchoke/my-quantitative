"""PSV1 scored-run wrapper: heavy lock -> M3 ingest verification -> scored
run -> release (finally). One atomic process; plan §15/§17; evaluation_freeze
scored_run_ingest_verification (A7-M3 remediation, binding)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(REPO / "research"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance import heavy_lock  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "runtime" / "scored"


def main() -> int:
    handle = heavy_lock.acquire(
        cycle_id="PHASE-STRATEGY-V1",
        role="A1-SCORED-RUN",
        worktree=str(REPO / ".worktrees/phase-strategy-v1/integration"),
        command=["run_scored_under_lock.py", "--mode", "scored"],
        expected_artifacts=[str(OUT / "scored_ledger.json")],
    )
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        import verify_ingest
        ver = verify_ingest.verify()
        (OUT / "ingest_verification.json").write_text(json.dumps(ver, indent=1))
        if ver["verdict"] != "PASS":
            print(json.dumps({"verdict": "BLOCKED_DATA_OR_SELECTION",
                              "ingest_verification": ver}))
            return 2
        import run_scored
        ledger = run_scored.run_scored(OUT)
        print(json.dumps({"candidates_passing_G1_G7": ledger["candidates_passing_G1_G7"],
                          "budget_cells_consumed": ledger["budget_cells_consumed"],
                          "observed_scored_denominator": ledger["observed_scored_denominator"],
                          "ingest_verified": ver["verified"]}))
        handle.release(status="FINISHED", note="scored run complete")
        return 0
    except Exception as exc:  # noqa: BLE001 — fail loud, release lock cleanly
        handle.release(status="FAILED", note=f"{type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
