"""SFV9-A4-H2 family runner + driver tests.

Handbook 14.2/14.3 discipline: synthetic hand-computed fixtures ONLY.
No production data byte is read, no production outcome is pinned: the
hand-computed PnL expectations below are properties of the FIXTURE
arithmetic (flat prices, one price step on a dying name, band-A costs),
never of a scored production cell.
"""

import json
from datetime import date, timedelta

import pytest

from research.assets.stocks import kernel_band_cost_v9 as kernel
from research.assets.stocks import v9_e_driver as drv
from research.assets.stocks import v9_family_runner as r

RE = r.RE_FIELD
CASH = r.CASH_FIELD
ASSETS = r.ASSETS_FIELD

FOLDS_SMALL = [
    {"fold_id": "S0_FOLD_1", "start": "2016-01-01", "end": "2018-12-31"},
    {"fold_id": "S0_FOLD_2", "start": "2019-01-01", "end": "2019-12-31"},
    {"fold_id": "S0_FOLD_3", "start": "2020-01-01", "end": "2021-12-31"},
]
FOLDS_BIG = [
    {"fold_id": "S0_FOLD_1", "start": "2016-01-01", "end": "2017-06-30"},
    {"fold_id": "S0_FOLD_2", "start": "2017-07-01", "end": "2019-06-30"},
    {"fold_id": "S0_FOLD_3", "start": "2019-07-01", "end": "2021-12-31"},
]
DEAD = "CIK000000011"  # j=11, an anchor LONG in the weekly-vintage world


def _sessions(n, start=date(2015, 1, 2)):
    days, cur = [], start
    while len(days) < n:
        if cur.weekday() < 5:
            days.append(cur.isoformat())
        cur += timedelta(days=1)
    return days


def _sector(j):
    return "SEC0" if j % 2 == 0 else "SEC1"


def build_world(tmp, n_sessions=911, dead_last_idx=None, dead_price=110.0,
                start=date(2015, 1, 2), panel_end=date(2019, 1, 1)):
    """12 names, 2 sectors (j = 2i+s alternates sectors across the score
    order), flat 100.0 prices, band A liquidity, WEEKLY panel vintages.

    Prices start 2015-01-02 so fold 1 (2016-01-01..) has its first decision
    at a global index >= 252: every decision has a t-252 prior gate, and
    weekly vintages give every (decision, prior-gate) pair a 49-52 week
    fiscal gap (~343-364 days) inside [330, 400] - every decision populates.

    Hand computations (anchor arm): the weekly RE alternation (+0.5 at even
    week parities) is name-INDEPENDENT, so depletion is identical across
    names and
      score_j = (dep - j)/100, dep in {0, +-0.5}  -> strictly decreasing in j;
      terciles: L = {j8,j9,j10,j11}, S = {j0,j1,j2,j3}, w = +-0.125
      (two active sectors x two legs per side: 0.5/(2*2)).
    Fold-local decision k sits at fold session index 63 + 21k; warmup is
    local k = 0..3 (their entry fills cost 10 bps into a discarded window).
    """
    days = _sessions(n_sessions, start)
    eod = tmp / "eod"
    eod.mkdir(parents=True, exist_ok=True)
    names = [f"CIK{j:09d}" for j in range(12)]
    for j, cik in enumerate(names):
        bars = []
        for i, d in enumerate(days):
            if cik == DEAD and dead_last_idx is not None and i > dead_last_idx:
                continue  # the dying name's series ends here
            px = dead_price if (cik == DEAD and dead_last_idx == i) else 100.0
            bars.append({"date": d, "open": px, "high": px, "low": px,
                         "close": px, "adjusted_close": px, "volume": 1_000_000})
        (eod / f"{cik}__T{j}.json").write_text(json.dumps(bars))
    panel = tmp / "panel.jsonl"
    with open(panel, "w") as f:
        cur = date(2014, 1, 3)  # a Friday
        week = 0
        while cur < panel_end:
            eff = cur.isoformat()
            avail = (cur + timedelta(days=5)).isoformat()
            for j, cik in enumerate(names):
                re_v = (190.0 - 2 * j) + (0.5 if week % 2 else 0.0)
                for fld, v in ((RE, re_v), (CASH, float(j)), (ASSETS, 100.0)):
                    f.write(json.dumps({"e": cik, "s": _sector(j), "f": fld,
                                        "u": "USD", "v": v, "eff": eff,
                                        "avail": avail}) + "\n")
            cur += timedelta(days=7)
            week += 1
    cohort = tmp / "cohort_v9.json"
    cohort.write_text(json.dumps(
        {"members": {"ALIVE_EVIDENCED": [{"cik": c} for c in names
                                         if c != DEAD]}}))
    scan = tmp / "scan.json"
    scan.write_text(json.dumps({"dead_verdicts": {
        DEAD: {"verdict": "DEAD_PRICE_CONFIRMED"},
        "CIK999999999": {"verdict": "NOT_DEAD_PRICE_SURVIVAL"}}}))
    manifest = tmp / "manifest.json"
    manifest.write_text(json.dumps({"files": {}}))
    return {"days": days, "names": names, "panel": panel, "cohort": cohort,
            "scan": scan, "manifest": manifest, "eod": eod,
            "bench": tmp / "bench", "tmp": tmp}


