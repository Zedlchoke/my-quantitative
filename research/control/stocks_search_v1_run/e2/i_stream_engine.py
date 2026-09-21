"""STOCKS-SEARCH-V1 E2-lane STREAMING scored engine (owner remediation
decision (a): streaming/out-of-core E-engine + fresh GO, 2026-09-21).

Remediation contract (owner instruction, frozen):
  - The frozen experiment is UNCHANGED: universe, folds, clock, costs,
    configurations, controls, selection, thresholds, data, cost model and
    the 3 selected cells are byte-identical to the S freeze.  No S1.  No
    scored PnL is consulted for any implementation decision.
  - The memory defect class ENGINE_RESOURCE_INFEASIBILITY_ON_REAL_DATA
    (measured frozen-path peak floor 28.37 GiB >> 6 GiB safe budget on the
    8 GiB host; e/e_run_verdict.json) is remediated by replacing the
    load-everything materialization with a per-name streaming pass:
      * cohort parsed one name at a time (peak RAM ~ one NameData);
      * per-leg records appended to on-disk spill files (out-of-core);
      * P-11 book_log accumulated per calendar cell in exact leg order;
      * adjudication consumes streaming aggregates, no deepcopy of books.
  - SCIENTIFIC EQUIVALENCE, the load-bearing design law: every scalar the
    frozen path produced is reproduced with IDENTICAL floating-point
    semantics and IDENTICAL summation order:
      * i_engine.build_legs is reused UNMODIFIED per name (same math.log,
        same fills, same costs, same censoring);
      * state/complement/r5 masks reuse the frozen i_engine functions;
      * np.mean over spilled float64 arrays reproduces the reference
        np.mean over the same values in the same order (pairwise sum);
      * statistics.stdev over per-fold masked arrays reproduces the
        reference per-fold lists;
      * _finalize's series[ci] += slice additions happen in identical leg
        order (names sorted, decisions sorted).
    Equivalence is verified against the reference engine on fixtures
    (e2/equivalence.py): byte-equal canonical verdicts and bit-equal
    series; preregistered fallback tolerance |delta| <= 1e-12 (relative)
    on aggregates, disclosed if ever hit.
  - This module contains NO scored-run orchestration and NO GO bypass:
    the real-cohort iterator demands the exact owner GO phrase exactly as
    adjudicate.load_real_data does (P-8).  Fixtures/selfchecks are
    synthetic or explicitly-labelled bounded real subsets that never
    produce persisted performance numbers.

Lane discipline: allowed write root is research/control/
stocks_search_v1_run/e2/.  The frozen chain (i/, e/, s/, d1/, p0/, m0/,
z/, audits/) is READ-ONLY.  No push/merge/rebase.  No registry/ledger
writes from the lane.
"""

from __future__ import annotations

import gc
import json
import math
import os
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent          # .../stocks_search_v1_run/e2
_RUN_DIR = _HERE.parent
_I_DIR = _RUN_DIR / "i"
if str(_I_DIR) not in sys.path:
    sys.path.insert(0, str(_I_DIR))

import i_engine  # noqa: E402  (frozen, READ-ONLY reuse)
from i_engine import (  # noqa: E402
    NameData,
    REVERSAL_PLAIN_H,
    REVERSAL_PLAIN_PERIOD,
    STRESS_TIER,
    complement_fired_mask,
    r5_component_fired_mask,
    state_fired_mask,
    _warmup_gate,
    nm_dates_index,
    random_timing_decisions,
    cal_hist_twin_dates,
    spy_legs_for,
    canon_sha256,
    load_p0_lib,
)

FOLDS = ("F1", "F2", "F3")
FOLD_CODE = {"F1": 0, "F2": 1, "F3": 2}
KIND_CODE = {"died_before_entry": 0, "death_zero_length": 1, "death_open": 2}
KIND_NAME = {v: k for k, v in KIND_CODE.items()}


# ============================================================ GO-gated loader

class GoGateRefused(RuntimeError):
    """The exact owner GO phrase was not presented (P-8)."""


def verify_and_pin(go_phrase: str, cache_dir, retrieval_manifest_path) -> dict:
    """GO gate + freeze verify + p0_lib pin + data-plane preflight.

    Returns the pinned loader context for stream_iter_names.  Mirrors
    adjudicate.load_real_data's pre-load checks exactly (same checks, in
    the same order, with the same fail-closed exceptions).
    """
    if go_phrase != i_engine.GO_PHRASE:
        raise GoGateRefused(
            "GO gate: the exact phrase 'GO STOCKS SEARCH V1 SCORED "
            "EXECUTION' was not presented; early or paraphrased GO dies "
            "unconsumed (P-8). No data is streamed.")
    i_engine.verify_freeze()
    i_engine.load_p0_lib()
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        raise FileNotFoundError(f"raw cache dir not found: {cache_dir}")
    preflight = i_engine.verify_data_plane(cache_dir, retrieval_manifest_path)
    freeze = json.loads(i_engine._S_FREEZE_PATH.read_text())
    p0_run = i_engine._load_pinned_p0_run(
        freeze["data_manifests_sha256"]["p0_run.py"])
    retrieval = json.loads(
        i_engine.COMMITTED_RETRIEVAL_MANIFEST_PATH.read_text())
    import gzip
    cohort = json.loads(gzip.open(
        i_engine.COMMITTED_COHORT_CENSUS_PATH, "rt").read())
    return {"preflight": preflight, "p0_run": p0_run,
            "retrieval": retrieval,
            "cohort_served": {k: int(v.get("served", 0))
                              for k, v in cohort.items()},
            "go_phrase_state": "CONSUMED_AT_GATE (exact phrase presented)"}


def stream_iter_names(ctx: dict, cache_dir, max_names: int | None = None):
    """Yield (symbol, NameData) one at a time, sorted, GO-gated ctx.

    RESUME LAW (E2F-1 remediation): this iterator has NO skip parameter.
    Crash-resume skipping is owned EXCLUSIVELY by CheckpointablePassA/B
    (their names_done counters drop already-fed names) - a second skip
    layer here would silently double-skip names.  Callers pass the FULL
    iterator; the checkpointable pass consumes its own offset."""
    p0_run = ctx["p0_run"]
    retrieval = ctx["retrieval"]
    pulls = retrieval["pulls"]
    cache_dir = Path(cache_dir)
    n = 0
    for sym in sorted(s for s, m in pulls.items() if m.get("status") == 200):
        parsed = p0_run.parse_name(cache_dir / f"{sym}.json.gz")
        if parsed is None:
            continue
        dates, o, h, lo, c, v, _mal = parsed
        nd = NameData(sym, tuple(d[:10] for d in dates),
                      np.asarray(o, dtype=float),
                      np.asarray(h, dtype=float),
                      np.asarray(lo, dtype=float),
                      np.asarray(c, dtype=float),
                      np.asarray(v, dtype=float))
        n += 1
        yield sym, nd
        del parsed, nd
        if max_names is not None and n >= max_names:
            return


# ============================================================ spill plumbing

class SpillWriter:
    """Append-only fixed-record binary spill with flush/fsync and quota.

    Records are struct-free: callers append numpy scalars via typed
    array.tobytes().  Crash-safe resume is by record count (each writer
    tracks n_records; checkpoint stores it; reopen truncates to the
    checkpointed count before appending).
    """

    def __init__(self, path: Path, dtype, quota_bytes: int,
                 resume_records: int | None = None):
        self.path = Path(path)
        self.dtype = np.dtype(dtype)
        self.itemsize = self.dtype.itemsize
        self.quota_bytes = int(quota_bytes)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if resume_records is None:
            self.n = 0
            self._fh = open(self.path, "wb")
        else:
            self.n = int(resume_records)
            self._fh = open(self.path, "r+b")
            self._fh.truncate(self.n * self.itemsize)
            self._fh.seek(0, os.SEEK_END)
        self._buf = []

    def append_many(self, values) -> None:
        arr = np.asarray(values, dtype=self.dtype)
        self._buf.append(arr.tobytes())
        self.n += int(arr.shape[0])
        if len(self._buf) >= 64:
            self.flush()

    def flush(self) -> None:
        if self._buf:
            self._fh.write(b"".join(self._buf))
            self._buf = []
        self._fh.flush()
        os.fsync(self._fh.fileno())
        used = self.n * self.itemsize
        if used > self.quota_bytes:
            raise RuntimeError(
                f"SPILL_QUOTA_EXCEEDED {self.path.name}: {used} > "
                f"{self.quota_bytes} (fail-closed TECHABORT direction)")

    def read_all(self) -> np.ndarray:
        self.flush()
        self._fh.seek(0)
        data = np.fromfile(self.path, dtype=self.dtype)
        return data

    def close(self) -> None:
        self.flush()
        self._fh.close()


