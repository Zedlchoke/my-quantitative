# Engineering note — RESEARCH-PLATFORM-V3 (terminal)

Written by the A1 controller at P9 closeout. Union-at-merge record; the
authoritative artifacts live in
`research/control/research_platform_v3_run/` on
`orca/research-platform-v3-integration`.

## What was built

- **Query plane** (`research/platform_v3/query_plane.py`): DuckDB,
  read-only, explicit-manifest-ID-only, manifest hash verified before any
  query, bound parameters, frozen output schema/order, full result census
  (row count, nulls, clock min/max, result digest). 11-negative matrix
  tested (URL/extension/glob/order-drift/escape... all rejected).
- **Calendar engine** (`calendar_engine.py`): version-pinned
  exchange_calendars session manifests with canonical content digests;
  official cross-check fail-closed; forex/crypto refuse equity-calendar
  routing (tested).
- **Telemetry** (`telemetry.py`): OTel API + local-JSONL SDK at the
  controller boundary only; no-op default; recursive redaction
  (credentials/URL secrets/headers/env maps/S1 paths/outcome fields);
  on/off leaves scientific bytes identical (proven at V3-G4).
- **CADS** (`cads.py`): content-addressed store (sha256 = name = integrity
  proof), atomic journal, verify-on-read, restore; store at
  `.runtime/v3_cads_store` (gitignored), pins recorded in committed gate
  artifacts.
- **Authority registry** (`authority.py`): per-series forward-only state
  machine REGISTERED→INGESTED→VERIFIED→GRANTED|BLOCKED, fail-closed grant
  (PIT evidenced + license + entitlement + channel canary PASS + CADS pins,
  all required).

## Measured results

- Core SHA (P4, detached two-tree × three hash seeds × telemetry on/off,
  ALL_MATCH): `d68af12b348d6109c7893fae15d088ae71eba3f20b33c631bc0ccbec132d87a8`
- Authority: all 8 frozen-set S1–S4 series GRANTED on new measured
  evidence (GA4); ungranted-series refusal proven (GA5); everything
  outside S1–S4 stays BLOCKED_DATA by default.
- Canaries: 9/9 channels PASS (GA3), including keyed eodhd/fred via
  env-loaded owner keys (no key material in any artifact). Note: edgar and
  bis reject generic UAs — the repo-proven V13 contact UA
  `Research my-quantitative@example.com` is required; binance-vision
  klines objects live under interval subdirectories.
- Performance (G6, honest): DuckDB warm filter ~0.139s vs pandas ~0.081s
  on a 200k-row microbench — the plane is NOT a speed play; it buys
  verification and identity. Telemetry overhead within noise.
- Full suite: 1868 passed / 1 skipped (G7). Audit: 39 fresh-process
  checks, zero HIGH/CRITICAL (G8), independence limitation disclosed.

## Terminal verdict (conservative reading, recorded)

`RESEARCH_PLATFORM_V3_PASS_CORE_PARTIAL_ASSET_PILOTS` — asset pilots
V3-G5-C/F/S are NOT_APPLICABLE_NO_ELIGIBLE_ASSETS (MDP-V2 adoption packets
absent), so the top verdict's "bounded shadow proof per eligible asset"
clause cannot be measured and is not claimed, even though the full S1–S4
authority set is GRANTED. When a future cycle produces an adoption packet,
the missing pieces are: one bounded shadow parity pilot per eligible asset
against the already-frozen core SHA.

## Reuse guide for future cycles

1. Check the authority table (GA4 artifact) before touching any series;
   only GRANTED series are consumable via the plane, only by cycles that
   have not yet frozen a data contract (adoption boundary, handbook §30).
2. Consume via `pa4_pa5_authority.consume_via_plane`-shaped path: registry
   verdict check → CADS resolve (verify-on-read) → manifest-verified frozen
   query. Never open data files directly in scored code.
3. If a canary channel fails with 403/404 on a known-good URL, suspect the
   User-Agent first (see GA3 incident) before assuming the channel is dead.