def build_big_world(tmp):
    """Same weekly-vintage construction over a longer calendar and vintage
    history plus the real three-fold split: ~60 scored decisions, so the
    sampling floor and every non-vacuity gate are satisfiable."""
    return build_world(tmp, n_sessions=1830, start=date(2015, 1, 2),
                       panel_end=date(2023, 1, 1))


def _wire(monkeypatch, w, folds=FOLDS_SMALL):
    monkeypatch.setattr(r, "PANEL", str(w["panel"]))
    monkeypatch.setattr(r, "PRICES", str(w["eod"]))
    monkeypatch.setattr(r, "BENCH", str(w["bench"]))
    monkeypatch.setattr(r, "FOLDS", folds)
    monkeypatch.setattr(r, "COHORT_PATH", str(w["cohort"]))
    monkeypatch.setattr(r, "INTEGRITY_SCAN_PATH", str(w["scan"]))
    monkeypatch.setattr(r, "PRICE_MANIFEST_PATH", str(w["manifest"]))


def _load(w, folds=FOLDS_SMALL):
    universe = r.load_universe(w["cohort"], w["scan"])
    panel, counts = r.load_panel({RE, CASH, ASSETS}, panel_path=w["panel"])
    prices = r.load_prices(str(w["eod"]))
    folds = r.fold_sessions(prices, folds)
    return universe, panel, prices, folds


def _book_expected():
    """Hand-computed anchor book: L={j0..j3}, S={j8..j11}, w=+-0.125."""
    out = {}
    for j in (0, 1, 2, 3):
        out[f"CIK{j:09d}"] = "L"
    for j in (8, 9, 10, 11):
        out[f"CIK{j:09d}"] = "S"
    return out


def _pnl_at(rec, d):
    for x in rec["metrics"]["decision_pnl"]:
        if x["d"] == d:
            return x["pnl"]
    raise AssertionError(f"no scored decision at {d}")


@pytest.fixture()
def small_world(tmp_path, monkeypatch):
    w = build_world(tmp_path)
    _wire(monkeypatch, w)
    return w


@pytest.fixture()
def healthy(small_world):
    u, panel, prices, folds = _load(small_world)
    return {"w": small_world, "universe": u, "panel": panel,
            "prices": prices, "folds": folds}


# ------------------------------------------------------- signal goldens

def _golden_entity(re_prior=( "2018-06-01", "2017-12-31", 800.0),
                   re_now=("2019-06-01", "2018-12-31", 600.0),
                   cash=("2019-06-01", "2018-12-31", 150.0),
                   assets=("2019-06-01", "2018-12-31", 1000.0)):
    rows = {RE: [re_prior, re_now], CASH: [cash], ASSETS: [assets]}
    return {"sector": "SEC0", "rows": rows}


ANCHOR_SPEC = {"kind": "depletion_runway", "direction": "low_long",
               "warmup_decisions": 4}
NEIGHBOUR_SPEC = {"kind": "depletion_velocity", "direction": "low_long",
                  "warmup_decisions": 0}
CONTROL_SPEC = {"kind": "cash_ratio", "direction": "high_long",
                "warmup_decisions": 0}


def test_signal_golden_anchor_neighbour_control():
    """Hand golden: depletion = 800-600 = 200, cash = 150, assets = 1000.
    anchor = (200-150)/1000 = 0.05; neighbour = 200/1000 = 0.20;
    control = 150/1000 = 0.15."""
    ent = _golden_entity()
    assert r.signal_value(ANCHOR_SPEC, ent, "2019-07-01", "2018-07-01") == pytest.approx(0.05)
    assert r.signal_value(NEIGHBOUR_SPEC, ent, "2019-07-01", "2018-07-01") == pytest.approx(0.20)
    assert r.signal_value(CONTROL_SPEC, ent, "2019-07-01", None) == pytest.approx(0.15)


def test_fiscal_guard_330_400_boundaries():
    """The RE pair must be 330-400 effective days apart; 329/401 reject.
    The control carries no RE pair and is unaffected."""
    from datetime import date as _d
    base = _d(2017, 12, 31)
    for gap, ok in ((329, False), (330, True), (365, True), (400, True), (401, False)):
        eff_now = (base + timedelta(days=gap)).isoformat()
        ent = _golden_entity(re_now=("2019-06-01", eff_now, 600.0))
        a = r.signal_value(ANCHOR_SPEC, ent, "2019-07-01", "2018-07-01")
        if ok:
            assert a == pytest.approx(0.05)
        else:
            assert a is None
        # neighbour shares the guard...
        n = r.signal_value(NEIGHBOUR_SPEC, ent, "2019-07-01", "2018-07-01")
        assert (n is not None) == ok
        # ...the control does not (single vintage, no pair)
        assert r.signal_value(CONTROL_SPEC, ent, "2019-07-01", None) == pytest.approx(0.15)


def test_800d_clock_at_each_legs_own_gate():
    """Every leg cites the 800-day bounded clock at ITS OWN gate."""
    ent = _golden_entity()
    # now-leg stale at the decision gate (newest vintage filed 2019-06-01,
    # decision 2022-07-01 -> age 1126d > 800)
    assert r.signal_value(ANCHOR_SPEC, ent, "2022-07-01", "2021-07-01") is None
    # prior-leg stale at ITS OWN gate (gate 2022-01-01: newest vintage is
    # 945d old > 800) while the now-leg at 2019-07-01 is fresh
    assert r.signal_value(ANCHOR_SPEC, ent, "2019-07-01", "2022-01-01") is None
    # missing prior gate entirely -> unpopulated (never proxied)
    assert r.signal_value(ANCHOR_SPEC, ent, "2019-07-01", None) is None


