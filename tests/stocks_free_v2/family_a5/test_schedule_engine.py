"""Schedule-engine tests: hand-computed books, one-event lag, ramp suppression,
fold force-flat, no-lookahead mutations, raw-vs-TR split continuity, frozen
252/200 ramp goldens, control destruction and double-generation equality.

All series are synthetic and hand-checkable; the TR arithmetic in comments is
the expected-value derivation.  SCHEDULE-ONLY: nothing here computes returns,
PnL or any scored metric.
"""

import inspect
from datetime import date, timedelta

import pytest


def small_cfg(a5, *, gate="TSMOM_SIGN", lookback=2, inverted=False, clock="MONTHLY", vol_window=2):
    """A deliberately SMALL config so every gate/vol number is hand-checkable.

    The frozen per-arm values (252/200/63/monthly-weekly) are pinned in
    test_frozen_configs.py; the engine code path here is the shared one.
    """
    return a5.schedule.ArmConfig(
        arm_id="Z5-TEST-ARM",
        arm_role="UNIT_TEST",
        spec_filename="a5_arm1_tsm12_ivol.json",
        gate=gate,
        lookback_sessions=lookback,
        inverted_sign=inverted,
        clock=clock,
        vol_window_sessions=vol_window,
    )


def three_rising(a5, sessions):
    tr = {s: a5.geo_tr_series(sessions) for s in ("A", "B", "C")}
    return tr


def padded_calendar(a5, sessions, extra=8):
    return a5.SyntheticCalendar(sessions + a5.make_sessions(sessions[-1] + timedelta(days=1), extra))


def assert_book_invariants(a5, result):
    for book in result.books:
        if book.kind == "DECISION":
            assert book.gross <= 1.0 + 1e-9
            assert book.cash_weight >= -1e-12
            assert book.cash_weight + book.gross == pytest.approx(1.0, abs=1e-9)
            for sym, w in book.targets.items():
                assert w >= -1e-12
                if sym != "CASH":
                    assert w <= 0.35 + 1e-9
        else:
            assert book.cash_weight == 1.0 and book.gross == 0.0
            assert all(v == 0.0 for k, v in book.targets.items() if k != "CASH")
        assert book.turnover_two_way >= 0.0


# --------------------------------------------------------------------------- #
# Monthly mechanics, hand-computed fold book.                                 #
# --------------------------------------------------------------------------- #


