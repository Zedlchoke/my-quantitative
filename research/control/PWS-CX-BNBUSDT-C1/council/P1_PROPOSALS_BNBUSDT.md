# P1 PROPOSALS (BLIND) — PWS-CX-BNBUSDT-C1 — council outcome-blind lane

- **Lane:** blind-proposer P1 (outcome-blind). Authored 2026-09-26.
- **Worktree / branch:** `.worktrees/pws-cx-bnbusdt-c1/integration` @
  `orca/pws-cx-bnbusdt-c1-integration`.
- **Dispatch sha:** `363cf282` (as stated in the dispatch packet; registry C0 row).
- **Actual start sha (measured):** `f15e67ace68546d095065c6e7814ada0b8db542b`
  (= branch HEAD at lane start; the C0 control-plane commit landed after the
  registry row that pinned 363cf282 — disclosed, no drift in content owned by
  this lane).
- **Blindness held:** no PnL/outcome artifact for BNBUSDT exists in this
  program and none was sought or opened; no data plane file touched (at lane
  start the control dir contained only `C0_control_plane.md` — no BNB data
  staged, no BNB funding distribution measured, so no number in this document
  is a BNB measurement); no parameter tuned against any measurement. Inputs =
  the dispatch reading list only: `PLAN_pws_program_v1.md` §§1.2/2.2/2.3/6.4/7;
  `PLAN_pws_cx_bnbusdt_c1.md` §§1–2 (this lane's charter, incl. the §1
  information-novelty test and §2.1 data-plane prohibitions);
  `research/wayfinder/FAMILY_FAILURES.jsonl` (crypto rows, family_id +
  verdict_class + primary_failure only); `research/wayfinder/LESSONS.md`
  P-27/P-28/P-29; the SOLUSDT precedent pair
  (`.worktrees/pws-cx-solusdt-c1/integration/research/control/PWS-CX-SOLUSDT-C1/
  council/P1_PROPOSALS.md` + `council/SKEPTIC_F0_REPORT.md` — fences, not
  outcomes); `DATACOST_FEASIBILITY_MATRIX.md` BNB row (cost-class facts).

## 0. Headline

**PROPOSALS SUBMITTED: 0. WITHDRAWN FAMILIES WITH FULL AUTOPSIES: 5,
covering 11 direction-source classes.**

