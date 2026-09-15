# PLAN STOCKS-NG4 — off-exchange short-sale-volume pressure

> Status: `PLANNED_NOT_STARTED` (2026-09-15). This cycle follows the measured
> STOCKS-NG3 P0 data-entitlement close. It uses no purchased data and starts
> with a source/meaning census. A P0 close with zero scored cells is a valid
> result. Nothing in this plan is evidence of profitability.

## 0. Cycle identity

```text
cycle_id          STOCKS-NG4
asset             stocks
plan              plans/PLAN_stocks_ng4.md
branch            orca/stocks-ng4-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng4/integration
budget            6 scored cells max / 2 families max
go_phrase         GO STOCKS NG4 SCORED EXECUTION
S0                OPEN — screening only
S1                SEALED_UNTOUCHED
orders            NONE — no paper, testnet or live orders
```

`PROSPECTIVE-SHADOW-V1` remains independent and `ACTIVE_LIGHT`. This cycle
must not read its PnL, trades, marks or verdicts when proposing or selecting.

## 1. Question, in simple language

FINRA publishes how much reported off-exchange trading was marked as a short
sale for each US symbol. We ask one narrow question:

> After removing ordinary trading activity, momentum, volatility, sector and
> calendar effects, does an unusual change in FINRA off-exchange short-sale
> volume contain repeatable information about later returns?

Direction is not assumed. Outcome-blind proposal lanes may preregister either
continuation or reversal mechanisms before any scored return is visible.

This is **not short interest**. It is **not borrow fee**. It is **not proof
that traders are bearish**. Market makers can create reported short volume
while helping a customer sell a long position. Any family that relies on the
forbidden interpretation dies before scoring.

## 2. Why this is a new cycle

- The repo has a discovery-only FINRA adapter and offline fixtures, but no
  scored FINRA short-sale-volume family in the frozen ancestry.
- The observable is materially different from STOCKS-NG3 earnings history,
  filing lag, Form 4, dividends, accounting levels and price-only families.
- Novelty is only a proposal claim until the exact D2 ancestry measurement
  passes. Similarity beyond the frozen threshold kills the proposal.

## 3. Source authority and P0 kill gate

Primary source: FINRA Consolidated NMS Daily Short Sale Volume files:

```text
https://cdn.finra.org/equity/regsho/daily/CNMSshvolYYYYMMDD.txt
```

Officially documented facts to re-capture in committed evidence:

- consolidated NMS history begins 2018-08-01;
- publication is no later than 18:00 ET on the trade date;
- rare later updates can occur and must be represented as revisions;
- data is off-exchange publicly disseminated activity, not a consolidated
  all-venue picture and not short interest;
- FINRA describes the data as free for non-commercial use, subject to its
  current terms and attribution requirements.

The existing adapter is **known stale and must not be trusted**. The current
official URL differs from its discovery URL. Real files use compact dates and
multi-facility market codes; current files may contain fractional share
volumes. P0 must repair and independently test these schema regimes before any
proposal lane opens.

P0 passes only if all gates below pass:

