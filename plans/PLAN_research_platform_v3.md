# RESEARCH-PLATFORM-V3 — measured data authority, query plane, calendar checks, observability

> Status: `PLANNED_NOT_STARTED`. Amended 2026-09-11 by the Lead under the
> owner's "theo plane" decision (complete the platform so future cycles can
> CONSUME via the plane) — capability 4, the PA phases and the GA gates were
> added before bootstrap; the original three-capability scope stands
> unchanged.
>
> V3 is downstream of `plans/PLAN_market_data_plane_v2.md`. It does not
> supersede or bypass MDP-V2. No V3 implementation begins until MDP-V2 has a
> terminal core verdict and a frozen core SHA. This is engineering-only:
> zero scored PnL, zero denominator mutation, S1 sealed, no provider purchase,
> no credential publication, no push, no main merge and no live deployment.

## 0. Mission

Turn the MDP-V2 foundation into a real data authority — and a faster,
easier-to-operate platform — by adding four narrowly scoped capabilities:

1. **Measured data authority** (the completion layer): a content-addressed
   data store (CADS) plus a per-series authority registry, granting authority
   ONLY on new measured evidence (PIT per §11.7, license/entitlement,
   per-channel canary per P-7) — never by inheritance from past use. MDP-V2's
   `BLOCKED_DATA_AUTHORITY` stands unreopened; this changes it the only
   lawful way, series by series (§7A).
2. DuckDB as a deterministic, read-only query layer over explicitly named MDP
   manifests;
3. `exchange_calendars` as a version-pinned calendar engine and cross-check,
   never as silent legal/data authority; and
4. OpenTelemetry traces/metrics for cycles, lanes, jobs, adapters and gates,
   with a local/no-op default and no scientific payload leakage.

Strongest allowed positive verdict:

```text
RESEARCH_PLATFORM_V3_PASS_AUTHORITY_GRANTED_QUERY_CALENDAR_OBSERVABILITY_READY
```

This verdict means: the full §7A target set carries GRANTED authority rows,
AND the shared components and one bounded shadow proof per eligible asset
pass. Partial-authority variants are first-class successes (§10). No verdict
here means strategy edge, OOS, S1, paper/live or provider authority beyond
the granted series table.

## 1. Preconditions and frozen inputs

A1 must remeasure rather than copying these placeholders:

```text
MDP_V2_TERMINAL_SHA          required
MDP_V2_CORE_SHA              required
CRYPTO_ADOPTION_PACKET_SHA   required or asset marked NOT_ELIGIBLE
FOREX_ADOPTION_PACKET_SHA    required or asset marked NOT_ELIGIBLE
STOCKS_ADOPTION_PACKET_SHA   required or asset marked NOT_ELIGIBLE
DATA_FUSION_SHA              required
NAUTILUS_VERSION             remeasure and pin
GLOBAL_LEDGER_DIGEST         record-only, must remain unchanged
S1                           SEALED_UNTOUCHED
```

Allowed start conditions:

- MDP-V2 full core gates and A7 PASS; and
- no unresolved MDP-V2 HIGH/CRITICAL; and
- every asset used in a real shadow proof has an authorized S0/open-window
  manifest and adoption packet.

If MDP-V2 is only partial on asset adoption, V3 may build/test shared modules
and eligible adapters but cannot claim three-asset readiness.

Additional precondition (amendment 2026-09-11): the PA workstream's LANE
DISPATCH goes through the ZCODE-ORCHESTRATION-V3 controller loop when it has
reached a PASS-class terminal (this plan is its first customer); an explicit
owner waiver, recorded, may substitute. Capabilities 1–3 (P-phases) may run
under the manual Lead dispatch pattern if orchestration is not yet ready.

## 2. Selective open-source decisions

### 2.1 DuckDB — candidate for adoption

Upstream: `https://github.com/duckdb/duckdb` (MIT). Pin exact package version,
wheel hash, Python/OS compatibility and license bytes at intake.

Allowed role:

```text
explicit MDP manifest list -> read-only DuckDB relation/query -> frozen result
```

Forbidden roles:

- data authority;
- implicit file discovery in scored execution;
- mutable source of truth;
- automatic extension download;
- remote URL/network query;
- replacement for MDP archive verification or Data Fusion PIT logic.

Every query identity includes:

```text
duckdb version + query text canonical hash + parameter hash
ordered input manifest IDs + schema version + adapter version
calendar version where applicable + output schema/digest
```

### 2.2 exchange_calendars — candidate for measured adoption

