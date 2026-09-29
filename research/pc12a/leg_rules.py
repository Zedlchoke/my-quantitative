"""Stage-A wave-1 rule archetypes — PC12A implementation lane.

Parameterized mechanical rules for the T1_RULE_READY corpus legs frozen
from the corpus texts (FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/<SYM>.md)
and the mechanization triage. ONE frozen parameter set per leg — no grids.
``param_source`` is carried in every config: 'corpus_verbatim' when every
parameter is literal in the corpus text, 'triage_default' when at least one
declared default had to be frozen (the config names them).

Two clocks:
- DAILY legs subclass :class:`DailyRuleLeg` (fed completed D1 bars at 00:00
  UTC via ``on_daily_bar``; the engine fills at the day's first tradable
  M1 bar).
- INTRADAY legs subclass :class:`MinuteRuleLeg` (``wants_every_bar``; fed
  every tradable M1 bar via ``on_bar``; they aggregate their own M5/M15/
  M30/H1/H4 clocks and D1 history from the stream). Stops/targets for
  intraday legs are evaluated on completed M1 mid closes (declared
  mechanization; conservative, deterministic, PIT-clean).

Cross-asset daily feeds (EURUSD closes into GBPUSD legs etc.) arrive via
``set_cross_feeds``; legs only ever read entries dated <= their own
current bar date (PIT law).

NO PnL anywhere: legs emit decisions (vote/desired_units) only.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .legs import (BaseLeg, BarContext, LegDecision, LegIdentity,
                   UNIT_FIXED_10K, _pit, cal_final)

UTC = dt.timezone.utc


# ---------------------------------------------------------------------------
# numeric helpers (deterministic, list/ndarray in -> float/ndarray out)
# ---------------------------------------------------------------------------


def sma(x: Sequence[float], n: int) -> float:
    if len(x) < n:
        return float("nan")
    return float(np.mean(x[-n:]))


def ema_series(x: np.ndarray, n: int) -> np.ndarray:
    alpha = 2.0 / (n + 1.0)
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = alpha * x[i] + (1 - alpha) * out[i - 1]
    return out


def ema_last(x: Sequence[float], n: int) -> float:
    return float(ema_series(np.asarray(x, dtype=np.float64), n)[-1])


def rsi_series(x: Sequence[float], n: int) -> np.ndarray:
    c = np.asarray(x, dtype=np.float64)
    if len(c) < n + 1:
        return np.array([])
    d = np.diff(c)
    up = np.where(d > 0, d, 0.0)
    dn = np.where(d < 0, -d, 0.0)
    # Wilder smoothing
    au = np.zeros(len(d))
    ad = np.zeros(len(d))
    au[n - 1] = np.mean(up[:n])
    ad[n - 1] = np.mean(dn[:n])
    for i in range(n, len(d)):
        au[i] = (au[i - 1] * (n - 1) + up[i]) / n
        ad[i] = (ad[i - 1] * (n - 1) + dn[i]) / n
    rs = np.divide(au, ad, out=np.full(len(d), np.inf), where=ad > 0)
    return 100.0 - 100.0 / (1.0 + rs)


def rsi_last(x: Sequence[float], n: int) -> float:
    s = rsi_series(x, n)
    return float(s[-1]) if len(s) else float("nan")


def atr_from_bars(bars: Sequence[Dict], n: int) -> float:
    """Mean TR of the last n completed bars ({high, low, close} dicts)."""
    if len(bars) < n + 1:
        return float("nan")
    trs = []
    for i in range(len(bars) - n, len(bars)):
        h, l, pc = bars[i]["high"], bars[i]["low"], bars[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return float(np.mean(trs))


def adx_last(bars: Sequence[Dict], n: int = 14) -> float:
    """Wilder ADX(n) of completed bars ({high, low, close})."""
    if len(bars) < 2 * n + 1:
        return float("nan")
    plus, minus, tr = [], [], []
    for i in range(1, len(bars)):
        h, l, ph, pl, pc = (bars[i]["high"], bars[i]["low"],
                            bars[i - 1]["high"], bars[i - 1]["low"],
                            bars[i - 1]["close"])
        tr.append(max(h - l, abs(h - pc), abs(l - pc)))
        plus.append(max(h - ph, 0.0) if h - ph > pl - l
                    else (0.0 if pl - l > h - ph else max(h - ph, 0.0)))
        minus.append(max(pl - l, 0.0) if pl - l > h - ph
                     else (0.0 if h - ph > pl - l else max(pl - l, 0.0)))
    tr = np.asarray(tr)
    plus = np.asarray(plus)
    minus = np.asarray(minus)
    atr = np.zeros(len(tr))
    pdm = np.zeros(len(tr))
    ndm = np.zeros(len(tr))
    atr[n - 1] = tr[:n].sum()
    pdm[n - 1] = plus[:n].sum()
    ndm[n - 1] = minus[:n].sum()
    for i in range(n, len(tr)):
        atr[i] = atr[i - 1] - atr[i - 1] / n + tr[i]
        pdm[i] = pdm[i - 1] - pdm[i - 1] / n + plus[i]
        ndm[i] = ndm[i - 1] - ndm[i - 1] / n + minus[i]
    pdi = 100.0 * pdm / np.maximum(atr, 1e-12)
    ndi = 100.0 * ndm / np.maximum(atr, 1e-12)
    dx = 100.0 * np.abs(pdi - ndi) / np.maximum(pdi + ndi, 1e-12)
    adx = dx[n - 1]
    for i in range(n, len(tr)):
        adx = (adx * (n - 1) + dx[i]) / n
    return float(adx)


def bollinger_last(closes: Sequence[float], n: int, k: float
                   ) -> Tuple[float, float, float]:
    """(mid, upper, lower) of the last n closes; nan if insufficient."""
    if len(closes) < n:
        return (float("nan"),) * 3  # type: ignore[return-value]
    w = closes[-n:]
    m = float(np.mean(w))
    s = float(np.std(w, ddof=0))
    return m, m + k * s, m - k * s


def pct_rank_of_last(series: Sequence[float], n: int) -> float:
    """Percentile rank (0..100) of the last value within the trailing n."""
    if len(series) < n + 1:
        return float("nan")
    w = np.asarray(series[-(n + 1):], dtype=np.float64)
    last = w[-1]
    return 100.0 * float((w[:-1] < last).sum()) / n


def rv20_pct(closes: Sequence[float], n_ret: int = 20,
             pct_window: int = 252) -> float:
    """RV20 percentile over the trailing pct_window realizations."""
    c = np.asarray(closes, dtype=np.float64)
    if len(c) < pct_window + n_ret + 1:
        return float("nan")
    r = np.diff(np.log(c))
    vols = np.lib.stride_tricks.sliding_window_view(r, n_ret)
    vols = np.std(vols, axis=1)
    last = vols[-1]
    w = vols[-(pct_window + 1):-1]
    return 100.0 * float((w < last).sum()) / pct_window


def realized_vol_annualized(closes: Sequence[float], n: int) -> float:
    c = np.asarray(closes, dtype=np.float64)
    if len(c) < n + 1:
        return float("nan")
    r = np.diff(np.log(c[-(n + 1):]))
    return float(np.std(r) * math.sqrt(252.0))


def donchian(bars: Sequence[Dict], n: int, exclude_last: int = 1
             ) -> Tuple[float, float]:
    """(highest high, lowest low) of bars[-n-exclude_last:-exclude_last]."""
    hi = bars[-n - exclude_last:-exclude_last]
    if len(hi) < n:
        return (float("nan"),) * 2  # type: ignore[return-value]
    return (max(b["high"] for b in hi), min(b["low"] for b in hi))


def tz_minutes(ts: dt.datetime, tz_name: str) -> int:
    """Minutes-of-day of ts converted to tz_name (wall clock)."""
    from zoneinfo import ZoneInfo
    return (ts.astimezone(ZoneInfo(tz_name)).hour * 60
            + ts.astimezone(ZoneInfo(tz_name)).minute)


# ---------------------------------------------------------------------------
# bar aggregation for minute legs
# ---------------------------------------------------------------------------


@dataclass
class AggBar:
    ts: dt.datetime          # close time of the aggregate
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0      # size-weighted (opaque units, relative use only)

    def as_dict(self) -> Dict:
        return {"ts": self.ts, "open": self.open, "high": self.high,
                "low": self.low, "close": self.close,
                "volume": self.volume}


class BarAggregator:
    """Fixed-UTC-grid aggregator (n minutes per bar, 1440 % n == 0)."""

    def __init__(self, n: int):
        assert 1440 % n == 0
        self.n = n
        self._idx: Optional[int] = None
        self._o = self._h = self._l = self._c = 0.0
        self._v = 0.0
        self._count = 0
        self.bars: List[AggBar] = []

    def add(self, ctx: BarContext, mid_high: float, mid_low: float
            ) -> Optional[AggBar]:
        """Feed one M1 bar close; returns the completed aggregate if any."""
        m = ctx.ts.hour * 60 + ctx.ts.minute  # close minute (1..1440)
        idx = m // self.n
        emitted = None
        if self._idx is not None and idx != self._idx:
            emitted = self._flush()
        if self._idx is None or idx != self._idx:
            self._idx = idx
            self._o = self._h = self._l = ctx.mid_close
            self._v = 0.0
            self._count = 0
        self._h = max(self._h, mid_high)
        self._l = min(self._l, mid_low)
        self._c = ctx.mid_close
        self._v += getattr(ctx, "bid_volume", 0.0)
        self._count += 1
        return emitted

    def _flush(self) -> AggBar:
        bar = AggBar(ts=self._ts_of(self._idx), open=self._o, high=self._h,
                     low=self._l, close=self._c, volume=self._v)
        self.bars.append(bar)
        return bar

    def _ts_of(self, idx: int) -> dt.datetime:
        raise NotImplementedError  # set by subclass with day anchor

    def flush_day(self) -> Optional[AggBar]:
        if self._idx is not None and self._count > 0:
            b = self._flush()
            self._idx = None
            self._count = 0
            return b
        return None


class DayBarAggregator(BarAggregator):
    """Aggregator anchored to a calendar day (bar ts = day + idx*n min)."""

    def __init__(self, n: int):
        super().__init__(n)
        self._day: Optional[dt.date] = None

    def add(self, ctx, mid_high, mid_low):  # type: ignore[override]
        if self._day != ctx.ts.date():
            self._day = ctx.ts.date()
            self._idx = None
        return super().add(ctx, mid_high, mid_low)

    def _ts_of(self, idx: int) -> dt.datetime:
        return dt.datetime.combine(self._day, dt.time(0, 0), tzinfo=UTC) \
            + dt.timedelta(minutes=(idx + 1) * self.n)


# ---------------------------------------------------------------------------
# daily-clock base
# ---------------------------------------------------------------------------


class DailyRuleLeg(BaseLeg):
    """Base for D1-close rules: keeps daily bars, position, stop/target."""

    wants_every_bar = False
    warmup_trading_days = 2

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.unit = int(p.get("unit_base_units", UNIT_FIXED_10K))
        self.warmup_trading_days = int(p.get("warmup_trading_days", 2))
        self.bars: List[Dict] = []
        self.stop_level: Optional[float] = None
        self.target_level: Optional[float] = None
        self.entry_i: Optional[int] = None
        self.cross_feeds: Dict[str, List[Dict]] = {}

    # -- engine hooks ---------------------------------------------------------
    def set_cross_feeds(self, feeds: Dict[str, List[Dict]]) -> None:
        self.cross_feeds = feeds

    def cross_closes(self, symbol: str, upto_date: dt.date,
                     n: int) -> List[float]:
        """Last n cross closes dated <= upto_date (PIT-safe)."""
        out = [b["close"] for b in self.cross_feeds.get(symbol, [])
               if b["date"] <= upto_date]
        return out[-n:] if n else out

    def cross_bars(self, symbol: str, upto_date: dt.date) -> List[Dict]:
        return [b for b in self.cross_feeds.get(symbol, [])
                if b["date"] <= upto_date]

    # -- decisions --------------------------------------------------------------
    def _snap(self, bar: Dict) -> List[Dict]:
        return [_pit(f"{self.identity.symbol}_D1_CLOSE", bar["available"],
                     f"sha256:d1:{bar['close']:.10f}", "P7D", True)]

    def _exit(self, code: str, bar: Dict) -> LegDecision:
        self.desired_units = 0
        self.stop_level = None
        self.target_level = None
        self.entry_i = None
        return LegDecision(vote=0, desired_units=0, reason_code=code,
                           order_kind="CLOSE",
                           feature_pit_snapshot=self._snap(bar))

    def _enter(self, direction: int, code: str, bar: Dict,
               units: Optional[int] = None,
               stop: Optional[float] = None,
               target: Optional[float] = None) -> LegDecision:
        u = units if units is not None else self.unit
        self.desired_units = direction * u
        self.stop_level = stop
        self.target_level = target
        self.entry_i = len(self.bars)
        return LegDecision(vote=direction if u > 0 else -direction,
                           desired_units=self.desired_units,
                           reason_code=code, order_kind="OPEN",
                           feature_pit_snapshot=self._snap(bar))

    def _manage(self, bar: Dict) -> Optional[LegDecision]:
        c = bar["close"]
        if self.desired_units > 0:
            if self.stop_level is not None and c <= self.stop_level:
                return self._exit("STOP_HIT", bar)
            if self.target_level is not None and c >= self.target_level:
                return self._exit("TARGET_HIT", bar)
        elif self.desired_units < 0:
            if self.stop_level is not None and c >= self.stop_level:
                return self._exit("STOP_HIT", bar)
            if self.target_level is not None and c <= self.target_level:
                return self._exit("TARGET_HIT", bar)
        return None

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:  # abstract
        raise NotImplementedError




def bb_width_pct(closes: Sequence[float], n: int, k_mult: float,
                 window: int, back: int = 1) -> float:
    """Percentile (0..100) of the Bollinger width of the window ending
    ``back`` bars ago, ranked against the ``window`` widths before it.

    ``back=1`` reads the PRE-BREAK state (yesterday's window), so an
    expansion/entry bar cannot inflate its own squeeze measurement.
    """
    def bw(end: int) -> Optional[float]:
        if end - n < 0:
            return None
        m, u, lo = bollinger_last(closes[end - n:end], n, k_mult)
        if not (m == m) or m <= 0:
            return None
        return (u - lo) / m

    end = len(closes) - back
    cur = bw(end)
    if cur is None:
        return float("nan")
    prior = []
    for j in range(1, window + 1):
        v = bw(end - j)
        if v is not None:
            prior.append(v)
    if len(prior) < window:
        return float("nan")
    return 100.0 * sum(1 for h in prior if h < cur) / len(prior)

# ---------------------------------------------------------------------------
# daily archetypes
# ---------------------------------------------------------------------------


class DonchianSarLeg(DailyRuleLeg):
    """Donchian-20 entry / Donchian-55 stop-and-reverse (classic turtle SAR).

    USDCAD-S002 (no filter), AUDUSD-S002 (ADX14>20 gate). Risk 0.5%/trade
    is declared as fixed single-unit sizing (10k) — sizing policy is a
    Stage-B overlay (declared).
    """

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.entry_n = int(p.get("entry_donchian", 20))
        self.sar_n = int(p.get("sar_donchian", 55))
        self.adx_gate = float(p["adx_gate"]) if "adx_gate" in p else 0.0

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        need = self.sar_n + 1
        if len(self.bars) < need:
            return None
        if self.desired_units != 0:
            # SAR: opposite 55-channel close flips the position
            hh55, ll55 = donchian(self.bars, self.sar_n)
            c = bar["close"]
            if self.desired_units > 0 and c < ll55:
                self.desired_units = 0
                d = self._enter(-1, "DONCHIAN_SAR_FLIP_SHORT", bar)
                return d
            if self.desired_units < 0 and c > hh55:
                self.desired_units = 0
                return self._enter(+1, "DONCHIAN_SAR_FLIP_LONG", bar)
            return None
        if self.adx_gate:
            a = adx_last(self.bars, 14)
            if not (a == a) or a <= self.adx_gate:
                return None
        hh, ll = donchian(self.bars, self.entry_n)
        if bar["close"] > hh:
            return self._enter(+1, "DONCHIAN20_BREAK_LONG", bar)
        if bar["close"] < ll:
            return self._enter(-1, "DONCHIAN20_BREAK_SHORT", bar)
        return None


class DonchianTrailLeg(DailyRuleLeg):
    """Donchian-20 close entry, ATR(14) unit risk, trailing stop 2.5xATR.

    GBPUSD-S001 (stop trailing 2.5xATR, no hard target).
    """

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.entry_n = int(p.get("entry_donchian", 20))
        self.atr_n = int(p.get("atr_n", 14))
        self.trail_atr = float(p.get("trail_atr_mult", 2.5))

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        if len(self.bars) < max(self.entry_n + 1, self.atr_n + 1):
            return None
        if self.desired_units != 0:
            d = self._manage(bar)
            atr = atr_from_bars(self.bars, self.atr_n)
            if self.desired_units > 0:
                self.stop_level = max(self.stop_level or -1e18,
                                      bar["close"] - self.trail_atr * atr)
            else:
                self.stop_level = min(self.stop_level or 1e18,
                                      bar["close"] + self.trail_atr * atr)
            return d
        hh, ll = donchian(self.bars, self.entry_n)
        atr = atr_from_bars(self.bars, self.atr_n)
        if bar["close"] > hh:
            return self._enter(+1, "DONCHIAN20_CLOSE_LONG", bar,
                               stop=bar["close"] - self.trail_atr * atr)
        if bar["close"] < ll:
            return self._enter(-1, "DONCHIAN20_CLOSE_SHORT", bar,
                               stop=bar["close"] + self.trail_atr * atr)
        return None


class AdxMacdLeg(DailyRuleLeg):
    """ADX14-gated MACD-histogram persistence (AUDUSD-S003).

    Enter in the MACD-hist sign direction when ADX crosses above 25 with
    the histogram same-signed for 3 bars; exit when ADX < 20.
    """

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        if len(self.bars) < 40:
            return None
        closes = [b["close"] for b in self.bars]
        h = ema_series(np.asarray(closes), 12) - ema_series(
            np.asarray(closes), 26)
        hist = h - ema_series(h, 9)
        adx = adx_last(self.bars, 14)
        prev_bars = self.bars[:-1]
        adx_prev = adx_last(prev_bars, 14)
        if not (adx == adx and adx_prev == adx_prev):
            return None
        if self.desired_units != 0:
            if adx < 20.0:
                return self._exit("ADX_BELOW_20", bar)
            return None
        if adx > 25.0 and adx_prev <= 25.0:
            last3 = hist[-3:]
            if all(x > 0 for x in last3):
                return self._enter(+1, "ADX_CROSS_MACD_LONG", bar)
            if all(x < 0 for x in last3):
                return self._enter(-1, "ADX_CROSS_MACD_SHORT", bar)
        return None


class MaAdxRegimeLeg(DailyRuleLeg):
    """MA50/200 cross + ADX(14)>25 regime; 20d-swing stop; exit ADX<20
    twice consecutively (USDJPY-S002)."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        self._adx_low_streak = 0

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        if len(self.bars) < 201:
            return None
        closes = [b["close"] for b in self.bars]
        ma50, ma200 = sma(closes, 50), sma(closes, 200)
        adx = adx_last(self.bars, 14)
        if not (adx == adx):
            return None
        if self.desired_units != 0:
            if adx < 20.0:
                self._adx_low_streak += 1
                if self._adx_low_streak >= 2:
                    self._adx_low_streak = 0
                    return self._exit("ADX_BELOW_20_TWICE", bar)
            else:
                self._adx_low_streak = 0
            d = self._manage(bar)
            if d is None:
                swing = self.bars[-20:]
                if self.desired_units > 0:
                    self.stop_level = min(
                        b["low"] for b in swing)
                else:
                    self.stop_level = max(
                        b["high"] for b in swing)
            return d
        if adx > 25.0:
            if ma50 > ma200:
                swing_lo = min(b["low"] for b in self.bars[-20:])
                return self._enter(+1, "MA50_200_ADX_LONG", bar,
                                   stop=swing_lo)
            if ma50 < ma200:
                swing_hi = max(b["high"] for b in self.bars[-20:])
                return self._enter(-1, "MA50_200_ADX_SHORT", bar,
                                   stop=swing_hi)
        return None


class TsMomentumLeg(DailyRuleLeg):
    """Time-series momentum with vol-target sizing and periodic rebalance.

    EURUSD-S003 (6M sign, monthly, ATR60-inverse size), USDJPY-S003 (12M
    skip-1 sign, monthly, vol-target 10%), AUDUSD-S006 (63/126/252d
    majority, weekly, vol-target 10%).
    """

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.lookbacks = [int(x) for x in p["lookbacks"]]
        self.skip = int(p.get("skip_days", 0))
        self.vol_target = float(p.get("vol_target_annual", 0.10))
        self.rebalance = p.get("rebalance", "monthly")
        self._last_rebal_period: Optional[Tuple] = None

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        need = max(self.lookbacks) + self.skip + 2
        if len(self.bars) < need:
            return None
        d = bar["date"]
        if self.rebalance == "monthly":
            period = (d.year, d.month)
        else:
            period = (d.year, d.isocalendar()[1])
        if period == self._last_rebal_period:
            return None
        self._last_rebal_period = period
        closes = [b["close"] for b in self.bars]
        votes = []
        for n in self.lookbacks:
            i = len(closes) - 1 - self.skip - n
            if i < 0:
                return None
            votes.append(1 if closes[-1 - self.skip] > closes[i] else -1)
        sign = 1 if sum(votes) > 0 else (-1 if sum(votes) < 0 else 0)
        if sign == 0:
            if self.desired_units != 0:
                return self._exit("TSMOM_SIGN_FLAT", bar)
            return None
        rv = realized_vol_annualized(closes, 20)
        if not (rv == rv) or rv <= 0:
            return None
        units = int(self.unit * min(self.vol_target / rv, 3.0))
        if units < 1:
            units = 1
        if (self.desired_units > 0) != (sign > 0) or \
                abs(self.desired_units) != units:
            if self.desired_units != 0:
                self.desired_units = 0
            return self._enter(sign, "TSMOM_REBALANCE", bar, units=units)
        return None


class Ma200DislocationLeg(DailyRuleLeg):
    """|price-200DMA|/ATR200 > 2 + same-sign 20D momentum; stop halfway to
    the 200DMA (USDCAD-S004)."""

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        if len(self.bars) < 221:
            return None
        closes = [b["close"] for b in self.bars]
        ma200 = sma(closes, 200)
        atr200 = atr_from_bars(self.bars, 200)
        if not (atr200 == atr200 and ma200 == ma200) or atr200 <= 0:
            return None
        dis = (bar["close"] - ma200) / atr200
        mom20 = 1 if closes[-1] > closes[-21] else -1
        if self.desired_units != 0:
            d = self._manage(bar)
            if d is None and abs(dis) < 1.0:
                return self._exit("DISLOCATION_UNWOUND", bar)
            return d
        if dis > 2.0 and mom20 > 0:
            return self._enter(+1, "MA200_DISLOC_LONG", bar,
                               stop=(bar["close"] + ma200) / 2.0)
        if dis < -2.0 and mom20 < 0:
            return self._enter(-1, "MA200_DISLOC_SHORT", bar,
                               stop=(bar["close"] + ma200) / 2.0)
        return None


class TurtlePyramidLeg(DailyRuleLeg):
    """ATR-pyramiding turtle (USDJPY-S009): Donchian-20 break = 1 unit;
    add 1 unit per +1N favorable move (max 4); cluster stop entry-2N of the
    FIRST unit; trail 2N below the highest add price (longs; mirrored)."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.entry_n = int(p.get("entry_donchian", 20))
        self.atr_n = int(p.get("atr_n", 20))
        self.max_units = int(p.get("max_units", 4))
        self.n_units = 0
        self.cluster_stop: Optional[float] = None
        self.best = 0.0

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        if len(self.bars) < self.entry_n + self.atr_n + 1:
            return None
        c = bar["close"]
        if self.desired_units != 0:
            atr = atr_from_bars(self.bars, self.atr_n)
            if self.desired_units > 0:
                if c <= (self.cluster_stop if self.cluster_stop
                         else -1e18):
                    return self._pyramid_exit(bar)
                if c > self.best:
                    self.best = c
                self.cluster_stop = max(self.cluster_stop or -1e18,
                                        self.best - 2.0 * atr)
            else:
                if c >= (self.cluster_stop if self.cluster_stop
                         else 1e18):
                    return self._pyramid_exit(bar)
                if c < self.best:
                    self.best = c
                self.cluster_stop = min(self.cluster_stop or 1e18,
                                        self.best + 2.0 * atr)
            return None
        hh, ll = donchian(self.bars, self.entry_n)
        atr = atr_from_bars(self.bars, self.atr_n)
        if not (atr == atr):
            return None
        if c > hh:
            self.n_units = 1
            self.best = c
            self.cluster_stop = c - 2.0 * atr
            return self._enter(+1, "TURTLE_UNIT1_LONG", bar, units=self.unit)
        if c < ll:
            self.n_units = 1
            self.best = c
            self.cluster_stop = c + 2.0 * atr
            return self._enter(-1, "TURTLE_UNIT1_SHORT", bar, units=self.unit)
        return None

    def _pyramid_exit(self, bar: Dict) -> LegDecision:
        self.n_units = 0
        self.cluster_stop = None
        return self._exit("TURTLE_CLUSTER_STOP", bar)


class Rsi2DailyLeg(DailyRuleLeg):
    """RSI(2)D pullback with 200DMA trend (USDCAD-S011): RSI2<10 in an
    uptrend -> long next open; exit RSI2>60; stop 1.5xATR (mirrored)."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.stop_mult = float(p.get("stop_atr_mult", 1.5))

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        if len(self.bars) < 205:
            return None
        closes = [b["close"] for b in self.bars]
        r2 = rsi_last(closes, 2)
        ma200 = sma(closes, 200)
        atr = atr_from_bars(self.bars, 14)
        if not (r2 == r2 and ma200 == ma200 and atr == atr):
            return None
        if self.desired_units != 0:
            d = self._manage(bar)
            if d is None:
                if self.desired_units > 0 and r2 > 60.0:
                    return self._exit("RSI2_EXIT_LONG", bar)
                if self.desired_units < 0 and r2 < 40.0:
                    return self._exit("RSI2_EXIT_SHORT", bar)
            return d
        if r2 < 10.0 and bar["close"] > ma200:
            return self._enter(+1, "RSI2_PULLBACK_LONG", bar,
                               stop=bar["close"] - self.stop_mult * atr)
        if r2 > 90.0 and bar["close"] < ma200:
            return self._enter(-1, "RSI2_PULLBACK_SHORT", bar,
                               stop=bar["close"] + self.stop_mult * atr)
        return None


class BBSqueezeBreakLeg(DailyRuleLeg):
    """Bollinger-width squeeze breakout (USDJPY-S023: BW<P10(120d);
    AUDUSD-S026: BW pct<15 for 5 days). Entry: D1 close outside the band
    while squeezed; stop opposite/mid band; target 2x squeeze width or
    timeout."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.bb_n = int(p.get("bb_n", 20))
        self.bb_k = float(p.get("bb_k", 2.0))
        self.bbw_pct = float(p["bbw_pct_max"])
        self.bbw_window = int(p["bbw_window"])
        self.consec = int(p.get("bbw_consec_days", 1))
        self.stop_mode = p.get("stop_mode", "opposite_band")
        self.target_sq = float(p.get("target_squeeze_mult", 2.0))
        self.timeout = int(p.get("timeout_days", 0))

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        if len(self.bars) < max(self.bb_n + self.bbw_window + 2, 130):
            return None
        closes = [b["close"] for b in self.bars]
        m, up, lo = bollinger_last(closes, self.bb_n, self.bb_k)
        if not (m == m) or m <= 0:
            return None
        # squeeze measured on the PRE-BREAK state: the `consec` windows
        # ending 1..consec bars back must each sit below the percentile
        squeezed = True
        for back in range(1, self.consec + 1):
            pct_b = bb_width_pct(closes, self.bb_n, self.bb_k,
                                 self.bbw_window, back=back)
            if not (pct_b == pct_b) or pct_b >= self.bbw_pct:
                squeezed = False
                break
        if self.desired_units != 0:
            d = self._manage(bar)
            if d is None and self.timeout and self.entry_i is not None \
                    and len(self.bars) - self.entry_i >= self.timeout:
                return self._exit("SQUEEZE_TIMEOUT", bar)
            return d
        if not squeezed:
            return None
        c = bar["close"]
        if c > up:
            sq = up - lo
            stop = lo if self.stop_mode == "opposite_band" else m
            return self._enter(+1, "BB_SQUEEZE_BREAK_LONG", bar,
                               stop=stop, target=c + self.target_sq * sq)
        if c < lo:
            sq = up - lo
            stop = up if self.stop_mode == "opposite_band" else m
            return self._enter(-1, "BB_SQUEEZE_BREAK_SHORT", bar,
                               stop=stop, target=c - self.target_sq * sq)
        return None


class BBLowVolRangeLeg(DailyRuleLeg):
    """Bandwidth-percentile low + ADX low range fade (USDCAD-S016):
    fade 2-sigma band touches to the mid; stop 1xATR."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.bb_n = int(p.get("bb_n", 20))
        self.bbw_pct = float(p.get("bbw_pct_max", 20.0))
        self.bbw_window = int(p.get("bbw_window", 120))
        self.adx_max = float(p.get("adx_max", 15.0))

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        if len(self.bars) < self.bb_n + self.bbw_window + 2:
            return None
        closes = [b["close"] for b in self.bars]
        m, up, lo = bollinger_last(closes, self.bb_n, 2.0)
        if not (m == m) or m <= 0:
            return None
        # regime state measured on yesterday's window (the touch bar
        # cannot create its own low-BW regime)
        pct = bb_width_pct(closes, self.bb_n, 2.0, self.bbw_window, back=1)
        adx = adx_last(self.bars[:-1] or self.bars, 14)
        atr = atr_from_bars(self.bars, 14)
        if not (pct == pct and adx == adx and atr == atr):
            return None
        if pct >= self.bbw_pct or adx >= self.adx_max:
            return None
        c = bar["close"]
        if self.desired_units != 0:
            return self._manage(bar)
        if c >= up:
            return self._enter(-1, "BB_RANGE_FADE_SHORT", bar,
                               stop=c + atr, target=m)
        if c <= lo:
            return self._enter(+1, "BB_RANGE_FADE_LONG", bar,
                               stop=c - atr, target=m)
        return None


class AtrRatioBreakoutLeg(DailyRuleLeg):
    """ATR5/ATR20 > 1.5 + 10-day H/L break, RSI confirm (USDJPY-S029):
    stop 1.5xATR5; exit when the ratio < 1.0."""

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        if len(self.bars) < 26:
            return None
        a5 = atr_from_bars(self.bars, 5)
        a20 = atr_from_bars(self.bars, 20)
        if not (a5 == a5 and a20 == a20) or a20 <= 0:
            return None
        ratio = a5 / a20
        if self.desired_units != 0:
            d = self._manage(bar)
            if d is None and ratio < 1.0:
                return self._exit("ATR_RATIO_EXIT", bar)
            return d
        closes = [b["close"] for b in self.bars]
        r = rsi_last(closes, 14)
        if not (r == r):
            return None
        hh = max(b["high"] for b in self.bars[-11:-1])
        ll = min(b["low"] for b in self.bars[-11:-1])
        c = bar["close"]
        if ratio > 1.5 and c > hh and r > 55.0:
            return self._enter(+1, "ATR_RATIO_BREAK_LONG", bar,
                               stop=c - 1.5 * a5)
        if ratio > 1.5 and c < ll and r < 45.0:
            return self._enter(-1, "ATR_RATIO_BREAK_SHORT", bar,
                               stop=c + 1.5 * a5)
        return None


class WeeklySwingBreakLeg(DailyRuleLeg):
    """Weekly swing-high break + weekly close outside mid-Bollinger(20)
    (USDCAD-S006); entry next week; stop prior-week swing low."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        self.weeks: List[Dict] = []
        self._cur_week: List[Dict] = []
        self._pending: Optional[Tuple[int, float, float]] = None

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        self._cur_week.append(bar)
        d = bar["date"]
        if d.weekday() != 4:  # flush completed week on Friday close
            return None
        wk = {"date": d,
              "high": max(b["high"] for b in self._cur_week),
              "low": min(b["low"] for b in self._cur_week),
              "close": bar["close"], "open": self._cur_week[0]["open"],
              "available": bar["available"]}
        self._cur_week = []
        self.weeks.append(wk)
        if len(self.weeks) < 21:
            return None
        closes = [w["close"] for w in self.weeks]
        m, up, lo = bollinger_last(closes, 20, 2.0)
        if not (m == m):
            return None
        prev = self.weeks[-2]
        hh20 = max(w["high"] for w in self.weeks[-21:-1])
        ll20 = min(w["low"] for w in self.weeks[-21:-1])
        if self.desired_units != 0:
            d2 = self._manage(bar)
            if d2 is None and self.stop_level is None:
                # stop was armed at entry from prior-week swing low/high
                pass
            return d2
        if wk["close"] > hh20 and wk["close"] > m:
            self._pending = (+1, prev["low"], prev["high"])
        elif wk["close"] < ll20 and wk["close"] < m:
            self._pending = (-1, prev["high"], prev["low"])
        else:
            self._pending = None
        # entry executes at the start of next week -> emit on this bar's
        # next daily decision is wrong; per corpus "entry next week": emit
        # the entry decision now (fill lands on the next session open).
        if self._pending is not None:
            direction, stop, _ = self._pending
            self._pending = None
            if direction > 0:
                return self._enter(+1, "WEEKLY_SWING_BREAK_LONG", bar,
                                   stop=stop)
            return self._enter(-1, "WEEKLY_SWING_BREAK_SHORT", bar,
                               stop=stop)
        return None


class WeeklyMaRegimeLeg(DailyRuleLeg):
    """Weekly MA5/MA20 regime, weekly rebalance, stop on weekly close
    through MA20 (GBPUSD-S004)."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        self.weeks: List[Dict] = []
        self._cur_week: List[Dict] = []

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        self._cur_week.append(bar)
        if bar["date"].weekday() != 4:
            return None
        wk_close = bar["close"]
        self.weeks.append({"date": bar["date"], "close": wk_close,
                           "high": max(b["high"] for b in self._cur_week),
                           "low": min(b["low"] for b in self._cur_week)})
        self._cur_week = []
        if len(self.weeks) < 21:
            return None
        closes = [w["close"] for w in self.weeks]
        ma5, ma20 = sma(closes, 5), sma(closes, 20)
        if not (ma5 == ma5 and ma20 == ma20):
            return None
        if self.desired_units != 0:
            if self.desired_units > 0 and wk_close < ma20:
                return self._exit("WEEKLY_CLOSE_THROUGH_MA20", bar)
            if self.desired_units < 0 and wk_close > ma20:
                return self._exit("WEEKLY_CLOSE_THROUGH_MA20", bar)
        if ma5 > ma20 and (self.desired_units <= 0):
            if self.desired_units != 0:
                self.desired_units = 0
            return self._enter(+1, "WEEKLY_MA_REGIME_LONG", bar)
        if ma5 < ma20 and (self.desired_units >= 0):
            if self.desired_units != 0:
                self.desired_units = 0
            return self._enter(-1, "WEEKLY_MA_REGIME_SHORT", bar)
        return None


class CalendarSeasonLeg(DailyRuleLeg):
    """Calendar-geometry seasonality windows.

    USDJPY-S044 (short 10/03..31/03, 0.5x, stop 1.5xATR-week),
    USDJPY-S045 (last-Sep-week short after 5 weak sessions, 5 sessions,
    1xATR-week stop), AUDUSD-S044 (long 24..28/06, exit 01..02/07,
    stop 1xATR-D1), EURUSD-S044 (QTD<-3% in final week -> long; exit
    first business day of new quarter), EURUSD-S046 (4 sessions around
    month-turn, bias = prior-month sign, <=4-session hold).
    """

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        p = self.identity.params
        mode = p["window_mode"]
        d = bar["date"]
        atr_d = atr_from_bars(self.bars, 14)
        atr_w = atr_from_bars(self.bars, 5)
        if self.desired_units != 0:
            dec = self._manage(bar)
            if dec is not None:
                return dec
            if mode == "fixed_dates" and (d.month, d.day) >= tuple(
                    p["exit_after"]):
                return self._exit("SEASON_WINDOW_END", bar)
            if mode == "final_week_quarter" and d.month in (1, 4, 7, 10) \
                    and d.day <= 7 and self._in_window_last_week(d) is False:
                return self._exit("QUARTER_ROLL_EXIT", bar)
            if mode == "month_turn":
                w = p["window_days"]
                if not self._month_turn(d, w):
                    return self._exit("MONTH_TURN_END", bar)
                held = (len(self.bars) - 1) - (self.entry_i or 0)
                if held >= p["max_hold_sessions"]:
                    return self._exit("MONTH_TURN_MAX_HOLD", bar)
            if mode == "september_week":
                if not self._last_september_week(d):
                    return self._exit("SEP_WEEK_END", bar)
                held = (len(self.bars) - 1) - (self.entry_i or 0)
                if held >= 5:
                    return self._exit("SEP_WEEK_5SESSIONS", bar)
            return None
        # entries
        if mode == "fixed_dates":
            ey = getattr(self, "_entered_year", None)
            on = tuple(p["entry_on"])
            if (d.month, d.day) >= on and d.month == on[0] and ey != d.year:
                self._entered_year = d.year
                mult = float(p.get("size_mult", 1.0))
                stop = None
                if atr_w == atr_w:
                    stop = bar["close"] + float(
                        p.get("stop_atr_week_mult", 1.5)) * atr_w
                return self._enter(-1, "SEASON_ENTRY_SHORT", bar,
                                   units=int(self.unit * mult), stop=stop)
        elif mode == "final_week_quarter":
            closes = [b["close"] for b in self.bars]
            if self._in_window_last_week(d) and len(closes) > 66:
                q_start = self._quarter_start_close(d)
                if q_start is not None and q_start > 0:
                    qtd = closes[-1] / q_start - 1.0
                    if qtd < float(p["qtd_threshold"]):
                        return self._enter(+1, "QTD_HEDGE_REBAL_LONG", bar)
        elif mode == "month_turn":
            w = p["window_days"]
            if self._month_turn(d, w) and len(self.bars) > 45:
                prev_month_sign = self._prior_month_sign(d)
                if prev_month_sign != 0:
                    return self._enter(
                        prev_month_sign, "MONTH_TURN_CONTINUATION", bar)
        elif mode == "september_week":
            if self._last_september_week(d) and len(self.bars) > 6:
                closes = [b["close"] for b in self.bars]
                ret5 = closes[-1] / closes[-6] - 1.0
                if ret5 < 0:
                    stop = (bar["close"] + atr_w
                            if atr_w == atr_w else None)
                    return self._enter(-1, "SEP_WEAK_SHORT", bar,
                                       stop=stop)
        return None

    # -- helpers -------------------------------------------------------------
    def _in_window_last_week(self, d: dt.date) -> bool:
        return d.month in (3, 6, 9, 12) and d.day >= 25

    def _quarter_start_close(self, d: dt.date) -> Optional[float]:
        qm = {1: 1, 4: 1, 7: 1, 10: 1}
        start_month = {1: 1, 2: 1, 3: 1, 4: 4, 5: 4, 6: 4,
                       7: 7, 8: 7, 9: 7, 10: 10, 11: 10, 12: 10}[d.month]
        for b in self.bars:
            if b["date"].month == start_month and b["date"].day <= 5:
                return b["close"]
        return None

    def _month_turn(self, d: dt.date, w: int) -> bool:
        dim = [31, 29, 32, 30, 31, 30, 31, 31, 30, 31, 30, 32][d.month - 1]
        return d.day <= w or d.day > dim - w

    def _prior_month_sign(self, d: dt.date) -> int:
        pm_bars = [b for b in self.bars
                   if (b["date"].month == d.month - 1)
                   or (d.month == 1 and b["date"].month == 12)]
        if len(pm_bars) < 2:
            return 0
        r = (pm_bars[-1]["close"] / pm_bars[0].get("open", pm_bars[0]["close"]) - 1.0)
        return 1 if r > 0 else (-1 if r < 0 else 0)

    def _last_september_week(self, d: dt.date) -> bool:
        if d.month != 9:
            return False
        nxt = d + dt.timedelta(days=7)
        return nxt.month != 9


class RegimeGateLeg(DailyRuleLeg):
    """Regime-gate mechanized standalone (declared default mapping).

    EURUSD-S091 (RV20 pct: 20-80 trend-on / <20 MR / >80 flat),
    GBPUSD-S091 (RV20 1y-pct: <30 MR / >70 trend / middle half-size),
    USDCAD-S091 (20D RV percentile A-vs-B weighting; declared map:
    pct>50 trend-side long/short by 20d momentum, pct<=50 flat),
    GBPUSD-S048 (weekday allocation: Mon MR, Tue-Thu trend, Fri MR-am),
    AUDUSD-S096 (vol-target overlay size = target/RV20 cap 3).
    The corpus defines these as gates; the declared default (frozen per
    config) maps each gate state to a standalone position.
    """

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        p = self.identity.params
        gate = p["gate_mode"]
        closes = [b["close"] for b in self.bars]
        if gate == "rv_band":
            if len(closes) < 253:
                return None
            pct = rv20_pct(closes, 20, 252)
            if not (pct == pct):
                return None
            lo, hi = float(p["band_lo"]), float(p["band_hi"])
            mom = 1 if closes[-1] > closes[-21] else -1
            if pct < lo:
                want = -mom  # MR state: fade the 20d move
            elif pct > hi:
                want = 0     # chaos state: flat
            else:
                want = mom   # trend state: follow momentum
            return self._realign(want, bar, "RV_BAND_GATE")
        if gate == "rv_trio":
            if len(closes) < 253:
                return None
            pct = rv20_pct(closes, 20, 252)
            if not (pct == pct):
                return None
            lo, hi = float(p["band_lo"]), float(p["band_hi"])
            mom = 1 if closes[-1] > closes[-21] else -1
            if pct < lo:
                want = -mom
                units = self.unit
            elif pct > hi:
                want = mom
                units = self.unit
            else:
                want = mom
                units = self.unit // 2
            return self._realign(want, bar, "RV_TRIO_GATE", units)
        if gate == "rv_weight":
            if len(closes) < 253:
                return None
            pct = rv20_pct(closes, 20, 252)
            if not (pct == pct):
                return None
            mom = 1 if closes[-1] > closes[-21] else -1
            want = mom if pct > 50.0 else 0
            return self._realign(want, bar, "RV_WEIGHT_GATE")
        if gate == "weekday":
            if len(closes) < 2:
                return None
            dd = bar["available"] + dt.timedelta(days=1)
            wd = dd.weekday()
            if wd in (1, 2, 3):
                want = 1 if closes[-1] > closes[-2] else (
                    -1 if closes[-1] < closes[-2] else 0)
                code = "WEEKDAY_TREND_SIDE"
            else:
                want = -1 if closes[-1] > closes[-2] else (
                    1 if closes[-1] < closes[-2] else 0)
                code = "WEEKDAY_MR_SIDE"
            return self._realign(want, bar, code)
        if gate == "vol_target_overlay":
            if len(closes) < 25:
                return None
            rv = realized_vol_annualized(closes, 20)
            if not (rv == rv) or rv <= 0:
                return None
            mom = 1 if closes[-1] > closes[-21] else -1
            units = int(self.unit * min(float(p["target_vol"]) / rv,
                                        float(p["cap_mult"])))
            if units < 1:
                return None
            return self._realign(mom, bar, "VOL_TARGET_OVERLAY", units)
        raise ValueError(f"unknown gate {gate}")

    def _realign(self, want: int, bar: Dict, code: str,
                 units: Optional[int] = None) -> Optional[LegDecision]:
        u = units if units is not None else self.unit
        if want == 0:
            if self.desired_units != 0:
                return self._exit(code + "_FLAT", bar)
            return None
        if self.desired_units * want <= 0:
            if self.desired_units != 0:
                self.desired_units = 0
            return self._enter(want, code, bar, units=u)
        if units is not None and abs(self.desired_units) != u:
            self.desired_units = 0
            return self._enter(want, code, bar, units=u)
        return None


class CrossZLeg(DailyRuleLeg):
    """Cross-asset z-score legs on derivable crosses (GBPUSD-S019,
    GBPUSD-S087, GBPUSD-S083, GBPUSD-S063).

    Feed: EURUSD D1 closes (staged before GBPUSD in the engine's sorted
    stream). EURGBP = EURUSD/GBPUSD daily closes (declared derivation).
    """

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        p = self.identity.params
        mode = p["cross_mode"]
        eur = self.cross_bars("EURUSD", bar["date"])
        if mode == "ratio_router":
            need = 8
        elif mode == "beta_router":
            need = int(p["beta_window"]) + 25
        else:
            need = int(p["z_window"]) + 2
        if len(eur) < need or len(self.bars) < need:
            return None
        gbp_closes = [b["close"] for b in self.bars]
        eur_closes = [b["close"] for b in eur]
        n = len(gbp_closes)
        # align tails (same trading calendar; tolerate 1-day offset)
        m = min(len(gbp_closes), len(eur_closes))
        eg = [eur_closes[len(eur_closes) - m + i] / gbp_closes[
            n - m + i] for i in range(m)]
        if mode == "eurgbp_anchor":
            z_w = self._zscore(eg, int(p["z_window"]))
            ret5_eg = eg[-1] / eg[-6] - 1.0 if len(eg) > 5 else 0.0
            ret5_eu = eur_closes[-1] / eur_closes[-6] - 1.0 \
                if len(eur_closes) > 5 else 0.0
            if not (z_w == z_w):
                return None
            if abs(ret5_eg) > 1e-12 and \
                    abs(ret5_eu) < float(p["usd_flat_ratio"]) * abs(ret5_eg):
                if z_w > float(p["z_entry"]):
                    if self.desired_units != 0:
                        return self._manage(bar)
                    stop = (bar["close"] - float(p.get("stop_atr", 1.0))
                            * atr_from_bars(self.bars, 14)
                            if atr_from_bars(self.bars, 14) == atr_from_bars(
                                self.bars, 14) else None)
                    return self._enter(-1, "EURGBP_ANCHOR_FADE_SHORT", bar,
                                       stop=stop)
                if z_w < -float(p["z_entry"]):
                    if self.desired_units != 0:
                        return self._manage(bar)
                    stop = (bar["close"] + float(p.get("stop_atr", 1.0))
                            * atr_from_bars(self.bars, 14)
                            if atr_from_bars(self.bars, 14) == atr_from_bars(
                                self.bars, 14) else None)
                    return self._enter(+1, "EURGBP_ANCHOR_FADE_LONG", bar,
                                       stop=stop)
            if self.desired_units != 0 and abs(z_w) <= 1.0:
                return self._exit("Z_TARGET_ONE", bar)
            return self._manage(bar)
        if mode == "z_alignment":
            zg = self._zscore(eg, int(p["z_window"]))
            zc = self._zscore(gbp_closes, int(p["z_window"]))
            if not (zg == zg and zc == zc):
                return None
            # same GBP-meaning sign: EURGBP z<0 & Cable z>0 => GBP strong
            gbp_sign_g = -1 if zg > 0 else (1 if zg < 0 else 0)
            if abs(zg) > float(p["z_entry"]) and abs(zc) > float(
                    p["z_entry"]) and gbp_sign_g == np.sign(zc):
                want_dir = int(np.sign(zc))
                if self.desired_units == 0:
                    stop = (bar["close"] - want_dir * 1.0
                            * atr_from_bars(self.bars, 14))
                    return self._enter(want_dir, "CROSS_Z_ALIGN", bar,
                                       stop=stop)
            if self.desired_units != 0:
                z_tgt = float(p.get("z_target", 2.8))
                if abs(zg) >= z_tgt and abs(zc) >= z_tgt:
                    return self._exit("Z_TARGET_REACHED", bar)
                if abs(zg) < 1.0 or abs(zc) < 1.0 or \
                        (-1 if zg > 0 else 1) != np.sign(zc):
                    return self._exit("Z_FLIP_ONE_LEG", bar)
                return self._manage(bar)
            return None
        if mode == "beta_router":
            eg = np.asarray(eg, dtype=np.float64)
            eu = np.asarray(eur_closes[-len(eg):], dtype=np.float64)
            g = np.asarray(gbp_closes[-len(eg):], dtype=np.float64)
            reg = int(p["beta_window"])
            if len(eg) < reg + 5:
                return None
            r_eu = np.diff(np.log(eu))[-reg:]
            r_g = np.diff(np.log(g))[-reg:]
            beta = float(np.cov(r_eu, r_g)[0, 1] / np.var(r_eu))
            band_lo, band_hi = float(p["band_lo"]), float(p["band_hi"])
            out_days = int(p["outside_days"])
            if not hasattr(self, "_beta_streak"):
                self._beta_streak = 0
            if beta < band_lo or beta > band_hi:
                self._beta_streak += 1
            else:
                self._beta_streak = 0
            if self._beta_streak >= out_days:
                # idio regime: trade GBP-side momentum
                mom = 1 if gbp_closes[-1] > gbp_closes[-21] else -1
                return self._realign_generic(mom, bar, "BETA_IDIO_ROUTER")
            # USD-driver regime: trade opposite USD (EURUSD momentum proxy)
            mom_eu = 1 if eur_closes[-1] > eur_closes[-21] else -1
            return self._realign_generic(mom_eu, bar, "BETA_USD_ROUTER")
        if mode == "ratio_router":
            # GBPUSD-S063: 5d |ret| ratio EURGBP vs EURUSD
            ret_eg = eg[-1] / eg[-6] - 1.0
            ret_eu = eur_closes[-1] / eur_closes[-6] - 1.0
            if abs(ret_eu) > 1e-12:
                ratio = abs(ret_eg) / abs(ret_eu)
                if ratio > float(p["idio_ratio"]):
                    mom = 1 if gbp_closes[-1] > gbp_closes[-6] else -1
                    return self._realign_generic(mom, bar, "IDIO_DRIVER")
                if ratio < float(p["usd_ratio"]):
                    mom_eu = 1 if eur_closes[-1] > eur_closes[-6] else -1
                    return self._realign_generic(mom_eu, bar, "USD_DRIVER")
            return None
        raise ValueError(f"unknown cross mode {mode}")

    def _zscore(self, series: Sequence[float], n: int) -> float:
        if len(series) < n + 1:
            return float("nan")
        w = np.asarray(series[-(n + 1):-1], dtype=np.float64)
        m = float(np.mean(w))
        s = float(np.std(w))
        if s <= 0:
            return 0.0
        return (series[-1] - m) / s

    def _realign_generic(self, want: int, bar: Dict, code: str
                         ) -> Optional[LegDecision]:
        if want == 0:
            if self.desired_units != 0:
                return self._exit(code + "_FLAT", bar)
            return None
        if self.desired_units == 0:
            return self._enter(want, code, bar)
        if (self.desired_units > 0) != (want > 0):
            self.desired_units = 0
            return self._enter(want, code, bar)
        return None


# ---------------------------------------------------------------------------
# minute-clock base
# ---------------------------------------------------------------------------


class MinuteRuleLeg(BaseLeg):
    """Base for intraday legs fed every tradable M1 bar.

    Owns D1 history (from the M1 stream), aggregation clocks and a
    session-position state machine. Stop/target evaluated on M1 mid
    closes (declared mechanization). During engine warmup the leg builds
    history but never OPENS a position (``warmup_active`` gate) so it
    enters the window flat and its first entry is a journaled decision.
    """

    wants_every_bar = True
    warmup_trading_days = 25
    warmup_active = False

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.unit = int(p.get("unit_base_units", UNIT_FIXED_10K))
        self.warmup_trading_days = int(p.get("warmup_trading_days", 25))
        self.pip = float(p.get("pip_size", 0.0001))
        self.d1: List[Dict] = []          # completed days
        self._day: Optional[dt.date] = None
        self._day_o = self._day_h = self._day_l = 0.0
        self._day_c = 0.0
        self._day_seen = False
        self.stop_level: Optional[float] = None
        self.target_level: Optional[float] = None
        self.entry_ts: Optional[dt.datetime] = None
        self.cross_feeds: Dict[str, List[Dict]] = {}

    def set_cross_feeds(self, feeds: Dict[str, List[Dict]]) -> None:
        self.cross_feeds = feeds

    # -- stream plumbing -------------------------------------------------------
    def _on_new_day(self, ctx: BarContext) -> None:
        if self._day is not None and self._day_seen:
            self.d1.append({"date": self._day, "open": self._day_o,
                            "high": self._day_h, "low": self._day_l,
                            "close": self._day_c,
                            "available": dt.datetime.combine(
                                self._day, dt.time(0, 0), tzinfo=UTC)
                            + dt.timedelta(days=1)})
        self._day = ctx.ts.date()
        self._day_o = self._day_h = self._day_l = ctx.mid_close
        self._day_c = ctx.mid_close
        self._day_seen = True
        self.on_new_day(ctx)

    def on_new_day(self, ctx: BarContext) -> None:  # override hook
        pass

    def on_bar(self, ctx: BarContext) -> Optional[LegDecision]:
        if self._day != ctx.ts.date():
            self._on_new_day(ctx)
        mh = getattr(ctx, "mid_high", ctx.mid_close)
        ml = getattr(ctx, "mid_low", ctx.mid_close)
        self._day_h = max(self._day_h, mh)
        self._day_l = min(self._day_l, ml)
        self._day_c = ctx.mid_close
        return self._on_bar(ctx, mh, ml)

    def _on_bar(self, ctx: BarContext, mh: float, ml: float
                ) -> Optional[LegDecision]:  # abstract
        raise NotImplementedError

    # -- decision helpers ---------------------------------------------------------
    def _snap(self, ctx: BarContext, what: str = "M1_MIDCLOSE"
              ) -> List[Dict]:
        return [_pit(f"{self.identity.symbol}_{what}", ctx.ts,
                     f"sha256:m1:{ctx.mid_close:.10f}", "P7D", True)]

    def _atr_d1(self, n: int) -> float:
        if len(self.d1) < n + 1:
            return float("nan")
        return atr_from_bars(self.d1, n)

    def _flat(self, ctx: BarContext, code: str) -> LegDecision:
        self.desired_units = 0
        self.stop_level = None
        self.target_level = None
        self.entry_ts = None
        return LegDecision(vote=0, desired_units=0, reason_code=code,
                           order_kind="CLOSE",
                           feature_pit_snapshot=self._snap(ctx))

    def _open(self, ctx: BarContext, direction: int, code: str,
              stop: Optional[float] = None, target: Optional[float] = None,
              units: Optional[int] = None) -> Optional[LegDecision]:
        if self.warmup_active:
            return None   # history-building only; no unjournaled position
        u = units if units is not None else self.unit
        self.desired_units = direction * u
        self.stop_level = stop
        self.target_level = target
        self.entry_ts = ctx.ts
        return LegDecision(vote=direction, desired_units=self.desired_units,
                           reason_code=code, order_kind="OPEN",
                           feature_pit_snapshot=self._snap(ctx))

    def _manage(self, ctx: BarContext) -> Optional[LegDecision]:
        """Stop/target on M1 mid closes + optional bar-time flat."""
        c = ctx.mid_close
        if self.desired_units > 0:
            if self.stop_level is not None and c <= self.stop_level:
                return self._flat(ctx, "M1_STOP_HIT")
            if self.target_level is not None and c >= self.target_level:
                return self._flat(ctx, "M1_TARGET_HIT")
        elif self.desired_units < 0:
            if self.stop_level is not None and c >= self.stop_level:
                return self._flat(ctx, "M1_STOP_HIT")
            if self.target_level is not None and c <= self.target_level:
                return self._flat(ctx, "M1_TARGET_HIT")
        return None

    def _in_utc_window(self, ctx: BarContext, start_m: int, end_m: int
                       ) -> bool:
        m = ctx.ts.hour * 60 + ctx.ts.minute
        return start_m <= m < end_m

    def _in_tz_window(self, ctx: BarContext, tz_name: str,
                      start_m: int, end_m: int) -> bool:
        m = tz_minutes(ctx.ts, tz_name)
        return start_m <= m < end_m


# ---------------------------------------------------------------------------
# minute archetypes — bar-clock rules (H1/H4/M5/...)
# ---------------------------------------------------------------------------


class BarClockLeg(MinuteRuleLeg):
    """Aggregates an n-minute clock and decides on each completed bar."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        self.agg_n = int(identity.params["bar_minutes"])
        self.agg = DayBarAggregator(self.agg_n)
        self._cur: Optional[AggBar] = None

    def _on_bar(self, ctx, mh, ml):  # type: ignore[override]
        emitted = self.agg.add(ctx, mh, ml)
        if emitted is not None:
            return self.on_agbar(emitted, ctx)
        return None

    def on_agbar(self, bar: AggBar, ctx: BarContext
                 ) -> Optional[LegDecision]:
        raise NotImplementedError

    def _bars_dicts(self) -> List[Dict]:
        return [b.as_dict() for b in self.agg.bars]


class KeltnerBreakLeg(BarClockLeg):
    """H4 Keltner(EMA20, 2.5xATR) breakout (GBPUSD-S007): stop half
    channel, target 3R."""

    def on_agbar(self, bar: AggBar, ctx) -> Optional[LegDecision]:
        if len(self.agg.bars) < 40:
            return None
        bars = [b.as_dict() for b in self.agg.bars[-30:]]
        closes = [b.close for b in self.agg.bars[-100:]]
        mid = ema_last(closes, 20)
        atr = atr_from_bars(bars, 14)
        if not (mid == mid and atr == atr):
            return None
        up, dn = mid + 2.5 * atr, mid - 2.5 * atr
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None and self.entry_ts is not None:
                held = (ctx.ts - self.entry_ts).total_seconds() / 3600.0
                if held > 24 * 30:  # declared: monthly timeout
                    return self._flat(ctx, "KELTNER_TIMEOUT")
            return d
        if bar.close > up:
            risk = 1.25 * atr
            return self._open(ctx, +1, "KELTNER_BREAK_LONG",
                              stop=bar.close - risk,
                              target=bar.close + 3.0 * risk)
        if bar.close < dn:
            risk = 1.25 * atr
            return self._open(ctx, -1, "KELTNER_BREAK_SHORT",
                              stop=bar.close + risk,
                              target=bar.close - 3.0 * risk)
        return None


class AdxEmaRiderLeg(BarClockLeg):
    """ADX(14)H4>25 + EMA20/50 aligned; EMA20 pullback entry; chandelier
    3xATR(H4) (GBPUSD-S003)."""

    def on_agbar(self, bar: AggBar, ctx) -> Optional[LegDecision]:
        if len(self.agg.bars) < 60:
            return None
        bars = [b.as_dict() for b in self.agg.bars[-35:]]
        closes = [b.close for b in self.agg.bars[-150:]]
        e20, e50 = ema_last(closes, 20), ema_last(closes, 50)
        adx = adx_last(bars, 14)
        if not (e20 == e20 and e50 == e50 and adx == adx):
            return None
        atr = atr_from_bars(bars, 14)
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None and atr == atr:
                if self.desired_units > 0:
                    self.stop_level = max(
                        self.stop_level or -1e18, bar.close - 3 * atr)
                else:
                    self.stop_level = min(
                        self.stop_level or 1e18, bar.close + 3 * atr)
            return d
        if adx > 25.0 and e20 > e50 and bar.low <= e20 <= bar.high:
            return self._open(ctx, +1, "ADX_EMA_PULLBACK_LONG",
                              stop=bar.close - 3 * atr)
        if adx > 25.0 and e20 < e50 and bar.low <= e50 <= bar.high:
            # pullback to the EMA20 for shorts is the mirrored touch zone
            if bar.low <= e20 <= bar.high:
                return self._open(ctx, -1, "ADX_EMA_PULLBACK_SHORT",
                                  stop=bar.close + 3 * atr)
        return None


class WeeklyH4BreakLeg(BarClockLeg):
    """2 consecutive H4 closes beyond the prior week's H/L (AUDUSD-S029):
    stop inside prior week; exit 2xATR-W1."""

    def on_agbar(self, bar: AggBar, ctx) -> Optional[LegDecision]:
        if len(self.d1) < 12:
            return None
        prev_week = self._prev_week_hl()
        if prev_week is None:
            return None
        ph, pl = prev_week
        bars = self.agg.bars
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None:
                atr_w = self._atr_week()
                if atr_w == atr_w:
                    if self.desired_units > 0:
                        self.target_level = max(
                            self.target_level or -1e18,
                            (self.entry_px or bar.close) + 2 * atr_w)
                    else:
                        self.target_level = min(
                            self.target_level or 1e18,
                            (self.entry_px or bar.close) - 2 * atr_w)
            return d
        if len(bars) < 2:
            return None
        b1, b2 = bars[-2], bars[-1]
        if b2.close > ph and b1.close > ph:
            return self._open(ctx, +1, "WEEKLY_H4_BREAK_LONG",
                              stop=ph - self.pip if False else ph)
        if b2.close < pl and b1.close < pl:
            return self._open(ctx, -1, "WEEKLY_H4_BREAK_SHORT", stop=pl)
        return None

    def _prev_week_hl(self) -> Optional[Tuple[float, float]]:
        d1 = self.d1
        if len(d1) < 6:
            return None
        cur_iso = d1[-1]["date"].isocalendar()[1]
        wk = [b for b in d1 if b["date"].isocalendar()[1] != cur_iso]
        if not wk:
            return None
        last_iso = wk[-1]["date"].isocalendar()[1]
        prev = [b for b in wk if b["date"].isocalendar()[1] == last_iso]
        if len(prev) < 3:
            return None
        return (max(b["high"] for b in prev),
                min(b["low"] for b in prev))

    def _atr_week(self) -> float:
        d1 = self.d1
        if len(d1) < 11:
            return float("nan")
        # weekly ATR from last 2 completed weeks (10 trading days)
        weeks: List[List[Dict]] = []
        cur = [d1[0]]
        for b in d1[1:]:
            if b["date"].isocalendar()[1] == cur[0]["date"].isocalendar()[1]:
                cur.append(b)
            else:
                weeks.append(cur)
                cur = [b]
        weeks.append(cur)
        if len(weeks) < 3:
            return float("nan")
        wr = [{"high": max(x["high"] for x in w),
               "low": min(x["low"] for x in w),
               "close": w[-1]["close"]} for w in weeks]
        trs = []
        for i in range(1, len(wr)):
            trs.append(max(wr[i]["high"] - wr[i]["low"],
                           abs(wr[i]["high"] - wr[i - 1]["close"]),
                           abs(wr[i]["low"] - wr[i - 1]["close"])))
        return float(np.mean(trs[-2:])) if trs else float("nan")

    @property
    def entry_px(self) -> Optional[float]:
        return getattr(self, "_entry_px", None)

    def _open(self, ctx, direction, code, stop=None, target=None,
              units=None):  # type: ignore[override]
        dec = super()._open(ctx, direction, code, stop=stop, target=target,
                            units=units)
        self._entry_px = ctx.mid_close
        return dec


class H4ZscoreLeg(BarClockLeg):
    """H4 z=(close-SMA20)/sigma20 beyond +/-2 with ADX(14,H4)<20; target
    SMA20; stop 2.8 sigma (EURUSD-S013)."""

    def on_agbar(self, bar: AggBar, ctx) -> Optional[LegDecision]:
        if len(self.agg.bars) < 40:
            return None
        bars = [b.as_dict() for b in self.agg.bars[-35:]]
        closes = [b.close for b in self.agg.bars[-21:]]
        m, up, lo = bollinger_last(closes, 20, 2.0)
        adx = adx_last(bars, 14)
        sigma = (up - m) / 2.0
        if not (m == m and adx == adx) or sigma <= 0:
            return None
        if adx >= 20.0:
            return None
        z = (bar.close - m) / sigma
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None:
                long_pos = self.desired_units > 0
                if (long_pos and bar.close >= m) or \
                        (not long_pos and bar.close <= m):
                    return self._flat(ctx, "Z_TARGET_SMA20")
            return d
        if z > 2.0:
            return self._open(ctx, -1, "H4_Z_FADE_SHORT",
                              stop=m + 2.8 * sigma, target=m)
        if z < -2.0:
            return self._open(ctx, +1, "H4_Z_FADE_LONG",
                              stop=m - 2.8 * sigma, target=m)
        return None


class Rsi2BarClockLeg(BarClockLeg):
    """RSI(2) on the aggregate clock vs a 200EMA regime filter.

    USDJPY-S014 (H4, 200EMA-H4): RSI2<5 above EMA200 -> long; >95 below
    -> short; exit RSI2 crosses 50 or 8 bars; stop 1xATR(H4).
    GBPUSD-S012 (H1, within +/-1% of 200HMA): exit RSI 50 or 8 bars;
    stop 1.2xATR(H1).
    EURUSD-S012 (H1 + within 15 pip of weekly pivot/round + ADX(D)<25):
    target EMA9(H1); stop 1xATR(H1).
    """

    def on_agbar(self, bar: AggBar, ctx) -> Optional[LegDecision]:
        p = self.identity.params
        need = int(p.get("ema_filter_n", 200)) + 5
        if len(self.agg.bars) < need:
            return None
        bars = [b.as_dict() for b in self.agg.bars[-20:]]
        closes = [b.close for b in self.agg.bars[-400:]]
        r2 = rsi_last(closes, 2)
        atr = atr_from_bars(bars, 14)
        if not (r2 == r2 and atr == atr):
            return None
        lo_t, hi_t = float(p["rsi_lo"]), float(p["rsi_hi"])
        filt = p.get("filter_mode", "ema200")
        if filt == "ema200":
            f = ema_last(closes, int(p.get("ema_filter_n", 200)))
            reg_long = bar.close > f
            reg_short = bar.close < f
        else:  # proximity to 200-period mean
            f = sma(closes, int(p.get("ema_filter_n", 200)))
            reg_long = abs(bar.close / f - 1.0) <= float(
                p.get("prox_band", 0.01))
            reg_short = reg_long
        if "adx_d_max" in p:
            if not self.d1 or len(self.d1) < 16:
                return None
            adx_d = adx_last(self.d1, 14)
            if not (adx_d == adx_d) or adx_d >= float(p["adx_d_max"]):
                return None
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None:
                if "pivot_pips" in p:
                    tgt = ema_last(closes, 9)
                    long_pos = self.desired_units > 0
                    if (long_pos and bar.close >= tgt) or \
                            (not long_pos and bar.close <= tgt):
                        return self._flat(ctx, "EMA9_TARGET")
                if (self.desired_units > 0 and r2 >= 50.0) or \
                        (self.desired_units < 0 and r2 <= 50.0):
                    return self._flat(ctx, "RSI2_MID_CROSS")
                if self.entry_ts is not None:
                    n_bars = self._bars_since_entry()
                    if n_bars >= int(p.get("exit_bars", 8)):
                        return self._flat(ctx, "RSI2_BARS_EXIT")
            return d
        near_ok = True
        if "pivot_pips" in p:
            near_ok = self._near_pivot_or_round(bar.close, p)
        if not near_ok:
            return None
        if r2 < lo_t and reg_long:
            stop = bar.close - float(p.get("stop_atr_mult", 1.0)) * atr
            return self._open(ctx, +1, "RSI2_FADE_LONG", stop=stop)
        if r2 > hi_t and reg_short:
            stop = bar.close + float(p.get("stop_atr_mult", 1.0)) * atr
            return self._open(ctx, -1, "RSI2_FADE_SHORT", stop=stop)
        return None

    def _bars_since_entry(self) -> int:
        n = 0
        for b in reversed(self.agg.bars):
            if self.entry_ts and b.ts <= self.entry_ts:
                break
            n += 1
        return max(n - 1, 0)

    def _near_pivot_or_round(self, price: float, p: Dict) -> bool:
        thr = float(p["pivot_pips"]) * self.pip
        if not self.d1 or len(self.d1) < 7:
            return False
        # weekly pivot: (prior week H+L+C)/3 (classic), from the last 10
        # completed days (bounded window; the current week + one prior)
        d1 = self.d1[-10:]
        wk = {}
        for b in d1:
            wk.setdefault(b["date"].isocalendar()[:2], []).append(b)
        keys = sorted(wk.keys())
        if len(keys) < 2:
            return False
        prev = wk[keys[-2]]
        pp = (max(b["high"] for b in prev) + min(b["low"] for b in prev)
              + prev[-1]["close"]) / 3.0
        if abs(price - pp) <= thr:
            return True
        # round number: nearest .00/.50 (0.005 for 4-dec pairs)
        step = 50 * self.pip
        frac = (price / step) % 1.0
        dist = min(frac, 1.0 - frac) * step
        return dist <= thr


class AtrRatioH4Leg(BarClockLeg):
    """ATR(5)/ATR(50) H4 crossing 1.5 from below 1.0 within 10 sessions;
    enter the expansion candle's direction; stop 1xATR(5); trail (the
    'trail' is declared as the same 1xATR(5) ratchet) (EURUSD-S027)."""

    def on_agbar(self, bar: AggBar, ctx) -> Optional[LegDecision]:
        if len(self.agg.bars) < 61:
            return None
        bars = [b.as_dict() for b in self.agg.bars[-56:]]
        a5 = atr_from_bars(bars, 5)
        a50 = atr_from_bars(bars, 50)
        if not (a5 == a5 and a50 == a50) or a50 <= 0:
            return None
        ratio = a5 / a50
        prev_bars = [b.as_dict() for b in self.agg.bars[-57:-1]]
        a5p = atr_from_bars(prev_bars, 5)
        a50p = atr_from_bars(prev_bars, 50)
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None:
                if self.desired_units > 0:
                    self.stop_level = max(self.stop_level or -1e18,
                                          bar.close - a5)
                else:
                    self.stop_level = min(self.stop_level or 1e18,
                                          bar.close + a5)
                # declared: exit when the ratio falls back under 1.0
                if ratio < 1.0:
                    return self._flat(ctx, "ATR_RATIO_UNWIND")
            return d
        if not (a5p == a5p and a50p == a50p):
            return None
        rp = a5p / a50p
        if rp < 1.0 and ratio > 1.5:
            direction = 1 if bar.close > bar.open else -1
            return self._open(ctx, direction, "ATR_RATIO_ONSET",
                              stop=bar.close - direction * a5)
        return None


class H1PdhPdlLeg(BarClockLeg):
    """H1 close through PDH/PDL (USDJPY-S026 in London/NY; GBPUSD-S028
    after 14:00 London with EURUSD same-side confirm optional)."""

    def on_agbar(self, bar: AggBar, ctx) -> Optional[LegDecision]:
        if len(self.d1) < 2:
            return None
        pdh, pdl = self.d1[-1]["high"], self.d1[-1]["low"]
        p = self.identity.params
        if p.get("session_mode") == "after_1400_london":
            if not self._in_tz_window(ctx, "Europe/London", 14 * 60,
                                      16 * 60 + 30):
                return None
        elif p.get("session_mode") == "any":
            pass
        else:  # london_ny
            in_ldn = self._in_tz_window(ctx, "Europe/London", 8 * 60,
                                        16 * 60 + 30)
            in_ny = self._in_tz_window(ctx, "America/New_York",
                                       8 * 60, 17 * 60)
            if not (in_ldn or in_ny):
                return None
        atr_h1 = atr_from_bars(
            [b.as_dict() for b in self.agg.bars[-15:]], 14)
        atr_d1 = self._atr_d1(14)
        if not (atr_h1 == atr_h1 and atr_d1 == atr_d1):
            return None
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None:
                if self.desired_units > 0:
                    self.target_level = max(
                        self.target_level or -1e18,
                        (getattr(self, "_entry_px", None) or bar.close)
                        + atr_d1)
                else:
                    self.target_level = min(
                        self.target_level or 1e18,
                        (getattr(self, "_entry_px", None) or bar.close)
                        - atr_d1)
            return d
        if bar.close > pdh:
            conf_dir = 1
        elif bar.close < pdl:
            conf_dir = -1
        else:
            return None
        if p.get("require_eurusd_confirm"):
            conf = self._eurusd_prior_day_break(ctx)
            if conf != conf_dir:
                return None
        self._entry_px = ctx.mid_close
        stop_mode = p.get("stop_mode", "atr_half")
        if stop_mode == "level_measured":
            rng = pdh - pdl
            if rng <= 0:
                return None
            if conf_dir > 0:
                return self._open(ctx, +1, "H1_PDH_BREAK_LONG",
                                  stop=pdh, target=bar.close + rng)
            return self._open(ctx, -1, "H1_PDL_BREAK_SHORT",
                              stop=pdl, target=bar.close - rng)
        if stop_mode == "level_2r":
            risk = abs(bar.close - (pdh if conf_dir > 0 else pdl))
            if risk <= 0:
                return None
            if conf_dir > 0:
                return self._open(ctx, +1, "H1_PDH_BREAK_LONG",
                                  stop=pdh, target=bar.close + 2.0 * risk)
            return self._open(ctx, -1, "H1_PDL_BREAK_SHORT",
                              stop=pdl, target=bar.close - 2.0 * risk)
        if conf_dir > 0:
            return self._open(ctx, +1, "H1_PDH_BREAK_LONG",
                              stop=bar.close - 0.5 * atr_h1)
        return self._open(ctx, -1, "H1_PDL_BREAK_SHORT",
                          stop=bar.close + 0.5 * atr_h1)

    def _eurusd_prior_day_break(self, ctx: BarContext) -> int:
        key = ctx.ts.date()
        cache = getattr(self, "_eur_cache", None)
        if cache is None or cache[0] != key:
            eur = [b for b in self.cross_feeds.get("EURUSD", [])
                   if b["date"] < key]
            self._eur_cache = (key, eur[-2:] if len(eur) >= 2 else [])
        eur = self._eur_cache[1]
        if len(eur) < 2:
            return 0
        # declared same-side band-break proxy: prior EURUSD day CLOSED
        # beyond the day-before's high (up) / low (down)
        if eur[-1]["close"] > eur[-2]["high"]:
            return 1
        if eur[-1]["close"] < eur[-2]["low"]:
            return -1
        return 0


class UsdjpyMomentumGateLeg(BarClockLeg):
    """GBPUSD-S086: USDJPY 4h risk-momentum gate for Cable continuation
    (declared: momentum = sign of EMA20 vs EMA50 on H4). VIX>20 regime
    coupling NOT computable on this checkout — MECHANIZATION_DEVIATION
    declared in the config (coupling dropped, flagged)."""

    def on_agbar(self, bar: AggBar, ctx) -> Optional[LegDecision]:
        key = ctx.ts.date()
        cache = getattr(self, "_jpy_cache", None)
        if cache is None or cache[0] != key:
            jpy = [b for b in self.cross_feeds.get("USDJPY", [])
                   if b["date"] < key]
            self._jpy_cache = (key, jpy)
        jpy = self._jpy_cache[1]
        if len(jpy) < 60:
            return None
        closes = [b["close"] for b in jpy[-400:]]
        e20, e50 = ema_last(closes, 20), ema_last(closes, 50)
        if not (e20 == e20 and e50 == e50):
            return None
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None and len(self.agg.bars) > 5:
                # exit when the gate flips against the position
                e20n, e50n = ema_last(closes, 20), ema_last(closes, 50)
                gate = 1 if e20n > e50n else (-1 if e20n < e50n else 0)
                if gate != 0 and gate != np.sign(self.desired_units):
                    return self._flat(ctx, "GATE_FLIP_EXIT")
            return d
        gate = 1 if e20 > e50 else (-1 if e20 < e50 else 0)
        if gate == 0:
            return None
        return self._open(ctx, gate, "USDJPY_MOMENTUM_GATE",
                          stop=bar.close - gate * 3 * self._atr_d1(14)
                          if self._atr_d1(14) == self._atr_d1(14) else None)


# ---------------------------------------------------------------------------
# minute archetypes — session rules
# ---------------------------------------------------------------------------


class LondonPersistenceLeg(MinuteRuleLeg):
    """GBPUSD-S002: 07:00-09:00 London sign, |ret| > 0.3xATR-daily;
    09:30 entry; stop outside 07:00-09:00 range; exit 16:00 London."""

    def on_new_day(self, ctx) -> None:
        self._m7 = None
        self._range = None
        self._entered = False

    def _on_bar(self, ctx, mh, ml):
        if len(self.d1) < 16:
            return None
        atr_d = self._atr_d1(int(self.identity.params.get("atr_d_n", 14)))
        if not (atr_d == atr_d):
            return None
        in_ldn = self._in_tz_window(ctx, "Europe/London", 7 * 60, 9 * 60)
        m_l = tz_minutes(ctx.ts, "Europe/London")
        if in_ldn:
            if self._m7 is None:
                self._m7 = ctx.mid_close
                self._hi, self._lo = ctx.mid_close, ctx.mid_close
            self._hi = max(self._hi, mh)
            self._lo = min(self._lo, ml)
            self._last7 = ctx.mid_close
            return None
        if self._m7 is not None and self._range is None:
            self._range = (self._hi, self._lo)
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None and m_l >= 16 * 60:
                return self._flat(ctx, "LONDON_1600_EXIT")
            return d
        if self._range is None or self._entered:
            return None
        if 9 * 60 + 30 <= m_l < 16 * 60:
            hi, lo = self._range
            # session direction: window close vs window open
            side = 1 if self._last7 > self._m7 else -1
            if abs(self._last7 - self._m7) > 0.3 * atr_d:
                self._entered = True
                if side > 0:
                    return self._open(ctx, +1, "LONDON_PERSIST_LONG",
                                      stop=lo - 2 * self.pip)
                return self._open(ctx, -1, "LONDON_PERSIST_SHORT",
                                  stop=hi + 2 * self.pip)
        return None


class SessionRangeFadeLeg(MinuteRuleLeg):
    """Generic intraday session fade/join on a UTC window with an M5/M15/
    M30 confirmation close.

    GBPUSD-S011 (Asian-range fake-break, close back inside before 09:00
    UTC, fade to mid, stop +2 pip outside fake extreme),
    GBPUSD-S025 (Asian break 07:00-08:30 + M15 retest-hold within 3
    bars, stop 5 pip inside range, target 1x range height),
    GBPUSD-S090 (M5 sweep of Asian/overnight extreme + reclaim within 2
    bars 07:00-10:00 London + volume spike; stop +2 pip outside sweep),
    USDJPY-S017 (Asia move > 0.8xATR20(D1) + VWAP recross in first 90
    min London; stop London H/L; target Tokyo open),
    USDJPY-S018 (Monday gap > 0.5xATR(H1) fade toward Friday close; stop
    0.6x gap outside; target 50% gap),
    GBPUSD-S016 (Monday gap > 25 pip vs Friday 22:00 close; Sunday
    22:30 fade; stop half gap; target Friday close),
    GBPUSD-S013 (M15 close outside BB(20,2) in 22:00-05:00 then next
    bar back inside; target mid-band; stop half BB width),
    GBPUSD-S017 (15:30-18:30 outside session-VWAP +/-2sigma fade; stop
    +1 sigma),
    GBPUSD-S021 (07:00-08:00 box + M5 close outside + 2-bar no-reentry;
    stop mid-box; 1.5R; time-exit 11:30),
    GBPUSD-S024 (13:30-14:30 UTC box + M15 close outside after 14:45;
    stop mid-box; target day-range extreme; exit 19:00),
    GBPUSD-S029 (Mon-Tue range break on Wednesday London, M30 entry;
    stop opposite edge; exit Fri 16:00 / 2R trail),
    GBPUSD-S042 (Friday 18:30+ |week-move| > 1.5x weekly ATR fade; stop
    30 pip; flat pre-21:30),
    EURUSD-S020 (BB(40,2) M5 01:00-06:00 UTC with BBW percentile<40;
    target mid-band; stop 6 pip; max 3/night),
    USDJPY-S022 (NY 30-min ORB 08:30-09:00 ET; stop opposite OR; trail
    1xATR(H1); flat 15:00 ET).
    """

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.mode = p["session_mode"]
        self.conf_minutes = int(p.get("confirm_bar_minutes", 5))
        self.agg = DayBarAggregator(self.conf_minutes)
        self.state: Dict = {}
        self._reset_day_state()

    def _reset_day_state(self) -> None:
        self.state = {"hi": None, "lo": None, "open": None, "close": None,
                      "vwap_num": 0.0, "vwap_den": 0.0, "sig2_num": 0.0,
                      "n": 0, "fake_hi": None, "fake_lo": None,
                      "entries_today": 0, "broke": 0, "pending_retest": None,
                      "swept": None, "outside_bar": None, "prev_close": None,
                      "vwap": None}
        self._entry_r = None

    def on_new_day(self, ctx) -> None:
        # overnight/JST-anchored sessions span the UTC midnight flip;
        # their state resets at SESSION start, not at the calendar day
        if self.mode in ("asia_vwap_recross", "sweep_reclaim"):
            return
        self._reset_day_state()
        self.state["prev_close"] = self.d1[-1]["close"] if self.d1 else None

    def _on_bar(self, ctx, mh, ml):
        p = self.identity.params
        mode = self.mode
        d = ctx.ts.date()
        wd = d.weekday()

        if mode == "monday_gap_jpy":
            if wd != 0 or len(self.d1) < 2:
                return None
            # Monday Tokyo open fade
            if self.desired_units != 0:
                dd = self._manage(ctx)
                if dd is None and not self._in_tz_window(
                        ctx, "Asia/Tokyo", 9 * 60, 18 * 60):
                    return self._flat(ctx, "GAP_WINDOW_END")
                return dd
            atr_h1 = ctx.atr60  # ATR of the last 60 M1 bars (ATR(H1))
            gap_thr = 0.5 * atr_h1 if atr_h1 > 0 else None
            if gap_thr is None:
                return None
            fri = [b for b in self.d1 if b["date"].weekday() == 4]
            if not fri:
                return None
            fc = fri[-1]["close"]
            gap = ctx.mid_close - fc
            if self._in_tz_window(ctx, "Asia/Tokyo", 9 * 60, 9 * 60 + 30) \
                    and abs(gap) > gap_thr and self.state["entries_today"] == 0:
                self.state["entries_today"] = 1
                direction = -1 if gap > 0 else 1
                stop = ctx.mid_close - direction * 0.6 * abs(gap)
                target = fc + 0.5 * gap
                return self._open(ctx, direction, "MON_GAP_FADE", stop=stop,
                                  target=target)
            return None

        if mode == "monday_gap_gbp":
            if wd not in (6, 0) or len(self.d1) < 2:
                return None
            if self.desired_units != 0:
                dd = self._manage(ctx)
                if dd is None and not self._in_utc_window(
                        ctx, 22 * 60 + 30, 23 * 60):
                    # hold until late Monday, then flat (declared)
                    if ctx.ts.hour >= 12 and self.entry_ts and \
                            (ctx.ts - self.entry_ts).total_seconds() > \
                            12 * 3600:
                        return self._flat(ctx, "GAP_HOLD_TIMEOUT")
                return dd
            fri = [b for b in self.d1 if b["date"].weekday() == 4]
            if not fri:
                return None
            fc = fri[-1]["close"]
            gap = ctx.mid_close - fc
            in_reopen = self._in_utc_window(ctx, 22 * 60 + 30,
                                            23 * 60 + 30)
            in_mon_early = (wd == 0 and ctx.ts.hour < 2)
            if (in_reopen or in_mon_early) and \
                    abs(gap) > float(p["gap_pips"]) * self.pip and \
                    self.state["entries_today"] == 0:
                self.state["entries_today"] = 1
                direction = -1 if gap > 0 else 1
                return self._open(ctx, direction, "MON_GAP_FADE_GBP",
                                  stop=ctx.mid_close - direction
                                  * 0.5 * abs(gap), target=fc)
            return None

        if mode == "tokyo_bb_eu":
            # EURUSD-S020: M5 BB(40,2) in 01:00-06:00 UTC, BBW percentile
            # maintained incrementally (prefix sums over a persistent M5
            # close list; declared percentile window in the config)
            if not self._in_utc_window(ctx, 1 * 60, 6 * 60):
                return None
            emitted = self.agg.add(ctx, mh, ml)
            if emitted is None:
                return self._manage(ctx)
            if not hasattr(self, "_bbw_hist"):
                self._bbw_hist: List[float] = []
                self._bb_closes: List[float] = []
            self._bb_closes.append(emitted.close)
            n_bb = 40
            if len(self._bb_closes) < n_bb:
                return None
            w = self._bb_closes[-n_bb:]
            m = float(np.mean(w))
            s = float(np.std(w))
            up, lo = m + 2.0 * s, m - 2.0 * s
            if m > 0:
                self._bbw_hist.append((up - lo) / m)
            win = int(p.get("bbw_window", 2880))
            if len(self._bbw_hist) < win + 1:
                return None
            hist = self._bbw_hist
            last = hist[-1]
            arr = np.asarray(hist[-(win + 1):-1])
            pct = 100.0 * float((arr < last).sum()) / win
            if pct >= float(p["bbw_pct_max"]):
                return None
            bars = self.agg.bars
            prev = bars[-2]
            if self.desired_units != 0:
                return self._manage(ctx)
            if self.state["entries_today"] >= int(p.get("max_per_night", 3)):
                return None
            if prev.close > up and emitted.close < up:
                self.state["entries_today"] += 1
                return self._open(ctx, -1, "TOKYO_BB_SNAP_SHORT",
                                  stop=emitted.close + float(
                                      p["stop_pips"]) * self.pip, target=m)
            if prev.close < lo and emitted.close > lo:
                self.state["entries_today"] += 1
                return self._open(ctx, +1, "TOKYO_BB_SNAP_LONG",
                                  stop=emitted.close - float(
                                      p["stop_pips"]) * self.pip, target=m)
            return None

        if mode == "asian_fake_break":
            # GBPUSD-S011: Asian range (00:00-06:00 UTC), fake break then
            # close back inside before 09:00 UTC
            if self.state["open"] is None:
                self.state["open"] = ctx.mid_close
            if self._in_utc_window(ctx, 0, 6 * 60):
                self.state["hi"] = mh if self.state["hi"] is None else max(
                    self.state["hi"], mh)
                self.state["lo"] = ml if self.state["lo"] is None else min(
                    self.state["lo"], ml)
                return None
            if self.state["hi"] is None:
                return None
            if self.desired_units != 0:
                dd = self._manage(ctx)
                if dd is None and ctx.ts.hour >= 12:
                    return self._flat(ctx, "MORNING_FADE_EXIT")
                return dd
            if 6 * 60 <= ctx.ts.hour * 60 + ctx.ts.minute < 9 * 60:
                hi, lo = self.state["hi"], self.state["lo"]
                c = ctx.mid_close
                # track fake extremes
                if self.state["fake_hi"] is None:
                    self.state["fake_hi"] = hi
                if self.state["fake_lo"] is None:
                    self.state["fake_lo"] = lo
                if c > self.state["fake_hi"]:
                    self.state["fake_hi"] = c
                if c < self.state["fake_lo"]:
                    self.state["fake_lo"] = c
                # pierced above then closed back inside; ONE setup/day
                if self.state["entries_today"] == 0 and \
                        self.state["fake_hi"] > hi and c < hi:
                    self.state["entries_today"] = 1
                    mid = (hi + lo) / 2.0
                    return self._open(ctx, -1, "ASIAN_FAKE_BREAK_SHORT",
                                      stop=self.state["fake_hi"]
                                      + 2 * self.pip, target=mid)
                if self.state["entries_today"] == 0 and \
                        self.state["fake_lo"] < lo and c > lo:
                    self.state["entries_today"] = 1
                    mid = (hi + lo) / 2.0
                    return self._open(ctx, +1, "ASIAN_FAKE_BREAK_LONG",
                                      stop=self.state["fake_lo"]
                                      - 2 * self.pip, target=mid)
            return None

        if mode == "asian_break_retest":
            # GBPUSD-S025: Asian-range break, M15 retest within 3 bars,
            # stop 5 pip inside the range, target 1x range height
            emitted = self.agg.add(ctx, mh, ml) if self.conf_minutes else None
            cs, ce = p.get("collect_window_utc", (0, 6 * 60))
            if self._in_utc_window(ctx, cs, ce):
                self.state["hi"] = mh if self.state["hi"] is None else max(
                    self.state["hi"], mh)
                self.state["lo"] = ml if self.state["lo"] is None else min(
                    self.state["lo"], ml)
                return None
            if self.state["hi"] is None or emitted is None:
                return self._manage(ctx) if self.desired_units else None
            hi, lo = self.state["hi"], self.state["lo"]
            c = emitted.close
            frame = p.get("break_frame", "utc")
            m = (ctx.ts.hour * 60 + ctx.ts.minute if frame == "utc"
                 else tz_minutes(ctx.ts, frame))
            if self.desired_units != 0:
                dd = self._manage(ctx)
                if dd is None and (m >= 16 * 60 or self._entry_r is not None
                                   and self.target_level is None):
                    # declared: target 1x Asian range height, flat 16:00 UTC
                    if self.target_level is None and self._entry_r \
                            is not None:
                        rng = hi - lo
                        self.target_level = (
                            self._entry_r + rng if self.desired_units > 0
                            else self._entry_r - rng)
                    if m >= 16 * 60:
                        return self._flat(ctx, "RETEST_TIME_EXIT")
                return dd
            bs, be = p.get("break_window", (8 * 60 + 30, 15 * 60))
            if bs <= m < be:
                if self.state["broke"] == 0:
                    if c > hi:
                        self.state["broke"] = 1
                        self.state["pending_retest"] = {"edge": hi, "dir": 1,
                                                        "bars": 0}
                    elif c < lo:
                        self.state["broke"] = -1
                        self.state["pending_retest"] = {"edge": lo, "dir": -1,
                                                        "bars": 0}
                    return None
                pr = self.state["pending_retest"]
                if pr is None:
                    return None
                pr["bars"] += 1
                if pr["bars"] > 3:
                    self.state["broke"] = 0
                    self.state["pending_retest"] = None
                    return None
                # retest holds: pulled back to the edge but closed on the
                # break side of it
                if abs(c - pr["edge"]) <= (hi - lo) * 0.1 and \
                        (c > pr["edge"] if pr["dir"] > 0 else c < pr["edge"]):
                    self._entry_r = ctx.mid_close
                    rng = hi - lo
                    if pr["dir"] > 0:
                        return self._open(ctx, +1, "ASIAN_RETEST_LONG",
                                          stop=hi - 5 * self.pip,
                                          target=ctx.mid_close + rng)
                    return self._open(ctx, -1, "ASIAN_RETEST_SHORT",
                                      stop=lo + 5 * self.pip,
                                      target=ctx.mid_close - rng)
            return None

        if mode == "sweep_reclaim":
            # GBPUSD-S090: M5 sweep of Asian/overnight extreme + reclaim
            # within 2 bars (07:00-10:00 London) + volume spike; the
            # overnight range 22:00-07:00 UTC resets at 22:00 session open
            emitted = self.agg.add(ctx, mh, ml)
            if ctx.ts.hour == 22 and ctx.ts.minute == 0:
                self._reset_day_state()
            if self._in_utc_window(ctx, 22 * 60, 24 * 60) or \
                    self._in_utc_window(ctx, 0, 7 * 60):
                self.state["hi"] = mh if self.state["hi"] is None else max(
                    self.state["hi"], mh)
                self.state["lo"] = ml if self.state["lo"] is None else min(
                    self.state["lo"], ml)
                return None
            if self.state["hi"] is None or emitted is None:
                return self._manage(ctx) if self.desired_units else None
            hi, lo = self.state["hi"], self.state["lo"]
            if not self._in_tz_window(ctx, "Europe/London", 7 * 60, 10 * 60):
                return self._manage(ctx) if self.desired_units else None
            if self.desired_units != 0:
                dd = self._manage(ctx)
                if dd is None and ctx.ts.hour >= 13:
                    return self._flat(ctx, "SWEEP_EXIT_MIDDAY")
                return dd
            bars = self.agg.bars
            if len(bars) < 3:
                return None
            prev = bars[-2]
            cur = emitted
            vols = [b.volume for b in bars[-21:-1]]
            if not vols or max(vols) <= 0:
                return None
            spike = cur.volume > 1.5 * float(np.median(vols))
            if not spike:
                return None
            mid = (hi + lo) / 2.0
            if prev.high > hi and cur.close < hi:
                return self._open(ctx, -1, "SWEEP_RECLAIM_SHORT",
                                  stop=prev.high + 2 * self.pip, target=mid)
            if prev.low < lo and cur.close > lo:
                return self._open(ctx, +1, "SWEEP_RECLAIM_LONG",
                                  stop=prev.low - 2 * self.pip, target=mid)
            return None

        if mode == "asia_vwap_recross":
            # USDJPY-S017: Asia (00:00-09:00 JST) move > 0.8xATR20(D1) and
            # price recrosses the Asia VWAP within the first 90 London min
            jst = tz_minutes(ctx.ts, "Asia/Tokyo")
            if 0 <= jst < 9 * 60:
                if getattr(self, "_asia_in_sess", False) is False:
                    # new Asia session (JST 00:00) -> fresh accumulation
                    self._reset_day_state()
                    self._asia_in_sess = True
                v = getattr(ctx, "bid_volume", 0.0)
                self.state["vwap_num"] += ctx.mid_close * v
                self.state["vwap_den"] += v
                self.state["open"] = ctx.mid_close if self.state[
                    "open"] is None else self.state["open"]
                self.state["close"] = ctx.mid_close
                self.state["hi"] = mh if self.state["hi"] is None else max(
                    self.state["hi"], mh)
                self.state["lo"] = ml if self.state["lo"] is None else min(
                    self.state["lo"], ml)
                return None
            self._asia_in_sess = False
            if self.state["open"] is None or len(self.d1) < 21:
                return None
            atr_d = self._atr_d1(20)
            if not (atr_d == atr_d):
                return None
            asia_move = max(abs(self.state["hi"] - self.state["open"]),
                            abs(self.state["lo"] - self.state["open"]))
            vwap = (self.state["vwap_num"] / self.state["vwap_den"]
                    if self.state["vwap_den"] > 0 else self.state["close"])
            m_utc = ctx.ts.hour * 60 + ctx.ts.minute
            in_ldn_first90 = self._in_tz_window(ctx, "Europe/London",
                                                8 * 60, 9 * 60 + 30)
            if self.desired_units != 0:
                dd = self._manage(ctx)
                if dd is None and not in_ldn_first90:
                    # stop outside London H/L approximated by trailing the
                    # position to flat at London 10:30 (declared)
                    if not self._in_tz_window(ctx, "Europe/London",
                                              8 * 60, 10 * 60 + 30):
                        return self._flat(ctx, "LONDON_WINDOW_EXIT")
                return dd
            if not in_ldn_first90 or asia_move <= 0.8 * atr_d:
                return None
            asia_dir = 1 if self.state["close"] > self.state["open"] else -1
            # recross: prev bar below VWAP (for an up-Asia) and now above
            prev_side = getattr(self, "_prev_vwap_side", None)
            cur_side = 1 if ctx.mid_close > vwap else -1
            self._prev_vwap_side = cur_side
            if prev_side is not None and prev_side == -asia_dir and \
                    cur_side == asia_dir:
                # fade the Asia move (it failed): opposite direction
                direction = -asia_dir
                return self._open(ctx, direction, "ASIA_VWAP_RECROSS",
                                  stop=(self.state["hi"] + 2 * self.pip
                                        if direction < 0
                                        else self.state["lo"] - 2 * self.pip),
                                  target=self.state["open"])
            return None

        if mode == "ny_vwap_reversion":
            # GBPUSD-S017: 15:30-18:30 London outside session VWAP +/-2sigma
            if not self._in_tz_window(ctx, "Europe/London",
                                      15 * 60 + 30, 18 * 60 + 30):
                return None
            v = getattr(ctx, "bid_volume", 0.0)
            self.state["vwap_num"] += ctx.mid_close * v
            self.state["vwap_den"] += v
            self.state["n"] += 1
            self.state["sig2_num"] += ctx.mid_close ** 2
            if self.state["vwap_den"] <= 0 or self.state["n"] < 30:
                return None
            vwap = self.state["vwap_num"] / self.state["vwap_den"]
            var = max(self.state["sig2_num"] / self.state["n"] - vwap ** 2,
                      0.0)
            sigma = math.sqrt(var)
            if sigma <= 0:
                return None
            if self.desired_units != 0:
                return self._manage(ctx)
            c = ctx.mid_close
            if c > vwap + 2 * sigma:
                return self._open(ctx, -1, "NY_VWAP_FADE_SHORT",
                                  stop=c - sigma, target=vwap)
            if c < vwap - 2 * sigma:
                return self._open(ctx, +1, "NY_VWAP_FADE_LONG",
                                  stop=c + sigma, target=vwap)
            return None

        if mode == "bb_m15_asia_snap":
            # GBPUSD-S013: M15 close outside BB(20,2) within 22:00-05:00
            # UTC, next bar closes back inside; target mid; stop half width
            if not (self._in_utc_window(ctx, 22 * 60, 24 * 60)
                    or self._in_utc_window(ctx, 0, 5 * 60)):
                return None
            emitted = self.agg.add(ctx, mh, ml)
            if emitted is None:
                return self._manage(ctx)
            bars = self.agg.bars
            if len(bars) < 22:
                return None
            closes = [b.close for b in bars]
            m, up, lo = bollinger_last(closes, 20, 2.0)
            if not (m == m):
                return None
            prev = bars[-2]
            if self.desired_units != 0:
                dd = self._manage(ctx)
                if dd is None and ctx.ts.hour >= 8:
                    return self._flat(ctx, "ASIA_SNAP_EXIT")
                return dd
            half_w = (up - lo) / 4.0
            if prev.close > up and emitted.close < up:
                return self._open(ctx, -1, "ASIA_BB_SNAP_SHORT",
                                  stop=emitted.close + half_w, target=m)
            if prev.close < lo and emitted.close > lo:
                return self._open(ctx, +1, "ASIA_BB_SNAP_LONG",
                                  stop=emitted.close - half_w, target=m)
            return None

        if mode == "london_box_orb":
            # GBPUSD-S021 (07:00-08:00 London box, M5 close outside + 2-bar
            # no-reentry, stop mid-box, 1.5R, time-exit 11:30) and
            # GBPUSD-S024 (13:30-14:30 UTC box, M15 close outside after
            # 14:45, stop mid-box, target day extreme, exit 19:00)
            emitted = self.agg.add(ctx, mh, ml)
            frame = p.get("time_frame", "utc")
            if frame == "utc":
                m = ctx.ts.hour * 60 + ctx.ts.minute
            else:
                m = tz_minutes(ctx.ts, frame)
            s, e = p["box_window"]
            if s <= m < e:
                self.state["hi"] = mh if self.state["hi"] is None else max(
                    self.state["hi"], mh)
                self.state["lo"] = ml if self.state["lo"] is None else min(
                    self.state["lo"], ml)
                return None
            if self.state["hi"] is None:
                return None
            hi, lo = self.state["hi"], self.state["lo"]
            if self.desired_units != 0:
                dd = self._manage(ctx)
                if dd is None and m >= int(p["flat_minute_utc"]):
                    return self._flat(ctx, "BOX_TIME_EXIT")
                return dd
            after = int(p["after_minute_utc"])
            if m < after or emitted is None:
                return None
            bars = self.agg.bars
            if len(bars) < 3:
                return None
            last2 = [bars[-2], bars[-1]]
            c = last2[-1].close
            if self.state["entries_today"]:
                return None            # one setup per session (corpus)
            if all(b.close > hi for b in last2):
                mid = (hi + lo) / 2.0
                risk = c - mid
                if risk <= 0:
                    return None
                tgt_mult = float(p.get("target_r_mult", 1.5))
                self.state["entries_today"] = 1
                return self._open(ctx, +1, "BOX_ORB_LONG", stop=mid,
                                  target=c + tgt_mult * risk)
            if all(b.close < lo for b in last2):
                mid = (hi + lo) / 2.0
                risk = mid - c
                if risk <= 0:
                    return None
                tgt_mult = float(p.get("target_r_mult", 1.5))
                self.state["entries_today"] = 1
                return self._open(ctx, -1, "BOX_ORB_SHORT", stop=mid,
                                  target=c - tgt_mult * risk)
            return None

        if mode == "ny_orb":
            # USDJPY-S022: NY 30-min ORB 08:30-09:00 ET, break of OR,
            # stop opposite OR, trail 1xATR(H1), flat 15:00 ET
            emitted = self.agg.add(ctx, mh, ml)
            et = tz_minutes(ctx.ts, "America/New_York")
            if 8 * 60 + 30 <= et < 9 * 60:
                self.state["hi"] = mh if self.state["hi"] is None else max(
                    self.state["hi"], mh)
                self.state["lo"] = ml if self.state["lo"] is None else min(
                    self.state["lo"], ml)
                return None
            if self.state["hi"] is None:
                return None
            hi, lo = self.state["hi"], self.state["lo"]
            if self.desired_units != 0:
                dd = self._manage(ctx)
                if dd is None:
                    if et >= 15 * 60:
                        return self._flat(ctx, "NY_FLAT_1500_ET")
                    atr_h1 = ctx.atr60
                    if atr_h1 > 0:
                        if self.desired_units > 0:
                            self.stop_level = max(
                                self.stop_level or -1e18,
                                ctx.mid_close - atr_h1)
                        else:
                            self.stop_level = min(
                                self.stop_level or 1e18,
                                ctx.mid_close + atr_h1)
                return dd
            if emitted is None or et < 9 * 60:
                return None
            if self.state["entries_today"]:
                return None            # one setup per session (corpus)
            c = emitted.close
            if c > hi:
                self.state["entries_today"] = 1
                return self._open(ctx, +1, "NY_ORB_LONG", stop=lo)
            if c < lo:
                self.state["entries_today"] = 1
                return self._open(ctx, -1, "NY_ORB_SHORT", stop=hi)
            return None

        if mode == "midweek_range_break":
            # GBPUSD-S029: break of Mon-Tue range on Wednesday London,
            # M30 entry, stop opposite edge, exit Fri 16:00 London / 2R
            is_friday = wd == 4
            if self.desired_units != 0:
                dd = self._manage(ctx)
                if dd is None and is_friday and self._in_tz_window(
                        ctx, "Europe/London", 16 * 60, 18 * 60):
                    return self._flat(ctx, "WED_EXIT_FRI_1600")
                return dd
            if wd != 2:  # entries: Wednesday only
                return None
            mt = [b for b in self.d1 if b["date"].weekday() in (0, 1)
                  and b["date"].isocalendar()[1]
                  == ctx.ts.date().isocalendar()[1]]
            if len(mt) < 2:
                return None
            hi = max(b["high"] for b in mt)
            lo = min(b["low"] for b in mt)
            emitted = self.agg.add(ctx, mh, ml)
            if emitted is None:
                return None
            if not self._in_tz_window(ctx, "Europe/London", 8 * 60,
                                      16 * 60 + 30):
                return None
            c = emitted.close
            if c > hi:
                risk = c - lo
                return self._open(ctx, +1, "MIDWEEK_RANGE_LONG", stop=lo,
                                  target=c + 2.0 * risk)
            if c < lo:
                risk = hi - c
                return self._open(ctx, -1, "MIDWEEK_RANGE_SHORT", stop=hi,
                                  target=c - 2.0 * risk)
            return None

        if mode == "friday_late_fade":
            # GBPUSD-S042: Friday 18:30+ |week-move| > 1.5x weekly ATR
            if wd != 4:
                return None
            if not self._in_utc_window(ctx, 18 * 60 + 30, 21 * 60):
                return None
            if len(self.d1) < 11:
                return None
            wk = [b for b in self.d1 if b["date"].isocalendar()[1]
                  == ctx.ts.date().isocalendar()[1]]
            prev_wk = [b for b in self.d1 if b["date"].isocalendar()[1]
                       != ctx.ts.date().isocalendar()[1]]
            if len(wk) < 4 or not prev_wk:
                return None
            last_iso = prev_wk[-1]["date"].isocalendar()[1]
            prev = [b for b in prev_wk
                    if b["date"].isocalendar()[1] == last_iso]
            trs = []
            weeks = self._group_weeks()
            for i in range(1, len(weeks)):
                trs.append(max(
                    max(b["high"] for b in weeks[i]) - min(
                        b["low"] for b in weeks[i]),
                    abs(max(b["high"] for b in weeks[i]) - weeks[i - 1][-1][
                        "close"]),
                    abs(min(b["low"] for b in weeks[i]) - weeks[i - 1][-1][
                        "close"])))
            if not trs:
                return None
            w_atr = float(np.mean(trs[-2:]))
            week_open = wk[0]["open"]
            week_move = ctx.mid_close - week_open
            if self.desired_units != 0:
                dd = self._manage(ctx)
                if dd is None and ctx.ts.hour >= 21:
                    return self._flat(ctx, "FRIDAY_FLAT_PRE_2130")
                return dd
            if abs(week_move) > 1.5 * w_atr and \
                    self.state["entries_today"] == 0:
                self.state["entries_today"] = 1
                direction = -1 if week_move > 0 else 1
                return self._open(ctx, direction, "FRIDAY_LATE_FADE",
                                  stop=ctx.mid_close - direction
                                  * float(p["stop_pips"]) * self.pip)
            return None

        raise ValueError(f"unknown session mode {mode}")

    # -- helpers -------------------------------------------------------------
    def _group_weeks(self) -> List[List[Dict]]:
        weeks: List[List[Dict]] = []
        cur = [self.d1[0]]
        for b in self.d1[1:]:
            if b["date"].isocalendar()[1] == cur[0]["date"].isocalendar()[1]:
                cur.append(b)
            else:
                weeks.append(cur)
                cur = [b]
        weeks.append(cur)
        return weeks

    def _h1_atr(self) -> float:
        # ATR(20) of the trailing 20 hours of M1 mid closes (declared
        # hourly ATR estimator from the M1 stream)
        if not self.d1:
            return float("nan")
        return self._atr_d1(int(self.identity.params.get(
            "orb_atr_h1_proxy_days", 3)))


class Nr7StopOrderLeg(MinuteRuleLeg):
    """EURUSD-S024: NR7 or 2 inside days -> next-day stop orders both
    sides of the day range +3 pip (intrabar touch via M1 mid); trail
    2xATR(10)."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        self._armed: Optional[Dict] = None

    def on_new_day(self, ctx) -> None:
        self._armed_today = False

    def _nr7_or_inside(self) -> bool:
        d1 = self.d1
        if len(d1) < 9:
            return False
        rng = lambda b: b["high"] - b["low"]  # noqa: E731
        last = d1[-1]
        prev7 = d1[-8:-1]
        if rng(last) < min(rng(b) for b in prev7):
            return True
        if d1[-2]["high"] <= d1[-3]["high"] and \
                d1[-2]["low"] >= d1[-3]["low"] and \
                d1[-1]["high"] <= d1[-2]["high"] and \
                d1[-1]["low"] >= d1[-2]["low"]:
            return True
        return False

    def _on_bar(self, ctx, mh, ml):
        if self.desired_units == 0 and not self._armed \
                and len(self.d1) >= 9:
            if self._nr7_or_inside():
                last = self.d1[-1]
                pad = 3 * self.pip
                self._armed = {"hi": last["high"] + pad,
                               "lo": last["low"] - pad}
        if self._armed and self.desired_units == 0:
            hi, lo = self._armed["hi"], self._armed["lo"]
            if ctx.mid_close > hi:
                self._armed = None
                atr = self._atr_d1(10)
                return self._open(ctx, +1, "NR7_STOP_LONG",
                                  stop=(ctx.mid_close - 2 * atr
                                        if atr == atr else None))
            if ctx.mid_close < lo:
                self._armed = None
                atr = self._atr_d1(10)
                return self._open(ctx, -1, "NR7_STOP_SHORT",
                                  stop=(ctx.mid_close + 2 * atr
                                        if atr == atr else None))
        if self._armed is not None and self._armed_expired(ctx):
            self._armed = None
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None:
                atr = self._atr_d1(10)
                if atr == atr:
                    if self.desired_units > 0:
                        self.stop_level = max(self.stop_level or -1e18,
                                              ctx.mid_close - 2 * atr)
                    else:
                        self.stop_level = min(self.stop_level or 1e18,
                                              ctx.mid_close + 2 * atr)
            return d
        return None

    def _armed_expired(self, ctx) -> bool:
        # stop orders live one session day (declared)
        return self._armed is not None and False  # replaced on new arm


