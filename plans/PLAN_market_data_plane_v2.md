# MARKET-DATA-PLANE-V2 — remediation, BAR contract, and three-asset shadow adoption

> Status at authoring: `PLANNED_NOT_STARTED`.
>
> This plan is a fresh engineering authority. It does not rewrite the closed
> `MARKET-DATA-PLANE-V1` history, does not retrofit an active crypto, stocks,
> or forex cycle, and authorizes no scored result, S1 access, provider signup,
> purchase, credential use, push, or merge to `main`.

## 0. Owner intent and exact objective

The owner asks for two outcomes:

1. repair the defects discovered by the independent post-V1 review; and
2. raise practical integration of the shared market-data plane with the three
   existing research factories: crypto, stocks, and forex.

This is one engineering cycle, not a strategy-research cycle. Its strongest
allowed positive claim is:

```text
MARKET_DATA_PLANE_V2_PASS_THREE_ASSET_SHADOW_READY
```

That claim means all three asset factories can consume their own authorized
S0/open-window inputs through deterministic MDP adapters in a shadow path, and
the resulting canonical rows and schedule-only outputs reconcile against the
legacy path under frozen tolerances. It does **not** mean:

- an active asset cycle was changed;
- data authority was granted;
- a strategy edge was found;
- scored PnL was computed;
- S1 was opened;
- paper or live trading is ready.

## 1. Historical authorities and measured intake snapshot

### 1.1 Immutable historical authorities

- V1 plan: `plans/PLAN_market_data_plane_v1.md`.
- V1 integration branch: `orca/market-data-plane-v1-integration`.
- V1 terminal tip measured at authoring:
  `917b8749c6e61887d0e1046a3b99a1f1cf53dca6`.
- V1 merged into `origin/main` at `9ecf48e8081f3e8e51c6a917d0de2925bc3d3037`.
- V1 terminal verdict:
  `MARKET_DATA_PLANE_V1_BLOCKED_RESOURCE_CONFLICT`.
- V1 A7 audited source SHA:
  `42981b1b1f66ed03e0a933db0a5ef7041220d80e`, 16/16 PASS,
  zero HIGH/CRITICAL.

The V1 terminal report, state, heartbeat, manifests, event log, benchmark and
audit artifacts are historical evidence. V2 may append a correction/addendum;
it must not silently rewrite the original claim.

### 1.2 Measured state at plan authoring

The A1 controller must remeasure all of this at dispatch. At authoring:

```text
root HEAD                 a85ebedacbe277f22c09fd2034df2d7a9ea95d87
origin/main               9ecf48e8081f3e8e51c6a917d0de2925bc3d3037
root relationship         main ahead of origin/main by four Forex control commits
root dirty                 M plans/ACTIVE_CYCLES.json; ?? .zcode/
heavy lock                 HELD_PROVEN by STOCKS-FREE-V13/P0D_BULK_INGEST
MDP full-suite job         MARKET-DATA-PLANE-V1/FULL_SUITE_REGRESSION/
                           20545b514b91, WAITING
active asset authorities  PLAN_crypto_v17.md / PLAN_stocks_v13.md /
                           PLAN_forex_v9.md
S1                         SEALED_UNTOUCHED for every asset
scored budget              0; this engineering cycle has no scored-cell budget
```

The listed dirty paths are owner/current-cycle state. Preserve them. They are
not authorized contents of an MDP-V2 implementation commit.

### 1.3 Verified V1 baseline

The post-V1 review freshly measured:

```text
MDP tests                 227 PASS
Data Fusion tests         206 PASS
governance tests          112 PASS
combined targeted total   545 PASS
protocol suite            163 PASS (includes six protocol-registry tests)
synthetic end-to-end demo PASS
compileall                PASS
JSON evidence parse       24/24 PASS
pip check                 PASS
git diff --check          PASS
```

These counts are an intake snapshot, not a future PASS. V2 reruns the tests at
its own frozen SHA.

## 2. Findings V2 must close

### F1 — V1 full-suite gate is still not complete

V1 G9 is `PARTIAL`; the full repository suite was
`NOT_RUN_RESOURCE_CONFLICT`. The scheduler entry exists but does not by itself
prove that the command will run automatically after the lock is released.

Required closure:

- inspect the machine-wide lock before any full-suite attempt;
- when and only when it is `FREE_PROVEN`, run the full suite alone from the
  exact V1 terminal tip or an explicitly frozen reproduction tree;
- record command, exit code, stdout/stderr digest, duration, host, exact SHA,
  lock evidence, and clean-tree result;