def read_spill(path: Path, dtype) -> np.ndarray:
    return np.fromfile(Path(path), dtype=np.dtype(dtype))


# ============================================================ accumulators

@dataclass
class BookAcc:
    """Streaming accumulator for one book (candidate or control).

    Per-leg scalars spill to disk in exact leg order; book_log is
    accumulated in RAM in the same order i_engine._finalize would add
    slices after the fact, so the float addition order per calendar cell
    is identical.  Censored death_open legs spill (fold, net_at_marks,
    entry_yyyymmdd, exit_yyyymmdd) for the BC-7 included variant and its
    spy pairing.
    """
    book_id: str
    config_id: str
    H: int
    stress: float
    calendar: tuple
    spill_dir: Path
    quota_bytes: int
    keep_spy: bool = False
    resume_records: dict | None = None
    resume_gen: int = 0
    # RAM accumulators
    counts: dict = field(default_factory=dict)
    n_censored: int = 0
    censored_kinds: set = field(default_factory=set)
    book_log_sum: np.ndarray = None      # float64[ncal]
    active: np.ndarray = None            # int64[ncal]
    # spill state
    _writers: dict = field(default_factory=dict, repr=False)

    def writer_counts(self) -> dict:
        return {k: w.n for k, w in self._writers.items()}

    def record_counts(self) -> dict:
        return {k: int(w.n) for k, w in self._writers.items()}

    def __post_init__(self):
        ncal = len(self.calendar)
        self.book_log_sum = np.zeros(ncal, dtype=np.float64)
        self.active = np.zeros(ncal, dtype=np.int64)
        rr = getattr(self, "resume_records", None) or {}
        self._writers = {
            "net": SpillWriter(self.spill_dir / f"{self.book_id}__net.f64",
                               np.float64, self.quota_bytes,
                               resume_records=rr.get("net")),
            "fold": SpillWriter(self.spill_dir / f"{self.book_id}__fold.i8",
                                np.int8, self.quota_bytes,
                                resume_records=rr.get("fold")),
        }
        if self.keep_spy:
            self._writers["gross"] = SpillWriter(
                self.spill_dir / f"{self.book_id}__gross.f64",
                np.float64, self.quota_bytes,
                resume_records=rr.get("gross"))
            self._writers["band"] = SpillWriter(
                self.spill_dir / f"{self.book_id}__band.i8",
                np.int8, self.quota_bytes,
                resume_records=rr.get("band"))
            self._writers["spy"] = SpillWriter(
                self.spill_dir / f"{self.book_id}__spy.f64",
                np.float64, self.quota_bytes,
                resume_records=rr.get("spy"))
        self._writers["cens"] = SpillWriter(
            self.spill_dir / f"{self.book_id}__cens_death_open.f64",
            np.float64, self.quota_bytes,
            resume_records=rr.get("cens"))   # fold,net,entry,exit quads
        if rr:
            gen = int(getattr(self, "resume_gen", 0))
            z = np.load(self.spill_dir /
                        f"{self.book_id}__accum_gen{gen}.npz")
            self.book_log_sum = z["book_log_sum"].copy()
            self.active = z["active"].copy()
            self.counts = {k: int(v) for k, v in
                           json.loads(z["counts_json"].item()).items()}
            self.n_censored = int(z["n_censored"])
            self.censored_kinds = set(json.loads(
                z["censored_kinds_json"].item()))

    def save_checkpoint(self, gen: int = 0) -> None:
        """Generation-numbered atomic snapshot.

        Transaction law: the accumulator snapshot for generation g is
        fully written+renamed BEFORE the pass checkpoint names g; a crash
        between generations therefore always resumes from a CONSISTENT
        (spill record counts, accumulators) pair named by the last
        committed checkpoint generation - a mid-write crash can never
        double-count a name into book_log."""
        for w in self._writers.values():
            w.flush()
        dst = self.spill_dir / f"{self.book_id}__accum_gen{int(gen)}.npz"
        tmp = self.spill_dir / (dst.name + ".tmp")
        with open(tmp, "wb") as f:
            np.savez(f, book_log_sum=self.book_log_sum,
                     active=self.active,
                     counts_json=json.dumps(self.counts, sort_keys=True),
                     n_censored=self.n_censored,
                     censored_kinds_json=json.dumps(
                         sorted(self.censored_kinds)))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, dst)
        # keep only the two newest generations
        gens = sorted(int(f.name.split("gen")[-1].split(".")[0])
                      for f in self.spill_dir.glob(
                          f"{self.book_id}__accum_gen*.npz"))
        for old in gens[:-2]:
            (self.spill_dir /
             f"{self.book_id}__accum_gen{old}.npz").unlink(missing_ok=True)

    # ------------------------------------------------------------ feeding

    def add_legs(self, legs, censored, counts) -> None:
        """Feed one name's build_legs output, in the frozen order."""
        for k, v in counts.items():
            self.counts[k] = self.counts.get(k, 0) + v
        nets, folds, grosss, bands, spys = [], [], [], [], []
        for lg in legs:
            nets.append(lg.net)
            folds.append(FOLD_CODE[lg.fold])
            if self.keep_spy:
                grosss.append(lg.gross)
                bands.append({"A": 0, "B": 1, "C": 2}[lg.band])
                spys.append(_spy_leg_value(lg.entry_date, lg.exit_date))
            # P-11 accumulation in _finalize's exact order
            if lg.log_slices:
                for ci, val in lg.log_slices:
                    self.book_log_sum[ci] += val
                    self.active[ci] += 1
        self._writers["net"].append_many(nets)
        self._writers["fold"].append_many(folds)
        if self.keep_spy:
            self._writers["gross"].append_many(grosss)
            self._writers["band"].append_many(bands)
            self._writers["spy"].append_many(spys)
        sext = []
        for lg in censored:
            self.n_censored += 1
            if lg.censored_kind:
                self.censored_kinds.add(lg.censored_kind)
            if lg.censored_kind != "death_open":
                continue
            L = load_p0_lib()
            net = lg.gross - 2.0 * (L.BAND_BPS[lg.band] * self.stress) / 1e4
            sext.extend((FOLD_CODE[lg.fold], net,
                         int(lg.entry_date.replace("-", "")),
                         int(lg.exit_date.replace("-", "")),
                         lg.gross,
                         {"A": 0, "B": 1, "C": 2}[lg.band]))
        self._writers["cens"].append_many(sext)

    # ---------------------------------------------------------- finalize

    def finalize(self) -> "BookStats":
        for w in self._writers.values():
            w.flush()
        nets = read_spill(self.spill_dir / f"{self.book_id}__net.f64",
                          np.float64)
        folds = read_spill(self.spill_dir / f"{self.book_id}__fold.i8",
                           np.int8)
        ncal = len(self.calendar)
        series = np.zeros(ncal, dtype=float)
        nz = self.active > 0
        series[nz] = self.book_log_sum[nz] / self.active[nz]

        def _fold_expectancy(nets_arr, folds_arr):
            out = {}
            for f in FOLDS:
                v = nets_arr[folds_arr == FOLD_CODE[f]]
                if v.size:
                    out[f] = float(np.mean(v))
            return out

        stats = BookStats(
            book_id=self.book_id, config_id=self.config_id, H=self.H,
            stress=self.stress, calendar=self.calendar,
            expectancy=float(np.mean(nets)) if nets.size else math.nan,
            fold_expectancy=_fold_expectancy(nets, folds),
            fold_leg_counts={f: int(np.count_nonzero(
                folds == FOLD_CODE[f])) for f in FOLDS
                if int(np.count_nonzero(folds == FOLD_CODE[f]))},
            n_legs=int(nets.size), n_censored=self.n_censored,
            censored_kinds=sorted(self.censored_kinds),
            counts=dict(self.counts), book_log=series,
        )
        # candidate-only aligned arrays (held for adjudication; the caller
        # frees them after use to keep finalize-time RAM bounded)
        if self.keep_spy:
            stats.gross = read_spill(
                self.spill_dir / f"{self.book_id}__gross.f64", np.float64)
            stats.band_codes = read_spill(
                self.spill_dir / f"{self.book_id}__band.i8", np.int8)
            stats.spy = read_spill(
                self.spill_dir / f"{self.book_id}__spy.f64", np.float64)
        # BC-7 included variant (death_open legs at their marks, appended
        # AFTER all primary legs exactly like include_censored_nets)
        cens = read_spill(
            self.spill_dir / f"{self.book_id}__cens_death_open.f64",
            np.float64).reshape(-1, 6) if (self.spill_dir /
            f"{self.book_id}__cens_death_open.f64").stat().st_size else \
            np.zeros((0, 6), dtype=np.float64)
        if cens.shape[0]:
            inc_nets = np.concatenate([nets, cens[:, 1]])
            inc_folds = np.concatenate([
                folds, cens[:, 0].astype(np.int8)])
            stats.inc_expectancy = float(np.mean(inc_nets))
            stats.inc_fold_expectancy = _fold_expectancy(inc_nets, inc_folds)
            stats.inc_nets = inc_nets
            stats.inc_folds = inc_folds
            stats.inc_spy = np.concatenate([
                stats.spy if stats.spy is not None else nets[:0],
                _spy_for_censored(cens[:, 2], cens[:, 3], self.calendar)])
            # E2F-4: the included variant's break-even inputs must span
            # the appended death_open legs too (gross + band codes)
            if stats.gross is not None:
                stats.inc_gross = np.concatenate(
                    [stats.gross, cens[:, 4]])
                stats.inc_band_codes = np.concatenate(
                    [stats.band_codes, cens[:, 5].astype(np.int8)])
        else:
            stats.inc_expectancy = stats.expectancy
            stats.inc_fold_expectancy = dict(stats.fold_expectancy)
            stats.inc_nets = nets
            stats.inc_folds = folds
            stats.inc_spy = stats.spy
            stats.inc_gross = stats.gross
            stats.inc_band_codes = stats.band_codes
        stats.nets, stats.folds = nets, folds
        return stats

    def close(self) -> None:
        for w in self._writers.values():
            try:
                w.close()
            except Exception:
                pass