def test_asof_strict_gate_one_bar_lag():
    """A filing ON the decision date is not visible (gate = 00:00 UTC,
    stamp = end of filed day); the next session sees it: one-bar lag."""
    rows = [("2019-06-01", "2018-12-31", 600.0),
            ("2018-06-01", "2017-12-31", 800.0)]
    rows.sort()
    ent = {"sector": "SEC0", "rows": {
        RE: rows, CASH: [("2019-06-01", "2018-12-31", 150.0)],
        ASSETS: [("2019-06-01", "2018-12-31", 1000.0)]}}
    # decision ON the avail day: new vintage invisible
    a = r.signal_value(ANCHOR_SPEC, ent, "2019-06-01", "2018-07-01")
    assert a is None  # (RE pair would be same-vintage -> guard rejects)
    # one session later (next calendar day): visible
    a = r.signal_value(ANCHOR_SPEC, ent, "2019-06-02", "2018-07-01")
    assert a == pytest.approx(0.05)


def test_no_lookahead_mutation():
    """Adding a FUTURE filing must not change a PAST decision."""
    import copy
    ent = _golden_entity()
    before = r.signal_value(ANCHOR_SPEC, ent, "2019-07-01", "2018-07-01")
    ent2 = copy.deepcopy(ent)
    ent2["rows"][RE].append(("2019-08-01", "2019-05-31", 999.0))  # filed later
    ent2["rows"][RE].sort()
    after = r.signal_value(ANCHOR_SPEC, ent2, "2019-07-01", "2018-07-01")
    assert before == after == pytest.approx(0.05)


def test_nan_and_zero_denominator_unpopulated():
    ent = _golden_entity(re_now=("2019-06-01", "2018-12-31", float("nan")))
    assert r.signal_value(ANCHOR_SPEC, ent, "2019-07-01", "2018-07-01") is None
    ent = _golden_entity(assets=("2019-06-01", "2018-12-31", 0.0))
    assert r.signal_value(ANCHOR_SPEC, ent, "2019-07-01", "2018-07-01") is None
    assert r.signal_value(CONTROL_SPEC, ent, "2019-07-01", None) is None
    ent = _golden_entity(cash=("2019-06-01", "2018-12-31", float("nan")))
    assert r.signal_value(ANCHOR_SPEC, ent, "2019-07-01", "2018-07-01") is None


def test_anchor_vs_control_distinctness():
    """Tiny panel: depletion-carrying name A vs cash-rich name B.
    anchor: A=(100-50)/1000=0.05 > B=(0-500)/1000=-0.5 (A ranks higher burn).
    control (high_long): B=0.5 > A=0.05 - rank vectors are NOT identical.
    neighbour keeps the anchor's ordering (trajectory support direction)."""
    a = {"sector": "SEC0", "rows": {
        RE: [("2019-06-01", "2018-12-31", 900.0),   # now (depleted by 100)
             ("2018-06-01", "2017-12-31", 1000.0)],  # prior
        CASH: [("2019-06-01", "2018-12-31", 50.0)],
        ASSETS: [("2019-06-01", "2018-12-31", 1000.0)]}}
    b = {"sector": "SEC0", "rows": {
        RE: [("2019-06-01", "2018-12-31", 1000.0),  # no depletion
             ("2018-06-01", "2017-12-31", 1000.0)],
        CASH: [("2019-06-01", "2018-12-31", 500.0)],
        ASSETS: [("2019-06-01", "2018-12-31", 1000.0)]}}
    anchor = {n: r.signal_value(ANCHOR_SPEC, e, "2019-07-01", "2018-07-01")
              for n, e in (("A", a), ("B", b))}
    control = {n: r.signal_value(CONTROL_SPEC, e, "2019-07-01", None)
               for n, e in (("A", a), ("B", b))}
    neighbour = {n: r.signal_value(NEIGHBOUR_SPEC, e, "2019-07-01", "2018-07-01")
                 for n, e in (("A", a), ("B", b))}
    assert anchor["A"] > anchor["B"]
    assert control["B"] > control["A"]
    assert neighbour["A"] > neighbour["B"]  # same ordering as the anchor
    ra, rc, rn = (r.pct_rank(anchor), r.pct_rank(control), r.pct_rank(neighbour))
    assert (ra["A"] > ra["B"]) != (rc["A"] > rc["B"])  # not rank-identical
    assert (ra["A"] > ra["B"]) == (rn["A"] > rn["B"])


# ---------------------------------------------------------- data layer

def test_universe_legs_small_world(small_world):
    uni = r.load_universe(small_world["cohort"], small_world["scan"])
    assert DEAD in uni                        # DEAD_PRICE_CONFIRMED included
    assert "CIK999999999" not in uni          # NOT_DEAD_PRICE_SURVIVAL excluded
    assert len(uni) == 12                     # 11 alive + 1 dead


