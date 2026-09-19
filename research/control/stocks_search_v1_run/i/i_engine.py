"""STOCKS-SEARCH-V1 I-lane exact-arm engines (plans/PLAN_stocks_search_v1.md §8–§9).

Implements the three frozen S-selected cells EXACTLY as frozen in
``research/control/stocks_search_v1_run/s/selection_freeze.json``
(sha256 2d56c0dbcd21117272ae0d618d697020271b088896255b4ecf132452524e3fac,
frozen at 2cf6a12b):

    SSS-GAP-P25-CONFIRM-H1       d60cf26dc71df137a7375d5684dfac1a53fb6745f90618e16286100a31f3f9f4
    SSS-52W-HIGH-B10-H20         6ccb3fa582d1bea140b90355516ddd87796e2f17a43896d337d930492b445ded
    SSS-VOL-REGIME-L21-LOW-H20   f41e94a3164d2b1bf51f7ad990e867e8b9a98bb1ccf470cc453c4a03806f8f47

plus the §6 falsification book builders and the §8 trading/cost/risk
contract.  The state FIRING predicates are NOT reimplemented: they are
reused READ-ONLY from the frozen P0 census kernels (p0/p0_lib.py, sha256
pinned against the freeze's data_manifests_sha256 before use), so the arm
identity with the frozen census is structural, not asserted.

Execution contract (§8, pinned here verbatim in code):
- decision at session t CLOSE (frozen daily clock, F5); entry t+1 OPEN;
  exit t+1+H OPEN (p0_lib.clock_legs);
- fold force-flat (execution contract, S-lane convention c8): a leg whose
  natural exit crosses the decision fold's end date exits at the OPEN of
  the name's last served session on or before that fold end; a decision
  whose entry would not precede its fold end (no held session inside the
  fold) is NOT OPENED and counted (fold_not_opened);
- death per BC-7 in full: if the natural exit session is beyond the
  name's last served session the leg is flagged DEATH_CENSORED, exits at
  the death-session OPEN when the name serves it (it does by
  construction: the death session is the last served session), is
  EXCLUDED from the expectancy numerator and reported in separate
  censored-leg accounting (gross marks kept for the invariance rerun);
  a name dying before the entry session yields a censored no-leg; a
  death on the entry session yields a zero-length censored leg (no
  return recorded);
- costs (F6): band from the trailing 252-session median dollar volume at
  the fired decision (ending at and including t), bands {A:50M, B:10M,
  C:2M} -> {A:10, B:15, C:25} bps per fill, charged ONCE PER FILL (two
  fills per round trip); STRESS TIER 2.0 PRIMARY multiplier; worst-case
  ceiling 25 bps x 2 fills x 2.0 = 100 bps/round trip (P-21); SUBFLOOR
  band at a fired decision -> leg not opened (counted); non-finite
  median -> UNRESOLVED, fail-closed raise (p0_lib.resolve_band);
- accounting: total-return (adjusted series), equal-notional per fired
  decision; per-leg net = gross - 2 * band_bps * stress / 1e4;
  legs are assigned to folds by DECISION DATE (p0_lib.assign_fold);
- per-period (P-11) daily book series: mean of active legs' daily
  open-to-open log slices per calendar session (equal-notional legs),
  persisted with sha256 by adjudicate.persist_series;
- long-only, no leverage, no short leg, no stops.

Leg conventions shared by every book (candidate, complement, R5,
C-RANDOM-TIMING, C-CAL-HIST, C-DELAY-H, C-REVERSAL-PLAIN):

Pinned ex ante in THIS lane (before any measurement, disclosed):
- C-RANDOM-TIMING: decisions on every 63rd calendar session
  (0-based index j with j % 63 == 0 and j >= 63), all names bookable at
  that date under the F4 floors AND the 252-served-session warmup needed
  for band determination (short-history names skipped and counted, never
  fail-closed-raised: the warmup law, not a data fault);
- C-CAL-HIST: bucket = (weekday 0..6, month-half {first: day <= 15,
  second: day >= 16}); for each bucket x fold the twin fires on
  ceil-spaced sessions of that bucket (chronological, step =
  max(1, n_available // N_candidate), first N taken) where N_candidate
  is the candidate's fired-decision count in that bucket x fold; minimum
  twin population 10 fired decisions per bucket per fold - a sub-floor
  bucket is NOT_ADJUDICABLE and disclosed, never silently skipped;
- C-REVERSAL-PLAIN: at every 5th calendar session (j % 5 == 0, j >= 5)
  rank F4-bookable names by trailing 5-session adjusted-close return
  ascending; equal-weight the worst quintile (k = max(1, ceil(n/5)));
  decision at j close, entry j+1 open, exit j+1+5 open (SFV3-A5 ancestor
  class, plain form; no idiosyncratic decomposition);
- K6 fold noise scale: SE_f = std(candidate leg nets in fold, ddof=1) /
  sqrt(n_f); a pair is indistinguishable in fold f iff
  |E_x,f - E_y,f| <= SE_f; folds with < 2 candidate legs are not counted.
  (The plan froze the K6 exact test "at S"; the S freeze does not contain
  it - disclosed deviation: the test is pinned HERE, before any E
  measurement, and the deviation is recorded in the I handoff.)

NO scored execution happens anywhere in this module: the real-data path
is adjudicate.load_real_data, which refuses without the exact owner GO
phrase AND refuses without a PASSING data-plane preflight
(verify_data_plane, A7 F-1 / GO condition C-2: committed retrieval-
manifest sha pin, per-pull identity vs the digest-pinned cohort census,
SPY-pinned calendar + fold law, the 3 arms' pooled position series
rebuilt and digest-compared to the S freeze, and the rebuilt fired/
bookable census cross-checked EXACTLY against p0_census.json; any drift
is INPUT_MISMATCH and the E run is refused).  This module is pure
computation over provided arrays only.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# --------------------------------------------------------------- paths
# i/ = <root>/research/control/stocks_search_v1_run/i
_HERE = Path(__file__).resolve().parent
_RUN_DIR = _HERE.parent                      # stocks_search_v1_run
_P0_DIR = _RUN_DIR / "p0"
_S_FREEZE_PATH = _RUN_DIR / "s" / "selection_freeze.json"
_D1_MANIFEST_PATH = _RUN_DIR / "d1" / "search_space_manifest.json"
_REPO_ROOT = _RUN_DIR.parents[1].parent      # worktree root (research/../..)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canon_sha256(obj) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class FrozenShaMismatch(RuntimeError):
    """STOP_CONDITION FROZEN_SHA_MISMATCH - fail-closed, never improvised."""


class DataPlaneMismatch(RuntimeError):
    """STOP_CONDITION INPUT_MISMATCH - the scored-path data-plane preflight
    (verify_data_plane, A7 finding F-1 / GO condition C-2) failed; the E run
    is REFUSED.  Never an override, never a warning.  The exception payload
    is the fail-closed verdict artifact (dict) or the refusing check detail."""


# Committed data-plane artifacts (A7 F-1: the scored loader must not accept
# caller-substituted substitutes for any of these).
COMMITTED_RETRIEVAL_MANIFEST_PATH = _P0_DIR / "retrieval_manifest.json"
COMMITTED_P0_CENSUS_PATH = _P0_DIR / "p0_census.json"
COMMITTED_CENSUS_CONFIGS_PATH = _P0_DIR / "census_configs.json"
COMMITTED_COHORT_CENSUS_PATH = _P0_DIR / "p0_census_cohort.json.gz"
COMMITTED_P0_RUN_PATH = _P0_DIR / "p0_run.py"

DATA_PLANE_PREFLIGHT_LAW = (
    "scored-path data-plane preflight (A7 F-1 / GO condition C-2): the live "
    "gitignored cache is bound to the frozen chain at load time - committed "
    "retrieval manifest pinned by sha256 against the S freeze's "
    "data_manifests_sha256 (caller-substitute paths refused), per-pull "
    "digest pins verified where the manifest carries them, every "
    "status-200 pull present and served-count-identical to the digest-"
    "pinned cohort census, SPY-pinned calendar and fold boundaries "
    "re-derived and matched to the freeze pins, the 3 arms' pooled daily "
    "position series rebuilt with the frozen census engines in P0 census "
    "space and compared EXACTLY (all stats + series sha256) to the S "
    "freeze's pooled_series_stats, and rebuilt per-config per-fold "
    "fired/bookable_fired compared EXACTLY to the frozen p0_census.json "
    "rows (s_select r3 282-cell comparison approach, restricted to the 3 "
    "rebuild states); ANY mismatch = INPUT_MISMATCH, the E run is refused, "
    "never an override")

RETRIEVAL_EMPTY_COUNT_DISCLOSURE_VERBATIM = (
    "retrieval_meta.n_empty_or_no_series=0 counts FRESH pulls only (cached "
    "re-pulls return rows=null and are not counted); the authoritative "
    "zero-served count is 7,476 cohort names (p0_census_cohort.json.gz "
    "served==0; heavy_pass names_served0=7,476) - counting artifact "
    "disclosed per A7 finding F-4; the data-plane preflight re-verifies "
    "every served count against the digest-pinned cohort census")


_P0_LIB = None


def load_p0_lib(expected_sha: str | None = None):
    """Import the frozen P0 census library READ-ONLY, sha256-pinned.

    expected_sha defaults to the pin recorded in the S freeze
    (data_manifests_sha256['p0_lib.py']).  A mismatch is a
    FROZEN_SHA_MISMATCH stop condition.
    """
    global _P0_LIB
    if _P0_LIB is not None:
        return _P0_LIB
    if expected_sha is None:
        freeze = json.loads(_S_FREEZE_PATH.read_text())
        expected_sha = freeze["data_manifests_sha256"]["p0_lib.py"]
    path = _P0_DIR / "p0_lib.py"
    disk = sha256_file(path)
    if disk != expected_sha:
        raise FrozenShaMismatch(
            f"p0_lib.py sha256 {disk} != frozen pin {expected_sha}")
    spec = importlib.util.spec_from_file_location("stocks_search_v1_p0_lib", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, mod)
    spec.loader.exec_module(mod)
    _P0_LIB = mod
    return _P0_LIB


def verify_freeze(freeze_path: Path | None = None) -> dict:
    """Verify the binding S freeze (sha256 + the 3 arm identity hashes).

    Read-only.  Raises FrozenShaMismatch on any mismatch.
    """
    path = Path(freeze_path) if freeze_path else _S_FREEZE_PATH
    digest = sha256_file(path)
    if digest != FREEZE_SHA256:
        raise FrozenShaMismatch(
            f"selection_freeze.json sha256 {digest} != binding {FREEZE_SHA256}")
    freeze = json.loads(path.read_text())
    if freeze.get("status") != "SELECTION_FROZEN":
        raise FrozenShaMismatch(f"freeze status {freeze.get('status')!r}")
    frozen = {c["config_id"]: c for c in freeze["selected_candidates"]}
    for cell in FROZEN_CELLS:
        got = frozen.get(cell["config_id"])
        if got is None:
            raise FrozenShaMismatch(f"{cell['config_id']} missing from freeze")
        if got["arm_identity_sha256"] != cell["arm_identity_sha256"]:
            raise FrozenShaMismatch(
                f"{cell['config_id']} arm_identity_sha256 mismatch")
        if got["manifest_config_excerpt"]["params"] != cell["params"]:
            raise FrozenShaMismatch(f"{cell['config_id']} params mismatch")
        if got["manifest_config_excerpt"]["family"] != cell["family"]:
            raise FrozenShaMismatch(f"{cell['config_id']} family mismatch")
    return {"freeze_sha256": digest, "n_cells": len(FROZEN_CELLS),
            "status": freeze["status"]}


# ----------------------------------------------------- frozen cells
FREEZE_SHA256 = "2d56c0dbcd21117272ae0d618d697020271b088896255b4ecf132452524e3fac"

# Verbatim from the frozen D1 manifest excerpts carried in the S freeze.
FROZEN_CELLS: tuple[dict, ...] = (
    {
        "config_id": "SSS-GAP-P25-CONFIRM-H1",
        "family": "GAP",
        "params": {"H": 1, "direction": "confirm", "pctl": 25},
        "warmup_need": 252,
        "arm_identity_sha256":
            "d60cf26dc71df137a7375d5684dfac1a53fb6745f90618e16286100a31f3f9f4",
        "complement_verbatim": (
            "gap state without direction (plan §6 example): FIRED iff "
            "gap_t <= threshold OR gap_t >= threshold - threshold-state "
            "presence with the fade/confirm split removed"),
        "r5_verbatim": (
            "threshold-state-only (plan §6 R5 example): FIRED iff the "
            "percentile threshold is crossed on either side - conditioning "
            "state without any directional/trigger component"),
    },
    {
        "config_id": "SSS-52W-HIGH-B10-H20",
        "family": "52W-HIGH",
        "params": {"H": 20, "band_pct": 10},
        "warmup_need": 252,
        "arm_identity_sha256":
            "6ccb3fa582d1bea140b90355516ddd87796e2f17a43896d337d930492b445ded",
        "complement_verbatim": (
            "proximity complement region: FIRED iff high_t defined AND "
            "proximity_t > band/100 - the candidate's flat (outside-band) "
            "region under the same construction"),
        "r5_verbatim": (
            "high-window-only: FIRED iff the rolling 252-session high is "
            "defined - proximity condition removed"),
    },
    {
        "config_id": "SSS-VOL-REGIME-L21-LOW-H20",
        "family": "VOL-REGIME",
        "params": {"H": 20, "L": 21, "direction": "low"},
        "warmup_need": 272,
        "arm_identity_sha256":
            "f41e94a3164d2b1bf51f7ad990e867e8b9a98bb1ccf470cc453c4a03806f8f47",
        "complement_verbatim": (
            "tercile-state complement: FIRED iff q1 < sigma_t < q2 - the "
            "middle tercile under the same causal machinery, extremal "
            "direction removed"),
        "r5_verbatim": (
            "tercile-assigned-only: FIRED iff sigma_t is assigned to any "
            "tercile (boundaries defined) - extremal selection removed"),
    },
)

CELL_BY_ID = {c["config_id"]: c for c in FROZEN_CELLS}
CELL_IDS = tuple(c["config_id"] for c in FROZEN_CELLS)

STRESS_TIER = 2.0
REVERSAL_PLAIN_H = 5
REVERSAL_PLAIN_PERIOD = 5
RANDOM_TIMING_PERIOD = 63
CAL_HIST_BUCKET_FLOOR = 10
GO_PHRASE = "GO STOCKS SEARCH V1 SCORED EXECUTION"

R0_NOT_RUN_LABEL = "R0_NOT_RUN"
R0_NOT_RUN_VERBATIM = (
    "R0 NOT_RUN (D2 skipped by owner amendment §3b)")
PBO_NOT_RUN_LABEL = "PBO_NOT_RUN"
PBO_NOT_RUN_VERBATIM = (
    "PBO NOT_RUN fail-closed (<=3 cells, d0992d17 class)")
DISCLOSURE_SECTION10_VERBATIM = (
    "accepted under owner-relaxed acceptance battery (R0 0.30 / DSR alpha "
    "0.10 at N = grid) | PBO NOT_RUN fail-closed (<=3 cells, d0992d17 "
    "class) | R0 NOT_RUN (D2 skipped by owner amendment §3b)")


# ------------------------------------------------------------- data model

@dataclass(frozen=True)
class NameData:
    """One name's adjusted (P-12) served history, ascending by date."""
    symbol: str
    dates: tuple[str, ...]           # ISO served sessions
    adj_open: np.ndarray
    adj_high: np.ndarray
    adj_low: np.ndarray
    adj_close: np.ndarray
    volume: np.ndarray

    def __post_init__(self):
        n = len(self.dates)
        for a in (self.adj_open, self.adj_high, self.adj_low,
                  self.adj_close, self.volume):
            if a.shape[0] != n:
                raise ValueError(f"{self.symbol}: ragged arrays")


