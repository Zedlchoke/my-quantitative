# BACKTEST_LAUNCH_DRAFT — FUTURES-BEHAVIOR-10SYMS (drafted 2026-10-02, lane BACKTEST-ENGINE-PREP)

STATUS: **DRAFT — NOT A GO.** Two blockers stand between this draft and any
launch: (1) data-depth decision (owner must choose vendor purchase vs
prospective accumulation vs accepting the ~14-month true-volume window), and
(2) registration — every arm below that produces return/PnL-linked selections
requires a future REGISTERED cycle with frozen budget/trial accounting before
a single scored run. Nothing here self-grants GO. The engine that would
execute this plan lives in `code/` (package `futbt`, 147 offline tests green
— 140 original + 7 close-only-fill-law regressions, audit M3 fix 2026-10-02).

## 0. Premises (measured, from FUTURES-DATA-10SYMS-V1, 2026-10-02)

- SIGNAL_RESEARCH_READY = PASS 10/10; DAILY_BT and INTRADAY_BT = BLOCKED 10/10.
- Front-month TRUE-volume continuous depth: ~2025-08→2026-10 (~14 months).
  Deeper per-contract daily bars are close-only settlement-derived (65-88%
  of bars per symbol, re-measured by our adapter smoke,
  `analysis/engine_adapter_smoke.json`) — reference/signal price only,
  NEVER fill price.
- Intraday H1/M1 ~10 recent months (NG ~2.2y). Daily BID/ASK 1y all symbols
  (not synchronous → not an executable spread).
- Quote conventions verified: 6J = USD per JPY (mult 12.5M JPY, minTick
  5e-7 = $6.25/tick, NO inversion anywhere); SI = COMEX 5000oz class SI.
- Roll rule (declared baseline, PIT-legal): hold until the LAST SESSION
  BEFORE day-1 of the expiry month (expiry month = month of the contract's
  last-trade date, i.e. the raw `expiry_month` header field — the CANONICAL
  basis per audit M2 reconciliation 2026-10-02, NOT the delivery month; S1's
  `expiry_date` is the delivery month and must not be used for this rule),
  roll to the next listed contract at that close. On this basis the rule is
  feasible for all 10 symbols incl. NG: NG fronts stop trading on the
  3rd-last business day of the month before delivery, so the roll session
  still precedes the front's final session by ~4 weeks (NGX26: LTD
  2026-10-28, roll 2026-09-30). A delivery-month reading would bind at the
  front's own final session — the same rule's boundary consequence, not a
  fork; see futbt/roll.py docstring and NG_DOSSIER.md §1.
- Costs measured/published: spread medians (USD/contract, close-to-close
  proxy): ES 12.5 · NG 20 · 6A 20 · 6E 18.75 · 6B 18.75 · 6J 25 · NQ 32.5 ·
  CL 30 · GC 50 · SI 112.5. Commission IBKR 0.85 + exchange + regulatory;
  only ES has a rendered all-in example (2.24). Slippage: NO declared value
  exists (NOT_RUN_NO_DECLARED_VALUE). Margins: broker-published (NinjaTrader
  2026-08-31, AMP 2026-10-02), CME SPAN NOT_RUN.

## 1. Arms and variants (proposed; exact rule set R to be frozen at registration)

| arm | data window | price use | fills | outputs allowed |
|---|---|---|---|---|
| A. Signal research (descriptive) | full per-contract daily depth 2019/20→2026-10 | settlement-derived closes DECLARED as reference prices | none (no orders simulated) | descriptive stats, regime tags, strict past/rolling windows only |
| B. Daily backtest (narrow-depth) | true-volume front chain 2025-08→2026-10 | raw TRADES prices | next-session open, tick-rounded, cost-shifted | journal + walk-forward + cost stress; NO parameter selection outside nested TRAIN |
| C. Intraday mechanism (descriptive) | H1/M1 ~10 months (NG 2.2y) | raw TRADES | none (no fill claims; M1 depth insufficient for execution studies) | session-profile descriptives, roll-window behavior |

Variants (cross-product within an arm):
- V1 roll rule: calendar baseline (default) vs PIT volume-migration rule
  (cutoff t-1, confirm 2 sessions) — framework test #11.
- V2 cost stress: ×1.0 / ×1.5 / ×2.0 on variable execution costs
  (spread + declared slippage).
- V3 declared slippage scenarios: S0 = none declared (costs flagged
  incomplete, no complete-cost claims) and S1..Sk = owner-declared nonzero
  values (REQUIRED before any Arm B pass/fail statement).