def test_panel_unit_and_value_filter(tmp_path):
    p = tmp_path / "p.jsonl"
    with open(p, "w") as f:
        f.write(json.dumps({"e": "E1", "s": "S", "f": ASSETS, "u": "USD",
                            "v": 10.0, "eff": "2018-01-01",
                            "avail": "2018-02-01"}) + "\n")
        f.write(json.dumps({"e": "E1", "s": "S", "f": ASSETS, "u": "shares",
                            "v": 99.0, "eff": "2018-01-01",
                            "avail": "2018-02-01"}) + "\n")
        f.write(json.dumps({"e": "E1", "s": "S", "f": ASSETS, "u": "USD",
                            "v": None, "eff": "2018-01-01",
                            "avail": "2018-02-01"}) + "\n")
        f.write(json.dumps({"e": "E1", "s": "S", "f": ASSETS, "u": "USD",
                            "v": "bad", "eff": "2018-01-01",
                            "avail": "2018-02-01"}) + "\n")
    panel, counts = r.load_panel({ASSETS}, panel_path=str(p))
    assert counts["rows_read"] == 4 and counts["rows_kept"] == 1
    assert panel["E1"]["rows"][ASSETS] == [("2018-02-01", "2018-01-01", 10.0)]


def test_malformed_price_file_fail_closed(small_world):
    (small_world["eod"] / "CIKbroken__X.json").write_text("{not json")
    with pytest.raises(json.JSONDecodeError):
        r.load_prices(str(small_world["eod"]))


def test_missing_panel_field_fail_closed(healthy):
    panel = {k: v for k, v in healthy["panel"].items()}
    for ent in panel.values():
        ent["rows"].pop(RE, None)
    with pytest.raises(ValueError):
        r.run_arm("SFV9-A4-H2-ANCHOR", panel, healthy["prices"],
                  healthy["folds"], dry_run=True)


def test_band_cost_via_kernel_fail_closed():
    # costs flow through the kernel only; missing band = hard error (L-I3)
    assert r.change_cost("X", 0.25, {"X": "B"}, 1.0) == pytest.approx(0.25 * 15.0 / 10_000.0)
    with pytest.raises(kernel.BandResolutionError):
        r.change_cost("DEADNAME", 0.25, {"OTHER": "A"}, 1.0)


# --------------------------------------------------------- book + grid

def test_book_weights_hand_computed(healthy):
    rec = r.run_arm("SFV9-A4-H2-ANCHOR", healthy["panel"], healthy["prices"],
                    healthy["folds"], dry_run=True, universe=healthy["universe"])
    first = next(x for x in rec["schedule"]
                 if x.get("event") is None and x["legs"] > 0)
    # first decision of fold 1: fold-local index 63
    sess0 = healthy["folds"][0]["sessions"]
    assert first["decision_date"] == sess0[63]
    assert first["legs"] == 8                      # 4 long + 4 short
    assert first["eligible"] == 12 and first["populated"] == 12
    assert first["populated_frac"] == pytest.approx(1.0)
    # entry fills: 8 legs x 0.125 x 10 bps = 10 bps of notional, once
    assert first["turnover"] == pytest.approx(1.0)
    assert first["cost_bps_paid"] == pytest.approx(10.0)
    assert first["warmup"] is True  # fold-1 warmup carries the entry cost


def test_dry_run_no_outcome_fields(healthy):
    rec = r.run_arm("SFV9-A4-H2-ANCHOR", healthy["panel"], healthy["prices"],
                    healthy["folds"], dry_run=True, universe=healthy["universe"])
    blob = json.dumps(rec)
    for forbidden in ("pnl", "expectancy", "metrics", "pf", "mdd", "alpha"):
        assert forbidden not in blob, f"leak: {forbidden} in dry-run record"
    assert rec["dry_run"] is True and rec["scored"] is False


def test_dry_run_deterministic_double_generation(healthy):
    a = r.run_arm("SFV9-A4-H2-ANCHOR", healthy["panel"], healthy["prices"],
                  healthy["folds"], dry_run=True, universe=healthy["universe"])
    b = r.run_arm("SFV9-A4-H2-ANCHOR", healthy["panel"], healthy["prices"],
                  healthy["folds"], dry_run=True, universe=healthy["universe"])
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_record_ids_pairwise_distinct(healthy):
    for arm in r.ARM_IDS:
        rec = r.run_arm(arm, healthy["panel"], healthy["prices"],
                        healthy["folds"], dry_run=True,
                        universe=healthy["universe"])
        ids = [x["record_id"] for x in rec["schedule"]]
        assert len(set(ids)) == len(ids) > 0


def test_decision_grid_inherited(healthy):
    _, _, prices, folds = _load(healthy["w"])
    dates, idx = r.decision_grid(folds[0]["sessions"])
    assert idx == list(range(63, len(folds[0]["sessions"]), 21))
    assert dates[0] == folds[0]["sessions"][63]


# ------------------------------------------------ scored-path mechanics

def _scored(healthy, arm="SFV9-A4-H2-ANCHOR", monkeypatch=None, stress=False):
    monkeypatch.setenv("V9_LAUNCH_AUTHORIZED", "1")
    return r.run_arm(arm, healthy["panel"], healthy["prices"],
                     healthy["folds"], dry_run=False,
                     owner_go=r.GO_PHRASE, universe=healthy["universe"],
                     stress=stress)


