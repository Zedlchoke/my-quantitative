# PB2 ANCESTRY COURT DRAFT — futures 6E/6B London design vs the dead FOREX-FREE-V1/V2 London families

- Task: `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003`, lane **B2-DEEP-6E6B**,
  generated 2026-10-03 (UTC).
- **Status: DRAFT DOSSIER FOR A FUTURE REOPENING DECISION. This document does
  NOT reopen PB2.** PB2 remains **HOLD** by Co-Owner ruling (PLAYBOOKS_DRAFT
  r5 §2: "PHÁN QUYẾT CO-OWNER: HOLD. Lý do ancestry: FOREX-FREE-V1/V2 London
  failures — họ London-session trên FX spot đã chết; bản futures này chưa
  chứng minh khác họ"). The reopening ruling is the Co-Owner's alone; this
  court draft only assembles the evidence such a ruling would consume.
- Class: PREP desk research. **0 PnL computed here, 0 scored runs, 0 signal
  ranking.** Historical expectancy numbers of the dead families are FROZEN
  PUBLISHED terminal artifacts cited as ancestry evidence, not new results.
  Every PB2 parameter remains **[PROVISIONAL]**.
- Ancestry evidence sources (root checkout, READ-ONLY, never written):
  `/Users/hoangminhlong/my-quantitative/plans/PLAN_forex_v2.md` (the dead
  family plan, §0–§1 binding); git objects at frozen SHAs (cited per claim);
  `research/control/FUTURES-DATACONTRACT-QUAL-V1/PLAYBOOKS_DRAFT.md` §0/§2
  (binding lineage statement). Futurе-side evidence: dossiers v2 + analysis
  JSONs (cited file:section / script:field).
- Taxonomy: FACT (frozen artifact @ SHA / official source + date) / OBSERVED
  (script + window) / POSTULATED / NOT_RUN / NOT_LOCATABLE / DERIVED
  (arithmetic from named inputs).

---

## (a) What the dead families were

### Common data plane of both dead cycles [FACT]

- Seven-pair FREE FX **spot** snapshot (AUD/USD, USD/CAD, USD/CHF, USD/JPY,
  EUR/USD, NZD/USD, GBP/USD — pair set enumerated in the published
  concentration tables), **H1 = hourly OHLCV bars** in UTC
  [FACT: `research/control/forex_free_v1_run/execution_summary.json` @
  bee64bea `pair_concentration`; `data_probe/audit_*_1h.json` file set;
  PLAN_forex_v2.md §0].
- Cost authority: frozen **proxy 1.5 bps per side × stress multipliers
  {1.0, 1.5, 2.0}** (base round trip 3.0 bps); **no bid/ask series used or
  assumed** (H4 unavailable fail-closed); no rollover/swap authority — every
  position **forced flat before the 17:00 New York rollover** (uniformly the
  H1 bar ending 16:00 NY) [FACT: PLAN_forex_v2.md §0; V1 family1 module
  docstring @ orca/forex-free-v1-f6-family-1 ed6eecca; V2 accounting
  `COST_TIERS = (1.0, 1.5, 2.0)` @ b91d31d0].
- Proposals requiring macro release calendars, rates vintages, bid/ask or
  swap fields were **ineligible** in V2 [FACT: PLAN_forex_v2.md §2] — the
  dead families had **no central-bank event conditioning capability**.
- Both cycles terminated REJECT_ALL with exact reproduction; historical
  Forex denominator after V2 = **12 scored cells (6 + 6), 0 survivors**
  [FACT: PLAN_forex_v2.md §0; V2 close commit 2d68c81c "denominator 12"].

### FOREX-FREE-V1 (terminal `FOREX_FREE_V1_REJECT_ALL` @ bee64beaf2637ea51216cffc6be6393d545bf474)

Six cells (anchor/neighbour/control × 2 families), all
EXPECTANCY_NONPOSITIVE [FACT: `scored_ledger_published.jsonl` @ bee64bea;
terminal audit commit 132496e3]:

| family | design (frozen spec) | arm | expectancy USD/trade | PF | trades |
|---|---|---|---|---|---|
| V1-A3-P1 **London-Open Session Continuation** | anchor = London open 08:00 Europe/London; momentum m = c3/c0−1 on the first 3 H1 session bars (signal public 11:00 London); **entry = close of next H1 bar (fill 12:00 London)**, sign(m); hold to flatten at the H1 bar ending 16:00 NY; neighbour = same construction anchored 08:00 America/New_York; causal control = **−sign(m)** | anchor | **−2.353** | 0.849 | 11,459 |
| | | neighbour (NY-open) | −3.160 | 0.629 | 11,512 |
| | | control (anti-momentum) | −3.647 | 0.776 | 11,459 |
| V1-A3-P2 **Late-NY Fade of Volatility-Standardized Extension** | NY 08:00 anchor; r = same-day move after exactly 4 completed NY H1 bars; gate \|z\| = \|r/σ20\| ≥ 1.0 (σ20 = trailing-20-day daily log-close std, strict past); take **−sign(r)** for the late-NY window; flatten pre-rollover; neighbour = Tokyo 09:00 anchor; control = sign-flipped (continuation) | anchor (fade) | **−2.896** | 0.638 | 1,020 |
| | | neighbour (Tokyo) | −2.720 | 0.887 | 142 |
| | | control (continuation) | −3.104 | 0.618 | 1,020 |

[FACT: family specs from frozen modules @ orca/forex-free-v1-f6-family-1
ed6eecca and orca/forex-free-v1-f6-family-2; cell books from
`research/control/forex_free_v1_run/execution_summary.json` @ bee64bea —
per-cell folds all negative for the family1 anchor (−1.75/−3.09/−2.22),
stress tier ×1.5 expectancy −3.85.]

- Controls were WORSE than anchors (direction coherence existed); "a worse
  control cannot rescue a negative mechanism" [FACT: PLAN_forex_v2.md §1].
- V1 family1's trade-count concentration: EUR/USD 12.5%, GBP/USD 14.6% of
  11,459 anchor trades [FACT: execution_summary pair_concentration @ bee64bea]
  — the pair legs that PB2 would trade were inside the dead portfolio.
  **Per-pair EXPECTANCY of the dead families: NOT_LOCATABLE** in the
  published ledgers (books are portfolio-level only; recovery = re-running
  the frozen dead modules per-pair — a registered-cycle action, NOT a desk
  action; listed in §d).
- Forbidden-inventory facts carried forward by V2: London-open continuation
  and NY-open nearby-clock variants; late-NY standardized-extension fade and
  nearby threshold/horizon variants; sign inversion, reduced costs, selected
  pairs, session relabeling; and "the near-duplicate London-to-NY momentum
  proposal identified in V1 novelty audit" [FACT: PLAN_forex_v2.md §1; the
  V1 F5 novelty audit flagged exactly one HIGH-pair near-duplicate:
  "A3-P1/A4-P2 near-duplicate London momentum", commit bd5f2a32].

