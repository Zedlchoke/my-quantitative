"""STOCKS-NG2 D2 exposures: anchors, arrival shadow, sham permutation.

Anchor exposures (proposal definitions, verbatim):

  amendlag(e,t)    SFNG2-A4-P1: MEDIAN of d(p) in calendar days over the
                   entity's resolvable measurement pairs whose AMENDMENT
                   acceptance session falls in the trailing 63 trading
                   sessions ending at decision close t; defined iff
                   >= 1 in-window pair (P1 definition floor).  Even
                   counts average the two middle order statistics.
  cdays(e,t)       SFNG2-A4-P2: (sum over P(e,t) of dV(p)) / ADV63 dollars;
                   dV(p) = V(A_p) - V(O_p) doc-level D-coded totals
                   (shares x raw close at each doc's own acceptance date
                   - no dollar value field exists on either surface);
                   defined iff >= 1 in-window pair with MEASURED dV != 0
                   (zero-correction pairs are contentless: excluded by
                   the floor, never zero-ranked).

Controls:

  arrival shadow   exposure_arr(e,t) = log1p(n4), n4 = the entity's
                   Form-4 acceptance EVENTS of ANY kind (type-4 stream
                   accessions + every parseable 4/A doc attributed to a
                   cohort issuer, pair or not) in the trailing 63
                   sessions; no pair, no lag, no direction.
  sham             sham_amendment_matched_original_only (both proposals'
                   control class): within each (amendment-acceptance-
                   session, sector) cell, reassign the observed pair
                   values (P1: lags; P2: dVs) across the cell's ENTITY
                   support uniformly at random, preserving each cell's
                   value MULTISET EXACTLY, destroying the value-to-issuer
                   linkage.  Support = treatment entities with a pair in
                   the cell + matched original-only cohort entities of
                   the same sector with >= 1 type-4 stream acceptance
                   session in the trailing 63 sessions ending at the
                   cell session and ZERO resolvable measurement pairs in
                   the whole compliance window (the proposal's matched
                   original-only cohort basis, sector+window-mass legs;
                   the size-class stratum is a scoring-time book leg and
                   does not change the D2 permutation support).  numpy
                   PCG64 seed 20260912; cells in (session, sector)
                   order, values (origin entity, accession)-sorted; the
                   full anchor machinery is then recomputed unchanged on
                   the permuted events.
"""

from __future__ import annotations

import math
from bisect import bisect_left, bisect_right

from . import core
from .core import SHAM_SEED, TRAIL_SESSIONS


# ------------------------------------------------------------ windows --------
def _win_events(E4a, cik, t_iso, sess_idx):
    """[(lag, dv), ...] of events in the trailing 63 sessions ending at
    t (inclusive); [] when none.  t must be a grid session."""
    E = E4a.get(cik)
    if E is None:
        return []
    gi = sess_idx[t_iso]
    hi = bisect_right(E["sess_idx"], gi) - 1
    if hi < 0:
        return []
    lo = bisect_left(E["sess_idx"], gi - TRAIL_SESSIONS + 1)
    return [E["events"][i] for i in range(lo, hi + 1)]


