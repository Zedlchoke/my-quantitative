"""V13 family runner (A8 lane): the sole selected family SFV13-A6-P1
(dividend-policy transition state, EODHD dividends family), built EXACTLY per
the frozen spec:

  - selection freeze : research/control/stocks_free_v13_run/selection_freeze.json
                       (family SFV13-A6-P1 ONLY; 3 arms; 3 cells of budget 6)
  - frozen spec      : research/control/stocks_free_v13_run/d1/proposals/
                       proposal_A6_P1.json
                       (sha256 c5958b96cb6fa5dec334f60020155dee08b7a73993429e6
                       743aaeae48f55ef7d per the selection freeze)
  - book invariants  : research/control/stocks_free_v13_run/p3_v13_invariants_
                       freeze.json (carried houses folds, band costs A/B/C
                       10/15/25 bps per side base, stress x2, diagnostic
                       output contract P-11, margins-to-fail P-2)

ARMS (frozen ids, one book each; identical machinery except the exposure
algebra / name assignment):
  SFV13-A6-H1-ANCHOR                            X_i(D) in {-1,0,+1} transition
                                                state, within-sector demeaned
                                                weights, gross 1.0 (0.5/leg)
  SFV13-A6-H1-NEIGHBOUR-PAYMENT-FREQUENCY-CHANGE  X' = paid_now - paid_prev
                                                (continuous integer), same
                                                everything else
  SFV13-A6-H1-CONTROL-WITHIN-SECTOR-PERMUTATION   anchor exposure values
                                                permuted within
                                                (decision-date, sector) cells
                                                by the frozen deterministic
                                                sha256 hex-sorted order

EXPOSURE STAGE reuses the ALREADY-TESTED D2 handler logic verbatim
(research/assets/stocks/d2_v13_proposal_handlers.py): a6_div_exposures builds
the anchor state from staged EODHD dividend records (ex-date evidence;
365/730 trailing existence windows; absence-assertable iff earliest staged
ex_date <= D-730 or the prior window holds >= 1 record) and
within_sector_hash_permutation_sham builds the control assignment.  The
neighbour's paid_now/paid_prev are computed here with the identical window
arithmetic and the identical absence gate (assertable iff paid_prev >= 1 OR
earliest <= D-730); the fixture tests cross-check the two implementations.

EXECUTION (frozen entry_exit_fills verbatim):
  - decision grid: the 30 frozen census dates; first three are declared
    warmup and ABSTAIN (27 scored dates: 7/10/10 across the carried folds).
  - eligibility at D (fail-closed, counted): >= 63 own-series bars strictly
    before D; ADV63 (median daily dollar volume through D-1) band C or
    better via kernel.band_of (UNTRADABLE excluded); RAW close >= 1.00 at
    D-1 (last bar strictly before D); assertable PIT state; mapped cohort
    sector tag (UNMAPPED excluded-with-reason, never guessed).
  - STRICT_NEXT_BAR: orders filled at the FIRST SESSION STRICTLY AFTER D on
    the union calendar, close-to-close; a name without a bar at the fill
    session simply does not fill (order does not exist; legs NOT
    renormalized - realized gross is reported).
  - holding one 21-session span in the FILLED entity's OWN trading sessions;
    dead names exit at their LAST recorded close (exit-at-last-close; the
    delisting return is carried by the series itself; no post-series price
    is ever read); any position still open at a fold boundary is force-flat
    at the fold's last session WITH cost (books are flat at every fold
    boundary by construction: each decision window self-contains its round
    trip).
  - costs via kernel_band_cost_v9 ONLY, linear in fills, charged EXACTLY
    ONCE PER SIDE (entry fill once, exit fill once); band resolution is
    FAIL-CLOSED (L-I3: BandResolutionError, silent 10 bps fallback
    forbidden); exits use resolve_exit_band_bps (C-rate ceiling when the
    exit band is unrateable).  Stress rerun = cost multiplier 2.0.
  - the per-decision thinning constant "at most one NEW position per
    21-session span" is structurally satisfied by the quarterly grid (63 >>
    21) and is declared, not filtered.

DIAGNOSTICS (P-11 / P-2, written under
research/control/stocks_free_v13_run/run/):
  per_period_series/{arm}__{BASE|STRESS}.json   per-period (decision-date)
    net returns per arm (DSR computable at terminal WITHOUT re-running);
    benchmark context: SPY-excess (arm return minus SPY scaled EX ANTE by
    the frozen gross rule 1.0) and equal-weight 11-SPDR sector benchmark
    (reported, not gated - no ETF legs in any arm).
  entity_legs/{arm}__{BASE|STRESS}.json         per-entity legs with
    fill-level cost lines (linear-in-fills proof), dead/alive split via the
    cohort class, exit reason per leg (SCHEDULED / DEAD_LEG /
    FOLD_FORCE_FLAT / VOID_NO_FILL); all costs are allocated to legs so
    per-period net return == sum of leg contributions EXACTLY and drop-one
    arithmetic is exact from persisted legs.
  family_verdicts.json                          per-gate margins per arm
    (P-2), counters, state-multiset permutation audit, pre-score
    self-subsumption rho (falsification rule 2).
  execution_ledger.json                         driver-emitted counters only
    (F-A7T-1), record-ID pairwise-distinctness proof, input digests.

DRY-RUN HYGIENE (P3): dry-run artifacts are sanitized - no arm return, no
PnL, no benchmark return is computed or emitted (PnL-derived gate margins
withheld); a recursive leak scan runs at every record depth over every
artifact before it is written (stress PnL leak class) and refuses the write
on any violation.  Record IDs are pairwise distinct across all arms and
variants (asserted, and proven in the ledger).

LOCK DISCIPLINE: the scored execution phase AND the dry-run both acquire the
machine-wide governance.heavy_lock (cycle STOCKS-FREE-V13, role A8_DRYRUN).
LockBusy -> stderr NOT_RUN_RESOURCE_CONFLICT, exit 3, single attempt.

AUTHORIZATION (two-key, P-8): the scored path refuses unless BOTH the exact
owner GO phrase "GO STOCKS V13 SCORED EXECUTION" is given AND the
environment flag STOCKS_V13_LAUNCH_AUTHORIZED=1 is set.  No wall-clock
timestamp is generated inside artifacts: built_at_utc is caller-provided.

NO GRID SEARCH anywhere: one window pair (365/730), one weight scale, one
hold (21 sessions), one floor per concept, one deterministic hash order.

AMBIGUITY RESOLUTIONS (documented, narrower than the frozen text; none
reinterprets a kill rule - all returned to A1 in the lane handoff):
  - "leg weights proportional to the demeaned exposure scaled by
    1.4826 * MAD ... normalized to gross 1.0 (0.5 per leg)": the MAD factor
    is a strictly positive constant per decision, so it cancels exactly
    under the frozen gross-1.0 normalization; the book is
    w_i = xd_i / sum_j |xd_j| (sum of positive weights = 0.5 = sum of
    |negative| weights).  The MAD-scaled intermediate is computed as
    xd_i / (1.4826 * MAD) whenever MAD > 0 and as xd_i when MAD = 0 (a
    majority-zero-state cross-section gives MAD 0; the identity scale keeps
    the same normalized book byte-for-byte).  Recorded per decision.
  - leg floor: "abstain if either leg < 5 names" is evaluated per scored
    decision date on the BOOK's two legs (all sectors pooled after
    within-sector demeaning), per expected_fold_population.per_date_floors.
  - ADV63 = MEDIAN daily dollar volume over the 63 bars strictly before D
    (the carried V8/V9 houses convention for "ADV63").
  - "RAW close >= 1.00 USD at D-1" = the raw close of the entity's last bar
    strictly before D.
  - bookable_pair_rule ("needs >= 1 priced bar in (prev(D), D]") is
    evaluated together with the eligibility gate; a name whose series has
    no bar at or after prev(D) is not bookable at D.
  - benchmark window: SPY / sector-EW are taken over [fill session, the
    union-calendar session 21 sessions after the fill, capped at the fold
    end] - the market-grid twin of the frozen per-name 21-own-session hold.

Usage (from the worktree ROOT, venv python only):
  python -m research.assets.stocks.v13_a6p1_family_runner --dry-run [built_at_utc]
  python -m research.assets.stocks.v13_a6p1_family_runner \
      'GO STOCKS V13 SCORED EXECUTION' [built_at_utc]   # + STOCKS_V13_LAUNCH_AUTHORIZED=1
Exit codes: 0 ok; 1 failed; 2 blocked/refused; 3 NOT_RUN_RESOURCE_CONFLICT;
4 CONTROL_STATE_DRIFT.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import os
import statistics
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from research.assets.stocks import kernel_band_cost_v9 as kernel
from research.assets.stocks.d2_v13_proposal_handlers import (
    A6_SCORED_GRID,
    A6_WARMUP_DECISIONS,
    CYCLE,
    DECISION_GRID_30,
    WAVE_SHA,
    _div_ex_dates,
    a6_div_exposures,
    within_sector_hash_permutation_sham,
)
from research.governance import heavy_lock

# ===========================================================================
# frozen identity + paths
# ===========================================================================
FAMILY_ID = "SFV13-A6-P1"
HYPOTHESIS_ID = "SFV13-A6-H1"
PROPOSAL_SHA256 = ("c5958b96cb6fa5dec334f60020155dee08b7a73993429e6743"
                   "aaeae48f55ef7d")

WORKTREE = Path(__file__).resolve().parents[3]
V9_ROOT = Path(os.environ.get(
    "V13_V9_ROOT",
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/integration"))
DIV_DIR = WORKTREE / ".staging_sec_v13" / "eodhd_div"
PRICE_DIR = V9_ROOT / ".staging_prices_v9" / "eod"
BENCH_DIR = V9_ROOT / ".staging_prices_v9" / "benchmarks"
COHORT_PATH = (V9_ROOT / "research" / "control" / "stocks_free_v9_run"
               / "cohort_v9.json")
PRICE_MANIFEST_PATH = (WORKTREE / "research" / "control" / "stocks_free_v13_run"
                       / "p0d_v13_price_manifest.json")
RUN_DIR = (WORKTREE / "research" / "control" / "stocks_free_v13_run" / "run")

# p3 carried houses folds, verbatim (book folds; the census fold-thirds is a
# census-reporting convention only, per p3 note_census_folds)
FOLDS = [
    {"fold_id": "S0_FOLD_1", "start": "2018-04-04", "end": "2020-09-01"},
    {"fold_id": "S0_FOLD_2", "start": "2020-09-10", "end": "2023-02-09"},
    {"fold_id": "S0_FOLD_3", "start": "2023-02-17", "end": "2025-07-24"},
]

# ===========================================================================
# frozen constants (proposal_A6_P1 + p3 invariants, verbatim values)
# ===========================================================================
NOW_WINDOW_DAYS = 365
PREV_WINDOW_DAYS = 730
HISTORY_BARS = 63
HOLD_SESSIONS = 21
MAD_SCALE = 1.4826
LEG_FLOOR = 5
COHORT_SCOREABLE_FLOOR = 30
OVERALL_FLOOR_SCORED = 30
PER_FOLD_FLOOR_SCORED = 5
TARGET_GROSS = 1.0
LEG_GROSS = 0.5
RAW_CLOSE_FLOOR = 1.00
SELF_SUBSUMPTION_RHO = 0.98
CONTROL_RATIO_KILL = 0.5
PF_THRESHOLD = 1.10
MDD_CARRIED_THRESHOLD = 0.20
MDD_PROPOSAL_THRESHOLD = 0.15
STRESS_MULTIPLIER = 2.0
SPY_EXCESS_FOLD_MIN = 2          # >= 2 of 3 folds
FOLDS_POSITIVE_MIN = 2           # >= 2 of 3 folds positive
SECTOR_ETFS = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE",
               "XLU", "XLV", "XLY"]

ARM_SPECS = {
    "SFV13-A6-H1-ANCHOR": {
        "role": "anchor",
        "exposure_form": "transition_state_pm1",
        "spec": ("X_i(D) = +1 initiation / -1 omission / 0 otherwise from "
                 "staged EODHD ex-dates (365/730 existence windows, "
                 "absence-assertability gate); within-sector demeaned "
                 "weights normalized to gross 1.0 (0.5 per leg)"),
    },
    "SFV13-A6-H1-NEIGHBOUR-PAYMENT-FREQUENCY-CHANGE": {
        "role": "neighbour",
        "exposure_form": "payment_count_change",
        "spec": ("X' = paid_now - paid_prev (continuous integer), computed "
                 "only where the state is assertable under the same absence "
                 "rule; identical machinery - exactly one thing changed"),
    },
    "SFV13-A6-H1-CONTROL-WITHIN-SECTOR-PERMUTATION": {
        "role": "control",
        "exposure_form": "within_sector_permutation",
        "spec": ("anchor exposure values permuted within (date, sector) by "
                 "sha256 of 'cycle|{hyp}|{cik}|{decision_index}' hex-sorted "
                 "(no RNG library); identical machinery"),
    },
}
ARM_IDS = tuple(sorted(ARM_SPECS))
VARIANT_BASE, VARIANT_STRESS = "BASE", "STRESS"

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BLOCKED = 2
EXIT_LOCK_BUSY = 3
EXIT_DRIFT = 4
LOCK_ROLE = "A8_DRYRUN"          # frozen instruction: dry-run also under lock
GO_PHRASE = "GO STOCKS V13 SCORED EXECUTION"
LAUNCH_ENV = "STOCKS_V13_LAUNCH_AUTHORIZED"

RECORD_SCHEMA = "stocks_free_v13_run/arm_record@1"
VERDICTS_SCHEMA = "stocks_free_v13_run/family_verdicts@1"
LEDGER_SCHEMA = "stocks_free_v13_run/execution_ledger@1"
SERIES_SCHEMA = "stocks_free_v13_run/per_period_series@1"
LEGS_SCHEMA = "stocks_free_v13_run/entity_legs@1"

# keys that must NEVER carry a non-null value in a dry-run artifact
# (stress PnL leak class; recursive scan at every record depth)
PNL_LEAK_KEYS = frozenset({
    "pnl", "pnl_contrib", "return", "return_net", "return_gross", "returns",
    "ret", "expectancy", "sum_pnl", "pf", "mdd", "spy_return",
    "sector_ew_return", "spy_excess", "metrics", "top_name_contribution",
})


def new_diag():
    return {
        "div_window_formation_abstains": 0,
        "div_entities_without_staged_file": 0,
        "div_unreadable_files": 0,
        "div_undated_records_excluded": 0,
        "missing_price_series": 0,
        "unmapped_sector_names": 0,
        "elig_untradable_at_decision": 0,
        "elig_raw_close_floor": 0,
        "elig_not_bookable_window": 0,
        "elig_state_missing": 0,
        "floor_abstain_cohort": 0,
        "floor_abstain_leg": 0,
        "floor_abstain_degenerate_scale": 0,
        "void_entry_orders": 0,
        "dead_leg_exits": 0,
        "fold_force_flat_exits": 0,
        "scheduled_exits": 0,
        "benchmark_missing_bars": 0,
        "benchmark_sector_files_missing": 0,
        "mad_zero_identity_scale_decisions": 0,
    }


# ===========================================================================
# data loaders (all take explicit paths; module constants are defaults only)
# ===========================================================================
def load_cohort(cohort_path=None):
    """The two frozen bookable legs ONLY: ALIVE_EVIDENCED (ticker) +
    DEAD_EVIDENCED (ticker_eodhd).  GAP_COVERAGE / NOT_DEAD_NAME_ALIVE never
    enter (excluded-with-reasons, recorded, never held)."""
    path = Path(cohort_path or COHORT_PATH)
    cohort = json.loads(path.read_text())
    members = cohort["members"]
    out = {}
    for m in members.get("ALIVE_EVIDENCED", []):
        out[m["cik"]] = {"sector": m.get("sector") or "",
                         "ticker": m.get("ticker") or "",
                         "status": "ALIVE_EVIDENCED"}
    for m in members.get("DEAD_EVIDENCED", []):
        out[m["cik"]] = {"sector": m.get("sector") or "",
                         "ticker": m.get("ticker_eodhd") or "",
                         "status": "DEAD_EVIDENCED"}
    return out


def load_dividends(div_dir=None, tickers=None):
    """{ticker: raw vendor record list} from the staged EODHD dividend
    arrays (the exact input contract of the tested D2 handler).  PRESENT-but-
    unreadable file -> None (the tested handler semantics: the entity
    abstains, counted); missing file -> key absent.  Ex-date extraction and
    the undated-record counter live INSIDE the handler/_div_ex_dates - this
    loader never pre-processes records."""
    root = Path(div_dir or DIV_DIR)
    out = {}
    names = sorted(tickers) if tickers else sorted(
        p.name[: -len(".json")] for p in root.glob("*.json"))
    for tkr in names:
        path = root / f"{tkr}.json"
        if not path.exists():
            continue                       # missing file -> no staged data
        try:
            recs = json.loads(path.read_text())
        except Exception:
            out[tkr] = None                # unreadable -> abstain (counted)
            continue
        out[tkr] = recs if isinstance(recs, list) else None
    return out


def _require(cond, msg):
    if not cond:
        raise ValueError(f"{msg} - fail closed")


def load_prices_v13(prices_dir=None, cohort=None):
    """{cik: {"date","raw","adj","dvol","pos","source_file"}} for cohort
    CIKs.  A PRESENT-but-malformed file FAILS CLOSED (ValueError): bad JSON,
    non-array, missing/non-numeric required keys, negative or NaN volume,
    non-strictly-increasing dates.  A cohort member with NO file is a
    measured exclusion (missing_price_series), never a guess."""
    root = Path(prices_dir or PRICE_DIR)
    out = {}
    for fn in sorted(os.listdir(root)):
        if not fn.endswith(".json"):
            continue
        cik = fn.split("__")[0]
        if cohort is not None and cik not in cohort:
            continue
        path = root / fn
        try:
            bars = json.loads(path.read_text())
        except Exception as exc:
            raise ValueError(f"malformed price file {fn}: {exc} - fail closed")
        _require(isinstance(bars, list) and len(bars) > 0,
                 f"malformed price file {fn}: not a non-empty bar array")
        dates, raw, adj, dvol = [], [], [], []
        prev = None
        for b in bars:
            _require(isinstance(b, dict), f"malformed price file {fn}: bar is not an object")
            try:
                d = str(b["date"])
                c = float(b["close"])
                a = float(b["adjusted_close"])
                v = float(b["volume"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"malformed price file {fn}: {exc} - fail closed")
            _require(d, f"malformed price file {fn}: empty date")
            _require(c == c and a == a and v == v and v >= 0.0,
                     f"malformed price file {fn}: NaN/negative value at {d}")
            _require(prev is None or d > prev,
                     f"malformed price file {fn}: dates not strictly increasing at {d}")
            prev = d
            dates.append(d)
            raw.append(c)
            adj.append(a)
            dvol.append(c * v)
        out[cik] = {"date": dates, "raw": raw, "adj": adj, "dvol": dvol,
                    "pos": {dd: i for i, dd in enumerate(dates)},
                    "source_file": fn}
    return out


def load_benchmarks(bench_dir=None):
    """{"SPY": series, "<ETF>": series} with {"date","adj","pos"};
    malformed benchmark files fail closed."""
    root = Path(bench_dir or BENCH_DIR)
    out = {}
    for tkr in ["SPY"] + SECTOR_ETFS:
        path = root / f"{tkr}.json"
        if not path.exists():
            continue
        try:
            bars = json.loads(path.read_text())
        except Exception as exc:
            raise ValueError(f"malformed benchmark file {tkr}.json: {exc}")
        _require(isinstance(bars, list) and bars,
                 f"malformed benchmark file {tkr}.json: empty")
        dates, adj = [], []
        prev = None
        for b in bars:
            d = str(b["date"])
            a = float(b["adjusted_close"])
            _require(prev is None or d > prev,
                     f"malformed benchmark file {tkr}.json: date order")
            prev = d
            dates.append(d)
            adj.append(a)
        out[tkr] = {"date": dates, "adj": adj,
                    "pos": {dd: i for i, dd in enumerate(dates)}}
    return out


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def verify_price_manifest(manifest_path=None, price_dir=None,
                          bench_dir=None, limit=None):
    """Verify staged file bytes against p0d_v13_price_manifest.json
    (per-file sha256).  Returns {"checked": n, "mismatches": [...],
    "missing": [...]}.  `limit` caps the sample size (deterministic: files
    in sorted manifest-key order); None verifies everything."""
    manifest = json.loads(Path(manifest_path or PRICE_MANIFEST_PATH).read_text())
    files = manifest["files"]
    roots = {"eod/": Path(price_dir or PRICE_DIR),
             "benchmarks/": Path(bench_dir or BENCH_DIR)}
    res = {"checked": 0, "mismatches": [], "missing": []}
    for key in sorted(files):
        if limit is not None and res["checked"] >= limit:
            break
        prefix = next((p for p in roots if key.startswith(p)), None)
        if prefix is None:
            continue
        path = roots[prefix] / key[len(prefix):]
        if not path.exists():
            res["missing"].append(key)
            continue
        res["checked"] += 1
        if sha256_file(path) != files[key]:
            res["mismatches"].append(key)
    return res


# ===========================================================================
# feature stage (identical arithmetic to the tested D2 handlers)
# ===========================================================================
def paid_windows(div_by_ticker, ticker_of, bookable, grid=None, diag=None):
    """{(cik, D): {"paid_now","paid_prev"}} on the SCORED grid for entities
    with an ASSERTABLE state.  Window arithmetic identical to the tested
    handler a6_div_exposures: paid_now = # ex-dates in [D-365, D);
    paid_prev = # in [D-730, D-365); assertable iff paid_prev >= 1 OR the
    entity's earliest staged ex_date <= D-730; otherwise the entity
    ABSTAINS (window-formation abstain).  The shared diag counters for
    abstains/undated records are OWNED by the anchor path (the handler,
    which runs first in build_world and applies the identical gate); this
    function keeps local throwaway counters so the abstain sets can never
    be double-counted."""
    diag = diag if diag is not None else new_diag()
    grid = grid if grid is not None else A6_SCORED_GRID
    out = {}
    for cik in sorted(bookable):
        tkr = ticker_of.get(cik)
        recs = div_by_ticker.get(tkr) if tkr else None
        if not recs:
            continue                       # counted by the anchor path
        ex = _div_ex_dates(recs, {"div_undated_records_excluded": 0})
        earliest = ex[0] if ex else None
        for d in grid:
            ddate = date.fromisoformat(d)
            lo_now = (ddate - timedelta(days=NOW_WINDOW_DAYS)).isoformat()
            lo_prev = (ddate - timedelta(days=PREV_WINDOW_DAYS)).isoformat()
            paid_now = sum(1 for s in ex if lo_now <= s < d)
            paid_prev = sum(1 for s in ex if lo_prev <= s < lo_now)
            assertable = paid_prev >= 1 or (earliest is not None
                                            and earliest <= lo_prev)
            if not assertable:
                continue                   # counted by the anchor path
            out[(cik, d)] = {"paid_now": paid_now, "paid_prev": paid_prev}
    return out


def neighbour_exposure(paid):
    """X' = paid_now - paid_prev (continuous integer-valued) at exactly the
    anchor's assertability set."""
    return {k: float(v["paid_now"] - v["paid_prev"]) for k, v in paid.items()}


