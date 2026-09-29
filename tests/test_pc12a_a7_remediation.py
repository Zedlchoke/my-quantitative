"""A7-prelaunch remediation regression tests (F-2, F-3)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.pc12a import journal as jr  # noqa: E402


def test_f2_blocked_rows_carry_null_not_zero(tmp_path):
    with jr.JournalWriter(str(tmp_path / "j.jsonl"), run_id="test-run") as w:
        row = w.write("BLOCK", {
            "sleeve_id": "X", "outcome": "BLOCKED_STALE",
            "blocked_reason_detail": "unit test"})
        r2 = w.write("NETTED_TO_ZERO", {"sleeve_id": "X",
                                        "outcome": "NETTED_TO_ZERO"})
        r3 = w.write("DEFER", {"sleeve_id": "X",
                               "outcome": "DEFERRED_COST_GUARD"})
    assert row["cash_delta_usd"] is None
    for f in jr.NULL_FILL_FIELDS:
        assert row.get(f) is None, f"{f} must be NULL on BLOCK rows"
    assert r2["cash_delta_usd"] is None and r3["cash_delta_usd"] is None


def test_f2_net_order_rows_carry_cash_delta(tmp_path):
    with jr.JournalWriter(str(tmp_path / "j.jsonl"), run_id="test-run") as w:
        row = w.write("NET_ORDER", jr.net_order_row(
            order_id="o1", order_kind="OPEN", ts_fill_utc="t", symbol="E",
            side="buy", delta_units=1000, fill_price=1.1,
            quoted_side=1.1001, mid_at_fill=1.10005, spread_once_usd=0.05,
            slip_beyond_halfspread_usd=0.02, cross_cost_usd=0.07,
            commission_usd=0.04, cell_id="C1_E_2000", u3_band_id="U3",
            venue_model="PANEL_DUKA", units_after=1000,
            contributing_legs=[], cash_delta_usd=-(1000 * 1.1 + 0.04)))
    assert row["cash_delta_usd"] == -(1000 * 1.1 + 0.04)


def test_f3_enum_contains_unavailable_fill_bar():
    assert "UNAVAILABLE_FILL_BAR" in jr.OUTCOME_ENUM


def test_f3_unavailable_path_journals_without_crash(tmp_path):
    with jr.JournalWriter(str(tmp_path / "j.jsonl"), run_id="test-run") as w:
        row = w.write("BLOCK", jr.blocked_row(
            outcome="UNAVAILABLE_FILL_BAR",
            blocked_reason_detail="no fill bar (fail-closed)",
            decision_fields={"sleeve_id": "X"}))
    assert row["outcome"] == "UNAVAILABLE_FILL_BAR"
    # and the chain verifies over such rows
    p = tmp_path / "j.jsonl"
    assert jr.verify_chain(str(p))["ok"]
