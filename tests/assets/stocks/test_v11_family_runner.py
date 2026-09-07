"""SFV11-A5-H1 family runner + driver tests.

Handbook 14.2/14.3 discipline: synthetic hand-computed fixtures ONLY.
No production data byte is read, no production outcome is pinned: the
hand-computed cost/PnL expectations below are properties of the FIXTURE
arithmetic (flat prices, one price step on a dying name, band-A costs),
never of a scored production cell.  The scored-path tests set the launch
env var INSIDE the test scope only (monkeypatch) - the lane itself never
sets or persists it.
"""

import hashlib
import json
import math
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from research.assets.stocks import kernel_band_cost_v9 as kernel
from research.assets.stocks import v11_e_driver as drv
from research.assets.stocks import v11_family_runner as r
from research.assets.stocks.v9_e_driver import SECTORS
from research.assets.stocks.v9_family_runner import pct_rank, target_book

FIELD = "us-gaap:Assets"
DEAD = "CIK000000000"  # j=0, an anchor LONG in the fixture world

FOLDS_SMALL = [
    {"fold_id": "S0_FOLD_1", "start": "2016-01-01", "end": "2018-12-31"},
    {"fold_id": "S0_FOLD_2", "start": "2019-01-01", "end": "2019-12-31"},
    {"fold_id": "S0_FOLD_3", "start": "2020-01-01", "end": "2021-12-31"},
]
FOLDS_BIG = [
    {"fold_id": "S0_FOLD_1", "start": "2016-01-01", "end": "2018-12-31"},
    {"fold_id": "S0_FOLD_2", "start": "2019-01-01", "end": "2020-06-30"},
    {"fold_id": "S0_FOLD_3", "start": "2020-07-01", "end": "2021-12-31"},
]


def _sessions(n, start=date(2015, 1, 2)):
    days, cur = [], start
    while len(days) < n:
        if cur.weekday() < 5:
            days.append(cur.isoformat())
        cur += timedelta(days=1)
    return days


def _sector(j):
    return "SEC0" if j % 2 == 0 else "SEC1"


def _cik(j):
    return f"CIK{j:09d}"


def build_world(tmp, n_sessions=911, dead_last_idx=None, dead_price=110.0,
                start=date(2015, 1, 2), n_groups=90,
                group_start=date(2014, 1, 31), stamps_future=None,
                iarr_map=None, depth_map=None):
    """12 names, 2 sectors (j even -> SEC0), flat 100.0 prices, band A
    liquidity.  Each name carries n_groups monthly chain groups
    (eff = group_start + 32k days, last_avail = eff + 40d).

    Hand exposure construction: late flag and depth are NAME-level constants
    (j >= 6 -> late iarr 500 + depth 6; j < 6 -> iarr 30 + depth 2), so at
    every decision late_share/deep_share are exactly 0.0 (j<6) or 1.0
    (j>=6): six tied lows rank into the long tercile, six tied highs into
    the short tercile, both sectors active, w = 0.5/(2*3) = 1/12 per leg.

    The revision fixture rows carry DECOY direction/magnitude keys that the
    loader must never read (leak canary).
    """
    days = _sessions(n_sessions, start)
    eod = Path(tmp) / "eod"
    eod.mkdir(parents=True, exist_ok=True)
    names = [_cik(j) for j in range(12)]
    iarr_map = iarr_map or (lambda j, k: 500 if j >= 6 else 30)
    depth_map = depth_map or (lambda j, k: 6 if j >= 6 else 2)
    for j, cik in enumerate(names):
        bars = []
        for i, d in enumerate(days):
            if cik == DEAD and dead_last_idx is not None and i > dead_last_idx:
                continue  # the dying name's series ends here
            px = dead_price if (cik == DEAD and dead_last_idx == i) else 100.0
            bars.append({"date": d, "open": px, "high": px, "low": px,
                         "close": px, "adjusted_close": px,
                         "volume": 1_000_000})
        (eod / f"{cik}__T{j}.json").write_text(json.dumps(bars))
    rev = Path(tmp) / "revision.jsonl"
    tim = Path(tmp) / "timing.jsonl"
    groups = []
    for k in range(n_groups):
        eff = group_start + timedelta(days=32 * k)
        la = eff + timedelta(days=40)
        if stamps_future:
            la = date.fromisoformat(stamps_future)  # nothing ever visible
        groups.append((eff.isoformat(), la.isoformat(), k))
    with open(rev, "w") as fr, open(tim, "w") as ft:
        for j, cik in enumerate(names):
            for eff, la, k in groups:
                iarr = iarr_map(j, k)
                depth = depth_map(j, k)
                fr.write(json.dumps({
                    "e": cik, "s": _sector(j), "f": FIELD, "eff": eff,
                    "depth": depth, "first_avail": eff, "last_avail": la,
                    "inter_arrival_days": iarr, "amend_count": depth - 1,
                    "rev_dir": 1, "rev_mag": 99.0,  # DECOY - never read
                    "observable_available_at": la, "reason": None}) + "\n")
                ft.write(json.dumps({
                    "e": cik, "s": _sector(j), "f": FIELD, "eff": eff,
                    "first_avail": eff, "last_avail": la, "depth": depth,
                    "first_lag_days": 40, "amend_count": depth - 1,
                    "own_z": None, "cohort_z": None,
                    "observable_available_at": la}) + "\n")
    cohort = Path(tmp) / "cohort_v9.json"
    cohort.write_text(json.dumps({"members": {
        "ALIVE_EVIDENCED": [{"cik": c, "sector": _sector(j)}
                            for j, c in enumerate(names) if c != DEAD],
        "DEAD_EVIDENCED": [{"cik": c, "sector": _sector(j)}
                           for j, c in enumerate(names)]}}))
    scan = Path(tmp) / "scan.json"
    scan.write_text(json.dumps({"dead_verdicts": {
        DEAD: {"verdict": "DEAD_PRICE_CONFIRMED"},
        "CIK999999999": {"verdict": "NOT_DEAD_PRICE_SURVIVAL"}}}))
    manifest = Path(tmp) / "manifest.json"
    manifest.write_text(json.dumps({"files": {}}))
    return {"days": days, "names": names, "revision": rev, "timing": tim,
            "cohort": cohort, "scan": scan, "manifest": manifest,
            "eod": eod, "bench": Path(tmp) / "bench", "tmp": Path(tmp)}