# ===========================================================================
# eligibility + book construction (frozen)
# ===========================================================================
def decision_eligibility(prices, D, prev_D, diag=None):
    """Frozen eligibility gate at decision D.  Returns
    (eligible {cik: band}, bands_all {cik: band}) where bands_all covers
    every name with a computable band at D (fail-closed costing substrate).

    (i)   >= 63 own-series bars STRICTLY before D (history floor only);
    (ii)  band C or better: ADV63 = MEDIAN daily dollar volume through D-1
          (63 bars strictly before D); kernel.band_of; UNTRADABLE excluded;
    (iii) RAW close >= 1.00 at D-1 = the last bar strictly before D;
    (pair) >= 1 priced bar in (prev_D, D] (price-leg bookability).
    """
    diag = diag if diag is not None else new_diag()
    elig, bands = {}, {}
    for cik in sorted(prices):
        p = prices[cik]
        dates = p["date"]
        j = bisect.bisect_left(dates, D)          # bars strictly before D
        if j < HISTORY_BARS:
            continue
        if j - bisect.bisect_right(dates, prev_D) < 1:
            diag["elig_not_bookable_window"] += 1
            continue
        adv = statistics.median(p["dvol"][j - HISTORY_BARS: j])
        b = kernel.band_of(adv)
        bands[cik] = b
        if b == "UNTRADABLE":
            diag["elig_untradable_at_decision"] += 1
            continue
        if p["raw"][j - 1] < RAW_CLOSE_FLOOR:
            diag["elig_raw_close_floor"] += 1
            continue
        elig[cik] = b
    return elig, bands