def _spy_for_censored(entry_yyyymmdd, exit_yyyymmdd, calendar) -> np.ndarray:
    """spy legs for included censored legs, aligned by append order.

    Mirrors i_engine.spy_legs_for over the extra legs: NaN where SPY does
    not serve the dates.  Uses the SPY NameData pinned on the calendar
    holder (set via set_spy_reference before finalize).
    """
    out = [_spy_leg_value(_iso(int(ey)), _iso(int(xy)))
           for ey, xy in zip(entry_yyyymmdd, exit_yyyymmdd)]
    return np.asarray(out, dtype=np.float64)


_SPY_REF: list = [None]


def set_spy_reference(spy: NameData | None) -> None:
    _SPY_REF[0] = spy


def get_spy_reference():
    return _SPY_REF[0]


def _spy_leg_value(entry_date: str, exit_date: str) -> float:
    """One benchmark leg, mirroring i_engine.spy_legs_for per leg
    (NaN where SPY does not serve the dates).  The SPY reference is
    pinned BEFORE any name streams, so the value never depends on
    parse order."""
    spy = _SPY_REF[0]
    if spy is None:
        return math.nan
    e = nm_dates_index(spy, entry_date)
    x = nm_dates_index(spy, exit_date)
    if e is None or x is None or x <= e:
        return math.nan
    return float(spy.adj_open[x]) / float(spy.adj_open[e]) - 1.0


def _iso(yyyymmdd: int) -> str:
    s = str(int(yyyymmdd))
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"


@dataclass
class BookStats:
    """Finalized streaming book: everything adjudicate.py consumes."""
    book_id: str
    config_id: str
    H: int
    stress: float
    calendar: tuple
    expectancy: float
    fold_expectancy: dict
    fold_leg_counts: dict
    n_legs: int
    n_censored: int
    censored_kinds: list
    counts: dict
    book_log: np.ndarray
    gross: np.ndarray = None
    band_codes: np.ndarray = None
    spy: np.ndarray = None
    nets: np.ndarray = None
    folds: np.ndarray = None
    inc_expectancy: float = math.nan
    inc_fold_expectancy: dict = field(default_factory=dict)
    inc_nets: np.ndarray = None
    inc_folds: np.ndarray = None
    inc_spy: np.ndarray = None
    inc_gross: np.ndarray = None
    inc_band_codes: np.ndarray = None

    def series_sha256(self) -> str:
        return canon_sha256({
            "book_id": self.book_id, "config_id": self.config_id,
            "calendar": list(self.calendar),
            "book_log": [round(float(x), 15) for x in self.book_log],
        })

    def free_arrays(self) -> None:
        self.gross = self.band_codes = self.spy = None
        self.nets = self.folds = None
        self.inc_nets = self.inc_folds = self.inc_spy = None


# ============================================================ streaming pass

@dataclass
class PassAState:
    """Everything pass A accumulates (all small or on-disk)."""
    fired_dates: set = field(default_factory=set)
    pit_total: int = 0
    pit_changed: int = 0
    pit_per_name: dict = field(default_factory=dict)
    cohort_counts: dict = field(default_factory=dict)


def per_name_masks(name: NameData, cell: dict) -> dict:
    """The four per-name decision masks (candidate/complement/r5/delay).

    Bit-identical to i_engine.arm_decision_masks/complement_masks/
    r5_masks/delay_masks restricted to one name.
    """
    fired, _bookable = state_fired_mask(name, cell["family"], cell["params"])
    cand = [int(i) for i in
            np.nonzero(_warmup_gate(fired, cell["warmup_need"]))[0]]
    comp = [int(i) for i in
            np.nonzero(complement_fired_mask(name, cell))[0]]
    r5 = [int(i) for i in
          np.nonzero(r5_component_fired_mask(name, cell))[0]]
    return {"candidate": cand, "c_complement": comp, "r5_component": r5,
            "c_delay_h": list(cand)}


def per_name_pit(name: NameData, cand_idx, cell: dict) -> dict:
    """C-PIT-MUTATION for one name, mirroring i_engine.pit_mutation_gate."""
    if not cand_idx:
        return {"fired": 0, "changed": 0}
    mut_state = state_fired_mask(name, cell["family"], cell["params"])[0]
    mutated = np.zeros(len(mut_state), dtype=bool)
    mutated[1:] = mut_state[:-1]
    core = i_engine.pit_gate_core(mutated, cand_idx)
    return {"fired": core["fired"], "changed": core["changed_or_refused"]}


def reversal_eligibility(name: NameData, calendar) -> list:
    """Per-name C-REVERSAL-PLAIN eligibility spill rows (formation_j, r).

    Mirrors reversal_plain_decisions' inner loop for ONE name exactly:
    formation j = calendar index, j % 5 == 0 and j >= 5; eligibility =
    both dates served, pos >= 251, bookable floors at pos.
    """
    L = load_p0_lib()
    med60 = L._rolling_median(name.adj_close * name.volume, L.DVOL_WINDOW)
    rows = []
    for j in range(REVERSAL_PLAIN_PERIOD, len(calendar),
                  REVERSAL_PLAIN_PERIOD):
        d = calendar[j]
        pos = nm_dates_index(name, d)
        prev = nm_dates_index(name, calendar[j - REVERSAL_PLAIN_PERIOD])
        if pos is None or prev is None:
            continue
        if pos < 251:
            continue
        if not _bookable_at(name, pos, med60):
            continue
        r = float(name.adj_close[pos]) / float(name.adj_close[prev]) - 1.0
        rows.append((j, r))
    return rows


