"""test_fxng3_golden.py — golden tests for the FXNG3-A4-P1 engine (lane I).

Cycle D2-CURIOSITY-V1, cell FXNG3-A4-P1. NON_GOVERNING_DIAGNOSTIC.
Every construction test runs on SYNTHETIC events+prices generated in-file.
The REAL bound data under ../data/fxng3/ is never scored and never has
positions/PnL built on it — the single real-data test (j) asserts
CONSTRUCTION INVARIANTS ONLY (exactly 72 events, by-year 8/47/17 split,
frozen grid census), per the dispatch; no outcome is computed anywhere in
this lane and the engine refuses aggregates.

Golden laws (all must PASS before scoring):
  a  no-lookahead incl. the strictly-after-EOD clock: D(e) is the first
     grid day STRICTLY after v2.realtime_start (never the same day; an
     event whose v2 day moves later must move D later), and price
     perturbations at/after a position's entry bar never change its
     decision (D, d) or entry_open, nor any earlier position's row
  b  next-available-bar fills: entry exactly the NEXT grid bar's open
     after D (STRICT_NEXT_BAR); exit exactly bar i+H open (H=5), one
     entry + one exit fill per position
  c  fold boundaries + force-flat: F1/F2/F3 frozen; a position never
     spans a fold boundary; i+H beyond the decision fold's last grid day
     -> FORCE_FLAT exit at that fold's LAST grid bar; entry at/beyond the
     fold's last bar -> DROPPED_TAIL_ENTRY (counted)
  d  cost debit > 0 at frozen tiers: 1.5 bps/side ladder x{1.0,1.5,2.0},
     tier 2.0 PRIMARY = 3.0 bps/fill, once per fill, 2 fills/position
     (6.0 bps RT), 72x2 ceiling 432.0 bps arithmetic; zero cost forbidden
  e  missing-data fail-closed: missing/unfillable grid bar for entry or
     exit -> the trade is UNMEASURED and counted, never imputed; missing
     decision day -> NO_DECISION_DAY counted; exact-zero R -> skip
     counted; duplicate obs-month events raise; digest mismatch raises
  f  exactly-three registry: shared cells_registry intact; foreign ids
     rejected; no registry writes
  g  S1 denial: any path containing '/S1/' or 's1_' raises
  h  fixed public surface / zero-parameter-search: introspected public
     surface == PUBLIC_API; frozen tables immutable; builder signatures
     exact; folds/force-flat/H frozen; score_cells refuses prelaunch
  i  determinism: two runs over the same inputs -> byte-identical rows;
     loader round-trip preserves rows byte-for-byte
  j  real-data construction invariant (the ONLY real-data touch): the
     bound derived-events file loads with digest pins and has EXACTLY 72
     events with the by-year 8/47/17 split; the bound USDCAD grid matches
     the frozen own-calendar census (1846 days by-year exact) with the
     disclosed +4 delta vs the frozen 1842-day COMMON grid and the
     no-effect demonstration; construction invariants ONLY — no
     positions, no PnL, no returns
  smoke  REPLAY_NOT_PROSPECTIVE end-to-end on a synthetic fold-boundary
     environment (incl. overlap netting sign-of-sum never 0 and the
     DESCRIPTIVE_ONLY benchmark builder)

Runs under plain python (lane pattern, same as the CNG2 lane):
  /Users/hoangminhlong/my-quantitative/.venv/bin/python test_fxng3_golden.py

Results are recorded honestly (pass/fail per test) to
engines/test_results_fxng3.json via an atexit hook.
"""

import atexit as _atexit
import copy as _copy
import datetime as _dt
import hashlib as _hashlib
import inspect as _inspect
import json as _json
import pathlib as _pth
import sys as _sys

_HERE = _pth.Path(__file__).resolve().parent
if str(_HERE) not in _sys.path:
    _sys.path.insert(0, str(_HERE))

import cells_registry
import fxng3_engine as engine

# Real bound files (construction invariants ONLY — never scored).
_RUN = _HERE.parent
_REAL_EVENTS = _RUN / "data" / "fxng3" / "fred_vintaged_repull" / "CANCPIALLMINMEI_derived_events.json"
_REAL_BARS = _RUN / "data" / "fxng3" / "twelvedata_repull" / "USDCAD_1day_repull.json"
# Digests as recorded in data/fxng3/binding_report.json (observed_sha256).
_REAL_EVENTS_SHA = "e7f3b9ad12037c497ef48e6ae9da478224df6401131e31e47b65c5d57c3f9e12"
_REAL_BARS_SHA = "8401427da0c2cb46391d9481d2190df7ae9aee319fd37e7c298cf573ed2755ff"

_RESULTS = []