def demean_within_sector(exposure_at_d, sector_of):
    """Within-sector demeaned exposure xd_i = X_i - mean_sector(X)."""
    by_sec = {}
    for cik in sorted(exposure_at_d):
        by_sec.setdefault(sector_of[cik], []).append(cik)
    xd = {}
    for sec in sorted(by_sec):
        names = by_sec[sec]
        mean = sum(exposure_at_d[c] for c in names) / len(names)
        for c in names:
            xd[c] = exposure_at_d[c] - mean
    return xd


def build_book(exposure_at_d, sector_of, diag=None):
    """Frozen book form at one decision date.  Within-sector demean; robust
    MAD scale; weights proportional to the scaled demeaned exposure,
    NORMALIZED TO GROSS 1.0 (0.5 per leg): w_i = scaled_i / sum_j |scaled_j|
    (the strictly positive MAD constant cancels under normalization - see
    module docstring ambiguity note).  Floors fail-closed:
      < 30 mapped-sector assertable exposures -> COHORT_FLOOR abstain;
      either leg < 5 names -> LEG_FLOOR abstain; MAD = 0 (a majority-zero
    cross-section) uses the identity scale, counted.  Returns
    ({cik: weight} , "OK") or (None, reason)."""
    diag = diag if diag is not None else new_diag()
    scoreable = {c: v for c, v in exposure_at_d.items() if sector_of.get(c)}
    if len(scoreable) < COHORT_SCOREABLE_FLOOR:
        diag["floor_abstain_cohort"] += 1
        return None, "COHORT_FLOOR"
    xd = demean_within_sector(scoreable, sector_of)
    vals = [xd[c] for c in sorted(xd)]
    med = statistics.median(vals)
    mad = statistics.median([abs(v - med) for v in vals])
    if mad > 0.0:
        scaled = {c: xd[c] / (MAD_SCALE * mad) for c in xd}
    else:
        diag["mad_zero_identity_scale_decisions"] += 1
        scaled = dict(xd)
    longs = [c for c in scaled if scaled[c] > 0.0]
    shorts = [c for c in scaled if scaled[c] < 0.0]
    if len(longs) < LEG_FLOOR or len(shorts) < LEG_FLOOR:
        diag["floor_abstain_leg"] += 1
        return None, "LEG_FLOOR"
    denom = sum(abs(v) for v in scaled.values())
    w = {c: scaled[c] / denom for c in sorted(scaled) if scaled[c] != 0.0}
    return w, "OK"


