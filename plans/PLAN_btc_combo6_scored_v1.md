# PLAN — BTC-COMBO6-SCORED-V1

- cycle_id: `BTC-COMBO6-SCORED-V1`
- asset: `crypto`
- status: REGISTERED (owner-directed)
- registration authority: owner directive verbatim, 2026-09-29 (chat, ZCode session):
  > "implement cho tôi các strategy này thành 1. Rồi sau đó chạy scored run back test. Nhớ phải có A7 kiểm toán độc lập và nhớ tối đa hoá agent để công việc nhanh hơn"
  (kèm 2 ảnh chụp: 1 strategy detail Momentum 1%/4h + bảng 5 strategy MA/RSI)
- branch: `orca/btc-combo6-scored-v1-integration`
- worktree: `.worktrees/btc-combo6-scored-v1/integration`
- budget: 7 planned scored cells, max 12 (`{used:0, max:12}`)
- GO phrase (registered-not-consumed): `GO BTC COMBO6 SCORED V1 SCORED EXECUTION`
- scored execution authority: owner standing directive above, consumable ONLY after
  independent A7 prelaunch verdict `AUTHORIZED` (two-key; DAYTRADER-100-V1
  standing-directive precedent). If A7 REFUSES: STOP, report, no scored cell.
- S1: `SEALED_UNTOUCHED`. S0: OPEN (historical BTCUSDT only).
- plan sha256: pinned at registration commit (self-hash excluded).

## §0 Question and honest prior

Owner supplied 6 externally-pinned bot strategies (screenshots, a bot-platform
portfolio). Question: **do these 6 exact specifications, combined into one
equal-weight 6-sleeve portfolio, show positive after-cost expectancy on
BTCUSDT perp 2021-01→2025-12 walk-forward folds, under the frozen declared
cost kernel?**

Honest prior: NEGATIVE. Ancestry overlap is heavy and disclosed:
- MA-cross / MA-spread / trend-following on crypto: SANDBOX-OVERFIT-3ASSETS
  SMA_X IS→OOS decay (81.8%→17.6% BTC) — diagnostic evidence, not registry law.
- Oscillator families: FXOS-04 oscillator-fade dead (FAMILY_FAILURES).
- Day-clock momentum class: standing veto TRACKA2-P3B-DINV-1D.
This cycle is owner-directed replication of externally-pinned specs, NOT a
novel-family claim. The F0-style ancestry court is therefore recorded as
DISCLOSED_HITS_OWNER_OVERRIDE (owner directive outranks the veto for scoring
authorization; the deaths still govern interpretation: a "survivor" here is a
candidate at best, and no parameter rescue is permitted after scored PnL is
visible). Negative close is a first-class successful outcome (Q-16).

## §1 Strategy spec freeze (owner screenshots, verbatim transcription)

Source images: `research/control/BTC-COMBO6-SCORED-V1/owner_screenshots/`
(Capture.PNG, Capture-1.png, copied 2026-09-29) + transcription below.

Image 1 (strategy detail):
- Name: `Momentum 1% / 4h · TP 1% / SL 1% · 5m`; Symbol: BTC/USD
- Rules: IF price moves up 1% over 4h THEN BUY 10,000 USD; IF price above
  purchase price × 1.01 OR below purchase price × 0.99 THEN SELL
- Settings: Signals 5m, Max open trades 1, Buy delay 0s, Status: running

Image 2 (strategy table, 5 rows):
1. `MA 4h/24h spread turn · TP 8% / SL 3% · 4h` — Spread — position open at end
2. `MA 12h/72h spread turn · TP 8% / SL 4% · 4h` — Spread — position open at end
3. `MA 2h/8h cross · TP 8% / SL 3% · 15m` — MA — position open at end
4. `RSI 20/55 · TP 8% / SL 3% · 15m` — RSI
5. `MA 2h/12h trend · TP 8% / SL 4% · 1h` — MA — position open at end

### Frozen leg specifications (LEG-1..LEG-6)

