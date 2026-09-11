"""RESEARCH-PLATFORM-V3 shared components.

Four narrowly scoped capabilities (plan sections 0, 2, 5-7, 7A):

- ``query_plane``      deterministic read-only DuckDB queries over explicit
                       MDP manifest lists (capability 2);
- ``calendar_engine``  version-pinned exchange_calendars adapter producing
                       versioned session manifests (capability 3);
- ``telemetry``        OpenTelemetry traces/metrics with a no-op default and
                       a local-JSONL-only exporter (capability 4);
- ``cads``             content-addressed data store (capability 1 / PA);
- ``authority``        per-series authority registry with a fail-closed
                       state machine (capability 1 / PA).

Everything here is engineering infrastructure: zero scored PnL, zero
denominator mutation, no data authority by inheritance.
"""
