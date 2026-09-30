"""Stage-A TRAIN diagnostics runner — PC12A wave 2 (the campaign's FIRST
PnL computation; TRAIN folds ONLY, labeled DISCOVERY-TRAIN-ONLY).

Usage:
    .venv/bin/python -m research.pc12a.run_diag \
        --legs <dir of floor-passed leg configs> \
        --out research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics \
        [--symbols EURUSD,GBPUSD] [--x2] [--controls] \
        [--ledger <TRIAL_LEDGER.jsonl>] [--ledger-stop-at 1400] [--lock]

Laws implemented here:

- TRAIN-ONLY partition: every PnL window is [first campaign Friday,
  fold_k.train_end] of the frozen 8-fold expanding walk-forward
  (calendar_service.fold_calendar). Test folds and the sealed 26w tail are
  NEVER computed on: the longest stream ends at fold 7's train_end
  (2025-06-20), 14 days before test fold 7 starts (2025-07-04) and well
  before the sealed tail (2026-01-02). Partition arithmetic proven in
  tests/test_pc12a_stageA_wave2.py (disjointness, embargo, prefix identity
  vs genuinely truncated re-runs).
- Solo-leg engines: each leg runs in its own SymbolEngine (no cross-leg
  netting) so PnL attribution is the leg's own. DISCLOSED deviation vs the
  multi-leg dry-run: the E1 floor arms 26w after the engine's FIRST
  decision; solo, that is the LEG's own first decision (dry-run: the
  symbol's fastest sibling). Both are frozen-engine behaviors; solo is the
  diagnostic semantic ("a full 26w of the LEG's history").
- Accounting per FILL_ACCOUNTING_SPEC / books.py: equity = cash + units *
  mid mark; net = gross_vs_mid - spread - slip - commission - swap; the
  decomposition residual is asserted <= 1e-6 per fold and recorded.
- x2.0 stress: a full separate tier-2.0 pass per leg over the fold-7 TRAIN
  window (the whole TRAIN span); TRAIN expectancy@x2.0 <= 0 -> typed
  COST_DOMINATED kill row.
- VOLPROF controls per CLASS_SPEC_VOLPROF_M1 r2 section 7: CTRL-A
  dwell-matched random-entry and CTRL-C clock-only shadow, seeded
  deterministically from (arm, fold, ctrl); single replicate per fold
  (multi-seed ensembles are Stage-B/C re-runs if kill adjudication needs
  them; the comparison vs the arm is recorded, adjudication is NOT
  performed here).
- Discovery ledger budget: appends stop at --ledger-stop-at rows
  (dispatch: stop before 1400 of the 1500 cap; never silent).

Outputs (PnL-bearing, ALL labeled DISCOVERY-TRAIN-ONLY):
  diagnostics/DIAG_MAIN_{SYM}.json, DIAG_X2_{SYM}.json,
  diagnostics/DIAG_CONTROLS.json, diagnostics/COMPLEMENTARITY_TRAIN.json,
  diagnostics/DIAG_MANIFEST.json + TRIAL_LEDGER.jsonl appends.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional

import numpy as np

from . import calendar_service as cal
from . import cost_kernel as _ck
from . import legs as _legs
from . import panels as _panels
from . import policy as _pol
from . import run_dry as _rd

UTC = dt.timezone.utc
CYCLE = "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
INITIAL_CASH = 100_000.0
RESIDUAL_TOL = 1e-6
LABEL = "DISCOVERY-TRAIN-ONLY"
ROOT_CHECKOUT = "/Users/hoangminhlong/my-quantitative"


class _DiagJournal:
    """No-op journal that signals NET_ORDER events to the engine: the
    engine also calls price_ordinary_fill on the cost-guard ESTIMATE and
    ONOFF-twin paths, so only a fill confirmed by a NET_ORDER row is a
    real book event (fills are staged and committed on NET_ORDER)."""

    n_rows = 0

    def __init__(self):
        self.engine = None

    def write(self, kind: str, row: Dict) -> None:
        self.n_rows += 1
        if kind == "NET_ORDER" and self.engine is not None:
            self.engine._commit_staged_fill()


class _Args:
    def __init__(self, window_start: dt.date, window_end: dt.date,
                 tier: float):
        self.window_start = window_start
        self.window_end = window_end
        self.tier = tier


def _fmt(t: dt.datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class FoldSnapshot:
    """Aggregates of one leg over one fold's expanding TRAIN prefix."""

    def __init__(self, fold: cal.Fold):
        self.fold = fold
        self.n_decisions = 0
        self.fills: List[Dict] = []
        self.swaps: List[Dict] = []
        self.mark: Optional[float] = None
        self.units = 0
        self.cash = INITIAL_CASH
        self.friday_equity: Dict[dt.date, float] = {}

    def finalize(self, episodes: List[Dict]) -> Dict:
        mark = self.mark if self.mark is not None else 0.0
        equity = self.cash + self.units * mark
        gross = sum(f["delta"] * (mark - f["fq"].mid_at_fill)
                    for f in self.fills)
        cost = sum(f["fq"].spread_once_usd
                   + f["fq"].slip_beyond_halfspread_usd
                   + f["commission"] for f in self.fills) \
            + sum(s["usd"] for s in self.swaps)
        net = equity - INITIAL_CASH
        residual = (gross - cost) - net
        pos = 0
        n_entries = 0
        for f in self.fills:
            before = pos
            pos += f["delta"]
            if before == 0 and pos != 0:
                n_entries += 1
        return {
            "fold_id": self.fold.fold_id,
            "train_window": [self.fold.train_start.isoformat(),
                             self.fold.train_end.isoformat()],
            "n_decisions": self.n_decisions,
            "n_fills": len(self.fills),
            "n_entries": n_entries,
            "n_closed_episodes": len(episodes),
            "n_swap_events": len(self.swaps),
            "mark_close": round(mark, 8),
            "units_open": self.units,
            "gross_pnl_usd": round(gross, 6),
            "cost_total_usd": round(cost, 6),
            "net_pnl_usd": round(net, 6),
            "residual_usd": round(residual, 9),
            "expectancy_per_trade_usd": (
                round(net / n_entries, 6) if n_entries else None),
            "friday_equity": {d.isoformat(): round(v, 6)
                              for d, v in self.friday_equity.items()},
        }