def build_big_world(tmp):
    """Same construction over the real three-fold split and a vintage
    history covering every 800-day window: ~60 scored decisions, so all
    three non-vacuity gates are satisfiable on synthetic data."""
    return build_world(tmp, n_sessions=1830, n_groups=90)


def _wire(monkeypatch, w):
    monkeypatch.setattr(r, "COHORT_PATH", str(w["cohort"]))
    monkeypatch.setattr(r, "INTEGRITY_SCAN_PATH", str(w["scan"]))
    monkeypatch.setattr(r, "PRICE_MANIFEST_PATH", str(w["manifest"]))
    monkeypatch.setattr(r, "REVISION_PATH", str(w["revision"]))
    monkeypatch.setattr(r, "TIMING_PATH", str(w["timing"]))


# captured at import (never monkeypatched): the fixture-layer builder
_ORIG_BUILD_LAYERS = drv.build_layers


def _layers(w, verify_pins=False):
    rev_rows, _ = r.load_revision_layer(str(w["revision"]))
    total = sum(len(v) for v in rev_rows.values())
    return _ORIG_BUILD_LAYERS(
        verify_pins=verify_pins, revision_path=str(w["revision"]),
        timing_path=str(w["timing"]), cohort_path=str(w["cohort"]),
        scan_path=str(w["scan"]), manifest_path=str(w["manifest"]),
        expected_join=total)


def _load(w, folds=FOLDS_SMALL):
    universe = r.load_universe(w["cohort"], w["scan"])
    sectors = r.load_sectors(w["cohort"])
    rev_rows, _ = r.load_revision_layer(w["revision"])
    depth_map, _ = r.load_timing_depth(w["timing"])
    stacks, join = r.build_stacks(
        rev_rows, depth_map,
        expected_join=sum(len(v) for v in rev_rows.values()))
    prices = r.load_prices(str(w["eod"]))
    folds_s = r.fold_sessions(prices, folds)
    return universe, sectors, stacks, prices, folds_s, join


def _fixture_bench(w):
    out = {}
    for t in ["SPY"] + list(SECTORS):
        bars = json.loads((w["bench"] / f"{t}.json").read_text())
        out[t] = {"adj": [float(b["adjusted_close"]) for b in bars],
                  "pos": {b["date"]: i for i, b in enumerate(bars)}}
    return out


@pytest.fixture()
def small_world(tmp_path, monkeypatch):
    w = build_world(tmp_path)
    _wire(monkeypatch, w)
    return w


def _tiny_stacks(rows_by_entity):
    """Build stacks from hand rows {entity: [(last_avail, iarr, depth)]}."""
    n = 0
    with tempfile.TemporaryDirectory() as td:
        rev, tim = Path(td) / "rev.jsonl", Path(td) / "tim.jsonl"
        with open(rev, "w") as fr, open(tim, "w") as ft:
            for e, rows in rows_by_entity.items():
                for i, (la, iarr, d) in enumerate(rows):
                    eff = f"20{i:02d}-01-01"  # distinct period per row
                    fr.write(json.dumps({"e": e, "f": FIELD, "eff": eff,
                                         "last_avail": la,
                                         "inter_arrival_days": iarr}) + "\n")
                    ft.write(json.dumps({"e": e, "f": FIELD, "eff": eff,
                                         "depth": d}) + "\n")
                    n += 1
        rev_rows, counts = r.load_revision_layer(str(rev))
        depth_map, _ = r.load_timing_depth(str(tim))
        stacks, join = r.build_stacks(rev_rows, depth_map, expected_join=n)
    return stacks, counts


T = "2020-06-01"


def _t(days):
    return r._shift_iso(T, days)


# --------------------------------------------------- exposure arithmetic

def test_late_share_hand_computed_window_bounds():
    """|Q| counts last_avail in [t-800, t): strict gate at t, inclusive at
    exactly t-800.  Hand: 5 in-window groups of which 2 are late
    (iarr 500) -> 0.4."""
    rows = {
        "CIKA": [
            (_t(-10), 500, 2),    # late, in window
            (_t(-20), 500, 3),    # late, in window
            (_t(-30), 100, 2),    # punctual
            (_t(-40), 100, 4),    # punctual
            (_t(-800), 100, 2),   # exactly the 800-day bound: INCLUSIVE
            (_t(-801), 500, 2),   # one day past the bound: stale, OUT
            (T, 500, 2),          # stamped AT the gate: not visible
        ],
    }
    stacks, counts = _tiny_stacks(rows)
    st = stacks["CIKA"]
    assert r._window_count(st["avails"], st["ctot"], T) == 5
    assert r._window_count(st["avails"], st["clate"], T) == 2
    assert r.exposure_value("late_share", st, T) == pytest.approx(0.4)


def test_min_q_floor_and_neighbour_deep_share():
    """|Q| < 4 -> UNPOPULATED (never zero-ranked); deep_share counts
    depth >= 6 over the same Q."""
    rows3 = {"CIKB": [(_t(-150), 500, 2), (_t(-120), 100, 2),
                      (_t(-90), 100, 6)]}  # |Q| = 3 < 4
    stacks, _ = _tiny_stacks(rows3)
    assert r.exposure_value("late_share", stacks["CIKB"], T) is None
    rows4 = {"CIKC": [(_t(-150), 100, 2), (_t(-120), 100, 2),
                      (_t(-90), 100, 6), (_t(-60), 500, 6)]}
    stacks, _ = _tiny_stacks(rows4)
    st = stacks["CIKC"]
    assert r.exposure_value("late_share", st, T) == pytest.approx(0.25)
    assert r.exposure_value("deep_share", st, T) == pytest.approx(0.5)


