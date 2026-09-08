# RULES — the operating law of the research factory

> Reinforcement layer, read by every agent at dispatch. This file summarizes
> and points to the authorities; it never overrides them. Order of authority
> (handbook §3): (1) latest clear owner instruction, (2) the live plan of the
> running cycle, (3) `CLAUDE.md`, (4) frozen manifests/selections/run
> contracts/gate definitions, (5) historical plans and terminal reports,
> (6) README/NOTES/chat prose.
>
> Companion authorities: `CLAUDE.md` (operating contract),
> `HOW_TO_BE_A_LEAD_ENGINEER.md` (§1–35), `research/wayfinder/LESSONS.md`
> (P-1..P-9, each paid for), `research/wayfinder/HYPOTHESIS_LEDGER.md`
> (every family ever tried + forbidden ancestry; the ONLY cross-asset
> denominator authority per P-9), `research/wayfinder/SURVIVORS.md`.
> All plans live in `plans/` — highest version per asset is live; every
> lower version is a closed historical authority, never rewritten.

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
  tree state and evidence paths. A missing artifact is never an inferred PASS.
- Fail closed: unclear identity, data, license, timestamp, cost, SHA or
  authority defaults to STOP, never to a convenient assumption.
- History is append-only: scored artifacts, ledgers, terminal reports,
  historical worktrees and lessons are evidence. Never reset, rewrite or
  "improve" a recorded number. Publication is append-only (F-A7T-1).
- Two denominators per program: `observed` (every computed outcome, even if
  publication failed) and `published`. Cross-asset totals come ONLY from the
  Lead-maintained ledger; terminal-report sums are as-of-intake (P-9).
- S0 is screening, NOT untouched OOS. **S1 stays SEALED_UNTOUCHED** until a
  future owner-authorized plan opens it. Opening S1, pushing, merging to
  main, purchases and any keyed signup are OWNER-ONLY actions.
- One cycle = one A1 thread. Heavy cap 1 machine-wide; full pytest runs
  alone; conflicts with sibling cycles are `NOT_RUN_RESOURCE_CONFLICT`,
  never contention. `pwd` before every `git worktree add`; never one branch
  in two worktrees; **never `git add -A`** — stage files by name only
  (the root checkout carries the owner's untracked artifacts).
- Availability evidence is absolute (P-1): every conditioning row carries an
  EVIDENCED stamp or the conservative LATER bound; asserted-without-evidence
  timestamps are never authorized. The forex V3 survivor died for exactly
  this.
- Margin-to-fail is reported per gate (P-2): a pass says nothing about how
  close it was; thin margins get recorded as thin.
- A control's verdict binds only under the data semantics it was computed
  with (P-3); any semantics change recomputes controls too.
- Reproduction `ALL_MATCH` certifies self-consistency, never truth (P-4);
  exact reproduction reproduces the bug as well as the result.
- Launch is two-key (P-8): fresh-context A7 publishes
  `<CYCLE>_S0_LAUNCH_AUTHORIZED` (0 unresolved HIGH/CRITICAL) AND the owner
  types the exact GO phrase AFTER seeing that verdict. A GO typed before
  its gate exists is intent, never a key; the frozen phrase gate adjudicates
  form; GO phrases never carry across cycles.

## 2. The anti-overfitting doctrine (why 197 cells produced 0 survivors)

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
   control cluster has killed 9 families and every kill was real
   information (exposure-form shadows are now measured veto entries).
4. **Ancestry veto**: a proposal is a relabelled ancestor if pooled
   |rho| > 0.20 vs any forbidden family or shadow (nine-entry veto set in
   stocks; equivalent sets per asset in the ledger). Measured, never argued.
5. **Multiple testing is priced in**: one survivor after ~200 cells is a
   candidate, not an edge. DSR is computed in crypto terminals over the
   cumulative trial count; PBO stays fail-closed below 8 configurations;
   "best-of-many" without deflation is never claimed.
6. **Marginal gates are load-bearing**: fold concentration 0.5110 > 0.50
   killed a PF-1.36 family. Do not weaken a gate to let a beautiful number
   through; report the margin instead.
7. **Knife-edge awareness**: at PF 1.2–1.3 there is no room for ANY optimism
   anywhere in the chain — data timing, costs, fills, financing (P-2).
8. **Dry-runs must be non-vacuous**: empty books and zero-decision passes
   are failures (V8's F-A7-1 nearly burned a whole budget on vacuous
   cells); recursive leak scans check every record depth for outcome-shaped
   fields.

## 3. FOREX rules (live plan: `plans/PLAN_forex_v8.md`)

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
  rho 0.997–1.000), commodity-bloc risk-off. The V3R economic observation
  (PF 1.2825 under honest availability) stays recorded — it is not a license.

