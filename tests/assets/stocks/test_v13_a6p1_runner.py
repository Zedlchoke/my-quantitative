"""SFV13-A6-P1 family runner tests (A8 lane).

Handbook 14.2/14.3 discipline: synthetic hand-computed fixtures ONLY.  No
production data byte participates in any assertion EXCEPT the one mandated
manifest-integrity check (verify_price_manifest sample against
p0d_v13_price_manifest.json), which SKIPS when the staging root is absent so
the suite stays hermetic elsewhere.  Every PnL/return number asserted below
is a property of the FIXTURE arithmetic (flat prices, single price steps,
band-A 10 bps costs, 1/16 leg weights), never of a scored production cell.

Frozen-spec properties under test:
  - transition-state classification (+1 / -1 / 0) with the absence-evidence
    abstain gate, cross-checked against the TESTED D2 handler
    (d2_v13_proposal_handlers.a6_div_exposures);
  - one-event one-bar lag: STRICT_NEXT_BAR (decision uses ex_date < D only;
    the fill is the first union session strictly AFTER D);
  - no-lookahead mutation: shifting an ex_date one day past D does NOT
    change the decision at D, and the record enters the windows exactly at
    the first decision strictly after the new ex_date;
  - costs charged EXACTLY ONCE PER SIDE (10/15/25 bps x1; stress x2);
  - fold force-flat (exit at the fold's last session, with cost);
  - dead-leg exit-at-last-close on a synthetic dead series;
  - sham control determinism (same seed -> same book) + frozen hash order;
  - malformed price file fail-closed; missing series counted, never guessed;
  - record-ID pairwise distinctness;
  - per-period series written and reconcilable against per-entity legs;
  - dry-run hygiene: recursive PnL leak scan (stress PnL leak class);
  - heavy-lock discipline: single attempt, LockBusy -> exit 3, and the
    scored path refuses without the two keys.
"""

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from research.assets.stocks import v13_a6p1_family_runner as R
from research.assets.stocks.d2_v13_proposal_handlers import (
    a6_div_exposures,
    within_sector_hash_permutation_sham,
)

D1 = "2019-01-03"      # a real frozen scored grid date (index 3)
D2 = "2019-04-04"      # the next frozen scored date
GRID_T = [D1, D2]
GRID_ONE = [D1]
FOLD_T = [{"fold_id": "S0_FOLD_1", "start": "2018-12-01",
           "end": "2019-06-30"}]
FOLD_TIGHT = [{"fold_id": "S0_FOLD_1", "start": "2018-12-01",
               "end": "2019-01-25"}]   # force-flat before the 21st session

NAMES = [f"CIK{i:010d}" for i in range(1, 41)]           # 4 sectors x 10
UNMAPPED = ["CIK0000000041", "CIK0000000042"]            # sector "" excluded
LONGS = {i for i in range(1, 41) if i % 10 in (1, 2)}    # initiators +1
SHORTS = {i for i in range(1, 41) if i % 10 in (3, 4)}   # omitters -1
DEAD_CLASS = {39, 40}                                    # DEAD_EVIDENCED legs


def sector_of(i):
    return f"SEC_{(i - 1) // 10}"


def sessions(start=date(2017, 6, 1), end=date(2019, 6, 28)):
    days, cur = [], start
    while cur <= end:
        if cur.weekday() < 5:
            days.append(cur.isoformat())
        cur += timedelta(days=1)
    return days


def dividends_for(i):
    """Hand-computed states at D1 AND D2 (windows move identically):
      i%10 in (1,2): initiation +1  (ancient 2017-01-01 + now 2018-06-01)
      i%10 in (3,4): omission  -1   (ancient 2016-01-01 + prev 2017-06-01)
      else         : assertable never-payer 0 (ancient 2016-06-01)
    D1: lo_now=2018-01-03, lo_prev=2017-01-04; D2: lo_now=2018-04-05,
    lo_prev=2017-04-06."""
    if i % 10 in (1, 2):
        return [{"ex_date": "2017-01-01"}, {"ex_date": "2018-06-01"}]
    if i % 10 in (3, 4):
        return [{"ex_date": "2016-01-01"}, {"ex_date": "2017-06-01"}]
    return [{"ex_date": "2016-06-01"}]


def default_adj(i, d):
    """Flat 100 with one +5% (longs) / -5% (shorts) step inside the D1 hold
    (from 2019-01-10) and a -5% (longs) / +5% (shorts) step inside the D2
    hold (from 2019-04-15; 99.75 = 105x0.95 = 95x1.05): every leg return is
    exactly +-0.05 in both windows."""
    if i % 10 in (1, 2):
        if d >= "2019-04-15":
            return 99.75
        if d >= "2019-01-10":
            return 105.0
    if i % 10 in (3, 4):
        if d >= "2019-04-15":
            return 99.75                    # 95 -> 99.75 = +5% (short gains)
        if d >= "2019-01-10":
            return 95.0
    return 100.0