```text
F1 AUTHORITY
   Pin current official documentation, terms, attribution and a written
   internal-research compatibility verdict. Ambiguous or incompatible terms
   => terminal close, not an inferred PASS.

F2 LIVENESS + HISTORY
   Fetch real non-holiday canaries at the beginning, middle and recent end of
   the documented window. Validate status, content type, header, trailer when
   present, non-HTML body and raw SHA-256. At least two retrievals of the same
   dates test silent mutation/revision behavior.

F3 PARSER
   Replace the stale request path and support documented observed regimes:
   YYYYMMDD dates, one-or-more comma-separated facility codes and exact
   non-negative decimal share quantities. Never coerce Decimal to binary
   float. Enforce short_exempt <= short <= total and fail closed on unknown
   schema. Offline fixtures cover integer, fractional, malformed and revision
   cases; a live canary contract test remains explicitly network-gated.

F4 AVAILABILITY
   Freeze one conservative rule for every row: no same-session decision.
   Earliest eligible decision is the first regular session open after the
   documented 18:00 ET deadline. Later updated files retain vintage identity;
   current bytes may not impersonate the original vintage.

F5 COVERAGE + SURVIVORSHIP
   Measure 2018-08-01 through the latest completed trade date: sessions,
   symbols, missing files, duplicate rows, schema regimes and per-year
   coverage. Map against the pinned death-inclusive stock cohort and prove
   at least two delisted-name pre-death histories plus never-existed controls.
   Symbol renames/classes are explicit mappings, never fuzzy joins.

F6 MEANING + DENOMINATOR
   FINRA TotalVolume is the denominator for the primary FINRA-only ratio.
   It must never be presented as consolidated market volume. If an external
   consolidated-volume normalization is proposed, it is a separate arm with
   its own availability and authority proof.

F7 POPULATION
   Freeze three chronological folds before return measurement. Each fold must
   have >= 250 eligible entity-decisions in each proposed family and the most
   recent 24 months must contain >= 100 unique eligible symbols. Failure means
   `STOCKS_NG4_BLOCKED_DATA_OR_SELECTION`, budget 0/6.

F8 REPRODUCIBILITY
   Commit the census code, raw-request manifest, digest manifest, schema
   report, availability contract, cohort mapping and frozen fold boundaries
   under research/control/stocks_ng4_run/. A detached rerun must reproduce
   census counts and digests or explicitly identify a source revision.
```

P0 is source engineering and census only. It may inspect price/cohort metadata
needed for joins, but may not compute strategy returns, PnL, PF, Sharpe,
drawdown, survivors or S1 evidence.

## 4. D1 outcome-blind proposal contract

Only after P0 PASS, dispatch two independent proposal lanes. They may see the
P0 schema, coverage and frozen folds, but no scored outcomes.

Each proposal must specify one causal mechanism, formula, direction logic,
lookback, rebalance rule, holding period, universe filters, turnover estimate,
missing-data rule, falsifier and all mandatory controls. Maximum two family
identities enter D2; variants are arms inside a family and consume declared
trial identities.

No proposal may call the field sentiment, crowd bearishness, short squeeze
probability, borrow scarcity or short positioning without separate authorized
evidence. Such a proposal is invalid rather than repairable by wording.

## 5. Mandatory controls and killers

Every proposal carries:

```text
C1 TOTAL-VOLUME-ONLY      same construction without short-sale information
C2 UNSIGNED-ACTIVITY      magnitude/activity control without directional sign
C3 PRICE MOMENTUM         frozen short/intermediate momentum controls
C4 VOLATILITY/LIQUIDITY   vol level, dollar volume and Amihud-like ancestry
C5 SECTOR + MARKET        sector-residual and SPY-excess representations
C6 CALENDAR               weekday, month-end and holiday-distance controls
C7 FACILITY COMPOSITION   test whether changing B/Q/N mix explains the signal
C8 SIGN/INVERSION         continuation and reversal cannot both receive credit
C9 STALE/LAGGED           lag placebo and shuffled-within-date valid nulls
C10 ANCESTRY RHO          pooled absolute rho <= 0.20 on frozen decision grid
C11 PIT MUTATION          one-session-earlier mutation must change/refuse book
C12 NULL VALIDITY         autocorrelation and population of each null reported
```

If a price/volume/liquidity shadow explains the anchor, the FINRA family dies.
If facility composition cannot be compared consistently across schema regimes,
the affected window is excluded by the preregistered rule or the family dies.

## 6. D2 feasibility and novelty gate

D2 may calculate only preregistered non-scored diagnostics: exact-grid
ancestry correlations, eligible decision counts, turnover, missingness,
concentration and cost/borrow feasibility. It cannot inspect candidate return
performance.

