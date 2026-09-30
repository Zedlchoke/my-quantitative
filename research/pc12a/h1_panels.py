"""H1 ANC panel adapter — PC12A Stage-A wave 2.

Stages the ERP1-TRACKA-COHORT-1 ANC H1 parquets (AUDUSD/USDCAD) behind the
SAME ``DayPanel`` interface the M1 engine consumes, so the frozen
``run_dry.SymbolEngine`` streams them without modification.

Source plane (read-only; ERP1-TRACKA-COHORT-1 DATAGATE_REPORT):
``bars1h_ANC_{SYM}.parquet`` — one row per TRADED hour, columns
``ts, b_o, b_h, b_l, b_c, a_o, a_c, s_open, s_close``; bid OHLC from the
ANC M1 plane, ask open/close measured (a_o = b_o + s_open), spreads in
price units; pip 1e-4, price_scale 1e5 both pairs; coverage 2021-01-03 →
2026-06-30 (BUILD_PASS census; spreads identical to the port plane per
``plane_diff_*.json``).

Adaptation semantics (ALL declared, disclosed in
``data_freeze/H1_PANELS.json``):

- Slot mapping: hour ``h`` (bar ``[h:00, h+1:00)``) occupies minute slot
  ``m = h*60 + 59`` of the day; the engine stamps the bar close at
  ``m+1 = (h+1):00`` — the PIT-honest instant the H1 close exists. Fills
  at "next-bar open" therefore execute at the NEXT hour's open price —
  exactly the campaign §1 clock law ("H1 pairs fill from the 20:00-open
  bar"). Non-slot minutes carry volume 0 (untradable).
- No intra-hour path is fabricated: each slot carries its hour's true
  interval OHLC (open=close-of-day aggregates, D1/H4 recombinations from
  slots preserve true highs/lows/first/last).
- ANC open semantics (quantified at staging): the bar open is the hour's
  LEFT-BOUNDARY quote and can sit above the hour's high (AUDUSD 2,504 /
  USDCAD 2,566 of ~30.4k hours; never below the low); closes are always
  inside [low, high]. The adapter enforces close-in-range + non-negative
  spread and treats opens purely as boundary fill quotes.
- Ask side: open/close MEASURED (a_o/a_c); intra-hour ask extremes are
  NOT in the ANC plane and are declared as bid extreme + s_open.
- Volume is a presence indicator (1.0 on traded slots) — NOT the M1
  size-weighted magnitude. LAWFUL only because no size-weighted consumer
  (VOLPROF profiles) runs on H1 pairs; disclosed.
- Cost cells: C1 per the wave-2 dispatch COST_AUTHORITY_TABLE note
  (USDCAD p50/p90 1.2/1.6 · AUDUSD 1.0/1.3 pips); C2_MON_THU / C2_FRI /
  C3 from the ERP1 census session buckets (rollover_21_22,
  friday_20_23_open, sunday_open_21_22 OPEN p50/p90).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from typing import Dict, List, Optional

import numpy as np

from . import cost_kernel as _ck
from . import panels as _panels

UTC = dt.timezone.utc

# Default read-only parquet locations (ERP1-TRACKA-COHORT-1 worktree).
_DEFAULT_H1_ROOTS = {
    "AUDUSD": (
        "/Users/hoangminhlong/my-quantitative/.worktrees/"
        "erp1-tracka-cohort-1/repro_twin/research/control/"
        "ERP1-TRACKA-COHORT-1/data_local/derived/bars1h_ANC_AUDUSD.parquet"
    ),
    "USDCAD": (
        "/Users/hoangminhlong/my-quantitative/.worktrees/"
        "erp1-tracka-cohort-1/repro_twin/research/control/"
        "ERP1-TRACKA-COHORT-1/data_local/derived/bars1h_ANC_USDCAD.parquet"
    ),
}

H1_PAIR_SPECS = {
    "AUDUSD": _panels.PairSpec("AUDUSD", 0.0001, 1e5, True),
    "USDCAD": _panels.PairSpec("USDCAD", 0.0001, 1e5, True),
}

# Measured cells (pips) — provenance in the module docstring; the census
# overall_open p90 (1.4 / 1.7) is DISCLOSED alongside the dispatch C1 note
# numbers which GOVERN here (latest owner instruction authority).
H1_MEASURED_CELLS: Dict[str, Dict[str, Dict[str, float]]] = {
    "C1": {
        "AUDUSD": {"p50": 1.0, "p90": 1.3},
        "USDCAD": {"p50": 1.2, "p90": 1.6},
    },
    "C2_MON_THU": {
        "AUDUSD": {"p50": 2.0, "p90": 5.4},
        "USDCAD": {"p50": 2.3, "p90": 7.7},
    },
    "C2_FRI": {
        "AUDUSD": {"p50": 1.1, "p90": 1.6},
        "USDCAD": {"p50": 1.3, "p90": 2.0},
    },
    "C3": {
        "AUDUSD": {"p50": 4.6, "p90": 7.79},
        "USDCAD": {"p50": 6.8, "p90": 14.7},
    },
}

_INSTALLED = False


def install() -> None:
    """Idempotently extend panels.PAIR_SPECS, cost_kernel.MEASURED_CELLS
    and policy.KNOWN_INPUT_DOMAINS with the H1 pairs so the frozen engine
    code paths accept them. Mid-range domains are the ERP1 DATAGATE
    REGISTERED price bands (probe min x0.80 floor / max x1.20 ceil on the
    pip grid, union the registered guard) — the same 'sane price band'
    construction the M1 table froze from the Lane D audit."""
    global _INSTALLED
    if _INSTALLED:
        return
    _panels.PAIR_SPECS.update(H1_PAIR_SPECS)
    for cell, per_pair in H1_MEASURED_CELLS.items():
        _ck.MEASURED_CELLS[cell].update(per_pair)
    from . import policy as _pol
    _pol.KNOWN_INPUT_DOMAINS.setdefault(
        "AUDUSD_mid_range", (0.5209, 0.85))
    _pol.KNOWN_INPUT_DOMAINS.setdefault(
        "USDCAD_mid_range", (1.1057, 1.6751))
    _INSTALLED = True


class H1PanelError(RuntimeError):
    pass


def _slot_of_hour(h: int) -> int:
    """Minute slot carrying hour h's bar (bar END, stamped (h+1):00)."""
    return h * 60 + 59


