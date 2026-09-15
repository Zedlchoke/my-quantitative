# CRITIC report — CRYPTO pre-cycle frontier survey (CRYPTO-PRECYCLE-SURVEY)

- TASK_ID `cxf-critic-frontier-1`, role CRITIC (independent falsifier; did not
  write the surveyed directions; pre-plan-stage adversarial review).
- HEAD measured at critic start: `3a3032f320ad443b333dfe7e36e075648e59be27`
  (researcher dispatched at `53d2d152…`; the mid-flight registry advance is
  researcher INC-CXF1-4, consistent with my own `git status`: only untracked
  `.zcode/`, `crypto_frontier_2026-09/`, `forex_frontier_2026-09/`).
- Today 2026-09-15. No returns/PnL computed by the critic (supply-census
  arithmetic and transport probes only). All critic fetches: keyless,
  sequential, small (≤139 KB per response), UA-tagged; digests in §5.

---

## 1. Ancestry re-measure (done by the critic, not trusted from the survey)

- `FAMILY_FAILURES.jsonl`: 109 total rows; **asset=crypto rows = 32** — the
  researcher's headline count is EXACT (re-counted by filter, not quoted).
  Composition: V6..V16 = 19 rows; V17 = 6; NG1 = 4; NG2 = 4. Kill codes:
  ANCESTRY_RHO_BLOCK 8 (all eight NG1/NG2 rows), CONTROL_OUTEARNED_ANCHOR 5,
  FOLD_CONCENTRATION 3, EXPECTANCY_NONPOSITIVE 6, others DATA_BLOCK /
  SELECTION / COST. FOLD_CONCENTRATION killed CARRY-7D (51.66%), ILLIQ
  (0.7055), PREMFADE (0.5110) — the exact gate class any sparse-regime
  conditioning book must fear.
- `HYPOTHESIS_LEDGER.md` §A read in full; crypto denominators 155 published /
  158 observed (unchanged since V17; NG1/NG2 closed at 0 cells). §E.2
  falsification-by-control cluster now #17 program-wide (P-24).
- `LESSONS.md` P-1..P-24 + Q-1..Q-16 confirmed present and binding. Most
  load-bearing for this adjudication: P-1 (asserted bounds are
  unauthorized), P-8 (GO mechanics), P-11 (per-period series persisted),
  P-12 (representation identity is measurement identity), P-15 (smoke kills
  one-directional), P-20 (control sharing the arm's state source is a
  mirror), P-21 (preregistered cost ceilings), Q-6 (recent-window
  feasibility ceilings), Q-7 (clock-only shadow), Q-10 (closed door states
  its reopening condition), Q-11 (invalid-null check).
- `PLAN_crypto_ng1.md` / `PLAN_crypto_ng2.md` read. NG2 binding law,
  verbatim shape: proposals CLEAN on the full 29-shape panel and all named
  controls (funding-LEVEL < 0.021) still died at D2 (0.4178 / 0.4872)
  against **dead-FOMC-form shadows** — being clean vs the standard panel is
  NOT sufficient; the dead-form envelope executes. Any NG3 plan must
  preregister its own dead-form shadow, not just the 29-panel.
- FOREX V9 binding law (ledger row): current-vintage revised-in-place tables
  are FORBIDDEN for scored consumption — vintaged channel mandatory. This is
  decisive for Direction 2.

## 2. Researcher-claim spot-checks (treated unverified; checked from their bytes + my own fetches)

