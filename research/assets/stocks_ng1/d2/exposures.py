"""STOCKS-NG1 D2 exposures: stream aggregation, anchors, shadow, sham.

One physical pass over the pinned stream builds, per cohort entity, a
sorted list of ACCEPTANCE SESSIONS (global SPY-session indices) with
per-session aggregate counters and prefix arrays, so every window query
(trailing 63 sessions / trailing 800 calendar days) is O(log n):

  cum_docs        distinct accessions accepted in the session
  cum_rows_all    all stream rows (any table, any code)
  cum_nnd / nndD / nndA   nonDerivative rows / D-coded / A-coded
  cum_nderiv      derivative-table rows
  cum_vD / vA     dollar value (shares x raw close at acceptance) of
                  nonDerivative D / A rows
  cum_flag_sess   sessions carrying >= 1 DECLARED (aff10b5One) doc
  cum_vD_flag     dollar value of D rows whose doc is DECLARED
  cum_sess_nd     sessions with >= 1 nonDerivative row
  cum_sess_netD   sessions with vD > vA (net-disposition majority)
  cum_sess_multi  sessions with >= 2 distinct accessions (doc chains)
  cum_gap_n/late  inter-acceptance calendar gaps attributed at the later
                  session; late iff gap > 460 days (veto 12 form)

Anchor exposures (proposal definitions, verbatim):

  fdens(e,t)      count of DISTINCT flagged acceptance sessions of e in
                  the trailing 63 sessions ending at decision close t;
                  defined iff >= 1 (P1 definition floor).
  planshare(e,t)  V_flagged_dispose / V_all_dispose (nonDerivative D rows
                  in trailing 63 sessions; value = shares x raw close at
                  acceptance - the stream carries no value field);
                  defined iff V_all >= 2,000 USD AND >= 2 D rows.

Sham (flag-permutation, both proposals' control_arms): within each
(acceptance-session, sector) cell over cohort docs, reassign the DECLARED
flags uniformly at random preserving the cell's flag-count marginal
EXACTLY (numpy PCG64, seed 20260911, cells processed in decision-date
session order, docs (cik, accession)-sorted within cell), destroying the
flag-to-issuer linkage; then the FULL anchor machinery is recomputed on
the permuted flags.  Nothing but the flag-doc linkage changes.
"""

from __future__ import annotations

import json
import math
from bisect import bisect_left, bisect_right
from datetime import date, timedelta

from . import core
from .core import (AGG_CUTOFF, P2_MIN_D_ROWS, P2_VALUE_FLOOR, SHAM_SEED,
                   TRAIL_SESSIONS, first_session_ge)