def test_monthly_mechanics_hand_computed(a5):
    """Two folds, 3 rising ETFs: 4 books with hand-derived dates and turnovers."""
    s = a5.schedule
    # 70 weekday sessions from 2018-01-01: Jan 23 + Feb 20 + Mar 22 + Apr 5
    # -> sessions span 2018-01-01 .. 2018-04-06.
    sessions = a5.make_sessions(date(2018, 1, 1), 70)
    assert sessions[-1] == date(2018, 4, 6)
    tr = three_rising(a5, sessions)
    cfg = small_cfg(a5)  # TSMOM lookback 2, monthly, vol window 2
    folds = [
        s.FoldWindow("F1", date(2018, 1, 1), date(2018, 2, 15), 5),
        s.FoldWindow("F2", date(2018, 2, 16), date(2018, 3, 30), 5),
    ]
    result = s.generate_arm_schedule(
        cfg, tr_by_symbol=tr, sessions=sessions, calendar=padded_calendar(a5, sessions),
        folds=folds, coverage_start=sessions[0],
    )

    # Exactly 4 books: 1 decision + 1 force-flat per fold.  The Feb 28 clock
    # date lies beyond F1's scored_end, and the Mar 30 decision would fill on
    # 2018-04-02 > scored_end (fills only on sessions <= scored_end) -> dropped.
    assert [b.kind for b in result.books] == ["DECISION", "FORCE_FLAT", "DECISION", "FORCE_FLAT"]

    d0, ff0, d1, ff1 = result.books
    # Book 1: monthly decision at January's last session; fill NEXT session.
    assert (d0.decision_date, d0.fill_date) == (date(2018, 1, 31), date(2018, 2, 1))
    assert d0.fold_id == "F1" and d0.scored is True
    assert d0.eligible == ("A", "B", "C")
    # Constant 1%/day returns -> std(ddof=1)=0 -> arena 0 -> g=1.0 (tie-break);
    # n=3 -> cap slack -> w_i = 1/3 exactly; cash = 0.
    for sym in ("A", "B", "C"):
        assert d0.targets[sym] == pytest.approx(1.0 / 3.0)
    assert d0.targets["CASH"] == pytest.approx(0.0, abs=1e-12)
    assert d0.gross == pytest.approx(1.0)
    assert d0.turnover_two_way == pytest.approx(1.0)  # from flat: 3 x 1/3

    # Book 2: force-flat at F1 scored_end close; liquidation turnover = gross 1.0.
    assert (ff0.decision_date, ff0.fill_date, ff0.kind) == (date(2018, 2, 15), date(2018, 2, 15), "FORCE_FLAT")
    assert ff0.cash_weight == 1.0 and ff0.turnover_two_way == pytest.approx(1.0)

    # Book 3: F2 starts FLAT, so re-establishing the book costs 1.0 again.
    assert (d1.decision_date, d1.fill_date) == (date(2018, 2, 28), date(2018, 3, 1))
    assert d1.fold_id == "F2" and d1.turnover_two_way == pytest.approx(1.0)

    assert (ff1.decision_date, ff1.fill_date) == (date(2018, 3, 30), date(2018, 3, 30))

    # Fold summaries: F1 window Jan 1..Feb 15 = 23 + 11 = 34 sessions;
    # turnover 2.0 -> 2.0 / (34/252) = 2*252/34 = 14.823529... > 6.0 ceiling.
    f1, f2 = result.fold_summaries
    assert (f1.decision_events, f1.scored_events, f1.suppressed_events) == (1, 1, 0)
    assert f1.total_two_way_turnover == pytest.approx(2.0)
    assert f1.scored_window_sessions == 34
    assert f1.years == pytest.approx(34 / 252)
    assert f1.turnover_per_year == pytest.approx(2.0 * 252 / 34)
    assert f1.within_turnover_ceiling is False  # synthetic micro-window, arithmetic only
    # F2 window Feb 16..Mar 30 = 9 + 22 = 31 sessions; per-year = 2*252/31 = 16.258...
    assert f2.scored_window_sessions == 31
    assert f2.turnover_per_year == pytest.approx(2.0 * 252 / 31)
    assert f2.within_turnover_ceiling is False
    assert result.total_two_way_turnover == pytest.approx(4.0)
    assert_book_invariants(a5, result)


def test_one_event_delay_and_no_purge_executions(a5):
    s = a5.schedule
    sessions = a5.make_sessions(date(2018, 1, 1), 70)
    tr = three_rising(a5, sessions)
    cfg = small_cfg(a5)
    folds = [s.FoldWindow("F1", date(2018, 1, 1), date(2018, 2, 15), 5),
             s.FoldWindow("F2", date(2018, 2, 16), date(2018, 3, 30), 5)]
    result = s.generate_arm_schedule(
        cfg, tr_by_symbol=tr, sessions=sessions, calendar=padded_calendar(a5, sessions),
        folds=folds, coverage_start=sessions[0],
    )
    for book in result.books:
        if book.kind in ("DECISION", "RAMP_CASH"):
            # mandatory one-event delay: fill is the NEXT session, never the signal close
            assert book.fill_date > book.decision_date
        # no execution lands inside the 5-session purge or beyond scored_end
        assert book.fill_date <= (date(2018, 2, 15) if book.fold_id == "F1" else date(2018, 3, 30))
    # the dropped Mar-30 decision never appears as a book
    assert not any(b.decision_date == date(2018, 3, 30) and b.kind == "DECISION" for b in result.books)


# --------------------------------------------------------------------------- #
# Ramp suppression to 100% cash (unscored).                                   #
# --------------------------------------------------------------------------- #