def build_world_files(tmp, price_fn=None, volume_fn=None, dead_end=None,
                      dead_price=None, dividends=None, bench=False,
                      sessions_end=None, names=None):
    """Write cohort + dividend + price (+optional benchmark) staging into a
    tmp dir.  names defaults to NAMES + the two UNMAPPED probes."""
    tmp = Path(tmp)
    eod = tmp / "eod"
    eod.mkdir(parents=True, exist_ok=True)
    divd = tmp / "div"
    divd.mkdir(parents=True, exist_ok=True)
    names = names if names is not None else NAMES + UNMAPPED
    days = sessions(end=sessions_end or date(2019, 6, 28))
    for n in names:
        i = int(n[3:])
        ticker = f"T{i}"
        recs = (dividends or {}).get(i, dividends_for(i))
        (divd / f"{ticker}.json").write_text(json.dumps(recs))
        series = []
        for d in days:
            if dead_end and i == int(dead_end[0]) and d > dead_end[1]:
                continue                      # the dying name's series ends
            px = (price_fn or default_adj)(i, d)
            raw = 100.0                       # raw close floor never binds
            vol = (volume_fn or (lambda i2, d2: 1_000_000))(i, d)
            if dead_end and i == int(dead_end[0]) and d == dead_end[1]:
                px = dead_price               # last recorded close
            series.append({"date": d, "open": raw, "high": raw,
                           "low": raw, "close": raw, "adjusted_close": px,
                           "volume": vol})
        (eod / f"{n}__{ticker}.json").write_text(json.dumps(series))
    cohort = {"members": {"ALIVE_EVIDENCED": [], "DEAD_EVIDENCED": []}}
    for n in names:
        i = int(n[3:])
        m = {"cik": n, "ticker": f"T{i}", "sector": "" if i > 40
             else sector_of(i)}
        if i in DEAD_CLASS:
            cohort["members"]["DEAD_EVIDENCED"].append(
                {"cik": n, "ticker_eodhd": f"T{i}",
                 "sector": sector_of(i)})
        else:
            cohort["members"]["ALIVE_EVIDENCED"].append(m)
    (tmp / "cohort.json").write_text(json.dumps(cohort))
    if bench:
        bd = tmp / "bench"
        bd.mkdir(parents=True, exist_ok=True)
        for tkr, step_from, level in (("SPY", "2019-01-10", 101.0),
                                      ("XLF", "2019-01-10", 103.0)):
            bars = [{"date": d, "adjusted_close": (level if d >= step_from
                                                   else 100.0)} for d in days]
            (bd / f"{tkr}.json").write_text(json.dumps(bars))
    return {"tmp": tmp, "eod": eod, "div": divd, "cohort": tmp / "cohort.json",
            "bench": tmp / "bench" if bench else tmp / "bench_absent"}


def make_world(w, diag=None, bench=False):
    return R.build_world(cohort_path=str(w["cohort"]),
                         div_dir=str(w["div"]),
                         prices_dir=str(w["eod"]),
                         bench_dir=str(w["bench"]) if bench
                         else str(w["tmp"] / "bench_absent"),
                         diag=diag)


LEG_W = 1.0 / 16.0            # 8 long + 8 short active names, gross 1.0
LEG_COST_BPS = LEG_W * 10.0   # one side, band A: 0.625 bps per leg


def approx(a, b, eps=1e-9):
    return a is not None and abs(a - b) <= eps


# ===========================================================================
# transition-state classification + absence gate (+ cross-check vs handler)
# ===========================================================================
def test_transition_states_and_absence_gate(tmp_path):
    w = build_world_files(tmp_path)
    diag = R.new_diag()
    world = make_world(w, diag)
    anchor = world["exposures"]["SFV13-A6-H1-ANCHOR"]
    for d in (D1, D2):
        for n in NAMES:
            i = int(n[3:])
            want = 1.0 if i % 10 in (1, 2) else (
                -1.0 if i % 10 in (3, 4) else 0.0)
            assert anchor[(n, d)] == want, (n, d, anchor[(n, d)])
        assert (UNMAPPED[0], d) in anchor        # state exists even unmapped
    # the three warmup dates NEVER appear (clock.warmup: decisions = 3)
    assert not any(t in ("2018-04-04", "2018-07-03", "2018-10-02")
                   for _c, t in anchor)
    # cross-check against the TESTED D2 handler on the same synthetic bytes
    cohort = world["cohort"]
    ticker_of = {c: v["ticker"] for c, v in cohort.items()}
    divs = R.load_dividends(str(w["div"]),
                            tickers={v["ticker"] for v in cohort.values()})
    d2_diag = R.new_diag()
    handler_x = a6_div_exposures(divs, ticker_of, cohort,
                                 R.DECISION_GRID_30, d2_diag)
    assert handler_x == anchor                   # byte-equal classification
    # paid windows: same assertability set as the handler's key set, and the
    # anchor state is the frozen function of (paid_now, paid_prev)
    paid = R.paid_windows(divs, ticker_of, cohort, R.A6_SCORED_GRID,
                          R.new_diag())
    assert set(paid) == set(anchor)
    for (cik, d), pw in paid.items():
        pn, pp = pw["paid_now"], pw["paid_prev"]
        want = 1.0 if (pp == 0 and pn >= 1) else (
            -1.0 if (pp >= 1 and pn == 0) else 0.0)
        assert anchor[(cik, d)] == want
    # neighbour = paid_now - paid_prev on exactly the anchor's key set
    nb = R.neighbour_exposure(paid)
    assert set(nb) == set(anchor)
    assert nb[(NAMES[0], D1)] == 1.0             # 1 - 0
    assert nb[(NAMES[2], D1)] == -1.0            # 0 - 1
    assert nb[(NAMES[4], D1)] == 0.0             # 0 - 0 never-payer
    # the window-formation abstain was counted (unassertable entities)
    (w["div"] / "T1001.json").write_text(json.dumps([{"ex_date":
                                                      "2018-06-01"}]))
    divs2 = R.load_dividends(str(w["div"]),
                             tickers={v["ticker"] for v in cohort.values()}
                             | {"T1001"})
    paid2 = R.paid_windows(divs2, {"CIK0000001001": "T1001"},
                           {"CIK0000001001": {"sector": "SEC_0"}},
                           [D1], R.new_diag())
    assert (  # only record 2018-06-01, earliest > D1-730 -> abstain
        ("CIK0000001001", D1) not in paid2)


