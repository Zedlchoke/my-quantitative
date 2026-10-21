"""W0 acceptance replay (PAPERDESK-FIXALL-NCAA-V1): the two live-stuck NBA
bets (401909088, 401909090) must settle through the NORMAL settle path
(settle_pass -> fetch_espn_results -> cmd_settle) once W0.1 identity goes
through the pinned team-name crosswalk.

Runs on a byte-copy of the production ledger inside a throwaway data root —
the production ledger is NEVER opened for writing. The ESPN transport is
served from the REAL journaled evidence bytes captured on the live desk
(ops/results/evidence/espn_nba_20261020_2026-10-21T073429Z.json — the last
snapshot in which BOTH events are FINAL), so this is an offline replay of
exactly what the live runner would have fetched.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import execute                       # noqa: E402
from research.papertrade_exec import results_fetch as RF           # noqa: E402
from research.papertrade_exec.ops_service import OpsService        # noqa: E402

PROD_LEDGER = Path("/Users/hoangminhlong/.my-quantitative-data/"
                   "sports-papertrade-exec-v1/ledger/paper_ledger.jsonl")
EVIDENCE_BOARD = Path("/Users/hoangminhlong/.my-quantitative-data/"
                      "sports-papertrade-exec-v1/ops/results/evidence/"
                      "espn_nba_20261020_2026-10-21T073429Z.json")
STUCK = ("401909088", "401909090")


def main() -> int:
    board = EVIDENCE_BOARD.read_bytes()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "ledger").mkdir(parents=True)
        shutil.copy2(PROD_LEDGER, root / "ledger" / "paper_ledger.jsonl")
        served = {"count": 0}

        def fake_espn_get(path_league: str, date_compact: str):
            served["count"] += 1
            return json.loads(board), board, 200

        RF._espn_get = fake_espn_get
        svc = OpsService(data_root=root, sandbox=False, serve=False, once=True)
        out = svc.settle_pass()

        rows = [json.loads(l) for l in
                (root / "ledger" / "paper_ledger.jsonl").read_text()
                .splitlines() if l.strip()]
        stl = {r["match_id"]: r for r in rows if r["type"] == "SETTLEMENT"}
        record = {
            "acceptance": "W0 auto-settle replay of the two live-stuck NBA bets",
            "mode": "REAL settle path on a byte-copy ledger; ESPN transport "
                    "served from real journaled evidence bytes",
            "espn_transport_calls": served["count"],
            "settle_pass_out": out,
            "stuck_bets": STUCK,
            "settlements": {
                mid: {"result": stl[mid]["result"],
                      "outcome_for_leg": stl[mid]["outcome_for_leg"],
                      "pnl_cents": stl[mid]["pnl_cents"],
                      "source_ref": stl[mid]["source_ref"][:160]}
                for mid in STUCK if mid in stl},
            "chain_verify_after": None,
            "production_ledger_untouched": True,
        }
        core = execute.load_pinned_core(roots={})
        led = core.ledger.PaperLedger(
            root / "ledger" / "paper_ledger.jsonl").load()
        ok, errs = led.verify_chain()
        record["chain_verify_after"] = {"ok": ok, "errors": errs[:3]}

        missing = [m for m in STUCK if m not in stl]
        record["verdict"] = "PASS" if (not missing and ok and
                                       out["settled"] == 2) else "FAIL"
        out_path = REPO / ("research/control/PAPERDESK-FIXALL-NCAA-V1/"
                           "evidence/W0_ACCEPTANCE_REPLAY_2026-10-21.json")
        out_path.write_text(json.dumps(record, indent=1, sort_keys=True))
        print(json.dumps(record, indent=1, sort_keys=True)[:2000])
        return 0 if record["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
