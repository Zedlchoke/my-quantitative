"""STOCKS-NG2 D2 core: frozen constants, paths, context, grid, eligibility.

Read surfaces (ALL read-only inherited pins or this cycle's committed
control artifacts; nothing here is written):

  * pinned V13 staging  : .worktrees/stocks-free-v13/integration/.staging_sec_v13/
                          form4_stream.jsonl (546,039 rows; sha256 pinned),
                          form4_xml/ (345,150 type-4 docs, enumerated by the
                          substrate manifest), submissions_alive/ (410 pinned
                          cohort CIKs - the 4/A acceptanceDateTime authority)
  * pinned V9 prices    : .worktrees/stocks-free-v9/integration/.staging_prices_v9/
                          {eod, benchmarks} + cohort_v9 + p0d (same surface
                          the ng1 D2 machine read)
  * 4/A re-ingest tree  : the MAIN stocks-ng2 worktree's
                          integration/data_raw/form4a/ (read-only bytes
                          pinned by p0_form4a_ingest_manifest.json, whose
                          aggregate digest is re-verified at load)
  * census B / census A : this worktree's committed P0 control artifacts
                          (reconciliation authorities, fail-closed)

Grid law (proposal clock, re-measured): DAILY SPY-session decision grid,
first decision = first session on/after 2018-01-01 (= 2018-01-02); last
decision = the pinned acceptance evidence end = max(stream last
acceptance date, last 4/A acceptanceDateTime date among the pinned
enumerated 4/A accessions), FROZEN at load so post-substrate price-tail
refreshes (the inherited EODHD files' alive tail extends beyond) cannot
enter any measured window (the ng1 D2 law applied to the extended
substrate).  The measured price-data end is recorded alongside; it is
NOT the grid authority.

PIT convention (inherited house rule, unchanged): UTC acceptance-
timestamp string compare; an acceptance enters exposure at the first
decision session on/after its UTC calendar date.
"""

from __future__ import annotations

import hashlib
import json
import math
from bisect import bisect_left, bisect_right
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]

# ---------------------------------------------------------------- paths ----
V13_INTEG = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                 "stocks-free-v13/integration")
V9_INTEG = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                "stocks-free-v9/integration")
NG2_MAIN_INTEG = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                      "stocks-ng2/integration")

STREAM_PATH = V13_INTEG / ".staging_sec_v13/form4_stream.jsonl"
SUBSTRATE_MANIFEST_PATH = (V13_INTEG /
                          "research/control/stocks_free_v13_run/"
                          "substrate_manifest.json")
SUBMISSIONS_DIR = V13_INTEG / ".staging_sec_v13/submissions_alive"
PRICES_DIR = V9_INTEG / ".staging_prices_v9/eod"
BENCH_SPY = V9_INTEG / ".staging_prices_v9/benchmarks/SPY.json"
COHORT_PATH = V9_INTEG / "research/control/stocks_free_v9_run/cohort_v9.json"
P0D_PATH = (V9_INTEG /
            "research/control/stocks_free_v9_run/p0d_v9_integrity_scan.json")

FORM4A_ROOT = NG2_MAIN_INTEG / "data_raw/form4a"
FORM4A_STATE_PATH = NG2_MAIN_INTEG / "data_raw/form4a_fetch_state.jsonl"
FORM4A_MANIFEST_PATH = (REPO_ROOT /
                        "research/control/stocks_ng2_run/"
                        "p0_form4a_ingest_manifest.json")
CENSUS_B_PATH = (REPO_ROOT /
                 "research/control/stocks_ng2_run/"
                 "p0_census_b_amendments_extended.json")
CENSUS_A_PATH = (REPO_ROOT /
                 "research/control/stocks_ng1_run/p0_census_a_10b5.json")
NG1_GATE_PATH = REPO_ROOT / "research/control/stocks_ng1_run/p0_gate.json"

# ------------------------------------------------------- pinned digests ----
PIN_STREAM_SHA256 = ("6ac2cd5bdd62566efe106b46de715030e9a8a940cb90f5a991"
                     "df5f05ba6742b2")
PIN_COHORT_SHA256 = ("6a95401ff84bff2144ac3c0b9426a6fa86daf3dde8d478195666"
                     "249e3fa2aa62")