def state_multiset_by_sector(anchor_exposure, sector_of):
    """Per (scored date, sector) multiset of anchor states - the permutation
    audit substrate (diagnostic_commitments.additional_declared)."""
    audit = {}
    for (cik, d), v in sorted(anchor_exposure.items()):
        sec = sector_of.get(cik, "")
        cell = audit.setdefault(d, {}).setdefault(sec, {"plus1": 0, "zero": 0,
                                                        "minus1": 0})
        if v > 0:
            cell["plus1"] += 1
        elif v < 0:
            cell["minus1"] += 1
        else:
            cell["zero"] += 1
    return audit


# ===========================================================================
# execution (STRICT_NEXT_BAR, 21 own-session hold, once-per-side costs)
# ===========================================================================
def _bench_return(series, start_d, end_d, diag):
    """Benchmark adjusted-close return over [start_d, end_d]; None + counted
    when either exact bar is missing (no interpolation ever)."""
    si = series["pos"].get(start_d)
    ei = series["pos"].get(end_d)
    if si is None or ei is None or ei <= si:
        diag["benchmark_missing_bars"] += 1
        return None
    return series["adj"][ei] / series["adj"][si] - 1.0


def execute_decision(book_w, prices, bands, D, fold, global_days, day_pos,
                     cost_mult, dry_run, bench=None, sector_ew=None, diag=None):
    """One decision's round trip.  Returns (period_row, leg_rows).

    STRICT_NEXT_BAR: fill at the FIRST union-calendar session strictly after
    D; a name without a bar there does not fill (order does not exist, legs
    NOT renormalized).  Hold 21 OWN sessions; exit capped at the fold's last
    session (FOLD_FORCE_FLAT, with cost) and at the series' last recorded
    close (DEAD_LEG, exit-at-last-close, with cost).  Costs charged EXACTLY
    once per side via the kernel (entry resolve_band_bps fail-closed; exit
    resolve_exit_band_bps).  Returns/PnL computed ONLY when not dry_run.
    """
    diag = diag if diag is not None else new_diag()
    fill_d = (global_days[day_pos[D] + 1]
              if day_pos[D] + 1 < len(global_days) else None)
    fold_end = fold["end"]
    period = {
        "decision_date": D,
        "fill_date": fill_d,
        "fold": fold["fold_id"],
        "target_gross": round(TARGET_GROSS, 10),
        "realized_gross": 0.0,
        "legs_target": len(book_w),
        "legs_filled": 0,
        "void_orders": 0,
        "dead_legs": 0,
        "force_flats": 0,
        "scheduled_exits": 0,
        "cost_bps_paid": 0.0,
        "return_net": None,
        "spy_return": None,
        "sector_ew_return": None,
        "spy_excess": None,
    }
    if fill_d is None or fill_d > fold_end:
        period["event"] = "FILL_BEYOND_FOLD_END"
        return period, []
    legs = []
    ret_total = 0.0
    cost_total = 0.0
    for cik in sorted(book_w):
        w = book_w[cik]
        p = prices.get(cik)
        fi = p["pos"].get(fill_d) if p else None
        leg = {
            "record_id": None,          # assigned by the caller (arm+variant)
            "decision_date": D,
            "fill_date": fill_d,
            "fold": fold["fold_id"],
            "entity": cik,
            "target_weight": w,
            "filled": fi is not None,
            "exit_date": None,
            "exit_reason": None,
            "hold_sessions": None,
            "entry_band": bands.get(cik),
            "entry_cost_bps": None,
            "exit_cost_bps": None,
            "ret": None,
            "pnl_contrib": None,
        }
        if fi is None:
            period["void_orders"] += 1
            diag["void_entry_orders"] += 1
            leg["exit_reason"] = "VOID_NO_FILL"
            legs.append(leg)
            continue
        entry_cost = (abs(w) * kernel.resolve_band_bps(cik, bands)
                      * cost_mult / 10_000.0)
        target_ei = fi + HOLD_SESSIONS
        cap_i = min(bisect.bisect_right(p["date"], fold_end) - 1,
                    len(p["date"]) - 1)
        ei = min(target_ei, cap_i)
        if ei == target_ei:
            exit_reason = "SCHEDULED"
            period["scheduled_exits"] += 1
            diag["scheduled_exits"] += 1
        elif cap_i == len(p["date"]) - 1:
            # the series itself ended inside the hold window: exit at the
            # LAST recorded close; the delisting return is carried by the
            # series; no post-series price is read or synthesized
            exit_reason = "DEAD_LEG"
            period["dead_legs"] += 1
            diag["dead_leg_exits"] += 1
        else:
            exit_reason = "FOLD_FORCE_FLAT"
            period["force_flats"] += 1
            diag["fold_force_flat_exits"] += 1
        exit_cost = (abs(w) * kernel.resolve_exit_band_bps(cik, bands)
                     * cost_mult / 10_000.0)
        realized_ret = None
        if not dry_run:
            realized_ret = p["adj"][ei] / p["adj"][fi] - 1.0
            ret_total += w * realized_ret
            leg["ret"] = realized_ret
            leg["pnl_contrib"] = (w * realized_ret - entry_cost - exit_cost)
        period["realized_gross"] += abs(w)
        period["legs_filled"] += 1
        cost_total += entry_cost + exit_cost
        period["cost_bps_paid"] += (entry_cost + exit_cost) * 1e4
        leg["exit_date"] = p["date"][ei]
        leg["exit_reason"] = exit_reason
        leg["hold_sessions"] = ei - fi
        leg["entry_cost_bps"] = entry_cost * 1e4
        leg["exit_cost_bps"] = exit_cost * 1e4
        legs.append(leg)
    period["realized_gross"] = round(period["realized_gross"], 10)
    period["cost_bps_paid"] = round(period["cost_bps_paid"], 6)
    if not dry_run:
        period["return_net"] = ret_total - cost_total
        if bench and "SPY" in bench:
            b_end = min(day_pos[fill_d] + HOLD_SESSIONS, len(global_days) - 1)
            end_d = global_days[b_end]
            if end_d > fold_end:
                end_d = global_days[bisect.bisect_right(global_days, fold_end) - 1]
            spy = _bench_return(bench["SPY"], fill_d, end_d, diag)
            period["spy_return"] = spy
            ews = [_bench_return(series, fill_d, end_d, diag)
                   for name, series in sorted((sector_ew or {}).items())]
            defined = [r for r in ews if r is not None]
            period["sector_ew_return"] = (sum(defined) / len(defined)
                                          if defined else None)
            if spy is not None:
                # SPY scaled EX ANTE by the arm's frozen gross rule (1.0)
                period["spy_excess"] = period["return_net"] - TARGET_GROSS * spy
    return period, legs


