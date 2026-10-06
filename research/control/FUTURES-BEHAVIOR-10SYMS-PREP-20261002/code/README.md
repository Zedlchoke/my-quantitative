# futbt — futures backtest-prep package (FUTURES-BEHAVIOR-10SYMS-PREP-20261002)

OFFLINE PREP code for the 10-symbol futures universe (NQ ES CL NG GC SI 6E
6J 6B 6A). Contains **no real-strategy PnL runs, no performance selection,
no scored anything**. All tests run offline on deterministic synthetic
fixtures that replicate the exact raw IBKR JSON schema.

## Run the tests

```bash
cd research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/code
./run_tests.sh
# or directly:
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m unittest discover -s tests -t .
```

Expected: `Ran 273 tests ... OK` for the pre-DBN lanes (pure stdlib, ~3 s,
no network, no lock): 147 at base eae8c3d2 + 29 WF-PIT-FIX (walkforward
window/PIT laws) + 35 EXEC-FIX (execution laws) + 62 MULTIASSET-WIRING
(portfolio wiring). The concurrent DBN lane's `test_dbn_*` files are in
flight in this shared worktree — measure the suite at your read time;
on 2026-10-02 (16:5x) `tests/test_*.py` minus `test_dbn_*` = 273 OK.

Optional real-data adapter smoke (descriptive only — parses the read-only
raw snapshot, no PnL):

```bash
/Users/hoangminhlong/my-quantitative/.venv/bin/python \
  scripts/smoke_adapter_real.py \
  --raw ~/.my-quantitative-data/futures-10syms-v1/raw \
  --out ../analysis/engine_adapter_smoke.json
```

Latest run: 1160/1160 files parsed, 202 contracts grouped, close-only
fractions 0.65–0.88 per symbol — consistent with the data lane's measured
25–90% pathology (OBSERVED, see `../analysis/engine_adapter_smoke.json`).

## Layout

