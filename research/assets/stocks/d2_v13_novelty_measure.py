"""STOCKS-FREE-V13 D2 novelty + identifiability measurement MACHINE
(D2 machine-preparation lane, cycle STOCKS-FREE-V13).

ADAPTED FROM: the V12 D2 module (worktree-local untracked reference
d2_v12_reference.py, itself adapted from d2_v11_novelty_measure.py @ 9d3a0612).
The V12 skeleton is carried wholesale: as-of engines, panel/prices streaming,
midrank Spearman, novelty_block with per-entry margin_to_020, fail-closed
novelty on unmeasured vetoes, and the determinism contract (the ONLY
wall-clock input is built_at_utc; two passes at the same built_at_utc are
byte-identical: sort_keys=True, every cross-entity sequence iterated in
sorted order). Disclosure: this is a NEW cycle-specific V13 machine.

WHAT IS NEW VS THE V12 MODULE (the only deltas):
  1. The veto set grows THIRTEEN -> FIFTEEN. The 13 V12 builders are carried
     UNCHANGED in semantics. Two NEW veto builders lift the V12-KILLED
     proposal forms (their definitions live in the V12 module as proposal
     anchor handlers, lifted here verbatim in semantics):
       - "v12_chain_structure_form" (veto 14): the SFV12-A4-H1 DEPTH-STRAIN
         anchor deep_share(e,t) = |{g in Q(e,t): depth(g) >= 6}| / |Q(e,t)|
         over the depth>=2 staged revision-layer groups, defined iff
         |Q| >= 4 (V12 rho-contaminated 0.5822/0.2085 vs the V11 shadow).
       - "v12_death_event_form" (veto 15): the SFV12-A5-H1 FINALQ-CONTAGION
         anchor exposure (sector-peer death-event leg weight; V12
         anchor-vs-sham self-subsumption 0.9923).
     This is the D1 selection_rubric.json measured set verbatim: "the
     V12-module 13 veto builders PLUS the two V12-killed proposal forms as
     veto builders = 15 measured exposures, a strictly conservative superset
     of the plan's fourteen-entry veto set (filing-event reaction carried as
     its own measured shadow, as in V12's D2)".
  2. PATHS block: all heavy inputs stay at the EXISTING prior-cycle staging
     (V9 panel/prices/cohort/p0d, V10 timing/revision observables - byte pins
     re-verified this cycle, P2 4/4 MATCH). The V13 OUTPUT dir is
     research/control/stocks_free_v13_run/audits/ IN THIS WORKTREE. Form-4
     submissions staging: V13 alive dir (.staging_sec_v13/submissions_alive,
     fetching at machine-build time) + the V9 dead cache
     (.staging_sec_v9/submissions_dead), read by the shared loader
     load_form4_acceptances().
  3. PROPOSAL_EXPOSURE_BUILDERS registry (empty at machine-build time) with a
     documented extension contract and one worked example handler for a
     hypothetical insider proposal. The example's transaction-direction term
     is NOT computable from the staged submissions JSON (direction lives in
     the Form-4 XML, not yet staged) - it is marked XML_INGEST_REQUIRED and
     uses a FILING-LEVEL COUNT placeholder only. No direction data is faked.
  4. --selfcheck mode (mandatory, carries the INC-V-V12-4 fromisoformat
     lesson): imports the module fresh, builds a 5-entity x 3-date synthetic
     in-memory fixture (monkeypatched C-dict, zero staged data), asserts all
     FIFTEEN veto builders return a float or None without exceptions, and
     checks the midrank Spearman on known-answer fixtures (rho(x, x) = 1.0,
     rho(x, reversed) = -1.0, tie case against the exact closed form, plus
     the n >= 10 and zero-variance abstentions), the registry plumbing, the
     Form-4 loader against both submissions shapes (columnar dead-cache and
     row-list), and an in-process determinism x2 table check.

DISCIPLINE: feature/rank arithmetic only - zero PnL, zero returns, zero
selection, zero scoring. This lane BUILDS AND SELFCHECKS the machine only; it
runs NO measurement against real data (no network, no full panel pass). D2
execution happens later under A1: the proposal handlers get registered into
PROPOSAL_EXPOSURE_BUILDERS and the heavy path runs under the machine-wide
heavy lock. Until then run_full() refuses to run (exit 3, fail-closed) on the
empty registry - an empty measurement is never written.

Usage:
  d2_v13_novelty_measure.py --selfcheck
  d2_v13_novelty_measure.py <built_at_utc> <out_path>   (A1 execution lane)

Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python ONLY.
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

# ===========================================================================
# PATHS (V13 D2 machine)
# ===========================================================================
# Repo root of THIS worktree (the module lives at
# research/assets/stocks/d2_v13_novelty_measure.py under it).
REPO_ROOT = Path(__file__).resolve().parents[3]

# ---- prior-cycle heavy inputs (EXISTING staging; byte-pinned, P2 4/4 MATCH)
V9 = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/integration")
V10 = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v10/integration")
V13_INTEG = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13/integration")

PRICES = V9 / ".staging_prices_v9/eod"
BENCH = V9 / ".staging_prices_v9/benchmarks"
PANEL = V9 / ".staging_sec_v9/multivintage_panel.jsonl"
COHORT = V9 / "research/control/stocks_free_v9_run/cohort_v9.json"
P0D = V9 / "research/control/stocks_free_v9_run/p0d_v9_integrity_scan.json"
TIMING = V10 / ".staging_sec_v10/v10_timing_observables.jsonl"
REVISION = V10 / ".staging_sec_v10/v10_revision_observables.jsonl"
V10_P0_MANIFEST = V10 / "research/control/stocks_free_v10_run/p0_v10_observable_manifest.json"
P3_V13 = V13_INTEG / "research/control/stocks_free_v13_run/p3_v13_invariants_freeze.json"

# ---- Form-4 submissions staging (insider lane inputs; plain JSON, no gzip)
FORM4_ALIVE_DIR = V13_INTEG / ".staging_sec_v13/submissions_alive"   # V13 fetch (alive)
FORM4_DEAD_DIR = V9 / ".staging_sec_v9/submissions_dead"             # V9 dead cache

# ---- V13 OUTPUT dir (this worktree; created by the A1 execution lane)
V13_OUT = REPO_ROOT / "research/control/stocks_free_v13_run/audits"

# ---- carried input integrity pins (bytes verified before any measurement;
#      the same four sha256 pins the V13 P2 pin-rehash verified MATCH)
PIN_EXPECTED = {
    "panel": "67591464ee49acc159886143a379bda5890b1df602818b600d7938df92af1447",
    "cohort_v9": "6a95401ff84bff2144ac3c0b9426a6fa86daf3dde8d478195666249e3fa2aa62",
    "v10_timing_observables": "b1477ea39b8b794b7f32162cb349ff53fdd1a37b9a64d0ee20e77412ae802337",
    "v10_revision_observables": "7110cbf010ae6d3f414a1a45eec1e504aff5e94464755991e98605e4795657c2",
}
PIN_PATHS = {
    "panel": PANEL,
    "cohort_v9": COHORT,
    "v10_timing_observables": TIMING,
    "v10_revision_observables": REVISION,
}

# ===========================================================================
# constants (V12 skeleton carried; cycle identifiers V13)
# ===========================================================================
STALE_DAYS = 800
CYCLE = "STOCKS-FREE-V13"
BASE_SHA = "c7995e160fd16fc020bb9b09e1d9205794466353"   # D1 selection-rubric freeze commit
NOVELTY_BAR = 0.20
SELF_SUBSUMPTION_RHO = 0.98   # V15 lesson; pre-score kill, carried
A4_R1_DATE_RHO = 0.30         # per-date identifiability gate (V12 skeleton)
A4_DATE_PASS_SHARE = 0.90
MIN_GROUPS_Q = 4              # chain-structure form defined iff |Q| >= 4
GRID_START = 63               # fold-local grid: session index 63 + 21k
GRID_STEP = 21
A5_GAP_CUT = 10               # death-event form: ORDERLY <= 10 / GAPPED >= 11
A5_LATE_IARR_CUT = 460        # veto 12: inter_arrival_days > 460 (V11 form)
REACTION_STALE_DAYS = 800     # veto 13 state staleness (uniform bound)
# rubric-declared feasibility ceilings (adjudicated per proposal at A9-F;
# reported here as constants only - no PnL arithmetic exists in this module)
TURNOVER_CEILING_BPS_QTR = 200

REV_DIR_ENCODING = {1: "up", 0: "flat", -1: "down"}

FOLDS_FALLBACK = [
    {"fold_id": "S0_FOLD_1", "start": "2018-04-04", "end": "2020-09-01"},
    {"fold_id": "S0_FOLD_2", "start": "2020-09-10", "end": "2023-02-09"},
    {"fold_id": "S0_FOLD_3", "start": "2023-02-17", "end": "2025-07-24"},
]

# FIFTEEN-entry measured veto set. Entries 1-13 are the V12 module's veto set
# carried UNCHANGED in semantics; entries 14-15 are the V12-killed proposal
# forms lifted as veto builders. Per the D1 selection rubric this is a
# strictly conservative superset of the plan's fourteen-entry inventory.
VETO_NAMES = [
    "momentum_63s",                    # 1 momentum (V2; V11-measured blocker)
    "semivariance_share",              # 2
    "vol_level",                       # 3
    "wc_stock_intensity",              # 4
    "goodwill_bloat",                  # 5
    "f1_accrual_flow",                 # 6
    "depletion_interaction",           # 7
    "cash_level",                      # 8
    "sector_exposure_form",            # 9
    "own_z_characteristic_form",       # 10 V10 deseasonalized-timing own_z
    "revision_direction_breadth_form", # 11 V10 revision direction/breadth
    "v11_cadence_latency_form",        # 12 V11 amendment cadence-latency
    "filing_event_reaction_shadow",    # 13 filing-event reaction (momentum_63s shadow)
    "v12_chain_structure_form",        # 14 V12-killed SFV12-A4-H1 deep_share anchor form
    "v12_death_event_form",            # 15 V12-killed SFV12-A5-H1 sector-peer death-event form
]

# accounting veto fields (V10 form, unchanged from the V12 skeleton)
NEEDED_FIELDS = [
    "us-gaap:AssetsCurrent", "us-gaap:LiabilitiesCurrent",
    "us-gaap:Goodwill", "us-gaap:Assets",
    "us-gaap:CashAndCashEquivalentsAtCarryingValue",
    "us-gaap:RetainedEarningsAccumulatedDeficit",
    "us-gaap:AccountsReceivableNetCurrent", "us-gaap:InventoryNet",
    "us-gaap:AccountsPayableCurrent",
]
SECTOR_ETFS = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]


# ===========================================================================
# small helpers (V12 skeleton, verbatim)
# ===========================================================================
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


# ===========================================================================
# Form-4 submissions loader (shared; insider lane input)
# ===========================================================================
def _cik_key(doc, path):
    """Entity key 'CIK##########' from the document's cik field, falling back
    to the CIK##########.json filename digits. None if neither parses."""
    raw = doc.get("cik") if isinstance(doc, dict) else None
    if raw is not None:
        digits = "".join(ch for ch in str(raw) if ch.isdigit())
        if digits:
            return f"CIK{int(digits):010d}"
    digits = "".join(ch for ch in path.stem if ch.isdigit())
    if digits:
        return f"CIK{int(digits):010d}"
    return None


