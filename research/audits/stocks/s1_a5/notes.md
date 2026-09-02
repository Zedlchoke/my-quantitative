# S1 A5 — accounting identity, borrow/dividend, execution costs

Owner: A5 lane (`orca/stocks-s1-accounting`), bootstrapped at
`a04b8d1b90a3cc079ddf6a726eea9cff86a0a9df`. Implements PLAN_stocks.md §7 A5
against the frozen common core (`research/assets/common/{contracts,
carrying_cost,execution_cost,trial_identity}.py` — never edited).

## Deliverables

| File | Contents |
|---|---|
| `research/assets/stocks/accounting.py` | canonical identity (`IdentityTerms`, float tolerance + exact-Decimal path), `IdentityLedger` (USD cash, average-cost positions, per-symbol buckets), borrow/dividend section (`BorrowLocate`, `submit_short_sale`, `compute_borrow_fee`, `accrue_borrow_fee` via ledger, `apply_dividend`, `StockBorrowDividendCarry` implementing the frozen `EquityBorrowDividendCarry`), `ObservableEvent` + `last_executable_event` |
| `research/assets/stocks/execution.py` | `CommissionSchedule`, `SpreadPolicy` (quotes, else explicit bps proxy; quotes win, no blending), `ImpactModel` (sqrt participation + hard cap), `EquityExecutionModel` implementing frozen `ExecutionCostModel` (`model_id` = `CostModelId`, `digest` = sha256 over canonical params), `attempt_fill` fail-closed decisions, one-event entry delay helpers |
| `research/assets/stocks/portfolio.py` | `SharedCapitalReplay` (N arms, one USD account, per-arm attribution books with starting equity 0), `ReplayArm` interface + `OrderIntent` (no strategy logic), `positive_pnl_shares` concentration helper |

## Canonical identity (PLAN §7 A5, verbatim terms)

```
ending_equity - starting_equity
= realized_price_pnl + terminal_pnl + cash_dividends
  - commissions - spread - slippage - market_impact
  - short_borrow_fees - short_dividend_liability - rejection_costs
```

* Float path: `math.fsum` on both sides, frozen tolerance
  `FLOAT_IDENTITY_TOLERANCE_USD = 1e-9`; breach raises `IdentityBreakError`
  (gate SD3 "isolate first mismatching ledger row": residual, lhs, rhs and all
  terms are in the message).
* Exact path: `identity_residual_exact` / `assert_identity_exact` convert terms
  via `Decimal(str(v))`; goldens written as decimal strings close to exactly
  `Decimal("0")`.
* Accounting conventions that make the identity close by construction:
  average-cost positions; `realized_price_pnl` on every fill that reduces a
  position; `terminal_pnl += qty * (mark - avg_cost)` (sign-correct for
  shorts); equity = `cash + Σ qty*mark` (mark-to-market). Short-sale proceeds
  STAY in cash (verified by golden: long→short cross leaves cash 13,500 on the
  blended trade).

## Terminal valuation — fail-closed

`mark_terminal` accepts ONLY executable events (non-executable prints are
never marks); `finalize_terminal(symbol, events)` picks the LAST executable
one via `last_executable_event` and raises when none exists. Double-marking a
symbol raises. `identity_terms()` raises while any open position is unmarked
(there is no equity without a terminal valuation). A later non-executable
print is ignored (golden: mark 52.00 kept, later 55.00 halted print ignored).

## Borrow / dividend rules

* PIT locate record per short (`BorrowLocate`): available=True REQUIRES a
  rate; available=False must NOT carry one (no invented data).
* `submit_short_sale` / `SharedCapitalReplay.submit_intent`: missing locate,
  symbol mismatch or unavailable borrow REJECT the short with cost 0.00 —
  never filled free. Rejection is recorded as evidence (`OrderRejection`).
* Borrow fees accrue only while a short is HELD: accrual on a flat/long
  symbol raises. Fee = `price * qty * PIT_rate * days / 360`
  (`BORROW_DAY_COUNT_BASIS = 360`).
* Ex-date dividends: long → `cash_dividends += dps*qty`; short →
  `short_dividend_liability += dps*|qty|`; flat → nothing.
* `StockBorrowDividendCarry` (frozen common carry interface) emits signed
  `CashflowLine`s: BORROW −fee at interval end; DIVIDEND ±dps*qty at each
  event; flat position → no lines; short without PIT rate/mark raises.

## Execution cost model (frozen `ExecutionCostModel` interface)