def test_scored_refused_without_two_keys(healthy, monkeypatch):
    monkeypatch.delenv("V9_LAUNCH_AUTHORIZED", raising=False)
    with pytest.raises(SystemExit):  # no phrase
        r.run_arm("SFV9-A4-H2-ANCHOR", healthy["panel"], healthy["prices"],
                  healthy["folds"], dry_run=False)
    with pytest.raises(SystemExit):  # wrong phrase, no env
        r.run_arm("SFV9-A4-H2-ANCHOR", healthy["panel"], healthy["prices"],
                  healthy["folds"], dry_run=False, owner_go="GO STOCKS V8 SCORED EXECUTION")
    monkeypatch.setenv("V9_LAUNCH_AUTHORIZED", "1")
    with pytest.raises(SystemExit):  # env set but phrase wrong
        r.run_arm("SFV9-A4-H2-ANCHOR", healthy["panel"], healthy["prices"],
                  healthy["folds"], dry_run=False, owner_go="wrong")
    # both keys -> the scored path runs (synthetic fixture, fixture pnl only)
    rec = r.run_arm("SFV9-A4-H2-ANCHOR", healthy["panel"], healthy["prices"],
                    healthy["folds"], dry_run=False, owner_go=r.GO_PHRASE,
                    universe=healthy["universe"])
    assert rec["scored"] is True and "metrics" in rec
    assert all({"d", "fill_d", "end_d", "fold", "pnl"} <= set(x)
               for x in rec["metrics"]["decision_pnl"])


def test_dead_name_exit_at_last_close(small_world, monkeypatch):
    """The dying long's series ends mid-window (last bar 110 at its final
    session): the leg is exited at THAT close, delisting return carried by
    the price series, exit costed once at the name's own band."""
    days = _sessions(911, date(2015, 1, 2))
    f1_start = next(i for i, d in enumerate(days) if d >= "2016-01-01")
    last_decision = f1_start + 63 + 21 * 27  # last grid decision of fold 1
    w = build_world(small_world["tmp"], dead_last_idx=last_decision + 10,
                    dead_price=110.0)  # dies mid-window
    _wire(monkeypatch, w)
    u, panel, prices, folds = _load(w)
    monkeypatch.setenv("V9_LAUNCH_AUTHORIZED", "1")
    rec = r.run_arm("SFV9-A4-H2-ANCHOR", panel, prices, folds, dry_run=False,
                    owner_go=r.GO_PHRASE, universe=u)
    assert rec["terminations"] == 1 and rec["void_entry_orders"] == 0
    sess = folds[0]["sessions"]
    last_d = sess[63 + 21 * 27]  # last grid decision of fold 1
    # pnl = 0.125*(110/100-1) - 0.125*10bps (dead exit) - 7*0.125*10bps (flat)
    assert _pnl_at(rec, last_d) == pytest.approx(0.0125 - 0.000125 - 0.000875,
                                                 abs=1e-12)
    # every scored decision between the warmup and the fold end is flat
    assert _pnl_at(rec, sess[63 + 21 * 4]) == pytest.approx(0.0, abs=1e-12)
    flat = [x for x in rec["schedule"] if x.get("event") == "FOLD_FORCE_FLAT"]
    assert len(flat) == 1
    assert flat[0]["turnover"] == pytest.approx(0.875)   # 7 survivors x 0.125
    assert flat[0]["cost_bps_paid"] == pytest.approx(8.75)


def test_fill_check_void_entry(small_world, monkeypatch):
    """The dying name has a bar at the decision but none at the fill
    session: the order does not exist - no leg, no cost; CASH absorbs."""
    days = _sessions(911, date(2015, 1, 2))
    f1_start = next(i for i, d in enumerate(days) if d >= "2016-01-01")
    w = build_world(small_world["tmp"], dead_last_idx=f1_start + 63 + 21 * 27,
                    dead_price=110.0)  # last bar AT the last decision
    _wire(monkeypatch, w)
    u, panel, prices, folds = _load(w)
    monkeypatch.setenv("V9_LAUNCH_AUTHORIZED", "1")
    rec = r.run_arm("SFV9-A4-H2-ANCHOR", panel, prices, folds, dry_run=False,
                    owner_go=r.GO_PHRASE, universe=u)
    assert rec["void_entry_orders"] == 1
    assert rec["terminations"] == 1  # died inside the previous window
    sess = folds[0]["sessions"]
    # window where it died: exit at last recorded close (110 at its final bar)
    d_die = sess[63 + 21 * 26]
    assert _pnl_at(rec, d_die) == pytest.approx(0.0125 - 0.000125, abs=1e-12)
    # void-entry decision earns nothing; its pnl carries only the fold-end
    # force-flat cost (7 surviving legs x 0.125 x 10 bps)
    d_void = sess[63 + 21 * 27]
    assert _pnl_at(rec, d_void) == pytest.approx(-0.000875, abs=1e-12)
    flat = [x for x in rec["schedule"] if x.get("event") == "FOLD_FORCE_FLAT"]
    assert flat[0]["turnover"] == pytest.approx(0.875)
    flat = [x for x in rec["schedule"] if x.get("event") == "FOLD_FORCE_FLAT"]
    assert flat[0]["turnover"] == pytest.approx(0.875)


def test_cost_charged_exactly_once(healthy, monkeypatch):
    monkeypatch.setenv("V9_LAUNCH_AUTHORIZED", "1")
    rec = r.run_arm("SFV9-A4-H2-ANCHOR", healthy["panel"], healthy["prices"],
                    healthy["folds"], dry_run=False, owner_go=r.GO_PHRASE,
                    universe=healthy["universe"])
    # total scheduled cost = warmup entry 10 bps + fold-end force-flat 10 bps
    total_cost_bps = sum(x["cost_bps_paid"] for x in rec["schedule"])
    assert total_cost_bps == pytest.approx(20.0)
    # the warmup entry cost sits in the discarded warmup window, so the
    # scored PnL carries only the fold-flat cost (charged exactly once)
    assert rec["metrics"]["sum_pnl"] == pytest.approx(-0.001, abs=1e-12)