PIN_FORM4A_AGGREGATE_SHA256 = ("53daea6172ff5538c279970d7a1d1ea85c8294c637"
                               "b7b2de3102ffc2ad05f062")

# census B reconciliation authorities (committed P0 artifact; fail-closed)
PIN_CENSUS_B = {
    "fetched_accessions": 3062,
    "fetched_non_xml": 3,
    "amendment_docs": 3059,
    "amendments_with_resolvable_original": 1877,
    "original_index_size": 342801,
    "resolvable_by_year": {"2018": 157, "2019": 218, "2020": 237,
                           "2021": 286, "2022": 257, "2023": 271,
                           "2024": 262, "2025": 179, "2026": 10},
}

# ------------------------------------------------- frozen BEFORE measuring --
NOVELTY_BAR = 0.20            # pooled |rho| bar vs every veto entry (17)
SELF_SUBSUMPTION_RHO = 0.98   # anchor-vs-control pooled rho kill (pre-score)
SPEARMAN_MIN_N = 10           # pooled rho undefined below n=10 (fail-closed)
Q6_RECENT_YEAR = "2025"       # Q-6 recent-window year
Q6_RECENT_WINDOW_FLOOR = 30   # frozen: >= 30 bookable decisions in 2025
FOLD_POPULATION_FLOOR = 20    # frozen: >= 20 bookable decisions per fold
SECTOR_BOOKABLE_NAMES = 6     # proposal book_form: >= 6 ranked names/sector
TURNOVER_CEILING_BPS_QTR = 200  # referenced rubric ceiling (V13 constant)
SHAM_SEED = 20260912          # pair-lag/dV permutation seed (proposal P1)
TRAIL_SESSIONS = 63           # trailing amendment-acceptance window (sessions)
BARS_FLOOR = 63               # eligibility: >= 63 bars through t
ADV63_FLOOR_USD = 2_000_000.0  # eligibility: mean daily close*volume >= 2M
CLOSE_FLOOR = 1.00            # eligibility: raw close >= 1.00 USD

FOLDS_DECLARED = [
    {"fold_id": "SFNG2-A4-F1", "start": "2018-01-01", "end": "2020-12-31"},
    {"fold_id": "SFNG2-A4-F2", "start": "2021-01-01", "end": "2022-12-31"},
    {"fold_id": "SFNG2-A4-F3", "start": "2023-01-01", "end": "DYNAMIC"},
    # F3 end = substrate_end (the frozen grid end); resolved at load and
    # frozen in the artifact before any counting (proposal book_folds).
]
# fold resolvable-pair mass declared ex ante on the census by-year split
# (157+218+237 | 286+257 | 271+262+179+10) - verified at D2, never re-tuned
FOLD_PAIR_MASS_DECLARED = {"SFNG2-A4-F1": 612, "SFNG2-A4-F2": 543,
                           "SFNG2-A4-F3": 722}

GRID_FIRST = "2018-01-01"     # first decision = first session on/after this
STREAM_AGG_CUTOFF = "2015-11-24"  # 800d before grid first (covers windows)
PRICE_TRIM = "2015-11-24"     # price bars kept from this date on

# 17-entry veto set: the 15 V13 audit names (verbatim, reused from the ng1
# D2 machinery) + the ng1 10b5-1 kills (fdens / planshare, constructed by
# the ng1 D2 exposure machinery on THIS cycle's panel/grid).
VETO_NAMES_15 = [
    "momentum_63s", "semivariance_share", "vol_level", "wc_stock_intensity",
    "goodwill_bloat", "f1_accrual_flow", "depletion_interaction",
    "cash_level", "sector_exposure_form", "own_z_characteristic_form",
    "revision_direction_breadth_form", "v11_cadence_latency_form",
    "filing_event_reaction_shadow", "v12_chain_structure_form",
    "v12_death_event_form",
]
VETO_NAMES_NG1 = ["ng1_10b5_1_fdens", "ng1_10b5_1_planshare"]
VETO_NAMES = VETO_NAMES_15 + VETO_NAMES_NG1


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------ rank correlation ----
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
    """Pooled midrank Spearman; None below SPEARMAN_MIN_N or on zero
    variance (fail-closed abstention, never a pass)."""
    n = len(a)
    if n < SPEARMAN_MIN_N:
        return None
    ra, rb = midrank(a), midrank(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra))
    vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    if va == 0 or vb == 0:
        return None
    return cov / (va * vb)


