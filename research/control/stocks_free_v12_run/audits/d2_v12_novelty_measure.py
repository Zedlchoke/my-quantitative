"""PLAN_stocks_v12 D2 novelty + control-identifiability + A9-F-style feasibility
(D2 measurement lane, cycle STOCKS-FREE-V12).

ADAPTED FROM: research/assets/stocks/d2_v11_novelty_measure.py at terminal
commit 9d3a0612f1e35430a300ba02c1b4c28bc748d4b0 (V11-cycle tooling, read-only
reference). Disclosure: this is a NEW cycle-specific V12 module; the V11
skeleton (midrank Spearman, veto-engine forms, load_context shape, verdict
discipline, determinism contract) is carried; the veto set grows ELEVEN ->
THIRTEEN (adds the V11 amendment cadence-latency form and the filing-event
reaction momentum_63s shadow), and the six proposal builders are rewritten to
the V12 d2_predeclarations. Feature/RANK ARITHMETIC ONLY — zero PnL, no
returns, no selection, no scoring.

For each of the SIX committed V12 D1 proposals (SFV12-A4-H1/H2, SFV12-A5-H1/H2,
SFV12-A6-H1/H2) the DECLARED conditioning exposure is computed exactly as its
d2_predeclarations / exposure_definition state (recorded house conventions
listed under conventions_applied). Measured per proposal:

  (a) novelty: pooled Spearman (midrank ties) of the declared exposure vs each
      of the THIRTEEN veto entries on common (entity, decision-instant) pairs;
      bar pooled |rho| <= 0.20 per entry; fail-closed (a null entry fails).
  (b) control identifiability: anchor-vs-own-control rho (A4: per-date and
      pooled; A5: anchor leg-weight vs sham leg-weight; A6: hash-order
      permutation placebo) with the declared gates (A4 R1 0.30 / self-
      subsumption 0.98; A5 per-date 0.30 on >= 90% dates / self-subsumption
      0.98; A6 self-subsumption 0.98), plus the declared cross-anchor checks
      (A4-H1 vs A4-H2 mutual-distinctness rho, 0.98 kill declared binding).
  (c) feasibility: funded-clock resolution (incl. the A6 V12-S3 adjudication
      evidence measured in-module), decision counts per fold vs the >= 30
      overall / >= 5 per fold floors, warmup coverage under max_age 800,
      control runnability counts (a control that cannot run = DESIGN FAILURE,
      not a pass), and turnover/cost-ceiling exposure notes vs the frozen band
      ladder 10/15/25 bps (stress x2) — A9-F pre-measure arithmetic only.

Determinism: the ONLY wall-clock input is built_at_utc, passed as argv[1]
(two passes are byte-identical; sort_keys=True; every cross-entity sequence
iterated in sorted order; the A4 controls use numpy PCG64 with the seeds
FROZEN IN THE PROPOSALS — 20260908 H1 / 20260909 H2 — redrawn per decision
date in session-index order). No band computation, no returns, no outcome
files. Universe: entity-decision pairs where the proposal exposure is defined
on the bookable pool (ALIVE_EVIDENCED + DEAD_EVIDENCED cohort legs), with the
inherited 63-bar pre-check floor for the grid/S3 families.

Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python ONLY.
Usage: d2_v12_novelty_measure.py <built_at_utc> <out_path> [--selfcheck]
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from array import array
from bisect import bisect_left, bisect_right
from datetime import date, timedelta
from pathlib import Path

# --------------- machine-local path constants (V11 skeleton, paths carried) -
V12 = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v12/integration")
V10 = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v10/integration")
V9 = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/integration")
PRICES = V9 / ".staging_prices_v9/eod"
BENCH = V9 / ".staging_prices_v9/benchmarks"
TIMING = V10 / ".staging_sec_v10/v10_timing_observables.jsonl"
REVISION = V10 / ".staging_sec_v10/v10_revision_observables.jsonl"
PANEL = V9 / ".staging_sec_v9/multivintage_panel.jsonl"
COHORT = V10 / "research/control/stocks_free_v9_run/cohort_v9.json"
P0D = V9 / "research/control/stocks_free_v9_run/p0d_v9_integrity_scan.json"
V10_P0_MANIFEST = V10 / "research/control/stocks_free_v10_run/p0_v10_observable_manifest.json"
P2 = V12 / "research/control/stocks_free_v12_run/p2_v12_coverage_first.json"
P3 = V12 / "research/control/stocks_free_v12_run/p3_v12_invariants_freeze.json"
P0_CENSUS = V12 / "research/control/stocks_free_v12_run/p0_v12_structure_death_census.json"
HASH_FILES = [
    V12 / "research/control/stocks_free_v12_run/d1_a4_proposal_hashes.json",
    V12 / "research/control/stocks_free_v12_run/d1_a5_proposal_hashes.json",
    V12 / "research/control/stocks_free_v12_run/d1_a6_proposal_hashes.json",
]
PROPOSALS_DIR = V12 / "research/control/stocks_free_v12_run/proposals"

STALE_DAYS = 800
CYCLE = "STOCKS-FREE-V12"
WAVE_SHA = "b3524024f6e3d4c3ca8c5729889c80f6adbc3aa5"
BASE_SHA = "ca5388dc8d971cd9242ce5082d81e8205e65b2b8"
NOVELTY_BAR = 0.20
SELF_SUBSUMPTION_RHO = 0.98
A4_R1_DATE_RHO = 0.30
A4_DATE_PASS_SHARE = 0.90
A4_TERCILE_MIN = 6
A4_R3_COVERAGE = 0.60
A4_R5_SECTOR_PART = 0.60
MIN_GROUPS_Q = 4
MIN_SECTOR_NAMES = 6
PCG_SEED_H1 = 20260908   # frozen in SFV12-A4-H1 frozen_thresholds
PCG_SEED_H2 = 20260909   # frozen in SFV12-A4-H2 frozen_thresholds
GRID_START = 63
GRID_STEP = 21
S3_MIN_STRICT_BARS = 5   # A6 decision threshold (census 1,546,323 groups at >=5 bars)
A5_GAP_CUT = 10          # ORDERLY <= 10 / GAPPED >= 11 (SFV12-A5-H1 frozen cut)
A5_WINDOW = 20           # 20-bar windows (both A5 families)
A5_PRINT_CUT = 15        # printed_bars >= 15 ORDERLY-REORG (SFV12-A5-H2 frozen cut)
A5_LIQ_FLOOR = 10_000    # post-window median dollar-volume floor (SFV12-A5-H2)
FLOOR_OVERALL, FLOOR_PER_FOLD = 30, 5
VACUITY_MIN_CLASS_EVENTS = 30
ANNUAL_SESSIONS = 252
SECTOR_ETFS = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]

# THIRTEEN-entry veto set (P3 v12_additions.forbidden_inventory verbatim split)
VETO_NAMES = [
    "momentum_63s",                        # 1 momentum (V2; V11-measured blocker)
    "semivariance_share",                  # 2
    "vol_level",                           # 3
    "wc_stock_intensity",                  # 4
    "goodwill_bloat",                      # 5
    "f1_accrual_flow",                     # 6
    "depletion_interaction",               # 7
    "cash_level",                          # 8
    "sector_exposure_form",                # 9
    "own_z_characteristic_form",           # 10 V10 deseasonalized-timing own_z
    "revision_direction_breadth_form",     # 11 V10 revision direction/breadth
    "v11_cadence_latency_form",            # 12 V11 amendment cadence-latency
    "filing_event_reaction_shadow",        # 13 filing-event reaction (momentum_63s shadow)
]
REV_DIR_ENCODING = {1: "up", 0: "flat", -1: "down"}
A5_LATE_IARR_CUT = 460    # veto 12: inter_arrival_days > 460 (V11 A5-H1 anchor form)
REACTION_STALE_DAYS = 800  # veto 13 state staleness (uniform bound)

# accounting veto fields (V10 form, unchanged) + A6 panel-characteristic fields
NEEDED_FIELDS = [
    "us-gaap:AssetsCurrent", "us-gaap:LiabilitiesCurrent",
    "us-gaap:Goodwill", "us-gaap:Assets",
    "us-gaap:CashAndCashEquivalentsAtCarryingValue",
    "us-gaap:RetainedEarningsAccumulatedDeficit",
    "us-gaap:AccountsReceivableNetCurrent", "us-gaap:InventoryNet",
    "us-gaap:AccountsPayableCurrent",
    # A6 adjudication + exposure fields (panel-characteristic substrate)
    "us-gaap:Revenues",
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap:CostOfGoodsAndServicesSold",
    "us-gaap:CostOfRevenue",
]
REV_PRIORITY = ["us-gaap:Revenues", "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"]
COGS_PRIORITY = ["us-gaap:CostOfGoodsAndServicesSold", "us-gaap:CostOfRevenue"]

FOLDS_FALLBACK = [
    {"fold_id": "S0_FOLD_1", "start": "2018-04-04", "end": "2020-09-01"},
    {"fold_id": "S0_FOLD_2", "start": "2020-09-10", "end": "2023-02-09"},
    {"fold_id": "S0_FOLD_3", "start": "2023-02-17", "end": "2025-07-24"},
]

PROPOSAL_FILES = {
    "SFV12-A4-H1": "SFV12-A4-H1.json",
    "SFV12-A4-H2": "SFV12-A4-H2.json",
    "SFV12-A5-H1": "SFV12-A5-H1.json",
    "SFV12-A5-H2": "SFV12-A5-H2.json",
    "SFV12-A6-H1": "SFV12-A6-H1.json",
    "SFV12-A6-H2": "SFV12-A6-H2.json",
}
PROPOSAL_ORDER = list(PROPOSAL_FILES.keys())
# declared warmup decisions (proposal warmup_decisions)
WARMUP = {"SFV12-A4-H1": 0, "SFV12-A4-H2": 0,
          "SFV12-A5-H1": 0, "SFV12-A5-H2": 0,
          "SFV12-A6-H1": 3, "SFV12-A6-H2": 3}
# frozen falsification rule carried verbatim (P3 lane mandates): control
# same-sign >= 0.5x anchor kills at scoring; D2 measures identifiability only.


def dd(s: str) -> date:
    return date.fromisoformat(s)


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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


def tercile_counts(vals):
    """Bottom/Top tercile populations under the declared tie rule (boundary
    ties join the lower = long tercile; deterministic midrank thresholds)."""
    n = len(vals)
    if n < 3:
        return 0, 0, 0
    r = midrank(vals)
    b1 = n / 3.0
    b2 = 2.0 * n / 3.0
    bot = sum(1 for x in r if x <= b1)
    top = sum(1 for x in r if x > b2)
    return bot, top, n - bot - top


# ===========================================================================
# context loading (heavy path — run under the machine-wide heavy lock)
# ===========================================================================
def load_context():
    import numpy as np  # only the heavy path needs PCG64

    class Ctx:
        pass

    C = Ctx()
    C.np = np

    # ---- input integrity pins (P-1: bytes verified before any measurement) --
    pins = {}
    pins["panel"] = file_sha256(PANEL)
    pins["cohort_v9"] = file_sha256(COHORT)
    pins["v10_timing_observables"] = file_sha256(TIMING)
    pins["v10_revision_observables"] = file_sha256(REVISION)
    pins["p0d_integrity_scan"] = file_sha256(P0D)
    pins["p0_v12_census"] = file_sha256(P0_CENSUS)
    C.pins = {
        "panel": {"sha256": pins["panel"],
                  "expected": "67591464ee49acc159886143a379bda5890b1df602818b600d7938df92af1447"},
        "cohort_v9": {"sha256": pins["cohort_v9"],
                      "expected": "6a95401ff84bff2144ac3c0b9426a6fa86daf3dde8d478195666249e3fa2aa62"},
        "v10_timing_observables": {"sha256": pins["v10_timing_observables"],
                                   "expected": "b1477ea39b8b794b7f32162cb349ff53fdd1a37b9a64d0ee20e77412ae802337"},
        "v10_revision_observables": {"sha256": pins["v10_revision_observables"],
                                     "expected": "7110cbf010ae6d3f414a1a45eec1e504aff5e94464755991e98605e4795657c2"},
    }
    C.pin_verdicts = {k: ("MATCH" if v["sha256"] == v["expected"] else "MISMATCH")
                      for k, v in C.pins.items()}
    if any(v != "MATCH" for v in C.pin_verdicts.values()):
        sys.stderr.write(f"BLOCKED: staged-input pin mismatch {C.pin_verdicts}\n")
        return C, 2

    # ---- cohort + p0d verdicts -------------------------------------------
    cohort = json.loads(COHORT.read_text())
    C.bookable = {}
    for cls in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED"):
        for m in cohort["members"][cls]:
            C.bookable[m["cik"]] = {"sector": m.get("sector", ""),
                                    "ticker": m.get("ticker", ""),
                                    "cls": cls}
    p0d = json.loads(P0D.read_text())
    C.p0d = {}
    for cik, rec in p0d["dead_verdicts"].items():
        if cik in C.bookable:
            C.p0d[cik] = {"verdict": rec["verdict"],
                          "death_date": rec["death_filing_date"]}
    C.verdict_counts = {}
    for rec in C.p0d.values():
        C.verdict_counts[rec["verdict"]] = C.verdict_counts.get(rec["verdict"], 0) + 1

    # ---- frozen folds ------------------------------------------------------
    try:
        p3 = json.loads(P3.read_text())
        folds = p3["carried_payload"]["folds"]
    except Exception:
        folds = FOLDS_FALLBACK
    C.folds = folds

    # ---- global trading calendar from SPY ----------------------------------
    spy = json.loads((BENCH / "SPY.json").read_text())
    sessions = [dd(r["date"]) for r in sorted(spy, key=lambda r: r["date"])]
    C.sessions = sessions
    C.sess_idx = {d: i for i, d in enumerate(sessions)}

    # ---- priced bookable entities (files kept at ANY length: the sham
    # pairing needs first_bar_date of every priced entity, census semantics) --
    print("[d2] loading price series...", flush=True)
    series = {}
    for p in sorted(PRICES.glob("CIK*.json")):
        cik = p.name.split("__")[0]
        if cik not in C.bookable:
            continue
        try:
            arr = json.loads(p.read_text())
        except Exception:
            continue
        arr = [r for r in arr if r.get("close") is not None]
        if not arr:
            continue
        arr.sort(key=lambda r: r["date"])
        series[cik] = {
            "dates": [dd(r["date"]) for r in arr],
            "close": [r["close"] for r in arr],
            "adj": [r.get("adjusted_close") for r in arr],
            "vol": [r.get("volume", 0) for r in arr],
        }
    C.series = series
    C.priced_counts = {
        "priced_files_bookable": len(series),
        "ge63_bars": sum(1 for s in series.values() if len(s["dates"]) >= 63),
    }

    # ---- prefix arrays over ADJ log returns (63-bar veto family) -----------
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

    # ---- panel: accounting veto fields + A6 fields + per-entity eff groups --
    print("[d2] streaming panel for veto + A6 fields...", flush=True)
    fields = {}          # (e, f) -> sorted [(avail, eff, v)]
    eff_groups = {}      # (e, f) -> {eff: sorted [(avail, v)]}
    panel_field_stats = {}  # f -> {"rows": n, "entities_bookable": n}
    want = set(NEEDED_FIELDS)
    with open(PANEL, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            e, f = r["e"], r["f"]
            if e in C.bookable and f in want and isinstance(r["v"], (int, float)):
                av, eff, v = r["avail"], r["eff"], float(r["v"])
                fields.setdefault((e, f), []).append((av, eff, v))
                eff_groups.setdefault((e, f), {}).setdefault(eff, []).append((av, v))
                st = panel_field_stats.setdefault(f, {"rows": 0, "entities": set()})
                st["rows"] += 1
                st["entities"].add(e)
    for k in fields:
        fields[k].sort()
    C.fields = fields
    C.eff_groups = {}
    for (e, f), effs in eff_groups.items():
        for eff in effs:
            effs[eff].sort()
        C.eff_groups[(e, f)] = dict(sorted(effs.items()))
    C.panel_field_stats = {f: {"rows_bookable": st["rows"],
                               "entities_bookable": len(st["entities"])}
                           for f, st in sorted(panel_field_stats.items())}

    # ---- timing layer: own_z rows + filer-event dates -----------------------
    print("[d2] loading timing layer (own_z + filer events)...", flush=True)
    ownz = {}
    event_dates = {}
    with open(TIMING, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            e = r["e"]
            if e not in C.bookable:
                continue
            fa = r["first_avail"]
            event_dates.setdefault(e, set()).add(fa)
            oz = r["own_z"]
            if oz is not None:
                ownz.setdefault(e, []).append((r["observable_available_at"], float(oz)))
    for e in ownz:
        ownz[e].sort()
    C.ownz = {e: ([x[0] for x in lst], array("d", [x[1] for x in lst]))
              for e, lst in ownz.items()}
    C.event_dates = {e: sorted(v) for e, v in event_dates.items()}
    C.filer_event_count = sum(len(v) for v in C.event_dates.values())

    # ---- revision layer: depth>=2 groups (A4 anchors, vetoes 11/12, A6) -----
    print("[d2] loading revision layer...", flush=True)
    rev = {}
    dir_counts = {1: 0, 0: 0, -1: 0}
    with open(REVISION, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            e = r["e"]
            d = r["rev_dir"]
            if d in dir_counts:
                dir_counts[d] += 1
            if e not in C.bookable:
                continue
            ia = r["inter_arrival_days"]
            rev.setdefault(e, []).append(
                (r["last_avail"], r["depth"],
                 ia if ia is not None else -1,   # None-safe sort key; -1 never > 460
                 d))
    for e in rev:
        rev[e].sort()
    C.rev = rev
    # per-entity prefix arrays: total / down / late(iarr>460) / deep(depth>=6) / sum(depth)
    C.bread, C.late, C.deep, C.dsum = {}, {}, {}, {}
    for e, rows in rev.items():
        n = len(rows)
        avs = [r[0] for r in rows]
        ctot = array("i", [0] * n); cdn = array("i", [0] * n)
        t = dn = 0
        for i, r in enumerate(rows):
            t += 1
            dn += 1 if r[3] == -1 else 0
            ctot[i] = t; cdn[i] = dn
        C.bread[e] = (avs, ctot, cdn)
        clate = array("i", [0] * n); cdeep = array("i", [0] * n); csum = array("l", [0] * n)
        la = de = sm = 0
        for i, r in enumerate(rows):
            la += 1 if r[2] > A5_LATE_IARR_CUT else 0
            de += 1 if r[1] >= 6 else 0
            sm += r[1]
            clate[i] = la; cdeep[i] = de; csum[i] = sm
        C.late[e] = (avs, ctot, clate)
        C.deep[e] = (avs, ctot, cdeep)
        C.dsum[e] = (avs, csum)
    # distinct last_avail dates (A6 S3 instants)
    C.rev_avails = {e: sorted({r[0] for r in rows}) for e, rows in rev.items()}

    # ---- rev_dir encoding fail-closed check vs the V10 P0 manifest ----------
    manifest = json.loads(V10_P0_MANIFEST.read_text())
    md = manifest["census"]["revision"]["dir_counts"]
    expected = {1: md["up"], 0: md["flat"], -1: md["down"]}
    C.dir_check = {"measured": {REV_DIR_ENCODING[k]: v for k, v in sorted(dir_counts.items())},
                   "manifest": md, "verdict": "MATCH" if dir_counts == expected else "MISMATCH"}
    if dir_counts != expected:
        sys.stderr.write("BLOCKED: rev_dir encoding check FAILED\n")
        return C, 2

    # ---- decision grids -----------------------------------------------------
    C.grid21 = grid_dates(C, GRID_START, GRID_STEP)
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


def fold_of(C, d):
    for f in C.folds:
        if dd(f["start"]) <= d <= dd(f["end"]):
            return f
    return None


# ===========================================================================
# VETO ENGINE — THIRTEEN entries; 1-11 in the inherited V10/V11 form
# (verbatim adaptation), 12 = V11 amendment cadence-latency form, 13 = the
# filing-event reaction momentum_63s shadow. Each builder: (C, e, t) -> value
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
    lo, hi = i - 62, i
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
    """Veto 10 — V10 deseasonalized-timing own_z characteristic form (V11 form
    unchanged): most recent in-window (<=800d stale) timing-layer group own_z;
    MEAN over the qualifying groups sharing that most-recent stamp."""
    rec = C.ownz.get(e)
    if rec is None:
        return None
    avs, zs = rec
    lo = bisect_left(avs, (t - timedelta(days=STALE_DAYS)).isoformat())
    hi = bisect_right(avs, t.isoformat())
    if hi <= lo:
        return None
    j = hi - 1
    stamp = avs[j]
    tot, n = 0.0, 0
    while j >= lo and avs[j] == stamp:
        tot += zs[j]
        n += 1
        j -= 1
    return tot / n


def veto_breadth(C, e, t):
    """Veto 11 — V10 revision direction/breadth form (V11 form unchanged):
    share of in-window depth>=2 revision-layer groups whose last-vintage value
    moved DOWN (rev_dir == -1)."""
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


def veto_cadence(C, e, t):
    """Veto 12 — V11 amendment cadence-latency form: share of in-window
    depth>=2 revision-layer groups (last_avail <= t, > t-800d) with
    inter_arrival_days > 460 (the V11 A5-H1 anchor statistic, vetoed
    FALSIFIED_BY_CONTROL cluster #13)."""
    rec = C.late.get(e)
    if rec is None:
        return None
    avs, ctot, clate = rec
    lo = bisect_right(avs, (t - timedelta(days=STALE_DAYS)).isoformat())
    hi = bisect_right(avs, t.isoformat())
    if hi == 0:
        return None
    tot = ctot[hi - 1] - (ctot[lo - 1] if lo > 0 else 0)
    if tot <= 0:
        return None
    lt = clate[hi - 1] - (clate[lo - 1] if lo > 0 else 0)
    return lt / tot


_reaction_cache = {}


def residual_reaction(C, e, arr, bench_tkr):
    """5-bar STRICT_NEXT_BAR benchmark-residual initial reaction (V11 A4 arm
    arithmetic, verbatim). Returns (sign, entry_date, reason)."""
    s = C.series.get(e)
    if s is None:
        return None, None, "no_price_series"
    i0 = bisect_right(s["dates"], arr) - 1
    if i0 < 0:
        return None, None, "no_base_bar"
    if i0 + 20 >= len(s["dates"]):
        return None, None, "fewer_than_20_strict_bars"
    ben = C.bench.get(bench_tkr)
    if ben is None:
        return None, None, "bench_missing"
    bc = []
    for k in range(0, 6):
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


def veto_filing_reaction(C, e, t):
    """Veto 13 — filing-event reaction event-time space, operationalized as the
    momentum_63s-shaped reaction shadow that V11 D2 measured rho-blocked
    (0.219/0.2192): the sign of the 5-bar SPY-residual initial reaction at the
    entity's most recent evidenced filer-event arrival with arrival < t and
    t - arrival <= 800d; None if no qualifying arrival or the reaction
    abstained-with-reason (counted against measurement)."""
    arrs = C.event_dates.get(e)
    if not arrs:
        return None
    hi = bisect_left(arrs, t.isoformat())  # arrivals strictly < t
    if hi == 0:
        return None
    lo = bisect_left(arrs, (t - timedelta(days=REACTION_STALE_DAYS)).isoformat())
    if hi <= lo:
        return None
    a = arrs[hi - 1]
    key = (e, a)
    if key not in _reaction_cache:
        sign, _entry, _why = residual_reaction(C, e, dd(a), "SPY")
        _reaction_cache[key] = sign
    return _reaction_cache[key]


def _bench_series(C):
    if not hasattr(C, "bench"):
        C.bench = {}
        for tkr in ["SPY"] + SECTOR_ETFS:
            p = BENCH / f"{tkr}.json"
            if not p.exists():
                continue
            arr = json.loads(p.read_text())
            C.bench[tkr] = {dd(r["date"]): r["close"] for r in arr
                            if r.get("close") is not None}
    return C.bench


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
    "v11_cadence_latency_form": lambda C, e, t: veto_cadence(C, e, t),
    "filing_event_reaction_shadow": lambda C, e, t: veto_filing_reaction(C, e, t),
}


