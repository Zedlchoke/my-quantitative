"""DBN v3 wire-format tests: framing, metadata, record layouts, pack/
unpack round-trips, CSV/JSONL export shapes (synthetic fixtures only).

Verifies the byte-level port against layouts confirmed from the official
reference implementation (databento/dbn main@2026-10-02; URLs in
futbt/dbn/spec.py header and dbn/README.md).
"""
from __future__ import annotations

import unittest

from futbt.dbn import spec as S
from futbt.dbn import textio
from futbt.dbn.fixtures import build_fixture_dir
from futbt.dbn.wire import (DbnMetadata, MappingInterval, SymbolMapping,
                            decode_dbn_bytes, encode_metadata,
                            decode_metadata_from_blob, read_dbn, write_dbn)


class FixtureBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmp = tempfile.TemporaryDirectory(prefix="dbn_wire_")
        cls.universe = build_fixture_dir(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def path(self, name: str) -> str:
        return f"{self.tmp.name}/{name}"


class TestPriceSentinels(unittest.TestCase):
    def test_price_to_nanos_exact(self):
        self.assertEqual(S.price_to_nanos("68.25"), 68_250_000_000)
        self.assertEqual(S.price_to_nanos("0.006335"), 6_335_000)
        self.assertEqual(S.price_to_nanos("-2.75"), -2_750_000_000)
        self.assertEqual(S.price_to_nanos("17350.25"), 17_350_250_000_000)
        self.assertEqual(S.price_to_nanos("0"), 0)

    def test_price_roundtrip_str(self):
        cases = {"68.25": "68.250000000", "-2.75": "-2.750000000",
                 "0.006335": "0.006335000", "17350.25": "17350.250000000",
                 "0": "0.000000000"}
        for s, expect in cases.items():
            self.assertEqual(S.nanos_to_price_str(S.price_to_nanos(s)), expect)

    def test_more_than_9_decimals_refused(self):
        with self.assertRaises(ValueError):
            S.price_to_nanos("0.0000000001")

    def test_undef_sentinels_match_reference(self):
        # lib.rs main@2026-10-02: UNDEF_PRICE i64::MAX, UNDEF_TIMESTAMP
        # u64::MAX, UNDEF_STAT_QUANTITY (v3) i64::MAX.
        self.assertEqual(S.UNDEF_PRICE, 2**63 - 1)
        self.assertEqual(S.UNDEF_TIMESTAMP, 2**64 - 1)
        self.assertEqual(S.UNDEF_STAT_QUANTITY, 2**63 - 1)
        self.assertEqual(S.FIXED_PRICE_SCALE, 1_000_000_000)


class TestRecordLayouts(unittest.TestCase):
    """Byte sizes are part of the documented wire format."""

    def test_layout_sizes(self):
        # record.rs main@2026-10-02: OhlcvMsg 56, TradeMsg 48, Mbp1Msg 80,
        # StatMsg 80, InstrumentDefMsg 520, SymbolMappingMsg 176 (with
        # SYMBOL_CSTR_LEN=71), SystemMsg 320, BboMsg 80.
        self.assertEqual(S.OHLCV_SPEC.size, 56)
        self.assertEqual(S.TRADE_SPEC.size, 48)
        self.assertEqual(S.MBP1_SPEC.size, 80)
        self.assertEqual(S.STAT_SPEC.size, 80)
        self.assertEqual(S.DEF_SPEC.size, 520)
        self.assertEqual(S.SYMBOL_MAPPING_SPEC.size, 176)
        self.assertEqual(S.SYSTEM_SPEC.size, 320)
        self.assertEqual(S.BBO_1M_SPEC.size, 80)

    def test_header_layout(self):
        self.assertEqual(S.HEADER_SIZE, 16)
        # length is in 4-byte words (RecordHeader::LENGTH_MULTIPLIER == 4)
        self.assertEqual(S.OHLCV_SPEC.size % 4, 0)
        self.assertEqual(S.OHLCV_SPEC.words, 14)

    def test_rtype_enum_values_match_reference(self):
        self.assertEqual(S.RTYPE_MBP_0, 0x00)
        self.assertEqual(S.RTYPE_MBP_1, 0x01)
        self.assertEqual(S.RTYPE_INSTRUMENT_DEF, 0x13)
        self.assertEqual(S.RTYPE_SYMBOL_MAPPING, 0x16)
        self.assertEqual(S.RTYPE_SYSTEM, 0x17)
        self.assertEqual(S.RTYPE_STATISTICS, 0x18)
        self.assertEqual(S.RTYPE_OHLCV_1M, 0x21)
        self.assertEqual(S.RTYPE_OHLCV_1D, 0x23)
        self.assertEqual(S.RTYPE_OHLCV_EOD, 0x24)
        self.assertEqual(S.RTYPE_BBO_1S, 0xC3)
        self.assertEqual(S.RTYPE_BBO_1M, 0xC4)

    def test_schema_and_stype_enums(self):
        self.assertEqual(S.SCHEMA_BY_NAME["ohlcv-1d"], 8)
        self.assertEqual(S.SCHEMA_BY_NAME["definition"], 9)
        self.assertEqual(S.SCHEMA_BY_NAME["statistics"], 10)
        self.assertEqual(S.STYPE_INSTRUMENT_ID, 0)
        self.assertEqual(S.STYPE_RAW_SYMBOL, 1)
        self.assertEqual(S.STYPE_CONTINUOUS, 3)
        self.assertEqual(S.STYPE_PARENT, 4)

    def test_stat_types_match_reference(self):
        self.assertEqual(S.STAT_TYPE_SETTLEMENT_PRICE, 3)
        self.assertEqual(S.STAT_TYPE_CLEARED_VOLUME, 6)
        self.assertEqual(S.STAT_TYPE_OPEN_INTEREST, 9)
        self.assertEqual(S.STAT_TYPE_CLOSE_PRICE, 11)
        self.assertEqual(S.STAT_TYPE_VWAP, 13)

    def test_stat_flags_glbx_semantics(self):
        # GLBX.MDP3 spec: bit 0 = final, bit 1 = ACTUAL (not theoretical).
        self.assertEqual(S.STAT_FLAG_FINAL, 0x01)
        self.assertEqual(S.STAT_FLAG_ACTUAL, 0x02)

    def test_flag_bits_match_reference(self):
        # flags.rs main@2026-10-02
        self.assertEqual(S.FLAG_LAST, 1 << 7)
        self.assertEqual(S.FLAG_TOB, 1 << 6)
        self.assertEqual(S.FLAG_SNAPSHOT, 1 << 5)
        self.assertEqual(S.FLAG_MBP, 1 << 4)
        self.assertEqual(S.FLAG_BAD_TS_RECV, 1 << 3)
        self.assertEqual(S.FLAG_MAYBE_BAD_BOOK, 1 << 2)
        self.assertEqual(S.FLAG_PUBLISHER_SPECIFIC, 1 << 1)


class TestPackUnpack(unittest.TestCase):
    def test_ohlcv_roundtrip(self):
        vals = dict(open=1, high=5, low=-3, close=2, volume=123)
        blob = S.pack_record(S.RTYPE_OHLCV_1D, 77, vals, 1, 4242)
        self.assertEqual(len(blob), 56)
        words, rtype, pub, inst, ts = S.read_header(blob)
        self.assertEqual((words, rtype, pub, inst, ts), (14, 0x23, 1, 4242, 77))
        out = S.unpack_record(S.RTYPE_OHLCV_1D, blob)
        self.assertEqual(out["open"], 1)
        self.assertEqual(out["low"], -3)
        self.assertEqual(out["volume"], 123)

    def test_trade_roundtrip_with_encode_orders(self):
        vals = dict(price=4826_000_000_000, size=12, action="T", side="B",
                    flags=128, depth=0, ts_recv=55, ts_in_delta=100,
                    sequence=9)
        blob = S.pack_record(S.RTYPE_MBP_0, 54, vals, 1, 7)
        self.assertEqual(len(blob), 48)
        out = S.unpack_record(S.RTYPE_MBP_0, blob)
        self.assertEqual(out["action"], "T")
        self.assertEqual(out["side"], "B")
        self.assertEqual(out["ts_recv"], 55)

    def test_bbo_reserved_fields_roundtrip(self):
        # BboMsg carries three hidden reserved fields; pack must zero-fill
        # them and unpack must skip them WITHOUT mis-aligning later fields
        # (predecessor bug: zip truncation silently shifted columns).
        vals = dict(price=100, size=5, side="B", flags=64, ts_recv=200,
                    sequence=7, bid_px_00=1, ask_px_00=2, bid_sz_00=3,
                    ask_sz_00=4, bid_ct_00=5, ask_ct_00=6)
        blob = S.pack_record(S.RTYPE_BBO_1M, 111, vals, 1, 42)
        self.assertEqual(len(blob), 80)
        out = S.unpack_record(S.RTYPE_BBO_1M, blob)
        self.assertEqual(out["sequence"], 7)       # after reserved3
        self.assertEqual(out["bid_px_00"], 1)
        self.assertEqual(out["ask_ct_00"], 6)
        self.assertNotIn("_reserved1", out)
        self.assertNotIn("_reserved2", out)
        self.assertNotIn("_reserved3", out)

    def test_stat_roundtrip_reserved18(self):
        vals = dict(ts_recv=1, ts_ref=2, price=3, quantity=4, sequence=5,
                    ts_in_delta=6, stat_type=3, channel_id=0,
                    update_action=1, stat_flags=1)
        blob = S.pack_record(S.RTYPE_STATISTICS, 9, vals, 1, 8)
        self.assertEqual(len(blob), 80)
        out = S.unpack_record(S.RTYPE_STATISTICS, blob)
        self.assertEqual(out["stat_type"], 3)      # after the 18s reserved
        self.assertEqual(out["stat_flags"], 1)
        self.assertEqual(out["update_action"], 1)

    def test_definition_roundtrip(self):
        vals = dict(ts_recv=10, min_price_increment=250_000_000,
                    raw_symbol="ESZ6", exchange="CME", group="ES",
                    security_update_action="A", instrument_class="F",
                    maturity_year=2026, maturity_month=12,
                    expiration=99, activation=11)
        blob = S.pack_record(S.RTYPE_INSTRUMENT_DEF, 10, vals, 1, 5)
        self.assertEqual(len(blob), 520)
        out = S.unpack_record(S.RTYPE_INSTRUMENT_DEF, blob)
        self.assertEqual(out["raw_symbol"], "ESZ6")
        self.assertEqual(out["security_update_action"], "A")
        self.assertEqual(out["min_price_increment"], 250_000_000)
        self.assertEqual(out["underlying"], "")    # cstr zero-fill -> ""

    def test_pack_unknown_rtype_fails_closed(self):
        with self.assertRaises(S.UnknownRecordTypeError):
            S.pack_record(0xA0, 1, {})             # mbo not implemented

    def test_negative_prices_exact_integers(self):
        blob = S.pack_record(S.RTYPE_OHLCV_1D, 1,
                             dict(open=5825_000000000, high=5850_000000000,
                                  low=-3000_000000, close=-2750_000000,
                                  volume=9), 1, 1)
        out = S.unpack_record(S.RTYPE_OHLCV_1D, blob)
        self.assertEqual(out["low"], -3_000_000_000)
        self.assertEqual(out["close"], -2_750_000_000)


class TestMetadataCodec(unittest.TestCase):
    def _meta(self) -> DbnMetadata:
        return DbnMetadata(
            schema=S.SCHEMA_OHLCV_1D, start=100, end=200,
            stype_in=S.STYPE_RAW_SYMBOL, stype_out=S.STYPE_INSTRUMENT_ID,
            symbols=["CLZ6", "CLF7"], partial=["CLZ6"], not_found=["XXX"],
            mappings=[SymbolMapping("CL.c.0", [
                MappingInterval(20260101, 20261101, "CLZ6"),
                MappingInterval(20261102, 20261231, "CLF7")])])

    def test_metadata_roundtrip(self):
        blob = encode_metadata(self._meta())
        meta = decode_metadata_from_blob(blob[8:], blob[3])
        self.assertEqual(meta.schema, S.SCHEMA_OHLCV_1D)
        self.assertEqual(meta.stype_in, S.STYPE_RAW_SYMBOL)
        self.assertEqual(meta.symbols, ["CLZ6", "CLF7"])
        self.assertEqual(meta.partial, ["CLZ6"])
        self.assertEqual(meta.not_found, ["XXX"])
        m = meta.mappings[0]
        self.assertEqual(m.raw_symbol, "CL.c.0")
        self.assertEqual([(i.start_date, i.end_date, i.symbol)
                          for i in m.intervals],
                         [(20260101, 20261101, "CLZ6"),
                          (20261102, 20261231, "CLF7")])

    def test_metadata_fixed_layout(self):
        blob = encode_metadata(self._meta())
        self.assertEqual(blob[:3], b"DBN")
        self.assertEqual(blob[3], 3)               # version byte
        self.assertGreaterEqual(len(blob) - 8, S.METADATA_FIXED_LEN)
        self.assertEqual(S.METADATA_FIXED_LEN, 100)
        self.assertEqual(S.SYMBOL_CSTR_LEN, 71)
        self.assertEqual(S.ASSET_CSTR_LEN, 11)
        self.assertEqual(S.METADATA_RESERVED_LEN, 53)

    def test_null_sentinels_roundtrip(self):
        meta = DbnMetadata(schema=None, end=None, limit=None, stype_in=None)
        blob = encode_metadata(meta)
        out = decode_metadata_from_blob(blob[8:], blob[3])
        self.assertIsNone(out.schema)
        self.assertIsNone(out.end)
        self.assertIsNone(out.limit)
        self.assertIsNone(out.stype_in)


class TestDbnFileStream(FixtureBase):
    def test_fixture_dbn_files_decode(self):
        from futbt.dbn.wire import read_dbn
        for name in sorted(self.universe.files):
            if not name.endswith(".dbn"):
                continue
            meta, records = read_dbn(self.path(name))
            self.assertIsNotNone(meta.dataset)
            self.assertGreater(len(records), 0, name)

    def test_ohlcv_1d_metadata_carries_schema_and_stype(self):
        meta, records = read_dbn(self.path(
            "ohlcv-1d.glbx-mdp3.raw_symbol.synthetic.dbn"))
        self.assertEqual(meta.schema, S.SCHEMA_OHLCV_1D)
        self.assertEqual(meta.stype_in, S.STYPE_RAW_SYMBOL)
        self.assertEqual(meta.stype_out, S.STYPE_INSTRUMENT_ID)
        self.assertTrue(all(r.rtype == S.RTYPE_OHLCV_1D for r in records))

    def test_continuous_file_carries_mappings(self):
        meta, records = read_dbn(self.path(
            "ohlcv-1d.glbx-mdp3.continuous.synthetic.dbn"))
        self.assertEqual(meta.stype_in, S.STYPE_CONTINUOUS)
        self.assertEqual(meta.symbols, ["CL.c.0"])
        self.assertEqual(meta.mappings[0].raw_symbol, "CL.c.0")
        ivs = [(i.start_date, i.end_date, i.symbol)
               for i in meta.mappings[0].intervals]
        self.assertIn((20260101, 20261101, "CLZ6"), ivs)
        self.assertIn((20261102, 20261231, "CLF7"), ivs)

    def test_bad_magic_rejected(self):
        with self.assertRaises(S.DbnFormatError):
            decode_dbn_bytes(b"XXX\x03" + b"\x00" * 64)

    def test_newer_version_rejected_fail_closed(self):
        blob = encode_metadata(DbnMetadata())
        with self.assertRaises(S.DbnFormatError):
            decode_dbn_bytes(b"DBN\x09" + blob[4:])

    def test_unknown_record_type_fails_closed_typed(self):
        # craft a valid file whose first record has an unsupported rtype
        # (mbo 0xA0): decode must raise the TYPED error, never skip.
        meta = DbnMetadata(schema=S.SCHEMA_OHLCV_1M)
        rec = bytearray(b"\x00" * 56)
        rec[0] = 14                                  # words
        rec[1] = 0xA0                                # mbo rtype
        with self.assertRaises(S.UnknownRecordTypeError) as cm:
            decode_dbn_bytes(encode_metadata(meta) + bytes(rec))
        self.assertIn("0xa0", str(cm.exception))
        self.assertIn("fail-closed", str(cm.exception))

    def test_truncated_record_rejected(self):
        meta, records = read_dbn(self.path(
            "ohlcv-1m.glbx-mdp3.raw_symbol.synthetic.dbn"))
        import struct
        blob = encode_metadata(meta) + S.pack_record(
            S.RTYPE_OHLCV_1M, 5, dict(open=1, high=2, low=0, close=1, volume=1))
        with self.assertRaises(S.DbnFormatError):
            decode_dbn_bytes(blob[:-4])              # chop 4 bytes off

    def test_fixture_is_deterministic(self):
        import hashlib
        second = build_fixture_dir(f"{self.tmp.name}/_second")
        for name in sorted(self.universe.files):
            h1 = hashlib.sha256(open(self.path(name), "rb").read()).hexdigest()
            h2 = hashlib.sha256(open(f"{self.tmp.name}/_second/{name}",
                                     "rb").read()).hexdigest()
            self.assertEqual(h1, h2, name)
        self.assertEqual(sorted(second.files), sorted(self.universe.files))

    def test_fixture_manifest_declares_synthetic(self):
        import json
        man = json.load(open(self.path("FIXTURE_MANIFEST.json")))
        self.assertTrue(man["synthetic"])
        self.assertIn("SYNTHETIC", man["label"])
        self.assertEqual(man["seed"], 20261002)


class TestCsvJsonShapes(FixtureBase):
    def test_csv_column_order_matches_reference_algorithm(self):
        # trades: ts_recv first, then flattened header (ts_event, rtype,
        # publisher_id, instrument_id), then action, side, depth (encode
        # orders 2,3,4 land right after the header SLOT), then price...
        cols = [c for c, _ in textio.csv_columns(S.RTYPE_MBP_0)]
        self.assertEqual(cols, ["ts_recv", "ts_event", "rtype", "publisher_id",
                                "instrument_id", "action", "side", "depth",
                                "price", "size", "flags", "ts_in_delta",
                                "sequence"])

    def test_ohlcv_column_order(self):
        cols = [c for c, _ in textio.csv_columns(S.RTYPE_OHLCV_1M)]
        self.assertEqual(cols, ["ts_event", "rtype", "publisher_id",
                                "instrument_id", "open", "high", "low",
                                "close", "volume"])

    def test_definition_column_order_prefix(self):
        cols = [c for c, _ in textio.csv_columns(S.RTYPE_INSTRUMENT_DEF)]
        self.assertEqual(cols[:7], ["ts_recv", "ts_event", "rtype",
                                    "publisher_id", "instrument_id",
                                    "raw_symbol", "security_update_action"])
        self.assertEqual(cols[7], "instrument_class")
        self.assertNotIn("_reserved", cols)

    def test_stat_columns_exclude_reserved(self):
        cols = [c for c, _ in textio.csv_columns(S.RTYPE_STATISTICS)]
        self.assertNotIn("_reserved", cols)
        self.assertEqual(cols[:6], ["ts_recv", "ts_event", "rtype",
                                    "publisher_id", "instrument_id",
                                    "ts_ref"])

    def test_pretty_rules_empty_fields_for_sentinels(self):
        self.assertEqual(textio.ts_to_iso(0), "")
        self.assertEqual(textio.ts_to_iso(S.UNDEF_TIMESTAMP), "")
        # reference pretty CSV: UNDEF prices and NUL chars write EMPTY
        self.assertEqual(textio._format_value("p", S.UNDEF_PRICE, "px"), "")
        self.assertEqual(textio._format_value("c", 0, "char"), "")
        self.assertEqual(S.nanos_to_price_str(S.UNDEF_PRICE), "UNDEF_PRICE")

    def test_ts_iso_format(self):
        self.assertEqual(textio.ts_to_iso(1),
                         "1970-01-01T00:00:00.000000001Z")
        self.assertEqual(textio.iso_to_ts("1970-01-01T00:00:00.000000001Z"), 1)
        self.assertEqual(textio.iso_to_ts(""), 0)

    def test_csv_roundtrip_values(self):
        rows = textio.parse_csv(self.path(
            "ohlcv-1m.glbx-mdp3.raw_symbol.synthetic.csv"))
        self.assertTrue(rows)
        for r in rows:
            self.assertIsInstance(r["open"], int)
            self.assertIsInstance(r["ts_event"], int)
            self.assertEqual(r["rtype"], S.RTYPE_OHLCV_1M)

    def test_csv_missing_column_fails_closed(self):
        bad = "ts_recv,ts_event,rtype,publisher_id,instrument_id,price\n" \
              "2026-01-01T00:00:00Z,2026-01-01T00:00:00Z,0,1,2,3\n"
        with self.assertRaises(textio.TextSchemaError):
            textio.parse_csv(bad, rtype=S.RTYPE_MBP_0)

    def test_jsonl_roundtrip(self):
        rows = textio.parse_jsonl(self.path(
            "ohlcv-1d.glbx-mdp3.raw_symbol.synthetic.jsonl"))
        self.assertTrue(rows)
        self.assertEqual(rows[0]["rtype"], S.RTYPE_OHLCV_1D)
        self.assertIsInstance(rows[0]["close"], int)

    def test_jsonl_unknown_rtype_fails_closed(self):
        with self.assertRaises(textio.TextSchemaError):
            textio.parse_jsonl('{"rtype": 200}', rtype=None)


if __name__ == "__main__":
    unittest.main()