class DiagEngine(_rd.SymbolEngine):
    """Solo-leg SymbolEngine with fold-boundary + Friday-equity snapshots.

    The stream runs ONCE over the LONGEST TRAIN prefix (fold 7); snapshots
    at each earlier fold boundary are exact prefix aggregates (the
    truncation-prefix law; proven by test against genuinely truncated
    re-runs).
    """

    def __init__(self, symbol: str, cfg: Dict, store, folds: List[cal.Fold],
                 tier: float):
        args = _Args(folds[0].train_start, folds[-1].train_end, tier)
        lid = cfg.get("class_candidate_id") or cfg["corpus_gid"]
        report = {
            "legs": {lid: {"decisions": 0, "votes": {},
                           "fills_by_outcome": {}}},
            "cost_bill_totals_usd": {"spread_once": 0.0, "slip": 0.0,
                                     "slip_gap_excess": 0.0,
                                     "commission": 0.0, "swap": 0.0},
            "blocked_reason_histogram": {},
        }
        super().__init__(symbol, [cfg], args, _DiagJournal(),
                         _pol.CostGuard(_pol.CostGuardState()), report)
        self.journal.engine = self
        self.diag_window_end = folds[-1].train_end
        self.diag_store = store
        self.fold_by_end = {f.train_end: f for f in folds}
        self.snapshots: Dict[int, FoldSnapshot] = {
            f.fold_id: FoldSnapshot(f) for f in folds}
        self._captured_fills: List[Dict] = []
        self._staged_fills: List[Dict] = []
        self._captured_swaps: List[Dict] = []
        self._friday_equity: Dict[dt.date, float] = {}
        self._now_ts: Optional[dt.datetime] = None
        self._swap_ts: Optional[dt.datetime] = None
        orig_fill = self.kernel.price_ordinary_fill
        orig_swap = self.kernel.swap_usd

        def cap_fill(side, delta_units, bid_open, ask_open):
            fq = orig_fill(side, delta_units, bid_open, ask_open)
            signed = delta_units if side == "buy" else -delta_units
            # STAGED: committed only when the engine journals NET_ORDER
            # (the estimate/twin paths price quotes without booking)
            self._staged_fills.append({
                "ts": self._now_ts, "delta": signed, "fq": fq,
                "commission": self.kernel.commission(
                    delta_units, fq.fill_price)})
            return fq

        def cap_swap(units_abs, mult, mid):
            usd = orig_swap(units_abs, mult, mid)
            if units_abs:
                self._captured_swaps.append({"ts": self._swap_ts,
                                             "usd": usd})
            return usd

        self.kernel.price_ordinary_fill = cap_fill
        self.kernel.swap_usd = cap_swap

    def _commit_staged_fill(self) -> None:
        if self._staged_fills:
            self._captured_fills.append(self._staged_fills[-1])
            self._staged_fills.clear()

    def _apply_decisions(self, decisions, ts, day, m):
        self._now_ts = ts
        super()._apply_decisions(decisions, ts, day, m)
        self._staged_fills.clear()

    def _process_day(self, day, date):
        self._swap_ts = dt.datetime.combine(date, dt.time(22, 0),
                                            tzinfo=UTC)
        super()._process_day(day, date)
        mark = self.last_mid_close
        if mark is not None and date.strftime("%a") == "Fri":
            self._friday_equity[date] = self.cash \
                + self.book_units * float(mark)
        fold = self.fold_by_end.get(date)
        if fold is not None:
            self._take_snapshot(fold)

    def _take_snapshot(self, fold: cal.Fold) -> None:
        snap = self.snapshots[fold.fold_id]
        lid = self.legs[0].identity.candidate_id
        snap.n_decisions = self.report["legs"][lid]["decisions"]
        end_ts = dt.datetime.combine(fold.train_end, dt.time(23, 59, 59),
                                     tzinfo=UTC)
        snap.fills = [f for f in self._captured_fills if f["ts"] <= end_ts]
        snap.swaps = [s for s in self._captured_swaps if s["ts"] <= end_ts]
        snap.mark = float(self.last_mid_close or 0.0)
        snap.units = int(self.book_units)
        snap.cash = float(self.cash)
        snap.friday_equity = {d: v for d, v in self._friday_equity.items()
                              if d <= fold.train_end}