def test_latency_cut_is_strictly_greater_than_460():
    """The frozen cut: inter_arrival_days > 460 is late; exactly 460 is not."""
    rows = {"CIKD": [(_t(-150), 460, 2), (_t(-120), 100, 2),
                     (_t(-90), 100, 2), (_t(-60), 100, 2)]}
    stacks, _ = _tiny_stacks(rows)
    assert r.exposure_value("late_share", stacks["CIKD"], T) == 0.0
    rows["CIKD"][0] = (_t(-150), 461, 2)
    stacks, _ = _tiny_stacks(rows)
    assert r.exposure_value("late_share", stacks["CIKD"], T) == 0.25


def test_depth3_drop_one_process_leg_stack():
    """drop-one-process-leg: late_share recomputed over ONLY depth>=3
    groups; the |Q'| >= 4 floor re-applies on the filtered Q.
    Hand: 7 groups in Q (3 late, two of them depth-2); Q' = the five
    depth-3 rows with 1 late -> late_share_depth3 = 0.2."""
    rows = {"CIKE": [
        (_t(-150), 500, 2), (_t(-120), 500, 2),   # depth-2 late pair
        (_t(-90), 500, 3),                        # depth-3 late
        (_t(-60), 100, 3), (_t(-50), 100, 3),
        (_t(-40), 100, 4), (_t(-30), 100, 3)]}
    stacks, _ = _tiny_stacks(rows)
    st = stacks["CIKE"]
    assert r.exposure_value("late_share", st, T) == pytest.approx(3 / 7)
    assert r.exposure_value("late_share_depth3", st, T) == pytest.approx(0.2)
    # floor on the filtered set: three depth-3 rows -> unpopulated
    rows["CIKE"] = rows["CIKE"][:3] + [(_t(-60), 100, 3)]
    stacks, _ = _tiny_stacks(rows)
    assert r.exposure_value("late_share_depth3",
                            stacks["CIKE"], T) is None


def test_availability_lag_mutation_moves_membership_exactly():
    """P3 mutation: pushing a last_avail stamp later moves the affected
    group's window membership exactly per the stamp - out at the strict
    gate, or at the 800-day staleness bound - and nothing else changes."""
    base = {
        "CIK0000000A": [(_t(-10), 500, 2), (_t(-20), 500, 3),
                        (_t(-30), 100, 2), (_t(-40), 100, 4),
                        (_t(-800), 100, 2)],
        "CIK0000000B": [(_t(-10), 100, 2), (_t(-20), 100, 3),
                        (_t(-30), 100, 2), (_t(-40), 100, 6)],
    }
    stacks, _ = _tiny_stacks(base)
    a, b = stacks["CIK0000000A"], stacks["CIK0000000B"]
    assert r.exposure_value("late_share", a, T) == pytest.approx(0.4)
    assert r.exposure_value("late_share", b, T) == 0.0
    # (a) cross the GATE: move g2 from t-30d to t+5d -> |Q| 4, late 2
    moved = {k: list(v) for k, v in base.items()}
    moved["CIK0000000A"][2] = (_t(5), 100, 2)
    stacks2, _ = _tiny_stacks(moved)
    a2, b2 = stacks2["CIK0000000A"], stacks2["CIK0000000B"]
    assert r.exposure_value("late_share", a2, T) == pytest.approx(0.5)
    assert r.exposure_value("late_share", b2, T) == 0.0  # neighbour untouched
    # (b) cross the STALENESS bound: move g0 from t-10d to t-801d
    moved = {k: list(v) for k, v in base.items()}
    moved["CIK0000000A"][0] = (_t(-801), 500, 2)
    stacks3, _ = _tiny_stacks(moved)
    a3 = stacks3["CIK0000000A"]
    assert r.exposure_value("late_share", a3, T) == pytest.approx(0.25)


def test_fixture_loader_never_reads_direction_magnitude(tmp_path):
    """Leak canary at record depth: the fixture rows carry decoy
    direction/magnitude keys; the loaded stacks are pure sanctioned prefix
    structures, and the lane sources never reference the decoy tokens
    (source inspection)."""
    w = build_world(tmp_path)
    rev_rows, counts = r.load_revision_layer(w["revision"])
    ent = rev_rows["CIK000000001"]
    assert isinstance(ent[0], tuple) and len(ent[0]) == 4  # (la, f, eff, iarr)
    assert "rev_dir" not in json.dumps(ent[0], default=str)
    depth_map, _ = r.load_timing_depth(w["timing"])
    key = next(iter(depth_map["CIK000000001"]))
    assert depth_map["CIK000000001"][key] in (2, 6)
    joined, _ = r.build_stacks(
        rev_rows, depth_map,
        expected_join=sum(len(v) for v in rev_rows.values()))
    assert set(joined["CIK000000001"]) == {
        "avails", "ctot", "clate", "cdeep", "avails3", "ctot3", "clate3"}
    # source inspection: no decoy token anywhere in the new lane modules
    src_root = os.path.dirname(os.path.abspath(r.__file__))
    for mod in ("v11_family_runner.py", "v11_e_driver.py"):
        src = open(os.path.join(src_root, mod)).read()
        for token in ("rev_dir", "rev_mag"):
            assert token not in src, f"leak: {token} referenced in {mod}"


# ------------------------------------------------------------ book rules