def test_ramp_suppression_before_feature_requirement(a5):
    s = a5.schedule
    sessions = a5.make_sessions(date(2018, 1, 1), 70)
    tr = three_rising(a5, sessions)
    cfg = small_cfg(a5, lookback=30)  # requirement: 31 completed sessions
    folds = [s.FoldWindow("F1", date(2018, 1, 1), date(2018, 3, 9), 5)]
    result = s.generate_arm_schedule(
        cfg, tr_by_symbol=tr, sessions=sessions, calendar=padded_calendar(a5, sessions),
        folds=folds, coverage_start=sessions[0],
    )
    # Jan 31 has 23 completed sessions (< 31) -> suppressed to 100% cash, no trades.
    # Feb 28 has 23 + 20 = 43 (>= 31) -> first allowed decision.
    ramp, dec = result.books[0], result.books[1]
    assert (ramp.kind, ramp.decision_date) == ("RAMP_CASH", date(2018, 1, 31))
    assert ramp.scored is False
    assert ramp.cash_weight == 1.0 and ramp.gross == 0.0 and ramp.turnover_two_way == 0.0
    assert (dec.kind, dec.decision_date, dec.fill_date) == ("DECISION", date(2018, 2, 28), date(2018, 3, 1))
    assert dec.gross == pytest.approx(1.0)
    summary = result.fold_summaries[0]
    assert (summary.decision_events, summary.scored_events, summary.suppressed_events) == (2, 1, 1)
    assert summary.total_two_way_turnover == pytest.approx(2.0)  # build 1.0 + force-flat 1.0
    assert_book_invariants(a5, result)


# --------------------------------------------------------------------------- #
# Frozen-config integration: 252/200 ramp goldens + control destruction.      #
# --------------------------------------------------------------------------- #


def _integration_setup(a5):
    s = a5.schedule
    # 340 weekday sessions from 2018-01-01 (holiday-free synthetic), spanning
    # 2018-01-01 .. 2019-04-19.  Cumulative completed sessions (hand sum of
    # weekday counts 23,20,22,21,23,21,22,23,20,23,22,21): through Nov 2018
    # = 240, through Dec 2018 = 261, through Sep 2018 = 195, Oct 5 2018 = 200.
    sessions = a5.make_sessions(date(2018, 1, 1), 340)
    assert sessions[-1] == date(2019, 4, 19)
    tr = {"SPY": a5.geo_tr_series(sessions), "XLK": a5.geo_tr_series(sessions, base=50.0),
          "XLE": a5.geo_tr_series(sessions, base=200.0)}
    folds = [s.FoldWindow("S0_FOLD_1", date(2018, 1, 1), date(2019, 3, 29), 5)]
    return sessions, tr, folds


def test_frozen_anchor_252_ramp_golden_and_invariants(a5):
    s = a5.schedule
    sessions, tr, folds = _integration_setup(a5)
    result = s.generate_arm_schedule(
        s.ARM_CONFIG_ANCHOR, tr_by_symbol=tr, sessions=sessions,
        calendar=padded_calendar(a5, sessions), folds=folds, coverage_start=sessions[0],
    )
    assert_book_invariants(a5, result)
    decisions = [b for b in result.books if b.kind == "DECISION"]
    ramps = [b for b in result.books if b.kind == "RAMP_CASH"]
    # 252-session TSMOM needs TR(t-252), i.e. 253 points: first allowed monthly
    # decision is Dec 2018 (240 < 253 <= 261); Jan..Nov 2018 are suppressed.
    assert len(ramps) == 11
    assert all(r.cash_weight == 1.0 and r.turnover_two_way == 0.0 and r.scored is False for r in ramps)
    assert [r.decision_date.month for r in ramps] == list(range(1, 12))
    # Dec-31 decision fills on the next synthetic session (2019-01-01, Monday —
    # the synthetic calendar is deliberately holiday-free); the Mar-29-2019
    # clock date would fill 2019-04-01 > scored_end, so it is dropped.
    assert decisions[0].decision_date == date(2018, 12, 31)
    assert decisions[0].fill_date == date(2019, 1, 1)
    assert decisions[0].eligible == ("SPY", "XLE", "XLK")
    # constant 1%/day returns -> sigma 0 -> g = 1.0; n=3 -> 1/3 each, no cap bind
    for sym in ("SPY", "XLK", "XLE"):
        assert decisions[0].targets[sym] == pytest.approx(1.0 / 3.0)
    assert decisions[0].gross == pytest.approx(1.0)
    # sticky monthly state: identical books after the first -> zero-turnover events
    assert [d.turnover_two_way for d in decisions] == [pytest.approx(1.0), 0.0, 0.0]
    assert len(decisions) == 3
    force_flat = result.books[-1]
    assert (force_flat.kind, force_flat.decision_date) == ("FORCE_FLAT", date(2019, 3, 29))
    assert force_flat.turnover_two_way == pytest.approx(1.0)
    assert result.total_two_way_turnover == pytest.approx(2.0)