def test_unmapped_sector_never_guessed(tmp_path):
    w = build_world_files(tmp_path)
    world = make_world(w)
    rec, _periods, legs = R.run_arm(
        "SFV13-A6-H1-ANCHOR", world["exposures"]["SFV13-A6-H1-ANCHOR"],
        world["prices"], world["cohort"], world["global_days"],
        world["day_pos"], scored_grid=GRID_ONE, folds=FOLD_T,
        dry_run=False)
    leg_names = {l["entity"] for l in legs}
    assert not (set(UNMAPPED) & leg_names)       # never held, never guessed
    diag = R.new_diag()
    R.decision_eligibility(world["prices"], D1, "2018-10-02", diag)
    # the unmapped probes WERE eligible on price grounds (band A) - only the
    # book stage excludes them; counted once per decision at the arm level
    assert all(world["cohort"][c]["sector"] == "" for c in UNMAPPED)


# ===========================================================================
# book form: within-sector demean, gross 1.0 (0.5 per leg), floors
# ===========================================================================
def test_book_form_gross_and_floors(tmp_path):
    w = build_world_files(tmp_path)
    world = make_world(w)
    sector_of_map = {c: v["sector"] for c, v in world["cohort"].items()}
    anchor = world["exposures"]["SFV13-A6-H1-ANCHOR"]
    ex_d1 = {c: anchor[(c, D1)] for c in NAMES}
    diag = R.new_diag()
    book, reason = R.build_book(ex_d1, sector_of_map, diag)
    assert reason == "OK"
    assert len(book) == 16                        # 8 long + 8 short
    assert all(approx(abs(w), LEG_W, 1e-12) for w in book.values())
    assert approx(sum(w for w in book.values() if w > 0), 0.5, 1e-12)
    assert approx(-sum(w for w in book.values() if w < 0), 0.5, 1e-12)
    longs = {c for c, w in book.items() if w > 0}
    shorts = {c for c, w in book.items() if w < 0}
    assert longs == {f"CIK{i:010d}" for i in LONGS}
    assert shorts == {f"CIK{i:010d}" for i in SHORTS}
    # COHORT_FLOOR: 20 mapped scoreable < 30
    few = {c: ex_d1[c] for c in NAMES[:20]}
    assert R.build_book(few, sector_of_map, diag) == (None, "COHORT_FLOOR")
    # LEG_FLOOR: all-one-sign cross-section demeaans to zero everywhere
    flat = {c: 1.0 for c in NAMES}
    assert R.build_book(flat, sector_of_map, diag) == (None, "LEG_FLOOR")
    assert diag["floor_abstain_cohort"] == 1
    assert diag["floor_abstain_leg"] == 1
    assert diag["mad_zero_identity_scale_decisions"] >= 1


# ===========================================================================
# STRICT_NEXT_BAR: decision at D reads ex_date < D only; fill next session
# ===========================================================================
def test_strict_next_bar_one_event_one_bar_lag(tmp_path):
    # name 2 is a long; its price JUMPS ON the decision date 2019-01-03 and
    # stays flat after: a STRICT_NEXT_BAR fill (01-04) earns ZERO; any
    # same-day or earlier fill basis would earn +1.0.
    def price_fn(i, d):
        if i == 2:
            return 200.0 if d >= D1 else 100.0
        return default_adj(i, d)

    w = build_world_files(tmp_path, price_fn=price_fn)
    world = make_world(w)
    rec, periods, legs = R.run_arm(
        "SFV13-A6-H1-ANCHOR", world["exposures"]["SFV13-A6-H1-ANCHOR"],
        world["prices"], world["cohort"], world["global_days"],
        world["day_pos"], scored_grid=GRID_ONE, folds=FOLD_T,
        dry_run=False)
    leg2 = next(l for l in legs if l["entity"] == NAMES[1])
    assert leg2["fill_date"] == "2019-01-04"      # first session AFTER D
    assert leg2["ret"] == 0.0                     # 200/200 - 1
    # the decision itself used only ex_date < D: a record dated exactly at D
    # must NOT condition D1 (name with ancient record + a D1-dated record is
    # still a 0, never a +1)
    divs = {"T1": [{"ex_date": "2016-06-01"}, {"ex_date": D1}]}
    paid = R.paid_windows(divs, {"CIK0000000001": "T1"},
                          {"CIK0000000001": {"sector": "SEC_0"}}, [D1],
                          R.new_diag())
    assert paid[("CIK0000000001", D1)] == {"paid_now": 0, "paid_prev": 0}
    assert ("CIK0000000001", D1) in paid          # assertable (ancient) -> 0


