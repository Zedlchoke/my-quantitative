# PLAN CRYPTO-NG3 — issuer-contract stablecoin net-flow census as float-state conditioning

> Status: `PLANNED_NOT_STARTED` (2026-09-15). Authority: LESSONS.md P-19
> (owner verbatim 2026-09-11: a generation ending <= 6 scored cells / <= 2
> families opens ONE more full cycle from scratch) fired by the CRYPTO-NG2
> terminal close at 0 cells / budget 0/6 (`plans/CYCLE_REGISTRY.json`
> CRYPTO-NG2 row) and the NG1/NG2 recorded law that the exogenous-clock /
> announced-information classes are measured-dead ancestry. This cycle's
> information source is a different class entirely: finalized issuer-contract
> logs (USDT Issue/Redeem, USDC Mint/Burn) from the settlement layer itself —
> point-in-time at event time, keyless-verified end to end. Pre-cycle
> evidence: `research/control/crypto_frontier_2026-09/` (survey_report.md,
> critic_report.md, probes/). A P0 close with zero scored cells is a valid
> result. Nothing in this plan is evidence of profitability.

## 0. Cycle identity

```text
cycle_id          CRYPTO-NG3
asset             crypto
plan              plans/PLAN_crypto_ng3.md
branch            orca/crypto-ng3-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/crypto-ng3/integration
budget            6 scored cells max / 2 families max
go_phrase         GO CRYPTO NG3 SCORED EXECUTION
S0                OPEN — screening only
S1                SEALED_UNTOUCHED
orders            NONE — no paper, testnet or live orders
```

`PROSPECTIVE-SHADOW-V1` remains independent and `ACTIVE_LIGHT`. This cycle
must not read its PnL, trades, marks or verdicts when proposing or selecting.

## 1. Question, in simple language

When a stablecoin issuer mints or redeems tokens on-chain, the settlement-
layer float changes. We ask one narrow question:

> After removing price momentum, open-interest/funding shadows, tape-fitted
> issuance proxies and every measured-dead exogenous-clock form, does the
> measured state of issuer-contract net flows (census-grade, finalized logs,
> minter-identity-netted) contain repeatable information about later returns
> on the frozen crypto panels?

Direction is not assumed. The honest causal position: reverse causality
(price moves causing issuance) is NOT fully identifiable — so this family
survives only as a CONDITIONING-ONLY design whose D2 claim is incremental
information over the declared shadow set. Any proposal claiming "new dollars
entering → must buy crypto" as a forcing mechanism is invalid, not
repairable. Survey-closed alternatives (critic_report.md, binding as Q-10
conditions): aggregate-supply regime conditioning (revised-in-place, license)
and depeg-episode designs (Q-6 floors unreachable) are FORBIDDEN as proposal
material.

## 2. Why this is a new cycle

- The 32 crypto rows in `research/wayfinder/FAMILY_FAILURES.jsonl` (plus the
  pre-factory ledger §B families) consume no settlement-layer issuance
  observable: NG1 was the announcement clock, NG2 the macro-print/funding
  grid. On-chain issuer-contract net flows are a materially new information
  source, not a relabel of any dead family.
