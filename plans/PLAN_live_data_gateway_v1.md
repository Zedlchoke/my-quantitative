# PLAN LIVE-DATA-GATEWAY-V1 — local single-owner market-data gateway (platform cycle)

> Status: `A7 PLAN AUDIT r1 AUTHORIZED_WITH_FINDINGS (0 CRITICAL / 0
> HIGH / 5 MEDIUM / 6 LOW) — ALL 11 FINDINGS REMEDIATED IN-PLAN
> PRE-REGISTRATION` (FND-1 canary direct-leg pacing law frozen;
> FND-2/3 total response-classification law incl. Retry-After on any
> class + 403 fail-fast; FND-4 surface_state added to the datum
> contract with a total 7-state mapping; FND-5/11 evidence claims
> scoped to durable records; LOWs FND-6..10 folded in, §12 test list
> extended). Audit artifact: `plans/audits_live_data_gateway_v1/a7_plan_r1.json`.
> Owner instruction
> 2026-09-21 (verbatim intent, condensed): build one local market-data
> gateway that (1) reduces duplicate requests, (2) prevents HTTP 418/429
> and retry storms, (3) feeds near-real-time prices to the valuation
> worker, (4) provides a controlled REST cache for the decision worker,
> (5) gives the dashboard truthful data status, (6) lays the foundation
> for MICROSTRUCTURE-DATA-MOAT-V1. This cycle searches NO strategy,
> computes NO scored PnL, opens NO S1, places NO order.

## 0. Cycle identity

```text
cycle_id          LIVE-DATA-GATEWAY-V1
asset             shared (market-data platform; consumer cycles span crypto)
plan              plans/PLAN_live_data_gateway_v1.md
budget            0/0 scored cells (platform cycle — NO bookable claim,
                  NO profitability language, ever)
S0                NOT_APPLICABLE (no screening, no hypothesis lane)
S1                SEALED_UNTOUCHED
orders            NONE (no paper/testnet/live order, no broker, no account)
heavy_worker      false (ACTIVE_LIGHT; never acquires the machine-wide
                  heavy lock; lock INSPECTED each status write)
go_phrase         GO LIVE DATA GATEWAY V1 CUTOVER   (typed ONLY at the
                  §9.3 gate; registered-not-consumed until then)
lifecycle         PLANNED_NOT_STARTED at registration; flips to
                  ACTIVE_LIGHT only when the sidecar gateway process is
                  actually running with a live heartbeat
worktree          .worktrees/live-data-gateway-v1/integration
branch            orca/live-data-gateway-v1-integration
```

## 1. What this cycle is NOT

- NOT a strategy/research cycle: no strategy formula, decision schedule,
  universe, cost model or fill rule changes anywhere in this cycle.
- NOT an accounting cycle: historical ledgers, old valuation marks and
  their digests are byte-untouchable; the gateway OBSERVES files
  read-only during sidecar/dual-run.
- NOT an execution surface: no orders, no broker calls, no credentials
  (keyless public data only — the same public Binance fapi surfaces the
  shadow workers already use), no S1 access, no scored computation.
- NOT a silent cutover: every existing worker keeps its CURRENT direct
  Binance path until the owner types the §14 GO phrase; consumers never
  silently fall back to Binance or to the gateway.
- NOT a dashboard rebuild: §10 changes status labels only.

## 2. Measured motivation (evidence, 2026-09-21)

- `results/prospective_shadow_v1/runtime/valuation_heartbeat.json`
  (prospective-shadow-v1 integration worktree): `last_error = price
  fetch: HTTPError: HTTP Error 418: I'm a teapot` at loop 07:15Z.
