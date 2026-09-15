# PLAN FOREX-NG5 — CFTC currency-futures positioning state on the spot grid

> Status: `PLANNED_NOT_STARTED` (2026-09-15). Authority: LESSONS.md P-19
> (owner verbatim 2026-09-11: a generation ending <= 6 scored cells / <= 2
> families opens ONE more full cycle from scratch) fired by the FOREX-NG4
> terminal close at 0 cells / budget 0/6 (`plans/CYCLE_REGISTRY.json`
> FOREX-NG4 row), together with the recorded NG3/NG4 reopening condition
> "re-entry needs a new evidenced information source". That condition is
> satisfied by the CFTC Commitments of Traders weekly positioning census —
> free, official, keyless, no-revision (FAQ-6, critic-verified) — an
> information source never consumed by any of the 29 dead forex families.
> Pre-cycle evidence: `research/control/forex_frontier_2026-09/`
> (survey_report.md, critic_report.md, probes/). A P0 close with zero scored
> cells is a valid result. Nothing in this plan is evidence of profitability.

## 0. Cycle identity

```text
cycle_id          FOREX-NG5
asset             forex
plan              plans/PLAN_forex_ng5.md
branch            orca/forex-ng5-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/forex-ng5/integration
budget            6 scored cells max / 2 families max
go_phrase         GO FOREX NG5 SCORED EXECUTION
S0                OPEN — screening only
S1                SEALED_UNTOUCHED
orders            NONE — no paper, testnet or live orders
```

`PROSPECTIVE-SHADOW-V1` remains independent and `ACTIVE_LIGHT`. This cycle
must not read its PnL, trades, marks or verdicts when proposing or selecting.

## 1. Question, in simple language

CFTC publishes, every week, how large leveraged non-commercial positions in
currency futures are. We ask one narrow question:

> After removing calendar/day-of-week structure, release-clock geometry,
> policy-rate-differential and rate-level shadows, and price momentum, does
> the measured state of the CFTC positioning census (crowding / build-vs-fade
> states on the frozen 16:00-NY daily grid) contain repeatable information
> about later spot FX returns on the existing TD spot legs?

Direction is not assumed; outcome-blind lanes may preregister continuation or
reversal mechanisms before any scored return is visible. The honest causal
claim is **state-conditioning only**: CME currency-futures open interest is
orders of magnitude below OTC G10 spot turnover, so the futures crowd cannot
force spot. No proposal may use forced-liquidation or positioning-drives-price
causal language — such a proposal is invalid, not repairable by wording.

## 2. Why this is a new cycle

- The 29 forex rows in `research/wayfinder/FAMILY_FAILURES.jsonl` consume no
  positioning census: not a relabel, lookback change or re-parameterization
  of any dead family. Nearest ancestors are cross-plane: crypto #17/V15
  positioning/clock kills and the same-source COMMODITIES-NG1 lineage. Per
  the program's own P-12/ancestry law (critic report §3), cross-plane
  closures transfer as MANDATORY CONTROL TEMPLATES, never as automatic
  measured vetoes; this plan adopts them as the G-D2-1 battery below.
- The source is new to this plane, free and official: cftc.gov bulk zips
  (HEAD + zip-magic verified live 2026-09-15), legacy 1986-01-15→,
  disaggregated/TFF 2006-06-13→, FAQ-6 "historical data is not updated once
  published" (critic-verified verbatim).
- Survey-closed alternatives (recorded with reopening conditions in
  critic_report.md §5-§6, binding as Q-10 conditions): D2 central-bank
  statement text (population/source gate fail) and D3 TIC flows
  (revisions/staleness fail) are FORBIDDEN as blind-proposal material for
  this cycle.

## 3. Source authority and P0 gates

Primary source: CFTC Commitments of Traders reports, bulk-file channel on
cftc.gov. The Socrata API door is 403 from this host (verified twice) and is
NOT used.

```text
A1 CENSUS CANARIES
   One full pre-2016 legacy-year zip pull; per-year market-code validation
   table for every used currency-futures code + USD-index across the used
   span (codes are not guaranteed stable across eras); dead and
   never-existed market-code controls per P-7. Failure => BLOCKED_SOURCE.
A2 AVAILABILITY (P-1)
   Per-release bytes-exist evidence incl. holiday-delayed weeks (release
   can slip 1-2 days). The release-schedule page is a rolling ~13-month
   window: per-cycle re-pin item. Exact or conservative decision times only.
A3 CORRECTIONS CENSUS
   CFTC Special Announcements corrections class censused and classified
   against the FAQ-6 no-revision claim; handling preregistered
   (annotate-and-keep vs exclude-window) before D2.
A4 SCHEMA
   Legacy long format vs disaggregated/TFF regimes parsed separately; exact
   Decimal for contract counts; fail-closed on unknown schema; offline
   fixtures for integer/malformed/revision cases; no binary-float coercion.
A5 COVERAGE + MAPPING
   Sessions, missing reports, duplicate records, per-year coverage;
   futures-code <-> existing-TD-spot-leg mapping explicit (no fuzzy joins);
   pairs without an entitled TD leg are out of scope, declared.
A6 FOLD FREEZE (at P0)
   Three chronological folds + the C7-analog exclusion rule frozen textually
   in the P0 census commit, before any D2 diagnostic exists.
A7 REPRODUCIBILITY
   Census code, raw-request manifest, digest manifest, schema report and
   frozen folds committed under research/control/forex_ng5_run/. Detached
   rerun reproduces counts and digests or identifies a source revision.
   Point-in-time freeze: later corrections never re-open folds.
```