def _median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    if n % 2 == 1:
        return float(s[n // 2])
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


# ------------------------------------------------------------- anchors -------
def amendlag(C, cik, t_iso):
    """P1 anchor: median pair-lag over the trailing-63-session amendment
    acceptance window; defined iff >= 1 in-window pair."""
    evs = _win_events(C.E4a, cik, t_iso, C.sess_idx)
    if not evs:
        return None
    return _median([lag for lag, _dv in evs])


def cdays(C, cik, t_iso):
    """P2 anchor: signed corrected-disposition days = sum(dV)/ADV63 over
    the trailing-63-session window; floor: >= 1 in-window pair with
    MEASURED dV != 0."""
    evs = _win_events(C.E4a, cik, t_iso, C.sess_idx)
    if not any(dv is not None and dv != 0.0 for _lag, dv in evs):
        return None
    adv = core.adv63(C, cik, t_iso)
    if adv is None or adv <= 0:
        return None
    return sum(dv for _lag, dv in evs if dv is not None) / adv


def arrival_shadow(C, cik, t_iso):
    """Filing-arrival clock shadow: log1p(n4), n4 = Form-4 acceptance
    events of ANY kind (type-4 + 4/A) in the trailing 63 sessions."""
    from research.assets.stocks_ng1.d2.exposures import _win63, _pfx, has_E
    gi = C.sess_idx[t_iso]
    n4 = 0
    if has_E(C, cik):
        b = _win63(C, cik, t_iso)
        if b is not None:
            n4 += _pfx(C, cik, "docs", b)
    A = getattr(C, "Arr4a", {}).get(cik)
    if A is not None:
        hi = bisect_right(A["sess_idx"], gi) - 1
        if hi >= 0:
            lo = bisect_left(A["sess_idx"], gi - TRAIL_SESSIONS + 1)
            n4 += A["cum"][hi] - (A["cum"][lo - 1] if lo > 0 else 0)
    if n4 < 1:
        return None
    return math.log1p(n4)


# ---------------------------------------------------------- sham -------------
def _matched_original_only_support(C, cell_si, sector, treat_entities):
    """Matched original-only support for one cell: same-sector cohort
    entities with >= 1 type-4 stream acceptance session in the trailing
    63 sessions ending at the cell session and ZERO resolvable
    measurement pairs in the compliance window."""
    have_pairs = set(C.E4a.keys())
    out = []
    for cik in sorted(C.bookable):
        if cik in have_pairs or cik in treat_entities:
            continue
        if C.bookable[cik]["sector"] != sector:
            continue
        E = C.E.get(cik)
        if E is None:
            continue
        hi = bisect_right(E["sess_idx"], cell_si) - 1
        if hi < 0:
            continue
        if E["sess_idx"][hi] < cell_si - TRAIL_SESSIONS + 1:
            continue
        out.append(cik)
    return out


def build_sham(C, seed: int = SHAM_SEED):
    """Pair-value permutation sham (both proposals' control class; see
    module docstring).  Deterministic under the frozen seed; rebuilds
    per-entity sham event structures with the SAME query interface as
    E4a (two variants: lags and dVs)."""
    import numpy as np

    cells = {}
    for cik, E in C.E4a.items():
        sector = C.bookable[cik]["sector"]
        if not sector:
            continue
        for i, si in enumerate(E["sess_idx"]):
            if not (C.sess_idx[C.grid[0]] <= si
                    <= C.sess_idx[C.grid_end]):
                continue          # permutation support = compliance window
            lag, dv = E["events"][i]
            cells.setdefault((si, sector), []).append(
                (cik, E["accs"][i], lag, dv))

    rng = np.random.default_rng(seed)
    sham_lag = {}      # (cik, si) -> list of lags
    sham_dv = {}       # (cik, si) -> list of dvs
    cells_processed = 0
    values_permuted = 0
    support_sizes = []
    for (si, sector) in sorted(cells):
        members = sorted(cells[(si, sector)])
        treat = {c for c, _a, _l, _d in members}
        support = sorted(treat | set(
            _matched_original_only_support(C, si, sector, treat)))
        support_sizes.append(len(support))
        values = [(c, a, l, d) for c, a, l, d in members]
        values_permuted += len(values)
        cells_processed += 1
        draws = rng.integers(0, len(support), size=len(values))
        for j, (c, a, l, d) in enumerate(values):
            recv = support[int(draws[j])]
            sham_lag.setdefault((recv, si), []).append(l)
            sham_dv.setdefault((recv, si), []).append(d)

    def _rebuild(table):
        per_ent = {}
        for (cik, si) in table:
            per_ent.setdefault(cik, []).append(si)
        out = {}
        for cik in sorted(per_ent):
            sis = sorted(per_ent[cik])
            evs = [None] * len(sis)
            for i, si in enumerate(sis):
                evs[i] = table[(cik, si)]
            out[cik] = {"sess_idx": sis,
                        "sess_d": [C.sessions[i] for i in sis],
                        "events": evs, "accs": [None] * len(sis)}
        return out

    C.Esham_lag = _rebuild(sham_lag)
    C.Esham_dv = _rebuild(sham_dv)
    # multiset preservation evidence (per-cell value multisets identical)
    return {
        "seed": seed,
        "cells": cells_processed,
        "values_permuted": values_permuted,
        "support_size_min": min(support_sizes) if support_sizes else 0,
        "support_size_max": max(support_sizes) if support_sizes else 0,
        "support_size_mean": (round(sum(support_sizes) / len(support_sizes), 2)
                              if support_sizes else 0.0),
    }


def amendlag_sham(C, cik, t_iso):
    E = getattr(C, "Esham_lag", {}).get(cik)
    if E is None:
        return None
    gi = C.sess_idx[t_iso]
    hi = bisect_right(E["sess_idx"], gi) - 1
    if hi < 0:
        return None
    lo = bisect_left(E["sess_idx"], gi - TRAIL_SESSIONS + 1)
    if hi < lo:
        return None
    return _median([E["events"][i][k] for i in range(lo, hi + 1)
                    for k in range(len(E["events"][i]))])


def cdays_sham(C, cik, t_iso):
    E = getattr(C, "Esham_dv", {}).get(cik)
    if E is None:
        return None
    gi = C.sess_idx[t_iso]
    hi = bisect_right(E["sess_idx"], gi) - 1
    if hi < 0:
        return None
    lo = bisect_left(E["sess_idx"], gi - TRAIL_SESSIONS + 1)
    if hi < lo:
        return None
    dvs = [d for i in range(lo, hi + 1) for d in E["events"][i]]
    if not any(d is not None and d != 0.0 for d in dvs):
        return None
    adv = core.adv63(C, cik, t_iso)
    if adv is None or adv <= 0:
        return None
    return sum(d for d in dvs if d is not None) / adv
