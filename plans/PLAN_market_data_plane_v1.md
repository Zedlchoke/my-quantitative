# MARKET-DATA-PLANE-V1 — selective MDRAP adaptation on the hardened research factory

Status: `PLANNED_NOT_STARTED`

This is the sole fresh-context execution authority for MARKET-DATA-PLANE-V1
(`MDP-V1`). It defines one logical A1 controller session and one continuous
run from intake to an honest terminal verdict. Context compaction does not
start a new session: A1 reloads this file, the run contract, state, event log,
and frozen hashes, then continues from the last committed checkpoint.

This plan is engineering-only. It authorizes no scored PnL, no S1 access, no
paper/testnet/live order, no broker connection, no provider signup or purchase,
no credential handling, no push, and no merge to `main`.

## 0. Owner dispatch and non-authorities

Execution begins only after this file is committed and the owner sends:

```text
GO MARKET DATA PLANE V1 ENGINEERING
```

That phrase authorizes the engineering work in this plan only. It is not a
scored-execution GO and cannot be reused by an asset cycle.

Historical SHV1, Data Fusion, Crypto, Stocks, and Forex plans and artifacts
remain append-only evidence. MDP-V1 may read them and run compatibility tests;
it may not normalize, repair, or reinterpret their scientific outcomes.

One session and one continuous run mean:

- one top-level A1 owns the cycle from intake through closeout;
- A1 may use flat child lanes, but a child may not create grandchildren;
- A1 continues automatically after successful checkpoints;
- A1 does not pause merely to ask whether it should run the next plan phase;
- a real hard stop closes the run honestly rather than being bypassed;
- no shell busy-loop or repeated blind retry is permitted;
- resource conflicts are journaled and light work continues first;
- if a required heavy gate remains unavailable after all light phases, the run
  ends `BLOCKED_RESOURCE_CONFLICT` with resumable evidence.

## 1. Mission

Build a small, research-grade market-data plane that sits below the existing
strategy factory and above raw provider payloads:

```text
provider payloads
  -> immutable raw chunks + manifests
  -> canonical market events + quality reasons
  -> quarantine or accepted stream
  -> deterministic replay
  -> BBO/depth/TCA research views
  -> strict NautilusTrader bridge
  -> existing asset research factories
```

The goal is not to import a second trading platform. The goal is to adapt the
useful data-engineering ideas from MDRAP while keeping the repository's current
governance, Data Fusion semantics, NautilusTrader execution model, scientific
gates, and asset-specific data authorities.

MDP-V1 must make bad data observable, replayable, and fail-closed. It does not
make a provider authoritative and does not make a strategy profitable.

## 2. Measured planning snapshot — remeasure at dispatch

Planning audit performed 2026-09-09 in
`/Users/hoangminhlong/my-quantitative`:

- owner checkout: `main` at
  `f325ef903fb56e35f11ca044ca8c193c6811b647`;
- owner tree: only `.zcode/` untracked; it is owner space and must remain
  untouched and uncommitted;
- SHV1 merged to main and its frozen closeout reported
  `SYSTEM_HARDENING_V1_PASS` with A7 audit commit `8b2a5ca`;
- current SHV1 targeted suite:
  `2 failed, 44 passed`;
- current canonical registry is operationally stale: it lacks Stocks V13 and
  planned Forex V9, and its recorded V17/V8 HEADs differ from measured branch
  HEADs;
- `researchctl cycle doctor` reports `ROUTER_GAP`, `HEAD_MISMATCH`, and a stale
  heartbeat;
- `researchctl job list` returns an empty list while the machine-wide heavy
  lock registry proves a live `STOCKS-FREE-V13/P0D_BULK_INGEST` process;
- full-suite verification was not run because that live V13 heavy worker owns
  the machine-wide slot. This is `NOT_RUN_RESOURCE_CONFLICT`, not PASS or FAIL;
- audited Data Fusion implementation commit:
  `c6a0576ef98dd4392e90805c8ba33821da62eabc`;