def test_tercile_ties_join_long_and_hysteresis():
    """7-name sector, values [0, 1,1,1, 2,2,2]: the tie group at EXACTLY
    the 1/3 boundary joins the LONG tercile; the short leg is strictly the
    highest exposures.  Hysteresis on a 12-name ladder (pct = k/11): a held
    L is retained at 4/11 = 0.3636 <= 1/3+0.10, dropped at 5/11; a held S
    is retained at 7/11 = 0.6364 >= 2/3-0.10, dropped at 6/11."""
    names7 = [f"CIK{i:09d}" for i in range(20, 27)]
    vals = dict(zip(names7, [0.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0]))
    ranks = {n: ("SECX", p) for n, p in pct_rank(vals).items()}
    assert ranks[names7[1]][1] == pytest.approx(1 / 3)  # exact boundary tie
    book, active = target_book(ranks, {}, "low_long")
    assert active == 1
    assert set(book) == set(names7)
    for n in names7[:4]:
        assert book[n] == "L"                # tie group joins LONG
    for n in names7[4:]:
        assert book[n] == "S"
    names12 = [f"CIK{i:09d}" for i in range(30, 42)]
    vals12 = {n: float(k) for k, n in enumerate(names12)}
    ranks12 = {n: ("SECX", p) for n, p in pct_rank(vals12).items()}
    held = {names12[1]: "L", names12[4]: "L", names12[5]: "L",
            names12[10]: "S", names12[7]: "S", names12[6]: "S"}
    book2, _ = target_book(ranks12, held, "low_long")
    assert book2[names12[1]] == "L"   # 1/11: plain long
    assert book2[names12[4]] == "L"   # 0.3636 <= 0.4333: retained
    assert names12[5] not in book2    # 0.4545 > 0.4333: exited band+decile
    assert book2[names12[10]] == "S"  # plain short
    assert book2[names12[7]] == "S"   # 0.6364 >= 0.5667: retained
    assert names12[6] not in book2    # 0.5455 < 0.5667: exited


def test_sector_below_six_names_abstains():
    names5 = [f"CIK{i:09d}" for i in range(40, 45)]
    ranks = {n: ("TINY", float(i)) for i, n in enumerate(names5)}
    book, active = target_book(ranks, {}, "low_long")
    assert book == {} and active == 0


# ---------------------------------------------------------- world wiring

def test_universe_legs_and_sectors(small_world):
    uni = r.load_universe(small_world["cohort"], small_world["scan"])
    assert DEAD in uni                        # DEAD_PRICE_CONFIRMED included
    assert "CIK999999999" not in uni          # NOT_DEAD_PRICE_SURVIVAL excluded
    assert len(uni) == 12                     # 11 alive + 1 dead
    sect = r.load_sectors(small_world["cohort"])
    assert sect[DEAD] == "SEC0" and sect["CIK000000001"] == "SEC1"


def test_join_reconciliation_fail_closed(small_world):
    rev_rows, _ = r.load_revision_layer(small_world["revision"])
    depth_map, _ = r.load_timing_depth(small_world["timing"])
    with pytest.raises(ValueError, match="reconciliation FAILED"):
        r.build_stacks(rev_rows, depth_map,
                       expected_join=r.CENSUS_REVISION_GROUPS)


def test_frozen_constants_and_arm_digests():
    ds = {a: hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()
          for a, s in r.ARM_SPECS.items()}
    assert len(set(ds.values())) == len(ds) == 3
    assert set(r.ARM_IDS) == set(r.ARM_SPECS)
    assert r.GO_PHRASE == "GO STOCKS V11 SCORED EXECUTION"
    assert r.LAUNCH_ENV == "V11_LAUNCH_AUTHORIZED"
    assert r.LATENCY_CUT_DAYS == 460 and r.NEIGHBOUR_DEPTH_CUT == 6
    assert r.MIN_Q == 4 and r.MIN_SECTOR_NAMES == 6 and r.GROSS_CAP == 2.0
    assert r.STALE_DAYS == 800 and r.PCG_SEED == 20260907
    assert r.CENSUS_REVISION_GROUPS == 1_667_422
    assert not r.scored_authorized(r.GO_PHRASE)  # env absent: refused
    assert r.REVISION_SHA_EXPECTED.startswith("7110cbf0")
    assert r.TIMING_SHA_EXPECTED.startswith("b1477ea3")


def test_decision_grid_inherited(small_world):
    _, _, _, prices, folds, _ = _load(small_world)
    dates, idx = r.decision_grid(folds[0]["sessions"])
    assert idx == list(range(63, len(folds[0]["sessions"]), 21))
    assert dates[0] == folds[0]["sessions"][63]


def test_band_cost_kernel_fail_closed_wrapper():
    assert r.change_cost("X", 0.25, {"X": "B"}, 1.0) == pytest.approx(
        0.25 * 15.0 / 10_000.0)
    with pytest.raises(kernel.BandResolutionError):
        r.change_cost("GHOST", 0.25, {"OTHER": "A"}, 1.0)  # missing band (L-I3)
    with pytest.raises(kernel.BandResolutionError):
        r.change_cost("X", 0.25, {"X": "UNTRADABLE"}, 1.0)  # never tradable
    # exits use the C-rate ceiling, never the silent fallback
    assert kernel.resolve_exit_band_bps("G", {}) == 25.0
    assert kernel.resolve_exit_band_bps("G", {"G": "UNTRADABLE"}) == 25.0
    assert kernel.resolve_exit_band_bps("G", {"G": "A"}) == 10.0


# ------------------------------------------------- dry-run arm records

def test_first_decision_book_hand_computed(small_world):
    """Flat world: 12 tied-low/tied-high names, both sectors active ->
    12 legs at w = 1/12; entry fills cost 12 x (1/12) x 10 bps = 10 bps,
    charged exactly once; no further cost until the fold-end force-flat
    (another 10 bps; the small fixture only populates fold 1)."""
    u, sect, stacks, prices, folds, join = _load(small_world)
    assert join["joined_rows"] == 12 * 90
    rec = r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds,
                    dry_run=True, universe=u, sectors=sect)
    sess0 = folds[0]["sessions"]
    first = next(x for x in rec["schedule"]
                 if x.get("event") is None and x["legs"] > 0)
    assert first["decision_date"] == sess0[63]
    assert first["legs"] == 12 and first["eligible"] == 12
    assert first["populated"] == 12 and first["populated_frac"] == 1.0
    assert first["turnover"] == pytest.approx(1.0)
    assert first["cost_bps_paid"] == pytest.approx(10.0)
    mids = [x for x in rec["schedule"]
            if x.get("event") is None and x["decision_date"] != sess0[63]]
    assert mids and all(x["cost_bps_paid"] == 0.0 for x in mids)
    flats = [x for x in rec["schedule"] if x.get("event") == "FOLD_FORCE_FLAT"]
    assert len(flats) == 1
    assert flats[0]["cost_bps_paid"] == pytest.approx(10.0)
    assert flats[0]["turnover"] == pytest.approx(1.0)


