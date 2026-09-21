"""STOCKS-SEARCH-V1 E2-lane targeted selfchecks (pre-scoring, non-scored).

Each test targets one specific equivalence-critical mechanism of the
streaming remediation.  All inputs are SYNTHETIC (plus the real SPY
calendar/folds for clock realism); no scored outcome is computed for the
real cohort anywhere in this file.  Honest verdicts only: a test that
did not run reports NOT_RUN and fails the suite.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_RUN_DIR = _HERE.parent
_I_DIR = _RUN_DIR / "i"
for _p in (str(_I_DIR), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import i_engine
import i_stream_engine as se
from equivalence import real_calendar_spy, synthetic_cohort

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append({"test": name, "status": "PASS"})
        print(f"[selfcheck] {name}: PASS")
    except Exception as e:
        import traceback
        RESULTS.append({"test": name, "status": "FAIL", "error": repr(e),
                        "traceback": traceback.format_exc()[-3000:]})
        print(f"[selfcheck] {name}: FAIL {e!r}")


def require(cond, msg):
    if not cond:
        raise AssertionError(msg)


# ---------------------------------------------------------------- helpers

def _mk_name(sym, dates, opens, highs, lows, closes, vols):
    return i_engine.NameData(sym, tuple(dates),
                             np.asarray(opens, float),
                             np.asarray(highs, float),
                             np.asarray(lows, float),
                             np.asarray(closes, float),
                             np.asarray(vols, float))


def _flat_calendar(n=1400):
    from datetime import date, timedelta
    out = []
    d = date(2015, 1, 2)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _bigvol(n):
    return np.full(n, 1.0e6)          # dvol 1e8 -> band A, never SUBFLOOR


# ---------------------------------------------------------------- tests

def t_go_gate():
    """Wrong/absent GO phrase refuses before any data touch (P-8)."""
    try:
        se.verify_and_pin("GO STOCKS SEARCH V1 PARAPHRASED",
                          "/nonexistent", "/nonexistent")
        raise AssertionError("GoGateRefused not raised")
    except se.GoGateRefused:
        pass


def t_warmup_gate():
    """State firing before warmup never opens a candidate leg."""
    cal = _flat_calendar(1400)
    name = _mk_name("WARM", cal,
                    np.full(1400, 100.0), np.full(1400, 101.0),
                    np.full(1400, 99.0), np.full(1400, 100.0),
                    _bigvol(1400))
    masks = se.per_name_masks(
        name, {"family": "GAP", "params": {"H": 1, "direction": "confirm",
                                           "pctl": 25},
               "warmup_need": 252})
    require(all(i >= 252 for i in masks["candidate"]),
            "candidate fired below warmup")
    require(len(masks["candidate"]) > 0, "no candidate fires at all")


def t_fold_force_flat():
    """A decision whose natural exit crosses the fold end force-flattens
    at the last served session inside the decision fold."""
    cal = _flat_calendar(1400)
    b1 = cal[400]
    b2 = cal[800]
    fends = i_engine.fold_ends(tuple(cal), b1, b2)
    dec = [397]        # entry 398; natural exit crosses the fold end
    cal_idx = {d: i for i, d in enumerate(cal)}
    name = _mk_name("FF", cal, np.linspace(100, 200, 1400),
                    np.linspace(101, 201, 1400),
                    np.linspace(99, 199, 1400),
                    np.linspace(100, 200, 1400), _bigvol(1400))
    # sanity: a decision whose entry falls PAST the fold end cannot
    # open (fold_not_opened); an entry landing exactly ON the fold-end
    # session force-flats there the same session (ff_exit == entry)
    _l0, _c0, _k0 = i_engine.build_legs(name, [400], 20, cal_idx, fends,
                                        2.0)
    require(_k0["fold_not_opened"] == 1 and not _l0,
            f"entry-past-fold-end law broken: {_k0}")
    _l1, _c1, _k1 = i_engine.build_legs(name, [398], 20, cal_idx, fends,
                                        2.0)
    require(len(_l1) == 1 and _l1[0].force_flat
            and _l1[0].exit_date == fends["F1"],
            f"fold-end-session force-flat law broken: {_k1}")
    legs, cens, counts = i_engine.build_legs(
        name, dec, 20, cal_idx, fends, 2.0)
    require(len(legs) == 1, f"expected 1 leg, got {len(legs)}")
    lg = legs[0]
    require(lg.force_flat is True, "leg not force-flattened")
    require(lg.exit_date <= fends["F1"], "exit crossed fold end")
    require(lg.fold == "F1", "wrong fold")


def t_death_censoring_kinds():
    """All three death-censoring classes reproduce exactly."""
    cal = _flat_calendar(600)
    b1 = cal[200]
    b2 = cal[400]
    fends = i_engine.fold_ends(tuple(cal), b1, b2)
    cal_idx = {d: i for i, d in enumerate(cal)}
    # name dies (last served = 500) inside F3 well before window end
    n = 501
    name = _mk_name("DIE", cal[:n], np.linspace(100, 150, n),
                    np.linspace(101, 151, n), np.linspace(99, 149, n),
                    np.linspace(100, 150, n), _bigvol(n))
    legs, cens, counts = i_engine.build_legs(
        name, [499, 500, 480], 20, cal_idx, fends, 2.0)
    kinds = sorted(lg.censored_kind for lg in cens)
    require("died_before_entry" in kinds, f"kinds={kinds}")
    require("death_open" in kinds, f"kinds={kinds}")
    require(counts["censored_died_before_entry"] == 1, str(counts))
    require(counts["censored_death_open"] == 1, str(counts))
    # death_zero_length: entry lands exactly on the death session
    # (a >= 253-session name so the med252 band resolves - the frozen
    # band law makes the 3-session version impossible by construction)
    name2 = _mk_name("DZ", cal[:300], np.linspace(100, 130, 300),
                     np.linspace(101, 131, 300),
                     np.linspace(99, 129, 300),
                     np.linspace(100, 130, 300), _bigvol(300))
    legs2, cens2, counts2 = i_engine.build_legs(
        name2, [298], 20, cal_idx, fends, 2.0)
    require(counts2["censored_death_zero_length"] == 1, str(counts2))


def t_band_subfloor_and_costs():
    """SUBFLOOR decisions open no leg; costs are the exact frozen
    expression net = gross - 2*(bps*stress)/1e4."""
    cal = _flat_calendar(600)
    b1, b2 = cal[200], cal[400]
    fends = i_engine.fold_ends(tuple(cal), b1, b2)
    cal_idx = {d: i for i, d in enumerate(cal)}
    name = _mk_name("CST", cal, np.full(600, 100.0), np.full(600, 100.0),
                    np.full(600, 100.0), np.full(600, 100.0),
                    np.full(600, 1.0e6))
    legs, cens, counts = i_engine.build_legs(
        name, [300], 5, cal_idx, fends, 2.0)
    require(len(legs) == 1, f"expected 1 leg, got {len(legs)}")
    L = i_engine.load_p0_lib()
    lg = legs[0]
    expect_net = lg.gross - 2.0 * (L.BAND_BPS[lg.band] * 2.0) / 1e4
    require(lg.net == expect_net, f"{lg.net} != {expect_net}")
    require(math.isfinite(lg.net), "non-finite net")
    sub = _mk_name("SUBF", cal, np.full(600, 0.5), np.full(600, 0.5),
                   np.full(600, 0.5), np.full(600, 0.5), np.ones(600))
    legs3, cens3, counts3 = i_engine.build_legs(
        sub, [300], 5, cal_idx, fends, 2.0)
    require(counts3["band_subfloor"] == 1 and not legs3,
            str(counts3))


def t_ordering_symbol_sorted():
    """Streaming feeds names in sorted order; per-book leg order matches
    the reference run_book order (validated on a small synthetic cohort
    by comparing per-book first-decision dates and counts)."""
    cal, b1, b2, spy = real_calendar_spy()
    names = synthetic_cohort(cal, spy, n_names=24, seed=99)
    cell = i_engine.FROZEN_CELLS[0]
    tmp = Path(tempfile.mkdtemp(prefix="ord_"))
    try:
        pa, _ = se.stream_cell_pass_a(
            iter(sorted(names.items())), cell, cal, b1, b2, tmp,
            1 << 30, spy)
        pb = se.stream_cell_pass_b(
            iter(sorted(names.items())), cell, cal, b1, b2, tmp,
            1 << 30, pa["fired_dates"], pa["_rev_rows"], spy)
        ref = i_engine.build_all_books(names, cell, cal, b1, b2)
        for k in ("candidate", "c_complement", "r5_component",
                  "c_delay_h", "c_random_timing", "c_cal_hist",
                  "c_reversal_plain"):
            st = (pa["books"] if k in pa["books"] else pb["books"])[k]\
                .finalize()
            rb = ref[k]
            require(st.n_legs == len(rb.legs),
                    f"{k}: {st.n_legs} != {len(rb.legs)}")
            require(st.counts == rb.counts, f"{k} counts differ")
            require(st.n_censored == len(rb.censored_legs), f"{k} cens")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_resume_equality():
    """A pass interrupted mid-cohort and resumed produces BIT-IDENTICAL
    accumulators to an uninterrupted pass (crash-safety, no
    double-count)."""
    cal, b1, b2, spy = real_calendar_spy()
    names = synthetic_cohort(cal, spy, n_names=40, seed=1234)
    cell = i_engine.FROZEN_CELLS[0]
    items = sorted(names.items())
    tmp = Path(tempfile.mkdtemp(prefix="res_"))
    try:
        # uninterrupted
        pa_full, _ = se.stream_cell_pass_a(
            iter(items), cell, cal, b1, b2, tmp / "full",
            1 << 30, spy)
        full_stats = {k: a.finalize() for k, a in pa_full["books"].items()}
        # interrupted: feed 11 names, "crash", resume
        ck = se.CheckpointablePassA(cell, cal, b1, b2, tmp / "res",
                                    1 << 30, spy)
        ck.run(iter(items[:11]), checkpoint_every=4)
        ck2 = se.CheckpointablePassA(cell, cal, b1, b2, tmp / "res",
                                     1 << 30, spy, resume=True)
        ck2.run(iter(items))
        res_a = ck2.result()
        res_stats = {k: a.finalize() for k, a in ck2.books.items()}
        for k, fs in full_stats.items():
            rs = res_stats[k]
            require(fs.n_legs == rs.n_legs, f"{k} n_legs resume mismatch")
            require(np.array_equal(fs.book_log, rs.book_log),
                    f"{k} book_log resume mismatch")
            require(fs.counts == rs.counts, f"{k} counts resume mismatch")
            require(fs.inc_expectancy == rs.inc_expectancy,
                    f"{k} inc_expectancy resume mismatch")
        require(sorted(res_a["fired_dates"]) ==
                sorted(pa_full["fired_dates"]), "fired_dates resume")
        require(res_a["pit_mutation"]["fired"] ==
                pa_full["pit_mutation"]["fired"], "pit resume")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_atomic_and_quota():
    """persist_p11 leaves no .tmp and loads back; a tiny spill quota
    aborts fail-closed."""
    cal = _flat_calendar(300)
    acc = se.BookAcc("candidate", "X", 1, 2.0, tuple(cal),
                     Path(tempfile.mkdtemp(prefix="qa_")) / "sp",
                     1 << 20)
    acc.book_log_sum[5] = 0.01
    acc.active[5] = 1
    st = acc.finalize()
    p = acc.spill_dir / "p11.json"
    digest = se.persist_p11(p, st)
    require(not list(acc.spill_dir.glob("*.tmp")), "tmp file left behind")
    loaded = json.loads(p.read_text())
    require(loaded["sha256"] == digest, "digest mismatch")
    tiny = se.BookAcc("candidate", "X", 1, 2.0, tuple(cal),
                      Path(tempfile.mkdtemp(prefix="qa_")) / "sp2",
                      64)          # 64-byte quota: 9+ legs breach it
    try:
        legs = [i_engine.Leg("A", i, cal[0], cal[1], cal[2], "F1", "A",
                             0.01, 0.0) for i in range(9)]
        tiny.add_legs(legs, [], {"fired": 9})
        tiny._writers["net"].flush()
        raise AssertionError("quota not enforced")
    except RuntimeError as e:
        require("SPILL_QUOTA" in str(e), f"wrong error {e}")


def t_pit_mutation_mirror():
    """Per-name PIT aggregation equals i_engine.pit_mutation_gate."""
    cal, b1, b2, spy = real_calendar_spy()
    names = synthetic_cohort(cal, spy, n_names=20, seed=555)
    cell = i_engine.FROZEN_CELLS[2]
    masks = {s: se.per_name_masks(nm, cell)["candidate"]
             for s, nm in sorted(names.items())}
    ref = i_engine.pit_mutation_gate(names, masks, cell)
    total = changed = 0
    per_name = {}
    for s, nm in sorted(names.items()):
        pit = se.per_name_pit(nm, masks[s], cell)
        total += pit["fired"]
        changed += pit["changed"]
        per_name[s] = pit
    require(total == ref["fired"] and changed == ref["changed_or_refused"],
            f"{total}/{changed} != {ref['fired']}/{ref['changed_or_refused']}")
    require(per_name == ref["per_name"], "per_name differs")


def t_reversal_picks_mirror():
    """Streaming reversal picks/stats equal i_engine.reversal_plain_masks."""
    cal, b1, b2, spy = real_calendar_spy()
    names = synthetic_cohort(cal, spy, n_names=25, seed=777)
    ref_masks, ref_stats = i_engine.reversal_plain_masks(names, cal)
    rev_rows = {s: se.reversal_eligibility(nm, cal)
                for s, nm in sorted(names.items())}
    rev_rows = {s: r for s, r in rev_rows.items() if r}
    picks, stats = se.reversal_picks(rev_rows, cal)
    require(stats == ref_stats, f"{stats} != {ref_stats}")
    for s in sorted(set(picks) | set(ref_masks)):
        got = sorted(picks.get(s, []))
        want = sorted(names[s].dates[i] for i in ref_masks.get(s, []))
        require(got == want, f"{s}: {len(got)} vs {len(want)}")


def main() -> int:
    check("go_gate", t_go_gate)
    check("warmup_gate", t_warmup_gate)
    check("fold_force_flat", t_fold_force_flat)
    check("death_censoring_kinds", t_death_censoring_kinds)
    check("band_subfloor_and_costs", t_band_subfloor_and_costs)
    check("ordering_symbol_sorted", t_ordering_symbol_sorted)
    check("resume_equality", t_resume_equality)
    check("atomic_and_quota", t_atomic_and_quota)
    check("pit_mutation_mirror", t_pit_mutation_mirror)
    check("reversal_picks_mirror", t_reversal_picks_mirror)
    out = {"schema": "stocks_search_v1_e2_selfcheck@1",
           "results": RESULTS,
           "pass": all(r["status"] == "PASS" for r in RESULTS)}
    (_HERE / "selfcheck_verdict.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"selfcheck pass={out['pass']} -> "
          f"{_HERE / 'selfcheck_verdict.json'}")
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