Upstream: `https://github.com/gerrymanoim/exchange_calendars`
(Apache-2.0). Pin exact version/source SHA and supported date range.

Allowed roles:

- generate expected sessions, opens, closes, breaks and early closes;
- cross-check provider bars and the repository's frozen exchange calendar;
- support deterministic schedule construction after a parity gate.

Authority boundary:

- package calendars are maintained software data, not an exchange legal
  announcement;
- a disagreement with an official exchange source is a visible finding;
- V3 never silently picks the result that makes coverage pass;
- historical calendar revisions require a new calendar-manifest version;
- forex sessions and crypto 24/7 clocks do not inherit equity semantics.

### 2.3 OpenTelemetry — candidate for measured adoption

Upstream: `https://github.com/open-telemetry/opentelemetry-python`
(Apache-2.0). Pin the API and SDK separately. Prefer the API in libraries and
inject the SDK/exporter only at the controller boundary.

Allowed signals:

```text
trace: cycle -> phase -> lane -> job -> adapter -> gate
metrics: duration, queue time, row count, quarantine count, memory, retries
```

Forbidden telemetry:

- API keys, cookies, tokens, request headers or environment dumps;
- raw provider rows;
- S1 paths/identities;
- PnL, PF, Sharpe, drawdown or unpublished outcome metrics;
- prompts/transcripts by default;
- network exporter without a later owner decision.

The default exporter is local JSONL under a gitignored runtime directory; the
default library behavior is no-op when no SDK is configured.

### 2.4 Deferred candidates

These projects are evaluated, not automatically installed:

| Project | Activation trigger | Forbidden premature use |
|---|---|---|
| Dagster | >=2 hosts, >=10 recurring jobs, or >=2 evidenced scheduler failures | replacing `researchctl` before parity |
| OpenLineage | stable V3 job/dataset/run identity plus a demonstrated interoperability consumer | second writable authority |
| lakeFS | object storage plus hundreds of GB/multi-host snapshot need | replacing MDP/DVC on local-only data |
| skfolio | >=2 independently validated strategy survivors | optimizing rejected/uncertain strategies |
| Qlib/RD-Agent | MDP-native cycle completed and outcome-blind sandbox contract passed | scorer, selector, auditor or S1 reader |

Each deferred candidate needs a separate POC and owner plan after its trigger.

## 3. Architecture

```text
authorized provider bytes
  -> MDP immutable archive + canonical event/bar
  -> Data Fusion PIT/authority observables
  -> explicit manifest set
  -> DuckDB read-only query plan
  -> asset compatibility projection
  -> existing strategy factory

cycle/phase/lane/job/gate metadata
  -> OpenTelemetry local trace/metrics

stocks timestamps
  -> exchange_calendars expected schedule
  -> official/frozen calendar cross-check
  -> reconciled versioned session manifest
```

There remains one scientific source of truth: committed/frozen manifests and
ledgers. DuckDB databases, telemetry files and calendar caches are derived,
rebuildable and gitignored unless a small evidence digest is explicitly
published.

## 4. Branches, agents and ownership

```text
cycle       RESEARCH-PLATFORM-V3
integration .worktrees/research-platform-v3/integration
branch      orca/research-platform-v3-integration
base        exact clean owner-plan commit
```

| Lane | Owner | Scope |
|---|---|---|
| A2 | query contract | DuckDB wrapper, query identity, sandbox, tests |
| A3 | calendar | calendar adapter, versioned session manifest, tests |
| A4 | observability | OTel abstraction, local exporter, redaction, tests |
| A5 | crypto pilot | explicit-manifest query/parity only |
| A6 | forex pilot | query/PIT/session parity only |
| A8 | stocks pilot | query/calendar/corporate-action parity only |
| A9 | performance/reproduction | independent benchmarks and detached replay |
| A7 | independent audit | audit artifacts only; never repairs |

A1 owns integration, dependency freeze, shared exports, central docs, control
artifacts and terminal publication. Maximum A1 plus three light lanes. Heavy
benchmarks/full suite/reproduction require the machine-wide lock.

## 5. Query-plane contract

The V3 query wrapper must:

1. accept only an explicit ordered manifest-ID list;
2. verify every manifest/chunk through MDP before DuckDB sees it;
3. map manifest IDs to exact local files without glob discovery;
4. reject URLs and extension autoload/install;
5. open derived databases read-only wherever supported;
6. use bound parameters for values;
7. canonicalize and hash SQL plus parameters;
8. enforce an output schema and deterministic order;
9. record row count, null census, min/max clocks and result digest;
10. return `NOT_EVALUABLE`/error on missing evidence, never an empty-success
    substitution.

