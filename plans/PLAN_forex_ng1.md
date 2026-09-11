# PLAN FOREX-NG1 — next-generation forex cycle on platform v3

> Status: `PLANNED_NOT_STARTED` (registered 2026-09-11).
>
> Generation note: first forex cycle on the research platform v3 data plane;
> `ng1` generation opened by the owner's standing directive of 2026-09-11.
> A correct `FOREX_NG1_REJECT_ALL` is a successful research run.

## 0. Owner directive and authority

Owner instruction, verbatim (2026-09-11): identical standing directive as
`plans/PLAN_crypto_ng1.md` §0 (open crypto_ng1/forex_ng1/stocks_ng1 on the
new system + old lessons; full Lead autonomy; one-shot run; terminal
output).

Standing GO delegation (P-8 adaptation, recorded here and in the registry):
at this cycle's own prelaunch gate, AFTER independent A7 publishes
`FOREX_NG1_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL, the
Lead (A1) types the GO decision under the owner's standing delegation.
Scope excludes S1 opening, push/merge to `main`, purchases, keyed signups,
credentials, live/paper/testnet. A7 REFUSED => no GO.

GO phrase (typed only at this cycle's own gate):

```text
GO FOREX NG1 SCORED EXECUTION
```

## 1. Prior verdicts and forbidden ancestry

- FOREX-FREE-V7 `FOREX_FREE_V7_REJECT_ALL`: cross-economy spillover and
  lead-lag both dead AND control-killed (cluster #12) — "the
  reaction-direction class is CLOSED on both sides of the economy
  boundary".
- FOREX-FREE-V8 `FOREX_FREE_V8_REJECT_ALL` (falsification-by-control #14,
  budget 3/6): slope-dispersion "expectation mechanism" exposed as a
  nominal-yield-LEVEL exposure by the DGS10 level control; parameterization
  rejected by neighbour z504 out-earning anchor. LESSON MADE LAW: a
  nominal-exposure control is MANDATORY on every yield/inflation lane.
- FOREX-FREE-V9 `FOREX_FREE_V9_BLOCKED_DATA_OR_SELECTION` (0/6): all four
  D1 proposals measured-dead at D2 (pooled rho vs V8 nominal-level shadow
  0.2599/0.4842/0.3034/0.3119); P0 CPI census kill test PASSED (funded
  non-US {GB, CA, AU, NZ} + US via vintaged archives — the CPI index-level
  door is OPEN, contrary to the registry's pre-D2 note); P-12 originated
  here (representation identity committed with the measurement).
- V9 HIGH finding BINDING on this cycle: GB/CA legs implemented on
  current-vintage revised-in-place tables are FORBIDDEN; all non-US legs
  MUST come from the vintaged channel (S3 archives).
- BLOCKED: non-US real-yield/breakeven series (absent from keyed
  FRED/ALFRED catalog). Re-entry only via a NEW evidenced non-FRED
  authority preregistered in a future plan — NOT this cycle.
- Canonical inventory: `research/wayfinder/FAMILY_FAILURES.jsonl` +
  `research/wayfinder/HYPOTHESIS_LEDGER.md`, pooled with H0 hygiene rows.

## 2. Objective and terminal outcomes (frozen before any proposal)

Objective: test whether CPI-print deviation structure around PIT-evidenced
announcement instants (surprise measured against FROZEN naive predictors of
realized vintages — no consensus data anywhere) carries after-cost
expectancy on the daily 16:00-NY decision grid that no dead
reaction-direction/nominal-level family can explain.

Terminal outcomes (preregistered, negative-first):

```text
FOREX_NG1_REJECT_ALL
FOREX_NG1_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
FOREX_NG1_BLOCKED_DATA_OR_SELECTION
FOREX_NG1_BLOCKED_PRELAUNCH
FOREX_NG1_INCOMPLETE_NOT_PROMOTABLE
```

`BLOCKED_DATA is live and cheap`: if the S2/S3 CADS re-pin, the vintaged
GB/CA channel verification, or the announcement-instant PIT evidence fails
in P0, the cycle dies before proposals.

## 3. Data authority and platform v3 adoption (P0)

Frozen consumption set (exactly GRANTED S2/S3 series, nothing else):

- S2 FRED keyed vintaged evidence (V8/V9 classes): DFII10, DFII5, T10YIE,
  T5YIE, DGS10 (mandatory control series), CPIAUCSL — CADS address
  `07d1e0d5…`, 5 files, 0 drift.
- S3 forex vintaged CPI archives + print calendars:
  `GB/ons_d7bt_cpi_allitems.csv`, `CA/canada_allitems_nsa_2002_100_monthly.csv`
  + `CA/statcan_18100004.zip`, `AU/abs_640101_jul2026.xlsx`,
  `US/fred_cpiaucsl_rt.json`; print calendars GB/CA/AU/NZ + US and the
  announcement ledger (EMU v2, CA v3 pins) — GRANTED (GA4).
- Tail-trim law (V8 verdicts): vintaged feeds end ~2025-03..2025-06;
  the S0 window TRIMS accordingly; no current-vintage backfill, ever.

Adoption law: one per-asset adoption commit; consumption ONLY via
`consume_via_plane` (AuthorityRegistry verdict -> CADS resolve
verify-on-read -> manifest-verified frozen query); bounded shadow-parity
pilot (plane-read vs V9 staging bytes, digest equality on overlap) must
PASS before downstream lanes consume. FRED_API_KEY presence is not data
authority; P0 re-proves per series (V9 law). Every series outside the
frozen set stays BLOCKED_DATA.

## 4. Phases and gates

```text
P0  data authority + platform adoption (S2/S3 re-pin, vintaged GB/CA
    channel proof, announcement-instant PIT census, shadow parity)
