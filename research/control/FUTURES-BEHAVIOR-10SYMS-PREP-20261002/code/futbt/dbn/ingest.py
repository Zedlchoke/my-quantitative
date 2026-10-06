"""Ingestion adapter: DBN binary / CSV / JSON -> normalized frames.

Consumes files produced by fixtures (or, later, real Databento exports of
the SAME wire shape) and produces typed normalized frames:

  BarFrame          ohlcv records (any cadence), prices in exact int nanos
  DefinitionFrame   instrument definition actions (A/M/D)
  StatisticsFrame   venue statistics (settlement/OI/volume/official OHLC)
  TradeFrame        trades-schema records
  BookFrame         mbp-1 / tbbo / bbo-1m quote records

Contract identity resolution: raw_symbol -> (instrument_id, expiry,
activation, tick, multiplier) from definition records, with add/modify/
delete action semantics applied in ts order (fail-closed on unknown
actions, duplicate instrument_id with conflicting identity, or bars whose
instrument_id cannot be resolved).

Execution guard (program rule): continuous (stype=3) or vendor-parent
symbol series are EXECUTION_FORBIDDEN — usable only as declared
signal-feature inputs, never as fill prices. `require_outright()` raises
the shared PolicyError on violation.

NOT_IMPLEMENTED (typed, fail-closed): live API paths, .zst files, record
types outside spec.SUPPORTED_RTYPES, DBN v1/v2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import spec as S
from .textio import TextSchemaError, parse_csv, parse_jsonl
from .wire import DbnMetadata, RawRecord, decode_dbn_bytes

# Stable interface from the parent package (read-only dependency; the
# taxonomy module is not owned by any concurrent lane).
from ..taxonomy import Evidence, EvidenceTag, PolicyError


class IngestError(PolicyError):
    """Raised for identity/schema/continuity violations during ingest."""


EXECUTION_FORBIDDEN = "EXECUTION_FORBIDDEN"


# ---------------------------------------------------------------------------
# normalized frames
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Bar:
    ts_event: int            # bar START timestamp (Databento ohlcv convention)
    instrument_id: int
    open: int
    high: int
    low: int
    close: int
    volume: int
    rtype: int

    def is_stale_flat(self, prev_close: int | None) -> bool:
        return (prev_close is not None and self.open == self.high == self.low
                == self.close == prev_close)

    def negative(self) -> bool:
        return min(self.open, self.high, self.low, self.close) < 0


@dataclass(frozen=True)
class DefinitionAction:
    ts_event: int
    instrument_id: int
    raw_symbol: str
    action: str              # 'A' | 'M' | 'D'
    activation: int
    expiration: int
    maturity_year: int
    maturity_month: int
    min_price_increment: int
    unit_of_measure_qty: int
    exchange: str
    security_type: str
    instrument_class: str


@dataclass(frozen=True)
class Statistic:
    ts_event: int            # publication time (ts_recv)
    ts_ref: int              # as-of trading date the statistic describes
    instrument_id: int
    stat_type: int
    stat_flags: int
    price: int
    quantity: int
    update_action: int       # 1 New / 2 Delete

    @property
    def stat_type_name(self) -> str:
        return S.STAT_TYPE_NAMES.get(self.stat_type, f"stat_{self.stat_type}")

    @property
    def is_final_settlement(self) -> bool:
        return (self.stat_type == S.STAT_TYPE_SETTLEMENT_PRICE
                and bool(self.stat_flags & S.STAT_FLAG_FINAL))

    @property
    def is_preliminary_settlement(self) -> bool:
        return (self.stat_type == S.STAT_TYPE_SETTLEMENT_PRICE
                and not self.stat_flags & S.STAT_FLAG_FINAL)


@dataclass(frozen=True)
class Trade:
    ts_event: int
    ts_recv: int
    instrument_id: int
    price: int
    size: int
    action: str
    side: str                # aggressor: 'A' ask / 'B' bid / 'N' none
    flags: int
    sequence: int

    def is_trade(self) -> bool:
        """Trade classification where the docs define it: the trades schema
        always carries action 'T'; in mbp-1 only action 'T' records are
        trades (add/cancel/modify/clear are book events)."""
        return self.action == "T"


@dataclass(frozen=True)
class Quote:
    ts_event: int
    ts_recv: int
    instrument_id: int
    bid_px: int
    ask_px: int
    bid_sz: int
    ask_sz: int
    action: str


@dataclass
class Ingested:
    source: str
    meta: DbnMetadata
    bars: list[Bar] = field(default_factory=list)
    definitions: list[DefinitionAction] = field(default_factory=list)
    statistics: list[Statistic] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    quotes: list[Quote] = field(default_factory=list)
    stype_in: int | None = None

    @property
    def continuous(self) -> bool:
        return self.stype_in == S.STYPE_CONTINUOUS or self.meta.stype_in == S.STYPE_CONTINUOUS

    @property
    def stype_proven(self) -> bool:
        """True only when stype_in came from DBN metadata. CSV/JSONL exports
        carry no stype metadata, so an outright/continuous classification
        from text files is UNPROVEN (see dbn/README.md)."""
        return self.stype_in is not None

    def execution_use(self) -> str:
        if self.continuous:
            return EXECUTION_FORBIDDEN
        return "outright" if self.stype_proven else "unproven_stype"


def require_outright(*frames: Ingested, what: str = "execution path") -> None:
    """Hard stop if any frame feeding an execution path is continuous."""
    for f in frames:
        if f.continuous:
            raise PolicyError(
                f"{what}: frame {f.source!r} is a CONTINUOUS (stype="
                f"{S.STYPE_NAMES[S.STYPE_CONTINUOUS]}) series; vendor continuous "
                "series are signal-feature-only by program rule and can never "
                "be fill prices (declared execution roll is our own table)")


# ---------------------------------------------------------------------------
# identity resolution
# ---------------------------------------------------------------------------

@dataclass
class ContractIdentity:
    raw_symbol: str
    instrument_id: int
    activation: int
    expiration: int            # ts of last eligible trade (venue semantics)
    maturity_year: int
    maturity_month: int
    min_price_increment: int   # nanos
    unit_of_measure_qty: int   # nanos (contract multiplier)
    exchange: str
    first_notice: int | None = None   # NOT AVAILABLE in DBN definitions (typed)

    @property
    def tick_decimal_str(self) -> str:
        return S.nanos_to_price_str(self.min_price_increment)

    @property
    def multiplier(self) -> int:
        return self.unit_of_measure_qty // S.FIXED_PRICE_SCALE


class ContractRegistry:
    """raw_symbol <-> instrument_id identity from definition actions."""

    def __init__(self):
        self.by_raw: dict[str, ContractIdentity] = {}
        self.by_id: dict[int, ContractIdentity] = {}
        self.actions_seen: list[tuple[int, str, str]] = []

    def apply(self, d: DefinitionAction) -> None:
        if d.action not in ("A", "M", "D"):
            raise IngestError(
                f"unknown security_update_action {d.action!r} for {d.raw_symbol} "
                f"@ts={d.ts_event} (fail-closed; documented actions are A/M/D)")
        self.actions_seen.append((d.ts_event, d.raw_symbol, d.action))
        if d.action == "D":
            existing = self.by_raw.get(d.raw_symbol)
            if existing is not None:
                del self.by_raw[d.raw_symbol]
                self.by_id.pop(existing.instrument_id, None)
            return
        ident = ContractIdentity(
            raw_symbol=d.raw_symbol, instrument_id=d.instrument_id,
            activation=d.activation, expiration=d.expiration,
            maturity_year=d.maturity_year, maturity_month=d.maturity_month,
            min_price_increment=d.min_price_increment,
            unit_of_measure_qty=d.unit_of_measure_qty, exchange=d.exchange)
        clash = self.by_raw.get(d.raw_symbol)
        if clash is not None and clash.instrument_id != d.instrument_id:
            raise IngestError(
                f"{d.raw_symbol}: identity clash instrument_id "
                f"{clash.instrument_id} != {d.instrument_id}")
        self.by_raw[d.raw_symbol] = ident
        self.by_id[d.instrument_id] = ident

    def require(self, *, raw_symbol: str | None = None,
                instrument_id: int | None = None) -> ContractIdentity:
        ident = (self.by_raw.get(raw_symbol) if raw_symbol is not None
                 else self.by_id.get(instrument_id or -1))
        if ident is None:
            key = raw_symbol if raw_symbol is not None else instrument_id
            raise IngestError(f"unresolved contract identity for {key!r} "
                              "(no live definition; deleted or absent)")
        return ident

    def raw_for(self, instrument_id: int) -> str:
        return self.require(instrument_id=instrument_id).raw_symbol

    # --- identity traps the program must never assume away ---------------
    def check_identity_traps(self, raw_symbol: str) -> None:
        ident = self.require(raw_symbol=raw_symbol)
        if raw_symbol.startswith("6J"):
            if ident.min_price_increment != 500:
                raise IngestError(
                    "6J identity trap: min_price_increment "
                    f"{ident.tick_decimal_str} != 5e-7 (USD-per-JPY orientation "
                    "guard; an inverted quote would show ~157)")
        if raw_symbol.startswith("SI"):
            if ident.multiplier != 5000:
                raise IngestError(
                    f"SI identity trap: multiplier {ident.multiplier} != 5000 "
                    "(must be the COMEX 5000oz class SI, not SIL 1000oz)")


def resolve_first_notice(raw_symbol: str) -> None:
    """DBN instrument definitions carry no first-notice-date field; any
    first-notice-dependent logic must be typed NOT_RUN, never guessed."""
    raise PolicyError(
        f"first_notice for {raw_symbol}: NOT_AVAILABLE in DBN definition "
        "records (field does not exist in the schema); declaring a value "
        "would be fabrication")


FIRST_NOTICE_STATUS = Evidence(
    tag=EvidenceTag.NOT_RUN,
    note="first_notice absent from DBN InstrumentDefMsg; NOT_AVAILABLE",
)


# ---------------------------------------------------------------------------
# file ingestion
# ---------------------------------------------------------------------------

def ingest_file(path: str | Path) -> Ingested:
    """Fail-closed ingestion of one DBN/CSV/JSONL export file."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in (".csv",):
        return _ingest_csv(p)
    if suffix in (".jsonl", ".json"):
        return _ingest_jsonl(p)
    if suffix == ".zst":
        raise IngestError(
            f"{p.name}: .zst decompression is NOT_IMPLEMENTED (Python 3.12 "
            "stdlib has no zstd); decompress externally or install vendor "
            "tooling — refusing to guess")
    meta, records = decode_dbn_bytes(p.read_bytes(), where=str(p))
    out = Ingested(source=str(p.resolve()), meta=meta, stype_in=meta.stype_in)
    for r in records:
        _dispatch_record(out, r, str(p))
    return out