def _parse_float(x):
    try:
        v = float(str(x).replace(",", ""))
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def aggregate_stream(C) -> dict:
    """Single pass over the pinned stream -> per-entity session records.

    Returns diagnostics + the entity aggregate structure consumed by the
    exposure builders and veto builders.  Fail-closed accounting: rows
    whose shares are unparseable, or whose acceptance-date close lookup
    fails, are excluded from VALUE sums only and counted (never guessed).
    """
    diag = {"rows_total": 0, "rows_before_cutoff": 0,
            "rows_noncohort": 0, "shares_unparseable_rows": 0,
            "value_close_missing_rows": 0,
            "null_acceptance_rows": 0}
    # (cik, session_idx) -> counters
    agg = {}
    # doc-level: (cik, acc) -> {"session": i, "vD": v, "flag": bool}
    docs = {}
    flagged_tx_post_2023 = 0
    flagged_tx_by_year = {}

    with open(core.STREAM_PATH, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            diag["rows_total"] += 1
            cik = r.get("cik")
            acc_ts = r.get("acceptance") or ""
            if not acc_ts:
                diag["null_acceptance_rows"] += 1
                continue
            if acc_ts < AGG_CUTOFF:
                diag["rows_before_cutoff"] += 1
                continue
            if cik not in C.bookable:
                diag["rows_noncohort"] += 1
                continue
            sess = first_session_ge(C.sessions, acc_ts[:10])
            if sess is None:
                continue
            si = C.sess_idx[sess]
            acc = (r.get("accession") or "").replace("-", "")
            table_nd = str(r.get("table", "")).strip().lower() == "nonderivative"
            direction = r.get("direction")
            shares = _parse_float(r.get("shares"))
            px = core.close_at(C, cik, acc_ts[:10])
            val = shares * px if (shares is not None and px is not None
                                  and shares >= 0 and px > 0) else None
            if table_nd and direction in ("A", "D") and shares is not None \
                    and val is None:
                if px is None:
                    diag["value_close_missing_rows"] += 1
                else:
                    diag["shares_unparseable_rows"] += 1

            cell = agg.setdefault((cik, si), {
                "docs": set(), "rows_all": 0, "nnd": 0, "nndD": 0,
                "nndA": 0, "nderiv": 0, "nPS": 0, "vD": 0.0, "vA": 0.0,
                "vD_flag": 0.0, "flag": False})
            cell["docs"].add(acc)
            cell["rows_all"] += 1
            if str(r.get("transaction_code", "")).strip() in ("P", "S"):
                cell["nPS"] += 1
            if table_nd:
                cell["nnd"] += 1
                if direction == "D":
                    cell["nndD"] += 1
                    if val is not None:
                        cell["vD"] += val
                        doc = docs.setdefault(
                            (cik, acc), {"session": si, "vD": 0.0,
                                         "flag": False})
                        doc["vD"] += val
                elif direction == "A":
                    cell["nndA"] += 1
                    if val is not None:
                        cell["vA"] += val
            else:
                cell["nderiv"] += 1

            if acc in C.declared_accessions:
                cell["flag"] = True
                d = docs.setdefault((cik, acc), {"session": si, "vD": 0.0,
                                                 "flag": False})
                d["flag"] = True
                if val is not None and table_nd and direction == "D":
                    cell["vD_flag"] += val
                if acc_ts >= "2023-01-01":
                    flagged_tx_post_2023 += 1
                    y = acc_ts[:4]
                    flagged_tx_by_year[y] = flagged_tx_by_year.get(y, 0) + 1

    # ---- per-entity structures + prefix arrays ----------------------------
    ent_sessions = {}
    for (cik, si), cell in agg.items():
        ent_sessions.setdefault(cik, []).append((si, cell))
    E = {}
    for cik in sorted(ent_sessions):
        lst = sorted(ent_sessions[cik])
        n = len(lst)
        sess_idx = [x[0] for x in lst]
        sess_d = [C.sessions[i] for i in sess_idx]
        cum = {k: [0] * n for k in
               ("docs", "rows_all", "nnd", "nndD", "nndA", "nderiv",
                "nPS", "flag_sess", "sess_nd", "sess_netD", "sess_multi",
                "gap_n", "gap_late")}
        cumv = {k: [0.0] * n for k in ("vD", "vA", "vD_flag")}
        prev_date = None
        for i, (si, cell) in enumerate(lst):
            gap = None if prev_date is None else _cal_days(sess_d[i],
                                                           prev_date)
            cum["docs"][i] = len(cell["docs"])   # distinct accessions
            cum["rows_all"][i] = cell["rows_all"]
            cum["nnd"][i] = cell["nnd"]
            cum["nndD"][i] = cell["nndD"]
            cum["nndA"][i] = cell["nndA"]
            cum["nderiv"][i] = cell["nderiv"]
            cum["nPS"][i] = cell["nPS"]
            cum["flag_sess"][i] = 1 if cell["flag"] else 0
            cum["sess_nd"][i] = 1 if cell["nnd"] > 0 else 0
            cum["sess_netD"][i] = 1 if cell["vD"] > cell["vA"] else 0
            cum["sess_multi"][i] = 1 if len(cell["docs"]) >= 2 else 0
            if gap is not None:
                cum["gap_n"][i] = 1
                cum["gap_late"][i] = 1 if gap > 460 else 0
            cumv["vD"][i] = cell["vD"]
            cumv["vA"][i] = cell["vA"]
            cumv["vD_flag"][i] = cell["vD_flag"]
            prev_date = sess_d[i]
        # prefix
        for k in cum:
            for i in range(1, n):
                cum[k][i] += cum[k][i - 1]
        for k in cumv:
            for i in range(1, n):
                cumv[k][i] += cumv[k][i - 1]
        E[cik] = {"sess_idx": sess_idx, "sess_d": sess_d,
                  "cum": cum, "cumv": cumv}
    C.E = E
    C.docs = docs
    C.stream_diag = diag
    C.flagged_tx_post_2023 = flagged_tx_post_2023
    C.flagged_tx_by_year = dict(sorted(flagged_tx_by_year.items()))
    return diag


def _cal_days(a: str, b: str) -> int:
    return (date.fromisoformat(a) - date.fromisoformat(b)).days


def _win63(C, cik, t_iso):
    """Session-index range [lo, hi] of the trailing 63 sessions ending at
    t (t must be a grid session); returns entity prefix bounds (lo_i,
    hi_i) into E[cik] plus the grid session index."""
    gi = C.sess_idx[t_iso]
    hi = bisect_right(C.E[cik]["sess_idx"], gi) - 1
    if hi < 0:
        return None
    lo_gi = gi - TRAIL_SESSIONS + 1
    lo = bisect_left(C.E[cik]["sess_idx"], lo_gi)
    return lo, hi


def _win_cal(C, cik, t_iso, days):
    """Entity prefix bounds over the trailing `days` calendar window
    ending at t (inclusive)."""
    cut = (date.fromisoformat(t_iso) - timedelta(days=days)).isoformat()
    hi = bisect_right(C.E[cik]["sess_d"], t_iso) - 1
    if hi < 0:
        return None
    lo = bisect_left(C.E[cik]["sess_d"], cut)
    return lo, hi


def _pfx(C, cik, key, bounds, is_value=False):
    lo, hi = bounds
    arr = C.E[cik]["cumv" if is_value else "cum"][key]
    base = 0.0 if is_value else 0
    return arr[hi] - (arr[lo - 1] if lo > 0 else base)


def has_E(C, cik):
    return cik in getattr(C, "E", {})


def fdens(C, cik, t_iso):
    """P1 anchor: distinct flagged acceptance sessions in trailing 63
    sessions ending at t; defined iff >= 1 (definition floor)."""
    if not has_E(C, cik):
        return None
    b = _win63(C, cik, t_iso)
    if b is None:
        return None
    v = _pfx(C, cik, "flag_sess", b)
    return float(v) if v >= 1 else None


def planshare(C, cik, t_iso):
    """P2 anchor: V_flagged_dispose / V_all_dispose over nonDerivative
    D rows in trailing 63 sessions; floor: V_all >= 2,000 USD and >= 2
    D rows.  Value = shares x raw close at the acceptance date (the
    stream carries no value field - the proposal's declared fallback)."""
    if not has_E(C, cik):
        return None
    b = _win63(C, cik, t_iso)
    if b is None:
        return None
    v_all = _pfx(C, cik, "vD", b, is_value=True)
    if v_all < P2_VALUE_FLOOR:
        return None
    if _pfx(C, cik, "nndD", b) < P2_MIN_D_ROWS:
        return None
    v_flag = _pfx(C, cik, "vD_flag", b, is_value=True)
    return v_flag / v_all


def arrival_shadow(C, cik, t_iso):
    """Filing-arrival clock shadow: log1p(n4) with n4 = the entity's
    Form-4 acceptance EVENTS (distinct accessions, any table/code) in
    the trailing 63 sessions."""
    if not has_E(C, cik):
        return None
    b = _win63(C, cik, t_iso)
    if b is None:
        return None
    n = _pfx(C, cik, "docs", b)
    if n < 1:
        return None
    return math.log1p(n)


# ------------------------------------------------------------------ sham ----
def build_sham(C, seed: int = SHAM_SEED):
    """Flag-permutation sham (both proposals' control_arms verbatim):
    within each (acceptance-session, sector) cell over cohort docs with
    acceptance in the compliance window [grid first .. grid end], choose
    uniformly at random which docs carry the DECLARED flag, preserving
    the cell's flag-count marginal EXACTLY.  Deterministic: cells in
    (session, sector) order, docs (cik, accession)-sorted, numpy PCG64
    with the frozen seed; the RNG is consumed in exactly that order.

    Returns per-entity sham aggregates (flagged sessions prefix +
    flagged-D-value prefix) with the same query interface as E."""
    import numpy as np

    cells = {}
    for (cik, acc), d in C.docs.items():
        si = d["session"]
        if si < C.sess_idx[C.grid[0]] or si > C.sess_idx[C.grid_end]:
            continue   # permutation support = compliance window only
        sec = C.bookable[cik]["sector"]
        if not sec:
            continue
        cells.setdefault((si, sec), []).append((cik, acc, d["flag"]))
    rng = np.random.default_rng(seed)
    sham_flagged = {}          # (cik, si) -> True
    sham_vD_flag_sess = {}     # (cik, si) -> flagged D value
    cells_processed = 0
    docs_permuted = 0
    for (si, sec) in sorted(cells):
        members = sorted(cells[(si, sec)])
        k = sum(1 for _c, _a, f in members if f)
        docs_permuted += len(members)
        chosen = set()
        if k > 0:
            perm = rng.permutation(len(members))
            chosen = {int(perm[j]) for j in range(k)}
        for j, (cik, acc, _f) in enumerate(members):
            if j in chosen:
                sham_flagged[(cik, si)] = True
                v = C.docs[(cik, acc)]["vD"]
                if v:
                    sham_vD_flag_sess[(cik, si)] = \
                        sham_vD_flag_sess.get((cik, si), 0.0) + v
        cells_processed += 1

    # rebuild per-entity prefix arrays for the two sham quantities
    per_ent = {}
    for (cik, si) in sham_flagged:
        per_ent.setdefault(cik, []).append(si)
    Esham = {}
    for cik in sorted(per_ent):
        idxs = sorted(per_ent[cik])
        n = len(idxs)
        fs = [0] * n
        vf = [0.0] * n
        for i, si in enumerate(idxs):
            fs[i] = 1
            vf[i] = sham_vD_flag_sess.get((cik, si), 0.0)
        for i in range(1, n):
            fs[i] += fs[i - 1]
            vf[i] += vf[i - 1]
        Esham[cik] = {"sess_idx": idxs, "cum_flag_sess": fs,
                      "cum_vD_flag": vf}
    C.Esham = Esham
    return {"cells": cells_processed, "docs_in_support": docs_permuted,
            "flagged_docs_assigned": len(sham_flagged), "seed": seed}


def fdens_sham(C, cik, t_iso):
    E = getattr(C, "Esham", {}).get(cik)
    if E is None:
        return None
    gi = C.sess_idx[t_iso]
    hi = bisect_right(E["sess_idx"], gi) - 1
    if hi < 0:
        return None
    lo = bisect_left(E["sess_idx"], gi - TRAIL_SESSIONS + 1)
    fs = E["cum_flag_sess"]
    v = fs[hi] - (fs[lo - 1] if lo > 0 else 0)
    return float(v) if v >= 1 else None


def planshare_sham(C, cik, t_iso):
    """P2 anchor recomputed under permuted flags: numerator = D-value of
    docs carrying a PERMUTED flag; denominator unchanged (all D rows)."""
    if not has_E(C, cik):
        return None
    b = _win63(C, cik, t_iso)
    if b is None:
        return None
    v_all = _pfx(C, cik, "vD", b, is_value=True)
    if v_all < P2_VALUE_FLOOR:
        return None
    if _pfx(C, cik, "nndD", b) < P2_MIN_D_ROWS:
        return None
    E = getattr(C, "Esham", {}).get(cik)
    if E is None:
        return None
    gi = C.sess_idx[t_iso]
    hi = bisect_right(E["sess_idx"], gi) - 1
    lo = bisect_left(E["sess_idx"], gi - TRAIL_SESSIONS + 1)
    if hi < 0:
        return None
    vf = E["cum_vD_flag"]
    return (vf[hi] - (vf[lo - 1] if lo > 0 else 0.0)) / v_all
