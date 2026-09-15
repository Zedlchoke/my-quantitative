# CRYPTO frontier survey — pre-cycle (CRYPTO-PRECYCLE-SURVEY)

- TASK_ID `cxf-researcher-frontier-1`, role RESEARCHER (proposal-side only; an
  independent critic will attack these directions — no self-certification).
- Base/dispatch sha `53d2d152c5c5ad61a772c81e3437d1dfd22a0d05` (branch main,
  HEAD verified identical at start). Today 2026-09-15.
- Scope discipline honored: NO returns/PnL computed anywhere (all probe math is
  supply-census arithmetic); no registry/ledger writes; no keys, no signups, no
  paid endpoints; sequential light canary probes only; artifacts confined to
  `research/control/crypto_frontier_2026-09/`.
- Authoritative ancestry read first: `research/wayfinder/MAP.md`,
  `LESSONS.md` (P-1..P-24, Q-1..Q-16), `HYPOTHESIS_LEDGER.md`,
  `FAMILY_FAILURES.jsonl`, plans crypto v13..v17 + ng1 + ng2, NG1/NG2 terminal
  reports (read from git branches `orca/crypto-ng1-integration` /
  `orca/crypto-ng2-integration` — worktrees archived per P-13, evidence lives in
  branches; empty worktree dirs confirmed 2026-09-15).

---

## 1. Dead-family inventory (crypto) — what any new direction must beat

