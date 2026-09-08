# CRYPTO-V17 — THE INTRADAY MICROSTRUCTURE FRONTIER: SUB-DAILY AGGTRADES CLOCKS

> Owner plan dated 2026-09-08, drafted by the Lead Engineer from V16's
> measured terminal (verified from bytes at `46db31d` + canonical close
> `9d62d5c`). Activates on owner dispatch; nothing starts on its own. A
> correct `V17_REJECT_ALL` is a successful research run.
>
> `plans/PLAN_crypto_v16.md` and all earlier crypto plans/records are
> closed historical authorities.

## 0. Frozen starting point

```text
V16 terminal            46db31d + canonical close 9d62d5c (budget 6/6,
                       6/6 published; reproduction ALL_MATCH 60/60 files,
                       1854 leaves; A7 prelaunch AUTHORIZED with A7-side
                       recompute; owner exact GO after a form-refused
                       attempt — P-8 gate working)
V16 outcome             both families mechanically dead: CLOSE-DISPLACE-FADE
                       G2 PF razor (1.06356 vs 1.10, margin -0.0364,
                       plain negative, no shadow); RUNPERSIST G1 negative
                       with control OUT-EARNING (corroborating shadow).
                       D2 measured vetoes: A4-P1 elite-level 0.2225,
                       A5-P1 0.3385, A5-P2 0.3885; run_imb razor 0.1927
                       pooled (ETH-alone 0.2078 disclosed). The aggTrades
                       frontier is measured-exhausted at the DAILY clock
                       on BTC/ETH.
first governance cycle  V16 adopted and exercised gate + lock + registry
                       end-to-end; per-period series persisted (V16 DSR
                       NOT_RUN was historical-only: 152 prior Sharpes
                       never persisted — prospective deflation now
                       computable). V17 continues all three MANDATORY.
denominators           crypto 155/158; program 233 published / 236
                       observed (ledger authority, P-9); budget 0/6 for
                       V17; S1 SEALED_UNTOUCHED
durable assets         bounded aggTrades streaming pipeline (1.29B rows
                       reduced, RSS < 1 GiB proven, sha-pinned panel);
                       39-symbol-month keyless census incl SOLUSDT
                       (19.71 GB with SOL); publication/DSR kernel with
                       the diagnostic contract
the open axis          V16's plan granted daily-or-slower ONLY
                       (NOT_GRANTED_BY_DESIGN for sub-daily). The intraday
                       clock dimension of the tick panel is UNTESTED —
                       V17's frontier. V16's dead forms stay dead at any
                       clock: re-entering CDF/RUNPERSIST (or any D2-killed
                       form) at H1/H4/whatever is rescue; novelty rho vs
                       the V16 exposures is measured at D2 on conditioning
                       exposures.
```

## 1. What is closed and may not be rescued

The cumulative forbidden inventory through V16 (RULES §4), now including
the **day-boundary close-vs-VWAP displacement fade form** and the
**same-side run persistence form** at ANY clock/parameter/universe, the
D2-measured vetoes (elite-level, A5-P1/P2 forms), and the run_imb
corroborating shadow (recorded, never promotable). All priors stand: OI
term-structure, liquidity episodicity, OILEV-V2 + inverted shadow,
PREMFADE, BAB, carry, ILLIQ owner-gated, V15's elite-size-asymmetry /
taker-saturation / elite-level shadow. An intraday proposal that turns
out to be a dead daily form on a faster grid dies at D2 by measured
pooled rho.

## 2. Mission and allowed scope

V17 asks one question:

> Does SUB-DAILY (H1-class) reaction structure computed from the aggTrades
> panel — displacement, persistence and imbalance shapes at intraday
> clocks — carry incremental after-cost information at taker costs + stress
> tier 2.0, beyond the dead daily forms?

Cost realism is the named risk of this frontier: intraday books trade more
per unit edge, and crypto taker costs killed the daily PF razor (margin
-0.0364). Every lane's expected_failure_mode must name cost domination,
and the A9-F turnover/cost ceiling kill runs BEFORE selection.

Three sanctioned axes (wave diversity binding):

1. **intraday reaction structure** (mandatory lane): H1/H4-class
   displacement/imbalance/reaction books that are NEW mechanisms (not
   V16 forms re-clocked) on the BTC/ETH panel; sham/consistency controls
   mandatory per mechanism class (e.g. randomized session-boundary
   placebo for session-conditioned books; exposure-form controls for
   characteristic books).
