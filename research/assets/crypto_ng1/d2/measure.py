"""CRYPTO-NG1 D2 measurement library: NOVELTY + FEASIBILITY, no PnL.

Measured on the frozen S4 H1 panels (3 symbols, 2025-08-22T00..2026-08-21T23)
consumed ONLY through the cycle plane adapter (CADS resolve verify-on-read,
digest-pinned).  Every number this module produces is one of:

  * pooled Pearson/Spearman |rho| between a proposal's declared D2 series
    (per-decision gross return vector, per its frozen representation_identity)
    and a veto-panel shadow evaluated on the same decision grid;
  * decision counts, fill counts, calendar-arithmetic facts;
  * margins to the frozen 0.20 bar.

NO expectancy, NO profit factor, NO PnL, NO aggregate of returns is computed
or emitted anywhere (outcome-leak ban for the D2 lane).

Cost invariance (why gross returns suffice): the declared per-decision
after-cost return is r_net = r - 2*c with a CONSTANT c per anchor arm.  Pearson
is invariant to additive shifts of either argument; Spearman is invariant to
any strictly monotone transform.  Therefore rho(r_net, v) == rho(r, v) for
every veto series v and every tier constant c: the novelty measurement needs
no cost constant and none is invented here.
"""

from __future__ import annotations

import calendar as _calendar
import csv
import io
import json
import math
import statistics
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

SCHEMA_LIB = "crypto_ng1/d2_measure@1"

#: Frozen novelty bar (plan section 6 rubric item 2; P-2 margins recorded).
VETO_BAR = 0.20

#: Q-6 recent-window anchor floor (frozen for this cycle).
Q6_RECENT_WINDOW_MONTHS = 6
Q6_ANCHOR_FLOOR = 8

#: Minimum aligned pairs for a rho to be reported as a veto decision number.
#: (V17 D2 used 30 on multi-thousand-point grids; the NG1 frozen D2 series are
#: 12/24 rows BY DECLARATION, so the guard is scaled to the cycle's own
#: Q-6 floor of 8.  Pairs below it are recorded NOT_COMPUTABLE_LOW_N, never
#: guessed.)  The 0.20 bar itself is unchanged.
MIN_PAIRS = 8

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

PANEL_WINDOW_START = datetime(2025, 8, 22, 0, tzinfo=timezone.utc)
PANEL_WINDOW_END = datetime(2026, 8, 21, 23, tzinfo=timezone.utc)

#: Frozen FOMC decision instants (p0_calendar_census.json, DST-correct UTC).
FOMC_INSTANTS = [
    "2025-09-17T18:00:00Z",
    "2025-10-29T18:00:00Z",
    "2025-12-10T19:00:00Z",
    "2026-01-28T19:00:00Z",
    "2026-03-18T18:00:00Z",
    "2026-04-29T18:00:00Z",
    "2026-06-17T18:00:00Z",
    "2026-07-29T18:00:00Z",
]

#: Quarterly delivery instants pinned in proposal CNG1-A5-P1 (last Friday of
#: Mar/Jun/Sep/Dec at 08:00 UTC inside the panel window).
A5_P1_PINNED_QUARTERLY = [
    "2025-09-26", "2025-12-26", "2026-03-27", "2026-06-26",
]

#: Non-quarterly monthly options-expiry instants pinned in CNG1-A5-P2 (last
#: Friday of every non-quarterly month at 08:00 UTC inside the window).
A5_P2_PINNED_NONQUARTERLY = [
    "2025-08-29", "2025-10-31", "2025-11-28", "2026-01-30",
    "2026-02-27", "2026-04-24", "2026-05-29", "2026-07-31",
]

#: Venue-pinned out-of-window epochs recorded in the A5 proposals'
#: spec_verification (Binance fapi deliveryDate, milliseconds UTC).
VENUE_PINNED_EPOCHS_MS = {
    "BTCUSDT_260925": 1790323200000,   # -> 2026-09-25T08:00:00Z expected
    "BTCUSDT_261225": 1798185600000,   # -> 2026-12-25T08:00:00Z expected
}

#: Deribit monthly/quarterly options expiration DATES pinned in the proposals.
VENUE_PINNED_DERIBIT_DATES = [
    "2026-10-30", "2026-11-27", "2026-12-25", "2027-03-26", "2027-06-25",
]

#: Disclosed holiday-hazard dates (A5 lane): retained in the grids per the
#: declarations; liquidity-level leakage is measured by the dvol veto rows.
HOLIDAY_HAZARD_DATES = ["2025-11-28", "2025-12-26"]

#: V17 endpoint-series inheritance (READ-ONLY): funding history used only to
#: rebuild the FUNDJUMP funding-LEVEL veto exactly per the V17 family spec
#: (BTC/ETH only -- the family never had SOL).
DEFAULT_FUNDING_HISTORY_PATH = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v17/integration/"
    "research/control/v17_run/d2/funding_history.json")

#: V17 OI reduced series geometry: 484 days x 6 H4 snapshots from this warmup
#: start (V17 pull_endpoint_series.py; matches oi_metrics_manifest first date).
OI_WARMUP_START = datetime(2025, 4, 25, 0, tzinfo=timezone.utc)
OI_SNAPSHOTS_EXPECTED = 484 * 6

_S0_START_MS = int(PANEL_WINDOW_START.timestamp() * 1000)
_S0_END_MS = int((PANEL_WINDOW_END + timedelta(hours=1)).timestamp() * 1000) - 1

H4_MS = 4 * 3600 * 1000
DAY_MS = 86400 * 1000


# --------------------------------------------------------------------------- #
# 1. statistics (hand-rolled, deterministic; average-rank Spearman)
# --------------------------------------------------------------------------- #

def _valid_pairs(x, y):
    return [(a, b) for a, b in zip(x, y)
            if a is not None and b is not None
            and isinstance(a, (int, float)) and isinstance(b, (int, float))
            and math.isfinite(a) and math.isfinite(b)]