def _bookable_at(name: NameData, i: int, med60_arr) -> bool:
    L = load_p0_lib()
    if i < 0 or i >= len(name.dates):
        return False
    m = med60_arr[i]
    return bool(name.adj_close[i] >= L.FLOOR_PRICE
                and np.isfinite(m) and m >= L.FLOOR_DVOL)


def reversal_picks(rev_rows_by_sym: dict, calendar) -> tuple[dict, dict]:
    """Cross-sectional worst-quintile picks from the per-name spill rows.

    Mirrors reversal_plain_decisions exactly: per formation, score list of
    (r, sym) sorted ascending, k = max(1, ceil(n/5)), first k picked;
    stats.formations / eligible_avg identical.
    """
    by_j: dict[int, list] = {}
    for sym, rows in rev_rows_by_sym.items():
        for j, r in rows:
            by_j.setdefault(j, []).append((r, sym))
    picks: dict[str, list[str]] = {}
    stats = {"formations": 0, "eligible_avg": 0.0}
    n_elig = 0
    for j in sorted(by_j):
        scored = by_j[j]
        if not scored:
            continue
        stats["formations"] += 1
        n_elig += len(scored)
        scored.sort()
        k = max(1, math.ceil(len(scored) / 5))
        for _r, sym in scored[:k]:
            picks.setdefault(sym, []).append(calendar[j])
    stats["eligible_avg"] = n_elig / stats["formations"] \
        if stats["formations"] else 0.0
    return picks, stats


def cohort_mask_for_name(name: NameData, decision_dates, counts=None) -> list:
    """cohort_bookable_decisions restricted to one name (order preserved).

    Mirrors i_engine.cohort_bookable_decisions: date-major iteration, F4
    floors + 252-session warmup law; counter increments ONLY when a counts
    dict is passed (the reference passes it for C-RANDOM-TIMING only).
    """
    L = load_p0_lib()
    if len(name.dates) < 252:
        # every decision date would trip the warmup law for this name
        if counts is not None:
            for d in decision_dates:
                if nm_dates_index(name, d) is not None:
                    counts["warmup_short_history"] = \
                        counts.get("warmup_short_history", 0) + 1
        return []
    med60 = L._rolling_median(name.adj_close * name.volume, L.DVOL_WINDOW)
    out = []
    for d in decision_dates:
        pos = nm_dates_index(name, d)
        if pos is None:
            continue
        if pos < 251:
            if counts is not None:
                counts["warmup_short_history"] = \
                    counts.get("warmup_short_history", 0) + 1
            continue
        if _bookable_at(name, pos, med60):
            out.append(pos)
        elif counts is not None:
            counts["cohort_floor_reject"] = \
                counts.get("cohort_floor_reject", 0) + 1
    return out


# ============================================================ cell drivers

def _fends(calendar, b1: str, b2: str) -> dict:
    return i_engine.fold_ends(tuple(calendar), b1, b2)


def stream_cell_pass_a(names_iter, cell: dict, calendar, b1: str, b2: str,
                       spill_dir: Path, quota_bytes: int,
                       spy: NameData | None) -> tuple[dict, PassAState]:
    """PASS A over the cohort: candidate/complement/r5/delay books + PIT +
    fired-date census + reversal eligibility spill.  names_iter yields
    (symbol, NameData) in sorted order (identical to the frozen
    build_all_books iteration order).  spy pins the SPY benchmark
    reference BEFORE any name streams (order-independent).

    Every leg comes from the UNMODIFIED i_engine.build_legs; the only
    change vs the frozen path is that legs are folded into streaming
    accumulators instead of being materialized across the cohort.
    """
    set_spy_reference(spy)
    cal = tuple(calendar)
    calendar_index = {d: i for i, d in enumerate(cal)}
    fends = _fends(cal, b1, b2)
    H = int(cell["params"]["H"])
    stress = STRESS_TIER
    cid = cell["config_id"]
    spill_dir = Path(spill_dir)
    books = {
        "candidate": BookAcc("candidate", cid, H, stress, cal, spill_dir,
                             quota_bytes, keep_spy=True),
        "c_complement": BookAcc("c_complement", cid, H, stress, cal,
                                spill_dir, quota_bytes),
        "r5_component": BookAcc("r5_component", cid, H, stress, cal,
                                spill_dir, quota_bytes),
        "c_delay_h": BookAcc("c_delay_h", cid, H, stress, cal, spill_dir,
                             quota_bytes),
    }
    st = PassAState()
    rev_rows: dict[str, list] = {}
    for sym, nm in names_iter:
        pass_a_feed_name(books, st, rev_rows, cell, calendar_index,
                         fends, sym, nm, rev_calendar=cal)
    out = {
        "cell": cid, "H": H, "stress": stress,
        "books": books,
        "fired_dates": sorted(st.fired_dates),
        "pit_mutation": {
            "gate": "C-PIT-MUTATION", "fired": st.pit_total,
            "changed_or_refused": st.pit_changed,
            "pass": st.pit_total > 0 and st.pit_changed == st.pit_total,
            "per_name": st.pit_per_name,
            "law": ("one-session-earlier recomputation changes/refuses the "
                    "book on every fired decision (plan §6 verbatim; "
                    "mechanics pinned in i_engine)")},
        "_rev_rows": rev_rows,
    }
    return out, st


def stream_cell_pass_b(names_iter, cell: dict, calendar, b1: str, b2: str,
                       spill_dir: Path, quota_bytes: int,
                       fired_dates: list, rev_rows: dict,
                       spy: NameData | None) -> dict:
    """PASS B over the cohort: the three cohort books (C-RANDOM-TIMING,
    C-CAL-HIST, C-REVERSAL-PLAIN).  A second parse pass is REQUIRED
    because C-CAL-HIST twin dates depend on the COMPLETE candidate
    fired-date census (pass A) and C-REVERSAL-PLAIN picks depend on the
    complete cross-section - both frozen cross-sectional controls.
    """
    set_spy_reference(spy)
    cal = tuple(calendar)
    calendar_index = {d: i for i, d in enumerate(cal)}
    fends = _fends(cal, b1, b2)
    H = int(cell["params"]["H"])
    stress = STRESS_TIER
    cid = cell["config_id"]
    spill_dir = Path(spill_dir)
    rt_dates = random_timing_decisions(cal)
    ch_dates, ch_report = cal_hist_twin_dates(fired_dates, cal, b1, b2)
    picks, rev_stats = reversal_picks(rev_rows, cal)
    books = {
        "c_random_timing": BookAcc("c_random_timing", cid, H, stress, cal,
                                   spill_dir, quota_bytes),
        "c_cal_hist": BookAcc("c_cal_hist", cid, H, stress, cal,
                              spill_dir, quota_bytes),
        "c_reversal_plain": BookAcc("c_reversal_plain", cid,
                                    REVERSAL_PLAIN_H, stress, cal,
                                    spill_dir, quota_bytes),
    }
    cohort_counts: dict = {}
    for sym, nm in names_iter:
        pass_b_feed_name(books, cohort_counts, rt_dates, ch_dates, picks,
                         calendar_index, fends, H, stress, sym, nm)
    return {"books": books, "c_cal_hist_report": ch_report,
            "reversal_stats": rev_stats, "counts_cohort": cohort_counts}


# ====================================================== adjudication mirror
#
# LINE-BY-LINE mirror of i/adjudicate.py (ordered_kills, stage_a_gates,
# adjudicate_candidate, k6_slow_drift and helpers) over BookStats.  The
# mirror consumes streaming aggregates instead of materialized Leg lists;
# every float expression and every summation ORDER is identical.  The
# equivalence runner (e2/equivalence.py) proves mirror == reference on
# fixtures by running BOTH and comparing canonical outputs bit-for-bit.

def _m_mean(xs) -> float:
    xs = [x for x in xs if x == x and x is not None]
    return float(np.mean(xs)) if xs else math.nan