- append `v1_g9_resumption_verdict.json` and an event; never overwrite the V1
  terminal report;
- if the lock remains held, keep the job `WAITING` and report
  `NOT_RUN_RESOURCE_CONFLICT` without contention.

### F2 — manifest/chunk identifier and path confinement

At V1, `chunk_path()` accepts any string of length at least four,
`manifest_path()` accepts arbitrary strings, and `load_manifest()` validates
the loaded body but does not bind the requested ID to the body's
`manifest_id`.

Required closure:

```text
content ID grammar        exactly [0-9a-f]{64}
manifest filename binding requested_id == validated manifest_id
path confinement          resolved target remains below the declared archive root
failure mode              fail closed before filesystem read/write outside root
reason                    explicit ArchiveError/ManifestValidationError
```

Mandatory negative tests:

- empty, short, uppercase, non-hex and overlong IDs;
- `../`, absolute path, separator and encoded/pathlike variants;
- valid manifest bytes stored under a different valid 64-hex filename;
- a symlink escape at a chunk or manifest directory boundary;
- `verify_chunk()` with a malicious ID;
- replay with a malicious or filename/body-mismatched manifest ID;
- valid historical IDs remain byte-compatible.

### F3 — terminal/control-plane reconciliation

V1's terminal report says P9 closed, while its state and heartbeat still say
`P8_A7_AUDIT_IN_FLIGHT`; its worktree manifest still lists completed lanes as
planned; the canonical registry records an early M0 SHA and an empty
integration worktree.

Required closure:

- append a V1 post-terminal reconciliation artifact that names every stale
  field and its corrected value;
- append an event-log correction; do not delete or rewrite prior events;
- update the canonical registry only through `researchctl cycle update` or the
  atomic registry API, with CAS+journal evidence;
- record V1 terminal tip `917b8749...`, the historical integration path or an
  explicit `HISTORICAL_WORKTREE_UNAVAILABLE`, workers zero, lifecycle terminal,
  GO dead, and the resumption status of G9;
- generate the `ACTIVE_CYCLES.json` projection through the canonical writer;
- create a terminal-consistency validator that compares terminal report,
  state/addendum, heartbeat/addendum, worktree manifest/addendum, registry,
  branch tip, workers, gates and event log.

The validator must fail on the exact V1 stale-state fixture, then pass only
when the addendum is supplied. Historical bad bytes stay visible.

### F4 — portable resource metrics

V1 names raw `resource.getrusage(...).ru_maxrss` as `peak_rss_kb`, although
macOS reports bytes and Linux reports KiB.

Required schema bump:

```json
{
  "schema": "mdp_perf_run@2",
  "platform": "darwin|linux|...",
  "peak_rss_raw": 0,
  "peak_rss_raw_unit": "bytes|kib|unknown",
  "peak_rss_bytes": 0,
  "peak_rss_mib": 0.0
}
```

Tests must monkeypatch both macOS and Linux values and verify conversion. V1's
baseline is not rewritten; a `perf_v1_unit_erratum.json` explains that
`1293058048` on the V1 Darwin host means about 1233.2 MiB.

### F5 — operational doctor signal quality

Current doctor output contains long-lived expected drift mixed with actionable
HIGH findings. V2 must add a structured waiver/supersession record rather than
normalizing or hiding findings.

Minimum waiver fields:

```text
finding identity / severity / exact affected digest
classification / evidence reference / approver authority
created UTC / expiry UTC or terminal event
status ACTIVE|EXPIRED|SUPERSEDED|RESOLVED
```

Doctor behavior:

- an unwaived HIGH remains HIGH;
- a mismatched or expired waiver does not suppress it;
- an active exact-digest waiver emits `WAIVED_HIGH` visibly, never `PASS`;
- terminal/resumed-cycle evolution can supersede a historical pause pin only
  with an append-only transition record;
- monitoring remains read-only; dashboard refresh never writes tracked files.

## 3. What “integrated with three research machines” means

The three “machines” are the crypto, stocks and forex research factories, not
three physical computers.

Integration has four measurable levels:

| Level | Meaning | Approximate integration score |
|---|---|---:|
| L0 | shared MDP library exists; no asset imports it | 4.5/10 |
| L1 | three provider-neutral adapters pass synthetic tests | 6.0/10 |
| L2 | one authorized S0 snapshot per asset passes dual-read parity | 7.5/10 |
| L3 | three next-cycle adoption packets are frozen and shadow-ready | 8.5/10 |
| L4 | each asset completes at least one full future research cycle with MDP as canonical input | 9.0+/10 |