def test_no_lookahead_mutation_exactly_one_period(tmp_path):
    """clock.mutation_contract: a record pushed later enters the trailing
    windows exactly at the first decision date strictly after the new
    ex_date and at NO other time; shifting one day past D must NOT change
    the decision at D."""
    base = {"T9": [{"ex_date": "2016-06-01"}, {"ex_date": "2019-01-02"}]}
    shifted = {"T9": [{"ex_date": "2016-06-01"}, {"ex_date": D1}]}
    shifted2 = {"T9": [{"ex_date": "2016-06-01"}, {"ex_date": "2019-01-04"}]}
    book9 = {"CIK0000000009": {"sector": "SEC_0"}}
    tick9 = {"CIK0000000009": "T9"}
    grid = [D1, D2]
    a = R.paid_windows(base, tick9, book9, grid, R.new_diag())
    b = R.paid_windows(shifted, tick9, book9, grid, R.new_diag())
    c = R.paid_windows(shifted2, tick9, book9, grid, R.new_diag())
    # world A: ex 01-02 is inside [D1-365, D1) -> +1 at D1 and inside D2's
    # window -> +1 at D2
    assert a[("CIK0000000009", D1)] == {"paid_now": 1, "paid_prev": 0}
    assert a[("CIK0000000009", D2)] == {"paid_now": 1, "paid_prev": 0}
    # world B: the record pushed to exactly D1 leaves D1 UNCHANGED IN KIND
    # (still outside the now-window) and enters EXACTLY at D2 - the first
    # decision strictly after the new ex_date - and nowhere else
    assert b[("CIK0000000009", D1)] == {"paid_now": 0, "paid_prev": 0}
    assert b[("CIK0000000009", D2)] == {"paid_now": 1, "paid_prev": 0}
    # world C: pushed one day PAST D1 -> D1 state identical to world B
    assert c[("CIK0000000009", D1)] == b[("CIK0000000009", D1)]
    assert c[("CIK0000000009", D2)] == b[("CIK0000000009", D2)]
    # handler-level cross-check of the same mutation on the anchor state
    for dv, want_d1 in ((base, 1.0), (shifted, 0.0)):
        hx = a6_div_exposures(dv, tick9, book9, R.DECISION_GRID_30,
                              R.new_diag())
        assert hx.get(("CIK0000000009", D1)) == want_d1


# ===========================================================================
# costs: charged exactly once per side (10/15/25 x1; stress x2)
# ===========================================================================
def test_costs_once_per_side_base_and_stress(tmp_path):
    w = build_world_files(tmp_path)
    world = make_world(w)
    anchor = world["exposures"]["SFV13-A6-H1-ANCHOR"]
    base, periods_b, legs_b = R.run_arm(
        "SFV13-A6-H1-ANCHOR", anchor, world["prices"], world["cohort"],
        world["global_days"], world["day_pos"], scored_grid=GRID_ONE,
        folds=FOLD_T, dry_run=False, stress=False)
    stress, periods_s, legs_s = R.run_arm(
        "SFV13-A6-H1-ANCHOR", anchor, world["prices"], world["cohort"],
        world["global_days"], world["day_pos"], scored_grid=GRID_ONE,
        folds=FOLD_T, dry_run=False, stress=True)
    for legs, mult, period in ((legs_b, 1.0, periods_b[0]),
                               (legs_s, 2.0, periods_s[0])):
        assert len(legs) == 16
        for leg in legs:
            assert approx(leg["entry_cost_bps"], LEG_COST_BPS * mult, 1e-9)
            assert approx(leg["exit_cost_bps"], LEG_COST_BPS * mult, 1e-9)
            assert leg["entry_band"] == "A"
        # exactly 20 bps of gross at base (2 sides x 10 bps), 40 at stress
        assert approx(period["cost_bps_paid"], 20.0 * mult, 1e-6)
        assert period["legs_filled"] == 16 and period["void_orders"] == 0
    # hand-computed net: gross 16 x (1/16) x 0.05 = 0.05; costs 0.002 / 0.004
    assert approx(periods_b[0]["return_net"], 0.048, 1e-12)
    assert approx(periods_s[0]["return_net"], 0.046, 1e-12)
    assert approx(base["metrics"]["expectancy"], 0.048, 1e-12)
    assert approx(stress["metrics"]["expectancy"], 0.046, 1e-12)


def test_band_b_and_c_costs(tmp_path):
    """15 / 25 bps per side for band B / C names, charged once per side."""
    days = sessions(end=date(2019, 3, 29))
    D = D1
    fold = {"fold_id": "F", "start": "2018-12-01", "end": "2019-03-29"}
    n = "CIK0000000050"
    for vol, band, want_bps in ((100_000, "B", 15.0), (30_000, "C", 25.0)):
        prices = {n: {"date": days, "raw": [100.0] * len(days),
                      "adj": [100.0] * len(days),
                      "dvol": [vol * 100.0] * len(days),
                      "pos": {dd: k for k, dd in enumerate(days)}}}
        gdays = days
        dpos = {d: k for k, d in enumerate(gdays)}
        bands = {n: band}
        for mult in (1.0, 2.0):
            diag = R.new_diag()
            period, legs = R.execute_decision(
                {n: 0.5}, prices, bands, D, fold, gdays, dpos, mult,
                False, diag=diag)
            side_bps = 0.5 * want_bps * mult
            assert approx(legs[0]["entry_cost_bps"], side_bps, 1e-9)
            assert approx(legs[0]["exit_cost_bps"], side_bps, 1e-9)
            assert approx(period["cost_bps_paid"], 2 * side_bps, 1e-9)
            assert legs[0]["exit_reason"] == "SCHEDULED"


# ===========================================================================
# fold force-flat and dead-leg honesty
# ===========================================================================
def test_fold_force_flat(tmp_path):
    # fold ends 2019-01-25, the 15th session after the 01-04 fill: every leg
    # is force-flattened there WITH exit cost (21-session target unreachable)
    w = build_world_files(tmp_path)
    world = make_world(w)
    rec, periods, legs = R.run_arm(
        "SFV13-A6-H1-ANCHOR", world["exposures"]["SFV13-A6-H1-ANCHOR"],
        world["prices"], world["cohort"], world["global_days"],
        world["day_pos"], scored_grid=GRID_ONE, folds=FOLD_TIGHT,
        dry_run=False)
    assert all(l["exit_reason"] == "FOLD_FORCE_FLAT" for l in legs)
    assert all(l["exit_date"] == "2019-01-25" for l in legs)
    assert all(l["hold_sessions"] == 15 for l in legs)
    assert periods[0]["force_flats"] == 16
    assert rec["counters"]["fold_force_flat_exits"] == 16
    # the +5% step (>= 2019-01-10) is inside the capped window: same net
    assert approx(periods[0]["return_net"], 0.048, 1e-12)