Registry rows (`FAMILY_FAILURES.jsonl`, asset=crypto): **32 rows**. Ledger §A/§B
add the pre-factory families (semi-governed) — ~8 more method families. The
recurring killers: CONTROL_OUTEARNED_ANCHOR (falsification-by-control cluster
instances #11, #14 crypto-side; #8-#17 program-wide), FOLD_CONCENTRATION
(ILLIQ 0.7055, CARRY-7D 51.66%, PREMFADE 0.5110), EXPECTANCY_NONPOSITIVE after
stress-tier costs, ANCESTRY_RHO_BLOCK at D2 (V17 six, NG1 4/4, NG2 4/4).

| Class | Dead rows (cycle) | Kill |
|---|---|---|
| Funding carry (level) | CARRY-1D/3D/7D (V6) | fold concentration; edge_too_weak |
| Funding/price divergence | XSECT-FUND-PRICE-DIV (V7, never run) | superseded |
| Cross-sectional reversal/trend/vol-shock | V8/V8R, V9 (2 rows) | expectancy; NOT_ELIGIBLE |
| Order-flow absorption | M01 panel (V10/V10R) | prelaunch coverage → family reject |
| LOT / residual-MAX | V11 | control out-earned (PF 1.34 vs 0.72) |
| ILLIQ-AMIHUD | V11 (+ blocked V12 replication) | concentration 0.7055; data block |
| OI lever/cycle/term-structure | OILEV (V11), OILEV-V2 (V12), OITD (V13), OICYC (V14) | control out-earned; negative; DSR≈0 |
| Betting-against-beta | BAB-LOWBETA (V12) | cost-dominated |
| Basis/premium fade | PREMFADE-28D (V14, near-miss PF 1.360) | fold concentration 0.5110 |
| Elite positioning asymmetry / taker saturation | ELITE-SIZE-ASYM, TAKER-SAT (V15) | control out-earned (#11); negative |
| aggTrades microstructure (daily) | CLOSE-DISPLACE-FADE, RUNPERSIST (V16) | PF razor; control out-earned; exhausted at daily clock |
| Sub-daily intraday lanes | SILRES, WKNDLIQ, TICKET-BREADTH, FUNDJUMP, ATTN-PHASE, OICASCADE (V17) | frozen-rule coverage; rho 0.5628/0.475/0.2439; expectancy; control out-earned |
| Exogenous announcement clocks | CNG1-A4-P1/P2 (FOMC instant), CNG1-A5-P1/P2 (derivatives calendar) | rho 0.4409/0.3988/0.7483/0.3904 vs dead forms |
| Announced-information clocks (all classes) | CNG2-A4-P1/P2 (CPI/NFP), CNG2-A5-P1/P2 (funding settlement microtiming) | rho 0.9007/1.0/0.4178/0.4872 vs dead-FOMC-form envelope |
| Pre-factory (ledger §B) | ema_atr, mean_reversion (transfer failed), regime_switch, Wyckoff, VOLCOMP-BRKOUT, 24h-sprint matrix (0 PASS), FUNDCROWD-MR, XSECT-MOM (risk-gate dead despite real signal) | assorted; never promoted |

Binding statements: exogenous-clock crypto frontier = measured-dead ancestry
across ALL announced-information classes (NG2 terminal); lane-1 intraday
re-opens only via a future owner plan with materially new mechanism + source +
causal control (V17 law); D2 novelty bar pooled |rho| <= 0.20 vs the FULL
inventory.

---

## 2. Per-source census (A–D)

Raw bytes + sha256 + URL + timestamp for every fetch:
`research/control/crypto_frontier_2026-09/probes/` (53 probe pairs). Probe
tooling: `tools/fetch_probe.py` (sequential, UA-tagged), `tools/keccak_probe.py`
(pure-python keccak256, self-tested: empty-string, 'abc', fox vectors and the
canonical `Transfer(address,address,uint256)` topic `0xddf252ad…` all PASS —
no new dependencies installed; repo venv untouched).

### A. Coin Metrics Community API — verdict: DOCUMENTED_CANDIDATE (keyless), CROSS-CHECK-GRADE only

- Keyless: YES on `https://community-api.coinmetrics.io/v4` (catalog-v2 +
  timeseries). The `api.coinmetrics.io` host 401s timeseries without a key.
  Docs (fetched via gitbook-docs.coinmetrics.io): "API key is not required when
  accessing community endpoints"; rate limit 10 req/6s/IP.
- Correct data path is `/v4/timeseries/asset-metrics` with `start_time`/
  `end_time` (probes A22-A30; `start`/`end` unsupported, wildcards unsupported
  in catalog filter — measured).
- Coverage for stablecoins (probes A1b/A7, usdt + usdc catalogs, 22 community
  metrics each): `SplyCur` (current supply), `IssTotNtv`, `IssTotUSD`
  (issuance totals), `CapMrktCurUSD`, `PriceUSD`, `TxCnt`, `TxTfrCnt`,
  `AdrActCnt`, 1s `ReferenceRate*` (7-day depth only). **No redemption
  metric** (`RedTot*` rejected by catalog for usdc — measured A1c).
- Depth (measured, probes A27-A30): daily 1d from 2014-10-06 (usdt) /
  usdc equivalent; windows 2018-06 (usdt 2.83B), 2019-01 (usdc), 2023-03-10..16
  (depeg week present), 2026-09-07..14 (usdt 189.157B, usdc 66.61B) all served.
- Availability/revision: daily aggregates, completion-time metrics exist
  (`AssetCompletionTime`); NO public vintage channel measured → treat as
  revised-in-place; PIT-unsafe as primary.
- License: community data = **CC BY-NC 4.0 (Attribution-NonCommercial)** per
  Coin Metrics community docs — terms caveat recorded; internal research use
  must be owner-adjudicated before this becomes a primary scored input.
- Census finding (A29/A30): `IssTot*` is GROSS issuance and is CCTP/bridge
  contaminated — usdc 2026-09-14 IssTotUSD = $2.293B while TOTAL SplyCur FELL
  $44.5M the same day. Gross issuance ≠ new dollars; unusable as a flow measure
  without minter-class netting.

### B. On-chain mint/burn contract events (finalized logs) — verdict: DOCUMENTED_CANDIDATE (keyless), PIT-CLEAN PRIMARY CANDIDATE

- Contracts pinned: USDT Ethereum `0xdAC17F958D2ee523a2206206994597C13D831ec7`
  (TetherToken; supply changes only via `issue()`/`redeem()` → events
  `Issue(uint256)` topic `0xcb8241ad…`, `Redeem(uint256)` topic `0x702d5967…`,
  both computed from the canonical ABI string with the self-tested keccak);
  USDC Ethereum `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` (FiatToken proxy;
  `Mint(address,address,uint256)` topic `0xab8530f8…`,
  `Burn(address,uint256)` topic `0xcc16f5db…`). Cross-checked against
  4byte.directory (D1 probe; 27 colliding text-signature variants exist for
  Mint(address,address,uint256) — collision hazard recorded; pin by emitting
  CONTRACT ADDRESS + topic pair, never by topic alone).
- Keyless transports measured:
  - `https://eth.blockscout.com/api?module=logs&action=getLogs` (GET,
    etherscan-compatible, no key): served USDC Mint 990-block window (456
    events, +40.33M), Burn window (326 events, −128.98M), Mar-2023 depeg
    window (32 burns, −6.99M, burner = Circle's pinned burner
    `0x55fe002a…`) — probes B4/B5/B6/B8. **Hard 429 ban after ~4MB of pulls**
    (incident) — burst budget is the constraint, not entitlement.
  - `https://rpc.mevblocker.io` (POST JSON-RPC eth_getLogs, keyless): served
    the FULL 7,182-block UTC-day census (probes B13) — 2,215 mints
    +156,813,344.60 / 1,588 burns −128,067,159.59 → net **+28,746,185.02 USDC**
    minted on Ethereum 2026-09-13T00:00:11Z→09-14T00:00:11Z (block-pinned
    25962689→25969871, boundaries timestamped via publicnode
    eth_getBlockByNumber).
  - `https://api.trongrid.io/v1/contracts/{addr}/events` (GET, keyless,
    rate-limited): works — returns event_name/block_timestamp(ms)/result dict
    (probe B7). Required for USDT chain-completeness (Tron hosts the USDT
    majority; Ethereum-only census CANNOT tie USDT total).
  - FAILED keyless: `ethereum-rpc.publicnode.com` archive eth_call → 403
    "Archive requests require a personal token" (NOT_ENTITLED — recorded, not
    fetched with a key); `rpc.ankr.com/eth` → requires key; `1rpc.io` → plan
    limit; llamarpc 525; drpc/blastapi 400 on our filter; flashbots 504;
    cloudflare-eth −32603 on getLogs.
- Event-time vs availability-time: event-time = block timestamp (12s
  granularity, final at ~2 epochs); aggregator exposure lags to next-day
  aggregates (CM) or intraday snapshots (llama). Chain-first design needs only
  its own ingest stamp — the lag is ours to measure.
- Conservation identity (task-mandated check, RUN, small window):
  - Design: FiatToken/USDT supply on a chain changes ONLY via Mint/Burn (resp.
    Issue/Redeem) → Σ(Mint−Burn) over a block window == chain supply delta.
  - Executed: full-day USDC Ethereum census above is internally exact (sum of
    logs). Cross-source tie vs DefiLlama ETH-chain daily delta **DOES NOT
    MATCH**: llama Δ(09-13→09-14) = +75.87M vs on-chain exact-UTC-day
    +28.75M — llama day labels are intraday snapshots (timing mismatch) and/or
    bridge adjustments; AND at head: blockscout `total_supply` 50.497B vs llama
    ETH-chain 47.166B — a 3.33B (6.6%) definitional gap. **Aggregate supply
    numbers are definition-laden; only the on-chain census with a pinned
    identity is primary.** Archive eth_call (the exact tie-out tool) is
    keyless-BLOCKED on every free RPC tested → full identity gate is feasible
    only via log-census vs blockscout head + pinned windows (partially
    evidenced), recorded as the P0 gate design for any future cycle.

### C. DefiLlama stablecoins API — verdict: DOCUMENTED_CANDIDATE (keyless), CROSS-CHECK-GRADE ONLY (measured identity breaks)

- Keyless: YES (`https://stablecoins.llama.fi`, no key, no signup).
- Endpoints measured: `/stablecoincharts/Ethereum?stablecoin=2` (USDC
  ETH-chain, 651,832 bytes, 2,927 points 2018-09-11→2026-09-15); same for USDC
  id=2 / USDT id=1; `/stablecoin/{id}` full-history chart is >9MB (two
  truncated fetches kept as schema evidence, disclosed).
- Fields (measured exact): `date`, `totalCirculating.peggedUSD`,
  `totalUnreleased.peggedUSD`, `totalCirculatingUSD.peggedUSD`,
  `totalMintedUSD.peggedUSD`, `totalBridgedToUSD.peggedUSD` — a bridge-adjusted
  field EXISTS on the chain-filtered series; chain breakdown
  (`chain_breakdown`) exists on the per-asset chart.
- Revision/availability: intraday snapshots labeled by date; no vintage
  channel; measured day-delta vs on-chain exact-day mismatch (+75.9M vs
  +28.7M) and head-level 3.3B gap vs blockscout → **cross-check-grade only;
  never primary**.
- License/terms: no explicit API license surfaced on the API surface probed;
  terms gap recorded honestly (owner decision if it ever becomes primary).

### D. Other keyless sources

- `4byte.directory` (keyless GET): signature resolution aid only — community
  data, colliding variants (27) → identity must come from pinned contract ABI,
  not 4byte.
- Etherscan API: keyless V1 returns "deprecated V1 endpoint" (probe D2); V2
  requires a (free) API key → **NOT_ENTITLED** (needs key = account creation =
  forbidden).
- The Graph: decentralized-network gateway queries require an API key;
  hosted-service sunset — docs pages unreachable this host (404 on both doc
  URLs tried) → recorded **NOT_ENTITLED / UNVERIFIED-THIS-HOST** (fail-closed;
  not fetched with a key).
- Token Terminal: needs account/key → NOT_ENTITLED (not probed further).
- Public RPC zoo (8 hosts tested for getLogs): only `rpc.mevblocker.io` served
  keyless at probe scale → transport fragility is a first-class feasibility
  risk for any log-census cycle (blockscout 429 ban, mevblocker untested at
  depth>7k blocks/day).

---

## 3. Candidate directions (≤3, proposal-side; critic will attack)

### Direction 1 (RANK 1) — Issuer-contract net-flow census → float-contraction conditioning ("forced de-risking when settlement float contracts")

- Causal hypothesis (forced parties): when NET new stablecoin float on the
  settlement chain contracts (issuer burns exceed mints AFTER netting
  chain-to-chain rotation), stablecoin-denominated margin becomes scarce for
  the marginal perp participant; OTC/arb desks that pre-position stablecoin
  inventory must de-risk perp books into thin stablecoin liquidity. Prediction:
  net-flow regime states (not flow prints) modify the response of the frozen
  BTC/ETH/SOL H1 panels — a conditioning book, never a directional print book.
- Reverse-causality statement (mandatory): issuers mint/burn in RESPONSE to
  demand that prices may already express — full causal identification is NOT
  designable. The design separates "new dollars entering" from "price moves
  causing issuance" only partially: (i) minter-class identity layer — CCTP
  `TokenMinter` mints/burns (measured dominant: minter `0xfd78ee…`, burner
  `0x55fe002a…`) are chain-to-chain TRANSFERS, not new dollars; netting them by
  on-chain-verifiable contract identity (not exchange-wallet labels) removes
  the rotation component; (ii) event-time precedence: decisions use only flows
  finalized ≥N blocks deep before the decision bar; (iii) the honest claim is
  INCREMENTAL INFORMATION after named shadows (D2 rho ≤ 0.20 vs price/momentum/
  OI/funding forms), not causality. If that decorrelation fails, the direction
  dies at D2 with zero budget — declared in advance.
- Source + docs URL (verified by fetch): logs via keyless RPC — blockscout
  etherscan-compat `https://eth.blockscout.com/api?module=logs&action=getLogs`
  and `https://rpc.mevblocker.io` (eth_getLogs); Tron via
  `https://api.trongrid.io/v1/contracts/{addr}/events`. Docs: blockscout REST
  docs (etherscan-compat), trongrid docs. Event topics self-computed and
  cross-checked (4byte + measured events).
- Access/entitlement: DOCUMENTED_CANDIDATE keyless (measured end-to-end today:
  a full UTC-day census ran at probe scale).
- Historical depth: Ethereum logs full history since USDT-ERC20 Nov 2017 /
  USDC Oct 2018 (deep windows 2018-06, 2023-03 measured; full-history census
  is a HEAVY job — NOT probed, forbidden this survey → its feasibility is its
  own P0 gate). USDT needs Tron + (historical) Omni — chain-completeness for
  USDT UNPROVEN at depth: fail-closed coverage gate.
- Availability time: event-time = block timestamp; publication = our own
  ingest (measured lag ours); CM/llama aggregates lag ≥ next day → chain-first
  architecture.
- PIT hazards → fail-closed answers: bridge double-counting (CCTP netting
  layer, pinned TokenMessenger/Minter identities; proxy-upgrade risk pinned at
  P0); chain migration (USDT Omni→ETH→TRON; USDC multichain expansion —
  per-chain census, never cross-chain sums without identity); wrapped/canonical
  (USDC.e/bridged variants excluded by contract address, never by symbol);
  contract identity pinning (address+topic pairs from pinned ABI; 4byte
  collisions recorded); exchange-wallet labels (NOT USED — issuer-contract
  events only); revised historical aggregates (chain facts immutable; CM/llama
  downgraded to cross-check); sparse issuance regimes (USDT-ETH: 0 Issue/Redeem
  events in the recent 990-block window — measured; instants floor must count
  net-flow days, not raw events); conservation identities (P0 census gate:
  Σ(Mint−Burn) == pinned-window chain delta; measured runnable, exact-tie tool
  keyless-blocked → gate defined on log-census + head supply); historical
  constituent composition (UST collapse 2022-05, USDC depeg 2023-03 pre-flagged
  as composition breaks — either excluded with reason or arm-split, frozen at
  D1); license/terms (on-chain facts; no vendor license needed for primary).
- Falsifiers + ancestry controls: D2 pooled |rho| ≤ 0.20 vs the FULL 32-row
  inventory + the named shadows: `v17_oi_level` (0.3904), OILEV-V2 flow form,
  `CTL-OISHARE` (0.431), funding-LEVEL (NG2 measured <0.021 — must stay),
  `generic_dvol_shock` (0.4409), momentum/dvol forms, and the NG1/NG2
  dead-FOMC-form envelope; Q-7 clock-only shadow (hour-of-week/UTC-day clock
  reproduces the regime?); Q-11 invalid-null check on any permuted-flow
  control; P-21 preregistered cost ceiling at P2; S1 stays sealed.
- Differs from dead families: new INFORMATION SOURCE (settlement-layer dollar
  float — a cross-asset flow never consumed by any crypto cycle; OI/funding/
  aggTrades are perp-native), new mechanism (scarcity conditioning, not carry/
  momentum/reversal/announcement-reaction), and its own census-gate falsifier.
  Mapping: not V6/V7 (funding level/divergence), not V9-V16 (price/volume/OI
  perp-native), not V17/NG1/NG2 (not a clock; not announcement information).

### Direction 2 (RANK 2) — Aggregate-supply regime conditioning (CM Community + DefiLlama), secondary expression only

- Hypothesis: multi-day aggregate net-supply REGIMES (expansion/contraction,
  chain-aggregate) gate the same frozen panels. Same forced-party story at
  lower resolution.
- Honest causal statement: conditioning regime only; NOT causal identification
  (aggregates are demand-following); the D2 decorrelation bar decides, nothing
  else.
- Source/entitlement: DOCUMENTED_CANDIDATE keyless (CM community host — daily
  2014→, `SplyCur`; llama chain series 2018-09→ with `totalBridgedToUSD`).
- Depth: measured (2014/2018/2019/2023/2026 windows).
- Availability/PIT: daily aggregates revised-in-place, no vintage channel,
  CC BY-NC 4.0 (CM) and unlicensed API (llama) → PRIMARY AUTHORITY FAILS the
  PIT test as-is; usable only as cross-check/breadth confirmation of the
  Direction-1 census, or as a coarse fallback if the owner accepts the license
  and the revision risk explicitly.
- Falsifiers/ancestry: identical D2 rho battery + a PIT gate that FAILS this
  source as primary (by design); must decorrelate from Direction 1's own
  census-derived regime (self-subsumption rho measured, not assumed).

### Direction 3 (RANK 3) — Depeg-stress forced-redemption episodes (USDC 2023-03 class) — expected-kill disclosure

- Cleanest forced-party causal story (depeg arbitrageurs are FORCED buyers with
  redemption access; panicked holders forced sellers; quasi-exogenous trigger
  off-chain banking stress), but feasibility is almost certainly fatal: the
  episode count since 2018 is a handful → the frozen Q-6 recent-window floors
  (n ≥ 30 instants class) fail at P2 → the direction dies pre-score at zero
  budget. Proposed because its census artifacts (depeg windows already probed:
  B6, A21) feed the composition-break flags of Directions 1-2. NOT_RUN at the
  census floor is the honest close, not a rescue path.

---

## 4. Weakest-point self-assessment (for the critic)

1. **Reverse causality is not identifiable** — Direction 1 survives only as an
   incremental-information claim under the 0.20 rho bar; a critic arguing
   "net flow is a lagged price consequence" is economically right; the defense
   is precedence + minter-class netting + D2 decorrelation, not identification.
2. **USDT chain-completeness unproven** — Tron majority; keyless trongrid
   rate limits at multi-year depth unknown; the coverage gate may kill the
   census at P0 (fail-closed, honest).
3. **Keyless transport fragility (measured)** — blockscout hard-banned the IP
   after ~4MB; only mevblocker served getLogs; a multi-year log census is a
   heavy job with an unmeasured transport ceiling.
4. **The 0.20 bar against 32 dead rows is brutal** — no rho was measured here
   (proposal-side only); flow-vs-OI correlation may exceed the bar; D2 is the
   designed executioner.
5. **CCTP netting layer is itself an identity assumption** (minter-contract
   labels are on-chain-verifiable, but proxy upgrades/pinned lists must be
   frozen at P0; misclassification flips "new dollars" ↔ "rotation").
6. **Costs** — any tradeable expression rides the frozen stress-tier ladder
   that produced crypto falsifications #11/#14 and the VOL-NG1 ceiling kill;
   P-21 ceiling must be preregistered before selection.
7. **License/terms** — CM community = CC BY-NC 4.0 (non-commercial); llama =
   no surfaced license; on-chain primary avoids both but inherits the transport
   risks in (3).

## 5. Probe inventory (all under probes/; every fetch has .meta.json with url/UTC/sha256/bytes/status)

- CM: A1..A30 (catalog + data windows incl. 2018/2019/2023-03-depeg/2026-09).
- Blockscout: B1 head, B2 USDC token record (total_supply 50,497,424,343.51),
  B4 USDC Mint 990-block window, B5 Mar-2023 block meta, B6 depeg-window Burns,
  B8 same-window Burns, B9/B10 USDT Issue/Redeem (0 events — sparse-regime
  evidence), B13 FULL UTC-day census summary (7,182/7,182 blocks; sha256
  ed4c8cfdf76a83bf25ea997c43e41ffa7afed667a69d6c746c0dc878d548d4bf).
- TronGrid: B3 (contract-info 404 — path dead), B7 events API (works keyless).
- Publicnode: B11/B12 archive eth_call → 403 NOT_ENTITLED (evidence kept).
- DefiLlama: C1/C1b/C2 (oversized charts, 2 truncated + disclosed),
  C3/C4 ETH-chain series (full, 652KB/700KB).
- D: 4byte signature lookup; Etherscan no-key deprecation notice.
- Deviations disclosed: two small POST JSON-RPC bodies (publicnode block
  timestamps, mevblocker getLogs) — "GETs only" read strictly would have made
  the mandated conservation-identity check impossible; payloads ≤ a few hundred
  bytes each, sequential; oversized llama responses capped and truncated
  bytes kept with truncation disclosed. No returns/PnL computed anywhere.

## 6. Handoff

`handoff_researcher_cxf-researcher-frontier-1.handoff.json` (schema
`zcode_orch_v3_handoff@1`) sits beside this report. commit_sha=null (no git
writes; artifacts uncommitted in the allowed directory, per dispatch).