P0 is source engineering and census only. No returns, PnL, PF, Sharpe,
drawdown, survivors or S1 evidence.

## 4. D1 outcome-blind proposal contract

Only after P0 PASS: two independent proposal lanes, one family identity
(forex positioning-state conditioning) with variants as arms consuming
declared trial identities. Proposals see P0 schema/coverage/folds only.
Each must specify causal mechanism (state-conditioning form), formula,
decision-grid rule, lookback, holding window, universe filters, turnover
estimate, missing-data rule, falsifier and all mandatory controls. Crowding
may not be called sentiment or proof of directional intent.

## 5. Mandatory vetoes and controls (the G-D2-1 battery)

All measured on the frozen 16:00-NY representation (P-12). **No E-stage cell
is funded unless the five G-D2-1 vetoes have all run measured and the anchor
survives all five** (G-Scope-1).

```text
V1 CLOCK BOOK         bare CoT release-clock book, same grid/hold/cost
                      geometry — kill if it out-earns the anchor or books
                      distinctness is unmeasurable (P-20 fail-closed None)
V2 GENERIC DAY-OF-WEEK named explicit veto — the CoT calendar is
                      Friday-clustered by construction (holiday-delayed weeks
                      push Mon/Tue); FOREX-NG4's rho 0.8883 class is the
                      exact killer; kill at the frozen ancestry bar
V3 POLICY-RATE-DIFFERENTIAL DIRECTION shadow — a DGS10-LEVEL control does
                      not cover the differential form; FXFV8-A4-P2's
                      carry_unconditional veto (0.3831) is the template
V4 DGS10 NOMINAL LEVEL program-law control (#14/#15)
V5 MOMENTUM + ANCESTRY pooled |rho| <= 0.20 vs the full same-plane shape
                      inventory and a price-only momentum shadow pool
S1 STALENESS SHAM     +1w/+2w delayed-state books must NOT reproduce the
                      anchor; Q-11 INVALID-NULL distinction explicit
S2 POPULATION         Q-6 recent-window floors frozen from census; decile-
                      state books only — tail-extreme-only designs forbidden
E1 COST CEILING (P-21) financing-inclusive worst-case round-trip ceiling
                      measured at P2; weekly holds make rollover first-order;
                      dual-book kernel (raw + financing-adjusted) required
```

## 6. D2 feasibility and novelty gate

Non-scored diagnostics only: exact-grid ancestry correlations for V1-V5,
eligible decision counts, turnover, missingness, concentration and the E1
cost ceiling. D2 PASS requires all vetoes survived, folds populated, costs
chargeable, no relabelled carry/momentum/clock family, and proposal + arm
hashes frozen. Otherwise selection is empty and the cycle closes at 0/6.

## 7. Trading, costs and risk contract

```text
decision        first 16:00-NY grid point strictly after release bytes exist
entry/exit      next executable session open / preregistered window;
                force-flat at fold boundary
universe        P0-mapped TD spot legs only (entitled files)
costs           frozen forex band schedule + P-21 financing convention
gross cap 1.0   symbol cap 0.10   stress tier 2.0 + break-even margin
```

No claim may rely only on gross or pre-financing performance.

## 8. Execution phases and ownership

```text
P0  A1-A7 gates (census, availability, corrections, schema, folds)
D1  two outcome-blind proposal lanes
D2  V1-V5 + S1/S2/E1 measurement, no scored outcomes
S   selection + exact arm/data/fold/config hash freeze
I   isolated implementation lanes; A1 integrates one handoff at a time
Z   sanitized exact-arm dry-run + recursive leak scan
A7  fresh-context prelaunch audit; zero unresolved HIGH/CRITICAL
GO  owner types exact phrase at its own gate; early GO dies unconsumed
E   at most 6 scored cells under the machine-wide heavy lock
R   detached reproduction; T terminal audit + two-half close
```

All lanes write `zcode_orch_v3_handoff@1` to their exact dispatch path.
Lanes never merge, rebase, push, edit registries/ledgers or read other lanes'
outcomes.

## 9. Trial accounting and result language

Observed and published denominators counted separately; every computed cell
consumes an observed slot. `D2 eligible` means only "allowed to be tested".
Expected modal terminal (per critic §8): a measured D2 kill by the clock,
day-of-week or carry-differential shadow — an acceptable outcome, paid at
near-zero scored cost. This plan contains no predeclared survivor outcome.

## 10. Prewritten terminal outcomes

```text
FOREX_NG5_BLOCKED_SOURCE_OR_SCHEMA
FOREX_NG5_BLOCKED_DATA_OR_SELECTION
FOREX_NG5_BLOCKED_PRELAUNCH
FOREX_NG5_REJECT_ALL
FOREX_NG5_INCOMPLETE_NOT_PROMOTABLE
FOREX_NG5_TECHABORT_PRESERVED
```

## 11. Boundaries

- No paid source, signup, API key or credential request; Socrata stays unused.
- No S1 access and no paper/testnet/live orders.
- No score before A7 authorization plus the fresh exact owner GO.
- No pushes or writes to `.zcode/`; registry only via `researchctl`.
- One heavy job machine-wide; never kill a foreign worker.
- Shadow valuation remains light and independent.

## 12. Immediate actions

```text
1. Commit this plan and the frontier evidence by exact pathspec.
2. Independent fresh-context adversarial plan audit.
3. Remediate every valid HIGH/CRITICAL finding; re-audit.
4. Register FOREX-NG5 through researchctl as PLANNED_NOT_STARTED.
5. Bootstrap the integration worktree and dispatch P0 only.
6. Stop at the scored prelaunch gate and wait for the exact owner GO.
```