| module | role |
|---|---|
| `futbt/taxonomy.py` | FACT/OBSERVED/POSTULATED/NOT_RUN evidence tags; PUBLISHED/MEASURED/DECLARED/NOT_RUN cost provenance; `PolicyError` hard stops |
| `futbt/instruments.py` | 10-symbol instrument table (multiplier/minTick/timezone OBSERVED from IBKR secdef 2026-10-02; units/cycle/LTD PUBLISHED from the specs dossier; margins PUBLISHED NinjaTrader+AMP, CME SPAN NOT_RUN). 6J = USD-per-JPY orientation guard ($6.25/tick, inversion trips a PolicyError); SI = 5000oz class SI |
| `futbt/calendarx.py` | `ExchangeCalendar` protocol, deterministic `WeekdayCalendar` (fixtures), empirical calendar-from-bars; real holiday/DST calendar is a NOT_RUN placeholder that raises |
| `futbt/rawdata.py` | per-contract raw adapter: filename pattern `{SYM}_{LOCAL}_{CONID}[_(front|next|nearest_expired)]_{TRADES|BID|ASK}_{1day|1hour|1min}_{SPAN}.json`, header validation (conId/localSymbol/whatUse/barSize/n_rows), close-only settlement-bar detection, BID/ASK v=-1 semantics, IBKR error-162-empty tolerance, ordering authority = lastTradeDate |
| `futbt/roll.py` | roll engine: declared calendar baseline (last session before day-1 of expiry month by last-trade date, roll at that close), PIT-guarded `VolumeRollRule` (strictly-earlier cutoff, final same-day volume refused), full roll tables (old/new, reason, volumes, OI=NOT_RUN, raw gap, additive+ratio factors), raw execution chain, causal additive/ratio feature adjustment |
| `futbt/accounting.py` | arithmetic PnL (negative-CL safe; `log_return` is a tripwire that raises on non-positive), exact Decimal tick rounding, 6J plausibility band, `CashLedger` with reconciliation + per-kind event sums (independent reconciliation input), `Position` with roll events, `MarginModel` over published tables, `drawdown_series`/`max_drawdown` (arithmetic levels only) |
| `futbt/costs.py` | component-tagged cost book: IBKR 0.85 PUBLISHED, exchange+reg NOT_RUN except the ES 2.24 documented example, spread MEASURED (daily-BBO proxy with explicit caveat), declared-slippage NONZERO scenario hook, ×1/1.5/2 stress on variable components, completeness refusal; quantity-scaled commissions with NULL+source-class disclosure for missing components (R1) |
| `futbt/journal.py` | trade journal: PIT feature snapshots (as-of enforcement), trigger/veto, fills/rolls/exits, lifecycle gross segments + per-contract MAE/MFE segments + `cost_missing_components` (R2/R3/R1), censoring, frozen breakeven tolerance, `AMBIGUOUS_ORDER` handling with `tp_first`/`sl_first` bounded scenarios, booked-bound stamp and no point PnL |
| `futbt/engine.py` | deterministic single-symbol daily replay: decisions at close through a `PITDataView` that raises on future reads, next-open fills (tick-rounded cost shift, quantity-scaled commissions, all-component incomplete-cost law), intrabar TP/SL with gap-aware stop-market/limit semantics BEFORE the end-of-session roll (R3/R4), same-bar TP+SL → AMBIGUOUS_ORDER (ledger books worst-case bound), auto-roll of open positions with rebased stops and lifecycle segment accounting (R2), forced exit at expiry wall, close-only bars can NEVER fill on any path (entries lapse; TP/SL silent without a real high/low; TIME/MANUAL exits deferred to the next tradeable session; roll legs wait for a tradeable bar pair; else right-censored — audit M3 fix, proven by TestCloseOnlyNeverFills), finite-OHLC validation at construction, per-bar + end-of-run independent reconciliation (journal ↔ cash ↔ events ↔ inventory ↔ MTM), truncation & future-mutation hooks. MULTIASSET-WIRING 2026-10-02: the loop body lives in the steppable `_Replay` (single-symbol behavior byte-identical) + `PortfolioEngine`: synchronous multi-symbol lockstep replay with a gate protocol (structural caps at the decision close, margin admission at the fill open — both as journaled vetoes, never silent), per-symbol netting on the current chain contract, USD cash aggregation asserted per session against the event logs, per-bar portfolio MTM/equity/drawdown series on the HELD contract's closes (frozen-marks protocol: the current close is never visible at its own open), margin aggregation series, portfolio cutoff + future-mutation hooks |
| `futbt/walkforward.py` | exposure calendar, anchored folds with per-window integrity (R5 fix, 2026-10-02): test_end ENFORCED per fold (post-test cells excluded + audited `out_of_fold/POST_TEST_WINDOW`, never evaluated), label maturity (`LABEL_CENSORED` for test cells whose horizon extends past the fold boundary or the calendar end — never truncated silently), purge >= true horizon (under-purge raises, validation before any fold mutation), embargo with per-cell audit trail, NO overlapping folds (`validate_no_overlap`; final fold extended to calendar end for gapless coverage — coverage arithmetic only), planner is the single horizon authority, performance-reason fold drops forbidden (only INSUFFICIENT_COVERAGE), nested TRAIN selection stamped at train_end, deterministic replay, prefix-determinism / future-mutation assert helpers |
| `futbt/composition.py` | sleeve descriptives (overlap, Pearson+Spearman tie-safe, co-loss, joint tail), `PortfolioRiskCaps` with the WIRED veto-mode `enforce_veto` (never clips/rescales; blocked signals carry machine codes and land in journals; legacy clip-mode `enforce` is analysis-only), `PortfolioRiskGate` (reference gate for PortfolioEngine: structural caps at decision close over the effective book incl. same-close pendings + margin admission at fill open, full audit trail), sleeve series / descriptives / blocked-signal accounting / combined breakeven from wired portfolio runs, `AlwaysOn` baseline strategy, `portfolio_leave_one_leg` full-path harness, `CombineSpec` (weights must be DECLARED; fitted weights = IN_SAMPLE_MASQUERADE unless acknowledged), `FullPathRunner`, leave-one-leg / leave-one-rule specs (`additive_attribution_guard` forbids summing leg PnLs), flat / always-on / single-leg baselines |
| `futbt/synth.py` | deterministic synthetic-fixture generator (see below) |
| `tests/` | 273 offline tests outside the DBN lane (147 base + 29 `test_wf_*` + 35 `test_exec_*` + 62 `test_portfolio_*`) |
| `scripts/smoke_adapter_real.py` | descriptive adapter smoke on the real read-only raw snapshot |