class H1DayPanel:
    """DayPanel-compatible view over one pair-day of H1 bars."""

    def __init__(self, symbol: str, date: dt.date,
                 hours: List[dict]):
        n = _panels.RECORDS_PER_DAY
        bid_open = np.zeros(n)
        bid_close = np.zeros(n)
        bid_low = np.zeros(n)
        bid_high = np.zeros(n)
        ask_open = np.zeros(n)
        ask_close = np.zeros(n)
        ask_low = np.zeros(n)
        ask_high = np.zeros(n)
        bvol = np.zeros(n)
        avol = np.zeros(n)
        seen: Dict[int, dict] = {}
        for row in hours:
            ts = row["ts"]
            if ts.date() != date or ts.minute != 0 or ts.second != 0:
                raise H1PanelError(f"{symbol} {date}: off-grid hour {ts}")
            h = ts.hour
            if h in seen:
                raise H1PanelError(f"{symbol} {date}: duplicate hour {h}")
            seen[h] = row
        for h, row in seen.items():
            m = _slot_of_hour(h)
            s_open = float(row["s_open"])
            b_o, b_c = float(row["b_o"]), float(row["b_c"])
            b_l, b_h = float(row["b_l"]), float(row["b_h"])
            a_o, a_c = float(row["a_o"]), float(row["a_c"])
            # ANC open semantics (dispatch; ERP1 build_bars.py): the bar's
            # OPEN is the LEFT-BOUNDARY quote of the hour's first M1 bar --
            # it can sit ABOVE the hour's high (~8% of hours, price fell off
            # the boundary; never below the low in either pair) and is NOT
            # an interval extreme. The interval self-consistency gate is
            # therefore close-in-range (H/L/C are true interval extremes,
            # which is what stops/ATR/aggregations consume); opens feed
            # ONLY the next-bar-open fill law, where the boundary quote is
            # exactly the executable price the campaign clock charges.
            if not (b_l <= b_c <= b_h):
                raise H1PanelError(
                    f"{symbol} {date} h{h}: ANC interval OHLC violated "
                    f"(close outside [low, high])")
            if a_o < b_o or a_c < b_c or s_open < 0:
                raise H1PanelError(f"{symbol} {date} h{h}: negative spread")
            bid_open[m], bid_close[m] = b_o, b_c
            bid_low[m], bid_high[m] = b_l, b_h
            # ask extremes: bid extreme + the hour's measured open spread
            ask_open[m], ask_close[m] = a_o, a_c
            ask_low[m] = b_l + s_open
            ask_high[m] = b_h + s_open
            bvol[m] = 1.0     # presence indicator (see module docstring)
            avol[m] = 1.0
        self.symbol = symbol
        self.date = date
        self.bid = _panels.SideBar(
            np.arange(0, 60 * n, 60, dtype=np.int64), bid_open, bid_close,
            bid_low, bid_high, bvol)
        self.ask = _panels.SideBar(
            np.arange(0, 60 * n, 60, dtype=np.int64), ask_open, ask_close,
            ask_low, ask_high, avol)
        self.n_hours = len(seen)
        self.hours_sorted = [seen[h] for h in sorted(seen)]

    @property
    def mid_open(self) -> np.ndarray:
        return (self.bid.open + self.ask.open) / 2.0

    @property
    def mid_close(self) -> np.ndarray:
        return (self.bid.close + self.ask.close) / 2.0

    def tradable_mask(self) -> np.ndarray:
        return (self.bid.volume > 0) & (self.ask.volume > 0)


