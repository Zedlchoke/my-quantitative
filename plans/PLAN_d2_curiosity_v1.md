# PLAN D2-CURIOSITY-V1 — owner curiosity diagnostic: score three families killed at D2

> Status: `PLANNED_NOT_STARTED`. Owner instruction 2026-09-22 (intent,
> verbatim anchors preserved): halt STOCKS-SEARCH-V1; open `D2-CURIOSITY-V1`
> to run exactly 3 outcome/scored diagnostic cells for three families
> that were killed BEFORE scoring, answering "Nếu giữ nguyên ba
> construction cũ và thực sự tính outcome sau chi phí thì chúng lời hay
> lỗ?". Owner-authorized CURIOSITY experiment.

## 0. Cycle identity

```text
cycle_id     D2-CURIOSITY-V1
class        NON_GOVERNING_DIAGNOSTIC   (hard: never changes old verdicts)
budget       3/3 diagnostic outcome cells (one anchor per family; no
             neighbours, no parameter search, no rescue, no threshold
             change, no post-outcome change to universe/horizon/
             direction/folds/signal)
S1           SEALED_UNTOUCHED (every asset)
orders       NONE (no paper/testnet/live/broker/shadow deployment)
go_phrase    GO D2 CURIOSITY V1 THREE DIAGNOSTIC CELLS
forbidden    research/control/SANDBOX-OVERFIT-3ASSETS/ (never read,
             never used to choose or explain anything)
```

## 1. What this cycle is NOT

- NOT a reversal of the old D2 verdicts. The three kills stand forever:
  - `SFNG2-A4-P1` (STOCKS-NG2): 16/17 controls CLEAN but ONE control
    UNMEASURABLE.
  - `FXNG3-A4-P1` (FOREX-NG3): rho 0.2138 vs the 0.20 bar.
  - `CNG2-A5-P1` (CRYPTO-NG2): ordinary 29-shadow panel clean, but
    rho 0.4178 with the dead-FOMC form.
- NO result of this cycle may be phrased as D2 PASS, survivor,
  validated edge, production-ready; NO promotion to paper/shadow/live;
  NO writes into any old cycle's official denominator/ledger. This
  cycle keeps its OWN honest trial accounting: exactly 3 observed
  diagnostic cells (every computed cell consumes a slot even if
  reporting later fails; slots never reassigned).

## 2. The three cells (exactly three, verbatim constructions)

The exact construction of each cell is FROZEN from the source tree by
`research/control/d2_curiosity_v1_sources/*_identity.json` (extracted
from read-only reconstructions at the terminal SHAs), then committed in
the freeze artifacts before any outcome:

```text
SFNG2-A4-P1  amendment-delay structure      (STOCKS-NG2 @ 4e483bb…)
FXNG3-A4-P1  CA revision sign drift, USDCAD (FOREX-NG3 @ b3786a2…)
CNG2-A5-P1   pre-settlement funding-dodge   (CRYPTO-NG2 @ 71a29b1…)
```

Inheritance law: every inherited input carries source path + terminal
SHA + SHA256 digest. Old terminal cycles are read-only evidence; their
worktrees are reconstructed read-only if absent (done: /tmp/d2c_sources
for identity extraction; scoring inputs are the DATA artifacts, not the
old worktrees). Each asset keeps its OWN data contract, calendar, cost
model and accounting; shared code only with compatibility tests.

## 3. Freeze-before-outcome (all four committed before any PnL exists)

1. `source_identity_freeze.json` — terminal SHA + artifact digests per
   family, exact data inputs, exact implementation source.
2. `three_cell_contract.json` — the 3 cell IDs + exact signal
   construction, direction, entry/exit clock, holding period, universe,
   fold boundaries, warmup/purge/embargo, missing-data law
   (fail-closed, never imputed), tie-breaking law.
3. `cost_contract.json` — per-asset commission/spread/slippage/funding,
   stress tiers; NO silent zero cost.
4. `evaluation_contract.json` — after-cost realized/net PnL, gross,
   return %, CAGR (if horizon allows), max drawdown, profit factor,
   expectancy/trade, trades, win rate, fold-by-fold, exposure, turnover,
   cost attribution, concentration, benchmark/control comparison.

## 4. Data gate (fail-closed)

Scoring requires each family's frozen data inputs to be available at
the pinned digests (cached or re-fetchable under the SAME entitlement).
A family whose data cannot be bound is NOT improvised: the run
terminates `BLOCKED_DATA_OR_COST` with the failing family named.

## 5. Golden tests (must PASS before scoring; no outcome computed during
implementation)

no-lookahead (every decision's information set <= t) ·
next-available-bar execution · fold boundaries · cost debit ·
missing-data fail-closed · exactly-three-cell enforcement · S1 access
denial · zero-parameter-search enforcement.

## 6. Gates and phases

```text
I    implementation lanes (per-asset engines) + golden tests
Z    sanitized dry-run (no outcome)
A7   fresh-context audit: plan, source identities, three-cell freeze,
     data/PIT, costs, code, tests, absence of outcome leakage, S1
     sealed, exact 3-cell budget. A7 audits and writes artifacts only.
GATE stop: report plan path, worktree, branch, full HEAD, freeze
     digests, test results, A7 verdict path, heavy-lock state + the
     exact GO phrase. Owner GO must be typed AFTER the gate exists.
E    one atomic scored job: acquire heavy lock, run the 3 frozen cells;
     never peek cell 1 to alter cells 2-3; never rerun for bad results;
     record observed counter; release lock.
R    independent reproduce/reconcile; A7 terminal fresh-context audit.
T    terminal verdict, one of:
     DIAGNOSTIC_COMPLETE_NO_PROMOTION | DIAGNOSTIC_COMPLETE_TECHNICAL_FAILURE |
     BLOCKED_CONTROL_STATE | BLOCKED_DATA_OR_COST | BLOCKED_PRELAUNCH |
     TECHABORT
```

Scoring-gate preconditions (ALL): zero unresolved CRITICAL/HIGH ·
source/data gates PASS · cost contracts PASS · tests PASS · freeze
digests committed · clean worktree · heavy lock FREE_PROVEN · A7
prelaunch verdict allowing · fresh owner GO.

## 7. Final output

One table (per family: Gross PnL | Costs | Net PnL | Return % | PF |
MaxDD | Trades | Positive folds | Diagnostic verdict) + a
five-year-old explanation answering: which made money, which lost,
which merely mimics an old effect, which is too thin to believe — and
the no-promotion rule. The old D2 verdicts are reprinted verbatim.

## 8. Boundaries

No push, no merge to main, no edits to old cycles, no S1, no orders,
no reading of SANDBOX-OVERFIT-3ASSETS, registry only via researchctl,
one heavy worker machine-wide, never kill a foreign worker.
