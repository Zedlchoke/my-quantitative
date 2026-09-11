# RULES — the operating law of the research factory

> Reinforcement layer, read by every agent at dispatch. This file summarizes
> and points to the authorities; it never overrides them. Order of authority
> (handbook §3): (1) latest clear owner instruction — an imperative, not a
> question, (2) the live plan of the running cycle, (3) `CLAUDE.md`, (4)
> frozen manifests/selections/run contracts/gate definitions, (5) historical
> plans and terminal reports, (6) README/NOTES/chat prose.
>
> Companion authorities: `CLAUDE.md` (operating contract),
> `HOW_TO_BE_A_LEAD_ENGINEER.md` v2 (§1–38, orchestrated+platform era),
> `docs/RESEARCHCTL.md` (control-plane entrypoint), `research/wayfinder/
> LESSONS.md` (P-1..P-17 program lessons + Q-1..Q-16 imported doctrine —
> all binding), `research/wayfinder/HYPOTHESIS_LEDGER.md` (every family
> ever tried + forbidden ancestry; the ONLY cross-asset denominator
> authority per P-9), `research/wayfinder/SURVIVORS.md`. All plans live in
> `plans/`; cycle state resolves ONLY through the canonical registry
> `plans/CYCLE_REGISTRY.json` (schema `cycle_registry@1`, written only via
> `researchctl`/governance — `plans/ACTIVE_CYCLES.json` is a generated
> read-only projection).

## 1. Universal law (every asset, every cycle)

**Evidence first.** No evidence, no claim.

```text
not run                  -> NOT_RUN
no data / no entitlement -> UNAVAILABLE_FAIL_CLOSED
ran, gate missed         -> FAIL
cannot proceed safely    -> BLOCKED
ran correctly, artifact  -> PASS
```

- Gates report `PASS/FAIL/NOT_RUN/BLOCKED` with command, exit code, SHA,
  tree state and evidence paths. A missing artifact is never an inferred
  PASS.
- Fail closed: unclear identity, data, license, timestamp, cost, SHA or
  authority defaults to STOP. Malformed/stale control state is
  `CONTROL_STATE_DRIFT` — refuse, never repair in place.
- History is append-only: scored artifacts, ledgers, terminal reports,
  historical worktrees and lessons are evidence. Never reset, rewrite or
  "improve" a recorded number. Publication is append-only (F-A7T-1).
- Two denominators per program: `observed` and `published`. Cross-asset
  totals come ONLY from the Lead-maintained ledger; terminal-report sums
  are as-of-intake (P-9). Program state 2026-09-11: **239 published / 242
  observed, 0 survivors; stocks 42/42, forex 42/42, crypto 155/158; S1
  SEALED everywhere.**
- S0 is screening, NOT untouched OOS. **S1 stays SEALED_UNTOUCHED** until a
  future owner-authorized plan opens it — sealed data AND criteria (Q-9:
  half a seal protects nothing). Opening S1, merging to main, purchases and
  any keyed signup are OWNER-ONLY actions. **Push carries a standing Lead
  authorization** (owner delegation 2026-09-11, "Bạn tự do push"): the Lead
  session in the root checkout pushes and verifies the remote tip; lane
  worktrees NEVER push (hook-enforced, scoped to `.worktrees/`).
- One cycle = one A1 thread. **One live Lead session per cycle** (P-17);
  mid-flight is not abandoned — check activity before writing to a surface
  another authority may own. Heavy cap 1 machine-wide; full pytest runs
  alone; sibling conflicts are `NOT_RUN_RESOURCE_CONFLICT`, never
  contention. `git -C <absolute path>` for every repo command; `pwd` before
  every `git worktree add`; never one branch in two worktrees; **never
  `git add -A`** — stage by pathspec only.
- **Structured handoff is mandatory** for every orchestrated task
  (schema `zcode_orch_v3_handoff@1` at the exact `handoff_path`); chat
  prose is advisory, the artifact is authority.
