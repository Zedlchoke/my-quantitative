"""SYNTHETIC deterministic DBN fixture generator — GLBX.MDP3-shaped.

ALL data produced here is fabricated (labeled synthetic=True in the
manifest; file names carry `synthetic`). It contains NO real market data
and no real prices; patterns are arithmetic. Its purpose is to exercise
the ingestion adapter against the exact DBN v3 wire shape plus the
adversarial behaviors the 10-symbol program must survive:

  * all 10 roots' venue-native raw_symbols (NQZ6, ESH7, CLZ6, CLF7, ...)
  * normal sessions + the 2026 America/Chicago DST transitions
    (spring forward 2026-03-08; fall back 2026-11-01 inside the roll window)
  * a holiday short session (declared early close 12:00 CT on 2026-04-03)
  * a roll-critical window: CLZ6 -> CLF7 volume crossover 2026-11-02 and
    open-interest crossover 2026-11-05 (OI lags volume, as measured in
    real markets), spanning the fall-back DST change
  * a NEGATIVE-price CL day (2026-03-13: low -3.00, close -2.75, negative
    settlement), preserved as exact negative int nanos
  * crossed (bid>ask) and locked (bid==ask) BBO moments in mbp-1/bbo-1m
  * duplicate ts_event bars + no-trade minute gaps (Databento ohlcv is
    sparse by design: no trade -> no bar)
  * a 6J USD-per-JPY scale session (~0.006335, tick 5e-7 = 500 nanos)
  * close-only-ish sessions: sessions with a statistics settlement but NO
    ohlcv bar at all (the Databento-native form of the close-only
    pathology), plus one stale 1m bar (o=h=l=c=prev close, v=1)
  * definition add/modify/delete actions; preliminary->final settlement
    revision; a continuous (CL.c.0) file for the execution guard

Deterministic: same seed -> byte-identical files.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

from . import spec as S
from .wire import DbnMetadata, MappingInterval, SymbolMapping, write_dbn

CHICAGO = ZoneInfo("America/Chicago")
UTC = dt.timezone.utc

FIXTURE_SEED = 20261002
PUBLISHER_ID = 1
INSTRUMENT_ID_BASE = 1_000_000
CONTINUOUS_INSTRUMENT_ID = 9_990_001

SYNTHETIC_LABEL = "SYNTHETIC FIXTURE - fabricated data, not real market data"

NEG_DAY = "2026-03-13"


def ct(y, mo, d, h, mi, s=0) -> int:
    """Chicago wall-clock -> UTC ns (DST-correct via zoneinfo)."""
    t = dt.datetime(y, mo, d, h, mi, s, tzinfo=CHICAGO)
    return int(t.timestamp()) * 1_000_000_000


def utc_ns(y, mo, d, h, mi, s=0) -> int:
    return int(dt.datetime(y, mo, d, h, mi, s, tzinfo=UTC).timestamp()) * 1_000_000_000


def date_str(d: dt.date) -> str:
    return d.isoformat()


class _Rng:
    """xorshift64 - deterministic, synthetic-only."""

    def __init__(self, seed: int):
        self.s = (seed or 1) & 0xFFFFFFFFFFFFFFFF

    def next_u64(self) -> int:
        x = self.s
        x ^= (x << 13) & 0xFFFFFFFFFFFFFFFF
        x ^= x >> 7
        x ^= (x << 17) & 0xFFFFFFFFFFFFFFFF
        self.s = x
        return x

    def below(self, n: int) -> int:
        return self.next_u64() % max(1, n)


# ---------------------------------------------------------------------------
# synthetic instrument table for the 10 roots (tick/multiplier mirror the
# program's OBSERVED S1 identity values; everything else is fabricated)
# ---------------------------------------------------------------------------

ROOT_SPECS: dict[str, dict] = {
    "NQ": dict(exchange="CME", tick=250_000_000, mult=20 * 10**9, base=17_350_250_000_000, months="HMUZ"),
    "ES": dict(exchange="CME", tick=250_000_000, mult=50 * 10**9, base=4_825_000_000_000, months="HMUZ"),
    "CL": dict(exchange="NYMEX", tick=10_000_000, mult=1000 * 10**9, base=58_250_000_000, months="FGHJKMNQUVXZ"),
    "NG": dict(exchange="NYMEX", tick=1_000_000, mult=10_000 * 10**9, base=4_120_000_000, months="FGHJKMNQUVXZ"),
    "GC": dict(exchange="COMEX", tick=100_000_000, mult=100 * 10**9, base=2_915_500_000_000, months="GJMQZV"),
    "SI": dict(exchange="COMEX", tick=5_000_000, mult=5000 * 10**9, base=32_450_000_000, months="HKNUZ"),
    "6E": dict(exchange="CME", tick=50_000, mult=125_000 * 10**9, base=1_084_500_000, months="HMUZ"),
    "6J": dict(exchange="CME", tick=500, mult=12_500_000 * 10**9, base=6_335_000, months="HMUZ"),
    "6B": dict(exchange="CME", tick=100_000, mult=62_500 * 10**9, base=1_296_500_000, months="HMUZ"),
    "6A": dict(exchange="CME", tick=100_000, mult=100_000 * 10**9, base=650_500_000, months="HMUZ"),
}

MONTH_OF_CODE = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}


@dataclass
class ContractTruth:
    raw_symbol: str
    root: str
    instrument_id: int
    tick_nanos: int
    unit_of_measure_qty_nanos: int
    exchange: str
    maturity_year: int
    maturity_month: int
    activation_ns: int
    expiration_ns: int
    actions: list = field(default_factory=list)   # [(ts, 'A'|'M'|'D')]


@dataclass
class SessionTruth:
    date: str
    open_utc_ns: int
    close_utc_ns: int
    kind: str                                  # NORMAL | HOLIDAY_SHORT | DST_SHIFTED


@dataclass
class FixtureUniverse:
    out_dir: str
    seed: int
    files: dict = field(default_factory=dict)           # name -> abs path
    contracts: dict = field(default_factory=dict)       # raw_symbol -> ContractTruth
    minute_sessions: dict = field(default_factory=dict) # raw_symbol -> [SessionTruth]
    daily_bars: dict = field(default_factory=dict)      # raw_symbol -> {date: bar dict}
    absent_sessions: dict = field(default_factory=dict) # raw_symbol -> [date] settlement-only
    settlements: dict = field(default_factory=dict)     # raw_symbol -> {date: [(pub,px,final)]}
    oi_roll: dict = field(default_factory=dict)         # date -> {raw: qty} + 'crossover'
    volume_roll: dict = field(default_factory=dict)     # date -> {old,new} + 'crossover'
    bbo_states: list = field(default_factory=list)      # (ts, 'NORMAL'|'CROSSED'|'LOCKED')
    trade_join_truth: list = field(default_factory=list)  # (trade_ts, expected_kind)
    duplicate_bars: dict = field(default_factory=dict)  # raw_symbol -> [ts]
    minute_gaps: dict = field(default_factory=dict)     # raw_symbol -> [missing minute ts]
    stale_bar: dict = field(default_factory=dict)       # raw_symbol -> ts
    continuous: dict = field(default_factory=dict)      # {symbol, intervals}

    def to_json_dict(self) -> dict:
        return {
            "synthetic": True,
            "label": SYNTHETIC_LABEL,
            "seed": self.seed,
            "files": dict(self.files),
            "contracts": {k: {**vars(v), "actions": [list(a) for a in v.actions]}
                          for k, v in self.contracts.items()},
            "minute_sessions": {k: [vars(s) for s in v] for k, v in self.minute_sessions.items()},
            "daily_bars": {k: {d: dict(b) for d, b in v.items()} for k, v in self.daily_bars.items()},
            "absent_sessions": self.absent_sessions,
            "settlements": self.settlements,
            "oi_roll": self.oi_roll,
            "volume_roll": self.volume_roll,
            "bbo_states": [(t, s) for t, s in self.bbo_states],
            "trade_join_truth": [(t, k) for t, k in self.trade_join_truth],
            "duplicate_bars": self.duplicate_bars,
            "minute_gaps": self.minute_gaps,
            "stale_bar": self.stale_bar,
            "continuous": self.continuous,
        }


# ---------------------------------------------------------------------------
# contract universe
# ---------------------------------------------------------------------------

def _contracts() -> dict[str, ContractTruth]:
    listed = [
        ("NQ", "Z", 2026), ("ES", "Z", 2026),
        ("CL", "Z", 2026), ("CL", "F", 2027),
        ("NG", "F", 2027), ("GC", "Z", 2026), ("SI", "Z", 2026),
        ("6E", "Z", 2026), ("6J", "Z", 2026), ("6B", "Z", 2026), ("6A", "F", 2027),
        ("CL", "V", 2026),   # expired Oct-2026 contract: gets a DELETE action
    ]
    out: dict[str, ContractTruth] = {}
    for i, (root, code, yy) in enumerate(listed):
        # Venue-native one-digit-year raw symbol (CME style: NQZ6, CLF7).
        raw = f"{root}{code}{yy % 10}"
        mm = MONTH_OF_CODE[code]
        spec_ = ROOT_SPECS[root]
        # synthetic listing window: active ~1 year before the delivery
        # month, so every synthetic bar sits inside activation..expiration
        activation = ct(yy - 1, mm, 15, 17, 0)
        # last eligible trade ~20th of the month prior to delivery (fabricated)
        exp_m = mm - 1 if mm > 1 else 12
        exp_y = yy if mm > 1 else yy - 1
        expiration = ct(exp_y, exp_m, 20, 13, 0)
        out[raw] = ContractTruth(
            raw_symbol=raw, root=root, instrument_id=INSTRUMENT_ID_BASE + i,
            tick_nanos=spec_["tick"], unit_of_measure_qty_nanos=spec_["mult"],
            exchange=spec_["exchange"], maturity_year=yy, maturity_month=mm,
            activation_ns=activation, expiration_ns=expiration,
            actions=[(activation, "A")],
        )
    out["NQZ6"].actions.append((ct(2026, 2, 2, 8, 0), "M"))     # modified def
    out["CLV6"].actions.append((out["CLV6"].expiration_ns, "D"))  # deleted at expiry
    return out


def _def_record(c: ContractTruth, ts: int, action: str) -> dict:
    return dict(
        ts_recv=ts, min_price_increment=c.tick_nanos,
        display_factor=100_000_000, expiration=c.expiration_ns,
        activation=c.activation_ns,
        high_limit_price=c.tick_nanos * 200_000, low_limit_price=-c.tick_nanos * 200_000,
        max_price_variation=c.tick_nanos * 200, unit_of_measure_qty=c.unit_of_measure_qty_nanos,
        min_price_increment_amount=c.tick_nanos, price_ratio=1_000_000_000,
        strike_price=S.UNDEF_PRICE, raw_instrument_id=c.instrument_id * 10,
        leg_price=S.UNDEF_PRICE, leg_delta=S.UNDEF_PRICE,
        inst_attrib_value=0, underlying_id=0, market_depth_implied=0,
        market_depth=10, market_segment_id=0, max_trade_vol=1000,
        min_lot_size=1, min_lot_size_block=0, min_lot_size_round_lot=0,
        min_trade_vol=1, contract_multiplier=0, decay_quantity=0,
        original_contract_size=0, leg_instrument_id=0,
        leg_ratio_price_numerator=0, leg_ratio_price_denominator=0,
        leg_ratio_qty_numerator=0, leg_ratio_qty_denominator=0,
        leg_underlying_id=0, appl_id=0, maturity_year=c.maturity_year,
        decay_start_date=0, channel_id=0, leg_count=0, leg_index=0,
        currency="USD", settl_currency="USD", secsubtype="",
        raw_symbol=c.raw_symbol, group=c.root, exchange=c.exchange,
        asset=c.root, cfi="FFFFFF", security_type="FUT",
        unit_of_measure="USD", underlying="", strike_price_currency="USD",
        leg_raw_symbol="", instrument_class="F", match_algorithm="K",
        main_fraction=0, price_display_format=0, sub_fraction=0,
        underlying_product=0, security_update_action=action,
        maturity_month=c.maturity_month, maturity_day=0, maturity_week=0,
        user_defined_instrument="N", contract_multiplier_unit=0,
        flow_schedule_type=0, tick_rule=0, leg_instrument_class=" ", leg_side=" ",
    )


# ---------------------------------------------------------------------------
# session scaffolding
# ---------------------------------------------------------------------------

def _weekdays(start: dt.date, end: dt.date) -> list[dt.date]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def _next_weekday(d: dt.date) -> dt.date:
    x = d + dt.timedelta(days=1)
    while x.weekday() >= 5:
        x += dt.timedelta(days=1)
    return x


# fabricated holiday: Good Friday 2026-04-03 early close 12:00 CT
HOLIDAY_EARLY_CLOSE = {(2026, 4, 3): (12, 0)}


def session_bounds(d: dt.date) -> tuple[int, int, str]:
    """Synthetic CME-style session for exchange-date d:
    open 17:00 CT the previous calendar day, close 16:00 CT.
    DST-correct; holiday early close applied."""
    kind = "NORMAL"
    close_h, close_m = 16, 0
    if (d.year, d.month, d.day) in HOLIDAY_EARLY_CLOSE:
        close_h, close_m = HOLIDAY_EARLY_CLOSE[(d.year, d.month, d.day)]
        kind = "HOLIDAY_SHORT"
    prev = d - dt.timedelta(days=1)
    open_ns = ct(prev.year, prev.month, prev.day, 17, 0)
    close_ns = ct(d.year, d.month, d.day, close_h, close_m)
    return open_ns, close_ns, kind


def _bar(ts: int, o: int, h: int, low: int, c: int, v: int) -> dict:
    assert h >= max(o, c, low) and low <= min(o, c, h)
    return dict(ts_event=ts, open=o, high=h, low=low, close=c, volume=v)


def _with_inst(rows: dict, inst: int) -> dict:
    r = dict(rows)
    r["_instrument_id"] = inst
    return r


# ---------------------------------------------------------------------------
# builder
# ---------------------------------------------------------------------------

def build_fixture_dir(out_dir, seed: int = FIXTURE_SEED) -> FixtureUniverse:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = _Rng(seed)
    u = FixtureUniverse(out_dir=str(out.resolve()), seed=seed)
    u.contracts = _contracts()
    _build_ohlcv_1m(u, rng)
    _build_ohlcv_1d(u, rng)
    _build_definitions(u)
    _build_statistics(u)
    _build_trades_and_book(u)
    _build_continuous(u)
    _write_manifest(u)
    return u


def out_path(u: FixtureUniverse, name: str) -> Path:
    p = Path(u.out_dir) / name
    # store the BASENAME so the manifest is byte-reproducible regardless of
    # where the fixture dir lives (out_dir is recorded separately for humans)
    u.files[name] = name
    return p


def _write_bar_file(path, rows, rtype, schema, symbols):
    recs = [(rtype, S.pack_record(rtype, r["ts_event"], r, PUBLISHER_ID,
                                  r["_instrument_id"])) for r in rows]
    meta = DbnMetadata(schema=schema,
                       start=rows[0]["ts_event"] if rows else 0,
                       end=(rows[-1]["ts_event"] + 1) if rows else None,
                       stype_in=S.STYPE_RAW_SYMBOL,
                       stype_out=S.STYPE_INSTRUMENT_ID,
                       symbols=list(symbols))
    write_dbn(path, meta, recs)


def _text_rows(rows, rtype: int) -> list[dict]:
    """CSV/JSONL rows must carry their own header columns (rtype,
    publisher_id, instrument_id, ts_event) so text exports round-trip to
    the same records as the binary files."""
    out = []
    for r in rows:
        x = dict(r)
        x.setdefault("rtype", rtype)
        x.setdefault("publisher_id", PUBLISHER_ID)
        if "_instrument_id" in x:
            x["instrument_id"] = x.pop("_instrument_id")
        x.setdefault("ts_event", x.get("ts_recv", 0))
        out.append(x)
    return out


def _write_bar_csv(path, rows, rtype):
    from .textio import write_csv
    write_csv(path, rtype, _text_rows(rows, rtype))


# ------------------------- ohlcv-1m ----------------------------------------

def _build_ohlcv_1m(u: FixtureUniverse, rng: _Rng) -> None:
    es = u.contracts["ESZ6"]
    sessions = [dt.date(2026, 3, 5), dt.date(2026, 3, 6), dt.date(2026, 3, 9)]
    rows = []
    price = ROOT_SPECS["ES"]["base"]
    tick = ROOT_SPECS["ES"]["tick"]
    u.minute_gaps["ESZ6"] = []
    u.duplicate_bars["ESZ6"] = []
    for d in sessions:
        open_ns, close_ns, _kind = session_bounds(d)
        minutes = [open_ns,
                   ct(d.year, d.month, d.day, 9, 30),
                   ct(d.year, d.month, d.day, 9, 31),
                   ct(d.year, d.month, d.day, 9, 32),
                   close_ns - 60_000_000_000]
        if d == dt.date(2026, 3, 6):       # no-trade gap: minute absent on purpose
            minutes.remove(ct(2026, 3, 6, 9, 31))
            u.minute_gaps["ESZ6"].append(ct(2026, 3, 6, 9, 31))
        for m in minutes:
            o = price + rng.below(9) * tick
            c = o + (rng.below(5) - 2) * tick
            h = max(o, c) + tick
            low = min(o, c) - tick
            v = 50 + rng.below(400)
            rows.append(_with_inst(_bar(m, o, h, low, c, v), es.instrument_id))
            price = c
        u.minute_sessions.setdefault("ESZ6", []).append(
            SessionTruth(date_str(d), open_ns, close_ns, "NORMAL"))
    # duplicate ts_event pair (same bar, different volume)
    dup_ts = ct(2026, 3, 9, 9, 30)
    first = next(r for r in rows if r["ts_event"] == dup_ts)
    rows.append(_with_inst(
        _bar(dup_ts, first["open"], first["high"], first["low"], first["close"], 77),
        es.instrument_id))
    u.duplicate_bars["ESZ6"].append(dup_ts)

    # 6J USD-per-JPY scale day (2026-03-09) + a STALE bar (o=h=l=c=prev close)
    j6 = u.contracts["6JZ6"]
    jt = ROOT_SPECS["6J"]["tick"]
    p = ROOT_SPECS["6J"]["base"]
    d = dt.date(2026, 3, 9)
    open_ns, close_ns, _ = session_bounds(d)
    for m in [open_ns, ct(2026, 3, 9, 9, 30), ct(2026, 3, 9, 9, 31)]:
        rows.append(_with_inst(_bar(m, p, p + jt, p - jt, p + jt, 10), j6.instrument_id))
        p = p + jt
    stale_ts = ct(2026, 3, 9, 9, 32)
    rows.append(_with_inst(_bar(stale_ts, p, p, p, p, 1), j6.instrument_id))
    # near-close bar so the session is classifiable as full coverage
    rows.append(_with_inst(_bar(close_ns - 60_000_000_000, p, p + jt, p, p + jt, 5),
                           j6.instrument_id))
    u.stale_bar["6JZ6"] = stale_ts
    u.minute_sessions.setdefault("6JZ6", []).append(
        SessionTruth(date_str(d), open_ns, close_ns, "NORMAL"))

    # NQ: full session 2026-04-02 + holiday short session 2026-04-03
    nq = u.contracts["NQZ6"]
    nt = ROOT_SPECS["NQ"]["tick"]
    p0 = ROOT_SPECS["NQ"]["base"]
    for d in (dt.date(2026, 4, 2), dt.date(2026, 4, 3)):
        open_ns, close_ns, kind = session_bounds(d)
        for m in [open_ns, ct(d.year, d.month, d.day, 9, 30), close_ns - 60_000_000_000]:
            rows.append(_with_inst(
                _bar(m, p0, p0 + nt, p0 - nt, p0 + nt, 500), nq.instrument_id))
        u.minute_sessions.setdefault("NQZ6", []).append(
            SessionTruth(date_str(d), open_ns, close_ns, kind))

    rows.sort(key=lambda r: (r["ts_event"], r["_instrument_id"]))
    syms = ["6JZ6", "ESZ6", "NQZ6"]
    _write_bar_file(out_path(u, "ohlcv-1m.glbx-mdp3.raw_symbol.synthetic.dbn"),
                    rows, S.RTYPE_OHLCV_1M, S.SCHEMA_OHLCV_1M, syms)
    _write_bar_csv(out_path(u, "ohlcv-1m.glbx-mdp3.raw_symbol.synthetic.csv"),
                   rows, S.RTYPE_OHLCV_1M)


# ------------------------- ohlcv-1d ----------------------------------------

def _build_ohlcv_1d(u: FixtureUniverse, rng: _Rng) -> None:
    daily = {r: {} for r in u.contracts}
    dates = _weekdays(dt.date(2026, 2, 20), dt.date(2026, 4, 10))
    for raw, c in u.contracts.items():
        if raw == "CLV6":
            continue                          # expired: definitions only
        rs = ROOT_SPECS[c.root]
        price = rs["base"] + rng.below(20) * rs["tick"]
        for d in dates:
            drift = (rng.below(7) - 3) * rs["tick"]
            o = price
            cpx = price + drift
            h = max(o, cpx) + rs["tick"]
            low = min(o, cpx) - rs["tick"]
            v = 1000 + rng.below(9000)
            daily[raw][date_str(d)] = dict(open=o, high=h, low=low, close=cpx, volume=v)
            price = cpx
    # negative-price CL day
    daily["CLZ6"][NEG_DAY] = dict(open=S.price_to_nanos("58.25"),
                                  high=S.price_to_nanos("58.50"),
                                  low=S.price_to_nanos("-3.00"),
                                  close=S.price_to_nanos("-2.75"),
                                  volume=999_999)
    # close-only-by-absence: NO bar these sessions (settlement only)
    u.absent_sessions = {"GCZ6": ["2026-03-16", "2026-03-17"], "6BZ6": ["2026-03-16"]}
    for raw, ds in u.absent_sessions.items():
        for d in ds:
            daily[raw].pop(d, None)

    # roll-critical window 2026-10-26 .. 2026-11-06 (spans fall-back 11-01)
    roll_dates = _weekdays(dt.date(2026, 10, 26), dt.date(2026, 11, 6))
    n = len(roll_dates)
    base_px = S.price_to_nanos("61.00")
    for i, d in enumerate(roll_dates):
        f = i / (n - 1)
        ds_ = date_str(d)
        old_v = int(12_000 * (1 - f)) + 10
        new_v = int(12_000 * f) + 10
        old_oi = 15_000 - int(5_000 * f)
        new_oi = 2_000 + int(10_000 * f)    # OI lags volume: crosses later
        old_c = base_px - 40_000_000 * i
        new_c = old_c + 30_000_000          # ~0.03 premium on the new contract
        daily["CLZ6"][ds_] = dict(open=old_c + 10_000_000, high=old_c + 25_000_000,
                                  low=old_c - 20_000_000, close=old_c, volume=old_v)
        daily["CLF7"][ds_] = dict(open=new_c + 10_000_000, high=new_c + 25_000_000,
                                  low=new_c - 20_000_000, close=new_c, volume=new_v)
        u.volume_roll[ds_] = dict(old=old_v, new=new_v)
        u.oi_roll[ds_] = {"CLZ6": old_oi, "CLF7": new_oi}
    u.volume_roll["crossover"] = next(
        d for d in (date_str(x) for x in roll_dates)
        if u.volume_roll[d]["new"] >= u.volume_roll[d]["old"])
    u.oi_roll["crossover"] = next(
        d for d in (date_str(x) for x in roll_dates)
        if u.oi_roll[d]["CLF7"] >= u.oi_roll[d]["CLZ6"])

    rows = []
    for raw, by_date in daily.items():
        c = u.contracts[raw]
        for ds_, b in sorted(by_date.items()):
            y, m, d = (int(x) for x in ds_.split("-"))
            # ohlcv-1d = UTC-day bars; ts_event marks the interval START
            ts = utc_ns(y, m, d, 0, 0)
            rows.append(_with_inst(dict(ts_event=ts, **b), c.instrument_id))
    rows.sort(key=lambda r: (r["ts_event"], r["_instrument_id"]))
    syms = sorted(daily)
    _write_bar_file(out_path(u, "ohlcv-1d.glbx-mdp3.raw_symbol.synthetic.dbn"),
                    rows, S.RTYPE_OHLCV_1D, S.SCHEMA_OHLCV_1D, syms)
    _write_bar_csv(out_path(u, "ohlcv-1d.glbx-mdp3.raw_symbol.synthetic.csv"),
                   rows, S.RTYPE_OHLCV_1D)
    from .textio import write_jsonl
    write_jsonl(out_path(u, "ohlcv-1d.glbx-mdp3.raw_symbol.synthetic.jsonl"),
                S.RTYPE_OHLCV_1D, _text_rows(rows, S.RTYPE_OHLCV_1D))
    u.daily_bars = daily


# ------------------------- definition --------------------------------------

def _build_definitions(u: FixtureUniverse) -> None:
    rows = []
    for raw, c in u.contracts.items():
        for ts, action in c.actions:
            r = _def_record(c, ts, action)
            r["_instrument_id"] = c.instrument_id
            rows.append(r)
    rows.sort(key=lambda r: r["ts_recv"])
    recs = [(S.RTYPE_INSTRUMENT_DEF,
             S.pack_record(S.RTYPE_INSTRUMENT_DEF, r["ts_recv"], r,
                           PUBLISHER_ID, r["_instrument_id"])) for r in rows]
    meta = DbnMetadata(schema=S.SCHEMA_DEFINITION, start=rows[0]["ts_recv"],
                       end=rows[-1]["ts_recv"] + 1,
                       stype_in=S.STYPE_PARENT, stype_out=S.STYPE_INSTRUMENT_ID,
                       symbols=sorted({c.root for c in u.contracts.values()}))
    write_dbn(out_path(u, "definition.glbx-mdp3.parent.synthetic.dbn"), meta, recs)
    from .textio import write_csv
    write_csv(out_path(u, "definition.glbx-mdp3.parent.synthetic.csv"),
              S.RTYPE_INSTRUMENT_DEF, _text_rows(rows, S.RTYPE_INSTRUMENT_DEF))


# ------------------------- statistics --------------------------------------

def _stat_row(inst, pub, ts_ref, st, price, qty, flags, seq) -> dict:
    return dict(ts_recv=pub, ts_ref=ts_ref, price=price, quantity=qty,
                sequence=seq, ts_in_delta=0, stat_type=st, channel_id=0,
                update_action=S.STAT_UPDATE_NEW, stat_flags=flags,
                _instrument_id=inst, ts_event=pub)


def _build_statistics(u: FixtureUniverse) -> None:
    rows = []
    u.settlements = {r: {} for r in u.contracts}
    for raw, by_date in u.daily_bars.items():
        c = u.contracts[raw]
        for ds_, b in by_date.items():
            y, m, d = (int(x) for x in ds_.split("-"))
            ts_ref = utc_ns(y, m, d, 0, 0)
            if raw == "CLZ6" and ds_ == NEG_DAY:
                # preliminary 19:00 same day, final revision 03:00 next day
                prelim_ts, final_ts = ct(2026, 3, 13, 19, 0), ct(2026, 3, 14, 3, 0)
                prelim_px = S.price_to_nanos("-2.50")
                final_px = S.price_to_nanos("-2.75")
                rows.append(_stat_row(c.instrument_id, prelim_ts, ts_ref,
                                      S.STAT_TYPE_SETTLEMENT_PRICE, prelim_px,
                                      S.UNDEF_STAT_QUANTITY, 0, 2))
                rows.append(_stat_row(c.instrument_id, final_ts, ts_ref,
                                      S.STAT_TYPE_SETTLEMENT_PRICE, final_px,
                                      S.UNDEF_STAT_QUANTITY, S.STAT_FLAG_FINAL, 3))
                u.settlements[raw][ds_] = [(prelim_ts, prelim_px, False),
                                           (final_ts, final_px, True)]
                continue
            pub = ct(y, m, d, 18, 5)
            rows.append(_stat_row(c.instrument_id, pub, ts_ref,
                                  S.STAT_TYPE_SETTLEMENT_PRICE, b["close"],
                                  S.UNDEF_STAT_QUANTITY, S.STAT_FLAG_FINAL, 1))
            u.settlements[raw][ds_] = [(pub, b["close"], True)]
    # absent sessions: settlement exists, bar does not (close-only-by-absence)
    for raw, ds in u.absent_sessions.items():
        c = u.contracts[raw]
        base = ROOT_SPECS[c.root]["base"]
        for ds_ in ds:
            y, m, d = (int(x) for x in ds_.split("-"))
            pub = ct(y, m, d, 18, 5)
            rows.append(_stat_row(c.instrument_id, pub, utc_ns(y, m, d, 0, 0),
                                  S.STAT_TYPE_SETTLEMENT_PRICE, base,
                                  S.UNDEF_STAT_QUANTITY, S.STAT_FLAG_FINAL, 1))
            u.settlements.setdefault(raw, {})[ds_] = [(pub, base, True)]
    # open interest through the roll window
    for ds_ in sorted(u.volume_roll):
        if ds_ == "crossover":
            continue
        y, m, d = (int(x) for x in ds_.split("-"))
        ts_ref, pub = utc_ns(y, m, d, 0, 0), ct(y, m, d, 18, 10)
        for raw in ("CLZ6", "CLF7"):
            rows.append(_stat_row(u.contracts[raw].instrument_id, pub, ts_ref,
                                  S.STAT_TYPE_OPEN_INTEREST, S.UNDEF_PRICE,
                                  u.oi_roll[ds_][raw], 0, 1))
    # cleared volume: published next morning, ts_ref = trading date of volume
    for ds_ in sorted(u.volume_roll):
        if ds_ == "crossover":
            continue
        y, m, d = (int(x) for x in ds_.split("-"))
        nd = _next_weekday(dt.date(y, m, d))
        pub = ct(nd.year, nd.month, nd.day, 8, 0)
        for raw, key in (("CLZ6", "old"), ("CLF7", "new")):
            rows.append(_stat_row(u.contracts[raw].instrument_id, pub,
                                  utc_ns(y, m, d, 0, 0),
                                  S.STAT_TYPE_CLEARED_VOLUME, S.UNDEF_PRICE,
                                  u.volume_roll[ds_][key], 0, 1))
    # ESZ6 official session high/low/close for two days
    es = u.contracts["ESZ6"]
    for ds_, b in list(u.daily_bars["ESZ6"].items())[:2]:
        y, m, d = (int(x) for x in ds_.split("-"))
        ts_ref, pub = utc_ns(y, m, d, 0, 0), ct(y, m, d, 16, 15)
        for st, px in ((S.STAT_TYPE_TRADING_SESSION_HIGH_PRICE, b["high"]),
                       (S.STAT_TYPE_TRADING_SESSION_LOW_PRICE, b["low"]),
                       (S.STAT_TYPE_CLOSE_PRICE, b["close"])):
            rows.append(_stat_row(es.instrument_id, pub, ts_ref, st, px,
                                  S.UNDEF_STAT_QUANTITY, 0, 1))
    rows.sort(key=lambda r: r["ts_recv"])
    recs = [(S.RTYPE_STATISTICS, S.pack_record(S.RTYPE_STATISTICS, r["ts_event"], r,
                                               PUBLISHER_ID, r["_instrument_id"]))
            for r in rows]
    meta = DbnMetadata(schema=S.SCHEMA_STATISTICS, start=rows[0]["ts_recv"],
                       end=rows[-1]["ts_recv"] + 1,
                       stype_in=S.STYPE_PARENT, stype_out=S.STYPE_INSTRUMENT_ID,
                       symbols=sorted({c.root for c in u.contracts.values()}))
    write_dbn(out_path(u, "statistics.glbx-mdp3.parent.synthetic.dbn"), meta, recs)
    from .textio import write_csv
    write_csv(out_path(u, "statistics.glbx-mdp3.parent.synthetic.csv"),
              S.RTYPE_STATISTICS, _text_rows(rows, S.RTYPE_STATISTICS))


# ------------------------- trades / book ------------------------------------

def _build_trades_and_book(u: FixtureUniverse) -> None:
    es = u.contracts["ESZ6"]
    tick = ROOT_SPECS["ES"]["tick"]
    px = ROOT_SPECS["ES"]["base"] + 10 * tick
    t = ct(2026, 3, 9, 9, 30)
    sec = 1_000_000_000

    def trade_row(ts, price, size, side, seq, action=S.ACTION_TRADE):
        return dict(price=price, size=size, action=action, side=side,
                    flags=S.FLAG_LAST, depth=0, ts_recv=ts, ts_in_delta=100,
                    sequence=seq, _instrument_id=es.instrument_id, ts_event=ts)

    def book_row(ts, action, bid, ask, bsz, asz, seq, side=S.SIDE_NONE,
                 price=0, size=0):
        return dict(price=price, size=size, action=action, side=side,
                    flags=S.FLAG_TOB, depth=1, ts_recv=ts, ts_in_delta=50,
                    sequence=seq, bid_px_00=bid, ask_px_00=ask, bid_sz_00=bsz,
                    ask_sz_00=asz, bid_ct_00=1, ask_ct_00=1,
                    _instrument_id=es.instrument_id, ts_event=ts)

    book_rows = [
        book_row(t - 100_000_000, S.ACTION_MODIFY, px - tick, px + tick, 40, 35, 1),
        book_row(t, S.ACTION_TRADE, px - tick, px + tick, 40, 35, 2,
                 side=S.SIDE_BID, price=px, size=12),        # trade + pre-trade BBO
        book_row(t + 100_000_000, S.ACTION_MODIFY, px - tick, px + tick, 38, 35, 3),
        book_row(t + 4 * sec, S.ACTION_NONE, px + tick, px, 20, 20, 4),   # CROSSED
        book_row(t + 5 * sec, S.ACTION_NONE, px, px, 20, 20, 5),          # LOCKED
        book_row(t + 9 * sec, S.ACTION_MODIFY, px - 2 * tick, px + tick, 30, 30, 6),
    ]
    u.bbo_states = [(t + 4 * sec, "CROSSED"), (t + 5 * sec, "LOCKED")]
    trade_rows = [
        trade_row(t, px, 12, S.SIDE_BID, 10),                        # EXACT
        trade_row(t + 500_000_000, px + tick, 5, S.SIDE_ASK, 11),    # BOOK_TIME
        trade_row(t + 3 * sec, px + tick, 3, S.SIDE_ASK, 12),        # STALE
        trade_row(t + 11 * sec, px + 2 * tick, 8, S.SIDE_BID, 13),   # STALE (2s lead)
        trade_row(t - 200_000_000, px - tick, 4, S.SIDE_ASK, 9),     # NO_QUOTE
    ]
    # truth validated against the book timeline above with the default 1s
    # staleness: quotes exist at t-0.1, t, t+0.1, t+4, t+5, t+9 only, so
    # leads are 0.5s (BOOK_TIME), 2.9s / 2s (STALE), no quote before the
    # earliest trade (NO_QUOTE).
    u.trade_join_truth = [
        (t, "EXACT"),
        (t + 500_000_000, "BOOK_TIME"),
        (t + 3 * sec, "STALE"),
        (t + 11 * sec, "STALE"),
        (t - 200_000_000, "NO_QUOTE"),
    ]
    from .textio import write_csv
    for rows, rtype, schema, name in (
        (trade_rows, S.RTYPE_MBP_0, S.SCHEMA_TRADES, "trades"),
        (book_rows, S.RTYPE_MBP_1, S.SCHEMA_MBP_1, "mbp-1"),
    ):
        rows2 = sorted(rows, key=lambda r: r["ts_recv"])
        recs = [(rtype, S.pack_record(rtype, r["ts_event"], r, PUBLISHER_ID,
                                      r["_instrument_id"])) for r in rows2]
        meta = DbnMetadata(schema=schema, start=rows2[0]["ts_recv"],
                           end=rows2[-1]["ts_recv"] + 1,
                           stype_in=S.STYPE_RAW_SYMBOL,
                           stype_out=S.STYPE_INSTRUMENT_ID, symbols=["ESZ6"])
        write_dbn(out_path(u, f"{name}.glbx-mdp3.raw_symbol.synthetic.dbn"), meta, recs)
        write_csv(out_path(u, f"{name}.glbx-mdp3.raw_symbol.synthetic.csv"),
                  rtype, _text_rows(rows2, rtype))
    # tbbo variant (same rtype, tbbo schema semantics: pre-trade BBO on trades)
    tbbo_rows = sorted(book_rows, key=lambda r: r["ts_recv"])
    recs = [(S.RTYPE_MBP_1, S.pack_record(S.RTYPE_MBP_1, r["ts_event"], r,
                                          PUBLISHER_ID, r["_instrument_id"]))
            for r in tbbo_rows]
    meta = DbnMetadata(schema=S.SCHEMA_TBBO, start=tbbo_rows[0]["ts_recv"],
                       end=tbbo_rows[-1]["ts_recv"] + 1,
                       stype_in=S.STYPE_RAW_SYMBOL, stype_out=S.STYPE_INSTRUMENT_ID,
                       symbols=["ESZ6"])
    write_dbn(out_path(u, "tbbo.glbx-mdp3.raw_symbol.synthetic.dbn"), meta, recs)
    # bbo-1m variant exercises the BboMsg layout (rtype 0xC4)
    bbo_rows = []
    for i, (ts, state) in enumerate([(t, "NORMAL"), (t + 4 * sec, "CROSSED"),
                                     (t + 5 * sec, "LOCKED")]):
        bid = {"NORMAL": px - tick, "CROSSED": px + tick, "LOCKED": px}[state]
        ask = {"NORMAL": px + tick, "CROSSED": px, "LOCKED": px}[state]
        bbo_rows.append(dict(price=px if i == 0 else S.UNDEF_PRICE,
                             size=12 if i == 0 else 0,
                             side="B" if i == 0 else " ", flags=S.FLAG_TOB,
                             ts_recv=ts, sequence=100 + i,
                             bid_px_00=bid, ask_px_00=ask,
                             bid_sz_00=30, ask_sz_00=30, bid_ct_00=1, ask_ct_00=1,
                             _instrument_id=es.instrument_id, ts_event=ts))
    recs = [(S.RTYPE_BBO_1M, S.pack_record(S.RTYPE_BBO_1M, r["ts_event"], r,
                                           PUBLISHER_ID, r["_instrument_id"]))
            for r in bbo_rows]
    meta = DbnMetadata(schema=S.SCHEMA_BBO_1M, start=bbo_rows[0]["ts_recv"],
                       end=bbo_rows[-1]["ts_recv"] + 1, stype_in=S.STYPE_RAW_SYMBOL,
                       stype_out=S.STYPE_INSTRUMENT_ID, symbols=["ESZ6"])
    write_dbn(out_path(u, "bbo-1m.glbx-mdp3.raw_symbol.synthetic.dbn"), meta, recs)


# ------------------------- continuous ---------------------------------------

def _build_continuous(u: FixtureUniverse) -> None:
    rows = []
    i = 0
    for ds_ in sorted(u.volume_roll):
        if ds_ == "crossover":
            continue
        y, m, d = (int(x) for x in ds_.split("-"))
        ts = utc_ns(y, m, d, 0, 0)
        px = S.price_to_nanos("61.00") - 40_000_000 * i
        v = u.volume_roll[ds_]
        rows.append(dict(ts_event=ts, open=px + 10_000_000, high=px + 25_000_000,
                         low=px - 20_000_000, close=px,
                         volume=v["old"] + v["new"],
                         _instrument_id=CONTINUOUS_INSTRUMENT_ID))
        i += 1
    recs = [(S.RTYPE_OHLCV_1D, S.pack_record(S.RTYPE_OHLCV_1D, r["ts_event"], r,
                                             PUBLISHER_ID, r["_instrument_id"]))
            for r in rows]
    m1 = MappingInterval(20260101, 20261101, "CLZ6")
    m2 = MappingInterval(20261102, 20261231, "CLF7")
    meta = DbnMetadata(schema=S.SCHEMA_OHLCV_1D, start=rows[0]["ts_event"],
                       end=rows[-1]["ts_event"] + 1,
                       stype_in=S.STYPE_CONTINUOUS, stype_out=S.STYPE_INSTRUMENT_ID,
                       symbols=["CL.c.0"],
                       mappings=[SymbolMapping("CL.c.0", [m1, m2])])
    write_dbn(out_path(u, "ohlcv-1d.glbx-mdp3.continuous.synthetic.dbn"), meta, recs)
    u.continuous = {"symbol": "CL.c.0",
                    "intervals": [[m1.start_date, m1.end_date, m1.symbol],
                                  [m2.start_date, m2.end_date, m2.symbol]]}


def _write_manifest(u: FixtureUniverse) -> None:
    doc = u.to_json_dict()
    p = Path(u.out_dir) / "FIXTURE_MANIFEST.json"
    p.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str))
    u.files["FIXTURE_MANIFEST.json"] = str(p.resolve())
