"""PC12A journal hash-chain tamper detection, books identity on synthetic
sequences, policy skeleton (FEATURES_BLACKLIST, netting, guard, W1/W4)."""

import datetime as dt
import json

import pytest

from research.pc12a import books
from research.pc12a import journal as jr
from research.pc12a import policy as pol

UTC = dt.timezone.utc


# ---------------------------------------------------------------------------
# journal: hash chain
# ---------------------------------------------------------------------------


def _write_some_journal(path, n=6):
    with jr.JournalWriter(path, "run-test") as jw:
        for i in range(n):
            jw.write("DECISION", {
                "ts_decision_utc": f"2024-06-0{i + 1}T14:00:00Z",
                "leg_id": f"LEG-{i}", "direction_vote": 1,
                "desired_risk_units": 10_000, "outcome": "FILLED"})
        jw.write("SWAP", jr.swap_row(
            ts_utc="2024-06-02T22:00:00Z", symbol="EURUSD",
            weekday_utc="sunday", units_abs=10_000, multiplier=1,
            swap_usd=1.0, wed_x3=False, units_after=10_000))


def test_hash_chain_verifies_clean(tmp_path):
    p = str(tmp_path / "journal.jsonl")
    _write_some_journal(p)
    assert jr.verify_chain(p)["ok"] is True
    assert jr.verify_chain(p)["n_rows"] == 8  # header + 7 rows


def test_hash_chain_detects_field_tamper(tmp_path):
    p = str(tmp_path / "journal.jsonl")
    _write_some_journal(p)
    rows = jr.read_rows(p)
    rows[3]["direction_vote"] = -1           # tamper one decision row
    with open(p, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True,
                                separators=(",", ":")) + "\n")
    res = jr.verify_chain(p)
    assert res["ok"] is False
    assert res["reason"] == "row_sha256 mismatch (field tampered)"


def test_hash_chain_detects_row_removal(tmp_path):
    p = str(tmp_path / "journal.jsonl")
    _write_some_journal(p)
    rows = jr.read_rows(p)
    del rows[2]                               # truncate history
    with open(p, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True,
                                separators=(",", ":")) + "\n")
    res = jr.verify_chain(p)
    assert res["ok"] is False


def test_append_only_no_second_run(tmp_path):
    p = str(tmp_path / "journal.jsonl")
    _write_some_journal(p)
    with pytest.raises(jr.JournalError):
        jr.JournalWriter(p, "run-again")      # append-only: one run per file


def test_corrections_are_new_rows(tmp_path):
    p = str(tmp_path / "journal.jsonl")
    with jr.JournalWriter(p, "run-corr") as jw:
        first = jw.write("DECISION", {"leg_id": "L1", "outcome": "FILLED",
                                      "direction_vote": 1})
        jw.write_correction(first["seq"], "DECISION",
                            {"leg_id": "L1", "outcome": "FILLED",
                             "direction_vote": -1,
                             "corrects_row_id": None})
    rows = jr.read_rows(p)
    corr = [r for r in rows if "corrects_row_id" in r]
    assert corr and corr[0]["corrects_row_id"] == first["seq"]
    assert jr.verify_chain(p)["ok"] is True


def test_blocked_rows_reject_fill_fields(tmp_path):
    p = str(tmp_path / "journal.jsonl")
    with jr.JournalWriter(p, "run-b") as jw:
        with pytest.raises(jr.JournalError):
            jw.write("BLOCK", {"outcome": "BLOCKED_STALE",
                               "fill_price": 1.08})   # NULL discipline
        with pytest.raises(jr.JournalError):
            jw.write("BLOCK", {"outcome": "NOT_IN_ENUM"})
        jw.write("BLOCK", {"outcome": "BLOCKED_STALE",
                           "blocked_reason_detail": "E3",
                           "fill_price": None})
    assert jr.verify_chain(p)["ok"] is True


# ---------------------------------------------------------------------------
# books: identity on synthetic sequences
# ---------------------------------------------------------------------------


def test_book_identity_buy_sell_round_trip():
    b = books.Book()
    b.apply_fill("EURUSD", 100_000, 1.08438, 3.79533)
    assert b.position("EURUSD") == 100_000
    eq = b.mark_equity({"EURUSD": 1.08442})
    assert eq == pytest.approx(100_000.20467, abs=1e-6)
    b.apply_fill("EURUSD", -100_000, 1.08500, 3.79750)
    assert b.position("EURUSD") == 0
    eq2 = b.mark_equity({"EURUSD": 1.08502})
    assert eq2 == pytest.approx(100_054.40717, abs=1e-6)


def test_book_swap_debits_cash_only():
    b = books.Book()
    b.apply_fill("EURUSD", 100_000, 1.08, 3.78)
    before = b.cash_usd
    b.apply_swap(10.0)
    assert b.cash_usd == pytest.approx(before - 10.0)
    assert b.position("EURUSD") == 100_000    # units unchanged


def test_book_unavailable_never_zero():
    b = books.Book()
    b.apply_fill("USDJPY", 10_000, 155.0, 0.35)
    with pytest.raises(books.UnavailableQuote):
        b.mark_equity({})                     # missing mark -> fail closed
    with pytest.raises(books.UnavailableQuote):
        b.mark_equity({"USDJPY": None})


