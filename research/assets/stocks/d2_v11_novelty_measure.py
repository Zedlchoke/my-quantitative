"""PLAN_stocks_v11 D2 novelty + control-identifiability + A9-F feasibility (executed by A1).

Feature/RANK ARITHMETIC ONLY — zero PnL (V5/V9/V10 D2 audit discipline).

For each of the SIX V11 D1 proposals (SFV11-A4-H1/H2, SFV11-A5-H1/H2,
SFV11-A6-H1/H2) the ANCHOR exposure is computed exactly as its
exposure_definition + arms state (with documented house conventions applied
where the definition needs one — every convention is recorded in the output
JSON under conventions_applied). Pooled Spearman (midrank ties) of the anchor
exposure vs each of the ELEVEN veto entries (the nine inherited V10 entries in
unchanged form + two NEW V10-ancestor entries: own_z_characteristic_form and
revision_direction_breadth_form); plus anchor-vs-control and anchor-vs-neighbour
rank correlations for the pre-selection identifiability gates, each judged
against the gate DECLARED IN THE PROPOSAL FILE.

Verdict per proposal: INELIGIBLE_NOVELTY if max|rho| > 0.20 vs any of the
eleven; INELIGIBLE_CONTROL_UNIDENTIFIABLE if |anchor-control rho| >= its
declared gate; else ELIGIBLE (novelty/identifiability dimension — feasibility
is separate). FEASIBILITY SECTION (same module, no PnL): expected scored
decisions overall + per fold from the P0 census arithmetic (warmup-aware),
margins vs the >=30 overall / >=5 per fold floors, sham/control runnability
counts, turnover-ceiling arithmetic shown explicitly, verdict RUNNABLE /
INFEASIBLE_<REASON>; declared-and-designed-around infeasibility_declarations
are respected as honest, not infeasible.

Determinism: the ONLY wall-clock input is built_at_utc, passed by the runner
as argv[1] or env D2_BUILT_AT so two runs are byte-identical (sort_keys=True;
every cross-entity sequence is iterated in sorted order — no set/hash-order
iteration). Universe: entity-decision pairs where the proposal exposure is
defined — grid families (A5-H1/H2, A6-H1) additionally require >= 63 price
bars through the decision session (inherited tradability eligibility), while
the event-anchored A4 families use their own declared >= 20 STRICT_NEXT_BAR
conditioning. No band computation, no returns, no outcome files.

Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python ONLY.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from array import array
from bisect import bisect_left, bisect_right
from datetime import date, timedelta
from pathlib import Path

# --------------- machine-local path constants (inherited EXACTLY from
# d2_v10_novelty_measure.py; they exist on this host) -----------------------
V10 = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v10/integration")
V9 = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/integration")
PRICES = V9 / ".staging_prices_v9/eod"
BENCH = V9 / ".staging_prices_v9/benchmarks"
TIMING = V10 / ".staging_sec_v10/v10_timing_observables.jsonl"
REVISION = V10 / ".staging_sec_v10/v10_revision_observables.jsonl"
PANEL = V9 / ".staging_sec_v9/multivintage_panel.jsonl"
COHORT = V10 / "research/control/stocks_free_v9_run/cohort_v9.json"
CENSUS = V10 / "research/control/stocks_free_v6_run/p0a_coverage_census.json"  # inherited constant; V11 grid dates come from the frozen folds instead
# --------------- V11 machine-local paths -----------------------------------
V11 = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v11/integration")
OUT = V11 / "research/control/stocks_free_v11_run/audits/d2_v11_novelty_measure.json"
PROPOSALS_DIR = V11 / "research/control/stocks_free_v11_run/proposals"
HASHES_FILE = V11 / "research/control/stocks_free_v11_run/d1_proposal_hashes.json"
P3_FREEZE = V11 / "research/control/stocks_free_v11_run/p3_v11_invariants_freeze.json"
EVENT_ARTIFACT = V11 / ".staging_sec_v11/v11_event_window_census.jsonl"
P0_CENSUS = V11 / "research/control/stocks_free_v11_run/p0_v11_event_amendment_census.json"
V10_P0_MANIFEST = V10 / "research/control/stocks_free_v10_run/p0_v10_observable_manifest.json"

STALE_DAYS = 800
WAVE_SHA = "ea668797b661dfa2c9d2b2799e46fe0f13f71820"
CYCLE = "STOCKS-FREE-V11"
NOVELTY_BAR = 0.20
PCG_SEED = 20260907  # frozen by A5-H1/A5-H2 pre_selection_identifiability_check
SECTOR_ETFS = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]

VETO_NAMES = [
    "momentum_63s", "semivariance_share", "vol_level", "wc_stock_intensity",
    "goodwill_bloat", "f1_accrual_flow", "depletion_interaction",
    "cash_level", "sector_exposure_form",
    "own_z_characteristic_form",            # NEW veto 10 (V10 timing ancestor)
    "revision_direction_breadth_form",      # NEW veto 11 (V10 revision ancestor)
]
# rev_dir encoding, VERIFIED against the V10 P0 manifest dir_counts
# (up=63342, flat=1519910, down=84170 on the sha-pinned layer):
REV_DIR_ENCODING = {1: "up", 0: "flat", -1: "down"}

# fields pulled from the panel for the accounting veto entries (V10 form, unchanged)
NEEDED_FIELDS = [
    "us-gaap:AssetsCurrent", "us-gaap:LiabilitiesCurrent",
    "us-gaap:Goodwill", "us-gaap:Assets",
    "us-gaap:CashAndCashEquivalentsAtCarryingValue",
    "us-gaap:RetainedEarningsAccumulatedDeficit",
    "us-gaap:AccountsReceivableNetCurrent", "us-gaap:InventoryNet",
    "us-gaap:AccountsPayableCurrent",
]
# A6-H1 share-count priority fields (priority order per exposure_definition)
SHARE_FIELDS = [
    "us-gaap:CommonStockSharesOutstanding",
    "dei:EntityCommonStockSharesOutstanding",
    "us-gaap:CommonStockSharesIssued",
]

FOLDS_FALLBACK = [
    {"fold_id": "S0_FOLD_1", "start": "2018-04-04", "end": "2020-09-01"},
    {"fold_id": "S0_FOLD_2", "start": "2020-09-10", "end": "2023-02-09"},
    {"fold_id": "S0_FOLD_3", "start": "2023-02-17", "end": "2025-07-24"},
]

PROPOSAL_FILES = {
    "SFV11-A4-H1": "a4_event_H1.json",
    "SFV11-A4-H2": "a4_event_H2.json",
    "SFV11-A5-H1": "a5_process_H1.json",
    "SFV11-A5-H2": "a5_process_H2.json",
    "SFV11-A6-H1": "a6_open_H1.json",
    "SFV11-A6-H2": "a6_open_H2.json",
}
PROPOSAL_ORDER = list(PROPOSAL_FILES.keys())
# gates from each proposal's pre_selection_identifiability_check (the number is
# cross-checked against the gate text read from the proposal file at runtime)
GATES = {
    "SFV11-A4-H1": 0.95,
    "SFV11-A4-H2": 0.95,
    "SFV11-A5-H1": 0.30,
    "SFV11-A5-H2": 0.70,
    "SFV11-A6-H1": 0.10,
    "SFV11-A6-H2": 0.10,
}
# declared warmup decisions (proposal warmup_decisions; the A4 arms dict declares 0)
WARMUP = {"SFV11-A4-H1": 0, "SFV11-A4-H2": 0,
          "SFV11-A5-H1": 0, "SFV11-A5-H2": 0,
          "SFV11-A6-H1": 3, "SFV11-A6-H2": 1}
# declared turnover ceilings where the proposal freezes a number
TURNOVER_CEILING = {"SFV11-A4-H1": 25.0, "SFV11-A4-H2": 25.0,
                    "SFV11-A5-H1": 6.0, "SFV11-A5-H2": 6.0,
                    "SFV11-A6-H1": None, "SFV11-A6-H2": None}
ANNUAL_SESSIONS = 252


def dd(s: str) -> date:
    return date.fromisoformat(s)


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def midrank(xs):
    items = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(items):
        j = i
        while j + 1 < len(items) and xs[items[j + 1]] == xs[items[i]]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[items[k]] = r
        i = j + 1
    return ranks


def spearman(a, b):
    n = len(a)
    if n < 10:
        return None
    ra, rb = midrank(a), midrank(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra))
    vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    if va == 0 or vb == 0:
        return None
    return cov / (va * vb)


# ===========================================================================
# context loading (heavy path — executed by A1)
# ===========================================================================
def load_context():
    import numpy as np  # local import: only the heavy path needs PCG64

    class Ctx:
        pass

    C = Ctx()
    C.np = np
    C.rng = np.random.Generator(np.random.PCG64(PCG_SEED))

    cohort = json.loads(COHORT.read_text())
    bookable = {}
    for cls in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED"):
        for m in cohort["members"][cls]:
            bookable[m["cik"]] = {"sector": m.get("sector", ""), "ticker": m.get("ticker", "")}
    C.bookable = bookable

    # frozen folds (carried payload of the V11 invariants freeze)
    try:
        p3 = json.loads(P3_FREEZE.read_text())
        folds = p3["carried_payload"]["folds"]
    except Exception:
        folds = FOLDS_FALLBACK
    C.folds = folds

    # global trading calendar from SPY
    spy = json.loads((BENCH / "SPY.json").read_text())
    sessions = [dd(r["date"]) for r in sorted(spy, key=lambda r: r["date"])]
    C.sessions = sessions
    C.sess_idx = {d: i for i, d in enumerate(sessions)}

    # benchmark close series (SPY + 11 SPDR sectors), close indexed by date
    C.bench = {}
    for tkr in ["SPY"] + SECTOR_ETFS:
        p = BENCH / f"{tkr}.json"
        if not p.exists():
            continue
        arr = json.loads(p.read_text())
        C.bench[tkr] = {dd(r["date"]): r["close"] for r in arr if r.get("close") is not None}

    # per-entity price series
    print("[d2] loading price series...", flush=True)
    series = {}
    for p in sorted(PRICES.glob("CIK*.json")):
        cik = p.name.split("__")[0]
        if cik not in bookable:
            continue
        try:
            arr = json.loads(p.read_text())
        except Exception:
            continue
        arr = [r for r in arr if r.get("close") is not None]
        if len(arr) < 63:
            continue
        arr.sort(key=lambda r: r["date"])
        series[cik] = {
            "dates": [dd(r["date"]) for r in arr],
            "close": [r["close"] for r in arr],
            "adj": [r.get("adjusted_close") for r in arr],
            "vol": [r.get("volume", 0) for r in arr],
        }
    C.series = series

    # per-entity prefix arrays over ADJ log returns for the 63-bar veto family
    print("[d2] building prefix arrays...", flush=True)
    pre = {}
    for cik, s in series.items():
        adj = s["adj"]
        n = len(adj)
        lr = [0.0] * n
        ok = [False] * n
        for i in range(1, n):
            if adj[i - 1] is not None and adj[i] is not None and adj[i - 1] > 0 and adj[i] > 0:
                lr[i] = math.log(adj[i] / adj[i - 1])
                ok[i] = True
        s_lr = array("d", [0.0] * n)
        s_l2 = array("d", [0.0] * n)
        s_dn = array("d", [0.0] * n)
        for i in range(1, n):
            s_lr[i] = s_lr[i - 1] + (lr[i] if ok[i] else 0.0)
            s_l2[i] = s_l2[i - 1] + ((lr[i] ** 2) if ok[i] else 0.0)
            s_dn[i] = s_dn[i - 1] + ((lr[i] ** 2) if (ok[i] and lr[i] < 0) else 0.0)
        pre[cik] = (s_lr, s_l2, s_dn, ok)
    C.pre = pre

    # panel fields: nine veto accounting fields + three share-count fields
    print("[d2] streaming panel for veto + share fields...", flush=True)
    fields = {}
    shares = {}
    want = set(NEEDED_FIELDS)
    want_share = set(SHARE_FIELDS)
    with open(PANEL, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            f = r["f"]
            if r["e"] in bookable and isinstance(r["v"], (int, float)):
                if f in want:
                    fields.setdefault((r["e"], f), []).append((r["avail"], r["eff"], r["v"]))
                elif f in want_share:
                    shares.setdefault((r["e"], f), {}).setdefault(r["eff"], []).append(
                        (r["avail"], r["v"]))
    for k in fields:
        fields[k].sort()
    C.fields = fields
    # share groups: eff -> vintages sorted by avail; plus eff order per (e,f)
    share_groups = {}
    for (e, f), effs in shares.items():
        for eff, vint in effs.items():
            vint.sort()
        share_groups[(e, f)] = sorted(effs.keys())
    C.share_groups = share_groups
    C.share_vintages = shares

    # timing layer (all groups; veto 10 + A5-H2 + A4-H2 chain keys)
    print("[d2] loading timing layer...", flush=True)
    tim = {}
    with open(TIMING, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            e = r["e"]
            if e in bookable:
                tim.setdefault(e, []).append(
                    (r["first_avail"], r["eff"], r["f"], r["last_avail"],
                     r["depth"], r["amend_count"], r["own_z"],
                     r["observable_available_at"]))
    for e in tim:
        tim[e].sort(key=lambda x: (x[7], x[0], x[1], x[2]))  # by observable_available_at
    C.tim = tim
    # own_z rows per entity: (observable_available_at, own_z) for non-null own_z
    ownz = {}
    for e, rows in tim.items():
        lst = sorted((r[7], r[6]) for r in rows if r[6] is not None)
        if lst:
            ownz[e] = ([x[0] for x in lst], array("d", [x[1] for x in lst]))
    C.ownz = ownz
    # depth>=2 timing rows per entity sorted by last_avail (A5-H2 Q windows)
    tim_d2 = {}
    for e, rows in tim.items():
        lst = sorted((r[3], r[2], r[1], r[5]) for r in rows if r[4] >= 2)
        if lst:
            tim_d2[e] = (lst, [x[0] for x in lst])  # rows + sorted last_avail index
    C.tim_d2 = tim_d2

    # revision layer (depth>=2 groups; A5-H1 + veto 11)
    print("[d2] loading revision layer...", flush=True)
    rev = {}
    dir_counts = {1: 0, 0: 0, -1: 0}
    with open(REVISION, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            e = r["e"]
            if e in bookable:
                d = r["rev_dir"]
                dir_counts[d] = dir_counts.get(d, 0) + 1
                rev.setdefault(e, []).append(
                    (r["last_avail"], d, r["rev_mag"], r["inter_arrival_days"], r["depth"]))
    for e in rev:
        rev[e].sort()
    C.rev = rev
    # veto-11 prefix arrays per entity: avails + cumulative total/down counts
    bread = {}
    for e, rows in rev.items():
        avs = [r[0] for r in rows]
        ctot = array("i", [0] * len(rows))
        cdn = array("i", [0] * len(rows))
        t = dn = 0
        for i, r in enumerate(rows):
            t += 1
            dn += 1 if r[1] == -1 else 0
            ctot[i] = t
            cdn[i] = dn
        bread[e] = (avs, ctot, cdn)
    C.bread = bread
    # A5-H1 prefix arrays per entity: cumulative count / count(iarr>460) /
    # count(depth>=6) over last_avail-sorted rows
    late = {}
    for e, rows in rev.items():
        avs = [r[0] for r in rows]
        n = len(rows)
        ctot = array("i", [0] * n)
        clate = array("i", [0] * n)
        cdeep = array("i", [0] * n)
        a = b = c = 0
        for i, r in enumerate(rows):
            a += 1
            b += 1 if r[3] is not None and r[3] > 460 else 0
            c += 1 if r[4] >= 6 else 0
            ctot[i] = a
            clate[i] = b
            cdeep[i] = c
        late[e] = (avs, ctot, clate, cdeep)
    C.late = late

    # dir_counts cross-check against the V10 P0 manifest (fail-closed)
    manifest = json.loads(V10_P0_MANIFEST.read_text())
    md = manifest["census"]["revision"]["dir_counts"]
    expected = {1: md["up"], 0: md["flat"], -1: md["down"]}
    C.dir_check = {"measured": {REV_DIR_ENCODING[k]: v for k, v in sorted(dir_counts.items())},
                   "manifest": md, "verdict": "MATCH" if dir_counts == expected else "MISMATCH"}
    if dir_counts != expected:
        sys.stderr.write("BLOCKED: rev_dir encoding check FAILED — measured %r vs manifest %r\n"
                         % (dir_counts, expected))
        return C, 2

    # event artifact (V11-E1 derived, sha-pinned in the P0 census)
    print("[d2] loading event artifact...", flush=True)
    events = []
    with open(EVENT_ARTIFACT, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            events.append((r["cik"], r["first_avail"], r["class"], r["strict_bars"]))
    C.events = events
    C.event_dates = {}
    for cik, fa, _cls, _sb in events:
        C.event_dates.setdefault(cik, set()).add(fa)

    # decision grids
    C.grid21 = grid_dates(C, 63, 21)
    C.grid5 = grid_dates(C, 63, 5)
    return C, 0


def grid_dates(C, start_idx, step):
    """per-fold local session indices start_idx + step*k, strictly inside folds."""
    out = {}
    for f in C.folds:
        lo, hi = dd(f["start"]), dd(f["end"])
        local = [d for d in C.sessions if lo <= d <= hi]
        out[f["fold_id"]] = [local[i] for i in range(start_idx, len(local), step)
                             if i < len(local)]
    return out


def grid_dates_flat(C, grid):
    ds = []
    for fid in sorted(grid):
        ds.extend(grid[fid])
    return sorted(ds)


def has_bars(C, cik, t, n=63):
    s = C.series.get(cik)
    if s is None:
        return False
    return bisect_left(s["dates"], t) >= n


# ===========================================================================
# VETO ENGINE — eleven entries; entries 1-9 in the inherited V10 form,
# entries 10-11 the new V10-ancestor forms. Each builder: (C, e, t) -> value|None
# ===========================================================================
def last_strict_bar_idx(C, cik, t):
    s = C.series[cik]
    i = bisect_left(s["dates"], t)
    if i >= len(s["dates"]):
        i = len(s["dates"]) - 1
    if s["dates"][i] >= t:
        i -= 1
    return i


def veto_momentum(C, e, t):
    s = C.series.get(e)
    if s is None:
        return None
    i = last_strict_bar_idx(C, e, t)
    if i < 62:
        return None
    w0, w1 = s["adj"][i - 62], s["adj"][i]
    if w0 is None or w1 is None or w0 <= 0 or w1 <= 0:
        return None
    return w1 / w0 - 1.0


def veto_vol(C, e, t, kind):
    s = C.series.get(e)
    if s is None:
        return None
    i = last_strict_bar_idx(C, e, t)
    if i < 62:
        return None
    s_lr, s_l2, s_dn, ok = C.pre[e]
    lo, hi = i - 62, i  # in-window returns live on bars (i-62+1 .. i)
    nret = 0
    for k in range(lo + 1, hi + 1):
        if ok[k]:
            nret += 1
    if nret < 30:
        return None
    tot = s_l2[hi] - s_l2[lo]
    if kind == "semi":
        return (s_dn[hi] - s_dn[lo]) / tot if tot > 0 else None
    mu = (s_lr[hi] - s_lr[lo]) / nret
    var = tot / nret - mu * mu
    return math.sqrt(var) if var > 0 else 0.0


def _asof(C, e, f, t, prior_annual=None):
    lst = C.fields.get((e, f))
    if not lst:
        return None
    lo, hi = 0, len(lst)
    while lo < hi:
        mid = (lo + hi) // 2
        if lst[mid][0] < t.isoformat():
            lo = mid + 1
        else:
            hi = mid
    if lo == 0:
        return None
    if prior_annual is None:
        return lst[lo - 1][2]
    for k in range(lo - 1, -1, -1):
        av, eff, v = lst[k]
        if eff[5:7] == "12" and int(eff[:4]) < prior_annual[0]:
            return v
    return None


def _latest_annual_year(C, e, f, t):
    lst = C.fields.get((e, f))
    if not lst:
        return None
    best = None
    for av, eff, v in lst:
        if av < t.isoformat() and eff[5:7] == "12":
            y = int(eff[:4])
            if best is None or y > best:
                best = y
    return best


def veto_ratio(C, e, t, num_f, den_f="us-gaap:Assets", flow=False):
    den = _asof(C, e, den_f, t)
    if not den:
        return None
    if flow:
        y = _latest_annual_year(C, e, "us-gaap:AccountsReceivableNetCurrent", t)
        if y is None:
            return None
        num = 0.0
        for f, sign in (("us-gaap:AccountsReceivableNetCurrent", 1),
                        ("us-gaap:InventoryNet", 1),
                        ("us-gaap:AccountsPayableCurrent", -1)):
            cur = _asof(C, e, f, t)
            pri = _asof(C, e, f, t, prior_annual=(y, None))
            if cur is None or pri is None:
                return None
            num += sign * (cur - pri)
        return num / den
    if isinstance(num_f, tuple):
        num = _asof(C, e, num_f[0], t)
        if num is None:
            return None
        num2 = _asof(C, e, num_f[1], t)
        if num2 is None:
            return None
        return (num - num2) / den
    num = _asof(C, e, num_f, t)
    if num is None:
        return None
    return num / den


def veto_depletion(C, e, t):
    RE = "us-gaap:RetainedEarningsAccumulatedDeficit"
    assets = _asof(C, e, "us-gaap:Assets", t)
    if not assets:
        return None
    y = _latest_annual_year(C, e, RE, t)
    if y is None:
        return None
    re_now = _asof(C, e, RE, t)
    re_prior = _asof(C, e, RE, t, prior_annual=(y, None))
    cash = _asof(C, e, "us-gaap:CashAndCashEquivalentsAtCarryingValue", t)
    if re_now is None or re_prior is None or cash is None:
        return None
    return (re_prior - re_now - cash) / assets


_sector_cache = {}


def veto_sector_form(C, e, t):
    """Veto 9 — sector equal-weight mean of the 63s momentum cross-section at t."""
    sec = C.bookable.get(e, {}).get("sector", "")
    key = (sec, t.isoformat())
    if key in _sector_cache:
        return _sector_cache[key]
    vals = []
    for e2 in sorted(C.series):
        if C.bookable.get(e2, {}).get("sector", "") != sec:
            continue
        v = veto_momentum(C, e2, t)
        if v is not None:
            vals.append(v)
    out = (sum(vals) / len(vals)) if vals else None
    _sector_cache[key] = out
    return out


def veto_own_z(C, e, t):
    """Veto 10 — own_z_characteristic_form: per entity, the most recent
    in-window (<=800d stale) timing-layer group own_z; MEAN over the
    qualifying groups sharing that most recent observable_available_at stamp;
    missing if none. PIT stamp = observable_available_at."""
    rec = C.ownz.get(e)
    if rec is None:
        return None
    avs, zs = rec
    lo = bisect_left(avs, (t - timedelta(days=STALE_DAYS)).isoformat())
    hi = bisect_right(avs, t.isoformat())
    if hi <= lo:
        return None
    # groups at the most recent qualifying stamp (ties averaged)
    j = hi - 1
    stamp = avs[j]
    tot, n = 0.0, 0
    while j >= lo and avs[j] == stamp:
        tot += zs[j]
        n += 1
        j -= 1
    return tot / n


def veto_breadth(C, e, t):
    """Veto 11 — revision_direction_breadth_form: share of in-window depth>=2
    revision-layer groups whose last-vintage value moved DOWN vs first vintage
    (rev_dir == -1; encoding verified against the V10 P0 manifest dir_counts).
    Window: observable_available_at (= last_avail) <= t and > t-800d.
    breadth = down_share; missing if no groups."""
    rec = C.bread.get(e)
    if rec is None:
        return None
    avs, ctot, cdn = rec
    lo = bisect_right(avs, (t - timedelta(days=STALE_DAYS)).isoformat())
    hi = bisect_right(avs, t.isoformat())
    if hi == 0:
        return None
    tot = ctot[hi - 1] - (ctot[lo - 1] if lo > 0 else 0)
    if tot <= 0:
        return None
    dn = cdn[hi - 1] - (cdn[lo - 1] if lo > 0 else 0)
    return dn / tot


VETO_BUILDERS = {
    "momentum_63s": lambda C, e, t: veto_momentum(C, e, t),
    "semivariance_share": lambda C, e, t: veto_vol(C, e, t, "semi"),
    "vol_level": lambda C, e, t: veto_vol(C, e, t, "vol"),
    "wc_stock_intensity": lambda C, e, t: veto_ratio(
        C, e, t, ("us-gaap:AssetsCurrent", "us-gaap:LiabilitiesCurrent")),
    "goodwill_bloat": lambda C, e, t: veto_ratio(C, e, t, "us-gaap:Goodwill"),
    "f1_accrual_flow": lambda C, e, t: veto_ratio(
        C, e, t, ("us-gaap:AccountsReceivableNetCurrent",), flow=True),
    "depletion_interaction": lambda C, e, t: veto_depletion(C, e, t),
    "cash_level": lambda C, e, t: veto_ratio(
        C, e, t, "us-gaap:CashAndCashEquivalentsAtCarryingValue"),
    "sector_exposure_form": lambda C, e, t: veto_sector_form(C, e, t),
    "own_z_characteristic_form": lambda C, e, t: veto_own_z(C, e, t),
    "revision_direction_breadth_form": lambda C, e, t: veto_breadth(C, e, t),
}


# ===========================================================================
# PROPOSAL EXPOSURE BUILDERS (six)
# ===========================================================================
def chain_is_amendment(C, e, a_iso):
    """A4-H2 chain-position partition from timing-layer group keys, stamps
    <= the arrival only: arrival a is an AMENDMENT arrival (chain position >= 2
    in at least one same-filer-period group) iff any group of e has first_avail
    strictly < a; else (a being some group's first_avail) it is a FIRST-VINTAGE
    arrival (position 1). Exact per-group rank is bounded by [2, depth_g] from
    the group aggregates (first/last stamps + depth); max over groups is the
    against-eligibility reading (recorded convention)."""
    for row in C.tim.get(e, ()):
        if row[0] < a_iso:  # row[0] = first_avail
            return True
    return False


def fold_of(C, d):
    for f in C.folds:
        if dd(f["start"]) <= d <= dd(f["end"]):
            return f
    return None


def residual_reaction(C, e, arr, bench_tkr):
    """5-bar STRICT_NEXT_BAR benchmark-residual initial reaction.
    Returns (sign, entry_date, reason); sign None means abstain-with-reason.
    Base of bar 1 = the last close at-or-before the arrival; the benchmark must
    print closes on all six dates d0..d5 else the event abstains (recorded
    against-eligibility convention)."""
    s = C.series.get(e)
    if s is None:
        return None, None, "no_price_series"
    i0 = bisect_right(s["dates"], arr) - 1  # last bar <= arrival (base close)
    if i0 < 0:
        return None, None, "no_base_bar"
    if i0 + 20 >= len(s["dates"]):
        return None, None, "fewer_than_20_strict_bars"
    ben = C.bench.get(bench_tkr)
    if ben is None:
        return None, None, "bench_missing"
    bc = []
    for k in range(0, 6):  # d0..d5
        d = s["dates"][i0 + k]
        b = ben.get(d)
        if b is None or b <= 0:
            return None, None, "bench_bar_missing"
        bc.append(b)
    r_ent = 1.0
    for k in range(1, 6):
        p0, p1 = s["close"][i0 + k - 1], s["close"][i0 + k]
        if p0 is None or p1 is None or p0 <= 0 or p1 <= 0:
            return None, None, "entity_bar_missing"
        r_ent *= p1 / p0
    r_ben = 1.0
    for k in range(1, 6):
        r_ben *= bc[k] / bc[k - 1]
    r = (r_ent - 1.0) - (r_ben - 1.0)
    entry = s["dates"][i0 + 6]
    if r > 0:
        return 1, entry, None
    if r < 0:
        return -1, entry, None
    return None, entry, "reaction_zero"


def _clear_window_prefix(C, e, k=20):
    """Per-entity prefix over clear k-bar window starts: a window starting at
    bar j is clear iff it fits inside the entity's series with j >= 1 (a base
    close is needed for the pseudo-reaction) and contains no bar date equal to
    any filer-event date of the entity (P0 census section-d definition)."""
    s = C.series[e]
    ev = C.event_dates.get(e, set())
    n = len(s["dates"])
    ok = [0] * n
    run = 0  # consecutive non-event bars starting at j (scanned backward)
    for j in range(n - 1, -1, -1):
        if s["dates"][j].isoformat() in ev:
            run = 0
        else:
            run += 1
        ok[j] = 1 if (j >= 1 and run >= k) else 0
    pre = array("i", [0] * (n + 1))
    for j in range(n):
        pre[j + 1] = pre[j] + ok[j]
    return pre, ok


def _sham_pick(C, e, first_avail_iso, fold, pre, ok, k=20):
    """Deterministic hash-seeded uniform pick among clear k-bar windows lying
    entirely inside `fold`; seed = sha256('cik|first_avail'). Returns the start
    bar index j or None."""
    s = C.series[e]
    lo = bisect_left(s["dates"], dd(fold["start"]))
    hi = bisect_right(s["dates"], dd(fold["end"])) - 1
    jlo = max(lo, 1)
    jhi = hi - (k - 1)
    if jhi < jlo:
        return None
    cnt = pre[jhi + 1] - pre[jlo]
    if cnt <= 0:
        return None
    h = int(sha256_hex(f"{e}|{first_avail_iso}".encode())[:16], 16)
    target = pre[jlo] + (h % cnt)
    a, b = jlo, jhi
    while a < b:  # first j with pre[j+1] >= target
        mid = (a + b) // 2
        if pre[mid + 1] < target:
            a = mid + 1
        else:
            b = mid
    return a if ok[a] == 1 else None


def build_a4(C, h2):
    """SFV11-A4-H1 / SFV11-A4-H2 — filing-event reaction anchors.

    anchor exposure(e, t = bar-6 close date) = +1/-1 sign of the 5-bar
    sector-residual initial reaction (H1: all in-universe arrivals; H2:
    amendment arrivals, chain position >= 2, only). neighbour = identical
    arithmetic residualized against SPY (H1) / run on first-vintage arrivals
    (H2). control = hash-seeded clear 20-bar sham windows matched 1:1 to the
    anchor events; the identifiability rho is measured on the aligned (entity,
    calendar-date) cell grid with positions coded +1/-1 open and 0
    flat/absent (union grid, 0-filled)."""
    anchor, neighbour = {}, {}
    a_cells, c_cells = {}, {}
    ctr = {"events_total": 0, "excluded_class": 0, "excluded_strict_bars": 0,
           "excluded_out_of_fold": 0, "excluded_entry_after_fold_end": 0,
           "abstain_reaction_zero": 0, "abstain_bench_bar_missing": 0,
           "abstain_sector_unmapped": 0, "abstain_no_base_bar": 0,
           "abstain_other": 0, "anchor_pairs": 0, "neighbour_pairs": 0,
           "matched_events": 0, "sham_no_clear_window": 0,
           "sham_pseudo_signal_abstain": 0, "sham_cells": 0}
    clear_cache = {}

    for cik, fa, cls, sb in C.events:
        ctr["events_total"] += 1
        if cls not in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED"):
            ctr["excluded_class"] += 1
            continue
        if (sb is None) or sb < 20 or cik not in C.series:
            ctr["excluded_strict_bars"] += 1
            continue
        fold = fold_of(C, dd(fa))
        if fold is None:
            ctr["excluded_out_of_fold"] += 1
            continue
        is_amend = chain_is_amendment(C, cik, fa) if h2 else None
        is_anchor_event = (not h2) or is_amend
        sector = C.bookable[cik]["sector"]
        bench_tkr = sector if sector in C.bench else None
        sign, entry, why = residual_reaction(C, cik, dd(fa), bench_tkr or "__NONE__")
        if why == "reaction_zero":
            ctr["abstain_reaction_zero"] += 1
        elif why == "bench_bar_missing":
            ctr["abstain_bench_bar_missing"] += 1
        elif why == "no_base_bar":
            ctr["abstain_no_base_bar"] += 1
        elif bench_tkr is None:
            ctr["abstain_sector_unmapped"] += 1
        elif why is not None:
            ctr["abstain_other"] += 1
        if sign is not None:
            if entry > dd(fold["end"]):
                ctr["excluded_entry_after_fold_end"] += 1
            elif is_anchor_event:
                anchor[(cik, entry)] = float(sign)
            else:
                neighbour[(cik, entry)] = float(sign)
        if not is_anchor_event:
            continue  # H2 sham control is matched to ANCHOR (amendment) events only
        # anchor holding cells: bars 6..20 clipped at fold end (position state)
        if sign is not None:
            s = C.series[cik]
            i0 = bisect_right(s["dates"], dd(fa)) - 1
            end_d = dd(fold["end"])
            for k in range(6, 21):
                d = s["dates"][i0 + k]
                if d > end_d:
                    break
                a_cells[(cik, d)] = a_cells.get((cik, d), 0.0) + sign
        # neighbour residualization (H1: same events vs SPY)
        if not h2 and sign is not None:
            nsign, nentry, _nwhy = residual_reaction(C, cik, dd(fa), "SPY")
            if nsign is not None and nentry <= dd(fold["end"]):
                neighbour[(cik, nentry)] = float(nsign)
        # ---- control: hash-seeded clear 20-bar sham window in the same fold
        ctr["matched_events"] += 1
        rec = clear_cache.get(cik)
        if rec is None:
            rec = _clear_window_prefix(C, cik, 20)
            clear_cache[cik] = rec
        j = _sham_pick(C, cik, fa, fold, rec[0], rec[1], 20)
        if j is None:
            ctr["sham_no_clear_window"] += 1
            continue
        s = C.series[cik]
        ben = C.bench.get(bench_tkr) if bench_tkr else None
        bclose = []
        bad = ben is None
        if not bad:
            for kk in range(j - 1, j + 5):  # dates d0..d5 of the sham window
                b = ben.get(s["dates"][kk])
                if b is None or b <= 0:
                    bad = True
                    break
                bclose.append(b)
        if bad:
            ctr["sham_pseudo_signal_abstain"] += 1
            continue
        r_ent = 1.0
        ok_ent = True
        for kk in range(j - 1, j + 4):  # bars 1-5, base = bar j-1
            p0, p1 = s["close"][kk], s["close"][kk + 1]
            if p0 is None or p1 is None or p0 <= 0 or p1 <= 0:
                ok_ent = False
                break
            r_ent *= p1 / p0
        if not ok_ent:
            ctr["sham_pseudo_signal_abstain"] += 1
            continue
        r_ben = 1.0
        for kk in range(5):
            r_ben *= bclose[kk + 1] / bclose[kk]
        r = (r_ent - 1.0) - (r_ben - 1.0)
        if r == 0:
            ctr["sham_pseudo_signal_abstain"] += 1
            continue
        ssign = 1.0 if r > 0 else -1.0
        end_d = dd(fold["end"])
        for k in range(6, 21):  # sham positions: window bars 6..20
            d = s["dates"][j - 1 + k]
            if d > end_d:
                break
            c_cells[(cik, d)] = c_cells.get((cik, d), 0.0) + ssign
            ctr["sham_cells"] += 1

    # net position states (sign of summed open signs; exact nets code 0)
    a_cells = {k: (0.0 if v == 0 else (1.0 if v > 0 else -1.0)) for k, v in a_cells.items()}
    c_cells = {k: (0.0 if v == 0 else (1.0 if v > 0 else -1.0)) for k, v in c_cells.items()}
    ctr["anchor_pairs"] = len(anchor)
    ctr["neighbour_pairs"] = len(neighbour)
    return {"anchor": anchor, "neighbour": neighbour,
            "anchor_cells": a_cells, "control_cells": c_cells, "counters": ctr}


def build_a5_h1(C):
    """SFV11-A5-H1 — late-share latency exposure on the inherited 21-session
    grid. anchor late_share(e,t) = |{g in Q: inter_arrival_days > 460}| / |Q|,
    Q = revision-layer (depth>=2) groups with last_avail < t and
    0 <= t-last_avail <= 800, defined iff |Q| >= 4. neighbour deep_share =
    share with depth >= 6. control = within-sector marginal-preserving
    permutation of the anchor values (numpy PCG64 seed 20260907, applied to the
    CIK-sorted index vector, re-drawn per decision date in session-index
    order)."""
    anchor, neighbour, control = {}, {}, {}
    for t in grid_dates_flat(C, C.grid21):
        names = []
        for e in sorted(C.series):
            if not has_bars(C, e, t):
                continue
            rec = C.late.get(e)
            if rec is None:
                continue
            avs, ctot, clate, cdeep = rec
            lo = bisect_left(avs, (t - timedelta(days=STALE_DAYS)).isoformat())
            hi = bisect_left(avs, t.isoformat())
            if hi == 0:
                continue
            n = ctot[hi - 1] - (ctot[lo - 1] if lo > 0 else 0)
            if n < 4:
                continue
            late_n = clate[hi - 1] - (clate[lo - 1] if lo > 0 else 0)
            deep_n = cdeep[hi - 1] - (cdeep[lo - 1] if lo > 0 else 0)
            anchor[(e, t)] = late_n / n
            neighbour[(e, t)] = deep_n / n
            names.append(e)
        # control: within-sector permutation over the CIK-sorted index vector
        by_sec = {}
        for e in names:  # already CIK-sorted
            by_sec.setdefault(C.bookable[e]["sector"], []).append(e)
        for sec in sorted(by_sec):
            block = by_sec[sec]
            m = len(block)
            if m == 1:
                control[(block[0], t)] = anchor[(block[0], t)]
                continue
            perm = C.rng.permutation(m)
            for i, e in enumerate(block):
                control[(e, t)] = anchor[(block[int(perm[i])], t)]
    return {"anchor": anchor, "neighbour": neighbour, "control": control}


def build_a5_h2(C):
    """SFV11-A5-H2 — chain-shape concentration (HHI) exposure on the inherited
    21-session grid. anchor hhi(e,t) = sum_f (n_f/N)^2 over timing-layer
    depth>=2 groups with last_avail in [t-800, t), N >= 4. neighbour vol_med =
    median amend_count over Q. control = geometry-null: per entity keep N and
    the distinct field set F exactly and REDRAW each group's field label
    uniformly over F(e,t) (PCG64 seed 20260907, permutation applied to the
    group-key-sorted index vector, re-drawn per decision date in session-index
    order); HHI recomputed on the redrawn labels."""
    import statistics
    anchor, neighbour, control = {}, {}, {}
    for t in grid_dates_flat(C, C.grid21):
        t_iso = t.isoformat()
        lo_iso = (t - timedelta(days=STALE_DAYS)).isoformat()
        for e in sorted(C.series):
            if not has_bars(C, e, t):
                continue
            rec = C.tim_d2.get(e)
            if rec is None:
                continue
            rows, avs = rec
            lo = bisect_left(avs, lo_iso)
            hi = bisect_left(avs, t_iso)
            q = rows[lo:hi]
            n = len(q)
            if n < 4:
                continue
            cnt = {}
            amends = []
            for _la, f, _eff, amend in q:
                cnt[f] = cnt.get(f, 0) + 1
                amends.append(amend)
            anchor[(e, t)] = sum((c / n) ** 2 for c in cnt.values())
            neighbour[(e, t)] = float(statistics.median(amends))
            # geometry-null control: redraw labels uniformly over F(e,t)
            f_order = sorted(cnt)
            k = len(f_order)
            groups_sorted = sorted(q, key=lambda r: (r[1], r[2]))  # group-key-sorted
            perm = C.rng.permutation(len(groups_sorted))
            cnt2 = {}
            for i in range(len(groups_sorted)):
                f2 = f_order[int(perm[i]) % k]
                cnt2[f2] = cnt2.get(f2, 0) + 1
            control[(e, t)] = sum((c / n) ** 2 for c in cnt2.values())
    return {"anchor": anchor, "neighbour": neighbour, "control": control}


def build_a6_h1(C):
    """SFV11-A6-H1 — net share-issuance log-ratio exposure S_i(t) =
    ln(V_last/V_prev) on the entity's primary share-count field, |S| > ln 2
    excluded, both values strictly positive. neighbour = long-only buyback
    book — the SAME exposure vector (portfolio construction variant), so the
    anchor-vs-neighbour rho is 1.0 by construction. control = deterministic
    within-decision permutation placebo: exposure values rotated by one in the
    hex-sorted sha256('cycle|hid|cik|decision_index') hash order (no RNG
    library, byte-reproducible)."""
    anchor = {}
    for t in grid_dates_flat(C, C.grid21):
        t_iso = t.isoformat()
        for e in sorted(C.series):
            if not has_bars(C, e, t):
                continue
            best_f, best_n = None, -1
            for f in SHARE_FIELDS:  # priority order; strict > keeps the earliest on ties
                g = C.share_groups.get((e, f))
                if g and len(g) > best_n:
                    best_f, best_n = f, len(g)
            if best_f is None:
                continue
            effs = C.share_groups[(e, best_f)]
            vints = C.share_vintages[(e, best_f)]
            cand = []
            for eff in effs:
                fa = vints[eff][0][0]  # group first_avail = earliest vintage stamp
                if fa < t_iso and 0 <= (t - dd(fa)).days <= STALE_DAYS:
                    cand.append(eff)
            if len(cand) < 2:
                continue

            def grp_val(eff):
                v = None
                for av, val in vints[eff]:
                    if av < t_iso:
                        v = val
                    else:
                        break
                return v

            vl, vp = grp_val(cand[-1]), grp_val(cand[-2])
            if vl is None or vp is None or vl <= 0 or vp <= 0:
                continue
            sval = math.log(vl / vp)
            if abs(sval) > math.log(2.0):
                continue
            anchor[(e, t)] = sval
    # control: rotate-by-one in hash order per decision index
    control = {}
    by_date = {}
    for (e, t), v in anchor.items():
        by_date.setdefault(t, []).append(e)
    for di, t in enumerate(grid_dates_flat(C, C.grid21)):
        names = sorted(by_date.get(t, []),
                       key=lambda e: sha256_hex(f"{CYCLE}|SFV11-A6-H1|{e}|{di}".encode()))
        m = len(names)
        if m < 2:
            continue
        for i, e in enumerate(names):
            control[(e, t)] = anchor[(names[(i - 1) % m], t)]
    return {"anchor": anchor, "neighbour": None,
            "neighbour_note": ("long-only buyback arm uses the SAME S_i(t) exposure vector "
                               "(portfolio construction variant) — anchor-vs-neighbour rho "
                               "= 1.0 by construction"),
            "control": control}


def build_a6_h2(C):
    """SFV11-A6-H2 — event-window holding-indicator exposure on the weekly
    5-session scheduling grid. Predictor: next_hat = the latest evidenced
    arrival projected forward in frozen 364-day steps (V11-E3 cadence constant)
    to the first projection after t; window = [next_hat-7, next_hat+7]; an
    entity is scheduled when the window STARTS within the next 5 sessions and
    the tranche floor (>= 5 names) is met. exposure(e,t) = 1 if an open
    anchor-scheduled window covers t else 0. neighbour = sector-residual hedged
    book — the SAME name legs (hedge leg only), so the indicator is identical
    and the neighbour rho is 1.0 by construction. control = sham calendar: for
    each anchor window the first 15-calendar-day position, searched forward in
    15-day steps from the anchor window start, that contains NO evidenced
    filer-event date of the entity."""
    anchor_cells, control_cells = {}, {}
    sched_counts = {f["fold_id"]: 0 for f in C.folds}
    sham_ok = {f["fold_id"]: 0 for f in C.folds}
    sham_fail = {f["fold_id"]: 0 for f in C.folds}
    arrivals = {}
    for cik, fa, _cls, _sb in C.events:
        arrivals.setdefault(cik, []).append(dd(fa))
    for e in arrivals:
        arrivals[e].sort()
    folds_dd = [(f["fold_id"], dd(f["start"]), dd(f["end"])) for f in C.folds]

    def window_sessions(e, w0, w1, fold_triple):
        s = C.series.get(e)
        if s is None:
            return None
        _fid, flo, fhi = fold_triple
        a = None
        for k in range(bisect_left(s["dates"], flo), bisect_right(s["dates"], fhi)):
            if s["dates"][k] >= w0:
                a = k
                break
        if a is None:
            return None
        b = a
        rng = range(bisect_left(s["dates"], flo), bisect_right(s["dates"], fhi))
        for k in rng:
            if s["dates"][k] <= w1:
                b = max(b, k)
        if b < a:
            return None
        return list(range(a, b + 1))

    for t in grid_dates_flat(C, C.grid5):
        fold_triple = next((x for x in folds_dd if x[1] <= t <= x[2]), None)
        if fold_triple is None:
            continue
        gi = C.sess_idx[t]
        hi_s = C.sessions[min(gi + 5, len(C.sessions) - 1)]
        tranche = []
        for e in sorted(C.series):
            if not has_bars(C, e, t):
                continue
            arrs = arrivals.get(e)
            if not arrs:
                continue
            k = bisect_right(arrs, t) - 1
            if k < 0:
                continue
            a_last = arrs[k]
            next_hat = a_last + timedelta(days=364 * (1 + (t - a_last).days // 364))
            w0 = next_hat - timedelta(days=7)
            if not (t < w0 <= hi_s) or w0 > fold_triple[2]:
                continue
            tranche.append((e, w0))
        if len(tranche) < 5:
            continue  # frozen tranche floor: abstain
        sched_counts[fold_triple[0]] += len(tranche)
        for e, w0 in tranche:
            w1 = w0 + timedelta(days=14)
            sess = window_sessions(e, w0, w1, fold_triple)
            if not sess:
                continue
            s = C.series[e]
            for k in sess:
                anchor_cells[(e, s["dates"][k])] = 1.0
            # ---- sham calendar: first clear 15-day position, 15-day steps
            ev = C.event_dates.get(e, set())
            placed = None
            step = 0
            while True:
                c0 = w0 + timedelta(days=15 * step)
                if c0 > fold_triple[2]:
                    break
                clear = True
                for i in range(15):
                    if (c0 + timedelta(days=i)).isoformat() in ev:
                        clear = False
                        break
                if clear:
                    placed = c0
                    break
                step += 1
            if placed is None:
                sham_fail[fold_triple[0]] += 1
                continue
            sess2 = window_sessions(e, placed, placed + timedelta(days=14), fold_triple)
            if not sess2:
                sham_fail[fold_triple[0]] += 1
                continue
            sham_ok[fold_triple[0]] += 1
            for k in sess2:
                control_cells[(e, s["dates"][k])] = 1.0
    return {"anchor_cells": anchor_cells, "control_cells": control_cells,
            "neighbour": None,
            "neighbour_note": ("sector-residual hedged arm holds the SAME name legs — the "
                               "holding-indicator exposure is identical, anchor-vs-neighbour "
                               "rho = 1.0 by construction"),
            "sched_counts": sched_counts, "sham_ok": sham_ok, "sham_fail": sham_fail}


PROPOSAL_BUILDERS = {
    "SFV11-A4-H1": lambda C: build_a4(C, h2=False),
    "SFV11-A4-H2": lambda C: build_a4(C, h2=True),
    "SFV11-A5-H1": build_a5_h1,
    "SFV11-A5-H2": build_a5_h2,
    "SFV11-A6-H1": build_a6_h1,
    "SFV11-A6-H2": build_a6_h2,
}


# ===========================================================================
# CORRELATION + VERDICTS
# ===========================================================================
def novelty_block(C, anchor):
    entry = {"veto_rho": {}, "n_per_veto": {}}
    for vn in VETO_NAMES:
        vf = VETO_BUILDERS[vn]
        common_a, common_v = [], []
        for (e, t), av in anchor.items():
            vv = vf(C, e, t)
            if vv is not None:
                common_a.append(av)
                common_v.append(vv)
        rho = spearman(common_a, common_v)
        entry["veto_rho"][vn] = None if rho is None else round(rho, 4)
        entry["n_per_veto"][vn] = len(common_a)
    valid = {vn: abs(v) for vn, v in entry["veto_rho"].items() if v is not None}
    entry["max_abs_veto_rho"] = round(max(valid.values()), 4) if valid else None
    arg = max(sorted(valid), key=lambda k: valid[k]) if valid else None
    entry["argmax_veto"] = arg
    entry["margin_to_020"] = (round(NOVELTY_BAR - valid[arg], 4) if arg else None)
    entry["vetoes_measured"] = len(valid)
    # fail-closed: ALL ELEVEN forbidden-ancestor entries must be measured
    entry["novelty_pass_le_020"] = (len(valid) == len(VETO_NAMES)
                                    and max(valid.values()) <= NOVELTY_BAR)
    return entry


def rho_on_common(a, b):
    common = [k for k in a if k in b]
    if not common:
        return None, 0
    return spearman([a[k] for k in common], [b[k] for k in common]), len(common)


def rho_on_union_zerofill(a, b):
    ka = sorted(set(a) | set(b))  # sorted: no hash-order dependence
    va = [a.get(k, 0.0) for k in ka]
    vb = [b.get(k, 0.0) for k in ka]
    return spearman(va, vb), len(ka)


def gate_text_for(pid):
    try:
        prop = json.loads((PROPOSALS_DIR / PROPOSAL_FILES[pid]).read_text())
        chk = prop.get("pre_selection_identifiability_check", {})
        return chk.get("gate") or chk.get("anchor_vs_control_gate") or chk.get("rule") or ""
    except Exception as ex:  # pragma: no cover
        return f"READ_FAILED: {ex}"


def identifiability_block(C, pid, built):
    g = GATES[pid]
    out = {"gate_value": g, "anchor_vs_control_rho": None,
           "control_identifiable": None, "margin_to_gate": None,
           "anchor_vs_neighbour_rho": None, "neighbour_pairs": None}
    gt = gate_text_for(pid)
    out["gate_declared_text"] = gt[:600]
    out["gate_number_found_in_text"] = (f"{g:.2f}" in gt) or (f"{g:g}" in gt)

    if pid in ("SFV11-A4-H1", "SFV11-A4-H2"):
        rho, n = rho_on_union_zerofill(built["anchor_cells"], built["control_cells"])
        out["control_cells"] = n
        out["grid"] = "union (entity, calendar-date) cells, positions +1/-1 open, 0 flat/absent"
        ctr = built["counters"]
        out["control_runnability"] = {
            "matched_events": ctr["matched_events"],
            "sham_no_clear_window": ctr["sham_no_clear_window"],
            "sham_pseudo_signal_abstain": ctr["sham_pseudo_signal_abstain"],
        }
    elif pid in ("SFV11-A5-H1", "SFV11-A5-H2", "SFV11-A6-H1"):
        rho, n = rho_on_common(built["anchor"], built["control"])
        out["control_cells"] = n
        if pid in ("SFV11-A5-H1", "SFV11-A5-H2"):
            # per-date rho compliance share (R1 second clause), dates in
            # session-index order
            okd = tot = 0
            for t in grid_dates_flat(C, C.grid21):
                ks = sorted(k for k in built["anchor"] if k[1] == t and k in built["control"])
                if len(ks) < 10:
                    continue
                r = spearman([built["anchor"][k] for k in ks],
                             [built["control"][k] for k in ks])
                if r is None:
                    continue
                tot += 1
                okd += 1 if abs(r) <= g else 0
            out["per_date_le_gate_share"] = round(okd / tot, 4) if tot else None
            out["per_date_dates_measured"] = tot
    else:  # SFV11-A6-H2
        rho, n = rho_on_union_zerofill(built["anchor_cells"], built["control_cells"])
        out["control_cells"] = n
        out["grid"] = "union (entity, calendar-date) holding-indicator cells"
        out["control_runnability"] = {
            "scheduled_windows": int(sum(built["sched_counts"].values())),
            "sham_placed": int(sum(built["sham_ok"].values())),
            "sham_failed": int(sum(built["sham_fail"].values())),
        }
    out["anchor_vs_control_rho"] = None if rho is None else round(rho, 4)
    if rho is not None:
        out["control_identifiable"] = bool(abs(rho) < g)
        out["margin_to_gate"] = round(g - abs(rho), 4)
    if built.get("neighbour") is not None:
        rn, nn = rho_on_common(built["anchor"], built["neighbour"])
        out["anchor_vs_neighbour_rho"] = None if rn is None else round(rn, 4)
        out["neighbour_pairs"] = nn
    else:
        out["anchor_vs_neighbour_rho"] = 1.0
        out["neighbour_pairs"] = 0
        out["anchor_vs_neighbour_note"] = built.get(
            "neighbour_note", "neighbour uses the identical exposure vector")
    return out


# ===========================================================================
# FEASIBILITY (A9-F arithmetic; zero PnL)
# ===========================================================================
def feasibility_block(C, pid, built):
    floor_overall, floor_fold = 30, 5
    out = {"floors": {"overall_min": floor_overall, "per_fold_min": floor_fold}}
    ar = out["arithmetic"] = {}

    def decisions_block(overall, per_fold, warmup, basis):
        scored = overall - warmup
        return {"basis": basis,
                "grid_or_event_decisions_overall": overall,
                "warmup_decisions_deducted_overall": warmup,
                "expected_scored_decisions_overall": scored,
                "expected_scored_decisions_per_fold": dict(per_fold),
                "margin_overall_vs_30": scored - floor_overall,
                "margin_min_fold_vs_5": (min(per_fold.values()) - floor_fold)
                                        if per_fold else None,
                "floors_pass": bool(scored >= floor_overall and per_fold
                                    and min(per_fold.values()) >= floor_fold)}

    if pid in ("SFV11-A4-H1", "SFV11-A4-H2"):
        # P0 census arithmetic: in-universe (two sanctioned legs) events with
        # >= 20 STRICT_NEXT_BAR bars, per fold, from the derived event artifact
        per_fold = {f["fold_id"]: 0 for f in C.folds}
        total = 0
        h2_counts = {f["fold_id"]: [0, 0] for f in C.folds}  # [amendment, first]
        for cik, fa, cls, sb in C.events:
            if cls not in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED") or sb is None or sb < 20:
                continue
            f = fold_of(C, dd(fa))
            if f is None:
                continue
            per_fold[f["fold_id"]] += 1
            total += 1
            if pid == "SFV11-A4-H2":
                h2_counts[f["fold_id"]][0 if chain_is_amendment(C, cik, fa) else 1] += 1
        entry_dates = {}
        for (e, t) in built["anchor"]:
            fid = next((f["fold_id"] for f in C.folds if dd(f["start"]) <= t <= dd(f["end"])),
                       None)
            if fid:
                entry_dates.setdefault(fid, set()).add(t.isoformat())
        dec = {fid: len(ds) for fid, ds in sorted(entry_dates.items())}
        ar["census_event_counts_per_fold_ge20_strict"] = per_fold
        ar["census_event_count_overall"] = total
        ar["scored_decision_dates_distinct_per_fold"] = dec
        out["decisions"] = decisions_block(
            sum(dec.values()), dec, WARMUP[pid],
            "event-anchored: distinct entry-fill calendar dates per fold (a scored decision "
            "= a date with >= 1 entry fill and >= 1 non-CASH leg); an upper bound on the "
            "event count is the census per-fold event counts shown above")
        arms = 3
        fills = total * arms * 2
        slot_two_way = 2 / 14 * ANNUAL_SESSIONS
        slot_rt = ANNUAL_SESSIONS / 14
        ceil_v = TURNOVER_CEILING[pid]
        ar["turnover_ceiling"] = {
            "declared_ceiling_two_way_per_year": ceil_v,
            "arithmetic": (f"events={total} x arms={arms} x 2 fills = {fills} fills; "
                           f"holding bar6..bar20 = 14 session steps; slot churn = "
                           f"2/14 x {ANNUAL_SESSIONS} = {slot_two_way:.1f} two-way/yr "
                           f"(ADJ-5 fill reading) vs ceiling {ceil_v:g} -> margin "
                           f"{ceil_v - slot_two_way:+.1f}; round-trip reading "
                           f"{ANNUAL_SESSIONS}/14 = {slot_rt:.1f}/yr -> margin "
                           f"{ceil_v - slot_rt:+.1f}"),
            "implied_two_way_per_year_fill_convention": round(slot_two_way, 2),
            "implied_round_trips_per_year": round(slot_rt, 2),
            "note": ("two-way convention ambiguity recorded; the against-eligibility reading "
                     "is the ADJ-5 fill convention (higher churn); the ceiling margin is "
                     "A9-adjudicated on the actual book — reported, never silently passed"),
        }
        if pid == "SFV11-A4-H2":
            ar["partition_counts_amend_first_per_fold"] = {
                k: {"amendment_arrivals_chain_ge2": v[0], "first_vintage_arrivals": v[1]}
                for k, v in sorted(h2_counts.items())}
        ctr = built["counters"]
        out["control_runnability"] = {
            "matched_events": ctr["matched_events"],
            "sham_no_clear_window": ctr["sham_no_clear_window"],
            "sham_pseudo_signal_abstain": ctr["sham_pseudo_signal_abstain"],
            "p0_census_reference": ("19 entities with zero clear 20-bar windows (P0 census "
                                    "section d) — declared ex-ante as matched-subset "
                                    "falsification; honest, not infeasible"),
            "runnable": ctr["matched_events"] > 0
                        and ctr["sham_no_clear_window"] < ctr["matched_events"],
        }
    elif pid in ("SFV11-A5-H1", "SFV11-A5-H2"):
        per_fold = {fid: len(C.grid21[fid]) for fid in sorted(C.grid21)}
        ar["grid_decisions_per_fold_21s"] = per_fold
        out["decisions"] = decisions_block(
            sum(per_fold.values()), per_fold, WARMUP[pid],
            "inherited 21-session grid: per-fold local session indices 63+21k")
        ceil_v = TURNOVER_CEILING[pid]
        ar["turnover_ceiling"] = {
            "declared_ceiling_two_way_per_year": ceil_v,
            "arithmetic": (f"{sum(per_fold.values())} grid decisions over ~3.5y -> ~12 "
                           f"decisions/yr; upper bound without hysteresis 2.0 two-way per "
                           f"decision x 12 = 24.0/yr; per-slot 2/21 x {ANNUAL_SESSIONS} = "
                           f"{2 / 21 * ANNUAL_SESSIONS:.1f}/yr vs ceiling {ceil_v:g}; the "
                           "declared hysteresis is the design response (expectation 'below "
                           "the 6.0/year ceiling'); measured on the actual book by A9"),
        }
        out["control_runnability"] = {
            "mechanism": ("A5-H1 within-sector permutation / A5-H2 geometry-null label "
                          "redraw — both run wherever the anchor runs, by construction"),
            "runnable": True,
        }
    elif pid == "SFV11-A6-H1":
        per_fold = {fid: len(C.grid21[fid]) for fid in sorted(C.grid21)}
        ar["grid_decisions_per_fold_21s"] = per_fold
        out["decisions"] = decisions_block(
            sum(per_fold.values()), per_fold, WARMUP[pid],
            "inherited 21-session grid; 3 warmup decisions deducted overall per "
            "warmup_decisions")
        ents = len({e for (e, _t) in built["anchor"]})
        ar["entities_with_defined_exposure"] = ents
        ar["cohort_floor"] = {"floor_valid_exposures_per_decision": 30,
                              "measured_entities_with_exposure_any_date": ents,
                              "note": "A9 re-verifies the per-decision valid-exposure floor",
                              "runnable": ents >= 30}
        ar["turnover_ceiling"] = {
            "declared_ceiling_two_way_per_year": None,
            "arithmetic": ("per-decision one-way ~1x gross declared; ~12 decisions/yr -> "
                           "~24 two-way/yr structural; NO numeric ceiling declared in "
                           "turnover_and_sample_floor — nothing to breach; A9 verifies"),
        }
        out["control_runnability"] = {
            "mechanism": ("deterministic hash-order permutation placebo — abstains exactly "
                          "where the anchor abstains, can never abort (forex V3 lesson)"),
            "runnable": True,
        }
    else:  # SFV11-A6-H2
        per_fold = {fid: len(C.grid5[fid]) for fid in sorted(C.grid5)}
        ar["scheduling_decisions_per_fold_weekly_5s"] = per_fold
        ar["scheduled_windows_measured_per_fold"] = dict(built["sched_counts"])
        ar["declared_lane_precheck"] = {
            "windows_total": 37527,
            "by_fold": {"S0_FOLD_1": 14846, "S0_FOLD_2": 12262, "S0_FOLD_3": 10419},
            "source": "A6-H2 decision_grid / non_vacuity_gates (P0 derived artifact); "
                      "the module's own measured counts are shown alongside",
        }
        out["decisions"] = decisions_block(
            int(sum(built["sched_counts"].values())), dict(built["sched_counts"]),
            WARMUP[pid],
            "scored decisions = scheduled windows (warmup 1 deducted overall)")
        placed = int(sum(built["sham_ok"].values()))
        failed = int(sum(built["sham_fail"].values()))
        ar["sham_runnability"] = {
            "sham_placed": placed,
            "sham_failed": failed,
            "match_rate": round(placed / max(1, placed + failed), 4),
            "gate": 0.80,
            "p0_reference": ("clear-window density 84.6% at the 20-bar bracket; 3 entities "
                             "with zero clear 5-bar windows excluded-from-control-only "
                             "(declared; tolerated per P0 limitation note)"),
        }
        ar["turnover_ceiling"] = {
            "declared_ceiling_two_way_per_year": None,
            "arithmetic": ("one entry + one exit fill per window per side; ~10.5 sessions "
                           "held per 15-day window -> ~47.6 two-way/yr per slot structural; "
                           "NO numeric ceiling declared in turnover_and_sample_floor; "
                           "A9 verifies"),
        }
        out["control_runnability"] = {
            "scheduled_windows": int(sum(built["sched_counts"].values())),
            "sham_placed": placed,
            "sham_failed": failed,
            "runnable": placed > 0,
        }

    d = out["decisions"]
    ok_floors = d["floors_pass"]
    ok_ctrl = out["control_runnability"].get("runnable", True)
    if not ok_floors and not ok_ctrl:
        out["verdict"] = "INFEASIBLE_FLOORS_AND_CONTROL"
    elif not ok_floors:
        out["verdict"] = "INFEASIBLE_FLOORS_MISSED"
    elif not ok_ctrl:
        out["verdict"] = "INFEASIBLE_CONTROL_CANNOT_RUN"
    else:
        out["verdict"] = "RUNNABLE"
    out["declared_constraints_note"] = (
        "infeasibility_declarations respected: a declared-and-designed-around limitation is "
        "honest, not infeasible (excluded-with-reason counts carried in the counters)")
    return out


# ===========================================================================
# HASH / WAVE VERIFICATION
# ===========================================================================
def verify_hashes():
    pins = json.loads(HASHES_FILE.read_text())["hashes"]
    out = {}
    ok = True
    for pid, fn in PROPOSAL_FILES.items():
        p = PROPOSALS_DIR / fn
        if not p.exists():
            out[fn] = {"pin": pins.get(fn), "measured": None, "verdict": "MISSING_FILE"}
            ok = False
            continue
        measured = sha256_hex(p.read_bytes())
        verdict = "MATCH" if pins.get(fn) == measured else "MISMATCH"
        out[fn] = {"pin": pins.get(fn), "measured": measured, "verdict": verdict}
        if verdict != "MATCH":
            ok = False
        try:
            prop = json.loads(p.read_text())
            if prop.get("wave_sha") != WAVE_SHA:
                out[fn]["wave_sha_verdict"] = "MISMATCH"
                ok = False
            else:
                out[fn]["wave_sha_verdict"] = "MATCH"
        except Exception:
            out[fn]["wave_sha_verdict"] = "UNREADABLE"
            ok = False
    return ok, out


def build_audit_skeleton(built_at_utc, proposal_hashes):
    return {
        "schema": "stocks_free_v11_run/d2_novelty_measure@1",
        "built_at_utc": built_at_utc,
        "producer_role": "D2 measurement lane module (executed by A1)",
        "wave_sha": WAVE_SHA,
        "discipline": ("feature/rank arithmetic only; zero PnL; universe = entity-decision "
                       "pairs where the proposal exposure is defined on the bookable pool "
                       "(ALIVE_EVIDENCED + DEAD_EVIDENCED); grid families additionally "
                       "require >= 63 price bars through the decision session, event-anchored "
                       "A4 families use their declared >= 20 STRICT_NEXT_BAR conditioning; "
                       "Spearman midrank ties, pooled; deterministic output (built_at passed "
                       "by the runner)"),
        "proposal_hashes": proposal_hashes,
        "decision_dates": {},
        "veto_set": {"count": len(VETO_NAMES), "names": VETO_NAMES,
                     "rev_dir_encoding": {"mapping": REV_DIR_ENCODING,
                                          "authority": "v10 P0 manifest dir_counts "
                                                       "(up 63342 / flat 1519910 / down 84170)"}},
        "conventions_applied": {"global": [], "per_proposal": {}},
        "results": {},
        "verdict_rule": ("INELIGIBLE_NOVELTY if max|rho| > 0.20 vs any of the eleven veto "
                         "entries (argmax veto + rho + margin reported); "
                         "INELIGIBLE_CONTROL_UNIDENTIFIABLE if |anchor-control rho| >= the "
                         "gate declared in that proposal's pre_selection_identifiability_check "
                         "(0.95 A4-H1/H2, 0.30 A5-H1, 0.70 A5-H2, 0.10 A6-H1/H2); else "
                         "ELIGIBLE on the novelty/identifiability dimension — feasibility is "
                         "reported separately as RUNNABLE / INFEASIBLE_<REASON>; novelty is "
                         "fail-closed (a null veto entry fails the gate, never passes open)"),
    }


REQUIRED_SCHEMA_FIELDS = ["schema", "built_at_utc", "producer_role", "wave_sha",
                          "proposal_hashes", "decision_dates", "veto_set",
                          "conventions_applied", "results", "verdict_rule"]

GLOBAL_CONVENTIONS = [
    "group->entity aggregation by MEAN over qualifying groups so rank correlation is defined "
    "at the entity level (house convention; applied in the A4 anchors, the veto-10 mean over "
    "the most-recent-stamp groups, and every share-valued exposure)",
    "PIT stamps: veto 10 windows on observable_available_at (most recent in-window stamp, "
    "ties averaged); veto 11 window observable_available_at <= t and > t-800d, per the D2 "
    "mandate wording",
    "rev_dir encoding -1=down / 0=flat / 1=up, fail-closed verified at runtime against the "
    "V10 P0 manifest dir_counts",
    "veto values evaluated at arbitrary (entity, decision-instant) pairs including "
    "event-anchored dates; the 63-bar lookback family uses adjusted closes strictly before "
    "t (inherited V10 form unchanged); accounting vetoes as-of t (latest avail < t)",
    "sector_exposure_form sector means computed over all priced bookable entities with a "
    "defined 63s momentum at the same decision instant (V10 form)",
    "Spearman midrank ties, pooled; n >= 10 per comparison else None; novelty fail-closed: a "
    "null veto measurement fails the gate",
    "decision grids: 21-session grid = per-fold local session indices 63+21k (A5-H1/H2, "
    "A6-H1); weekly 5-session scheduling grid = per-fold local indices 63+5k (A6-H2; the 63 "
    "offset is the inherited eligibility warmup — recorded convention)",
    "A4 abstain-with-reason semantics: the exposure pair is excluded (counted) when the "
    "reaction is exactly 0, a required entity/benchmark bar is missing, or the sector tag "
    "is unmapped — against-eligibility resolution of the 'missing dates abstain' clause",
    "A4 residual-reaction base: bar 1's return is measured from the last close at-or-before "
    "the arrival (STRICT_NEXT_BAR); the benchmark must print closes on all six dates d0..d5 "
    "else the event abstains (against-eligibility)",
]

PER_PROPOSAL_CONVENTIONS = {
    "SFV11-A4-H1": [
        "anchor exposure(e, t=bar-6 close date) = sign of the 5-bar sector-residual initial "
        "reaction; universe = in-fold arrivals of the two sanctioned cohort legs with >= 20 "
        "STRICT_NEXT_BAR bars; neighbour = identical arithmetic vs SPY",
        "identifiability control = hash-seeded (sha256 of 'cik|first_avail') uniformly drawn "
        "clear 20-bar sham window inside the matched event's fold (P0 section-d clearance); "
        "enumerated deterministically via prefix sums over clear window starts + hash-mod "
        "index (uniform over clear windows)",
        "anchor-vs-control rho on the aligned (entity, calendar-date) UNION cell grid, "
        "positions coded +1/-1 open and 0 flat/absent (0-fill on the union)",
        "same-entity same-date collisions of multiple events aggregate the open signs and "
        "code the net state (MEAN-family house convention)",
    ],
    "SFV11-A4-H2": [
        "anchor = AMENDMENT arrivals only: chain position >= 2 derived from timing-layer "
        "group keys with stamps <= the arrival (an arrival is an amendment iff any "
        "same-filer-period group has first_avail strictly before it; the exact rank is "
        "bounded [2, depth_g] from the group aggregates; max over groups = "
        "against-eligibility)",
        "neighbour = FIRST-VINTAGE arrivals (chain position 1) with identical arithmetic",
        "sham control identical to H1, matched 1:1 on the amendment events; union-grid "
        "position-state rho, gate 0.95",
    ],
    "SFV11-A5-H1": [
        "anchor late_share on the raw share values (no standardization) per the exposure "
        "definition; Q window last_avail in [t-800d, t), floor |Q| >= 4",
        "control = within-sector marginal-preserving permutation of the anchor values "
        "(numpy PCG64 seed 20260907, applied to the CIK-sorted index vector, redrawn per "
        "decision date in session-index order; sectors of size 1 map to identity)",
        "anchor-vs-neighbour rho on common (entity, date) pairs (deep_share neighbour)",
    ],
    "SFV11-A5-H2": [
        "anchor HHI over timing-layer depth>=2 groups (fields enter as chain keys only); "
        "Q window last_avail in [t-800d, t), floor N >= 4",
        "control = geometry-null: per entity-date keep N and the field set F exactly and "
        "REDRAW each group's field label uniformly over F via the PCG64 permutation applied "
        "to the group-key-sorted index vector (labels F_order[p[i] mod |F|]); the "
        "alternative within-entity label-permutation reading was REJECTED as internally "
        "contradictory (it would leave the per-entity n_f multiset — and therefore HHI — "
        "invariant, making control == anchor and contradicting the proposal's declared "
        "0.2-0.5 expected band and its 'only the repetition geometry is destroyed' text)",
        "neighbour = median amend_count over Q on the same pairs",
    ],
    "SFV11-A6-H1": [
        "primary field per entity = the priority-ordered share field with the most period "
        "groups (ties broken by the declared priority order)",
        "V_last = the latest qualifying eff-period group (group first_avail < t, within "
        "800d) valued at its latest vintage with avail < t; V_prev = the immediately "
        "preceding eff group valued the same as-of way — the as-of convention matches the "
        "accounting-veto reading (highest plausible correlation to vetoed forms; "
        "against-eligibility)",
        "|S| > ln 2 excluded; both values strictly positive required",
        "neighbour (long-only buyback) uses the SAME exposure vector — neighbour rho 1.0 by "
        "construction, recorded",
        "control = exposure values rotated by one in the hex-sorted "
        "sha256('cycle|hid|cik|decision_index') hash order per decision (no RNG library, "
        "byte-reproducible) — the deterministic permutation placebo as declared",
    ],
    "SFV11-A6-H2": [
        "predictor: next_hat = the latest evidenced arrival projected forward in frozen "
        "364-day steps (V11-E3 cadence constant) to the first projection after t; window "
        "[next_hat-7, next_hat+7]; scheduled when the window starts within the next 5 "
        "sessions and the tranche floor (>= 5 names) is met; exposure = holding indicator "
        "(1 while an open anchor window covers the date) at scheduling dates",
        "scheduling grid = per-fold local session indices 63+5k (the 63 offset is the "
        "inherited eligibility warmup; recorded convention — it shifts scheduling dates "
        "only, not the exposure form); the declared lane pre-check window counts are cited "
        "alongside the module's own measured counts",
        "control = sham calendar: the first 15-calendar-day position searched forward in "
        "15-day steps from the anchor window start containing no evidenced event date, "
        "clipped to the fold; windows with no clear position excluded-with-reason (counted), "
        "per the declared P0 limitation note",
        "neighbour (sector-residual hedged) holds the SAME name legs — the indicator is "
        "identical, rho 1.0 by construction, recorded",
    ],
}


# ===========================================================================
# MAIN (heavy run) + SELFCHECK (tiny synthetic fixtures)
# ===========================================================================
def run_full(built_at_utc):
    ok, hashes = verify_hashes()
    if not ok:
        for fn, rec in hashes.items():
            if rec.get("verdict") != "MATCH" or rec.get("wave_sha_verdict") != "MATCH":
                sys.stderr.write(f"BLOCKED: proposal hash/wave pin mismatch {fn}: {rec}\n")
        return 2
    print("[d2] proposal hash pins verified (6/6 MATCH).", flush=True)

    C, rc = load_context()
    if rc != 0:
        return rc

    audit = build_audit_skeleton(built_at_utc, hashes)
    audit["decision_dates"] = {
        "grid_21s_per_fold": {fid: [d.isoformat() for d in C.grid21[fid]]
                              for fid in sorted(C.grid21)},
        "scheduling_weekly_5s_per_fold": {fid: [d.isoformat() for d in C.grid5[fid]]
                                          for fid in sorted(C.grid5)},
        "a4_event_anchored": {
            "note": ("A4 decision instants are arrival-anchored (t = the bar-6 close date of "
                     "each in-fold event); no fixed date grid — folds: "
                     + "; ".join(f"{f['fold_id']} {f['start']}..{f['end']}" for f in C.folds)),
            "folds": C.folds,
        },
    }
    audit["veto_set"]["rev_dir_encoding"]["runtime_check"] = C.dir_check
    audit["conventions_applied"]["global"] = GLOBAL_CONVENTIONS
    audit["conventions_applied"]["per_proposal"] = PER_PROPOSAL_CONVENTIONS

    for pid in PROPOSAL_ORDER:
        print(f"[d2] building {pid}...", flush=True)
        built = PROPOSAL_BUILDERS[pid](C)
        nov = novelty_block(C, built["anchor"] if built.get("anchor") is not None
                            else built["anchor_cells"])
        ident = identifiability_block(C, pid, built)
        feas = feasibility_block(C, pid, built)
        if not nov["novelty_pass_le_020"]:
            verdict = "INELIGIBLE_NOVELTY"
        elif ident["control_identifiable"] is False:
            verdict = "INELIGIBLE_CONTROL_UNIDENTIFIABLE"
        else:
            verdict = "ELIGIBLE"
        audit["results"][pid] = {
            "proposal_file": PROPOSAL_FILES[pid],
            "anchor_pairs": len(built["anchor"]) if built.get("anchor") is not None
                            else len(built["anchor_cells"]),
            "counters": built.get("counters", {}),
            "novelty": nov,
            "identifiability": ident,
            "feasibility": feas,
            "verdict": verdict,
        }
        print(f"[d2] {pid}: pairs={audit['results'][pid]['anchor_pairs']} "
              f"max|rho|={nov['max_abs_veto_rho']} argmax={nov['argmax_veto']} "
              f"ctrl_rho={ident['anchor_vs_control_rho']} gate={ident['gate_value']} "
              f"feas={feas['verdict']} -> {verdict}", flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, indent=1, sort_keys=True) + "\n")
    print("[d2] written", OUT, flush=True)
    return 0


# ------------------------- selfcheck fixtures ------------------------------
def _synth_ctx():
    import numpy as np

    class Ctx:
        pass

    C = Ctx()
    C.np = np
    C.rng = np.random.Generator(np.random.PCG64(PCG_SEED))
    sessions = []
    d = date(2018, 1, 1)
    while len(sessions) < 520:  # ~2 years of weekdays
        if d.weekday() < 5:
            sessions.append(d)
        d += timedelta(days=1)
    C.sessions = sessions
    C.sess_idx = {x: i for i, x in enumerate(sessions)}
    C.folds = [{"fold_id": "F1", "start": "2018-01-01", "end": "2019-12-31"}]

    def mk(base, drift):
        adj, close, vol, dates = [], [], [], []
        p = base
        for s in sessions:
            p *= (1.0 + drift)
            dates.append(s)
            close.append(round(p, 4))
            adj.append(round(p, 4))
            vol.append(1_000_000)
        return {"dates": dates, "close": close, "adj": adj, "vol": vol}

    ciks = [f"CIK000000000{i}" for i in range(1, 7)]
    C.series = {c: mk(100.0, 0.002 if i % 2 == 0 else -0.001) for i, c in enumerate(ciks, 1)}
    C.bookable = {c: {"sector": "XLV", "ticker": f"T{i}"} for i, c in enumerate(ciks, 1)}
    # benchmarks perfectly flat -> entity drift dominates the residual sign
    C.bench = {"SPY": {s: 100.0 for s in sessions},
               "XLV": {s: 100.0 for s in sessions}}

    pre = {}
    for cik, s in C.series.items():
        n = len(s["adj"])
        lr = [0.0] + [math.log(s["adj"][i] / s["adj"][i - 1]) for i in range(1, n)]
        s_lr = array("d", [0.0] * n)
        s_l2 = array("d", [0.0] * n)
        s_dn = array("d", [0.0] * n)
        for i in range(1, n):
            s_lr[i] = s_lr[i - 1] + lr[i]
            s_l2[i] = s_l2[i - 1] + lr[i] ** 2
            s_dn[i] = s_dn[i - 1] + (lr[i] ** 2 if lr[i] < 0 else 0.0)
        pre[cik] = (s_lr, s_l2, s_dn, [True] * n)
    C.pre = pre

    # accounting fields for the ratio vetoes (avail before all fixture dates;
    # a prior-annual (Dec) row pair so the flow/depletion legs resolve; lists
    # APPENDED per (cik, f) and SORTED by avail — _asof binary-searches)
    fields = {}
    for cik in ciks:
        for f, v in (("us-gaap:Assets", 1000.0),
                     ("us-gaap:AssetsCurrent", 500.0),
                     ("us-gaap:LiabilitiesCurrent", 200.0),
                     ("us-gaap:Goodwill", 100.0),
                     ("us-gaap:CashAndCashEquivalentsAtCarryingValue", 50.0),
                     ("us-gaap:RetainedEarningsAccumulatedDeficit", 300.0),
                     ("us-gaap:AccountsReceivableNetCurrent", 120.0),
                     ("us-gaap:InventoryNet", 80.0),
                     ("us-gaap:AccountsPayableCurrent", 60.0)):
            fields.setdefault((cik, f), []).append(("2017-01-01", "2016-12-31", v))
        for f, v in (("us-gaap:RetainedEarningsAccumulatedDeficit", 250.0),
                     ("us-gaap:AccountsReceivableNetCurrent", 100.0),
                     ("us-gaap:InventoryNet", 70.0),
                     ("us-gaap:AccountsPayableCurrent", 50.0)):
            fields.setdefault((cik, f), []).append(("2016-01-15", "2015-12-31", v))
    for k in fields:
        fields[k].sort()
    C.fields = fields

    # timing rows: (first_avail, eff, f, last_avail, depth, amend, own_z, obs_avail)
    tim = {}
    for cik in ciks:
        rows = [("2018-04-02", "2018-03-31", "us-gaap:CommonStockSharesOutstanding",
                 "2018-04-02", 1, 0, None, "2018-04-02")]
        if cik == "CIK0000000001":
            rows += [
                ("2018-03-01", "2017-12-31", "us-gaap:Revenues", "2018-03-01", 1, 0, None,
                 "2018-03-01"),
                ("2018-03-05", "2018-03-31", "us-gaap:CommonStockSharesOutstanding",
                 "2018-04-02", 2, 1, 0.5, "2018-04-02"),
                ("2018-03-06", "2018-03-31", "us-gaap:Revenues", "2018-04-03", 2, 1, 1.0,
                 "2018-04-03"),
            ]
        tim[cik] = sorted(rows, key=lambda x: (x[7], x[0], x[1], x[2]))
    C.tim = tim
    C.ownz = {}
    for e, rows in tim.items():
        lst = sorted((r[7], r[6]) for r in rows if r[6] is not None)
        if lst:
            C.ownz[e] = ([x[0] for x in lst], array("d", [x[1] for x in lst]))
    tim_d2 = {}
    for cik in ciks:
        rows = [("2018-04-02", "us-gaap:Revenues", "2017-12-31", 1),
                ("2018-04-03", "us-gaap:Revenues", "2017-09-30", 1),
                ("2018-04-04", "us-gaap:Revenues", "2017-06-30", 1),
                ("2018-04-05", "us-gaap:Revenues", "2017-03-31", 1)]
        if cik == "CIK0000000001":
            rows = [("2018-04-02", "us-gaap:CommonStockSharesOutstanding", "2018-03-31", 1),
                    ("2018-04-03", "us-gaap:Revenues", "2018-03-31", 2),
                    ("2018-04-04", "us-gaap:Revenues", "2017-12-31", 1),
                    ("2018-04-05", "us-gaap:Revenues", "2017-09-30", 6)]
        rows.sort()
        tim_d2[cik] = (rows, [x[0] for x in rows])
    C.tim_d2 = tim_d2

    # revision rows: (last_avail, rev_dir, rev_mag, inter_arrival_days, depth)
    rev = {}
    for cik in ciks:
        rows = [("2018-04-02", 1, 0.1, 100, 2),
                ("2018-04-03", 1, 0.1, 100, 2),
                ("2018-04-04", 1, 0.1, 100, 2),
                ("2018-04-05", 1, 0.1, 100, 2)]
        if cik == "CIK0000000001":
            rows = [("2018-04-02", -1, 0.1, 500, 6),   # down, late, deep
                    ("2018-04-03", 0, 0.0, 200, 2),    # flat
                    ("2018-04-04", 1, 0.2, 100, 2),    # up
                    ("2018-04-05", -1, 0.05, 90, 2)]   # down
        rows.sort()
        rev[cik] = rows
    C.rev = rev
    C.bread = {}
    for e, rows in rev.items():
        avs = [r[0] for r in rows]
        ctot, cdn = array("i", []), array("i", [])
        tt = dn = 0
        for r in rows:
            tt += 1
            dn += 1 if r[1] == -1 else 0
            ctot.append(tt)
            cdn.append(dn)
        C.bread[e] = (avs, ctot, cdn)
    C.late = {}
    for e, rows in rev.items():
        avs = [r[0] for r in rows]
        ctot, clate, cdeep = array("i", []), array("i", []), array("i", [])
        a = b = c = 0
        for r in rows:
            a += 1
            b += 1 if r[3] > 460 else 0
            c += 1 if r[4] >= 6 else 0
            ctot.append(a)
            clate.append(b)
            cdeep.append(c)
        C.late[e] = (avs, ctot, clate, cdeep)

    # event artifact rows (CIK1 keeps an amendment arrival at 2018-04-02)
    events = []
    for cik in ciks:
        events.append((cik, "2018-04-02", "ALIVE_EVIDENCED", 300))
    events += [
        ("CIK0000000001", "2018-03-01", "ALIVE_EVIDENCED", 300),
        ("CIK0000000099", "2018-03-03", "NOT_DEAD_NAME_ALIVE", 300),  # excluded class
        ("CIK0000000001", "2018-09-03", "ALIVE_EVIDENCED", 3),        # excluded bars
    ]
    C.events = events
    C.event_dates = {}
    for cik, fa, _c, _s in events:
        C.event_dates.setdefault(cik, set()).add(fa)

    # share groups: eff -> vintages
    C.share_groups = {}
    C.share_vintages = {}
    for cik in ciks:
        C.share_groups[(cik, "us-gaap:CommonStockSharesOutstanding")] = ["2017-12-31"]
        C.share_vintages[(cik, "us-gaap:CommonStockSharesOutstanding")] = {
            "2017-12-31": [("2018-01-15", 1000.0)]}
    C.share_groups[("CIK0000000001", "us-gaap:CommonStockSharesOutstanding")] = \
        ["2017-12-31", "2018-03-31"]
    C.share_vintages[("CIK0000000001", "us-gaap:CommonStockSharesOutstanding")] = {
        "2017-12-31": [("2018-01-15", 1000.0)],
        "2018-03-31": [("2018-04-02", 800.0), ("2018-04-20", 780.0)]}

    C.grid21 = grid_dates(C, 63, 21)
    C.grid5 = grid_dates(C, 63, 5)
    C.dir_check = {"measured": {"down": 6, "flat": 2, "up": 16},
                   "manifest": {"up": 63342, "flat": 1519910, "down": 84170},
                   "verdict": "FIXTURE"}
    return C


def selfcheck() -> int:
    """Validates on TINY inline synthetic fixtures (no big data reads):
    eleven veto builders, six proposal builders, pinned proposal hashes,
    output schema fields, gate extraction, determinism, hash-mismatch BLOCK."""
    fails = []
    tmp_path = None

    def check(name, cond, extra=""):
        print(f"[selfcheck] {'PASS' if cond else 'FAIL'} {name} {extra}")
        if not cond:
            fails.append(name)

    # 1. eleven veto builders, six proposal builders
    check("eleven_veto_builders", len(VETO_BUILDERS) == 11
          and list(VETO_BUILDERS) == VETO_NAMES, f"n={len(VETO_BUILDERS)}")
    check("six_proposal_builders", len(PROPOSAL_BUILDERS) == 6
          and sorted(PROPOSAL_BUILDERS) == sorted(PROPOSAL_ORDER), f"n={len(PROPOSAL_BUILDERS)}")

    # 2. pinned proposal hashes (small real files)
    ok, hashes = verify_hashes()
    check("proposal_hash_pins", ok,
          json.dumps({k: v.get("verdict") for k, v in hashes.items()}, sort_keys=True))

    # 3. veto builders on fixtures
    C = _synth_ctx()
    t0 = date(2018, 5, 1)
    vals = {vn: VETO_BUILDERS[vn](C, "CIK0000000001", t0) for vn in VETO_NAMES}
    # CIK0000000002 has fixture drift +0.002/bar -> positive 63s momentum
    mom2 = VETO_BUILDERS["momentum_63s"](C, "CIK0000000002", t0)
    check("veto_momentum_finite", isinstance(mom2, float) and mom2 > 0,
          str(mom2))
    check("veto_semivariance_in_01", 0.0 <= (vals["semivariance_share"] or 0.0) <= 1.0,
          str(vals["semivariance_share"]))
    check("veto_vol_finite", isinstance(vals["vol_level"], float) and vals["vol_level"] >= 0.0,
          str(vals["vol_level"]))
    check("veto_wc_stock", abs(vals["wc_stock_intensity"] - 0.3) < 1e-9,
          str(vals["wc_stock_intensity"]))
    check("veto_goodwill", abs(vals["goodwill_bloat"] - 0.1) < 1e-9,
          str(vals["goodwill_bloat"]))
    check("veto_cash", abs(vals["cash_level"] - 0.05) < 1e-9, str(vals["cash_level"]))
    # accrual flow: ((120-100) + (80-70) - (60-50))/1000 = 0.02 (fiscal-matched
    # annual Dec legs: FY2016 current vs FY2015 prior)
    check("veto_f1_accrual", vals["f1_accrual_flow"] is not None
          and abs(vals["f1_accrual_flow"] - 0.02) < 1e-9, str(vals["f1_accrual_flow"]))
    # depletion: (250 - 300 - 50)/1000 = -0.10 (RE prior FY2015 - RE now - cash)
    check("veto_depletion", vals["depletion_interaction"] is not None
          and abs(vals["depletion_interaction"] - -0.10) < 1e-9,
          str(vals["depletion_interaction"]))
    check("veto_sector_form_finite", vals["sector_exposure_form"] is not None,
          str(vals["sector_exposure_form"]))
    # veto 10: most recent in-window own_z stamp 2018-04-03 -> own_z 1.0
    check("veto10_own_z_mean_at_most_recent_stamp",
          vals["own_z_characteristic_form"] is not None
          and abs(vals["own_z_characteristic_form"] - 1.0) < 1e-9,
          str(vals["own_z_characteristic_form"]))
    # veto 11: window (t-800, t] covers all 4 rows, two down (-1,-1) -> 0.5
    check("veto11_breadth_down_share",
          vals["revision_direction_breadth_form"] is not None
          and abs(vals["revision_direction_breadth_form"] - 0.5) < 1e-9,
          str(vals["revision_direction_breadth_form"]))
    # staleness: evaluate before any timing/revision row exists -> both None
    early = date(2018, 1, 5)
    check("veto10_missing_when_no_groups",
          VETO_BUILDERS["own_z_characteristic_form"](C, "CIK0000000001", early) is None)
    check("veto11_missing_when_no_groups",
          VETO_BUILDERS["revision_direction_breadth_form"](C, "CIK0000000001", early) is None)

    # 4. all six builders run on fixtures and produce anchors
    anchors = {}
    for pid in PROPOSAL_ORDER:
        built = PROPOSAL_BUILDERS[pid](C)
        anchors[pid] = built
        a = built.get("anchor") or built.get("anchor_cells")
        check(f"builder_{pid}_nonempty", len(a) > 0, f"n={len(a)}")
    # A4-H1 anchor sign: every fixture entity drifts vs the flat benchmark -> +/-1;
    # the rising entities (even index) must print +1
    a41 = anchors["SFV11-A4-H1"]["anchor"]
    check("a4_h1_anchor_signs_binary", all(v in (1.0, -1.0) for v in a41.values())
          and len(a41) >= 6, f"n={len(a41)}")
    check("a4_h1_rising_entity_positive",
          any(k[0] == "CIK0000000002" and v == 1.0 for k, v in a41.items()))
    # A4-H2 partition semantics: CIK1's 2018-04-02 arrival IS an amendment
    # (prior rows exist) -> anchor; CIK1's 2018-03-01 arrival is first-vintage
    # -> neighbour ONLY (its entry, 6 bars after 2018-03-01, precedes 2018-04-02);
    # CIK2..6's 2018-04-02 arrivals are first-vintage -> neighbour.
    a42 = anchors["SFV11-A4-H2"]["anchor"]
    n42 = anchors["SFV11-A4-H2"]["neighbour"]
    check("a4_h2_anchor_amendment_only",
          len(a42) >= 1 and all(k[1] > date(2018, 4, 2) for k in a42), f"n={len(a42)}")
    check("a4_h2_neighbour_first_vintage",
          any(k[0] == "CIK0000000001" and k[1] < date(2018, 4, 2) for k in n42)
          and all(not (k[0] == "CIK0000000001" and k[1] > date(2018, 4, 2))
                  for k in n42), f"n={len(n42)}")
    # veto rho machinery runs on a fixture anchor
    nov = novelty_block(C, {("CIK0000000001", t0): 1.0, ("CIK0000000002", t0): -1.0,
                            ("CIK0000000001", date(2018, 5, 2)): 1.0,
                            ("CIK0000000002", date(2018, 5, 2)): -1.0})
    check("novelty_block_runs", isinstance(nov, dict) and len(nov["veto_rho"]) == 11)

    # 5. identifiability block runs for every proposal + gate extraction from files
    for pid in PROPOSAL_ORDER:
        ib = identifiability_block(C, pid, anchors[pid])
        check(f"identifiability_{pid}", ib["gate_value"] == GATES[pid]
              and ib["gate_declared_text"] != "" and ib["gate_number_found_in_text"],
              f"gate={ib['gate_value']} text_found={ib.get('gate_number_found_in_text')}")

    # 6. feasibility block runs for every proposal
    for pid in PROPOSAL_ORDER:
        fb = feasibility_block(C, pid, anchors[pid])
        check(f"feasibility_{pid}", fb["verdict"].startswith(("RUNNABLE", "INFEASIBLE")),
              fb["verdict"])

    # 7. output schema fields exist
    sk = build_audit_skeleton("FIXED-BUILT-AT", hashes)
    check("schema_fields_present", all(k in sk for k in REQUIRED_SCHEMA_FIELDS),
          str([k for k in REQUIRED_SCHEMA_FIELDS if k not in sk]))

    # 8. determinism: identical skeleton bytes across two builds
    sk2 = build_audit_skeleton("FIXED-BUILT-AT", hashes)
    check("deterministic_skeleton_bytes",
          json.dumps(sk, sort_keys=True) == json.dumps(sk2, sort_keys=True))

    # 9. hash mismatch => verification fails (tampered pin table simulation)
    global HASHES_FILE
    real = HASHES_FILE
    try:
        import tempfile
        tampered = json.loads(real.read_text())
        first = sorted(tampered["hashes"])[0]
        tampered["hashes"][first] = "0" * 64
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(tampered, fh)
            tmp_path = fh.name
        HASHES_FILE = Path(tmp_path)
        ok2, _h2 = verify_hashes()
        check("hash_mismatch_detected", ok2 is False)
    finally:
        HASHES_FILE = real
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    print("[selfcheck] " + ("ALL PASS" if not fails else f"FAILURES: {fails}"))
    return 0 if not fails else 1


def main(built_at_utc: str = None) -> int:
    if built_at_utc is not None:
        return run_full(built_at_utc)
    if "--selfcheck" in sys.argv[1:]:
        return selfcheck()
    built_at_utc = os.environ.get("D2_BUILT_AT")
    if built_at_utc is None:
        pos = [a for a in sys.argv[1:] if not a.startswith("--")]
        if pos:
            built_at_utc = pos[0]
        else:
            import time
            built_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return run_full(built_at_utc)


if __name__ == "__main__":
    sys.exit(main())