* BUY fills at ask, SELL at bid; `spread_cost = qty * (ask-bid)/2` (half-spread
  vs mid). Proxy: `mid * proxy_bps / 2 / 1e4`. Quotes win over proxy; crossed
  quotes are a data error; no quotes + no proxy → `MISSING_QUOTE` NO_FILL.
* Commission: `max(per_share*qty, min_per_order)`.
* Slippage: `qty * fill_price * slippage_bps / 1e4`.
* Impact: `coefficient * price * qty * sqrt(qty/ADV)`; `qty/ADV >
  max_participation` → `PARTICIPATION_CAP` NO_FILL (no partial fills);
  coefficient>0 without ADV → `MISSING_ADV` NO_FILL.
* Fail-closed decision order: HALTED → SESSION_CLOSED → MISSING_QUOTE →
  MISSING_ADV → PARTICIPATION_CAP. NO_FILL decisions carry zero cost, a
  non-empty reason, and never touch the ledger. Session/halt state arrives as
  explicit bool flags (calendar is another lane's module).
* One-event entry delay: `next_executable_event_index` returns the first
  executable index STRICTLY AFTER the signal (never the signal event); None =
  entry never executes.
* Model is a frozen dataclass; `digest` = sha256 over canonical JSON of the
  full parameter set (sensitive to every param; byte-stable).

## Portfolio — shared capital

One USD account, N arms. Each arm owns an `IdentityLedger` attribution book
with starting equity 0; `shared_cash = starting_equity + Σ arm cash deltas`.
Identity closes PER ARM and for the account; account terms are field-wise
sums of arm terms (golden: 2 arms, 4 symbols, both levels close to 1e-9).
`submit_intent` locate-gates any SELL that would open/increase a short
(reducing a long needs no locate). Concentration: `positive_pnl_shares` —
per-symbol PnL (realized + terminal + dividends − costs), positive parts only,
share = part/Σ positive; `{}` when nothing is positive.

## Hand-computed goldens (all literals in tests, arithmetic in comments)

* Long round trip: 10,000 → BUY 100@50.01 (comm 1.00, spread 1.00) → SELL
  100@50.99 (comm 1.00, spread 1.00): cash 10,094; Δ94 = 98 realized − 2 − 2.
* Terminal on last executable event: Δ197 = terminal 199.00 (=100*(52−50.01))
  − 2.00.
* Short round trip with carry: 10,000 → short 100@49.99 (2.00 costs) → div
  0.50/sh (−50.00) → borrow 50*100*0.036*10/360 (−5.00) → cover 100@48.01
  (2.00 costs): cash 10,139; Δ139 = 198 − 2 − 2 − 5 − 50.
* Locate-rejected short: no fill, no cash movement, zero-cost rejection
  record; identity Δ0.
* Long dividend: Δ23 = 25.00 (0.25*100) − 2.00 commissions.
* Exact Decimal: 10094−10000 = 98−2−2 exactly (`Decimal("0")`); penny-off
  payload raises.
* Impact: 0.5*100*100*sqrt(100/1e6) = 50.00; with quotes fill 100.01 →
  50.005; total 51.005 = spread 1.00 + impact 50.005.
* Two-arm shared account: TREND terminal 498.50 (499.50−100.50+99.50), MR
  199.00; account 100,000 → 100,691.00 = terminal 697.50 − comm 4.00 −
  spread 2.50.

## Assumptions / decisions

1. `rejection_costs` is a first-class identity term (venue reject fee may be
   non-zero) but locate/halt rejections book zero cost per PLAN SD4 intent.
2. Terminal marks and borrow/dividend/borrow-rate records arrive as explicit
   inputs; no dependency on A3/A4 modules.
3. Ledger books USD only (any other currency is a construction error).
4. Tests never write to the repo (`test_importing_stocks_modules_writes_nothing_to_the_worktree`
   pins this); bytecode caches are gitignored.
5. Suite files use plain `research.assets.stocks.*` imports: works both in
   this lane (namespace packages, no `__init__.py` created) and at
   integration (other lane's `__init__.py` present).

## Verification (lane, via `/Users/hoangminhlong/my-quantitative/.venv/bin/python`)

```
pytest tests/assets/stocks/test_accounting.py      -> 21 passed
pytest tests/assets/stocks/test_borrow_dividend.py -> 14 passed
pytest tests/assets/stocks/test_execution.py       -> 22 passed   (57 total)
compileall research/assets/stocks research/assets/common -> ok
git status --porcelain=v1 before == after suite (only this lane's new files)
```