def test_book_multi_symbol_equity():
    b = books.Book()
    b.apply_fill("EURUSD", 50_000, 1.08, 1.89)
    b.apply_fill("USDJPY", -20_000, 155.0, 0.7)
    eq = b.mark_equity({"EURUSD": 1.09, "USDJPY": 154.0})
    expect = b.cash_usd + 50_000 * 1.09 - 20_000 * 154.0
    assert eq == pytest.approx(expect, abs=1e-9)


def test_decomposition_residual_zero_on_clean_sequence():
    # one round trip + one overnight swap, mirrors fx1+fx2 arithmetic:
    # spread_once = HALF the crossing distance per fill (2.0 + 2.0)
    fills = [  # (signed units, fill, mid_at_fill)
        (100_000, 1.08316, 1.08312),
        (-100_000, 1.08668, 1.08672)]
    final_mark = 1.0867
    gross = sum(u * (final_mark - m) for u, _, m in fills)
    spread = sum(abs(f - m) * abs(u) / 2 for u, f, m in fills)  # half-spread
    slip = 4.0
    comm = 7.59444
    swap = 70.0
    eq0, eqT = 100_000.0, 100_274.40556
    assert abs(books.decomposition_residual(
        gross, spread, slip, comm, swap, eqT - eq0)) < 5e-3


# ---------------------------------------------------------------------------
# policy: blacklist, netting, guard, standing out
# ---------------------------------------------------------------------------


def test_features_blacklist_enforced():
    pol.assert_features_lawful(["decision_count_trailing:LEG-1",
                                "pit_freshness:LEG-1"])
    for bad in ("future_data_return", "leg_in_fold_pnl",
                "regime_prediction_vix", "test_fold_selector",
                "unevidenced_input_cot", "in_fold_loss_tag",
                "consensus_surprise", "sofr_rate"):
        with pytest.raises(pol.ForbiddenFeature):
            pol.assert_features_lawful([bad])
    # the frozen list covers all six GROUPING_PROPOSAL 3.6 clauses
    assert len(pol.FEATURES_BLACKLIST) >= 6


def test_netting_truncation_and_ties():
    n = pol.Netting()
    out = n.net({"A": 60_000, "B": -40_000})
    assert out.net_target_units == 20_000
    assert not out.tie_zero
    tie = n.net({"A": 10_000, "B": -10_000})
    assert tie.net_target_units == 0 and tie.tie_zero
    capped = n.net({"A": 60_000, "B": 60_000})
    assert capped.net_target_units == 100_000           # +/-1 lot truncation
    floored = n.net({"A": -60_000, "B": -60_000})
    assert floored.net_target_units == -100_000
    assert tie.offsets["A"] == ["B"]                    # who offsets whom


def test_cost_guard_defers_non_urgent_only():
    g = pol.CostGuard(pol.CostGuardState(window_days=28, cap_usd=9.0))
    now = dt.datetime(2024, 7, 5, 20, 0, tzinfo=UTC)
    g.record_spend(dt.datetime(2024, 6, 11, 14, 0, tzinfo=UTC), 8.4)
    g.record_spend(dt.datetime(2024, 6, 28, 20, 0, tzinfo=UTC), 0.780191)
    defer = g.evaluate(now, current_units=10_000, target_units=30_000,
                       est_total_usd=1.56)
    assert defer.allow is False
    assert defer.urgency == "NON_URGENT_INCREASE"
    close = g.evaluate(now, current_units=30_000, target_units=0,
                       est_total_usd=1.56)
    assert close.allow is True and close.urgency == "RISK_REDUCING_CLOSE"
    # window roll: the 06-11 spend ages out of the 28d window
    later = dt.datetime(2024, 7, 12, 20, 0, tzinfo=UTC)
    ok = g.evaluate(later, 10_000, 30_000, 1.56)
    assert ok.allow is True
    assert ok.trailing_spend_usd == pytest.approx(0.780191, abs=1e-12)


def test_w1_w4_typed():
    assert pol.w1_check([]).code == "W1_NO_ELIGIBLE_LEGS"
    assert pol.w1_check(["L1"]) is None
    w4 = pol.w4_check({"EURUSD_mid_range": 1.08})
    assert w4 is None
    trip = pol.w4_check({"EURUSD_mid_range": 0.70})
    assert trip.code == "W4_UNSEEN_STRUCTURE"
    unk = pol.w4_check({"new_input_xyz": 1.0})
    assert unk.code == "W4_UNSEEN_STRUCTURE"


def test_eligibility_e3_stale_fail_closed():
    now = dt.datetime(2024, 6, 20, 14, 0, tzinfo=UTC)
    st = pol.LegRuntimeStats(leg_start_ts=dt.datetime(2024, 1, 1,
                                                      tzinfo=UTC))
    e = pol.Eligibility()
    v = e.evaluate("L1", st, [{"input_id": "X", "max_age_ok": False}], now)
    assert v.state == "OFF" and v.rule_id == "E3"
    ok = e.evaluate("L1", st, [{"input_id": "X", "max_age_ok": True}], now)
    assert ok.state == "ON"