This plan can authorize L3. L4 requires later asset-cycle evidence and cannot
be claimed by an engineering-only plan.

### 3.1 Why BAR support is mandatory

MDP-V1 intentionally supports canonical TRADE and QUOTE events only. The
existing research factories predominantly consume OHLCV bars. V2 must not
mislabel OHLCV as quotes, trades or depth. It must add a separate versioned
bar contract.

Frozen design name:

```text
mdp.market_bar@2
```

The `@2` name denotes a new schema contract; it does not mutate
`mdp.market_event@1`.

Minimum bar fields:

```text
schema_version / bar_id / raw_id / source_id / provider_id / venue
instrument_id / asset_class / bar_type / interval_ns
open_time_utc_ns / close_time_utc_ns / available_time_utc_ns
open / high / low / close / volume
quote_volume / trade_count / taker_buy_base / taker_buy_quote
price_precision / size_precision
adjustment_mode / corporate_action_ref
completeness_status / quality_status / reason_codes
raw_sha256 / manifest_sha256 / normalizer_version
```

Rules:

- OHLCV values persist as exact decimal strings;
- `open_time < close_time <= available_time` unless a provider-specific,
  evidenced publication rule proves a later availability time;
- no bar may create BBO, depth, spread or TCA evidence;
- adjusted and raw prices are separate identities;
- stocks corporate actions and delistings remain explicit;
- forex session/DST and crypto continuous-clock rules are asset-specific;
- missing volume/trade count stays null/NOT_EVALUABLE, never zero;
- duplicate or non-disjoint bar intervals fail closed;
- Nautilus mapping is lossless-or-raise to its pinned Bar type;
- any change to score-affecting bar semantics requires a new schema version.

## 4. Adoption boundaries for active cycles

At dispatch, A1 must inspect the canonical registry and each asset worktree.

Hard rule:

```text
An asset cycle that has frozen data, proposals, selection, code, or scored
identity MUST NOT adopt MDP-V2 in place.
```

Therefore:

- Crypto V17, Stocks V13 and Forex V9 are read-only consumers of attention,
  not edit targets for this plan.
- Their workers may continue. V2 performs light work in parallel and queues
  heavy tests behind the machine-wide lock.
- Adoption packets target the next eligible cycle after each current cycle
  reaches a terminal verdict.
- If an active cycle has not crossed any freeze, A1 still needs a fresh owner
  amendment before adoption; V2 does not infer that authority.

## 5. Branch, worktree and ownership topology

### 5.1 Integration seat

Create only after the root plan commit is clean and the cycle ID/branch do not
already exist:

```text
cycle       MARKET-DATA-PLANE-V2
worktree    .worktrees/market-data-plane-v2/integration
branch      orca/market-data-plane-v2-integration
base        exact owner-plan commit on main, remeasured at bootstrap
owner       A1
```

A1 owns:

- integration and cherry-picks;
- architecture/run contracts and freezes;
- `research/control/market_data_plane_v2_run/**`;
- V1 append-only remediation/addendum files;
- canonical registry commands;
- central documentation and adoption packets;
- final publication and terminal verdict.

### 5.2 Lane topology

Every lane branches from the exact frozen wave SHA and receives a disjoint
ownership manifest.

| Lane | Role | Allowed implementation paths |
|---|---|---|
| A2 | archive integrity | `research/market_data_plane/archive.py`, manifest/replay security tests |
| A3 | control reconciliation | governance terminal-consistency and doctor-waiver modules/tests |
| A4 | bar contract | bar model, bar quality, archive/replay extensions, Nautilus bar bridge, dedicated tests |
| A5 | crypto adapter | `research/market_data_plane/adapters/crypto/**`, crypto adapter tests |
| A6 | forex adapter | `research/market_data_plane/adapters/forex/**`, forex adapter tests |
| A8 | stocks adapter | `research/market_data_plane/adapters/stocks/**`, stocks adapter tests |
| A9 | parity/reproduction | generic dual-read comparator and detached-tree reproduction tests |
| A7 | independent audit | `research/audits/market_data_plane_v2/**` only |

`__init__.py`, shared exports, central docs and control artifacts are
integration-owned. A lane must not edit them merely to make imports convenient;
A1 performs the small integration export patch after each targeted gate.

### 5.3 Concurrency

- At most A1 plus three light lanes concurrently.
- Full pytest, large snapshot conversion, performance benchmark and detached
  full reproduction are HEAVY and require `FREE_PROVEN` plus exclusive
  machine-wide lock.