### FOREX-FREE-V2 (terminal `FOREX_FREE_V2_REJECT_ALL` @ 2d68c81c)

Six cells, all EXPECTANCY_NONPOSITIVE; denominator 12 [FACT: terminal commit
a86e3f79; A7 terminal PASS 5cc8a7a0]:

| family | design (frozen spec) | arm | expectancy USD/trade | PF | trades |
|---|---|---|---|---|---|
| FXFV2-A4-P1 **Tokyo-range compression → London-morning expansion** | Tokyo session 09:00–18:00 Asia/Tokyo (9 H1 bars); state = Tokyo range < 0.75 × median of trailing 20 sessions (30-day window, strict past); trigger/expansion evaluated in the **London-morning window 08:00–12:00 Europe/London (4 H1 bars)**; governor ≤1 entry/pair/UTC-day, ≤3 RT/pair/week; flat at 16:00 NY bar; notional $10,000 USD-units | anchor | **−3.80** | 0.593 | 1,541 |
| FXFV2-A4-P2 **London-AM range break confirmed by retest-hold** | London-AM range = H1 bars opening [08:00,12:00) London (L_H/L_L); initial break = first bar opening [12:00,17:00) with high > L_H or low < L_L; anchor requires a **retest-hold** in [break+1h, 19:00) London (retrace to the break level, close holds beyond it); void = failed retest; neighbour = retest at the break bar's far extreme E_B; control = placebo level (Tokyo midpoint class) | anchor | **−3.09** | 0.720 | 3,830 |

[FACT: specs from frozen modules @ 355df3fa (family1.py, proposal sha256
e9878d43…) and cae566aa (family2.py, proposal sha256 93e940a9…); cell books
from commit a86e3f79 message and `research/control/forex_free_v2_run/
scored_ledger_published.jsonl` @ 2d68c81c.]