def _ingest_csv(p: Path) -> Ingested:
    rows = parse_csv(str(p))
    if not rows:
        raise TextSchemaError(f"{p.name}: no rows")
    rtype = int(rows[0]["rtype"]) if "rtype" in rows[0] else None
    out = Ingested(source=str(p.resolve()),
                   meta=DbnMetadata(dataset="GLBX.MDP3"), stype_in=None)
    for row in rows:
        rt = int(row.get("rtype", rtype))
        rec = RawRecord(rt, int(row.get("publisher_id", 1)),
                        int(row.get("instrument_id", 0)),
                        int(row.get("ts_event", 0)), row)
        _dispatch_record(out, rec, str(p))
    return out


def _ingest_jsonl(p: Path) -> Ingested:
    rows = parse_jsonl(str(p))
    if not rows:
        raise TextSchemaError(f"{p.name}: no rows")
    out = Ingested(source=str(p.resolve()),
                   meta=DbnMetadata(dataset="GLBX.MDP3"), stype_in=None)
    for row in rows:
        rt = int(row["rtype"])
        rec = RawRecord(rt, int(row.get("publisher_id", 1)),
                        int(row.get("instrument_id", 0)),
                        int(row.get("ts_event", 0)), row)
        _dispatch_record(out, rec, str(p))
    return out