- No V2 process may kill, pause, throttle or reuse the worker of another cycle.
- If the lock is held, record `NOT_RUN_RESOURCE_CONFLICT` and continue only
  independent light work.

## 6. Data authority and credential contract

V2 creates adapters; it does not create authority.

- No new signup, purchase, browser acceptance or credential request.
- Existing keys remain environment-only and must never appear in prompts,
  commands, logs, artifacts or Git.
- Tests use provider-neutral synthetic fixtures or small redistributable
  fixtures already authorized by the repository.
- Real shadow proofs may read only an existing asset cycle's S0/open-window
  snapshot whose entitlement explicitly permits this internal derived use.
- Raw/provider payloads stay gitignored. Commit hashes, schemas, manifests,
  census and bounded derived diagnostics only when the source terms permit.
- If permission cannot be established, that asset's real proof is
  `BLOCKED_DATA_AUTHORITY`; synthetic adapter tests may still pass but do not
  qualify for L2/L3.
- S1 paths and dates are forbidden inputs. A recursive input-manifest scan must
  prove the shadow proof does not intersect S1.

## 7. Per-asset adapter contracts

### 7.1 Crypto

Priority: easiest first because crypto already has event/tick-like aggTrades
and continuous-clock bars.

Inputs allowed when separately authorized:

- Binance aggTrades -> `mdp.market_event@1` TRADE;
- Binance kline/OHLCV -> `mdp.market_bar@2`;
- existing funding/OI records remain Data Fusion observables and join only by
  evidenced availability clocks; they are not fabricated as market events.

Required checks:

- symbol/instrument mapping and perpetual contract identity;
- millisecond-to-nanosecond conversion exactly once;
- aggTrade ID/sequence duplicate and gap semantics;
- 24/7 interval coverage and no overlapping klines;
- close-time availability and one-bar lag;
- 1m-to-2m aggregation, if tested, must use two complete 1m bars and a frozen
  boundary rule; direct Binance 2m must not be claimed;
- existing 15m research schedule parity on an S0 subset.

### 7.2 Forex

Inputs allowed when separately authorized:

- stored Twelve Data or other already-authorized OHLCV ->
  `mdp.market_bar@2`;
- genuine bid/ask history -> QUOTE only when the source actually provides both;
- macro/rate/release observables remain Data Fusion rows and retain their PIT
  clocks.

Required checks:

- canonical pair/base/quote identity;
- provider timezone -> UTC with DST fixtures;
- session/weekend gaps distinguished from missing data;
- date-only macro observations retain next-day-exclusive availability bounds;
- OHLCV never creates bid/ask, spread, swap or rollover evidence;
- legacy hourly decision schedule parity on an authorized S0 subset.

### 7.3 Stocks

Inputs allowed when separately authorized:

- stored authorized daily OHLCV -> `mdp.market_bar@2`;
- SEC/FINRA/macro facts remain Data Fusion observables;
- corporate-action, symbol-history and delisting evidence are referenced, not
  erased by adjustment.

Required checks:

- permanent entity ID distinct from ticker;
- exchange calendar, holidays and early closes;
- raw versus adjusted OHLCV identity;
- split/dividend factors and exact availability;
- delisted/dead-name coverage census;
- no forward-filled price after delisting;
- total-return use declared separately from raw execution prices;
- legacy daily decision schedule parity on an authorized S0 subset.

## 8. Dual-read shadow contract

For each asset, use one bounded, predeclared S0/open-window snapshot. Run:

```text
legacy reader  -> legacy normalized rows -> schedule-only consumer
same raw bytes -> MDP adapter -> canonical rows -> compatibility projection
```

Compare without computing PnL:

1. input raw SHA set;
2. instrument universe and identity mapping;
3. row/event/bar count;
4. min/max exchange/open/close/available clocks;
5. coverage gaps and duplicates;
6. exact OHLCV/price/quantity/volume values after declared representation;
7. adjustment and corporate-action mode;
8. feature-ready ordering;
9. decision timestamps and schedule-only target/signals;
10. diagnostics/quarantine counts and reasons.

Allowed tolerances must be frozen before running:

- identifiers, timestamps, counts, missingness and schedules: exact;
- decimal prices/volumes: exact after canonical decimal conversion;
- derived floating indicators: either exact Decimal or a named absolute/relative
  tolerance justified by the legacy implementation;
- zero unexplained differences.

Forbidden shadow outputs:

- PnL, PF, Sharpe, drawdown, break-even cost, stress PnL;
- family ranking or selection;
- observed/published trial records;
- S1 results.

Replay of the shadow run must produce zero scientific denominator delta.

## 9. Execution phases

### P0 — Intake and first report

Before editing implementation:

1. read this plan, `CLAUDE.md`, `HOW_TO_BE_A_LEAD_ENGINEER.md`, `NOTES.md`,
   `research/wayfinder/MAP.md`, V1 terminal/audit, and current registry;
2. print absolute cwd, branch, full HEAD, status, remote relation and all
   worktrees;
3. classify every dirty path;
4. inspect lock and reconciled jobs;
5. confirm no V2 branch/worktree/cycle record exists;
6. remeasure active asset phases and freeze boundaries;
7. publish the Section 15 first report;
8. bootstrap the V2 integration seat and append-only control artifacts.

Gate `V2-G0`: correct clean integration seat, exact base, owner dirty files
untouched, cycle registered `ACTIVE_LIGHT`, workers zero, S1 sealed.

### P1 — V1 G9 resumption attempt

Inspect the lock once. If `FREE_PROVEN`, acquire it and run the V1 full suite
alone at exact V1 tip. If held, keep the scheduler job waiting and proceed with
light V2 work; do not poll aggressively.

Outputs:

- `research/control/market_data_plane_v1_run/v1_g9_resumption_verdict.json`;
- append-only event;
- stdout/stderr logs outside Git or small digests inside the artifact;
- explicit `PASS`, `FAIL`, or `NOT_RUN_RESOURCE_CONFLICT`.

Gate `V2-G1`: evidence is complete and historical V1 bytes are preserved.

### P2 — Architecture freeze

A1 freezes:

- exact V1/source/base SHAs;
- findings F1-F5 and negative-test matrix;
- `mdp.market_bar@2` field list and semantic rules;
- adapter interfaces and per-asset identity rules;
- dual-read comparator schema and tolerances;
- permitted S0 snapshot manifests or `UNAVAILABLE` status;
- performance procedure and portable RSS schema;
- ownership and merge order.

No implementation lane branches before `architecture_freeze_v2.json` exists,
validates and is committed.

### P3 — Core remediation wave

Dispatch A2, A3 and A4 in parallel from the same P2 wave SHA.

- A2: F2 identifier/path confinement.
- A3: F3 terminal validator, F5 structured waivers and registry/doctor tests.
- A4: F4 portable benchmark plus the `market_bar@2` contract and bridge.

Each lane returns one clean focused commit. A1 integrates in order A2 -> A3 ->
A4, running that lane's targeted tests after each pick. Any shared-export patch
belongs to A1 and receives its own test.

Gate `V2-G2`: all negative cases fail closed; no historical valid fixture
changes bytes unexpectedly.

### P4 — Core reproduction freeze

Run twice from two detached trees:

- V1 TRADE/QUOTE archive and replay goldens;
- new BAR build/archive/replay/bridge goldens;
- filename/body mismatch and path-confinement negatives;
- terminal-consistency stale fixture and corrected-addendum fixture;
- Darwin/Linux resource-unit fixtures.

Freeze `MDP_V2_CORE_SHA` only on exact match and clean trees.

Gate `V2-G3`: core reproduction `ALL_MATCH` and V1 compatibility PASS.

### P5 — Adapter implementation wave

From exact `MDP_V2_CORE_SHA`, dispatch A5 crypto, A6 forex and A8 stocks in
parallel. Each adapter owns only its namespace and tests. Network calls are
forbidden in unit tests; fixtures are synthetic or already authorized.

Merge order: crypto -> forex -> stocks. After each pick:

1. compile/import;
2. adapter targeted tests;
3. core MDP tests;
4. corresponding legacy asset parsing/calendar tests;
5. status and diff check;
6. event-log record.

Gate `V2-G4`: three adapter suites PASS without changing active cycle files or
scientific counters.

### P6 — Real S0 shadow proofs

For each asset independently:

1. prove source entitlement and snapshot eligibility;
2. freeze bounded input manifest and S1 exclusion proof;
3. run legacy and MDP readers from the same raw SHA set;
4. run the frozen comparator;
5. run schedule-only consumer and recursive PnL-field leak scan;
6. reproduce from a detached tree;
7. record PASS/BLOCKED separately.

Recommended order: crypto -> forex -> stocks. This order reflects increasing
calendar/corporate-action complexity, not scientific importance.

