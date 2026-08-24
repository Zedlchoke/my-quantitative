"""Shared-capital cross-sectional portfolio backtest engine (Sprint V4, owner A2).

Contract: PLAN.md section 20. One shared cash/margin account is iterated over
the merged 15m event timeline of ALL symbols across ALL folds and gaps; the
cross-section is rebalanced as a single portfolio (never per-symbol PnL sum).

Execution semantics
-------------------
* Signal cutoffs are UTC midnights ``C``. At the FIRST bar event whose
  ``ts_event >= C`` the engine calls ``weight_fn(C)`` — a callable compatible
  with ``research.xsect_rank.compute_target_weights``'s return shape
  (``status``/``longs``/``shorts``, weights pre-rounding).
  NEXT_BAR_EVENT_BASELINE: fills happen at that SAME bar event's close
  +/- ``slippage_ticks * tick_size`` adverse.
* ``SKIP_INCOMPLETE`` records a skipped-rebalance row and keeps positions.
* Target quantity = floor_to_step(w * equity / close). Reductions execute
  before increases; a whole-rebalance margin pre-check requires the sum of buy
  outlays <= free cash AFTER reductions, otherwise every increase order is
  rejected with reason ``margin_breach`` while reductions still execute.
* Funding: at each 8h settlement (00:00/08:00/16:00 UTC) every HELD leg is
  charged ``cashflow = -rate * signed_mark_notional``, joined by
  ``(symbol, fundingTime_ms * 1e6 == settlement_ns)`` against
  ``reports.funding._load_bundle``-layout bundles. A held symbol missing the
  row for a settlement fails closed with ValueError.
* Closed-leg rows are emitted when a position reduces to exactly zero or flips
  (flip = reduction-to-zero order, then a reverse opening order).

Invariants checked on EVERY rebalance row: target weights sum to ~0 (@1e-9,
pre-rounding), gross <= 1 + 1e-9, |w| <= 0.25 + 1e-9 per symbol,
equity == cash + sum(signed mark notional) @1e-6, margin (free cash) >= 0;
a negative margin aborts the current fold (trading suppressed until the next
fold starts) with reason code ``margin_breach``.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from contracts.protocol import PORTFOLIO_CONSTRAINTS, position_pnl_stats

DAY_NS = 86_400_000_000_000
FUNDING_PERIOD_NS = 8 * 3_600 * 1_000_000_000
SUM_TOL = 1e-9
GROSS_CAP = float(PORTFOLIO_CONSTRAINTS["gross_target"])
WEIGHT_CAP = float(PORTFOLIO_CONSTRAINTS["max_abs_weight_per_symbol"])
CASH_IDENTITY_TOL = 1e-6
MARGIN_TOL = 1e-9
POS_EPS = 1e-12


@dataclass(frozen=True)
class PortfolioRunResult:
    """Shared-capital run output consumed by A3 metrics/gates."""

    portfolio_ledger: list[dict]
    orders: list[dict]
    closed_legs: list[dict]
    equity_curve: list[tuple[int, float]]
    skipped_rebalances: list[dict]
    invariant_checks: list[dict]
    funding_cashflows: list[dict]
    summary: dict
    meta: dict

    def to_dict(self) -> dict:
        return {
            "portfolio_ledger": self.portfolio_ledger,
            "orders": self.orders,
            "closed_legs": self.closed_legs,
            "equity_curve": [list(p) for p in self.equity_curve],
            "skipped_rebalances": self.skipped_rebalances,
            "invariant_checks": self.invariant_checks,
            "funding_cashflows": self.funding_cashflows,
            "summary": self.summary,
            "meta": self.meta,
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
def _floor_step(x: float, step: float) -> float:
    """Floor |x| to the step grid, sign preserved; fp dust cleaned."""
    if step <= 0:
        raise ValueError(f"step_size must be positive, got {step!r}")
    sign = -1.0 if x < 0 else 1.0
    steps = math.floor(abs(x) / step + 1e-9)
    return sign * round(steps * step, 12)


def _tick_round(price: float, tick: float) -> float:
    if tick <= 0:
        raise ValueError(f"tick_size must be positive, got {tick!r}")
    return round(round(price / tick) * tick, 10)


def _targets_from_weight_result(res: dict) -> dict[str, float]:
    if not isinstance(res, dict) or res.get("status") != "OK":
        status = res.get("status") if isinstance(res, dict) else type(res).__name__
        raise ValueError(f"weight_fn returned non-OK result in rebalance path: {status!r}")
    targets: dict[str, float] = {}
    for leg in ("longs", "shorts"):
        for item in res.get(leg) or []:
            sym, w = str(item[0]), float(item[1])
            if sym in targets:
                raise ValueError(f"duplicate target for symbol {sym}")
            targets[sym] = w
    return targets


def _load_funding_settlements(
    bundles_dir: str | Path | None, symbols: list[str]
) -> dict[str, dict[int, float]]:
    """{symbol: {settlement_ns: rate}} from reports.funding bundle layout.

    Missing bundle FILES yield empty maps (fail-closed enforcement happens at
    settlement application time only if a held leg actually needs the row).
    """
    if bundles_dir is None:
        return {}
    from research.funding_pit import load_funding_bundle

    root = Path(bundles_dir)
    out: dict[str, dict[int, float]] = {}
    for sym in symbols:
        path = root / sym / "funding.json"
        if not path.exists():
            out[sym] = {}
            continue
        payload = load_funding_bundle(root, sym)
        out[sym] = {
            int(row["fundingTime"]) * 1_000_000: float(str(row["fundingRate"]))
            for row in payload["rows"]
        }
    return out


class _Grid:
    """Ascending epoch-aligned grid of due timestamps crossed by bar events."""

    def __init__(self, period_ns: int) -> None:
        self.period = int(period_ns)
        self.next: int | None = None

    def due(self, ts: int) -> list[int]:
        if self.next is None:
            self.next = ((ts + self.period - 1) // self.period) * self.period
        out: list[int] = []
        while self.next <= ts:
            out.append(self.next)
            self.next += self.period
        return out


def _rejected_order_row(ts, fid, sym, qty_signed, ref, kind, reason) -> dict:
    return {
        "ts": ts,
        "fold_id": fid,
        "symbol": sym,
        "side": "BUY" if qty_signed > 0 else "SELL",
        "qty": abs(qty_signed),
        "ref_price": ref,
        "fill_price": None,
        "notional": abs(qty_signed) * ref,
        "fee": 0.0,
        "slippage_cost": 0.0,
        "kind": kind,
        "rejected_reason": reason,
    }


# --------------------------------------------------------------------------- #
# Rebalance core (module-level for white-box unit testing)
# --------------------------------------------------------------------------- #
def _apply_fill(
    sym: str,
    qty_signed: float,
    ref: float,
    ts: int,
    fid: int | None,
    kind: str,
    state: dict,
    params: dict,
    orders: list[dict],
    closed_legs: list[dict],
) -> float:
    """Execute one fill at ref +/- adverse slip; mutate shared state.

    Returns the turnover contribution (qty_abs * ref).
    """
    tick = params["tick_size"][sym]
    slip_amt = abs(params["slippage_ticks"]) * tick
    fee_taker = params["fee_taker"]
    side = "BUY" if qty_signed > 0 else "SELL"
    fill = _tick_round(ref + (slip_amt if qty_signed > 0 else -slip_amt), tick)
    qty_abs = abs(qty_signed)
    fee = fee_taker * qty_abs * fill
    slippage_cost = qty_abs * slip_amt
    state["cash"] += -(qty_signed * fill) - fee
    # dEquity = dCash + d(pos*ref) = -fee - slippage_cost (value-neutral at ref)
    state["equity"] += -(qty_signed * fill) - fee + qty_signed * ref
    orders.append(
        {
            "ts": ts,
            "fold_id": fid,
            "symbol": sym,
            "side": side,
            "qty": qty_abs,
            "ref_price": ref,
            "fill_price": fill,
            "notional": qty_abs * fill,
            "fee": fee,
            "slippage_cost": slippage_cost,
            "kind": kind,
            "rejected_reason": None,
        }
    )
    cur = state["pos"][sym]
    if cur == 0.0 or (cur > 0) == (qty_signed > 0):
        new_abs = abs(cur) + qty_abs
        state["avg_entry"][sym] = (
            state["avg_entry"][sym] * abs(cur) + ref * qty_abs
        ) / new_abs
        state["pos"][sym] = cur + qty_signed
        state["leg_cost"][sym] += fee + slippage_cost
        return qty_abs * ref
    dq = min(qty_abs, abs(cur))
    side_sign = 1.0 if cur > 0 else -1.0
    entry_px = state["avg_entry"][sym]
    gross_pnl = dq * side_sign * (ref - entry_px)
    alloc = state["leg_cost"][sym] * (dq / abs(cur))
    realized = gross_pnl - alloc
    state["leg_cost"][sym] -= alloc
    state["pos"][sym] = cur + qty_signed
    residual_cost = 0.0
    if abs(state["pos"][sym]) <= POS_EPS:
        state["pos"][sym] = 0.0
        state["avg_entry"][sym] = 0.0
        residual_cost = state["leg_cost"][sym]
        state["leg_cost"][sym] = 0.0
    closed_legs.append(
        {
            "ts": ts,
            "fold_id": fid,
            "symbol": sym,
            "side": "LONG" if side_sign > 0 else "SHORT",
            "qty": dq,
            "entry_price": entry_px,
            "exit_price": ref,
            "gross_pnl": gross_pnl,
            "costs_allocated": alloc + residual_cost,
            "realized_pnl": realized - residual_cost,
        }
    )
    return qty_abs * ref


def _classify_orders(
    pos: dict[str, float], desired: dict[str, float]
) -> tuple[list[tuple[str, float, str]], list[tuple[str, float, str]]]:
    """Split per-symbol deltas into (reductions, increases), both pre-sorted."""
    reductions: list[tuple[str, float, str]] = []
    increases: list[tuple[str, float, str]] = []
    for sym in sorted(desired):
        cur, tgt = pos[sym], desired[sym]
        delta = tgt - cur
        if abs(delta) < POS_EPS:
            continue
        if cur == 0.0:
            increases.append((sym, delta, "open"))
        elif (cur > 0) == (tgt >= 0):
            if abs(tgt) >= abs(cur):
                increases.append((sym, delta, "increase"))
            else:
                kind = "reduce_to_zero" if abs(tgt) < POS_EPS else "partial_reduce"
                reductions.append((sym, delta, kind))
        else:
            reductions.append((sym, -math.copysign(abs(cur), cur), "reduce_to_zero"))
            increases.append((sym, math.copysign(abs(tgt), tgt), "flip_open"))
    return reductions, increases


def _execute_rebalance_core(
    *,
    cutoff: int,
    ts: int,
    fold_id: int | None,
    targets: dict[str, float],
    refs: dict[str, float],
    state: dict,
    params: dict,
    orders: list[dict],
    closed_legs: list[dict],
    invariant_checks: list[dict],
) -> bool:
    """Execute one whole cross-section rebalance. Returns True on margin breach.

    State keys mutated: cash, equity, pos, avg_entry, leg_cost.
    """
    traded = sorted(targets)

    # ---- invariant inputs (pre-rounding weights from weight_fn) ----
    w_sum = sum(targets.values())
    gross_w = sum(abs(w) for w in targets.values())
    caps_ok = all(abs(w) <= WEIGHT_CAP + SUM_TOL for w in targets.values())
    sum_ok = abs(w_sum) <= SUM_TOL
    gross_ok = gross_w <= GROSS_CAP + SUM_TOL

    def emit_invariant(margin_ok: bool, identity_ok: bool) -> None:
        row = {
            "signal_ts": int(cutoff),
            "execution_bar_ts": ts,
            "fold_id": fold_id,
            "sum_targets_zero": sum_ok,
            "gross_within_cap": gross_ok,
            "weight_caps_ok": caps_ok,
            "cash_identity_ok": identity_ok,
            "margin_ok": margin_ok,
            "all_pass": bool(sum_ok and gross_ok and caps_ok and identity_ok and margin_ok),
        }
        invariant_checks.append(row)

    if not (sum_ok and gross_ok and caps_ok):
        emit_invariant(margin_ok=True, identity_ok=True)
        raise ValueError(
            f"target-weight invariant breach at cutoff {cutoff}: "
            f"sum={w_sum!r} gross={gross_w!r} caps_ok={caps_ok}"
        )

    desired: dict[str, float] = {}
    for sym in traded:
        raw_qty = targets[sym] * state["equity"] / refs[sym]
        desired[sym] = _floor_step(raw_qty, params["step_size"][sym])

    reductions, increases = _classify_orders(state["pos"], desired)

    def sub_min_notional(qty_signed: float, sym: str) -> bool:
        return abs(qty_signed) * refs[sym] < params["min_notional"] - 1e-12

    executable_reds: list[tuple[str, float, str]] = []
    for sym, q, kind in reductions:
        if sub_min_notional(q, sym):
            orders.append(
                _rejected_order_row(ts, fold_id, sym, q, refs[sym], kind,
                                    "weight_precision_reject")
            )
        else:
            executable_reds.append((sym, q, kind))

    # whole-rebalance margin pre-check: buy outlays vs free cash AFTER
    # reductions (virtual pass mirroring the executor exactly)
    cash_virtual = state["cash"]
    for sym, q, _kind in executable_reds:
        tick = params["tick_size"][sym]
        slip_amt = abs(params["slippage_ticks"]) * tick
        fill = _tick_round(refs[sym] + (-slip_amt if q < 0 else slip_amt), tick)
        cash_virtual += -(q * fill) - params["fee_taker"] * abs(q) * fill
    buy_outlay = 0.0
    for sym, q, _kind in increases:
        if q > 0 and not sub_min_notional(q, sym):
            tick = params["tick_size"][sym]
            slip_amt = abs(params["slippage_ticks"]) * tick
            fill = _tick_round(refs[sym] + slip_amt, tick)
            buy_outlay += abs(q) * fill
    margin_pre_ok = buy_outlay <= cash_virtual + MARGIN_TOL

    for sym, q, kind in executable_reds:
        _apply_fill(sym, q, refs[sym], ts, fold_id, kind, state, params,
                    orders, closed_legs)

    for sym, q, kind in increases:
        if sub_min_notional(q, sym):
            orders.append(
                _rejected_order_row(ts, fold_id, sym, q, refs[sym], kind,
                                    "weight_precision_reject")
            )
        elif not margin_pre_ok:
            orders.append(
                _rejected_order_row(ts, fold_id, sym, q, refs[sym], kind,
                                    "margin_breach")
            )
        else:
            _apply_fill(sym, q, refs[sym], ts, fold_id, kind, state, params,
                        orders, closed_legs)

    # post-trade invariants: identity vs marks at this event's closes, margin
    rhs = state["cash"] + sum(
        state["pos"][s] * refs[s] for s in traded
    )
    identity_ok = abs(state["equity"] - rhs) <= CASH_IDENTITY_TOL * max(1.0, abs(rhs))
    margin_ok = state["cash"] >= -MARGIN_TOL
    emit_invariant(margin_ok=margin_ok, identity_ok=identity_ok)
    return not margin_ok


# --------------------------------------------------------------------------- #
# Engine driver
# --------------------------------------------------------------------------- #
def run_shared_capital_backtest(
    bars_15m: dict[str, list[tuple[int, float, float, float, float, float]]],
    daily_closes: dict[str, list[tuple[int, float]]],
    weight_fn: Callable[[int], dict],
    *,
    tick_size: dict[str, float],
    step_size: dict[str, float],
    min_notional: float,
    fee_taker: float = 0.0005,
    slippage_ticks: int = 1,
    funding_bundles_dir: str | Path | None = None,
    initial_capital: float = 100000.0,
    folds: list[tuple[int, int]] | None = None,
) -> PortfolioRunResult:
    """Run the shared-capital cross-sectional backtest over merged 15m events."""
    symbols = sorted(bars_15m)
    for sym in symbols:
        bars_15m[sym].sort(key=lambda b: b[0])
    for name, table in (("tick_size", tick_size), ("step_size", step_size)):
        missing = [s for s in symbols if s not in table or table[s] <= 0]
        if missing:
            raise ValueError(f"{name} missing/non-positive for symbols {missing}")

    fold_list = sorted((int(a), int(b)) for a, b in (folds or [(0, (1 << 62))]))
    funding_enabled = funding_bundles_dir is not None
    settlements = _load_funding_settlements(funding_bundles_dir, symbols)
    params = {
        "tick_size": dict(tick_size),
        "step_size": dict(step_size),
        "min_notional": float(min_notional),
        "fee_taker": float(fee_taker),
        "slippage_ticks": int(slippage_ticks),
    }

    all_ts: set[int] = set()
    for sym in symbols:
        all_ts.update(b[0] for b in bars_15m[sym])
    timeline = sorted(all_ts)

    bars_by_ts: dict[int, list[tuple]] = {}
    for sym in symbols:
        for b in bars_15m[sym]:
            bars_by_ts.setdefault(b[0], []).append((sym, *b[1:]))

    def close_at(sym: str, ts: int) -> float | None:
        # bars_by_ts stores (sym, open, high, low, close, volume)
        for bar in bars_by_ts.get(ts, []):
            if bar[0] == sym:
                return bar[4]
        return None

    cutoff_grid = _Grid(DAY_NS)
    settle_grid = _Grid(FUNDING_PERIOD_NS)

    state: dict = {
        "cash": float(initial_capital),
        "equity": float(initial_capital),
        "pos": {s: 0.0 for s in symbols},
        "avg_entry": {s: 0.0 for s in symbols},
        "leg_cost": {s: 0.0 for s in symbols},
    }
    last_close: dict[str, float] = {}

    ledger: list[dict] = []
    orders: list[dict] = []
    closed_legs: list[dict] = []
    equity_curve: list[tuple[int, float]] = []
    skipped: list[dict] = []
    invariant_checks: list[dict] = []
    funding_rows: list[dict] = []

    turnover = 0.0
    n_orders_before = {"n": 0}
    gross_exposure_max = 0.0
    net_abs_max = 0.0
    aborted_folds: set[int | None] = set()
    abort_all = False
    suppressed_cutoffs = 0
    rebalances_scored = 0
    weight_calls = {"n": 0}
    dd_holder = {"max_dd_frac": 0.0, "max_dd_duration_days": 0.0}
    dd_state = {"peak": float(initial_capital), "peak_ts": None, "dd_start": None}

    def fold_index(ts: int) -> int | None:
        for fid, (start, end) in enumerate(fold_list):
            if start <= ts <= end:
                return fid
        return None

    def do_rebalance(cutoff: int, ts: int, fid: int | None) -> None:
        nonlocal rebalances_scored, turnover
        res = weight_fn(int(cutoff))
        weight_calls["n"] += 1
        if isinstance(res, dict) and res.get("status") == "SKIP_INCOMPLETE":
            skipped.append(
                {
                    "signal_ts": int(cutoff),
                    "execution_bar_ts": ts,
                    "reason_code": res.get("reason_code", "incomplete_cross_section_skip"),
                    "detail": "weight_fn SKIP_INCOMPLETE",
                }
            )
            return
        targets = _targets_from_weight_result(res)
        # cross-section completeness: any HELD symbol absent from the new
        # targets is flattened (membership drop => exit, never frozen leg)
        for s in symbols:
            if state["pos"][s] != 0.0 and s not in targets:
                targets[s] = 0.0
        refs: dict[str, float] = {}
        for sym in sorted(targets):
            px = close_at(sym, ts)
            if px is None:
                skipped.append(
                    {
                        "signal_ts": int(cutoff),
                        "execution_bar_ts": ts,
                        "reason_code": "incomplete_cross_section_skip",
                        "detail": f"missing_execution_bar:{sym}",
                    }
                )
                return
            refs[sym] = px

        breached = _execute_rebalance_core(
            cutoff=cutoff,
            ts=ts,
            fold_id=fid,
            targets=targets,
            refs=refs,
            state=state,
            params=params,
            orders=orders,
            closed_legs=closed_legs,
            invariant_checks=invariant_checks,
        )
        for o in orders[n_orders_before["n"]:]:
            if o["rejected_reason"] is None:
                turnover += o["qty"] * o["ref_price"]
        n_orders_before["n"] = len(orders)
        rebalances_scored += 1
        if breached:
            if fid is None:
                abort_all = True
            else:
                aborted_folds.add(fid)

    def track_drawdown(ts: int) -> None:
        eq = state["equity"]
        if eq > dd_state["peak"]:
            if dd_state["dd_start"] is not None:
                dur = (ts - dd_state["peak_ts"]) / DAY_NS
                dd_holder["max_dd_duration_days"] = max(
                    dd_holder["max_dd_duration_days"], dur
                )
            dd_state["peak"] = eq
            dd_state["peak_ts"] = ts
            dd_state["dd_start"] = None
        elif eq < dd_state["peak"]:
            dd = (
                (dd_state["peak"] - eq) / dd_state["peak"]
                if dd_state["peak"] > 0
                else 0.0
            )
            dd_holder["max_dd_frac"] = max(dd_holder["max_dd_frac"], dd)
            if dd_state["dd_start"] is None:
                dd_state["dd_start"] = ts
            if dd_state["peak_ts"] is None:
                dd_state["peak_ts"] = ts

    for ts in timeline:
        fid = fold_index(ts)

        # 1) refresh marks FIRST (on pre-fill positions) so fills, funding and
        #    every identity check reference THIS event's closes.
        for sym, *_rest in bars_by_ts.get(ts, []):
            px = close_at(sym, ts)
            if px is not None:
                prev = last_close.get(sym)
                if prev is not None and state["pos"][sym] != 0.0:
                    state["equity"] += state["pos"][sym] * (px - prev)
                last_close[sym] = px

        dues: list[tuple[int, int, int]] = []  # (time, priority, value)
        if funding_enabled:
            for s in settle_grid.due(ts):
                dues.append((s, 0, s))
        trading_suppressed = abort_all or (fid is not None and fid in aborted_folds)
        if not trading_suppressed:
            for c in cutoff_grid.due(ts):
                dues.append((c, 1, c))
        else:
            suppressed_cutoffs += len(cutoff_grid.due(ts))
        dues.sort()

        for _time, priority, stamp_ts in dues:
            if priority == 0:
                # FUNDING settlement applied to currently HELD legs at the
                # last observable close (this event's close when S == ts).
                for sym in symbols:
                    if state["pos"][sym] == 0.0:
                        continue
                    mark = last_close.get(sym)
                    if mark is None:
                        raise ValueError(
                            "funding settlement before any observable close: "
                            f"symbol={sym} settlement_ns={stamp_ts}"
                        )
                    table = settlements.get(sym) or {}
                    rate = table.get(stamp_ts)
                    if rate is None:
                        # Exchange settlement timestamps carry small jitter
                        # (milliseconds). Snap to the NEAREST known settlement
                        # within +/- 120s; beyond that, fail closed.
                        nearest_ts = None
                        if table:
                            known = sorted(table)
                            lo = 0
                            hi = len(known) - 1
                            while lo < hi:
                                mid = (lo + hi) // 2
                                if known[mid] < stamp_ts:
                                    lo = mid + 1
                                else:
                                    hi = mid
                            candidates = [known[lo]]
                            if lo > 0:
                                candidates.append(known[lo - 1])
                            nearest_ts = min(
                                candidates,
                                key=lambda t: abs(t - stamp_ts),
                            )
                        if (
                            nearest_ts is None
                            or abs(nearest_ts - stamp_ts) > 120_000_000_000
                        ):
                            raise ValueError(
                                "missing funding settlement for held leg "
                                f"(fail-closed): symbol={sym} settlement_ns={stamp_ts} "
                                f"bundle_dir={funding_bundles_dir!r} "
                                f"known_settlements={sorted(table)}"
                            )
                        rate = table[nearest_ts]
                    mark_notional = state["pos"][sym] * mark
                    cashflow = -rate * mark_notional
                    state["cash"] += cashflow
                    state["equity"] += cashflow
                    funding_rows.append(
                        {
                            "ts": stamp_ts,
                            "fold_id": fid,
                            "symbol": sym,
                            "rate": rate,
                            "mark_price": mark,
                            "mark_notional": mark_notional,
                            "cashflow": cashflow,
                        }
                    )
            else:
                do_rebalance(stamp_ts, ts, fid)

        # ledger / equity curve / exposure extremes for this event
        held_marks = {
            s: last_close[s] for s in symbols
            if state["pos"][s] != 0.0 and s in last_close
        }
        gross_val = sum(abs(state["pos"][s]) * px for s, px in held_marks.items())
        net_val = sum(state["pos"][s] * px for s, px in held_marks.items())
        rhs = state["cash"] + net_val
        identity_ok = abs(state["equity"] - rhs) <= CASH_IDENTITY_TOL * max(1.0, abs(rhs))
        frac_den = state["equity"] if state["equity"] > 0 else 1.0
        ledger.append(
            {
                "ts": ts,
                "fold_id": fid,
                "equity": state["equity"],
                "cash": state["cash"],
                "margin": state["cash"],
                "gross_exposure": gross_val / frac_den,
                "net_exposure": net_val / frac_den,
                "positions": {s: state["pos"][s] for s in symbols if state["pos"][s] != 0.0},
                "marks": held_marks,
                "cash_identity_ok": identity_ok,
            }
        )
        equity_curve.append((ts, state["equity"]))
        gross_exposure_max = max(gross_exposure_max, gross_val / frac_den)
        net_abs_max = max(net_abs_max, abs(net_val) / frac_den)
        track_drawdown(ts)

    if timeline:
        # still underwater at the end -> measure to the last event
        if dd_state["dd_start"] is not None and dd_state["peak_ts"] is not None:
            dur = (timeline[-1] - dd_state["peak_ts"]) / DAY_NS
            dd_holder["max_dd_duration_days"] = max(
                dd_holder["max_dd_duration_days"], dur
            )

    pnls = [leg["realized_pnl"] for leg in closed_legs]
    stats = position_pnl_stats(pnls)
    summary = {
        "total_pnl": state["equity"] - float(initial_capital),
        "trades": stats.trades,
        "gross_profit": stats.gross_profit,
        "gross_loss": stats.gross_loss,
        "profit_factor": stats.profit_factor,
        "pf_reason": stats.pf_reason,
        "max_drawdown_frac": dd_holder["max_dd_frac"],
        "max_dd_duration_days": dd_holder["max_dd_duration_days"],
        "turnover_total_notional": turnover,
        "gross_exposure_max": gross_exposure_max,
        "net_abs_max": net_abs_max,
        "rebalances_scored": rebalances_scored,
        "legs_closed": len(closed_legs),
    }
    meta = {
        "symbols": symbols,
        "initial_capital": float(initial_capital),
        "fee_taker": fee_taker,
        "slippage_ticks": slippage_ticks,
        "min_notional": float(min_notional),
        "folds": [list(f) for f in fold_list],
        "aborted_folds": sorted(f for f in aborted_folds),
        "aborted_unfolded_margin": bool(abort_all),
        "n_events": len(timeline),
        "first_event_ts": timeline[0] if timeline else None,
        "last_event_ts": timeline[-1] if timeline else None,
        "weight_fn_calls": weight_calls["n"],
        "cutoffs_suppressed_aborted_fold": suppressed_cutoffs,
        "funding_total": sum(r["cashflow"] for r in funding_rows),
        "funding_enabled": funding_enabled,
        "daily_closes_symbols": sorted(daily_closes),
        "final_equity": state["equity"],
    }
    return PortfolioRunResult(
        portfolio_ledger=ledger,
        orders=orders,
        closed_legs=closed_legs,
        equity_curve=equity_curve,
        skipped_rebalances=skipped,
        invariant_checks=invariant_checks,
        funding_cashflows=funding_rows,
        summary=summary,
        meta=meta,
    )