# ===========================================================================
# arm simulation
# ===========================================================================
def run_arm(arm_id, exposure, prices, cohort, global_days, day_pos,
            scored_grid=None, folds=None, dry_run=True, stress=False,
            bench=None, sector_ew=None, diag=None):
    """Simulate one arm over the scored grid.  exposure: {(cik, D): value}
    (anchor states, neighbour count-change, or the permuted control).
    dry_run=True emits STRUCTURE ONLY (no return/PnL/benchmark anywhere)."""
    diag = diag if diag is not None else new_diag()
    scored_grid = scored_grid if scored_grid is not None else A6_SCORED_GRID
    folds = folds if folds is not None else FOLDS
    spec = ARM_SPECS[arm_id]
    cost_mult = STRESS_MULTIPLIER if stress else 1.0
    variant = VARIANT_STRESS if stress else VARIANT_BASE
    arm_diag = new_diag()     # per-arm counters: snapshots stay exact (the
    sector_of = {c: v["sector"] for c, v in cohort.items()}   # shared world
    status_of = {c: v["status"] for c, v in cohort.items()}   # diag is merged
    prev_of = {d: (DECISION_GRID_30[i - 1] if i > 0 else None)  # at the end)
               for i, d in enumerate(DECISION_GRID_30)}

    schedule = []
    legs_all = []
    periods = []
    for fold in folds:
        for D in scored_grid:
            if not (fold["start"] <= D <= fold["end"]):
                continue
            prev_d = prev_of.get(D)
            elig, bands = decision_eligibility(prices, D, prev_d, arm_diag)
            exposure_at_d = {}
            for c in elig:
                if (c, D) in exposure:
                    if sector_of.get(c):
                        exposure_at_d[c] = exposure[(c, D)]
                    else:
                        arm_diag["unmapped_sector_names"] += 1
                else:
                    arm_diag["elig_state_missing"] += 1
            book_w, reason = build_book(exposure_at_d, sector_of, arm_diag)
            if book_w is None:
                schedule.append({
                    "record_id": f"{arm_id}|{variant}|FLOOR|{D}",
                    "decision_date": D, "fold": fold["fold_id"],
                    "event": f"FLOOR_ABSTAIN_{reason}",
                    "eligible": len(elig),
                    "scoreable": len(exposure_at_d),
                })
                # P-11 diagnostic contract: EVERY scored date appears in the
                # per-period series (an abstained date is a 0.0 net return
                # when scored; dry-run keeps structure only). Otherwise the
                # terminal DSR is computed on an action-conditional subset.
                periods.append({
                    "record_id": f"{arm_id}|{variant}|D|{D}",
                    "decision_date": D, "fold": fold["fold_id"],
                    "abstained": reason,
                    "return_net": None if dry_run else 0.0,
                    "spy_return": None if dry_run else None,
                    "sector_ew_return": None,
                    "spy_excess": None,
                    "legs_long": 0, "legs_short": 0,
                    "cost_bps_paid": 0.0,
                })
                continue
            period, legs = execute_decision(
                book_w, prices, bands, D, fold, global_days, day_pos,
                cost_mult, dry_run, bench=bench, sector_ew=sector_ew,
                diag=arm_diag)
            for leg in legs:
                leg = dict(leg)
                leg["record_id"] = f"{arm_id}|{variant}|LEG|{D}|{leg['entity']}"
                leg["sector"] = sector_of.get(leg["entity"], "")
                leg["cohort_class"] = status_of.get(leg["entity"], "")
                legs_all.append(leg)
            period["record_id"] = f"{arm_id}|{variant}|D|{D}"
            period["legs_long"] = sum(1 for w in book_w.values() if w > 0)
            period["legs_short"] = sum(1 for w in book_w.values() if w < 0)
            periods.append(period)
            schedule.append({
                "record_id": period["record_id"],
                "decision_date": D, "fill_date": period["fill_date"],
                "fold": fold["fold_id"], "event": "DECISION",
                "eligible": len(elig), "scoreable": len(exposure_at_d),
                "legs_target": period["legs_target"],
                "legs_filled": period["legs_filled"],
                "legs_long": period["legs_long"],
                "legs_short": period["legs_short"],
                "void_orders": period["void_orders"],
                "realized_gross": period["realized_gross"],
                "cost_bps_paid": period["cost_bps_paid"],
            })

    record = {
        "schema": RECORD_SCHEMA,
        "family_id": FAMILY_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "arm_id": arm_id,
        "role": spec["role"],
        "exposure_form": spec["exposure_form"],
        "arm_spec": spec["spec"],
        "variant": variant,
        "cost_multiplier": cost_mult,
        "dry_run": dry_run,
        "scored": not dry_run,
        "stress": stress,
        "grid": {"scored_dates": len(scored_grid),
                 "warmup_decisions": A6_WARMUP_DECISIONS,
                 "first_scored": scored_grid[0],
                 "frozen_scored_dates": len(A6_SCORED_GRID),
                 "folds": {f["fold_id"]: [f["start"], f["end"]]
                           for f in folds}},
        "hold_sessions": HOLD_SESSIONS,
        "target_gross": TARGET_GROSS,
        "counters": {
            "decisions_scheduled": sum(
                1 for s in schedule if s["event"] == "DECISION"),
            "floor_abstains": sum(
                1 for s in schedule if s["event"].startswith("FLOOR_ABSTAIN")),
            "void_entry_orders": arm_diag["void_entry_orders"],
            "dead_leg_exits": arm_diag["dead_leg_exits"],
            "fold_force_flat_exits": arm_diag["fold_force_flat_exits"],
            "scheduled_exits": arm_diag["scheduled_exits"],
        },
        "schedule": schedule,
    }
    for k, v in arm_diag.items():     # merge into the shared world diag
        diag[k] = diag.get(k, 0) + v
    if not dry_run:
        record["metrics"] = arm_metrics(periods, legs_all)
    return record, periods, legs_all


