"""STOCKS-SEARCH-V1 E2-lane equivalence runner (reference vs streaming).

THE pre-scoring verification gate of the streaming remediation:

  1. MIRROR-ONLY check - the adjudication mirror
     (i_stream_engine.adjudicate_candidate_stream) is run on BookStats
     built DIRECTLY from the reference engine's in-RAM BookResult
     objects.  This isolates mirror defects from streaming defects.
  2. FULL-STREAMING check - the streaming engine (pass A + pass B +
     finalize) runs the same fixture cohort; its BookStats and its
     mirrored verdict are compared against the reference
     i_engine.build_all_books + adjudicate.adjudicate_candidate outputs.
  3. DETERMINISM check - two independent streaming runs must produce
     bit-identical book_log/series sha and verdict canonical JSON.

Comparison law (preregistered): BYTE/BIT EQUALITY is the primary gate
(bitwise compare of every float array; canonical-JSON equality of every
verdict).  A preregistered fallback tolerance |delta| <= 1e-12 relative
on aggregate scalars exists ONLY as a disclosed TOLERANCE_PASS - it never
silently replaces a bitwise failure, and hitting it at all is reported to
A7 as a finding to adjudicate.

Fixtures:
  * synthetic cohort - deterministic seeded generator over the REAL
    SPY-pinned calendar and REAL fold boundaries (exercises warmup
    boundaries, fold force-flat, all three death-censoring kinds, band
    subfloor, SUBFLOOR/A/B/C dollar-volume mixes, gap/tercile/52w state
    machinery on all three frozen families);
  * real-subset cohort (engineering verification, NOT scored evidence) -
    SPY + the first K status-200 cohort names, deterministic.  The
    artifact stores ONLY equality booleans and sha256 digests - no
    performance numbers are persisted (no expectancy/PF/PnL of any real
    subset is ever written).

This module NEVER touches the scored GO gate and never streams the full
real cohort (max_names bounds every real parse).
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_RUN_DIR = _HERE.parent
_I_DIR = _RUN_DIR / "i"
_E2_DIR = _HERE
for _p in (str(_I_DIR), str(_E2_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import i_engine          # frozen reference engine (READ-ONLY)
import adjudicate        # frozen reference adjudication (READ-ONLY)
import i_stream_engine as se

P0_DIR = _RUN_DIR / "p0"
CACHE_DIR = P0_DIR / "raw" / "eod_cache"
S_FREEZE_PATH = _RUN_DIR / "s" / "selection_freeze.json"
QUOTA_BYTES = int(6.0 * 1024 ** 3)
TOL_REL = 1e-12


# --------------------------------------------------------------- fixtures

def real_calendar_spy() -> tuple:
    """REAL SPY-pinned S0 calendar + fold boundaries + SPY NameData."""
    freeze = json.loads(S_FREEZE_PATH.read_text())
    cal, _sha = i_engine._build_calendar_from_cache(
        CACHE_DIR, freeze["s0_window"]["start"], freeze["s0_window"]["end"])
    b1 = freeze["folds"]["boundaries"]["B1"]
    b2 = freeze["folds"]["boundaries"]["B2"]
    # SPY via the FROZEN pinned parser (same construction as
    # load_real_data), then clipped to the S0 window (the reference
    # names dict holds full served histories; the calendar is the
    # in-window SPY date set - the fixture keeps SPY full-history so
    # books see the same object the real path provides).
    p0_run = i_engine._load_pinned_p0_run(
        freeze["data_manifests_sha256"]["p0_run.py"])
    parsed = p0_run.parse_name(CACHE_DIR / "SPY.json.gz")
    dates, o, h, lo, c, v, _mal = parsed
    spy = i_engine.NameData(
        "SPY", tuple(d[:10] for d in dates),
        np.asarray(o, dtype=float), np.asarray(h, dtype=float),
        np.asarray(lo, dtype=float), np.asarray(c, dtype=float),
        np.asarray(v, dtype=float))
    return cal, b1, b2, spy


def synthetic_cohort(calendar, spy, n_names: int = 140,
                     seed: int = 20260921) -> dict:
    """Deterministic synthetic cohort over the real calendar/folds.

    Edge-case coverage is INTENTIONAL and labelled: warmup-short names,
    subfloor dollar-volume names, names dying at each fold boundary,
    names dying mid-fold (death_open), names with entry-past-end
    (died_before_entry), zero-length death legs, overnight-gap structure
    on both sides of the percentile, vol-tercile clustering, 52w-high
    proximity structure.
    """
    rng = np.random.default_rng(seed)
    cal = list(calendar)
    ncal = len(cal)
    names = {"SPY": spy}
    kinds = (
        ["full"] * max(1, n_names // 2)
        + ["die_F1"] * 3 + ["die_F2"] * 3 + ["die_F3_edge"] * 3
        + ["die_mid"] * 4 + ["die_before_entry"] * 2
        + ["zero_length"] * 2 + ["short"] * 5 + ["subfloor"] * 5
        + ["zero_range"] * 2)
    kinds = (kinds * (n_names // len(kinds) + 1))[:n_names]
    fold_ends = i_engine.fold_ends(tuple(cal), *(
        json.loads(S_FREEZE_PATH.read_text())["folds"]["boundaries"]
        [k] for k in ("B1", "B2")))
    for i, kind in enumerate(kinds):
        sym = f"SYN{i:04d}_{kind}"
        if kind == "short":
            n = int(rng.integers(5, 251))
            start = int(rng.integers(0, max(1, ncal - n)))
        else:
            n = int(rng.integers(300, ncal))
            start = int(rng.integers(0, max(1, ncal - n)))
        end = start + n
        if kind.startswith("die_F"):
            end = min(end, cal.index(fold_ends["F1" if kind == "die_F1"
                                                else "F2"]) + 1
                      if kind != "die_F3_edge" else ncal)
        dates = tuple(cal[start:end])
        if not dates:
            continue
        m = len(dates)
        # random-walk close with regime structure
        drift = float(rng.normal(0, 0.0005))
        vol = float(rng.uniform(0.005, 0.05))
        shocks = rng.normal(0.0, 1.0, m)
        if kind == "zero_range":                 # long flat stretches
            shocks = np.zeros(m)
        logc = np.cumsum(drift + vol * shocks)
        close = 100.0 * np.exp(logc)
        # overnight gaps: explicit fat gaps so both percentile sides fire
        opens = np.empty(m)
        opens[0] = close[0]
        gsign = rng.choice([-1.0, 1.0], size=m)
        gmag = np.where(rng.random(m) < 0.12,
                        rng.uniform(0.005, 0.06, m), rng.uniform(0, 0.004, m))
        opens[1:] = close[:-1] * (1.0 + gsign[1:] * gmag[1:])
        high = np.maximum(opens, close) * (1.0 + np.abs(
            rng.normal(0, 0.004, m)))
        low = np.minimum(opens, close) * (1.0 - np.abs(
            rng.normal(0, 0.004, m)))
        if kind == "zero_range":
            high = np.maximum(opens, close)
            low = np.minimum(opens, close)
        if kind == "subfloor":
            volume = np.full(m, 5.0)             # dvol ~ sub-floor
        else:
            volume = np.exp(rng.uniform(9.0, 16.5, m))
        nd = i_engine.NameData(sym, dates,
                               opens, high, low, close, volume)
        names[sym] = nd
    return names


def real_subset_cohort(k: int = 40) -> dict:
    """SPY + the first K status-200 cohort names (deterministic prefix).

    Engineering verification only: bounded, deterministic, and never
    persisted with performance numbers.
    """
    freeze = json.loads(S_FREEZE_PATH.read_text())
    p0_run = i_engine._load_pinned_p0_run(
        freeze["data_manifests_sha256"]["p0_run.py"])
    retrieval = json.loads(
        i_engine.COMMITTED_RETRIEVAL_MANIFEST_PATH.read_text())
    pulls = retrieval["pulls"]
    syms = ["SPY"] + [s for s in sorted(
        s for s, m in pulls.items() if m.get("status") == 200)
        if s != "SPY"][:k]
    names = {}
    for sym in syms:
        parsed = p0_run.parse_name(CACHE_DIR / f"{sym}.json.gz")
        if parsed is None:
            continue
        dates, o, h, lo, c, v, _mal = parsed
        names[sym] = i_engine.NameData(
            sym, tuple(d[:10] for d in dates),
            np.asarray(o, dtype=float), np.asarray(h, dtype=float),
            np.asarray(lo, dtype=float), np.asarray(c, dtype=float),
            np.asarray(v, dtype=float))
    return names


# --------------------------------------------------- reference vs stream

def stats_from_reference_book(book, spy, calendar) -> se.BookStats:
    """BookStats built DIRECTLY from a reference BookResult (mirror-only
    check: validates the adjudication mirror without streaming)."""
    nets = np.asarray([lg.net for lg in book.legs], dtype=np.float64)
    folds = np.asarray([se.FOLD_CODE[lg.fold] for lg in book.legs],
                       dtype=np.int8)
    gross = np.asarray([lg.gross for lg in book.legs], dtype=np.float64)
    bands = np.asarray([{"A": 0, "B": 1, "C": 2}[lg.band]
                        for lg in book.legs], dtype=np.int8)
    spy_legs = np.asarray(i_engine.spy_legs_for(spy, book.legs),
                          dtype=np.float64) if spy is not None else None
    inc = i_engine.include_censored_nets(book)
    inc_nets = np.asarray([lg.net for lg in inc.legs], dtype=np.float64)
    inc_folds = np.asarray([se.FOLD_CODE[lg.fold] for lg in inc.legs],
                           dtype=np.int8)
    inc_spy = np.asarray(i_engine.spy_legs_for(spy, inc.legs),
                         dtype=np.float64) if spy is not None else None
    return se.BookStats(
        book_id=book.book_id, config_id=book.config_id, H=book.H,
        stress=book.stress, calendar=tuple(calendar),
        expectancy=book.expectancy,
        fold_expectancy=dict(book.fold_expectancy),
        fold_leg_counts=dict(book.fold_leg_counts),
        n_legs=len(book.legs), n_censored=len(book.censored_legs),
        censored_kinds=sorted({lg.censored_kind for lg in
                               book.censored_legs if lg.censored_kind}),
        counts=dict(book.counts), book_log=book.book_log,
        gross=gross, band_codes=bands, spy=spy_legs,
        nets=nets, folds=folds,
        inc_expectancy=inc.expectancy,
        inc_fold_expectancy=dict(inc.fold_expectancy),
        inc_nets=inc_nets, inc_folds=inc_folds, inc_spy=inc_spy)


def run_reference(names: dict, cell: dict, calendar, b1, b2, spy):
    bundle = i_engine.build_all_books(names, cell, calendar, b1, b2,
                                      i_engine.STRESS_TIER)
    report = adjudicate.adjudicate_candidate(bundle, spy, calendar, b1, b2)
    return bundle, report


def run_streaming(names: dict, cell: dict, calendar, b1, b2, spy,
                  spill_dir: Path):
    spill_dir = Path(spill_dir)
    pa, _st = se.stream_cell_pass_a(
        iter(sorted(names.items())), cell, calendar, b1, b2, spill_dir,
        QUOTA_BYTES, spy)
    pb = se.stream_cell_pass_b(
        iter(sorted(names.items())), cell, calendar, b1, b2, spill_dir,
        QUOTA_BYTES, pa["fired_dates"], pa["_rev_rows"], spy)
    stats = {k: acc.finalize() for k, acc in pa["books"].items()}
    stats.update({k: acc.finalize() for k, acc in pb["books"].items()})
    bundle = {
        "cell": cell["config_id"],
        "H": int(cell["params"]["H"]),
        "stress": i_engine.STRESS_TIER,
        "candidate": stats["candidate"],
        "c_complement": stats["c_complement"],
        "r5_component": stats["r5_component"],
        "c_delay_h": stats["c_delay_h"],
        "c_random_timing": stats["c_random_timing"],
        "c_cal_hist": stats["c_cal_hist"],
        "c_reversal_plain": stats["c_reversal_plain"],
        "pit_mutation": pa["pit_mutation"],
        "c_cal_hist_report": pb["c_cal_hist_report"],
        "reversal_stats": pb["reversal_stats"],
        "counts_cohort": pb["counts_cohort"],
    }
    report = se.adjudicate_candidate_stream(bundle, spy, calendar, b1, b2)
    return bundle, report


# ------------------------------------------------------------- comparison

def _bits(x) -> str:
    if isinstance(x, np.ndarray):
        return hashlib.sha256(np.ascontiguousarray(x).tobytes())\
            .hexdigest()
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=str)
                          .encode()).hexdigest()


def _close(a: float, b: float) -> bool:
    if a != a and b != b:
        return True
    if a != a or b != b:
        return False
    return abs(a - b) <= TOL_REL * max(1.0, abs(a), abs(b))


def compare(names: dict, cell: dict, calendar, b1, b2, spy,
            spill_root: Path, label: str) -> dict:
    """Full three-part comparison for one cell.  Returns the verdict row."""
    ref_bundle, ref_report = run_reference(names, cell, calendar, b1, b2,
                                           spy)
    checks = {}

    # 1. mirror-only: reference books -> stats -> mirror adjudication
    mirror_bundle = {
        "cell": cell["config_id"], "H": int(cell["params"]["H"]),
        "stress": i_engine.STRESS_TIER,
        "pit_mutation": ref_bundle["pit_mutation"],
        "c_cal_hist_report": ref_bundle["c_cal_hist_report"],
        "reversal_stats": ref_bundle["reversal_stats"],
        "counts_cohort": ref_bundle["counts_cohort"],
    }
    for k in ("candidate", "c_complement", "r5_component", "c_delay_h",
              "c_random_timing", "c_cal_hist", "c_reversal_plain"):
        mirror_bundle[k] = stats_from_reference_book(
            ref_bundle[k], spy, calendar)
    mirror_report = se.adjudicate_candidate_stream(mirror_bundle, spy,
                                                   calendar, b1, b2)
    checks["mirror_verdict_json_equal"] = (
        _bits(_canon(mirror_report)) == _bits(_canon(ref_report)))

    # 2. full streaming vs reference
    st_bundle, st_report = run_streaming(
        names, cell, calendar, b1, b2, spy,
        spill_root / f"{label}_{cell['config_id']}")
    checks["stream_verdict_json_equal"] = (
        _bits(_canon(st_report)) == _bits(_canon(ref_report)))
    per_book = {}
    ref_spy_legs = i_engine.spy_legs_for(
        spy, ref_bundle["candidate"].legs) if spy is not None else []
    for k in ("candidate", "c_complement", "r5_component", "c_delay_h",
              "c_random_timing", "c_cal_hist", "c_reversal_plain"):
        rb = ref_bundle[k]
        sb = st_bundle[k]
        row = {
            "n_legs": len(rb.legs) == sb.n_legs,
            "n_censored": len(rb.censored_legs) == sb.n_censored,
            "counts": rb.counts == sb.counts,
            "expectancy_bits": (
                float(rb.expectancy) == sb.expectancy),
            "fold_expectancy_bits": (
                {k2: float(v) for k2, v in rb.fold_expectancy.items()}
                == {k2: float(v)
                    for k2, v in sb.fold_expectancy.items()}),
            "book_log_bits": _bits(rb.book_log) == _bits(sb.book_log),
            "series_sha_equal": rb.series_sha256() == sb.series_sha256(),
        }
        inc = i_engine.include_censored_nets(rb)
        row["inc_expectancy_bits"] = (
            float(inc.expectancy) == sb.inc_expectancy)
        row["inc_fold_expectancy_bits"] = (
            {k2: float(v) for k2, v in inc.fold_expectancy.items()}
            == {k2: float(v)
                for k2, v in sb.inc_fold_expectancy.items()})
        per_book[k] = row
    checks["books_bit_equal"] = all(all(r.values()) for r in
                                    per_book.values())
    checks["spy_legs_bits"] = _bits(
        np.asarray(ref_spy_legs, dtype=float)) == _bits(
        st_bundle["candidate"].spy if
        st_bundle["candidate"].spy is not None else np.zeros(0))
    checks["pit_mutation_json_equal"] = _bits(
        _canon(ref_bundle["pit_mutation"])) == _bits(
        _canon(st_bundle["pit_mutation"]))
    checks["cal_hist_report_equal"] = (
        ref_bundle["c_cal_hist_report"] == st_bundle["c_cal_hist_report"])
    checks["reversal_stats_equal"] = (
        ref_bundle["reversal_stats"] == st_bundle["reversal_stats"])
    checks["counts_cohort_equal"] = (
        ref_bundle["counts_cohort"] == st_bundle["counts_cohort"])

    # 3. determinism: second independent streaming run
    st_bundle2, st_report2 = run_streaming(
        names, cell, calendar, b1, b2, spy,
        spill_root / f"{label}_det_{cell['config_id']}")
    checks["determinism_verdict_json_equal"] = (
        _bits(_canon(st_report)) == _bits(_canon(st_report2)))
    checks["determinism_series_sha_equal"] = (
        st_bundle["candidate"].series_sha256()
        == st_bundle2["candidate"].series_sha256())

    for b in (st_bundle, st_bundle2, mirror_bundle):
        for v in b.values():
            if isinstance(v, se.BookStats):
                v.free_arrays()

    ok = all(bool(v) for v in checks.values())
    return {"label": label, "config_id": cell["config_id"],
            "checks": {k: bool(v) for k, v in checks.items()},
            "books": per_book, "pass": ok}


def _canon(obj):
    return json.dumps(obj, sort_keys=True, default=str, allow_nan=True)


# ----------------------------------------------------------------- main

def main() -> int:
    out = {"schema": "stocks_search_v1_e2_equivalence@1",
           "tolerance_preregistered": {"relative": TOL_REL,
                                       "role": "disclosed fallback only; "
                                               "primary gate is bitwise"},
           "runs": []}
    cal, b1, b2, spy = real_calendar_spy()
    spill_root = _E2_DIR / "fixtures_spill"
    modes = []
    if "--synthetic" in sys.argv or len(sys.argv) == 1:
        modes.append(("synthetic", synthetic_cohort(cal, spy), True))
    if "--real-subset" in sys.argv:
        k = 40
        for a in sys.argv:
            if a.startswith("--k="):
                k = int(a.split("=")[1])
        modes.append((f"real_subset_k{k}", real_subset_cohort(k), False))
    all_pass = True
    for label, names, persist_numbers in modes:
        for cell in i_engine.FROZEN_CELLS:
            row = compare(names, cell, cal, b1, b2, spy, spill_root, label)
            if not persist_numbers:
                # digest-only persistence: no performance numbers for the
                # real-subset engineering check
                row = {"label": row["label"],
                       "config_id": row["config_id"],
                       "pass": row["pass"],
                       "checks": row["checks"],
                       "books": {k: {kk: vv for kk, vv in v.items()}
                                 for k, v in row["books"].items()}}
            out["runs"].append(row)
            all_pass = all_pass and row["pass"]
            print(f"[equivalence] {label} {cell['config_id']}: "
                  f"{'PASS' if row['pass'] else 'FAIL'}")
    out["pass"] = all_pass
    dest_name = "equivalence_verdict.json"
    for a in sys.argv:
        if a.startswith("--out="):
            dest_name = a.split("=", 1)[1]
    dest = _E2_DIR / dest_name
    dest.write_text(json.dumps(out, indent=1, sort_keys=True,
                               default=str) + "\n")
    print(f"verdict -> {dest} pass={all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