def test_stress_doubles_costs(healthy, monkeypatch):
    monkeypatch.setenv("V9_LAUNCH_AUTHORIZED", "1")
    rec = r.run_arm("SFV9-A4-H2-ANCHOR", healthy["panel"], healthy["prices"],
                    healthy["folds"], dry_run=False, owner_go=r.GO_PHRASE,
                    universe=healthy["universe"], stress=True)
    total_cost_bps = sum(x["cost_bps_paid"] for x in rec["schedule"])
    assert total_cost_bps == pytest.approx(40.0)  # 20/30/50 = 2x base table


def test_force_flat_resets_state_between_folds(small_world, monkeypatch):
    """A second fold starts flat: no position carries the boundary, and the
    next fold's first populated decision pays full (re)entry fills."""
    w = build_world(small_world["tmp"], n_sessions=911)
    folds2 = [
        {"fold_id": "S0_FOLD_1", "start": "2016-01-01", "end": "2017-12-31"},
        {"fold_id": "S0_FOLD_2", "start": "2018-01-01", "end": "2019-12-31"},
        {"fold_id": "S0_FOLD_3", "start": "2021-01-01", "end": "2021-12-31"},
    ]
    _wire(monkeypatch, w, folds=folds2)
    u, panel, prices, folds = _load(w, folds=folds2)
    assert len(folds[0]["sessions"]) > 378 and len(folds[1]["sessions"]) > 63
    monkeypatch.setenv("V9_LAUNCH_AUTHORIZED", "1")
    rec = r.run_arm("SFV9-A4-H2-ANCHOR", panel, prices, folds, dry_run=False,
                    owner_go=r.GO_PHRASE, universe=u)
    # first populated decision of fold 2 must pay entry fills again
    f2_first = next(x for x in rec["schedule"]
                    if x["fold"] == "S0_FOLD_2" and x.get("event") is None
                    and x["legs"] > 0)
    assert f2_first["turnover"] == pytest.approx(1.0)  # full (re)entry
    flats = [x for x in rec["schedule"] if x.get("event") == "FOLD_FORCE_FLAT"]
    assert [x["fold"] for x in flats] == ["S0_FOLD_1", "S0_FOLD_2"]


# ------------------------------------------------------------- driver

def test_driver_dry_run_sanitized_deterministic(healthy, monkeypatch):
    led1, ok1 = drv.build_dry_run_ledger(
        "0" * 40, universe=healthy["universe"], panel=healthy["panel"],
        prices=healthy["prices"], folds=healthy["folds"],
        panel_sha="a" * 64, price_manifest_sha="b" * 64)
    led2, ok2 = drv.build_dry_run_ledger(
        "0" * 40, universe=healthy["universe"], panel=healthy["panel"],
        prices=healthy["prices"], folds=healthy["folds"],
        panel_sha="a" * 64, price_manifest_sha="b" * 64)
    b1 = json.dumps(led1, sort_keys=True)
    b2 = json.dumps(led2, sort_keys=True)
    assert b1 == b2  # byte-identical, no wall-clock anywhere
    assert led1["scored"] is False and led1["real_pnl"] is False
    assert led1["published"] is False
    assert led1["counters"] == kernel.driver_ledger_counters(3, 0)
    assert led1["counters"]["published_delta"] == 0
    assert led1["record_ids_pairwise_distinct"] is True
    # the only "pnl"-bearing key in the sanitized ledger is real_pnl=False
    for cell in led1["cells"]:
        assert cell["scored"] is False and cell["real_pnl"] is False
        assert "metrics" not in cell["record"]
    # sampling floor: all non-warmup anchor decisions fully populated
    assert led1["sampling_floor_gate"]["verdict"] == "PASS"
    assert led1["sampling_floor_gate"]["median_populated_frac"] == pytest.approx(1.0)
    # small fixture cannot carry 30 scored decisions: overall nv gate binds
    nv = {g["gate"]: g for g in led1["non_vacuity_gates"]}
    assert nv["nv_scored_decisions_overall_ge"]["verdict"] == "FAIL"
    assert nv["nv_scored_decisions_per_fold_ge"]["verdict"] == "PASS"
    assert nv["nv_noncash_legs_per_decision_ge"]["verdict"] == "PASS"
    assert ok1 is False and ok2 is False


def test_driver_dry_run_blocked_data_when_unpopulated(tmp_path, monkeypatch):
    """Sampling floor: no vintage is ever visible at any gate -> the anchor
    is unpopulated everywhere -> BLOCKED_DATA (sanctioned close)."""
    w = build_world(tmp_path)
    panel2 = tmp_path / "panel_late.jsonl"
    with open(w["panel"]) as f, open(panel2, "w") as g:
        for line in f:
            row = json.loads(line)
            row["avail"] = "2030-01-01"  # nothing ever becomes available
            g.write(json.dumps(row) + "\n")
    w["panel"] = panel2
    _wire(monkeypatch, w)
    u, panel, prices, folds = _load(w)
    led, ok = drv.build_dry_run_ledger(
        "0" * 40, universe=u, panel=panel, prices=prices, folds=folds,
        panel_sha="a" * 64, price_manifest_sha="b" * 64)
    assert led["sampling_floor_gate"]["verdict"] == "BLOCKED_DATA"
    assert led["sampling_floor_gate"]["median_populated_frac"] == 0.0
    assert ok is False


