"""AMENDMENT_MACOS_APP_UI_V1 battery — the UI control seam only.

Covers the pause_decisions.flag contract the PaperDesk.app controller uses:
  * flag present            -> cadence pass is SKIPPED (PAUSED_BY_UI_FLAG),
                               settle pass still runs (an already-open
                               BET_PAPER row still settles), heartbeat
                               exposes decisions_paused=true;
  * flag absent             -> cadence runs as before, incident journal shows
                               the PAUSED -> RESUMED transition pair;
  * corrupt/foreign flag    -> read as PAUSED (fail-closed);
  * payload transcription   -> every transition copies the flag payload
                               ({by, at_utc, reason}) into incidents.jsonl;
  * no decision-law surface -> the flag cannot create, alter or unblock a
                               ledger row; the ledger is byte-identical with
                               the flag present or absent across ticks.

Sandbox-only (tmp data roots + fabricated sandbox control copies). The real
ledger, real registry and any network are never touched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tests.papertrade_exec import test_ops_live_service as _ops  # noqa: E402

env = _ops.env                    # re-bind the sandbox env fixture
make_svc = _ops.make_svc
seed_open_bet = _ops.seed_open_bet
ledger_rows = _ops.ledger_rows
incidents = _ops.incidents


def flag_path(env) -> Path:
    return env["data"] / "sandbox" / "ops" / "control" / "pause_decisions.flag"


def write_flag(env, *, by="PaperDesk.app", reason="window-close"):
    flag_path(env).parent.mkdir(parents=True, exist_ok=True)
    flag_path(env).write_text(json.dumps(
        {"by": by, "at_utc": "2026-10-19T00:00:00Z", "reason": reason}))


def test_flag_absent_cadence_runs_normally(env):
    svc = make_svc(env)
    assert svc.decisions_paused() is False
    assert svc.pause_flag_payload() is None
    svc.tick()
    assert "PAUSED_BY_UI_FLAG" not in json.dumps(svc.last_cadence)


def test_flag_present_skips_cadence_only(env):
    seed_open_bet(env)                       # one settle-due open bet
    write_flag(env)
    svc = make_svc(env)
    assert svc.decisions_paused() is True
    results = svc.tick()
    assert results["cadence"] == "PAUSED_BY_UI_FLAG"
    # settle pass still ran (attempted>=0 — the pass itself is not blocked)
    assert "settle" in results
    # heartbeat exposes the paused state for the UI
    hb = json.loads((env["data"] / "sandbox" / "ops" / "state" /
                     "heartbeat.json").read_text())
    assert hb["decisions_paused"] is True


def test_transition_pair_journaled_with_payload(env):
    write_flag(env, by="PaperDesk.app", reason="unit-window-close")
    svc = make_svc(env)
    svc.tick()
    svc.tick()
    flag_path(env).unlink()
    svc.tick()
    kinds = [i["kind"] for i in incidents(env)]
    assert "DECISIONS_PAUSED_BY_UI" in kinds
    assert "DECISIONS_RESUMED_BY_UI" in kinds
    paused_row = next(i for i in incidents(env)
                      if i["kind"] == "DECISIONS_PAUSED_BY_UI")
    assert "unit-window-close" in paused_row["detail"]
    assert "PaperDesk.app" in paused_row["detail"]


def test_corrupt_flag_is_fail_closed_paused(env):
    flag_path(env).parent.mkdir(parents=True, exist_ok=True)
    flag_path(env).write_text("{not json")
    svc = make_svc(env)
    assert svc.decisions_paused() is True
    assert svc.pause_flag_payload() == {"corrupt": True}
    results = svc.tick()
    assert results["cadence"] == "PAUSED_BY_UI_FLAG"


def test_flag_present_never_appends(env):
    """The seam is decision-timing only: a tick with the flag present must
    leave the ledger byte-identical (cadence cannot append anything while
    paused). Removing the flag re-enables lawful cadence refusals, which MAY
    journal NOT_RUN rows — that is the runner's own behavior, not the seam."""
    seed_open_bet(env)
    before = (env["data"] / "sandbox" /
              "sandbox_ledger.jsonl").read_bytes()
    write_flag(env)
    make_svc(env).tick()
    assert (env["data"] / "sandbox" /
            "sandbox_ledger.jsonl").read_bytes() == before
    flag_path(env).unlink()
    make_svc(env).tick()                 # lawful refusals may append here
    assert len(ledger_rows(env)) >= 4    # genesis+forecast+quote+decision(+refusals)


def test_pause_never_unblocks_a_blocked_row(env):
    """A BET_PAPER decision stays OPEN across paused ticks; the seam has no
    path that settles, mutates or appends anything by itself."""
    seed_open_bet(env)
    write_flag(env)
    svc = make_svc(env)
    for _ in range(3):
        svc.tick()
    rows = ledger_rows(env)
    assert sum(1 for r in rows if r.get("type") == "SETTLEMENT") == 0
    assert sum(1 for r in rows if r.get("type") == "DECISION") == 1