@dataclass
class Leg:
    symbol: str
    decision_i: int
    decision_date: str
    entry_date: str
    exit_date: str
    fold: str
    band: str
    gross: float
    net: float
    force_flat: bool = False
    censored: bool = False
    censored_kind: str | None = None   # died_before_entry | death_zero_length | death_open
    log_slices: list | None = None     # [(calendar_idx, log_ret), ...] held sessions


@dataclass
class BookResult:
    book_id: str
    config_id: str
    H: int
    stress: float
    legs: list = field(default_factory=list)          # completed, non-censored
    censored_legs: list = field(default_factory=list) # BC-7 censored accounting
    counts: dict = field(default_factory=dict)
    calendar: tuple = ()
    book_log: np.ndarray | None = None                # P-11 daily series
    expectancy: float = math.nan                      # mean net (numerator)
    fold_expectancy: dict = field(default_factory=dict)
    fold_leg_counts: dict = field(default_factory=dict)

    def series_sha256(self) -> str:
        return canon_sha256({
            "book_id": self.book_id, "config_id": self.config_id,
            "calendar": list(self.calendar),
            "book_log": [round(float(x), 15) for x in self.book_log],
        })


# ------------------------------------------------------------- state masks

def state_fired_mask(name: NameData, family: str, params: dict):
    """EXACT frozen census state (read-only p0_lib kernels).

    Returns (fired, bookable) boolean masks over the name's served
    sessions - identical to what the S freeze's heavy pass counted.
    """
    L = load_p0_lib()
    o, h, lo, c, v = (name.adj_open, name.adj_high, name.adj_low,
                      name.adj_close, name.volume)
    med60 = L._rolling_median(c * v, L.DVOL_WINDOW)
    if family == "GAP":
        fired, bookable, _drops = L.census_gap(o, c, v, params["pctl"],
                                               params["direction"],
                                               med60=med60)
        return fired, bookable
    if family == "52W-HIGH":
        fired, bookable, _drops = L.census_52w_high(c, v, params["band_pct"],
                                                    med60=med60)
        return fired, bookable
    if family == "VOL-REGIME":
        fired, bookable, _drops = L.census_vol_regime(c, v, params["L"],
                                                      params["direction"],
                                                      med60=med60)
        return fired, bookable
    raise ValueError(f"family {family} not among the frozen cells")


def _warmup_gate(mask: np.ndarray, warmup_need: int) -> np.ndarray:
    out = mask.copy()
    out[:warmup_need] = False
    return out