- Data Fusion freeze commit: `a276421` on
  `orca/data-fusion-v1-integration`; the core provides semantics and evidence
  structures but authorizes zero sources for scored research;
- NautilusTrader dependency: `nautilus_trader==1.230.0`;
- MDRAP upstream inspected at
  `7bc831ccde5b3d97dd784aeeb51e2d17982771c3` under the MIT license.

Every item is a planning snapshot, not bootstrap truth. A1 reports drift and
never silently changes the measured history to match this section.

## 3. Mandatory SHV1 post-adoption closure

### 3.1 Audit conclusion

SHV1 is sound at its frozen closeout, but it is not fully adopted in today's
operational paths. Do not rebuild SHV1 and do not change its historical
verdict. MDP-V1 starts with a bounded `SHV1_POST_ADOPTION_CLOSURE` phase.

The following are real open defects, not optional cleanup:

1. `tests/test_cycle_registry.py` asserts transient cycle names/lifecycles
   instead of schema invariants, so legitimate lifecycle progress breaks the
   governance suite.
2. `plans/CYCLE_REGISTRY.json` does not represent the current live/planned
   cycle set and cannot stay current through a documented atomic workflow.
3. `plans/ACTIVE_CYCLES.json` remains a stale second router surface. Its status
   as generated projection versus deprecated compatibility file is not fully
   enforced.
4. Scheduler admission/journal records are not connected to actual
   machine-wide heavy-lock ownership. An operator can see a live lock while
   `researchctl job list` claims no job exists.
5. Lock inspection reports `HELD or unknown` even when PID and process-start
   token can prove an exact live holder.

### 3.2 M0 required fixes

A1 assigns a governance lane before any market-data implementation. It must:

- replace transient-state assertions with invariant tests: schema validity,
  exact resolution, terminal absorption, terminal GO death, active/closed
  disjointness, unique cycle IDs, and projection equality;
- provide an explicit atomic registry reconciliation command with compare-and-
  swap, append-only event, dry-run diff, and no legacy-state rewrite;
- support registering a new planned cycle and updating an existing cycle's
  measured HEAD/lifecycle without hand-editing JSON;
- define `ACTIVE_CYCLES.json` as a deterministic projection of canonical
  non-terminal registry records, generated only by the registry writer;
- make doctor compare projection to non-terminal canonical records rather than
  treating every historical lookup row as an active-cycle requirement;
- connect heavy-lock acquire/heartbeat/release observations to the scheduler
  journal, or expose a single reconciled job view that labels source and proves
  the live process token. Silent divergence is forbidden;
- make `locks inspect` return exactly `HELD_PROVEN`, `FREE_PROVEN`, or
  `CONTROL_STATE_DRIFT`, with evidence; ambiguous state never becomes FREE;
- retain backward compatibility for existing callers of `heavy_lock.acquire`;
- add crash, malformed-row, PID-reuse, concurrent-writer, stale-registry, and
  projection-drift tests;
- never kill or modify the currently running asset worker. M0 code and light
  tests may proceed while it runs; the full suite waits for the slot to be
  genuinely free.

Gate `M0_SHV1_POST_ADOPTION_PASS` requires:

- targeted governance suite exit 0;
- `researchctl cycle doctor --json` contains no unexplained HIGH findings;
- the registry includes the current highest-version cycles or explicitly
  records a current cycle as `PLANNED_NOT_STARTED`;
- active projection byte-equals a regeneration from the canonical registry;
- a hermetic real-lock integration test makes `job list` show the holder and
  then its terminal release;
- current live lock inspection truthfully identifies the V13 holder if it is
  still alive;
- tree cleanliness differs from intake only by MDP-V1-owned files.

Failure closes `MARKET_DATA_PLANE_V1_BLOCKED_SHV1_POST_ADOPTION`. No MDRAP or
Data Fusion code is integrated after an M0 failure.

## 4. Selective MDRAP adoption boundary