def test_neighbour_arm_same_books(small_world):
    """Neighbour (deep_share) shares the anchor's exposure construction;
    on the fixture the depth cut separates the same names -> same books."""
    u, sect, stacks, prices, folds, _ = _load(small_world)
    a = r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds, dry_run=True,
                  universe=u, sectors=sect)
    n = r.run_arm("SFV11-A5-H1-NEIGHBOUR", stacks, prices, folds,
                  dry_run=True, universe=u, sectors=sect)
    ka = [(x["decision_date"], x["legs"]) for x in a["schedule"]]
    kn = [(x["decision_date"], x["legs"]) for x in n["schedule"]]
    assert ka == kn


def test_control_arm_population_matches_anchor(small_world):
    """The control permutes the anchor's values WITHIN each sector: the
    sector-level value multiset is preserved exactly, so population,
    eligibility and sector participation must match the anchor on EVERY
    decision; names may move between the tied value levels, so the control
    book legitimately churns while the anchor's book is stable."""
    u, sect, stacks, prices, folds, _ = _load(small_world)
    a = r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds, dry_run=True,
                  universe=u, sectors=sect)
    c = r.run_arm("SFV11-A5-H1-CONTROL", stacks, prices, folds, dry_run=True,
                  universe=u, sectors=sect)
    ka = [(x["decision_date"], x["eligible"], x["populated"],
           x["active_sectors"], x["legs"]) for x in a["schedule"]
          if x.get("event") is None]
    kc = [(x["decision_date"], x["eligible"], x["populated"],
           x["active_sectors"], x["legs"]) for x in c["schedule"]
          if x.get("event") is None]
    assert ka == kc and ka
    # anchor: stable tied book -> single entry fill, then zero turnover
    a_mid = [x for x in a["schedule"] if x.get("event") is None
             and x["decision_date"] != folds[0]["sessions"][63]]
    assert all(x["turnover"] == 0.0 for x in a_mid)
    # control: churn (names move between the tied levels) -> turnover > 0
    c_mid = [x for x in c["schedule"] if x.get("event") is None
             and x["decision_date"] != folds[0]["sessions"][63]]
    assert any(x["turnover"] > 0.0 for x in c_mid)
    # every control leg weight stays within the frozen gross cap
    assert all(x["cost_bps_paid"] <= 200.0 * 2.0 for x in c["schedule"])


def test_dry_run_no_outcome_fields(small_world):
    u, sect, stacks, prices, folds, _ = _load(small_world)
    for arm in r.ARM_IDS:
        rec = r.run_arm(arm, stacks, prices, folds, dry_run=True,
                        universe=u, sectors=sect)
        blob = json.dumps(rec)
        for forbidden in ("pnl", "expectancy", "metrics", "pf", "mdd",
                          "alpha", "sharpe"):
            assert forbidden not in blob, f"leak: {forbidden} in dry-run record"
        assert rec["dry_run"] is True and rec["scored"] is False


def test_dry_run_deterministic_and_stress_doubles(small_world):
    u, sect, stacks, prices, folds, _ = _load(small_world)
    a = r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds, dry_run=True,
                  universe=u, sectors=sect)
    b = r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds, dry_run=True,
                  universe=u, sectors=sect)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    s = r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds, dry_run=True,
                  universe=u, sectors=sect, stress=True)
    base_cost = sum(x["cost_bps_paid"] for x in a["schedule"])
    stress_cost = sum(x["cost_bps_paid"] for x in s["schedule"])
    assert base_cost > 0
    assert stress_cost == pytest.approx(2 * base_cost)  # 20/30/50 per side


def test_record_ids_pairwise_distinct(small_world):
    u, sect, stacks, prices, folds, _ = _load(small_world)
    for arm in r.ARM_IDS:
        rec = r.run_arm(arm, stacks, prices, folds, dry_run=True,
                        universe=u, sectors=sect)
        ids = [x["record_id"] for x in rec["schedule"]]
        assert len(set(ids)) == len(ids) > 0


# ------------------------------------------------- scored-path mechanics

def test_scored_refused_without_two_keys(small_world, monkeypatch):
    monkeypatch.delenv("V11_LAUNCH_AUTHORIZED", raising=False)
    u, sect, stacks, prices, folds, _ = _load(small_world)
    with pytest.raises(SystemExit):  # no phrase, no env
        r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds, dry_run=False)
    with pytest.raises(SystemExit):  # another cycle's phrase never authorizes
        r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds, dry_run=False,
                  owner_go="GO STOCKS V10 SCORED EXECUTION")
    monkeypatch.setenv("V11_LAUNCH_AUTHORIZED", "1")
    with pytest.raises(SystemExit):  # env set but phrase wrong
        r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds, dry_run=False,
                  owner_go="wrong")
    # both keys -> the scored path runs (synthetic fixture, fixture pnl only)
    rec = r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds,
                    dry_run=False, owner_go=r.GO_PHRASE,
                    universe=u, sectors=sect)
    assert rec["scored"] is True and "metrics" in rec
    assert all({"d", "fill_d", "end_d", "fold", "pnl"} <= set(x)
               for x in rec["metrics"]["decision_pnl"])


def test_dead_name_exit_at_last_close(small_world, monkeypatch):
    """The dying long's series ends mid-window (last bar 110 at its final
    session): the leg is exited at THAT close, the delisting return carried
    by the price series, the exit costed once at the name's own band.
    Hand pnl at the discovering decision (w = 1/12, flat prices):
      1/12*0.10 - 1/12*10bps (dead exit) - 11/12*10bps (fold force-flat)."""
    days = _sessions(911)
    f1_start = next(i for i, d in enumerate(days) if d >= "2016-01-01")
    last_decision = f1_start + 63 + 21 * 27  # last grid decision of fold 1
    w = build_world(small_world["tmp"], dead_last_idx=last_decision + 10,
                    dead_price=110.0)
    _wire(monkeypatch, w)
    u, sect, stacks, prices, folds, _ = _load(w)
    monkeypatch.setenv("V11_LAUNCH_AUTHORIZED", "1")
    rec = r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds,
                    dry_run=False, owner_go=r.GO_PHRASE,
                    universe=u, sectors=sect)
    assert rec["terminations"] == 1 and rec["void_entry_orders"] == 0
    sess = folds[0]["sessions"]
    last_d = sess[63 + 21 * 27]
    pnl = (1 / 12) * 0.10 - (1 / 12) * 0.001 - (11 / 12) * 0.001
    got = next(x for x in rec["metrics"]["decision_pnl"] if x["d"] == last_d)
    assert got["pnl"] == pytest.approx(pnl, abs=1e-9)
    flat = next(x for x in rec["schedule"]
                if x.get("event") == "FOLD_FORCE_FLAT"
                and x["fold"] == "S0_FOLD_1")
    assert flat["turnover"] == pytest.approx(11 / 12)  # survivors only
    assert flat["cost_bps_paid"] == pytest.approx((11 / 12) * 10.0, abs=1e-3)