def rho_on_common(a: dict, b: dict):
    """Pooled Spearman over common keys of two {(e,t): v} panels."""
    common = sorted(k for k in a if k in b)
    if not common:
        return None, 0
    return (spearman([a[k] for k in common], [b[k] for k in common]),
            len(common))


# ------------------------------------------------------------- context ------
class Ctx:
    """Everything the D2 measurement reads, built once per pass."""


def _load_price_file(path: Path):
    arr = json.loads(path.read_text())
    arr = [r for r in arr if r.get("close") is not None]
    arr.sort(key=lambda r: r["date"])
    return ([r["date"] for r in arr],
            [float(r["close"]) for r in arr],
            [r.get("adjusted_close") for r in arr],
            [float(r.get("volume") or 0.0) for r in arr])


def _verify_form4a_tree():
    """Re-digest the 4/A re-ingest tree against the committed ingest
    manifest (per-file + aggregate); fail-closed on any drift."""
    man = json.loads(FORM4A_MANIFEST_PATH.read_text())
    files = {}
    for dirpath, _dirnames, filenames in sorted(os_walk(FORM4A_ROOT)):
        for fn in sorted(filenames):
            if fn.endswith(".tmp"):
                continue
            p = Path(dirpath) / fn
            files[str(p.relative_to(FORM4A_ROOT))] = sha256_file(p)
    drift = [k for k in files if man["files"].get(k) != files[k]]
    missing = [k for k in man["files"] if k not in files]
    agg_input = "\n".join(f"{k} {files[k]}" for k in sorted(files))
    agg = hashlib.sha256(agg_input.encode("utf-8")).hexdigest()
    if drift or missing or agg != PIN_FORM4A_AGGREGATE_SHA256:
        raise RuntimeError(
            f"form4a tree drift: {len(drift)} changed, {len(missing)} "
            f"missing, aggregate {agg}")
    return {"files": len(files), "aggregate_sha256": agg,
            "manifest_status": man["status"]}


def os_walk(root):
    import os
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        yield dirpath, dirnames, filenames


def _submissions_acceptance_index():
    """accession_nodash -> acceptanceDateTime (UTC, pinned submissions
    metadata) for every OK row of the 4/A fetch state; plus the last
    acceptance date over the enumerated 4/A accessions (grid authority).
    None acceptanceDateTime rows are recorded, never guessed."""
    state = {}
    with open(FORM4A_STATE_PATH) as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("status") == "OK":
                state[row["accession_nodash"]] = row
    acc = {}
    missing = 0
    for fname in sorted(SUBMISSIONS_DIR.glob("*.json")):
        d = json.loads(fname.read_text())
        recent = d.get("filings", {}).get("recent", {})
        accs = recent.get("accessionNumber", [])
        ats = recent.get("acceptanceDateTime", [])
        for i, a in enumerate(accs):
            an = a.replace("-", "")
            if an in state:
                ts = ats[i] if i < len(ats) else None
                if ts is None:
                    missing += 1
                acc[an] = ts
    if len(acc) != len(state):
        raise RuntimeError(
            f"submissions/fetch-state accession mismatch: "
            f"{len(acc)} vs {len(state)}")
    return acc, missing