def test_driver_main_dry_run_writes_ledger_blocked_exit(healthy, monkeypatch):
    monkeypatch.delenv("V9_LAUNCH_AUTHORIZED", raising=False)
    out = healthy["w"]["panel"].parent / "ledger_dryrun.json"
    monkeypatch.setattr(drv, "LEDGER_DRYRUN", str(out))
    with pytest.raises(SystemExit):  # small fixture: nv overall gate blocks
        drv.main(["--dry-run"])
    first = out.read_bytes()
    with pytest.raises(SystemExit):
        drv.main(["--dry-run"])
    assert out.read_bytes() == first  # byte-equal double generation


def test_big_world_dry_run_ok(tmp_path, monkeypatch):
    """End-to-end wiring on a fixture big enough to satisfy the sampling
    floor and every non-vacuity gate: dry-run exits clean."""
    w = build_big_world(tmp_path)
    _wire(monkeypatch, w, folds=FOLDS_BIG)
    u, panel, prices, folds = _load(w, folds=FOLDS_BIG)
    led, ok = drv.build_dry_run_ledger(
        "0" * 40, universe=u, panel=panel, prices=prices, folds=folds,
        panel_sha="a" * 64, price_manifest_sha="b" * 64)
    assert led["sampling_floor_gate"]["verdict"] == "PASS", led["sampling_floor_gate"]
    for g in led["non_vacuity_gates"]:
        assert g["verdict"] == "PASS", g
    assert ok is True
    anchor = led["cells"][0]["record"]
    assert anchor["scored_decisions_total"] >= 30


def test_driver_scored_two_key_and_pipeline(healthy, monkeypatch):
    monkeypatch.delenv("V9_LAUNCH_AUTHORIZED", raising=False)
    # inert without the env key even with the exact phrase
    with pytest.raises(SystemExit):
        drv.main([r.GO_PHRASE])
    # inert with the env key but a wrong phrase
    monkeypatch.setenv("V9_LAUNCH_AUTHORIZED", "1")
    with pytest.raises(SystemExit):
        drv.main(["GO STOCKS V8 SCORED EXECUTION"])
    # full synthetic scored pipeline with both keys
    bench = healthy["w"]["bench"]
    bench.mkdir(parents=True, exist_ok=True)
    for t in ["SPY"] + drv.SECTORS:
        bars = [{"date": d, "open": 100.0, "high": 100.0, "low": 100.0,
                 "close": 100.0, "adjusted_close": 100.0, "volume": 0}
                for d in healthy["w"]["days"]]
        (bench / f"{t}.json").write_text(json.dumps(bars))
    ledger_p = healthy["w"]["panel"].parent / "execution_ledger.json"
    verdicts_p = healthy["w"]["panel"].parent / "family_verdicts.json"
    monkeypatch.setattr(drv, "LEDGER", str(ledger_p))
    monkeypatch.setattr(drv, "VERDICTS", str(verdicts_p))
    drv.main([r.GO_PHRASE])
    ledger = json.loads(ledger_p.read_text())
    verdicts = json.loads(verdicts_p.read_text())
    assert ledger["counters"]["observed_delta"] == 7   # 3 arms x2 + drop-one
    assert ledger["counters"]["published_delta"] == 0
    assert ledger["counters"]["counter_provenance"].startswith("driver_emitted")
    v = verdicts["SFV9-A4-H2"]
    assert v["family_verdict"] in {"STAGE_A_SURVIVOR_CANDIDATE",
                                   "FALSIFIED_BY_CONTROL", "REJECT"}
    names = [g["gate"] for g in v["anchor"]["gates"]]
    for expected in ("expectancy_gt", "position_pf_ge", "folds_positive_ge",
                     "min_populated_fold_pf_ge", "max_fold_mdd_le",
                     "fold_positive_share_le", "etf_positive_share_le",
                     "etf_share_le_packet", "risk_matched_excess_positive_folds_ge",
                     "anchor_overall_alpha_gt"):
        assert expected in names
        row = next(g for g in v["anchor"]["gates"] if g["gate"] == expected)
        assert "margin_to_fail" in row
    # the control's reproduction gate lives on the control evaluation
    control_names = [g["gate"] for g in v["control"]["gates"]]
    assert "control_alpha_abs_ratio_lt" in control_names
    # in this fixture the control's cash ranks coincide with the anchor's
    # cash term (identical books) - the driver must flag the reproduction
    assert v["control"]["reproduces_anchor"] is True
    assert v["family_verdict"] == "FALSIFIED_BY_CONTROL"
    packet = {g["gate"]: g for g in v["packet_gates"]}
    assert {"stress_positive", "drop_one_survival",
            "neighbor_mechanism_support"} <= set(packet)
    # benches are flat: no sector co-movement, no SPY excess anywhere
    assert next(g for g in v["anchor"]["gates"]
                if g["gate"] == "etf_positive_share_le")["observed"] == 0.0


# --------------------------------------------- evaluation hand goldens