def test_fill_check_void_entry(small_world, monkeypatch):
    """The dying name has a bar at the decision but none at the fill
    session: the ENTRY order does not exist - no leg, no cost; CASH
    absorbs.  Its exit already happened at last close in the PRIOR window."""
    days = _sessions(911)
    f1_start = next(i for i, d in enumerate(days) if d >= "2016-01-01")
    w = build_world(small_world["tmp"],
                    dead_last_idx=f1_start + 63 + 21 * 27, dead_price=110.0)
    _wire(monkeypatch, w)
    u, sect, stacks, prices, folds, _ = _load(w)
    monkeypatch.setenv("V11_LAUNCH_AUTHORIZED", "1")
    rec = r.run_arm("SFV11-A5-H1-ANCHOR", stacks, prices, folds,
                    dry_run=False, owner_go=r.GO_PHRASE,
                    universe=u, sectors=sect)
    assert rec["void_entry_orders"] == 1 and rec["terminations"] == 1
    sess = folds[0]["sessions"]
    d_die = sess[63 + 21 * 26]  # window where it died: exit at last close
    pnl_die = next(x for x in rec["metrics"]["decision_pnl"] if x["d"] == d_die)
    assert pnl_die["pnl"] == pytest.approx((1 / 12) * 0.10 - (1 / 12) * 0.001,
                                           abs=1e-9)
    d_void = sess[63 + 21 * 27]  # void entry + fold force-flat on survivors
    pnl_void = next(x for x in rec["metrics"]["decision_pnl"]
                    if x["d"] == d_void)
    assert pnl_void["pnl"] == pytest.approx(-(11 / 12) * 0.001, abs=1e-9)


def test_availability_lag_mutation_runner_level(tmp_path, monkeypatch):
    """Shifting ONE group's stamp 900 days later shifts that evidence by
    exactly 900 days: the affected name's |Q| drops by one at the affected
    decision, every other name's stack is byte-identical, and the late mass
    (a property of the inter-arrival value, not of the stamp) is unchanged."""
    w = build_world(tmp_path)
    _wire(monkeypatch, w)
    u, sect, stacks, prices, folds, _ = _load(w)
    # build the mutated revision layer: move CIK000000003's first stamp
    src = open(w["revision"]).read().splitlines()
    dst, shifted = [], 0
    for line in src:
        row = json.loads(line)
        if row["e"] == "CIK000000003" and shifted == 0:
            row["last_avail"] = (date.fromisoformat(row["last_avail"])
                                 + timedelta(days=900)).isoformat()
            shifted += 1
        dst.append(json.dumps(row))
    mut_rev = tmp_path / "mut_rev.jsonl"
    mut_rev.write_text("\n".join(dst) + "\n")
    rev_rows, _ = r.load_revision_layer(str(mut_rev))
    depth_map, _ = r.load_timing_depth(str(w["timing"]))
    stacks2, _ = r.build_stacks(
        rev_rows, depth_map,
        expected_join=sum(len(v) for v in rev_rows.values()))
    # unaffected names: byte-identical stacks
    assert json.dumps(stacks["CIK000000004"], sort_keys=True) == \
        json.dumps(stacks2["CIK000000004"], sort_keys=True)
    # affected name at the first fold-1 decision: membership -1 exactly
    t = folds[0]["sessions"][63]
    n_before = r._window_count(stacks["CIK000000003"]["avails"],
                               stacks["CIK000000003"]["ctot"], t)
    n_after = r._window_count(stacks2["CIK000000003"]["avails"],
                              stacks2["CIK000000003"]["ctot"], t)
    assert n_after == n_before - 1
    late_before = r._window_count(stacks["CIK000000003"]["avails"],
                                  stacks["CIK000000003"]["clate"], t)
    late_after = r._window_count(stacks2["CIK000000003"]["avails"],
                                 stacks2["CIK000000003"]["clate"], t)
    assert late_after == late_before  # same late mass, moved by the stamp


# ----------------------------------------------------- control mechanics

def test_control_permutation_marginal_preservation_and_identity():
    rng1 = r._pcg_rng()
    rng2 = r._pcg_rng()
    names = [f"CIK{i:09d}" for i in range(60)]
    anchor = {n: float(i) * 0.37 for i, n in enumerate(names)}
    sectors = {n: ("S1" if i % 2 else "S0") for i, n in enumerate(names)}
    c1 = r.control_permutation(names, anchor, sectors, rng1)
    c2 = r.control_permutation(names, anchor, sectors, rng2)
    assert c1 == c2  # deterministic at the frozen seed
    for sec in ("S0", "S1"):
        block = [n for n in names if sectors[n] == sec]
        assert sorted(c1[n] for n in block) == \
            sorted(anchor[n] for n in block)  # EXACT multiset preservation
    # sectors of size 1 map identity
    one = {"CIK000000900": 3.0}
    c3 = r.control_permutation(["CIK000000900"], one,
                               {"CIK000000900": "S9"}, r._pcg_rng())
    assert c3 == one

    def _rho(xs, ys):
        n = len(xs)
        ra = {v: i for i, v in enumerate(sorted(xs))}
        rb = {v: i for i, v in enumerate(sorted(ys))}
        ax = [ra[v] for v in xs]
        ay = [rb[v] for v in ys]
        mx, my = sum(ax) / n, sum(ay) / n
        cov = sum((x - mx) * (y - my) for x, y in zip(ax, ay))
        vx = math.sqrt(sum((x - mx) ** 2 for x in ax))
        vy = math.sqrt(sum((y - my) ** 2 for y in ay))
        return cov / (vx * vy)

    # expected ~0 rank correlation vs the anchor ordering (frozen draw:
    # deterministic; asserted against a generous no-bias bound)
    rho = _rho([anchor[n] for n in names], [c1[n] for n in names])
    assert abs(rho) < 0.35
    moved = sum(1 for n in names if c1[n] != anchor[n])
    assert moved > len(names) // 2  # the entity-value link is destroyed


