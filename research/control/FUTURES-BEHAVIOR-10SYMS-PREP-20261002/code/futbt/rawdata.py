"""Per-contract raw adapter for IBKR JSON bar files.

Raw directory layout (FUTURES-DATA-10SYMS-V1, read-only):
  {SYM}_{LOCALSYMBOL}_{CONID}_{TYPE}_{BAR}_{SPAN}.json
  TYPE in {TRADES, BID, ASK}; some files carry an extra marker token between
  CONID and TYPE ('front', 'next', 'nearest_expired' — 3-day convenience
  snapshots that must NOT be merged into the canonical per-contract series).
  e.g. CL_CLX6_304037511_TRADES_1day_6Y.json
       CL_CLX6_304037511_front_TRADES_1min_1800S.json
       6A_6AX6_881167003_next_TRADES_1day_3D.json
       NG_NGX26_269460170_TRADES_1day_6Y.json

File body (OBSERVED, headers of the 1160 raw files, 2026-10-02):
  header: fetched_utc, symbol, conId, localSymbol, expiry_month (YYYYMMDD —
    this is the *lastTradeDate*, per data-lane caveat C3, NOT always the
    delivery month), exchange, whatUse, barSize ("1 day"/"1 hour"/"1 min"),
    durationStr, useRTH, timeZoneId, ok, errors, exception, n_rows
  bars[]: {"t": "2026-08-20" | "2026-08-20T09:30:00-04:00",
           "o","h","l","c","v","wap","n"}
  BID/ASK files: v = -1, wap = -1.0, n = -1 (no volume on quote bars).
  Deep-history TRADES bars are close-only settlement-derived: o=h=l=c, v=0.

This module NEVER writes to the raw directory.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .instruments import MONTH_OF_CODE

FILENAME_RE = re.compile(
    r"^(?P<sym>[A-Z0-9]{1,4})"
    r"_(?P<local>[A-Z0-9]+)"
    r"_(?P<conid>\d+)"
    r"(?:_(?P<marker>front|next|nearest_expired))?"
    r"_(?P<what>TRADES|BID|ASK)"
    r"_(?P<bar>[A-Za-z0-9]+)"
    r"_(?P<span>[A-Za-z0-9]+)"
    r"\.json$"
)

BAR_TOKEN_TO_SIZE = {
    "1day": "1 day",
    "1hour": "1 hour",
    "1min": "1 min",
}

PRICE_FIELDS = ("o", "h", "l", "c")


class RawFileError(ValueError):
    pass


@dataclass(frozen=True)
class RawFileName:
    symbol: str
    local_symbol: str
    conid: int
    what: str            # TRADES | BID | ASK
    bar_size: str        # normalized: "1 day" | "1 hour" | "1 min"
    span: str            # e.g. 6Y, 1Y, 30D, 2D, 1800S, 3D
    marker: str | None   # 'front' | 'next' | 'nearest_expired' | None

    @property
    def is_front_marker(self) -> bool:
        """Convenience: any convenience-snapshot marker file (3-day windows
        captured alongside the canonical per-contract series)."""
        return self.marker is not None

    @classmethod
    def parse(cls, filename: str) -> "RawFileName":
        m = FILENAME_RE.match(filename)
        if not m:
            raise RawFileError(f"filename does not match raw pattern: {filename!r}")
        bar = m.group("bar")
        if bar not in BAR_TOKEN_TO_SIZE:
            raise RawFileError(f"unknown bar token {bar!r} in {filename!r}")
        return cls(
            symbol=m.group("sym"),
            local_symbol=m.group("local"),
            conid=int(m.group("conid")),
            what=m.group("what"),
            bar_size=BAR_TOKEN_TO_SIZE[bar],
            span=m.group("span"),
            marker=m.group("marker"),
        )


@dataclass(frozen=True)
class Bar:
    t: dt.date            # session date (daily) or bar start date (intraday)
    t_raw: str            # verbatim timestamp string from the file
    t_iso: str | None     # full ISO instant for intraday bars, else None
    o: float
    h: float
    l: float
    c: float
    v: float              # -1 on BID/ASK files (no volume); 0 on close-only
    wap: float
    n: float

    @property
    def is_close_only(self) -> bool:
        """Settlement-derived bar: no intraday range, no volume (data-lane
        finding #3). Usable as reference/signal price, NOT as fill price."""
        return (self.o == self.h == self.l == self.c) and self.v == 0

    def validate(self) -> "Bar":
        for f in PRICE_FIELDS:
            if getattr(self, f) is None:
                raise RawFileError(f"bar {self.t_raw}: missing {f}")
        if not (self.h >= self.l):
            raise RawFileError(f"bar {self.t_raw}: h < l")
        # NOTE: o/h/l/c outside [l,h] is impossible by construction above.
        return self


def _parse_t(t: str) -> tuple[dt.date, str | None]:
    if "T" in t:
        # intraday bar carries explicit UTC offset (e.g. "2026-08-20T09:30:00-04:00")
        iso = t
        date_part = dt.date.fromisoformat(t.split("T")[0])
        return date_part, iso
    return dt.date.fromisoformat(t), None


@dataclass
class RawContractFile:
    """One parsed raw JSON file (one contract, one whatUse, one bar size)."""
    name: RawFileName
    path: Path
    header: dict
    bars: list[Bar]

    @property
    def last_trade_date(self) -> dt.date:
        """Raw `expiry_month` field is YYYYMMDD = lastTradeDate (caveat C3)."""
        s = str(self.header.get("expiry_month", ""))
        if not re.fullmatch(r"\d{8}", s):
            raise RawFileError(
                f"{self.path.name}: header expiry_month={s!r} not YYYYMMDD")
        return dt.date(int(s[:4]), int(s[4:6]), int(s[6:8]))

    @property
    def tz(self) -> str:
        return self.header.get("timeZoneId") or ""

    @property
    def symbol(self) -> str:
        return self.name.symbol

    def close_only_fraction(self) -> float:
        if not self.bars:
            return 0.0
        return sum(1 for b in self.bars if b.is_close_only) / len(self.bars)


def load_raw_file(path: str | Path) -> RawContractFile:
    path = Path(path)
    name = RawFileName.parse(path.name)
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    errors = doc.get("errors") or []
    n_bars = len(doc.get("bars") or [])
    # Tolerated error class (measured across the whole snapshot 2026-10-02):
    # IBKR error 162 'HMDS query returned no data' with ZERO bars and no
    # exception — deferred contracts with no intraday history. Every other
    # error combination fails the load.
    tolerated = (errors and n_bars == 0 and not doc.get("exception")
                 and all(e.get("code") == 162 for e in errors))
    if (not doc.get("ok", False) or (errors and not tolerated)
            or doc.get("exception")):
        raise RawFileError(
            f"{path.name}: fetch marked not-ok (errors={errors})")
    header_bar = str(doc.get("barSize", "")).strip().lower()
    if header_bar and header_bar != name.bar_size.lower():
        raise RawFileError(
            f"{path.name}: header barSize {header_bar!r} != filename {name.bar_size!r}")
    if str(doc.get("whatUse")) != name.what:
        raise RawFileError(
            f"{path.name}: header whatUse {doc.get('whatUse')!r} != {name.what!r}")
    if int(doc.get("conId", -1)) != name.conid:
        raise RawFileError(f"{path.name}: conId mismatch")
    if str(doc.get("localSymbol")) != name.local_symbol:
        raise RawFileError(f"{path.name}: localSymbol mismatch")
    bars: list[Bar] = []
    seen: set[str] = set()
    for r in doc.get("bars", []):
        d, iso = _parse_t(r["t"])
        if r["t"] in seen:
            raise RawFileError(f"{path.name}: duplicate bar timestamp {r['t']}")
        seen.add(r["t"])
        bars.append(Bar(
            t=d, t_raw=r["t"], t_iso=iso,
            o=float(r["o"]), h=float(r["h"]), l=float(r["l"]), c=float(r["c"]),
            v=float(r.get("v", 0)), wap=float(r.get("wap", 0.0)),
            n=float(r.get("n", 0)),
        ).validate())
    bars.sort(key=lambda b: b.t_raw)
    if doc.get("n_rows") is not None and int(doc["n_rows"]) != len(bars):
        raise RawFileError(
            f"{path.name}: n_rows={doc['n_rows']} != parsed {len(bars)}")
    return RawContractFile(name=name, path=path, header=doc, bars=bars)


@dataclass(frozen=True)
class ContractIdentity:
    symbol: str
    local_symbol: str
    conid: int
    last_trade_date: dt.date

    @property
    def expiry_month_key(self) -> tuple[int, int]:
        """(year, month) of the LAST-TRADE date — the roll baseline's
        'expiry month' (see roll.py: ExpiryMonthBasis.LAST_TRADE_DATE)."""
        return (self.last_trade_date.year, self.last_trade_date.month)

    @property
    def month_code(self) -> str | None:
        """Month code letter from the local symbol, if parseable.

        Ordering authority is ALWAYS last_trade_date; the parsed code is
        diagnostics only (1-digit years are decade-ambiguous; for CL/NG the
        delivery month = the letter-code month, one month AFTER the
        last-trade month — caveat C3).
        """
        root, code, yr = split_local_symbol(self.symbol, self.local_symbol)
        return code

    def order_key(self) -> tuple:
        return (self.last_trade_date, self.conid)


def split_local_symbol(symbol: str, local_symbol: str) -> tuple[str, str, str]:
    """Split e.g. ('CL','CLX6') -> ('CL','X','6'); ('NG','NGX26') -> ('NG','X','26');
    ('6J','6JV6') -> ('6J','V','6'). Raises if the local symbol does not start
    with the root or the tail is not code+digits."""
    if not local_symbol.startswith(symbol):
        raise RawFileError(
            f"local symbol {local_symbol!r} does not start with root {symbol!r}")
    tail = local_symbol[len(symbol):]
    if len(tail) < 2:
        raise RawFileError(f"local symbol {local_symbol!r} tail too short")
    code, digits = tail[0], tail[1:]
    if code not in MONTH_OF_CODE:
        raise RawFileError(f"unknown month code {code!r} in {local_symbol!r}")
    if not digits.isdigit():
        raise RawFileError(f"non-digit year {digits!r} in {local_symbol!r}")
    return symbol, code, digits


@dataclass
class ContractData:
    """All files loaded for one (symbol, conid) contract."""
    identity: ContractIdentity
    daily_trades: list[Bar] = field(default_factory=list)
    daily_bid: list[Bar] = field(default_factory=list)
    daily_ask: list[Bar] = field(default_factory=list)
    hourly_trades: list[Bar] = field(default_factory=list)
    minute_trades: list[Bar] = field(default_factory=list)
    extra_files: list[str] = field(default_factory=list)  # front_* markers etc.

    def close_map(self) -> dict[dt.date, float]:
        return {b.t: b.c for b in self.daily_trades}

    def bar_map(self) -> dict[dt.date, Bar]:
        return {b.t: b for b in self.daily_trades}

    def volume_map(self) -> dict[dt.date, float]:
        return {b.t: b.v for b in self.daily_trades}

    def daily_bidask_map(self) -> dict[dt.date, tuple[float, float]]:
        bid = {b.t: b for b in self.daily_bid}
        ask = {b.t: b for b in self.daily_ask}
        common = sorted(set(bid) & set(ask))
        return {d: (bid[d].c, ask[d].c) for d in common}


def load_contract_directory(
    raw_dir: str | Path,
    symbols: list[str] | None = None,
) -> dict[tuple[str, int], ContractData]:
    """Scan a raw directory and group files by (symbol, conid).

    Only canonical per-contract files feed ContractData; marker files
    ('front'/'next'/'nearest_expired') are recorded in extra_files and NOT
    merged (they are 3-day convenience snapshots overlapping the canonical
    series).
    """
    raw_dir = Path(raw_dir)
    out: dict[tuple[str, int], ContractData] = {}
    for p in sorted(raw_dir.glob("*.json")):
        try:
            name = RawFileName.parse(p.name)
        except RawFileError:
            continue  # non-conforming filename in raw dir: skip, don't guess
        if symbols is not None and name.symbol not in symbols:
            continue
        rf = load_raw_file(p)
        key = (name.symbol, name.conid)
        if key not in out:
            ident = ContractIdentity(
                symbol=name.symbol,
                local_symbol=name.local_symbol,
                conid=name.conid,
                last_trade_date=rf.last_trade_date,
            )
            out[key] = ContractData(identity=ident)
        cd = out[key]
        if cd.identity.local_symbol != name.local_symbol:
            raise RawFileError(
                f"conid {name.conid} maps to two local symbols: "
                f"{cd.identity.local_symbol} vs {name.local_symbol}")
        if name.is_front_marker:
            cd.extra_files.append(p.name)
            continue
        if name.what == "TRADES" and name.bar_size == "1 day":
            cd.daily_trades = rf.bars
        elif name.what == "BID" and name.bar_size == "1 day":
            cd.daily_bid = rf.bars
        elif name.what == "ASK" and name.bar_size == "1 day":
            cd.daily_ask = rf.bars
        elif name.what == "TRADES" and name.bar_size == "1 hour":
            cd.hourly_trades = rf.bars
        elif name.what == "TRADES" and name.bar_size == "1 min":
            cd.minute_trades = rf.bars
        else:
            cd.extra_files.append(p.name)
    return out


def contracts_by_symbol(contracts: dict[tuple[str, int], ContractData]
                        ) -> dict[str, list[ContractData]]:
    """Contracts of each symbol ordered by last_trade_date (ordering authority
    is the exchange-published expiry, NOT the parsed local-symbol year)."""
    by: dict[str, list[ContractData]] = {}
    for cd in contracts.values():
        by.setdefault(cd.identity.symbol, []).append(cd)
    for s in by:
        by[s].sort(key=lambda c: c.identity.order_key())
    return by