- **Guards are law, not suggestions** (handbook §2.6): CAS writes, heavy
  lock, task-store transitions, hook deny-lists (push, history rewrite,
  secrets, main-merge). A guard refusing is the system working; route
  around it only through owner authority and a commit, never in-session.
- Availability evidence is absolute (P-1): asserted-without-evidence
  timestamps are never authorized. **Measured beats stated, every time
  (Q-8)**: a vendor-stated constant is a hypothesis until measured from
  bytes.
- Margin-to-fail is reported per gate (P-2), with the bar's exclusion zone
  (Q-12). A control's verdict binds only under the data semantics it was
  computed with (P-3); a control is itself checked for null validity before
  it can kill (Q-11). Reproduction `ALL_MATCH` certifies self-consistency,
  never truth (P-4).
- Launch is two-key (P-8): fresh-context A7 publishes
  `<CYCLE>_S0_LAUNCH_AUTHORIZED` (0 unresolved HIGH/CRITICAL) AND the owner
  types the exact GO phrase AFTER seeing that verdict, at that cycle's own
  gate. GO typed early is intent and dies unconsumed; phrases never carry
  across cycles or pauses; TERMINAL is absorbing.

## 2. The anti-overfitting doctrine (why 242 cells produced 0 survivors)

1. **Preregistration**: hypothesis, mechanism, universe, clock, arms, costs,
   gates, falsification rule and failure interpretation are frozen BEFORE
   any scored outcome exists. No parameter, threshold, universe, top-K,
   cost or gate change after PnL is visible — that is rescue, and rescue is
   forbidden. `REJECT`, `BLOCKED` and `NOT_RUN` are successful outcomes.
2. **Blind proposals**: proposal agents receive the forbidden packet and no
   per-arm outcome files; outcome-blind attestations are signed on the wave
   SHA.
3. **Falsification controls**: every family carries a placebo/causal control
   that must RUN under evidenced semantics. If the control reproduces the
   anchor (>= 0.5x, same sign), the family dies — the falsification-by-
   control cluster has killed 14 families (latest #14: forex V8's
   DGS10-level control out-earned its anchor 4.0116x) and every kill was
   real information. A control that barely moves the signal may be an
   INVALID NULL, not a kill — adjudicate explicitly (Q-11).
4. **Ancestry veto**: a proposal is a relabelled ancestor if pooled
   |rho| > 0.20 vs any forbidden family or shadow (eleven-entry veto set in
   stocks, equivalents per asset in the ledger). Measured, never argued.
   Cross-horizon rescue of a dead family is the same violation (Q-3).
5. **Multiple testing is priced in**: one survivor after ~240 cells is a
   candidate, not an edge. DSR is computed in terminals over the cumulative
   trial count; PBO stays fail-closed below 8 configurations.
6. **Marginal gates are load-bearing**: fold concentration 0.5110 > 0.50
   killed a PF-1.36 family. Do not weaken a gate to let a beautiful number
   through; report the margin instead.
7. **Knife-edge awareness**: at PF 1.2–1.3 there is no room for ANY optimism
   anywhere in the chain (P-2). Cost models are conditional, never flat
   constants (Q-2); feasibility ceilings are measured on the recent window,
   never the archive average (Q-6).
8. **Dry-runs must be non-vacuous**: empty books and zero-decision passes
   are failures; recursive leak scans check every record depth for
   outcome-shaped fields.
9. **Closed doors stay closed (Q-10)**: every closure names the instrument
   that closed it and its reopening condition; re-litigating a closed cell
   by accident is what the failure registry + forbidden ancestry exist to
   prevent. A near-miss positive is decomposed into bill / clock / calendar
   before any successor plan exists (Q-1).

## 3. FOREX rules (no live plan — V8 and V9 both TERMINAL)

Forex V8 closed `FOREX_FREE_V8_REJECT_ALL` (2026-09-09, budget 3/6, GO
consumed at its own gate); V9 closed 0/6 without scored cells (its GO died
unconsumed). The next forex plan writes fresh; the standing constraints
below bind any future forex cycle.