An unavailable asset snapshot does not permit substitution. It yields
`ASSET_SHADOW_BLOCKED_DATA_AUTHORITY` and prevents the three-asset L3 claim.

Gate `V2-G5-{CRYPTO,FOREX,STOCKS}`: exact parity, zero unexplained differences,
zero denominator delta, S1 sealed.

### P7 — Adoption packets

For every asset with P6 PASS, create a machine-readable packet under:

```text
research/control/market_data_plane_v2_run/adoption/crypto_next_cycle.json
research/control/market_data_plane_v2_run/adoption/forex_next_cycle.json
research/control/market_data_plane_v2_run/adoption/stocks_next_cycle.json
```

Each packet contains:

- MDP V2 core SHA;
- adapter SHA and tests;
- source/data manifest SHA;
- authority scope and expiry;
- legacy-vs-MDP parity digest;
- supported event/bar types and explicit unsupported fields;
- required import/config changes for the next cycle;
- rollback rule;
- first-cycle canary gates;
- forbidden active-cycle IDs.

No active plan is edited. The next asset plan explicitly adopts the packet
after its previous cycle is terminal.

Gate `V2-G6`: packet schema validates and cannot be applied to a forbidden
active/frozen cycle.

### P8 — Performance and complete test battery

Light tests may run while a foreign heavy worker exists. Heavy work waits.

Required battery when lock is `FREE_PROVEN`:

1. compileall;
2. archive/manifest/replay/security tests;
3. BAR model/quality/bridge tests;
4. all three adapter suites;
5. Data Fusion suite;
6. governance and protocol suites;
7. crypto, stocks and forex compatibility suites selected by the test router;
8. full `pytest tests/ -q` alone;
9. V2 performance benchmark with portable RSS fields;
10. `git diff --check` and clean-tree verification.

Performance gates:

- retain the V1 TRADE/QUOTE throughput within the frozen 20% regression
  ceiling on the same host class;
- report BAR throughput separately;
- report peak RSS in normalized bytes/MiB;
- make no HFT or cross-host speed claim;
- if host class differs, record a new baseline without comparing unlike hosts.

Gate `V2-G7`: full battery PASS. If the heavy lock never becomes free, the
only honest result is `NOT_RUN_RESOURCE_CONFLICT` and no global PASS.

### P9 — Independent A7 audit

A7 branches from the exact candidate SHA and writes audit artifacts only. A7
must independently verify:

1. V1 history preserved and G9 resumption truthfully labeled;
2. identifier/path confinement, including symlink and mismatch attacks;
3. terminal-consistency validator catches the frozen V1 stale fixture;
4. registry update used atomic CAS+journal path;
5. portable RSS math on Darwin and Linux;
6. BAR schema does not synthesize microstructure;
7. each adapter preserves its asset identity/calendar semantics;
8. real shadow source authority and S1 exclusion;
9. parity comparison from raw SHA to schedules;
10. zero PnL leakage and zero denominator mutation;
11. detached reproduction;
12. full-suite/lock evidence;
13. no active-cycle retrofit;
14. no credentials/raw licensed payloads in Git;
15. worktrees, workers and clean state;
16. strongest allowed terminal verdict.

Any HIGH/CRITICAL blocks PASS. A7 never repairs findings.

Gate `V2-G8`: fresh A7 audit PASS with zero unresolved HIGH/CRITICAL.

### P10 — Terminal closeout

A1 synchronizes:

```text
state.json
heartbeat.json
event_log.jsonl
worktree_manifest.json
terminal_report.json
registry + generated projection
V1 append-only correction/resumption references
three adoption packets or explicit blocked records
```

Run the terminal-consistency validator against V2 itself before commit. Workers
must be zero. Do not delete evidence worktrees without owner approval. No push
or merge is authorized by this plan.

## 10. Gate matrix

| Gate | Required evidence |
|---|---|
| V2-G0 | intake, clean integration bootstrap, registry truth |
| V2-G1 | V1 G9 resumption PASS/FAIL/NOT_RUN recorded append-only |
| V2-G2 | F2-F5 remediation and negative tests PASS |
| V2-G3 | detached core reproduction ALL_MATCH; V1 compatibility PASS |
| V2-G4 | crypto/forex/stocks adapter suites PASS |
| V2-G5-C | authorized crypto S0 shadow exact parity |
| V2-G5-F | authorized forex S0 shadow exact parity |
| V2-G5-S | authorized stocks S0 shadow exact parity |
| V2-G6 | three next-cycle adoption packets validate |
| V2-G7 | full battery and portable performance evidence PASS |
| V2-G8 | independent A7, zero unresolved HIGH/CRITICAL |
| V2-G9 | terminal metadata/registry/workers/trees reconcile |