def _m_same_sign_half(value: float, ref: float) -> bool:
    if value == value and ref == ref and ref != 0.0:
        return value * ref > 0.0 and abs(value) >= 0.5 * abs(ref)
    return False


def _m_fold_pairs(cand_fold: dict, ctrl_fold: dict) -> dict:
    folds = sorted(set(cand_fold) | set(ctrl_fold))
    return {f: (cand_fold.get(f, math.nan), ctrl_fold.get(f, math.nan))
            for f in folds}


def folds_reproducing(cand_fold: dict, ctrl_fold: dict) -> int:
    return sum(1 for f, (c, k) in _m_fold_pairs(cand_fold, ctrl_fold).items()
               if _m_same_sign_half(k, c))


def fold_pnl_by_fold(book, calendar, b1: str, b2: str) -> dict:
    L = load_p0_lib()
    out = {"F1": 0.0, "F2": 0.0, "F3": 0.0}
    for d, x in zip(calendar, book.book_log):
        out[L.assign_fold(d, b1, b2)] += float(x)
    return out


def max_drawdown(book_log) -> float:
    wealth = np.exp(np.cumsum(book_log))
    peak = np.maximum.accumulate(wealth)
    dd = 1.0 - wealth / peak
    return float(dd.max()) if dd.size else 0.0


def break_even_margin(book) -> dict:
    gross = _m_mean([float(x) for x in book.gross]) \
        if book.gross is not None and book.gross.size else math.nan
    if gross != gross:
        return {"break_even_bps_per_fill": math.nan, "margin_bps": math.nan}
    be = gross * 1e4 / 2.0
    L = load_p0_lib()
    if book.n_legs:
        band_name = {0: "A", 1: "B", 2: "C"}
        avg_bps = _m_mean([float(L.BAND_BPS[band_name[int(b)]])
                           for b in book.band_codes])
    else:
        avg_bps = math.nan
    return {"break_even_bps_per_fill": be,
            "operative_stress_bps_per_fill": avg_bps * book.stress,
            "margin_bps": be - avg_bps * book.stress}


def k6_slow_drift(cand, delay, compl) -> dict:
    by_fold: dict[str, list[float]] = {}
    for net, fc in zip(cand.nets, cand.folds):
        by_fold.setdefault(FOLDS[int(fc)], []).append(float(net))
    counted = 0
    indist = 0
    detail = {}
    for f in sorted(set(by_fold) | set(cand.fold_expectancy)):
        nets = by_fold.get(f, [])
        if len(nets) < 2:
            detail[f] = {"counted": False, "reason": "fewer than 2 legs"}
            continue
        counted += 1
        se = statistics.stdev(nets) / math.sqrt(len(nets))
        e_c = cand.fold_expectancy.get(f, math.nan)
        d1 = abs(e_c - delay.fold_expectancy.get(f, math.nan))
        d2 = abs(e_c - compl.fold_expectancy.get(f, math.nan))
        pair = bool(d1 <= se and d2 <= se)
        indist += int(pair)
        detail[f] = {"counted": True, "se": se, "d_delay": d1,
                     "d_complement": d2, "indistinguishable": pair}
    reject = counted >= 1 and indist * 3 >= 2 * counted
    return {"rule": "K6", "reject": reject, "folds_counted": counted,
            "folds_indistinguishable": indist, "detail": detail,
            "test_status": "PINNED_AT_I_DEVIATION_DISCLOSED"}


def ordered_kills(bundle: dict, spy, calendar, b1: str, b2: str) -> dict:
    cand = bundle["candidate"]
    rows = []

    def bind(rule, why):
        rows.append({"rule": rule, "binding": True, "detail": why})
        return {"binding_rule": rule, "reject": True, "rows": rows,
                "verdict": f"REJECT_{rule}"}

    e_c = cand.expectancy
    rows.append({"rule": "R1", "binding": False,
                 "detail": {"net_expectancy_stress2": e_c,
                            "law": "net expectancy <= 0 at stress 2.0 -> "
                                   "REJECT_ALL"}})
    if not (e_c == e_c) or e_c <= 0.0:
        return bind("R1", {"net_expectancy_stress2": e_c})

    spy_legs = [float(s) for s in cand.spy] \
        if cand.spy is not None else []
    e_market = _m_mean(spy_legs)
    e_random = bundle["c_random_timing"].expectancy
    comparators = {k: v for k, v in (("C-MARKET", e_market),
                                     ("C-RANDOM-TIMING", e_random))
                   if v == v}
    rows.append({"rule": "R2", "binding": False,
                 "detail": {"e_candidate": e_c, "e_cmarket": e_market,
                            "e_random_timing": e_random,
                            "populated_comparators": sorted(comparators)}})
    if comparators and e_c <= max(comparators.values()):
        return bind("R2", {"e_candidate": e_c,
                           "comparator": max(comparators,
                                             key=comparators.get),
                           "comparator_value": max(comparators.values())})
    if not comparators:
        rows[-1]["detail"]["disposition"] = (
            "both R2 comparators unpopulated -> NOT_ADJUDICABLE")

    compl = bundle["c_complement"]
    n_repro = folds_reproducing(cand.fold_expectancy,
                                compl.fold_expectancy)
    rows.append({"rule": "R3", "binding": False,
                 "detail": {"e_complement": compl.expectancy,
                            "e_candidate": e_c,
                            "folds_reproducing_0.5x_same_sign": n_repro,
                            "not_adjudicable": compl.n_legs == 0}})
    if compl.n_legs == 0:
        rows[-1]["detail"]["disposition"] = (
            "C-COMPLEMENT unpopulated -> NOT_ADJUDICABLE, never silently "
            "skipped (plan §6 disposition rule)")
    else:
        if compl.expectancy > e_c or n_repro >= 2:
            return bind("R3", {"e_complement": compl.expectancy,
                               "folds_reproducing": n_repro})

    rev = bundle["c_reversal_plain"]
    n_repro_r = folds_reproducing(cand.fold_expectancy,
                                  rev.fold_expectancy)
    rows.append({"rule": "R4", "binding": False,
                 "detail": {"e_reversal_plain": rev.expectancy,
                            "folds_reproducing_0.5x_same_sign": n_repro_r,
                            "not_adjudicable": rev.n_legs == 0}})
    if rev.n_legs == 0:
        rows[-1]["detail"]["disposition"] = (
            "C-REVERSAL-PLAIN unpopulated -> NOT_ADJUDICABLE (mandatory "
            "rule cannot pass on an empty control)")
    else:
        if rev.expectancy > e_c or n_repro_r >= 2:
            return bind("R4", {"e_reversal_plain": rev.expectancy,
                               "folds_reproducing": n_repro_r})

    r5 = bundle["r5_component"]
    n_repro_5 = folds_reproducing(cand.fold_expectancy,
                                  r5.fold_expectancy)
    full_rep = _m_same_sign_half(r5.expectancy, e_c)
    rows.append({"rule": "R5", "binding": False,
                 "detail": {"e_component_only": r5.expectancy,
                            "folds_reproducing_0.5x_same_sign": n_repro_5,
                            "full_sample_0.5x_same_sign": full_rep,
                            "not_adjudicable": r5.n_legs == 0,
                            "binding_form": "union(folds>=2/3, full-sample)",
                            "fold_rule_not_adjudicable":
                                len(cand.fold_expectancy) < 3}})
    if r5.n_legs == 0:
        rows[-1]["detail"]["disposition"] = (
            "R5 component-only unpopulated -> NOT_ADJUDICABLE (manifest "
            "declares every family adjudicable; an empty book on real "
            "data is a disclosed anomaly, never an inferred PASS)")
    else:
        if n_repro_5 >= 2 or full_rep:
            return bind("R5", {"folds_reproducing": n_repro_5,
                               "full_sample": full_rep})

    rnd = bundle["c_random_timing"]
    ch = bundle["c_cal_hist"]
    sub_floor = any(v["sub_floor"]
                    for rep in bundle["c_cal_hist_report"].values()
                    for v in rep.values())
    rows.append({"rule": "R6", "binding": False,
                 "detail": {"e_random_timing": rnd.expectancy,
                            "e_cal_hist": ch.expectancy,
                            "cal_hist_bucket_sub_floor": sub_floor}})
    if (rnd.expectancy == rnd.expectancy) and rnd.expectancy > e_c:
        return bind("R6", {"out_earner": "C-RANDOM-TIMING"})
    if sub_floor:
        rows[-1]["detail"]["disposition"] = (
            "C-CAL-HIST sub-floor bucket -> NOT_ADJUDICABLE and disclosed; "
            "R6 binds on C-RANDOM-TIMING only (plan §6)")
    elif (ch.expectancy == ch.expectancy) and ch.expectancy > e_c:
        return bind("R6", {"out_earner": "C-CAL-HIST"})

    k6 = k6_slow_drift(cand, bundle["c_delay_h"], compl)
    rows.append({"rule": "K6", "binding": False, "detail": k6})
    if k6["reject"]:
        return bind("K6", k6)

    return {"binding_rule": None, "reject": False, "rows": rows,
            "verdict": "NO_KILL_THROUGH_K6"}