def build_context() -> Ctx:
    C = Ctx()

    # ---- integrity pins (fail-closed) --------------------------------------
    C.stream_sha256 = sha256_file(STREAM_PATH)
    if C.stream_sha256 != PIN_STREAM_SHA256:
        raise RuntimeError(f"stream digest drift: {C.stream_sha256}")
    C.cohort_sha256 = sha256_file(COHORT_PATH)
    if C.cohort_sha256 != PIN_COHORT_SHA256:
        raise RuntimeError(f"cohort digest drift: {C.cohort_sha256}")
    C.p0d_sha256 = sha256_file(P0D_PATH)
    C.form4a_verify = _verify_form4a_tree()

    # ---- cohort -------------------------------------------------------------
    cohort = json.loads(COHORT_PATH.read_text())
    C.bookable = {}
    for cls in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED"):
        for m in cohort["members"][cls]:
            C.bookable[m["cik"]] = {"sector": m.get("sector", ""),
                                    "cls": cls}
    C.cohort_counts = {"ALIVE_EVIDENCED": sum(
        1 for v in C.bookable.values() if v["cls"] == "ALIVE_EVIDENCED"),
        "DEAD_EVIDENCED": sum(
            1 for v in C.bookable.values() if v["cls"] == "DEAD_EVIDENCED")}

    # ---- p0d dead verdicts (veto 15 trigger set) ----------------------------
    p0d = json.loads(P0D_PATH.read_text())
    C.p0d = {cik: rec for cik, rec in p0d["dead_verdicts"].items()
             if cik in C.bookable}
    split = {}
    for rec in C.p0d.values():
        split[rec["verdict"]] = split.get(rec["verdict"], 0) + 1
    if split != {"DEAD_PRICE_CONFIRMED": 1550,
                 "NOT_DEAD_PRICE_SURVIVAL": 219}:
        raise RuntimeError(f"p0d verdict split mismatch: {split}")

    # ---- census A (ng1 10b5-1 veto flag source) ------------------------------
    census = json.loads(CENSUS_A_PATH.read_text())
    C.declared_accessions = set(census["census"]["declared_docs_post_2023"])
    C.census_declared_counter = census["census"]["docs_declared_post_2023"]
    gate = json.loads(NG1_GATE_PATH.read_text())
    C.census_flagged_tx_expected = gate["census_floors"]["census_a"][
        "flagged_transactions_post_2023"]

    # ---- session calendar (SPY) ----------------------------------------------
    spy = json.loads(BENCH_SPY.read_text())
    spy = [r for r in spy if r.get("close") is not None]
    spy.sort(key=lambda r: r["date"])
    C.sessions = [r["date"] for r in spy]
    C.sess_idx = {d: i for i, d in enumerate(C.sessions)}
    C.spy_close = {r["date"]: float(r["close"]) for r in spy}
    C.price_data_end = C.sessions[-1]

    # ---- grid: frozen at the pinned acceptance evidence end -------------------
    C.stream_last_acceptance = None
    C.stream_first_acceptance = None
    with open(STREAM_PATH) as fh:
        for line in fh:
            a = json.loads(line).get("acceptance") or ""
            if a:
                if (C.stream_last_acceptance is None
                        or a > C.stream_last_acceptance):
                    C.stream_last_acceptance = a
                if (C.stream_first_acceptance is None
                        or a < C.stream_first_acceptance):
                    C.stream_first_acceptance = a
    C.acc4a, C.acc4a_missing_ts = _submissions_acceptance_index()
    last4a = max((ts for ts in C.acc4a.values() if ts), default="")
    end_candidates = {
        "stream_last_acceptance_date": C.stream_last_acceptance[:10],
        "last_4a_acceptance_date": last4a[:10],
    }
    grid_end_date = max(end_candidates.values())
    C.grid_end_authority = {
        "rule": ("grid end = max(pinned stream last acceptance date, "
                 "last 4/A acceptanceDateTime date over the pinned "
                 "enumerated 4/A accessions) - the pinned acceptance "
                 "evidence end; the measured price-data end is recorded "
                 "but is NOT the grid authority (post-substrate price "
                 "refreshes cannot enter any measured window; ng1 law)"),
        "candidates": end_candidates,
        "grid_end": grid_end_date,
        "price_data_end_measured": C.price_data_end,
    }
    C.grid = [d for d in C.sessions
              if d >= GRID_FIRST and d <= grid_end_date]
    if not C.grid:
        raise RuntimeError("empty decision grid")
    C.grid_end = C.grid[-1]
    C.folds = [{"fold_id": f["fold_id"], "start": f["start"],
                "end": (C.grid_end if f["end"] == "DYNAMIC" else f["end"])}
               for f in FOLDS_DECLARED]

    # ---- prices (cohort entities; trimmed; death triggers need full dates) ---
    C.series = {}
    C.death_triggers = []
    C.price_files_bookable = 0
    for path in sorted(PRICES_DIR.glob("CIK*.json")):
        cik = path.name.split("__")[0]
        if cik not in C.bookable:
            continue
        try:
            dates, close, adj, vol = _load_price_file(path)
        except Exception:
            continue
        if not dates:
            continue
        C.price_files_bookable += 1
        # veto-15 death-trigger classification reads the FULL history
        # (deaths date back to 2018); resolved now, before the trim.
        rec = C.p0d.get(cik)
        if rec is not None and rec["verdict"] == "DEAD_PRICE_CONFIRMED":
            T = rec["death_filing_date"]
            i = bisect_right(dates, T) - 1
            C.death_triggers.append(
                {"cik": cik, "T": T, "last_bar": (dates[i] if i >= 0
                                                  else None)})
        lo = bisect_left(dates, PRICE_TRIM)
        d_t = dates[lo:]
        c_t = close[lo:]
        a_t = adj[lo:]
        v_t = vol[lo:]
        n = len(d_t)
        lr = [0.0] * n
        ok = [False] * n
        for i in range(1, n):
            if (a_t[i - 1] is not None and a_t[i] is not None
                    and a_t[i - 1] > 0 and a_t[i] > 0):
                lr[i] = math.log(a_t[i] / a_t[i - 1])
                ok[i] = True
        s_lr = [0.0] * n
        s_l2 = [0.0] * n
        s_dn = [0.0] * n
        s_ok = [0] * n
        s_dv = [0.0] * n
        for i in range(1, n):
            s_lr[i] = s_lr[i - 1] + (lr[i] if ok[i] else 0.0)
            s_l2[i] = s_l2[i - 1] + ((lr[i] ** 2) if ok[i] else 0.0)
            s_dn[i] = s_dn[i - 1] + ((lr[i] ** 2) if (ok[i] and lr[i] < 0)
                                     else 0.0)
            s_ok[i] = s_ok[i - 1] + (1 if ok[i] else 0)
            s_dv[i] = s_dv[i - 1] + (c_t[i] * v_t[i] if c_t[i] > 0 else 0.0)
        s = C.series.setdefault(cik, {})
        s.update({"dates": d_t, "close": c_t, "adj": a_t, "vol": v_t,
                  "pre": (s_lr, s_l2, s_dn, s_ok), "dv": s_dv})
    return C