def test_frozen_control_destroyed_on_universal_uptrend(a5):
    # Control-destruction fixture: with EVERY ETF in a 12m uptrend (m > 0), the
    # inverted control (eligible iff m < 0) holds NOTHING while the anchor is
    # fully invested — same data, same machinery, only the gate sign differs.
    s = a5.schedule
    sessions, tr, folds = _integration_setup(a5)
    control = s.generate_arm_schedule(
        s.ARM_CONFIG_CONTROL, tr_by_symbol=tr, sessions=sessions,
        calendar=padded_calendar(a5, sessions), folds=folds, coverage_start=sessions[0],
    )
    anchor = s.generate_arm_schedule(
        s.ARM_CONFIG_ANCHOR, tr_by_symbol=tr, sessions=sessions,
        calendar=padded_calendar(a5, sessions), folds=folds, coverage_start=sessions[0],
    )
    c_dec = [b for b in control.books if b.kind == "DECISION"]
    a_dec = [b for b in anchor.books if b.kind == "DECISION"]
    assert [b.decision_date for b in c_dec] == [b.decision_date for b in a_dec]  # same clock/ramp
    assert all(b.eligible == () and b.cash_weight == 1.0 and b.gross == 0.0 for b in c_dec)
    assert all(b.gross == pytest.approx(1.0) for b in a_dec)
    assert control.total_two_way_turnover == pytest.approx(0.0)  # flat -> flat, no trades
    assert_book_invariants(a5, control)


def test_frozen_neighbour_200_weekly_ramp_golden(a5):
    s = a5.schedule
    sessions, tr, folds = _integration_setup(a5)
    result = s.generate_arm_schedule(
        s.ARM_CONFIG_NEIGHBOUR, tr_by_symbol=tr, sessions=sessions,
        calendar=padded_calendar(a5, sessions), folds=folds, coverage_start=sessions[0],
    )
    assert_book_invariants(a5, result)
    ramps = [b for b in result.books if b.kind == "RAMP_CASH"]
    decisions = [b for b in result.books if b.kind == "DECISION"]
    # SMA200 needs 200 completed sessions inclusive of t.  Hand sum: 195
    # sessions through Fri 2018-09-28; Oct 1..5 are sessions 196..200, so the
    # first allowed WEEKLY decision is Fri 2018-10-05 (39 weeks suppressed).
    assert len(ramps) == 39
    assert decisions[0].decision_date == date(2018, 10, 5)
    assert decisions[0].fill_date == date(2018, 10, 8)  # next Monday
    assert decisions[0].eligible == ("SPY", "XLE", "XLK")
    for sym in ("SPY", "XLK", "XLE"):
        assert decisions[0].targets[sym] == pytest.approx(1.0 / 3.0)
    # weekly maintenance on a sticky SMA state: zero turnover after entry
    assert all(d.turnover_two_way == 0.0 for d in decisions[1:])
    # Fri Oct 5 2018 .. Fri Mar 22 2019: the Mar-29 clock date would fill
    # 2019-04-01 > scored_end, so it is dropped (fills only <= scored_end).
    assert len(decisions) == 25
    assert result.books[-1].kind == "FORCE_FLAT"