After exhaustive F-0 enumeration over the AUTHORIZED observables for BNBUSDT
(1h klines OHLCV, floor 2020-02-10; funding settlements observable only at
their settlement timestamps; bookTicker/aggTrades spread census as cost book —
`NOT_RUN_DISK_CONSTRAINT` tonight; NO L2 history, NO liquidation tape, NO
multi-year OI, NO event/calendar layer — sources outside DATACOST are NOT
openable tonight, delegation boundary), **every constructible direction source
matches a recorded dead family or an in-force fence**. Under child plan §1
(the binding information-novelty test), a proposal can enter the registry only
by differing on ≥2 of 3 axes (payer / information layer / risk shape) from
EVERY recorded fence, or by R5-class new-information authority or a dated
cost-regime break — neither exists tonight within the authorized class, and
the axis test cannot be met on it (§3 below). Submitting any rows-1–11
mechanism would burn one of BNB's 15 survey-ceiling registry slots on a
guaranteed `F0_KILLED_VETO_VARIANT_SAME_FAMILY` / `K-ANC` / `K-COST` /
fictional-counterparty veto. Per master §1.2 and the dispatch instruction
("a proposal whose own F-0 fails is withdrawn by you, not submitted — burning
zero registry slots"), the honest lane output is the enumeration + withdrawal
ledger. This is the expected modal shape (child §1: "Modal outcome kỳ vọng:
slate rỗng") and the exact LESSON P-29 prediction for pair #2: *"pair #2 với
cùng lớp observable và không có góc thông tin mới có kết quả lặp lại"* —
this document is that prediction, verified lane-by-lane.

**This does not end the council.** Proposer lanes P2..Pn may hold candidates
this lane cannot see; the C1/C2 data+exposure gates proceed regardless (they
are mandatory independently of proposals, child §2.1–2.2). This lane
certifies only that, from economic reasoning + failure memory, the currently
authorized observable class has no surviving direction source for BNBUSDT.

## 1. Frontier enumeration — every direction source the authorized observables can express

A mechanism = direction source + trigger + exit. Killing all direction sources
is sufficient: no trigger/exit engineering resurrects a dead source (LESSON
P-27: "adding an observable/gate to a dead law is a variant, not a
mechanism"). The SOLUSDT C3 fences are pair-agnostic within the same
observable class (SOL P1 row-8 logic; child §1 states it as law: "SOLUSDT C3
fences là pair-agnostic trong lớp observable giống hệt") — so each fence
transfers to BNB unless a mechanism differs ≥2/3 axes, which §2 shows none
does.

| # | Direction source (from allowed observables) | Nearest recorded death / fence | F-0 verdict for any BNB mechanism |
|---|---|---|---|
| 1 | Price-shape, continuation side (breakout/donchian/markup-follow) | `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION` + `PSV1-BTC_H1-UPTREND-BREAKOUT_CONT` (CONTROL_OUTEARNED_ANCHOR), `PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT` (CONTROL_OUTEARNED), `H-VOLCOMP-BRKOUT-v1` (EXPECTANCY_NONPOSITIVE 26/28 cells), `H-XSECT-MOM-v1` (MDD_OVER_CEILING), `markdown-breakdown-short` (FOLD_CONCENTRATION), `24h-sprint-matrix` (98/98 dead) — all SCIENTIFIC_REJECTION, multiple skeletons × multiple cadences | DEAD. "BNB trends more orderly than SOL/BTC" is a distribution claim, not an identity axis; K-CONC is hostile to concentrated books regardless |
| 2 | Price-shape, reversal/fade side (band/oscillator MR) | `H-XSECT-REVERSAL-v2` (EXPECTANCY_NONPOSITIVE), `mean-reversion-transfer` (RULE_TRANSFER_FAILED — frozen-rule transfer to 6 altcoins failed; BNB-class alt inside that universe class), FXOS-04 oscillator-class law via F-0 skeleton identity | DEAD |
| 3 | Kline sweep/zone/absorption (`PROXY_NOT_ORDERBOOK`) | BTC-BEAR Confirmation-Lag Front-Run `VETOED_FICTIONAL_COUNTERPARTY`; Mark-Trigger Catch-Down VETOED ×3; `M01-AGGRESSOR-ABSORPTION-PANEL` SCIENTIFIC_REJECTION; `SRLVCX1-M1-SETTLE-RESOLVE` REJECT_ALL_DEV_GATES (net −25k/−34k bps PF 0.65/0.63 both directions both pairs) | DEAD + fictional-counterparty veto: no legal PIT observable encodes the absorbing counterparty |
| 4 | Funding level/state as direction (carry or fade; level/window/percentile/change/run transforms) | `CARRY-1D/3D/7D` SCIENTIFIC_REJECTION (FOLD_CONC 51.7%); `TRACKB1-CLASSA-FUNDING-LEVEL-GATED-CARRY` SELECTION_REJECTION — reopening language closes "ALL funding-level-derived gates — window/percentile/change/run transforms alike" (identity rho 1.0 on BTC); `H-FUNDCROWD-MR-v2` (FOLD_CONC 68–81%); `A14-V14-A5-BASISLV-PREMFADE` (FOLD_CONC 0.511); `V17-A6-P1-FUNDJUMP` (ANCESTRY_RHO_BLOCK 0.2439 — the change/event form still carries the level); `PWSCXSOL1-I001-TAILPAYER-RUN-REGIME` VETOED_SAME_FAMILY_PRE_PNL (representation rho 0.316–0.703, ceiling×power grid EMPTY) | DEAD (all transforms named inside closed classes). See W1 |
| 5 | Settlement-adjacent timing (±k h of 00/08/16 UTC) | `SRLVCX1-M1-SETTLE-RESOLVE` REJECT_ALL_DEV_GATES — measured on BTC and ETH, BOTH directions negative at every cost tier; LESSON P-28 fence BOTH readings (continuation out-earned absorption ⇒ inverted = kill, not signal); the settlement-history information layer already spent SRLV-CX-C1's revival clause | DEAD / AIRTIGHT. Funding cadence and settlement clock are venue-level (8h UTC), identical for BNB — symbol swap changes nothing |
| 6 | Volume / tape-derived (1h volume, aggTrades quantities, any transform) | `ILLIQ-AMIHUD-28D` (FOLD_CONC 0.7055 — closest near-miss on record, still dead); `LOT-residual-MAX-7D` (inverted control WON); `A5-V15-F1-ELITE-SIZE-ASYM`; `A6-V15-F1-TAKER-SAT` (EXPECTANCY_NONPOSITIVE); `V17-A5-P2-TICKET-BREADTH`; `M01-AGGRESSOR-ABSORPTION-PANEL` | DEAD. On BNB, aggTrades are authorized tonight ONLY as spread-census cost book (and that census is NOT_RUN_DISK_CONSTRAINT) — not a signal plane. See W5 |
| 7 | Clock / session / calendar (UTC hour, weekday, weekend) | `V17-A4-P1-WKNDLIQ` (ANCESTRY_RHO_BLOCK, corrected pooled rho 0.34–0.56 vs dvol proxies); `V17-A5-P1-ATTN-PHASE`; Q-7 clock-book kill law; block-shuffle GMT-hour twin MANDATED at freeze ⇒ the killing control is constructed by law before the anchor exists | DEAD. See W4 |
| 8 | Cross-pair state (BTC price-state gates; BNB/BTC, BNB/ETH ratio state) | `EOS1-E1` (G3_BASELINE_LOSS — long/flat gates can't beat the always-on baseline on 2020/21 beta); `EOS1-E2` (G6_CONTROL_OUTEARNS — block-shuffled ETHBTC ratio state out-earned the real ratio in all 3 arms: the ratio series carried NO timing information); family-dead, symbol-swap-invariant ⇒ fence transfers to BNB | FENCED. See W3 |
| 9 | OI / liquidation / depth (as signal) | `BLOCKED_UNCONSTRUCTIBLE` tonight (child §2.1: liquidationSnapshot, OI lịch sử, L2 history CẤM như SOL; no multi-year OI authorized) — and dead wherever previously measurable: `OILEV-quintiles` (ADAPTER_WEIGHT_INFEASIBLE), `OILEV-V2` (CONTROL_OUTEARNED), `OITD` (EXPECTANCY_NONPOSITIVE), `V13-LIQEPIS`, `V17-A6-P2-OICASCADE` (randomized-event-time sham OUT-EARNED the anchor) | UNCONSTRUCTIBLE tonight + DEAD on record. See W5 |
| 10 | Vol-state as direction source (vol-managed direction, vol-compression direction) | Q-7 law (variance predictable, direction 0/96 twice); `XSECT-VOLSHK-S15` SELECTION_REJECTION; `ES1-VOLMAN-LONG` G3_BASELINE_LOSS (vol-scaling reduced net more than it protected); `H-VOLCOMP-BRKOUT-v1` | DEAD |
| 11 | Risk-factor tilts (low-beta, size, quality/illiquidity premia on the perp) | `BAB-LOWBETA` COST_DOMINATED (anchor PF 0.992 after taker costs + funding; inverted control outperforms); `ILLIQ-AMIHUD-28D`; G8 fold-concentration 0.50 binding same-by-law on BNB (child §2.3): any long-biased book on 2020–2026 ancestry must prove short-capability or pre-freeze an alternative concentration statistic or define conclusions prospectively only | DEAD |

Union of rows 1–11 = the entire space the authorized observables can express.
**No mechanism exists on tonight's authorized class.** Rows are closed by law
(dead family, fence, unconstructible-by-delegation-boundary), not by this
lane's priors.

## 2. Withdrawal ledger — the five near-miss families (full autopsies, mapped to the BNB-specific angles a naive proposer would raise)

### W1 — Funding-carry / funding-run class on BNBUSDT (dispatch angle a: level-gated / persistence-gated / sign-run / squeeze-mirror)

- **One-liner:** same payer (the contractual funding counterparty — the only
  clean payer in this whole space: forced at every settlement, not arbitrable
  away by a crowd that values levered directional exposure over the rent) +
  same information layer (the settled funding series; a run/persistence
  statistic is a transform of it, per P-27 and the TRACKB1 closing language
  which closes "window/percentile/change/run transforms alike" BY NAME) + same
  risk shape (multi-day directional hold) as `CARRY-1D/3D/7D` /
  `TRACKB1-CLASSA` / `H-FUNDCROWD-MR-v2` / `V17-A6-P1-FUNDJUMP` /
  `PWSCXSOL1-I001` ⇒ at most 1-of-3 axes different (universe construction:
  BNB instead of BTC/ETH/SOL basket) ⇒ `VETO_VARIANT_SAME_FAMILY` by master
  §2.3.
- **The honest caveat the dispatch asked this lane to record, recorded:** C1
  will measure BNB's OWN funding distribution (child §2.4 — no inheritance of
  the SOL/BTC constants), and the ceiling×power grid (P-29: run-mean × H_min ≥
  RT_stress AND episodes ≥ 100 — empty at every (θ,K) on SOL) is a **cost
  argument** (K-COST/K-THIN), which is distribution-dependent and therefore
  not yet measurable for BNB tonight. **The IDENTITY kill is not.** The
  family law binds regardless of how fat BNB's tail turns out to be: "BNB's
  funding distribution is different" changes parameters, not the
  payer/information/risk triple. A different distribution can only ever feed
  the revival path, never the registry tonight.
- **P-29 representation law, pre-applied:** any ≥K-same-sign-persistence gate
  on a funding sign series is the level-window state smoothed, because the
  thing persisting IS the level. On SOL this measured rho 0.316–0.703 vs the
  dead CARRY level windows (1.5–3.5× the immovable 0.20 bar) and +0.615
  against the unconditional receiver. BNB's autocorr is unknown to this lane
  (outcome-blind, data plane not staged) — but P-29's operational law does not
  require the number to be favorable: the gate proposer must show the gate
  state escapes the bar on its own series BEFORE claiming a new information
  layer, and no tonight-authorized construct can differ from the level family
  by more than a transform. Until measured otherwise, assume the dead family.
- **K-CONC third-occurrence expectation:** every measured funding-class book
  in memory died on fold concentration (CARRY-7D 51.7%, H-FUNDCROWD 68–81%,
  BASISLV 0.511, PWSCXSOL1 59.1% of negative mass in one year / 42.2% in one
  9-day window). There is no recorded funding-class mechanism whose edge was
  NOT single-regime concentrated; BNB inherits the prior.
- **BNB-specific naive angle disposed:** "BNB is an exchange token — its
  funding is structurally long-biased, so the carry/fade economics differ."
  The payer is still the same contractual counterparty (levered crowd vs
  receivers at settlement); structural long-bias is a claim about the
  distribution's mean, not a new payer, information layer, or risk shape.
- **F-0 record:** skeleton FAIL (strip the funding observable and the identity
  does not exist; with it, the skeleton is the dead carry skeleton); payer
  PASS (clean, contractual — and therefore the SAME payer as every recorded
  funding death); information PASS on construction / FAIL on novelty (not new
  relative to the closed funding-level class). WITHDRAWN: family law binds
  tonight; ceiling is C1's business and cannot rescue the family even if
  favorable.

### W2 — BNB event-layer classes: quarterly burn calendar, SEC/DOJ 2023 events, Launchpool cycles (dispatch angle b)

- **One-liner:** these are real, dated, public BNB-specific events and WOULD
  constitute a genuinely new information layer (event/calendar) with
  nameable payer stories (burn = dated supply removal; DOJ/SEC November 2023
  = dated exchange-risk repricing; Launchpool = dated demand lock-up for
  staking BNB). **None of them is in the authorized observables tonight.**
  The authorized class is 1h klines + funding settlements + (disk-blocked)
  spread census; an event calendar is a new download = owner gate. Sources
  outside DATACOST are NOT openable tonight (delegation boundary).
- **Disposition:** `BLOCKED_NEW_DATA_OWNER_GATE`. Recorded here as a
  **revival-condition R5-class for the owner**, NOT as a proposal — a
  proposal cannot carry an observable its data plane does not contain.
- **Additional honesty flag (so the future proposer starts from the correct
  gap):** even with dates authorized, the perp-side effect (direction,
  duration, decay of the reaction in 1h bars) is asserted, not encoded — the
  proposer would still owe an F-0 payer story encodable in legal PIT
  observables (who is forced to trade, and why the forced flow lands on the
  side claimed). The burn-payer story (float reduction ⇒ persistent demand/
  supply imbalance) and the regulatory-event story (one-shot repricing, no
  repeatable hold) are different mechanisms and must be F-0'd separately;
  neither has ever been measured in this program.
- **F-0 record:** n/a — unopenable at the delegation boundary, which precedes
  F-0. This is the one BNB-specific class tonight that could in principle
  clear all three F-0 tests IF the layer were authorized; it is deliberately
  not submitted.

### W3 — BNB-as-exchange-token cross-sectional state: BNB/BTC, BNB/ETH ratios, BTC-regime gates on BNB (dispatch angle c)

- **One-liner:** the only executable form of "BNB's exchange-token state" on
  authorized observables is a cross-pair ratio or BTC-price-state gate on the
  1h klines — exactly the `EOS1-E1`/`EOS1-E2` skeletons. E1: BTC own-price
  state gates → long/flat, died G3 (always-on baseline beat every gate on
  2020/21 beta — a structural property of any 2020-floor large-cap long book,
  which BNB shares: same era, same beta class). E2: ratio trend/pct-rank
  died G6 — the block-shuffled ratio state OUT-EARNED the real ratio in all
  3 arms; the recorded finding is that the ratio series carried NO timing
  information for execution. That finding is about the class (pair-ratio
  state as an execution gate on a perp), not about the pair: swapping
  ETHBTC → BNBBTC changes the symbol, not the identity axes. Payer same
  (generic direction-taker — no forced counterparty), information same class
  (cross-pair ratio state), risk shape same (long/flat gating) ⇒ 0-of-3
  genuine differences ⇒ symbol-swap-invariant fence transfers (SOL P1
  row-8 logic).
- **BNB-specific naive angle disposed:** "BNB/BTC carries exchange-health
  information that ETHBTC doesn't." The part of exchange-health that lives in
  reserves/flows/redemptions is not in any authorized observable
  (unconstructible tonight); the part that would leak into the ratio IS the
  E2 skeleton, whose measured death was that the state, real or shuffled,
  made no execution difference. A "richer ratio" is a distribution claim on
  the same dead identity.
- **F-0 record:** skeleton FAIL (E2 gate skeleton verbatim); payer FAIL (no
  forced payer — direction-taker against flow that the G6 sham control
  already replicated); information FAIL (G6: no timing information in the
  class on record). WITHDRAWN.

### W4 — Weekend / clock / session classes on a 24/7 venue (dispatch angle d)

- **One-liner:** `V17-A4-P1-WKNDLIQ` died ANCESTRY_RHO_BLOCK at corrected
  pooled rho 0.34–0.56 against dvol proxies (the first measurement's PASS
  was a never-true clause — A7 caught it; the corrected kill is the fence);
  `V17-A5-P1-ATTN-PHASE` died the same cycle; Q-7 law holds the clock book
  carries no direction information; and the freeze mandates block-shuffle
  GMT-hour dummies as a clock twin — the control that kills any
  session-conditioned book is constructed by law before the anchor is.
- **Why there is no BNB gap here:** BNBUSDT trades the identical 24/7 venue
  with the identical 8h UTC funding clock; weekend is not a settlement or
  financing boundary for a USDⓈ-M perp (funding cadence is invariant across
  the week — the FX weekend-carry mechanism has no crypto analogue by
  construction), and DATACOST §3.2.4's venue-outage band (418 precedent
  2026-09-21) is a DECLARED cost band, not a direction source. Symbol swap
  changes nothing about which hours exist; any hour- or weekday-conditioned
  BNB book is a re-clock variant of a dead class (master §2.3: changing
  session/pair with the same skeleton = same identity) and is reproduced by
  its own mandated twin.
- **F-0 record:** skeleton FAIL (clock-gated directional skeleton); payer
  FAIL (no forced counterparty at any BNB-specific hour); information FAIL
  (Q-7 + measured WKNDLIQ rho). WITHDRAWN.

### W5 — Tape / volume / OI / liquidation transforms (dispatch angle e)

- **One-liner, two-part kill.** (i) **Unconstructible tonight:** child §2.1
  carries the SOL prohibitions verbatim — liquidationSnapshot, OI lịch sử,
  L2 history CẤM; no multi-year OI; aggTrades are authorized ONLY as the
  spread-census cost book, and that census is `NOT_RUN_DISK_CONSTRAINT`
  tonight (fail-closed per child §2.1 — no substituting another pair's
  census). The signal planes simply do not exist in the authorization.
  (ii) **Dead wherever they were measurable:** `M01-AGGRESSOR-ABSORPTION`
  (SCIENTIFIC_REJECTION), `ILLIQ-AMIHUD-28D` (fold conc 0.7055 — the
  closest near-miss in the ledger, still dead), `LOT-residual-MAX-7D`
  (preregistered falsification fired: inverted control WON), `A5-V15-F1-
  ELITE-SIZE-ASYM`, `A6-V15-F1-TAKER-SAT` (EXPECTANCY_NONPOSITIVE),
  `V17-A5-P2-TICKET-BREADTH`, `OILEV-quintiles` (adapter-infeasible),
  `OILEV-V2` (control out-earned), `OITD` (expectancy nonpositive),
  `V13-LIQEPIS`, `V17-A6-P2-OICASCADE` (randomized-event-time sham
  OUT-EARNED the anchor — falsification-by-control).
- **BNB-specific naive angle disposed:** "BNB has the deepest, cleanest tape
  among the alts." (a) Depth/tape as signal is not authorized tonight; (b)
  the recorded deaths are mechanism-level (controls out-earn, expectancy
  nonpositive, single-fold concentration), not liquidity-level — a deeper
  tape lowers the cost of running a dead mechanism, it does not create its
  payer; (c) the only place BNB tape depth legitimately enters tonight is
  the cost book, which is exactly the census that cannot run under the disk
  constraint.
- **F-0 record:** skeleton FAIL where constructible (dead tape/volume
  skeletons); payer FAIL (liquidation/absorption counterparty = fictional on
  authorized observables); information n/a (plane unauthorized).
  WITHDRAWN.

## 3. Certified conclusion for the track record

**Does ANY mechanism clear the information-novelty bar on tonight's authorized
class? NO.** This is this lane's certified conclusion, with the enumeration of
§1 as the proof:

1. **Same observable class as SOL.** BNBUSDT tonight is authorized exactly
   what SOLUSDT was at its C3: 1h klines + settled funding (settlement-
   timestamp availability) + spread census as cost book. Nothing in the
   authorization is pair-specific.
2. **The fences are symbol-swap-invariant within that class.** SOL P1 row-8
   logic, ratified into this child's plan §1 ("SOLUSDT C3 fences là
   pair-agnostic trong lớp observable giống hệt") and re-derived per-row
   above: for every one of rows 1–11, the nearest recorded death kills the
   payer/information/risk triple, not the ticker.
3. **LESSON P-29 states the expected result verbatim** and this lane confirms
   it: "Pair-swap không mở lại không gian … child #1 của chương trình
   pair-by-pair đóng slate trống với 0 cell/0 look; fences killing nó là
   pair-agnostic trên cùng lớp observable — pair #2 với cùng lớp observable
   và không có góc thông tin mới có kết quả lặp lại."
4. **No R5-class new information and no dated cost-regime break exist
   tonight within the authorized class** — the only two doors other than the
   ≥2-of-3 axis test (child §1), both of which require bytes this program
   does not have authorization (or, for the spread census, disk) to touch
   tonight.
5. **Axis-differencing cannot be manufactured on tonight's observables:**
   every constructible direction source (rows 1–11) maps to ≤1-of-3 genuine
   axis differences vs its nearest death. The one class that would differ on
   all three axes if authorized (BNB event layer, W2) sits outside the
   delegation boundary and is therefore a revival condition, not a proposal.

Zero registry slots burned; withdrawals here are free (the ceiling counts
only submitted rows). No DEFERRED rows requested.

## 4. Revival conditions (what would reopen BNB proposal space — gates, not wishes)

1. **C1 measured BNB funding distribution** (mandatory regardless of this
   lane, child §2.1/§2.4): if the ceiling×power grid (run-mean × H_min ≥
   RT_stress ∧ episodes ≥ 100) is non-empty on BNB's own series, a
   carry-class row MAY be re-proposed — it must FIRST name 2-of-3 genuine
   axis differences vs `CARRY`/`TRACKB1`/`FUNDCROWD`/`FUNDJUMP`/
   `PWSCXSOL1-I001` AND clear the P-29 representation-rho bar (gate state vs
   the dead level-window shadows ≤ 0.20) or it stays dead by family law.
   Proposal drafting post-census remains legitimately outcome-blind (the
   funding distribution is cost book, not PnL).
2. **New data authority (owner action, R5-class):** (a) a BNB event calendar
   (burns, regulatory events, Launchpool cycles) — W2, the one class that
   could pass all three F-0 tests; (b) liquidation tape / multi-year OI / L2
   history — W5's payers become encodable; (c) an options surface —
   vol-risk-premium payers. Each is a new information layer, the only thing
   the recorded reopen conditions accept.
3. **Nothing else.** Re-clock, re-label, buffer, window, filter, sign-flip,
   pair-swap, timeframe-downshift (15m/1m = `ANCESTRY_EXPOSED_RECLK`, dev
   only, never OOS — Q-3), and "different distribution" claims are
   pre-vetoed (master §2.3/§1.2/§7; LESSONS P-27/P-28/P-29).

## 5. Cost-auditor note

No proposal submitted ⇒ no fill distribution to condition this cycle. Facts
for the cost lane: BNB funding must be measured per-settlement at C1
(child §2.4 — no SOL/BTC/ETH constant inheritance); the spread census is
`NOT_RUN_DISK_CONSTRAINT` (≥25GB required vs available; SOL precedent ~12GB
for a 6-month stratified census) ⇒ cost gate fail-closed for scoring tonight,
making C4 infeasible this sprint per child §3-C4 — independent of this lane's
output. If a future carry-class identity is revived, its fills will cluster
in the 8h-settlement neighborhood (00–02, 08–10, 16–18 UTC); keep
settlement-adjacent buckets separate in any census.

## 6. Known limitations of this lane

- Outcome-blind by design: no BNB funding distribution, no BNB spread census,
  and no PnL were seen or computed against (data plane not staged at lane
  time; only `C0_control_plane.md` existed in the control dir). All
  distribution-shaped arguments in this document are priors from recorded
  deaths on other pairs of the same class — deliberately, because the
  identity kills do not depend on BNB's own numbers.
- The zero-survivor claim is against failure memory as of 2026-09-26 (137
  entries, incl. `PWSCXSOL1-I001`); an owner-authorized new information layer
  (§4.2) invalidates it by design — that is the intended reopening path, not
  a flaw.
- Dispatch-vs-measured HEAD discrepancy (363cf282 vs f15e67ac) disclosed in
  the header and handoff; no lane-owned content was affected.
- Registry discipline: nothing from this lane was written to
  `IDENTITY_REGISTRY.jsonl`; withdrawals made here are free. This lane holds
  no lock (light lane) and touched no data plane file.

— P1, outcome-blind lane, PWS-CX-BNBUSDT-C1