def stage_a_gates(bundle: dict, spy, calendar, b1: str, b2: str,
                  cand=None) -> dict:
    cand = cand or bundle["candidate"]
    L = load_p0_lib()
    gates = {}

    pnl = fold_pnl_by_fold(cand, calendar, b1, b2)
    pos = {f: max(v, 0.0) for f, v in pnl.items()}
    tot_pos = sum(pos.values())
    fps = (max(pos.values()) / tot_pos) if tot_pos > 0 else math.nan
    gates["fold_positive_share"] = {
        "value": fps, "limit": 0.50,
        "pass": fps == fps and fps <= 0.50,
        "law": "fold-positive-share > 50% KILLS (V11 precedent 0.5034 "
               "FAILING)",
        "statistic": "largest positive fold share of total positive fold "
                     "PnL (P-11)",
        "not_adjudicable": tot_pos <= 0.0}

    abs_pnl = {f: abs(v) for f, v in pnl.items()}
    tot_abs = sum(abs_pnl.values())
    conc = (max(abs_pnl.values()) / tot_abs) if tot_abs > 0 else math.nan
    gates["largest_fold_concentration"] = {
        "value": conc, "limit": 0.50,
        "pass": conc == conc and conc <= 0.50,
        "law": "largest-fold PnL concentration > 50% KILLS",
        "statistic": "max |fold PnL| / sum |fold PnL| (P-11)"}

    if cand.spy is not None:
        by_fold: dict[str, list[float]] = {}
        for net, s, fc in zip(cand.nets, cand.spy, cand.folds):
            if s == s:
                by_fold.setdefault(FOLDS[int(fc)], []).append(float(net) - s)
        excess = {f: _m_mean(v) for f, v in sorted(by_fold.items())}
        n_pos = sum(1 for v in excess.values() if v > 0)
    else:
        excess, n_pos = {}, 0
    gates["spy_excess_folds"] = {
        "per_fold": excess, "positive_folds": n_pos,
        "pass": n_pos >= 2,
        "law": "SPY-excess positive in >= 2/3 folds REQUIRED",
        "not_adjudicable": len(excess) < 3 or spy is None}

    mdd = max_drawdown(cand.book_log)
    gates["mdd"] = {"value": mdd, "limit": 0.15,
                    "pass": mdd <= 0.15,
                    "law": "MDD <= 15% (P-11 daily book series)"}

    be = break_even_margin(cand)
    gates["stress_margin"] = {
        "net_expectancy_stress2": cand.expectancy,
        "break_even_bps_per_fill": be["break_even_bps_per_fill"],
        "margin_bps": be["margin_bps"],
        "pass": cand.expectancy == cand.expectancy
        and cand.expectancy > 0,
        "law": "stress-2.0 net positive with break-even margin"}

    drop_one = {}
    stable = True
    adjudicable = True
    for f in ("F1", "F2", "F3"):
        rest = [float(x) for x, fc in zip(cand.nets, cand.folds)
                if FOLDS[int(fc)] != f]
        if not rest:
            drop_one[f] = "NOT_ADJUDICABLE (empty drop-one set)"
            adjudicable = False
            continue
        e_rest = _m_mean(rest)
        ok = cand.expectancy == cand.expectancy and \
            (e_rest > 0) == (cand.expectancy > 0)
        drop_one[f] = {"e_rest": e_rest, "sign_stable": ok}
        stable = stable and ok
    gates["drop_one_stability"] = {
        "per_fold": drop_one, "pass": stable and adjudicable,
        "not_adjudicable": not adjudicable,
        "law": "drop-one sign stability (all leave-one-fold-out sets)"}

    gates["pit_mutation"] = dict(bundle["pit_mutation"])
    gates["pit_mutation"]["pass"] = bool(bundle["pit_mutation"]["pass"])

    gates["death_censoring_accounting"] = {
        "censored_legs": cand.n_censored,
        "kinds": list(cand.censored_kinds),
        "invariance_mode": "censored legs excluded from the numerator "
                           "(primary); included-at-marks rerun compared "
                           "in adjudicate_candidate (binds verdict AND "
                           "gates)",
        "law": "BC-7 in full"}

    return {"gates": gates, "fold_pnl": pnl}


def _gate_summary(sa: dict) -> dict:
    out = {}
    for name, g in sa["gates"].items():
        if name in ("death_censoring_accounting",):
            continue
        out[name] = ("NOT_ADJUDICABLE" if g.get("not_adjudicable")
                     else "PASS" if g.get("pass") else "FAIL")
    return out


def as_included(stats: BookStats) -> BookStats:
    """The BC-7 included-at-marks view of a BookStats (mirror of
    include_censored_nets: same book with death_open legs appended)."""
    return BookStats(
        book_id=stats.book_id + "+censored", config_id=stats.config_id,
        H=stats.H, stress=stats.stress, calendar=stats.calendar,
        expectancy=stats.inc_expectancy,
        fold_expectancy=dict(stats.inc_fold_expectancy),
        fold_leg_counts={}, n_legs=stats.n_legs, n_censored=stats.n_censored,
        censored_kinds=list(stats.censored_kinds), counts=dict(stats.counts),
        book_log=stats.book_log, gross=stats.inc_gross,
        band_codes=stats.inc_band_codes, spy=stats.inc_spy,
        nets=stats.inc_nets, folds=stats.inc_folds)


def _invariant_rerun(bundle: dict, spy, calendar, b1, b2,
                     primary_rule) -> dict:
    inv_bundle = {k: (as_included(v) if isinstance(v, BookStats) else v)
                  for k, v in bundle.items()}
    inv = ordered_kills(inv_bundle, spy, calendar, b1, b2)
    return {"included_binding_rule": inv["binding_rule"],
            "primary_binding_rule": primary_rule,
            "verdict_matches": inv["binding_rule"] == primary_rule}