def _ch(v) -> str:
    """Normalize a c_char field to its 1-char string across paths (DBN
    decode returns str, CSV/JSON parse returns the ordinal int)."""
    if isinstance(v, str):
        return v
    return chr(v) if isinstance(v, int) and 0 <= v < 256 else str(v)


def _dispatch_record(out: Ingested, r: RawRecord, where: str) -> None:
    if r.rtype in S.OHLCV_RTYPES:
        out.bars.append(Bar(
            ts_event=r.ts_event, instrument_id=r.instrument_id,
            open=r.fields["open"], high=r.fields["high"], low=r.fields["low"],
            close=r.fields["close"], volume=r.fields["volume"], rtype=r.rtype))
    elif r.rtype == S.RTYPE_INSTRUMENT_DEF:
        f = r.fields
        out.definitions.append(DefinitionAction(
            ts_event=r.ts_event, instrument_id=r.instrument_id,
            raw_symbol=f["raw_symbol"], action=_ch(f["security_update_action"]),
            activation=f["activation"], expiration=f["expiration"],
            maturity_year=f["maturity_year"], maturity_month=f["maturity_month"],
            min_price_increment=f["min_price_increment"],
            unit_of_measure_qty=f["unit_of_measure_qty"],
            exchange=f["exchange"], security_type=f["security_type"],
            instrument_class=_ch(f["instrument_class"])))
    elif r.rtype == S.RTYPE_STATISTICS:
        f = r.fields
        if f["update_action"] not in (S.STAT_UPDATE_NEW, S.STAT_UPDATE_DELETE):
            raise IngestError(
                f"statistics update_action {f['update_action']} unknown "
                "(fail-closed)")
        out.statistics.append(Statistic(
            ts_event=f["ts_recv"], ts_ref=f["ts_ref"], instrument_id=r.instrument_id,
            stat_type=f["stat_type"], stat_flags=f["stat_flags"],
            price=f["price"], quantity=f["quantity"],
            update_action=f["update_action"]))
    elif r.rtype == S.RTYPE_MBP_0:
        f = r.fields
        out.trades.append(Trade(
            ts_event=r.ts_event, ts_recv=f["ts_recv"], instrument_id=r.instrument_id,
            price=f["price"], size=f["size"], action=_ch(f["action"]),
            side=_ch(f["side"]), flags=f["flags"], sequence=f["sequence"]))
    elif r.rtype == S.RTYPE_MBP_1:
        f = r.fields
        action = _ch(f["action"])
        if action == "T":
            out.trades.append(Trade(
                ts_event=r.ts_event, ts_recv=f["ts_recv"],
                instrument_id=r.instrument_id, price=f["price"], size=f["size"],
                action=action, side=_ch(f["side"]), flags=f["flags"],
                sequence=f["sequence"]))
        out.quotes.append(Quote(
            ts_event=r.ts_event, ts_recv=f["ts_recv"], instrument_id=r.instrument_id,
            bid_px=f["bid_px_00"], ask_px=f["ask_px_00"], bid_sz=f["bid_sz_00"],
            ask_sz=f["ask_sz_00"], action=action))
    elif r.rtype in (S.RTYPE_BBO_1S, S.RTYPE_BBO_1M):
        f = r.fields
        out.quotes.append(Quote(
            ts_event=r.ts_event, ts_recv=f["ts_recv"], instrument_id=r.instrument_id,
            bid_px=f["bid_px_00"], ask_px=f["ask_px_00"], bid_sz=f["bid_sz_00"],
            ask_sz=f["ask_sz_00"], action="N"))
    elif r.rtype in (S.RTYPE_SYMBOL_MAPPING, S.RTYPE_SYSTEM):
        # legitimate stream bookkeeping records: retained in meta, not frames
        return
    else:  # pragma: no cover - decode_dbn_bytes already fails closed earlier
        raise IngestError(f"unhandled rtype 0x{r.rtype:02x} in {where}")


def build_registry(frames: list[Ingested]) -> ContractRegistry:
    """Merge definition actions across frames, in ts order."""
    reg = ContractRegistry()
    actions = [d for f in frames for d in f.definitions]
    actions.sort(key=lambda d: d.ts_event)
    for d in actions:
        reg.apply(d)
    return reg
