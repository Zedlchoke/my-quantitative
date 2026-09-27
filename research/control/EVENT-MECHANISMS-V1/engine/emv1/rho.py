"""E5 — ancestry / representation rho battery (pre-PnL, bar 0.20 immovable).

Identity stream: event -> (name, entry_session, direction) decision records,
projected onto a signed per-(name, session) indicator (0 where no event).
Proxy dead-observables constructed from the staged bytes (constructions
documented in REPORT.md):
  reversal_5d / reversal_20d : -sign(raw k-session return) evaluated on the
                               last CLOSED session before t (bars t-1 and
                               t-1-k) => unfinished-window safe for a
                               decision taken at t's open.
  momentum_60d               : +sign of the same 60-session raw return.
  amihud_28d / amihud_63d    : mean(|ret_1d| / dollar-volume) over the
                               trailing k closed sessions, cross-sectionally
                               percentile-ranked per session, scaled [-1,1].
  declared_plan_cadence      : per issuer, count of aff10b5One='1' flagged
                               purchase accessions in the trailing 180
                               calendar days (universe = the A2 parsed
                               accession set — recorded limitation).
Rho = Spearman + Pearson, pooled and per fold. A1-vs-A2 stream rho computed
on the union grid (RECORD ONLY, merge condition not adjudicated here).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from . import config as C
from .panel import NameSeries

_FOLD_CODES = {"POOLED": -1, "F1": 0, "F2": 1, "F3": 2, "F4": 3}


def _rank_avg(a: np.ndarray) -> np.ndarray:
    order = np.argsort(a, kind="stable")
    ranks = np.empty(len(a), dtype=np.float64)
    sa = a[order]
    i = 0
    n = len(a)
    while i < n:
        j = i
        while j + 1 < n and sa[j + 1] == sa[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 3:
        return float("nan")
    sx = float(x.std())
    sy = float(y.std())
    if sx == 0.0 or sy == 0.0:
        return 0.0  # degenerate (all-ties) => no representational overlap
    return float(np.mean((x - x.mean()) * (y - y.mean())) / (sx * sy))


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    return _pearson(_rank_avg(x), _rank_avg(y))


def fold_codes_for(ns: NameSeries) -> np.ndarray:
    """Per-session fold code: 0..3 = F1..F4, 4 = outside (excluded from
    per-fold scopes)."""
    codes = np.full(len(ns.dates), 4, dtype=np.int8)
    dates = ns.dates
    for code, (_, lo, hi) in enumerate(C.FOLDS):
        for i, d in enumerate(dates):
            if lo <= d < hi:
                codes[i] = code
    return codes


def identity_indicator(
    records: List[dict], panel_names: Dict[str, NameSeries]
) -> Dict[str, np.ndarray]:
    out: Dict[str, np.ndarray] = {}
    for r in records:
        t = r["ticker"]
        ns = panel_names.get(t)
        if ns is None:
            continue
        if t not in out:
            out[t] = np.zeros(len(ns.dates), dtype=np.float64)
        i = ns.idx.get(r["entry_session"])
        if i is None:
            continue
        sign = 1.0 if r["direction"] == "LONG" else -1.0
        if out[t][i] != 0.0 and out[t][i] != sign:
            out[t][i] = 0.0  # opposing same-session events cancel
        else:
            out[t][i] = sign
    return out


def proxy_reversal(ns: NameSeries, k: int) -> np.ndarray:
    """-sign(raw k-session return) on bars t-1, t-1-k (closed before t)."""
    n = len(ns.dates)
    out = np.zeros(n, dtype=np.float64)
    if n <= k + 1:
        return out
    c = np.asarray(ns.close)
    r = c[k:-1] / c[: n - 1 - k] - 1.0
    out[k + 1 :] = np.where(r < 0, -1.0, np.where(r > 0, 1.0, 0.0))
    return out


def proxy_momentum(ns: NameSeries, k: int = 60) -> np.ndarray:
    return -proxy_reversal(ns, k)  # momentum = +sign of the same return


def proxy_amihud(ns: NameSeries, k: int) -> np.ndarray:
    """Trailing-k mean |ret|/dollar-volume (closed sessions), raw basis."""
    n = len(ns.dates)
    out = np.zeros(n, dtype=np.float64)
    if n < 3:
        return out
    c = np.asarray(ns.close)
    dv = np.asarray(ns.dv)
    ret = np.zeros(n, dtype=np.float64)
    ret[1:] = np.where(c[:-1] > 0, c[1:] / c[:-1] - 1.0, 0.0)
    illiq = np.zeros(n, dtype=np.float64)
    ok = dv > 0
    illiq[ok] = np.abs(ret[ok]) / dv[ok]
    cs = np.concatenate(([0.0], np.cumsum(illiq)))
    for t in range(k + 1, n):
        out[t] = (cs[t] - cs[t - k]) / k
    return out


def cross_sectional_rank_scale(
    levels: Dict[str, np.ndarray], panel_names: Dict[str, NameSeries]
) -> Dict[str, np.ndarray]:
    """Per-session cross-sectional percentile rank scaled to [-1, 1]."""
    tickers = sorted(t for t in levels if t in panel_names)
    out: Dict[str, np.ndarray] = {
        t: np.zeros(len(panel_names[t].dates), dtype=np.float64) for t in tickers
    }
    if not tickers:
        return out
    max_len = max(len(panel_names[t].dates) for t in tickers)
    mat = np.full((len(tickers), max_len), np.nan, dtype=np.float64)
    for i, t in enumerate(tickers):
        v = levels[t]
        mat[i, : len(v)] = v
    for j in range(max_len):
        col = mat[:, j]
        valid = ~np.isnan(col)
        nv = int(valid.sum())
        if nv < 2:
            continue
        order = np.argsort(col[valid], kind="stable")
        ranks = np.empty(nv, dtype=np.float64)
        ranks[order] = np.arange(1, nv + 1)
        scaled = (ranks - 1) / max(1, nv - 1) * 2.0 - 1.0
        idxs = np.where(valid)[0]
        for k, ti in enumerate(idxs):
            out[tickers[ti]][j] = scaled[k]
    return out


def rho_table(
    identity: Dict[str, np.ndarray],
    proxies: Dict[str, Dict[str, np.ndarray]],
    panel_names: Dict[str, NameSeries],
) -> List[dict]:
    """Pooled + per-fold Spearman/Pearson for each identity-proxy pair."""
    fold_codes = {t: fold_codes_for(ns) for t, ns in panel_names.items() if t in identity}
    rows = []
    for px_name, px_by_t in proxies.items():
        for scope in ("POOLED", "F1", "F2", "F3", "F4"):
            xs, ys = [], []
            for t, idv in identity.items():
                px = px_by_t.get(t)
                ns = panel_names.get(t)
                if px is None or ns is None:
                    continue
                n = min(len(idv), len(px), len(ns.dates))
                iv, pv = idv[:n], px[:n]
                if scope == "POOLED":
                    xs.append(iv)
                    ys.append(pv)
                else:
                    code = _FOLD_CODES[scope]
                    mask = fold_codes[t][:n] == code
                    if mask.any():
                        xs.append(iv[mask])
                        ys.append(pv[mask])
            if not xs:
                continue
            x = np.concatenate(xs)
            y = np.concatenate(ys)
            sp = spearman(x, y) if len(x) >= 3 else float("nan")
            pe = _pearson(x, y)
            over = (sp == sp) and abs(sp) > C.RHO_BAR
            rows.append({
                "proxy": px_name, "scope": scope, "n_points": int(len(x)),
                "n_nonzero_identity": int((x != 0).sum()),
                "spearman": None if sp != sp else round(sp, 6),
                "pearson": round(pe, 6),
                "bar": C.RHO_BAR,
                "over_bar": bool(over),
            })
    return rows


def stream_rho_between(
    ind_a: Dict[str, np.ndarray], ind_b: Dict[str, np.ndarray],
    panel_names: Dict[str, NameSeries],
) -> List[dict]:
    """A1-vs-A2 event-stream representation rho (RECORD ONLY, no
    adjudication) on each scope's grid."""
    rows = []
    fold_codes = {t: fold_codes_for(ns) for t, ns in panel_names.items()
                  if t in ind_a or t in ind_b}
    for scope in ("POOLED", "F1", "F2", "F3", "F4"):
        ax, bx = [], []
        for t, ns in sorted(panel_names.items()):
            a = ind_a.get(t)
            b = ind_b.get(t)
            if a is None or b is None:
                continue
            n = min(len(a), len(b), len(ns.dates))
            av, bv = a[:n], b[:n]
            if scope == "POOLED":
                ax.append(av)
                bx.append(bv)
            else:
                code = _FOLD_CODES[scope]
                mask = fold_codes[t][:n] == code
                if mask.any():
                    ax.append(av[mask])
                    bx.append(bv[mask])
        if not ax:
            continue
        a = np.concatenate(ax)
        b = np.concatenate(bx)
        sp = spearman(a, b) if len(a) >= 3 else float("nan")
        rows.append({
            "pair": "A1_vs_A2_event_streams", "scope": scope,
            "n_points": int(len(a)),
            "n_a_nonzero": int((a != 0).sum()), "n_b_nonzero": int((b != 0).sum()),
            "overlap_points": int(((a != 0) & (b != 0)).sum()),
            "spearman": None if sp != sp else round(sp, 6),
            "pearson": round(_pearson(a, b), 6),
            "merge_condition_note": "rho > 0.20 => A2 collapses into A1 (G1 court) — RECORD ONLY",
        })
    return rows
