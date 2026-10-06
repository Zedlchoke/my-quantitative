"""REPRO: mixed-direction intents in ONE identity — FIXED state.

HISTORY (never delete): the owner-reported defect (independent audit at
d938e9a5) is recorded in REPRO_FAIL.json, committed at f1f69c8e — the
positional seam picked the runner arm from intents[0]["direction"] and made
ONE trade per identity, silently dropping the Short leg of a Long+Short
pair in the same identity (1 trial row instead of 2).

THIS script proves the FIXED state through the PRODUCTION wiring path:
intent_contract -> wiring/intent_executor (intent_packet@1) ->
exec/scored_runner_v2.py intent-mode engine -> shared ledger. Every intent
executes as ITS OWN trade: 2 trades, directions {1, -1}, per-intent
entry/exit timestamps and PnLs preserved, ONE identity row (+1 observed
denominator, not +2). SYNTHETIC inputs only; sandbox authority only; no
real governance/GO/lock.

Exit code: 0 = verdict PASS (defect fixed), 1 = still broken.
"""
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WIRING = HERE.parent / "wiring"
TESTS = HERE.parent / "tests"
sys.path.insert(0, str(WIRING.parent))
sys.path.insert(0, str(TESTS))

from wiring import intent_executor as ie               # noqa: E402
from wiring.intent_contract import normalize_intent    # noqa: E402

PY = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"

# The owner's exact mixed-direction submission (same identity, Long then
# Short) — verbatim from REPRO_FAIL.json's intents_submitted/expected rows.
iid = "FBNQ1-F1-CONT-UP-D0-S2"
SESSION_DATES = ["2023-06-13", "2023-06-14", "2023-06-15", "2023-06-16"]
SESSIONS = [{"session_date": d, "open": 0.0, "high": 0.0, "low": 0.0,
             "close": 0.0} for d in SESSION_DATES]   # timeline only; the
# intent-mode engine takes fill prices from the INTENT records, never from
# a re-encoded price series.


def mk(direction, entry_date):
    return normalize_intent(
        identity_id=iid, symbol="NQ", family="NQ-F1", direction=direction,
        entry_date=entry_date, exit_date=entry_date,
        entry_price=15110.0,
        exit_price=(15130.0 if direction == 1 else 15090.0),
        cost_tier="S2", stress=1.0, source_adapter="FomcEraAdapter",
        exit_reason="session_close",
        labels=["REPRO_MIXED_DIRECTION"])

intents = [mk(+1, "2023-06-14"), mk(-1, "2023-06-15")]   # Long then Short

with tempfile.TemporaryDirectory() as td:
    res = ie.intent_and_run(
        ie.group_intents(intents), SESSIONS,
        folds=[{"fold_id": "F1", "start_bar": 0, "end_bar": len(SESSIONS)}],
        work_dir=td, run_label="repro_mixed_fixed", python=PY)
    trials = res["trials"]
    journal = trials[0]["payload"]["journal"] if trials else []
    dirs = [t["direction"] for t in journal]
    outcome = {
        "defect": "mixed-direction intents in one identity drop the Short leg",
        "fix": "intent_packet@1 seam (wiring/intent_executor.py) + runner "
               "intent-mode engine: every intent executes as its own trade",
        "history_artifact": "REPRO_FAIL.json (committed f1f69c8e; untouched)",
        "identity_id": iid,
        "intents_submitted": [{"direction": i["direction"],
                               "entry_date": i["entry_date"]}
                              for i in intents],
        "executed_trades": [
            {"intent_seq": t["intent_seq"], "direction": t["direction"],
             "entry_ts": t["entry_ts"], "exit_ts": t["exit_ts"],
             "entry_price": t["entry_price"], "exit_price": t["exit_price"],
             "exit_reason": t["exit_reason"], "era": t["era"],
             "net_pnl_usd": t["net_pnl_usd"]} for t in journal],
        "ledger_trial_rows": len(trials),
        "ledger_directions": dirs,
        "observed_identity_count":
            res["final_status"]["observed_identity_count"],
        "expected_net_pnl_usd_each": 343.0,
        "verdict": "PASS" if (
            res["exit_code"] == 0
            and len(trials) == 1
            and len(journal) == 2
            and sorted(dirs) == [-1, 1]
            and [t["entry_ts"] for t in journal] ==
                ["2023-06-14", "2023-06-15"]
            and all(abs(t["net_pnl_usd"] - 343.0) < 1e-6 for t in journal)
            and res["final_status"]["observed_identity_count"] == 1)
            else "FAIL",
    }
    print(json.dumps(outcome, indent=1))
    (HERE / "REPRO_FIXED.json").write_text(json.dumps(outcome, indent=1))
    sys.exit(0 if outcome["verdict"] == "PASS" else 1)