- `results/prospective_shadow_v1/valuation_marks/XSECT-FUND-CARRY-7D.jsonl`
  carried 45 and `ILLIQ-AMIHUD-28D-W.jsonl` 22
  `DATA_BLOCKED`/`UNAVAILABLE_FAIL_CLOSED` marks at plan-commit instant.
  Ledger-first per family: ILLIQ's first blocked mark is exactly
  2026-09-21T03:55Z (the outage episode start per ops commit 99e00263);
  XSECT additionally carries 23 blocked marks from an earlier episode
  (first 2026-09-15T16:30Z) — the 03:55Z claim is scoped to the
  2026-09-21 episode only. Root cause (registry phase note + 99e00263):
  the shared Cloudflare-WARP egress IP repeatedly auto-banned by fapi
  (`418 … banned until <ms>`; the live error class has since drifted —
  the heartbeat slot read `HTTP Error 403: Forbidden` at 07:25Z;
  durable citations are the registry phase note and commit 99e00263,
  since the heartbeat is a single-slot moving file).
- Current duplicate-request surface (measured from code):
  - `valuation_worker.py` — 1 bulk `GET /fapi/v1/premiumIndex` per 5-min
    loop (bounded retry added 2026-09-21 at 99e00263);
  - `shadow_worker.py` decision fetches — `GET /fapi/v1/klines`,
    `/futures/data/basis`, `/fapi/v1/fundingRate`, `/fapi/v1/time`,
    `/fapi/v1/exchangeInfo` through `PacedFetch` (0.25 s min gap, 6
    attempts, Retry-After honored);
  - each future consumer re-fetches identical historical windows with
    no shared cache;
  - retry behavior lives in EACH worker separately — no machine-wide
  request budget, no breaker, no suppressed-duplicate accounting.
- The gateway exists to make that whole class of failure observable,
  coalesced and bounded at ONE chokepoint.

## 3. Architecture (frozen)

```text
Binance fapi public (WS + REST, keyless)
        |
        v
LIVE-DATA-GATEWAY-V1  (single process, 127.0.0.1 only)
        |
        +--> valuation worker        (post-cutover §9.3; sidecar first)
        +--> decision worker         (post-cutover §9.3, step 3 only)
        +--> dashboard               (post-cutover §9.3, step 1)
        +--> prospective recorder    (post-cutover, if adopted)
        +--> future collectors / MICROSTRUCTURE-DATA-MOAT-V1
```

- ONE gateway process; binds `127.0.0.1:<port>` ONLY (default port
  8792; `--port`; fail-closed if the port is taken). No LAN bind, no
  0.0.0.0, no IPv6 wildcard.
- Stack: Python 3.12 + `aiohttp` (already in `.venv`; measured MISSING:
  websockets/fastapi/uvicorn — so aiohttp is the frozen choice; NO new
  dependency may be added without a plan amendment).
- Code lives in `research/live_gateway/` inside THIS cycle's worktree
  only. The root checkout and every other worktree receive ZERO code
  changes from this cycle before the owner GO; after GO only the
  §9.3/§10 consumer integrations touch their own surfaces.
- Gateway runtime root: `results/live_data_gateway_v1/` inside this
  worktree (git-ignored via `results/`; never committed).
- The gateway is the ONLY process allowed to call Binance for surfaces
  it has adopted, AFTER §9.3 cutover of that surface. Before cutover
  it calls Binance in PARALLEL (sidecar) — its own budget, §5.

## 4. Binance market-data adapter (frozen surfaces)

Live (WebSocket, `wss://fstream.binance.com/stream?streams=…`):
1. `<symbol>@markPrice@1s` per symbol — payload carries markPrice,
   indexPrice, fundingRate, nextFundingTime, event time `E`. This ONE
   stream class serves D-requirements mark price (1), index price (2),
   current funding (3) and source timestamp (4).
2. Local receive timestamp (5) stamped on arrival; reconnect count (6)
   per connection; message-gap diagnostic (7): per-symbol monotonic
   check on `E` (a silent >10 s gap in a 1 s stream ⇒ symbol flagged
   GAP_DETECTED until the next message; WS streams carry no sequence
   number — the plan freezes wall-clock-gap diagnostics, honestly
   labeled as such, never claimed as venue sequencing).