## 11. Terminal verdicts

Use the strongest label supported by evidence:

- `MARKET_DATA_PLANE_V2_PASS_THREE_ASSET_SHADOW_READY` — every gate PASS;
  three authorized real S0 shadow proofs and packets exist.
- `MARKET_DATA_PLANE_V2_PASS_CORE_PARTIAL_ASSET_ADOPTION` — core remediation,
  BAR, full tests and A7 PASS, but only one or two real asset shadow proofs
  pass. Name each blocked asset.
- `MARKET_DATA_PLANE_V2_BLOCKED_DATA_AUTHORITY` — synthetic adapters pass but
  no sufficient authorized real S0 snapshot exists for required parity.
- `MARKET_DATA_PLANE_V2_BLOCKED_RESOURCE_CONFLICT` — a mandatory heavy/full
  gate remains NOT_RUN because the machine-wide lock never became free.
- `MARKET_DATA_PLANE_V2_BLOCKED_ACTIVE_CYCLE_BOUNDARY` — required proof would
  modify or expose an active frozen asset cycle and no safe snapshot exists.
- `MARKET_DATA_PLANE_V2_FAIL_INTEGRITY` — identifier, confinement, replay,
  clock, parity or no-lookahead correctness fails.
- `MARKET_DATA_PLANE_V2_FAIL_COMPATIBILITY` — a legacy asset contract changes
  without an authorized versioned migration.
- `MARKET_DATA_PLANE_V2_INCOMPLETE_NOT_PROMOTABLE` — no stronger truthful
  label applies.

No terminal label from this plan may contain `EDGE`, `SURVIVOR`, `OOS`,
`LIVE_READY` or `DATA_AUTHORIZED` without a separate asset authority.

## 12. First future-cycle canary rule

After this plan closes L3, each asset must adopt MDP in a future plan one at a
time. For that first cycle:

1. pin the adoption packet and exact MDP core SHA;
2. run legacy and MDP inputs in shadow through prelaunch;
3. MDP becomes canonical only after exact parity gate PASS;
4. keep a one-cycle rollback path to the frozen legacy reader;
5. scoring identity includes the MDP data-manifest digest;
6. any post-freeze mismatch closes the cycle; it does not fall back silently;
7. A7 audits the data path, not only the strategy output.

Recommended rollout:

```text
crypto canary -> forex canary -> stocks canary
```

Stocks is last because delistings, permanent identity, exchange calendars and
corporate actions create the largest semantic surface.

## 13. Required tests and commands

Exact filenames may be added by the architecture freeze, but the command
classes are mandatory:

```bash
.venv/bin/python -m compileall -q research/market_data_plane \
  research/data_fusion research/governance

.venv/bin/python -m pytest -q \
  tests/test_mdp_models.py tests/test_mdp_quality.py \
  tests/test_mdp_quarantine.py tests/test_mdp_archive.py \
  tests/test_mdp_replay.py tests/test_mdp_bbo.py \
  tests/test_mdp_depth.py tests/test_mdp_tca.py \
  tests/test_mdp_nautilus_bridge.py tests/data_fusion

.venv/bin/python -m pytest -q \
  tests/test_cycle_registry.py tests/test_heavy_lock.py \
  tests/test_scheduler.py tests/test_protocol_registry.py \
  tests/test_atomic_io.py tests/test_legacy_adapters.py \
  tests/test_diagnostic_persistability.py tests/test_registry_reconcile.py \
  tests/test_lock_job_reconciliation.py

.venv/bin/python research/researchctl.py cycle doctor --json
.venv/bin/python research/researchctl.py locks inspect
.venv/bin/python research/researchctl.py job list
git diff --check
git status --porcelain=v1
```

The test router must add new BAR, security, terminal-consistency and per-asset
adapter tests. Full `pytest tests/ -q` runs only under the free heavy lock.

## 14. Forbidden actions

- Do not rewrite V1 terminal/audit/ledger bytes.
- Do not retrofit Crypto V17, Stocks V13, Forex V9 or any frozen successor.
- Do not read or score S1.
- Do not compute or expose PnL in shadow runs.
- Do not increment scientific denominators.
- Do not create data authority from adapter/test success.
- Do not synthesize quote, spread, depth, swap or TCA from OHLCV.
- Do not put keys, cookies, tokens, passwords or provider payloads in Git.
- Do not run network tests from unit suites.
- Do not contend for, steal or kill a foreign heavy worker.
- Do not hand-edit the canonical registry/projection.
- Do not let A7 repair implementation.
- Do not push, merge to main, delete/reset worktrees or rewrite history without
  fresh owner authority.