### 4.1 Exact upstream pin

The intake candidate is:

```text
repository  https://github.com/Aryan-20-04/mdrap
commit      7bc831ccde5b3d97dd784aeeb51e2d17982771c3
license     MIT
```

A1 clones it read-only into a disposable staging directory outside tracked
source, checks out that exact commit, hashes the license and every inspected
source file, and records the result in `upstream_manifest.json`. Upstream HEAD
movement is irrelevant after the pin.

Never execute upstream setup scripts, load its DLL/fast path, use demo keys, or
contact its live endpoints. Do not add MDRAP as a runtime dependency. Full
upstream test success must not be claimed: the planning audit found missing
optional dependencies and targeted failures.

### 4.2 Ideas allowed for adaptation

- canonical raw/canonical event separation;
- explicit quality status and reason codes;
- quarantine with lineage;
- deterministic archive and replay;
- venue BBO and consolidated BBO;
- optional order-book depth views;
- research TCA metrics;
- observable watchdog/failover states;
- terminal/operator presentation concepts.

### 4.3 Components forbidden from import

- strategy SDK and paper executor;
- broker/live execution adapters;
- shared-memory, SBE, multicast, C fast path, or HFT benchmark claims;
- Excel export;
- MDRAP security/RBAC defaults;
- hard-coded credentials, demo keys, or secrets;
- any component that competes with NautilusTrader's execution model;
- any automatic provider fallback that changes the scientific information set.

Prefer a clean implementation against this plan's frozen contracts. If code is
copied or materially derived, retain MIT attribution in file headers and the
third-party notice. Provenance is mandatory even when the algorithm is small.

## 5. Architecture and ownership

### 5.1 Branches and worktrees

```text
.worktrees/market-data-plane-v1/
  integration/       orca/market-data-plane-v1-integration
  m0-governance/      orca/market-data-plane-v1-m0-governance
  a2-schema-quality/  orca/market-data-plane-v1-a2-schema-quality
  a3-archive-replay/  orca/market-data-plane-v1-a3-archive-replay
  a4-bbo-tca/         orca/market-data-plane-v1-a4-bbo-tca
  a8-nautilus/        orca/market-data-plane-v1-a8-nautilus
  a7-audit/           orca/market-data-plane-v1-a7-audit
```

Before every `git worktree add`, print absolute `pwd`, root HEAD, branch
occupancy, ancestry, and porcelain. One frozen wave SHA feeds every
implementation lane. A1 alone cherry-picks in the frozen order. Lanes never
merge, rebase, amend, push, or touch `main`.

Use no more than A1 plus three child agents at once. Reuse the slots:

1. M0 governance lane alone for control-plane ownership;
2. A2, A3, and A4 in parallel after architecture freeze;
3. A8 after those three integrate;
4. A7 fresh-context audit last.

Children may not spawn children. A7 writes audit artifacts only and never
repairs an objection.

### 5.2 File ownership

- M0: `research/governance/**`, `research/researchctl.py`, corresponding
  governance tests, registry/projection migration tools;
- A2: `research/market_data_plane/models.py`, `quality.py`, `reason_codes.py`,
  schema/quality tests;
- A3: `archive.py`, `manifest.py`, `replay.py`, `quarantine.py`, archive tests;
- A4: `bbo.py`, `depth.py`, `tca.py`, market-view tests;
- A8: `nautilus_bridge.py`, adapter fixtures, integration tests, operator docs;
- A1: run-control artifacts, contract freeze, Data Fusion adoption glue,
  integration-only corrections, terminal report;
- A7: `research/audits/market_data_plane_v1/**` only.

No two live lanes own the same file. Shared `__init__.py` edits belong to A1
after picks.

## 6. Canonical contracts

### 6.1 Data Fusion dependency

Adopt the exact audited Data Fusion core commit
`c6a0576ef98dd4392e90805c8ba33821da62eabc`; verify the commit, file hashes,
tests, and ancestry before use. Do not copy an arbitrary later branch tip.