REST (bootstrap / historical / metadata ONLY — D-list 8–11):
`/fapi/v1/klines`, `/futures/data/basis`, `/fapi/v1/fundingRate`,
`/fapi/v1/premiumIndex` (bootstrap + WS fallback detection),
`/fapi/v1/time`, `/fapi/v1/exchangeInfo` (tick size). Allowlist-frozen;
anything else is a hard error. REST polling may NOT replace a healthy
WS stream (poller emits zero requests while the stream is HEALTHY; a
degraded stream allows ONE bounded freshness probe per 30 s, counted
in §5 budget, and the payload stays labeled with its REST source).

Symbol universe (MVP): the union of (a) every symbol appearing as an
open position in the LATEST valuation marks (read-only tail of the
prospective-shadow mark ledgers), (b) the frozen decision candidate
sets published in the SHV1 worker config (20 ILLIQ + 13 PREMFADE
declared + 7 CARRY symbols), (c) a static config override list.
Refreshed hourly; subscription changes are logged as events. MVP cap
190 symbols = ONE WS connection (vendor-stated combined-stream limit
200/connection, mitigated by the 10-symbol margin; the limit is
re-MEASURED with a live probe at G1 and the measurement recorded in
G1 evidence — if the measured limit is lower, the cap shrinks to
measured-limit − 10). `--all-symbols` expansion is a future amendment,
not MVP.

## 5. Rate limiter + circuit breaker (machine-wide law inside gateway)

Shared limiter for ALL gateway upstream calls:
- canonical-request key = method + path + sorted params;
- request coalescing: concurrent identical requests share ONE inflight
  call (suppressed-duplicate counter incremented per suppressed hit);
- min-gap pacing between ANY two upstream REST calls (default 0.25 s);
- machine-wide budget: gateway-originated REST ≤ 60 requests/min AND
  tracked `X-MBX-USED-WEIGHT-1M` with a SOFT budget at 1200 (stop
  issuing new non-essential requests) and a HARD stop-issuing at 1800;
  the header measures IP-level weight INCLUDING foreign tenants of the
  shared egress IP (uncontrollable) — the 418/429 breaker below is the
  compensating control, and the budget is reported, never assumed to be
  solely ours;
- response-classification law (total, any status):
  (a) ANY response carrying `Retry-After` (any status class, incl.
  5xx/403) suppresses ALL retries to that surface until expiry — no
  retry inside an active Retry-After window, ever;
  (b) 418/429 ⇒ circuit breaker OPEN (below);
  (c) 5xx without Retry-After ⇒ bounded retry (≤2) without opening the
  ban breaker; 3 consecutive 5xx ⇒ DEGRADED;
  (d) non-retryable 4xx (403/451/404/400…) ⇒ FAIL FAST: distinct
  `non_retryable_status` event, zero retry-budget consumption, surface
  marked DEGRADED until a later success; never retried, never
  converted into data;
- exponential backoff with bounded jitter (base 2 s, factor 2, cap
  30 s, jitter ±20%), bounded attempts per logical call (≤4 transport
  retries), per-call timeout 20 s;
- HTTP 418/429 ⇒ circuit breaker OPEN for the REST surface:
  zero retries to that surface while open, `Retry-After` header AND
  body `banned until <ms epoch>` parsed (longer wins; if neither
  present, default open 120 s); breaker telemetry MUST expose: opened
  at, Retry-After, allowed-retry-at, the triggering request URL, and
  the running count of suppressed requests during the open window;
- single HALF_OPEN probe exactly when the window expires (one request,
  everything else still suppressed); success ⇒ RECOVERING → HEALTHY,
  failure ⇒ OPEN again with doubled window (cap 15 min);
- WS disconnect ⇒ DISCONNECTED state + reconnect with the same
  bounded-jitter backoff (cap 60 s); no REST fallback storm (§4).
- error history is append-only and NEVER truncated by restart.

Circuit states (per surface, reported verbatim): `HEALTHY`, `DEGRADED`,
`RATE_LIMITED`, `DISCONNECTED`, `STALE`, `GAP_DETECTED`, `RECOVERING`.

Rate-limit truth law: a ban/limit is reported as STATUS, never
converted into data (no zero-prices, no interpolation, no invented
marks). Consumers see `RATE_LIMITED` + `retry_allowed_at` and decide
their own fail-closed behavior.

## 6. Local data contract (API)