def complement_fired_mask(name: NameData, cell: dict):
    """The family's C-COMPLEMENT, built from the SAME frozen machinery.

    GAP:        union of the fade and confirm masks (threshold-state
                presence; the fade/confirm split removed) - verbatim
                'gap_t <= threshold OR gap_t >= threshold'.
    52W-HIGH:   high defined AND proximity > band/100 (the candidate's
                flat region) - recomputed with p0_lib._rolling_max.
    VOL-REGIME: finite tercile boundaries AND NOT low-fired AND NOT
                high-fired (the middle tercile, q1 < sigma < q2).
    """
    L = load_p0_lib()
    fam = cell["family"]
    p = cell["params"]
    warm = cell["warmup_need"]
    o, h, lo, c, v = (name.adj_open, name.adj_high, name.adj_low,
                      name.adj_close, name.volume)
    med60 = L._rolling_median(c * v, L.DVOL_WINDOW)
    if fam == "GAP":
        f_fade, _, _ = L.census_gap(o, c, v, p["pctl"], "fade", med60=med60)
        f_conf, _, _ = L.census_gap(o, c, v, p["pctl"], "confirm", med60=med60)
        return _warmup_gate(f_fade | f_conf, warm)
    if fam == "52W-HIGH":
        hi = L._rolling_max(c, 252)
        n = c.shape[0]
        out = np.zeros(n, dtype=bool)
        for i in range(warm, n):
            hi_i = float(hi[i])
            if np.isfinite(hi_i) and hi_i > 0.0:
                prox = (hi_i - float(c[i])) / hi_i
                out[i] = prox > p["band_pct"] / 100.0
        return out
    if fam == "VOL-REGIME":
        f_low, _, _ = L.census_vol_regime(c, v, p["L"], "low", med60=med60)
        f_high, _, _ = L.census_vol_regime(c, v, p["L"], "high", med60=med60)
        # finiteness of the boundaries is implied by either extreme firing
        # machinery; the middle-tercile complement needs the boundaries
        # DEFINED at i even when neither extreme fires, so recompute the
        # finite-boundary domain from the same causal sigma series.
        with np.errstate(divide="ignore", invalid="ignore"):
            lr = np.full(c.shape[0], np.nan)
            lr[1:] = np.log(c[1:] / c[:-1])
        rets = lr[1:]
        sigma = np.full(c.shape[0], np.nan)
        for j in range(p["L"], c.shape[0]):
            w = rets[j - p["L"]:j]
            if np.all(np.isfinite(w)) and w.shape[0] == p["L"]:
                sigma[j] = float(np.std(w, ddof=1))
        n = c.shape[0]
        fin = np.zeros(n, dtype=bool)
        for i in range(warm, n):
            if i >= 251:
                hist = sigma[i - 251:i + 1]
                fin[i] = bool(np.all(np.isfinite(hist)))
        return _warmup_gate(fin & ~f_low & ~f_high, warm)
    raise ValueError(f"family {fam}")


def r5_component_fired_mask(name: NameData, cell: dict):
    """The family's R5 component-only book, verbatim from the D1 manifest.

    GAP:        threshold crossed on either side - strict crossing
                (gap < thr OR gap > thr); the <=/>= equality edge is the
                complement's presence law, not a crossing.
    52W-HIGH:   rolling 252-session high DEFINED (proximity removed).
    VOL-REGIME: sigma assigned to ANY tercile (boundaries defined).
    """
    L = load_p0_lib()
    fam = cell["family"]
    p = cell["params"]
    warm = cell["warmup_need"]
    o, c, v = name.adj_open, name.adj_close, name.volume
    med60 = L._rolling_median(c * v, L.DVOL_WINDOW)
    if fam == "GAP":
        f_fade, _, _ = L.census_gap(o, c, v, p["pctl"], "fade", med60=med60)
        f_conf, _, _ = L.census_gap(o, c, v, p["pctl"], "confirm", med60=med60)
        presence = _warmup_gate(f_fade | f_conf, warm)
        with np.errstate(divide="ignore", invalid="ignore"):
            gaps = np.full(c.shape[0], np.nan)
            gaps[1:] = o[1:] / c[:-1] - 1.0
        strict = np.zeros(c.shape[0], dtype=bool)
        for i in range(warm, c.shape[0]):
            hist = gaps[i - 251:i + 1]
            if not np.all(np.isfinite(hist)):
                continue
            thr = float(np.percentile(hist, p["pctl"], method="linear"))
            g = float(gaps[i])
            strict[i] = (g < thr) or (g > thr)
        return presence & strict
    if fam == "52W-HIGH":
        hi = L._rolling_max(c, 252)
        n = c.shape[0]
        out = np.zeros(n, dtype=bool)
        for i in range(warm, n):
            out[i] = bool(np.isfinite(hi[i]) and hi[i] > 0.0)
        return out
    if fam == "VOL-REGIME":
        # any-tercile assignment == boundaries defined (same causal sigma)
        return complement_fired_mask_volregime_domain(name, cell, warm)
    raise ValueError(f"family {fam}")


def complement_fired_mask_volregime_domain(name: NameData, cell: dict,
                                           warm: int) -> np.ndarray:
    """Finite-tercile-boundary domain for VOL-REGIME (shared)."""
    p = cell["params"]
    c = name.adj_close
    n = c.shape[0]
    with np.errstate(divide="ignore", invalid="ignore"):
        lr = np.full(n, np.nan)
        lr[1:] = np.log(c[1:] / c[:-1])
    rets = lr[1:]
    sigma = np.full(n, np.nan)
    for j in range(p["L"], n):
        w = rets[j - p["L"]:j]
        if np.all(np.isfinite(w)) and w.shape[0] == p["L"]:
            sigma[j] = float(np.std(w, ddof=1))
    out = np.zeros(n, dtype=bool)
    for i in range(warm, n):
        if i >= 251:
            hist = sigma[i - 251:i + 1]
            out[i] = bool(np.all(np.isfinite(hist)))
    return out


# ------------------------------------------------------------- bands/clock

def med252_series(name: NameData) -> np.ndarray:
    """Trailing 252-session median dollar volume ENDING AT AND INCLUDING i."""
    L = load_p0_lib()
    dvol = name.adj_close * name.volume
    n = dvol.shape[0]
    out = np.full(n, np.nan)
    if n >= 252:
        from numpy.lib.stride_tricks import sliding_window_view
        sw = sliding_window_view(dvol, 252)
        out[251:] = np.median(sw, axis=1)
    return out


def band_at(name: NameData, i: int, med252: np.ndarray | None = None) -> str:
    """F6 ADV band at decision i (fail-closed via p0_lib.resolve_band)."""
    L = load_p0_lib()
    if med252 is None:
        med252 = med252_series(name)
    return L.resolve_band(float(med252[i]))


def fold_ends(calendar, b1: str, b2: str) -> dict:
    """Last calendar session of each fold (force-flat anchors)."""
    L = load_p0_lib()
    ends = {}
    for d in calendar:
        f = L.assign_fold(d, b1, b2)
        ends[f] = d            # calendar ascending -> last write wins
    if set(ends) != {"F1", "F2", "F3"}:
        raise ValueError(f"folds not all populated: {sorted(ends)}")
    return ends


# ------------------------------------------------------------- leg engine

def build_legs(name: NameData, decision_idx, H: int, calendar_index: dict,
               fends: dict, stress: float, entry_offset: int = 1,
               book_id: str = "book") -> tuple[list, list, dict]:
    """§8 execution engine for ONE name's decision indices.

    Returns (legs, censored_legs, counts).  All conventions per the module
    docstring (clock, fold force-flat, BC-7 death, bands, costs).
    """
    L = load_p0_lib()
    if H <= 0:
        raise ValueError("H must be positive")
    n = len(name.dates)
    med252 = med252_series(name)
    dates = name.dates
    op = name.adj_open
    legs: list[Leg] = []
    censored: list[Leg] = []
    counts = {"fired": 0, "band_subfloor": 0, "fold_not_opened": 0,
              "censored_died_before_entry": 0, "censored_death_zero_length": 0,
              "censored_death_open": 0, "open_offset": 0}
    for t in sorted(int(i) for i in decision_idx):
        counts["fired"] += 1
        try:
            band = L.resolve_band(float(med252[t]))
        except ValueError:
            raise  # UNRESOLVED: fail-closed, never a silent default band
        if band == "SUBFLOOR":
            counts["band_subfloor"] += 1
            continue
        entry_i = t + entry_offset
        exit_i = t + entry_offset + H
        d_t = dates[t]
        fold = L.assign_fold(d_t, fends["F1"], fends["F2"])
        if entry_i > n - 1:
            lg = Leg(name.symbol, t, d_t, "-", dates[n - 1], fold, band,
                     math.nan, math.nan, censored=True,
                     censored_kind="died_before_entry")
            censored.append(lg)
            counts["censored_died_before_entry"] += 1
            continue
        entry_date = dates[entry_i]
        if entry_date > fends[fold]:
            counts["fold_not_opened"] += 1
            continue
        # force-flat anchor: last served session with date <= fold end
        ff_exit = entry_i
        while ff_exit + 1 < n and dates[ff_exit + 1] <= fends[fold]:
            ff_exit += 1
        natural_served = exit_i <= n - 1
        if natural_served and dates[exit_i] <= fends[fold]:
            # natural exit inside the decision fold
            eff_exit, exit_date, force_flat = exit_i, dates[exit_i], False
        elif not natural_served and dates[n - 1] <= fends[fold]:
            # BC-7: death binds before the fold end - exit at the
            # death-session OPEN when the name serves it (it does:
            # the death session is the last served session)
            if n - 1 <= entry_i:
                lg = Leg(name.symbol, t, d_t, entry_date, dates[n - 1],
                         fold, band, math.nan, math.nan, censored=True,
                         censored_kind="death_zero_length")
                censored.append(lg)
                counts["censored_death_zero_length"] += 1
                continue
            gross = float(op[n - 1]) / float(op[entry_i]) - 1.0
            lg = Leg(name.symbol, t, d_t, entry_date, dates[n - 1], fold,
                     band, gross, math.nan, censored=True,
                     censored_kind="death_open")
            censored.append(lg)
            counts["censored_death_open"] += 1
            continue
        else:
            # natural exit crosses the fold end (or death lands after it):
            # fold force-flat binds first (execution contract, c8)
            if ff_exit <= entry_i:
                counts["fold_not_opened"] += 1
                continue
            eff_exit, exit_date, force_flat = ff_exit, dates[ff_exit], True
        gross = float(op[eff_exit]) / float(op[entry_i]) - 1.0
        net = gross - 2.0 * (L.BAND_BPS[band] * stress) / 1e4
        held = list(range(entry_i, eff_exit))       # log-slice sessions
        slices = []
        for d in held:
            ci = calendar_index.get(dates[d], -1)
            if ci < 0:
                counts["open_offset"] += 1
                continue
            slices.append((ci, math.log(float(op[d + 1]) / float(op[d]))))
        lg = Leg(name.symbol, t, d_t, entry_date, exit_date, fold, band,
                 gross, net, force_flat=force_flat, log_slices=slices)
        legs.append(lg)
    return legs, censored, counts


