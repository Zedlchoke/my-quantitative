"""ES1 engine — bar-level backtester for the frozen BTC_H4 panel.

Conventions (PSV1 law, reconciled against the PSV1 committed ledger by
scripts/es1_reconcile_comparator.py — identity gate rel-err <= 1e-6):
  decision at H4 close t -> position change filled at open of t+1
  fees: 6 bps/side full stack x tier, charged on traded notional at fill
  funding: signed, charged at 00:00/08:00/16:00 UTC bar opens on the held
           notional (constant law: 1.377e-5; measured law: Vision series)
  fold ends force-flat (exit at the fold's last bar close, costs charged)
  capital $100,000, fraction <= 1.0, no leverage

NO lookahead: every signal uses bars with close time <= decision time.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

CAPITAL = 100_000.0
COST_PER_SIDE_BPS = 6.0
FUNDING_CONST = 1.377e-5
WARMUP = 153
FOLD_EDGES_MS = [pd.Timestamp(e, tz="UTC").value // 10**6
                 for e in ("2021-05-01", "2023-01-01", "2025-01-01")]
BTC_PANEL = ("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
             "lane-btc-h4/research/control/phase_strategy_v1/lane_btc_h4/data_staging/scored_h4.parquet")
BTC_LABELS = ("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
              "lane-btc-h4/research/control/phase_strategy_v1/lane_btc_h4/data_staging/labels_frozen.parquet")
FUNDING_DIR = ("/Users/hoangminhlong/my-quantitative/.worktrees/btc-h4-edge-search-v1/"
               "integration/research/control/btc_h4_edge_search_v1/data_local/vision/funding_BTCUSDT")

# PSV1 frozen Donchian constants (lane_btc_h4 pipeline/config.py, verbatim)
DONCH_ENTRY, DONCH_STOP, MIN_HOLD, MAX_HOLD, EXIT_BUFFER = 30, 15, 12, 450, 6


@dataclass
class Result:
    net: float
    gross: float
    fees: float
    funding: float
    entries: int
    fills: int
    max_drawdown: float
    fold_net: dict = field(default_factory=dict)
    equity: np.ndarray = None

    def as_dict(self, include_equity=False):
        d = {"net": round(self.net, 2), "gross": round(self.gross, 2),
             "fees": round(self.fees, 2), "funding": round(self.funding, 2),
             "entries": self.entries, "fills": self.fills,
             "max_drawdown": round(self.max_drawdown, 4),
             "fold_net": {k: round(v, 2) for k, v in self.fold_net.items()}}
        if include_equity:
            d["equity"] = self.equity
        return d


def load_panel():
    h4 = pd.read_parquet(BTC_PANEL)
    lab = pd.read_parquet(BTC_LABELS)
    assert (h4["bucket_ms"].to_numpy() == lab["bucket_ms"].to_numpy()).all()
    return h4, lab["phase"].to_numpy().astype(str)


def load_funding_measured() -> pd.DataFrame:
    import zipfile
    rows = []
    for p in sorted(Path(FUNDING_DIR).glob("*.zip")):
        with zipfile.ZipFile(p) as z:
            raw = z.read(z.namelist()[0]).decode()
        lines = raw.strip().split("\n")
        start = 1 if not lines[0].split(",")[0].strip().isdigit() else 0
        for ln in lines[start:]:
            f = ln.split(",")
            rows.append((int(f[0]), float(f[2])))
    fr = pd.DataFrame(rows, columns=["ms", "rate"]).sort_values("ms")
    assert fr["ms"].is_monotonic_increasing and fr["rate"].notna().all()
    return fr


def fold_ids(open_ms: np.ndarray) -> np.ndarray:
    f = np.zeros(len(open_ms), dtype=int)
    for e in FOLD_EDGES_MS:
        f += (open_ms >= e).astype(int)
    return f


# ---------------- signal builders (all causal) ----------------

def sig_always_on(panel) -> np.ndarray:
    return np.ones(len(panel))


def sig_trend_lf(panel, band: float = 0.0) -> np.ndarray:
    close = panel["close"].to_numpy(float)
    sma = pd.Series(close).rolling(200).mean().to_numpy()
    out = np.zeros(len(panel))
    state = 0
    for t in range(len(panel)):
        if not np.isfinite(sma[t]):
            out[t] = 0
            continue
        r = close[t] / sma[t] - 1.0
        if state == 0 and r > band:
            state = 1
        elif state == 1 and r < -band:
            state = 0
        out[t] = state
    return out


def sig_donchian(panel, labels):
    """PSV1 BTC_H4 Donchian-continuation long book, frozen law.
    Returns (pos, exit_reasons dict)."""
    close = panel["close"].to_numpy(float)
    up = (labels == "UPTREND")
    n = len(panel)
    pos = np.zeros(n, dtype=int)
    state = 0
    held = 0
    non_up_run = 0
    exits = {"DONCHIAN_STOP": 0, "GATE_INACTIVE": 0, "MAX_HOLD": 0}
    for t in range(n):
        if t < WARMUP:
            pos[t] = 0
            continue
        enter_break = close[t] > np.max(close[t - DONCH_ENTRY:t])
        stop_break = close[t] < np.min(close[t - DONCH_STOP:t])
        if state == 0:
            if up[t] and enter_break:
                state, held, non_up_run = 1, 0, 0
        else:
            held += 1
            non_up_run = non_up_run + 1 if not up[t] else 0
            if stop_break and held >= MIN_HOLD:
                state = 0
                exits["DONCHIAN_STOP"] += 1
            elif held >= MAX_HOLD:
                state = 0
                exits["MAX_HOLD"] += 1
            elif non_up_run >= EXIT_BUFFER:
                state = 0
                exits["GATE_INACTIVE"] += 1
        pos[t] = state
    return pos, exits


def rvol_series(panel, bars: int = 150) -> np.ndarray:
    close = panel["close"].to_numpy(float)
    ret = np.diff(np.log(close), prepend=np.log(close[0]))
    return pd.Series(ret).rolling(bars).std().to_numpy() * np.sqrt(6 * 365)


def sig_vol_managed(base: np.ndarray, rvol: np.ndarray, target: float) -> np.ndarray:
    scale = np.minimum(1.0, target / rvol)
    scale = np.where(np.isfinite(scale), scale, 0.0)
    return base * scale


def block_shuffle(series: np.ndarray, block: int = 30, seed: int = 20260923) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = len(series)
    nblocks = int(np.ceil(n / block))
    order = rng.permutation(nblocks)
    out = np.concatenate([series[src * block: (src + 1) * block] for src in order])[:n]
    return out


# ---------------- core simulator ----------------

def simulate(decision_fraction: np.ndarray, panel, folds: np.ndarray,
             tier: float = 1.0, funding_law: str = "constant",
             funding_df: pd.DataFrame | None = None) -> Result:
    """decision_fraction[t] is decided at close of bar t; held from open t+1.
    Fold law: at the fold's last bar the position is force-closed AT CLOSE
    (exit fee charged to that fold); the next fold starts flat and re-fills
    at its own first open (PSV1 're-entered at each fold start' convention)."""
    n = len(panel)
    open_ = panel["open"].to_numpy(float)
    close = panel["close"].to_numpy(float)
    fee = COST_PER_SIDE_BPS / 1e4 * tier
    hours = pd.to_datetime(panel["bucket_ms"], unit="ms", utc=True).dt.hour.to_numpy()
    is_boundary = np.isin(hours, [0, 8, 16])
    if funding_law == "measured":
        assert funding_df is not None
        fms = funding_df["ms"].to_numpy()
        frt = funding_df["rate"].to_numpy()

    def measured_rate(ms: int) -> float:
        i = np.searchsorted(fms, ms)
        for j in (i - 1, i):
            if 0 <= j < len(fms) and abs(int(fms[j]) - ms) <= 60_000:
                return float(frt[j])
        return 0.0

    pos = np.zeros(n)
    pos[1:] = decision_fraction[:-1]
    pos[0] = 0.0  # window starts flat; each fold re-fills via its own decisions

    equity = CAPITAL
    gross = fees = funding_paid = 0.0
    eq_path = np.empty(n)
    entries = fills = 0
    fold_net = {}

    for t in range(n):
        pnl_t = 0.0
        fee_t = 0.0
        if t == 0:
            eq_path[t] = equity
            continue
        gap = open_[t] / close[t - 1] - 1.0
        leg = pos[t - 1] * gap * equity
        equity *= (1.0 + pos[t - 1] * gap)
        dpos = pos[t] - pos[t - 1]
        if abs(dpos) > 1e-12:
            notional = abs(dpos) * equity
            fee_t += notional * fee
            equity -= notional * fee
            fills += 1
            if pos[t - 1] == 0.0 and pos[t] > 0.0:
                entries += 1
        ib = close[t] / open_[t] - 1.0
        leg += pos[t] * ib * equity
        equity *= (1.0 + pos[t] * ib)
        pay = 0.0
        if is_boundary[t] and pos[t] > 0:
            rate = FUNDING_CONST if funding_law == "constant" else measured_rate(int(panel["bucket_ms"].iloc[t]))
            pay = rate * pos[t] * equity
            equity -= pay
        last_of_fold = (t == n - 1) or (folds[t + 1] != folds[t])
        if last_of_fold and abs(pos[t]) > 1e-12:
            notional = abs(pos[t]) * equity
            fee_t += notional * fee
            equity -= notional * fee
            fills += 1
            pos[t] = 0.0
        gross += leg
        fees += fee_t
        funding_paid += pay
        fold = int(folds[t])
        fold_net[f"F{fold+1}"] = fold_net.get(f"F{fold+1}", 0.0) + leg - fee_t - pay
        eq_path[t] = equity

    net = equity - CAPITAL
    assert abs(net - (gross - fees - funding_paid)) < 1e-6 * max(1.0, abs(net)), \
        "accounting identity violated"
    dd = float(np.max(1.0 - eq_path / np.maximum.accumulate(eq_path)))
    return Result(net=net, gross=gross, fees=fees, funding=funding_paid,
                  entries=entries, fills=fills, max_drawdown=dd,
                  fold_net=fold_net, equity=eq_path)


def run_window(window=slice(WARMUP, None)):
    """Load + slice panel to the post-warmup window; returns panel/folds."""
    h4, labels = load_panel()
    h4w = h4.iloc[window].reset_index(drop=True)
    labw = labels[window]
    folds = fold_ids(h4w["bucket_ms"].to_numpy())
    return h4w, labw, folds