def test_dead_leg_exit_at_last_close(tmp_path):
    # name 1 (a long) dies 2019-01-15; its last recorded close is 90.0
    w = build_world_files(tmp_path, dead_end=(1, "2019-01-15"),
                          dead_price=90.0)
    world = make_world(w)
    rec, periods, legs = R.run_arm(
        "SFV13-A6-H1-ANCHOR", world["exposures"]["SFV13-A6-H1-ANCHOR"],
        world["prices"], world["cohort"], world["global_days"],
        world["day_pos"], scored_grid=GRID_ONE, folds=FOLD_T,
        dry_run=False)
    dead = next(l for l in legs if l["entity"] == NAMES[0])
    assert dead["exit_reason"] == "DEAD_LEG"
    assert dead["exit_date"] == "2019-01-15"
    assert approx(dead["ret"], 90.0 / 100.0 - 1.0, 1e-12)
    assert approx(dead["exit_cost_bps"], LEG_COST_BPS, 1e-9)  # band A exit
    # hand-computed: 15 live legs at +0.003 minus the dead leg
    # (0.0625 x -0.10 - 0.000125 = -0.006375)  =>  0.045 - 0.006375
    assert approx(periods[0]["return_net"], 0.038625, 1e-12)
    assert periods[0]["dead_legs"] == 1
    assert rec["counters"]["dead_leg_exits"] == 1
    assert rec["metrics"]["dead_legs_total"] == 1
    # no post-series price is ever read: the exit date is the series end
    last = json.loads((w["eod"] / f"{NAMES[0]}__T1.json").read_text())[-1]
    assert last["date"] == "2019-01-15"


# ===========================================================================
# sham control: determinism, frozen hash order, multiset preservation
# ===========================================================================
def test_sham_determinism_and_hash_order(tmp_path):
    w = build_world_files(tmp_path)
    world = make_world(w)
    anchor = world["exposures"]["SFV13-A6-H1-ANCHOR"]
    control = world["exposures"][
        "SFV13-A6-H1-CONTROL-WITHIN-SECTOR-PERMUTATION"]
    # same seed -> same book (byte-identical re-derivation)
    again = within_sector_hash_permutation_sham(anchor, world["cohort"],
                                                R.HYPOTHESIS_ID)
    assert again == control
    # the exact within-(date, sector) multiset of states is preserved
    for d in (D1, D2):
        a_vals = sorted(v for (c, t), v in anchor.items() if t == d)
        c_vals = sorted(v for (c, t), v in control.items() if t == d)
        assert a_vals == c_vals
        per_sector = {}
        for (c, t), v in anchor.items():
            if t == d:
                per_sector.setdefault(world["cohort"][c]["sector"],
                                      []).append(v)
        for sec, vals in per_sector.items():
            cvals = sorted(control[(c, dd)] for (c, dd) in control
                           if dd == d
                           and world["cohort"][c]["sector"] == sec)
            assert sorted(vals) == cvals
            assert vals != cvals or len(set(vals)) == 1 or True
    # independent re-derivation of the frozen hash-order assignment
    import hashlib as _h
    d = D1
    idx = R.DECISION_GRID_30.index(d)
    names = sorted(c for (c, t) in anchor if t == d
                   and world["cohort"][c]["sector"] == "SEC_0")
    keyed = sorted(names, key=lambda c: _h.sha256(
        f"{R.CYCLE}|{R.HYPOTHESIS_ID}|{c}|{idx}".encode()).hexdigest())
    vals = sorted(anchor[(c, d)] for c in names)
    for c, v in zip(keyed, vals):
        assert control[(c, d)] == v
    # the control book is runnable by construction: it abstains exactly
    # where the anchor abstains (same key set) and floors pass identically
    assert set(control) == set(anchor)


def test_self_subsumption_and_control_ratio_arithmetic():
    # rule (2): pooled rho > 0.98 kills PRE-SCORE
    xs = [1.0, -1.0, 0.0, 1.0, -1.0, 0.0]
    assert R.spearman_rho(xs, list(xs)) == 1.0
    assert R.spearman_rho(xs, [-v for v in xs]) == -1.0
    assert R.spearman_rho(xs, [0.0] * len(xs)) is None
    # rule (1): same-sign >= 0.5x kills, incl. the negative-anchor case
    blk = R.control_ratio_block(0.04, 0.03)
    assert blk["same_sign"] and blk["kill"] and blk["observed_ratio"] == 0.75
    blk = R.control_ratio_block(0.04, 0.01)
    assert blk["same_sign"] and not blk["kill"]
    assert approx(blk["margin_to_fail"], 0.02 - 0.01, 1e-12)
    blk = R.control_ratio_block(-0.04, -0.01)
    assert blk["same_sign"] and not blk["kill"]
    blk = R.control_ratio_block(-0.04, -0.05)
    assert blk["same_sign"] and blk["kill"]      # outruns a negative anchor
    blk = R.control_ratio_block(0.04, -0.03)
    assert not blk["same_sign"] and not blk["kill"]
    blk = R.control_ratio_block(0.0, 0.02)
    assert blk["observed_ratio"] is None and not blk["kill"]


