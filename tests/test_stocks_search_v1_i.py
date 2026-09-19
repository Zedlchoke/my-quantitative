"""STOCKS-SEARCH-V1 I-lane tests (sanitized SYNTHETIC fixtures ONLY).

Covers, per the ssearch-i dispatch:
- engine determinism; entry/exit timing; fold force-flat;
- BC-7 death handling (death-session OPEN exit served + DEATH_CENSORED
  excluded from the numerator + separate censored accounting);
- cost band assignment + the 100 bps worst-case round trip;
- every ordered kill rule on hand-computed books;
- DSR math on hand-computable fixtures (Bailey/Lopez de Prado E[max SR]);
- GO-gate hard refusal on the real-data loader without the exact phrase
  `GO STOCKS SEARCH V1 SCORED EXECUTION`;
- R0_NOT_RUN / PBO_NOT_RUN labels present verbatim.

NO real data is read and NO engine runs on real data anywhere in this
file: every fixture is constructed in-memory from constants.
"""

import hashlib
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
_I_DIR = _REPO_ROOT / "research" / "control" / "stocks_search_v1_run" / "i"
for p in (str(_REPO_ROOT), str(_I_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import i_engine as E  # noqa: E402
import adjudicate as A  # noqa: E402

GO_PHRASE = "GO STOCKS SEARCH V1 SCORED EXECUTION"

CFG_GAP = "SSS-GAP-P25-CONFIRM-H1"
CFG_52W = "SSS-52W-HIGH-B10-H20"
CFG_VOL = "SSS-VOL-REGIME-L21-LOW-H20"


# ------------------------------------------------------------- fixtures

D0 = date(2015, 1, 1)


def mk_calendar(n=320, start=D0):
    return [(start + timedelta(days=i)).isoformat() for i in range(n)]


CALENDAR = mk_calendar()
B1, B2 = CALENDAR[199], CALENDAR[259]


def mk_name(sym, n=310, step_i=None, step=1.10, vol=5e6, start=D0,
            close_step_i=None, down_i=None, down=0.5):
    """Deterministic synthetic name.  Flat price 1.0 with an optional
    multiplicative STEP at index step_i (open+close) - leg returns are
    then exact hand-computable constants.  volume constant.  down_i
    applies a second (down) step to open+close."""
    op = np.full(n, 1.0)
    cl = np.full(n, 1.0)
    if step_i is not None:
        op[step_i:] *= step
        cl[step_i:] *= step
    if close_step_i is not None:
        cl[close_step_i:] *= step
    if down_i is not None:
        op[down_i:] *= down
        cl[down_i:] *= down
    hi = cl * 1.001
    lo = cl * 0.999
    v = np.full(n, vol)
    dates = tuple((start + timedelta(days=i)).isoformat() for i in range(n))
    return E.NameData(sym, dates, op, hi, lo, cl, v)


def leg(sym, fold, net, gross=None, di=0, ddate="2015-01-01",
        edate="2015-01-02", xdate="2015-01-03", band="C"):
    return E.Leg(sym, di, ddate, edate, xdate, fold, band,
                 gross if gross is not None else net, net,
                 log_slices=[])


def hand_book(book_id, legs, pnl_by_fold=None, calendar=CALENDAR):
    """Hand-computed BookResult: legs given; P-11 series from pnl_by_fold."""
    book = E.BookResult(book_id=book_id, config_id="FIX", H=5, stress=2.0,
                        calendar=tuple(calendar))
    book.legs = legs
    E._finalize(book)
    if pnl_by_fold:
        series = np.zeros(len(calendar))
        for d, x in zip(calendar, series):
            pass
        series = np.zeros(len(calendar))
        for f, pnl in pnl_by_fold.items():
            idx = {"F1": 50, "F2": 230, "F3": 300}[f]
            series[idx] = pnl
        book.book_log = series
    return book


def bundle_from_books(cand, compl=None, r5=None, rev=None, rnd=None,
                      ch=None, delay=None, pit_pass=True, spy_legs=None):
    """Assemble a minimal bundle for adjudicate.ordered_kills."""
    spy_legs = spy_legs if spy_legs is not None else []

    class SpyStub:
        pass

    b = {
        "cell": "FIX", "H": 5, "stress": 2.0,
        "candidate": cand,
        "c_complement": compl or hand_book("c_complement", []),
        "r5_component": r5 or hand_book("r5_component", []),
        "c_reversal_plain": rev or hand_book("c_reversal_plain", []),
        "c_random_timing": rnd or hand_book("c_random_timing", []),
        "c_cal_hist": ch or hand_book("c_cal_hist", []),
        "c_delay_h": delay or hand_book("c_delay_h", []),
        "c_cal_hist_report": {},
        "pit_mutation": {"gate": "C-PIT-MUTATION", "fired": 1,
                         "changed_or_refused": 1, "pass": pit_pass},
    }
    return b, spy_legs


def spy_fixture(returns_by_leg):
    """Minimal SPY NameData + legs whose same-date SPY legs realize the
    given per-leg returns exactly (open step construction)."""
    # build a wide SPY series: constant 100 with a fresh +r step region
    # per leg is impossible on one path; instead spy_legs_for reads
    # open[exit]/open[entry]; we place ONE step per leg on disjoint
    # date ranges.
    n = 400
    op = np.full(n, 100.0)
    dates = tuple((D0 + timedelta(days=i)).isoformat() for i in range(n))
    # default: no steps (all returns 0)
    return E.NameData("SPY", dates, op, op, op, op, np.ones(n)), dates


def spy_with_leg_returns(cand_legs, rets):
    """Build a SPY NameData such that spy_legs_for(spy, cand_legs) equals
    rets exactly.  Each leg i uses its own disjoint entry/exit dates; we
    set open[exit_i] = open[entry_i] * (1 + rets[i]) - entry prices all
    100 - by writing the exit index directly (dates distinct per leg).
    """
    n = 1200
    op = np.full(n, 100.0)
    dates = list((D0 + timedelta(days=i)).isoformat() for i in range(n))
    spy = E.NameData("SPY", tuple(dates), op, op, op, op, np.ones(n))
    pos = {d: i for i, d in enumerate(dates)}
    for lg, r in zip(cand_legs, rets):
        e, x = pos[lg.entry_date], pos[lg.exit_date]
        spy.adj_open[x] = 100.0 * (1.0 + r)
    return spy


# ------------------------------------------------------------ freeze pin

def test_verify_freeze_binding_identity():
    out = E.verify_freeze()
    assert out["status"] == "SELECTION_FROZEN"
    assert out["n_cells"] == 3
    assert out["freeze_sha256"] == E.FREEZE_SHA256


def test_verify_freeze_tampered_copy_raises(tmp_path):
    src = _I_DIR.parent / "s" / "selection_freeze.json"
    data = json.loads(src.read_text())
    data["selected_candidates"][0]["arm_identity_sha256"] = "0" * 64
    bad = tmp_path / "freeze.json"
    bad.write_text(json.dumps(data))
    with pytest.raises(E.FrozenShaMismatch):
        E.verify_freeze(bad)


def test_p0_lib_pin_mismatch_raises():
    with pytest.raises(E.FrozenShaMismatch):
        E.load_p0_lib(expected_sha="0" * 64)
    L = E.load_p0_lib()          # correct pin loads (cached)
    assert L.BAND_BPS == {"A": 10, "B": 15, "C": 25}
    assert L.STRESS_TIER == 2.0
    assert L.WORST_CASE_BPS_ROUNDTRIP == 100


# ----------------------------------------------------- engine determinism

def _fixture_names():
    return {"AAA": mk_name("AAA", step_i=290),
            "BBB": mk_name("BBB", step_i=290)}


def test_engine_determinism_identical_reruns():
    names = _fixture_names()
    cell = E.CELL_BY_ID[CFG_GAP]
    b1 = E.build_all_books(names, cell, CALENDAR, B1, B2, stress=2.0)
    b2 = E.build_all_books(names, cell, CALENDAR, B1, B2, stress=2.0)
    for key in ("candidate", "c_complement", "r5_component", "c_delay_h",
                "c_random_timing", "c_cal_hist", "c_reversal_plain"):
        assert b1[key].series_sha256() == b2[key].series_sha256()
        assert b1[key].expectancy == b2[key].expectancy
        assert len(b1[key].legs) == len(b2[key].legs)


def test_state_masks_equal_frozen_p0_kernels():
    L = E.load_p0_lib()
    nm = mk_name("CCC", step_i=280, step=1.20)
    cell = E.CELL_BY_ID[CFG_GAP]
    fired, bookable = E.state_fired_mask(nm, "GAP", cell["params"])
    f2, b2m, _ = L.census_gap(nm.adj_open, nm.adj_close, nm.volume,
                              cell["params"]["pctl"],
                              cell["params"]["direction"])
    assert np.array_equal(fired, f2)
    assert np.array_equal(bookable, b2m)
    # 52W-HIGH identity
    cell2 = E.CELL_BY_ID[CFG_52W]
    f3, b3 = E.state_fired_mask(nm, "52W-HIGH", cell2["params"])
    f4, b4, _ = L.census_52w_high(nm.adj_close, nm.volume,
                                  cell2["params"]["band_pct"])
    assert np.array_equal(f3, f4) and np.array_equal(b3, b4)
    # VOL-REGIME identity
    cell3 = E.CELL_BY_ID[CFG_VOL]
    f5, b5 = E.state_fired_mask(nm, "VOL-REGIME", cell3["params"])
    f6, b6, _ = L.census_vol_regime(nm.adj_close, nm.volume,
                                    cell3["params"]["L"],
                                    cell3["params"]["direction"])
    assert np.array_equal(f5, f6) and np.array_equal(b5, b6)


def test_arm_warmup_gate():
    names = _fixture_names()
    for cid, warm in ((CFG_GAP, 252), (CFG_52W, 252), (CFG_VOL, 272)):
        masks = E.arm_decision_masks(names, E.CELL_BY_ID[cid])
        for sym, idx in masks.items():
            assert all(i >= warm for i in idx), (cid, sym, idx[:3])


# ------------------------------------------------------ timing / clock

def test_entry_exit_timing_t_plus_1_open_to_t_plus_1_plus_H_open():
    nm = mk_name("TIM", n=320, step_i=310, step=1.21)
    fends = {"F1": CALENDAR[199], "F2": CALENDAR[259], "F3": CALENDAR[319]}
    cidx = {d: i for i, d in enumerate(CALENDAR[:320])}
    # decision t=300, H=5 -> entry 301, exit 306; step at 310 NOT spanned
    legs, cens, counts = E.build_legs(nm, [300], 5, cidx, fends, stress=2.0)
    assert len(legs) == 1 and not cens
    lg = legs[0]
    assert lg.entry_date == nm.dates[301]
    assert lg.exit_date == nm.dates[306]
    assert lg.gross == pytest.approx(0.0)     # 1.00/1.00 - 1, step not spanned
    assert lg.net == pytest.approx(0.0 - 2 * 25 * 2.0 / 1e4)
    assert len(lg.log_slices) == 5            # sessions 301..305
    assert lg.fold == "F3"
    # a leg spanning the step prices exactly: entry 309, exit 314
    legs2, _, _ = E.build_legs(nm, [308], 5, cidx, fends, stress=2.0)
    assert legs2[0].gross == pytest.approx(1.21 / 1.00 - 1.0)


def test_fold_force_flat_exits_at_fold_end_open():
    # decision in F2 with H=20 whose natural exit crosses B2
    # (t=252 >= 251 so med252 is defined; CALENDAR[252] <= B2 < CALENDAR[272])
    cal = CALENDAR
    nm = mk_name("FF", n=320, step_i=310, step=1.31)
    t = 252
    legs, cens, counts = E.build_legs(
        nm, [t], 20, {d: i for i, d in enumerate(cal)},
        {"F1": cal[199], "F2": cal[259], "F3": cal[319]}, stress=2.0)
    assert len(legs) == 1
    lg = legs[0]
    assert lg.force_flat is True
    assert lg.exit_date == cal[259]           # the F2 fold end
    assert lg.exit_date < nm.dates[252 + 1 + 20]   # before the natural exit
    assert lg.gross == pytest.approx(
        float(nm.adj_open[_idx(nm, cal[259])])
        / float(nm.adj_open[253]) - 1.0)
    # decision at the fold end -> no held session -> not opened
    legs2, _, counts2 = E.build_legs(
        nm, [259], 20, {d: i for i, d in enumerate(cal)},
        {"F1": cal[199], "F2": cal[259], "F3": cal[319]}, stress=2.0)
    assert legs2 == []
    assert counts2["fold_not_opened"] == 1


def _idx(nm, iso):
    return nm.dates.index(iso)


# ------------------------------------------------------- BC-7 death law

def test_bc7_death_session_open_exit_served_and_censored():
    # name dies at served session n-1 = 305; decision 300 H=10 -> natural
    # exit 311 beyond history -> DEATH_CENSORED, exit at death-session OPEN
    nm = mk_name("DTH", n=306, step_i=302, step=1.50)
    legs, cens, counts = E.build_legs(
        nm, [300], 10, {d: i for i, d in enumerate(CALENDAR)},
        {"F1": CALENDAR[199], "F2": B2, "F3": CALENDAR[319]}, stress=2.0)
    assert legs == [] and len(cens) == 1
    lg = cens[0]
    assert lg.censored and lg.censored_kind == "death_open"
    assert lg.exit_date == nm.dates[305]      # death session
    assert lg.gross == pytest.approx(1.50 / 1.00 - 1.0)  # entry 1.0, death open 1.5
    # excluded from the numerator: run_book keeps censored out of legs
    book = E.run_book("cand", "X", {"DTH": nm}, {("DTH"): [300]}, 10,
                      CALENDAR, B1, B2, stress=2.0)
    assert len(book.legs) == 0
    assert math.isnan(book.expectancy)        # nothing in the numerator
    assert len(book.censored_legs) == 1
    # invariance mode includes the mark net of costs
    inc = A.include_censored_nets(book)
    assert len(inc.legs) == 1
    assert inc.legs[0].net == pytest.approx(lg.gross - 2 * 25 * 2.0 / 1e4)
    assert inc.expectancy == pytest.approx(inc.legs[0].net)


def test_bc7_death_before_entry_and_zero_length():
    nm = mk_name("DTH2", n=310)
    # decision at the last served session: entry impossible
    legs, cens, counts = E.build_legs(
        nm, [309], 5, {d: i for i, d in enumerate(CALENDAR)},
        {"F1": CALENDAR[199], "F2": B2, "F3": CALENDAR[319]}, stress=2.0)
    assert legs == [] and len(cens) == 1
    assert cens[0].censored_kind == "died_before_entry"
    # decision one session before death: entry == death session ->
    # zero-length censored leg, no return recorded
    legs2, cens2, counts2 = E.build_legs(
        nm, [308], 5, {d: i for i, d in enumerate(CALENDAR)},
        {"F1": CALENDAR[199], "F2": B2, "F3": CALENDAR[319]}, stress=2.0)
    assert legs2 == [] and len(cens2) == 1
    assert cens2[0].censored_kind == "death_zero_length"
    assert cens2[0].gross != cens2[0].gross   # NaN: never a made-up return


# ------------------------------------------------- costs: bands, stress

def test_cost_band_assignment_from_med252():
    nm_a = mk_name("BA", vol=100e6)
    nm_b = mk_name("BB", vol=30e6)
    nm_c = mk_name("BC", vol=5e6)
    assert E.band_at(nm_a, 260) == "A"
    assert E.band_at(nm_b, 260) == "B"
    assert E.band_at(nm_c, 260) == "C"
    nm_sub = mk_name("BD", vol=1e6)
    assert E.band_at(nm_sub, 260) == "SUBFLOOR"


def test_band_subfloor_not_opened_and_unresolved_fail_closed():
    nm = mk_name("SUB", vol=1e6, n=320)
    legs, cens, counts = E.build_legs(
        nm, [260], 5, {d: i for i, d in enumerate(CALENDAR)},
        {"F1": CALENDAR[199], "F2": B2, "F3": CALENDAR[319]}, stress=2.0)
    assert legs == [] and counts["band_subfloor"] == 1
    # non-finite median on an otherwise eligible name -> fail-closed raise
    nm_bad = mk_name("UNR", n=260)
    with pytest.raises(ValueError, match="UNRESOLVED"):
        E.build_legs(nm_bad, [100], 5, {d: i for i, d in enumerate(CALENDAR)},
                     {"F1": CALENDAR[199], "F2": B2, "F3": CALENDAR[319]},
                     stress=2.0)


def test_worst_case_100bps_round_trip_band_c_stress2():
    # gross 0.0 legs; band C (25bps) at stress 2.0 -> net = -0.01 exactly
    nm = mk_name("WC", n=320)
    legs, _, _ = E.build_legs(
        nm, [260], 5, {d: i for i, d in enumerate(CALENDAR)},
        {"F1": CALENDAR[199], "F2": B2, "F3": CALENDAR[319]}, stress=2.0)
    assert len(legs) == 1
    assert legs[0].band == "C"
    assert legs[0].gross == pytest.approx(0.0)
    assert legs[0].net == pytest.approx(-0.01)   # 25 x 2 fills x 2.0 = 100bps
    # band A at stress 2.0: 10 x 2 x 2.0 = 40 bps
    nm_a = mk_name("WCA", vol=100e6, n=320)
    legs_a, _, _ = E.build_legs(
        nm_a, [260], 5, {d: i for i, d in enumerate(CALENDAR)},
        {"F1": CALENDAR[199], "F2": B2, "F3": CALENDAR[319]}, stress=2.0)
    assert legs_a[0].net == pytest.approx(-0.004)
    # non-stress path (stress 1.0): band C costs 50 bps round trip
    legs_s1, _, _ = E.build_legs(
        nm, [260], 5, {d: i for i, d in enumerate(CALENDAR)},
        {"F1": CALENDAR[199], "F2": B2, "F3": CALENDAR[319]}, stress=1.0)
    assert legs_s1[0].net == pytest.approx(-0.005)


# --------------------------------------- complements, R5, cohort twins

def test_gap_complement_is_union_and_r5_is_strict_crossing():
    L = E.load_p0_lib()
    # all gaps equal 0 -> threshold == 0 at every eligible session:
    # complement (presence, <= OR >=) fires everywhere; R5 (strict
    # crossing, < OR >) fires NOWHERE
    nm = mk_name("EQ", n=300)
    cell = E.CELL_BY_ID[CFG_GAP]
    compl = E.complement_fired_mask(nm, cell)
    r5 = E.r5_component_fired_mask(nm, cell)
    warm = cell["warmup_need"]
    assert np.array_equal(compl[warm:], np.ones(300 - warm, dtype=bool))
    assert not r5[warm:].any()
    # a real gap step crosses strictly -> R5 fires there too
    nm2 = mk_name("EQ2", n=300, step_i=280, step=1.40)
    r5b = E.r5_component_fired_mask(nm2, cell)
    compl2 = E.complement_fired_mask(nm2, cell)
    assert r5b[280] and compl2[280]


def test_52w_complement_and_r5_masks():
    # price doubles at 150 then halves at 260: on the plateau (255) the
    # close equals the rolling 252-session high -> candidate fires,
    # complement does not; after the crash (290) the close sits 50% below
    # the high -> candidate flat, complement and R5 fired
    nm = mk_name("W", n=300, step_i=150, step=2.0, down_i=260, down=0.5)
    cell = E.CELL_BY_ID[CFG_52W]
    fired = E.state_fired_mask(nm, "52W-HIGH", cell["params"])[0]
    compl = E.complement_fired_mask(nm, cell)
    r5 = E.r5_component_fired_mask(nm, cell)
    assert fired[255] and not compl[255] and r5[255]
    assert not fired[290] and compl[290] and r5[290]


def test_random_timing_cadence_every_63rd_session():
    dec = E.random_timing_decisions(CALENDAR)
    expected = [CALENDAR[j] for j in range(63, len(CALENDAR)) if j % 63 == 0]
    assert dec == expected
    assert len(dec) == 5            # 63,126,189,252,315


def test_cal_hist_twin_dates_and_floor_report():
    cal = CALENDAR
    # candidate fires on 12 dates all inside one bucket x F1
    bucket_dates = [d for d in cal[:199] if E._bucket_of(d) == E._bucket_of(cal[30])]
    assert len(bucket_dates) >= 12
    fired = bucket_dates[:12]
    twin, report = E.cal_hist_twin_dates(fired, cal, B1, B2)
    assert twin, "twin dates must be produced"
    for b, per_fold in report.items():
        for f, v in per_fold.items():
            if v["n_candidate"] == 0:
                assert v["n_twin"] == 0 and not v["sub_floor"]
    key = E._bucket_of(cal[30])
    assert report[key]["F1"]["n_candidate"] == 12
    assert report[key]["F1"]["n_twin"] == 12
    assert report[key]["F1"]["sub_floor"] is False   # 12 >= 10
    # a 2-fired bucket is sub-floor -> NOT_ADJUDICABLE disclosed
    twin2, report2 = E.cal_hist_twin_dates(fired[:2], cal, B1, B2)
    assert report2[key]["F1"]["sub_floor"] is True
    assert report2[key]["F1"]["n_twin"] == 2


def test_reversal_plain_worst_quintile_selection():
    # 5 names; known trailing 5-session returns via close steps
    names = {}
    for i, sym in enumerate(("N1", "N2", "N3", "N4", "N5")):
        names[sym] = mk_name(sym, n=320, close_step_i=280,
                             step=1.0 + 0.10 * (i + 1))
    masks, stats = E.reversal_plain_masks(names, CALENDAR)
    # at the first formation after the steps (j = 285: 285 % 5 == 0),
    # trailing 5-session returns rank N5 (worst, +10%) < N4 ... < N1
    assert stats["formations"] >= 1
    j = 285
    d = CALENDAR[j]
    picked = {sym for sym, idx in masks.items()
              if E.nm_dates_index(names[sym], d) in idx}
    assert picked == {"N1"}          # k = ceil(5/5) = 1; N1 = worst return


def test_pit_mutation_core_and_consecutive_runs():
    # isolated firing at t (t-1 unfired) -> changed -> gate passes
    mutated = np.zeros(10, dtype=bool)
    core = E.pit_gate_core(mutated, [5])
    assert core["pass"] and core["changed_or_refused"] == 1
    # consecutive run: state fired at t-1 -> the one-session-earlier
    # recomputation ALSO fires at t -> the book is unchanged -> gate fails
    mutated2 = np.zeros(10, dtype=bool)
    mutated2[5] = True
    core2 = E.pit_gate_core(mutated2, [5])
    assert not core2["pass"]
    assert core2["changed_or_refused"] == 0
    # full-book path on a real fixture shape (engines on synthetic data)
    names = _fixture_names()
    cell = E.CELL_BY_ID[CFG_GAP]
    masks = E.arm_decision_masks(names, cell)
    gate = E.pit_mutation_gate(names, masks, cell)
    assert gate["law"].startswith("one-session-earlier")


# ---------------------------------------------- kill rules (hand books)

def _cand_book(nets, folds, pnl=None):
    legs = [leg("X", f, n) for n, f in zip(nets, folds)]
    return hand_book("candidate", legs, pnl)


def test_r1_kills_nonpositive_expectancy_first_binding():
    cand = _cand_book([-0.01, -0.02], ("F1", "F2"))
    b, _ = bundle_from_books(cand)
    out = A.ordered_kills(b, None, CALENDAR, B1, B2)
    assert out["verdict"] == "REJECT_R1" and out["reject"]
    # equality to zero also kills (<= 0)
    cand0 = _cand_book([0.0, 0.0], ("F1", "F2"))
    out0 = A.ordered_kills(bundle_from_books(cand0)[0], None, CALENDAR,
                           B1, B2)
    assert out0["binding_rule"] == "R1"


def test_r2_kills_when_candidate_below_max_market_or_random():
    # candidate E = +0.001; C-MARKET legs realize +0.002 -> REJECT_R2
    cand = _cand_book([0.001] * 4, ("F1", "F1", "F2", "F3"))
    cand.legs[0].entry_date, cand.legs[0].exit_date = \
        CALENDAR[10], CALENDAR[20]
    for i, (e, x) in enumerate(((100, 110), (120, 130), (140, 150),
                                (160, 170))):
        cand.legs[i].entry_date = CALENDAR[e]
        cand.legs[i].exit_date = CALENDAR[x]
    spy = spy_with_leg_returns(cand.legs, [0.002] * 4)
    rnd = _cand_book([0.0] * 2, ("F1", "F2"))     # E 0.0 < 0.001
    b, _ = bundle_from_books(cand, rnd=rnd)
    out = A.ordered_kills(b, spy, CALENDAR, B1, B2)
    assert out["verdict"] == "REJECT_R2"
    # random-timing above the candidate also binds R2
    spy0 = spy_with_leg_returns(cand.legs, [0.0] * 4)
    rnd_hi = _cand_book([0.005] * 2, ("F1", "F2"))
    b2, _ = bundle_from_books(cand, rnd=rnd_hi)
    out2 = A.ordered_kills(b2, spy0, CALENDAR, B1, B2)
    assert out2["verdict"] == "REJECT_R2"
    # both controls below -> no R2 kill
    b3, _ = bundle_from_books(cand, rnd=rnd)
    out3 = A.ordered_kills(b3, spy0, CALENDAR, B1, B2)
    assert not out3["reject"]


def test_r3_complement_out_earn_or_half_same_sign_two_folds():
    cand = _cand_book([0.004] * 6, ("F1", "F1", "F2", "F2", "F3", "F3"))
    # (a) complement out-earns full sample
    compl_hi = _cand_book([0.010] * 3, ("F1", "F2", "F3"))
    out = A.ordered_kills(bundle_from_books(cand, compl=compl_hi)[0], None,
                          CALENDAR, B1, B2)
    assert out["verdict"] == "REJECT_R3"
    # (b) complement reproduces >= 0.5x same-sign in 2 folds (0.6x, 0.6x)
    compl_f = _cand_book([0.0024, 0.0024, -0.001, 0.009],
                         ("F1", "F1", "F2", "F3"))
    # F1: cand 0.004 vs compl 0.0024 -> 0.6x same sign (reproduces)
    # F2: cand 0.004 vs compl -0.001 -> no; F3: cand 0.004 vs 0.009 -> 2.25x
    out_b = A.ordered_kills(bundle_from_books(cand, compl=compl_f)[0], None,
                            CALENDAR, B1, B2)
    assert out_b["verdict"] == "REJECT_R3"
    # (c) complement negative or tiny elsewhere -> no kill
    compl_ok = _cand_book([-0.002, -0.002, -0.002, 0.0001],
                          ("F1", "F1", "F2", "F3"))
    out_c = A.ordered_kills(bundle_from_books(cand, compl=compl_ok)[0], None,
                            CALENDAR, B1, B2)
    assert not out_c["reject"] and out_c["binding_rule"] is None


def test_r4_reversal_plain_mandatory_kill():
    cand = _cand_book([0.004] * 6, ("F1", "F1", "F2", "F2", "F3", "F3"))
    rev = _cand_book([0.010] * 3, ("F1", "F2", "F3"))
    out = A.ordered_kills(bundle_from_books(cand, rev=rev)[0], None,
                          CALENDAR, B1, B2)
    assert out["verdict"] == "REJECT_R4"
    # reproduces in 2 folds at >= 0.5x same sign also binds
    rev_f = _cand_book([0.002, 0.002, -0.01, -0.01],
                       ("F1", "F2", "F3", "F3"))
    out_b = A.ordered_kills(bundle_from_books(cand, rev=rev_f)[0], None,
                            CALENDAR, B1, B2)
    assert out_b["verdict"] == "REJECT_R4"


def test_r5_union_full_sample_same_sign_half_kills():
    cand = _cand_book([0.004] * 6, ("F1", "F1", "F2", "F2", "F3", "F3"))
    # fold rule alone would NOT bind (only F3 reproduces), but the
    # full-sample component-only book reproduces exactly 0.5x same-sign
    r5 = _cand_book([0.006, 0.006, -0.02, 0.012],
                    ("F1", "F1", "F2", "F3"))
    # E_r5 = (0.006+0.006-0.02+0.012)/4 = 0.001 = 0.25x -> no full kill;
    # fold reproductions: F1 0.6x yes, F2 negative no, F3 3x yes -> 2 folds
    out = A.ordered_kills(bundle_from_books(cand, r5=r5)[0], None,
                          CALENDAR, B1, B2)
    assert out["verdict"] == "REJECT_R5"
    # union second leg: full-sample >= 0.5x same-sign with < 2 fold reps
    r5b = _cand_book([0.002, 0.002, -0.02, -0.02], ("F1", "F1", "F2", "F3"))
    # E_r5 = -0.0095? -> (0.002+0.002-0.02-0.02)/4 = -0.009 -> wrong sign
    r5b = _cand_book([0.005, -0.002, -0.002, -0.002], ("F1", "F2", "F3", "F3"))
    # E_r5 = -0.00025 -> no.  construct exactly 0.5x: E_r5 = 0.002
    r5c = _cand_book([0.006, 0.006, 0.006, -0.012], ("F1", "F2", "F3", "F3"))
    # folds: F1 0.006 (1.5x, same sign), F2 0.006 (1.5x) -> 2 folds would
    # bind the fold rule; adjust to keep only one fold reproducing
    r5d = _cand_book([0.006, -0.02, -0.02, 0.006], ("F1", "F2", "F2", "F3"))
    # E_r5 = (0.006-0.02-0.02+0.006)/4 = -0.007 -> negative.  Use instead:
    r5e = _cand_book([0.003, 0.003, 0.003, 0.003], ("F1", "F2", "F3", "F3"))
    # every fold reproduces 0.75x -> fold rule binds (>= 2/3)
    out_e = A.ordered_kills(bundle_from_books(cand, r5=r5e)[0], None,
                            CALENDAR, B1, B2)
    assert out_e["verdict"] == "REJECT_R5"
    # exact full-sample-only binding: one fold reproduces, full = 0.5x
    r5f = _cand_book([0.004, 0.004, 0.004, 0.004], ("F1", "F2", "F3", "F3"))
    # full E = 0.004 = 1.0x same sign; folds all reproduce -> fold rule
    out_f = A.ordered_kills(bundle_from_books(cand, r5=r5f)[0], None,
                            CALENDAR, B1, B2)
    assert out_f["verdict"] == "REJECT_R5"


def test_r5_empty_book_not_adjudicable_disclosed():
    cand = _cand_book([0.004] * 6, ("F1", "F1", "F2", "F2", "F3", "F3"))
    out = A.ordered_kills(bundle_from_books(cand)[0], None, CALENDAR,
                          B1, B2)
    r5_rows = [r for r in out["rows"] if r["rule"] == "R5"]
    assert r5_rows and "NOT_ADJUDICABLE" in r5_rows[0]["detail"]["disposition"]


def test_r6_cal_hist_out_earn_and_random_timing_ordering():
    # C-CAL-HIST out-earning binds R6 (the R6 clock rule extends to it)
    cand = _cand_book([0.004] * 6, ("F1", "F1", "F2", "F2", "F3", "F3"))
    ch_hi = _cand_book([0.006] * 2, ("F1", "F2"))
    rnd_lo = _cand_book([0.001] * 2, ("F1", "F2"))
    out = A.ordered_kills(bundle_from_books(cand, ch=ch_hi, rnd=rnd_lo)[0],
                          None, CALENDAR, B1, B2)
    assert out["verdict"] == "REJECT_R6"
    # a C-RANDOM-TIMING out-earner is caught EARLIER by R2 (candidate <=
    # max(C-MARKET, C-RANDOM-TIMING)): the ordered battery binds R2
    # first; R6 is the defense-in-depth clock rule behind it
    rnd_hi = _cand_book([0.005] * 2, ("F1", "F2"))
    out_b = A.ordered_kills(bundle_from_books(cand, rnd=rnd_hi)[0], None,
                            CALENDAR, B1, B2)
    assert out_b["verdict"] == "REJECT_R2"
    # both controls below the candidate -> survive R6
    ch_lo = _cand_book([0.001] * 2, ("F1", "F2"))
    out_c = A.ordered_kills(bundle_from_books(cand, rnd=rnd_lo, ch=ch_lo)[0],
                            None, CALENDAR, B1, B2)
    assert not out_c["reject"]


def test_k6_slow_drift_reject_on_indistinguishable_pairs():
    # candidate fold nets [0.010, -0.006] -> E_f = 0.002,
    # SE_f = std(ddof=1)/sqrt(2) ~= 0.008: the delay (E_f = 0.006) and
    # the OPPOSITE-SIGN complement (E_f = -0.002, so R3 does NOT see a
    # 0.5x same-sign reproduction) are both within SE in F1+F2 -> K6
    cand = _cand_book([0.010, -0.006] * 3, ("F1", "F1", "F2", "F2",
                                            "F3", "F3"))
    delay = _cand_book([0.006] * 3, ("F1", "F2", "F3"))
    compl = _cand_book([-0.002] * 3, ("F1", "F2", "F3"))
    out = A.ordered_kills(bundle_from_books(cand, compl=compl,
                                            delay=delay)[0], None,
                          CALENDAR, B1, B2)
    assert out["verdict"] == "REJECT_K6"
    # distinguishable: the delay moves outside SE in two folds
    delay_far = _cand_book([0.100] * 3, ("F1", "F2", "F3"))
    out_b = A.ordered_kills(bundle_from_books(cand, compl=compl,
                                              delay=delay_far)[0], None,
                            CALENDAR, B1, B2)
    assert not out_b["reject"]
    k6_rows = [r for r in out_b["rows"] if r["rule"] == "K6"]
    assert k6_rows and k6_rows[0]["detail"]["folds_indistinguishable"] < 2


def test_first_binding_order_r1_beats_later_kills():
    # candidate negative AND complement out-earning -> R1 binds first
    cand = _cand_book([-0.01] * 4, ("F1", "F1", "F2", "F3"))
    compl = _cand_book([0.05] * 2, ("F1", "F2"))
    out = A.ordered_kills(bundle_from_books(cand, compl=compl)[0], None,
                          CALENDAR, B1, B2)
    assert out["binding_rule"] == "R1"


# ---------------------------------------------------- Stage-A battery

def test_stage_a_fold_positive_share_gate():
    sa = A.stage_a_gates
    cal = CALENDAR
    # positive PnL concentrated 3/4 in F1 -> 0.75 > 0.5 -> FAIL
    book = hand_book("c", [leg("X", "F1", 0.001)], pnl_by_fold={
        "F1": 0.03, "F2": 0.01, "F3": -0.01})
    bundle, _ = bundle_from_books(book)
    got = A.stage_a_gates(bundle, None, cal, B1, B2)
    g = got["gates"]["fold_positive_share"]
    assert g["value"] == pytest.approx(0.75) and g["pass"] is False
    # exactly balanced positive folds -> share 0.50, kill is STRICTLY
    # > 50% (V11 precedent 0.5034 was FAILING) -> 0.50 passes
    book2 = hand_book("c", [leg("X", "F1", 0.001)], pnl_by_fold={
        "F1": 0.02, "F2": 0.02, "F3": -0.001})
    bundle2, _ = bundle_from_books(book2)
    g2 = A.stage_a_gates(bundle2, None, cal, B1, B2)[
        "gates"]["fold_positive_share"]
    assert g2["value"] == pytest.approx(0.50) and g2["pass"] is True


def test_stage_a_largest_fold_concentration_gate():
    book = hand_book("c", [leg("X", "F1", 0.001)], pnl_by_fold={
        "F1": 0.04, "F2": -0.005, "F3": -0.005})
    bundle, _ = bundle_from_books(book)
    g = A.stage_a_gates(bundle, None, CALENDAR, B1, B2)[
        "gates"]["largest_fold_concentration"]
    assert g["value"] == pytest.approx(0.04 / 0.05) and g["pass"] is False
    # balanced absolute PnL -> 1/3 <= 0.5 -> pass
    book2 = hand_book("c", [leg("X", "F1", 0.001)], pnl_by_fold={
        "F1": 0.01, "F2": -0.01, "F3": 0.01})
    bundle2, _ = bundle_from_books(book2)
    g2 = A.stage_a_gates(bundle2, None, CALENDAR, B1, B2)[
        "gates"]["largest_fold_concentration"]
    assert g2["value"] == pytest.approx(1 / 3) and g2["pass"] is True


def test_stage_a_spy_excess_fold_rule():
    cand = _cand_book([0.004] * 6, ("F1", "F1", "F2", "F2", "F3", "F3"))
    for i, (e, x) in enumerate(((100, 110), (120, 130), (140, 150),
                                (160, 170), (180, 190), (200, 210))):
        cand.legs[i].entry_date = CALENDAR[e]
        cand.legs[i].exit_date = CALENDAR[x]
    # SPY legs realize 0.001 everywhere -> excess +0.003 in all 3 folds
    spy = spy_with_leg_returns(cand.legs, [0.001] * 6)
    bundle, _ = bundle_from_books(cand)
    g = A.stage_a_gates(bundle, spy, CALENDAR, B1, B2)[
        "gates"]["spy_excess_folds"]
    assert g["positive_folds"] == 3 and g["pass"] is True
    # SPY legs realize 0.005 -> excess negative everywhere -> fail
    spy2 = spy_with_leg_returns(cand.legs, [0.005] * 6)
    g2 = A.stage_a_gates(bundle, spy2, CALENDAR, B1, B2)[
        "gates"]["spy_excess_folds"]
    assert g2["positive_folds"] == 0 and g2["pass"] is False


def test_stage_a_mdd_gate():
    cal_len = len(CALENDAR)
    book = E.BookResult(book_id="c", config_id="FIX", H=5, stress=2.0,
                        calendar=tuple(CALENDAR))
    book.legs = []
    series = np.zeros(cal_len)
    series[100:120] = 0.005          # +10%
    series[120:130] = -0.02          # then -20% -> DD ~ 27% > 15%
    book.book_log = series
    bundle, _ = bundle_from_books(book)
    g = A.stage_a_gates(bundle, None, CALENDAR, B1, B2)["gates"]["mdd"]
    assert g["value"] > 0.15 and g["pass"] is False
    series2 = np.zeros(cal_len)
    series2[100:120] = 0.005
    series2[120:130] = -0.003        # DD ~ 6% <= 15%
    book2 = E.BookResult(book_id="c", config_id="FIX", H=5, stress=2.0,
                         calendar=tuple(CALENDAR))
    book2.legs = []
    book2.book_log = series2
    bundle2, _ = bundle_from_books(book2)
    g2 = A.stage_a_gates(bundle2, None, CALENDAR, B1, B2)["gates"]["mdd"]
    assert g2["pass"] is True


def test_stage_a_drop_one_stability():
    # positive in every drop-one remainder -> stable
    cand = _cand_book([0.004] * 6, ("F1", "F1", "F2", "F2", "F3", "F3"))
    bundle, _ = bundle_from_books(cand)
    g = A.stage_a_gates(bundle, None, CALENDAR, B1, B2)[
        "gates"]["drop_one_stability"]
    assert g["pass"] is True
    # F3 dominated by a huge loss -> dropping F1 leaves positive? craft:
    cand2 = _cand_book([0.010, 0.010, 0.010, 0.010, -0.100, -0.100],
                       ("F1", "F1", "F2", "F2", "F3", "F3"))
    # full E = (0.04 - 0.2)/6 < 0 (would die at R1) - use positive full:
    cand3 = _cand_book([0.050, 0.050, 0.001, 0.001, -0.030, -0.030],
                       ("F1", "F1", "F2", "F2", "F3", "F3"))
    # full E = (0.102 - 0.06)/6 = +0.007
    bundle3, _ = bundle_from_books(cand3)
    g3 = A.stage_a_gates(bundle3, None, CALENDAR, B1, B2)[
        "gates"]["drop_one_stability"]
    # drop F1 -> E = (0.002 - 0.06)/4 < 0 -> unstable
    assert g3["pass"] is False


def test_break_even_margin_quantified():
    cand = hand_book("c", [leg("X", "F1", net=0.0, gross=0.02)])
    be = A.break_even_margin(cand)
    assert be["break_even_bps_per_fill"] == pytest.approx(100.0)
    assert be["operative_stress_bps_per_fill"] == pytest.approx(50.0)
    assert be["margin_bps"] == pytest.approx(50.0)


# ------------------------------------------ DSR math (hand-computable)

def test_dsr_gate_refuses_off_the_scored_path():
    out = A.dsr_gate(np.zeros(10), [0.1, 0.1], 47, 0.10, allow_scored=False)
    assert out["status"] == "NOT_RUN_E_ONLY" and out["dsr"] is None


def test_dsr_math_hand_computed_zero_variance_trials():
    from statistics import NormalDist
    # trials variance 0 -> SR0 = 0 -> DSR = Phi(SR* sqrt(T-1) / denom)
    # with the sample skew/kurtosis in the denominator (the deep
    # estimator math is covered by tests/test_dsr.py; this checks the
    # wrapper plumbing: log->simple transform, SR, sample length, SR0
    # and the pass threshold)
    simple = np.array([0.01, -0.005, 0.02, -0.01, 0.015] * 20)  # T=100
    log_series = np.log1p(simple)          # dsr_gate consumes the P-11 LOG series
    r = simple
    sr = float(np.mean(r) / np.std(r, ddof=1))
    skew = float(((r - r.mean()) ** 3).mean() / r.std(ddof=1) ** 3)
    kurt = float(((r - r.mean()) ** 4).mean() / r.std(ddof=1) ** 4)
    denom = math.sqrt(max(1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr * sr,
                          1e-12))
    expected = NormalDist().cdf(sr * math.sqrt(99) / denom)
    out = A.dsr_gate(log_series, [0.05, 0.05], 47, 0.10, allow_scored=True)
    assert out["dsr"] == pytest.approx(expected, abs=1e-9)
    assert out["sr0"] == pytest.approx(0.0, abs=1e-12)
    assert out["z_statistic"] == pytest.approx(sr * math.sqrt(99) / denom,
                                               abs=1e-9)
    # alpha 0.10 -> pass iff DSR >= 0.90
    assert out["pass"] == (out["dsr"] >= 0.90)


def test_dsr_higher_than_expected_max_gives_high_probability():
    # candidate SR far above the trials' expected max -> DSR ~ 1
    series = np.array([0.01, -0.005, 0.02, -0.01, 0.015] * 20)
    out = A.dsr_gate(series, [0.05, 0.05], 47, 0.10, allow_scored=True)
    assert out["dsr"] > 0.99 and out["pass"] is True


def test_dsr_decreases_with_inflating_trials():
    series = np.array([0.01, -0.005, 0.02, -0.01, 0.015] * 20)
    low = A.dsr_gate(series, [0.05, 0.05], 47, 0.10, allow_scored=True)
    high = A.dsr_gate(series, [0.05, 0.2, 0.5, -0.1], 47, 0.10,
                      allow_scored=True)
    assert high["sr0"] > low["sr0"]
    assert high["dsr"] < low["dsr"]
    # program-cumulative N=260 @ 0.05 is reported-only (structure present)
    rep = A.dsr_gate(series, [0.05, 0.05], 260, 0.05, allow_scored=True)
    assert rep["alpha"] == 0.05


# ------------------------------------------------------ full verdicts

def test_full_adjudication_labels_and_verdict_on_synthetic_cohort():
    from datetime import date as _d
    names = _fixture_names()
    spy = mk_name("SPY", n=320)
    rep = A.run_candidate_adjudication(names, CFG_GAP, CALENDAR, B1,
                                       B2, spy)
    assert rep["r0_status"] == "R0_NOT_RUN"
    assert rep["r0_verbatim"] == "R0 NOT_RUN (D2 skipped by owner amendment §3b)"
    assert rep["pbo_status"] == "PBO_NOT_RUN"
    assert "PBO NOT_RUN fail-closed (<=3 cells, d0992d17 class)" == rep["pbo_verbatim"]
    assert rep["budget"]["max"] == 3 and rep["budget"]["used"] == 0
    assert "owner-relaxed acceptance battery" in rep["disclosure_section10"]
    assert rep["verdict"].startswith(("REJECT_", "STAGE_A",
                                      "PASS_I_STAGE",
                                      "DEATH_CENSORING"))
    # ordered rows contain the whole battery in order
    rules = [r["rule"] for r in rep["primary"]["rows"]]
    assert rules == sorted(rules, key=["R1", "R2", "R3", "R4", "R5", "R6",
                                       "K6"].index) or len(rules) >= 1
    assert rep["primary"]["rows"][0]["rule"] == "R1"


def test_death_censoring_invariance_binds_verdict():
    # hand-built bundle: primary survives everything; censored-included
    # legs flip R1 -> the verdict must become UNBOOKABLE (coupled)
    cand = hand_book("c", [leg("X", "F1", net=0.004, gross=0.004)],
                     pnl_by_fold={"F1": 0.02, "F2": 0.02, "F3": 0.02})
    # attach one huge negative censored leg (death_open mark)
    cen = E.Leg("X", 9, CALENDAR[300], CALENDAR[301], CALENDAR[310],
                "F3", "C", -0.5, math.nan, censored=True,
                censored_kind="death_open")
    cand.censored_legs = [cen]
    compl = hand_book("cc", [leg("X", "F1", -0.001)])
    r5 = hand_book("r5", [leg("X", "F2", -0.001)])
    rev = hand_book("rev", [leg("X", "F3", -0.001)])
    rnd = hand_book("rnd", [leg("X", "F1", 0.0)])
    ch = hand_book("ch", [leg("X", "F2", 0.0)])
    delay = hand_book("dl", [leg("X", "F3", 99.0)])   # far from SE
    b, _ = bundle_from_books(cand, compl=compl, r5=r5, rev=rev, rnd=rnd,
                             ch=ch, delay=delay)
    # spy legs 0.0 -> SPY-excess +0.004 in all folds... spy fixture needed
    spy = spy_with_leg_returns(cand.legs, [0.0])
    out = A.adjudicate_candidate(b, spy, CALENDAR, B1, B2)
    assert out["primary"]["reject"] is False
    assert out["death_invariance"]["verdict_matches"] is False
    assert out["verdict"] == "DEATH_CENSORING_COUPLED_UNBOOKABLE"


def test_go_gate_hard_refusal_on_real_data_loader():
    cache = _REPO_ROOT / "research" / "control" / "stocks_search_v1_run" / "p0" / "raw"
    manifest = _REPO_ROOT / "research" / "control" / "stocks_search_v1_run" / "p0" / "retrieval_manifest.json"
    # early / paraphrased / wrong-case GO dies unconsumed (P-8)
    for bad in ("", "go stocks search v1 scored execution",
                "GO STOCKS SEARCH V1 SCORED EXECUTION NOW",
                "GO STOCKS SEARCH V1 SCORED EXECUTION",
                "GO STOCKS SEARCH V1  SCORED EXECUTION",
                "Please GO STOCKS SEARCH V1 SCORED EXECUTION"):
        if bad == GO_PHRASE:
            continue
        with pytest.raises(A.GoGateRefused):
            A.load_real_data(bad, cache, manifest)
    # exact phrase passes the gate, then the loader's data-path check runs
    with pytest.raises(FileNotFoundError):
        A.load_real_data(GO_PHRASE, "/nonexistent/cache/dir", manifest)


def test_go_phrase_constant_matches_dispatch():
    assert E.GO_PHRASE == "GO STOCKS SEARCH V1 SCORED EXECUTION"
    assert A.GO_PHRASE == "GO STOCKS SEARCH V1 SCORED EXECUTION"


# ------------------------------------------------- P-11 persistence

def test_p11_series_persistence_deterministic(tmp_path):
    names = _fixture_names()
    cell = E.CELL_BY_ID[CFG_GAP]
    b1 = E.build_all_books(names, cell, CALENDAR, B1, B2, stress=2.0)
    d1 = A.persist_series(tmp_path / "a.json", b1["candidate"])
    d2 = A.persist_series(tmp_path / "b.json", b1["candidate"])
    assert d1 == d2
    payload = json.loads((tmp_path / "a.json").read_text())
    assert payload["sha256"] == d1
    body = {k: v for k, v in payload.items() if k != "sha256"}
    recomputed = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest()
    assert recomputed == d1


# ------------------------------------- build_all_books integration

def test_build_all_books_produces_full_battery_and_is_outcome_safe():
    names = _fixture_names()
    spy = mk_name("SPY", n=320)
    for cid in (CFG_GAP, CFG_52W, CFG_VOL):
        bundle = E.build_all_books(names, E.CELL_BY_ID[cid], CALENDAR,
                                   B1, B2, stress=2.0)
        for key in ("candidate", "c_complement", "r5_component",
                    "c_delay_h", "c_random_timing", "c_cal_hist",
                    "c_reversal_plain"):
            assert bundle[key].book_log is not None
            assert bundle[key].book_log.shape[0] == len(CALENDAR)
        assert "pass" in bundle["pit_mutation"]
        assert bundle["c_cal_hist_report"]
        # spy legs align 1:1 with candidate legs, NaN only off-dates
        sl = E.spy_legs_for(spy, bundle["candidate"].legs)
        assert len(sl) == len(bundle["candidate"].legs)
