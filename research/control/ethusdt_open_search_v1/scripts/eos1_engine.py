"""EOS1 engine — deterministic, stdlib-only backtest kernel for
ETHUSDT-OPEN-SEARCH-V1 (plan: plans/PLAN_ethusdt_open_search_v1.md §2–§6).

Frozen laws encoded here (any change after scored PnL is visible = new
experiment, never a silent edit):

  Grid       H4 bars at UTC boundaries 00/04/08/12/16/20 built from 1h
             Vision zips; an H4 bar exists iff all 4 hourly bars exist
             (incomplete groups dropped and counted, never patched).
  PIT        target[i] is decided at bar i-1's close from info-series bars
             with open_ts <= open_ts(i-1) (they close simultaneously);
             the first fill lands on bar i's OPEN. build_targets() applies
             exactly ONE one-bar shift; run_book consumes the shifted
             series as-is.
  Costs      taker 5.0 bps/side on raw fill price; 1 adverse tick (0.01)
             in PRICE per side; tier k in {1.0,1.5,2.0} scales fee AND
             tick. Funding = measured per-settlement account cashflow
             -sign * qty * price_at_settlement * rate (longs pay when
             rate > 0; shorts receive); settlement priced at the 1h OPEN
             of the settlement timestamp, else the last 1h close <= ts
             (counted fallback).
  Notion     $100,000 fixed at each entry (qty = notional / raw fill px).
  Folds      by ETH H4 bar open_ts date in [start, end):
             F1 [2020-01-01, 2021-05-01) F2 [2021-05-01, 2023-01-01)
             F3 [2023-01-01, 2025-01-01) F4 [2025-01-01, 2026-09-01)
             Trading only inside folds. At the LAST existing ETH bar of a
             fold the position force-closes at that bar's CLOSE (boundary
             law, identical everywhere). Trade PnL (entry+exit fees booked
             at exit) and funding cashflow attribute to the fold of the
             exit fill / settlement bar.
  States     arms long/flat {0,1}; references may hold {-1,0,1}. A missing
             info boundary reads the last observed state (hold, counted).
"""
from __future__ import annotations

import bisect
import csv
import datetime as dt
import hashlib
import io
import json
import math
import pathlib
import random
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data_local" / "vision"

H4_MS = 4 * 3600 * 1000
NOTIONAL = 100_000.0
FEE_BPS = 5.0
TICK = 0.01
TIERS = (1.0, 1.5, 2.0)
BLOCK_SHUFFLE_BARS = 30