def arm_metrics(periods, legs):
    """Per-arm scored metrics from the per-period net-return series and the
    per-entity legs (exact drop-one arithmetic; costs are allocated to
    legs)."""
    scored = [p for p in periods if p.get("return_net") is not None]
    rets = [p["return_net"] for p in scored]
    n = len(rets)
    e_sum = sum(rets)
    wins = sum(r for r in rets if r > 0)
    losses = -sum(r for r in rets if r < 0)
    folds_order = []
    for p in scored:
        if p["fold"] not in folds_order:
            folds_order.append(p["fold"])
    fold_rows = {}
    for fid in folds_order:
        fr = [p["return_net"] for p in scored if p["fold"] == fid]
        cum = peak = mdd = 0.0
        for r in fr:
            cum += r
            peak = max(peak, cum)
            mdd = max(mdd, peak - cum)
        fw = sum(r for r in fr if r > 0)
        fl = -sum(r for r in fr if r < 0)
        fold_rows[fid] = {"decisions": len(fr), "sum_pnl": round(sum(fr), 10),
                          "pf": round(fw / fl, 6) if fl > 0 else None,
                          "mdd": round(mdd, 10)}
    cum = peak = mdd_overall = 0.0
    for r in rets:
        cum += r
        peak = max(peak, cum)
        mdd_overall = max(mdd_overall, peak - cum)
    spy_ex = [(p["decision_date"], p["spy_excess"], p["fold"])
              for p in scored if p.get("spy_excess") is not None]
    spy_excess_overall = (sum(x[1] for x in spy_ex) / len(spy_ex)
                          if spy_ex else None)
    spy_folds = {}
    for fid in folds_order:
        vals = [x[1] for x in spy_ex if x[2] == fid]
        if vals:
            spy_folds[fid] = sum(vals) / len(vals)
    sector_ews = [p["sector_ew_return"] for p in scored
                  if p.get("sector_ew_return") is not None]
    # ---- exact drop-one arithmetic from persisted legs ---------------------
    n_periods = n
    total_contrib = 0.0
    by_sym = {}
    by_fold = {}
    for leg in legs:
        c = leg.get("pnl_contrib")
        if c is None:
            continue
        total_contrib += c
        by_sym[leg["entity"]] = by_sym.get(leg["entity"], 0.0) + c
        by_fold[leg["fold"]] = by_fold.get(leg["fold"], 0.0) + c
    drop_sym = {}
    for sym, c in sorted(by_sym.items()):
        drop_sym[sym] = ((total_contrib - c) / n_periods
                         if n_periods else None)
    drop_fold = {}
    for fid, c in sorted(by_fold.items()):
        drop_fold[fid] = ((total_contrib - c) / n_periods
                          if n_periods else None)
    return {
        "scored_periods": n,
        "expectancy": round(e_sum / n, 12) if n else None,
        "sum_pnl": round(e_sum, 10),
        "pf": round(wins / losses, 6) if losses > 0 else None,
        "max_fold_mdd": round(max((f["mdd"] for f in fold_rows.values()),
                                  default=0.0), 10),
        "mdd_overall_cum": round(mdd_overall, 10),
        "folds": fold_rows,
        "folds_positive": sum(1 for f in fold_rows.values()
                              if f["sum_pnl"] > 0),
        "spy_excess_overall": (round(spy_excess_overall, 12)
                               if spy_excess_overall is not None else None),
        "spy_excess_folds": {k: round(v, 12) for k, v in spy_folds.items()},
        "spy_excess_folds_positive": sum(1 for v in spy_folds.values()
                                         if v > 0),
        "sector_ew_mean": (round(sum(sector_ews) / len(sector_ews), 12)
                           if sector_ews else None),
        "dead_legs_total": sum(1 for l in legs
                               if l.get("exit_reason") == "DEAD_LEG"),
        "alive_legs_total": sum(1 for l in legs
                                if l.get("cohort_class") == "ALIVE_EVIDENCED"),
        "dead_class_legs_total": sum(
            1 for l in legs if l.get("cohort_class") == "DEAD_EVIDENCED"),
        "drop_one_symbol_expectancy_min": (
            round(min(drop_sym.values()), 12) if drop_sym and n_periods
            else None),
        "drop_one_fold_expectancy_min": (
            round(min(drop_fold.values()), 12) if drop_fold and n_periods
            else None),
        "drop_one_symbol_worst": (min(drop_sym, key=drop_sym.get)
                                  if drop_sym and n_periods else None),
    }


# ===========================================================================
# gates (P-2 margins per gate per arm)
# ===========================================================================
def gate_row(name, ok, observed, threshold, direction, basis=""):
    num = isinstance(observed, (int, float)) and not isinstance(observed, bool)
    if num and isinstance(threshold, (int, float)):
        margin = (round(observed - threshold, 8) if direction in ("gt", "ge")
                  else round(threshold - observed, 8))
    else:
        margin = None
    return {"gate": name, "verdict": "PASS" if ok else "FAIL",
            "observed": observed, "threshold": threshold,
            "direction": direction, "margin_to_fail": margin,
            "basis": basis}


def _pf_gate(metrics, threshold, name, basis):
    """PF >= threshold; a metrics dict with NO losing period has PF = +inf
    (undefined division) and trivially clears the gate - reported with
    observed None and margin None rather than a fake number."""
    pf = metrics.get("pf")
    n = metrics.get("scored_periods", 0)
    if pf is None:
        ok = n > 0                       # no losing period at all
    else:
        ok = pf >= threshold
    return gate_row(name, ok, pf, threshold, "ge", basis + "; PF undefined "
                    "(no losing periods) passes as +inf")


def arm_gates(base_record, stress_record, diag=None):
    """Frozen Stage-A gate family per arm with margins (P-2).  Stress rows
    read the STRESS rerun's metrics (stress x2 on booked PnL)."""
    diag = diag if diag is not None else new_diag()
    m = base_record["metrics"]
    s = stress_record["metrics"]
    rows = [
        gate_row("expectancy_gt_0_after_base_costs", m["expectancy"] > 0,
                 m["expectancy"], 0.0, "gt",
                 "frozen rule (3): anchor expectancy <= 0 after base band "
                 "costs -> REJECT"),
        _pf_gate(m, PF_THRESHOLD, "position_pf_ge_1.10",
                 "frozen Stage-A position PF gate"),
        gate_row("folds_positive_ge_2_of_3",
                 m["folds_positive"] >= FOLDS_POSITIVE_MIN,
                 m["folds_positive"], FOLDS_POSITIVE_MIN, "ge"),
        gate_row("max_fold_mdd_le_0.20_houses_carried",
                 m["max_fold_mdd"] <= MDD_CARRIED_THRESHOLD,
                 m["max_fold_mdd"], MDD_CARRIED_THRESHOLD, "le",
                 "carried houses gate per selection_freeze.stage_a_gates"),
        gate_row("max_fold_mdd_le_0.15_proposal_table",
                 m["max_fold_mdd"] <= MDD_PROPOSAL_THRESHOLD,
                 m["max_fold_mdd"], MDD_PROPOSAL_THRESHOLD, "le",
                 "proposal stage_a_gate_expectations declares 0.15; BOTH "
                 "thresholds reported, adjudication returned to A1"),
        gate_row("spy_excess_overall_gt_0",
                 m["spy_excess_overall"] is not None
                 and m["spy_excess_overall"] > 0, m["spy_excess_overall"],
                 0.0, "gt", "risk-matched SPY-excess, SPY scaled ex ante by "
                 "the frozen gross rule 1.0"),
        gate_row("spy_excess_folds_ge_2_of_3",
                 m["spy_excess_folds_positive"] >= SPY_EXCESS_FOLD_MIN,
                 m["spy_excess_folds_positive"], SPY_EXCESS_FOLD_MIN, "ge"),
        gate_row("etf_share_le_0.50", True, 0.0, 0.50, "le",
                 "NOT_APPLICABLE ex ante (preregistered): no ETF legs in "
                 "any arm"),
        gate_row("stress_pnl_gt_0", s["sum_pnl"] > 0, s["sum_pnl"], 0.0,
                 "gt", "frozen rule (5): stress x2 PnL <= 0 -> dead"),
        _pf_gate(s, 1.0, "stress_pf_ge_1.0",
                 "frozen rule (5): stress PF < 1.0 -> dead"),
        gate_row("drop_one_symbol_min_expectancy_gt_0",
                 m["drop_one_symbol_expectancy_min"] is not None
                 and m["drop_one_symbol_expectancy_min"] > 0,
                 m["drop_one_symbol_expectancy_min"], 0.0, "gt",
                 "frozen rule (6), symbol dimension; exact arithmetic from "
                 "persisted per-entity legs (costs allocated to legs)"),
        gate_row("drop_one_fold_min_expectancy_gt_0",
                 m["drop_one_fold_expectancy_min"] is not None
                 and m["drop_one_fold_expectancy_min"] > 0,
                 m["drop_one_fold_expectancy_min"], 0.0, "gt",
                 "frozen rule (6), fold dimension"),
    ]
    floors = floor_gate_rows(base_record, scored_floor=OVERALL_FLOOR_SCORED,
                             per_fold_floor=PER_FOLD_FLOOR_SCORED)
    return rows + floors


def floor_gate_rows(record, scored_floor, per_fold_floor):
    """FLOORS gate rows from the arm's schedule (rule (8): any floor abstained
    under count -> INFEASIBLE; declared terminal, never a reduced book)."""
    sched = record["schedule"]
    decisions = [s for s in sched if s["event"] == "DECISION"]
    floors = [s for s in sched if s["event"].startswith("FLOOR_ABSTAIN")]
    min_scoreable = min((s["scoreable"] for s in decisions), default=0)
    min_legs = min((min(s["legs_long"], s["legs_short"]) for s in decisions),
                   default=0)
    fold_counts = {}
    for s in decisions:
        fold_counts[s["fold"]] = fold_counts.get(s["fold"], 0) + 1
    min_fold = min(fold_counts.values(), default=0)
    return [
        gate_row("floor_cohort_scoreable_ge_30_every_scored_date",
                 min_scoreable >= COHORT_SCOREABLE_FLOOR and not floors,
                 min_scoreable, COHORT_SCOREABLE_FLOOR, "ge",
                 f"floor abstains recorded: {len(floors)}"),
        gate_row("floor_legs_ge_5_every_scored_date",
                 min_legs >= LEG_FLOOR and not floors, min_legs, LEG_FLOOR,
                 "ge"),
        gate_row("scored_decisions_overall_ge_30",
                 len(decisions) >= scored_floor, len(decisions), scored_floor,
                 "ge"),
        gate_row("scored_decisions_per_fold_ge_5",
                 min_fold >= per_fold_floor, min_fold, per_fold_floor, "ge"),
    ]