def fends_key(fends: dict) -> tuple:
    return (fends["F1"], fends["F2"])


# ------------------------------------------------------------- book runner

def run_book(book_id: str, config_id: str, names: dict, decision_masks: dict,
             H: int, calendar, b1: str, b2: str, stress: float,
             entry_offset: int = 1, include_censored: bool = False) -> BookResult:
    """Assemble a BookResult from per-name decision-index sequences."""
    cal = tuple(calendar)
    calendar_index = {d: i for i, d in enumerate(cal)}
    fends = fold_ends(cal, b1, b2)
    book = BookResult(book_id=book_id, config_id=config_id, H=H,
                      stress=stress, calendar=cal)
    all_legs: list[Leg] = []
    all_censored: list[Leg] = []
    for sym in sorted(names):
        idx = decision_masks.get(sym)
        if idx is None or len(idx) == 0:
            continue
        legs, cens, counts = build_legs(names[sym], idx, H, calendar_index,
                                        fends, stress,
                                        entry_offset=entry_offset,
                                        book_id=book_id)
        all_legs.extend(legs)
        all_censored.extend(cens)
        for k, v in counts.items():
            book.counts[k] = book.counts.get(k, 0) + v
    book.legs = all_legs
    book.censored_legs = all_censored
    _finalize(book)
    return book


def _finalize(book: BookResult, extra_legs: list | None = None) -> None:
    legs = book.legs + (extra_legs or [])
    nets = [lg.net for lg in legs]
    book.expectancy = float(np.mean(nets)) if nets else math.nan
    folds = {}
    counts = {}
    for lg in legs:
        folds.setdefault(lg.fold, []).append(lg.net)
        counts[lg.fold] = counts.get(lg.fold, 0) + 1
    book.fold_expectancy = {f: float(np.mean(v)) for f, v in folds.items()}
    book.fold_leg_counts = counts
    # P-11 daily series: mean of active legs' log slices per calendar day
    ncal = len(book.calendar)
    series = np.zeros(ncal, dtype=float)
    active = np.zeros(ncal, dtype=int)
    for lg in legs:
        if not lg.log_slices:
            continue
        for ci, val in lg.log_slices:
            series[ci] += val
            active[ci] += 1
    nz = active > 0
    series[nz] /= active[nz]
    book.book_log = series


def include_censored_nets(book: BookResult) -> BookResult:
    """BC-7 invariance rerun: censored legs INCLUDED at their marks, net
    of costs (death_open legs only; zero-length/no-leg contribute none)."""
    import copy
    out = copy.deepcopy(book)
    extra = []
    L = load_p0_lib()
    for lg in book.censored_legs:
        if lg.censored_kind != "death_open":
            continue
        net = lg.gross - 2.0 * (L.BAND_BPS[lg.band] * book.stress) / 1e4
        lg2 = Leg(lg.symbol, lg.decision_i, lg.decision_date, lg.entry_date,
                  lg.exit_date, lg.fold, lg.band, lg.gross, net,
                  censored=True, censored_kind=lg.censored_kind)
        extra.append(lg2)
    out.legs = list(book.legs) + extra
    out.censored_legs = list(book.censored_legs)
    out.book_id = book.book_id + "+censored"
    _finalize(out)
    return out


# ------------------------------------------------------- cohort book utils

def _bookable_idx_at(name: NameData, i: int, med60_arr) -> bool:
    L = load_p0_lib()
    if i < 0 or i >= len(name.dates):
        return False
    m = med60_arr[i]
    return bool(name.adj_close[i] >= L.FLOOR_PRICE
                and np.isfinite(m) and m >= L.FLOOR_DVOL)


def cohort_bookable_decisions(names: dict, calendar, decision_dates,
                              counts: dict | None = None) -> dict:
    """Dates -> per-name decision served indices for cohort books.

    A name participates at a decision date iff the date is served, the F4
    floors hold (adj_close >= $1, med60 dvol >= $2M) AND the name has >=
    252 served sessions (warmup needed for band determination); skipped
    names are counted (warmup_law), never fail-closed-raised.
    """
    L = load_p0_lib()
    masks: dict[str, list[int]] = {s: [] for s in names}
    date_pos = {d: i for i, d in enumerate(calendar)}
    med60s = {s: L._rolling_median(n.adj_close * n.volume, L.DVOL_WINDOW)
              for s, n in names.items()}
    for d in decision_dates:
        for sym in sorted(names):
            nm = names[sym]
            pos = nm_dates_index(nm, d)
            if pos is None:
                continue
            if len(nm.dates) < 252 or pos < 251:
                # warmup/band law: no trailing 252-session median at the
                # decision -> not eligible (counted, never fail-closed:
                # the F6 UNRESOLVED raise is reserved for a non-finite
                # median on an otherwise eligible name)
                if counts is not None:
                    counts["warmup_short_history"] = \
                        counts.get("warmup_short_history", 0) + 1
                continue
            if _bookable_idx_at(nm, pos, med60s[sym]):
                masks[sym].append(pos)
            elif counts is not None:
                counts["cohort_floor_reject"] = \
                    counts.get("cohort_floor_reject", 0) + 1
    return {s: sorted(v) for s, v in masks.items()}


def nm_dates_index(nm: NameData, iso: str) -> int | None:
    import bisect
    i = bisect.bisect_left(nm.dates, iso)
    if i < len(nm.dates) and nm.dates[i] == iso:
        return i
    return None


def random_timing_decisions(calendar) -> list[str]:
    """Every-63rd-session clock: 0-based calendar indices j % 63 == 0, j >= 63."""
    return [calendar[j] for j in range(RANDOM_TIMING_PERIOD, len(calendar))
            if j % RANDOM_TIMING_PERIOD == 0]


def cal_hist_buckets(calendar, b1: str, b2: str) -> dict:
    """bucket = (weekday, month-half) -> fold -> [dates] (chronological)."""
    L = load_p0_lib()
    out: dict[tuple, dict[str, list[str]]] = {}
    for d in calendar:
        b = _bucket_of(d)
        f = L.assign_fold(d, b1, b2)
        out.setdefault(b, {"F1": [], "F2": [], "F3": []})[f].append(d)
    return out


def _bucket_of(iso: str) -> tuple[int, str]:
    from datetime import date
    dt = date.fromisoformat(iso)
    half = "first" if dt.day <= 15 else "second"
    return (dt.weekday(), half)