def load_form4_acceptances(alive_dir=None, dead_dir=None):
    """Shared Form-4 acceptance loader over BOTH staged submissions dirs.

    Reads FORM4_DEAD_DIR (the V9 dead cache) and FORM4_ALIVE_DIR (the V13
    alive fetch, landing at .staging_sec_v13/submissions_alive/), and returns
        {cik: [(filing_date, acceptance_dt), ...]}
    for form == '4' rows only. Plain JSON files (gzip not needed). Handles
    BOTH observed submissions shapes:
      - columnar (V9 dead cache): filings.recent is a dict of parallel arrays
        (form / filingDate / acceptanceDateTime / ...);
      - row-list (standard SEC submissions shape): filings.recent is a list
        of row dicts.
    acceptanceDateTime is the authoritative acceptance timestamp; filingDate
    is carried alongside it. Rows with a missing acceptanceDateTime are kept
    with "" (never substituted, never inferred). Both dirs are merged and
    deduplicated per CIK; each CIK's list is sorted (filing_date,
    acceptance_dt) for determinism. Raw strings only - NO date parsing here;
    the PIT binding (as-of joins, prev-decision windows) is the caller's job.
    """
    alive_dir = FORM4_ALIVE_DIR if alive_dir is None else Path(alive_dir)
    dead_dir = FORM4_DEAD_DIR if dead_dir is None else Path(dead_dir)
    out = {}
    for d in (dead_dir, alive_dir):   # deterministic dir order
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.json")):
            try:
                doc = json.loads(p.read_text())
            except Exception:
                continue
            cik = _cik_key(doc, p)
            if cik is None:
                continue
            recent = (doc.get("filings") or {}).get("recent") or []
            rows = []
            if isinstance(recent, dict):
                forms = recent.get("form") or []
                fds = recent.get("filingDate") or []
                ads = recent.get("acceptanceDateTime") or []
                for i in range(len(forms)):
                    if str(forms[i]) != "4":
                        continue
                    fd = fds[i] if i < len(fds) else ""
                    ad = ads[i] if i < len(ads) else ""
                    rows.append((str(fd), "" if ad is None else str(ad)))
            elif isinstance(recent, list):
                for r in recent:
                    if not isinstance(r, dict) or str(r.get("form")) != "4":
                        continue
                    fd = str(r.get("filingDate") or "")
                    ad = r.get("acceptanceDateTime")
                    rows.append((fd, "" if ad is None else str(ad)))
            if rows:
                out.setdefault(cik, set()).update(rows)
    return {c: sorted(v) for c, v in sorted(out.items())}