REST (all JSON, 127.0.0.1 only):
```text
GET /health                     liveness: pid, uptime, state summary
GET /v1/status                  full §11 observability snapshot
GET /v1/prices/latest           all subscribed symbols
GET /v1/prices/latest/{symbol}  one symbol (404 + reason if absent)
GET /v1/bars?symbol&interval&start&end[&limit]   klines (cache-first)
GET /v1/basis?pair&period&start&end[&limit]      basis (cache-first)
GET /v1/funding?symbol&start&end[&limit]         settled funding
GET /v1/metrics                 counters (§11)
WS   /ws/market?replay=<lastN>  §8 fan-out (replay ≤ ring size)
```

Every datum carries: `provider` (binance_fapi), `symbol`,
`value`(+field-specific fields), `provider_timestamp_utc`,
`received_at_utc`, `age_seconds`, `status`
(HEALTHY|STALE|GAP_DETECTED|RATE_LIMITED|DISCONNECTED|NOT_SUBSCRIBED),
`stale_reason` (null or one-line cause), `source`
(ws_channel e.g. `btcusdt@markPrice@1s`, or rest_endpoint+params),
`surface_state` (the FULL 7-state §5 surface value:
HEALTHY|DEGRADED|RATE_LIMITED|DISCONNECTED|STALE|GAP_DETECTED|
RECOVERING — per-datum status is the datum's usability, surface_state
is the upstream's health; the mapping is total: DEGRADED/RECOVERING
surfaces still serve fresh data as `status: HEALTHY` with
`surface_state` disclosing the transition, while RATE_LIMITED/
DISCONNECTED surfaces force the datum to their own status), and
`provenance` (`response_sha256` for REST-sourced, `ws_event` marker for
stream-sourced). Staleness thresholds [LEAD-FROZEN]: mark/index/funding
STALE after 10 s without a stream message (1 s stream), GAP_DETECTED
during a detected §4 gap, DISCONNECTED while the WS is down and no
message since > 10 s.

Last-known-value law: stale values ARE served (dashboard wants them)
but every stale payload carries `status: "STALE"` AND
`canonical_current: false`. Fresh values carry `canonical_current:
true`. Nothing may present an old price as current.

Historical endpoints return the RAW venue payload rows plus the
envelope (`cache_hit`, `fetched_at_utc`, `response_sha256`, `complete`
coverage flag). NO interpolation of gaps: a requested range with a
cache/paging gap returns `complete: false` + the gap list.

## 7. Cache + persistence (four separated stores)

```text
results/live_data_gateway_v1/
  raw/            immutable append-only observations (daily .jsonl.gz)
  cache/rest/     normalized REST cache, canonical-key files
  snapshot/       current snapshot (fsynced heartbeat + latest.json)
  events/         health/error/incident history (append-only .jsonl)
```

- atomic writes everywhere (tmp + fsync + rename); crash-safe resume:
  on restart the snapshot is reloaded, the monotonic §8 sequence
  continues from the persisted counter +1 (persisted BEFORE reuse), and
  per-day raw files are deduplicated by event digest on reload
  (restart never double-counts metrics);
- raw observations: append-only, gzipped daily, retention 14 days OR
  2 GiB total (whichever first; deletion of the OLDEST files only,
  each deletion logged to events/);
- REST cache: keyed by endpoint+params; a request whose exact
  canonical key exists and is `complete` is served from cache with
  `cache_hit: true` — it is NOT re-downloaded; TTLs [LEAD-FROZEN]:
  klines/basis/funding historical (closed ranges) = forever (immutable
  venue history; revalidation only on explicit `?refresh=1` which is
  itself counted in §5), premiumIndex 5 s, time 1 h, exchangeInfo 24 h;
  a re-download forced by §7 LRU eviction is a NORMAL §5-budgeted
  request (not a TTL violation), logged distinctly from `refresh=1`
  (`eviction_refetch` event);
- bounded disk: cache LRU-capped at 500 MiB (evictions logged);
- providers are NEVER mixed (single provider MVP; the store is
  provider-namespaced by design for future MICROSTRUCTURE-DATA-MOAT-V1);