## Synthetic fixture (what the tests run on)

`futbt.synth.build_universe(raw_dir, seed=20261002)` writes raw-format JSON
files (identical header fields and filename pattern to the real snapshot)
for three symbols over 2024-07-01..2026-09-30 on a Mon-Fri calendar:

- **CL-like**: monthly expiries, 0.01 tick, deterministic NEGATIVE price
  episode 2025-03-03..2025-03-14.
- **6J-like**: quarterly, USD-per-JPY scale (~0.0065), 5e-7 tick.
- **ES-like**: quarterly, 0.25 tick, strictly positive staircase.

Replicated raw pathologies (so adapter/engine face the real shapes):
deep-history bars are close-only settlement bars (o=h=l=c, v=0) before
`last_trade_date - 140d`; BID/ASK quote bars carry v=-1/wap=-1.0/n=-1;
volume migrates to the next contract ~1 month before the calendar roll date
(the PIT volume rule therefore rolls earlier than the baseline); marker
(`_front_`) convenience files exist alongside canonical series.

Known ground truth for assertions: `SynthUniverse.closes` (per symbol/conid/
session) and `expected_calendar_rolls()` — the roll engine is verified to
recover the exact baseline schedule and gaps. Same seed → byte-identical
files (verified by sha256 in tests). DST is NOT modeled (fixed -04:00
offset in the small intraday fixtures) — the real calendar/DST layer is a
NOT_RUN placeholder by design.

## WF/PIT disclosures (R5 + review-extra items, typed)

Co-owner review round co-owner-review-fix-1, lane WF-PIT-FIX, 2026-10-02.
One-liner status per item; evidence = named tests, all green.

- R5 window enforcement (test_end, no post-test leakage, no fold overlap):
  IMPLEMENTED + TESTED (`tests/test_wf_window_integrity.py`; co-owner case
  Jan–Jun 2026 / 4 folds / train_frac 0.7 / horizon 2: fold1 planned test
  May 8–20 previously emitted TEST cells through Jun 30 — 29 excess
  sessions and a 29-session overlap with fold2 — now emits May 8–18 only,
  with May 19/20 `LABEL_CENSORED` and the 29 post-test cells excluded +
  audited; reproduced failing first: 12 failures + 1 error at base).
- Label maturity (label at t needs horizon h of future data; immature
  labels dropped/censored, never silently truncated): IMPLEMENTED + TESTED
  (`LABEL_CENSORED` audit per cell; applies at every fold boundary
  including the calendar end for the final fold).
- Purge >= true horizon on the train side + validation before mutation:
  IMPLEMENTED + TESTED (under-purge and horizon-authority mismatch raise
  `PolicyError` before any fold state is touched).
- Embargo audit trail (every embargoed cell recorded with phase+reason):
  IMPLEMENTED + TESTED (per-cell `DroppedCell` records; exact embargo
  window asserted in `tests/test_walkforward.py` and
  `tests/test_wf_window_integrity.py::TestEmbargoAuditTrail`).
- Producer-prefix completeness (truncation/mutation tests cover bars +
  roll table + metadata + selection inputs, roll table REBUILT from
  truncated bars — not a static filter): IMPLEMENTED + TESTED
  (`tests/test_wf_pit_prefix.py`; honest replay reproduces the decision
  prefix on the truncated producer, and garbage in every post-cutoff
  channel changes nothing at or before the cutoff).
- Counter-lookahead teeth (a lookahead implementation WOULD change emitted
  decisions, proving the PIT tests are not vacuous): IMPLEMENTED + TESTED
  (leaky bar / roll-table / metadata / selection readers are each caught
  by `assert_future_mutation_invariance`).