def test_control_sign_complement_with_flat_tiebreak_symbol(a5):
    """Mixed fixture: anchor buys m>0, control buys m<0, m==0 in neither."""
    s = a5.schedule
    sessions = a5.make_sessions(date(2018, 1, 1), 70)
    tr = {
        "A": a5.geo_tr_series(sessions, daily=1.01),   # m = 1.01^2 - 1 > 0
        "Z": a5.geo_tr_series(sessions, daily=0.99),   # m = 0.99^2 - 1 < 0
        "E": {d: 100.0 for d in sessions},             # m = 0 exactly -> ineligible both
    }
    folds = [s.FoldWindow("F1", date(2018, 1, 1), date(2018, 2, 15), 5)]
    kw = dict(tr_by_symbol=tr, sessions=sessions, calendar=padded_calendar(a5, sessions),
              folds=folds, coverage_start=sessions[0])
    anchor = s.generate_arm_schedule(small_cfg(a5), **kw)
    control = s.generate_arm_schedule(small_cfg(a5, inverted=True), **kw)
    a0, c0 = anchor.books[0], control.books[0]
    assert a0.eligible == ("A",) and c0.eligible == ("Z",)
    assert set(a0.eligible) | set(c0.eligible) == {"A", "Z"}
    assert "E" not in a0.eligible and "E" not in c0.eligible
    # n=1: cap binds at 0.35; sigma 0 -> g=1 -> w=0.35, cash 0.65 (residual to cash)
    assert a0.targets["A"] == pytest.approx(0.35) and a0.targets["CASH"] == pytest.approx(0.65)
    assert c0.targets["Z"] == pytest.approx(0.35) and c0.targets["CASH"] == pytest.approx(0.65)
    assert a0.targets["Z"] == 0.0 and c0.targets["A"] == 0.0
    # force-flat liquidations equal each book's gross 0.35
    assert anchor.books[1].turnover_two_way == pytest.approx(0.35)
    assert control.books[1].turnover_two_way == pytest.approx(0.35)
    assert_book_invariants(a5, anchor)
    assert_book_invariants(a5, control)


# --------------------------------------------------------------------------- #
# No-lookahead mutation tests.                                                #
# --------------------------------------------------------------------------- #


def _baseline(a5):
    s = a5.schedule
    sessions = a5.make_sessions(date(2018, 1, 1), 70)
    tr = three_rising(a5, sessions)
    folds = [s.FoldWindow("F1", date(2018, 1, 1), date(2018, 2, 15), 5),
             s.FoldWindow("F2", date(2018, 2, 16), date(2018, 3, 30), 5)]
    result = s.generate_arm_schedule(
        small_cfg(a5), tr_by_symbol=tr, sessions=sessions,
        calendar=padded_calendar(a5, sessions), folds=folds, coverage_start=sessions[0],
    )
    return sessions, tr, folds, result


def test_mutating_future_and_fill_session_data_cannot_change_books(a5):
    s = a5.schedule
    sessions, tr, folds, baseline = _baseline(a5)
    last_decision = date(2018, 2, 28)

    # (a) shock ALL series strictly after the last decision date
    future = {sym: {d: (v * 10.0 if d > last_decision else v) for d, v in m.items()} for sym, m in tr.items()}
    r_a = s.generate_arm_schedule(small_cfg(a5), tr_by_symbol=future, sessions=sessions,
                                  calendar=padded_calendar(a5, sessions), folds=folds,
                                  coverage_start=sessions[0])
    assert r_a.to_dict() == baseline.to_dict()

    # (b) shock ONLY the Jan-31 decision's fill session (2018-02-01): a decision
    # must never see its own fill-session data.
    fill_day = {sym: {d: (v * 2.0 if d == date(2018, 2, 1) else v) for d, v in m.items()} for sym, m in tr.items()}
    r_b = s.generate_arm_schedule(small_cfg(a5), tr_by_symbol=fill_day, sessions=sessions,
                                  calendar=padded_calendar(a5, sessions), folds=folds,
                                  coverage_start=sessions[0])
    assert r_b.to_dict() == baseline.to_dict()


def test_mutating_used_history_does_change_books(a5):
    # Guard against a vacuous invariance: doubling A's TR at 2018-01-29 (inside
    # the Jan-31 decision's momentum/vol window) must move the book.
    s = a5.schedule
    sessions, tr, folds, baseline = _baseline(a5)
    past = dict(tr)
    past["A"] = {d: (v * 2.0 if d == date(2018, 1, 29) else v) for d, v in tr["A"].items()}
    r = s.generate_arm_schedule(small_cfg(a5), tr_by_symbol=past, sessions=sessions,
                                calendar=padded_calendar(a5, sessions), folds=folds,
                                coverage_start=sessions[0])
    assert r.to_dict() != baseline.to_dict()


# --------------------------------------------------------------------------- #
# Double-generation equality + deterministic serialization.                   #
# --------------------------------------------------------------------------- #