- adjusted/raw representations never mix (Binance fapi klines are raw —
  documented; no adjustment layer exists in this gateway);
- no secrets (there are none — keyless), no runtime data in git.

## 8. Consumer fan-out

- every WS consumer gets its OWN bounded queue (default 2000 events);
- gateway NEVER blocks on a slow consumer: queue full ⇒ disconnect
  that consumer (`slow_consumer` event with reason + sequence), others
  unaffected;
- every outbound event carries `seq` (gateway-monotonic, gapless per
  connection lifetime) + `event_id` (content digest) so consumers
  deduplicate after reconnect;
- bounded replay ring (default last 10,000 events): on reconnect a
  consumer may request `replay=<lastN>` from the ring; ring misses
  (older than ring) are answered with `replay_truncated: true` so the
  consumer fails closed on its side;
- graceful shutdown: SIGTERM/SIGINT ⇒ stop accepting, flush queues
  (≤5 s), final heartbeat with `shutdown_clean: true`, exit 0.

## 9. Integration with PROSPECTIVE-SHADOW-V1 (three frozen steps)

### 9.1 STEP 1 — SIDECAR (this cycle's implementation phase)
- gateway runs in parallel; existing shadow/valuation workers and the
  dashboard are UNTOUCHED (zero code/process changes);
- gateway only observes (read-only tails of mark ledgers for §4 symbol
  discovery) and records canary data;
- nobody consumes the gateway yet; no behavior of any worker changes.

### 9.2 STEP 2 — DUAL RUN (canary; thresholds FROZEN HERE, before any
run; A7 audits this freeze)
New canary client processes (separate from all workers) compare:
A. Mark prices — gateway WS mark vs the valuation worker's REST
   premiumIndex source, same symbol, timestamp-aligned
   (|Δprovider_ts| ≤ 2 s). Per comparison record: absolute diff,
   relative diff (bps), ages, missingness. PASS requires, over a
   ≥24 h window covering ≥1000 aligned comparisons per watched
   symbol-class: ≥99% comparisons present, ≥99.9% of present
   comparisons with relative diff ≤ 5 bps, ZERO comparison with
   relative diff > 50 bps, and every missing side explained by a
   recorded gateway/upstream event.
B. Historical decision inputs — klines/basis/funding windows fetched
   (i) via gateway cache and (ii) directly from Binance by the canary,
   same endpoints, same params, same cutoffs, same PIT rules (SHV1
   data_feed semantics: completed-by-cutoff only). PASS requires:
   identical row counts, identical canonical timestamps, and digest
   equality OR exact numeric equality (rel tol 0, abs tol 1e-12) on
   every row; ANY mismatch ⇒ FAIL (no averaging, no exceptions).
   Scored PnL is NEVER read for equivalence.
Canary direct-Binance pacing law [FROZEN, A7 FND-1]: the canary's own
direct leg (ii) runs under the SAME §5-class discipline as the
gateway — min-gap 1.0 s between requests, ≤6 requests/min hard cap,
≤2 attempts per logical call, and ANY 418/429/Retry-After/banned-
until response ABORTS the whole direct leg for max(Retry-After,
banned-until, 120 s) with the abort recorded; zero worker
interference is verified by the live workers' own heartbeats staying
error-free-throughout on their own reads (their independent failures
are reported as environment, not blamed on the canary, but 418-class
abort telemetry MUST show the canary stopped issuing).
Canary fault-injection checklist (offline fixtures, MUST all pass):
reconnect; network loss; HTTP 418 with `Retry-After` + `banned until`
body; HTTP 429; Retry-After-ONLY fixture (header present, no
banned-until body, on a 429 and on a 5xx); non-retryable 403
fail-fast fixture; stale stream; duplicate WS messages; out-of-order
WS messages; gateway restart mid-stream; slow consumer; gateway
kill -9; WS stream death; corrupted REST cache file (detected ⇒
poisoned row quarantined + event, never served).
Dual-run runs ≥24 h with zero worker interference; report age/missingness.