def _episodes(fills: List[Dict]) -> List[Dict]:
    """Entry->exit episodes from a solo fill list."""
    out = []
    pos = 0
    entry = None
    for f in fills:
        before = pos
        pos += f["delta"]
        if before == 0 and pos != 0:
            entry = f
        elif entry is not None and pos == 0:
            out.append({
                "entry_ts": entry["ts"], "exit_ts": f["ts"],
                "direction": 1 if entry["delta"] > 0 else -1,
                "units": abs(entry["delta"]),
                "entry_fq": entry["fq"], "exit_fq": f["fq"],
                "entry_commission": entry["commission"],
                "exit_commission": f["commission"]})
            entry = None
    return out


def run_leg_diag(symbol: str, cfg: Dict, store, folds: List[cal.Fold],
                 tier: float, digest: Optional[str] = None) -> Dict:
    """One solo-leg stream over the longest of `folds` TRAIN prefixes."""
    eng = DiagEngine(symbol, cfg, store, folds, tier)
    eng.run(store)
    ident = _legs.make_identity(cfg)
    per_fold_episodes: Dict[int, List[Dict]] = {}
    finalized = []
    for f in folds:
        eps = _episodes(eng.snapshots[f.fold_id].fills)
        per_fold_episodes[f.fold_id] = eps
        finalized.append(eng.snapshots[f.fold_id].finalize(eps))
    return {
        "leg_id": ident.candidate_id,
        "symbol": symbol,
        "sleeve_id": ident.sleeve_id,
        "family_id": ident.family_id,
        "cluster_id": ident.cluster_id,
        "mech_key": ident.mech_key,
        "outcome_exposed_label": ident.outcome_exposed_label,
        "arm_config_digest": ident.arm_config_digest,
        "tier": tier,
        "folds": finalized,
        "data_digest": digest or "",
        "episodes": per_fold_episodes,   # objects; NOT JSON-dumped
    }


def _dumpable(res: Dict) -> Dict:
    out = {k: v for k, v in res.items() if k != "episodes"}
    return out


# ---------------------------------------------------------------------------
# VOLPROF controls (CLASS_SPEC section 7a CTRL-A, 7c CTRL-C)
# ---------------------------------------------------------------------------


def _episode_net(ep: Dict, swaps_usd: float) -> float:
    pnl = (ep["exit_fq"].fill_price - ep["entry_fq"].fill_price) \
        * ep["direction"] * ep["units"]
    cost = (ep["entry_fq"].spread_once_usd
            + ep["entry_fq"].slip_beyond_halfspread_usd
            + ep["exit_fq"].spread_once_usd
            + ep["exit_fq"].slip_beyond_halfspread_usd
            + ep["entry_commission"] + ep["exit_commission"] + swaps_usd)
    return pnl - cost


def _nights_swap_usd(kernel, store, symbol: str, entry: dt.datetime,
                     exit_ts: dt.datetime, units_abs: float) -> float:
    total = 0.0
    for ev in cal.swap_events_between(entry, exit_ts):
        try:
            day = store.load_day(symbol, ev.ts_utc.date())
        except (FileNotFoundError, _panels.PanelError):
            continue
        tradable = day.tradable_mask()
        mins = np.nonzero(tradable)[0]
        if not len(mins):
            continue
        upto = mins[mins <= 22 * 60]
        mid = float(day.mid_close[int(upto[-1])]) if len(upto) else None
        if mid is None:
            continue
        total += kernel.swap_usd(units_abs, ev.multiplier, mid)
    return total


def _next_tradable_minute(store, symbol: str, ts: dt.datetime):
    """First tradable bar AT/after ts; returns (day, minute_index, close_ts)
    — engine fill semantics (the [T,T+1) bar's OPEN prices the fill)."""
    d = ts.date()
    for _ in range(4):
        try:
            day = store.load_day(symbol, d)
        except (FileNotFoundError, _panels.PanelError):
            d += dt.timedelta(days=1)
            continue
        tradable = day.tradable_mask()
        mins = np.nonzero(tradable)[0]
        if not len(mins):
            d += dt.timedelta(days=1)
            continue
        want = ts.hour * 60 + ts.minute if d == ts.date() else 0
        cand = mins[mins >= want]
        if len(cand):
            m = int(cand[0])
            bar_ts = dt.datetime.combine(d, dt.time(0, 0), tzinfo=UTC) \
                + dt.timedelta(minutes=m + 1)
            return day, m, bar_ts
        d += dt.timedelta(days=1)
    return None