| # | Claim | Result |
|---|---|---|
| V1 | 32 crypto registry rows | **VERIFIED** (my own re-count = 32) |
| V2 | Keccak topics Issue/Redeem/Mint/Burn | **VERIFIED** — ran their `tools/keccak_probe.py` locally; self-test PASS; all 5 topics reproduce |
| V3 | CM community keyless; usdc 2026-09-14 IssTotUSD = $2.293B while SplyCur FELL $44.5M (gross-issuance contamination) | **VERIFIED TWICE** — from their A29 bytes (2,293,226,492 / −44,532,027) AND my own fresh pull today (`ac344781…`): identical values |
| V4 | B13 full-day census: 7,182/7,182 blocks; net +28,746,185.02 | **REPRODUCED at chunk level** — my independent mevblocker pull of chunk 1 (219 mints +4,901,125.58) + chunk-1 burns (145) = **364 = their chunk_meta n exactly**; the chunk_meta column is mints+burns combined (Σchunk_meta 3,803 = mint_n 2,215 + burn_n 1,588 exactly — internally consistent, though the summary's labeling was ambiguous) |
| V5 | Blockscout head total_supply 50,497,424,343.51 (50.497B) | **VERIFIED** from B2 raw (`50497424343509521`, 6 dp) |
| V6 | USDT-ETH Issue/Redeem sparse (0 events in recent 990 blocks) | **VERIFIED + EXTENDED** — my own 300-block window at Mar-2023 depth also returns 0 Issue/Redeem (empty `46ab8616…`); the ETH-USDT census leg is genuinely starved |
| V7 | TronGrid events keyless works | **VERIFIED WITH A CATCH** — see FINDING-1 |
| V8 | "CCTP mints/burns measured dominant (minter 0xfd78ee…, burner 0x55fe002a…)" | **NOT REPRODUCED in my sample** — see FINDING-2 |
| V9 | "Deep windows 2018-06 … measured" under Direction 1 historical depth | **OVERCLAIMED AS WORDED** — see FINDING-3 |
| V10 | 429-ban incident on blockscout; only mevblocker served getLogs keyless | Accepted from incident record + my transports succeeded on mevblocker; blockscout not re-pounded by the critic (respect the ban) |

### FINDING-1 (new hazard, unflagged by the researcher)
Their own B7 trongrid probe bytes contain `"_unconfirmed":true` — the default
TronGrid events channel serves **UNCONFIRMED events**. A finalized-log census
using the default Tron channel would ingest pre-finality data (a finality/PIT
hazard the survey missed). Mitigation measured by the critic: the
`only_confirmed=true` parameter **works keyless** and combines with
`event_name=Issue` filtering and 2020-depth historical windows
(`22d41af8…`, 1 confirmed Issue at block 20,279,269, June 2020). The Tron leg
is feasible AND pinnable — but only via the confirmed channel; this must be a
frozen transport contract, not an option.

### FINDING-2 (composition claim does not reproduce in my window)
Chunk-1 (219 mint events, +4.901M USDC): the claimed CCTP minter `0xfd78ee…`
does not appear among the top-5 minters by count or value (not visibly present
at all). The dominant minter is `0x55fe002aeff02f77364de339a1292923a15844b8` —
the very address the researcher labels "Circle's pinned burner" (it is the
USDC treasury; it mints AND burns) — with **7 events = 2,763,125 USDC = 56%
of chunk-1 minted value**; top-5 minters = 86.6% of value. Two consequences:
(i) the census is **treasury-dominated, not CCTP-dominated** in my sample —
if that holds full-window, most census flow is primary-market issuance/
redemption (exactly the "new dollars" the hypothesis wants), and the CCTP
netting layer the researcher pre-built may be netting the WRONG minority;
(ii) the researcher's composition statement was asserted from one probe
window and does not generalize — P-1 applies: the minter/burner classification
table must be measured over the FULL scored window at P0 and frozen, never
asserted. My finding does not kill Direction 1; it corrects its identity-layer
design and hardens the P0 gate.

### FINDING-3 (wording overclaim, bounded)
Direction 1's "Historical depth: deep windows 2018-06 … measured" conflates
CM community aggregate windows with log-transport depth. No 2018-06 LOG
window exists in probes. My own deep-history test: mevblocker served the
Mar-2023 window (block 16,805,800; 9.18M blocks deep, ~2.5 y) with **32 burns
/ 6,992,269.48 USDC — byte-value-identical to blockscout's independent B6
pull** (`5ba4da11…` vs `dbe0c8bc…`), a strong cross-transport identity result.
But my 2019 (block 8.5M) and 2018 (block 6.66M) windows returned empty —
inconclusive (could be genuinely sparse batch-minting eras) — so 2018/2019
log depth on the surviving transports remains UNMEASURED. Materiality is LOW
because the frozen S4/NG H1 panels bound the scored window to
2025-08-22..2026-08-21; a 1-year census ≈ 2.6M blocks ≈ 5.2k chunk requests at
my measured rate (~500 blocks/1.4 s) ≈ 2-3 h — feasible under the single
heavy-job lock. But the wording must be corrected before it becomes a plan
premise.

---

## 3. Direction 1 — Issuer-contract net-flow census → float-contraction conditioning

### Attack
1. **Proxy contamination / dead ancestors (named rows):** "float contraction →
   forced de-risking" is structurally the same forced-deleveraging-crowding
   mechanism as dead **OILEV-V2** (V12, CONTROL_OUTEARNED_ANCHOR), **OITD**
   (V13), **OICYC** (V14), and the measured shadows `v17_oi_level` (0.3904)
   and `CTL-OISHARE` (0.431). Under the NG2 binding law, a census-regime book
   that is clean on the 29-panel can still die to a built OILEV-V2-dead-form
   shadow. Survival probability is genuinely low — but a D2 death is
   zero-budget by design, which is the factory working (Q-16).
2. **Reverse causality — is the "incremental information" claim honest
   science or a disguised momentum/dollars-flow family?** Adjudication: the
   researcher's framing ("full causal identification is NOT designable; the
   honest claim is D2 decorrelation, dies at 0.20 with zero budget") IS
   honest as far as it goes — it is falsifiable, preregistered, and
   one-directional. BUT the declared shadow battery has a HOLE: net-flow
   regimes are plausibly a deterministic transform of trailing price/vol
   (issuers supply demand-followers), i.e. the census regime can be a
   *relabelled momentum/vol state* — the exact disguise class that killed
   FXFV8-A5-P1 (DGS10-level shadow 4.01x) and RATES-NG1 (#16). The battery
   must add a mandatory **price-derived issuance proxy shadow**: fit the
   census net-flow regime from tape features only (frozen fit, PIT), then
   measure what the census adds beyond its own tape-predictable component.
   Without that shadow, "D2 decorrelation vs momentum forms" is measured
   against the wrong null.
3. **Double-counting / chain migration / wrapped:** handled in the proposal
   at the right standard (per-chain census, contract-address membership,
   never symbol matching) — but FINDING-2 shows the specific netting table
   was asserted, not measured. Fixable at P0.
4. **Conservation identity over time:** the identity Σ(Mint−Burn) == Δchain
   supply is contract-true for FiatToken and TetherToken v1 today, but both
   are PROXY contracts (USDT's implementation has been upgraded before;
   USDC's V2/V2.1/V3 era migrations). An implementation upgrade can add
   supply-changing paths. Gate: identity re-verified per window-batch and
   the census refused (fail-closed) on identity breach > tolerance; archive
   `eth_call` tie-out is keyless-blocked (measured by researcher, 403), so
   the gate runs on log-census vs second-transport window deltas — the exact
   cross-transport check I executed successfully at 2.5 y depth.
5. **Transport completeness / rate limits vs census scale:** 1-year scored
   window ≈ 5.2k chunk requests ≈ hours, single-transport (my measured
   rate); the blockscout 429-ban proves burst budgets are the constraint →
   census must run under the machine-wide heavy-job lock with pacing +
   coverage counters (Q-13 loud-payload law), 100% chunk coverage as the
   completeness contract (B13's 7182/7182 is the demonstrated standard).
6. **Tron completeness (USDT leg):** the unproven leg. My probe upgrades the
   state of knowledge: `event_name` + `only_confirmed=true` + historical
   windows all work keyless. USDT-ETH is event-starved (V6 + my C7); the
   USDT census is effectively a Tron census. Gate: if Tron filtered-census
   fails its sampled-depth agreement gate, the USDT leg dies and the plan
   proceeds **USDC-primary, per-issuer declared** — never a silent
   "stablecoin total".
7. **Sparse regimes / folds / history:** regime states are multi-day and
   autocorrelated; big float-contraction episodes cluster (2022-05, 2023-03,
   2022-06/11 — outside the 1-year scored window anyway). FOLD_CONCENTRATION
   (the gate that killed the three near-misses) is the most likely post-D2
   death; floors must count net-flow REGIME DAYS (not raw events — the
   researcher already says this) and Q-6 recent-window arithmetic must be
   run at P2, not assumed.
8. **Availability lag / finality / timezone:** event-time = block timestamp;
   decision bars use only flows ≥ 2 epochs (≥ 64 blocks, ~13 min) finalized
   before bar start; the lag is ours to measure and persist (P-11: per-
   period series for DSR must be an output-contract item). UTC-day boundary
   via block timestamps measured sound (00:00:11Z boundaries).
9. **Data snooping at 155 cells:** the source (settlement-layer primary-
   market float from issuer-contract logs) appears in NO dead row — every
   dead family is perp-native (OI, funding, aggTrades, tape) or clock-native
   (NG1/NG2). Snooping risk is handled by preregistration + D2, per law.

### Verdict — Direction 1
**PASS_SOURCE_GATE** (verified end-to-end keyless by my own probes: census
chunk reproduced; deep history cross-transport identical; Tron confirmed
channel works) + **PASS_MATERIALLY_NEW** (new information source with a
new census-gate falsifier; the reverse-causality concession is honest and
the design is falsifiable at D2 for zero budget) — **CONDITIONAL** on the
P0 gates in §5, with two corrections the plan MUST absorb: the
treasury-vs-CCTP composition re-measure (FINDING-2) and the added
price-derived issuance-proxy shadow (§3 attack 2).

## 4. Direction 2 (CM Community + DefiLlama aggregates) and Direction 3 (depeg episodes)

### Direction 2 — adjudication: **FAIL for plan candidacy**
Two independent kills, either sufficient:
1. **PIT-primary-fails-by-design, and the repo's own law already binds this:**
   FOREX-V9's binding HIGH ("current-vintage revised-in-place tables are
   forbidden — vintaged channel mandatory") plus the researcher's own
   admission (no vintage channel; measured revision/identity breaks: day-label
   delta +75.9M vs on-chain +28.7M; head gap 3.33B). A plan slot for a
   source that fails its own primary gate by design is theater.
2. **License:** CM community = CC BY-NC 4.0 (researcher-stated; owner
   adjudication never obtained); llama = no surfaced license. A trading
   research program is not cleanly "non-commercial" — under P-18, until an
   owner ruling lives at the exact bytes a gate reads, scored consumption is
   not authorized. No owner ruling exists.
Residual legitimacy: cross-check-grade ONLY, zero scored weight, inside an
NG3 built on Direction 1 — which is exactly how the researcher ranked it.
Reopening condition (Q-10): an owner-authored license/PIT ruling plus a
vintage channel reopens it as a primary candidate; otherwise dead.

### Direction 3 — adjudication: **FAIL for plan candidacy (dies at survey)**
The researcher self-declares EXPECTED KILL: a handful of depeg episodes since
2018 vs frozen Q-6 floors (n ≥ 30 instants class) → NOT_RUN at the census
floor is the honest close. I concur and go one step further: it should not
consume a plan slot or a lane. Value extracted: its probed windows (B6,
A21/A26/A30) become composition-break flags for the NG3 census, and the
direction is recorded as a survey finding with its reopening condition
(a fundamentally new episode-rich regime class, which does not exist).
Recording it as a "direction" was disclosure, not a proposal — accept the
disclosure, refuse the slot.

---

## 5. Overall verdict and required P0 kill-gates for CRYPTO-NG3

**Does any direction merit a plan? YES — exactly one: Direction 1**, as a
conditioning-only, D2-executed, census-gated cycle. Directions 2-3 get no
slot (2 = cross-check grade inside NG3 only; 3 = survey finding only). If
the Lead disagrees on budget grounds, the honest alternative is
NO_CRYPTO_CYCLE_OPENED with this report as the evidence — but the
feasibility basis for a cheap, honest falsification run exists and is
measured.

P0 kill-gates the plan must pin (specific, frozen before D1):

1. **Census-identity gate:** per-window Σ(Mint−Burn) == chain-supply delta
   cross-checked on a SECOND independent transport (the blockscout/mevblocker
   pattern my probes executed); identity breach beyond frozen tolerance in
   any batch → census refuses, fail-closed; re-run only after named cause.
   Proxy-upgrade monitor: contract implementation re-pinned at cycle start
   and end; any upgrade inside the window flags all affected windows.
2. **Transport-depth gate:** 12 sampled windows spanning the FULL scored
   depth on BOTH surviving transports with event-set agreement (my 2.5 y
   reproduction is the template); 2018/2019 log depth unmeasured → either
   measure at P0 or scope the census to the frozen 1-year panel window
   (+ warmup margin), which my rate measurement shows is hours-scale under
   the heavy-job lock.
3. **Census-completeness contract:** 100% chunk coverage with per-chunk
   counters persisted (B13 7182/7182 standard), loud failure on payload
   shape (Q-13), pacing under the machine-wide lock (blockscout 429 is the
   proven ban mode).
4. **Tron-leg gate (USDT):** `only_confirmed=true` + `event_name=Issue/
   Redeem` + per-year sampled-depth agreement (my June-2020 confirmed hit is
   the evidence it can pass); on failure the USDT leg dies and the census is
   declared USDC-primary per-issuer — never a silent stablecoin total.
5. **Identity netting gate (FINDING-2 correction):** minter/burner
   classification table measured over the FULL window at P0 and frozen
   (address + topic pairs from pinned ABIs; 4byte collisions irrelevant
   under that pinning); composition disclosed (my sample: treasury-
   dominated, 86.6% top-5 concentration); CCTP-vs-treasury share re-measured,
   never asserted (P-1).
6. **Composition-break flags:** UST-2022-05, USDC-2023-03 and any detected
   episode windows flagged at D1 (arm-split or excluded, frozen); inside the
   1-year scored window, scan for the same class and flag identically.
7. **D2 incremental-information design constraints:** pooled |rho| ≤ 0.20
   vs the FULL 32-row inventory + 29-shape panel + NG2 law dead-form shadow
   (**an OILEV-V2 flow/stock dead-form built as a named kill-candidate**) +
   **NEW mandatory price-derived issuance-proxy shadow** (tape-fitted
   net-flow regime; census must add information beyond its own
   tape-predictable component) + Q-7 clock-only shadow + Q-11 invalid-null
   check on any permuted-flow control. Declared in advance: D2 failure =
   zero-budget death, no rescue, no re-clock.
8. **Conditioning-only book law:** regime states only, never directional
   flow prints; flows used only when finalized ≥ 2 epochs before bar start;
   regime-state series + per-period book series persisted (P-11) for DSR.
9. **Cost/financing:** P-21 preregistered ceiling measured at P2 on the
   frozen stress-tier ladder (the tier that killed falsification
   instances #11/#14 and VOL-NG1); funding and denominated-vs-quote
   rounding per the frozen program cost kernel; fold floors count net-flow
   REGIME DAYS under Q-6 recent-window arithmetic.
10. **CM/llama cross-check discipline:** zero scored weight; CC BY-NC owner
    adjudication recorded at the enforcing bytes (P-18) BEFORE any scored
    consumption, or the cross-check leg is dropped.
11. **Boundaries unchanged:** S1 sealed; no push/merge; single heavy-job
    lock for the census; no keys/signups; census artifacts sha-pinned at
    ingest (the census IS the data authority; no vendor file is consumed).

## 6. Residual risks (post-gate, honest)

- The 0.20 bar against a 32-row measured-dead inventory has killed 8/8
  NG1/NG2 proposals; even with the corrected shadow battery, Direction 1's
  most likely outcome is a D2 kill. That is an acceptable, cheap,
  information-positive outcome (Q-16) — but it must be written into the plan
  as the expected close, not oversold.
- Keyless transports are single-point dependencies (one healthy getLogs
  host measured); a mid-cycle host policy change is a
  BLOCKED_DATA risk, not a science risk — plan the terminal for it.
- USDT coverage may remain structurally partial (Tron gate); the census's
  economic claim must then be scoped to "USDC primary-market float", which
  weakens (but does not invalidate) the scarcity story for BTC/ETH/SOL
  margin.

## 7. Critic probe inventory (my own fetches; all keyless, sequential)

| Probe | Transport | Key result | sha256 (prefix) |
|---|---|---|---|
| C1 CM usdc 09-13..14 | community-api.coinmetrics.io | IssTotUSD 2,293,226,491.58 vs SplyCur −44,532,027 (claim V3 verified) | ac344781… |
| C2 chunk-1 mints 25962689-25963188 | rpc.mevblocker.io | 219 mints +4,901,125.58; byte-identical on repeat pull | a759f31e… |
| C3 2019/2018 depth windows (2x) | rpc.mevblocker.io | empty results — inconclusive (genuinely sparse eras not excluded) | 46ab8616… |
| C4 depeg burns 16805800-16806100 | rpc.mevblocker.io | 32 burns, 6,992,269.48 — byte-value-identical to blockscout B6 (cross-transport identity at 2.5 y depth) | 5ba4da11… |
| C4b chunk-1 burns | rpc.mevblocker.io | 145 burns; 219+145 = 364 = B13 chunk_meta exactly | 2faeb4c0… |
| C5 trongrid Issue, confirmed, Jun-2020 | api.trongrid.io | 1 confirmed Issue @ block 20,279,269 — only_confirmed + event_name + depth all work keyless | 22d41af8… |
| C6 minter distribution chunk-1 | (same pull as C2) | treasury 0x55fe002a… = 56% of minted value; CCTP minter absent from top-5 (FINDING-2) | a759f31e… |
| C7 USDT-ETH Issue/Redeem Mar-2023 window | rpc.mevblocker.io | 0 events (sparsity confirmed at depth; query served fine) | 46ab8616… |

Deviations: three small POST JSON-RPC bodies (mevblocker eth_getLogs) —
same class the researcher disclosed (INC-CXF1-2); no repo writes outside my
two allowed artifact paths; no registry/ledger/git writes; S1 untouched;
scratch fetch scripts kept outside the repo (/tmp).