- **The V2 selected families were BOTH London-window families** — A4's wave
  was "session-range proposals" (commit f20dfe5d) and both selected designs
  evaluate their state/trigger inside 08:00–12:00 Europe/London. The PB2
  lineage statement ("FOREX-FREE-V1/V2 London failures") is therefore
  literally supported: V1 died on a London-open continuation (+ late-NY
  fade), V2 died on two London-morning range constructions.
- **Specifics NOT_LOCATABLE in-repo (within this lane's read budget), tagged
  NOT_RUN**: per-arm neighbour/control books for V2 beyond the anchor
  summaries in commit messages (locatable at
  `research/control/forex_free_v2_run/execution_summary.json` @ 2d68c81c but
  not extracted here); per-pair books (both cycles); the full text of the V1
  near-duplicate "London-to-NY momentum" proposal; the seven-pair snapshot
  itself (data_raw gitignored). None of these were invented.

### The ancestry overlap, stated honestly

PB2-H-C (London-morning range 08:00–11:00 local, 1m-close trigger
11:00–15:30 local, hold to 16:00 CT) vs the closest dead ancestor
V2-A4-P2 (range from H1 bars 08:00–12:00 local, break [12:00,17:00),
resolve by 19:00 local): **same signal family, same city-clock, same
continent of holding window**. Differences are: resolution (1m vs H1),
confirmation (PB2 base trigger has NO retest-hold requirement — the V2
anchor's extra filter), exit (16:00 CT ≈ 22:00/23:00 London — PB2 holds
~3–4h LONGER into the US afternoon than V2's 19:00 resolution), venue,
costs, conditioning. **The court therefore cannot claim "different
mechanism" by construction; the distinction must be measured.** That is the
whole point of this dossier.

---

## (b) Three-part ancestry-veto distinction

For each veto axis: is the futures 6E/6B London design distinguishable IN
PRINCIPLE, and what measurable PRE-REGISTRATION evidence would prove the
distinction. "Pre-registration evidence" = descriptive, prep-legal
measurements freezable BEFORE any scored cell (no PnL, no selection).

### b1. Mechanism veto

- Dead claim: London(-morning) session information, read off spot H1 bars,
  continues/reverses predictably intraday. Futures claim: London-morning
  flow on a central-limit-order-book vehicle discovers information while US
  liquidity is absent; US-session absorption continues (H-C) or fades (H-D)
  it. IN PRINCIPLE: **PARTIALLY distinguishable** — the economic story is
  the same family claim; what differs is the microstructure through which
  the information is created and observed.
- Measurable pre-registration evidence that would prove distinction:
  1. **1m trigger-time anatomy** [prep-legal, NOT_RUN to date]: at each
     trigger minute, volume / |1m return| / RV vs matched non-trigger
     minutes (same London clock-minute, non-trigger days). Information
     burst (H-C world) vs thin-book drift (H-D world) make opposite
     predictions. This measurement cannot be replicated by the dead H1
     families — hourly aggregation cannot see it. Required BEFORE any
     scored registration; it is falsifiable without PnL.
  2. **Trigger census** (§c): the dead families' trade counts are known
     (11,459 / 3,830 anchor trades); the futures trigger density at 1m is
     NOT_RUN and must be censused first.
  3. **USD common-factor diagnostic**: the dead 7-pair portfolio could not
     be USD-neutral in V1 family1's concentration (EUR 12.5% / GBP 14.6%
     trade share [FACT @ bee64bea]); PB2 trades exactly the two
     non-USD-quote legs. Pre-register: same-London-day 6E/6B trigger
     co-occurrence rate + DXY-class conditioning is NOT available (no DXY
     PIT series on disk) — so the pre-registrable version is the 6E/6B
     trigger correlation itself. If triggers co-fire and arms move
     together, the "mechanism" reduces to a USD factor the dead families
     already failed to exploit; K3 guards the family claim.
  4. **Exit-horizon decomposition**: PB2 holds to 16:00 CT vs V2's 19:00
     London resolution — pre-register the London-afternoon (15:30 London →
     16:00 CT) leg as a separately reported descriptive segment so the
     longer hold cannot silently absorb a V2-style resolution effect.

### b2. Information-source veto

- Dead: vendor free spot H1 OHLCV, no order book, no bid/ask, no macro
  calendar (ineligible by law), forced-flat clock. Futures: exchange 1m
  bars of a CME Globex central limit order book; tick-grid prices (6E 5e-05
  / 6B 0.0001 adjudicated, §1 of both addenda); exchange-cleared volume;
  PIT-verified ECB 55/55 + BoE MPC + FOMC calendars. IN PRINCIPLE:
  **YES — distinguishable.** The information set is strictly richer and
  differently sourced; this is the strongest of the three distinctions.
- Measurable pre-registration evidence:
  1. **Event-day conditioning implementable for the first time**: base-EXCLUDE
     ECB GC (6E) / BoE MPC (6B) / FOMC days with verified timestamps
     (addenda §2) — the dead families could not even represent this filter.
     The INCLUDE-sensitivity leg is the measurable distinction: if the
     effect exists ONLY on excluded-day types, K1 reclassifies it as an
     event effect — a family the dead corpus never tested.
  2. **Volume observability at decision time**: exchange 1m volume at the
     trigger minute (usable for the b1.1 anatomy); the dead H1 corpus had
     only hourly volume. Pre-register trigger-minute volume percentile vs
     the session's own distribution.
  3. **Tick-grid discipline**: 0 close-price tick violations on 3.05M bars
     (6E) / 2.55M (6B) [OBSERVED, addenda §1/§6] — every trigger close is a
     book price, not a vendor-interpolated mark. (Fill realism remains
     unproven — no BBO; see §d.)
  4. **Session-template evidence**: Globex 23h template + London-local
     bucketing DST-proof (6E mismatch-week 1h shift; 6B minute-720 anchor)
     [OBSERVED, addenda §3] — the city-clock law is measured on THIS venue,
     not assumed from the spot corpus.

### b3. Causal-control veto

- Dead: V1 arms = anchor + clock-neighbour + sign-flipped causal control;
  V2 proposals REQUIRED "anchor, one neighbour and one causal/placebo
  control" each [FACT: PLAN_forex_v2.md §7]. So "having controls" is NOT a
  distinction — the dead cycles had them. What failed: after-cost
  expectancy was negative for every anchor AND every control (V1), i.e.,
  the cost base (3.0 bps round trip proxy) ate any coherence; and controls
  were one-shot, without published power analysis.
- IN PRINCIPLE: **PARTIALLY distinguishable** — via control POWER and
  registration structure, not via control existence.
- Measurable pre-registration evidence:
  1. **Placebo court with power analysis** (§c): multi-seed clock/placebo
     distribution with a pre-computed separation band, and always-in-window
     baseline. PB1's single-seed 20261002 placebo was an explicitly
     published limitation (PLAYBOOKS §1 identity table note) — the PB2
     court must NOT inherit it.
  2. **Both-tails both-arms registration**: H-C and H-D registered
     simultaneously (PB §4.6 law: no post-hoc tail/direction choice) — the
     dead cycles' anchors were single-direction with sign-flipped controls;
     registering the competitor arm as a first-class hypothesis is a
     stronger falsification structure.
  3. **Delay-pair structure**: mandatory +1-bar and +30m delay variants
     (the 07:30 CT ×1.95 US-macro spike falls inside the trigger window
     [OBSERVED, 6E addendum §5]) — a microstructure-artifact detector the
     H1 corpus could not express (its smallest delay was 1 hour).
  4. **Kill rules K1–K5 pre-frozen** (addenda §9), incl. K4 DST-mismatch
     sign flip = clock-law bug not alpha — a bug class the dead cycles'
     DST tests covered at entry instants but not as a sign-stability
     diagnostic.

### b4. Cost-structure comparison (the uncomfortable arithmetic) [DERIVED]

| vehicle | half-turn spread | round-trip modeled cost | authority |
|---|---|---|---|
| Dead spot V1/V2 proxy | 1.5 bp/side fixed | **3.0 bp** base (4.5 / 6.0 stress) | frozen proxy [FACT] |
| 6E futures, modeled | close-proxy 1.21–1.57 bp/side (3 ticks; px 0.9552–1.2429) + slippage 0.45–1.36 bp/side (1–3 ticks @ 1.10) + commission ≈0.006 bp/side ($0.85/$137.5k) | **≈3.3–5.9 bp + exchange fee (NOT_FETCHED)** | DC §1.7 + addendum §7 arithmetic |
| 6B futures, modeled | close-proxy 2.11–2.89 bp/side (px 1.0392–1.4205) + slippage 0.77–2.31 bp/side (1–3 ticks @ 1.30) + commission ≈0.010 bp/side | **≈5.8–10.4 bp + exchange fee (NOT_FETCHED)** | DC §1.7 + addendum §7 arithmetic |

- Reading: **the futures vehicle is NOT cheaper per notional than the dead
  spot proxy** — 6E is comparable-to-worse, 6B is clearly worse — and the
  exchange fee layer is still missing. Any reopening argument of the form
  "futures costs are lower" is CURRENTLY UNSUPPORTED. The honest
  cost-distinction claim is structural (observable tick grid, fee
  components decomposable, no dealer spread opacity) not level-based — and
  even that requires the A4 fee table to complete.
- Margin: 6E $2.4–2.6k, 6B $2.2–2.4k per contract [FACT public-reference,
  DC §1.7] — vs spot $10,000 USD-units frozen notional in V2 [FACT @
  355df3fa]. Capital efficiency differs; that is a sizing fact, not an edge.

---

## (c) Placebo court — design + POWER analysis

### c1. Population

- 6E held-chain sessions 2020-01→2026-09: 1,746 [OBSERVED, 6E_v2 §1].
- 6B calendar-chain sessions: 1,746 [OBSERVED, 6B_v2 §0.1].
- Evaluable population after stand-asides [DERIVED]: warmup 60d + base
  event-day exclusions (6E: ECB 55 + FOMC 58; 6B: MPC 56 + FOMC 58;
  ECB/MPC/FOMC date overlap assumed zero — ECB/MPC are Thursdays, FOMC
  Wednesdays, 2020 emergencies excepted; assumption disclosed):
  **6E ≈ 1,573; 6B ≈ 1,572** sessions (~233/symbol/year). Matches the
  dispatch's "~1,700/session-symbol" order before exclusions.

### c2. Expected trigger counts — census NOT_RUN, bounds stated

- Trigger = first 1m close strictly outside R_lon in 11:00–15:30 London.
  Design cap: 1 trigger/session (first-touch; re-arm policy unspecified
  [PROVISIONAL]) ⇒ upper bound = evaluable sessions ≈ 1,573/1,572.
- Actual census: **NOT_RUN in this lane** (prep-legal descriptive pass, not
  executed here). The court REQUIRES it as its first evidence item.
- Decisive consequence [DERIVED]: if first-touch frequency < ~1/3 of
  sessions (n < ~500/symbol), per-symbol MDE rises above ~6 bp (c3) — at or
  above the modeled cost scale — and the court is underpowered by
  thinness. **Pre-commit a minimum-census gate (suggested ≥500
  triggers/symbol [PROVISIONAL]) BEFORE any scored design is frozen** —
  the PB3/K0 kill-by-thinness lesson applied prospectively.

### c3. Minimum detectable effect (MDE) [DERIVED]

Method: two-sided α=0.05, power 80% (z = 2.80); dispersion proxy = daily
return std — 6E 0.463% (46.3 bp) [OBSERVED, `6E_a1_regimes.json`], 6B
0.549% (54.9 bp) [OBSERVED, 6B_v2 §1]. The trade horizon (entry → 16:00 CT
same day) is shorter than a full session day, so daily σ is an
**upper-bound** dispersion proxy ⇒ tabulated MDEs are conservative
(upper bounds). True per-trade dispersion: NOT_RUN (would require the
census + descriptive per-trade return distribution — court input).

| n triggers | 6E MDE (bp/trade) | 6B MDE (bp/trade) |
|---|---|---|
| 100 | 12.97 | 15.38 |
| 300 | 7.49 | 8.88 |
| 500 | 5.80 | 6.88 |
| 600 | 5.30 | 6.28 |
| 900 | 4.32 | 5.13 |
| 1,573/1,572 (full) | 3.27 | 3.88 |

Against modeled round-trip cost (b4): 6E ≈3.3–5.9 bp + fee; 6B ≈5.8–10.4 bp
+ fee. **Reading: at realistic trigger densities (n ≈ 300–900/symbol) the
court can only detect mean effects of ~4–9 bp/trade — i.e., effects at or
above the full modeled cost.** An edge smaller than cost is simultaneously
undetectable at this power AND unprofitable, so the court's power floor and
the cost floor coincide. Pooled 6E+6B (n ≈ 3,145, common-mechanism claim
guarded by K3) would cut MDE to ~2.3–2.7 bp [DERIVED] — pooling is a
design option for the future registered cycle, not a claim made here.

### c4. Control arms the court must run (all [PROVISIONAL], none run here)

1. **Clock/placebo (C1-class)**: identical entry times to the triggered
   set, random sign, seeded; **multi-seed (≥100 seeds) distribution** with
   pre-computed seed-dispersion band — the arm means must separate from the
   placebo band by more than its own width. Single-seed is explicitly
   insufficient (PB1 precedent). Placebo seeds are diagnostics (or must be
   budgeted as scored identities — Co-Owner trial-ceiling decision, §d).
2. **Always-in-London-window (C2-class)**: enter every evaluable session at
   a fixed London time unconditionally. Distinguishes range-break
   INFORMATION from mere London-window exposure/drift (6B's London share
   drifted 28.7%→23.7% — a full-sample always-in baseline would smear two
   liquidity regimes; run split 2020-22 / 2023-26).
3. **What the placebo court must be able to distinguish — pass criteria
   [PROVISIONAL]**:
   - range-break trigger information vs window exposure (arm vs C2);
   - continuation vs fade (H-C vs H-D both registered, K2 both-floor);
   - open-microstructure timing artifact (delay 0 vs +1-bar vs +30m pair,
     K4-analog from PB1);
   - event-day contamination (base-EXCLUDE vs INCLUDE sensitivity, K1);
   - clock-law bug (DST-mismatch-week sign flip, K4);
   - common mechanism vs symbol-specific (6E vs 6B sign agreement, K3);
   - regime artifact (rolling 2020-22 vs 2023-26 sign stability, K5).
   The court FAILS if any of: placebo band overlaps the arm means; C2
   reproduces the arm; arms flip sign across delay variants; or the effect
   exists only under INCLUDE. A court that cannot reach the c2 census gate
   or the c3 power floor is VOID before scoring — kill-by-thinness, no
   rescue (PB3 K0 precedent).

---

## (d) Verdict-in-draft — what this court CAN and CANNOT establish, and the dependency list

**Can establish today (evidence assembled above):**
- What died, precisely: four frozen London/NY window families on 7-pair
  spot H1, 3.0 bp round-trip proxy cost, forced-flat clock, no event
  conditioning — all 12 cells EXPECTANCY_NONPOSITIVE, 0 survivors,
  reproduction exact [FACT].
- That the PB2 futures design is IN PRINCIPLE distinguishable on
  information source (strongest axis: venue, resolution, PIT calendars,
  tick-grid), PARTIALLY distinguishable on mechanism (resolution +
  conditioning + exit horizon; the signal family overlaps V2-A4-P2) and on
  causal control (power + registration structure, not control existence),
  and NOT currently distinguishable on cost level (b4 arithmetic is
  unfavorable and incomplete).
- The falsifiable pre-registration package (b1–b3 evidence items + c4
  controls + K1–K5) a future reopening decision would demand.

**CANNOT establish today — explicit dependency list:**

| # | missing evidence | owner of the unlock | status |
|---|---|---|---|
| 1 | FX official holiday calendar 6E/6B (calendar-uncertain ⇒ EXCLUDE must become evidence-based) | lane A2-CMECAL-FX (in flight, same task) | NOT_RUN at write time — requirements written (addenda §4) |
| 2 | Exchange fee table 6E/6B (completes b4; without it the cost-structure distinction stays open) | lane A4-FEES (public) + owner account verification (NOT_RUN) | NOT_FETCHED |
| 3 | BBO / execution realism (fill realism claims impossible; conservative fills only — D5 ruling: not purchased) | owner | NOT_RUN |
| 4 | Trigger census + 1m trigger-time anatomy + per-trade dispersion (court's first inputs; prep-legal descriptive) | a future prep lane / registered cycle design phase | NOT_RUN (this lane: desk only) |
| 5 | Dead-family per-pair expectancy (EUR/USD, GBP/USD legs) — was the death uniform or pair-concentrated? | owner decision to re-run frozen dead modules per-pair under registered action | NOT_LOCATABLE in published ledgers |
| 6 | Multi-seed placebo budget ruling (are placebo seeds scored identities under the Co-Owner ceiling?) | Co-Owner | NOT_RUN |
| 7 | (Boundary note, not PB2) CIP-vintage quantification + real-time SOFR source decision — gates H2-family carry registration only; PB2 holds no overnight positions | owner | NOT_RUN |

**This court draft renders NO reopening verdict.** PB2 remains HOLD. If the
Co-Owner ever reopens, the order of consumption should be: (1) dependencies
1–2 land; (2) court inputs 4 censused; (3) census ≥ threshold and power
floor reachable; (4) mechanism court (b) evidence package frozen
outcome-blind; (5) placebo court (c) pass; (6) only then a scored spec may
be drafted — under the then-current trial ceiling and standing
NO_GO_REGISTER/NO_SCORE/NO_ORDER rulings.

— End PB2_ANCESTRY_COURT_DRAFT.
