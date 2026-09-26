# P1 PROPOSALS (BLIND) — PWS-CX-SOLUSDT-C1 — council outcome-blind lane

- **Lane:** blind-proposer P1 (outcome-blind). Authored 2026-09-26.
- **Worktree / branch:** `.worktrees/pws-cx-solusdt-c1/integration` @
  `orca/pws-cx-solusdt-c1-integration`.
- **Base (dispatch) sha:** `ef3418d30d225a218b5916fc3d45c7376441e9b0`.
- **Blindness held:** no outcome/PnL artifact opened; no data plane touched;
  no parameter tuned against any measurement. Inputs = the dispatch reading
  list (`PLAN_pws_program_v1.md` §§1.2/2.2/2.3/7; `PLAN_pws_cx_solusdt_c1.md`
  §§1–2; `OUTCOME_EXPOSURE_MAP.md` §4; `FAMILY_FAILURES.jsonl` crypto rows —
  family_id + verdict_class only; `VIABILITY_cohort3_REPORT.md` §A as the
  kill-standard exemplar), plus cost-book facts already disclosed in control
  documents (DATACOST matrix SOL rows, BTC/ETH funding authority stats,
  LESSONS P-27/P-28).

## 0. Headline

**PROPOSALS SUBMITTED: 0. NEAR-MISS FAMILIES WITHDRAWN WITH FULL AUTOPSIES: 3
(covering 11 direction-source classes).**