Common execution law (all legs):
- Long-only. Max 1 concurrent position per leg. Notional per entry: $10,000
  (declared interpretation D5; image 1 shows BUY 10,000 USD).
- Signals evaluated on completed bars of the leg's decision clock; decision at
  bar close t executes at the open of the next 5m master bar whose open time
  ≥ t + 5m (PIT: bar knowable at close; fill next bar open; Bandridge law).
- TP/SL monitored on completed 5m bars from the fill bar onward, relative to
  actual fill price: TP hit if 5m high ≥ fill×(1+tp); SL hit if 5m low ≤
  fill×(1−sl). Same 5m bar touches both ⇒ SL first (pessimistic). SL gap
  through: fill at min(SL level, that bar's open) (worst-fill grading).
  TP fills at TP level. Exit fees on exit notional.
- Re-entry only on a fresh signal state-change after flat.
- Fold-edge force-flat: positions closed at next 5m open after each test-fold
  boundary (costs charged); no positions carried across folds.
- Funding: measured Binance funding events applied at each settlement
  timestamp crossed while a position is open, signed, bps of entry notional
  (measured series; UNSTRESSED, noted in outputs).

| leg | family | clock | entry rule (frozen) | TP | SL |
|-----|--------|-------|---------------------|----|----|
| LEG-1 | MOM4H-1PCT | 5m | state-change of `close/close[-48×5m] − 1 ≥ +1%` false→true | +1.0% | −1.0% |
| LEG-2 | MAS-4H24H-TURN | 4h | spread `SMA(4h) − SMA(24h)` crosses ≤0 → >0 | +8.0% | −3.0% |
| LEG-3 | MAS-12H72H-TURN | 4h | spread `SMA(12h) − SMA(72h)` crosses ≤0 → >0 | +8.0% | −4.0% |
| LEG-4 | MAC-2H8H | 15m | `SMA(2h)` crosses above `SMA(8h)` | +8.0% | −3.0% |
| LEG-5 | RSI-20-55 | 15m | `RSI(20 bars, Wilder)` crosses above `RSI(55 bars, Wilder)` on 15m closes | +8.0% | −3.0% |
| LEG-6 | MAT-2H12H | 1h | `SMA(2h)` crosses above `SMA(12h)` ("trend", D4) | +8.0% | −4.0% |

SMA windows are TIME windows on the 5m close master (4h = trailing 48
5m-closes; 24h = 288; 2h = 24; 8h = 96; 12h = 144; 72h = 864), sampled at the
leg's decision-clock close. RSI periods are bar-counts on 15m closes.

### Declared interpretation register (agent interpretations of ambiguous
screenshot fields — NOT owner-supplied, flagged for owner review at scored GO)

- D1: long-only (screenshots show BUY rules only; no short rules visible).
- D2: MA = simple moving average (platform default), time-window semantics.
- D3: "RSI 20/55" = two RSI lines, fast 20 crossing above slow 55 (mirrors the
  two-line naming pattern of the MA legs).
- D4: "trend" leg enters on the same cross-up pattern; exits via TP/SL like
  all other legs (no time-stop visible on screenshots).
- D5: $10,000 notional per entry on every leg; 1 open position per leg.
- D6: momentum re-entry requires fresh threshold state-change (anti
  instant-re-entry).
- D7: "spread turn" = sign change of fast−slow spread (≤0 → >0).
- D8: TP/SL measured from actual fill price (not decision price).

## §2 Data authority (frozen)

- Master corpus: Binance Vision 5m klines zips `kl_*.zip` (102 files,
  2020-01→2026-09 tail), git-tracked at
  `research/control/bear_opportunity_recon_2026-09/killer_a4/dl5m/` (present
  in the cycle worktree by construction — branched from main).
- Funding: `research/control/bear_opportunity_recon_2026-09/data_a2/funding_events.parquet`
  (measured, 2019-09→2026-08-31, tracked).
- Symbol: BTCUSDT USDT-M perpetual ("BTC/USD" on the bot platform maps to the
  USD-margined BTC proxy; BTCUSDT-PERP is the house crypto BTC vehicle —
  declared vehicle mapping, disclosed).