def spearman_rho(xs, ys):
    """Pooled Spearman rho with average ranks for ties (rule (2)
    self-subsumption and the D2-declared identifiability arithmetic)."""
    def ranks(vs):
        order = sorted(range(len(vs)), key=lambda i: vs[i])
        out = [0.0] * len(vs)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vs[order[j + 1]] == vs[order[i]]:
                j += 1
            avg = (i + j) / 2.0
            for k in range(i, j + 1):
                out[order[k]] = avg
            i = j + 1
        n = len(vs)
        mean = (n - 1) / 2.0
        return [r - mean for r in out]
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    rx, ry = ranks(xs), ranks(ys)
    num = sum(a * b for a, b in zip(rx, ry))
    den = (sum(a * a for a in rx) * sum(b * b for b in ry)) ** 0.5
    return num / den if den else None


def control_ratio_block(anchor_expectancy, control_expectancy):
    """Frozen falsification rule (1): control reproduction -> DEAD iff
    same-sign and |c| >= 0.5|a|, INCLUDING the negative-anchor case (the
    control never outruns a negative anchor)."""
    a, c = anchor_expectancy, control_expectancy
    if a is None or c is None or a == 0.0:
        return {"observed_ratio": None, "kill": False,
                "note": "anchor expectancy zero/undefined; ratio undefined"}
    same_sign = (a > 0 and c > 0) or (a < 0 and c < 0)
    ratio = c / a
    kill = False
    margin = None
    if same_sign:
        kill = abs(c) >= CONTROL_RATIO_KILL * abs(a)
        margin = round(CONTROL_RATIO_KILL * abs(a) - abs(c), 12)
    elif a < 0 and c < a:
        kill = True                      # control outruns a negative anchor
        margin = round(c - a, 12)
    return {"observed_ratio": round(ratio, 8), "same_sign": same_sign,
            "kill": kill, "margin_to_fail": margin,
            "rule": "same-sign >= 0.5x kills (incl. negative-anchor case)"}


# ===========================================================================
# dry-run hygiene: recursive PnL leak scan (stress PnL leak class)
# ===========================================================================
def scan_no_pnl(obj, path="$"):
    """Recursively walk `obj` at EVERY record depth; return the list of
    violations (PnL-class keys carrying a non-null value)."""
    bad = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}"
            if k in PNL_LEAK_KEYS and v is not None:
                bad.append(p)
            bad.extend(scan_no_pnl(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad.extend(scan_no_pnl(v, f"{path}[{i}]"))
    return bad


def collect_record_ids(arm_records):
    ids = []
    for rec in arm_records:
        for row in rec["schedule"]:
            ids.append(row["record_id"])
    return ids


# ===========================================================================
# world assembly + artifact writers
# ===========================================================================
def build_world(cohort_path=None, div_dir=None, prices_dir=None,
                bench_dir=None, diag=None):
    diag = diag if diag is not None else new_diag()
    cohort = load_cohort(cohort_path)
    ticker_of = {c: v["ticker"] for c, v in cohort.items()}
    divs = load_dividends(div_dir,
                          tickers={v["ticker"] for v in cohort.values()
                                   if v["ticker"]})
    prices = load_prices_v13(prices_dir, cohort=cohort)
    diag["missing_price_series"] = len(set(cohort) - set(prices))
    diag["unmapped_sector_names"] = sum(
        1 for v in cohort.values() if not v["sector"])
    bench = load_benchmarks(bench_dir)
    sector_ew = {k: bench[k] for k in SECTOR_ETFS if k in bench}
    diag["benchmark_sector_files_missing"] = sum(
        1 for k in SECTOR_ETFS if k not in bench)
    # anchor via the TESTED D2 handler (full 30-date grid; it emits the 27
    # scored dates only - the three warmup dates abstain per the clock)
    anchor = a6_div_exposures(divs, ticker_of, cohort, DECISION_GRID_30, diag)
    paid = paid_windows(divs, ticker_of, cohort, A6_SCORED_GRID, diag)
    neighbour = neighbour_exposure(paid)
    control = within_sector_hash_permutation_sham(anchor, cohort,
                                                  HYPOTHESIS_ID)
    exposures = {
        "SFV13-A6-H1-ANCHOR": anchor,
        "SFV13-A6-H1-NEIGHBOUR-PAYMENT-FREQUENCY-CHANGE": neighbour,
        "SFV13-A6-H1-CONTROL-WITHIN-SECTOR-PERMUTATION": control,
    }
    global_days = sorted({d for p in prices.values() for d in p["date"]})
    day_pos = {d: i for i, d in enumerate(global_days)}
    return {"cohort": cohort, "prices": prices, "bench": bench,
            "sector_ew": sector_ew, "exposures": exposures,
            "global_days": global_days, "day_pos": day_pos, "diag": diag}


def run_family(world, dry_run=True, scored_grid=None, folds=None):
    """Three arms x (base + stress x2 rerun) -> verdicts, series, legs.
    scored_grid/folds default to the frozen census grid and carried houses
    folds; tests inject synthetic schedules (never production bytes)."""
    diag = world["diag"]
    arm_records = {}
    series = {}
    legs_by = {}
    for arm_id in ARM_IDS:
        exposure = world["exposures"][arm_id]
        for stress in (False, True):
            rec, periods, legs = run_arm(
                arm_id, exposure, world["prices"], world["cohort"],
                world["global_days"], world["day_pos"], dry_run=dry_run,
                stress=stress, bench=world["bench"],
                sector_ew=world["sector_ew"], diag=diag,
                scored_grid=scored_grid, folds=folds)
            variant = rec["variant"]
            arm_records.setdefault(arm_id, {})[variant] = rec
            series[(arm_id, variant)] = periods
            legs_by[(arm_id, variant)] = legs
    return arm_records, series, legs_by


def family_gate_blocks(arm_records, world):
    """Family-level falsification arithmetic (rules (1) and (2)) + the
    pre-score self-subsumption rho."""
    a_id = "SFV13-A6-H1-ANCHOR"
    c_id = "SFV13-A6-H1-CONTROL-WITHIN-SECTOR-PERMUTATION"
    a_exp = world["exposures"][a_id]
    c_exp = world["exposures"][c_id]
    common = sorted(set(a_exp) & set(c_exp))
    rho = (spearman_rho([a_exp[k] for k in common],
                        [c_exp[k] for k in common]) if common else None)
    a_exp_m = arm_records[a_id][VARIANT_BASE].get("metrics", {})
    c_exp_m = arm_records[c_id][VARIANT_BASE].get("metrics", {})
    ratio = control_ratio_block(a_exp_m.get("expectancy"),
                                c_exp_m.get("expectancy"))
    return {
        "self_subsumption": {
            "pooled_spearman_rho": (round(rho, 8) if rho is not None
                                    else None),
            "pairs": len(common),
            "threshold": SELF_SUBSUMPTION_RHO,
            "kill": rho is not None and rho > SELF_SUBSUMPTION_RHO,
            "rule": "rule (2): pooled rho > 0.98 -> DESIGN FAILURE "
                    "(killed PRE-SCORE; the sham was not executed as "
                    "declared)",
        },
        "control_reproduction": ratio,
    }


def write_artifacts(run_dir, built_at_utc, mode, arm_records, series,
                    legs_by, world, family_gates):
    """Persist the P-11 diagnostic contract under run_dir.  Dry-run
    artifacts are leak-scanned at every record depth BEFORE the write; any
    PnL-class leak refuses the whole write (fail closed)."""
    run_dir = Path(run_dir)
    series_dir = run_dir / "per_period_series"
    legs_dir = run_dir / "entity_legs"
    artifacts = []

    def _emit(rel, payload):
        artifacts.append(rel)
        if mode == "dry_run":
            bad = scan_no_pnl(payload, f"{rel}")
            if bad:
                raise RuntimeError(
                    "dry-run leak scan FAILED (stress PnL leak class): "
                    + ", ".join(bad))
        path = run_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=1, sort_keys=True,
                                   default=str))
    for arm_id, variants in sorted(arm_records.items()):
        for variant, rec in sorted(variants.items()):
            suffix = "base" if variant == VARIANT_BASE else "stress"
            _emit(f"per_period_series/{arm_id}__{suffix}.json", {
                "schema": SERIES_SCHEMA,
                "family_id": FAMILY_ID,
                "hypothesis_id": HYPOTHESIS_ID,
                "arm_id": arm_id,
                "variant": variant,
                "scored": rec["scored"],
                "note": "per-period (decision-date) net returns; DSR "
                        "computable at terminal WITHOUT re-running cells "
                        "(P-11)" if rec["scored"] else
                        "dry-run sanitized: returns withheld (PnL leak "
                        "class); structure only",
                "periods": series[(arm_id, variant)],
            })
            _emit(f"entity_legs/{arm_id}__{suffix}.json", {
                "schema": LEGS_SCHEMA,
                "family_id": FAMILY_ID,
                "arm_id": arm_id,
                "variant": variant,
                "scored": rec["scored"],
                "legs": legs_by[(arm_id, variant)],
            })
    a_id = "SFV13-A6-H1-ANCHOR"
    c_id = "SFV13-A6-H1-CONTROL-WITHIN-SECTOR-PERMUTATION"
    sector_of = {c: v["sector"] for c, v in world["cohort"].items()}
    verdicts = {
        "schema": VERDICTS_SCHEMA,
        "family_id": FAMILY_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "cycle": CYCLE,
        "wave_sha": WAVE_SHA,
        "proposal_sha256": PROPOSAL_SHA256,
        "built_at_utc": built_at_utc,
        "mode": mode,
        "scored": mode == "scored",
        "real_pnl": mode == "scored",
        "published": False,
        "cells": 3,
        "arms": {arm_id: {
            "role": ARM_SPECS[arm_id]["role"],
            "exposure_form": ARM_SPECS[arm_id]["exposure_form"],
            "base": arm_records[arm_id][VARIANT_BASE],
            "stress": arm_records[arm_id][VARIANT_STRESS],
            "gates": (arm_gates(arm_records[arm_id][VARIANT_BASE],
                                arm_records[arm_id][VARIANT_STRESS], world["diag"])
                      if mode == "scored" else "WITHHELD_DRY_RUN_SANITIZED"),
        } for arm_id in ARM_IDS},
        "family_gates": family_gates,
        "permutation_audit": {
            "anchor_state_multiset_by_sector":
                state_multiset_by_sector(world["exposures"][a_id], sector_of),
            "identical_to_sham": _audit_multisets_match(world, sector_of),
        },
        "diag": {k: v for k, v in sorted(world["diag"].items())},
        "dry_run_hygiene": {
            "sanitized": mode == "dry_run",
            "recursive_leak_scan": "ran on every artifact at every record "
                                   "depth (stress PnL leak class)",
            "record_ids_pairwise_distinct": True,
        },
    }
    _emit("family_verdicts.json", verdicts)
    all_ids = collect_record_ids(
        [rec for arm in arm_records.values() for rec in arm.values()])
    ledger = {
        "schema": LEDGER_SCHEMA,
        "cycle": CYCLE,
        "family_id": FAMILY_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "mode": mode,
        "scored": mode == "scored",
        "real_pnl": mode == "scored",
        "published": False,
        "cells": 3,
        "built_at_utc": built_at_utc,
        "producer_role": "A8 (family runner; machine-wide heavy lock held, "
                         f"role {LOCK_ROLE}; dry-run also under lock)",
        "counter_provenance": "driver_emitted (F-A7T-1); publish-time edits "
                              "forbidden",
        "counters": {
            "arms": len(ARM_IDS),
            "variants_per_arm": 2,
            "records_total": len(all_ids),
            "void_entry_orders": world["diag"]["void_entry_orders"],
            "dead_leg_exits": world["diag"]["dead_leg_exits"],
            "fold_force_flat_exits": world["diag"]["fold_force_flat_exits"],
            "scheduled_exits": world["diag"]["scheduled_exits"],
            "floor_abstain_cohort": world["diag"]["floor_abstain_cohort"],
            "floor_abstain_leg": world["diag"]["floor_abstain_leg"],
            "div_window_formation_abstains":
                world["diag"]["div_window_formation_abstains"],
            "missing_price_series": world["diag"]["missing_price_series"],
        },
        "record_ids_pairwise_distinct":
            len(all_ids) == len(set(all_ids)),
        "input_digests": input_digests(),
        "stress": {"multiplier": STRESS_MULTIPLIER,
                   "applied_to": "booked PnL (cost multiplier on every "
                                 "fill side)"},
        "artifacts": sorted(artifacts),
    }
    if len(all_ids) != len(set(all_ids)):
        raise RuntimeError("record IDs not pairwise distinct - fail closed")
    _emit("execution_ledger.json", ledger)
    return sorted(artifacts)