- Data: keyless official sources ONLY (BIS WS_CBPOL, ECB SDMX, official
  release-calendar pages, ALFRED if evidenced). No signup, no key, no
  purchase; any key-requiring route is an owner decision.
- Availability: the announcement-ledger pattern is the house standard
  (pinned sha256, append-only extensions, conservative LATER bound when
  unevidenced); per-print CPI calendars must reach the same evidence class.
- Structure: daily-or-slower clocks; dual books (price-only must not invert
  sign); stress tier 2.0 is a PRIMARY gate; break-even bps mandatory;
  USD-drift gate; placebo controls runnable.
- Forbidden: session momentum/fade, Tokyo/London range structures, the
  invalidated vol-gated carry region (front door CLOSED by V4's measured
  rho 0.997–1.000), commodity-bloc risk-off, the V8 term-structure
  dispersion family and its DGS10-level control. The V3R economic
  observation (PF 1.2825 under honest availability) stays recorded — it is
  not a license.

## 4. CRYPTO rules (no live plan — V17 TERMINAL)

Crypto V17 closed 0/6: all six blind families died by their OWN frozen
rules BEFORE any scored cell (WKNDLIQ/TICKET-BREADTH/FUNDJUMP ancestry
vetoes, ATTN-PHASE non-positive expectancy, OICASCADE control-out-earns,
SILRES duty-coverage) — its GO died unconsumed. The next crypto plan
writes fresh; standing constraints:

- Data: keyless Binance public endpoints + the data.binance.vision bulk
  repository ONLY. Coverage-first: a source that cannot fund the S0 window
  is `COVERAGE_INSUFFICIENT_FAIL_CLOSED` before any proposal exists.
- Kernel: cost charged exactly once per fill (L-V14-0 fixtures); stress
  multipliers applied to booked PnL; costs broken out by fills vs holding.
- Forbidden: OI term-structure (OITD + duplicates), liquidity episodicity
  (LIQEPIS + duplicates), OILEV-V2 and its inverted shadow, basis-level
  fade (PREMFADE), BAB, carry families, weekend-liquidity structures
  (WKNDLIQ), ticket-breadth (V17), attention-phase (V17). ILLIQ replication
  remains owner-data-gated.
- Terminals: DSR over the cumulative crypto trial count; confirmatory
  status, where declared, is bound in every cell and the ledger.

## 5. STOCKS rules (no live plan — V13 TERMINAL)

Stocks V13 closed (budget 3/6; its GO consumed at its own gate). The V13
Form-4 substrate is a durable asset: 345,150 XMLs, digest `5d351623…`
(the `78c4fb1a` vintage is pre-F-1 evidence, not the current pin). The
next stocks plan writes fresh; standing constraints:

- Data: EODHD is owner-entitled (subscription owner-held; key in gitignored
  `.env`, environment-only, redacted from error strings, never in
  chat/commits) + SEC EDGAR multi-vintage machinery (declared UA). Raw data
  gitignored with sha256 manifests; no raw-data commit.
- Universe: the death-inclusive cohort is the standing universe (evidenced
  Form-15 census with 12B/12G taxonomy; dead-filer fundamentals; priced
  dead names). Survivorship claims are scoped to what the cohort proves —
  never claim a delisted leg the data does not contain (M-I1).
- Publication is append-only (F-A7T-1); band resolution fails closed (L-I3).
- Forbidden: the V13-measured chain-structure shadows join the eleven-entry
  veto set (momentum, semivariance, vol-level, WC-stock intensity,
  Goodwill/bloat, F1 accrual flow, depletion interaction, cash-level,
  V10's deseasonalized-timing form, V10's revision-correction form, V13
  chain-structure/death-event forms).
- Substrate integrity: external drift against the pinned digest is a
  hard blocker (byte-restore from `~/staging_backups/` per manifest is the
  sanctioned repair — P-13).

## 6. The agent roster (who gets spawned, and what each one is)

