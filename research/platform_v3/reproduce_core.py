#!/usr/bin/env python
"""P4/P6 evidence runners: detached reproduction + perf characterization.

reproduce_core.py runs INSIDE a detached tree (any absolute path) and
executes the deterministic core fixtures, printing one JSON line:

    {"digest": <sha256 of canonical outputs>, "identifiers": ...}

The A1 driver runs it twice from DIFFERENT cwds with DIFFERENT
PYTHONHASHSEED values plus telemetry on/off and requires ALL_MATCH.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__"
    else "."))

from research.platform_v3.query_plane import (  # noqa: E402
    FrozenQuery, ManifestEntry, OutputColumn, QueryPlane,
)
from research.platform_v3.calendar_engine import (  # noqa: E402
    SessionManifestBuilder, package_pin,
)
from research.platform_v3.telemetry import telemetry_from_env  # noqa: E402
from research.platform_v3.cads import CADS  # noqa: E402


def run_core(tmp_root: str) -> dict:
    """Deterministic core workload: manifest-verified query + session
    manifest + CADS round-trip.  All outputs are canonical."""
    # --- query fixture ------------------------------------------------- #
    csv = "mid,ts,val\n" + "".join(
        f"{i},2026-01-{(i % 28) + 1:02d}T00:00:00Z,{(i * 7) % 101}\n"
        for i in range(1, 101)
    )
    p = os.path.join(tmp_root, "fixture.csv")
    with open(p, "w") as fh:
        fh.write(csv)
    digest = hashlib.sha256(csv.encode()).hexdigest()
    plane = QueryPlane({"m:fixture": ManifestEntry(
        "m:fixture", p, digest)})
    plane.register_views({"m:fixture": "v_fix"})
    frozen = FrozenQuery(
        "core_agg",
        "SELECT mid, ts, val FROM v_fix WHERE val > 50 ORDER BY mid",
        ["mid"],
        [OutputColumn("mid", "BIGINT"), OutputColumn("ts", "TIMESTAMPTZ"),
         OutputColumn("val", "BIGINT")],
        clock_column="ts",
    )
    result = plane.run(frozen, ["m:fixture"])
    plane.close()
    if result.verdict != "SUCCESS":
        raise SystemExit(f"core query not SUCCESS: {result.reason}")

    # --- calendar fixture ----------------------------------------------- #
    builder = SessionManifestBuilder(package_pin())
    manifest = builder.build("XNYS", "stocks", "2026-07-01", "2026-07-10",
                             "America/New_York")

    # --- CADS round-trip ------------------------------------------------ #
    store = CADS(os.path.join(tmp_root, "cads"))
    addr = store.register(b"core-fixture-bytes")
    assert store.resolve(addr) == b"core-fixture-bytes"

    canonical = {
        "query_identity": result.identity,
        "query_digest": result.result_digest,
        "row_count": result.row_count,
        "null_census": result.null_census,
        "clock_min": result.clock_min,
        "calendar_digest": manifest["canonical_content_digest"],
        "calendar_version": manifest["calendar_package"]["version"],
        "calendar_pkg_digest": manifest["calendar_package"]["source_digest"],
        "cads_address": addr,
    }
    return canonical


def main() -> int:
    telemetry_mode = sys.argv[1] if len(sys.argv) > 1 else "off"
    tmp_root = tempfile.mkdtemp(prefix="v3_repro_")
    if telemetry_mode == "jsonl":
        os.environ["V3_TELEMETRY"] = "jsonl"
        tel = telemetry_from_env(os.path.join(tmp_root, "trace.jsonl"),
                                 "f" * 32,
                                 {"cycle_id": "RESEARCH-PLATFORM-V3",
                                  "phase_id": "P4"})
        with tel.span_start("repro_core"):
            canonical = run_core(tmp_root)
        tel.close()
    else:
        canonical = run_core(tmp_root)
    payload = {
        "digest": hashlib.sha256(
            json.dumps(canonical, sort_keys=True).encode()).hexdigest(),
        "canonical": canonical,
        "telemetry": telemetry_mode,
        "pythonhashseed": os.environ.get("PYTHONHASHSEED", ""),
        "cwd": os.getcwd(),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