def test_evaluate_gates_hand_computed():
    spy = {"adj": [100.0, 101.0], "pos": {"2020-01-01": 0, "2020-01-02": 1}}
    basket = {"adj": [100.0, 101.0], "pos": {"2020-01-01": 0, "2020-01-02": 1}}
    pnl = [0.01, 0.02, -0.005, 0.008, 0.003, -0.001]
    folds = ["S0_FOLD_1", "S0_FOLD_2"]
    xs = [{"d": f"d{i}", "fill_d": "2020-01-01", "end_d": "2020-01-02",
           "fold": folds[0] if i < 4 else folds[1], "pnl": v}
          for i, v in enumerate(pnl)]
    rec = {"metrics": {"decision_pnl": xs}}
    ev = drv.evaluate(rec, spy, basket, folds, control_alpha=-0.002)
    # expectancy = 0.035; pf = 0.041/0.006 = 6.8333
    g = {x["gate"]: x for x in ev["gates"]}
    assert g["expectancy_gt"]["observed"] == pytest.approx(0.035)
    assert g["expectancy_gt"]["margin_to_fail"] == pytest.approx(0.035)
    assert g["position_pf_ge"]["observed"] == pytest.approx(6.8333, abs=1e-4)
    assert g["position_pf_ge"]["verdict"] == "PASS"
    # per-fold mdd = max(0.005, 0.001) -> margin 0.145
    assert g["max_fold_mdd_le"]["observed"] == pytest.approx(0.005)
    assert g["max_fold_mdd_le"]["margin_to_fail"] == pytest.approx(0.145)
    # fold concentration: max fold wins 0.038 / 0.041 = 0.9268 -> FAIL
    assert g["fold_positive_share_le"]["observed"] == pytest.approx(0.9268, abs=1e-4)
    assert g["fold_positive_share_le"]["verdict"] == "FAIL"
    # both folds positive
    assert g["folds_positive_ge"]["observed"] == 2
    assert g["folds_positive_ge"]["verdict"] == "PASS"
    # spy window return = 0.01 per decision -> alpha = -0.025/6 = -0.0041667
    assert ev["alpha"] == pytest.approx(-0.0041667, abs=1e-6)
    assert g["anchor_overall_alpha_gt"]["verdict"] == "FAIL"
    # control ratio |−0.002| / |−0.0041667| = 0.48 < 0.5 (knife-edge pass)
    assert g["control_alpha_abs_ratio_lt"]["observed"] == pytest.approx(0.48, abs=1e-4)
    assert g["control_alpha_abs_ratio_lt"]["verdict"] == "PASS"
    assert g["control_alpha_abs_ratio_lt"]["margin_to_fail"] == pytest.approx(0.02, abs=1e-4)
    # flat-up basket: every positive decision co-moves -> etf share 1.0
    assert g["etf_positive_share_le"]["observed"] == 1.0
    assert g["etf_positive_share_le"]["verdict"] == "FAIL"
    assert g["etf_share_le_packet"]["verdict"] == "FAIL"
    # per-fold alpha sums both negative -> 0 excess folds
    assert g["risk_matched_excess_positive_folds_ge"]["observed"] == 0


def test_drop_one_fold_ok():
    xs = [{"pnl": 0.01, "fold": "F1"}, {"pnl": 0.02, "fold": "F1"},
          {"pnl": -0.005, "fold": "F1"}, {"pnl": 0.008, "fold": "F1"},
          {"pnl": 0.003, "fold": "F2"}, {"pnl": -0.001, "fold": "F2"}]
    ok, vals = drv.drop_one_fold_ok(xs, ["F1", "F2"])
    assert ok is True
    assert vals == [pytest.approx(0.002, abs=1e-12), pytest.approx(0.033, abs=1e-12)]
    ok2, _ = drv.drop_one_fold_ok([{"pnl": -0.01, "fold": "F1"},
                                   {"pnl": 0.001, "fold": "F2"}], ["F1", "F2"])
    assert ok2 is False


def test_redact_and_no_secrets():
    assert drv.redact("boom api_token=SECRET123 end") == "boom REDACTED end"
    assert "SECRET" not in drv.redact("EODHD_API_KEY=hunter2 leaked")
    with pytest.raises(RuntimeError):
        drv.assert_no_secrets({"cell": "x", "err": "EODHD_API_KEY=abc"})
    with pytest.raises(RuntimeError):
        drv.assert_no_secrets({"url": "https://eodhd.com/api/eod/SPY?api_token=k"})
    drv.assert_no_secrets({"clean": True})  # no raise


def test_arm_specs_pairwise_distinct_digests():
    ds = {a: hashlib_sha(s) for a, s in r.ARM_SPECS.items()}
    assert len(set(ds.values())) == len(ds) == 3
    assert set(ds) == set(r.ARM_IDS)


def hashlib_sha(spec):
    import hashlib
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def test_go_phrase_and_launch_env_constants():
    assert r.GO_PHRASE == "GO STOCKS V9 SCORED EXECUTION"
    assert r.LAUNCH_ENV == "V9_LAUNCH_AUTHORIZED"
    assert not r.scored_authorized(r.GO_PHRASE)  # env absent by default
    assert not r.scored_authorized("nếu A7 authorized thì GO STOCKS V9 SCORED EXECUTION")
    monkey_free = "GO STOCKS V9 SCORED EXECUTION"
    assert r.scored_authorized(monkey_free) is False  # P-8: phrase alone never authorizes