def test_control_rng_redrawn_per_decision_in_session_order():
    """Replaying the draw sequence from a fresh generator reproduces the
    first decision's permutation exactly, while the second draw differs
    (re-drawn per decision date)."""
    names = [f"CIK{i:09d}" for i in range(8)]
    anchor = {n: float(i) for i, n in enumerate(names)}
    sectors = {n: "S0" for n in names}
    rng = r._pcg_rng()
    first = r.control_permutation(names, anchor, sectors, rng)
    second = r.control_permutation(names, anchor, sectors, rng)
    replay = r.control_permutation(names, anchor, sectors, r._pcg_rng())
    assert first == replay
    assert first != second


# ------------------------------------------------------------ driver

def test_driver_dry_run_sanitized_deterministic(small_world):
    w = small_world
    layers = _layers(w)
    prices = r.load_prices(str(w["eod"]))
    folds = r.fold_sessions(prices, FOLDS_SMALL)
    led1, ok1 = drv.build_dry_run_ledger(
        "0" * 40, layers=layers, prices=prices, folds=folds)
    led2, ok2 = drv.build_dry_run_ledger(
        "0" * 40, layers=layers, prices=prices, folds=folds)
    b1 = json.dumps(led1, sort_keys=True)
    b2 = json.dumps(led2, sort_keys=True)
    assert b1 == b2  # byte-identical, no wall-clock anywhere
    assert led1["scored"] is False and led1["real_pnl"] is False
    assert led1["published"] is False
    assert led1["counters"] == kernel.driver_ledger_counters(3, 0)
    assert led1["counters"]["published_delta"] == 0
    assert led1["counters"]["counter_provenance"].startswith("driver_emitted")
    assert led1["record_ids_pairwise_distinct"] is True
    for cell in led1["cells"]:
        assert cell["scored"] is False and cell["real_pnl"] is False
        assert "metrics" not in cell["record"]
        for g in cell["non_vacuity_gates"]:
            assert "margin_to_fail" in g
    # the small fixture populates only fold 1: 28 decisions < 30 overall
    nv = {g["gate"]: g for g in led1["non_vacuity_gates"]}
    assert nv["nv_scored_decisions_overall_ge"]["verdict"] == "FAIL"
    assert nv["nv_scored_decisions_per_fold_ge"]["verdict"] == "PASS"
    assert nv["nv_noncash_legs_per_decision_ge"]["verdict"] == "PASS"
    assert ok1 is False and ok2 is False


def test_big_world_dry_run_ok(tmp_path, monkeypatch):
    """End-to-end wiring on a fixture big enough to satisfy every
    non-vacuity gate: ok is True."""
    w = build_big_world(tmp_path)
    _wire(monkeypatch, w)
    layers = _layers(w)
    prices = r.load_prices(str(w["eod"]))
    folds = r.fold_sessions(prices, FOLDS_BIG)
    led, ok = drv.build_dry_run_ledger("0" * 40, layers=layers,
                                       prices=prices, folds=folds)
    for g in led["non_vacuity_gates"]:
        assert g["verdict"] == "PASS", g
    assert ok is True
    anchor = next(c for c in led["cells"]
                  if c["arm_id"] == "SFV11-A5-H1-ANCHOR")["record"]
    assert anchor["scored_decisions_total"] >= 30
    per_fold = {}
    for x in anchor["schedule"]:
        if x.get("event") is None:
            per_fold[x["fold"]] = per_fold.get(x["fold"], 0) + 1
    assert min(per_fold.values()) >= 5


def test_driver_dry_run_empty_books_fail(tmp_path, monkeypatch):
    """Zero populated decisions (no stamp ever visible) -> empty books ->
    non-vacuity gates FAIL -> DRY_RUN_FAIL (sanctioned close)."""
    w = build_world(tmp_path, stamps_future="2030-06-01")
    _wire(monkeypatch, w)
    layers = _layers(w)
    prices = r.load_prices(str(w["eod"]))
    folds = r.fold_sessions(prices, FOLDS_SMALL)
    led, ok = drv.build_dry_run_ledger("0" * 40, layers=layers,
                                       prices=prices, folds=folds)
    assert ok is False
    nv = {g["gate"]: g for g in led["non_vacuity_gates"]}
    assert nv["nv_scored_decisions_overall_ge"]["observed"] == 0
    assert nv["nv_noncash_legs_per_decision_ge"]["observed"] == 0


def test_driver_main_dry_run_writes_ledger_fail_exit(small_world, monkeypatch):
    monkeypatch.delenv("V11_LAUNCH_AUTHORIZED", raising=False)
    out = small_world["tmp"] / "ledger_dryrun.json"
    monkeypatch.setattr(drv, "LEDGER_DRYRUN", str(out))
    monkeypatch.setattr(drv, "build_layers", lambda: _layers(small_world))
    monkeypatch.setattr(drv, "load_prices",
                        lambda: r.load_prices(str(small_world["eod"])))
    monkeypatch.setattr(
        drv, "fold_sessions",
        lambda prices, folds=None: r.fold_sessions(prices, FOLDS_SMALL))
    with pytest.raises(SystemExit, match="DRY_RUN_FAIL"):
        drv.main(["--dry-run"])  # small fixture: nv overall gate blocks
    first = out.read_bytes()
    with pytest.raises(SystemExit):
        drv.main(["--dry-run"])
    assert out.read_bytes() == first  # byte-equal double generation
    ledger = json.loads(out.read_text())
    assert ledger["scored"] is False and ledger["real_pnl"] is False
    assert ledger["go_phrase_observed"] is None
    assert ledger["launch_flag_observed"] is False


