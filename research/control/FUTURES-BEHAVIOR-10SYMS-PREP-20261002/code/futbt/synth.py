"""Deterministic synthetic-fixture generator.

Generates a small synthetic futures universe and writes it in the EXACT raw
IBKR JSON format (same header fields, same filename pattern) so the adapter,
roll engine, cost model and replay engine are tested against the real file
schema — offline, with known ground truth.

Known ground truth exposed for assertions:
  * closes per (symbol, conid, session) — expected roll gaps derivable;
  * expected calendar roll sessions (last weekday before day-1 of each
    contract's expiry month);
  * the CL-like symbol includes a NEGATIVE price episode;
  * deep-history bars are close-only settlement bars (v=0, o=h=l=c),
    replicating the measured raw pathology;
  * BID/ASK daily files carry v=-1/wap=-1.0/n=-1 like real quote bars;
  * per-contract volume follows a front-migration shape, so the PIT
    VolumeRollRule triggers materially earlier than the calendar baseline.

DST is NOT modeled (fixed UTC offset in intraday fixtures) — the real
exchange calendar/DST handling is a NOT_RUN placeholder (calendarx.py).
"""
from __future__ import annotations

import datetime as dt
import json
import random
from dataclasses import dataclass, field
from pathlib import Path

from .calendarx import WeekdayCalendar
from .instruments import MONTH_CODES, MONTH_OF_CODE

FIXTURE_FETCHED_UTC = "2026-10-02T00:00:00Z"


@dataclass(frozen=True)
class SynthContractSpec:
    local_symbol: str
    conid: int
    expiry_month: tuple[int, int]        # (year, month) of last-trade month E
    last_trade_date: dt.date


@dataclass
class SynthSymbolSpec:
    symbol: str
    exchange: str
    tz: str
    multiplier: float
    min_tick: float
    start_level: float
    daily_sigma: float                   # absolute price sigma per session
    step_offset: float                   # calendar level offset per contract
    letter_offset_months: int            # +1 for NYMEX delivery convention
    expiry_months: list[tuple[int, int]]
    conid_base: int
    contracts: list[SynthContractSpec] = field(default_factory=list)


def _nth_weekday_of(year: int, month: int, day: int) -> dt.date:
    """Clamp `day` into the month, then shift back to a weekday."""
    import calendar as _cal
    last = _cal.monthrange(year, month)[1]
    d = dt.date(year, month, min(day, last))
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return d