def _audit_multisets_match(world, sector_of):
    """The sham preserves the exact per-(date, sector) state multiset."""
    a_id = "SFV13-A6-H1-ANCHOR"
    c_id = "SFV13-A6-H1-CONTROL-WITHIN-SECTOR-PERMUTATION"
    a_ms = state_multiset_by_sector(world["exposures"][a_id], sector_of)
    c_ms = state_multiset_by_sector(world["exposures"][c_id], sector_of)
    return a_ms == c_ms


def input_digests():
    """Digests of the pinned inputs (hash the manifest; count the staged
    dividend files; hash the cohort).  Absent optional inputs -> None."""
    out = {"dividends_dir": str(DIV_DIR),
           "dividends_file_count": (len(list(DIV_DIR.glob("*.json")))
                                    if DIV_DIR.is_dir() else None),
           "price_manifest_path": str(PRICE_MANIFEST_PATH),
           "price_manifest_sha256": (sha256_file(PRICE_MANIFEST_PATH)
                                     if PRICE_MANIFEST_PATH.exists()
                                     else None),
           "cohort_path": str(COHORT_PATH),
           "cohort_sha256": (sha256_file(COHORT_PATH)
                             if COHORT_PATH.exists() else None)}
    return out


def scored_authorized(owner_go):
    """Two-key scored authorization (P-8): exact owner GO phrase AND the
    launch environment flag.  Early or standing phrases never authorize."""
    return (owner_go == GO_PHRASE
            and os.environ.get(LAUNCH_ENV) == "1")


def code_freeze_sha():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"],
                             cwd=str(WORKTREE), capture_output=True,
                             text=True, timeout=10)
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return ""


# ===========================================================================
# main (lock discipline: single attempt; LockBusy -> exit 3)
# ===========================================================================
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dry_run = "--dry-run" in argv
    pos = [a for a in argv if not a.startswith("--")]
    built_at_utc = pos[1] if len(pos) > 1 else (pos[0] if dry_run and pos
                                                else None)
    if not dry_run:
        owner_go = pos[0] if pos else None
        if not scored_authorized(owner_go):
            sys.stderr.write(
                "SCORED EXECUTION REFUSED: the exact owner GO phrase "
                f"'{GO_PHRASE}' AND {LAUNCH_ENV}=1 are both required "
                "(two-key; P-8)\n")
            return EXIT_BLOCKED
    try:
        handle = heavy_lock.acquire(
            cycle_id=CYCLE, role=LOCK_ROLE, worktree=str(WORKTREE),
            command=[sys.executable, __file__, *argv],
            expected_artifacts=[
                str(RUN_DIR / "family_verdicts.json"),
                str(RUN_DIR / "execution_ledger.json")])
    except heavy_lock.LockBusyError as exc:
        sys.stderr.write(f"NOT_RUN_RESOURCE_CONFLICT: {exc}\n")
        return EXIT_LOCK_BUSY
    except heavy_lock.HeavyLockError as exc:
        sys.stderr.write(f"CONTROL_STATE_DRIFT: {exc}\n")
        return EXIT_DRIFT
    try:
        diag = new_diag()
        world = build_world(diag=diag)
        arm_records, series, legs_by = run_family(world, dry_run=dry_run)
        mode = "dry_run" if dry_run else "scored"
        family_gates = family_gate_blocks(arm_records, world)
        write_artifacts(RUN_DIR, built_at_utc, mode, arm_records, series,
                        legs_by, world, family_gates)
        handle.release(status="FINISHED")
        return EXIT_OK
    except Exception as exc:
        try:
            handle.release(status="FAILED", note=str(exc)[:500])
        except Exception:
            pass
        raise


if __name__ == "__main__":
    sys.exit(main(sys.argv))
