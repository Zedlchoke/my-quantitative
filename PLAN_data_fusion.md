# FREE DATA FUSION V1 — COMMON PIT DATA AUTHORITY FOR THREE ASSETS

> Owner plan dated 2026-09-04.
>
> Build one reusable, audit-first data layer that can combine free sources
> without changing any frozen Crypto, Stocks or Forex experiment. This is an
> engineering/data-authority cycle: no strategy PnL, no S1 and no deployment.

## 0. Integration boundary

Data Fusion runs independently:

```text
branch    orca/data-fusion-v1-integration
worktree  .worktrees/data-fusion-v1/integration
base      owner-plan commit on main
```

Asset adoption rules:

- Crypto V12 is frozen at W12 and may not adopt Data Fusion V1. Its first
  eligible consumer is V13.
- Stocks V4 may adopt the frozen Data Fusion core only before its data and
  selection freeze, through an explicit compatibility cherry-pick.
- Forex V2 may adopt it under the same rule.
- If an asset has already frozen selection/data, adoption waits for its next
  cycle. No result-aware retrofitting is permitted.

The data-fusion branch never edits asset state, ledgers, selections, W pins,
scored artifacts or worktree manifests.

## 1. Mission

Create a small common library that answers, for every datum:

```text
where did it come from?
what entity and field does it describe?
when did the event happen?
when was it available to the market?
when did it become effective?
which revision/vintage is this?
what raw bytes prove it?
what license/use boundary applies?
may this datum be used for research at decision time T?
```

V1 does not promise that every free source becomes authorized. A truthful
`CANDIDATE_NOT_AUTHORIZED` or `UNAVAILABLE_FAIL_CLOSED` is acceptable.

## 2. Initial source registry

Register capabilities, not marketing claims:

### Forex candidates

- TrueFX: historical top-of-book bid/ask tick candidate; internal-use license
  and redistribution restrictions must be captured.
- BIS: policy-rate history and effective-date metadata candidate.
- ECB SDMX: official rates/macro/statistical series candidate.
- FRED/ALFRED: release/vintage macro candidate; API key required.
- OANDA public financing history: broker-specific swap/financing candidate,
  never generic market-swap authority without proof.
- Twelve Data: existing price source/cross-check under its current entitlement.

### Stocks candidates

- SEC Company Facts/Submissions: official fundamentals and filing clocks.
- SEC Form 13F: delayed institutional-holdings candidate.
- FINRA short-interest/short-sale-volume: distinct datasets; never borrow fee.
- Alpha Vantage Earnings: earnings/estimate/surprise candidate requiring free
  key and historical-PIT/revision audit.
- Massive Basic: two-year price/corporate-action cross-check candidate.
- Twelve Data: existing price source under current entitlement.
- S&P DJI announcements: index-event archive candidate; completeness and
  machine-readable history not assumed.

No source enters an asset scoring run merely by appearing in this registry.

## 3. Required common record

Every normalized observation includes:

```text
source_id
dataset_id
entity_id
field
value
unit
event_time_utc
available_time_utc
effective_time_utc
vintage_time_utc
retrieved_time_utc
raw_path
raw_sha256
license_id
entitlement_id
normalizer_version
```

Rules:

- all timestamps are timezone-aware UTC;
- `available_time_utc` is mandatory for scored use;
- retrieval time never substitutes for historical availability time;
- raw SHA-256 is lowercase 64-hex and binds normalized rows to immutable bytes;
- revisions are appended as new vintages; earlier observations are not
  overwritten;
- missing authority is represented explicitly, never guessed.

## 4. Point-in-time join contract

For a decision at `T`, a row is eligible only when:

```text
available_time_utc <= T
effective_time_utc <= T, when effectiveness is required by the field
identity mapping is valid at T and was itself available by T
license and entitlement permit internal research use
raw bytes and normalizer version match the frozen manifest
```

Among eligible revisions for the same key, select the latest vintage that was
available by `T`. Never select a later-restated fact.

No forward fill crosses:

- entity-identity changes;
- source coverage gaps;
- filing/release boundaries;
- entitlement boundaries;
- explicit invalidation or delisting.

## 5. Identity mapping

Support temporal, auditable aliases:

```text
Stocks: ticker/share class <-> canonical security ID <-> CIK
Forex: provider symbol <-> ISO base/quote pair
Crypto: venue instrument <-> canonical base/quote/contract identity
```

An alias row has valid-from, valid-to, available-at, source and raw hash. Current
ticker mappings may not be projected backward without evidence.

## 6. Conflict policy

Data Fusion never averages conflicting facts silently.

Each dataset freezes one authority role:

```text
PRIMARY       value used for research
CROSS_CHECK   compared but never fills PRIMARY gaps
DIAGNOSTIC    displayed only
UNAVAILABLE   cannot be used
```

Examples:

- SEC filing fact may be PRIMARY for reported accounting data while Alpha
  Vantage estimate is a separate candidate field, not a blended EPS.
- TrueFX bid/ask may be PRIMARY for execution-cost research while Twelve Data
  H1 is CROSS_CHECK; missing TrueFX intervals are not patched with midpoint.
- FINRA short-sale volume is not converted into short interest or borrow fee.

Every conflict emits a stable reason code and remains fail-closed until an
owner-approved authority policy resolves it.

## 7. License and entitlement gate

Each source manifest records:

- official source URL and terms URL;
- cost tier and whether account/key is required;
- internal research, local storage, derivative-work and redistribution rights;
- geography/user-type restrictions;
- retrieval method and rate limits;
- raw-data Git policy;
- evidence capture time and content hash.

Allowed statuses:

```text
DOCUMENTED_CANDIDATE
CANDIDATE_NOT_AUTHORIZED
AUTHORIZED_INTERNAL_RESEARCH
UNAVAILABLE_FAIL_CLOSED
REJECTED_LICENSE
```

Free of charge is not equivalent to no account, no key or unrestricted license.

## 8. Package and ownership

Create:

```text
research/data_fusion/
  __init__.py
  models.py
  authority.py
  pit.py
  identity.py
  conflicts.py
  manifest.py
  source_registry.py

tests/data_fusion/
  test_models.py
  test_authority.py
  test_pit.py
  test_identity.py
  test_conflicts.py
  test_manifest.py
  test_source_registry.py

research/control/data_fusion_v1_run/
  run_contract.json
  state.json
  heartbeat.json
  event_log.jsonl
  source_registry.json
  worktree_manifest.json
  gates/
```

Common code must use the Python standard library where practical and introduce
no new dependency without evidence.

## 9. Phase DF0 — bootstrap

1. Measure main, active worktrees, dirty files and workers.
2. Create the dedicated integration branch/worktree.
3. Record Crypto/Stocks/Forex adoption boundaries.
4. Freeze source registry schema and reason-code vocabulary.
5. Confirm zero strategy/scoring paths in the cycle diff.

## 10. Phase DF1 — offline common core

Implement and test:

- immutable normalized records;
- strict UTC parsing and timestamp ordering;
- raw SHA/path validation;
- license/entitlement authority decisions;
- PIT as-of joins across revisions;
- temporal identity aliases;
- explicit source-role conflicts;
- deterministic manifest serialization and hashing;
- append-only revision behavior.

All tests use tiny hand-computed fixtures. No network is required.

## 11. Phase DF2 — source adapters

Adapters are separated from the common core. First wave:

```text
SEC Company Facts/Submissions
ECB SDMX
BIS policy rates
FINRA catalog/download
TrueFX archive inventory
FRED/ALFRED contract (key-gated, no credential required for tests)
```

Each adapter must support:

- discovery without scoring;
- deterministic request identity;
- local raw cache outside Git;
- response byte hash and HTTP metadata;
- rate-limit/retry policy;
- parser version;
- no silent schema coercion;
- two-pull equality where the source is expected immutable;
- fail-closed missing timestamp/license fields.

Do not create accounts, request keys or accept new click-through terms without
owner instruction. Key-gated adapters can be implemented and fixture-tested but
remain `CANDIDATE_NOT_AUTHORIZED`.

## 12. Phase DF3 — independent audit and freeze

Independent audit recomputes:

- every model invariant and PIT golden;
- no future vintage leakage;
- no current-ticker backward projection;
- conflict refusal and no cross-source gap patching;
- manifest/digest determinism;
- license status from captured evidence;
- raw-data Git exclusion;
- zero strategy PnL/S1/deployment activity;
- compatibility tests against current common/protocol code.

Freeze:

```text
MULTISOURCE_DATA_CORE_SHA
SOURCE_REGISTRY_SHA256
SCHEMA_VERSION
```

The core is adoptable only after all mandatory gates PASS and the integration
tree is clean.

## 13. Asset adoption gates

Each asset uses a separate adoption commit and never merges the whole
data-fusion history blindly.

### Stocks V4

Adoption before data/selection freeze requires:

- existing authorized price/cohort behavior byte-compatible;
- SEC/13F/FINRA fields remain unavailable until provider-specific authority
  passes;
- no ETF strategy consumes company fundamentals accidentally;
- full Stocks and protocol suites PASS;
- selection remains outcome-blind.

### Forex V2

Adoption before data/selection freeze requires:

- existing H1 snapshot behavior unchanged;
- TrueFX is cross-check only until 7-pair coverage/license/PIT gates PASS;
- BIS/ECB/FRED data does not unlock carry or macro-surprise automatically;
- rollover remains fail-closed without authoritative history;
- full Forex and protocol suites PASS.

### Crypto V13

V12 stays byte-frozen. V13 may adopt only after V12 terminal closeout and a new
owner plan. No data-fusion result changes V12 W12, cells or denominator.

## 14. Test and gate commands

```bash
.venv/bin/python -m pytest tests/data_fusion -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q
.venv/bin/python -m compileall research/data_fusion
git diff --check
git status --porcelain=v1
```

Run the repository full suite alone before freezing the common core. Do not run
it while another asset has a heavy worker.

Every gate records full SHA, command, exit code, stdout/stderr, input/output
hashes, expected/observed, verdict, blocker and clean-tree status.

## 15. Concurrency

Data Fusion DF0/DF1 unit work is light and may run while asset proposal/coding
lanes run. Across the whole 8 GB host:

- only one full pytest, large download, parsing job or scored worker at a time;
- network adapters respect provider rate limits;
- no Data Fusion job reads an asset's gitignored staged data without explicit
  adoption authority;
- no agent edits another worktree.

## 16. Hard boundaries

- No strategy scoring or PnL.
- No S1 listing, opening, hashing or copying.
- No paper/live/orders/broker operations.
- No credentials in files/logs/commands.
- No paid source, account creation or click-through acceptance without owner.
- No raw-data commit or redistribution.
- No patching PRIMARY gaps with another source.
- No modifying frozen asset cycles.
- No force-push, main merge, history rewrite or worktree deletion without owner.

## 17. Delivery

The first deliverable is DF1 offline common core plus tests and source registry.
DF2 adapters follow only after DF1 freezes its interfaces. Final report includes:

```text
full integration SHA
MULTISOURCE_DATA_CORE_SHA
tests and gate results
source-by-source authority status
known unavailable fields
adoption eligibility for Stocks V4 / Forex V2 / Crypto V13
workers zero and tree clean
```