def test_double_generation_equality_and_digest_binding(a5):
    import json

    s = a5.schedule
    sessions, tr, folds, first = _baseline(a5)
    second = s.generate_arm_schedule(
        small_cfg(a5), tr_by_symbol=tr, sessions=sessions,
        calendar=padded_calendar(a5, sessions), folds=folds, coverage_start=sessions[0],
    )
    assert first == second
    assert first.to_dict() == second.to_dict()
    assert json.dumps(first.to_dict(), sort_keys=True) == json.dumps(second.to_dict(), sort_keys=True)
    # the result carries the digest of the config that produced it
    assert first.config_digest == s.arm_config_digest(small_cfg(a5))


# --------------------------------------------------------------------------- #
# Raw-vs-TR separation: 2:1 split step proves TR continuity.                  #
# --------------------------------------------------------------------------- #


def test_split_factor_tr_continuity_and_gate_equivalence(a5):
    """Raw closes halve at the split; factor-adjusted TR is unchanged; a gate
    on the split-reconstructed TR is bit-identical to the split-free gate,
    while a raw-close momentum would be corrupted by ~-50%."""
    s = a5.schedule
    sessions = a5.make_sessions(date(2018, 1, 1), 60)
    split_idx = 40
    raw, factor, tr_split, tr_free = {}, {}, {}, {}
    for i, d in enumerate(sessions):
        raw[d] = (50.0 + 0.5 * i) / (2.0 if i >= split_idx else 1.0)  # 2:1 split at i=40
        factor[d] = 2.0 if i >= split_idx else 1.0
        tr_split[d] = raw[d] * factor[d]  # amended FD2: raw x issuer-confirmed split factor
        tr_free[d] = 50.0 + 0.5 * i
    d40, d39 = sessions[40], sessions[39]
    # raw price halves across the split (35.0 / 69.5 = 0.5036...)
    assert raw[d40] == pytest.approx(35.0) and raw[d39] == pytest.approx(69.5)
    assert raw[d40] / raw[d39] < 0.51
    # TR chain is continuous through the split: same growth as the unsplit series
    assert tr_split[d40] == pytest.approx(tr_free[d40]) == pytest.approx(70.0)
    assert tr_split[d40] / tr_split[d39] == pytest.approx(tr_free[d40] / tr_free[d39])

    # signal level: the split WOULD corrupt a raw-close 12m-style momentum...
    sig = a5.signals
    d_last = sessions[59]
    raw_mom = raw[d_last] / raw[sessions[29]] - 1.0
    tr_mom = tr_split[d_last] / tr_split[sessions[29]] - 1.0
    assert raw_mom < 0.0 < tr_mom  # raw sees ~-50%; TR sees the true uptrend

    # engine level: gates/books on split-reconstructed TR == split-free TR
    cfg = small_cfg(a5, gate="SMA_ABOVE", lookback=10)
    folds = [s.FoldWindow("F1", date(2018, 1, 1), sessions[-1], 5)]
    cal = padded_calendar(a5, sessions)
    r_split = s.generate_arm_schedule(cfg, tr_by_symbol={"S": tr_split}, sessions=sessions,
                                      calendar=cal, folds=folds, coverage_start=sessions[0])
    r_free = s.generate_arm_schedule(cfg, tr_by_symbol={"S": tr_free}, sessions=sessions,
                                     calendar=cal, folds=folds, coverage_start=sessions[0])
    assert r_split.to_dict() == r_free.to_dict()
    assert any(b.eligible == ("S",) for b in r_split.books if b.kind == "DECISION")


def test_engine_takes_no_raw_price_input(a5):
    # Structural raw/TR separation: the shared code path consumes ONLY the
    # issuer-reconstructed TR chains (plus sessions/calendar/folds); there is
    # no raw-close input anywhere in the schedule API.
    params = set(inspect.signature(a5.schedule.generate_arm_schedule).parameters)
    assert params == {"config", "tr_by_symbol", "sessions", "calendar", "folds", "coverage_start"}
    assert not any("raw" in p for p in params)


def test_engine_rejects_sessions_before_coverage_start(a5):
    s = a5.schedule
    sessions = a5.make_sessions(date(2018, 1, 1), 70)
    tr = three_rising(a5, sessions)
    with pytest.raises(ValueError):
        s.generate_arm_schedule(small_cfg(a5), tr_by_symbol=tr, sessions=sessions,
                                calendar=padded_calendar(a5, sessions),
                                folds=[s.FoldWindow("F1", date(2018, 1, 1), date(2018, 2, 15), 5)],
                                coverage_start=date(2018, 2, 1))  # sessions predate coverage