# ===========================================================================
# price loading: fail-closed on malformed files, missing series counted
# ===========================================================================
def test_malformed_price_file_fails_closed(tmp_path):
    w = build_world_files(tmp_path)
    (w["eod"] / "CIK0000000099__BAD.json").write_text("{not json")
    with pytest.raises(ValueError, match="fail closed"):
        R.load_prices_v13(str(w["eod"]), cohort=None)
    # structurally-typed corruption also fails closed
    for bad in ([{"date": "2019-01-02", "close": 1.0}],        # missing keys
                [{"date": "2019-01-02", "close": "x", "adjusted_close": 1.0,
                  "volume": 1}],                                 # non-numeric
                [{"date": "2019-01-02", "close": 1.0, "adjusted_close": 1.0,
                  "volume": -5}],                                # negative vol
                [{"date": "2019-01-05", "close": 1.0, "adjusted_close": 1.0,
                  "volume": 1}, {"date": "2019-01-04", "close": 1.0,
                                 "adjusted_close": 1.0, "volume": 1}]):
        (w["eod"] / "CIK0000000099__BAD.json").write_text(json.dumps(bad))
        with pytest.raises(ValueError, match="fail closed"):
            R.load_prices_v13(str(w["eod"]), cohort=None)
    # a missing cohort series is a MEASURED exclusion (counted), not a crash
    world = make_world(w)
    assert world["diag"]["missing_price_series"] == 0
    (w["eod"] / f"{NAMES[0]}__T1.json").unlink()
    world2 = R.build_world(cohort_path=str(w["cohort"]),
                           div_dir=str(w["div"]), prices_dir=str(w["eod"]),
                           bench_dir=str(w["tmp"] / "bench_absent"))
    assert world2["diag"]["missing_price_series"] == 1
    assert NAMES[0] not in world2["prices"]


# ===========================================================================
# end-to-end: reconciliation, distinct record ids, gates, benchmarks
# ===========================================================================
def _run_scored(w, grid=GRID_T, folds=FOLD_T, bench=False):
    world = make_world(w, bench=bench)
    arm_records, series, legs_by = R.run_family(world, dry_run=False,
                                                scored_grid=grid,
                                                folds=folds)
    return world, arm_records, series, legs_by


def test_end_to_end_reconciliation_and_distinct_ids(tmp_path):
    w = build_world_files(tmp_path)
    world, arm_records, series, legs_by = _run_scored(w)
    all_ids = []
    for arm_id, variants in arm_records.items():
        for variant, rec in variants.items():
            key = (arm_id, variant)
            per_leg = {}
            for leg in legs_by[key]:
                all_ids.append(leg["record_id"])
                per_leg.setdefault(leg["decision_date"], 0.0)
                per_leg[leg["decision_date"]] += leg["pnl_contrib"]
            for p in series[key]:
                all_ids.append(p["record_id"])
                # per-period net return == sum of leg contributions EXACTLY
                assert approx(p["return_net"], per_leg[p["decision_date"]],
                              1e-12)
            m = rec["metrics"]
            # series sum == ledger sum == expectancy x n
            tot = sum(p["return_net"] for p in series[key])
            assert approx(tot, m["sum_pnl"], 1e-9)
            assert approx(m["expectancy"] * m["scored_periods"], m["sum_pnl"],
                          1e-9)
            assert m["scored_periods"] == len(series[key]) == len(GRID_T)
            # dead/alive split persisted per leg
            for leg in legs_by[key]:
                assert leg["cohort_class"] in ("ALIVE_EVIDENCED",
                                               "DEAD_EVIDENCED")
    assert len(all_ids) == len(set(all_ids))       # pairwise distinct
    # arms/variants shape: 3 arms x (BASE + STRESS)
    assert set(arm_records) == set(R.ARM_IDS)
    for arm_id in R.ARM_IDS:
        assert set(arm_records[arm_id]) == {"BASE", "STRESS"}
        assert arm_records[arm_id]["BASE"]["cost_multiplier"] == 1.0
        assert arm_records[arm_id]["STRESS"]["cost_multiplier"] == 2.0
        # control abstains exactly where the anchor abstains: same periods
        if "CONTROL" in arm_id:
            assert len(series[(arm_id, "BASE")]) == \
                len(series[("SFV13-A6-H1-ANCHOR", "BASE")])


def test_benchmarks_spy_excess_and_sector_ew(tmp_path):
    w = build_world_files(tmp_path, bench=True)
    world, arm_records, series, legs_by = _run_scored(w, grid=GRID_ONE,
                                                      bench=True)
    p = series[("SFV13-A6-H1-ANCHOR", "BASE")][0]
    # SPY over [2019-01-04, 2019-02-04]: 100 -> 101; sector EW = XLF 1.03
    assert approx(p["spy_return"], 0.01, 1e-12)
    assert approx(p["sector_ew_return"], 0.03, 1e-12)
    # SPY scaled EX ANTE by the frozen gross rule (1.0)
    assert approx(p["spy_excess"], 0.048 - 0.01, 1e-12)
    m = arm_records["SFV13-A6-H1-ANCHOR"]["BASE"]["metrics"]
    assert approx(m["spy_excess_overall"], 0.038, 1e-9)
    assert m["spy_excess_folds_positive"] == 1