def adjudicate_candidate_stream(bundle: dict, spy, calendar,
                                b1: str, b2: str) -> dict:
    """Mirror of adjudicate.adjudicate_candidate over streaming stats."""
    primary = ordered_kills(bundle, spy, calendar, b1, b2)
    result = {
        "config_id": bundle["cell"],
        "stress": STRESS_TIER,
        "primary": primary,
        "r0_status": i_engine.R0_NOT_RUN_LABEL,
        "r0_verbatim": i_engine.R0_NOT_RUN_VERBATIM,
        "pbo_status": i_engine.PBO_NOT_RUN_LABEL,
        "pbo_verbatim": i_engine.PBO_NOT_RUN_VERBATIM,
        "disclosure_section10": i_engine.DISCLOSURE_SECTION10_VERBATIM,
        "retrieval_empty_count_disclosure":
            i_engine.RETRIEVAL_EMPTY_COUNT_DISCLOSURE_VERBATIM,
        "budget": {"used": 0, "max": 3,
                   "label": "0/3 (consumed only at scored E)"},
        "dsr": {"gate": "E_SCORED_ONLY", "n_grid": 47, "alpha": 0.10,
                "program": {"n": 260, "alpha": 0.05,
                            "role": "reported-only"}},
    }
    if primary["reject"]:
        result["verdict"] = primary["verdict"]
        result["stage_a"] = None
        inv = _invariant_rerun(bundle, spy, calendar, b1, b2,
                               primary["binding_rule"])
        result["death_invariance"] = inv
        if inv["verdict_matches"] is False:
            result["verdict"] = "DEATH_CENSORING_COUPLED_UNBOOKABLE"
        return result

    sa = stage_a_gates(bundle, spy, calendar, b1, b2)
    summary = _gate_summary(sa)
    result["stage_a"] = {"gates": summary, "detail_fold_pnl": sa["fold_pnl"]}
    inv_bundle = dict(bundle)
    for key in ("candidate", "c_complement", "r5_component", "c_delay_h",
                "c_random_timing", "c_cal_hist", "c_reversal_plain"):
        inv_bundle[key] = as_included(bundle[key])
    inv_kills = ordered_kills(inv_bundle, spy, calendar, b1, b2)
    inv_sa = stage_a_gates(inv_bundle, spy, calendar, b1, b2)
    inv_summary = _gate_summary(inv_sa)

    def _verdict_from_summary(s: dict, kills_rule) -> str:
        if kills_rule is not None:
            return f"REJECT_{kills_rule}"
        if any(v == "FAIL" for v in s.values()):
            return "STAGE_A_FAIL"
        if any(v == "NOT_ADJUDICABLE" for v in s.values()):
            return "STAGE_A_NOT_ADJUDICABLE_DISCLOSED"
        return "PASS_I_STAGE_PENDING_DSR_E"

    v_primary = _verdict_from_summary(summary, None)
    v_inv = _verdict_from_summary(inv_summary, inv_kills["binding_rule"])
    matches = (v_inv == v_primary) and (summary == inv_summary)
    result["death_invariance"] = {
        "primary_stage_a": summary, "included_stage_a": inv_summary,
        "primary_kills_rule": primary["binding_rule"],
        "included_kills_rule": inv_kills["binding_rule"],
        "verdict_matches": matches,
        "law": "death-censoring invariance binds the verdict AND every "
               "Stage-A gate (BC-7; a coupled result is unbookable)"}
    if not matches:
        result["verdict"] = "DEATH_CENSORING_COUPLED_UNBOOKABLE"
    else:
        result["verdict"] = v_primary
        if v_primary == "PASS_I_STAGE_PENDING_DSR_E":
            result["dsr"]["binding_law"] = (
                "DSR (E[max SR], DSR_BAILEY_LOPEZDEPRADO_V1) gates BEFORE "
                "any survivor name is named; computed ONLY at the scored "
                "E run")
    return result


def persist_p11(path: Path, book: BookStats) -> str:
    """Mirror of adjudicate.persist_series (P-11 daily series)."""
    payload = {
        "schema": "stocks_search_v1_p11_series@1",
        "book_id": book.book_id,
        "config_id": book.config_id,
        "calendar": list(book.calendar),
        "book_log": [float(x) for x in book.book_log],
        "expectancy": book.expectancy,
        "fold_expectancy": book.fold_expectancy,
    }
    digest = canon_sha256(payload)
    payload["sha256"] = digest
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    os.replace(tmp, path)
    return digest


def pass_a_feed_name(books: dict, st: PassAState, rev_rows: dict,
                     cell: dict, calendar_index: dict, fends: dict,
                     sym: str, nm: NameData,
                     rev_calendar=None) -> None:
    """Feed ONE name through pass A (the exact per-name body of the
    monolithic stream_cell_pass_a loop)."""
    H = int(cell["params"]["H"])
    stress = STRESS_TIER
    if rev_calendar is None:
        rev_calendar = tuple(calendar_index)
    masks = per_name_masks(nm, cell)
    for key in ("candidate", "c_complement", "r5_component"):
        if masks[key]:
            legs, cens, counts = i_engine.build_legs(
                nm, masks[key], H, calendar_index, fends, stress)
            books[key].add_legs(legs, cens, counts)
    if masks["c_delay_h"]:
        legs, cens, counts = i_engine.build_legs(
            nm, masks["c_delay_h"], H, calendar_index, fends, stress,
            entry_offset=1 + H)
        books["c_delay_h"].add_legs(legs, cens, counts)
    st.fired_dates.update(nm.dates[t] for t in masks["candidate"])
    pit = per_name_pit(nm, masks["candidate"], cell)
    st.pit_total += pit["fired"]
    st.pit_changed += pit["changed"]
    st.pit_per_name[sym] = pit
    rows = reversal_eligibility(nm, rev_calendar)
    if rows:
        rev_rows[sym] = rows


def pass_b_feed_name(books: dict, cohort_counts: dict, rt_dates,
                     ch_dates, picks: dict, calendar_index: dict,
                     fends: dict, H: int, stress: float,
                     sym: str, nm: NameData) -> None:
    """Feed ONE name through pass B (cohort books)."""
    rt_idx = cohort_mask_for_name(nm, rt_dates, counts=cohort_counts)
    if rt_idx:
        legs, cens, counts = i_engine.build_legs(
            nm, rt_idx, H, calendar_index, fends, stress)
        books["c_random_timing"].add_legs(legs, cens, counts)
    ch_idx = cohort_mask_for_name(nm, ch_dates)
    if ch_idx:
        legs, cens, counts = i_engine.build_legs(
            nm, ch_idx, H, calendar_index, fends, stress)
        books["c_cal_hist"].add_legs(legs, cens, counts)
    rev_idx = [i for i in (nm_dates_index(nm, d)
                           for d in picks.get(sym, []))
               if i is not None]
    if rev_idx:
        legs, cens, counts = i_engine.build_legs(
            nm, rev_idx, REVERSAL_PLAIN_H, calendar_index, fends,
            stress)
        books["c_reversal_plain"].add_legs(legs, cens, counts)


# ----------------------------------------------------- checkpointable pass

