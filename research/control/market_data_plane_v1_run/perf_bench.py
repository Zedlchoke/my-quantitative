#!/usr/bin/env python
"""MDP-V1 P6 performance characterization (not an HFT claim).

Frozen method (architecture_freeze.json benchmark_method):
- fixture: 200k mixed TRADE/QUOTE events generated deterministically (seed 20260909)
- the measured path is the plane's real one: build+validate every event
  (models.build_event), classify (quality.evaluate), serialize (canonical_json),
  then archive + deterministic replay over the whole stream
- 2 warmups + 7 measured runs; report median/p95 events-per-second and peak RSS
- correctness dominates speed; the gate compares against the frozen baseline
  recorded at first PASS (perf_baseline.json), tolerance 20%
"""
from __future__ import annotations

import hashlib
import json
import os
import resource
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "research"))

from market_data_plane import archive, models, quality, replay  # noqa: E402
from market_data_plane.quality import QualityParams  # noqa: E402

N = 200_000
WARMUPS = 2
RUNS = 7


def build_events():
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


def one_run(tmp: Path) -> float:
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


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="mdp_perf_"))
    try:
        for _ in range(WARMUPS):
            one_run(tmp)
        times = [one_run(tmp) for _ in range(RUNS)]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    eps = [N / t for t in times]
    record = {
        "schema": "mdp_perf_run@1",
        "python": sys.version.split()[0],
        "host_node": os.uname().nodename,
        "fixture_events": N,
        "fixture_fingerprint": hashlib.sha256(f"mdp-perf-{N}-{models.SCHEMA_VERSION}".encode()).hexdigest()[:16],
        "warmups": WARMUPS,
        "runs": RUNS,
        "run_seconds": [round(t, 4) for t in times],
        "median_eps": round(statistics.median(eps), 1),
        "p95_eps": round(sorted(eps)[int(0.95 * (len(eps) - 1))], 1),
        "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "note": "not an HFT claim; no comparison to MDRAP benchmarks",
    }
    print(json.dumps(record, indent=1))
    out = Path(__file__).parent / "perf_run_latest.json"
    out.write_text(json.dumps(record, indent=1) + "\n")
    baseline = Path(__file__).parent / "perf_baseline.json"
    if not baseline.exists():
        record["role"] = "FROZEN_BASELINE (first PASS)"
        baseline.write_text(json.dumps(record, indent=1) + "\n")
        print("baseline frozen")
    else:
        base = json.loads(baseline.read_text())
        ratio = record["median_eps"] / base["median_eps"]
        record["baseline_median_eps"] = base["median_eps"]
        record["ratio_to_baseline"] = round(ratio, 4)
        record["gate_no_unexplained_regression_gt_20pct"] = bool(ratio >= 0.8)
        out.write_text(json.dumps(record, indent=1) + "\n")
        print("gate ratio_to_baseline:", record["ratio_to_baseline"],
              "=> PASS" if ratio >= 0.8 else "=> INVESTIGATE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