2. **universe extension — SOLUSDT**: NEW daily-or-slower mechanisms on
   the 3-symbol panel (SOL census pre-measured, 2.34 GB; the high-beta
   attention alt is a structurally different participant mix); V16-dead
   forms on SOL remain vetoed; rho vs all forbidden exposures measured.
3. **open axis**: any literature-backed mechanism on authorized keyless
   Binance data in the non-forbidden space.

Binding rules carried: coverage-first (a source/clock that cannot fund S0
is COVERAGE_INSUFFICIENT_FAIL_CLOSED before proposals); cost charged
exactly once per fill (L-V14-0); stress tier 2.0 PRIMARY; margin-to-fail
per gate (P-2) with the V16 defect lesson — margins attributed per-arm
from emitted series; controls recompute under semantics change (P-3);
diagnostic contract MANDATORY (P-11); |rho| <= 0.20 pooled vs the full
forbidden inventory; exactly three arms; max six cells; unused slots
never reassigned.

Allowed terminal outcomes:

```text
V17_REJECT_ALL
V17_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
V17_BLOCKED_DATA_OR_SELECTION
V17_BLOCKED_PRELAUNCH
V17_INCOMPLETE_NOT_PROMOTABLE
```

`BLOCKED_DATA` is live and cheap: if the intraday reduction breaches the
frozen RSS/disk/serial ceilings, or the intraday panel cannot fund the S0
window with the 1-day-purge fold contract, the axis dies in P0 before any
proposal exists.

## 3. Governance (mandatory, continuing)

As V16 (first full adoption): diagnostic persistability gate with
canonical per-period series contract — DSR must be computable at terminal
from persisted bytes over N = 158 + V17 cells; machine-wide heavy lock
(stderr tail on FAILED releases — the V16 P0 lesson); failure-registry
append at close.

## 4. Cycle structure (standard, deltas only)

- **P0 (A3)**: staging re-run under the streaming discipline — intraday
  reduction contract FROZEN before extraction (which sub-daily
  observables, which ceilings; SOL pull decision bound to lane-2
  viability per §2); license/coverage re-verified keyless; ceilings
  re-frozen from V16's measured margins (RSS 954.8 MiB proven — headroom
  re-derived, not assumed). Publish BEFORE D1.
- **P1**: kernel regression (cost-once L-V14-0 fixtures; DSR kernel now
  consuming persisted historical series where they exist).
- **P2**: coverage-first per proposal clock (intraday decision counts,
  warmup, fold population with the 1-day-purge contract).
- **P3**: invariants freeze incl. diagnostic_output_contract + per-arm
  margins attribution (V16 defect); no PnL.
- **D1/D2**: three blind lanes from one wave SHA; causal-claim +
  falsification-rule + expected-failure-mode frozen fields; novelty vs
  the full inventory (incl. V16 forms at the NEW clock — measured, not
  argued); control identifiability + A9-F turnover/cost ceiling measured
  pre-selection.
- **I/Q**: availability-lag mutation per conditioning field; exact-arm
  sanitized dry-run, non-vacuous, recursive leak scan; twins at freeze +
  twin smoke-rerun; heavy phases (staging, full suite, scored) under the
  machine-wide lock.
- **E**: max six serial cells after the two-key HARD STOP — A7
  fresh-context first (diagnostic gate in scope), then the owner types,
  fresh and informed:

```text
GO CRYPTO V17 SCORED EXECUTION
```

- **Terminal**: reproduction from the twin; DSR over the crypto program
  history (N = 158 + V17 cells) from persisted series; PBO fail-closed
  below 8 configurations; margins per gate per arm; failure-registry
  append; program totals as-of-intake (P-9).

## 5. Hard boundaries

Unchanged from V16: keyless Binance public data only (no key, no signup,
no purchase by agents); no S1/paper/live/orders; no raw-data commit
(sha256 manifests only); no optimizer/rescue/threshold weakening; no
history rewrite; pushes only on owner instruction; gates report
PASS/FAIL/NOT_RUN/BLOCKED with commands, exit codes, SHAs and margins;
heavy jobs serialized machine-wide UNDER THE LOCK (sibling cycles V12/V8
respectfully wait — NOT_RUN_RESOURCE_CONFLICT, never contention).

## 6. First report from a fresh A1

```text
measured UTC / root / branch / HEAD / porcelain
V16 terminal + canonical close chain verified; crypto 155/158, budget 0/6, S1 seal
governance mechanisms verified on-branch (tests + registry --verify, 55 entries)
intraday reduction contract draft + ceiling margins re-derived from V16 measured
keyless coverage re-check (BTC/ETH +/- SOL census pins)
GO/NO_GO for P0
```
