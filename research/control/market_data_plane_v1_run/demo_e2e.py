#!/usr/bin/env python
"""MDP-V1 safe local demo: ingest -> manifest -> quality -> replay -> BBO/TCA -> Nautilus.

Runs only on committed synthetic fixtures generated in-memory (no network,
no credentials, no orders, no scored strategy logic). Mirrors P7's operator
proof requirement.
"""
from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "research"))

from market_data_plane import archive, bbo, models, quality, replay, tca  # noqa: E402
from market_data_plane.quality import QualityParams  # noqa: E402


def trade(i, price):
    return models.build_event(dict(
        schema_version=models.SCHEMA_VERSION, raw_id=f"t{i}", source_id="DEMO",
        venue="VEN-A", instrument_id="DEMO-PERP", asset_class="crypto", event_type="TRADE",
        exchange_time_utc_ns=1_700_000_000_000_000_000 + i * 1_000_000_000,
        receive_time_utc_ns=1_700_000_000_000_000_001 + i * 1_000_000_000,
        available_time_utc_ns=1_700_000_000_000_000_002 + i * 1_000_000_000,
        sequence_number=i, price=price, quantity="1.0", side="buy",
        price_precision=2, size_precision=1,
        raw_sha256=hashlib.sha256(f"t{i}".encode()).hexdigest(),
        manifest_sha256=hashlib.sha256(f"tm{i}".encode()).hexdigest(),
        normalizer_version="1"))


def quote(i, bid, ask):
    return models.build_event(dict(
        schema_version=models.SCHEMA_VERSION, raw_id=f"q{i}", source_id="DEMO",
        venue="VEN-A", instrument_id="DEMO-PERP", asset_class="crypto", event_type="QUOTE",
        exchange_time_utc_ns=1_700_000_000_000_000_500 + i * 1_000_000_000,
        receive_time_utc_ns=1_700_000_000_000_000_501 + i * 1_000_000_000,
        available_time_utc_ns=1_700_000_000_000_000_502 + i * 1_000_000_000,
        sequence_number=i, bid_price=bid, ask_price=ask, bid_size="10",
        ask_size="10", price_precision=2, size_precision=0,
        raw_sha256=hashlib.sha256(f"q{i}".encode()).hexdigest(),
        manifest_sha256=hashlib.sha256(f"qm{i}".encode()).hexdigest(),
        normalizer_version="1"))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="mdp_demo_"))
    try:
        events = []
        for i in range(10):
            events.append(trade(i, f"100.{i:02d}"))
            events.append(quote(i, f"100.{i:02d}", f"100.{i + 5:02d}"))
        # classify every event and promote its measured status (construction
        # default is QUARANTINED — set_quality from evaluate() is the only
        # promotion path, per the freeze)
        qp = QualityParams(evaluation_time_ns=1_700_000_010_000_000_000,
                           staleness_threshold_ns=10**15,
                           instrument_registry=frozenset({"DEMO-PERP"}))
        events = [models.set_quality(e, *quality.evaluate(e, None, qp))
                  for e in events]

        # one poisoned event: crossed quote inside the venue -> INVALID
        crossed = dict(quote(99, "101.00", "100.00"))
        events.append(models.set_quality(crossed, "INVALID", ["CROSSED_QUOTE"]))

        print("[1] quality:", [
            (e["event_type"], *quality.evaluate(e, None, QualityParams(
                evaluation_time_ns=e["exchange_time_utc_ns"], staleness_threshold_ns=10**15,
                instrument_registry=frozenset({"DEMO-PERP"}))))
            for e in events if e["raw_id"] in ("t0", "q0", "q99")])

        lines = ("\n".join(models.canonical_json(e) for e in events) + "\n").encode()
        chunk = archive.write_chunk(tmp, lines)
        manifest = archive.build_manifest(
            chunk["sha256"], len(lines), len(events), source_id="DEMO", provider_id="DEMO",
            venue="VEN-A", instrument_id="DEMO-PERP", asset_class="crypto",
            event_class="MIXED", entitlement_evidence_ref="ent://demo/synthetic",
            parser_version="demo@1", normalizer_version="1",
            sequence_semantics="NONE", ordered_delivery=False, created_utc=1)
        mid = archive.publish_manifest(tmp, manifest).stem
        print("[2] archive+manifest:", mid[:16], chunk["sha256"][:16])

        res = replay.replay(tmp, [mid], predicate={})
        print("[3] replay:", res["event_count"], "events, digest", res["stream_digest"][:16])

        book = bbo.VenueBook()
        for e in events:
            if e["event_type"] == "QUOTE" and e["quality_status"] in ("VALID", "SUSPECT"):
                book.apply_quote(e)
        consolidated = book.consolidated_bbo(
            ["VEN-A"], "DEMO-PERP", {"VEN-A"}, now_ns=1_700_000_000_010_000_000,
            staleness_threshold_ns=10**15)
        print("[4] consolidated BBO:", consolidated["bid"], "/",
              consolidated["ask"], "| crossed:", consolidated["crossed"],
              "| ref ccy:", consolidated["reference_currency"])

        fills = [dict(fill_id="f1", side="buy", price="100.02", quantity="1.0",
                      fee="0.10", funding_or_swap="0.00",
                      decision_time_utc_ns=1_700_000_000_000_000_000,
                      fill_time_utc_ns=1_700_000_000_000_100_000)]
        quotes = [e for e in events if e["event_type"] == "QUOTE"
                  and e["quality_status"] == "VALID"]
        report = tca.evaluate_tca(fills, quotes, staleness_threshold_ns=10**15,
                                  submitted_quantity="1.0")
        fill0 = report["fills"][0]
        print("[5] TCA keys:", sorted(k for k in fill0 if "bps" in k or "mid" in k))
        print("[5] TCA fill_ratio:", report["fill_ratio"])

        from market_data_plane import nautilus_bridge
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
        from nautilus_trader.test_kit.providers import TestInstrumentProvider
        from mdp_bridge_fixtures import crypto_trades
        instrument = TestInstrumentProvider.btcusdt_perp_binance()
        tick = nautilus_bridge.to_trade_tick(crypto_trades.events()[0], instrument)
        print("[6] Nautilus:", type(tick).__name__, "price", tick.price,
              "ts_event", tick.ts_event)

        print("DEMO OK — all stages ran on synthetic fixtures only")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