def _month_add(ym: tuple[int, int], k: int) -> tuple[int, int]:
    y, m = ym
    t = y * 12 + (m - 1) + k
    return (t // 12, t % 12 + 1)


def _local_symbol(sym_spec: SynthSymbolSpec, e: tuple[int, int]) -> str:
    letter_ym = _month_add(e, sym_spec.letter_offset_months)
    code = MONTH_CODES[letter_ym[1] - 1]
    if sym_spec.symbol == "NG":  # 2-digit-year family
        return f"{sym_spec.symbol}{code}{letter_ym[0] % 100:02d}"
    return f"{sym_spec.symbol}{code}{letter_ym[0] % 10}"


def build_symbol_specs() -> dict[str, SynthSymbolSpec]:
    """Three symbols exercising the interesting corners of the real table:
    CL (negative prices, 0.01 tick), 6J (USD-per-JPY, 5e-7 tick), ES
    (0.25 tick, quarterly)."""
    quarterly: list[tuple[int, int]] = []
    y, m = 2024, 9
    while (y, m) <= (2026, 12):
        quarterly.append((y, m))
        y, m = _month_add((y, m), 3)
    monthly: list[tuple[int, int]] = []
    y, m = 2024, 10
    while (y, m) <= (2026, 12):
        monthly.append((y, m))
        y, m = _month_add((y, m), 1)

    def mk(symbol, exchange, tz, mult, tick, level, sigma, step, letter_off,
           months, conid_base, ltd_day):
        spec = SynthSymbolSpec(
            symbol=symbol, exchange=exchange, tz=tz, multiplier=mult,
            min_tick=tick, start_level=level, daily_sigma=sigma,
            step_offset=step, letter_offset_months=letter_off,
            expiry_months=months, conid_base=conid_base)
        spec.contracts = [
            SynthContractSpec(
                local_symbol=_local_symbol(spec, e),
                conid=conid_base + 137 * (i + 1),
                expiry_month=e,
                last_trade_date=_nth_weekday_of(e[0], e[1], ltd_day))
            for i, e in enumerate(months)
        ]
        return spec

    return {
        "CL": mk("CL", "NYMEX", "US/Eastern", 1000, 0.01, 80.0, 1.2, -0.40, 1,
                 monthly, 704_000_000, 20),
        "6J": mk("6J", "CME", "US/Central", 12_500_000, 5e-07, 0.0065,
                 0.00006, 0.00002, 0, quarterly, 881_100_000, 19),
        "ES": mk("ES", "CME", "US/Central", 50, 0.25, 5000.0, 38.0, 6.0, 0,
                 quarterly, 563_900_000, 18),
    }


def _round_tick(price: float, tick: float) -> float:
    return round(round(price / tick) * tick, 12)


def _volume_shape(mte: int) -> float:
    """Relative volume by months-to-expiry (mte) of the contract's expiry
    month E: dies inside E, peaks at mte==2, migrates during mte==1."""
    table = {0: 0.02, 1: 0.60, 2: 1.00, 3: 0.45, 4: 0.20}
    if mte in table:
        return table[mte]
    return max(0.02, 0.20 - 0.02 * (mte - 4))


@dataclass
class SynthUniverse:
    raw_dir: Path
    calendar: WeekdayCalendar
    specs: dict[str, SynthSymbolSpec]
    sessions: list[dt.date]
    closes: dict[tuple[str, int], dict[dt.date, float]]  # (sym, conid) -> close
    files_written: list[str] = field(default_factory=list)

    def close(self, symbol: str, conid: int, session: dt.date) -> float | None:
        return self.closes.get((symbol, conid), {}).get(session)

    def expected_calendar_rolls(self, symbol: str
                                 ) -> list[tuple[dt.date, int, int]]:
        """(decision_session, old_conid, new_conid) per declared baseline:
        last session before day-1 of each contract's expiry month E."""
        out = []
        cons = self.specs[symbol].contracts
        for a, b in zip(cons, cons[1:]):
            y, m = a.expiry_month
            day1 = dt.date(y, m, 1)
            t = self.calendar.last_session_before(day1)
            out.append((t, a.conid, b.conid))
        return out


def _gen_symbol_prices(spec: SynthSymbolSpec, sessions: list[dt.date],
                       rng: random.Random
                       ) -> dict[int, dict[dt.date, dict[str, float]]]:
    """level walk + per-contract offsets -> OHLCV per contract per session."""
    level = spec.start_level
    levels: dict[dt.date, float] = {}
    neg_window = (dt.date(2025, 3, 3), dt.date(2025, 3, 14))  # CL episode
    for s in sessions:
        level += rng.gauss(0.0, spec.daily_sigma)
        if spec.symbol == "CL" and neg_window[0] <= s <= neg_window[1]:
            # deterministic negative-price episode (Apr-2020 style)
            level -= 12.0
        levels[s] = level
    out: dict[int, dict[dt.date, dict[str, float]]] = {}
    for k, con in enumerate(spec.contracts):
        offset = spec.step_offset * k
        bars: dict[dt.date, dict[str, float]] = {}
        prev_close = None
        for s in sessions:
            if s > con.last_trade_date:
                continue
            listing = dt.date(*_month_add(con.expiry_month, -9), 1)
            if s < listing:
                continue
            c = levels[s] + offset + rng.gauss(0.0, spec.daily_sigma * 0.05)
            c = _round_tick(c, spec.min_tick)
            o = (prev_close if prev_close is not None else c)
            o = _round_tick(o + rng.gauss(0.0, spec.daily_sigma * 0.1),
                            spec.min_tick)
            spread_px = abs(rng.gauss(spec.daily_sigma * 0.6,
                                      spec.daily_sigma * 0.05))
            h = _round_tick(max(o, c) + spread_px, spec.min_tick)
            l = _round_tick(min(o, c) - spread_px, spec.min_tick)
            mte = (con.expiry_month[0] - s.year) * 12 \
                + con.expiry_month[1] - s.month
            live_depth = con.last_trade_date - dt.timedelta(days=140)
            if s < live_depth:
                # deep-history pathology: close-only settlement bar, v=0
                bars[s] = {"o": c, "h": c, "l": c, "c": c, "v": 0}
            else:
                vol = max(1, int(12000 * _volume_shape(mte)
                                 * rng.uniform(0.7, 1.3)))
                bars[s] = {"o": o, "h": h, "l": l, "c": c, "v": vol}
            prev_close = c
        out[con.conid] = bars
    return out


def _write_file(path: Path, spec: SynthSymbolSpec, con: SynthContractSpec,
                what: str, bar_token: str, bar_size: str, span: str,
                rows: list[dict]) -> None:
    dur = {"6Y": "6 Y", "1Y": "1 Y", "30D": "30 D", "2D": "2 D",
           "3D": "3 D"}[span]
    doc = {
        "fetched_utc": FIXTURE_FETCHED_UTC,
        "symbol": spec.symbol,
        "conId": con.conid,
        "localSymbol": con.local_symbol,
        "expiry_month": con.last_trade_date.strftime("%Y%m%d"),
        "exchange": spec.exchange,
        "whatUse": what,
        "barSize": bar_size,
        "durationStr": dur,
        "endDateTime": "",
        "useRTH": True,
        "endpoint": "synthetic-fixture (deterministic)",
        "timeZoneId": spec.tz,
        "ok": True,
        "errors": [],
        "exception": None,
        "n_rows": len(rows),
        "bars": rows,
    }
    path.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")


def build_universe(raw_dir: str | Path, seed: int = 20261002,
                   start: dt.date = dt.date(2024, 7, 1),
                   end: dt.date = dt.date(2026, 9, 30)) -> SynthUniverse:
    """Build the deterministic synthetic universe and write raw-format files.

    Idempotent for the same (seed, start, end): overwrites files in raw_dir.
    """
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    cal = WeekdayCalendar(start, end)
    sessions = cal.sessions()
    specs = build_symbol_specs()
    uni = SynthUniverse(raw_dir=raw_dir, calendar=cal, specs=specs,
                        sessions=sessions, closes={})

    half_spread_ticks = {"CL": 1, "6J": 2, "ES": 1}
    for sym, spec in specs.items():
        rng = random.Random(f"futbt-synth:{seed}:{sym}")
        bars_by_con = _gen_symbol_prices(spec, sessions, rng)
        for con in spec.contracts:
            bars = bars_by_con[con.conid]
            uni.closes[(sym, con.conid)] = {s: b["c"] for s, b in bars.items()}
            rows = [{"t": s.isoformat(), "o": b["o"], "h": b["h"],
                     "l": b["l"], "c": b["c"], "v": b["v"],
                     "wap": b["c"], "n": max(0, int(b["v"] * 0.6))}
                    for s, b in sorted(bars.items())]
            name = f"{sym}_{con.local_symbol}_{con.conid}_TRADES_1day_6Y.json"
            _write_file(raw_dir / name, spec, con, "TRADES", "1day", "1 day",
                        "6Y", rows)
            uni.files_written.append(name)

            # BID/ASK daily for contracts whose life intersects the last
            # 252 sessions (mirrors the 1Y quote depth of the real snapshot)
            recent = set(sessions[-252:])
            if recent & set(bars):
                half = half_spread_ticks[sym] * spec.min_tick
                for what, shift in (("BID", -half), ("ASK", +half)):
                    qrows = [{"t": s.isoformat(),
                              "o": _round_tick(b["o"] + shift, spec.min_tick),
                              "h": _round_tick(b["h"] + shift, spec.min_tick),
                              "l": _round_tick(b["l"] + shift, spec.min_tick),
                              "c": _round_tick(b["c"] + shift, spec.min_tick),
                              "v": -1, "wap": -1.0, "n": -1}
                             for s, b in sorted(bars.items()) if s in recent]
                    name = (f"{sym}_{con.local_symbol}_{con.conid}_{what}"
                            f"_1day_1Y.json")
                    _write_file(raw_dir / name, spec, con, what, "1day",
                                "1 day", "1Y", qrows)
                    uni.files_written.append(name)

        # small intraday files for the two most recent contracts (adapter
        # coverage only; fixed -04:00 offset, DST NOT modeled)
        for con in spec.contracts[-2:]:
            bars = bars_by_con[con.conid]
            last_days = sorted(bars)[-3:]
            h1rows, m1rows = [], []
            for s in last_days:
                base = bars[s]["c"]
                for hh in range(9, 16):
                    for mm in (0, 30):
                        px = _round_tick(base * (1 + rng.gauss(0, 0.0005)),
                                         spec.min_tick)
                        t = f"{s.isoformat()}T{hh:02d}:{mm:02d}:00-04:00"
                        if mm == 0:
                            h1rows.append({"t": t, "o": px, "h": px, "l": px,
                                           "c": px, "v": 100, "wap": px, "n": 60})
                        m1rows.append({"t": t, "o": px, "h": px, "l": px,
                                       "c": px, "v": 40, "wap": px, "n": 25})
            if h1rows:
                name = f"{sym}_{con.local_symbol}_{con.conid}_TRADES_1hour_30D.json"
                _write_file(raw_dir / name, spec, con, "TRADES", "1hour",
                            "1 hour", "30D", h1rows)
                uni.files_written.append(name)
            if m1rows:
                name = f"{sym}_{con.local_symbol}_{con.conid}_TRADES_1min_2D.json"
                _write_file(raw_dir / name, spec, con, "TRADES", "1min",
                            "1 min", "2D", m1rows)
                uni.files_written.append(name)

        # one `_front_` marker file (front snapshot convention in raw dir)
        con = spec.contracts[-1]
        bars = bars_by_con[con.conid]
        rows = [{"t": s.isoformat(), "o": b["o"], "h": b["h"], "l": b["l"],
                 "c": b["c"], "v": b["v"], "wap": b["c"], "n": 1}
                for s, b in sorted(bars.items())[-3:]]
        name = f"{sym}_{con.local_symbol}_{con.conid}_front_TRADES_1day_3D.json"
        _write_file(raw_dir / name, spec, con, "TRADES", "1day", "1 day",
                    "3D", rows)
        uni.files_written.append(name)
    return uni


FIXTURE_DESCRIPTION = {
    "name": "futbt synthetic futures universe",
    "determinism": "random.Random(str seed) per symbol; same seed -> "
                   "byte-identical files (sha-stable across runs/platforms)",
    "sessions": "Mon-Fri weekday calendar, no holidays, DST NOT modeled",
    "symbols": {
        "CL": "monthly expiries, 0.01 tick, NEGATIVE price episode "
              "2025-03-03..2025-03-14 (closes below zero)",
        "6J": "quarterly, USD-per-JPY quote scale (~0.0065), 5e-7 tick",
        "ES": "quarterly, 0.25 tick, positive prices only",
    },
    "pathologies_replicated": [
        "deep-history bars are close-only settlement bars (o=h=l=c, v=0) "
        "before last_trade_date - 140 days",
        "BID/ASK quote bars carry v=-1/wap=-1.0/n=-1",
        "volume migrates to the next contract ~1 month before the calendar "
        "roll date (volume rule rolls earlier than calendar rule)",
        "filename conventions incl. NG-style 2-digit years are not present "
        "here (NG not in fixture) but are covered by unit tests on the parser",
    ],
    "known_truth": "SynthUniverse.closes + expected_calendar_rolls() let tests "
                   "verify the roll engine exactly (sessions, gaps, factors)",
}