After exhaustive F-0 enumeration over the authorized PIT observables for
SOLUSDT (1h klines OHLCV, floor 2020-09-14; funding settlements observable
only at their settlement timestamps; bookTicker/aggTrades spread census as
cost book — no L2, no liquidation tape, no multi-year OI), **every
constructible direction source matches a recorded dead family or an in-force
fence**. Submitting any of them would spend a scarce registry slot
(program ceiling 100, SOL slot 20) on a guaranteed
`F0_KILLED_VETO_VARIANT_SAME_FAMILY` / `K-ANC` / `K-COST` /
fictional-counterparty veto. Per master §1.2, §2 and the dispatch instruction
("a proposal whose own F-0 fails should be withdrawn by you, not submitted"),
the honest lane output is the enumeration + withdrawal ledger below. This is
the expected modal shape of the child (plan §1: "Modal outcome kỳ vọng:
REJECT_ALL / slate rỗng") and mirrors the SRLV-CX-C1 terminal precedent
(`a92664cd`: closing conditions = new payer + genuinely new information
layer; no re-clock/label/buffer/window rescue).

**This does not end the council.** Proposer lanes P2..Pn may hold candidates
this lane cannot see; the council, falsifier battery and C1 measured gates
proceed regardless. My lane certifies only that, from economic reasoning +
failure memory, the currently authorized observable space has no surviving
direction source.

## 1. Frontier enumeration — every direction source the authorized observables can express

A mechanism = direction source + trigger + exit. Killing all direction
sources is sufficient: no trigger/exit engineering resurrects a dead source
(LESSON P-27, read in reverse: adding a trigger to a dead source is not a new
payer).

| # | Direction source (from allowed observables) | Nearest recorded death / fence | F-0 verdict for any SOL mechanism |
|---|---|---|---|
| 1 | Price-shape, continuation side | `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION` CONTROL_OUTEARNED_ANCHOR; `PSV1-BTC_H1-UPTREND-BREAKOUT_CONT` / `DOWNTREND-BREAKDOWN_CONT`; `H-VOLCOMP-BRKOUT-v1`; `H-XSECT-MOM-v1`; `markdown-breakdown-short`; `24h-sprint-matrix` — all SCIENTIFIC_REJECTION | DEAD (multiple skeletons, multiple cadences) |
| 2 | Price-shape, reversal/fade side | `H-XSECT-REVERSAL-v2`; `mean-reversion-transfer`; `PSV1-BTC_H1-ACC-FLOOR_PROVISION`; FX oscillator class law (FXOS-04) carries via F-0 skeleton identity | DEAD |
| 3 | Kline sweep/zone/absorption (`PROXY_NOT_ORDERBOOK`) | BTC-BEAR Confirmation-Lag Front-Run `VETOED_FICTIONAL_COUNTERPARTY`; Mark-Trigger Catch-Down VETOED ×3; `M01-AGGRESSOR-ABSORPTION-PANEL` BLOCKED_PRELAUNCH; `SRLVCX1-M1-SETTLE-RESOLVE` REJECT_ALL_DEV_GATES | DEAD + fictional-counterparty veto: no legal PIT observable encodes the counterparty |
| 4 | Funding level/state as direction (carry or fade) | `CARRY-1D/3D/7D` SCIENTIFIC_REJECTION (xsect); `TRACKB1-CLASSA-FUNDING-LEVEL-GATED-CARRY` SELECTION_REJECTION; `H-FUNDCROWD-MR-v2` SCIENTIFIC_REJECTION; `A14-V14-A5-BASISLV-PREMFADE`; `V17-A6-P1-FUNDJUMP` SELECTION_REJECTION | DEAD. Single-pair SOL variants differ by ≤1 of the 3 required axes (universe construction only) ⇒ same identity per master §2.3 |
| 5 | Settlement-adjacent timing (±k h of 00/08/16 UTC) | `SRLVCX1-M1-SETTLE-RESOLVE` REJECT_ALL_DEV_GATES — measured, both pairs; LESSON P-28 fence BOTH directions (continuation re-read forbidden; fade = the dead anchor). Settlement-history information layer already spent its revival clause | DEAD / AIRTIGHT |
| 6 | Volume / tape-derived (1h volume, aggTrades quantities, any transform) | `ILLIQ-AMIHUD-28D`; `LOT-residual-MAX-7D`; `A5-V15-F1-ELITE-SIZE-ASYM`; `A6-V15-F1-TAKER-SAT`; `V17-A5-P2-TICKET-BREADTH`; `M01-AGGRESSOR-ABSORPTION-PANEL` | DEAD |
| 7 | Clock / session / calendar (UTC hour, weekday, weekend) | `V17-A4-P1-WKNDLIQ`; `V17-A5-P1-ATTN-PHASE`; Q-7 clock-book kill law; block-shuffle GMT-hour twin mandated at freeze ⇒ control-reproducible by construction | DEAD |
| 8 | Cross-pair state (BTC price-state, ratios as SOL gates) | `EOS1-E1`/`EOS1-E2` family-dead, symbol-swap-invariant ⇒ fence transfers to SOL | FENCED |
| 9 | OI / liquidation / depth | `BLOCKED_UNCONSTRUCTIBLE` (no L2 history, liqSnapshot 404, OI lookback ≈41.6h) + `OILEV-quintiles`, `OILEV-V2`, `OITD`, `V13-LIQEPIS`, `V17-A6-P2-OICASCADE` dead | UNCONSTRUCTIBLE |
| 10 | Vol-state as direction source | Q-7 law (variance predictable, direction 0/96 twice); `XSECT-VOLSHK-S15`; `ES1-VOLMAN-LONG` | DEAD |
| 11 | Risk-factor tilts (low-beta, size, quality) | `BAB-LOWBETA` dead; G8 fold-concentration 0.50 structurally hostile to long-biased books on this ancestry | DEAD |

Union of rows 1–11 = the entire expressible space. **No mechanism exists on
the currently authorized observables.** Rows are closed by law (dead family,
fence, unconstructible), not by my priors — my priors only enter §2-W1's
cost arithmetic, and there the conclusion is doubled by recorded deaths.

## 2. Withdrawal ledger — the three near-miss families (full autopsies, so the council can audit and so future proposers start from the correct kill)

### W1 — Funding-carry family on SOL (level-gated / persistence-gated / sign-run / squeeze-mirror / clamp-conditional)

- **One-liner:** same payer (contractual funding counterparty) + same
  information (funding settlement level/path) + same risk shape (multi-day
  directional hold) as `CARRY-1D/3D/7D` / `TRACKB1-CLASSA` /
  `H-FUNDCROWD-MR-v2` ⇒ at best 1-of-3 axes different (universe construction)
  ⇒ `VETO_VARIANT_SAME_FAMILY`; and independently, cost-ceiling arithmetic
  fails at honest order-of-magnitude (below).
- **Ceiling arithmetic (field-8 honesty; measured distribution to be re-made
  at C1 per child §2.4):** BTC measured funding authority = 11.798%/yr
  ≈ 1.08 bps/settlement; SOL prior 1–4× BTC ⇒ ~1–4 bps/8h mean with fat
  tails. Round-trip book: fee 2×5 bps + 2 adverse ticks (tick 0.01 USDT;
  0.4–5 bps each depending on price regime) + census spread ⇒ ~11–21 bps
  base, ~17–42 bps at stress ×1.5–2.0. Breakeven hold ≈ 5–14 days in a mean
  regime; 1σ weekly SOL price risk prior ~800–1,200 bps ⇒ premium:risk
  ≈ 1:40–1:100; PF≈1.3 power floor (n≈236) unattainable. Negative expected
  ceiling ⇒ K-COST VETO before scoring even if the family law were somehow
  survived.
- **F-0 record:** skeleton test FAIL (strip the funding observable and the
  identity does not exist; with it, the skeleton is the dead carry skeleton);
  payer test PASS (the only clean payer in this whole space: contractual,
  forced every settlement, not arbitrable away by a crowd that values levered
  directional exposure over the rent); information test PASS (funding state
  is not in clock/trend/spread). Withdrawn on family law + ceiling — recorded
  here so that a post-C1 revival, if the measured SOL funding distribution is
  genuinely fat, starts from the right autopsy and must still name 2-of-3
  genuine axis differences before entering the registry.

### W2 — Settlement-adjacent SOL mechanism (any trigger inside ±k hours of the 8h settlements)

- **One-liner:** BOTH directions fenced — fade/absorption side is the dead
  `SRLVCX1-M1-SETTLE-RESOLVE` anchor (+ M01 absorption family); continuation
  side is the LESSON P-28 fence ("inverted out-earn = kill, not signal";
  continuation measurably out-earned absorption on BOTH BTC and ETH). The
  entry clock is identical by construction ⇒ any such row is a re-clock
  variant, pre-vetoed by the recorded reopening conditions.
- **Payer audit:** the only candidate payer this lane could construct — the
  post-settlement exit flow of funding farmers (positions held exactly
  through a settlement, closed immediately after because the next rate is
  unobservable and the rent is spent) — is behavioral, its direction
  resolved AGAINST the fade side by the BTC/ETH measurement, and re-reading
  that measurement as a SOL continuation signal is precisely the forbidden
  P-28 move. No payer/information/risk triple inside the settlement window
  is expressible on the authorized observables that is not already spent.
- **F-0 record:** skeleton FAIL (same trigger/exit geometry as the dead
  anchor, window shifted); payer FAIL (unencodable or already measured
  against); information FAIL (settlement-history layer consumed by
  SRLV-CX-C1's revival clause).

### W3 — Forced-flow / kline-geometry events (post-crash drift, exhaustion, absorption, unlock-hedging)

- **One-liner:** the payer is an unobservable counterparty (liquidation
  cascade, hidden absorber, ETF/unlock hedger) ⇒ fictional-counterparty veto
  (master §7: every payer story must be encodable in legal PIT observables);
  chart-shape variants additionally land on dead skeletons (rows 1–3).
- **The unlock-hedger variant is named and parked as a revival condition,
  not a proposal:** SOL token-unlock calendars are real, dated, public
  forced-supply events and would constitute a genuinely new payer
  (recipients hedging vested supply) with a genuinely new information layer
  (event calendar). But the calendar is NOT in the authorized observables —
  new download = owner gate — and the perp-side hedge-flow effect is
  asserted, not encoded. Today: `BLOCKED_NEW_DATA_OWNER_GATE`. This is the
  one candidate on SOL this lane believes could pass all three F-0 tests
  IF the information layer were authorized; it is deliberately not submitted
  because a proposal cannot carry an observable its data plane does not
  contain.

## 3. F-0 self-court record (summary)

| Near-miss | Skeleton test | Payer test | Information test | Disposition |
|---|---|---|---|---|
| W1 funding-carry | FAIL (dead carry skeleton) | PASS | PASS | WITHDRAWN (family law + cost ceiling) |
| W2 settlement-adjacent | FAIL (dead anchor, re-clock) | FAIL | FAIL (layer spent) | WITHDRAWN |
| W3 forced-flow events | FAIL (dead skeletons) | FAIL (fictional, unencodable) | n/a | WITHDRAWN (revivable only via owner-authorized event calendar) |

## 4. Revival conditions (what would reopen SOL proposal space — each is a gate, not a wish)

1. **C1 measured SOL funding distribution** (already mandatory per child
   §2.1/§2.4, independent of proposals): if conditional-regime settlements at
   high percentiles clear the stressed RT over realistic holds, a carry-class
   row MAY be re-proposed — it must first name 2-of-3 genuine axis
   differences vs `CARRY`/`TRACKB1`/`FUNDCROWD` or it stays dead. Proposal
   drafting post-census remains legitimately outcome-blind (the funding
   distribution is cost book, not PnL).
2. **New data authority (owner action, R5-class):** liquidation tape /
   multi-year OI / L2 history ⇒ forced-flow payers become encodable; an
   options surface ⇒ vol-risk-premium payers; an unlock/event calendar ⇒
   W3's supply-event payer. Each is a new information layer — the only thing
   the recorded reopen conditions accept.
3. **Nothing else.** Re-clock, re-label, buffer, window, filter, sign-flip,
   pair-swap, timeframe-downshift (15m/1m = `ANCESTRY_EXPOSED_RECLK`, dev
   only, never OOS) are pre-vetoed (master §2.3, §1.2, §7; LESSON P-27/P-28).

## 5. Cost-auditor note (expected fill-hours profile)

No proposal submitted ⇒ no fill distribution to condition this cycle. For
future reference: any revived carry- or settlement-adjacent-class identity
would cluster fills in the 8h-settlement neighborhood (00–02, 08–10, 16–18
UTC) plus US-afternoon liquidity hours; the census should keep
settlement-adjacent buckets separate regardless, and the C1 funding
re-measure plus spread census remain mandatory gates independently of this
lane's output (child §2.1/§2.4 — fail-closed if absent).

## 6. Known limitations of this lane

- Outcome-blind by design: SOL-specific funding distribution, spread census
  and any PnL were not seen. All magnitudes in §2-W1 are priors anchored to
  BTC/ETH precedents disclosed in control documents, explicitly to be
  re-measured at C1.
- The "no direction source survives" claim is against failure memory as of
  today (136 entries; crypto rows enumerated in §1). An owner-authorized new
  information layer (§4.2) invalidates it — that is the intended reopening
  path, not a flaw.
- Registry discipline: nothing from this lane was written to
  `IDENTITY_REGISTRY.jsonl`; withdrawals made here are free (the ceiling
  counts only submitted rows). No DEFERRED rows requested.

— P1, outcome-blind lane, PWS-CX-SOLUSDT-C1
