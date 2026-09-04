"""A7-N novelty measurement for STOCKS-FREE-V5 (independent audit lane).

Measures Spearman rank correlations between each of the six V5 blind-proposal
ANCHOR features and (a) the four V4 reference features reconstructed from the
V4 terminal family modules, (b) the forbidden-family feature proxies named in
research/control/stocks_free_v5_run/forbidden_family_inventory.json, and
(c) the other proposals' anchor features (six-way matrix).

AUDIT DISCIPLINE (PLAN_stocks_v5.md section 8):
* FEATURE / RANK ARITHMETIC ONLY -- zero PnL, zero portfolio returns, zero
  scored metrics of any kind are computed here.
* All reads are S0-bounded: no session after 2025-07-31 is ever read.
* SEC conditioning goes exclusively through the canonical bridge
  research/assets/stocks/pit_conditioning.py (aggregate_sector_asof with the
  proposal-declared max_filing_gap_days); records are pre-filtered per field
  to the frozen panel purely for runtime -- the bridge applies its own field
  filter and sector mapping, so results are identical to passing the full
  store.
* V4 reference features are reconstructed with the V4 terminal's own modules:
  research/stocks_free_v4/family_semivar/signals.py (semivariance_share,
  total_sum_sq) and research/stocks_free_v4/family_participation (shock
  windows), per tests/assets/stocks/test_v4_family_semivar.py and
  test_v4_family_participation.py.

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python \
      research/audits/stocks_free_v5/a7_n_novelty_measure.py measure
      ... compose   (writes the audit artifact after human review of `measure`)
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKTREE))

from research.assets.stocks.pit_conditioning import (  # noqa: E402
    SECTOR_UNIVERSE,
    SectorObservation,
    aggregate_sector_asof,
)
from research.data_fusion.models import NormalizedRecord  # noqa: E402
from research.stocks_free_v4.family_semivar.signals import (  # noqa: E402
    semivariance_share,
    total_sum_sq,
)
from research.stocks_free_v4.family_participation.config import (  # noqa: E402
    SHOCK_WINDOWS,
    ShockWindows,
)

SNAPSHOT = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1/.staging"
)
SEC_DIR = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v5/p0-a3-data/.staging_sec"
)

SECTORS = tuple(SECTOR_UNIVERSE)  # 11 sector ETFs, frozen order
S0_START = "2018-04-04"
S0_END = "2025-07-31"
FOLDS = (
    ("S0_FOLD_1", "2018-04-04", "2020-09-01"),
    ("S0_FOLD_2", "2020-09-10", "2023-02-09"),
    ("S0_FOLD_3", "2023-02-17", "2025-07-24"),
)

MIN_COMMON_SECTORS = 6  # below this a cross-sectional rank rho is meaningless

FIELD_ASSETS = "us-gaap:Assets"
FIELD_CASH = "us-gaap:CashAndCashEquivalentsAtCarryingValue"
FIELD_FLOAT = "dei:EntityPublicFloat"
FIELD_LSE = "us-gaap:LiabilitiesAndStockholdersEquity"
FIELD_CURR = "us-gaap:AssetsCurrent"

# proposal -> declared SEC inputs (field, max_filing_gap_days, coverage floor)
SEC_DECL = {
    "a4_h1": [(FIELD_ASSETS, 400, 0.60)],
    "a4_h2": [(FIELD_CASH, 400, 0.60), (FIELD_ASSETS, 400, 0.60)],
    "a5_h1": [(FIELD_FLOAT, 550, 0.60), (FIELD_LSE, 550, 0.60)],
    "a6_h1": [(FIELD_CURR, 200, 0.40), (FIELD_ASSETS, 200, 0.40)],
}

A6_CENSUS_9 = ("XLB", "XLC", "XLE", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY")


# --------------------------------------------------------------------------- #
# small utilities
# --------------------------------------------------------------------------- #
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def avg_ranks(vals: list[float]) -> list[float]:
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    n = len(vals)
    while i < n:
        j = i
        while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs, ys) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    rx, ry = avg_ranks(list(xs)), avg_ranks(list(ys))
    mx = math.fsum(rx) / n
    my = math.fsum(ry) / n
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = math.fsum((a - mx) ** 2 for a in rx)
    syy = math.fsum((b - my) ** 2 for b in ry)
    if sxx <= 0.0 or syy <= 0.0:
        return None
    return sxy / math.sqrt(sxx * syy)


def pearson(xs, ys) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    mx = math.fsum(xs) / n
    my = math.fsum(ys) / n
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = math.fsum((a - mx) ** 2 for a in xs)
    syy = math.fsum((b - my) ** 2 for b in ys)
    if sxx <= 1e-300 or syy <= 1e-300:
        return None
    return sxy / math.sqrt(sxx * syy)


# --------------------------------------------------------------------------- #
# data loading (read-only, S0-bounded)
# --------------------------------------------------------------------------- #
def load_snapshot():
    master = sorted(
        v["datetime"] for v in json.load(open(SNAPSHOT / "SPY_all_p1.json"))["values"]
    )
    master = [d for d in master if d <= S0_END]
    assert master[0] == "2010-01-04" and master[-1] == S0_END
    assert all(master[i] < master[i + 1] for i in range(len(master) - 1))

    close_all: dict[str, list[float | None]] = {}
    dv: dict[str, list[float | None]] = {}
    presence: dict[str, set[str]] = {}
    pins: dict[str, str] = {}

    for s in ["SPY"] + list(SECTORS):
        path = SNAPSHOT / f"{s}_all_p1.json"
        pins[f"{s}_all_p1.json"] = sha256_file(path)
        payload = json.load(open(path))
        cmap = {v["datetime"]: float(v["close"]) for v in payload["values"]}
        presence[s] = {v["datetime"] for v in payload["values"]}
        close_all[s] = [cmap.get(d) for d in master]

    for s in SECTORS:
        path = SNAPSHOT / f"{s}_none_p1.json"
        pins[f"{s}_none_p1.json"] = sha256_file(path)
        payload = json.load(open(path))
        dmap = {
            v["datetime"]: float(v["close"]) * float(v["volume"])
            for v in payload["values"]
        }
        dv[s] = [dmap.get(d) for d in master]

    return master, close_all, dv, presence, pins


def build_returns(master, close_all):
    """Master-aligned close-to-close adjusted returns (None where undefined)."""
    ret: dict[str, list[float | None]] = {}
    for s, closes in close_all.items():
        out: list[float | None] = [None] * len(closes)
        for i in range(1, len(closes)):
            a, b = closes[i - 1], closes[i]
            if a is not None and b is not None:
                out[i] = b / a - 1.0
        ret[s] = out
    return ret


def window_ok(series, i: int, w: int) -> bool:
    if i + 1 < w:
        return False
    seg = series[i - w + 1: i + 1]
    return all(v is not None for v in seg)


# --------------------------------------------------------------------------- #
# V4 reference features (terminal modules) + forbidden proxies
# --------------------------------------------------------------------------- #
def ref_semivar_shape_126(ret, s, i):
    if not window_ok(ret[s], i, 126):
        return None
    return semivariance_share([float(v) for v in ret[s][i - 125: i + 1]])


def ref_vollevel_126(ret, s, i):
    if not window_ok(ret[s], i, 126):
        return None
    return total_sum_sq([float(v) for v in ret[s][i - 125: i + 1]])


def ref_vollevel_63(ret, s, i):
    if not window_ok(ret[s], i, 63):
        return None
    return total_sum_sq([float(v) for v in ret[s][i - 62: i + 1]])


def _dv_mean(dv_row, i, a: int, b: int) -> float | None:
    lo, hi = i - a, i - b
    if lo < 0 or hi >= len(dv_row):
        return None
    seg = dv_row[lo: hi + 1]
    if any(v is None for v in seg):
        return None
    return math.fsum(float(v) for v in seg) / len(seg)


def ref_shock(dv, s, i, windows: ShockWindows):
    num = _dv_mean(dv[s], i, windows.num_start_back, windows.num_end_back)
    den = _dv_mean(dv[s], i, windows.den_start_back, windows.den_end_back)
    if num is None or den is None or den <= 0.0:
        return None
    return num / den


def ref_mom_12_1(close_all, s, i):
    closes = close_all[s]
    if i < 252 or closes[i] is None or closes[i - 21] is None or closes[i - 252] is None:
        return None
    return closes[i - 21] / closes[i - 252] - 1.0


def ref_sma200_dist(close_all, s, i):
    closes = close_all[s]
    if i < 199:
        return None
    win = closes[i - 199: i + 1]
    if any(v is None for v in win):
        return None
    sma = math.fsum(float(v) for v in win) / 200.0
    if sma <= 0.0:
        return None
    return float(closes[i]) / sma - 1.0


# --------------------------------------------------------------------------- #
# SEC bridge panels
# --------------------------------------------------------------------------- #
def load_panel_filers():
    panel = json.load(open(SEC_DIR / "panel.json"))["panel"]
    filer_sectors: dict[str, str] = {}
    per_sector_counts = {}
    for sector, filers in panel.items():
        per_sector_counts[sector] = len(filers)
        for f in filers:
            entity = f"CIK{int(f['cik']):010d}"
            filer_sectors[entity] = sector
    return filer_sectors, per_sector_counts


def load_sec_records(fields_needed, filer_sectors, pins):
    """Stream the frozen pit store once, keeping only panel filers' records of
    the needed fields (the bridge re-applies its own field filter)."""
    wanted = set(fields_needed)
    by_field: dict[str, list[NormalizedRecord]] = {f: [] for f in wanted}
    n_lines = 0
    n_kept = 0
    with open(SEC_DIR / "pit_records.jsonl", encoding="utf-8") as fh:
        for line in fh:
            n_lines += 1
            if not any(f'"{f}"' in line for f in wanted):
                continue
            row = json.loads(line)
            if row.get("field") not in wanted:
                continue
            if row.get("entity_id") not in filer_sectors:
                continue
            eff = row.get("effective_time_utc")
            rec = NormalizedRecord(
                source_id=row["source_id"],
                dataset_id=row["dataset_id"],
                entity_id=row["entity_id"],
                field=row["field"],
                value=row["value"],
                unit=row.get("unit", ""),
                event_time_utc=dt.datetime.fromisoformat(row["event_time_utc"]),
                available_time_utc=dt.datetime.fromisoformat(row["available_time_utc"]),
                effective_time_utc=(
                    dt.datetime.fromisoformat(eff) if eff else None
                ),
                vintage_time_utc=dt.datetime.fromisoformat(row["vintage_time_utc"]),
                retrieved_time_utc=dt.datetime.fromisoformat(row["retrieved_time_utc"]),
                raw_path=row.get("raw_path", ""),
                raw_sha256=row.get("raw_sha256", ""),
                license_id=row.get("license_id", ""),
                entitlement_id=row.get("entitlement_id", ""),
                normalizer_version=row.get("normalizer_version", ""),
            )
            by_field[row["field"]].append(rec)
            n_kept += 1
    print(f"[sec] lines={n_lines} kept={n_kept}")
    return by_field


class SecPanels:
    """Cached bridge aggregates per (field, gap) over the requested dates."""

    def __init__(self, by_field, filer_sectors):
        self.by_field = by_field
        self.filer_sectors = filer_sectors
        self.cache: dict[tuple[str, int], dict[str, dict[str, SectorObservation]]] = {}

    def ensure(self, field: str, gap: int, dates: list[str]):
        key = (field, gap)
        obs = self.cache.get(key)
        if obs is None:
            obs = {}
            self.cache[key] = obs
        records = self.by_field[field]
        for d in sorted(set(dates) - set(obs)):
            ddate = dt.date.fromisoformat(d)
            obs[d] = aggregate_sector_asof(
                records,
                filer_sectors=self.filer_sectors,
                decision_session=ddate,
                field=field,
                max_filing_gap_days=gap,
            )
        return obs

    def value(self, field, gap, d, sector):
        obs = self.cache[(field, gap)].get(d, {})
        return obs.get(sector)


# --------------------------------------------------------------------------- #
# clocks
# --------------------------------------------------------------------------- #
def build_clocks(master):
    idx = {d: i for i, d in enumerate(master)}
    clock63 = []  # (fold_id, date) -- fold-reseeded, offsets 0,63..567
    fold_sessions = {}
    for fold_id, a, b in FOLDS:
        sess = [d for d in master if a <= d <= b]
        fold_sessions[fold_id] = sess
        assert len(sess) >= 568, (fold_id, len(sess))
        for off in range(0, 568, 63):
            clock63.append((fold_id, sess[off]))
    s0 = [d for d in master if S0_START <= d <= S0_END]
    clock42 = [s0[i] for i in range(0, len(s0), 42)]
    assert len(s0) == 1842, len(s0)
    return idx, clock63, clock42, fold_sessions, s0


# --------------------------------------------------------------------------- #
# proposal anchor features
# --------------------------------------------------------------------------- #
class Anchors:
    """Anchor feature values for each proposal, per its declared rule and
    eligibility gates, evaluated at arbitrary decision dates."""

    def __init__(self, master, idx, ret, close_all, sec: SecPanels, presence):
        self.master = master
        self.idx = idx
        self.ret = ret
        self.close_all = close_all
        self.sec = sec
        self.presence = presence

    def hist_count(self, s, d):
        i = self.idx[d]
        hist = self.presence[s]
        # count symbol sessions <= d (bounded by master end already)
        return sum(1 for x in hist if x <= d)

    def eligible(self, prop, d):
        if prop == "a4_h1":
            need, sectors = 63, SECTORS
        elif prop == "a4_h2":
            need, sectors = 63, tuple(s for s in SECTORS if s != "XLF")
        elif prop == "a5_h1":
            need, sectors = 21, SECTORS
        elif prop == "a5_h2":
            need, sectors = 63, SECTORS
        elif prop == "a6_h1":
            need, sectors = 252, A6_CENSUS_9
        elif prop == "a6_h2":
            need, sectors = 252, SECTORS
        else:
            raise KeyError(prop)
        return tuple(s for s in sectors if self.hist_count(s, d) >= need)

    # -- SEC-based keys -----------------------------------------------------
    def _sec_pair(self, field, gap, d, sector, floor):
        o = self.sec.value(field, gap, d, sector)
        if o is None or o.coverage < floor:
            return None
        return o

    def a4_h1(self, d):
        """g_i(t) = ln(M_i(t)/M_i(t-252s)); coverage >= .60 both endpoints;
        endpoint effective dates within 100 calendar days (a4_h1.json:28-29)."""
        i = self.idx[d]
        d_ref = self.master[i - 252]
        out = {}
        for s in self.eligible("a4_h1", d):
            o1 = self._sec_pair(FIELD_ASSETS, 400, d, s, 0.60)
            o0 = self._sec_pair(FIELD_ASSETS, 400, d_ref, s, 0.60)
            if o1 is None or o0 is None:
                continue
            gapdays = abs((o1.effective_date - o0.effective_date).days)
            if gapdays > 100:
                continue
            if o0.value <= 0.0 or o1.value <= 0.0:
                continue
            out[s] = math.log(o1.value / o0.value)
        return out

    def a4_h2(self, d):
        """CI_i(t) = M_cash/M_assets; XLF excluded ex ante; coverage >= .60
        both fields; 100-day effective-date coherence (a4_h2.json:29-30)."""
        out = {}
        for s in self.eligible("a4_h2", d):
            oc = self._sec_pair(FIELD_CASH, 400, d, s, 0.60)
            oa = self._sec_pair(FIELD_ASSETS, 400, d, s, 0.60)
            if oc is None or oa is None:
                continue
            if abs((oc.effective_date - oa.effective_date).days) > 100:
                continue
            if oc.value <= 0.0 or oa.value <= 0.0:
                continue
            out[s] = oc.value / oa.value
        return out

    def a5_h1(self, d):
        """R_s = mean_float / mean_lse; gap 550; coverage >= .60 both fields
        (a5_h1.json:42)."""
        out = {}
        for s in self.eligible("a5_h1", d):
            of = self._sec_pair(FIELD_FLOAT, 550, d, s, 0.60)
            ol = self._sec_pair(FIELD_LSE, 550, d, s, 0.60)
            if of is None or ol is None:
                continue
            if of.value <= 0.0 or ol.value <= 0.0:
                continue
            out[s] = of.value / ol.value
        return out

    def a6_h1(self, d):
        """WCINT = mean(AssetsCurrent)/mean(Assets); gap 200; coverage >= .40
        per leg; census 9-sector set; >= 252 sessions history
        (a6_h1.json:56)."""
        out = {}
        for s in self.eligible("a6_h1", d):
            oc = self._sec_pair(FIELD_CURR, 200, d, s, 0.40)
            oa = self._sec_pair(FIELD_ASSETS, 200, d, s, 0.40)
            if oc is None or oa is None:
                continue
            if oc.value <= 0.0 or oa.value <= 0.0:
                continue
            out[s] = oc.value / oa.value
        return out

    # -- A7-N measurement fallbacks (DIAGNOSTIC ONLY, clearly labelled) -----
    # The declared constructions above are gated by the bridge's own
    # SectorObservation.coverage, which collapses to <= 0.125 in sectors
    # whose panel contains a laggard fiscal-calendar filer (single-vintage
    # semantics: the sector vintage locks to the MAX effective date and
    # includes only filers reporting at that exact date).  Where the declared
    # series has fewer than MIN_COMMON_SECTORS rankable sectors at a tick, a
    # labelled diagnostic series is measured so lineage evidence exists; a
    # diagnostic can never make a proposal MORE eligible -- verdicts rest on
    # the declared construction first.

    def a4_h1_fb(self, d):
        """A4H1_FB_NO_GATE_C: declared a4_h1 minus gate (c).  Gate (c) (the
        two endpoint effective dates within 100 calendar days) is
        unsatisfiable for a 252-session-differenced key on annually
        re-vintaged aggregates: the endpoints are structurally ~365 days
        apart at every tick.  Gates (a)+(b) and all other elements kept."""
        i = self.idx[d]
        d_ref = self.master[i - 252]
        out = {}
        for s in self.eligible("a4_h1", d):
            o1 = self._sec_pair(FIELD_ASSETS, 400, d, s, 0.60)
            o0 = self._sec_pair(FIELD_ASSETS, 400, d_ref, s, 0.60)
            if o1 is None or o0 is None:
                continue
            if o0.value <= 0.0 or o1.value <= 0.0:
                continue
            out[s] = math.log(o1.value / o0.value)
        return out

    def a4_h2_diag(self, d):
        """A4H2_DIAG_NO_COV: declared a4_h2 with the coverage floor dropped
        (both fields' observations required; XLF exclusion, 100-day
        cross-field coherence and history rule kept)."""
        out = {}
        for s in self.eligible("a4_h2", d):
            oc = self.sec.value(FIELD_CASH, 400, d, s)
            oa = self.sec.value(FIELD_ASSETS, 400, d, s)
            if oc is None or oa is None:
                continue
            if abs((oc.effective_date - oa.effective_date).days) > 100:
                continue
            if oc.value <= 0.0 or oa.value <= 0.0:
                continue
            out[s] = oc.value / oa.value
        return out

    def a5_h1_diag(self, d):
        """A5H1_DIAG_NO_COV: declared a5_h1 with the coverage floor dropped
        (both fields' observations required)."""
        out = {}
        for s in self.eligible("a5_h1", d):
            of = self.sec.value(FIELD_FLOAT, 550, d, s)
            ol = self.sec.value(FIELD_LSE, 550, d, s)
            if of is None or ol is None:
                continue
            if of.value <= 0.0 or ol.value <= 0.0:
                continue
            out[s] = of.value / ol.value
        return out

    def a6_h1_diag(self, d):
        """A6H1_DIAG_NO_COV: declared a6_h1 with the coverage floor dropped
        (census 9-sector set, gap 200, both fields' observations)."""
        out = {}
        for s in self.eligible("a6_h1", d):
            oc = self.sec.value(FIELD_CURR, 200, d, s)
            oa = self.sec.value(FIELD_ASSETS, 200, d, s)
            if oc is None or oa is None:
                continue
            if oc.value <= 0.0 or oa.value <= 0.0:
                continue
            out[s] = oc.value / oa.value
        return out

    # -- price-based keys ----------------------------------------------------
    def a5_h2(self, d):
        """sigma_s = sqrt(mean(r^2, 63 trailing returns)) realized-vol LEVEL
        (a5_h2.json:34)."""
        i = self.idx[d]
        out = {}
        for s in self.eligible("a5_h2", d):
            if not window_ok(self.ret[s], i, 63):
                continue
            seg = [float(v) for v in self.ret[s][i - 62: i + 1]]
            out[s] = math.sqrt(math.fsum(r * r for r in seg) / 63.0)
        return out

    def a6_h2(self, d):
        """c_i = mean pairwise Pearson correlation of 63-session return
        windows vs eligible peers; < 5 defined pairs -> not eligible
        (a6_h2.json:47)."""
        i = self.idx[d]
        elig = list(self.eligible("a6_h2", d))
        windows = {}
        for s in elig:
            if not window_ok(self.ret[s], i, 63):
                continue
            windows[s] = [float(v) for v in self.ret[s][i - 62: i + 1]]
        out = {}
        for s, ws in windows.items():
            cors = []
            for t, wt in windows.items():
                if t == s:
                    continue
                c = pearson(ws, wt)
                if c is not None:
                    cors.append(c)
            if len(cors) >= 5:
                out[s] = math.fsum(cors) / len(cors)
        return out

    def feature(self, prop, d):
        return getattr(self, prop)(d)

    def stale_ranks_a5h2(self, d):
        """A5-H2's own falsification control: sigma ranks as of t-63 sessions
        (a5_h2.json:37)."""
        i = self.idx[d]
        assert i >= 63
        d_old = self.master[i - 63]
        return self.a5_h2(d_old)


# --------------------------------------------------------------------------- #
# reference feature evaluation over a common sector set
# --------------------------------------------------------------------------- #
REFERENCES = (
    "V4_SEMIVAR_SHAPE_126",
    "V4_VOLLEVEL_126",
    "V4_PART_FRESH_SHOCK_21_252",
    "V4_PART_STALE_SHOCK_21_252",
    "FORBIDDEN_MOM_12_1",
    "FORBIDDEN_SMA200_TREND",
    "FORBIDDEN_DVSHOCK_21_252",
    "VOLLEVEL_63",
)


def eval_reference(name, ctx, d, sectors):
    ret, close_all, dv, idx = ctx
    i = idx[d]
    out = {}
    if name == "V4_PART_FRESH_SHOCK_21_252" or name == "FORBIDDEN_DVSHOCK_21_252":
        w = SHOCK_WINDOWS["A"]
        for s in sectors:
            v = ref_shock(dv, s, i, w)
            if v is not None:
                out[s] = v
        return out
    if name == "V4_PART_STALE_SHOCK_21_252":
        w = SHOCK_WINDOWS["C"]
        for s in sectors:
            v = ref_shock(dv, s, i, w)
            if v is not None:
                out[s] = v
        return out
    for s in sectors:
        if name == "V4_SEMIVAR_SHAPE_126":
            v = ref_semivar_shape_126(ret, s, i)
        elif name == "V4_VOLLEVEL_126":
            v = ref_vollevel_126(ret, s, i)
        elif name == "VOLLEVEL_63":
            v = ref_vollevel_63(ret, s, i)
        elif name == "FORBIDDEN_MOM_12_1":
            v = ref_mom_12_1(close_all, s, i)
        elif name == "FORBIDDEN_SMA200_TREND":
            v = ref_sma200_dist(close_all, s, i)
        else:
            raise KeyError(name)
        if v is not None:
            out[s] = v
    return out


# --------------------------------------------------------------------------- #
# measurement driver
# --------------------------------------------------------------------------- #
PROPOSALS = ("a4_h1", "a4_h2", "a5_h1", "a5_h2", "a6_h1", "a6_h2")


def cmd_measure(out_path: Path):
    master, close_all, dv, presence, pins = load_snapshot()
    ret = build_returns(master, close_all)
    idx, clock63, clock42, fold_sessions, s0 = build_clocks(master)
    ctx = (ret, close_all, dv, idx)

    print("[sec] loading panel filers ...")
    filer_sectors, per_sector_counts = load_panel_filers()
    fields_needed = sorted({f for decl in SEC_DECL.values() for f, _, _ in decl})
    print("[sec] streaming pit store for fields:", fields_needed)
    by_field = load_sec_records(fields_needed, filer_sectors, pins)
    sec = SecPanels(by_field, filer_sectors)
    anchors = Anchors(master, idx, ret, close_all, sec, presence)

    clocks = {
        "a4_h1": [d for _, d in clock63],
        "a4_h2": [d for _, d in clock63],
        "a5_h1": [d for _, d in clock63],
        "a5_h2": [d for _, d in clock63],
        "a6_h1": list(clock42),
        "a6_h2": list(clock42),
    }

    # all dates the SEC panels must cover: every tick (union) plus the
    # t-252s reference session of every tick (a4_h1 key endpoints)
    all_ticks = sorted({d for ds in clocks.values() for d in ds})
    sec_dates = list(all_ticks) + [
        master[idx[d] - 252] for d in all_ticks
    ]
    for field, gap in sorted({(f, g) for decl in SEC_DECL.values() for f, g, _ in decl}):
        print(f"[sec] bridge aggregates field={field} gap={gap}")
        sec.ensure(field, gap, sec_dates)

    # sanity: presence completeness post-inception (return windows contiguous)
    presence_notes = {}
    for s in ["SPY"] + list(SECTORS):
        first = min(presence[s])
        sess = [d for d in master if d >= first]
        missing = [d for d in sess if d not in presence[s]]
        presence_notes[s] = {
            "first_session": first,
            "sessions_through_S0": len(sess),
            "missing_after_first": len(missing),
        }

    result = {
        "schema": "stocks_free_v5_run/a7_n_measurements@1",
        "producer_role": "A7-N",
        "method": (
            "Spearman rank correlation (average ranks, Pearson on ranks) of "
            "anchor feature vectors per proposal decision tick over the "
            "common sector set (proposal-eligible intersect reference-ready, "
            "minimum 6 sectors); V4 references reconstructed with the V4 "
            "terminal modules; SEC keys via the canonical bridge "
            "pit_conditioning.aggregate_sector_asof with each proposal's "
            "declared max_filing_gap_days and coverage floors; zero PnL."
        ),
        "data_pins": {
            "pit_store_sha256": sha256_file(SEC_DIR / "pit_records.jsonl"),
            "panel_sha256": sha256_file(SEC_DIR / "panel.json"),
            "snapshot_files": pins,
            "snapshot_path": str(SNAPSHOT),
            "sec_store_path": str(SEC_DIR / "pit_records.jsonl"),
        },
        "calendar": {
            "master_sessions_s0_bounded": len(master),
            "s0_sessions": len(s0),
            "fold_sessions": {k: len(v) for k, v in fold_sessions.items()},
            "presence_notes": presence_notes,
        },
        "clocks": {
            "clock63_fold_reseeded": [d for _, d in clock63],
            "clock63_fold_ids": [f for f, _ in clock63],
            "clock42_global": list(clock42),
        },
        "sec_field_record_counts": {k: len(v) for k, v in by_field.items()},
        "eligible_counts": {},
        "rho_vs_references": {},
        "cross_proposal": {},
        "a5h2_own_control_checks": {},
        "a4h1_endpoint_gates": {},
    }

    # eligible counts per proposal per tick
    for prop in PROPOSALS:
        counts = []
        for d in clocks[prop]:
            counts.append(
                {"date": d, "n_eligible": len(anchors.eligible(prop, d))}
            )
        result["eligible_counts"][prop] = counts

    # ---- primary measurement series per proposal --------------------------
    # Declared constructions first; where the declared series is degenerate
    # on the frozen store (canonical-bridge coverage collapse / unsatisfiable
    # gate), the labelled fallback/diagnostic series above is used and the
    # degeneracy is recorded per tick.  series_label records which was used.
    declared_methods = {
        "a4_h1": anchors.a4_h1,
        "a4_h2": anchors.a4_h2,
        "a5_h1": anchors.a5_h1,
        "a5_h2": anchors.a5_h2,
        "a6_h1": anchors.a6_h1,
        "a6_h2": anchors.a6_h2,
    }
    primary_methods = {
        "a4_h1": anchors.a4_h1_fb,
        "a4_h2": anchors.a4_h2_diag,
        "a5_h1": anchors.a5_h1_diag,
        "a5_h2": anchors.a5_h2,
        "a6_h1": anchors.a6_h1_diag,
        "a6_h2": anchors.a6_h2,
    }
    series_labels = {}
    declared_construct = {}
    for prop in PROPOSALS:
        rows = []
        n_constructible = 0
        for d in clocks[prop]:
            n_decl = len(declared_methods[prop](d))
            ok = n_decl >= MIN_COMMON_SECTORS
            n_constructible += int(ok)
            rows.append({"date": d, "n_sectors_declared": n_decl,
                         "constructible_ge6": ok})
        declared_construct[prop] = {
            "ticks_total": len(rows),
            "ticks_constructible_ge6": n_constructible,
            "per_tick": rows,
        }
        series_labels[prop] = (
            "DECLARED" if n_constructible == len(rows)
            else f"DIAGNOSTIC_FALLBACK (declared series constructible at "
                 f"{n_constructible}/{len(rows)} ticks only)"
        )
    result["series_labels"] = series_labels
    result["declared_series_constructibility"] = declared_construct

    def feature_primary(prop, d):
        return primary_methods[prop](d)

    # ---- reference correlations at each proposal's native ticks ----------
    for prop in PROPOSALS:
        result["rho_vs_references"][prop] = {}
        for ref in REFERENCES:
            per_tick = []
            for d in clocks[prop]:
                fs = feature_primary(prop, d)
                fr = eval_reference(ref, ctx, d, anchors.eligible(prop, d))
                common = sorted(set(fs) & set(fr))
                if len(common) < MIN_COMMON_SECTORS:
                    per_tick.append(
                        {"date": d, "n_sectors": len(common), "rho": None}
                    )
                    continue
                rho = spearman([fs[s] for s in common], [fr[s] for s in common])
                per_tick.append(
                    {"date": d, "n_sectors": len(common), "rho": rho}
                )
            valid = [abs(p["rho"]) for p in per_tick if p["rho"] is not None]
            secs = [p["n_sectors"] for p in per_tick if p["rho"] is not None]
            result["rho_vs_references"][prop][ref] = {
                "mean_abs_rho": (math.fsum(valid) / len(valid)) if valid else None,
                "max_abs_rho": max(valid) if valid else None,
                "ticks_valid": len(valid),
                "ticks_total": len(per_tick),
                "mean_sectors": (math.fsum(secs) / len(secs)) if secs else None,
                "per_tick": per_tick,
            }
        print(f"[rho] {prop} done")

    # ---- cross-proposal matrix (row proposal's ticks) ---------------------
    for pa in PROPOSALS:
        result["cross_proposal"][pa] = {}
        for pb in PROPOSALS:
            if pa == pb:
                continue
            per_tick = []
            for d in clocks[pa]:
                fa = feature_primary(pa, d)
                fb = feature_primary(pb, d)
                common = sorted(set(fa) & set(fb))
                if len(common) < MIN_COMMON_SECTORS:
                    per_tick.append({"date": d, "n_sectors": len(common), "rho": None})
                    continue
                rho = spearman([fa[s] for s in common], [fb[s] for s in common])
                per_tick.append({"date": d, "n_sectors": len(common), "rho": rho})
            valid = [abs(p["rho"]) for p in per_tick if p["rho"] is not None]
            secs = [p["n_sectors"] for p in per_tick if p["rho"] is not None]
            result["cross_proposal"][pa][pb] = {
                "mean_abs_rho": (math.fsum(valid) / len(valid)) if valid else None,
                "max_abs_rho": max(valid) if valid else None,
                "ticks_valid": len(valid),
                "ticks_total": len(per_tick),
                "mean_sectors": (math.fsum(secs) / len(secs)) if secs else None,
                "per_tick": per_tick,
            }
        print(f"[cross] {pa} done")

    # ---- A5-H2 own falsification control (fresh vs one-quarter-stale) ----
    checks = []
    for d in clocks["a5_h2"]:
        fresh = anchors.a5_h2(d)
        stale = anchors.stale_ranks_a5h2(d)
        common = sorted(set(fresh) & set(stale))
        entry = {"date": d, "n_sectors": len(common)}
        if len(common) >= MIN_COMMON_SECTORS:
            entry["rank_rho_fresh_vs_stale"] = spearman(
                [fresh[s] for s in common], [stale[s] for s in common]
            )
        if common:
            longs_f = sorted(sorted(common, key=lambda s: fresh[s])[:3])
            shorts_f = sorted(sorted(common, key=lambda s: -fresh[s])[:3])
            longs_s = sorted(sorted(common, key=lambda s: stale[s])[:3])
            shorts_s = sorted(sorted(common, key=lambda s: -stale[s])[:3])
            legs_f = set(longs_f) | set(shorts_f)
            legs_s = set(longs_s) | set(shorts_s)
            entry["legs_differ"] = legs_f != legs_s
            entry["n_leg_overlap"] = len(legs_f & legs_s)
        checks.append(entry)
    valid_rho = [c["rank_rho_fresh_vs_stale"] for c in checks
                 if c.get("rank_rho_fresh_vs_stale") is not None]
    differ = [c for c in checks if c.get("legs_differ") is not None]
    result["a5h2_own_control_checks"] = {
        "rule": "control = sigma ranks as of t-63 sessions, same overlay/book",
        "preregistered_gates": {
            "rank_rho_le": 0.90,
            "membership_differ_share_ge": 0.25,
            "source": "proposals/a5_h2.json:40 (identifiability_preregistration_L7)",
        },
        "mean_rank_rho": math.fsum(valid_rho) / len(valid_rho) if valid_rho else None,
        "max_abs_rank_rho": max(abs(r) for r in valid_rho) if valid_rho else None,
        "slots_with_rho": len(valid_rho),
        "membership_differ_share": (
            math.fsum(1.0 for c in differ if c["legs_differ"]) / len(differ)
            if differ else None
        ),
        "slots_total": len(checks),
        "per_slot": checks,
    }

    # ---- A4-H1 endpoint gate diagnostics ---------------------------------
    endpoint = []
    for d in clocks["a4_h1"]:
        i = idx[d]
        d_ref = master[i - 252]
        row = {"date": d, "ref_date": d_ref, "sectors": {}}
        for s in anchors.eligible("a4_h1", d):
            o1 = sec.value(FIELD_ASSETS, 400, d, s)
            o0 = sec.value(FIELD_ASSETS, 400, d_ref, s)
            row["sectors"][s] = {
                "cov_t": (o1.coverage if o1 else None),
                "cov_ref": (o0.coverage if o0 else None),
                "eff_gap_days": (
                    abs((o1.effective_date - o0.effective_date).days)
                    if o1 and o0 else None
                ),
                "eligible": s in anchors.a4_h1(d),
            }
        endpoint.append(row)
    result["a4h1_endpoint_gates"] = endpoint

    out_path.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(f"[done] measurements -> {out_path}")


def cmd_compose(measure_path: Path, out_path: Path):
    m = json.loads(measure_path.read_text())
    raise SystemExit("compose is written after measurement review")


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    if len(sys.argv) >= 2 and sys.argv[1] == "measure":
        cmd_measure(here / "a7_n_measurements.json")
    elif len(sys.argv) >= 2 and sys.argv[1] == "compose":
        cmd_compose(
            here / "a7_n_measurements.json",
            here / "a7_n_novelty_audit.json",
        )
    else:
        raise SystemExit("usage: a7_n_novelty_measure.py measure|compose")
