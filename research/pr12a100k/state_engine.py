"""pr12a100k.state_engine — macro state engine (Lane I1b, cycle
PORTFOLIO-ROUTER-12ASSETS-100K-V1).

Weekly macro-regime identifier over three PIT-evidenced exogenous series,
consumed by the router lanes. NO PnL anywhere in this module: it produces
state labels, bands, percentiles, ages and anti-churn bookkeeping only.

FROZEN CONTRACT (dispatch packet I1b + ROUTER_POLICY_DESIGN_DRAFT §3 +
PIT_DOSSIER G-PIT-V1/V2/V3; deviations are incidents):

Decision clock
    Weekly, Friday 17:00 America/New_York.

V1 — policy momentum (EFFR, NY Fed JSON; G-PIT-V1 PASS_EVIDENCED)
    available_at(effectiveDate d) = d+1 15:00 ET (published ~09:00 ET next
    NY Fed business day; same-day revision window closes ~14:30 ET).
    PM = EFFR_now − EFFR_63-business-days-earlier in bp, where the business
    -day index is POSITIONAL over the usable EFFR series itself (row
    ``now_pos - 63``). Band: TIGHT >= +12.5 bp, EASE <= −12.5 bp, else MID.

V2 — risk/vol stress (VIX; channel of record = CBOE direct file
    ``raw/vix/VIX_History_cboe.csv``; G-PIT-V2 PASS_EVIDENCED)
    available_at(day d) = d 16:15 ET, PLUS the design-draft §3.4 uniform
    T−1 publication buffer (``published <= Thursday close``): at a Friday
    decision only observations with date <= decision_date − 1 calendar day
    are consulted. This reproduces the PIT_DOSSIER G-PIT-V2 application
    sentence verbatim ("Friday 17:00 ET decision consumes Thursday's close,
    margin 24h45m >= 24h") — see INTERPRETATION NOTE below.
    RV = percentile of the latest usable VIX close within the trailing 252
    usable observations (window ends at and INCLUDES the latest value; all
    window values are strictly older-available than the decision).
    Band: STRESS >= p80, else CALM.

V3 — energy term premium (DCOILBRENTEU − DCOILWTICO FRED CSVs; G-PIT-V3)
    FROZEN date rule: at a decision on calendar date D, use ONLY common
    observations with observation_date <= D − 10 calendar days; take the two
    series' latest such COMMON date (both non-missing); spread = brent − wti;
    ES = percentile of that spread within the trailing 252 common
    observations (same inclusive-rank convention as V2).
    Band: WAR >= p85, else BASE.

State ladder (frozen priority)
    1 WAR_ENERGY  if V3 WAR; 2 RISK_STRESS elif V2 STRESS;
    3 TIGHTENING elif V1 TIGHT; 4 EASING elif V1 EASE; 5 ABSTAIN else.

Staleness fail-closed (ABSTAIN, NEVER carry state forward)
    v1 stale if freshest usable effectiveDate is older than 10 calendar
    days; v2 stale if older than 5 BUSINESS days (Mon–Fri count, holidays
    counted as business days — conservative direction); v3 stale if the
    latest used common observation is older than 25 calendar days. Any
    missing input (no usable row, insufficient window history, NaN) also
    forces ABSTAIN.

Anti-churn
    Min-dwell: a candidate state must hold for 2 consecutive weekly
    observations before it becomes effective (effective at the 2nd
    observation); the very first observation initializes effective state.
    ABSTAIN bypasses dwell and is effective IMMEDIATELY (holding a prior
    tradeable state through an abstain week would be carrying state
    forward — forbidden).
    Episode merge: same-state runs of the effective sequence separated by
    fewer than 4 intervening weekly observations share one episode_id.
    Merge is an EPISODE-ACCOUNTING convention only: it never rewrites the
    weekly effective_state values (doing so would fabricate state during
    intervening weeks, including ABSTAIN weeks).
    KS3 whipsaw: more than 4 completed flips within the trailing 8 weekly
    observations of the effective sequence => whipsaw_flag (router
    flattens).

INTERPRETATION NOTE (V2 T−1): the raw G-PIT-V2 formula "usable from
d 16:15 ET" would nominally admit the decision Friday's own close (16:15 <
17:00); both PIT_DOSSIER's application sentence and design draft §3.4
("VIX Thursday close (Friday's VIX print lands ... inside the decision
hour)") pin the Friday decision to THURSDAY's close, so the engine applies
the extra obs_date <= decision_date − 1 buffer. The buffer is strictly
conservative: it can only cost staleness, never lookahead.

Percentile convention (documented, deterministic): weak/inclusive rank,
pct = 100 * count(window <= current) / len(window), window = trailing 252
observations ending at and including the current one.

age units: ages_days["v1"] and ["v3"] are CALENDAR days; ages_days["v2"]
is BUSINESS days (Mon–Fri, holidays counted) — each var is reported in the
unit its own staleness law uses.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd

try:  # sibling import when pr12a100k/ is on sys.path (tests, battery)
    import loaders
except ImportError:  # pragma: no cover - direct module execution
    from . import loaders  # type: ignore[no-reimport]

__all__ = [
    "STATES",
    "MacroPanel",
    "StateResult",
    "build_macro_panel",
    "compute_state",
    "state_timeline",
    "apply_dwell",
    "ladder",
]

DECISION_TZ = "America/New_York"
DECISION_HOURS = 17
DECISION_MINUTES = 0

V1_THRESHOLD_BP = 12.5      # half a standard 25bp hike per quarter
V2_STRESS_PCT = 80.0
V3_WAR_PCT = 85.0
PERCENTILE_WINDOW = 252     # trailing usable observations (inclusive)
V1_LAG_BUSINESS_ROWS = 63   # positional rows back in the EFFR series

V3_LAG_CALENDAR_DAYS = 10   # frozen G-PIT-V3 date rule
V2_TMINUS1_CALENDAR_DAYS = 1  # design-draft §3.4 uniform T−1 buffer (V2)

V1_STALE_CALENDAR_DAYS = 10
V2_STALE_BUSINESS_DAYS = 5
V3_STALE_CALENDAR_DAYS = 25

DWELL_WEEKS = 2             # min-dwell: effective at the 2nd observation
MERGE_GAP_WEEKS = 4         # same-state runs separated by < 4 weeks merge
WHIPSAW_WINDOW_WEEKS = 8
WHIPSAW_MAX_FLIPS = 4

STATES = ("WAR_ENERGY", "RISK_STRESS", "TIGHTENING", "EASING", "ABSTAIN")

RAW_STORE = os.path.expanduser("~/.my-quantitative-data/pr12a100k/raw")
MANIFEST_MACRO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data_manifest_macro.json"
)

DEFAULT_PATHS = {
    "effr": os.path.join(RAW_STORE, "effr",
                         "EFFR_nyfed_search_full_2016-01-01_2026-09-27.json"),
    "vix": os.path.join(RAW_STORE, "vix", "VIX_History_cboe.csv"),
    "brent": os.path.join(RAW_STORE, "brent", "DCOILBRENTEU_fredgraph.csv"),
    "wti": os.path.join(RAW_STORE, "wti", "DCOILWTICO_fredgraph.csv"),
}


# ---------------------------------------------------------------------------
# CBOE VIX history parser (channel of record for V2)
# ---------------------------------------------------------------------------

def _parse_cboe_vix(path: str) -> tuple[pd.Series, dict[str, Any]]:
    """Parse the CBOE-direct ``VIX_History_cboe.csv`` daily file.

    Layout: ``DATE,OPEN,HIGH,LOW,CLOSE`` with ``MM/DD/YYYY`` dates. Returns
    the CLOSE column as a date-indexed float Series (name ``VIX``) plus
    metadata. Fail-closed on missing file, wrong header, unparsable rows,
    duplicate dates or zero rows.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"CBOE VIX file not found: {path}")
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        lines = [ln.rstrip("\r\n") for ln in fh]
    lines = [ln for ln in lines if ln.strip() != ""]
    if not lines:
        raise ValueError(f"CBOE VIX CSV is empty: {path}")
    header = [h.strip() for h in lines[0].split(",")]
    if header[:5] != ["DATE", "OPEN", "HIGH", "LOW", "CLOSE"]:
        raise ValueError(
            f"CBOE VIX CSV header must be DATE,OPEN,HIGH,LOW,CLOSE; got {lines[0]!r}"
        )
    dates: list[str] = []
    closes: list[float] = []
    for i, ln in enumerate(lines[1:], start=2):
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) != 5:
            raise ValueError(f"CBOE VIX row {i} must have 5 fields, got {ln!r}")
        m, d, y = parts[0].split("/")
        iso = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        try:
            dates.append(pd.Timestamp(iso).date().isoformat())
            closes.append(float(parts[4]))
        except ValueError as exc:
            raise ValueError(f"CBOE VIX row {i}: unparsable {ln!r}") from exc
    idx = pd.to_datetime(dates)
    if idx.has_duplicates:
        dup = idx[idx.duplicated()][0]
        raise ValueError(f"CBOE VIX CSV has duplicate DATE {dup.date()}")
    s = pd.Series(closes, index=idx, name="VIX", dtype="float64")
    s.index.name = "observation_date"
    meta = {
        "series_name": "VIX",
        "channel": "cboe_direct",
        "n_obs": len(s),
        "n_missing": 0,
        "first_date": str(idx.min().date()),
        "last_date": str(idx.max().date()),
    }
    return s, meta


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _expected_sha256s() -> dict[str, str]:
    """Expected sha256 per series key, read from data_manifest_macro.json.

    brent/wti/effr come from ``series[].sha256``; the CBOE channel sha is
    only quoted inside the VIXCLS ``license_note`` and is regex-extracted.
    """
    out: dict[str, str] = {}
    with open(MANIFEST_MACRO, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    for key, rec in manifest["series"].items():
        out[key.lower() if key != "EFFR" else "effr"] = rec["sha256"]
    note = manifest["series"]["VIXCLS"].get("license_note", "")
    m = re.search(r"VIX_History_cboe\.csv \(sha256 ([0-9a-f]{64})", note)
    if m:
        out["vix"] = m.group(1)
    return out


# ---------------------------------------------------------------------------
# Timezone helpers
# ---------------------------------------------------------------------------

def _ny_ts(date: pd.Timestamp, hh: int, mm: int) -> pd.Timestamp:
    """Timezone-aware timestamp at ``hh:mm`` America/New_York on ``date``."""
    day = pd.Timestamp(date).tz_localize(None).normalize()
    return (day + pd.Timedelta(hours=hh, minutes=mm)).tz_localize(DECISION_TZ)


def _decision_friday_ts(friday: pd.Timestamp) -> pd.Timestamp:
    return _ny_ts(friday, DECISION_HOURS, DECISION_MINUTES)


def _to_utc_ns(ts: pd.Timestamp) -> int:
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize(DECISION_TZ)
    return int(ts.tz_convert("UTC").value)


def _naive_date(ts: pd.Timestamp) -> pd.Timestamp:
    """Calendar date of ``ts`` in America/New_York (wall-clock)."""
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        return pd.Timestamp(ts).normalize()
    return pd.Timestamp(ts.tz_convert(DECISION_TZ).date())


def _busdays_between(start_date: pd.Timestamp, end_date: pd.Timestamp) -> int:
    """Mon–Fri day count in the half-open interval (start, end] (dates)."""
    if end_date <= start_date:
        return 0
    return int(np.busday_count(
        np.datetime64(start_date.date().isoformat()),
        np.datetime64(end_date.date().isoformat()),
    ))


def _pct_rank_inclusive(window: np.ndarray, current: float) -> float:
    """Weak/inclusive percentile rank of ``current`` within ``window``."""
    return 100.0 * float(np.count_nonzero(window <= current)) / float(window.size)


# ---------------------------------------------------------------------------
# MacroPanel
# ---------------------------------------------------------------------------

@dataclass
class MacroPanel:
    """The three state-engine inputs plus derivation caches.

    ``effr``/``vix``/``brent``/``wti`` are date-indexed float Series (tz-
    naive calendar dates). Derived arrays are rebuilt in ``__post_init__``;
    ``truncate`` returns a new panel holding only observations a decision at
    ``ts`` could legally see under each series' own frozen rule.
    """

    effr: pd.Series
    vix: pd.Series
    brent: pd.Series
    wti: pd.Series
    sources: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.effr = self._clean(self.effr, "effr")
        self.vix = self._clean(self.vix, "vix")
        self.brent = self._clean(self.brent, "brent")
        self.wti = self._clean(self.wti, "wti")

        # --- EFFR: usable = non-NaN; available_at = d+1 15:00 ET -------
        e = self.effr.dropna().sort_index()
        self._e_dates = pd.DatetimeIndex(e.index)
        self._e_vals = e.to_numpy(dtype="float64")
        self._e_avail_ns = np.array(
            [_to_utc_ns(_ny_ts(d + pd.Timedelta(days=1), 15, 0))
             for d in self._e_dates],
            dtype="int64",
        )

        # --- VIX: usable = non-NaN CBOE closes; available_at = d 16:15 ET
        v = self.vix.dropna().sort_index()
        self._v_dates = pd.DatetimeIndex(v.index)
        self._v_vals = v.to_numpy(dtype="float64")
        self._v_avail_ns = np.array(
            [_to_utc_ns(_ny_ts(d, 16, 15)) for d in self._v_dates],
            dtype="int64",
        )
        # date keys normalized to NANOSECOND ints: pandas-3 ``asi8`` returns
        # the index's OWN unit (us for FRED-parsed dates) while
        # ``Timestamp.value`` is always ns — mixing them silently corrupts
        # searchsorted cursors (same trap loaders.asof guards against).
        self._v_dates_ns = self._v_dates.as_unit("ns").asi8

        # --- Brent/WTI common series (both non-NaN on the same date) ---
        b = self.brent.dropna().sort_index()
        w = self.wti.dropna().sort_index()
        common = b.index.intersection(w.index)
        self._c_dates = pd.DatetimeIndex(common)
        self._c_spread = (b.loc[common].to_numpy(dtype="float64")
                          - w.loc[common].to_numpy(dtype="float64"))
        self._c_dates_ns = self._c_dates.as_unit("ns").asi8

    @staticmethod
    def _clean(s: pd.Series, name: str) -> pd.Series:
        if not isinstance(s, pd.Series):
            raise TypeError(f"{name} must be a pandas Series")
        if s.index.has_duplicates:
            raise ValueError(f"{name} index has duplicate dates")
        s = s.sort_index()
        if not isinstance(s.index, pd.DatetimeIndex):
            raise ValueError(f"{name} index must be a DatetimeIndex of dates")
        if (s.index != s.index.normalize()).any():
            raise ValueError(f"{name} index must be calendar dates (midnight)")
        return s

    # -- derived-cursor helpers -------------------------------------------

    def _effr_cursor(self, dec_ns: int) -> int:
        return int(self._e_avail_ns.searchsorted(dec_ns, side="right")) - 1

    def _vix_cursor(self, dec_ns: int, obs_cutoff_ns: int) -> int:
        by_avail = int(self._v_avail_ns.searchsorted(dec_ns, side="right")) - 1
        by_date = int(self._v_dates_ns.searchsorted(obs_cutoff_ns, side="right")) - 1
        return min(by_avail, by_date)

    def _common_cursor(self, cutoff_ns: int) -> int:
        return int(self._c_dates_ns.searchsorted(cutoff_ns, side="right")) - 1

    # -- no-lookahead truncation ------------------------------------------

    def truncate(self, ts: pd.Timestamp) -> "MacroPanel":
        """Panel restricted to what a decision at ``ts`` could see.

        EFFR/VIX keep rows with available_at <= ts (VIX additionally obeys
        its T−1 date rule); brent/wti keep observation_date <= date(ts) − 10
        calendar days — exactly the frozen visibility rules, so a truncated
        panel reproduces byte-identical StateResults (the no-lookahead law).
        """
        dec_ns = _to_utc_ns(pd.Timestamp(ts))
        dec_date = _naive_date(pd.Timestamp(ts))
        e_keep = self._e_dates[self._e_avail_ns <= dec_ns]
        v_cutoff_ns = int((dec_date - pd.Timedelta(
            days=V2_TMINUS1_CALENDAR_DAYS)).value)
        v_keep = self._v_dates[
            (self._v_avail_ns <= dec_ns) & (self._v_dates_ns <= v_cutoff_ns)]
        c_cutoff_ns = int((dec_date - pd.Timedelta(
            days=V3_LAG_CALENDAR_DAYS)).value)
        c_keep = self._c_dates[self._c_dates_ns <= c_cutoff_ns]

        effr = pd.Series(
            self._e_vals[: len(e_keep)], index=pd.DatetimeIndex(e_keep), name="EFFR")
        vix = pd.Series(
            self._v_vals[: len(v_keep)], index=pd.DatetimeIndex(v_keep), name="VIX")
        brent = pd.Series(
            self.brent.loc[: c_keep.max()].dropna()
            if len(c_keep) else self.brent.iloc[:0],
            name=self.brent.name)
        wti = pd.Series(
            self.wti.loc[: c_keep.max()].dropna()
            if len(c_keep) else self.wti.iloc[:0],
            name=self.wti.name)
        return MacroPanel(effr=effr, vix=vix, brent=brent, wti=wti,
                          sources=dict(self.sources))

    # -- epoch (first computable decision Friday) --------------------------

    def epoch_ts(self) -> pd.Timestamp | None:
        """Earliest decision time at which all three variables are computable.

        Deterministic function of the panel contents; stable under
        ``truncate`` (truncation only removes late observations).
        """
        need = PERCENTILE_WINDOW
        if len(self._e_vals) < V1_LAG_BUSINESS_ROWS + 1:
            return None
        if len(self._v_vals) < need:
            return None
        if len(self._c_spread) < need:
            return None
        v1_ready = _utc_ts_from_ns(int(self._e_avail_ns[V1_LAG_BUSINESS_ROWS]))
        # v2 ready when the 252nd obs is both published (16:15) and T−1 legal
        v2_ready = max(
            _utc_ts_from_ns(int(self._v_avail_ns[need - 1])),
            _ny_ts(self._v_dates[need - 1] + pd.Timedelta(
                days=V2_TMINUS1_CALENDAR_DAYS), DECISION_HOURS, DECISION_MINUTES),
        )
        # v3 ready when cutoff can reach the 252nd common observation
        v3_ready = _ny_ts(self._c_dates[need - 1] + pd.Timedelta(
            days=V3_LAG_CALENDAR_DAYS), DECISION_HOURS, DECISION_MINUTES)
        ready = max(v1_ready, v2_ready, v3_ready)
        # first Friday 17:00 ET at or after `ready`
        day = _naive_date(ready)
        days_ahead = (4 - day.dayofweek) % 7  # Monday=0 .. Friday=4
        cand = _decision_friday_ts(day + pd.Timedelta(days=days_ahead))
        while cand < ready:
            cand = _decision_friday_ts(_naive_date(cand) + pd.Timedelta(days=7))
        return cand


def _utc_ts_from_ns(ns: int) -> pd.Timestamp:
    return pd.Timestamp(ns, unit="ns", tz="UTC")


# ---------------------------------------------------------------------------
# Per-variable evaluation
# ---------------------------------------------------------------------------

def _eval_v1(dec_ns: int, dec_date: pd.Timestamp, p: MacroPanel) -> dict[str, Any]:
    pos = p._effr_cursor(dec_ns)
    out: dict[str, Any] = {
        "pm_bp": None, "band": None, "age": None, "stale": True,
        "ok": False, "used_date": None,
    }
    if pos < V1_LAG_BUSINESS_ROWS:
        return out
    pm_bp = (p._e_vals[pos] - p._e_vals[pos - V1_LAG_BUSINESS_ROWS]) * 100.0
    used = p._e_dates[pos]
    age = int((dec_date - used).days)
    band = "TIGHT" if pm_bp >= V1_THRESHOLD_BP else (
        "EASE" if pm_bp <= -V1_THRESHOLD_BP else "MID")
    out.update(pm_bp=pm_bp, band=band, age=age,
               stale=age > V1_STALE_CALENDAR_DAYS, ok=True,
               used_date=used.date().isoformat())
    return out


def _eval_v2(dec_ns: int, dec_date: pd.Timestamp, p: MacroPanel) -> dict[str, Any]:
    cutoff_ns = int((dec_date - pd.Timedelta(
        days=V2_TMINUS1_CALENDAR_DAYS)).value)
    pos = p._vix_cursor(dec_ns, cutoff_ns)
    out: dict[str, Any] = {
        "pct": None, "band": None, "age": None, "stale": True,
        "ok": False, "used_date": None,
    }
    if pos < PERCENTILE_WINDOW - 1:
        return out
    window = p._v_vals[pos - PERCENTILE_WINDOW + 1: pos + 1]
    cur = float(p._v_vals[pos])
    pct = _pct_rank_inclusive(window, cur)
    used = p._v_dates[pos]
    age = _busdays_between(used, dec_date)
    out.update(pct=pct, band="STRESS" if pct >= V2_STRESS_PCT else "CALM",
               age=age, stale=age > V2_STALE_BUSINESS_DAYS, ok=True,
               used_date=used.date().isoformat())
    return out


def _eval_v3(dec_ns: int, dec_date: pd.Timestamp, p: MacroPanel) -> dict[str, Any]:
    cutoff_ns = int((dec_date - pd.Timedelta(days=V3_LAG_CALENDAR_DAYS)).value)
    pos = p._common_cursor(cutoff_ns)
    out: dict[str, Any] = {
        "spread": None, "pct": None, "band": None, "age": None,
        "stale": True, "ok": False, "used_date": None,
    }
    if pos < PERCENTILE_WINDOW - 1:
        return out
    window = p._c_spread[pos - PERCENTILE_WINDOW + 1: pos + 1]
    cur = float(p._c_spread[pos])
    pct = _pct_rank_inclusive(window, cur)
    used = p._c_dates[pos]
    age = int((dec_date - used).days)
    out.update(spread=cur, pct=pct,
               band="WAR" if pct >= V3_WAR_PCT else "BASE",
               age=age, stale=age > V3_STALE_CALENDAR_DAYS, ok=True,
               used_date=used.date().isoformat())
    return out


def ladder(v1_band: str | None, v2_band: str | None, v3_band: str | None) -> str:
    """Frozen priority ladder over the three per-variable bands."""
    if v3_band == "WAR":
        return "WAR_ENERGY"
    if v2_band == "STRESS":
        return "RISK_STRESS"
    if v1_band == "TIGHT":
        return "TIGHTENING"
    if v1_band == "EASE":
        return "EASING"
    return "ABSTAIN"


def _candidate_entry(decision_ts: pd.Timestamp, p: MacroPanel) -> dict[str, Any]:
    dec_ns = _to_utc_ns(decision_ts)
    dec_date = _naive_date(decision_ts)
    v1 = _eval_v1(dec_ns, dec_date, p)
    v2 = _eval_v2(dec_ns, dec_date, p)
    v3 = _eval_v3(dec_ns, dec_date, p)
    ok = v1["ok"] and v2["ok"] and v3["ok"]
    stale = v1["stale"] or v2["stale"] or v3["stale"]
    if not ok or stale:
        state = "ABSTAIN"
    else:
        state = ladder(v1["band"], v2["band"], v3["band"])
    return {
        "decision_ts": decision_ts,
        "state": state,
        "v1": v1, "v2": v2, "v3": v3,
        "stale_flags": {"v1": bool(v1["stale"] or not v1["ok"]),
                        "v2": bool(v2["stale"] or not v2["ok"]),
                        "v3": bool(v3["stale"] or not v3["ok"])},
    }


# ---------------------------------------------------------------------------
# Anti-churn (pure functions over weekly candidate sequences)
# ---------------------------------------------------------------------------

def apply_dwell(candidates: Sequence[str]) -> list[str]:
    """Min-dwell: a NEW state becomes effective at its 2nd consecutive
    weekly observation; ABSTAIN is effective immediately (fail-closed, no
    carry-forward); the first observation initializes.
    """
    eff: list[str] = []
    for i, c in enumerate(candidates):
        if i == 0:
            eff.append(c)
        elif c == "ABSTAIN":
            eff.append("ABSTAIN")
        elif c == eff[-1]:
            eff.append(c)
        elif c == candidates[i - 1]:
            eff.append(c)          # 2nd consecutive obs of the new state
        else:
            eff.append(eff[-1])    # dwell not yet satisfied, hold
    return eff


def _whipsaw_flags(effective: Sequence[str]) -> list[bool]:
    flags: list[bool] = []
    for i in range(len(effective)):
        lo = max(0, i - WHIPSAW_WINDOW_WEEKS + 1)
        flips = sum(1 for j in range(lo + 1, i + 1)
                    if effective[j] != effective[j - 1])
        flags.append(flips > WHIPSAW_MAX_FLIPS)
    return flags


def _episode_ids(effective: Sequence[str]) -> list[str | None]:
    """Merged episode ids: same-state runs separated by < MERGE_GAP_WEEKS
    intervening weekly observations share one id. Ids are chronological
    ``EP###`` over merged episodes; ABSTAIN runs get ids too (uniform).
    """
    n = len(effective)
    if n == 0:
        return []
    # raw runs: (state, start, end)
    runs: list[tuple[str, int, int]] = []
    s = 0
    for i in range(1, n + 1):
        if i == n or effective[i] != effective[s]:
            runs.append((effective[s], s, i - 1))
            s = i
    owner = list(range(len(runs)))  # union-find over run indices

    def find(x: int) -> int:
        while owner[x] != x:
            owner[x] = owner[owner[x]]
            x = owner[x]
        return x

    for a in range(len(runs) - 1):
        for b in range(a + 1, len(runs)):
            if runs[a][0] != runs[b][0]:
                continue
            gap = runs[b][1] - runs[a][2] - 1  # intervening weekly obs
            if gap < MERGE_GAP_WEEKS:
                ra, rb = find(a), find(b)
                if ra != rb:
                    owner[max(ra, rb)] = min(ra, rb)

    # chronological merged-episode numbering by the minimum run index
    roots = sorted({find(i) for i in range(len(runs))})
    number = {r: k + 1 for k, r in enumerate(roots)}
    ids: list[str | None] = []
    for a, (_state, start, end) in enumerate(runs):
        ep = f"EP{number[find(a)]:03d}"
        ids.extend([ep] * (end - start + 1))
    return ids


# ---------------------------------------------------------------------------
# Chain construction (single source of truth for compute_state / timeline)
# ---------------------------------------------------------------------------

def _chain_fridays(p: MacroPanel, upto_ts: pd.Timestamp) -> list[pd.Timestamp]:
    epoch = p.epoch_ts()
    if epoch is None:
        return []
    upto = pd.Timestamp(upto_ts)
    if upto.tzinfo is None:
        upto = upto.tz_localize(DECISION_TZ)
    fridays: list[pd.Timestamp] = []
    f = epoch
    while f <= upto:
        fridays.append(f)
        f = _decision_friday_ts(_naive_date(f) + pd.Timedelta(days=7))
    return fridays


def _chain_entries(p: MacroPanel, upto_ts: pd.Timestamp) -> list[dict[str, Any]]:
    """Candidate entries at every decision Friday 17:00 ET <= ``upto_ts``,
    plus (when ``upto_ts`` is later than the last canonical Friday stamp)
    one final entry evaluated exactly at ``upto_ts``. Only data available at
    each entry's own timestamp is consulted — the no-lookahead law.
    """
    entries = [_candidate_entry(f, p) for f in _chain_fridays(p, upto_ts)]
    upto = pd.Timestamp(upto_ts)
    if upto.tzinfo is None:
        upto = upto.tz_localize(DECISION_TZ)
    if entries and upto > entries[-1]["decision_ts"]:
        entries.append(_candidate_entry(upto, p))
    # anti-churn over the candidate sequence
    eff = apply_dwell([e["state"] for e in entries])
    whi = _whipsaw_flags(eff)
    epi = _episode_ids(eff)
    for e, ef, wf, ep in zip(entries, eff, whi, epi):
        e["effective_state"] = ef
        e["whipsaw_flag"] = wf
        e["episode_id"] = ep
    return entries


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class StateResult:
    """One decision's full state readout (frozen field set)."""

    decision_ts: str
    state: str
    effective_state: str
    vars: dict[str, Any]
    ages_days: dict[str, Any]
    stale_flags: dict[str, bool]
    whipsaw_flag: bool
    episode_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_ts": self.decision_ts,
            "state": self.state,
            "effective_state": self.effective_state,
            "vars": dict(self.vars),
            "ages_days": dict(self.ages_days),
            "stale_flags": dict(self.stale_flags),
            "whipsaw_flag": self.whipsaw_flag,
            "episode_id": self.episode_id,
        }

    def to_json(self) -> str:
        """Canonical JSON bytes (sorted keys, rounded floats)."""
        return json.dumps(self.to_dict(), sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False)


