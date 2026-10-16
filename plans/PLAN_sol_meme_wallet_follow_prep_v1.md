# PLAN — SOL-MEME-WALLET-FOLLOW-PREP-V1 (Solana new-token wallet-follow: data feasibility + specs + read-only core, ZERO scored)

- cycle_id: SOL-MEME-WALLET-FOLLOW-PREP-V1 · asset: crypto · budget 0/0
  (ZERO scored cells — historical net-PnL strategy comparison is scored
  computation in this repo and is NOT authorized in this cycle) ·
  registered 2026-10-16.
- owner authority 2026-10-16 (this chat): explicit owner authorization to
  research a strategy on newly launched Solana memecoins — following wallets
  with large buys / good track records, and testing whether a follower
  entering/exiting with delay, size and real costs can be profitable. Owner
  explicitly ordered: plan AND execute the authorized parts; do not stop at
  the plan; a survivor is NOT required.
- This cycle is **PREP/FEASIBILITY + READ-ONLY CORE**, not scored execution.
  It ends in a report + NEXT_GATE_PACKET. A successor scored cycle (if any)
  requires its own owner instruction, its own plan, its own data/cost freeze,
  non-vacuous dry-run and independent A7 — none of which are granted here.
- **NO GO phrase is registered** (none can exist for a cycle with no scored
  phase). **NO PUSH** (owner explicit 2026-10-16; supersedes the standing
  push delegation for the duration of this cycle). No merge, no rebase, no
  history rewrite.

## Hard boundaries (all lanes)

- $0. No account creation, no terms acceptance, no subscription, no paid API
  activation, no quota evasion. Free ≠ authorized: every source carries
  `DOCUMENTED_CANDIDATE → CANDIDATE_NOT_AUTHORIZED → AUTHORIZED_INTERNAL_RESEARCH
  | UNAVAILABLE_FAIL_CLOSED | REJECTED_LICENSE` status with evidence URL+date.
- Read public docs, download free samples, and use ONLY pre-existing
  entitlements whose scope is verified free-of-charge. Anything needing new
  rights → record as a specific owner request in NEXT_GATE_PACKET, do not buy.
- No private keys, no seed phrases, no signing, no `sendTransaction` /
  `sendBundle` / any broadcast path, no claim/airdrop/token-link interaction.
  On-chain data and off-chain metadata are untrusted input — never executed.
- No scored/OOS computation, no historical net-PnL strategy comparison, no
  survivor claims. Signal-side census, data audit, synthetic execution tests
  and protocol/simulation development ARE authorized.
- Shadow data collection: only after spec+tests+readiness PASS, horizon ≤7
  days, verified free quota, and NEVER auto-started as a long-lived daemon in
  this session. If no durable runtime exists: deliver start/stop commands +
  activation packet and claim `NOT_ACTIVE`.
- Never touch frozen/TERMINAL cycles, other cycles' worktrees/ledgers/
  registries, running futures work (FUTURES-PAH-V1, WEATHER-TEMP-PROB-V1),
  or `.my-quantitative-data/` (FOREIGN content, never read).
- Missing evidence = `NOT_RUN` / `UNAVAILABLE_FAIL_CLOSED`, never inferred
  PASS. Every gate verdict carries command, exit code, SHA, tree state.

## Core question (three-way separation — never conflate)

After a wallet is selected USING ONLY KNOWN HISTORY buys a new token, can a
follower with delay, size and real costs enter and exit profitably?

1. Source wallet has profit (accounting fact about the wallet).
2. Wallet signal is predictive (statistical fact about future tokens).
3. A copier is executable and profitable net of costs (execution fact).

1 and 2 are NOT evidence for 3. This cycle builds the machinery and the
specs for all three and runs NONE of the scored comparison.

## Data plane

- Bulk bytes live OUTSIDE git under
  `~/.my-quantitative-data/sol-meme-wfp-v1/<source_id>/…` with per-source
  `manifest.json` (sha256, size, retrieval URL, retrieval UTC, license URL +
  verbatim snippet, attribution). Only manifests/code/reports enter git.
- Politeness: light fetches only (≤10 MB per source per lane run,
  sequential, identified UA, back off on 429/5xx). Anything larger/slower
  than ~2 minutes takes the machine-wide heavy lock via
  `governance.heavy_lock.acquire(...)`; refusal = `NOT_RUN_RESOURCE_CONFLICT`.
