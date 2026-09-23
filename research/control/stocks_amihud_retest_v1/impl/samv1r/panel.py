"""STOCKS-AMIHUD-V1 engine — panel loading with the frozen guard laws.

Guard classes (d1/division_site_register.json):
  i   adjusted_close <= 0 or non-finite  -> name-day EXCLUDED + counted
  ii  DV = adjusted_close * volume <= 0 or non-finite -> excluded from
      formation means + counted (volume==0 rows keep price but carry DV=0)
No other data mutation. Raw CSVs are sha-pinned by the crawl manifest.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

P0 = Path(__file__).resolve().parents[2] / "p0"  # retest namespace
STAGING = P0 / "staging_eod_csv"


class GuardCounters:
    def __init__(self) -> None:
        self.adj_nonpositive = 0
        self.adj_nonfinite = 0
        self.dv_zero_or_nonpositive = 0
        self.duplicate_dates = 0
        self.extreme_print_bars_b1 = 0      # |log-ratio| >= log(10)
        self.zero_volume_bars_b2 = 0

    def as_dict(self) -> dict:
        return {"adj_nonpositive": self.adj_nonpositive,
                "adj_nonfinite": self.adj_nonfinite,
                "dv_zero_or_nonpositive": self.dv_zero_or_nonpositive,
                "duplicate_dates": self.duplicate_dates,
                "extreme_print_bars_b1": self.extreme_print_bars_b1,
                "zero_volume_bars_b2": self.zero_volume_bars_b2}

    def add(self, other: "GuardCounters") -> None:
        for k in self.__dict__:
            setattr(self, k, getattr(self, k) + getattr(other, k))


class NameSeries:
    """Guarded per-name arrays on the frozen basis."""

    __slots__ = ("code", "dates", "idx", "open_raw", "close_raw", "adj",
                 "vol", "dv", "adj_ok", "fill_ok")

    def __init__(self, code: str) -> None:
        self.code = code
        self.dates: list[str] = []
        self.idx: dict[str, int] = {}
        self.open_raw: list[float] = []
        self.close_raw: list[float] = []
        self.adj: list[float] = []          # NaN where class-i excluded
        self.vol: list[float] = []
        self.dv: list[float] = []           # 0.0 where class-ii excluded
        self.adj_ok: list[bool] = []
        self.fill_ok: list[bool] = []       # B1/B2 feasibility (pass 2)

    # adjusted open = raw open * (adj_close / raw close)  [frozen impl law]
    def adj_open(self, i: int) -> float:
        f = self.adj[i] / self.close_raw[i]          # close_raw>0 asserted at load
        return self.open_raw[i] * f

    def adj_close(self, i: int) -> float:
        return self.adj[i]


def load_name(code: str, guards: GuardCounters) -> NameSeries | None:
    p = STAGING / f"{code}.csv"
    if not p.exists():
        return None
    ns = NameSeries(code)
    seen: set[str] = set()
    with p.open(newline="") as f:
        for rec in csv.DictReader(f):
            d = (rec.get("Date") or "").strip()
            if not d or d in seen:
                if d:
                    guards.duplicate_dates += 1
                continue
            try:
                o = float(rec["Open"]); c = float(rec["Close"])
                a = float(rec["Adjusted_close"]); v = float(rec["Volume"])
            except (ValueError, TypeError, KeyError):
                continue
            if not (math.isfinite(o) and math.isfinite(c) and math.isfinite(v)):
                continue
            if c <= 0.0 or o < 0.0 or v < 0.0:
                continue
            seen.add(d)
            ok = math.isfinite(a) and a > 0.0
            if not ok:
                if math.isfinite(a):
                    guards.adj_nonpositive += 1
                else:
                    guards.adj_nonfinite += 1
            dv = a * v if ok else 0.0
            if ok and not (math.isfinite(dv) and dv > 0.0):
                guards.dv_zero_or_nonpositive += 1
                dv = 0.0
            ns.dates.append(d); ns.idx[d] = len(ns.dates) - 1
            ns.open_raw.append(o); ns.close_raw.append(c)
            ns.adj.append(a if ok else float("nan"))
            ns.vol.append(v); ns.dv.append(dv); ns.adj_ok.append(ok)
            ns.fill_ok.append(False)  # set on pass 2 (needs prev bar)
    if not ns.dates:
        return None
    import math as _m
    for i in range(len(ns.dates)):
        ok_fill = ns.adj_ok[i] and ns.vol[i] > 0.0
        if i > 0 and ok_fill and ns.adj_ok[i - 1] and ns.adj[i - 1] > 0:
            if abs(_m.log(ns.adj[i] / ns.adj[i - 1])) >= _m.log(10.0):
                ok_fill = False
                guards.extreme_print_bars_b1 += 1
        if ns.adj_ok[i] and ns.vol[i] <= 0.0:
            guards.zero_volume_bars_b2 += 1
        ns.fill_ok[i] = ok_fill
    return ns


def load_panel(codes: list[str]) -> tuple[dict[str, NameSeries], dict]:
    guards = GuardCounters()
    panel: dict[str, NameSeries] = {}
    for c in codes:
        ns = load_name(c, guards)
        if ns is not None:
            panel[c] = ns
    return panel, guards.as_dict()


def sessions_from_spy() -> list[str]:
    g = GuardCounters()
    spy = load_name("SPY", g)
    assert spy is not None and len(spy.dates) > 0
    return list(spy.dates)