Mandatory negatives:

- manifest absent/hash drift/path escape;
- unordered query without a frozen order;
- `read_csv_auto`/remote URL/extension/network attempts;
- query changes after freeze;
- duplicate input manifest IDs;
- output row-order drift;
- timestamp/decimal coercion loss;
- newer file present but not named;
- malformed DuckDB cache/database.

## 6. Calendar contract

The calendar component emits a versioned session manifest containing:

```text
calendar name/version/source SHA
requested date range/timezone
session label/open/close/breaks/early-close flags
official cross-check evidence digest
exceptions and disposition
generated-at metadata excluded from scientific identity
canonical content digest
```

Mandatory tests:

- DST boundaries;
- US federal holiday versus exchange holiday differences;
- early close;
- weekend/non-session;
- lunch-break market fixture;
- release-to-next-valid-session mapping;
- package upgrade changes calendar -> digest changes and gate blocks;
- official discrepancy -> fail closed;
- forex and crypto refuse accidental equity-calendar routing.

## 7. Observability contract

Stable identifiers:

```text
trace_id       one controller execution
cycle_id       canonical registry ID
phase_id       plan phase
lane_id        ownership-manifest lane
job_id         scheduler/heavy-lock job
run_id         command attempt
dataset_id     MDP/Data Fusion manifest identity
gate_id        evidence gate
```

Telemetry is append-only operational evidence, not scientific publication.
It must be possible to disable the SDK entirely without changing research
outputs. Tests compare output digests with telemetry on versus off.

Required redaction tests include common credential names, URLs with query
secrets, authorization headers, environment maps, raw payload snippets, S1
paths and outcome fields.

## 7A. Authority and store contract (capability 4 — the completion layer)

### 7A.1 Content-addressed data store (CADS)

```text
layout        data_store/ bytes (gitignored) + committed manifests
address       sha256 of content — an object's name IS its integrity proof
APIs          register / pin / resolve / verify / restore
durability    atomic writes + append-only event journal (governance/atomic_io)
backends      repo store (primary) + ~/staging_backups (read/restore only)
invariant     every inherited-pin consumer (P-13 class) resolves through the
              store, never through worktree paths; a mismatched re-hash is an
              incident + fail-closed series-BLOCKED, never a fix
```

### 7A.2 Authority registry (per-series, fail-closed)

Every row: series_id / source / channel / license+entitlement status /
PIT verdict per §11.7 (PASS_PIT_EVIDENCED | RETROSPECTIVE_ONLY | BLOCKED_DATA)
/ canary probe result per P-7 (per CHANNEL, not vendor) / CADS pins /
granted_at / granted_by. Verdicts per series: `GRANTED` or `BLOCKED` — no
partial credit. Adoption boundary (handbook §30): only cycles that have not
yet frozen a data contract may consume a granted series.

### 7A.3 First-grant target set (frozen; additions need a plan amendment)

```text
S1  Form-4 substrate (345,150 XMLs + 427,096-row stream) + EODHD
    corp-actions — evidence: pinned digests, zero-unexplained
    reconciliation, dead-name canary census (V13)
S2  FRED keyed series pinned by V8/V9 (US CPI legs, DFII10/T10YIE/DGS10
    vintage classes) — license = owner key terms; PIT = measured vintage
    semantics
S3  per-print calendars + announcement ledger GB/CA/AU/NZ (forex) —
    V5 announcement-instant evidence class
S4  Binance daily/H1 panels + OI authority (crypto) — V16/V17 coverage
    censuses + publication-lag evidence for data.binance.vision
```

Any series NOT in S1–S4 stays `BLOCKED_DATA` by default, including every
channel this plan does not canary-probe itself.

### 7A.4 First-consumer proof

A FIXTURE research cycle (no asset plan touched) preregisters
consume-via-plane for one granted series end-to-end: resolve from CADS →
PIT-verified feed → gate evaluation → refusal paths PROVEN for an ungranted
series. The next real asset cycle may then preregister plane consumption for
exactly its granted series and nothing else.

## 8. Execution phases

### P0 — intake

Read this plan and all authorities, remeasure root/worktrees/registry/lock,
verify MDP-V2 pins, classify dirty paths, freeze counters/S1, and publish a
first report before implementation.

### P1 — upstream provenance and dependency POCs

