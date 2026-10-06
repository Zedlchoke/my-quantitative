"""DBN binary file/stream encode+decode for the supported record subset.

Byte-exact implementation of the CURRENT (v3) format per the official
reference decoder (rust/dbn/src/decode/dbn/fsm.rs, databento/dbn
main@2026-10-02; see spec.py header for the full source list):

  prelude : b"DBN" | version u8 | metadata_length u32 LE
  metadata: dataset cstr[16] | schema u16 | start u64 | end u64 | limit u64
            | stype_in u8 | stype_out u8 | ts_out u8 | symbol_cstr_len u16
            | reserved[53] | schema_definition_length u32 (must be 0)
            | symbols: u32 count + cstr[]   | partial: u32 + cstr[]
            | not_found: u32 + cstr[]
            | mappings: u32 count, each { raw_symbol cstr,
                u32 interval_count, each { start_date u32 YYYYMMDD,
                end_date u32, symbol cstr } }
  records: length-prefixed by the header word count (length u8 = 4-byte words)

NOT_IMPLEMENTED (typed): DBN v1/v2 metadata/record compat (we reject
versions != 3), .zst decompression (Python stdlib has no zstd in 3.12),
and every record type outside SUPPORTED_RTYPES — those raise
UnknownRecordTypeError, never a silent skip.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

from . import spec as S
from .spec import DbnFormatError, UnknownRecordTypeError


@dataclass
class MappingInterval:
    start_date: int          # YYYYMMDD
    end_date: int            # YYYYMMDD, inclusive
    symbol: str


@dataclass
class SymbolMapping:
    raw_symbol: str
    intervals: list[MappingInterval] = field(default_factory=list)


@dataclass
class DbnMetadata:
    version: int = S.DBN_VERSION
    dataset: str = "GLBX.MDP3"
    schema: int | None = None
    start: int = 0                       # ns since epoch
    end: int | None = None               # None == UNDEF_TIMESTAMP
    limit: int | None = None
    stype_in: int | None = S.STYPE_RAW_SYMBOL
    stype_out: int = S.STYPE_RAW_SYMBOL
    ts_out: bool = False
    symbols: list[str] = field(default_factory=list)
    partial: list[str] = field(default_factory=list)
    not_found: list[str] = field(default_factory=list)
    mappings: list[SymbolMapping] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version, "dataset": self.dataset,
            "schema": S.SCHEMA_NAMES.get(self.schema) if self.schema is not None else None,
            "start": self.start, "end": self.end, "limit": self.limit,
            "stype_in": S.STYPE_NAMES.get(self.stype_in) if self.stype_in is not None else None,
            "stype_out": S.STYPE_NAMES.get(self.stype_out),
            "ts_out": self.ts_out, "symbols": list(self.symbols),
            "partial": list(self.partial), "not_found": list(self.not_found),
            "mappings": [
                {"raw_symbol": m.raw_symbol,
                 "intervals": [{"start_date": i.start_date,
                                "end_date": i.end_date,
                                "symbol": i.symbol} for i in m.intervals]}
                for m in self.mappings
            ],
        }


@dataclass
class RawRecord:
    rtype: int
    publisher_id: int
    instrument_id: int
    ts_event: int
    fields: dict          # decoded body fields (without header)


def _cstr16(s: str) -> bytes:
    raw = s.encode("utf-8")[: S.METADATA_DATASET_CSTR_LEN]
    return raw.ljust(S.METADATA_DATASET_CSTR_LEN, b"\x00")


def _cstr_sym(s: str) -> bytes:
    raw = s.encode("utf-8")[: S.SYMBOL_CSTR_LEN]
    return raw.ljust(S.SYMBOL_CSTR_LEN, b"\x00")


def encode_metadata(meta: DbnMetadata) -> bytes:
    body = bytearray()
    body += _cstr16(meta.dataset)
    body += struct.pack("<H", S.NULL_SCHEMA if meta.schema is None else meta.schema)
    body += struct.pack("<Q", meta.start)
    body += struct.pack("<Q", S.UNDEF_TIMESTAMP if meta.end is None else meta.end)
    body += struct.pack("<Q", meta.limit if meta.limit is not None else 0)
    body += struct.pack("<B", S.NULL_STYPE if meta.stype_in is None else meta.stype_in)
    body += struct.pack("<B", meta.stype_out)
    body += struct.pack("<B", 1 if meta.ts_out else 0)
    body += struct.pack("<H", S.SYMBOL_CSTR_LEN)
    body += b"\x00" * S.METADATA_RESERVED_LEN
    body += struct.pack("<I", 0)             # schema_definition_length
    for group in (meta.symbols, meta.partial, meta.not_found):
        body += struct.pack("<I", len(group))
        for sym in group:
            body += _cstr_sym(sym)
    body += struct.pack("<I", len(meta.mappings))
    for m in meta.mappings:
        body += _cstr_sym(m.raw_symbol)
        body += struct.pack("<I", len(m.intervals))
        for iv in m.intervals:
            body += struct.pack("<II", iv.start_date, iv.end_date)
            body += _cstr_sym(iv.symbol)
    if len(body) < S.METADATA_FIXED_LEN:
        raise DbnFormatError("metadata body shorter than fixed length")
    prelude = S.DBN_PREFIX + bytes([S.DBN_VERSION]) + struct.pack("<I", len(body))
    return prelude + bytes(body)


def decode_metadata_from_blob(body: bytes, version: int) -> DbnMetadata:
    """Decode a metadata body (the `metadata_length` bytes after prelude)."""
    if version != S.DBN_VERSION:
        raise DbnFormatError(
            f"DBN version {version} is NOT_IMPLEMENTED for decode "
            f"(this package decodes v3 only); refusing to guess")
    if len(body) < S.METADATA_FIXED_LEN:
        raise DbnFormatError("metadata shorter than fixed length")
    pos = 0
    dataset = body[pos:pos + S.METADATA_DATASET_CSTR_LEN].rstrip(b"\x00").decode("utf-8")
    pos += S.METADATA_DATASET_CSTR_LEN
    (raw_schema,) = struct.unpack_from("<H", body, pos); pos += 2
    schema = None if raw_schema == S.NULL_SCHEMA else raw_schema
    start, end, limit = struct.unpack_from("<QQQ", body, pos); pos += 24
    stype_in_raw = body[pos]; pos += 1
    stype_in = None if stype_in_raw == S.NULL_STYPE else stype_in_raw
    stype_out = body[pos]; pos += 1
    ts_out = body[pos] != 0; pos += 1
    (symbol_cstr_len,) = struct.unpack_from("<H", body, pos); pos += 2
    if symbol_cstr_len != S.SYMBOL_CSTR_LEN:
        raise DbnFormatError(
            f"symbol_cstr_len {symbol_cstr_len} != v3 {S.SYMBOL_CSTR_LEN} "
            "(v1/v2 compat NOT_IMPLEMENTED)")
    pos += S.METADATA_RESERVED_LEN
    (schema_def_len,) = struct.unpack_from("<I", body, pos); pos += 4
    if schema_def_len != 0:
        raise DbnFormatError("schema definitions are NOT_IMPLEMENTED")

    def read_symbol_list() -> list[str]:
        nonlocal pos
        (count,) = struct.unpack_from("<I", body, pos); pos += 4
        out = []
        for _ in range(count):
            out.append(body[pos:pos + symbol_cstr_len].rstrip(b"\x00").decode("utf-8"))
            pos += symbol_cstr_len
        return out

    symbols = read_symbol_list()
    partial = read_symbol_list()
    not_found = read_symbol_list()
    (map_count,) = struct.unpack_from("<I", body, pos); pos += 4
    mappings = []
    for _ in range(map_count):
        raw_symbol = body[pos:pos + symbol_cstr_len].rstrip(b"\x00").decode("utf-8")
        pos += symbol_cstr_len
        (iv_count,) = struct.unpack_from("<I", body, pos); pos += 4
        intervals = []
        for _ in range(iv_count):
            sd, ed = struct.unpack_from("<II", body, pos); pos += 8
            sym = body[pos:pos + symbol_cstr_len].rstrip(b"\x00").decode("utf-8")
            pos += symbol_cstr_len
            intervals.append(MappingInterval(sd, ed, sym))
        mappings.append(SymbolMapping(raw_symbol, intervals))
    return DbnMetadata(
        version=version, dataset=dataset, schema=schema, start=start,
        end=None if end == S.UNDEF_TIMESTAMP else end,
        limit=limit if limit else None,
        stype_in=stype_in, stype_out=stype_out, ts_out=ts_out,
        symbols=symbols, partial=partial, not_found=not_found, mappings=mappings,
    )


def write_dbn(path, meta: DbnMetadata, records: list[tuple[int, bytes]]) -> None:
    """`records`: (rtype, packed_record_bytes) in file order."""
    with open(path, "wb") as fh:
        fh.write(encode_metadata(meta))
        for _, blob in records:
            fh.write(blob)


def read_dbn(path) -> tuple[DbnMetadata, list[RawRecord]]:
    """Full-file decode. Fails closed on unknown record types."""
    with open(path, "rb") as fh:
        data = fh.read()
    return decode_dbn_bytes(data, where=str(path))


def decode_dbn_bytes(data: bytes, where: str = "<bytes>") -> tuple[DbnMetadata, list[RawRecord]]:
    if len(data) < S.METADATA_PRELUDE_LEN:
        raise DbnFormatError(f"{where}: shorter than the 8-byte DBN prelude")
    if data[:S.DBN_PREFIX_LEN] != S.DBN_PREFIX:
        raise DbnFormatError(
            f"{where}: bad magic {data[:S.DBN_PREFIX_LEN]!r} (expected b'DBN')")
    version = data[S.DBN_PREFIX_LEN]
    if version > S.DBN_VERSION:
        raise DbnFormatError(
            f"{where}: DBN version {version} is newer than implemented "
            f"v{S.DBN_VERSION}; refusing to guess")
    (meta_len,) = struct.unpack_from("<I", data, 4)
    if meta_len < S.METADATA_FIXED_LEN:
        raise DbnFormatError(f"{where}: metadata length {meta_len} < fixed {S.METADATA_FIXED_LEN}")
    body_end = S.METADATA_PRELUDE_LEN + meta_len
    if len(data) < body_end:
        raise DbnFormatError(f"{where}: truncated metadata")
    meta = decode_metadata_from_blob(data[S.METADATA_PRELUDE_LEN:body_end], version)
    pos = body_end
    out: list[RawRecord] = []
    while pos < len(data):
        if len(data) - pos < S.HEADER_SIZE:
            raise DbnFormatError(f"{where}: trailing garbage after last record")
        words, rtype, pub, inst, ts_event = S.read_header(data[pos:pos + S.HEADER_SIZE])
        size = words * 4
        if size < S.HEADER_SIZE or size % 4 != 0:
            raise DbnFormatError(f"{where}: invalid record length {words} words")
        blob = data[pos:pos + size]
        if len(blob) < size:
            raise DbnFormatError(f"{where}: truncated record rtype 0x{rtype:02x}")
        pos += size
        if rtype not in S.SUPPORTED_RTYPES:
            raise UnknownRecordTypeError(rtype, where)
        rec_spec = S.SPECS_BY_RTYPE[rtype]
        if size != rec_spec.size:
            raise DbnFormatError(
                f"{where}: rtype 0x{rtype:02x} record size {size} != layout "
                f"{rec_spec.size} ({rec_spec.name})")
        fields = S.unpack_record(rtype, blob, where)
        out.append(RawRecord(rtype, pub, inst, ts_event, fields))
    return meta, out