## 4. CRYPTO rules (live plan: `plans/PLAN_crypto_v16.md`)

- Data: keyless Binance public endpoints + the data.binance.vision bulk
  repository ONLY. Coverage-first: a source that cannot fund the S0 window
  is `COVERAGE_INSUFFICIENT_FAIL_CLOSED` before any proposal exists.
- Kernel: cost charged exactly once per fill (L-V14-0 fixtures); stress
  multipliers applied to booked PnL; costs broken out by fills vs holding.
- Forbidden: OI term-structure (OITD + duplicates), liquidity episodicity
  (LIQEPIS + duplicates), OILEV-V2 and its inverted shadow (the §1.1 front
  door was exercised by OICYC and closed), basis-level fade (PREMFADE),
  BAB, carry families. ILLIQ replication remains owner-data-gated.
- Terminals: DSR over the cumulative crypto trial count; confirmatory
  status, where declared, is bound in every cell and the ledger.

## 5. STOCKS rules (live plan: `plans/PLAN_stocks_v12.md`)

- Data: EODHD is owner-entitled (subscription owner-held; key in gitignored
  `.env`, environment-only, redacted from error strings, never in
  chat/commits) + SEC EDGAR multi-vintage machinery (declared UA). Raw data
  gitignored with sha256 manifests; no raw-data commit.
- Universe: the death-inclusive cohort is the standing universe (evidenced
  Form-15 census with 12B/12G taxonomy; dead-filer fundamentals; priced
  dead names). Survivorship claims are scoped to what the cohort proves —
  never claim a delisted leg the data does not contain (M-I1).