MDP-V1 must version and fix these two recorded low-risk Data Fusion issues:

- a date-only validity end may not use `23:59:59` and leave a sub-second gap;
- equal `available_time`/vintage with differing content may not silently choose
  by later retrieval timestamp. It must fail closed or use a preregistered
  authoritative revision key.

Data Fusion remains the semantic evidence layer for availability, validity,
license, source, and transformation lineage. MDP-V1 adds event-stream and
microstructure semantics; it must not create a competing `NormalizedRecord`.

### 6.2 Raw chunk manifest

Each raw chunk manifest contains at least:

- schema version and immutable manifest ID;
- source/provider ID, venue, instrument, asset class, event class;
- request identity with secrets removed;
- entitlement/license evidence reference and allowed-use classification;
- retrieval start/end UTC nanoseconds;
- payload byte length, record count, SHA-256, media/encoding type;
- minimum/maximum exchange, receive, and available timestamps;
- parser and normalizer versions;
- previous/next chunk linkage where available;
- completeness status and explicit gap reasons.

Raw provider bytes and credentials are gitignored. Git stores only safe
manifests, fixtures, hashes, contracts, and evidence.

### 6.3 Canonical market event

The frozen event envelope includes:

```text
schema_version, event_id, raw_id, source_id, venue, instrument_id,
asset_class, event_type, exchange_time_utc_ns, receive_time_utc_ns,
available_time_utc_ns, sequence_number, price, quantity, side,
bid_price, ask_price, bid_size, ask_size, currency, price_precision,
size_precision, quality_status, reason_codes, raw_sha256,
manifest_sha256, normalizer_version
```

Rules:

- times are integer UTC nanoseconds; naive/local timestamps are rejected;
- price and quantity use exact decimal/fixed-point representation, never
  binary float in persisted canonical evidence;
- `event_id` is deterministic from canonical identity fields;
- absent fields are explicit nulls allowed only for compatible event types;
- source sequence resets require an evidenced session/reset marker;
- exchange, receive, and availability time are not aliases;
- no event is marked valid merely because parsing succeeded.

### 6.4 Quality and quarantine

Statuses are `VALID`, `SUSPECT`, `INVALID`, and `QUARANTINED`. Reason codes are
versioned and include malformed shape, precision loss, duplicate, sequence gap,
out-of-order, impossible time order, stale quote, crossed quote, negative
price/size, source reset, unknown instrument, manifest mismatch, and anomaly.

Quality rules are source/instrument/event-class aware:

- a sequence jump is not called missing data unless the source guarantees
  contiguous sequence semantics;
- cross-venue crossed prices are not treated like a crossed quote inside one
  venue;
- statistical anomalies are diagnostic by default, not silent deletion;
- every rejection or quarantine retains a raw reference and reason;
- corrupted replay records fail or quarantine visibly; they are never skipped
  with `except Exception: pass`.

## 7. Archive, replay, and views

### 7.1 Immutable archive

Write content-addressed chunks using sibling temp file, flush, `fsync`, atomic
rename, post-write hash/read verification, then manifest publication. An
existing content hash is read-only. Appending to a supposedly immutable JSONL
file is forbidden.

Crash tests must cover interruption before flush, before rename, after data
rename but before manifest publication, truncated payload, wrong byte length,
wrong count, and wrong SHA. Orphans are diagnosed and quarantined; never guessed
complete.

### 7.2 Deterministic replay

Freeze a total replay order using explicit fields, including a final stable
event ID tie-break. Replay of the same manifest set must emit byte-identical
canonical streams and identical aggregate digests on a second process and
detached worktree.

Replay filters record their exact input manifest set and predicate. A replay
cannot silently discover newer files. Clock speed affects waiting only, never
event order or content.

### 7.3 BBO and depth

- compute venue-local BBO first;
- consolidated BBO includes only identity-compatible, non-stale, permitted
  venues and records the contributing quote IDs;