def _atomic_json(path: Path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        f.write(json.dumps(obj, indent=1, sort_keys=True,
                           default=str) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


class CheckpointablePassA:
    """Pass A with crash-safe resume.

    State = spill record counts + in-RAM accumulator snapshots
    (book_log_sum/active/counts/censoring) + pit jsonl + fired dates +
    reversal rows + names_done.  Resume truncates each spill to its
    checkpointed record count and skips the first names_done names, so a
    crashed run never double-counts a name.
    """

    def __init__(self, cell, calendar, b1, b2, spill_dir, quota_bytes,
                 spy, resume: bool = False):
        self.cell = cell
        self.cal = tuple(calendar)
        self.calendar_index = {d: i for i, d in enumerate(self.cal)}
        self.fends = _fends(self.cal, b1, b2)
        self.spill_dir = Path(spill_dir)
        self.quota_bytes = quota_bytes
        self.spy = spy
        self.ckpt = self.spill_dir / "ckpt_pass_a.json"
        H = int(cell["params"]["H"])
        stress = STRESS_TIER
        cid = cell["config_id"]
        self.names_done = 0
        self.fed = 0
        self.gen = 0
        self.st = PassAState()
        self.rev_rows: dict[str, list] = {}
        rr = None
        rg = 0
        if resume and self.ckpt.exists():
            state = json.loads(self.ckpt.read_text())
            self.names_done = int(state["names_done"])
            self.fed = int(state["names_done"])
            self.gen = int(state["gen"])
            self.st.pit_total = int(state["pit_total"])
            self.st.pit_changed = int(state["pit_changed"])
            self.st.fired_dates = set(state["fired_dates"])
            rr = state["writer_counts"]
            rg = self.gen
        self.books = {
            "candidate": BookAcc("candidate", cid, H, stress, self.cal,
                                 self.spill_dir, quota_bytes,
                                 keep_spy=True, resume_records=rr
                                 and rr.get("candidate"), resume_gen=rg),
            "c_complement": BookAcc("c_complement", cid, H, stress,
                                    self.cal, self.spill_dir, quota_bytes,
                                    resume_records=rr
                                    and rr.get("c_complement"),
                                    resume_gen=rg),
            "r5_component": BookAcc("r5_component", cid, H, stress,
                                    self.cal, self.spill_dir, quota_bytes,
                                    resume_records=rr
                                    and rr.get("r5_component"),
                                    resume_gen=rg),
            "c_delay_h": BookAcc("c_delay_h", cid, H, stress, self.cal,
                                 self.spill_dir, quota_bytes,
                                 resume_records=rr
                                 and rr.get("c_delay_h"), resume_gen=rg),
        }
        if resume and self.ckpt.exists():
            self._reload_rows()
        set_spy_reference(spy)

    def _rows_path(self):
        return self.spill_dir / "rows_pass_a.jsonl"

    def _reload_rows(self) -> None:
        rp = self._rows_path()
        if rp.exists():
            for line in rp.read_text().splitlines():
                if not line.strip():
                    continue
                obj = json.loads(line)
                if obj.get("kind") == "pit":
                    self.st.pit_per_name[obj["sym"]] = {
                        "fired": int(obj["fired"]),
                        "changed": int(obj["changed"])}
                elif obj.get("kind") == "rev":
                    self.rev_rows[obj["sym"]] = [
                        (int(j), float(r)) for j, r in obj["rows"]]

    def run(self, names_iter, checkpoint_every: int = 256,
            guard=None, log=None):
        rf = None
        n_since = 0
        for sym, nm in names_iter:
            if self.names_done > 0:
                self.names_done -= 1
                continue
            pass_a_feed_name(self.books, self.st, self.rev_rows,
                             self.cell, self.calendar_index, self.fends,
                             sym, nm, rev_calendar=self.cal)
            self.fed += 1
            if rf is None:
                rf = open(self._rows_path(), "a")
            rf.write(json.dumps({"kind": "pit", "sym": sym,
                                 "fired": self.st.pit_per_name[sym][
                                     "fired"],
                                 "changed": self.st.pit_per_name[sym][
                                     "changed"]}) + "\n")
            if self.rev_rows.get(sym):
                rf.write(json.dumps({"kind": "rev", "sym": sym,
                                     "rows": self.rev_rows[sym]}) + "\n")
            rf.flush()
            n_since += 1
            if guard is not None:
                guard(f"pass_a:{sym}")
            if n_since >= checkpoint_every:
                rf.flush()
                os.fsync(rf.fileno())
                rf.close()
                rf = None
                self.save()
                if log:
                    log(f"pass A checkpoint at {sym}")
                n_since = 0
        if rf is not None:
            rf.close()
        self.save()

    def save(self) -> None:
        g = self.gen + 1
        for acc in self.books.values():
            acc.save_checkpoint(g)
        _atomic_json(self.ckpt, {
            "gen": g,
            "names_done": self.fed,
            "pit_total": self.st.pit_total,
            "pit_changed": self.st.pit_changed,
            "fired_dates": sorted(self.st.fired_dates),
            "writer_counts": {k: b.record_counts()
                              for k, b in self.books.items()},
        })
        self.gen = g
        # rewrite the rows journal compactly (pit + rev) so resume never
        # depends on stale tail bytes
        rp = self._rows_path()
        tmp = rp.with_suffix(".jsonl.tmp")
        with open(tmp, "w") as f:
            for sym2, pit2 in sorted(self.st.pit_per_name.items()):
                f.write(json.dumps({"kind": "pit", "sym": sym2,
                                    "fired": pit2["fired"],
                                    "changed": pit2["changed"]}) + "\n")
            for sym2, rows in sorted(self.rev_rows.items()):
                f.write(json.dumps({"kind": "rev", "sym": sym2,
                                    "rows": rows}) + "\n")
        os.replace(tmp, rp)

    def result(self) -> dict:
        return {
            "cell": self.cell["config_id"],
            "H": int(self.cell["params"]["H"]),
            "stress": STRESS_TIER,
            "books": self.books,
            "fired_dates": sorted(self.st.fired_dates),
            "pit_mutation": {
                "gate": "C-PIT-MUTATION", "fired": self.st.pit_total,
                "changed_or_refused": self.st.pit_changed,
                "pass": (self.st.pit_total > 0
                         and self.st.pit_changed == self.st.pit_total),
                "per_name": self.st.pit_per_name,
                "law": ("one-session-earlier recomputation changes/"
                        "refuses the book on every fired decision (plan "
                        "§6 verbatim; mechanics pinned in i_engine)")},
            "_rev_rows": self.rev_rows,
        }


class CheckpointablePassB:
    """Pass B with crash-safe resume (same state law as pass A)."""

    def __init__(self, cell, calendar, b1, b2, spill_dir, quota_bytes,
                 spy, fired_dates, rev_rows, resume: bool = False):
        self.cell = cell
        self.cal = tuple(calendar)
        self.calendar_index = {d: i for i, d in enumerate(self.cal)}
        self.fends = _fends(self.cal, b1, b2)
        self.spill_dir = Path(spill_dir)
        self.quota_bytes = quota_bytes
        self.spy = spy
        self.ckpt = self.spill_dir / "ckpt_pass_b.json"
        H = int(cell["params"]["H"])
        stress = STRESS_TIER
        cid = cell["config_id"]
        self.rt_dates = random_timing_decisions(self.cal)
        self.ch_dates, self.ch_report = cal_hist_twin_dates(
            fired_dates, self.cal, b1, b2)
        self.picks, self.rev_stats = reversal_picks(rev_rows, self.cal)
        self.cohort_counts: dict = {}
        self.names_done = 0
        self.fed = 0
        self.gen = 0
        rr = None
        rg = 0
        if resume and self.ckpt.exists():
            state = json.loads(self.ckpt.read_text())
            self.names_done = int(state["names_done"])
            self.fed = int(state["names_done"])
            self.gen = int(state["gen"])
            self.cohort_counts = dict(state["cohort_counts"])
            rr = state["writer_counts"]
            rg = self.gen
        self.books = {
            "c_random_timing": BookAcc("c_random_timing", cid, H, stress,
                                       self.cal, self.spill_dir,
                                       quota_bytes,
                                       resume_records=rr
                                       and rr.get("c_random_timing"),
                                       resume_gen=rg),
            "c_cal_hist": BookAcc("c_cal_hist", cid, H, stress, self.cal,
                                  self.spill_dir, quota_bytes,
                                  resume_records=rr
                                  and rr.get("c_cal_hist"),
                                  resume_gen=rg),
            "c_reversal_plain": BookAcc("c_reversal_plain", cid,
                                        REVERSAL_PLAIN_H, stress,
                                        self.cal, self.spill_dir,
                                        quota_bytes,
                                        resume_records=rr
                                        and rr.get("c_reversal_plain"),
                                        resume_gen=rg),
        }
        set_spy_reference(spy)

    def run(self, names_iter, checkpoint_every: int = 256,
            guard=None, log=None):
        H = int(self.cell["params"]["H"])
        n_since = 0
        for sym, nm in names_iter:
            if self.names_done > 0:
                self.names_done -= 1
                continue
            pass_b_feed_name(self.books, self.cohort_counts,
                             self.rt_dates, self.ch_dates, self.picks,
                             self.calendar_index, self.fends, H,
                             STRESS_TIER, sym, nm)
            self.fed += 1
            n_since += 1
            if guard is not None:
                guard(f"pass_b:{sym}")
            if n_since >= checkpoint_every:
                self.save()
                if log:
                    log(f"pass B checkpoint at {sym}")
                n_since = 0
        self.save()

    def save(self) -> None:
        g = self.gen + 1
        for acc in self.books.values():
            acc.save_checkpoint(g)
        _atomic_json(self.ckpt, {
            "gen": g,
            "names_done": self.fed,
            "cohort_counts": self.cohort_counts,
            "writer_counts": {k: b.record_counts()
                              for k, b in self.books.items()},
        })
        self.gen = g

    def result(self) -> dict:
        return {"books": self.books,
                "c_cal_hist_report": self.ch_report,
                "reversal_stats": self.rev_stats,
                "counts_cohort": self.cohort_counts}