- date-asof vs timestamp-release distinction at the WF layer:
  NOT_IMPLEMENTED — WF asof is DATE-granular (session atomic at daily
  close; views pinned by calendar date). No intraday release-time registry
  exists, so a data item released intraday ON date t is indistinguishable
  from end-of-t information at this layer; NOT_RUN until a
  timestamp-release provider exists.
- Nested TRAIN selection visibility (selector sees only a view pinned at
  train_end; params frozen + stamped before TEST): IMPLEMENTED + TESTED
  (`run_selection` stamps `selection_asof`/note; stability under
  post-train-end mutation proven, leaky selector proven detectable).
- Known scope note: in anchored-expanding folds, a later fold's TRAIN
  lawfully contains earlier folds' TEST sessions (past data by then);
  per-fold integrity is enforced per fold, not globally exclusive.
- Base-test erratum: `tests/test_walkforward.py::
  test_embargo_drops_test_cells_right_after_train` assertion tightened
  (test-phase drops now also include `LABEL_CENSORED` cells); the embargo
  law itself is unchanged and asserted exactly.

## Execution disclosures (R1–R4 + review-extra items, typed)

Co-owner review round co-owner-review-fix-1, lane EXEC-FIX, 2026-10-02.
Every finding was reproduced on base eae8c3d2 with a failing test first,
then fixed (laws in the `futbt/engine.py` module docstring; reproducing +
adversarial tests in `tests/test_exec_*.py`, 35 tests):

- R1 commission quantity + incomplete-cost law: IMPLEMENTED + TESTED —
  `commission_cash_usd(qty)` scales every priced component (base charged
  qty-1: ES qty3 roundtrip was $4.48, must be $13.44); `allow_incomplete_costs`
  covers ALL cost components (base flagged only commission components, so a
  NOT_RUN slippage left `cost_incomplete=False`); when allowed-incomplete,
  KNOWN fees are deducted (base zeroed ALL fees when one commission
  component was missing: CL charged $0.00 instead of its known $0.85/side)
  and missing components are recorded as NULL with their source class —
  never a fabricated 0, never MEASURED; incomplete book +
  `allow_incomplete_costs=False` refuses at engine construction.
- R2 roll gross into journal lifecycle + reconciliation: IMPLEMENTED +
  TESTED — every contract segment (roll old legs incl. roll fees and the
  final exit) accumulates into the record (`gross_segments`; the es_universe
  repro trade: ledger 700 vs journal 425 at base — now 700/700, net
  691.04); per-bar AND end-of-run reconciliation journal <-> cash <->
  events <-> inventory <-> MTM, where the ledger is checked against an
  INDEPENDENT recomputation from journal records — never against its own
  event log. (MULTIASSET-WIRING follow-up 2026-10-02: right-censored
  records with EXECUTED roll legs now contribute their segment gross to
  the final identity — the ALWAYS-ON baseline exposed the gap; repro +
  fix in `tests/test_portfolio_composition.py::TestCensoredRollLegReconciliation`.)
- R3 intrabar barrier vs end-of-session roll ordering: IMPLEMENTED + TESTED
  — barriers evaluate on the OLD position/contract BEFORE the roll, on
  that bar's own extrema (base rolled first, then fired the gap-rebased
  stop off the OLD bar's low and filled on the NEW contract at 184.75,
  outside its entire [198,205] range; now fills 94.75 on the old contract
  and never rolls); MAE/MFE are per-contract segments on legal intervals
  (the new contract's roll-session bar happened BEFORE the close-time
  fill and never counts for the new position).
- R4 gap-stop + limit semantics: IMPLEMENTED + TESTED — SL is
  stop-market: a gap through the barrier fills at the open (long stop
  `min(open, sl)`, short stop `max(open, sl)`), adverse cost shift
  afterwards — a long stop never fills above the open (base filled a long
  SL95 at 94.75 into a O80/H90/L70 bar); TP is a limit: barrier or better
  (`max(open, tp)` long / `min(open, tp)` short); same-bar TP+SL stays
  AMBIGUOUS_ORDER with gap-aware scenario bounds — the order is NEVER
  inferred from OHLC alone; entry-beyond-barrier fills against the open.