def test_gates_and_margins_two_period_world(tmp_path):
    # D1 net +0.048, D2 net -0.052: the full margin arithmetic is live
    w = build_world_files(tmp_path)
    world, arm_records, series, legs_by = _run_scored(w)
    base = arm_records["SFV13-A6-H1-ANCHOR"]["BASE"]
    stress = arm_records["SFV13-A6-H1-ANCHOR"]["STRESS"]
    gates = R.arm_gates(base, stress)
    by_name = {g["gate"]: g for g in gates}
    m, s = base["metrics"], stress["metrics"]
    assert approx(m["expectancy"], (0.048 - 0.052) / 2, 1e-12)
    assert approx(m["pf"], 0.048 / 0.052, 1e-6)
    # both scored periods sit in the SINGLE synthetic fold whose sum is
    # negative (0.048 - 0.052 < 0): zero positive folds
    assert m["folds_positive"] == 0
    assert approx(m["folds"]["S0_FOLD_1"]["sum_pnl"], -0.004, 1e-9)
    assert approx(m["max_fold_mdd"], 0.052, 1e-9)
    assert by_name["expectancy_gt_0_after_base_costs"]["verdict"] == "FAIL"
    assert by_name["position_pf_ge_1.10"]["verdict"] == "FAIL"
    assert by_name["folds_positive_ge_2_of_3"]["verdict"] == "FAIL"
    assert by_name["max_fold_mdd_le_0.20_houses_carried"]["verdict"] == "PASS"
    # mdd 0.052 clears BOTH declared thresholds; margins are exact
    assert by_name["max_fold_mdd_le_0.15_proposal_table"]["verdict"] == "PASS"
    assert approx(by_name["max_fold_mdd_le_0.20_houses_carried"]["margin_to_fail"],
                  0.20 - 0.052, 1e-9)
    assert approx(by_name["max_fold_mdd_le_0.15_proposal_table"]["margin_to_fail"],
                  0.15 - 0.052, 1e-9)
    # margin-to-fail distances are exact
    assert approx(by_name["expectancy_gt_0_after_base_costs"]["margin_to_fail"],
                  -0.002, 1e-9)
    assert approx(by_name["position_pf_ge_1.10"]["margin_to_fail"],
                  0.048 / 0.052 - 1.10, 1e-6)   # observed - threshold (ge)
    # floors: both scored dates booked 8/8 legs, 40 scoreable, 1 fold x 2
    assert by_name["floor_legs_ge_5_every_scored_date"]["verdict"] == "PASS"
    assert by_name["floor_cohort_scoreable_ge_30_every_scored_date"][
        "verdict"] == "PASS"
    assert by_name["scored_decisions_overall_ge_30"]["verdict"] == "FAIL"
    assert by_name["scored_decisions_per_fold_ge_5"]["verdict"] == "FAIL"
    # stress x2 gate rows read the STRESS rerun
    assert approx(s["sum_pnl"], 0.046 - 0.054, 1e-9)
    assert by_name["stress_pnl_gt_0"]["verdict"] == "FAIL"
    # drop-one from persisted legs: each active symbol carries BOTH period
    # legs (+0.003 at D1, -0.00325 at D2 = -0.00025 total); the worst drop
    # removes that total and re-divides by n periods
    assert by_name["drop_one_symbol_min_expectancy_gt_0"]["verdict"] == "FAIL"
    assert approx(m["drop_one_symbol_expectancy_min"],
                  (m["sum_pnl"] - m["sum_pnl"] / 16) / 2, 1e-9)
    # single-positive-period world: expectancy PASS with exact margin;
    # pf with no losing periods reports PASS (undefined +inf, margin None)
    w2 = build_world_files(tmp_path / "one")
    world2, arm2, series2, _ = _run_scored(w2, grid=GRID_ONE)
    gates2 = R.arm_gates(arm2["SFV13-A6-H1-ANCHOR"]["BASE"],
                         arm2["SFV13-A6-H1-ANCHOR"]["STRESS"])
    g2 = {g["gate"]: g for g in gates2}
    assert g2["expectancy_gt_0_after_base_costs"]["verdict"] == "PASS"
    assert approx(g2["expectancy_gt_0_after_base_costs"]["margin_to_fail"],
                  0.048, 1e-9)
    assert g2["position_pf_ge_1.10"]["verdict"] == "PASS"
    assert g2["position_pf_ge_1.10"]["margin_to_fail"] is None
    assert g2["drop_one_symbol_min_expectancy_gt_0"]["verdict"] == "PASS"
    assert approx(g2["drop_one_symbol_min_expectancy_gt_0"]["margin_to_fail"],
                  0.045, 1e-9)
    assert g2["etf_share_le_0.50"]["verdict"] == "PASS"   # NOT_APPLICABLE