### 9.3 STEP 3 — CUTOVER (FORBIDDEN before the owner types exactly
`GO LIVE DATA GATEWAY V1 CUTOVER`)
Order, one consumer at a time, each with its own tested rollback that
does NOT delete gateway evidence or historical marks:
1. Dashboard health/status reads gateway /v1/status (badge split §10).
2. Valuation worker mark price: fetch from gateway `/v1/prices/latest`
   (bulk). Frozen law: no direct Binance call for mark price after
   cutover; source name becomes `live_gateway_v1:/v1/prices/latest`
   recorded in the mark; historical marks untouched; the FIRST mark
   after cutover carries `cutover_metadata` (gateway seq, source
   timestamps); a missing/stale symbol still yields
   UNAVAILABLE_FAIL_CLOSED (a STALE last-known value may be displayed
   but is never canonical — `canonical_current: false` is honored);
   gateway down ⇒ valuation loop records its fetch error exactly as
   today (fail closed, no silent Binance fallback).
3. Decision worker historical fetches — ONLY after 9.2B PASS: same
   strategy inputs, same cutoffs, same event IDs, same schedules, same
   fill rules, same replay guard; no retroactive re-execution of any
   skipped event; no compensating BASISLV entry for 21/09; ANY
   difference fails closed as DATA_BLOCKED.
4. Prospective collectors / future cycles as separately authorized.
Rollback per step = flip that consumer back to its previous source
(config flag in ITS worktree), appended event, no evidence deletion.

## 10. Dashboard (minimal, post-GO step 1 only)

Split the single `DATA BLOCKED` chip into distinct truthful states:
`WORKER LIVE`, `DECISION OK`, `DECISION DATA BLOCKED`, `MARK PRICE OK`,
`MARK PRICE RATE LIMITED`, `MARK PRICE STALE`, `ACCOUNTING UNAVAILABLE`
(e.g. "Mark price: RATE LIMITED — last valid valuation 11:15, retry
allowed 12:06"). Top badge set: `LIVE` (worker + canonical price
fresh), `PARTIAL` (worker alive, one data surface failing), `STALE`
(mark too old), `DATA ERROR` (schema/read failure), `OFFLINE`
(heartbeat dead). NO new analytics, NO new charts, NO other dashboard
change. Live dashboard code is touched ONLY in cutover step 1 (post-GO).

## 11. Observability (heartbeat + metrics + status command)

Gateway heartbeat (`snapshot/heartbeat.json`, fsynced ≥ every 15 s):
pid, uptime_s, ws_state + reconnect_count + last_message_utc, source
latency (received_at − provider_ts percentiles over 5 min), stale
symbol list, REST calls per endpoint, request weight used, cache
hits/misses, suppressed duplicates, 418/429 counts, circuit state +
breaker reopen time, connected consumers, dropped slow consumers, disk
usage per §7 store, error-history tail. `GET /v1/status` returns the
same structure live.

Canonical status command (frozen; researchctl extension deliberately
NOT used to keep the shared control plane untouched):
```bash
cd /Users/hoangminhlong/my-quantitative/.worktrees/live-data-gateway-v1/integration
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m research.live_gateway status
```

## 12. Tests (frozen list; targeted; no full suite unless heavy lock FREE)

one-upstream-connection (WS subscription ≤190 symbols ⇒ exactly 1;
plus the G1 live re-measurement of the venue stream-per-connection
limit); request coalescing; cache hit (no re-download of a valid
canonical request); REST pagination correctness; WS reconnect;
duplicate message dedup; out-of-order message handling; timestamp
normalization (ms → ISO-Z); stale detection thresholds; Retry-After
parsing (header-only, `banned until` body-only, both, neither);
Retry-After honored on a 5xx; 403/451 non-retryable fail-fast (zero
retry-budget consumption, DEGRADED surface, distinct event); 418
breaker open + zero-retry window + suppress counter; 429 breaker;
half-open SINGLE probe; 5xx bounded retry; network timeout bounded;
consumer isolation (slow consumer disconnect does not delay others);
replay/dedup on reconnect; atomic persistence (kill -9 mid-write ⇒ no
partial file served); restart recovery (sequence continues, no metric
double-count); valuation missing-mark behavior (UNAVAILABLE_FAIL_CLOSED
path exercised against gateway payloads); dashboard PARTIAL state
mapping (pure function); decision historical equivalence (fixture
windows, digest law); eviction-triggered cache re-fetch accounting;
no-order surface (grep law: no order/broker/credential tokens);
no-credentials-in-artifacts (scan runtime tree after fixture runs).
Tests are offline-first (fixture transports); live network only where
explicitly labeled. NOT_RUN is reported as NOT_RUN.