- staleness threshold is an input contract, not a hidden constant;
- L1 is required; L2/depth is optional and reports `NOT_EVALUABLE` when absent;
- never synthesize order-book depth from OHLCV bars;
- depth updates require snapshot/delta and sequence semantics to be proven per
  source.

### 7.4 Research TCA

Provide hand-verifiable calculations for arrival mid, decision-to-fill
slippage, effective spread, realized spread at frozen horizons, fill ratio,
fees, funding/swap, and market impact proxy. Fees, funding, and price slippage
remain separate columns before any total-cost view.

TCA accepts fills/evidence as input but does not place orders. Missing quote,
clock, side, currency conversion, or fee evidence returns `NOT_EVALUABLE`; it
does not substitute zero.

## 8. NautilusTrader bridge

The bridge targets exactly `nautilus_trader==1.230.0` and maps canonical events
to existing Nautilus types such as `QuoteTick`, `TradeTick`, and `Bar` where the
mapping is lossless and semantically valid.

Required rules:

- instrument metadata and precisions are mandatory;
- `exchange_time_utc_ns` and `available_time_utc_ns` map explicitly to event and
  initialization/receipt time semantics; no implicit now-time;
- Decimal/fixed-point values round-trip without precision drift;
- invalid/suspect events cannot enter a strategy stream unless an explicit
  diagnostic-only policy permits them;
- OHLCV bars cannot become fabricated quotes or depth;
- adapter round-trip and no-lookahead mutations have golden fixtures;
- no strategy, risk engine, portfolio, broker, or execution code is introduced.

Compatibility fixtures cover one provider-neutral example for crypto trades,
forex bid/ask, and stocks trades/quotes. Fixtures prove code semantics only;
they do not confer data authority on a real source.

## 9. Execution phases — one continuous run

### P0 — First report and safe bootstrap

Read this plan in full, then `CLAUDE.md`, `RULES.md`, `NOTES.md`,
`research/wayfinder/MAP.md`, and the relevant handbook sections. Report:

```text
measured UTC / absolute cwd / branch / full HEAD / origin relation
porcelain and owner-owned dirty files
live highest-version asset plans and worktrees
active processes + machine-wide lock holder/token
SHV1 targeted gate exact result
canonical registry/projection/doctor/job-list state
Data Fusion commit/hash availability
MDRAP exact pin/license availability
workers and resource cap
GO/NO_GO for M0
```

Create `research/control/market_data_plane_v1_run/` with `run_contract.json`,
`state.json`, `heartbeat.json`, `event_log.jsonl`, and
`worktree_manifest.json`. Events are append-only.

### M0 — SHV1 post-adoption closure

Perform Section 3 in its own lane, integrate, run targeted gates, and publish
`gates/M0_SHV1_POST_ADOPTION.json`. Do not touch asset scientific artifacts or
interrupt the live holder.

### P1 — Upstream and Data Fusion intake

- pin and hash MDRAP source/license without executing it;
- inventory allowed/forbidden components and provenance obligations;
- verify Data Fusion exact commit and its frozen audit;
- write `upstream_manifest.json`, `data_fusion_pin.json`, and
  `third_party_decision.md`;
- reject any secret/default-key/example credential during recursive scan.

### P2 — Contract freeze

Freeze schemas, quality codes, replay order, exact arithmetic, archive protocol,
TCA definitions, Nautilus mapping, ownership, tests, benchmark method, and
integration order in `architecture_freeze.json`. Hash it. No lane starts from
an unfrozen contract.

### P3 — Parallel implementation wave

Dispatch A2 schema/quality, A3 archive/replay/quarantine, and A4 BBO/depth/TCA
from the exact wave SHA. Each returns one clean focused commit, test commands,
counts, limitations, and tree status. A1 verifies allowed paths and cherry-picks
in order A2 -> A3 -> A4, running targeted tests after every pick.

### P4 — Data Fusion and Nautilus integration