# ===========================================================================
# PROPOSAL EXPOSURE BUILDERS (six) — V12 declared formulas
# ===========================================================================
def a4_walk(C, e, t):
    """One window walk per (entity, decision) pair over Q(e,t) = depth>=2
    revision-layer groups with last_avail < t and t - last_avail <= 800d.
    Returns dict with |Q|, deep_count(>=6), sum depth, max depth, median depth;
    None if |Q| == 0."""
    rec = C.deep.get(e)
    if rec is None:
        return None
    avs = rec[0]
    hi = bisect_left(avs, t.isoformat())               # last_avail < t (strict)
    lo = bisect_left(avs, (t - timedelta(days=STALE_DAYS)).isoformat())  # >= t-800d
    n = hi - lo
    if n <= 0:
        return None
    rows = C.rev[e]
    deep = sum_d = 0
    max_d = 0
    vals = []
    for i in range(lo, hi):
        d = rows[i][1]
        deep += 1 if d >= 6 else 0
        sum_d += d
        if d > max_d:
            max_d = d
        vals.append(d)
    vals.sort()
    med = vals[n // 2] if n % 2 == 1 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0
    return {"n": n, "deep": deep, "sum": sum_d, "max": max_d, "median": med}


def build_a4(C, hid, seed):
    """SFV12-A4-H1 (DEPTH-STRAIN deep_share) / SFV12-A4-H2 (CONCENTRATION-SHAPE
    max/sum excess concentration). Grid 63+21k per fold; measured universe =
    bookable-pool names with >= 63 bars through t; anchor defined iff |Q| >= 4.
    Control = within-sector marginal-preserving permutation of the anchor
    values (numpy PCG64 seed frozen in the proposal, applied to the CIK-sorted
    index vector, redrawn per decision date in session-index order)."""
    anchor, control = {}, {}
    win = {}  # (e,t) -> walk dict (for neighbour/cross stats)
    measured_univ = {}   # t -> measured universe size (>= 63 bars)
    sect_ok_count = {}   # t -> measured-universe members in >= 6-name sectors
    r4_pos_top = {}      # t -> names in top tercile with exposure > 0
    r2_ctrl = {}         # t -> (bot, top) control tercile counts
    dates = grid_dates_flat(C, C.grid21)
    # first pass: anchors + walks
    per_date = {}
    for t in dates:
        names = []
        for e in sorted(C.series):
            if not has_bars(C, e, t):
                continue
            names.append(e)
        measured_univ[t] = len(names)
        for e in names:
            w = a4_walk(C, e, t)
            if w is None or w["n"] < MIN_GROUPS_Q:
                continue
            win[(e, t)] = w
            if hid == "SFV12-A4-H1":
                v = w["deep"] / w["n"]
            else:
                denom = w["sum"] - 2 * w["n"]
                v = 0.0 if denom <= 0 else (w["max"] - 2) / denom
            anchor[(e, t)] = v
            per_date.setdefault(t, []).append(e)
        # sector participation (R5): sectors with >= MIN_SECTOR_NAMES
        # defined-exposure names
        sec_counts = {}
        for e in per_date.get(t, []):
            sec_counts[C.bookable[e]["sector"]] = sec_counts.get(
                C.bookable[e]["sector"], 0) + 1
        ok_sectors = {s for s, c in sec_counts.items() if c >= MIN_SECTOR_NAMES}
        sect_ok_count[t] = sum(sec_counts.get(s, 0) for s in ok_sectors)
    # second pass: controls, terciles, R4 (dates in session order)
    rng = C.np.random.Generator(C.np.random.PCG64(seed))
    for t in dates:
        names = sorted(per_date.get(t, []))
        if not names:
            continue
        # within-sector CIK-sorted permutation (sector order sorted)
        by_sec = {}
        for e in names:
            by_sec.setdefault(C.bookable[e]["sector"], []).append(e)
        for sec in sorted(by_sec):
            lst = by_sec[sec]
            m = len(lst)
            if m == 1:
                control[(lst[0], t)] = anchor[(lst[0], t)]
                continue
            vals = [anchor[(e, t)] for e in lst]
            perm = rng.permutation(m)
            for i, e in enumerate(lst):
                control[(e, t)] = vals[int(perm[i])]
        avals = [anchor[(e, t)] for e in names]
        bot, top, _mid = tercile_counts(avals)
        top_names = sorted(names, key=lambda e: anchor[(e, t)])[-top:] if top else []
        r4_pos_top[t] = sum(1 for e in top_names if anchor[(e, t)] > 0)
        cvals = [control[(e, t)] for e in names]
        cbot, ctop, _ = tercile_counts(cvals)
        r2_ctrl[t] = (cbot, ctop)
    return {"anchor": anchor, "control": control, "walk": win,
            "measured_universe": measured_univ, "sect_ok_count": sect_ok_count,
            "r4_pos_top": r4_pos_top, "r2_ctrl": r2_ctrl,
            "grid_dates": {fid: [d.isoformat() for d in C.grid21[fid]]
                           for fid in sorted(C.grid21)}}


def _pair_sham_pairs(C):
    """Deterministic census sham pairing (verbatim rule): DEAD_EVIDENCED priced
    entities with evidenced death date matched to ALIVE_EVIDENCED priced hosts
    by cohort sector tag; within sector both sides CIK-sorted,
    dead[i] -> alive[i mod n_alive]. Returns (pairs_with_multiplicity,
    unmapped_count, unique_hosts_used). Census reference: 1098 mapped pairs,
    671 UNMAPPED, 391 hosts receiving >= 1 pair (of 409 mapped priced alive)."""
    dead_by_sec, alive_by_sec = {}, {}
    for e in sorted(C.bookable):
        info = C.bookable[e]
        if e not in C.series:
            continue
        if info["cls"] == "DEAD_EVIDENCED" and e in C.p0d:
            dead_by_sec.setdefault(info["sector"], []).append(e)
        elif info["cls"] == "ALIVE_EVIDENCED":
            alive_by_sec.setdefault(info["sector"], []).append(e)
    pairs = []
    for sec in sorted(dead_by_sec):
        deads = dead_by_sec[sec]
        alives = alive_by_sec.get(sec, [])
        if not alives:
            continue
        n = len(alives)
        for i, d in enumerate(deads):
            pairs.append((d, alives[i % n], sec))
    unmapped = sum(len(v) for s, v in sorted(dead_by_sec.items())
                   if not alive_by_sec.get(s))
    return pairs, unmapped, len({h for _d, h, _s in pairs})


def build_a5_h1(C):
    """SFV12-A5-H1 FINALQ-CONTAGION. Trigger set = DEAD_PRICE_CONFIRMED (priced,
    evidenced death date). Conditioner (declared exposure ii): gap_days class
    ORDERLY=+1 / GAPPED=-1 at (trigger, arrival). Declared exposure (i):
    per-entity net leg weight of the sector-residual peer book at event dates
    (dedup by (sector, class, date); equal-weight basket of mapped
    ALIVE_EVIDENCED priced peers with >= 63 bars through the event date)."""
    triggers = {}
    events = []           # (T, sector, class, trigger)
    excl = {"no_price_series": 0, "no_bar_within_800d": 0, "unmapped_sector": 0}
    for e in sorted(C.bookable):
        rec = C.p0d.get(e)
        if rec is None or rec["verdict"] != "DEAD_PRICE_CONFIRMED":
            continue
        s = C.series.get(e)
        if s is None:
            excl["no_price_series"] += 1
            continue
        T = dd(rec["death_date"])
        i = bisect_right(s["dates"], T) - 1
        if i < 0 or (T - s["dates"][i]).days > STALE_DAYS:
            excl["no_bar_within_800d"] += 1
            continue
        gap = (T - s["dates"][i]).days
        if gap <= A5_GAP_CUT:
            cls = 1
        else:
            cls = -1
        sec = C.bookable[e]["sector"]
        if not sec:
            excl["unmapped_sector"] += 1
            continue
        triggers[e] = {"T": T.isoformat(), "gap_days": gap, "class": cls}
        events.append((T, sec, cls, e))
    # conditioner vector (ii)
    conditioner = {(e, dd(v["T"])): float(v["class"]) for e, v in triggers.items()}
    # leg-weight vectors: full anchor + matched-subset anchor + sham
    pairs, unmapped, hosts = _pair_sham_pairs(C)
    matched_dead = {d for d, _h, _s in pairs}
    pair_of = {d: (h, sec) for d, h, sec in pairs}

    def baskets_at(date_t, sec, exclude):
        out = []
        for p in sorted(C.bookable):
            if C.bookable[p]["cls"] != "ALIVE_EVIDENCED" or C.bookable[p]["sector"] != sec:
                continue
            if p == exclude or not has_bars(C, p, date_t):
                continue
            out.append(p)
        return out

    def weights_from(evt_list):
        # evt_list: (date, sector, class, name); dedup (sector, class, date);
        # the event's own name is excluded from its basket (no-op for anchor
        # events whose name is dead-class; excludes the host for sham events)
        groups = {}
        for T, sec, cls, name in evt_list:
            groups.setdefault((sec, cls, T), []).append(name)
        w = {}
        n_ev = 0
        for (sec, cls, T), names in sorted(groups.items(),
                                           key=lambda kv: (kv[0][2], kv[0][0], kv[0][1])):
            bsk = [p for p in baskets_at(T, sec, exclude=None) if p not in set(names)]
            n_ev += 1
            if not bsk:
                continue
            wgt = float(cls) / len(bsk)
            for p in bsk:
                w[(p, T)] = w.get((p, T), 0.0) + wgt
        return w, n_ev

    anchor_w, ev_full = weights_from(events)
    events_matched = [ev for ev in events if ev[3] in matched_dead]
    anchor_m_w, ev_matched = weights_from(events_matched)
    # sham events: host inherits the dead's class at the sham date
    sham_events = []
    sham_stats = {"pairs_total": len(pairs), "pairs_class_defined": 0,
                  "sham_basket_empty": 0}
    for d, h, sec in pairs:
        rec = triggers.get(d)
        if rec is None:
            continue
        sham_stats["pairs_class_defined"] += 1
        hs = C.series[h]
        off = (dd(rec["T"]) - hs["dates"][0]).days
        sham_date = hs["dates"][0] + timedelta(days=off)
        sham_events.append((sham_date, sec, rec["class"], h))
    sham_w, ev_sham = weights_from(sham_events)
    sham_in_fold = sum(1 for T, *_ in sham_events if fold_of(C, T) is not None)
    anchor_m_in_fold = sum(1 for T, *_ in events_matched if fold_of(C, T) is not None)
    # per-fold trigger counts + class counts (full trigger set and matched subset)
    folds_ct, folds_ct_m = {}, {}
    class_ct = {1: 0, -1: 0}
    class_ct_m = {1: 0, -1: 0}
    for T, sec, cls, e in events:
        f = fold_of(C, T)
        if f:
            folds_ct[f["fold_id"]] = folds_ct.get(f["fold_id"], 0) + 1
        class_ct[cls] += 1
    for T, sec, cls, e in events_matched:
        f = fold_of(C, T)
        if f:
            folds_ct_m[f["fold_id"]] = folds_ct_m.get(f["fold_id"], 0) + 1
        class_ct_m[cls] += 1
    return {"conditioner": conditioner, "anchor_w": anchor_w,
            "anchor_matched_w": anchor_m_w, "sham_w": sham_w,
            "triggers": {e: v for e, v in sorted(triggers.items())},
            "excluded": excl, "sham_stats": {
                **sham_stats, "hosts": hosts,
                "sham_events": ev_sham, "sham_in_fold": sham_in_fold,
                "matched_events": ev_matched, "matched_in_fold": anchor_m_in_fold,
                "unmapped_no_host": unmapped,
                "census_reference": {"mapped_pairs": 1098, "hosts": 391,
                                     "unmapped": 671}},
            "matched_pair_verdict": (
                "MATCH" if (len(pairs) == 1098 and hosts == 391)
                else "MISMATCH"),
            "fold_trigger_counts": {k: v for k, v in sorted(folds_ct.items())},
            "fold_trigger_counts_matched": {k: v for k, v in sorted(folds_ct_m.items())},
            "class_counts": {("ORDERLY" if k == 1 else "GAPPED"): v
                             for k, v in sorted(class_ct.items(), reverse=True)},
            "class_counts_matched": {("ORDERLY" if k == 1 else "GAPPED"): v
                                     for k, v in sorted(class_ct_m.items(), reverse=True)}}


def build_a5_h2(C):
    """SFV12-A5-H2 POSTSTAMP-CONTINUATION. Event set = NOT_DEAD_PRICE_SURVIVAL
    names with >= 20 strict post-stamp bars + matched host + (eligibility)
    post-window median dollar-volume >= 10k. Declared exposures: (i) long
    leg-weight vector over the 20-bar STRICT windows (equal-weight across
    concurrent events); (ii) raw conditioner printed_bars at arrivals."""
    events = []
    stats = {"survival_priced": 0, "fail_20bars": 0, "fail_liquidity": 0,
             "unmapped_sector": 0, "eligible": 0}
    for e in sorted(C.bookable):
        rec = C.p0d.get(e)
        if rec is None or rec["verdict"] != "NOT_DEAD_PRICE_SURVIVAL":
            continue
        s = C.series.get(e)
        if s is None:
            continue
        stats["survival_priced"] += 1
        T = dd(rec["death_date"])
        a = bisect_right(s["dates"], T)
        post = s["dates"][a:a + A5_WINDOW]
        if len(post) < A5_WINDOW:
            stats["fail_20bars"] += 1
            continue
        dol = sorted(s["close"][a + k] * (s["vol"][a + k] or 0.0)
                     for k in range(A5_WINDOW))
        med = (dol[A5_WINDOW // 2 - 1] + dol[A5_WINDOW // 2]) / 2.0  # standard even-n median
        if med < A5_LIQ_FLOOR:
            stats["fail_liquidity"] += 1
            continue
        sec = C.bookable[e]["sector"]
        if not sec:
            stats["unmapped_sector"] += 1
            continue
        # printed_bars: entity bars in the 20 SPY sessions ending at the last
        # session <= T (print-attendance count over calendar sessions)
        i_last = a - 1
        if i_last < 0:
            stats["fail_20bars"] += 1
            continue
        si = C.sess_idx.get(s["dates"][i_last])
        if si is None or si - (A5_WINDOW - 1) < 0:
            stats["fail_20bars"] += 1
            continue
        dset = set(x.isoformat() for x in s["dates"][max(0, i_last - A5_WINDOW):i_last + 1])
        printed = sum(1 for k in range(si - A5_WINDOW + 1, si + 1)
                      if C.sessions[k].isoformat() in dset)
        stats["eligible"] += 1
        events.append({"e": e, "T": T, "sec": sec, "printed": printed,
                       "cls": 1 if printed >= A5_PRINT_CUT else -1,
                       "window": post, "median_dolvol": med})
    pairs, unmapped, hosts = _pair_sham_pairs(C)
    matched = {d for d, _h, _s in pairs}
    ev_matched = [ev for ev in events if ev["e"] in matched]

    def long_weights(evts):
        slots = []
        for ev in evts:
            for dt in ev["window"]:
                slots.append((dt, ev["e"]))
        cnt = {}
        for dt, _e in slots:
            cnt[dt] = cnt.get(dt, 0) + 1
        return {(e, dt): 1.0 / cnt[dt] for dt, e in slots}

    anchor_w = long_weights(events)
    anchor_m_w = long_weights(ev_matched)
    # sham: long the HOST for 20 strict bars at its sham_date
    sham_events = []
    for ev in ev_matched:
        h, sec = None, None
        for d, hh, ss in pairs:
            if d == ev["e"]:
                h, sec = hh, ss
                break
        hs = C.series[h]
        off = (ev["T"] - hs["dates"][0]).days
        sham_date = hs["dates"][0] + timedelta(days=off)
        b = bisect_right(hs["dates"], sham_date)
        win = hs["dates"][b:b + A5_WINDOW]
        if len(win) < A5_WINDOW:
            continue
        sham_events.append({"e": h, "T": sham_date, "sec": sec,
                            "printed": ev["printed"], "cls": ev["cls"],
                            "window": win})
    sham_w = long_weights(sham_events)
    fold_ct, fold_ct_m = {}, {}
    for ev in events:
        f = fold_of(C, ev["T"])
        if f:
            fold_ct[f["fold_id"]] = fold_ct.get(f["fold_id"], 0) + 1
    for ev in ev_matched:
        f = fold_of(C, ev["T"])
        if f:
            fold_ct_m[f["fold_id"]] = fold_ct_m.get(f["fold_id"], 0) + 1
    class_ct = {"ORDERLY_REORG": sum(1 for ev in events if ev["cls"] == 1),
                "GAPPED_REORG": sum(1 for ev in events if ev["cls"] == -1)}
    return {"conditioner": {(ev["e"], ev["T"]): float(ev["printed"]) for ev in events},
            "anchor_w": anchor_w, "anchor_matched_w": anchor_m_w,
            "sham_w": sham_w,
            "stats": stats, "eligible_events": len(events),
            "eligible_matched": len(ev_matched),
            "sham_placed": len(sham_events),
            "unmapped_no_host": unmapped, "hosts": hosts,
            "matched_pair_verdict": (
                "MATCH" if (len(pairs) == 1098 and hosts == 391) else "MISMATCH"),
            "fold_counts": {k: v for k, v in sorted(fold_ct.items())},
            "fold_counts_matched": {k: v for k, v in sorted(fold_ct_m.items())},
            "class_counts": class_ct,
            "median_dolvols": {ev["e"]: round(ev["median_dolvol"], 2)
                               for ev in sorted(events, key=lambda x: x["e"])}}


def _field_primary(C, e, priority):
    """Primary field per entity = the priority-ordered field with the most
    period groups (ties broken by the declared priority order)."""
    best, best_n = None, -1
    for rank, f in enumerate(priority):
        effs = C.eff_groups.get((e, f))
        n = len(effs) if effs else 0
        if n > best_n:  # strict > keeps the earlier priority on ties
            best, best_n = f, n
    return best if best_n > 0 else None


def _latest_vintage(C, e, f, tau, eff=None):
    """Latest evidenced vintage with avail strictly before tau and
    tau - avail <= 800d; restricted to eff group when eff given."""
    if eff is None:
        lst = C.fields.get((e, f))
        if not lst:
            return None
        hi = bisect_left(lst, tau.isoformat(), key=lambda x: x[0])
        if hi == 0:
            return None
        av, eff_v, v = lst[hi - 1]
        if (tau - dd(av)).days > STALE_DAYS:
            return None
        return v, eff_v
    grp = C.eff_groups.get((e, f), {}).get(eff)
    if not grp:
        return None
    hi = bisect_left(grp, tau.isoformat(), key=lambda x: x[0])
    if hi == 0:
        return None
    av, v = grp[hi - 1]
    if (tau - dd(av)).days > STALE_DAYS:
        return None
    return v, eff


def build_a6(C, hid):
    """SFV12-A6-H1 (GP/assets level) / SFV12-A6-H2 (asset-turnover change).
    Decision instants = S3 structure-complete instants (last_avail of depth>=2
    chain groups whose entity has >= 5 strict bookable bars after last_avail),
    per-entity thinned to at most one NEW decision per 21-session span (first
    qualifying instant), within folds; exposure stamps strictly before the
    decision session (conservative LATER bound), 800d bound, positivity.
    Control = deterministic hash-order permutation placebo (sha256 of
    'cycle|hid|cik|decision_index', hex-sorted, rotate-by-one; V11 precedent
    convention for 'frozen deterministic hash order')."""
    REV_PRI, COGS_PRI = REV_PRIORITY, COGS_PRIORITY
    anchor = {}
    instants_all = 0
    instants_qual = 0
    abstain = {"no_primary_field": 0, "missing_or_stale_or_nonpositive": 0,
               "bars_63": 0, "outside_fold": 0}
    per_fold_defined = {}
    dec_dates_by_fold = {}
    # decision instants per entity
    decisions = []  # (tau_date, e, decision_index_global_later)
    for e in sorted(C.rev_avails):
        if e not in C.series:
            continue
        s_dates = C.series[e]["dates"]
        last_kept = None
        for a_iso in C.rev_avails[e]:
            a = dd(a_iso)
            instants_all += 1
            bi = bisect_right(s_dates, a)
            if len(s_dates) - bi < S3_MIN_STRICT_BARS:
                continue
            instants_qual += 1
            # decision session = first session strictly after the stamp
            si = bisect_right(C.sessions, a)
            if si >= len(C.sessions):
                continue
            tau = C.sessions[si]
            f = fold_of(C, tau)
            if f is None:
                abstain["outside_fold"] += 1
                continue
            if last_kept is not None and C.sess_idx[tau] < last_kept + GRID_STEP:
                continue
            last_kept = C.sess_idx[tau]
            if not has_bars(C, e, tau):
                abstain["bars_63"] += 1
                continue
            decisions.append((tau, e, f["fold_id"]))
            dec_dates_by_fold.setdefault(f["fold_id"], set()).add(tau)
    dec_dates_all = sorted({t for t, _e, _f in decisions})
    di_of = {t: i for i, t in enumerate(dec_dates_all)}
    for tau, e, fid in sorted(decisions):
        rev_f = _field_primary(C, e, REV_PRI)
        if rev_f is None:
            abstain["no_primary_field"] += 1
            continue
        if hid == "SFV12-A6-H1":
            cogs_f = _field_primary(C, e, COGS_PRI)
            r = _latest_vintage(C, e, rev_f, tau)
            c = _latest_vintage(C, e, cogs_f, tau) if cogs_f else None
            a = _latest_vintage(C, e, "us-gaap:Assets", tau)
            if not (r and c and a) or r[0] <= 0 or c[0] <= 0 or a[0] <= 0:
                abstain["missing_or_stale_or_nonpositive"] += 1
                continue
            anchor[(e, tau)] = (r[0] - c[0]) / a[0]
        else:
            r = _latest_vintage(C, e, rev_f, tau)
            a = _latest_vintage(C, e, "us-gaap:Assets", tau)
            if not (r and a) or r[0] <= 0 or a[0] <= 0:
                abstain["missing_or_stale_or_nonpositive"] += 1
                continue
            # preceding eff group of the same field stream
            effs = C.eff_groups.get((e, rev_f), {})
            eff_last = r[1]
            prior_effs = [k for k in effs if k < eff_last]
            if not prior_effs:
                abstain["missing_or_stale_or_nonpositive"] += 1
                continue
            eff_prev = prior_effs[-1]
            rv = _latest_vintage(C, e, rev_f, tau, eff=eff_prev)
            av_ = _latest_vintage(C, e, "us-gaap:Assets", tau, eff=eff_prev)
            if not (rv and av_) or rv[0] <= 0 or av_[0] <= 0:
                abstain["missing_or_stale_or_nonpositive"] += 1
                continue
            anchor[(e, tau)] = (r[0] / a[0]) - (rv[0] / av_[0])
        per_fold_defined[fid] = per_fold_defined.get(fid, 0) + 1
    # control: rotate-by-one in hex-sorted sha256 hash order per decision date
    control = {}
    by_date = {}
    for (e, t) in anchor:
        by_date.setdefault(t, []).append(e)
    for t in sorted(by_date):
        names = sorted(by_date[t],
                       key=lambda e: sha256_hex(
                           f"{CYCLE}|{hid}|{e}|{di_of[t]}".encode()))
        m = len(names)
        if m < 2:
            continue
        for i, e in enumerate(names):
            control[(e, t)] = anchor[(names[(i - 1) % m], t)]
    # A6 adjudication measurements: panel field presence on the bookable pool
    field_evidence = {}
    for f in REV_PRI + COGS_PRI + ["us-gaap:Assets"]:
        st = C.panel_field_stats.get(f, {"rows_bookable": 0, "entities_bookable": 0})
        field_evidence[f] = st
    return {"anchor": anchor, "control": control,
            "instants_all_depth2": instants_all,
            "instants_ge5_strict_bars": instants_qual,
            "decision_dates_total": len(dec_dates_all),
            "decision_counts_defined_per_fold": {k: v for k, v in sorted(per_fold_defined.items())},
            "decision_dates_per_fold": {k: len(v) for k, v in sorted(dec_dates_by_fold.items())},
            "abstain": abstain,
            "warmup_declared": 3,
            "panel_field_evidence": field_evidence}


PROPOSAL_BUILDERS = {
    "SFV12-A4-H1": lambda C: build_a4(C, "SFV12-A4-H1", PCG_SEED_H1),
    "SFV12-A4-H2": lambda C: build_a4(C, "SFV12-A4-H2", PCG_SEED_H2),
    "SFV12-A5-H1": build_a5_h1,
    "SFV12-A5-H2": build_a5_h2,
    "SFV12-A6-H1": lambda C: build_a6(C, "SFV12-A6-H1"),
    "SFV12-A6-H2": lambda C: build_a6(C, "SFV12-A6-H2"),
}


# ===========================================================================
# CORRELATION + VERDICTS
# ===========================================================================
def novelty_block(C, anchor):
    entry = {"veto_rho": {}, "n_per_veto": {}, "margin_to_020": {}}
    for vn in VETO_NAMES:
        vf = VETO_BUILDERS[vn]
        common_a, common_v = [], []
        for (e, t), av in sorted(anchor.items()):
            vv = vf(C, e, t)
            if vv is not None:
                common_a.append(av)
                common_v.append(vv)
        rho = spearman(common_a, common_v)
        entry["veto_rho"][vn] = None if rho is None else round(rho, 4)
        entry["n_per_veto"][vn] = len(common_a)
        entry["margin_to_020"][vn] = (
            None if rho is None else round(NOVELTY_BAR - abs(rho), 4))
    valid = {vn: abs(v) for vn, v in entry["veto_rho"].items() if v is not None}
    entry["max_abs_veto_rho"] = round(max(valid.values()), 4) if valid else None
    arg = max(sorted(valid), key=lambda k: valid[k]) if valid else None
    entry["argmax_veto"] = arg
    entry["worst_margin_to_020"] = (round(NOVELTY_BAR - valid[arg], 4) if arg else None)
    entry["vetoes_measured"] = len(valid)
    entry["novelty_pass_le_020"] = (len(valid) == len(VETO_NAMES)
                                    and max(valid.values()) <= NOVELTY_BAR)
    return entry


def rho_on_common(a, b):
    common = sorted(k for k in a if k in b)
    if not common:
        return None, 0
    return spearman([a[k] for k in common], [b[k] for k in common]), len(common)


def rho_on_union_zerofill(a, b):
    ka = sorted(set(a) | set(b))  # sorted: no hash-order dependence
    va = [a.get(k, 0.0) for k in ka]
    vb = [b.get(k, 0.0) for k in ka]
    return spearman(va, vb), len(ka)


def daily_series(a):
    """Per-date (book-level) aggregate of leg weights — the 'per-period series'
    the A5 self-subsumption language refers to."""
    out = {}
    for (_e, t), w in a.items():
        out[t] = out.get(t, 0.0) + w
    return out


def identifiability_weights(C, built, aw_key):
    """A5 anchor-vs-sham identifiability. Primary: pooled Spearman on the UNION
    (entity, date) cell grid with 0-fill (V11 union-grid precedent — sham dates
    differ from event dates by construction, so common-pairs rho is empty);
    per-date rho on the same union grid for dates with >= 10 cells; plus the
    daily book-level weight-series rho as descriptive support."""
    a, b = built[aw_key], built["sham_w"]
    dates = sorted({t for _e, t in a} | {t for _e, t in b})
    out = {"gate_per_date_rho": A4_R1_DATE_RHO,
           "gate_date_pass_share": A4_DATE_PASS_SHARE,
           "gate_self_subsumption_rho": SELF_SUBSUMPTION_RHO,
           "grid": "union (entity, date) leg-weight cells, 0-filled on the union"}
    pooled, n = rho_on_union_zerofill(a, b)
    out["pooled_anchor_vs_sham_rho"] = None if pooled is None else round(pooled, 4)
    out["union_cells"] = n
    if pooled is not None:
        out["self_subsumption_kill"] = bool(abs(pooled) > SELF_SUBSUMPTION_RHO)
    # per-date union-grid rho (date-bucketed once)
    buckets = {}
    for k in set(a) | set(b):
        buckets.setdefault(k[1], []).append(k)
    ok = tot = 0
    for t in sorted(buckets):
        ks = buckets[t]
        if len(ks) < 10:
            continue
        r = spearman([a.get(k, 0.0) for k in ks], [b.get(k, 0.0) for k in ks])
        if r is None:
            continue
        tot += 1
        ok += 1 if abs(r) <= A4_R1_DATE_RHO else 0
    out["per_date"] = {"dates_measured": tot,
                       "share_dates_abs_le_gate": round(ok / tot, 4) if tot else None,
                       "gate": A4_R1_DATE_RHO}
    # daily book-level weight-series rho (descriptive)
    da, db = daily_series(a), daily_series(b)
    common = sorted(k for k in da if k in db)
    out["daily_series_overlap_dates"] = len(common)
    if len(common) >= 10:
        rs = spearman([da[k] for k in common], [db[k] for k in common])
        out["daily_series_rho"] = None if rs is None else round(rs, 4)
    gate_ok = tot > 0 and ok / tot >= A4_DATE_PASS_SHARE
    out["verdict"] = ("BLOCKED_SELF_SUBSUMPTION" if out.get("self_subsumption_kill")
                      else ("PASS" if pooled is not None and gate_ok
                            else "BLOCKED_CONTROL_UNIDENTIFIABLE"))
    return out


def per_date_rho_stats(C, a, b, dates, gate):
    """Per-date Spearman rho on common pairs (dates in session order,
    >= 10 pairs each)."""
    rhos = []
    for t in dates:
        ks = sorted(k for k in a if k[1] == t and k in b)
        if len(ks) < 10:
            continue
        r = spearman([a[k] for k in ks], [b[k] for k in ks])
        if r is None:
            continue
        rhos.append((t, r))
    if not rhos:
        return None
    ok = sum(1 for _t, r in rhos if abs(r) <= gate)
    return {"dates_measured": len(rhos),
            "mean_per_date_rho": round(sum(r for _t, r in rhos) / len(rhos), 4),
            "share_dates_abs_le_gate": round(ok / len(rhos), 4),
            "gate": gate}


def identifiability_a4(C, pid, built):
    anchor, control = built["anchor"], built["control"]
    dates = grid_dates_flat(C, C.grid21)
    out = {"gate_R1_date_rho": A4_R1_DATE_RHO,
           "gate_R1_pooled_mean": A4_R1_DATE_RHO,
           "gate_self_subsumption_rho": SELF_SUBSUMPTION_RHO}
    stats = per_date_rho_stats(C, anchor, control, dates, A4_R1_DATE_RHO)
    out["per_date"] = stats
    pooled, n = rho_on_common(anchor, control)
    out["pooled_anchor_vs_control_rho"] = None if pooled is None else round(pooled, 4)
    out["control_pairs"] = n
    if pooled is not None:
        out["self_subsumption_kill"] = bool(abs(pooled) > SELF_SUBSUMPTION_RHO)
    # R2 control non-degeneracy
    tot = ok = 0
    for t in dates:
        if t not in built["r2_ctrl"]:
            continue
        bot, top = built["r2_ctrl"][t]
        tot += 1
        ok += 1 if (bot >= A4_TERCILE_MIN and top >= A4_TERCILE_MIN) else 0
    out["R2_control_terciles"] = {"share_dates_both_ge6": round(ok / tot, 4) if tot else None,
                                  "dates": tot,
                                  "pass": bool(tot and ok / tot >= A4_DATE_PASS_SHARE)}
    # R3 anchor coverage
    tot = ok = 0
    for t in dates:
        mu = built["measured_universe"].get(t, 0)
        anc = sum(1 for k in anchor if k[1] == t)
        if mu < 10:
            continue
        tot += 1
        ok += 1 if anc / mu >= A4_R3_COVERAGE else 0
    out["R3_anchor_coverage"] = {"share_dates_ge_060": round(ok / tot, 4) if tot else None,
                                 "dates": tot,
                                 "pass": bool(tot and ok / tot >= A4_DATE_PASS_SHARE)}
    # R4 short-leg population
    tot = ok = 0
    for t in dates:
        if t not in built["r4_pos_top"]:
            continue
        tot += 1
        ok += 1 if built["r4_pos_top"][t] >= A4_TERCILE_MIN else 0
    out["R4_short_leg_population"] = {"share_dates_ge6_pos": round(ok / tot, 4) if tot else None,
                                      "dates": tot,
                                      "pass": bool(tot and ok / tot >= A4_DATE_PASS_SHARE)}
    # R5 sector participation
    tot = ok = 0
    for t in dates:
        mu = built["measured_universe"].get(t, 0)
        sok = built["sect_ok_count"].get(t, 0)
        if mu < 10:
            continue
        tot += 1
        ok += 1 if sok / mu >= A4_R5_SECTOR_PART else 0
    out["R5_sector_participation"] = {"share_dates_ge_060": round(ok / tot, 4) if tot else None,
                                      "dates": tot,
                                      "pass": bool(tot and ok / tot >= A4_DATE_PASS_SHARE)}
    r1 = stats is not None and stats["share_dates_abs_le_gate"] >= A4_DATE_PASS_SHARE \
        and abs(stats["mean_per_date_rho"]) <= A4_R1_DATE_RHO
    out["R1_rank_gate_pass"] = bool(r1)
    out["verdict"] = ("BLOCKED_SELF_SUBSUMPTION" if out.get("self_subsumption_kill")
                      else ("PASS" if r1 and out["R2_control_terciles"]["pass"]
                            and out["R3_anchor_coverage"]["pass"]
                            and out["R4_short_leg_population"]["pass"]
                            and out["R5_sector_participation"]["pass"]
                            else "BLOCKED_CONTROL_UNIDENTIFIABLE_OR_BOOK_UNPOPULATED"))
    return out


def identifiability_weights(C, built, aw_key):
    a, b = built[aw_key], built["sham_w"]
    dates = sorted({t for _e, t in a})
    out = {"gate_per_date_rho": A4_R1_DATE_RHO,
           "gate_date_pass_share": A4_DATE_PASS_SHARE,
           "gate_self_subsumption_rho": SELF_SUBSUMPTION_RHO}
    pooled, n = rho_on_common(a, b)
    out["pooled_anchor_vs_sham_rho"] = None if pooled is None else round(pooled, 4)
    out["common_pairs"] = n
    if pooled is not None:
        out["self_subsumption_kill"] = bool(abs(pooled) > SELF_SUBSUMPTION_RHO)
    stats = per_date_rho_stats(C, a, b, dates, A4_R1_DATE_RHO)
    out["per_date"] = stats
    ok = stats is not None and stats["share_dates_abs_le_gate"] >= A4_DATE_PASS_SHARE
    out["verdict"] = ("BLOCKED_SELF_SUBSUMPTION" if out.get("self_subsumption_kill")
                      else ("PASS" if ok and pooled is not None
                            else "BLOCKED_CONTROL_UNIDENTIFIABLE"))
    return out


def identifiability_a6(C, hid, built):
    anchor, control = built["anchor"], built["control"]
    out = {"gate_self_subsumption_rho": SELF_SUBSUMPTION_RHO}
    pooled, n = rho_on_common(anchor, control)
    out["pooled_anchor_vs_control_rho"] = None if pooled is None else round(pooled, 4)
    out["control_pairs"] = n
    if pooled is not None:
        out["self_subsumption_kill"] = bool(abs(pooled) > SELF_SUBSUMPTION_RHO)
    stats = per_date_rho_stats(C, anchor, control, sorted({t for _e, t in anchor}),
                               A4_R1_DATE_RHO)
    if stats:
        out["per_date_descriptive"] = stats
    out["verdict"] = ("BLOCKED_SELF_SUBSUMPTION" if out.get("self_subsumption_kill")
                      else "PASS")
    return out


def feasibility_block(C, pid, built):
    out = {"floors": {"overall_min": FLOOR_OVERALL, "per_fold_min": FLOOR_PER_FOLD},
           "cost_ladder": {"band_bps": {"A": 10.0, "B": 15.0, "C": 25.0},
                           "stress_mult": 2.0,
                           "note": ("A9-F adjudicates the cost ceiling; D2 reports exposure "
                                    "arithmetic only — no returns, no PnL")}}
    ar = out["arithmetic"] = {}
    if pid in ("SFV12-A4-H1", "SFV12-A4-H2"):
        per_fold = {f["fold_id"]: len(C.grid21[f["fold_id"]]) for f in C.folds}
        overall = sum(per_fold.values())
        warmup = WARMUP[pid]
        first_t = dd(grid_dates_flat(C, C.grid21)[0])
        mu0 = built["measured_universe"].get(first_t, 0)
        anc0 = sum(1 for k in built["anchor"] if k[1] == first_t)
        ar = {"basis": "inherited 21-session grid (fold-local 63+21k), all grid dates scored",
              "decisions_overall": overall, "warmup_decisions": warmup,
              "scored_decisions_overall": overall - warmup,
              "per_fold": per_fold,
              "warmup_coverage_first_decision": {
                  "date": first_t.isoformat(), "measured_universe": mu0,
                  "anchor_defined": anc0,
                  "share": round(anc0 / mu0, 4) if mu0 else None,
                  "note": "Q(e,t) requires |Q| >= 4 within the 800d staleness bound"}}
        turnover = ("tercile book, 21-session hold + one-decile rank hysteresis: upper "
                    "bound 2x gross per decision ~ 24x gross/yr two-way without "
                    "hysteresis; declared expected below the 6.0/yr ceiling")
        cost = ("blended base expected 15-25 bps/side (short leg skews deep-chain, "
                "lower-ADV); stress x2 = 20/30/50 bps declared primary gate; A9-F "
                "adjudicates at the frozen floor")
    elif pid == "SFV12-A5-H1":
        per_fold = {f["fold_id"]: built["fold_trigger_counts_matched"].get(f["fold_id"], 0)
                    for f in C.folds}
        overall = sum(per_fold.values())
        ar = {"basis": "evidenced Form-15 triggers, mapped-sector matched subset "
                       "(identical exclusion across arms)",
              "triggers_full": sum(built["fold_trigger_counts"].values()),
              "triggers_matched": overall,
              "per_fold_matched": per_fold,
              "class_counts_full": built["class_counts"],
              "class_counts_matched": built["class_counts_matched"],
              "vacuity_gate": {"min_events_per_class": VACUITY_MIN_CLASS_EVENTS,
                               "pass": all(v >= VACUITY_MIN_CLASS_EVENTS
                                           for v in built["class_counts_matched"].values())},
              "warmup_coverage": "event-set family: no grid warmup; coverage = fold "
                                 "trigger counts above",
              "control_runnability": built["sham_stats"]}
        turnover = ("event book, 20-bar windows: per event 2 fills (entry+exit) "
                    "2-way ~ 24/yr per continuously-active name; overlap-aggregated "
                    "book turnover reported raw and ceiling-normalized at scoring")
        cost = ("fills on ALIVE_EVIDENCED peers: mixed B/C cohort expected, blended "
                "base 15-25 bps/side; stress x2 = 20/30/50 bps; A9-F adjudicates")
    elif pid == "SFV12-A5-H2":
        per_fold = {f["fold_id"]: built["fold_counts_matched"].get(f["fold_id"], 0)
                    for f in C.folds}
        overall = sum(per_fold.values())
        ar = {"basis": "survival-verdict events: >= 20 strict post-stamp bars AND "
                       "post-window median dollar-volume >= 10k AND matched host",
              "survival_priced": built["stats"]["survival_priced"],
              "fail_20bars": built["stats"]["fail_20bars"],
              "fail_liquidity": built["stats"]["fail_liquidity"],
              "eligible": built["eligible_events"],
              "eligible_matched": built["eligible_matched"],
              "per_fold_matched": per_fold,
              "class_counts": built["class_counts"],
              "warmup_coverage": "event-set family: no grid warmup; coverage = "
                                 "eligible event counts above",
              "control_runnability": {"sham_placed": built["sham_placed"],
                                      "hosts": built["hosts"],
                                      "census_host_side": "391/391 hosts hold >= 1 "
                                                          "runnable w20 window (census)"}}
        turnover = ("long book, 20-bar windows: 2 fills per event, ~24 2-way/yr per "
                    "active name; ceiling-normalized at scoring")
        cost = ("DECLARED expected kill zone: band-C-dominant OTC fills, 25 bps base, "
                "stress 50 bps expected to consume the entire margin; the family "
                "claims no immunity — A9-F cheap-kill is a correct REJECT")
    else:  # A6
        per_fold = {f["fold_id"]: built["decision_counts_defined_per_fold"].get(f["fold_id"], 0)
                    for f in C.folds}
        overall = sum(per_fold.values())
        warmup = WARMUP[pid]
        ar = {"basis": "S3 structure-complete instants (last_avail of depth>=2 groups "
                       "with >= 5 strict bookable bars after), per-entity thinning 1 "
                       "per 21-session span, exposure-defined decisions, within folds",
              "instants_all_depth2_bookable": built["instants_all_depth2"],
              "instants_ge5_strict_bars": built["instants_ge5_strict_bars"],
              "decision_dates_total": built["decision_dates_total"],
              "defined_decisions_overall": overall,
              "warmup_decisions": warmup,
              "scored_decisions_overall": max(0, overall - warmup),
              "per_fold_defined": per_fold,
              "abstain_counts": built["abstain"]}
        turnover = ("21-session holds, one NEW position per entity per span: ~1x gross "
                    "one-way per span ~ 12x/yr one-way upper bound plus dead-leg exits")
        cost = ("expected band-B/C-weighted ~ 15-25 bps/side on a 21-session hold; "
                "stress x2 = 20/30/50 bps; A9-F adjudicates at the frozen floor")
    out["arithmetic"] = ar
    scored = ar.get("scored_decisions_overall", ar.get("triggers_matched",
                                                       ar.get("eligible_matched", 0)))
    min_fold = min(per_fold.values()) if per_fold else 0
    out["margin_overall_vs_30"] = scored - FLOOR_OVERALL
    out["margin_min_fold_vs_5"] = min_fold - FLOOR_PER_FOLD
    out["floors_pass"] = bool(scored >= FLOOR_OVERALL and min_fold >= FLOOR_PER_FOLD)
    out["turnover_exposure_note"] = turnover
    out["cost_ceiling_exposure_note"] = cost
    return out


# ===========================================================================
# MAIN (heavy run) + SELFCHECK
# ===========================================================================
def verify_proposals():
    pins = {}
    ok = True
    for hf in HASH_FILES:
        d = json.loads(hf.read_text())
        for rec in d["proposals"]:
            p = PROPOSALS_DIR / Path(rec["file"]).name
            measured = sha256_hex(p.read_bytes())
            verdict = "MATCH" if rec["sha256"] == measured else "MISMATCH"
            pins[Path(rec["file"]).name] = {"pin": rec["sha256"], "measured": measured,
                                            "verdict": verdict}
            if verdict != "MATCH":
                ok = False
    for pid, fn in PROPOSAL_FILES.items():
        prop = json.loads((PROPOSALS_DIR / fn).read_text())
        wv = "MATCH" if prop.get("wave_sha") == WAVE_SHA else "MISMATCH"
        pins[fn]["wave_sha_verdict"] = wv
        if wv != "MATCH":
            ok = False
    return ok, pins


CONVENTIONS = {
    "global": [
        "adapted from d2_v11_novelty_measure.py @ 9d3a0612 (V11-cycle tooling); "
        "V12-specific: THIRTEEN-entry veto set, V12 proposal builders, A6 S3 "
        "decision stream, A5 class/leg-weight exposure vectors",
        "Spearman midrank ties, pooled on common (entity, decision-instant) pairs; "
        "n >= 10 per comparison else None; novelty fail-closed (a null veto entry "
        "fails the gate, never passes open)",
        "veto values evaluated at the proposal's own decision instants, including "
        "event-anchored dates (inherited V10/V11 form for vetoes 1-11; veto 12 = "
        "share of in-window groups with inter_arrival_days > 460 — the V11 "
        "measured-dead cadence-latency statistic, ancestry substrate only; veto 13 "
        "= sign of the 5-bar SPY-residual initial reaction at the most recent "
        "filing arrival within 800d — the V11 A4 reaction-shadow form)",
        "rev_dir encoding -1=down / 0=flat / 1=up fail-closed verified against the "
        "V10 P0 manifest dir_counts at load",
        "gate(t) semantics: date-only stamps; last_avail < decision date (strict); "
        "staleness 0 <= t - last_avail <= 800d; first_avail/avail stamps take the "
        "conservative LATER bound (decision session = first session strictly after "
        "the stamp)",
        "63-bar pre-check floor uses staged price bar counts only; NO band "
        "computation, NO ADV, NO returns anywhere",
        "universe = ALIVE_EVIDENCED + DEAD_EVIDENCED cohort legs (bookable pool); "
        "priced = has staged EOD file (any length) for pairing arithmetic; the "
        "63-bar floor gates measured-universe membership for grid/S3 families",
        "control identifiability self-subsumption kill at pooled |rho| > 0.98 per "
        "the V15 lesson (declared in all six proposals, binding pre-score)",
    ],
    "per_proposal": {
        "SFV12-A4-H1": [
            "anchor deep_share(e,t) = |{g in Q: depth >= 6}| / |Q|, |Q| >= 4, raw "
            "value (no standardization) per the declared formula",
            "neighbour median qualifying depth computed from the same window walk; "
            "cross-anchor A4-H1 vs A4-H2 pooled rho reported as the declared "
            "mutual-distinctness check (0.98 kill declared binding)",
            "control = within-sector marginal-preserving permutation, PCG64 seed "
            "20260908 (proposal-frozen), applied to the CIK-sorted index vector, "
            "redrawn per decision date in session-index order",
            "tercile counts under the declared boundary-tie rule (ties join the "
            "long/lower tercile)",
        ],
        "SFV12-A4-H2": [
            "anchor conc(e,t) = (max depth - 2) / (sum depth - 2|Q|) over Q, "
            "|Q| >= 4; degenerate sum of excess = 0 mapped to the declared diffuse "
            "floor 0.0",
            "neighbour peak excess severity = max qualifying depth - 2 from the "
            "same window walk",
            "control = same permutation machinery, PCG64 seed 20260909 "
            "(proposal-frozen)",
        ],
        "SFV12-A5-H1": [
            "conditioner exposure (ii) = gap_days class ORDERLY=+1 / GAPPED=-1 at "
            "(trigger, evidenced Form-15 arrival); gap_days = calendar days "
            "T - last bar <= T within 800d",
            "leg-weight exposure (i) = per-entity net weight at event dates: dedup "
            "(sector, class, date), equal-weight basket of mapped ALIVE_EVIDENCED "
            "priced peers with >= 63 bars through the event date, dying name never "
            "held; UNMAPPED-sector triggers excluded-with-reason (counted)",
            "identifiability measured on the matched-host subset (identical "
            "exclusion across arms per the declared 671-UNMAPPED answer); sham = "
            "host inherits the paired dead's class at sham_date = host first bar + "
            "offset (census pairing rule, runtime-verified against census counts "
            "1098 pairs / 391 hosts / 671 unmapped)",
            "peer-basket eligibility uses the 63-bar bar-count floor only (no ADV "
            "band computation at D2 — recorded against-eligibility convention)",
        ],
        "SFV12-A5-H2": [
            "conditioner exposure (ii) = printed_bars over the 20 SPY sessions "
            "ending at the last session <= stamp (print-attendance count); class "
            "ORDERLY-REORG >= 15 / GAPPED-REORG <= 14 recorded",
            "leg-weight exposure (i) = long 1/n_active per active 20-bar STRICT "
            "window (equal-weight across concurrent events); eligibility = "
            ">= 20 strict post-stamp bars AND post-window median dollar-volume "
            ">= 10k AND mapped sector; matched-host subset for identifiability",
            "sham = long the matched host for 20 strict bars at its sham_date "
            "(census pairing rule); reorg/survival semantics acknowledged (the "
            "family declares them ex-ante; D2 measures conditioning exposures "
            "only)",
            "dollar-volume eligibility arithmetic uses unadjusted close * volume "
            "(census liquidity convention) — an eligibility floor, not a return",
        ],
        "SFV12-A6-H1": [
            "decision stream = S3 instants (last_avail of depth>=2 groups with "
            ">= 5 strict bookable bars after last_avail), decision session = "
            "first session strictly after the stamp (conservative LATER bound), "
            "per-entity thinning: at most one NEW decision per 21-session span "
            "(first qualifying instant), within folds",
            "exposure = (REV_last - COGS_last) / ASSETS_last; primary revenue/"
            "COGS field per entity = the priority-ordered field with the most "
            "period groups (ties broken by the declared priority order); latest "
            "evidenced vintage with avail strictly before the decision session "
            "and within 800d; abstain fail-closed on missing/non-positive/stale",
            "control = exposure values rotated by one in the hex-sorted "
            "sha256('cycle|hid|cik|decision_index') hash order per decision date "
            "(no RNG library, byte-reproducible; decision_index = ordinal of the "
            "decision date in the family's sorted distinct-date list)",
        ],
        "SFV12-A6-H2": [
            "decision stream identical to H1 (same S3 scaffold, same thinning)",
            "exposure = (REV_last/ASSETS_last) - (REV_prev/ASSETS_prev) across "
            "consecutive eff periods of the SAME field stream (never across "
            "revisions of one period); all four stamps strictly before the "
            "decision session and within 800d; abstain fail-closed",
            "control = hash-order permutation placebo as H1 (full eligible set, "
            "declared within-decision variant)",
        ],
    },
}


def run_full(built_at_utc):
    ok, hashes = verify_proposals()
    if not ok:
        for fn, rec in hashes.items():
            if rec.get("verdict") != "MATCH" or rec.get("wave_sha_verdict") != "MATCH":
                sys.stderr.write(f"BLOCKED: proposal hash/wave pin mismatch {fn}: {rec}\n")
        return 2
    print("[d2] proposal hash pins verified (6/6 MATCH).", flush=True)

    C, rc = load_context()
    if rc != 0:
        return rc
    _bench_series(C)  # benchmark closes for the veto-13 reaction shadow
    # census cross-checks
    census = json.loads(P0_CENSUS.read_text())
    s3 = census["census_l1_structure"]["bookable_groups_strict_after_last_avail"]
    C.s3_census = {"groups_ge5": s3["groups_ge5"], "groups_ge1": s3["groups_ge1"],
                   "groups_ge20": s3["groups_ge20"]}
    C.verdict_check = {
        "p0d_measured": C.verdict_counts,
        "p3_expected": {"DEAD_PRICE_CONFIRMED": 1550, "NOT_DEAD_PRICE_SURVIVAL": 219},
        "verdict": "MATCH" if C.verdict_counts == {"DEAD_PRICE_CONFIRMED": 1550,
                                                   "NOT_DEAD_PRICE_SURVIVAL": 219}
        else "MISMATCH"}
    if C.verdict_check["verdict"] != "MATCH":
        sys.stderr.write("BLOCKED: p0d verdict split mismatch\n")
        return 2

    built = {pid: PROPOSAL_BUILDERS[pid](C) for pid in PROPOSAL_ORDER}

    # cross-anchor A4-H1 vs A4-H2 (declared mutual-distinctness check)
    x_rho, x_n = rho_on_common(built["SFV12-A4-H1"]["anchor"], built["SFV12-A4-H2"]["anchor"])

    results = {}
    for pid in PROPOSAL_ORDER:
        b = built[pid]
        if pid in ("SFV12-A4-H1", "SFV12-A4-H2"):
            anchor_vec = b["anchor"]
            id_block = identifiability_a4(C, pid, b)
            feas = feasibility_block(C, pid, b)
            feas["control_runnability_verdict"] = (
                "RUNNABLE" if (id_block.get("control_pairs") or 0) > 0
                else "DESIGN_FAILURE")
        elif pid == "SFV12-A5-H1":
            anchor_vec = {**b["conditioner"], **b["anchor_w"]}
            # veto rho on the union of declared exposure vectors (conditioner ii
            # + leg weights i); also reported separately below
            id_block = identifiability_weights(C, b, "anchor_matched_w")
            id_block["sham_runnability"] = b["sham_stats"]
            id_block["matched_pair_verdict"] = b["matched_pair_verdict"]
            id_block["control_runnability_verdict"] = (
                "RUNNABLE" if b["matched_pair_verdict"] == "MATCH"
                and b["sham_stats"]["sham_events"] > 0 and id_block["verdict"] == "PASS"
                else "DESIGN_FAILURE" if b["matched_pair_verdict"] != "MATCH"
                or b["sham_stats"]["sham_events"] == 0 else id_block["verdict"])
            feas = feasibility_block(C, pid, b)
        elif pid == "SFV12-A5-H2":
            anchor_vec = {**b["conditioner"], **b["anchor_w"]}
            id_block = identifiability_weights(C, b, "anchor_matched_w")
            id_block["sham_runnability"] = {"sham_placed": b["sham_placed"],
                                            "eligible_matched": b["eligible_matched"],
                                            "hosts": b["hosts"]}
            id_block["matched_pair_verdict"] = b["matched_pair_verdict"]
            id_block["control_runnability_verdict"] = (
                "RUNNABLE" if b["matched_pair_verdict"] == "MATCH"
                and b["sham_placed"] > 0 and id_block["verdict"] == "PASS"
                else "DESIGN_FAILURE" if b["matched_pair_verdict"] != "MATCH"
                or b["sham_placed"] == 0 else id_block["verdict"])
            feas = feasibility_block(C, pid, b)
        else:
            anchor_vec = b["anchor"]
            id_block = identifiability_a6(C, pid, b)
            id_block["control_runnability_verdict"] = (
                "RUNNABLE" if (id_block.get("control_pairs") or 0) > 0
                else "DESIGN_FAILURE")
            feas = feasibility_block(C, pid, b)
        nov = novelty_block(C, anchor_vec)
        nov["exposure_vectors_measured"] = (
            "declared conditioner + per-entity net leg weight (union on common pairs)"
            if pid.startswith("SFV12-A5") else "single declared conditioning exposure")
        verdict = "ELIGIBLE"
        if not nov["novelty_pass_le_020"]:
            verdict = "BLOCKED_NOVELTY"
        elif "BLOCKED" in id_block["verdict"]:
            verdict = "BLOCKED_IDENTIFIABILITY"
        elif id_block.get("control_runnability_verdict") == "DESIGN_FAILURE":
            verdict = "BLOCKED_CONTROL_DESIGN_FAILURE"
        elif not feas["floors_pass"]:
            verdict = "INFEASIBLE_DECISION_FLOORS"
        results[pid] = {"novelty": nov, "identifiability": id_block,
                        "feasibility": feas, "verdict": verdict}

    a6_evidence = built["SFV12-A6-H1"]["panel_field_evidence"]
    audit = {
        "schema": "stocks_free_v12_run/d2_novelty_measure@1",
        "built_at_utc": built_at_utc,
        "producer_role": "D2 measurement lane module (adapted from V11 d2 module; "
                         "executed under the machine-wide heavy lock)",
        "cycle": CYCLE,
        "wave_sha": WAVE_SHA,
        "base_sha": BASE_SHA,
        "discipline": "feature/rank arithmetic only; zero PnL, zero returns, zero "
                      "selection, zero scoring; universe = entity-decision pairs "
                      "where the proposal exposure is defined on the bookable pool",
        "proposal_hashes": hashes,
        "input_integrity": {
            "pins": C.pins, "pin_verdicts": C.pin_verdicts,
            "rev_dir_encoding_check": C.dir_check,
            "p0d_verdict_split_check": C.verdict_check,
            "priced_counts": C.priced_counts,
            "filer_events_distinct_bookable": C.filer_event_count,
            "census_s3_reference": C.s3_census,
        },
        "decision_dates": {
            "grid_21s_per_fold": built["SFV12-A4-H1"]["grid_dates"],
            "a5_event_anchored": "trigger/event arrival-anchored; per-fold counts "
                                 "in results[].feasibility.arithmetic",
            "a6_s3_event_staggered": {
                "instants_ge5_strict_bars": built["SFV12-A6-H1"]["instants_ge5_strict_bars"],
                "decision_dates_total": built["SFV12-A6-H1"]["decision_dates_total"]},
        },
        "veto_set": {"count": len(VETO_NAMES), "names": VETO_NAMES,
                     "rev_dir_encoding": {"mapping": REV_DIR_ENCODING,
                                          "runtime_check": C.dir_check}},
        "conventions_applied": CONVENTIONS,
        "cross_anchor_checks": {
            "SFV12-A4-H1_vs_SFV12-A4-H2": {
                "pooled_rho": None if x_rho is None else round(x_rho, 4),
                "pairs": x_n,
                "declared_rule": "mutual distinctness: rho > 0.98 would be a "
                                 "self-subsumption of one another and BOTH die "
                                 "pre-score (declared binding in both proposals)",
                "verdict": ("BLOCKED_MUTUAL_SUBSUMPTION"
                            if x_rho is not None and abs(x_rho) > SELF_SUBSUMPTION_RHO
                            else "DISTINCT")},
        },
        "a6_clock_adjudication": {
            "item": "A1 adjudication item: A6 cites clock V12-S3 as 'decision "
                    "scaffold only' with panel-characteristic conditioners - "
                    "legitimately carried, or UNFUNDED at P2?",
            "p2_gating_rule_verbatim": json.loads(P2.read_text())["gating_rule_for_D2"],
            "clock_resolution": {
                "clock_id": "V12-S3-STRUCTURE-BOOKABLE-WINDOWS",
                "in_p2_funded_clocks": True,
                "p2_record_verbatim": [c for c in json.loads(P2.read_text())["funded_clocks"]
                                       if c["clock_id"] == "V12-S3-STRUCTURE-BOOKABLE-WINDOWS"][0],
                "usage": "decision scaffold only (structure-complete instants); no "
                         "chain observable conditioned on, ranked, or interacted - "
                         "declared in both A6 proposals as clock_usage_honesty"},
            "panel_substrate_evidence": {
                "source": "measured directly on the sha-pinned V9 panel bytes "
                          "(67591464..., pin verified at load) over the bookable pool",
                "fields": a6_evidence,
                "note": "us-gaap:Assets rows are the balance-sheet substrate the "
                        "measured V9 vetoes (cash-level, WC-stock intensity, "
                        "Goodwill/bloat) were computed on; revenue/COGS tags are "
                        "measured here for the first time this cycle"},
            "measured_decision_stream": {
                "instants_ge5_strict_bars": built["SFV12-A6-H1"]["instants_ge5_strict_bars"],
                "census_groups_ge5_all_entities": C.s3_census["groups_ge5"],
                "defined_decisions_per_fold":
                    built["SFV12-A6-H1"]["decision_counts_defined_per_fold"],
                "note": "the defined-decision counts are the operative "
                        "coverage-first evidence: they measure fold-window vintage "
                        "coverage end-to-end on the declared stream"},
            "verdict": "FUNDED_CARRIED",
            "verdict_basis": "(1) the P2 gating rule requires the declared clock to "
                             "resolve to a funded clock_id - V12-S3 IS a funded "
                             "clock (p2 funded_clocks, verbatim record above); "
                             "(2) the panel-characteristic conditioners ride the "
                             "hash-pinned V9 panel, a carried durable asset "
                             "('carried_observables_still_funded_as_data' class); "
                             "(3) D2 directly measured the named fields present "
                             "with evidenced stamps on the bookable pool and a "
                             "populated defined-decision stream per fold (numbers "
                             "above) - coverage-first evidence, not prose; "
                             "(4) remaining field-level fold-window coverage at "
                             "full A8/A9 density stays with A9-F per the gating "
                             "rule, as the proposals themselves declare (their "
                             "'p2_field_coverage_failure' terminals). The clocks "
                             "are FUNDED; they are not UNFUNDED at P2.",
            "caveats": "the S3-instant decision stream is event-staggered and "
                       "asymmetric across entities vs the grid families; A9-F "
                       "still owns the cost-ceiling and full-density coverage "
                       "adjudication; no PnL exists anywhere in this audit",
        },
        "results": results,
        "verdict_rule": ("BLOCKED_NOVELTY if pooled |rho| > 0.20 vs any of the "
                         "THIRTEEN veto entries (fail-closed on null); "
                         "BLOCKED_IDENTIFIABILITY on the declared gates (A4 R1-R5, "
                         "per-date 0.30 on >= 90% dates; A5 per-date 0.30 share; "
                         "self-subsumption pooled |rho| > 0.98 kills pre-score for "
                         "ALL six); BLOCKED_CONTROL_DESIGN_FAILURE if a mandated "
                         "control cannot run (a control that cannot run is a "
                         "DESIGN FAILURE, not a pass); INFEASIBLE_DECISION_FLOORS "
                         "if scored-decision floors (>= 30 overall / >= 5 per fold) "
                         "fail; else ELIGIBLE on the D2 dimension - selection, "
                         "scoring and Stage-A remain A7+ decisions, not D2's"),
        "margins": "margin-to-threshold reported per veto entry (margin_to_020), "
                   "per identifiability gate, and per feasibility floor (P-2)",
        "no_pnl_no_outcomes": True,
        "no_pnl_assertion": "this audit contains rho/feasibility measurements "
                            "ONLY - no returns, no PnL, no selection, no scoring, "
                            "no outcome-shaped fields; a killed proposal is a "
                            "SUCCESS under the preregistered failure "
                            "interpretations",
    }
    out = json.dumps(audit, indent=1, sort_keys=True)
    return 0, out


# ---------------------------------------------------------------------------
def _synth_ctx():
    """Tiny deterministic synthetic fixture for --selfcheck (no staged data)."""
    class Ctx:
        pass
    C = Ctx()
    C.np = None
    C.folds = FOLDS_FALLBACK
    spy = [{"date": (date(2015, 1, 1) + timedelta(days=i)).isoformat(),
            "close": 100.0 + (i % 7) * 0.5} for i in range(2100)]
    C.sessions = [dd(r["date"]) for r in spy]
    C.sess_idx = {d: i for i, d in enumerate(C.sessions)}
    C.bookable = {"CIK0000000001": {"sector": "XLF", "ticker": "A1", "cls": "ALIVE_EVIDENCED"},
                  "CIK0000000002": {"sector": "XLF", "ticker": "B2", "cls": "DEAD_EVIDENCED"},
                  "CIK0000000003": {"sector": "XLK", "ticker": "C3", "cls": "ALIVE_EVIDENCED"}}
    C.p0d = {"CIK0000000002": {"verdict": "DEAD_PRICE_CONFIRMED", "death_date": "2019-06-03"}}
    C.series = {}
    for cik in C.bookable:
        base = 50.0 if cik != "CIK0000000003" else 80.0
        arr = [{"date": (date(2015, 1, 1) + timedelta(days=i)).isoformat(),
                "close": base + (i % 13) * 0.25,
                "adjusted_close": base + (i % 13) * 0.25,
                "volume": 1_000_000} for i in range(1700)]
        C.series[cik] = {"dates": [dd(r["date"]) for r in arr],
                         "close": [r["close"] for r in arr],
                         "adj": [r["adjusted_close"] for r in arr],
                         "vol": [r["volume"] for r in arr]}
    C.pre = {}
    for cik, s in C.series.items():
        adj = s["adj"]
        n = len(adj)
        s_lr = array("d", [0.0] * n)
        s_l2 = array("d", [0.0] * n)
        s_dn = array("d", [0.0] * n)
        ok = [False] * n
        for i in range(1, n):
            lr = math.log(adj[i] / adj[i - 1])
            ok[i] = True
            s_lr[i] = s_lr[i - 1] + lr
            s_l2[i] = s_l2[i - 1] + lr * lr
            s_dn[i] = s_dn[i - 1] + (lr * lr if lr < 0 else 0.0)
        C.pre[cik] = (s_lr, s_l2, s_dn, ok)
    # fields: annual revenue/cogs/assets for A6 + accounting vetoes
    C.fields = {}
    C.eff_groups = {}
    for cik in C.bookable:
        for y in range(2010, 2020):
            eff = f"{y}-12-31"
            av = f"{y + 1}-02-15"
            rev = 100.0 + y + (7 if cik == "CIK0000000002" else 0)
            cogs = rev * 0.6
            assets = 500.0 + y
            for f, v in (("us-gaap:Revenues", rev),
                         ("us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", rev * 0.9),
                         ("us-gaap:CostOfGoodsAndServicesSold", cogs),
                         ("us-gaap:CostOfRevenue", cogs * 0.95),
                         ("us-gaap:Assets", assets),
                         ("us-gaap:Goodwill", 10.0 + y),
                         ("us-gaap:RetainedEarningsAccumulatedDeficit", 5.0 + y),
                         ("us-gaap:CashAndCashEquivalentsAtCarryingValue", 20.0 + y)):
                C.fields.setdefault((cik, f), []).append((av, eff, float(v)))
    for k in C.fields:
        C.fields[k].sort()
    C.panel_field_stats = {}
    for (e, f), lst in C.fields.items():
        g = {}
        for av, eff, v in lst:
            g.setdefault(eff, []).append((av, v))
        C.eff_groups[(e, f)] = {k: sorted(v) for k, v in sorted(g.items())}
    # timing: own_z + filer events
    C.ownz = {cik: ([f"20{10 + i}-03-01" for i in range(8)], array("d", [0.1 * i for i in range(8)]))
              for cik in C.bookable}
    C.event_dates = {cik: [f"20{10 + i}-03-01" for i in range(8)] for cik in C.bookable}
    # benchmark closes (selfcheck-local; veto 13 residual denominator)
    C.bench = {"SPY": {d: 100.0 + i * 0.01 for i, d in enumerate(C.sessions)}}
    # revision: depth>=2 rows, semiannual (two per year)
    C.rev = {}
    for cik in C.bookable:
        rows = []
        i = 0
        for y in range(2010, 2020):
            for month in ("03", "09"):
                rows.append((f"{y + 1}-{month}-{10 + (i % 10):02d}",
                             2 + (i % 5), 200 + 40 * i, 0))
                i += 1
        rows.sort()
        C.rev[cik] = rows
    C.bread, C.late, C.deep, C.dsum = {}, {}, {}, {}
    for e, rows in C.rev.items():
        n = len(rows)
        avs = [r[0] for r in rows]
        ctot = array("i", [0] * n); cdn = array("i", [0] * n)
        t = dn = 0
        for i, r in enumerate(rows):
            t += 1; dn += 1 if r[3] == -1 else 0
            ctot[i] = t; cdn[i] = dn
        C.bread[e] = (avs, ctot, cdn)
        clate = array("i", [0] * n); cdeep = array("i", [0] * n); csum = array("l", [0] * n)
        la = de = sm = 0
        for i, r in enumerate(rows):
            la += 1 if r[2] > A5_LATE_IARR_CUT else 0
            de += 1 if r[1] >= 6 else 0
            sm += r[1]
            clate[i] = la; cdeep[i] = de; csum[i] = sm
        C.late[e] = (avs, ctot, clate)
        C.deep[e] = (avs, ctot, cdeep)
        C.dsum[e] = (avs, csum)
    C.rev_avails = {e: sorted({r[0] for r in rows}) for e, rows in C.rev.items()}
    C.grid21 = grid_dates(C, GRID_START, GRID_STEP)
    return C


def selfcheck() -> int:
    fails = []
    def check(name, cond, msg=""):
        if not cond:
            fails.append(f"{name}: {msg}")
    C = _synth_ctx()
    t0 = date(2019, 3, 4)
    check("momentum_finite", isinstance(veto_momentum(C, "CIK0000000001", t0), float),
          str(veto_momentum(C, "CIK0000000001", t0)))
    semi = veto_vol(C, "CIK0000000001", t0, "semi")
    check("semivariance_in_01", semi is not None and 0.0 <= semi <= 1.0, str(semi))
    check("vol_finite", isinstance(veto_vol(C, "CIK0000000001", t0, "vol"), float))
    check("goodwill_ratio", veto_ratio(C, "CIK0000000001", t0, "us-gaap:Goodwill") is not None)
    check("depletion_defined", veto_depletion(C, "CIK0000000001", t0) is not None)
    check("own_z_in_window", veto_own_z(C, "CIK0000000001", t0) is not None)
    check("breadth_in_01", 0.0 <= (veto_breadth(C, "CIK0000000001", t0) or 0.0) <= 1.0)
    check("cadence_in_01", 0.0 <= (veto_cadence(C, "CIK0000000001", t0) or 0.0) <= 1.0)
    check("reaction_sign", veto_filing_reaction(C, "CIK0000000001", t0) in (-1, 0, 1))
    t1 = date(2020, 6, 1)  # later instant: the 800d window holds 4 semiannual rows
    w = a4_walk(C, "CIK0000000002", t1)
    check("a4_walk_n", w is not None and w["n"] >= MIN_GROUPS_Q, str(w))
    check("a4_walk_median", w and w["median"] in (2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6),
          str(w and w["median"]))
    # A5 pairing on synthetic: 1 dead, 1 alive in XLF
    pairs, unmapped, hosts = _pair_sham_pairs(C)
    check("pairing_shape", len(pairs) == 1 and hosts == 1 and unmapped == 0,
          f"{pairs} {hosts} {unmapped}")
    # A6 builder smoke
    b = build_a6(C, "SFV12-A6-H1")
    check("a6_decisions", len(b["anchor"]) >= 5, str(len(b["anchor"])))
    for (e, t), v in sorted(b["anchor"].items())[:3]:
        check("a6_value_finite", isinstance(v, float) and math.isfinite(v), f"{e} {t} {v}")
    # A5-H1 builder smoke
    b51 = build_a5_h1(C)
    check("a5h1_trigger", "CIK0000000002" in b51["triggers"])
    check("a5h1_class", b51["triggers"]["CIK0000000002"]["class"] in (-1, 1))
    check("a5h1_weights", len(b51["anchor_w"]) > 0)
    # spearman sanity: perfect monotone
    check("spearman_perfect", abs(spearman(list(range(20)), [2 * x for x in range(20)]) - 1.0) < 1e-9)
    check("spearman_inverse", abs(spearman(list(range(20)), [-x for x in range(20)]) + 1.0) < 1e-9)
    if fails:
        for f in fails:
            print("SELFCHECK FAIL:", f, file=sys.stderr)
        return 1
    print("selfcheck OK")
    return 0


def main(argv):
    if "--selfcheck" in argv:
        return selfcheck()
    if len(argv) < 3:
        sys.stderr.write("usage: d2_v12_novelty_measure.py <built_at_utc> <out_path>\n")
        return 64
    built_at, out_path = argv[1], argv[2]
    rc = run_full(built_at)
    if isinstance(rc, tuple):
        rc, payload = rc
    else:
        return rc
    with open(out_path, "w") as fh:
        fh.write(payload)
    print(f"[d2] wrote {out_path} ({len(payload)} bytes)", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