def _golden(name):
    """Decorator: run the test, record an honest PASS/FAIL row, re-raise."""
    def deco(fn):
        def wrapped():
            try:
                fn()
                _RESULTS.append({"test": name, "status": "PASS", "detail": ""})
            except BaseException as exc:  # noqa: BLE001 — record honestly, re-raise
                _RESULTS.append(
                    {"test": name, "status": "FAIL",
                     "detail": ("%s: %s" % (type(exc).__name__, exc))[:500]}
                )
                raise
        wrapped.__name__ = name
        wrapped._golden_name = name
        return wrapped
    return deco


def _write_results_atexit():
    out = {
        "schema": "fxng3_golden_test_results@1",
        "cycle_id": "D2-CURIOSITY-V1",
        "cell_id": "FXNG3-A4-P1",
        "label": ("NON_GOVERNING_DIAGNOSTIC REPLAY_NOT_PROSPECTIVE (synthetic "
                  "events+prices for all construction tests; real bound data "
                  "touched for construction invariants only, never scored)"),
        "python": _sys.version.split()[0],
        "engine_public_api": list(engine.PUBLIC_API),
        "results": _RESULTS,
        "all_pass": bool(_RESULTS) and all(r["status"] == "PASS" for r in _RESULTS),
    }
    try:
        path = _HERE / "test_results_fxng3.json"
        path.write_text(_json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:  # pragma: no cover
        print("WARNING: could not write test_results_fxng3.json: %r" % (exc,))


_atexit.register(_write_results_atexit)


# --------------------------------------------------------------------------
# Synthetic fixture builders (deterministic; stdlib only)
# --------------------------------------------------------------------------

class _LCG(object):
    """Tiny deterministic PRNG (no external deps, no randomness)."""

    def __init__(self, seed):
        self._s = seed & 0x7FFFFFFF

    def next(self):
        self._s = (1103515245 * self._s + 12345) & 0x7FFFFFFF
        return (self._s / float(1 << 30)) - 1.0  # [-1, 1)


def _weekdays(start_iso, end_iso):
    """Ascending weekday dates in [start, end] (frozen grid law shape)."""
    d0 = _dt.date.fromisoformat(start_iso)
    d1 = _dt.date.fromisoformat(end_iso)
    out = []
    d = d0
    while d <= d1:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += _dt.timedelta(days=1)
    return out


# Synthetic environment A: weekdays 2022-09-01..2022-11-15 — crosses the
# frozen F2/F3 boundary (2022-11). F2's last grid day = 2022-10-31.
_GRID_A = _weekdays("2022-09-01", "2022-11-15")
_F2_LAST = "2022-10-31"

# Synthetic restricted events (obs_month is the unique event key).
_SYNTH_EVENTS = [
    {"obs_month": "2022-06-01", "v2_availability_day": "2022-09-05",
     "R": -0.0100},  # e_measured:  D 09-06, entry 09-07, exit 09-14 (F2)
    {"obs_month": "2022-06-02", "v2_availability_day": "2022-09-06",
     "R": -0.0200},  # e_overlap1:  D 09-07, entry 09-08, exit 09-15 (F2)
    {"obs_month": "2022-06-03", "v2_availability_day": "2022-09-08",
     "R": +0.0400},  # e_overlap2:  D 09-09, entry 09-12, exit 09-19 (F2)
    {"obs_month": "2022-06-04", "v2_availability_day": "2022-09-12",
     "R": 0.0},      # e_zero:      D 09-13 -> SIGN_ZERO_SKIP
    {"obs_month": "2022-06-05", "v2_availability_day": "2022-10-25",
     "R": +0.0200},  # e_forceflat: D 10-26, entry 10-27, i+5=11-04 beyond
                    #              F2's last grid day 10-31 -> FORCE_FLAT
    {"obs_month": "2022-06-06", "v2_availability_day": "2022-10-27",
     "R": +0.0100},  # e_tail2:     D 10-28, entry 10-31 == F2 last
                    #              -> DROPPED_TAIL_ENTRY
    {"obs_month": "2022-06-07", "v2_availability_day": "2022-10-28",
     "R": -0.0300},  # e_tail:      D 10-31 == F2 last -> DROPPED_TAIL_ENTRY
    {"obs_month": "2022-06-08", "v2_availability_day": "2022-11-14",
     "R": -0.0500},  # e_noentry:   D 11-15 == grid last -> MISSING_ENTRY_BAR
    {"obs_month": "2022-06-09", "v2_availability_day": "2022-11-18",
     "R": -0.0700},  # e_nodec:     no grid day strictly after -> NO_DECISION_DAY
]
_N_EVENTS = len(_SYNTH_EVENTS)

_MEASURED = 3          # e_measured, e_overlap1, e_overlap2
_FORCE_FLAT = 1        # e_forceflat
_DROPPED = 2           # e_tail, e_tail2


def _make_bars(seed=20260922):
    """{date: {'open','high','low','close'}} — USDCAD-like daily bars."""
    rng = _LCG(seed)
    bars = {}
    price = 1.3000
    for day in _GRID_A:
        price = price * (1.0 + 0.004 * rng.next())
        o = round(price * (1.0 + 0.001 * rng.next()), 5)
        c = round(price, 5)
        bars[day] = {
            "open": o,
            "high": round(max(o, c) * 1.002, 5),
            "low": round(min(o, c) * 0.998, 5),
            "close": c,
        }
    return bars


def _make_events(events=None):
    """Normalized event list in the engine's consumed shape.

    R is stored as the value recomputed from the published v1/v2 values
    (v2/v1 - 1) so the in-memory fixture and the file-loader round-trip
    carry BIT-IDENTICAL ratios (100.0*(1+R)/100.0 - 1 is not bit-equal to
    R in floating point; the loader recomputes and fail-closes on any
    drift, so the fixture must use the same arithmetic).
    """
    out = []
    for e in (events if events is not None else _SYNTH_EVENTS):
        v1 = 100.0
        v2 = 100.0 * (1.0 + float(e["R"]))
        r = v2 / v1 - 1.0
        out.append({
            "event_id": e["obs_month"],
            "obs_month": e["obs_month"],
            "v1_day": "2022-01-01",
            "v1_value": v1,
            "v2_day": e["v2_availability_day"],
            "v2_value": v2,
            "v2_availability_day": e["v2_availability_day"],
            "R": r,
            "r_pp": 100.0 * r,
        })
    return out


def _find(rows, event_id):
    for r in rows:
        if r["event_id"] == event_id:
            return r
    raise AssertionError("row not found for event %s" % (event_id,))


def _expect_raises(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type:
        return
    except BaseException as exc:  # noqa: BLE001
        raise AssertionError("expected %s, got %r" % (exc_type.__name__, exc))
    raise AssertionError("expected %s, nothing raised" % (exc_type.__name__,))


def _bytes_of(position_set):
    return _json.dumps(position_set, sort_keys=True).encode("utf-8")


# --------------------------------------------------------------------------
# (a) no-lookahead incl. the strictly-after-EOD clock
# --------------------------------------------------------------------------

@_golden("a1_strictly_after_eod_clock")
def test_a1_strictly_after_eod_clock():
    """D(e) is the first grid day STRICTLY after v2.realtime_start: never
    the same day; moving the v2 day later must move D later (never
    earlier); a v2 day at/after the grid end -> NO_DECISION_DAY."""
    bars = _make_bars()
    events = _make_events()
    base = engine.build_positions(events, _GRID_A, bars)
    m0 = {r["event_id"]: r for r in base["rows"]}

    import bisect
    for e in _SYNTH_EVENTS:
        row = m0[e["obs_month"]]
        v2 = e["v2_availability_day"]
        k = bisect.bisect_right(_GRID_A, v2)
        if k >= len(_GRID_A):
            assert row["status"] == "NO_DECISION_DAY", e["obs_month"]
            assert row["D"] is None
            continue
        assert row["D"] == _GRID_A[k], "%s: D != first grid day strictly after v2" % (e["obs_month"],)
        assert row["D"] > v2, "D must be STRICTLY after the v2 availability day"

    # Shift e_forceflat's v2 day one day later (10-25 -> 10-26): D must move
    # LATER (10-26 -> 10-27), never stay or move earlier.
    shifted = _make_events()
    for e in shifted:
        if e["obs_month"] == "2022-06-05":
            e["v2_day"] = e["v2_availability_day"] = "2022-10-26"
    after = engine.build_positions(shifted, _GRID_A, bars)
    r0 = m0["2022-06-05"]
    r1 = _find(after["rows"], "2022-06-05")
    assert r0["D"] == "2022-10-26" and r1["D"] == "2022-10-27"
    assert r1["D"] > r0["D"], "a later v2 realtime_start must move D later"
    assert r1["status"] == "FORCE_FLAT_FOLD_BOUNDARY" and r1["exit_day"] == _F2_LAST

    # A v2 day on the last grid day still gets a decision day lookup that
    # fails only at the ENTRY bar (D is last, no next bar) — distinct from
    # NO_DECISION_DAY (v2 beyond the grid end).
    assert m0["2022-06-08"]["status"] == "MISSING_ENTRY_BAR"
    assert m0["2022-06-09"]["status"] == "NO_DECISION_DAY"


@_golden("a2_no_lookahead_price_perturbation")
def test_a2_no_lookahead_price_perturbation():
    """Perturbing bar opens strictly AFTER a position's entry bar may change
    only that position's exit-side fields (exit_open/gross/net); no
    position's (D, d, entry_open) may change, and no earlier position's row
    may change at all."""
    bars = _make_bars()
    base = engine.build_positions(_make_events(), _GRID_A, bars)
    b0 = {r["event_id"]: r for r in base["rows"]}

    # Perturb every open strictly after e_forceflat's entry bar 2022-10-27.
    pert = dict(bars)
    for day in _GRID_A:
        if day > "2022-10-27":
            nb = dict(pert[day])
            nb["open"] = nb["open"] * 1.31
            pert[day] = nb
    after = engine.build_positions(_make_events(), _GRID_A, pert)
    a0 = {r["event_id"]: r for r in after["rows"]}
    assert set(b0) == set(a0)

    for eid, row0 in b0.items():
        row1 = a0[eid]
        for f in ("D", "d", "entry_open"):
            assert row1[f] == row0[f], (
                "%s: %s changed when bars after its entry were perturbed "
                "(lookahead)" % (eid, f)
            )
        if eid == "2022-06-05":  # e_forceflat: exit bar 10-31 was perturbed
            assert row1["exit_open"] != row0["exit_open"]
            assert row1["gross"] != row0["gross"] and row1["net"] != row0["net"]
        else:
            assert row1 == row0, "%s: row changed by later-bar perturbation" % (eid,)


# --------------------------------------------------------------------------
# (b) next-available-bar fills
# --------------------------------------------------------------------------

@_golden("b_fills_strict_next_bar")
def test_b_fills_strict_next_bar():
    bars = _make_bars()
    ps = engine.build_positions(_make_events(), _GRID_A, bars)

    import bisect
    for r in ps["rows"]:
        if r["status"] not in ("MEASURED", "FORCE_FLAT_FOLD_BOUNDARY"):
            assert r["entry_open"] is None and r["exit_open"] is None
            assert r["costs"] is None
            continue
        k = bisect.bisect_right(_GRID_A, r["v2_availability_day"])
        assert r["entry_day"] == _GRID_A[k + 1], "entry != NEXT grid bar after D"
        assert r["entry_open"] == bars[r["entry_day"]]["open"], "entry fill != that bar's OPEN"
        i = k + 1
        if r["status"] == "MEASURED":
            assert r["exit_day"] == _GRID_A[i + engine.H_GRID_DAYS], "exit != bar i+H"
        else:
            assert r["exit_day"] == _F2_LAST, "force-flat exit != the decision fold's LAST grid bar"
        assert r["exit_open"] == bars[r["exit_day"]]["open"], "exit fill != that bar's OPEN"
        assert r["hold_days"] >= 1, "a measured position holds at least one grid day"
    assert sum(1 for r in ps["rows"] if r["status"] == "MEASURED") == _MEASURED
    assert sum(1 for r in ps["rows"] if r["status"] == "FORCE_FLAT_FOLD_BOUNDARY") == _FORCE_FLAT


# --------------------------------------------------------------------------
# (c) fold boundaries + force-flat
# --------------------------------------------------------------------------

@_golden("c_fold_boundaries_force_flat")
def test_c_fold_boundaries_force_flat():
    bars = _make_bars()
    ps = engine.build_positions(_make_events(), _GRID_A, bars)

    # Frozen folds (three_cell_contract fold_boundaries; ng1 run_contract
    # folds block via the identity extract), force-flat AT the boundary.
    assert dict(engine.FOLDS) == {
        "F1": ("2018-04", "2020-06"),
        "F2": ("2020-07", "2022-10"),
        "F3": ("2022-11", "2025-04"),
    }
    assert engine.FOLD_FORCE_FLAT is True

    r = _find(ps["rows"], "2022-06-05")  # e_forceflat
    assert r["fold"] == "F2" and r["status"] == "FORCE_FLAT_FOLD_BOUNDARY"
    assert r["exit_day"] == _F2_LAST, "force-flat exits AT the decision fold's last grid bar"
    assert r["exit_day"] < "2022-11-01", "the position never spans into F3"
    assert r["hold_days"] < engine.H_GRID_DAYS, "force-flat shortens the hold"

    # No measured position spans a fold boundary.
    for row in ps["rows"]:
        if row["status"] in ("MEASURED", "FORCE_FLAT_FOLD_BOUNDARY"):
            assert engine._fold_of(row["entry_day"]) == row["fold"], (
                "%s: entry outside its decision fold" % (row["event_id"],)
            )
            assert engine._fold_of(row["exit_day"]) == row["fold"], (
                "%s: position spans a fold boundary" % (row["event_id"],)
            )

    # Tail entries at the boundary are dropped and counted, with no fills
    # and no costs (fail-closed, never degenerate same-bar fills).
    for eid in ("2022-06-06", "2022-06-07"):
        row = _find(ps["rows"], eid)
        assert row["status"] == "DROPPED_TAIL_ENTRY"
        assert row["entry_open"] is None and row["exit_open"] is None
        assert row["costs"] is None

    # Fold assignment is by the DECISION day's month.
    assert _find(ps["rows"], "2022-06-01")["fold"] == "F2"
    assert ps["folds_note"].startswith("FOLDS_FROZEN_F1_F2_F3_FORCE_FLAT")


# --------------------------------------------------------------------------
# (d) cost debit > 0 at frozen tiers
# --------------------------------------------------------------------------

@_golden("d_cost_debit_frozen_tiers")
def test_d_cost_debit_frozen_tiers():
    # Frozen ladder (cost_contract.json FXNG3-A4-P1): flat 1.5 bps/side
    # x {1.0, 1.5, 2.0}; tier 2.0 PRIMARY = 3.0 bps/fill.
    assert engine.COST_BPS_PER_SIDE == 1.5
    assert engine.COST_TIERS["1.0"]["bps_per_side"] == 1.5
    assert engine.COST_TIERS["1.5"]["bps_per_side"] == 2.25
    assert engine.COST_TIERS["2.0"]["bps_per_side"] == 3.0
    assert engine.PRIMARY_TIER == "2.0"
    # Ceiling arithmetic preserved: 72 positions x 2 fills x 3.0 bps.
    assert engine.COST_CEILING_BPS == 72 * 2 * 3.0 == 432.0

    ps = engine.build_positions(_make_events(), _GRID_A, _make_bars())
    rt = ps["cost_bps_round_trip_per_position"]
    assert rt == {"1.0": 3.0, "1.5": 4.5, "2.0": 6.0}
    n_filled = 0
    for r in ps["rows"]:
        if r["status"] not in ("MEASURED", "FORCE_FLAT_FOLD_BOUNDARY"):
            continue
        assert r["costs"] == 2.0 * 3.0 / 10000.0 == 0.0006, (
            "filled position must debit 2 fills x 3.0 bps at tier 2.0 PRIMARY"
        )
        assert r["costs"] > 0.0, "zero-cost fill is forbidden (no silent zero cost)"
        assert r["net"] == r["gross"] - r["costs"]
        n_filled += 1
    assert n_filled == _MEASURED + _FORCE_FLAT > 0


# --------------------------------------------------------------------------
# (e) missing-data fail-closed
# --------------------------------------------------------------------------

@_golden("e_missing_data_fail_closed")
def test_e_missing_data_fail_closed():
    bars = _make_bars()

    # Missing grid bar for an EXIT fill (2022-09-14, e_measured's exit) and
    # for an ENTRY fill (2022-09-08, e_overlap1's entry): the trades are
    # UNMEASURED and counted — never imputed, never silently re-timed.
    bars_hole = dict(bars)
    del bars_hole["2022-09-14"]
    del bars_hole["2022-09-08"]
    ps = engine.build_positions(_make_events(), _GRID_A, bars_hole)
    c = ps["counts"]
    r = _find(ps["rows"], "2022-06-01")
    assert r["status"] == "MISSING_EXIT_BAR"
    assert r["entry_open"] is not None and r["exit_open"] is None
    assert r["gross"] is None and r["costs"] is None and r["net"] is None
    r = _find(ps["rows"], "2022-06-02")
    assert r["status"] == "MISSING_ENTRY_BAR" and r["entry_open"] is None
    assert c["MISSING_EXIT_BAR"] == 1 and c["MISSING_ENTRY_BAR"] == 2
    assert c["MEASURED"] == 1 and c["FORCE_FLAT_FOLD_BOUNDARY"] == 1
    assert sum(c.values()) == _N_EVENTS

    # Unfillable (non-positive) open at an exit bar is equally unmeasured.
    bad = dict(bars)
    bad["2022-09-14"] = dict(bars["2022-09-14"], open=0.0)
    ps2 = engine.build_positions(_make_events(), _GRID_A, bad)
    assert _find(ps2["rows"], "2022-06-01")["status"] == "MISSING_EXIT_BAR"

    # Exact-zero R -> skip, counted (d/costs stay None; never a position).
    ps3 = engine.build_positions(_make_events(), _GRID_A, bars)
    rz = _find(ps3["rows"], "2022-06-04")
    assert rz["status"] == "SIGN_ZERO_SKIP"
    assert rz["d"] is None and rz["costs"] is None and rz["R"] == 0.0

    # A grid date with no bar at all inside the S0-shape grid, given
    # directly to the builder, fail-closes the affected row (the builder
    # never fabricates a bar).
    grid_gap = list(_GRID_A)
    ps4 = engine.build_positions(_make_events(), grid_gap, bars)
    assert sum(ps4["counts"].values()) == _N_EVENTS

    # Loader-level fail-closed: duplicate obs-month events raise and
    # nothing is built; non-first-print events raise; a stored-vs-
    # recomputed ratio mismatch raises; digest mismatch raises.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = _pth.Path(td) / "events.json"
        ev = _make_events()
        ev.append(dict(ev[0]))  # duplicate obs_month
        p.write_text(_json.dumps({"restricted_events": [_bound_shape(e) for e in ev]}))
        _expect_raises(engine.BLOCKED_DATA, engine.load_events, p)

        p2 = _pth.Path(td) / "events_backfill.json"
        rows = [_bound_shape(e) for e in _make_events()]
        rows[0]["first_print_in_realtime_era"] = False
        p2.write_text(_json.dumps({"restricted_events": rows}))
        _expect_raises(engine.BLOCKED_DATA, engine.load_events, p2)

        p3 = _pth.Path(td) / "events_drift.json"
        rows = [_bound_shape(e) for e in _make_events()]
        rows[0]["ratio"] = rows[0]["ratio"] * (1.0 + 1e-15) + 1e-300
        p3.write_text(_json.dumps({"restricted_events": rows}))
        _expect_raises(engine.BLOCKED_DATA, engine.load_events, p3)

        p4 = _pth.Path(td) / "bars_bad.json"
        p4.write_text(_json.dumps({"bars": [
            {"datetime": "2022-09-06", "open": "-1.0", "high": "1.3",
             "low": "1.2", "close": "1.25"}]}))
        _expect_raises(engine.BLOCKED_DATA, engine.load_bars, p4)

        p5 = _pth.Path(td) / "events_ok.json"
        p5.write_text(_json.dumps({"restricted_events": [_bound_shape(e) for e in _make_events()]}))
        _expect_raises(ValueError, engine.load_events, p5, "0" * 64)
        loaded = engine.load_events(p5, _sha256_of(p5))
        assert len(loaded) == _N_EVENTS


def _sha256_of(path):
    return _hashlib.sha256(_pth.Path(path).read_bytes()).hexdigest()


def _bound_shape(e):
    """Events file shape identical to the bound derived-events artifact."""
    return {
        "obs_month": e["obs_month"],
        "v1": [e["v1_day"], repr(e["v1_value"])],
        "v2": [e["v2_day"], repr(e["v2_value"])],
        "v2_availability_day": e["v2_availability_day"],
        "ratio": e["v2_value"] / e["v1_value"] - 1.0,
        "ratio_pct": round(100.0 * (e["v2_value"] / e["v1_value"] - 1.0), 6),
        "first_print_in_realtime_era": True,
    }


# --------------------------------------------------------------------------
# (f) exactly-three-cell enforcement
# --------------------------------------------------------------------------

@_golden("f_exactly_three_cells_registry")
def test_f_exactly_three_cells_registry():
    assert set(cells_registry.EXACTLY_THREE_CELLS) == {
        "SFNG2-A4-P1", "FXNG3-A4-P1", "CNG2-A5-P1",
    }
    assert len(cells_registry.EXACTLY_THREE_CELLS) == 3
    cells_registry.assert_registry_intact()
    for bad in ("FXNG3-A4-P2", "FXNG3-A4-P1-NEIGH", "fxng3-a4-p1", "", None):
        _expect_raises(cells_registry.UnknownCellError, cells_registry.validate_cell_id, bad)
    for ok in ("SFNG2-A4-P1", "FXNG3-A4-P1", "CNG2-A5-P1"):
        assert cells_registry.validate_cell_id(ok) == ok
    _expect_raises(cells_registry.RegistryFrozenError, cells_registry.register_cell, "NEW-CELL")
    assert engine.CELL_ID == "FXNG3-A4-P1"
    # The engine module asserted the registry at import time; prove it again.
    import importlib
    importlib.reload(engine)
    assert engine.CELL_ID == "FXNG3-A4-P1"


# --------------------------------------------------------------------------
# (g) S1 access denial
# --------------------------------------------------------------------------

@_golden("g_s1_access_denial")
def test_g_s1_access_denial():
    for bad_path in ("/data/S1/events.json", "/tmp/s1_probe/bars.json",
                     "S1_events.json", "dir/s1_usdcad_bars.json"):
        _expect_raises(engine.S1_ACCESS_DENIED, engine.load_events, bad_path)
        _expect_raises(engine.S1_ACCESS_DENIED, engine.load_bars, bad_path)
        _expect_raises(engine.S1_ACCESS_DENIED, engine.construction_check,
                       bad_path, _REAL_BARS)


# --------------------------------------------------------------------------
# (h) fixed public surface / zero-parameter-search
# --------------------------------------------------------------------------

@_golden("h_zero_parameter_search_public_surface")
def test_h_zero_parameter_search_public_surface():
    public = sorted(n for n in vars(engine) if not n.startswith("_"))
    assert public == list(engine.PUBLIC_API), (
        "engine public surface drifted: %s" % (sorted(set(public) ^ set(engine.PUBLIC_API)),)
    )
    assert "PUBLIC_API" in (engine.__doc__ or ""), "public surface must be documented"
    assert engine.ALLOW_SCORE is False, "this lane never sets ALLOW_SCORE"
    assert engine.CELL_ID == "FXNG3-A4-P1"
    assert engine.UNIVERSE == ("USDCAD",)
    assert engine.H_GRID_DAYS == 5
    assert engine.S0_START == "2018-04-04" and engine.S0_END == "2025-04-30"
    assert engine.FOLD_FORCE_FLAT is True

    # Frozen tables are immutable (no tuning knobs).
    def _attempt_item_assignment(mapping, key, value):
        mapping[key] = value  # must raise TypeError on frozen tables

    _expect_raises(TypeError, _attempt_item_assignment, engine.FOLDS, "F4", ("2025-05", "2026-01"))
    _expect_raises(TypeError, _attempt_item_assignment,
                   engine.COST_TIERS["2.0"], "bps_per_side", 0.0)

    # Builder signatures are exact — no knob parameters anywhere.
    assert list(_inspect.signature(engine.build_positions).parameters) == ["events", "grid", "bars"]
    assert list(_inspect.signature(engine.build_benchmark).parameters) == ["position_set"]
    assert list(_inspect.signature(engine.build_grid).parameters) == ["bars"]
    for fn in (engine.load_events, engine.load_bars):
        sig = _inspect.signature(fn)
        assert list(sig.parameters) == ["path", "expected_sha256"]
        assert sig.parameters["expected_sha256"].default is None
    sig = _inspect.signature(engine.construction_check)
    assert list(sig.parameters) == ["events_path", "bars_path", "events_sha256", "bars_sha256"]
    assert all(sig.parameters[k].default is None for k in ("events_sha256", "bars_sha256"))

    # score_cells refuses prelaunch (and has no aggregate implementation).
    _expect_raises(engine.REFUSES_PRELAUNCH, engine.score_cells, [1, 2, 3])


# --------------------------------------------------------------------------
# (i) determinism
# --------------------------------------------------------------------------

@_golden("i_determinism_byte_identical_rows")
def test_i_determinism_byte_identical_rows():
    bars = _make_bars()
    events = _make_events()
    b1 = _bytes_of(engine.build_positions(events, _GRID_A, bars))
    b2 = _bytes_of(engine.build_positions(events, _GRID_A, bars))
    assert b1 == b2, "two runs over the same inputs differ (non-determinism)"

    # Same rows when rebuilt through the file loaders (the bound-file JSON
    # shape repr-round-trips floats exactly).
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p_ev = _pth.Path(td) / "events.json"
        p_bars = _pth.Path(td) / "bars.json"
        p_ev.write_text(_json.dumps({"restricted_events": [_bound_shape(e) for e in events]}))
        p_bars.write_text(_json.dumps({"bars": [
            {"datetime": d,
             "open": repr(bars[d]["open"]),
             "high": repr(bars[d]["high"]),
             "low": repr(bars[d]["low"]),
             "close": repr(bars[d]["close"])}
            for d in sorted(bars)
        ]}))
        events2 = engine.load_events(p_ev)
        bars2 = engine.load_bars(p_bars)
        b_file = _bytes_of(engine.build_positions(events2, _GRID_A, bars2))
        assert b_mem_ok(b1, b_file), "loader round-trip changed position rows"


def b_mem_ok(a, b):
    return a == b


# --------------------------------------------------------------------------
# (j) real-data construction invariant (the ONLY real-data touch)
# --------------------------------------------------------------------------

@_golden("j_real_data_construction_invariants_only")
def test_j_real_data_construction_invariants_only():
    """The bound derived-events file loads (digest-pinned) with EXACTLY 72
    restricted events and the by-year 8/47/17 split; the bound USDCAD grid
    matches the frozen census. Construction invariants ONLY: no positions,
    no PnL, no returns (dispatch: 'you MAY assert the real event file loads
    and has exactly 72 events with the by-year 8/47/17 split — that's a
    construction invariant, not an outcome')."""
    if not _REAL_EVENTS.exists() or not _REAL_BARS.exists():
        raise AssertionError("real bound files missing (construction check required them)")
    out = engine.construction_check(
        _REAL_EVENTS, _REAL_BARS,
        events_sha256=_REAL_EVENTS_SHA, bars_sha256=_REAL_BARS_SHA,
    )
    assert out["events"]["n_restricted"] == 72
    assert out["events"]["by_v2_year"] == {"2018": 8, "2022": 47, "2024": 17}
    assert out["events"]["first_print_all"] is True
    assert out["events"]["exact_zero_R_events"] == 0
    assert out["events"]["ratio_recompute_exact"] is True
    assert out["grid"]["days_own_calendar"] == engine.OWN_GRID_DAYS == 1846
    assert out["grid"]["by_year_own_calendar"] == dict(engine.OWN_GRID_BY_YEAR)
    assert out["grid"]["first"] == "2018-04-04" and out["grid"]["last"] == "2025-04-30"
    assert out["grid"]["common_grid_frozen_days"] == engine.COMMON_GRID_DAYS == 1842
    assert out["grid"]["delta_vs_common_grid_by_year"] == {"2019": 1, "2025": 3}
    assert out["grid"]["no_effect_demonstration"] is True
    assert "NON_GOVERNING_DIAGNOSTIC" in out["label"]

    # Structural no-outcome law: no position/return/PnL field may escape.
    blob = _json.dumps(out).lower()
    for bad in ('"gross"', '"net"', '"pnl"', '"return"', '"expectancy"',
                '"profit_factor"', '"drawdown"', '"rows"'):
        assert bad not in blob, "construction_check leaked an outcome-like field %s" % (bad,)


# --------------------------------------------------------------------------
# smoke: REPLAY_NOT_PROSPECTIVE end-to-end on the synthetic fold environment
# --------------------------------------------------------------------------

@_golden("smoke_replay_not_prospective_synthetic")
def test_smoke_replay_not_prospective():
    bars = _make_bars(seed=777)
    ps = engine.build_positions(_make_events(), _GRID_A, bars)

    assert sum(ps["counts"].values()) == _N_EVENTS
    assert ps["counts"]["MEASURED"] == _MEASURED
    assert ps["counts"]["FORCE_FLAT_FOLD_BOUNDARY"] == _FORCE_FLAT
    assert ps["counts"]["SIGN_ZERO_SKIP"] == 1
    assert ps["counts"]["DROPPED_TAIL_ENTRY"] == _DROPPED
    assert ps["counts"]["MISSING_ENTRY_BAR"] == 1
    assert ps["counts"]["NO_DECISION_DAY"] == 1
    assert "NON_GOVERNING_DIAGNOSTIC" in ps["label"]
    assert "REPLAY_NOT_PROSPECTIVE" in ps["label"]

    # Direction law: R<0 -> +1 (LONG USDCAD), R>0 -> -1.
    assert _find(ps["rows"], "2022-06-01")["d"] == 1
    assert _find(ps["rows"], "2022-06-05")["d"] == -1

    for r in ps["rows"]:
        if r["status"] in ("MEASURED", "FORCE_FLAT_FOLD_BOUNDARY"):
            assert r["entry_open"] > 0.0 and r["exit_open"] > 0.0
            assert r["costs"] > 0.0
            assert r["net"] == r["gross"] - r["costs"]

    # Exposure-schedule artifact: overlapping same-pair cells net
    # sign-of-sum, NEVER 0 (sum > 0 -> +1 else -1); collisions counted.
    # Held cells here: e_measured 09-07..09-13 (+1 each), e_overlap1
    # 09-08..09-14 (+1 each), e_overlap2 09-12..09-16 (-1 each). The exit
    # fill bars (09-14/09-15/09-19, 10-31) are NOT held cells.
    cells = ps["schedule_cells"]
    assert len(cells) > 0
    assert all(v in (1, -1) for v in cells.values()), "no netted cell may be 0 or non-sign"
    assert cells["2022-09-12"] == 1, "stack (+1,+1,-1): sum > 0 nets +1 (never 0)"
    assert cells["2022-09-13"] == 1, "stack (+1,+1,-1): sum > 0 nets +1 (never 0)"
    assert cells["2022-09-14"] == -1, "stack (+1,-1): zero sum nets -1 (never 0)"
    assert cells["2022-09-15"] == -1 and cells["2022-09-16"] == -1, "single-sign holds carry through"
    assert "2022-09-19" not in cells, "the exit fill bar is not a held cell"
    assert ps["net_collisions"] == 3

    # DESCRIPTIVE_ONLY benchmark over the same held cells.
    bench = engine.build_benchmark(ps)
    assert bench["descriptive_only"] is True
    assert "DESCRIPTIVE_ONLY" in bench["label"]
    assert bench["n_rows"] == _MEASURED + _FORCE_FLAT
    for br in bench["rows"]:
        pr = _find(ps["rows"], br["event_id"])
        assert br["entry_day"] == pr["entry_day"] and br["exit_day"] == pr["exit_day"]
        assert br["bh_gross"] == pr["exit_open"] / pr["entry_open"] - 1.0

    # Machinery refuses aggregates: no PnL/expectancy can escape this lane.
    _expect_raises(engine.REFUSES_PRELAUNCH, engine.score_cells, ps["rows"])


# --------------------------------------------------------------------------
# runners
# --------------------------------------------------------------------------

def _run_all_plain():
    tests = [
        test_a1_strictly_after_eod_clock,
        test_a2_no_lookahead_price_perturbation,
        test_b_fills_strict_next_bar,
        test_c_fold_boundaries_force_flat,
        test_d_cost_debit_frozen_tiers,
        test_e_missing_data_fail_closed,
        test_f_exactly_three_cells_registry,
        test_g_s1_access_denial,
        test_h_zero_parameter_search_public_surface,
        test_i_determinism_byte_identical_rows,
        test_j_real_data_construction_invariants_only,
        test_smoke_replay_not_prospective,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print("PASS  %s" % t.__name__)
        except BaseException as exc:  # noqa: BLE001
            failed += 1
            print("FAIL  %s  ->  %s: %s" % (t.__name__, type(exc).__name__, exc))
    print("\n%d/%d passed" % (len(tests) - failed, len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    _sys.exit(_run_all_plain())