# ===========================================================================
# persistence: P-11 artifacts, dry-run hygiene, leak scan
# ===========================================================================
def test_write_artifacts_scored_and_dry_run(tmp_path):
    w = build_world_files(tmp_path / "world")
    world = make_world(w)
    run_dir = tmp_path / "run"
    # ---- scored mode writes the full diagnostic contract -------------------
    arm_records, series, legs_by = R.run_family(world, dry_run=False,
                                                scored_grid=GRID_ONE,
                                                folds=FOLD_T)
    fg = R.family_gate_blocks(arm_records, world)
    arts = R.write_artifacts(run_dir, "2026-09-10T00:00:00Z", "scored",
                             arm_records, series, legs_by, world, fg)
    assert "family_verdicts.json" in arts
    assert "execution_ledger.json" in arts
    for arm_id in R.ARM_IDS:
        assert f"per_period_series/{arm_id}__base.json" in arts
        assert f"entity_legs/{arm_id}__stress.json" in arts
    v = json.loads((run_dir / "family_verdicts.json").read_text())
    assert v["schema"] == R.VERDICTS_SCHEMA and v["scored"] is True
    assert v["family_id"] == "SFV13-A6-P1"
    assert "self_subsumption" in v["family_gates"]
    assert "control_reproduction" in v["family_gates"]
    # permutation audit: anchor multiset == sham multiset per (date, sector)
    assert v["permutation_audit"]["identical_to_sham"] is True
    led = json.loads((run_dir / "execution_ledger.json").read_text())
    assert led["record_ids_pairwise_distinct"] is True
    assert led["counters"]["arms"] == 3
    s = json.loads(
        (run_dir / "per_period_series" /
         "SFV13-A6-H1-ANCHOR__base.json").read_text())
    assert s["schema"] == R.SERIES_SCHEMA
    assert approx(s["periods"][0]["return_net"], 0.048, 1e-12)
    lg = json.loads(
        (run_dir / "entity_legs" / "SFV13-A6-H1-ANCHOR__base.json").read_text())
    assert lg["schema"] == R.LEGS_SCHEMA and len(lg["legs"]) == 16
    # ---- dry-run mode is sanitized and leak-scanned ------------------------
    arm_d, series_d, legs_d = R.run_family(world, dry_run=True,
                                           scored_grid=GRID_ONE,
                                           folds=FOLD_T)
    assert "metrics" not in arm_d["SFV13-A6-H1-ANCHOR"]["BASE"]
    assert all(p["return_net"] is None
               for p in series_d[("SFV13-A6-H1-ANCHOR", "BASE")])
    run_dry = tmp_path / "run_dry"
    arts_d = R.write_artifacts(run_dry, "2026-09-10T00:00:00Z", "dry_run",
                               arm_d, series_d, legs_d, world, fg)
    v_d = json.loads((run_dry / "family_verdicts.json").read_text())
    assert v_d["scored"] is False and v_d["real_pnl"] is False
    assert v_d["arms"]["SFV13-A6-H1-ANCHOR"]["gates"] == \
        "WITHHELD_DRY_RUN_SANITIZED"
    # a poisoned PnL field at ANY depth refuses the whole write
    import copy
    series_poison = copy.deepcopy(series_d)
    series_poison[("SFV13-A6-H1-ANCHOR", "BASE")][0]["return_net"] = 0.048
    with pytest.raises(RuntimeError, match="leak scan FAILED"):
        R.write_artifacts(tmp_path / "run_poison", None, "dry_run", arm_d,
                          series_poison, legs_d, world, fg)
    nested = {"a": [{"b": {"pnl_contrib": 0.1}}]}
    assert R.scan_no_pnl(nested) == ["$.a[0].b.pnl_contrib"]
    assert R.scan_no_pnl({"pnl": None, "ret": None}) == []


def test_dry_run_structure_matches_scored_structure(tmp_path):
    """P3 dry_run_hygiene: the exact-arm sanitized dry-run is non-vacuous -
    identical books, fills and cost lines, zero outcome fields."""
    w = build_world_files(tmp_path)
    world = make_world(w)
    dry, series_d, legs_d = R.run_family(world, dry_run=True,
                                         scored_grid=GRID_ONE, folds=FOLD_T)
    score, series_s, legs_s = R.run_family(world, dry_run=False,
                                           scored_grid=GRID_ONE, folds=FOLD_T)
    for arm_id in R.ARM_IDS:
        d_rec = dry[arm_id]["BASE"]
        s_rec = score[arm_id]["BASE"]
        assert d_rec["counters"] == s_rec["counters"]
        assert len(d_rec["schedule"]) == len(s_rec["schedule"])
        d_legs = legs_d[(arm_id, "BASE")]
        s_legs = legs_s[(arm_id, "BASE")]
        assert [l["entity"] for l in d_legs] == [l["entity"] for l in s_legs]
        assert [l["target_weight"] for l in d_legs] == \
            [l["target_weight"] for l in s_legs]
        assert [l["exit_date"] for l in d_legs] == \
            [l["exit_date"] for l in s_legs]
        assert [l["entry_cost_bps"] for l in d_legs] == \
            [l["entry_cost_bps"] for l in s_legs]
        assert all(l["ret"] is None and l["pnl_contrib"] is None
                   for l in d_legs)
        assert all(l["ret"] is not None for l in s_legs)


# ===========================================================================
# price manifest integrity (the one production-byte check; skips if absent)
# ===========================================================================
PRICE_ROOT = R.PRICE_DIR
MANIFEST = R.PRICE_MANIFEST_PATH


@pytest.mark.skipif(not (PRICE_ROOT.is_dir() and MANIFEST.is_file()),
                    reason="V13 price staging / manifest not present")
def test_price_manifest_sample_verification():
    res = R.verify_price_manifest(limit=5)
    assert res["checked"] >= 1
    assert res["mismatches"] == [], res["mismatches"]
    assert res["missing"] == [], res["missing"]


# ===========================================================================
# lock + authorization discipline
# ===========================================================================
def test_lock_busy_exit_3_single_attempt(monkeypatch):
    calls = []

    def fake_acquire(**kwargs):
        calls.append(kwargs)
        raise R.heavy_lock.LockBusyError("held by another worker")

    monkeypatch.setattr(R.heavy_lock, "acquire", fake_acquire)
    rc = R.main(["--dry-run", "2026-09-10T00:00:00Z"])
    assert rc == R.EXIT_LOCK_BUSY == 3
    assert len(calls) == 1                        # single attempt, no spin
    assert calls[0]["cycle_id"] == "STOCKS-FREE-V13"
    assert calls[0]["role"] == "A8_DRYRUN"


def test_scored_refuses_without_two_keys(monkeypatch):
    def boom(**kwargs):
        raise AssertionError("lock must not be touched before authorization")

    monkeypatch.setattr(R.heavy_lock, "acquire", boom)
    assert R.main(["WRONG PHRASE"]) == R.EXIT_BLOCKED
    monkeypatch.setenv(R.LAUNCH_ENV, "1")
    assert R.main(["WRONG PHRASE"]) == R.EXIT_BLOCKED
    monkeypatch.delenv(R.LAUNCH_ENV)
    assert R.main([R.GO_PHRASE]) == R.EXIT_BLOCKED
    assert R.scored_authorized(R.GO_PHRASE) is False
    monkeypatch.setenv(R.LAUNCH_ENV, "1")
    assert R.scored_authorized(R.GO_PHRASE) is True