def cal_hist_twin_dates(candidate_fired_dates, calendar, b1: str, b2: str):
    """Deterministic C-CAL-HIST twin dates + bucket population report.

    For each (bucket, fold): step = max(1, n_available // N_candidate);
    twin dates = available[0::step][:N_candidate] (chronological,
    ceil-spaced, deterministic).  The report carries per-bucket twin
    fired-decision populations for the >= 10 floor.
    """
    L = load_p0_lib()
    cand = {}
    for d in candidate_fired_dates:
        b = _bucket_of(d)
        f = L.assign_fold(d, b1, b2)
        cand.setdefault(b, {"F1": 0, "F2": 0, "F3": 0})[f] += 1
    avail = cal_hist_buckets(calendar, b1, b2)
    twin: list[str] = []
    report = {}
    for b in sorted(set(avail) | set(cand)):
        report[b] = {}
        for f in ("F1", "F2", "F3"):
            n_cand = int(cand.get(b, {}).get(f, 0))
            available = avail.get(b, {}).get(f, [])
            if n_cand == 0 or not available:
                report[b][f] = {"n_candidate": n_cand, "n_twin": 0,
                                "sub_floor": n_cand > 0}
                continue
            step = max(1, len(available) // n_cand)
            picked = available[0::step][:n_cand]
            twin.extend(picked)
            report[b][f] = {"n_candidate": n_cand, "n_twin": len(picked),
                            "sub_floor": len(picked) < CAL_HIST_BUCKET_FLOOR}
    return sorted(set(twin)), report


def reversal_plain_decisions(names: dict, calendar) -> tuple[list[str], dict]:
    """Worst-quintile 5-session-return names at every 5th calendar session.

    Returns (decision_map symbol->dates list is overkill) - implemented as
    per-formation selection; the caller converts to per-name decision
    served indices.  Formation j: j % 5 == 0 and j >= 5.
    """
    L = load_p0_lib()
    cal_pos = {d: i for i, d in enumerate(calendar)}
    med60s = {s: L._rolling_median(n.adj_close * n.volume, L.DVOL_WINDOW)
              for s, n in names.items()}
    picks: dict[str, list[str]] = {s: [] for s in names}
    stats = {"formations": 0, "eligible_avg": 0.0}
    n_elig = 0
    for j in range(REVERSAL_PLAIN_PERIOD, len(calendar), REVERSAL_PLAIN_PERIOD):
        d = calendar[j]
        scored = []
        for sym in sorted(names):
            nm = names[sym]
            pos = nm_dates_index(nm, d)
            prev = nm_dates_index(nm, calendar[j - REVERSAL_PLAIN_PERIOD])
            if pos is None or prev is None:
                continue
            if pos < 251:
                continue          # band law: no med252 at the decision yet
            if not _bookable_idx_at(nm, pos, med60s[sym]):
                continue
            r = float(nm.adj_close[pos]) / float(nm.adj_close[prev]) - 1.0
            scored.append((r, sym))
        if not scored:
            continue
        stats["formations"] += 1
        n_elig += len(scored)
        scored.sort()                                  # ascending = worst first
        k = max(1, math.ceil(len(scored) / 5))
        for _r, sym in scored[:k]:
            picks[sym].append(d)
    stats["eligible_avg"] = n_elig / stats["formations"] if stats["formations"] else 0.0
    return picks, stats


def reversal_plain_masks(names: dict, calendar) -> dict:
    picks, stats = reversal_plain_decisions(names, calendar)
    masks = {}
    for sym, dates in picks.items():
        idx = [nm_dates_index(names[sym], d) for d in dates]
        masks[sym] = [i for i in idx if i is not None]
    return masks, stats


# ------------------------------------------------------------- pit mutation

def pit_gate_core(mutated: np.ndarray, fired_indices) -> dict:
    """Pure C-PIT-MUTATION core: given the one-session-earlier
    recomputation mask, the gate PASSES iff EVERY originally fired
    decision is changed or refused by the mutated book."""
    total = len(fired_indices)
    changed = sum(1 for t in fired_indices
                  if t >= len(mutated) or not mutated[t])
    return {"fired": total, "changed_or_refused": changed,
            "pass": total > 0 and changed == total}


def pit_mutation_gate(names: dict, decision_masks: dict, cell: dict) -> dict:
    """C-PIT-MUTATION (verbatim §6): one-session-earlier recomputation
    must change/refuse the book on EVERY fired decision.

    Mechanics (pinned): mutated_fired(i) = original state recomputed at
    i-1 (the same frozen machinery, warmup applied at i-1).  Refusal
    includes warmup or undefined-state at t-1.
    """
    total, changed = 0, 0
    per_name = {}
    for sym in sorted(decision_masks):
        nm = names[sym]
        orig = list(decision_masks[sym])
        if not orig:
            per_name[sym] = {"fired": 0, "changed": 0}
            continue
        mut_state = state_fired_mask(nm, cell["family"], cell["params"])[0]
        mutated = np.zeros(len(mut_state), dtype=bool)
        mutated[1:] = mut_state[:-1]          # one-session-earlier recompute
        core = pit_gate_core(mutated, orig)
        total += core["fired"]
        changed += core["changed_or_refused"]
        per_name[sym] = {"fired": core["fired"], "changed": core["changed_or_refused"]}
    return {"gate": "C-PIT-MUTATION", "fired": total, "changed_or_refused": changed,
            "pass": total > 0 and changed == total,
            "per_name": per_name,
            "law": ("one-session-earlier recomputation changes/refuses the "
                    "book on every fired decision (plan §6 verbatim; "
                    "mechanics pinned in i_engine)")}


# ------------------------------------------------------------- arm runner

def arm_decision_masks(names: dict, cell: dict) -> dict:
    """Exact-arm decision masks: the frozen census state, warmup-gated."""
    out = {}
    for sym in sorted(names):
        fired, _bookable = state_fired_mask(names[sym], cell["family"],
                                            cell["params"])
        idx = np.nonzero(_warmup_gate(fired, cell["warmup_need"]))[0]
        out[sym] = [int(i) for i in idx]
    return out


def complement_masks(names: dict, cell: dict) -> dict:
    out = {}
    for sym in sorted(names):
        m = complement_fired_mask(names[sym], cell)
        out[sym] = [int(i) for i in np.nonzero(m)[0]]
    return out


def r5_masks(names: dict, cell: dict) -> dict:
    out = {}
    for sym in sorted(names):
        m = r5_component_fired_mask(names[sym], cell)
        out[sym] = [int(i) for i in np.nonzero(m)[0]]
    return out


def delay_masks(masks: dict) -> dict:
    """C-DELAY-H: identical decisions; entry_offset H later (build_legs
    entry_offset=1+H shifts entry to t+1+H and exit to t+1+2H)."""
    return {s: list(v) for s, v in masks.items()}


def build_all_books(names: dict, cell: dict, calendar, b1: str, b2: str,
                    stress: float = STRESS_TIER) -> dict:
    """Build the candidate arm + its full §6 falsification battery.

    Pure over provided arrays; no I/O; deterministic (sorted symbols).
    """
    cid = cell["config_id"]
    H = int(cell["params"]["H"])
    out = {"cell": cid, "H": H, "stress": stress}
    masks = arm_decision_masks(names, cell)
    out["masks"] = masks
    fired_dates = sorted({names[s].dates[t] for s, idx in masks.items()
                          for t in idx})
    out["candidate"] = run_book("candidate", cid, names, masks, H, calendar,
                                b1, b2, stress)
    out["c_complement"] = run_book("c_complement", cid, names,
                                   complement_masks(names, cell), H, calendar,
                                   b1, b2, stress)
    out["r5_component"] = run_book("r5_component", cid, names,
                                   r5_masks(names, cell), H, calendar,
                                   b1, b2, stress)
    out["c_delay_h"] = run_book("c_delay_h", cid, names,
                                delay_masks(masks), H, calendar, b1, b2,
                                stress, entry_offset=1 + H)
    rt_dates = random_timing_decisions(calendar)
    counts: dict = {}
    rt_masks = cohort_bookable_decisions(names, calendar, rt_dates, counts)
    out["counts_cohort"] = counts
    out["c_random_timing"] = run_book("c_random_timing", cid, names, rt_masks,
                                      H, calendar, b1, b2, stress)
    ch_dates, ch_report = cal_hist_twin_dates(fired_dates, calendar, b1, b2)
    ch_masks = cohort_bookable_decisions(names, calendar, ch_dates)
    out["c_cal_hist_report"] = ch_report
    out["c_cal_hist"] = run_book("c_cal_hist", cid, names, ch_masks, H,
                                 calendar, b1, b2, stress)
    rev_masks, rev_stats = reversal_plain_masks(names, calendar)
    out["reversal_stats"] = rev_stats
    out["c_reversal_plain"] = run_book("c_reversal_plain", cid, names,
                                       rev_masks, REVERSAL_PLAIN_H, calendar,
                                       b1, b2, stress)
    out["pit_mutation"] = pit_mutation_gate(names, masks, cell)
    return out


def spy_legs_for(spy: NameData, legs: list) -> list:
    """C-MARKET: SPY buy-and-hold legs on the SAME entry/exit dates as the
    candidate legs (exposure-matched per fired decision, benchmark has no
    costs).  Returns gross SPY leg returns aligned with `legs` (NaN where
    SPY does not serve the dates - counted, never imputed)."""
    out = []
    for lg in legs:
        e = nm_dates_index(spy, lg.entry_date)
        x = nm_dates_index(spy, lg.exit_date)
        if e is None or x is None or x <= e:
            out.append(math.nan)
            continue
        out.append(float(spy.adj_open[x]) / float(spy.adj_open[e]) - 1.0)
    return out


# ------------------------------------------------- data-plane preflight (F-1)
#
# A7 prelaunch audit finding F-1 (HIGH) / GO condition C-2: the scored E run
# had NO load-time control binding the live gitignored cache to the frozen
# chain.  verify_data_plane is that control, modeled on the sibling FOREX
# cycle's verify_positions_vs_freeze (INPUT_MISMATCH fail-closed) and on
# s_select.py's r3 heavy pass + 282-cell census gate (reused READ-ONLY:
# same engines, same census space, same exact-equality comparison form - no
# s/ code is imported or modified).

def _warmup_law(family: str, params: dict) -> int:
    """p0 enumeration warmup law recomputed (s_select.warmup_from_params,
    read-only): WARMUP=252 base; longer construction need wins."""
    WARMUP = 252
    if family == "EVENT-UNWIND":
        return max(WARMUP, params["K"])
    if family == "GAP":
        return WARMUP
    if family == "52W-HIGH":
        return WARMUP
    if family == "CLV-RANGE":
        return max(WARMUP, 20 - 1 + params["k"])
    if family == "DVOL-SHOCK":
        return WARMUP
    if family == "VOL-REGIME":
        return max(WARMUP, WARMUP - 1 + params["L"])
    raise ValueError(f"unknown family {family}")


def _state_key(family: str, params: dict) -> tuple:
    """(family, sorted non-H params) - the p0 hold-invariance state key
    (s_select.state_maps convention; H affects only execution legs)."""
    return (family, tuple(sorted((k, v) for k, v in params.items()
                                 if k != "H")))


def _load_pinned_p0_run(expected_sha: str):
    """Import the frozen P0 runner READ-ONLY for its parse_name parser,
    sha256-pinned against the S freeze (FROZEN_SHA_MISMATCH on drift)."""
    import importlib.util
    path = COMMITTED_P0_RUN_PATH
    disk = sha256_file(path)
    if disk != expected_sha:
        raise FrozenShaMismatch(
            f"p0_run.py sha256 {disk} != frozen pin {expected_sha}")
    spec = importlib.util.spec_from_file_location(
        "stocks_search_v1_p0_run", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, mod)
    spec.loader.exec_module(mod)
    return mod


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _canon_json(obj) -> str:
    """Canonical-JSON digest of a parsed row (s_select.canon convention)."""
    return canon_sha256(obj)


def _arm_state_machinery(census_configs: dict) -> dict:
    """State machinery for the 3 FROZEN_CELLS from the (sha-pinned)
    census_configs.json: the arm configs' states plus EVERY census config
    sharing each state (H variants; p0 hold-invariance law), for the
    census cross-check and the pooled-series rebuild."""
    configs = census_configs["configs"]
    by_id = {c["config_id"]: c for c in configs}
    state_cfgs: dict[tuple, dict] = {}
    configs_of_state: dict[tuple, list] = {}
    warmup_of: dict[tuple, int] = {}
    state_key_of: dict[str, tuple] = {}
    for cfg in configs:
        cid = cfg["config_id"]
        key = _state_key(cfg["family"], cfg["params"])
        state_key_of[cid] = key
        if key in warmup_of:
            if warmup_of[key] != _warmup_law(cfg["family"], cfg["params"]):
                raise DataPlaneMismatch(
                    {"failed_check": "warmup_law_within_state",
                     "detail": {"config_id": cid}})
            continue
        # first time this state appears: pin the warmup and, if it is one
        # of the 3 arms' states, register the rebuild state config
        warmup_of[key] = _warmup_law(cfg["family"], cfg["params"])
    for cell in FROZEN_CELLS:
        cid = cell["config_id"]
        cc = by_id.get(cid)
        if cc is None:
            raise DataPlaneMismatch(
                {"failed_check": "arm_config_in_census_configs",
                 "detail": {"config_id": cid}})
        if cc["family"] != cell["family"] or \
                {k: v for k, v in cc["params"].items() if k != "H"} != \
                {k: v for k, v in cell["params"].items() if k != "H"}:
            raise DataPlaneMismatch(
                {"failed_check": "arm_state_params_identity",
                 "detail": {"config_id": cid,
                            "census_configs": cc["params"],
                            "frozen_cell": cell["params"]}})
        if cc.get("warmup_need") != _warmup_law(cc["family"], cc["params"]):
            raise DataPlaneMismatch(
                {"failed_check": "arm_warmup_law",
                 "detail": {"config_id": cid, "warmup_need": cc.get("warmup_need"),
                            "law": _warmup_law(cc["family"], cc["params"])}})
        key = state_key_of[cid]
        state_cfgs[key] = {
            "config_id": cid, "family": cc["family"],
            "params": {k: v for k, v in cc["params"].items() if k != "H"}}
    for cfg in configs:
        key = state_key_of[cfg["config_id"]]
        if key in state_cfgs:
            configs_of_state.setdefault(key, []).append(
                (cfg["config_id"], int(cfg["params"]["H"])))
    for key in state_cfgs:
        configs_of_state[key].sort()
    return {"state_cfgs": state_cfgs,
            "configs_of_state": configs_of_state,
            "warmup_of": warmup_of,
            "state_key_of": state_key_of,
            "n_configs_total": len(configs)}


def _build_calendar_from_cache(cache_dir: Path, start: str,
                               end: str) -> tuple[list, str]:
    """SPY-pinned S0-window session calendar (s_select.build_calendar,
    read-only): SPY trades every XNYS session, so its served dates ARE the
    calendar.  Returns (calendar, spy_json_gz_sha256)."""
    spy_gz = Path(cache_dir) / "SPY.json.gz"
    if not spy_gz.exists():
        raise DataPlaneMismatch(
            {"failed_check": "spy_cache_present",
             "detail": {"path": str(spy_gz)}})
    spy_sha = sha256_file(spy_gz)
    rows = json.loads(_gzip_read(spy_gz))
    dates = sorted(str(r["date"])[:10] for r in rows
                   if r.get("date") is not None)
    in_win = [d for d in dates if start <= d <= end]
    return in_win, spy_sha


def _gzip_read(gz_path: Path) -> str:
    import gzip
    with gzip.open(gz_path, "rt") as f:
        return f.read()


def _rebuild_data_plane(cache_dir: Path, p0_run, L, retrieval: dict,
                        cohort_census: dict, calendar: list,
                        b1: str, b2: str, machinery: dict,
                        on_refuse, pooled_cids=None) -> dict:
    """ONE pass over the required cohort in P0 CENSUS SPACE (the s_select
    r3 heavy pass, restricted to the 3 arms' states, reused READ-ONLY:
    p0_run.parse_name + p0_lib.run_config_census on each name's FULL served
    history - warm gate in served-session index space, fold-by-decision-DATE,
    full-history med60, positions pooled by held-session DATE onto the
    SPY-pinned calendar with per-name bincount so overlapping names EACH
    count).  Also performs the per-pull identity checks (existence, manifest
    digest pins where carried, served-count equality vs the digest-pinned
    cohort census).  Per-name refuses call on_refuse(name, detail) (which
    raises fail-closed in the caller); aggregate results are returned.
    pooled_cids defaults to the 3 FROZEN_CELLS configs - only the scored
    arms' pooled series are built (per-config per-fold census fold counters
    cover every config of the rebuilt states regardless).

    NOTE: the served0/short counter laws follow s_select.heavy_pass exactly
    (names_served0 = parse->None; names_short = parsed but < 3 sessions,
    skipped by the rebuild but still served-count-verified).
    """
    pulls = retrieval["pulls"]
    required = sorted(s for s, m in pulls.items() if m.get("status") == 200)
    counters = {"required_names": len(required), "missing_cache": 0,
                "digest_pinned_pulls_verified": 0, "names_parsed": 0,
                "names_served0": 0, "names_short": 0,
                "off_or_out_of_window_bars": 0,
                "off_or_out_of_window_held_sessions": 0}
    state_cfgs = machinery["state_cfgs"]
    configs_of_state = machinery["configs_of_state"]
    warmup_of = machinery["warmup_of"]
    if pooled_cids is None:
        pooled_cids = tuple(c["config_id"] for c in FROZEN_CELLS)
    pooled_cids = sorted(pooled_cids)
    ncal = len(calendar)
    pooled = {cid: np.zeros(ncal, dtype=np.int64) for cid in pooled_cids}
    stats = {cid: {"positions_used": 0, "position_days": 0,
                   "death_censored_legs": 0, "pooled_max": 0,
                   "pooled_nonzero_days": 0} for cid in pooled_cids}
    fold_ids = ("F1", "F2", "F3")
    state_fired_fold = {k: {f: 0 for f in fold_ids} for k in state_cfgs}
    state_bookable_fold = {k: {f: 0 for f in fold_ids} for k in state_cfgs}

    cal_arr = np.array(calendar, dtype="<U10")
    for sym in required:
        gz = Path(cache_dir) / f"{sym}.json.gz"
        if not gz.exists():
            counters["missing_cache"] += 1
            on_refuse(sym, {"failed_check": "cache_file_present",
                            "detail": {"symbol": sym, "path": str(gz)}})
            continue
        m = pulls[sym]
        if "sha256_gz" in m:
            if sha256_file(gz) != m["sha256_gz"]:
                on_refuse(sym, {"failed_check": "per_pull_digest_gz",
                                "detail": {"symbol": sym,
                                           "manifest": m["sha256_gz"],
                                           "disk": sha256_file(gz)}})
            if "sha256_raw" in m:
                import gzip
                raw = gzip.decompress(gz.read_bytes())
                if _sha256_bytes(raw) != m["sha256_raw"]:
                    on_refuse(sym, {"failed_check": "per_pull_digest_raw",
                                    "detail": {"symbol": sym}})
            counters["digest_pinned_pulls_verified"] += 1
        parsed = p0_run.parse_name(gz)
        served = int(cohort_census[sym].get("served", 0))
        if parsed is None:
            if served != 0:
                on_refuse(sym, {"failed_check": "served_count_vs_cohort_census",
                                "detail": {"symbol": sym, "parsed": 0,
                                           "cohort_census_served": served}})
            counters["names_served0"] += 1
            continue
        dates, o, h, lo, c, v, _mal = parsed
        if len(dates) != served:
            on_refuse(sym, {"failed_check": "served_count_vs_cohort_census",
                            "detail": {"symbol": sym, "parsed": len(dates),
                                       "cohort_census_served": served}})
        counters["names_parsed"] += 1
        if len(dates) < 3:
            counters["names_short"] += 1
            continue
        darr = np.array([d[:10] for d in dates], dtype="<U10")
        n = int(darr.shape[0])
        fold_code = np.where(darr <= b1, 0,
                             np.where(darr <= b2, 1, 2)).astype(np.int8)
        ins = np.searchsorted(cal_arr, darr)
        vic = np.clip(ins, 0, ncal - 1)
        oncal = cal_arr[vic] == darr
        cal_pos = np.where(oncal, vic, np.int64(-1))
        counters["off_or_out_of_window_bars"] += int((~oncal).sum())
        med60 = L._rolling_median(c * v, L.DVOL_WINDOW)
        for key, scfg in state_cfgs.items():
            fired, bookable, _drops = L.run_config_census(
                scfg, o, h, lo, c, v, med60=med60)
            fi_all = np.nonzero(fired)[0]
            fi = fi_all[fi_all >= warmup_of[key]]
            fb = fi[bookable[fi]]
            for fc, fold in enumerate(fold_ids):
                msm = fi[fold_code[fi] == fc]
                state_fired_fold[key][fold] += int(msm.size)
                state_bookable_fold[key][fold] += int(
                    np.count_nonzero(bookable[msm]))
            if fb.size == 0:
                continue
            for cid, hold in configs_of_state[key]:
                if cid not in pooled:
                    continue
                ends = fb + hold
                okk = ends <= n - 1
                stats[cid]["death_censored_legs"] += int((~okk).sum())
                s2 = fb[okk] + 1
                if s2.size == 0:
                    continue
                e2 = ends[okk]
                lens = e2 - s2 + 1
                tot = int(lens.sum())
                idx = (np.repeat(s2, lens) + np.arange(tot, dtype=np.int64)
                       - np.repeat(np.cumsum(lens) - lens, lens))
                pos = np.zeros(n, dtype=bool)
                pos[idx] = True
                pdays = np.nonzero(pos)[0]
                cp = cal_pos[pdays]
                dropped = int((cp < 0).sum())
                if dropped:
                    counters["off_or_out_of_window_held_sessions"] += dropped
                # bincount: overlapping names on one calendar session must
                # EACH count (plain fancy += collapses duplicates)
                pooled[cid] += np.bincount(cp[cp >= 0], minlength=ncal)
                stats[cid]["positions_used"] += int(s2.size)
                stats[cid]["position_days"] += int(pdays.size)
    calendar_sha = canon_sha256(calendar)
    series_sha = {}
    for cid in pooled_cids:
        s = pooled[cid]
        stats[cid]["pooled_max"] = int(s.max())
        stats[cid]["pooled_nonzero_days"] = int(np.count_nonzero(s))
        series_sha[cid] = canon_sha256({
            "config_id": cid, "calendar_sha256": calendar_sha,
            "counts": [int(x) for x in s]})
    return {"counters": counters, "pooled": pooled, "stats": stats,
            "series_sha256": series_sha, "calendar_sha256": calendar_sha,
            "state_fired_fold": state_fired_fold,
            "state_bookable_fold": state_bookable_fold,
            "n_names": len(required)}


def verify_data_plane(cache_dir, retrieval_manifest_path=None, *,
                      freeze_path=None, census_path=None,
                      census_configs_path=None,
                      cohort_census_path=None) -> dict:
    """MANDATORY scored-path data-plane preflight (A7 F-1, GO condition C-2).

    Binds the live gitignored raw cache to the frozen chain BEFORE any
    scored computation.  Fail-closed: returns the PASS verdict artifact, or
    raises DataPlaneMismatch (INPUT_MISMATCH) - the E run is refused, never
    overridden.  Checks, in order:

      1. freeze identity: the committed S freeze is byte-pinned via
         verify_freeze (FREEZE_SHA256 + arm identities); an injected
         freeze path (tests/fixtures only) must still be status
         SELECTION_FROZEN and carry the 3 frozen arms verbatim;
      2. consumed-artifact pins vs data_manifests_sha256: p0_lib.py,
         p0_run.py, census_configs.json, p0_census.json,
         p0_census_cohort.json.gz, retrieval_manifest.json;
      3. retrieval-manifest commitment: a caller-supplied path that is not
         the COMMITTED p0/retrieval_manifest.json is REFUSED
         (substitution), and the committed file must hash to the freeze
         pin; schema/cycle_id must match the freeze;
      4. retrieval completeness: every pull status-200, pull set ==
         cohort-census set (both directions), SPY present;
      5. calendar + folds: SPY-pinned S0-window calendar re-derived and
         matched to the freeze calendar pin (n/first/last/sha256); freeze
         fold boundaries == the p0_lib calendar-thirds law;
      6. per-pull identity: cache file present for every required name;
         manifest digest pins (sha256_gz/sha256_raw) verified where
         carried; parsed served count == cohort-census served count
         (served0/short counter laws as in s_select.heavy_pass);
      7. pooled-series digests: the 3 arms' pooled daily position series
         rebuilt via the frozen census engines (census space) and compared
         EXACTLY (positions_used, position_days, death_censored_legs,
         pooled_max, pooled_nonzero_days, series_sha256) to the S freeze's
         pooled_series_stats (6fd58cc9.../495d9bca.../f55a14ba...);
      8. census cross-check: rebuilt per-config per-fold fired and
         bookable_fired == frozen p0_census.json rows EXACTLY (s_select
         r3 282-cell comparison approach, restricted to the 3 rebuilt
         states), plus the freeze's embedded per-fold census verbatim ==
         the census rows for the 3 arm cells.

    cache_dir stays caller-supplied (gitignored location, not committed);
    its CONTENT is bound by checks 4-8.  freeze_path/census_path/
    census_configs_path/cohort_census_path default to the committed
    artifacts and are overridable only for synthetic test fixtures.
    """
    checks: dict = {}

    def ok(name, detail):
        checks[name] = {"pass": True, "detail": detail}

    def fail(name, detail):
        checks[name] = {"pass": False, "detail": detail}
        raise DataPlaneMismatch({
            "schema": "stocks_search_v1_data_plane_preflight@1",
            "status": "INPUT_MISMATCH", "failed_check": name,
            "checks": checks, "law": DATA_PLANE_PREFLIGHT_LAW})

    def on_name_refuse(sym, detail):
        fail(detail["failed_check"], dict(detail, symbol=sym))

    # ---- 1. freeze identity ------------------------------------------------
    fp = Path(freeze_path) if freeze_path else _S_FREEZE_PATH
    production_freeze = fp.resolve() == _S_FREEZE_PATH.resolve()
    if production_freeze:
        vf = verify_freeze(fp)          # byte pin + arm identities
        ok("freeze_binding", {"mode": "committed_byte_pin",
                              "freeze_sha256": vf["freeze_sha256"],
                              "status": vf["status"], "n_cells": vf["n_cells"]})
    else:
        freeze = json.loads(fp.read_text())
        if freeze.get("status") != "SELECTION_FROZEN":
            fail("freeze_binding", {"mode": "injected", "status": "not frozen"})
        frozen = {c["config_id"]: c for c in freeze["selected_candidates"]}
        bad = []
        for cell in FROZEN_CELLS:
            got = frozen.get(cell["config_id"])
            if (got is None
                    or got["arm_identity_sha256"] != cell["arm_identity_sha256"]
                    or got["manifest_config_excerpt"]["params"] != cell["params"]
                    or got["manifest_config_excerpt"]["family"] != cell["family"]
                    or "pooled_series_stats" not in got):
                bad.append(cell["config_id"])
        if bad:
            fail("freeze_binding", {"mode": "injected", "bad_cells": bad})
        ok("freeze_binding", {
            "mode": "injected_fixture (authority owned by the caller)",
            "n_cells": len(FROZEN_CELLS)})
    freeze = json.loads(fp.read_text())
    pins = freeze.get("data_manifests_sha256") or {}
    cycle_id = freeze.get("cycle_id")

    # ---- 2. consumed-artifact pins ----------------------------------------
    for key in ("p0_lib.py", "p0_run.py", "census_configs.json",
                "p0_census.json", "p0_census_cohort.json.gz",
                "retrieval_manifest.json"):
        if key not in pins:
            fail("data_manifests_pins", {"missing_key": key})
    ok("data_manifests_pins", {"n_keys": len(pins)})

    L = load_p0_lib(expected_sha=pins["p0_lib.py"])
    ok("p0_lib_pin", {"sha256": pins["p0_lib.py"]})
    p0_run = _load_pinned_p0_run(pins["p0_run.py"])
    ok("p0_run_pin", {"sha256": pins["p0_run.py"]})

    ccp = Path(census_configs_path) if census_configs_path \
        else COMMITTED_CENSUS_CONFIGS_PATH
    if sha256_file(ccp) != pins["census_configs.json"]:
        fail("census_configs_pin", {"path": str(ccp),
                                    "expected": pins["census_configs.json"],
                                    "actual": sha256_file(ccp)})
    census_configs = json.loads(ccp.read_text())
    ok("census_configs_pin", {"path": str(ccp),
                              "n_configs": len(census_configs["configs"])})

    # ---- 3. retrieval-manifest commitment ----------------------------------
    mp = Path(retrieval_manifest_path) if retrieval_manifest_path is not None \
        else COMMITTED_RETRIEVAL_MANIFEST_PATH
    if mp.resolve() != COMMITTED_RETRIEVAL_MANIFEST_PATH.resolve():
        fail("retrieval_manifest_substitution_refused", {
            "law": "the scored path reads ONLY the committed "
                   "p0/retrieval_manifest.json; caller-supplied substitutes "
                   "are refused (A7 F-1)",
            "committed": str(COMMITTED_RETRIEVAL_MANIFEST_PATH),
            "received": str(mp)})
    manifest_sha = sha256_file(mp)
    if manifest_sha != pins["retrieval_manifest.json"]:
        fail("retrieval_manifest_sha_pin", {
            "path": str(mp), "expected": pins["retrieval_manifest.json"],
            "actual": manifest_sha})
    retrieval = json.loads(mp.read_text())
    if retrieval.get("schema") != "stocks_search_v1_retrieval@1" \
            or retrieval.get("cycle_id") != cycle_id:
        fail("retrieval_manifest_schema", {
            "schema": retrieval.get("schema"),
            "cycle_id": retrieval.get("cycle_id"),
            "freeze_cycle_id": cycle_id})
    ok("retrieval_manifest_pinned", {
        "path": str(mp), "sha256": manifest_sha,
        "n_pulls": len(retrieval.get("pulls", {}))})

    # ---- 4. completeness ----------------------------------------------------
    cp = Path(census_path) if census_path else COMMITTED_P0_CENSUS_PATH
    if sha256_file(cp) != pins["p0_census.json"]:
        fail("p0_census_pin", {"path": str(cp),
                               "expected": pins["p0_census.json"],
                               "actual": sha256_file(cp)})
    p0_census = json.loads(cp.read_text())
    ok("p0_census_pin", {"path": str(cp), "n_rows":
                         len(p0_census["per_config_per_fold"])})

    kop = Path(cohort_census_path) if cohort_census_path \
        else COMMITTED_COHORT_CENSUS_PATH
    if sha256_file(kop) != pins["p0_census_cohort.json.gz"]:
        fail("cohort_census_pin", {"path": str(kop),
                                   "expected": pins["p0_census_cohort.json.gz"],
                                   "actual": sha256_file(kop)})
    cohort_census = json.loads(_gzip_read(kop))
    ok("cohort_census_pin", {"path": str(kop), "n_names": len(cohort_census)})

    pulls = retrieval["pulls"]
    required = sorted(s for s, m in pulls.items() if m.get("status") == 200)
    bad_status = sorted(s for s, m in pulls.items() if m.get("status") != 200)
    if bad_status:
        fail("retrieval_complete_all_200", {"n_non_200": len(bad_status),
                                            "symbols": bad_status[:10]})
    if set(required) != set(cohort_census):
        fail("pull_set_equals_cohort_census", {
            "n_pulls": len(required), "n_cohort": len(cohort_census),
            "pulls_only": sorted(set(required) - set(cohort_census))[:10],
            "cohort_only": sorted(set(cohort_census) - set(required))[:10]})
    if "SPY" not in required:
        fail("spy_present", {"law": "F7 benchmark pin: SPY is a served "
                                    "cohort name and pins the calendar"})
    ok("retrieval_complete", {"n_required": len(required),
                              "n_digest_pinned_pulls":
                                  sum(1 for m in pulls.values()
                                      if "sha256_gz" in m)})

    # ---- 5. calendar + folds -----------------------------------------------
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        fail("cache_dir_present", {"path": str(cache_dir)})
    s0 = freeze["s0_window"]
    try:
        calendar, spy_sha = _build_calendar_from_cache(
            cache_dir, s0["start"], s0["end"])
    except DataPlaneMismatch as e:
        d = e.args[0] if isinstance(e.args[0], dict) else {}
        fail(d.get("failed_check", "calendar_build"),
             dict(d.get("detail", {})))
    cal_pin = freeze["calendar"]
    if (len(calendar) != cal_pin["n_sessions"]
            or calendar[0] != cal_pin["first_session"]
            or calendar[-1] != cal_pin["last_session"]
            or canon_sha256(calendar) != cal_pin["sha256"]
            or calendar[0] != s0["start"] or calendar[-1] != s0["end"]):
        fail("calendar_pin", {"n_sessions": len(calendar),
                              "first": calendar[0], "last": calendar[-1],
                              "sha256": canon_sha256(calendar),
                              "freeze_pin": cal_pin, "spy_sha256": spy_sha})
    b1f = freeze["folds"]["boundaries"]["B1"]
    b2f = freeze["folds"]["boundaries"]["B2"]
    if [b1f, b2f] != L.fold_boundaries(s0["start"], s0["end"]):
        fail("fold_boundaries_law", {"freeze": [b1f, b2f],
                                     "law": L.fold_boundaries(s0["start"],
                                                              s0["end"])})
    ok("calendar_and_folds", {"n_sessions": len(calendar),
                              "calendar_sha256": canon_sha256(calendar),
                              "b1": b1f, "b2": b2f})

    # ---- 6-8. rebuild + comparisons -----------------------------------------
    try:
        machinery = _arm_state_machinery(census_configs)
    except DataPlaneMismatch as e:
        d = e.args[0] if isinstance(e.args[0], dict) else {}
        fail(d.get("failed_check", "arm_state_machinery"),
             dict(d.get("detail", {})))
    rebuilt = _rebuild_data_plane(cache_dir, p0_run, L, retrieval,
                                  cohort_census, calendar, b1f, b2f,
                                  machinery, on_name_refuse)
    ok("per_pull_identity", {"n_names": rebuilt["n_names"],
                             **rebuilt["counters"]})

    cand_by_id = {c["config_id"]: c for c in freeze["selected_candidates"]}
    series_diffs = {}
    for cell in FROZEN_CELLS:
        cid = cell["config_id"]
        want = cand_by_id[cid]["pooled_series_stats"]
        got = dict(rebuilt["stats"][cid])
        got["series_sha256"] = rebuilt["series_sha256"][cid]
        diff = {k: {"freeze": want.get(k), "rebuilt": got.get(k)}
                for k in sorted(set(want) | set(got))
                if want.get(k) != got.get(k)}
        if diff:
            series_diffs[cid] = diff
    if series_diffs:
        fail("pooled_series_digests", series_diffs)
    ok("pooled_series_digests", {
        cid: {"series_sha256": rebuilt["series_sha256"][cid],
              "positions_used": rebuilt["stats"][cid]["positions_used"]}
        for cid in sorted(rebuilt["series_sha256"])})

    # census cross-check: s_select r3 comparison approach (exact equality),
    # restricted to the 3 rebuilt states; the freeze's embedded per-fold
    # census verbatim must ALSO equal the census rows for the 3 arm cells.
    rows_by_cid: dict[str, dict] = {}
    for r in p0_census["per_config_per_fold"]:
        rows_by_cid.setdefault(r["config_id"], {})[r["fold"]] = r
    excerpt_by_cid = {c["config_id"]:
                      c["manifest_config_excerpt"]["p0_census_per_fold_verbatim"]
                      for c in freeze["selected_candidates"]}
    excerpt_diffs = {}
    for cid, verbatim in excerpt_by_cid.items():
        for fold in ("F1", "F2", "F3"):
            if _canon_json(verbatim[fold]) != _canon_json(rows_by_cid[cid][fold]):
                excerpt_diffs[f"{cid}:{fold}"] = True
    if excerpt_diffs:
        fail("freeze_excerpt_census_equality",
             {"mismatched": sorted(excerpt_diffs)})
    ok("freeze_excerpt_census_equality", {"n_rows": 3 * len(excerpt_by_cid)})

    cell_diffs = {}
    n_cells = 0
    configs_checked = set()
    for cfg in census_configs["configs"]:
        cid = cfg["config_id"]
        key = machinery["state_key_of"][cid]
        if key not in machinery["state_cfgs"]:
            continue
        configs_checked.add(cid)
        rows = rows_by_cid.get(cid)
        if rows is None:
            cell_diffs[f"{cid}:missing_rows"] = True
            continue
        for fold in ("F1", "F2", "F3"):
            n_cells += 1
            want_f = rows[fold]["fired"]
            want_b = rows[fold]["bookable_fired"]
            got_f = rebuilt["state_fired_fold"][key][fold]
            got_b = rebuilt["state_bookable_fold"][key][fold]
            if got_f != want_f or got_b != want_b:
                cell_diffs[f"{cid}:{fold}"] = {
                    "want_fired": want_f, "got_fired": got_f,
                    "want_bookable_fired": want_b,
                    "got_bookable_fired": got_b}
    arm_cells = 3 * len(FROZEN_CELLS)
    if cell_diffs or n_cells < arm_cells:
        fail("census_cells_equal_p0_census", {
            "law": "rebuilt fired/bookable_fired must equal the frozen "
                   "p0_census.json rows EXACTLY (s_select r3 282-cell gate "
                   "form, restricted to the 3 rebuilt states)",
            "n_cells_checked": n_cells, "n_cells_required": arm_cells,
            "mismatched_cells": cell_diffs if cell_diffs else "none"})
    ok("census_cells_equal_p0_census", {
        "n_cells_checked": n_cells,
        "n_configs_checked": len(configs_checked),
        "n_configs_total": machinery["n_configs_total"],
        "n_arm_cells": arm_cells})

    return {
        "schema": "stocks_search_v1_data_plane_preflight@1",
        "status": "PASS",
        "checks": checks,
        "counters": rebuilt["counters"],
        "arms": {cid: {"series_sha256": rebuilt["series_sha256"][cid],
                       "positions_used": rebuilt["stats"][cid]["positions_used"],
                       "position_days": rebuilt["stats"][cid]["position_days"]}
                 for cid in sorted(rebuilt["series_sha256"])},
        "n_census_cells_checked": n_cells,
        "retrieval_empty_count_disclosure":
            RETRIEVAL_EMPTY_COUNT_DISCLOSURE_VERBATIM,
        "law": DATA_PLANE_PREFLIGHT_LAW,
    }