def _result_from_entry(e: dict[str, Any]) -> StateResult:
    v1, v2, v3 = e["v1"], e["v2"], e["v3"]
    return StateResult(
        decision_ts=pd.Timestamp(e["decision_ts"]).isoformat(),
        state=e["state"],
        effective_state=e["effective_state"],
        vars={
            "v1_pm_bp": None if v1["pm_bp"] is None else round(float(v1["pm_bp"]), 6),
            "v1_band": v1["band"],
            "v2_pct": None if v2["pct"] is None else round(float(v2["pct"]), 6),
            "v2_band": v2["band"],
            "v3_spread": None if v3["spread"] is None else round(float(v3["spread"]), 6),
            "v3_pct": None if v3["pct"] is None else round(float(v3["pct"]), 6),
            "v3_band": v3["band"],
        },
        ages_days={"v1": v1["age"], "v2": v2["age"], "v3": v3["age"]},
        stale_flags=dict(e["stale_flags"]),
        whipsaw_flag=bool(e["whipsaw_flag"]),
        episode_id=e["episode_id"],
    )


def compute_state(decision_ts: pd.Timestamp | str,
                  macro: MacroPanel) -> StateResult:
    """State readout at ``decision_ts`` (must be a Friday in America/New_York).

    The effective state / whipsaw flag / episode id are computed over the
    full chain of decision Fridays from the panel epoch up to
    ``decision_ts`` — each chain entry consults only data available at its
    own timestamp, so truncating the panel at ``decision_ts`` reproduces a
    byte-identical result (the ERP-tracka truncation law).
    """
    ts = pd.Timestamp(decision_ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize(DECISION_TZ)
    else:
        ts = ts.tz_convert(DECISION_TZ)
    if _naive_date(ts).dayofweek != 4:
        raise ValueError(
            f"decision clock is weekly Friday 17:00 {DECISION_TZ}; "
            f"{ts.isoformat()} is not a Friday")
    entries = _chain_entries(macro, ts)
    if not entries:
        epoch = macro.epoch_ts()
        v = {"v1_pm_bp": None, "v1_band": None, "v2_pct": None,
             "v2_band": None, "v3_spread": None, "v3_pct": None,
             "v3_band": None}
        return StateResult(
            decision_ts=ts.isoformat(), state="ABSTAIN",
            effective_state="ABSTAIN", vars=v,
            ages_days={"v1": None, "v2": None, "v3": None},
            stale_flags={"v1": True, "v2": True, "v3": True},
            whipsaw_flag=False, episode_id=None)
    return _result_from_entry(entries[-1])


_TIMELINE_COLUMNS = [
    "decision_ts", "state", "effective_state",
    "v1_pm_bp", "v1_band", "v2_pct", "v2_band", "v3_spread", "v3_pct",
    "v3_band", "age_v1_days", "age_v2_busdays", "age_v3_days",
    "stale_v1", "stale_v2", "stale_v3", "whipsaw_flag", "episode_id",
]


def state_timeline(panel: MacroPanel,
                   fridays: Iterable[pd.Timestamp | str]) -> pd.DataFrame:
    """One deterministic row per requested decision Friday.

    Rows are exactly ``compute_state(f, panel)`` flattened; the chain is
    built once to the last requested Friday (identical by construction).
    """
    fr = [pd.Timestamp(f) for f in fridays]
    if not fr:
        return pd.DataFrame(columns=_TIMELINE_COLUMNS)
    for f in fr:
        if _naive_date(f).dayofweek != 4:
            raise ValueError(f"state_timeline: {f} is not a Friday")
    # normalize every requested Friday to its canonical 17:00 ET decision
    # stamp BEFORE computing the chain cutoff, else a naive date truncates
    # the chain at midnight and the last Friday goes fail-closed ABSTAIN.
    fr = [f if f.tzinfo is not None else _decision_friday_ts(f)
          for f in fr]
    entries = _chain_entries(panel, max(fr))
    by_ts = {pd.Timestamp(e["decision_ts"]).isoformat(): e for e in entries}
    rows = []
    for f in fr:
        key = f.tz_convert(DECISION_TZ).isoformat()
        if key not in by_ts:
            # a Friday before the panel epoch: fail-closed abstain row
            res = StateResult(
                decision_ts=key, state="ABSTAIN", effective_state="ABSTAIN",
                vars={"v1_pm_bp": None, "v1_band": None, "v2_pct": None,
                      "v2_band": None, "v3_spread": None, "v3_pct": None,
                      "v3_band": None},
                ages_days={"v1": None, "v2": None, "v3": None},
                stale_flags={"v1": True, "v2": True, "v3": True},
                whipsaw_flag=False, episode_id=None)
        else:
            res = _result_from_entry(by_ts[key])
        rows.append({
            "decision_ts": res.decision_ts,
            "state": res.state,
            "effective_state": res.effective_state,
            "v1_pm_bp": res.vars["v1_pm_bp"],
            "v1_band": res.vars["v1_band"],
            "v2_pct": res.vars["v2_pct"],
            "v2_band": res.vars["v2_band"],
            "v3_spread": res.vars["v3_spread"],
            "v3_pct": res.vars["v3_pct"],
            "v3_band": res.vars["v3_band"],
            "age_v1_days": res.ages_days["v1"],
            "age_v2_busdays": res.ages_days["v2"],
            "age_v3_days": res.ages_days["v3"],
            "stale_v1": res.stale_flags["v1"],
            "stale_v2": res.stale_flags["v2"],
            "stale_v3": res.stale_flags["v3"],
            "whipsaw_flag": res.whipsaw_flag,
            "episode_id": res.episode_id,
        })
    return pd.DataFrame(rows, columns=_TIMELINE_COLUMNS)


def build_macro_panel(paths: dict[str, str] | None = None) -> MacroPanel:
    """Load the panel from raw files via the frozen loader layer.

    ``paths`` may override any of ``effr``/``vix``/``brent``/``wti``. The
    CBOE VIX channel of record is parsed by this module; EFFR and the FRED
    CSVs go through ``loaders.load_macro_series``. sha256s are verified
    against ``data_manifest_macro.json`` for the default raw-store paths
    (fail-closed on mismatch); overridden paths skip verification.
    """
    p = dict(DEFAULT_PATHS)
    if paths:
        unknown = set(paths) - set(DEFAULT_PATHS)
        if unknown:
            raise ValueError(f"unknown panel path keys {sorted(unknown)}")
        p.update(paths)

    effr, me = loaders.load_macro_series(p["effr"], "nyfed_effr_json")
    vix, mv = _parse_cboe_vix(p["vix"])
    brent, mb = loaders.load_macro_series(p["brent"], "fredgraph_csv")
    wti, mw = loaders.load_macro_series(p["wti"], "fredgraph_csv")

    sources = {"effr": me, "vix": mv, "brent": mb, "wti": mw}
    for key in ("effr", "vix", "brent", "wti"):
        sources[key]["path"] = p[key]
        sources[key]["sha256"] = _sha256_file(p[key])

    if paths is None and os.path.isfile(MANIFEST_MACRO):
        expected = _expected_sha256s()
        for key, want in expected.items():
            if key in sources and want != sources[key]["sha256"]:
                raise ValueError(
                    f"{key} sha256 mismatch vs data_manifest_macro.json: "
                    f"expected {want}, got {sources[key]['sha256']} "
                    f"({p[key]})")

    return MacroPanel(effr=effr, vix=vix, brent=brent, wti=wti,
                      sources=sources)