| Agent | Spawned as | Description and hard boundaries |
|---|---|---|
| **A1** | Cycle controller, one per cycle, one thread per cycle | The ONLY integrator/freezer/publisher/counter-owner. Worktree + manifest, dispatch from exact SHAs, serial cherry-picks with tests, freeze, ledger append, cycle close. Never repairs what it audits; never pushes; never `git add -A`. |
| **A2** | Accounting/kernel lane | Cost-once fixtures, publication regression, dual books, stress tiers, ledger serialization. |
| **A3** | Data-authority lane | PIT discipline (event/effective/available/retrieved), coverage censuses, availability evidence, provider probes, staging manifests. Kills unfundable sources BEFORE proposals exist. |
| **A4 / A5 / A6** | Blind proposal lanes (one axis each) | Two proposals per lane from the wave SHA; forbidden packet, NO outcome files; outcome-blind attestations; never see scored results. |
| **A7** | Independent auditor — **fresh context, mandatory at prelaunch and terminal** | Recomputes from bytes, hunts reasons to REFUTE, audits positives stricter than negatives, proves refusal paths, never repairs code, never asks the implementer how to pass. The A1's own thread may never audit itself (V8 lesson). |
| **A8** | Implementation lane | Frozen family runner + scored driver; synthetic fixtures; never "improves" a frozen spec. |
| **A9 (A9-F)** | Feasibility auditor | Decision counts, warmup coverage, turnover/cost ceilings, control identifiability — measured BEFORE selection, no PnL anywhere. |
| **quant-explorer / quant-implementer / quant-reproducer / quant-auditor** | Orchestrated dispatch surface (plugin, optional per cycle) | The plugin's four role types map onto the roster above (explorer≈A3/A9-read, implementer≈A2/A8, reproducer≈reproduction lane, auditor=A7). Dispatch via MCP task store; forward-only state machine; structured handoff mandatory; hooks enforce the deny-list on every lane. |
| **Lead Engineer** | The referee (this file's maintainer) | Reviews every handoff against artifacts, adjudicates disputes, enforces discipline and the P/Q lessons, lands the control-plane half of every close (P-16), maintains ledger/lessons/MAP, prepares owner decisions but never takes them. One live session per cycle. |
| **Owner** | The only human authority | Decides via cards/imperative phrases: purchases, signups, merge-to-main, S1 opening, every GO (push delegated to the Lead 2026-09-11). Questions are probes, not authority; silence is not authorization; a GO is consumed only at its own gate. |

## 7. GO phrase registry (exact strings; frozen phrase gates adjudicate form)

**ng1 generation live phrases (registered 2026-09-11, none consumed):**
All three ng1 GO phrases are DEAD: `GO FOREX NG1 SCORED EXECUTION` was
CONSUMED at its own gate 2026-09-11 (two-key: A7 v3 AUTHORIZED + Lead exercising
the owner standing delegation verbatim; 6/6 scored cells ran → FOREX_NG1_REJECT_ALL);
`GO CRYPTO NG1 SCORED EXECUTION` and `GO STOCKS NG1 SCORED EXECUTION` died UNCONSUMED
with their cycles' TERMINAL closes (BLOCKED_DATA_OR_SELECTION at 0/6 each);
`GO FOREX NG2 SCORED EXECUTION` and `GO FOREX NG3 SCORED EXECUTION` died UNCONSUMED with their cycles' closes (FOREX-NG2 P0-floor; FOREX-NG3 4/4 D2 VETO).
`GO CRYPTO NG2 SCORED EXECUTION` died UNCONSUMED with CRYPTO-NG2's close (4/4 D2 VETO at 0/6; 2026-09-12).
`GO FOREX NG4 SCORED EXECUTION` died UNCONSUMED with FOREX-NG4's close (4/4 D2 VETO at 0/6; 2026-09-12).

Historical dispositions (P-8; TERMINAL is absorbing):

```text
GO FOREX V8 SCORED EXECUTION    consumed at its own gate 2026-09-09
                                (two-key complete 720decb) — DEAD
GO STOCKS V13 SCORED EXECUTION  consumed at its own gate (3/6 scored cells
                                ran) — DEAD
GO FOREX V9 SCORED EXECUTION    died UNCONSUMED with V9's TERMINAL close
                                (0 cells; close chain landed 2026-09-10)
GO CRYPTO V17 SCORED EXECUTION  died UNCONSUMED with V17's TERMINAL close
                                (0 cells; all six families killed
                                pre-authorization by their own rules)
GO STOCKS V12 SCORED EXECUTION  died UNCONSUMED (BLOCKED_DATA_OR_SELECTION,
                                0 cells — 2026-09-08)
GO CRYPTO V16 / STOCKS V11 / FOREX V7 (and earlier) — consumed at their
own gates, DEAD. Expired/consumed phrases never carry forward (V6 ruling;
P-8).
```

## 8. The one-paragraph spirit

This factory does not optimize for beautiful backtests; it optimizes for
**trustworthy conclusions, cheaply reached and permanently recorded**. A
negative result with full evidence is a success — 242 recorded noes are the
calibration that prices the first yes, not 242 failures (Q-16). A thin
survivor with unevidenced assumptions is the most expensive failure the
program knows (forex V3 paid for P-1..P-6). Freeze the rules while calm —
they are the only thing that holds when the number is beautiful and wrong
(P-6).

## 9. Mechanism status ladder (governance; see `research/wayfinder/FAMILY_PIPELINE.md`)

Ladder: `DOCUMENTED -> IMPLEMENTED -> TESTED -> ADOPTED_BY_ACTIVE_CYCLE`.
Frozen and running cycles are never retrofitted (adoption boundary: crypto
V16+, forex V7+, stocks V12+; platform capabilities adopt per asset commit).

```text
canonical registry + researchctl     ADOPTED (SYSTEM_HARDENING_V1_PASS on
                                     main 4e71261; every cycle since boots
                                     through it — V8/V9/V13/V17, MDP-V2/
                                     V2R1, orchestration, platform. Atomic
                                     CAS writes + event journal + retry
                                     taxonomy + monitoring purity)
FAMILY_FAILURES registry + validator ADOPTED (61 entries, --verify PASS;
                                     V17/V13/V8 closes appended under it)
diagnostic persistability gate       ADOPTED (first delivery forex V7 — DSR
                                     computed at terminal from persisted
                                     per-period series, N=39; V8 N=42;
                                     V13/V17 NOT_RUN fail-closed with zero
                                     scored trials — correct under contract)
global heavy lock                    ADOPTED (round-1 by CRYPTO-V16 P0;
                                     round-2 hardened, machine-wide flock +
                                     PID/token registry; V13 substrate
                                     exercised the silence-window YIELDING
                                     pattern — release during idle windows)
orchestrator plugin v3.1             IMPLEMENTED + TESTED + CANARY-VERIFIED
                                     (PASS_AUTONOMOUS_HANDOFF_CANARY; store
                                     8/8 TERMINAL; STORE-FLOW-1/2/3 fixed
                                     @2ebf5c2; known-open: STOP-CAP-1 hook
                                     bound not enforced — LOW; mark_terminal
                                     MCP exposure pending). Available for
                                     adoption by future orchestrated cycles
research platform v3                 TERMINAL 2026-09-11, MERGED to the
                                     trunk 9024812 (owner imperative
                                     'hãy merge'; verdict
                                     RESEARCH_PLATFORM_V3_PASS_CORE_PARTIAL_
                                     ASSET_PILOTS @45561a1; 18/18 gates —
                                     core+authority lanes PASS, asset pilots
                                     NOT_APPLICABLE (MDP-V2 adoption packets
                                     absent); full battery 1868 PASS,
                                     reproduction ALL_MATCH; fresh-context A7
                                     re-audit returned CONFIRM_WITH_FINDINGS
                                     — 0 CRITICAL/HIGH, 1 MEDIUM traceability
                                     defect repaired-by-addendum
                                     (V3-G8_a7_fresh_context_addendum.json),
                                     8 LOW recorded; capabilities adopt per
                                     future asset commits)
dashboard                            BUILT (stdlib collector, self-contained
                                     HTML, purity G5: refresh leaves
                                     git status unchanged)
```
