"""PC12A dry-run engine end-to-end on SYNTHETIC panels: determinism
(byte-identical journals), leak scan (RGC-INC-1), report shape, chain.

The real-panel 8-week smoke is run by the lane (not by pytest) and its
numbers land in the handoff; these tests pin the engine's laws on a
synthetic tree so the suite is hermetic and fast.
"""

import datetime as dt
import json
import os
import pathlib

import numpy as np
import pytest

from research.pc12a import journal as jr
from research.pc12a import legs as _legs
from research.pc12a import panels as _panels
from research.pc12a import run_dry as rd

SYMS = ("EURUSD", "GBPUSD", "USDJPY")
MID = {"EURUSD": 1.0850, "GBPUSD": 1.2700, "USDJPY": 155.50}


def _build_synthetic_tree(root: pathlib.Path, start: dt.date,
                          end: dt.date) -> None:
    for sym in SYMS:
        for side in ("BID", "ASK"):
            (root / sym / side).mkdir(parents=True, exist_ok=True)
    d = start
    while d <= end:
        for i, sym in enumerate(SYMS):
            seed = d.toordinal() * 10 + i
            # weekends: carry-forward days (zero volume)
            weekend = d.weekday() >= 5
            if weekend:
                n = _panels.RECORDS_PER_DAY
                vol = np.zeros(n)
            else:
                vol = None
            bid, ask = _panels.synthetic_day_bytes(
                sym, d, mid_level=MID[sym], vol_pattern=vol, seed=seed)
            (root / sym / "BID" / f"{d.isoformat()}.bi5").write_bytes(bid)
            (root / sym / "ASK" / f"{d.isoformat()}.bi5").write_bytes(ask)
        d += dt.timedelta(days=1)


@pytest.fixture(scope="module")
def synthetic_env(tmp_path_factory):
    """A synthetic panel tree + legs config (9 VOLPROF + GBPUSD-S027)."""
    base = tmp_path_factory.mktemp("pc12a_synth")
    root = base / "panels"
    # window 10 days; VOLPROF warmup 25 trading days ~ 47 calendar days
    _build_synthetic_tree(root, dt.date(2024, 5, 1), dt.date(2024, 6, 18))
    legs_dir = base / "legs"
    legs_dir.mkdir()
    keep = {"GBPUSD-S027"}
    for cfg in _legs.default_leg_configs():
        lid = cfg.get("class_candidate_id") or cfg["corpus_gid"]
        if lid in keep or cfg["sleeve_id"] == "POOL_B_VOLPROF":
            (legs_dir / f"{lid}.json").write_text(json.dumps(cfg))
    return {"root": root, "legs": str(legs_dir), "base": base,
            "env": {"PC12A_PANEL_ROOTS": json.dumps(
                {s: str(root / s) for s in SYMS})}}


def _run(out_dir: str, env: dict, legs: str) -> int:
    import subprocess
    import sys

    exe = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"
    worktree = pathlib.Path(__file__).resolve().parent.parent
    e = dict(os.environ)
    e.update(env)
    r = subprocess.run(
        [exe, "-m", "research.pc12a.run_dry", "--legs", legs,
         "--window", "2024-06-05,2024-06-18", "--out", out_dir],
        cwd=str(worktree), env=e, capture_output=True, text=True,
        timeout=540)
    assert r.returncode == 0, r.stderr[-3000:]
    return r.returncode


def test_dry_run_deterministic_and_clean(synthetic_env, tmp_path):
    out1 = str(tmp_path / "run1")
    out2 = str(tmp_path / "run2")
    _run(out1, synthetic_env["env"], synthetic_env["legs"])
    _run(out2, synthetic_env["env"], synthetic_env["legs"])
    j1 = (pathlib.Path(out1) / "journal.jsonl").read_bytes()
    j2 = (pathlib.Path(out2) / "journal.jsonl").read_bytes()
    assert j1 == j2, "two identical dry runs must be byte-identical"

    r1 = json.loads((pathlib.Path(out1) / "DRY_RUN_REPORT.json").read_text())
    r2 = json.loads((pathlib.Path(out2) / "DRY_RUN_REPORT.json").read_text())
    r1.pop("elapsed_seconds")
    r2.pop("elapsed_seconds")
    assert r1 == r2

    # RGC-INC-1 leak scan: forbidden keys absent from BOTH artifacts
    assert r1["leak_scan"]["clean"] is True
    low = (pathlib.Path(out1) / "journal.jsonl").read_text().lower()
    for key in rd.FORBIDDEN_KEYS:
        assert key not in low

    # report shape: ONLY decision counts, votes, fills-by-outcome, blocked
    # histogram, cost bills, row count, digests, elapsed
    for leg, st in r1["legs"].items():
        assert set(st) <= {"decisions", "votes", "fills_by_outcome",
                           "outcome_exposed_label", "family_id",
                           "mech_key", "symbol"}
        assert st["decisions"] == sum(st["votes"].values())
    assert set(r1["cost_bill_totals_usd"]) == {
        "spread_once", "slip", "slip_gap_excess", "commission", "swap"}
    assert r1["journal_row_count"] == jr.verify_chain(
        str(pathlib.Path(out1) / "journal.jsonl"))["n_rows"]
    # every journal row carries the leg's outcome-exposed label
    rows = jr.read_rows(str(pathlib.Path(out1) / "journal.jsonl"))
    labelled = [r for r in rows
                if "outcome_exposed_label" in r]
    assert labelled and all(r["outcome_exposed_label"] for r in labelled)


def test_dry_run_journal_chain_and_outcomes(synthetic_env, tmp_path):
    out = str(tmp_path / "run3")
    _run(out, synthetic_env["env"], synthetic_env["legs"])
    jp = str(pathlib.Path(out) / "journal.jsonl")
    assert jr.verify_chain(jp)["ok"] is True
    rows = jr.read_rows(jp)
    kinds = {r["row_kind"] for r in rows}
    assert kinds <= set(jr.ROW_KINDS)
    # blocked/deferred/tie rows: fill/cost fields NULL, zero cash effect
    for r in rows:
        if r["row_kind"] in ("BLOCK", "DEFER", "NETTED_TO_ZERO"):
            for f in jr.NULL_FILL_FIELDS:
                # A7-prelaunch F-2: cash_delta_usd is NULL (never 0.0) on
                # blocked/deferred/tie rows — zero cash EFFECT, absent field.
                assert r.get(f) is None
    # NET_ORDER rows satisfy the spread-once identity per fill
    for r in rows:
        if r["row_kind"] == "NET_ORDER":
            assert abs((r["spread_once_usd"]
                        + r["slip_beyond_halfspread_usd"])
                       - r["cross_cost_usd"]) < 1e-9
    # swap rows only on accrual-event weekdays with Wed x3 flags
    for r in rows:
        if r["row_kind"] == "SWAP":
            assert r["weekday_utc"] in ("sunday", "monday", "tuesday",
                                        "wednesday", "thursday")
            assert r["wed_x3"] == (r["weekday_utc"] == "wednesday")


def test_leak_scan_catches_forbidden_keys():
    scan = rd.leak_scan('{"gross_pnl_usd": 1.0}')
    assert scan["clean"] is False and "pnl" in scan["keys"]
    scan2 = rd.leak_scan('{"sharpe": 2, "max_drawdown": 3}')
    assert {"sharpe", "drawdown"} <= set(scan2["keys"])
    scan3 = rd.leak_scan('{"spread_once": 1.0, "decisions": 5}')
    assert scan3["clean"] is True