A1 adopts the pinned Data Fusion core and versioned low-risk corrections. A8
then implements the strict Nautilus bridge and cross-asset fixtures from the
new integration SHA. Integrate A8 only after all P3 contracts are green.

### P5 — Negative, compatibility, and replay gates

Run:

- schema validation and exact-arithmetic goldens;
- property-like fixed-seed event permutations;
- malformed/truncated/hash-drift archive negatives;
- crash-boundary atomicity tests;
- duplicate/gap/reset/out-of-order quality tests;
- deterministic replay twice plus detached-tree reproduction;
- BBO staleness/crossed/venue isolation tests;
- depth `NOT_EVALUABLE` and no-bar-synthesis tests;
- hand-computed TCA fixtures and missing-evidence failures;
- Nautilus round-trip/no-lookahead/precision tests;
- existing Data Fusion, governance, protocol, and asset compatibility suites;
- recursive secret and forbidden-component scan;
- `compileall` and `git diff --check`.

Full pytest runs alone only when the machine-wide lock is proven free. If an
asset worker still owns it, record `NOT_RUN_RESOURCE_CONFLICT`, finish all
light gates, and enqueue the full suite through the reconciled scheduler. Never
contend with or terminate the asset worker.

### P6 — Performance characterization

This is not an HFT claim. Freeze host, Python version, fixture hash, warmup,
run count, and measurement command. Report median and p95 throughput/latency,
peak memory, and variance. Correctness gates dominate speed.

The acceptance gate is no unexplained regression greater than 20% against the
frozen local pure-Python baseline on the same host and fixture. Do not compare
to MDRAP's synthetic benchmark as if hardware/workload were equivalent. Do not
publish the fastest single run.

### P7 — Documentation and operator proof

Write:

- `docs/MARKET_DATA_PLANE.md` architecture and examples;
- `docs/THIRD_PARTY_NOTICES.md` MDRAP pin/license/provenance;
- provider-adapter checklist;
- archive recovery and quarantine runbook;
- asset adoption checklist explaining that each future cycle must separately
  authorize data and freeze semantics.

Run a safe local demo only on committed synthetic fixtures: ingest -> manifest
-> quality -> replay -> BBO/TCA -> Nautilus conversion. It must not use network,
credentials, real orders, or scored strategy logic.

### P8 — Independent A7 audit

Create A7 from the frozen integration SHA with fresh context. Supply the plan,
freeze hashes, manifests, commits, and gate commands, but no desired verdict.
A7 must independently test:

- SHV1 M0 operational closure;
- provenance/license accuracy;
- no competing strategy/execution stack;
- exact arithmetic and clock semantics;
- archive immutability and corruption visibility;
- deterministic replay from a detached tree;
- quality/quarantine non-silent behavior;
- BBO/depth/TCA correctness;
- Nautilus compatibility;
- no credentials/raw licensed payloads in git;
- full-suite result and resource precondition;
- tree/worktree/worker state.

A7 records objections as LOW/MEDIUM/HIGH/CRITICAL and never repairs them. Any
HIGH or CRITICAL objection blocks PASS. A1 may open one versioned remediation
wave, after which A7 reruns the affected gates from a new frozen SHA.

### P9 — Terminal closeout

Publish `terminal_report.json`, final state/heartbeat/event, exact SHA chain,
test counts, NOT_RUN items, limitations, files, workers, locks, and adoption
instructions. Stop every owned worker and leave all cycle worktrees clean.

## 10. Gate matrix

| Gate | Requirement |
|---|---|
| G0 | Intake identity, authority, cleanliness, and owner GO valid |
| G1 | M0 SHV1 post-adoption closure PASS |
| G2 | MDRAP exact pin, MIT license, hashes, and selective boundary PASS |
| G3 | Data Fusion exact adoption + two recorded semantics fixes PASS |
| G4 | Canonical event/schema/quality goldens and negatives PASS |
| G5 | Immutable archive/quarantine/replay exact reproduction PASS |
| G6 | BBO/depth/TCA hand-computed and missing-evidence gates PASS |
| G7 | NautilusTrader 1.230.0 round-trip and no-lookahead PASS |
| G8 | No secrets, raw licensed data, forbidden modules, or execution code PASS |
| G9 | Targeted/compatibility/full suite, compileall, diff-check PASS |
| G10 | Bounded performance characterization complete without false HFT claim |
| G11 | Fresh A7 audit: zero HIGH/CRITICAL |
| G12 | Clean closeout, workers zero, asset cycles untouched |