# ===========================================================================
# context loading (heavy path - run under the machine-wide heavy lock)
# ===========================================================================
def load_context():
    class Ctx:
        pass

    C = Ctx()

    # ---- input integrity pins (bytes verified before any measurement) ------
    pins = {}
    for k, p in PIN_PATHS.items():
        pins[k] = file_sha256(p)
    C.pins = {k: {"sha256": pins[k], "expected": PIN_EXPECTED[k]} for k in sorted(PIN_PATHS)}
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

    # ---- frozen folds (V13 P3 book_folds_carried; fallback = V9 folds) -----
    try:
        folds = json.loads(P3_V13.read_text())["carried_payload"]["book_folds_carried"]
    except Exception:
        folds = FOLDS_FALLBACK
    C.folds = folds

    # ---- global trading calendar from SPY ----------------------------------
    spy = json.loads((BENCH / "SPY.json").read_text())
    sessions = [dd(r["date"]) for r in sorted(spy, key=lambda r: r["date"])]
    C.sessions = sessions
    C.sess_idx = {d: i for i, d in enumerate(sessions)}

    # ---- priced bookable entities (files kept at ANY length: the pairing
    # arithmetic needs first_bar_date of every priced entity, census semantics)
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

    # ---- panel: accounting veto fields + per-entity as-of field streams ----
    print("[d2] streaming panel for veto fields...", flush=True)
    fields = {}            # (e, f) -> sorted [(avail, eff, v)]
    panel_field_stats = {}  # f -> {"rows": n, "entities": set()}
    want = set(NEEDED_FIELDS)
    with open(PANEL, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            e, f = r["e"], r["f"]
            if e in C.bookable and f in want and isinstance(r["v"], (int, float)):
                fields.setdefault((e, f), []).append((r["avail"], r["eff"], float(r["v"])))
                st = panel_field_stats.setdefault(f, {"rows": 0, "entities": set()})
                st["rows"] += 1
                st["entities"].add(e)
    for k in fields:
        fields[k].sort()
    C.fields = fields
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

    # ---- revision layer: depth>=2 groups (vetoes 11/12/14) ------------------
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
    # per-entity prefix arrays: total / down / late(iarr>460) / deep(depth>=6)
    C.bread, C.late, C.deep = {}, {}, {}
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
        clate = array("i", [0] * n); cdeep = array("i", [0] * n)
        la = de = 0
        for i, r in enumerate(rows):
            la += 1 if r[2] > A5_LATE_IARR_CUT else 0
            de += 1 if r[1] >= 6 else 0
            clate[i] = la; cdeep[i] = de
        C.late[e] = (avs, ctot, clate)
        C.deep[e] = (avs, ctot, cdeep)

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
# VETO ENGINE - FIFTEEN entries. 1-13 are the V12 builders carried UNCHANGED
# in semantics (verbatim adaptation). 14 = v12_chain_structure_form, 15 =
# v12_death_event_form (the V12-killed proposal anchor forms). Each builder:
# (C, e, t) -> float value, or None = UNMEASURED (novelty fails closed).
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


def veto_sector_form(C, e, t):
    """Veto 9 - sector equal-weight mean of the 63s momentum cross-section at t.
    (Cache lives on the context, so multiple contexts never collide.)"""
    sec = C.bookable.get(e, {}).get("sector", "")
    cache = getattr(C, "_sector_cache", None)
    if cache is None:
        cache = C._sector_cache = {}
    key = (sec, t.isoformat())
    if key in cache:
        return cache[key]
    vals = []
    for e2 in sorted(C.series):
        if C.bookable.get(e2, {}).get("sector", "") != sec:
            continue
        v = veto_momentum(C, e2, t)
        if v is not None:
            vals.append(v)
    out = (sum(vals) / len(vals)) if vals else None
    cache[key] = out
    return out


def veto_own_z(C, e, t):
    """Veto 10 - V10 deseasonalized-timing own_z characteristic form (V12 form
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
    """Veto 11 - V10 revision direction/breadth form (V12 form unchanged):
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
    """Veto 12 - V11 amendment cadence-latency form: share of in-window
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
    """Veto 13 - filing-event reaction event-time space, operationalized as the
    momentum_63s-shaped reaction shadow that V11 D2 measured rho-blocked: the
    sign of the 5-bar SPY-residual initial reaction at the entity's most
    recent evidenced filer-event arrival with arrival < t and
    t - arrival <= 800d; None if no qualifying arrival or the reaction
    abstained-with-reason (counted against measurement). (Value semantics
    identical to V12; the sign is normalized to float.)"""
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
    cache = getattr(C, "_reaction_cache", None)
    if cache is None:
        cache = C._reaction_cache = {}
    key = (e, a)
    if key not in cache:
        sign, _entry, _why = residual_reaction(C, e, dd(a), "SPY")
        cache[key] = None if sign is None else float(sign)
    return cache[key]


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


# ---------------------------------------------------------------------------
# vetoes 14-15: the V12-KILLED proposal forms, lifted verbatim in semantics
# ---------------------------------------------------------------------------
def a4_walk(C, e, t):
    """One window walk per (entity, decision) pair over Q(e,t) = depth>=2
    revision-layer groups with last_avail < t (strict) and
    0 <= t - last_avail <= 800d. Returns dict with |Q|, deep_count(>=6),
    sum depth, max depth, median depth; None if |Q| == 0.
    (Verbatim lift of the V12 SFV12-A4 window-walk engine - the shared
    substrate of veto 14 and of the V12 A4 family's anchor arithmetic.)"""
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


def veto_chain_deep_share(C, e, t):
    """Veto 14 - v12_chain_structure_form. The V12-killed SFV12-A4-H1
    DEPTH-STRAIN anchor, verbatim in semantics:
        deep_share(e,t) = |{g in Q(e,t): depth(g) >= 6}| / |Q(e,t)|
    where Q(e,t) = the chain groups of e in the staged revision layer
    (.staging_sec_v10/v10_revision_observables.jsonl) with last_avail < t
    (strict) and 0 <= t - last_avail <= 800d; DEFINED IFF |Q| >= MIN_GROUPS_Q
    (= 4), else None. (V12 measured this form rho-contaminated
    0.5822/0.2085 vs the V11 shadow - it is a veto since V13.)"""
    w = a4_walk(C, e, t)
    if w is None or w["n"] < MIN_GROUPS_Q:
        return None
    return w["deep"] / w["n"]


def build_death_event_anchor(C):
    """Sector-peer death-event leg weights - the V12-killed SFV12-A5-H1
    FINALQ-CONTAGION declared anchor exposure (i), lifted verbatim in
    semantics from the V12 module's A5-H1 anchor path (the sham/matched-subset
    machinery was proposal-scoring apparatus and is NOT part of the exposure
    definition; the anchor leg only is lifted):

      Trigger set = DEAD_PRICE_CONFIRMED (priced, evidenced death date, last
      bar <= death date within 800d, mapped sector). Class at (trigger,
      arrival): gap_days = T - last bar <= T within 800d; ORDERLY (+1) iff
      gap_days <= 10, else GAPPED (-1).

      Per-entity net leg weight: dedup (sector, class, death-date); the
      equal-weight basket of mapped ALIVE_EVIDENCED priced peers with >= 63
      bars through the event date, EXCLUDING the event's own names (the dying
      name is never held); each peer gets class / |basket|; concurrent events
      accumulate.

    Returns {"weights": {(e, event_date): net_weight}, "triggers": n,
             "events_defined": n, "excluded": {...}}. Deterministic: all
    iteration in sorted order; no RNG."""
    events = []
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
        cls = 1 if gap <= A5_GAP_CUT else -1
        sec = C.bookable[e]["sector"]
        if not sec:
            excl["unmapped_sector"] += 1
            continue
        events.append((T, sec, cls, e))

    def baskets_at(date_t, sec):
        out = []
        for p in sorted(C.bookable):
            if C.bookable[p]["cls"] != "ALIVE_EVIDENCED" or C.bookable[p]["sector"] != sec:
                continue
            if not has_bars(C, p, date_t):
                continue
            out.append(p)
        return out

    groups = {}
    for T, sec, cls, name in events:
        groups.setdefault((sec, cls, T), []).append(name)
    weights = {}
    n_ev = 0
    for (sec, cls, T), names in sorted(groups.items(),
                                       key=lambda kv: (kv[0][2], kv[0][0], kv[0][1])):
        bsk = [p for p in baskets_at(T, sec) if p not in set(names)]
        n_ev += 1
        if not bsk:
            continue
        wgt = float(cls) / len(bsk)
        for p in bsk:
            weights[(p, T)] = weights.get((p, T), 0.0) + wgt
    return {"weights": weights, "triggers": len(events),
            "events_defined": n_ev, "excluded": excl}


def veto_death_event_form(C, e, t):
    """Veto 15 - v12_death_event_form. The V12-killed SFV12-A5-H1 sector-peer
    death-event anchor exposure, evaluated at (e, t): the net leg weight of
    entity e at event date t under build_death_event_anchor(C); None where no
    event leg is booked at (e, t). Weights are built once per context and
    cached on it (deterministic construction, see build_death_event_anchor).
    (V12 measured this form's anchor-vs-sham self-subsumption at 0.9923 -
    the sham control is indistinguishable from the anchor, so the form is a
    veto since V13.)"""
    w = getattr(C, "_death_form_weights", None)
    if w is None:
        w = C._death_form_weights = build_death_event_anchor(C)["weights"]
    return w.get((e, t))


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
    "v12_chain_structure_form": lambda C, e, t: veto_chain_deep_share(C, e, t),
    "v12_death_event_form": lambda C, e, t: veto_death_event_form(C, e, t),
}


# ===========================================================================
# PROPOSAL EXPOSURE BUILDER REGISTRY (V13 extension point)
# ===========================================================================
# REGISTRY CONTRACT
#   PROPOSAL_EXPOSURE_BUILDERS: {proposal_id: handler}
#   handler(C) -> anchor exposure dict {(entity_cik, decision_date): float}
#   - keys are (entity, decision-instant) pairs on the bookable pool, at the
#     proposal's OWN decision instants (grid, event-anchored, or staged);
#   - values are the DECLARED conditioning exposures exactly as the
#     proposal's exposure_definition states them (raw values, no
#     standardization, no returns, no PnL);
#   - the handler must be deterministic (sorted iteration; no wall clock, no
#     RNG unless the proposal freezes seeds and the redraft order);
#   - run_full() measures each registered handler with novelty_block: pooled
#     midrank Spearman vs EVERY one of the 15 veto builders on common pairs,
#     bar |rho| <= 0.20, FAIL-CLOSED on any unmeasured veto.
#
# The registry ships EMPTY: D2 execution happens under A1, after the
# insider/macro proposal handlers exist against their staged inputs
# (Form-4 submissions/XML; macro vintages). An unregistered run refuses to
# measure (see run_full) - an empty measurement is never written.
PROPOSAL_EXPOSURE_BUILDERS = {}


def example_insider_buy_pressure(C):
    """WORKED EXAMPLE - NOT REGISTERED (registry ships empty).

    Documented worked example for a HYPOTHETICAL insider proposal handler:
    the declared form is

        buy_pressure(e,t) = sum over Form-4 acceptances a of issuer e with
        prev_decision_date < a <= decision_date of
            (non-derivative-table G-code buys) - (non-derivative-table sells)

    where A(e,t) = the issuer's Form-4 acceptances from
    load_form4_acceptances() (V13 alive dir + V9 dead cache), and
    prev_decision_date is the previous decision date on the proposal's own
    grid (the first grid date has no predecessor: its exposure is undefined
    and abstains).

    XML_INGEST_REQUIRED - READ THIS BEFORE TRUSTING ANY NUMBER OUT OF THIS
    HANDLER: transaction-level direction (the G-code buys/sells split, and
    the non-derivative vs derivative table attribution) lives in the Form-4
    XML ownership documents (filings.primaryDocument -> ownership.xml), which
    are NOT STAGED YET. The submissions JSON carries only form / filingDate /
    acceptanceDateTime per row. This example therefore uses the FILING-LEVEL
    ACCEPTANCE COUNT as a PLACEHOLDER exposure:

        placeholder(e,t) = |{a in A(e,t): prev_decision_date < a.acceptance
                              <= decision_date}|

    and MUST NOT be read as a signed buy-pressure measure. Do NOT fake
    direction data; the signed form is registered only after the Form-4 XML
    ingest lands in V13 staging. Placeholder value semantics: float count
    (unsigned, monotone in filing activity) - enough to exercise the veto
    machinery end-to-end, not enough to claim the insider mechanism.
    """
    form4 = getattr(C, "form4", None)
    if form4 is None:
        return None   # loader not wired onto the context: abstain, never guess
    dates = grid_dates_flat(C, C.grid21)
    out = {}
    for e in sorted(C.series):
        accs = form4.get(e, [])
        for i, t in enumerate(dates):
            if i == 0:
                continue   # prev_decision_date undefined at the first grid date
            prev = dates[i - 1].isoformat()
            t_iso = t.isoformat()
            # PLACEHOLDER: filing-level acceptance count in (prev, t].
            # XML_INGEST_REQUIRED for the signed G-code buys-minus-sells form.
            n = sum(1 for fd, ad in accs
                    if prev < (ad or fd) <= t_iso)
            out[(e, t)] = float(n)
    return out


# ===========================================================================
# CORRELATION + VERDICTS (V12 skeleton, verbatim)
# ===========================================================================
def novelty_block(C, anchor):
    """Pooled midrank Spearman of the anchor exposure vs EVERY veto entry on
    common (entity, decision-instant) pairs; bar pooled |rho| <= 0.20; a null
    entry (n < 10, zero variance, or the veto itself unmeasured at the pair)
    FAILS the gate - fail-closed, never a pass by absence."""
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
    """Per-date (book-level) aggregate of leg weights."""
    out = {}
    for (_e, t), w in a.items():
        out[t] = out.get(t, 0.0) + w
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


def identifiability_anchor_vs_control(C, anchor, control, ctrl_gate,
                                      per_date_gate=None, date_pass_share=None):
    """Generic anchor-vs-control identifiability for a registered proposal
    (the A1 lane supplies anchor and control exposure dicts and the
    proposal's DECLARED ctrl_gate). Measured:
      - pooled |rho| vs the declared ctrl_gate; the self-subsumption kill at
        |rho| > SELF_SUBSUMPTION_RHO (0.98) is binding pre-score for ALL
        proposals (V15 lesson, carried);
      - per-date rho stats vs per_date_gate (default: the proposal's
        ctrl_gate) at the A4_R1_DATE_RHO / A4_DATE_PASS_SHARE convention.
    A control that cannot be constructed (empty control dict) is a DESIGN
    FAILURE, not a pass."""
    out = {"declared_ctrl_gate": ctrl_gate,
           "gate_self_subsumption_rho": SELF_SUBSUMPTION_RHO}
    if not control:
        out["verdict"] = "BLOCKED_CONTROL_DESIGN_FAILURE"
        out["control_pairs"] = 0
        return out
    pooled, n = rho_on_common(anchor, control)
    out["pooled_anchor_vs_control_rho"] = None if pooled is None else round(pooled, 4)
    out["control_pairs"] = n
    if pooled is not None:
        out["self_subsumption_kill"] = bool(abs(pooled) > SELF_SUBSUMPTION_RHO)
    dg = A4_R1_DATE_RHO if per_date_gate is None else per_date_gate
    sh = A4_DATE_PASS_SHARE if date_pass_share is None else date_pass_share
    stats = per_date_rho_stats(C, anchor, control, sorted({t for _e, t in anchor}), dg)
    out["per_date"] = stats
    gate_ok = stats is not None and stats["share_dates_abs_le_gate"] >= sh
    out["per_date_gate_pass"] = bool(gate_ok)
    out["verdict"] = ("BLOCKED_SELF_SUBSUMPTION" if out.get("self_subsumption_kill")
                      else ("PASS" if gate_ok and pooled is not None
                            and abs(pooled) < ctrl_gate
                            else "BLOCKED_CONTROL_UNIDENTIFIABLE"))
    return out


# ===========================================================================
# MAIN (heavy run - A1 execution lane) + SELFCHECK
# ===========================================================================
CONVENTIONS = {
    "global": [
        "adapted from the V12 D2 module (untracked worktree reference; itself "
        "adapted from d2_v11_novelty_measure.py @ 9d3a0612); V13-specific: "
        "FIFTEEN-entry veto set (13 carried + the two V12-killed proposal "
        "forms as builders), PROPOSAL_EXPOSURE_BUILDERS registry, shared "
        "Form-4 acceptance loader over the V13 alive + V9 dead staging",
        "Spearman midrank ties, pooled on common (entity, decision-instant) "
        "pairs; n >= 10 per comparison else None; novelty fail-closed (a null "
        "veto entry fails the gate, never passes open)",
        "veto values evaluated at the proposal's own decision instants, "
        "including event-anchored dates (vetoes 1-13 in the inherited "
        "V10/V11/V12 form; veto 14 = the SFV12-A4-H1 deep_share anchor over "
        "Q(e,t), defined iff |Q| >= 4; veto 15 = the SFV12-A5-H1 sector-peer "
        "death-event net leg weight at (e, t))",
        "rev_dir encoding -1=down / 0=flat / 1=up fail-closed verified against "
        "the V10 P0 manifest dir_counts at load",
        "gate(t) semantics: date-only stamps; last_avail < decision date "
        "(strict); staleness 0 <= t - last_avail <= 800d; avail stamps take "
        "the conservative LATER bound",
        "63-bar pre-check floor uses staged price bar counts only; NO band "
        "computation, NO ADV, NO returns anywhere",
        "universe = ALIVE_EVIDENCED + DEAD_EVIDENCED cohort legs (bookable "
        "pool); priced = has staged EOD file (any length)",
        "control identifiability self-subsumption kill at pooled |rho| > 0.98 "
        "(V15 lesson; binding pre-score for every registered proposal)",
        "determinism: the only wall-clock input is built_at_utc; two passes "
        "at the same built_at_utc are byte-identical (sort_keys=True, sorted "
        "cross-entity iteration, frozen or sorted-order randomness only)",
    ],
    "new_veto_forms": {
        "v12_chain_structure_form": [
            "deep_share(e,t) = |{g in Q(e,t): depth(g) >= 6}| / |Q(e,t)|; "
            "Q = depth>=2 chain groups of e in the staged revision layer with "
            "last_avail < t strict and 0 <= t - last_avail <= 800d; defined "
            "iff |Q| >= 4 (MIN_GROUPS_Q), else None (fail-closed)",
            "lifted from the V12 SFV12-A4-H1 DEPTH-STRAIN anchor handler "
            "(a4_walk engine carried verbatim); V12 measured this form "
            "rho-contaminated 0.5822/0.2085 vs the V11 filing-reaction shadow",
        ],
        "v12_death_event_form": [
            "net sector-peer death-event leg weight at (e, t): triggers = "
            "DEAD_PRICE_CONFIRMED priced with a bar <= death date within 800d "
            "and a mapped sector; class ORDERLY +1 (gap_days <= 10) / GAPPED "
            "-1; dedup (sector, class, death-date); equal-weight basket of "
            "mapped ALIVE_EVIDENCED priced peers with >= 63 bars through the "
            "event date, dying name never held; concurrent events accumulate",
            "lifted from the V12 SFV12-A5-H1 FINALQ-CONTAGION anchor path; "
            "the V12 sham/matched-subset machinery was proposal-scoring "
            "apparatus and is not part of the exposure definition; V12 "
            "measured anchor-vs-sham self-subsumption 0.9923",
        ],
    },
    "registry": [
        "PROPOSAL_EXPOSURE_BUILDERS ships EMPTY; D2 execution under A1 "
        "registers handlers with contract handler(C) -> {(e, t): float} and "
        "run_full measures each with novelty_block (fail-closed on the 15 "
        "vetoes) + identifiability_anchor_vs_control with the proposal's "
        "declared ctrl_gate",
        "the documented worked example (example_insider_buy_pressure) uses a "
        "FILING-LEVEL acceptance-count placeholder; the declared signed form "
        "(non-derivative-table G-code buys minus sells) requires the Form-4 "
        "XML ingest and is marked XML_INGEST_REQUIRED - direction data is "
        "never faked",
    ],
}


def run_full(built_at_utc):
    """Heavy measurement path (A1 execution lane, machine-wide heavy lock).

    Refuses to run on the empty registry (exit 3): this lane built and
    selfchecked the MACHINE; a run with zero registered handlers would write
    an empty measurement, and an empty measurement is never written. When A1
    registers handlers, each is measured with novelty_block against all 15
    vetoes; determinism contract: two passes at the same built_at_utc are
    byte-identical."""
    if not PROPOSAL_EXPOSURE_BUILDERS:
        sys.stderr.write(
            "BLOCKED: PROPOSAL_EXPOSURE_BUILDERS is empty - D2 execution "
            "happens under A1 after the insider/macro proposal handlers are "
            "registered; this module is the machine, not the run (an empty "
            "measurement is never written).\n")
        return 3
    C, rc = load_context()
    if rc != 0:
        return rc
    _bench_series(C)  # benchmark closes for the veto-13 reaction shadow
    # carried p0d verdict-split check (V9 census numbers)
    C.verdict_check = {
        "p0d_measured": C.verdict_counts,
        "p3_expected": {"DEAD_PRICE_CONFIRMED": 1550, "NOT_DEAD_PRICE_SURVIVAL": 219},
        "verdict": "MATCH" if C.verdict_counts == {"DEAD_PRICE_CONFIRMED": 1550,
                                                   "NOT_DEAD_PRICE_SURVIVAL": 219}
        else "MISMATCH"}
    if C.verdict_check["verdict"] != "MATCH":
        sys.stderr.write("BLOCKED: p0d verdict split mismatch\n")
        return 2

    results = {}
    for pid in sorted(PROPOSAL_EXPOSURE_BUILDERS):
        anchor = PROPOSAL_EXPOSURE_BUILDERS[pid](C)
        if not isinstance(anchor, dict) or not anchor:
            results[pid] = {"novelty": None, "verdict": "BLOCKED_EXPOSURE_UNDEFINED"}
            continue
        nov = novelty_block(C, anchor)
        verdict = "ELIGIBLE" if nov["novelty_pass_le_020"] else "BLOCKED_NOVELTY"
        results[pid] = {"novelty": nov, "verdict": verdict,
                        "identifiability_note": (
                            "measured at A1 via identifiability_anchor_vs_control "
                            "with the proposal's declared ctrl_gate (anchor and "
                            "control exposure dicts)")}

    audit = {
        "schema": "stocks_free_v13_run/d2_novelty_measure@1",
        "built_at_utc": built_at_utc,
        "producer_role": "D2 measurement lane module (V13 machine; executed "
                         "under the machine-wide heavy lock by the A1 lane)",
        "cycle": CYCLE,
        "base_sha": BASE_SHA,
        "discipline": "feature/rank arithmetic only; zero PnL, zero returns, "
                      "zero selection, zero scoring; universe = "
                      "entity-decision pairs where the registered exposure is "
                      "defined on the bookable pool",
        "input_integrity": {
            "pins": C.pins, "pin_verdicts": C.pin_verdicts,
            "rev_dir_encoding_check": C.dir_check,
            "p0d_verdict_split_check": C.verdict_check,
            "priced_counts": C.priced_counts,
            "filer_events_distinct_bookable": C.filer_event_count,
        },
        "decision_dates": {
            "grid_21s_per_fold": {fid: [d.isoformat() for d in C.grid21[fid]]
                                  for fid in sorted(C.grid21)},
            "other": "registered handlers may use event-anchored instants; "
                     "their keys carry the instants",
        },
        "veto_set": {"count": len(VETO_NAMES), "names": VETO_NAMES,
                     "rev_dir_encoding": {"mapping": REV_DIR_ENCODING,
                                          "runtime_check": C.dir_check}},
        "conventions_applied": CONVENTIONS,
        "form4_staging": {
            "alive_dir": str(FORM4_ALIVE_DIR),
            "dead_dir": str(FORM4_DEAD_DIR),
            "loader": "load_form4_acceptances()",
            "xml_ingest_required": "transaction direction (G-code buys/sells, "
                                   "derivative-table attribution) lives in the "
                                   "Form-4 XML, NOT staged yet",
        },
        "results": results,
        "verdict_rule": ("BLOCKED_NOVELTY if pooled |rho| > 0.20 vs any of the "
                         "FIFTEEN veto entries (fail-closed on null); "
                         "identifiability/feasibility per the D1 selection "
                         "rubric eligibility_hard_gates_measured_at_d2 are "
                         "measured at A1 with the declared ctrl_gate and "
                         "floors; selection and scoring remain A7+ decisions, "
                         "not D2's"),
        "margins": "margin-to-threshold reported per veto entry "
                   "(margin_to_020) and per identifiability gate (P-2)",
        "no_pnl_no_outcomes": True,
        "no_pnl_assertion": "this audit contains rho/feasibility-arithmetic "
                            "measurements ONLY - no returns, no PnL, no "
                            "selection, no scoring, no outcome-shaped fields; "
                            "a killed proposal is a SUCCESS under the "
                            "preregistered failure interpretations",
    }
    out = json.dumps(audit, indent=1, sort_keys=True)
    return 0, out


# ---------------------------------------------------------------------------
# SELFCHECK (mandatory - carries the INC-V-V12-4 fromisoformat lesson:
# every date-parse path the machine uses is exercised on known answers)
# ---------------------------------------------------------------------------
SYNTH_ENTITIES = ["CIK0000000001", "CIK0000000002", "CIK0000000003",
                  "CIK0000000004", "CIK0000000005"]
SYNTH_DATES = [date(2018, 3, 4), date(2018, 9, 3), date(2019, 3, 4)]


def _synth_ctx():
    """Tiny deterministic synthetic fixture for --selfcheck: FIVE entities x
    THREE decision dates, zero staged data, zero network."""
    class Ctx:
        pass

    C = Ctx()
    C.folds = FOLDS_FALLBACK
    spy = [{"date": (date(2015, 1, 1) + timedelta(days=i)).isoformat(),
            "close": 100.0 + (i % 7) * 0.5} for i in range(2100)]
    C.sessions = [dd(r["date"]) for r in spy]
    C.sess_idx = {d: i for i, d in enumerate(C.sessions)}
    secs = {"CIK0000000001": "XLF", "CIK0000000002": "XLF", "CIK0000000003": "XLK",
            "CIK0000000004": "XLK", "CIK0000000005": "XLE"}
    C.bookable = {cik: {"sector": secs[cik],
                        "ticker": f"T{i + 1}",
                        "cls": ("DEAD_EVIDENCED" if cik == "CIK0000000002"
                                else "ALIVE_EVIDENCED")}
                  for i, cik in enumerate(SYNTH_ENTITIES)}
    # death lands ON fixture date 2 so the death-event veto is measurable
    # inside the 5x3 loop (trigger bar <= T exists in the daily fixture series)
    C.p0d = {"CIK0000000002": {"verdict": "DEAD_PRICE_CONFIRMED",
                               "death_date": "2018-09-03"}}
    C.series = {}
    for k, cik in enumerate(SYNTH_ENTITIES):
        base = 40.0 + 10.0 * k
        # per-entity sawtooth phase (3*k) so 5-bar returns differ in sign
        # across entities (the veto-13 residual needs cross-sectional variance)
        arr = [{"date": (date(2015, 1, 1) + timedelta(days=i)).isoformat(),
                "close": base + ((i + 3 * k) % 13) * 0.25,
                "adjusted_close": base + ((i + 3 * k) % 13) * 0.25,
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
    # fields: annual accounting values (veto 4-8 substrate + accrual flow legs)
    C.fields = {}
    for k, cik in enumerate(SYNTH_ENTITIES):
        off = 7.0 * k
        for y in range(2010, 2020):
            eff = f"{y}-12-31"
            av = f"{y + 1}-02-15"
            assets = 500.0 + y + off
            vals = (
                ("us-gaap:Assets", assets),
                ("us-gaap:AssetsCurrent", assets * 0.45),
                ("us-gaap:LiabilitiesCurrent", assets * 0.28),
                ("us-gaap:Goodwill", 10.0 + y + off),
                ("us-gaap:CashAndCashEquivalentsAtCarryingValue", 20.0 + y + off),
                ("us-gaap:RetainedEarningsAccumulatedDeficit", 5.0 + y + off),
                ("us-gaap:AccountsReceivableNetCurrent", 30.0 + y + off),
                ("us-gaap:InventoryNet", 25.0 + y + off * 0.5),
                ("us-gaap:AccountsPayableCurrent", 18.0 + y + off * 0.25),
            )
            for f, v in vals:
                C.fields.setdefault((cik, f), []).append((av, eff, float(v)))
    for k in C.fields:
        C.fields[k].sort()
    # timing: own_z + filer events (annual stamps 2010..2019)
    stamps = [f"{2010 + i}-03-01" for i in range(10)]
    C.ownz = {cik: (stamps, array("d", [0.1 * i + 0.01 * k for i in range(10)]))
              for k, cik in enumerate(SYNTH_ENTITIES)}
    C.event_dates = {cik: list(stamps) for cik in SYNTH_ENTITIES}
    # benchmark closes (selfcheck-local; veto 13 residual denominator)
    C.bench = {"SPY": {d: 100.0 + i * 0.01 for i, d in enumerate(C.sessions)}}
    # revision: depth>=2 rows, quarterly 2011..2019
    #   depth = 2 + (i % 5)  -> depth 6 present (veto 14 deep count > 0)
    #   iarr  = 100 + 60*((i + 3k) % 9) -> crosses the 460 late cut inside the
    #           veto-12 window with entity- and date-dependent share (values
    #           100..580; late iff >= 470, i.e. (i + 3k) % 9 >= 7)
    #   dir   = (1, 0, -1)[i % 3] -> down rows present (veto 11)
    C.rev = {}
    for k, cik in enumerate(SYNTH_ENTITIES):
        rows = []
        i = 0
        for y in range(2011, 2020):
            for month in ("03", "06", "09", "12"):
                rows.append((f"{y}-{month}-{10 + (i % 10):02d}",
                             2 + (i % 5), 100 + 60 * ((i + 3 * k) % 9),
                             (1, 0, -1)[i % 3]))
                i += 1
        rows.sort()
        C.rev[cik] = rows
    C.bread, C.late, C.deep = {}, {}, {}
    for e, rows in C.rev.items():
        n = len(rows)
        avs = [r[0] for r in rows]
        ctot = array("i", [0] * n); cdn = array("i", [0] * n)
        t = dn = 0
        for i, r in enumerate(rows):
            t += 1; dn += 1 if r[3] == -1 else 0
            ctot[i] = t; cdn[i] = dn
        C.bread[e] = (avs, ctot, cdn)
        clate = array("i", [0] * n); cdeep = array("i", [0] * n)
        la = de = 0
        for i, r in enumerate(rows):
            la += 1 if r[2] > A5_LATE_IARR_CUT else 0
            de += 1 if r[1] >= 6 else 0
            clate[i] = la; cdeep[i] = de
        C.late[e] = (avs, ctot, clate)
        C.deep[e] = (avs, ctot, cdeep)
    C.grid21 = grid_dates(C, GRID_START, GRID_STEP)
    return C


def selfcheck() -> int:
    fails = []
    def check(name, cond, msg=""):
        if not cond:
            fails.append(f"{name}: {msg}")

    # ---- (a) fresh import of the module file --------------------------------
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "d2_v13_novelty_measure_selfcheck", Path(__file__).resolve())
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    check("import_module", len(mod.VETO_NAMES) == 15 and mod.NOVELTY_BAR == 0.20
          and len(mod.VETO_BUILDERS) == 15,
          f"names={len(mod.VETO_NAMES)} builders={len(mod.VETO_BUILDERS)}")
    check("import_registry_empty", mod.PROPOSAL_EXPOSURE_BUILDERS == {},
          str(mod.PROPOSAL_EXPOSURE_BUILDERS))

    # ---- fromisoformat lesson (INC-V-V12-4): known-answer date parses -------
    check("dd_known_answer", dd("2020-02-29") == date(2020, 2, 29)
          and dd("2018-04-04") == date(2018, 4, 4))

    # ---- (c) spearman midrank known answers ---------------------------------
    x20 = list(range(20))
    check("spearman_perfect", spearman(x20, [2 * v for v in x20]) == 1.0,
          str(spearman(x20, [2 * v for v in x20])))
    check("spearman_inverse", spearman(x20, x20[::-1]) == -1.0,
          str(spearman(x20, x20[::-1])))
    # ties: x has 6 tied pairs; exact closed form 140/sqrt(140*143)
    xt = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6]
    yt = list(range(1, 13))
    rho_t = spearman(xt, yt)
    check("spearman_ties_exact",
          rho_t is not None and abs(rho_t - 140.0 / math.sqrt(140.0 * 143.0)) < 1e-12,
          str(rho_t))
    # midrank tie values themselves
    mr = midrank([3.0, 1.0, 2.0, 2.0])
    check("midrank_ties", mr == [4.0, 1.0, 2.5, 2.5], str(mr))
    # abstentions: n < 10 guard and zero-variance guard
    check("spearman_n_guard", spearman([1.0] * 9, list(range(9))) is None)
    check("spearman_zero_var", spearman([1.0] * 12, list(range(12))) is None)

    # ---- (b) FIVE entities x THREE dates: all 15 builders float-or-None -----
    C = _synth_ctx()
    n_vals = {}
    for vn in mod.VETO_NAMES:
        vf = mod.VETO_BUILDERS[vn]
        vals = []
        for e in SYNTH_ENTITIES:
            for t in SYNTH_DATES:
                try:
                    v = vf(C, e, t)
                except Exception as exc:  # noqa: BLE001 - the check IS the guard
                    fails.append(f"builder_exception:{vn}: {type(exc).__name__}: {exc}")
                    v = None
                ok_type = (v is None) or (isinstance(v, float) and math.isfinite(v))
                if not ok_type:
                    fails.append(f"builder_type:{vn}: {type(v).__name__} {v!r}")
                vals.append(v)
        n_vals[vn] = sum(1 for v in vals if v is not None)

    # every veto measures on the fixture (none silently returns all-None)
    for vn, n in n_vals.items():
        check(f"veto_measures:{vn}", n > 0, f"all 15 cells unmeasured for {vn}")

    # targeted known-value checks
    w = mod.a4_walk(C, "CIK0000000001", SYNTH_DATES[0])
    check("a4_walk_defined", w is not None and w["n"] >= MIN_GROUPS_Q, str(w))
    ds = mod.veto_chain_deep_share(C, "CIK0000000001", SYNTH_DATES[0])
    check("chain_veto_defined",
          isinstance(ds, float) and 0.0 <= ds <= 1.0, str(ds))
    # |Q| < 4 must abstain: strip rows to leave 3 in-window groups
    C3 = _synth_ctx()
    e0 = "CIK0000000001"
    rows3 = [r for r in C3.rev[e0] if r[0] >= "2017-01-01"][:3]
    C3.rev[e0] = rows3
    avs3 = [r[0] for r in rows3]
    n3 = len(rows3)
    ctot3 = array("i", list(range(1, n3 + 1)))
    cdeep3 = array("i", [0] * n3)
    de = 0
    for i, r in enumerate(rows3):
        de += 1 if r[1] >= 6 else 0
        cdeep3[i] = de
    C3.deep[e0] = (avs3, ctot3, cdeep3)
    check("chain_veto_abstains_Q_lt_4",
          mod.veto_chain_deep_share(C3, e0, SYNTH_DATES[2]) is None,
          str(mod.veto_chain_deep_share(C3, e0, SYNTH_DATES[2])))
    # death-event veto: the dead XLF trigger books the surviving XLF peer at
    # the death-date cell (fixture date 2)
    dv = mod.veto_death_event_form(C, "CIK0000000001", SYNTH_DATES[1])
    check("death_veto_defined", dv == 1.0, str(dv))
    check("death_veto_absent_elsewhere",
          mod.veto_death_event_form(C, "CIK0000000005", SYNTH_DATES[0]) is None)

    # ---- registry plumbing: a probe handler through novelty_block -----------
    probe_anchor = {}
    for e in SYNTH_ENTITIES:
        for t in SYNTH_DATES:
            probe_anchor[(e, t)] = float(
                int(mod.sha256_hex(f"{e}|{t}".encode())[:8], 16) % 97 + 1)
    # plus one death-event cell so veto 15 measures on some pair
    probe_anchor[("CIK0000000001", date(2018, 9, 3))] = 42.0
    mod.PROPOSAL_EXPOSURE_BUILDERS["__selfcheck_probe__"] = lambda ctx: probe_anchor
    try:
        nov = mod.novelty_block(C, probe_anchor)
    finally:
        mod.PROPOSAL_EXPOSURE_BUILDERS.pop("__selfcheck_probe__", None)
    check("novelty_structure",
          set(nov["veto_rho"]) == set(mod.VETO_NAMES)
          and set(nov["n_per_veto"]) == set(mod.VETO_NAMES)
          and set(nov["margin_to_020"]) == set(mod.VETO_NAMES))
    # vetoes 1-14 measure >= 10 common pairs each (rho computable); veto 15 is
    # defined on a single fixture cell (n = 1 < 10) so its rho abstains - the
    # FAIL-CLOSED consequence is novelty_pass False, never a pass by absence
    check("novelty_vetoes_measured",
          nov["vetoes_measured"] == 14 and nov["novelty_pass_le_020"] is False,
          f"{nov['vetoes_measured']} of 15: "
          f"{sorted(k for k, v in nov['veto_rho'].items() if v is None)}")
    check("novelty_death_form_counts",
          nov["n_per_veto"]["v12_death_event_form"] == 1
          and nov["veto_rho"]["v12_death_event_form"] is None
          and nov["margin_to_020"]["v12_death_event_form"] is None,
          str(nov["n_per_veto"]["v12_death_event_form"]))
    check("novelty_margin_shape",
          all((nov["margin_to_020"][vn] is None)
              == (nov["veto_rho"][vn] is None) for vn in mod.VETO_NAMES))
    # fail-closed demonstration: an anchor with an unmeasurable veto fails
    nov_fc = mod.novelty_block(C, {("CIK0000000099", date(2019, 1, 2)): 1.0})
    check("novelty_fail_closed", nov_fc["novelty_pass_le_020"] is False
          and nov_fc["vetoes_measured"] < 15, str(nov_fc["vetoes_measured"]))
    check("registry_restored_empty", mod.PROPOSAL_EXPOSURE_BUILDERS == {},
          str(mod.PROPOSAL_EXPOSURE_BUILDERS))

    # ---- worked example handler (filing-count placeholder, direction stub) --
    mod_kept = mod.example_insider_buy_pressure
    C.form4 = {"CIK0000000001": [("2018-06-05", "2018-06-05T17:00:00.000Z"),
                                 ("2018-08-01", "2018-08-01T17:30:00.000Z")]}
    ex = mod_kept(C)
    check("example_handler_type", isinstance(ex, dict))
    grid = mod.grid_dates_flat(C, C.grid21)
    tgt = min(t for t in grid if t >= date(2018, 8, 2))
    check("example_handler_count", ex.get(("CIK0000000001", tgt)) == 1.0,
          str({str(k): v for k, v in sorted(ex.items())[:4]}))
    idx = grid.index(tgt)
    check("example_handler_prev_window_empty",
          idx >= 2 and ex.get(("CIK0000000001", grid[idx - 1])) == 0.0,
          str(ex.get(("CIK0000000001", grid[idx - 1]))))
    C_noform4 = _synth_ctx()
    check("example_handler_abstains_without_form4",
          mod_kept(C_noform4) is None)

    # ---- Form-4 loader: both submissions shapes, merge + dedup --------------
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        dead_dir = Path(td) / "dead"
        alive_dir = Path(td) / "alive"
        dead_dir.mkdir(); alive_dir.mkdir()
        # dead-cache shape: columnar parallel arrays (row 2: acceptanceDateTime
        # missing -> kept with "")
        (dead_dir / "CIK0000000001.json").write_text(json.dumps({
            "cik": "1",
            "filings": {"recent": {
                "form": ["4", "4", "4", "10-K"],
                "filingDate": ["2018-06-05", "2018-06-06", "2018-08-01", "2018-02-01"],
                "acceptanceDateTime": ["2018-06-05T17:00:00.000Z", None,
                                       "2018-08-01T17:30:00.000Z", "2018-02-01T09:00:00.000Z"],
            }}}))
        # standard submissions shape: row list
        (alive_dir / "CIK0000000001.json").write_text(json.dumps({
            "cik": "000000001",
            "filings": {"recent": [
                {"form": "4", "filingDate": "2018-06-05",
                 "acceptanceDateTime": "2018-06-05T17:00:00.000Z"},
                {"form": "4", "filingDate": "2019-01-15",
                 "acceptanceDateTime": "2019-01-15T18:01:00.000Z"},
                {"form": "S-1", "filingDate": "2019-02-01",
                 "acceptanceDateTime": "2019-02-01T10:00:00.000Z"},
            ]}}))
        # non-Form-4-only file: must be absent from the output
        (alive_dir / "CIK0000000009.json").write_text(json.dumps({
            "cik": "9",
            "filings": {"recent": [{"form": "10-K", "filingDate": "2019-02-01",
                                    "acceptanceDateTime": "2019-02-01T10:00:00.000Z"}]}}))
        got = mod.load_form4_acceptances(alive_dir=alive_dir, dead_dir=dead_dir)
        want = {"CIK0000000001": [("2018-06-05", "2018-06-05T17:00:00.000Z"),
                                  ("2018-06-06", ""),
                                  ("2018-08-01", "2018-08-01T17:30:00.000Z"),
                                  ("2019-01-15", "2019-01-15T18:01:00.000Z")]}
        check("form4_loader", got == want, f"got {got}")
        got2 = mod.load_form4_acceptances(alive_dir=alive_dir / "missing",
                                          dead_dir=dead_dir)
        check("form4_loader_missing_dir",
              got2 == {"CIK0000000001": [("2018-06-05", "2018-06-05T17:00:00.000Z"),
                                         ("2018-06-06", ""),
                                         ("2018-08-01", "2018-08-01T17:30:00.000Z")]},
              f"got {got2}")

    # ---- determinism x2 (in-process): two fresh fixtures, byte-identical ----
    def veto_table(ctx):
        tab = {}
        for vn in mod.VETO_NAMES:
            vf = mod.VETO_BUILDERS[vn]
            for e in SYNTH_ENTITIES:
                for t in SYNTH_DATES:
                    tab[f"{vn}|{e}|{t.isoformat()}"] = vf(ctx, e, t)
        return tab
    s1 = json.dumps(veto_table(_synth_ctx()), sort_keys=True)
    s2 = json.dumps(veto_table(_synth_ctx()), sort_keys=True)
    check("determinism_x2_table", s1 == s2 and len(s1) > 100,
          f"len={len(s1)} identical={s1 == s2}")

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
        sys.stderr.write("usage: d2_v13_novelty_measure.py <built_at_utc> <out_path> [--selfcheck]\n")
        return 64
    built_at, out_path = argv[1], argv[2]
    rc = run_full(built_at)
    if isinstance(rc, tuple):
        rc, payload = rc
    else:
        return rc
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, "w") as fh:
        fh.write(payload)
    print(f"[d2] wrote {outp} ({len(payload)} bytes)", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
