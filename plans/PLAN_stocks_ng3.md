# PLAN STOCKS-NG3 — earnings-surprise drift (consensus-free SUE) on the death-inclusive cohort

> Status: `PLANNED_NOT_STARTED` (2026-09-15, Lead discovery under the owner's
> 2026-09-15 live instruction to open the highest-value surviving cycle,
> standing on the frozen P-19 authority: a generation that ends with <= 6
> scored cells / <= 2 families opens ONE more full cycle from scratch — the
> new-assets generation closed 12 cells / 3 families at 0 survivors and
> STOCKS-NG2 closed 0/6 with the reopening condition recorded at the V8
> next_owner_path and the V12 close: "next stocks re-entry needs a materially
> new information set". PROSPECTIVE-SHADOW-V1 continues ACTIVE_LIGHT
> untouched). A correct
> `STOCKS_NG3_BLOCKED_DATA_OR_SELECTION` at any pre-scored gate is a successful
> research run. This plan authorizes NO scored cell until its own prelaunch
> gate passes both keys (A7 `AUTHORIZED`, then the owner's fresh exact phrase,
> P-8).

## 0. Cycle identity

```text
cycle_id          STOCKS-NG3
asset             stocks
plan              plans/PLAN_stocks_ng3.md
branch            orca/stocks-ng3-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng3/integration
budget            6 scored cells max / 2 families max
go_phrase         GO STOCKS NG3 SCORED EXECUTION   (REGISTERED_NOT_CONSUMED at registration)
S0                OPEN (screening only)
S1                SEALED_UNTOUCHED — never opened by this cycle
orders            NONE — no paper, testnet, live order, no credential request
```

## 1. The one hypothesis (simple, causal, falsifiable)

**Falsifiable causal hypothesis:** the market underreacts to the *magnitude and
sign of realized earnings surprises*; conditioning a book on consensus-free
standardized unexpected earnings (SUE = actual EPS minus its own seasonal
naive forecast, scaled by its own trailing surprise scale) produces drift in
the surprise direction that survives (a) the announcement calendar itself,
(b) price-momentum and disclosure-timing ancestry, and (c) after-cost,
after-borrow accounting on the death-inclusive cohort.

Mechanism reading: earnings information diffuses slowly (Bernard–Thomas
underreaction class). The tradable object is the SUE-signed drift window —
never the announcement-day reaction itself, never a price pattern.