## 13. macOS lifecycle (agent-independent)

Start:  `… -m research.live_gateway start [--port 8792]` (nohup-detached,
writes pid + heartbeat; refuses if already running).
Stop:   `… -m research.live_gateway stop` (SIGTERM, waits ≤10 s for
`shutdown_clean`, else reports unclean).
Status: §11 command (reads heartbeat; `STALE` if >30 s old).
Restart: stop → start; crash recovery = §7 resume law.
Logs: `results/live_data_gateway_v1/events/` + stdout log
`results/live_data_gateway_v1/gateway.log` (rotated at 10 MiB, keep 3).
A `LaunchAgent` TEMPLATE (plist) may be committed under
`research/live_gateway/launchagent/` but is NOT installed, NOT
enabled at login, NO sudo, NO credentials in the plist — installation
happens only on a future owner instruction. Gateway runs only while
the Mac is awake + networked; sleep/off simply means no live data
collected (streams resume on wake; gaps stay gaps — §6 truth law).

## 14. Gates / registration mechanics / GO

- G0: plan audit (A7 fresh-context, artifacts under
  `plans/audits_live_data_gateway_v1/`) → remediate → commit plan on
  main (root checkout, pathspec-only add) → register via
  `researchctl cycle register --cycle LIVE-DATA-GATEWAY-V1 --asset
  shared --lifecycle PLANNED_NOT_STARTED --budget-max 0 --go-phrase
  "GO LIVE DATA GATEWAY V1 CUTOVER" --branch
  orca/live-data-gateway-v1-integration --worktree
  .worktrees/live-data-gateway-v1/integration` → create worktree from
  the plan commit → lifecycle ACTIVE_LIGHT at first live heartbeat
  (researchctl cycle update).
- G1: implementation complete + §12 targeted tests PASS (commit).
- G2: sidecar ≥24 h stable (heartbeat continuity; breaker telemetry
  sane; zero impact on existing workers — verified by their own
  heartbeats being unaffected).
- G3: dual-run canary PASS at the §9.2 frozen thresholds (evidence
  JSON committed under `research/control/live_data_gateway_v1/canary/`).
- G4: A7 implementation/canary audit AUTHORIZED (fresh context).
- STOP: owner types exactly `GO LIVE DATA GATEWAY V1 CUTOVER`.
- G5 (post-GO): cutover steps §9.3 in order, one commit + rollback
  proof each; G6: A7 post-cutover audit.
Every gate reports command + exit code + SHA + evidence paths.

## 15. Boundaries (hard stops)

No push; no merge to main without owner authorization; no reset of
owner changes (`.zcode/`, `research/control/SANDBOX-OVERFIT-3ASSETS/`,
dashboard app, ACTIVE_CYCLES projection, live ledgers, valuation
marks); no `git add -A`; no killing foreign workers; no historical
ledger or old-mark edits; no S1; no scored research; no
paper/testnet/live orders; no broker account; no data purchase; no
strategy change; no stale mark as canonical current; no Binance retry
inside an active Retry-After window; no cutover before GO.

## 16. Artifacts / evidence paths

```text
plans/PLAN_live_data_gateway_v1.md                     (this file, main)
plans/audits_live_data_gateway_v1/a7_plan_r1.json      (G0)
.worktrees/live-data-gateway-v1/integration/research/live_gateway/   (code)
  …/research/control/live_data_gateway_v1/canary/*.json (G3 evidence)
  …/results/live_data_gateway_v1/                      (runtime, git-ignored)
handoffs: research/control/live_data_gateway_v1/handoff_*.json
```