## 15. First-report template

Before implementation, A1 reports:

```yaml
cycle: MARKET-DATA-PLANE-V2
measured_utc: ...
cwd: /absolute/path
root_branch: ...
root_head: <40-char-sha>
origin_main: <40-char-sha>
root_dirty:
  - path: ...
    classification: OWNER_CHANGE|AUTHORIZED_HANDOFF|UNEXPLAINED_DRIFT
integration_worktree: ...
integration_branch: ...
integration_head: ...
active_asset_cycles:
  crypto: {cycle: ..., phase: ..., head: ..., workers: ...}
  stocks: {cycle: ..., phase: ..., head: ..., workers: ...}
  forex: {cycle: ..., phase: ..., head: ..., workers: ...}
heavy_lock: FREE_PROVEN|HELD_PROVEN|CONTROL_STATE_DRIFT
v1_tip_verified: true|false
v1_g9_job: ...
s1: SEALED_UNTOUCHED
scientific_budget: 0
go_no_go:
  bootstrap: GO|NO_GO
  light_remediation: GO|NO_GO
  heavy_tests: GO|NO_GO
  asset_retrofit: NO_GO
blockers: []
next_safe_action: ...
```

## 16. Definition of done and score interpretation

The plan is done only when:

- F1-F5 each has an explicit verdict and evidence;
- all valid V1 fixtures remain compatible;
- path/ID negatives fail closed;
- terminal metadata cannot contradict itself without a failing gate;
- portable RSS values are truthful;
- BAR data remains distinct from microstructure evidence;
- three adapters exist and pass synthetic tests;
- every claimed real asset shadow proof has authority, exact raw hashes,
  parity and detached reproduction;
- adoption packets target only future cycles;
- full suite and A7 are complete, or the terminal label explicitly says why
  they are NOT RUN;
- workers are zero and registry/control artifacts agree.

Expected score movement, as a planning target rather than a test claim:

```text
current practical three-asset integration  about 4.5/10 (L0)
after synthetic adapters                   about 6.0/10 (L1)
after three real shadow proofs             about 7.5/10 (L2)
after frozen next-cycle packets            about 8.5/10 (L3)
after one completed MDP-native cycle/asset 9.0+/10 (L4, outside this plan)
```

No agent may report the higher score until the corresponding gates actually
pass.

## 17. Fresh-session A1 dispatch prompt

```text
You are A1 Controller for MARKET-DATA-PLANE-V2.

Read plans/PLAN_market_data_plane_v2.md IN FULL before any change. Then read
CLAUDE.md, HOW_TO_BE_A_LEAD_ENGINEER.md, NOTES.md, research/wayfinder/MAP.md,
the complete V1 terminal/audit evidence, and the canonical cycle registry.
The V2 plan is the sole fresh-cycle authority; V1 and all asset plans remain
historical/current boundaries and must not be rewritten.

Remeasure cwd, full HEADs, porcelain, worktrees, current asset phases,
processes, heavy lock and scheduler job. Preserve the owner's dirty
plans/ACTIVE_CYCLES.json and .zcode/ state unless current evidence proves a
different classification. Produce the exact Section 15 first report before
editing beyond intake.

Run one engineering cycle continuously through the strongest honest terminal
verdict. Do light work while foreign heavy workers run; never contend. Do not
retrofit an active/frozen crypto, stocks or forex cycle. Remediate V1 only via
append-only addenda, fix ID/path confinement, add terminal-consistency gates,
normalize RSS units, add structured doctor waivers, design and implement the
versioned mdp.market_bar@2 contract, build isolated crypto/forex/stocks
adapters, and run authorized S0 dual-read shadow proofs without PnL or
denominator mutation. Dispatch lanes only from frozen SHAs with disjoint
ownership and integrate sequentially. A7 is independent and never repairs.

Full pytest, large snapshot conversion, performance and reproduction are
heavy: run them only when researchctl locks inspect returns FREE_PROVEN and
after acquiring the global lock. Missing authority/resource evidence is
BLOCKED or NOT_RUN, never inferred PASS. Keep S1 sealed. No credentials,
purchase, push, main merge, live/paper/testnet activity, destructive cleanup,
or history rewrite is authorized.
```