Expected failure interpretation (prewritten): if the clock-only shadow earns
like the anchor, the edge is announcement-calendar geometry (RATES-NG1
falsification #16 class). If the sign-flipped arm earns the same, it is the
exposure form. If D2 measures rho > 0.20 vs momentum/filing-lag ancestry, the
class is a relabelled ancestor and dies pre-score.

## 2. Ancestry position and novelty claim

- 109-family failure registry contains **no earnings event family**: no SUE,
  no PEAD, no actual-EPS surprise observable has ever been measured on any
  asset (announcement-*clock* classes exist and are dead — CPI/FOMC/NFP
  instants, release windows, day-of-week — but none conditions on realized
  earnings surprise magnitude). This is a materially new information set on
  the stocks plane — the
  recorded STOCKS-NG2 reopening condition ("next stocks re-entry needs a
  materially new information set") is satisfied by the information source,
  not by a re-parameterization.
- NOT rescue: SFV10-A4-H1 (filing-lag level) is rejected ancestry; the
  filing-event and 10b5-1/amendment frontiers are measured-closed; the V13
  dividend-transition family is rejected ancestry. Earnings report dates and
  actual EPS are different observables with a different causal mechanism
  (surprise magnitude, not lag or event count). This claim must SURVIVE
  MEASUREMENT at D2 (pooled |rho| <= 0.20 on the frozen decision
  representation, P-12), or the cycle closes honestly.
- Disclosure duty: PROSPECTIVE-SHADOW-V1 observes three crypto families
  forward; no interaction (different asset plane, no shared state). This
  cycle must not read shadow ledgers or condition anything on them.

## 3. Data authority and the P0 census kill test (cheapest gate, before any proposal)

Authority source: the owner-entitled EODHD "All World" key (gitignored
`.env`, programmatic load only, never echoed — V8/V13 precedent). No new
purchase, no signup, no other provider.

P0 census (fail-closed, preregistered floors frozen HERE, before any lane
runs — FOREX-NG2 precedent):

```text
E1  per-ticker earnings history reachable under the EXISTING entitlement for
    the pinned cohort (living + delisted); entitlement gap => 404-class
    CANDIDATE_NOT_AUTHORIZED => terminal BLOCKED, no lane A4/A5 opens.
E2  usable SUE events (actual EPS + prior-year same-quarter EPS + trailing
    surprise scale all present) >= 400 in the most recent 24 months of S0
    (Q-6 recent-window floor), drawn from >= 150 unique entities.
E3  delisted-capability canary: >= 2 dead canaries (TWTR, SIVB class from
    the pinned death census) show real pre-death earnings records ending
    before their evidenced death dates; 3/3 never-existed controls absent.
    0/2 => survivorship-blocked => terminal BLOCKED.
E4  availability semantics: per-event timing field (BMO/AMC) coverage is
    MEASURED and the evidenced-timing share is PINNED in the census manifest;
    the uniform-fallback decision rule is FIXED IN THIS PLAN ex ante — if
    evidenced timing covers < 100% of sampled events, the conservative
    fallback (decide at the first session open strictly after the report
    date's close) applies to ALL events uniformly, never selectively
    (no selective-optimism channel exists by construction).
E5  PIT mutation battery: shifting a decision one session earlier must
    change the book (no-lookahead proof), BMO/AMC boundaries tested.
E6  sha-pinned census manifest (entity list, event list, floors measured,
    entitlement verdict, AND the frozen chronological fold boundaries with
    per-fold event counts) committed under
    research/control/stocks_ng3_run/p0_census.json. Fold boundaries freeze
    HERE, at the census, before any D2 measurement runs (P-15/P-21: nothing
    re-derived after numbers exist; the per-fold >= 60 floor of §3 is thus
    not boundary-shoppable).
```

Floors E1/E2/E3 are kill tests: any miss => registry phase
`STOCKS_NG3_BLOCKED_DATA_OR_SELECTION`, budget 0/6, cycle closes honestly
with the measured census as evidence. No floor is re-derived after
measurement (P-15/P-21).

S0 window: 2019-01-01..2026-08-31 candidate, narrowed to the census-evidenced
common window; prices from the pinned EODHD channel with the V8 probe canary
set re-run on this channel (P-7). Fold contract: 3 chronological folds,
preregistered boundaries at freeze; per-fold event population >= 60 or the
fold is UNPOPULATED and the family dies R3-class.

## 4. Universe, clock, fills, costs, financing, risk

```text
universe        census-evidenced entities on the death-inclusive cohort;
                no survivorship filter anywhere; dead-name exposure measured
decision clock  daily, first session open strictly after each event's
                evidenced-or-fallback availability instant (uniform rule)
entry           next session open after the decision; no intraday paths
holding         frozen in the proposal (drift window), force-flat at fold end
costs           band-cost schedule pinned from the V8-V13 stocks cycles,
                charged exactly once per fill; measured break-even floor
                reported per gate (P-2 margin-to-fail mandatory)
financing       short-leg borrow at the frozen program stocks convention;
                dual books: raw AND financing-adjusted, both reported
risk contract   gross cap 1.0; max symbol weight 0.10; sector-residual and
                SPY-excess books BOTH measured (V2 sector-beta law); stress
                tier 2.0 as frozen; MDD ceiling as frozen in Stage-A gates
```

## 5. Mandatory controls (declared killers, frozen before proposals)

Every proposal carries, and every verdict is adjudicated against:

```text
C1  CLOCK-ONLY SHADOW  announcement-calendar conditioning with SUE removed
    (Q-7 law: the event gets credit only for what remains above the clock)
C2  SIGN-FLIPPED SUE   placebo arm; must lose, else exposure-form kill
C3  SHAM-CALENDAR      shifted announcement dates on the matched cohort
C4  D2 ANCESTRY RHO    pooled |rho| <= 0.20 vs the declared veto inventory
    on the frozen decision-grid representation (P-12): momentum_63s,
    filing_lag_level (SFV10-A4-H1), vol_level, goodwill_bloat,
    cadence_latency, dividend_transition (V13), wc_accrual_flow,
    dep_reserve_coverage, day_of_week, declared-plan 10b5-1 forms,
    amendment forms, plus the full 15-entry ng1 veto set and ng2 kills
C5  Q-11 VALID-NULL CHECK  every permutation control's autocorrelation is
    measured; a control that reproduces the anchor is adjudicated kill vs
    invalid-null explicitly, never silently
C6  PIT MUTATION       §16.2 battery incl. one-event lag, timezone, DST
```

Stage-A gates: the standing frozen battery (expectancy > 0; PF >= 1.10;
fold-positive share; concentration ceiling; MDD ceiling; stress tier 2.0;
LOPO/drop-one; break-even floor; SPY-excess and sector-residual coherence),
thresholds pinned at the S selection freeze with the exclusion zone logged
(Q-12), margins-to-fail reported for every gate (P-2).

## 6. Phases, lanes and merge order

```text
P0  census (above) — Lead-run cheap gate under the machine-wide heavy lock;
    LANES NOT DISPATCHED until E1-E6 land. Kill here ends the cycle.
D1  outcome-blind proposal lanes (quant-explorer, never seeing scored
    outcomes): A4 primary lane — SUE-drift family, 2 proposals (anchor +
    structurally distinct neighbour form). A5 conditional lane — one second
    earnings observable ONLY if the census evidences an independent timing
    field with coverage (E4 strong); else A5 is NOT_RUN, disclosed.
D2  quant-implementer measurement lane: novelty rho (C4) + feasibility
    (Q-6 recent-window decision counts, turnover/cost ceiling A9-F,
    fold population) — computed pre-score, fail-closed.
S   selection freeze (rubric pre-exists this plan §5; selected hashes,
    arm_config_digest, data pins, budget, gates committed).
I   quant-implementer implementation lanes in isolated worktrees, one
    bounded task each; handoff zcode_orch_v3_handoff@1; A1 integrates one
    lane at a time, targeted tests after every pick.
Z   exact-arm sanitized dry-run, recursive scan, non-vacuous; degenerate
    populations (empty book) get explicit fail-closed verdict rows (P-23).
A7  independent fresh-context prelaunch audit (two-key #1). Required
    verdict STOCKS_NG3_S0_LAUNCH_AUTHORIZED, 0 unresolved HIGH/CRITICAL.
    STATE: PRELAUNCH_WAITING_OWNER_GO.
GO  owner types the fresh exact phrase at the cycle's own gate (two-key
    #2). Early or paraphrased GOs are recorded intent and die unconsumed
    (P-8). The standing delegation does NOT authorize this gate.
E   scored execution under the heavy lock, cells bounded by budget,
    per-period series persisted (P-11), trial identities exact (§15.1).
R   detached reproduction from committed bytes (ALL_MATCH or disclosed).
T   terminal + independent A7 terminal audit, then two-half close (§32).
```

Merge order: lanes -> orca/stocks-ng3-integration only; no lane merges,
rebases, pushes, or registry/ledger writes. A1 is the sole integrator.

## 7. Trial accounting

observed and published denominators counted separately; every scientifically
computed scored result increments observed even on publication failure.
Program totals read only from HYPOTHESIS_LEDGER.md (P-9). Budget 6/6 hard
cap; slots unused are dead, never reassigned.

## 8. Negative terminal outcomes (prewritten, first-class)

```text
STOCKS_NG3_BLOCKED_DATA_OR_SELECTION   census E1-E3 miss, entitlement gap,
                                       D2 all-veto, or selection empty
STOCKS_NG3_BLOCKED_PRELAUNCH           A7 prelaunch REFUSED past remediation
STOCKS_NG3_REJECT_ALL                  scored, no survivor (SUCCESS class:
                                       a correct falsification)
STOCKS_NG3_INCOMPLETE_NOT_PROMOTABLE   partial execution, verdict-defective
STOCKS_NG3_TECHABORT_PRESERVED         infra death, zero-budget honest stop
```

There is deliberately no SURVIVOR-carrying terminal in this plan text; a
survivor would be recorded only through the standing SURVIVORS.md contract
with margin-to-fail (P-2) and a fresh S1-owner decision. S1 stays sealed
either way.

## 9. Boundaries

S1 SEALED_UNTOUCHED; no paper/testnet/live orders; no credential requests
beyond the existing `.env` entitlement read; no pushes; no edits to
CYCLE_REGISTRY.json outside researchctl; PROSPECTIVE-SHADOW-V1 remains
ACTIVE_LIGHT and untouched; no writes to owner `.zcode/`; heavy lock
discipline machine-wide (one heavy job at a time).

## 10. Immediate next actions

```text
1. commit this plan (pathspec, atomic, root checkout)
2. independent fresh-context plan audit (adversarial, read-only)
3. remediate or record findings
4. register via researchctl (PLANNED_NOT_STARTED, budget 6, GO phrase)
5. land registry commit; PRELAUNCH chain (P0 census first) may proceed —
   scored execution may NOT, until its own two-key gate closes
```