Every gate is exactly `PASS`, `FAIL`, `NOT_RUN`, or `BLOCKED`, with command,
exit code, UTC, HEAD, input hashes, output path, and stderr tail. A missing
test is never inferred from a neighboring PASS.

## 11. Terminal verdicts

Only these verdicts are legal:

- `MARKET_DATA_PLANE_V1_PASS` — every required gate passes and A7 has zero
  HIGH/CRITICAL objections;
- `MARKET_DATA_PLANE_V1_BLOCKED_SHV1_POST_ADOPTION` — M0 cannot be completed;
- `MARKET_DATA_PLANE_V1_BLOCKED_RESOURCE_CONFLICT` — a required alone/heavy
  gate remains unavailable after every light phase and scheduler admission;
- `MARKET_DATA_PLANE_V1_BLOCKED_COMPATIBILITY` — pinned Data Fusion or
  Nautilus compatibility cannot be satisfied without scope change;
- `MARKET_DATA_PLANE_V1_FAIL_CORRECTNESS` — canonical, archive, replay,
  quality, BBO, depth, TCA, or bridge correctness fails;
- `MARKET_DATA_PLANE_V1_INCOMPLETE_NOT_ADOPTABLE` — evidence/provenance/audit
  is incomplete despite code existing.

`PASS` means the shared engineering plane is suitable for future cycle-level
adoption. It does not authorize any dataset for scoring, open S1, validate an
edge, or authorize trading.

## 12. Forbidden actions

- no push or merge to `main`;
- no reset, branch/worktree deletion, history rewrite, or cleanup of owner
  `.zcode/` files;
- no edit to historical cycle evidence, ledgers, survivors, or failure rows;
- no scored PnL, S1, optimization, or strategy-family work;
- no paper/testnet/live broker or exchange activity;
- no provider account, purchase, license acceptance, or credential display;
- no raw proprietary payload in git;
- no disabling a gate because it is slow or inconvenient;
- no killing or competing with a foreign cycle's worker;
- no whole-repo MDRAP vendor drop and no unreviewed binary.

## 13. First-session dispatch prompt

After committing this plan, give one fresh A1 exactly:

```text
You are A1 Controller for MARKET-DATA-PLANE-V1. Read
plans/PLAN_market_data_plane_v1.md IN FULL, then CLAUDE.md, RULES.md,
NOTES.md, research/wayfinder/MAP.md, and the lead-engineer handbook. The plan
is the sole fresh-context authority.

Owner GO: GO MARKET DATA PLANE V1 ENGINEERING

Run one logical session continuously through an honest terminal verdict. Begin
with the Section 9 P0 first report, then perform mandatory M0 SHV1
post-adoption closure. Do not skip M0 because the historical SHV1 closeout was
PASS; remeasure current operational adoption. Use flat child lanes only, never
grandchildren. Continue automatically after every passing checkpoint. Respect
the machine-wide heavy lock and all foreign asset cycles; never kill, edit, or
compete with their workers. No score, S1, provider signup/purchase, credential,
paper/live order, push, main merge, reset, or worktree deletion is authorized.

Selective MDRAP adaptation only: pin the exact upstream commit, preserve MIT
provenance, do not execute its untrusted scripts/binaries, do not add it as a
runtime dependency, and do not import its strategy/execution/security stack.
Use the audited Data Fusion pin and NautilusTrader 1.230.0 contracts exactly.
Publish evidence at every gate and close truthfully on a real hard stop.
```