D2 PASS requires all of:

- pooled absolute ancestry rho <= 0.20;
- every fold populated under F7;
- expected turnover can be charged under the frozen stocks cost bands;
- any short leg has an explicit conservative borrow/financing convention;
- no family identity is a relabelled volume, momentum or liquidity family;
- proposal and arm hashes freeze before sanitized dry-run.

Otherwise selection is empty and the cycle closes at 0/6.

## 7. Trading, costs and risk contract

```text
decision        first regular-session open strictly after source availability
entry           next executable session open under the frozen daily-bar rule
exit            preregistered holding window; force-flat at fold boundary
universe        P0-evidenced death-inclusive cohort only
costs           frozen stocks band-cost schedule, charged once per fill
financing       raw and financing-adjusted books both required
gross cap       1.0
symbol cap      0.10
market control  SPY-excess and sector-residual books both reported
stress          frozen tier 2.0 plus break-even cost margin
```

No claim may rely only on gross or pre-borrow performance.

## 8. Execution phases and ownership

```text
P0  source authority, parser repair, PIT/coverage/death census
D1  two independent outcome-blind proposal lanes
D2  independent feasibility and ancestry measurement
S   selection + exact arm/data/fold/config hash freeze
I   isolated implementation lanes; A1 integrates one handoff at a time
Z   sanitized exact-arm dry-run and recursive leak scan
A7  fresh-context independent prelaunch audit; zero unresolved HIGH/CRITICAL
GO  owner types exact registered phrase; early/paraphrased GO is unconsumed
E   at most 6 scored cells under the machine-wide heavy lock
R   detached reproduction from committed artifacts
T   terminal audit and two-half close
```

All delegated lanes must write `zcode_orch_v3_handoff@1` JSON to their exact
dispatch path. Lanes never merge, rebase, push, edit registries/ledgers or read
other lane outcomes. A1 alone integrates by commit identity and reruns targeted
tests after each pick.

## 9. Trial accounting and result language

Observed and published trials are counted separately. Every scientifically
computed cell consumes one observed slot even if publication fails. Unused
slots are not reassigned. `D2 eligible` means only “allowed to be tested”; it
does not mean profitable, robust or promotable.

Stage-A thresholds, exclusion zone, concentration, fold-positive, PF,
expectancy, MDD, stress, break-even and drop-one rules must be frozen before E.
Every reported gate includes margin-to-fail and per-period series. S1 remains
sealed unless a later, separate owner decision opens it.

## 10. Prewritten terminal outcomes

```text
STOCKS_NG4_BLOCKED_SOURCE_OR_SCHEMA
STOCKS_NG4_BLOCKED_DATA_OR_SELECTION
STOCKS_NG4_BLOCKED_PRELAUNCH
STOCKS_NG4_REJECT_ALL
STOCKS_NG4_INCOMPLETE_NOT_PROMOTABLE
STOCKS_NG4_TECHABORT_PRESERVED
```

A correct early close is success of governance, not failure of engineering.
This plan contains no predeclared survivor outcome.

## 11. Boundaries

- No paid source, signup, API key or credential request.
- No S1 access and no paper/testnet/live orders.
- No score before A7 authorization plus the fresh exact owner GO.
- No pushes or writes to `.zcode/`.
- `CYCLE_REGISTRY.json` changes only through `researchctl`.
- One heavy job machine-wide; never kill a foreign worker.
- Shadow valuation remains light and independent.

## 12. Immediate actions

```text
1. Commit this plan by exact pathspec in the root owner checkout.
2. Obtain an independent, fresh-context adversarial plan audit.
3. Remediate every valid HIGH/CRITICAL finding.
4. Register STOCKS-NG4 through researchctl as PLANNED_NOT_STARTED.
5. Bootstrap its integration worktree and dispatch P0 only.
6. Stop at the scored prelaunch gate and wait for the exact owner GO.
```