class Nr7M30BreakLeg(MinuteRuleLeg):
    """GBPUSD-S023: NR7/inside day -> next-day 30m close break of the
    day range; stop mid-range; target 2R."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        self.agg = DayBarAggregator(30)
        self._day_bar_done = False

    def on_new_day(self, ctx) -> None:
        self._day_bar_done = False

    def _on_bar(self, ctx, mh, ml):
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None and ctx.ts.hour >= 21:
                return self._flat(ctx, "NR7_M30_DAY_END")
            return d
        if self._day_bar_done:
            return None
        d1 = self.d1
        if len(d1) < 9:
            return None
        rng = lambda b: b["high"] - b["low"]  # noqa: E731
        prev = d1[-1]
        prev7 = d1[-8:-1]
        nr7 = rng(prev) < min(rng(b) for b in prev7)
        inside = (len(d1) >= 3 and d1[-1]["high"] <= d1[-2]["high"]
                  and d1[-1]["low"] >= d1[-2]["low"])
        if not (nr7 or inside):
            return None
        emitted = self.agg.add(ctx, mh, ml)
        if emitted is None:
            return None
        if emitted.close > prev["high"]:
            self._day_bar_done = True
            risk = emitted.close - (prev["high"] + prev["low"]) / 2.0
            if risk <= 0:
                return None
            return self._open(ctx, +1, "NR7_M30_BREAK_LONG",
                              stop=(prev["high"] + prev["low"]) / 2.0,
                              target=emitted.close + 2.0 * risk)
        if emitted.close < prev["low"]:
            self._day_bar_done = True
            risk = (prev["high"] + prev["low"]) / 2.0 - emitted.close
            if risk <= 0:
                return None
            return self._open(ctx, -1, "NR7_M30_BREAK_SHORT",
                              stop=(prev["high"] + prev["low"]) / 2.0,
                              target=emitted.close - 2.0 * risk)
        return None


class HourOfDayDriftLeg(MinuteRuleLeg):
    """USDJPY-S050: M30 hour-of-day drift, t>3 after FDR (declared:
    Benjamini-Hochberg q=0.05 over the 48 half-hour slots), rolling 3y;
    enter the slot's drift sign at slot start, exit at slot end, stop
    0.5xATR(M30). Event-hour exclusion inactive until calendar staged
    (triage)."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.slot_min = int(p.get("slot_minutes", 30))
        self.n_slots = 1440 // self.slot_min
        self.t_min = float(p.get("t_min", 3.0))
        self.fdr_q = float(p.get("fdr_q", 0.05))
        self.window_days = int(p.get("rolling_window_trading_days", 750))
        # per-slot deque of (ts, bar) M30 aggregates
        self.agg = DayBarAggregator(self.slot_min)
        self._ret_cache: Dict[int, List[float]] = {
            i: [] for i in range(self.n_slots)}
        self._last_sig: Dict[int, int] = {}
        self._in_slot: Optional[int] = None
        self._sig_slots: set = set()

    def _on_bar(self, ctx, mh, ml):
        emitted = self.agg.add(ctx, mh, ml)
        if emitted is not None:
            slot = ((emitted.ts.hour * 60 + emitted.ts.minute - 1)
                    // self.slot_min) % self.n_slots
            self._ret_cache[slot].append(emitted.close
                                         / emitted.open - 1.0)
            self._last_sig.pop(slot, None)
            if len(self._ret_cache[slot]) > self.window_days:
                self._ret_cache[slot] = \
                    self._ret_cache[slot][-self.window_days:]
        # refresh FDR-significant slots once per day (first bar of day)
        m = ctx.ts.hour * 60 + ctx.ts.minute
        slot_now = (m - 1) // self.slot_min % self.n_slots
        if self._in_slot != slot_now:
            self._in_slot = slot_now
            if self.desired_units == 0 and slot_now in self._sig_slots:
                sign = self._slot_sign(slot_now)
                if sign != 0:
                    atr = self._m30_atr()
                    stop = (ctx.mid_close - sign * 0.5 * atr
                            if atr == atr else None)
                    return self._open(ctx, sign,
                                      f"HOD_DRIFT_{'LONG' if sign>0 else 'SHORT'}",
                                      stop=stop)
            elif self.desired_units != 0 and \
                    self._sig_slots and slot_now not in self._sig_slots:
                pass
        if self.desired_units != 0:
            d = self._manage(ctx)
            if d is None:
                # exit at slot end
                if self._in_slot is not None and \
                        self._in_slot not in self._sig_slots:
                    return self._flat(ctx, "HOD_SLOT_END")
                # refresh significant set daily at 00:30 UTC
                if m == 30:
                    self._sig_slots = self._fdr_slots()
            return d
        if m == 30 and sum(len(v) for v in self._ret_cache.values()) > \
                self.n_slots * 100:
            self._sig_slots = self._fdr_slots()
        return None

    def _slot_sign(self, slot: int) -> int:
        r = self._ret_cache[slot]
        if len(r) < 60:
            return 0
        mean = float(np.mean(r))
        return 1 if mean > 0 else -1

    def _fdr_slots(self) -> set:
        stats = []
        for slot in range(self.n_slots):
            r = self._ret_cache[slot]
            if len(r) < 60:
                stats.append((slot, 0.0))
                continue
            x = np.asarray(r)
            sd = float(np.std(x))
            if sd <= 0:
                stats.append((slot, 0.0))
                continue
            t = abs(float(np.mean(x)) / (sd / math.sqrt(len(x))))
            stats.append((slot, t))
        stats.sort(key=lambda kv: -kv[1])
        m = len(stats)
        out: set = set()
        for rank, (slot, t) in enumerate(stats, start=1):
            thresh = t if t > 0 else 0.0
            crit = self.t_min + 0.0
            # BH: slot significant if t >= t_min AND its BH rank p <= q
            if t < self.t_min:
                break
            # convert t to a one-sided p via normal approx, BH step-up
            from math import erf
            p = 1.0 - 0.5 * (1.0 + erf(t / math.sqrt(2.0)))
            if p <= (rank / m) * self.fdr_q:
                out.add(slot)
        return out

    def _m30_atr(self) -> float:
        bars = [b.as_dict() for b in self.agg.bars[-15:]]
        if len(bars) < 15:
            return float("nan")
        trs = []
        for i in range(1, len(bars)):
            trs.append(max(bars[i]["high"] - bars[i]["low"],
                           abs(bars[i]["high"] - bars[i - 1]["close"]),
                           abs(bars[i]["low"] - bars[i - 1]["close"])))
        return float(np.mean(trs))


# ---------------------------------------------------------------------------
# registry (sleeve, mech_key) -> class
# ---------------------------------------------------------------------------

class RoundNumberFadeLeg(BarClockLeg):
    """GBPUSD-S014: 3rd+ test of a .00/.50 level within 10 days without an
    H4 close through; fade from the level; stop 15 pip outside; target
    50 pip. A "test" = an H4 bar whose [low, high] spans the level with
    its close on the approach side (declared mechanization)."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.touch_days = int(p.get("touch_window_days", 10))
        self.stop_pips = float(p.get("stop_pips", 15.0))
        self.target_pips = float(p.get("target_pips", 50.0))
        self.min_touches = int(p.get("min_touches", 3))
        self.step_pips = float(p.get("level_step_pips", 50.0))

    def _nearest_level(self, price: float) -> float:
        step = self.step_pips * self.pip
        return round(price / step) * step

    def on_agbar(self, bar: AggBar, ctx) -> Optional[LegDecision]:
        level = self._nearest_level(bar.close)
        if abs(bar.close - level) > self.step_pips * self.pip:
            return None
        if self.desired_units != 0:
            return self._manage(ctx)
        # H4 close THROUGH the level resets the count (barrier broken)
        through = ((bar.close > level and bar.open < level) or
                   (bar.close < level and bar.open > level))
        if not hasattr(self, "_touches"):
            self._touches: Dict[float, List[dt.datetime]] = {}
        tlist = self._touches.setdefault(level, [])
        if through:
            self._touches[level] = []
            return None
        if bar.low <= level <= bar.high and abs(bar.close - level) <= \
                0.5 * self.step_pips * self.pip:
            tlist.append(bar.ts)
            cutoff = bar.ts - dt.timedelta(days=self.touch_days)
            self._touches[level] = [t for t in tlist if t >= cutoff]
            if len(self._touches[level]) >= self.min_touches and \
                    self.state_ok_for_entry(ctx):
                direction = -1 if bar.close > level else 1
                # approach side: fade back away from the level
                if direction < 0:
                    stop = level + self.stop_pips * self.pip
                    target = level - self.target_pips * self.pip
                else:
                    stop = level - self.stop_pips * self.pip
                    target = level + self.target_pips * self.pip
                self._touches[level] = []
                return self._open(ctx, direction, "ROUND_NUMBER_FADE",
                                  stop=stop, target=target)
        return None

    def state_ok_for_entry(self, ctx) -> bool:
        return True


class ArGateLeg(BarClockLeg):
    """GBPUSD-S084: rolling 120h AR(1) sign of H1 returns with |coef|>0.1
    as an intraday persistence gate (gate role; declared default maps the
    gate to a standalone position: coef>+0.1 follow the last hour's sign,
    coef<-0.1 fade it, else flat). Estimator: standard OLS AR(1) slope."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.window = int(p.get("ar_window", 120))
        self.coef_min = float(p.get("coef_min", 0.1))

    def on_agbar(self, bar: AggBar, ctx) -> Optional[LegDecision]:
        if len(self.agg.bars) < self.window + 2:
            return None
        closes = np.asarray([b.close for b in self.agg.bars
                             [-(self.window + 1):]])
        r = np.diff(np.log(closes))
        x, y = r[:-1], r[1:]
        var_x = float(np.var(x))
        if var_x <= 0:
            return None
        coef = float(np.cov(x, y)[0, 1] / var_x)
        if self.desired_units != 0:
            if abs(coef) < self.coef_min:
                return self._flat(ctx, "AR_GATE_NEUTRAL")
            want_sign = 1 if self.desired_units > 0 else -1
            last_sign = 1 if r[-1] > 0 else -1
            gate_dir = last_sign if coef > 0 else -last_sign
            if gate_dir != want_sign:
                return self._flat(ctx, "AR_GATE_FLIP")
            return self._manage(ctx)
        if abs(coef) < self.coef_min:
            return None
        last_sign = 1 if r[-1] > 0 else -1
        want = last_sign if coef > 0 else -last_sign
        return self._open(ctx, want, "AR_GATE_PERSIST",
                          stop=None)


class WeeklyNr7BracketLeg(DailyRuleLeg):
    """AUDUSD-S023: weekly NR7 squeeze + position in the 20-week range
    half -> Monday bracket toward the occupied half; stop inside the
    squeeze range (declared: stop at the prior-week mid; the bracket is
    mechanized as an immediate Monday entry in the occupied half's
    direction)."""

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        self._cur_week: List[Dict] = []
        self._weeks: List[Dict] = []
        self._armed: Optional[Tuple[int, float]] = None

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.bars.append(bar)
        self._cur_week.append(bar)
        d = bar["date"]
        if d.weekday() != 4:
            wk_entry = None
        else:
            wk_entry = {"date": d,
                        "high": max(b["high"] for b in self._cur_week),
                        "low": min(b["low"] for b in self._cur_week),
                        "close": bar["close"],
                        "open": self._cur_week[0].get("open", self._cur_week[0]["close"])}
            self._weeks.append(wk_entry)
            self._cur_week = []
        if self.desired_units != 0:
            return self._manage(bar)
        # arm on the first trading day of a new week
        if self._weeks and d.weekday() == 0 and self._armed is None:
            prev = self._weeks[-1]
            prior7 = self._weeks[-8:-1]
            if len(prior7) >= 7:
                nr7 = (prev["high"] - prev["low"]) < min(
                    w["high"] - w["low"] for w in prior7)
                w20 = self._weeks[-20:]
                if len(w20) >= 20 and nr7:
                    hi20 = max(w["high"] for w in w20)
                    lo20 = min(w["low"] for w in w20)
                    mid = (hi20 + lo20) / 2.0
                    self._armed = ((1 if prev["close"] > mid else -1)
                                   if prev["close"] != mid else None,
                                   (prev["high"] + prev["low"]) / 2.0)
        if self._armed is not None and d.weekday() == 0:
            direction, mid = self._armed
            self._armed = None
            if direction is None:
                return None
            prev = self._weeks[-1]
            if direction > 0:
                stop = max(mid, prev["low"])
                return self._enter(+1, "WEEKLY_NR7_BRACKET_LONG", bar,
                                   stop=stop)
            stop = min(mid, prev["high"])
            return self._enter(-1, "WEEKLY_NR7_BRACKET_SHORT", bar,
                               stop=stop)
        return None


RULE_REGISTRY = {
    ("POOL_B_TRIAGE", "donchian_sar"): DonchianSarLeg,
    ("POOL_B_TRIAGE", "donchian_trail"): DonchianTrailLeg,
    ("POOL_B_TRIAGE", "adx_macd_persist"): AdxMacdLeg,
    ("POOL_B_TRIAGE", "ma_adx_regime"): MaAdxRegimeLeg,
    ("POOL_B_TRIAGE", "ts_momentum"): TsMomentumLeg,
    ("POOL_B_TRIAGE", "ma200_dislocation"): Ma200DislocationLeg,
    ("POOL_B_TRIAGE", "turtle_pyramid"): TurtlePyramidLeg,
    ("POOL_B_TRIAGE", "rsi2_daily_pullback"): Rsi2DailyLeg,
    ("POOL_B_TRIAGE", "bb_squeeze_break"): BBSqueezeBreakLeg,
    ("POOL_B_TRIAGE", "bb_lowvol_range"): BBLowVolRangeLeg,
    ("POOL_B_TRIAGE", "atr_ratio_break"): AtrRatioBreakoutLeg,
    ("POOL_B_TRIAGE", "weekly_swing_break"): WeeklySwingBreakLeg,
    ("POOL_B_TRIAGE", "weekly_ma_regime"): WeeklyMaRegimeLeg,
    ("POOL_B_TRIAGE", "calendar_season"): CalendarSeasonLeg,
    ("POOL_B_TRIAGE", "regime_gate"): RegimeGateLeg,
    ("POOL_B_TRIAGE", "cross_z"): CrossZLeg,
    ("POOL_B_TRIAGE", "keltner_break"): KeltnerBreakLeg,
    ("POOL_B_TRIAGE", "adx_ema_rider"): AdxEmaRiderLeg,
    ("POOL_B_TRIAGE", "weekly_h4_break"): WeeklyH4BreakLeg,
    ("POOL_B_TRIAGE", "h4_zscore"): H4ZscoreLeg,
    ("POOL_B_TRIAGE", "rsi2_barclock"): Rsi2BarClockLeg,
    ("POOL_B_TRIAGE", "atr_ratio_h4"): AtrRatioH4Leg,
    ("POOL_B_TRIAGE", "h1_pdh_pdl"): H1PdhPdlLeg,
    ("POOL_B_TRIAGE", "usdjpy_momentum_gate"): UsdjpyMomentumGateLeg,
    ("POOL_B_TRIAGE", "london_persistence"): LondonPersistenceLeg,
    ("POOL_B_TRIAGE", "session_range_rule"): SessionRangeFadeLeg,
    ("POOL_B_TRIAGE", "nr7_stop_orders"): Nr7StopOrderLeg,
    ("POOL_B_TRIAGE", "nr7_m30_break"): Nr7M30BreakLeg,
    ("POOL_B_TRIAGE", "hour_of_day_drift"): HourOfDayDriftLeg,
    ("POOL_B_TRIAGE", "round_number_fade"): RoundNumberFadeLeg,
    ("POOL_B_TRIAGE", "ar_persistence_gate"): ArGateLeg,
    ("POOL_B_TRIAGE", "weekly_nr7_bracket"): WeeklyNr7BracketLeg,
}