- **PROBE BUDGET (committed before any RPC probing)**: public mainnet-beta
  JSON-RPC only; ≤400 requests total across the whole cycle; ≤20 MB
  transferred; ≤30 min wall clock; request shapes limited to
  `getHealth / getVersion / getBlock / getTransaction /
  getSignaturesForAddress / getAccountInfo` on a ≤3 mint sample.
  Any need beyond this budget → STOP and record in NEXT_GATE_PACKET.
- 24/48h replay is NOT multi-year history. Tokens existing today are NOT the
  historical universe. Price candles are NOT sufficient to replay execution.

## Universe & event law (frozen by spec, implemented by core)

- Token identity = mint address (base58), never ticker.
- "New" = per-token creation/first-trade time measured on-chain; venue =
  launch program (e.g. pump.fun bonding curve) + migration target pool
  program version, pinned by program IDs measured from bytes.
- Inclusion/exclusion rules must handle: never-graduated, dead, rugged,
  liquidity-removed, unsellable (freeze authority / transfer-hook), wrapped
  SOL, decimals, protocol fees, USD conversion point-in-time.
- Transaction ↔ economic action reconciliation: aggregator multi-hop = ONE
  action; fee-payer ≠ trader unless attribution proven; transfer ≠ buy/sell;
  LP withdrawal ≠ wallet sell.
- Sample completeness report + missingness ledger are mandatory deliverables.

## Wallet selection law (no lookahead)

- No current "smart money" list applied backwards. Selection uses a rolling
  historical window with data available strictly BEFORE the selection
  timestamp; refresh schedule + eligibility rules frozen in spec.
- Separate: large size relative to pool liquidity ≠ rich wallet ≠ good
  realized performance ≠ skilled. Insider/deployer/sniper/MM behavior is
  labeled, not called skill.
- Funding links / transfer graphs / synchronized behavior → same-owner
  clusters are inference with confidence levels, never certain identity.
- Performance accounting includes initial inventory, transfers, airdrops,
  open positions, fees, and worthless/illiquid marks; missing cost basis is
  UNKNOWN, never 0.

## Strategy concepts (≤3; wave-1 config budget ≤12 INCLUDING baselines)

- A: follow a single eligible wallet. B: consensus of N seemingly-independent
  eligible wallets. C: conditional on liquidity/exitability gates.
- Each concept must define: null, baseline, mechanism, entry/exit, cooldown,
  position cap, time stop, invalidation, kill criteria.
- Every change to wallet rule, delay, threshold, hold or exit = a new
  variant → ledger row. 12-config wave list is frozen in
  STRATEGY_CONCEPTS.md as SPEC ONLY (no scored run in this cycle).
- Controls: matched random wallets; randomized timing on the same valid
  universe; price/volume/liquidity baseline without wallet identity.
  Controls get no favorable population or execution assumptions.

## Execution realism law

Record separately per event: chain slot/order/blockTime;
provider_received_at; decision_at; quote_requested_at/quote_received_at;
hypothetical submission/landing time. Historical chain time does NOT prove
when our system would have known → absent historical receive timestamps,
latency is `MODELED_LATENCY` with a locked, published grid (small).
- Entry happens AFTER signal + delay; exit after observing the source sell;
  never front-run the source's own impact. Follower never buys at the
  whale's price.
- Cost items enumerated separately: DEX/protocol/platform fees; network/
  priority fees and tips if modeled; price impact + slippage; failed/retried
  transactions; token transfer fees/extensions; account creation/rent cash
  flows (refundable rent flagged); data/provider costs kept OUT of execution
  costs.
- Four evidence tiers, never conflated: historical pool-state replay;
  current quote; modeled fill; live executable evidence. A current Jupiter
  quote proves nothing about historical fills.
- Model must include partial/no exit, liquidity removal, migration, stale
  state, failed swap, adverse ordering/MEV scenarios; unsellable cases stay
  in the sample; no guaranteed stop-loss assumption.

## Token risk & structural data

Mint/freeze authority, Token vs Token-2022, transfer-fee, transfer-hook,
and other rights that affect tradability are checked and recorded.
Top-holder concentration excludes/marks pools, vaults, burn addresses and
program-owned accounts; top holders are not assumed independent buyers.

## Read-only harness + shadow (build, do not run long-lived)

