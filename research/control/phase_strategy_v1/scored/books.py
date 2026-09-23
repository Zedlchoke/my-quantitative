"""PSV1 scored: arm books — candidate adapters (lane machines verbatim),
frozen baselines, frozen falsification controls. A1 scored namespace.

Adapters convert the lanes' frozen event machines into FILL SCHEDULES for
accounting.run_accounting:
- L1 (BTC_H1) events are DECISION bars: entry fills at decision+1 open,
  non-fold exits at decision+1 open, FOLD_END_FORCE_FLAT at the fold's last
  close (force-flat law; no spill).
- L2 (BTC_H4) records carry fill bars: fill_bar = decision+1 -> open fill;
  fold-end / SERIES_END fill_bar = last bar -> close fill.
Same-bar exit+entry pairs are NETTED by the accounting engine (churn law).
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from cells import L1_CODE, L2_PIPE, L2_STAGE  # noqa: F401
from accounting import run_accounting  # noqa: F401

CONTROL_SEED = 20260923           # frozen in both proposals
SHUFFLE_DRAWS_L1 = 100            # frozen (L1 phase-shuffled controls)
KS_MOVEMENT_BAR = 0.15            # frozen movement-validation bar (L1)
CLOCK_ONLY_EXIT_BARS = 720        # frozen (ACC clock-only control)


# ---------------------------------------------------------------- L1 adapter
def l1_events_to_fills(ev, side: int, n_bars: int | None = None) -> list[tuple[int, float, bool]]:
    fills: list[tuple[int, float, bool]] = []
    for t in ev.entries:
        if n_bars is not None and t + 1 >= n_bars:
            continue  # entry decided on the final bar: no executable fill bar
        fills.append((t + 1, float(side), False))
    for t, reason in ev.exits:
        if reason == "FOLD_END_FORCE_FLAT":
            fills.append((t, 0.0, True))       # force-flat: close of fold's last bar
        elif n_bars is not None and t + 1 >= n_bars:
            fills.append((t, 0.0, True))       # series end: flat at final close
        else:
            fills.append((t + 1, 0.0, False))
    return fills


def l1_candidate_signals(cell: dict, which: str):
    """Run the frozen L1 signal machine; returns (events, side)."""
    if str(L1_CODE) not in sys.path:
        sys.path.insert(0, str(L1_CODE))
    import proposals as prop  # noqa
    df = cell["labels_df"]
    fold_ids = cell["fold_ids"]
    if which == "PSV1-BTC_H1-UPTREND-BREAKOUT_CONT":
        ev, _ = prop.signals_uptrend_breakout(df, fold_ids)
        return ev, 1
    if which == "PSV1-BTC_H1-ACC-FLOOR_PROVISION":
        ev, _ = prop.signals_acc_floor_provision(df, fold_ids)
        return ev, 1
    if which == "PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT":
        ev, _ = prop.signals_downtrend_breakdown_cont(df, fold_ids)
        return ev, -1
    raise KeyError(which)


# ---------------------------------------------------------------- L2 adapter
def l2_run_book(cell: dict, labels: np.ndarray | None = None) -> dict:
    """Run the frozen L2 Donchian book verbatim (config constants are the
    frozen arm parameters); returns the book dict with trade records."""
    if str(L2_PIPE) not in sys.path:
        sys.path.insert(0, str(L2_PIPE))
    from pipeline import events as ev2, config as cfg2  # noqa
    spec = ev2.BookSpec(
        name="PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION",
        phase="UPTREND",
        trigger="donchian_breakout",
        donch_entry=cfg2.DONCH_ENTRY, donch_stop=cfg2.DONCH_STOP,
        exit_buffer=cfg2.EXIT_BUFFER_BARS, min_hold=cfg2.MIN_HOLD_BARS,
        max_hold=cfg2.MAX_HOLD_BARS, direction=1)
    labels = cell["labels"] if labels is None else labels
    return ev2.run_book(labels, cell["close"], spec, cell["fold_ids"])


def l2_fills_from_book(book: dict) -> list[tuple[int, float, bool]]:
    fills: list[tuple[int, float, bool]] = []
    for trs in book["_trade_records"].values():
        for tr in trs:
            fills.append((int(tr["entry_bar"]), 1.0, False))
            # fold-end / series-end exits carry fill_bar == last bar of fold
            at_close = bool(tr["exit_reason"] in ("FOLD_END", "SERIES_END_OPEN"))
            fills.append((int(tr["exit_bar"]), 0.0, at_close))
    return fills


# ---------------------------------------------------------------- baselines
def baseline_always_on_long(cell: dict) -> list[tuple[int, float, bool]]:
    fills = []
    fold_ids = cell["fold_ids"]
    n = len(fold_ids)
    for f in sorted(set(fold_ids.tolist())):
        idx = np.where(fold_ids == f)[0]
        fills.append((int(idx[0]), 1.0, False))
        fills.append((int(idx[-1]), 0.0, True))
    return fills


def _target_to_fills(decision: np.ndarray, fold_ids: np.ndarray):
    """Decision series (position decided at close t, held from open t+1) ->
    fill events. during[t] = decision[t-1]; fold force-flat: during = 0 at
    each fold's last bar (exit at that bar's close, no spill)."""
    n = len(decision)
    fold_last: dict[int, int] = {}
    for i, f in enumerate(fold_ids):
        f = int(f)
        if i == n - 1 or int(fold_ids[i + 1]) != f:
            fold_last[f] = i
    during = np.zeros(n)
    if n > 1:
        during[1:] = np.asarray(decision)[: n - 1]
    for last in fold_last.values():
        during[last] = 0.0
    fills: list[tuple[int, float, bool]] = []
    prev = 0.0
    for t in range(n):
        cur = float(during[t])
        if cur != prev:
            if cur == 0.0:
                at_close = t in fold_last.values()
                fills.append((t, 0.0, at_close))
            else:
                fills.append((t, cur, False))
            prev = cur
    return fills


def baseline_always_on_trend_lf(cell: dict) -> list[tuple[int, float, bool]]:
    close = cell["close"]
    sma = pd.Series(close).rolling(200, min_periods=200).mean().to_numpy()
    decision = np.where(np.isfinite(sma) & (close > sma), 1.0, 0.0)
    return _target_to_fills(decision, cell["fold_ids"])


def baseline_sparse_risk_off(cell: dict, out_dd: float, in_dd: float = 0.10,
                             min_hold: int = 5) -> list[tuple[int, float, bool]]:
    close = cell["close"]
    runmax = np.maximum.accumulate(close)
    dd = 1.0 - close / runmax
    n = len(close)
    state = 1.0
    last_flip = -10**9
    decision = np.empty(n)
    for t in range(n):
        if t - last_flip >= min_hold:
            if state == 1.0 and dd[t] > out_dd:
                state = 0.0
                last_flip = t
            elif state == 0.0 and dd[t] <= in_dd:
                state = 1.0
                last_flip = t
        decision[t] = state
    return _target_to_fills(decision, cell["fold_ids"])


# ---------------------------------------------------------------- controls
def _episode_blocks(labels: np.ndarray, fold_ids: np.ndarray):
    """Per fold: list of (start, length, label) maximal same-label runs."""
    blocks = []
    n = len(labels)
    for f in sorted(set(int(x) for x in fold_ids.tolist())):
        idx = np.where(fold_ids == f)[0]
        start = int(idx[0])
        for k in range(int(idx[0]) + 1, int(idx[-1]) + 2):
            if k > idx[-1] or labels[k] != labels[k - 1]:
                blocks.append((f, start, k - start, str(labels[start])))
                start = k
    _ = n
    return blocks


def _permute_labels_by_episode_blocks(cell: dict, rng: np.random.Generator) -> np.ndarray:
    labels = np.asarray(cell["labels_df"]["state_label"].astype(str))
    out = labels.copy()
    for f in sorted(set(int(x) for x in cell["fold_ids"].tolist())):
        fblocks = [(s, ln, lb) for (ff, s, ln, lb) in _episode_blocks(labels, cell["fold_ids"]) if ff == f]
        order = rng.permutation(len(fblocks))
        pos = fblocks[0][0]
        for j in order:
            s, ln, lb = fblocks[j]
            out[pos:pos + ln] = lb
            pos += ln
    return out


def _ks_2samp(a: np.ndarray, b: np.ndarray) -> float:
    a = np.sort(np.asarray(a, float))
    b = np.sort(np.asarray(b, float))
    allv = np.concatenate([a, b])
    cdf_a = np.searchsorted(a, allv, side="right") / max(len(a), 1)
    cdf_b = np.searchsorted(b, allv, side="right") / max(len(b), 1)
    return float(np.max(np.abs(cdf_a - cdf_b)))


def _entry_forward_moves(close: np.ndarray, decision_bars: list[int], horizon: int) -> np.ndarray:
    out = []
    for t in decision_bars:
        j = t + horizon
        if j < len(close) and close[t] > 0:
            out.append(close[j] / close[t] - 1.0)
    return np.asarray(out)


def l1_phase_shuffled_control(cell: dict, which: str, tier: float, bps: float,
                              funding_mask, funding_rate):
    """100 draws; per draw: rebuild labels by episode-block permutation,
    re-run the IDENTICAL frozen signal machine, account it; movement
    validation KS <= 0.15 on entry-time 24h realized moves (candidate vs
    control decision bars); control verdict = median net over VALID draws."""
    if str(L1_CODE) not in sys.path:
        sys.path.insert(0, str(L1_CODE))
    import proposals as prop  # noqa
    rng = np.random.default_rng(CONTROL_SEED)
    cand_ev, side = l1_candidate_signals(cell, which)
    cand_moves = _entry_forward_moves(cell["close"], cand_ev.entries, 24)
    fold_ids = cell["fold_ids"]
    nets: list[float] = []
    valid = 0
    for _ in range(SHUFFLE_DRAWS_L1):
        sh = _permute_labels_by_episode_blocks(cell, rng)
        df2 = cell["labels_df"].copy()
        df2["state_label"] = sh
        if which == "PSV1-BTC_H1-UPTREND-BREAKOUT_CONT":
            ev, _ = prop.signals_uptrend_breakout(df2, fold_ids)
        elif which == "PSV1-BTC_H1-ACC-FLOOR_PROVISION":
            ev, _ = prop.signals_acc_floor_provision(df2, fold_ids)
        else:
            ev, _ = prop.signals_downtrend_breakdown_cont(df2, fold_ids)
        if not ev.entries:
            continue
        moves = _entry_forward_moves(cell["close"], ev.entries, 24)
        if len(cand_moves) and _ks_2samp(moves, cand_moves) > KS_MOVEMENT_BAR:
            continue
        fills = l1_events_to_fills(ev, side)
        res = run_accounting(cell["open"], cell["close"], fills,
                             cell["fold_ids"], bps, tier,
                             funding_mask, funding_rate)
        nets.append(res["net"])
        valid += 1
    med = float(np.median(nets)) if nets else None
    return {"valid_draws": valid, "total_draws": SHUFFLE_DRAWS_L1,
            "median_net": med, "candidate_entry_moves_n": int(len(cand_moves))}


def l1_clock_only_control(cell: dict, tier: float, bps: float,
                          funding_mask, funding_rate):
    """ACC control: identical structure entry (lower quartile of the trailing
    720-bar close range) WITHOUT the phase gate; thinned keep-every-k to the
    candidate's entry count; exits on the frozen 720-bar clock."""
    df = cell["labels_df"]
    close = df["close"].to_numpy(float)
    n = len(close)
    r_hi = pd.Series(close).rolling(720).max().to_numpy()
    r_lo = pd.Series(close).rolling(720).min().to_numpy()
    in_lower_q = close <= r_lo + 0.25 * (r_hi - r_lo)
    trigger = in_lower_q & np.isfinite(r_hi - r_lo)
    cand_ev, _ = l1_candidate_signals(cell, "PSV1-BTC_H1-ACC-FLOOR_PROVISION")
    k = max(1, int(np.ceil(len(np.where(trigger)[0]) / max(len(cand_ev.entries), 1))))
    # thinned event loop: min_hold 0, gate always active, 720-bar clock exit
    entry_decisions: list[int] = []
    pos = 0
    entry_i = -1
    fold_ids = cell["fold_ids"]
    fills: list[tuple[int, float, bool]] = []
    kept = 0
    for t in range(n):
        if fold_ids[t] != fold_ids[t - 1] and t > 0 and pos != 0:
            fills.append((t - 1, 0.0, True))
            pos = 0
        if pos != 0 and (t - entry_i) >= CLOCK_ONLY_EXIT_BARS:
            fills.append((t + 1, 0.0, False) if t + 1 < n else (t, 0.0, True))
            pos = 0
        if pos == 0 and trigger[t]:
            kept += 1
            if kept % k == 0:
                pos = 1
                entry_i = t
                fills.append((t + 1, 1.0, False) if t + 1 < n else (t, 1.0, True))
    res = run_accounting(cell["open"], cell["close"], fills, fold_ids, bps, tier,
                         funding_mask, funding_rate)
    return {"k": k, "ungated_events": int(np.sum(trigger)), "kept": kept,
            "candidate_entries": len(cand_ev.entries), "net": res["net"]}