def run_control(symbol: str, leg_id: str,
                arm_folds: Dict[int, Dict], store,
                kernel: _ck.CostKernel, folds: List[cal.Fold],
                ctrl: str) -> Dict[int, Dict]:
    """CTRL-A (dwell-matched) / CTRL-C (clock-only) per fold, seeded.

    CTRL-A: same dwell per trade, entry minute uniform within a
    (weekday, hour) cell sampled from the arm's own entry occupancy,
    direction drawn from the arm's realized long/short ratio, cost bill
    via the same kernel path (fill-bar measured quotes + swap nights).
    CTRL-C: same occupancy sampling and count, dwell = the arm's realized
    hold quantiles, same direction draw.
    """
    out: Dict[int, Dict] = {}
    for fold in folds:
        eps = arm_folds[fold.fold_id]
        n = len(eps)
        seed = int.from_bytes(hashlib.sha256(
            f"{symbol}|{leg_id}|{fold.fold_id}|{ctrl}".encode()
        ).digest()[:8], "big")
        rng = np.random.default_rng(seed)
        if n == 0:
            out[fold.fold_id] = {"n_trades": 0, "net_pnl_usd": 0.0,
                                 "expectancy_per_trade_usd": None,
                                 "seed": seed, "n_unplaced": 0}
            continue
        cells: Dict[tuple, int] = {}
        for ep in eps:
            key = (ep["entry_ts"].weekday(), ep["entry_ts"].hour)
            cells[key] = cells.get(key, 0) + 1
        cell_keys = sorted(cells)
        cell_w = np.array([cells[k] for k in cell_keys], dtype=float)
        cell_w /= cell_w.sum()
        long_share = sum(1 for ep in eps if ep["direction"] > 0) / n
        dwell_sorted = sorted((ep["exit_ts"] - ep["entry_ts"]
                               for ep in eps),
                              key=lambda x: x.total_seconds())
        if ctrl == "CTRL-C":
            holds = [dwell_sorted[i] for i in range(n)]
        cands_by_wd: Dict[int, List[dt.date]] = {}
        dd = fold.train_start
        while dd <= fold.train_end:
            cands_by_wd.setdefault(dd.weekday(), []).append(dd)
            dd += dt.timedelta(days=1)
        nets: List[float] = []
        used: List[dt.datetime] = []
        n_unplaced = 0
        for i in range(n):
            dwell = (eps[i]["exit_ts"] - eps[i]["entry_ts"]) \
                if ctrl == "CTRL-A" else holds[i]
            placed = False
            for _ in range(60):
                ck = cell_keys[int(rng.choice(len(cell_keys), p=cell_w))]
                wd, hr = ck
                cands = cands_by_wd.get(wd)
                if not cands:
                    continue
                day_choice = cands[int(rng.integers(0, len(cands)))]
                minute = hr * 60 + int(rng.integers(0, 60))
                ts = dt.datetime.combine(
                    day_choice, dt.time(minute // 60, minute % 60),
                    tzinfo=UTC)
                if any(abs((ts - u).total_seconds()) < 3600 for u in used):
                    continue
                entry_bar = _next_tradable_minute(store, symbol, ts)
                if entry_bar is None:
                    continue
                day, m, bar_ts = entry_bar
                direction = 1 if rng.random() < long_share else -1
                units = eps[i]["units"]
                entry_fq = kernel.price_ordinary_fill(
                    "buy" if direction > 0 else "sell", units,
                    float(day.bid.open[m]), float(day.ask.open[m]))
                exit_bar = _next_tradable_minute(store, symbol,
                                                 bar_ts + dwell)
                if exit_bar is None:
                    continue
                xday, xm, xts = exit_bar
                exit_fq = kernel.price_ordinary_fill(
                    "sell" if direction > 0 else "buy", units,
                    float(xday.bid.open[xm]), float(xday.ask.open[xm]))
                swaps = _nights_swap_usd(kernel, store, symbol, bar_ts,
                                         xts, units)
                nets.append(_episode_net({
                    "entry_fq": entry_fq, "exit_fq": exit_fq,
                    "direction": direction, "units": units,
                    "entry_commission": kernel.commission(
                        units, entry_fq.fill_price),
                    "exit_commission": kernel.commission(
                        units, exit_fq.fill_price)}, swaps))
                used.append(ts)
                placed = True
                break
            if not placed:
                n_unplaced += 1
        out[fold.fold_id] = {
            "n_trades": n,
            "net_pnl_usd": round(float(sum(nets)), 6) if nets else 0.0,
            "expectancy_per_trade_usd": round(float(np.mean(nets)), 6)
            if nets else None,
            "seed": seed,
            "n_unplaced": n_unplaced,
        }
    return out


# ---------------------------------------------------------------------------
# complementarity (feeds Stage-B grouping)
# ---------------------------------------------------------------------------


def _pearson(x: List[float], y: List[float]) -> Optional[float]:
    if len(x) < 3:
        return None
    xa, ya = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if xa.std() == 0 or ya.std() == 0:
        return None
    c = float(np.corrcoef(xa, ya)[0, 1])
    return c if math.isfinite(c) else None


def complementarity(per_leg: Dict[str, Dict], folds: List[cal.Fold]) -> Dict:
    """Per-fold pairwise weekly-equity-delta correlation + co-loss weeks."""
    out: Dict[str, Dict] = {}
    legs = sorted(per_leg)
    for fold in folds:
        fk = fold.fold_id
        series: Dict[str, Dict[str, float]] = {}
        for leg in legs:
            fe = per_leg[leg]["folds"][fk]["friday_equity"]
            marks = [(d, fe[d]) for d in sorted(fe)]
            wk: Dict[str, float] = {}
            for i in range(1, len(marks)):
                d1, e1 = marks[i]
                e0 = marks[i - 1][1]
                y, w, _ = dt.date.fromisoformat(d1).isocalendar()
                wk[f"{y}-W{w:02d}"] = e1 - e0
            series[leg] = wk
        common = sorted(set.intersection(*(set(series[l]) for l in legs))) \
            if legs else []
        pairs = {}
        for i in range(len(legs)):
            for j in range(i + 1, len(legs)):
                a, b = legs[i], legs[j]
                if a not in series or b not in series:
                    continue
                xs = [series[a][k] for k in common if k in series[a]]
                ys = [series[b][k] for k in common if k in series[b]]
                if len(xs) != len(common):
                    xs, ys = [], []
                corr = _pearson(xs, ys) if xs else None
                co = sum(1 for x, y in zip(xs, ys) if x < 0 and y < 0)
                pairs[f"{a}|{b}"] = {
                    "corr": round(corr, 4) if corr is not None else None,
                    "co_loss_weeks": co, "n_weeks": len(xs)}
        out[str(fk)] = {"n_legs": len(legs), "n_weeks": len(common),
                        "pairs": pairs}
    return out


# ---------------------------------------------------------------------------
# ledger
# ---------------------------------------------------------------------------


def _ledger_len(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as fh:
        return sum(1 for _ in fh)


class LedgerBudgetExceeded(RuntimeError):
    pass


def append_rows(path: str, rows: List[Dict], stop_at: int) -> int:
    have = _ledger_len(path)
    if have + len(rows) > stop_at:
        raise LedgerBudgetExceeded(
            f"append of {len(rows)} would take the ledger from {have} "
            f"past the stop line {stop_at} (cap 1500)")
    now = dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(path, "a", encoding="utf-8") as fh:
        for i, r in enumerate(rows):
            r.setdefault("row_id", f"ADIAG-W2-{have + 1 + i:04d}")
            r.setdefault("cycle_id", CYCLE)
            r.setdefault("stage", "A-DIAG")
            r.setdefault("fold_scope", "TRAIN_ONLY")
            r.setdefault("label", LABEL)
            r.setdefault("recorded_utc", now)
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return have + len(rows)


def _row(res: Dict, f: Dict, tier: float, tag: str,
         gid: Optional[str] = None,
         result: str = "DIAG_TRAIN_COMPUTED", extra: Optional[Dict] = None,
         label_override: Optional[str] = None,
         outcome_label_override: Optional[str] = None) -> Dict:
    row = {
        "stage": "A-DIAG",
        "sleeve_id": res["sleeve_id"],
        "corpus_gid": gid or res["leg_id"],
        "arm_config_digest": res["arm_config_digest"],
        "outcome_exposed_label": outcome_label_override
        or res["outcome_exposed_label"],
        "cluster_id": res["cluster_id"],
        "fold_id": f["fold_id"],
        "train_window": f["train_window"],
        "n_decisions": f["n_decisions"],
        "n_trades": f.get("n_entries", f.get("n_trades")),
        "gross_pnl_usd": f["gross_pnl_usd"],
        "cost_total_usd": f["cost_total_usd"],
        "net_pnl_usd": f["net_pnl_usd"],
        "expectancy_per_trade_usd": f["expectancy_per_trade_usd"],
        "tier": tier,
        "pass_tag": tag,
        "residual_usd": f.get("residual_usd"),
        "result": result,
    }
    if label_override:
        row["label"] = label_override
    if extra:
        row.update(extra)
    return row


# ---------------------------------------------------------------------------
# heavy lock (root checkout governance module; machine-wide)
# ---------------------------------------------------------------------------


def _take_lock(command: List[str]):
    _gov = os.path.join(ROOT_CHECKOUT, "research")
    if _gov not in sys.path:
        sys.path.insert(0, _gov)
    from governance import heavy_lock

    return heavy_lock.acquire(
        cycle_id=CYCLE, role="stage-a-wave2-train-diag",
        worktree="/Users/hoangminhlong/my-quantitative/.worktrees/"
                 "portfolio-composite-12assets-100k-v1/integration",
        command=command,
        expected_artifacts=[
            "research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/"
            "diagnostics/COMPLEMENTARITY_TRAIN.json"])


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def _make_store(symbol: str):
    h1_env = os.environ.get("PC12A_H1_PARQUETS")
    if h1_env:
        mapping = json.loads(h1_env)
        if symbol in mapping:
            from . import h1_panels as _h1
            _h1.install()
            return _h1.H1PanelStore(roots={symbol: mapping[symbol]})
    return _panels.PanelStore()


def _symbol_digest(store, symbol: str, folds: List[cal.Fold]) -> str:
    root = store.roots.get(symbol, "")
    days = []
    d = folds[0].train_start - dt.timedelta(days=450)
    end = folds[-1].train_end
    if root.endswith(".parquet"):
        while d <= end:
            days.append(d)
            d += dt.timedelta(days=1)
    else:
        while d <= end:
            if os.path.exists(os.path.join(root, "BID",
                                           f"{d.isoformat()}.bi5")):
                days.append(d)
            d += dt.timedelta(days=1)
    return store.panel_digest(symbol, days)


def _serialize_episodes(res: Dict) -> Dict[str, List[Dict]]:
    out = {}
    for fk, eps in res["episodes"].items():
        out[str(fk)] = [{
            "entry_ts": _fmt(ep["entry_ts"]), "exit_ts": _fmt(ep["exit_ts"]),
            "direction": ep["direction"], "units": ep["units"]}
            for ep in eps]
    return out


def _parse_episodes(serialized: Dict[str, List[Dict]]) -> Dict[int, List[Dict]]:
    out = {}
    for fk, eps in serialized.items():
        out[int(fk)] = [{
            "entry_ts": dt.datetime.strptime(e["entry_ts"],
                                             "%Y-%m-%dT%H:%M:%SZ").replace(
                                                 tzinfo=UTC),
            "exit_ts": dt.datetime.strptime(e["exit_ts"],
                                            "%Y-%m-%dT%H:%M:%SZ").replace(
                                                tzinfo=UTC),
            "direction": e["direction"], "units": e["units"]}
            for e in eps]
    return out


def _write_pass(args, pass_type: str, symbol: str, results: List[Dict],
                digest: str, folds: List[cal.Fold], seconds: float) -> None:
    tier = 1.0 if pass_type == "MAIN" else 2.0
    tag = getattr(args, "file_tag", None)
    stem = f"{tag}_{symbol}" if tag else symbol
    payload_legs = []
    for r in results:
        d = _dumpable(r)
        if pass_type == "MAIN":
            d["episodes_serialized"] = _serialize_episodes(r)
        payload_legs.append(d)
    body = {"schema": "pc12a_diag_report@1", "label": LABEL, "tier": tier,
            "max_train_end": folds[-1].train_end.isoformat(),
            "data_digest": digest, "legs": payload_legs}
    with open(os.path.join(args.out, f"DIAG_{pass_type}_{stem}.json"),
              "w", encoding="utf-8") as fh:
        json.dump(body, fh, sort_keys=True, indent=1)
        fh.write("\n")
    print(json.dumps({"pass": pass_type, "symbol": symbol, "tag": tag,
                      "legs": len(results), "seconds": round(seconds, 1)}))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PC12A Stage-A TRAIN diag")
    ap.add_argument("--legs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--symbols", default=None)
    ap.add_argument("--gids", default=None,
                    help="optional comma list of leg gids (pass mode)")
    ap.add_argument("--mode", default="single",
                    choices=["single", "pass", "assemble"],
                    help="single: everything in this process; pass: one "
                         "MAIN or X2 pass, no ledger writes; assemble: "
                         "controls + complementarity + ledger appends from "
                         "the written pass files")
    ap.add_argument("--pass-type", default="MAIN", choices=["MAIN", "X2"])
    ap.add_argument("--file-tag", default=None,
                    help="pass mode: filename tag (default: symbol); "
                         "distinct tags keep split-group files from "
                         "overwriting each other")
    ap.add_argument("--x2", action="store_true",
                    help="(single mode) x2.0 full-TRAIN pass per leg")
    ap.add_argument("--controls", action="store_true",
                    help="(single mode) VOLPROF controls")
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--ledger-stop-at", type=int, default=1400)
    ap.add_argument("--lock", action="store_true")
    args = ap.parse_args(argv)

    t0 = time.time()
    folds = cal.fold_calendar()
    os.makedirs(args.out, exist_ok=True)
    ledger_path = args.ledger or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))),
        "research", "control", CYCLE, "TRIAL_LEDGER.jsonl")

    cfgs = _legs.load_leg_configs(args.legs)
    if args.gids:
        keep = set(args.gids.split(","))
        cfgs = [c for c in cfgs
                if (c.get("class_candidate_id") or c["corpus_gid"]) in keep]
    by_symbol: Dict[str, List[Dict]] = {}
    for c in cfgs:
        by_symbol.setdefault(c["symbol"], []).append(c)
    if args.symbols:
        keep = set(args.symbols.split(","))
        by_symbol = {s: v for s, v in by_symbol.items() if s in keep}

    # ------------------------------------------------------------------
    # PASS mode: one symbol group, one tier, no ledger writes
    # ------------------------------------------------------------------
    if args.mode == "pass":
        for symbol in sorted(by_symbol):
            ts = time.time()
            store = _make_store(symbol)
            pass_folds = folds if args.pass_type == "MAIN" else [folds[-1]]
            tier = 1.0 if args.pass_type == "MAIN" else 2.0
            digest = _symbol_digest(store, symbol, pass_folds)
            results = []
            for cfg in by_symbol[symbol]:
                res = run_leg_diag(symbol, cfg, store, pass_folds, tier,
                                   digest=digest)
                for f in res["folds"]:
                    assert abs(f["residual_usd"]) < RESIDUAL_TOL, \
                        f"{res['leg_id']} fold {f['fold_id']} residual " \
                        f"{f['residual_usd']}"
                results.append(res)
            _write_pass(args, args.pass_type, symbol, results, digest,
                        pass_folds, time.time() - ts)
        print(json.dumps({"done": True,
                          "elapsed": round(time.time() - t0, 1)}))
        return 0

    # ------------------------------------------------------------------
    # ASSEMBLE mode: controls + complementarity + ledger from pass files
    # ------------------------------------------------------------------
    if args.mode == "assemble":
        manifest = {"schema": "pc12a_diag_manifest@1", "label": LABEL,
                    "started_utc": _fmt(dt.datetime.now(UTC))}
        ledger_rows: List[Dict] = []
        main_legs: Dict[str, Dict] = {}
        for fn in sorted(os.listdir(args.out)):
            if not (fn.startswith("DIAG_MAIN_") and fn.endswith(".json")):
                continue
            body = json.load(open(os.path.join(args.out, fn),
                                  encoding="utf-8"))
            for leg in body["legs"]:
                main_legs[leg["leg_id"]] = leg
        # MAIN rows
        for lid in sorted(main_legs):
            leg = main_legs[lid]
            for f in leg["folds"]:
                ledger_rows.append(_row(leg, f, 1.0, "MAIN"))
        # X2 rows + typed kills
        n_kills = 0
        for fn in sorted(os.listdir(args.out)):
            if not (fn.startswith("DIAG_X2_") and fn.endswith(".json")):
                continue
            body = json.load(open(os.path.join(args.out, fn),
                                  encoding="utf-8"))
            for leg in body["legs"]:
                f = leg["folds"][0]
                exp = f["expectancy_per_trade_usd"]
                x2_result = ("DIAG_TRAIN_COMPUTED" if exp is not None
                             else "NO_ENTRIES_TRAIN")
                ledger_rows.append(_row(leg, f, 2.0, "X2",
                                        result=x2_result,
                                        extra={"stress_tier": 2.0}))
                if exp is not None and exp <= 0.0:
                    n_kills += 1
                    ledger_rows.append(_row(
                        leg, f, 2.0, "X2", result="COST_DOMINATED",
                        extra={"stress_tier": 2.0,
                               "detail": ("typed kill: TRAIN expectancy "
                                          "at x2.0 measured spread + "
                                          "DECLARED bands <= 0 per "
                                          "campaign §4")}))
        manifest["x2_kills"] = n_kills
        # controls
        control_out: Dict[str, Dict] = {}
        arm_by_symbol: Dict[str, List[str]] = {}
        for lid, leg in main_legs.items():
            if leg["sleeve_id"] == _legs.VOLPROF_SLEEVE:
                arm_by_symbol.setdefault(leg["symbol"], []).append(lid)
        for symbol in sorted(arm_by_symbol):
            store = _make_store(symbol)
            kernel = _ck.CostKernel(symbol, tier=1.0)
            for lid in sorted(arm_by_symbol[symbol]):
                arm = main_legs[lid]
                eps_by_fold = _parse_episodes(
                    arm["episodes_serialized"])
                for ctrl in ("CTRL-A", "CTRL-C"):
                    ctr = run_control(symbol, lid, eps_by_fold, store,
                                      kernel, folds, ctrl)
                    control_out[f"{lid}|{ctrl}"] = ctr
                    for fk in sorted(ctr):
                        c = ctr[fk]
                        f7 = arm["folds"][int(fk)]
                        ledger_rows.append({
                            "stage": "A-DIAG",
                            "sleeve_id": arm["sleeve_id"],
                            "corpus_gid": f"{lid}#{ctrl}",
                            "arm_config_digest": arm["arm_config_digest"],
                            "outcome_exposed_label":
                                "CONTROL_PLACEBO_SEEDED",
                            "cluster_id": arm["cluster_id"],
                            "fold_id": int(fk),
                            "train_window": f7["train_window"],
                            "n_decisions": c["n_trades"],
                            "n_trades": c["n_trades"],
                            "gross_pnl_usd": None,
                            "cost_total_usd": None,
                            "net_pnl_usd": c["net_pnl_usd"],
                            "expectancy_per_trade_usd":
                                c["expectancy_per_trade_usd"],
                            "tier": 1.0,
                            "pass_tag": ctrl,
                            "result": "CONTROL_COMPUTED",
                            "control_meta": {
                                "seed": c["seed"],
                                "n_unplaced": c["n_unplaced"],
                                "arm_net_pnl_usd": f7["net_pnl_usd"],
                                "arm_expectancy":
                                    f7["expectancy_per_trade_usd"],
                                "control_ge_arm": (
                                    c["expectancy_per_trade_usd"]
                                    is not None
                                    and f7["expectancy_per_trade_usd"]
                                    is not None
                                    and c["expectancy_per_trade_usd"]
                                    >= f7["expectancy_per_trade_usd"])},
                        })
        with open(os.path.join(args.out, "DIAG_CONTROLS.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"schema": "pc12a_diag_controls@1", "label": LABEL,
                       "spec": "CLASS_SPEC_VOLPROF_M1 r2 section 7a/7c",
                       "single_replicate_disclosure": (
                           "one seeded replicate per (arm, fold, ctrl); "
                           "multi-seed ensembles are Stage-B/C re-runs if "
                           "kill adjudication needs them"),
                       "controls": control_out}, fh, sort_keys=True,
                      indent=1)
            fh.write("\n")
        # complementarity
        comp = complementarity(main_legs, folds)
        with open(os.path.join(args.out, "COMPLEMENTARITY_TRAIN.json"),
                  "w", encoding="utf-8") as fh:
            json.dump({"schema": "pc12a_complementarity_train@1",
                       "label": LABEL,
                       "series": "weekly equity deltas (Friday marks)",
                       "max_train_end": folds[-1].train_end.isoformat(),
                       "folds": comp}, fh, sort_keys=True)
            fh.write("\n")
        total = append_rows(ledger_path, ledger_rows,
                            args.ledger_stop_at)
        manifest.update({
            "ledger_rows_appended": len(ledger_rows),
            "ledger_total": total,
            "n_main_legs": len(main_legs),
            "finished_utc": _fmt(dt.datetime.now(UTC)),
            "elapsed_seconds": round(time.time() - t0, 3)})
        with open(os.path.join(args.out, "DIAG_MANIFEST.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(manifest, fh, sort_keys=True, indent=1)
            fh.write("\n")
        print(json.dumps({"done": "assemble",
                          "rows": len(ledger_rows), "total": total,
                          "elapsed": round(time.time() - t0, 1)}))
        return 0

    # ------------------------------------------------------------------
    # SINGLE mode (original whole-wave in-process path)
    # ------------------------------------------------------------------
    lock = None
    if args.lock:
        lock = _take_lock(["research.pc12a.run_diag",
                           "--legs", args.legs, "--out", args.out])

    manifest = {"schema": "pc12a_diag_manifest@1", "label": LABEL,
                "started_utc": _fmt(dt.datetime.now(UTC)),
                "tiers": {}, "controls": {}, "runtimes": {}}
    ledger_rows = []
    per_leg_main: Dict[str, Dict] = {}
    runtimes: Dict[str, float] = {}
    try:
        for symbol in sorted(by_symbol):
            ts = time.time()
            store = _make_store(symbol)
            digest = _symbol_digest(store, symbol, folds)
            results = []
            for cfg in by_symbol[symbol]:
                res = run_leg_diag(symbol, cfg, store, folds, 1.0,
                                   digest=digest)
                per_leg_main[res["leg_id"]] = res
                results.append(res)
                for f in res["folds"]:
                    assert abs(f["residual_usd"]) < RESIDUAL_TOL
                    ledger_rows.append(_row(res, f, 1.0, "MAIN"))
            runtimes[f"MAIN/{symbol}"] = round(time.time() - ts, 3)
            _write_pass(args, "MAIN", symbol, results, digest, folds,
                        time.time() - ts)

        if args.x2:
            for symbol in sorted(by_symbol):
                ts = time.time()
                store = _make_store(symbol)
                digest = _symbol_digest(store, symbol, [folds[-1]])
                results = []
                for cfg in by_symbol[symbol]:
                    res = run_leg_diag(symbol, cfg, store, [folds[-1]],
                                       2.0, digest=digest)
                    results.append(res)
                    f = res["folds"][0]
                    assert abs(f["residual_usd"]) < RESIDUAL_TOL
                    exp = f["expectancy_per_trade_usd"]
                    x2_result = ("DIAG_TRAIN_COMPUTED" if exp is not None
                                 else "NO_ENTRIES_TRAIN")
                    ledger_rows.append(_row(res, f, 2.0, "X2",
                                            result=x2_result,
                                            extra={"stress_tier": 2.0}))
                    if exp is not None and exp <= 0.0:
                        ledger_rows.append(_row(
                            res, f, 2.0, "X2", result="COST_DOMINATED",
                            extra={"stress_tier": 2.0,
                                   "detail": (
                                       "typed kill: TRAIN expectancy at "
                                       "x2.0 measured spread + DECLARED "
                                       "bands <= 0 per campaign §4")}))
                runtimes[f"X2/{symbol}"] = round(time.time() - ts, 3)
                _write_pass(args, "X2", symbol, results, digest,
                            [folds[-1]], time.time() - ts)

        if args.controls:
            for symbol in sorted(by_symbol):
                arms = [c for c in by_symbol[symbol]
                        if c["sleeve_id"] == _legs.VOLPROF_SLEEVE]
                if not arms:
                    continue
                store = _make_store(symbol)
                kernel = _ck.CostKernel(symbol, tier=1.0)
                for cfg in arms:
                    lid = cfg.get("class_candidate_id") or cfg["corpus_gid"]
                    arm = per_leg_main[lid]
                    for ctrl in ("CTRL-A", "CTRL-C"):
                        ctr = run_control(symbol, lid, arm["episodes"],
                                          store, kernel, folds, ctrl)
                        for fk, c in sorted(ctr.items()):
                            f7 = arm["folds"][int(fk)]
                            ledger_rows.append({
                                "stage": "A-DIAG",
                                "sleeve_id": arm["sleeve_id"],
                                "corpus_gid": f"{lid}#{ctrl}",
                                "arm_config_digest":
                                    arm["arm_config_digest"],
                                "outcome_exposed_label":
                                    "CONTROL_PLACEBO_SEEDED",
                                "cluster_id": arm["cluster_id"],
                                "fold_id": int(fk),
                                "train_window": f7["train_window"],
                                "n_decisions": c["n_trades"],
                                "n_trades": c["n_trades"],
                                "gross_pnl_usd": None,
                                "cost_total_usd": None,
                                "net_pnl_usd": c["net_pnl_usd"],
                                "expectancy_per_trade_usd":
                                    c["expectancy_per_trade_usd"],
                                "tier": 1.0,
                                "pass_tag": ctrl,
                                "result": "CONTROL_COMPUTED",
                            })

        comp = complementarity(per_leg_main, folds)
        with open(os.path.join(args.out, "COMPLEMENTARITY_TRAIN.json"),
                  "w", encoding="utf-8") as fh:
            json.dump({"schema": "pc12a_complementarity_train@1",
                       "label": LABEL,
                       "series": "weekly equity deltas (Friday marks)",
                       "max_train_end": folds[-1].train_end.isoformat(),
                       "folds": comp}, fh, sort_keys=True)
            fh.write("\n")

        if ledger_rows:
            total = append_rows(ledger_path, ledger_rows,
                                args.ledger_stop_at)
            manifest["ledger_rows_appended"] = len(ledger_rows)
            manifest["ledger_total"] = total
    finally:
        manifest["runtimes"] = runtimes
        manifest["finished_utc"] = _fmt(dt.datetime.now(UTC))
        manifest["elapsed_seconds"] = round(time.time() - t0, 3)
        with open(os.path.join(args.out, "DIAG_MANIFEST.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(manifest, fh, sort_keys=True, indent=1)
            fh.write("\n")
        if lock is not None:
            lock.release(status="FINISHED",
                         note=f"rows={len(ledger_rows)}")

    print(json.dumps({"done": True,
                      "elapsed": round(time.time() - t0, 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