def pearson(x, y, min_pairs: int = MIN_PAIRS):
    """Pearson r over aligned non-None pairs; None when not decidable."""
    pairs = _valid_pairs(x, y)
    if len(pairs) < min_pairs:
        return None
    xs = [a for a, _ in pairs]
    ys = [b for _, b in pairs]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0.0 or syy <= 0.0:
        return None
    return sum((a - mx) * (b - my) for a, b in pairs) / math.sqrt(sxx * syy)


def _average_ranks(v):
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


def spearman(x, y, min_pairs: int = MIN_PAIRS):
    """Spearman rho (average ranks for ties); None when not decidable."""
    pairs = _valid_pairs(x, y)
    if len(pairs) < min_pairs:
        return None
    return pearson(_average_ranks([a for a, _ in pairs]),
                   _average_ranks([b for _, b in pairs]),
                   min_pairs=1)          # guard already applied above


def rho_pair_status(x, y, min_pairs: int = MIN_PAIRS) -> dict:
    """Measure one veto pair: rho values + explicit status, never a guess."""
    pairs = _valid_pairs(x, y)
    n = len(pairs)
    if n == 0:
        return {"n_pairs": 0, "pearson": None, "spearman": None,
                "max_abs_rho": None, "margin_to_bar": None,
                "status": "NOT_COMPUTABLE_MISSING_COVERAGE",
                "pair_verdict": "UNMEASURED"}
    if n < min_pairs:
        return {"n_pairs": n, "pearson": None, "spearman": None,
                "max_abs_rho": None, "margin_to_bar": None,
                "status": "NOT_COMPUTABLE_LOW_N", "pair_verdict": "UNMEASURED"}
    p = pearson(x, y, min_pairs=1)
    s = spearman(x, y, min_pairs=1)
    if p is None or s is None:
        return {"n_pairs": n, "pearson": None, "spearman": None,
                "max_abs_rho": None, "margin_to_bar": None,
                "status": "DEGENERATE_ZERO_VARIANCE",
                "pair_verdict": "UNMEASURED"}
    m = max(abs(p), abs(s))
    return {"n_pairs": n, "pearson": round(p, 6), "spearman": round(s, 6),
            "max_abs_rho": round(m, 6),
            "margin_to_bar": round(VETO_BAR - m, 6),
            "status": "MEASURED",
            "pair_verdict": "VETO" if m > VETO_BAR else "PASS"}


# --------------------------------------------------------------------------- #
# 2. calendar arithmetic (deterministic, network-free)
# --------------------------------------------------------------------------- #

def last_friday(year: int, month: int) -> date:
    """Last Friday of (year, month) by pure calendar arithmetic."""
    d = date(year, month, _calendar.monthrange(year, month)[1])
    while d.weekday() != 4:      # Monday=0 .. Sunday=6; Friday=4
        d -= timedelta(days=1)
    return d


def quarterly_delivery_dates(start: date, end: date) -> list[date]:
    """Last Fridays of Mar/Jun/Sep/Dec inside [start, end]."""
    out = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        if m in (3, 6, 9, 12):
            d = last_friday(y, m)
            if start <= d <= end:
                out.append(d)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def monthly_last_fridays(start: date, end: date) -> list[date]:
    """Last Fridays of every month inside [start, end]."""
    out = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        d = last_friday(y, m)
        if start <= d <= end:
            out.append(d)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def epoch_ms_to_utc(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)