# ----------------------------------------------- series queries (ng1 law) ----
def last_bar_le(C, cik, t_iso):
    """Index of the last bar with date <= t_iso, or None."""
    s = C.series.get(cik)
    if s is None:
        return None
    i = bisect_right(s["dates"], t_iso) - 1
    return i if i >= 0 else None


def first_session_ge(sessions, d_iso):
    i = bisect_left(sessions, d_iso)
    return sessions[i] if i < len(sessions) else None


def bars_through(C, cik, t_iso):
    """Count of bars with date <= t (eligibility: 'through t')."""
    s = C.series.get(cik)
    if s is None:
        return 0
    return bisect_right(s["dates"], t_iso)


def adv63(C, cik, t_iso):
    """Mean daily raw close*volume over the last <=63 bars through t."""
    s = C.series.get(cik)
    if s is None:
        return None
    i = bisect_right(s["dates"], t_iso) - 1
    if i < 0:
        return None
    lo = max(0, i - BARS_FLOOR + 1)
    n = i - lo + 1
    dv = (s["dv"][i] - (s["dv"][lo - 1] if lo > 0 else 0.0)) / n
    return dv


def close_at(C, cik, t_iso):
    """Raw close of the last bar at or before t_iso (None if no bar)."""
    i = last_bar_le(C, cik, t_iso)
    return None if i is None else C.series[cik]["close"][i]


def eligible(C, cik, t_iso):
    """Frozen per-decision eligibility: >=63 bars through t, ADV63 >= 2M
    USD, raw close >= 1.00.  Deterministic; evaluated per (e, t)."""
    s = C.series.get(cik)
    if s is None:
        return False
    if bars_through(C, cik, t_iso) < BARS_FLOOR:
        return False
    i = bisect_right(s["dates"], t_iso) - 1
    if s["close"][i] < CLOSE_FLOOR:
        return False
    lo = max(0, i - BARS_FLOOR + 1)
    n = i - lo + 1
    dv = (s["dv"][i] - (s["dv"][lo - 1] if lo > 0 else 0.0)) / n
    return dv >= ADV63_FLOOR_USD