- V4 entry-delay sensitivity: 0 / 1 / 2 sessions (framework test #9).

Trial accounting formula (freeze exact counts at registration):
- Arm B cells = 10 symbols × R rules × 2 roll rules × 3 stress × K slippage
  scenarios × 3 entry delays = 180·R·K cells, plus baselines (flat 1 +
  always-on 2 + single-leg 10) and ablations (leave-one-leg 10,
  leave-one-rule R), each a FULL-PATH re-run (never additive attribution).
- Example with R=3 candidate rule sets and K=2 slippage scenarios:
  1,080 primary cells + 13 baselines + 13 ablations.
- Arm A/C are selection-free descriptives; they still log every computed
  statistic with script + window (OBSERVED taxonomy).

## 2. Seeds and determinism

- Master seed: 20261002. Per-cell seed = 20261002 + cell_index (stable
  enumeration order: symbol → rule → roll → stress → slippage → delay).
- Synthetic-fixture seed (engine tests): 20261002.
- All replays must be byte-identical on re-run (futbt enforces; journal
  JSON equality asserted in tests). Prefix determinism and future-mutation
  invariance hooks must pass at every cutoff used in reporting.

## 3. Calendar / roll / execution specification

- Sessions: weekday-empirical calendar from the raw bar union per symbol
  until a real exchange holiday calendar is supplied (currently NOT_RUN;
  `futbt.calendarx.require_real_calendar` hard-stops paths that need it).
  Holiday-vs-fetch-gap distinction stays NOT_RUN.
- Roll: declared baseline above; OI inputs NOT_RUN (absent from raw);
  volume variant strictly PIT (cutoff ≥ 1 session before decision).
- Execution model (futbt defaults): decision at session close through a
  PIT-enforced view; entry fill next session open (or same-close, stamped
  OPTIMISTIC and excluded from primary reporting); TP/SL intrabar vs
  high/low; same-bar TP+SL → AMBIGUOUS_ORDER (ledger books worst-case
  bound; reporting uses bounds, never a point value).
- Continuous adjustment: additive (panama), causal, FEATURES ONLY;
  execution/MTM on raw contracts. Ratio adjustment refused on non-positive
  prices (CL 2020).
- Close-only bars can never fill (orders lapse with reason recorded).
- Accounting: arithmetic PnL only; negative CL legal; 6J orientation guard
  active; margins via published broker tables with buffer parameter.

## 4. Cost assumptions (frozen pre-run; incomplete pieces stay NOT_RUN)

- Commission: 0.85 USD/side PUBLISHED (IBKR) + exchange+regulatory:
  ES 1.39 (documented example, all-in 2.24) — other 9 symbols NOT_RUN
  until fetched or owner-declared; cells touching them report
  cost_incomplete=True and cannot claim pass bars.
- Spread: measured medians (above), tagged with the daily-BBO caveat
  (no intrabar path / executable-spread / capacity proof).
- Slippage: BLOCKED on owner declaration. Requirement: explicit nonzero
  USD/contract/side + declarer + rationale per symbol; zero or silent
  values are rejected by the cost book. Proposed default for discussion:
  1 tick/side/symbol (CL $10, ES $12.5, 6J $6.25, ...) — a DECLARED
  assumption, not a measurement.
- Roll cost: adjacent-contract close gap on roll dates (computed by the
  roll table); reported per roll with raw gap and both fills.
- Margin: initial/maintenance from published tables; stress buffer +10%
  proposed; overnight position fees NOT_RUN (not fetched).

## 5. PIT rules (hard constraints, enforced in code)

1. Feature values carry as-of dates ≤ decision session (violations raise).
2. Volume/OI roll decisions use data strictly earlier than the decision
   session; final same-day volume/OI is unreachable by construction.
3. Expiry schedules (exchange-published years ahead) are the only roll
   inputs for the baseline rule.
4. No CONTFUT synthetic chains (measured 41-63% dead bars previously).
5. Adjusted continuous series: causal construction only, never used for
   fills/MTM/PnL.
6. Daily BID/ASK closes are cost evidence, not executable quotes.
7. Every ex-post label (MAE/MFE, exits) is description-only, never an
   entry feature.

## 6. Admission bars (data gate, before any Arm B run)

- DAILY_BT READY: true-volume front chain ≥ 24 months + PIT roll + complete
  costs (incl. declared slippage). Currently BLOCKED 10/10 (~14 months).
  Unblocking options (owner decision): (a) licensed vendor history
   (Databento / CME DataMine-class, owner purchases), (b) prospective
  accumulation from the working collector pattern, (c) accept 14 months
  with declared costs and a shortened-pass-bar caveat stamped on every
  output.
- INTRADAY READY: multi-year M1/H1 per contract — NOT on any near-term
  path; Arm C stays descriptive.

## 7. Pass bars (research gate, per owner framework §6 — evaluated only in
the future registered cycle)

1. Full-sample result; 2. walk-forward/rolling OOS (purge = true horizon =
   max hold + entry delay sessions; embargo = same; ≥ 4 anchored folds);
3. regime split; 4. year-by-year stability; 5. long vs short contribution;
6. event vs non-event; 7. front vs deferred; 8. parameter perturbation;
9. entry-delay sensitivity; 10. cost/slippage stress ×1/1.5/2; 11.
alternative roll rule; 12. alternative data cross-check where possible;
13. look-ahead audit (truncation + future-mutation hooks green);
14. survivorship/symbol-mapping audit; 15. capacity and turnover review
(daily-BBO caveat: capacity is NOT_RUN until better microstructure data).

Additional hard rules: ambiguous-bar trades reported as bounds only;
censored trades never netted into point totals; fold suppression for
performance reasons forbidden (only INSUFFICIENT_COVERAGE, recorded);
marginal contributions only via full-path leave-one-out; combine weights
DECLARED ex ante (fitted weights must be labeled IN_SAMPLE_MASQUERADE).

## 8. Resource needs

- Compute: negligible (stdlib offline; the whole 147-test suite runs in ~2 s).
- Storage: raw snapshot 36 MB (read-only); fixtures ~10 MB in temp dirs.
- Data (the real cost): see §6 options; any purchase is an owner decision.
- Locks: none needed for prep; the future registered cycle follows the
  standard lock/gate protocol.

## 9. Open items blocking launch

1. Owner data-depth decision (§6 a/b/c).
2. Registration of the scored cycle with frozen trial budget (§1 counts).
3. Owner-declared slippage values (§4) and, ideally, fetched per-symbol
   exchange fees.
4. Real exchange holiday calendar (or an explicit decision to run on the
   empirical bar calendar with the caveat stamped).
5. Rule set R and hypothesis sheets per symbol (dossiers lane output) to
   freeze the exact arms.