For each candidate: exact source/package pin, license bytes, dependency graph,
offline import, malicious/negative probes, runtime/memory benchmark and removal
proof. No candidate is adopted merely because installation succeeds.

### P2 — contract freeze

Freeze query, calendar, telemetry schemas; tolerances; redaction denylist;
asset-pilot manifests; ownership; commands; negative matrix; performance and
terminal criteria. Commit before lanes branch.

### P3 — parallel core wave

Dispatch A2/A3/A4 from one wave SHA. Integrate query -> calendar -> telemetry,
with targeted and adjacent compatibility tests after every pick.

### P4 — core detached reproduction

Run manifest verification and identical queries in two detached trees and
different cwd/hash seeds. Telemetry on/off must leave scientific bytes equal.
Freeze `RESEARCH_PLATFORM_V3_CORE_SHA` only on `ALL_MATCH`.

### P5 — three asset pilots

Dispatch crypto/forex/stocks pilots from the same core SHA. Each uses only its
MDP-V2 adoption packet and bounded authorized S0/open-window manifest. Run
query/calendar/schedule parity without PnL or denominator mutation.

### P6 — performance characterization

Measure separately:

- manifest verification;
- legacy scan;
- DuckDB cold/warm scan;
- feature-ready projection;
- calendar generation;
- telemetry disabled/local JSONL;
- peak RSS normalized by MDP-V2 perf schema.

No fixed speedup is promised. Report median/p95, input size, host and exact
versions. A candidate that makes end-to-end representative workload >20%
slower without a measured correctness benefit is rejected or kept optional.

### P7 — full battery

Under `FREE_PROVEN` heavy lock: targeted suites, three asset compatibility
suites, protocol/governance, compileall, full `pytest tests/ -q`, dependency
check, secret/network scan, diff-check and clean trees.

### P8 — A7 audit

A7 independently verifies provenance, isolation, deterministic queries,
calendar authority boundaries, telemetry redaction/noninterference, three
asset parity, performance claims, S1/counters, full suite and active-cycle
noninterference. Zero unresolved HIGH/CRITICAL is required.

### PA0 — authority kill-test (before any PA build; may interleave with P0)

Re-verify the §0 frozen inputs' substrates from disk + backup (SHA256SUMS
14/14; Form-4 digest 78c4fb1a-family). If the substrate cannot re-verify:
terminal `RESEARCH_PLATFORM_V3_BLOCKED_SUBSTRATE_VERIFY` — cheap and final,
capabilities 1-3 may still proceed as a partial close.

### PA1 — CADS + authority-row contract freeze

Schemas, state machine REGISTERED→INGESTED→VERIFIED→GRANTED|BLOCKED (no
backward transitions; retries are new attempt records), event formats.

### PA2 — CADS implementation + tests

Idempotent ingest, concurrent register, corruption detection,
restore-from-backup, malformed state = CONTROL_STATE_DRIFT.

### PA3 — migration of S1–S4 into the store (heavy lock, resumable)

Full re-hash vs every existing pin under the machine-wide lock; every
mismatch is an incident and that series stays BLOCKED.

### PA4 — authority evidence + per-channel canary re-probes

PIT/license rows per series; the canary probes RUN HERE (EODHD alive+dead,
EDGAR channel, Binance vision, BIS/ECB/ONS/StatCan/ABS official pages) —
network jobs, resumable, etiquette-bound (P-7).

### PA5 — first-consumer canary (§7A.4) + authority table publication

### P9 — terminal closeout

Synchronize state, heartbeat, event log, worktree manifest, terminal report,
registry/projection and Wayfinder engineering note. Run terminal consistency
gate. Workers zero; no push/merge without owner authority.

## 9. Gates

| Gate | Requirement |
|---|---|
| V3-G0 | clean intake and valid MDP-V2 pins |
| V3-G1 | upstream provenance/licenses/dependency POCs |
| V3-G2 | query/calendar/telemetry freeze complete |
| V3-G3 | core targeted/negative tests PASS |
| V3-G4 | detached reproduction ALL_MATCH |
| V3-G5-C | crypto bounded shadow parity PASS |
| V3-G5-F | forex bounded shadow parity PASS |
| V3-G5-S | stocks bounded shadow parity PASS |
| V3-G6 | honest performance characterization |
| V3-G7 | full suite and compatibility PASS |
| V3-G8 | A7 zero unresolved HIGH/CRITICAL |
| V3-G9 | terminal metadata/counters/S1/workers reconcile |
| V3-GA0 | substrate re-verify kill-test adjudicated (PA0) |
| V3-GA1 | CADS + authority schemas frozen, transition tests PASS |
| V3-GA2 | S1–S4 migrated, every pin re-hashed exact |
| V3-GA3 | per-channel canary re-probes recorded (P-7 class) |
| V3-GA4 | authority table published: each S1–S4 series GRANTED or BLOCKED with reason |
| V3-GA5 | first-consumer fixture canary PASS incl. ungranted-series refusal |