def parse_hour(h: str) -> datetime:
    return datetime.strptime(h, "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)


def fmt_hour(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H")


def parse_instant(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)


# --------------------------------------------------------------------------- #
# 3. panel (plane-adapter consumption only)
# --------------------------------------------------------------------------- #

@dataclass
class Panel:
    """One frozen S4 H1 panel parsed from plane-adapter bytes."""
    symbol: str
    hours: list[str]                       # ordered hour keys
    rows: dict[str, dict]                  # hour -> parsed numeric row
    first_ts_ms: int
    last_ts_ms: int

    @classmethod
    def from_bytes(cls, symbol: str, data: bytes) -> "Panel":
        reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
        rows, hours = {}, []
        for r in reader:
            h = r["hour_utc"]
            rows[h] = {
                "hour": h,
                "day": r["day_utc"],
                "n_trades": int(r["n_trades"]),
                "buy_count": int(r["buy_count"]),
                "buy_qty": float(r["buy_qty"]),
                "sell_qty": float(r["sell_qty"]),
                "buy_quote": float(r["buy_quote"]),
                "sell_quote": float(r["sell_quote"]),
                "quote_total": float(r["quote_total"]),
                "qty_total": float(r["qty_total"]),
                "vwap": float(r["vwap"]),
                "first_price": float(r["first_price"]),
                "last_price": float(r["last_price"]),
                "max_trade_quote": float(r["max_trade_quote"]),
                "entry_gap_s": float(r["entry_gap_s"]),
                "max_run_buy": int(r["max_run_buy"]),
                "max_run_sell": int(r["max_run_sell"]),
                "last_ts_ms": int(r["last_ts_ms"]),
            }
            hours.append(h)
        hours.sort()
        if not hours:
            raise ValueError(f"empty panel for {symbol}")
        return cls(symbol=symbol, hours=hours, rows=rows,
                   first_ts_ms=rows[hours[0]]["last_ts_ms"],
                   last_ts_ms=rows[hours[-1]]["last_ts_ms"])

    def bar(self, hour: str) -> Optional[dict]:
        return self.rows.get(hour)

    def bar_offset(self, hour: str, k: int) -> Optional[dict]:
        """The bar k H1 steps after the bar keyed `hour` (None if absent)."""
        return self.rows.get(fmt_hour(parse_hour(hour) + timedelta(hours=k)))

    def bar_close_ms(self, hour: str) -> Optional[int]:
        b = self.rows.get(hour)
        return None if b is None else b["last_ts_ms"]

    def price_at_close(self, ts_ms: int) -> Optional[float]:
        """last_price of the H1 bar whose close is ts (bar starting ts-1h)."""
        dt = epoch_ms_to_utc(ts_ms) - timedelta(hours=1)
        b = self.rows.get(fmt_hour(dt))
        return None if b is None else b["last_price"]


def load_panels(consume: Callable[[str], dict]) -> dict[str, Panel]:
    """Consume the 3 frozen panels by entry name through the plane adapter."""
    out = {}
    for sym in SYMBOLS:
        res = consume(f"staging_v17/panel_{sym}_h1.csv")
        out[sym] = Panel.from_bytes(sym, res["data"])
    return out


def daily_aggregates(panel: Panel) -> dict[str, dict]:
    """Per-UTC-day aggregates, faithful to V17 d2 daily() definitions."""
    by: dict[str, list[dict]] = {}
    for h in panel.hours:
        by.setdefault(panel.rows[h]["day"], []).append(panel.rows[h])
    out = {}
    for d, rs in sorted(by.items()):
        q = sum(r["quote_total"] for r in rs)
        n = sum(r["n_trades"] for r in rs)
        qty = sum(r["qty_total"] for r in rs)
        vwap = q / qty if qty else 0.0
        last, first = rs[-1]["last_price"], rs[0]["first_price"]
        bq = sum(r["buy_qty"] for r in rs)
        sq = sum(r["sell_qty"] for r in rs)
        bc = sum(r["buy_count"] for r in rs)
        mb = max(r["max_run_buy"] for r in rs)
        ms = max(r["max_run_sell"] for r in rs)
        out[d] = {
            "ret": math.log(last / first) if first and last else 0.0,
            "cdf_disp": (last - vwap) / vwap if vwap else 0.0,
            "run_imb": (bq - sq) / (bq + sq) if (bq + sq) else 0.0,
            "run_persist": (mb - ms) / (mb + ms) if (mb + ms) else 0.0,
            "taker_sat": bc / n if n else 0.0,
            "dvol": q,
            "ntrades": n,
            "elite": sum(r["max_trade_quote"] for r in rs),
            "avg_ticket": q / n if n else 0.0,
        }
    ks = sorted(out)
    for i, d in enumerate(ks):
        r = out[d]
        prior21 = [out[x]["dvol"] for x in ks[max(0, i - 21):i]]
        r["dvol_shock"] = (r["dvol"] / statistics.median(prior21)
                           if i >= 21 and statistics.median(prior21) else None)
        r["amihud"] = (abs(r["ret"]) / r["dvol"] * 1e9
                       if r["dvol"] else None)
        r["tsmom28"] = (sum(out[x]["ret"] for x in ks[max(0, i - 27):i + 1])
                        if i >= 27 else None)
        r["dvol_level_log"] = math.log(r["dvol"]) if r["dvol"] else None
        prior60 = [out[x]["avg_ticket"] for x in ks[max(0, i - 59):i]]
        med60 = statistics.median(prior60) if i >= 59 else None
        r["avg_ticket_ratio"] = (r["avg_ticket"] / med60
                                 if med60 else None)
    return out


# --------------------------------------------------------------------------- #
# 4. proposal signal series (exact representation_identity, gross returns)
# --------------------------------------------------------------------------- #

@dataclass
class Decision:
    symbol: str
    instant: str                 # ISO Z instant of the clock event
    decision_ts: str             # ISO Z bar close at which the decision lands
    decision_bar: str            # hour key of the bar closed at decision
    decision_date: str           # UTC date of the decision (daily projection key)
    role: str                    # anchor | neighbour
    status: str                  # FUNDED | UNFUNDED_SKIP | BLOCKED_MISSING_BAR
    direction: Optional[int] = None
    r_gross: Optional[float] = None   # cost-shift invariant for rho (see header)


def _imb(bar: dict) -> Optional[float]:
    if bar["quote_total"] == 0.0:
        return None
    return (bar["buy_quote"] - bar["sell_quote"]) / bar["quote_total"]


def _press(panel: Panel, a_hour: str, k_start: int, k_end: int):
    """Bounded net-pressure ratio over bars A+k_start..A+k_end (inclusive)."""
    num = den = 0.0
    for k in range(k_start, k_end + 1):
        b = panel.bar_offset(a_hour, k)
        if b is None:
            return None, True
        num += b["buy_quote"] - b["sell_quote"]
        den += b["quote_total"]
    if den == 0.0:
        return None, False
    return num / den, False


def _mk(panel, sym, instant, dec_bar, dec_ts, d, entry_bar, exit_bar) -> Decision:
    eb, xb = panel.bar(entry_bar), panel.bar(exit_bar)
    dd = Decision(symbol=sym, instant=instant, decision_ts=dec_ts,
                  decision_bar=dec_bar, decision_date=dec_bar[:10],
                  role="anchor", status="FUNDED")
    if eb is None or xb is None:
        dd.status = "BLOCKED_MISSING_BAR"
        return dd
    if d is None or d == 0:
        dd.status = "UNFUNDED_SKIP"
        return dd
    dd.direction = d
    dd.r_gross = d * (xb["last_price"] / eb["last_price"] - 1.0)
    return dd


def build_a4_p1(panel: Panel, role: str = "anchor") -> list[Decision]:
    """CNG1-A4-P1: d = sign(imb on announcement bar A); entry close A,
    exit close A+H (anchor H=6, neighbour H=12)."""
    H = 6 if role == "anchor" else 12
    out = []
    for inst in FOMC_INSTANTS:
        dt = parse_instant(inst)
        a = fmt_hour(dt)
        bar = panel.bar(a)
        imb = None if bar is None else _imb(bar)
        d = 0 if imb is None else (1 if imb > 0 else (-1 if imb < 0 else 0))
        row = _mk(panel, panel.symbol, inst, a,
                  fmt_hour(dt + timedelta(hours=1)) + ":00:00Z",
                  d, a, fmt_hour(dt + timedelta(hours=H)))
        row.role = role
        out.append(row)
    return out


def build_a4_p2(panel: Panel, role: str = "anchor") -> list[Decision]:
    """CNG1-A4-P2: d = sign(press over A-4..A-1); entry close A, exit close
    A+8 (anchor; neighbour deepens the pre-window to k=8)."""
    k = 4 if role == "anchor" else 8
    out = []
    for inst in FOMC_INSTANTS:
        dt = parse_instant(inst)
        a = fmt_hour(dt)
        press, blocked = _press(panel, a, -k, -1)
        d = 0 if blocked or press is None else (
            1 if press > 0 else (-1 if press < 0 else 0))
        row = _mk(panel, panel.symbol, inst, a,
                  fmt_hour(dt + timedelta(hours=1)) + ":00:00Z",
                  d, a, fmt_hour(dt + timedelta(hours=8)))
        row.role = role
        out.append(row)
    return out


def build_a5_p1(panel: Panel, role: str = "anchor",
                dates: Optional[list[str]] = None) -> list[Decision]:
    """CNG1-A5-P1: d = sign(press over A-8..A-3); entry close A-3 (06:00),
    exit close A-1 (08:00 delivery instant).  Neighbour deepens to A-12..A-3."""
    k_start = -8 if role == "anchor" else -12
    ds = dates or A5_P1_PINNED_QUARTERLY
    out = []
    for dstr in ds:
        a = f"{dstr}T08"
        press, blocked = _press(panel, a, k_start, -3)
        d = 0 if blocked or press is None else (
            1 if press > 0 else (-1 if press < 0 else 0))
        dt_a = parse_hour(a)
        row = _mk(panel, panel.symbol, f"{dstr}T08:00:00Z",
                  fmt_hour(dt_a - timedelta(hours=3)),
                  fmt_hour(dt_a - timedelta(hours=2)) + ":00:00Z",
                  d, fmt_hour(dt_a - timedelta(hours=3)),
                  fmt_hour(dt_a - timedelta(hours=1)))
        row.role = role
        out.append(row)
    return out


def build_a5_p2(panel: Panel, role: str = "anchor",
                dates: Optional[list[str]] = None) -> list[Decision]:
    """CNG1-A5-P2: d = -sign(imb on expiry bar A); entry close A (09:00),
    exit close A+H (anchor H=12 -> 21:00; neighbour H=4 -> 13:00)."""
    H = 12 if role == "anchor" else 4
    ds = dates or A5_P2_PINNED_NONQUARTERLY
    out = []
    for dstr in ds:
        a = f"{dstr}T08"
        dt_a = parse_hour(a)
        bar = panel.bar(a)
        imb = None if bar is None else _imb(bar)
        d = 0 if imb is None else (-1 if imb > 0 else (1 if imb < 0 else 0))
        row = _mk(panel, panel.symbol, f"{dstr}T08:00:00Z", a,
                  fmt_hour(dt_a + timedelta(hours=1)) + ":00:00Z",
                  d, a, fmt_hour(dt_a + timedelta(hours=H)))
        row.role = role
        out.append(row)
    return out


BUILDERS = {
    "CNG1-A4-P1": build_a4_p1,
    "CNG1-A4-P2": build_a4_p2,
    "CNG1-A5-P1": build_a5_p1,
    "CNG1-A5-P2": build_a5_p2,
}


def build_series(panels: dict[str, Panel], hyp: str, role: str = "anchor"
                 ) -> list[Decision]:
    """Pooled 3-symbol decision series in (symbol-major, chronological) order."""
    out = []
    for sym in SYMBOLS:
        out.extend(BUILDERS[hyp](panels[sym], role=role))
    return out


# --------------------------------------------------------------------------- #
# 5. veto panel
# --------------------------------------------------------------------------- #

@dataclass
class VetoPanel:
    """Veto shadows evaluated on a decision grid (fail-closed bookkeeping)."""
    hourly: dict[str, Callable[[str, str, int], Optional[float]]] = field(
        default_factory=dict)
    daily: dict[str, Callable[[str, str], Optional[float]]] = field(
        default_factory=dict)
    build_failures: dict[str, str] = field(default_factory=dict)
    meta: list[dict] = field(default_factory=list)

    def add(self, veto_id: str, family: str, cls: str, definition: str,
            fn=None, hourly: bool = True, coverage: str = "full grid",
            build_failure: Optional[str] = None):
        if build_failure is not None:
            self.build_failures[veto_id] = build_failure
            self.meta.append({"veto_id": veto_id, "family": family,
                              "class": cls, "definition": definition,
                              "build_status": "BUILD_FAILED",
                              "failure": build_failure,
                              "coverage": "none"})
            return
        if hourly:
            self.hourly[veto_id] = fn
        else:
            self.daily[veto_id] = fn
        self.meta.append({"veto_id": veto_id, "family": family, "class": cls,
                          "definition": definition,
                          "build_status": "BUILT", "coverage": coverage})


def build_veto_panel(panels: dict[str, Panel],
                     funding_history_path: str = DEFAULT_FUNDING_HISTORY_PATH
                     ) -> VetoPanel:
    """Minimum dispatch list: 6 V17 families + V16 daily forms + generic
    shadows, plus the remaining V17 d2 daily proxy set (full-inventory law).
    Alignment convention (inherited from V17 D2): daily veto values are dated
    D = the decision's UTC date (the V17 exposure-vs-proxy convention); hourly
    veto values are evaluated on the decision bar (closed, PIT at decision)."""
    vp = VetoPanel()
    daily = {s: daily_aggregates(panels[s]) for s in SYMBOLS}
    days = sorted(daily[SYMBOLS[0]])

    # ---- (a) V17 families -------------------------------------------------- #
    def wkndliq(sym, bar_hour, ts):
        dt = parse_hour(bar_hour)
        wd = dt.weekday()
        return -1.0 if (wd == 4 and dt.hour >= 22) or wd in (5, 6) else 0.0

    vp.add("v17_wkndliq_flag", "V17-A4-P1-WKNDLIQ", "v17_family",
           "corrected frozen spec: -1 if (Friday and hour>=22) or Saturday "
           "or Sunday else 0, on the decision bar (weekday() Mon=0..Sun=6)",
           wkndliq, hourly=True)

    def silres(sym, bar_hour, ts):
        panel = panels[sym]
        idx = panel.hours.index(bar_hour)
        if idx < 720:
            return None
        b = panel.rows[bar_hour]
        w_g = [panel.rows[h]["entry_gap_s"] for h in panel.hours[idx - 720:idx]]
        w_n = [panel.rows[h]["n_trades"] for h in panel.hours[idx - 720:idx]]
        q90 = sorted(w_g)[min(len(w_g) - 1, int(len(w_g) * 0.90))]
        med = statistics.median(w_n)
        d = (1 if b["last_price"] > b["first_price"]
             else (-1 if b["last_price"] < b["first_price"] else 0))
        return float(d) if (b["entry_gap_s"] >= q90
                            and b["n_trades"] >= 1.5 * med) else 0.0

    vp.add("v17_silres_event", "V17-A4-P2-SILRES", "v17_family",
           "dir(b) * 1[entry_gap_s(b) >= Q90(prev 720 bars) and n_trades(b) "
           ">= 1.5 * median(prev 720 bars)] on the decision bar",
           silres, hourly=True)

    # funding LEVEL (the FUNDJUMP killer, rho 0.2439 in V17) from the V17
    # endpoint pull (BTC/ETH; the family spec never had SOL).
    funding = None
    try:
        funding = json.loads(Path(funding_history_path).read_text())
    except Exception as exc:                                  # pragma: no cover
        funding = None
        vp.add("v17_fundjump_funding_level", "V17-A6-P1-FUNDJUMP",
               "v17_family",
               "funding LEVEL: last settlement rate <= decision ts "
               "(V17 funding_history.json, BTC/ETH)",
               build_failure=f"cannot read funding history: {exc}")
    if funding is not None:
        fset = {}
        for sym in ("BTCUSDT", "ETHUSDT"):
            rows = [r for r in funding.get(sym, [])
                    if _S0_START_MS <= r["fundingTime"] <= _S0_END_MS]
            rows.sort(key=lambda r: r["fundingTime"])
            fset[sym] = [(r["fundingTime"], float(r["fundingRate"]))
                         for r in rows]
        if not all(fset[s] for s in fset):
            vp.add("v17_fundjump_funding_level", "V17-A6-P1-FUNDJUMP",
                   "v17_family", "funding LEVEL (BTC/ETH)",
                   build_failure="funding history empty in window")
        else:
            def funding_level(sym, bar_hour, ts):
                if sym not in fset:
                    return None            # SOL: outside the family spec
                lo, hi = 0, len(fset[sym]) - 1
                ans = None
                while lo <= hi:
                    mid = (lo + hi) // 2
                    if fset[sym][mid][0] <= ts:
                        ans = fset[sym][mid][1]
                        lo = mid + 1
                    else:
                        hi = mid - 1
                return ans

            vp.add("v17_fundjump_funding_level", "V17-A6-P1-FUNDJUMP",
                   "v17_family",
                   "funding LEVEL: rate of last settlement with "
                   "fundingTime <= decision bar close (V17 "
                   "funding_history.json); BTC/ETH rows only -- the family "
                   "spec pools BTC/ETH and never had SOL (coverage recorded "
                   "per pair, SOL rows excluded, never imputed)",
                   funding_level, hourly=True,
                   coverage="BTCUSDT+ETHUSDT rows; SOLUSDT rows unmeasured")

    # OI endpoint (frozen CADS S4 oi_series_reduced.json) -> level + events.
    oi = getattr(build_veto_panel, "_oi_cache", None)
    if oi is None:
        vp.add("v17_oi_level", "V17-A6-P2-OICASCADE", "v17_family",
               "OI level at the H4 snapshot containing the decision bar close",
               build_failure="OI series not supplied")
        vp.add("v17_oicascade_event", "V17-A6-P2-OICASCADE", "v17_family",
               "spec event exposure (+1 for the 24h after a bottom-decile "
               "24h OI drop with negative 24h panel return)",
               build_failure="OI series not supplied")
    else:
        def oi_at(sym, ts):
            bucket = ts // H4_MS * H4_MS
            i = int((bucket - int(OI_WARMUP_START.timestamp() * 1000)) // H4_MS)
            if 0 <= i < len(oi[sym]):
                return oi[sym][i]
            return None

        def oi_level(sym, bar_hour, ts):
            v = oi_at(sym, ts)
            return None if v is None else float(v)

        vp.add("v17_oi_level", "V17-A6-P2-OICASCADE", "v17_family",
               "OI level (sum_open_interest) of the H4 snapshot containing "
               "the decision bar close, from the frozen CADS "
               "oi_series_reduced.json (V17 pull geometry: 484d x 6 H4 from "
               "2025-04-25T00Z)",
               oi_level, hourly=True)

        # OICASCADE events per the frozen spec (past-only P10 over 720 H4).
        warmup_ms = int(OI_WARMUP_START.timestamp() * 1000)
        events = {}
        for sym in SYMBOLS:
            panel = panels[sym]
            n_h4 = len(oi[sym])
            r_series = []
            for i in range(n_h4):
                ts = warmup_ms + i * H4_MS + H4_MS       # H4 close
                if i >= 6:
                    cur, prev = oi[sym][i], oi[sym][i - 6]
                    r = (cur / prev - 1.0) if prev else None
                else:
                    r = None
                r_series.append(r)
            ev = set()
            for j in range(n_h4):
                r = r_series[j]
                if r is None or j < 720:      # 120d x 6 H4 warmup (spec)
                    continue
                win = [x for x in r_series[j - 720:j] if x is not None]
                if not win:
                    continue
                p10 = sorted(win)[max(0, int(len(win) * 0.10) - 1)]
                ts = warmup_ms + j * H4_MS + H4_MS
                p_now = panel.price_at_close(ts)
                p_prev = panel.price_at_close(ts - DAY_MS)
                if p_now is None or p_prev is None or not p_prev:
                    continue
                if r <= p10 and (p_now / p_prev - 1.0) < 0:
                    ev.add(ts)
            events[sym] = sorted(ev)

        def oicascade_flag(sym, bar_hour, ts):
            return 1.0 if any(e < ts <= e + DAY_MS
                              for e in events[sym]) else 0.0

        vp.add("v17_oicascade_event", "V17-A6-P2-OICASCADE", "v17_family",
               "+1 for 24h following an H4 close whose 24h OI change <= P10 "
               "of the past 720 H4 closes AND 24h panel return < 0, else 0 "
               "(spec sign +1; the inherited V17 code painted -1 -- |rho| "
               "unaffected, discrepancy disclosed)",
               oicascade_flag, hourly=True)

    # ATTN-PHASE (daily, value dated t uses t-1): SOL vs majors 14..21 share.
    hourly_trades = {}
    for sym in SYMBOLS:
        acc: dict[str, dict[int, int]] = {}
        for h in panels[sym].hours:
            b = panels[sym].rows[h]
            acc.setdefault(b["day"], {})[parse_hour(h).hour] = (
                acc.setdefault(b["day"], {}).get(parse_hour(h).hour, 0)
                + b["n_trades"])
        hourly_trades[sym] = acc

    def attn_phase(sym, d):
        i = days.index(d)
        if i == 0:
            return None
        prev = days[i - 1]
        sol_h = hourly_trades["SOLUSDT"].get(prev, {})
        maj_h = {h: hourly_trades["BTCUSDT"].get(prev, {}).get(h, 0)
                 + hourly_trades["ETHUSDT"].get(prev, {}).get(h, 0)
                 for h in range(24)}
        ts_, tm_ = sum(sol_h.values()), sum(maj_h.values())
        if not ts_ or not tm_:
            return None
        return sum(sol_h.get(h, 0) / ts_ - maj_h[h] / tm_
                   for h in range(14, 22))

    vp.add("v17_attn_phase", "V17-a5-P1-ATTN-PHASE", "v17_family",
           "SOL US-session (14..21 UTC) trade-count share minus majors' "
           "share, day t-1 (single market-state series evaluated at every "
           "decision row's date; the V17 exposure was SOL-only)",
           attn_phase, hourly=False)

    # TICKET-BREADTH (daily, t-1): SOL avg-ticket ratio vs majors' med60.
    def ticket_breadth(sym, d):
        i = days.index(d)
        if i < 60:
            return None
        prev = days[i - 1]
        sol = daily["SOLUSDT"][prev]["avg_ticket"]
        mq = (daily["BTCUSDT"][prev]["dvol"] + daily["ETHUSDT"][prev]["dvol"])
        mn = (daily["BTCUSDT"][prev]["ntrades"]
              + daily["ETHUSDT"][prev]["ntrades"])
        if not mn:
            return None
        maj = mq / mn
        ms = statistics.median(
            daily["SOLUSDT"][x]["avg_ticket"] for x in days[i - 60:i])
        mm = statistics.median(
            (daily["BTCUSDT"][x]["dvol"] + daily["ETHUSDT"][x]["dvol"])
            / max(1, daily["BTCUSDT"][x]["ntrades"]
                  + daily["ETHUSDT"][x]["ntrades"]) for x in days[i - 60:i])
        if not ms or not mm:
            return None
        return (sol / ms) / (maj / mm)

    vp.add("v17_ticket_breadth", "V17-a5-P2-TICKET-BREADTH", "v17_family",
           "SOL avg-ticket / med60 ratio divided by majors' same ratio, "
           "day t-1 (single market-state series evaluated at every decision "
           "row's date)",
           ticket_breadth, hourly=False)

    # ---- (b) V16 daily forms ----------------------------------------------- #
    def dget(name):
        def fn(sym, d):
            i = days.index(d)
            if i < 0:
                return None
            return daily[sym][d].get(name)
        return fn

    vp.add("v16_close_displace_fade", "CRYPTO-V16-A6-V16-F1", "v16_daily_form",
           "daily (last_price - vwap)/vwap of the decision date (per symbol)",
           dget("cdf_disp"), hourly=False)
    vp.add("v16_runpersist", "CRYPTO-V16-A6-V16-F2", "v16_daily_form",
           "daily (max_run_buy - max_run_sell)/(max_run_buy + max_run_sell) "
           "of the decision date (per symbol)",
           dget("run_persist"), hourly=False)

    # ---- (c) generic shadows + full V17 d2 daily proxy set ----------------- #
    vp.add("generic_tsmom28", "GENERIC", "generic",
           "28-day cumulative daily log return through the decision date "
           "(per symbol; V17 tsmom28 definition)",
           dget("tsmom28"), hourly=False)
    vp.add("generic_dvol_level_log", "GENERIC", "generic",
           "log dollar-volume of the decision date (per symbol) -- the "
           "WKNDLIQ killer proxy",
           dget("dvol_level_log"), hourly=False)
    vp.add("generic_dvol_shock", "GENERIC", "generic",
           "decision-date dollar-volume / median of the prior 21 days "
           "(per symbol)",
           dget("dvol_shock"), hourly=False)
    for name, desc in [
            ("run_imb", "daily (buy_qty-sell_qty)/(buy_qty+sell_qty)"),
            ("taker_sat", "daily buy_count/n_trades (TAKER-SAT)"),
            ("ret", "daily log return of the decision date"),
            ("amihud", "daily |ret|/dollar-volume x 1e9 (ILLIQ class)"),
            ("avg_ticket_ratio", "avg ticket / median of prior 60 days"),
            ("elite", "daily sum of max_trade_quote (elite level)")]:
        vp.add(f"v17proxy_{name}", "V17-D2-PROXY", "v17_d2_proxy_set",
               f"{desc} (per symbol, decision date)", dget(name),
               hourly=False)

    # day-of-week dummies (7) -- evaluated on the decision date
    for wd in range(7):
        def dow_fn(sym, d, _wd=wd):
            return 1.0 if date.fromisoformat(d).weekday() == _wd else 0.0
        vp.add(f"generic_dow_{wd}", "GENERIC", "generic_dummy",
               f"1 if decision-date weekday()=={wd} "
               f"({['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][wd]})",
               dow_fn, hourly=False)

    # session dummies -- evaluated on the decision hour (decision bar)
    for sid, lo, hi in [("us", 13, 21), ("eu", 7, 15), ("asia", 0, 7)]:
        def sess_fn(sym, bar_hour, ts, _lo=lo, _hi=hi):
            return 1.0 if _lo <= parse_hour(bar_hour).hour <= _hi else 0.0
        vp.add(f"generic_session_{sid}", "GENERIC", "generic_dummy",
               f"1 if the decision bar hour is in [{lo:02d},{hi:02d}] UTC "
               "else 0", sess_fn, hourly=True)

    def weekend_fn(sym, bar_hour, ts):
        return 1.0 if parse_hour(bar_hour).weekday() in (5, 6) else 0.0

    vp.add("generic_weekend_flag", "GENERIC", "generic_dummy",
           "1 if the decision bar lands on Saturday/Sunday else 0",
           weekend_fn, hourly=True)

    return vp


def supply_oi(oi):
    """Attach the frozen OI series (runner calls this before build_veto_panel)."""
    build_veto_panel._oi_cache = oi


# --------------------------------------------------------------------------- #
# 6. measurement assembly
# --------------------------------------------------------------------------- #

REQUIRED_VETOES = [
    "v17_wkndliq_flag", "v17_silres_event", "v17_fundjump_funding_level",
    "v17_oi_level", "v17_oicascade_event", "v17_attn_phase",
    "v17_ticket_breadth",                       # (a) six V17 families
    "v16_close_displace_fade", "v16_runpersist",          # (b) V16 forms
    "generic_tsmom28", "generic_dvol_level_log", "generic_dvol_shock",   # (c)
    "generic_dow_0", "generic_dow_1", "generic_dow_2", "generic_dow_3",
    "generic_dow_4", "generic_dow_5", "generic_dow_6",
    "generic_session_us", "generic_session_eu", "generic_session_asia",
    "generic_weekend_flag",
]


def evaluate_pairs(decisions: list[Decision], vp: VetoPanel) -> dict:
    """All veto pairs for one decision series, pooled across symbols."""
    sig = [d.r_gross for d in decisions]
    out = {}
    for veto_id, fn in vp.hourly.items():
        vals = []
        for d in decisions:
            t = panels_ts_lookup(d)
            vals.append(None if t is None else
                        fn(d.symbol, d.decision_bar, t))
        out[veto_id] = rho_pair_status(sig, vals)
    for veto_id, fn in vp.daily.items():
        vals = [fn(d.symbol, d.decision_date) for d in decisions]
        out[veto_id] = rho_pair_status(sig, vals)
    return out


_TS_CACHE: dict[tuple[str, str], int] = {}


def register_panel_ts(panels: dict[str, Panel]):
    for sym, p in panels.items():
        for h in p.hours:
            _TS_CACHE[(sym, h)] = p.rows[h]["last_ts_ms"]


def panels_ts_lookup(d: Decision) -> Optional[int]:
    return _TS_CACHE.get((d.symbol, d.decision_bar))


def novelty_verdict(pairs: dict, vp: VetoPanel) -> dict:
    """Mechanical proposal-level novelty verdict (fail-closed on unbuilt
    REQUIRED vetoes; VETO on any measured pair over the bar)."""
    missing_required = [v for v in REQUIRED_VETOES
                        if v in vp.build_failures]
    if missing_required:
        return {"novelty_verdict": "INELIGIBLE_FAIL_CLOSED",
                "reason": "required veto(s) could not be rebuilt: "
                          + ", ".join(missing_required),
                "worst_pair": None, "worst_abs_rho": None,
                "margin_to_bar": None, "vetoed_pairs": []}
    measured = {k: v for k, v in pairs.items() if v["status"] == "MEASURED"}
    vetoed = [k for k, v in measured.items()
              if v["pair_verdict"] == "VETO"]
    if measured:
        worst = max(measured.items(), key=lambda kv: kv[1]["max_abs_rho"])
        return {"novelty_verdict": ("VETO_MEASURED" if vetoed
                                    else "NOVELTY_PASS"),
                "vetoed_pairs": vetoed,
                "worst_pair": worst[0],
                "worst_abs_rho": worst[1]["max_abs_rho"],
                "margin_to_bar": worst[1]["margin_to_bar"]}
    return {"novelty_verdict": "INELIGIBLE_FAIL_CLOSED",
            "reason": "no veto pair measurable on the declared grid",
            "worst_pair": None, "worst_abs_rho": None,
            "margin_to_bar": None, "vetoed_pairs": []}


def f5_collapse(series_a: list[Decision], series_b: list[Decision]) -> dict:
    """F5 pooled |rho| between two anchor return vectors on shared grid keys
    ((symbol, instant)); disjoint grids are recorded, never forced."""
    ka = {(d.symbol, d.instant): d for d in series_a}
    kb = {(d.symbol, d.instant): d for d in series_b}
    shared = [k for k in ka if k in kb]
    if not shared:
        return {"status": "NOT_COMPUTABLE_GRID_DISJOINT",
                "shared_grid_keys": 0,
                "n_a": len(ka), "n_b": len(kb),
                "max_abs_rho": None, "margin_to_bar": None,
                "f5_fired": False}
    xs = [ka[k].r_gross if ka[k].status == "FUNDED" else None
          for k in shared]
    ys = [kb[k].r_gross if kb[k].status == "FUNDED" else None
          for k in shared]
    res = rho_pair_status(xs, ys)
    return {"status": res["status"], "shared_grid_keys": len(shared),
            "n_a": len(ka), "n_b": len(kb),
            "max_abs_rho": res["max_abs_rho"],
            "margin_to_bar": res["margin_to_bar"],
            "f5_fired": bool(res["max_abs_rho"] is not None
                             and res["max_abs_rho"] > VETO_BAR)}


def date_disjoint(dates_a: list[str], dates_b: list[str]) -> dict:
    inter = sorted(set(dates_a) & set(dates_b))
    return {"n_a": len(set(dates_a)), "n_b": len(set(dates_b)),
            "intersection": inter, "disjoint": not inter}


# --------------------------------------------------------------------------- #
# 7. feasibility (counts + ceilings only; no PnL)
# --------------------------------------------------------------------------- #

#: Referenced cost ceiling from the V17 kernel inheritance (NOT invented
#: here): measured taker+spread stress tier 2.0 round-trip per event.
COST_REFERENCE = {
    "tier": "2.0",
    "round_trip_bps": 24.0,
    "source": ("inherited V17 d2_a9f_feasibility_v17.json "
               "(per_proposal.*.cost_ceiling: 'per-event round trip tier2.0 "
               "~= 24bps'); the NG1 P1 kernel adoption re-measures the "
               "schedule; measured beats referenced"),
}


def recent_window_bounds(months: int = Q6_RECENT_WINDOW_MONTHS
                         ) -> tuple[str, str]:
    """Last N calendar months of the panel window (inclusive date bounds)."""
    end = PANEL_WINDOW_END.date()
    m = end.month - months
    y = end.year
    while m <= 0:
        m += 12
        y -= 1
    start = date(y, m, min(end.day, _calendar.monthrange(y, m)[1]))
    return start.isoformat(), end.isoformat()


def feasibility_for(hyp: str, anchor: list[Decision],
                    neighbour: Optional[list[Decision]] = None) -> dict:
    rstart, rend = recent_window_bounds()
    funded = [d for d in anchor if d.status == "FUNDED"]
    skips = [d for d in anchor if d.status == "UNFUNDED_SKIP"]
    blocked = [d for d in anchor if d.status == "BLOCKED_MISSING_BAR"]
    recent = [d for d in funded if rstart <= d.decision_date <= rend]
    fills_window = 2 * len(funded)
    months_total = ((PANEL_WINDOW_END - PANEL_WINDOW_START).days + 1) / 30.4375
    declared_counts = {"CNG1-A4-P1": 24, "CNG1-A4-P2": 24,
                       "CNG1-A5-P1": 12, "CNG1-A5-P2": 24}
    return {
        "total_window": {
            "instants": len({d.instant for d in anchor}),
            "symbols": len({d.symbol for d in anchor}),
            "funded_decisions_measured": len(funded),
            "declared_decision_count": declared_counts[hyp],
            "declared_match": len(funded) == declared_counts[hyp],
            "unfunded_tie_skips": len(skips),
            "blocked_missing_bar": len(blocked),
        },
        "recent_window": {
            "definition": (f"last {Q6_RECENT_WINDOW_MONTHS} calendar months "
                           f"of the panel window: {rstart}..{rend} "
                           "(decision-date within bounds)"),
            "start": rstart, "end": rend,
            "anchor_decisions": len(recent),
            "floor": Q6_ANCHOR_FLOOR,
            "verdict": "PASS" if len(recent) >= Q6_ANCHOR_FLOOR else "FAIL",
        },
        "turnover": {
            "fills_per_funded_decision": 2,
            "anchor_fills_per_window": fills_window,
            "anchor_fills_per_month_approx": round(
                fills_window / months_total, 2),
            "note": ("unit notional 1.0 per decision; entry+exit only; no "
                     "interim rebalancing exists in the representation"),
        },
        "cost_ceiling_reference": dict(COST_REFERENCE),
        "a9f_verdict": (
            "TURNOVER_LOW_CEILING_REFERENCED: measured fills/window and the "
            "referenced tier-2.0 round-trip are recorded; the cost-vs-gross-"
            "move adjudication is the scoring lane's F4 gate and is NOT "
            "computed here (outcome-leak ban)"),
    }


# --------------------------------------------------------------------------- #
# 8. expiry-instant re-verification (fail-closed, lane A5)
# --------------------------------------------------------------------------- #

def reverify_expiry_instants() -> dict:
    """Rebuild delivery/expiry instants by calendar arithmetic and check them
    against every pinned number in the A5 proposals.  Any mismatch is a
    fail-closed INELIGIBLE for lane A5."""
    start, end = PANEL_WINDOW_START.date(), PANEL_WINDOW_END.date()
    monthly = monthly_last_fridays(start, end)
    quarterly = [d for d in monthly if d.month in (3, 6, 9, 12)]
    nonquarterly = [d for d in monthly if d.month not in (3, 6, 9, 12)]

    def iso(ds):
        return [d.isoformat() for d in ds]

    checks = {
        "monthly_all_fridays": all(d.weekday() == 4 for d in monthly),
        "quarterly_matches_pinned_A5_P1": (
            iso(quarterly) == sorted(A5_P1_PINNED_QUARTERLY)),
        "nonquarterly_matches_pinned_A5_P2": (
            iso(nonquarterly) == sorted(A5_P2_PINNED_NONQUARTERLY)),
        "monthly_count_in_window": len(monthly),
        "venue_epoch_checks": {},
        "deribit_date_checks": {},
    }
    for name, ms in VENUE_PINNED_EPOCHS_MS.items():
        dt = epoch_ms_to_utc(ms)
        lf = last_friday(dt.year, dt.month)
        checks["venue_epoch_checks"][name] = {
            "epoch_ms": ms,
            "converted_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "hour_is_08_utc": dt.hour == 8,
            "is_last_friday_of_its_month": dt.date() == lf,
            "pass": dt.hour == 8 and dt.date() == lf,
        }
    for ds in VENUE_PINNED_DERIBIT_DATES:
        d = date.fromisoformat(ds)
        checks["deribit_date_checks"][ds] = {
            "weekday": d.strftime("%a"),
            "is_last_friday_of_its_month": d == last_friday(d.year, d.month),
        }
    all_pass = (
        checks["monthly_all_fridays"]
        and checks["quarterly_matches_pinned_A5_P1"]
        and checks["nonquarterly_matches_pinned_A5_P2"]
        and all(c["pass"] for c in checks["venue_epoch_checks"].values())
        and all(c["is_last_friday_of_its_month"]
                for c in checks["deribit_date_checks"].values()))
    return {
        "rule": ("delivery/expiry instant = 08:00:00 UTC on the LAST FRIDAY "
                 "of the month; quarterly futures only in Mar/Jun/Sep/Dec; "
                 "monthly options every month's last Friday"),
        "derived_in_window": {
            "monthly_last_fridays": iso(monthly),
            "quarterly": iso(quarterly),
            "nonquarterly": iso(nonquarterly),
        },
        "holiday_leak_handling": {
            "hazard_dates": HOLIDAY_HAZARD_DATES,
            "declared_handling": ("retained in the decision grids (no drop, "
                                  "no shift); liquidity-level leakage is "
                                  "measured by the dvol veto rows "
                                  "(generic_dvol_level_log / "
                                  "generic_dvol_shock) exactly as the "
                                  "proposals' F3 declarations require"),
        },
        "checks": checks,
        "verdict": "MATCH" if all_pass else "MISMATCH",
        "fail_closed_consequence": (
            "MISMATCH -> lane A5 proposals INELIGIBLE_FAIL_CLOSED (rule or "
            "holiday handling does not reproduce the pinned numbers)"),
    }
