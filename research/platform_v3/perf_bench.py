#!/usr/bin/env python
"""P6: honest performance characterization on a bounded synthetic workload.

Measures separately (plan section 8 P6):
- manifest verification (sha256 re-hash of inputs);
- DuckDB cold/warm scan of the verified views;
- legacy pandas scan baseline;
- calendar generation;
- telemetry disabled vs local-JSONL overhead.

No fixed speedup is promised; the artifact reports median/p95, input
size, host and exact versions so future cycles can compare honestly.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

ROWS = 200_000


def build_fixture(tmp_root: str) -> tuple[str, str]:
    import csv
    path = os.path.join(tmp_root, "bench.csv")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["mid", "ts", "val"])
        for i in range(ROWS):
            w.writerow([i, f"2026-01-01T00:{i % 60:02d}:{i % 60:02d}Z",
                        (i * 37) % 1000])
    return path, hashlib.sha256(open(path, "rb").read()).hexdigest()


def timed(fn, repeats: int = 5) -> dict:
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        samples.append(round(time.perf_counter() - t0, 4))
    return {"median_s": statistics.median(samples),
            "p95_s": sorted(samples)[int(0.95 * (len(samples) - 1))],
            "samples": samples}


def main() -> int:
    import duckdb
    import pandas as pd
    from research.platform_v3.query_plane import (FrozenQuery,
                                                  ManifestEntry,
                                                  OutputColumn,
                                                  QueryPlane)
    from research.platform_v3.calendar_engine import (SessionManifestBuilder,
                                                      package_pin)
    from research.platform_v3.telemetry import JsonlTelemetry, NoopTelemetry

    tmp_root = os.path.join("/Users/hoangminhlong/my-quantitative/.runtime",
                            "v3_perf_tmp")
    os.makedirs(tmp_root, exist_ok=True)
    path, sha = build_fixture(tmp_root)
    size_bytes = os.path.getsize(path)

    frozen = FrozenQuery(
        "bench_filter",
        "SELECT mid, val FROM v_bench WHERE val >= 500 ORDER BY mid",
        ["mid"],
        [OutputColumn("mid", "BIGINT"), OutputColumn("val", "BIGINT")],
    )

    plane = QueryPlane({"m:bench": ManifestEntry("m:bench", path, sha)})
    plane.register_views({"m:bench": "v_bench"})

    manifest_verify = timed(lambda: hashlib.sha256(
        open(path, "rb").read()).hexdigest())
    duckdb_cold = timed(lambda: plane.run(frozen, ["m:bench"]), repeats=1)

    def warm():
        r = plane.run(frozen, ["m:bench"])
        assert r.verdict == "SUCCESS"
    duckdb_warm = timed(warm)

    def legacy():
        df = pd.read_csv(path)
        out = df[df["val"] >= 500].sort_values("mid")
        return len(out)
    legacy_scan = timed(legacy)
    legacy_rows = legacy()

    # feature-ready projection: a frozen window-function projection over the
    # same verified view (plan section 8 P6 item 4)
    feat = FrozenQuery(
        "bench_feature_projection",
        "SELECT mid, val, avg(val) OVER (ORDER BY mid ROWS BETWEEN 9 "
        "PRECEDING AND CURRENT ROW) AS roll10 FROM v_bench WHERE val >= 500 "
        "ORDER BY mid",
        ["mid"],
        [OutputColumn("mid", "BIGINT"), OutputColumn("val", "BIGINT"),
         OutputColumn("roll10", "DOUBLE")],
    )
    feature_projection_cold = timed(lambda: plane.run(feat, ["m:bench"]),
                                    repeats=1)

    def feature_warm():
        r = plane.run(feat, ["m:bench"])
        assert r.verdict == "SUCCESS"
    feature_projection_warm = timed(feature_warm)

    pin = package_pin()
    builder = SessionManifestBuilder(pin)
    calendar_gen = timed(lambda: builder.build(
        "XNYS", "stocks", "2020-01-01", "2026-09-01", "America/New_York"),
        repeats=3)

    # telemetry overhead on the warm query path
    tel_jsonl = JsonlTelemetry(os.path.join(tmp_root, "bench_trace.jsonl"),
                               "e" * 32, {"cycle_id": "RESEARCH-PLATFORM-V3"})

    def with_tel():
        with tel_jsonl.span_start("bench_query"):
            warm()
    telemetry_on = timed(with_tel)
    tel_jsonl.close()

    def without_tel():
        noop = NoopTelemetry()
        with noop.span_start("bench_query"):
            warm()
    telemetry_off = timed(without_tel)

    plane.close()

    # peak RSS of this process, macOS reports bytes / Linux reports KiB
    import resource
    ru_maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_note = ("macOS: bytes" if platform.system() == "Darwin"
                else "Linux: KiB (multiply by 1024 for bytes)")

    artifact = {
        "schema": "research_platform_v3_run/p6_perf@1",
        "gate": "V3-G6",
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "host": {"node": platform.node(), "cpu": platform.processor(),
                 "machine": platform.machine(),
                 "python": platform.python_version()},
        "versions": {"duckdb": duckdb.__version__,
                     "pandas": pd.__version__,
                     "exchange_calendars": pin.package_version},
        "workload": {"rows": ROWS, "csv_bytes": size_bytes,
                     "path_sha256": sha,
                     "predicate": "val >= 500 ORDER BY mid"},
        "manifest_verification": manifest_verify,
        "duckdb_cold": duckdb_cold,
        "duckdb_warm": duckdb_warm,
        "legacy_pandas_scan": legacy_scan,
        "feature_projection_cold": feature_projection_cold,
        "feature_projection_warm": feature_projection_warm,
        "calendar_generation_7y": calendar_gen,
        "telemetry_jsonl": telemetry_on,
        "telemetry_noop": telemetry_off,
        "peak_rss": {"ru_maxrss": ru_maxrss, "unit": rss_note},
        "honesty_note": ("no speedup promised; legacy baseline is a plain "
                         "pandas read_csv+filter+sort on the same bytes"),
    }
    print(json.dumps(artifact, indent=1))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       "control/research_platform_v3_run/gates/"
                       "V3-G6_p6_perf.json")
    with open(os.path.normpath(out), "w") as fh:
        json.dump(artifact, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