## 10. Terminal verdicts

- `RESEARCH_PLATFORM_V3_PASS_AUTHORITY_GRANTED_QUERY_CALENDAR_OBSERVABILITY_READY`
- `RESEARCH_PLATFORM_V3_PASS_PARTIAL_AUTHORITY_QUERY_CALENDAR_OBSERVABILITY_READY`
  (subset of S1–S4 granted; every non-granted series carries its own BLOCKED
  reason — a first-class success with disclosure)
- `RESEARCH_PLATFORM_V3_PASS_THREE_ASSET_QUERY_CALENDAR_OBSERVABILITY_READY`
  (capabilities 1–3 only — PA work BLOCKED below substrate/orchestration)
- `RESEARCH_PLATFORM_V3_PASS_CORE_PARTIAL_ASSET_PILOTS`
- `RESEARCH_PLATFORM_V3_BLOCKED_MDP_V2_PRECONDITION`
- `RESEARCH_PLATFORM_V3_BLOCKED_DATA_AUTHORITY`
- `RESEARCH_PLATFORM_V3_BLOCKED_SUBSTRATE_VERIFY`
- `RESEARCH_PLATFORM_V3_BLOCKED_RESOURCE_CONFLICT`
- `RESEARCH_PLATFORM_V3_FAIL_STORE_INTEGRITY`
- `RESEARCH_PLATFORM_V3_FAIL_QUERY_INTEGRITY`
- `RESEARCH_PLATFORM_V3_FAIL_CALENDAR_AUTHORITY`
- `RESEARCH_PLATFORM_V3_FAIL_TELEMETRY_NONINTERFERENCE`
- `RESEARCH_PLATFORM_V3_FAIL_COMPATIBILITY`
- `RESEARCH_PLATFORM_V3_INCOMPLETE_NOT_PROMOTABLE`

## 11. Definition of done and expected effect

V3 is done only with explicit terminal evidence. A full positive result gives:

- deterministic SQL over explicit frozen manifests;
- less memory-heavy filtering and feature preparation;
- versioned stock-session checks;
- traceable cycle/lane/job/gate timings;
- three asset shadow proofs;
- no change to scientific output when telemetry is enabled;
- no silent authority or file discovery.

Planning target, not a predeclared PASS:

```text
research engineering quality   about 8.8 -> 9.1-9.3 / 10
idea-to-terminal wall time      measure; expected 15-35% reduction after warmup
manual diagnosis time           measure; expected 30-60% reduction
scored kernel speed             no promised improvement
```

## 12. Fresh-session dispatch

```text
You are A1 Controller for RESEARCH-PLATFORM-V3. Read
plans/PLAN_research_platform_v3.md IN FULL plus CLAUDE.md,
HOW_TO_BE_A_LEAD_ENGINEER.md, current registry/Wayfinder and the complete
MDP-V2 terminal/adoption packets. Remeasure everything and produce P0/PA0
first reports before implementation: PA0 is the substrate re-verify
kill-test (disk + ~/staging_backups SHA256SUMS; Form-4 digest 78c4fb1a
family) — a failed re-verify is the cheap BLOCKED_SUBSTRATE_VERIFY terminal.
Then run BOTH workstreams to the strongest honest terminal verdict:
capabilities 1-3 (P-phases) and capability 4 (PA-phases: CADS store,
per-series authority registry with §11.7 PIT verdicts + P-7 per-channel
canary re-probes, S1-S4 migration under the heavy lock, first-consumer
fixture canary with ungranted-series refusal proof). Use isolated lanes and
exact wave SHAs; PA lane dispatch goes through the orchestration-v3
controller loop when its PASS-class terminal exists (else recorded owner
waiver). Do not bypass an MDP-V2 precondition, data authority, S1,
active-cycle boundary or heavy lock. Authority is granted only by new
measurement, never by inheritance from past use. No scored PnL, denominator
mutation, credentials, provider purchase, network exporter, push, main merge
or destructive cleanup is authorized.
```