P1  kernel/accounting inheritance (V8/V9 dual-book kernel; spread/cost
    constants re-measured Q-8)                        -> P1_GATE
P2  feasibility: recent-window print counts (Q-6), decision floor,
    warmup/coverage; lane dies cheap if under floor   -> P2_GATE
D1  blind proposal lanes (A4, A5) from one wave SHA
D2  novelty + feasibility MEASURED; code AND representation committed
    before any number is cited (P-12)
S   selection freeze (rubric §6 frozen BEFORE D1 dispatch)
I   implementation lanes (only if selection non-empty)
Z   exact-arm sanitized dry-run
A7  independent prelaunch audit
GO  Lead types GO under owner standing delegation
E   scored cells under machine-wide heavy lock (budget 6)
R   detached-twin reproduction
T   terminal A7 + two-half close
```

## 5. Cost, kernel and clock identity

- Clock: daily 16:00-NY decision grid (V9 frozen representation); decision
  instants at print publication timestamps; UTC/NY DST fixtures mandatory.
- Costs: measured spreads per pair at stress tier (Q-8: FX spread measured,
  never vendor-stated); cost once per fill.
- Kernel: V8/V9 dual-book accounting kernel inherited with compatibility
  tests; diagnostics 14-canon + prospective DSR (P-11); PBO fail-closed
  when cells < 8.

## 6. Proposal lanes (blind) and frozen selection rubric

Lane A4 — CPI print-deviation reaction: surprise = realized vintaged print
vs a FROZEN naive predictor (declared at proposal time, e.g.
seasonal-naive or trailing-YoY, frozen before any outcome). MANDATORY
controls: nominal-exposure control (V8 law), clock-only shadow (Q-7),
placebo on non-print days, and one falsification rule. No consensus data.

Lane A5 — cross-economy release-order information structure: within-month
relative timing of GB/CA/AU/NZ prints vs US as conditioning clock. Because
V7 closed the reaction-direction class, this lane MUST carry an explicit
V7-ancestry falsification control proving the signal is not a
reaction-direction form re-clocked; failure = D2 VETO (recorded).

Frozen rubric (before D1 returns; no threshold moves after any scored
number is seen):

1. Mechanism with forced/late participant; pass/fail.
2. Ancestry pooled |rho| <= 0.20 vs full inventory (incl. V8 nominal-level
   shadow and V9 vetoes); margin recorded (P-2).
3. Feasibility without PnL: print-count vs frozen decision floor on the
   RECENT window (Q-6); cost ceiling kill before selection.
4. Control battery runnable on the frozen representation; invalid-null
   distinction recorded (Q-11).
5. Max 2 families x 3 arms = 6 cells; budget 6; pairwise distinct
   arm_config_digest.
6. Ranking by preregistered evidence strength only; smoke numbers kill +
   disclose, never select (P-15).

## 7. Dry-run, prelaunch, GO, scored execution, reproduction

Identical structure to `plans/PLAN_crypto_ng1.md` §7 with
`FOREX_NG1_S0_LAUNCH_AUTHORIZED` as the A7 verdict key. Heavy lock
serialized machine-wide with the sibling ng1 cycles (yielding pattern §8 if
long idles). Reproduction detached twin; ALL_MATCH proves
self-consistency only (P-4).

## 8. Orchestration and evidence channel

Same law as `plans/PLAN_crypto_ng1.md` §8 with handoffs at
`research/control/FOREX-NG1/orchestration/handoffs/` inside this cycle's
worktree; single-cycle MCP store untouched; Flash pin disclosed (35ce190).

## 9. Hard boundaries

Same as `plans/PLAN_crypto_ng1.md` §9. Additionally: no consensus/forecast
data (no authority); vintaged-only non-US legs; nominal-exposure control
mandatory on yield/inflation lanes.
