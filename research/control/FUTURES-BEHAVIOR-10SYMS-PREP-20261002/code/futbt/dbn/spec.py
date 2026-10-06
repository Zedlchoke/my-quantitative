"""DBN v3 wire/format specification — byte-exact layouts for the record
subset used by this package, plus the enums and sentinels of the format.

SOURCES (all accessed 2026-10-02; official Databento reference
implementation, main branch, is the machine-readable authority because the
docs pages at databento.com are JS-rendered and not fetchable by an
automated reader — same-day WebSearch snippets confirmed the docs pages):

  * Record structs, RType values, enums, sentinels:
      https://github.com/databento/dbn/blob/main/rust/dbn/src/record.rs
      https://github.com/databento/dbn/blob/main/rust/dbn/src/enums.rs
  * DBN file prelude + metadata layout (decode_prelude / decode_metadata_impl):
      https://github.com/databento/dbn/blob/main/rust/dbn/src/decode/dbn/fsm.rs
  * Header constants (DBN prefix, fixed lengths, reserved sizes):
      https://github.com/databento/dbn/blob/main/rust/dbn/src/lib.rs
      https://github.com/databento/dbn/blob/main/rust/dbn/src/decode/dbn.rs
  * Version-specific string lengths: rust/dbn/src/compat.rs (SYMBOL_CSTR_LEN_V3=71, ...)
  * CSV/JSON column order + pretty formats:
      https://github.com/databento/dbn/blob/main/rust/dbn-macros/src/dbn_attr.rs
        (get_sorted_fields — the encode_order remove/insert algorithm)
      https://github.com/databento/dbn/blob/main/rust/dbn/src/encode/csv/serialize.rs
      https://github.com/databento/dbn/blob/main/rust/dbn/src/pretty.rs
  * Docs pages (JS-rendered; confirmed via WebSearch snippets 2026-10-02):
      https://databento.com/docs/schemas-and-data-formats/ohlcv
        ("The ts_event timestamp marks the start of each interval. If no
         trade occurs within the interval, no record is printed.")
      https://databento.com/docs/schemas-and-data-formats/statistics
        (stat_type enum incl. 3 settlement, 6 cleared volume, 9 open
         interest, 11 close, 13 VWAP; settlement flags final/preliminary
         and actual/theoretical)
      https://databento.com/docs/venues-and-datasets/glbx-mdp3
        (Stat flags table: tag 731-SettlPriceType normalized to stat_flags;
         bit 0 = final, bit 1 = actual)
      https://databento.com/docs/schemas-and-data-formats/instrument-definitions
      https://databento.com/docs/standards-and-conventions/symbology
        (stype raw_symbol/continuous/parent; continuous = ROOT.c|n|v.RANK)
      https://databento.com/docs/standards-and-conventions/databento-binary-encoding

Everything here is stdlib-only and offline. Prices are kept as exact int
nanos (fixed-point 1e-9, FIXED_PRICE_SCALE); no floats anywhere in the
value path.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Format constants (lib.rs / decode/dbn.rs / compat.rs, main@2026-10-02)
# ---------------------------------------------------------------------------

DBN_PREFIX = b"DBN"
DBN_PREFIX_LEN = 3
DBN_VERSION = 3                      # current default DBN version (v3)
METADATA_PRELUDE_LEN = 8             # b"DBN" + version u8 + metadata length u32 LE
METADATA_FIXED_LEN = 100             # minimum metadata body length enforced by decoder
METADATA_DATASET_CSTR_LEN = 16
METADATA_RESERVED_LEN = 53           # v2/v3 reserved block (v1 used 47)
SYMBOL_CSTR_LEN = 71                 # v2/v3 (v1 used 22)
ASSET_CSTR_LEN = 11                  # v3 (v1/v2 used 7)
FIXED_PRICE_SCALE = 1_000_000_000    # 1 price unit == 1e9 (i64 nanos)

NULL_SCHEMA = 0xFFFF                 # u16 sentinel: no schema in metadata
NULL_STYPE = 0xFF                    # u8 sentinel: stype_in null

UNDEF_PRICE = 2**63 - 1              # i64::MAX
UNDEF_TIMESTAMP = 2**64 - 1          # u64::MAX
UNDEF_STAT_QUANTITY = 2**63 - 1      # i64::MAX (v3)


def price_to_nanos(px_decimal_str: str) -> int:
    """'68.25' -> 68_250_000_000. Exact, via integer math on the string."""
    s = px_decimal_str.strip()
    if not s:
        raise ValueError("empty price")
    sign = 1
    if s[0] == "-":
        sign, s = -1, s[1:]
    elif s[0] == "+":
        s = s[1:]
    if "." in s:
        intpart, frac = s.split(".", 1)
    else:
        intpart, frac = s, ""
    if len(frac) > 9:
        raise ValueError(f"more than 9 decimal places: {px_decimal_str!r}")
    frac = frac.ljust(9, "0")
    if not intpart:
        intpart = "0"
    return sign * (int(intpart) * FIXED_PRICE_SCALE + int(frac))


def nanos_to_price_str(nanos: int) -> str:
    """Inverse of price_to_nanos; prints all 9 decimals (fmt_px rule).
    UNDEF_PRICE prints 'UNDEF_PRICE'."""
    if nanos == UNDEF_PRICE:
        return "UNDEF_PRICE"
    sign = "-" if nanos < 0 else ""
    a = abs(nanos)
    return f"{sign}{a // FIXED_PRICE_SCALE}.{a % FIXED_PRICE_SCALE:09d}"


# ---------------------------------------------------------------------------
# rtype values (enums.rs RType, main@2026-10-02)
# ---------------------------------------------------------------------------

RTYPE_MBP_0 = 0x00          # trades schema records
RTYPE_MBP_1 = 0x01          # mbp-1 and tbbo schema records
RTYPE_MBP_10 = 0x0A
RTYPE_OHLCV_DEPRECATED = 0x11
RTYPE_STATUS = 0x12
RTYPE_INSTRUMENT_DEF = 0x13
RTYPE_IMBALANCE = 0x14
RTYPE_ERROR = 0x15
RTYPE_SYMBOL_MAPPING = 0x16
RTYPE_SYSTEM = 0x17
RTYPE_STATISTICS = 0x18
RTYPE_OHLCV_1S = 0x20
RTYPE_OHLCV_1M = 0x21
RTYPE_OHLCV_1H = 0x22
RTYPE_OHLCV_1D = 0x23       # daily bars aggregated on the UTC date
RTYPE_OHLCV_EOD = 0x24      # daily bars aggregated at session end
RTYPE_MBO = 0xA0
RTYPE_CMBP_1 = 0xB1
RTYPE_CBBO_1S = 0xC0
RTYPE_CBBO_1M = 0xC1
RTYPE_TCBBO = 0xC2
RTYPE_BBO_1S = 0xC3
RTYPE_BBO_1M = 0xC4

OHLCV_RTYPES = frozenset({RTYPE_OHLCV_1S, RTYPE_OHLCV_1M, RTYPE_OHLCV_1H,
                          RTYPE_OHLCV_1D, RTYPE_OHLCV_EOD})

# rtypes this package can decode; anything else on the wire fails closed.
SUPPORTED_RTYPES = frozenset(
    OHLCV_RTYPES | {RTYPE_MBP_0, RTYPE_MBP_1, RTYPE_BBO_1S, RTYPE_BBO_1M,
                    RTYPE_INSTRUMENT_DEF, RTYPE_STATISTICS,
                    RTYPE_SYMBOL_MAPPING, RTYPE_SYSTEM})


# ---------------------------------------------------------------------------
# Schema / SType enums (enums.rs, main@2026-10-02)
# ---------------------------------------------------------------------------

SCHEMA_MBO = 0
SCHEMA_MBP_1 = 1
SCHEMA_MBP_10 = 2
SCHEMA_TBBO = 3
SCHEMA_TRADES = 4
SCHEMA_OHLCV_1S = 5
SCHEMA_OHLCV_1M = 6
SCHEMA_OHLCV_1H = 7
SCHEMA_OHLCV_1D = 8
SCHEMA_DEFINITION = 9
SCHEMA_STATISTICS = 10
SCHEMA_STATUS = 11
SCHEMA_IMBALANCE = 12
SCHEMA_OHLCV_EOD = 13
SCHEMA_CMBP_1 = 14
SCHEMA_CBBO_1S = 15
SCHEMA_CBBO_1M = 16
SCHEMA_TCBBO = 17
SCHEMA_BBO_1S = 18
SCHEMA_BBO_1M = 19

SCHEMA_NAMES = {
    SCHEMA_MBO: "mbo", SCHEMA_MBP_1: "mbp-1", SCHEMA_MBP_10: "mbp-10",
    SCHEMA_TBBO: "tbbo", SCHEMA_TRADES: "trades", SCHEMA_OHLCV_1S: "ohlcv-1s",
    SCHEMA_OHLCV_1M: "ohlcv-1m", SCHEMA_OHLCV_1H: "ohlcv-1h",
    SCHEMA_OHLCV_1D: "ohlcv-1d", SCHEMA_DEFINITION: "definition",
    SCHEMA_STATISTICS: "statistics", SCHEMA_STATUS: "status",
    SCHEMA_IMBALANCE: "imbalance", SCHEMA_OHLCV_EOD: "ohlcv-eod",
    SCHEMA_CMBP_1: "cmbp-1", SCHEMA_CBBO_1S: "cbbo-1s",
    SCHEMA_CBBO_1M: "cbbo-1m", SCHEMA_TCBBO: "tcbbo",
    SCHEMA_BBO_1S: "bbo-1s", SCHEMA_BBO_1M: "bbo-1m",
}
SCHEMA_BY_NAME = {v: k for k, v in SCHEMA_NAMES.items()}

STYPE_INSTRUMENT_ID = 0
STYPE_RAW_SYMBOL = 1
STYPE_SMART = 2            # deprecated
STYPE_CONTINUOUS = 3
STYPE_PARENT = 4
STYPE_NAMES = {
    STYPE_INSTRUMENT_ID: "instrument_id",
    STYPE_RAW_SYMBOL: "raw_symbol",
    STYPE_SMART: "smart",
    STYPE_CONTINUOUS: "continuous",
    STYPE_PARENT: "parent",
    5: "nasdaq_symbol", 6: "cms_symbol", 7: "isin", 8: "us_code",
    9: "bbg_comp_id", 10: "bbg_comp_ticker", 11: "figi", 12: "figi_ticker",
    13: "listing_id", 14: "issuer_id", 15: "security_id",
}

# ---------------------------------------------------------------------------
# Action / Side / class / stat enums
# ---------------------------------------------------------------------------

ACTION_ADD = ord("A")
ACTION_CANCEL = ord("C")
ACTION_MODIFY = ord("M")
ACTION_TRADE = ord("T")
ACTION_CLEAR = ord("R")
ACTION_FILL = ord("F")
ACTION_NONE = ord("N")

SIDE_ASK = ord("A")
SIDE_BID = ord("B")
SIDE_NONE = ord("N")

INSTRUMENT_CLASS_FUTURE = ord("F")
INSTRUMENT_CLASS_FUTURE_SPREAD = ord("S")
INSTRUMENT_CLASS_CALL = ord("C")
INSTRUMENT_CLASS_PUT = ord("P")

SEC_ACTION_ADD = ord("A")
SEC_ACTION_MODIFY = ord("M")
SEC_ACTION_DELETE = ord("D")
SEC_ACTION_INVALID = ord("~")

# statistics update_action (StatUpdateAction)
STAT_UPDATE_NEW = 1
STAT_UPDATE_DELETE = 2

# stat_type (enums.rs StatType, main@2026-10-02)
STAT_TYPE_OPENING_PRICE = 1
STAT_TYPE_INDICATIVE_OPENING_PRICE = 2
STAT_TYPE_SETTLEMENT_PRICE = 3
STAT_TYPE_TRADING_SESSION_LOW_PRICE = 4
STAT_TYPE_TRADING_SESSION_HIGH_PRICE = 5
STAT_TYPE_CLEARED_VOLUME = 6
STAT_TYPE_LOWEST_OFFER = 7
STAT_TYPE_HIGHEST_BID = 8
STAT_TYPE_OPEN_INTEREST = 9
STAT_TYPE_FIXING_PRICE = 10
STAT_TYPE_CLOSE_PRICE = 11
STAT_TYPE_NET_CHANGE = 12
STAT_TYPE_VWAP = 13
STAT_TYPE_NAMES = {
    1: "opening_price", 2: "indicative_opening_price", 3: "settlement_price",
    4: "trading_session_low_price", 5: "trading_session_high_price",
    6: "cleared_volume", 7: "lowest_offer", 8: "highest_bid",
    9: "open_interest", 10: "fixing_price", 11: "close_price",
    12: "net_change", 13: "vwap", 14: "volatility", 15: "delta",
    16: "uncrossing_price", 17: "upper_price_limit", 18: "lower_price_limit",
    19: "block_volume", 20: "indicative_close_price", 21: "mwcb_level1",
    22: "mwcb_level2", 23: "mwcb_level3", 24: "auction_collar_reference_price",
    25: "auction_collar_upper_price", 26: "auction_collar_lower_price",
    10001: "venue_specific_volume_1", 10002: "venue_specific_price_1",
}

# stat_flags bits for settlement prices. VERIFIED 2026-10-02 against the
# GLBX.MDP3 data-feed specification page (tag 731-SettlPriceType is
# normalized into stat_flags):
#   https://databento.com/docs/venues-and-datasets/glbx-mdp3
#     "1 << 0, 1, Whether the settlement price is final, as opposed to
#      preliminary. 1 << 1, 2, Whether the settlement price is actual, as
#      opposed to theoretical."
# CAVEAT (published data-quality issue, access 2026-10-02): normalization
# is inconsistent on GLBX.MDP3 for data prior to 2015-01-20
# (https://issues.databento.com/roadmap/glbxmdp3-inconsistent-normalization-of-settlement-price-stat-flags-prior-to-2015-01-20).
STAT_FLAG_FINAL = 0x01
STAT_FLAG_ACTUAL = 0x02

# flags bitfield (flags.rs, main@2026-10-02)
FLAG_LAST = 1 << 7
FLAG_TOB = 1 << 6
FLAG_SNAPSHOT = 1 << 5
FLAG_MBP = 1 << 4
FLAG_BAD_TS_RECV = 1 << 3
FLAG_MAYBE_BAD_BOOK = 1 << 2
FLAG_PUBLISHER_SPECIFIC = 1 << 1

# ---------------------------------------------------------------------------
# Record field layouts
# ---------------------------------------------------------------------------

HEADER_FMT = "<BBHIQ"      # length(words u8), rtype u8, publisher_id u16,
HEADER_SIZE = 16           # instrument_id u32, ts_event u64


@dataclass(frozen=True)
class Field:
    name: str
    code: str              # struct format char (after '<')
    kind: str = "int"      # int | px | ts | char | cstr | skip | bytes
    encode_order: int | None = None


def _hdr_fields() -> list[Field]:
    return [
        Field("length", "B", "skip"),
        Field("rtype", "B"),
        Field("publisher_id", "H"),
        Field("instrument_id", "I"),
        Field("ts_event", "Q", "ts", encode_order=0),
    ]


def _sorted_fields(fields: list[Field]) -> list[Field]:
    """Exact port of dbn-macros get_sorted_fields (dbn_attr.rs): fields with
    an encode_order, ascending, are removed and re-inserted at that index
    (pushed to the back if the index is past the end)."""
    order_fields = sorted((f for f in fields if f.encode_order is not None),
                          key=lambda f: f.encode_order)
    out = list(fields)
    for f in order_fields:
        out.remove(f)
        if f.encode_order >= len(out):
            out.append(f)
        else:
            out.insert(f.encode_order, f)
    return out


@dataclass(frozen=True)
class RecordSpec:
    name: str
    rtypes: tuple[int, ...]
    fields: tuple[Field, ...]        # AFTER the common header
    size: int                        # total bytes including header

    @property
    def words(self) -> int:
        return self.size // 4

    def body_fmt(self) -> str:
        return "<" + "".join(f.code for f in self.fields)

    def sorted_for_text(self) -> list[Field]:
        """Column order for CSV/JSON exports, exactly per the reference.

        Model (dbn-macros get_sorted_fields + the flattening WriteField for
        RecordHeader, verified 2026-10-02):
          1. The RecordHeader participates in the record's field list as ONE
             slot at its natural position (first); get_sorted_fields then
             removes/re-inserts fields with an encode_order at that index of
             the SLOT list (so e.g. encode_order=2 lands directly after the
             ts_recv + header slots, not two columns after ts_event).
          2. At write time the header slot is flattened into the header's own
             sorted order: ts_event, rtype, publisher_id, instrument_id.
        """
        hd_slot = Field("__hd__", "", "skip")
        slots = _sorted_fields([hd_slot] + [f for f in self.fields
                                            if f.kind != "skip"])
        hdr_sorted = _sorted_fields([f for f in _hdr_fields()
                                     if f.kind != "skip"])
        out: list[Field] = []
        for f in slots:
            if f.name == "__hd__":
                out.extend(hdr_sorted)
            else:
                out.append(f)
        return out


def _mk(name: str, rtypes: tuple[int, ...], body: list[Field], size: int) -> RecordSpec:
    spec_ = RecordSpec(name=name, rtypes=rtypes, fields=tuple(body), size=size)
    got = HEADER_SIZE + struct.calcsize(spec_.body_fmt())
    assert got == size, f"{name}: layout mismatch {got} != {size}"
    assert size % 4 == 0, f"{name}: size not 4-byte aligned"
    return spec_


OHLCV_SPEC = _mk("OhlcvMsg", (RTYPE_OHLCV_1S, RTYPE_OHLCV_1M, RTYPE_OHLCV_1H,
                              RTYPE_OHLCV_1D, RTYPE_OHLCV_EOD), [
    Field("open", "q", "px"),
    Field("high", "q", "px"),
    Field("low", "q", "px"),
    Field("close", "q", "px"),
    Field("volume", "Q"),
], 56)

_TRADE_BODY = [
    Field("price", "q", "px"),
    Field("size", "I"),
    Field("action", "B", "char", encode_order=2),
    Field("side", "B", "char", encode_order=3),
    Field("flags", "B"),
    Field("depth", "B", encode_order=4),
    Field("ts_recv", "Q", "ts", encode_order=0),
    Field("ts_in_delta", "i"),
    Field("sequence", "I"),
]

TRADE_SPEC = _mk("TradeMsg", (RTYPE_MBP_0,), _TRADE_BODY, 48)

_LEVELS_BODY = _TRADE_BODY + [
    Field("bid_px_00", "q", "px"),
    Field("ask_px_00", "q", "px"),
    Field("bid_sz_00", "I"),
    Field("ask_sz_00", "I"),
    Field("bid_ct_00", "I"),
    Field("ask_ct_00", "I"),
]
MBP1_SPEC = _mk("Mbp1Msg", (RTYPE_MBP_1,), _LEVELS_BODY, 80)

TBBO_SPEC = _mk("TbboMsg", (RTYPE_MBP_1,), _LEVELS_BODY, 80)  # same rtype, tbbo schema

STAT_SPEC = _mk("StatMsg", (RTYPE_STATISTICS,), [
    Field("ts_recv", "Q", "ts", encode_order=0),
    Field("ts_ref", "Q", "ts"),
    Field("price", "q", "px"),
    Field("quantity", "q"),
    Field("sequence", "I"),
    Field("ts_in_delta", "i"),
    Field("stat_type", "H"),
    Field("channel_id", "H"),
    Field("update_action", "B"),
    Field("stat_flags", "B"),
    Field("_reserved", "18s", "skip"),
], 80)

DEF_SPEC = _mk("InstrumentDefMsg", (RTYPE_INSTRUMENT_DEF,), [
    Field("ts_recv", "Q", "ts", encode_order=0),
    Field("min_price_increment", "q", "px"),
    Field("display_factor", "q", "px"),
    Field("expiration", "Q", "ts"),
    Field("activation", "Q", "ts"),
    Field("high_limit_price", "q", "px"),
    Field("low_limit_price", "q", "px"),
    Field("max_price_variation", "q", "px"),
    Field("unit_of_measure_qty", "q", "px"),
    Field("min_price_increment_amount", "q", "px"),
    Field("price_ratio", "q", "px"),
    Field("strike_price", "q", "px", encode_order=54),
    Field("raw_instrument_id", "Q", encode_order=20),
    Field("leg_price", "q", "px", encode_order=165),
    Field("leg_delta", "q", "px", encode_order=166),
    Field("inst_attrib_value", "i"),
    Field("underlying_id", "I"),
    Field("market_depth_implied", "i"),
    Field("market_depth", "i"),
    Field("market_segment_id", "I"),
    Field("max_trade_vol", "I"),
    Field("min_lot_size", "i"),
    Field("min_lot_size_block", "i"),
    Field("min_lot_size_round_lot", "i"),
    Field("min_trade_vol", "I"),
    Field("contract_multiplier", "i"),
    Field("decay_quantity", "i"),
    Field("original_contract_size", "i"),
    Field("leg_instrument_id", "I", encode_order=160),
    Field("leg_ratio_price_numerator", "i", encode_order=167),
    Field("leg_ratio_price_denominator", "i", encode_order=168),
    Field("leg_ratio_qty_numerator", "i", encode_order=169),
    Field("leg_ratio_qty_denominator", "i", encode_order=170),
    Field("leg_underlying_id", "I", encode_order=171),
    Field("appl_id", "h"),
    Field("maturity_year", "H"),
    Field("decay_start_date", "H"),
    Field("channel_id", "H"),
    Field("leg_count", "H", encode_order=158),
    Field("leg_index", "H", encode_order=159),
    Field("currency", "4s", "cstr"),
    Field("settl_currency", "4s", "cstr"),
    Field("secsubtype", "6s", "cstr"),
    Field("raw_symbol", f"{SYMBOL_CSTR_LEN}s", "cstr", encode_order=2),
    Field("group", "21s", "cstr"),
    Field("exchange", "5s", "cstr"),
    Field("asset", f"{ASSET_CSTR_LEN}s", "cstr"),
    Field("cfi", "7s", "cstr"),
    Field("security_type", "7s", "cstr"),
    Field("unit_of_measure", "31s", "cstr"),
    Field("underlying", "21s", "cstr"),
    Field("strike_price_currency", "4s", "cstr"),
    Field("leg_raw_symbol", f"{SYMBOL_CSTR_LEN}s", "cstr", encode_order=161),
    Field("instrument_class", "B", "char", encode_order=4),
    Field("match_algorithm", "B", "char"),
    Field("main_fraction", "B"),
    Field("price_display_format", "B"),
    Field("sub_fraction", "B"),
    Field("underlying_product", "B"),
    Field("security_update_action", "B", "char", encode_order=3),
    Field("maturity_month", "B"),
    Field("maturity_day", "B"),
    Field("maturity_week", "B"),
    Field("user_defined_instrument", "B", "char"),
    Field("contract_multiplier_unit", "b"),
    Field("flow_schedule_type", "b"),
    Field("tick_rule", "B"),
    Field("leg_instrument_class", "B", "char", encode_order=163),
    Field("leg_side", "B", "char", encode_order=164),
    Field("_reserved", "17s", "skip"),
], 520)

SYMBOL_MAPPING_SPEC = _mk("SymbolMappingMsg", (RTYPE_SYMBOL_MAPPING,), [
    Field("stype_in", "B"),
    Field("stype_in_symbol", f"{SYMBOL_CSTR_LEN}s", "cstr"),
    Field("stype_out", "B"),
    Field("stype_out_symbol", f"{SYMBOL_CSTR_LEN}s", "cstr"),
    Field("start_ts", "Q", "ts"),
    Field("end_ts", "Q", "ts"),
], 176)

SYSTEM_SPEC = _mk("SystemMsg", (RTYPE_SYSTEM,), [
    Field("msg", "303s", "cstr"),
    Field("code", "B"),
], 320)

BBO_1M_SPEC = _mk("BboMsg", (RTYPE_BBO_1S, RTYPE_BBO_1M), [
    Field("price", "q", "px"),
    Field("size", "I"),
    Field("_reserved1", "B", "skip"),
    Field("side", "B", "char", encode_order=2),
    Field("flags", "B"),
    Field("_reserved2", "B", "skip"),
    Field("ts_recv", "Q", "ts", encode_order=0),
    Field("_reserved3", "4s", "skip"),
    Field("sequence", "I"),
    Field("bid_px_00", "q", "px"),
    Field("ask_px_00", "q", "px"),
    Field("bid_sz_00", "I"),
    Field("ask_sz_00", "I"),
    Field("bid_ct_00", "I"),
    Field("ask_ct_00", "I"),
], 80)

SPECS_BY_RTYPE: dict[int, RecordSpec] = {}
for _s in (OHLCV_SPEC, TRADE_SPEC, MBP1_SPEC, STAT_SPEC, DEF_SPEC,
           SYMBOL_MAPPING_SPEC, SYSTEM_SPEC, BBO_1M_SPEC):
    for _r in _s.rtypes:
        SPECS_BY_RTYPE[_r] = _s


class DbnFormatError(ValueError):
    """Malformed DBN bytes (bad magic/version/length/alignment)."""


class UnknownRecordTypeError(DbnFormatError):
    """Fail-closed: a record type we do not implement was encountered.

    Never silently skipped — the caller must decide how to proceed.
    """

    def __init__(self, rtype: int, where: str = ""):
        self.rtype = rtype
        super().__init__(
            f"unknown/unsupported DBN rtype 0x{rtype:02x} "
            f"({'at ' + where if where else ''}this package implements "
            f"{sorted(hex(r) for r in SUPPORTED_RTYPES)}); refusing to "
            f"silently skip (fail-closed)")


# ---------------------------------------------------------------------------
# Pack / unpack
# ---------------------------------------------------------------------------

def _clean(value, fld: Field):
    if fld.kind == "cstr" or (fld.kind == "bytes" and fld.code.endswith("s")):
        if isinstance(value, str):
            raw = value.encode("utf-8")
        elif isinstance(value, (bytes, bytearray)):
            raw = bytes(value)
        else:
            raw = b""
        n = int(fld.code[:-1])
        if len(raw) > n:
            raise ValueError(f"{fld.name}: cstr too long ({len(raw)} > {n})")
        return raw.ljust(n, b"\x00")
    if fld.kind == "char":
        if isinstance(value, str):
            if len(value) != 1:
                raise ValueError(f"{fld.name}: single char expected")
            return ord(value)
        return int(value)
    return int(value)


def _restore(value, fld: Field):
    if fld.kind == "cstr":
        return bytes(value).rstrip(b"\x00").decode("utf-8")
    if fld.kind == "char":
        return chr(value) if 0 <= value < 256 else value
    return value


def _zero_for(fld: Field):
    """Zero fill for a skipped (reserved) field, matching its struct code."""
    if fld.code.endswith("s"):
        return b"\x00" * int(fld.code[:-1])
    return 0


def pack_record(rtype: int, ts_event: int, values: dict,
                publisher_id: int = 1, instrument_id: int = 0) -> bytes:
    spec_ = SPECS_BY_RTYPE.get(rtype)
    if spec_ is None:
        raise UnknownRecordTypeError(rtype, "pack_record")
    body = tuple(_zero_for(f) if f.kind == "skip"
                 else _clean(values.get(f.name, 0), f)
                 for f in spec_.fields)
    body_bytes = struct.pack(spec_.body_fmt(), *body)
    words = (HEADER_SIZE + len(body_bytes)) // 4
    header = struct.pack(HEADER_FMT, words, rtype, publisher_id,
                         instrument_id, ts_event)
    return header + body_bytes


def unpack_record(rtype: int, buf: bytes, where: str = "") -> dict:
    spec_ = SPECS_BY_RTYPE.get(rtype)
    if spec_ is None:
        raise UnknownRecordTypeError(rtype, where)
    if len(buf) < spec_.size:
        raise DbnFormatError(
            f"{where}: buffer {len(buf)} < {spec_.size} for {spec_.name}")
    raw = struct.unpack(spec_.body_fmt(), buf[HEADER_SIZE:spec_.size])
    # zip over ALL fields keeps skip fields aligned; they are dropped from
    # the returned dict (reserved wire bytes are never exposed).
    out = {f.name: _restore(v, f) for f, v in zip(spec_.fields, raw)
           if f.kind != "skip"}
    return out


def read_header(buf: bytes) -> tuple[int, int, int, int, int]:
    """Returns (length_words, rtype, publisher_id, instrument_id, ts_event)."""
    if len(buf) < HEADER_SIZE:
        raise DbnFormatError("record buffer shorter than the 16-byte header")
    return struct.unpack(HEADER_FMT, buf[:HEADER_SIZE])


def record_name_for_rtype(rtype: int) -> str | None:
    s = SPECS_BY_RTYPE.get(rtype)
    return s.name if s else None