Review-extra items, each typed IMPLEMENTED / TESTED / NOT_IMPLEMENTED:

| item | status | why (one line) |
|---|---|---|
| expiry/first-notice wall when no next contract exists | IMPLEMENTED/TESTED | roll row exists but no tradeable next-contract price on the scheduled session -> FORCED_ROLL exit at the old close (test_engine forced-exit test); held contract is the LAST listed (no roll row at all) -> right-censored END_OF_DATA rather than an invented forced liquidation (censoring test) — the wall is never crossed on either path |
| finite OHLC validation (O/C within [L,H]) | IMPLEMENTED/TESTED (engine-side) | every bar of every contract validated at engine construction (finite OHLCV, h>=l, o/c within [l,h], else PolicyError — tests/test_exec_data_validation.py); `rawdata.Bar.validate` still checks only h>=l, so adapter-level validation stays NOT_RUN |
| date-asof vs timestamp-release PIT distinction | NOT_IMPLEMENTED | `PITDataView` pins by session DATE only; vendor publish/release-lag semantics are absent (no release timestamps in the raw snapshot) — NOT_RUN until a PIT release-timestamp provider exists |
| same_close / next_open config actually enforced | PARTIAL: next_open IMPLEMENTED/TESTED; ENTRY same_close NOT_IMPLEMENTED | entries always fill at the NEXT open; `fill_timing='same_close'` only stamps an OPTIMISTIC_SAME_CLOSE note on the record (a true same-close entry fill would be optimistic look-ahead and is deliberately absent); MANUAL strategy exits do fill at the decision close and are stamped OPTIMISTIC_SAME_CLOSE (tested) |
| MTM / drawdown / margin / portfolio caps wired vs scaffold | IMPLEMENTED + TESTED (portfolio layer, MULTIASSET-WIRING 2026-10-02) | `PortfolioEngine` enforces margin + structural caps DURING the run through the gate (veto/blocked journal entries, never silent clipping), records per-bar portfolio MTM/equity/drawdown and per-session aggregated margin; the SINGLE-symbol engine still runs cap-free by design (caps are a portfolio-level law). Evidence: `tests/test_portfolio_risk_caps.py`, `tests/test_portfolio_wiring.py` — see "Portfolio / multi-asset disclosures" below |
| raw roll gap must not be double-charged as a transaction cost | IMPLEMENTED/TESTED | the gap is borne exactly once via raw-contract segment accounting ((old_fill−entry) + (exit−new_fill)); roll cash costs are commissions only; test_exec_roll_accounting proves gross ≠ any gap-inflated total and ledger cost outflow == commissions |
| CostBook serial-dead-book vs liquid-quarterly spread selection + provenance + freeze | NOT_IMPLEMENTED | one front-measured (daily-BBO proxy) spread per symbol applies to ALL contracts incl. serials; serial books are materially wider and unmeasured, and MEASURED execution is not claimable from bar-side proxy spreads — per-book selection + freeze NOT_RUN until per-book measurements exist |
| risk-cap freeze law independent of economic gates | IMPLEMENTED + TESTED (portfolio layer, MULTIASSET-WIRING 2026-10-02) | caps are frozen data (`PortfolioRiskCaps`) enforced by the gate BEFORE economics enter (structural vetoes at decision close over the effective book; margin admission at fill open), each with its own audit trail + journal record — see portfolio disclosures below |

## Portfolio / multi-asset disclosures (MULTIASSET-WIRING, 2026-10-02)

Owner steering (round steering-waiting-databento): "multiasset
netting/risk/MTM/DD must be WIRED and TESTED if the launch intends to use
them; a scaffold is not ready". BACKTEST_LAUNCH_DRAFT.md §1/§7 intends
sleeves across the 10 symbols with risk caps, co-loss/overlap
descriptives, combined net, baselines and leave-one-leg ablations as
FULL-PATH re-runs. Status after this round — every wired item is proven
by tests on synthetic multi-symbol universes (`tests/test_portfolio_*.py`,
62 tests):