Discovery/ingestion → append-only raw event journal → dedupe/reconnect/gap
detection/reconciliation → program-version-aware parsers → wallet eligibility
snapshots → signal engine (spec-level) → quote observer (if rights allow) →
shadow position state machine → cost/latency simulator → risk/no-trade gates
→ monitoring + deterministic replay. No signer anywhere; quote/simulation
must not auto-escalate to execution.

## Lanes (worktree per agent; integration is controller-only)

- BASE_SHA: measured at bootstrap (recorded in registry + dispatch packets).
- L1 `lane-sources` — SOURCE_MATRIX + DATA_COVERAGE_AND_COMPLETENESS (web
  evidence only, no bulk): Solana RPC/archive reality, Helius, Bitquery,
  Birdeye, Jupiter, plus candidates found during research; per endpoint:
  historical start/end + retention, token creation/swaps/transfers/balance
  changes, pool creation/migration + liquidity + program versions, wallet
  attribution, slot/order/commitment/finality, provider receive time,
  historical pool/account state, failed transactions, pagination/rate
  limits/completeness/license, free/owned/paid/account-required, cost +
  storage/compute estimate.
- L2 `lane-specs` — UNIVERSE_AND_WALLET_SELECTION_SPEC + STRATEGY_CONCEPTS +
  EXECUTION_LATENCY_COST_SPEC (writing only; cross-references L1 rows by ID;
  unresolved facts marked NOT_RUN, not guessed).
- L3 `lane-core` (integration worktree, after L1/L2 land) —
  `research/solmeme/` + `tests/`: journal schema, dedupe/reconnect/gap,
  synthetic-fixture parsers (bonding-curve buy/sell, pool swap multi-hop
  dedupe, trader attribution, Token-2022 transfer-fee/hook detection),
  eligibility snapshot module, shadow position state machine, cost/latency
  simulator with MODELED_LATENCY grid, no-trade gates, deterministic replay
  harness, NO_BROADCAST_PROOF tests. Hand-computed fixtures; no production
  outcomes in tests.
- L4 `lane-verify` — independent verifier, fresh context, dispatched LAST
  against integration HEAD; audit-only namespace; rebuilds attribution from
  raw synthetic transactions, checks selection cutoff, survivorship,
  entry-after-source-trade ordering, migration/fees/decimals, failed-exit
  accounting, prefix replay / future mutation, trial accounting,
  no-signer/no-broadcast; verdict per claim.

## Gates

- G1 plan+registry committed, worktrees+manifests live (controller).
- G2 L1/L2 handoffs valid, integrated, cross-references resolve.
- G3 core tests PASS (exact commands recorded); `pytest -k solmeme` targeted.
- G4 probe (if network available) inside committed budget; results appended
  as MEASURED appendix; if sandbox blocks network → `NOT_RUN_NETWORK`.
- G5 NO_BROADCAST_PROOF: static scan (no send/broadcast/signer tokens in
  research/solmeme/) + test evidence; quote-observer escalation guard test.
- G6 verifier verdict recorded (PASS / PASS_WITH_FINDINGS / FAIL).
- G7 next-gate packet + REPORT_VI + registry head sync; zero scored cells.

## Terminal outcomes

Legal terminal verdicts include `PREP_COMPLETE_PENDING_OWNER_SCORED_DECISION`,
`PREP_COMPLETE_BLOCKED_DATA` (data authority insufficient for the question),
`PREP_COMPLETE_NEGATIVE_FEASIBILITY`. A negative/no-survivor outcome is a
valid, expected result. REPORT_VI answers the owner's six questions
explicitly, including whether a scored cycle SHOULD be opened or not.

## Deliverables

CAMPAIGN_PLAN (this file) · SOURCE_MATRIX · DATA_COVERAGE_AND_COMPLETENESS ·
UNIVERSE_AND_WALLET_SELECTION_SPEC · STRATEGY_CONCEPTS ·
EXECUTION_LATENCY_COST_SPEC · code+tests (`research/solmeme/`, `tests/`) ·
event/trial ledgers (0 scored rows) · NO_BROADCAST_PROOF · VERIFIER_REPORT ·
NEXT_GATE_PACKET · REPORT_VI — all under
`research/control/SOL-MEME-WALLET-FOLLOW-PREP-V1/` on the integration branch
except the plan file itself.