- Every zip sha256-pinned at code/data freeze; loader re-verifies digests
  before use (PSV1 law: archives get rewritten upstream; re-verify on reuse).
- Panel build: zips → 5m UTC OHLCV frame; monotonic ts, drop-duplicate
  open_time (keep first), no imputation; gap census recorded (count, max run).
  Aggregations to 15m/1h/4h with complete-bucket law: bucket emitted iff all
  constituent 5m bars present; incomplete buckets are ABSENT (absence is
  information; decisions deferred to next present bar of the clock).
- PIT disclosure: Vision klines are retrospective exchange snapshots with no
  per-bar publication timestamps; frozen house convention (PSV1): bar knowable
  at close; first executable fill at next bar open. RETROSPECTIVE_SNAPSHOT
  label carried on all outputs.
- End cap: last 5m bar in corpus. Sealed tail (see §4) NOT loaded past
  2025-12-27 boundary? — NO: sealed tail is loaded (one corpus, one digest)
  but NEVER evaluated: engine hard-caps evaluation at F10 end 2025-12-26;
  sealed-tail equality is asserted by count in outputs only.

## §3 Cost authority (frozen, declared-pessimistic)

Per side, on entry/exit notional: `fee 5.0 bps (taker, DECLARED — CHR3F frozen
posture, unvalidated vs fills) + half-spread 1.0 bp (DECLARED_PESSIMISTIC)` =
6.0 bps/side; stress multipliers ×1.0/×1.5/×2.0 on fee+spread. Funding:
measured events, signed, unstressed. Slippage beyond half-spread: none
declared; the SL gap-through worst-fill rule is the adverse-move guard.
GROSS/NET dual books: NET (with full kernel) is decision-grade.

## §4 Calendar and folds (frozen)

- Corpus: 2020-01-01 → 2026-09-22 (5m, UTC).
- Warmup: 2020-01-01 → 2020-12-31 (≥ 52w; max indicator need 72h — generous).
- Test folds: 10 × 26w, F1 starts 2021-01-04 (Monday):
  F1 2021-01-04…, each fold 26 weeks, F10 ends 2025-12-26.
  No parameter fitting exists (owner-pinned specs) ⇒ embargo N/A_NO_FITTING
  (recorded, not inferred); fold boundaries are force-flat + attribution walls.
- Sealed OOS tail: 2025-12-27 → 2026-09-22 (~39w) SEALED — not evaluated this
  cycle; candidate for prospective verification only (new authority required).
- Non-vacuity: ≥ 30 closed trades per leg over the 10 folds, else leg verdict
  carries `TRADE_COUNT_ONLY`.

## §5 Portfolio construction (frozen)

6 independent sleeves, each $10,000 starting equity, fixed-notional re-arm
(no compounding). Combo = equal-weight sum of sleeve equity curves
($60,000 aggregate). No cross-margining, no reallocation, no interaction.
"Combined into 1" = this single portfolio instrument, one scored cell.

## §6 Baselines and typed bars (frozen; computed inside the scored pass as
re-evaluations, NOT counted as trials — EURUSD budget_note precedent)

- B0 FLAT (0 by construction — sanity identity only).
- B1 ALWAYS-LONG: $10,000 bought at F1 start open, held to F10 end, same cost
  kernel + funding (buy-and-hold benchmark).
- B3 BEST-LEG-PRIOR: per fold, hold the leg with best cumulative net PnL over
  PRIOR folds only (ties → lowest leg id); F1 defaults LEG-1.

Verdict bars:
- P1 after-cost net PnL > 0 (per leg, and combo).
- P2 combo profit factor ≥ 1.25.
- P3 combo net-positive folds ≥ 7/10.
- P4 combo max drawdown ≤ 25% of $60,000 aggregate.
- P5 combo net > 0 at stress ×1.5.
- P6 when combo net > 0: no single fold > 50% of combo net PnL.
- P7 combo net ≥ B1 net AND combo net ≥ mean(legs net).

## §7 Terminal outcomes (predecided)