class H1PanelStore:
    """Read-only parquet-backed H1 store with the PanelStore call shape."""

    def __init__(self, roots: Optional[Dict[str, str]] = None):
        install()
        if roots is None:
            env = os.environ.get("PC12A_H1_PARQUETS")
            roots = json.loads(env) if env else dict(_DEFAULT_H1_ROOTS)
        self.roots = dict(roots)
        missing = {p: r for p, r in self.roots.items()
                   if not os.path.isfile(r)}
        if missing:
            raise H1PanelError(f"H1 parquet(s) missing: {missing}")
        self._by_day: Dict[str, Dict[dt.date, List[dict]]] = {}
        self._digests: Dict[str, str] = {}
        self.coverage: Dict[str, Dict] = {}
        for sym, path in self.roots.items():
            self._load_parquet(sym, path)

    def _load_parquet(self, symbol: str, path: str) -> None:
        import pandas as pd

        df = pd.read_parquet(path)
        need = {"ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c",
                "s_open", "s_close"}
        if not need.issubset(df.columns):
            raise H1PanelError(f"{symbol}: parquet columns {list(df.columns)}")
        by_day: Dict[dt.date, List[dict]] = {}
        for rec in df.itertuples(index=False):
            ts = rec.ts.to_pydatetime().astimezone(UTC)
            by_day.setdefault(ts.date(), []).append({
                "ts": ts, "b_o": rec.b_o, "b_h": rec.b_h, "b_l": rec.b_l,
                "b_c": rec.b_c, "a_o": rec.a_o, "a_c": rec.a_c,
                "s_open": rec.s_open, "s_close": rec.s_close})
        self._by_day[symbol] = by_day
        first = df["ts"].min().to_pydatetime()
        last = df["ts"].max().to_pydatetime()
        self.coverage[symbol] = {
            "first_ts": first.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "last_ts": last.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "n_rows": int(len(df)),
        }

    def load_day(self, symbol: str, date: dt.date) -> H1DayPanel:
        hours = self._by_day.get(symbol, {}).get(date)
        if not hours:
            raise FileNotFoundError(
                f"{symbol} {date}: no H1 bars (weekend/holiday/out of range)")
        return H1DayPanel(symbol, date, hours)

    def load_range(self, symbol: str, start: dt.date,
                   end: dt.date) -> Dict[dt.date, H1DayPanel]:
        out = {}
        for d in sorted(self._by_day.get(symbol, {})):
            if start <= d <= end:
                out[d] = self.load_day(symbol, d)
        return out

    def panel_digest(self, symbol: str, days) -> str:
        """Deterministic sha256 over the consumed days' raw rows (mirrors
        the M1 audit method: date | side-less | row payload digest)."""
        lines = []
        for d in sorted(days):
            if d not in self._by_day.get(symbol, {}):
                continue
            blob = hashlib.sha256(
                "\n".join(
                    f"{r['ts'].isoformat()}|{r['b_o']!r}|{r['b_h']!r}|"
                    f"{r['b_l']!r}|{r['b_c']!r}|{r['a_o']!r}|{r['a_c']!r}|"
                    f"{r['s_open']!r}|{r['s_close']!r}"
                    for r in self._by_day[symbol][d]).encode()).hexdigest()
            lines.append(f"{d.isoformat()}|{len(self._by_day[symbol][d])}|{blob}")
        return hashlib.sha256("\n".join(lines).encode()).hexdigest()


class CombinedStore:
    """M1 PanelStore ∪ H1PanelStore with the engine-facing call shape."""

    def __init__(self, m1: _panels.PanelStore, h1: H1PanelStore):
        self.m1 = m1
        self.h1 = h1
        self.roots = dict(m1.roots)
        self.roots.update({s: p for s, p in h1.roots.items()})

    def load_day(self, symbol: str, date: dt.date):
        if symbol in self.h1.roots:
            return self.h1.load_day(symbol, date)
        return self.m1.load_day(symbol, date)

    def load_range(self, symbol: str, start: dt.date, end: dt.date):
        if symbol in self.h1.roots:
            return self.h1.load_range(symbol, start, end)
        return self.m1.load_range(symbol, start, end)

    def panel_digest(self, symbol: str, days) -> str:
        if symbol in self.h1.roots:
            return self.h1.panel_digest(symbol, days)
        return self.m1.panel_digest(symbol, days)


def configured_store() -> CombinedStore:
    """install() + M1 store + H1 store (env-overridable H1 parquets)."""
    install()
    return CombinedStore(_panels.PanelStore(), H1PanelStore())