| wired item | status | evidence (one line) |
|---|---|---|
| portfolio position state across symbols, per-contract-chain netting | IMPLEMENTED + TESTED | `PortfolioEngine.net_positions()`/`effective_book()` + `positions_by_session`; rolls move the net qty to the next chain contract while other symbols hold (`TestRollWhileOtherHolds`) |
| USD cash aggregation | IMPLEMENTED + TESTED | portfolio cash = Σ member ledgers, asserted EVERY session against an independent event-log recomputation (`engine.PortfolioEngine.run`; `TestThreeConventionsExactCash`) |
| per-bar portfolio MTM + drawdown series | IMPLEMENTED + TESTED | MTM on the HELD contract's latest close ≤ t (settlement closes are legal marks, never fills); equity = cash+MTM; DD vs running peak; frozen-marks protocol keeps the current close invisible at its own open (`TestPortfolioPITAndLookahead`) |
| margin aggregation vs risk-cap interface | IMPLEMENTED + TESTED | `MarginModel.check` over the aggregated book at fill admission (enforcement) and per session (descriptive utilization series with buffer; `TestMarginUtilizationSeries`) |
| risk caps enforced as VETO/blocked journal entries, never silent clipping | IMPLEMENTED + TESTED | `PortfolioRiskCaps.enforce_veto` (wired mode; quantities never clipped/rescaled) + gate → journal records with codes `BLOCKED_*`; blocked accounting reconciles gate audit ↔ journals (`TestMarginCapBreachBlocksAndJournals`, `TestStructuralCapVetoes`) |
| co-loss/overlap descriptives from journals | IMPLEMENTED + TESTED | `sleeve_series_from_result` (daily sleeve PnL = Δ(cash+MTM), exposure-gated) → `portfolio_pairwise_descriptives` (`TestCoLossDescriptivesFromJournals`) |
| DECLARED-weights combine, IN_SAMPLE_MASQUERADE guard intact | IMPLEMENTED + TESTED | `CombineSpec` unchanged and re-proven (`TestCombineSpecIntact`) |
| leave-one-leg FULL-PATH re-run harness | IMPLEMENTED + TESTED | `portfolio_leave_one_leg` over wired runs; genuine non-additivity: with a binding margin cap, removing a small leg UNBLOCKS a big one — marginal effect flips sign vs the leg's own PnL (`TestLeaveOneLegNonAdditive`) |
| baselines flat / always-on / single-leg | IMPLEMENTED + TESTED | `flat_baseline`, `AlwaysOn` (censors END_OF_DATA through rolls), `single_leg_baselines` adapters over portfolio-of-one runs (`TestBaselinesFullPath`) |
| breakeven tolerance on the combined journal | IMPLEMENTED + TESTED | `combined_breakeven` under the ONE shared frozen tolerance (mixed tolerances refused); AMBIGUOUS_ORDER and censored records excluded, bounds disclosed (`TestCombinedBreakeven`) |
| lookahead: portfolio decisions cannot see future legs | IMPLEMENTED + TESTED | portfolio-wide cutoff + future-mutation invariance (mutating every symbol's post-cutoff bars changes nothing ≤ cutoff), future-view trap raises, gate audit never runs ahead (`TestPortfolioPITAndLookahead`) |
| exact USD cash math across the three quote conventions | IMPLEMENTED + TESTED | CL (incl. negative-capable arithmetic) + 6J (USD-per-JPY, $6.25/tick) + ES concurrently; fills/costs/cash reproduced exactly from the declared cost model (`TestThreeConventionsExactCash`) |

NOT_IMPLEMENTED (honestly absent pre-data — no scaffold is called ready):

- intraday/intrabar portfolio decisions: NOT_IMPLEMENTED — the replay is
  session-atomic (decision at close, fill next open); intrabar path
  beyond AMBIGUOUS_ORDER bounds is unknowable from daily bars, and no
  M1/H1 execution layer exists yet (DBN lane's adapter aside).
- intra-symbol multiple concurrent positions / offsetting legs:
  NOT_IMPLEMENTED — one net position per sleeve per chain (the single
  engine's law); pyramiding/legging-in needs a declared rule set first.
- forced liquidation / de-risking on cap breach mid-run:
  NOT_IMPLEMENTED — caps block NEW exposure only; existing positions are
  never force-closed by the cap layer (an undeclared liquidation policy
  would be invented risk law).
- maintenance-margin calls / margin-call liquidation sequencing:
  NOT_IMPLEMENTED — admission checks the initial level on new fills; a
  call/liquidation timeline needs broker margin-call semantics data.
- cross-margining / SPAN offsets across symbols: NOT_IMPLEMENTED —
  margins are summed per contract from PUBLISHED broker tables (CME SPAN
  official NOT_RUN, transport-blocked 2026-10-02).
- portfolio notional caps on live BBO: NOT_IMPLEMENTED — notional uses
  the latest session close × multiplier (abs, negative-CL-safe); no
  intraday notional path exists.
- simultaneous same-close auctions across symbols: NOT_IMPLEMENTED —
  deterministic sorted-symbol sequencing is the declared convention
  (later symbols' fill admission sees earlier symbols' same-open fills;
  disclosed, not a defect).
- real-data portfolio runs: NOT_RUN — wired and tested on synthetic
  fixtures only; any real-data run belongs to the future registered
  cycle (see ../BACKTEST_LAUNCH_DRAFT.md §6).

Daily vs intraday scope (what "tested end-to-end" means here):

| scope | status | note |
|---|---|---|
| DAILY fixtures end-to-end (adapter → roll table → chain → portfolio replay → journals → series → composition) | TESTED | 62 portfolio tests on synthetic DAILY bars in the exact raw IBKR schema; three quote conventions; rolls, censoring, close-only fill law all inside the portfolio path |
| intraday session replay (H1/M1 bars as the portfolio clock) | NOT_IMPLEMENTED | no intraday calendar/session clock exists; `calendarx.require_real_calendar` raises |
| intrabar fills beyond the declared bounds | NOT_IMPLEMENTED by law | same-bar TP+SL stays AMBIGUOUS_ORDER (tp_first/sl_first bounds only); inventing a path from OHLC is forbidden at any granularity |
| intraday release-time PIT (timestamp vs date-asof) | NOT_IMPLEMENTED | portfolio PIT is DATE-granular like the WF layer; needs a release-timestamp provider |

## What is deliberately NOT implemented (NOT_RUN, do not fake)

- Real exchange holiday/DST session calendar (`calendarx.require_real_calendar`
  raises; CME pages transport-blocked 2026-10-02).
- Delivery-month expiry basis for the roll rule (needs exchange mapping
  tables; raw `expiry_month` field holds the last-trade date — caveat C3).
- Open interest anywhere in raw IBKR bars (roll-table OI stays None).
- Per-symbol exchange/regulatory fees for the 9 non-ES symbols.
- Declared slippage value (no value exists in the repo; hook requires an
  explicit nonzero declaration with declarer + rationale).
- Official CME SPAN margins (published broker tables only).
- Overnight position fees (IBKR tiered tables not fetched).
- Capacity/intrabar-path proof from daily BBO (explicit caveat attached to
  every spread component).
- Any real-data strategy run: the replay engine only ever runs in tests on
  synthetic fixtures. Running it on real data requires the future
  registered cycle + budget freeze (see ../BACKTEST_LAUNCH_DRAFT.md).

## Evidence/provenance rules used throughout

- Static specs: OBSERVED (IBKR secdef via S1, 2026-10-02) + FACT (public
  spec dossier with URLs). Margins: PUBLISHED with sources and as-of dates.
- Cost components: PUBLISHED / MEASURED / DECLARED / NOT_RUN per component,
  never silently mixed. A "complete" cost total refuses to compute while
  any component is NOT_RUN.
- Everything unmeasured is tagged NOT_RUN; missing evidence is never
  inferred PASS.