- `COMBO6_SURVIVOR_CANDIDATE` — all P1-P7 (combo); still only a candidate:
  prospective verification + PIT authority beyond RETROSPECTIVE_SNAPSHOT
  required before any stronger label.
- `COMBO6_REJECT_ALL` — no leg passes P1.
- `COMBO6_NO_INCREMENTAL_VALUE` — some legs pass P1 but combo fails P7.
- `COMBO6_STRESS_FAIL` — P1-P4 pass, P5 fails.
- `COMBO6_RISK_BAR_FAIL` — P1-P3 pass, P4 (or P6) fails.
- `NOT_RUN_A7_REFUSED` — A7 prelaunch REFUSED and owner declines remediation.
- `NOT_RUN_DRY_RUN_FAIL`, `NOT_RUN_BUDGET_OVERFLOW`, `TECHABORT_*` per house
  taxonomy. No parameter rescue, no family substitution after scored PnL
  visible. Reopen only on changed mechanism axis (Q-10).

## §8 Trial budget freeze (frozen)

- Scored cells: 7 planned (6 legs + 1 combo), max 12. Overflow ⇒ HARD STOP ⇒
  owner packet. Unused cap expires at close. Observed denominator counts every
  computed scored outcome at computation time (including failures).
- Ledger rows ≤ 20. DSR per combo cell only if ≥ 100 trade observations
  (else `NOT_ENOUGH_OBSERVATIONS`); PBO CSCV `N_A_NO_SEARCH` — parameters are
  owner-pinned, no selection grid exists (recorded honestly; the program
  ledger 257/260 remains the multiple-testing denominator authority).

## §9 Governance

- A1 (Lead, this session): registration, freeze, dispatch, integration, close.
- Lanes (subagents, one worktree each where writing): IMPL (engine package +
  tests, worktree), DATA-VERIFY (read-only digest/coverage court), A7-PRE
  (fresh-context prelaunch audit), R-REPRO (detached reproduction twin),
  A7-TERM (terminal audit). Handoffs: `zcode_orch_v3_handoff@1` JSON to
  `research/control/BTC-COMBO6-SCORED-V1/handoffs/`.
- A7 independence: fresh context, audit artifacts only, never repairs, never
  told how to pass; A1's thread never audits A1's implementation choices
  without recompute-from-bytes evidence.
- Scored execution ONLY under machine-wide heavy lock (`role="E_SCORED_CELLS"`,
  `researchctl locks inspect` FREE_PROVEN first), wrapper
  `run_scored_locked.py` (DAYTRADER-100-V1 pattern).
- Two-key: key-1 = A7 prelaunch `AUTHORIZED` (0 unresolved HIGH/CRITICAL);
  key-2 = owner standing directive recorded verbatim in
  `auth/GO_RECORDED.json` at consumption time. A7 REFUSED ⇒ no consumption.

## §10 Deliverables map

| step | artifact |
|------|----------|
| spec freeze | this plan + `SPEC_FREEZE.md` |
| data/cost freeze | `DATA_COST_FREEZE.md` (sha256 pins at freeze) |
| implementation | `research/btcombo6/` (worktree) + tests |
| dry-run | `dry_run/btcombo6_dry.json` (no PnL at any depth) |
| A7 prelaunch | `audits/A7_PRELAUNCH.md` |
| scored | `scored/btcombo6_scored_stress{1.0,1.5,2.0}.json`, `scored/SCORED_REPORT.md`, `TRIAL_LEDGER.jsonl` |
| reproduction | `scored_repro/` + ALL_MATCH verdict |
| terminal | `audits/A7_TERMINAL_AUDIT.md`, `TERMINAL_DECISION.md` |
| close | registry TERMINAL, HYPOTHESIS_LEDGER row, FAMILY_FAILURES, MAP, LESSONS |

## §11 Owner open items (non-blocking, disclosed)

- D1-D8 interpretation register review (owner may override BEFORE scored run;
  after scored PnL visible, no rescue).
- Sealed tail disposition (prospective-only default).
- Vehicle mapping BTC/USD → BTCUSDT-PERP accepted unless owner objects.
