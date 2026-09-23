"""Deterministic event-loop backtest engine on execution bars.

V2 carry-over: engine math is byte-identical to V1 (fold-partition law +
reconciliation identity built in); only this note differs.

Pinned laws (each golden-tested):
- next-bar-open fills: a signal on completed exec bar i fills at open of i+1;
  there is NO same-bar fill and NO same-open flip (a bar whose open processed
  an exit cannot also process an entry).
- one position at a time; notional fraction 1.0 of current equity;
  units = equity/price rounded to 8 dp (fractional units allowed).
- costs debited EXACTLY ONCE per fill (entries, exits, stops, force-flat):
  fees = fee_bps * 1e-4 * notional, slippage = slip_bps * 1e-4 * notional,
  booked as separate ledger components (SPY books its single all-in band as
  fees with zero slippage).
- intrabar stops evaluated only on bars AFTER the entry bar; stop fills at
  the stop price (slippage debited separately as for any fill).
- strategy exits and regime-off exits fill at the NEXT exec bar open; an open
  position reconciles to the new regime's target at the next open (and is
  closed there when the target maps away / changed strategy).
- BTC funding: rate * signed_notional at every 8h UTC boundary strictly after
  entry and up to the exit fill timestamp / bar close while held; longs pay,
  shorts receive (signed cost, can be a credit).
- fold-terminal force-flat: position closed at the LAST exec bar close of the
  fold (costs debited); equity itself is continuous across folds.
- fold law (A7-1 F3 amendment): the exec-bar fold partition is CONTIGUOUS —
  every exec bar from the first fold's first bar onward belongs to exactly
  one fold (folds_from_regime_ts); entry fills/signals are refused on
  unassigned (pre-warmup) bars; no position ever spans a fold boundary; and
  the runner asserts sum(fold_net_pnl) == totals.net_pnl within 1e-9 after
  every run.
- stale-data rejection: a governing decision older than 2 regime periods at
  an exec bar open maps to FLAT there.
- BUY_HOLD (reference metric): enters TREND_LONG at the first exec bar open
  of each fold; while held, the position still takes TREND_LONG
  strategy_exit/stop exits mid-fold and re-arms only at the NEXT fold start
  (A5-F1 arbitration 2026-09-23: this docstring previously claimed "exits
  only via fold force-flat" — the implemented behavior stands unchanged to
  preserve the fork's V2 byte-equivalence; buy-hold is a REFERENCE metric,
  never a scored arm).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .data import Bars
from .strategies import (
    FLAT,
    MR_LONG,
    TREND_LONG,
    TREND_SHORT,
    exec_indicators,
    mr_long_entry,
    mr_long_exit,
    stop_hit,
    stop_price,
    trend_long_entry,
    trend_long_exit,
    trend_short_entry,
    trend_short_exit,
)

HOUR_NS = 3_600_000_000_000
EIGHT_H_NS = 8 * HOUR_NS
BUY_HOLD = "BUY_HOLD"
STALE_REGIME_PERIODS = 2


@dataclass
class CostModel:
    fee_bps: float
    slip_bps: float
    funding_rate: float = 0.0  # per 8h on signed notional; 0 disables
    label: str = ""


@dataclass
class Position:
    strategy: str
    direction: int
    qty: float
    entry_px: float
    entry_ts: int
    entry_bar: int
    stop: float
    fees: float = 0.0
    slip: float = 0.0
    funding: float = 0.0
    funding_up_to: int = 0
    entry_costs: float = 0.0  # fees+slip debited at the entry fill


@dataclass
class Trade:
    strategy: str
    direction: int
    qty: float
    entry_bar: int
    entry_ts: int
    entry_px: float
    exit_bar: int
    exit_ts: int
    exit_px: float
    exit_reason: str
    gross_pnl: float
    fees: float
    slip: float
    funding: float
    net_pnl: float
    fold_id: int


@dataclass
class EngineResult:
    equity: np.ndarray
    trades: list[Trade]
    invested: np.ndarray  # 1.0 when a position is open at bar close
    fold_id: np.ndarray  # fold index per exec bar (-1 outside folds)
    fold_net_pnl: list[float]
    fold_return_series: list[list[float]]
    totals: dict = field(default_factory=dict)


def _entry_signal(strategy: str, i: int, bars: Bars, x: ExecIndicators) -> bool:
    if strategy == TREND_LONG:
        return trend_long_entry(i, bars, x)
    if strategy == TREND_SHORT:
        return trend_short_entry(i, bars, x)
    if strategy == MR_LONG:
        return mr_long_entry(i, bars, x)
    return False


def _exit_signal(strategy: str, i: int, bars: Bars, x: ExecIndicators, held: int) -> bool:
    if strategy == TREND_LONG:
        return trend_long_exit(i, bars, x)
    if strategy == TREND_SHORT:
        return trend_short_exit(i, bars, x)
    if strategy == MR_LONG:
        return mr_long_exit(i, bars, x, held)
    return False


class Engine:
    def __init__(
        self,
        bars: Bars,
        targets: list[str | None],
        folds: list[tuple[int, int, int]],  # (fold_id, start_i, end_i) inclusive
        costs: CostModel,
        initial_equity: float = 100_000.0,
        ind: ExecIndicators | None = None,
    ) -> None:
        self.bars = bars
        self.x = ind if ind is not None else exec_indicators(bars)
        self.targets = targets
        assert len(targets) == len(bars.ts_close)
        self.folds = sorted(folds)
        self.costs = costs
        self.initial_equity = float(initial_equity)
        self.fold_id = np.full(len(bars.ts_close), -1, dtype=np.int64)
        self._fold_starts = set()
        self._fold_ends = {}
        for fid, s, e in self.folds:
            self.fold_id[s : e + 1] = fid
            self._fold_starts.add(s)
            self._fold_ends[e] = fid

    # -- fills ------------------------------------------------------------

    def _apply_fill_costs(self, pos: Position, px: float, qty: float) -> None:
        notional = px * qty
        pos.fees += self.costs.fee_bps * 1e-4 * notional
        pos.slip += self.costs.slip_bps * 1e-4 * notional

    def _charge_funding_until(self, pos: Position, until_ts: int, ref_px: float) -> None:
        if self.costs.funding_rate == 0.0:
            pos.funding_up_to = until_ts
            return
        t = ((pos.funding_up_to // EIGHT_H_NS) + 1) * EIGHT_H_NS
        while t <= until_ts:
            pos.funding += self.costs.funding_rate * pos.direction * pos.qty * ref_px
            pos.funding_up_to = t
            t += EIGHT_H_NS

    # -- main loop ---------------------------------------------------------

    def run(self) -> EngineResult:
        bars = self.bars
        N = len(bars.ts_close)
        cash = self.initial_equity
        equity = np.full(N, np.nan)
        invested = np.zeros(N)
        trades: list[Trade] = []

        pos: Position | None = None
        pending_entry: str | None = None
        pending_exit: str | None = None

        for i in range(N):
            o = float(bars.open[i])
            c = float(bars.close[i])
            ts_o = int(bars.ts_open[i])
            ts_c = int(bars.ts_close[i])

            # 1) fills queued for THIS open (no same-open flip) -----------
            if pos is not None and pending_exit is not None:
                cash = self._close_position(pos, i, ts_o, o, pending_exit, cash, trades)
                pos = None
                pending_exit = None
            elif pos is None and pending_entry is not None:
                tgt = self.targets[i]
                # fold law (A7-1 F3): a position may only OPEN on an exec bar
                # that belongs to a fold — never on unassigned bars
                if (tgt == pending_entry or tgt == BUY_HOLD) and self.fold_id[i] >= 0:
                    pos = self._open_position(pending_entry, i, ts_o, o, cash)
                    cash -= pos.direction * pos.qty * o + pos.fees + pos.slip
                pending_entry = None

            # 2) regime reconciliation at this open -----------------------
            if pos is not None:
                tgt = self.targets[i]
                if tgt == BUY_HOLD:
                    pass  # arm A holds through everything except fold-flat
                elif tgt is None or tgt == FLAT or tgt != pos.strategy:
                    cash = self._close_position(pos, i, ts_o, o, "regime_off", cash, trades)
                    pos = None

            # 3) intrabar stop (bars AFTER the entry bar only; disabled until
            #    ATR initializes, in which case stop is NaN) ----------------
            if pos is not None and i > pos.entry_bar and np.isfinite(pos.stop):
                if stop_hit(pos.strategy, float(bars.high[i]), float(bars.low[i]), pos.stop):
                    cash = self._close_position(
                        pos, i, ts_o, o, "stop", cash, trades, px_override=pos.stop
                    )
                    pos = None

            # 4) funding while held ---------------------------------------
            if pos is not None:
                self._charge_funding_until(pos, ts_c, c)

            # 5) fold-terminal force-flat at this bar's close --------------
            if pos is not None and i in self._fold_ends:
                cash = self._close_position(pos, i, ts_c, c, "fold_flat", cash, trades)
                pos = None
            # fold law invariant (A7-1 F3): after the fold-flat step a
            # position may exist ONLY on a bar that belongs to a fold — a
            # position can never cross a fold boundary (hard fail, no warning)
            assert pos is None or self.fold_id[i] >= 0, (
                f"fold law violated: position open on unassigned exec bar {i}"
            )

            # 6) mark equity -----------------------------------------------
            equity[i] = cash + (pos.direction * pos.qty * c if pos is not None else 0.0)
            invested[i] = 1.0 if pos is not None else 0.0

            # 7) signals on THIS close for the NEXT open -------------------
            pending_exit = None
            if pos is None:
                pending_entry = None
                tgt = self.targets[i]
                if tgt == BUY_HOLD:
                    if i in self._fold_starts:
                        pending_entry = TREND_LONG
                elif (
                    tgt is not None
                    and tgt != FLAT
                    and self.fold_id[i] >= 0  # fold law: no entry signals on unassigned bars
                    and _entry_signal(tgt, i, bars, self.x)
                ):
                    pending_entry = tgt
            else:
                held = i - pos.entry_bar + 1
                if _exit_signal(pos.strategy, i, bars, self.x, held):
                    pending_exit = "strategy_exit"

        result = self._assemble(equity, invested, trades)
        _assert_engine_invariants(result, self.folds)
        return result

    # -- helpers -----------------------------------------------------------

    def _open_position(self, strategy: str, i: int, ts: int, px: float, cash: float) -> Position:
        qty = round(cash / px, 8)
        a = float(self.x.atr14[i - 1]) if i > 0 else float("nan")
        if not np.isfinite(a):
            a = float(self.x.atr14[i])  # may still be NaN -> stop disabled
        pos = Position(
            strategy=strategy,
            direction=-1 if strategy == TREND_SHORT else 1,
            qty=qty,
            entry_px=px,
            entry_ts=ts,
            entry_bar=i,
            stop=stop_price(strategy, px, a),
            funding_up_to=ts,
        )
        self._apply_fill_costs(pos, px, qty)  # entry fill costs, exactly once
        pos.entry_costs = pos.fees + pos.slip
        return pos

    def _close_position(
        self,
        pos: Position,
        i: int,
        ts: int,
        px: float,
        reason: str,
        cash: float,
        trades: list[Trade],
        px_override: float | None = None,
    ) -> float:
        fill_px = float(px_override) if px_override is not None else float(px)
        self._apply_fill_costs(pos, fill_px, pos.qty)  # exit fill costs, once
        self._charge_funding_until(pos, ts, fill_px)
        gross = (fill_px - pos.entry_px) * pos.direction * pos.qty
        # entry debited notional + entry costs; exit credits full notional
        # minus the EXIT-SIDE costs only (never double-debits the entry side)
        exit_costs = pos.fees + pos.slip - pos.entry_costs
        cash += pos.direction * pos.qty * fill_px - exit_costs - pos.funding
        trades.append(
            Trade(
                strategy=pos.strategy,
                direction=pos.direction,
                qty=pos.qty,
                entry_bar=pos.entry_bar,
                entry_ts=pos.entry_ts,
                entry_px=pos.entry_px,
                exit_bar=i,
                exit_ts=ts,
                exit_px=fill_px,
                exit_reason=reason,
                gross_pnl=gross,
                fees=pos.fees,
                slip=pos.slip,
                funding=pos.funding,
                net_pnl=gross - pos.fees - pos.slip - pos.funding,
                fold_id=int(self.fold_id[i]),
            )
        )
        return cash

    def _assemble(self, equity, invested, trades) -> EngineResult:
        fold_net: dict[int, float] = {}
        fold_series: dict[int, list[float]] = {}
        eq = equity
        for fid, s, e in self.folds:
            prev = float(eq[s - 1]) if s > 0 else self.initial_equity
            rets = []
            for k in range(s, e + 1):
                base = float(eq[k - 1]) if k > s else prev
                rets.append(float(eq[k]) / base - 1.0)
            fold_series[fid] = rets
            fold_net[fid] = float(eq[e]) - prev
        totals = {
            "gross_pnl": float(sum(t.gross_pnl for t in trades)),
            "costs_fee": float(sum(t.fees for t in trades)),
            "costs_slip": float(sum(t.slip for t in trades)),
            "costs_funding": float(sum(t.funding for t in trades)),
            "net_pnl": float(sum(t.net_pnl for t in trades)),
            "trades": len(trades),
        }
        return EngineResult(
            equity=equity,
            trades=trades,
            invested=invested,
            fold_id=self.fold_id,
            fold_net_pnl=[fold_net[k] for k in sorted(fold_net)],
            fold_return_series=[fold_series[k] for k in sorted(fold_series)],
            totals=totals,
        )


# targets + folds construction ----------------------------------------------


def targets_from_regime(
    exec_bars: Bars,
    regime_ts: list[int],
    regime_labels: list[str],
    regime_period_ns: int,
    mapping: dict,
) -> list[str | None]:
    """Per-exec-bar target strategy from the persisted regime timeline.

    Governing decision for exec bar i = latest regime close STRICTLY BEFORE
    the exec bar open (decisions act on bars strictly after their close).
    Stale decisions (> 2 regime periods old) map to FLAT. Bars before the
    first decision get None (no trading).
    """
    targets: list[str | None] = [None] * len(exec_bars.ts_close)
    j = -1
    for i, ts_o in enumerate(exec_bars.ts_open.tolist()):
        while j + 1 < len(regime_ts) and regime_ts[j + 1] < ts_o:
            j += 1
        if j < 0:
            continue
        if ts_o - regime_ts[j] > STALE_REGIME_PERIODS * regime_period_ns:
            targets[i] = FLAT
            continue
        targets[i] = mapping.get(regime_labels[j], FLAT)
    return targets


def constant_targets(n: int, strategy: str | None) -> list[str | None]:
    return [strategy] * n


def folds_from_regime_ts(
    exec_bars: Bars,
    fold_spans: list[tuple[int, int]],  # (start_ts, end_ts) inclusive, regime clock
) -> list[tuple[int, int, int]]:
    """Exec-bar fold ranges as a CONTIGUOUS partition (amended A7-1 F3).

    Fold k starts at its first exec bar strictly after the frozen regime-span
    start (``start_k < ts_open <= end_k``, the DECISION boundary — frozen and
    untouched), and now OWNS exec bars through the bar immediately preceding
    fold k+1's first exec bar; the last fold extends to the final exec bar.
    The frozen spans are non-adjacent (BTC 4 exec bars / SPY 1 session between
    spans), which previously left those gap bars in NO fold so positions could
    span boundaries and fold PnL did not reconcile with totals. With this
    partition EVERY exec bar from the first fold's first bar onward belongs to
    exactly one fold; bars BEFORE it stay unassigned (-1, pre-warmup tag).
    Force-flat at each fold's LAST exec bar is unchanged.
    """
    out = []
    ts = exec_bars.ts_open.tolist()
    starts: list[int | None] = []
    for a, _b in fold_spans:
        s = next((k for k, t in enumerate(ts) if a < t), None)
        starts.append(s)
    for fid, (_a, _b) in enumerate(fold_spans):
        s = starts[fid]
        if s is None:
            continue
        e = len(ts) - 1  # last fold extends to the final exec bar
        for nfid in range(fid + 1, len(fold_spans)):
            if starts[nfid] is not None:
                e = starts[nfid] - 1  # through the bar before the next fold's first bar
                break
        out.append((fid, s, e))
    return out


def fold_partition_invariants(
    folds: list[tuple[int, int, int]],
    n_exec_bars: int,
    first_required_bar: int | None = None,
) -> None:
    """Hard invariants of the exec-bar fold partition (A7-1 F3).

    Raises AssertionError when:
    - fold ranges overlap or are unordered;
    - assignment is not contiguous from the first fold's start through the
      last fold's end (every such bar in exactly one fold);
    - ``first_required_bar`` (e.g. the first post-warmup exec bar) is not
      covered — i.e. any exec bar after warmup would lack a fold index.
    Bars before the first fold's start are the explicit pre-warmup tag (-1).
    """
    fs = sorted(folds)
    for (f1, s1, e1), (f2, s2, e2) in zip(fs, fs[1:]):
        assert s2 == e1 + 1, f"fold partition gap/overlap: fold {f1} ends {e1}, fold {f2} starts {s2}"
        assert f2 == f1 + 1, f"fold ids not consecutive: {f1} -> {f2}"
    for _fid, s, e in fs:
        assert 0 <= s <= e < n_exec_bars, f"fold range [{s},{e}] outside exec grid"
    if first_required_bar is not None and fs:
        assert fs[0][1] <= first_required_bar, (
            f"exec bar {first_required_bar} (post-warmup) before first fold start {fs[0][1]}"
        )
        assert fs[-1][2] >= first_required_bar


def _assert_engine_invariants(res: EngineResult, folds: list[tuple[int, int, int]]) -> None:
    """Runner invariants (A7-1 F3), hard-fail (never warn):

    1. no position open crosses a fold boundary (every invested bar carries a
       fold index; every trade lives inside a single fold's exec range);
    2. sum(fold_net_pnl) == totals.net_pnl within 1e-9.
    """
    invested = res.invested
    fold_id = res.fold_id
    for i in range(len(invested)):
        if invested[i] == 1.0:
            assert fold_id[i] >= 0, f"position open on unassigned exec bar {i} (fold_id=-1)"
    ranges = {fid: (s, e) for fid, s, e in folds}
    for t in res.trades:
        fid = t.fold_id
        assert fid in ranges, f"trade exit assigned to unknown fold {fid}"
        s, e = ranges[fid]
        assert s <= t.entry_bar and t.exit_bar <= e, (
            f"trade {t.entry_bar}..{t.exit_bar} spans outside fold {fid} range [{s},{e}]"
        )
    fold_sum = float(sum(res.fold_net_pnl))
    total = float(res.totals["net_pnl"])
    assert abs(fold_sum - total) <= 1e-9, (
        f"fold attribution does not reconcile: sum(fold_net_pnl)={fold_sum!r} != totals.net_pnl={total!r}"
    )