- The census arithmetic is verified: conservation identity RUN on-chain
  (2026-09-13 net +28.746M USDC exact from logs) while aggregate APIs
  disagree by definition (llama day-label +75.87M; blockscout/llama head gap
  3.33B) — the chain census is the only primary; aggregates are cross-check
  only, zero scored weight (CC BY-NC and revised-in-place histories fail the
  program's PIT-primary law, FOREX-V9 binding).
- Critic catches absorbed as gates: Tron default events are unfinalized
  (`_unconfirmed:true`) — the `only_confirmed=true` keyless channel is
  MANDATORY and the USDC-primary fallback is declared; minter-identity
  netting is MEASURED full-window (observed dominant minter is the USDC
  treasury 0x55fe002a, 56% of minted value in the sampled chunk), never
  asserted.

## 3. Source authority and P0 gates (the critic's eleven, pinned)

Primary source: finalized on-chain issuer-contract logs via keyless
transports only — public RPC (mevblocker; full-UTC-day census proven),
Blockscout (GET works, hard-429 ban risk documented), TronGrid events with
`only_confirmed=true`. 4byte signatures are aid-only; contract address +
topic hash are pinned from self-computed keccak (collisions documented).
No paid endpoint, no new API key, no account.

```text
C1  CENSUS-IDENTITY      cross-transport byte-identity gate: two transports
                         agree on overlapping windows (mevblocker ==
                         blockscout already proven at 2.5y depth for USDC
                         burns); any mismatch => fail
C2  TRANSPORT-DEPTH      log-depth sampling gate for 2018/2019 (deeper than
                         current probes); inconclusive empties recorded, not
                         assumed empty; frozen panels bound the scored
                         window to ~1y so depth gaps are scope declarations
C3  CHUNK COVERAGE       100% chunk-coverage contract over any census window
C4  TRON FINALITY        Tron only with only_confirmed=true; USDC-primary
                         fallback declared; never a silent stablecoin total
C5  IDENTITY NETTING     minter classes measured FULL-WINDOW (treasury,
                         CCTP, exchanges only if labels are PIT-evidenced);
                         netting rule frozen in the census commit; no
                         hindsight labels
C6  COMPOSITION FLAGS    composition-break flags (depeg windows, regime
                         seams) carried into D2 as declared strata
C7  CONTRACT IDENTITY    address + topic pinned from self-computed keccak;
                         fail-closed on any mismatch or unknown event shape
C8  AVAILABILITY         event_time = block finalized; available_time = when
                         a keyless transport serves it, measured; decision
                         times conservative; >= 2-epoch finality convention
C9  CONSERVATION         supply-delta == mints - burns identity checked per
                         window; breaks are verdict rows, never smoothed
C10 FOLD FREEZE          three chronological folds + exclusion rule frozen
                         textually in the census commit, before any D2
C11 REPRODUCIBILITY      census code, raw-request manifest, digest manifest,
                         schema report under research/control/crypto_ng3_run/;
                         detached rerun reproduces counts and digests
```

P0 is source engineering and census only. No returns, PnL, PF, Sharpe,
drawdown, survivors or S1 evidence. Any C1-C9 miss => `BLOCKED_SOURCE`.

## 4. D1 outcome-blind proposal contract

Only after P0 PASS: two independent proposal lanes, one family identity
(stablecoin float-state conditioning) with variants as arms consuming
declared trial identities. Proposals see P0 schema/coverage/folds only.
Each must specify mechanism (conditioning form), formula, decision rule,
lookback, holding window, universe, turnover, missing-data rule, falsifier
and all mandatory controls. Net issuance may not be called "money entering
crypto" or "buying pressure"; those interpretations die without repair.

## 5. Mandatory vetoes and controls (D2 constraints)

All on the frozen representation (P-12). **No E-stage cell is funded unless
every veto below has run measured and the anchor survives** (the NG2 dead-
form-envelope law: panel-clean anchors still die to dead-form shadows).

```text
X1 ANCESTRY RHO          pooled |rho| <= 0.20 vs the full crypto inventory,
                         explicitly including the NG2 dead-form 29-shape
                         panel triad (the complete NG2 declared shadow set)
X2 OI/FUNDING DEAD FORMS OILEV-V2 and the NG2 dead-form shadow set — the
                         anchor must not be a relabelled OI/funding state
X3 TAPE-FITTED ISSUANCE  NEW mandatory shadow: an issuance proxy fitted from
                         price/tape alone; if it explains the anchor, the
                         on-chain census adds nothing and dies
X4 CLOCK/CALENDAR        Q-7 clock-only conditioning shadow + day-of-week
                         geometry (the NG1 killer class)
X5 NULL VALIDITY         Q-11: delayed-state and shuffled nulls must MOVE the
                         signal; INVALID-NULL verdicts explicit
F1 COST CEILING (P-21)   financing-inclusive worst-case round-trip ceiling
                         measured at P2 on the frozen funding/cost bands
```

## 6. D2 feasibility and novelty gate

Non-scored diagnostics only: X1-X5 rho measurements, eligible decision
counts, turnover, missingness, concentration, F1 ceiling. D2 PASS requires
all vetoes survived, folds populated, costs chargeable, proposal + arm hashes
frozen. The expected modal terminal (critic residual-risk note): a measured
D2 kill — the 0.20 bar has killed 8/8 NG1/NG2 proposals; a kill is the
system working and must never be oversold. Otherwise selection is empty and
the cycle closes at 0/6.

## 7. Trading, costs and risk contract

```text
decision        conservative, post-finality, per C8 availability evidence
entry/exit      next executable bar on the frozen panel / preregistered
                window; force-flat at fold boundary
universe        frozen Binance panels (existing S4 target set) only
costs           frozen crypto band schedule charged once per fill + funding
gross cap 1.0   symbol cap 0.10   stress tier 2.0 + break-even margin
```

No claim may rely only on gross or pre-funding performance.

## 8. Execution phases and ownership

```text
P0  C1-C11 census gates
D1  two outcome-blind proposal lanes
D2  X1-X5 + F1 measurement, no scored outcomes
S   selection + exact arm/data/fold/config hash freeze
I   isolated implementation lanes; A1 integrates one handoff at a time
Z   sanitized exact-arm dry-run + recursive leak scan
A7  fresh-context prelaunch audit; zero unresolved HIGH/CRITICAL; the A7
    launch key is `CRYPTO_NG3_S0_LAUNCH_AUTHORIZED`
GO  owner types exact phrase at its own gate; early GO dies unconsumed
E   at most 6 scored cells under the machine-wide heavy lock
R   detached reproduction; T terminal audit + two-half close
```

All lanes write `zcode_orch_v3_handoff@1` to their exact dispatch path.
Lanes never merge, rebase, push, edit registries/ledgers or read other
lanes' outcomes.

## 9. Trial accounting and result language

Observed and published denominators counted separately; every computed cell
consumes an observed slot. `D2 eligible` means only "allowed to be tested" —
never profitable, robust or promotable. This plan contains no predeclared
survivor outcome.

## 10. Prewritten terminal outcomes

```text
CRYPTO_NG3_BLOCKED_SOURCE_OR_SCHEMA
CRYPTO_NG3_BLOCKED_DATA_OR_SELECTION
CRYPTO_NG3_BLOCKED_PRELAUNCH
CRYPTO_NG3_REJECT_ALL
CRYPTO_NG3_SURVIVORS_LOCKED_FOR_FUTURE_S1
CRYPTO_NG3_INCOMPLETE_NOT_PROMOTABLE
CRYPTO_NG3_TECHABORT_PRESERVED
```

Gate-to-terminal mapping: any C1-C9 miss at P0 closes under
`BLOCKED_SOURCE_OR_SCHEMA`; a C10 fold-freeze or C11 reproducibility miss
closes under `BLOCKED_DATA_OR_SELECTION`.

## 11. Boundaries

- No paid endpoint, new API key, account creation or credential request;
  keyless transports only; Etherscan v2 / The Graph gateway / publicnode
  archive remain NOT_ENTITLED.
- Coin Metrics Community and DefiLlama are CROSS-CHECK only, zero scored
  weight (PIT-revised + license), never a sole authority. If any enforcing
  stage would need CC BY-NC bytes beyond cross-check display, that leg is
  DROPPED (zero scored weight) or routed to an explicit frozen owner license
  decision (P-18/P-25); no license term is ever auto-accepted.
- No S1 access and no paper/testnet/live orders.
- No pushes or writes to `.zcode/`; registry only via `researchctl`.
- One heavy job machine-wide; never kill a foreign worker; blockscout 429
  etiquette (bounded session volume) is binding.
- Shadow valuation remains light and independent.

## 12. Immediate actions

```text
1. Commit this plan and the crypto frontier evidence by exact pathspec.
2. Independent fresh-context adversarial plan audit.
3. Remediate every valid HIGH/CRITICAL finding; re-audit.
4. Register CRYPTO-NG3 through researchctl as PLANNED_NOT_STARTED.
5. Bootstrap the integration worktree and dispatch P0 only.
6. Stop at the scored prelaunch gate and wait for the exact owner GO.
```