FOLDS = [
    ("F1", "2020-01-01", "2021-05-01"),
    ("F2", "2021-05-01", "2023-01-01"),
    ("F3", "2023-01-01", "2025-01-01"),
    ("F4", "2025-01-01", "2026-09-01"),
]
_FOLD_START_MS = {s: int(dt.datetime.strptime(s, "%Y-%m-%d")
                         .replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
                  for _, s, _ in FOLDS}
_FOLD_END_MS = {e: int(dt.datetime.strptime(e, "%Y-%m-%d")
                       .replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
                for _, _, e in FOLDS}

SERIES_ETHUSDT = "klines_um_ETHUSDT_1h"
SERIES_BTCUSDT = "klines_um_BTCUSDT_1h"
SERIES_ETHBTC = "klines_spot_ETHBTC_1h"
SERIES_FUNDING = "fundingRate_um_ETHUSDT"


# ---------------------------------------------------------------- loaders

def _norm_ts(v: str) -> int:
    """Vision kline open_time is ms in older files and us in newer ones
    (magnitude >= 1e14 => us). Normalise to ms."""
    n = int(v)
    return n // 1000 if n >= 10 ** 14 else n


def _is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False


def load_1h(series: str) -> list[dict]:
    """Sorted, de-duplicated 1h bars [{ts,open,high,low,close}] from
    monthly zips. UM futures kline files have NO header row (positional
    columns open_time,open,high,low,close,...); spot files carry a header
    — both handled by sniffing the first cell. Fail-closed on malformed
    rows (file+row reported)."""
    bars: dict[int, dict] = {}
    d = DATA / series
    for zpath in sorted(d.glob("*.zip")):
        with zipfile.ZipFile(zpath) as z:
            text = z.read(z.namelist()[0]).decode("utf-8")
        rdr = csv.reader(io.StringIO(text))
        first = next(rdr)
        if first and _is_int(first[0]):
            oi = 0                       # um: positional, no header
            ci = 4
            data_rows = [first] + list(rdr)
        else:
            header = [h.strip() for h in first]   # spot: named header
            oi = header.index("open_time")
            ci = header.index("close")
            data_rows = list(rdr)
        for ln, row in enumerate(data_rows, start=2):
            if not row or not row[oi]:
                continue
            try:
                ts = _norm_ts(row[oi])
                bar = {"ts": ts, "open": float(row[oi + 1]),
                       "high": float(row[oi + 2]),
                       "low": float(row[oi + 3]),
                       "close": float(row[ci])}
            except Exception as e:
                raise RuntimeError(f"malformed row {zpath.name}:{ln}: {e}") from e
            if ts in bars and bars[ts]["close"] != bar["close"]:
                raise RuntimeError(f"conflicting duplicate ts {zpath.name}:{ln}")
            bars[ts] = bar
    return [bars[k] for k in sorted(bars)]


def load_funding(series: str = SERIES_FUNDING) -> list[dict]:
    """Settlement rows [{ts, rate}] from monthly fundingRate zips."""
    rows: dict[int, float] = {}
    d = DATA / series
    for zpath in sorted(d.glob("*.zip")):
        with zipfile.ZipFile(zpath) as z:
            text = z.read(z.namelist()[0]).decode("utf-8")
        rdr = csv.reader(io.StringIO(text))
        header = next(rdr)
        ti = next(i for i, h in enumerate(header) if "time" in h.lower())
        ri = next(i for i, h in enumerate(header)
                  if "rate" in h.lower() and "interval" not in h.lower())
        for ln, row in enumerate(rdr, start=2):
            if not row or not row[ti]:
                continue
            try:
                rows[_norm_ts(row[ti])] = float(row[ri])
            except Exception as e:
                raise RuntimeError(f"malformed funding row {zpath.name}:{ln}: {e}") from e
    return [{"ts": k, "rate": rows[k]} for k in sorted(rows)]


# ---------------------------------------------------------------- H4 grid

def to_h4(bars_1h: list[dict]) -> tuple[list[dict], int]:
    """4h bars at UTC boundaries (open_ts % 4h == 0); a bar is emitted iff
    all 4 hourly bars exist. Dropped counts every 4h window in the data
    span (first bar's boundary .. last bar) that produced no bar — whether
    the boundary hour itself is missing or the group is incomplete."""
    by_ts = {b["ts"]: b for b in bars_1h}
    out, dropped = [], 0
    if not bars_1h:
        return out, dropped
    first_b = (bars_1h[0]["ts"] // H4_MS) * H4_MS
    last_b = (bars_1h[-1]["ts"] // H4_MS) * H4_MS
    b = first_b
    while b <= last_b:
        hours = [by_ts.get(b + i * 3600_000) for i in range(4)]
        if any(h is None for h in hours):
            dropped += 1
        else:
            out.append({"ts": b, "open": hours[0]["open"],
                        "high": max(h["high"] for h in hours),
                        "low": min(h["low"] for h in hours),
                        "close": hours[3]["close"]})
        b += H4_MS
    return out, dropped


# ---------------------------------------------------------------- indicators

def sma_states(closes: list[float], n: int) -> list[int | None]:
    """1 iff close > SMA(n) ending at that bar; None during warmup."""
    out, s = [], 0.0
    for i, c in enumerate(closes):
        s += c
        if i >= n:
            s -= closes[i - n]
        out.append((1 if c > s / n else 0) if i + 1 >= n else None)
    return out


def sign_states(closes: list[float], lag_bars: int) -> list[int | None]:
    """1 iff close > close lag_bars earlier; None during warmup."""
    return [(1 if c > closes[i - lag_bars] else 0) if i >= lag_bars else None
            for i, c in enumerate(closes)]


def pct_rank_states(closes: list[float], window: int) -> list[int | None]:
    """1 iff percentile rank of the latest close within the trailing
    `window` closes > 0.50; rank = #{x in window : x < v}/(window-1)."""
    out = []
    for i, c in enumerate(closes):
        if i + 1 >= window:
            w = closes[i - window + 1: i + 1]
            rank = sum(1 for x in w if x < c) / (window - 1)
            out.append(1 if rank > 0.50 else 0)
        else:
            out.append(None)
    return out


# ---------------------------------------------------------------- state plumbing

class InfoSeries:
    """Signal series on its own H4 sequence with last-observed reads at
    any boundary (hold-previous law when the boundary is missing)."""

    def __init__(self, h4: list[dict], states: list[int | None]):
        self.by_ts = {b["ts"]: s for b, s in zip(h4, states) if s is not None}
        self.ts_sorted = sorted(self.by_ts)
        self.fallback_reads = 0

    def state_at(self, ts: int) -> int | None:
        if ts in self.by_ts:
            return self.by_ts[ts]
        i = bisect.bisect_right(self.ts_sorted, ts) - 1
        if i < 0:
            return None
        self.fallback_reads += 1
        return self.by_ts[self.ts_sorted[i]]


def shuffle_blocks(states: list[int], block: int, seed: str) -> list[int]:
    """G6 block-shuffle: permute the ORDER of consecutive `block`-bar
    blocks (seeded), preserving within-block structure."""
    rng = random.Random(int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16))
    blocks = [states[i:i + block] for i in range(0, len(states), block)]
    rng.shuffle(blocks)
    out: list[int] = []
    for b in blocks:
        out.extend(b)
    return out


def spearman(x: list[float], y: list[float]) -> float:
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


# ---------------------------------------------------------------- backtest

def fold_of(ts: int) -> str | None:
    d = dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc).strftime("%Y-%m-%d")
    for name, s, e in FOLDS:
        if s <= d < e:
            return name
    return None


class PriceAtSettlement:
    """Settlement priced at the 1h OPEN of the settlement timestamp; if
    that 1h bar is missing, the last 1h CLOSE strictly <= ts (counted)."""

    def __init__(self, bars_1h: list[dict]):
        self.open_by_ts = {b["ts"]: b["open"] for b in bars_1h}
        self.ts_sorted = sorted(self.open_by_ts)
        self.close_by_ts = {b["ts"]: b["close"] for b in bars_1h}
        self.fallbacks = 0

    def price(self, ts: int) -> float | None:
        if ts in self.open_by_ts:
            return self.open_by_ts[ts]
        i = bisect.bisect_right(self.ts_sorted, ts) - 1
        if i < 0:
            return None
        self.fallbacks += 1
        return self.close_by_ts[self.ts_sorted[i]]


def run_book(target: list[int], eth_h4: list[dict], funding: list[dict],
             tier: float, px_settle: PriceAtSettlement) -> dict:
    """Run one book on the ETH H4 grid. target[i] = desired position sign
    from bar i's OPEN (already one-bar-shifted by the caller)."""
    fee = FEE_BPS * 1e-4 * tier
    tick = TICK * tier
    folds = {name: {"net": 0.0, "gross": 0.0, "fees": 0.0, "funding": 0.0,
                    "trades": 0, "fills": 0, "funding_events": 0}
             for name, _, _ in FOLDS}
    f_idx = 0
    pos, qty = 0, 0.0
    entry_px = entry_raw = 0.0
    entry_ts = 0
    fills_total = 0
    raw_px_sum = 0.0  # sum of raw fill prices (both legs) for G7 arithmetic

    def settle(upto_ts: int, fold: str) -> None:
        """Account cashflow for settlement rows in [entry_ts, upto_ts)
        while a position is open; rows before entry are consumed free."""
        nonlocal f_idx
        while f_idx < len(funding) and funding[f_idx]["ts"] < upto_ts:
            r = funding[f_idx]
            f_idx += 1
            if pos == 0 or r["ts"] < entry_ts:
                continue
            px = px_settle.price(r["ts"])
            if px is None:
                continue
            cf = -pos * qty * px * r["rate"]  # longs pay positive funding
            folds[fold]["funding"] += cf
            folds[fold]["net"] += cf
            folds[fold]["funding_events"] += 1

    def close(px_raw: float, fold: str) -> None:
        nonlocal pos, qty, fills_total, raw_px_sum
        if pos == 0:
            return
        exit_eff = px_raw - tick if pos == 1 else px_raw + tick
        gross = qty * (exit_eff - entry_px) if pos == 1 else qty * (entry_px - exit_eff)
        fees = qty * entry_raw * fee + qty * px_raw * fee
        folds[fold]["gross"] += gross
        folds[fold]["fees"] += fees
        folds[fold]["net"] += gross - fees
        folds[fold]["trades"] += 1
        folds[fold]["fills"] += 1
        fills_total += 1
        raw_px_sum += px_raw
        pos, qty = 0, 0.0

    def open_(sign: int, px_raw: float, ts: int, fold: str) -> None:
        nonlocal pos, qty, entry_px, entry_raw, entry_ts, fills_total, raw_px_sum
        pos, qty = sign, NOTIONAL / px_raw
        entry_raw = px_raw
        entry_px = px_raw + tick if sign == 1 else px_raw - tick
        entry_ts = ts
        fills_total += 1
        raw_px_sum += px_raw
        folds[fold]["fills"] += 1

    for i, bar in enumerate(eth_h4):
        fold = fold_of(bar["ts"])
        if fold is None:
            continue  # outside scored folds: no fills, no funding accounting
        desired = target[i]
        if desired != pos:
            if pos != 0:
                close(bar["open"], fold)
            if desired != 0:
                open_(desired, bar["open"], bar["ts"], fold)
        settle(bar["ts"] + H4_MS, fold)
        nxt = eth_h4[i + 1]["ts"] if i + 1 < len(eth_h4) else None
        if nxt is None or fold_of(nxt) != fold:
            close(bar["close"], fold)  # fold-end boundary law

    total_net = sum(f["net"] for f in folds.values())
    return {"folds": folds, "fills_total": fills_total,
            "settlement_price_fallbacks": px_settle.fallbacks,
            "net_total": total_net,
            "avg_raw_fill_px": (raw_px_sum / fills_total) if fills_total else None}


# ---------------------------------------------------------------- arms

ARMS = {
    "EOS1-E1-A1": ("E1", "BTC SMA200(H4) state -> ETH long/flat"),
    "EOS1-E1-A2": ("E1", "BTC SMA100(H4) state -> ETH long/flat"),
    "EOS1-E1-A3": ("E1", "BTC 180-H4-bar (30d) momentum sign -> ETH long/flat"),
    "EOS1-E1-A4": ("E1", "A1 AND ETH SMA200(H4) state (combo)"),
    "EOS1-E2-B1": ("E2", "ETHBTC > SMA600(H4) (~100d) -> ETH long/flat"),
    "EOS1-E2-B2": ("E2", "ETHBTC > SMA1200(H4) (~200d) -> ETH long/flat"),
    "EOS1-E2-B3": ("E2", "ETHBTC 540-H4 (90d) pct-rank > 0.50 -> ETH long/flat"),
    "EOS1-E2-B4": ("E2", "B1 AND BTC SMA200(H4) state (combo)"),
}


def build_all_series() -> dict:
    eth1h, btc1h, ratio1h = (load_1h(SERIES_ETHUSDT), load_1h(SERIES_BTCUSDT),
                             load_1h(SERIES_ETHBTC))
    funding = load_funding()
    eth_h4, eth_drop = to_h4(eth1h)
    btc_h4, btc_drop = to_h4(btc1h)
    ratio_h4, ratio_drop = to_h4(ratio1h)
    return {"eth1h": eth1h, "eth_h4": eth_h4, "btc_h4": btc_h4,
            "ratio_h4": ratio_h4, "funding": funding,
            "px_settle": PriceAtSettlement(eth1h),
            "h4_dropped": {"eth": eth_drop, "btc": btc_drop, "ratio": ratio_drop}}


def build_targets(data: dict) -> dict[str, list[int]]:
    """Desired-position series on the ETH H4 grid, one-bar-shifted so
    target[i] acts from bar i's open (decision at bar i-1 close)."""
    eth = data["eth_h4"]
    btc_closes = [b["close"] for b in data["btc_h4"]]
    ratio_closes = [b["close"] for b in data["ratio_h4"]]
    eth_closes = [b["close"] for b in eth]

    btc_sma200 = InfoSeries(data["btc_h4"], sma_states(btc_closes, 200))
    btc_sma100 = InfoSeries(data["btc_h4"], sma_states(btc_closes, 100))
    btc_sign180 = InfoSeries(data["btc_h4"], sign_states(btc_closes, 180))
    ratio_sma600 = InfoSeries(data["ratio_h4"], sma_states(ratio_closes, 600))
    ratio_sma1200 = InfoSeries(data["ratio_h4"], sma_states(ratio_closes, 1200))
    ratio_pctrank = InfoSeries(data["ratio_h4"], pct_rank_states(ratio_closes, 540))
    eth_sma200 = InfoSeries(eth, sma_states(eth_closes, 200))

    def shift(raw: list[int]) -> list[int]:
        return [0] + raw[:-1]

    def read1(series: InfoSeries) -> list[int]:
        return [series.state_at(b["ts"]) or 0 for b in eth]

    def read2(a: InfoSeries, b: InfoSeries) -> list[int]:
        out = []
        for bar in eth:
            va, vb = a.state_at(bar["ts"]), b.state_at(bar["ts"])
            out.append(1 if (va == 1 and vb == 1) else 0)
        return out

    t: dict[str, list[int]] = {}
    raw: dict[str, list[int]] = {
        "EOS1-E1-A1": read1(btc_sma200),
        "EOS1-E1-A2": read1(btc_sma100),
        "EOS1-E1-A3": read1(btc_sign180),
        "EOS1-E1-A4": read2(btc_sma200, eth_sma200),
        "EOS1-E2-B1": read1(ratio_sma600),
        "EOS1-E2-B2": read1(ratio_sma1200),
        "EOS1-E2-B3": read1(ratio_pctrank),
        "EOS1-E2-B4": read2(ratio_sma600, btc_sma200),
    }
    for arm in ARMS:
        t[arm] = shift(raw[arm])
        t[f"{arm}|G6-SHUF"] = shift(
            shuffle_blocks(raw[arm], BLOCK_SHUFFLE_BARS, f"eos1|{arm}|shuffle"))
        t[f"{arm}|G6-INV"] = [-v for v in t[arm]]

    trend_raw = read1(eth_sma200)
    t["BASE_CASH"] = [0] * len(eth)
    t["BASE_ALWAYS_ON_LONG"] = [1] * len(eth)
    t["REF_SHORT_ALWAYS"] = [-1] * len(eth)
    t["BASE_TREND_LF"] = shift(trend_raw)

    data["_reads_fallback"] = {
        "btc_sma200": btc_sma200.fallback_reads,
        "btc_sma100": btc_sma100.fallback_reads,
        "btc_sign180": btc_sign180.fallback_reads,
        "ratio_sma600": ratio_sma600.fallback_reads,
        "ratio_sma1200": ratio_sma1200.fallback_reads,
        "ratio_pctrank": ratio_pctrank.fallback_reads,
        "eth_sma200": eth_sma200.fallback_reads,
    }
    data["_raw_states"] = raw
    data["_trend_raw"] = trend_raw
    return t