def test_driver_scored_refused_before_any_work(small_world, monkeypatch):
    monkeypatch.delenv("V11_LAUNCH_AUTHORIZED", raising=False)
    # exact phrase but no env: refused BEFORE any work (no git probe, no load)
    def _boom():
        raise AssertionError("work attempted before authorization")
    monkeypatch.setattr(drv, "_git_head", _boom)
    with pytest.raises(SystemExit, match="REFUSED"):
        drv.main([r.GO_PHRASE])
    # env set but wrong phrase: still refused before any work
    monkeypatch.setenv("V11_LAUNCH_AUTHORIZED", "1")
    with pytest.raises(SystemExit, match="REFUSED"):
        drv.main(["GO STOCKS V9 SCORED EXECUTION"])
    with pytest.raises(SystemExit, match="REFUSED"):
        drv.main([])


def test_driver_scored_pipeline_and_gates(small_world, monkeypatch):
    monkeypatch.delenv("V11_LAUNCH_AUTHORIZED", raising=False)
    monkeypatch.setenv("V11_LAUNCH_AUTHORIZED", "1")  # test scope only
    w = small_world
    bench = w["bench"]
    bench.mkdir(parents=True, exist_ok=True)
    for t in ["SPY"] + list(SECTORS):
        bars = [{"date": d, "open": 100.0, "high": 100.0, "low": 100.0,
                 "close": 100.0, "adjusted_close": 100.0, "volume": 0}
                for d in w["days"]]
        (bench / f"{t}.json").write_text(json.dumps(bars))
    ledger_p = w["tmp"] / "execution_ledger.json"
    verdicts_p = w["tmp"] / "family_verdicts.json"
    monkeypatch.setattr(drv, "LEDGER", str(ledger_p))
    monkeypatch.setattr(drv, "VERDICTS", str(verdicts_p))
    monkeypatch.setattr(drv, "build_layers", lambda: _layers(w))
    monkeypatch.setattr(drv, "load_prices",
                        lambda: r.load_prices(str(w["eod"])))
    monkeypatch.setattr(
        drv, "fold_sessions",
        lambda prices, folds=None: r.fold_sessions(prices, FOLDS_SMALL))
    monkeypatch.setattr(drv, "load_bench", lambda: _fixture_bench(w))
    drv.main([r.GO_PHRASE])
    ledger = json.loads(ledger_p.read_text())
    verdicts = json.loads(verdicts_p.read_text())
    assert ledger["counters"]["observed_delta"] == 8  # 3 arms x2 + 2 drop-one
    assert ledger["counters"]["published_delta"] == 0
    v = verdicts["SFV11-A5-H1"]
    assert v["family_verdict"] in {"STAGE_A_SURVIVOR_CANDIDATE",
                                   "FALSIFIED_BY_CONTROL", "REJECT"}
    names = [g["gate"] for g in v["anchor"]["gates"]]
    for expected in ("expectancy_gt", "position_pf_ge", "folds_positive_ge",
                     "min_populated_fold_pf_ge", "max_fold_mdd_le",
                     "fold_positive_share_le", "etf_positive_share_le",
                     "etf_share_le_packet",
                     "risk_matched_excess_positive_folds_ge",
                     "anchor_overall_alpha_gt"):
        assert expected in names
        row = next(g for g in v["anchor"]["gates"] if g["gate"] == expected)
        assert "margin_to_fail" in row
    # frozen v11 thresholds bind (ETF 0.50, PF 1.10 - not the v9 values)
    assert next(g for g in v["anchor"]["gates"]
                if g["gate"] == "etf_positive_share_le")["threshold"] == 0.50
    assert next(g for g in v["anchor"]["gates"]
                if g["gate"] == "position_pf_ge")["threshold"] == 1.10
    control_names = [g["gate"] for g in v["control"]["gates"]]
    assert "control_alpha_abs_ratio_lt" in control_names
    # tied fixture: control == anchor identically -> reproduction kill fires
    assert v["control"]["reproduces_anchor"] is True
    assert v["family_verdict"] == "FALSIFIED_BY_CONTROL"
    packet = {g["gate"]: g for g in v["packet_gates"]}
    assert {"drop_one_symbol_survival", "drop_one_fold_survival",
            "drop_one_process_leg_survival",
            "neighbor_mechanism_support"} <= set(packet)
    reruns = [c for c in ledger["cells"] if c.get("rerun")]
    assert {c["rerun"] for c in reruns} == {
        "drop_one_symbol", "drop_one_process_leg_depth_ge3"}


def test_drop_one_fold_expectancy_hand_computed():
    xs = [{"pnl": 0.01, "fold": "F1"}, {"pnl": -0.004, "fold": "F1"},
          {"pnl": 0.02, "fold": "F2"}, {"pnl": 0.006, "fold": "F3"}]
    ok, vals = drv.drop_one_fold_expectancy(xs, ["F1", "F2", "F3"])
    # drop F1 -> (0.02+0.006)/2 = 0.013; drop F2 -> 0.012/3 = 0.004;
    # drop F3 -> 0.026/3 = 0.008666...
    assert ok is True
    assert vals == [pytest.approx(0.013), pytest.approx(0.004),
                    pytest.approx(0.026 / 3)]
    ok2, _ = drv.drop_one_fold_expectancy(
        [{"pnl": -0.01, "fold": "F1"}, {"pnl": 0.001, "fold": "F2"}],
        ["F1", "F2"])
    assert ok2 is False  # dropping F2 leaves the negative fold alone


def test_redact_and_no_secrets_boundary():
    assert drv.redact("boom api_token=SECRET123 end") == "boom REDACTED end"
    with pytest.raises(RuntimeError):
        drv.assert_no_secrets({"err": "EODHD_API_KEY=abc"})
    drv.assert_no_secrets({"clean": True})
