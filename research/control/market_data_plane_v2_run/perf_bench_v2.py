#!/usr/bin/env python
"""MDP-V2 performance characterization — HEAVY (extends the V1 P6 method).

Freeze authority: research/control/market_data_plane_v2_run/architecture_freeze_v2.json
(p3_wave_sha 09a223f6ce166e219beb67b25b8151361979ca21), section
"performance_procedure" and finding F4 (portable resource metrics).

Frozen method:

* EVENT path (gate-comparable): the EXACT V1 200k-event mixed TRADE/QUOTE
  synthetic fixture — same generator constants, same build path
  (models.build_event + quality.evaluate + canonical_json + archive +
  deterministic replay) and the same fingerprint discipline
  (``sha256("mdp-perf-{N}-{models.SCHEMA_VERSION}")[:16]``) as
  research/control/market_data_plane_v1_run/perf_bench.py — so the frozen
  V1 TRADE/QUOTE throughput regression ceiling (20 percent, same host class)
  stays comparable.
* BAR path (reported separately, no cross-host comparison): 200k
  ``mdp.market_bar@2`` bars built (bars.build_bar), validated, archived
  (bar_archive.put_bar_records) and read back (bar_archive.load_bar_records)
  per run.
* 2 warmups + 7 measured runs per path; median/p95 events- (bars-) per-second.
* Portable RSS (F4): ``mdp_perf_run@2`` records ``platform`` plus the
  normalized RSS fields from perf_metrics.normalize_rss
  (darwin -> bytes, linux -> KiB, unknown -> null bytes + visible note).
  The misleading V1 field name ``peak_rss_kb`` (which held DARWIN BYTES —
  see perf_v1_unit_erratum.json) is deliberately NOT carried into @2.

WEIGHT: HEAVY — requires the machine-wide heavy lock FREE_PROVEN and
exclusive host access (V2-G7).  NEVER run it under a held lock; when the
lock is held the gate records NOT_RUN_RESOURCE_CONFLICT instead.  This
script is deliberately NOT exercised by the test suite (tests cover only the
perf_metrics math).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "research"))

from market_data_plane import archive, bar_archive, bars, models, perf_metrics, quality, replay  # noqa: E402
from market_data_plane.quality import QualityParams  # noqa: E402

N = 200_000
WARMUPS = 2
RUNS = 7

BAR_INTERVAL_NS = 60_000_000_000  # 1-minute bars
BAR_OPEN_BASE_NS = 1_700_000_000_000_000_000


def build_events():
    """The exact V1 fixture generator (byte-identical discipline)."""
    events = []
    for i in range(N):
        if i % 2 == 0:
            fields = dict(
                schema_version=models.SCHEMA_VERSION, raw_id=f"r{i}", source_id="SRC",
                venue="VEN", instrument_id="INST", asset_class="crypto", event_type="TRADE",
                exchange_time_utc_ns=1_700_000_000_000_000_000 + i,
                receive_time_utc_ns=1_700_000_000_000_000_500 + i,
                available_time_utc_ns=1_700_000_000_000_001_000 + i, sequence_number=i,
                price=f"60000.{i % 100:02d}", quantity=f"{1 + (i % 9) * 0.25:.2f}", side="buy",
                price_precision=2, size_precision=2,
                raw_sha256=hashlib.sha256(f"raw{i}".encode()).hexdigest(),
                manifest_sha256=hashlib.sha256(f"m{i}".encode()).hexdigest(),
                normalizer_version="1",
            )
        else:
            fields = dict(
                schema_version=models.SCHEMA_VERSION, raw_id=f"q{i}", source_id="SRC",
                venue="VEN", instrument_id="INST", asset_class="crypto", event_type="QUOTE",
                exchange_time_utc_ns=1_700_000_000_000_000_000 + i,
                receive_time_utc_ns=1_700_000_000_000_000_500 + i,
                available_time_utc_ns=1_700_000_000_000_001_000 + i, sequence_number=i,
                bid_price=f"60000.{i % 100:02d}", ask_price=f"60001.{i % 100:02d}",
                bid_size="5.00", ask_size="7.00",
                price_precision=2, size_precision=2,
                raw_sha256=hashlib.sha256(f"rawq{i}".encode()).hexdigest(),
                manifest_sha256=hashlib.sha256(f"m{i}".encode()).hexdigest(),
                normalizer_version="1",
            )
        events.append(models.build_event(fields))
    return events


def build_bars():
    """200k canonical 1-minute mdp.market_bar@2 bars (deterministic)."""
    out = []
    for i in range(N):
        open_ns = BAR_OPEN_BASE_NS + i * BAR_INTERVAL_NS
        close_ns = open_ns + BAR_INTERVAL_NS - 1_000_000
        out.append(bars.build_bar(dict(
            source_id="SRC", provider_id="PROV", venue="VEN", instrument_id="INST",
            asset_class="crypto", bar_type="1m", interval_ns=BAR_INTERVAL_NS,
            open_time_utc_ns=open_ns, close_time_utc_ns=close_ns,
            available_time_utc_ns=close_ns,
            open=f"60000.{i % 100:02d}", high=f"60010.{i % 100:02d}",
            low=f"59990.{i % 100:02d}", close=f"60005.{i % 100:02d}",
            volume=f"{100 + (i % 50)}.00", quote_volume=f"{6_000_000 + i}.00",
            trade_count=1_000 + (i % 17), taker_buy_base=f"{50 + (i % 10)}.00",
            taker_buy_quote=f"{3_000_000 + i}.00",
            price_precision=2, size_precision=2,
            adjustment_mode="RAW", quality_status="VALID",
            raw_sha256=hashlib.sha256(f"barraw{i}".encode()).hexdigest(),
            manifest_sha256=hashlib.sha256(f"barmanifest{i}".encode()).hexdigest(),
            normalizer_version="2",
        )))
    return out


def one_event_run(tmp: Path) -> float:
    """V1 TRADE/QUOTE path: build+classify+serialize+archive+replay."""
    shutil.rmtree(tmp, ignore_errors=True)
    t0 = time.perf_counter()
    events = build_events()
    qp = QualityParams(evaluation_time_ns=0, staleness_threshold_ns=10**9,
                       instrument_registry=frozenset({"INST"}))
    for e in events[:1000]:
        quality.evaluate(e, None, qp)
    lines = ("\n".join(models.canonical_json(e) for e in events) + "\n").encode()
    out = archive.write_chunk(tmp, lines)
    manifest = archive.build_manifest(
        out["sha256"], len(lines), N, source_id="SRC", provider_id="PROV", venue="VEN",
        instrument_id="INST", asset_class="crypto", event_class="MIXED",
        request_identity_secrets_removed={"note": "redacted"},
        entitlement_evidence_ref="ent://synthetic/perf", retrieval_start_utc_ns=1,
        retrieval_end_utc_ns=2, parser_version="1", normalizer_version="1",
        sequence_semantics="NONE", ordered_delivery=False, created_utc=1)
    mid = archive.publish_manifest(tmp, manifest).stem
    res = replay.replay(tmp, [mid], predicate={})
    assert res["event_count"] == N, res["event_count"]
    return time.perf_counter() - t0


def one_bar_run(tmp: Path) -> float:
    """BAR path: build+validate+archive a 200k bar stream, then read back."""
    shutil.rmtree(tmp, ignore_errors=True)
    t0 = time.perf_counter()
    stream = build_bars()
    result = bar_archive.put_bar_records(
        tmp, stream, source_id="SRC", provider_id="PROV", venue="VEN",
        instrument_id="INST", asset_class="crypto",
        request_identity_secrets_removed={"note": "redacted"},
        entitlement_evidence_ref="ent://synthetic/perf", retrieval_start_utc_ns=1,
        retrieval_end_utc_ns=2, parser_version="1", normalizer_version="2",
        sequence_semantics="NONE", ordered_delivery=False, created_utc=1)
    assert result["record_count"] == N, result["record_count"]
    readback = bar_archive.load_bar_records(tmp, result["manifest"]["manifest_id"])
    assert len(readback) == N
    assert readback[0]["bar_id"] == stream[0]["bar_id"]
    return time.perf_counter() - t0


def _median_p95(times, count):
    per_second = [count / t for t in times]
    return (round(statistics.median(per_second), 1),
            round(sorted(per_second)[int(0.95 * (len(per_second) - 1))], 1))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="mdp_perf_v2_"))
    try:
        for _ in range(WARMUPS):
            one_event_run(tmp)
        event_times = [one_event_run(tmp) for _ in range(RUNS)]
        for _ in range(WARMUPS):
            one_bar_run(tmp)
        bar_times = [one_bar_run(tmp) for _ in range(RUNS)]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    median_eps, p95_eps = _median_p95(event_times, N)
    median_bps, p95_bps = _median_p95(bar_times, N)

    rss = perf_metrics.peak_rss_now(sys.platform)

    record = {
        "schema": "mdp_perf_run@2",
        "python": sys.version.split()[0],
        "host_node": os.uname().nodename,
        "platform": sys.platform,
        "fixture_events": N,
        "fixture_fingerprint": hashlib.sha256(
            f"mdp-perf-{N}-{models.SCHEMA_VERSION}".encode()).hexdigest()[:16],
        "warmups": WARMUPS,
        "runs": RUNS,
        "run_seconds": [round(t, 4) for t in event_times],
        "median_eps": median_eps,
        "p95_eps": p95_eps,
        "bar_section": {
            "bar_count": N,
            "bar_fingerprint": hashlib.sha256(
                f"mdp-perf-bar-{N}-{bars.SCHEMA_VERSION}".encode()).hexdigest()[:16],
            "warmups": WARMUPS,
            "runs": RUNS,
            "run_seconds": [round(t, 4) for t in bar_times],
            "median_bps": median_bps,
            "p95_bps": p95_bps,
            "note": "bar throughput reported separately; no cross-host comparison",
        },
        # F4 portable RSS fields (the V1 peak_rss_kb name is NOT carried into
        # @2 — it held darwin bytes; perf_v1_unit_erratum.json).
        "peak_rss_raw": rss["peak_rss_raw"],
        "peak_rss_raw_unit": rss["peak_rss_raw_unit"],
        "peak_rss_bytes": rss["peak_rss_bytes"],
        "peak_rss_mib": rss["peak_rss_mib"],
        "note": "not an HFT claim; no comparison to MDRAP benchmarks",
    }

    baseline = (Path(__file__).resolve().parents[1]
                / "market_data_plane_v1_run" / "perf_baseline.json")
    if baseline.exists():
        base = json.loads(baseline.read_text())
        ratio = record["median_eps"] / base["median_eps"]
        record["baseline_median_eps"] = base["median_eps"]
        record["ratio_to_baseline"] = round(ratio, 4)
        record["gate_no_unexplained_regression_gt_20pct"] = bool(ratio >= 0.8)
        print("gate ratio_to_baseline:", record["ratio_to_baseline"],
              "=> PASS" if ratio >= 0.8 else "=> INVESTIGATE")
    else:
        record["baseline_comparison"] = "NOT_AVAILABLE (no V1 baseline on this host)"

    print(json.dumps(record, indent=1))
    out = Path(__file__).parent / "perf_run_v2_latest.json"
    out.write_text(json.dumps(record, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