- Publication is append-only (F-A7T-1); band resolution fails closed (L-I3).
- Forbidden: all prior stocks families plus the measured shadows (momentum,
  semivariance, vol-level, WC-stock intensity, Goodwill/bloat, F1 accrual
  flow, depletion interaction, cash-level, V10's deseasonalized-timing
  characteristic form, V10's revision-correction direction/breadth form) —
  the eleven-entry veto set.

## 6. The agent roster (who gets spawned, and what each one is)

| Agent | Spawned as | Description and hard boundaries |
|---|---|---|
| **A1** | Cycle controller, one per cycle, one thread per cycle | The ONLY integrator/freezer/publisher/counter-owner. Creates the worktree + manifest, dispatches lanes from exact SHAs, cherry-picks serially with tests after each pick, freezes, appends the ledger, closes the cycle. Never repairs what it audits; never pushes (Lead/owner does); never stages with `git add -A`. |
| **A2** | Accounting/kernel lane | Cost-once fixtures, publication regression, dual books, stress tiers, ledger serialization. Owns the accounting contract of the cycle. |
| **A3** | Data-authority lane | PIT discipline (event/effective/available/retrieved), coverage censuses, availability-evidence tables, provider probes, staging with hash manifests. Kills unfundable sources BEFORE proposals exist. |
| **A4 / A5 / A6** | Blind proposal lanes (one axis each) | Write exactly two proposals per lane from the wave SHA under full packet discipline; receive the forbidden packet and NO outcome files; sign outcome-blind attestations; never see scored results. |
| **A7** | Independent auditor — **fresh context, mandatory at prelaunch and terminal** | Recomputes from bytes, hunts reasons to REFUTE claims, audits positives stricter than negatives (§20.2), proves refusal paths, never repairs code, never asks the implementer how to pass. Lead-dispatched or owner-dispatched separately — the A1's own thread may never audit itself (V8 lesson). |
| **A8** | Implementation lane | Builds the frozen family runner + scored driver from the selection freeze; synthetic-fixture tests; never "improves" a frozen spec — ambiguities go back to A1. |
| **A9 (A9-F)** | Feasibility auditor | Measures decision counts, warmup coverage, turnover/cost ceilings, control identifiability and runnability BEFORE selection — no PnL anywhere. |
| **Lead Engineer** | The referee (this file's maintainer) | Reviews every handoff against artifacts, adjudicates disputes, enforces discipline and the P-lessons, maintains ledger/lessons/MAP at every close, prepares owner decisions but never takes them. |
| **Owner** | The only human authority | Decides via cards/phrases: purchases, signups, push/merge, S1 opening, and every GO phrase. Silence is not authorization; a GO is consumed only at its own gate. |

## 7. GO phrase registry (exact strings; frozen phrase gates adjudicate form)

```text
GO CRYPTO V16 SCORED EXECUTION     (live plan plans/PLAN_crypto_v16.md;
                                    CONSUMED at its gate 2026-09-08 07:35 VN
                                    — cycle in scored execution; dead for any
                                    future use per P-8)
GO STOCKS V12 SCORED EXECUTION     (live plan plans/PLAN_stocks_v12.md)
GO FOREX V8 SCORED EXECUTION       (live plan plans/PLAN_forex_v8.md)
```

The stocks V11 and forex V7 phrases were each consumed at their own gates
(2026-09-07) and are dead with their closed cycles; the crypto V15, forex
V6 and all earlier phrases are likewise dead. Expired/consumed phrases
never carry forward (V6 ruling; P-8).

## 8. The one-paragraph spirit

This factory does not optimize for beautiful backtests; it optimizes for
**trustworthy conclusions, cheaply reached and permanently recorded**. A
negative result with full evidence is a success. A thin survivor with
unevidenced assumptions is the most expensive failure the program knows
(forex V3 paid for P-1..P-6). Freeze the rules while calm — they are the
only thing that holds when the number is beautiful and wrong (P-6).

## 9. Mechanism status ladder (governance; see `research/wayfinder/FAMILY_PIPELINE.md`)

Ladder: `DOCUMENTED -> IMPLEMENTED -> TESTED -> ADOPTED_BY_ACTIVE_CYCLE`.
A mechanism reaches IMPLEMENTED/TESTED only after its code and tests
pass; ADOPTED only when a cycle's live plan preregisters it. Frozen and
running cycles are never retrofitted (adoption boundary: crypto V16+,
forex V7+, stocks V12+).

```text
FAMILY_PIPELINE protocol              DOCUMENTED (merge candidate on branch
                                      orca/governance-family-pipeline — standing
                                      standard only upon owner merge to main)
FAMILY_FAILURES registry + validator  IMPLEMENTED + TESTED (54 governance tests green;
                                      50 entries, git --verify PASS); adopted only at
                                      the first cycle close that appends under it
diagnostic persistability gate        IMPLEMENTED + TESTED, round-2 hardened (canon
                                      CATEGORY_REQUIRED_FIELDS — contracts cannot pick
                                      field lists; schema_id must resolve to the
                                      registered diag/<category>@1; relative-path-only
                                      artifacts; smoke runs in a fresh empty sandbox so
                                      stale artifacts can never PASS; BLOCKED_PRELAUNCH
                                      on any gap; runs BEFORE A7 launch authorization
                                      when adopted); adopted only at the first
                                      prelaunch that runs it
global heavy lock                     IMPLEMENTED + TESTED, round-2 hardened (machine-
                                      wide = this user on this host; home runtime
                                      outside every repository; fcntl.flock; registry
                                      PID+process-start-token; malformed registry or
                                      live-pid-with-missing/unrecoverable token =
                                      CONTROL_STATE_DRIFT fail closed; reclaim only on
                                      PROVEN pid-dead or DEFINITE token mismatch;
                                      cleanup holds the flock). Round-1 lock was
                                      ADOPTED by CRYPTO-V16 P0 (2026-09-07, runtime
                                      history 2 FAILED + 1 FINISHED); round-2 re-adopts
                                      on next acquisition
ADOPTED_BY_ACTIVE_CYCLE              heavy lock: round-1 yes (V16 P0 evidence);
                                      round-2 pending. gate/registry: not yet —
                                      marked adopted only when actually used
```
